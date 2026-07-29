#!/usr/bin/env python3
"""Compare SEM-TIMER product, raw Python oracle, and native x87 probe."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from analysis.th08_ecl_timer_raw_oracle import (
    ORACLE_SEMANTICS_VERSION,
    oracle_advance_timer_raw,
    oracle_preserve_fraction_on_branch,
    oracle_reset_timer_components,
)
from th08_ecl_vm_state import float32_bits
from th08_native_timer import (
    TH08_NATIVE_TIMER_SEMANTICS_VERSION,
    Th08TimerState,
    advance_scaled_timer,
    reset_timer_elapsed,
)


SCHEMA = "th08-native-ecl-timer-differential-v1"


def _signed_dword(raw: int) -> int:
    raw &= 0xFFFFFFFF
    return raw - (1 << 32) if raw & 0x80000000 else raw


def _hex_dword(value: int) -> str:
    return f"0x{value & 0xFFFFFFFF:08x}"


def _probe_state(probe: Path, *arguments: str) -> tuple[int, int]:
    completed = subprocess.run(
        (str(probe), *arguments),
        check=True,
        capture_output=True,
        text=True,
    )
    words = completed.stdout.strip().split()
    if len(words) != 2:
        raise ValueError(f"unexpected probe output: {completed.stdout!r}")
    return _signed_dword(int(words[0], 0)), int(words[1], 0)


def _advance_cases() -> tuple[tuple[str, int, int, int, int], ...]:
    return (
        ("unit_fast_preserves_fraction", 0, float32_bits(0.75), 0x3F800000, 1),
        ("nonunit_carry", 10, float32_bits(0.75), float32_bits(0.5), 1),
        ("nonunit_no_carry", -10, float32_bits(0.125), float32_bits(0.25), 1),
        ("threshold_exact", 7, float32_bits(0.125), 0x3F7D70A4, 1),
        ("threshold_next_float", 7, float32_bits(0.125), 0x3F7D70A5, 1),
        ("negative_scale", 4, float32_bits(0.75), float32_bits(-0.5), 1),
        ("signed_wrap", (1 << 31) - 1, float32_bits(0.5), 0x3F800000, 1),
        ("signed_min", -(1 << 31), float32_bits(0.75), float32_bits(0.5), 1),
        ("positive_subnormals", 1, 0x00000001, 0x00000001, 1),
        ("negative_zero_plus_zero", 1, 0x80000000, 0x00000000, 1),
        ("rounded_carry", 20, float32_bits(0.6), float32_bits(0.4), 1),
        ("fast_scale_two", 20, float32_bits(-0.25), 0x40000000, 1),
        ("repeated_slow_ticks", 3, float32_bits(0.1), float32_bits(0.2), 9),
    )


def _advance_record(
    probe: Path,
    case: tuple[str, int, int, int, int],
) -> dict[str, object]:
    label, elapsed, fraction_bits, scale_bits, ticks = case
    product = Th08TimerState(elapsed, fraction_bits)
    oracle = (elapsed, fraction_bits)
    for _ in range(ticks):
        product = advance_scaled_timer(
            product,
            time_scale_bits=scale_bits,
        )
        oracle = oracle_advance_timer_raw(
            oracle[0],
            oracle[1],
            scale_bits,
        )
    native = _probe_state(
        probe,
        "advance",
        _hex_dword(elapsed),
        _hex_dword(fraction_bits),
        _hex_dword(scale_bits),
        str(ticks),
    )
    product_pair = (product.elapsed, product.fraction_bits)
    return {
        "label": label,
        "operation": "advance",
        "input": {
            "elapsed": elapsed,
            "fraction_bits": _hex_dword(fraction_bits),
            "time_scale_bits": _hex_dword(scale_bits),
            "ticks": ticks,
        },
        "product": {
            "elapsed": product_pair[0],
            "fraction_bits": _hex_dword(product_pair[1]),
        },
        "oracle": {
            "elapsed": oracle[0],
            "fraction_bits": _hex_dword(oracle[1]),
        },
        "native_probe": {
            "elapsed": native[0],
            "fraction_bits": _hex_dword(native[1]),
        },
        "passed": product_pair == oracle == native,
    }


def _branch_record(
    probe: Path,
    *,
    label: str,
    target: int,
    fraction_bits: int,
) -> dict[str, object]:
    product = Th08TimerState(123, fraction_bits).with_elapsed_preserving_fraction(
        target
    )
    oracle = oracle_preserve_fraction_on_branch(target, fraction_bits)
    native = _probe_state(
        probe,
        "branch",
        _hex_dword(target),
        _hex_dword(fraction_bits),
    )
    product_pair = (product.elapsed, product.fraction_bits)
    return {
        "label": label,
        "operation": "branch",
        "input": {
            "target_elapsed": target,
            "fraction_bits": _hex_dword(fraction_bits),
        },
        "product": {
            "elapsed": product_pair[0],
            "fraction_bits": _hex_dword(product_pair[1]),
        },
        "oracle": {
            "elapsed": oracle[0],
            "fraction_bits": _hex_dword(oracle[1]),
        },
        "native_probe": {
            "elapsed": native[0],
            "fraction_bits": _hex_dword(native[1]),
        },
        "passed": product_pair == oracle == native,
    }


def _reset_record(probe: Path, *, label: str, target: int) -> dict[str, object]:
    product = reset_timer_elapsed(target)
    oracle = oracle_reset_timer_components(target)
    native = _probe_state(probe, "reset", _hex_dword(target))
    product_pair = (product.elapsed, product.fraction_bits)
    return {
        "label": label,
        "operation": "reset",
        "input": {"target_elapsed": target},
        "product": {
            "elapsed": product_pair[0],
            "fraction_bits": _hex_dword(product_pair[1]),
        },
        "oracle": {
            "elapsed": oracle[0],
            "fraction_bits": _hex_dword(oracle[1]),
        },
        "native_probe": {
            "elapsed": native[0],
            "fraction_bits": _hex_dword(native[1]),
        },
        "passed": product_pair == oracle == native,
    }


def build_report(probe: Path) -> dict[str, object]:
    records = [_advance_record(probe, case) for case in _advance_cases()]
    records.extend(
        (
            _branch_record(
                probe,
                label="op04_op05_preserve_nonzero_fraction",
                target=4,
                fraction_bits=float32_bits(0.75),
            ),
            _branch_record(
                probe,
                label="branch_preserves_negative_zero",
                target=-1,
                fraction_bits=0x80000000,
            ),
            _reset_record(probe, label="reset_signed_minus_one", target=-1),
            _reset_record(
                probe,
                label="reset_signed_min",
                target=-(1 << 31),
            ),
        )
    )
    probe_bytes = probe.read_bytes()
    passed_cases = sum(bool(record["passed"]) for record in records)
    return {
        "schema": SCHEMA,
        "product_semantics_version": TH08_NATIVE_TIMER_SEMANTICS_VERSION,
        "oracle_semantics_version": ORACLE_SEMANTICS_VERSION,
        "native_probe": {
            "name": probe.name,
            "sha256": hashlib.sha256(probe_bytes).hexdigest(),
            "size": len(probe_bytes),
            "rounding": "FE_TONEAREST",
            "slow_path": "x87_fadd_fsub_with_fstp_dword",
        },
        "counts": {
            "cases": len(records),
            "passed": passed_cases,
            "failed": len(records) - passed_cases,
        },
        "gates": {
            "all_product_oracle_native_bitwise_equal": (passed_cases == len(records)),
            "nonzero_fraction_present": any(
                record["input"].get("fraction_bits") not in (None, "0x00000000")
                for record in records
            ),
            "nonunit_scale_present": any(
                record["input"].get("time_scale_bits") not in (None, "0x3f800000")
                for record in records
            ),
            "branch_and_reset_present": {record["operation"] for record in records}
            >= {"branch", "reset"},
        },
        "cases": records,
        "passed": all(bool(record["passed"]) for record in records),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    report = build_report(arguments.probe)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return 0 if report["passed"] and all(report["gates"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
