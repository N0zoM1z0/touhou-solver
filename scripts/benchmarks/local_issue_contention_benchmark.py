#!/usr/bin/env python3
"""Measure local native geometry while background viability consumes CPU."""

from __future__ import annotations

import argparse
import json
import math
import platform
import statistics
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

from benchmarks.local_hazard_geometry_benchmark import _query, _workload
from th08_corridor_adapter import (
    TH08_CORRIDOR_CONFIG,
    TH08_PLAYFIELD,
    TH08_VIABILITY_ACTIONS,
)
from touhou_control import native_backend
from touhou_control.background_priority import lower_current_thread_priority
from touhou_control.viability import (
    ViabilityConfig,
    build_robust_viability_policy,
)


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)]


def _summary(values: list[float]) -> dict[str, float | int]:
    return {
        "count": len(values),
        "median_ms": statistics.median(values),
        "p95_ms": _p95(values),
        "max_ms": max(values),
    }


def _viability_problem() -> dict[str, object]:
    config = TH08_CORRIDOR_CONFIG
    x_axis = np.arange(
        TH08_PLAYFIELD.left,
        TH08_PLAYFIELD.right + 0.5 * config.grid_step,
        config.grid_step,
        dtype=np.float32,
    )
    y_axis = np.arange(
        TH08_PLAYFIELD.top,
        TH08_PLAYFIELD.bottom + 0.5 * config.grid_step,
        config.grid_step,
        dtype=np.float32,
    )
    generator = np.random.default_rng(0xCE0125)
    # A deterministic, temporally correlated signed-clearance field exercises
    # both early losing exits and complete safe transitions.
    base = generator.normal(
        9.0,
        16.0,
        (len(y_axis), len(x_axis)),
    ).astype(np.float32)
    drift = generator.normal(
        0.0,
        1.5,
        (config.horizon_frames + 1, len(y_axis), len(x_axis)),
    ).astype(np.float32)
    clearance_volume = np.empty_like(drift)
    clearance_volume[0] = base
    for frame in range(1, config.horizon_frames + 1):
        clearance_volume[frame] = (
            0.94 * clearance_volume[frame - 1] + drift[frame]
        )
    return {
        "x_axis": x_axis,
        "y_axis": y_axis,
        "clearance_volume": clearance_volume,
        "actions": TH08_VIABILITY_ACTIONS,
        "delay_frames": (2, 3, 4, 5, 6),
        "nominal_delay": 4,
        "config": ViabilityConfig(
            frames_per_layer=config.frames_per_layer,
            required_clearance=config.required_clearance,
            clamp_to_bounds=True,
            repair_radius_cells=1,
        ),
        "backend": "native",
    }


class _BackgroundViability:
    def __init__(
        self,
        worker_limit: int,
        problem: dict[str, object],
        *,
        low_priority: bool,
    ) -> None:
        self.worker_limit = worker_limit
        self.problem = problem
        self.low_priority = low_priority
        self.stop = threading.Event()
        self.ready = threading.Event()
        self.solve_ms: list[float] = []
        self.priority_lowered = False
        self.worker_limit_applied = False

    def run(self) -> None:
        self.priority_lowered = (
            lower_current_thread_priority()
            if self.low_priority
            else False
        )
        self.worker_limit_applied = (
            native_backend.set_current_thread_viability_worker_limit(
                self.worker_limit
            )
        )
        self.ready.set()
        while not self.stop.is_set():
            started = time.perf_counter()
            build_robust_viability_policy(**self.problem)
            self.solve_ms.append(
                (time.perf_counter() - started) * 1000.0
            )


def _geometry_sequence(workload: dict[str, object]) -> None:
    for step in range(1, 11):
        _query(workload, backend="native", step=step)


def _measure_geometry(
    workload: dict[str, object],
    *,
    warmup: int,
    samples: int,
) -> list[float]:
    for _ in range(warmup):
        _geometry_sequence(workload)
    values: list[float] = []
    for _ in range(samples):
        started = time.perf_counter()
        _geometry_sequence(workload)
        values.append((time.perf_counter() - started) * 1000.0)
    return values


