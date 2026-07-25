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
    failures = []
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
        }
        started = time.perf_counter()
        scalar = scalar_belief_cadence_survival(**arguments)
        scalar_ms.append((time.perf_counter() - started) * 1000.0)
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
    return {
        "case_count": case_count,
        "failure_count": len(failures),
        "failures": failures,
        "scalar_ms": _summary(scalar_ms),
        "native_cold_ms": _summary(native_ms),
        "native_warm_ms": _summary(warm_ms),
        "native_memoized_states": _summary(
            [float(value) for value in native_states]
        ),
    }


def _th08_case(
    *,
    horizon: int,
    action_count: int,
    continuation_action_count: int,
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
    with problem.build_belief_pipeline_workspace(
        policy_version=(horizon, action_count, cadence),
        decision_frame_support=cadence,
        continuation_actions=tuple(
            action.name
            for action in actions[:continuation_action_count]
        ),
    ) as workspace:
        started = time.perf_counter()
        try:
            result = workspace.query_cell(
                policy_version=(horizon, action_count, cadence),
                frame=0,
                row=13,
                column=12,
                observed_action="stay",
                pending_command=PendingCommand(
                    actions[1].name,
                    (1, 2, 3, 4, 5, 6),
                ),
                timeout_ms=timeout_ms,
            )
        except PipelineWorkspaceDeadlineError:
            return {
                "horizon": horizon,
                "action_count": action_count,
                "continuation_action_count": continuation_action_count,
                "cadence": list(cadence),
                "timeout_ms": timeout_ms,
                "completed": False,
                "elapsed_ms": (
                    time.perf_counter() - started
                ) * 1000.0,
            }
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        started = time.perf_counter()
        warm = workspace.query_cell(
            policy_version=(horizon, action_count, cadence),
            frame=0,
            row=13,
            column=12,
            observed_action="stay",
            pending_command=PendingCommand(
                actions[1].name,
                (1, 2, 3, 4, 5, 6),
            ),
        )
        warm_ms = (time.perf_counter() - started) * 1000.0
    return {
        "horizon": horizon,
        "action_count": action_count,
        "continuation_action_count": continuation_action_count,
        "cadence": list(cadence),
        "timeout_ms": timeout_ms,
        "completed": True,
        "elapsed_ms": elapsed_ms,
        "warm_ms": warm_ms,
        "state_label": {
            "frames": result.state_label.guaranteed_frames,
            "margin": result.state_label.bottleneck_margin,
        },
        "best_actions": list(result.best_actions),
        "warm_matches": _equal(result, warm),
        "stats": {
            field: int(value)
            for field, value in vars(result.workspace_stats).items()
        },
    }


def benchmark(small_cases: int, timeout_ms: int) -> dict[str, object]:
    scaling_cases = (
        (32, 9, 9, (4, 5, 6)),
        (32, 17, 9, (4, 5, 6)),
        (32, 17, 17, (4, 5, 6)),
        (80, 17, 9, (4, 5, 6)),
        (8, 17, 9, (2, 3, 4, 5, 6, 7, 8, 9)),
        (16, 17, 9, (2, 3, 4, 5, 6, 7, 8, 9)),
        (32, 17, 9, (2, 3, 4, 5, 6, 7, 8, 9)),
    )
    return {
        "schema": "th08.belief_pipeline_workspace_benchmark.v3",
        "contract": (
            "conditional hold/no-write, recursive cadence, and "
            "non-clairvoyant remaining-delay information-set merging"
        ),
        "small_differential": _small_differential(small_cases),
        "th08_structured_scaling": [
            _th08_case(
                horizon=horizon,
                action_count=action_count,
                continuation_action_count=continuation_action_count,
                cadence=cadence,
                timeout_ms=timeout_ms,
            )
            for (
                horizon,
                action_count,
                continuation_action_count,
                cadence,
            ) in scaling_cases
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--small-cases", type=int, default=128)
    parser.add_argument("--timeout-ms", type=int, default=3000)
    arguments = parser.parse_args()
    report = benchmark(arguments.small_cases, arguments.timeout_ms)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
