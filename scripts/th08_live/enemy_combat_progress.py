"""Trace-only ordinary-enemy health and damage inventory."""

from __future__ import annotations

from dataclasses import dataclass
import math
import struct
import time
from typing import Callable, NamedTuple

from th08_boss_phase import (
    ENEMY_CURRENT_HEALTH_OFFSET,
    ENEMY_FLAGS2_OFFSET,
    ENEMY_FLAGS2_UPDATE_BLOCKED,
    ENEMY_FLAGS_OFFSET,
    ENEMY_FRAME_DAMAGE_OFFSET,
    ENEMY_MAXIMUM_HEALTH_OFFSET,
    ENEMY_PHASE_HEALTH_OFFSET,
)


ENEMY_COMBAT_PROGRESS_LAYOUT = "th08-enemy-combat-progress-inventory-v1"
ENEMY_PLAYER_SHOT_DAMAGE_FLAG = 0x00000040
ENEMY_DAMAGE_BLOCKING_FLAGS = 0x00000830
ENEMY_DEFEAT_MODE_SHIFT = 20
ENEMY_DEFEAT_MODE_MASK = 0x7
_FLAGS_PADDING = (
    ENEMY_FLAGS_OFFSET
    - ENEMY_CURRENT_HEALTH_OFFSET
    - 3 * struct.calcsize("<i")
)
_FRAME_DAMAGE_PADDING = (
    ENEMY_FRAME_DAMAGE_OFFSET - ENEMY_FLAGS2_OFFSET - struct.calcsize("<I")
)
_COMBAT_FIELDS = struct.Struct(
    f"<iii{_FLAGS_PADDING}xII{_FRAME_DAMAGE_PADDING}xi"
)


class EnemyCombatProgressObservation(NamedTuple):
    """Raw capture-time combat fields for one active ordinary-enemy slot."""

    slot: int
    enemy_pointer: int
    flags: int
    flags2: int
    current_health: int
    maximum_health: int
    phase_start_health: int
    frame_damage: int
    local_damage_flags_open: bool
    defeat_mode: int

    def record(self) -> list[int | bool]:
        return [
            self.slot,
            self.enemy_pointer,
            self.flags,
            self.flags2,
            self.current_health,
            self.maximum_health,
            self.phase_start_health,
            self.frame_damage,
            self.local_damage_flags_open,
            self.defeat_mode,
        ]


@dataclass(frozen=True, slots=True)
class EnemyCombatProgressInventory:
    """Bounded rows decoded from one already-captured enemy-pool blob."""

    scanned_slots: int
    active_slots: int
    observations: tuple[EnemyCombatProgressObservation, ...]
    decode_ms: float


