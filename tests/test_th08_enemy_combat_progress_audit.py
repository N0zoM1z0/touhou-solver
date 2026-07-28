#!/usr/bin/env python3
"""Tests for the strict physical enemy combat-progress audit."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from analysis.th08_enemy_combat_progress_audit import (
    EnemyCombatProgressAuditError,
    audit_enemy_combat_progress,
)


def _inventory(
    *,
    current_health: int,
    frame_damage: int,
    decode_ms: float = 0.05,
) -> dict[str, object]:
    return {
        "layout": "th08-enemy-combat-progress-inventory-v1",
        "authority": "trace_only",
        "scope": "ordinary_enemy_pool_first_64_capture_time_rows",
        "row_layout": (
            "slot_enemy_pointer_flags_flags2_current_hp_maximum_hp_"
            "phase_start_hp_frame_damage_local_damage_flags_open_defeat_mode"
        ),
        "field_offsets": {
            "current_health": 0x2DFC,
            "maximum_health": 0x2E00,
            "phase_start_health": 0x2E04,
            "flags": 0x3324,
            "flags2": 0x3328,
            "frame_damage": 0x3354,
        },
        "field_masks": {
            "player_shot_damage": 0x40,
            "damage_blocking": 0x830,
            "flags2_update_blocked": 0x80,
            "defeat_mode_shift": 20,
            "defeat_mode_mask": 0x7,
        },
        "scanned_slots": 64,
        "active_slots": 1,
        "rows": [
            [
                63,
                0x005826C0 + 63 * 0x53D0,
                0x1 | 0x40 | (3 << 20),
                0,
                current_health,
                100,
                100,
                frame_damage,
                True,
                3,
            ]
        ],
        "decode_ms": decode_ms,
        "record_ms": 0.02,
        "generation_authority": "none",
        "end_reason_authority": "none",
        "damageability_authority": "local_flags_only",
    }


def _observation(
    *,
    decision_frame: int,
    current_health: int,
    frame_damage: int,
    previous_emit_ms: float | None,
    decode_ms: float = 0.05,
) -> dict[str, object]:
    return {
        "schema": "th08-enemy-combat-progress-observation-v1",
        "kind": "enemy_combat_progress",
        "route_id": 2,
        "difficulty_index": 3,
        "stage_route_index": 5,
        "gameplay_epoch": 1,
        "decision_frame": decision_frame,
        "frame_before": decision_frame,
        "frame_after": decision_frame,
        "capture_attempts": 1,
        "capture_ms": 0.15,
        "previous_emit_ms": previous_emit_ms,
        "stable": True,
        "inventory": _inventory(
            current_health=current_health,
            frame_damage=frame_damage,
            decode_ms=decode_ms,
        ),
        "stage_ms": 0.04,
    }


def _write_trace(path: Path, records: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8",
        newline="\n",
    )


class EnemyCombatProgressAuditTests(unittest.TestCase):
    def test_streaming_audit_accepts_exact_progress_and_is_deterministic(
        self,
    ) -> None:
        records = [
            {"kind": "unrelated"},
            _observation(
                decision_frame=100,
                current_health=100,
                frame_damage=0,
                previous_emit_ms=None,
            ),
            _observation(
                decision_frame=102,
                current_health=90,
                frame_damage=10,
                previous_emit_ms=0.03,
            ),
        ]
        with TemporaryDirectory() as directory:
            trace = Path(directory) / "trace.jsonl"
            _write_trace(trace, records)
            first = audit_enemy_combat_progress(
                trace,
                expected_route_id=2,
                expected_difficulty_index=3,
                expected_stage_route_index=5,
            )
            second = audit_enemy_combat_progress(
                trace,
                expected_route_id=2,
                expected_difficulty_index=3,
                expected_stage_route_index=5,
            )
        self.assertTrue(first["passed"])
        self.assertEqual(first, second)
        self.assertEqual(first["observation_count"], 2)
        self.assertEqual(first["positive_frame_damage_rows"], 1)
        self.assertEqual(first["positive_hp_decrease_candidates"], 1)
        self.assertEqual(first["kill_authority"], "none")

    def test_schema_error_rejects_inconsistent_slot_pointer(self) -> None:
        record = _observation(
            decision_frame=100,
            current_health=100,
            frame_damage=1,
            previous_emit_ms=None,
        )
        inventory = record["inventory"]
        assert isinstance(inventory, dict)
        rows = inventory["rows"]
        assert isinstance(rows, list)
        rows[0][1] = 0xDEADBEEF  # type: ignore[index]
        with TemporaryDirectory() as directory:
            trace = Path(directory) / "trace.jsonl"
            _write_trace(trace, [record])
            with self.assertRaisesRegex(
                EnemyCombatProgressAuditError,
                "pointer",
            ):
                audit_enemy_combat_progress(
                    trace,
                    expected_route_id=2,
                    expected_difficulty_index=3,
                    expected_stage_route_index=5,
                )

    def test_timing_miss_is_retained_as_a_failed_gate(self) -> None:
        records = [
            _observation(
                decision_frame=100,
                current_health=100,
                frame_damage=0,
                previous_emit_ms=None,
                decode_ms=0.5,
            ),
            _observation(
                decision_frame=102,
                current_health=90,
                frame_damage=10,
                previous_emit_ms=0.03,
                decode_ms=0.5,
            ),
        ]
        with TemporaryDirectory() as directory:
            trace = Path(directory) / "trace.jsonl"
            _write_trace(trace, records)
            report = audit_enemy_combat_progress(
                trace,
                expected_route_id=2,
                expected_difficulty_index=3,
                expected_stage_route_index=5,
            )
        self.assertFalse(report["passed"])
        self.assertFalse(report["gates"]["decode_timing"])
        self.assertTrue(report["gates"]["record_timing"])


if __name__ == "__main__":
    unittest.main()
