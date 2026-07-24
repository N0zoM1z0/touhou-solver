#!/usr/bin/env python3
"""Offline comparison of two retained practice dossiers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _reduction(before: float, after: float) -> float | None:
    if before == 0.0:
        return None
    return (before - after) / before


def _change(before: float | int, after: float | int) -> dict[str, object]:
    return {
        "baseline": before,
        "candidate": after,
        "delta": after - before,
        "reduction_fraction": _reduction(float(before), float(after)),
    }


def _mapping_count(mapping: object, key: str) -> int:
    return int(mapping.get(key, 0)) if isinstance(mapping, dict) else 0


def _phase_map(dossier: dict[str, object]) -> dict[str, dict[str, object]]:
    return {
        str(phase["phase_key"]): phase
        for phase in dossier["totals"].get("per_spell", [])
    }


def _percentile_change(
    baseline: object,
    candidate: object,
) -> dict[str, object] | None:
    if not isinstance(baseline, dict) or not isinstance(candidate, dict):
        return None
    return {
        key: _change(float(baseline[key]), float(candidate[key]))
        for key in ("median", "p95", "max")
        if baseline.get(key) is not None and candidate.get(key) is not None
    }


def _optional_mapping_change(
    baseline: dict[str, object],
    candidate: dict[str, object],
    key: str,
) -> dict[str, object]:
    before = baseline.get(key)
    after = candidate.get(key)
    if before is None or after is None:
        return {
            "baseline": before,
            "candidate": after,
            "delta": None,
            "reduction_fraction": None,
        }
    return _change(float(before), float(after))


def compare_dossiers(
    baseline: dict[str, object],
    candidate: dict[str, object],
) -> dict[str, object]:
    for name, dossier in (("baseline", baseline), ("candidate", candidate)):
        if dossier.get("schema") != "th08-practice-dossier-v1":
            raise ValueError(f"{name} has an unsupported dossier schema")

    before = baseline["totals"]
    after = candidate["totals"]
    before_robust = before.get("robust_viability", {})
    after_robust = after.get("robust_viability", {})
    before_status = before_robust.get("policy_status_counts", {})
    after_status = after_robust.get("policy_status_counts", {})

    robust_counts = {}
    for key in (
        "policy_decision_count",
        "decision_without_query_count",
        "unique_solution_count",
        "query_count",
        "available_query_count",
        "support_uncovered_query_count",
        "viable_query_count",
        "empty_action_set_count",
        "constrained_decision_count",
        "serial_worker_serviceable_count",
    ):
        robust_counts[key] = _change(
            int(before_robust.get(key, 0)),
            int(after_robust.get(key, 0)),
        )
    robust_counts["queryable_policy_decisions"] = _change(
        _mapping_count(before_status, "queryable"),
        _mapping_count(after_status, "queryable"),
    )
    robust_counts["expired_policy_decisions"] = _change(
        _mapping_count(before_status, "expired"),
        _mapping_count(after_status, "expired"),
    )

    baseline_phases = _phase_map(baseline)
    candidate_phases = _phase_map(candidate)
    per_phase = {}
    for key in sorted(
        set(baseline_phases) | set(candidate_phases),
        key=lambda value: (value != "nonspell", int(value) if value != "nonspell" else -1),
    ):
        baseline_phase = baseline_phases.get(key, {})
        candidate_phase = candidate_phases.get(key, {})
        before_phase_robust = baseline_phase.get("robust_viability", {})
        after_phase_robust = candidate_phase.get("robust_viability", {})
        before_phase_timing = baseline_phase.get("runtime_timing_ms", {})
        after_phase_timing = candidate_phase.get("runtime_timing_ms", {})
        per_phase[key] = {
            "spell_name": (
                candidate_phase.get("spell_name")
                or baseline_phase.get("spell_name")
            ),
            "hit_count": _change(
                int(baseline_phase.get("hit_count", 0)),
                int(candidate_phase.get("hit_count", 0)),
            ),
            "decision_count": _change(
                int(baseline_phase.get("decision_count", 0)),
                int(candidate_phase.get("decision_count", 0)),
            ),
            "query_count": _change(
                int(before_phase_robust.get("query_count", 0)),
                int(after_phase_robust.get("query_count", 0)),
            ),
            "empty_action_set_count": _change(
                int(before_phase_robust.get("empty_action_set_count", 0)),
                int(after_phase_robust.get("empty_action_set_count", 0)),
            ),
            "solve_ms": _percentile_change(
                before_phase_robust.get("solve_ms"),
                after_phase_robust.get("solve_ms"),
            ),
            "decision_cadence_frames": _percentile_change(
                baseline_phase.get("decision_cadence_frames"),
                candidate_phase.get("decision_cadence_frames"),
            ),
            "runtime_timing_ms": {
                timing_key: change
                for timing_key in sorted(
                    set(before_phase_timing) | set(after_phase_timing)
                )
                if (
                    change := _percentile_change(
                        before_phase_timing.get(timing_key),
                        after_phase_timing.get(timing_key),
                    )
                )
                is not None
            },
        }

    before_prehit = before.get("behavior_context", {}).get(
        "alive_preceding_hit_60f",
        {},
    )
    after_prehit = after.get("behavior_context", {}).get(
        "alive_preceding_hit_60f",
        {},
    )
    before_input = before.get("input_visibility", {})
    after_input = after.get("input_visibility", {})
    candidate_scope = candidate.get("practice_scope", {})
    return {
        "schema": "th08-practice-comparison-v2",
        "baseline_run_id": baseline["run_id"],
        "candidate_run_id": candidate["run_id"],
        "scope_compatibility": {
            "same_stage_route_index": (
                baseline.get("practice_scope", {}).get("stage_route_index")
                == candidate_scope.get("stage_route_index")
            ),
            "candidate_selected_frame_epoch_index": (
                candidate_scope.get("selected_frame_epoch_index", 0)
            ),
            "candidate_frame_epoch_count": (
                candidate_scope.get("frame_epoch_count", 1)
            ),
            "candidate_pre_scope_decisions_excluded": (
                candidate_scope.get("pre_scope_decision_count_excluded", 0)
            ),
            "candidate_raw_summary_scope_valid": bool(
                candidate_scope.get("raw_summary_is_scope_valid")
            ),
            "candidate_accepted_completion": bool(
                candidate_scope.get("accepted_completion")
            ),
        },
        "no_bomb_passed": {
            "baseline": bool(
                baseline["control_policy"]["verification"]["passed"]
            ),
            "candidate": bool(
                candidate["control_policy"]["verification"]["passed"]
            ),
        },
        "death_count": _change(
            int(before["death_count"]),
            int(after["death_count"]),
        ),
        "robust_viability": {
            "counts": robust_counts,
            "solve_ms": _percentile_change(
                before_robust.get("solve_ms"),
                after_robust.get("solve_ms"),
            ),
            "backend_counts": {
                "baseline": before_robust.get("backend_counts", {}),
                "candidate": after_robust.get("backend_counts", {}),
            },
            "solver_phase_ms": {
                "baseline": before_robust.get("solver_phase_ms", {}),
                "candidate": after_robust.get("solver_phase_ms", {}),
            },
            "serial_coverage_margin_frames": {
                "baseline": before_robust.get(
                    "serial_coverage_margin_frames"
                ),
                "candidate": after_robust.get(
                    "serial_coverage_margin_frames"
                ),
            },
        },
        "prehit_behavior": {
            key: _optional_mapping_change(before_prehit, after_prehit, key)
            for key in (
                "fast_fraction",
                "bottom_8px_fraction",
                "nonpositive_pipeline_fraction",
                "negative_corridor_slack_fraction",
                "control_reserve_deficit_mean",
                "positive_control_reserve_deficit_fraction",
            )
        },
        "input_visible_next_observation_fraction": _change(
            float(before_input.get("visible_on_next_observation_fraction", 0.0)),
            float(after_input.get("visible_on_next_observation_fraction", 0.0)),
        ),
        "per_phase": per_phase,
        "candidate_primary_cause_counts": after["primary_cause_counts"],
        "candidate_planner_failure_counts": after.get(
            "planner_failure_counts",
            {},
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args(argv)
    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
    comparison = compare_dossiers(baseline, candidate)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(comparison, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
