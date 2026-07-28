"""Deterministic report builder for auxiliary ECL pointer observations."""

from __future__ import annotations

from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
from typing import Iterable

from analysis.main_vm_source_join.model import InventoryCapture
from analysis.main_vm_source_join.trace import scan_schema11_trace

from .analysis import analyze_pointer_dynamics


REPORT_SCHEMA = "th08-g5-auxiliary-pointer-density-v1"
ACTIVE_VM_PROJECTION_BYTES = 104
ALLOCATED_AUXILIARY_CONTEXT_BYTES = 0x24B0


class AuxiliaryPointerReportError(ValueError):
    """Raised when retained evidence cannot support a strict report."""


def canonical_report_bytes(report: dict[str, object]) -> bytes:
    return (
        json.dumps(
            report,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("ascii")
        + b"\n"
    )


def _quantile(values: tuple[int, ...], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = fraction * (len(ordered) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(ordered[lower])
    weight = position - lower
    return round(
        ordered[lower] * (1.0 - weight) + ordered[upper] * weight,
        6,
    )


def _summary(values: Iterable[int]) -> dict[str, float | int]:
    materialized = tuple(values)
    return {
        "count": len(materialized),
        "min": min(materialized, default=0),
        "p50": _quantile(materialized, 0.50),
        "p95": _quantile(materialized, 0.95),
        "p99": _quantile(materialized, 0.99),
        "max": max(materialized, default=0),
    }


def _capture_counts(
    capture: InventoryCapture,
) -> tuple[int, int, tuple[int, ...]]:
    owner_counts = tuple(
        owner.non_null_count for owner in capture.auxiliary_pointer_owners
    )
    return (
        len(capture.auxiliary_pointer_owners),
        sum(owner_counts),
        owner_counts,
    )


def _phase_key(capture: InventoryCapture) -> str:
    return (
        "nonspell"
        if capture.scope.spell_id is None
        else str(capture.scope.spell_id)
    )


def _per_phase(captures: tuple[InventoryCapture, ...]) -> dict[str, object]:
    grouped: dict[str, list[InventoryCapture]] = defaultdict(list)
    for capture in captures:
        grouped[_phase_key(capture)].append(capture)
    return {
        phase: {
            "captures": len(rows),
            "active_owners_per_capture": _summary(
                len(row.auxiliary_pointer_owners) for row in rows
            ),
            "non_null_contexts_per_capture": _summary(
                sum(
                    owner.non_null_count
                    for owner in row.auxiliary_pointer_owners
                )
                for row in rows
            ),
        }
        for phase, rows in sorted(grouped.items())
    }


def build_auxiliary_pointer_report(trace_path: Path) -> dict[str, object]:
    trace = scan_schema11_trace(trace_path)
    if trace.schema11_rows:
        raise AuxiliaryPointerReportError(
            "pointer density requires a pure schema-12 trace"
        )
    if trace.schema12_rows != len(trace.captures):
        raise AuxiliaryPointerReportError(
            "schema-12 rows and joined captures differ"
        )
    if trace.invalid_auxiliary_contexts:
        raise AuxiliaryPointerReportError(
            "trace contains invalid auxiliary context pointers"
        )
    captures = trace.captures
    owner_counts: list[int] = []
    context_counts: list[int] = []
    per_owner_counts: list[int] = []
    for capture in captures:
        owners, contexts, owner_non_null = _capture_counts(capture)
        owner_counts.append(owners)
        context_counts.append(contexts)
        per_owner_counts.extend(owner_non_null)

    dynamics = analyze_pointer_dynamics(captures)
    fully_bounded_runs = tuple(
        run
        for run in dynamics.observed_runs
        if not run.left_censored and not run.right_censored
    )
    reused_pointers = {
        pointer: sorted([list(token) for token in tokens])
        for pointer, tokens in dynamics.pointer_tokens.items()
        if len(tokens) > 1
    }
    minimum_payloads = tuple(
        count * ACTIVE_VM_PROJECTION_BYTES for count in context_counts
    )
    full_context_payloads = tuple(
        count * ALLOCATED_AUXILIARY_CONTEXT_BYTES
        for count in context_counts
    )
    report: dict[str, object] = {
        "schema": REPORT_SCHEMA,
        "authority": {
            "status": "offline_observation_only",
            "permits": [
                "auxiliary_pointer_density_measurement",
                "observation_level_pointer_churn_measurement",
                "bounded_capture_delivery_design",
            ],
            "forbids": [
                "future_geometry",
                "source_completeness",
                "planner_input",
                "feasibility",
                "live_action",
            ],
        },
        "provenance": {
            "trace_path": str(trace_path),
            "trace_sha256": trace.trace_sha256,
            "trace_bytes": trace.trace_bytes,
            "trace_lines": trace.trace_lines,
            "schema12_rows": trace.schema12_rows,
        },
        "scope": {
            "captures": len(captures),
            "stable_enemy_prefix_brackets": sum(
                capture.stable for capture in captures
            ),
            "invalid_active_main_vms": trace.invalid_active_vm_rows,
            "invalid_auxiliary_context_pointers": (
                trace.invalid_auxiliary_contexts
            ),
            "identity_limit": (
                "slot and enemy address do not distinguish reincarnations "
                "that reuse the same ordinary-enemy pool slot"
            ),
        },
        "capture_density": {
            "active_owners_per_capture": _summary(owner_counts),
            "non_null_contexts_per_capture": _summary(context_counts),
            "non_null_contexts_per_active_owner": _summary(per_owner_counts),
            "per_phase": _per_phase(captures),
        },
        "observed_dynamics": {
            "comparable_capture_pairs": dynamics.comparable_capture_pairs,
            "capture_frame_gap": _summary(dynamics.capture_frame_gaps),
            "owner_slot_transitions": dynamics.owner_transitions,
            "pointer_transitions_for_continuing_owner_slots": (
                dynamics.pointer_transitions
            ),
            "unique_non_null_pointer_values": len(dynamics.pointer_tokens),
            "pointer_values_seen_at_multiple_slot_indices": len(
                reused_pointers
            ),
            "reused_pointer_samples": [
                {
                    "pointer": pointer,
                    "pointer_hex": f"{pointer:#010x}",
                    "slot_auxiliary_indices": tokens,
                }
                for pointer, tokens in list(sorted(reused_pointers.items()))[
                    :32
                ]
            ],
            "observed_non_null_runs": len(dynamics.observed_runs),
            "fully_bounded_runs": len(fully_bounded_runs),
            "run_observation_count": _summary(
                run.observation_count for run in dynamics.observed_runs
            ),
            "run_observed_frame_span": _summary(
                run.observed_frame_span for run in dynamics.observed_runs
            ),
            "fully_bounded_run_observed_frame_span": _summary(
                run.observed_frame_span for run in fully_bounded_runs
            ),
            "run_semantics": (
                "Runs are consecutive observation agreement, not exact "
                "allocation lifetimes; boundary runs are censored."
            ),
        },
        "bounded_capture_payload": {
            "declared_maximum_contexts_from_64_owners": 64 * 4,
            "minimum_active_vm_projection_bytes_per_context": (
                ACTIVE_VM_PROJECTION_BYTES
            ),
            "minimum_projection_payload_per_capture": _summary(
                minimum_payloads
            ),
            "full_allocated_context_bytes_per_context": (
                ALLOCATED_AUXILIARY_CONTEXT_BYTES
            ),
            "full_context_payload_per_capture": _summary(
                full_context_payloads
            ),
            "excludes": [
                "owner_pointer_recheck_transport",
                "native_batch_headers",
                "call_depth_and_required_saved_frames",
            ],
        },
        "delivery_decision": {
            "selected_design": "native_compact_batch",
            "rationale": (
                "One Python RPM per pointer would add a data-dependent 0..34 "
                "calls on this workload and up to 256 under the declared "
                "first-64/four-context scope. A native compact batch can "
                "bound pointer validation, active-VM projection, saved-frame "
                "selection, and owner recheck under one explicit "
                "frame/version bracket."
            ),
            "phase_b_status": "design_selected_not_implemented",
            "fallback": (
                "On churn, unreadable state, deadline, or version mismatch, "
                "publish no auxiliary state and preserve existing live policy."
            ),
        },
        "gates": {
            "pure_schema12_trace": trace.schema12_rows > 0,
            "all_prefix_brackets_stable": all(
                capture.stable for capture in captures
            ),
            "zero_invalid_auxiliary_pointers": (
                trace.invalid_auxiliary_contexts == 0
            ),
            "pointer_presence_has_no_action_authority": True,
        },
    }
    report["report_digest"] = hashlib.sha256(
        canonical_report_bytes(report)
    ).hexdigest()
    return report


__all__ = [
    "AuxiliaryPointerReportError",
    "build_auxiliary_pointer_report",
    "canonical_report_bytes",
]
