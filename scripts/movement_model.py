#!/usr/bin/env python3
"""Game-independent axis-aligned player movement primitives."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

from numeric_model import StoreQuantizer, identity_store


class Direction(Enum):
    NEUTRAL = (0, 0)
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)
    UP_LEFT = (-1, -1)
    UP_RIGHT = (1, -1)
    DOWN_LEFT = (-1, 1)
    DOWN_RIGHT = (1, 1)

    @property
    def axes(self) -> tuple[int, int]:
        return self.value


@dataclass(frozen=True)
class MovementProfile:
    unfocused_cardinal: float
    focused_cardinal: float
    unfocused_diagonal_axis: float
    focused_diagonal_axis: float


@dataclass(frozen=True)
class MovementBounds:
    left: float
    top: float
    right: float
    bottom: float

    def __post_init__(self) -> None:
        if self.left > self.right or self.top > self.bottom:
            raise ValueError("movement bounds must be ordered")


@dataclass(frozen=True)
class MovementStep:
    x: float
    y: float
    velocity_x: float
    velocity_y: float
    clamped_x: bool
    clamped_y: bool


def step_axis_aligned_movement(
    *,
    x: float,
    y: float,
    direction: Direction,
    focused: bool,
    profile: MovementProfile,
    bounds: MovementBounds,
    axis_scale_x: float = 1.0,
    axis_scale_y: float = 1.0,
    time_scale: float = 1.0,
    store: StoreQuantizer = identity_store,
) -> MovementStep:
    """Apply one profile-driven movement and clamp pass.

    ``store`` models target-side memory rounding at the three native write
    boundaries: scaled velocity, time-scaled delta, and position.
    """

    numbers = (
        x,
        y,
        axis_scale_x,
        axis_scale_y,
        time_scale,
        profile.unfocused_cardinal,
        profile.focused_cardinal,
        profile.unfocused_diagonal_axis,
        profile.focused_diagonal_axis,
    )
    if not all(math.isfinite(value) for value in numbers):
        raise ValueError("movement values must be finite")
    if min(numbers[2:]) < 0.0:
        raise ValueError("movement scales and speeds must be non-negative")

    axis_x, axis_y = direction.axes
    diagonal = axis_x != 0 and axis_y != 0
    if diagonal:
        speed = (
            profile.focused_diagonal_axis
            if focused
            else profile.unfocused_diagonal_axis
        )
    else:
        speed = profile.focused_cardinal if focused else profile.unfocused_cardinal

    scaled_x = store(axis_x * speed * axis_scale_x)
    scaled_y = store(axis_y * speed * axis_scale_y)
    velocity_x = store(scaled_x * time_scale)
    velocity_y = store(scaled_y * time_scale)
    raw_x = store(x + velocity_x)
    raw_y = store(y + velocity_y)
    next_x = min(max(raw_x, bounds.left), bounds.right)
    next_y = min(max(raw_y, bounds.top), bounds.bottom)
    return MovementStep(
        x=next_x,
        y=next_y,
        velocity_x=velocity_x,
        velocity_y=velocity_y,
        clamped_x=next_x != raw_x,
        clamped_y=next_y != raw_y,
    )
