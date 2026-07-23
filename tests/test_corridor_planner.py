#!/usr/bin/env python3
"""Tests for the game-neutral time-expanded corridor planner."""

from __future__ import annotations

import math
import unittest

import numpy as np

from corridor_planner import (
    CorridorBounds,
    CorridorConfig,
    MovingAabbHazard,
    RobustControlSpec,
    SegmentHazard,
    _aabb_clearance_field,
    _aabb_clearance_volume,
    _segment_clearance_field,
    plan_corridor,
)
from touhou_control.viability import ControlAction


BOUNDS = CorridorBounds(0.0, 96.0, 0.0, 96.0)
CONFIG = CorridorConfig(
    grid_step=8.0,
    frames_per_layer=4,
    horizon_frames=32,
    cardinal_speed=4.0,
    diagonal_axis_speed=2.8284270763397217,
    preferred_clearance=6.0,
)


class CorridorPlannerTests(unittest.TestCase):
    def test_sparse_aabb_volume_matches_dense_geometry_below_cap(
        self,
    ) -> None:
        grid_x, grid_y = np.meshgrid(
            np.arange(0.0, 49.0, 8.0, dtype=np.float32),
            np.arange(0.0, 41.0, 8.0, dtype=np.float32),
        )
        hazards = (
            MovingAabbHazard(
                x=-5.0,
                y=4.0,
                velocity_x=2.5,
                velocity_y=1.25,
                half_width=3.0,
                half_height=5.0,
                base_uncertainty=0.5,
                uncertainty_per_frame=0.25,
            ),
            MovingAabbHazard(
                x=52.0,
                y=36.0,
                velocity_x=-1.5,
                velocity_y=-2.0,
                half_width=7.0,
                half_height=2.0,
            ),
        )
        cap = 12.0
        actual = _aabb_clearance_volume(
            grid_x,
            grid_y,
            hazards,
            horizon_frames=8,
            player_radius=2.0,
            clearance_cap=cap,
        )
        dense = np.stack(
            [
                _aabb_clearance_field(
                    grid_x,
                    grid_y,
                    hazards,
                    frame=frame,
                    player_radius=2.0,
                )
                for frame in range(9)
            ]
        )
        np.testing.assert_allclose(
            actual,
            np.minimum(dense, cap),
            atol=2e-5,
        )

    def test_vectorized_segment_field_matches_scalar_finite_geometry(
        self,
    ) -> None:
        grid_x, grid_y = np.meshgrid(
            np.asarray([0.0, 10.0, 20.0], dtype=np.float32),
            np.asarray([0.0, 10.0], dtype=np.float32),
        )
        hazards = (
            SegmentHazard(0.0, 0.0, 0.0, 0.0, 20.0, 2.0, 1.0, 0.5),
            SegmentHazard(
                10.0,
                -10.0,
                math.pi / 2.0,
                0.0,
                20.0,
                1.0,
            ),
            SegmentHazard(20.0, 10.0, 0.0, 0.0, 0.0, 3.0),
        )
        actual = _segment_clearance_field(
            grid_x,
            grid_y,
            hazards,
            frame=4,
            player_radius=2.0,
        )
        expected = np.full(grid_x.shape, np.inf, dtype=np.float64)
        for hazard in hazards:
            cosine = math.cos(hazard.angle)
            sine = math.sin(hazard.angle)
            start_x = hazard.origin_x + cosine * hazard.tail
            start_y = hazard.origin_y + sine * hazard.tail
            end_x = hazard.origin_x + cosine * hazard.head
            end_y = hazard.origin_y + sine * hazard.head
            segment_x = end_x - start_x
            segment_y = end_y - start_y
            length_sq = segment_x**2 + segment_y**2
            if length_sq <= 1e-9:
                distance = np.hypot(grid_x - start_x, grid_y - start_y)
            else:
                projection = np.clip(
                    (
                        (grid_x - start_x) * segment_x
                        + (grid_y - start_y) * segment_y
                    )
                    / length_sq,
                    0.0,
                    1.0,
                )
                distance = np.hypot(
                    grid_x - (start_x + projection * segment_x),
                    grid_y - (start_y + projection * segment_y),
                )
            expected = np.minimum(
                expected,
                distance
                - hazard.half_width
                - 2.0
                - hazard.base_uncertainty
                - hazard.uncertainty_per_frame * 4,
            )
        np.testing.assert_allclose(actual, expected, atol=2e-5)

    def test_clear_field_reaches_preferred_region_without_touching_boundary(self) -> None:
        plan = plan_corridor(
            start_x=48.0,
            start_y=88.0,
            bounds=BOUNDS,
            preferred_x=48.0,
            preferred_y=64.0,
            config=CONFIG,
        )
        self.assertTrue(plan.reachable)
        self.assertGreater(plan.path[-1].y, 0.0)
        self.assertLess(plan.path[-1].y, 96.0)
        self.assertGreater(plan.bottleneck_clearance, 0.0)

    def test_future_wall_commits_to_open_left_corridor(self) -> None:
        hazards = tuple(
            MovingAabbHazard(
                x=float(x),
                y=30.0,
                velocity_x=0.0,
                velocity_y=1.5,
                half_width=5.0,
                half_height=5.0,
            )
            for x in range(32, 97, 8)
        )
        plan = plan_corridor(
            start_x=48.0,
            start_y=88.0,
            bounds=BOUNDS,
            aabbs=hazards,
            preferred_x=48.0,
            preferred_y=64.0,
            config=CONFIG,
        )
        self.assertTrue(plan.reachable)
        self.assertEqual(plan.lane, "left")
        self.assertIsNotNone(plan.gate)
        assert plan.gate is not None
        self.assertLess(plan.gate.x, 32.0)
        self.assertTrue(any(point.x < 32.0 for point in plan.path))

    def test_long_horizon_sees_gate_before_local_horizon_does(self) -> None:
        hazards = tuple(
            MovingAabbHazard(
                x=float(x),
                y=30.0,
                velocity_x=0.0,
                velocity_y=1.5,
                half_width=5.0,
                half_height=5.0,
            )
            for x in range(32, 97, 8)
        )
        local = plan_corridor(
            start_x=48.0,
            start_y=88.0,
            bounds=BOUNDS,
            aabbs=hazards,
            preferred_x=48.0,
            preferred_y=64.0,
            config=CorridorConfig(
                grid_step=8.0,
                frames_per_layer=4,
                horizon_frames=8,
                cardinal_speed=4.0,
                diagonal_axis_speed=2.8284270763397217,
                preferred_clearance=6.0,
            ),
        )
        global_plan = plan_corridor(
            start_x=48.0,
            start_y=88.0,
            bounds=BOUNDS,
            aabbs=hazards,
            preferred_x=48.0,
            preferred_y=64.0,
            config=CONFIG,
        )
        self.assertEqual(local.lane, "center")
        self.assertTrue(all(point.x >= 32.0 for point in local.path))
        self.assertEqual(global_plan.lane, "left")
        self.assertTrue(any(point.x < 32.0 for point in global_plan.path))

    def test_closed_sweeping_wall_proves_corridor_unreachable(self) -> None:
        hazards = tuple(
            MovingAabbHazard(
                x=float(x),
                y=48.0,
                velocity_x=0.0,
                velocity_y=0.0,
                half_width=6.0,
                half_height=50.0,
            )
            for x in range(0, 97, 8)
        )
        plan = plan_corridor(
            start_x=48.0,
            start_y=88.0,
            bounds=BOUNDS,
            aabbs=hazards,
            config=CONFIG,
        )
        self.assertFalse(plan.reachable)
        self.assertEqual(plan.path, ())
        self.assertIsNone(plan.gate)

    def test_required_gate_lane_selects_a_stable_component(self) -> None:
        constrained_config = CorridorConfig(
            grid_step=8.0,
            frames_per_layer=4,
            horizon_frames=32,
            cardinal_speed=4.0,
            diagonal_axis_speed=2.8284270763397217,
            preferred_clearance=20.0,
        )
        plan = plan_corridor(
            start_x=48.0,
            start_y=88.0,
            bounds=BOUNDS,
            preferred_x=48.0,
            preferred_y=64.0,
            required_gate_lane="right",
            config=constrained_config,
        )
        self.assertTrue(plan.reachable)
        self.assertEqual(plan.lane, "right")
        self.assertLess(
            plan.bottleneck_clearance,
            constrained_config.preferred_clearance,
        )
        self.assertIn("commitment", plan.reason)

    def test_required_closed_gate_lane_fails_instead_of_switching(self) -> None:
        hazards = tuple(
            MovingAabbHazard(
                x=float(x),
                y=48.0,
                velocity_x=0.0,
                velocity_y=0.0,
                half_width=4.0,
                half_height=50.0,
            )
            for x in range(32, 65, 8)
        )
        plan = plan_corridor(
            start_x=16.0,
            start_y=88.0,
            bounds=BOUNDS,
            aabbs=hazards,
            required_gate_lane="center",
            config=CONFIG,
        )
        self.assertFalse(plan.reachable)
        self.assertIn("required center", plan.reason)

    def test_waypoint_uses_first_point_at_or_after_requested_frame(self) -> None:
        plan = plan_corridor(
            start_x=48.0,
            start_y=88.0,
            bounds=BOUNDS,
            preferred_x=48.0,
            preferred_y=64.0,
            config=CONFIG,
        )
        self.assertEqual(plan.waypoint(9).frame, 12)
        self.assertEqual(plan.waypoint(999), plan.path[-1])

    def test_robust_mode_returns_backward_policy_not_only_waypoint(self) -> None:
        actions = (
            ControlAction("stay", 0.0, 0.0),
            ControlAction("left", -4.0, 0.0),
            ControlAction("right", 4.0, 0.0),
        )
        plan = plan_corridor(
            start_x=48.0,
            start_y=88.0,
            bounds=BOUNDS,
            preferred_x=32.0,
            preferred_y=64.0,
            config=CONFIG,
            robust_control=RobustControlSpec(
                actions=actions,
                delay_frames=(0, 1, 2),
                nominal_delay=1,
                active_action="stay",
            ),
        )
        self.assertTrue(plan.reachable)
        self.assertEqual(plan.planning_mode, "robust_viability")
        self.assertIsNotNone(plan.viability_policy)
        self.assertGreater(plan.initial_safe_action_count, 0)
        self.assertGreater(plan.initial_repair_volume, 0)
        assert plan.viability_policy is not None
        query = plan.viability_policy.query(
            frame=4,
            x=plan.path[1].x,
            y=plan.path[1].y,
            active_action=plan.path[1].x < 48.0 and "left" or "stay",
        )
        self.assertTrue(query.available)

    def test_robust_mode_proves_initial_action_set_empty(self) -> None:
        wall = (
            MovingAabbHazard(
                x=48.0,
                y=88.0,
                velocity_x=0.0,
                velocity_y=0.0,
                half_width=8.0,
                half_height=8.0,
            ),
        )
        plan = plan_corridor(
            start_x=48.0,
            start_y=88.0,
            bounds=BOUNDS,
            aabbs=wall,
            config=CONFIG,
            robust_control=RobustControlSpec(
                actions=(ControlAction("stay", 0.0, 0.0),),
                delay_frames=(0,),
                nominal_delay=0,
                active_action="stay",
            ),
        )
        self.assertFalse(plan.reachable)
        self.assertEqual(plan.planning_mode, "robust_viability")
        self.assertIsNotNone(plan.viability_policy)
        self.assertIn("action set is empty", plan.reason)


if __name__ == "__main__":
    unittest.main()
