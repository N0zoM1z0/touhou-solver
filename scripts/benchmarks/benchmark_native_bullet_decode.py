#!/usr/bin/env python3
"""Benchmark Python-object and native-packed TH08 bullet snapshots."""

from __future__ import annotations

import argparse
import json
import math
import struct
import time
from pathlib import Path

import numpy as np

from th08_live_dodge_agent import (
    BULLET_ANGLE_OFFSET,
    BULLET_CALLBACK_AUX_STATE_OFFSET,
    BULLET_CALLBACK_PHASE_STATE_OFFSET,
    BULLET_GEOMETRY_OFFSET,
    BULLET_ORIGINAL_TRANSFORM_FLAGS_OFFSET,
    BULLET_POOL_SIZE,
    BULLET_POSITION_OFFSET,
    BULLET_SPEED_OFFSET,
    BULLET_STATE_OFFSET,
    BULLET_STRIDE,
    BULLET_TRANSFORM_FLAGS_OFFSET,
    BULLET_VELOCITY_OFFSET,
    NATIVE_PACKED_BULLET_MIN_COUNT,
    _build_bullet_frames,
    decode_bullets,
    decode_live_planning_bullets,
    decode_packed_bullets,
)


def _pool(active_count: int) -> bytes:
    blob = bytearray(BULLET_POOL_SIZE * BULLET_STRIDE)
    for slot in range(active_count):
        base = slot * BULLET_STRIDE
        struct.pack_into("<H", blob, base + BULLET_STATE_OFFSET, 1)
        struct.pack_into(
            "<ff",
            blob,
            base + BULLET_GEOMETRY_OFFSET,
            -2.0 - slot % 31,
            4.0 + slot % 47,
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
            float(slot % 7) - 3.0,
            float(slot % 11) - 5.0,
        )
        struct.pack_into(
            "<f",
            blob,
            base + BULLET_SPEED_OFFSET,
            float("nan") if slot % 127 == 0 else 1.414 + slot * 0.001,
        )
        struct.pack_into(
            "<f",
            blob,
            base + BULLET_ANGLE_OFFSET,
            float("inf") if slot % 131 == 0 else -1.0 + slot * 0.002,
        )
        struct.pack_into(
            "<I",
            blob,
            base + BULLET_TRANSFORM_FLAGS_OFFSET,
            slot % 5,
        )
        struct.pack_into(
            "<I",
            blob,
            base + BULLET_ORIGINAL_TRANSFORM_FLAGS_OFFSET,
            0x00100202 if slot % 3 == 0 else 0,
        )
        struct.pack_into(
            "<h",
            blob,
            base + BULLET_CALLBACK_PHASE_STATE_OFFSET,
            slot % 32767,
        )
        blob[base + BULLET_CALLBACK_AUX_STATE_OFFSET] = slot % 256
    return bytes(blob)


def _percentile(values: list[float], quantile: float) -> float:
    ordered = sorted(values)
    index = max(
        0,
        min(
            len(ordered) - 1,
            math.ceil(quantile * len(ordered)) - 1,
        ),
    )
    return ordered[index]


def _measure(function, *, warmup: int, samples: int) -> dict[str, float]:
    for _ in range(warmup):
        function()
    timings: list[float] = []
    for _ in range(samples):
        started = time.perf_counter()
        function()
        timings.append((time.perf_counter() - started) * 1000.0)
    return {
        "median_ms": _percentile(timings, 0.5),
        "p95_ms": _percentile(timings, 0.95),
        "max_ms": max(timings),
    }


