#!/usr/bin/env python3
"""Build an offline scoped thprac no-Bomb practice dossier."""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter
from pathlib import Path

from analysis.dossier.attribution import (
    build_death_ledger as _death_ledger,
    case_prefix_for_difficulty as _case_prefix_for_difficulty,
    cluster_deaths as _death_clusters,
)
from analysis.dossier import practice_render as _render
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
_format = _render._format
render_markdown = _render.render_markdown
write_death_csv = _render.write_death_csv
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
