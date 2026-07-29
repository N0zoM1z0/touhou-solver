"""Streaming, timing, session, and version helpers for the physical gate."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import statistics
from typing import Any

from analysis.th08_runtime_ecl_identity_audit import STAGE5_STATIC_SHA256

from .replay_evidence import ACCEPTED_VERSION_SCHEMA


class AuxiliaryEclEventPhysicalAuditError(ValueError):
    """Raised when retained physical evidence violates the fixed contract."""


def digest(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def finite_nonnegative(value: object, context: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AuxiliaryEclEventPhysicalAuditError(
            f"{context} must be numeric"
        )
    result = float(value)
    if not math.isfinite(result) or result < 0.0:
        raise AuxiliaryEclEventPhysicalAuditError(
            f"{context} must be finite and nonnegative"
        )
    return result


def _percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    rank = (len(ordered) - 1) * percentile / 100.0
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return ordered[lower]
    weight = rank - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def distribution(
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


def within(
    observed: dict[str, float | int] | None,
    limits: tuple[float, float, float],
) -> bool:
    return bool(
        observed is not None
        and observed["p95"] <= limits[0]
        and observed["p99"] <= limits[1]
        and observed["max"] <= limits[2]
    )


def session_record(path: Path) -> tuple[dict[str, object], bool]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise AuxiliaryEclEventPhysicalAuditError(
            "session must be a JSON object"
        )
    summary = raw.get("agent_summary")
    accepted = bool(
        raw.get("status") == "completed"
        and raw.get("trial_accepted") is True
        and raw.get("hard_no_bomb") is True
        and raw.get("trace_auxiliary_vm_batches") is True
        and raw.get("trace_auxiliary_ecl_events") is True
        and raw.get("auxiliary_vm_batch_spell_id") == 107
        and raw.get("runtime_ecl_static_sha256")
        == STAGE5_STATIC_SHA256
        and isinstance(summary, dict)
        and summary.get("termination_reason") == "route_complete"
    )
    return (
        {
            "path": str(path),
            "run_id": raw.get("run_id"),
            "status": raw.get("status"),
            "trial_accepted": raw.get("trial_accepted"),
            "hard_no_bomb": raw.get("hard_no_bomb"),
            "trace_auxiliary_vm_batches": raw.get(
                "trace_auxiliary_vm_batches"
            ),
            "trace_auxiliary_ecl_events": raw.get(
                "trace_auxiliary_ecl_events"
            ),
            "auxiliary_vm_batch_spell_id": raw.get(
                "auxiliary_vm_batch_spell_id"
            ),
            "runtime_ecl_static_sha256": raw.get(
                "runtime_ecl_static_sha256"
            ),
            "termination_reason": (
                summary.get("termination_reason")
                if isinstance(summary, dict)
                else None
            ),
            "hit_count": (
                summary.get("hit_count")
                if isinstance(summary, dict)
                else None
            ),
            "passed": accepted,
        },
        accepted,
    )


def expected_runtime_version(
    identity: dict[str, object],
) -> dict[str, object]:
    observation = identity["observation"]
    workload = identity["fixed_workload"]
    assert isinstance(observation, dict)
    assert isinstance(workload, dict)
    return {
        "schema": ACCEPTED_VERSION_SCHEMA,
        "runtime_base": observation["runtime_base"],
        "image_length": workload["static_length"],
        "relocated_sha256": observation["relocated_sha256"],
        "normalized_sha256": observation["normalized_sha256"],
        "static_sha256": workload["static_sha256"],
        "route_id": workload["route_id"],
        "difficulty_index": workload["difficulty_index"],
        "stage_route_index": workload["stage_route_index"],
        "gameplay_epoch": observation["gameplay_epoch"],
        "decision_frame": observation["decision_frame"],
        "snapshot_frame": observation["snapshot_frame"],
    }


def trace_delivery_rows(
    path: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str, int]:
    batch_rows: list[dict[str, Any]] = []
    preparation_rows: list[dict[str, Any]] = []
    trace_digest = hashlib.sha256()
    byte_count = 0
    with path.open("rb") as source:
        for line_number, raw_line in enumerate(source, 1):
            trace_digest.update(raw_line)
            byte_count += len(raw_line)
            prefix = raw_line[:512]
            is_batch = (
                b'"kind":"auxiliary_vm_batch"' in prefix
                or b'"kind": "auxiliary_vm_batch"' in prefix
            )
            is_preparation = (
                b'"kind":"auxiliary_ecl_event_preparation"' in prefix
                or b'"kind": "auxiliary_ecl_event_preparation"' in prefix
            )
            if not is_batch and not is_preparation:
                continue
            try:
                row = json.loads(raw_line)
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise AuxiliaryEclEventPhysicalAuditError(
                    f"trace line {line_number} is invalid JSON"
                ) from error
            if not isinstance(row, dict):
                raise AuxiliaryEclEventPhysicalAuditError(
                    f"trace line {line_number} is not an object"
                )
            if is_batch:
                batch_rows.append(row)
            else:
                preparation_rows.append(row)
    return (
        batch_rows,
        preparation_rows,
        trace_digest.hexdigest(),
        byte_count,
    )


def trace_event_rows(
    path: Path,
) -> tuple[list[dict[str, Any]], str, int]:
    rows, _, trace_sha256, byte_count = trace_delivery_rows(path)
    return rows, trace_sha256, byte_count


__all__ = [
    "AuxiliaryEclEventPhysicalAuditError",
    "digest",
    "distribution",
    "expected_runtime_version",
    "finite_nonnegative",
    "session_record",
    "trace_delivery_rows",
    "trace_event_rows",
    "within",
]
