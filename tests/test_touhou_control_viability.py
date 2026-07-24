#!/usr/bin/env python3
"""Tests for game-neutral robust backward reachability."""

from __future__ import annotations

import unittest

import numpy as np

from touhou_control import native_backend
from touhou_control.viability import (
    ControlAction,
    SafetyValueQuery,
    ViabilityConfig,
    build_robust_safety_value_policy,
    build_robust_viability_policy,
)
from touhou_control.native_backend import available as native_available


class RobustViabilityTests(unittest.TestCase):
    def test_safety_value_certificate_pays_initial_off_grid_error(
        self,
    ) -> None:
        query = SafetyValueQuery(
            available=True,
            layer=0,
            row=0,
            column=0,
            active_action="stay",
            state_value=1.0,
            action_values=(("left", 0.75), ("right", 0.4)),
            best_actions=("left",),
            position_error=0.5,
            reason="test",
        )
        self.assertEqual(query.certified_actions(), ("left",))
        self.assertEqual(
            query.certified_actions(additional_position_error=0.3),
            (),
        )
        with self.assertRaisesRegex(ValueError, "nonnegative"):
            query.certified_actions(additional_position_error=-0.1)

    def test_safety_value_threshold_exactly_recovers_boolean_policy(
        self,
    ) -> None:
        rng = np.random.default_rng(0xCE0087)
        actions = (
            ControlAction("stay", 0.0, 0.0),
            ControlAction("left", -0.75, 0.0),
            ControlAction("right", 0.75, 0.0),
        )
        x_axis = np.arange(5, dtype=np.float32) * 2.0
        y_axis = np.arange(3, dtype=np.float32) * 2.0
        clearance = rng.uniform(
            -3.0,
            7.0,
            size=(7, len(y_axis), len(x_axis)),
        ).astype(np.float32)
        value_policy = build_robust_safety_value_policy(
            x_axis=x_axis,
            y_axis=y_axis,
            clearance_volume=clearance,
            actions=actions,
            delay_frames=(0, 2, 3),
            nominal_delay=2,
            config=ViabilityConfig(
                frames_per_layer=3,
                clamp_to_bounds=False,
            ),
            backend="numpy",
        )
        for threshold in (-1.25, 0.0, 2.5):
            boolean = build_robust_viability_policy(
                x_axis=x_axis,
                y_axis=y_axis,
                clearance_volume=clearance,
                actions=actions,
                delay_frames=(0, 2, 3),
                nominal_delay=2,
                config=ViabilityConfig(
                    frames_per_layer=3,
                    required_clearance=threshold,
                    clamp_to_bounds=False,
                ),
                backend="numpy",
            )
            viable, masks = value_policy.threshold_arrays(threshold)
            np.testing.assert_array_equal(viable, boolean.viable)
            np.testing.assert_array_equal(masks, boolean.safe_action_masks)

    def test_empty_boolean_kernel_retains_continuous_least_bad_action(
        self,
    ) -> None:
        actions = (
            ControlAction("stay", 0.0, 0.0),
            ControlAction("right", 1.0, 0.0),
        )
        clearance = np.full((3, 2, 5), 10.0, dtype=np.float32)
        clearance[2, :, 1] = -5.0
        clearance[2, :, 3] = -1.0
        value_policy = build_robust_safety_value_policy(
            x_axis=np.arange(5, dtype=np.float32),
            y_axis=np.asarray([0.0, 1.0], dtype=np.float32),
            clearance_volume=clearance,
            actions=actions,
            delay_frames=(0,),
            nominal_delay=0,
            config=ViabilityConfig(
                frames_per_layer=2,
                clamp_to_bounds=False,
            ),
            backend="numpy",
        )
        query = value_policy.query(
            frame=0,
            x=1.0,
            y=0.0,
            active_action="stay",
        )
        self.assertTrue(query.available)
        self.assertEqual(query.best_actions, ("right",))
        self.assertEqual(query.action_value("stay"), -5.0)
        self.assertEqual(query.action_value("right"), -1.0)
        viable, masks = value_policy.threshold_arrays(0.0)
        self.assertFalse(viable[0, 0, 0, 1])
        self.assertEqual(int(masks[0, 0, 0, 1]), 0)
        compact = build_robust_safety_value_policy(
            x_axis=np.arange(5, dtype=np.float32),
            y_axis=np.asarray([0.0, 1.0], dtype=np.float32),
            clearance_volume=clearance,
            actions=actions,
            delay_frames=(0,),
            nominal_delay=0,
            config=ViabilityConfig(
                frames_per_layer=2,
                clamp_to_bounds=False,
            ),
            backend="numpy",
            compact=True,
        )
        compact_query = compact.query(
            frame=0,
            x=1.0,
            y=0.0,
            active_action="stay",
        )
        self.assertEqual(compact_query.best_actions, ("right",))
        self.assertEqual(compact_query.action_values, ())
        self.assertEqual(compact_query.state_value, -1.0)
        with self.assertRaisesRegex(ValueError, "does not retain"):
            compact.threshold_arrays(0.0)

    @unittest.skipUnless(
        native_available(),
        "native viability backend is not built",
    )
    def test_native_safety_value_matches_numpy_oracle(self) -> None:
        rng = np.random.default_rng(0x5AFE0087)
        actions = (
            ControlAction("stay", 0.0, 0.0),
            ControlAction("left", -0.8, 0.0),
            ControlAction("right", 0.8, 0.0),
            ControlAction("up_right", 0.6, -0.6),
        )
        x_axis = np.arange(5, dtype=np.float32) * 2.0
        y_axis = np.arange(4, dtype=np.float32) * 2.0
        config = ViabilityConfig(
            frames_per_layer=3,
            clamp_to_bounds=False,
        )
        for _ in range(12):
            clearance = rng.uniform(
                -2.0,
                8.0,
                size=(7, len(y_axis), len(x_axis)),
            ).astype(np.float32)
            reference = build_robust_safety_value_policy(
                x_axis=x_axis,
                y_axis=y_axis,
                clearance_volume=clearance,
                actions=actions,
                delay_frames=(0, 2, 3),
                nominal_delay=2,
                config=config,
                backend="numpy",
            )
            native = build_robust_safety_value_policy(
                x_axis=x_axis,
                y_axis=y_axis,
                clearance_volume=clearance,
                actions=actions,
                delay_frames=(0, 2, 3),
                nominal_delay=2,
                config=config,
                backend="native",
            )
            np.testing.assert_allclose(
                native.state_values,
                reference.state_values,
                rtol=0.0,
                atol=2e-6,
            )
            np.testing.assert_allclose(
                native.action_values,
                reference.action_values,
                rtol=0.0,
                atol=2e-6,
            )
            optimized = native_backend.build_safety_policy_arrays(
                x_axis=x_axis,
                y_axis=y_axis,
                clearance_volume=clearance,
                velocity_x=np.asarray(
                    [action.velocity_x for action in actions],
                    dtype=np.float64,
                ),
                velocity_y=np.asarray(
                    [action.velocity_y for action in actions],
                    dtype=np.float64,
                ),
                delay_frames=np.asarray((0, 2, 3), dtype=np.int32),
                frames_per_layer=config.frames_per_layer,
                clamp_to_bounds=config.clamp_to_bounds,
            )
            self.assertIsNotNone(optimized)
            optimized_values, optimized_masks = optimized
            np.testing.assert_allclose(
                optimized_values,
                reference.state_values,
                rtol=0.0,
                atol=2e-6,
            )
            best_values = np.max(reference.action_values, axis=2)
            best_bits = np.left_shift(
                np.uint32(1),
                np.arange(len(actions), dtype=np.uint32),
            )[None, None, :, None, None]
            expected_masks = np.bitwise_or.reduce(
                np.where(
                    reference.action_values == best_values[:, :, None],
                    best_bits,
                    np.uint32(0),
                ),
                axis=2,
            )
            np.testing.assert_array_equal(
                optimized_masks,
                expected_masks,
            )
            self.assertEqual(native.backend, "native")

    @unittest.skipUnless(
        native_available(),
        "native viability backend is not built",
    )
    def test_native_kernel_matches_numpy_for_randomized_delay_game(
        self,
    ) -> None:
        rng = np.random.default_rng(0xCE0044)
        actions = (
            ControlAction("stay", 0.0, 0.0),
            ControlAction("left", -0.8, 0.0),
            ControlAction("right", 0.8, 0.0),
            ControlAction("up_right", 0.6, -0.6),
        )
        x_axis = np.arange(5, dtype=np.float32) * 2.0
        y_axis = np.arange(4, dtype=np.float32) * 2.0
        config = ViabilityConfig(
            frames_per_layer=3,
            clamp_to_bounds=False,
        )
        for _ in range(12):
            clearance = rng.uniform(
                -2.0,
                8.0,
                size=(7, len(y_axis), len(x_axis)),
            ).astype(np.float32)
            reference = build_robust_viability_policy(
                x_axis=x_axis,
                y_axis=y_axis,
                clearance_volume=clearance,
                actions=actions,
                delay_frames=(0, 2, 3),
                nominal_delay=2,
                config=config,
                backend="numpy",
            )
            native = build_robust_viability_policy(
                x_axis=x_axis,
                y_axis=y_axis,
                clearance_volume=clearance,
                actions=actions,
                delay_frames=(0, 2, 3),
                nominal_delay=2,
                config=config,
                backend="native",
            )
            np.testing.assert_array_equal(native.viable, reference.viable)
            np.testing.assert_array_equal(
                native.safe_action_masks,
                reference.safe_action_masks,
            )
            self.assertEqual(native.backend, "native")

    def test_clear_lattice_exposes_all_robust_actions_and_repair_volume(
        self,
    ) -> None:
        actions = (
            ControlAction("stay", 0.0, 0.0),
            ControlAction("right", 1.0, 0.0),
        )
        policy = build_robust_viability_policy(
            x_axis=np.asarray([0.0, 1.0, 2.0], dtype=np.float32),
            y_axis=np.asarray([0.0, 1.0], dtype=np.float32),
            clearance_volume=np.full((5, 2, 3), 100.0, dtype=np.float32),
            actions=actions,
            delay_frames=(0, 1),
            nominal_delay=1,
            config=ViabilityConfig(frames_per_layer=2),
        )
        query = policy.query(
            frame=0,
            x=1.0,
            y=0.0,
            active_action="stay",
        )
        self.assertTrue(query.available)
        self.assertTrue(query.state_viable)
        self.assertEqual(query.safe_actions, ("stay", "right"))
        self.assertGreater(query.repair_volume("stay"), 0)
        self.assertEqual(policy.layer_count, 2)
        self.assertEqual(policy.horizon_frames, 4)

    def test_query_and_rollout_projection_share_round_to_even_ties(
        self,
    ) -> None:
        policy = build_robust_viability_policy(
            x_axis=np.asarray([0.0, 16.0, 32.0], dtype=np.float32),
            y_axis=np.asarray([0.0, 16.0], dtype=np.float32),
            clearance_volume=np.full((3, 2, 3), 100.0, dtype=np.float32),
            actions=(ControlAction("stay", 0.0, 0.0),),
            delay_frames=(0,),
            nominal_delay=0,
            config=ViabilityConfig(frames_per_layer=2),
        )
        self.assertEqual(
            policy.project_to_lattice(x=8.0, y=0.0)[2:4],
            (0, 0),
        )
        self.assertEqual(
            policy.project_to_lattice(x=24.0, y=0.0)[2:4],
            (0, 2),
        )
        self.assertEqual(
            policy.query(
                frame=0,
                x=24.0,
                y=0.0,
                active_action="stay",
            ).column,
            2,
        )

    def test_repair_volume_is_computed_exactly_for_the_queried_state(
        self,
    ) -> None:
        actions = (
            ControlAction("stay", 0.0, 0.0),
            ControlAction("right", 1.0, 0.0),
        )
        policy = build_robust_viability_policy(
            x_axis=np.asarray([0.0, 1.0, 2.0], dtype=np.float32),
            y_axis=np.asarray([0.0, 1.0], dtype=np.float32),
            clearance_volume=np.full((5, 2, 3), 100.0, dtype=np.float32),
            actions=actions,
            delay_frames=(0, 1),
            nominal_delay=1,
            config=ViabilityConfig(
                frames_per_layer=2,
                repair_radius_cells=0,
            ),
        )
        first = policy.query(
            frame=0,
            x=1.0,
            y=0.0,
            active_action="stay",
        )
        terminal_predecessor = policy.query(
            frame=2,
            x=1.0,
            y=0.0,
            active_action="stay",
        )
        self.assertEqual(first.repair_volume("stay"), 2)
        self.assertEqual(terminal_predecessor.repair_volume("stay"), 1)

    def test_action_is_rejected_when_one_delay_branch_crosses_hazard(
        self,
    ) -> None:
        actions = (
            ControlAction("stay", 0.0, 0.0),
            ControlAction("right", 1.0, 0.0),
        )
        clearance = np.full((3, 2, 3), 100.0, dtype=np.float32)
        clearance[1, :, 1] = -1.0
        policy = build_robust_viability_policy(
            x_axis=np.asarray([0.0, 1.0, 2.0], dtype=np.float32),
            y_axis=np.asarray([0.0, 1.0], dtype=np.float32),
            clearance_volume=clearance,
            actions=actions,
            delay_frames=(0, 1),
            nominal_delay=1,
            config=ViabilityConfig(frames_per_layer=2),
        )
        query = policy.query(
            frame=0,
            x=0.0,
            y=0.0,
            active_action="stay",
        )
        self.assertTrue(query.state_viable)
        self.assertEqual(query.safe_actions, ("stay",))

    def test_empty_kernel_exposes_soft_recovery_without_claiming_safety(
        self,
    ) -> None:
        actions = (
            ControlAction("stay", 0.0, 0.0),
            ControlAction("right", 1.0, 0.0),
        )
        clearance = np.full((3, 2, 4), 100.0, dtype=np.float32)
        clearance[1] = -1.0
        policy = build_robust_viability_policy(
            x_axis=np.arange(4, dtype=np.float32),
            y_axis=np.asarray([0.0, 1.0], dtype=np.float32),
            clearance_volume=clearance,
            actions=actions,
            delay_frames=(0, 1),
            nominal_delay=1,
            config=ViabilityConfig(frames_per_layer=2),
        )
        query = policy.query(
            frame=0,
            x=1.0,
            y=0.0,
            active_action="stay",
        )
        self.assertFalse(query.state_viable)
        self.assertEqual(query.safe_actions, ())
        self.assertTrue(query.repair_volumes)
        self.assertGreater(query.repair_volume("stay"), 0)
        self.assertIn("recovery neighborhoods found", query.reason)

    def test_empty_neighborhood_exposes_robust_distance_to_distant_kernel(
        self,
    ) -> None:
        actions = (
            ControlAction("stay", 0.0, 0.0),
            ControlAction("right", 1.0, 0.0),
        )
        clearance = np.full((3, 2, 5), -1.0, dtype=np.float32)
        clearance[:2] = 100.0
        clearance[2, :, 4] = 100.0
        policy = build_robust_viability_policy(
            x_axis=np.arange(5, dtype=np.float32),
            y_axis=np.asarray([0.0, 1.0], dtype=np.float32),
            clearance_volume=clearance,
            actions=actions,
            delay_frames=(0, 1),
            nominal_delay=1,
            config=ViabilityConfig(
                frames_per_layer=2,
                repair_radius_cells=0,
            ),
        )
        query = policy.query(
            frame=0,
            x=0.0,
            y=0.0,
            active_action="stay",
        )
        self.assertFalse(query.state_viable)
        self.assertEqual(query.safe_actions, ())
        self.assertEqual(query.repair_volumes, ())
        self.assertEqual(query.recovery_distance("stay"), 4.0)
        self.assertEqual(query.recovery_distance("right"), 3.0)
        self.assertIn("distant recovery found", query.reason)

    def test_exists_action_forall_delay_is_not_swapped(self) -> None:
        actions = (
            ControlAction("stay", 0.0, 0.0),
            ControlAction("left", -1.0, 0.0),
            ControlAction("right", 1.0, 0.0),
        )
        clearance = np.full((3, 2, 5), -1.0, dtype=np.float32)
        clearance[0, :, 2] = 100.0
        clearance[1, :, (1, 2, 3)] = 100.0
        clearance[2, :, (0, 3)] = 100.0

        robust = build_robust_viability_policy(
            x_axis=np.arange(5, dtype=np.float32),
            y_axis=np.asarray([0.0, 1.0], dtype=np.float32),
            clearance_volume=clearance,
            actions=actions,
            delay_frames=(0, 1),
            nominal_delay=1,
            config=ViabilityConfig(
                frames_per_layer=2,
                clamp_to_bounds=False,
            ),
        )
        query = robust.query(
            frame=0,
            x=2.0,
            y=0.0,
            active_action="stay",
        )
        self.assertFalse(query.state_viable)
        self.assertEqual(query.safe_actions, ())

        delay_zero = build_robust_viability_policy(
            x_axis=np.arange(5, dtype=np.float32),
            y_axis=np.asarray([0.0, 1.0], dtype=np.float32),
            clearance_volume=clearance,
            actions=actions,
            delay_frames=(0,),
            nominal_delay=0,
            config=ViabilityConfig(
                frames_per_layer=2,
                clamp_to_bounds=False,
            ),
        )
        delay_one = build_robust_viability_policy(
            x_axis=np.arange(5, dtype=np.float32),
            y_axis=np.asarray([0.0, 1.0], dtype=np.float32),
            clearance_volume=clearance,
            actions=actions,
            delay_frames=(1,),
            nominal_delay=1,
            config=ViabilityConfig(
                frames_per_layer=2,
                clamp_to_bounds=False,
            ),
        )
        self.assertEqual(
            delay_zero.query(
                frame=0,
                x=2.0,
                y=0.0,
                active_action="stay",
            ).safe_actions,
            ("left",),
        )
        self.assertEqual(
            delay_one.query(
                frame=0,
                x=2.0,
                y=0.0,
                active_action="stay",
            ).safe_actions,
            ("right",),
        )

    def test_active_action_is_part_of_delay_state(self) -> None:
        actions = (
            ControlAction("stay", 0.0, 0.0),
            ControlAction("right", 1.0, 0.0),
        )
        clearance = np.full((2, 2, 3), 100.0, dtype=np.float32)
        clearance[1, :, 2] = -1.0
        policy = build_robust_viability_policy(
            x_axis=np.asarray([0.0, 1.0, 2.0], dtype=np.float32),
            y_axis=np.asarray([0.0, 1.0], dtype=np.float32),
            clearance_volume=clearance,
            actions=actions,
            delay_frames=(1,),
            nominal_delay=1,
            config=ViabilityConfig(frames_per_layer=1),
        )
        staying = policy.query(
            frame=0,
            x=1.0,
            y=0.0,
            active_action="stay",
        )
        moving = policy.query(
            frame=0,
            x=1.0,
            y=0.0,
            active_action="right",
        )
        self.assertTrue(staying.state_viable)
        self.assertFalse(moving.state_viable)

    def test_nearest_cell_clearance_pays_continuous_sampling_error(
        self,
    ) -> None:
        actions = (
            ControlAction("stay", 0.0, 0.0),
            ControlAction("right_half", 0.5, 0.0),
        )
        clearance = np.full((2, 2, 2), 100.0, dtype=np.float32)
        clearance[1, :, 0] = 0.4
        policy = build_robust_viability_policy(
            x_axis=np.asarray([0.0, 2.0], dtype=np.float32),
            y_axis=np.asarray([0.0, 2.0], dtype=np.float32),
            clearance_volume=clearance,
            actions=actions,
            delay_frames=(0,),
            nominal_delay=0,
            config=ViabilityConfig(frames_per_layer=1),
        )
        query = policy.query(
            frame=0,
            x=0.0,
            y=0.0,
            active_action="stay",
        )
        self.assertNotIn("right_half", query.safe_actions)

    def test_delay_must_fit_control_layer(self) -> None:
        with self.assertRaisesRegex(ValueError, "cannot exceed"):
            build_robust_viability_policy(
                x_axis=np.asarray([0.0, 1.0], dtype=np.float32),
                y_axis=np.asarray([0.0, 1.0], dtype=np.float32),
                clearance_volume=np.ones((3, 2, 2), dtype=np.float32),
                actions=(ControlAction("stay", 0.0, 0.0),),
                delay_frames=(3,),
                nominal_delay=3,
                config=ViabilityConfig(frames_per_layer=2),
            )

    def test_noncontiguous_delay_support_selects_cached_geometry(self) -> None:
        policy = build_robust_viability_policy(
            x_axis=np.asarray([0.0, 1.0, 2.0], dtype=np.float32),
            y_axis=np.asarray([0.0, 1.0], dtype=np.float32),
            clearance_volume=np.full((3, 2, 3), 100.0, dtype=np.float32),
            actions=(
                ControlAction("stay", 0.0, 0.0),
                ControlAction("right", 1.0, 0.0),
            ),
            delay_frames=(0, 2),
            nominal_delay=2,
            config=ViabilityConfig(frames_per_layer=2),
        )
        query = policy.query(
            frame=0,
            x=1.0,
            y=0.0,
            active_action="stay",
        )
        self.assertTrue(query.state_viable)
        self.assertEqual(policy.delay_frames, (0, 2))


if __name__ == "__main__":
    unittest.main()
