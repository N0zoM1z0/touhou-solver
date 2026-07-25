#!/usr/bin/env python3
"""Benchmark feasibility-first candidate portfolios and gap refinement."""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

from benchmarks.benchmark_belief_pipeline_workspace import (
    _small_differential,
    _th08_certification_problem,
)
from touhou_control.policy_synthesis import (
    evaluate_candidate_policy_portfolio,
    refine_candidate_policy_gap,
    singleton_continuation_candidates,
)


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


def _query_reference(
    problem,
    actions,
    cadence,
    query,
    *,
    version: object,
    continuation_count: int | None,
) -> tuple[object, float]:
    arguments = {}
    if continuation_count is not None:
        arguments["continuation_actions"] = tuple(
            action.name for action in actions[:continuation_count]
        )
    with problem.build_belief_pipeline_workspace(
        policy_version=version,
        decision_frame_support=cadence,
        **arguments,
    ) as workspace:
        started = time.perf_counter()
        result = workspace.query_cell(
            policy_version=version,
            timeout_ms=10_000,
            **query,
        )
        elapsed_ms = (time.perf_counter() - started) * 1000.0
    return result, elapsed_ms


def _structured_seed(
    seed: int,
    repetitions: int,
) -> dict[str, object]:
    problem, actions, cadence, query = _th08_certification_problem(seed)
    candidates = singleton_continuation_candidates(problem)
    exact, exact_ms = _query_reference(
        problem,
        actions,
        cadence,
        query,
        version=("exact-reference", seed),
        continuation_count=None,
    )
    base, base_ms = _query_reference(
        problem,
        actions,
        cadence,
        query,
        version=("base-reference", seed),
        continuation_count=9,
    )

    early_runs = []
    full_runs = []
    dual_runs = []
    checks = []
    for repetition in range(repetitions):
        started = time.perf_counter()
        early = evaluate_candidate_policy_portfolio(
            problem=problem,
            policy_version=("early", seed, repetition),
            decision_frame_support=cadence,
            candidates=candidates,
            stop_on_feasibility=True,
            **query,
        )
        early_ms = (time.perf_counter() - started) * 1000.0
        started = time.perf_counter()
        full = evaluate_candidate_policy_portfolio(
            problem=problem,
            policy_version=("full", seed, repetition),
            decision_frame_support=cadence,
            candidates=candidates,
            stop_on_feasibility=False,
            **query,
        )
        full_ms = (time.perf_counter() - started) * 1000.0
        started = time.perf_counter()
        dual = refine_candidate_policy_gap(
            problem=problem,
            policy_version=("dual", seed, repetition),
            decision_frame_support=cadence,
            candidates=candidates,
            timeout_ms_per_lower=3000,
            timeout_ms_upper=3000,
            max_columns=6,
            **query,
        )
        dual_ms = (time.perf_counter() - started) * 1000.0

        def lower_is_bounded(result) -> bool:
            return all(
                lower_label <= exact_label
                for (_, lower_label), (_, exact_label) in zip(
                    result.action_labels,
                    exact.action_labels,
                )
            )

        run_checks = {
            "early_is_attainable_lower": lower_is_bounded(
                early.result
            ),
            "full_is_attainable_lower": lower_is_bounded(full.result),
            "dual_is_attainable_lower": lower_is_bounded(
                dual.final_lower_result
            ),
            "early_feasibility_sufficient": (
                early.feasibility_sufficient
            ),
            "dual_optimality_certified": dual.optimality_certified,
            "certified_value_matches_exact": (
                not dual.optimality_certified
                or dual.final_lower_result.state_label
                == exact.state_label
            ),
        }
        checks.extend(run_checks.values())
        early_runs.append(
            {
                "elapsed_ms": early_ms,
                "label": _label(early.result.state_label),
                "best_actions": list(early.result.best_actions),
                "completed_candidates": list(
                    early.completed_candidates
                ),
                "states": early.result.evaluated_state_count,
                "hidden_simulations": (
                    early.result.workspace_stats.hidden_simulation_count
                ),
            }
        )
        full_runs.append(
            {
                "elapsed_ms": full_ms,
                "label": _label(full.result.state_label),
                "best_actions": list(full.result.best_actions),
                "completed_candidate_count": len(
                    full.completed_candidates
                ),
                "states": full.result.evaluated_state_count,
                "hidden_simulations": (
                    full.result.workspace_stats.hidden_simulation_count
                ),
            }
        )
        dual_runs.append(
            {
                "elapsed_ms": dual_ms,
                "portfolio_label": _label(
                    dual.portfolio.result.state_label
                ),
                "final_label": _label(
                    dual.final_lower_result.state_label
                ),
                "final_best_actions": list(
                    dual.final_lower_result.best_actions
                ),
                "final_continuation_actions": list(
                    dual.final_continuation_actions
                ),
                "certified": dual.optimality_certified,
                "unresolved_actions": list(
                    dual.final_upper_certification.unresolved_actions
                ),
                "steps": [
                    {
                        "continuation_actions": list(
                            step.continuation_actions
                        ),
                        "lower_label": _label(
                            step.lower_result.state_label
                        ),
                        "target_root_action": (
                            step.target_root_action
                        ),
                        "recommended_action": (
                            step.recommendation.recommended_action
                            if step.recommendation is not None
                            else None
                        ),
                        "upper_unresolved_actions": list(
                            step.upper_certification
                            .unresolved_actions
                        ),
                    }
                    for step in dual.refinement_steps
                ],
                "checks": run_checks,
            }
        )

    return {
        "seed": seed,
        "exact": {
            "elapsed_ms": exact_ms,
            "label": _label(exact.state_label),
            "best_actions": list(exact.best_actions),
            "states": exact.evaluated_state_count,
            "hidden_simulations": (
                exact.workspace_stats.hidden_simulation_count
            ),
        },
        "base_nine": {
            "elapsed_ms": base_ms,
            "label": _label(base.state_label),
            "best_actions": list(base.best_actions),
            "states": base.evaluated_state_count,
            "hidden_simulations": (
                base.workspace_stats.hidden_simulation_count
            ),
        },
        "summary": {
            "early_feasibility_ms": _summary(
                [run["elapsed_ms"] for run in early_runs]
            ),
            "full_singleton_portfolio_ms": _summary(
                [run["elapsed_ms"] for run in full_runs]
            ),
            "dual_refinement_ms": _summary(
                [run["elapsed_ms"] for run in dual_runs]
            ),
        },
        "all_checks_pass": all(checks),
        "early_runs": early_runs,
        "full_runs": full_runs,
        "dual_runs": dual_runs,
    }


