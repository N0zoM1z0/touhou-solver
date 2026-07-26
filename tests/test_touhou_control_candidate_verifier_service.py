#!/usr/bin/env python3
"""Tests for bounded newest-target candidate verification."""

from __future__ import annotations

import threading
import unittest
from unittest.mock import patch

import numpy as np

from touhou_control.candidate_verifier_service import (
    CandidateVerifierService,
    CandidateVerifierTarget,
)
from touhou_control.policy_synthesis import (
    evaluate_candidate_policy_portfolio,
)
from touhou_control.query_survival import (
    ReachablePipelineRoot,
    SurvivalQueryProblem,
)
from touhou_control.viability import ControlAction, ViabilityConfig


class CandidateVerifierServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        axis = np.arange(7, dtype=np.float32)
        self.problem = SurvivalQueryProblem(
            x_axis=axis,
            y_axis=axis,
            clearance_volume=np.full(
                (17, 7, 7),
                10.0,
                dtype=np.float32,
            ),
            actions=(
                ControlAction("stay", 0.0, 0.0),
                ControlAction("left", -1.0, 0.0),
                ControlAction("right", 1.0, 0.0),
            ),
            delay_frames=(0, 1, 2),
            nominal_delay=1,
            config=ViabilityConfig(
                frames_per_layer=4,
                clamp_to_bounds=True,
            ),
        )

    @staticmethod
    def target(
        version: str,
        frame: int,
        column: int,
    ) -> CandidateVerifierTarget:
        return CandidateVerifierTarget(
            policy_version=version,
            root=ReachablePipelineRoot(
                frame=frame,
                row=3,
                column=column,
                observed_action="stay",
                pending_command=None,
            ),
        )

    def test_completed_exact_target_is_lookup_only_hit(self) -> None:
        target = self.target("policy-a", 2, 3)
        with CandidateVerifierService(
            horizon_frames=8,
            decision_frame_support=(2, 3, 4),
        ) as service:
            revision = service.submit(
                problem=self.problem,
                target=target,
            )
            self.assertEqual(revision, 1)
            self.assertTrue(service.wait_until_idle(2.0))
            outcome = service.lookup(target)
            mismatch = service.lookup(self.target("policy-b", 2, 3))
            snapshot = service.snapshot()
        self.assertIsNotNone(outcome)
        assert outcome is not None
        self.assertEqual(outcome.status, "feasible")
        self.assertTrue(outcome.winning)
        self.assertEqual(
            {witness.root_action for witness in outcome.action_witnesses},
            {action.name for action in self.problem.actions},
        )
        self.assertTrue(
            all(
                witness.candidate_policy
                in outcome.completed_candidates
                for witness in outcome.action_witnesses
            )
        )
        self.assertIsNone(mismatch)
        self.assertEqual(snapshot.lookup_hit_count, 1)
        self.assertEqual(snapshot.lookup_miss_count, 1)

    def test_busy_service_keeps_only_newest_queued_target(self) -> None:
        first = self.target("policy-a", 0, 2)
        superseded = self.target("policy-a", 1, 3)
        newest = self.target("policy-b", 2, 4)
        started = threading.Event()
        release = threading.Event()
        call_count = 0

        def blocking_evaluate(**arguments):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                started.set()
                self.assertTrue(release.wait(timeout=2.0))
            return evaluate_candidate_policy_portfolio(**arguments)

        with patch(
            "touhou_control.candidate_verifier_service."
            "evaluate_candidate_policy_portfolio",
            side_effect=blocking_evaluate,
        ):
            with CandidateVerifierService(
                horizon_frames=8,
                decision_frame_support=(2, 3, 4),
            ) as service:
                service.submit(problem=self.problem, target=first)
                self.assertTrue(started.wait(timeout=1.0))
                service.submit(problem=self.problem, target=superseded)
                newest_revision = service.submit(
                    problem=self.problem,
                    target=newest,
                )
                release.set()
                self.assertTrue(service.wait_until_idle(2.0))
                outcomes = service.outcomes()
                snapshot = service.snapshot()
                newest_outcome = service.lookup(newest)
        self.assertEqual(newest_revision, 3)
        self.assertEqual(
            [outcome.revision for outcome in outcomes],
            [1, 3],
        )
        self.assertTrue(outcomes[0].stale_at_completion)
        self.assertEqual(snapshot.target_replacement_count, 1)
        self.assertEqual(snapshot.stale_completion_count, 1)
        self.assertIsNotNone(newest_outcome)

    def test_discard_invalidates_running_and_drops_queued_target(self) -> None:
        first = self.target("policy-a", 0, 2)
        queued = self.target("policy-a", 1, 3)
        started = threading.Event()
        release = threading.Event()

        def blocking_evaluate(**arguments):
            started.set()
            self.assertTrue(release.wait(timeout=2.0))
            return evaluate_candidate_policy_portfolio(**arguments)

        with patch(
            "touhou_control.candidate_verifier_service."
            "evaluate_candidate_policy_portfolio",
            side_effect=blocking_evaluate,
        ):
            with CandidateVerifierService(
                horizon_frames=8,
                decision_frame_support=(2, 3, 4),
            ) as service:
                service.submit(problem=self.problem, target=first)
                self.assertTrue(started.wait(timeout=1.0))
                service.submit(problem=self.problem, target=queued)
                self.assertTrue(service.discard_target())
                release.set()
                self.assertTrue(service.wait_until_idle(2.0))
                outcomes = service.outcomes()
                snapshot = service.snapshot()
        self.assertEqual([item.revision for item in outcomes], [1])
        self.assertTrue(outcomes[0].stale_at_completion)
        self.assertEqual(snapshot.target_discard_count, 1)
        self.assertFalse(snapshot.target_queued)


if __name__ == "__main__":
    unittest.main()
