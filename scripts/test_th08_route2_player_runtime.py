#!/usr/bin/env python3
"""Regression tests for the route-2 priority-9 player runtime."""

from __future__ import annotations

import unittest

from th08_movement_model import INPUT_BOMB, INPUT_FOCUS, INPUT_RIGHT
from th08_option_model import OPTION_EXIT
from th08_player_model import BombIndex
from th08_route2_player_runtime import (
    BombStartKind,
    PlayerPhase,
    initial_route2_player_state,
    step_route2_player,
)


class Route2PlayerRuntimeTests(unittest.TestCase):
    def test_native_initializer_sentinel_releases_options_on_neutral_start(self) -> None:
        state = initial_route2_player_state()
        self.assertEqual(state.focus.focus_logic_value, 2)
        result = step_route2_player(state, input_mask=0)
        self.assertEqual(result.state.focus.focus_logic_value, 0)
        self.assertTrue(
            all(option.state == OPTION_EXIT for option in result.state.focus.options)
        )

    def test_normal_stage_start_moves_on_first_player_callback(self) -> None:
        result = step_route2_player(
            initial_route2_player_state(), input_mask=INPUT_RIGHT
        )
        self.assertTrue(result.movement_applied)
        self.assertEqual(result.state.phase, PlayerPhase.INVULNERABLE)
        self.assertEqual(result.state.state_timer_elapsed, 239)
        self.assertEqual(result.state.x, 196.0)

    def test_short_spawn_mode_first_moves_when_timer_enters_thirty(self) -> None:
        state = initial_route2_player_state(short_spawn_mode=True)
        for _ in range(20):
            result = step_route2_player(state, input_mask=INPUT_RIGHT)
            self.assertFalse(result.movement_applied)
            state = result.state
        result = step_route2_player(state, input_mask=INPUT_RIGHT)
        self.assertTrue(result.movement_applied)
        self.assertEqual(result.state.phase, PlayerPhase.INVULNERABLE)
        self.assertEqual(result.state.state_timer_elapsed, 29)
        self.assertEqual(result.state.x, 196.0)

    def test_normal_bomb_uses_prior_focus_and_halves_sakuya_movement(self) -> None:
        state = step_route2_player(
            initial_route2_player_state(), input_mask=0
        ).state
        result = step_route2_player(
            state,
            input_mask=INPUT_BOMB | INPUT_FOCUS | INPUT_RIGHT,
            bomb_start=BombStartKind.NORMAL,
        )
        self.assertEqual(result.bomb_started.index, BombIndex.SAKUYA_NORMAL)
        self.assertFalse(result.effective_focus)
        self.assertEqual(result.state.x, 194.0)
        self.assertEqual(result.state.bombs, 2)
        self.assertEqual(result.state.bomb.timer_elapsed, 1)
        self.assertEqual(result.state.phase, PlayerPhase.INVULNERABLE)
        self.assertEqual(result.state.state_timer_elapsed, 289)

    def test_remilia_normal_is_stationary_until_local_frame_sixty(self) -> None:
        state = step_route2_player(
            initial_route2_player_state(), input_mask=INPUT_FOCUS
        ).state
        start_x = state.x
        result = step_route2_player(
            state,
            input_mask=INPUT_BOMB | INPUT_RIGHT,
            bomb_start=BombStartKind.NORMAL,
        )
        self.assertEqual(result.bomb_started.index, BombIndex.REMILIA_NORMAL)
        self.assertEqual(result.state.x, start_x)
        state = result.state
        for _ in range(59):
            state = step_route2_player(state, input_mask=INPUT_RIGHT).state
        self.assertEqual(state.x, start_x)
        result = step_route2_player(state, input_mask=INPUT_RIGHT)
        self.assertEqual(result.state.x, 196.60000610351562)

    def test_deathbomb_uses_partner_and_costs_two(self) -> None:
        state = step_route2_player(
            initial_route2_player_state(bombs=3), input_mask=INPUT_FOCUS
        ).state
        result = step_route2_player(
            state,
            input_mask=INPUT_BOMB,
            bomb_start=BombStartKind.DEATHBOMB,
        )
        self.assertEqual(result.bomb_started.index, BombIndex.SAKUYA_LAST_SPELL)
        self.assertEqual(result.state.bombs, 1)
        self.assertEqual(result.state.phase, PlayerPhase.INVULNERABLE)
        self.assertEqual(result.state.state_timer_elapsed, 349)

    def test_bomb_ends_before_movement_on_duration_boundary(self) -> None:
        state = step_route2_player(
            initial_route2_player_state(), input_mask=0
        ).state
        state = step_route2_player(
            state,
            input_mask=INPUT_BOMB,
            bomb_start=BombStartKind.NORMAL,
        ).state
        for _ in range(289):
            state = step_route2_player(state, input_mask=0).state
        self.assertIsNotNone(state.bomb)
        self.assertEqual(state.bomb.timer_elapsed, 290)
        result = step_route2_player(state, input_mask=INPUT_FOCUS | INPUT_RIGHT)
        self.assertEqual(result.bomb_ended.index, BombIndex.SAKUYA_NORMAL)
        self.assertIsNone(result.state.bomb)
        self.assertTrue(result.effective_focus)
        self.assertAlmostEqual(result.state.x, 194.3000030517578)


if __name__ == "__main__":
    unittest.main()
