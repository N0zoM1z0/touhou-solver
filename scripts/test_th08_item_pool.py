#!/usr/bin/env python3
"""Tests for stable-slot item execution and integrated shared-RNG order."""

from __future__ import annotations

import struct
import unittest
from dataclasses import replace
from pathlib import Path

from th08_ecl import EclFile, EclHeader, Timeline, TimelineInstruction
from th08_item_model import (
    FREE,
    ITEM_BOMB,
    ITEM_POWER_LARGE,
    ITEM_POWER_OVERFLOW,
    ITEM_POWER_SMALL,
    ItemResources,
    ItemState,
    SCATTER_DELAY,
)
from th08_item_pool import (
    ItemPoolConfig,
    ItemPoolState,
    ItemSlot,
    ItemSpawnRequest,
    step_item_pool,
)
from th08_rng import Th08Rng
from th08_route2_player_runtime import PlayerPhase
from th08_simulator import (
    Th08Route2FrameControl,
    initial_route2_stage_simulation_state,
    route2_stage_item_executor,
)


CONFIG = ItemPoolConfig(difficulty_index=4, stage_load_index=8)


def _word(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def _random_spawn_ecl() -> EclFile:
    insn = TimelineInstruction(
        0x100,
        0,
        0x02,
        36,
        0xFF,
        (3, _word(10.0), _word(20.0), _word(-20.0), 10, 1, 1000),
    )
    timeline = Timeline(0, 0, 0, (insn,), 0, 0)
    return EclFile(
        Path("random.ecl"),
        "synthetic",
        EclHeader(1, 1, (), 0, (0,)),
        (),
        (timeline,),
    )


class ItemPoolTests(unittest.TestCase):
    def test_spawn_move_collect_bomb_and_release_slot(self) -> None:
        result = step_item_pool(
            ItemPoolState((), ItemResources(bombs=2)),
            spawns_before_update=(ItemSpawnRequest(100, 100, ITEM_BOMB, FREE),),
            player_x=100,
            player_y=100,
            player_state=0,
            focused=False,
            config=CONFIG,
            rng=Th08Rng(0),
        )
        self.assertEqual(result.spawned_slots, (0,))
        self.assertEqual(result.state.resources.bombs, 3)
        self.assertEqual(len(result.collected), 1)
        self.assertFalse(result.state.slots)

    def test_reaching_full_power_converts_every_active_power_item(self) -> None:
        state = ItemPoolState(
            (
                ItemSlot(0, ItemState(300, 300, 0, 0, item_type=ITEM_POWER_SMALL)),
                ItemSlot(1, ItemState(100, 100, 0, 0, item_type=ITEM_POWER_LARGE)),
                ItemSlot(2, ItemState(320, 300, 0, 0, item_type=ITEM_POWER_LARGE)),
            ),
            ItemResources(power=120),
        )
        result = step_item_pool(
            state,
            player_x=100,
            player_y=100,
            player_state=0,
            focused=False,
            config=CONFIG,
            rng=Th08Rng(0),
        )
        self.assertGreaterEqual(result.state.resources.power, 128)
        self.assertEqual(
            [slot.item.item_type for slot in result.state.slots],
            [ITEM_POWER_OVERFLOW, ITEM_POWER_OVERFLOW],
        )

    def test_integrated_timeline_then_item_share_one_rng_stream(self) -> None:
        program = _random_spawn_ecl()
        state = initial_route2_stage_simulation_state(
            program,
            rng_seed=0xC0A4,
            active_timeline_difficulty_mask=0x0F,
            item_resources=ItemResources(bombs=3),
            item_config=CONFIG,
            short_spawn_mode=True,
        )
        state = replace(
            state,
            player=replace(state.player, phase=PlayerPhase.NORMAL),
        )
        executor = route2_stage_item_executor()
        self.assertEqual(
            executor.event_order,
            (
                "replay_publish_input",
                "player_input_movement",
                "stage_timeline_step",
                "item_manager_update",
            ),
        )
        result = executor.step(
            state,
            Th08Route2FrameControl(
                0,
                item_spawns_before_update=(
                    ItemSpawnRequest(300, 300, ITEM_POWER_SMALL, SCATTER_DELAY),
                ),
            ),
            frame_index=0,
        ).state
        self.assertEqual(result.gameplay_rng_calls, 6)
        self.assertEqual(result.timeline.rng_calls, 2)
        self.assertEqual(len(result.last_timeline_step.spawns), 1)
        self.assertEqual(len(result.item_pool.slots), 1)

    def test_player_bomb_use_and_item_stock_stay_synchronized(self) -> None:
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
            item_config=CONFIG,
            short_spawn_mode=True,
        )
        state = replace(
            state,
            player=replace(state.player, phase=PlayerPhase.NORMAL),
        )
        from th08_route2_player_runtime import BombStartKind

        result = route2_stage_item_executor().step(
            state,
            Th08Route2FrameControl(0x02, BombStartKind.NORMAL),
            frame_index=0,
        ).state
        self.assertEqual(result.player.bombs, 2)
        self.assertEqual(result.item_pool.resources.bombs, 2)


if __name__ == "__main__":
    unittest.main()
