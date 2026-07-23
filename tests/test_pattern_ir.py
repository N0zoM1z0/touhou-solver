#!/usr/bin/env python3
"""Regression tests for game-neutral pattern motion IR."""

from __future__ import annotations

import unittest

from pattern_ir import (
    Easing,
    FixedSpellRewardPolicy,
    HistoricalHitboxTrail,
    SetTimelineSpawnEnabled,
    TimedDisplacement,
    Vec2,
    easing_progress,
    timed_displacement_position,
)


class PatternIrTests(unittest.TestCase):
    def test_reward_and_collision_trail_validate_neutral_state(self) -> None:
        reward = FixedSpellRewardPolicy(99_999_990, 700)
        self.assertEqual(reward.capture_result_units, 700)

        trail = HistoricalHitboxTrail(15, 13, 6, True)
        self.assertEqual(trail.collision_stride, 6)
        with self.assertRaises(ValueError):
            HistoricalHitboxTrail(15, 1, 6)

    def test_easing_family(self) -> None:
        self.assertEqual(easing_progress(Easing.LINEAR, 0.5), 0.5)
        self.assertEqual(easing_progress(Easing.EASE_IN_QUAD, 0.5), 0.25)
        self.assertEqual(easing_progress(Easing.EASE_IN_CUBIC, 0.5), 0.125)
        self.assertEqual(easing_progress(Easing.EASE_IN_QUART, 0.5), 0.0625)
        self.assertEqual(easing_progress(Easing.EASE_OUT_QUAD, 0.5), 0.75)
        self.assertEqual(easing_progress(Easing.EASE_OUT_CUBIC, 0.5), 0.875)
        self.assertEqual(easing_progress(Easing.EASE_OUT_QUART, 0.5), 0.9375)

    def test_motion_endpoints_and_clamping(self) -> None:
        motion = TimedDisplacement(Vec2(10, 20), Vec2(100, -40), 80)
        self.assertEqual(timed_displacement_position(motion, elapsed=-1), Vec2(10, 20))
        self.assertEqual(timed_displacement_position(motion, elapsed=40), Vec2(60, 0))
        self.assertEqual(timed_displacement_position(motion, elapsed=100), Vec2(110, -20))

    def test_timeline_spawn_gate_is_an_event_not_a_pause(self) -> None:
        self.assertTrue(SetTimelineSpawnEnabled(enabled=True).enabled)
        self.assertFalse(SetTimelineSpawnEnabled(enabled=False).enabled)


if __name__ == "__main__":
    unittest.main()
