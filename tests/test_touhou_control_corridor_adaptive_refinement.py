#!/usr/bin/env python3
"""Soundness tests for query-local dual-bound corridor refinement."""

from __future__ import annotations

import unittest

import numpy as np

from touhou_control.corridor import (
    CorridorBounds,
    CorridorConfig,
    MovingAabbHazard,
    RobustControlSpec,
    build_policy_candidate_guide,
    build_query_local_refinement_patch,
    prepare_corridor_problem,
    prepare_dual_bound_scope,
    solve_query_local_dual_bounds,
    solve_query_local_dual_bounds_vectorized,
    trivial_coarse_action_bounds,
)
from touhou_control.corridor.clearance import hazard_clearance_volume
from touhou_control.corridor.dual_bounds import (
    ActionMaskBounds,
    build_spatial_cell_partition,
    build_transition_lattice,
    check_fine_reference_inclusion,
)
from touhou_control.corridor.grid import axis
from touhou_control.viability import (
    ControlAction,
    RobustViabilityPolicy,
    ViabilityConfig,
    build_robust_viability_policy,
)


class QueryLocalAdaptiveRefinementTests(unittest.TestCase):
    def setUp(self) -> None:
        self.actions = (
            ControlAction("stay", 0.0, 0.0),
            ControlAction("right", 2.0, 0.0),
            ControlAction("up", 0.0, -2.0),
        )
        self.bounds = CorridorBounds(
            left=0.0,
            right=128.0,
            top=0.0,
            bottom=128.0,
        )
        self.config = CorridorConfig(
            grid_step=16.0,
            frames_per_layer=2,
            horizon_frames=6,
            player_radius=0.0,
            required_clearance=0.0,
        )
        self.control = RobustControlSpec(
            actions=self.actions,
            delay_frames=(0, 1),
            nominal_delay=1,
            active_action="stay",
        )
        self.prepared = prepare_corridor_problem(
            bounds=self.bounds,
            config=self.config,
            robust_control=self.control,
        )
        self.scope = prepare_dual_bound_scope(
            prepared_problem=self.prepared,
            start_x=64.0,
            start_y=64.0,
        )

    def _patch(self, *, allow_full_field: bool = False):
        return build_query_local_refinement_patch(
            prepared_problem=self.prepared,
            scope=self.scope,
            incoming_bounds=trivial_coarse_action_bounds(
                prepared_problem=self.prepared
            ),
            fine_step=8.0,
            state_halo_cells=1,
            allow_full_field=allow_full_field,
        )

    def _fine_reference(self, patch):
        fine_config = CorridorConfig(
            grid_step=patch.fine_step,
            frames_per_layer=self.config.frames_per_layer,
            horizon_frames=self.config.horizon_frames,
            cardinal_speed=self.config.cardinal_speed,
            diagonal_axis_speed=self.config.diagonal_axis_speed,
            player_radius=self.config.player_radius,
            required_clearance=self.config.required_clearance,
            preferred_clearance=self.config.preferred_clearance,
            danger_radius=self.config.danger_radius,
            boundary_danger_radius=self.config.boundary_danger_radius,
            preferred_position_weight=self.config.preferred_position_weight,
        )
        grid_x, grid_y = np.meshgrid(patch.fine_x, patch.fine_y)
        clearance = hazard_clearance_volume(
            grid_x,
            grid_y,
            aabbs=self.prepared.aabbs,
            aabb_trajectories=self.prepared.aabb_trajectories,
            piecewise_aabbs=self.prepared.piecewise_aabbs,
            segments=self.prepared.segments,
            segment_trajectories=self.prepared.segment_trajectories,
            packed_segments=self.prepared.packed_segments,
            config=fine_config,
        )
        policy = build_robust_viability_policy(
            x_axis=patch.fine_x,
            y_axis=patch.fine_y,
            clearance_volume=clearance,
            actions=self.actions,
            delay_frames=self.control.delay_frames,
            nominal_delay=self.control.nominal_delay,
            config=ViabilityConfig(
                frames_per_layer=self.config.frames_per_layer,
                required_clearance=self.config.required_clearance,
                clamp_to_bounds=True,
            ),
            backend="numpy",
        )
        return policy

    def _inclusion_report(self, result, reference):
        identity = build_spatial_cell_partition(
            coarse_x=result.patch.fine_x,
            coarse_y=result.patch.fine_y,
            fine_x=result.patch.fine_x,
            fine_y=result.patch.fine_y,
        )
        return check_fine_reference_inclusion(
            bounds=ActionMaskBounds(
                lower=result.lower_action_masks,
                upper=result.upper_action_masks,
                action_count=len(self.actions),
            ),
            fine_reference_masks=reference.safe_action_masks,
            partition=identity,
        )

    def test_patch_is_root_local_and_has_a_transition_halo(self) -> None:
        patch = self._patch()
        self.assertLess(patch.spatial_fraction, 1.0)
        self.assertGreaterEqual(patch.dependency_halo_cells, 2)
        root_rows = patch.partition.member_rows(self.scope.root_row)
        root_columns = patch.partition.member_columns(self.scope.root_column)
        self.assertTrue(
            np.all(
                patch.requested_states[
                    0,
                    self.scope.root_active_index,
                    root_rows[:, None],
                    root_columns[None, :],
                ]
            )
        )

    def test_partial_recurrence_sandwiches_the_dense_fine_reference(self) -> None:
        patch = self._patch()
        result = solve_query_local_dual_bounds(
            prepared_problem=self.prepared,
            patch=patch,
            stop_when_root_sufficient=False,
        )
        reference = self._fine_reference(patch)
        report = self._inclusion_report(result, reference)
        self.assertTrue(report.passed)
        self.assertEqual(result.status, "complete")
        self.assertNotEqual(result.root_lower_mask, 0)
        self.assertEqual(
            result.root_lower_mask & ~result.root_upper_mask,
            0,
        )
        self.assertTrue(np.all(result.processed_states[patch.requested_states]))

    def test_vectorized_rectangle_sandwiches_the_dense_reference(self) -> None:
        patch = self._patch()
        result = solve_query_local_dual_bounds_vectorized(
            prepared_problem=self.prepared,
            patch=patch,
            backend="numpy",
        )
        reference = self._fine_reference(patch)
        report = self._inclusion_report(result, reference)
        self.assertTrue(report.passed)
        self.assertNotEqual(result.root_point_lower_mask, 0)
        self.assertEqual(
            result.root_point_lower_mask & ~result.root_point_upper_mask,
            0,
        )
        self.assertFalse(np.any(result.lower_branch_action_masks))
        self.assertTrue(
            np.all(result.upper_branch_action_masks == (1 << len(self.actions)) - 1)
        )

    def test_hidden_branch_masks_match_reference_when_marked_exact(self) -> None:
        patch = self._patch()
        result = solve_query_local_dual_bounds(
            prepared_problem=self.prepared,
            patch=patch,
            stop_when_root_sufficient=False,
        )
        reference = self._fine_reference(patch)
        transitions = build_transition_lattice(
            x_axis=patch.fine_x,
            y_axis=patch.fine_y,
            actions=self.actions,
            delay_frames=self.control.delay_frames,
            config=reference.config,
        )
        for layer, active_index, row, column in np.argwhere(
            result.processed_states[:-1]
        ):
            exact = int(
                result.exact_action_masks[
                    layer,
                    active_index,
                    row,
                    column,
                ]
            )
            for selected_index in range(len(self.actions)):
                action_bit = 1 << selected_index
                if not exact & action_bit:
                    continue
                for branch_index in range(len(self.control.delay_frames)):
                    successor_row = transitions.terminal_rows[
                        active_index,
                        selected_index,
                        branch_index,
                        row,
                        column,
                    ]
                    successor_column = transitions.terminal_columns[
                        active_index,
                        selected_index,
                        branch_index,
                        row,
                        column,
                    ]
                    branch_reference = bool(
                        reference.viable[
                            layer + 1,
                            selected_index,
                            successor_row,
                            successor_column,
                        ]
                    )
                    lower_branch = bool(
                        int(
                            result.lower_branch_action_masks[
                                layer,
                                active_index,
                                branch_index,
                                row,
                                column,
                            ]
                        )
                        & action_bit
                    )
                    upper_branch = bool(
                        int(
                            result.upper_branch_action_masks[
                                layer,
                                active_index,
                                branch_index,
                                row,
                                column,
                            ]
                        )
                        & action_bit
                    )
                    self.assertEqual(lower_branch, branch_reference)
                    self.assertEqual(upper_branch, branch_reference)

    def test_expired_deadline_retains_only_trivial_sound_bounds(self) -> None:
        patch = self._patch()
        result = solve_query_local_dual_bounds(
            prepared_problem=self.prepared,
            patch=patch,
            deadline_monotonic=0.0,
        )
        reference = self._fine_reference(patch)
        report = self._inclusion_report(result, reference)
        self.assertTrue(report.passed)
        self.assertEqual(result.status, "deadline")
        self.assertEqual(result.root_lower_mask, 0)
        self.assertEqual(
            result.root_upper_mask,
            (1 << len(self.actions)) - 1,
        )
        self.assertFalse(np.any(result.processed_states))

    def test_nonzero_query_layer_preserves_root_time_identity(self) -> None:
        scope = prepare_dual_bound_scope(
            prepared_problem=self.prepared,
            start_x=64.0,
            start_y=64.0,
            root_frame=self.config.frames_per_layer,
        )
        patch = build_query_local_refinement_patch(
            prepared_problem=self.prepared,
            scope=scope,
            incoming_bounds=trivial_coarse_action_bounds(
                prepared_problem=self.prepared
            ),
            fine_step=8.0,
            allow_full_field=False,
        )
        result = solve_query_local_dual_bounds(
            prepared_problem=self.prepared,
            patch=patch,
            stop_when_root_sufficient=False,
        )
        reference = self._fine_reference(patch)
        report = self._inclusion_report(result, reference)
        self.assertTrue(report.passed)
        self.assertEqual(patch.root_layer, 1)
        self.assertFalse(np.any(patch.requested_states[0]))
        self.assertNotEqual(result.root_lower_mask, 0)

    def test_restrictive_candidate_guide_can_only_weaken_the_lower(self) -> None:
        candidates = np.zeros(
            (
                self.scope.layer_count + 1,
                len(self.actions),
                self.prepared.y_axis.size,
                self.prepared.x_axis.size,
            ),
            dtype=np.bool_,
        )
        patch = build_query_local_refinement_patch(
            prepared_problem=self.prepared,
            scope=self.scope,
            incoming_bounds=trivial_coarse_action_bounds(
                prepared_problem=self.prepared
            ),
            fine_step=8.0,
            coarse_candidate_states=candidates,
            coarse_candidate_halo_cells=0,
            allow_full_field=False,
        )
        result = solve_query_local_dual_bounds(
            prepared_problem=self.prepared,
            patch=patch,
            stop_when_root_sufficient=False,
        )
        reference = self._fine_reference(patch)
        self.assertTrue(self._inclusion_report(result, reference).passed)
        self.assertEqual(result.root_lower_mask, 0)
        self.assertEqual(
            result.root_upper_mask,
            (1 << len(self.actions)) - 1,
        )

    def test_policy_guide_keeps_root_actions_unrestricted_then_narrows(
        self,
    ) -> None:
        layer_count = self.scope.layer_count
        state_shape = (
            layer_count + 1,
            len(self.actions),
            self.prepared.y_axis.size,
            self.prepared.x_axis.size,
        )
        mask_shape = (
            layer_count,
            len(self.actions),
            self.prepared.y_axis.size,
            self.prepared.x_axis.size,
        )
        safe_masks = np.ones(mask_shape, dtype=np.uint32)
        safe_masks[
            self.scope.root_layer,
            self.scope.root_active_index,
            self.scope.root_row,
            self.scope.root_column,
        ] = 0
        viable = np.ones(state_shape, dtype=np.bool_)
        viable[:-1] = safe_masks != 0
        policy = RobustViabilityPolicy(
            x_axis=self.prepared.x_axis,
            y_axis=self.prepared.y_axis,
            actions=self.actions,
            delay_frames=self.control.delay_frames,
            nominal_delay=self.control.nominal_delay,
            config=self.prepared.viability_config,
            viable=viable,
            safe_action_masks=safe_masks,
        )
        guide = build_policy_candidate_guide(
            policy=policy,
            scope=self.scope,
            empty_expansion_layers=1,
        )
        self.assertGreater(int(np.count_nonzero(guide[1])), 1)
        self.assertLess(
            int(np.count_nonzero(guide)),
            int(np.prod(guide.shape)),
        )
        patch = build_query_local_refinement_patch(
            prepared_problem=self.prepared,
            scope=self.scope,
            incoming_bounds=trivial_coarse_action_bounds(
                prepared_problem=self.prepared
            ),
            fine_step=8.0,
            coarse_candidate_states=guide,
            coarse_candidate_halo_cells=1,
            allow_full_field=True,
        )
        result = solve_query_local_dual_bounds(
            prepared_problem=self.prepared,
            patch=patch,
            stop_when_root_sufficient=False,
        )
        reference = self._fine_reference(patch)
        self.assertTrue(self._inclusion_report(result, reference).passed)

    def test_full_field_patch_is_rejected_without_explicit_test_override(
        self,
    ) -> None:
        small_bounds = CorridorBounds(
            left=0.0,
            right=32.0,
            top=0.0,
            bottom=32.0,
        )
        prepared = prepare_corridor_problem(
            bounds=small_bounds,
            config=self.config,
            robust_control=self.control,
        )
        scope = prepare_dual_bound_scope(
            prepared_problem=prepared,
            start_x=16.0,
            start_y=16.0,
        )
        with self.assertRaisesRegex(ValueError, "forbidden full field"):
            build_query_local_refinement_patch(
                prepared_problem=prepared,
                scope=scope,
                incoming_bounds=trivial_coarse_action_bounds(prepared_problem=prepared),
                fine_step=8.0,
            )

    def test_no_ambiguous_cell_fails_closed_without_starting_work(self) -> None:
        layer_count = self.scope.layer_count
        shape = (
            layer_count,
            len(self.actions),
            self.prepared.y_axis.size,
            self.prepared.x_axis.size,
        )
        exact_empty = ActionMaskBounds(
            lower=np.zeros(shape, dtype=np.uint64),
            upper=np.zeros(shape, dtype=np.uint64),
            action_count=len(self.actions),
        )
        with self.assertRaisesRegex(ValueError, "no ambiguous"):
            build_query_local_refinement_patch(
                prepared_problem=self.prepared,
                scope=self.scope,
                incoming_bounds=exact_empty,
                fine_step=8.0,
            )


