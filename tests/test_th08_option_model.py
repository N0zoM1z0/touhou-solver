#!/usr/bin/env python3
"""Regression tests for Sakuya/Remilia option positioning."""

from __future__ import annotations

import math
import unittest

from th08_option_model import (
    OPTION_ACTIVE,
    OPTION_ENTER,
    OPTION_EXIT,
    OPTION_INACTIVE,
    Route2FocusState,
    initial_route2_focus_state,
    route2_option_shot_positions,
    step_route2_focus,
)


class Route2OptionModelTests(unittest.TestCase):
    def test_native_initializer_uses_non_boolean_focus_sentinel(self) -> None:
        state = initial_route2_focus_state()
        self.assertEqual(state.focus_logic_value, 2)
        self.assertTrue(state.focus_logic_active)
        self.assertTrue(all(option.state == OPTION_ENTER for option in state.options))

    def test_focus_edge_captures_post_movement_player_position(self) -> None:
        result = step_route2_focus(
            Route2FocusState(),
            focused=True,
            post_movement_player_x=100.0,
            post_movement_player_y=200.0,
        )
        self.assertTrue(result.focus_logic_active)
        self.assertFalse(result.remilia_character_active)
        self.assertEqual([option.state for option in result.options], [2] * 4)
        self.assertEqual(
            route2_option_shot_positions(result),
            {1: (78.0, 184.0), 2: (82.0, 168.0), 3: (118.0, 168.0), 4: (122.0, 184.0)},
        )

    def test_rotation_starts_only_after_elapsed_timer_exceeds_twelve(self) -> None:
        state = step_route2_focus(
            Route2FocusState(),
            focused=True,
            post_movement_player_x=100.0,
            post_movement_player_y=200.0,
        )
        initial_angle = state.options[0].angle
        for _ in range(12):
            state = step_route2_focus(
                state,
                focused=True,
                post_movement_player_x=999.0,
                post_movement_player_y=999.0,
            )
        self.assertEqual(state.options[0].timer_elapsed, 13)
        self.assertEqual(state.options[0].angle, initial_angle)

        state = step_route2_focus(
            state,
            focused=True,
            post_movement_player_x=999.0,
            post_movement_player_y=999.0,
        )
        self.assertAlmostEqual(state.options[0].angle, math.radians(1.5))
        self.assertAlmostEqual(state.options[0].target_x, 70.0)
        self.assertAlmostEqual(state.options[0].target_y, 184.0)

    def test_focus_logic_switches_immediately_but_character_byte_lags(self) -> None:
        state = Route2FocusState()
        state = step_route2_focus(
            state,
            focused=True,
            post_movement_player_x=0.0,
            post_movement_player_y=0.0,
        )
        self.assertTrue(state.focus_logic_active)
        self.assertFalse(state.remilia_character_active)
        for _ in range(6):
            state = step_route2_focus(
                state,
                focused=True,
                post_movement_player_x=0.0,
                post_movement_player_y=0.0,
            )
        self.assertFalse(state.remilia_character_active)
        state = step_route2_focus(
            state,
            focused=True,
            post_movement_player_x=0.0,
            post_movement_player_y=0.0,
        )
        self.assertTrue(state.remilia_character_active)

    def test_release_freezes_then_clears_options_after_timer_sixteen(self) -> None:
        state = step_route2_focus(
            Route2FocusState(),
            focused=True,
            post_movement_player_x=100.0,
            post_movement_player_y=200.0,
        )
        positions = route2_option_shot_positions(state)
        state = step_route2_focus(
            state,
            focused=False,
            post_movement_player_x=200.0,
            post_movement_player_y=300.0,
        )
        self.assertTrue(all(option.state == OPTION_EXIT for option in state.options))
        self.assertEqual(
            [(option.x, option.y) for option in state.options],
            list(positions.values()),
        )
        for _ in range(16):
            state = step_route2_focus(
                state,
                focused=False,
                post_movement_player_x=200.0,
                post_movement_player_y=300.0,
            )
        self.assertTrue(all(option.state == OPTION_EXIT for option in state.options))
        state = step_route2_focus(
            state,
            focused=False,
            post_movement_player_x=200.0,
            post_movement_player_y=300.0,
        )
        self.assertTrue(
            all(option.state == OPTION_INACTIVE for option in state.options)
        )

    def test_fractional_timer_uses_global_time_scale(self) -> None:
        state = step_route2_focus(
            Route2FocusState(),
            focused=True,
            post_movement_player_x=0.0,
            post_movement_player_y=0.0,
            time_scale=0.5,
        )
        self.assertEqual(state.options[0].state, OPTION_ACTIVE)
        self.assertEqual(state.options[0].timer_elapsed, 0)
        self.assertAlmostEqual(state.options[0].timer_fraction, 0.5)
        state = step_route2_focus(
            state,
            focused=True,
            post_movement_player_x=0.0,
            post_movement_player_y=0.0,
            time_scale=0.5,
        )
        self.assertEqual(state.options[0].timer_elapsed, 1)
        self.assertAlmostEqual(state.options[0].timer_fraction, 0.0)


if __name__ == "__main__":
    unittest.main()
