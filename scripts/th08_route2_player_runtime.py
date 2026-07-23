#!/usr/bin/env python3
"""Frame-executable TH08 route-2 player movement and Bomb runtime.

This adapter covers the priority-9 state/focus/movement path needed to project
replay controls. Hostile collision and item pickup are later schedule phases;
callers must supply accepted Bomb starts explicitly until those systems drive
the same state in the integrated simulator.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from enum import Enum, IntEnum

from movement_model import MovementBounds
from th08_movement_model import (
    INPUT_BOMB,
    TH08_PLAYFIELD_BOUNDS,
    route2_effective_focus,
    step_route2_movement,
)
from th08_option_model import (
    Route2FocusState,
    initial_route2_focus_state,
    step_route2_focus,
)
from th08_player_model import BombIndex, BombProfile, ROUTE2_BOMBS


class PlayerPhase(IntEnum):
    NORMAL = 0
    SPAWNING = 1
    DEAD = 2
    INVULNERABLE = 3


class BombStartKind(Enum):
    NORMAL = "normal"
    DEATHBOMB = "deathbomb"
    FORCED_DISSOLVE = "forced_dissolve"


@dataclass(frozen=True)
class Route2BombState:
    profile: BombProfile
    timer_elapsed: int = 0
    timer_fraction: float = 0.0


@dataclass(frozen=True)
class Route2PlayerState:
    frame_index: int
    x: float
    y: float
    z: float
    phase: PlayerPhase
    state_timer_elapsed: int
    state_timer_fraction: float
    bombs: int
    focus: Route2FocusState
    bomb: Route2BombState | None = None
    axis_scale_x: float = 1.0
    axis_scale_y: float = 1.0
    short_spawn_mode: bool = False
    previous_input_mask: int = 0


@dataclass(frozen=True)
class Route2PlayerStep:
    state: Route2PlayerState
    effective_focus: bool
    movement_applied: bool
    bomb_started: BombProfile | None
    bomb_ended: BombProfile | None


def _advance_timer(
    elapsed: int, fraction: float, time_scale: float
) -> tuple[int, float]:
    if time_scale > 0.99000001:
        return elapsed + 1, fraction
    fraction += time_scale
    while fraction >= 1.0:
        elapsed += 1
        fraction -= 1.0
    return elapsed, fraction


def _decrement_timer(
    elapsed: int, fraction: float, time_scale: float
) -> tuple[int, float]:
    if time_scale > 0.99000001:
        return elapsed - 1, fraction
    fraction -= time_scale
    while fraction < 0.0:
        elapsed -= 1
        fraction += 1.0
    return elapsed, fraction


def initial_route2_player_state(
    *,
    bombs: int = 3,
    short_spawn_mode: bool = False,
    playfield_width: float = 384.0,
    playfield_height: float = 448.0,
) -> Route2PlayerState:
    """Return fields written by player_initialize_resources at 0x44D650."""

    if bombs < 0:
        raise ValueError("bomb stock cannot be negative")
    if playfield_width < 0.0 or playfield_height < 64.0:
        raise ValueError("playfield dimensions cannot form the native spawn point")
    return Route2PlayerState(
        frame_index=0,
        x=playfield_width / 2.0,
        y=playfield_height - 64.0,
        z=0.49000000953674316,
        phase=PlayerPhase.SPAWNING,
        state_timer_elapsed=10 if short_spawn_mode else 120,
        state_timer_fraction=0.0,
        bombs=bombs,
        focus=initial_route2_focus_state(),
        short_spawn_mode=short_spawn_mode,
    )


def _native_route2_bomb_index(
    focus_logic_value: int, kind: BombStartKind
) -> BombIndex:
    if kind is BombStartKind.FORCED_DISSOLVE:
        return BombIndex.DISSOLVE_SPELL
    index = focus_logic_value
    if kind is BombStartKind.DEATHBOMB:
        index = 1 - index + 2
    try:
        return BombIndex(index)
    except ValueError as exc:
        raise ValueError(
            f"focus byte {focus_logic_value} selects invalid route-2 Bomb index {index}"
        ) from exc


def _bomb_cost(kind: BombStartKind, stock: int) -> int:
    if kind is BombStartKind.FORCED_DISSOLVE:
        return 0
    if stock <= 0:
        raise ValueError("accepted Bomb start requires positive stock")
    return min(stock, 2) if kind is BombStartKind.DEATHBOMB else 1


def _bomb_axis_scale(index: BombIndex, timer_elapsed: int) -> float:
    if index in (BombIndex.SAKUYA_NORMAL, BombIndex.SAKUYA_LAST_SPELL):
        return 0.5
    if index is BombIndex.REMILIA_NORMAL:
        return 0.0 if timer_elapsed < 60 else 2.0
    if index is BombIndex.REMILIA_LAST_SPELL:
        return 0.0 if timer_elapsed < 60 else 3.0
    return 0.0


def _step_bomb_before_movement(
    state: Route2PlayerState,
    *,
    bomb_start: BombStartKind | None,
    time_scale: float,
) -> tuple[Route2PlayerState, BombProfile | None, BombProfile | None]:
    """Run the Bomb branch and callback before player state/movement."""

    current = state
    started = None
    ended = None
    if current.bomb is not None:
        bomb = current.bomb
        if bomb.timer_elapsed >= bomb.profile.duration_frames:
            ended = bomb.profile
            current = replace(
                current,
                bomb=None,
                axis_scale_x=1.0,
                axis_scale_y=1.0,
            )
        else:
            scale = _bomb_axis_scale(bomb.profile.index, bomb.timer_elapsed)
            elapsed, fraction = _advance_timer(
                bomb.timer_elapsed, bomb.timer_fraction, time_scale
            )
            current = replace(
                current,
                bomb=replace(
                    bomb, timer_elapsed=elapsed, timer_fraction=fraction
                ),
                axis_scale_x=scale,
                axis_scale_y=scale,
            )
        return current, started, ended

    if bomb_start is None:
        return current, started, ended

    index = _native_route2_bomb_index(current.focus.focus_logic_value, bomb_start)
    profile = ROUTE2_BOMBS[index]
    cost = _bomb_cost(bomb_start, current.bombs)
    scale = _bomb_axis_scale(index, 0)
    elapsed, fraction = _advance_timer(0, 0.0, time_scale)
    current = replace(
        current,
        phase=PlayerPhase.INVULNERABLE,
        state_timer_elapsed=profile.duration_frames,
        state_timer_fraction=0.0,
        bombs=current.bombs - cost,
        bomb=Route2BombState(profile, elapsed, fraction),
        axis_scale_x=scale,
        axis_scale_y=scale,
    )
    return current, profile, ended


def _step_player_phase(
    state: Route2PlayerState, *, time_scale: float
) -> Route2PlayerState:
    current = state
    if current.phase is PlayerPhase.SPAWNING and current.state_timer_elapsed >= 30:
        current = replace(
            current,
            phase=PlayerPhase.INVULNERABLE,
            state_timer_elapsed=(30 if current.short_spawn_mode else 240),
            state_timer_fraction=0.0,
        )

    if current.phase is PlayerPhase.INVULNERABLE:
        elapsed, fraction = _decrement_timer(
            current.state_timer_elapsed,
            current.state_timer_fraction,
            time_scale,
        )
        if elapsed <= 0:
            return replace(
                current,
                phase=PlayerPhase.NORMAL,
                state_timer_elapsed=0,
                state_timer_fraction=0.0,
            )
        return replace(
            current,
            state_timer_elapsed=elapsed,
            state_timer_fraction=fraction,
        )

    if current.phase is PlayerPhase.DEAD:
        if current.state_timer_elapsed <= 0:
            return replace(
                current,
                state_timer_elapsed=0,
                state_timer_fraction=0.0,
            )
        elapsed, fraction = _decrement_timer(
            current.state_timer_elapsed,
            current.state_timer_fraction,
            time_scale,
        )
        return replace(
            current,
            state_timer_elapsed=max(elapsed, 0),
            state_timer_fraction=fraction if elapsed > 0 else 0.0,
        )

    elapsed, fraction = _advance_timer(
        current.state_timer_elapsed,
        current.state_timer_fraction,
        time_scale,
    )
    return replace(
        current,
        state_timer_elapsed=elapsed,
        state_timer_fraction=fraction,
    )


def step_route2_player(
    state: Route2PlayerState,
    *,
    input_mask: int,
    bomb_start: BombStartKind | None = None,
    time_scale: float = 1.0,
    bounds: MovementBounds = TH08_PLAYFIELD_BOUNDS,
) -> Route2PlayerStep:
    """Execute the recovered priority-9 state/focus/movement subset once.

    ``bomb_start`` means the native gate accepted the current Bomb input. It is
    explicit because replay input alone cannot distinguish a normal Bomb from
    a hit-triggered Last Spell, nor prove that item pickups replenished stock.
    """

    if not math.isfinite(time_scale) or time_scale < 0.0:
        raise ValueError("time scale must be finite and non-negative")
    input_mask &= 0xFFFF
    if bomb_start is not None and not input_mask & INPUT_BOMB:
        raise ValueError("an accepted Bomb start requires Bomb input this frame")

    current, started, ended = _step_bomb_before_movement(
        state,
        bomb_start=bomb_start,
        time_scale=time_scale,
    )
    current = _step_player_phase(current, time_scale=time_scale)

    bomb_active = current.bomb is not None
    bomb_index = int(current.bomb.profile.index) if bomb_active else 0
    effective_focus = route2_effective_focus(
        input_mask,
        bomb_active=bomb_active,
        bomb_callback_index=bomb_index,
    )
    movement_applied = current.phase not in (
        PlayerPhase.SPAWNING,
        PlayerPhase.DEAD,
    )
    if movement_applied:
        movement = step_route2_movement(
            x=current.x,
            y=current.y,
            input_mask=input_mask,
            bomb_active=bomb_active,
            bomb_callback_index=bomb_index,
            axis_scale_x=current.axis_scale_x,
            axis_scale_y=current.axis_scale_y,
            time_scale=time_scale,
            bounds=bounds,
        )
        current = replace(current, x=movement.x, y=movement.y)
        focus = step_route2_focus(
            current.focus,
            focused=effective_focus,
            post_movement_player_x=current.x,
            post_movement_player_y=current.y,
            post_movement_player_z=current.z,
            time_scale=time_scale,
        )
        current = replace(current, focus=focus)

    current = replace(
        current,
        frame_index=current.frame_index + 1,
        previous_input_mask=input_mask,
    )
    return Route2PlayerStep(
        state=current,
        effective_focus=effective_focus,
        movement_applied=movement_applied,
        bomb_started=started,
        bomb_ended=ended,
    )
