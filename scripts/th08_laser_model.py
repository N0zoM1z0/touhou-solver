#!/usr/bin/env python3
"""Executable TH08 laser motion, phase, collision, and graze geometry.

The 0x59C-byte runtime record is allocated by laser_pool_spawn (0x00430F20)
and advanced in the laser loop inside bullet_manager_update (0x00431B7A).
The rotated-rectangle player test is player_test_collision_and_graze
(0x0044A6A0).

The model retains every native lifecycle field used by the collision branches,
including the flag-selected alpha/width ramp and the two fallthrough calls.
"""

from __future__ import annotations

import math
import struct
from dataclasses import dataclass, replace
from enum import IntEnum
from functools import lru_cache

from numeric_model import binary32_store
from th08_ecl_vm_state import float32_bits, float32_from_bits
from th08_native_timer import Th08TimerState, advance_scaled_timer
from th08_time_scale import (
    TH08_PLAYER_LASER_SCALE_SEMANTICS_VERSION,
    TH08_UNIT_TIME_SCALE_BITS,
    canonical_time_scale_bits,
    validate_time_scale_bits,
)


LASER_POOL_SIZE = 256
LASER_RECORD_SIZE = 0x59C
LASER_GRAZE_EXPANSION = 48.0
LASER_GRAZE_PERIOD = 20
LASER_TAIL_CULL_DISTANCE = 640.0
TH08_LASER_SCALE_SEMANTICS_VERSION = (
    f"{TH08_PLAYER_LASER_SCALE_SEMANTICS_VERSION}:laser-lifecycle"
)


class LaserPhase(IntEnum):
    WARMUP = 0
    ACTIVE = 1
    FADE = 2


@dataclass(frozen=True)
class LaserState:
    origin_x: float
    origin_y: float
    angle: float
    tail_distance: float
    head_distance: float
    maximum_length: float
    width: float
    speed: float
    warmup_frames: int
    active_frames: int
    fade_frames: int
    collision_enable_frame: int
    collision_disable_frame: int
    flags: int = 0
    current_width: float = 0.0
    phase: LaserPhase = LaserPhase.WARMUP
    timer: int = 0
    timer_fraction: float = 0.0
    active: bool = True

    @property
    def timer_fraction_bits(self) -> int:
        return float32_bits(self.timer_fraction)

    @property
    def serialized_scale_identity(self) -> tuple[object, ...]:
        return (
            TH08_LASER_SCALE_SEMANTICS_VERSION,
            float32_bits(self.tail_distance),
            float32_bits(self.head_distance),
            float32_bits(self.current_width),
            int(self.phase),
            self.timer,
            self.timer_fraction_bits,
            self.active,
        )


@dataclass(frozen=True)
class LaserCollisionBox:
    center_x: float
    center_y: float
    width: float
    height: float
    angle: float
    pivot_x: float
    pivot_y: float


@dataclass(frozen=True)
class LaserCollisionCheck:
    graze_enabled: bool
    phase: LaserPhase
    collision_box: LaserCollisionBox


@dataclass(frozen=True)
class LaserStepResult:
    laser: LaserState
    collision_box: LaserCollisionBox
    checks: tuple[LaserCollisionCheck, ...]


@lru_cache(maxsize=2048)
def _cached_collision_geometry_frames(
    laser: LaserState,
    frame_count: int,
    constant_time_scale_bits: int = TH08_UNIT_TIME_SCALE_BITS,
    time_scale_schedule_bits: tuple[int, ...] = (),
) -> tuple[tuple[tuple[float, float, float], ...], ...]:
    validate_time_scale_bits(constant_time_scale_bits)
    if time_scale_schedule_bits and len(time_scale_schedule_bits) < frame_count:
        raise ValueError("laser time-scale schedule does not cover frame count")
    frames: list[tuple[tuple[float, float, float], ...]] = []
    state = laser
    for frame in range(frame_count):
        result = step_laser(
            state,
            time_scale_bits=(
                time_scale_schedule_bits[frame]
                if time_scale_schedule_bits
                else constant_time_scale_bits
            ),
        )
        state = result.laser
        seen: set[tuple[float, float, float]] = set()
        geometry: list[tuple[float, float, float]] = []
        for check in result.checks:
            box = check.collision_box
            center_distance = box.center_x - state.origin_x
            half_length = box.width / 2.0
            segment = (
                center_distance - half_length,
                center_distance + half_length,
                box.height / 2.0,
            )
            if segment not in seen:
                seen.add(segment)
                geometry.append(segment)
        frames.append(tuple(geometry))
    return tuple(frames)


