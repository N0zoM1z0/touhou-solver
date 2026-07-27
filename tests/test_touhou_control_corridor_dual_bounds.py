#!/usr/bin/env python3
"""Tests for sound spatial bounds and root-relevant G2 tubes."""

from __future__ import annotations

import unittest

import numpy as np

from touhou_control.corridor import (
    CorridorBounds,
    CorridorConfig,
    RobustControlSpec,
    prepare_corridor_problem,
)
from touhou_control.corridor.dual_bounds import (
    ActionMaskBounds,
    aggregate_fine_action_mask_bounds,
    build_spatial_cell_partition,
    build_transition_lattice,
    check_fine_reference_inclusion,
    prepare_dual_bound_scope,
    root_branch_forward_tube,
    terminal_coreachable_tube,
)
from touhou_control.viability import ControlAction, ViabilityConfig


class SpatialActionMaskBoundTests(unittest.TestCase):
    def setUp(self) -> None:
        self.partition = build_spatial_cell_partition(
            coarse_x=np.asarray([0.0, 16.0, 32.0], dtype=np.float32),
            coarse_y=np.asarray([0.0, 16.0, 32.0], dtype=np.float32),
            fine_x=np.asarray(
                [0.0, 8.0, 16.0, 24.0, 32.0],
                dtype=np.float32,
            ),
            fine_y=np.asarray(
                [0.0, 8.0, 16.0, 24.0, 32.0],
                dtype=np.float32,
            ),
        )

    def test_partition_uses_round_to_even_projection(self) -> None:
        np.testing.assert_array_equal(
            self.partition.fine_columns_to_coarse,
            np.asarray([0, 0, 1, 2, 2]),
        )
        np.testing.assert_array_equal(
            self.partition.fine_rows_to_coarse,
            np.asarray([0, 0, 1, 2, 2]),
        )

    def test_bounds_preserve_time_plane_and_hidden_branch_axes(self) -> None:
        fine = np.full((2, 3, 2, 5, 5), 0b111, dtype=np.uint64)
        fine[1, 2, 1, 0, 0] = 0b011
        fine[1, 2, 1, 1, 1] = 0b101
        bounds = aggregate_fine_action_mask_bounds(
            fine_action_masks=fine,
            partition=self.partition,
            action_count=3,
        )
        self.assertEqual(bounds.lower.shape, (2, 3, 2, 3, 3))
        self.assertEqual(int(bounds.lower[1, 2, 1, 0, 0]), 0b001)
        self.assertEqual(int(bounds.upper[1, 2, 1, 0, 0]), 0b111)
        self.assertTrue(bounds.ambiguous[1, 2, 1, 0, 0])
        self.assertEqual(
            int(bounds.lower[0, 2, 1, 0, 0]),
            0b111,
        )

    def test_aggregated_bounds_contain_the_fine_reference(self) -> None:
        rng = np.random.default_rng(0xD2A1)
        fine = rng.integers(
            0,
            1 << 36,
            size=(2, 4, 3, 5, 5),
            dtype=np.uint64,
        )
        bounds = aggregate_fine_action_mask_bounds(
            fine_action_masks=fine,
            partition=self.partition,
            action_count=36,
        )
        report = check_fine_reference_inclusion(
            bounds=bounds,
            fine_reference_masks=fine,
            partition=self.partition,
        )
        self.assertTrue(report.passed)
        self.assertEqual(report.false_safe_action_count, 0)
        self.assertEqual(report.missing_upper_action_count, 0)

    def test_inclusion_report_exposes_action_specific_failures(self) -> None:
        fine = np.zeros((1, 1, 1, 5, 5), dtype=np.uint64)
        bounds = ActionMaskBounds(
            lower=np.ones((1, 1, 1, 3, 3), dtype=np.uint64),
            upper=np.ones((1, 1, 1, 3, 3), dtype=np.uint64),
            action_count=2,
        )
        report = check_fine_reference_inclusion(
            bounds=bounds,
            fine_reference_masks=fine,
            partition=self.partition,
        )
        self.assertFalse(report.passed)
        self.assertEqual(report.false_safe_action_count, 25)
        self.assertEqual(report.missing_upper_action_count, 0)
        self.assertEqual(report.first_false_safe.action_bits, 0b01)
        self.assertEqual(len(report.first_false_safe.index), 5)

        reference = np.full((1, 1, 1, 5, 5), 0b10, dtype=np.uint64)
        missing = check_fine_reference_inclusion(
            bounds=bounds,
            fine_reference_masks=reference,
            partition=self.partition,
        )
        self.assertEqual(missing.false_safe_action_count, 25)
        self.assertEqual(missing.missing_upper_action_count, 25)
        self.assertEqual(missing.first_missing_upper.action_bits, 0b10)


class TransitionTubeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.actions = (
            ControlAction("stay", 0.0, 0.0),
            ControlAction("right", 1.0, 0.0),
        )
        self.config = ViabilityConfig(
            frames_per_layer=2,
            clamp_to_bounds=False,
        )
        self.transitions = build_transition_lattice(
            x_axis=np.asarray([0.0, 1.0, 2.0, 3.0], dtype=np.float32),
            y_axis=np.asarray([0.0, 1.0], dtype=np.float32),
            actions=self.actions,
            delay_frames=(0, 1),
            config=self.config,
        )

    def test_transition_lattice_preserves_active_selected_and_delay(self) -> None:
        stay = 0
        right = 1
        delay_zero = 0
        delay_one = 1
        self.assertEqual(
            int(self.transitions.terminal_columns[stay, right, delay_zero, 0, 0]),
            2,
        )
        self.assertEqual(
            int(self.transitions.terminal_columns[stay, right, delay_one, 0, 0]),
            1,
        )
        self.assertEqual(
            int(self.transitions.terminal_columns[right, stay, delay_one, 0, 0]),
            1,
        )
        self.assertFalse(
            self.transitions.terminal_inside[stay, right, delay_zero, 0, 2]
        )

    def test_root_forward_tube_fixes_first_action_and_hidden_branch(self) -> None:
        forward = root_branch_forward_tube(
            transitions=self.transitions,
            layer_count=2,
            root_active_index=0,
            root_row=0,
            root_column=0,
            root_selected_index=1,
            root_branch_index=1,
        )
        self.assertTrue(forward[0, 0, 0, 0])
        self.assertEqual(int(np.count_nonzero(forward[0])), 1)
        self.assertTrue(forward[1, 1, 0, 1])
        self.assertEqual(int(np.count_nonzero(forward[1])), 1)
        self.assertGreater(int(np.count_nonzero(forward[2])), 1)

    def test_terminal_coreach_is_plane_aware_and_optimistic(self) -> None:
        terminal = np.zeros(self.transitions.state_shape, dtype=np.bool_)
        terminal[1, 0, 3] = True
        coreachable = terminal_coreachable_tube(
            transitions=self.transitions,
            layer_count=2,
            terminal_scope=terminal,
        )
        self.assertTrue(coreachable[2, 1, 0, 3])
        self.assertFalse(coreachable[2, 0, 0, 3])
        self.assertTrue(coreachable[1, 0, 0, 1])
        self.assertTrue(coreachable[1, 1, 0, 1])

    def test_prepared_scope_keeps_root_branch_identity(self) -> None:
        prepared_actions = (
            ControlAction("stay", 0.0, 0.0),
            ControlAction("right", 8.0, 0.0),
        )
        bounds = CorridorBounds(left=0.0, right=32.0, top=0.0, bottom=32.0)
        config = CorridorConfig(
            grid_step=16.0,
            frames_per_layer=2,
            horizon_frames=4,
            player_radius=0.0,
        )
        control = RobustControlSpec(
            actions=prepared_actions,
            delay_frames=(0, 1),
            nominal_delay=1,
            active_action="stay",
        )
        prepared = prepare_corridor_problem(
            bounds=bounds,
            config=config,
            robust_control=control,
        )
        scope = prepare_dual_bound_scope(
            prepared_problem=prepared,
            start_x=7.0,
            start_y=9.0,
        )
        self.assertEqual(scope.layer_count, 2)
        self.assertEqual(scope.root_row, 1)
        self.assertEqual(scope.root_column, 0)
        self.assertAlmostEqual(
            scope.root_position_error,
            np.hypot(7.0, -7.0),
        )
        delay_zero = scope.branch_tube(
            root_action="right",
            hidden_delay=0,
        )
        delay_one = scope.branch_tube(
            root_action="right",
            hidden_delay=1,
        )
        self.assertNotEqual(
            np.flatnonzero(delay_zero.forward[1]).tolist(),
            np.flatnonzero(delay_one.forward[1]).tolist(),
        )
        np.testing.assert_array_equal(
            delay_zero.relevant,
            delay_zero.forward & delay_zero.terminal_coreachable,
        )

        overridden = prepare_dual_bound_scope(
            prepared_problem=prepared,
            start_x=7.0,
            start_y=9.0,
            root_active_action="right",
        )
        self.assertEqual(overridden.root_active_index, 1)


if __name__ == "__main__":
    unittest.main()
