#!/usr/bin/env python3
"""Tests for the live agent's target-independent short-horizon geometry."""

from __future__ import annotations

import math
import struct
import unittest

from corridor_planner import (
    CorridorBounds,
    CorridorConfig,
    RobustControlSpec,
    plan_corridor,
)
from th08_live_dodge_agent import (
    AutoConfirmPulse,
    Bullet,
    CorridorCommitment,
    CORRIDOR_INITIAL_SUBMIT_FRAME,
    CorridorSolution,
    ENEMY_BODY_READ_OFFSET,
    ENEMY_BODY_READ_SIZE,
    ENEMY_CONTACT_SIZE_OFFSET,
    ENEMY_FLAGS_OFFSET,
    ENEMY_POSITION_OFFSET,
    ENEMY_VELOCITY_OFFSET,
    EnemyBody,
    GameplaySceneGuard,
    Item,
    LASER_ACTIVE_OFFSET,
    LASER_ANGLE_OFFSET,
    LASER_COLLISION_DISABLE_FRAME_OFFSET,
    LASER_COLLISION_ENABLE_FRAME_OFFSET,
    LASER_CURRENT_WIDTH_OFFSET,
    LASER_FADE_FRAMES_OFFSET,
    LASER_FLAGS_OFFSET,
    LASER_HEAD_OFFSET,
    LASER_MAXIMUM_LENGTH_OFFSET,
    LASER_ORIGIN_OFFSET,
    LASER_PHASE_OFFSET,
    LASER_POOL_SIZE,
    LASER_SPEED_OFFSET,
    LASER_STRIDE,
    LASER_TAIL_OFFSET,
    LASER_TIMER_OFFSET,
    LASER_WARMUP_FRAMES_OFFSET,
    LASER_ACTIVE_FRAMES_OFFSET,
    LASER_WIDTH_OFFSET,
    LEFT,
    Laser,
    RIGHT,
    UP,
    _auto_confirm_eligible,
    _action_name_from_mask,
    _corridor_policy_status,
    _corridor_submit_due,
    _corridor_target,
    _corridor_viability_query,
    _estimate_live_action_hold,
    _frozen_auto_confirm_eligible,
    _stage_corridor_solution,
    build_laser_collision_frames,
    choose_action,
    decode_enemy_body,
    decode_lasers,
    decode_player_lethal_aabb,
)
from touhou_control.viability import ControlAction


