#!/usr/bin/env python3
"""Benchmark the capture-aligned TH08 ECL VM-local projection."""

from __future__ import annotations

import argparse
import gc
import json
import platform
import statistics
import struct
import sys
import time
from pathlib import Path

from th08_ecl_runtime import (
    ECL_VM_CALLBACK_ANGLE_OFFSET,
    ECL_VM_CALLBACK_SPEED_OFFSET,
    ECL_VM_SNAPSHOT_SIZE,
    ECL_VM_TAG_MASK_OFFSET,
    ECL_VM_TIMER_ELAPSED_OFFSET,
    ECL_VM_TIMER_FRACTION_OFFSET,
)
from th08_ecl_vm_state import (
    ECL_VM_FLOAT_LOCALS_OFFSET,
    ECL_VM_INTEGER_LOCALS_OFFSET,
    ECL_VM_LOCAL_PROJECTION_SIZE,
    ECL_VM_SCRATCH_INTEGERS_OFFSET,
    EclVmLocalProjection,
)


SCHEMA = "th08-ecl-vm-projection-benchmark-v1"
LEGACY_CAPTURE_BYTES = 0x40


def _legacy_decode(vm: bytes) -> tuple[int, int, int, int, int, int]:
    """Decode the legacy VM fields with float values represented as raw bits."""

    return (
        struct.unpack_from("<I", vm, 0)[0],
        struct.unpack_from("<I", vm, ECL_VM_TIMER_FRACTION_OFFSET)[0],
        struct.unpack_from("<i", vm, ECL_VM_TIMER_ELAPSED_OFFSET)[0],
        struct.unpack_from("<I", vm, ECL_VM_TAG_MASK_OFFSET)[0],
        struct.unpack_from("<I", vm, ECL_VM_CALLBACK_ANGLE_OFFSET)[0],
        struct.unpack_from("<I", vm, ECL_VM_CALLBACK_SPEED_OFFSET)[0],
    )


def _projection_decode(
    vm: bytes,
) -> tuple[tuple[int, int, int, int, int, int], EclVmLocalProjection]:
    projection = EclVmLocalProjection.from_vm_bytes(vm)
    compatibility_fields = (
        struct.unpack_from("<I", vm, 0)[0],
        struct.unpack_from("<I", vm, ECL_VM_TIMER_FRACTION_OFFSET)[0],
        struct.unpack_from("<i", vm, ECL_VM_TIMER_ELAPSED_OFFSET)[0],
        projection.integer_locals[0] & 0xFFFFFFFF,
        projection.float_local_bits[0],
        projection.float_local_bits[1],
    )
    return compatibility_fields, projection


def _sample_ns(
    operation,
    *,
    batches: int,
    iterations_per_batch: int,
) -> tuple[list[float], object]:
    samples: list[float] = []
    result: object = None
    for _ in range(batches):
        started = time.perf_counter_ns()
        for _ in range(iterations_per_batch):
            result = operation()
        elapsed = time.perf_counter_ns() - started
        samples.append(elapsed / iterations_per_batch)
    return samples, result


def _timing_record(samples_ns: list[float]) -> dict[str, float]:
    ordered = sorted(samples_ns)
    p95_index = round((len(ordered) - 1) * 0.95)
    return {
        "median_ns_per_decode": statistics.median(samples_ns),
        "p95_ns_per_decode": ordered[p95_index],
        "max_ns_per_decode": max(samples_ns),
    }


def _fixture() -> bytes:
    vm = bytearray(ECL_VM_LOCAL_PROJECTION_SIZE)
    struct.pack_into("<I", vm, 0, 0x0B1D6FCC)
    struct.pack_into("<f", vm, ECL_VM_TIMER_FRACTION_OFFSET, 0.25)
    struct.pack_into("<i", vm, ECL_VM_TIMER_ELAPSED_OFFSET, 200)
    struct.pack_into(
        "<8i",
        vm,
        ECL_VM_INTEGER_LOCALS_OFFSET,
        0x100000,
        -1,
        2,
        -3,
        4,
        -5,
        6,
        -7,
    )
    struct.pack_into(
        "<8I",
        vm,
        ECL_VM_FLOAT_LOCALS_OFFSET,
        0x3F490FDB,
        0x3FC00000,
        0x80000000,
        0x7FC12345,
        0x7F800000,
        0xFF800000,
        0x00000001,
        0xFFFFFFFF,
    )
    struct.pack_into(
        "<4i",
        vm,
        ECL_VM_SCRATCH_INTEGERS_OFFSET,
        9,
        8,
        7,
        6,
    )
    return bytes(vm)


def run_benchmark(
    *,
    batches: int,
    iterations_per_batch: int,
) -> dict[str, object]:
    if batches <= 0 or iterations_per_batch <= 0:
        raise ValueError("benchmark counts must be positive")
    vm = _fixture()
    reference = _legacy_decode(vm)
    projected_fields, projection = _projection_decode(vm)
    legacy_samples, legacy_result = _sample_ns(
        lambda: _legacy_decode(vm),
        batches=batches,
        iterations_per_batch=iterations_per_batch,
    )
    projection_samples, projection_result = _sample_ns(
        lambda: _projection_decode(vm),
        batches=batches,
        iterations_per_batch=iterations_per_batch,
    )
    projection_record = {
        "vm_local_projection": projection.trace_record(),
    }
    compact_projection = json.dumps(
        projection_record,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")

    gates = {
        "compatibility_fields_bit_exact": projected_fields == reference,
        "legacy_benchmark_stable": legacy_result == reference,
        "projection_benchmark_stable": (
            isinstance(projection_result, tuple)
            and projection_result[0] == reference
            and projection_result[1] == projection
        ),
        "one_call_capture_size_is_104": (
            ECL_VM_SNAPSHOT_SIZE
            == ECL_VM_LOCAL_PROJECTION_SIZE
            == 104
        ),
        "capture_growth_is_40_bytes": (
            ECL_VM_LOCAL_PROJECTION_SIZE - LEGACY_CAPTURE_BYTES == 40
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
            "batches": batches,
            "iterations_per_batch": iterations_per_batch,
            "total_decodes_per_variant": batches * iterations_per_batch,
        },
        "payload": {
            "legacy_vm_read_bytes": LEGACY_CAPTURE_BYTES,
            "projection_vm_read_bytes": ECL_VM_LOCAL_PROJECTION_SIZE,
            "vm_read_growth_bytes": (
                ECL_VM_LOCAL_PROJECTION_SIZE - LEGACY_CAPTURE_BYTES
            ),
            "compact_projection_trace_bytes": len(compact_projection),
        },
        "timing": {
            "legacy": _timing_record(legacy_samples),
            "projection": _timing_record(projection_samples),
        },
        "gates": gates,
        "passed": all(gates.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batches", type=int, default=40)
    parser.add_argument("--iterations-per-batch", type=int, default=10_000)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    report = run_benchmark(
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
