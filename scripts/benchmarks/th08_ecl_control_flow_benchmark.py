#!/usr/bin/env python3
"""Benchmark shipped Stage-4A callback lookahead control boundaries."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import platform
import statistics
import sys
import time
from pathlib import Path

from th08_ecl_runtime import (
    EclInstructionCache,
    EclVmSnapshot,
    analyze_tagged_velocity_toggles,
)


SCHEMA = "th08-ecl-control-flow-benchmark-v1"
DEFAULT_RUNTIME_BASE = 0x0B1C1430
WORKLOADS = (
    {
        "name": "spell57_frame10971",
        "offset": 0x331C,
        "timer_elapsed": 32,
        "tag_mask": 16,
        "expected_instructions": 26,
        "expected_stop_frame": 159,
    },
    {
        "name": "spell73_frame42279",
        "offset": 0x70DC,
        "timer_elapsed": 319,
        "tag_mask": 66,
        "expected_instructions": 3,
        "expected_stop_frame": 141,
    },
)


class _MappedEcl:
    def __init__(self, *, base: int, code: bytes) -> None:
        self.base = base
        self.code = code

    def read(self, address: int, size: int) -> bytes:
        start = address - self.base
        end = start + size
        if size <= 0 or start < 0 or end > len(self.code):
            raise OSError(f"invalid benchmark ECL read at {address:#x}")
        return self.code[start:end]


def _percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    index = min(
        len(ordered) - 1,
        max(0, int(round((len(ordered) - 1) * fraction))),
    )
    return ordered[index]


def run_benchmark(
    *,
    ecl_path: Path,
    iterations: int,
    runtime_base: int = DEFAULT_RUNTIME_BASE,
) -> dict[str, object]:
    if iterations <= 0:
        raise ValueError("iterations must be positive")
    code = ecl_path.read_bytes()
    mapped = _MappedEcl(base=runtime_base, code=code)
    records: list[dict[str, object]] = []
    gates: dict[str, bool] = {}

    for workload in WORKLOADS:
        cache = EclInstructionCache()
        snapshot = EclVmSnapshot(
            runtime_base + int(workload["offset"]),
            0.0,
            int(workload["timer_elapsed"]),
            int(workload["tag_mask"]),
            0.0,
            0.0,
            1.0,
        )

        def analyze():
            return analyze_tagged_velocity_toggles(
                snapshot,
                instruction_at=lambda address: cache.instruction(
                    mapped.read,
                    address,
                ),
                horizon_frames=256,
                active_difficulty_mask=0x08,
            )

        reference = analyze()
        samples_ms: list[float] = []
        for _ in range(iterations):
            started = time.perf_counter_ns()
            result = analyze()
            samples_ms.append((time.perf_counter_ns() - started) / 1_000_000)
            if result != reference:
                raise RuntimeError("lookahead result changed during benchmark")

        name = str(workload["name"])
        gate = (
            reference.stop_reason == "unsupported_control_flow"
            and reference.coverage_status == "unknown"
            and reference.complete_events is None
            and reference.instructions_scanned
            == int(workload["expected_instructions"])
            and reference.stop_frame == int(workload["expected_stop_frame"])
        )
        gates[name] = gate
        records.append(
            {
                "name": name,
                "snapshot": {
                    "instruction_pointer": (
                        f"0x{snapshot.instruction_pointer:08X}"
                    ),
                    "decoded_offset": f"0x{int(workload['offset']):X}",
                    "timer_elapsed": snapshot.timer_elapsed,
                    "tag_mask": snapshot.tag_mask,
                    "horizon_frames": 256,
                    "active_difficulty_mask": 0x08,
                },
                "result": {
                    "instructions_scanned": reference.instructions_scanned,
                    "stop_reason": reference.stop_reason,
                    "stop_frame": reference.stop_frame,
                    "coverage_status": reference.coverage_status,
                    "prefix_event_count": len(reference.events),
                    "lowered_event_count": (
                        None
                        if reference.complete_events is None
                        else len(reference.complete_events)
                    ),
                },
                "timing_ms": {
                    "median": statistics.median(samples_ms),
                    "p95": _percentile(samples_ms, 0.95),
                    "max": max(samples_ms),
                },
                "passed": gate,
            }
        )

    return {
        "schema": SCHEMA,
        "environment": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "python": sys.version,
            "gc_enabled": gc.isenabled(),
        },
        "input": {
            "ecl_name": ecl_path.name,
            "ecl_sha256": hashlib.sha256(code).hexdigest(),
            "runtime_base": f"0x{runtime_base:08X}",
            "iterations": iterations,
        },
        "workloads": records,
        "gates": gates,
        "passed": all(gates.values()),
    }


def _parse_int(value: str) -> int:
    return int(value, 0)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ecl", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=10_000)
    parser.add_argument(
        "--runtime-base",
        type=_parse_int,
        default=DEFAULT_RUNTIME_BASE,
    )
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    report = run_benchmark(
        ecl_path=arguments.ecl,
        iterations=arguments.iterations,
        runtime_base=arguments.runtime_base,
    )
    encoded = json.dumps(
        report,
        indent=2,
        sort_keys=True,
        allow_nan=False,
    ) + "\n"
    if arguments.output is None:
        print(encoded, end="")
    else:
        arguments.output.write_text(encoded, encoding="utf-8", newline="\n")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
