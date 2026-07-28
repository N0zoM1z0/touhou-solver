#!/usr/bin/env python3
"""Benchmark the opt-in ordinary-enemy main-VM inventory decoder."""

from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import platform
import struct
import time

from th08_live.enemy_ecl_inventory import (
    ENEMY_AUXILIARY_ECL_CONTEXT_POINTERS_OFFSET,
    decode_enemy_main_ecl_vm_inventory,
)
from th08_live.enemy_sensor import (
    ENEMY_ACTIVE_FLAG,
    ENEMY_FLAGS_OFFSET,
    ENEMY_LOCAL_PREFIX_SIZE,
    ENEMY_POOL_BASE,
    ENEMY_STRIDE,
    decode_enemy_bodies,
)


SCHEMA = "th08-enemy-main-ecl-vm-inventory-benchmark-v2"


def _fixture(*, active_slots: int, invalid_slots: int) -> bytes:
    if not 0 <= invalid_slots <= active_slots <= ENEMY_LOCAL_PREFIX_SIZE:
        raise ValueError("invalid active/invalid slot counts")
    blob = bytearray(ENEMY_LOCAL_PREFIX_SIZE * ENEMY_STRIDE)
    for slot in range(active_slots):
        base = slot * ENEMY_STRIDE
        struct.pack_into("<I", blob, base + ENEMY_FLAGS_OFFSET, 5)
        instruction_pointer = (
            0
            if slot < invalid_slots
            else 0x015A0000 + slot * 0x40
        )
        struct.pack_into("<I", blob, base + 0x07F8, instruction_pointer)
        struct.pack_into("<I", blob, base + 0x0800, 0x3E800000 + slot)
        struct.pack_into("<i", blob, base + 0x0804, slot * 3)
        struct.pack_into(
            "<8i",
            blob,
            base + 0x0810,
            *(slot * 16 + index for index in range(8)),
        )
        struct.pack_into(
            "<8I",
            blob,
            base + 0x0830,
            *(0x3F000000 + slot * 16 + index for index in range(8)),
        )
        struct.pack_into(
            "<4i",
            blob,
            base + 0x0850,
            *(slot * 4 + index for index in range(4)),
        )
        auxiliary_pointers = tuple(
            (
                0x02000000 + (slot * 4 + index) * 0x24B0
                if index <= slot % 4
                else 0
            )
            for index in range(4)
        )
        struct.pack_into(
            "<4I",
            blob,
            base + ENEMY_AUXILIARY_ECL_CONTEXT_POINTERS_OFFSET,
            *auxiliary_pointers,
        )
        struct.pack_into("<ff", blob, base + 0x2D4C, 1.0, -1.0)
        struct.pack_into("<ff", blob, base + 0x2D70, 8.0, 8.0)
        struct.pack_into(
            "<ff",
            blob,
            base + 0x2D88,
            64.0 + slot,
            128.0,
        )
    return bytes(blob)


def _distribution(values: list[float]) -> dict[str, float]:
    ordered = sorted(values)

    def percentile(fraction: float) -> float:
        index = (len(ordered) - 1) * fraction
        lower = int(index)
        upper = min(lower + 1, len(ordered) - 1)
        weight = index - lower
        return ordered[lower] * (1.0 - weight) + ordered[upper] * weight

    return {
        "p50": percentile(0.50),
        "p95": percentile(0.95),
        "p99": percentile(0.99),
        "p99_9": percentile(0.999),
        "max": ordered[-1],
    }


