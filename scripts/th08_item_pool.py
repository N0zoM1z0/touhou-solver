#!/usr/bin/env python3
"""Stable-slot TH08 item manager built from the recovered item primitives."""

from __future__ import annotations

from dataclasses import dataclass, replace

from th08_item_model import (
    HOMING,
    ITEM_POWER_LARGE,
    ITEM_POWER_OVERFLOW,
    ITEM_POWER_SMALL,
    ITEM_TIME,
    ITEM_TIME_PSEUDO,
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
class ItemAllocationFailure:
    request_index: int
    reason: str


@dataclass(frozen=True)
class ItemPoolStep:
    state: ItemPoolState
    collected: tuple[CollectedItem, ...]
    spawned_slots: tuple[int, ...]
    culled_slots: tuple[int, ...]
    allocation_failures: tuple[ItemAllocationFailure, ...]
    pool_exhausted: bool


@dataclass(frozen=True)
class ItemPoolAllocationStep:
    state: ItemPoolState
    spawned_slots: tuple[int, ...]
    failures: tuple[ItemAllocationFailure, ...]
    pool_exhausted: bool


@dataclass(frozen=True)
class ItemPoolForcedHoming:
    state: ItemPoolState
    affected_slots: tuple[int, ...]


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


def force_all_active_items_homing(
    state: ItemPoolState,
) -> ItemPoolForcedHoming:
    """Apply the post-allocation item mutation used by message start.

    Native ``item_manager_force_all_homing`` (0x004413E0) walks the current
    active list, sets motion state 1, and stores velocity ``(0, -0.5, 0)``.
    The solver's item state is two-dimensional, so the observed zero z
    component is structural rather than stored here. No timer, position,
    type, resource, allocation-cursor, active-order, or RNG state changes in
    this sub-transition.
    """

    active_order = _validate_state(state)
    slots = {slot.index: slot.item for slot in state.slots}
    for index in active_order:
        slots[index] = replace(
            slots[index],
            velocity_x=0.0,
            velocity_y=-0.5,
            motion_state=HOMING,
        )
    successor = replace(
        state,
        slots=tuple(
            ItemSlot(index, item) for index, item in sorted(slots.items())
        ),
    )
    return ItemPoolForcedHoming(successor, active_order)


def _next_free_slot(
    occupied: set[int],
    cursor: int,
    *,
    probe_limit: int = ITEM_POOL_SIZE,
) -> tuple[int | None, int]:
    """Match the native rotating allocation cursor and cyclic scan."""

    if not 1 <= probe_limit <= ITEM_POOL_SIZE:
        raise ValueError("item allocation probe limit is outside the pool")
    for _ in range(probe_limit):
        index = cursor
        cursor = (cursor + 1) % ITEM_POOL_SIZE
        if index not in occupied:
            return index, cursor
    return None, cursor


def allocate_items_before_update(
    state: ItemPoolState,
    *,
    requests: tuple[ItemSpawnRequest, ...],
    player_state: int,
    rng: Th08Rng,
) -> ItemPoolAllocationStep:
    """Apply only native item allocation, without the later manager update.

    Effective type 7 is a native special case: after one occupied cursor
    probe, ``item_pool_spawn`` returns failure instead of scanning later
    slots. Input pseudo-type 10 is remapped to effective type 7 before that
    branch. Every other type scans the complete cyclic pool.
    """

    active_order = list(_validate_state(state))
    slots = {slot.index: slot.item for slot in state.slots}
    occupied = set(slots)
    allocation_cursor = state.next_allocation_index
    spawned: list[int] = []
    failures: list[ItemAllocationFailure] = []
    pool_exhausted = False

    for request_index, request in enumerate(requests):
        if request.x < -64.0 or request.x > 448.0:
            failures.append(
                ItemAllocationFailure(request_index, "x_out_of_range")
            )
            continue
        effective_type_7 = request.item_type in (
            ITEM_TIME,
            ITEM_TIME_PSEUDO,
        )
        index, allocation_cursor = _next_free_slot(
            occupied,
            allocation_cursor,
            probe_limit=1 if effective_type_7 else ITEM_POOL_SIZE,
        )
        if index is None:
            exhausted = len(occupied) == ITEM_POOL_SIZE
            pool_exhausted = pool_exhausted or exhausted
            failures.append(
                ItemAllocationFailure(
                    request_index,
                    (
                        "pool_exhausted"
                        if exhausted
                        else "effective_type_7_cursor_slot_occupied"
                    ),
                )
            )
            continue
        item = spawn_item_state(
            x=request.x,
            y=request.y,
            item_type=request.item_type,
            motion_state=request.motion_state,
            power=state.resources.power,
            player_state=player_state,
            rng=rng,
        )
        if item is None:
            raise RuntimeError(
                "validated item allocation unexpectedly rejected its spawn"
            )
        slots[index] = item
        occupied.add(index)
        active_order.append(index)
        spawned.append(index)

    return ItemPoolAllocationStep(
        replace(
            state,
            slots=tuple(
                ItemSlot(index, item)
                for index, item in sorted(slots.items())
            ),
            next_allocation_index=allocation_cursor,
            active_order=tuple(active_order),
        ),
        tuple(spawned),
        tuple(failures),
        pool_exhausted,
    )


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

    allocation = allocate_items_before_update(
        state,
        requests=spawns_before_update,
        player_state=player_state,
        rng=rng,
    )
    active_order = list(_validate_state(allocation.state))
    slots = {slot.index: slot.item for slot in allocation.state.slots}
    allocation_cursor = allocation.state.next_allocation_index
    resources = allocation.state.resources

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
        allocation.spawned_slots,
        tuple(culled),
        allocation.failures,
        allocation.pool_exhausted,
    )
