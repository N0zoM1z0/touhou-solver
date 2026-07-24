#!/usr/bin/env python3
"""Benchmark planning and diagnostic TH08 bullet-pool decoding."""

from __future__ import annotations

import argparse
import json
import statistics
import struct
import timeit
from pathlib import Path

from th08_live_dodge_agent import (
    BULLET_ANGLE_OFFSET,
    BULLET_GEOMETRY_OFFSET,
    BULLET_ORIGINAL_TRANSFORM_FLAGS_OFFSET,
    BULLET_POOL_SIZE,
    BULLET_POSITION_OFFSET,
    BULLET_SPEED_OFFSET,
    BULLET_STATE_OFFSET,
    BULLET_STRIDE,
    BULLET_TRANSFORM_QUEUE_CURSOR_OFFSET,
    BULLET_VELOCITY_OFFSET,
    PLANNING_BULLET_VECTOR_THRESHOLD,
    decode_bullets,
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
            4.0,
            6.0,
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
            1.0,
            -1.0,
        )
        struct.pack_into(
            "<f",
            blob,
            base + BULLET_SPEED_OFFSET,
            1.414,
        )
        struct.pack_into(
            "<f",
            blob,
            base + BULLET_ANGLE_OFFSET,
            0.5,
        )
        struct.pack_into(
            "<I",
            blob,
            base + BULLET_ORIGINAL_TRANSFORM_FLAGS_OFFSET,
            0x00100202,
        )
        struct.pack_into(
            "<i",
            blob,
            base + BULLET_TRANSFORM_QUEUE_CURSOR_OFFSET,
            18,
        )
    return bytes(blob)


def _core(bullet) -> tuple[object, ...]:
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
        default=(200, 400, 600, 800, 1200),
    )
    parser.add_argument("--number", type=int, default=20)
    parser.add_argument("--repeat", type=int, default=7)
    args = parser.parse_args(argv)
    if (
        not args.densities
        or min(args.densities) < 0
        or max(args.densities) > BULLET_POOL_SIZE
        or args.number <= 0
        or args.repeat <= 0
    ):
        raise ValueError("invalid benchmark density or repeat count")

    results = []
    for density in args.densities:
        blob = _pool(density)
        diagnostic = decode_bullets(blob)
        planning = decode_bullets(
            blob,
            retain_transform_runtime=False,
        )
        parity = (
            len(diagnostic) == len(planning)
            and all(
                _core(left) == _core(right)
                for left, right in zip(diagnostic, planning)
            )
        )
        if not parity:
            raise AssertionError(
                f"planning decoder changed gameplay fields at density {density}"
            )

        def measure(retain: bool) -> dict[str, float]:
            samples = [
                elapsed / args.number * 1000.0
                for elapsed in timeit.repeat(
                    lambda: decode_bullets(
                        blob,
                        retain_transform_runtime=retain,
                    ),
                    number=args.number,
                    repeat=args.repeat,
                )
            ]
            return {
                "median_ms": statistics.median(samples),
                "max_repeat_ms": max(samples),
            }

        full = measure(True)
        compact = measure(False)
        results.append(
            {
                "active_bullets": density,
                "diagnostic_runtime": full,
                "planning_runtime": compact,
                "median_speedup": (
                    full["median_ms"] / compact["median_ms"]
                ),
                "gameplay_field_parity": parity,
            }
        )
    output = {
        "schema": "th08-bullet-decode-benchmark-v1",
        "scope": (
            "Synthetic allocated native-pool records with nonzero original "
            "transform tags and no pending queue record. Planning parity "
            "covers every field consumed by gameplay; diagnostic queue/stop "
            "state is deliberately excluded from the planning path."
        ),
        "number_per_repeat": args.number,
        "repeat_count": args.repeat,
        "planning_vector_threshold": PLANNING_BULLET_VECTOR_THRESHOLD,
        "results": results,
    }
    args.output.write_text(
        json.dumps(output, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
