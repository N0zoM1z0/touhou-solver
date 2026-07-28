"""Exact offline interpreter for a narrow capture-aligned TH08 ECL subset."""

from __future__ import annotations

import math
import struct
from collections.abc import Callable

from th08_ecl_runtime import (
    CALLBACK_TOGGLE_TAGGED_BULLET,
    ECL_OP_CALL_SUBROUTINE,
    ECL_OP_FIRST_CONDITIONAL_JUMP,
    ECL_OP_INVOKE_CALLBACK,
    ECL_OP_JUMP,
    ECL_OP_LAST_CONDITIONAL_JUMP,
    ECL_OP_LOOP_DECREMENT_JUMP,
    ECL_OP_RESET_TIMER,
    ECL_OP_RETURN_SUBROUTINE,
    ECL_OP_SET_FLOAT,
    ECL_OP_SET_INT,
    ECL_OP_TERMINATE,
    EclVmSnapshot,
    RuntimeEclInstruction,
    TaggedVelocityToggle,
)
from th08_ecl_shadow.model import EclVmLocalShadowResult
from th08_ecl_shadow.registers import (
    LocalRegisters,
    float_destination_variable,
    signed_int32,
)
from th08_ecl_vm_state import (
    EclVmLocalProjection,
    float32_from_bits,
)


ECL_OP_NOP = 0x00


def _eligible(
    instruction: RuntimeEclInstruction,
    active_difficulty_mask: int,
) -> bool:
    return (
        active_difficulty_mask & instruction.difficulty_mask
    ) == active_difficulty_mask


def _integer_arguments(
    instruction: RuntimeEclInstruction,
    count: int,
) -> tuple[int, ...] | None:
    if len(instruction.payload) != 4 * count:
        return None
    return struct.unpack(f"<{count}i", instruction.payload)


def _unknown_reason(instruction: RuntimeEclInstruction) -> str:
    if instruction.opcode == ECL_OP_RESET_TIMER:
        return "unsupported_timer_reset"
    if (
        ECL_OP_FIRST_CONDITIONAL_JUMP
        <= instruction.opcode
        <= ECL_OP_LAST_CONDITIONAL_JUMP
        or instruction.opcode
        in (ECL_OP_CALL_SUBROUTINE, ECL_OP_RETURN_SUBROUTINE)
    ):
        return "unsupported_control_flow"
    return f"unsupported_opcode_{instruction.opcode:04x}"


