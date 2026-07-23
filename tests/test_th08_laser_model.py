#!/usr/bin/env python3
"""Regression tests for the recovered TH08 laser runtime."""

import math
import unittest
from dataclasses import replace

from th08_laser_model import (
    LaserPhase,
    _cached_collision_geometry_frames,
    laser_collision_box,
    laser_collision_geometry_frames,
    laser_overlaps_player,
    spawn_laser_state,
    step_laser,
)


def _laser(**overrides):
    values = dict(
        origin_x=0.0,
        origin_y=0.0,
        angle=0.0,
        speed=0.0,
        tail_distance=0.0,
        head_distance=100.0,
        maximum_length=100.0,
        width=16.0,
        warmup_frames=10,
        active_frames=20,
        fade_frames=10,
        collision_enable_frame=5,
        collision_disable_frame=5,
    )
    values.update(overrides)
    return spawn_laser_state(**values)


class LaserModelTests(unittest.TestCase):
    def test_collision_dimensions_and_tail_reduction(self) -> None:
        full = laser_collision_box(_laser())
        shortened = laser_collision_box(
            _laser(tail_distance=20.0, head_distance=120.0)
        )
        self.assertEqual((full.center_x, full.width, full.height), (50.0, 100.0, 8.0))
        self.assertAlmostEqual(shortened.center_x, 70.0)
        self.assertAlmostEqual(shortened.width, 70.0)

    def test_inclusive_hit_and_48_unit_graze_expansion(self) -> None:
        box = laser_collision_box(_laser())
        self.assertTrue(
            laser_overlaps_player(
                box,
                player_x=50.0,
                player_y=6.0,
                player_half_width=2.0,
                player_half_height=2.0,
            )
        )
        self.assertFalse(
            laser_overlaps_player(
                box,
                player_x=50.0,
                player_y=6.001,
                player_half_width=2.0,
                player_half_height=2.0,
            )
        )
        self.assertTrue(
            laser_overlaps_player(
                box,
                player_x=50.0,
                player_y=54.0,
                player_half_width=2.0,
                player_half_height=2.0,
                graze=True,
            )
        )

    def test_rotation_is_about_origin(self) -> None:
        box = laser_collision_box(_laser(angle=math.pi / 2.0))
        self.assertTrue(
            laser_overlaps_player(
                box,
                player_x=0.0,
                player_y=50.0,
                player_half_width=2.0,
                player_half_height=2.0,
            )
        )

    def test_motion_clamps_length_and_tail(self) -> None:
        result = step_laser(
            _laser(speed=20.0, head_distance=90.0, maximum_length=100.0),
            time_scale=0.5,
        )
        self.assertEqual(result.laser.head_distance, 100.0)
        self.assertEqual(result.laser.tail_distance, 0.0)
        result = step_laser(replace(result.laser, speed=20.0), time_scale=1.0)
        self.assertEqual(result.laser.head_distance, 120.0)
        self.assertEqual(result.laser.tail_distance, 20.0)

    def test_warmup_transition_falls_through_to_active(self) -> None:
        laser = replace(_laser(), timer=10)
        result = step_laser(laser)
        self.assertEqual(
            [(check.phase, check.graze_enabled) for check in result.checks],
            [(LaserPhase.WARMUP, False), (LaserPhase.ACTIVE, True)],
        )
        self.assertEqual((result.laser.phase, result.laser.timer), (LaserPhase.ACTIVE, 1))
        self.assertEqual(
            [check.collision_box.width for check in result.checks],
            [8.0, 8.0],
        )

    def test_active_transition_falls_through_to_fade(self) -> None:
        laser = replace(_laser(warmup_frames=0), timer=20)
        result = step_laser(laser)
        self.assertEqual(
            [(check.phase, check.graze_enabled) for check in result.checks],
            [(LaserPhase.ACTIVE, True), (LaserPhase.FADE, False)],
        )
        self.assertEqual((result.laser.phase, result.laser.timer), (LaserPhase.FADE, 1))
        self.assertEqual(
            [check.collision_box.width for check in result.checks],
            [100.0, 8.0],
        )

    def test_non_alpha_warning_uses_short_ramped_longitudinal_box(self) -> None:
        before_enable = step_laser(replace(_laser(), timer=4))
        self.assertEqual(before_enable.checks, ())
        enabled = step_laser(replace(_laser(), timer=5))
        self.assertEqual(len(enabled.checks), 1)
        self.assertEqual(enabled.checks[0].phase, LaserPhase.WARMUP)
        self.assertAlmostEqual(enabled.checks[0].collision_box.width, 4.0)
        self.assertAlmostEqual(enabled.checks[0].collision_box.height, 8.0)

    def test_alpha_flag_keeps_full_length_during_warmup_and_fade(self) -> None:
        warmup = step_laser(replace(_laser(flags=1), timer=5))
        fading = step_laser(
            replace(
                _laser(flags=1, warmup_frames=0),
                phase=LaserPhase.FADE,
                timer=2,
            )
        )
        self.assertEqual(warmup.checks[0].collision_box.width, 100.0)
        self.assertEqual(fading.checks[0].collision_box.width, 100.0)

    def test_fade_collision_stops_at_disable_threshold(self) -> None:
        enabled = step_laser(
            replace(_laser(warmup_frames=0), phase=LaserPhase.FADE, timer=4)
        )
        disabled = step_laser(
            replace(_laser(warmup_frames=0), phase=LaserPhase.FADE, timer=5)
        )
        self.assertEqual(len(enabled.checks), 1)
        self.assertEqual(disabled.checks, ())

    def test_projection_template_is_shared_across_origin_and_angle(self) -> None:
        _cached_collision_geometry_frames.cache_clear()
        first = laser_collision_geometry_frames(
            _laser(origin_x=12.0, origin_y=34.0, angle=0.25),
            frame_count=8,
        )
        second = laser_collision_geometry_frames(
            _laser(origin_x=300.0, origin_y=400.0, angle=1.5),
            frame_count=8,
        )
        self.assertEqual(first, second)
        info = _cached_collision_geometry_frames.cache_info()
        self.assertEqual((info.misses, info.hits), (1, 1))


if __name__ == "__main__":
    unittest.main()
