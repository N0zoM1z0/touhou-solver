#!/usr/bin/env python3
"""Tests for the independent weight-free robust-survival oracle."""

from __future__ import annotations

import unittest

import numpy as np

from touhou_control import native_backend
from touhou_control.adversarial import (
    AdversarialAabb,
    AdversarialScenario,
    generate_adversarial_scenario,
    reference_clearance_volume,
)
from touhou_control.reachability_oracle import (
    scalar_robust_survival_query,
)
from touhou_control.viability import (
    ControlAction,
    ViabilityConfig,
    build_robust_safety_value_policy,
    build_robust_viability_policy,
)
from touhou_control.trajectory import PiecewiseLinearTrajectory


class RobustSurvivalOracleTests(unittest.TestCase):
    def test_native_fused_survival_labels_match_scalar_oracle(
        self,
    ) -> None:
        actions = (
            ControlAction("stay", 0.0, 0.0),
            ControlAction("left", -2.0, 0.0),
            ControlAction("right", 2.0, 0.0),
        )
        x_axis = np.arange(8.0, 40.1, 8.0, dtype=np.float32)
        y_axis = np.arange(16.0, 40.1, 8.0, dtype=np.float32)
        config = ViabilityConfig(
            frames_per_layer=2,
            required_clearance=0.25,
            clamp_to_bounds=True,
        )
        scenario = generate_adversarial_scenario(
            0xCE0098,
            hazard_count=10,
            horizon_frames=4,
            left=8.0,
            right=40.0,
            top=16.0,
            bottom=40.0,
            maximum_events=2,
        )
        clearance = reference_clearance_volume(
            x_axis=x_axis,
            y_axis=y_axis,
            scenario=scenario,
            player_radius=2.0,
            clearance_cap=48.0,
        )
        native = native_backend.build_survival_viability_arrays(
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
            delay_frames=np.asarray((0, 1, 2), dtype=np.int32),
            frames_per_layer=config.frames_per_layer,
            required_clearance=config.required_clearance,
            clamp_to_bounds=config.clamp_to_bounds,
        )
        if native is None:
            self.skipTest("native survival-viability backend is not built")
        (
            survival_frames,
            bottleneck_margins,
            best_masks,
            viable,
            safe_masks,
        ) = native
        for layer in range(survival_frames.shape[0] - 1):
            for active_index, active in enumerate(actions):
                for row in range(len(y_axis)):
                    for column in range(len(x_axis)):
                        scalar = scalar_robust_survival_query(
                            x_axis=x_axis,
                            y_axis=y_axis,
                            clearance_volume=clearance,
                            actions=actions,
                            delay_frames=(0, 1, 2),
                            config=config,
                            layer=layer,
                            row=row,
                            column=column,
                            active_action=active.name,
                        )
                        state_index = (
                            layer,
                            active_index,
                            row,
                            column,
                        )
                        self.assertEqual(
                            int(survival_frames[state_index]),
                            scalar.state_label.guaranteed_frames,
                        )
                        self.assertAlmostEqual(
                            float(bottleneck_margins[state_index]),
                            scalar.state_label.bottleneck_margin,
                            places=5,
                        )
                        expected_best_mask = 0
                        expected_safe_mask = 0
                        for selected_index, selected in enumerate(actions):
                            if selected.name in scalar.best_actions:
                                expected_best_mask |= 1 << selected_index
                            label = scalar.action_label(selected.name)
                            if (
                                label.guaranteed_frames
                                == scalar.remaining_frames
                                and label.bottleneck_margin > 0.0
                            ):
                                expected_safe_mask |= 1 << selected_index
                        action_index = (
                            layer,
                            active_index,
                            row,
                            column,
                        )
                        self.assertEqual(
                            int(best_masks[action_index]),
                            expected_best_mask,
                        )
                        self.assertEqual(
                            int(safe_masks[action_index]),
                            expected_safe_mask,
                        )
                        self.assertEqual(
                            bool(viable[state_index]),
                            scalar.winning,
                        )

    def test_scalar_winning_labels_match_vectorized_boolean_game(
        self,
    ) -> None:
        actions = (
            ControlAction("stay", 0.0, 0.0),
            ControlAction("left", -4.0, 0.0),
            ControlAction("right", 4.0, 0.0),
        )
        x_axis = np.arange(8.0, 40.1, 8.0, dtype=np.float32)
        y_axis = np.arange(16.0, 40.1, 8.0, dtype=np.float32)
        config = ViabilityConfig(
            frames_per_layer=2,
            required_clearance=0.0,
            clamp_to_bounds=True,
        )
        for seed in (17, 8008, 0xBAD5EED):
            with self.subTest(seed=seed):
                scenario = generate_adversarial_scenario(
                    seed,
                    hazard_count=12,
                    horizon_frames=4,
                    left=8.0,
                    right=40.0,
                    top=16.0,
                    bottom=40.0,
                    maximum_events=2,
                )
                clearance = reference_clearance_volume(
                    x_axis=x_axis,
                    y_axis=y_axis,
                    scenario=scenario,
                    player_radius=2.0,
                    clearance_cap=48.0,
                )
                vectorized = build_robust_viability_policy(
                    x_axis=x_axis,
                    y_axis=y_axis,
                    clearance_volume=clearance,
                    actions=actions,
                    delay_frames=(0, 1, 2),
                    nominal_delay=1,
                    config=config,
                    backend="numpy",
                )
                for active_index, active in enumerate(actions):
                    for row in range(len(y_axis)):
                        for column in range(len(x_axis)):
                            scalar = scalar_robust_survival_query(
                                x_axis=x_axis,
                                y_axis=y_axis,
                                clearance_volume=clearance,
                                actions=actions,
                                delay_frames=(0, 1, 2),
                                config=config,
                                layer=0,
                                row=row,
                                column=column,
                                active_action=active.name,
                            )
                            self.assertEqual(
                                scalar.winning,
                                bool(
                                    vectorized.viable[
                                        0,
                                        active_index,
                                        row,
                                        column,
                                    ]
                                ),
                            )
                            mask = int(
                                vectorized.safe_action_masks[
                                    0,
                                    active_index,
                                    row,
                                    column,
                                ]
                            )
                            for selected_index, selected in enumerate(
                                actions
                            ):
                                label = scalar.action_label(selected.name)
                                action_wins = (
                                    label.guaranteed_frames
                                    == scalar.remaining_frames
                                    and label.bottleneck_margin > 0.0
                                )
                                self.assertEqual(
                                    action_wins,
                                    bool(mask & (1 << selected_index)),
                                )

    def test_survival_horizon_outranks_shallower_immediate_collision(
        self,
    ) -> None:
        actions = (
            ControlAction("stay", 0.0, 0.0),
            ControlAction("right", 1.0, 0.0),
        )
        x_axis = np.asarray([0.0, 1.0, 2.0], dtype=np.float32)
        y_axis = np.asarray([0.0, 1.0], dtype=np.float32)
        clearance = np.full((3, 2, 3), 5.0, dtype=np.float32)
        clearance[1, :, 0] = -0.1
        clearance[2, :, 0] = -0.1
        clearance[2, :, 1:] = -10.0
        config = ViabilityConfig(
            frames_per_layer=1,
            clamp_to_bounds=True,
        )
        scalar = scalar_robust_survival_query(
            x_axis=x_axis,
            y_axis=y_axis,
            clearance_volume=clearance,
            actions=actions,
            delay_frames=(0,),
            config=config,
            layer=0,
            row=0,
            column=0,
            active_action="stay",
        )
        margin_policy = build_robust_safety_value_policy(
            x_axis=x_axis,
            y_axis=y_axis,
            clearance_volume=clearance,
            actions=actions,
            delay_frames=(0,),
            nominal_delay=0,
            config=config,
            backend="numpy",
        )
        margin_query = margin_policy.query(
            frame=0,
            x=0.0,
            y=0.0,
            active_action="stay",
        )
        self.assertEqual(margin_query.best_actions, ("stay",))
        self.assertEqual(scalar.best_actions, ("right",))
        self.assertEqual(
            scalar.action_label("stay").guaranteed_frames,
            0,
        )
        self.assertEqual(
            scalar.action_label("right").guaranteed_frames,
            1,
        )

    def test_narrow_tunnel_requires_spatial_refinement_not_a_weight(
        self,
    ) -> None:
        actions = (ControlAction("stay", 0.0, 0.0),)
        y_axis = np.asarray([0.0, 1.0], dtype=np.float32)
        config = ViabilityConfig(
            frames_per_layer=1,
            clamp_to_bounds=True,
        )

        def tunnel(axis: np.ndarray) -> np.ndarray:
            field = 0.4 - np.abs(axis.astype(np.float32) - 1.0)
            return np.broadcast_to(
                field[None, None, :],
                (3, len(y_axis), len(axis)),
            ).copy()

        coarse_x = np.asarray([0.0, 2.0, 4.0], dtype=np.float32)
        fine_x = np.asarray(
            [0.0, 1.0, 2.0, 3.0, 4.0],
            dtype=np.float32,
        )
        coarse = scalar_robust_survival_query(
            x_axis=coarse_x,
            y_axis=y_axis,
            clearance_volume=tunnel(coarse_x),
            actions=actions,
            delay_frames=(0,),
            config=config,
            layer=0,
            row=0,
            column=0,
            active_action="stay",
        )
        fine = scalar_robust_survival_query(
            x_axis=fine_x,
            y_axis=y_axis,
            clearance_volume=tunnel(fine_x),
            actions=actions,
            delay_frames=(0,),
            config=config,
            layer=0,
            row=0,
            column=1,
            active_action="stay",
        )
        self.assertFalse(coarse.winning)
        self.assertTrue(fine.winning)
        self.assertEqual(fine.best_actions, ("stay",))

    def test_future_birth_must_be_in_the_event_model_or_revalidated(
        self,
    ) -> None:
        x_axis = np.asarray([0.0, 1.0], dtype=np.float32)
        y_axis = np.asarray([0.0, 1.0], dtype=np.float32)
        actions = (ControlAction("stay", 0.0, 0.0),)
        config = ViabilityConfig(
            frames_per_layer=1,
            clamp_to_bounds=True,
        )
        unmodeled = reference_clearance_volume(
            x_axis=x_axis,
            y_axis=y_axis,
            scenario=AdversarialScenario(0xCE0092, 2, ()),
            player_radius=0.0,
            clearance_cap=48.0,
        )
        birth = AdversarialAabb(
            PiecewiseLinearTrajectory(0.0, 0.0, 0.0, 0.0),
            half_width=2.0,
            half_height=2.0,
            active_from_frame=1,
        )
        modeled = reference_clearance_volume(
            x_axis=x_axis,
            y_axis=y_axis,
            scenario=AdversarialScenario(0xCE0092, 2, (birth,)),
            player_radius=0.0,
            clearance_cap=48.0,
        )
        stale_query = scalar_robust_survival_query(
            x_axis=x_axis,
            y_axis=y_axis,
            clearance_volume=unmodeled,
            actions=actions,
            delay_frames=(0,),
            config=config,
            layer=0,
            row=0,
            column=0,
            active_action="stay",
        )
        birth_aware_query = scalar_robust_survival_query(
            x_axis=x_axis,
            y_axis=y_axis,
            clearance_volume=modeled,
            actions=actions,
            delay_frames=(0,),
            config=config,
            layer=0,
            row=0,
            column=0,
            active_action="stay",
        )
        self.assertTrue(stale_query.winning)
        self.assertFalse(birth_aware_query.winning)
        self.assertEqual(
            birth_aware_query.state_label.guaranteed_frames,
            0,
        )


if __name__ == "__main__":
    unittest.main()
