#!/usr/bin/env python3
"""Regression tests for TH08 route-2 movement and input decoding."""

from __future__ import annotations

import unittest

from movement_model import Direction
from th08_movement_model import (
    INPUT_DOWN,
    INPUT_FOCUS,
    INPUT_LEFT,
    INPUT_RIGHT,
    INPUT_UP,
    TH08_PLAYFIELD_BOUNDS,
    decode_th08_direction,
    route2_effective_focus,
    step_route2_movement,
)
from th08_option_model import Route2FocusState, step_route2_focus


class Th08MovementModelTests(unittest.TestCase):
    def test_direction_decoder_preserves_native_test_order(self) -> None:
        self.assertEqual(decode_th08_direction(0), Direction.NEUTRAL)
        self.assertEqual(decode_th08_direction(INPUT_DOWN), Direction.DOWN)
        self.assertEqual(
            decode_th08_direction(INPUT_UP | INPUT_RIGHT), Direction.UP_RIGHT
        )
        self.assertEqual(
            decode_th08_direction(INPUT_UP | INPUT_DOWN | INPUT_LEFT),
            Direction.UP_LEFT,
        )

    def test_route2_cardinal_and_diagonal_speeds(self) -> None:
        unfocused = step_route2_movement(
            x=100.0, y=200.0, input_mask=INPUT_RIGHT
        )
        self.assertAlmostEqual(unfocused.x, 104.0)
        focused = step_route2_movement(
            x=100.0,
            y=200.0,
            input_mask=INPUT_FOCUS | INPUT_UP | INPUT_LEFT,
        )
        self.assertAlmostEqual(focused.velocity_x, -1.6263456344604492)
        self.assertAlmostEqual(focused.velocity_y, -1.6263456344604492)

    def test_default_bounds_are_native_player_center_bounds(self) -> None:
        self.assertEqual(
            (
                TH08_PLAYFIELD_BOUNDS.left,
                TH08_PLAYFIELD_BOUNDS.top,
                TH08_PLAYFIELD_BOUNDS.right,
                TH08_PLAYFIELD_BOUNDS.bottom,
            ),
            (8.0, 16.0, 376.0, 432.0),
        )
        cases = (
            (8.0, 200.0, INPUT_LEFT, 8.0, 200.0),
            (376.0, 200.0, INPUT_RIGHT, 376.0, 200.0),
            (200.0, 16.0, INPUT_UP, 200.0, 16.0),
            (200.0, 432.0, INPUT_DOWN, 200.0, 432.0),
        )
        for x, y, mask, expected_x, expected_y in cases:
            with self.subTest(mask=mask):
                step = step_route2_movement(x=x, y=y, input_mask=mask)
                self.assertEqual((step.x, step.y), (expected_x, expected_y))

    def test_active_bomb_callback_parity_overrides_focus_input(self) -> None:
        self.assertFalse(
            route2_effective_focus(
                INPUT_FOCUS, bomb_active=True, bomb_callback_index=0
            )
        )
        self.assertTrue(
            route2_effective_focus(0, bomb_active=True, bomb_callback_index=1)
        )

    def test_option_entry_captures_position_after_same_frame_movement(self) -> None:
        movement = step_route2_movement(
            x=100.0,
            y=200.0,
            input_mask=INPUT_FOCUS | INPUT_RIGHT,
        )
        focus = step_route2_focus(
            Route2FocusState(),
            focused=True,
            post_movement_player_x=movement.x,
            post_movement_player_y=movement.y,
        )
        self.assertAlmostEqual(focus.options[0].target_x, movement.x - 30.0)
        self.assertAlmostEqual(focus.options[0].target_y, movement.y - 16.0)


if __name__ == "__main__":
    unittest.main()
