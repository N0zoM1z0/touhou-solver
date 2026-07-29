"""Streaming extraction for coalesced auxiliary evidence decisions."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from analysis.auxiliary_vm_batch_trace import scan_trace

from .coalesced_replay_v6 import (
    ENVELOPE_FIELD,
    DecodedCoalescedBatch,
    decode_coalesced_batch,
)
from .physical_report_v2 import (
    AuxiliaryEclEventPhysicalAuditError,
    DeliveryTraceData,
)
from .physical_replay import AuxiliaryEclEventReplayError


@dataclass(frozen=True)
class CoalescedTraceEvidence:
    delivery: DeliveryTraceData
    pack_ms: list[float]
    evidence_plus_pack_ms: list[float]
    bearing_decision_emit_ms: list[float]
    all_decision_emit_ms: list[float]
    payload_base64_bytes: list[float]
    compressed_bytes: list[float]
    uncompressed_bytes: list[float]
    bearing_decision_line_bytes: list[float]
    sequences: list[int]
    standalone_batch_count: int


def _finite_nonnegative(value: object, *, context: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
        or float(value) < 0.0
    ):
        raise AuxiliaryEclEventPhysicalAuditError(
            f"{context} is not finite nonnegative"
        )
    return float(value)


def _decision_previous_trace(
    row: dict[str, Any],
    *,
    context: str,
) -> float | None:
    timing = row.get("timing_ms")
    if not isinstance(timing, dict):
        raise AuxiliaryEclEventPhysicalAuditError(
            f"{context} decision timing is absent"
        )
    value = timing.get("previous_trace")
    if value is None:
        return None
    return _finite_nonnegative(
        value,
        context=f"{context}.timing_ms.previous_trace",
    )


def load_coalesced_trace(path: Path) -> CoalescedTraceEvidence:
    """Decode every envelope and pair it with its causal next measurement."""

    independent_scan = scan_trace(path, audit_batches=False)
    digest = hashlib.sha256()
    byte_count = 0
    rows: list[dict[str, Any]] = []
    preparations: list[dict[str, Any]] = []
    pack_ms: list[float] = []
    evidence_plus_pack_ms: list[float] = []
    bearing_emit_ms: list[float] = []
    all_emit_ms: list[float] = []
    payload_sizes: list[float] = []
    compressed_sizes: list[float] = []
    uncompressed_sizes: list[float] = []
    bearing_line_sizes: list[float] = []
    sequences: list[int] = []
    process_reads: list[float] = []
    statuses: Counter[str] = Counter()
    schema_versions: Counter[int] = Counter()
    pending_sequence: int | None = None
    standalone_batch_count = 0

    with path.open("rb") as source:
        for line_number, raw_line in enumerate(source, 1):
            digest.update(raw_line)
            byte_count += len(raw_line)
            prefix = raw_line[:512]
            is_decision = (
                b'"kind":"decision"' in prefix
                or b'"kind": "decision"' in prefix
            )
            is_preparation = (
                b'"kind":"auxiliary_ecl_event_preparation"' in prefix
                or b'"kind": "auxiliary_ecl_event_preparation"' in prefix
            )
            is_standalone_batch = (
                b'"kind":"auxiliary_vm_batch"' in prefix
                or b'"kind": "auxiliary_vm_batch"' in prefix
            )
            if not (is_decision or is_preparation or is_standalone_batch):
                continue
            try:
                parsed = json.loads(raw_line)
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise AuxiliaryEclEventPhysicalAuditError(
                    f"trace line {line_number} is invalid JSON"
                ) from error
            if not isinstance(parsed, dict):
                raise AuxiliaryEclEventPhysicalAuditError(
                    f"trace line {line_number} is not an object"
                )
            if is_standalone_batch:
                standalone_batch_count += 1
                continue
            if is_preparation:
                preparations.append(parsed)
                continue

            context = f"decision line {line_number}"
            previous_trace = _decision_previous_trace(
                parsed,
                context=context,
            )
            if previous_trace is not None:
                all_emit_ms.append(previous_trace)
            if pending_sequence is not None:
                if previous_trace is None:
                    raise AuxiliaryEclEventPhysicalAuditError(
                        "coalesced decision is missing next-decision "
                        "publication timing"
                    )
                bearing_emit_ms.append(previous_trace)
                pending_sequence = None
            if ENVELOPE_FIELD not in parsed:
                continue
            try:
                decoded = decode_coalesced_batch(
                    parsed,
                    expected_sequence=len(rows),
                    context=context,
                )
            except AuxiliaryEclEventReplayError as error:
                raise AuxiliaryEclEventPhysicalAuditError(
                    str(error)
                ) from error
            _append_decoded(
                decoded,
                raw_line_bytes=len(raw_line),
                rows=rows,
                pack_ms=pack_ms,
                evidence_plus_pack_ms=evidence_plus_pack_ms,
                payload_sizes=payload_sizes,
                compressed_sizes=compressed_sizes,
                uncompressed_sizes=uncompressed_sizes,
                bearing_line_sizes=bearing_line_sizes,
                sequences=sequences,
                process_reads=process_reads,
                statuses=statuses,
                schema_versions=schema_versions,
            )
            pending_sequence = decoded.sequence

    if standalone_batch_count:
        raise AuxiliaryEclEventPhysicalAuditError(
            "V6 trace contains a standalone auxiliary batch row"
        )
    if pending_sequence is not None:
        raise AuxiliaryEclEventPhysicalAuditError(
            "final coalesced decision has no causal publication timing"
        )
    trace_sha256 = digest.hexdigest()
    if (
        independent_scan.sha256 != trace_sha256
        or independent_scan.byte_count != byte_count
    ):
        raise AuxiliaryEclEventPhysicalAuditError(
            "independent coalesced trace digests disagree"
        )
    if len(bearing_emit_ms) != len(rows):
        raise AuxiliaryEclEventPhysicalAuditError(
            "coalesced publication timing coverage is incomplete"
        )
    return CoalescedTraceEvidence(
        delivery=DeliveryTraceData(
            rows=rows,
            preparations=preparations,
            trace_sha256=trace_sha256,
            trace_bytes=byte_count,
            batch_count=len(rows),
            batch_schema_versions=schema_versions,
            batch_statuses=statuses,
            validation_errors=[],
            process_reads=process_reads,
            decision_deltas=independent_scan.decision_deltas,
            batch_line_bytes=uncompressed_sizes,
        ),
        pack_ms=pack_ms,
        evidence_plus_pack_ms=evidence_plus_pack_ms,
        bearing_decision_emit_ms=bearing_emit_ms,
        all_decision_emit_ms=all_emit_ms,
        payload_base64_bytes=payload_sizes,
        compressed_bytes=compressed_sizes,
        uncompressed_bytes=uncompressed_sizes,
        bearing_decision_line_bytes=bearing_line_sizes,
        sequences=sequences,
        standalone_batch_count=standalone_batch_count,
    )


def _append_decoded(
    decoded: DecodedCoalescedBatch,
    *,
    raw_line_bytes: int,
    rows: list[dict[str, Any]],
    pack_ms: list[float],
    evidence_plus_pack_ms: list[float],
    payload_sizes: list[float],
    compressed_sizes: list[float],
    uncompressed_sizes: list[float],
    bearing_line_sizes: list[float],
    sequences: list[int],
    process_reads: list[float],
    statuses: Counter[str],
    schema_versions: Counter[int],
) -> None:
    row = decoded.row
    timing = row.get("timing_ms")
    assert isinstance(timing, dict)
    transaction_total = _finite_nonnegative(
        timing.get("total"),
        context=f"coalesced[{decoded.sequence}].timing_ms.total",
    )
    process_read_count = row.get("process_read_count")
    if (
        isinstance(process_read_count, bool)
        or not isinstance(process_read_count, int)
        or process_read_count < 0
    ):
        raise AuxiliaryEclEventPhysicalAuditError(
            f"coalesced[{decoded.sequence}] process reads are invalid"
        )
    status = row.get("status")
    schema_version = row.get("schema_version")
    if not isinstance(status, str):
        raise AuxiliaryEclEventPhysicalAuditError(
            f"coalesced[{decoded.sequence}] status is invalid"
        )
    if isinstance(schema_version, bool) or not isinstance(schema_version, int):
        raise AuxiliaryEclEventPhysicalAuditError(
            f"coalesced[{decoded.sequence}] schema version is invalid"
        )
    rows.append(row)
    pack_ms.append(decoded.pack_ms)
    evidence_plus_pack_ms.append(transaction_total + decoded.pack_ms)
    payload_sizes.append(float(decoded.payload_base64_bytes))
    compressed_sizes.append(float(decoded.compressed_bytes))
    uncompressed_sizes.append(float(decoded.uncompressed_bytes))
    bearing_line_sizes.append(float(raw_line_bytes))
    sequences.append(decoded.sequence)
    process_reads.append(float(process_read_count))
    statuses[status] += 1
    schema_versions[schema_version] += 1


def decision_emit_values(path: Path) -> list[float]:
    """Read causal decision-publication samples from an ordinary trace."""

    result: list[float] = []
    with path.open("rb") as source:
        for line_number, raw_line in enumerate(source, 1):
            prefix = raw_line[:512]
            if not (
                b'"kind":"decision"' in prefix
                or b'"kind": "decision"' in prefix
            ):
                continue
            try:
                row = json.loads(raw_line)
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise AuxiliaryEclEventPhysicalAuditError(
                    f"baseline line {line_number} is invalid JSON"
                ) from error
            if not isinstance(row, dict):
                raise AuxiliaryEclEventPhysicalAuditError(
                    f"baseline line {line_number} is not an object"
                )
            value = _decision_previous_trace(
                row,
                context=f"baseline decision line {line_number}",
            )
            if value is not None:
                result.append(value)
    return result


__all__ = [
    "CoalescedTraceEvidence",
    "decision_emit_values",
    "load_coalesced_trace",
]
