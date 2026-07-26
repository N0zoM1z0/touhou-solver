#!/usr/bin/env python3
"""Authority-boundary tests for candidate witness publication."""

from __future__ import annotations

import unittest
from dataclasses import replace

from th08_live_dodge_agent import (
    RobustActionCertificate,
    _candidate_outcome_record,
    _candidate_shadow_publications,
)
from touhou_control.candidate_verifier_service import (
    CandidateVerifierOutcome,
    CandidateVerifierTarget,
)
from touhou_control.policy_synthesis import CandidateActionWitness
from touhou_control.query_survival import ReachablePipelineRoot
from touhou_control.reachability_oracle import SurvivalLabel


class CandidateWitnessPublicationTests(unittest.TestCase):
    @staticmethod
    def outcome() -> CandidateVerifierOutcome:
        winning = SurvivalLabel(32, 1.25)
        issued = SurvivalLabel(11, -0.5)
        return CandidateVerifierOutcome(
            revision=7,
            target=CandidateVerifierTarget(
                policy_version=(100, 90, (1, 7, None)),
                root=ReachablePipelineRoot(
                    frame=10,
                    row=20,
                    column=8,
                    observed_action="stay",
                    pending_command=None,
                ),
            ),
            status="feasible",
            queue_ms=0.5,
            elapsed_ms=4.0,
            horizon_frames=32,
            state_label=winning,
            best_actions=("right",),
            action_witnesses=(
                CandidateActionWitness(
                    root_action="stay",
                    label=issued,
                    candidate_policy="always_stay",
                ),
                CandidateActionWitness(
                    root_action="right",
                    label=winning,
                    candidate_policy="always_stay",
                ),
            ),
            completed_candidates=("always_stay",),
            stopped_on_feasibility=True,
        )

    @staticmethod
    def certificate(
        *,
        collisions: int = 0,
        clearance: float = 0.5,
    ) -> RobustActionCertificate:
        return RobustActionCertificate(
            action="right",
            delay_frames=(3, 4, 5, 6),
            worst_collisions=collisions,
            min_clearance=clearance,
            cvar_risk=0.0,
            worst_delay=6,
        )

    def test_record_retains_best_witness_and_issued_action_label(self) -> None:
        record = _candidate_outcome_record(
            self.outcome(),
            issued_action="stay",
        )
        assert record is not None
        self.assertEqual(
            record["best_action_witnesses"],
            (
                {
                    "root_action": "right",
                    "candidate_policy": "always_stay",
                    "survival_frames": 32,
                    "bottleneck_margin": 1.25,
                },
            ),
        )
        self.assertEqual(
            record["issued_action_label"]["survival_frames"],
            11,
        )

    def test_safe_publication_is_one_shot_and_shadow_only(self) -> None:
        publications = _candidate_shadow_publications(
            self.outcome(),
            issue_action_certificates=(self.certificate(),),
            issued_action="stay",
            issue_frame=123,
            deadline_missed=False,
        )
        self.assertEqual(len(publications), 1)
        publication = publications[0]
        self.assertEqual(
            publication["role"],
            "shadow_no_action_authority",
        )
        self.assertEqual(publication["status"], "issue_eligible")
        self.assertTrue(publication["would_change_action"])
        self.assertEqual(publication["valid_for_issue_frame"], 123)
        self.assertEqual(publication["expires_after_issue_frame"], 123)
        self.assertEqual(publication["root"]["observed_action"], "stay")

    def test_missing_unsafe_or_expired_certificate_never_qualifies(self) -> None:
        cases = (
            ((), False, False, "issue_certificate_missing"),
            (
                (self.certificate(collisions=1),),
                False,
                False,
                "issue_certificate_unsafe",
            ),
            (
                (self.certificate(),),
                True,
                False,
                "deadline_missed",
            ),
            (
                (self.certificate(),),
                False,
                True,
                "input_override",
            ),
        )
        for certificates, deadline_missed, input_override, expected in cases:
            with self.subTest(expected=expected):
                publication = _candidate_shadow_publications(
                    self.outcome(),
                    issue_action_certificates=certificates,
                    issued_action="stay",
                    issue_frame=123,
                    deadline_missed=deadline_missed,
                    input_override=input_override,
                )[0]
                self.assertEqual(publication["status"], expected)
                self.assertFalse(publication["issue_eligible"])

    def test_inconsistent_witness_never_qualifies(self) -> None:
        outcome = self.outcome()
        corrupted = replace(
            outcome,
            action_witnesses=(
                outcome.action_witnesses[0],
                replace(
                    outcome.action_witnesses[1],
                    label=SurvivalLabel(31, 1.25),
                ),
            ),
        )
        publication = _candidate_shadow_publications(
            corrupted,
            issue_action_certificates=(self.certificate(),),
            issued_action="stay",
            issue_frame=123,
            deadline_missed=False,
        )[0]
        self.assertEqual(
            publication["status"],
            "witness_result_mismatch",
        )
        self.assertFalse(publication["issue_eligible"])


if __name__ == "__main__":
    unittest.main()
