#!/usr/bin/env python3
"""Build an offline stitched run dossier from live-agent traces."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from th08_ecl import parse_ecl
from analysis.dossier import attribution as _attribution
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
_robust_control_unsafe = _attribution.robust_control_unsafe
_spell_attribution = _attribution.spell_attribution
_viability_action_set_empty = _attribution.viability_action_set_empty
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


def _planner_consistency_summary(
    decisions: list[dict[str, object]],
) -> dict[str, object]:
    """Cross-tab distinct global-horizon and local-prefix safety contracts.

    A global winning state promises a policy over the remaining corridor
    horizon.  The local certificate only checks the selected action over its
    delay-plus-hold prefix.  Those Boolean values are useful together, but
    disagreement is not itself a contradiction.  The action-level
    contradiction is narrower: an action in the global winning set that the
    fresh local tube checker finds unsafe.
    """

    comparable = []
    excluded_hazard_version_change_count = 0
    excluded_deadline_hold_count = 0
    for row in decisions:
        player = row.get("player")
        if isinstance(player, dict) and (
            int(player.get("phase", 0)) != 0
            or int(player.get("phase_at_action", 0)) != 0
        ):
            continue
        viability = row.get("viability")
        robust = row.get("robust_control")
        if (
            not isinstance(viability, dict)
            or not bool(viability.get("available"))
            or not bool(viability.get("support_covers_current", True))
            or not isinstance(robust, dict)
        ):
            continue
        issue_guard = row.get("issue_time_enemy_guard")
        if (
            isinstance(issue_guard, dict)
            and bool(issue_guard.get("changes"))
        ):
            # The global policy and its action mask belong to the pre-issue
            # hazard version.  The issue guard deliberately invalidates that
            # version and recertifies against a newer local snapshot.
            excluded_hazard_version_change_count += 1
            continue
        deadline_guard = row.get("deadline_guard")
        if (
            isinstance(deadline_guard, dict)
            and bool(deadline_guard.get("input_suppressed"))
        ):
            # The traced action is the already-active input, not the newly
            # planned action whose global membership was queried.
            excluded_deadline_hold_count += 1
            continue
        global_safe = (
            bool(viability.get("state_viable"))
            and int(viability.get("safe_action_count", 0)) > 0
        )
        local_safe = (
            int(robust.get("worst_collisions", 0)) == 0
            and float(robust.get("min_clearance", 0.0)) >= 0.0
        )
        safe_actions = {
            str(action) for action in viability.get("safe_actions", ())
        }
        comparable.append(
            {
                "global_winning": global_safe,
                "local_prefix_safe": local_safe,
                "selected_in_winning_set": (
                    str(row.get("action", "")) in safe_actions
                ),
            }
        )
    count = len(comparable)

    def count_where(predicate) -> int:
        return sum(bool(predicate(item)) for item in comparable)

    global_winning_local_prefix_unsafe = count_where(
        lambda item: (
            item["global_winning"] and not item["local_prefix_safe"]
        )
    )
    global_losing_local_prefix_safe = count_where(
        lambda item: (
            not item["global_winning"] and item["local_prefix_safe"]
        )
    )
    certified_action_local_prefix_unsafe = count_where(
        lambda item: (
            item["global_winning"]
            and item["selected_in_winning_set"]
            and not item["local_prefix_safe"]
        )
    )
    selected_outside = count_where(
        lambda item: (
            item["global_winning"]
            and not item["selected_in_winning_set"]
        )
    )
    return {
        "comparable_decision_count": count,
        "global_winning_local_prefix_safe_count": count_where(
            lambda item: (
                item["global_winning"] and item["local_prefix_safe"]
            )
        ),
        "global_winning_local_prefix_unsafe_count": (
            global_winning_local_prefix_unsafe
        ),
        "global_losing_local_prefix_safe_count": (
            global_losing_local_prefix_safe
        ),
        "global_losing_local_prefix_unsafe_count": count_where(
            lambda item: (
                not item["global_winning"]
                and not item["local_prefix_safe"]
            )
        ),
        "selected_certified_action_local_prefix_unsafe_count": (
            certified_action_local_prefix_unsafe
        ),
        "selected_certified_action_local_prefix_unsafe_fraction": (
            certified_action_local_prefix_unsafe / count
            if count
            else None
        ),
        "selected_action_outside_global_winning_set_count": selected_outside,
        "excluded_hazard_version_change_count": (
            excluded_hazard_version_change_count
        ),
        "excluded_deadline_hold_count": excluded_deadline_hold_count,
        "semantics": (
            "global is a remaining-horizon winning-set claim; local is a "
            "delay-plus-hold prefix claim. After excluding observed "
            "issue-time invalidations, a selected cached-policy action that "
            "the fresh local prefix finds unsafe is a forecast/version "
            "contradiction; future births can still make the cached hazard "
            "set older than the local one. Deadline holds are excluded "
            "because their final input is not governed by that policy query."
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
            spells.append(
                {
                    "spell_id": spell_id,
                    "name": spell["name"],
                    "owner": spell["owner"],
                    "subroutine": int(spell["subroutine"]),
                    "feature_counts": spell["feature_counts"],
                    "runtime_attribution": {
                        "status": (
                            "resolved_live_spell_state"
                            if spell_schema_complete
                            else "unresolved_current_trace_schema"
                        ),
                        "hit_count": (
                            attributed_hits[(stage_index, spell_id)]
                            if spell_schema_complete
                            else None
                        ),
                        "reason": (
                            None
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
        "schema": "th08-route-run-dossier-v3",
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


def _format_number(value: object) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def render_markdown(dossier: dict[str, object]) -> str:
    totals = dossier["totals"]
    integrity = dossier["integrity"]
    control_policy = dossier["control_policy"]
    no_bomb = control_policy["no_bomb_verification"]
    viability = control_policy["robust_viability"]
    consistency = control_policy["planner_consistency"]
    spell_attribution_resolved = (
        integrity["spell_attribution"] == "resolved_live_spell_state"
    )
    difficulty = str(dossier["acceptance_target"]["difficulty"])
    lines = [
        f"# TH08 {difficulty} Full-Run Review: {dossier['run_id']}",
        "",
        "## Result",
        "",
        f"- Route: Sakuya/Remilia, {difficulty}, Final B / Kaguya.",
        "- Combat completion: yes; gameplay scene unloaded at frame "
        f"{dossier['completion_probe']['enemy_manager_frame']}.",
        "- Native phase-2 hit edges, including Last-Spell-saveable edges: "
        f"{totals['death_count']}.",
        f"- Deathbomb requests at those edges: {totals['deathbomb_count']}.",
        "- Hard no-Bomb input verification: "
        f"{'passed' if no_bomb['passed'] else 'FAILED'} across "
        f"{no_bomb['decision_count_checked']} decisions.",
        "- Post-hit Bomb-stock decreases: "
        f"{_format_number(totals['post_hit_bomb_stock_decrease'])}; this is "
        "respawn-stock reset telemetry, not evidence of Bomb input.",
        f"- Agent decisions: {totals['decision_count']}.",
        f"- Raw trace size: {integrity['raw_trace_bytes']} bytes across "
        f"{integrity['trace_count']} segments.",
        f"- JSON decode errors: {integrity['json_decode_errors']}.",
        (
            "- Exact spell-level hit attribution: available from live "
            "`g_spell_card_state`."
            if spell_attribution_resolved
            else (
                "- Exact spell-level hit attribution: unavailable in this run "
                "because the live schema did not record `g_spell_card_state`."
            )
        ),
        "",
        "The run is valid for stage-, death-, resource-, projectile-, latency-, "
        "and route-level analysis. Spell names below are the statically "
        f"reachable {difficulty} route inventory; unavailable runtime hit counts "
        "remain explicitly unresolved instead of guessed. The no-life patch "
        "allows post-hit resource resets to repeat, so resource-stock changes "
        "must not be interpreted as Bomb commands.",
        "",
        "## Trace Integrity",
        "",
        "| Segment | Frames | Decisions | Wall Z | Termination | Runtime error "
        "| SHA-256 |",
        "| --- | ---: | ---: | ---: | --- | --- | --- |",
    ]
    for index, item in enumerate(dossier["provenance"], 1):
        runtime_errors = item["runtime_errors"]
        runtime_error = (
            str(runtime_errors[-1].get("error")) if runtime_errors else "-"
        )
        termination = (
            item["summary"].get("termination_reason")
            if item["summary"]
            else "missing"
        )
        lines.append(
            f"| {index} | {item['first_frame']}..{item['last_frame']} | "
            f"{item['decision_count']} | "
            f"{len(item['wall_auto_confirm_frames'])} | {termination} | "
            f"{runtime_error} | "
            f"`{item['sha256']}` |"
        )
    interruptions = integrity["foreground_interruption_count"]
    if interruptions:
        lines.extend(
            [
                "",
                f"Foreground interruptions: {interruptions}. Interruption "
                "intervals are excluded from agent-controlled scoring.",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "The route is one continuous agent-controlled trace with no "
                "foreground interruption or manual re-arm gap.",
            ]
        )
    lines.extend(
        [
            "",
            "## Stage Summary",
            "",
            "| Stage | Frames | Decisions | Native hits | Deathbombs | "
            "Post-hit Bomb-stock decrease | "
            "Power start/end/min | Max bullets | Max lasers |",
            "| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |",
        ]
    )
    for stage in dossier["stages"]:
        power = stage["resources"]["power"]
        lines.append(
            f"| {stage['stage_label']} | {stage['first_frame']}.."
            f"{stage['last_frame']} | {stage['decision_count']} | "
            f"{stage['death_count']} | {stage['deathbomb_count']} | "
            f"{_format_number(stage['post_hit_bomb_stock_decrease'])} | "
            f"{_format_number(power['start'])}/"
            f"{_format_number(power['end'])}/"
            f"{_format_number(power['min'])} | "
            f"{stage['max_active_bullets']} | "
            f"{stage['max_active_lasers']} |"
        )
    lines.extend(
        [
            "",
            "## Failure Taxonomy",
            "",
            "| Primary class | Deaths | Interpretation |",
            "| --- | ---: | --- |",
        ]
    )
    interpretations = {
        "observed_enemy_body_overlap": (
            "A captured lethal enemy-body AABB overlaps the player at action "
            "time."
        ),
        "observed_multiple_hazard_overlap": (
            "More than one captured native hazard family overlaps at the hit "
            "edge; the trace does not invent a single causal winner."
        ),
        "observed_bullet_overlap": (
            "A bullet overlaps the native player AABB in the hit observation."
        ),
        "observed_laser_overlap": (
            "The player overlaps an active laser's exact finite segment; TH08 "
            "checks this before the broad bullet pass."
        ),
        "active_laser_without_observed_overlap": (
            "At least one laser is active, but none of the persisted finite "
            "segments overlaps the player in the hit observation."
        ),
        "modeled_committed_prefix_collision": (
            "The measured three-frame input pipeline was already unsafe."
        ),
        "sensor_gap_or_unmodeled_hazard": (
            "No observed overlap and positive pipeline clearance; same-frame "
            "ECL emission, transform error, or another unmodeled hazard is "
            "the leading explanation."
        ),
    }
    for cause, count in sorted(
        totals["primary_cause_counts"].items(),
        key=lambda item: (-item[1], item[0]),
    ):
        lines.append(
            f"| `{cause}` | {count} | {interpretations[cause]} |"
        )
    lines.extend(
        [
            "",
            "Contributing factors:",
            "",
        ]
    )
    for factor, count in sorted(
        totals["contributing_factor_counts"].items(),
        key=lambda item: (-item[1], item[0]),
    ):
        lines.append(f"- `{factor}`: {count} deaths")

    lines.extend(
        [
            "",
            "## High-Risk Clusters",
            "",
            "| Cluster | Stage | Frames | Deaths | Min Power | Max bullets at "
            "hit |",
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for cluster in sorted(
        dossier["death_clusters"],
        key=lambda cluster: (
            -int(cluster["death_count"]),
            int(cluster["start_frame"]),
        ),
    ):
        if int(cluster["death_count"]) < 2:
            continue
        lines.append(
            f"| {cluster['cluster_id']} | {cluster['stage_label']} | "
            f"{cluster['start_frame']}..{cluster['end_frame']} | "
            f"{cluster['death_count']} | "
            f"{_format_number(cluster['minimum_power'])} | "
            f"{cluster['maximum_active_bullets_at_hit']} |"
        )

    lines.extend(
        [
            "",
            "## Stage Detail",
            "",
        ]
    )
    deaths_by_stage = defaultdict(list)
    for death in dossier["deaths"]:
        deaths_by_stage[int(death["stage_route_index"])].append(death)
    for stage in dossier["stages"]:
        stage_index = int(stage["stage_route_index"])
        lines.extend(
            [
                f"### {stage['stage_label']}",
                "",
                f"- Death frames: "
                f"{', '.join(str(frame) for frame in stage['death_frames']) or '-'}",
                f"- Cause counts: `{json.dumps(stage['death_cause_counts'], ensure_ascii=False)}`",
                f"- Phase markers: observed "
                f"{stage['phase_marker_alignment']['observed_approximately_1800_frame_jump_count']}, "
                f"reachable static opcode `0x94` "
                f"{stage['phase_marker_alignment']['expected_reachable_opcode_94_count']}.",
                f"- Bottom/side occupancy decisions: "
                f"{stage['boundary_occupancy']['bottom_decisions']}/"
                f"{stage['boundary_occupancy']['side_decisions']}.",
                "",
                "| Frame | Bombs | Power | Post-hit stock drop | Bullets | Pipeline | "
                "Corridor slack | Cause | Factors |",
                "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
            ]
        )
        for death in deaths_by_stage[stage_index]:
            factors = ",".join(death["contributing_factors"]) or "-"
            lines.append(
                f"| {death['frame']} | "
                f"{_format_number(death['resources_at_hit']['bombs'])} | "
                f"{_format_number(death['resources_at_hit']['power'])} | "
                f"{_format_number(death['post_hit_bomb_stock_decrease'])} | "
                f"{death['active_bullets']} | "
                f"{_format_number(death['pipeline_clearance_at_hit'])} | "
                f"{_format_number(death['minimum_corridor_slack_240f'])} | "
                f"`{death['primary_cause_class']}` | {factors} |"
            )
        lines.append("")

    lines.extend(
        [
            "## Spell Inventory And Runtime Coverage",
            "",
            f"Every spell below is statically reachable for route 2 {difficulty} "
            "Final B. `unresolved` means this run did not persist the live "
            "spell ID; it does not mean the spell was absent.",
            "",
        ]
    )
    for stage in dossier["spell_inventory"]:
        lines.extend(
            [
                f"### {stage['stage_label']}",
                "",
                f"- ECL: `{stage['ecl_file']}`",
                f"- Observed/expected phase-counter markers: "
                f"{len(stage['observed_counter_jump_markers'])}/"
                f"{len(stage['expected_reachable_phase_markers'])}.",
                "",
                "| ID | Name | Owner | Emits | Transforms | Lasers | Runtime |",
                "| ---: | --- | --- | ---: | ---: | ---: | --- |",
            ]
        )
        for spell in stage["spells"]:
            features = spell["feature_counts"]
            runtime = spell["runtime_attribution"]
            runtime_value = (
                str(runtime["hit_count"])
                if runtime["hit_count"] is not None
                else "unresolved"
            )
            lines.append(
                f"| {spell['spell_id']} | {spell['name']} | "
                f"{spell['owner']} | {features['bullet_emit']} | "
                f"{features['transform_define']} | "
                f"{features['laser_spawn']} | {runtime_value} |"
            )
        lines.append("")

    stalls = dossier["observed_auto_confirm_stalls"]["frames"]
    solve_ms = viability["solve_ms"] or {
        "median": None,
        "p95": None,
        "max": None,
    }
    policy_age = viability["first_observed_age_frames"] or {
        "median": None,
        "p95": None,
        "max": None,
    }
    stalls_text = ", ".join(str(frame) for frame in stalls) or "none"
    final_summary = dossier["provenance"][-1].get("summary") or {}
    termination_reason = final_summary.get("termination_reason", "missing")
    sensor_gap_count = int(
        totals["primary_cause_counts"].get(
            "sensor_gap_or_unmodeled_hazard",
            0,
        )
    )
    lines.extend(
        [
            "## Runtime And Harness Findings",
            "",
            f"- Observed auto-Z stall frames: {stalls_text}.",
            "- Route termination: "
            f"`{termination_reason}` "
            f"at completion probe frame "
            f"{dossier['completion_probe']['enemy_manager_frame']}.",
            "- Unique robust solutions observed: "
            f"{viability['unique_solution_count']}; solve time median/p95/max "
            f"{_format_number(solve_ms['median'])}/"
            f"{_format_number(solve_ms['p95'])}/"
            f"{_format_number(solve_ms['max'])} ms.",
            "- First-observed policy age median/p95/max: "
            f"{_format_number(policy_age['median'])}/"
            f"{_format_number(policy_age['p95'])}/"
            f"{_format_number(policy_age['max'])} frames.",
            "- Viability queries available: "
            f"{viability['available_query_count']}/"
            f"{viability['query_count']}; robustly constrained decisions: "
            f"{viability['constrained_decision_count']}/"
            f"{totals['decision_count']}.",
            "- Robust-policy decisions without any usable query: "
            f"{viability['decision_without_query_count']}/"
            f"{viability['policy_decision_count']}.",
            "- Global-horizon/local-prefix cross-tab: "
            f"{consistency['comparable_decision_count']} decisions; winning "
            "global state with unsafe selected prefix: "
            f"{consistency['global_winning_local_prefix_unsafe_count']}; "
            "losing global state with safe short prefix: "
            f"{consistency['global_losing_local_prefix_safe_count']}; "
            "selected globally certified action contradicted by the fresh "
            "local prefix checker: "
            f"{consistency['selected_certified_action_local_prefix_unsafe_count']}; "
            "selected action outside the reported winning set: "
            f"{consistency['selected_action_outside_global_winning_set_count']}.",
            "- Live spell attribution was recorded at every hit edge; exact "
            "per-spell counts are preserved below.",
            f"- `{sensor_gap_count}` hit edges remain in the "
            "`sensor_gap_or_unmodeled_hazard` class and require executor-level "
            "same-frame emission/transform evidence.",
            "",
            "## Next Regression Work",
            "",
            "1. Keep robust backward-reachability solves within the finite "
            "policy horizon, then verify nonzero live query and constrained-"
            "decision counts.",
            f"2. Replay all {totals['death_count']} retained witnesses through "
            "the integrated executor and preserve one regression per concrete "
            "failure.",
            "3. Re-run focused Stage 4A and Final B practices before another "
            f"full {difficulty} route; compare hit frames, policy age, action-set "
            "exhaustion, and cluster recurrence.",
            "4. Add item/Power state and finite Bomb resources only after the "
            "no-Bomb movement policy has passed physical validation.",
        ]
    )
    return "\n".join(lines)


def write_death_csv(
    path: Path,
    deaths: list[dict[str, object]],
) -> None:
    fieldnames = [
        "case_id",
        "frame",
        "trace_index",
        "stage_route_index",
        "stage_label",
        "player_x",
        "player_y",
        "bombs",
        "power",
        "observed_bomb_cost",
        "post_hit_bomb_stock_decrease",
        "deathbomb_requested",
        "active_bullets",
        "active_lasers",
        "active_items",
        "pipeline_clearance_at_hit",
        "minimum_pipeline_clearance_240f",
        "minimum_corridor_slack_240f",
        "action_lag",
        "action",
        "nearest_bullet_slot",
        "nearest_bullet_clearance",
        "nearest_laser_slot",
        "nearest_laser_clearance",
        "primary_cause_class",
        "planner_failure_class",
        "usable_robust_warning_lead_frames",
        "usable_viability_warning_lead_frames",
        "viability_kernel_exhausted_at_frame",
        "contributing_factors",
        "spell_id",
        "spell_name",
        "spell_attribution_status",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(
            output,
            fieldnames=fieldnames,
            lineterminator="\n",
        )
        writer.writeheader()
        for death in deaths:
            nearest = death["nearest_observed_bullet"]
            nearest_laser = death["nearest_observed_laser"]
            writer.writerow(
                {
                    "case_id": death["case_id"],
                    "frame": death["frame"],
                    "trace_index": death["trace_index"],
                    "stage_route_index": death["stage_route_index"],
                    "stage_label": death["stage_label"],
                    "player_x": death["player"]["x"],
                    "player_y": death["player"]["y"],
                    "bombs": death["resources_at_hit"]["bombs"],
                    "power": death["resources_at_hit"]["power"],
                    "observed_bomb_cost": death["observed_bomb_cost"],
                    "post_hit_bomb_stock_decrease": death[
                        "post_hit_bomb_stock_decrease"
                    ],
                    "deathbomb_requested": death["deathbomb_requested"],
                    "active_bullets": death["active_bullets"],
                    "active_lasers": death["active_lasers"],
                    "active_items": death["active_items"],
                    "pipeline_clearance_at_hit": death[
                        "pipeline_clearance_at_hit"
                    ],
                    "minimum_pipeline_clearance_240f": death[
                        "minimum_pipeline_clearance_240f"
                    ],
                    "minimum_corridor_slack_240f": death[
                        "minimum_corridor_slack_240f"
                    ],
                    "action_lag": death["action_lag"],
                    "action": death["action"],
                    "nearest_bullet_slot": (
                        nearest["slot"] if nearest else None
                    ),
                    "nearest_bullet_clearance": (
                        nearest["aabb_clearance"] if nearest else None
                    ),
                    "nearest_laser_slot": (
                        nearest_laser["slot"] if nearest_laser else None
                    ),
                    "nearest_laser_clearance": (
                        nearest_laser["clearance"] if nearest_laser else None
                    ),
                    "primary_cause_class": death["primary_cause_class"],
                    "planner_failure_class": death[
                        "planner_failure_class"
                    ],
                    "usable_robust_warning_lead_frames": death.get(
                        "usable_robust_warning_lead_frames",
                        0,
                    ),
                    "usable_viability_warning_lead_frames": death.get(
                        "usable_viability_warning_lead_frames",
                        0,
                    ),
                    "viability_kernel_exhausted_at_frame": death.get(
                        "viability_kernel_exhausted_at_frame"
                    ),
                    "contributing_factors": ";".join(
                        death["contributing_factors"]
                    ),
                    "spell_id": death["spell_attribution"]["spell_id"],
                    "spell_name": death["spell_attribution"]["spell_name"],
                    "spell_attribution_status": death[
                        "spell_attribution"
                    ]["status"],
                }
            )


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
        json.dumps(dossier, indent=2, ensure_ascii=False) + "\n",
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
        )
        + "\n",
        encoding="utf-8",
    )
    print(args.markdown_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
