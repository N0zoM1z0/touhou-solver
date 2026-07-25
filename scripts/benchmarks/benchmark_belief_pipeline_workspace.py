#!/usr/bin/env python3
"""Benchmark the recursive non-clairvoyant pipeline workspace."""

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
    PipelineWorkspaceDeadlineError,
    SurvivalQueryProblem,
)
from touhou_control.variable_cadence_oracle import (
    scalar_belief_cadence_survival,
    scalar_clairvoyant_recursive_cadence_survival,
)
from touhou_control.viability import ControlAction, ViabilityConfig


def _summary(values: list[float]) -> dict[str, float]:
    ordered = sorted(values)
    return {
        "median": statistics.median(ordered),
        "p95": ordered[int(0.95 * (len(ordered) - 1))],
        "max": max(ordered),
    }


def _equal(left, right) -> bool:
    def label_equal(left_label, right_label) -> bool:
        return (
            left_label.guaranteed_frames
            == right_label.guaranteed_frames
            and (
                left_label.bottleneck_margin
                == right_label.bottleneck_margin
                if (
                    math.isinf(left_label.bottleneck_margin)
                    or math.isinf(right_label.bottleneck_margin)
                )
                else abs(
                    left_label.bottleneck_margin
                    - right_label.bottleneck_margin
                ) <= 1e-5
            )
        )

    return (
        label_equal(left.state_label, right.state_label)
        and left.best_actions == right.best_actions
        and all(
            left_name == right_name
            and label_equal(left_label, right_label)
            for (left_name, left_label), (
                right_name,
                right_label,
            ) in zip(left.action_labels, right.action_labels)
        )
    )


