#!/usr/bin/env python3
"""Tests for the extracted asynchronous corridor runtime boundary."""

from __future__ import annotations

import math
import unittest
from dataclasses import replace
from unittest.mock import patch

import numpy as np

from corridor_planner import CorridorPlan
from th08_corridor_runtime import (
    CorridorSolution,
    LIVE_REFINEMENT_GRID_STEPS,
    LIVE_SURVIVAL_LABELS,
    SHADOW_REFINEMENT_GRID_STEPS,
    SHADOW_SURVIVAL_LABELS,
    corridor_pipeline_survival_query,
    corridor_pipeline_prewarm_query,
    corridor_pipeline_prewarm_retarget,
    corridor_postpublished_survival_query,
    corridor_viability_query,
    prepare_pipeline_survival_workspace,
    solve_corridor,
    solve_postpublished_survival,
    close_pipeline_prewarm,
)
from touhou_control.query_survival import ReachablePipelineRoot
from touhou_control.viability import (
    ControlAction,
    RobustViabilityPolicy,
    ViabilityConfig,
)


class Th08CorridorRuntimeTests(unittest.TestCase):
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
        )
        self.assertIsNotNone(solution.plan.viability_policy)
        self.assertIsNone(solution.plan.survival_policy)
        self.assertIsNotNone(solution.plan.survival_query_problem)
        assert solution.plan.survival_query_problem is not None
        self.assertEqual(
            solution.plan.survival_query_problem.clearance_volume.shape[0],
            81,
        )
        labeled = solve_postpublished_survival(solution)
        self.assertIsNone(labeled.plan.survival_policy)
        self.assertIsNotNone(labeled.postpublished_survival_policy)
        self.assertTrue(labeled.postpublished_survival_parity)
        query = corridor_postpublished_survival_query(
            labeled,
            current_frame=100,
            player_x=192.0,
            player_y=400.0,
            observed_action="stay",
            max_age_frames=79,
        )
        self.assertIsNotNone(query)
        assert query is not None
        self.assertIsNotNone(query.survival_frames)
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

    def test_prepublication_shadow_is_ready_for_predicted_source_root(
        self,
    ) -> None:
        solution = solve_corridor(
            source_frame=100,
            snapshot_frame=84,
            forecast_lead_frames=16,
            player_x=192.0,
            player_y=400.0,
            bullets=(),
            lasers=(),
            enemy_bodies=(),
            snapshot_lag=0,
            control_delay_candidates=(1, 2, 3, 4, 5, 6),
            nominal_control_delay=4,
            active_action="stay",
            pipeline_prewarm_shadow=True,
        )
        service = solution.pipeline_prewarm_service
        self.assertIsNotNone(service)
        assert service is not None
        try:
            self.assertTrue(service.wait_until_idle(2.0))
            query = corridor_pipeline_prewarm_query(
                solution,
                current_frame=104,
                player_x=192.0,
                player_y=400.0,
                observed_action="stay",
                pending_command=None,
                max_age_frames=79,
            )
            self.assertEqual(query.status, "hit")
            self.assertIsNotNone(query.result)
            retarget = corridor_pipeline_prewarm_retarget(
                solution,
                root=query.root,
                selected_action="right",
                physical_x=192.0,
                physical_y=400.0,
                command_issue_offset=2,
                preferred_decision_frame=4,
            )
            self.assertEqual(retarget.status, "queued")
            self.assertGreater(retarget.root_count, 0)
        finally:
            close_pipeline_prewarm(solution)
        self.assertTrue(service.closed)

    def test_prepublication_shadow_rejects_solution_version_mismatch(
        self,
    ) -> None:
        solution = solve_corridor(
            source_frame=100,
            snapshot_frame=84,
            forecast_lead_frames=16,
            player_x=192.0,
            player_y=400.0,
            bullets=(),
            lasers=(),
            enemy_bodies=(),
            snapshot_lag=0,
            control_delay_candidates=(1, 2, 3, 4, 5, 6),
            nominal_control_delay=4,
            active_action="stay",
            pipeline_prewarm_shadow=True,
        )
        try:
            stale = replace(solution, source_frame=101)
            query = corridor_pipeline_prewarm_query(
                stale,
                current_frame=105,
                player_x=192.0,
                player_y=400.0,
                observed_action="stay",
                pending_command=None,
                max_age_frames=79,
            )
            self.assertEqual(query.status, "stale_policy_version")
            retarget = corridor_pipeline_prewarm_retarget(
                stale,
                root=ReachablePipelineRoot(
                    frame=4,
                    row=24,
                    column=12,
                    observed_action="stay",
                    pending_command=None,
                ),
                selected_action="right",
                physical_x=192.0,
                physical_y=400.0,
                command_issue_offset=2,
                preferred_decision_frame=4,
            )
            self.assertEqual(retarget.status, "stale_policy_version")
        finally:
            close_pipeline_prewarm(solution)

    def test_prepublication_start_failure_does_not_fail_boolean_policy(
        self,
    ) -> None:
        with patch(
            "th08_corridor_runtime.PipelinePrewarmService",
            side_effect=RuntimeError("injected shadow failure"),
        ):
            solution = solve_corridor(
                source_frame=100,
                snapshot_frame=84,
                forecast_lead_frames=16,
                player_x=192.0,
                player_y=400.0,
                bullets=(),
                lasers=(),
                enemy_bodies=(),
                snapshot_lag=0,
                control_delay_candidates=(1, 2, 3, 4, 5, 6),
                nominal_control_delay=4,
                active_action="stay",
                pipeline_prewarm_shadow=True,
            )
        self.assertIsNone(solution.pipeline_prewarm_service)
        self.assertEqual(
            solution.pipeline_prewarm_start_error,
            "RuntimeError: injected shadow failure",
        )
        self.assertIsNotNone(solution.plan.viability_policy)


if __name__ == "__main__":
    unittest.main()
