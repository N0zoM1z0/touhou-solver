#!/usr/bin/env python3
"""TH08 input adapter for the reusable movement primitive."""

from __future__ import annotations

from movement_model import (
    Direction,
    MovementBounds,
    MovementProfile,
    MovementStep,
    step_axis_aligned_movement,
)
from numeric_model import binary32_store
from th08_sht import ShtHeader


INPUT_SHOT = 0x01
INPUT_BOMB = 0x02
INPUT_FOCUS = 0x04
INPUT_UP = 0x10
INPUT_DOWN = 0x20
INPUT_LEFT = 0x40
INPUT_RIGHT = 0x80

TH08_PLAYFIELD_BOUNDS = MovementBounds(0.0, 0.0, 384.0, 448.0)
ROUTE2_MOVEMENT_PROFILE = MovementProfile(
    unfocused_cardinal=4.0,
    focused_cardinal=2.299999952316284,
    unfocused_diagonal_axis=2.8284270763397217,
    focused_diagonal_axis=1.6263456344604492,
)


def movement_profile_from_sht(
    primary: ShtHeader, secondary: ShtHeader
) -> MovementProfile:
    """Build the profile selected by TH08's primary/secondary SHT pointers."""

    return MovementProfile(
        unfocused_cardinal=primary.unfocused_cardinal_speed,
        focused_cardinal=secondary.focused_cardinal_speed,
        unfocused_diagonal_axis=primary.unfocused_diagonal_axis_speed,
        focused_diagonal_axis=secondary.focused_diagonal_axis_speed,
    )


def decode_th08_direction(input_mask: int) -> Direction:
    """Match the ordered direction tests at 0x0044AEF5..0x0044AFF0."""

    input_mask &= 0xFFFF
    if input_mask & (INPUT_UP | INPUT_LEFT) == INPUT_UP | INPUT_LEFT:
        return Direction.UP_LEFT
    if input_mask & (INPUT_DOWN | INPUT_LEFT) == INPUT_DOWN | INPUT_LEFT:
        return Direction.DOWN_LEFT
    if input_mask & (INPUT_UP | INPUT_RIGHT) == INPUT_UP | INPUT_RIGHT:
        return Direction.UP_RIGHT
    if input_mask & (INPUT_DOWN | INPUT_RIGHT) == INPUT_DOWN | INPUT_RIGHT:
        return Direction.DOWN_RIGHT
    if input_mask & INPUT_DOWN:
        return Direction.DOWN
    if input_mask & INPUT_UP:
        return Direction.UP
    if input_mask & INPUT_LEFT:
        return Direction.LEFT
    if input_mask & INPUT_RIGHT:
        return Direction.RIGHT
    return Direction.NEUTRAL


def route2_effective_focus(
    input_mask: int, *, bomb_active: bool, bomb_callback_index: int = 0
) -> bool:
    """Apply the active-Bomb focus override used by player movement/SHT."""

    if bomb_callback_index < 0:
        raise ValueError("bomb callback index cannot be negative")
    if bomb_active:
        return bool(bomb_callback_index & 1)
    return bool(input_mask & INPUT_FOCUS)


def step_route2_movement(
    *,
    x: float,
    y: float,
    input_mask: int,
    bomb_active: bool = False,
    bomb_callback_index: int = 0,
    axis_scale_x: float = 1.0,
    axis_scale_y: float = 1.0,
    time_scale: float = 1.0,
    bounds: MovementBounds = TH08_PLAYFIELD_BOUNDS,
    profile: MovementProfile = ROUTE2_MOVEMENT_PROFILE,
) -> MovementStep:
    return step_axis_aligned_movement(
        x=x,
        y=y,
        direction=decode_th08_direction(input_mask),
        focused=route2_effective_focus(
            input_mask,
            bomb_active=bomb_active,
            bomb_callback_index=bomb_callback_index,
        ),
        profile=profile,
        bounds=bounds,
        axis_scale_x=axis_scale_x,
        axis_scale_y=axis_scale_y,
        time_scale=time_scale,
        store=binary32_store,
    )
