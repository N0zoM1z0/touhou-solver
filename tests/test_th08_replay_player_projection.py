#!/usr/bin/env python3
"""Regression tests for compact replay player projections."""

from __future__ import annotations

import unittest

from th08_movement_model import INPUT_BOMB, INPUT_RIGHT
from th08_route2_player_runtime import BombStartKind
from th08_replay_player_projection import project_route2_inputs


class ReplayPlayerProjectionTests(unittest.TestCase):
    def test_unresolved_bomb_press_is_explicit_and_not_activated(self) -> None:
        report = project_route2_inputs(
            (0, INPUT_BOMB | INPUT_RIGHT, INPUT_RIGHT), starting_bombs=3
        )
        self.assertEqual(report["unresolved_bomb_press_frames"], [1])
        self.assertEqual(report["accepted_bomb_starts"], [])
        self.assertEqual(report["final_state"]["bomb_stock"], 3)

    def test_explicit_normal_bomb_is_consumed_and_reported(self) -> None:
        report = project_route2_inputs(
            (0, INPUT_BOMB | INPUT_RIGHT, INPUT_RIGHT),
            starting_bombs=3,
            bomb_starts={1: BombStartKind.NORMAL},
        )
        self.assertEqual(report["unresolved_bomb_press_frames"], [])
        self.assertEqual(report["accepted_bomb_starts"][0]["index"], 0)
        self.assertEqual(report["final_state"]["bomb_stock"], 2)

    def test_event_requires_a_bomb_rising_edge(self) -> None:
        with self.assertRaises(ValueError):
            project_route2_inputs(
                (INPUT_RIGHT,),
                starting_bombs=3,
                bomb_starts={0: BombStartKind.NORMAL},
            )


if __name__ == "__main__":
    unittest.main()
