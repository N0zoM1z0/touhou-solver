#!/usr/bin/env python3
"""Executable route-2 focus transition and option-position model.

The four route-2 option slots share update callback 0x0044EB70.  Focus-edge
allocation occurs early in player_update_input_movement; this callback runs
after player movement in the same function and therefore captures the
post-movement player position as its fixed orbit target.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace


OPTION_INACTIVE = 0
OPTION_ENTER = 1
OPTION_ACTIVE = 2
OPTION_EXIT = 3
OPTION_COUNT = 4
OPTION_ORBIT_RADIUS = 8.0

_TARGET_OFFSETS = (
    (-30.0, -16.0),
    (-10.0, -32.0),
    (10.0, -32.0),
    (30.0, -16.0),
)
_INITIAL_ANGLES = (0.0, math.pi, 0.0, math.pi)
_ANGLE_DELTAS = (
    math.radians(1.5),
    math.radians(-2.0),
    math.radians(2.0),
    math.radians(-1.5),
)


@dataclass(frozen=True)
class Route2Option:
    index: int
    state: int = OPTION_INACTIVE
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    target_x: float = 0.0
    target_y: float = 0.0
    target_z: float = 0.0
    angle: float = 0.0
    timer_elapsed: int = 0
    timer_fraction: float = 0.0


def inactive_route2_options() -> tuple[Route2Option, ...]:
    return tuple(Route2Option(index) for index in range(OPTION_COUNT))


@dataclass(frozen=True)
class Route2FocusState:
    """Player fields +3, +5, +8 and the four 0x2F4-byte option slots."""

    focus_logic_value: int = 0
    remilia_character_active: bool = False
    transition_counter: int = 0
    options: tuple[Route2Option, ...] = field(
        default_factory=inactive_route2_options
    )

    def __post_init__(self) -> None:
        if not 0 <= self.focus_logic_value <= 0xFF:
            raise ValueError("focus logic byte must fit in one unsigned byte")
        if len(self.options) != OPTION_COUNT:
            raise ValueError("route 2 requires exactly four option slots")

    @property
    def focus_logic_active(self) -> bool:
        return self.focus_logic_value != 0


def initial_route2_focus_state() -> Route2FocusState:
    """Return the state written by player_initialize_resources.

    The native initializer uses the non-boolean sentinel value 2 and creates
    all four option callbacks in enter state. The first movement callback
    normalizes the byte to 0 or 1 from effective focus.
    """

    return Route2FocusState(
        focus_logic_value=2,
        options=tuple(
            Route2Option(index=index, state=OPTION_ENTER)
            for index in range(OPTION_COUNT)
        ),
    )


def _normalize_angle(angle: float) -> float:
    while angle > math.pi:
        angle -= math.tau
    while angle < -math.pi:
        angle += math.tau
    return angle


def _advance_timer(
    elapsed: int, fraction: float, time_scale: float
) -> tuple[int, float]:
    if time_scale < 0.0 or not math.isfinite(time_scale):
        raise ValueError("time scale must be finite and non-negative")
    if time_scale > 0.99000001:
        return elapsed + 1, fraction
    fraction += time_scale
    if fraction >= 1.0:
        return elapsed + 1, fraction - 1.0
    return elapsed, fraction


def step_route2_option(
    option: Route2Option,
    *,
    player_x: float,
    player_y: float,
    player_z: float = 0.0,
    time_scale: float = 1.0,
) -> Route2Option:
    """Run 0x0044EB70 and the caller's following timer advance once."""

    if not 0 <= option.index < OPTION_COUNT:
        raise ValueError("option index must be in [0, 4)")

    current = option
    if current.state == OPTION_ENTER:
        offset_x, offset_y = _TARGET_OFFSETS[current.index]
        current = replace(
            current,
            state=OPTION_ACTIVE,
            target_x=player_x + offset_x,
            target_y=player_y + offset_y,
            target_z=player_z,
            angle=_INITIAL_ANGLES[current.index],
        )

    if current.state == OPTION_ACTIVE:
        angle = current.angle
        if current.timer_elapsed > 12:
            angle = _normalize_angle(angle + _ANGLE_DELTAS[current.index])
        current = replace(
            current,
            x=current.target_x + math.cos(angle) * OPTION_ORBIT_RADIUS,
            y=current.target_y + math.sin(angle) * OPTION_ORBIT_RADIUS,
            z=current.target_z,
            angle=angle,
        )
    elif current.state == OPTION_EXIT and current.timer_elapsed > 16:
        current = replace(current, state=OPTION_INACTIVE, x=0.0, y=0.0)

    elapsed, fraction = _advance_timer(
        current.timer_elapsed, current.timer_fraction, time_scale
    )
    return replace(current, timer_elapsed=elapsed, timer_fraction=fraction)


def step_route2_focus(
    state: Route2FocusState,
    *,
    focused: bool,
    post_movement_player_x: float,
    post_movement_player_y: float,
    post_movement_player_z: float = 0.0,
    time_scale: float = 1.0,
) -> Route2FocusState:
    """Apply route-2 focus edges, option callbacks, and transition counters."""

    options = state.options
    counter = state.transition_counter
    remilia_active = state.remilia_character_active

    if focused:
        if state.focus_logic_value == 1:
            counter += 1
        else:
            options = tuple(
                Route2Option(index=index, state=OPTION_ENTER)
                for index in range(OPTION_COUNT)
            )
            counter = 0
        if counter >= 7:
            remilia_active = True
        focus_logic_value = 1
    else:
        if state.focus_logic_active:
            options = tuple(
                replace(option, state=OPTION_EXIT, timer_elapsed=0, timer_fraction=0.0)
                if option.state not in (OPTION_INACTIVE, OPTION_EXIT)
                else option
                for option in options
            )
            counter = 0
        else:
            counter += 1
        if counter >= 7:
            remilia_active = False
        focus_logic_value = 0

    stepped = tuple(
        step_route2_option(
            option,
            player_x=post_movement_player_x,
            player_y=post_movement_player_y,
            player_z=post_movement_player_z,
            time_scale=time_scale,
        )
        for option in options
    )
    return Route2FocusState(
        focus_logic_value=focus_logic_value,
        remilia_character_active=remilia_active,
        transition_counter=counter,
        options=stepped,
    )


def route2_option_shot_positions(
    state: Route2FocusState,
) -> dict[int, tuple[float, float]]:
    """Return the source-index mapping consumed by default SHT shot spawn."""

    return {
        option.index + 1: (option.x, option.y)
        for option in state.options
        if option.state == OPTION_ACTIVE
    }
