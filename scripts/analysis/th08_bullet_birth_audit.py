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

from analysis.derived_pattern_source_join import (
    build_derived_pattern_source_join,
)


SCHEMA = "th08-bullet-birth-residual-audit-v8"
TRACE_KIND = "bullet_birth_audit"
TRACE_ROLE = "trace_only_no_action_authority"
TRACE_SCHEMA_VERSIONS = frozenset((1, 2, 3, 4, 5, 6, 7, 8, 9, 10))
NATIVE_CALL_MODES = frozenset(("gil-released", "gil-held"))
NATIVE_PHASES = ("prepare", "native_call", "materialize")
THREAD_CYCLE_SOURCE_WINDOWS = "windows_query_thread_cycle_time"
THREAD_CYCLE_SOURCES = frozenset(
    (
        THREAD_CYCLE_SOURCE_WINDOWS,
        "unavailable_non_windows",
        "query_failed",
    )
)
FUTURE_STATES = frozenset(("absent", "done", "inflight"))
CONTENTION_FUTURES = (
    "corridor_future",
    "survival_future",
    "enemy_future",
)
CONTENTION_OMITTED_SOURCES = frozenset(
    (
        "game_process",
        "os_scheduler_and_other_processes",
        "native_internal_workers_after_endpoint_ambiguity",
        "candidate_supplemental_and_prewarm_services",
        "allocator_and_page_faults",
    )
)
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
    lookahead_prefix_event_count = 0
    lookahead_instructions_scanned = 0
    lookahead_coverage_status: str | None = None
    lookahead_lowering_status: str | None = None
    lookahead_unknown_from_frame: int | None = None
    lookahead_tagged_bullets = 0
    lookahead_metadata_valid = False
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
            raw_prefix_events = lookahead.get("prefix_events")
            if isinstance(raw_prefix_events, list):
                lookahead_prefix_event_count = len(raw_prefix_events)
            raw_scanned = lookahead.get("instructions_scanned")
            if type(raw_scanned) is int and raw_scanned >= 0:
                lookahead_instructions_scanned = raw_scanned
            lookahead_metadata_valid = _valid_velocity_lookahead_coverage(
                lookahead
            )
            raw_coverage_status = lookahead.get("coverage_status")
            lookahead_coverage_status = (
                raw_coverage_status
                if isinstance(raw_coverage_status, str)
                else None
            )
            raw_lowering_status = lookahead.get("lowering_status")
            lookahead_lowering_status = (
                raw_lowering_status
                if isinstance(raw_lowering_status, str)
                else None
            )
            raw_horizon_covered = lookahead.get("horizon_covered")
            if (
                lookahead_coverage_status is None
                and type(raw_horizon_covered) is bool
            ):
                if raw_horizon_covered:
                    lookahead_coverage_status = "legacy_declared_complete"
                    lookahead_lowering_status = (
                        "legacy_complete_events_lowered_unchecked"
                    )
                else:
                    lookahead_coverage_status = "legacy_declared_unknown"
                    lookahead_lowering_status = (
                        "legacy_incomplete_prefix_lowered_as_schedule"
                    )
                lookahead_prefix_event_count = lookahead_event_count
            raw_unknown_from = lookahead.get("unknown_from_frame")
            lookahead_unknown_from_frame = (
                raw_unknown_from
                if type(raw_unknown_from) is int
                else None
            )
            raw_tagged_bullets = lookahead.get("tagged_bullets")
            if type(raw_tagged_bullets) is int and raw_tagged_bullets >= 0:
                lookahead_tagged_bullets = raw_tagged_bullets
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
        "velocity_lookahead_prefix_event_count": (
            lookahead_prefix_event_count
        ),
        "velocity_lookahead_instructions_scanned": (
            lookahead_instructions_scanned
        ),
        "velocity_lookahead_coverage_status": lookahead_coverage_status,
        "velocity_lookahead_lowering_status": lookahead_lowering_status,
        "velocity_lookahead_unknown_from_frame": (
            lookahead_unknown_from_frame
        ),
        "velocity_lookahead_tagged_bullets": lookahead_tagged_bullets,
        "velocity_lookahead_metadata_valid": lookahead_metadata_valid,
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


