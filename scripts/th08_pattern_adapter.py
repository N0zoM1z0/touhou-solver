#!/usr/bin/env python3
"""TH08-specific lowering into game-neutral pattern IR."""

from __future__ import annotations

from dataclasses import dataclass

from pattern_ir import (
    FixedSpellRewardPolicy,
    HistoricalHitboxTrail,
    SetTimelineSpawnEnabled,
)


@dataclass(frozen=True)
class Th08TrailPresentation:
    """TH08-only visual settings retained for a renderer/validator."""

    enabled: bool
    mode: int
    history_samples: int
    render_stride: int


@dataclass(frozen=True)
class Th08TrailLowering:
    presentation: Th08TrailPresentation
    collision: HistoricalHitboxTrail | None


def lower_opcode_af(value: int) -> SetTimelineSpawnEnabled:
    """Lower TH08's inverted timeline-spawn suppression dword."""

    return SetTimelineSpawnEnabled(enabled=value == 0)


def lower_opcode_9b(enabled: int) -> FixedSpellRewardPolicy | None:
    """Lower TH08's fixed, non-decaying spell-reward flag."""

    if not enabled:
        return None
    return FixedSpellRewardPolicy(
        initial_bonus=99_999_990,
        capture_result_units=700,
    )


def lower_opcode_9d(
    mode: int,
    history_samples: int,
    collision_sample_limit: int,
    render_stride: int,
) -> Th08TrailLowering:
    """Separate TH08 trail presentation from optional historical collision."""

    if min(history_samples, collision_sample_limit, render_stride) < 0:
        raise ValueError("trail counts and stride must be non-negative")
    if mode and (history_samples == 0 or render_stride == 0):
        raise ValueError("an enabled TH08 trail needs history and render stride")

    collision = None
    if mode and collision_sample_limit > 1:
        collision = HistoricalHitboxTrail(
            history_samples=history_samples,
            collision_sample_limit=collision_sample_limit,
            collision_stride=6,
            interpolate_collision=bool(mode & 0x02),
        )
    return Th08TrailLowering(
        presentation=Th08TrailPresentation(
            enabled=bool(mode),
            mode=mode & 0xFF,
            history_samples=history_samples,
            render_stride=render_stride,
        ),
        collision=collision,
    )
