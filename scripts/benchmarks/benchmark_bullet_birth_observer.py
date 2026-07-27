#!/usr/bin/env python3
"""Benchmark the default-off TH08 bullet-birth pool-blob observer."""

from __future__ import annotations

import argparse
import json
import statistics
import struct
import time
from pathlib import Path

import numpy as np


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(SCRIPTS_DIR))

from th08_live.bullet_birth import (  # noqa: E402
    BULLET_TIMER_CURRENT_OFFSET,
    BulletBirthTracker,
)
from th08_live.bullet_decode import (  # noqa: E402
    BULLET_GEOMETRY_OFFSET,
    BULLET_POSITION_OFFSET,
    BULLET_STATE_OFFSET,
    BULLET_VELOCITY_OFFSET,
    decode_planning_bullets,
)
from th08_live.sensor import BULLET_POOL_SIZE, BULLET_STRIDE  # noqa: E402


P95_LIMIT_MS = 0.20
P99_LIMIT_MS = 0.40
MAX_LIMIT_MS = 2.00
INTERLEAVED_P95_RATIO_LIMIT = 1.05


def _percentile(values: list[float], percentile: float) -> float:
    return float(np.percentile(np.asarray(values, dtype=np.float64), percentile))


def _pool(density: int) -> bytearray:
    if not 0 <= density <= BULLET_POOL_SIZE:
        raise ValueError("density is outside the hostile-bullet pool")
    blob = bytearray(BULLET_POOL_SIZE * BULLET_STRIDE)
    for slot in range(density):
        base = slot * BULLET_STRIDE
        struct.pack_into("<H", blob, base + BULLET_STATE_OFFSET, 1)
        struct.pack_into(
            "<i",
            blob,
            base + BULLET_TIMER_CURRENT_OFFSET,
            100 + slot,
        )
        struct.pack_into(
            "<ff",
            blob,
            base + BULLET_GEOMETRY_OFFSET,
            8.0,
            8.0,
        )
        struct.pack_into(
            "<ff",
            blob,
            base + BULLET_POSITION_OFFSET,
            float(slot % 384),
            float(slot % 448),
        )
        struct.pack_into(
            "<ff",
            blob,
            base + BULLET_VELOCITY_OFFSET,
            0.25,
            0.5,
        )
    return blob


def _samples(
    callback,
    *,
    iterations: int,
    warmup: int,
) -> list[float]:
    for _ in range(warmup):
        callback()
    result: list[float] = []
    for _ in range(iterations):
        started = time.perf_counter_ns()
        callback()
        result.append((time.perf_counter_ns() - started) / 1_000_000.0)
    return result


def _summary(samples: list[float]) -> dict[str, float]:
    return {
        "p50_ms": statistics.median(samples),
        "p95_ms": _percentile(samples, 95.0),
        "p99_ms": _percentile(samples, 99.0),
        "max_ms": max(samples),
    }


