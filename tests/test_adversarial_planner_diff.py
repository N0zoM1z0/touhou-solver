#!/usr/bin/env python3
"""Small deterministic gates for the adversarial differential harness."""

from __future__ import annotations

import unittest

from adversarial_planner_diff import compare_scenario
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


if __name__ == "__main__":
    unittest.main()
