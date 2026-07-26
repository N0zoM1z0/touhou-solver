#!/usr/bin/env python3
"""Focused authority-boundary tests for candidate counterfactuals."""

from __future__ import annotations

import unittest

from analysis.candidate_witness_counterfactual_audit import (
    issue_certificate_lower_bound,
)


class CandidateWitnessCounterfactualTests(unittest.TestCase):
    def test_alternate_candidate_action_is_not_inferred_safe_from_trace(self) -> None:
        row = {
            "deadline_guard": {"missed": False},
            "robust_control": {
                "worst_collisions": 0,
                "min_clearance": 12.0,
            },
        }
        result = issue_certificate_lower_bound(
            row,
            candidate_best_actions=("left",),
            issued_action="right",
        )
        self.assertFalse(result["available"])
        self.assertIsNone(result["safe"])
        self.assertEqual(
            result["status"],
            "alternate_action_certificate_not_retained",
        )

    def test_issued_candidate_action_requires_nonnegative_hard_certificate(
        self,
    ) -> None:
        row = {
            "deadline_guard": {"missed": False},
            "robust_control": {
                "worst_collisions": 0,
                "min_clearance": -0.25,
                "cvar_risk": 3.0,
                "worst_delay": 4,
            },
        }
        result = issue_certificate_lower_bound(
            row,
            candidate_best_actions=("left", "stay"),
            issued_action="left",
        )
        self.assertTrue(result["available"])
        self.assertFalse(result["safe"])
        self.assertEqual(
            result["status"],
            "issued_candidate_action_unsafe",
        )


if __name__ == "__main__":
    unittest.main()
