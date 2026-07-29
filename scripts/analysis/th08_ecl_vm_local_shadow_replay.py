#!/usr/bin/env python3
"""Replay the offline ECL VM-local shadow over retained live projections."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from collections import Counter, defaultdict
from pathlib import Path

from analysis.th08_ecl_timer_raw_oracle import (
    ORACLE_SEMANTICS_VERSION,
    oracle_advance_timer_raw,
    oracle_preserve_fraction_on_branch,
)
from analysis.th08_ecl_trace_support import spell_key
from th08_ecl_runtime import (
    ECL_OP_LOOP_DECREMENT_JUMP,
    EclInstructionCache,
    EclVmSnapshot,
    RuntimeEclInstruction,
)
from th08_ecl_shadow import (
    ECL_VM_LOCAL_SHADOW_SEMANTICS_VERSION,
    interpret_vm_local_shadow,
)
from th08_ecl_vm_state import (
    ECL_VM_LOCAL_PROJECTION_LAYOUT,
    EclVmLocalProjection,
    float32_bits,
    float32_from_bits,
)
from th08_native_timer import TH08_NATIVE_TIMER_SEMANTICS_VERSION


SCHEMA = "th08-ecl-vm-local-shadow-replay-v2"
CASE_SCHEMA = "th08-ecl-vm-local-op05-cases-v2"
LOCAL_LOOP_SPELLS = frozenset(("57", "61", "65"))


def _signed_int32(value: int) -> int:
    value &= 0xFFFFFFFF
    return value - (1 << 32) if value & (1 << 31) else value


class _MappedEcl:
    def __init__(self, *, runtime_base: int, code: bytes) -> None:
        self.runtime_base = runtime_base
        self.code = code

    def read(self, address: int, size: int) -> bytes:
        start = address - self.runtime_base
        end = start + size
        if size <= 0 or start < 0 or end > len(self.code):
            raise OSError(f"unmapped replay ECL read at {address:#x}")
        return self.code[start:end]


def _projection(record: object) -> EclVmLocalProjection:
    if not isinstance(record, dict):
        raise ValueError("missing VM-local projection")
    if record.get("layout") != ECL_VM_LOCAL_PROJECTION_LAYOUT:
        raise ValueError("unexpected VM-local projection layout")
    integer_locals = record.get("integer_locals")
    float_local_bits = record.get("float_local_bits")
    scratch_integers = record.get("scratch_integers")
    if not all(
        isinstance(values, list)
        for values in (integer_locals, float_local_bits, scratch_integers)
    ):
        raise ValueError("VM-local projection arrays are missing")
    assert isinstance(integer_locals, list)
    assert isinstance(float_local_bits, list)
    assert isinstance(scratch_integers, list)
    return EclVmLocalProjection(
        tuple(integer_locals),
        tuple(float_local_bits),
        tuple(scratch_integers),
    )


def _snapshot(
    lookahead: dict[str, object],
) -> EclVmSnapshot:
    projection = _projection(lookahead.get("vm_local_projection"))
    angle = float32_from_bits(projection.float_local_bits[0])
    speed = float32_from_bits(projection.float_local_bits[1])
    return EclVmSnapshot(
        instruction_pointer=int(lookahead["instruction_pointer"]),
        timer_fraction=float(lookahead["timer_fraction"]),
        timer_elapsed=int(lookahead["timer_elapsed"]),
        tag_mask=int(lookahead["tag_mask"]),
        callback_angle=angle,
        callback_speed=speed,
        time_scale=float(lookahead["time_scale"]),
        local_projection=projection,
    )


def _op05_arguments(
    instruction: RuntimeEclInstruction,
) -> tuple[int, int, int] | None:
    if (
        instruction.opcode != ECL_OP_LOOP_DECREMENT_JUMP
        or instruction.parameter_mask != 0x04
        or len(instruction.payload) != 12
    ):
        return None
    return struct.unpack("<3i", instruction.payload)


def _case_record(
    *,
    snapshot: EclVmSnapshot,
    instruction: RuntimeEclInstruction,
    runtime_base: int,
) -> tuple[dict[str, object], bool]:
    arguments = _op05_arguments(instruction)
    projection = snapshot.local_projection
    if arguments is None or projection is None:
        raise ValueError("one-step case is not a projected opcode 0x05")
    target_time, relative_offset, variable = arguments
    counter = projection.integer_value(variable)
    if counter is None:
        raise ValueError("opcode 0x05 lvalue is outside the projection")
    expected_elapsed = snapshot.timer_elapsed
    expected_fraction_bits = snapshot.timer_fraction_bits
    time_scale_bits = snapshot.time_scale_bits
    expected_stop_frame = 0
    while instruction.time != expected_elapsed:
        if expected_stop_frame >= 256:
            raise ValueError("opcode 0x05 is outside the replay horizon")
        expected_elapsed, expected_fraction_bits = oracle_advance_timer_raw(
            expected_elapsed,
            expected_fraction_bits,
            time_scale_bits,
        )
        expected_stop_frame += 1
    post_decrement = _signed_int32(counter - 1)
    expected_pc = (
        instruction.address + relative_offset
        if post_decrement > 0
        else instruction.address + instruction.size
    )
    if post_decrement > 0:
        expected_elapsed, expected_fraction_bits = oracle_preserve_fraction_on_branch(
            target_time,
            expected_fraction_bits,
        )
    expected_timer = expected_elapsed + float32_from_bits(expected_fraction_bits)
    result = interpret_vm_local_shadow(
        snapshot,
        instruction_at=lambda _address: instruction,
        horizon_frames=256,
        active_difficulty_mask=0x08,
        max_instructions=1,
    )
    final_projection = result.final_projection
    passed = (
        final_projection is not None
        and result.stop_reason == "instruction_limit"
        and result.instructions_scanned == 1
        and result.final_instruction_pointer == expected_pc
        and result.final_timer_elapsed == expected_elapsed
        and result.final_timer_fraction_bits == expected_fraction_bits
        and result.stop_frame == expected_stop_frame
        and final_projection.integer_value(variable) == post_decrement
    )
    return (
        {
            "instruction_offset": instruction.address - runtime_base,
            "instruction_time": instruction.time,
            "instruction_size": instruction.size,
            "difficulty_mask": instruction.difficulty_mask,
            "parameter_mask": instruction.parameter_mask,
            "arguments": list(arguments),
            "timer_fraction": snapshot.timer_fraction,
            "timer_fraction_bits": f"{snapshot.timer_fraction_bits:#010x}",
            "timer_elapsed": snapshot.timer_elapsed,
            "time_scale": snapshot.time_scale,
            "time_scale_bits": f"{snapshot.time_scale_bits:#010x}",
            "variable": variable,
            "counter_before": counter,
            "counter_after": post_decrement,
            "expected_pc_offset": expected_pc - runtime_base,
            "expected_timer": expected_timer,
            "expected_timer_elapsed": expected_elapsed,
            "expected_timer_fraction_bits": (f"{expected_fraction_bits:#010x}"),
            "expected_stop_frame": expected_stop_frame,
        },
        passed,
    )


def audit_vm_local_shadow_replay(
    *,
    trace_path: Path,
    ecl_path: Path,
    runtime_base: int,
) -> tuple[dict[str, object], dict[str, object]]:
    code = ecl_path.read_bytes()
    mapped = _MappedEcl(runtime_base=runtime_base, code=code)
    cache = EclInstructionCache()
    trace_digest = hashlib.sha256()
    decision_rows = 0
    unknown_rows = 0
    candidate_rows = 0
    excluded_dynamic_rows = 0
    decoded_rows = 0
    initial_opcodes: Counter[str] = Counter()
    shadow_stop_reasons: Counter[str] = Counter()
    per_spell_rows: dict[str, Counter[str]] = defaultdict(Counter)
    decode_errors = 0
    error_samples: list[dict[str, object]] = []
    initial_op05_rows = 0
    one_step_failures = 0
    new_complete_rows = 0
    complete_samples: list[dict[str, object]] = []
    unique_cases: dict[str, dict[str, object]] = {}

    def instruction_at(address: int) -> RuntimeEclInstruction:
        return cache.instruction(mapped.read, address)

    with trace_path.open("rb") as stream:
        for raw_line in stream:
            trace_digest.update(raw_line)
            try:
                decision = json.loads(raw_line)
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            if decision.get("kind") != "decision":
                continue
            decision_rows += 1
            lookahead = decision.get("bullet_velocity_lookahead")
            if (
                not isinstance(lookahead, dict)
                or lookahead.get("coverage_status") != "unknown"
            ):
                continue
            unknown_rows += 1
            spell = spell_key(decision)
            if spell not in LOCAL_LOOP_SPELLS:
                excluded_dynamic_rows += 1
                per_spell_rows[spell]["excluded_dynamic_rows"] += 1
                continue
            candidate_rows += 1
            per_spell_rows[spell]["candidate_rows"] += 1
            try:
                snapshot = _snapshot(lookahead)
                initial = instruction_at(snapshot.instruction_pointer)
                decoded_rows += 1
                opcode_key = f"0x{initial.opcode:04x}"
                initial_opcodes[opcode_key] += 1
                per_spell_rows[spell][f"initial:{opcode_key}"] += 1

                if _op05_arguments(initial) is not None:
                    initial_op05_rows += 1
                    case, passed = _case_record(
                        snapshot=snapshot,
                        instruction=initial,
                        runtime_base=runtime_base,
                    )
                    one_step_failures += not passed
                    case_key = json.dumps(
                        case,
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                    unique_cases[case_key] = case

                result = interpret_vm_local_shadow(
                    snapshot,
                    instruction_at=instruction_at,
                    horizon_frames=int(lookahead["requested_horizon_frames"]),
                    active_difficulty_mask=0x08,
                )
                shadow_stop_reasons[result.stop_reason] += 1
                per_spell_rows[spell][f"shadow_stop:{result.stop_reason}"] += 1
                if result.horizon_covered:
                    new_complete_rows += 1
                    if len(complete_samples) < 20:
                        complete_samples.append(
                            {
                                "frame": decision.get("frame"),
                                "spell": spell,
                                "initial_opcode": opcode_key,
                                "instructions_scanned": (result.instructions_scanned),
                                "stop_reason": result.stop_reason,
                                "event_count": len(result.events),
                            }
                        )
            except (KeyError, TypeError, ValueError, OSError) as exc:
                decode_errors += 1
                if len(error_samples) < 20:
                    error_samples.append(
                        {
                            "frame": decision.get("frame"),
                            "spell": spell,
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    )

    gates = {
        "candidate_unknown_rows_present": candidate_rows > 0,
        "all_candidate_rows_decoded": (
            decoded_rows == candidate_rows and decode_errors == 0
        ),
        "capture_aligned_op05_rows_present": initial_op05_rows > 0,
        "all_op05_one_step_transitions_exact": one_step_failures == 0,
        "no_unverified_new_completion": new_complete_rows == 0,
    }
    case_records = sorted(
        unique_cases.values(),
        key=lambda item: (
            int(item["instruction_offset"]),
            int(item["counter_before"]),
            float(item["timer_elapsed"]),
            float(item["timer_fraction"]),
        ),
    )
    cases = {
        "schema": CASE_SCHEMA,
        "semantics": {
            "product_shadow": ECL_VM_LOCAL_SHADOW_SEMANTICS_VERSION,
            "native_timer": TH08_NATIVE_TIMER_SEMANTICS_VERSION,
            "independent_oracle": ORACLE_SEMANTICS_VERSION,
            "timer_identity": "signed_elapsed_plus_float32_fraction_bits",
        },
        "source": {
            "trace_name": trace_path.name,
            "trace_sha256": trace_digest.hexdigest(),
            "ecl_name": ecl_path.name,
            "ecl_sha256": hashlib.sha256(code).hexdigest(),
            "runtime_base": runtime_base,
        },
        "rows": {
            "initial_op05_rows": initial_op05_rows,
            "unique_cases": len(case_records),
            "nonzero_fraction_cases": sum(
                int(case["timer_fraction_bits"], 0) != 0 for case in case_records
            ),
            "nonunit_scale_cases": sum(
                int(case["time_scale_bits"], 0) != float32_bits(1.0)
                for case in case_records
            ),
        },
        "authority": {
            "scope": "retained_zero_fraction_observed_scale_slice",
            "general_native_timer_exactness": "separate_differential_gate",
            "historical_v1_fixture": "immutable",
        },
        "cases": case_records,
    }
    report = {
        "schema": SCHEMA,
        "source": cases["source"],
        "counts": {
            "decision_rows": decision_rows,
            "unknown_rows": unknown_rows,
            "candidate_unknown_rows": candidate_rows,
            "excluded_dynamic_unknown_rows": excluded_dynamic_rows,
            "decoded_rows": decoded_rows,
            "decode_errors": decode_errors,
            "initial_opcode_rows": dict(sorted(initial_opcodes.items())),
            "shadow_stop_reason_rows": dict(sorted(shadow_stop_reasons.items())),
            "initial_op05_rows": initial_op05_rows,
            "unique_op05_cases": len(case_records),
            "op05_one_step_failures": one_step_failures,
            "unverified_new_complete_rows": new_complete_rows,
        },
        "per_spell": {
            spell: dict(sorted(counts.items()))
            for spell, counts in sorted(per_spell_rows.items())
        },
        "violations": {
            "decode_error_samples": error_samples,
            "unverified_complete_samples": complete_samples,
        },
        "gates": gates,
        "passed": all(gates.values()),
        "authority": {
            "scope": "offline_shadow_only",
            "timer_semantics": TH08_NATIVE_TIMER_SEMANTICS_VERSION,
            "retained_timer_slice": "zero_fraction_observed_scale",
            "candidate_completion": "none_verified",
            "live_callback_schedule": "unchanged",
            "physical_action": "none_added",
        },
    }
    return report, cases


def _parse_int(value: str) -> int:
    return int(value, 0)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("trace", type=Path)
    parser.add_argument("--ecl", type=Path, required=True)
    parser.add_argument("--runtime-base", type=_parse_int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cases-output", type=Path, required=True)
    arguments = parser.parse_args()
    report, cases = audit_vm_local_shadow_replay(
        trace_path=arguments.trace,
        ecl_path=arguments.ecl,
        runtime_base=arguments.runtime_base,
    )
    arguments.output.write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    arguments.cases_output.write_text(
        json.dumps(cases, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
