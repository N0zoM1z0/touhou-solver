#!/usr/bin/env python3
"""Regression tests for native-order TH08 laser pool execution."""

import unittest
from dataclasses import replace
from pathlib import Path

from th08_ecl import EclFile, EclHeader, Timeline
from th08_item_model import ItemResources
from th08_item_pool import ItemPoolConfig
from th08_laser_model import LASER_POOL_SIZE, spawn_laser_state
from th08_laser_pool import (
    LaserPoolState,
    LaserSlot,
    LaserSpawnRequest,
    step_laser_pool,
)
from th08_route2_player_runtime import PlayerPhase
from th08_simulator import (
    LaserPlayerConfig,
    PlayerHitContext,
    Th08Route2FrameControl,
    initial_route2_stage_simulation_state,
    route2_stage_item_laser_executor,
)


def _active_laser(*, y: float = 0.0):
    return spawn_laser_state(
        origin_x=0.0,
        origin_y=y,
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


def _step(state, **overrides):
    values = dict(
        player_x=50.0,
        player_y=0.0,
        player_half_width=2.0,
        player_half_height=2.0,
        player_state=0,
    )
    values.update(overrides)
    return step_laser_pool(state, **values)


class LaserPoolTests(unittest.TestCase):
    def test_new_laser_uses_first_free_slot_and_is_scanned_same_pass(self) -> None:
        result = _step(
            LaserPoolState(),
            spawns_before_update=(LaserSpawnRequest(_active_laser()),),
        )
        self.assertEqual(result.spawned_slots, (0,))
        self.assertEqual([(c.slot_index, c.kind) for c in result.contacts], [(0, "hit")])
        self.assertEqual(result.state.slots[0].laser.timer, 1)

    def test_first_hit_suppresses_later_hits_in_same_scan(self) -> None:
        state = LaserPoolState(
            (LaserSlot(0, _active_laser()), LaserSlot(1, _active_laser()))
        )
        result = _step(state)
        self.assertEqual([(c.slot_index, c.kind) for c in result.contacts], [(0, "hit")])

    def test_direct_overlap_does_not_become_graze_when_invulnerable(self) -> None:
        state = LaserPoolState((LaserSlot(0, _active_laser()),))
        result = _step(state, player_state=3)
        self.assertFalse(result.contacts)
        graze = _step(
            LaserPoolState((LaserSlot(0, _active_laser(y=50.0)),)),
            player_state=3,
        )
        self.assertEqual([(c.slot_index, c.kind) for c in graze.contacts], [(0, "graze")])

    def test_spawning_and_dead_states_cannot_graze(self) -> None:
        state = LaserPoolState((LaserSlot(0, _active_laser(y=50.0)),))
        self.assertFalse(_step(state, player_state=1).contacts)
        self.assertFalse(_step(state, player_state=2).contacts)

    def test_pool_exhaustion_preserves_existing_slots(self) -> None:
        state = LaserPoolState(
            tuple(LaserSlot(index, _active_laser()) for index in range(LASER_POOL_SIZE))
        )
        result = _step(
            state,
            spawns_before_update=(LaserSpawnRequest(_active_laser()),),
            player_state=2,
        )
        self.assertTrue(result.pool_exhausted)
        self.assertFalse(result.spawned_slots)
        self.assertEqual(len(result.state.slots), LASER_POOL_SIZE)

    def test_inactive_laser_releases_its_slot(self) -> None:
        state = LaserPoolState((LaserSlot(7, replace(_active_laser(), active=False)),))
        result = _step(state)
        self.assertEqual(result.released_slots, (7,))
        self.assertFalse(result.state.slots)

    def test_integrated_hit_reaches_deathbomb_on_following_frame(self) -> None:
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
            laser_player_config=LaserPlayerConfig(),
            short_spawn_mode=True,
        )
        state = replace(
            state,
            player=replace(state.player, phase=PlayerPhase.NORMAL),
        )
        executor = route2_stage_item_laser_executor()
        self.assertEqual(
            executor.event_order[-2:],
            ("item_manager_update", "laser_motion_collision_graze"),
        )
        hit_laser = replace(
            _active_laser(y=state.player.y),
            origin_x=state.player.x - 50.0,
        )
        hit = executor.step(
            state,
            Th08Route2FrameControl(
                0,
                laser_spawns_before_update=(LaserSpawnRequest(hit_laser),),
                player_hit_context=PlayerHitContext(False, False, 8),
            ),
            frame_index=0,
        ).state
        self.assertEqual(hit.player.phase, PlayerPhase.DEAD)
        self.assertEqual(hit.player.state_timer_elapsed, 15)
        self.assertIsNone(hit.last_bomb_started)

        deathbomb = executor.step(
            hit,
            Th08Route2FrameControl(0x02),
            frame_index=1,
        ).state
        self.assertEqual(deathbomb.player.phase, PlayerPhase.INVULNERABLE)
        self.assertTrue(deathbomb.last_bomb_started.is_last_spell)
        self.assertEqual(deathbomb.player.bombs, 1)
        self.assertFalse(deathbomb.last_laser_step.hit)


if __name__ == "__main__":
    unittest.main()
