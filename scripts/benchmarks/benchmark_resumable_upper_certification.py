#!/usr/bin/env python3
"""Measure resumable threshold certification on a hard TH08-shaped root."""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

from benchmarks.benchmark_belief_pipeline_workspace import (
    _th08_certification_problem,
)


def _summary(values: list[float]) -> dict[str, float]:
    ordered = sorted(values)
    return {
        "median": statistics.median(ordered),
        "p95": ordered[int(0.95 * (len(ordered) - 1))],
        "max": max(ordered),
    }


def _certificate(
    workspace,
    *,
    version: str,
    lower_bound,
    query: dict[str, object],
    timeout_ms: int,
) -> tuple[object, float]:
    started = time.perf_counter()
    result = workspace.certify_upper_bound(
        policy_version=version,
        lower_bound=lower_bound,
        timeout_ms=timeout_ms,
        **query,
    )
    return result, (time.perf_counter() - started) * 1000.0


def _build_upper(problem, cadence, version: str):
    return problem.build_belief_pipeline_workspace(
        policy_version=version,
        decision_frame_support=cadence,
        reveal_remaining_delay=True,
    )


def _result_record(result, elapsed_ms: float) -> dict[str, object]:
    stats = result.workspace_stats
    return {
        "elapsed_ms": elapsed_ms,
        "deadline_expired": result.deadline_expired,
        "unresolved_actions": list(result.unresolved_actions),
        "memoized_states": stats.memoized_state_count,
        "new_states": stats.new_state_count,
        "memo_hits": stats.memo_hit_count,
        "hidden_simulations": stats.hidden_simulation_count,
    }


def _run_one_shot(
    problem,
    cadence,
    lower_bound,
    query: dict[str, object],
    *,
    version: str,
    timeout_ms: int,
) -> dict[str, object]:
    with _build_upper(problem, cadence, version) as workspace:
        result, elapsed_ms = _certificate(
            workspace,
            version=version,
            lower_bound=lower_bound,
            query=query,
            timeout_ms=timeout_ms,
        )
    return _result_record(result, elapsed_ms)


def _run_resumable(
    problem,
    cadence,
    lower_bound,
    query: dict[str, object],
    *,
    version: str,
    slice_ms: int,
    max_slices: int,
) -> dict[str, object]:
    slices: list[dict[str, object]] = []
    with _build_upper(problem, cadence, version) as workspace:
        for _ in range(max_slices):
            result, elapsed_ms = _certificate(
                workspace,
                version=version,
                lower_bound=lower_bound,
                query=query,
                timeout_ms=slice_ms,
            )
            slices.append(_result_record(result, elapsed_ms))
            if not result.deadline_expired:
                break
    return {
        "completed": bool(slices) and not slices[-1]["deadline_expired"],
        "slice_count": len(slices),
        "total_ms": sum(float(item["elapsed_ms"]) for item in slices),
        "total_new_states": sum(
            int(item["new_states"]) for item in slices
        ),
        "total_memo_hits": sum(
            int(item["memo_hits"]) for item in slices
        ),
        "total_hidden_simulations": sum(
            int(item["hidden_simulations"]) for item in slices
        ),
        "unresolved_counts": [
            len(item["unresolved_actions"]) for item in slices
        ],
        "final_unresolved_actions": (
            slices[-1]["unresolved_actions"] if slices else []
        ),
        "slices": slices,
    }


def _run_fresh_restarts(
    problem,
    cadence,
    lower_bound,
    query: dict[str, object],
    *,
    repetition: int,
    slice_ms: int,
    attempt_count: int,
) -> dict[str, object]:
    attempts = [
        _run_one_shot(
            problem,
            cadence,
            lower_bound,
            query,
            version=f"restart-{repetition}-{attempt}",
            timeout_ms=slice_ms,
        )
        for attempt in range(attempt_count)
    ]
    return {
        "attempt_count": len(attempts),
        "total_ms": sum(float(item["elapsed_ms"]) for item in attempts),
        "total_new_states": sum(
            int(item["new_states"]) for item in attempts
        ),
        "total_hidden_simulations": sum(
            int(item["hidden_simulations"]) for item in attempts
        ),
        "unresolved_counts": [
            len(item["unresolved_actions"]) for item in attempts
        ],
        "distinct_unresolved_sets": len(
            {
                tuple(item["unresolved_actions"])
                for item in attempts
            }
        ),
        "attempts": attempts,
    }


