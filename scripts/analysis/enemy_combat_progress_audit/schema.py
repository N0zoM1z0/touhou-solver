"""Fixed schema and row validation for combat-progress observations."""

from __future__ import annotations

import math


OBSERVATION_SCHEMA = "th08-enemy-combat-progress-observation-v1"
INVENTORY_LAYOUT = "th08-enemy-combat-progress-inventory-v1"
ROW_LAYOUT = (
    "slot_enemy_pointer_flags_flags2_current_hp_maximum_hp_"
    "phase_start_hp_frame_damage_local_damage_flags_open_defeat_mode"
)
ENEMY_POOL_BASE = 0x005826C0
ENEMY_STRIDE = 0x53D0
ENEMY_ACTIVE_FLAG = 0x1
PLAYER_SHOT_DAMAGE_FLAG = 0x40
DAMAGE_BLOCKING_FLAGS = 0x830
FLAGS2_UPDATE_BLOCKED = 0x80
DEFEAT_MODE_SHIFT = 20
DEFEAT_MODE_MASK = 0x7
EXPECTED_FIELD_OFFSETS = {
    "current_health": 0x2DFC,
    "maximum_health": 0x2E00,
    "phase_start_health": 0x2E04,
    "flags": 0x3324,
    "flags2": 0x3328,
    "frame_damage": 0x3354,
}
EXPECTED_FIELD_MASKS = {
    "player_shot_damage": PLAYER_SHOT_DAMAGE_FLAG,
    "damage_blocking": DAMAGE_BLOCKING_FLAGS,
    "flags2_update_blocked": FLAGS2_UPDATE_BLOCKED,
    "defeat_mode_shift": DEFEAT_MODE_SHIFT,
    "defeat_mode_mask": DEFEAT_MODE_MASK,
}


class EnemyCombatProgressAuditError(ValueError):
    """Raised when a trace violates the fixed observation schema."""


def require_exact_int(
    value: object,
    *,
    line_number: int,
    field: str,
) -> int:
    if type(value) is not int:
        raise EnemyCombatProgressAuditError(
            f"line {line_number}: {field} must be an integer"
        )
    return value


def require_finite_nonnegative(
    value: object,
    *,
    line_number: int,
    field: str,
) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise EnemyCombatProgressAuditError(
            f"line {line_number}: {field} must be numeric"
        )
    numeric = float(value)
    if not math.isfinite(numeric) or numeric < 0.0:
        raise EnemyCombatProgressAuditError(
            f"line {line_number}: {field} must be finite and non-negative"
        )
    return numeric


def _validate_inventory_header(
    inventory: dict[object, object],
    *,
    line_number: int,
) -> tuple[int, list[object]]:
    if inventory.get("layout") != INVENTORY_LAYOUT:
        raise EnemyCombatProgressAuditError(
            f"line {line_number}: unexpected inventory layout"
        )
    expected_text = {
        "authority": "trace_only",
        "scope": "ordinary_enemy_pool_first_64_capture_time_rows",
        "row_layout": ROW_LAYOUT,
        "generation_authority": "none",
        "end_reason_authority": "none",
        "damageability_authority": "local_flags_only",
    }
    for field, expected in expected_text.items():
        if inventory.get(field) != expected:
            raise EnemyCombatProgressAuditError(
                f"line {line_number}: unexpected {field}"
            )
    if inventory.get("field_offsets") != EXPECTED_FIELD_OFFSETS:
        raise EnemyCombatProgressAuditError(
            f"line {line_number}: field offsets changed"
        )
    if inventory.get("field_masks") != EXPECTED_FIELD_MASKS:
        raise EnemyCombatProgressAuditError(
            f"line {line_number}: field masks changed"
        )
    scanned_slots = require_exact_int(
        inventory.get("scanned_slots"),
        line_number=line_number,
        field="scanned_slots",
    )
    active_slots = require_exact_int(
        inventory.get("active_slots"),
        line_number=line_number,
        field="active_slots",
    )
    if scanned_slots != 64:
        raise EnemyCombatProgressAuditError(
            f"line {line_number}: expected exactly 64 scanned slots"
        )
    rows = inventory.get("rows")
    if not isinstance(rows, list) or active_slots != len(rows):
        raise EnemyCombatProgressAuditError(
            f"line {line_number}: active slot count does not match rows"
        )
    if not 0 <= active_slots <= scanned_slots:
        raise EnemyCombatProgressAuditError(
            f"line {line_number}: active slot count is out of range"
        )
    return scanned_slots, rows


