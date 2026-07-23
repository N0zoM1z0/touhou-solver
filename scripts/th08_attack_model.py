#!/usr/bin/env python3
"""Observed TH08 player damage and hostile-projectile cancel regions.

The shared 64-byte record layout is recovered from the allocators at
0x0044DE60..0x0044E040, the point/cancel consumer at 0x00449FF0, the enemy
damage consumer at 0x00451670, and the updater at 0x0044C5B0.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace


@dataclass(frozen=True)
class AttackRegion:
    center_x: float
    center_y: float
    radius: float = 0.0
    radius_delta: float = 0.0
    width: float = 0.0
    height: float = 0.0
    width_delta: float = 0.0
    height_delta: float = 0.0
    angle: float = 0.0
    frames_remaining: int = -1
    cancel_code: int = 0
    damage: int = 0
    accumulated: int = 0
    damage_cap: int = 0
    tick_interval: int = 1
    active: bool = True


def step_region(region: AttackRegion) -> AttackRegion:
    """Apply the exact shared-region update order at 0x0044C5EF."""

    if not region.active or region.frames_remaining < 0:
        return region
    remaining = region.frames_remaining - 1
    return replace(
        region,
        radius=region.radius + region.radius_delta,
        width=region.width + region.width_delta,
        height=region.height + region.height_delta,
        frames_remaining=remaining,
        active=remaining > 0,
    )


def _to_region_local(region: AttackRegion, x: float, y: float) -> tuple[float, float]:
    dx = x - region.center_x
    dy = y - region.center_y
    cosine = math.cos(-region.angle)
    sine = math.sin(-region.angle)
    return cosine * dx - sine * dy, sine * dx + cosine * dy


def cancel_region_contains_point(
    region: AttackRegion, *, point_x: float, point_y: float
) -> bool:
    """Match the hostile-bullet point test in 0x00449FF0.

    The game's circle comparison is strict. Rectangle boundaries are
    inclusive, and hostile bullet dimensions are not used by this function.
    """

    if not region.active:
        return False
    if region.radius != 0.0:
        dx = point_x - region.center_x
        dy = point_y - region.center_y
        return dx * dx + dy * dy < region.radius * region.radius
    if region.angle != 0.0:
        local_x, local_y = _to_region_local(region, point_x, point_y)
        return (
            -region.width / 2.0 <= local_x <= region.width / 2.0
            and -region.height / 2.0 <= local_y <= region.height / 2.0
        )
    return (
        region.center_x - region.width / 2.0
        <= point_x
        <= region.center_x + region.width / 2.0
        and region.center_y - region.height / 2.0
        <= point_y
        <= region.center_y + region.height / 2.0
    )


def damage_region_overlaps_enemy(
    region: AttackRegion,
    *,
    enemy_x: float,
    enemy_y: float,
    enemy_width: float,
    enemy_height: float,
) -> bool:
    """Match the region/enemy overlap branches in 0x00451670."""

    if not region.active:
        return False
    if enemy_width < 0.0 or enemy_height < 0.0:
        raise ValueError("enemy dimensions cannot be negative")
    if region.radius != 0.0:
        dx = region.center_x - enemy_x
        dy = region.center_y - enemy_y
        return dx * dx + dy * dy <= region.radius * region.radius
    if region.angle != 0.0:
        local_x, local_y = _to_region_local(region, enemy_x, enemy_y)
        return (
            local_x + enemy_width / 2.0 >= -region.width / 2.0
            and local_x - enemy_width / 2.0 <= region.width / 2.0
            and local_y + enemy_height / 2.0 >= -region.height / 2.0
            and local_y - enemy_height / 2.0 <= region.height / 2.0
        )
    return (
        region.center_x - region.width / 2.0 <= enemy_x + enemy_width / 2.0
        and region.center_x + region.width / 2.0 >= enemy_x - enemy_width / 2.0
        and region.center_y - region.height / 2.0 <= enemy_y + enemy_height / 2.0
        and region.center_y + region.height / 2.0 >= enemy_y - enemy_height / 2.0
    )


def apply_damage_region(
    region: AttackRegion,
    *,
    enemy_x: float,
    enemy_y: float,
    enemy_width: float,
    enemy_height: float,
) -> tuple[AttackRegion, int]:
    """Return updated region accounting and damage contributed this check."""

    if region.tick_interval <= 0:
        raise ValueError("tick interval must be positive")
    if not region.active or region.frames_remaining % region.tick_interval:
        return region, 0
    if not damage_region_overlaps_enemy(
        region,
        enemy_x=enemy_x,
        enemy_y=enemy_y,
        enemy_width=enemy_width,
        enemy_height=enemy_height,
    ):
        return region, 0

    contribution = region.damage
    accumulated = region.accumulated + contribution
    next_damage = region.damage
    if region.damage_cap > 0 and accumulated >= region.damage_cap:
        contribution -= accumulated - region.damage_cap
        next_damage = 0
    return (
        replace(region, damage=next_damage, accumulated=accumulated),
        max(contribution, 0),
    )


def sakuya_knife_regions(
    x: float, y: float, *, last_spell: bool
) -> tuple[AttackRegion, AttackRegion]:
    """Return the paired route-2 knife damage/cancel regions.

    Killing Doll creates 96 knives and uses damage 20. Phantom Killer creates
    128 and uses damage 30. Both use radius 32, nominal lifetime 500, and
    cancel result code 6; each callback explicitly releases the records when
    the knife times out or registers damage.
    """

    common = dict(center_x=x, center_y=y, radius=32.0, frames_remaining=500)
    damage = AttackRegion(**common, damage=30 if last_spell else 20)
    cancel = AttackRegion(**common, cancel_code=6)
    return damage, cancel
