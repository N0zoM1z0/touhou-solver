#!/usr/bin/env python3
"""Focused publication-integrity regression for the physical shadow audit."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from analysis.candidate_verifier_shadow_audit import audit


class CandidateVerifierShadowAuditTests(unittest.TestCase):
    def test_exact_safe_publication_and_feasibility_gain_are_counted(
        self,
    ) -> None:
        root = {
            "frame": 10,
            "row": 20,
            "column": 8,
            "observed_action": "stay",
            "pending_action": None,
            "pending_remaining_frames": [],
        }
        version = [100, 90, [1, 7, None]]
        result = {
            "revision": 7,
            "policy_version": version,
            "root": root,
            "status": "feasible",
            "winning": True,
            "horizon_frames": 32,
            "best_actions": ["right"],
            "best_action_witnesses": [
                {
                    "root_action": "right",
                    "candidate_policy": "always_stay",
                    "survival_frames": 32,
                    "bottleneck_margin": 1.25,
                }
            ],
            "issued_action_label": {
                "root_action": "stay",
                "candidate_policy": "always_stay",
                "survival_frames": 11,
                "bottleneck_margin": -0.5,
            },
            "completed_candidates": ["always_stay"],
            "issued_in_best": False,
        }
        publication = {
            "role": "shadow_no_action_authority",
            "status": "issue_eligible",
            "issue_eligible": True,
            "revision": 7,
            "policy_version": version,
            "root": root,
            "root_action": "right",
            "candidate_policy": "always_stay",
            "would_change_action": True,
            "valid_for_issue_frame": 123,
            "expires_after_issue_frame": 123,
            "deadline_missed": False,
            "input_override": False,
            "witness_matches_result": True,
            "issue_certificate": {
                "worst_collisions": 0,
                "min_clearance": 0.5,
            },
        }
        decision = {
            "kind": "decision",
            "frame": 123,
            "read_ms": 1.0,
            "plan_ms": 2.0,
            "action_lag": 1,
            "corridor": {
                "viability": {"state_viable": False},
            },
            "candidate_verifier_shadow": {
                "status": "hit",
                "submit_ms": 0.01,
                "lookup_ms": 0.02,
                "publication_ms": 0.003,
                "result": result,
                "publications": [publication],
                "service": {},
            },
        }
        with TemporaryDirectory() as temporary:
            trace = Path(temporary) / "trace.jsonl"
            trace.write_text(
                json.dumps(decision)
                + "\n"
                + json.dumps(
                    {
                        "kind": "summary",
                        "termination_reason": "route_complete",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            report = audit(trace, baseline_dossier=None)
        self.assertEqual(
            report["schema"],
            "candidate-verifier-physical-shadow-audit-v2",
        )
        self.assertEqual(
            report["delivery"]["candidate_feasibility_gain_rows"],
            1,
        )
        self.assertEqual(
            report["publication"]["issue_eligible_change_rows"],
            1,
        )
        self.assertEqual(
            report["publication"]["eligible_feasibility_gain_rows"],
            1,
        )
        self.assertEqual(
            report["publication"]["integrity_error_count"],
            0,
        )


if __name__ == "__main__":
    unittest.main()
