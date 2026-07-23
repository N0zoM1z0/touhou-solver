#!/usr/bin/env python3
"""Tests for game-neutral robust backward reachability."""

from __future__ import annotations

import unittest

import numpy as np

from touhou_control.viability import (
    ControlAction,
    ViabilityConfig,
    build_robust_viability_policy,
)


class RobustViabilityTests(unittest.TestCase):
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
