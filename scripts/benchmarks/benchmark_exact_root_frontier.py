#!/usr/bin/env python3
"""Validate one-step cadence robustness and phase-sharded root prewarming."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import statistics
import time
from pathlib import Path

import numpy as np

from benchmarks.benchmark_augmented_pipeline_workspace import _results_equal
from benchmarks.benchmark_postpublished_survival import _structured_clearance
from th08_corridor_adapter import (
    TH08_CORRIDOR_CONFIG,
    TH08_VIABILITY_ACTIONS,
)
from touhou_control.query_survival import (
    PendingCommand,
    ReachablePipelineRoot,
    SurvivalQueryProblem,
    enumerate_next_decision_roots,
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


def _one_step_scalar_differential(seed_count: int) -> dict[str, object]:
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
        rng = np.random.default_rng(90_000 + seed)
        clearance = rng.uniform(
            -3.0,
            8.0,
            size=(11, 5, 5),
        ).astype(np.float32)
        delay_frames = tuple(sorted(set((0, 1, 3, seed % 6))))
        cadence_support = tuple(
            sorted(set((1 + seed % 4, 2 + (seed // 3) % 4, 4)))
        )
        config = ViabilityConfig(
            frames_per_layer=1 + (seed // 7) % 4,
            clamp_to_bounds=bool(seed % 3),
        )
        pending = (
            None
            if seed % 4 == 0
            else PendingCommand(
                actions[(seed + 1) % len(actions)].name,
                tuple(range(1, 1 + max(1, seed % 5))),
            )
        )
        start_frame = seed % 8
        arguments = {
            "x_axis": axis,
            "y_axis": axis,
            "clearance_volume": clearance,
            "actions": actions,
            "delay_frames": delay_frames,
            "config": config,
            "start_frame": start_frame,
            "row": seed % len(axis),
            "column": (seed // len(axis)) % len(axis),
            "observed_action": actions[seed % len(actions)].name,
            "pending_command": pending,
            "decision_frame_support": cadence_support,
        }
        scalar = scalar_query_local_survival(**arguments)
        problem = SurvivalQueryProblem(
            x_axis=axis,
            y_axis=axis,
            clearance_volume=clearance,
            actions=actions,
            delay_frames=delay_frames,
            nominal_delay=delay_frames[len(delay_frames) // 2],
            config=config,
        )
        with problem.build_pipeline_workspace(
            policy_version=seed,
            decision_frame_support=cadence_support,
        ) as workspace:
            started = time.perf_counter()
            native = workspace.query_cell(
                policy_version=seed,
                frame=start_frame,
                row=arguments["row"],
                column=arguments["column"],
                observed_action=arguments["observed_action"],
                pending_command=pending,
            )
            elapsed_ms.append((time.perf_counter() - started) * 1000.0)
        if not _results_equal(native, scalar):
            failures.append(seed)
    return {
        "seed_count": seed_count,
        "failure_count": len(failures),
        "failures": failures,
        "native_cold_ms": _summary(elapsed_ms),
    }


def _root_arguments(
    root: ReachablePipelineRoot,
    *,
    policy_version: str,
) -> dict[str, object]:
    return {
        "policy_version": policy_version,
        "frame": root.frame,
        "row": root.row,
        "column": root.column,
        "observed_action": root.observed_action,
        "pending_command": root.pending_command,
    }


def _local_seed_cell(
    clearance: np.ndarray,
    *,
    frame: int,
    row: int,
    column: int,
) -> tuple[int, int]:
    candidates = [
        (candidate_row, candidate_column)
        for candidate_row in range(max(0, row - 1), min(clearance.shape[1], row + 2))
        for candidate_column in range(
            max(0, column - 1),
            min(clearance.shape[2], column + 2),
        )
    ]
    return max(
        candidates,
        key=lambda cell: float(clearance[frame, cell[0], cell[1]]),
    )


def _th08_phase_shards(case_count: int) -> dict[str, object]:
    config = ViabilityConfig(
        frames_per_layer=TH08_CORRIDOR_CONFIG.frames_per_layer,
        required_clearance=TH08_CORRIDOR_CONFIG.required_clearance,
    )
    delay_frames = (1, 2, 3, 4, 5, 6)
    cadence_support = (4, 5, 6)
    cold_ms: list[float] = []
    seed_ms: list[float] = []
    specialize_ms: list[float] = []
    consume_ms: list[float] = []
    parallel_seed_wall_ms: list[float] = []
    parallel_specialize_wall_ms: list[float] = []
    failures: list[dict[str, object]] = []
    cases: list[dict[str, object]] = []

    for case_index in range(case_count):
        seed = 3 + case_index * 8
        x_axis, y_axis, clearance = _structured_clearance(seed)
        problem = SurvivalQueryProblem(
            x_axis=x_axis,
            y_axis=y_axis,
            clearance_volume=clearance,
            actions=TH08_VIABILITY_ACTIONS,
            delay_frames=delay_frames,
            nominal_delay=4,
            config=config,
        )
        row = 13 + case_index % 3
        column = 12 + case_index % 4
        roots = enumerate_next_decision_roots(
            x_axis=x_axis,
            y_axis=y_axis,
            actions=TH08_VIABILITY_ACTIONS,
            delay_frames=delay_frames,
            decision_frame_support=cadence_support,
            config=config,
            start_frame=0,
            horizon_frame=problem.horizon_frames,
            row=row,
            column=column,
            observed_action="stay",
            selected_action="down_right_fast",
            pending_command=PendingCommand("left", (1, 3, 5)),
        )
        roots_by_frame: dict[int, list[ReachablePipelineRoot]] = {}
        for root in roots:
            roots_by_frame.setdefault(root.frame, []).append(root)

        cold_results = {}
        case_cold_ms = []
        for root_index, root in enumerate(roots):
            version = f"cold-{seed}-{root_index}"
            with problem.build_pipeline_workspace(
                policy_version=version,
            ) as workspace:
                started = time.perf_counter()
                result = workspace.query_cell(
                    **_root_arguments(root, policy_version=version)
                )
                elapsed = (time.perf_counter() - started) * 1000.0
            cold_results[root] = result
            cold_ms.append(elapsed)
            case_cold_ms.append(elapsed)

        phase_seed_times: dict[str, float] = {}
        phase_specialize_times: dict[str, list[float]] = {}
        case_specialize_ms = []
        case_consume_ms = []
        early_hit_count = 0
        shards = {}
        for frame in roots_by_frame:
            version = f"phase-{seed}-{frame}"
            shards[frame] = problem.build_pipeline_workspace(
                policy_version=version,
            )
        try:
            def seed_phase(frame: int) -> tuple[int, float]:
                version = f"phase-{seed}-{frame}"
                workspace = shards[frame]
                seed_row, seed_column = _local_seed_cell(
                    clearance,
                    frame=frame,
                    row=row,
                    column=column,
                )
                started = time.perf_counter()
                workspace.query_cell(
                    policy_version=version,
                    frame=frame,
                    row=seed_row,
                    column=seed_column,
                    observed_action="stay",
                )
                return frame, (time.perf_counter() - started) * 1000.0

            started = time.perf_counter()
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=len(shards)
            ) as executor:
                seed_results = list(executor.map(seed_phase, shards))
            phase_seed_wall = (time.perf_counter() - started) * 1000.0
            parallel_seed_wall_ms.append(phase_seed_wall)
            for frame, elapsed in seed_results:
                seed_ms.append(elapsed)
                phase_seed_times[str(frame)] = elapsed

            def specialize_phase(
                frame: int,
            ) -> tuple[
                int,
                list[float],
                list[float],
                int,
                list[dict[str, object]],
            ]:
                version = f"phase-{seed}-{frame}"
                workspace = shards[frame]
                elapsed_values = []
                consume_values = []
                phase_early_hits = 0
                phase_failures = []
                for root in roots_by_frame[frame]:
                    arguments = _root_arguments(
                        root,
                        policy_version=version,
                    )
                    if workspace.lookup_cell(**arguments) is not None:
                        phase_early_hits += 1
                    root_started = time.perf_counter()
                    specialized = workspace.query_cell(**arguments)
                    elapsed_values.append(
                        (time.perf_counter() - root_started) * 1000.0
                    )
                    if not _results_equal(
                        specialized,
                        cold_results[root],
                    ):
                        phase_failures.append(
                            {
                                "seed": seed,
                                "frame": frame,
                                "root": repr(root),
                            }
                        )

                    consume_started = time.perf_counter()
                    consumed = workspace.lookup_cell(**arguments)
                    consume_values.append(
                        (time.perf_counter() - consume_started) * 1000.0
                    )
                    if consumed is None:
                        phase_failures.append(
                            {
                                "seed": seed,
                                "frame": frame,
                                "root": repr(root),
                                "reason": (
                                    "post-specialization cache miss"
                                ),
                            }
                        )
                return (
                    frame,
                    elapsed_values,
                    consume_values,
                    phase_early_hits,
                    phase_failures,
                )

            started = time.perf_counter()
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=len(shards)
            ) as executor:
                specialization_results = list(
                    executor.map(specialize_phase, shards)
                )
            phase_specialize_wall = (
                time.perf_counter() - started
            ) * 1000.0
            parallel_specialize_wall_ms.append(phase_specialize_wall)
            for (
                frame,
                elapsed_values,
                consume_values,
                phase_early_hits,
                phase_failures,
            ) in specialization_results:
                phase_specialize_times[str(frame)] = elapsed_values
                specialize_ms.extend(elapsed_values)
                case_specialize_ms.extend(elapsed_values)
                consume_ms.extend(consume_values)
                case_consume_ms.extend(consume_values)
                early_hit_count += phase_early_hits
                failures.extend(phase_failures)
        finally:
            for workspace in shards.values():
                workspace.close()

        cases.append(
            {
                "seed": seed,
                "frontier_root_count": len(roots),
                "roots_per_frame": {
                    str(frame): len(frame_roots)
                    for frame, frame_roots in roots_by_frame.items()
                },
                "early_exact_hit_count": early_hit_count,
                "cold_exact_ms": _summary(case_cold_ms),
                "phase_seed_ms": phase_seed_times,
                "specialize_ms": phase_specialize_times,
                "parallel_phase_seed_wall_ms": phase_seed_wall,
                "parallel_post_issue_specialize_wall_ms": (
                    phase_specialize_wall
                ),
                "consume_lookup_ms": _summary(case_consume_ms),
            }
        )

    return {
        "case_count": case_count,
        "failure_count": len(failures),
        "failures": failures,
        "cadence_support": list(cadence_support),
        "cold_exact_ms": _summary(cold_ms),
        "phase_seed_ms": _summary(seed_ms),
        "post_issue_specialize_ms": _summary(specialize_ms),
        "consume_lookup_ms": _summary(consume_ms),
        "parallel_phase_seed_wall_ms": _summary(parallel_seed_wall_ms),
        "parallel_post_issue_specialize_wall_ms": _summary(
            parallel_specialize_wall_ms
        ),
        "cases": cases,
    }


def benchmark(
    *,
    scalar_seeds: int,
    th08_cases: int,
) -> dict[str, object]:
    scalar = _one_step_scalar_differential(scalar_seeds)
    th08 = _th08_phase_shards(th08_cases)
    return {
        "schema": "exact-root-frontier-benchmark-v1",
        "algorithm": (
            "A public root is robust to one declared next-decision cadence "
            "support; deeper values retain the configured fixed cadence. "
            "After an action is issued, kinematic delay/cadence branches are "
            "deduplicated into exact next roots. Expensive phase skeletons "
            "can be seeded before the exact root is known, then specialized "
            "and consumed through a fail-closed lookup-only API."
        ),
        "timing_boundary": (
            "Clearance construction and workspace construction are excluded. "
            "Cold roots execute sequentially. Phase seed and post-issue "
            "specialization wall times use three concurrent phase-shard "
            "workspaces through a Python thread pool."
        ),
        "semantic_boundary": (
            "Variable cadence is adversarial only on the public root's first "
            "transition. This is a receding-horizon shadow value, not a full "
            "unbounded variable-cadence survival certificate."
        ),
        "one_step_scalar_differential": scalar,
        "th08_phase_shards": th08,
        "failure_count": scalar["failure_count"] + th08["failure_count"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--scalar-seeds", type=int, default=512)
    parser.add_argument("--th08-cases", type=int, default=5)
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
