"""Practice-run cadence, control, and viability summaries."""

from __future__ import annotations

from collections import Counter

from analysis.dossier.statistics import percentiles as _percentiles


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


__all__ = [
    "_action_hold_summary",
    "_adaptive_control_summary",
    "_control_delay_summary",
    "_input_visibility_summary",
    "_robust_viability_summary",
]