def _contention_overlap(
    contention: dict[str, Any],
) -> tuple[str, list[str], str]:
    definite: list[str] = []
    ambiguous: list[str] = []
    pattern: list[str] = []
    for future_name in CONTENTION_FUTURES:
        endpoints = contention[future_name]
        assert isinstance(endpoints, dict)
        before = str(endpoints["before"])
        after = str(endpoints["after"])
        pattern.append(f"{future_name}:{before}->{after}")
        if before == after == "inflight":
            definite.append(future_name)
        elif "inflight" in {before, after}:
            ambiguous.append(future_name)
    if definite:
        classification = "definite_known_future_overlap"
        names = definite
    elif ambiguous:
        classification = "ambiguous_endpoint_overlap"
        names = ambiguous
    else:
        classification = "no_known_future_overlap"
        names = []
    return classification, names, "|".join(pattern)


def _valid_velocity_lookahead_coverage(
    lookahead: dict[str, Any],
) -> bool:
    horizon_covered = lookahead.get("horizon_covered")
    status = lookahead.get("coverage_status")
    horizon = lookahead.get("requested_horizon_frames")
    stop_frame = lookahead.get("stop_frame")
    covered_through = lookahead.get("covered_through_frame")
    unknown_from = lookahead.get("unknown_from_frame")
    result_kind = lookahead.get("result_kind")
    stop_reason = lookahead.get("stop_reason")
    prefix_events = lookahead.get("prefix_events")
    lowered_events = lookahead.get("events")
    lowering_status = lookahead.get("lowering_status")
    if (
        type(horizon_covered) is not bool
        or type(horizon) is not int
        or horizon < 0
        or type(stop_frame) is not int
        or not 0 <= stop_frame <= horizon
        or type(covered_through) is not int
        or not isinstance(prefix_events, list)
        or not isinstance(lowered_events, list)
    ):
        return False
    if horizon_covered:
        return (
            status == "complete"
            and stop_reason in {"horizon", "terminate"}
            and covered_through == horizon
            and unknown_from is None
            and result_kind == "complete_schedule"
            and lowering_status == "complete_schedule_lowered"
            and prefix_events == lowered_events
        )
    return (
        status == "unknown"
        and stop_reason not in {"horizon", "terminate"}
        and isinstance(stop_reason, str)
        and covered_through == max(0, stop_frame - 1)
        and unknown_from == covered_through + 1
        and result_kind == "prefix_only"
        and lowering_status == "incomplete_prefix_not_lowered"
        and not lowered_events
    )


def _validate_intent_coverage(
    intent: dict[str, Any],
    *,
    line_number: int,
) -> None:
    coverage = intent.get("coverage")
    if not isinstance(coverage, dict):
        raise BulletBirthAuditError(
            f"line {line_number}: schema-v8 intent omits coverage"
        )
    horizon_covered = intent.get("horizon_covered")
    status = coverage.get("status")
    horizon = coverage.get("requested_horizon_frames")
    stop_frame = coverage.get("stop_frame")
    covered_through = coverage.get("covered_through_frame")
    unknown_from = coverage.get("unknown_from_frame")
    result_kind = coverage.get("result_kind")
    stop_reason = intent.get("stop_reason")
    if (
        type(horizon_covered) is not bool
        or type(horizon) is not int
        or horizon < 0
        or type(stop_frame) is not int
        or not 0 <= stop_frame <= horizon
        or type(covered_through) is not int
    ):
        raise BulletBirthAuditError(
            f"line {line_number}: schema-v8 intent has invalid coverage"
        )
    expected_covered = horizon if horizon_covered else max(0, stop_frame - 1)
    expected_unknown = None if horizon_covered else expected_covered + 1
    expected_status = "complete" if horizon_covered else "unknown"
    expected_kind = "complete_schedule" if horizon_covered else "prefix_only"
    if (
        status != expected_status
        or (
            horizon_covered
            and stop_reason not in {"horizon", "terminate"}
        )
        or (
            not horizon_covered
            and (
                not isinstance(stop_reason, str)
                or stop_reason in {"horizon", "terminate"}
            )
        )
        or covered_through != expected_covered
        or unknown_from != expected_unknown
        or result_kind != expected_kind
    ):
        raise BulletBirthAuditError(
            f"line {line_number}: schema-v8 intent coverage is inconsistent"
        )


