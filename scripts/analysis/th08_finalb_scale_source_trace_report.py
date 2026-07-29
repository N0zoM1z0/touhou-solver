#!/usr/bin/env python3
"""Audit one physical Final-B complete scale-source observer result."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from th08_live.scale_source_trace import (  # noqa: E402
    FINAL_B_ECL_STATIC_SHA256,
    FINAL_B_QUARTER_SCALE_BITS,
    FINAL_B_SCALE_HORIZON_FRAMES,
    FINAL_B_SCALE_SOURCE_TRACE_SCHEMA,
    FINAL_B_SCALE_SPELL_ID,
    FINAL_B_SCALE_SUBROUTINE,
    FINAL_B_STAGE_ROUTE_INDEX,
)
from th08_runtime.game_state import EXPECTED_EXE_SHA256  # noqa: E402


REPORT_SCHEMA = "th08-finalb-scale-source-physical-report-v1"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_report(path: Path) -> dict[str, object]:
    envelope = json.loads(path.read_text(encoding="utf-8"))
    record = envelope.get("record")
    identity = envelope.get("executable_identity")
    checks: dict[str, bool] = {}
    checks["executable_identity"] = bool(
        isinstance(identity, dict)
        and str(identity.get("sha256", "")).lower()
        == EXPECTED_EXE_SHA256
    )
    checks["accepted_status"] = bool(
        isinstance(record, dict)
        and record.get("status") == "accepted_complete_source_trace"
    )
    if not isinstance(record, dict):
        record = {}
    checks["trace_only"] = (
        record.get("authority") == "trace_only_no_action_authority"
        and record.get("hard_action_authority") is False
        and record.get("changes_input") is False
    )
    checks["scope_identity"] = (
        record.get("schema") == FINAL_B_SCALE_SOURCE_TRACE_SCHEMA
        and record.get("route_id") == 2
        and record.get("difficulty_index") == 3
        and record.get("stage_route_index") == FINAL_B_STAGE_ROUTE_INDEX
        and record.get("spell_id") == FINAL_B_SCALE_SPELL_ID
    )
    configuration = record.get("configuration")
    checks["configuration_identity"] = bool(
        isinstance(configuration, dict)
        and configuration.get("static_sha256")
        == FINAL_B_ECL_STATIC_SHA256
        and configuration.get("target_subroutine")
        == FINAL_B_SCALE_SUBROUTINE
        and configuration.get("horizon_frames")
        == FINAL_B_SCALE_HORIZON_FRAMES
    )
    runtime_identity = record.get("runtime_ecl_identity")
    checks["runtime_ecl_identity"] = bool(
        isinstance(runtime_identity, dict)
        and runtime_identity.get("exact_match") is True
        and runtime_identity.get("static_sha256")
        == FINAL_B_ECL_STATIC_SHA256
        and runtime_identity.get("normalized_runtime_sha256")
        == FINAL_B_ECL_STATIC_SHA256
    )
    source_capture = record.get("source_capture")
    sources = (
        source_capture.get("sources")
        if isinstance(source_capture, dict)
        else None
    )
    checks["complete_source_capture"] = bool(
        isinstance(source_capture, dict)
        and source_capture.get("coherent") is True
        and source_capture.get("ordinary_pool_complete") is True
        and source_capture.get("ordinary_pool_slots_scanned") == 480
        and source_capture.get("source_count") == 1
        and isinstance(sources, list)
        and len(sources) == 1
    )
    source = sources[0] if isinstance(sources, list) and sources else {}
    installed_callback = (
        source.get("installed_callback")
        if isinstance(source, dict)
        else None
    )
    installed_callback_index = (
        source.get("installed_callback_index")
        if isinstance(source, dict)
        else None
    )
    installed_callback_safe = (
        installed_callback == 0
        or (
            isinstance(installed_callback, int)
            and installed_callback != 0
            and isinstance(installed_callback_index, int)
            and installed_callback_index not in {18, 28, 29}
        )
    )
    checks["source_callback_auxiliary_absence"] = bool(
        isinstance(source, dict)
        and installed_callback_safe
        and source.get("invalid_reason") is None
        and source.get("auxiliary_context_pointers") == [0, 0, 0, 0]
    )
    phase = (
        source_capture.get("phase_before")
        if isinstance(source_capture, dict)
        else None
    )
    checks["stable_quarter_no_bomb_root"] = bool(
        isinstance(phase, dict)
        and phase.get("scale_bits") == FINAL_B_QUARTER_SCALE_BITS
        and phase.get("player_bomb_active") == 0
        and isinstance(phase.get("player_predeath_counter"), int)
        and phase.get("player_predeath_counter") >= 0
    )
    schedule = record.get("schedule")
    writes = schedule.get("writes") if isinstance(schedule, dict) else None
    checks["complete_schedule"] = bool(
        isinstance(schedule, dict)
        and schedule.get("coverage") == "complete"
        and schedule.get("complete_horizon")
        == FINAL_B_SCALE_HORIZON_FRAMES
        and schedule.get("stop_reason") == "horizon"
        and schedule.get("root_scale_bits") == FINAL_B_QUARTER_SCALE_BITS
        and len(schedule.get("player_scale_bits", []))
        == FINAL_B_SCALE_HORIZON_FRAMES
        and len(schedule.get("laser_scale_bits", []))
        == FINAL_B_SCALE_HORIZON_FRAMES
        and schedule.get("bullet_velocity_rescale_frames") == []
    )
    checks["supported_restore_write"] = bool(
        isinstance(writes, list)
        and writes
        and all(
            isinstance(write, dict)
            and write.get("callback_index") == 18
            and write.get("scales_active_bullet_velocity") is False
            for write in writes
        )
        and writes[-1].get("scale_bits_after") == 0x3F800000
    )
    checks["no_internal_incomplete_reason"] = (
        record.get("incomplete_reasons") == []
        and record.get("error") is None
    )
    passed = all(checks.values())
    return {
        "schema": REPORT_SCHEMA,
        "source": {
            "path": path.as_posix(),
            "sha256": _sha256(path),
        },
        "gate": {
            "name": "SEM-SCALE-C4 default-off physical complete-source trace",
            "passed": passed,
            "checks": checks,
        },
        "observed": {
            "manager_frame": record.get("capture_manager_frame"),
            "trigger_manager_frame": record.get("expected_manager_frame"),
            "gameplay_epoch": record.get("gameplay_epoch"),
            "runtime_ecl_capture": record.get("runtime_ecl_capture"),
            "source_count": (
                source_capture.get("source_count")
                if isinstance(source_capture, dict)
                else None
            ),
            "process_read_count": (
                source_capture.get("process_read_count")
                if isinstance(source_capture, dict)
                else None
            ),
            "process_read_bytes": (
                source_capture.get("process_read_bytes")
                if isinstance(source_capture, dict)
                else None
            ),
            "capture_ms": (
                source_capture.get("capture_ms")
                if isinstance(source_capture, dict)
                else None
            ),
            "schedule_stop_frame": (
                schedule.get("stop_frame")
                if isinstance(schedule, dict)
                else None
            ),
            "writes": writes,
            "player_predeath_counter": (
                phase.get("player_predeath_counter")
                if isinstance(phase, dict)
                else None
            ),
        },
        "authority": {
            "observed": (
                "Exact executable/runtime-ECL identity and one coherent "
                "physical complete-source transaction, when every check "
                "passes."
            ),
            "inferred": (
                "The causal schedule is the supported no-hit/no-Bomb target "
                "continuation from the captured native VM state."
            ),
            "not_proved": (
                "This trace changes no input and proves neither action "
                "authority, a clean zero-predeath player root, clean "
                "survival, callback-28 hazard consumption, nor NMNB."
            ),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args(argv)
    report = build_report(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, sort_keys=True))
    return 0 if report["gate"]["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
