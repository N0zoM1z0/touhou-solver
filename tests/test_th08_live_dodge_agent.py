#!/usr/bin/env python3
"""Tests for the live agent's target-independent short-horizon geometry."""

from __future__ import annotations

import math
import struct
import unittest
from unittest.mock import patch

import numpy as np

from corridor_planner import (
    CorridorBounds,
    CorridorConfig,
    RobustControlSpec,
    plan_corridor,
)
from th08_live_dodge_agent import (
    ASYNC_POLICY_DELAY_PADDING,
    AutoConfirmPulse,
    Bullet,
    CorridorCommitment,
    CORRIDOR_INITIAL_SUBMIT_FRAME,
    CORRIDOR_REPLAN_FRAMES,
    CORRIDOR_POLICY_MINIMUM_LEAD_FRAMES,
    CorridorSolution,
    DOWN,
    ENEMY_BODY_READ_OFFSET,
    ENEMY_BODY_READ_SIZE,
    ENEMY_CONTACT_SIZE_OFFSET,
    ENEMY_FLAGS_OFFSET,
    ENEMY_POOL_BASE,
    ENEMY_POOL_SIZE,
    ENEMY_POSITION_OFFSET,
    ENEMY_STRIDE,
    ENEMY_VELOCITY_OFFSET,
    EnemyBody,
    EnemyPoolSnapshot,
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
    _enemy_sensor_submit_due,
    _frozen_auto_confirm_eligible,
    _hazards_for_positions,
    _stage_corridor_solution,
    build_laser_collision_frames,
    choose_action,
    decode_enemy_body,
    decode_enemy_bodies,
    decode_lasers,
    decode_player_lethal_aabb,
    project_enemy_pool_snapshot,
    read_enemy_bodies_sparse,
    serialize_laser_trace,
)
from touhou_control.viability import ControlAction


