#!/usr/bin/env python3
"""Executable gates for the first complete TH08 Lunatic failure corpus."""

from __future__ import annotations

import unittest
from pathlib import Path

from th08_fullrun_regression import (
    _action_lag_factor_expected,
    load_and_validate,
)


ROOT = Path(__file__).resolve().parent.parent
CORPUS = (
    ROOT
    / "artifacts"
    / "runtime_reports"
    / "lunatic_route2_fullrun_20260723.regressions.json"
)
ROBUST_NO_BOMB_CORPUS = (
    ROOT
    / "artifacts"
    / "runtime_reports"
    / "lunatic_route2_fullrun_robust_viability_20260723_194644.regressions.json"
)
STRICT_ENEMY_VERSION_STAGE5_CORPUS = (
    ROOT
    / "artifacts"
    / "runtime_reports"
    / "lunatic_route2_stage5_unattended_20260724_191313.regressions.json"
)


class Th08FullrunRegressionTests(unittest.TestCase):
    def test_action_lag_factor_includes_last_alive_support_miss(self) -> None:
        case = {
            "action_lag": 6,
            "control_delay_frames": 6,
            "control_delay_candidates": [5, 6],
            "last_alive_decision": {
                "action_lag": 7,
                "control_delay_frames": 6,
                "control_delay_candidates": [5, 6],
            },
        }
        self.assertTrue(_action_lag_factor_expected(case))
        case["last_alive_decision"]["action_lag"] = 6
        self.assertFalse(_action_lag_factor_expected(case))

    def test_robust_fullrun_retains_all_hard_no_bomb_failures(self) -> None:
        summary = load_and_validate(ROBUST_NO_BOMB_CORPUS)
        self.assertEqual(summary.case_count, 90)
        self.assertEqual(summary.deathbomb_count, 0)
        self.assertEqual(
            summary.stage_counts,
            {
                "Stage 1": 1,
                "Stage 2": 5,
                "Stage 3": 10,
                "Stage 4A / Reimu": 28,
                "Stage 5": 13,
                "Final B / Kaguya": 33,
            },
        )

    def test_ce_0098_stage5_retains_strict_enemy_version_failures(self) -> None:
        summary = load_and_validate(STRICT_ENEMY_VERSION_STAGE5_CORPUS)
        self.assertEqual(summary.case_count, 28)
        self.assertEqual(summary.deathbomb_count, 0)
        self.assertEqual(summary.stage_counts, {"Stage 5": 28})
        self.assertEqual(
            summary.cause_counts,
            {
                "observed_bullet_overlap": 11,
                "modeled_committed_prefix_collision": 16,
                "sensor_gap_or_unmodeled_hazard": 1,
            },
        )
        self.assertEqual(summary.exact_bullet_witnesses, 11)
        self.assertEqual(summary.exact_enemy_body_witnesses, 0)

    def test_every_retained_native_hit_is_a_valid_unique_witness(self) -> None:
        summary = load_and_validate(CORPUS)
        self.assertEqual(summary.case_count, 91)
        self.assertEqual(
            summary.stage_counts,
            {
                "Stage 1": 2,
                "Stage 2": 4,
                "Stage 3": 13,
                "Stage 4A / Reimu": 21,
                "Stage 5": 22,
                "Final B / Kaguya": 29,
            },
        )
        self.assertEqual(summary.deathbomb_count, 62)
        self.assertEqual(
            summary.factor_counts,
            {
                "playfield_boundary": 32,
                "corridor_deadline_miss": 74,
                "fast_mode": 68,
                "action_lag_over_model": 14,
                "pool_density_over_1000": 16,
            },
        )

    def test_failure_taxonomy_retains_exact_geometry_and_model_gaps(self) -> None:
        summary = load_and_validate(CORPUS)
        self.assertEqual(
            summary.cause_counts,
            {
                "sensor_gap_or_unmodeled_hazard": 20,
                "observed_bullet_overlap": 35,
                "modeled_committed_prefix_collision": 20,
                "observed_laser_overlap": 11,
                "active_laser_without_observed_overlap": 5,
            },
        )
        self.assertEqual(summary.exact_bullet_witnesses, 35)
        self.assertEqual(summary.exact_laser_witnesses, 11)


if __name__ == "__main__":
    unittest.main()
