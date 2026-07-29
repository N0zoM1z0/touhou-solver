"""Strict physical report for coalesced schema-v8 auxiliary evidence."""

from __future__ import annotations

import json
from pathlib import Path

from analysis.th08_runtime_ecl_identity_audit import STAGE5_STATIC_SHA256

from .coalesced_replay_v6 import (
    BASE64_MAXIMUM_BYTES,
    COMPRESSED_MAXIMUM_BYTES,
    UNCOMPRESSED_MAXIMUM_BYTES,
)
from .coalesced_trace_v6 import (
    decision_emit_values,
    load_coalesced_trace,
)
from .physical_gate_support import digest, distribution, within
from .physical_report_v2 import (
    AuxiliaryEclEventPhysicalAuditError,
    build_delivery_physical_report,
)
from .physical_report_v5 import (
    PREPARATION_MAXIMUM_MS,
    PREPARATION_SCHEMA,
    SURVIVAL_HIT_MAXIMUM,
    _empty_row_valid_v5,
)
from .physical_replay_v5 import audit_event_batch_v5


REPORT_SCHEMA = "th08-g5-auxiliary-ecl-event-physical-gate-v6"
PACK_LIMIT_MS = (0.750, 1.250, 3.000)
EVIDENCE_PLUS_PACK_LIMIT_MS = (3.500, 6.000, 18.000)
BEARING_EMIT_P95_REGRESSION_MS = 0.500
BEARING_EMIT_P99_REGRESSION_MS = 1.000
ALL_EMIT_P95_REGRESSION_MS = 0.500


def _distribution_maximum(
    value: dict[str, float | int] | None,
    maximum: float,
) -> bool:
    return bool(value is not None and float(value["max"]) <= maximum)


