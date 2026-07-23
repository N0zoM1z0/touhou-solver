#!/usr/bin/env python3
"""Regression tests for the observed TH08 solver update order."""

from __future__ import annotations

import unittest

from th08_update_order import (
    LIVE,
    PLAYBACK_EXTENDED,
    RECORD,
    SAME_FRAME_IMPLICATIONS,
    TH08_FRAME_SCHEDULE,
    ordered_update_phases,
)


class Th08UpdateOrderTests(unittest.TestCase):
    def test_registered_priorities_are_ascending(self) -> None:
        priorities = [phase.priority for phase in ordered_update_phases(LIVE)]
        self.assertEqual(priorities, sorted(priorities))

    def test_playback_input_precedes_player_and_projectile_collisions(self) -> None:
        order = TH08_FRAME_SCHEDULE
        self.assertTrue(
            order.happens_before(
                PLAYBACK_EXTENDED, "replay_publish_input", "player_input_movement"
            )
        )
        self.assertTrue(
            order.happens_before(
                PLAYBACK_EXTENDED,
                "player_input_movement",
                "hostile_bullet_transform_motion_collision_graze",
            )
        )

    def test_enemy_emission_precedes_bullet_scan(self) -> None:
        self.assertTrue(
            TH08_FRAME_SCHEDULE.happens_before(
                LIVE,
                "enemy_vm_motion_and_player_shot_damage",
                "hostile_bullet_transform_motion_collision_graze",
            )
        )

    def test_deathbomb_transition_precedes_hostile_collision_pass(self) -> None:
        self.assertTrue(
            TH08_FRAME_SCHEDULE.happens_before(
                PLAYBACK_EXTENDED,
                "player_deathbomb_or_death_transition",
                "hostile_bullet_transform_motion_collision_graze",
            )
        )

    def test_item_pass_precedes_bullets_and_lasers(self) -> None:
        self.assertTrue(
            TH08_FRAME_SCHEDULE.happens_before(
                LIVE,
                "item_manager_update",
                "hostile_bullet_transform_motion_collision_graze",
            )
        )
        self.assertTrue(
            TH08_FRAME_SCHEDULE.happens_before(
                LIVE, "item_manager_update", "laser_motion_collision_graze"
            )
        )

    def test_recording_captures_input_after_gameplay_physics(self) -> None:
        self.assertTrue(
            TH08_FRAME_SCHEDULE.happens_before(
                RECORD,
                "hostile_bullet_transform_motion_collision_graze",
                "replay_capture_input",
            )
        )

    def test_static_implications_are_explicitly_not_runtime_observations(self) -> None:
        self.assertTrue(SAME_FRAME_IMPLICATIONS)
        self.assertTrue(
            all(
                implication.confidence == "inferred_from_static_order"
                for implication in SAME_FRAME_IMPLICATIONS
            )
        )


if __name__ == "__main__":
    unittest.main()