def _validate_derived_source_observation(
    record: dict[str, Any],
    *,
    line_number: int,
) -> None:
    observation = record.get("derived_source_observation")
    error = record.get("derived_source_error")
    diagnostics = record.get("derived_source_diagnostics")
    backend = record.get("observation_backend")
    timing = record.get("timing_ms")
    if error is not None:
        if not isinstance(error, str) or observation is not None:
            raise BulletBirthAuditError(
                f"line {line_number}: invalid derived-source failure"
            )
        if diagnostics is not None:
            raise BulletBirthAuditError(
                f"line {line_number}: failed derived-source scan publishes "
                "diagnostics"
            )
        return
    if not isinstance(observation, dict):
        raise BulletBirthAuditError(
            f"line {line_number}: schema-v10 row omits derived-source observation"
        )
    if (
        observation.get("schema_version") != 1
        or observation.get("role") != TRACE_ROLE
    ):
        raise BulletBirthAuditError(
            f"line {line_number}: invalid derived-source schema or role"
        )
    active_count = observation.get("active_count")
    candidate_count = observation.get("candidate_count")
    candidates = observation.get("candidates")
    if (
        type(active_count) is not int
        or not 0 <= active_count <= 1536
        or type(candidate_count) is not int
        or not 0 <= candidate_count <= active_count
        or not isinstance(candidates, list)
        or len(candidates) != candidate_count
    ):
        raise BulletBirthAuditError(
            f"line {line_number}: invalid derived-source counts"
        )
    for candidate in candidates:
        if (
            not isinstance(candidate, dict)
            or candidate.get("classification")
            != "derived_pattern_ready_candidate"
            or candidate.get("authority") != "trace_only"
            or type(candidate.get("slot")) is not int
            or not 0 <= candidate["slot"] < 1536
            or type(candidate.get("geometry_finite")) is not bool
        ):
            raise BulletBirthAuditError(
                f"line {line_number}: invalid derived-source candidate"
            )
        position = candidate.get("position")
        if candidate["geometry_finite"]:
            if (
                not isinstance(position, list)
                or len(position) != 2
                or any(
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not math.isfinite(value)
                    for value in position
                )
            ):
                raise BulletBirthAuditError(
                    f"line {line_number}: invalid derived-source position"
                )
        elif position is not None:
            raise BulletBirthAuditError(
                f"line {line_number}: nonfinite source publishes geometry"
            )
        for field in ("first_words", "second_words"):
            words = candidate.get(field)
            if (
                not isinstance(words, list)
                or len(words) != 6
                or any(
                    type(value) is not int or not 0 <= value <= 0xFFFFFFFF
                    for value in words
                )
            ):
                raise BulletBirthAuditError(
                    f"line {line_number}: invalid derived-source record words"
                )
        pattern = candidate.get("pattern")
        if not isinstance(pattern, dict):
            raise BulletBirthAuditError(
                f"line {line_number}: derived-source pattern is missing"
            )
        count_1 = pattern.get("count_1")
        count_2 = pattern.get("count_2")
        predicted = pattern.get("predicted_child_count")
        if (
            type(count_1) is not int
            or type(count_2) is not int
            or type(predicted) is not int
            or predicted != max(0, count_1) * max(0, count_2)
        ):
            raise BulletBirthAuditError(
                f"line {line_number}: inconsistent derived-source child count"
            )
    if not isinstance(timing, dict):
        raise BulletBirthAuditError(
            f"line {line_number}: derived-source timing is missing"
        )
    source_ms = timing.get("derived_source_observation")
    combined_ms = timing.get("combined_pool_observation")
    birth_ms = timing.get("observation")
    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value < 0.0
        for value in (source_ms, combined_ms, birth_ms)
    ) or not math.isclose(
        float(combined_ms),
        float(source_ms) + float(birth_ms),
        rel_tol=1e-9,
        abs_tol=1e-6,
    ):
        raise BulletBirthAuditError(
            f"line {line_number}: derived-source timing does not reconcile"
        )
    if backend == "python":
        if diagnostics is not None:
            raise BulletBirthAuditError(
                f"line {line_number}: Python derived-source scan fabricates "
                "native diagnostics"
            )
        return
    if not isinstance(diagnostics, dict):
        raise BulletBirthAuditError(
            f"line {line_number}: native derived-source diagnostics are missing"
        )
    segments = diagnostics.get("native_segments_ms")
    if not isinstance(segments, dict):
        raise BulletBirthAuditError(
            f"line {line_number}: derived-source diagnostics omit segments"
        )
    total = 0.0
    for field in (
        "prepare",
        "native_call",
        "materialize",
        "controller_residual",
    ):
        value = segments.get(field)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value < 0.0
        ):
            raise BulletBirthAuditError(
                f"line {line_number}: invalid derived-source segment {field}"
            )
        total += float(value)
    if not math.isclose(
        total,
        float(source_ms),
        rel_tol=1e-9,
        abs_tol=1e-6,
    ):
        raise BulletBirthAuditError(
            f"line {line_number}: derived-source segments do not reconcile"
        )


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
        record.get("schema_version") in {5, 6, 7, 8, 9, 10}
        and record.get("observation_backend") not in {"python", "native"}
    ):
        raise BulletBirthAuditError(
            f"line {line_number}: audit omits a valid observation backend"
        )
    if record.get("schema_version") in {7, 8, 9, 10}:
        backend = record.get("observation_backend")
        native_call_mode = record.get("native_call_mode")
        if backend == "native" and native_call_mode not in NATIVE_CALL_MODES:
            raise BulletBirthAuditError(
                f"line {line_number}: native audit omits a valid call mode"
            )
        if backend == "python" and native_call_mode is not None:
            raise BulletBirthAuditError(
                f"line {line_number}: Python audit fabricates a native call mode"
            )
    if record.get("schema_version") in {6, 7, 8, 9, 10}:
        backend = record.get("observation_backend")
        diagnostics = record.get("observation_diagnostics")
        if backend == "python":
            if diagnostics is not None:
                raise BulletBirthAuditError(
                    f"line {line_number}: Python audit fabricates "
                    "native diagnostics"
                )
        elif record.get("observation_error") is None:
            if not isinstance(record.get("observation"), dict):
                raise BulletBirthAuditError(
                    f"line {line_number}: successful native audit "
                    "omits its observation"
                )
            _validate_native_diagnostics(
                diagnostics,
                timing=record.get("timing_ms"),
                line_number=line_number,
                require_thread_cycles=record.get("schema_version") in {9, 10},
            )
        elif diagnostics is not None:
            raise BulletBirthAuditError(
                f"line {line_number}: failed native audit publishes "
                "diagnostics"
            )
    if record.get("schema_version") in {8, 9, 10}:
        intent = record.get("intent")
        if isinstance(intent, dict):
            _validate_intent_coverage(intent, line_number=line_number)
    if record.get("schema_version") in {9, 10}:
        _validate_observer_contention(
            record.get("observer_contention"),
            line_number=line_number,
        )
    if record.get("schema_version") == 10:
        _validate_derived_source_observation(
            record,
            line_number=line_number,
        )
    for field in ("frame", "snapshot_frame", "gameplay_epoch"):
        if type(record.get(field)) is not int:
            raise BulletBirthAuditError(
                f"line {line_number}: audit omits integer {field}"
            )
    return record


