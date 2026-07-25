#!/usr/bin/env python3
"""Benchmark the exact-phase persistent pending-input survival workspace."""

from __future__ import annotations

import argparse
import json
import math
import statistics
import time
from pathlib import Path

import numpy as np

from benchmarks.benchmark_postpublished_survival import _structured_clearance
from th08_corridor_adapter import (
    TH08_CORRIDOR_CONFIG,
    TH08_VIABILITY_ACTIONS,
)
from touhou_control.query_survival import (
    PendingCommand,
    SurvivalQueryProblem,
    query_local_survival,
    scalar_query_local_survival,
)
from touhou_control.viability import ControlAction, ViabilityConfig


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[int(0.95 * (len(ordered) - 1))]


def _summary(values: list[float]) -> dict[str, float]:
    return {
        "median": statistics.median(values),
        "p95": _p95(values),
        "max": max(values),
    }


def _margin_equal(left: float, right: float) -> bool:
    if math.isinf(left) or math.isinf(right):
        return left == right
    return abs(left - right) <= 1e-5


def _results_equal(left, right) -> bool:
    return (
        left.state_label.guaranteed_frames
        == right.state_label.guaranteed_frames
        and _margin_equal(
            left.state_label.bottleneck_margin,
            right.state_label.bottleneck_margin,
        )
        and left.best_actions == right.best_actions
        and all(
            left_name == right_name
            and left_label.guaranteed_frames
            == right_label.guaranteed_frames
            and _margin_equal(
                left_label.bottleneck_margin,
                right_label.bottleneck_margin,
            )
            for (left_name, left_label), (
                right_name,
                right_label,
            ) in zip(left.action_labels, right.action_labels)
        )
    )


