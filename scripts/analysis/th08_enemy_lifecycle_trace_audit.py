#!/usr/bin/env python3
"""Lower exact TH08 lifecycle-ring trace batches into slot generations.

The lowerer is intentionally fail-closed. It accepts only a continuous
post-baseline uint32 serial chain with zero dropped events. Transient
nonadvancing read failures may be recovered by a later exact batch; an
overflow or malformed advancing batch ends the authoritative prefix.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
from typing import Iterable, Mapping

from analysis.th08_route2_combat_resource_candidate_board import (
    EXPECTED_SOURCE_ATLAS_SHA256,
    SCHEMA as CANDIDATE_BOARD_SCHEMA,
)
from th08_enemy_end_semantics import (
    BOSS_DEFEAT_FORCED_HP_ZERO,
    INHERITED_VM_INITIAL_RETIRE,
    MANAGER_HP_DEFEAT_MODE0_RETIRE,
    MANAGER_MAIN_VM_RETIRE,
    MANAGER_OFFSCREEN_RETIRE,
    MESSAGE_START_FORCED_HP_ZERO,
    OPCODE_5F_FORCED_HP_ZERO,
    SPELL_FINISH_FORCED_HP_ZERO,
    TIMELINE_INITIAL_VM_RETIRE,
    EnemyRetirementEvidence,
    PlayerShotDamageTransition,
    classify_enemy_retirement,
)
from th08_runtime.enemy_lifecycle_probe import (
    ENEMY_POOL_BASE,
    ENEMY_POOL_SIZE,
    ENEMY_STRIDE,
    ENEMY_DEFEAT_ITEM_ALLOCATION_RETURN_ADDRESSES,
    FORCED_ZERO_RETURN_BOSS_DEFEAT,
    FORCED_ZERO_RETURN_MESSAGE_START,
    FORCED_ZERO_RETURN_OPCODE_5F,
    FORCED_ZERO_RETURN_SPELL_FINISH,
    ITEM_ALLOCATION_RETURN_ADDRESSES,
    ITEM_POOL_BASE,
    ITEM_POOL_SIZE,
    ITEM_STRIDE,
    PROBE_SCHEMA,
)


REPORT_SCHEMA = "th08-enemy-item-lifecycle-trace-audit-v3"
EXPECTED_CANDIDATE_BOARD_SHA256 = (
    "34e70a50e6c38c8241df0425be83367e6bf9e369106d600956d5a052dfa8cfea"
)
_UINT32_MASK = 0xFFFFFFFF
_RECOVERABLE_NONADVANCING = frozenset({"read_error", "race_unknown"})
_RETIREMENT_SOURCE = {
    "retire_initial_vm_timeline": TIMELINE_INITIAL_VM_RETIRE,
    "retire_initial_vm_inherited": INHERITED_VM_INITIAL_RETIRE,
    "retire_main_vm": MANAGER_MAIN_VM_RETIRE,
    "retire_offscreen_cull": MANAGER_OFFSCREEN_RETIRE,
    "retire_defeat_mode0": MANAGER_HP_DEFEAT_MODE0_RETIRE,
}
_FORCED_ZERO_SOURCE = {
    FORCED_ZERO_RETURN_SPELL_FINISH: SPELL_FINISH_FORCED_HP_ZERO,
    FORCED_ZERO_RETURN_OPCODE_5F: OPCODE_5F_FORCED_HP_ZERO,
    FORCED_ZERO_RETURN_BOSS_DEFEAT: BOSS_DEFEAT_FORCED_HP_ZERO,
    FORCED_ZERO_RETURN_MESSAGE_START: MESSAGE_START_FORCED_HP_ZERO,
}
_ALLOCATION_KINDS = frozenset(
    {"allocate_timeline", "allocate_inherited_registers"}
)
_ITEM_KINDS = frozenset({"item_allocate", "item_pickup", "item_cull"})


def _exact_int(value: object, field: str) -> int:
    if type(value) is not int:
        raise ValueError(f"{field} must be an integer")
    return value


def _optional_uint32(value: object, field: str) -> int | None:
    if value is None:
        return None
    parsed = _exact_int(value, field)
    if not 0 <= parsed <= _UINT32_MASK:
        raise ValueError(f"{field} is outside uint32")
    return parsed


def _exact_number(value: object, field: str) -> float:
    if type(value) not in {int, float}:
        raise ValueError(f"{field} must be numeric")
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError(f"{field} must be finite")
    return parsed


def _exact_mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be an object")
    return value


def _validated_rng(
    value: object,
    *,
    field: str,
    required: bool,
) -> dict[str, int] | None:
    if value is None:
        if required:
            raise ValueError(f"{field} is missing")
        return None
    mapping = _exact_mapping(value, field)
    state = _exact_int(mapping.get("state"), f"{field}.state")
    calls = _exact_int(mapping.get("calls"), f"{field}.calls")
    if not 0 <= state <= 0xFFFF or not 0 <= calls <= _UINT32_MASK:
        raise ValueError(f"{field} is outside native RNG range")
    return {"state": state, "calls": calls}


def _batch_from_record(
    record: Mapping[str, object],
    *,
    location: str,
) -> dict[str, object]:
    if record.get("schema") != PROBE_SCHEMA:
        raise ValueError(f"{location} has an unsupported probe schema")
    if record.get("action_authority") is not False:
        raise ValueError(f"{location} does not deny action authority")
    status = record.get("status")
    if not isinstance(status, str):
        raise ValueError(f"{location} status is missing")
    events = record.get("events")
    if not isinstance(events, list):
        raise ValueError(f"{location} events must be a list")
    dropped = _exact_int(
        record.get("dropped_event_count"),
        f"{location}.dropped_event_count",
    )
    if dropped < 0:
        raise ValueError(f"{location} dropped-event count is negative")
    error = record.get("error")
    if error is not None and not isinstance(error, str):
        raise ValueError(f"{location} error must be text or null")
    return {
        "location": location,
        "status": status,
        "previous_serial": _optional_uint32(
            record.get("previous_serial"),
            f"{location}.previous_serial",
        ),
        "observed_serial": _optional_uint32(
            record.get("observed_serial"),
            f"{location}.observed_serial",
        ),
        "events": events,
        "dropped_event_count": dropped,
        "error": error,
    }


def _extract_batches(
    rows: Iterable[Mapping[str, object]],
) -> tuple[
    list[dict[str, object]],
    str,
    bool,
    list[str],
]:
    batches: list[dict[str, object]] = []
    installation_status = "missing"
    final_seen = False
    extraction_errors: list[str] = []
    for row_index, row in enumerate(rows, start=1):
        kind = row.get("kind")
        if kind == "controller_config":
            installation = row.get("enemy_lifecycle_probe")
            if isinstance(installation, Mapping):
                status = installation.get("status")
                if isinstance(status, str):
                    installation_status = status
        candidate: Mapping[str, object] | None = None
        location = f"row:{row_index}"
        if kind == "enemy_lifecycle_probe_baseline":
            candidate = row
            location += ":baseline"
        elif kind == "decision":
            envelope = row.get("enemy_lifecycle_probe")
            if isinstance(envelope, Mapping):
                capture = envelope.get("capture")
                if isinstance(capture, Mapping):
                    candidate = capture
                    location += ":decision"
        elif kind == "enemy_lifecycle_probe_final":
            final_seen = True
            candidate = row
            location += ":final"
        if candidate is None:
            continue
        try:
            batches.append(_batch_from_record(candidate, location=location))
        except ValueError as error:
            extraction_errors.append(str(error))
    return batches, installation_status, final_seen, extraction_errors


def _validated_event(
    event: object,
    *,
    expected_serial: int,
    location: str,
) -> dict[str, object]:
    if not isinstance(event, Mapping):
        raise ValueError(f"{location} event is not an object")
    serial = _exact_int(event.get("serial"), f"{location}.serial")
    if serial != expected_serial:
        raise ValueError(
            f"{location} event serial {serial} != expected {expected_serial}"
        )
    manager_frame = _exact_int(
        event.get("manager_frame"),
        f"{location}.manager_frame",
    )
    if manager_frame < 0:
        raise ValueError(f"{location} manager frame is negative")
    kind = event.get("kind")
    if (
        not isinstance(kind, str)
        or kind
        not in _ALLOCATION_KINDS
        | frozenset(_RETIREMENT_SOURCE)
        | {"forced_hp_zero"}
        | _ITEM_KINDS
    ):
        raise ValueError(f"{location} lifecycle kind is unsupported")
    stage_route_index = _exact_int(
        event.get("stage_route_index"),
        f"{location}.stage_route_index",
    )
    if not 0 <= stage_route_index <= 8:
        raise ValueError(f"{location} stage-route index is outside 0..8")
    parsed: dict[str, object] = {
        "serial": serial,
        "manager_frame": manager_frame,
        "kind": kind,
        "stage_route_index": stage_route_index,
    }

    if kind in _ITEM_KINDS:
        slot = _exact_int(event.get("item_slot"), f"{location}.item_slot")
        if not 0 <= slot < ITEM_POOL_SIZE:
            raise ValueError(f"{location} slot is outside the item pool")
        item_pointer = _exact_int(
            event.get("item_pointer"),
            f"{location}.item_pointer",
        )
        if item_pointer != ITEM_POOL_BASE + slot * ITEM_STRIDE:
            raise ValueError(f"{location} item pointer and slot disagree")
        item_type = _exact_int(
            event.get("item_type"),
            f"{location}.item_type",
        )
        motion_state = _exact_int(
            event.get("motion_state"),
            f"{location}.motion_state",
        )
        if item_type not in range(9):
            raise ValueError(f"{location} item type is outside 0..8")
        if motion_state not in {0, 1, 2, 3, 5}:
            raise ValueError(f"{location} item motion state is unsupported")
        full_value = event.get("full_value")
        if type(full_value) is not bool:
            raise ValueError(f"{location} full-value flag is not Boolean")
        item_position = _exact_mapping(
            event.get("item_position"),
            f"{location}.item_position",
        )
        item_velocity = _exact_mapping(
            event.get("item_velocity"),
            f"{location}.item_velocity",
        )
        player_position = _exact_mapping(
            event.get("player_position"),
            f"{location}.player_position",
        )
        resources_before = _exact_mapping(
            event.get("resources_before"),
            f"{location}.resources_before",
        )
        resources_after = _exact_mapping(
            event.get("resources_after"),
            f"{location}.resources_after",
        )
        caller = event.get("caller_return_address")
        caller_return_address = (
            0
            if caller is None
            else _exact_int(caller, f"{location}.caller_return_address")
        )
        source_enemy = event.get("source_enemy_pointer")
        source_enemy_pointer = (
            None
            if source_enemy is None
            else _exact_int(
                source_enemy,
                f"{location}.source_enemy_pointer",
            )
        )
        allocation_next = event.get("allocation_next_index")
        allocation_next_index = (
            None
            if allocation_next is None
            else _exact_int(
                allocation_next,
                f"{location}.allocation_next_index",
            )
        )
        rng_before = _validated_rng(
            event.get("rng_before"),
            field=f"{location}.rng_before",
            required=kind == "item_pickup",
        )
        rng_after = _validated_rng(
            event.get("rng_after"),
            field=f"{location}.rng_after",
            required=kind in {"item_allocate", "item_pickup"},
        )
        active_previous = event.get("active_previous_pointer")
        active_previous_pointer = (
            0
            if active_previous is None
            else _exact_int(
                active_previous,
                f"{location}.active_previous_pointer",
            )
        )
        if kind == "item_allocate":
            if caller_return_address not in ITEM_ALLOCATION_RETURN_ADDRESSES:
                raise ValueError(
                    f"{location} item allocation caller is unsupported"
                )
            if rng_before is not None or rng_after is None:
                raise ValueError(
                    f"{location} item allocation RNG boundary is malformed"
                )
            if (
                allocation_next_index is None
                or not 0 <= allocation_next_index < ITEM_POOL_SIZE
            ):
                raise ValueError(
                    f"{location} item allocation cursor is invalid"
                )
            if caller_return_address in (
                ENEMY_DEFEAT_ITEM_ALLOCATION_RETURN_ADDRESSES
            ):
                if source_enemy_pointer is None:
                    raise ValueError(
                        f"{location} defeat allocation lacks source enemy"
                    )
                owner_offset = source_enemy_pointer - ENEMY_POOL_BASE
                if (
                    owner_offset < 0
                    or owner_offset >= ENEMY_POOL_SIZE * ENEMY_STRIDE
                    or owner_offset % ENEMY_STRIDE
                ):
                    raise ValueError(
                        f"{location} source enemy is outside ordinary pool"
                    )
            elif source_enemy_pointer is not None:
                raise ValueError(
                    f"{location} non-defeat allocation invents source enemy"
                )
        elif kind == "item_pickup":
            if (
                caller_return_address
                or source_enemy_pointer is not None
                or allocation_next_index is not None
                or rng_before is None
                or rng_after is None
            ):
                raise ValueError(
                    f"{location} item pickup boundary is malformed"
                )
        else:
            if (
                caller_return_address
                or source_enemy_pointer is not None
                or allocation_next_index is not None
                or rng_before is not None
                or rng_after is not None
            ):
                raise ValueError(f"{location} item cull boundary is malformed")

        parsed.update(
            {
                "item_slot": slot,
                "item_pointer": item_pointer,
                "item_type": item_type,
                "motion_state": motion_state,
                "full_value": full_value,
                "item_position": {
                    axis: _exact_number(
                        item_position.get(axis),
                        f"{location}.item_position.{axis}",
                    )
                    for axis in ("x", "y")
                },
                "item_velocity": {
                    axis: _exact_number(
                        item_velocity.get(axis),
                        f"{location}.item_velocity.{axis}",
                    )
                    for axis in ("x", "y")
                },
                "player_position": {
                    axis: _exact_number(
                        player_position.get(axis),
                        f"{location}.player_position.{axis}",
                    )
                    for axis in ("x", "y")
                },
                "player_state": _exact_int(
                    event.get("player_state"),
                    f"{location}.player_state",
                ),
                "focus_logic": _exact_int(
                    event.get("focus_logic"),
                    f"{location}.focus_logic",
                ),
                "input_current": _exact_int(
                    event.get("input_current"),
                    f"{location}.input_current",
                ),
                "resources_before": {
                    field: _exact_number(
                        resources_before.get(field),
                        f"{location}.resources_before.{field}",
                    )
                    for field in ("power", "lives", "bombs")
                },
                "resources_after": {
                    field: _exact_number(
                        resources_after.get(field),
                        f"{location}.resources_after.{field}",
                    )
                    for field in ("power", "lives", "bombs")
                },
                "rng_before": rng_before,
                "rng_after": rng_after,
                "caller_return_address": caller_return_address,
                "active_previous_pointer": active_previous_pointer,
                "source_enemy_pointer": source_enemy_pointer,
                "allocation_next_index": allocation_next_index,
            }
        )
        if not 0 <= int(parsed["player_state"]) <= 0xFF:
            raise ValueError(f"{location} player state is outside uint8")
        if not 0 <= int(parsed["focus_logic"]) <= 0xFF:
            raise ValueError(f"{location} focus logic is outside uint8")
        if not 0 <= int(parsed["input_current"]) <= 0xFFFF:
            raise ValueError(f"{location} active input is outside uint16")
        if (
            kind == "item_cull"
            and parsed["resources_before"] != parsed["resources_after"]
        ):
            raise ValueError(f"{location} item cull changes resources")
        return parsed

    slot = _exact_int(event.get("slot"), f"{location}.slot")
    if not 0 <= slot < ENEMY_POOL_SIZE:
        raise ValueError(f"{location} slot is outside the ordinary pool")
    enemy_pointer = _exact_int(
        event.get("enemy_pointer"),
        f"{location}.enemy_pointer",
    )
    if enemy_pointer != ENEMY_POOL_BASE + slot * ENEMY_STRIDE:
        raise ValueError(f"{location} pointer and slot disagree")
    parsed.update({"slot": slot, "enemy_pointer": enemy_pointer})
    for field in (
        "flags_before",
        "flags_after",
        "hp_before",
        "hp_after",
        "frame_damage",
    ):
        parsed[field] = _exact_int(event.get(field), f"{location}.{field}")
    if _exact_int(parsed["frame_damage"], "frame_damage") < 0:
        raise ValueError(f"{location} frame damage is negative")
    caller = event.get("caller_return_address")
    if caller is None:
        parsed["caller_return_address"] = 0
    else:
        parsed["caller_return_address"] = _exact_int(
            caller,
            f"{location}.caller_return_address",
        )
    root_subroutine = event.get("root_subroutine")
    if kind in _ALLOCATION_KINDS:
        root = _exact_int(
            root_subroutine,
            f"{location}.root_subroutine",
        )
        if not 0 <= root <= 0x7FFF:
            raise ValueError(
                f"{location} root subroutine is outside signed-word range"
            )
        parsed["root_subroutine"] = root
    else:
        if root_subroutine is not None:
            raise ValueError(
                f"{location} non-allocation event has a root subroutine"
            )
        parsed["root_subroutine"] = None
    return parsed


def _serial_distance(previous: int, observed: int) -> int:
    distance = (observed - previous) & _UINT32_MASK
    if distance >= 1 << 31:
        raise ValueError("lifecycle serial moved backward")
    return distance


def _continuous_prefix(
    batches: list[dict[str, object]],
    extraction_errors: list[str],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    errors = list(extraction_errors)
    status_counts: Counter[str] = Counter()
    accepted: list[dict[str, object]] = []
    last_serial: int | None = None
    baseline_serial: int | None = None
    pending_nonadvancing = False
    irrecoverable_gap: dict[str, object] | None = None

    for batch_index, batch in enumerate(batches):
        status = str(batch["status"])
        status_counts[status] += 1
        previous = batch["previous_serial"]
        observed = batch["observed_serial"]
        events = list(batch["events"])
        dropped = int(batch["dropped_event_count"])
        location = str(batch["location"])

        if batch_index == 0:
            if (
                status != "baseline"
                or previous is not None
                or type(observed) is not int
                or events
                or dropped
            ):
                errors.append(f"{location} is not a valid baseline")
                irrecoverable_gap = {
                    "location": location,
                    "reason": "invalid_baseline",
                }
                break
            last_serial = observed
            baseline_serial = observed
            continue

        if last_serial is None:
            errors.append(f"{location} appears before a valid baseline")
            irrecoverable_gap = {
                "location": location,
                "reason": "missing_baseline",
            }
            break
        if previous != last_serial:
            errors.append(
                f"{location} previous serial {previous} != {last_serial}"
            )
            irrecoverable_gap = {
                "location": location,
                "reason": "serial_chain_mismatch",
            }
            break

        if status in _RECOVERABLE_NONADVANCING:
            if observed is not None or events or dropped:
                errors.append(
                    f"{location} recoverable failure unexpectedly advances"
                )
                irrecoverable_gap = {
                    "location": location,
                    "reason": "malformed_nonadvancing_failure",
                }
                break
            pending_nonadvancing = True
            continue

        if type(observed) is not int:
            errors.append(f"{location} advancing batch has no serial")
            irrecoverable_gap = {
                "location": location,
                "reason": "missing_observed_serial",
            }
            break
        try:
            distance = _serial_distance(last_serial, observed)
        except ValueError as error:
            errors.append(f"{location}: {error}")
            irrecoverable_gap = {
                "location": location,
                "reason": "serial_moved_backward",
            }
            break

        if status == "overflow_or_trace_truncation":
            errors.append(
                f"{location} dropped {dropped} lifecycle events"
            )
            irrecoverable_gap = {
                "location": location,
                "reason": "overflow_or_trace_truncation",
                "previous_serial": last_serial,
                "observed_serial": observed,
                "dropped_event_count": dropped,
            }
            break
        if status not in {"exact", "no_events"}:
            errors.append(f"{location} has unsupported status {status}")
            irrecoverable_gap = {
                "location": location,
                "reason": "unsupported_status",
            }
            break
        if dropped:
            errors.append(f"{location} exact batch reports dropped events")
            irrecoverable_gap = {
                "location": location,
                "reason": "dropped_events_in_exact_batch",
            }
            break
        if len(events) != distance:
            errors.append(
                f"{location} retains {len(events)} events for distance {distance}"
            )
            irrecoverable_gap = {
                "location": location,
                "reason": "event_count_mismatch",
            }
            break
        if status == "no_events" and distance:
            errors.append(f"{location} no-events status advances the serial")
            irrecoverable_gap = {
                "location": location,
                "reason": "advancing_no_events",
            }
            break
        try:
            parsed_events: list[dict[str, object]] = []
            for offset, event in enumerate(events, start=1):
                expected = (last_serial + offset) & _UINT32_MASK
                parsed_events.append(
                    _validated_event(
                        event,
                        expected_serial=expected,
                        location=f"{location}:event:{offset}",
                    )
                )
        except ValueError as error:
            errors.append(str(error))
            irrecoverable_gap = {
                "location": location,
                "reason": "invalid_event",
            }
            break
        accepted.extend(parsed_events)
        last_serial = observed
        pending_nonadvancing = False

    return accepted, {
        "baseline_present": baseline_serial is not None,
        "baseline_serial": baseline_serial,
        "prefix_complete_from_install": baseline_serial == 0,
        "last_continuous_serial": last_serial,
        "pending_nonadvancing_read": pending_nonadvancing,
        "irrecoverable_gap": irrecoverable_gap,
        "errors": errors,
        "status_counts": dict(sorted(status_counts.items())),
    }


def _new_lifetime(
    event: Mapping[str, object],
    *,
    observed_generation_index: int | None,
) -> dict[str, object]:
    slot = int(event["slot"])
    serial = int(event["serial"])
    if observed_generation_index is None:
        generation_key = f"slot-{slot}:baseline-partial:{serial}"
    else:
        generation_key = f"slot-{slot}:observed-{observed_generation_index}"
    return {
        "generation_key": generation_key,
        "slot": slot,
        "enemy_pointer": int(event["enemy_pointer"]),
        "stage_route_index": int(event["stage_route_index"]),
        "observed_generation_index": observed_generation_index,
        "start_observed": observed_generation_index is not None,
        "start_serial": serial if observed_generation_index is not None else None,
        "start_manager_frame": (
            int(event["manager_frame"])
            if observed_generation_index is not None
            else None
        ),
        "allocation_kind": (
            str(event["kind"])
            if observed_generation_index is not None
            else None
        ),
        "root_subroutine": (
            int(event["root_subroutine"])
            if observed_generation_index is not None
            else None
        ),
        "first_observed_serial": serial,
        "first_observed_manager_frame": int(event["manager_frame"]),
        "forced_hp_zero_events": [],
        "end_observed": False,
        "end_serial": None,
        "end_manager_frame": None,
        "end_kind": None,
        "end_classification": None,
    }


def _lower_generations(
    events: list[dict[str, object]],
) -> tuple[list[dict[str, object]], list[str], int]:
    lifetimes: list[dict[str, object]] = []
    current: dict[int, dict[str, object]] = {}
    generation_counts: Counter[int] = Counter()
    errors: list[str] = []
    lowered_count = 0

    for event in events:
        kind = str(event["kind"])
        if kind in _ITEM_KINDS:
            continue
        pointer = int(event["enemy_pointer"])
        lifetime = current.get(pointer)
        if kind in _ALLOCATION_KINDS:
            if lifetime is not None:
                errors.append(
                    f"serial {event['serial']} reallocates active "
                    f"{lifetime['generation_key']}"
                )
                break
            generation_counts[int(event["slot"])] += 1
            lifetime = _new_lifetime(
                event,
                observed_generation_index=generation_counts[int(event["slot"])],
            )
            lifetimes.append(lifetime)
            current[pointer] = lifetime
            lowered_count += 1
            continue

        if lifetime is None:
            lifetime = _new_lifetime(
                event,
                observed_generation_index=None,
            )
            lifetimes.append(lifetime)
            current[pointer] = lifetime
        elif int(lifetime["stage_route_index"]) != int(
            event["stage_route_index"]
        ):
            errors.append(
                f"serial {event['serial']} changes stage-route index inside "
                f"{lifetime['generation_key']}"
            )
            break

        if kind == "forced_hp_zero":
            caller = int(event["caller_return_address"])
            source = _FORCED_ZERO_SOURCE.get(caller)
            if source is None:
                errors.append(
                    f"serial {event['serial']} has unknown forced-zero caller"
                )
                break
            if (
                not int(event["flags_before"]) & 0x01
                or not int(event["flags_after"]) & 0x01
                or int(event["hp_after"]) != 0
            ):
                errors.append(
                    f"serial {event['serial']} forced-zero edge is malformed"
                )
                break
            forced_events = lifetime["forced_hp_zero_events"]
            assert isinstance(forced_events, list)
            forced_events.append(
                {
                    "serial": int(event["serial"]),
                    "manager_frame": int(event["manager_frame"]),
                    "source": source,
                }
            )
            lowered_count += 1
            continue

        source = _RETIREMENT_SOURCE[kind]
        if (
            not int(event["flags_before"]) & 0x01
            or int(event["flags_after"]) & 0x01
        ):
            errors.append(
                f"serial {event['serial']} retirement does not clear active"
            )
            break
        damage: PlayerShotDamageTransition | None = None
        preceding_forced: str | None = None
        defeat_mode: int | None = None
        post_health: int | None = None
        if source == MANAGER_HP_DEFEAT_MODE0_RETIRE:
            defeat_mode = 0
            post_health = int(event["hp_after"])
            frame_damage = int(event["frame_damage"])
            if frame_damage:
                damage = PlayerShotDamageTransition(
                    hp_before_damage=int(event["hp_before"]) + frame_damage,
                    resolved_damage=frame_damage,
                    hp_after_damage=int(event["hp_before"]),
                )
            forced_events = lifetime["forced_hp_zero_events"]
            assert isinstance(forced_events, list)
            if forced_events:
                preceding_forced = str(forced_events[-1]["source"])
        try:
            classification = classify_enemy_retirement(
                EnemyRetirementEvidence(
                    physical_update=int(event["manager_frame"]),
                    sequence=int(event["serial"]),
                    slot=int(event["slot"]),
                    source=source,
                    active_bit_cleared=True,
                    defeat_mode=defeat_mode,
                    post_current_health=post_health,
                    damage_transition=damage,
                    preceding_forced_hp_zero_source=preceding_forced,
                )
            )
        except ValueError as error:
            errors.append(f"serial {event['serial']}: {error}")
            break
        lifetime.update(
            {
                "end_observed": True,
                "end_serial": int(event["serial"]),
                "end_manager_frame": int(event["manager_frame"]),
                "end_kind": kind,
                "end_classification": classification.record(),
            }
        )
        current.pop(pointer)
        lowered_count += 1

    return lifetimes, errors, lowered_count


def _source_enemy_generation_key(
    lifetimes: list[dict[str, object]],
    *,
    pointer: int | None,
    stage_route_index: int,
    allocation_serial: int,
) -> str | None:
    if pointer is None:
        return None
    matches = []
    for lifetime in lifetimes:
        if (
            int(lifetime["enemy_pointer"]) != pointer
            or int(lifetime["stage_route_index"]) != stage_route_index
        ):
            continue
        start = lifetime["start_serial"]
        end = lifetime["end_serial"]
        if start is not None and int(start) > allocation_serial:
            continue
        if end is not None and int(end) < allocation_serial:
            continue
        matches.append(str(lifetime["generation_key"]))
    return matches[0] if len(matches) == 1 else None


def _new_item_generation(
    event: Mapping[str, object],
    *,
    observed_generation_index: int | None,
    enemy_lifetimes: list[dict[str, object]],
) -> dict[str, object]:
    slot = int(event["item_slot"])
    serial = int(event["serial"])
    source_enemy_pointer = event.get("source_enemy_pointer")
    source_pointer = (
        int(source_enemy_pointer)
        if source_enemy_pointer is not None
        else None
    )
    generation_key = (
        f"item-slot-{slot}:baseline-partial:{serial}"
        if observed_generation_index is None
        else f"item-slot-{slot}:observed-{observed_generation_index}"
    )
    return {
        "generation_key": generation_key,
        "item_slot": slot,
        "item_pointer": int(event["item_pointer"]),
        "stage_route_index": int(event["stage_route_index"]),
        "observed_generation_index": observed_generation_index,
        "allocation_observed": observed_generation_index is not None,
        "allocation_serial": (
            serial if observed_generation_index is not None else None
        ),
        "allocation_manager_frame": (
            int(event["manager_frame"])
            if observed_generation_index is not None
            else None
        ),
        "allocation_caller_return_address": (
            int(event["caller_return_address"])
            if observed_generation_index is not None
            else None
        ),
        "allocation_next_index": (
            event["allocation_next_index"]
            if observed_generation_index is not None
            else None
        ),
        "allocation_rng_after": (
            event["rng_after"]
            if observed_generation_index is not None
            else None
        ),
        "allocation_item_type": (
            int(event["item_type"])
            if observed_generation_index is not None
            else None
        ),
        "allocation_motion_state": (
            int(event["motion_state"])
            if observed_generation_index is not None
            else None
        ),
        "allocation_position": (
            event["item_position"]
            if observed_generation_index is not None
            else None
        ),
        "allocation_velocity": (
            event["item_velocity"]
            if observed_generation_index is not None
            else None
        ),
        "source_enemy_pointer": source_pointer,
        "source_enemy_generation_key": _source_enemy_generation_key(
            enemy_lifetimes,
            pointer=source_pointer,
            stage_route_index=int(event["stage_route_index"]),
            allocation_serial=serial,
        ),
        "end_observed": False,
        "end_kind": None,
        "end_serial": None,
        "end_manager_frame": None,
        "end_item_type": None,
        "end_motion_state": None,
        "end_position": None,
        "pickup_transaction": None,
    }


def _lower_item_generations(
    events: list[dict[str, object]],
    enemy_lifetimes: list[dict[str, object]],
) -> tuple[list[dict[str, object]], list[str], int]:
    generations: list[dict[str, object]] = []
    current: dict[int, dict[str, object]] = {}
    generation_counts: Counter[int] = Counter()
    errors: list[str] = []
    lowered_count = 0
    thresholds = (8, 24, 48, 80, 128)

    for event in events:
        kind = str(event["kind"])
        if kind not in _ITEM_KINDS:
            continue
        pointer = int(event["item_pointer"])
        generation = current.get(pointer)
        if kind == "item_allocate":
            if generation is not None:
                errors.append(
                    f"serial {event['serial']} reallocates active "
                    f"{generation['generation_key']}"
                )
                break
            slot = int(event["item_slot"])
            generation_counts[slot] += 1
            generation = _new_item_generation(
                event,
                observed_generation_index=generation_counts[slot],
                enemy_lifetimes=enemy_lifetimes,
            )
            generations.append(generation)
            current[pointer] = generation
            lowered_count += 1
            continue

        if generation is None:
            generation = _new_item_generation(
                event,
                observed_generation_index=None,
                enemy_lifetimes=enemy_lifetimes,
            )
            generations.append(generation)
            current[pointer] = generation
        elif int(generation["stage_route_index"]) != int(
            event["stage_route_index"]
        ):
            errors.append(
                f"serial {event['serial']} changes stage-route index inside "
                f"{generation['generation_key']}"
            )
            break

        allocation_type = generation["allocation_item_type"]
        end_type = int(event["item_type"])
        if (
            allocation_type is not None
            and end_type != int(allocation_type)
            and not (
                int(allocation_type) in {0, 2}
                and end_type == 8
            )
        ):
            errors.append(
                f"serial {event['serial']} changes item type outside "
                "full-Power conversion"
            )
            break

        pickup_transaction: dict[str, object] | None = None
        if kind == "item_pickup":
            rng_before = event["rng_before"]
            rng_after = event["rng_after"]
            if rng_before != rng_after:
                errors.append(
                    f"serial {event['serial']} pickup changes gameplay RNG"
                )
                break
            resources_before = event["resources_before"]
            resources_after = event["resources_after"]
            assert isinstance(resources_before, Mapping)
            assert isinstance(resources_after, Mapping)
            deltas = {
                field: float(resources_after[field])
                - float(resources_before[field])
                for field in ("power", "lives", "bombs")
            }
            power_before = float(resources_before["power"])
            power_after = float(resources_after["power"])
            pickup_transaction = {
                "player_position": event["player_position"],
                "player_state": int(event["player_state"]),
                "focus_logic": int(event["focus_logic"]),
                "input_current": int(event["input_current"]),
                "resources_before": dict(resources_before),
                "resources_after": dict(resources_after),
                "resource_delta": deltas,
                "power_thresholds_crossed": [
                    threshold
                    for threshold in thresholds
                    if power_before < threshold <= power_after
                ],
                "rng_before": rng_before,
                "rng_after": rng_after,
            }

        generation.update(
            {
                "end_observed": True,
                "end_kind": kind,
                "end_serial": int(event["serial"]),
                "end_manager_frame": int(event["manager_frame"]),
                "end_item_type": end_type,
                "end_motion_state": int(event["motion_state"]),
                "end_position": event["item_position"],
                "pickup_transaction": pickup_transaction,
            }
        )
        current.pop(pointer)
        lowered_count += 1

    return generations, errors, lowered_count


def audit_lifecycle_trace_rows(
    rows: Iterable[Mapping[str, object]],
) -> dict[str, object]:
    materialized = list(rows)
    batches, installation_status, final_seen, extraction_errors = (
        _extract_batches(materialized)
    )
    events, chain = _continuous_prefix(batches, extraction_errors)
    lifetimes, lowering_errors, lowered_event_count = _lower_generations(events)
    item_generations, item_errors, lowered_item_event_count = (
        _lower_item_generations(events, lifetimes)
    )
    errors = [*chain["errors"], *lowering_errors, *item_errors]
    completed = [
        lifetime for lifetime in lifetimes if lifetime["end_observed"]
    ]
    verified_kills = [
        lifetime
        for lifetime in completed
        if isinstance(lifetime["end_classification"], Mapping)
        and lifetime["end_classification"].get(
            "verified_player_shot_kill"
        )
        is True
    ]
    reason_counts = Counter(
        str(lifetime["end_classification"]["reason"])
        for lifetime in completed
        if isinstance(lifetime["end_classification"], Mapping)
    )
    root_counts = Counter(
        int(lifetime["root_subroutine"])
        for lifetime in lifetimes
        if lifetime["root_subroutine"] is not None
    )
    program_counts = Counter(
        (
            int(lifetime["stage_route_index"]),
            int(lifetime["root_subroutine"]),
        )
        for lifetime in lifetimes
        if lifetime["root_subroutine"] is not None
    )
    continuous_after_baseline = bool(
        chain["baseline_present"]
        and chain["irrecoverable_gap"] is None
        and not chain["pending_nonadvancing_read"]
        and not extraction_errors
    )
    generation_stream_complete = bool(
        installation_status == "installed"
        and continuous_after_baseline
        and final_seen
        and not lowering_errors
        and not item_errors
    )
    completed_items = [
        generation
        for generation in item_generations
        if generation["end_observed"]
    ]
    pickups = [
        generation
        for generation in completed_items
        if generation["end_kind"] == "item_pickup"
    ]
    defeat_allocations = [
        generation
        for generation in item_generations
        if generation["source_enemy_pointer"] is not None
    ]
    return {
        "schema": REPORT_SCHEMA,
        "role": "offline_trace_audit_no_action_authority",
        "installation_status": installation_status,
        "row_count": len(materialized),
        "batch_count": len(batches),
        "final_batch_present": final_seen,
        "serial_chain": {
            **chain,
            "errors": errors,
            "continuous_after_baseline": continuous_after_baseline,
        },
        "accepted_prefix_event_count": len(events),
        "lowered_event_count": lowered_event_count,
        "lowered_item_event_count": lowered_item_event_count,
        "lifetimes": lifetimes,
        "item_generations": item_generations,
        "summary": {
            "lifetime_count": len(lifetimes),
            "completed_lifetime_count": len(completed),
            "open_lifetime_count": len(lifetimes) - len(completed),
            "partial_start_lifetime_count": sum(
                not bool(lifetime["start_observed"])
                for lifetime in lifetimes
            ),
            "verified_player_shot_kill_count": len(verified_kills),
            "end_reason_counts": dict(sorted(reason_counts.items())),
            "observed_root_subroutine_counts": {
                str(root): root_counts[root] for root in sorted(root_counts)
            },
            "observed_program_counts": {
                f"stage-{stage}:root-{root}": program_counts[(stage, root)]
                for stage, root in sorted(program_counts)
            },
            "item_generation_count": len(item_generations),
            "completed_item_generation_count": len(completed_items),
            "partial_item_start_count": sum(
                not bool(generation["allocation_observed"])
                for generation in item_generations
            ),
            "item_pickup_count": len(pickups),
            "item_cull_count": sum(
                generation["end_kind"] == "item_cull"
                for generation in completed_items
            ),
            "defeat_item_allocation_count": len(defeat_allocations),
            "defeat_item_generation_join_count": sum(
                generation["source_enemy_generation_key"] is not None
                for generation in defeat_allocations
            ),
            "power_threshold_crossing_count": sum(
                bool(
                    generation["pickup_transaction"]
                    and generation["pickup_transaction"][
                        "power_thresholds_crossed"
                    ]
                )
                for generation in pickups
            ),
        },
        "authority": {
            "continuous_native_event_stream_after_baseline": (
                continuous_after_baseline
            ),
            "generation_stream_complete": generation_stream_complete,
            "prefix_lifetimes_are_exact_only": True,
            "accepted_allocation_root_identity_exact": not lowering_errors,
            "accepted_program_identity_exact": not lowering_errors,
            "accepted_item_generation_identity_exact": not item_errors,
            "accepted_pickup_resource_transactions_exact": not item_errors,
            "defeat_item_owner_pointer_captured": True,
            "runtime_installation_observed": False,
            "strategy_authority": False,
            "action_authority": False,
        },
    }


def join_candidate_board(
    report: dict[str, object],
    candidate_board_path: Path,
) -> dict[str, object]:
    raw = candidate_board_path.read_bytes()
    board_sha256 = hashlib.sha256(raw).hexdigest()
    if board_sha256 != EXPECTED_CANDIDATE_BOARD_SHA256:
        raise ValueError(
            "combat/resource candidate board SHA-256 differs from the "
            "accepted checkpoint"
        )
    board = json.loads(raw)
    if board.get("schema") != CANDIDATE_BOARD_SCHEMA:
        raise ValueError("combat/resource candidate board schema is unsupported")
    source_sha256 = board["inputs"]["source_emission_atlas"]["sha256"]
    if source_sha256 != EXPECTED_SOURCE_ATLAS_SHA256:
        raise ValueError(
            "candidate board source-atlas identity is unsupported"
        )

    indexed: dict[tuple[int, int], Mapping[str, object]] = {}
    for stage in board["stages"]:
        stage_index = _exact_int(
            stage["route_stage_index"],
            "candidate board route_stage_index",
        )
        for program in stage["programs"]:
            root = _exact_int(
                program["root_subroutine"],
                "candidate board root_subroutine",
            )
            key = (stage_index, root)
            if key in indexed:
                raise ValueError(
                    f"candidate board duplicates stage {stage_index} root {root}"
                )
            indexed[key] = program

    matched: list[dict[str, object]] = []
    unmatched_counts: Counter[tuple[int, int]] = Counter()
    partial_start_count = 0
    family_counts: Counter[str] = Counter()
    lifetimes = report.get("lifetimes")
    if not isinstance(lifetimes, list):
        raise ValueError("lifecycle report has no lifetime list")
    raw_item_generations = report.get("item_generations")
    if not isinstance(raw_item_generations, list):
        raise ValueError("lifecycle report has no item-generation list")
    items_by_source: dict[str, list[Mapping[str, object]]] = {}
    for item_generation in raw_item_generations:
        if not isinstance(item_generation, Mapping):
            raise ValueError("item generation is not an object")
        source_key = item_generation.get("source_enemy_generation_key")
        if source_key is not None:
            items_by_source.setdefault(str(source_key), []).append(
                item_generation
            )
    for lifetime in lifetimes:
        if not isinstance(lifetime, Mapping):
            raise ValueError("lifecycle report lifetime is not an object")
        root = lifetime.get("root_subroutine")
        if root is None:
            partial_start_count += 1
            continue
        stage_index = _exact_int(
            lifetime.get("stage_route_index"),
            "lifetime stage_route_index",
        )
        root_index = _exact_int(root, "lifetime root_subroutine")
        program = indexed.get((stage_index, root_index))
        if program is None:
            unmatched_counts[(stage_index, root_index)] += 1
            continue
        families = [str(value) for value in program["candidate_families"]]
        family_counts.update(families)
        source_items = items_by_source.get(
            str(lifetime["generation_key"]),
            [],
        )
        pickup_transactions = [
            item["pickup_transaction"]
            for item in source_items
            if isinstance(item.get("pickup_transaction"), Mapping)
        ]
        matched.append(
            {
                "generation_key": lifetime["generation_key"],
                "stage_route_index": stage_index,
                "root_subroutine": root_index,
                "candidate_id": program["candidate_id"],
                "candidate_families": families,
                "start_serial": lifetime["start_serial"],
                "start_manager_frame": lifetime["start_manager_frame"],
                "source_item_generation_keys": [
                    item["generation_key"] for item in source_items
                ],
                "observed_item_allocation_count": len(source_items),
                "observed_item_pickup_count": len(pickup_transactions),
                "observed_power_delta": sum(
                    float(transaction["resource_delta"]["power"])
                    for transaction in pickup_transactions
                ),
                "observed_power_thresholds_crossed": sorted(
                    {
                        int(threshold)
                        for transaction in pickup_transactions
                        for threshold in transaction[
                            "power_thresholds_crossed"
                        ]
                    }
                ),
            }
        )

    return {
        "schema": "th08-enemy-lifecycle-candidate-board-join-v1",
        "role": "offline_trace_join_no_action_authority",
        "candidate_board": {
            "name": candidate_board_path.name,
            "sha256": board_sha256,
            "report_digest": board["report_digest"],
        },
        "summary": {
            "lifetime_count": len(lifetimes),
            "matched_lifetime_count": len(matched),
            "unmatched_program_lifetime_count": sum(unmatched_counts.values()),
            "partial_start_lifetime_count": partial_start_count,
            "candidate_family_lifetime_counts": dict(
                sorted(family_counts.items())
            ),
            "matched_lifetime_item_allocation_count": sum(
                int(item["observed_item_allocation_count"])
                for item in matched
            ),
            "matched_lifetime_item_pickup_count": sum(
                int(item["observed_item_pickup_count"])
                for item in matched
            ),
            "matched_lifetime_power_delta": sum(
                float(item["observed_power_delta"])
                for item in matched
            ),
        },
        "matched_lifetimes": matched,
        "unmatched_programs": [
            {
                "stage_route_index": stage,
                "root_subroutine": root,
                "lifetime_count": unmatched_counts[(stage, root)],
                "reason": "program_not_timeline_rooted_in_candidate_board",
            }
            for stage, root in sorted(unmatched_counts)
        ],
        "authority": {
            "immutable_candidate_board_identity": True,
            "matched_program_identity_exact": bool(
                report["authority"]["accepted_program_identity_exact"]
            ),
            "runtime_installation_observed": bool(
                report["authority"]["runtime_installation_observed"]
            ),
            "candidate_benefit_verified": False,
            "strategy_authority": False,
            "action_authority": False,
        },
    }


def _load_jsonl(path: Path) -> tuple[list[Mapping[str, object]], bytes]:
    raw = path.read_bytes()
    rows: list[Mapping[str, object]] = []
    for line_number, line in enumerate(raw.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(
                f"{path}:{line_number}: invalid JSON: {error}"
            ) from error
        if not isinstance(row, Mapping):
            raise ValueError(f"{path}:{line_number}: row is not an object")
        rows.append(row)
    return rows, raw


def build_report(
    path: Path,
    *,
    candidate_board_path: Path | None = None,
) -> dict[str, object]:
    rows, raw = _load_jsonl(path)
    report = audit_lifecycle_trace_rows(rows)
    report["source"] = {
        "path": str(path),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "size_bytes": len(raw),
    }
    if candidate_board_path is not None:
        report["candidate_board_join"] = join_candidate_board(
            report,
            candidate_board_path,
        )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--candidate-board", type=Path)
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help=(
            "return status 2 unless the installed probe has a complete "
            "post-baseline generation stream and final batch"
        ),
    )
    arguments = parser.parse_args()
    report = build_report(
        arguments.trace,
        candidate_board_path=arguments.candidate_board,
    )
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if arguments.output is None:
        print(encoded, end="")
    else:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(encoded, encoding="utf-8")
    if (
        arguments.require_complete
        and not report["authority"]["generation_stream_complete"]
    ):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