def _small_differential(case_count: int) -> dict[str, object]:
    x_axis = np.arange(3, dtype=np.float32)
    y_axis = np.arange(2, dtype=np.float32)
    actions = (
        ControlAction("left", -1.0, 0.0),
        ControlAction("stay", 0.0, 0.0),
        ControlAction("right", 1.0, 0.0),
    )
    delays = (0, 1, 3)
    cadence = (1, 2)
    config = ViabilityConfig(
        frames_per_layer=2,
        required_clearance=0.0,
        clamp_to_bounds=True,
    )
    scalar_ms = []
    native_ms = []
    warm_ms = []
    upper_scalar_ms = []
    upper_native_ms = []
    failures = []
    upper_failures = []
    bound_violation_seeds = []
    native_states = []
    for seed in range(case_count):
        random = np.random.default_rng(30_000 + seed)
        clearance = np.where(
            random.random((7, 2, 3)) < 0.2,
            -1.0,
            random.choice((1.0, 2.0, 4.0), size=(7, 2, 3)),
        ).astype(np.float32)
        clearance[0, :, 1] = 4.0
        pending = (
            PendingCommand("right", (1, 2, 3))
            if seed % 2
            else None
        )
        continuation_actions = (
            ("left", "stay") if seed % 3 == 0 else None
        )
        budgeted_actions = (
            ("right",) if continuation_actions is not None else None
        )
        continuation_budget = (
            (seed // 3) % 3
            if continuation_actions is not None
            else 0
        )
        arguments = {
            "x_axis": x_axis,
            "y_axis": y_axis,
            "clearance_volume": clearance,
            "actions": actions,
            "delay_frames": delays,
            "decision_frame_support": cadence,
            "config": config,
            "start_frame": 0,
            "row": 0,
            "column": 1,
            "observed_action": "stay",
            "pending_command": pending,
            "continuation_actions": continuation_actions,
            "budgeted_continuation_actions": budgeted_actions,
            "continuation_action_budget": continuation_budget,
        }
        started = time.perf_counter()
        scalar = scalar_belief_cadence_survival(**arguments)
        scalar_ms.append((time.perf_counter() - started) * 1000.0)
        upper_arguments = {
            key: value
            for key, value in arguments.items()
            if key not in {
                "continuation_actions",
                "budgeted_continuation_actions",
                "continuation_action_budget",
            }
        }
        started = time.perf_counter()
        scalar_upper = scalar_clairvoyant_recursive_cadence_survival(
            **upper_arguments
        )
        upper_scalar_ms.append(
            (time.perf_counter() - started) * 1000.0
        )
        problem = SurvivalQueryProblem(
            x_axis=x_axis,
            y_axis=y_axis,
            clearance_volume=clearance,
            actions=actions,
            delay_frames=delays,
            nominal_delay=1,
            config=config,
        )
        with problem.build_belief_pipeline_workspace(
            policy_version=seed,
            decision_frame_support=cadence,
            continuation_actions=continuation_actions,
            budgeted_continuation_actions=budgeted_actions,
            continuation_action_budget=continuation_budget,
        ) as workspace:
            query = {
                "policy_version": seed,
                "frame": 0,
                "row": 0,
                "column": 1,
                "observed_action": "stay",
                "pending_command": pending,
            }
            started = time.perf_counter()
            native = workspace.query_cell(**query)
            native_ms.append((time.perf_counter() - started) * 1000.0)
            started = time.perf_counter()
            warm = workspace.query_cell(**query)
            warm_ms.append((time.perf_counter() - started) * 1000.0)
        native_states.append(native.evaluated_state_count)
        if not _equal(native, scalar) or not _equal(warm, scalar):
            failures.append(seed)
        with problem.build_belief_pipeline_workspace(
            policy_version=("upper", seed),
            decision_frame_support=cadence,
            reveal_remaining_delay=True,
        ) as workspace:
            started = time.perf_counter()
            native_upper = workspace.query_cell(
                policy_version=("upper", seed),
                frame=0,
                row=0,
                column=1,
                observed_action="stay",
                pending_command=pending,
            )
            upper_native_ms.append(
                (time.perf_counter() - started) * 1000.0
            )
        if not _equal(native_upper, scalar_upper):
            upper_failures.append(seed)
        if any(
            lower_label > upper_label
            for (_, lower_label), (_, upper_label) in zip(
                scalar.action_labels,
                scalar_upper.action_labels,
            )
        ):
            bound_violation_seeds.append(seed)
    return {
        "case_count": case_count,
        "failure_count": len(failures),
        "failures": failures,
        "upper_failure_count": len(upper_failures),
        "upper_failures": upper_failures,
        "bound_violation_count": len(bound_violation_seeds),
        "bound_violation_seeds": bound_violation_seeds,
        "scalar_ms": _summary(scalar_ms),
        "native_cold_ms": _summary(native_ms),
        "native_warm_ms": _summary(warm_ms),
        "scalar_upper_ms": _summary(upper_scalar_ms),
        "native_upper_ms": _summary(upper_native_ms),
        "native_memoized_states": _summary(
            [float(value) for value in native_states]
        ),
    }


def _th08_case(
    *,
    horizon: int,
    action_count: int,
    continuation_action_count: int,
    continuation_action_budget: int,
    reveal_remaining_delay: bool,
    cadence: tuple[int, ...],
    timeout_ms: int,
) -> dict[str, object]:
    x_axis, y_axis, full_clearance = _structured_clearance(3)
    clearance = np.ascontiguousarray(
        full_clearance[: horizon + 1],
        dtype=np.float32,
    )
    actions = TH08_VIABILITY_ACTIONS[:action_count]
    config = ViabilityConfig(
        frames_per_layer=TH08_CORRIDOR_CONFIG.frames_per_layer,
        required_clearance=TH08_CORRIDOR_CONFIG.required_clearance,
    )
    problem = SurvivalQueryProblem(
        x_axis=x_axis,
        y_axis=y_axis,
        clearance_volume=clearance,
        actions=actions,
        delay_frames=(1, 2, 3, 4, 5, 6),
        nominal_delay=4,
        config=config,
    )
    policy_version = (
        horizon,
        action_count,
        continuation_action_count,
        continuation_action_budget,
        reveal_remaining_delay,
        cadence,
    )
    with problem.build_belief_pipeline_workspace(
        policy_version=policy_version,
        decision_frame_support=cadence,
        continuation_actions=tuple(
            action.name
            for action in actions[:continuation_action_count]
        ),
        budgeted_continuation_actions=tuple(
            action.name
            for action in actions[continuation_action_count:]
        ),
        continuation_action_budget=continuation_action_budget,
        reveal_remaining_delay=reveal_remaining_delay,
    ) as workspace:
        query = {
            "policy_version": policy_version,
            "frame": 0,
            "row": 13,
            "column": 12,
            "observed_action": "stay",
            "pending_command": PendingCommand(
                actions[1].name,
                (1, 2, 3, 4, 5, 6),
            ),
        }
        refinement_steps = []
        result = None
        for budget in range(continuation_action_budget + 1):
            started = time.perf_counter()
            try:
                result = workspace.query_cell(
                    **query,
                    continuation_action_budget=budget,
                    timeout_ms=timeout_ms,
                )
            except PipelineWorkspaceDeadlineError:
                refinement_steps.append({
                    "budget": budget,
                    "completed": False,
                    "elapsed_ms": (
                        time.perf_counter() - started
                    ) * 1000.0,
                })
                return {
                    "horizon": horizon,
                    "action_count": action_count,
                    "continuation_action_count": (
                        continuation_action_count
                    ),
                    "continuation_action_budget": (
                        continuation_action_budget
                    ),
                    "reveal_remaining_delay": reveal_remaining_delay,
                    "cadence": list(cadence),
                    "timeout_ms": timeout_ms,
                    "completed": False,
                    "refinement_steps": refinement_steps,
                }
            refinement_steps.append({
                "budget": budget,
                "completed": True,
                "elapsed_ms": (
                    time.perf_counter() - started
                ) * 1000.0,
                "new_state_count": (
                    result.workspace_stats.new_state_count
                ),
                "state_frames": result.state_label.guaranteed_frames,
                "state_margin": result.state_label.bottleneck_margin,
                "best_actions": list(result.best_actions),
            })
        assert result is not None
        started = time.perf_counter()
        warm = workspace.query_cell(
            **query,
            continuation_action_budget=continuation_action_budget,
        )
        warm_ms = (time.perf_counter() - started) * 1000.0
    return {
        "horizon": horizon,
        "action_count": action_count,
        "continuation_action_count": continuation_action_count,
        "continuation_action_budget": continuation_action_budget,
        "reveal_remaining_delay": reveal_remaining_delay,
        "cadence": list(cadence),
        "timeout_ms": timeout_ms,
        "completed": True,
        "elapsed_ms": refinement_steps[-1]["elapsed_ms"],
        "total_refinement_ms": sum(
            step["elapsed_ms"] for step in refinement_steps
        ),
        "refinement_steps": refinement_steps,
        "warm_ms": warm_ms,
        "state_label": {
            "frames": result.state_label.guaranteed_frames,
            "margin": result.state_label.bottleneck_margin,
        },
        "best_actions": list(result.best_actions),
        "action_labels": {
            name: {
                "frames": label.guaranteed_frames,
                "margin": label.bottleneck_margin,
            }
            for name, label in result.action_labels
        },
        "warm_matches": _equal(result, warm),
        "stats": {
            field: int(value)
            for field, value in vars(result.workspace_stats).items()
        },
}


def _bound_certification(
    scaling_results: list[dict[str, object]],
) -> dict[str, object]:
    def selected(
        *,
        continuation_action_count: int,
        reveal_remaining_delay: bool,
    ) -> dict[str, object] | None:
        return next(
            (
                result
                for result in scaling_results
                if result.get("completed")
                and result["horizon"] == 32
                and result["action_count"] == 17
                and result["continuation_action_count"]
                    == continuation_action_count
                and result["continuation_action_budget"] == 0
                and result["reveal_remaining_delay"]
                    is reveal_remaining_delay
                and result["cadence"] == [4, 5, 6]
            ),
            None,
        )

    lower = selected(
        continuation_action_count=9,
        reveal_remaining_delay=False,
    )
    upper = selected(
        continuation_action_count=17,
        reveal_remaining_delay=True,
    )
    if lower is None or upper is None:
        return {"available": False}
    lower_labels = lower["action_labels"]
    upper_labels = upper["action_labels"]

    def label(item: dict[str, object]) -> tuple[int, float]:
        return int(item["frames"]), float(item["margin"])

    best_lower = max(label(item) for item in lower_labels.values())
    best_upper = max(label(item) for item in upper_labels.values())
    bound_violations = [
        name
        for name, item in lower_labels.items()
        if label(item) > label(upper_labels[name])
    ]
    lower_best_actions = [
        name
        for name, item in lower_labels.items()
        if label(item) == best_lower
    ]
    unresolved_actions = [
        name
        for name, item in upper_labels.items()
        if label(item) >= best_lower
    ]
    return {
        "available": True,
        "lower_policy": "all-root/focused-continuation B=0",
        "upper_policy": "unrestricted with revealed remaining delay",
        "best_lower": {
            "frames": best_lower[0],
            "margin": best_lower[1],
        },
        "best_upper": {
            "frames": best_upper[0],
            "margin": best_upper[1],
        },
        "bound_violations": bound_violations,
        "state_value_certified": (
            not bound_violations and best_upper <= best_lower
        ),
        "lower_best_actions": lower_best_actions,
        "unresolved_actions": unresolved_actions,
    }


def benchmark(
    small_cases: int,
    timeout_ms: int,
    profile: str,
) -> dict[str, object]:
    quick_cases = (
        (32, 9, 9, 0, False, (4, 5, 6)),
        (32, 17, 9, 0, False, (4, 5, 6)),
        (32, 17, 9, 1, False, (4, 5, 6)),
    )
    full_only_cases = (
        (32, 17, 17, 0, True, (4, 5, 6)),
        (32, 17, 9, 2, False, (4, 5, 6)),
        (32, 17, 17, 0, False, (4, 5, 6)),
        (80, 17, 9, 0, False, (4, 5, 6)),
        (8, 17, 9, 0, False, (2, 3, 4, 5, 6, 7, 8, 9)),
        (16, 17, 9, 0, False, (2, 3, 4, 5, 6, 7, 8, 9)),
        (32, 17, 9, 0, False, (2, 3, 4, 5, 6, 7, 8, 9)),
    )
    scaling_cases = (
        quick_cases
        if profile == "quick"
        else quick_cases + full_only_cases
    )
    scaling_results = [
        _th08_case(
            horizon=horizon,
            action_count=action_count,
            continuation_action_count=continuation_action_count,
            continuation_action_budget=continuation_action_budget,
            reveal_remaining_delay=reveal_remaining_delay,
            cadence=cadence,
            timeout_ms=timeout_ms,
        )
        for (
            horizon,
            action_count,
            continuation_action_count,
            continuation_action_budget,
            reveal_remaining_delay,
            cadence,
        ) in scaling_cases
    ]
    return {
        "schema": "th08.belief_pipeline_workspace_benchmark.v5",
        "profile": profile,
        "contract": (
            "conditional hold/no-write, recursive cadence, and "
            "non-clairvoyant remaining-delay information-set merging; "
            "future non-base actions consume a finite decision budget; "
            "revealed remaining delay is an explicit optimistic relaxation"
        ),
        "small_differential": _small_differential(small_cases),
        "th08_structured_scaling": scaling_results,
        "th08_structured_bound_certification": (
            _bound_certification(scaling_results)
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--profile",
        choices=("quick", "full"),
        default="quick",
    )
    parser.add_argument("--small-cases", type=int)
    parser.add_argument("--timeout-ms", type=int, default=3000)
    arguments = parser.parse_args()
    small_cases = (
        arguments.small_cases
        if arguments.small_cases is not None
        else (16 if arguments.profile == "quick" else 128)
    )
    report = benchmark(
        small_cases,
        arguments.timeout_ms,
        arguments.profile,
    )
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