def benchmark(
    *,
    small_cases: int,
    repetitions: int,
) -> dict[str, object]:
    small = _small_differential(small_cases)
    structured = [
        _structured_seed(seed, repetitions) for seed in (0, 3)
    ]
    small_checks = (
        small["failure_count"] == 0
        and small["candidate_failure_count"] == 0
        and small["candidate_bound_violation_count"] == 0
        and small["portfolio_bound_violation_count"] == 0
        and small["upper_failure_count"] == 0
        and small["certification_failure_count"] == 0
        and small["bound_violation_count"] == 0
    )
    return {
        "schema": "th08.dual_bound_policy_synthesis_benchmark.v1",
        "contract": (
            "candidate proposals gain authority only after exact "
            "non-clairvoyant universal verification; full-horizon lower "
            "feasibility may stop without unrestricted optimality"
        ),
        "small_differential": small,
        "small_checks_pass": small_checks,
        "structured": structured,
        "all_checks_pass": (
            small_checks
            and all(case["all_checks_pass"] for case in structured)
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--small-cases", type=int, default=128)
    parser.add_argument("--repetitions", type=int, default=5)
    arguments = parser.parse_args()
    report = benchmark(
        small_cases=arguments.small_cases,
        repetitions=arguments.repetitions,
    )
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
