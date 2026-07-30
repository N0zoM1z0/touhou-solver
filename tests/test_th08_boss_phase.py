#!/usr/bin/env python3
"""Focused decode tests for read-only TH08 boss phase telemetry."""

from __future__ import annotations

import struct
import unittest

from th08_boss_phase import (
    ADDR_ENEMY_MANAGER_FRAME,
    BOSS_REGISTRY_ADDRESS,
    ENEMY_ACTIVE_FLAG,
    ENEMY_BOSS_FLAG2,
    ENEMY_CONTROL_WINDOW_SIZE,
    ENEMY_CURRENT_HEALTH_OFFSET,
    ENEMY_FLAGS_OFFSET,
    ENEMY_FRAME_DAMAGE_OFFSET,
    ENEMY_HEALTH_THRESHOLDS_OFFSET,
    ENEMY_HEALTH_WINDOW_SIZE,
    ENEMY_HP_SUBTRACTION_FLAG,
    ENEMY_PHASE_TIMER_ELAPSED_OFFSET,
    ENEMY_PHASE_TIMER_FRACTION_OFFSET,
    ENEMY_PLAYER_SHOT_DAMAGE_FLAG,
    ENEMY_TIMEOUT_FRAME_OFFSET,
    capture_boss_phase_snapshot,
    project_boss_phase_transition_prefix,
)
from th08_enemy_damage_model import (
    ENEMY_PAUSE_DURING_BOMB_OR_TRANSITION_FLAG,
)


class Reader:
    def __init__(self, pointer: int) -> None:
        self.pointer = pointer
        self.health = bytearray(ENEMY_HEALTH_WINDOW_SIZE)
        self.control = bytearray(ENEMY_CONTROL_WINDOW_SIZE)
        struct.pack_into("<iii", self.health, 0, 720, 1000, 1000)
        struct.pack_into(
            "<f",
            self.health,
            ENEMY_PHASE_TIMER_FRACTION_OFFSET - ENEMY_CURRENT_HEALTH_OFFSET,
            0.5,
        )
        struct.pack_into(
            "<i",
            self.health,
            ENEMY_PHASE_TIMER_ELAPSED_OFFSET - ENEMY_CURRENT_HEALTH_OFFSET,
            125,
        )
        struct.pack_into(
            "<II",
            self.control,
            0,
            (
                ENEMY_ACTIVE_FLAG
                | ENEMY_HP_SUBTRACTION_FLAG
                | ENEMY_PLAYER_SHOT_DAMAGE_FLAG
            ),
            ENEMY_BOSS_FLAG2,
        )
        struct.pack_into(
            "<i",
            self.control,
            ENEMY_FRAME_DAMAGE_OFFSET - ENEMY_FLAGS_OFFSET,
            12,
        )
        struct.pack_into(
            "<iiii",
            self.control,
            ENEMY_HEALTH_THRESHOLDS_OFFSET - ENEMY_FLAGS_OFFSET,
            500,
            -1,
            -1,
            -1,
        )
        struct.pack_into(
            "<i",
            self.control,
            ENEMY_TIMEOUT_FRAME_OFFSET - ENEMY_FLAGS_OFFSET,
            1800,
        )

    def u32(self, address: int) -> int:
        self.assert_address(address, ADDR_ENEMY_MANAGER_FRAME)
        return 900

    @staticmethod
    def assert_address(actual: int, expected: int) -> None:
        if actual != expected:
            raise AssertionError(f"{actual:#x} != {expected:#x}")

    def read(self, address: int, size: int) -> bytes:
        if address == BOSS_REGISTRY_ADDRESS:
            return struct.pack("<IIII", self.pointer, 0, 0, 0)
        if address == self.pointer + ENEMY_CURRENT_HEALTH_OFFSET:
            return bytes(self.health)
        if address == self.pointer + ENEMY_FLAGS_OFFSET:
            return bytes(self.control)
        raise AssertionError(f"unexpected read {address:#x}, {size}")


