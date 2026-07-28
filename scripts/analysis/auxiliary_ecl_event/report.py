"""Deterministic report composition for the first auxiliary event gate."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .static_program import summarize_observed_target_programs
from .trace_inventory import scan_compact_auxiliary_trace


REPORT_SCHEMA = "th08-g5-auxiliary-ecl-event-inventory-v1"
REPORT_AUTHORITY = "offline_trace_inventory_no_action_authority"


def _digest(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_auxiliary_ecl_event_inventory_report(
    trace_path: Path,
    ecl_path: Path,
    *,
    expected_ecl_sha256: str,
) -> dict[str, object]:
    inventory = scan_compact_auxiliary_trace(trace_path)
    targets = tuple(target for target, _count in inventory.target_subroutines)
    static = summarize_observed_target_programs(
        ecl_path,
        targets,
        expected_sha256=expected_ecl_sha256,
    )
    report: dict[str, object] = {
        "schema": REPORT_SCHEMA,
        "authority": REPORT_AUTHORITY,
        "trace": inventory.record(),
        "static_ecl": static,
        "conclusion": {
            "selected_event_class": "auxiliary_literal_fire_cycle_intent",
            "event_replay_status": inventory.event_replay_status,
            "hash_is_reversible_state": False,
            "timer_or_geometry_authority": False,
            "physical_action_authority": "none",
        },
    }
    report["report_digest"] = _digest(report)
    return report


def write_report(report: dict[str, object], path: Path) -> None:
    path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


__all__ = [
    "REPORT_AUTHORITY",
    "REPORT_SCHEMA",
    "build_auxiliary_ecl_event_inventory_report",
    "write_report",
]