def build_physical_report_v6(
    trace_path: Path,
    baseline_path: Path,
    session_path: Path,
    ecl_path: Path,
    *,
    expected_ecl_sha256: str = STAGE5_STATIC_SHA256,
) -> dict[str, object]:
    evidence = load_coalesced_trace(trace_path)
    baseline_emit_ms = decision_emit_values(baseline_path)
    report = build_delivery_physical_report(
        trace_path,
        baseline_path,
        session_path,
        ecl_path,
        expected_ecl_sha256=expected_ecl_sha256,
        report_schema=REPORT_SCHEMA,
        batch_schema_version=8,
        preparation_schema=PREPARATION_SCHEMA,
        preparation_maximum_ms=PREPARATION_MAXIMUM_MS,
        require_same_gameplay_epoch=False,
        audit_batch=audit_event_batch_v5,
        survival_hit_maximum=SURVIVAL_HIT_MAXIMUM,
        empty_row_valid=_empty_row_valid_v5,
        batch_line_maximum=UNCOMPRESSED_MAXIMUM_BYTES,
        trace_data=evidence.delivery,
        trace_emit_limits=None,
    )

    pack = distribution(evidence.pack_ms)
    evidence_plus_pack = distribution(evidence.evidence_plus_pack_ms)
    bearing_emit = distribution(evidence.bearing_decision_emit_ms)
    all_emit = distribution(evidence.all_decision_emit_ms)
    baseline_emit = distribution(baseline_emit_ms)
    base64_bytes = distribution(evidence.payload_base64_bytes)
    compressed_bytes = distribution(evidence.compressed_bytes)
    bearing_line_bytes = distribution(
        evidence.bearing_decision_line_bytes
    )

    gates = report["gates"]
    assert isinstance(gates, dict)
    gates["schema_v8_inner_rows_present"] = gates.pop(
        "schema_v8_rows_present"
    )
    gates["canonical_inner_maximum"] = gates.pop(
        "projected_batch_line_maximum"
    )
    gates.update(
        {
            "coalesced_envelopes_present_and_ordered": bool(
                evidence.sequences
                and evidence.sequences
                == list(range(len(evidence.sequences)))
            ),
            "no_standalone_auxiliary_batch_write": (
                evidence.standalone_batch_count == 0
            ),
            "next_decision_publication_timing_complete": bool(
                evidence.bearing_decision_emit_ms
                and len(evidence.bearing_decision_emit_ms)
                == len(evidence.delivery.rows)
            ),
            "coalesced_pack_timing": within(pack, PACK_LIMIT_MS),
            "evidence_plus_pack_timing": within(
                evidence_plus_pack,
                EVIDENCE_PLUS_PACK_LIMIT_MS,
            ),
            "base64_payload_maximum": _distribution_maximum(
                base64_bytes,
                BASE64_MAXIMUM_BYTES,
            ),
            "compressed_payload_maximum": _distribution_maximum(
                compressed_bytes,
                COMPRESSED_MAXIMUM_BYTES,
            ),
            "bearing_decision_emit_regression": bool(
                bearing_emit is not None
                and baseline_emit is not None
                and float(bearing_emit["p95"])
                <= (
                    float(baseline_emit["p95"])
                    + BEARING_EMIT_P95_REGRESSION_MS
                )
                and float(bearing_emit["p99"])
                <= (
                    float(baseline_emit["p99"])
                    + BEARING_EMIT_P99_REGRESSION_MS
                )
            ),
            "all_decision_emit_p95_regression": bool(
                all_emit is not None
                and baseline_emit is not None
                and float(all_emit["p95"])
                <= (
                    float(baseline_emit["p95"])
                    + ALL_EMIT_P95_REGRESSION_MS
                )
            ),
        }
    )

    timing = report["timing_ms"]
    assert isinstance(timing, dict)
    timing.pop("previous_trace_emit")
    timing.update(
        {
            "coalesced_pack": pack,
            "evidence_plus_pack": evidence_plus_pack,
            "bearing_decision_emit": bearing_emit,
            "all_decision_emit": all_emit,
            "baseline_decision_emit": baseline_emit,
        }
    )
    transport = report["transport"]
    assert isinstance(transport, dict)
    canonical_line_bytes = transport.pop("batch_line_bytes")
    transport["coalesced"] = {
        "envelope_count": len(evidence.sequences),
        "sequences": evidence.sequences,
        "standalone_batch_count": evidence.standalone_batch_count,
        "canonical_inner_bytes": canonical_line_bytes,
        "compressed_bytes": compressed_bytes,
        "payload_base64_bytes": base64_bytes,
        "bearing_decision_line_bytes": bearing_line_bytes,
    }
    limits_ms = report["limits_ms"]
    assert isinstance(limits_ms, dict)
    limits_ms.update(
        {
            "coalesced_pack_p95_p99_max": list(PACK_LIMIT_MS),
            "evidence_plus_pack_p95_p99_max": list(
                EVIDENCE_PLUS_PACK_LIMIT_MS
            ),
            "bearing_decision_emit_p95_regression": (
                BEARING_EMIT_P95_REGRESSION_MS
            ),
            "bearing_decision_emit_p99_regression": (
                BEARING_EMIT_P99_REGRESSION_MS
            ),
            "all_decision_emit_p95_regression": (
                ALL_EMIT_P95_REGRESSION_MS
            ),
        }
    )
    report["limits_bytes"] = {
        "canonical_inner_maximum": UNCOMPRESSED_MAXIMUM_BYTES,
        "compressed_payload_maximum": COMPRESSED_MAXIMUM_BYTES,
        "base64_payload_maximum": BASE64_MAXIMUM_BYTES,
    }
    report["passed"] = all(bool(value) for value in gates.values())
    report["report_digest"] = digest(report)
    return report


def write_report_v6(report: dict[str, object], path: Path) -> None:
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
    "ALL_EMIT_P95_REGRESSION_MS",
    "AuxiliaryEclEventPhysicalAuditError",
    "BEARING_EMIT_P95_REGRESSION_MS",
    "BEARING_EMIT_P99_REGRESSION_MS",
    "EVIDENCE_PLUS_PACK_LIMIT_MS",
    "PACK_LIMIT_MS",
    "REPORT_SCHEMA",
    "build_physical_report_v6",
    "write_report_v6",
]
