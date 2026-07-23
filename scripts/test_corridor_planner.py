#!/usr/bin/env python3
"""Tests for the game-neutral time-expanded corridor planner."""

from __future__ import annotations

import unittest

from corridor_planner import (
    CorridorBounds,
    CorridorConfig,
    MovingAabbHazard,
    plan_corridor,
)


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


if __name__ == "__main__":
    unittest.main()
