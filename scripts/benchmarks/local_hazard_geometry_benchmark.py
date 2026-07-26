#!/usr/bin/env python3
"""Benchmark dense local bullet/segment geometry on certificate-like queries."""

from __future__ import annotations

import argparse
import json
import math
import platform
import statistics
import time
from pathlib import Path

import numpy as np

from th08_laser_runtime import PackedLaserFrame
from th08_live_dodge_agent import (
    EnemyBody,
    _native_hazards_for_positions,
    _numpy_hazards_for_positions,
)
from touhou_control import native_backend


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)]


def _timing(function, *, warmup: int, samples: int) -> dict[str, float]:
    for _ in range(warmup):
        function()
    values: list[float] = []
    for _ in range(samples):
        started = time.perf_counter()
        function()
        values.append((time.perf_counter() - started) * 1000.0)
    return {
        "median_ms": statistics.median(values),
        "p95_ms": _p95(values),
        "max_ms": max(values),
    }


def _workload(
    *,
    seed: int,
    position_count: int,
    bullet_count: int,
    laser_count: int,
    body_count: int,
    clustered_positions: bool,
    distant_lasers: bool = False,
) -> dict[str, object]:
    generator = np.random.default_rng(seed)
    if clustered_positions:
        positions_x = generator.uniform(
            160.0,
            224.0,
            position_count,
        ).astype(np.float32)
        positions_y = generator.uniform(
            256.0,
            320.0,
            position_count,
        ).astype(np.float32)
    else:
        positions_x = generator.uniform(
            0.0,
            384.0,
            position_count,
        ).astype(np.float32)
        positions_y = generator.uniform(
            16.0,
            448.0,
            position_count,
        ).astype(np.float32)
    bullet_frame = (
        generator.uniform(-96.0, 480.0, bullet_count).astype(np.float32),
        generator.uniform(-96.0, 544.0, bullet_count).astype(np.float32),
        generator.uniform(0.5, 12.0, bullet_count).astype(np.float32),
        generator.uniform(0.5, 12.0, bullet_count).astype(np.float32),
        generator.integers(
            0,
            2,
            bullet_count,
            dtype=np.uint8,
        ).astype(np.bool_),
    )
    if distant_lasers:
        start_x = generator.uniform(800.0, 1200.0, laser_count)
        start_y = generator.uniform(800.0, 1200.0, laser_count)
        segment_x = generator.uniform(-48.0, 48.0, laser_count)
        segment_y = generator.uniform(-48.0, 48.0, laser_count)
    else:
        start_x = generator.uniform(-128.0, 512.0, laser_count)
        start_y = generator.uniform(-128.0, 576.0, laser_count)
        angles = generator.uniform(
            -math.pi,
            math.pi,
            laser_count,
        )
        lengths = generator.uniform(48.0, 640.0, laser_count)
        segment_x = np.cos(angles) * lengths
        segment_y = np.sin(angles) * lengths
    lasers = PackedLaserFrame(
        start_x=np.asarray(start_x, dtype=np.float32),
        start_y=np.asarray(start_y, dtype=np.float32),
        segment_x=np.asarray(segment_x, dtype=np.float32),
        segment_y=np.asarray(segment_y, dtype=np.float32),
        collision_radius=generator.uniform(
            2.0,
            18.0,
            laser_count,
        ).astype(np.float32),
        base_uncertainty=generator.uniform(
            0.0,
            4.0,
            laser_count,
        ).astype(np.float32),
        uncertainty_per_frame=generator.uniform(
            0.0,
            0.5,
            laser_count,
        ).astype(np.float32),
    )
    bodies = tuple(
        EnemyBody(
            pointer=index + 1,
            x=float(generator.uniform(0.0, 384.0)),
            y=float(generator.uniform(16.0, 448.0)),
            vx=float(generator.uniform(-3.0, 3.0)),
            vy=float(generator.uniform(-3.0, 3.0)),
            half_width=float(generator.uniform(2.0, 24.0)),
            half_height=float(generator.uniform(2.0, 24.0)),
            flags=0,
            uncertainty=float(generator.uniform(0.0, 8.0)),
        )
        for index in range(body_count)
    )
    return {
        "positions_x": positions_x,
        "positions_y": positions_y,
        "bullet_frame": bullet_frame,
        "lasers": lasers,
        "enemy_bodies": bodies,
    }


def _query(workload: dict[str, object], *, backend: str, step: int):
    implementation = (
        _native_hazards_for_positions
        if backend == "native"
        else _numpy_hazards_for_positions
    )
    return implementation(
        workload["positions_x"],
        workload["positions_y"],
        step=step,
        bullet_frame=workload["bullet_frame"],
        lasers=workload["lasers"],
        enemy_bodies=workload["enemy_bodies"],
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--label", required=True)
    parser.add_argument("--samples", type=int, default=100)
    parser.add_argument("--warmup", type=int, default=8)
    parser.add_argument("--steps", type=int, default=10)
    args = parser.parse_args(argv)
    if args.samples <= 0 or args.warmup < 0 or args.steps <= 0:
        raise ValueError("invalid benchmark counts")

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
        "certificate_irrelevant_segments": _workload(
            seed=0xCE0122C,
            position_count=81,
            bullet_count=111,
            laser_count=240,
            body_count=5,
            clustered_positions=True,
            distant_lasers=True,
        ),
    }
    results: dict[str, object] = {}
    for name, workload in workloads.items():
        maximum_risk_difference = 0.0
        maximum_clearance_difference = 0.0
        for step in range(1, args.steps + 1):
            reference = _query(workload, backend="numpy", step=step)
            native = _query(workload, backend="native", step=step)
            np.testing.assert_array_equal(native[1], reference[1])
            np.testing.assert_array_equal(
                native[2] <= 0.0,
                reference[2] <= 0.0,
            )
            maximum_risk_difference = max(
                maximum_risk_difference,
                float(np.max(np.abs(native[0] - reference[0]))),
            )
            maximum_clearance_difference = max(
                maximum_clearance_difference,
                float(np.max(np.abs(native[2] - reference[2]))),
            )

        def native_sequence():
            return tuple(
                _query(workload, backend="native", step=step)
                for step in range(1, args.steps + 1)
            )

        def python_sequence():
            return tuple(
                _query(workload, backend="numpy", step=step)
                for step in range(1, args.steps + 1)
            )

        results[name] = {
            "position_count": len(workload["positions_x"]),
            "bullet_count": len(workload["bullet_frame"][0]),
            "laser_count": len(workload["lasers"].start_x),
            "body_count": len(workload["enemy_bodies"]),
            "sequence_steps": args.steps,
            "native": _timing(
                native_sequence,
                warmup=args.warmup,
                samples=args.samples,
            ),
            "python": _timing(
                python_sequence,
                warmup=min(args.warmup, 3),
                samples=max(10, args.samples // 5),
            ),
            "parity": {
                "collision_exact": True,
                "clearance_sign_exact": True,
                "maximum_risk_absolute_difference": (
                    maximum_risk_difference
                ),
                "maximum_clearance_absolute_difference": (
                    maximum_clearance_difference
                ),
            },
        }
    output = {
        "schema": "th08-local-hazard-geometry-benchmark-v1",
        "label": args.label,
        "environment": {
            "platform": platform.platform(),
            "native_library": str(native_backend._library_path()),
        },
        "boundary": (
            "Ten sequential local hazard queries over fixed already-projected "
            "float32 geometry. Includes ctypes validation/conversion and "
            "output allocation; excludes pool decode, lifecycle lowering, "
            "beam reduction, and action selection."
        ),
        "samples": args.samples,
        "warmup": args.warmup,
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