class LiveDodgeAgentTests(unittest.TestCase):
    def test_async_policy_minimum_covers_two_layers_and_control_latency(
        self,
    ) -> None:
        self.assertEqual(CORRIDOR_POLICY_MINIMUM_LEAD_FRAMES, 16)
        self.assertEqual(CORRIDOR_REPLAN_FRAMES, 8)
        self.assertEqual(ASYNC_POLICY_DELAY_PADDING, 5)

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

    def test_enemy_sensor_throttles_completed_background_scans(self) -> None:
        self.assertFalse(
            _enemy_sensor_submit_due(
                current_frame=103,
                last_submit_frame=100,
                pending=False,
            )
        )
        self.assertTrue(
            _enemy_sensor_submit_due(
                current_frame=104,
                last_submit_frame=100,
                pending=False,
            )
        )
        self.assertFalse(
            _enemy_sensor_submit_due(
                current_frame=140,
                last_submit_frame=100,
                pending=True,
            )
        )

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

    def test_full_enemy_pool_retains_nonspell_contact_slots(self) -> None:
        blob = bytearray(ENEMY_POOL_SIZE * ENEMY_STRIDE)
        slot = 17
        base = slot * ENEMY_STRIDE
        struct.pack_into(
            "<ff",
            blob,
            base + ENEMY_VELOCITY_OFFSET,
            -1.0,
            2.0,
        )
        struct.pack_into(
            "<ff",
            blob,
            base + ENEMY_CONTACT_SIZE_OFFSET,
            20.0,
            12.0,
        )
        struct.pack_into(
            "<ff",
            blob,
            base + ENEMY_POSITION_OFFSET,
            144.0,
            96.0,
        )
        struct.pack_into(
            "<I",
            blob,
            base + ENEMY_FLAGS_OFFSET,
            0x05,
        )
        bodies = decode_enemy_bodies(bytes(blob))
        self.assertEqual(len(bodies), 1)
        self.assertEqual(
            bodies[0].pointer,
            ENEMY_POOL_BASE + slot * ENEMY_STRIDE,
        )
        self.assertEqual(
            (bodies[0].half_width, bodies[0].half_height),
            (15.0, 9.0),
        )

    def test_sparse_enemy_reader_fetches_only_contact_enabled_windows(
        self,
    ) -> None:
        active_slot = 17
        active_pointer = ENEMY_POOL_BASE + active_slot * ENEMY_STRIDE
        body_blob = bytearray(ENEMY_BODY_READ_SIZE)
        struct.pack_into(
            "<ff",
            body_blob,
            ENEMY_VELOCITY_OFFSET - ENEMY_BODY_READ_OFFSET,
            -1.0,
            2.0,
        )
        struct.pack_into(
            "<ff",
            body_blob,
            ENEMY_CONTACT_SIZE_OFFSET - ENEMY_BODY_READ_OFFSET,
            20.0,
            12.0,
        )
        struct.pack_into(
            "<ff",
            body_blob,
            ENEMY_POSITION_OFFSET - ENEMY_BODY_READ_OFFSET,
            144.0,
            96.0,
        )
        struct.pack_into(
            "<I",
            body_blob,
            ENEMY_FLAGS_OFFSET - ENEMY_BODY_READ_OFFSET,
            0x05,
        )

        class Reader:
            def __init__(self) -> None:
                self.body_reads = []

            def u32(self, address: int) -> int:
                slot = (address - ENEMY_POOL_BASE - ENEMY_FLAGS_OFFSET) // (
                    ENEMY_STRIDE
                )
                return 0x05 if slot == active_slot else 0x01

            def read(self, address: int, size: int) -> bytes:
                self.body_reads.append((address, size))
                return bytes(body_blob)

        reader = Reader()
        bodies = read_enemy_bodies_sparse(reader)
        self.assertEqual([body.pointer for body in bodies], [active_pointer])
        self.assertEqual(
            reader.body_reads,
            [(active_pointer + ENEMY_BODY_READ_OFFSET, ENEMY_BODY_READ_SIZE)],
        )

    def test_async_enemy_snapshot_projects_age_with_bounded_uncertainty(
        self,
    ) -> None:
        snapshot = EnemyPoolSnapshot(
            100,
            101,
            (
                EnemyBody(
                    ENEMY_POOL_BASE,
                    20.0,
                    40.0,
                    2.0,
                    -1.0,
                    12.0,
                    8.0,
                    0x05,
                ),
            ),
            14.0,
        )
        projected = project_enemy_pool_snapshot(snapshot, frame=105)[0]
        self.assertEqual((projected.x, projected.y), (28.0, 36.0))
        self.assertEqual(projected.uncertainty, 3.0)

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
        self.assertEqual(
            serialize_laser_trace(laser)[15:],
            [10, 5, 20, 10, 5, 0.0, 0.75],
        )
        frames = build_laser_collision_frames(lasers, horizon=2)
        self.assertEqual(frames[0], ())
        self.assertEqual(len(frames[1]), 1)
        self.assertLess(frames[1][0].head - frames[1][0].tail, 10.0)

    def test_laser_broad_phase_discards_only_segments_beyond_risk_radius(
        self,
    ) -> None:
        positions_x = np.asarray([100.0], dtype=np.float32)
        positions_y = np.asarray([100.0], dtype=np.float32)
        bullet_frame = tuple(
            np.asarray([], dtype=np.float32) for _ in range(5)
        )
        near = Laser(80.0, 100.0, 0.0, 0.0, 40.0, 2.0)
        far = Laser(400.0, 400.0, 0.0, 0.0, 40.0, 2.0)
        expected = _hazards_for_positions(
            positions_x,
            positions_y,
            step=1,
            bullet_frame=bullet_frame,
            lasers=(near,),
            enemy_bodies=(),
        )
        actual = _hazards_for_positions(
            positions_x,
            positions_y,
            step=1,
            bullet_frame=bullet_frame,
            lasers=(near, far),
            enemy_bodies=(),
        )
        for left, right in zip(expected, actual):
            np.testing.assert_allclose(left, right)

    def test_local_planner_projects_one_shared_laser_timeline(self) -> None:
        laser = Laser(80.0, 100.0, 0.0, 0.0, 180.0, 2.0)
        with patch(
            "th08_live_dodge_agent.build_laser_collision_frames",
            wraps=build_laser_collision_frames,
        ) as build:
            choose_action(
                player_x=192.0,
                player_y=400.0,
                bullets=(),
                lasers=(laser,),
                previous_direction=0,
                can_bomb=False,
                control_delay_frames=2,
                control_delay_candidates=(2, 3),
                action_hold_frames=3,
                horizon=4,
                threat_horizon=8,
            )
        self.assertEqual(build.call_count, 1)
        self.assertEqual(build.call_args.kwargs["horizon"], 6)

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

    def test_empty_kernel_safety_value_is_soft_but_precedes_position(
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
            viability_safety_actions=("right",),
            viability_safety_state_value=-1.25,
        )
        self.assertEqual(decision.action, "right")
        self.assertTrue(decision.viability_safety_value_preferred)
        self.assertEqual(
            decision.viability_safety_state_value,
            -1.25,
        )

    def test_safety_value_never_overrides_local_collision_priority(
        self,
    ) -> None:
        decision = choose_action(
            player_x=192.0,
            player_y=400.0,
            bullets=(
                Bullet(196.0, 400.0, 0.0, 0.0, 4.0, 4.0),
            ),
            lasers=(),
            previous_direction=0,
            previous_focus=True,
            can_bomb=False,
            horizon=2,
            viability_safety_actions=("right",),
            viability_safety_state_value=-2.0,
        )
        self.assertNotEqual(decision.action, "right")
        self.assertFalse(decision.viability_safety_value_preferred)

    def test_ce_stage1_frame_2512_distant_recovery_survives_beam_pruning(
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
            beam_width=1,
            viability_recovery_distances=(
                ("left", 48.0),
                ("right", 16.0),
            ),
        )
        self.assertEqual(decision.action, "right")
        self.assertFalse(decision.viability_constrained)
        self.assertEqual(decision.viability_recovery_distance, 16.0)

    def test_distant_recovery_preserves_delay_scaled_boundary_control(
        self,
    ) -> None:
        common = {
            "player_x": 8.0,
            "player_y": 424.0,
            "bullets": (),
            "lasers": (),
            "previous_direction": DOWN,
            "previous_focus": True,
            "can_bomb": False,
            "control_delay_frames": 3,
            "control_delay_candidates": (3, 4, 5, 6),
            "action_hold_frames": 6,
            "horizon": 10,
            "viability_recovery_distances": (
                ("stay", 226.0),
                ("down", 164.0),
                ("up_right_fast", 315.0),
            ),
        }
        baseline = choose_action(
            **common,
            recovery_control_reserve=False,
        )
        decision = choose_action(
            **common,
            recovery_control_reserve=True,
        )
        self.assertEqual(baseline.action, "down")
        self.assertGreater(
            baseline.viability_control_reserve_deficit,
            0.0,
        )
        self.assertEqual(decision.action, "up_right_fast")
        self.assertEqual(decision.viability_recovery_distance, 315.0)
        self.assertEqual(decision.viability_control_reserve_deficit, 0.0)

    def test_exact_local_collision_outranks_distant_kernel_recovery(
        self,
    ) -> None:
        decision = choose_action(
            player_x=192.0,
            player_y=400.0,
            bullets=(
                Bullet(200.0, 400.0, 0.0, 0.0, 2.0, 2.0),
            ),
            lasers=(),
            previous_direction=0,
            previous_focus=True,
            can_bomb=False,
            horizon=2,
            viability_recovery_distances=(
                ("left", 48.0),
                ("right", 0.0),
            ),
        )
        self.assertEqual(decision.action, "left")
        self.assertEqual(decision.viability_recovery_distance, 48.0)

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

    def test_newer_terminal_collision_can_relax_stale_global_mask(
        self,
    ) -> None:
        decision = choose_action(
            player_x=192.0,
            player_y=432.0,
            bullets=(
                Bullet(160.0, 432.0, 4.0, 0.0, 2.0, 2.0),
            ),
            lasers=(),
            previous_direction=0,
            previous_focus=True,
            can_bomb=False,
            control_delay_frames=3,
            control_delay_candidates=(3, 4, 5, 6),
            action_hold_frames=5,
            horizon=10,
            threat_horizon=32,
            allowed_first_actions=("stay", "down", "left"),
            viability_repair_volumes=(
                ("stay", 10),
                ("down", 10),
                ("left", 10),
            ),
            relax_stale_viability_contradiction=True,
        )
        self.assertEqual(decision.action, "up_right_fast")
        self.assertFalse(decision.viability_constrained)
        self.assertTrue(decision.viability_constraint_relaxed)
        self.assertEqual(decision.robust_collisions, 0)
        self.assertEqual(decision.terminal_threat_collisions, 0)

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

    def test_boundary_clamps_allowed_action_without_neutral_fallback(self) -> None:
        decision = choose_action(
            player_x=351.7697448730469,
            player_y=412.4698486328125,
            bullets=(),
            lasers=(),
            previous_direction=DOWN | RIGHT,
            previous_focus=True,
            snapshot_lag=0,
            control_delay_frames=6,
            control_delay_candidates=(4, 5, 6),
            action_hold_frames=6,
            can_bomb=False,
            horizon=10,
            threat_horizon=32,
            allowed_first_actions=("down_left_fast", "down_right_fast"),
            viability_repair_volumes=(
                ("down_left_fast", 10),
                ("down_right_fast", 2),
            ),
            viability_position_error=6.901441524171802,
        )
        self.assertIn(
            decision.action,
            ("down_left_fast", "down_right_fast"),
        )
        self.assertTrue(decision.viability_constrained)

    def test_ce_stage2_frame_13517_terminal_threat_leaves_clamped_aliases(
        self,
    ) -> None:
        bullets = tuple(
            Bullet(x, y, vx, vy, width, height, slot=slot)
            for slot, x, y, vx, vy, width, height in (
                (
                    246,
                    268.00494384765625,
                    423.29119873046875,
                    0.2894723415374756,
                    1.9789408445358276,
                    2.0,
                    2.0,
                ),
                (
                    255,
                    310.0292053222656,
                    399.29315185546875,
                    0.6699826121330261,
                    1.8844417333602905,
                    2.0,
                    2.0,
                ),
                (
                    344,
                    285.4129638671875,
                    398.8815002441406,
                    0.30125316977500916,
                    1.9771815538406372,
                    2.0,
                    2.0,
                ),
                (
                    391,
                    207.90084838867188,
                    325.9405822753906,
                    1.584021806716919,
                    1.221012830734253,
                    2.0,
                    2.0,
                ),
                (
                    570,
                    332.90472412109375,
                    385.6181640625,
                    0.4250517785549164,
                    3.3733270168304443,
                    5.0,
                    5.0,
                ),
                (
                    577,
                    334.0790710449219,
                    394.9444274902344,
                    0.4500548243522644,
                    3.5717580318450928,
                    5.0,
                    5.0,
                ),
            )
        )
        common = {
            "player_x": 304.103759765625,
            "player_y": 429.64422607421875,
            "bullets": bullets,
            "lasers": (),
            "previous_direction": 0,
            "previous_focus": True,
            "snapshot_lag": 1,
            "control_delay_frames": 3,
            "control_delay_candidates": (3, 4, 5, 6),
            "action_hold_frames": 4,
            "can_bomb": False,
            "horizon": 10,
            "allowed_first_actions": (
                "stay",
                "down",
                "left_fast",
                "down_fast",
            ),
            "viability_repair_volumes": (
                ("stay", 3),
                ("down", 3),
                ("left_fast", 1),
                ("down_fast", 3),
            ),
        }
        legacy = choose_action(**common, threat_horizon=10)
        decision = choose_action(**common, threat_horizon=32)
        self.assertIn(legacy.action, ("stay", "down", "down_fast"))
        self.assertEqual(decision.action, "left_fast")
        self.assertFalse(decision.viability_constraint_relaxed)
        self.assertEqual(decision.terminal_threat_horizon, 32)
        self.assertGreater(
            decision.terminal_threat_min_clearance,
            legacy.min_clearance,
        )
        self.assertFalse(decision.bomb)

        coarse_grid_common = {
            **common,
            "player_x": 366.32177734375,
            "player_y": 424.7275390625,
            "bullets": (
                Bullet(
                    347.1014404296875,
                    409.2017517089844,
                    1.6826684474945068,
                    1.0810304880142212,
                    2.0,
                    2.0,
                    slot=827,
                ),
            ),
            "snapshot_lag": 1,
            "control_delay_frames": 4,
            "allowed_first_actions": ("stay", "down", "down_fast"),
            "viability_repair_volumes": (
                ("stay", 8),
                ("down", 3),
                ("down_fast", 3),
            ),
        }
        coarse_grid_legacy = choose_action(
            **coarse_grid_common,
            threat_horizon=10,
        )
        coarse_grid_alias = choose_action(
            **coarse_grid_common,
            threat_horizon=32,
        )
        self.assertIn(
            coarse_grid_legacy.action,
            ("stay", "down", "down_fast"),
        )
        self.assertNotIn(
            coarse_grid_alias.action,
            ("stay", "down", "down_fast"),
        )
        self.assertTrue(coarse_grid_alias.viability_constraint_relaxed)
        self.assertEqual(coarse_grid_alias.terminal_threat_horizon, 32)

        singleton_common = {
            **common,
            "player_x": 17.515056610107422,
            "player_y": 414.66705322265625,
            "bullets": (
                Bullet(
                    18.422264099121094,
                    394.4905700683594,
                    -0.27819836139678955,
                    1.2698835134506226,
                    2.0,
                    2.0,
                    slot=866,
                ),
            ),
            "snapshot_lag": 0,
            "control_delay_frames": 4,
            "allowed_first_actions": ("stay",),
            "viability_repair_volumes": (("stay", 1),),
            "viability_position_error": 6.620516436150773,
        }
        singleton_legacy = choose_action(
            **singleton_common,
            threat_horizon=10,
        )
        singleton_fixed = choose_action(
            **singleton_common,
            threat_horizon=32,
        )
        self.assertEqual(singleton_legacy.action, "stay")
        self.assertNotEqual(singleton_fixed.action, "stay")
        self.assertTrue(singleton_fixed.viability_constraint_relaxed)

        safe_singleton = choose_action(
            **{
                **common,
                "player_x": 192.37,
                "player_y": 400.0,
                "bullets": (),
                "snapshot_lag": 0,
                "control_delay_frames": 4,
                "allowed_first_actions": ("stay",),
                "viability_repair_volumes": (("stay", 3),),
                "viability_position_error": 3.63,
            },
            threat_horizon=32,
        )
        self.assertEqual(safe_singleton.action, "stay")
        self.assertFalse(safe_singleton.viability_constraint_relaxed)
        self.assertEqual(safe_singleton.terminal_threat_horizon, 32)

        interior = choose_action(
            **{**common, "player_y": 400.0},
            threat_horizon=32,
        )
        self.assertEqual(interior.terminal_threat_horizon, 10)

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
