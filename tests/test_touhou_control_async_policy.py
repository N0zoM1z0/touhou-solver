#!/usr/bin/env python3
"""Tests for asynchronous policy timing."""

from __future__ import annotations

import unittest

from touhou_control.async_policy import (
    AsyncPolicyLead,
    delay_support_envelope,
)


class AsyncPolicyLeadTests(unittest.TestCase):
    def test_initial_lead_covers_the_first_warm_solve(self) -> None:
        lead = AsyncPolicyLead(initial_frames=80)
        self.assertEqual(lead.frames, 80)
        lead.observe(1000.0)
        self.assertEqual(lead.frames, 80)

    def test_slow_solve_moves_policy_epoch_forward_immediately(self) -> None:
        lead = AsyncPolicyLead(initial_frames=80, overlap_frames=8)
        lead.observe(2000.0)
        self.assertEqual(lead.frames, 112)

    def test_rolling_p90_ignores_one_fast_outlier(self) -> None:
        lead = AsyncPolicyLead(initial_frames=80, overlap_frames=6)
        for solve_ms in (1200.0, 1250.0, 1300.0, 400.0):
            lead.observe(solve_ms)
        self.assertEqual(lead.frames, 72)

    def test_warm_fast_worker_can_shrink_below_legacy_48_frame_floor(
        self,
    ) -> None:
        lead = AsyncPolicyLead(
            initial_frames=80,
            overlap_frames=8,
            minimum_frames=16,
        )
        for _ in range(4):
            lead.observe(400.0)
        self.assertEqual(lead.p90_solve_frames, 24)
        self.assertEqual(lead.frames, 16)
        self.assertEqual(lead.serial_coverage_margin(80), 56)

    def test_invalid_duration_is_rejected(self) -> None:
        lead = AsyncPolicyLead()
        with self.assertRaisesRegex(ValueError, "finite"):
            lead.observe(float("nan"))

    def test_serial_serviceability_requires_solve_inside_horizon(
        self,
    ) -> None:
        lead = AsyncPolicyLead(initial_frames=48, overlap_frames=8)
        for _ in range(4):
            lead.observe(500.0)
        self.assertEqual(lead.p90_solve_frames, 30)
        self.assertEqual(lead.serial_coverage_margin(80), 32)
        self.assertTrue(lead.serial_worker_serviceable(80))
        lead.observe(2000.0)
        self.assertEqual(lead.p90_solve_frames, 120)
        self.assertFalse(lead.serial_worker_serviceable(80))

    def test_delay_envelope_covers_one_step_estimator_drift(self) -> None:
        self.assertEqual(
            delay_support_envelope(
                (2, 3, 4),
                minimum=1,
                maximum=6,
            ),
            (1, 2, 3, 4, 5),
        )
        self.assertEqual(
            delay_support_envelope(
                (1, 2, 3, 4, 5, 6),
                minimum=1,
                maximum=6,
            ),
            (1, 2, 3, 4, 5, 6),
        )


if __name__ == "__main__":
    unittest.main()
