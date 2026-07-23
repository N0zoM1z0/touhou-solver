#!/usr/bin/env python3
"""Tests for the transform-free native hostile-bullet pool slice."""

import unittest
from dataclasses import replace
from pathlib import Path

from th08_ecl import EclFile, EclHeader, Timeline
from th08_hostile_bullet_pool import (
    BULLET_POOL_SIZE,
    HostileBulletPoolState,
    HostileBulletSlot,
    HostileBulletSpawnRequest,
    HostileBulletState,
    native_bullet_scan_order,
    step_hostile_bullet_pool,
)
from th08_item_model import ItemResources
from th08_item_pool import ItemPoolConfig
from th08_laser_model import spawn_laser_state
from th08_laser_pool import LaserSpawnRequest
from th08_route2_player_runtime import PlayerPhase
from th08_simulator import (
    HostileBulletPlayerConfig,
    LaserPlayerConfig,
    PlayerHitContext,
    Th08Route2FrameControl,
    initial_route2_stage_simulation_state,
    route2_stage_item_projectile_executor,
)


def _bullet(*, x: float = 100.0, y: float = 100.0, age: int = 0, **kwargs):
    return HostileBulletState(x, y, 0.0, 0.0, 8.0, 8.0, age=age, **kwargs)


def _step(state, **overrides):
    values = dict(
        player_x=100.0,
        player_y=100.0,
        player_hitbox_half_width=2.0,
        player_hitbox_half_height=2.0,
        player_aux_half_width=6.0,
        player_aux_half_height=6.0,
        player_state=0,
    )
    values.update(overrides)
    return step_hostile_bullet_pool(state, **values)


class HostileBulletPoolTests(unittest.TestCase):
    def test_native_scan_order_starts_zero_then_descends(self) -> None:
        order = native_bullet_scan_order()
        self.assertEqual(order[:4], (0, 1535, 1534, 1533))
        self.assertEqual(order[-1], 1)
        self.assertEqual(len(order), BULLET_POOL_SIZE)

    def test_ring_cursor_allocation_wraps_and_new_bullet_is_scanned(self) -> None:
        state = HostileBulletPoolState(allocation_cursor=1535)
        result = _step(
            state,
            spawns_before_update=(
                HostileBulletSpawnRequest(_bullet(x=10, y=10)),
                HostileBulletSpawnRequest(_bullet(x=20, y=20)),
            ),
            player_state=2,
        )
        self.assertEqual(result.spawned_slots, (1535, 0))
        self.assertEqual(result.state.allocation_cursor, 1)
        self.assertEqual([slot.index for slot in result.state.slots], [0, 1535])
        self.assertTrue(all(slot.bullet.age == 1 for slot in result.state.slots))

    def test_exact_contact_hits_before_graze_age_and_releases_bullet(self) -> None:
        state = HostileBulletPoolState((HostileBulletSlot(4, _bullet()),))
        result = _step(state)
        self.assertEqual([(c.slot_index, c.kind) for c in result.contacts], [(4, "hit")])
        self.assertEqual(result.released_slots, (4,))

    def test_graze_latches_then_does_not_repeat(self) -> None:
        state = HostileBulletPoolState(
            (HostileBulletSlot(4, _bullet(x=130.0, age=16)),)
        )
        first = _step(state)
        self.assertEqual([(c.slot_index, c.kind) for c in first.contacts], [(4, "graze")])
        second = _step(first.state)
        self.assertFalse(second.contacts)
        self.assertEqual(second.state.graze_count, 1)

    def test_first_native_order_hit_suppresses_later_player_hit(self) -> None:
        state = HostileBulletPoolState(
            (
                HostileBulletSlot(0, _bullet()),
                HostileBulletSlot(1, _bullet()),
                HostileBulletSlot(1535, _bullet()),
            )
        )
        result = _step(state)
        self.assertEqual(
            [(c.slot_index, c.kind) for c in result.contacts],
            [(0, "hit"), (1535, "absorbed"), (1, "absorbed")],
        )

    def test_transform_bullet_is_rejected_instead_of_approximated(self) -> None:
        with self.assertRaises(NotImplementedError):
            _step(
                HostileBulletPoolState(),
                spawns_before_update=(
                    HostileBulletSpawnRequest(_bullet(transform_flags=0x20)),
                ),
            )

    def test_integrated_bullet_precedes_laser_and_owns_the_hit(self) -> None:
        program = EclFile(
            Path("empty.ecl"),
            "synthetic",
            EclHeader(1, 1, (), 0, (0,)),
            (),
            (Timeline(0, 0, 0, (), 0, 0),),
        )
        state = initial_route2_stage_simulation_state(
            program,
            rng_seed=0,
            active_timeline_difficulty_mask=1,
            item_resources=ItemResources(bombs=3),
            item_config=ItemPoolConfig(difficulty_index=4, stage_load_index=8),
            hostile_bullet_player_config=HostileBulletPlayerConfig(),
            laser_player_config=LaserPlayerConfig(),
            short_spawn_mode=True,
        )
        state = replace(
            state,
            player=replace(state.player, phase=PlayerPhase.NORMAL),
        )
        laser = spawn_laser_state(
            origin_x=state.player.x - 50.0,
            origin_y=state.player.y,
            angle=0.0,
            speed=0.0,
            tail_distance=0.0,
            head_distance=100.0,
            maximum_length=100.0,
            width=16.0,
            warmup_frames=0,
            active_frames=20,
            fade_frames=10,
            collision_enable_frame=0,
            collision_disable_frame=5,
        )
        executor = route2_stage_item_projectile_executor()
        self.assertEqual(
            executor.event_order[-3:],
            (
                "item_manager_update",
                "hostile_bullet_transform_motion_collision_graze",
                "laser_motion_collision_graze",
            ),
        )
        result = executor.step(
            state,
            Th08Route2FrameControl(
                0,
                hostile_bullet_spawns_before_update=(
                    HostileBulletSpawnRequest(
                        _bullet(x=state.player.x, y=state.player.y)
                    ),
                ),
                laser_spawns_before_update=(LaserSpawnRequest(laser),),
                player_hit_context=PlayerHitContext(False, False, 8),
            ),
            frame_index=0,
        ).state
        self.assertTrue(result.last_hostile_bullet_step.hit)
        self.assertFalse(result.last_laser_step.hit)
        self.assertEqual(result.player.phase, PlayerPhase.DEAD)


if __name__ == "__main__":
    unittest.main()
