#!/usr/bin/env python3
"""Stable-slot TH08 item manager built from the recovered item primitives."""

from __future__ import annotations

from dataclasses import dataclass, replace

from th08_item_model import (
    ITEM_POWER_LARGE,
    ITEM_POWER_OVERFLOW,
    ITEM_POWER_SMALL,
    ItemCollection,
    ItemResources,
    ItemState,
    collect_item,
    item_collection_overlaps,
    spawn_item_state,
    step_item,
)
from th08_rng import Th08Rng


ITEM_POOL_SIZE = 2096


@dataclass(frozen=True)
class ItemSpawnRequest:
    x: float
    y: float
    item_type: int
    motion_state: int


@dataclass(frozen=True)
class ItemSlot:
    index: int
    item: ItemState


@dataclass(frozen=True)
class ItemPoolConfig:
    difficulty_index: int
    route_id: int
    point_value_line_y: float = 128.0
    homing_speed: float = 10.0
    unfocused_fall_scale: float = 0.6499999761581421
    focused_fall_scale: float = 0.8999999761581421
    collection_width: float = 24.0
    playfield_bottom_y: float = 448.0
    score_double: bool = False
    special_score_mode: bool = False
    stage_counter_0c: int = 0


@dataclass(frozen=True)
class ItemPoolState:
    slots: tuple[ItemSlot, ...]
    resources: ItemResources
    next_allocation_index: int = 0
    active_order: tuple[int, ...] = ()


@dataclass(frozen=True)
class CollectedItem:
    slot_index: int
    item_type: int
    x: float
    y: float
    result: ItemCollection


@dataclass(frozen=True)
class ItemPoolStep:
    state: ItemPoolState
    collected: tuple[CollectedItem, ...]
    spawned_slots: tuple[int, ...]
    culled_slots: tuple[int, ...]
    pool_exhausted: bool


def initial_item_pool_state(resources: ItemResources) -> ItemPoolState:
    return ItemPoolState((), resources)


def _validate_state(state: ItemPoolState) -> tuple[int, ...]:
    indices = tuple(slot.index for slot in state.slots)
    if indices != tuple(sorted(indices)) or len(indices) != len(set(indices)):
        raise ValueError("item slots must be uniquely sorted")
    if any(not 0 <= index < ITEM_POOL_SIZE for index in indices):
        raise ValueError("item slot index is outside the native pool")
    if not 0 <= state.next_allocation_index < ITEM_POOL_SIZE:
        raise ValueError("item allocation cursor is outside the native pool")
    active_order = state.active_order or indices
    if len(active_order) != len(set(active_order)) or set(active_order) != set(
        indices
    ):
        raise ValueError(
            "item active order must contain every occupied slot exactly once"
        )
    return active_order


def _next_free_slot(
    occupied: set[int],
    cursor: int,
) -> tuple[int | None, int]:
    """Match the native rotating allocation cursor and cyclic scan."""

    for _ in range(ITEM_POOL_SIZE):
        index = cursor
        cursor = (cursor + 1) % ITEM_POOL_SIZE
        if index not in occupied:
            return index, cursor
    return None, cursor


def _convert_active_power_items(slots: dict[int, ItemState]) -> None:
    for index, item in tuple(slots.items()):
        if item.item_type in (ITEM_POWER_SMALL, ITEM_POWER_LARGE):
            converted = replace(item, item_type=ITEM_POWER_OVERFLOW)
            if converted.velocity_y > -0.5:
                converted = replace(
                    converted,
                    velocity_x=0.0,
                    velocity_y=-0.5,
                )
            slots[index] = converted


def step_item_pool(
    state: ItemPoolState,
    *,
    spawns_before_update: tuple[ItemSpawnRequest, ...] = (),
    player_x: float,
    player_y: float,
    player_state: int,
    focused: bool,
    config: ItemPoolConfig,
    rng: Th08Rng,
    time_scale: float = 1.0,
    timer_scale: float = 1.0,
    global_scatter_timer_negative: bool = False,
) -> ItemPoolStep:
    """Spawn, move, collect, and cull once in native active-list order.

    ``spawns_before_update`` is deliberately explicit: it means the source
    event occurred before priority-14 ``item_manager_update``. Items created by
    the later hostile-projectile pass must be supplied on the next frame.
    """

    active_order = list(_validate_state(state))
    slots = {slot.index: slot.item for slot in state.slots}
    occupied = set(slots)
    allocation_cursor = state.next_allocation_index
    spawned: list[int] = []
    pool_exhausted = False
    resources = state.resources

    for request in spawns_before_update:
        # Native rejects an out-of-range spawn before it scans or advances the
        # allocation cursor and before callback RNG is consumed.
        if request.x < -64.0 or request.x > 448.0:
            continue
        index, allocation_cursor = _next_free_slot(
            occupied,
            allocation_cursor,
        )
        if index is None:
            pool_exhausted = True
            break
        item = spawn_item_state(
            x=request.x,
            y=request.y,
            item_type=request.item_type,
            motion_state=request.motion_state,
            power=resources.power,
            player_state=player_state,
            rng=rng,
        )
        if item is None:
            continue
        slots[index] = item
        occupied.add(index)
        active_order.append(index)
        spawned.append(index)

    collected: list[CollectedItem] = []
    culled: list[int] = []
    fall_scale = (
        config.focused_fall_scale if focused else config.unfocused_fall_scale
    )
    for index in tuple(active_order):
        item = slots.get(index)
        if item is None:
            continue
        stepped = step_item(
            item,
            player_x=player_x,
            player_y=player_y,
            player_state=player_state,
            focused=focused,
            power=resources.power,
            route_id=config.route_id,
            point_value_line_y=config.point_value_line_y,
            homing_speed=config.homing_speed,
            fall_scale=fall_scale,
            time_scale=time_scale,
            timer_scale=timer_scale,
            global_scatter_timer_negative=global_scatter_timer_negative,
            playfield_bottom_y=config.playfield_bottom_y,
        )
        if not stepped.alive:
            del slots[index]
            active_order.remove(index)
            culled.append(index)
            continue
        slots[index] = stepped.item
        if not stepped.collection_allowed or not item_collection_overlaps(
            player_x=player_x,
            player_y=player_y,
            player_state=player_state,
            item_x=stepped.item.x,
            item_y=stepped.item.y,
            collection_width=config.collection_width,
        ):
            continue

        result = collect_item(
            stepped.item,
            resources,
            difficulty_index=config.difficulty_index,
            score_double=config.score_double,
            special_score_mode=config.special_score_mode,
            stage_counter_0c=config.stage_counter_0c,
            point_value_line_y=config.point_value_line_y,
        )
        resources = result.resources
        collected.append(
            CollectedItem(
                index,
                stepped.item.item_type,
                stepped.item.x,
                stepped.item.y,
                result,
            )
        )
        del slots[index]
        active_order.remove(index)
        if result.converted_active_power_items:
            _convert_active_power_items(slots)

    next_slots = tuple(ItemSlot(index, item) for index, item in sorted(slots.items()))
    return ItemPoolStep(
        ItemPoolState(
            next_slots,
            resources,
            allocation_cursor,
            tuple(active_order),
        ),
        tuple(collected),
        tuple(spawned),
        tuple(culled),
        pool_exhausted,
    )
