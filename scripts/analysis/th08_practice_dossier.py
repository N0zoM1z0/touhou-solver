#!/usr/bin/env python3
"""Build an offline scoped thprac no-Bomb practice dossier."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import Counter
from pathlib import Path

from analysis.dossier.attribution import (
    build_death_ledger as _death_ledger,
    case_prefix_for_difficulty as _case_prefix_for_difficulty,
    cluster_deaths as _death_clusters,
)
from analysis.dossier.statistics import (
    percentiles as _percentiles,
    resource_range as _resource_range,
)
from analysis.dossier.trace_reader import (
    PracticeTrace,
    extract_scope,
    read_practice_trace,
    select_frame_epoch,
)
from analysis.th08_run_dossier import _planner_consistency_summary
from analysis.th08_trial_report import STAGE_ROUTE_LABELS


ROOT = Path(__file__).resolve().parents[2]
_extract_scope = extract_scope
_select_frame_epoch = select_frame_epoch
BOMB_INPUT_BIT = 0x02
TERMINAL_THREAT_SAFETY_CLEARANCE = 8.0
ENEMY_POOL_BASE = 0x005826C0
ENEMY_POOL_SIZE = 480
ENEMY_STRIDE = 0x53D0


def _no_bomb_verification(
    decisions: list[dict[str, object]],
    controller_configs: tuple[dict[str, object], ...],
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
    configured_disabled = any(
        row.get("bomb_policy") == "disabled" for row in controller_configs
    )
    passed = (
        configured_disabled
        and not mask_violations
        and not flag_violations
        and not action_violations
    )
    return {
        "passed": passed,
        "bomb_input_bit": BOMB_INPUT_BIT,
        "controller_policy_disabled": configured_disabled,
        "decision_count_checked": len(decisions),
        "mask_violation_frames": mask_violations,
        "bomb_flag_violation_frames": flag_violations,
        "bomb_action_violation_frames": action_violations,
        "resource_note": (
            "Bomb stock changes after a hit are thprac respawn-state changes, "
            "not Bomb input; the mask, decision flag, and action are the "
            "controller evidence."
        ),
    }


def _promote_enemy_body_candidates(
    deaths: list[dict[str, object]],
) -> None:
    for index, death in enumerate(deaths):
        spell = death["spell_attribution"]
        if not (
            death["primary_cause_class"]
            == "sensor_gap_or_unmodeled_hazard"
            and spell["status"] == "resolved_live_spell_state"
            and int(spell.get("enemy_pointer", 0)) != 0
            and int(death["active_bullets"]) == 0
            and int(death["active_lasers"]) == 0
            and float(death["pipeline_clearance_at_hit"]) > 0.0
        ):
            continue
        death["primary_cause_class"] = "enemy_body_contact_candidate"
        death["enemy_body_evidence"] = {
            "confidence": (
                "strong static candidate; exact runtime overlap not yet "
                "captured"
            ),
            "enemy_pointer": int(spell["enemy_pointer"]),
            "canonical_fresh_attempt_sample": index == 0,
            "native_path": [
                {
                    "address": "0x42cf7a",
                    "meaning": (
                        "enemy manager invokes player contact using enemy "
                        "+0x2d88 position, +0x2d70 contact size, and +0x3324 "
                        "contact flags"
                    ),
                },
                {
                    "address": "0x42c33f",
                    "meaning": "enemy contact size is scaled by 1.5",
                },
                {
                    "address": "0x44a360",
                    "name": "player_test_deadly_aabb_contact",
                    "meaning": (
                        "enemy AABB versus player lethal rectangle; overlap "
                        "calls player_dead_handler"
                    ),
                },
            ],
            "missing_runtime_field": (
                "active enemy position/contact-size/flags at the hit frame"
            ),
        }


def _corridor_latency(
    decisions: list[dict[str, object]],
) -> dict[str, object]:
    unique: dict[int, dict[str, object]] = {}
    for row in decisions:
        source = row.get("corridor_source_frame")
        if source is None:
            continue
        unique.setdefault(int(source), row)

    def stats(
        rows: list[dict[str, object]],
    ) -> dict[str, object]:
        return {
            "unique_solution_count": len(rows),
            "solve_ms": _percentiles(
                float(row["corridor_solve_ms"]) for row in rows
            ),
            "age_frames": _percentiles(
                float(row["corridor_age"]) for row in rows
            ),
            "stale_solution_count": sum(
                bool(row["corridor_stale"]) for row in rows
            ),
        }

    unique_rows = list(unique.values())
    spell_50_rows = [
        row
        for row in unique_rows
        if isinstance(row.get("spell"), dict)
        and bool(row["spell"].get("active"))
        and int(row["spell"].get("spell_id", -1)) == 50
    ]
    return {
        "all": stats(unique_rows),
        "active_spell_50": stats(spell_50_rows),
    }


def _decision_cadence(
    decisions: list[dict[str, object]],
) -> dict[str, object]:
    deltas = [
        int(right["frame"]) - int(left["frame"])
        for left, right in zip(decisions, decisions[1:])
        if 0 < int(right["frame"]) - int(left["frame"]) < 120
    ]
    percentiles = _percentiles(deltas) or {
        "median": None,
        "p95": None,
        "max": None,
    }
    return {
        **percentiles,
        "mean": sum(deltas) / len(deltas) if deltas else None,
        "sample_count": len(deltas),
    }


def _runtime_timing(
    decisions: list[dict[str, object]],
) -> dict[str, object]:
    keys = (
        "observe",
        "read_pools",
        "read_enemy_prefix",
        "read_enemy_issue_prefix",
        "decode_pools",
        "corridor_bookkeeping",
        "local_plan",
        "local_plan_initial",
        "issue_enemy_recertificate",
        "input",
        "before_trace",
        "previous_trace",
        "previous_iteration",
    )
    result = {}
    for key in keys:
        values = [
            float(timing[key])
            for row in decisions
            if isinstance((timing := row.get("timing_ms")), dict)
            and timing.get(key) is not None
        ]
        if values:
            result[key] = _percentiles(values)
    return result


def _enemy_sensor_summary(
    decisions: list[dict[str, object]],
) -> dict[str, object] | None:
    valid_rows = []
    for row in decisions:
        timing = row.get("timing_ms")
        if not isinstance(timing, dict) or timing.get("read_enemy_pool") is None:
            continue
        source_value = row.get("enemy_body_snapshot_frame", 0)
        if source_value is None:
            continue
        source_frame = int(source_value)
        age = int(row["frame"]) - source_frame
        if source_frame <= 0 or age < 0:
            continue
        valid_rows.append((row, source_frame, age, timing))
    if not valid_rows:
        return None

    snapshots: dict[int, float] = {}
    for _row, source_frame, _age, timing in valid_rows:
        snapshots.setdefault(source_frame, float(timing["read_enemy_pool"]))
    source_frames = sorted(snapshots)
    intervals = [
        right - left
        for left, right in zip(source_frames, source_frames[1:])
        if 0 < right - left < 120
    ]
    body_counts = [
        int(row.get("active_enemy_bodies", 0))
        for row, _source, _age, _timing in valid_rows
    ]
    contact_enabled_counts = [
        int(
            row.get(
                "enemy_body_contact_enabled_count",
                row.get("active_enemy_bodies", 0),
            )
        )
        for row, _source, _age, _timing in valid_rows
    ]
    anticipatory_counts = [
        int(row.get("enemy_body_anticipatory_count", 0))
        for row, _source, _age, _timing in valid_rows
    ]
    dormant_counts = [
        int(row.get("enemy_body_dormant_count", 0))
        for row, _source, _age, _timing in valid_rows
    ]
    extended_bodies = [
        body
        for row, _source, _age, _timing in valid_rows
        for body in row.get("enemy_bodies", ())
        if isinstance(body, list) and len(body) >= 11
    ]
    world_speeds = [
        max(abs(float(body[3])), abs(float(body[4])))
        for body in extended_bodies
    ]
    internal_speeds = [
        max(
            abs(float(body[9] or 0.0)),
            abs(float(body[10] or 0.0)),
        )
        for body in extended_bodies
    ]
    motion_disagreements = [
        max(
            abs(float(body[3]) - float(body[9] or 0.0)),
            abs(float(body[4]) - float(body[10] or 0.0)),
        )
        for body in extended_bodies
    ]
    operational_ages = [
        age for _row, _source, age, _timing in valid_rows if age < 120
    ]
    return {
        "decision_count_with_snapshot": len(valid_rows),
        "snapshot_count": len(snapshots),
        "snapshot_age_frames": _percentiles(operational_ages),
        "snapshot_age_discontinuity_count": (
            len(valid_rows) - len(operational_ages)
        ),
        "snapshot_interval_frames": _percentiles(intervals),
        "capture_read_ms": _percentiles(snapshots.values()),
        "decision_count_with_active_bodies": sum(
            count > 0 for count in body_counts
        ),
        "max_active_bodies": max(body_counts, default=0),
        "decision_count_with_contact_enabled_bodies": sum(
            count > 0 for count in contact_enabled_counts
        ),
        "max_contact_enabled_bodies": max(
            contact_enabled_counts,
            default=0,
        ),
        "decision_count_with_anticipatory_bodies": sum(
            count > 0 for count in anticipatory_counts
        ),
        "max_anticipatory_bodies": max(anticipatory_counts, default=0),
        "decision_count_with_dormant_bodies": sum(
            count > 0 for count in dormant_counts
        ),
        "max_dormant_bodies": max(dormant_counts, default=0),
        "observed_world_motion_sample_count": len(extended_bodies),
        "observed_world_speed": _percentiles(world_speeds),
        "internal_component_speed": _percentiles(internal_speeds),
        "world_internal_motion_disagreement": _percentiles(
            motion_disagreements
        ),
        "world_internal_motion_disagreement_over_1px_count": sum(
            value > 1.0 for value in motion_disagreements
        ),
    }


def _issue_enemy_guard_summary(
    decisions: list[dict[str, object]],
) -> dict[str, object] | None:
    guards = [
        row["issue_time_enemy_guard"]
        for row in decisions
        if isinstance(row.get("issue_time_enemy_guard"), dict)
    ]
    if not guards:
        return None
    changes = [
        str(change)
        for guard in guards
        for change in guard.get("changes", ())
    ]
    transactions = [
        transaction
        for guard in guards
        if isinstance((transaction := guard.get("transaction")), dict)
    ]
    return {
        "observation_count": len(guards),
        "changed_observation_count": sum(
            bool(guard.get("changes")) for guard in guards
        ),
        "recertified_count": sum(
            bool(guard.get("recertified")) for guard in guards
        ),
        "action_override_count": sum(
            str(guard.get("planned_action_before_guard"))
            != str(guard.get("action_after_guard"))
            for guard in guards
        ),
        "transaction_count": len(transactions),
        "selection_reason_counts": dict(
            Counter(
                str(transaction.get("selection_reason"))
                for transaction in transactions
            )
        ),
        "planned_action_preserved_count": sum(
            str(transaction.get("planned_action"))
            == str(transaction.get("selected_action"))
            for transaction in transactions
        ),
        "fresh_global_intersection_count": sum(
            bool(transaction.get("global_constraint_applicable"))
            and bool(transaction.get("fresh_global_intersection"))
            for transaction in transactions
        ),
        "global_constraint_relaxation_count": sum(
            bool(transaction.get("global_constraint_relaxed"))
            for transaction in transactions
        ),
        "fresh_global_empty_relaxation_count": sum(
            bool(transaction.get("global_constraint_applicable"))
            and bool(transaction.get("global_constraint_relaxed"))
            for transaction in transactions
        ),
        "inherited_constraint_relaxation_count": sum(
            not bool(transaction.get("global_constraint_applicable"))
            and bool(transaction.get("global_constraint_relaxed"))
            for transaction in transactions
        ),
        "silent_outside_global_count": sum(
            bool(
                transaction.get(
                    "selected_outside_global_without_relaxation"
                )
            )
            for transaction in transactions
        ),
        "observation_count_with_anticipatory_bodies": sum(
            int(guard.get("anticipatory_count", 0)) > 0
            for guard in guards
        ),
        "max_anticipatory_bodies": max(
            (
                int(guard.get("anticipatory_count", 0))
                for guard in guards
            ),
            default=0,
        ),
        "observation_count_with_dormant_bodies": sum(
            int(guard.get("dormant_count", 0)) > 0
            for guard in guards
        ),
        "max_dormant_bodies": max(
            (
                int(guard.get("dormant_count", 0))
                for guard in guards
            ),
            default=0,
        ),
        "change_kind_counts": dict(
            Counter(change.split(":", 1)[0] for change in changes)
        ),
        "read_ms": _percentiles(
            float(guard.get("read_ms", 0.0)) for guard in guards
        ),
        "recertificate_ms": _percentiles(
            float(guard.get("recertificate_ms", 0.0))
            for guard in guards
            if bool(guard.get("recertified"))
        ),
    }


def _spell_owner_guard_summary(
    decisions: list[dict[str, object]],
) -> dict[str, object] | None:
    """Retain compact evidence for the synchronous spell-owner observation."""

    rows = [
        (row, guard)
        for row in decisions
        if isinstance((guard := row.get("spell_enemy_body_guard")), dict)
    ]
    if not rows:
        return None

    observed = [
        (row, guard)
        for row, guard in rows
        if isinstance(guard.get("body"), list) and guard["body"]
    ]
    pointer_counts: Counter[int] = Counter()
    per_spell: dict[str, Counter[str]] = {}
    outside_async_pool_count = 0
    for row, guard in observed:
        body = guard["body"]
        pointer = int(body[0])
        pointer_counts[pointer] += 1
        offset = pointer - ENEMY_POOL_BASE
        covered = (
            0 <= offset < ENEMY_POOL_SIZE * ENEMY_STRIDE
            and offset % ENEMY_STRIDE == 0
        )
        if not covered:
            outside_async_pool_count += 1
        spell = row.get("spell")
        spell_id = (
            str(spell.get("spell_id"))
            if isinstance(spell, dict) and spell.get("spell_id") is not None
            else "unknown"
        )
        counts = per_spell.setdefault(spell_id, Counter())
        counts["observation_count"] += 1
        counts["contact_enabled_count"] += bool(guard.get("contact_enabled"))
        counts["anticipatory_count"] += bool(guard.get("anticipatory"))

    return {
        "row_count": len(rows),
        "observation_count": len(observed),
        "error_count": sum(bool(guard.get("error")) for _row, guard in rows),
        "contact_enabled_count": sum(
            bool(guard.get("contact_enabled")) for _row, guard in observed
        ),
        "anticipatory_count": sum(
            bool(guard.get("anticipatory")) for _row, guard in observed
        ),
        "outside_async_pool_count": outside_async_pool_count,
        "pointer_counts": {
            f"0x{pointer:08X}": count
            for pointer, count in sorted(pointer_counts.items())
        },
        "per_spell": {
            spell_id: dict(sorted(counts.items()))
            for spell_id, counts in sorted(per_spell.items())
        },
    }


def _terminal_threat_summary(
    decisions: list[dict[str, object]],
) -> dict[str, object] | None:
    rows = [
        row["terminal_threat"]
        for row in decisions
        if isinstance(row.get("terminal_threat"), dict)
        and row["terminal_threat"]
    ]
    if not rows:
        return None
    clearances = [
        float(row["min_clearance"])
        for row in rows
        if float(row.get("min_clearance", 9999.0)) < 9999.0
    ]
    horizons = Counter(int(row.get("horizon_frames", 0)) for row in rows)
    return {
        "decision_count": len(rows),
        "mode_counts": dict(
            sorted(Counter(str(row.get("mode", "unknown")) for row in rows).items())
        ),
        "horizon_counts": {
            str(key): horizons[key] for key in sorted(horizons)
        },
        "collision_warning_count": sum(
            int(row.get("collisions", 0)) > 0 for row in rows
        ),
        "constraint_relaxed_count": sum(
            bool((decision.get("robust_control") or {}).get(
                "viability_constraint_relaxed"
            ))
            for decision in decisions
        ),
        "clearance_below_item_safety_count": sum(
            float(row.get("min_clearance", 9999.0))
            < TERMINAL_THREAT_SAFETY_CLEARANCE
            for row in rows
        ),
        "minimum_clearance": _percentiles(clearances),
    }


def _action_hold_summary(
    decisions: list[dict[str, object]],
) -> dict[str, object]:
    values = [int(row["action_hold_frames"]) for row in decisions]
    counts = Counter(values)
    spell_50 = [
        int(row["action_hold_frames"])
        for row in decisions
        if isinstance(row.get("spell"), dict)
        and bool(row["spell"].get("active"))
        and int(row["spell"].get("spell_id", -1)) == 50
    ]
    all_stats = _percentiles(values) or {
        "median": None,
        "p95": None,
        "max": None,
    }
    spell_50_stats = _percentiles(spell_50) or {
        "median": None,
        "p95": None,
        "max": None,
    }
    return {
        "all": {
            **all_stats,
            "counts": {str(key): counts[key] for key in sorted(counts)},
        },
        "active_spell_50": {
            **spell_50_stats,
            "counts": {
                str(key): count
                for key, count in sorted(Counter(spell_50).items())
            },
        },
    }


def _control_delay_summary(
    decisions: list[dict[str, object]],
) -> dict[str, object]:
    values = [int(row["control_delay_frames"]) for row in decisions]
    counts = Counter(values)
    stats = _percentiles(values) or {
        "median": None,
        "p95": None,
        "max": None,
    }
    return {
        **stats,
        "counts": {str(key): counts[key] for key in sorted(counts)},
    }


def _adaptive_control_summary(
    decisions: list[dict[str, object]],
) -> dict[str, object]:
    supports = Counter(
        ",".join(str(value) for value in row["control_delay_candidates"])
        for row in decisions
        if row["control_delay_candidates"]
    )
    robust_rows = [
        row["robust_control"]
        for row in decisions
        if isinstance(row.get("robust_control"), dict)
        and row["robust_control"]
    ]
    estimator_rows = [
        row["control_delay_estimator"]
        for row in decisions
        if isinstance(row.get("control_delay_estimator"), dict)
        and row["control_delay_estimator"]
    ]
    clearances = [
        float(robust["min_clearance"])
        for robust in robust_rows
        if robust.get("min_clearance") is not None
    ]
    return {
        "support_counts": {
            key: supports[key] for key in sorted(supports)
        },
        "robust_certificate_count": len(robust_rows),
        "robust_override_count": sum(
            bool(robust.get("override")) for robust in robust_rows
        ),
        "robust_collision_prediction_count": sum(
            int(robust.get("worst_collisions", 0)) > 0
            for robust in robust_rows
        ),
        "robust_negative_clearance_count": sum(
            float(robust.get("min_clearance", 9999.0)) < 0.0
            for robust in robust_rows
        ),
        "fresh_prefix_filtered_count": sum(
            bool(robust.get("viability_fresh_prefix_filtered"))
            for robust in robust_rows
        ),
        "fresh_prefix_relaxed_count": sum(
            bool(robust.get("viability_fresh_prefix_relaxed"))
            for robust in robust_rows
        ),
        "robust_min_clearance": _percentiles(clearances),
        "guard_active_decision_count": sum(
            bool(estimator.get("guard_active"))
            for estimator in estimator_rows
        ),
        "learned_end_to_end_sample_max": max(
            (
                int(estimator.get("end_to_end_samples", 0))
                for estimator in estimator_rows
            ),
            default=0,
        ),
        "overrun_max": max(
            (
                int(estimator.get("overruns", 0))
                for estimator in estimator_rows
            ),
            default=0,
        ),
        "censored_max": max(
            (
                int(estimator.get("censored", 0))
                for estimator in estimator_rows
            ),
            default=0,
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
    safe_counts = [
        int(query.get("safe_action_count", 0)) for query in available
    ]
    selected_repairs = [
        int(query.get("selected_repair_volume", 0))
        for query in available
    ]
    selected_recovery_distances = [
        float(query["selected_recovery_distance"])
        for query in available
        if query.get("selected_recovery_distance") is not None
    ]
    selected_control_reserve_deficits = [
        float(row["robust_control"]["viability_control_reserve_deficit"])
        for row in decisions
        if isinstance(row.get("robust_control"), dict)
        and bool(
            row["robust_control"].get(
                "viability_control_reserve_valid",
                True,
            )
        )
        and row["robust_control"].get(
            "viability_recovery_distance"
        ) is not None
        and row["robust_control"].get(
            "viability_control_reserve_deficit"
        ) is not None
    ]
    ages = [int(query.get("age", 0)) for query in queries]
    planning_modes = Counter(
        str(row["corridor_planning_mode"])
        for row in decisions
        if row.get("corridor_planning_mode") is not None
    )
    policy_phase_frames = Counter(
        str(query["phase_frames"])
        for query in queries
        if query.get("phase_frames") is not None
    )
    return {
        "planning_mode_counts": {
            key: planning_modes[key] for key in sorted(planning_modes)
        },
        "policy_phase_frame_counts": {
            key: policy_phase_frames[key]
            for key in sorted(policy_phase_frames, key=int)
        },
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
        "recovery_guided_query_count": sum(
            not bool(query.get("state_viable"))
            and any(
                int(volume) > 0
                for volume in dict(query.get("repair_volumes", {})).values()
            )
            for query in available
        ),
        "recovery_selected_count": sum(
            not bool(query.get("state_viable"))
            and int(query.get("selected_repair_volume", 0)) > 0
            for query in available
        ),
        "distant_recovery_guided_query_count": sum(
            not bool(query.get("state_viable"))
            and bool(dict(query.get("recovery_distances", {})))
            for query in available
        ),
        "distant_recovery_selected_count": sum(
            not bool(query.get("state_viable"))
            and query.get("selected_recovery_distance") is not None
            for query in available
        ),
        "constrained_decision_count": sum(
            bool(row.get("robust_control", {}).get("viability_constrained"))
            for row in decisions
            if isinstance(row.get("robust_control"), dict)
        ),
        "constrained_decision_fraction": (
            sum(
                bool(
                    row.get("robust_control", {}).get(
                        "viability_constrained"
                    )
                )
                for row in decisions
                if isinstance(row.get("robust_control"), dict)
            )
            / len(decisions)
            if decisions
            else None
        ),
        "safe_action_count": _percentiles(safe_counts),
        "selected_repair_volume": _percentiles(selected_repairs),
        "selected_recovery_distance": _percentiles(
            selected_recovery_distances
        ),
        "selected_control_reserve_deficit": _percentiles(
            selected_control_reserve_deficits
        ),
        "policy_age_frames": _percentiles(ages),
    }


def _input_visibility_summary(
    decisions: list[dict[str, object]],
) -> dict[str, object]:
    transitions = []
    previous_mask = None
    for left, right in zip(decisions, decisions[1:]):
        sent_mask = int(left["mask"])
        if previous_mask is not None and sent_mask == previous_mask:
            continue
        previous_mask = sent_mask
        current = left.get("input_snapshot")
        next_input = right.get("input_snapshot")
        if not isinstance(current, dict) or not isinstance(next_input, dict):
            continue
        if int(current.get("current", sent_mask)) == sent_mask:
            continue
        snapshot_delta = (
            int(right["snapshot_frame"]) - int(left["frame"])
        )
        observation_delta = int(right["frame"]) - int(left["frame"])
        if not (
            0 < snapshot_delta < 120
            and 0 < observation_delta < 120
        ):
            continue
        transitions.append(
            {
                "visible": int(next_input.get("current", -1)) == sent_mask,
                "snapshot_delta": snapshot_delta,
                "observation_delta": observation_delta,
            }
        )
    visible = [row for row in transitions if row["visible"]]
    return {
        "interpretation": (
            "Heuristic SendInput-to-observation evidence. Output transitions "
            "already equal to the current game input are excluded as "
            "ambiguous; visibility means the next decision snapshot reports "
            "the newly sent mask."
        ),
        "unambiguous_transition_count": len(transitions),
        "visible_on_next_observation_count": len(visible),
        "visible_on_next_observation_fraction": (
            len(visible) / len(transitions) if transitions else None
        ),
        "visible_snapshot_delta_frames": _percentiles(
            int(row["snapshot_delta"]) for row in visible
        ),
        "visible_observation_delta_frames": _percentiles(
            int(row["observation_delta"]) for row in visible
        ),
    }


def _behavior_slice(
    rows: list[dict[str, object]],
) -> dict[str, object]:
    if not rows:
        return {"sample_count": 0}
    slacks = [
        float(row["corridor_slack"])
        for row in rows
        if row["corridor_slack"] is not None
    ]
    count = len(rows)
    recovery_guided = 0
    recovery_selected = 0
    distant_recovery_guided = 0
    distant_recovery_selected = 0
    control_reserve_deficits = []
    for row in rows:
        robust_control = row.get("robust_control")
        if (
            isinstance(robust_control, dict)
            and robust_control.get(
                "viability_control_reserve_deficit"
            ) is not None
        ):
            control_reserve_deficits.append(
                float(
                    robust_control[
                        "viability_control_reserve_deficit"
                    ]
                )
            )
        viability = row.get("viability")
        if not isinstance(viability, dict) or bool(
            viability.get("state_viable")
        ):
            continue
        repair_volumes = viability.get("repair_volumes", {})
        if isinstance(repair_volumes, dict) and any(
            int(volume) > 0 for volume in repair_volumes.values()
        ):
            recovery_guided += 1
        if int(viability.get("selected_repair_volume", 0)) > 0:
            recovery_selected += 1
        recovery_distances = viability.get("recovery_distances", {})
        if isinstance(recovery_distances, dict) and recovery_distances:
            distant_recovery_guided += 1
        if viability.get("selected_recovery_distance") is not None:
            distant_recovery_selected += 1
    return {
        "sample_count": count,
        "fast_fraction": sum(
            "_fast" in str(row["action"]) for row in rows
        )
        / count,
        "focused_fraction": sum(
            bool(int(row["mask"]) & 0x04) for row in rows
        )
        / count,
        "bottom_8px_fraction": sum(
            float(row["player"]["y"]) >= 424.0 for row in rows
        )
        / count,
        "nonpositive_pipeline_fraction": sum(
            float(row["pipeline_clearance"]) <= 0.0 for row in rows
        )
        / count,
        "negative_corridor_slack_fraction": (
            sum(slack < 0.0 for slack in slacks) / len(slacks)
            if slacks
            else None
        ),
        "action_lag_over_model_fraction": sum(
            int(row["action_lag"]) > int(row["control_delay_frames"])
            for row in rows
        )
        / count,
        "recovery_guided_fraction": recovery_guided / count,
        "recovery_selected_fraction": recovery_selected / count,
        "distant_recovery_guided_fraction": (
            distant_recovery_guided / count
        ),
        "distant_recovery_selected_fraction": (
            distant_recovery_selected / count
        ),
        "control_reserve_deficit_mean": (
            statistics.mean(control_reserve_deficits)
            if control_reserve_deficits
            else None
        ),
        "positive_control_reserve_deficit_fraction": (
            sum(value > 1e-6 for value in control_reserve_deficits)
            / len(control_reserve_deficits)
            if control_reserve_deficits
            else None
        ),
    }


def _behavior_context(
    decisions: list[dict[str, object]],
    deaths: list[dict[str, object]],
) -> dict[str, object]:
    death_frames = [int(death["frame"]) for death in deaths]
    alive = [
        row for row in decisions if int(row["player"]["phase"]) == 0
    ]

    def prehit(row: dict[str, object]) -> bool:
        frame = int(row["frame"])
        return any(
            0 <= death_frame - frame <= 60
            for death_frame in death_frames
        )

    def spell_50(row: dict[str, object]) -> bool:
        spell = row.get("spell")
        return (
            isinstance(spell, dict)
            and bool(spell.get("active"))
            and int(spell.get("spell_id", -1)) == 50
        )

    prehit_rows = [row for row in alive if prehit(row)]
    other_rows = [row for row in alive if not prehit(row)]
    spell_50_rows = [row for row in alive if spell_50(row)]
    return {
        "alive_all": _behavior_slice(alive),
        "alive_preceding_hit_60f": _behavior_slice(prehit_rows),
        "alive_outside_preceding_hit_60f": _behavior_slice(other_rows),
        "spell_50_alive_all": _behavior_slice(spell_50_rows),
        "spell_50_alive_preceding_hit_60f": _behavior_slice(
            [row for row in spell_50_rows if prehit(row)]
        ),
        "spell_50_alive_other": _behavior_slice(
            [row for row in spell_50_rows if not prehit(row)]
        ),
    }


def _spell_phase_summary(
    decisions: list[dict[str, object]],
    deaths: list[dict[str, object]],
) -> list[dict[str, object]]:
    rows_by_key: dict[str, list[dict[str, object]]] = {}
    spell_names: dict[str, str | None] = {}
    for row in decisions:
        spell = row.get("spell")
        if (
            isinstance(spell, dict)
            and bool(spell.get("active"))
            and spell.get("spell_id") is not None
        ):
            key = str(int(spell["spell_id"]))
            name = (
                str(spell["spell_name"])
                if spell.get("spell_name") is not None
                else None
            )
        else:
            key = "nonspell"
            name = None
        rows_by_key.setdefault(key, []).append(row)
        if name is not None:
            spell_names[key] = name

    death_frames: dict[str, list[int]] = {}
    for death in deaths:
        spell = death["spell_attribution"]
        spell_id = spell.get("spell_id")
        key = str(int(spell_id)) if spell_id is not None else "nonspell"
        death_frames.setdefault(key, []).append(int(death["frame"]))
        if spell.get("spell_name") is not None:
            spell_names[key] = str(spell["spell_name"])

    def sort_key(key: str) -> tuple[int, int]:
        return (0, -1) if key == "nonspell" else (1, int(key))

    result = []
    for key in sorted(rows_by_key, key=sort_key):
        rows = rows_by_key[key]
        alive = [
            row for row in rows if int(row["player"]["phase"]) == 0
        ]
        viability = _robust_viability_summary(rows)
        result.append(
            {
                "phase_key": key,
                "spell_id": None if key == "nonspell" else int(key),
                "spell_name": spell_names.get(key),
                "decision_count": len(rows),
                "alive_decision_count": len(alive),
                "hit_count": len(death_frames.get(key, [])),
                "hit_frames": death_frames.get(key, []),
                "max_active_bullets": max(
                    int(row["active_bullets"]) for row in rows
                ),
                "max_active_lasers": max(
                    int(row["active_lasers"]) for row in rows
                ),
                "behavior_alive": _behavior_slice(alive),
                "decision_cadence_frames": _decision_cadence(rows),
                "runtime_timing_ms": _runtime_timing(rows),
                "robust_viability": viability,
                "planner_consistency": _planner_consistency_summary(rows),
            }
        )
    return result


def build_dossier(
    *,
    run_id: str,
    trace: PracticeTrace,
) -> dict[str, object]:
    decisions = list(trace.decisions)
    run_difficulty = run_id.split("_", 1)[0].lower()
    case_prefix = (
        _case_prefix_for_difficulty(run_difficulty)
        if run_difficulty
        in {"easy", "normal", "hard", "lunatic", "extra"}
        else "LUN"
    )
    deaths = _death_ledger(decisions, case_prefix=case_prefix)
    _promote_enemy_body_candidates(deaths)
    no_bomb = _no_bomb_verification(
        decisions,
        trace.controller_configs,
    )
    if not no_bomb["passed"]:
        raise ValueError("hard no-Bomb invariant failed")

    for index, death in enumerate(deaths):
        death["sample_role"] = (
            "canonical_fresh_attempt_causal_sample"
            if index == 0
            else "post_respawn_discovery_sample"
        )
        death["bomb_input_verified_absent"] = True

    stage = int(decisions[0]["stage_route_index"])
    cause_counts = Counter(
        str(death["primary_cause_class"]) for death in deaths
    )
    planner_failure_counts = Counter(
        str(death["planner_failure_class"]) for death in deaths
    )
    contributor_counts = Counter(
        factor
        for death in deaths
        for factor in death["contributing_factors"]
    )
    spell_counts = Counter(
        (
            str(death["spell_attribution"]["spell_id"])
            if death["spell_attribution"]["spell_id"] is not None
            else "nonspell"
        )
        for death in deaths
    )
    first_hit = deaths[0] if deaths else None
    first_hit_frame = int(first_hit["frame"]) if first_hit else None
    first_window = (
        [
            row
            for row in decisions
            if first_hit_frame - 240 <= int(row["frame"]) <= first_hit_frame
        ]
        if first_hit_frame is not None
        else []
    )
    operational_lag_rows = [
        row for row in decisions if int(row["action_lag"]) < 120
    ]
    phase_counter_discontinuities = len(decisions) - len(
        operational_lag_rows
    )
    accepted_completion = (
        trace.end_event.get("reason") != "runtime_error"
        and trace.raw_summary is not None
        and trace.raw_summary.get("termination_reason") == "route_complete"
    )

    return {
        "schema": "th08-practice-dossier-v1",
        "run_id": run_id,
        "practice_scope": {
            "stage_route_index": stage,
            "stage_label": STAGE_ROUTE_LABELS.get(stage),
            "first_frame": int(decisions[0]["frame"]),
            "last_frame": int(decisions[-1]["frame"]),
            "observed_frame_span": (
                int(decisions[-1]["frame"]) - int(decisions[0]["frame"])
            ),
            "decision_count": len(decisions),
            "selected_frame_epoch_index": trace.frame_epoch_index,
            "frame_epoch_count": trace.frame_epoch_count,
            "end_event": trace.end_event,
            "pre_scope_decision_count_excluded": (
                trace.pre_scope_decision_count
            ),
            "post_scope_decision_count_excluded": (
                trace.post_scope_decision_count
            ),
            "scene_events": list(trace.scene_events),
            "raw_summary_is_scope_valid": (
                trace.raw_summary is not None
                and trace.frame_epoch_count == 1
                and int(trace.raw_summary.get("last_frame", -1))
                == int(decisions[-1]["frame"])
            ),
            "accepted_completion": accepted_completion,
        },
        "provenance": {
            "path": trace.path,
            "sha256": trace.sha256,
            "size_bytes": trace.size_bytes,
            "parse_errors": trace.parse_errors,
            "identity": trace.identity,
            "controller_configs": list(trace.controller_configs),
            "raw_kind_counts": trace.raw_kind_counts,
            "raw_summary": trace.raw_summary,
        },
        "control_policy": {
            "practice_rule": "hard no-Bomb",
            "verification": no_bomb,
        },
        "interpretation_policy": {
            "canonical_sample": (
                "Only the first hit of a fresh practice attempt preserves the "
                "initial position, bullets, power, and respawn history."
            ),
            "later_samples": (
                "Later hits remain useful discovery evidence, but death and "
                "thprac respawn mutate position, projectile state, Bomb stock, "
                "and Power."
            ),
        },
        "totals": {
            "death_count": len(deaths),
            "death_frames": [int(death["frame"]) for death in deaths],
            "primary_cause_counts": dict(cause_counts),
            "planner_failure_counts": dict(planner_failure_counts),
            "contributing_factor_counts": dict(contributor_counts),
            "spell_hit_counts": dict(spell_counts),
            "max_active_bullets": max(
                int(row["active_bullets"]) for row in decisions
            ),
            "max_active_lasers": max(
                int(row["active_lasers"]) for row in decisions
            ),
            "hit_contact_epoch": {
                "stable_capture_count": sum(
                    isinstance(death.get("hit_contact_observation"), dict)
                    and bool(death["hit_contact_observation"].get("stable"))
                    for death in deaths
                ),
                "stable_capture_with_enemy_body_count": sum(
                    isinstance(death.get("hit_contact_observation"), dict)
                    and bool(death["hit_contact_observation"].get("stable"))
                    and bool(
                        death["hit_contact_observation"].get("enemy_bodies")
                    )
                    for death in deaths
                ),
                "exact_enemy_body_overlap_count": sum(
                    death["observed_enemy_body_contact_candidate"] is not None
                    for death in deaths
                ),
            },
            "resources": {
                key: _resource_range(decisions, key)
                for key in ("lives", "bombs", "power")
            },
            "latency_ms": {
                "read": _percentiles(row["read_ms"] for row in decisions),
                "plan": _percentiles(row["plan_ms"] for row in decisions),
                "corridor_solver": _corridor_latency(decisions),
            },
            "decision_cadence_frames": _decision_cadence(decisions),
            "action_hold_frames": _action_hold_summary(decisions),
            "control_delay_frames": _control_delay_summary(decisions),
            "adaptive_control_delay": _adaptive_control_summary(decisions),
            "robust_viability": _robust_viability_summary(decisions),
            "planner_consistency": _planner_consistency_summary(decisions),
            "input_visibility": _input_visibility_summary(decisions),
            "runtime_timing_ms": _runtime_timing(decisions),
            "enemy_sensor": _enemy_sensor_summary(decisions),
            "issue_enemy_guard": _issue_enemy_guard_summary(decisions),
            "spell_owner_guard": _spell_owner_guard_summary(decisions),
            "terminal_threat": _terminal_threat_summary(decisions),
            "behavior_context": _behavior_context(decisions, deaths),
            "per_spell": _spell_phase_summary(decisions, deaths),
            "frame_lag": {
                "interpretation": (
                    "Values >=120 are phase-counter discontinuities and are "
                    "excluded from operational lag percentiles."
                ),
                "phase_counter_discontinuity_count": (
                    phase_counter_discontinuities
                ),
                "snapshot": _percentiles(
                    row["snapshot_lag"] for row in operational_lag_rows
                ),
                "action": _percentiles(
                    row["action_lag"] for row in operational_lag_rows
                ),
            },
        },
        "canonical_first_hit": {
            "death": first_hit,
            "preceding_240f": {
                "sample_count": len(first_window),
                "first_frame": (
                    int(first_window[0]["frame"]) if first_window else None
                ),
                "minimum_pipeline_clearance": (
                    min(
                        float(row["pipeline_clearance"])
                        for row in first_window
                    )
                    if first_window
                    else None
                ),
                "minimum_corridor_slack": (
                    min(
                        float(row["corridor_slack"])
                        for row in first_window
                        if row["corridor_slack"] is not None
                    )
                    if any(
                        row["corridor_slack"] is not None
                        for row in first_window
                    )
                    else None
                ),
            },
        },
        "death_clusters": _death_clusters(deaths),
        "deaths": deaths,
    }


def _format(value: object) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def render_markdown(dossier: dict[str, object]) -> str:
    scope = dossier["practice_scope"]
    totals = dossier["totals"]
    bomb = dossier["control_policy"]["verification"]
    canonical = dossier["canonical_first_hit"]["death"]
    canonical_cause = (
        canonical["primary_cause_class"] if canonical is not None else None
    )
    if canonical is None:
        primary_lines = [
            "No native hit edge occurred in this scoped practice trace.",
            "",
            "This is a physical no-Bomb pass for the captured scope. It does "
            "not by itself establish repeatability; retain repeated clean "
            "focused passes before promoting the phase.",
        ]
    else:
        canonical_spell = canonical["spell_attribution"]
        canonical_spell_label = (
            f"spell {canonical_spell['spell_id']} "
            f"`{canonical_spell['spell_name']}`"
            if canonical_spell["spell_id"] is not None
            else "a nonspell phase"
        )
        primary_lines = [
            f"The authoritative fresh-attempt hit is "
            f"`{canonical['case_id']}`. It occurred during "
            f"{canonical_spell_label} at player "
            f"({_format(canonical['player']['x'])}, "
            f"{_format(canonical['player']['y'])}), with "
            f"{canonical['active_bullets']} bullets and "
            f"{canonical['active_lasers']} lasers. The projectile model "
            "reported pipeline clearance "
            f"{_format(canonical['pipeline_clearance_at_hit'])}.",
            "",
        ]
    if canonical_cause == "enemy_body_contact_candidate":
        primary_explanation = (
            "This is a strong enemy-body collision candidate, not a "
            "bullet-planner miss. Static analysis proves that the active "
            "spell owner can invoke a lethal player/enemy AABB check at "
            "`0x42cf7a -> 0x42c290 -> 0x44a360`. The baseline trace records "
            "the owner pointer but not its position/contact size/flags, so "
            "exact same-frame overlap remains the next telemetry closure."
        )
    elif canonical is not None:
        primary_explanation = (
            f"The primary class is `{canonical_cause}`. This trace contains "
            "the retained hit-window geometry for that classification; later "
            "post-respawn hits remain discovery evidence rather than fresh "
            "independent trials."
        )
    else:
        primary_explanation = None
    if primary_explanation is not None:
        primary_lines.append(primary_explanation)

    stage_label = scope.get("stage_label") or (
        f"route {scope['stage_route_index']}"
    )
    lines = [
        f"# TH08 {stage_label} No-Bomb Practice Review: {dossier['run_id']}",
        "",
        "## Scope And Integrity",
        "",
        f"- Valid practice scope: `{scope['first_frame']}.."
        f"{scope['last_frame']}` ({scope['decision_count']} decisions).",
        f"- Selected frame epoch: {scope.get('selected_frame_epoch_index', 0)} "
        f"of {scope.get('frame_epoch_count', 1)}; "
        f"{scope.get('pre_scope_decision_count_excluded', 0)} earlier decisions "
        "were excluded.",
        f"- Scope terminator: `{scope['end_event']['reason']}`; "
        f"{scope['post_scope_decision_count_excluded']} reset-tail decisions "
        "were excluded.",
        "- The agent's raw summary is not scope-valid because thprac reset the "
        "manager counter before the external stop."
        if not scope["raw_summary_is_scope_valid"]
        else "- The agent's raw summary agrees with the scoped trace.",
        f"- Accepted complete practice: **"
        f"{'YES' if scope.get('accepted_completion') else 'NO'}**.",
        f"- Native hit edges: {totals['death_count']}, at "
        f"`{totals['death_frames']}`.",
        f"- Hard no-Bomb verification: **{'PASS' if bomb['passed'] else 'FAIL'}"
        f"** across {bomb['decision_count_checked']} decisions; mask/flag/"
        "action violations are all empty.",
        "",
        "Bomb-stock changes in the trace are death/respawn state changes. They "
        "are not Bomb use: every scoped input mask has bit `0x02` clear, every "
        "decision has `bomb=false`, and no action requests Bomb.",
        "",
        "## Primary Finding",
        "",
        *primary_lines,
        "",
        "## Failure Taxonomy",
        "",
        "| Cause | Hits |",
        "| --- | ---: |",
    ]
    for cause, count in sorted(
        totals["primary_cause_counts"].items(),
        key=lambda item: (-item[1], item[0]),
    ):
        lines.append(f"| `{cause}` | {count} |")
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
        lines.append(f"- `{factor}`: {count}")
    lines.extend(
        [
            "",
            "## Death Ledger",
            "",
            "| Role | Frame | Spell | Player | Active input | Bullets/lasers | "
            "Pipeline/min 240f | Pipeline/robust warning | Contact/cause | "
            "Planner failure |",
            "| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for death in dossier["deaths"]:
        spell = death["spell_attribution"]
        spell_label = (
            f"{spell['spell_id']} {spell['spell_name']}"
            if spell["spell_id"] is not None
            else "nonspell"
        )
        role = (
            "canonical"
            if death["sample_role"]
            == "canonical_fresh_attempt_causal_sample"
            else "discovery"
        )
        lines.append(
            f"| {role} | {death['frame']} | {spell_label} | "
            f"({_format(death['player']['x'])}, "
            f"{_format(death['player']['y'])}) | "
            f"`{death.get('active_input_action', death['action'])}` | "
            f"{death['active_bullets']}/{death['active_lasers']} | "
            f"{_format(death['pipeline_clearance_at_hit'])}/"
            f"{_format(death['minimum_pipeline_clearance_240f'])} | "
            f"{death['usable_pipeline_warning_lead_frames']}f/"
            f"{death.get('usable_robust_warning_lead_frames', 0)}f | "
            f"`{death['primary_cause_class']}` | "
            f"`{death['planner_failure_class']}` |"
        )
    lines.extend(
        [
            "",
            "## Per-Phase Planner Health",
            "",
            "| Phase | Hits | Decisions | Queries | Empty | Support outside | "
            "Constrained | Solves | Solve median ms | Bottom alive |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | "
            "---: | ---: |",
        ]
    )
    for phase in totals["per_spell"]:
        viability = phase["robust_viability"]
        solve_ms = viability["solve_ms"]
        phase_label = (
            "nonspell"
            if phase["spell_id"] is None
            else f"{phase['spell_id']} {phase['spell_name'] or ''}".strip()
        )
        bottom = phase["behavior_alive"].get("bottom_8px_fraction")
        lines.append(
            f"| {phase_label} | {phase['hit_count']} | "
            f"{phase['decision_count']} | {viability['query_count']} | "
            f"{viability['empty_action_set_count']} | "
            f"{viability['support_uncovered_query_count']} | "
            f"{viability['constrained_decision_count']} | "
            f"{viability['unique_solution_count']} | "
            f"{_format(solve_ms.get('median') if solve_ms else None)} | "
            f"{_format(bottom)} |"
        )
    cause_counts = totals["primary_cause_counts"]
    planner_failure_counts = totals["planner_failure_counts"]
    behavior = totals["behavior_context"]
    cadence = totals["decision_cadence_frames"]
    action_hold = totals["action_hold_frames"]
    control_delay = totals["control_delay_frames"]
    adaptive_delay = totals["adaptive_control_delay"]
    robust_viability = totals["robust_viability"]
    planner_consistency = totals.get(
        "planner_consistency",
        {
            "comparable_decision_count": 0,
            "global_winning_local_prefix_unsafe_count": 0,
            "global_losing_local_prefix_safe_count": 0,
            "selected_certified_action_local_prefix_unsafe_count": 0,
            "selected_action_outside_global_winning_set_count": 0,
        },
    )
    input_visibility = totals["input_visibility"]
    enemy_sensor = totals.get("enemy_sensor")
    issue_enemy_guard = totals.get("issue_enemy_guard")
    spell_owner_guard = totals.get("spell_owner_guard")
    terminal_threat = totals.get("terminal_threat")
    body_overlaps = sum(
        death["observed_enemy_body_contact_candidate"] is not None
        for death in dossier["deaths"]
    )
    body_overlaps_absent_at_action = sum(
        death["observed_enemy_body_contact_candidate"] is not None
        and not bool(
            death["observed_enemy_body_contact_candidate"].get(
                "present_in_action_snapshot",
                False,
            )
        )
        for death in dossier["deaths"]
    )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"- Retained witnesses classify "
            f"{cause_counts.get('observed_bullet_overlap', 0)} bullet "
            f"overlaps, {cause_counts.get('observed_laser_overlap', 0)} "
            f"laser overlaps, and {body_overlaps} exact same-epoch enemy-body "
            "overlaps; "
            f"{body_overlaps_absent_at_action} of those enemy slots were "
            "absent from the action snapshot.",
            f"- The controller decision cadence was "
            f"{_format(cadence['median'])} frames median and "
            f"{_format(cadence['p95'])} frames p95. The local plan took "
            f"{_format(totals['latency_ms']['plan']['median'])} ms median and "
            f"{_format(totals['latency_ms']['plan']['p95'])} ms p95.",
            (
                "- The full enemy sensor produced "
                f"{enemy_sensor['snapshot_count']} snapshots; capture read "
                f"time was `{enemy_sensor['capture_read_ms']}`, snapshot age "
                f"was `{enemy_sensor['snapshot_age_frames']}` frames, and "
                f"{enemy_sensor['snapshot_age_discontinuity_count']} "
                "phase-counter discontinuities were excluded; "
                f"{enemy_sensor['decision_count_with_active_bodies']} "
                "decisions retained at least one robust-union body "
                f"(maximum {enemy_sensor['max_active_bodies']}); "
                f"{enemy_sensor['decision_count_with_anticipatory_bodies']} "
                "decisions contained latent contact-disabled geometry "
                f"(maximum {enemy_sensor['max_anticipatory_bodies']}), and "
                f"{enemy_sensor['decision_count_with_dormant_bodies']} "
                "contained bounded inactive-slot memory "
                f"(maximum {enemy_sensor['max_dormant_bodies']}). "
                f"{enemy_sensor.get('observed_world_motion_sample_count', 0)} "
                "body samples retained observed world-motion estimates; "
                "world/internal speed and disagreement were "
                f"`{enemy_sensor.get('observed_world_speed')}` / "
                f"`{enemy_sensor.get('internal_component_speed')}` / "
                f"`{enemy_sensor.get('world_internal_motion_disagreement')}`."
            )
            if isinstance(enemy_sensor, dict)
            else "- No full enemy-pool sensor telemetry was present.",
            (
                "- The issue-time enemy guard retained "
                f"{issue_enemy_guard['observation_count']} observations, "
                f"detected {issue_enemy_guard['changed_observation_count']} "
                "during-plan geometry changes, recertified "
                f"{issue_enemy_guard['recertified_count']} decisions, and "
                f"overrode {issue_enemy_guard['action_override_count']} "
                "actions. Read/recertificate timing was "
                f"`{issue_enemy_guard['read_ms']}` / "
                f"`{issue_enemy_guard['recertificate_ms']}` ms; "
                f"{issue_enemy_guard['observation_count_with_anticipatory_bodies']} "
                "issue captures contained latent bodies "
                f"(maximum {issue_enemy_guard['max_anticipatory_bodies']}), "
                f"and {issue_enemy_guard['observation_count_with_dormant_bodies']} "
                "contained dormant bodies "
                f"(maximum {issue_enemy_guard['max_dormant_bodies']}). "
                f"Fresh/global transactions preserved "
                f"{issue_enemy_guard['planned_action_preserved_count']}/"
                f"{issue_enemy_guard['transaction_count']} planned actions, "
                "relaxed "
                f"{issue_enemy_guard['fresh_global_empty_relaxation_count']} "
                "fresh/global empty intersections, inherited "
                f"{issue_enemy_guard['inherited_constraint_relaxation_count']} "
                "earlier planner relaxations, "
                "and recorded "
                f"{issue_enemy_guard['silent_outside_global_count']} silent "
                "outside-global selections."
            )
            if isinstance(issue_enemy_guard, dict)
            else "- No issue-time enemy-geometry guard telemetry was present.",
            (
                "- The synchronous spell-owner guard retained "
                f"{spell_owner_guard['observation_count']} observations "
                f"({spell_owner_guard['contact_enabled_count']} contact "
                "enabled, "
                f"{spell_owner_guard['anticipatory_count']} anticipatory, "
                f"{spell_owner_guard['error_count']} errors). "
                f"{spell_owner_guard['outside_async_pool_count']} observed "
                "owners were outside the ordinary 480-slot async scan; "
                f"pointer counts were "
                f"`{spell_owner_guard['pointer_counts']}`."
            )
            if isinstance(spell_owner_guard, dict)
            else "- No synchronous spell-owner guard telemetry was present.",
            (
                "- The terminal-threat heuristic covered "
                f"{terminal_threat['decision_count']} decisions with horizon "
                f"counts `{terminal_threat['horizon_counts']}`; it reported "
                f"{terminal_threat['collision_warning_count']} collision and "
                f"{terminal_threat['clearance_below_item_safety_count']} "
                "sub-safety-clearance warnings, and relaxed "
                f"{terminal_threat['constraint_relaxed_count']} coarse "
                "constraints at clamped aliases."
            )
            if isinstance(terminal_threat, dict)
            else "- No extended terminal-threat telemetry was present.",
            "- Modeled action hold counts were "
            f"`{action_hold['all']['counts']}` overall.",
            "- Modeled uncontrollable-prefix counts were "
            f"`{control_delay['counts']}`.",
            (
                "- Adaptive delay supports were "
                f"`{adaptive_delay['support_counts']}`; "
                f"{adaptive_delay['robust_override_count']} decisions changed "
                "their nominal first action, "
                f"{adaptive_delay['learned_end_to_end_sample_max']} "
                "end-to-end transition samples were retained, and the "
                f"maximum observed overrun/censored counters were "
                f"{adaptive_delay['overrun_max']}/"
                f"{adaptive_delay['censored_max']}."
            ),
            (
                "- Robust viability supplied "
                f"{robust_viability['available_query_count']} available "
                "policy queries "
                f"({robust_viability['support_uncovered_query_count']} had "
                "new delay support outside the cached policy), constrained "
                f"{robust_viability['constrained_decision_count']} decisions, "
                "and exposed "
                f"{robust_viability['empty_action_set_count']} empty queried "
                "action sets. Recovery guidance was available/selected on "
                f"{robust_viability.get('recovery_guided_query_count', 0)}/"
                f"{robust_viability.get('recovery_selected_count', 0)} "
                "empty-kernel "
                "queries; distant-kernel guidance was available/selected on "
                f"{robust_viability.get('distant_recovery_guided_query_count', 0)}/"
                f"{robust_viability.get('distant_recovery_selected_count', 0)}. "
                "Safe-action count, selected repair-volume, selected "
                "recovery-distance, and selected control-reserve deficit "
                f"statistics were `{robust_viability['safe_action_count']}`, "
                f"`{robust_viability['selected_repair_volume']}`, "
                f"`{robust_viability.get('selected_recovery_distance')}`, "
                "and "
                f"`{robust_viability.get('selected_control_reserve_deficit')}`."
            ),
            (
                "- Queried policy phase offsets within the coarse control "
                "layer were "
                f"`{robust_viability.get('policy_phase_frame_counts', {})}`."
            ),
            (
                "- Global-horizon/local-prefix cross-tab covered "
                f"{planner_consistency['comparable_decision_count']} "
                "decisions: "
                f"{planner_consistency['global_winning_local_prefix_unsafe_count']} "
                "had a winning global state but unsafe selected prefix, "
                f"{planner_consistency['global_losing_local_prefix_safe_count']} "
                "had a losing global state but safe short prefix, "
                f"{planner_consistency['selected_certified_action_local_prefix_unsafe_count']} "
                "selected globally certified actions contradicted the fresh "
                "local prefix checker, and "
                f"{planner_consistency['selected_action_outside_global_winning_set_count']} "
                "selected actions were outside the reported winning set. "
                f"{planner_consistency.get('excluded_hazard_version_change_count', 0)} "
                "newer issue-time hazard versions and "
                f"{planner_consistency.get('excluded_deadline_hold_count', 0)} "
                "deadline-held old inputs were excluded from the aligned "
                "comparison."
            ),
            (
                "- The rolling worker produced "
                f"{robust_viability['unique_solution_count']} unique policies "
                "with solve-time statistics "
                f"`{robust_viability['solve_ms']}` and first-observed ages "
                f"`{robust_viability['first_observed_age_frames']}`. Policy "
                "status counts were "
                f"`{robust_viability['policy_status_counts']}`; "
                f"{robust_viability['decision_without_query_count']} robust-"
                "mode decisions had no query."
            ),
            "- Of "
            f"{input_visibility['unambiguous_transition_count']} unambiguous "
            "output transitions, "
            f"{input_visibility['visible_on_next_observation_count']} "
            f"({_format(input_visibility['visible_on_next_observation_fraction'])}) "
            "were already visible in the next decision snapshot; their "
            "snapshot delta had median "
            f"{_format(input_visibility['visible_snapshot_delta_frames']['median'])} "
            "frame.",
            "- Separating physical contact from planner causality gives "
            f"`{planner_failure_counts}`. Active input is the game-observed "
            "input at collision; the newly issued action on a hit row occurs "
            "after hit detection.",
            "- Robust action-set exhaustion supplied "
            f"{sum(death.get('usable_robust_warning_lead_frames', 0) > 0 for death in dossier['deaths'])} "
            "hit windows with a positive warning lead; those leads were "
            f"`{[death.get('usable_robust_warning_lead_frames', 0) for death in dossier['deaths']]}` "
            "frames.",
            "- Across all phases, bottom-eight-pixel occupancy was "
            f"{_format(behavior['alive_preceding_hit_60f'].get('bottom_8px_fraction'))} "
            "during the 60 frames preceding a hit versus "
            f"{_format(behavior['alive_outside_preceding_hit_60f'].get('bottom_8px_fraction'))} "
            "outside those windows.",
            "- Mean selected control-reserve deficit was "
            f"{_format(behavior['alive_preceding_hit_60f'].get('control_reserve_deficit_mean'))} "
            "during the 60 frames preceding a hit versus "
            f"{_format(behavior['alive_outside_preceding_hit_60f'].get('control_reserve_deficit_mean'))} "
            "outside those windows.",
            "- Soft recovery was selected on "
            f"{_format(behavior['alive_preceding_hit_60f'].get('recovery_selected_fraction'))} "
            "of alive decisions in the 60-frame pre-hit windows versus "
            f"{_format(behavior['alive_outside_preceding_hit_60f'].get('recovery_selected_fraction'))} "
            "outside; correlation alone is not a causal acceptance result.",
            "- Later hits cannot estimate an initial-stock clear rate because "
            f"Power falls from 128 to "
            f"{_format(totals['resources']['power']['end'])} after respawns. "
            "They remain valid counterexamples for geometry, latency, "
            "boundary use, and spell-specific pressure.",
        ]
    )
    if canonical_cause == "enemy_body_contact_candidate":
        lines.extend(
            [
                "",
                "## Baseline Correction Gate",
                "",
                "Add active-enemy lethal AABBs to the runtime snapshot, "
                "predictor, and corridor occupancy. The next fresh focused "
                "run must eliminate the canonical body-contact candidate "
                "without regressing the no-Bomb invariant.",
                "",
                "## Offline Correction Prepared",
                "",
                "- The live adapter now reads the active spell owner's native "
                "contact window and lowers its proven lethal AABB into local "
                "and global planners.",
                "- Runtime hit telemetry now captures the native player lethal "
                "rectangle and spell-owner AABB in a stable manager-frame "
                "epoch.",
                "- Local and global finite laser-segment clearance fields are "
                "vectorized; physical acceptance remains pending in this "
                "baseline report.",
            ]
        )
    elif robust_viability["policy_decision_count"] > 0:
        lines.extend(
            [
                "",
                "## Next Correction Gate",
                "",
                "Treat policy delivery, delay-support coverage, and viability "
                "exhaustion as separate gates. The next focused run must keep "
                "rolling-policy queries available, reduce unsupported query "
                "epochs, and preserve a non-empty action kernel before each "
                "former hit window. Compare per-phase position and warning "
                "lead, not only aggregate hit count.",
            ]
        )
    elif max(
        (int(value) for value in action_hold["all"]["counts"]),
        default=2,
    ) > 2:
        lines.extend(
            [
                "",
                "## Next Correction Gate",
                "",
                "Dynamic action hold is now physically exercised and complete "
                "loop timing is available. The next controller must model the "
                "separate actuation-delay distribution: newly injected input "
                "is usually visible one manager snapshot after SendInput, "
                "while planning cadence controls how long it remains held. "
                "The global corridor objective must also score terminal "
                "reachable volume and repair directions so a locally clear "
                "boundary cell is not accepted as a dead end.",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "## Next Correction Gate",
                "",
                "Measure complete loop, decode, trace-write, and input costs; "
                "make the MPC action-hold model follow observed controller "
                "cadence instead of assuming a fixed two frames. Separately, "
                "the global objective must value terminal escape viability so "
                "that a currently clear bottom cell is not treated as a good "
                "long-horizon component when it has no repair space.",
            ]
        )
    return "\n".join(lines)


def write_death_csv(
    path: Path,
    deaths: list[dict[str, object]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "case_id",
        "sample_role",
        "frame",
        "spell_id",
        "spell_name",
        "player_x",
        "player_y",
        "power",
        "action",
        "mask",
        "issued_action_after_hit_detection",
        "active_bullets",
        "active_lasers",
        "pipeline_clearance",
        "minimum_pipeline_clearance_240f",
        "minimum_corridor_slack_240f",
        "nearest_bullet_clearance",
        "nearest_laser_clearance",
        "primary_cause_class",
        "planner_failure_class",
        "usable_pipeline_warning_lead_frames",
        "usable_robust_warning_lead_frames",
        "usable_viability_warning_lead_frames",
        "viability_kernel_exhausted_at_frame",
        "contributing_factors",
        "bomb_input_verified_absent",
    ]
    with path.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=fields)
        writer.writeheader()
        for death in deaths:
            bullet = death["nearest_observed_bullet"]
            laser = death["nearest_observed_laser"]
            spell = death["spell_attribution"]
            writer.writerow(
                {
                    "case_id": death["case_id"],
                    "sample_role": death["sample_role"],
                    "frame": death["frame"],
                    "spell_id": spell["spell_id"],
                    "spell_name": spell["spell_name"],
                    "player_x": death["player"]["x"],
                    "player_y": death["player"]["y"],
                    "power": death["resources_at_hit"]["power"],
                    "action": death["active_input_action"],
                    "mask": death["active_input_mask"],
                    "issued_action_after_hit_detection": death[
                        "issued_action_after_hit_detection"
                    ],
                    "active_bullets": death["active_bullets"],
                    "active_lasers": death["active_lasers"],
                    "pipeline_clearance": (
                        death["pipeline_clearance_at_hit"]
                    ),
                    "minimum_pipeline_clearance_240f": (
                        death["minimum_pipeline_clearance_240f"]
                    ),
                    "minimum_corridor_slack_240f": (
                        death["minimum_corridor_slack_240f"]
                    ),
                    "nearest_bullet_clearance": (
                        bullet["aabb_clearance"] if bullet else None
                    ),
                    "nearest_laser_clearance": (
                        laser["clearance"] if laser else None
                    ),
                    "primary_cause_class": death["primary_cause_class"],
                    "planner_failure_class": death[
                        "planner_failure_class"
                    ],
                    "usable_pipeline_warning_lead_frames": death[
                        "usable_pipeline_warning_lead_frames"
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
                    "bomb_input_verified_absent": True,
                }
            )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument(
        "--frame-epoch",
        default=None,
        help="'first', 'last', or a zero-based monotone gameplay-frame epoch",
    )
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    parser.add_argument("--death-csv", type=Path, required=True)
    parser.add_argument("--regression-output", type=Path, required=True)
    args = parser.parse_args(argv)

    trace = read_practice_trace(
        args.trace,
        frame_epoch=args.frame_epoch,
    )
    dossier = build_dossier(run_id=args.run_id, trace=trace)
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
                "schema": "th08-practice-death-regressions-v1",
                "run_id": args.run_id,
                "scope": dossier["practice_scope"],
                "no_bomb_verification": dossier["control_policy"][
                    "verification"
                ],
                "case_count": len(dossier["deaths"]),
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