def _variant(
    *,
    worker_limit: int | None,
    workloads: dict[str, dict[str, object]],
    problem: dict[str, object],
    warmup: int,
    samples: int,
    background_low_priority: bool,
) -> tuple[
    dict[str, object],
    dict[str, list[float]],
    list[float],
]:
    background = None
    executor = None
    future = None
    if worker_limit is not None:
        background = _BackgroundViability(
            worker_limit,
            problem,
            low_priority=background_low_priority,
        )
        executor = ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix=f"viability-{worker_limit}",
        )
        future = executor.submit(background.run)
        if not background.ready.wait(timeout=10.0):
            raise TimeoutError("background viability worker did not start")
        while not background.solve_ms:
            if future.done():
                future.result()
            time.sleep(0.001)
    try:
        geometry_values = {
            name: _measure_geometry(
                workload,
                warmup=warmup,
                samples=samples,
            )
            for name, workload in workloads.items()
        }
    finally:
        if background is not None:
            background.stop.set()
        if future is not None:
            future.result(timeout=60.0)
        if executor is not None:
            executor.shutdown(wait=True)
    report = {
        "worker_limit": worker_limit,
        "geometry": {
            name: _summary(values)
            for name, values in geometry_values.items()
        },
        "background_viability": (
            {
                "solve": _summary(background.solve_ms),
                "priority_lowered": background.priority_lowered,
                "worker_limit_applied": background.worker_limit_applied,
            }
            if background is not None
            else None
        ),
    }
    return (
        report,
        geometry_values,
        background.solve_ms if background is not None else [],
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--samples", type=int, default=30)
    parser.add_argument("--warmup", type=int, default=3)
    parser.add_argument("--rounds", type=int, default=4)
    parser.add_argument(
        "--background-low-priority",
        action="store_true",
        help=(
            "lower the parent viability thread; disabled by default to match "
            "the authoritative planner"
        ),
    )
    args = parser.parse_args(argv)
    if args.samples <= 0 or args.warmup < 0 or args.rounds <= 0:
        raise ValueError("invalid benchmark counts")
    if not native_backend.available():
        raise RuntimeError("native backend is unavailable")

    workloads = {
        "certificate_laser_storm": _workload(
            seed=0xCE0122A,
            position_count=81,
            bullet_count=111,
            laser_count=210,
            body_count=5,
            clustered_positions=True,
        ),
        "beam_laser_storm": _workload(
            seed=0xCE0122B,
            position_count=240,
            bullet_count=600,
            laser_count=210,
            body_count=5,
            clustered_positions=False,
        ),
    }
    problem = _viability_problem()
    variant_limits = {
        "idle": None,
        "workers_1": 1,
        "workers_2": 2,
        "workers_4": 4,
    }
    base_order = tuple(variant_limits)
    round_reports: list[dict[str, object]] = []
    aggregate_geometry = {
        name: {workload_name: [] for workload_name in workloads}
        for name in variant_limits
    }
    aggregate_solve = {name: [] for name in variant_limits}
    aggregate_priority = {name: [] for name in variant_limits}
    aggregate_applied = {name: [] for name in variant_limits}
    for round_index in range(args.rounds):
        offset = round_index % len(base_order)
        order = base_order[offset:] + base_order[:offset]
        round_variants: dict[str, object] = {}
        for name in order:
            variant_report, geometry_values, solve_values = _variant(
                worker_limit=variant_limits[name],
                workloads=workloads,
                problem=problem,
                warmup=args.warmup,
                samples=args.samples,
                background_low_priority=args.background_low_priority,
            )
            round_variants[name] = variant_report
            for workload_name, values in geometry_values.items():
                aggregate_geometry[name][workload_name].extend(values)
            aggregate_solve[name].extend(solve_values)
            background_report = variant_report["background_viability"]
            if background_report is not None:
                aggregate_priority[name].append(
                    background_report["priority_lowered"]
                )
                aggregate_applied[name].append(
                    background_report["worker_limit_applied"]
                )
        round_reports.append(
            {
                "round": round_index,
                "order": list(order),
                "variants": round_variants,
            }
        )
    aggregate = {}
    for name, worker_limit in variant_limits.items():
        aggregate[name] = {
            "worker_limit": worker_limit,
            "geometry": {
                workload_name: _summary(values)
                for workload_name, values
                in aggregate_geometry[name].items()
            },
            "background_viability": (
                {
                    "solve": _summary(aggregate_solve[name]),
                    "priority_lowered_every_round": all(
                        aggregate_priority[name]
                    ),
                    "worker_limit_applied_every_round": all(
                        aggregate_applied[name]
                    ),
                }
                if worker_limit is not None
                else None
            ),
        }
    report = {
        "schema": "th08_local_issue_contention_v1",
        "platform": platform.platform(),
        "native_library": str(native_backend._library_path()),
        "samples": args.samples,
        "warmup": args.warmup,
        "rounds": args.rounds,
        "background_low_priority": args.background_low_priority,
        "geometry_steps_per_sample": 10,
        "viability_shape": list(
            problem["clearance_volume"].shape
        ),
        "viability_action_count": len(TH08_VIABILITY_ACTIONS),
        "round_reports": round_reports,
        "aggregate": aggregate,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