class BossPhaseTests(unittest.TestCase):
    def test_capture_decodes_threshold_timer_and_damage_gate(self) -> None:
        snapshot = capture_boss_phase_snapshot(Reader(0x57D2F0))
        self.assertIsNotNone(snapshot)
        self.assertTrue(snapshot.stable)
        self.assertEqual(snapshot.registry_slot, 0)
        self.assertEqual(snapshot.phase_end_health, 500)
        self.assertEqual(snapshot.health_remaining, 220)
        self.assertEqual(snapshot.elapsed_frames, 125.5)
        self.assertEqual(snapshot.frame_damage, 12)
        self.assertTrue(snapshot.native_damage_gate_open)
        self.assertTrue(
            snapshot.as_progress_state(
                player_transition_state=0,
            ).damageable
        )

    def test_progress_damage_gate_includes_player_transition_state(self) -> None:
        reader = Reader(0x57D2F0)
        flags = struct.unpack_from("<I", reader.control, 0)[0]
        struct.pack_into(
            "<I",
            reader.control,
            0,
            flags | ENEMY_PAUSE_DURING_BOMB_OR_TRANSITION_FLAG,
        )
        snapshot = capture_boss_phase_snapshot(reader)
        self.assertIsNotNone(snapshot)
        self.assertTrue(
            snapshot.as_progress_state(
                player_transition_state=0,
            ).damageable
        )
        self.assertFalse(
            snapshot.as_progress_state(
                player_transition_state=3,
            ).damageable
        )

    def test_post_damage_threshold_overshoot_stays_in_current_phase(self) -> None:
        reader = Reader(0x57D2F0)
        struct.pack_into("<i", reader.health, 0, 490)
        struct.pack_into(
            "<iiii",
            reader.control,
            ENEMY_HEALTH_THRESHOLDS_OFFSET - ENEMY_FLAGS_OFFSET,
            500,
            100,
            -1,
            -1,
        )
        snapshot = capture_boss_phase_snapshot(reader)
        self.assertIsNotNone(snapshot)
        self.assertEqual(snapshot.phase_end_health, 500)
        self.assertEqual(snapshot.health_remaining, 0)
        self.assertEqual(snapshot.completion_pending, "health")
        self.assertEqual(
            snapshot.as_progress_state().completion_pending,
            "health",
        )
        projection = snapshot.transition_projection
        self.assertEqual(len(projection.steps), 1)
        self.assertEqual(projection.steps[0].health_threshold_index, 0)
        self.assertEqual(projection.current_health, 500)
        self.assertEqual(projection.phase_start_health, 500)
        self.assertEqual(projection.health_thresholds, (-1, 100, -1, -1))
        self.assertIsNone(projection.timeout_frame)

    def test_health_transition_precedes_due_timeout(self) -> None:
        projection = project_boss_phase_transition_prefix(
            current_health=490,
            phase_start_health=1000,
            health_thresholds=(500, 100, -1, -1),
            timer_elapsed=1800,
            timer_fraction=0.75,
            timeout_frame=1800,
        )
        self.assertEqual(tuple(step.kind for step in projection.steps), ("health",))
        self.assertEqual(projection.current_health, 500)
        self.assertEqual(projection.timer_elapsed, 1800)
        self.assertEqual(projection.timer_fraction, 0.75)
        self.assertIsNone(projection.timeout_frame)

    def test_timeout_uses_integer_timer_and_restores_largest_threshold(self) -> None:
        not_due = project_boss_phase_transition_prefix(
            current_health=720,
            phase_start_health=1000,
            health_thresholds=(100, 500, -1, -1),
            timer_elapsed=1799,
            timer_fraction=0.99,
            timeout_frame=1800,
        )
        self.assertFalse(not_due.steps)
        due = project_boss_phase_transition_prefix(
            current_health=720,
            phase_start_health=1000,
            health_thresholds=(100, 500, -1, -1),
            timer_elapsed=1800,
            timer_fraction=0.25,
            timeout_frame=1800,
        )
        self.assertEqual(tuple(step.kind for step in due.steps), ("timeout",))
        self.assertEqual(due.steps[0].health_threshold_index, 1)
        self.assertEqual(due.current_health, 500)
        self.assertEqual(due.phase_start_health, 500)
        self.assertEqual(due.health_thresholds, (100, -1, -1, -1))
        self.assertEqual(due.timer_elapsed, 0)
        self.assertEqual(due.timer_fraction, 0.0)
        self.assertIsNone(due.timeout_frame)

    def test_health_transition_loop_preserves_native_slot_order(self) -> None:
        reader = Reader(0x57D2F0)
        struct.pack_into("<i", reader.health, 0, 50)
        struct.pack_into(
            "<iiii",
            reader.control,
            ENEMY_HEALTH_THRESHOLDS_OFFSET - ENEMY_FLAGS_OFFSET,
            100,
            500,
            -1,
            -1,
        )
        snapshot = capture_boss_phase_snapshot(reader)
        self.assertIsNotNone(snapshot)
        self.assertEqual(snapshot.phase_end_health, 100)
        projection = project_boss_phase_transition_prefix(
            current_health=50,
            phase_start_health=1000,
            health_thresholds=(100, 500, -1, -1),
            timer_elapsed=10,
            timer_fraction=0.0,
            timeout_frame=None,
        )
        self.assertEqual(
            tuple(
                (step.health_threshold_index, step.health_threshold)
                for step in projection.steps
            ),
            ((0, 100), (1, 500)),
        )
        self.assertEqual(projection.current_health, 500)
        self.assertEqual(projection.health_thresholds, (-1, -1, -1, -1))

    def test_negative_post_damage_health_is_valid_telemetry(self) -> None:
        reader = Reader(0x57D2F0)
        struct.pack_into("<i", reader.health, 0, -5)
        snapshot = capture_boss_phase_snapshot(reader)
        self.assertIsNotNone(snapshot)
        self.assertEqual(snapshot.current_health, -5)
        self.assertEqual(snapshot.completion_pending, "health")


if __name__ == "__main__":
    unittest.main()
