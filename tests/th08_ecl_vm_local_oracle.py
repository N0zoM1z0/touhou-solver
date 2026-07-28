"""Independent scalar oracle for TH08 ECL VM-local shadow tests."""

from __future__ import annotations

import math
import struct

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
    horizon_frames: int = 20,
    max_instructions: int = 64,
) -> dict[str, object]:
    """Interpret raw tuples and a plain variable dict without product helpers."""

    variables = {10036: counter}
    pc = start
    timer = 0.0
    physical_frame = 0
    scanned = 0
    visited: set[tuple[int, float, int, tuple[tuple[int, int], ...]]] = set()
    reason = "instruction_limit"
    for _ in range(max_instructions):
        state = (pc, timer, physical_frame, tuple(sorted(variables.items())))
        if state in visited:
            reason = "repeated_state"
            break
        visited.add(state)
        time_value, opcode, size, difficulty, mask, arguments = instructions[pc]
        scanned += 1
        if time_value > timer:
            delta = max(
                1,
                math.ceil((time_value - timer) / 1.0 - 1e-9),
            )
            if physical_frame + delta > horizon_frames:
                physical_frame = horizon_frames
                reason = "horizon"
                break
            physical_frame += delta
            timer += delta
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
            timer = float(target_time)
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
                timer = float(target_time)
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
        "timer": timer,
        "physical_frame": physical_frame,
        "variables": variables,
    }


__all__ = ["RawInstruction", "oracle_interpret", "raw_instruction"]