def laser_collision_geometry_frames(
    laser: LaserState,
    *,
    frame_count: int,
    time_scale_bits: int = TH08_UNIT_TIME_SCALE_BITS,
    time_scale_schedule_bits: tuple[int, ...] = (),
) -> tuple[tuple[tuple[float, float, float], ...], ...]:
    """Project collision geometry while sharing translated/rotated templates."""

    if frame_count < 0:
        raise ValueError("laser projection frame count cannot be negative")
    validate_time_scale_bits(time_scale_bits)
    if time_scale_schedule_bits:
        if len(time_scale_schedule_bits) < frame_count:
            raise ValueError(
                "laser time-scale schedule does not cover projection horizon"
            )
        for bits in time_scale_schedule_bits[:frame_count]:
            validate_time_scale_bits(bits)
    normalized = replace(
        laser,
        origin_x=0.0,
        origin_y=0.0,
        angle=0.0,
    )
    return _cached_collision_geometry_frames(
        normalized,
        frame_count,
        time_scale_bits,
        time_scale_schedule_bits[:frame_count],
    )


def spawn_laser_state(
    *,
    origin_x: float,
    origin_y: float,
    angle: float,
    speed: float,
    tail_distance: float,
    head_distance: float,
    maximum_length: float,
    width: float,
    warmup_frames: int,
    active_frames: int,
    fade_frames: int,
    collision_enable_frame: int,
    collision_disable_frame: int,
    flags: int = 0,
) -> LaserState:
    """Construct the runtime state initialized by 0x00430F20."""

    if maximum_length < 0.0 or width < 0.0:
        raise ValueError("laser maximum length and width cannot be negative")
    if min(
        warmup_frames,
        active_frames,
        fade_frames,
        collision_enable_frame,
        collision_disable_frame,
    ) < 0:
        raise ValueError("laser phase thresholds cannot be negative")
    phase = LaserPhase.WARMUP if warmup_frames else LaserPhase.ACTIVE
    return LaserState(
        origin_x=origin_x,
        origin_y=origin_y,
        angle=angle,
        tail_distance=tail_distance,
        head_distance=head_distance,
        maximum_length=maximum_length,
        width=width,
        speed=speed,
        warmup_frames=warmup_frames,
        active_frames=active_frames,
        fade_frames=fade_frames,
        collision_enable_frame=collision_enable_frame,
        collision_disable_frame=collision_disable_frame,
        flags=flags,
        current_width=width if not warmup_frames else 1.2,
        phase=phase,
    )


def laser_collision_box(
    laser: LaserState,
    *,
    longitudinal_size: float | None = None,
) -> LaserCollisionBox:
    """Build the laser-local rectangle passed to ``0x0044A6A0``."""

    visible_length = laser.head_distance - laser.tail_distance
    collision_length = visible_length * (0.7 if laser.tail_distance > 0.0 else 1.0)
    if longitudinal_size is not None:
        collision_length = longitudinal_size
    return LaserCollisionBox(
        center_x=laser.origin_x
        + laser.tail_distance
        + visible_length / 2.0,
        center_y=laser.origin_y,
        width=collision_length,
        height=laser.width / 2.0,
        angle=laser.angle,
        pivot_x=laser.origin_x,
        pivot_y=laser.origin_y,
    )


def _player_in_laser_local(
    box: LaserCollisionBox, player_x: float, player_y: float
) -> tuple[float, float]:
    dx = player_x - box.pivot_x
    dy = player_y - box.pivot_y
    cosine = math.cos(-box.angle)
    sine = math.sin(-box.angle)
    return (
        box.pivot_x + cosine * dx - sine * dy,
        box.pivot_y + sine * dx + cosine * dy,
    )


def laser_overlaps_player(
    box: LaserCollisionBox,
    *,
    player_x: float,
    player_y: float,
    player_half_width: float,
    player_half_height: float,
    graze: bool = False,
) -> bool:
    """Match the inclusive transformed-player AABB test at 0x0044A7EB."""

    if player_half_width < 0.0 or player_half_height < 0.0:
        raise ValueError("player half extents cannot be negative")
    local_x, local_y = _player_in_laser_local(box, player_x, player_y)
    expansion = LASER_GRAZE_EXPANSION if graze else 0.0
    return (
        local_x - player_half_width <= box.center_x + box.width / 2.0 + expansion
        and local_x + player_half_width >= box.center_x - box.width / 2.0 - expansion
        and local_y - player_half_height <= box.center_y + box.height / 2.0 + expansion
        and local_y + player_half_height >= box.center_y - box.height / 2.0 - expansion
    )


def _advance_timer(
    timer: int,
    fraction: float,
    *,
    time_scale_bits: int,
) -> tuple[int, float]:
    """Delegate to the revalidated native timer component recurrence."""

    advanced = advance_scaled_timer(
        Th08TimerState(timer, float32_bits(fraction)),
        time_scale_bits=time_scale_bits,
    )
    return advanced.elapsed, advanced.fraction


def _stored_float32(value: float, *, field: str) -> float:
    try:
        stored = binary32_store(value)
    except (OverflowError, struct.error) as exc:
        raise ValueError(f"{field} is outside finite float32") from exc
    if not math.isfinite(stored):
        raise ValueError(f"{field} became non-finite")
    return stored


