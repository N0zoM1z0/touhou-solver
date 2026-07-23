#!/usr/bin/env python3
"""TH08 enemy-motion adapter for ECL opcode 0xB2.

The native handler is 0x004224A0. It consumes one RNG dword for a 1-in-4
uniform-angle branch and another RNG dword for the selected angle. The common
timed-displacement installer is 0x004222B0; the per-frame evaluator is
0x00422C40.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from movement_model import MovementBounds
from numeric_model import binary32_store
from pattern_ir import Easing, PolarVelocity, TimedDisplacement, Vec2
from th08_rng import Th08Rng


PI = binary32_store(math.pi)
HALF_PI = binary32_store(math.pi / 2.0)
QUARTER_PI = binary32_store(math.pi / 4.0)
THREE_QUARTER_PI = binary32_store(3.0 * math.pi / 4.0)
TAU = binary32_store(2.0 * math.pi)


TH08_EASING = {
    0: Easing.LINEAR,
    1: Easing.EASE_IN_QUAD,
    2: Easing.EASE_IN_CUBIC,
    3: Easing.EASE_IN_QUART,
    4: Easing.EASE_OUT_QUAD,
    5: Easing.EASE_OUT_CUBIC,
    6: Easing.EASE_OUT_QUART,
    7: Easing.LINEAR,
}


@dataclass(frozen=True)
class OpcodeB2Result:
    angle: float
    motion: TimedDisplacement | PolarVelocity
    direction_source: str
    horizontal_cone: str | None
    rng_u16_calls: int


def th08_easing(mode: int) -> Easing:
    return TH08_EASING[mode & 7]


def normalize_th08_angle(angle: float) -> float:
    """Match the binary32 range reduction used by 0x0043EDB0."""

    angle = binary32_store(angle)
    while angle > PI:
        angle = binary32_store(angle - TAU)
    while angle < -PI:
        angle = binary32_store(angle + TAU)
    return angle


def _player_biased_cone(
    *, enemy_x: float, player_x: float, horizontal_period: float
) -> str:
    """Choose the shortest horizontal direction on TH08's periodic x span."""

    if player_x < enemy_x:
        direct_left = enemy_x - player_x
        wrapped_right = player_x + horizontal_period - enemy_x
        return "right" if wrapped_right <= direct_left else "left"
    direct_right = player_x - enemy_x
    wrapped_left = enemy_x - (player_x - horizontal_period)
    return "left" if wrapped_left <= direct_right else "right"


def lower_opcode_b2(
    *,
    enemy_x: float,
    enemy_y: float,
    player_x: float,
    movement_bounds: MovementBounds,
    duration: int,
    interpolation_mode: int,
    speed: float,
    rng: Th08Rng,
    horizontal_period: float = 384.0,
    vertical_margin: float = 48.0,
) -> OpcodeB2Result:
    """Lower one opcode-0xB2 execution into game-neutral motion IR."""

    values = (
        enemy_x,
        enemy_y,
        player_x,
        speed,
        horizontal_period,
        vertical_margin,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError("opcode B2 inputs must be finite")
    if speed < 0.0 or horizontal_period <= 0.0 or vertical_margin < 0.0:
        raise ValueError("speed/margins must be non-negative and period positive")

    initial_calls = rng.calls
    if rng.next_mod(4) == 0:
        angle = binary32_store(rng.next_signed_unit() * PI)
        source = "uniform"
        cone = None
    else:
        cone = _player_biased_cone(
            enemy_x=enemy_x,
            player_x=player_x,
            horizontal_period=horizontal_period,
        )
        angle = rng.next_scaled(HALF_PI)
        if cone == "right":
            angle = binary32_store(angle - QUARTER_PI)
        else:
            angle = normalize_th08_angle(angle + THREE_QUARTER_PI)
        source = "player_x_biased"

    if enemy_y < movement_bounds.top + vertical_margin and angle < 0.0:
        angle = binary32_store(-angle)
    if enemy_y > movement_bounds.bottom - vertical_margin and angle > 0.0:
        angle = binary32_store(-angle)

    speed = binary32_store(speed)
    if duration > 0:
        displacement = Vec2(
            binary32_store(math.cos(angle) * speed * duration),
            binary32_store(math.sin(angle) * speed * duration),
        )
        motion: TimedDisplacement | PolarVelocity = TimedDisplacement(
            start=Vec2(binary32_store(enemy_x), binary32_store(enemy_y)),
            displacement=displacement,
            duration=duration,
            easing=th08_easing(interpolation_mode),
        )
    else:
        motion = PolarVelocity(angle=angle, speed=speed)

    return OpcodeB2Result(
        angle=angle,
        motion=motion,
        direction_source=source,
        horizontal_cone=cone,
        rng_u16_calls=rng.calls - initial_calls,
    )
