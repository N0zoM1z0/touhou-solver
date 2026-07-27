#!/usr/bin/env python3
"""Deterministic residual audit for trace-only TH08 bullet-birth evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


SCHEMA = "th08-bullet-birth-residual-audit-v3"
TRACE_KIND = "bullet_birth_audit"
TRACE_ROLE = "trace_only_no_action_authority"
TRACE_SCHEMA_VERSIONS = frozenset((1, 2, 3, 4, 5))
MAX_SAMPLES = 20
OBSERVER_P95_LIMIT_MS = 0.20
OBSERVER_P99_LIMIT_MS = 0.40
OBSERVER_MAX_LIMIT_MS = 2.00

_INTEGER_FIELD = {
    name: re.compile(rf'"{name}": (-?\d+)')
    for name in (
        "frame",
        "gameplay_epoch",
        "stage_route_index",
    )
}
_JSON_DECODER = json.JSONDecoder()
_EVIDENCE_CODE_KIND = {
    1: "invalid_timer",
    2: "bootstrap_recent",
    3: "activation_edge",
    4: "timer_regression",
}
_EVIDENCE_STATUS_CODE = {
    1: "invalid_timer",
    2: "capture_spanned",
    3: "slot_reuse_ambiguous",
    4: "complete",
}


class BulletBirthAuditError(ValueError):
    """The retained trace cannot support a deterministic residual audit."""


def _phase_key(stage: int, spell_id: int | None) -> str:
    suffix = "nonspell" if spell_id is None else f"spell_{spell_id}"
    return f"stage_{stage}:{suffix}"


def _decision_scope(line: str) -> tuple[tuple[int, int], dict[str, object]]:
    values: dict[str, int] = {}
    prefix_end = line.find('"boss_phase":')
    prefix = line if prefix_end < 0 else line[:prefix_end]
    for name, pattern in _INTEGER_FIELD.items():
        match = pattern.search(prefix)
        if match is None:
            raise BulletBirthAuditError(
                f"decision record omits integer field {name}"
            )
        values[name] = int(match.group(1))
    spell_marker = '"spell": '
    spell_start = prefix.find(spell_marker)
    if spell_start < 0:
        raise BulletBirthAuditError("decision record omits spell field")
    spell, _end = _JSON_DECODER.raw_decode(
        prefix,
        spell_start + len(spell_marker),
    )
    spell_id: int | None = None
    spell_name: str | None = None
    if isinstance(spell, dict) and spell.get("active"):
        raw_spell_id = spell.get("spell_id")
        if type(raw_spell_id) is not int:
            raise BulletBirthAuditError(
                "active decision spell omits integer spell_id"
            )
        spell_id = raw_spell_id
        raw_name = spell.get("name")
        spell_name = raw_name if isinstance(raw_name, str) else None
    lookahead_error: str | None = None
    lookahead_stop_reason: str | None = None
    lookahead_event_count = 0
    lookahead_instructions_scanned = 0
    lookahead_marker = '"bullet_velocity_lookahead": '
    lookahead_start = line.find(lookahead_marker)
    if lookahead_start >= 0:
        lookahead, _lookahead_end = _JSON_DECODER.raw_decode(
            line,
            lookahead_start + len(lookahead_marker),
        )
        if isinstance(lookahead, dict):
            raw_error = lookahead.get("error")
            lookahead_error = (
                raw_error if isinstance(raw_error, str) else None
            )
            raw_stop = lookahead.get("stop_reason")
            lookahead_stop_reason = (
                raw_stop if isinstance(raw_stop, str) else None
            )
            raw_events = lookahead.get("events")
            if isinstance(raw_events, list):
                lookahead_event_count = len(raw_events)
            raw_scanned = lookahead.get("instructions_scanned")
            if type(raw_scanned) is int and raw_scanned >= 0:
                lookahead_instructions_scanned = raw_scanned
    lookahead_read_ms: float | None = None
    timing_marker = '"timing_ms": '
    timing_start = line.find(timing_marker)
    if timing_start >= 0:
        timing, _timing_end = _JSON_DECODER.raw_decode(
            line,
            timing_start + len(timing_marker),
        )
        if isinstance(timing, dict):
            raw_read_ms = timing.get("read_ecl_lookahead")
            if (
                isinstance(raw_read_ms, (int, float))
                and math.isfinite(raw_read_ms)
            ):
                lookahead_read_ms = float(raw_read_ms)
    scope = {
        "stage_route_index": values["stage_route_index"],
        "spell_id": spell_id,
        "spell_name": spell_name,
        "phase": _phase_key(values["stage_route_index"], spell_id),
        "velocity_lookahead_error": lookahead_error,
        "velocity_lookahead_stop_reason": lookahead_stop_reason,
        "velocity_lookahead_event_count": lookahead_event_count,
        "velocity_lookahead_instructions_scanned": (
            lookahead_instructions_scanned
        ),
        "velocity_lookahead_read_ms": lookahead_read_ms,
    }
    return (values["gameplay_epoch"], values["frame"]), scope


def _nearest_rank(values: list[float], quantile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, math.ceil(quantile * len(ordered)) - 1)
    return round(float(ordered[index]), 6)


def _distribution(values: list[float]) -> dict[str, float | int | None]:
    return {
        "count": len(values),
        "p50": _nearest_rank(values, 0.50),
        "p95": _nearest_rank(values, 0.95),
        "p99": _nearest_rank(values, 0.99),
        "p99_9": _nearest_rank(values, 0.999),
        "max": round(max(values), 6) if values else None,
    }


def _counter(counter: Counter[object]) -> dict[str, int]:
    return {
        str(key): int(counter[key])
        for key in sorted(counter, key=lambda item: str(item))
    }


def _evidence_count_bucket(count: int) -> str:
    if count == 0:
        return "0"
    if count <= 8:
        return "1_8"
    if count <= 32:
        return "9_32"
    if count <= 64:
        return "33_64"
    if count <= 320:
        return "65_320"
    return "321_plus"


def _validated_audit(record: Any, *, line_number: int) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise BulletBirthAuditError(
            f"line {line_number}: audit record is not an object"
        )
    if record.get("schema_version") not in TRACE_SCHEMA_VERSIONS:
        raise BulletBirthAuditError(
            f"line {line_number}: unsupported audit schema"
        )
    if record.get("role") != TRACE_ROLE:
        raise BulletBirthAuditError(
            f"line {line_number}: audit role is not trace-only"
        )
    if (
        record.get("schema_version") == 5
        and record.get("observation_backend") not in {"python", "native"}
    ):
        raise BulletBirthAuditError(
            f"line {line_number}: audit omits a valid observation backend"
        )
    for field in ("frame", "snapshot_frame", "gameplay_epoch"):
        if type(record.get(field)) is not int:
            raise BulletBirthAuditError(
                f"line {line_number}: audit omits integer {field}"
            )
    return record


def _read_trace(
    trace_path: Path,
) -> tuple[
    list[dict[str, Any]],
    dict[tuple[int, int], dict[str, object]],
    str,
    int,
]:
    audits: list[dict[str, Any]] = []
    decisions: dict[tuple[int, int], dict[str, object]] = {}
    digest = hashlib.sha256()
    size = 0
    with trace_path.open("rb") as source:
        for line_number, raw_line in enumerate(source, 1):
            digest.update(raw_line)
            size += len(raw_line)
            if b'"kind": "bullet_birth_audit"' in raw_line:
                try:
                    parsed = json.loads(raw_line)
                except (UnicodeDecodeError, json.JSONDecodeError) as error:
                    raise BulletBirthAuditError(
                        f"line {line_number}: invalid audit JSON: {error}"
                    ) from error
                audits.append(
                    _validated_audit(parsed, line_number=line_number)
                )
            elif b'"kind": "decision"' in raw_line:
                try:
                    key, scope = _decision_scope(raw_line.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError) as error:
                    raise BulletBirthAuditError(
                        f"line {line_number}: invalid decision prefix: {error}"
                    ) from error
                previous = decisions.setdefault(key, scope)
                if previous != scope:
                    raise BulletBirthAuditError(
                        f"line {line_number}: conflicting decision scope"
                    )
    if not audits:
        raise BulletBirthAuditError("trace contains no bullet-birth audits")
    return audits, decisions, digest.hexdigest(), size


def _scope_for(
    audit: dict[str, Any],
    decisions: dict[tuple[int, int], dict[str, object]],
) -> dict[str, object]:
    key = (audit["gameplay_epoch"], audit["frame"])
    scope = decisions.get(key)
    if scope is None:
        stage = audit.get("stage_route_index")
        if type(stage) is not int:
            raise BulletBirthAuditError(
                f"audit frame {audit['frame']} has no stage"
            )
        return {
            "stage_route_index": stage,
            "spell_id": None,
            "spell_name": None,
            "phase": f"stage_{stage}:unattributed",
        }
    return scope


def _evidence_items(
    observation: dict[str, Any],
) -> list[dict[str, object]]:
    evidence = observation.get("evidence")
    if isinstance(evidence, list):
        if not all(isinstance(item, dict) for item in evidence):
            raise BulletBirthAuditError("birth evidence is not an object")
        return evidence
    if not isinstance(evidence, dict):
        raise BulletBirthAuditError(
            "observation evidence is neither legacy rows nor columns"
        )
    if evidence.get("format") != "columnar_v1":
        raise BulletBirthAuditError("unknown birth evidence column format")
    count = observation.get("evidence_count")
    if type(count) is not int or count < 0:
        raise BulletBirthAuditError("invalid birth evidence count")
    column_names = (
        "slot",
        "code",
        "status",
        "state",
        "age",
        "geometry",
        "transform_flags",
        "geometry_finite",
    )
    columns: dict[str, list[Any]] = {}
    for name in column_names:
        value = evidence.get(name)
        if not isinstance(value, list) or len(value) != count:
            raise BulletBirthAuditError(
                f"birth evidence column {name} has invalid length"
            )
        columns[name] = value
    previous_columns: dict[str, list[Any]] = {}
    for name in ("previous_state", "previous_age"):
        value = evidence.get(name)
        if value is None:
            previous_columns[name] = [None] * count
        elif isinstance(value, list) and len(value) == count:
            previous_columns[name] = value
        else:
            raise BulletBirthAuditError(
                f"birth evidence column {name} has invalid length"
            )
    support_start = observation.get("previous_frame_before")
    support_end = observation.get("frame_after")
    if support_start is not None and type(support_start) is not int:
        raise BulletBirthAuditError("invalid previous capture frame")
    if type(support_end) is not int:
        raise BulletBirthAuditError("invalid capture end frame")

    rows: list[dict[str, object]] = []
    for index in range(count):
        code = columns["code"][index]
        status_code = columns["status"][index]
        if type(code) is not int or code not in _EVIDENCE_CODE_KIND:
            raise BulletBirthAuditError("unknown birth evidence code")
        if (
            type(status_code) is not int
            or status_code not in _EVIDENCE_STATUS_CODE
        ):
            raise BulletBirthAuditError("unknown birth evidence status code")
        slot = columns["slot"][index]
        state = columns["state"][index]
        age = columns["age"][index]
        transform_flags = columns["transform_flags"][index]
        geometry = columns["geometry"][index]
        geometry_finite = columns["geometry_finite"][index]
        if not all(
            type(value) is int
            for value in (slot, state, age, transform_flags)
        ):
            raise BulletBirthAuditError(
                "birth evidence integer column contains a non-int"
            )
        if (
            not isinstance(geometry, list)
            or len(geometry) != 6
            or not all(
                value is None
                or (
                    isinstance(value, (int, float))
                    and math.isfinite(value)
                )
                for value in geometry
            )
        ):
            raise BulletBirthAuditError("invalid birth evidence geometry")
        if type(geometry_finite) is not bool:
            raise BulletBirthAuditError(
                "birth evidence geometry flag is not a bool"
            )
        previous_state = previous_columns["previous_state"][index]
        previous_age = previous_columns["previous_age"][index]
        if (
            previous_state is not None
            and type(previous_state) is not int
        ) or (
            previous_age is not None
            and type(previous_age) is not int
        ):
            raise BulletBirthAuditError(
                "birth evidence previous column contains a non-int"
            )
        rows.append(
            {
                "slot": slot,
                "kind": _EVIDENCE_CODE_KIND[code],
                "observation_status": _EVIDENCE_STATUS_CODE[status_code],
                "state": state,
                "age": age,
                "previous_state": previous_state,
                "previous_age": previous_age,
                "activation_support": [
                    support_start if code in (3, 4) else None,
                    support_end,
                ],
                "position": geometry[:2],
                "velocity": geometry[2:4],
                "geometry": geometry[4:],
                "transform_flags": transform_flags,
                "geometry_finite": geometry_finite,
            }
        )
    return rows


def _intent_events(
    audits: list[dict[str, Any]],
    decisions: dict[tuple[int, int], dict[str, object]],
) -> tuple[
    list[dict[str, Any]],
    Counter[str],
    Counter[str],
    Counter[str],
    int,
    dict[str, Counter[str]],
    dict[str, list[float]],
]:
    sightings: defaultdict[tuple[object, ...], list[dict[str, Any]]] = (
        defaultdict(list)
    )
    status_counts: Counter[str] = Counter()
    stop_counts: Counter[str] = Counter()
    dependency_counts: Counter[str] = Counter()
    untimed_signatures: set[tuple[object, ...]] = set()
    by_phase: defaultdict[str, Counter[str]] = defaultdict(Counter)
    read_ms_by_phase: defaultdict[str, list[float]] = defaultdict(list)

    for audit in audits:
        scope = _scope_for(audit, decisions)
        phase = str(scope["phase"])
        by_phase[phase]["audit_rows"] += 1
        pointer = audit.get("spell_enemy_pointer")
        if type(pointer) is int and pointer:
            by_phase[phase]["active_main_vm_rows"] += 1
        else:
            by_phase[phase]["no_active_main_vm_rows"] += 1
        velocity_error = scope.get("velocity_lookahead_error")
        if isinstance(velocity_error, str):
            by_phase[phase][
                f"velocity_lookahead_error:{velocity_error}"
            ] += 1
        velocity_stop = scope.get("velocity_lookahead_stop_reason")
        if isinstance(velocity_stop, str):
            by_phase[phase][f"velocity_lookahead_stop:{velocity_stop}"] += 1
        velocity_events = scope.get("velocity_lookahead_event_count")
        if type(velocity_events) is int and velocity_events:
            by_phase[phase]["velocity_event_rows"] += 1
            by_phase[phase]["velocity_events"] += velocity_events
        velocity_scanned = scope.get(
            "velocity_lookahead_instructions_scanned"
        )
        if type(velocity_scanned) is int:
            by_phase[phase]["velocity_instructions_scanned"] += (
                velocity_scanned
            )
        velocity_read_ms = scope.get("velocity_lookahead_read_ms")
        if isinstance(velocity_read_ms, float):
            read_ms_by_phase[phase].append(velocity_read_ms)
        intent_result = audit.get("intent")
        if not isinstance(intent_result, dict):
            by_phase[phase]["intent_result_absent"] += 1
            continue
        by_phase[phase]["classified_rows"] += 1
        stop_counts[str(intent_result.get("stop_reason"))] += 1
        by_phase[phase][
            f"stop:{intent_result.get('stop_reason')}"
        ] += 1
        alignment = audit.get("alignment")
        if not isinstance(alignment, dict):
            raise BulletBirthAuditError("audit alignment is not an object")
        ecl_before = alignment.get("ecl_frame_before")
        ecl_after = alignment.get("ecl_frame_after")
        if type(pointer) is not int:
            raise BulletBirthAuditError("audit spell pointer is not an int")
        intents = intent_result.get("intents")
        if not isinstance(intents, list):
            raise BulletBirthAuditError("intent result omits intent list")
        for item in intents:
            if not isinstance(item, dict):
                raise BulletBirthAuditError("intent item is not an object")
            status = str(item.get("intent_status"))
            status_counts[status] += 1
            by_phase[phase][f"status:{status}"] += 1
            dependencies = item.get("dependencies")
            if not isinstance(dependencies, list) or not all(
                isinstance(value, str) for value in dependencies
            ):
                raise BulletBirthAuditError(
                    "intent dependencies are not strings"
                )
            dependency_counts.update(dependencies)
            signature = (
                audit["gameplay_epoch"],
                pointer,
                item.get("instruction_address"),
                item.get("instruction_time"),
                item.get("opcode"),
                status,
                item.get("requested_bullets"),
                tuple(dependencies),
                scope["phase"],
            )
            relative = item.get("activation_frame_support")
            if (
                not isinstance(relative, list)
                or len(relative) != 2
                or not all(type(value) is int for value in relative)
                or type(ecl_before) is not int
                or type(ecl_after) is not int
            ):
                untimed_signatures.add(signature)
                by_phase[phase]["untimed_sightings"] += 1
                continue
            by_phase[phase]["timed_sightings"] += 1
            support = (
                ecl_before + relative[0],
                ecl_after + relative[1],
            )
            if support[1] < support[0]:
                raise BulletBirthAuditError("intent support regresses")
            sightings[signature].append(
                {
                    "support": support,
                    "first_observed_frame": audit["frame"],
                }
            )

    events: list[dict[str, Any]] = []
    for signature in sorted(sightings, key=repr):
        entries = sorted(
            sightings[signature],
            key=lambda entry: (
                entry["support"][0],
                entry["support"][1],
                entry["first_observed_frame"],
            ),
        )
        clusters: list[dict[str, int]] = []
        for entry in entries:
            start, end = entry["support"]
            if clusters and start <= clusters[-1]["end"]:
                clusters[-1]["start"] = min(
                    clusters[-1]["start"],
                    start,
                )
                clusters[-1]["end"] = max(clusters[-1]["end"], end)
                clusters[-1]["sightings"] += 1
                clusters[-1]["first_observed_frame"] = min(
                    clusters[-1]["first_observed_frame"],
                    entry["first_observed_frame"],
                )
            else:
                clusters.append(
                    {
                        "start": start,
                        "end": end,
                        "sightings": 1,
                        "first_observed_frame": entry[
                            "first_observed_frame"
                        ],
                    }
                )
        (
            epoch,
            pointer,
            address,
            instruction_time,
            opcode,
            status,
            requested,
            dependencies,
            phase,
        ) = signature
        for cluster in clusters:
            events.append(
                {
                    "gameplay_epoch": epoch,
                    "spell_enemy_pointer": pointer,
                    "instruction_address": address,
                    "instruction_time": instruction_time,
                    "opcode": opcode,
                    "intent_status": status,
                    "requested_bullets": requested,
                    "dependencies": dependencies,
                    "phase": phase,
                    "support": (
                        cluster["start"],
                        cluster["end"],
                    ),
                    "sightings": cluster["sightings"],
                    "first_observed_frame": cluster[
                        "first_observed_frame"
                    ],
                }
            )
            by_phase[str(phase)]["deduplicated_timed_events"] += 1
            by_phase[str(phase)]["timed_event_sightings"] += int(
                cluster["sightings"]
            )
    events.sort(
        key=lambda event: (
            event["gameplay_epoch"],
            event["support"],
            event["instruction_address"],
            event["opcode"],
        )
    )
    return (
        events,
        status_counts,
        stop_counts,
        dependency_counts,
        len(untimed_signatures),
        dict(by_phase),
        dict(read_ms_by_phase),
    )


def analyze_trace(trace_path: Path) -> dict[str, object]:
    audits, decisions, trace_sha256, trace_bytes = _read_trace(trace_path)
    (
        events,
        intent_statuses,
        stop_reasons,
        intent_dependencies,
        untimed_intent_signatures,
        intent_by_phase,
        velocity_read_ms_by_phase,
    ) = _intent_events(audits, decisions)

    event_by_epoch: defaultdict[int, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        event_by_epoch[event["gameplay_epoch"]].append(event)

    evidence_kinds: Counter[str] = Counter()
    observation_statuses: Counter[str] = Counter()
    classifications: Counter[str] = Counter()
    residuals: Counter[str] = Counter()
    capture_spans: Counter[int] = Counter()
    by_phase: defaultdict[str, Counter[str]] = defaultdict(Counter)
    observation_ms: list[float] = []
    observation_cpu_ms: list[float] = []
    intent_ms: list[float] = []
    build_ms: list[float] = []
    pre_emit_total_ms: list[float] = []
    emit_ms: list[float] = []
    ages: list[float] = []
    evidence_per_row: list[float] = []
    unmatched_samples: list[dict[str, object]] = []
    ambiguous_samples: list[dict[str, object]] = []
    observation_errors = 0
    intent_errors = 0
    active_spell_scope_rows = 0
    omitted_sources: set[str] = set()
    trace_schema_versions: Counter[int] = Counter()
    observation_backends: Counter[str] = Counter()
    deferred_state_statuses: Counter[str] = Counter()
    deferred_state_values: Counter[str] = Counter()
    observation_by_evidence: defaultdict[str, list[float]] = defaultdict(list)
    observation_cpu_by_evidence: defaultdict[str, list[float]] = defaultdict(
        list
    )
    build_by_evidence: defaultdict[str, list[float]] = defaultdict(list)
    pre_emit_by_evidence: defaultdict[str, list[float]] = defaultdict(list)
    emit_by_previous_evidence: defaultdict[str, list[float]] = defaultdict(
        list
    )
    previous_evidence_count: int | None = None

    for audit in audits:
        trace_schema_versions[int(audit["schema_version"])] += 1
        observation_backends[
            str(
                audit.get(
                    "observation_backend",
                    "schema_v1_v4_unrecorded",
                )
            )
        ] += 1
        scope = _scope_for(audit, decisions)
        phase = str(scope["phase"])
        pointer = audit.get("spell_enemy_pointer")
        if type(pointer) is int and pointer:
            active_spell_scope_rows += 1
        source_scope = audit.get("scope")
        if isinstance(source_scope, dict):
            omitted = source_scope.get("omitted_sources")
            if isinstance(omitted, list):
                omitted_sources.update(
                    value for value in omitted if isinstance(value, str)
                )
        deferred_state = audit.get("deferred_fire_state")
        if isinstance(deferred_state, dict):
            deferred_state_statuses[
                str(deferred_state.get("status"))
            ] += 1
            active = deferred_state.get("active")
            value = (
                "unknown"
                if active is None
                else "enabled"
                if active is True
                else "disabled"
            )
            deferred_state_values[value] += 1
        else:
            deferred_state_statuses["schema_v1_unobserved"] += 1
            deferred_state_values["unknown"] += 1
        if audit.get("observation_error") is not None:
            observation_errors += 1
        if audit.get("intent_error") is not None:
            intent_errors += 1
        timing = audit.get("timing_ms")
        row_timing: dict[str, float] = {}
        if isinstance(timing, dict):
            for field, target in (
                ("observation", observation_ms),
                ("observation_cpu", observation_cpu_ms),
                ("intent", intent_ms),
                ("build", build_ms),
                ("pre_emit_total", pre_emit_total_ms),
                ("previous_emit", emit_ms),
            ):
                value = timing.get(field)
                if isinstance(value, (int, float)) and math.isfinite(value):
                    numeric = float(value)
                    target.append(numeric)
                    row_timing[field] = numeric
        observation = audit.get("observation")
        if not isinstance(observation, dict):
            continue
        capture_span = observation.get("capture_span")
        if type(capture_span) is int:
            capture_spans[capture_span] += 1
        evidence = _evidence_items(observation)
        evidence_count = len(evidence)
        evidence_per_row.append(float(evidence_count))
        bucket = _evidence_count_bucket(evidence_count)
        for field, target in (
            ("observation", observation_by_evidence),
            ("observation_cpu", observation_cpu_by_evidence),
            ("build", build_by_evidence),
            ("pre_emit_total", pre_emit_by_evidence),
        ):
            value = row_timing.get(field)
            if value is not None:
                target[bucket].append(value)
        previous_emit = row_timing.get("previous_emit")
        if previous_emit is not None and previous_evidence_count is not None:
            emit_by_previous_evidence[
                _evidence_count_bucket(previous_evidence_count)
            ].append(previous_emit)
        previous_evidence_count = evidence_count
        for item in evidence:
            kind = str(item.get("kind"))
            status = str(item.get("observation_status"))
            evidence_kinds[kind] += 1
            observation_statuses[status] += 1
            age = item.get("age")
            if isinstance(age, (int, float)) and math.isfinite(age):
                ages.append(float(age))
            by_phase[phase]["all_evidence"] += 1
            if kind != "activation_edge":
                residuals[f"evidence_kind:{kind}"] += 1
                by_phase[phase][f"evidence_kind:{kind}"] += 1
                continue
            support = item.get("activation_support")
            if (
                not isinstance(support, list)
                or len(support) != 2
                or not all(type(value) is int for value in support)
                or support[1] < support[0]
            ):
                raise BulletBirthAuditError(
                    "activation edge has invalid support"
                )
            candidates = [
                event
                for event in event_by_epoch[audit["gameplay_epoch"]]
                if (
                    event["support"][0] <= support[1]
                    and support[0] <= event["support"][1]
                )
            ]
            if not candidates:
                classification = "unmatched"
                if not pointer:
                    residuals["active_spell_main_vm_absent"] += 1
                else:
                    residuals[
                        "no_temporally_overlapping_timed_intent"
                    ] += 1
            elif len(candidates) > 1:
                classification = "ambiguous"
                residuals["multiple_temporal_intents"] += 1
            else:
                event = candidates[0]
                point_observation = support[0] == support[1]
                point_intent = (
                    event["support"][0] == event["support"][1]
                )
                classification = (
                    "exact"
                    if (
                        point_observation
                        and point_intent
                        and support[0] == event["support"][0]
                    )
                    else "support"
                )
                if classification == "support":
                    residuals["temporal_support_not_point"] += 1
                for dependency in event["dependencies"]:
                    residuals[f"intent_dependency:{dependency}"] += 1
                residuals["omitted_source_competition"] += 1
            if status != "complete":
                residuals[f"observation_status:{status}"] += 1
            classifications[classification] += 1
            by_phase[phase]["activation_edges"] += 1
            by_phase[phase][classification] += 1
            sample = {
                "frame": audit["frame"],
                "gameplay_epoch": audit["gameplay_epoch"],
                "phase": phase,
                "slot": item.get("slot"),
                "age": age,
                "activation_support": support,
                "candidate_event_supports": [
                    list(event["support"]) for event in candidates[:5]
                ],
                "candidate_count": len(candidates),
            }
            if classification == "unmatched" and len(unmatched_samples) < MAX_SAMPLES:
                unmatched_samples.append(sample)
            if classification == "ambiguous" and len(ambiguous_samples) < MAX_SAMPLES:
                ambiguous_samples.append(sample)

    phase_report = {
        phase: _counter(counts)
        for phase, counts in sorted(by_phase.items())
    }
    activation_edges = sum(classifications.values())
    unique_temporal = classifications["exact"] + classifications["support"]
    matched_temporal = unique_temporal + classifications["ambiguous"]
    observation_timing = _distribution(observation_ms)
    validation_passed = observation_errors == 0 and intent_errors == 0
    observer_budget_passed = bool(
        observation_timing["p95"] is not None
        and observation_timing["p99"] is not None
        and observation_timing["max"] is not None
        and observation_timing["p95"] <= OBSERVER_P95_LIMIT_MS
        and observation_timing["p99"] <= OBSERVER_P99_LIMIT_MS
        and observation_timing["max"] <= OBSERVER_MAX_LIMIT_MS
    )
    timed_intent_available = bool(events)
    return {
        "schema": SCHEMA,
        "passed": (
            validation_passed
            and observer_budget_passed
            and timed_intent_available
        ),
        "gates": {
            "validation_passed": validation_passed,
            "observer_budget_passed": observer_budget_passed,
            "timed_intent_available": timed_intent_available,
            "observer_limits_ms": {
                "p95": OBSERVER_P95_LIMIT_MS,
                "p99": OBSERVER_P99_LIMIT_MS,
                "max": OBSERVER_MAX_LIMIT_MS,
            },
        },
        "source": {
            "trace_name": trace_path.name,
            "trace_bytes": trace_bytes,
            "trace_sha256": trace_sha256,
        },
        "input": {
            "audit_rows": len(audits),
            "decision_scopes": len(decisions),
            "active_spell_main_vm_rows": active_spell_scope_rows,
            "observation_errors": observation_errors,
            "intent_errors": intent_errors,
            "trace_schema_versions": _counter(trace_schema_versions),
            "observation_backends": _counter(observation_backends),
            "deferred_fire_state_statuses": _counter(
                deferred_state_statuses
            ),
            "deferred_fire_state_values": _counter(
                deferred_state_values
            ),
        },
        "observation": {
            "evidence_kinds": _counter(evidence_kinds),
            "observation_statuses": _counter(observation_statuses),
            "capture_spans": _counter(capture_spans),
            "evidence_per_row": _distribution(evidence_per_row),
            "age": _distribution(ages),
        },
        "intent": {
            "status_sightings": _counter(intent_statuses),
            "stop_reasons": _counter(stop_reasons),
            "dependency_sightings": _counter(intent_dependencies),
            "timed_event_sightings": sum(
                int(event["sightings"]) for event in events
            ),
            "deduplicated_timed_events": len(events),
            "untimed_intent_signatures": untimed_intent_signatures,
        },
        "join": {
            "classification": _counter(classifications),
            "activation_edges": activation_edges,
            "unique_temporal_matches": unique_temporal,
            "any_temporal_matches": matched_temporal,
            "unique_temporal_fraction": (
                round(unique_temporal / activation_edges, 6)
                if activation_edges
                else None
            ),
            "residual_reasons": _counter(residuals),
            "unmatched_samples": unmatched_samples,
            "ambiguous_samples": ambiguous_samples,
            "semantics": {
                "exact": "one point intent equals one point observation",
                "support": "one intent interval overlaps the observation",
                "ambiguous": "multiple intent intervals overlap",
                "unmatched": "no timed main-VM intent interval overlaps",
                "causal_authority": "none",
            },
        },
        "by_phase_at_capture": phase_report,
        "by_phase_at_intent": {
            phase: _counter(counts)
            for phase, counts in sorted(intent_by_phase.items())
        },
        "velocity_lookahead_read_ms_by_phase": {
            phase: _distribution(values)
            for phase, values in sorted(velocity_read_ms_by_phase.items())
        },
        "timing_ms": {
            "observation": observation_timing,
            "observation_cpu": _distribution(observation_cpu_ms),
            "intent": _distribution(intent_ms),
            "build": _distribution(build_ms),
            "pre_emit_total": _distribution(pre_emit_total_ms),
            "previous_emit": _distribution(emit_ms),
        },
        "timing_by_evidence_count": {
            "semantics": {
                "observation_build_pre_emit": (
                    "bucketed by the current audit evidence count"
                ),
                "previous_emit": (
                    "bucketed by the preceding audit evidence count"
                ),
            },
            "observation": {
                bucket: _distribution(values)
                for bucket, values in sorted(
                    observation_by_evidence.items()
                )
            },
            "observation_cpu": {
                bucket: _distribution(values)
                for bucket, values in sorted(
                    observation_cpu_by_evidence.items()
                )
            },
            "build": {
                bucket: _distribution(values)
                for bucket, values in sorted(build_by_evidence.items())
            },
            "pre_emit_total": {
                bucket: _distribution(values)
                for bucket, values in sorted(pre_emit_by_evidence.items())
            },
            "previous_emit": {
                bucket: _distribution(values)
                for bucket, values in sorted(
                    emit_by_previous_evidence.items()
                )
            },
        },
        "scope": {
            "intent_source": "active_spell_enemy_main_vm_only",
            "omitted_sources": sorted(omitted_sources),
            "future_geometry_authority": "none",
            "hazard_coverage_authority": "none",
            "physical_action_authority": "none",
        },
    }


def canonical_report_bytes(report: dict[str, object]) -> bytes:
    return (
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = analyze_trace(args.trace)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical_report_bytes(report))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