def decode_enemy_combat_progress_inventory(
    blob: bytes,
    *,
    pool_base: int,
    pool_size: int,
    enemy_stride: int,
    enemy_active_flag: int,
    clock: Callable[[], float] = time.perf_counter,
) -> EnemyCombatProgressInventory:
    """Decode raw combat fields without issuing process-memory reads."""

    if pool_base <= 0:
        raise ValueError("enemy pool base must be positive")
    if pool_size < 0:
        raise ValueError("enemy pool size must be non-negative")
    if enemy_stride <= 0:
        raise ValueError("enemy stride must be positive")
    if not enemy_active_flag:
        raise ValueError("enemy active flag must be non-zero")
    required_end = max(
        ENEMY_CURRENT_HEALTH_OFFSET + 4,
        ENEMY_MAXIMUM_HEALTH_OFFSET + 4,
        ENEMY_PHASE_HEALTH_OFFSET + 4,
        ENEMY_FLAGS_OFFSET + 4,
        ENEMY_FLAGS2_OFFSET + 4,
        ENEMY_FRAME_DAMAGE_OFFSET + 4,
    )
    if required_end > enemy_stride:
        raise ValueError("combat-progress fields exceed one enemy record")
    expected_size = pool_size * enemy_stride
    if len(blob) < expected_size:
        raise ValueError(
            f"enemy combat-progress inventory requires {expected_size} bytes"
        )

    started = clock()
    observations: list[EnemyCombatProgressObservation] = []
    for slot in range(pool_size):
        record_base = slot * enemy_stride
        (
            current_health,
            maximum_health,
            phase_start_health,
            flags,
            flags2,
            frame_damage,
        ) = _COMBAT_FIELDS.unpack_from(
            blob,
            record_base + ENEMY_CURRENT_HEALTH_OFFSET,
        )
        if not flags & enemy_active_flag:
            continue
        observations.append(
            EnemyCombatProgressObservation(
                slot=slot,
                enemy_pointer=pool_base + record_base,
                flags=flags,
                flags2=flags2,
                current_health=current_health,
                maximum_health=maximum_health,
                phase_start_health=phase_start_health,
                frame_damage=frame_damage,
                local_damage_flags_open=bool(
                    flags & ENEMY_PLAYER_SHOT_DAMAGE_FLAG
                    and not flags & ENEMY_DAMAGE_BLOCKING_FLAGS
                    and not flags2 & ENEMY_FLAGS2_UPDATE_BLOCKED
                ),
                defeat_mode=(
                    flags >> ENEMY_DEFEAT_MODE_SHIFT
                )
                & ENEMY_DEFEAT_MODE_MASK,
            )
        )
    decode_ms = (clock() - started) * 1000.0
    if not math.isfinite(decode_ms) or decode_ms < 0.0:
        raise ValueError("enemy combat-progress decode timing must be finite")
    return EnemyCombatProgressInventory(
        scanned_slots=pool_size,
        active_slots=len(observations),
        observations=tuple(observations),
        decode_ms=decode_ms,
    )


def build_enemy_combat_progress_record(
    inventory: EnemyCombatProgressInventory,
    *,
    clock: Callable[[], float] = time.perf_counter,
) -> dict[str, object]:
    """Build the canonical compact inventory and retain construction timing."""

    started = clock()
    rows = [observation.record() for observation in inventory.observations]
    record_ms = (clock() - started) * 1000.0
    if not math.isfinite(record_ms) or record_ms < 0.0:
        raise ValueError("enemy combat-progress record timing must be finite")
    return {
        "layout": ENEMY_COMBAT_PROGRESS_LAYOUT,
        "authority": "trace_only",
        "scope": "ordinary_enemy_pool_first_64_capture_time_rows",
        "row_layout": (
            "slot_enemy_pointer_flags_flags2_current_hp_maximum_hp_"
            "phase_start_hp_frame_damage_local_damage_flags_open_defeat_mode"
        ),
        "field_offsets": {
            "current_health": ENEMY_CURRENT_HEALTH_OFFSET,
            "maximum_health": ENEMY_MAXIMUM_HEALTH_OFFSET,
            "phase_start_health": ENEMY_PHASE_HEALTH_OFFSET,
            "flags": ENEMY_FLAGS_OFFSET,
            "flags2": ENEMY_FLAGS2_OFFSET,
            "frame_damage": ENEMY_FRAME_DAMAGE_OFFSET,
        },
        "field_masks": {
            "player_shot_damage": ENEMY_PLAYER_SHOT_DAMAGE_FLAG,
            "damage_blocking": ENEMY_DAMAGE_BLOCKING_FLAGS,
            "flags2_update_blocked": ENEMY_FLAGS2_UPDATE_BLOCKED,
            "defeat_mode_shift": ENEMY_DEFEAT_MODE_SHIFT,
            "defeat_mode_mask": ENEMY_DEFEAT_MODE_MASK,
        },
        "scanned_slots": inventory.scanned_slots,
        "active_slots": inventory.active_slots,
        "rows": rows,
        "decode_ms": inventory.decode_ms,
        "record_ms": record_ms,
        "generation_authority": "none",
        "end_reason_authority": "none",
        "damageability_authority": "local_flags_only",
    }


__all__ = [
    "ENEMY_COMBAT_PROGRESS_LAYOUT",
    "EnemyCombatProgressInventory",
    "EnemyCombatProgressObservation",
    "build_enemy_combat_progress_record",
    "decode_enemy_combat_progress_inventory",
]
