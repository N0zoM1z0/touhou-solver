#!/usr/bin/env python3
"""Focused tests for scoped thprac no-Bomb dossiers."""

from __future__ import annotations

import unittest
from pathlib import Path

from th08_practice_dossier import (
    _adaptive_control_summary,
    _action_hold_summary,
    _behavior_context,
    _decision_cadence,
    _extract_scope,
    _input_visibility_summary,
    _no_bomb_verification,
    _promote_enemy_body_candidates,
)
from th08_fullrun_regression import load_and_validate
from th08_run_dossier import _input_mask_action


ROOT = Path(__file__).resolve().parent.parent
PRACTICE_CORPUS = (
    ROOT
    / "artifacts"
    / "runtime_reports"
    / "lunatic_route2_stage3_practice_20260723_160344.regressions.json"
)


def _decision(frame: int, *, mask: int = 5) -> dict[str, object]:
    return {
        "kind": "decision",
        "frame": frame,
        "stage_route_index": 2,
        "resources": {"lives": 8.0, "bombs": 4.0, "power": 128.0},
        "player": {
            "x": 192.0,
            "y": 384.0,
            "phase": 0,
            "phase_at_action": 0,
            "predeath_at_action": 10,
        },
        "active_bullets": 0,
        "active_lasers": 0,
        "active_items": 0,
        "action": "stay",
        "mask": mask,
        "bomb": False,
        "hit_started": False,
        "snapshot_lag": 0,
        "snapshot_frame": frame,
        "input_snapshot": {"raw": mask, "current": mask, "previous": mask},
        "action_lag": 0,
        "control_delay_frames": 3,
        "control_delay_candidates": [],
        "control_delay_estimator": {},
        "action_hold_frames": 3,
        "read_ms": 1.0,
        "plan_ms": 2.0,
        "pipeline_clearance": 9999.0,
        "minimum_clearance": 9999.0,
        "robust_control": {},
        "corridor_slack": 1.0,
        "spell": {"active": False, "flags": 0},
    }