class LiveDodgeAgentTests(unittest.TestCase):
    def test_action_name_preserves_focus_speed_and_native_direction_priority(
        self,
    ) -> None:
        self.assertEqual(_action_name_from_mask(0), "stay")
        self.assertEqual(_action_name_from_mask(LEFT), "left_fast")
        self.assertEqual(_action_name_from_mask(LEFT | 0x04), "left")
        self.assertEqual(
            _action_name_from_mask(UP | LEFT | RIGHT | 0x04),
            "up_left",
        )

    def test_live_action_hold_tracks_recent_controller_cadence(self) -> None:
        self.assertEqual(_estimate_live_action_hold(()), 3)
        self.assertEqual(
            _estimate_live_action_hold((2, 2, 3, 3, 4, 4, 1803)),
            4,
        )
        self.assertEqual(_estimate_live_action_hold((9, 10, 11)), 6)

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

    def test_auto_confirm_uses_wall_clock_when_game_frame_is_frozen(self) -> None:
        pulse = AutoConfirmPulse(interval_frames=15, idle_frames=20)
        self.assertFalse(
            pulse.frozen_pulse_due(
                now=10.2,
                last_progress=10.0,
                last_pulse=0.0,
                eligible=True,
            )
        )
        self.assertTrue(
            pulse.frozen_pulse_due(
                now=10.34,
                last_progress=10.0,
                last_pulse=0.0,
                eligible=True,
            )
        )
        self.assertFalse(
            pulse.frozen_pulse_due(
                now=10.34,
                last_progress=10.0,
                last_pulse=10.2,
                eligible=True,
            )
        )
        pulse.released = True
        pulse.mark_full_pulse(frame=400)
        self.assertFalse(pulse.released)
        self.assertEqual(pulse.next_release_frame, 415)

    def test_auto_confirm_hazard_policy_does_not_gate_on_residual_items(
        self,
    ) -> None:
        self.assertTrue(
            _auto_confirm_eligible(
                player_phase=0,
                bomb_active=False,
                active_bullets=0,
                active_lasers=0,
            )
        )
        self.assertFalse(
            _auto_confirm_eligible(
                player_phase=0,
                bomb_active=False,
                active_bullets=1,
                active_lasers=0,
            )
        )
        self.assertFalse(
            _auto_confirm_eligible(
                player_phase=3,
                bomb_active=True,
                active_bullets=0,
                active_lasers=0,
            )
        )

    def test_frozen_auto_confirm_only_excludes_an_active_bomb(self) -> None:
        # Projectile and item state are deliberately absent: once the manager
        # counter is frozen, neither can evolve into a collision.
        self.assertTrue(_frozen_auto_confirm_eligible(bomb_active=False))
        self.assertFalse(_frozen_auto_confirm_eligible(bomb_active=True))

    def test_scene_guard_waits_for_nonfinal_stage_transition(self) -> None:
        guard = GameplaySceneGuard({0: 1, 1: 2}, 90.0, 5.0)
        active = guard.observe(
            gameplay_active=True,
            current_stage=0,
            now=10.0,
        )
        self.assertEqual(active.status, "active")
        entered = guard.observe(
            gameplay_active=False,
            current_stage=0,
            now=11.0,
        )
        self.assertEqual(entered.status, "stage_transition")
        self.assertTrue(entered.entered)
        waiting = guard.observe(
            gameplay_active=False,
            current_stage=1,
            now=16.0,
        )
        self.assertEqual(waiting.status, "stage_transition")
        self.assertEqual(waiting.transition_from_stage, 0)
        self.assertEqual(waiting.expected_stage, 1)
        resumed = guard.observe(
            gameplay_active=True,
            current_stage=1,
            now=17.0,
        )
        self.assertEqual(resumed.status, "resumed")
        self.assertEqual(resumed.inactive_seconds, 6.0)

    def test_scene_guard_does_not_reclassify_stage5_transition_as_final(self) -> None:
        guard = GameplaySceneGuard({5: 7}, 90.0, 5.0)
        guard.observe(gameplay_active=True, current_stage=5, now=1.0)
        early_index_write = guard.observe(
            gameplay_active=True,
            current_stage=7,
            now=1.5,
        )
        self.assertEqual(early_index_write.status, "active")
        self.assertEqual(guard.last_active_stage, 5)
        guard.observe(gameplay_active=False, current_stage=5, now=2.0)
        waiting = guard.observe(
            gameplay_active=False,
            current_stage=7,
            now=10.0,
        )
        self.assertEqual(waiting.status, "stage_transition")
        self.assertEqual(waiting.transition_from_stage, 5)
        self.assertEqual(waiting.expected_stage, 7)

    def test_scene_guard_requires_stable_final_unload(self) -> None:
        guard = GameplaySceneGuard({5: 7}, 90.0, 5.0)
        guard.observe(gameplay_active=True, current_stage=7, now=20.0)
        entered = guard.observe(
            gameplay_active=False,
            current_stage=7,
            now=21.0,
        )
        self.assertEqual(entered.status, "terminal_unload")
        self.assertTrue(entered.entered)
        waiting = guard.observe(
            gameplay_active=False,
            current_stage=7,
            now=25.9,
        )
        self.assertEqual(waiting.status, "terminal_unload")
        finished = guard.observe(
            gameplay_active=False,
            current_stage=7,
            now=26.0,
        )
        self.assertEqual(finished.status, "route_complete")

    def test_scene_guard_reports_transition_timeout(self) -> None:
        guard = GameplaySceneGuard({0: 1}, 10.0, 5.0)
        guard.observe(gameplay_active=True, current_stage=0, now=1.0)
        guard.observe(gameplay_active=False, current_stage=0, now=2.0)
        timed_out = guard.observe(
            gameplay_active=False,
            current_stage=0,
            now=12.0,
        )
        self.assertEqual(timed_out.status, "stage_transition_timeout")

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

    def test_native_enemy_body_window_decodes_scaled_lethal_extents(
        self,
    ) -> None:
        blob = bytearray(ENEMY_BODY_READ_SIZE)
        struct.pack_into(
            "<ff",
            blob,
            ENEMY_VELOCITY_OFFSET - ENEMY_BODY_READ_OFFSET,
            1.5,
            -0.5,
        )
        struct.pack_into(
            "<ff",
            blob,
            ENEMY_CONTACT_SIZE_OFFSET - ENEMY_BODY_READ_OFFSET,
            32.0,
            24.0,
        )
        struct.pack_into(
            "<ff",
            blob,
            ENEMY_POSITION_OFFSET - ENEMY_BODY_READ_OFFSET,
            178.0,
            120.0,
        )
        struct.pack_into(
            "<I",
            blob,
            ENEMY_FLAGS_OFFSET - ENEMY_BODY_READ_OFFSET,
            0x05,
        )
        body = decode_enemy_body(bytes(blob), pointer=0x5826C0)
        self.assertIsNotNone(body)
        assert body is not None
        self.assertEqual((body.half_width, body.half_height), (24.0, 18.0))
        self.assertEqual((body.vx, body.vy), (1.5, -0.5))
        struct.pack_into(
            "<I",
            blob,
            ENEMY_FLAGS_OFFSET - ENEMY_BODY_READ_OFFSET,
            0x01,
        )
        self.assertIsNone(
            decode_enemy_body(bytes(blob), pointer=0x5826C0)
        )

    def test_enemy_body_is_a_local_planner_hazard(self) -> None:
        decision = choose_action(
            player_x=192.0,
            player_y=400.0,
            bullets=(),
            lasers=(),
            enemy_bodies=(
                EnemyBody(
                    0x5826C0,
                    192.0,
                    365.0,
                    0.0,
                    0.0,
                    16.0,
                    16.0,
                    5,
                ),
            ),
            previous_direction=0,
            can_bomb=False,
        )
        self.assertIn("down", decision.action)
        self.assertFalse(decision.bomb)

    def test_native_player_lethal_aabb_decoder_uses_exact_offsets(self) -> None:
        blob = bytearray(0x14)
        struct.pack_into("<ff", blob, 0, 190.5, 398.5)
        struct.pack_into("<ff", blob, 0x0C, 193.5, 401.5)
        self.assertEqual(
            decode_player_lethal_aabb(bytes(blob)),
            (190.5, 398.5, 193.5, 401.5),
        )

    def test_native_laser_decoder_retains_lifecycle_and_quarter_width(self) -> None:
        blob = bytearray(LASER_POOL_SIZE * LASER_STRIDE)
        struct.pack_into("<I", blob, LASER_ACTIVE_OFFSET, 1)
        struct.pack_into("<ff", blob, LASER_ORIGIN_OFFSET, 100.0, 200.0)
        struct.pack_into("<f", blob, LASER_ANGLE_OFFSET, 0.25)
        struct.pack_into("<f", blob, LASER_TAIL_OFFSET, 4.0)
        struct.pack_into("<f", blob, LASER_HEAD_OFFSET, 84.0)
        struct.pack_into("<f", blob, LASER_MAXIMUM_LENGTH_OFFSET, 120.0)
        struct.pack_into("<f", blob, LASER_WIDTH_OFFSET, 16.0)
        struct.pack_into("<f", blob, LASER_CURRENT_WIDTH_OFFSET, 8.0)
        struct.pack_into("<f", blob, LASER_SPEED_OFFSET, 3.0)
        struct.pack_into("<iiiii", blob, LASER_WARMUP_FRAMES_OFFSET, 10, 5, 20, 10, 5)
        struct.pack_into("<i", blob, LASER_TIMER_OFFSET, 4)
        struct.pack_into("<H", blob, LASER_FLAGS_OFFSET, 0)
        blob[LASER_PHASE_OFFSET] = 0
        lasers = decode_lasers(bytes(blob))
        self.assertEqual(len(lasers), 1)
        laser = lasers[0]
        self.assertEqual(laser.half_width, 4.0)
        self.assertEqual(laser.slot, 0)
        self.assertIsNotNone(laser.state)
        assert laser.state is not None
        self.assertEqual(laser.state.current_width, 8.0)
        self.assertEqual(laser.state.collision_enable_frame, 5)
        frames = build_laser_collision_frames(lasers, horizon=2)
        self.assertEqual(frames[0], ())
        self.assertEqual(len(frames[1]), 1)
        self.assertLess(frames[1][0].head - frames[1][0].tail, 10.0)

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

    def test_multi_delay_certificate_covers_until_next_command_effect(self) -> None:
        decision = choose_action(
            player_x=192.0,
            player_y=400.0,
            bullets=(Bullet(192.0, 370.0, 0.0, 3.0, 3.0, 3.0),),
            lasers=(),
            previous_direction=0,
            previous_focus=True,
            can_bomb=False,
            control_delay_frames=3,
            control_delay_candidates=(2, 3, 4),
            action_hold_frames=3,
        )
        self.assertEqual(decision.robust_delay_frames, (2, 3, 4))
        self.assertEqual(decision.robust_collisions, 0)
        self.assertGreater(decision.robust_min_clearance, 0.0)
        self.assertIn(decision.robust_worst_delay, (2, 3, 4))

    def test_multi_delay_candidates_require_the_nominal_delay(self) -> None:
        with self.assertRaisesRegex(ValueError, "nominal control delay"):
            choose_action(
                player_x=192.0,
                player_y=400.0,
                bullets=(),
                lasers=(),
                previous_direction=0,
                can_bomb=False,
                control_delay_frames=2,
                control_delay_candidates=(3, 4),
            )

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

    def test_gate_reachability_outranks_a_wider_local_dead_end(self) -> None:
        decision = choose_action(
            player_x=192.0,
            player_y=400.0,
            bullets=(
                Bullet(176.0, 394.0, 0.0, 0.0, 4.0, 4.0),
            ),
            lasers=(),
            previous_direction=0,
            previous_focus=True,
            can_bomb=False,
            target_x=160.0,
            target_y=400.0,
            target_deadline=5,
        )
        self.assertEqual(decision.action, "down_left_fast")
        self.assertGreater(decision.min_clearance, 0.0)

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

    def test_corridor_commitment_survives_replans_without_rolling_expiry(
        self,
    ) -> None:
        plan = plan_corridor(
            start_x=48.0,
            start_y=88.0,
            bounds=CorridorBounds(0.0, 96.0, 0.0, 96.0),
            required_gate_lane="left",
            config=CorridorConfig(
                grid_step=8.0,
                frames_per_layer=4,
                horizon_frames=32,
            ),
        )
        commitment = CorridorCommitment()
        self.assertTrue(commitment.set_context((0, 0, None)))
        commitment.accept(
            CorridorSolution(100, plan, 12.0, context_key=(0, 0, None)),
            current_frame=104,
        )
        original_expiry = commitment.expires_frame
        self.assertEqual(commitment.active_lane(104), "left")

        commitment.accept(
            CorridorSolution(
                120,
                plan,
                12.0,
                required_gate_lane="left",
                constraint_honored=True,
                context_key=(0, 0, None),
            ),
            current_frame=124,
        )
        self.assertEqual(commitment.expires_frame, original_expiry)
        self.assertIsNone(commitment.active_lane(original_expiry))

    def test_corridor_commitment_resets_at_spell_context_boundary(self) -> None:
        commitment = CorridorCommitment("right", 200, (0, 0, None))
        self.assertFalse(commitment.set_context((0, 0, None)))
        self.assertTrue(commitment.set_context((0, 0, 145)))
        self.assertIsNone(commitment.active_lane(150))

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

    def test_viability_policy_hard_constrains_first_action(self) -> None:
        decision = choose_action(
            player_x=192.0,
            player_y=400.0,
            bullets=(),
            lasers=(),
            previous_direction=0,
            previous_focus=True,
            can_bomb=False,
            target_x=300.0,
            target_y=400.0,
            target_deadline=8,
            allowed_first_actions=("left",),
            viability_repair_volumes=(("left", 5),),
        )
        self.assertEqual(decision.action, "left")
        self.assertTrue(decision.viability_constrained)
        self.assertEqual(decision.viability_safe_action_count, 1)
        self.assertEqual(decision.viability_repair_volume, 5)

    def test_viability_repair_volume_outranks_soft_waypoint_preference(
        self,
    ) -> None:
        decision = choose_action(
            player_x=192.0,
            player_y=400.0,
            bullets=(),
            lasers=(),
            previous_direction=0,
            previous_focus=True,
            can_bomb=False,
            horizon=2,
            target_x=160.0,
            target_y=400.0,
            target_deadline=2,
            allowed_first_actions=("left", "right"),
            viability_repair_volumes=(("left", 1), ("right", 9)),
        )
        self.assertEqual(decision.action, "right")
        self.assertEqual(decision.viability_repair_volume, 9)

    def test_empty_kernel_recovery_is_soft_not_a_hard_action_constraint(
        self,
    ) -> None:
        decision = choose_action(
            player_x=192.0,
            player_y=400.0,
            bullets=(),
            lasers=(),
            previous_direction=0,
            previous_focus=True,
            can_bomb=False,
            horizon=2,
            target_x=160.0,
            target_y=400.0,
            target_deadline=2,
            viability_repair_volumes=(("left", 1), ("right", 9)),
        )
        self.assertEqual(decision.action, "right")
        self.assertFalse(decision.viability_constrained)
        self.assertEqual(decision.viability_safe_action_count, 0)
        self.assertEqual(decision.viability_repair_volume, 9)

    def test_exact_local_collision_outranks_coarse_repair_volume(self) -> None:
        decision = choose_action(
            player_x=192.0,
            player_y=400.0,
            bullets=(
                Bullet(184.0, 400.0, 0.0, 0.0, 2.0, 2.0),
            ),
            lasers=(),
            previous_direction=0,
            previous_focus=True,
            can_bomb=False,
            horizon=2,
            allowed_first_actions=("left", "right"),
            viability_repair_volumes=(("left", 100), ("right", 1)),
        )
        self.assertEqual(decision.action, "right")
        self.assertEqual(decision.viability_repair_volume, 1)

    def test_async_viability_policy_is_queried_at_current_layer(self) -> None:
        actions = (
            ControlAction("stay", 0.0, 0.0),
            ControlAction("left", -4.0, 0.0),
            ControlAction("right", 4.0, 0.0),
        )
        plan = plan_corridor(
            start_x=48.0,
            start_y=88.0,
            bounds=CorridorBounds(0.0, 96.0, 0.0, 96.0),
            config=CorridorConfig(
                grid_step=8.0,
                frames_per_layer=4,
                horizon_frames=16,
                cardinal_speed=4.0,
                diagonal_axis_speed=2.8284270763397217,
            ),
            robust_control=RobustControlSpec(
                actions=actions,
                delay_frames=(1, 2),
                nominal_delay=1,
                active_action="stay",
            ),
        )
        solution = CorridorSolution(100, plan, 12.0)
        query = _corridor_viability_query(
            solution,
            current_frame=105,
            player_x=48.0,
            player_y=88.0,
            active_action="stay",
            max_age_frames=12,
        )
        self.assertIsNotNone(query)
        assert query is not None
        self.assertEqual(query.layer, 1)
        self.assertTrue(query.available)
        self.assertGreater(query.safe_action_count, 0)

    def test_future_policy_epoch_is_pending_then_queryable_then_expired(
        self,
    ) -> None:
        actions = (ControlAction("stay", 0.0, 0.0),)
        plan = plan_corridor(
            start_x=48.0,
            start_y=88.0,
            bounds=CorridorBounds(0.0, 96.0, 0.0, 96.0),
            config=CorridorConfig(
                grid_step=8.0,
                frames_per_layer=4,
                horizon_frames=16,
            ),
            robust_control=RobustControlSpec(
                actions=actions,
                delay_frames=(1,),
                nominal_delay=1,
                active_action="stay",
            ),
        )
        solution = CorridorSolution(
            120,
            plan,
            800.0,
            snapshot_frame=72,
            forecast_lead_frames=48,
            context_key=(0, 3, 57),
        )
        self.assertEqual(
            _corridor_policy_status(
                solution,
                current_frame=119,
                max_age_frames=15,
            ),
            "pending_future_epoch",
        )
        self.assertEqual(
            _corridor_policy_status(
                solution,
                current_frame=120,
                max_age_frames=15,
            ),
            "queryable",
        )
        self.assertEqual(
            _corridor_policy_status(
                solution,
                current_frame=136,
                max_age_frames=15,
            ),
            "expired",
        )

    def test_future_policy_does_not_replace_active_policy_before_epoch(
        self,
    ) -> None:
        plan = plan_corridor(
            start_x=48.0,
            start_y=88.0,
            bounds=CorridorBounds(0.0, 96.0, 0.0, 96.0),
            config=CorridorConfig(
                grid_step=8.0,
                frames_per_layer=4,
                horizon_frames=16,
            ),
        )
        active = CorridorSolution(100, plan, 10.0, context_key=(0, 3, 57))
        future = CorridorSolution(120, plan, 8.0, context_key=(0, 3, 57))
        staged_active, pending = _stage_corridor_solution(
            active,
            future,
            current_frame=119,
            context_key=(0, 3, 57),
        )
        self.assertIs(staged_active, active)
        self.assertIs(pending, future)
        staged_active, pending = _stage_corridor_solution(
            staged_active,
            pending,
            current_frame=120,
            context_key=(0, 3, 57),
        )
        self.assertIs(staged_active, future)
        self.assertIsNone(pending)

    def test_ce_0045_finalb_restart_discards_previous_gameplay_epoch_policy(
        self,
    ) -> None:
        self.assertFalse(
            _corridor_submit_due(
                current_frame=0,
                last_submit_frame=70_745,
                interval_frames=24,
            )
        )
        self.assertTrue(
            _corridor_submit_due(
                current_frame=0,
                last_submit_frame=CORRIDOR_INITIAL_SUBMIT_FRAME,
                interval_frames=24,
            )
        )
        plan = plan_corridor(
            start_x=48.0,
            start_y=88.0,
            bounds=CorridorBounds(0.0, 96.0, 0.0, 96.0),
            config=CorridorConfig(
                grid_step=8.0,
                frames_per_layer=4,
                horizon_frames=16,
            ),
        )
        old_future = CorridorSolution(
            70800,
            plan,
            4000.0,
            context_key=(0, 7, None),
        )
        active, pending = _stage_corridor_solution(
            None,
            old_future,
            current_frame=0,
            context_key=(1, 7, None),
        )
        self.assertIsNone(active)
        self.assertIsNone(pending)

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
