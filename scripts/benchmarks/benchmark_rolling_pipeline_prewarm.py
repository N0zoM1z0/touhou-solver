#!/usr/bin/env python3
"""Benchmark cancellable rolling prewarm with cadence-robust exact roots."""

from __future__ import annotations

import argparse
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
from touhou_control.pipeline_prewarm import (
    LatestPipelinePrewarmScheduler,
    enumerate_continuation_seed_roots,
)
from touhou_control.query_survival import (
    PendingCommand,
    ReachablePipelineRoot,
    SurvivalQueryProblem,
    enumerate_next_decision_roots,
    scalar_query_local_survival,
)
from touhou_control.viability import ControlAction, ViabilityConfig


CADENCE_SUPPORT = (4, 5, 6)
DELAY_SUPPORT = (1, 2, 3, 4, 5, 6)
ROLLING_ACTIONS = (
    "down_right_fast",
    "left_fast",
    "up_right",
    "stay",
    "down_left_fast",
)


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[int(0.95 * (len(ordered) - 1))]


def _summary(values: list[float]) -> dict[str, float]:
    return {
        "median": statistics.median(values),
        "p95": _p95(values),
        "max": max(values),
    }


def _frontier(
    problem: SurvivalQueryProblem,
    root: ReachablePipelineRoot,
    selected_action: str,
    decision_frame_support: tuple[int, ...],
) -> tuple[ReachablePipelineRoot, ...]:
    return enumerate_next_decision_roots(
        x_axis=problem.x_axis,
        y_axis=problem.y_axis,
        actions=problem.actions,
        delay_frames=problem.delay_frames,
        decision_frame_support=decision_frame_support,
        config=problem.config,
        start_frame=root.frame,
        horizon_frame=problem.horizon_frames,
        row=root.row,
        column=root.column,
        observed_action=root.observed_action,
        selected_action=selected_action,
        pending_command=root.pending_command,
    )


