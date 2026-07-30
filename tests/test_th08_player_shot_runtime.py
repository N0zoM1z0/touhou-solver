#!/usr/bin/env python3
"""Tests for the focused native player-shot emission-state capture."""

from __future__ import annotations

import struct
import unittest

from th08_player_shot_runtime import (
    PLAYER_SHOT_EMISSION_STATE_SCHEMA,
    PLAYER_SHOT_POOL_CAPTURE_SIZE,
    TH08_TIMER_CAPTURE_SIZE,
    capture_player_shot_emission_state,
)
from th08_runtime.game_state import (
    ADDR_PLAYER,
    PLAYER_SHOT_POOL_OFFSET,
    PLAYER_SHOT_SLOT_STATE_OFFSET,
    PLAYER_SHOT_SLOT_STRIDE,
    PLAYER_SHOT_TIMER_OFFSET,
)


class _Reader:
    def __init__(self, timer: bytes, pool: bytes) -> None:
        self.timer = timer
        self.pool = pool
        self.reads: list[tuple[int, int]] = []

    def read(self, address: int, size: int) -> bytes:
        self.reads.append((address, size))
        if address == ADDR_PLAYER + PLAYER_SHOT_TIMER_OFFSET:
            return self.timer
        if address == ADDR_PLAYER + PLAYER_SHOT_POOL_OFFSET:
            return self.pool
        raise AssertionError(f"unexpected read {address:#x}/{size}")


class PlayerShotRuntimeTests(unittest.TestCase):
    def test_capture_retains_timer_identity_and_all_slot_words(self) -> None:
        timer = struct.pack("<iIi", -999, 0x3F000000, 5)
        pool = bytearray(PLAYER_SHOT_POOL_CAPTURE_SIZE)
        for index, value in ((0, 1), (17, 2), (127, 0xFFFF)):
            struct.pack_into(
                "<H",
                pool,
                index * PLAYER_SHOT_SLOT_STRIDE + PLAYER_SHOT_SLOT_STATE_OFFSET,
                value,
            )
        reader = _Reader(timer, bytes(pool))
        state = capture_player_shot_emission_state(reader)

        self.assertEqual(
            reader.reads,
            [
                (
                    ADDR_PLAYER + PLAYER_SHOT_TIMER_OFFSET,
                    TH08_TIMER_CAPTURE_SIZE,
                ),
                (
                    ADDR_PLAYER + PLAYER_SHOT_POOL_OFFSET,
                    PLAYER_SHOT_POOL_CAPTURE_SIZE,
                ),
            ],
        )
        self.assertEqual(
            (
                state.timer_previous,
                state.timer_fraction_bits,
                state.timer_current,
                state.timer_integer_changed,
            ),
            (-999, 0x3F000000, 5, True),
        )
        self.assertEqual(state.occupied_slot_indices, (0, 17, 127))
        self.assertEqual(state.free_slot_count, 125)
        record = state.record()
        self.assertEqual(record["schema"], PLAYER_SHOT_EMISSION_STATE_SCHEMA)
        self.assertEqual(record["pool"]["slot_state_words"][127], 0xFFFF)


if __name__ == "__main__":
    unittest.main()
