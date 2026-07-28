#!/usr/bin/env python3
"""Benchmark exact one-step ECL VM-local shadow transitions."""

from __future__ import annotations

import argparse
import dis
import gc
import json
import platform
import statistics
import struct
import sys
import time
from pathlib import Path
from types import FrameType

from th08_ecl_runtime import EclVmSnapshot, RuntimeEclInstruction
from th08_ecl_shadow import (
    EclVmLocalShadowResult,
    interpret_vm_local_shadow,
)
from th08_ecl_vm_state import EclVmLocalProjection


SCHEMA = "th08-ecl-vm-local-shadow-benchmark-v1"


def _percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    index = round((len(ordered) - 1) * fraction)
    return ordered[index]


def _summary(values: list[float]) -> dict[str, float | int]:
    return {
        "count": len(values),
        "p50": statistics.median(values),
        "p95": _percentile(values, 0.95),
        "p99": _percentile(values, 0.99),
        "max": max(values),
    }


def _workload(
    case: dict[str, object],
    *,
    runtime_base: int,
) -> tuple[EclVmSnapshot, RuntimeEclInstruction]:
    address = runtime_base + int(case["instruction_offset"])
    arguments = tuple(int(value) for value in case["arguments"])
    instruction = RuntimeEclInstruction(
        address=address,
        time=int(case["instruction_time"]),
        opcode=0x05,
        size=int(case["instruction_size"]),
        difficulty_mask=int(case["difficulty_mask"]),
        parameter_mask=int(case["parameter_mask"]),
        payload=struct.pack("<3i", *arguments),
    )
    projection = EclVmLocalProjection(
        (16, 1, 2, 3, 4, 5, 6, 7),
        (0, 0, 2, 3, 4, 5, 6, 7),
        (int(case["counter_before"]), 8, 7, 6),
    )
    snapshot = EclVmSnapshot(
        address,
        float(case["timer_fraction"]),
        int(case["timer_elapsed"]),
        16,
        0.0,
        0.0,
        float(case["time_scale"]),
        projection,
    )
    return snapshot, instruction


def _run_one(
    workload: tuple[EclVmSnapshot, RuntimeEclInstruction],
) -> EclVmLocalShadowResult:
    snapshot, instruction = workload
    return interpret_vm_local_shadow(
        snapshot,
        instruction_at=lambda _address: instruction,
        horizon_frames=256,
        active_difficulty_mask=0x08,
        max_instructions=1,
    )


def _result_matches(
    case: dict[str, object],
    result: EclVmLocalShadowResult,
) -> bool:
    projection = result.final_projection
    return (
        projection is not None
        and result.instructions_scanned == 1
        and result.stop_reason == "instruction_limit"
        and result.final_instruction_pointer
        == int(case["runtime_base"]) + int(case["expected_pc_offset"])
        and result.final_timer_value == float(case["expected_timer"])
        and result.stop_frame == int(case["expected_stop_frame"])
        and projection.integer_value(int(case["variable"]))
        == int(case["counter_after"])
    )


def _count_shadow_bytecode_ops(
    workload: tuple[EclVmSnapshot, RuntimeEclInstruction],
) -> int:
    count = 0

    def trace(
        frame: FrameType,
        event: str,
        _argument: object,
    ) -> object:
        nonlocal count
        normalized = frame.f_code.co_filename.replace("\\", "/")
        if event == "call" and "/th08_ecl_shadow/" in normalized:
            frame.f_trace_opcodes = True
            return trace
        if event == "opcode" and "/th08_ecl_shadow/" in normalized:
            count += 1
        return trace

    sys.settrace(trace)
    try:
        _run_one(workload)
    finally:
        sys.settrace(None)
    return count


def run_benchmark(
    *,
    fixture_path: Path,
    batches: int,
    iterations_per_batch: int,
) -> dict[str, object]:
    if batches <= 0 or iterations_per_batch <= 0:
        raise ValueError("benchmark counts must be positive")
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    source = fixture["source"]
    runtime_base = int(source["runtime_base"])
    cases = fixture["cases"]
    workloads = [
        _workload(case, runtime_base=runtime_base) for case in cases
    ]
    augmented_cases = [
        {**case, "runtime_base": runtime_base} for case in cases
    ]
    references = [_run_one(workload) for workload in workloads]
    exact = all(
        _result_matches(case, result)
        for case, result in zip(augmented_cases, references, strict=True)
    )
    bytecode_ops = [
        float(_count_shadow_bytecode_ops(workload))
        for workload in workloads
    ]

    samples_ns: list[float] = []
    last_results = references
    for _ in range(batches):
        started = time.perf_counter_ns()
        for _ in range(iterations_per_batch):
            last_results = [
                _run_one(workload) for workload in workloads
            ]
        elapsed = time.perf_counter_ns() - started
        samples_ns.append(
            elapsed / (iterations_per_batch * len(workloads))
        )
    stable = last_results == references
    gates = {
        "fixture_schema_valid": (
            fixture.get("schema") == "th08-ecl-vm-local-op05-cases-v1"
        ),
        "all_108_unique_cases_loaded": len(cases) == 108,
        "all_reference_results_exact": exact,
        "timed_results_stable": stable,
        "one_logical_instruction_per_transition": all(
            result.instructions_scanned == 1 for result in references
        ),
    }
    return {
        "schema": SCHEMA,
        "environment": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "python": sys.version,
            "gc_enabled": gc.isenabled(),
        },
        "input": {
            "fixture_name": fixture_path.name,
            "unique_cases": len(cases),
            "batches": batches,
            "iterations_per_batch": iterations_per_batch,
            "total_transitions": (
                len(cases) * batches * iterations_per_batch
            ),
        },
        "logical_work": {
            "vm_instructions_per_transition": 1,
            "python_bytecode_scope": "scripts/th08_ecl_shadow package",
            "python_bytecode_ops_per_transition": _summary(bytecode_ops),
            "interpreter_function_bytecode_instructions": len(
                list(dis.get_instructions(interpret_vm_local_shadow))
            ),
        },
        "timing": {
            "ns_per_transition": _summary(samples_ns),
        },
        "gates": gates,
        "passed": all(gates.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--batches", type=int, default=30)
    parser.add_argument("--iterations-per-batch", type=int, default=100)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    report = run_benchmark(
        fixture_path=arguments.fixture,
        batches=arguments.batches,
        iterations_per_batch=arguments.iterations_per_batch,
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
