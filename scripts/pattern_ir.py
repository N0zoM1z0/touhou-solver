#!/usr/bin/env python3
"""Game-neutral motion primitives used by danmaku adapters."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

from numeric_model import StoreQuantizer, identity_store


class Easing(Enum):
    LINEAR = "linear"
    EASE_IN_QUAD = "ease_in_quad"
    EASE_IN_CUBIC = "ease_in_cubic"
    EASE_IN_QUART = "ease_in_quart"
    EASE_OUT_QUAD = "ease_out_quad"
    EASE_OUT_CUBIC = "ease_out_cubic"
    EASE_OUT_QUART = "ease_out_quart"


@dataclass(frozen=True)
class Vec2:
    x: float
    y: float


@dataclass(frozen=True)
class PolarVelocity:
    angle: float
    speed: float


@dataclass(frozen=True)
class TimedDisplacement:
    """Move from ``start`` by ``displacement`` over a fixed frame duration."""

    start: Vec2
    displacement: Vec2
    duration: int
    easing: Easing = Easing.LINEAR

    def __post_init__(self) -> None:
        values = (
            self.start.x,
            self.start.y,
            self.displacement.x,
            self.displacement.y,
        )
        if not all(math.isfinite(value) for value in values):
            raise ValueError("motion coordinates must be finite")
        if self.duration <= 0:
            raise ValueError("timed displacement duration must be positive")

    @property
    def destination(self) -> Vec2:
        return Vec2(
            self.start.x + self.displacement.x,
            self.start.y + self.displacement.y,
        )


@dataclass(frozen=True)
class SetTimelineSpawnEnabled:
    """Change whether future timeline spawn records create entities.

    The timeline still consumes a suppressed record. This event controls its
    spawn side effect; it does not pause or rewind timeline execution.
    """

    enabled: bool


@dataclass(frozen=True)
class FixedSpellRewardPolicy:
    """A spell reward whose value does not decay while the phase runs."""

    initial_bonus: int
    capture_result_units: int

    def __post_init__(self) -> None:
        if self.initial_bonus < 0:
            raise ValueError("initial spell bonus must be non-negative")
        if self.capture_result_units < 0:
            raise ValueError("capture result units must be non-negative")


@dataclass(frozen=True)
class HistoricalHitboxTrail:
    """Repeat an entity hitbox at selected historical position samples.

    Rendering is deliberately absent. A game adapter should only emit this
    event when history affects collision, keeping visual trails out of search
    snapshots and state hashes.
    """

    history_samples: int
    collision_sample_limit: int
    collision_stride: int
    interpolate_collision: bool = False

    def __post_init__(self) -> None:
        if self.history_samples <= 0:
            raise ValueError("trail history must contain at least one sample")
        if not 1 < self.collision_sample_limit <= self.history_samples:
            raise ValueError(
                "collision sample limit must be in [2, history_samples]"
            )
        if self.collision_stride <= 0:
            raise ValueError("collision stride must be positive")


def easing_progress(easing: Easing, progress: float) -> float:
    """Evaluate a normalized easing curve, clamping input to ``[0, 1]``."""

    if not math.isfinite(progress):
        raise ValueError("progress must be finite")
    progress = min(max(progress, 0.0), 1.0)
    if easing is Easing.LINEAR:
        return progress
    if easing is Easing.EASE_IN_QUAD:
        return progress * progress
    if easing is Easing.EASE_IN_CUBIC:
        return progress * progress * progress
    if easing is Easing.EASE_IN_QUART:
        return progress * progress * progress * progress

    remaining = 1.0 - progress
    if easing is Easing.EASE_OUT_QUAD:
        return 1.0 - remaining * remaining
    if easing is Easing.EASE_OUT_CUBIC:
        return 1.0 - remaining * remaining * remaining
    if easing is Easing.EASE_OUT_QUART:
        return 1.0 - remaining * remaining * remaining * remaining
    raise ValueError(f"unsupported easing curve: {easing!r}")


def timed_displacement_position(
    motion: TimedDisplacement,
    *,
    elapsed: float,
    store: StoreQuantizer = identity_store,
) -> Vec2:
    """Evaluate a motion without depending on a game's timer representation."""

    if not math.isfinite(elapsed):
        raise ValueError("elapsed time must be finite")
    progress = easing_progress(motion.easing, elapsed / motion.duration)
    return Vec2(
        store(motion.start.x + motion.displacement.x * progress),
        store(motion.start.y + motion.displacement.y * progress),
    )
