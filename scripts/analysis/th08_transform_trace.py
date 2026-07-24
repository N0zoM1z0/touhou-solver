#!/usr/bin/env python3
"""Offline compaction of bullet-transform differential evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from collections import Counter
from pathlib import Path


STOP_TRANSFORM_MASK = 0x40 | 0x80 | 0x100
RUNTIME_PAYLOAD_INDEX = 8
RUNTIME_PAYLOAD_LENGTH = 12
PROJECTION_PAYLOAD_INDEX = 9
PROJECTION_PAYLOAD_LENGTH = 8


def _hex_counter(counter: Counter[int]) -> dict[str, int]:
    return {
        f"0x{value:08X}": count
        for value, count in sorted(counter.items())
    }


def _summary(values: list[float]) -> dict[str, float] | None:
    if not values:
        return None
    ordered = sorted(values)
    return {
        "min": ordered[0],
        "median": statistics.median(ordered),
        "max": ordered[-1],
    }


def decode_trace_bullet(values: object) -> dict[str, object] | None:
    """Decode full diagnostics or the lightweight gameplay projection."""

    if not isinstance(values, list):
        return None
    runtime = (
        values[RUNTIME_PAYLOAD_INDEX]
        if len(values) > RUNTIME_PAYLOAD_INDEX
        else None
    )
    projection = (
        values[PROJECTION_PAYLOAD_INDEX]
        if len(values) > PROJECTION_PAYLOAD_INDEX
        else None
    )
    diagnostic_runtime = (
        isinstance(runtime, list)
        and len(runtime) >= RUNTIME_PAYLOAD_LENGTH
    )
    planning_projection = (
        not diagnostic_runtime
        and isinstance(projection, list)
        and len(projection) >= PROJECTION_PAYLOAD_LENGTH
    )
    if not diagnostic_runtime and not planning_projection:
        return None
    payload = runtime if diagnostic_runtime else projection
    assert isinstance(payload, list)
    next_record = runtime[4] if diagnostic_runtime else None
    next_kind = None
    if isinstance(next_record, list) and len(next_record) >= 2:
        next_kind = int(next_record[1])
    vx = float(values[3])
    vy = float(values[4])
    speed = float(payload[0]) if payload[0] is not None else None
    stopped = math.hypot(vx, vy) <= 1e-6
    velocity_changes = (
        runtime[14]
        if diagnostic_runtime and len(runtime) > 14
        else projection[5]
        if planning_projection
        else ()
    )
    return {
        "slot": int(values[0]),
        "x": float(values[1]),
        "y": float(values[2]),
        "vx": vx,
        "vy": vy,
        "active_flags": int(values[7]),
        "speed": speed,
        "angle": float(payload[1]) if payload[1] is not None else None,
        "original_flags": int(payload[2]),
        "queue_cursor": int(runtime[3]) if diagnostic_runtime else None,
        "next_kind": next_kind,
        "timer_fraction": (
            float(runtime[5]) if diagnostic_runtime else None
        ),
        "timer_elapsed": int(runtime[6]) if diagnostic_runtime else None,
        "duration": int(runtime[7]) if diagnostic_runtime else None,
        "resume_speed": float(runtime[8]) if diagnostic_runtime else None,
        "angle_operand": float(runtime[9]) if diagnostic_runtime else None,
        "repeat_limit": int(runtime[10]) if diagnostic_runtime else None,
        "repeat_count": int(runtime[11]) if diagnostic_runtime else None,
        "callback_phase_state": (
            int(runtime[12])
            if diagnostic_runtime and len(runtime) > 12
            else int(projection[3])
            if planning_projection
            else None
        ),
        "callback_aux_state": (
            int(runtime[13])
            if diagnostic_runtime and len(runtime) > 13
            else int(projection[4])
            if planning_projection
            else None
        ),
        "velocity_change_count": (
            len(velocity_changes)
            if isinstance(velocity_changes, list)
            else 0
        ),
        "diagnostic_runtime": diagnostic_runtime,
        "planning_projection": planning_projection,
        "motion": "stopped" if stopped else "moving",
    }


def _changed_events(
    previous: dict[str, object],
    current: dict[str, object],
) -> tuple[str, ...]:
    events: list[str] = []
    for field in ("active_flags",):
        if previous[field] != current[field]:
            events.append(field)
    for field in ("queue_cursor", "next_kind", "repeat_count"):
        if (
            previous[field] is not None
            and current[field] is not None
            and previous[field] != current[field]
        ):
            events.append(field)
    for field in ("callback_phase_state", "callback_aux_state"):
        if (
            previous[field] is not None
            and current[field] is not None
            and previous[field] != current[field]
        ):
            events.append(field)
    if previous["motion"] != current["motion"]:
        events.append("motion")
    previous_speed = previous["speed"]
    current_speed = current["speed"]
    if (
        previous_speed is not None
        and current_speed is not None
        and not math.isclose(
            float(previous_speed),
            float(current_speed),
            rel_tol=0.0,
            abs_tol=1e-6,
        )
        and (
            int(previous["active_flags"]) & STOP_TRANSFORM_MASK
            or int(current["active_flags"]) & STOP_TRANSFORM_MASK
        )
    ):
        events.append("stop_speed")
    previous_angle = previous["angle"]
    current_angle = current["angle"]
    if (
        previous_angle is not None
        and current_angle is not None
        and not math.isclose(
            float(previous_angle),
            float(current_angle),
            rel_tol=0.0,
            abs_tol=1e-6,
        )
        and (
            int(previous["active_flags"]) & STOP_TRANSFORM_MASK
            or int(current["active_flags"]) & STOP_TRANSFORM_MASK
            or "motion" in events
        )
    ):
        events.append("angle")
    return tuple(events)


def analyze_transform_trace(
    path: Path,
    *,
    spell_id: int | None = None,
    max_transitions: int = 256,
    maximum_adjacent_gap: int = 12,
) -> dict[str, object]:
    digest = hashlib.sha256()
    json_decode_errors = 0
    decisions = 0
    first_frame = None
    last_frame = None
    source_fields: Counter[str] = Counter()
    active_flags: Counter[int] = Counter()
    original_flags: Counter[int] = Counter()
    queue_cursors: Counter[int] = Counter()
    next_kinds: Counter[int] = Counter()
    durations: Counter[int] = Counter()
    repeat_limits: Counter[int] = Counter()
    callback_states: Counter[tuple[int, int, str]] = Counter()
    callback_states_by_pc: dict[int, Counter[tuple[int, int, str]]] = {}
    lookahead_rows = 0
    lookahead_event_rows = 0
    lookahead_attached_rows = 0
    lookahead_errors: Counter[str] = Counter()
    lookahead_timers: Counter[int] = Counter()
    lookahead_pcs: Counter[int] = Counter()
    runtime_counts: list[float] = []
    coverage_ratios: list[float] = []
    diagnostic_runtime_samples = 0
    planning_projection_samples = 0
    projected_velocity_event_samples = 0
    adjacent_pairs = 0
    active_stop_pairs = 0
    timer_progression_pairs = 0
    timer_progression_mismatches = 0
    transition_counts: Counter[str] = Counter()
    transitions: list[dict[str, object]] = []
    previous_by_slot: dict[int, dict[str, object]] = {}
    previous_snapshot_frame: int | None = None
    previous_epoch: int | None = None

    with path.open("rb") as input_file:
        for raw_line in input_file:
            digest.update(raw_line)
            if not raw_line.strip():
                continue
            try:
                row = json.loads(raw_line)
            except (UnicodeDecodeError, json.JSONDecodeError):
                json_decode_errors += 1
                continue
            if row.get("kind") != "decision":
                continue
            spell = row.get("spell")
            row_spell_id = (
                int(spell["spell_id"])
                if isinstance(spell, dict) and spell.get("spell_id") is not None
                else None
            )
            if spell_id is not None and row_spell_id != spell_id:
                continue
            frame = int(row["frame"])
            snapshot_frame = int(row.get("snapshot_frame", frame))
            epoch = int(row.get("gameplay_epoch", 0))
            decisions += 1
            first_frame = frame if first_frame is None else min(first_frame, frame)
            last_frame = frame if last_frame is None else max(last_frame, frame)
            lookahead = row.get("bullet_velocity_lookahead")
            lookahead_pc = None
            if isinstance(lookahead, dict):
                lookahead_rows += 1
                if lookahead.get("events"):
                    lookahead_event_rows += 1
                if int(lookahead.get("attached_bullets", 0) or 0) > 0:
                    lookahead_attached_rows += 1
                error = lookahead.get("error")
                lookahead_errors[str(error)] += 1
                timer = lookahead.get("timer_elapsed")
                if timer is not None:
                    lookahead_timers[int(timer)] += 1
                lookahead_pc = lookahead.get("instruction_pointer")
                if lookahead_pc is not None:
                    lookahead_pc = int(lookahead_pc)
                    lookahead_pcs[lookahead_pc] += 1

            if isinstance(row.get("transform_bullets"), list):
                source_field = "transform_bullets"
            elif isinstance(row.get("nearby_bullets"), list):
                source_field = "nearby_bullets"
            else:
                previous_by_slot = {}
                previous_snapshot_frame = snapshot_frame
                previous_epoch = epoch
                continue
            source_fields[source_field] += 1
            decoded = tuple(
                state
                for values in row[source_field]
                if (state := decode_trace_bullet(values)) is not None
            )
            runtime_counts.append(float(len(decoded)))
            active_bullet_count = int(row.get("active_bullets", 0))
            if active_bullet_count > 0:
                coverage_ratios.append(len(decoded) / active_bullet_count)
            for state in decoded:
                active_flags[int(state["active_flags"])] += 1
                original_flags[int(state["original_flags"])] += 1
                diagnostic_runtime_samples += int(
                    bool(state["diagnostic_runtime"])
                )
                planning_projection_samples += int(
                    bool(state["planning_projection"])
                )
                projected_velocity_event_samples += int(
                    int(state["velocity_change_count"]) > 0
                )
                if state["queue_cursor"] is not None:
                    queue_cursors[int(state["queue_cursor"])] += 1
                if state["next_kind"] is not None:
                    next_kinds[int(state["next_kind"])] += 1
                if state["duration"] is not None:
                    durations[int(state["duration"])] += 1
                if state["repeat_limit"] is not None:
                    repeat_limits[int(state["repeat_limit"])] += 1
                callback_phase = state["callback_phase_state"]
                callback_aux = state["callback_aux_state"]
                if callback_phase is not None and callback_aux is not None:
                    callback_state = (
                        int(callback_phase),
                        int(callback_aux),
                        str(state["motion"]),
                    )
                    callback_states[callback_state] += 1
                    if lookahead_pc is not None:
                        callback_states_by_pc.setdefault(
                            lookahead_pc,
                            Counter(),
                        )[callback_state] += 1

            adjacent = (
                previous_snapshot_frame is not None
                and previous_epoch == epoch
                and 0 < snapshot_frame - previous_snapshot_frame
                <= maximum_adjacent_gap
            )
            current_by_slot = {int(state["slot"]): state for state in decoded}
            if adjacent:
                gap = snapshot_frame - int(previous_snapshot_frame)
                for slot, current in current_by_slot.items():
                    previous = previous_by_slot.get(slot)
                    if previous is None:
                        continue
                    adjacent_pairs += 1
                    previous_active = int(previous["active_flags"])
                    current_active = int(current["active_flags"])
                    if (
                        previous_active & STOP_TRANSFORM_MASK
                        or current_active & STOP_TRANSFORM_MASK
                    ) and (
                        previous["timer_elapsed"] is not None
                        and current["timer_elapsed"] is not None
                    ):
                        active_stop_pairs += 1
                        timer_delta = int(current["timer_elapsed"]) - int(
                            previous["timer_elapsed"]
                        )
                        if previous_active == current_active and timer_delta >= 0:
                            timer_progression_pairs += 1
                            if timer_delta != gap:
                                timer_progression_mismatches += 1
                    events = _changed_events(previous, current)
                    if not events:
                        continue
                    transition_counts.update(events)
                    if len(transitions) < max_transitions:
                        residual = math.hypot(
                            float(current["x"])
                            - (
                                float(previous["x"])
                                + float(previous["vx"]) * gap
                            ),
                            float(current["y"])
                            - (
                                float(previous["y"])
                                + float(previous["vy"]) * gap
                            ),
                        )
                        transitions.append(
                            {
                                "frame": frame,
                                "snapshot_frame": snapshot_frame,
                                "snapshot_gap": gap,
                                "slot": slot,
                                "events": list(events),
                                "linear_residual": residual,
                                "previous": previous,
                                "current": current,
                            }
                        )
            previous_by_slot = current_by_slot
            previous_snapshot_frame = snapshot_frame
            previous_epoch = epoch

    return {
        "schema": "th08-transform-differential-v2",
        "source": str(path),
        "source_sha256": digest.hexdigest(),
        "filter": {"spell_id": spell_id},
        "json_decode_errors": json_decode_errors,
        "decision_count": decisions,
        "first_frame": first_frame,
        "last_frame": last_frame,
        "source_fields": dict(sorted(source_fields.items())),
        "runtime_samples_per_decision": _summary(runtime_counts),
        "active_pool_coverage_ratio": _summary(coverage_ratios),
        "diagnostic_runtime_sample_count": diagnostic_runtime_samples,
        "planning_projection_sample_count": planning_projection_samples,
        "projected_velocity_event_sample_count": (
            projected_velocity_event_samples
        ),
        "active_flags": _hex_counter(active_flags),
        "original_flags": _hex_counter(original_flags),
        "queue_cursors": {
            str(value): count for value, count in sorted(queue_cursors.items())
        },
        "next_kinds": _hex_counter(next_kinds),
        "durations": {
            str(value): count for value, count in sorted(durations.items())
        },
        "repeat_limits": {
            str(value): count for value, count in sorted(repeat_limits.items())
        },
        "callback_states": {
            f"phase={phase},aux={aux},motion={motion}": count
            for (phase, aux, motion), count in sorted(
                callback_states.items()
            )
        },
        "callback_states_by_instruction_pointer": {
            f"0x{pc:08X}": {
                f"phase={phase},aux={aux},motion={motion}": count
                for (phase, aux, motion), count in sorted(states.items())
            }
            for pc, states in sorted(callback_states_by_pc.items())
        },
        "ecl_lookahead": {
            "rows": lookahead_rows,
            "event_rows": lookahead_event_rows,
            "attached_rows": lookahead_attached_rows,
            "errors": dict(sorted(lookahead_errors.items())),
            "timer_elapsed": {
                str(value): count
                for value, count in sorted(lookahead_timers.items())
            },
            "instruction_pointers": {
                f"0x{value:08X}": count
                for value, count in sorted(lookahead_pcs.items())
            },
        },
        "adjacent_pairs": adjacent_pairs,
        "active_stop_pairs": active_stop_pairs,
        "timer_progression_pairs": timer_progression_pairs,
        "timer_progression_mismatches": timer_progression_mismatches,
        "transition_counts": dict(sorted(transition_counts.items())),
        "retained_transition_count": len(transitions),
        "transitions": transitions,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--spell-id", type=int)
    parser.add_argument("--max-transitions", type=int, default=256)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = analyze_transform_trace(
        args.trace,
        spell_id=args.spell_id,
        max_transitions=args.max_transitions,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
