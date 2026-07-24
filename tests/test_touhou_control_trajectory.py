#!/usr/bin/env python3
"""Tests for game-neutral piecewise-linear motion."""

from __future__ import annotations

import unittest

from touhou_control.trajectory import (
    PiecewiseLinearTrajectory,
    VelocityChange,
)


class PiecewiseLinearTrajectoryTests(unittest.TestCase):
    def test_velocity_change_applies_before_movement_on_event_frame(self) -> None:
        trajectory = PiecewiseLinearTrajectory(
            10.0,
            20.0,
            2.0,
            -1.0,
            (VelocityChange(3, -4.0, 0.5),),
        )
        self.assertEqual(trajectory.position(2), (14.0, 18.0))
        self.assertEqual(trajectory.position(3), (10.0, 18.5))
        self.assertEqual(trajectory.position(5), (2.0, 19.5))
        self.assertEqual(trajectory.velocity(2), (2.0, -1.0))
        self.assertEqual(trajectory.velocity(3), (-4.0, 0.5))

    def test_multiple_changes_compose_without_stage_semantics(self) -> None:
        trajectory = PiecewiseLinearTrajectory(
            0.0,
            0.0,
            1.0,
            0.0,
            (
                VelocityChange(2, 0.0, 0.0),
                VelocityChange(5, 0.0, 2.0),
            ),
        )
        self.assertEqual(trajectory.position(1), (1.0, 0.0))
        self.assertEqual(trajectory.position(4), (1.0, 0.0))
        self.assertEqual(trajectory.position(6), (1.0, 4.0))

    def test_past_projection_uses_observed_velocity_without_reversing_events(
        self,
    ) -> None:
        trajectory = PiecewiseLinearTrajectory(
            4.0,
            8.0,
            1.0,
            -2.0,
            (VelocityChange(2, 0.0, 0.0),),
        )
        self.assertEqual(trajectory.position(-2), (2.0, 12.0))

    def test_change_frames_must_be_strictly_increasing(self) -> None:
        with self.assertRaises(ValueError):
            PiecewiseLinearTrajectory(
                0.0,
                0.0,
                0.0,
                0.0,
                (
                    VelocityChange(3, 1.0, 0.0),
                    VelocityChange(3, 0.0, 1.0),
                ),
            )


if __name__ == "__main__":
    unittest.main()
