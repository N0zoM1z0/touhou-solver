#!/usr/bin/env python3
"""Regression tests for TH08 ECL opcode 0xB2 motion lowering."""

from __future__ import annotations

import math
import unittest

from movement_model import MovementBounds
from pattern_ir import Easing, PolarVelocity, TimedDisplacement
from th08_enemy_movement_model import lower_opcode_b2, th08_easing
from th08_rng import Th08Rng


BOUNDS = MovementBounds(-128.0, 48.0, 512.0, 128.0)


def _seed_for_selector(wanted_zero: bool) -> int:
    for seed in range(0x10000):
        rng = Th08Rng(seed)
        if (rng.next_mod(4) == 0) is wanted_zero:
            return seed
    raise AssertionError("no RNG seed found")


class Th08EnemyMovementModelTests(unittest.TestCase):
    def test_native_easing_codes(self) -> None:
        self.assertIs(th08_easing(0), Easing.LINEAR)
        self.assertIs(th08_easing(3), Easing.EASE_IN_QUART)
        self.assertIs(th08_easing(6), Easing.EASE_OUT_QUART)
        self.assertIs(th08_easing(7), Easing.LINEAR)

    def test_uniform_branch_consumes_two_rng_dwords(self) -> None:
        result = lower_opcode_b2(
            enemy_x=192,
            enemy_y=88,
            player_x=100,
            movement_bounds=BOUNDS,
            duration=0,
            interpolation_mode=0,
            speed=1.2,
            rng=Th08Rng(_seed_for_selector(True)),
        )
        self.assertEqual(result.direction_source, "uniform")
        self.assertEqual(result.rng_u16_calls, 4)
        self.assertIsInstance(result.motion, PolarVelocity)
        self.assertGreaterEqual(result.angle, -math.pi)
        self.assertLessEqual(result.angle, math.pi)

    def test_player_biased_branch_uses_periodic_shortest_direction(self) -> None:
        seed = _seed_for_selector(False)
        right = lower_opcode_b2(
            enemy_x=370,
            enemy_y=88,
            player_x=10,
            movement_bounds=BOUNDS,
            duration=80,
            interpolation_mode=0,
            speed=1.2,
            rng=Th08Rng(seed),
        )
        self.assertEqual(right.horizontal_cone, "right")
        self.assertEqual(right.rng_u16_calls, 4)
        self.assertIsInstance(right.motion, TimedDisplacement)
        self.assertEqual(right.motion.duration, 80)
        self.assertIs(right.motion.easing, Easing.LINEAR)
        self.assertAlmostEqual(
            math.hypot(right.motion.displacement.x, right.motion.displacement.y),
            96.0,
            places=4,
        )

    def test_vertical_margin_reflects_direction_into_bounds(self) -> None:
        seed = _seed_for_selector(False)
        top = lower_opcode_b2(
            enemy_x=100,
            enemy_y=60,
            player_x=200,
            movement_bounds=BOUNDS,
            duration=120,
            interpolation_mode=0,
            speed=1.0,
            rng=Th08Rng(seed),
        )
        self.assertGreaterEqual(top.angle, 0.0)

        bottom = lower_opcode_b2(
            enemy_x=100,
            enemy_y=120,
            player_x=200,
            movement_bounds=BOUNDS,
            duration=120,
            interpolation_mode=0,
            speed=1.0,
            rng=Th08Rng(seed),
        )
        self.assertLessEqual(bottom.angle, 0.0)


if __name__ == "__main__":
    unittest.main()
