#!/usr/bin/env python3
"""Tests for the extracted asynchronous corridor runtime boundary."""

from __future__ import annotations

import math
import unittest
from concurrent.futures import Future
from pathlib import Path
from unittest.mock import patch

import numpy as np

from corridor_planner import CorridorPlan
from th08_corridor_audit import CorridorAuditSubmission
from th08_corridor_runtime import (
    CorridorPolicyArtifact,
    CorridorPublication,
    CorridorRuntimeHandles,
    CorridorSolution,
    LIVE_REFINEMENT_GRID_STEPS,
    LIVE_SURVIVAL_LABELS,
    SHADOW_REFINEMENT_GRID_STEPS,
    SHADOW_SURVIVAL_LABELS,
    corridor_pipeline_survival_query,
    corridor_viability_query,
    prepare_pipeline_survival_workspace,
    require_corridor_background_priority,
    solve_corridor,
)
from touhou_control.viability import (
    ControlAction,
    RobustViabilityPolicy,
    ViabilityConfig,
)
from th08_time_scale import (
    IncompleteTimeScaleScheduleError,
    TH08_UNIT_TIME_SCALE_BITS,
    Th08TimeScaleSchedule,
    UnsupportedTimeScaleScheduleError,
)


_UNIT_SCALE = Th08TimeScaleSchedule.constant(
    TH08_UNIT_TIME_SCALE_BITS,
    horizon=128,
    provenance="corridor_runtime_test_fixture",
)


