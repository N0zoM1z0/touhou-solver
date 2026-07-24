#!/usr/bin/env python3
"""Tests for compact same-slot bullet-transform differential evidence."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from th08_transform_trace import analyze_transform_trace, decode_trace_bullet


def _bullet(
    *,
    slot: int = 7,
    x: float = 100.0,
    vx: float = 1.0,
    active_flags: int = 0x80,
    speed: float = 1.0,
    angle: float = 0.0,
    timer: int = 0,
    repeat_count: int = 0,
    callback_phase: int | None = None,
    callback_aux: int | None = None,
) -> list[object]:
    runtime: list[object] = [
        speed,
        angle,
        0x80,
        1,
        [1, 0, 0, 0.0, 0.0, 0, 0],
        0.0,
        timer,
        6,
        2.0,
        0.25,
        2,
        repeat_count,
    ]
    if callback_phase is not None and callback_aux is not None:
        runtime.extend((callback_phase, callback_aux, []))
    return [
        slot,
        x,
        200.0,
        vx,
        0.0,
        2.0,
        2.0,
        active_flags,
        runtime,
    ]


def _planning_bullet(
    *,
    slot: int = 7,
    x: float = 100.0,
    vx: float = 1.0,
    callback_phase: int = 1,
    callback_aux: int = 0,
    velocity_changes: list[list[float | int]] | None = None,
) -> list[object]:
    return [
        slot,
        x,
        200.0,
        vx,
        0.0,
        2.0,
        2.0,
        0,
        None,
        [
            1.0,
            0.0,
            0x00100202,
            callback_phase,
            callback_aux,
            velocity_changes or [],
            0.0,
            0.0,
        ],
    ]


class TransformTraceTests(unittest.TestCase):
    def test_runtime_payload_decoder_keeps_stop_state(self) -> None:
        state = decode_trace_bullet(
            _bullet(speed=0.0, vx=0.0, timer=5, repeat_count=1)
        )
        self.assertIsNotNone(state)
        self.assertEqual(
            (
                state["slot"],
                state["active_flags"],
                state["timer_elapsed"],
                state["repeat_count"],
                state["motion"],
            ),
            (7, 0x80, 5, 1, "stopped"),
        )
        self.assertIsNone(decode_trace_bullet(_bullet()[:8]))

    def test_planning_projection_keeps_callback_events_without_queue_state(
        self,
    ) -> None:
        state = decode_trace_bullet(
            _planning_bullet(velocity_changes=[[5, 0.0, 0.0]])
        )
        self.assertIsNotNone(state)
        self.assertTrue(state["planning_projection"])
        self.assertFalse(state["diagnostic_runtime"])
        self.assertIsNone(state["queue_cursor"])
        self.assertEqual(state["original_flags"], 0x00100202)
        self.assertEqual(state["callback_phase_state"], 1)
        self.assertEqual(state["velocity_change_count"], 1)

        row = {
            "kind": "decision",
            "frame": 100,
            "snapshot_frame": 100,
            "active_bullets": 1,
            "spell": {"spell_id": 111},
            "nearby_bullets": [
                _planning_bullet(velocity_changes=[[5, 0.0, 0.0]])
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trace.jsonl"
            path.write_text(json.dumps(row) + "\n", encoding="utf-8")
            report = analyze_transform_trace(path, spell_id=111)
        self.assertEqual(report["diagnostic_runtime_sample_count"], 0)
        self.assertEqual(report["planning_projection_sample_count"], 1)
        self.assertEqual(report["projected_velocity_event_sample_count"], 1)
        self.assertEqual(
            report["callback_states"],
            {"phase=1,aux=0,motion=moving": 1},
        )

    def test_full_pool_trace_retains_same_slot_stop_and_resume(self) -> None:
        rows = [
            {
                "kind": "decision",
                "frame": 100,
                "snapshot_frame": 100,
                "gameplay_epoch": 0,
                "active_bullets": 1,
                "spell": {"spell_id": 111},
                "nearby_bullets": [],
                "transform_bullets": [
                    _bullet(x=100.0, speed=1.0, vx=1.0, timer=0)
                ],
            },
            {
                "kind": "decision",
                "frame": 103,
                "snapshot_frame": 103,
                "gameplay_epoch": 0,
                "active_bullets": 1,
                "spell": {"spell_id": 111},
                "nearby_bullets": [],
                "transform_bullets": [
                    _bullet(x=103.0, speed=0.0, vx=0.0, timer=3)
                ],
            },
            {
                "kind": "decision",
                "frame": 106,
                "snapshot_frame": 106,
                "gameplay_epoch": 0,
                "active_bullets": 1,
                "spell": {"spell_id": 111},
                "nearby_bullets": [],
                "transform_bullets": [
                    _bullet(
                        x=109.0,
                        speed=2.0,
                        vx=2.0,
                        active_flags=0,
                        angle=0.5,
                        timer=6,
                        repeat_count=1,
                    )
                ],
            },
            {
                "kind": "decision",
                "frame": 109,
                "snapshot_frame": 109,
                "gameplay_epoch": 0,
                "active_bullets": 1,
                "spell": {"spell_id": 115},
                "transform_bullets": [_bullet()],
            },
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trace.jsonl"
            path.write_text(
                "".join(json.dumps(row) + "\n" for row in rows),
                encoding="utf-8",
            )
            report = analyze_transform_trace(path, spell_id=111)

        self.assertEqual(report["decision_count"], 3)
        self.assertEqual(report["source_fields"], {"transform_bullets": 3})
        self.assertEqual(report["active_pool_coverage_ratio"]["median"], 1.0)
        self.assertEqual(report["adjacent_pairs"], 2)
        self.assertEqual(report["active_stop_pairs"], 2)
        self.assertEqual(report["timer_progression_mismatches"], 0)
        self.assertEqual(report["transition_counts"]["motion"], 2)
        self.assertEqual(report["transition_counts"]["active_flags"], 1)
        self.assertEqual(report["transition_counts"]["repeat_count"], 1)
        self.assertEqual(report["retained_transition_count"], 2)

    def test_nearby_only_trace_exposes_incomplete_pool_coverage(self) -> None:
        row = {
            "kind": "decision",
            "frame": 100,
            "snapshot_frame": 100,
            "active_bullets": 10,
            "spell": {"spell_id": 111},
            "nearby_bullets": [_bullet()],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trace.jsonl"
            path.write_text(json.dumps(row) + "\n", encoding="utf-8")
            report = analyze_transform_trace(path, spell_id=111)
        self.assertEqual(report["source_fields"], {"nearby_bullets": 1})
        self.assertEqual(report["active_pool_coverage_ratio"]["median"], 0.1)

    def test_callback_state_exposes_lookahead_that_never_activated(self) -> None:
        row = {
            "kind": "decision",
            "frame": 39702,
            "snapshot_frame": 39700,
            "active_bullets": 1,
            "spell": {"spell_id": 111},
            "bullet_velocity_lookahead": {
                "instruction_pointer": 0x0B1D6FCC,
                "timer_elapsed": 0,
                "events": [],
                "attached_bullets": 0,
                "error": None,
            },
            "nearby_bullets": [
                _bullet(
                    active_flags=0,
                    speed=1.2,
                    vx=0.0,
                    callback_phase=0,
                    callback_aux=1,
                )
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trace.jsonl"
            path.write_text(json.dumps(row) + "\n", encoding="utf-8")
            report = analyze_transform_trace(path, spell_id=111)
        self.assertEqual(
            report["callback_states"],
            {"phase=0,aux=1,motion=stopped": 1},
        )
        self.assertEqual(report["ecl_lookahead"]["event_rows"], 0)
        self.assertEqual(report["ecl_lookahead"]["attached_rows"], 0)
        self.assertEqual(
            report["ecl_lookahead"]["timer_elapsed"],
            {"0": 1},
        )


if __name__ == "__main__":
    unittest.main()
