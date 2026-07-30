#!/usr/bin/env python3
"""Tests for native-ordered enemy item and defeat-drop semantics."""

from __future__ import annotations

import unittest

from th08_enemy_item_drop_model import (
    DEFAULT_DROP_SEQUENCE_TYPES,
    DefaultDropSequenceState,
    EnemyDropConfiguration,
    direct_item_request,
    materialize_enemy_defeat_drop_batch,
    materialize_point_item_requests,
    materialize_power_bundle_requests,
    route_item_callback_request,
)
from th08_item_model import (
    FREE,
    HOMING,
    ITEM_BOMB,
    ITEM_LIFE_OR_BOMB,
    ITEM_POINT,
    ITEM_POWER_LARGE,
    ITEM_POWER_SMALL,
)
from th08_rng import Th08Rng


class EnemyItemDropModelTests(unittest.TestCase):
    def test_template_default_produces_one_free_small_power(self) -> None:
        rng = Th08Rng(0x1234)
        batch = materialize_enemy_defeat_drop_batch(
            EnemyDropConfiguration(),
            enemy_x=192.0,
            enemy_y=80.0,
            power=0,
            bomb_related_damage=False,
            rng=rng,
        )
        self.assertTrue(batch.helper_invoked)
        self.assertEqual(
            tuple(
                (
                    request.x,
                    request.y,
                    request.item_type,
                    request.motion_state,
                )
                for request in batch.requests
            ),
            ((192.0, 80.0, ITEM_POWER_SMALL, FREE),),
        )
        self.assertEqual(rng.calls, 0)
        self.assertEqual(batch.post_configuration, EnemyDropConfiguration())

    def test_bomb_related_primary_is_homing_but_extra_drops_are_free(
        self,
    ) -> None:
        rng = Th08Rng(0x1234)
        batch = materialize_enemy_defeat_drop_batch(
            EnemyDropConfiguration(
                primary_item_type=ITEM_LIFE_OR_BOMB,
                point_item_count=1,
                power_item_count=2,
            ),
            enemy_x=192.0,
            enemy_y=80.0,
            power=127,
            bomb_related_damage=True,
            rng=rng,
        )
        self.assertEqual(
            tuple(request.item_type for request in batch.requests),
            (
                ITEM_LIFE_OR_BOMB,
                ITEM_POWER_SMALL,
                ITEM_POWER_SMALL,
                ITEM_POINT,
            ),
        )
        self.assertEqual(
            tuple(request.motion_state for request in batch.requests),
            (HOMING, FREE, FREE, FREE),
        )
        self.assertEqual(batch.randomized_position_count, 3)
        self.assertEqual(rng.calls, 12)
        self.assertEqual(batch.post_configuration.point_item_count, 0)
        self.assertEqual(batch.post_configuration.power_item_count, 0)

    def test_full_power_converts_configured_power_count_to_points(self) -> None:
        batch = materialize_enemy_defeat_drop_batch(
            EnemyDropConfiguration(point_item_count=2, power_item_count=3),
            enemy_x=10.0,
            enemy_y=20.0,
            power=128,
            bomb_related_damage=False,
            rng=Th08Rng(1),
        )
        self.assertEqual(
            tuple(request.item_type for request in batch.requests),
            (ITEM_POWER_SMALL,) + (ITEM_POINT,) * 5,
        )

    def test_defeat_mode_three_bypasses_helper_without_clearing_counts(
        self,
    ) -> None:
        configuration = EnemyDropConfiguration(
            point_item_count=5,
            power_item_count=4,
            defeat_mode=3,
        )
        rng = Th08Rng(2)
        batch = materialize_enemy_defeat_drop_batch(
            configuration,
            enemy_x=0.0,
            enemy_y=0.0,
            power=0,
            bomb_related_damage=False,
            rng=rng,
        )
        self.assertFalse(batch.helper_invoked)
        self.assertFalse(batch.requests)
        self.assertIs(batch.post_configuration, configuration)
        self.assertEqual(rng.calls, 0)

    def test_primary_minus_one_uses_every_third_global_schedule(self) -> None:
        configuration = EnemyDropConfiguration(primary_item_type=-1)
        sequence = DefaultDropSequenceState()
        observed = []
        for _ in range(4):
            batch = materialize_enemy_defeat_drop_batch(
                configuration,
                enemy_x=0.0,
                enemy_y=0.0,
                power=0,
                bomb_related_damage=False,
                rng=Th08Rng(3),
                sequence_state=sequence,
            )
            observed.append(
                tuple(request.item_type for request in batch.requests)
            )
            sequence = batch.post_sequence_state
        self.assertEqual(
            observed,
            [
                (DEFAULT_DROP_SEQUENCE_TYPES[0],),
                (),
                (),
                (DEFAULT_DROP_SEQUENCE_TYPES[1],),
            ],
        )
        self.assertEqual(sequence, DefaultDropSequenceState(4, 2))

    def test_primary_below_minus_one_suppresses_only_primary(self) -> None:
        batch = materialize_enemy_defeat_drop_batch(
            EnemyDropConfiguration(
                primary_item_type=-2,
                point_item_count=1,
                power_item_count=1,
            ),
            enemy_x=0.0,
            enemy_y=0.0,
            power=0,
            bomb_related_damage=False,
            rng=Th08Rng(4),
        )
        self.assertEqual(
            tuple(request.item_type for request in batch.requests),
            (ITEM_POWER_SMALL, ITEM_POINT),
        )

    def test_immediate_bundle_and_point_loops_preserve_composition_and_rng(
        self,
    ) -> None:
        below_rng = Th08Rng(5)
        below = materialize_power_bundle_requests(
            enemy_x=192.0,
            enemy_y=80.0,
            count=3,
            power=0,
            rng=below_rng,
        )
        self.assertEqual(
            tuple(request.item_type for request in below),
            (ITEM_POWER_LARGE, ITEM_POWER_SMALL, ITEM_POWER_SMALL),
        )
        self.assertEqual(below_rng.calls, 12)

        full = materialize_power_bundle_requests(
            enemy_x=192.0,
            enemy_y=80.0,
            count=3,
            power=128,
            rng=Th08Rng(5),
        )
        self.assertEqual(
            tuple(request.item_type for request in full),
            (ITEM_POINT, ITEM_POINT, ITEM_POINT),
        )
        point_rng = Th08Rng(6)
        points = materialize_point_item_requests(
            enemy_x=192.0,
            enemy_y=80.0,
            count=2,
            rng=point_rng,
        )
        self.assertEqual(
            tuple(request.item_type for request in points),
            (ITEM_POINT, ITEM_POINT),
        )
        self.assertEqual(point_rng.calls, 8)

    def test_direct_and_callback_requests_use_native_types(self) -> None:
        direct = direct_item_request(
            enemy_x=1.0,
            enemy_y=2.0,
            item_type=ITEM_BOMB,
        )
        self.assertEqual(
            (direct.x, direct.y, direct.item_type, direct.motion_state),
            (1.0, 2.0, ITEM_BOMB, FREE),
        )
        self.assertEqual(
            route_item_callback_request(
                enemy_x=1.0,
                enemy_y=2.0,
                bomb_active=False,
            ).item_type,
            ITEM_LIFE_OR_BOMB,
        )
        self.assertEqual(
            route_item_callback_request(
                enemy_x=1.0,
                enemy_y=2.0,
                bomb_active=True,
            ).item_type,
            ITEM_BOMB,
        )

    def test_invalid_defeat_mode_or_sequence_state_fails_loudly(self) -> None:
        with self.assertRaisesRegex(ValueError, "mode"):
            EnemyDropConfiguration(defeat_mode=4)
        with self.assertRaisesRegex(ValueError, "counter"):
            DefaultDropSequenceState(call_counter=-1)
        with self.assertRaisesRegex(ValueError, "index"):
            DefaultDropSequenceState(
                item_index=len(DEFAULT_DROP_SEQUENCE_TYPES),
            )


if __name__ == "__main__":
    unittest.main()