def step_laser(
    laser: LaserState,
    *,
    time_scale: float = 1.0,
    time_scale_bits: int | None = None,
) -> LaserStepResult:
    """Advance one manager call and list collision calls in execution order.

    Phase transitions intentionally fall through: the last warmup update also
    executes the active collision branch, and the last active update can also
    execute the fade collision branch.
    """

    if time_scale_bits is None:
        time_scale_bits = canonical_time_scale_bits(time_scale)
    elif time_scale != 1.0:
        raise ValueError(
            "specify either time_scale or time_scale_bits, not both"
        )
    time_scale = validate_time_scale_bits(time_scale_bits)
    if not laser.active:
        return LaserStepResult(laser, laser_collision_box(laser), ())

    # 0x431BC9..0x431BE1 performs the multiply/add on x87 and stores only the
    # final head field to dword.
    head = _stored_float32(
        laser.head_distance + laser.speed * time_scale,
        field="laser head",
    )
    tail = laser.tail_distance
    if head - tail > laser.maximum_length:
        tail = _stored_float32(
            head - laser.maximum_length,
            field="laser tail",
        )
    if tail < 0.0:
        tail = 0.0
    current = replace(laser, head_distance=head, tail_distance=tail)
    box = laser_collision_box(current)
    checks: list[LaserCollisionCheck] = []

    if current.phase == LaserPhase.WARMUP:
        if current.flags & 1:
            phase_box = box
        else:
            ramp_frames = min(current.warmup_frames, 30)
            ramp_start = current.warmup_frames - ramp_frames
            if ramp_start >= current.timer:
                current_width = float32_from_bits(0x3F99999A)
            elif current.warmup_frames:
                current_width = _stored_float32(
                    (current.timer + current.timer_fraction)
                    * current.width
                    / current.warmup_frames,
                    field="laser warmup width",
                )
            else:
                current_width = current.width
            current = replace(current, current_width=current_width)
            phase_box = laser_collision_box(
                current,
                longitudinal_size=current_width / 2.0,
            )
        if current.timer >= current.collision_enable_frame:
            checks.append(
                LaserCollisionCheck(False, LaserPhase.WARMUP, phase_box)
            )
        if current.timer < current.warmup_frames:
            timer, fraction = _advance_timer(
                current.timer,
                current.timer_fraction,
                time_scale_bits=time_scale_bits,
            )
            current = replace(current, timer=timer, timer_fraction=fraction)
            if current.tail_distance >= LASER_TAIL_CULL_DISTANCE:
                current = replace(current, active=False)
            return LaserStepResult(current, phase_box, tuple(checks))
        current = replace(
            current,
            phase=LaserPhase.ACTIVE,
            timer=0,
            timer_fraction=0.0,
            current_width=current.width,
        )
        box = phase_box

    if current.phase == LaserPhase.ACTIVE:
        checks.append(
            LaserCollisionCheck(
                current.timer % LASER_GRAZE_PERIOD == 0,
                LaserPhase.ACTIVE,
                box,
            )
        )
        if current.timer < current.active_frames:
            timer, fraction = _advance_timer(
                current.timer,
                current.timer_fraction,
                time_scale_bits=time_scale_bits,
            )
            current = replace(current, timer=timer, timer_fraction=fraction)
            if current.tail_distance >= LASER_TAIL_CULL_DISTANCE:
                current = replace(current, active=False)
            return LaserStepResult(current, box, tuple(checks))
        current = replace(current, phase=LaserPhase.FADE, timer=0, timer_fraction=0.0)
        if current.fade_frames == 0:
            return LaserStepResult(replace(current, active=False), box, tuple(checks))

    if current.flags & 1:
        phase_box = box
    else:
        current_width = _stored_float32(
            (
                current.width
                - (current.timer + current.timer_fraction)
                * current.width
                / current.fade_frames
                if current.fade_frames > 0
                else 0.0
            ),
            field="laser fade width",
        )
        current = replace(current, current_width=max(current_width, 0.0))
        phase_box = laser_collision_box(
            current,
            longitudinal_size=current.current_width / 2.0,
        )
    if current.timer < current.collision_disable_frame:
        checks.append(
            LaserCollisionCheck(False, LaserPhase.FADE, phase_box)
        )
    if current.timer >= current.fade_frames:
        return LaserStepResult(
            replace(current, active=False),
            phase_box,
            tuple(checks),
        )
    timer, fraction = _advance_timer(
        current.timer,
        current.timer_fraction,
        time_scale_bits=time_scale_bits,
    )
    current = replace(current, timer=timer, timer_fraction=fraction)
    if current.tail_distance >= LASER_TAIL_CULL_DISTANCE:
        current = replace(current, active=False)
    return LaserStepResult(current, phase_box, tuple(checks))
