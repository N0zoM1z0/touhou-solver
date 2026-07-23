#!/usr/bin/env python3
"""Tests for asynchronous policy timing."""

from __future__ import annotations

import unittest

from touhou_control.async_policy import AsyncPolicyLead


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

    def test_invalid_duration_is_rejected(self) -> None:
        lead = AsyncPolicyLead()
        with self.assertRaisesRegex(ValueError, "finite"):
            lead.observe(float("nan"))


if __name__ == "__main__":
    unittest.main()
