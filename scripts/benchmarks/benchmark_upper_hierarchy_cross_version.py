#!/usr/bin/env python3
"""Measure delay-bucket upper bounds and safe cross-version proposals."""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

import numpy as np

from benchmarks.benchmark_belief_pipeline_workspace import (
    _th08_certification_problem,
)
from touhou_control.policy_synthesis import (
    evaluate_candidate_policy_portfolio,
    prioritize_candidates_from_previous_version,
    refine_candidate_policy_gap,
    singleton_continuation_candidates,
)
from touhou_control.query_survival import SurvivalQueryProblem


def _summary(values: list[float]) -> dict[str, float]:
    ordered = sorted(values)
    return {
        "median": statistics.median(ordered),
        "p95": ordered[int(0.95 * (len(ordered) - 1))],
        "max": max(ordered),
    }


def _label(label) -> dict[str, float | int]:
    return {
        "frames": label.guaranteed_frames,
        "margin": label.bottleneck_margin,
    }


def _upper_hierarchy(repetitions: int) -> dict[str, object]:
    problem, _, cadence, query = _th08_certification_problem(0)
    candidates = singleton_continuation_candidates(problem)
    portfolio = evaluate_candidate_policy_portfolio(
        problem=problem,
        policy_version="upper-hierarchy-portfolio",
        decision_frame_support=cadence,
        candidates=candidates,
        stop_on_feasibility=False,
        **query,
    )
    refined = refine_candidate_policy_gap(
        problem=problem,
        policy_version="upper-hierarchy-refined",
        decision_frame_support=cadence,
        candidates=candidates,
        max_columns=6,
        **query,
    )
    rows = []
    checks = [refined.optimality_certified]
    for lower_name, lower in (
        ("singleton_portfolio", portfolio.result.state_label),
        ("refined_exact", refined.final_lower_result.state_label),
    ):
        for width in (62, 16, 8, 4, 2, 1):
            samples = []
            unresolved = None
            certified = None
            states = []
            simulations = []
            for repetition in range(repetitions):
                version = (
                    "upper-hierarchy",
                    lower_name,
                    width,
                    repetition,
                )
                started = time.perf_counter()
                with problem.build_belief_pipeline_workspace(
                    policy_version=version,
                    decision_frame_support=cadence,
                    remaining_delay_bucket_size=width,
                ) as workspace:
                    result = workspace.certify_upper_bound(
                        policy_version=version,
                        lower_bound=lower,
                        **query,
                    )
                samples.append(
                    (time.perf_counter() - started) * 1000.0
                )
                states.append(
                    result.workspace_stats.memoized_state_count
                )
                simulations.append(
                    result.workspace_stats.hidden_simulation_count
                )
                current_unresolved = tuple(result.unresolved_actions)
                if unresolved is None:
                    unresolved = current_unresolved
                    certified = result.certified
                checks.append(current_unresolved == unresolved)
                checks.append(result.certified == certified)
            rows.append(
                {
                    "lower": lower_name,
                    "lower_label": _label(lower),
                    "bucket_width": width,
                    "elapsed_ms": _summary(samples),
                    "certified": certified,
                    "unresolved_actions": list(unresolved or ()),
                    "memoized_states": _summary(
                        [float(value) for value in states]
                    ),
                    "hidden_simulations": _summary(
                        [float(value) for value in simulations]
                    ),
                }
            )
    return {
        "all_checks_pass": all(checks),
        "rows": rows,
    }


def _cross_version(repetitions: int) -> dict[str, object]:
    previous_problem, _, cadence, query = (
        _th08_certification_problem(0)
    )
    candidates = singleton_continuation_candidates(previous_problem)
    previous = evaluate_candidate_policy_portfolio(
        problem=previous_problem,
        policy_version="cross-version-previous",
        decision_frame_support=cadence,
        candidates=candidates,
        stop_on_feasibility=False,
        **query,
    )
    prioritized = prioritize_candidates_from_previous_version(
        candidates=candidates,
        previous=previous,
    )

    clearance = np.array(
        previous_problem.clearance_volume,
        dtype=np.float32,
        copy=True,
    )
    clearance[1:] += np.float32(0.125)
    current_problem = SurvivalQueryProblem(
        x_axis=previous_problem.x_axis,
        y_axis=previous_problem.y_axis,
        clearance_volume=clearance,
        actions=previous_problem.actions,
        delay_frames=previous_problem.delay_frames,
        nominal_delay=previous_problem.nominal_delay,
        config=previous_problem.config,
    )
    samples: dict[str, list[float]] = {"default": [], "reused": []}
    completed_counts: dict[str, list[int]] = {
        "default": [],
        "reused": [],
    }
    labels: dict[str, object] = {}
    checks = []
    for repetition in range(repetitions):
        for name, ordered in (
            ("default", candidates),
            ("reused", prioritized),
        ):
            started = time.perf_counter()
            result = evaluate_candidate_policy_portfolio(
                problem=current_problem,
                policy_version=(
                    "cross-version-current",
                    name,
                    repetition,
                ),
                decision_frame_support=cadence,
                candidates=ordered,
                stop_on_feasibility=True,
                **query,
            )
            samples[name].append(
                (time.perf_counter() - started) * 1000.0
            )
            completed_counts[name].append(
                len(result.completed_candidates)
            )
            labels[name] = result.result.state_label
            checks.append(result.feasibility_sufficient)

    default_full = evaluate_candidate_policy_portfolio(
        problem=current_problem,
        policy_version="cross-version-current-default-full",
        decision_frame_support=cadence,
        candidates=candidates,
        stop_on_feasibility=False,
        **query,
    )
    reused_full = evaluate_candidate_policy_portfolio(
        problem=current_problem,
        policy_version="cross-version-current-reused-full",
        decision_frame_support=cadence,
        candidates=prioritized,
        stop_on_feasibility=False,
        **query,
    )
    checks.append(
        default_full.result.action_labels
        == reused_full.result.action_labels
    )
    return {
        "all_checks_pass": all(checks),
        "contract": (
            "Prior-version labels only rank proposers. Every current-version "
            "candidate is exactly re-solved before use."
        ),
        "clearance_change": "+0.125 on frames 1..horizon",
        "prioritized_first_candidate": prioritized[0].name,
        "default": {
            "elapsed_ms": _summary(samples["default"]),
            "completed_candidates": _summary(
                [
                    float(value)
                    for value in completed_counts["default"]
                ]
            ),
            "label": _label(labels["default"]),
        },
        "reused": {
            "elapsed_ms": _summary(samples["reused"]),
            "completed_candidates": _summary(
                [
                    float(value)
                    for value in completed_counts["reused"]
                ]
            ),
            "label": _label(labels["reused"]),
        },
        "full_portfolio_order_invariant": (
            default_full.result.action_labels
            == reused_full.result.action_labels
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--repetitions", type=int, default=7)
    arguments = parser.parse_args()
    if arguments.repetitions < 1:
        parser.error("--repetitions must be positive")
    report = {
        "schema": "upper-hierarchy-cross-version-v1",
        "upper_hierarchy": _upper_hierarchy(arguments.repetitions),
        "cross_version": _cross_version(arguments.repetitions),
    }
    report["all_checks_pass"] = bool(
        report["upper_hierarchy"]["all_checks_pass"]
        and report["cross_version"]["all_checks_pass"]
    )
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
