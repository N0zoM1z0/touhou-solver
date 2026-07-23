#!/usr/bin/env python3
"""Regression tests for the recovered default player-shot path."""

import math
import unittest
from pathlib import Path

from th08_player_shot_model import (
    due_shot_records,
    player_shot_overlaps_enemy,
    remilia_bomb_sht_level,
    resolve_default_shot_damage,
    shot_damage_contribution,
    spawn_player_shot,
    step_player_shot,
)
from th08_sht import parse_sht


ROOT = Path(__file__).resolve().parents[1]
REMILIA_SHT = ROOT / "artifacts" / "decoded" / "ply02as.sht"


class PlayerShotModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sht = parse_sht(REMILIA_SHT)
        cls.normal = cls.sht.levels[6]
        cls.last_spell = cls.sht.levels[7]

    def test_remilia_bomb_level_gate(self) -> None:
        self.assertIsNone(remilia_bomb_sht_level(1, 59))
        self.assertEqual(remilia_bomb_sht_level(1, 60), 6)
        self.assertEqual(remilia_bomb_sht_level(3, 60), 7)
        with self.assertRaises(ValueError):
            remilia_bomb_sht_level(0, 60)

    def test_route2_special_level_invariants(self) -> None:
        self.assertEqual((len(self.normal.shots), len(self.last_spell.shots)), (16, 18))
        for record in (*self.normal.shots, *self.last_spell.shots):
            self.assertEqual(record.shot_type, 6)
            self.assertEqual(record.damage, 45)
            self.assertEqual((record.hitbox_width, record.hitbox_height), (32.0, 16.0))
            self.assertEqual(record.speed, 20.0)
            self.assertEqual(
                (
                    record.callback_0_index,
                    record.callback_1_index,
                    record.callback_2_index,
                    record.callback_3_index,
                ),
                (0, 0, 0, 0),
            )

    def test_cadence_zero_emissions(self) -> None:
        normal_due = due_shot_records(self.normal, 0)
        last_due = due_shot_records(self.last_spell, 0)
        self.assertEqual(len(normal_due), 2)
        self.assertEqual(len(last_due), 4)
        self.assertEqual([shot.source_index for shot in normal_due], [1, 1])
        self.assertEqual([shot.source_index for shot in last_due[:2]], [0, 0])

    def test_spawn_uses_option_or_player_and_trigonometric_velocity(self) -> None:
        option_record = self.normal.shots[0]
        option_shot = spawn_player_shot(
            option_record,
            player_position=(100.0, 200.0),
            option_positions=((1.0, 2.0), (3.0, 4.0), (5.0, 6.0), (7.0, 8.0)),
        )
        self.assertEqual((option_shot.x, option_shot.y), (1.0, 2.0))
        self.assertAlmostEqual(option_shot.velocity_x, 0.0, places=5)
        self.assertAlmostEqual(option_shot.velocity_y, -20.0, places=5)

        player_record = self.last_spell.shots[0]
        player_shot = spawn_player_shot(
            player_record,
            player_position=(100.0, 200.0),
            option_positions=(),
        )
        self.assertEqual((player_shot.x, player_shot.y), (100.0, 200.0))
        self.assertAlmostEqual(player_shot.velocity_x, -math.sqrt(200.0), places=5)
        self.assertAlmostEqual(player_shot.velocity_y, -math.sqrt(200.0), places=5)

    def test_motion_and_inclusive_aabb_boundary(self) -> None:
        shot = spawn_player_shot(
            self.normal.shots[8],
            player_position=(0.0, 0.0),
            option_positions=((0.0, 0.0),) * 4,
        )
        moved = step_player_shot(shot, time_scale=0.5)
        self.assertAlmostEqual(moved.x, 10.0)
        self.assertTrue(
            player_shot_overlaps_enemy(
                moved,
                enemy_x=27.0,
                enemy_y=0.0,
                enemy_width=2.0,
                enemy_height=2.0,
            )
        )

    def test_bomb_damage_scaling_type6_piercing_and_frame_cap(self) -> None:
        self.assertEqual(shot_damage_contribution(45, bomb_active=True), 9)
        shots = tuple(
            spawn_player_shot(
                record,
                player_position=(0.0, 0.0),
                option_positions=((0.0, 0.0),) * 4,
            )
            for record in self.last_spell.shots[:6]
        )
        updated, damage = resolve_default_shot_damage(
            shots,
            enemy_x=0.0,
            enemy_y=0.0,
            enemy_width=100.0,
            enemy_height=100.0,
            bomb_active=True,
        )
        self.assertEqual(damage, 50)
        self.assertTrue(all(shot.state == 1 and shot.active for shot in updated))


if __name__ == "__main__":
    unittest.main()
