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
from pathlib import Path
from typing import Iterable, Mapping

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
    FORCED_ZERO_RETURN_BOSS_DEFEAT,
    FORCED_ZERO_RETURN_MESSAGE_START,
    FORCED_ZERO_RETURN_OPCODE_5F,
    FORCED_ZERO_RETURN_SPELL_FINISH,
    PROBE_SCHEMA,
)


REPORT_SCHEMA = "th08-enemy-lifecycle-trace-audit-v1"
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
    ):
        raise ValueError(f"{location} lifecycle kind is unsupported")
    slot = _exact_int(event.get("slot"), f"{location}.slot")
    if not 0 <= slot < ENEMY_POOL_SIZE:
        raise ValueError(f"{location} slot is outside the ordinary pool")
    enemy_pointer = _exact_int(
        event.get("enemy_pointer"),
        f"{location}.enemy_pointer",
    )
    if enemy_pointer != ENEMY_POOL_BASE + slot * ENEMY_STRIDE:
        raise ValueError(f"{location} pointer and slot disagree")
    parsed: dict[str, object] = {
        "serial": serial,
        "manager_frame": manager_frame,
        "kind": kind,
        "slot": slot,
        "enemy_pointer": enemy_pointer,
    }
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
        pointer = int(event["enemy_pointer"])
        kind = str(event["kind"])
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


def audit_lifecycle_trace_rows(
    rows: Iterable[Mapping[str, object]],
) -> dict[str, object]:
    materialized = list(rows)
    batches, installation_status, final_seen, extraction_errors = (
        _extract_batches(materialized)
    )
    events, chain = _continuous_prefix(batches, extraction_errors)
    lifetimes, lowering_errors, lowered_event_count = _lower_generations(events)
    errors = [*chain["errors"], *lowering_errors]
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
    )
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
        "lifetimes": lifetimes,
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
        },
        "authority": {
            "continuous_native_event_stream_after_baseline": (
                continuous_after_baseline
            ),
            "generation_stream_complete": generation_stream_complete,
            "prefix_lifetimes_are_exact_only": True,
            "runtime_installation_observed": False,
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


def build_report(path: Path) -> dict[str, object]:
    rows, raw = _load_jsonl(path)
    report = audit_lifecycle_trace_rows(rows)
    report["source"] = {
        "path": str(path),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "size_bytes": len(raw),
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help=(
            "return status 2 unless the installed probe has a complete "
            "post-baseline generation stream and final batch"
        ),
    )
    arguments = parser.parse_args()
    report = build_report(arguments.trace)
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
