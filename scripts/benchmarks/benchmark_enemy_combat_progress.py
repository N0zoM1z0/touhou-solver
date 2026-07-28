#!/usr/bin/env python3
"""Benchmark the trace-only first-64 enemy combat-progress inventory."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import statistics
import struct

from th08_boss_phase import (
    ENEMY_CURRENT_HEALTH_OFFSET,
    ENEMY_FLAGS_OFFSET,
    ENEMY_FRAME_DAMAGE_OFFSET,
)
from th08_live.enemy_combat_progress import (
    build_enemy_combat_progress_record,
    decode_enemy_combat_progress_inventory,
)
from th08_live.enemy_sensor import (
    ENEMY_ACTIVE_FLAG,
    ENEMY_POOL_BASE,
    ENEMY_STRIDE,
)


SCHEMA = "th08-enemy-combat-progress-benchmark-v1"
DEFAULT_ITERATIONS = 10_000
POOL_SIZE = 64


def _percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(fraction * len(ordered)))
    return ordered[index]


def _summary(values: list[float]) -> dict[str, float]:
    return {
        "median": statistics.median(values),
        "p95": _percentile(values, 0.95),
        "p99": _percentile(values, 0.99),
        "max": max(values),
    }


def _fixture() -> bytes:
    blob = bytearray(POOL_SIZE * ENEMY_STRIDE)
    for slot in range(POOL_SIZE):
        base = slot * ENEMY_STRIDE
        flags = ENEMY_ACTIVE_FLAG | 0x40 | ((slot % 4) << 20)
        struct.pack_into(
            "<iii",
            blob,
            base + ENEMY_CURRENT_HEALTH_OFFSET,
            1000 - slot,
            1000,
            1000,
        )
        struct.pack_into("<II", blob, base + ENEMY_FLAGS_OFFSET, flags, 0)
        struct.pack_into(
            "<i",
            blob,
            base + ENEMY_FRAME_DAMAGE_OFFSET,
            slot % 17,
        )
    return bytes(blob)


def benchmark(iterations: int) -> dict[str, object]:
    if iterations <= 0:
        raise ValueError("iterations must be positive")
    blob = _fixture()
    decode_ms: list[float] = []
    record_ms: list[float] = []
    digest = hashlib.sha256()
    for _ in range(iterations):
        inventory = decode_enemy_combat_progress_inventory(
            blob,
            pool_base=ENEMY_POOL_BASE,
            pool_size=POOL_SIZE,
            enemy_stride=ENEMY_STRIDE,
            enemy_active_flag=ENEMY_ACTIVE_FLAG,
        )
        record = build_enemy_combat_progress_record(inventory)
        decode_ms.append(inventory.decode_ms)
        record_ms.append(float(record["record_ms"]))
    canonical = {
        key: value
        for key, value in record.items()
        if key not in {"decode_ms", "record_ms"}
    }
    digest.update(
        json.dumps(
            canonical,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    )
    return {
        "schema": SCHEMA,
        "platform": platform.platform(),
        "python": platform.python_version(),
        "iterations": iterations,
        "pool_size": POOL_SIZE,
        "active_slots": int(record["active_slots"]),
        "decode_ms": _summary(decode_ms),
        "record_ms": _summary(record_ms),
        "canonical_record_sha256": digest.hexdigest(),
        "limits_ms": {
            "p95": 0.10,
            "p99": 0.20,
            "max": 2.00,
        },
        "passed": (
            _percentile(decode_ms, 0.95) <= 0.10
            and _percentile(decode_ms, 0.99) <= 0.20
            and max(decode_ms) <= 2.00
            and _percentile(record_ms, 0.95) <= 0.10
            and _percentile(record_ms, 0.99) <= 0.20
            and max(record_ms) <= 2.00
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--iterations",
        type=int,
        default=DEFAULT_ITERATIONS,
    )
    args = parser.parse_args()
    report = benchmark(args.iterations)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
