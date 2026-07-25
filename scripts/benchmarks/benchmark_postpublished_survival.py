#!/usr/bin/env python3
"""Benchmark Boolean-first losing labels and the pending-command oracle."""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

import numpy as np

from th08_corridor_adapter import (
    TH08_CORRIDOR_CONFIG,
    TH08_PLAYFIELD,
    TH08_VIABILITY_ACTIONS,
)
from touhou_control.query_survival import (
    PendingCommand,
    SurvivalQueryProblem,
    query_local_survival,
    scalar_query_local_survival,
)
from touhou_control.viability import (
    ControlAction,
    ViabilityConfig,
    build_robust_viability_policy,
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


def _structured_clearance(seed: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    x_axis = np.linspace(
        TH08_PLAYFIELD.left,
        TH08_PLAYFIELD.right,
        int(
            round(
                (TH08_PLAYFIELD.right - TH08_PLAYFIELD.left)
                / TH08_CORRIDOR_CONFIG.grid_step
            )
        )
        + 1,
        dtype=np.float32,
    )
    y_axis = np.linspace(
        TH08_PLAYFIELD.top,
        TH08_PLAYFIELD.bottom,
        int(
            round(
                (TH08_PLAYFIELD.bottom - TH08_PLAYFIELD.top)
                / TH08_CORRIDOR_CONFIG.grid_step
            )
        )
        + 1,
        dtype=np.float32,
    )
    grid_x, grid_y = np.meshgrid(x_axis, y_axis)
    frame_count = TH08_CORRIDOR_CONFIG.horizon_frames + 1
    volume = np.full(
        (frame_count, len(y_axis), len(x_axis)),
        48.0,
        dtype=np.float32,
    )
    for _ in range(14):
        start_x = rng.uniform(TH08_PLAYFIELD.left, TH08_PLAYFIELD.right)
        start_y = rng.uniform(TH08_PLAYFIELD.top, TH08_PLAYFIELD.bottom)
        velocity_x = rng.uniform(-3.0, 3.0)
        velocity_y = rng.uniform(-3.0, 3.0)
        radius = rng.uniform(6.0, 22.0)
        for frame in range(frame_count):
            x = start_x + velocity_x * frame
            y = start_y + velocity_y * frame
            distance = np.hypot(grid_x - x, grid_y - y) - radius
            volume[frame] = np.minimum(volume[frame], distance)
    return x_axis, y_axis, volume


def benchmark(
    *,
    dense_seeds: int,
    oracle_seeds: int,
) -> dict[str, object]:
    timings = {"boolean": [], "fused": [], "postpublished": []}
    dense_failures = []
    dense_cases = []
    config = ViabilityConfig(
        frames_per_layer=TH08_CORRIDOR_CONFIG.frames_per_layer,
        required_clearance=TH08_CORRIDOR_CONFIG.required_clearance,
    )
    for seed in range(dense_seeds):
        x_axis, y_axis, clearance = _structured_clearance(seed)
        arguments = {
            "x_axis": x_axis,
            "y_axis": y_axis,
            "clearance_volume": clearance,
            "actions": TH08_VIABILITY_ACTIONS,
            "delay_frames": (1, 2, 3, 4, 5, 6),
            "nominal_delay": 4,
            "config": config,
        }
        started = time.perf_counter()
        boolean = build_robust_viability_policy(**arguments)
        timings["boolean"].append((time.perf_counter() - started) * 1000.0)
        started = time.perf_counter()
        fused = build_robust_viability_policy(
            **arguments,
            survival_labels=True,
        )
        timings["fused"].append((time.perf_counter() - started) * 1000.0)
        problem = SurvivalQueryProblem(**arguments)
        started = time.perf_counter()
        postpublished = problem.build_postpublished_policy(boolean)
        timings["postpublished"].append(
            (time.perf_counter() - started) * 1000.0
        )
        losing_states = ~boolean.viable
        losing_actions = losing_states[:-1]
        frames_equal = np.array_equal(
            postpublished.survival_frames[losing_states],
            fused.survival_frames[losing_states],
        )
        margins_equal = np.array_equal(
            postpublished.survival_bottleneck_margins[losing_states],
            fused.survival_bottleneck_margins[losing_states],
        )
        masks_equal = np.array_equal(
            postpublished.survival_best_action_masks[losing_actions],
            fused.survival_best_action_masks[losing_actions],
        )
        if not (frames_equal and margins_equal and masks_equal):
            dense_failures.append(seed)
        dense_cases.append(
            {
                "seed": seed,
                "losing_state_count": int(np.count_nonzero(losing_states)),
                "frames_equal": frames_equal,
                "margins_equal": margins_equal,
                "masks_equal": masks_equal,
                "boolean_ms": timings["boolean"][-1],
                "fused_ms": timings["fused"][-1],
                "postpublished_ms": timings["postpublished"][-1],
            }
        )

    oracle_failures = []
    oracle_cases = []
    small_axis = np.arange(4, dtype=np.float32)
    small_actions = (
        ControlAction("stay", 0.0, 0.0),
        ControlAction("left", -1.0, 0.0),
        ControlAction("right", 1.0, 0.0),
    )
    for seed in range(oracle_seeds):
        rng = np.random.default_rng(10_000 + seed)
        clearance = rng.uniform(
            -2.0,
            6.0,
            size=(9, 4, 4),
        ).astype(np.float32)
        arguments = {
            "x_axis": small_axis,
            "y_axis": small_axis,
            "clearance_volume": clearance,
            "actions": small_actions,
            "delay_frames": (0, 1, 3),
            "config": ViabilityConfig(frames_per_layer=2),
            "start_frame": seed % 4,
            "row": 1 + seed % 2,
            "column": 1 + (seed // 2) % 2,
            "observed_action": small_actions[seed % 3].name,
            "pending_command": (
                PendingCommand(
                    small_actions[(seed + 1) % 3].name,
                    (1, 2, 3),
                )
                if seed % 2
                else None
            ),
        }
        scalar = scalar_query_local_survival(**arguments)
        native = query_local_survival(**arguments, backend="native")
        labels_match = (
            native.state_label.guaranteed_frames
            == scalar.state_label.guaranteed_frames
            and abs(
                native.state_label.bottleneck_margin
                - scalar.state_label.bottleneck_margin
            )
            <= 1e-6
            and native.best_actions == scalar.best_actions
            and all(
                native_label.guaranteed_frames
                == scalar_label.guaranteed_frames
                and abs(
                    native_label.bottleneck_margin
                    - scalar_label.bottleneck_margin
                )
                <= 1e-6
                for (_, native_label), (_, scalar_label) in zip(
                    native.action_labels,
                    scalar.action_labels,
                )
            )
        )
        if not labels_match:
            oracle_failures.append(seed)
        oracle_cases.append(
            {
                "seed": seed,
                "labels_match": labels_match,
                "evaluated_state_count": native.evaluated_state_count,
            }
        )

    return {
        "schema": "postpublished-losing-survival-benchmark-v1",
        "dense_scope": (
            "Structured 24x27x81 moving-circle clearance fields. Dense fused "
            "is the accepted native oracle; postpublished labels may differ "
            "on Boolean-winning states but must be exact on every losing "
            "state and first-action mask."
        ),
        "pending_oracle_scope": (
            "Independent scalar/native phase-exact pipeline differential "
            "with observed, older-pending, selected, and carried remaining "
            "delay states."
        ),
        "dense_seed_count": dense_seeds,
        "dense_failure_count": len(dense_failures),
        "dense_failures": dense_failures,
        "timing_ms": {
            name: _summary(values) for name, values in timings.items()
        },
        "dense_cases": dense_cases,
        "pending_oracle_seed_count": oracle_seeds,
        "pending_oracle_failure_count": len(oracle_failures),
        "pending_oracle_failures": oracle_failures,
        "pending_oracle_cases": oracle_cases,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--dense-seeds", type=int, default=24)
    parser.add_argument("--oracle-seeds", type=int, default=64)
    args = parser.parse_args(argv)
    if args.dense_seeds <= 0 or args.oracle_seeds <= 0:
        parser.error("seed counts must be positive")
    report = benchmark(
        dense_seeds=args.dense_seeds,
        oracle_seeds=args.oracle_seeds,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    print(args.output)
    return (
        0
        if report["dense_failure_count"] == 0
        and report["pending_oracle_failure_count"] == 0
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
