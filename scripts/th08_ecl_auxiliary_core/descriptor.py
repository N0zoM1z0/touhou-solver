"""Literal transform and direct-fire descriptor classification."""

from __future__ import annotations

import math
import struct

from th08_ecl_birth import (
    DIRECT_FIRE_PARAMETER_NAMES,
    INTENT_DYNAMIC_PARAMETER,
    INTENT_LITERAL_SCHEDULE,
    INTENT_PLAYER_AIM,
    INTENT_RNG,
    PLAYER_AIM_MODES,
    RNG_MODES,
    DirectFireArguments,
)
from th08_ecl_runtime import RuntimeEclInstruction
from th08_ecl_vm_state import float32_from_bits

from .constants import (
    DIRECT_FIRE_ARGUMENT_SIZE,
    ECL_OP_FIRST_DIRECT_FIRE,
    MAXIMUM_TRANSFORM_INDEX,
    TRANSFORM_ARGUMENT_SIZE,
)
from .model import AuxiliaryDirectFireIntent, LiteralTransformDefinition


def decode_transform(
    instruction: RuntimeEclInstruction,
    *,
    timer_tick_offset: int,
    physical_frame_offset: int | None,
) -> LiteralTransformDefinition:
    if instruction.parameter_mask:
        raise ValueError("nonliteral_transform")
    if len(instruction.payload) != TRANSFORM_ARGUMENT_SIZE:
        raise ValueError("invalid_transform_payload")
    (
        index,
        kind,
        wait_for_active_clear,
        integer_0,
        integer_1,
        float_0_bits,
        float_1_bits,
    ) = struct.unpack("<iiiiiII", instruction.payload)
    if not 0 <= index <= MAXIMUM_TRANSFORM_INDEX:
        raise ValueError("invalid_transform_index")
    if not all(
        math.isfinite(float32_from_bits(bits))
        for bits in (float_0_bits, float_1_bits)
    ):
        raise ValueError("nonfinite_transform_literal")
    return LiteralTransformDefinition(
        instruction_address=instruction.address,
        timer_tick_offset=timer_tick_offset,
        physical_frame_offset=physical_frame_offset,
        index=index,
        kind=kind,
        wait_for_active_clear=wait_for_active_clear,
        integer_0=integer_0,
        integer_1=integer_1,
        float_0_bits=float_0_bits,
        float_1_bits=float_1_bits,
    )


def _fire_dependencies(
    instruction: RuntimeEclInstruction,
    arguments: DirectFireArguments,
    *,
    physical_frame_offset: int | None,
) -> tuple[str, ...]:
    dependencies = [
        f"vm_parameter:{name}"
        for bit, name in DIRECT_FIRE_PARAMETER_NAMES
        if instruction.parameter_mask & bit
    ]
    unknown_parameter_bits = instruction.parameter_mask & ~0xFF
    if unknown_parameter_bits:
        dependencies.append(
            f"unknown_parameter_bits:0x{unknown_parameter_bits:x}"
        )
    literal_floats = (
        (0x10, arguments.speed1),
        (0x20, arguments.speed2),
        (0x40, arguments.angle1),
        (0x80, arguments.angle2),
    )
    if any(
        not instruction.parameter_mask & bit and not math.isfinite(value)
        for bit, value in literal_floats
    ):
        dependencies.append("nonfinite_literal")
    mode = instruction.opcode - ECL_OP_FIRST_DIRECT_FIRE
    if mode in PLAYER_AIM_MODES:
        dependencies.append("player_aim_at_emission")
    if mode in RNG_MODES:
        dependencies.append("gameplay_rng")
    dependencies.extend(
        (
            "owner_emission_guard",
            "source_lifetime",
            "spell_rank_state",
            "minimum_fire_distance",
        )
    )
    if arguments.transform_flags & (0x8000 | 0x10000):
        dependencies.append("route_or_enemy_fire_filter")
    dependencies.extend(
        (
            "bullet_template_geometry",
            "emission_origin",
            "deferred_state",
            "pool_capacity",
        )
    )
    if arguments.transform_flags:
        dependencies.extend(
            ("transform_program", "shared_transform_state")
        )
    if physical_frame_offset is None:
        dependencies.append("physical_time_scale")
    return tuple(dict.fromkeys(dependencies))


def decode_fire(
    instruction: RuntimeEclInstruction,
    *,
    timer_tick_offset: int,
    physical_frame_offset: int | None,
) -> AuxiliaryDirectFireIntent:
    if len(instruction.payload) != DIRECT_FIRE_ARGUMENT_SIZE:
        raise ValueError("invalid_direct_fire_payload")
    arguments = DirectFireArguments.decode(instruction.payload)
    mode = instruction.opcode - ECL_OP_FIRST_DIRECT_FIRE
    if instruction.parameter_mask:
        intent_status = INTENT_DYNAMIC_PARAMETER
    elif mode in RNG_MODES:
        intent_status = INTENT_RNG
    elif mode in PLAYER_AIM_MODES:
        intent_status = INTENT_PLAYER_AIM
    else:
        intent_status = INTENT_LITERAL_SCHEDULE
    if instruction.parameter_mask & (0x04 | 0x08):
        requested_bullets = None
    elif arguments.count1 <= 0 or arguments.count2 <= 0:
        requested_bullets = 0
    else:
        requested_bullets = arguments.count1 * arguments.count2
    return AuxiliaryDirectFireIntent(
        timer_tick_offset=timer_tick_offset,
        physical_frame_offset=physical_frame_offset,
        instruction_address=instruction.address,
        instruction_time=instruction.time,
        opcode=instruction.opcode,
        mode=mode,
        parameter_mask=instruction.parameter_mask,
        intent_status=intent_status,
        arguments=arguments,
        requested_bullets=requested_bullets,
        dependencies=_fire_dependencies(
            instruction,
            arguments,
            physical_frame_offset=physical_frame_offset,
        ),
    )