def _scalar_differential(seed_count: int) -> dict[str, object]:
    axis = np.arange(5, dtype=np.float32)
    actions = (
        ControlAction("stay", 0.0, 0.0),
        ControlAction("left", -1.0, 0.0),
        ControlAction("right", 1.0, 0.0),
        ControlAction("up", 0.0, -1.0),
        ControlAction("down", 0.0, 1.0),
    )
    failures: list[int] = []
    elapsed_ms: list[float] = []
    for seed in range(seed_count):
        rng = np.random.default_rng(50_000 + seed)
        clearance = rng.uniform(
            -3.0,
            8.0,
            size=(10, 5, 5),
        ).astype(np.float32)
        delays = tuple(sorted(set((0, 1, 2, 4, seed % 6))))
        config = ViabilityConfig(
            frames_per_layer=1 + seed % 4,
            clamp_to_bounds=bool(seed % 3),
        )
        start_frame = seed % 7
        row = seed % 5
        column = (seed // 5) % 5
        observed = actions[seed % len(actions)].name
        pending = (
            None
            if seed % 4 == 0
            else PendingCommand(
                actions[(seed + 1) % len(actions)].name,
                tuple(range(1, 1 + seed % 4)),
            )
        )
        problem = SurvivalQueryProblem(
            x_axis=axis,
            y_axis=axis,
            clearance_volume=clearance,
            actions=actions,
            delay_frames=delays,
            nominal_delay=delays[len(delays) // 2],
            config=config,
        )
        scalar = scalar_query_local_survival(
            x_axis=axis,
            y_axis=axis,
            clearance_volume=clearance,
            actions=actions,
            delay_frames=delays,
            config=config,
            start_frame=start_frame,
            row=row,
            column=column,
            observed_action=observed,
            pending_command=pending,
        )
        with problem.build_pipeline_workspace(
            policy_version=seed,
        ) as workspace:
            started = time.perf_counter()
            native = workspace.query_cell(
                policy_version=seed,
                frame=start_frame,
                row=row,
                column=column,
                observed_action=observed,
                pending_command=pending,
            )
            elapsed_ms.append((time.perf_counter() - started) * 1000.0)
        if not _results_equal(native, scalar):
            failures.append(seed)
    return {
        "seed_count": seed_count,
        "failure_count": len(failures),
        "failures": failures,
        "workspace_cold_ms": _summary(elapsed_ms),
    }


def _th08_differential(case_count: int) -> dict[str, object]:
    config = ViabilityConfig(
        frames_per_layer=TH08_CORRIDOR_CONFIG.frames_per_layer,
        required_clearance=TH08_CORRIDOR_CONFIG.required_clearance,
    )
    failures: list[dict[str, int]] = []
    cases: list[dict[str, object]] = []
    old_ms: list[float] = []
    cold_ms: list[float] = []
    warm_ms: list[float] = []
    old_states: list[int] = []
    new_states: list[int] = []
    seed_count = max(1, (case_count + 4) // 5)
    completed = 0
    for seed_offset in range(seed_count):
        seed = 3 + seed_offset * 8
        x_axis, y_axis, clearance = _structured_clearance(seed)
        problem = SurvivalQueryProblem(
            x_axis=x_axis,
            y_axis=y_axis,
            clearance_volume=clearance,
            actions=TH08_VIABILITY_ACTIONS,
            delay_frames=(1, 2, 3, 4, 5, 6),
            nominal_delay=4,
            config=config,
        )
        with problem.build_pipeline_workspace(
            policy_version=seed,
        ) as workspace:
            for local_index, frame in enumerate((0, 2, 4, 6, 8)):
                if completed >= case_count:
                    break
                row = (13 + local_index * 3) % len(y_axis)
                column = (12 + local_index * 5) % len(x_axis)
                observed = TH08_VIABILITY_ACTIONS[
                    (seed + local_index) % len(TH08_VIABILITY_ACTIONS)
                ].name
                pending = PendingCommand(
                    TH08_VIABILITY_ACTIONS[
                        (seed + local_index + 3)
                        % len(TH08_VIABILITY_ACTIONS)
                    ].name,
                    (1, 2, 3, 4, 5, 6),
                )
                started = time.perf_counter()
                old = query_local_survival(
                    x_axis=x_axis,
                    y_axis=y_axis,
                    clearance_volume=clearance,
                    actions=TH08_VIABILITY_ACTIONS,
                    delay_frames=(1, 2, 3, 4, 5, 6),
                    config=config,
                    start_frame=frame,
                    row=row,
                    column=column,
                    observed_action=observed,
                    pending_command=pending,
                    backend="native",
                )
                old_elapsed = (time.perf_counter() - started) * 1000.0
                arguments = {
                    "policy_version": seed,
                    "frame": frame,
                    "row": row,
                    "column": column,
                    "observed_action": observed,
                    "pending_command": pending,
                }
                started = time.perf_counter()
                cold = workspace.query_cell(**arguments)
                cold_elapsed = (time.perf_counter() - started) * 1000.0
                started = time.perf_counter()
                warm = workspace.query_cell(**arguments)
                warm_elapsed = (time.perf_counter() - started) * 1000.0
                labels_match = (
                    _results_equal(old, cold)
                    and _results_equal(cold, warm)
                )
                if not labels_match:
                    failures.append(
                        {
                            "seed": seed,
                            "case": local_index,
                        }
                    )
                stats = cold.workspace_stats
                cases.append(
                    {
                        "seed": seed,
                        "frame": frame,
                        "row": row,
                        "column": column,
                        "labels_match": labels_match,
                        "v1_ms": old_elapsed,
                        "workspace_cold_ms": cold_elapsed,
                        "workspace_warm_ms": warm_elapsed,
                        "v1_evaluated_states": old.evaluated_state_count,
                        "workspace_new_states": stats.new_state_count,
                        "workspace_memoized_states": (
                            stats.memoized_state_count
                        ),
                        "action_upper_bound_prunes": (
                            stats.action_upper_bound_prune_count
                        ),
                        "delay_incumbent_prunes": (
                            stats.delay_incumbent_prune_count
                        ),
                        "warm_root_memo_hits": (
                            warm.workspace_stats.root_memo_hit_count
                        ),
                    }
                )
                old_ms.append(old_elapsed)
                cold_ms.append(cold_elapsed)
                warm_ms.append(warm_elapsed)
                old_states.append(old.evaluated_state_count)
                new_states.append(stats.new_state_count)
                completed += 1
    return {
        "case_count": completed,
        "failure_count": len(failures),
        "failures": failures,
        "timing_ms": {
            "v1_cold": _summary(old_ms),
            "workspace_cold_incremental": _summary(cold_ms),
            "workspace_exact_root_warm": _summary(warm_ms),
        },
        "state_count": {
            "v1_evaluated": _summary(
                [float(value) for value in old_states]
            ),
            "workspace_new": _summary(
                [float(value) for value in new_states]
            ),
        },
        "cases": cases,
    }


def benchmark(
    *,
    scalar_seeds: int,
    th08_cases: int,
) -> dict[str, object]:
    scalar = _scalar_differential(scalar_seeds)
    th08 = _th08_differential(th08_cases)
    return {
        "schema": "augmented-pipeline-workspace-benchmark-v1",
        "algorithm": (
            "Persistent sparse memo over exact frame, lattice cell, observed "
            "action, pending action, and remaining delay. Non-root states "
            "use admissible lexicographic action upper bounds and incumbent "
            "delay pruning; roots retain exact labels for every action."
        ),
        "timing_boundary": (
            "Clearance construction is excluded. Cold timings include one "
            "root query; workspace construction is excluded. Incremental "
            "TH08 timings share memo only within one immutable policy seed. "
            "Warm timings repeat the identical exact root."
        ),
        "scalar_differential": scalar,
        "th08_v1_differential": th08,
        "failure_count": (
            scalar["failure_count"] + th08["failure_count"]
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--scalar-seeds", type=int, default=512)
    parser.add_argument("--th08-cases", type=int, default=10)
    args = parser.parse_args(argv)
    if args.scalar_seeds <= 0 or args.th08_cases <= 0:
        parser.error("seed and case counts must be positive")
    report = benchmark(
        scalar_seeds=args.scalar_seeds,
        th08_cases=args.th08_cases,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    print(args.output)
    return 0 if report["failure_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