def _validate_row(
    row: object,
    *,
    row_index: int,
    line_number: int,
    scanned_slots: int,
    previous_slot: int,
) -> list[int | bool]:
    if not isinstance(row, list) or len(row) != 10:
        raise EnemyCombatProgressAuditError(
            f"line {line_number}: row {row_index} has invalid width"
        )
    integers = [
        require_exact_int(
            value,
            line_number=line_number,
            field=f"row {row_index} field {field_index}",
        )
        for field_index, value in enumerate(row)
        if field_index != 8
    ]
    if type(row[8]) is not bool:
        raise EnemyCombatProgressAuditError(
            f"line {line_number}: row {row_index} local gate must be Boolean"
        )
    (
        slot,
        enemy_pointer,
        flags,
        flags2,
        current_health,
        maximum_health,
        phase_start_health,
        frame_damage,
        defeat_mode,
    ) = integers
    if not 0 <= slot < scanned_slots or slot <= previous_slot:
        raise EnemyCombatProgressAuditError(
            f"line {line_number}: row slots are not unique ascending indices"
        )
    if enemy_pointer != ENEMY_POOL_BASE + slot * ENEMY_STRIDE:
        raise EnemyCombatProgressAuditError(
            f"line {line_number}: row {row_index} pointer does not match slot"
        )
    if not flags & ENEMY_ACTIVE_FLAG:
        raise EnemyCombatProgressAuditError(
            f"line {line_number}: row {row_index} is not active"
        )
    expected_gate = bool(
        flags & PLAYER_SHOT_DAMAGE_FLAG
        and not flags & DAMAGE_BLOCKING_FLAGS
        and not flags2 & FLAGS2_UPDATE_BLOCKED
    )
    if row[8] is not expected_gate:
        raise EnemyCombatProgressAuditError(
            f"line {line_number}: row {row_index} local gate is inconsistent"
        )
    if defeat_mode != (flags >> DEFEAT_MODE_SHIFT) & DEFEAT_MODE_MASK:
        raise EnemyCombatProgressAuditError(
            f"line {line_number}: row {row_index} defeat mode is inconsistent"
        )
    return [
        slot,
        enemy_pointer,
        flags,
        flags2,
        current_health,
        maximum_health,
        phase_start_health,
        frame_damage,
        expected_gate,
        defeat_mode,
    ]


def validate_inventory(
    inventory: object,
    *,
    line_number: int,
) -> tuple[list[list[int | bool]], float, float]:
    if not isinstance(inventory, dict):
        raise EnemyCombatProgressAuditError(
            f"line {line_number}: inventory must be an object"
        )
    scanned_slots, rows = _validate_inventory_header(
        inventory,
        line_number=line_number,
    )
    validated_rows: list[list[int | bool]] = []
    previous_slot = -1
    for row_index, row in enumerate(rows):
        validated = _validate_row(
            row,
            row_index=row_index,
            line_number=line_number,
            scanned_slots=scanned_slots,
            previous_slot=previous_slot,
        )
        previous_slot = int(validated[0])
        validated_rows.append(validated)
    decode_ms = require_finite_nonnegative(
        inventory.get("decode_ms"),
        line_number=line_number,
        field="decode_ms",
    )
    record_ms = require_finite_nonnegative(
        inventory.get("record_ms"),
        line_number=line_number,
        field="record_ms",
    )
    return validated_rows, decode_ms, record_ms


__all__ = [
    "EnemyCombatProgressAuditError",
    "OBSERVATION_SCHEMA",
    "require_exact_int",
    "require_finite_nonnegative",
    "validate_inventory",
]
