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


SCHEMA = "th08-bullet-birth-residual-audit-v1"
TRACE_KIND = "bullet_birth_audit"
TRACE_ROLE = "trace_only_no_action_authority"
TRACE_SCHEMA_VERSIONS = frozenset((1, 2))
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
    scope = {
        "stage_route_index": values["stage_route_index"],
        "spell_id": spell_id,
        "spell_name": spell_name,
        "phase": _phase_key(values["stage_route_index"], spell_id),
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


def _intent_events(
    audits: list[dict[str, Any]],
    decisions: dict[tuple[int, int], dict[str, object]],
) -> tuple[
    list[dict[str, Any]],
    Counter[str],
    Counter[str],
    Counter[str],
    int,
]:
    sightings: defaultdict[tuple[object, ...], list[dict[str, Any]]] = (
        defaultdict(list)
    )
    status_counts: Counter[str] = Counter()
    stop_counts: Counter[str] = Counter()
    dependency_counts: Counter[str] = Counter()
    untimed_signatures: set[tuple[object, ...]] = set()

    for audit in audits:
        intent_result = audit.get("intent")
        if not isinstance(intent_result, dict):
            continue
        stop_counts[str(intent_result.get("stop_reason"))] += 1
        scope = _scope_for(audit, decisions)
        alignment = audit.get("alignment")
        if not isinstance(alignment, dict):
            raise BulletBirthAuditError("audit alignment is not an object")
        ecl_before = alignment.get("ecl_frame_before")
        ecl_after = alignment.get("ecl_frame_after")
        pointer = audit.get("spell_enemy_pointer")
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
                continue
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
    )


def analyze_trace(trace_path: Path) -> dict[str, object]:
    audits, decisions, trace_sha256, trace_bytes = _read_trace(trace_path)
    (
        events,
        intent_statuses,
        stop_reasons,
        intent_dependencies,
        untimed_intent_signatures,
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
    intent_ms: list[float] = []
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
    deferred_state_statuses: Counter[str] = Counter()
    deferred_state_values: Counter[str] = Counter()

    for audit in audits:
        trace_schema_versions[int(audit["schema_version"])] += 1
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
        if isinstance(timing, dict):
            for field, target in (
                ("observation", observation_ms),
                ("intent", intent_ms),
                ("previous_emit", emit_ms),
            ):
                value = timing.get(field)
                if isinstance(value, (int, float)) and math.isfinite(value):
                    target.append(float(value))
        observation = audit.get("observation")
        if not isinstance(observation, dict):
            continue
        capture_span = observation.get("capture_span")
        if type(capture_span) is int:
            capture_spans[capture_span] += 1
        evidence = observation.get("evidence")
        if not isinstance(evidence, list):
            raise BulletBirthAuditError("observation evidence is not a list")
        evidence_per_row.append(float(len(evidence)))
        for item in evidence:
            if not isinstance(item, dict):
                raise BulletBirthAuditError("birth evidence is not an object")
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
        "timing_ms": {
            "observation": observation_timing,
            "intent": _distribution(intent_ms),
            "previous_emit": _distribution(emit_ms),
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
