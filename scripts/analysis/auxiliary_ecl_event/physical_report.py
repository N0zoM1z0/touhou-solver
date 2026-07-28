"""Strict physical gate for replay-capable auxiliary ECL event delivery."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path

from analysis.auxiliary_vm_batch_trace import scan_trace
from analysis.th08_runtime_ecl_identity_audit import (
    STAGE5_STATIC_LABEL,
    STAGE5_STATIC_LENGTH,
    STAGE5_STATIC_SHA256,
    audit as audit_runtime_ecl_identity,
)
from th08_ecl_tool.core import parse_ecl
from th08_live.auxiliary_vm.trace_service import (
    AUXILIARY_VM_BATCH_EVENT_TRACE_SCHEMA_VERSION,
)

from .physical_replay import (
    AuxiliaryEclEventReplayError,
    ReplayProgram,
    audit_event_batch,
)
from .physical_gate_support import (
    AuxiliaryEclEventPhysicalAuditError,
    digest,
    distribution,
    expected_runtime_version,
    finite_nonnegative,
    session_record,
    trace_event_rows,
    within,
)


REPORT_SCHEMA = "th08-g5-auxiliary-ecl-event-physical-gate-v1"
REPORT_AUTHORITY = "physical_trace_only_no_action_authority"
EVENT_DERIVE_LIMIT_MS = (0.50, 1.00, 3.00)
REPLAY_COMPACT_LIMIT_MS = (0.50, 1.00, 3.00)
TRACE_EMIT_LIMIT_MS = (1.00, 2.00, 6.00)
TRANSACTION_TOTAL_LIMIT_MS = (3.00, 5.00, 15.00)


def build_physical_report(
    trace_path: Path,
    baseline_path: Path,
    session_path: Path,
    ecl_path: Path,
    *,
    expected_ecl_sha256: str = STAGE5_STATIC_SHA256,
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

    scan = scan_trace(trace_path, audit_batches=True)
    baseline = scan_trace(baseline_path, audit_batches=False)
    rows, trace_sha256, trace_bytes = trace_event_rows(trace_path)
    if scan.sha256 != trace_sha256 or scan.byte_count != trace_bytes:
        raise AuxiliaryEclEventPhysicalAuditError(
            "independent trace digests disagree"
        )
    session, session_pass = session_record(session_path)

    event_statuses: Counter[str] = Counter()
    targets: Counter[int] = Counter()
    request_count = 0
    lowerable_count = 0
    complete_count = 0
    unknown_count = 0
    replayable_record_count = 0
    derive_ms: list[float] = []
    compact_ms: list[float] = []
    previous_emit_ms: list[float] = []
    total_ms: list[float] = []
    for index, row in enumerate(rows):
        context = f"batch[{index}]"
        if row.get("schema_version") != (
            AUXILIARY_VM_BATCH_EVENT_TRACE_SCHEMA_VERSION
        ):
            raise AuxiliaryEclEventPhysicalAuditError(
                f"{context} is not schema v4"
            )
        if (
            row.get("status") != "success"
            or row.get("stage_route_index") != 5
            or row.get("spell_id") != 107
            or row.get("gameplay_epoch")
            != expected_version["gameplay_epoch"]
        ):
            raise AuxiliaryEclEventPhysicalAuditError(
                f"{context} differs from the fixed spell-107 workload"
            )
        timing = row.get("timing_ms")
        if not isinstance(timing, dict):
            raise AuxiliaryEclEventPhysicalAuditError(
                f"{context} timing is not an object"
            )
        derive = finite_nonnegative(
            timing.get("event_derive"),
            f"{context}.event_derive",
        )
        compact = finite_nonnegative(
            timing.get("compact"),
            f"{context}.compact",
        )
        total = finite_nonnegative(
            timing.get("total"),
            f"{context}.total",
        )
        derive_ms.append(derive)
        compact_ms.append(compact)
        total_ms.append(total)
        previous_emit = timing.get("previous_emit")
        if previous_emit is not None:
            previous_emit_ms.append(
                finite_nonnegative(
                    previous_emit,
                    f"{context}.previous_emit",
                )
            )
        try:
            replay = audit_event_batch(
                row,
                expected_runtime_version=expected_version,
                program=program,
                context=context,
            )
        except AuxiliaryEclEventReplayError as error:
            raise AuxiliaryEclEventPhysicalAuditError(str(error)) from error
        event = row["event_derivation"]
        assert isinstance(event, dict)
        event_statuses[str(event["status"])] += 1
        request_count += replay.request_count
        lowerable_count += replay.lowerable_count
        complete_count += replay.complete_count
        unknown_count += replay.unknown_count
        replayable_record_count += replay.replayable_record_count
        targets.update(dict(replay.target_counts))

    event_distribution = distribution(derive_ms)
    compact_distribution = distribution(compact_ms)
    emit_distribution = distribution(previous_emit_ms)
    total_distribution = distribution(total_ms)
    cadence = distribution(scan.decision_deltas)
    baseline_cadence = distribution(baseline.decision_deltas)
    gates = {
        "schema_v4_rows_present": bool(rows)
        and scan.batch_schema_versions
        == Counter(
            {
                AUXILIARY_VM_BATCH_EVENT_TRACE_SCHEMA_VERSION: len(rows),
            }
        ),
        "transport_success_and_coherent": bool(rows)
        and scan.batch_statuses == Counter({"success": len(rows)})
        and not scan.validation_errors,
        "exact_runtime_version_on_every_batch": bool(rows),
        "replay_state_present": replayable_record_count > 0,
        "independent_oracle_parity": request_count > 0
        and lowerable_count == request_count
        and complete_count == request_count
        and unknown_count == 0,
        "contracted_targets_only": bool(targets)
        and set(targets).issubset({69, 72, 73}),
        "event_status_success": event_statuses
        == Counter({"success": len(rows)}),
        "no_added_process_reads_in_event_layer": bool(rows)
        and not scan.validation_errors,
        "event_derive_timing": within(
            event_distribution,
            EVENT_DERIVE_LIMIT_MS,
        ),
        "replay_compact_timing": within(
            compact_distribution,
            REPLAY_COMPACT_LIMIT_MS,
        ),
        "trace_emit_timing": within(
            emit_distribution,
            TRACE_EMIT_LIMIT_MS,
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
    report: dict[str, object] = {
        "schema": REPORT_SCHEMA,
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
        "session": session,
        "transport": {
            "batch_count": scan.batch_count,
            "schema_versions": {
                str(key): value
                for key, value in sorted(
                    scan.batch_schema_versions.items()
                )
            },
            "statuses": dict(sorted(scan.batch_statuses.items())),
            "validation_errors": scan.validation_errors,
            "process_read_count": distribution(scan.process_reads),
        },
        "replay": {
            "event_statuses": dict(sorted(event_statuses.items())),
            "request_count": request_count,
            "lowerable_count": lowerable_count,
            "complete_count": complete_count,
            "unknown_count": unknown_count,
            "replayable_record_count": replayable_record_count,
            "target_subroutines": {
                str(key): value for key, value in sorted(targets.items())
            },
            "physical_timing": "unavailable_timer_domain_only",
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
            "event_derive_p95_p99_max": list(EVENT_DERIVE_LIMIT_MS),
            "replay_compact_p95_p99_max": list(
                REPLAY_COMPACT_LIMIT_MS
            ),
            "trace_emit_p95_p99_max": list(TRACE_EMIT_LIMIT_MS),
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
    report["report_digest"] = digest(report)
    return report


def write_report(report: dict[str, object], path: Path) -> None:
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
    "EVENT_DERIVE_LIMIT_MS",
    "REPORT_AUTHORITY",
    "REPORT_SCHEMA",
    "REPLAY_COMPACT_LIMIT_MS",
    "TRACE_EMIT_LIMIT_MS",
    "TRANSACTION_TOTAL_LIMIT_MS",
    "build_physical_report",
    "write_report",
]
