"""Strict physical report for schema-v8 columnar event delivery."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from analysis.th08_runtime_ecl_identity_audit import STAGE5_STATIC_SHA256
from th08_live.auxiliary_vm.trace_service import (
    AUXILIARY_VM_BATCH_EVENT_V5_TRACE_SCHEMA_VERSION,
)

from .physical_report_v2 import (
    AuxiliaryEclEventPhysicalAuditError,
    build_delivery_physical_report,
)
from .physical_replay_v5 import (
    RECORD_COLUMNS,
    RECORD_PROJECTION_SCHEMA_V2,
    REQUEST_COLUMNS,
    REQUEST_PROJECTION_SCHEMA,
    audit_event_batch_v5,
)
from .replay_evidence import mapping


REPORT_SCHEMA = "th08-g5-auxiliary-ecl-event-physical-gate-v5"
PREPARATION_SCHEMA = "th08-auxiliary-ecl-event-preparation-v2"
PREPARATION_MAXIMUM_MS = 1.0
SURVIVAL_HIT_MAXIMUM = 10
PROJECTED_BATCH_LINE_MAXIMUM = 24576


def _empty_row_valid_v5(row: dict[str, Any]) -> bool:
    observation = mapping(row.get("observation"), "empty.observation")
    projection = mapping(
        observation.get("record_projection"),
        "empty.record_projection",
    )
    event = mapping(row.get("event_derivation"), "empty.event")
    requests = mapping(
        event.get("request_projection"),
        "empty.request_projection",
    )
    commitment = mapping(
        event.get("lowering_commitment"),
        "empty.lowering_commitment",
    )
    bundle = mapping(
        observation.get("replay_state_bundle"),
        "empty.replay_state_bundle",
    )
    return bool(
        "records" not in observation
        and observation.get("record_count") == 0
        and observation.get("non_null_context_count") == 0
        and observation.get("usable_context_count") == 0
        and observation.get("state_payload_bytes") == 0
        and projection
        == {
            "schema": RECORD_PROJECTION_SCHEMA_V2,
            "record_status_bits": {},
            "columns": RECORD_COLUMNS,
            "rows": [],
        }
        and bundle.get("blob_count") == 0
        and bundle.get("uncompressed_bytes") == 0
        and event.get("status") == "empty_complete"
        and event.get("request_count") == 0
        and event.get("complete_count") == 0
        and event.get("unknown_count") == 0
        and requests
        == {
            "schema": REQUEST_PROJECTION_SCHEMA,
            "columns": REQUEST_COLUMNS,
            "rows": [],
        }
        and commitment
        == {
            "schema": (
                "th08-auxiliary-literal-fire-result-commitment-v1"
            ),
            "request_count": 0,
            "unique_result_count": 0,
            "result_indices": [],
            "unique_result_sha256": [],
        }
    )


def build_physical_report_v5(
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
        report_schema=REPORT_SCHEMA,
        batch_schema_version=(
            AUXILIARY_VM_BATCH_EVENT_V5_TRACE_SCHEMA_VERSION
        ),
        preparation_schema=PREPARATION_SCHEMA,
        preparation_maximum_ms=PREPARATION_MAXIMUM_MS,
        require_same_gameplay_epoch=False,
        audit_batch=audit_event_batch_v5,
        survival_hit_maximum=SURVIVAL_HIT_MAXIMUM,
        empty_row_valid=_empty_row_valid_v5,
        batch_line_maximum=PROJECTED_BATCH_LINE_MAXIMUM,
    )


def write_report_v5(report: dict[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


__all__ = [
    "AuxiliaryEclEventPhysicalAuditError",
    "PREPARATION_MAXIMUM_MS",
    "PREPARATION_SCHEMA",
    "PROJECTED_BATCH_LINE_MAXIMUM",
    "REPORT_SCHEMA",
    "SURVIVAL_HIT_MAXIMUM",
    "build_physical_report_v5",
    "write_report_v5",
]
