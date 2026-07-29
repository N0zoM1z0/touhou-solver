"""Structurally independent raw oracle for TH08 ECL scale schedules.

This oracle decodes instruction bytes locally and carries timer/scale state as
plain integers. It intentionally does not import the product schedule,
instruction, VM projection, or time-scale schedule implementations.
"""

from __future__ import annotations

import struct
from collections.abc import Callable, Mapping

from analysis.th08_ecl_timer_raw_oracle import oracle_advance_timer_raw
from analysis.th08_scale_transition_raw_oracle import (
    oracle_reciprocal_int32_bits,
)


ORACLE_SEMANTICS_VERSION = (
    "th08-ecl-scale-schedule-raw-oracle-v1-player-ecl-laser"
)

_CALLBACK_RECIPROCAL = 18
_CALLBACK_SLOWDOWN = 28
_CALLBACK_RESTORE = 29
_UNIT_BITS = 0x3F800000
_INTEGER_CONDITIONALS = {
    0x28: lambda left, right: left == right,
    0x2A: lambda left, right: left != right,
    0x2C: lambda left, right: left < right,
    0x2E: lambda left, right: left <= right,
    0x30: lambda left, right: left > right,
    0x32: lambda left, right: left >= right,
}
_SCALE_NEUTRAL = frozenset({0x00, 0x07, 0x0F, 0x25, 0x7C, 0x7F, 0x8C})


def _signed(value: int) -> int:
    raw = value & 0xFFFFFFFF
    return raw - (1 << 32) if raw & 0x80000000 else raw


def _decode(raw: bytes) -> tuple[int, int, int, int, int, tuple[int, ...]]:
    if len(raw) < 12:
        raise ValueError("oracle instruction is shorter than its header")
    time, opcode, size, _unused, difficulty, parameter_mask = struct.unpack_from(
        "<iHHBBH",
        raw,
    )
    if size != len(raw) or size < 12 or (size - 12) % 4:
        raise ValueError("oracle instruction size is invalid")
    arguments = struct.unpack_from(f"<{(size - 12) // 4}i", raw, 12)
    return time, opcode, size, difficulty, parameter_mask, arguments


def _finish_flags(flags: int) -> int:
    if flags & 1:
        flags &= ~1
        if not flags & 8 and flags & 4:
            flags |= 0x200
    return flags & ~0x800


def _resolve(
    raw: int,
    *,
    dynamic: bool,
    integers: Mapping[int, int],
    difficulty_index: int,
    route_id: int,
    spell_flags: int,
    spell_timer_elapsed_by_frame: tuple[int, ...],
    frame: int,
) -> tuple[int | None, int | None]:
    if not dynamic:
        return _signed(raw), None
    variable = _signed(raw)
    if variable in integers:
        return integers[variable], variable
    if variable == 10040:
        return difficulty_index, variable
    if variable == 10052:
        return route_id, variable
    if variable == 10099:
        return (
            ((spell_flags >> 2) & 1)
            if spell_flags & 1
            else ((spell_flags >> 9) & 1),
            variable,
        )
    if variable == 10100 and frame <= len(spell_timer_elapsed_by_frame):
        return spell_timer_elapsed_by_frame[frame - 1], variable
    return None, variable


