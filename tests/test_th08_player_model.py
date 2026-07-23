#!/usr/bin/env python3
"""Regression tests for the recovered route-2 player resource model."""

from __future__ import annotations

import unittest

from th08_player_model import (
    BombIndex,
    ROUTE2_BOMBS,
    decide_route2_bomb,
    predeath_countdown_frames,
    route2_bomb_index,
)


class PlayerModelTests(unittest.TestCase):
    def test_predeath_no_stock_is_fixed_two(self) -> None:
        self.assertEqual(
            predeath_countdown_frames(
                0,
                team_meter_left_at_least_right=True,
                spell_state_active=True,
                stage_load_index=0,
            ),
            2,
        )

    def test_predeath_caps_and_stage_multiplier_order(self) -> None:
        self.assertEqual(
            predeath_countdown_frames(
                3,
                team_meter_left_at_least_right=True,
                spell_state_active=True,
                stage_load_index=0,
            ),
            54,
        )
        self.assertEqual(
            predeath_countdown_frames(
                3,
                team_meter_left_at_least_right=False,
                spell_state_active=False,
                stage_load_index=6,
            ),
            15,
        )

    def test_route2_callback_selection(self) -> None:
        self.assertEqual(
            route2_bomb_index(focused=False, deathbomb=False),
            BombIndex.SAKUYA_NORMAL,
        )
        self.assertEqual(
            route2_bomb_index(focused=True, deathbomb=False),
            BombIndex.REMILIA_NORMAL,
        )
        self.assertEqual(
            route2_bomb_index(focused=True, deathbomb=True),
            BombIndex.SAKUYA_LAST_SPELL,
        )
        self.assertEqual(
            route2_bomb_index(focused=False, deathbomb=True),
            BombIndex.REMILIA_LAST_SPELL,
        )

    def test_route2_costs_and_durations(self) -> None:
        normal = decide_route2_bomb(3, focused=False, deathbomb=False)
        self.assertEqual((normal.bombs_consumed, normal.bombs_after), (1, 2))
        self.assertEqual(normal.profile.duration_frames, 290)

        last_spell = decide_route2_bomb(3, focused=False, deathbomb=True)
        self.assertEqual((last_spell.bombs_consumed, last_spell.bombs_after), (2, 1))
        self.assertEqual(last_spell.profile.duration_frames, 320)

        one_stock = decide_route2_bomb(1, focused=True, deathbomb=True)
        self.assertEqual((one_stock.bombs_consumed, one_stock.bombs_after), (1, 0))
        self.assertEqual(one_stock.profile.duration_frames, 350)

        dissolve = decide_route2_bomb(
            0, focused=False, deathbomb=True, forced_dissolve=True
        )
        self.assertEqual(dissolve.profile.index, BombIndex.DISSOLVE_SPELL)
        self.assertEqual((dissolve.bombs_consumed, dissolve.bombs_after), (0, 0))
        self.assertEqual(ROUTE2_BOMBS[BombIndex.DISSOLVE_SPELL].duration_frames, 200)


if __name__ == "__main__":
    unittest.main()
