#!/usr/bin/env python3
"""Benchmark stop/resume/redirect/reversal piecewise-transform hazards."""

from __future__ import annotations

import argparse
import gc
import json
import statistics
import time
from pathlib import Path

import numpy as np

from corridor_planner import (
    AabbHazard,
    AabbTrajectoryHazard,
    CorridorConfig,
    PiecewiseAabbHazard,
)
from touhou_control import native_backend
from touhou_control.corridor.clearance import hazard_clearance_volume
from touhou_control.adversarial import (
    AdversarialScenario,
    generate_adversarial_scenario,
)


def _dense_lower(
    scenario: AdversarialScenario,
) -> tuple[AabbTrajectoryHazard, ...]:
    return tuple(
        AabbTrajectoryHazard(
            tuple(
                AabbHazard(
                    *hazard.motion.position(frame),
                    hazard.half_width,
                    hazard.half_height,
                )
                for frame in range(scenario.horizon_frames + 1)
            )
        )
        for hazard in scenario.hazards
    )


def _sparse_lower(
    scenario: AdversarialScenario,
) -> tuple[PiecewiseAabbHazard, ...]:
    return tuple(
        PiecewiseAabbHazard(
            motion=hazard.motion,
            half_width=hazard.half_width,
            half_height=hazard.half_height,
        )
        for hazard in scenario.hazards
    )


def _summary(values: list[float]) -> dict[str, object]:
    ordered = sorted(values)
    p95_index = min(len(ordered) - 1, int(0.95 * len(ordered)))
    return {
        "median": statistics.median(values),
        "p95": ordered[p95_index],
        "minimum": ordered[0],
        "samples": values,
    }


def _measure(
    *,
    scenario: AdversarialScenario,
    sparse: bool,
    grid_x: np.ndarray,
    grid_y: np.ndarray,
    config: CorridorConfig,
    repeats: int,
) -> tuple[dict[str, object], np.ndarray]:
    lower_times: list[float] = []
    clearance_times: list[float] = []
    total_times: list[float] = []
    volume: np.ndarray | None = None
    for _ in range(repeats):
        gc.collect()
        started = time.perf_counter()
        hazards = (
            _sparse_lower(scenario)
            if sparse
            else _dense_lower(scenario)
        )
        lowered = time.perf_counter()
        volume = hazard_clearance_volume(
            grid_x,
            grid_y,
            aabbs=(),
            aabb_trajectories=() if sparse else hazards,
            piecewise_aabbs=hazards if sparse else (),
            segments=(),
            segment_trajectories=(),
            config=config,
        )
        finished = time.perf_counter()
        lower_times.append((lowered - started) * 1000.0)
        clearance_times.append((finished - lowered) * 1000.0)
        total_times.append((finished - started) * 1000.0)
    assert volume is not None
    return (
        {
            "lower_ms": _summary(lower_times),
            "clearance_ms": _summary(clearance_times),
            "total_ms": _summary(total_times),
        },
        volume,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=82408)
    parser.add_argument("--hazards", type=int, default=1024)
    parser.add_argument("--horizon", type=int, default=80)
    parser.add_argument("--maximum-events", type=int, default=6)
    parser.add_argument("--grid-step", type=float, default=16.0)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.repeats <= 0:
        parser.error("repeats must be positive")

    scenario = generate_adversarial_scenario(
        args.seed,
        hazard_count=args.hazards,
        horizon_frames=args.horizon,
        maximum_events=args.maximum_events,
    )
    x_axis = np.arange(
        8.0,
        376.0 + 0.5 * args.grid_step,
        args.grid_step,
        dtype=np.float32,
    )
    y_axis = np.arange(
        16.0,
        432.0 + 0.5 * args.grid_step,
        args.grid_step,
        dtype=np.float32,
    )
    grid_x, grid_y = np.meshgrid(x_axis, y_axis)
    config = CorridorConfig(
        grid_step=args.grid_step,
        frames_per_layer=1,
        horizon_frames=args.horizon,
        danger_radius=48.0,
    )
    dense, dense_volume = _measure(
        scenario=scenario,
        sparse=False,
        grid_x=grid_x,
        grid_y=grid_y,
        config=config,
        repeats=args.repeats,
    )
    sparse, sparse_volume = _measure(
        scenario=scenario,
        sparse=True,
        grid_x=grid_x,
        grid_y=grid_y,
        config=config,
        repeats=args.repeats,
    )
    maximum_difference = float(
        np.max(np.abs(dense_volume - sparse_volume), initial=0.0)
    )
    dense_median = float(dense["total_ms"]["median"])
    sparse_median = float(sparse["total_ms"]["median"])
    result = {
        "schema": "touhou_piecewise_native_benchmark_v2",
        "workload_identity": (
            "game_neutral_piecewise_transform_adversarial"
        ),
        "configuration": {
            "seed": args.seed,
            "hazards": args.hazards,
            "horizon": args.horizon,
            "maximum_events": args.maximum_events,
            "grid_step": args.grid_step,
            "repeats": args.repeats,
        },
        "backend": "native" if native_backend.available() else "python",
        "dense_time_indexed": dense,
        "sparse_piecewise": sparse,
        "median_speedup": dense_median / sparse_median,
        "maximum_dense_sparse_difference": maximum_difference,
    }
    payload = json.dumps(result, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
