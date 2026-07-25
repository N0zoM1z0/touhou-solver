#!/usr/bin/env python3
"""Tests for asynchronous exact-root target orchestration."""

from __future__ import annotations

import threading
import unittest
from unittest.mock import patch

import numpy as np

from touhou_control.pipeline_prewarm_service import PipelinePrewarmService
from touhou_control.pipeline_prewarm import (
    enumerate_continuation_seed_roots,
)
from touhou_control.query_survival import (
    ReachablePipelineRoot,
    SurvivalQueryProblem,
)
from touhou_control.viability import ControlAction, ViabilityConfig


class PipelinePrewarmServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.axis = np.arange(7, dtype=np.float32)
        self.actions = (
            ControlAction("stay", 0.0, 0.0),
            ControlAction("left", -1.0, 0.0),
            ControlAction("right", 1.0, 0.0),
        )
        self.problem = SurvivalQueryProblem(
            x_axis=self.axis,
            y_axis=self.axis,
            clearance_volume=np.full(
                (17, 7, 7),
                10.0,
                dtype=np.float32,
            ),
            actions=self.actions,
            delay_frames=(0, 1, 2, 3),
            nominal_delay=1,
            config=ViabilityConfig(
                frames_per_layer=4,
                clamp_to_bounds=True,
            ),
        )

    def test_initial_target_becomes_lookup_only_hit(self) -> None:
        root = ReachablePipelineRoot(2, 3, 3, "stay", None)
        try:
            service = PipelinePrewarmService(
                problem=self.problem,
                policy_version="policy",
                initial_roots=(root,),
                decision_frame_support=(2, 3, 4),
                worker_count=3,
            )
        except RuntimeError as error:
            self.skipTest(str(error))
        with service:
            self.assertTrue(service.wait_until_idle(2.0))
            result = service.lookup(root)
            snapshot = service.snapshot()
        self.assertIsNotNone(result)
        self.assertEqual(snapshot.ready_revision, 1)
        self.assertEqual(snapshot.lookup_hit_count, 1)
        self.assertEqual(
            snapshot.latest_outcome.status,
            "ready",
        )

    def test_busy_service_retains_only_newest_queued_target(self) -> None:
        initial = ReachablePipelineRoot(0, 3, 3, "stay", None)
        second = ReachablePipelineRoot(2, 3, 2, "left", None)
        newest = ReachablePipelineRoot(3, 3, 4, "right", None)
        initial_started = threading.Event()
        release_initial = threading.Event()
        call_count = 0

        def blocking_enumeration(**arguments):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                initial_started.set()
                self.assertTrue(release_initial.wait(timeout=2.0))
            return enumerate_continuation_seed_roots(**arguments)

        with patch(
            "touhou_control.pipeline_prewarm_service."
            "enumerate_continuation_seed_roots",
            side_effect=blocking_enumeration,
        ):
            try:
                service = PipelinePrewarmService(
                    problem=self.problem,
                    policy_version="policy",
                    initial_roots=(initial,),
                    decision_frame_support=(2, 3, 4),
                    worker_count=3,
                )
            except RuntimeError as error:
                self.skipTest(str(error))
            with service:
                self.assertTrue(initial_started.wait(timeout=1.0))
                service.retarget((second,))
                newest_revision = service.retarget((newest,))
                release_initial.set()
                self.assertTrue(service.wait_until_idle(2.0))
                outcomes = service.outcomes()
                snapshot = service.snapshot()
                newest_result = service.lookup(newest)
        self.assertEqual(newest_revision, 3)
        self.assertEqual(
            [outcome.revision for outcome in outcomes],
            [1, 3],
        )
        self.assertEqual(snapshot.target_replacement_count, 1)
        self.assertIsNotNone(newest_result)


if __name__ == "__main__":
    unittest.main()
