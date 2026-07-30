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


if __name__ == "__main__":
    unittest.main()
