#!/usr/bin/env python3
"""Focused tests for scoped thprac no-Bomb dossiers."""

from __future__ import annotations

import unittest
from pathlib import Path

from th08_practice_dossier import (
    _behavior_context,
    _decision_cadence,
    _extract_scope,
    _no_bomb_verification,
    _promote_enemy_body_candidates,
)
from th08_fullrun_regression import load_and_validate


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
        "action_lag": 0,
        "read_ms": 1.0,
        "plan_ms": 2.0,
        "pipeline_clearance": 9999.0,
        "minimum_clearance": 9999.0,
        "corridor_slack": 1.0,
        "spell": {"active": False, "flags": 0},
    }


class Th08PracticeDossierTests(unittest.TestCase):
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
