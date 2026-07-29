"""Strict physical report for epoch-safe schema-v6 event delivery."""

from __future__ import annotations

import json
from pathlib import Path

from analysis.th08_runtime_ecl_identity_audit import STAGE5_STATIC_SHA256
from th08_live.auxiliary_vm.trace_service import (
    AUXILIARY_VM_BATCH_EVENT_V3_TRACE_SCHEMA_VERSION,
)

from .physical_report_v2 import (
    AuxiliaryEclEventPhysicalAuditError,
    build_delivery_physical_report,
)
from .physical_replay import audit_event_batch_v3


REPORT_SCHEMA = "th08-g5-auxiliary-ecl-event-physical-gate-v3"
PREPARATION_SCHEMA = "th08-auxiliary-ecl-event-preparation-v2"
PREPARATION_MAXIMUM_MS = 1.0
SURVIVAL_HIT_MAXIMUM = 10


def build_physical_report_v3(
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
            AUXILIARY_VM_BATCH_EVENT_V3_TRACE_SCHEMA_VERSION
        ),
        preparation_schema=PREPARATION_SCHEMA,
        preparation_maximum_ms=PREPARATION_MAXIMUM_MS,
        require_same_gameplay_epoch=False,
        audit_batch=audit_event_batch_v3,
        survival_hit_maximum=SURVIVAL_HIT_MAXIMUM,
    )


def write_report_v3(report: dict[str, object], path: Path) -> None:
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
    "PREPARATION_MAXIMUM_MS",
    "PREPARATION_SCHEMA",
    "REPORT_SCHEMA",
    "SURVIVAL_HIT_MAXIMUM",
    "build_physical_report_v3",
    "write_report_v3",
]
