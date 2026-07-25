#!/usr/bin/env python3
"""Tests for phase-exact query-local survival and pending input state."""

from __future__ import annotations

import unittest

import numpy as np

from touhou_control.query_survival import (
    PendingCommand,
    ReachablePipelineRoot,
    StalePipelineWorkspaceError,
    SurvivalQueryProblem,
    enumerate_next_decision_roots,
    query_local_survival,
    scalar_query_local_survival,
)
from touhou_control.pipeline_root_schedule import (
    schedule_pipeline_frontier,
)
from touhou_control.reachability_oracle import (
    scalar_robust_survival_query,
)
from touhou_control.viability import (
    ControlAction,
    ViabilityConfig,
    build_robust_viability_policy,
)


class QueryLocalSurvivalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.axis = np.asarray([0.0, 1.0, 2.0], dtype=np.float32)
        self.actions = (
            ControlAction("stay", 0.0, 0.0),
            ControlAction("right", 1.0, 0.0),
            ControlAction("left", -1.0, 0.0),
        )

    def test_aligned_without_pending_matches_existing_scalar_oracle(
        self,
    ) -> None:
        clearance = np.full((5, 3, 3), 10.0, dtype=np.float32)
        clearance[3:, :, 0] = -1.0
        config = ViabilityConfig(frames_per_layer=2)
        expected = scalar_robust_survival_query(
            x_axis=self.axis,
            y_axis=self.axis,
            clearance_volume=clearance,
            actions=self.actions,
            delay_frames=(0, 1),
            config=config,
            layer=0,
            row=1,
            column=1,
            active_action="stay",
        )
        actual = scalar_query_local_survival(
            x_axis=self.axis,
            y_axis=self.axis,
            clearance_volume=clearance,
            actions=self.actions,
            delay_frames=(0, 1),
            config=config,
            start_frame=0,
            row=1,
            column=1,
            observed_action="stay",
        )
        self.assertEqual(actual.state_label, expected.state_label)
        self.assertEqual(actual.action_labels, expected.action_labels)
        self.assertEqual(actual.best_actions, expected.best_actions)

    def test_exact_start_frame_does_not_reuse_older_layer_geometry(
        self,
    ) -> None:
        clearance = np.full((5, 3, 3), 10.0, dtype=np.float32)
        clearance[1, 1, 1] = -2.0
        result = scalar_query_local_survival(
            x_axis=self.axis,
            y_axis=self.axis,
            clearance_volume=clearance,
            actions=self.actions,
            delay_frames=(0,),
            config=ViabilityConfig(frames_per_layer=2),
            start_frame=1,
            row=1,
            column=1,
            observed_action="stay",
        )
        self.assertEqual(result.state_label.guaranteed_frames, 0)
        self.assertEqual(result.state_label.bottleneck_margin, -2.0)

    def test_pending_action_can_activate_before_new_selection(self) -> None:
        clearance = np.full((3, 3, 3), 10.0, dtype=np.float32)
        # At frame 2, only x=0 is unsafe.  The observed left action remains
        # there without a pending command, while the older pending right
        # action activates on frame 2 before the newly selected command's
        # two-frame delay expires.
        clearance[2, :, 0] = -1.0
        common = {
            "x_axis": self.axis,
            "y_axis": self.axis,
            "clearance_volume": clearance,
            "actions": self.actions,
            "delay_frames": (2,),
            "config": ViabilityConfig(frames_per_layer=2),
            "start_frame": 0,
            "row": 1,
            "column": 1,
            "observed_action": "left",
        }
        without_pending = scalar_query_local_survival(**common)
        with_pending = scalar_query_local_survival(
            **common,
            pending_command=PendingCommand("right", (1,)),
        )
        self.assertEqual(
            without_pending.state_label.guaranteed_frames,
            1,
        )
        self.assertEqual(with_pending.state_label.guaranteed_frames, 2)

    def test_delay_longer_than_interval_is_carried_as_pending(self) -> None:
        clearance = np.full((5, 3, 3), 10.0, dtype=np.float32)
        result = scalar_query_local_survival(
            x_axis=self.axis,
            y_axis=self.axis,
            clearance_volume=clearance,
            actions=self.actions,
            delay_frames=(3,),
            config=ViabilityConfig(frames_per_layer=2),
            start_frame=0,
            row=1,
            column=1,
            observed_action="stay",
        )
        self.assertTrue(result.winning)
        self.assertEqual(result.state_label.guaranteed_frames, 4)
        self.assertGreater(result.evaluated_state_count, 1)

    def test_pending_activates_at_successor_boundary_before_later_command(
        self,
    ) -> None:
        axis = np.arange(5, dtype=np.float32)
        clearance = np.full((5, 5, 5), 10.0, dtype=np.float32)
        # The observed action holds x=2 for the first two frames. The older
        # pending right command becomes active exactly at the successor
        # boundary and must move to x=3 on frame 3 while the newer command is
        # still pending. Keeping the observed action for one extra interval
        # would collide at x=2.
        clearance[3, :, 2] = -1.0
        arguments = {
            "x_axis": axis,
            "y_axis": axis,
            "clearance_volume": clearance,
            "actions": self.actions,
            "delay_frames": (3,),
            "config": ViabilityConfig(frames_per_layer=2),
            "start_frame": 0,
            "row": 2,
            "column": 2,
            "observed_action": "stay",
            "pending_command": PendingCommand("right", (2,)),
        }
        expected = scalar_query_local_survival(**arguments)
        self.assertGreaterEqual(
            expected.state_label.guaranteed_frames,
            3,
        )
        try:
            actual = query_local_survival(
                **arguments,
                backend="native",
            )
        except RuntimeError as error:
            self.skipTest(str(error))
        self.assertEqual(actual.state_label, expected.state_label)
        self.assertEqual(actual.action_labels, expected.action_labels)
        self.assertEqual(actual.best_actions, expected.best_actions)

    def test_native_matches_scalar_with_pending_and_phase_offset(self) -> None:
        clearance = np.full((7, 3, 3), 10.0, dtype=np.float32)
        clearance[4:, 0, :] = -1.25
        arguments = {
            "x_axis": self.axis,
            "y_axis": self.axis,
            "clearance_volume": clearance,
            "actions": self.actions,
            "delay_frames": (1, 3),
            "config": ViabilityConfig(frames_per_layer=2),
            "start_frame": 1,
            "row": 1,
            "column": 1,
            "observed_action": "left",
            "pending_command": PendingCommand("right", (1, 2)),
        }
        expected = scalar_query_local_survival(**arguments)
        try:
            actual = query_local_survival(
                **arguments,
                backend="native",
            )
        except RuntimeError as error:
            self.skipTest(str(error))
        self.assertEqual(actual.state_label, expected.state_label)
        self.assertEqual(actual.action_labels, expected.action_labels)
        self.assertEqual(actual.best_actions, expected.best_actions)

    def test_native_matches_scalar_on_deterministic_adversarial_seeds(
        self,
    ) -> None:
        for seed in range(16):
            with self.subTest(seed=seed):
                rng = np.random.default_rng(seed)
                clearance = rng.uniform(
                    -2.0,
                    4.0,
                    size=(7, 3, 3),
                ).astype(np.float32)
                clearance[seed % 5, 1, 1] = 3.0
                arguments = {
                    "x_axis": self.axis,
                    "y_axis": self.axis,
                    "clearance_volume": clearance,
                    "actions": self.actions,
                    "delay_frames": (0, 1, 3),
                    "config": ViabilityConfig(frames_per_layer=2),
                    "start_frame": seed % 3,
                    "row": 1,
                    "column": 1,
                    "observed_action": self.actions[seed % 3].name,
                    "pending_command": (
                        PendingCommand(
                            self.actions[(seed + 1) % 3].name,
                            (1, 2),
                        )
                        if seed % 2
                        else None
                    ),
                }
                expected = scalar_query_local_survival(**arguments)
                try:
                    actual = query_local_survival(
                        **arguments,
                        backend="native",
                    )
                except RuntimeError as error:
                    self.skipTest(str(error))
                self.assertEqual(
                    actual.state_label.guaranteed_frames,
                    expected.state_label.guaranteed_frames,
                )
                self.assertAlmostEqual(
                    actual.state_label.bottleneck_margin,
                    expected.state_label.bottleneck_margin,
                    places=5,
                )
                self.assertEqual(actual.best_actions, expected.best_actions)
                for (actual_name, actual_label), (
                    expected_name,
                    expected_label,
                ) in zip(actual.action_labels, expected.action_labels):
                    self.assertEqual(actual_name, expected_name)
                    self.assertEqual(
                        actual_label.guaranteed_frames,
                        expected_label.guaranteed_frames,
                    )
                    self.assertAlmostEqual(
                        actual_label.bottleneck_margin,
                        expected_label.bottleneck_margin,
                        places=5,
                    )

    def test_augmented_workspace_matches_scalar_and_reuses_exact_root(
        self,
    ) -> None:
        for seed in range(16):
            with self.subTest(seed=seed):
                rng = np.random.default_rng(30_000 + seed)
                clearance = rng.uniform(
                    -2.0,
                    6.0,
                    size=(9, 4, 4),
                ).astype(np.float32)
                axis = np.arange(4, dtype=np.float32)
                config = ViabilityConfig(frames_per_layer=2)
                pending = (
                    PendingCommand(
                        self.actions[(seed + 1) % 3].name,
                        (1, 2, 3),
                    )
                    if seed % 2
                    else None
                )
                scalar = scalar_query_local_survival(
                    x_axis=axis,
                    y_axis=axis,
                    clearance_volume=clearance,
                    actions=self.actions,
                    delay_frames=(0, 1, 3),
                    config=config,
                    start_frame=seed % 4,
                    row=1 + seed % 2,
                    column=1 + (seed // 2) % 2,
                    observed_action=self.actions[seed % 3].name,
                    pending_command=pending,
                )
                problem = SurvivalQueryProblem(
                    x_axis=axis,
                    y_axis=axis,
                    clearance_volume=clearance,
                    actions=self.actions,
                    delay_frames=(0, 1, 3),
                    nominal_delay=1,
                    config=config,
                )
                try:
                    workspace = problem.build_pipeline_workspace(
                        policy_version=seed,
                    )
                except RuntimeError as error:
                    self.skipTest(str(error))
                with workspace:
                    arguments = {
                        "policy_version": seed,
                        "frame": seed % 4,
                        "row": 1 + seed % 2,
                        "column": 1 + (seed // 2) % 2,
                        "observed_action": self.actions[seed % 3].name,
                        "pending_command": pending,
                    }
                    first = workspace.query_cell(**arguments)
                    second = workspace.query_cell(**arguments)
                self.assertEqual(first.state_label, scalar.state_label)
                self.assertEqual(first.action_labels, scalar.action_labels)
                self.assertEqual(first.best_actions, scalar.best_actions)
                self.assertGreaterEqual(
                    first.workspace_stats.new_state_count,
                    0,
                )
                self.assertEqual(second.workspace_stats.new_state_count, 0)
                self.assertEqual(
                    second.workspace_stats.branch_simulation_count,
                    0,
                )
                self.assertGreater(
                    second.workspace_stats.root_memo_hit_count,
                    0,
                )

    def test_augmented_workspace_rejects_stale_policy_version(self) -> None:
        clearance = np.full((5, 3, 3), 10.0, dtype=np.float32)
        problem = SurvivalQueryProblem(
            x_axis=self.axis,
            y_axis=self.axis,
            clearance_volume=clearance,
            actions=self.actions,
            delay_frames=(0, 1),
            nominal_delay=1,
            config=ViabilityConfig(frames_per_layer=2),
        )
        try:
            workspace = problem.build_pipeline_workspace(
                policy_version="policy-a",
            )
        except RuntimeError as error:
            self.skipTest(str(error))
        with workspace:
            with self.assertRaises(StalePipelineWorkspaceError):
                workspace.query_cell(
                    policy_version="policy-b",
                    frame=0,
                    row=1,
                    column=1,
                    observed_action="stay",
                )

    def test_workspace_lookup_only_never_expands_a_missing_root(self) -> None:
        clearance = np.full((5, 3, 3), 10.0, dtype=np.float32)
        problem = SurvivalQueryProblem(
            x_axis=self.axis,
            y_axis=self.axis,
            clearance_volume=clearance,
            actions=self.actions,
            delay_frames=(0, 1),
            nominal_delay=1,
            config=ViabilityConfig(frames_per_layer=2),
        )
        try:
            workspace = problem.build_pipeline_workspace(
                policy_version="lookup",
            )
        except RuntimeError as error:
            self.skipTest(str(error))
        arguments = {
            "policy_version": "lookup",
            "frame": 0,
            "row": 1,
            "column": 1,
            "observed_action": "stay",
        }
        with workspace:
            self.assertIsNone(workspace.lookup_cell(**arguments))
            workspace.query_cell(**arguments)
            cached = workspace.lookup_cell(**arguments)
        self.assertIsNotNone(cached)
        self.assertEqual(cached.workspace_stats.new_state_count, 0)
        self.assertGreater(cached.workspace_stats.root_memo_hit_count, 0)

    def test_variable_cadence_workspace_matches_scalar_adversarial_seeds(
        self,
    ) -> None:
        cadence_support = (1, 2, 3)
        axis = np.arange(4, dtype=np.float32)
        for seed in range(24):
            with self.subTest(seed=seed):
                rng = np.random.default_rng(80_000 + seed)
                clearance = rng.uniform(
                    -2.0,
                    6.0,
                    size=(9, 4, 4),
                ).astype(np.float32)
                pending = (
                    PendingCommand(
                        self.actions[(seed + 1) % 3].name,
                        (1, 2, 4),
                    )
                    if seed % 2
                    else None
                )
                arguments = {
                    "x_axis": axis,
                    "y_axis": axis,
                    "clearance_volume": clearance,
                    "actions": self.actions,
                    "delay_frames": (0, 2, 4),
                    "config": ViabilityConfig(frames_per_layer=2),
                    "start_frame": seed % 4,
                    "row": 1 + seed % 2,
                    "column": 1 + (seed // 2) % 2,
                    "observed_action": self.actions[seed % 3].name,
                    "pending_command": pending,
                    "decision_frame_support": cadence_support,
                }
                scalar = scalar_query_local_survival(**arguments)
                problem = SurvivalQueryProblem(
                    x_axis=axis,
                    y_axis=axis,
                    clearance_volume=clearance,
                    actions=self.actions,
                    delay_frames=(0, 2, 4),
                    nominal_delay=2,
                    config=ViabilityConfig(frames_per_layer=2),
                )
                try:
                    workspace = problem.build_pipeline_workspace(
                        policy_version=seed,
                        decision_frame_support=cadence_support,
                    )
                except RuntimeError as error:
                    self.skipTest(str(error))
                with workspace:
                    native = workspace.query_cell(
                        policy_version=seed,
                        frame=arguments["start_frame"],
                        row=arguments["row"],
                        column=arguments["column"],
                        observed_action=arguments["observed_action"],
                        pending_command=pending,
                    )
                self.assertEqual(
                    native.state_label.guaranteed_frames,
                    scalar.state_label.guaranteed_frames,
                )
                self.assertAlmostEqual(
                    native.state_label.bottleneck_margin,
                    scalar.state_label.bottleneck_margin,
                    places=5,
                )
                self.assertEqual(native.best_actions, scalar.best_actions)
                for (_, native_label), (_, scalar_label) in zip(
                    native.action_labels,
                    scalar.action_labels,
                ):
                    self.assertEqual(
                        native_label.guaranteed_frames,
                        scalar_label.guaranteed_frames,
                    )
                    self.assertAlmostEqual(
                        native_label.bottleneck_margin,
                        scalar_label.bottleneck_margin,
                        places=5,
                    )

    def test_next_decision_frontier_groups_remaining_delay_support(
        self,
    ) -> None:
        axis = np.arange(7, dtype=np.float32)
        roots = enumerate_next_decision_roots(
            x_axis=axis,
            y_axis=axis,
            actions=self.actions,
            delay_frames=(3, 4),
            decision_frame_support=(2,),
            config=ViabilityConfig(frames_per_layer=2),
            start_frame=5,
            horizon_frame=20,
            row=3,
            column=3,
            observed_action="stay",
            selected_action="right",
        )
        self.assertEqual(len(roots), 1)
        root = roots[0]
        self.assertEqual((root.frame, root.row, root.column), (7, 3, 3))
        self.assertEqual(root.observed_action, "stay")
        self.assertEqual(
            root.pending_command,
            PendingCommand("right", (1, 2)),
        )

    def test_next_frontier_preserves_older_activation_and_new_pending(
        self,
    ) -> None:
        axis = np.arange(7, dtype=np.float32)
        roots = enumerate_next_decision_roots(
            x_axis=axis,
            y_axis=axis,
            actions=self.actions,
            delay_frames=(4,),
            decision_frame_support=(2,),
            config=ViabilityConfig(frames_per_layer=2),
            start_frame=0,
            horizon_frame=8,
            row=3,
            column=3,
            observed_action="left",
            selected_action="stay",
            pending_command=PendingCommand("right", (1,)),
        )
        self.assertEqual(len(roots), 1)
        self.assertEqual(
            roots[0],
            ReachablePipelineRoot(
                frame=2,
                row=3,
                column=3,
                observed_action="right",
                pending_command=PendingCommand("stay", (2,)),
            ),
        )

    def test_physical_frontier_respects_subcell_and_issue_offset(
        self,
    ) -> None:
        axis = np.arange(9, dtype=np.float32)
        roots = enumerate_next_decision_roots(
            x_axis=axis,
            y_axis=axis,
            actions=self.actions,
            delay_frames=(1,),
            decision_frame_support=(2, 4),
            config=ViabilityConfig(frames_per_layer=2),
            start_frame=0,
            horizon_frame=8,
            row=3,
            column=3,
            observed_action="stay",
            selected_action="right",
            physical_start_x=3.6,
            physical_start_y=3.0,
            command_issue_offset=2,
        )
        self.assertEqual(
            roots,
            (
                ReachablePipelineRoot(
                    frame=4,
                    row=3,
                    column=5,
                    observed_action="right",
                    pending_command=None,
                ),
            ),
        )

    def test_physical_pipeline_schedule_bounds_exact_root_work(
        self,
    ) -> None:
        axis = np.arange(9, dtype=np.float32)
        problem = SurvivalQueryProblem(
            x_axis=axis,
            y_axis=axis,
            clearance_volume=np.full(
                (13, 9, 9),
                10.0,
                dtype=np.float32,
            ),
            actions=self.actions,
            delay_frames=(1, 2, 3, 4),
            nominal_delay=3,
            config=ViabilityConfig(frames_per_layer=2),
        )
        schedule = schedule_pipeline_frontier(
            problem=problem,
            root=ReachablePipelineRoot(0, 4, 4, "stay", None),
            selected_action="right",
            physical_x=4.4,
            physical_y=4.0,
            command_issue_offset=1,
            preferred_decision_frame=4,
            scheduling_frame_support=(2, 3, 4, 5),
            root_limit=2,
            preferred_pickup_delay=1,
        )
        self.assertEqual(len(schedule.roots), 2)
        self.assertGreater(schedule.candidate_count, len(schedule.roots))
        self.assertEqual(schedule.preferred_decision_frame, 4)
        self.assertEqual(schedule.preferred_pickup_delay, 1)
        self.assertEqual(schedule.roots[0].frame, 4)
        self.assertEqual(schedule.roots[0].observed_action, "right")

    def test_variable_cadence_seed_reuses_each_next_phase(self) -> None:
        axis = np.arange(9, dtype=np.float32)
        clearance = np.full((13, 9, 9), 10.0, dtype=np.float32)
        problem = SurvivalQueryProblem(
            x_axis=axis,
            y_axis=axis,
            clearance_volume=clearance,
            actions=self.actions,
            delay_frames=(0, 1, 3),
            nominal_delay=1,
            config=ViabilityConfig(frames_per_layer=2),
        )
        cadence_support = (2, 3, 4)
        try:
            workspace = problem.build_pipeline_workspace(
                policy_version="variable",
                decision_frame_support=cadence_support,
            )
        except RuntimeError as error:
            self.skipTest(str(error))
        with workspace:
            base = workspace.query_cell(
                policy_version="variable",
                frame=0,
                row=4,
                column=4,
                observed_action="stay",
            )
            roots = enumerate_next_decision_roots(
                x_axis=axis,
                y_axis=axis,
                actions=self.actions,
                delay_frames=(0, 1, 3),
                decision_frame_support=cadence_support,
                config=problem.config,
                start_frame=0,
                horizon_frame=problem.horizon_frames,
                row=4,
                column=4,
                observed_action="stay",
                selected_action="stay",
            )
            warmed = [
                workspace.query_cell(
                    policy_version="variable",
                    frame=root.frame,
                    row=root.row,
                    column=root.column,
                    observed_action=root.observed_action,
                    pending_command=root.pending_command,
                )
                for root in roots
            ]
        self.assertEqual({root.frame for root in roots}, {2, 3, 4})
        self.assertGreater(base.workspace_stats.new_state_count, 0)
        self.assertLess(
            max(
                result.workspace_stats.new_state_count
                for result in warmed
            ),
            base.workspace_stats.new_state_count,
        )

    def test_postpublished_labels_match_fused_on_every_losing_state(
        self,
    ) -> None:
        rng = np.random.default_rng(9183)
        clearance = rng.uniform(
            -1.5,
            5.0,
            size=(7, 3, 3),
        ).astype(np.float32)
        config = ViabilityConfig(frames_per_layer=2)
        arguments = {
            "x_axis": self.axis,
            "y_axis": self.axis,
            "clearance_volume": clearance,
            "actions": self.actions,
            "delay_frames": (0, 1, 2),
            "nominal_delay": 1,
            "config": config,
        }
        boolean = build_robust_viability_policy(**arguments)
        try:
            fused = build_robust_viability_policy(
                **arguments,
                survival_labels=True,
            )
        except RuntimeError as error:
            self.skipTest(str(error))
        problem = SurvivalQueryProblem(**arguments)
        postpublished = problem.build_postpublished_policy(boolean)
        losing_states = ~boolean.viable
        losing_actions = losing_states[:-1]
        np.testing.assert_array_equal(
            postpublished.survival_frames[losing_states],
            fused.survival_frames[losing_states],
        )
        np.testing.assert_allclose(
            postpublished.survival_bottleneck_margins[losing_states],
            fused.survival_bottleneck_margins[losing_states],
            rtol=0.0,
            atol=0.0,
        )
        np.testing.assert_array_equal(
            postpublished.survival_best_action_masks[losing_actions],
            fused.survival_best_action_masks[losing_actions],
        )


if __name__ == "__main__":
    unittest.main()
