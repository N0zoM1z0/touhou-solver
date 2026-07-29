#!/usr/bin/env python3
"""Build the strict focused Final-B live scale-delivery physical report."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Iterable

SCRIPT_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from th08_live.scale_schedule_authority import (  # noqa: E402
    FINAL_B_LIVE_SCALE_AUTHORITY_SCHEMA,
)
from th08_live.scale_source_trace import (  # noqa: E402
    FINAL_B_ECL_STATIC_SHA256,
    FINAL_B_QUARTER_SCALE_BITS,
    FINAL_B_SCALE_SOURCE_TRACE_SCHEMA,
)
from th08_runtime.game_state import EXPECTED_EXE_SHA256  # noqa: E402
from th08_time_scale import (  # noqa: E402
    SCALE_COVERAGE_COMPLETE,
    TH08_PLAYER_LASER_SCALE_SEMANTICS_VERSION,
    TH08_UNIT_TIME_SCALE_BITS,
)


REPORT_SCHEMA = "th08-finalb-scale-live-delivery-physical-report-v2"


def _records(path: Path) -> Iterable[dict[str, object]]:
    with path.open("r", encoding="utf-8") as source:
        for line_number, line in enumerate(source, 1):
            if not line.strip():
                continue
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError(
                    f"line {line_number} is not a JSON object"
                )
            yield record


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _integer(record: dict[str, object], field: str) -> int | None:
    value = record.get(field)
    return value if type(value) is int else None


def build_report(path: Path) -> dict[str, object]:
    identity: dict[str, object] | None = None
    configuration: dict[str, object] | None = None
    source_traces: list[dict[str, object]] = []
    authority_rows: list[dict[str, object]] = []
    decisions: list[dict[str, object]] = []
    pretarget_decision_count = 0
    pretarget_transport_labeled = True
    all_decisions_no_bomb = True
    exact_source_seen = False
    unknown_rows: list[dict[str, object]] = []
    runtime_errors: list[dict[str, object]] = []
    summaries: list[dict[str, object]] = []
    record_count = 0

    for record in _records(path):
        record_count += 1
        kind = record.get("kind")
        if kind == "identity" and identity is None:
            identity = record
        elif kind == "controller_config" and configuration is None:
            configuration = record
        elif kind == "finalb_scale_source_trace":
            source_traces.append(record)
            if record.get("status") == "accepted_complete_source_trace":
                exact_source_seen = True
        elif kind == "finalb_live_scale_schedule_authority":
            if (
                exact_source_seen
                or record.get("status")
                == "complete_exact_source_schedule"
            ):
                authority_rows.append(record)
        elif kind == "decision":
            all_decisions_no_bomb = (
                all_decisions_no_bomb
                and record.get("bomb") is False
                and not int(record.get("mask", 0)) & 0x02
            )
            if exact_source_seen:
                decisions.append(record)
            else:
                pretarget_decision_count += 1
                scale = record.get("time_scale")
                pretarget_transport_labeled = (
                    pretarget_transport_labeled
                    and isinstance(scale, dict)
                    and scale.get("hard_authority") is False
                    and scale.get("phase_schedule_omitted") is True
                    and str(scale.get("provenance", "")).startswith(
                        "experimental_pretarget_unit_transport"
                    )
                )
        elif kind == "time_scale_authority_unknown":
            unknown_rows.append(record)
        elif kind == "runtime_error":
            runtime_errors.append(record)
        elif kind == "run_summary":
            summaries.append(record)

    accepted_sources = [
        record
        for record in source_traces
        if record.get("status") == "accepted_complete_source_trace"
    ]
    source_trace = accepted_sources[0] if len(accepted_sources) == 1 else None
    accepted_authority = [
        record
        for record in authority_rows
        if (
            record.get("status") == "complete_exact_source_schedule"
            and record.get("planner_scale_schedule_authority") is True
        )
    ]
    origin_rows = [
        record
        for record in accepted_authority
        if _integer(record, "frame_offset") == 0
    ]
    origin_row = origin_rows[0] if len(origin_rows) == 1 else None
    origin_frame = (
        _integer(origin_row, "origin_source_frame")
        if origin_row is not None
        else None
    )
    scoped_authority = [
        record
        for record in accepted_authority
        if (
            origin_frame is not None
            and _integer(record, "origin_source_frame") == origin_frame
        )
    ]
    authority_by_frame = {
        _integer(record, "current_source_frame"): record
        for record in scoped_authority
        if _integer(record, "current_source_frame") is not None
    }
    quarter_offsets = [
        offset
        for record in scoped_authority
        if (
            (offset := _integer(record, "frame_offset")) is not None
            and record.get("root_scale_bits") == FINAL_B_QUARTER_SCALE_BITS
        )
    ]
    unit_offsets = [
        offset
        for record in scoped_authority
        if (
            (offset := _integer(record, "frame_offset")) is not None
            and record.get("root_scale_bits") == TH08_UNIT_TIME_SCALE_BITS
        )
    ]
    restore_row = (
        min(
            (
                record
                for record in scoped_authority
                if (
                    (_integer(record, "frame_offset") or -1) >= 240
                    and record.get("root_scale_bits")
                    == TH08_UNIT_TIME_SCALE_BITS
                )
            ),
            key=lambda record: _integer(record, "frame_offset") or 0,
            default=None,
        )
        if origin_frame is not None
        else None
    )
    restore_offset = (
        _integer(restore_row, "frame_offset")
        if restore_row is not None
        else None
    )
    scoped_decisions = [
        record
        for record in decisions
        if (
            origin_frame is not None
            and restore_offset is not None
            and isinstance(record.get("time_scale"), dict)
            and origin_frame
            <= int(record["time_scale"].get("source_frame", -1))
            <= origin_frame + restore_offset
        )
    ]
    source_schedule = (
        source_trace.get("schedule")
        if source_trace is not None
        and isinstance(source_trace.get("schedule"), dict)
        else None
    )
    source_capture = (
        source_trace.get("source_capture")
        if source_trace is not None
        and isinstance(source_trace.get("source_capture"), dict)
        else None
    )
    runtime_identity = (
        source_trace.get("runtime_ecl_identity")
        if source_trace is not None
        and isinstance(source_trace.get("runtime_ecl_identity"), dict)
        else None
    )
    writes = (
        source_schedule.get("writes", [])
        if source_schedule is not None
        else []
    )
    supported_restore = any(
        isinstance(write, dict)
        and write.get("frame") == 240
        and write.get("callback_index") == 18
        and write.get("scale_bits_before") == FINAL_B_QUARTER_SCALE_BITS
        and write.get("scale_bits_after") == TH08_UNIT_TIME_SCALE_BITS
        and write.get("scales_active_bullet_velocity") is False
        for write in writes
    )

    decisions_clean = bool(scoped_decisions) and all(
        record.get("hit_started") is False
        and record.get("bomb") is False
        and not int(record.get("mask", 0)) & 0x02
        for record in scoped_decisions
    )
    decision_scale_complete = bool(scoped_decisions) and all(
        isinstance((scale := record.get("time_scale")), dict)
        and scale.get("semantics_version")
        == TH08_PLAYER_LASER_SCALE_SEMANTICS_VERSION
        and scale.get("coverage") == SCALE_COVERAGE_COMPLETE
        and scale.get("hard_authority") is True
        and "live_exact_rebase" in str(scale.get("provenance", ""))
        and (
            (source_frame := _integer(scale, "source_frame"))
            in authority_by_frame
        )
        and (
            authority_by_frame[source_frame].get("root_scale_bits")
            == scale.get("root_scale_bits")
        )
        and (
            authority_by_frame[source_frame].get("complete_horizon")
            == scale.get("complete_horizon")
        )
        and (
            authority_by_frame[source_frame].get("provenance")
            == scale.get("provenance")
        )
        for record in scoped_decisions
    )
    authority_rows_exact = bool(scoped_authority) and all(
        record.get("schema") == FINAL_B_LIVE_SCALE_AUTHORITY_SCHEMA
        and record.get("semantics_version")
        == TH08_PLAYER_LASER_SCALE_SEMANTICS_VERSION
        and record.get("hard_action_authority") is False
        and record.get("experimental_pretarget_transport") is False
        and record.get("coverage") == SCALE_COVERAGE_COMPLETE
        and (
            _integer(record, "current_source_frame")
            == origin_frame + int(record.get("frame_offset", -1))
        )
        and (
            _integer(record, "complete_horizon")
            == 300 - int(record.get("frame_offset", -1))
        )
        for record in scoped_authority
    )
    source_phase = (
        source_capture.get("phase_before")
        if source_capture is not None
        and isinstance(source_capture.get("phase_before"), dict)
        else None
    )
    baseline_predeath_counter = (
        _integer(source_phase, "player_predeath_counter")
        if source_phase is not None
        else None
    )
    stable_player_root = (
        baseline_predeath_counter is not None
        and source_phase is not None
        and source_phase.get("player_bomb_active") == 0
        and bool(scoped_authority)
        and all(
            _integer(record, "baseline_predeath_counter")
            == baseline_predeath_counter
            for record in scoped_authority
        )
    )
    source_scope_exact = (
        source_trace is not None
        and source_trace.get("route_id") == 2
        and source_trace.get("difficulty_index") == 3
        and source_trace.get("stage_route_index") == 7
        and source_trace.get("spell_id") == 190
        and source_phase is not None
        and source_phase.get("route_id") == 2
        and source_phase.get("difficulty_index") == 3
        and source_phase.get("stage_route_index") == 7
        and source_phase.get("spell_id") == 190
        and source_phase.get("scale_bits") == FINAL_B_QUARTER_SCALE_BITS
    )
    source_schedule_exact = (
        source_schedule is not None
        and source_schedule.get("semantics_version")
        == TH08_PLAYER_LASER_SCALE_SEMANTICS_VERSION
        and source_schedule.get("coverage") == SCALE_COVERAGE_COMPLETE
        and source_schedule.get("root_scale_bits")
        == FINAL_B_QUARTER_SCALE_BITS
        and source_schedule.get("source_frame") == origin_frame
        and source_schedule.get("complete_horizon") == 300
        and isinstance(source_schedule.get("player_scale_bits"), list)
        and len(source_schedule["player_scale_bits"]) == 300
        and isinstance(source_schedule.get("laser_scale_bits"), list)
        and len(source_schedule["laser_scale_bits"]) == 300
    )
    summary = summaries[-1] if len(summaries) == 1 else None
    checks = {
        "executable_identity": (
            identity is not None
            and identity.get("sha256") == EXPECTED_EXE_SHA256
        ),
        "controller_contract": (
            configuration is not None
            and configuration.get("bomb_policy") == "disabled"
            and configuration.get("finalb_scale_source_authority") is True
            and configuration.get("finalb_scale_pretarget_transport")
            == "experimental_unit_unknown_direction"
            and configuration.get("runtime_ecl_static_sha256")
            == FINAL_B_ECL_STATIC_SHA256
        ),
        "single_accepted_complete_source": source_trace is not None,
        "complete_source_schema": (
            source_trace is not None
            and source_trace.get("schema")
            == FINAL_B_SCALE_SOURCE_TRACE_SCHEMA
        ),
        "runtime_ecl_identity": (
            runtime_identity is not None
            and runtime_identity.get("exact_match") is True
            and runtime_identity.get("static_sha256")
            == FINAL_B_ECL_STATIC_SHA256
        ),
        "source_frame_coherence": (
            source_trace is not None
            and source_trace.get("decision_frame")
            == source_trace.get("expected_manager_frame")
            and source_trace.get("capture_manager_frame")
            == source_trace.get("expected_manager_frame")
            and source_capture is not None
            and source_capture.get("coherent") is True
        ),
        "exact_finalb_scope": source_scope_exact,
        "stable_predeath_baseline": stable_player_root,
        "supported_restore_schedule": (
            source_schedule_exact
            and supported_restore
        ),
        "single_live_origin": (
            origin_row is not None
            and len(scoped_authority) == len(accepted_authority)
        ),
        "exact_authority_rebase": authority_rows_exact,
        "physical_restore_bracket": (
            bool(quarter_offsets)
            and max(quarter_offsets) < 240
            and bool(unit_offsets)
            and min(unit_offsets) >= 240
            and restore_row is not None
        ),
        "decision_scale_delivery": decision_scale_complete,
        "experimental_pretarget_transport_labeled": (
            pretarget_decision_count > 0
            and pretarget_transport_labeled
        ),
        "hard_no_bomb_entire_trial": all_decisions_no_bomb,
        "no_fresh_hit_in_exact_scope": decisions_clean,
        "no_scale_authority_fallback": not unknown_rows,
        "clean_supervised_termination": (
            summary is not None
            and summary.get("termination_reason")
            == "finalb_scale_delivery_complete"
            and not runtime_errors
        ),
    }
    passed = all(checks.values())
    return {
        "schema": REPORT_SCHEMA,
        "source": {
            "path": path.as_posix(),
            "sha256": _sha256(path),
            "record_count": record_count,
        },
        "gate": {
            "name": "SEM-SCALE-C5 focused Final-B live delivery",
            "passed": passed,
            "checks": checks,
        },
        "observed": {
            "origin_source_frame": origin_frame,
            "baseline_predeath_counter": baseline_predeath_counter,
            "pretarget_decision_count": pretarget_decision_count,
            "authority_row_count": len(scoped_authority),
            "decision_count": len(scoped_decisions),
            "last_quarter_offset": (
                max(quarter_offsets) if quarter_offsets else None
            ),
            "first_unit_offset": (
                min(unit_offsets) if unit_offsets else None
            ),
            "restore_observation_offset": restore_offset,
            "hit_count": sum(
                record.get("hit_started") is True
                for record in scoped_decisions
            ),
            "bomb_decision_count": sum(
                record.get("bomb") is True
                or bool(int(record.get("mask", 0)) & 0x02)
                for record in scoped_decisions
            ),
            "termination_reason": (
                summary.get("termination_reason")
                if summary is not None
                else None
            ),
            "entire_trial_hit_count": (
                summary.get("hit_count")
                if summary is not None
                else None
            ),
        },
        "authority": {
            "observed": (
                "Exact native source capture, live root observations, "
                "delivered schedule identities, issued masks, hit edges, "
                "and Bomb fields inside the focused scope."
            ),
            "inferred": (
                "Causal source-schedule rebase between sampled native roots "
                "under the retained no-hit/no-Bomb continuation."
            ),
            "not_proved": (
                "Clean Final-B practice survival, pre-target time-scale "
                "authority, another RNG/resource history, full-route "
                "Lunatic NMNB, or Extra."
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
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["gate"]["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