class Th08CorridorRuntimeTests(unittest.TestCase):
    def test_scale_coverage_and_nonunit_corridor_are_explicit_unknown(self) -> None:
        common = {
            "source_frame": 100,
            "snapshot_frame": 90,
            "forecast_lead_frames": 10,
            "player_x": 192.0,
            "player_y": 400.0,
            "bullets": (),
            "lasers": (),
            "enemy_bodies": (),
            "snapshot_lag": 0,
            "control_delay_candidates": (1, 2),
            "nominal_control_delay": 1,
            "active_action": "stay",
        }
        with self.assertRaises(IncompleteTimeScaleScheduleError):
            solve_corridor(
                **common,
                time_scale_schedule=(
                    Th08TimeScaleSchedule.root_observation(
                        TH08_UNIT_TIME_SCALE_BITS,
                        source_frame=90,
                    )
                ),
            )
        with self.assertRaises(UnsupportedTimeScaleScheduleError):
            solve_corridor(
                **common,
                time_scale_schedule=Th08TimeScaleSchedule.constant(
                    0x3F000000,
                    horizon=128,
                    provenance="complete_nonunit_test_fixture",
                ),
            )

    def test_requested_background_priority_fails_loud(self) -> None:
        class Solution:
            background_priority_lowered = False

        require_corridor_background_priority(
            Solution(),
            requested=False,
        )
        with self.assertRaisesRegex(RuntimeError, "was not applied"):
            require_corridor_background_priority(
                Solution(),
                requested=True,
            )

        Solution.background_priority_lowered = True
        require_corridor_background_priority(
            Solution(),
            requested=True,
        )

    def test_rejected_fine_and_survival_strategies_remain_shadow_only(self) -> None:
        self.assertEqual(LIVE_REFINEMENT_GRID_STEPS, ())
        self.assertFalse(LIVE_SURVIVAL_LABELS)
        self.assertEqual(SHADOW_REFINEMENT_GRID_STEPS, (8.0,))
        self.assertTrue(SHADOW_SURVIVAL_LABELS)

    def test_fine_boolean_query_inherits_only_coarse_losing_label(self) -> None:
        axis = np.asarray([0.0, 1.0], dtype=np.float32)
        actions = (ControlAction("stay", 0.0, 0.0),)
        config = ViabilityConfig(frames_per_layer=1)
        viable = np.zeros((2, 1, 2, 2), dtype=np.bool_)
        masks = np.zeros((1, 1, 2, 2), dtype=np.uint32)
        primary = RobustViabilityPolicy(
            x_axis=axis,
            y_axis=axis,
            actions=actions,
            delay_frames=(0,),
            nominal_delay=0,
            config=config,
            viable=viable,
            safe_action_masks=masks,
            backend="native",
        )
        survival = RobustViabilityPolicy(
            x_axis=axis,
            y_axis=axis,
            actions=actions,
            delay_frames=(0,),
            nominal_delay=0,
            config=config,
            viable=viable.copy(),
            safe_action_masks=masks.copy(),
            backend="native_fused_survival",
            survival_frames=np.full(
                viable.shape,
                7,
                dtype=np.uint16,
            ),
            survival_bottleneck_margins=np.full(
                viable.shape,
                -1.5,
                dtype=np.float32,
            ),
            survival_best_action_masks=np.ones(
                masks.shape,
                dtype=np.uint32,
            ),
        )
        plan = CorridorPlan(
            reachable=False,
            path=(),
            bottleneck_clearance=-math.inf,
            terminal_clearance=-math.inf,
            lane="none",
            gate=None,
            reason="test",
            viability_policy=primary,
            survival_policy=survival,
        )
        query = corridor_viability_query(
            CorridorSolution(100, plan, 1.0),
            current_frame=100,
            player_x=0.0,
            player_y=0.0,
            active_action="stay",
            max_age_frames=1,
        )
        self.assertIsNotNone(query)
        assert query is not None
        self.assertFalse(query.state_viable)
        self.assertEqual(query.survival_frames, 7)
        self.assertEqual(query.survival_bottleneck_margin, -1.5)
        self.assertEqual(query.survival_best_actions, ("stay",))

    def test_live_solve_publishes_boolean_before_survival_labels(self) -> None:
        solution = solve_corridor(
            source_frame=100,
            snapshot_frame=90,
            forecast_lead_frames=10,
            player_x=192.0,
            player_y=400.0,
            bullets=(),
            lasers=(),
            enemy_bodies=(),
            snapshot_lag=0,
            control_delay_candidates=(1, 2),
            nominal_control_delay=1,
            active_action="stay",
            time_scale_schedule=_UNIT_SCALE,
        )
        self.assertIsNotNone(solution.plan.viability_policy)
        self.assertIsInstance(solution.artifact, CorridorPolicyArtifact)
        self.assertIsInstance(
            solution.publication,
            CorridorPublication,
        )
        self.assertIsInstance(
            solution.handles,
            CorridorRuntimeHandles,
        )
        self.assertIs(solution.plan, solution.artifact.plan)
        self.assertEqual(
            solution.time_scale_identity,
            _UNIT_SCALE.serialized_identity,
        )
        self.assertFalse(
            hasattr(solution.artifact, "pipeline_prewarm_service")
        )
        self.assertFalse(
            hasattr(solution.publication, "audit_future")
        )
        self.assertIsNone(solution.plan.survival_policy)
        self.assertIsNotNone(solution.plan.survival_query_problem)
        assert solution.plan.survival_query_problem is not None
        self.assertEqual(
            solution.plan.survival_query_problem.clearance_volume.shape[0],
            81,
        )
        workspace_solution = prepare_pipeline_survival_workspace(solution)
        self.assertIsNotNone(
            workspace_solution.pipeline_survival_workspace,
        )
        self.assertIsNotNone(
            workspace_solution.pipeline_survival_workspace_ms,
        )
        exact = corridor_pipeline_survival_query(
            workspace_solution,
            current_frame=100,
            player_x=192.0,
            player_y=400.0,
            observed_action="stay",
            pending_command=None,
            max_age_frames=79,
        )
        self.assertIsNotNone(exact)
        assert exact is not None
        self.assertEqual(
            exact.backend,
            "native_augmented_pipeline_workspace",
        )
        workspace_solution.pipeline_survival_workspace.close()

    def test_audit_values_and_future_are_split_on_solution(self) -> None:
        future: Future[tuple[float, str | None]] = Future()
        future.set_result((1.5, None))
        submission = CorridorAuditSubmission(
            capsule="/tmp/policy.npz",
            write_ms=None,
            error=None,
            future=future,
        )
        with patch(
            "th08_corridor_runtime.submit_corridor_audit",
            return_value=submission,
        ) as submit:
            solution = solve_corridor(
                source_frame=100,
                snapshot_frame=90,
                forecast_lead_frames=10,
                player_x=192.0,
                player_y=400.0,
                bullets=(),
                lasers=(),
                enemy_bodies=(),
                snapshot_lag=0,
                control_delay_candidates=(1, 2),
                nominal_control_delay=1,
                active_action="stay",
                time_scale_schedule=_UNIT_SCALE,
                audit_capsule_dir=Path("/tmp/audit"),
            )

        self.assertEqual(
            solution.publication.audit_capsule,
            "/tmp/policy.npz",
        )
        self.assertIs(solution.handles.audit_future, future)
        self.assertFalse(hasattr(solution.publication, "audit_future"))
        self.assertTrue(
            submit.call_args.kwargs["plan_reachable"]
        )

    def test_background_resource_controls_are_applied_and_reported(self) -> None:
        with (
            patch(
                "th08_corridor_runtime.lower_current_thread_priority",
                return_value=True,
            ) as priority,
            patch(
                "th08_corridor_runtime.native_backend."
                "set_current_thread_viability_worker_limit",
                return_value=True,
            ) as worker_limit,
        ):
            solution = solve_corridor(
                source_frame=100,
                snapshot_frame=90,
                forecast_lead_frames=10,
                player_x=192.0,
                player_y=400.0,
                bullets=(),
                lasers=(),
                enemy_bodies=(),
                snapshot_lag=0,
                control_delay_candidates=(1, 2),
                nominal_control_delay=1,
                active_action="stay",
                time_scale_schedule=_UNIT_SCALE,
                background_low_priority=True,
                native_viability_worker_limit=2,
            )
        priority.assert_called_once_with()
        worker_limit.assert_called_once_with(2)
        self.assertTrue(solution.background_priority_lowered)
        self.assertEqual(solution.native_viability_worker_limit, 2)
        self.assertTrue(solution.native_viability_worker_limit_applied)

    def test_default_solve_does_not_lower_parent_worker_priority(self) -> None:
        with patch(
            "th08_corridor_runtime.lower_current_thread_priority",
        ) as priority:
            solution = solve_corridor(
                source_frame=100,
                snapshot_frame=90,
                forecast_lead_frames=10,
                player_x=192.0,
                player_y=400.0,
                bullets=(),
                lasers=(),
                enemy_bodies=(),
                snapshot_lag=0,
                control_delay_candidates=(1, 2),
                nominal_control_delay=1,
                active_action="stay",
                time_scale_schedule=_UNIT_SCALE,
            )

        priority.assert_not_called()
        self.assertFalse(solution.background_priority_lowered)

    def test_background_worker_limit_rejects_out_of_range_values(self) -> None:
        with self.assertRaisesRegex(ValueError, "must be 1..4"):
            solve_corridor(
                source_frame=100,
                snapshot_frame=90,
                forecast_lead_frames=10,
                player_x=192.0,
                player_y=400.0,
                bullets=(),
                lasers=(),
                enemy_bodies=(),
                snapshot_lag=0,
                control_delay_candidates=(1,),
                nominal_control_delay=1,
                active_action="stay",
                native_viability_worker_limit=0,
                time_scale_schedule=_UNIT_SCALE,
            )

if __name__ == "__main__":
    unittest.main()
