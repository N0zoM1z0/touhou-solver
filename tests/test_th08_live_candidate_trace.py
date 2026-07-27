#!/usr/bin/env python3
"""Tests for shadow candidate-verifier trace serialization."""

from __future__ import annotations

import unittest
from types import SimpleNamespace

from th08_live.candidate_trace import build_candidate_verifier_trace_record


class CandidateVerifierTraceTests(unittest.TestCase):
    def test_disabled_service_has_no_record(self) -> None:
        record = build_candidate_verifier_trace_record(
            enabled=False,
            target=None,
            eligibility=None,
            submit_revision=None,
            submit_ms=None,
            lookup_ms=None,
            publication_ms=None,
            submit_error=None,
            lookup_error=None,
            outcome=None,
            snapshot=None,
            publications=(),
            issued_mask=0,
            action_name_from_mask=lambda _mask: "stay",
        )
        self.assertIsNone(record)

    def test_completed_outcome_preserves_target_and_issued_label(self) -> None:
        root = SimpleNamespace(
            frame=10,
            row=20,
            column=8,
            observed_action="stay",
            pending_command=None,
        )
        target = SimpleNamespace(
            policy_version=(100, 90, (1, 7, None)),
            root=root,
        )
        outcome = SimpleNamespace(
            revision=7,
            target=target,
            status="feasible",
            queue_ms=0.5,
            elapsed_ms=4.0,
            horizon_frames=32,
            winning=True,
            state_label=SimpleNamespace(
                guaranteed_frames=32,
                bottleneck_margin=1.25,
            ),
            best_actions=("right",),
            action_witnesses=(),
            completed_candidates=("always_stay",),
            timed_out_candidates=(),
            unvisited_candidates=(),
            stopped_on_feasibility=True,
            budget_exhausted=False,
            background_priority_lowered=True,
            stale_at_completion=False,
            error=None,
        )

        record = build_candidate_verifier_trace_record(
            enabled=True,
            target=target,
            eligibility="boolean_losing",
            submit_revision=7,
            submit_ms=0.25,
            lookup_ms=0.1,
            publication_ms=0.05,
            submit_error=None,
            lookup_error=None,
            outcome=outcome,
            snapshot=None,
            publications=({"status": "issue_eligible"},),
            issued_mask=0x81,
            action_name_from_mask=lambda _mask: "right",
        )

        assert record is not None
        self.assertEqual(record["status"], "hit")
        self.assertEqual(record["target"]["observed_action"], "stay")
        self.assertTrue(record["result"]["issued_in_best"])
        self.assertEqual(record["publications"], ({"status": "issue_eligible"},))

    def test_status_precedence_is_deterministic(self) -> None:
        cases = (
            ("submit failed", None, None, None, "submit_error"),
            (None, "lookup failed", None, None, "lookup_error"),
            (None, None, None, "boolean_viable", "skipped_boolean_viable"),
            (None, None, None, "unavailable", "unavailable"),
        )
        for submit_error, lookup_error, target, eligibility, expected in cases:
            with self.subTest(expected=expected):
                record = build_candidate_verifier_trace_record(
                    enabled=True,
                    target=target,
                    eligibility=eligibility,
                    submit_revision=None,
                    submit_ms=None,
                    lookup_ms=None,
                    publication_ms=None,
                    submit_error=submit_error,
                    lookup_error=lookup_error,
                    outcome=None,
                    snapshot=None,
                    publications=(),
                    issued_mask=0,
                    action_name_from_mask=lambda _mask: "stay",
                )
                assert record is not None
                self.assertEqual(record["status"], expected)


if __name__ == "__main__":
    unittest.main()
