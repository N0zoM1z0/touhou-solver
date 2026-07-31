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
    HOMING,
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
    force_all_active_items_homing,
    step_item_pool,
)
from th08_rng import Th08Rng
from th08_route2_player_runtime import PlayerPhase
from th08_simulator import (
    Th08Route2FrameControl,
    initial_route2_stage_simulation_state,
    route2_stage_item_executor,
)


CONFIG = ItemPoolConfig(difficulty_index=4, route_id=2)


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
    def test_message_start_forces_active_list_homing_without_other_mutation(
        self,
    ) -> None:
        resources = ItemResources(
            power=23,
            bombs=3,
            lives=2,
            score_display=456,
        )
        state = ItemPoolState(
            (
                ItemSlot(
                    1,
                    ItemState(
                        10,
                        20,
                        1.25,
                        3.5,
                        motion_state=FREE,
                        timer_elapsed=17.25,
                        item_type=ITEM_POWER_SMALL,
                        full_value=True,
                    ),
                ),
                ItemSlot(
                    4,
                    ItemState(
                        30,
                        40,
                        -3,
                        2,
                        motion_state=SCATTER_DELAY,
                        timer_elapsed=8.5,
                        item_type=ITEM_BOMB,
                        start_x=7,
                        start_y=9,
                        target_x=11,
                        target_y=13,
                    ),
                ),
            ),
            resources,
            next_allocation_index=29,
            active_order=(4, 1),
        )

        transition = force_all_active_items_homing(state)

        self.assertEqual(transition.affected_slots, (4, 1))
        self.assertEqual(transition.state.resources, resources)
        self.assertEqual(transition.state.next_allocation_index, 29)
        self.assertEqual(transition.state.active_order, (4, 1))
        self.assertEqual(
            [
                (
                    slot.index,
                    slot.item.velocity_x,
                    slot.item.velocity_y,
                    slot.item.motion_state,
                )
                for slot in transition.state.slots
            ],
            [
                (1, 0.0, -0.5, HOMING),
                (4, 0.0, -0.5, HOMING),
            ],
        )
        for before, after in zip(
            (slot.item for slot in state.slots),
            (slot.item for slot in transition.state.slots),
            strict=True,
        ):
            self.assertEqual(
                replace(
                    after,
                    velocity_x=before.velocity_x,
                    velocity_y=before.velocity_y,
                    motion_state=before.motion_state,
                ),
                before,
            )
        self.assertEqual(state.slots[0].item.motion_state, FREE)
        self.assertEqual(state.slots[1].item.motion_state, SCATTER_DELAY)

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
        # Slot 0 was already updated before the pickup and retains the native
        # conversion clamp. Slot 2 is converted before its active-list turn,
        # then immediately performs the ordinary full-Power homing update.
        self.assertEqual(
            (
                result.state.slots[0].item.velocity_x,
                result.state.slots[0].item.velocity_y,
            ),
            (0.0, -0.5),
        )
        self.assertEqual(result.state.slots[1].item.motion_state, HOMING)

    def test_rotating_cursor_and_active_list_order_control_same_frame_ledger(
        self,
    ) -> None:
        state = ItemPoolState(
            (
                ItemSlot(
                    2,
                    ItemState(100, 100, 0, 0, item_type=ITEM_POWER_SMALL),
                ),
                ItemSlot(
                    10,
                    ItemState(100, 100, 0, 0, item_type=ITEM_POWER_LARGE),
                ),
            ),
            ItemResources(power=120, point_value=100000),
            next_allocation_index=10,
            active_order=(10, 2),
        )
        result = step_item_pool(
            state,
            player_x=100,
            player_y=100,
            player_state=0,
            focused=False,
            config=CONFIG,
            rng=Th08Rng(0x1234),
        )
        self.assertEqual(
            [(item.slot_index, item.item_type) for item in result.collected],
            [(10, ITEM_POWER_LARGE), (2, ITEM_POWER_OVERFLOW)],
        )
        self.assertEqual(result.state.resources.power, 128)
        self.assertEqual(result.state.active_order, ())
        self.assertEqual(result.state.next_allocation_index, 10)

        spawned = step_item_pool(
            result.state,
            spawns_before_update=(
                ItemSpawnRequest(300, 300, ITEM_POWER_SMALL, FREE),
            ),
            player_x=0,
            player_y=400,
            player_state=0,
            focused=False,
            config=CONFIG,
            rng=Th08Rng(0x1234),
        )
        self.assertEqual(spawned.spawned_slots, (10,))
        self.assertEqual(spawned.state.next_allocation_index, 11)
        self.assertEqual(spawned.state.active_order, (10,))

    def test_rejected_spawn_does_not_advance_cursor_or_rng(self) -> None:
        rng = Th08Rng(0x1234)
        result = step_item_pool(
            ItemPoolState(
                (),
                ItemResources(),
                next_allocation_index=37,
            ),
            spawns_before_update=(
                ItemSpawnRequest(-65, 100, ITEM_POWER_SMALL, SCATTER_DELAY),
            ),
            player_x=0,
            player_y=400,
            player_state=0,
            focused=False,
            config=CONFIG,
            rng=rng,
        )
        self.assertEqual(result.spawned_slots, ())
        self.assertEqual(result.state.next_allocation_index, 37)
        self.assertEqual(rng.calls, 0)

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
