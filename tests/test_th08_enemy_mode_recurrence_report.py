#!/usr/bin/env python3
"""Tests for physical TH08 player-mode recurrence reports."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from analysis.th08_enemy_mode_recurrence_report import build_report


def _decision(
    *,
    frame: int,
    mode_state: tuple[int, bool, int],
    focus: bool,
    coherent: bool = True,
    pending_focus: bool | None = None,
    target_focus: bool | None = None,
    action_authority: bool = False,
    player_phase: int = 3,
) -> dict[str, object]:
    mask = 0x05 if focus else 0x01
    pending_mask = None if pending_focus is None else (0x05 if pending_focus else 0x01)
    target_mask = mask if target_focus is None else (0x05 if target_focus else 0x01)
    return {
        "kind": "decision",
        "frame": frame,
        "gameplay_epoch": 1,
        "stage_route_index": 5,
        "local_pipeline_root": {
            "canonical_status": "available",
            "estimator_consistent": True,
            "active_mask": mask,
            "held_desired_mask": mask,
            "pending_mask": pending_mask,
        },
        "input_dispatch": {
            "target_mask": target_mask,
        },
        "player_enemy_mode_capture": {
            "role": "diagnostic_shadow",
            "coherent": coherent,
            "enemy_frame_after": frame,
            "action_authority": action_authority,
            "player_after": {
                "input_current": mask,
                "phase": player_phase,
                "focus_logic": mode_state[0],
                "secondary_character_active": mode_state[1],
                "focus_transition_counter": mode_state[2],
                "bomb_active": 0,
                "effective_focus": focus,
            },
        },
    }


def _report(rows: list[dict[str, object]]) -> dict[str, object]:
    with tempfile.TemporaryDirectory() as directory:
        trace = Path(directory) / "trace.jsonl"
        trace.write_text(
            "".join(json.dumps(row) + "\n" for row in rows),
            encoding="utf-8",
        )
        return build_report(trace)


class EnemyModeRecurrenceReportTests(unittest.TestCase):
    def test_constant_focus_intervals_match_native_recurrence(self) -> None:
        report = _report(
            [
                _decision(
                    frame=10,
                    mode_state=(0, False, 0),
                    focus=False,
                ),
                _decision(
                    frame=13,
                    mode_state=(0, False, 3),
                    focus=False,
                ),
                _decision(
                    frame=20,
                    mode_state=(0, False, 10),
                    focus=False,
                ),
                _decision(
                    frame=30,
                    mode_state=(1, False, 6),
                    focus=True,
                ),
                _decision(
                    frame=31,
                    mode_state=(1, True, 7),
                    focus=True,
                ),
            ]
        )
        self.assertTrue(report["integrity"]["passed"])
        intervals = report["intervals"]
        self.assertEqual(intervals["adjacent_coherent"], 4)
        self.assertEqual(intervals["eligible"], 3)
        self.assertEqual(intervals["matched"], 3)
        self.assertEqual(intervals["mismatched"], 0)
        self.assertEqual(
            intervals["exclusion_counts"],
            {"effective_focus_changed": 1},
        )
        self.assertEqual(
            intervals["manager_delta_counts"],
            {"1": 1, "3": 1, "7": 1},
        )
        self.assertFalse(
            report["scope"]["manager_frame_universal_physical_clock_authority"]
        )
        self.assertFalse(report["scope"]["action_authority"])

    def test_pending_or_dispatched_focus_edge_excludes_interval(self) -> None:
        report = _report(
            [
                _decision(
                    frame=1,
                    mode_state=(0, False, 0),
                    focus=False,
                    pending_focus=True,
                ),
                _decision(
                    frame=2,
                    mode_state=(0, False, 1),
                    focus=False,
                    target_focus=True,
                ),
                _decision(
                    frame=3,
                    mode_state=(0, False, 2),
                    focus=False,
                ),
                _decision(
                    frame=4,
                    mode_state=(0, False, 3),
                    focus=False,
                ),
            ]
        )
        self.assertTrue(report["integrity"]["passed"])
        self.assertEqual(report["intervals"]["eligible"], 1)
        self.assertEqual(
            report["intervals"]["exclusion_counts"],
            {
                "dispatch_target_focus_mismatch": 1,
                "pending_mask_focus_mismatch": 1,
            },
        )

    def test_incoherent_capture_breaks_adjacency(self) -> None:
        report = _report(
            [
                _decision(
                    frame=1,
                    mode_state=(0, False, 0),
                    focus=False,
                ),
                _decision(
                    frame=2,
                    mode_state=(0, False, 1),
                    focus=False,
                    coherent=False,
                ),
                _decision(
                    frame=3,
                    mode_state=(0, False, 2),
                    focus=False,
                ),
                _decision(
                    frame=4,
                    mode_state=(0, False, 3),
                    focus=False,
                ),
            ]
        )
        self.assertTrue(report["integrity"]["passed"])
        self.assertEqual(report["rows"]["coherent"], 3)
        self.assertEqual(report["intervals"]["adjacent_coherent"], 1)
        self.assertEqual(report["intervals"]["matched"], 1)

    def test_native_player_phases_one_and_two_suppress_mode_update(
        self,
    ) -> None:
        report = _report(
            [
                _decision(
                    frame=1,
                    mode_state=(0, False, 1),
                    focus=False,
                    player_phase=2,
                ),
                _decision(
                    frame=4,
                    mode_state=(0, False, 1),
                    focus=False,
                    player_phase=2,
                ),
                _decision(
                    frame=5,
                    mode_state=(0, False, 2),
                    focus=False,
                    player_phase=3,
                ),
                _decision(
                    frame=6,
                    mode_state=(0, False, 3),
                    focus=False,
                    player_phase=3,
                ),
            ]
        )
        self.assertTrue(report["integrity"]["passed"])
        self.assertEqual(report["intervals"]["eligible"], 1)
        self.assertEqual(
            report["intervals"]["exclusion_counts"],
            {
                "mode_update_suppressed_player_phase": 1,
                "player_phase_changed": 1,
            },
        )

    def test_nondecision_clock_boundary_is_retained_and_excluded(self) -> None:
        report = _report(
            [
                _decision(
                    frame=1,
                    mode_state=(0, False, 0),
                    focus=False,
                ),
                {"kind": "auto_confirm_wall_pulse", "frame": 1},
                _decision(
                    frame=1801,
                    mode_state=(0, False, 80),
                    focus=False,
                ),
                _decision(
                    frame=1802,
                    mode_state=(0, False, 81),
                    focus=False,
                ),
            ]
        )
        self.assertTrue(report["integrity"]["passed"])
        self.assertEqual(report["intervals"]["eligible"], 1)
        self.assertEqual(report["intervals"]["matched"], 1)
        self.assertEqual(
            report["intervals"]["exclusion_counts"],
            {"intervening_nondecision_trace_record": 1},
        )
        self.assertEqual(
            report["intervals"]["intervening_nondecision_kind_counts"],
            {"auto_confirm_wall_pulse": 1},
        )
        boundaries = report["retained_clock_boundary_intervals"]
        self.assertEqual(len(boundaries), 1)
        self.assertEqual(boundaries[0]["manager_delta"], 1800)

    def test_recurrence_mismatch_and_authority_tamper_fail_integrity(
        self,
    ) -> None:
        report = _report(
            [
                _decision(
                    frame=1,
                    mode_state=(0, False, 0),
                    focus=False,
                    action_authority=True,
                ),
                _decision(
                    frame=2,
                    mode_state=(0, False, 9),
                    focus=False,
                ),
            ]
        )
        self.assertFalse(report["integrity"]["passed"])
        self.assertEqual(report["intervals"]["mismatched"], 1)
        self.assertEqual(len(report["retained_mismatches"]), 1)
        errors = report["integrity"]["errors"]
        self.assertEqual(errors["recurrence_mismatch_count"], 1)
        self.assertEqual(
            errors["capture_action_authority_true_or_missing_lines"],
            [1],
        )


if __name__ == "__main__":
    unittest.main()
