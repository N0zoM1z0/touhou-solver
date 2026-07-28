#!/usr/bin/env python3
"""Audit a physical auxiliary-VM batch trace against its fixed gate."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
import statistics
import sys
from dataclasses import dataclass, field
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from th08_live.auxiliary_vm.trace_service import (  # noqa: E402
    AUXILIARY_VM_BATCH_TRACE_ROLE,
    AUXILIARY_VM_BATCH_TRACE_SCHEMA_VERSION,
)


P95_LIMIT_MS = 2.0
P99_LIMIT_MS = 4.0
MAX_LIMIT_MS = 12.0


def _percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    rank = (len(ordered) - 1) * percentile / 100.0
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return ordered[lower]
    weight = rank - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _distribution(
    values: list[float],
) -> dict[str, float | int] | None:
    if not values:
        return None
    return {
        "count": len(values),
        "p50": _percentile(values, 50.0),
        "p95": _percentile(values, 95.0),
        "p99": _percentile(values, 99.0),
        "max": max(values),
        "mean": statistics.fmean(values),
    }


def _digest(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


@dataclass(slots=True)
class TraceScan:
    path: Path
    sha256: str = ""
    byte_count: int = 0
    line_count: int = 0
    decision_count: int = 0
    decision_deltas: list[float] = field(default_factory=list)
    previous_iteration_ms: list[float] = field(default_factory=list)
    input_bomb_rows: int = 0
    hit_frames: list[int] = field(default_factory=list)
    summary: dict[str, object] | None = None
    batch_count: int = 0
    batch_schema_versions: Counter[int] = field(default_factory=Counter)
    batch_statuses: Counter[str] = field(default_factory=Counter)
    batch_status_bits: Counter[int] = field(default_factory=Counter)
    record_status_bits: Counter[int] = field(default_factory=Counter)
    call_depths: Counter[int] = field(default_factory=Counter)
    active_vm_hashes: set[str] = field(default_factory=set)
    native_call_ms: list[float] = field(default_factory=list)
    owner_capture_ms: list[float] = field(default_factory=list)
    materialize_ms: list[float] = field(default_factory=list)
    compact_ms: list[float] = field(default_factory=list)
    total_ms: list[float] = field(default_factory=list)
    owner_counts: list[float] = field(default_factory=list)
    non_null_counts: list[float] = field(default_factory=list)
    usable_counts: list[float] = field(default_factory=list)
    payload_bytes: list[float] = field(default_factory=list)
    process_reads: list[float] = field(default_factory=list)
    owner_blob_bytes: list[float] = field(default_factory=list)
    transaction_attempt_counts: list[float] = field(default_factory=list)
    retried_transaction_count: int = 0
    attempt_batch_status_bits: Counter[int] = field(
        default_factory=Counter
    )
    attempt_record_status_bits: Counter[int] = field(
        default_factory=Counter
    )
    validation_errors: list[str] = field(default_factory=list)


def _number(
    mapping: dict[str, object],
    key: str,
    *,
    context: str,
) -> float:
    value = mapping.get(key)
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{context}: {key} is not numeric")
    converted = float(value)
    if not math.isfinite(converted) or converted < 0.0:
        raise ValueError(f"{context}: {key} is not finite non-negative")
    return converted


_RETRYABLE_BATCH_BITS = (1 << 0) | (1 << 1) | (1 << 6)
_RETRYABLE_RECORD_BITS = (
    (1 << 0) | (1 << 7) | (1 << 11) | (1 << 12) | (1 << 13)
)
_MAXIMUM_ATTEMPT_READS = 837
_MAXIMUM_TRANSACTION_READS = 3 * _MAXIMUM_ATTEMPT_READS


def _status_histogram(
    value: object,
    *,
    context: str,
) -> Counter[int]:
    if not isinstance(value, dict):
        raise ValueError(f"{context}: record_status_bits is not an object")
    result: Counter[int] = Counter()
    for raw_bits, raw_count in value.items():
        try:
            bits = int(raw_bits)
        except (TypeError, ValueError) as error:
            raise ValueError(
                f"{context}: invalid record status key {raw_bits!r}"
            ) from error
        if (
            bits < 0
            or not isinstance(raw_count, int)
            or isinstance(raw_count, bool)
            or raw_count <= 0
        ):
            raise ValueError(f"{context}: invalid record status count")
        if str(bits) != raw_bits:
            raise ValueError(
                f"{context}: noncanonical record status key {raw_bits!r}"
            )
        result[bits] += raw_count
    return result


def _attempt_retryable(
    *,
    batch_bits: int,
    record_statuses: Counter[int],
) -> bool:
    return (
        batch_bits != 0
        and not (batch_bits & ~_RETRYABLE_BATCH_BITS)
        and all(
            not (bits & ~_RETRYABLE_RECORD_BITS)
            for bits in record_statuses
        )
    )


def _audit_v3_attempts(
    scan: TraceScan,
    row: dict[str, object],
    *,
    context: str,
    timing: dict[str, object],
) -> None:
    attempt_limit = row.get("attempt_limit")
    attempt_count = row.get("attempt_count")
    attempts = row.get("attempts")
    if attempt_limit != 3:
        scan.validation_errors.append(
            f"{context}: attempt limit is not three"
        )
    if (
        not isinstance(attempt_count, int)
        or isinstance(attempt_count, bool)
        or not 0 <= attempt_count <= 3
        or not isinstance(attempts, list)
        or len(attempts) != attempt_count
    ):
        raise ValueError(f"{context}: invalid attempt count/array")
    if attempt_count == 0:
        if row.get("status") != "native_transaction_failed":
            scan.validation_errors.append(
                f"{context}: empty non-exception transaction"
            )
        if row.get("selected_attempt_index") is not None:
            scan.validation_errors.append(
                f"{context}: empty transaction selected an attempt"
            )
        top_reads = row.get("process_read_count")
        if top_reads != 0:
            scan.validation_errors.append(
                f"{context}: empty transaction reports reads"
            )
        for key in ("native_call", "materialize"):
            if _number(timing, key, context=context) != 0.0:
                scan.validation_errors.append(
                    f"{context}: empty transaction reports {key}"
                )
        scan.transaction_attempt_counts.append(0.0)
        return
    scan.transaction_attempt_counts.append(float(attempt_count))
    if attempt_count > 1:
        scan.retried_transaction_count += 1

    native_sum = 0.0
    materialize_sum = 0.0
    read_sum = 0
    computed_retryable: list[bool] = []
    successes: list[bool] = []
    for attempt_index, attempt in enumerate(attempts):
        attempt_context = f"{context}.attempts[{attempt_index}]"
        if not isinstance(attempt, dict):
            raise ValueError(f"{attempt_context}: not an object")
        if attempt.get("index") != attempt_index:
            scan.validation_errors.append(
                f"{attempt_context}: noncanonical index"
            )
        batch_bits = attempt.get("batch_status_bits")
        success = attempt.get("success")
        producer_retryable = attempt.get("retryable")
        if (
            not isinstance(batch_bits, int)
            or isinstance(batch_bits, bool)
            or not isinstance(success, bool)
            or not isinstance(producer_retryable, bool)
        ):
            raise ValueError(f"{attempt_context}: invalid status fields")
        record_statuses = _status_histogram(
            attempt.get("record_status_bits"),
            context=attempt_context,
        )
        retryable = _attempt_retryable(
            batch_bits=batch_bits,
            record_statuses=record_statuses,
        )
        if retryable != producer_retryable:
            scan.validation_errors.append(
                f"{attempt_context}: forged retryable classification"
            )
        if success != (batch_bits == 0 and not any(
            bits not in (0, 1) for bits in record_statuses
        )):
            scan.validation_errors.append(
                f"{attempt_context}: success/status inconsistency"
            )
        scan.attempt_batch_status_bits[batch_bits] += 1
        scan.attempt_record_status_bits.update(record_statuses)
        computed_retryable.append(retryable)
        successes.append(success)

        attempt_timing = attempt.get("timing_ms")
        if not isinstance(attempt_timing, dict):
            raise ValueError(f"{attempt_context}: timing is not an object")
        native_sum += _number(
            attempt_timing,
            "native_call",
            context=attempt_context,
        )
        materialize_sum += _number(
            attempt_timing,
            "materialize",
            context=attempt_context,
        )
        reads = attempt.get("process_read_count")
        if (
            not isinstance(reads, int)
            or isinstance(reads, bool)
            or reads < 0
            or reads > _MAXIMUM_ATTEMPT_READS
        ):
            raise ValueError(f"{attempt_context}: invalid read count")
        read_sum += reads

    for attempt_index in range(attempt_count - 1):
        if successes[attempt_index] or not computed_retryable[attempt_index]:
            scan.validation_errors.append(
                f"{context}: illegal attempt after success/terminal failure"
            )
    status = row.get("status")
    selected = row.get("selected_attempt_index")
    last = attempt_count - 1
    if status == "success":
        if selected != last or not successes[last]:
            scan.validation_errors.append(
                f"{context}: invalid selected successful attempt"
            )
        observation = row.get("observation")
        if not isinstance(observation, dict):
            scan.validation_errors.append(
                f"{context}: successful transaction has no observation"
            )
        else:
            selected_attempt = attempts[last]
            assert isinstance(selected_attempt, dict)
            selected_fields = (
                "selected_manager_frame",
                "owner_manager_frame_after",
                "context_manager_frame_before",
                "manager_frame_after",
                "batch_status_bits",
                "success",
                "active_owner_count",
                "record_count",
                "non_null_context_count",
                "usable_context_count",
                "state_payload_bytes",
                "owner_blob_bytes",
            )
            for key in selected_fields:
                if selected_attempt.get(key) != observation.get(key):
                    scan.validation_errors.append(
                        f"{context}: selected attempt/observation "
                        f"{key} mismatch"
                    )
            observation_records = observation.get("records")
            if not isinstance(observation_records, list):
                scan.validation_errors.append(
                    f"{context}: selected observation records not an array"
                )
            else:
                selected_histogram = _status_histogram(
                    selected_attempt.get("record_status_bits"),
                    context=f"{context}.selected_attempt",
                )
                observation_histogram: Counter[int] = Counter()
                for record_index, record in enumerate(
                    observation_records
                ):
                    if not isinstance(record, dict):
                        raise ValueError(
                            f"{context}.observation.records"
                            f"[{record_index}]: not an object"
                        )
                    bits = record.get("status_bits")
                    if not isinstance(bits, int) or isinstance(bits, bool):
                        raise ValueError(
                            f"{context}.observation.records"
                            f"[{record_index}]: invalid status"
                        )
                    observation_histogram[bits] += 1
                if selected_histogram != observation_histogram:
                    scan.validation_errors.append(
                        f"{context}: selected attempt/observation "
                        "record-status histogram mismatch"
                    )
    elif status == "retry_exhausted":
        if (
            attempt_count != 3
            or selected is not None
            or not computed_retryable[last]
            or row.get("observation") is not None
        ):
            scan.validation_errors.append(
                f"{context}: invalid exhausted transaction"
            )
    elif status == "terminal_rejected":
        if (
            selected is not None
            or successes[last]
            or computed_retryable[last]
            or row.get("observation") is not None
        ):
            scan.validation_errors.append(
                f"{context}: invalid terminal transaction"
            )
    elif status == "native_transaction_failed":
        if (
            selected is not None
            or attempt_count >= 3
            or any(successes)
            or not all(computed_retryable)
            or row.get("observation") is not None
        ):
            scan.validation_errors.append(
                f"{context}: exception selected an attempt"
            )
    else:
        scan.validation_errors.append(f"{context}: unknown v3 status")

    top_reads = row.get("process_read_count")
    if top_reads != read_sum or read_sum > _MAXIMUM_TRANSACTION_READS:
        scan.validation_errors.append(f"{context}: read-count sum mismatch")
    for key, computed in (
        ("native_call", native_sum),
        ("materialize", materialize_sum),
    ):
        reported = _number(timing, key, context=context)
        if not math.isclose(reported, computed, abs_tol=1e-6):
            scan.validation_errors.append(
                f"{context}: {key} sum mismatch"
            )


def _audit_batch(scan: TraceScan, row: dict[str, object]) -> None:
    index = scan.batch_count
    context = f"batch[{index}]"
    scan.batch_count += 1
    schema_version = row.get("schema_version")
    if schema_version not in (
        1,
        2,
        AUXILIARY_VM_BATCH_TRACE_SCHEMA_VERSION,
    ):
        raise ValueError(f"{context}: unexpected schema version")
    assert isinstance(schema_version, int)
    scan.batch_schema_versions[schema_version] += 1
    if row.get("authority") != AUXILIARY_VM_BATCH_TRACE_ROLE:
        raise ValueError(f"{context}: unexpected authority")
    status = row.get("status")
    if not isinstance(status, str):
        raise ValueError(f"{context}: status is not a string")
    scan.batch_statuses[status] += 1
    timing = row.get("timing_ms")
    if not isinstance(timing, dict):
        raise ValueError(f"{context}: timing_ms is not an object")
    if "owner_capture" in timing:
        scan.owner_capture_ms.append(
            _number(timing, "owner_capture", context=context)
        )
    scan.total_ms.append(_number(timing, "total", context=context))
    if schema_version == 3:
        _audit_v3_attempts(scan, row, context=context, timing=timing)

    observation = row.get("observation")
    if observation is None:
        return
    if not isinstance(observation, dict):
        raise ValueError(f"{context}: observation is not an object")
    layout = observation.get("layout")
    expected_layout = (
        "th08-auxiliary-vm-batch-v2"
        if schema_version == 3
        else f"th08-auxiliary-vm-batch-v{schema_version}"
    )
    if layout != expected_layout:
        raise ValueError(
            f"{context}: expected observation layout {expected_layout}"
        )
    if (
        observation.get("authority")
        != "trace_only_no_action_authority"
    ):
        raise ValueError(f"{context}: unexpected observation authority")
    # Failed v3 transactions have no selected observation and fail the
    # physical gate. Keep selected-state distributions uncontaminated by
    # their failed attempt state.
    scan.native_call_ms.append(
        _number(timing, "native_call", context=context)
    )
    scan.materialize_ms.append(
        _number(timing, "materialize", context=context)
    )
    scan.compact_ms.append(_number(timing, "compact", context=context))
    batch_bits = observation.get("batch_status_bits")
    if not isinstance(batch_bits, int) or isinstance(batch_bits, bool):
        raise ValueError(f"{context}: batch status is not an integer")
    scan.batch_status_bits[batch_bits] += 1
    if schema_version == 1:
        owner_after = row.get("owner_frame_after")
        for key in (
            "expected_manager_frame",
            "manager_frame_before",
            "manager_frame_after",
        ):
            if observation.get(key) != owner_after:
                scan.validation_errors.append(
                    f"{context}: {key} does not equal owner frame"
                )
    else:
        frame_keys = (
            "selected_manager_frame",
            "owner_manager_frame_after",
            "context_manager_frame_before",
            "manager_frame_after",
        )
        for key in frame_keys:
            if observation.get(key) != row.get(key):
                scan.validation_errors.append(
                    f"{context}: top-level/observation {key} mismatch"
                )
        selected = observation.get("selected_manager_frame")
        if batch_bits == 0 and any(
            observation.get(key) != selected
            for key in frame_keys[1:]
        ):
            scan.validation_errors.append(
                f"{context}: successful v2 manager bracket differs"
            )
        scan.owner_blob_bytes.append(
            _number(observation, "owner_blob_bytes", context=context)
        )
    scan.owner_counts.append(
        _number(observation, "active_owner_count", context=context)
    )
    scan.non_null_counts.append(
        _number(observation, "non_null_context_count", context=context)
    )
    scan.usable_counts.append(
        _number(observation, "usable_context_count", context=context)
    )
    scan.payload_bytes.append(
        _number(observation, "state_payload_bytes", context=context)
    )
    scan.process_reads.append(
        _number(
            row if schema_version == 3 else observation,
            "process_read_count",
            context=context,
        )
    )
    records = observation.get("records")
    if not isinstance(records, list):
        raise ValueError(f"{context}: records is not an array")
    observed_record_statuses: Counter[int] = Counter()
    active_owner_slots: set[int] = set()
    non_null_contexts = 0
    for record_index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(
                f"{context}.records[{record_index}] is not an object"
            )
        slot = record.get("slot")
        context_pointer = record.get("context_pointer")
        if (
            not isinstance(slot, int)
            or isinstance(slot, bool)
            or not isinstance(context_pointer, int)
            or isinstance(context_pointer, bool)
        ):
            raise ValueError(
                f"{context}.records[{record_index}] identity is invalid"
            )
        active_owner_slots.add(slot)
        non_null_contexts += context_pointer != 0
        bits = record.get("status_bits")
        if not isinstance(bits, int) or isinstance(bits, bool):
            raise ValueError(
                f"{context}.records[{record_index}] status is not integer"
            )
        observed_record_statuses[bits] += 1
        scan.record_status_bits[bits] += 1
        if context_pointer != 0:
            depth = record.get("call_depth")
            if isinstance(depth, int) and not isinstance(depth, bool):
                scan.call_depths[depth] += 1
            active_hash = record.get("active_vm_sha256")
            if isinstance(active_hash, str):
                scan.active_vm_hashes.add(active_hash)
    semantic_success = (
        batch_bits == 0
        and all(bits in (0, 1) for bits in observed_record_statuses)
    )
    expected_counts = {
        "record_count": len(records),
        "active_owner_count": len(active_owner_slots),
        "non_null_context_count": non_null_contexts,
        "usable_context_count": (
            observed_record_statuses[0] if semantic_success else 0
        ),
    }
    for key, expected in expected_counts.items():
        if observation.get(key) != expected:
            scan.validation_errors.append(
                f"{context}: observation {key} mismatch"
            )
    if observation.get("success") != semantic_success:
        scan.validation_errors.append(
            f"{context}: observation success/status inconsistency"
        )


def scan_trace(path: Path, *, audit_batches: bool) -> TraceScan:
    scan = TraceScan(path=path)
    digest = hashlib.sha256()
    previous_decision: tuple[int, int, int] | None = None
    with path.open("rb") as source:
        for line_number, binary_line in enumerate(source, 1):
            digest.update(binary_line)
            scan.byte_count += len(binary_line)
            scan.line_count = line_number
            prefix = binary_line[:512]
            relevant = (
                b'"kind":"decision"' in prefix
                or b'"kind": "decision"' in prefix
                or b'"kind":"summary"' in prefix
                or b'"kind": "summary"' in prefix
                or (
                    audit_batches
                    and (
                        b'"kind":"auxiliary_vm_batch"' in prefix
                        or b'"kind": "auxiliary_vm_batch"' in prefix
                    )
                )
            )
            if not relevant:
                continue
            try:
                row = json.loads(binary_line)
            except (json.JSONDecodeError, UnicodeDecodeError) as error:
                raise ValueError(
                    f"{path}:{line_number}: invalid JSON: {error}"
                ) from error
            kind = row.get("kind")
            if kind == "decision":
                frame = row.get("frame")
                epoch = row.get("gameplay_epoch")
                stage = row.get("stage_route_index")
                if not all(
                    isinstance(value, int) and not isinstance(value, bool)
                    for value in (frame, epoch, stage)
                ):
                    raise ValueError(
                        f"{path}:{line_number}: invalid decision identity"
                    )
                identity = (int(epoch), int(stage), int(frame))
                if (
                    previous_decision is not None
                    and identity[:2] == previous_decision[:2]
                    and identity[2] > previous_decision[2]
                ):
                    scan.decision_deltas.append(
                        float(identity[2] - previous_decision[2])
                    )
                previous_decision = identity
                scan.decision_count += 1
                timing = row.get("timing_ms")
                if isinstance(timing, dict):
                    previous_iteration = timing.get("previous_iteration")
                    if isinstance(previous_iteration, (int, float)):
                        scan.previous_iteration_ms.append(
                            float(previous_iteration)
                        )
                if bool(row.get("bomb")) or (
                    isinstance(row.get("mask"), int)
                    and int(row["mask"]) & 0x02
                ):
                    scan.input_bomb_rows += 1
                if bool(row.get("hit_started")):
                    scan.hit_frames.append(int(frame))
            elif kind == "summary":
                scan.summary = row
            elif kind == "auxiliary_vm_batch" and audit_batches:
                _audit_batch(scan, row)
    scan.sha256 = digest.hexdigest()
    return scan


def _session_gate(path: Path | None) -> tuple[dict[str, object] | None, bool]:
    if path is None:
        return None, False
    session = json.loads(path.read_text(encoding="utf-8"))
    summary = session.get("agent_summary")
    passed = bool(
        session.get("status") == "completed"
        and session.get("trial_accepted") is True
        and session.get("hard_no_bomb") is True
        and isinstance(summary, dict)
        and summary.get("termination_reason") == "route_complete"
    )
    compact = {
        "path": str(path),
        "run_id": session.get("run_id"),
        "status": session.get("status"),
        "trial_accepted": session.get("trial_accepted"),
        "hard_no_bomb": session.get("hard_no_bomb"),
        "termination_reason": (
            summary.get("termination_reason")
            if isinstance(summary, dict)
            else None
        ),
        "decision_count": (
            summary.get("decision_count")
            if isinstance(summary, dict)
            else None
        ),
        "hit_count": (
            summary.get("hit_count")
            if isinstance(summary, dict)
            else None
        ),
        "passed": passed,
    }
    return compact, passed


def _scan_record(scan: TraceScan) -> dict[str, object]:
    return {
        "path": str(scan.path),
        "bytes": scan.byte_count,
        "sha256": scan.sha256,
        "line_count": scan.line_count,
        "decision_count": scan.decision_count,
        "decision_frame_delta": _distribution(scan.decision_deltas),
        "previous_iteration_ms": _distribution(
            scan.previous_iteration_ms
        ),
        "input_bomb_rows": scan.input_bomb_rows,
        "hit_frames": scan.hit_frames,
        "summary": scan.summary,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--session", type=Path, required=True)
    arguments = parser.parse_args(argv)

    scan = scan_trace(arguments.trace, audit_batches=True)
    baseline = scan_trace(arguments.baseline, audit_batches=False)
    native = _distribution(scan.native_call_ms)
    cadence = _distribution(scan.decision_deltas)
    baseline_cadence = _distribution(baseline.decision_deltas)
    session, session_pass = _session_gate(arguments.session)
    gates = {
        "batch_rows_present": scan.batch_count > 0,
        "schema_v3_only": scan.batch_schema_versions
        == Counter({AUXILIARY_VM_BATCH_TRACE_SCHEMA_VERSION: scan.batch_count}),
        "retry_path_observed": scan.retried_transaction_count > 0,
        "usable_context_observed": sum(scan.usable_counts) > 0,
        "zero_batch_failures": (
            scan.batch_statuses == Counter({"success": scan.batch_count})
            and scan.batch_status_bits == Counter({0: scan.batch_count})
            and all(bits in (0, 1) for bits in scan.record_status_bits)
            and not scan.validation_errors
        ),
        "native_p95_ms": bool(
            native is not None and native["p95"] <= P95_LIMIT_MS
        ),
        "native_p99_ms": bool(
            native is not None and native["p99"] <= P99_LIMIT_MS
        ),
        "native_max_ms": bool(
            native is not None and native["max"] <= MAX_LIMIT_MS
        ),
        "decision_cadence_p95_regression_at_most_one_frame": bool(
            cadence is not None
            and baseline_cadence is not None
            and cadence["p95"] <= baseline_cadence["p95"] + 1.0
        ),
        "hard_no_bomb_trace": scan.input_bomb_rows == 0,
        "route_transition_cleanup_session": session_pass,
    }
    passed = all(gates.values())
    report: dict[str, object] = {
        "schema": "th08-auxiliary-vm-batch-physical-gate-v3",
        "authority": "physical trace-only evidence; no action authority",
        "trace": _scan_record(scan),
        "baseline": _scan_record(baseline),
        "session": session,
        "batch": {
            "count": scan.batch_count,
            "schema_versions": {
                str(key): value
                for key, value in sorted(
                    scan.batch_schema_versions.items()
                )
            },
            "statuses": dict(sorted(scan.batch_statuses.items())),
            "batch_status_bits": {
                str(key): value
                for key, value in sorted(scan.batch_status_bits.items())
            },
            "record_status_bits": {
                str(key): value
                for key, value in sorted(scan.record_status_bits.items())
            },
            "retried_transaction_count": scan.retried_transaction_count,
            "attempt_count": _distribution(
                scan.transaction_attempt_counts
            ),
            "attempt_batch_status_bits": {
                str(key): value
                for key, value in sorted(
                    scan.attempt_batch_status_bits.items()
                )
            },
            "attempt_record_status_bits": {
                str(key): value
                for key, value in sorted(
                    scan.attempt_record_status_bits.items()
                )
            },
            "validation_errors": scan.validation_errors,
            "call_depths": {
                str(key): value
                for key, value in sorted(scan.call_depths.items())
            },
            "unique_active_vm_hashes": len(scan.active_vm_hashes),
            "active_owner_count": _distribution(scan.owner_counts),
            "non_null_context_count": _distribution(scan.non_null_counts),
            "usable_context_count": _distribution(scan.usable_counts),
            "state_payload_bytes": _distribution(scan.payload_bytes),
            "process_read_count": _distribution(scan.process_reads),
            "owner_blob_bytes": _distribution(scan.owner_blob_bytes),
            "timing_ms": {
                "owner_capture": _distribution(scan.owner_capture_ms),
                "native_call": native,
                "materialize": _distribution(scan.materialize_ms),
                "compact": _distribution(scan.compact_ms),
                "total": _distribution(scan.total_ms),
            },
        },
        "limits": {
            "native_p95_ms": P95_LIMIT_MS,
            "native_p99_ms": P99_LIMIT_MS,
            "native_max_ms": MAX_LIMIT_MS,
            "decision_cadence_p95_regression_frames": 1.0,
        },
        "gates": gates,
        "passed": passed,
    }
    report["report_digest"] = _digest(report)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
