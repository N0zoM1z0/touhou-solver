#!/usr/bin/env python3
"""Regression tests for recovered player damage/cancel region semantics."""

import math
import unittest

from th08_attack_model import (
    AttackRegion,
    apply_damage_region,
    cancel_region_contains_point,
    damage_region_overlaps_enemy,
    sakuya_knife_regions,
    step_region,
)


class AttackModelTests(unittest.TestCase):
    def test_cancel_circle_boundary_is_strict(self) -> None:
        region = AttackRegion(10, 20, radius=32)
        self.assertTrue(cancel_region_contains_point(region, point_x=41.999, point_y=20))
        self.assertFalse(cancel_region_contains_point(region, point_x=42, point_y=20))

    def test_damage_circle_boundary_is_inclusive_and_center_based(self) -> None:
        region = AttackRegion(10, 20, radius=32)
        self.assertTrue(
            damage_region_overlaps_enemy(
                region,
                enemy_x=42,
                enemy_y=20,
                enemy_width=100,
                enemy_height=100,
            )
        )
        self.assertFalse(
            damage_region_overlaps_enemy(
                region,
                enemy_x=42.001,
                enemy_y=20,
                enemy_width=100,
                enemy_height=100,
            )
        )

    def test_rotated_cancel_rectangle(self) -> None:
        region = AttackRegion(0, 0, width=20, height=4, angle=math.pi / 2)
        self.assertTrue(cancel_region_contains_point(region, point_x=0, point_y=10))
        self.assertFalse(cancel_region_contains_point(region, point_x=3, point_y=0))

    def test_damage_cap_clamps_final_hit(self) -> None:
        region = AttackRegion(
            0, 0, radius=10, frames_remaining=9, damage=7, accumulated=8, damage_cap=12
        )
        updated, damage = apply_damage_region(
            region, enemy_x=0, enemy_y=0, enemy_width=1, enemy_height=1
        )
        self.assertEqual(damage, 4)
        self.assertEqual(updated.accumulated, 15)
        self.assertEqual(updated.damage, 0)

    def test_region_update_decrements_before_expiry(self) -> None:
        region = AttackRegion(
            0,
            0,
            radius=2,
            radius_delta=0.5,
            width=3,
            width_delta=2,
            frames_remaining=1,
        )
        updated = step_region(region)
        self.assertEqual(updated.radius, 2.5)
        self.assertEqual(updated.width, 5)
        self.assertEqual(updated.frames_remaining, 0)
        self.assertFalse(updated.active)

    def test_route2_knife_profiles(self) -> None:
        normal_damage, normal_cancel = sakuya_knife_regions(1, 2, last_spell=False)
        last_damage, last_cancel = sakuya_knife_regions(1, 2, last_spell=True)
        self.assertEqual((normal_damage.damage, last_damage.damage), (20, 30))
        self.assertEqual(normal_cancel.cancel_code, 6)
        self.assertEqual(last_cancel.radius, 32)
        self.assertEqual(last_cancel.frames_remaining, 500)


if __name__ == "__main__":
    unittest.main()
