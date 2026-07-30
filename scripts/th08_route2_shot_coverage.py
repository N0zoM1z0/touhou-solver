"""Static Route-2 normal-shot coverage and cadence summaries.

The deterministic callback-0 geometry is the scalar projection of the
revalidated SHT path; it has not received a native-bit trigonometric
differential.  Callback-7 option geometry is deliberately represented as a
continuous outer envelope over its RNG angle support and steady focused option
orbit.  That envelope is useful for falsifying coarse Focus heuristics, but it
is optimistic for damage and has no hard-safety authority.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Literal

from th08_ecl_vm_state import float32_from_bits
from th08_option_model import OPTION_ORBIT_RADIUS
from th08_player_shot_model import (
    DEFAULT_SHOT_CALLBACK_INDEX,
    RANDOM_SPREAD_CENTER_BITS,
    RANDOM_SPREAD_DIVISOR_BITS,
    RANDOM_SPREAD_PI_BITS,
    RANDOM_SPREAD_SHOT_CALLBACK_INDEX,
    SHOT_CADENCE_LENGTH,
    shot_record_due,
)
from th08_sht import ShtLevel, ShtShotRecord


Route2ShotProfile = Literal["unfocused_primary", "focused_secondary"]

ROUTE2_OPTION_TARGET_OFFSETS = (
    (-30.0, -16.0),
    (-10.0, -32.0),
    (10.0, -32.0),
    (30.0, -16.0),
)


@dataclass(frozen=True, order=True)
class HorizontalInterval:
    lower: float
    upper: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.lower) or not math.isfinite(self.upper):
            raise ValueError("coverage interval bounds must be finite")
        if self.lower > self.upper:
            raise ValueError("coverage interval lower bound exceeds upper bound")

    @property
    def width(self) -> float:
        return self.upper - self.lower


@dataclass(frozen=True)
class NormalShotCadenceSummary:
    emissions_per_cycle: int
    base_damage_per_cycle: int
    callback_rng_u16_calls_per_cycle: int
    emissions_by_cadence: tuple[int, ...]
    base_damage_by_cadence: tuple[int, ...]

    def __post_init__(self) -> None:
        if len(self.emissions_by_cadence) != SHOT_CADENCE_LENGTH:
            raise ValueError("emission cadence summary must cover 20 frames")
        if len(self.base_damage_by_cadence) != SHOT_CADENCE_LENGTH:
            raise ValueError("damage cadence summary must cover 20 frames")


def merge_horizontal_intervals(
    intervals: Iterable[HorizontalInterval],
) -> tuple[HorizontalInterval, ...]:
    ordered = sorted(intervals)
    if not ordered:
        return ()
    merged: list[HorizontalInterval] = [ordered[0]]
    for interval in ordered[1:]:
        previous = merged[-1]
        if interval.lower <= previous.upper:
            merged[-1] = HorizontalInterval(
                previous.lower,
                max(previous.upper, interval.upper),
            )
        else:
            merged.append(interval)
    return tuple(merged)


def normal_level_cadence_summary(level: ShtLevel) -> NormalShotCadenceSummary:
    """Summarize one empty-pool native 0..19 firing-timer cycle."""

    emissions: list[int] = []
    damage: list[int] = []
    rng_calls = 0
    for cadence in range(SHOT_CADENCE_LENGTH):
        due = tuple(
            record for record in level.shots if shot_record_due(record, cadence)
        )
        unsupported = [
            record.callback_0_index
            for record in due
            if record.callback_0_index
            not in (
                DEFAULT_SHOT_CALLBACK_INDEX,
                RANDOM_SPREAD_SHOT_CALLBACK_INDEX,
            )
        ]
        if unsupported:
            raise ValueError(
                f"unsupported normal-shot callback indices: {unsupported}"
            )
        emissions.append(len(due))
        damage.append(sum(record.damage for record in due))
        rng_calls += 2 * sum(
            record.callback_0_index == RANDOM_SPREAD_SHOT_CALLBACK_INDEX
            for record in due
        )
    return NormalShotCadenceSummary(
        emissions_per_cycle=sum(emissions),
        base_damage_per_cycle=sum(damage),
        callback_rng_u16_calls_per_cycle=rng_calls,
        emissions_by_cadence=tuple(emissions),
        base_damage_by_cadence=tuple(damage),
    )


def _vertical_collision_half_extent(
    record: ShtShotRecord,
    enemy_height: float,
) -> float:
    if record.hitbox_height < 0.0 or enemy_height < 0.0:
        raise ValueError("shot and enemy dimensions cannot be negative")
    return (record.hitbox_height + enemy_height) / 2.0


def _horizontal_collision_half_extent(
    record: ShtShotRecord,
    enemy_width: float,
) -> float:
    if record.hitbox_width < 0.0 or enemy_width < 0.0:
        raise ValueError("shot and enemy dimensions cannot be negative")
    return (record.hitbox_width + enemy_width) / 2.0


def _deterministic_record_interval(
    record: ShtShotRecord,
    *,
    target_rise: float,
    enemy_width: float,
    enemy_height: float,
) -> HorizontalInterval:
    if record.source_index != 0:
        raise ValueError("deterministic Route-2 coverage expects player source 0")
    delta = record.angle + math.pi / 2.0
    if not -math.pi / 2.0 < delta < math.pi / 2.0:
        raise ValueError("normal-shot record does not travel upward")
    slope = math.tan(delta)
    center_distance = target_rise + record.spawn_offset_y
    vertical_half = _vertical_collision_half_extent(record, enemy_height)
    distances = (
        max(0.0, center_distance - vertical_half),
        max(0.0, center_distance + vertical_half),
    )
    centers = tuple(
        record.spawn_offset_x + distance * slope for distance in distances
    )
    horizontal_half = _horizontal_collision_half_extent(record, enemy_width)
    return HorizontalInterval(
        min(centers) - horizontal_half,
        max(centers) + horizontal_half,
    )


def _callback7_option_envelope(
    record: ShtShotRecord,
    *,
    target_rise: float,
    enemy_width: float,
    enemy_height: float,
) -> HorizontalInterval:
    if not 1 <= record.source_index <= len(ROUTE2_OPTION_TARGET_OFFSETS):
        raise ValueError("Route-2 callback 7 expects option source 1..4")
    target_x, target_y = ROUTE2_OPTION_TARGET_OFFSETS[
        record.source_index - 1
    ]
    pi = float32_from_bits(RANDOM_SPREAD_PI_BITS)
    divisor = float32_from_bits(RANDOM_SPREAD_DIVISOR_BITS)
    _center = float32_from_bits(RANDOM_SPREAD_CENTER_BITS)
    spread = pi / divisor
    tangent = math.tan(spread)
    secant = 1.0 / math.cos(spread)
    center_distance = target_rise + target_y + record.spawn_offset_y
    vertical_half = _vertical_collision_half_extent(record, enemy_height)

    # For a callback angle delta in [-spread, spread] and a steady option
    # orbit of radius r, x is
    #   target_x + spawn_x + d*tan(delta)
    #     + r*(cos(option_angle) + tan(delta)*sin(option_angle)).
    # The absolute terms below outer-bound the joint support.  Treating every
    # enclosed point as simultaneously attainable would be optimistic.
    support_half = (
        (abs(center_distance) + vertical_half) * tangent
        + OPTION_ORBIT_RADIUS * secant
    )
    collision_half = _horizontal_collision_half_extent(record, enemy_width)
    center_x = target_x + record.spawn_offset_x
    return HorizontalInterval(
        center_x - support_half - collision_half,
        center_x + support_half + collision_half,
    )


def normal_record_horizontal_coverage(
    record: ShtShotRecord,
    *,
    profile: Route2ShotProfile,
    target_rise: float,
    enemy_width: float = 0.0,
    enemy_height: float = 0.0,
) -> HorizontalInterval:
    """Return enemy-center x support at one player-relative target height.

    ``target_rise`` is positive upward from the player.  The interval includes
    the inclusive native center/size AABB footprint.  Callback-7 results are a
    continuous outer envelope, not a guaranteed or simultaneous hit set.
    """

    if not math.isfinite(target_rise) or target_rise < 0.0:
        raise ValueError("target rise must be finite and non-negative")
    if record.shot_type != 0:
        raise ValueError("normal coverage atlas supports shot type 0 only")
    if (
        record.callback_1_index
        or record.callback_2_index
        or record.callback_3_index
    ):
        raise ValueError(
            "normal coverage atlas requires default post-spawn callbacks"
        )
    if record.callback_0_index == DEFAULT_SHOT_CALLBACK_INDEX:
        return _deterministic_record_interval(
            record,
            target_rise=target_rise,
            enemy_width=enemy_width,
            enemy_height=enemy_height,
        )
    if (
        profile == "focused_secondary"
        and record.callback_0_index == RANDOM_SPREAD_SHOT_CALLBACK_INDEX
    ):
        return _callback7_option_envelope(
            record,
            target_rise=target_rise,
            enemy_width=enemy_width,
            enemy_height=enemy_height,
        )
    raise ValueError(
        f"unsupported callback/profile pair: {record.callback_0_index}/{profile}"
    )


def normal_level_horizontal_coverage(
    level: ShtLevel,
    *,
    profile: Route2ShotProfile,
    target_rise: float,
    enemy_width: float = 0.0,
    enemy_height: float = 0.0,
) -> tuple[HorizontalInterval, ...]:
    """Merge the static support of records due at least once per timer cycle."""

    intervals = (
        normal_record_horizontal_coverage(
            record,
            profile=profile,
            target_rise=target_rise,
            enemy_width=enemy_width,
            enemy_height=enemy_height,
        )
        for record in level.shots
        if any(
            shot_record_due(record, cadence)
            for cadence in range(SHOT_CADENCE_LENGTH)
        )
    )
    return merge_horizontal_intervals(intervals)