def run_benchmark(
    *,
    iterations: int,
    warmup: int,
    active_slots: int,
    invalid_slots: int,
) -> dict[str, object]:
    if iterations <= 0 or warmup < 0:
        raise ValueError("iteration counts must be positive/non-negative")
    blob = _fixture(
        active_slots=active_slots,
        invalid_slots=invalid_slots,
    )

    def decode_inventory(*, include_auxiliary_context_pointers: bool):
        return decode_enemy_main_ecl_vm_inventory(
            blob,
            pool_base=ENEMY_POOL_BASE,
            pool_size=ENEMY_LOCAL_PREFIX_SIZE,
            enemy_stride=ENEMY_STRIDE,
            enemy_flags_offset=ENEMY_FLAGS_OFFSET,
            enemy_active_flag=ENEMY_ACTIVE_FLAG,
            include_auxiliary_context_pointers=(
                include_auxiliary_context_pointers
            ),
        )

    for _ in range(warmup):
        decode_enemy_bodies(
            blob,
            pool_size=ENEMY_LOCAL_PREFIX_SIZE,
            include_contact_disabled=True,
        )
        baseline_inventory = decode_inventory(
            include_auxiliary_context_pointers=False
        )
        inventory = decode_inventory(
            include_auxiliary_context_pointers=True
        )
        json.dumps(
            replace(baseline_inventory, decode_ms=0.0).record(),
            separators=(",", ":"),
        )
        json.dumps(
            replace(inventory, decode_ms=0.0).record(),
            separators=(",", ":"),
        )

    body_ms: list[float] = []
    baseline_inventory_ms: list[float] = []
    auxiliary_inventory_ms: list[float] = []
    baseline_record_ms: list[float] = []
    auxiliary_record_ms: list[float] = []
    baseline_inventory = None
    inventory = None
    for iteration in range(iterations):
        started = time.perf_counter_ns()
        decode_enemy_bodies(
            blob,
            pool_size=ENEMY_LOCAL_PREFIX_SIZE,
            include_contact_disabled=True,
        )
        body_ms.append((time.perf_counter_ns() - started) / 1_000_000.0)

        decode_order = (
            (False, True) if iteration % 2 == 0 else (True, False)
        )
        decode_elapsed: dict[bool, float] = {}
        for include_auxiliary in decode_order:
            started = time.perf_counter_ns()
            decoded = decode_inventory(
                include_auxiliary_context_pointers=include_auxiliary
            )
            decode_elapsed[include_auxiliary] = (
                time.perf_counter_ns() - started
            ) / 1_000_000.0
            if include_auxiliary:
                inventory = decoded
            else:
                baseline_inventory = decoded
        baseline_inventory_ms.append(decode_elapsed[False])
        auxiliary_inventory_ms.append(decode_elapsed[True])
        assert baseline_inventory is not None and inventory is not None

        record_order = (
            (baseline_inventory, baseline_record_ms),
            (inventory, auxiliary_record_ms),
        )
        if iteration % 2:
            record_order = tuple(reversed(record_order))
        for current_inventory, target in record_order:
            started = time.perf_counter_ns()
            json.dumps(
                current_inventory.record(),
                separators=(",", ":"),
            )
            target.append(
                (time.perf_counter_ns() - started) / 1_000_000.0
            )

    assert baseline_inventory is not None and inventory is not None
    baseline_canonical_record = replace(
        baseline_inventory,
        decode_ms=0.0,
    ).record()
    canonical_record = replace(inventory, decode_ms=0.0).record()
    baseline_canonical_bytes = json.dumps(
        baseline_canonical_record,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    canonical_bytes = json.dumps(
        canonical_record,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    combined_ms = [
        body + vm
        for body, vm in zip(body_ms, auxiliary_inventory_ms, strict=True)
    ]
    pointer_decode_delta_ms = [
        auxiliary - baseline
        for baseline, auxiliary in zip(
            baseline_inventory_ms,
            auxiliary_inventory_ms,
            strict=True,
        )
    ]
    pointer_record_delta_ms = [
        auxiliary - baseline
        for baseline, auxiliary in zip(
            baseline_record_ms,
            auxiliary_record_ms,
            strict=True,
        )
    ]
    return {
        "schema": SCHEMA,
        "platform": platform.platform(),
        "python": platform.python_version(),
        "iterations": iterations,
        "warmup": warmup,
        "fixture": {
            "blob_bytes": len(blob),
            "scanned_slots": ENEMY_LOCAL_PREFIX_SIZE,
            "active_slots": active_slots,
            "valid_vms": len(inventory.observations),
            "invalid_active_vms": len(inventory.invalid),
            "non_null_auxiliary_contexts": sum(
                pointer != 0
                for owner in inventory.auxiliary_contexts
                for pointer in owner.context_pointers
            ),
            "baseline_canonical_record_bytes": len(
                baseline_canonical_bytes
            ),
            "baseline_canonical_record_sha256": hashlib.sha256(
                baseline_canonical_bytes
            ).hexdigest(),
            "canonical_record_bytes": len(canonical_bytes),
            "canonical_record_sha256": hashlib.sha256(
                canonical_bytes
            ).hexdigest(),
        },
        "timing_ms": {
            "body_decode_baseline": _distribution(body_ms),
            "main_vm_inventory_baseline": _distribution(
                baseline_inventory_ms
            ),
            "main_vm_and_auxiliary_pointer_inventory": _distribution(
                auxiliary_inventory_ms
            ),
            "auxiliary_pointer_decode_paired_delta": _distribution(
                pointer_decode_delta_ms
            ),
            "combined_body_and_vm_decode": _distribution(combined_ms),
            "main_vm_inventory_json_build": _distribution(
                baseline_record_ms
            ),
            "main_vm_and_auxiliary_pointer_json_build": _distribution(
                auxiliary_record_ms
            ),
            "auxiliary_pointer_json_paired_delta": _distribution(
                pointer_record_delta_ms
            ),
        },
        "authority": "offline_performance_only",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--iterations", type=int, default=20_000)
    parser.add_argument("--warmup", type=int, default=1_000)
    parser.add_argument("--active-slots", type=int, default=16)
    parser.add_argument("--invalid-slots", type=int, default=2)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    report = run_benchmark(
        iterations=args.iterations,
        warmup=args.warmup,
        active_slots=args.active_slots,
        invalid_slots=args.invalid_slots,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
