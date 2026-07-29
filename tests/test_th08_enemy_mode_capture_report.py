#!/usr/bin/env python3
"""Tests for compact TH08 player/enemy mode evidence reports."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from analysis.th08_enemy_mode_capture_report import build_report


def _capture(
    *,
    secondary: bool,
    input_current: int,
    frame: int,
    coherent: bool = True,
) -> dict[str, object]:
    flags = 0x0100194D if secondary else 0x0100114D
    return {
        "kind": "decision",
        "frame": frame,
        "gameplay_epoch": 1,
        "stage_route_index": 5,
        "player_enemy_mode_capture": {
            "role": "diagnostic_shadow",
            "status": "coherent" if coherent else "enemy_frame_unstable",
            "coherent": coherent,
            "attempts": 1 if coherent else 2,
            "read_ms": 0.25,
            "mode_sensitive_body_count": 1,
            "mode_sensitive_bodies": [[0x4B8A80, flags]],
            "player_after": {
                "input_current": input_current,
                "focus_logic": int(bool(input_current & 0x04)),
                "secondary_character_active": secondary,
                "focus_transition_counter": 7,
                "effective_focus": bool(input_current & 0x04),
            },
            "sync_mismatch_pointers": [],
            "action_authority": False,
        },
    }


class EnemyModeCaptureReportTests(unittest.TestCase):
    def test_report_retains_adjacent_secondary_transition_body_sets(self) -> None:
        rows = [
            {"kind": "wait_ready"},
            _capture(secondary=True, input_current=0x04, frame=10065),
            _capture(secondary=True, input_current=0x00, frame=10069),
            _capture(secondary=False, input_current=0x00, frame=10075),
        ]
        with tempfile.TemporaryDirectory() as directory:
            trace = Path(directory) / "trace.jsonl"
            trace.write_text(
                "".join(json.dumps(row) + "\n" for row in rows),
                encoding="utf-8",
            )
            report = build_report(trace)

        self.assertTrue(report["integrity"]["passed"])
        self.assertEqual(report["rows"]["capture"], 3)
        self.assertEqual(report["rows"]["coherent"], 3)
        self.assertEqual(
            report["input_focus_edges_between_adjacent_coherent_rows"],
            1,
        )
        transitions = report["secondary_character_transitions"]
        self.assertEqual(len(transitions), 1)
        self.assertEqual(transitions[0]["previous_frame"], 10069)
        self.assertEqual(transitions[0]["frame"], 10075)
        self.assertEqual(
            transitions[0]["mode_sensitive_bodies_after"],
            [[0x4B8A80, 0x0100114D]],
        )

    def test_incoherent_row_breaks_transition_adjacency(self) -> None:
        rows = [
            _capture(secondary=True, input_current=0x04, frame=10),
            _capture(
                secondary=True,
                input_current=0x00,
                frame=11,
                coherent=False,
            ),
            _capture(secondary=False, input_current=0x00, frame=12),
        ]
        with tempfile.TemporaryDirectory() as directory:
            trace = Path(directory) / "trace.jsonl"
            trace.write_text(
                "".join(json.dumps(row) + "\n" for row in rows),
                encoding="utf-8",
            )
            report = build_report(trace)

        self.assertTrue(report["integrity"]["passed"])
        self.assertEqual(report["rows"]["incoherent"], 1)
        self.assertEqual(report["secondary_character_transitions"], [])


if __name__ == "__main__":
    unittest.main()