def _choose_observed_root(
    roots: tuple[ReachablePipelineRoot, ...],
    previous_frame: int,
) -> ReachablePipelineRoot:
    nominal = [
        root for root in roots if root.frame == previous_frame + 5
    ]
    candidates = nominal or list(roots)
    return candidates[len(candidates) // 2]


def _scheduler_scalar_differential(
    seed_count: int,
) -> dict[str, object]:
    axis = np.arange(5, dtype=np.float32)
    actions = (
        ControlAction("stay", 0.0, 0.0),
        ControlAction("left", -1.0, 0.0),
        ControlAction("right", 1.0, 0.0),
        ControlAction("up", 0.0, -1.0),
        ControlAction("down", 0.0, 1.0),
    )
    failures = []
    seed_ms = []
    specialize_ms = []
    for seed in range(seed_count):
        rng = np.random.default_rng(120_000 + seed)
        clearance = rng.uniform(
            -2.0,
            7.0,
            size=(11, 5, 5),
        ).astype(np.float32)
        start_frame = seed % 6
        row = seed % 5
        column = (seed // 5) % 5
        clearance[start_frame, row, column] = 6.0
        config = ViabilityConfig(
            frames_per_layer=1 + seed % 4,
            clamp_to_bounds=bool(seed % 3),
        )
        delays = tuple(sorted(set((0, 1, 3, seed % 5))))
        cadence = tuple(sorted(set((1, 2 + seed % 3, 4))))
        problem = SurvivalQueryProblem(
            x_axis=axis,
            y_axis=axis,
            clearance_volume=clearance,
            actions=actions,
            delay_frames=delays,
            nominal_delay=delays[len(delays) // 2],
            config=config,
        )
        pending = (
            PendingCommand(
                actions[(seed + 1) % len(actions)].name,
                tuple(range(1, 1 + max(1, seed % 4))),
            )
            if seed % 2
            else None
        )
        root = ReachablePipelineRoot(
            frame=start_frame,
            row=row,
            column=column,
            observed_action=actions[seed % len(actions)].name,
            pending_command=pending,
        )
        expected = scalar_query_local_survival(
            x_axis=axis,
            y_axis=axis,
            clearance_volume=clearance,
            actions=actions,
            delay_frames=delays,
            config=config,
            start_frame=start_frame,
            row=row,
            column=column,
            observed_action=root.observed_action,
            pending_command=pending,
            decision_frame_support=cadence,
        )
        seeds = enumerate_continuation_seed_roots(
            problem=problem,
            public_roots=(root,),
            decision_frame_support=cadence,
        )
        try:
            scheduler = LatestPipelinePrewarmScheduler(
                worker_count=3,
                seed_timeout_ms=200,
                specialization_timeout_ms=200,
            )
            started = time.perf_counter()
            scheduler.publish(
                problem=problem,
                policy_version=seed,
                seed_roots=seeds,
                decision_frame_support=cadence,
            )
        except RuntimeError as error:
            return {
                "seed_count": seed_count,
                "failure_count": 1,
                "failures": [{"seed": seed, "error": repr(error)}],
            }
        with scheduler:
            seed_ready = scheduler.wait_for_seed(
                policy_version=seed,
                timeout=2.0,
            )
            seed_ms.append((time.perf_counter() - started) * 1000.0)
            specialize_started = time.perf_counter()
            submitted = scheduler.submit_frontier(
                policy_version=seed,
                roots=(root,),
            )
            specialized = scheduler.wait_for_frontier(
                policy_version=seed,
                timeout=2.0,
            )
            specialize_ms.append(
                (time.perf_counter() - specialize_started) * 1000.0
            )
            actual = scheduler.lookup(
                policy_version=seed,
                root=root,
            )
        if (
            not seed_ready
            or not submitted
            or not specialized
            or actual is None
            or not _results_equal(actual, expected)
            or actual.workspace_stats.new_state_count != 0
        ):
            failures.append(seed)
    return {
        "seed_count": seed_count,
        "failure_count": len(failures),
        "failures": failures,
        "seed_wall_ms": _summary(seed_ms),
        "specialization_wall_ms": _summary(specialize_ms),
    }


def _th08_rolling(case_count: int) -> dict[str, object]:
    config = ViabilityConfig(
        frames_per_layer=TH08_CORRIDOR_CONFIG.frames_per_layer,
        required_clearance=TH08_CORRIDOR_CONFIG.required_clearance,
    )
    failures = []
    cases = []
    frontier_enumeration_ms = []
    seed_enumeration_ms = []
    preparation_ms = []
    seed_ms = []
    specialize_ms = []
    lookup_ms = []
    compute_ms = []
    end_to_end_ms = []
    deadline_hit = []
    new_states = []

    for case_index in range(case_count):
        seed = 3 + case_index * 8
        x_axis, y_axis, clearance = _structured_clearance(seed)
        problem = SurvivalQueryProblem(
            x_axis=x_axis,
            y_axis=y_axis,
            clearance_volume=clearance,
            actions=TH08_VIABILITY_ACTIONS,
            delay_frames=DELAY_SUPPORT,
            nominal_delay=4,
            config=config,
        )
        root = ReachablePipelineRoot(
            frame=0,
            row=13 + case_index % 3,
            column=12 + case_index % 4,
            observed_action="stay",
            pending_command=PendingCommand("left", (1, 3, 5)),
        )
        validation = problem.build_pipeline_workspace(
            policy_version=f"validation-{seed}",
            decision_frame_support=CADENCE_SUPPORT,
        )
        scheduler = LatestPipelinePrewarmScheduler(
            worker_count=5,
            seed_timeout_ms=300,
            specialization_timeout_ms=100,
        )
        decisions = []
        try:
            for decision_index, selected_action in enumerate(
                ROLLING_ACTIONS
            ):
                if root.frame >= problem.horizon_frames:
                    break
                preparation_started = time.perf_counter()
                frontier_started = time.perf_counter()
                frontier = _frontier(
                    problem,
                    root,
                    selected_action,
                    CADENCE_SUPPORT,
                )
                frontier_elapsed = (
                    time.perf_counter() - frontier_started
                ) * 1000.0
                seed_enumeration_started = time.perf_counter()
                seeds = enumerate_continuation_seed_roots(
                    problem=problem,
                    public_roots=frontier,
                    decision_frame_support=CADENCE_SUPPORT,
                )
                seed_enumeration_elapsed = (
                    time.perf_counter() - seed_enumeration_started
                ) * 1000.0
                preparation_elapsed = (
                    time.perf_counter() - preparation_started
                ) * 1000.0
                frontier_enumeration_ms.append(frontier_elapsed)
                seed_enumeration_ms.append(seed_enumeration_elapsed)
                preparation_ms.append(preparation_elapsed)
                seed_before = len(scheduler.seed_outcomes())
                submitted_before = scheduler.snapshot().seed_submitted
                started = time.perf_counter()
                if decision_index == 0:
                    scheduler.publish(
                        problem=problem,
                        policy_version=seed,
                        seed_roots=seeds,
                        decision_frame_support=CADENCE_SUPPORT,
                    )
                    seed_submitted = True
                else:
                    seed_submitted = scheduler.extend_seeds(
                        policy_version=seed,
                        roots=seeds,
                    )
                seed_ready = (
                    seed_submitted
                    and scheduler.wait_for_seed(
                        policy_version=seed,
                        timeout=5.0,
                    )
                )
                seed_elapsed = (time.perf_counter() - started) * 1000.0
                seed_ms.append(seed_elapsed)

                specialization_started = time.perf_counter()
                frontier_submitted = scheduler.submit_frontier(
                    policy_version=seed,
                    roots=frontier,
                )
                frontier_ready = (
                    frontier_submitted
                    and scheduler.wait_for_frontier(
                        policy_version=seed,
                        timeout=3.0,
                    )
                )
                specialization_elapsed = (
                    time.perf_counter() - specialization_started
                ) * 1000.0
                specialize_ms.append(specialization_elapsed)
                compute = seed_elapsed + specialization_elapsed
                end_to_end = preparation_elapsed + compute
                compute_ms.append(compute)
                end_to_end_ms.append(end_to_end)
                physical_budget_ms = (
                    min(CADENCE_SUPPORT) * 1000.0 / 60.0
                )
                met_deadline = end_to_end <= physical_budget_ms
                deadline_hit.append(met_deadline)

                decision_failures = []
                for frontier_root in frontier:
                    lookup_started = time.perf_counter()
                    actual = scheduler.lookup(
                        policy_version=seed,
                        root=frontier_root,
                    )
                    lookup_elapsed = (
                        time.perf_counter() - lookup_started
                    ) * 1000.0
                    lookup_ms.append(lookup_elapsed)
                    expected = validation.query_cell(
                        policy_version=f"validation-{seed}",
                        frame=frontier_root.frame,
                        row=frontier_root.row,
                        column=frontier_root.column,
                        observed_action=frontier_root.observed_action,
                        pending_command=frontier_root.pending_command,
                    )
                    if (
                        actual is None
                        or not _results_equal(actual, expected)
                    ):
                        decision_failures.append(repr(frontier_root))
                outcomes = scheduler.seed_outcomes()[seed_before:]
                submitted_after = scheduler.snapshot().seed_submitted
                decision_new_states = sum(
                    outcome.new_state_count for outcome in outcomes
                )
                new_states.append(decision_new_states)
                specialization_outcomes = (
                    scheduler.specialization_outcomes()
                )
                if (
                    not seed_ready
                    or not frontier_ready
                    or decision_failures
                    or any(
                        outcome.new_state_count != 0
                        for outcome in specialization_outcomes
                    )
                ):
                    failures.append(
                        {
                            "seed": seed,
                            "decision": decision_index,
                            "seed_ready": seed_ready,
                            "frontier_ready": frontier_ready,
                            "label_failures": decision_failures,
                        }
                    )
                decisions.append(
                    {
                        "decision": decision_index,
                        "start_frame": root.frame,
                        "selected_action": selected_action,
                        "frontier_root_count": len(frontier),
                        "continuation_seed_count": len(seeds),
                        "new_seed_count": (
                            submitted_after - submitted_before
                        ),
                        "frontier_enumeration_wall_ms": frontier_elapsed,
                        "continuation_seed_enumeration_wall_ms": (
                            seed_enumeration_elapsed
                        ),
                        "preparation_wall_ms": preparation_elapsed,
                        "seed_wall_ms": seed_elapsed,
                        "specialization_wall_ms": specialization_elapsed,
                        "compute_wall_ms": compute,
                        "end_to_end_wall_ms": end_to_end,
                        "four_frame_budget_ms": physical_budget_ms,
                        "met_four_frame_budget": met_deadline,
                        "new_continuation_states": decision_new_states,
                        "specialization_new_states": sum(
                            outcome.new_state_count
                            for outcome in specialization_outcomes
                        ),
                    }
                )
                root = _choose_observed_root(frontier, root.frame)
        finally:
            scheduler.close()
            validation.close()
        cases.append({"seed": seed, "decisions": decisions})

    return {
        "case_count": case_count,
        "decision_count": len(end_to_end_ms),
        "failure_count": len(failures),
        "failures": failures,
        "frontier_enumeration_wall_ms": _summary(
            frontier_enumeration_ms
        ),
        "continuation_seed_enumeration_wall_ms": _summary(
            seed_enumeration_ms
        ),
        "preparation_wall_ms": _summary(preparation_ms),
        "seed_wall_ms": _summary(seed_ms),
        "specialization_wall_ms": _summary(specialize_ms),
        "compute_wall_ms": _summary(compute_ms),
        "end_to_end_wall_ms": _summary(end_to_end_ms),
        "lookup_ms": _summary(lookup_ms),
        "new_continuation_states": _summary(
            [float(value) for value in new_states]
        ),
        "four_frame_deadline_hit_count": sum(deadline_hit),
        "four_frame_deadline_miss_count": (
            len(deadline_hit) - sum(deadline_hit)
        ),
        "cases": cases,
    }


def _stale_replacement(case_count: int) -> dict[str, object]:
    config = ViabilityConfig(
        frames_per_layer=TH08_CORRIDOR_CONFIG.frames_per_layer,
        required_clearance=TH08_CORRIDOR_CONFIG.required_clearance,
    )
    replacement_ms = []
    new_ready_ms = []
    retired_reap_ms = []
    failures = []
    for case_index in range(case_count):
        seed = 3 + case_index * 8
        x_axis, y_axis, clearance = _structured_clearance(seed)
        problem = SurvivalQueryProblem(
            x_axis=x_axis,
            y_axis=y_axis,
            clearance_volume=clearance,
            actions=TH08_VIABILITY_ACTIONS,
            delay_frames=DELAY_SUPPORT,
            nominal_delay=4,
            config=config,
        )
        root = ReachablePipelineRoot(
            frame=0,
            row=13,
            column=12,
            observed_action="stay",
            pending_command=PendingCommand("left", (1, 3, 5)),
        )
        frontier = _frontier(
            problem,
            root,
            "down_right_fast",
            CADENCE_SUPPORT,
        )
        seeds = enumerate_continuation_seed_roots(
            problem=problem,
            public_roots=frontier,
            decision_frame_support=CADENCE_SUPPORT,
        )
        scheduler = LatestPipelinePrewarmScheduler(
            worker_count=5,
            seed_timeout_ms=300,
            specialization_timeout_ms=100,
        )
        try:
            scheduler.publish(
                problem=problem,
                policy_version=f"old-{seed}",
                seed_roots=seeds,
                decision_frame_support=CADENCE_SUPPORT,
            )
            time.sleep(0.010)
            started = time.perf_counter()
            scheduler.publish(
                problem=problem,
                policy_version=f"new-{seed}",
                seed_roots=seeds,
                decision_frame_support=CADENCE_SUPPORT,
            )
            replacement_ms.append(
                (time.perf_counter() - started) * 1000.0
            )
            reap_started = time.perf_counter()
            while (
                scheduler.snapshot().retired_generation_count
                and time.perf_counter() - reap_started < 2.0
            ):
                time.sleep(0.001)
            retired_reap_ms.append(
                (time.perf_counter() - reap_started) * 1000.0
            )
            ready = scheduler.wait_for_seed(
                policy_version=f"new-{seed}",
                timeout=5.0,
            )
            new_ready_ms.append(
                (time.perf_counter() - started) * 1000.0
            )
            snapshot = scheduler.snapshot()
            if (
                not ready
                or snapshot.policy_version != f"new-{seed}"
                or snapshot.retired_generation_count != 0
            ):
                failures.append(seed)
        finally:
            scheduler.close()
    return {
        "case_count": case_count,
        "failure_count": len(failures),
        "failures": failures,
        "replacement_call_ms": _summary(replacement_ms),
        "retired_generation_reap_ms": _summary(retired_reap_ms),
        "new_generation_seed_ready_ms": _summary(new_ready_ms),
    }


def benchmark(
    *,
    scalar_seeds: int,
    th08_cases: int,
    stale_cases: int,
) -> dict[str, object]:
    scalar = _scheduler_scalar_differential(scalar_seeds)
    rolling = _th08_rolling(th08_cases)
    stale = _stale_replacement(stale_cases)
    return {
        "schema": "rolling-pipeline-prewarm-benchmark-v1",
        "algorithm": (
            "Fixed-cadence continuation values are prewarmed in exact "
            "phase-residue shards, merged into short-lived one-transition "
            "cadence-robust root workspaces, and consumed lookup-only. "
            "Each newer policy gets a fresh executor and cooperatively "
            "cancels every older native workspace."
        ),
        "timing_boundary": (
            "Clearance construction is excluded. Frontier and continuation-"
            "seed enumeration are included in preparation and end-to-end "
            "timings. Workspace creation, native continuation expansion, memo "
            "merge, exact specialization, and lookup are included in their "
            "named measurements. Validation-oracle queries are excluded."
        ),
        "scheduler_scalar_differential": scalar,
        "th08_rolling": rolling,
        "stale_replacement": stale,
        "failure_count": (
            scalar["failure_count"]
            + rolling["failure_count"]
            + stale["failure_count"]
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--scalar-seeds", type=int, default=256)
    parser.add_argument("--th08-cases", type=int, default=5)
    parser.add_argument("--stale-cases", type=int, default=5)
    args = parser.parse_args(argv)
    if (
        args.scalar_seeds <= 0
        or args.th08_cases <= 0
        or args.stale_cases <= 0
    ):
        parser.error("all case counts must be positive")
    report = benchmark(
        scalar_seeds=args.scalar_seeds,
        th08_cases=args.th08_cases,
        stale_cases=args.stale_cases,
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