def oracle_ecl_scale_schedule_raw(
    *,
    instruction_bytes_at: Callable[[int], bytes],
    start_pc: int,
    timer_elapsed: int,
    timer_fraction_bits: int,
    root_scale_bits: int,
    integer_values: Mapping[int, int],
    difficulty_index: int,
    route_id: int,
    spell_flags: int,
    spell_timer_elapsed_by_frame: tuple[int, ...],
    horizon_frames: int,
    active_difficulty_mask: int,
    no_hit_no_bomb_continuation: bool,
    max_instructions: int = 4096,
) -> dict[str, object]:
    """Return a plain raw schedule result for the supported causal subset."""

    if horizon_frames < 0:
        raise ValueError("oracle horizon must be nonnegative")
    if not 0 < active_difficulty_mask <= 0xFF:
        raise ValueError("oracle difficulty mask must be a nonzero byte")
    integers = {
        int(variable): _signed(value)
        for variable, value in integer_values.items()
    }
    pc = start_pc
    elapsed = _signed(timer_elapsed)
    fraction_bits = timer_fraction_bits & 0xFFFFFFFF
    scale_bits = root_scale_bits & 0xFFFFFFFF
    flags = spell_flags & 0xFFFFFFFF
    player: list[int] = []
    laser: list[int] = []
    writes: list[tuple[int, int, int, int, int, bool]] = []
    consumed: set[int] = set()
    scanned = 0
    terminated = False

    def finish(reason: str, frame: int, covered: bool) -> dict[str, object]:
        return {
            "semantics_version": ORACLE_SEMANTICS_VERSION,
            "player_scale_bits": tuple(player),
            "laser_scale_bits": tuple(laser),
            "writes": tuple(writes),
            "instructions_scanned": scanned,
            "stop_reason": reason,
            "horizon_covered": covered,
            "stop_frame": frame,
            "consumed_external_variables": tuple(sorted(consumed)),
            "pc": pc,
            "timer_elapsed": elapsed,
            "timer_fraction_bits": fraction_bits,
            "integer_values": dict(sorted(integers.items())),
            "spell_flags": flags,
        }

    for frame in range(1, horizon_frames + 1):
        player.append(scale_bits)
        visited: set[tuple[object, ...]] = set()
        while not terminated:
            state = (
                pc,
                elapsed,
                fraction_bits,
                scale_bits,
                flags,
                tuple(sorted(integers.items())),
            )
            if state in visited:
                return finish("repeated_same_phase_state", frame, False)
            visited.add(state)
            try:
                raw = instruction_bytes_at(pc)
                (
                    instruction_time,
                    opcode,
                    size,
                    difficulty,
                    parameter_mask,
                    arguments,
                ) = _decode(raw)
            except (OSError, RuntimeError, ValueError, struct.error):
                return finish("instruction_read_error", frame, False)
            if instruction_time != elapsed:
                break
            scanned += 1
            if scanned > max_instructions:
                return finish("instruction_limit", frame, False)
            if active_difficulty_mask & difficulty != active_difficulty_mask:
                pc += size
                continue

            if opcode == 0x01:
                if arguments:
                    return finish("unsupported_terminate_payload", frame, False)
                terminated = True
                break
            if opcode == 0x04:
                if len(arguments) != 2 or parameter_mask:
                    return finish("unsupported_jump", frame, False)
                elapsed = _signed(arguments[0])
                pc += arguments[1]
                continue
            if opcode == 0x05:
                if len(arguments) != 3 or parameter_mask != 0x04:
                    return finish("unsupported_loop", frame, False)
                target_time, relative_offset, variable = arguments
                if variable not in integers:
                    return finish("unsupported_loop_lvalue", frame, False)
                integers[variable] = _signed(integers[variable] - 1)
                if integers[variable] > 0:
                    elapsed = _signed(target_time)
                    pc += relative_offset
                    continue
            elif opcode == 0x06:
                if len(arguments) != 2 or parameter_mask != 0x01:
                    return finish(
                        "unsupported_integer_assignment",
                        frame,
                        False,
                    )
                variable, value = arguments
                if variable in integers:
                    integers[variable] = _signed(value)
            elif opcode in _INTEGER_CONDITIONALS:
                if len(arguments) != 4 or parameter_mask & ~0x03:
                    return finish(
                        "unsupported_integer_conditional",
                        frame,
                        False,
                    )
                left_raw, right_raw, target_time, relative_offset = arguments
                left, left_variable = _resolve(
                    left_raw,
                    dynamic=bool(parameter_mask & 1),
                    integers=integers,
                    difficulty_index=difficulty_index,
                    route_id=route_id,
                    spell_flags=flags,
                    spell_timer_elapsed_by_frame=spell_timer_elapsed_by_frame,
                    frame=frame,
                )
                right, right_variable = _resolve(
                    right_raw,
                    dynamic=bool(parameter_mask & 2),
                    integers=integers,
                    difficulty_index=difficulty_index,
                    route_id=route_id,
                    spell_flags=flags,
                    spell_timer_elapsed_by_frame=spell_timer_elapsed_by_frame,
                    frame=frame,
                )
                consumed.update(
                    variable
                    for variable in (left_variable, right_variable)
                    if variable is not None
                )
                if left is None or right is None:
                    return finish("unsupported_integer_operand", frame, False)
                if _INTEGER_CONDITIONALS[opcode](left, right):
                    elapsed = _signed(target_time)
                    pc += relative_offset
                    continue
            elif 0x28 <= opcode <= 0x33:
                return finish("unsupported_float_conditional", frame, False)
            elif opcode == 0x88:
                if len(arguments) != 2 or parameter_mask & 1:
                    return finish("unsupported_callback_index", frame, False)
                callback_index, argument = arguments
                if callback_index not in {
                    _CALLBACK_RECIPROCAL,
                    _CALLBACK_SLOWDOWN,
                    _CALLBACK_RESTORE,
                }:
                    return finish("unsupported_non_scale_callback", frame, False)
                before = scale_bits
                if callback_index == _CALLBACK_RESTORE:
                    scale_bits = _UNIT_BITS
                else:
                    divisor, variable = _resolve(
                        argument,
                        dynamic=bool(parameter_mask & 2),
                        integers=integers,
                        difficulty_index=difficulty_index,
                        route_id=route_id,
                        spell_flags=flags,
                        spell_timer_elapsed_by_frame=spell_timer_elapsed_by_frame,
                        frame=frame,
                    )
                    if variable is not None:
                        consumed.add(variable)
                    if divisor is None:
                        return finish("unsupported_scale_divisor", frame, False)
                    try:
                        scale_bits = oracle_reciprocal_int32_bits(divisor)
                    except ValueError:
                        return finish("unsupported_scale_divisor", frame, False)
                writes.append(
                    (
                        frame,
                        callback_index,
                        before,
                        scale_bits,
                        pc,
                        callback_index in {_CALLBACK_SLOWDOWN, _CALLBACK_RESTORE},
                    )
                )
            elif opcode == 0x89:
                return finish("unsupported_callback_install", frame, False)
            elif opcode == 0x7B:
                if arguments:
                    return finish(
                        "unsupported_finish_spell_payload",
                        frame,
                        False,
                    )
                if not no_hit_no_bomb_continuation:
                    return finish(
                        "missing_no_hit_no_bomb_continuation",
                        frame,
                        False,
                    )
                flags = _finish_flags(flags)
            elif opcode not in _SCALE_NEUTRAL:
                return finish(f"unsupported_opcode_{opcode:04x}", frame, False)
            pc += size

        laser.append(scale_bits)
        if not terminated:
            elapsed, fraction_bits = oracle_advance_timer_raw(
                elapsed,
                fraction_bits,
                scale_bits,
            )
    return finish("horizon", horizon_frames, True)


__all__ = [
    "ORACLE_SEMANTICS_VERSION",
    "oracle_ecl_scale_schedule_raw",
]