def _fields(bullet) -> tuple[object, ...]:
    return (
        bullet.x,
        bullet.y,
        bullet.vx,
        bullet.vy,
        bullet.half_width,
        bullet.half_height,
        bullet.transform_flags,
        bullet.slot,
        bullet.speed,
        bullet.angle,
        bullet.callback_phase_state,
        bullet.callback_aux_state,
        bullet.original_transform_flags,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--densities",
        type=int,
        nargs="+",
        default=(0, 50, 200, 400, 600, 800, 1200, 1536),
    )
    parser.add_argument("--horizon", type=int, default=16)
    parser.add_argument("--snapshot-lag", type=int, default=2)
    parser.add_argument("--warmup", type=int, default=5)
    parser.add_argument("--samples", type=int, default=80)
    args = parser.parse_args(argv)
    if (
        not args.densities
        or min(args.densities) < 0
        or max(args.densities) > BULLET_POOL_SIZE
        or args.horizon <= 0
        or args.snapshot_lag < 0
        or args.warmup < 0
        or args.samples <= 0
    ):
        raise ValueError("invalid benchmark arguments")

    results: list[dict[str, object]] = []
    for density in args.densities:
        blob = _pool(density)
        object_snapshot = decode_bullets(
            blob,
            retain_transform_runtime=False,
        )
        packed_snapshot = decode_packed_bullets(blob)
        live_snapshot = decode_live_planning_bullets(
            blob,
            backend="native",
        )
        object_fields = tuple(_fields(bullet) for bullet in object_snapshot)
        packed_fields = tuple(_fields(bullet) for bullet in packed_snapshot)
        live_fields = tuple(_fields(bullet) for bullet in live_snapshot)
        field_parity = (
            packed_fields == object_fields
            and live_fields == object_fields
        )
        object_frames = _build_bullet_frames(
            object_snapshot,
            horizon=args.horizon,
            snapshot_lag=args.snapshot_lag,
        )
        packed_frames = _build_bullet_frames(
            packed_snapshot,
            horizon=args.horizon,
            snapshot_lag=args.snapshot_lag,
        )
        projection_parity = all(
            np.array_equal(left_field, right_field)
            for left_frame, right_frame in zip(
                object_frames,
                packed_frames,
            )
            for left_field, right_field in zip(
                left_frame,
                right_frame,
            )
        )
        if not field_parity or not projection_parity:
            raise AssertionError(
                f"native packed parity failed at density {density}"
            )

        def decode_object():
            return decode_bullets(
                blob,
                retain_transform_runtime=False,
            )

        def decode_packed():
            return decode_packed_bullets(blob)

        def decode_live():
            return decode_live_planning_bullets(
                blob,
                backend="native",
            )

        def project_object():
            return _build_bullet_frames(
                object_snapshot,
                horizon=args.horizon,
                snapshot_lag=args.snapshot_lag,
            )

        def project_packed():
            return _build_bullet_frames(
                packed_snapshot,
                horizon=args.horizon,
                snapshot_lag=args.snapshot_lag,
            )

        def object_end_to_end():
            return _build_bullet_frames(
                decode_object(),
                horizon=args.horizon,
                snapshot_lag=args.snapshot_lag,
            )

        def packed_end_to_end():
            return _build_bullet_frames(
                decode_packed(),
                horizon=args.horizon,
                snapshot_lag=args.snapshot_lag,
            )

        def live_end_to_end():
            return _build_bullet_frames(
                decode_live(),
                horizon=args.horizon,
                snapshot_lag=args.snapshot_lag,
            )

        measurements = {
            name: _measure(
                function,
                warmup=args.warmup,
                samples=args.samples,
            )
            for name, function in (
                ("python_object_decode", decode_object),
                ("native_packed_decode", decode_packed),
                ("live_hybrid_decode", decode_live),
                ("python_object_projection", project_object),
                ("native_packed_projection", project_packed),
                ("python_object_end_to_end", object_end_to_end),
                ("native_packed_end_to_end", packed_end_to_end),
                ("live_hybrid_end_to_end", live_end_to_end),
            )
        }
        python_end = measurements["python_object_end_to_end"]
        native_end = measurements["live_hybrid_end_to_end"]
        results.append(
            {
                "active_bullets": density,
                "field_parity": field_parity,
                "projection_parity": projection_parity,
                "measurements": measurements,
                "end_to_end_median_speedup": (
                    python_end["median_ms"]
                    / native_end["median_ms"]
                ),
                "end_to_end_p95_reduction_percent": (
                    (
                        python_end["p95_ms"]
                        - native_end["p95_ms"]
                    )
                    / python_end["p95_ms"]
                    * 100.0
                ),
            }
        )

    output = {
        "schema": "th08-native-packed-bullet-decode-benchmark-v1",
        "scope": (
            "Synthetic TH08 fixed-stride bullet pools. Timings include "
            "slot-state scan and owned output allocation. Projection covers "
            "the local planner's constant-velocity SoA timeline. ECL tagged "
            "velocity-event attachment and diagnostic transform queues are "
            "outside this boundary."
        ),
        "horizon": args.horizon,
        "snapshot_lag": args.snapshot_lag,
        "native_packed_minimum_active_count": (
            NATIVE_PACKED_BULLET_MIN_COUNT
        ),
        "warmup": args.warmup,
        "samples": args.samples,
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
