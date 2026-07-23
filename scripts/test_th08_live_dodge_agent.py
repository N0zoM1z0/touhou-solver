#!/usr/bin/env python3
"""Tests for the live agent's target-independent short-horizon geometry."""

from __future__ import annotations

import math
import unittest

from corridor_planner import CorridorBounds, CorridorConfig, plan_corridor
from th08_live_dodge_agent import (
    AutoConfirmPulse,
    Bullet,
    CorridorSolution,
    Item,
    LEFT,
    Laser,
    RIGHT,
    UP,
    _corridor_target,
    choose_action,
)


class LiveDodgeAgentTests(unittest.TestCase):
    def test_auto_confirm_creates_fresh_z_edge_after_sustained_empty_scene(
        self,
    ) -> None:
        pulse = AutoConfirmPulse(interval_frames=15, idle_frames=20)
        mask, event = pulse.apply(frame=100, eligible=True, mask=0x05)
        self.assertEqual((mask, event), (0x05, None))
        mask, event = pulse.apply(frame=119, eligible=True, mask=0x05)
        self.assertEqual((mask, event), (0x05, None))
        mask, event = pulse.apply(frame=120, eligible=True, mask=0x05)
        self.assertEqual((mask, event), (0x04, "release"))
        mask, event = pulse.apply(frame=121, eligible=True, mask=0x05)
        self.assertEqual((mask, event), (0x05, "press"))
        mask, event = pulse.apply(frame=135, eligible=True, mask=0x05)
        self.assertEqual((mask, event), (0x05, None))
        mask, event = pulse.apply(frame=136, eligible=True, mask=0x05)
        self.assertEqual((mask, event), (0x04, "release"))

    def test_auto_confirm_combat_resets_idle_window_and_restores_z(self) -> None:
        pulse = AutoConfirmPulse(interval_frames=15, idle_frames=2)
        pulse.apply(frame=10, eligible=True, mask=0x05)
        mask, event = pulse.apply(frame=12, eligible=True, mask=0x05)
        self.assertEqual((mask, event), (0x04, "release"))
        mask, event = pulse.apply(frame=13, eligible=False, mask=0x04)
        self.assertEqual((mask, event), (0x05, "press"))
        mask, event = pulse.apply(frame=14, eligible=True, mask=0x05)
        self.assertEqual((mask, event), (0x05, None))

    def test_clear_field_returns_finite_clearance(self) -> None:
        decision = choose_action(
            player_x=192.0,
            player_y=400.0,
            bullets=(),
            lasers=(),
            previous_direction=0,
            can_bomb=False,
        )
        self.assertEqual(decision.action, "stay")
        self.assertEqual(decision.min_clearance, 9999.0)
        self.assertEqual(decision.immediate_clearance, 9999.0)
        self.assertTrue(math.isfinite(decision.score))

    def test_incoming_bullet_forces_lateral_motion(self) -> None:
        decision = choose_action(
            player_x=192.0,
            player_y=400.0,
            bullets=(Bullet(192.0, 364.0, 0.0, 3.0, 3.0, 3.0),),
            lasers=(),
            previous_direction=0,
            can_bomb=False,
        )
        self.assertNotEqual(decision.action, "stay")
        self.assertFalse(decision.bomb)

    def test_unavoidable_laser_requests_available_bomb(self) -> None:
        decision = choose_action(
            player_x=192.0,
            player_y=400.0,
            bullets=(),
            lasers=(Laser(0.0, 400.0, 0.0, 0.0, 384.0, 80.0),),
            previous_direction=0,
            can_bomb=True,
        )
        self.assertTrue(decision.bomb)
        self.assertTrue(decision.mask & 0x02)

    def test_safe_large_power_item_is_collected(self) -> None:
        decision = choose_action(
            player_x=192.0,
            player_y=400.0,
            bullets=(),
            lasers=(),
            items=(Item(17, 235.0, 400.0, 0.0, 0.0, 2, 0, False),),
            power=0.0,
            bombs=2.0,
            previous_direction=0,
            can_bomb=False,
        )
        self.assertIn("right", decision.action)
        self.assertEqual(decision.predicted_collections, (17,))
        self.assertGreater(decision.item_utility, 0.0)

    def test_unsafe_bomb_item_is_rejected(self) -> None:
        decision = choose_action(
            player_x=192.0,
            player_y=400.0,
            bullets=(Bullet(220.0, 400.0, 0.0, 0.0, 12.0, 12.0),),
            lasers=(),
            items=(Item(23, 240.0, 400.0, 0.0, 0.0, 3, 0, False),),
            power=0.0,
            bombs=2.0,
            previous_direction=0,
            can_bomb=False,
        )
        self.assertIn("left", decision.action)
        self.assertEqual(decision.predicted_collections, ())

    def test_fast_mode_is_available_for_urgent_escape(self) -> None:
        decision = choose_action(
            player_x=192.0,
            player_y=400.0,
            bullets=(Bullet(192.0, 380.0, 0.0, 2.0, 8.0, 8.0),),
            lasers=(),
            previous_direction=0,
            can_bomb=False,
        )
        self.assertIn("fast", decision.action)
        self.assertFalse(decision.planned_focus)

    def test_global_gate_deadline_forces_commitment_before_local_danger(self) -> None:
        decision = choose_action(
            player_x=192.0,
            player_y=400.0,
            bullets=(),
            lasers=(),
            previous_direction=0,
            can_bomb=False,
            target_x=160.0,
            target_y=400.0,
            target_deadline=8,
        )
        self.assertIn("left", decision.action)
        self.assertNotEqual(decision.action, "stay")

    def test_async_corridor_age_advances_waypoint_and_deadline(self) -> None:
        plan = plan_corridor(
            start_x=48.0,
            start_y=88.0,
            bounds=CorridorBounds(0.0, 96.0, 0.0, 96.0),
            preferred_x=48.0,
            preferred_y=64.0,
            config=CorridorConfig(
                grid_step=8.0,
                frames_per_layer=4,
                horizon_frames=32,
            ),
        )
        solution = CorridorSolution(100, plan, 12.0)
        target = _corridor_target(
            solution,
            current_frame=106,
            lookahead_frames=9,
            max_age_frames=20,
        )
        self.assertIsNotNone(target)
        assert target is not None
        self.assertEqual(target[2], 10)
        self.assertIsNone(
            _corridor_target(
                solution,
                current_frame=121,
                lookahead_frames=9,
                max_age_frames=20,
            )
        )

    def test_ce_frame_844_leaves_bottom_left_corner_early(self) -> None:
        bullets = (
            Bullet(27.520088, 385.47934, -1.7204704, 1.6792853, 2.0, 2.0),
            Bullet(50.196167, 446.35184, -1.8843979, 2.4929240, 2.0, 2.0),
        )
        decision = choose_action(
            player_x=8.0,
            player_y=432.0,
            bullets=bullets,
            lasers=(),
            previous_direction=0,
            previous_focus=True,
            snapshot_lag=2,
            can_bomb=False,
        )
        self.assertIn("up", decision.action)
        self.assertNotEqual(decision.action, "stay")

    def test_ce_frame_1420_commits_away_before_bottom_edge_trap(self) -> None:
        bullet = Bullet(
            119.245995,
            408.33627,
            -1.3280246,
            2.8287764,
            2.0,
            2.0,
        )
        decision = choose_action(
            player_x=120.940872,
            player_y=432.0,
            bullets=(bullet,),
            lasers=(),
            previous_direction=0x40,
            previous_focus=True,
            snapshot_lag=0,
            can_bomb=False,
        )
        self.assertEqual(decision.action, "right_fast")

    def test_ce_frame_3254_pipeline_detects_slot_1136_before_hit(self) -> None:
        bullet = Bullet(
            337.4276123046875,
            382.9591369628906,
            1.226178526878357,
            1.7048418521881104,
            2.0,
            2.0,
            slot=1136,
        )
        legacy = choose_action(
            player_x=340.20098876953125,
            player_y=392.4019775390625,
            bullets=(bullet,),
            lasers=(),
            previous_direction=UP | RIGHT,
            previous_focus=True,
            control_delay_frames=1,
            can_bomb=True,
        )
        decision = choose_action(
            player_x=340.20098876953125,
            player_y=392.4019775390625,
            bullets=(bullet,),
            lasers=(),
            previous_direction=UP | RIGHT,
            previous_focus=True,
            control_delay_frames=3,
            can_bomb=True,
        )
        self.assertFalse(legacy.bomb)
        self.assertTrue(decision.bomb)
        self.assertLess(decision.pipeline_clearance, 0.0)

    def test_ce_frame_4963_does_not_reverse_into_delayed_slot_471_path(self) -> None:
        bullet = Bullet(
            226.39694213867188,
            412.6267395019531,
            0.8104109168052673,
            2.0093977451324463,
            5.0,
            5.0,
            slot=471,
        )
        legacy = choose_action(
            player_x=233.82810974121094,
            player_y=432.0,
            bullets=(bullet,),
            lasers=(),
            previous_direction=LEFT,
            previous_focus=False,
            control_delay_frames=1,
            can_bomb=False,
        )
        decision = choose_action(
            player_x=233.82810974121094,
            player_y=432.0,
            bullets=(bullet,),
            lasers=(),
            previous_direction=LEFT,
            previous_focus=False,
            control_delay_frames=3,
            can_bomb=False,
        )
        self.assertEqual(legacy.action, "right_fast")
        self.assertEqual(decision.action, "left_fast")

    def test_ce_frame_4969_slot_471_explains_native_hit(self) -> None:
        bullet = Bullet(
            231.2593994140625,
            424.6827392578125,
            0.8104109168052673,
            2.0093977451324463,
            5.0,
            5.0,
            slot=471,
        )
        decision = choose_action(
            player_x=233.82810974121094,
            player_y=432.0,
            bullets=(bullet,),
            lasers=(),
            previous_direction=RIGHT,
            previous_focus=False,
            control_delay_frames=3,
            can_bomb=True,
        )
        self.assertTrue(decision.bomb)
        self.assertLess(decision.pipeline_clearance, 0.0)


if __name__ == "__main__":
    unittest.main()
