#!/usr/bin/env python3
"""Regression tests for the recovered TH08 item runtime."""

from __future__ import annotations

import unittest

from th08_item_model import (
    FREE,
    HOMING,
    INTERPOLATE,
    ITEM_LIFE_OR_BOMB,
    ITEM_POINT,
    ITEM_POWER_LARGE,
    ITEM_POWER_OVERFLOW,
    ITEM_TIME,
    PLAYER_DYING,
    SCATTER_DELAY,
    SCATTER_TO_HOME,
    ItemResources,
    ItemState,
    collect_item,
    item_collection_overlaps,
    item_should_home,
    point_extend_threshold,
    point_item_value,
    spawn_item_state,
    step_item,
    step_standard_item,
)
from th08_rng import Th08Rng


STEP_ARGS = dict(
    player_x=10,
    player_y=128,
    player_state=0,
    focused=False,
    power=128,
    route_id=2,
    point_value_line_y=128,
    homing_speed=10,
    fall_scale=0.9,
)


class ItemModelTests(unittest.TestCase):
    def test_route2_collection_boundary_is_inclusive(self) -> None:
        self.assertTrue(
            item_collection_overlaps(
                player_x=100,
                player_y=200,
                player_state=0,
                item_x=124,
                item_y=176,
                collection_width=24,
            )
        )
        self.assertFalse(
            item_collection_overlaps(
                player_x=100,
                player_y=200,
                player_state=0,
                item_x=124.001,
                item_y=176,
                collection_width=24,
            )
        )

    def test_homing_uses_exact_header_speed(self) -> None:
        item = ItemState(0, 0, 0, -2.2)
        result = step_standard_item(
            item,
            player_x=3,
            player_y=4,
            player_state=0,
            focused=True,
            power=0,
            route_id=2,
            point_value_line_y=128,
            homing_speed=10,
            fall_scale=0.9,
        )
        self.assertEqual(result.motion_state, HOMING)
        self.assertAlmostEqual(result.velocity_x, 6)
        self.assertAlmostEqual(result.velocity_y, 8)
        self.assertAlmostEqual(result.x, 6)
        self.assertAlmostEqual(result.y, 8)

    def test_unfocused_low_power_homing_exception_uses_route_not_stage(self) -> None:
        item = ItemState(0, 0, 0, -2.2)
        common = {
            "player_y": 64,
            "player_state": 0,
            "focused": False,
            "power": 0,
            "point_value_line_y": 128,
        }
        self.assertTrue(item_should_home(item, route_id=1, **common))
        self.assertTrue(item_should_home(item, route_id=6, **common))
        self.assertFalse(item_should_home(item, route_id=2, **common))

    def test_point_line_boundary_falls_with_sakuya_scale(self) -> None:
        item = ItemState(10, 20, 1, -2.2)
        result = step_standard_item(item, **(STEP_ARGS | {"fall_scale": 0.65}))
        self.assertEqual(result.motion_state, FREE)
        self.assertEqual(result.velocity_x, 0)
        self.assertAlmostEqual(result.y, 20 - 2.2 * 0.65)
        self.assertAlmostEqual(result.velocity_y, -2.2 + 0.03 * 0.65)

    def test_dying_player_releases_homing_item(self) -> None:
        item = ItemState(10, 20, 3, 4, HOMING)
        result = step_standard_item(
            item,
            **(STEP_ARGS | {"player_y": 40, "player_state": PLAYER_DYING}),
        )
        self.assertEqual(result.motion_state, FREE)
        self.assertAlmostEqual(result.y, 20 - 0.7 * 0.9)
        self.assertAlmostEqual(result.velocity_y, -0.7 + 0.03 * 0.9)

    def test_spawn_modes_consume_rng_and_map_pseudo_type_10(self) -> None:
        rng = Th08Rng(0xC0A4)
        item = spawn_item_state(
            x=100,
            y=50,
            item_type=10,
            motion_state=0,
            power=0,
            player_state=0,
            rng=rng,
        )
        assert item is not None
        self.assertEqual(item.item_type, ITEM_TIME)
        self.assertEqual(item.motion_state, SCATTER_TO_HOME)
        self.assertEqual(rng.calls, 4)
        self.assertGreaterEqual(item.velocity_x, -0.6)
        self.assertLess(item.velocity_x, 0.6)
        self.assertGreaterEqual(item.velocity_y, -2.2)
        self.assertLessEqual(item.velocity_y, -2.0)

    def test_state2_interpolates_for_60_timer_frames(self) -> None:
        item = ItemState(
            10,
            20,
            10,
            10,
            INTERPOLATE,
            timer_elapsed=30,
            start_x=10,
            start_y=20,
            target_x=110,
            target_y=220,
        )
        result = step_item(item, **STEP_ARGS)
        self.assertEqual((result.item.x, result.item.y), (60, 120))
        self.assertEqual(result.item.motion_state, INTERPOLATE)
        self.assertTrue(result.collection_allowed)

    def test_state3_transition_uses_both_acceleration_terms(self) -> None:
        item = ItemState(10, 20, 0.5, -0.01, SCATTER_DELAY)
        result = step_item(item, **STEP_ARGS)
        self.assertEqual(result.item.motion_state, HOMING)
        self.assertTrue(result.collection_allowed)
        self.assertAlmostEqual(result.item.x, 10 + 0.5 * 0.9)
        self.assertAlmostEqual(result.item.y, 20 + 0.04 * 0.9)
        self.assertAlmostEqual(result.item.velocity_y, 0.04 + 0.03 * 0.9)

    def test_state5_moves_once_while_rising_and_twice_on_transition(self) -> None:
        rising = step_item(ItemState(10, 20, 0.5, -1, SCATTER_TO_HOME), **STEP_ARGS)
        self.assertEqual(rising.item.motion_state, SCATTER_TO_HOME)
        self.assertFalse(rising.collection_allowed)
        self.assertAlmostEqual(rising.item.x, 10 + 0.5 * 0.9)
        self.assertAlmostEqual(rising.item.y, 20 - 0.95 * 0.9)

        transition = step_item(ItemState(10, 20, 0.5, -0.01, SCATTER_TO_HOME), **STEP_ARGS)
        self.assertEqual(transition.item.motion_state, HOMING)
        self.assertTrue(transition.collection_allowed)
        self.assertAlmostEqual(transition.item.x, 10 + 2 * 0.5 * 0.9)
        self.assertAlmostEqual(transition.item.y, 20 + 2 * 0.04 * 0.9)

    def test_point_value_line_is_strict_and_overflow_is_one_tenth(self) -> None:
        self.assertEqual(
            point_item_value(
                item_y=127.999,
                point_value_line_y=128,
                base_point_value=100000,
                full_value=False,
            )[0],
            100000,
        )
        self.assertEqual(
            point_item_value(
                item_y=128,
                point_value_line_y=128,
                base_point_value=100000,
                full_value=False,
            )[0],
            50000,
        )
        self.assertEqual(
            point_item_value(
                item_y=128,
                point_value_line_y=128,
                base_point_value=100000,
                full_value=False,
                overflow_power=True,
            )[0],
            5000,
        )

    def test_power_crossing_and_point_extend_rewards(self) -> None:
        power = collect_item(
            ItemState(0, 0, 0, 0, item_type=ITEM_POWER_LARGE),
            ItemResources(power=124),
            difficulty_index=3,
        )
        self.assertEqual(power.resources.power, 132)
        self.assertTrue(power.converted_active_power_items)
        self.assertTrue(power.power_level_changed)
        self.assertEqual(power.score_value, 10)

        point = collect_item(
            ItemState(0, 100, 0, 0, item_type=ITEM_POINT),
            ItemResources(
                lives=7,
                point_value=100000,
                point_count_2c=99,
                point_count_30=99,
            ),
            difficulty_index=3,
        )
        self.assertEqual(point.resources.lives, 8)
        self.assertEqual(point.resources.point_extend_index, 1)
        self.assertEqual(point.life_awards, 1)

    def test_extra_extend_threshold_and_life_item_bomb_fallback(self) -> None:
        self.assertEqual(point_extend_threshold(4, 0), 200)
        self.assertEqual(point_extend_threshold(4, 1), 666)
        self.assertEqual(point_extend_threshold(4, 3), 99999)
        result = collect_item(
            ItemState(0, 0, 0, 0, item_type=ITEM_LIFE_OR_BOMB),
            ItemResources(lives=8, bombs=6),
            difficulty_index=4,
        )
        self.assertEqual((result.resources.lives, result.resources.bombs), (8, 7))
        self.assertEqual(result.bomb_awards, 1)

    def test_time_item_raises_point_value_every_other_unit(self) -> None:
        first = collect_item(
            ItemState(0, 0, 0, 0, item_type=ITEM_TIME),
            ItemResources(point_value=100000, point_count_2c=100, point_count_30=80),
            difficulty_index=4,
        )
        self.assertEqual(first.score_value, 400)
        self.assertEqual(first.resources.point_value, 100010)
        self.assertEqual(first.resources.time_units_44, 1)
        second = collect_item(
            ItemState(0, 0, 0, 0, item_type=ITEM_TIME),
            first.resources,
            difficulty_index=4,
        )
        self.assertEqual(second.resources.point_value, 100010)
        self.assertEqual(second.resources.time_units_44, 2)

    def test_full_value_flag_and_score_double_precede_comparison(self) -> None:
        result = collect_item(
            ItemState(0, 128, 0, 0, item_type=ITEM_POWER_OVERFLOW),
            ItemResources(point_value=100000),
            difficulty_index=3,
            score_double=True,
        )
        self.assertTrue(result.full_value_earned)


if __name__ == "__main__":
    unittest.main()
