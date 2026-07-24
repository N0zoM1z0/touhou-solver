#!/usr/bin/env python3
"""Small deterministic gates for the adversarial differential harness."""

from __future__ import annotations

import unittest

from analysis.adversarial_planner_diff import compare_scenario
from touhou_control.adversarial import generate_adversarial_scenario


class AdversarialPlannerDiffTests(unittest.TestCase):
    def test_random_piecewise_scenarios_match_reference_oracle(self) -> None:
        for seed in (3, 17, 8008, 0xBAD5EED):
            with self.subTest(seed=seed):
                scenario = generate_adversarial_scenario(
                    seed,
                    hazard_count=48,
                    horizon_frames=8,
                    maximum_events=3,
                )
                report = compare_scenario(
                    scenario,
                    grid_step=32.0,
                )
                self.assertTrue(report["passed"], report)

    def test_generator_is_seed_stable_and_can_exceed_native_pool_density(
        self,
    ) -> None:
        first = generate_adversarial_scenario(
            8008,
            hazard_count=1600,
            horizon_frames=2,
        )
        second = generate_adversarial_scenario(
            8008,
            hazard_count=1600,
            horizon_frames=2,
        )
        self.assertEqual(first, second)
        self.assertGreater(len(first.hazards), 1536)

    def test_generator_can_delay_births_without_moving_them_into_adapters(
        self,
    ) -> None:
        scenario = generate_adversarial_scenario(
            0xCE0092,
            hazard_count=64,
            horizon_frames=8,
            maximum_birth_frame=6,
        )
        self.assertTrue(
            any(hazard.active_from_frame > 0 for hazard in scenario.hazards)
        )
        self.assertTrue(
            all(0 <= hazard.active_from_frame <= 6 for hazard in scenario.hazards)
        )


if __name__ == "__main__":
    unittest.main()
