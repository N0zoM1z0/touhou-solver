#!/usr/bin/env python3
"""Tests for cancellable newest-version exact-root prewarming."""

from __future__ import annotations

import concurrent.futures
import time
import unittest

import numpy as np

from touhou_control.pipeline_prewarm import (
    LatestPipelinePrewarmScheduler,
    enumerate_continuation_seed_roots,
)
from touhou_control.query_survival import (
    PendingCommand,
    PipelineWorkspaceCancelledError,
    PipelineWorkspaceDeadlineError,
    ReachablePipelineRoot,
    SurvivalQueryProblem,
    scalar_query_local_survival,
)
from touhou_control.viability import ControlAction, ViabilityConfig


class PipelinePrewarmTests(unittest.TestCase):
    def setUp(self) -> None:
        self.axis = np.arange(5, dtype=np.float32)
        self.actions = (
            ControlAction("stay", 0.0, 0.0),
            ControlAction("left", -1.0, 0.0),
            ControlAction("right", 1.0, 0.0),
            ControlAction("up", 0.0, -1.0),
            ControlAction("down", 0.0, 1.0),
        )
        rng = np.random.default_rng(777)
        self.clearance = rng.uniform(
            -1.0,
            8.0,
            size=(11, 5, 5),
        ).astype(np.float32)
        self.clearance[0, 2, 2] = 7.0
        self.config = ViabilityConfig(
            frames_per_layer=3,
            clamp_to_bounds=True,
        )
        self.problem = SurvivalQueryProblem(
            x_axis=self.axis,
            y_axis=self.axis,
            clearance_volume=self.clearance,
            actions=self.actions,
            delay_frames=(0, 1, 3),
            nominal_delay=1,
            config=self.config,
        )

    def test_continuation_bank_preserves_one_step_cadence_root(self) -> None:
        cadence_support = (1, 2, 3)
        root = ReachablePipelineRoot(
            frame=0,
            row=2,
            column=2,
            observed_action="stay",
            pending_command=PendingCommand("right", (1, 2)),
        )
        expected = scalar_query_local_survival(
            x_axis=self.axis,
            y_axis=self.axis,
            clearance_volume=self.clearance,
            actions=self.actions,
            delay_frames=self.problem.delay_frames,
            config=self.config,
            start_frame=root.frame,
            row=root.row,
            column=root.column,
            observed_action=root.observed_action,
            pending_command=root.pending_command,
            decision_frame_support=cadence_support,
        )
        seeds = enumerate_continuation_seed_roots(
            problem=self.problem,
            public_roots=(root,),
            decision_frame_support=cadence_support,
        )
        try:
            scheduler = LatestPipelinePrewarmScheduler(
                worker_count=3,
                seed_timeout_ms=200,
                specialization_timeout_ms=200,
            )
            scheduler.publish(
                problem=self.problem,
                policy_version="policy",
                seed_roots=seeds,
                decision_frame_support=cadence_support,
            )
        except RuntimeError as error:
            self.skipTest(str(error))
        with scheduler:
            self.assertTrue(
                scheduler.wait_for_seed(
                    policy_version="policy",
                    timeout=2.0,
                )
            )
            self.assertTrue(
                scheduler.submit_frontier(
                    policy_version="policy",
                    roots=(root,),
                )
            )
            self.assertTrue(
                scheduler.wait_for_frontier(
                    policy_version="policy",
                    timeout=2.0,
                )
            )
            actual = scheduler.lookup(
                policy_version="policy",
                root=root,
            )
        self.assertIsNotNone(actual)
        self.assertEqual(actual.state_label, expected.state_label)
        self.assertEqual(actual.action_labels, expected.action_labels)
        self.assertEqual(actual.best_actions, expected.best_actions)
        self.assertEqual(
            actual.workspace_stats.new_state_count,
            0,
        )

    def test_cancelled_workspace_never_computes(self) -> None:
        try:
            workspace = self.problem.build_pipeline_workspace(
                policy_version="cancel",
            )
        except RuntimeError as error:
            self.skipTest(str(error))
        with workspace:
            workspace.cancel()
            with self.assertRaises(PipelineWorkspaceCancelledError):
                workspace.query_cell(
                    policy_version="cancel",
                    frame=0,
                    row=2,
                    column=2,
                    observed_action="stay",
                )

    def test_native_deadline_aborts_cold_expansion(self) -> None:
        axis = np.arange(20, dtype=np.float32)
        clearance = np.full((81, 20, 20), 10.0, dtype=np.float32)
        problem = SurvivalQueryProblem(
            x_axis=axis,
            y_axis=axis,
            clearance_volume=clearance,
            actions=self.actions,
            delay_frames=(0, 1, 2, 3, 4, 5, 6),
            nominal_delay=3,
            config=ViabilityConfig(
                frames_per_layer=8,
                clamp_to_bounds=True,
            ),
        )
        try:
            workspace = problem.build_pipeline_workspace(
                policy_version="deadline",
            )
        except RuntimeError as error:
            self.skipTest(str(error))
        with workspace:
            with self.assertRaises(PipelineWorkspaceDeadlineError):
                workspace.query_cell(
                    policy_version="deadline",
                    frame=0,
                    row=10,
                    column=10,
                    observed_action="stay",
                    timeout_ms=1,
                )

    def test_cancel_interrupts_running_native_expansion(self) -> None:
        axis = np.arange(36, dtype=np.float32)
        clearance = np.full((121, 36, 36), 10.0, dtype=np.float32)
        problem = SurvivalQueryProblem(
            x_axis=axis,
            y_axis=axis,
            clearance_volume=clearance,
            actions=self.actions,
            delay_frames=(0, 1, 2, 3, 4, 5, 6),
            nominal_delay=3,
            config=ViabilityConfig(
                frames_per_layer=8,
                clamp_to_bounds=True,
            ),
        )
        try:
            workspace = problem.build_pipeline_workspace(
                policy_version="running-cancel",
            )
        except RuntimeError as error:
            self.skipTest(str(error))
        with workspace:
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=1
            ) as executor:
                future = executor.submit(
                    workspace.query_cell,
                    policy_version="running-cancel",
                    frame=0,
                    row=18,
                    column=18,
                    observed_action="stay",
                )
                deadline = time.monotonic() + 1.0
                while not future.running() and time.monotonic() < deadline:
                    time.sleep(0.001)
                started = time.perf_counter()
                workspace.cancel()
                with self.assertRaises(PipelineWorkspaceCancelledError):
                    future.result(timeout=1.0)
                self.assertLess(
                    (time.perf_counter() - started) * 1000.0,
                    100.0,
                )

    def test_new_publication_rejects_every_old_result(self) -> None:
        root = ReachablePipelineRoot(
            frame=0,
            row=2,
            column=2,
            observed_action="stay",
            pending_command=None,
        )
        seeds = enumerate_continuation_seed_roots(
            problem=self.problem,
            public_roots=(root,),
            decision_frame_support=(1, 2),
        )
        try:
            scheduler = LatestPipelinePrewarmScheduler(
                worker_count=2,
                seed_timeout_ms=200,
                specialization_timeout_ms=200,
            )
            first = scheduler.publish(
                problem=self.problem,
                policy_version="old",
                seed_roots=seeds,
                decision_frame_support=(1, 2),
            )
            second = scheduler.publish(
                problem=self.problem,
                policy_version="new",
                seed_roots=seeds,
                decision_frame_support=(1, 2),
            )
        except RuntimeError as error:
            self.skipTest(str(error))
        with scheduler:
            self.assertGreater(second, first)
            self.assertIsNone(
                scheduler.lookup(policy_version="old", root=root)
            )
            self.assertEqual(
                scheduler.snapshot().policy_version,
                "new",
            )
            self.assertTrue(
                scheduler.wait_for_seed(
                    policy_version="new",
                    timeout=2.0,
                )
            )


if __name__ == "__main__":
    unittest.main()
