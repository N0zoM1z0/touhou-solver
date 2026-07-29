"""Strict physical report for schema-v5 cached/bundled event delivery."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

from analysis.auxiliary_vm_batch_trace import scan_trace
from analysis.th08_runtime_ecl_identity_audit import (
    STAGE5_STATIC_LABEL,
    STAGE5_STATIC_LENGTH,
    STAGE5_STATIC_SHA256,
    audit as audit_runtime_ecl_identity,
)
from th08_ecl_tool.core import parse_ecl
from th08_live.auxiliary_vm.trace_service import (
    AUXILIARY_VM_BATCH_EVENT_V2_TRACE_SCHEMA_VERSION,
)

from .cache_oracle import IndependentIntentLru
from .physical_gate_support import (
    AuxiliaryEclEventPhysicalAuditError,
    digest,
    distribution,
    expected_runtime_version,
    finite_nonnegative,
    session_record,
    trace_batch_line_bytes,
    trace_delivery_rows,
    within,
)
from .physical_replay import (
    AuxiliaryEclEventReplayError,
    BatchReplaySummary,
    ReplayProgram,
    audit_event_batch_v2,
)
from .replay_evidence import array, mapping


REPORT_SCHEMA = "th08-g5-auxiliary-ecl-event-physical-gate-v2"
REPORT_AUTHORITY = "physical_trace_only_no_action_authority"
PREPARATION_SCHEMA = "th08-auxiliary-ecl-event-preparation-v1"
EVENT_DERIVE_LIMIT_MS = (0.50, 1.00, 3.00)
REPLAY_COMPACT_LIMIT_MS = (0.50, 1.00, 3.00)
TRACE_EMIT_LIMIT_MS = (1.00, 2.00, 6.00)
TRANSACTION_TOTAL_LIMIT_MS = (3.00, 5.00, 15.00)
PREPARATION_MAXIMUM_MS = 8.0
CACHE_CAPACITY = 512


@dataclass(frozen=True)
class DeliveryTraceData:
    """Version-neutral physical rows and independently scanned transport."""

    rows: list[dict[str, Any]]
    preparations: list[dict[str, Any]]
    trace_sha256: str
    trace_bytes: int
    batch_count: int
    batch_schema_versions: Counter[int]
    batch_statuses: Counter[str]
    validation_errors: list[str]
    process_reads: list[float]
    decision_deltas: list[float]
    batch_line_bytes: list[float]


def standalone_delivery_trace_data(
    trace_path: Path,
    *,
    include_batch_line_bytes: bool,
) -> DeliveryTraceData:
    """Load the historical top-level auxiliary-batch transport."""

    scan = scan_trace(trace_path, audit_batches=True)
    rows, preparations, trace_sha256, trace_bytes = trace_delivery_rows(
        trace_path
    )
    if scan.sha256 != trace_sha256 or scan.byte_count != trace_bytes:
        raise AuxiliaryEclEventPhysicalAuditError(
            "independent trace digests disagree"
        )
    return DeliveryTraceData(
        rows=rows,
        preparations=preparations,
        trace_sha256=trace_sha256,
        trace_bytes=trace_bytes,
        batch_count=scan.batch_count,
        batch_schema_versions=scan.batch_schema_versions,
        batch_statuses=scan.batch_statuses,
        validation_errors=scan.validation_errors,
        process_reads=scan.process_reads,
        decision_deltas=scan.decision_deltas,
        batch_line_bytes=(
            trace_batch_line_bytes(trace_path)
            if include_batch_line_bytes
            else []
        ),
    )


def _preparation_record(
    rows: list[dict[str, Any]],
    *,
    expected_version: dict[str, object],
    first_batch_frame: int,
    preparation_schema: str = PREPARATION_SCHEMA,
    preparation_maximum_ms: float = PREPARATION_MAXIMUM_MS,
    require_epoch_separation: bool = False,
) -> tuple[dict[str, object], bool]:
    if len(rows) != 1:
        return (
            {
                "count": len(rows),
                "status": "missing_or_multiple",
            },
            False,
        )
    row = rows[0]
    timing = mapping(row.get("timing_ms"), "preparation.timing_ms")
    bind_ms = finite_nonnegative(
        timing.get("program_bind"),
        "preparation.program_bind",
    )
    total_ms = finite_nonnegative(
        timing.get("total"),
        "preparation.total",
    )
    configuration = mapping(
        row.get("configuration"),
        "preparation.configuration",
    )
    expected_program_identity = {
        key: expected_version[key]
        for key in (
            "runtime_base",
            "image_length",
            "relocated_sha256",
            "normalized_sha256",
            "static_sha256",
            "route_id",
            "difficulty_index",
            "stage_route_index",
        )
    }
    version_specific_pass = True
    version_specific_record: dict[str, object] = {}
    if require_epoch_separation:
        version_specific_pass = bool(
            row.get("accepted_gameplay_epoch")
            == expected_version["gameplay_epoch"]
            and row.get("observation_gameplay_epoch")
            == row.get("gameplay_epoch")
            and row.get("observation_epoch_semantics")
            == "provenance_not_program_mutation"
            and row.get("program_identity") == expected_program_identity
            and row.get("program_identity_key")
            == [
                expected_program_identity[key]
                for key in (
                    "runtime_base",
                    "image_length",
                    "relocated_sha256",
                    "normalized_sha256",
                    "static_sha256",
                    "route_id",
                    "difficulty_index",
                    "stage_route_index",
                )
            ]
            and row.get("prevalidated_instruction_count") == 1664
            and row.get("bound_instruction_count") == 9
        )
        version_specific_record = {
            "accepted_gameplay_epoch": row.get(
                "accepted_gameplay_epoch"
            ),
            "observation_gameplay_epoch": row.get(
                "observation_gameplay_epoch"
            ),
            "observation_epoch_semantics": row.get(
                "observation_epoch_semantics"
            ),
            "program_identity": row.get("program_identity"),
            "program_identity_key": row.get("program_identity_key"),
            "prevalidated_instruction_count": row.get(
                "prevalidated_instruction_count"
            ),
            "bound_instruction_count": row.get(
                "bound_instruction_count"
            ),
        }
    passed = bool(
        row.get("kind") == "auxiliary_ecl_event_preparation"
        and row.get("schema") == preparation_schema
        and row.get("authority") == "trace_only_no_action_authority"
        and row.get("status") == "success"
        and row.get("error") is None
        and row.get("runtime_version") == expected_version
        and row.get("gameplay_epoch")
        == expected_version["gameplay_epoch"]
        and row.get("stage_route_index") == 5
        and isinstance(row.get("decision_frame"), int)
        and row["decision_frame"] < first_batch_frame
        and row.get("snapshot_frame") is not None
        and configuration
        == {
            "active_difficulty_mask": 0x08,
            "maximum_instructions": 64,
            "maximum_physical_steps": 65536,
            "cache_capacity": CACHE_CAPACITY,
            "target_horizons": {"69": 16, "72": 16, "73": 60},
        }
        and bind_ms <= total_ms
        and total_ms <= preparation_maximum_ms
        and version_specific_pass
    )
    return (
        {
            "count": 1,
            "status": row.get("status"),
            "decision_frame": row.get("decision_frame"),
            "snapshot_frame": row.get("snapshot_frame"),
            "configuration": configuration,
            **version_specific_record,
            "timing_ms": {
                "program_bind": bind_ms,
                "total": total_ms,
                "maximum": preparation_maximum_ms,
            },
        },
        passed,
    )


def _empty_row_valid(row: dict[str, Any]) -> bool:
    observation = mapping(row.get("observation"), "empty.observation")
    event = mapping(row.get("event_derivation"), "empty.event")
    lowering = mapping(event.get("lowering"), "empty.lowering")
    bundle = mapping(
        observation.get("replay_state_bundle"),
        "empty.replay_state_bundle",
    )
    return bool(
        observation.get("record_count") == 0
        and observation.get("non_null_context_count") == 0
        and observation.get("usable_context_count") == 0
        and observation.get("state_payload_bytes") == 0
        and array(observation.get("records"), "empty.records") == []
        and bundle.get("blob_count") == 0
        and bundle.get("uncompressed_bytes") == 0
        and event.get("status") == "empty_complete"
        and event.get("request_count") == 0
        and event.get("complete_count") == 0
        and event.get("unknown_count") == 0
        and array(event.get("requests"), "empty.requests") == []
        and lowering.get("request_count") == 0
        and lowering.get("unique_result_count") == 0
    )


def build_delivery_physical_report(
    trace_path: Path,
    baseline_path: Path,
    session_path: Path,
    ecl_path: Path,
    *,
    expected_ecl_sha256: str = STAGE5_STATIC_SHA256,
    report_schema: str = REPORT_SCHEMA,
    batch_schema_version: int = (
        AUXILIARY_VM_BATCH_EVENT_V2_TRACE_SCHEMA_VERSION
    ),
    preparation_schema: str = PREPARATION_SCHEMA,
    preparation_maximum_ms: float = PREPARATION_MAXIMUM_MS,
    require_same_gameplay_epoch: bool = True,
    audit_batch: Callable[..., BatchReplaySummary] = audit_event_batch_v2,
    survival_hit_maximum: int | None = None,
    empty_row_valid: Callable[[dict[str, Any]], bool] = _empty_row_valid,
    batch_line_maximum: int | None = None,
    trace_data: DeliveryTraceData | None = None,
    trace_emit_limits: tuple[float, float, float] | None = (
        TRACE_EMIT_LIMIT_MS
    ),
) -> dict[str, object]:
    image = ecl_path.read_bytes()
    actual_ecl_sha256 = hashlib.sha256(image).hexdigest()
    if (
        expected_ecl_sha256 != STAGE5_STATIC_SHA256
        or actual_ecl_sha256 != expected_ecl_sha256
        or len(image) != STAGE5_STATIC_LENGTH
    ):
        raise AuxiliaryEclEventPhysicalAuditError(
            "static Stage-5 ECL identity is invalid"
        )
    ecl = parse_ecl(ecl_path)
    if ecl.sha256 != actual_ecl_sha256:
        raise AuxiliaryEclEventPhysicalAuditError(
            "parsed ECL identity differs from exact bytes"
        )
    identity = audit_runtime_ecl_identity(
        trace_path,
        expected_static_label=STAGE5_STATIC_LABEL,
        expected_static_length=STAGE5_STATIC_LENGTH,
        expected_static_sha256=STAGE5_STATIC_SHA256,
    )
    expected_version = expected_runtime_version(identity)
    runtime_base = expected_version["runtime_base"]
    assert isinstance(runtime_base, int)
    program = ReplayProgram.from_ecl(
        ecl,
        image,
        runtime_base=runtime_base,
    )

    baseline = scan_trace(baseline_path, audit_batches=False)
    delivery = (
        standalone_delivery_trace_data(
            trace_path,
            include_batch_line_bytes=batch_line_maximum is not None,
        )
        if trace_data is None
        else trace_data
    )
    rows = delivery.rows
    preparations = delivery.preparations
    trace_sha256 = delivery.trace_sha256
    trace_bytes = delivery.trace_bytes
    batch_line_bytes = delivery.batch_line_bytes
    session, session_pass = session_record(session_path)
    first_batch_frame = rows[0].get("frame") if rows else -1
    if isinstance(first_batch_frame, bool) or not isinstance(
        first_batch_frame,
        int,
    ):
        raise AuxiliaryEclEventPhysicalAuditError(
            "first batch frame is invalid"
        )
    preparation, preparation_pass = _preparation_record(
        preparations,
        expected_version=expected_version,
        first_batch_frame=first_batch_frame,
        preparation_schema=preparation_schema,
        preparation_maximum_ms=preparation_maximum_ms,
        require_epoch_separation=not require_same_gameplay_epoch,
    )

    event_statuses: Counter[str] = Counter()
    targets: Counter[int] = Counter()
    request_count = 0
    complete_count = 0
    unknown_count = 0
    replayable_record_count = 0
    replay_blob_count = 0
    empty_frames: list[int] = []
    seen_nonempty = False
    empty_prefix_valid = True
    derive_ms: list[float] = []
    compact_ms: list[float] = []
    previous_emit_ms: list[float] = []
    total_ms: list[float] = []
    cache_oracle = IndependentIntentLru(CACHE_CAPACITY)
    cache_totals: Counter[str] = Counter()
    batch_gameplay_epochs: Counter[int] = Counter()
    for index, row in enumerate(rows):
        context = f"batch[{index}]"
        if (
            row.get("schema_version")
            != batch_schema_version
            or row.get("status") != "success"
            or row.get("stage_route_index") != 5
            or row.get("spell_id") != 107
            or (
                require_same_gameplay_epoch
                and row.get("gameplay_epoch")
                != expected_version["gameplay_epoch"]
            )
        ):
            raise AuxiliaryEclEventPhysicalAuditError(
                f"{context} differs from the fixed schema-v"
                f"{batch_schema_version} workload"
            )
        timing = mapping(row.get("timing_ms"), f"{context}.timing")
        derive_ms.append(
            finite_nonnegative(
                timing.get("event_derive"),
                f"{context}.event_derive",
            )
        )
        compact_ms.append(
            finite_nonnegative(
                timing.get("compact"),
                f"{context}.compact",
            )
        )
        total_ms.append(
            finite_nonnegative(
                timing.get("total"),
                f"{context}.total",
            )
        )
        previous_emit = timing.get("previous_emit")
        if previous_emit is not None:
            previous_emit_ms.append(
                finite_nonnegative(
                    previous_emit,
                    f"{context}.previous_emit",
                )
            )
        try:
            replay = audit_batch(
                row,
                expected_runtime_version=expected_version,
                program=program,
                context=context,
            )
        except AuxiliaryEclEventReplayError as error:
            raise AuxiliaryEclEventPhysicalAuditError(str(error)) from error
        event = mapping(row.get("event_derivation"), f"{context}.event")
        batch_epoch = row.get("gameplay_epoch")
        if isinstance(batch_epoch, bool) or not isinstance(batch_epoch, int):
            raise AuxiliaryEclEventPhysicalAuditError(
                f"{context} gameplay epoch is invalid"
            )
        batch_gameplay_epochs[batch_epoch] += 1
        cache = mapping(event.get("cache"), f"{context}.cache")
        expected_cache = cache_oracle.observe(replay.intent_keys).record()
        if cache != expected_cache:
            raise AuxiliaryEclEventPhysicalAuditError(
                f"{context} cache statistics differ from independent LRU"
            )
        cache_totals.update(
            {
                "request_local_hits": expected_cache[
                    "request_local_hits"
                ],
                "persistent_hits": expected_cache["persistent_hits"],
                "misses": expected_cache["misses"],
                "evictions": expected_cache["evictions"],
            }
        )
        observation = mapping(
            row.get("observation"),
            f"{context}.observation",
        )
        bundle = mapping(
            observation.get("replay_state_bundle"),
            f"{context}.bundle",
        )
        blob_count = bundle.get("blob_count")
        if isinstance(blob_count, bool) or not isinstance(blob_count, int):
            raise AuxiliaryEclEventPhysicalAuditError(
                f"{context} replay blob count is invalid"
            )
        replay_blob_count += blob_count
        event_status = str(event.get("status"))
        event_statuses[event_status] += 1
        if replay.request_count == 0:
            frame = row.get("frame")
            assert isinstance(frame, int)
            empty_frames.append(frame)
            empty_prefix_valid = (
                empty_prefix_valid
                and not seen_nonempty
                and empty_row_valid(row)
            )
        else:
            seen_nonempty = True
        request_count += replay.request_count
        complete_count += replay.complete_count
        unknown_count += replay.unknown_count
        replayable_record_count += replay.replayable_record_count
        targets.update(dict(replay.target_counts))

    event_distribution = distribution(derive_ms)
    compact_distribution = distribution(compact_ms)
    emit_distribution = distribution(previous_emit_ms)
    total_distribution = distribution(total_ms)
    cadence = distribution(delivery.decision_deltas)
    baseline_cadence = distribution(baseline.decision_deltas)
    expected_statuses = Counter({"success": len(rows) - len(empty_frames)})
    if empty_frames:
        expected_statuses["empty_complete"] = len(empty_frames)
    gates: dict[str, bool] = {
        f"schema_v{batch_schema_version}_rows_present": bool(rows)
        and delivery.batch_schema_versions
        == Counter(
            {
                batch_schema_version: len(rows)
            }
        ),
        "preparation_exact_and_bounded": preparation_pass,
        "transport_success_and_coherent": bool(rows)
        and delivery.batch_statuses == Counter({"success": len(rows)})
        and not delivery.validation_errors,
        "exact_runtime_version_on_every_batch": bool(rows),
        "empty_prefix_valid": bool(seen_nonempty and empty_prefix_valid),
        "event_status_success_or_empty": event_statuses
        == expected_statuses,
        "replay_bundle_present": replay_blob_count > 0,
        "independent_oracle_parity": request_count > 0
        and complete_count == request_count
        and unknown_count == 0,
        "independent_cache_parity": request_count
        == (
            cache_totals["request_local_hits"]
            + cache_totals["persistent_hits"]
            + cache_totals["misses"]
        ),
        "contracted_targets_only": bool(targets)
        and set(targets).issubset({69, 72, 73}),
        "no_added_process_reads_in_event_layer": bool(rows)
        and not delivery.validation_errors,
        "event_derive_timing": within(
            event_distribution,
            EVENT_DERIVE_LIMIT_MS,
        ),
        "replay_compact_timing": within(
            compact_distribution,
            REPLAY_COMPACT_LIMIT_MS,
        ),
        "transaction_total_timing": within(
            total_distribution,
            TRANSACTION_TOTAL_LIMIT_MS,
        ),
        "decision_cadence_p95_regression_at_most_one_frame": bool(
            cadence is not None
            and baseline_cadence is not None
            and cadence["p95"] <= baseline_cadence["p95"] + 1.0
        ),
        "hard_no_bomb_route_complete": bool(
            identity["physical_scope"]["hard_no_bomb_passed"]
        ),
        "accepted_session_cleanup": session_pass,
    }
    if trace_emit_limits is not None:
        gates["trace_emit_timing"] = within(
            emit_distribution,
            trace_emit_limits,
        )
    if batch_line_maximum is not None:
        gates["projected_batch_line_maximum"] = bool(
            batch_line_bytes
            and max(batch_line_bytes) <= batch_line_maximum
        )
    survival_hit_count: int | None = None
    if survival_hit_maximum is not None:
        raw_session = json.loads(session_path.read_text(encoding="utf-8"))
        raw_summary = (
            raw_session.get("agent_summary")
            if isinstance(raw_session, dict)
            else None
        )
        raw_hit_frames = (
            raw_summary.get("hit_frames")
            if isinstance(raw_summary, dict)
            else None
        )
        if isinstance(raw_hit_frames, list) and all(
            isinstance(item, int) and not isinstance(item, bool)
            for item in raw_hit_frames
        ):
            survival_hit_count = len(raw_hit_frames)
        gates["stage5_survival_regression_boundary"] = bool(
            survival_hit_count is not None
            and survival_hit_count <= survival_hit_maximum
        )
    report: dict[str, object] = {
        "schema": report_schema,
        "authority": REPORT_AUTHORITY,
        "source": {
            "trace": str(trace_path),
            "trace_bytes": trace_bytes,
            "trace_sha256": trace_sha256,
            "baseline": str(baseline_path),
            "baseline_sha256": baseline.sha256,
            "session": str(session_path),
        },
        "static_ecl": {
            "path": str(ecl_path),
            "bytes": len(image),
            "sha256": actual_ecl_sha256,
        },
        "runtime_version": expected_version,
        "observation_epochs": {
            "accepted_gameplay_epoch": expected_version[
                "gameplay_epoch"
            ],
            "batch_gameplay_epochs": {
                str(key): value
                for key, value in sorted(batch_gameplay_epochs.items())
            },
            "cross_epoch_observed": any(
                key != expected_version["gameplay_epoch"]
                for key in batch_gameplay_epochs
            ),
        },
        "preparation": preparation,
        "session": session,
        "transport": {
            "batch_count": delivery.batch_count,
            "schema_versions": {
                str(key): value
                for key, value in sorted(
                    delivery.batch_schema_versions.items()
                )
            },
            "statuses": dict(sorted(delivery.batch_statuses.items())),
            "validation_errors": delivery.validation_errors,
            "process_read_count": distribution(delivery.process_reads),
        },
        "replay": {
            "event_statuses": dict(sorted(event_statuses.items())),
            "empty_prefix_frames": empty_frames,
            "request_count": request_count,
            "complete_count": complete_count,
            "unknown_count": unknown_count,
            "replayable_record_count": replayable_record_count,
            "replay_blob_count": replay_blob_count,
            "target_subroutines": {
                str(key): value for key, value in sorted(targets.items())
            },
            "physical_timing": "unavailable_timer_domain_only",
        },
        "cache": {
            **dict(sorted(cache_totals.items())),
            "entries_after": cache_oracle.observe(()).entries_after,
            "capacity": CACHE_CAPACITY,
        },
        "timing_ms": {
            "event_derive": event_distribution,
            "replay_compact": compact_distribution,
            "previous_trace_emit": emit_distribution,
            "transaction_total": total_distribution,
            "decision_frame_delta": cadence,
            "baseline_decision_frame_delta": baseline_cadence,
        },
        "limits_ms": {
            "preparation_maximum": preparation_maximum_ms,
            "event_derive_p95_p99_max": list(EVENT_DERIVE_LIMIT_MS),
            "replay_compact_p95_p99_max": list(
                REPLAY_COMPACT_LIMIT_MS
            ),
            "transaction_total_p95_p99_max": list(
                TRANSACTION_TOTAL_LIMIT_MS
            ),
            "cadence_p95_regression_frames": 1.0,
        },
        "gates": gates,
        "passed": all(gates.values()),
        "authority_boundary": {
            "runtime_instruction_bytes": "exact_for_this_immutable_image",
            "auxiliary_literal_fire_timer_schedule": (
                "independently_replayed_for_observed_contexts"
            ),
            "physical_frame_timing": "none",
            "source_lifetime": "none",
            "realized_birth_geometry": "none",
            "planner": "none",
            "physical_action": "none",
        },
    }
    if trace_emit_limits is not None:
        limits_ms = report["limits_ms"]
        assert isinstance(limits_ms, dict)
        limits_ms["trace_emit_p95_p99_max"] = list(trace_emit_limits)
    if batch_line_maximum is not None:
        report["transport"]["batch_line_bytes"] = distribution(
            batch_line_bytes
        )
        report["limits_bytes"] = {
            "projected_batch_line_maximum": batch_line_maximum,
        }
    if survival_hit_maximum is not None:
        report["survival_regression_boundary"] = {
            "hit_count": survival_hit_count,
            "maximum": survival_hit_maximum,
            "single_run_only": True,
            "consecutive_run_requirement": 2,
        }
    report["report_digest"] = digest(report)
    return report


def build_physical_report_v2(
    trace_path: Path,
    baseline_path: Path,
    session_path: Path,
    ecl_path: Path,
    *,
    expected_ecl_sha256: str = STAGE5_STATIC_SHA256,
) -> dict[str, object]:
    return build_delivery_physical_report(
        trace_path,
        baseline_path,
        session_path,
        ecl_path,
        expected_ecl_sha256=expected_ecl_sha256,
    )


def write_report_v2(report: dict[str, object], path: Path) -> None:
    import json

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )


__all__ = [
    "AuxiliaryEclEventPhysicalAuditError",
    "CACHE_CAPACITY",
    "DeliveryTraceData",
    "EVENT_DERIVE_LIMIT_MS",
    "PREPARATION_MAXIMUM_MS",
    "REPLAY_COMPACT_LIMIT_MS",
    "REPORT_AUTHORITY",
    "REPORT_SCHEMA",
    "TRACE_EMIT_LIMIT_MS",
    "TRANSACTION_TOTAL_LIMIT_MS",
    "build_delivery_physical_report",
    "build_physical_report_v2",
    "standalone_delivery_trace_data",
    "write_report_v2",
]
