#!/usr/bin/env python3
"""Benchmark allocating versus persistent ReadProcessMemory destinations."""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import platform
import statistics
import time
from pathlib import Path

from th08_runtime_agent import ProcessReader, Win32


def _percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    position = fraction * (len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _summary(values: list[float]) -> dict[str, float | int]:
    return {
        "count": len(values),
        "median_ms": statistics.median(values),
        "p95_ms": _percentile(values, 0.95),
        "max_ms": max(values),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--size", type=int, default=1536 * 0x10B8)
    parser.add_argument("--pairs", type=int, default=64)
    parser.add_argument("--warmup", type=int, default=4)
    args = parser.parse_args(argv)
    if min(args.size, args.pairs, args.warmup) <= 0:
        raise ValueError("size, pairs, and warmup must be positive")

    api = Win32()
    reader = ProcessReader(api, os.getpid())
    source = ctypes.create_string_buffer(args.size)
    ctypes.memset(source, 0xA5, args.size)
    source_address = ctypes.addressof(source)
    destination = reader.allocate_buffer(args.size)
    try:
        for _ in range(args.warmup):
            reader.read(source_address, args.size)
            reader.read_into(source_address, destination)

        allocating_ms: list[float] = []
        persistent_ms: list[float] = []
        for pair in range(args.pairs):
            order = (
                ("allocating_bytes", "persistent_buffer")
                if pair % 2 == 0
                else ("persistent_buffer", "allocating_bytes")
            )
            for method in order:
                started = time.perf_counter()
                if method == "allocating_bytes":
                    reader.read(source_address, args.size)
                else:
                    reader.read_into(source_address, destination)
                elapsed_ms = (time.perf_counter() - started) * 1000.0
                (
                    allocating_ms
                    if method == "allocating_bytes"
                    else persistent_ms
                ).append(elapsed_ms)

        allocating_blob = reader.read(source_address, args.size)
        reader.read_into(source_address, destination)
        persistent_blob = destination.raw
        parity = allocating_blob == persistent_blob
        if not parity:
            raise AssertionError("persistent ReadProcessMemory buffer changed bytes")
        allocating = _summary(allocating_ms)
        persistent = _summary(persistent_ms)
        output = {
            "schema": "th08-process-read-buffer-benchmark-v1",
            "scope": (
                "Paired alternating Windows ReadProcessMemory calls against "
                "the benchmark process itself. allocating_bytes includes a "
                "new ctypes destination and bytes copy; persistent_buffer "
                "reuses one writable ctypes destination and exposes it "
                "directly to decoders. This isolates host implementation "
                "overhead and is not a cross-process game timing claim."
            ),
            "platform": platform.platform(),
            "size_bytes": args.size,
            "pair_count": args.pairs,
            "warmup_count": args.warmup,
            "byte_parity": parity,
            "sha256": hashlib.sha256(allocating_blob).hexdigest(),
            "allocating_bytes": allocating,
            "persistent_buffer": persistent,
            "median_speedup": (
                float(allocating["median_ms"])
                / float(persistent["median_ms"])
            ),
            "p95_speedup": (
                float(allocating["p95_ms"])
                / float(persistent["p95_ms"])
            ),
        }
    finally:
        reader.close()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
