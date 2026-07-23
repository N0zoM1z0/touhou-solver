#!/usr/bin/env python3
"""Executable TH08 player-shot rules recovered from ``th08.exe``.

The model covers the default 56-byte SHT shot-record path. It is based on
player_emit_shot_level (0x00450F60), player_shot_initialize (0x0044FB70),
player_shot_record_emit_if_due (0x0044FD80), player_update_shots
(0x00451150), and player_compute_damage_to_enemy (0x00451670).

Custom SHT callbacks and enemy-specific hit callbacks remain outside this
module. Route-2 Remilia Bomb levels 6 and 7 use neither, so their basic
emission, motion, collision, and damage path is fully represented here.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Mapping, Sequence

from th08_sht import ShtLevel, ShtShotRecord


SHOT_CADENCE_LENGTH = 20
PLAYER_SHOT_POOL_SIZE = 128
PLAYER_SHOT_FRAME_DAMAGE_CAP = 50
REMILIA_NORMAL_BOMB_LEVEL = 6
REMILIA_LAST_SPELL_LEVEL = 7
PIERCING_SHOT_TYPES = frozenset((4, 5, 6))


@dataclass(frozen=True)
class PlayerShot:
    x: float
    y: float
    velocity_x: float
    velocity_y: float
    hitbox_width: float
    hitbox_height: float
    damage: int
    shot_type: int
    source_index: int
    record_offset: int
    state: int = 1
    active: bool = True


def remilia_bomb_sht_level(callback_index: int, bomb_frame: int) -> int | None:
    """Return the direct SHT level used by a route-2 Remilia Bomb callback.

    Callback index 1 is the normal Bomb and index 3 is Remilia's Last Spell.
    The special level override is gated until Bomb-local frame 60.
    """

    if callback_index not in (1, 3):
        raise ValueError("Remilia Bomb callback index must be 1 or 3")
    if bomb_frame < 0:
        raise ValueError("Bomb frame cannot be negative")
    if bomb_frame < 60:
        return None
    return (
        REMILIA_LAST_SPELL_LEVEL
        if callback_index & 2
        else REMILIA_NORMAL_BOMB_LEVEL
    )


def shot_record_due(record: ShtShotRecord, cadence_frame: int) -> bool:
    """Match the signed remainder test at 0x0044FD8C.

    The firing timer cycles over integer values 0..19 while shot is held.
    Parsed live records have positive periods and non-negative phases.
    """

    if record.fire_period <= 0:
        raise ValueError("a live SHT shot record must have a positive period")
    if not 0 <= cadence_frame < SHOT_CADENCE_LENGTH:
        raise ValueError("cadence frame must be in [0, 20)")
    return cadence_frame % record.fire_period == record.fire_phase


def due_shot_records(level: ShtLevel, cadence_frame: int) -> tuple[ShtShotRecord, ...]:
    """Return all records emitted for one integer cadence tick."""

    return tuple(
        record for record in level.shots if shot_record_due(record, cadence_frame)
    )


def _source_position(
    source_index: int,
    player_position: tuple[float, float],
    option_positions: Mapping[int, tuple[float, float]]
    | Sequence[tuple[float, float]],
) -> tuple[float, float]:
    if source_index == 0:
        return player_position
    if not 1 <= source_index <= 4:
        raise ValueError("SHT source index must be in [0, 4]")
    try:
        if isinstance(option_positions, Mapping):
            return option_positions[source_index]
        return option_positions[source_index - 1]
    except (IndexError, KeyError) as exc:
        raise ValueError(f"missing option position for source {source_index}") from exc


def spawn_player_shot(
    record: ShtShotRecord,
    *,
    player_position: tuple[float, float],
    option_positions: Mapping[int, tuple[float, float]]
    | Sequence[tuple[float, float]],
) -> PlayerShot:
    """Initialize the solver-visible fields of one default SHT shot."""

    source_x, source_y = _source_position(
        record.source_index, player_position, option_positions
    )
    return PlayerShot(
        x=source_x + record.spawn_offset_x,
        y=source_y + record.spawn_offset_y,
        velocity_x=math.cos(record.angle) * record.speed,
        velocity_y=math.sin(record.angle) * record.speed,
        hitbox_width=record.hitbox_width,
        hitbox_height=record.hitbox_height,
        damage=record.damage,
        shot_type=record.shot_type,
        source_index=record.source_index,
        record_offset=record.offset,
    )


def step_player_shot(shot: PlayerShot, *, time_scale: float = 1.0) -> PlayerShot:
    """Apply the default per-frame position update at 0x00451150."""

    if time_scale < 0.0 or not math.isfinite(time_scale):
        raise ValueError("time scale must be finite and non-negative")
    if not shot.active:
        return shot
    return replace(
        shot,
        x=shot.x + shot.velocity_x * time_scale,
        y=shot.y + shot.velocity_y * time_scale,
    )


def player_shot_overlaps_enemy(
    shot: PlayerShot,
    *,
    enemy_x: float,
    enemy_y: float,
    enemy_width: float,
    enemy_height: float,
) -> bool:
    """Use the inclusive center/size AABB test at 0x00451740."""

    if not shot.active or shot.state != 1:
        return False
    if enemy_width < 0.0 or enemy_height < 0.0:
        raise ValueError("enemy dimensions cannot be negative")
    return (
        shot.x + shot.hitbox_width / 2.0
        >= enemy_x - enemy_width / 2.0
        and shot.x - shot.hitbox_width / 2.0
        <= enemy_x + enemy_width / 2.0
        and shot.y + shot.hitbox_height / 2.0
        >= enemy_y - enemy_height / 2.0
        and shot.y - shot.hitbox_height / 2.0
        <= enemy_y + enemy_height / 2.0
    )


def shot_damage_contribution(base_damage: int, *, bomb_active: bool) -> int:
    """Apply the active-Bomb damage divisor used by ordinary shot slots."""

    if base_damage < 0:
        raise ValueError("shot damage cannot be negative")
    if not bomb_active:
        return base_damage
    return max(base_damage // 5, 1)


def resolve_default_shot_damage(
    shots: Sequence[PlayerShot],
    *,
    enemy_x: float,
    enemy_y: float,
    enemy_width: float,
    enemy_height: float,
    bomb_active: bool,
) -> tuple[tuple[PlayerShot, ...], int]:
    """Resolve one enemy collision pass and the shared 50-damage shot cap.

    Shot types 4, 5, and 6 remain active after a hit. Other default shot types
    enter hit state 2 and have velocity divided by 8. Enemy-specific hit
    callbacks can override this path and are intentionally not modeled here.
    """

    updated: list[PlayerShot] = []
    total = 0
    for shot in shots:
        if not player_shot_overlaps_enemy(
            shot,
            enemy_x=enemy_x,
            enemy_y=enemy_y,
            enemy_width=enemy_width,
            enemy_height=enemy_height,
        ):
            updated.append(shot)
            continue
        total += shot_damage_contribution(shot.damage, bomb_active=bomb_active)
        if shot.shot_type in PIERCING_SHOT_TYPES:
            updated.append(shot)
        else:
            updated.append(
                replace(
                    shot,
                    state=2,
                    velocity_x=shot.velocity_x / 8.0,
                    velocity_y=shot.velocity_y / 8.0,
                )
            )
    return tuple(updated), min(total, PLAYER_SHOT_FRAME_DAMAGE_CAP)