def run_benchmark(
    *,
    densities: tuple[int, ...],
    iterations: int,
    decode_iterations: int,
    burst_sizes: tuple[int, ...],
    burst_iterations: int,
    warmup: int,
) -> dict[str, object]:
    density_rows: list[dict[str, object]] = []
    for density in densities:
        blob = _pool(density)
        tracker = BulletBirthTracker(maximum_bootstrap_age=0)
        frame = 1

        def observe() -> None:
            nonlocal frame
            tracker.observe(blob, frame_before=frame, frame_after=frame)
            frame += 1

        observer_samples = _samples(
            observe,
            iterations=iterations,
            warmup=warmup,
        )
        density_rows.append(
            {
                "density": density,
                "observer": _summary(observer_samples),
            }
        )

    inactive_blob = _pool(0)
    burst_rows: list[dict[str, object]] = []
    for burst_size in burst_sizes:
        if not 0 < burst_size <= BULLET_POOL_SIZE:
            raise ValueError("burst size is outside the hostile-bullet pool")
        active_blob = _pool(burst_size)
        tracker = BulletBirthTracker(maximum_bootstrap_age=0)
        frame = 1
        tracker.observe(
            inactive_blob,
            frame_before=frame,
            frame_after=frame,
        )
        samples: list[float] = []
        for _ in range(burst_iterations):
            frame += 1
            started = time.perf_counter_ns()
            observation = tracker.observe(
                active_blob,
                frame_before=frame,
                frame_after=frame,
            )
            samples.append(
                (time.perf_counter_ns() - started) / 1_000_000.0
            )
            if len(observation.evidence) != burst_size:
                raise AssertionError("birth burst lost evidence")
            frame += 1
            tracker.observe(
                inactive_blob,
                frame_before=frame,
                frame_after=frame,
            )
        serialization_tracker = BulletBirthTracker(
            maximum_bootstrap_age=0,
        )
        serialization_tracker.observe(
            inactive_blob,
            frame_before=1,
            frame_after=1,
        )
        serialized_observation = serialization_tracker.observe(
            active_blob,
            frame_before=2,
            frame_after=2,
        )
        serialization_samples = _samples(
            lambda: json.dumps(serialized_observation.record()),
            iterations=burst_iterations,
            warmup=warmup,
        )
        serialized_bytes = len(
            json.dumps(
                serialized_observation.record(),
                separators=(",", ":"),
            ).encode("utf-8")
        )
        burst_rows.append(
            {
                "births_per_observation": burst_size,
                "observer": _summary(samples),
                "record_json": _summary(serialization_samples),
                "compact_json_bytes": serialized_bytes,
            }
        )

    full_blob = _pool(BULLET_POOL_SIZE)
    baseline_samples = _samples(
        lambda: decode_planning_bullets(full_blob),
        iterations=decode_iterations,
        warmup=max(2, warmup // 4),
    )
    tracker = BulletBirthTracker(maximum_bootstrap_age=0)
    frame = 1

    def interleaved() -> None:
        nonlocal frame
        tracker.observe(
            full_blob,
            frame_before=frame,
            frame_after=frame,
        )
        decode_planning_bullets(full_blob)
        frame += 1

    interleaved_samples = _samples(
        interleaved,
        iterations=decode_iterations,
        warmup=max(2, warmup // 4),
    )
    baseline = _summary(baseline_samples)
    interleaved = _summary(interleaved_samples)
    ratio = interleaved["p95_ms"] / max(baseline["p95_ms"], 1e-12)
    full_row = next(
        row for row in density_rows if row["density"] == BULLET_POOL_SIZE
    )
    observer = full_row["observer"]
    assert isinstance(observer, dict)
    gate = {
        "p95_limit_ms": P95_LIMIT_MS,
        "p99_limit_ms": P99_LIMIT_MS,
        "max_limit_ms": MAX_LIMIT_MS,
        "interleaved_p95_ratio_limit": INTERLEAVED_P95_RATIO_LIMIT,
        "observer_pass": (
            observer["p95_ms"] <= P95_LIMIT_MS
            and observer["p99_ms"] <= P99_LIMIT_MS
            and observer["max_ms"] <= MAX_LIMIT_MS
        ),
        "interleaved_pass": ratio <= INTERLEAVED_P95_RATIO_LIMIT,
    }
    gate["passed"] = gate["observer_pass"] and gate["interleaved_pass"]
    return {
        "schema": "th08-bullet-birth-observer-benchmark-v3",
        "pool_size": BULLET_POOL_SIZE,
        "iterations": iterations,
        "decode_iterations": decode_iterations,
        "burst_iterations": burst_iterations,
        "density_results": density_rows,
        "burst_results": burst_rows,
        "decode_baseline": baseline,
        "decode_interleaved": interleaved,
        "interleaved_p95_ratio": ratio,
        "gate": gate,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--densities",
        type=int,
        nargs="+",
        default=(0, 512, BULLET_POOL_SIZE),
    )
    parser.add_argument("--iterations", type=int, default=2_000)
    parser.add_argument("--decode-iterations", type=int, default=100)
    parser.add_argument(
        "--burst-sizes",
        type=int,
        nargs="+",
        default=(1, 8, 32, 33, 592),
    )
    parser.add_argument("--burst-iterations", type=int, default=200)
    parser.add_argument("--warmup", type=int, default=50)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if (
        args.iterations <= 0
        or args.decode_iterations <= 0
        or args.burst_iterations <= 0
        or args.warmup < 0
    ):
        parser.error("iterations must be positive and warmup non-negative")
    if BULLET_POOL_SIZE not in args.densities:
        parser.error("densities must include the full 1,536-slot gate")

    report = run_benchmark(
        densities=tuple(args.densities),
        iterations=args.iterations,
        decode_iterations=args.decode_iterations,
        burst_sizes=tuple(args.burst_sizes),
        burst_iterations=args.burst_iterations,
        warmup=args.warmup,
    )
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["gate"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