def _validate_native_diagnostics(
    diagnostics: Any,
    *,
    timing: Any,
    line_number: int,
    require_thread_cycles: bool = False,
) -> None:
    if not isinstance(diagnostics, dict):
        raise BulletBirthAuditError(
            f"line {line_number}: successful native audit omits diagnostics"
        )
    segments = diagnostics.get("native_segments_ms")
    if not isinstance(segments, dict):
        raise BulletBirthAuditError(
            f"line {line_number}: native diagnostics omit segments"
        )
    segment_total = 0.0
    for field in (
        "prepare",
        "native_call",
        "materialize",
        "controller_residual",
    ):
        value = segments.get(field)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value < 0.0
        ):
            raise BulletBirthAuditError(
                f"line {line_number}: invalid native segment {field}"
            )
        segment_total += float(value)
    if not isinstance(timing, dict):
        raise BulletBirthAuditError(
            f"line {line_number}: native diagnostics omit total timing"
        )
    observation_ms = timing.get("observation")
    if (
        isinstance(observation_ms, bool)
        or not isinstance(observation_ms, (int, float))
        or not math.isfinite(observation_ms)
        or observation_ms < 0.0
        or not math.isclose(
            segment_total,
            float(observation_ms),
            rel_tol=1e-9,
            abs_tol=1e-6,
        )
    ):
        raise BulletBirthAuditError(
            f"line {line_number}: native segments do not reconcile"
        )
    completed = diagnostics.get("gc_completed")
    if not isinstance(completed, dict):
        raise BulletBirthAuditError(
            f"line {line_number}: native diagnostics omit GC counts"
        )
    for phase in ("prepare", "native_call", "materialize"):
        counts = completed.get(phase)
        if (
            not isinstance(counts, list)
            or len(counts) != 3
            or any(type(value) is not int or value < 0 for value in counts)
        ):
            raise BulletBirthAuditError(
                f"line {line_number}: invalid {phase} GC counts"
            )
    if require_thread_cycles:
        _validate_thread_cycles(
            diagnostics.get("thread_cycles"),
            line_number=line_number,
        )