class Th08PracticeDossierTests(unittest.TestCase):
    def test_active_input_action_is_independent_of_post_hit_output(self) -> None:
        self.assertEqual(_input_mask_action(0x95), "up_right")
        self.assertEqual(_input_mask_action(0x91), "up_right_fast")
        self.assertEqual(_input_mask_action(0x05), "stay")
        self.assertEqual(_input_mask_action(0x07), "stay+bomb")

    def test_action_hold_distribution_is_retained(self) -> None:
        rows = [_decision(100), _decision(103), _decision(106)]
        rows[0]["action_hold_frames"] = 2
        rows[2]["spell"] = {"active": True, "spell_id": 50}
        summary = _action_hold_summary(rows)
        self.assertEqual(summary["all"]["counts"], {"2": 1, "3": 2})
        self.assertEqual(
            summary["active_spell_50"]["counts"],
            {"3": 1},
        )

    def test_input_visibility_separates_actuation_from_hold(self) -> None:
        rows = [_decision(100), _decision(102), _decision(105)]
        rows[0]["mask"] = 0x11
        rows[1]["mask"] = 0x11
        rows[0]["input_snapshot"]["current"] = 0x05
        rows[1]["input_snapshot"]["current"] = 0x11
        rows[1]["snapshot_frame"] = 101
        rows[2]["mask"] = 0x41
        summary = _input_visibility_summary(rows)
        self.assertEqual(summary["unambiguous_transition_count"], 1)
        self.assertEqual(summary["visible_on_next_observation_count"], 1)
        self.assertEqual(
            summary["visible_snapshot_delta_frames"]["median"],
            1.0,
        )

    def test_adaptive_delay_distribution_and_robust_overrides_are_retained(
        self,
    ) -> None:
        rows = [_decision(100), _decision(103), _decision(106)]
        for index, row in enumerate(rows):
            row["control_delay_candidates"] = [2, 3, 4]
            row["control_delay_estimator"] = {
                "end_to_end_samples": index + 4,
                "guard_active": index == 2,
                "overruns": 1,
                "censored": 2,
            }
            row["robust_control"] = {
                "override": index == 1,
                "worst_collisions": int(index == 2),
                "min_clearance": 4.0 - 3.0 * index,
            }
        summary = _adaptive_control_summary(rows)
        self.assertEqual(summary["support_counts"], {"2,3,4": 3})
        self.assertEqual(summary["robust_override_count"], 1)
        self.assertEqual(summary["robust_collision_prediction_count"], 1)
        self.assertEqual(summary["learned_end_to_end_sample_max"], 6)
        self.assertEqual(summary["guard_active_decision_count"], 1)
        self.assertEqual(summary["overrun_max"], 1)
        self.assertEqual(summary["censored_max"], 2)

    def test_cadence_and_prehit_behavior_are_retained(self) -> None:
        rows = [_decision(100), _decision(103), _decision(107)]
        cadence = _decision_cadence(rows)
        self.assertEqual(cadence["sample_count"], 2)
        self.assertEqual(cadence["mean"], 3.5)
        rows[-1]["action"] = "left_fast"
        rows[-1]["mask"] = 0x41
        rows[-1]["player"]["y"] = 430.0
        behavior = _behavior_context(rows, [{"frame": 110}])
        prehit = behavior["alive_preceding_hit_60f"]
        self.assertEqual(prehit["sample_count"], 3)
        self.assertEqual(prehit["bottom_8px_fraction"], 1 / 3)
        self.assertEqual(prehit["fast_fraction"], 1 / 3)

    def test_retained_stage3_corpus_is_executable_and_no_bomb(self) -> None:
        summary = load_and_validate(PRACTICE_CORPUS)
        self.assertEqual(summary.case_count, 16)
        self.assertEqual(summary.deathbomb_count, 0)
        self.assertEqual(
            summary.cause_counts,
            {
                "enemy_body_contact_candidate": 1,
                "modeled_committed_prefix_collision": 6,
                "observed_bullet_overlap": 5,
                "active_laser_without_observed_overlap": 3,
                "observed_laser_overlap": 1,
            },
        )

    def test_frame_regression_excludes_thprac_reset_tail(self) -> None:
        rows = [
            _decision(100),
            _decision(102),
            {"kind": "scene_inactive", "frame": 102},
            {"kind": "scene_resumed", "frame": 1},
            _decision(1),
            {"kind": "scene_inactive", "frame": 273},
            _decision(2),
        ]
        decisions, end, scenes, excluded = _extract_scope(
            rows,
            trace_path=Path("trace.jsonl"),
        )
        self.assertEqual([row["frame"] for row in decisions], [100, 102])
        self.assertEqual(end["reason"], "frame_counter_regression")
        self.assertEqual(excluded, 2)
        self.assertEqual(
            [(row["kind"], row["frame"]) for row in scenes],
            [("scene_inactive", 102)],
        )

    def test_no_bomb_invariant_checks_mask_flag_action_and_config(self) -> None:
        clean = [_decision(100)]
        result = _no_bomb_verification(
            clean,
            ({"kind": "controller_config", "bomb_policy": "disabled"},),
        )
        self.assertTrue(result["passed"])
        dirty = [_decision(100, mask=7)]
        result = _no_bomb_verification(
            dirty,
            ({"kind": "controller_config", "bomb_policy": "disabled"},),
        )
        self.assertFalse(result["passed"])
        self.assertEqual(result["mask_violation_frames"], [100])

    def test_projectile_free_active_spell_promotes_enemy_body_candidate(
        self,
    ) -> None:
        deaths = [
            {
                "primary_cause_class": "sensor_gap_or_unmodeled_hazard",
                "active_bullets": 0,
                "active_lasers": 0,
                "pipeline_clearance_at_hit": 9999.0,
                "spell_attribution": {
                    "status": "resolved_live_spell_state",
                    "enemy_pointer": 0x5826C0,
                },
            }
        ]
        _promote_enemy_body_candidates(deaths)
        self.assertEqual(
            deaths[0]["primary_cause_class"],
            "enemy_body_contact_candidate",
        )
        self.assertTrue(
            deaths[0]["enemy_body_evidence"][
                "canonical_fresh_attempt_sample"
            ]
        )


if __name__ == "__main__":
    unittest.main()