def benchmark(
    *,
    repetitions: int,
    slice_ms: int,
    max_slices: int,
    exact_timeout_ms: int,
) -> dict[str, object]:
    problem, actions, cadence, query = _th08_certification_problem(0)
    with problem.build_belief_pipeline_workspace(
        policy_version="resumable-lower",
        decision_frame_support=cadence,
        continuation_actions=tuple(
            action.name for action in actions[:9]
        ),
    ) as lower_workspace:
        started = time.perf_counter()
        lower = lower_workspace.query_cell(
            policy_version="resumable-lower",
            timeout_ms=exact_timeout_ms,
            **query,
        )
        lower_ms = (time.perf_counter() - started) * 1000.0

    runs: list[dict[str, object]] = []
    for repetition in range(repetitions):
        exact = _run_one_shot(
            problem,
            cadence,
            lower.state_label,
            query,
            version=f"exact-{repetition}",
            timeout_ms=exact_timeout_ms,
        )
        resumable = _run_resumable(
            problem,
            cadence,
            lower.state_label,
            query,
            version=f"resumable-{repetition}",
            slice_ms=slice_ms,
            max_slices=max_slices,
        )
        service_budget_ms = (
            slice_ms * int(resumable["slice_count"])
        )
        equal_budget_one_shot = _run_one_shot(
            problem,
            cadence,
            lower.state_label,
            query,
            version=f"equal-budget-{repetition}",
            timeout_ms=service_budget_ms,
        )
        restarts = _run_fresh_restarts(
            problem,
            cadence,
            lower.state_label,
            query,
            repetition=repetition,
            slice_ms=slice_ms,
            attempt_count=int(resumable["slice_count"]),
        )
        exact_actions = set(exact["unresolved_actions"])
        slice_sets = [
            set(item["unresolved_actions"])
            for item in resumable["slices"]
        ]
        unresolved_counts = resumable["unresolved_counts"]
        runs.append(
            {
                "exact": exact,
                "resumable": resumable,
                "equal_service_budget_ms": service_budget_ms,
                "equal_budget_one_shot": equal_budget_one_shot,
                "fresh_restarts": restarts,
                "checks": {
                    "exact_completed": not exact["deadline_expired"],
                    "resumable_completed": resumable["completed"],
                    "resumable_final_matches_exact": (
                        resumable["final_unresolved_actions"]
                        == exact["unresolved_actions"]
                    ),
                    "every_slice_is_conservative": all(
                        exact_actions <= item for item in slice_sets
                    ),
                    "unresolved_count_monotone": all(
                        right <= left
                        for left, right in zip(
                            unresolved_counts,
                            unresolved_counts[1:],
                        )
                    ),
                    "unresolved_set_monotone": all(
                        right <= left
                        for left, right in zip(
                            slice_sets,
                            slice_sets[1:],
                        )
                    ),
                    "fresh_restarts_make_no_mask_progress": (
                        restarts["distinct_unresolved_sets"] == 1
                    ),
                    "fresh_restarts_stay_fully_unresolved": all(
                        count == len(actions)
                        for count in restarts["unresolved_counts"]
                    ),
                },
            }
        )

    checks = [
        bool(value)
        for run in runs
        for value in run["checks"].values()
    ]
    return {
        "schema": "th08.resumable_upper_certification_benchmark.v1",
        "contract": (
            "same immutable workspace, canonical root, bit-preserving "
            "lower threshold, and policy version may reuse only completed "
            "threshold subproblems; deadline work remains unresolved"
        ),
        "workload": {
            "seed": 0,
            "horizon": 32,
            "action_count": 17,
            "lower_continuation_action_count": 9,
            "delay_support": [1, 2, 3, 4, 5, 6],
            "cadence": list(cadence),
            "slice_ms": slice_ms,
            "max_slices": max_slices,
            "repetitions": repetitions,
            "lower_ms": lower_ms,
            "lower_label": {
                "frames": lower.state_label.guaranteed_frames,
                "margin": lower.state_label.bottleneck_margin,
            },
        },
        "all_checks_pass": all(checks),
        "summary": {
            "exact_ms": _summary(
                [float(run["exact"]["elapsed_ms"]) for run in runs]
            ),
            "resumable_total_ms": _summary(
                [float(run["resumable"]["total_ms"]) for run in runs]
            ),
            "resumable_slice_count": _summary(
                [
                    float(run["resumable"]["slice_count"])
                    for run in runs
                ]
            ),
            "equal_budget_one_shot_ms": _summary(
                [
                    float(run["equal_budget_one_shot"]["elapsed_ms"])
                    for run in runs
                ]
            ),
            "fresh_restart_total_ms": _summary(
                [
                    float(run["fresh_restarts"]["total_ms"])
                    for run in runs
                ]
            ),
        },
        "runs": runs,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--repetitions", type=int, default=5)
    parser.add_argument("--slice-ms", type=int, default=5)
    parser.add_argument("--max-slices", type=int, default=64)
    parser.add_argument("--exact-timeout-ms", type=int, default=3000)
    arguments = parser.parse_args()
    report = benchmark(
        repetitions=arguments.repetitions,
        slice_ms=arguments.slice_ms,
        max_slices=arguments.max_slices,
        exact_timeout_ms=arguments.exact_timeout_ms,
    )
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