def interpret_vm_local_shadow(
    snapshot: EclVmSnapshot,
    *,
    instruction_at: Callable[[int], RuntimeEclInstruction],
    horizon_frames: int,
    active_difficulty_mask: int,
    max_instructions: int = 256,
) -> EclVmLocalShadowResult:
    """Interpret only the declared exact VM-local prefix.

    This function is offline-only.  Unknown instructions and dependencies
    terminate the prefix before they execute.
    """

    if horizon_frames < 0:
        raise ValueError("shadow horizon cannot be negative")
    if max_instructions <= 0:
        raise ValueError("shadow instruction limit must be positive")
    if not 0 <= active_difficulty_mask <= 0xFF:
        raise ValueError("active difficulty mask must be a byte")
    projection = snapshot.local_projection
    if projection is None:
        return EclVmLocalShadowResult(
            events=(),
            instructions_scanned=0,
            stop_reason="missing_local_projection",
            horizon_covered=False,
            requested_horizon_frames=horizon_frames,
            stop_frame=0,
            final_instruction_pointer=snapshot.instruction_pointer,
            final_timer_value=snapshot.timer_value,
            final_projection=None,
        )

    locals_state = LocalRegisters(projection)
    pc = snapshot.instruction_pointer
    timer_value = snapshot.timer_value
    physical_frame = 0
    events: list[TaggedVelocityToggle] = []
    visited: set[
        tuple[int, float, int, EclVmLocalProjection]
    ] = set()
    instructions_scanned = 0
    stop_reason = "instruction_limit"
    horizon_covered = False

    for _ in range(max_instructions):
        frozen = locals_state.freeze()
        state = (pc, timer_value, physical_frame, frozen)
        if state in visited:
            stop_reason = "repeated_state"
            break
        visited.add(state)

        instruction = instruction_at(pc)
        instructions_scanned += 1
        if instruction.time > timer_value:
            delta = int(
                math.ceil(
                    (instruction.time - timer_value) / snapshot.time_scale
                    - 1e-9
                )
            )
            delta = max(delta, 1)
            if physical_frame + delta > horizon_frames:
                stop_reason = "horizon"
                horizon_covered = True
                physical_frame = horizon_frames
                break
            physical_frame += delta
            timer_value += delta * snapshot.time_scale

        if not _eligible(instruction, active_difficulty_mask):
            pc = instruction.address + instruction.size
            continue
        if instruction.opcode == ECL_OP_NOP:
            if instruction.payload:
                stop_reason = "unsupported_nop_payload"
                break
        elif instruction.opcode == ECL_OP_TERMINATE:
            if instruction.payload:
                stop_reason = "unsupported_terminate_payload"
                break
            stop_reason = "terminate"
            horizon_covered = True
            break
        elif instruction.opcode == ECL_OP_JUMP:
            arguments = _integer_arguments(instruction, 2)
            if arguments is None or instruction.parameter_mask != 0:
                stop_reason = "unsupported_jump"
                break
            target_time, relative_offset = arguments
            pc = instruction.address + relative_offset
            timer_value = float(target_time)
            continue
        elif instruction.opcode == ECL_OP_LOOP_DECREMENT_JUMP:
            arguments = _integer_arguments(instruction, 3)
            if arguments is None:
                stop_reason = "unsupported_loop_payload"
                break
            if not instruction.parameter_mask & 0x04:
                stop_reason = "unsupported_literal_lvalue_loop"
                break
            if instruction.parameter_mask != 0x04:
                stop_reason = "unsupported_loop_operands"
                break
            target_time, relative_offset, variable = arguments
            counter = locals_state.read_integer(variable)
            if counter is None:
                stop_reason = "unsupported_loop_lvalue"
                break
            post_decrement = signed_int32(counter - 1)
            assert locals_state.write_integer(variable, post_decrement)
            if post_decrement > 0:
                pc = instruction.address + relative_offset
                timer_value = float(target_time)
                continue
        elif instruction.opcode == ECL_OP_SET_INT:
            arguments = _integer_arguments(instruction, 2)
            if arguments is None or instruction.parameter_mask != 0x01:
                stop_reason = "unsupported_integer_assignment"
                break
            variable, value = arguments
            if not locals_state.write_integer(variable, value):
                stop_reason = "unsupported_integer_write"
                break
        elif instruction.opcode == ECL_OP_SET_FLOAT:
            arguments = _integer_arguments(instruction, 2)
            if arguments is None or instruction.parameter_mask != 0x01:
                stop_reason = "unsupported_float_assignment"
                break
            destination_bits, value_bits_signed = arguments
            variable = float_destination_variable(destination_bits)
            if variable is None:
                stop_reason = "unsupported_float_write"
                break
            value_bits = value_bits_signed & 0xFFFFFFFF
            if not math.isfinite(float32_from_bits(value_bits)):
                stop_reason = "unsupported_nonfinite_float_write"
                break
            assert locals_state.write_float_bits(variable, value_bits)
        elif instruction.opcode == ECL_OP_INVOKE_CALLBACK:
            arguments = _integer_arguments(instruction, 2)
            if arguments is None or instruction.parameter_mask != 0:
                stop_reason = "unsupported_callback"
                break
            callback_index, _ = arguments
            if callback_index != CALLBACK_TOGGLE_TAGGED_BULLET:
                stop_reason = "unsupported_callback"
                break
            frozen = locals_state.freeze()
            tag_mask = frozen.integer_locals[0] & 0xFFFFFFFF
            callback_angle = float32_from_bits(frozen.float_local_bits[0])
            callback_speed = float32_from_bits(frozen.float_local_bits[1])
            if not all(
                math.isfinite(value)
                for value in (callback_angle, callback_speed)
            ):
                stop_reason = "unsupported_nonfinite_callback"
                break
            if physical_frame > 0 and tag_mask:
                speed = callback_speed * snapshot.time_scale
                events.append(
                    TaggedVelocityToggle(
                        physical_frame,
                        callback_index,
                        tag_mask,
                        math.cos(callback_angle) * speed,
                        math.sin(callback_angle) * speed,
                    )
                )
        else:
            stop_reason = _unknown_reason(instruction)
            break
        pc = instruction.address + instruction.size
    else:
        stop_reason = "instruction_limit"

    return EclVmLocalShadowResult(
        events=tuple(events),
        instructions_scanned=instructions_scanned,
        stop_reason=stop_reason,
        horizon_covered=horizon_covered,
        requested_horizon_frames=horizon_frames,
        stop_frame=physical_frame,
        final_instruction_pointer=pc,
        final_timer_value=timer_value,
        final_projection=locals_state.freeze(),
    )


__all__ = ["interpret_vm_local_shadow"]
