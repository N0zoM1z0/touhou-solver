"""Independent scalar oracle for TH08 ECL VM-local shadow tests."""

from __future__ import annotations

import struct

from analysis.th08_ecl_timer_raw_oracle import (
    oracle_advance_timer_raw,
    oracle_preserve_fraction_on_branch,
)
from th08_ecl_runtime import RuntimeEclInstruction


RawInstruction = tuple[int, int, int, int, int, tuple[int, ...]]


def raw_instruction(instruction: RuntimeEclInstruction) -> RawInstruction:
    argument_count = len(instruction.payload) // 4
    arguments = (
        struct.unpack(f"<{argument_count}i", instruction.payload)
        if argument_count
        else ()
    )
    return (
        instruction.time,
        instruction.opcode,
        instruction.size,
        instruction.difficulty_mask,
        instruction.parameter_mask,
        arguments,
    )


def oracle_interpret(
    instructions: dict[int, RawInstruction],
    *,
    start: int,
    counter: int,
    timer_fraction: float = 0.0,
    timer_elapsed: int = 0,
    time_scale: float = 1.0,
    horizon_frames: int = 20,
    max_instructions: int = 64,
) -> dict[str, object]:
    """Interpret raw tuples and a plain variable dict without product helpers."""

    variables = {10036: counter}
    pc = start
    timer_fraction_bits = struct.unpack(
        "<I",
        struct.pack("<f", timer_fraction),
    )[0]
    time_scale_bits = struct.unpack("<I", struct.pack("<f", time_scale))[0]
    physical_frame = 0
    scanned = 0
    visited: set[tuple[int, int, int, int, tuple[tuple[int, int], ...]]] = set()
    reason = "instruction_limit"
    for _ in range(max_instructions):
        state = (
            pc,
            timer_elapsed,
            timer_fraction_bits,
            physical_frame,
            tuple(sorted(variables.items())),
        )
        if state in visited:
            reason = "repeated_state"
            break
        visited.add(state)
        time_value, opcode, size, difficulty, mask, arguments = instructions[pc]
        scanned += 1
        while time_value != timer_elapsed:
            if physical_frame >= horizon_frames:
                reason = "horizon"
                break
            timer_elapsed, timer_fraction_bits = oracle_advance_timer_raw(
                timer_elapsed,
                timer_fraction_bits,
                time_scale_bits,
            )
            physical_frame += 1
        if reason == "horizon":
            break
        if 0x08 & difficulty != 0x08:
            pc += size
            continue
        if opcode == 0x00:
            pc += size
            continue
        if opcode == 0x01:
            reason = "terminate"
            break
        if opcode == 0x04 and mask == 0 and len(arguments) == 2:
            target_time, relative = arguments
            pc += relative
            timer_elapsed, timer_fraction_bits = oracle_preserve_fraction_on_branch(
                target_time,
                timer_fraction_bits,
            )
            continue
        if opcode == 0x05 and mask == 0x04 and len(arguments) == 3:
            target_time, relative, variable = arguments
            if variable not in variables:
                reason = "unsupported_loop_lvalue"
                break
            post = (variables[variable] - 1) & 0xFFFFFFFF
            if post & 0x80000000:
                post -= 1 << 32
            variables[variable] = post
            if post > 0:
                pc += relative
                timer_elapsed, timer_fraction_bits = oracle_preserve_fraction_on_branch(
                    target_time,
                    timer_fraction_bits,
                )
                continue
            pc += size
            continue
        if opcode == 0x06 and mask == 0x01 and len(arguments) == 2:
            variable, value = arguments
            if variable not in variables:
                reason = "unsupported_integer_write"
                break
            variables[variable] = value
            pc += size
            continue
        reason = f"unsupported_opcode_{opcode:04x}"
        break
    return {
        "reason": reason,
        "scanned": scanned,
        "pc": pc,
        "timer": timer_elapsed
        + struct.unpack(
            "<f",
            struct.pack("<I", timer_fraction_bits),
        )[0],
        "timer_elapsed": timer_elapsed,
        "timer_fraction_bits": timer_fraction_bits,
        "physical_frame": physical_frame,
        "variables": variables,
    }


__all__ = ["RawInstruction", "oracle_interpret", "raw_instruction"]
