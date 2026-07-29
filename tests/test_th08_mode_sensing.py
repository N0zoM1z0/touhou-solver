#!/usr/bin/env python3
"""Tests for native player-mode fields in the runtime observation."""

from __future__ import annotations

import unittest

from th08_runtime.game_state import (
    ADDR_CURRENT_INPUT,
    ADDR_DIFFICULTY_INDEX,
    ADDR_ENEMY_MANAGER_FRAME,
    ADDR_ENGINE_FLAGS,
    ADDR_GAMEPLAY_RNG,
    ADDR_GAMEPLAY_TIME_SCALE,
    ADDR_PLAYER,
    ADDR_PREVIOUS_INPUT,
    ADDR_RAW_INPUT,
    ADDR_ROUTE_ID,
    ADDR_RUN_STATE_INNER_POINTER,
    ADDR_SPELL_CARD_STATE,
    ADDR_STAGE_ROUTE_INDEX,
    PLAYER_BOMB_ACTIVE_OFFSET,
    PLAYER_BOMB_INDEX_OFFSET,
    PLAYER_BOMB_LOCKOUT_OFFSET,
    PLAYER_BOMB_TIMER_OFFSET,
    PLAYER_FOCUS_LOGIC_OFFSET,
    PLAYER_FOCUS_TRANSITION_COUNTER_OFFSET,
    PLAYER_POSITION_OFFSET,
    PLAYER_PREDEATH_COUNTER_OFFSET,
    PLAYER_SECONDARY_CHARACTER_ACTIVE_OFFSET,
    RUN_STATE_BOMBS_OFFSET,
    RUN_STATE_LIVES_OFFSET,
    RUN_STATE_POWER_OFFSET,
)
from th08_runtime.sensing import observe_state


class _Reader:
    INNER = 0x20000000

    def read(self, address: int, size: int) -> bytes:
        if address != ADDR_SPELL_CARD_STATE:
            raise AssertionError(f"unexpected read at {address:#x}")
        return bytes(size)

    def u8(self, address: int) -> int:
        values = {
            ADDR_ROUTE_ID: 2,
            ADDR_PLAYER: 0,
            ADDR_PLAYER + PLAYER_FOCUS_LOGIC_OFFSET: 0,
            ADDR_PLAYER + 4: 0,
            ADDR_PLAYER + PLAYER_SECONDARY_CHARACTER_ACTIVE_OFFSET: 3,
            ADDR_PLAYER + 6: 0,
        }
        return values[address]

    def u16(self, address: int) -> int:
        values = {
            ADDR_RAW_INPUT: 0x01,
            ADDR_CURRENT_INPUT: 0x01,
            ADDR_PREVIOUS_INPUT: 0x05,
            ADDR_GAMEPLAY_RNG: 0x1234,
        }
        return values[address]

    def u32(self, address: int) -> int:
        values = {
            ADDR_ENGINE_FLAGS: 0x04,
            ADDR_RUN_STATE_INNER_POINTER: self.INNER,
            ADDR_ENEMY_MANAGER_FRAME: 10075,
            ADDR_GAMEPLAY_TIME_SCALE: 0x3F800000,
            ADDR_STAGE_ROUTE_INDEX: 5,
            ADDR_DIFFICULTY_INDEX: 4,
            ADDR_GAMEPLAY_RNG + 4: 77,
            ADDR_PLAYER + PLAYER_BOMB_ACTIVE_OFFSET: 0,
        }
        return values[address]

    def i32(self, address: int) -> int:
        values = {
            ADDR_PLAYER + PLAYER_FOCUS_TRANSITION_COUNTER_OFFSET: 7,
            ADDR_PLAYER + PLAYER_BOMB_INDEX_OFFSET: 0,
            ADDR_PLAYER + PLAYER_BOMB_TIMER_OFFSET: 0,
            ADDR_PLAYER + PLAYER_PREDEATH_COUNTER_OFFSET: 0,
            ADDR_PLAYER + PLAYER_BOMB_LOCKOUT_OFFSET: 0,
        }
        return values[address]

    def f32(self, address: int) -> float:
        values = {
            self.INNER + RUN_STATE_LIVES_OFFSET: 3.0,
            self.INNER + RUN_STATE_BOMBS_OFFSET: 2.0,
            self.INNER + RUN_STATE_POWER_OFFSET: 64.0,
            ADDR_PLAYER + PLAYER_POSITION_OFFSET: 192.0,
            ADDR_PLAYER + PLAYER_POSITION_OFFSET + 4: 300.0,
        }
        return values[address]


class ModeSensingTests(unittest.TestCase):
    def test_observation_exposes_exact_native_focus_transition_fields(
        self,
    ) -> None:
        state = observe_state(_Reader())
        player = state["player"]
        self.assertEqual(player["focus_logic"], 0)
        self.assertTrue(player["secondary_character_active"])
        self.assertEqual(player["focus_transition_counter"], 7)


if __name__ == "__main__":
    unittest.main()
