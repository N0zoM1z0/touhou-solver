#!/usr/bin/env python3
"""Regression tests for game-independent movement geometry."""

from __future__ import annotations

import unittest

from movement_model import (
    Direction,
    MovementBounds,
    MovementProfile,
    step_axis_aligned_movement,
)


class MovementModelTests(unittest.TestCase):
    def test_profile_scales_and_clamps_each_axis(self) -> None:
        result = step_axis_aligned_movement(
            x=9.0,
            y=1.0,
            direction=Direction.UP_RIGHT,
            focused=False,
            profile=MovementProfile(4.0, 2.0, 3.0, 1.5),
            bounds=MovementBounds(0.0, 0.0, 10.0, 10.0),
            axis_scale_x=0.5,
            axis_scale_y=2.0,
            time_scale=0.5,
        )
        self.assertEqual((result.velocity_x, result.velocity_y), (0.75, -3.0))
        self.assertEqual((result.x, result.y), (9.75, 0.0))
        self.assertFalse(result.clamped_x)
        self.assertTrue(result.clamped_y)

    def test_neutral_has_zero_velocity(self) -> None:
        result = step_axis_aligned_movement(
            x=5.0,
            y=6.0,
            direction=Direction.NEUTRAL,
            focused=True,
            profile=MovementProfile(4.0, 2.0, 3.0, 1.5),
            bounds=MovementBounds(0.0, 0.0, 10.0, 10.0),
        )
        self.assertEqual((result.x, result.y), (5.0, 6.0))
        self.assertEqual((result.velocity_x, result.velocity_y), (0.0, 0.0))


if __name__ == "__main__":
    unittest.main()
