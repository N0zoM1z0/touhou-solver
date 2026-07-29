#!/usr/bin/env python3
"""Build an offline stitched run dossier from live-agent traces."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from th08_ecl import parse_ecl
from analysis.dossier import attribution as _attribution
from analysis.dossier import full_run_render as _render
from analysis.dossier import planner_consistency as _planner_summary
from analysis.dossier.schema import compact_decision
from analysis.dossier.statistics import (
    percentiles as _percentiles,
    resource_range as _resource_range,
)
from analysis.dossier.trace_reader import TraceProvenance, read_trace
from analysis.th08_trial_report import STAGE_ROUTE_LABELS


ROOT = Path(__file__).resolve().parents[2]
_compact_decision = compact_decision
_action_lag_over_model = _attribution.action_lag_over_model
_case_prefix_for_difficulty = _attribution.case_prefix_for_difficulty
_classify_death = _attribution.classify_death
_death_clusters = _attribution.cluster_deaths
_death_ledger = _attribution.build_death_ledger
_input_mask_action = _attribution.input_mask_action
_nearest_bullet = _attribution.nearest_bullet
_nearest_enemy_body = _attribution.nearest_enemy_body
_nearest_laser = _attribution.nearest_laser
_planner_consistency_summary = (
    _planner_summary.planner_consistency_summary
)
_robust_control_unsafe = _attribution.robust_control_unsafe
_spell_attribution = _attribution.spell_attribution
_viability_action_set_empty = _attribution.viability_action_set_empty
_format_number = _render._format_number
render_markdown = _render.render_markdown
write_death_csv = _render.write_death_csv
PHASE_COUNTER_JUMP_MIN = 1750
PHASE_COUNTER_JUMP_MAX = 1850
BOMB_INPUT_BIT = 0x02


def _no_bomb_verification(
    decisions: list[dict[str, object]],
    provenance: list[TraceProvenance],
) -> dict[str, object]:
    mask_violations = [
        int(row["frame"])
        for row in decisions
        if int(row["mask"]) & BOMB_INPUT_BIT
    ]
    flag_violations = [
        int(row["frame"]) for row in decisions if bool(row["bomb"])
    ]
    action_violations = [
        int(row["frame"])
        for row in decisions
        if "bomb" in str(row["action"]).lower()
    ]
    controller_configs = [
        config
        for trace in provenance
        for config in trace.controller_configs
    ]
    configured_disabled = bool(controller_configs) and all(
        config.get("bomb_policy") == "disabled"
        for config in controller_configs
    )
    return {
        "passed": (
            configured_disabled
            and not mask_violations
            and not flag_violations
            and not action_violations
        ),
        "bomb_input_bit": BOMB_INPUT_BIT,
        "controller_policy_disabled": configured_disabled,
        "decision_count_checked": len(decisions),
        "mask_violation_frames": mask_violations,
        "bomb_flag_violation_frames": flag_violations,
        "bomb_action_violation_frames": action_violations,
        "resource_note": (
            "Bomb stock can decrease after a native hit because TH08 resets "
            "the respawn stock. Only input mask, decision flag, action, and "
            "controller configuration prove Bomb use."
        ),
    }


def _robust_viability_summary(
    decisions: list[dict[str, object]],
) -> dict[str, object]:
    unique_solutions: dict[int, dict[str, object]] = {}
    policy_rows = []
    queries = []
    for row in decisions:
        if row.get("corridor_planning_mode") == "robust_viability":
            policy_rows.append(row)
        source = row.get("corridor_source_frame")
        if source is not None:
            unique_solutions.setdefault(int(source), row)
        viability = row.get("viability")
        if isinstance(viability, dict) and viability:
            queries.append(viability)

    unique_rows = list(unique_solutions.values())
    timing_keys = sorted(
        {
            str(key)
            for row in unique_rows
            for key in row.get("corridor_solver_timing_ms", {})
        }
    )
    available = [
        query for query in queries if bool(query.get("available"))
    ]
    constrained = [
        row
        for row in decisions
        if isinstance(row.get("robust_control"), dict)
        and bool(row["robust_control"].get("viability_constrained"))
    ]
    return {
        "policy_decision_count": len(policy_rows),
        "decision_without_query_count": len(policy_rows) - len(queries),
        "unique_solution_count": len(unique_rows),
        "solve_ms": _percentiles(
            float(row["corridor_solve_ms"])
            for row in unique_rows
            if row.get("corridor_solve_ms") is not None
        ),
        "first_observed_age_frames": _percentiles(
            float(row["corridor_age"])
            for row in unique_rows
            if row.get("corridor_age") is not None
        ),
        "forecast_lead_frames": _percentiles(
            float(row["corridor_forecast_lead_frames"])
            for row in unique_rows
            if row.get("corridor_forecast_lead_frames") is not None
        ),
        "backend_counts": dict(
            Counter(
                str(row["corridor_viability_backend"])
                for row in unique_rows
                if row.get("corridor_viability_backend") is not None
            )
        ),
        "solver_phase_ms": {
            key: _percentiles(
                float(row["corridor_solver_timing_ms"][key])
                for row in unique_rows
                if key in row.get("corridor_solver_timing_ms", {})
            )
            for key in timing_keys
        },
        "serial_coverage_margin_frames": _percentiles(
            float(row["corridor_serial_coverage_margin_frames"])
            for row in policy_rows
            if row.get("corridor_serial_coverage_margin_frames") is not None
        ),
        "serial_worker_serviceable_count": sum(
            bool(row.get("corridor_serial_worker_serviceable"))
            for row in policy_rows
        ),
        "policy_status_counts": dict(
            Counter(
                str(row["corridor_policy_status"])
                for row in policy_rows
                if row.get("corridor_policy_status") is not None
            )
        ),
        "reported_stale_solution_count": sum(
            bool(row.get("corridor_stale")) for row in unique_rows
        ),
        "query_count": len(queries),
        "available_query_count": len(available),
        "unavailable_reason_counts": dict(
            Counter(
                str(query.get("reason", "unspecified"))
                for query in queries
                if not bool(query.get("available"))
            )
        ),
        "support_covered_query_count": sum(
            bool(query.get("support_covers_current", True))
            for query in available
        ),
        "support_uncovered_query_count": sum(
            not bool(query.get("support_covers_current", True))
            for query in available
        ),
        "viable_query_count": sum(
            bool(query.get("state_viable")) for query in available
        ),
        "empty_action_set_count": sum(
            not bool(query.get("state_viable"))
            or int(query.get("safe_action_count", 0)) == 0
            for query in available
        ),
        "constrained_decision_count": len(constrained),
        "constrained_decision_fraction": (
            len(constrained) / len(decisions) if decisions else None
        ),
        "safe_action_count": _percentiles(
            int(query.get("safe_action_count", 0))
            for query in available
        ),
        "selected_repair_volume": _percentiles(
            int(query.get("selected_repair_volume", 0))
            for query in available
        ),
        "policy_age_frames": _percentiles(
            int(query.get("age", 0)) for query in queries
        ),
    }


def _phase_markers(
    decisions: list[dict[str, object]],
) -> dict[int, list[dict[str, int]]]:
    markers: dict[int, list[dict[str, int]]] = defaultdict(list)
    for previous, current in zip(decisions, decisions[1:]):
        if (
            previous["trace_index"] != current["trace_index"]
            or previous["stage_route_index"]
            != current["stage_route_index"]
        ):
            continue
        delta = int(current["frame"]) - int(previous["frame"])
        if PHASE_COUNTER_JUMP_MIN <= delta <= PHASE_COUNTER_JUMP_MAX:
            stage = int(current["stage_route_index"])
            markers[stage].append(
                {
                    "before_frame": int(previous["frame"]),
                    "after_frame": int(current["frame"]),
                    "delta": delta,
                }
            )
    return markers


def _spell_inventory(
    manifest: dict[str, object],
    phase_markers: dict[int, list[dict[str, int]]],
    deaths: list[dict[str, object]],
    decisions: list[dict[str, object]],
    *,
    spell_schema_complete: bool,
) -> dict[int, dict[str, object]]:
    active_difficulty_mask = int(manifest["active_difficulty_mask"])
    attributed_hits = Counter(
        (
            int(death["stage_route_index"]),
            int(death["spell_attribution"]["spell_id"]),
        )
        for death in deaths
        if death["spell_attribution"]["status"]
        == "resolved_live_spell_state"
    )
    observed_decisions: Counter[tuple[int, int]] = Counter()
    first_observed_frame: dict[tuple[int, int], int] = {}
    last_observed_frame: dict[tuple[int, int], int] = {}
    if spell_schema_complete:
        for decision in decisions:
            spell = decision["spell"]
            if not bool(spell.get("active")):
                continue
            spell_id = int(spell.get("spell_id", 0))
            if spell_id <= 0:
                continue
            key = (int(decision["stage_route_index"]), spell_id)
            frame = int(decision["frame"])
            observed_decisions[key] += 1
            first_observed_frame.setdefault(key, frame)
            last_observed_frame[key] = frame
    inventory = {}
    for stage in manifest["stages"]:
        stage_index = int(stage["internal_stage_index"])
        ecl = parse_ecl(ROOT / "artifacts" / "decoded" / stage["ecl_file"])
        reachable = set(int(value) for value in stage["reachable_subroutines"])
        expected_phase_markers = []
        for subroutine in ecl.subroutines:
            if subroutine.index not in reachable:
                continue
            for instruction in subroutine.instructions:
                if (
                    instruction.opcode == 0x94
                    and instruction.difficulty_mask
                    & active_difficulty_mask
                ):
                    expected_phase_markers.append(
                        {
                            "subroutine": subroutine.index,
                            "offset": instruction.offset,
                            "argument": int(instruction.arguments[0]),
                        }
                    )
        spells = []
        for spell in stage["reachable_spell_occurrences"]:
            spell_id = int(spell["spell_id"])
            runtime_key = (stage_index, spell_id)
            observed_decision_count = observed_decisions[runtime_key]
            runtime_observed = observed_decision_count > 0
            spells.append(
                {
                    "spell_id": spell_id,
                    "name": spell["name"],
                    "owner": spell["owner"],
                    "subroutine": int(spell["subroutine"]),
                    "feature_counts": spell["feature_counts"],
                    "runtime_attribution": {
                        "status": (
                            (
                                "observed_live_spell_state"
                                if runtime_observed
                                else "not_observed_in_trace"
                            )
                            if spell_schema_complete
                            else "unresolved_current_trace_schema"
                        ),
                        "observed": (
                            runtime_observed if spell_schema_complete else None
                        ),
                        "observed_decision_count": (
                            observed_decision_count
                            if spell_schema_complete
                            else None
                        ),
                        "first_decision_frame": (
                            first_observed_frame.get(runtime_key)
                            if spell_schema_complete
                            else None
                        ),
                        "last_decision_frame": (
                            last_observed_frame.get(runtime_key)
                            if spell_schema_complete
                            else None
                        ),
                        "hit_count": (
                            attributed_hits[runtime_key]
                            if spell_schema_complete
                            else None
                        ),
                        "reason": (
                            (
                                None
                                if runtime_observed
                                else (
                                    "No decision in this run reported this "
                                    "active spell ID."
                                )
                            )
                            if spell_schema_complete
                            else (
                                "The live decision schema did not record "
                                "g_spell_card_state spell ID."
                            )
                        ),
                    },
                }
            )
        inventory[stage_index] = {
            "stage_route_index": stage_index,
            "stage_label": stage["label"],
            "ecl_file": stage["ecl_file"],
            "expected_reachable_phase_markers": expected_phase_markers,
            "observed_counter_jump_markers": phase_markers.get(
                stage_index,
                [],
            ),
            "alignment_status": "insufficient_for_exact_spell_assignment",
            "spells": spells,
        }
    return inventory


def build_dossier(
    *,
    run_id: str,
    provenance: list[TraceProvenance],
    decisions: list[dict[str, object]],
    manifest: dict[str, object],
    observed_stall_frames: list[int],
    completion_probe: dict[str, object],
) -> dict[str, object]:
    if not decisions:
        raise ValueError("run contains no decisions")
    difficulty = str(manifest["difficulty"])
    difficulty_index = int(manifest["difficulty_index"])
    deaths = _death_ledger(
        decisions,
        case_prefix=_case_prefix_for_difficulty(difficulty),
    )
    phase_markers = _phase_markers(decisions)
    spell_schema_complete = all(
        isinstance(decision.get("spell"), dict) for decision in decisions
    )
    spell_inventory = _spell_inventory(
        manifest,
        phase_markers,
        deaths,
        decisions,
        spell_schema_complete=spell_schema_complete,
    )
    by_stage: dict[int, list[dict[str, object]]] = defaultdict(list)
    for decision in decisions:
        by_stage[int(decision["stage_route_index"])].append(decision)
    stage_reports = []
    for stage_index, stage_decisions in by_stage.items():
        stage_deaths = [
            death
            for death in deaths
            if int(death["stage_route_index"]) == stage_index
        ]
        stage_reports.append(
            {
                "stage_route_index": stage_index,
                "stage_label": STAGE_ROUTE_LABELS.get(stage_index),
                "first_frame": stage_decisions[0]["frame"],
                "last_frame": stage_decisions[-1]["frame"],
                "observed_frame_span": (
                    int(stage_decisions[-1]["frame"])
                    - int(stage_decisions[0]["frame"])
                ),
                "decision_count": len(stage_decisions),
                "death_count": len(stage_deaths),
                "death_frames": [death["frame"] for death in stage_deaths],
                "death_cause_counts": dict(
                    Counter(
                        str(death["primary_cause_class"])
                        for death in stage_deaths
                    )
                ),
                "deathbomb_count": sum(
                    bool(death["deathbomb_requested"])
                    for death in stage_deaths
                ),
                "post_hit_bomb_stock_decrease": sum(
                    float(death["post_hit_bomb_stock_decrease"])
                    for death in stage_deaths
                ),
                "resources": {
                    key: _resource_range(stage_decisions, key)
                    for key in ("lives", "bombs", "power")
                },
                "max_active_bullets": max(
                    int(row["active_bullets"])
                    for row in stage_decisions
                ),
                "max_active_lasers": max(
                    int(row["active_lasers"]) for row in stage_decisions
                ),
                "max_active_items": max(
                    int(row["active_items"]) for row in stage_decisions
                ),
                "boundary_occupancy": {
                    "bottom_decisions": sum(
                        float(row["player"]["y"]) >= 428.0
                        for row in stage_decisions
                    ),
                    "side_decisions": sum(
                        float(row["player"]["x"]) <= 12.0
                        or float(row["player"]["x"]) >= 372.0
                        for row in stage_decisions
                    ),
                },
                "latency_ms": {
                    "read": _percentiles(
                        row["read_ms"] for row in stage_decisions
                    ),
                    "plan": _percentiles(
                        row["plan_ms"] for row in stage_decisions
                    ),
                },
                "frame_lag": {
                    "snapshot": _percentiles(
                        row["snapshot_lag"] for row in stage_decisions
                    ),
                    "action": _percentiles(
                        row["action_lag"] for row in stage_decisions
                    ),
                },
                "phase_marker_alignment": {
                    "expected_reachable_opcode_94_count": len(
                        spell_inventory[stage_index][
                            "expected_reachable_phase_markers"
                        ]
                    ),
                    "observed_approximately_1800_frame_jump_count": len(
                        phase_markers.get(stage_index, [])
                    ),
                    "status": "not_one_to_one_with_spell_cards",
                },
                "robust_viability": _robust_viability_summary(
                    stage_decisions
                ),
                "planner_consistency": _planner_consistency_summary(
                    stage_decisions
                ),
            }
        )
    stage_reports.sort(key=lambda stage: int(stage["first_frame"]))

    interruptions = []
    for previous, current in zip(provenance, provenance[1:]):
        if previous.last_frame is None or current.first_frame is None:
            continue
        interruptions.append(
            {
                "after_trace": previous.path,
                "before_trace": current.path,
                "last_observed_frame": previous.last_frame,
                "next_observed_frame": current.first_frame,
                "unobserved_frame_delta": (
                    current.first_frame - previous.last_frame
                ),
                "reason": "foreground_loss_and_manual_rearm",
            }
        )

    cause_counts = Counter(
        str(death["primary_cause_class"]) for death in deaths
    )
    contributing_counts = Counter(
        factor
        for death in deaths
        for factor in death["contributing_factors"]
    )
    return {
        "schema": "th08-route-run-dossier-v4",
        "run_id": run_id,
        "acceptance_target": {
            "difficulty": difficulty,
            "difficulty_index": difficulty_index,
            "route_id": 2,
            "team": "Sakuya/Remilia",
            "ending_branch": "Final B / Kaguya",
            "combat_completion": True,
        },
        "route_manifest": {
            "profile": manifest["profile"],
            "active_difficulty_mask": int(
                manifest["active_difficulty_mask"]
            ),
        },
        "integrity": {
            "raw_trace_bytes": sum(item.size_bytes for item in provenance),
            "json_decode_errors": sum(
                item.parse_errors for item in provenance
            ),
            "trace_count": len(provenance),
            "foreground_interruption_count": len(interruptions),
            "spell_attribution": (
                "resolved_live_spell_state"
                if spell_schema_complete
                else "unresolved_current_trace_schema"
            ),
        },
        "provenance": [
            {
                **item.__dict__,
                "runtime_errors": list(item.runtime_errors),
            }
            for item in provenance
        ],
        "interruptions": interruptions,
        "completion_probe": completion_probe,
        "totals": {
            "decision_count": len(decisions),
            "first_frame": decisions[0]["frame"],
            "last_frame": decisions[-1]["frame"],
            "death_count": len(deaths),
            "deathbomb_count": sum(
                bool(death["deathbomb_requested"]) for death in deaths
            ),
            "post_hit_bomb_stock_decrease": sum(
                float(death["post_hit_bomb_stock_decrease"])
                for death in deaths
            ),
            "primary_cause_counts": dict(cause_counts),
            "contributing_factor_counts": dict(contributing_counts),
        },
        "observed_auto_confirm_stalls": {
            "frames": observed_stall_frames,
            "root_causes": [
                "phase==0 eligibility excluded dialogue windows in phase 3",
                (
                    "the live loop emitted input only after the enemy frame "
                    "counter advanced"
                ),
                (
                    "a frozen dialogue counter could strand a Z release "
                    "without the restoring press"
                ),
            ],
        },
        "control_policy": {
            "no_bomb_verification": _no_bomb_verification(
                decisions,
                provenance,
            ),
            "robust_viability": _robust_viability_summary(decisions),
            "planner_consistency": _planner_consistency_summary(decisions),
        },
        "stages": stage_reports,
        "death_clusters": _death_clusters(deaths),
        "deaths": deaths,
        "spell_inventory": [
            spell_inventory[index]
            for index in sorted(
                spell_inventory,
                key=lambda key: next(
                    int(stage["first_frame"])
                    for stage in stage_reports
                    if int(stage["stage_route_index"]) == key
                ),
            )
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--trace", type=Path, action="append", required=True)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=(
            ROOT
            / "artifacts"
            / "route_manifests"
            / "sakuya_remilia_lunatic_final_b.json"
        ),
    )
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    parser.add_argument("--death-csv", type=Path, required=True)
    parser.add_argument("--regression-output", type=Path, required=True)
    parser.add_argument(
        "--observed-stall-frame",
        type=int,
        action="append",
        default=[],
    )
    parser.add_argument(
        "--completion-frame",
        type=int,
        required=True,
    )
    parser.add_argument(
        "--completion-engine-flags",
        type=lambda value: int(value, 0),
        required=True,
    )
    args = parser.parse_args(argv)

    provenance = []
    decisions = []
    for trace_index, path in enumerate(args.trace):
        trace_provenance, trace_decisions = read_trace(
            path,
            trace_index=trace_index,
        )
        provenance.append(trace_provenance)
        decisions.extend(trace_decisions)
    decisions.sort(key=lambda row: (int(row["frame"]), int(row["trace_index"])))
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    dossier = build_dossier(
        run_id=args.run_id,
        provenance=provenance,
        decisions=decisions,
        manifest=manifest,
        observed_stall_frames=args.observed_stall_frame,
        completion_probe={
            "enemy_manager_frame": args.completion_frame,
            "engine_flags": args.completion_engine_flags,
            "engine_flags_hex": f"{args.completion_engine_flags:#x}",
            "gameplay_active": False,
            "resources_available": False,
            "interpretation": "Final B combat scene unloaded",
        },
    )

    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(
            dossier,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.write_text(
        render_markdown(dossier) + "\n",
        encoding="utf-8",
    )
    write_death_csv(args.death_csv, dossier["deaths"])
    args.regression_output.parent.mkdir(parents=True, exist_ok=True)
    args.regression_output.write_text(
        json.dumps(
            {
                "schema": "th08-live-death-regressions-v1",
                "run_id": args.run_id,
                "case_count": len(dossier["deaths"]),
                "no_bomb_verification": dossier["control_policy"][
                    "no_bomb_verification"
                ],
                "cases": dossier["deaths"],
            },
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )
    print(args.markdown_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