def _validate_thread_cycles(
    cycles: Any,
    *,
    line_number: int,
) -> bool:
    if not isinstance(cycles, dict):
        raise BulletBirthAuditError(
            f"line {line_number}: native diagnostics omit thread cycles"
        )
    source = cycles.get("source")
    if source not in THREAD_CYCLE_SOURCES:
        raise BulletBirthAuditError(
            f"line {line_number}: invalid thread-cycle source"
        )
    values = [cycles.get(phase) for phase in NATIVE_PHASES]
    if source == THREAD_CYCLE_SOURCE_WINDOWS:
        if any(type(value) is not int or value < 0 for value in values):
            raise BulletBirthAuditError(
                f"line {line_number}: invalid Windows thread-cycle delta"
            )
        return True
    if any(value is not None for value in values):
        raise BulletBirthAuditError(
            f"line {line_number}: unavailable thread cycles fabricate deltas"
        )
    return False


def _validate_observer_contention(
    contention: Any,
    *,
    line_number: int,
) -> None:
    if not isinstance(contention, dict):
        raise BulletBirthAuditError(
            f"line {line_number}: schema-v9 row omits observer contention"
        )
    for future_name in CONTENTION_FUTURES:
        endpoints = contention.get(future_name)
        if (
            not isinstance(endpoints, dict)
            or endpoints.get("before") not in FUTURE_STATES
            or endpoints.get("after") not in FUTURE_STATES
        ):
            raise BulletBirthAuditError(
                f"line {line_number}: invalid {future_name} endpoints"
            )
    omitted = contention.get("omitted_sources")
    if (
        not isinstance(omitted, list)
        or len(omitted) != len(CONTENTION_OMITTED_SOURCES)
        or frozenset(omitted) != CONTENTION_OMITTED_SOURCES
    ):
        raise BulletBirthAuditError(
            f"line {line_number}: invalid contention omitted sources"
        )


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
        velocity_prefix_events = scope.get(
            "velocity_lookahead_prefix_event_count"
        )
        if type(velocity_prefix_events) is int and velocity_prefix_events:
            by_phase[phase]["velocity_prefix_event_rows"] += 1
            by_phase[phase]["velocity_prefix_events"] += (
                velocity_prefix_events
            )
        velocity_coverage = scope.get(
            "velocity_lookahead_coverage_status"
        )
        if isinstance(velocity_coverage, str):
            by_phase[phase][
                f"velocity_lookahead_coverage:{velocity_coverage}"
            ] += 1
        velocity_lowering = scope.get(
            "velocity_lookahead_lowering_status"
        )
        if isinstance(velocity_lowering, str):
            by_phase[phase][
                f"velocity_lookahead_lowering:{velocity_lowering}"
            ] += 1
        if (
            audit["schema_version"] in {8, 9, 10}
            and pointer
            and not scope.get("velocity_lookahead_metadata_valid")
        ):
            raise BulletBirthAuditError(
                "schema-v8+ active-main-VM row omits valid callback coverage"
            )
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
    derived_source_join = build_derived_pattern_source_join(audits)
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
    derived_source_ms: list[float] = []
    combined_pool_observation_ms: list[float] = []
    intent_ms: list[float] = []
    build_ms: list[float] = []
    pre_emit_total_ms: list[float] = []
    emit_ms: list[float] = []
    ages: list[float] = []
    evidence_per_row: list[float] = []
    unmatched_samples: list[dict[str, object]] = []
    ambiguous_samples: list[dict[str, object]] = []
    observation_errors = 0
    derived_source_errors = 0
    derived_source_candidate_rows = 0
    derived_source_candidates = 0
    intent_errors = 0
    active_spell_scope_rows = 0
    omitted_sources: set[str] = set()
    trace_schema_versions: Counter[int] = Counter()
    observation_backends: Counter[str] = Counter()
    native_call_modes: Counter[str] = Counter()
    recorded_native_call_modes: set[str] = set()
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
    native_segment_ms: defaultdict[str, list[float]] = defaultdict(list)
    native_gc_completed: Counter[str] = Counter()
    native_rows_with_gc = 0
    native_observation_by_gc: defaultdict[str, list[float]] = defaultdict(
        list
    )
    native_over_budget_dominant_segments: Counter[str] = Counter()
    native_over_budget_samples: list[dict[str, object]] = []
    native_thread_cycle_sources: Counter[str] = Counter()
    native_thread_cycles: defaultdict[str, list[float]] = defaultdict(list)
    native_thread_cycles_by_evidence: defaultdict[
        str,
        defaultdict[str, list[float]],
    ] = defaultdict(lambda: defaultdict(list))
    native_cycle_attribution_rows = 0
    schema_v9_native_success_rows = 0
    schema_v10_rows = 0
    derived_source_native_segment_ms: defaultdict[str, list[float]] = (
        defaultdict(list)
    )
    observer_contention_classes: Counter[str] = Counter()
    observer_contention_patterns: Counter[str] = Counter()
    previous_evidence_count: int | None = None

    for audit in audits:
        if audit["schema_version"] == 10:
            schema_v10_rows += 1
        trace_schema_versions[int(audit["schema_version"])] += 1
        observation_backends[
            str(
                audit.get(
                    "observation_backend",
                    "schema_v1_v4_unrecorded",
                )
            )
        ] += 1
        native_call_mode = audit.get("native_call_mode")
        native_call_modes[
            (
                str(native_call_mode)
                if native_call_mode is not None
                else "none_or_schema_v1_v6_unrecorded"
            )
        ] += 1
        if native_call_mode in NATIVE_CALL_MODES:
            recorded_native_call_modes.add(str(native_call_mode))
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
        if audit.get("derived_source_error") is not None:
            derived_source_errors += 1
        derived_source_observation = audit.get(
            "derived_source_observation"
        )
        if isinstance(derived_source_observation, dict):
            candidate_count = int(
                derived_source_observation.get("candidate_count", 0)
            )
            derived_source_candidates += candidate_count
            if candidate_count:
                derived_source_candidate_rows += 1
        derived_source_diagnostics = audit.get(
            "derived_source_diagnostics"
        )
        if isinstance(derived_source_diagnostics, dict):
            source_segments = derived_source_diagnostics.get(
                "native_segments_ms"
            )
            if isinstance(source_segments, dict):
                for field in (
                    "prepare",
                    "native_call",
                    "materialize",
                    "controller_residual",
                ):
                    derived_source_native_segment_ms[field].append(
                        float(source_segments[field])
                    )
        if audit.get("intent_error") is not None:
            intent_errors += 1
        timing = audit.get("timing_ms")
        row_timing: dict[str, float] = {}
        if isinstance(timing, dict):
            for field, target in (
                ("observation", observation_ms),
                ("observation_cpu", observation_cpu_ms),
                ("derived_source_observation", derived_source_ms),
                (
                    "combined_pool_observation",
                    combined_pool_observation_ms,
                ),
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
        diagnostics = audit.get("observation_diagnostics")
        row_thread_cycles: dict[str, Any] | None = None
        row_contention: dict[str, Any] | None = None
        row_contention_class: str | None = None
        row_contention_names: list[str] = []
        if (
            audit["schema_version"] in {6, 7, 8, 9, 10}
            and isinstance(diagnostics, dict)
        ):
            segments = diagnostics["native_segments_ms"]
            completed = diagnostics["gc_completed"]
            assert isinstance(segments, dict)
            assert isinstance(completed, dict)
            numeric_segments = {
                field: float(segments[field])
                for field in (
                    "prepare",
                    "native_call",
                    "materialize",
                    "controller_residual",
                )
            }
            for field, value in numeric_segments.items():
                native_segment_ms[field].append(value)
            if audit["schema_version"] in {9, 10}:
                schema_v9_native_success_rows += 1
                raw_cycles = diagnostics.get("thread_cycles")
                assert isinstance(raw_cycles, dict)
                row_thread_cycles = raw_cycles
                cycle_source = str(raw_cycles["source"])
                native_thread_cycle_sources[cycle_source] += 1
                if cycle_source == THREAD_CYCLE_SOURCE_WINDOWS:
                    native_cycle_attribution_rows += 1
                    for cycle_phase in NATIVE_PHASES:
                        cycle_value = int(raw_cycles[cycle_phase])
                        native_thread_cycles[cycle_phase].append(
                            float(cycle_value)
                        )
                        native_thread_cycles_by_evidence[cycle_phase][
                            bucket
                        ].append(float(cycle_value))
                raw_contention = audit.get("observer_contention")
                assert isinstance(raw_contention, dict)
                row_contention = raw_contention
                (
                    row_contention_class,
                    row_contention_names,
                    contention_pattern,
                ) = _contention_overlap(raw_contention)
                observer_contention_classes[row_contention_class] += 1
                observer_contention_patterns[contention_pattern] += 1
            gc_total = 0
            for gc_phase in (
                "prepare",
                "native_call",
                "materialize",
            ):
                counts = completed[gc_phase]
                assert isinstance(counts, list)
                for generation, count in enumerate(counts):
                    numeric_count = int(count)
                    gc_total += numeric_count
                    native_gc_completed[
                        f"{gc_phase}:generation_{generation}"
                    ] += numeric_count
            gc_bucket = "with_gc" if gc_total else "without_gc"
            if gc_total:
                native_rows_with_gc += 1
            observation_value = row_timing.get("observation")
            if observation_value is not None:
                native_observation_by_gc[gc_bucket].append(
                    observation_value
                )
                if observation_value > OBSERVER_MAX_LIMIT_MS:
                    dominant = max(
                        numeric_segments,
                        key=numeric_segments.__getitem__,
                    )
                    native_over_budget_dominant_segments[dominant] += 1
                    if len(native_over_budget_samples) < MAX_SAMPLES:
                        native_over_budget_samples.append(
                            {
                                "frame": audit["frame"],
                                "evidence_count": evidence_count,
                                "observation_ms": observation_value,
                                "segments_ms": numeric_segments,
                                "gc_completed": completed,
                                "thread_cycles": row_thread_cycles,
                                "observer_contention": row_contention,
                                "known_future_overlap": {
                                    "classification": row_contention_class,
                                    "futures": row_contention_names,
                                },
                            }
                        )
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

    if len(recorded_native_call_modes) > 1:
        raise BulletBirthAuditError(
            "trace mixes native bullet-birth call modes"
        )

    phase_report = {
        phase: _counter(counts)
        for phase, counts in sorted(by_phase.items())
    }
    activation_edges = sum(classifications.values())
    unique_temporal = classifications["exact"] + classifications["support"]
    matched_temporal = unique_temporal + classifications["ambiguous"]
    observation_timing = _distribution(observation_ms)
    combined_observation_timing = _distribution(
        combined_pool_observation_ms
    )
    budget_timing = (
        combined_observation_timing
        if schema_v10_rows
        else observation_timing
    )
    validation_passed = (
        observation_errors == 0
        and derived_source_errors == 0
        and intent_errors == 0
    )
    observer_budget_passed = bool(
        budget_timing["p95"] is not None
        and budget_timing["p99"] is not None
        and budget_timing["max"] is not None
        and budget_timing["p95"] <= OBSERVER_P95_LIMIT_MS
        and budget_timing["p99"] <= OBSERVER_P99_LIMIT_MS
        and budget_timing["max"] <= OBSERVER_MAX_LIMIT_MS
    )
    cycle_attribution_required = schema_v9_native_success_rows > 0
    cycle_attribution_available = (
        not cycle_attribution_required
        or (
            native_cycle_attribution_rows
            == schema_v9_native_success_rows
        )
    )
    timed_intent_available = bool(events)
    velocity_coverage_statuses: Counter[str] = Counter()
    velocity_lowering_statuses: Counter[str] = Counter()
    incomplete_tagged_rows = 0
    incomplete_tagged_max = 0
    velocity_prefix_events = 0
    velocity_lowered_events = 0
    for scope in decisions.values():
        coverage = scope.get("velocity_lookahead_coverage_status")
        if isinstance(coverage, str):
            velocity_coverage_statuses[coverage] += 1
        lowering = scope.get("velocity_lookahead_lowering_status")
        if isinstance(lowering, str):
            velocity_lowering_statuses[lowering] += 1
        prefix_count = scope.get("velocity_lookahead_prefix_event_count")
        if type(prefix_count) is int:
            velocity_prefix_events += prefix_count
        lowered_count = scope.get("velocity_lookahead_event_count")
        if type(lowered_count) is int:
            velocity_lowered_events += lowered_count
        tagged = scope.get("velocity_lookahead_tagged_bullets")
        if (
            coverage in {"unknown", "legacy_declared_unknown"}
            and type(tagged) is int
            and tagged > 0
        ):
            incomplete_tagged_rows += 1
            incomplete_tagged_max = max(incomplete_tagged_max, tagged)
    return {
        "schema": SCHEMA,
        "passed": (
            validation_passed
            and observer_budget_passed
            and timed_intent_available
            and cycle_attribution_available
        ),
        "gates": {
            "validation_passed": validation_passed,
            "observer_budget_passed": observer_budget_passed,
            "timed_intent_available": timed_intent_available,
            "cycle_attribution_required": cycle_attribution_required,
            "cycle_attribution_available": cycle_attribution_available,
            "observer_limits_ms": {
                "boundary": (
                    "combined_birth_and_derived_source"
                    if schema_v10_rows
                    else "birth_observation"
                ),
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
            "derived_source_errors": derived_source_errors,
            "intent_errors": intent_errors,
            "trace_schema_versions": _counter(trace_schema_versions),
            "observation_backends": _counter(observation_backends),
            "native_call_modes": _counter(native_call_modes),
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
        "derived_pattern_source": {
            "schema_v10_rows": schema_v10_rows,
            "candidate_rows": derived_source_candidate_rows,
            "candidate_sightings": derived_source_candidates,
            "authority": "trace_only",
            "future_hazard_coverage": "unknown",
            "native_segments_ms": {
                field: _distribution(values)
                for field, values in sorted(
                    derived_source_native_segment_ms.items()
                )
            },
        },
        "derived_pattern_source_join": derived_source_join,
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
        "callback_lookahead": {
            "coverage_status_rows": _counter(
                velocity_coverage_statuses
            ),
            "lowering_status_rows": _counter(
                velocity_lowering_statuses
            ),
            "prefix_events": velocity_prefix_events,
            "lowered_events": velocity_lowered_events,
            "incomplete_tagged_rows": incomplete_tagged_rows,
            "incomplete_tagged_max": incomplete_tagged_max,
            "semantics": {
                "complete": "events cover the declared main-VM horizon",
                "unknown": "events are prefix evidence only",
                "legacy_declared_complete": (
                    "schema-v1-v7 declared horizon coverage without "
                    "an enforced lowering interface"
                ),
                "legacy_declared_unknown": (
                    "schema-v1-v7 incomplete prefix was exposed through "
                    "the old schedule interface"
                ),
                "incomplete_lowering": (
                    "no prefix tuple is consumed as complete"
                ),
            },
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
            "derived_source_observation": _distribution(
                derived_source_ms
            ),
            "combined_pool_observation": combined_observation_timing,
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
        "native_diagnostics": {
            "rows": len(native_segment_ms.get("native_call", ())),
            "segments_ms": {
                field: _distribution(values)
                for field, values in sorted(native_segment_ms.items())
            },
            "gc_completed": _counter(native_gc_completed),
            "rows_with_gc": native_rows_with_gc,
            "observation_ms_by_gc_overlap": {
                status: _distribution(values)
                for status, values in sorted(
                    native_observation_by_gc.items()
                )
            },
            "over_budget_dominant_segments": _counter(
                native_over_budget_dominant_segments
            ),
            "over_budget_samples": native_over_budget_samples,
            "thread_cycle_sources": _counter(
                native_thread_cycle_sources
            ),
            "thread_cycle_attribution_rows": (
                native_cycle_attribution_rows
            ),
            "thread_cycles": {
                phase: _distribution(values)
                for phase, values in sorted(native_thread_cycles.items())
            },
            "thread_cycles_by_evidence_count": {
                phase: {
                    bucket: _distribution(values)
                    for bucket, values in sorted(buckets.items())
                }
                for phase, buckets in sorted(
                    native_thread_cycles_by_evidence.items()
                )
            },
            "observer_contention": {
                "classifications": _counter(
                    observer_contention_classes
                ),
                "endpoint_patterns": _counter(
                    observer_contention_patterns
                ),
                "semantics": {
                    "definite_known_future_overlap": (
                        "one known future was inflight at both endpoints"
                    ),
                    "ambiguous_endpoint_overlap": (
                        "one known future changed to or from inflight"
                    ),
                    "no_known_future_overlap": (
                        "none of the three known futures overlapped both "
                        "endpoints"
                    ),
                    "causal_authority": "none",
                },
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
