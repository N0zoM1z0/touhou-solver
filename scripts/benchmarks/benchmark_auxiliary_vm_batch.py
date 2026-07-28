#!/usr/bin/env python3
"""Benchmark the bounded native TH08 auxiliary-VM fixture batch."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import statistics
import struct
import sys
import time
from dataclasses import dataclass
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from th08_live.auxiliary_vm import (  # noqa: E402
    NativeAuxiliaryVmBatchCapture,
    decode_auxiliary_vm_batch_fixture,
)
from th08_live.auxiliary_vm.model import (  # noqa: E402
    ACTIVE_VM_AUXILIARY_MARKER_OFFSET,
    ACTIVE_VM_BYTES,
    CONTEXT_BYTES,
    MAXIMUM_STATE_PAYLOAD_BYTES,
    SAVED_FRAME_BASE_OFFSET,
)


ARENA_BASE = 0x02100000
POOL_BASE = 0x005826C0
ENEMY_STRIDE = 0x53D0
ENEMY_FLAGS_OFFSET = 0x3324
CONTEXT_POINTER_OFFSET = 0x3384
P95_LIMIT_MS = 2.0
P99_LIMIT_MS = 4.0
MAX_LIMIT_MS = 12.0


@dataclass(frozen=True, slots=True)
class Workload:
    name: str
    active_owners: int
    non_null_contexts: int
    depths: tuple[int, ...]
    required_for_preflight: bool


WORKLOADS = (
    Workload("stage5_observed_p95_density", 7, 26, (0, 1), True),
    Workload("contract_34_context_depth0", 9, 34, (0,), True),
    Workload(
        "stage5_observed_max_density_depth15",
        9,
        34,
        (15,),
        True,
    ),
    Workload(
        "contract_256_context_depth15",
        64,
        256,
        (15,),
        False,
    ),
)


def _percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
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
        "max": max(values),
        "mean": statistics.fmean(values),
    }


def _digest(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _context(*, depth: int, auxiliary_index: int, serial: int) -> bytes:
    context = bytearray(CONTEXT_BYTES)
    struct.pack_into("<I", context, 0, 54 + serial)
    struct.pack_into("<h", context, 6, depth)
    struct.pack_into("<I", context, 8, 0x03100000 + serial * 0x20)
    struct.pack_into(
        "<I",
        context,
        8 + ACTIVE_VM_AUXILIARY_MARKER_OFFSET,
        auxiliary_index + 1,
    )
    for frame in range(16):
        base = SAVED_FRAME_BASE_OFFSET + frame * ACTIVE_VM_BYTES
        struct.pack_into(
            "<I",
            context,
            base,
            0x03500000 + serial * 0x200 + frame * 0x10,
        )
        context[base + 4 : base + ACTIVE_VM_BYTES] = bytes(
            [(serial + frame) & 0xFF]
        ) * (ACTIVE_VM_BYTES - 4)
    return bytes(context)


def _fixture(workload: Workload) -> tuple[bytes, bytes]:
    if not (
        0 <= workload.active_owners <= 64
        and 0 <= workload.non_null_contexts
        <= workload.active_owners * 4
    ):
        raise ValueError("invalid auxiliary-VM benchmark workload")
    owner = bytearray(workload.active_owners * ENEMY_STRIDE)
    arena = bytearray(workload.non_null_contexts * CONTEXT_BYTES)
    context_index = 0
    for slot in range(workload.active_owners):
        base = slot * ENEMY_STRIDE
        struct.pack_into("<I", owner, base + ENEMY_FLAGS_OFFSET, 1)
        pointers = [0, 0, 0, 0]
        for auxiliary_index in range(4):
            if context_index >= workload.non_null_contexts:
                break
            pointer = ARENA_BASE + context_index * CONTEXT_BYTES
            pointers[auxiliary_index] = pointer
            depth = workload.depths[context_index % len(workload.depths)]
            context = _context(
                depth=depth,
                auxiliary_index=auxiliary_index,
                serial=context_index,
            )
            start = context_index * CONTEXT_BYTES
            arena[start : start + CONTEXT_BYTES] = context
            context_index += 1
        struct.pack_into(
            "<4I",
            owner,
            base + CONTEXT_POINTER_OFFSET,
            *pointers,
        )
    return bytes(owner), bytes(arena)


def _arguments(workload: Workload) -> dict[str, int]:
    return {
        "arena_base": ARENA_BASE,
        "pool_base": POOL_BASE,
        "record_count": workload.active_owners,
        "enemy_stride": ENEMY_STRIDE,
        "enemy_flags_offset": ENEMY_FLAGS_OFFSET,
        "enemy_active_flag": 1,
        "context_pointer_offset": CONTEXT_POINTER_OFFSET,
        "expected_manager_frame": 100,
        "manager_frame_before": 100,
        "manager_frame_after": 100,
        "output_payload_capacity": MAXIMUM_STATE_PAYLOAD_BYTES,
    }


def _benchmark_workload(
    capture: NativeAuxiliaryVmBatchCapture,
    workload: Workload,
    *,
    iterations: int,
    warmup: int,
) -> dict[str, object]:
    owner, arena = _fixture(workload)
    arguments = _arguments(workload)
    scalar = decode_auxiliary_vm_batch_fixture(
        owner,
        owner,
        arena,
        arena,
        **arguments,
    )
    native = capture.decode_fixture(
        owner,
        owner,
        arena,
        arena,
        **arguments,
    )
    if native != scalar:
        raise RuntimeError(f"{workload.name}: scalar/native parity failed")
    for _ in range(warmup):
        capture.decode_fixture(owner, owner, arena, arena, **arguments)

    total_ms: list[float] = []
    native_ms: list[float] = []
    materialize_ms: list[float] = []
    for _ in range(iterations):
        started = time.perf_counter()
        observation = capture.decode_fixture(
            owner,
            owner,
            arena,
            arena,
            **arguments,
        )
        total_ms.append((time.perf_counter() - started) * 1000.0)
        diagnostics = capture.diagnostics()
        native_ms.append(diagnostics.native_call_ms)
        materialize_ms.append(diagnostics.materialize_ms)
    if observation != native:
        raise RuntimeError(f"{workload.name}: repeated output changed")

    total = _distribution(total_ms)
    gate = {
        "p95_limit_ms": P95_LIMIT_MS,
        "p99_limit_ms": P99_LIMIT_MS,
        "max_limit_ms": MAX_LIMIT_MS,
        "p95_pass": total["p95"] <= P95_LIMIT_MS,
        "p99_pass": total["p99"] <= P99_LIMIT_MS,
        "max_pass": total["max"] <= MAX_LIMIT_MS,
    }
    gate["passed"] = all(
        gate[key]
        for key in ("p95_pass", "p99_pass", "max_pass")
    )
    return {
        "name": workload.name,
        "active_owner_count": workload.active_owners,
        "non_null_context_count": workload.non_null_contexts,
        "depth_cycle": list(workload.depths),
        "required_for_preflight": workload.required_for_preflight,
        "record_count": len(native.records),
        "state_payload_bytes": native.state_payload_bytes,
        "process_read_count_fixture_schedule": native.process_read_count,
        "parity": {
            "passed": True,
            "compact_record_sha256": _digest(native.compact_record()),
        },
        "timing_ms": {
            "end_to_end": total,
            "native_fixture_call": _distribution(native_ms),
            "python_materialize": _distribution(materialize_ms),
        },
        "preflight_gate": gate,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--iterations", type=int, default=500)
    parser.add_argument("--warmup", type=int, default=30)
    parser.add_argument(
        "--native-call-mode",
        choices=("gil-released", "gil-held"),
        default="gil-held",
    )
    arguments = parser.parse_args(argv)
    if arguments.iterations <= 0 or arguments.warmup < 0:
        parser.error("iterations must be positive and warmup non-negative")

    capture = NativeAuxiliaryVmBatchCapture(
        call_mode=arguments.native_call_mode
    )
    results: list[dict[str, object]] = []
    passed = True
    for workload in WORKLOADS:
        result = _benchmark_workload(
            capture,
            workload,
            iterations=arguments.iterations,
            warmup=arguments.warmup,
        )
        results.append(result)
        gate = result["preflight_gate"]
        if (
            workload.required_for_preflight
            and isinstance(gate, dict)
            and not bool(gate["passed"])
        ):
            passed = False
    report: dict[str, object] = {
        "schema": "th08-auxiliary-vm-batch-benchmark-v1",
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python": platform.python_version(),
        },
        "workload": {
            "iterations_per_case": arguments.iterations,
            "warmup_per_case": arguments.warmup,
            "native_call_mode": arguments.native_call_mode,
        },
        "timing_boundary": {
            "includes": (
                "ctypes pointer preparation, one fixture FFI call, bounded "
                "native local-memory reads/validation, and Python raw-byte "
                "materialization"
            ),
            "excludes": (
                "game-process ReadProcessMemory latency, owner-pool capture, "
                "compact hashing, JSON serialization, planning, and input"
            ),
            "interpretation": (
                "cross-platform deterministic preflight only; the Windows "
                "game-process physical contention gate remains required"
            ),
        },
        "results": results,
        "authority": "offline trace-only preflight; no live action authority",
        "passed": passed,
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
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
