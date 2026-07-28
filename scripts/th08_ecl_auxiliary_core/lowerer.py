"""Bounded transition walker for one auxiliary literal fire-cycle class."""

from __future__ import annotations

import math
import struct
from collections.abc import Callable

from th08_ecl_runtime import RuntimeEclInstruction
from th08_ecl_vm_state import float32_bits
from th08_live.auxiliary_vm.model import (
    MAXIMUM_RUNTIME_ADDRESS,
    MINIMUM_RUNTIME_ADDRESS,
)

from .constants import (
    ECL_HEADER_SIZE,
    ECL_OP_DEFINE_BULLET_TRANSFORM,
    ECL_OP_FIRST_DIRECT_FIRE,
    ECL_OP_JUMP,
    ECL_OP_LAST_DIRECT_FIRE,
    ECL_OP_TERMINATE,
    PHYSICAL_TIMING_AVAILABLE,
    PHYSICAL_TIMING_BUDGET_EXHAUSTED,
    PHYSICAL_TIMING_INVALID,
    PHYSICAL_TIMING_UNAVAILABLE,
    STOP_HORIZON,
    STOP_INSTRUCTION_LIMIT,
    STOP_REPEATED_STATE,
    STOP_TERMINATE,
)
from .descriptor import decode_fire, decode_transform
from .model import (
    AuxiliaryDirectFireIntent,
    AuxiliaryEclVmState,
    AuxiliaryLiteralFireResult,
    LiteralTransformDefinition,
)
from .timer import float32, physical_wait


def _stop_result(
    *,
    intents: list[AuxiliaryDirectFireIntent],
    transforms: list[LiteralTransformDefinition],
    instructions_scanned: int,
    stop_reason: str,
    horizon: int,
    stop_tick: int,
    physical_timing_status: str,
) -> AuxiliaryLiteralFireResult:
    return AuxiliaryLiteralFireResult(
        intents=tuple(intents),
        transform_definitions=tuple(transforms),
        instructions_scanned=instructions_scanned,
        stop_reason=stop_reason,
        horizon_covered=stop_reason in {STOP_HORIZON, STOP_TERMINATE},
        requested_timer_tick_horizon=horizon,
        stop_timer_tick=stop_tick,
        physical_timing_status=physical_timing_status,
    )


def _stop(
    *,
    intents: list[AuxiliaryDirectFireIntent],
    transforms: list[LiteralTransformDefinition],
    scanned: int,
    reason: str,
    horizon: int,
    tick: int,
    physical_status: str,
) -> AuxiliaryLiteralFireResult:
    return _stop_result(
        intents=intents,
        transforms=transforms,
        instructions_scanned=scanned,
        stop_reason=reason,
        horizon=horizon,
        stop_tick=tick,
        physical_timing_status=physical_status,
    )


