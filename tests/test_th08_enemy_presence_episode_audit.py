#!/usr/bin/env python3
"""Tests for the observation-bounded enemy presence-episode audit."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from analysis.enemy_combat_progress_audit.schema import (
    EnemyCombatProgressAuditError,
)
from analysis.th08_enemy_presence_episode_audit import (
    audit_enemy_presence_episodes,
)


def _inventory(rows: list[list[object]]) -> dict[str, object]:
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
        "active_slots": len(rows),
        "rows": rows,
        "decode_ms": 0.01,
        "record_ms": 0.01,
        "generation_authority": "none",
        "end_reason_authority": "none",
        "damageability_authority": "local_flags_only",
    }


def _row(slot: int, hp: int, damage: int = 0) -> list[object]:
    return [
        slot,
        0x005826C0 + slot * 0x53D0,
        0x1 | 0x40,
        0,
        hp,
        100,
        100,
        damage,
        True,
        0,
    ]


def _observation(
    frame: int,
    rows: list[list[object]],
    *,
    epoch: int = 0,
) -> dict[str, object]:
    return {
        "schema": "th08-enemy-combat-progress-observation-v1",
        "kind": "enemy_combat_progress",
        "route_id": 2,
        "difficulty_index": 3,
        "stage_route_index": 5,
        "gameplay_epoch": epoch,
        "decision_frame": frame,
        "frame_before": frame,
        "frame_after": frame,
        "capture_attempts": 1,
        "capture_ms": 0.01,
        "previous_emit_ms": None,
        "stable": True,
        "inventory": _inventory(rows),
        "stage_ms": 0.01,
    }


def _write(path: Path, records: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8",
        newline="\n",
    )


class EnemyPresenceEpisodeAuditTests(unittest.TestCase):
    def test_presence_windows_and_damage_candidate_are_deterministic(self) -> None:
        records = [
            {"kind": "unrelated", "payload": [1, 2, 3]},
            _observation(1, [_row(0, 100)]),
            _observation(2, [_row(0, 80, 20), _row(1, 50)]),
            _observation(4, [_row(1, 50)]),
            _observation(5, []),
            _observation(1, [_row(0, 100)], epoch=1),
        ]
        with TemporaryDirectory() as directory:
            path = Path(directory) / "trace.jsonl"
            _write(path, records)
            first = audit_enemy_presence_episodes(
                path,
                expected_route_id=2,
                expected_difficulty_index=3,
                expected_stage_route_index=5,
            )
            second = audit_enemy_presence_episodes(
                path,
                expected_route_id=2,
                expected_difficulty_index=3,
                expected_stage_route_index=5,
            )
        self.assertEqual(first, second)
        self.assertEqual(first["presence_episode_count"], 3)
        self.assertEqual(first["ended_presence_episode_count"], 2)
        self.assertEqual(first["right_censored_presence_episode_count"], 1)
        self.assertEqual(
            first["classification"]["damage_adjacent_candidate_count"],
            1,
        )
        candidate = first["damage_adjacent_disappearance_candidates"][0]
        self.assertEqual(candidate["slot"], 0)
        self.assertEqual(
            candidate["end_window"],
            {"after_frame": 2, "at_or_before_frame": 4},
        )
        self.assertEqual(first["classification"]["verified_kill_count"], 0)

    def test_nonincreasing_epoch_frame_fails_closed(self) -> None:
        records = [
            _observation(2, [_row(0, 100)]),
            _observation(2, [_row(0, 90, 10)]),
        ]
        with TemporaryDirectory() as directory:
            path = Path(directory) / "trace.jsonl"
            _write(path, records)
            with self.assertRaises(EnemyCombatProgressAuditError):
                audit_enemy_presence_episodes(
                    path,
                    expected_route_id=2,
                    expected_difficulty_index=3,
                    expected_stage_route_index=5,
                )


if __name__ == "__main__":
    unittest.main()