class FineAxisContractTests(unittest.TestCase):
    def test_refinement_step_must_tile_the_same_domain(self) -> None:
        with self.assertRaisesRegex(ValueError, "integer number"):
            axis(0.0, 100.0, 16.0)


class GeneratedAdversarialRefinementTests(unittest.TestCase):
    def test_stop_redirect_and_reversal_cases_bound_dense_reference(
        self,
    ) -> None:
        rng = np.random.default_rng(0xA4D2)
        actions = (
            ControlAction("stay", 0.0, 0.0),
            ControlAction("right", 2.0, 0.0),
            ControlAction("left", -2.0, 0.0),
            ControlAction("down", 0.0, 2.0),
            ControlAction("up", 0.0, -2.0),
        )
        bounds = CorridorBounds(
            left=0.0,
            right=64.0,
            top=0.0,
            bottom=64.0,
        )
        config = CorridorConfig(
            grid_step=16.0,
            frames_per_layer=2,
            horizon_frames=4,
            player_radius=1.5,
            required_clearance=0.0,
        )
        control = RobustControlSpec(
            actions=actions,
            delay_frames=(0, 1, 2),
            nominal_delay=1,
            active_action="stay",
        )
        for case_index in range(12):
            hazards = tuple(
                MovingAabbHazard(
                    x=float(rng.uniform(8.0, 56.0)),
                    y=float(rng.uniform(8.0, 56.0)),
                    velocity_x=float(rng.uniform(-1.5, 1.5)),
                    velocity_y=float(rng.uniform(-1.5, 1.5)),
                    half_width=float(rng.uniform(2.0, 9.0)),
                    half_height=float(rng.uniform(2.0, 9.0)),
                    base_uncertainty=float(rng.uniform(0.0, 2.0)),
                    uncertainty_per_frame=float(rng.uniform(0.0, 0.25)),
                )
                for _ in range(4)
            )
            with self.subTest(case=case_index):
                prepared = prepare_corridor_problem(
                    bounds=bounds,
                    config=config,
                    robust_control=control,
                    aabbs=hazards,
                )
                scope = prepare_dual_bound_scope(
                    prepared_problem=prepared,
                    start_x=32.0,
                    start_y=32.0,
                )
                patch = build_query_local_refinement_patch(
                    prepared_problem=prepared,
                    scope=scope,
                    incoming_bounds=trivial_coarse_action_bounds(
                        prepared_problem=prepared
                    ),
                    fine_step=8.0,
                    allow_full_field=True,
                )
                result = solve_query_local_dual_bounds(
                    prepared_problem=prepared,
                    patch=patch,
                    stop_when_root_sufficient=False,
                )
                fine_config = CorridorConfig(
                    grid_step=8.0,
                    frames_per_layer=2,
                    horizon_frames=4,
                    player_radius=1.5,
                    required_clearance=0.0,
                )
                grid_x, grid_y = np.meshgrid(patch.fine_x, patch.fine_y)
                clearance = hazard_clearance_volume(
                    grid_x,
                    grid_y,
                    aabbs=hazards,
                    segments=(),
                    segment_trajectories=(),
                    config=fine_config,
                )
                reference = build_robust_viability_policy(
                    x_axis=patch.fine_x,
                    y_axis=patch.fine_y,
                    clearance_volume=clearance,
                    actions=actions,
                    delay_frames=control.delay_frames,
                    nominal_delay=control.nominal_delay,
                    config=ViabilityConfig(
                        frames_per_layer=2,
                        required_clearance=0.0,
                        clamp_to_bounds=True,
                    ),
                    backend="numpy",
                )
                identity = build_spatial_cell_partition(
                    coarse_x=patch.fine_x,
                    coarse_y=patch.fine_y,
                    fine_x=patch.fine_x,
                    fine_y=patch.fine_y,
                )
                report = check_fine_reference_inclusion(
                    bounds=ActionMaskBounds(
                        lower=result.lower_action_masks,
                        upper=result.upper_action_masks,
                        action_count=len(actions),
                    ),
                    fine_reference_masks=reference.safe_action_masks,
                    partition=identity,
                )
                self.assertTrue(report.passed)
                reference_branches = np.zeros(
                    result.lower_branch_action_masks.shape,
                    dtype=np.uint64,
                )
                x_start = float(patch.fine_x[0])
                x_end = float(patch.fine_x[-1])
                y_start = float(patch.fine_y[0])
                y_end = float(patch.fine_y[-1])
                for layer in range(reference.layer_count):
                    start_frame = layer * reference.config.frames_per_layer
                    for active_index, active in enumerate(actions):
                        for row, y in enumerate(patch.fine_y):
                            for column, x in enumerate(patch.fine_x):
                                current_safe = (
                                    float(clearance[start_frame, row, column])
                                    > reference.config.required_clearance
                                )
                                for selected_index, selected in enumerate(actions):
                                    action_bit = np.uint64(1 << selected_index)
                                    for branch_index, delay in enumerate(
                                        control.delay_frames
                                    ):
                                        path_safe = current_safe
                                        successor_row = row
                                        successor_column = column
                                        for physical_step in range(
                                            1,
                                            reference.config.frames_per_layer + 1,
                                        ):
                                            active_frames = min(
                                                physical_step,
                                                delay,
                                            )
                                            selected_frames = max(
                                                physical_step - delay,
                                                0,
                                            )
                                            target_x = (
                                                float(x)
                                                + active.velocity_x * active_frames
                                                + selected.velocity_x * selected_frames
                                            )
                                            target_y = (
                                                float(y)
                                                + active.velocity_y * active_frames
                                                + selected.velocity_y * selected_frames
                                            )
                                            target_x = min(
                                                x_end,
                                                max(x_start, target_x),
                                            )
                                            target_y = min(
                                                y_end,
                                                max(y_start, target_y),
                                            )
                                            successor_column = int(
                                                np.clip(
                                                    np.rint(
                                                        (target_x - x_start)
                                                        / patch.fine_step
                                                    ),
                                                    0,
                                                    patch.fine_x.size - 1,
                                                )
                                            )
                                            successor_row = int(
                                                np.clip(
                                                    np.rint(
                                                        (target_y - y_start)
                                                        / patch.fine_step
                                                    ),
                                                    0,
                                                    patch.fine_y.size - 1,
                                                )
                                            )
                                            error = np.hypot(
                                                target_x
                                                - float(patch.fine_x[successor_column]),
                                                target_y
                                                - float(patch.fine_y[successor_row]),
                                            )
                                            path_safe &= (
                                                float(
                                                    clearance[
                                                        start_frame + physical_step,
                                                        successor_row,
                                                        successor_column,
                                                    ]
                                                )
                                                - error
                                                > reference.config.required_clearance
                                            )
                                        branch_safe = path_safe and bool(
                                            reference.viable[
                                                layer + 1,
                                                selected_index,
                                                successor_row,
                                                successor_column,
                                            ]
                                        )
                                        if branch_safe:
                                            reference_branches[
                                                layer,
                                                active_index,
                                                branch_index,
                                                row,
                                                column,
                                            ] |= action_bit
                full_mask = np.uint64((1 << len(actions)) - 1)
                false_safe = (
                    result.lower_branch_action_masks
                    & np.bitwise_not(reference_branches)
                    & full_mask
                )
                missing_upper = (
                    reference_branches
                    & np.bitwise_not(result.upper_branch_action_masks)
                    & full_mask
                )
                self.assertFalse(np.any(false_safe))
                self.assertFalse(np.any(missing_upper))


if __name__ == "__main__":
    unittest.main()
