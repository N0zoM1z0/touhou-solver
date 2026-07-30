#!/usr/bin/env python3
"""Executable TH08 item spawn, motion, collection, and reward model.

The formulas are observed in item_pool_spawn (0x004400A0),
item_manager_update (0x00440500), and its type-specific collection helpers at
0x00440CF0..0x004413D0.  Conventional item labels are kept separate from the
numeric type IDs; the state mutations and branch order are the facts modeled
here.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace

from th08_rng import Th08Rng


FREE = 0
HOMING = 1
INTERPOLATE = 2
SCATTER_DELAY = 3
SCATTER_TO_HOME = 5

PLAYER_ALIVE = 0
PLAYER_SPAWNING = 1
PLAYER_DYING = 2

ITEM_POWER_SMALL = 0
ITEM_POINT = 1
ITEM_POWER_LARGE = 2
ITEM_BOMB = 3
ITEM_FULL_POWER = 4
ITEM_LIFE_OR_BOMB = 5
ITEM_SCORE_SCALED = 6
ITEM_TIME = 7
ITEM_POWER_OVERFLOW = 8

POWER_LEVEL_THRESHOLDS = (8, 24, 48, 80, 128)
STANDARD_POINT_EXTENDS = (100, 250, 500, 800, 1100, 9999)
EXTRA_POINT_EXTENDS = (200, 666, 9999)


@dataclass(frozen=True)
class ItemState:
    x: float
    y: float
    velocity_x: float
    velocity_y: float
    motion_state: int = FREE
    timer_elapsed: float = 0.0
    item_type: int = ITEM_POWER_SMALL
    full_value: bool = False
    start_x: float | None = None
    start_y: float | None = None
    target_x: float | None = None
    target_y: float | None = None


@dataclass(frozen=True)
class ItemStep:
    item: ItemState
    collection_allowed: bool
    alive: bool = True


@dataclass(frozen=True)
class ItemResources:
    """Solver-relevant fields mutated by item collection.

    ``point_count_2c`` and ``point_count_30`` retain their run-state offsets
    because their broader UI meanings are not yet independently named.
    ``time_units_3c`` and ``time_units_44`` similarly mirror offsets +0x3C
    and +0x44 in the persistent player/run state.
    """

    power: int = 0
    bombs: int = 0
    lives: int = 0
    score_display: int = 0
    point_value: int = 0
    point_count_2c: int = 0
    point_count_30: int = 0
    point_extend_index: int = 0
    time_units_3c: int = 0
    time_units_44: int = 0
    spell_bonus_raw: int = 0


@dataclass(frozen=True)
class ItemCollection:
    resources: ItemResources
    score_value: int = 0
    life_awards: int = 0
    bomb_awards: int = 0
    converted_active_power_items: bool = False
    full_value_earned: bool = False
    power_level_changed: bool = False


def item_collection_overlaps(
    *,
    player_x: float,
    player_y: float,
    player_state: int,
    item_x: float,
    item_y: float,
    collection_width: float,
) -> bool:
    """Match the inclusive AABB test at 0x0044A641..0x0044A693."""

    if collection_width < 0:
        raise ValueError("collection width cannot be negative")
    if player_state not in (0, 3, 4):
        return False
    return (
        abs(item_x - player_x) <= collection_width
        and abs(item_y - player_y) <= collection_width
    )


def item_should_home(
    item: ItemState,
    *,
    player_y: float,
    player_state: int,
    focused: bool,
    power: int,
    route_id: int,
    point_value_line_y: float,
) -> bool:
    """Return the attraction branch selected by item_manager_update."""

    if player_state in (PLAYER_SPAWNING, PLAYER_DYING):
        return False
    if item.motion_state == HOMING:
        return True
    if player_y >= point_value_line_y:
        return False
    if power < 128 and not focused and route_id not in (1, 6):
        return False
    return True


def spawn_item_state(
    *,
    x: float,
    y: float,
    item_type: int,
    motion_state: int,
    power: int,
    player_state: int,
    rng: Th08Rng,
) -> ItemState | None:
    """Apply item_pool_spawn initialization and its exact RNG consumption."""

    if x < -64.0 or x > 448.0:
        return None
    if power >= 128 and item_type in (ITEM_POWER_SMALL, ITEM_POWER_LARGE):
        item_type = ITEM_POWER_OVERFLOW
    if item_type == ITEM_TIME:
        motion_state = SCATTER_DELAY
    elif item_type == 10:
        item_type = ITEM_TIME
        motion_state = SCATTER_TO_HOME

    item = ItemState(
        x=x,
        y=y,
        velocity_x=0.0,
        velocity_y=-2.2,
        motion_state=motion_state,
        item_type=item_type,
        start_x=x,
        start_y=y,
    )
    if motion_state == INTERPOLATE:
        return replace(
            item,
            target_x=rng.next_scaled(288.0) + 48.0,
            target_y=rng.next_scaled(192.0) - 64.0,
        )
    if motion_state in (SCATTER_DELAY, SCATTER_TO_HOME):
        item = replace(
            item,
            velocity_y=-2.0 - rng.next_scaled(0.2),
            velocity_x=rng.next_signed_unit() * 0.6,
        )
        if player_state == PLAYER_DYING:
            item = replace(
                item,
                velocity_x=0.0,
                velocity_y=-0.9,
                motion_state=FREE,
            )
    return item


def _advance_timer(elapsed: float, timer_scale: float) -> float:
    if timer_scale < 0:
        raise ValueError("timer scale cannot be negative")
    return elapsed + (1.0 if timer_scale > 0.99000001 else timer_scale)


def _step_generic_fall(
    item: ItemState,
    *,
    frame_scale: float,
    playfield_bottom_y: float,
) -> ItemStep:
    moved = replace(
        item,
        x=item.x + item.velocity_x * frame_scale,
        y=item.y + item.velocity_y * frame_scale,
    )
    if moved.motion_state == FREE and moved.y >= playfield_bottom_y + 16.0:
        return ItemStep(moved, collection_allowed=False, alive=False)
    return ItemStep(
        replace(moved, velocity_y=min(3.0, moved.velocity_y + 0.03 * frame_scale)),
        collection_allowed=moved.motion_state != SCATTER_DELAY,
    )


def step_item(
    item: ItemState,
    *,
    player_x: float,
    player_y: float,
    player_state: int,
    focused: bool,
    power: int,
    route_id: int,
    point_value_line_y: float,
    homing_speed: float,
    fall_scale: float,
    time_scale: float = 1.0,
    timer_scale: float = 1.0,
    global_scatter_timer_negative: bool = False,
    playfield_bottom_y: float = 448.0,
) -> ItemStep:
    """Advance one item through the exact motion-state branch order.

    The returned state assumes the item was not collected and therefore
    advances its local timer at the end of the frame.
    """

    if item.motion_state not in (FREE, HOMING, INTERPOLATE, SCATTER_DELAY, SCATTER_TO_HOME):
        raise ValueError(f"unsupported item motion state {item.motion_state}")
    if homing_speed < 0 or fall_scale < 0 or time_scale < 0:
        raise ValueError("item speeds/scales cannot be negative")

    frame_scale = fall_scale * time_scale
    current = item

    if current.motion_state == INTERPOLATE:
        if current.start_x is None or current.start_y is None:
            raise ValueError("state 2 requires a start position")
        if current.target_x is None or current.target_y is None:
            raise ValueError("state 2 requires a target position")
        if current.timer_elapsed < 60.0:
            t = current.timer_elapsed / 60.0
            current = replace(
                current,
                x=current.start_x * (1.0 - t) + current.target_x * t,
                y=current.start_y * (1.0 - t) + current.target_y * t,
            )
            result = ItemStep(current, collection_allowed=True)
        else:
            current = replace(
                current,
                velocity_x=0.0,
                velocity_y=0.0,
                motion_state=FREE,
            )
            result = _step_generic_fall(
                current,
                frame_scale=frame_scale,
                playfield_bottom_y=playfield_bottom_y,
            )
    elif current.motion_state == SCATTER_DELAY:
        current = replace(current, velocity_y=current.velocity_y + 0.05 * time_scale)
        if current.velocity_y > 0.0 or global_scatter_timer_negative:
            current = replace(current, motion_state=HOMING)
        if player_state == PLAYER_DYING:
            current = replace(
                current,
                velocity_x=0.0,
                velocity_y=-0.7,
                motion_state=FREE,
            )
        result = _step_generic_fall(
            current,
            frame_scale=frame_scale,
            playfield_bottom_y=playfield_bottom_y,
        )
    elif current.motion_state == SCATTER_TO_HOME:
        current = replace(current, velocity_y=current.velocity_y + 0.05 * time_scale)
        current = replace(
            current,
            x=current.x + current.velocity_x * frame_scale,
            y=current.y + current.velocity_y * frame_scale,
        )
        if current.velocity_y <= 0.0:
            result = ItemStep(current, collection_allowed=False)
        else:
            current = replace(current, motion_state=HOMING)
            if player_state == PLAYER_DYING:
                current = replace(
                    current,
                    velocity_x=0.0,
                    velocity_y=-0.7,
                    motion_state=FREE,
                )
            result = _step_generic_fall(
                current,
                frame_scale=frame_scale,
                playfield_bottom_y=playfield_bottom_y,
            )
    elif item_should_home(
        current,
        player_y=player_y,
        player_state=player_state,
        focused=focused,
        power=power,
        route_id=route_id,
        point_value_line_y=point_value_line_y,
    ):
        dx = player_x - current.x
        dy = player_y - current.y
        length = math.hypot(dx, dy)
        if length:
            velocity_x = homing_speed * dx / length
            velocity_y = homing_speed * dy / length
        else:
            velocity_x = velocity_y = 0.0
        result = ItemStep(
            replace(
                current,
                x=current.x + velocity_x * time_scale,
                y=current.y + velocity_y * time_scale,
                velocity_x=velocity_x,
                velocity_y=velocity_y,
                motion_state=HOMING,
            ),
            collection_allowed=True,
        )
    else:
        velocity_y = current.velocity_y
        if current.motion_state == HOMING and player_state in (PLAYER_SPAWNING, PLAYER_DYING):
            velocity_y = -0.7
        current = replace(
            current,
            velocity_x=0.0,
            velocity_y=max(velocity_y, -2.2),
            motion_state=FREE,
        )
        result = _step_generic_fall(
            current,
            frame_scale=frame_scale,
            playfield_bottom_y=playfield_bottom_y,
        )

    if not result.alive:
        return result
    return replace(
        result,
        item=replace(
            result.item,
            timer_elapsed=_advance_timer(result.item.timer_elapsed, timer_scale),
        ),
    )


def step_standard_item(item: ItemState, **kwargs: object) -> ItemState:
    """Compatibility wrapper for callers that only model states 0 and 1."""

    if item.motion_state not in (FREE, HOMING):
        raise ValueError("only standard item motion states 0 and 1 are accepted")
    return step_item(item, **kwargs).item


def _c_div(value: int, divisor: int) -> int:
    return int(value / divisor)


def _round_to_tens(value: int) -> int:
    return value - (value - _c_div(value, 10) * 10)


def point_item_value(
    *,
    item_y: float,
    point_value_line_y: float,
    base_point_value: int,
    full_value: bool,
    score_double: bool = False,
    overflow_power: bool = False,
) -> tuple[int, int, bool]:
    """Return ``(score, comparison_base, earned_full_value)``.

    The line comparison is strict: an item exactly on the line enters the
    declining-value branch.  Integer conversion and division follow the x86
    signed truncation order used at 0x00440E8C and 0x0044106C.
    """

    if item_y < point_value_line_y:
        value = base_point_value
    else:
        value = _c_div(base_point_value, 2) - int(item_y - point_value_line_y) * _c_div(
            base_point_value, 1000
        )
    if full_value:
        value = base_point_value
    if overflow_power:
        base_point_value = _round_to_tens(_c_div(base_point_value, 10))
        value = _round_to_tens(_c_div(value, 10))
    else:
        value = _round_to_tens(value)
    if score_double:
        value *= 2
    return value, base_point_value, value >= base_point_value


def point_extend_threshold(difficulty_index: int, reward_index: int) -> int:
    if reward_index < 0:
        raise ValueError("reward index cannot be negative")
    if difficulty_index >= 4:
        return EXTRA_POINT_EXTENDS[reward_index] if reward_index < 3 else 99999
    if reward_index < len(STANDARD_POINT_EXTENDS):
        return STANDARD_POINT_EXTENDS[reward_index]
    return 9999 + 500 * (reward_index - 5)


def _award_life_or_bomb(resources: ItemResources) -> tuple[ItemResources, int, int]:
    if resources.lives < 8:
        return replace(resources, lives=resources.lives + 1), 1, 0
    if resources.bombs < 8:
        return replace(resources, bombs=resources.bombs + 1), 0, 1
    return resources, 0, 0


def collect_item(
    item: ItemState,
    resources: ItemResources,
    *,
    difficulty_index: int,
    score_double: bool = False,
    special_score_mode: bool = False,
    stage_counter_0c: int = 0,
    point_value_line_y: float = 128.0,
) -> ItemCollection:
    """Apply the direct solver-relevant mutation for one collected item."""

    item_type = item.item_type
    score_value = 0
    life_awards = 0
    bomb_awards = 0
    convert_power = False
    full_value_earned = False
    power_level_changed = False
    updated = resources

    if item_type in (ITEM_POWER_SMALL, ITEM_POWER_LARGE):
        if updated.power < 128:
            delta = 1 if item_type == ITEM_POWER_SMALL else 8
            old_level = sum(updated.power >= threshold for threshold in POWER_LEVEL_THRESHOLDS)
            updated = replace(updated, power=updated.power + delta)
            new_level = sum(updated.power >= threshold for threshold in POWER_LEVEL_THRESHOLDS)
            convert_power = updated.power >= 128
            score_value = 10
            power_level_changed = new_level != old_level
    elif item_type == ITEM_POINT:
        score_value, _, full_value_earned = point_item_value(
            item_y=item.y,
            point_value_line_y=point_value_line_y,
            base_point_value=updated.point_value,
            full_value=item.full_value,
            score_double=score_double,
        )
        updated = replace(
            updated,
            point_count_2c=updated.point_count_2c + 1,
            point_count_30=updated.point_count_30 + 1,
        )
        while updated.point_count_30 >= point_extend_threshold(
            difficulty_index, updated.point_extend_index
        ):
            updated, lives, bombs = _award_life_or_bomb(updated)
            life_awards += lives
            bomb_awards += bombs
            updated = replace(updated, point_extend_index=updated.point_extend_index + 1)
    elif item_type == ITEM_BOMB:
        if updated.bombs < 8:
            updated = replace(updated, bombs=updated.bombs + 1)
            bomb_awards = 1
    elif item_type == ITEM_FULL_POWER:
        if updated.power < 128:
            updated = replace(updated, power=128)
            convert_power = True
        score_value = 1000
    elif item_type == ITEM_LIFE_OR_BOMB:
        updated, life_awards, bomb_awards = _award_life_or_bomb(updated)
    elif item_type == ITEM_SCORE_SCALED:
        score_value = 100 if special_score_mode else 10 * _c_div(stage_counter_0c, 40) + 300
        if score_value <= 0:
            score_value = 10
    elif item_type == ITEM_TIME:
        if special_score_mode:
            score_value = 100
        elif updated.point_count_2c < 2000:
            score_value = max(100, 10 * _c_div(updated.point_count_30, 2))
        else:
            score_value = 10000
        new_time_44 = updated.time_units_44 + 1
        point_delta = 10 if new_time_44 & 1 else 0
        updated = replace(
            updated,
            point_value=updated.point_value + point_delta,
            time_units_3c=updated.time_units_3c + 1,
            time_units_44=new_time_44,
            spell_bonus_raw=updated.spell_bonus_raw + 8000,
        )
    elif item_type == ITEM_POWER_OVERFLOW:
        score_value, _, full_value_earned = point_item_value(
            item_y=item.y,
            point_value_line_y=point_value_line_y,
            base_point_value=updated.point_value,
            full_value=item.full_value,
            score_double=score_double,
            overflow_power=True,
        )

    updated = replace(updated, score_display=updated.score_display + score_value)
    return ItemCollection(
        resources=updated,
        score_value=score_value,
        life_awards=life_awards,
        bomb_awards=bomb_awards,
        converted_active_power_items=convert_power,
        full_value_earned=full_value_earned,
        power_level_changed=power_level_changed,
    )
