#!/usr/bin/env python3
"""Benchmark the bounded native TH08 derived-pattern source shadow."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import struct
import sys
import time
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from th08_bullet_transform_model import TransformKind  # noqa: E402
from th08_live.bullet_birth import (  # noqa: E402
    BULLET_TIMER_CURRENT_OFFSET,
)
from th08_live.bullet_decode import (  # noqa: E402
    BULLET_ORIGINAL_TRANSFORM_FLAGS_OFFSET,
    BULLET_POSITION_OFFSET,
    BULLET_STATE_OFFSET,
    BULLET_STRIDE,
    BULLET_TRANSFORM_PROGRAM_OFFSET,
    BULLET_TRANSFORM_QUEUE_CURSOR_OFFSET,
)
from th08_live.derived_pattern_source import (  # noqa: E402
    TRANSFORM_RECORD_SIZE,
    observe_derived_pattern_sources,
)
from th08_live.derived_pattern_source_native import (  # noqa: E402
    NativeDerivedPatternSourceObserver,
)
from th08_live.sensor import BULLET_POOL_SIZE  # noqa: E402


P95_LIMIT_MS = 0.20
P99_LIMIT_MS = 0.40
MAX_LIMIT_MS = 2.00


def _percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("distribution is empty")
    rank = (len(ordered) - 1) * percentile / 100.0
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return ordered[lower]
    weight = rank - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _distribution(values: list[float]) -> dict[str, float | int]:
    return {
        "count": len(values),
        "p50": _percentile(values, 50.0),
        "p95": _percentile(values, 95.0),
        "p99": _percentile(values, 99.0),
        "p99_9": _percentile(values, 99.9),
        "max": max(values),
        "mean": statistics.fmean(values),
    }


def _source_pool(*, active_count: int, source_count: int) -> bytearray:
    if not 0 <= source_count <= active_count <= BULLET_POOL_SIZE:
        raise ValueError("invalid active/source count")
    blob = bytearray(BULLET_POOL_SIZE * BULLET_STRIDE)
    for slot in range(active_count):
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
            base + BULLET_POSITION_OFFSET,
            float(slot % 384),
            float(slot % 448),
        )
    first = struct.pack(
        "<ffiiII",
        0.25,
        0.75,
        0x01020304,
        3,
        int(TransformKind.EMIT_DERIVED_PATTERN),
        0,
    )
    second = struct.pack(
        "<ffiiII",
        1.25,
        2.5,
        1,
        0x200,
        int(TransformKind.DERIVED_PATTERN_PARAMETERS),
        0,
    )
    for slot in range(source_count):
        base = slot * BULLET_STRIDE
        struct.pack_into(
            "<I",
            blob,
            base + BULLET_ORIGINAL_TRANSFORM_FLAGS_OFFSET,
            int(TransformKind.EMIT_DERIVED_PATTERN),
        )
        struct.pack_into(
            "<i",
            blob,
            base + BULLET_TRANSFORM_QUEUE_CURSOR_OFFSET,
            3,
        )
        offset = (
            base
            + BULLET_TRANSFORM_PROGRAM_OFFSET
            + 3 * TRANSFORM_RECORD_SIZE
        )
        blob[offset : offset + TRANSFORM_RECORD_SIZE] = first
        blob[
            offset
            + TRANSFORM_RECORD_SIZE : offset
            + 2 * TRANSFORM_RECORD_SIZE
        ] = second
    return blob


def _digest(payload: dict[str, object]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--iterations", type=int, default=5_000)
    parser.add_argument("--warmup", type=int, default=200)
    parser.add_argument("--active-count", type=int, default=422)
    parser.add_argument("--source-count", type=int, default=5)
    parser.add_argument(
        "--native-call-mode",
        choices=("gil-released", "gil-held"),
        default="gil-held",
    )
    arguments = parser.parse_args(argv)
    if arguments.iterations <= 0 or arguments.warmup < 0:
        parser.error("iterations must be positive and warmup non-negative")

    blob = _source_pool(
        active_count=arguments.active_count,
        source_count=arguments.source_count,
    )
    scalar = observe_derived_pattern_sources(
        blob,
        frame_before=100,
        frame_after=100,
    )
    native = NativeDerivedPatternSourceObserver(
        native_call_mode=arguments.native_call_mode,
    )
    native_record = native.observe(
        blob,
        frame_before=100,
        frame_after=100,
    ).record()
    scalar_record = scalar.record()
    if native_record != scalar_record:
        raise RuntimeError("scalar/native derived-source mismatch")

    for _ in range(arguments.warmup):
        native.observe(blob, frame_before=100, frame_after=100)
    elapsed_ms: list[float] = []
    native_call_ms: list[float] = []
    materialize_ms: list[float] = []
    for _ in range(arguments.iterations):
        started = time.perf_counter()
        native.observe(blob, frame_before=100, frame_after=100)
        elapsed_ms.append((time.perf_counter() - started) * 1000.0)
        diagnostics = native.diagnostics()
        native_call_ms.append(diagnostics.native_call_ms)
        materialize_ms.append(diagnostics.materialize_ms)

    observe_total = _distribution(elapsed_ms)
    gate = {
        "p95_limit_ms": P95_LIMIT_MS,
        "p99_limit_ms": P99_LIMIT_MS,
        "max_limit_ms": MAX_LIMIT_MS,
        "p95_pass": observe_total["p95"] <= P95_LIMIT_MS,
        "p99_pass": observe_total["p99"] <= P99_LIMIT_MS,
        "max_pass": observe_total["max"] <= MAX_LIMIT_MS,
    }
    gate["passed"] = bool(
        gate["p95_pass"] and gate["p99_pass"] and gate["max_pass"]
    )
    report: dict[str, object] = {
        "schema": "th08-derived-pattern-source-benchmark-v1",
        "workload": {
            "active_count": arguments.active_count,
            "source_count": arguments.source_count,
            "iterations": arguments.iterations,
            "warmup": arguments.warmup,
            "native_call_mode": arguments.native_call_mode,
        },
        "parity": {
            "passed": True,
            "candidate_count": len(scalar.candidates),
            "record_sha256": _digest(scalar_record),
        },
        "timing_ms": {
            "observe_total": observe_total,
            "native_call": _distribution(native_call_ms),
            "materialize": _distribution(materialize_ms),
        },
        "gate": gate,
        "authority": "offline trace-shadow performance only",
        "passed": gate["passed"],
    }
    report["report_digest"] = _digest(report)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