def lower_auxiliary_literal_fire_cycle(
    state: AuxiliaryEclVmState,
    *,
    instruction_at: Callable[[int], RuntimeEclInstruction],
    timer_tick_horizon: int,
    active_difficulty_mask: int,
    time_scale: float | None = None,
    max_instructions: int = 64,
    max_physical_steps: int = 65536,
) -> AuxiliaryLiteralFireResult:
    """Lower one capture-aligned literal auxiliary path without geometry."""

    if timer_tick_horizon < 0:
        raise ValueError("auxiliary timer-tick horizon cannot be negative")
    if active_difficulty_mask <= 0:
        raise ValueError("active difficulty mask must be positive")
    if max_instructions <= 0:
        raise ValueError("auxiliary instruction limit must be positive")
    if max_physical_steps <= 0:
        raise ValueError("auxiliary physical-step limit must be positive")

    if time_scale is None:
        physical_status = PHYSICAL_TIMING_UNAVAILABLE
        normalized_time_scale = None
    elif not math.isfinite(time_scale) or time_scale <= 0.0:
        physical_status = PHYSICAL_TIMING_INVALID
        normalized_time_scale = None
    else:
        physical_status = PHYSICAL_TIMING_AVAILABLE
        normalized_time_scale = float32(time_scale)

    pc = state.instruction_pointer
    elapsed = state.timer_elapsed
    fraction = state.timer_fraction
    timer_tick = 0
    physical_steps = 0
    intents: list[AuxiliaryDirectFireIntent] = []
    transforms: list[LiteralTransformDefinition] = []
    visited: set[tuple[int, int, int | None, int]] = set()
    instructions_scanned = 0

    for _ in range(max_instructions):
        fraction_key = (
            float32_bits(fraction)
            if physical_status == PHYSICAL_TIMING_AVAILABLE
            else None
        )
        visit = (pc, elapsed, fraction_key, timer_tick)
        if visit in visited:
            return _stop(
                intents=intents,
                transforms=transforms,
                scanned=instructions_scanned,
                reason=STOP_REPEATED_STATE,
                horizon=timer_tick_horizon,
                tick=timer_tick,
                physical_status=physical_status,
            )
        visited.add(visit)

        try:
            instruction = instruction_at(pc)
        except (KeyError, RuntimeError, ValueError):
            return _stop(
                intents=intents,
                transforms=transforms,
                scanned=instructions_scanned,
                reason="instruction_unavailable",
                horizon=timer_tick_horizon,
                tick=timer_tick,
                physical_status=physical_status,
            )
        instructions_scanned += 1
        if (
            instruction.address != pc
            or instruction.size < ECL_HEADER_SIZE
            or instruction.size > 0x400
            or len(instruction.payload)
            != instruction.size - ECL_HEADER_SIZE
        ):
            return _stop(
                intents=intents,
                transforms=transforms,
                scanned=instructions_scanned,
                reason="invalid_instruction",
                horizon=timer_tick_horizon,
                tick=timer_tick,
                physical_status=physical_status,
            )
        if instruction.time < elapsed:
            return _stop(
                intents=intents,
                transforms=transforms,
                scanned=instructions_scanned,
                reason="instruction_time_before_elapsed",
                horizon=timer_tick_horizon,
                tick=timer_tick,
                physical_status=physical_status,
            )
        wait_ticks = instruction.time - elapsed
        if timer_tick + wait_ticks > timer_tick_horizon:
            return _stop(
                intents=intents,
                transforms=transforms,
                scanned=instructions_scanned,
                reason=STOP_HORIZON,
                horizon=timer_tick_horizon,
                tick=timer_tick_horizon,
                physical_status=physical_status,
            )
        if wait_ticks:
            timer_tick += wait_ticks
            if (
                physical_status == PHYSICAL_TIMING_AVAILABLE
                and normalized_time_scale is not None
            ):
                waited = physical_wait(
                    elapsed=elapsed,
                    target=instruction.time,
                    fraction=fraction,
                    time_scale=normalized_time_scale,
                    used_steps=physical_steps,
                    maximum_steps=max_physical_steps,
                )
                if waited is None:
                    physical_status = PHYSICAL_TIMING_BUDGET_EXHAUSTED
                    elapsed = instruction.time
                else:
                    elapsed, fraction, physical_steps = waited
            else:
                elapsed = instruction.time

        physical_frame = (
            physical_steps
            if physical_status == PHYSICAL_TIMING_AVAILABLE
            else None
        )
        eligible = (
            active_difficulty_mask & instruction.difficulty_mask
        ) == active_difficulty_mask
        if not eligible:
            pc = instruction.address + instruction.size
            continue

        opcode = instruction.opcode
        if opcode == ECL_OP_TERMINATE:
            return _stop(
                intents=intents,
                transforms=transforms,
                scanned=instructions_scanned,
                reason=STOP_TERMINATE,
                horizon=timer_tick_horizon,
                tick=timer_tick,
                physical_status=physical_status,
            )
        if opcode == ECL_OP_JUMP:
            if instruction.parameter_mask or len(instruction.payload) != 8:
                reason = "nonliteral_jump"
            else:
                target_elapsed, relative_offset = struct.unpack(
                    "<ii",
                    instruction.payload,
                )
                target_pc = instruction.address + relative_offset
                if target_elapsed < 0:
                    reason = "invalid_jump_timer"
                elif not (
                    MINIMUM_RUNTIME_ADDRESS
                    <= target_pc
                    <= MAXIMUM_RUNTIME_ADDRESS
                ):
                    reason = "invalid_jump_target"
                else:
                    elapsed = target_elapsed
                    pc = target_pc
                    continue
            return _stop(
                intents=intents,
                transforms=transforms,
                scanned=instructions_scanned,
                reason=reason,
                horizon=timer_tick_horizon,
                tick=timer_tick,
                physical_status=physical_status,
            )
        if opcode == ECL_OP_DEFINE_BULLET_TRANSFORM:
            try:
                transforms.append(
                    decode_transform(
                        instruction,
                        timer_tick_offset=timer_tick,
                        physical_frame_offset=physical_frame,
                    )
                )
            except (ValueError, struct.error) as error:
                return _stop(
                    intents=intents,
                    transforms=transforms,
                    scanned=instructions_scanned,
                    reason=str(error),
                    horizon=timer_tick_horizon,
                    tick=timer_tick,
                    physical_status=physical_status,
                )
            pc = instruction.address + instruction.size
            continue
        if ECL_OP_FIRST_DIRECT_FIRE <= opcode <= ECL_OP_LAST_DIRECT_FIRE:
            try:
                intents.append(
                    decode_fire(
                        instruction,
                        timer_tick_offset=timer_tick,
                        physical_frame_offset=physical_frame,
                    )
                )
            except (ValueError, struct.error):
                return _stop(
                    intents=intents,
                    transforms=transforms,
                    scanned=instructions_scanned,
                    reason="invalid_direct_fire_payload",
                    horizon=timer_tick_horizon,
                    tick=timer_tick,
                    physical_status=physical_status,
                )
            pc = instruction.address + instruction.size
            continue
        return _stop(
            intents=intents,
            transforms=transforms,
            scanned=instructions_scanned,
            reason=f"unsupported_opcode:0x{opcode:02x}",
            horizon=timer_tick_horizon,
            tick=timer_tick,
            physical_status=physical_status,
        )

    return _stop(
        intents=intents,
        transforms=transforms,
        scanned=instructions_scanned,
        reason=STOP_INSTRUCTION_LIMIT,
        horizon=timer_tick_horizon,
        tick=timer_tick,
        physical_status=physical_status,
    )
