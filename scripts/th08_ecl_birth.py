#!/usr/bin/env python3
"""Fail-closed TH08 main-VM classifier for future bullet-birth intent."""

from __future__ import annotations

import math
import struct
from dataclasses import dataclass
from typing import Callable

from th08_ecl_opcodes import opcode_spec
from th08_ecl_runtime import (
    LOOKAHEAD_COVERAGE_COMPLETE,
    LOOKAHEAD_COVERAGE_UNKNOWN,
    EclVmSnapshot,
    RuntimeEclInstruction,
)


ECL_OP_TERMINATE = 0x01
ECL_OP_RESET_TIMER = 0x02
ECL_OP_JUMP = 0x04
ECL_OP_LOOP_DECREMENT_JUMP = 0x05
ECL_OP_FIRST_CONDITIONAL_JUMP = 0x28
ECL_OP_LAST_CONDITIONAL_JUMP = 0x33
ECL_OP_CALL_SUBROUTINE = 0x34
ECL_OP_RETURN_SUBROUTINE = 0x35

ECL_OP_FIRST_CHILD_SOURCE = 0x5A
ECL_OP_LAST_CHILD_SOURCE = 0x5E
ECL_OP_SET_MINIMUM_FIRE_DISTANCE = 0x52
ECL_OP_CALL_SUBROUTINE_WITH_ENEMY = 0x58
ECL_OP_FIRST_DIRECT_FIRE = 0x60
ECL_OP_LAST_DIRECT_FIRE = 0x68
ECL_OP_SET_FIRE_DELAY = 0x69
ECL_OP_SET_FIRE_DELAY_RANDOM_PHASE = 0x6A
ECL_OP_ENABLE_DEFERRED_FIRE = 0x6B
ECL_OP_DISABLE_DEFERRED_FIRE = 0x6C
ECL_OP_EMIT_CURRENT_PATTERN = 0x6D
ECL_OP_SET_EMISSION_OFFSET = 0x6E
ECL_OP_DEFINE_BULLET_TRANSFORM = 0x6F

ECL_OP_INVOKE_INTERRUPT = 0x7D
ECL_OP_START_AUXILIARY_VM = 0x87
ECL_OP_INVOKE_CALLBACK = 0x88
ECL_OP_SET_CALLBACK = 0x89

DIRECT_FIRE_ARGUMENT_SIZE = 32
ENEMY_DEFERRED_FIRE_FLAG = 0x00020000
DIRECT_FIRE_PARAMETER_NAMES = (
    (0x01, "type"),
    (0x02, "color"),
    (0x04, "count1"),
    (0x08, "count2"),
    (0x10, "speed1"),
    (0x20, "speed2"),
    (0x40, "angle1"),
    (0x80, "angle2"),
)
PLAYER_AIM_MODES = frozenset((0, 2, 4))
RNG_MODES = frozenset((6, 7, 8))

INTENT_LITERAL_SCHEDULE = "literal_schedule"
INTENT_DYNAMIC_PARAMETER = "dynamic_parameter"
INTENT_PLAYER_AIM = "player_aim"
INTENT_RNG = "rng"
INTENT_DEFERRED = "deferred"
INTENT_CURRENT_PATTERN = "current_pattern"


@dataclass(frozen=True)
class DeferredFireStateObservation:
    """Capture-aligned enemy state controlling direct-fire dispatch."""

    spell_enemy_pointer: int
    observed_enemy_pointer: int | None
    enemy_flags: int | None
    frame_before: int | None
    frame_after: int | None
    ecl_frame_before: int | None
    ecl_frame_after: int | None
    status: str
    active: bool | None

    def record(self) -> dict[str, object]:
        return {
            "spell_enemy_pointer": self.spell_enemy_pointer,
            "observed_enemy_pointer": self.observed_enemy_pointer,
            "enemy_flags": self.enemy_flags,
            "deferred_fire_flag_mask": ENEMY_DEFERRED_FIRE_FLAG,
            "frame_before": self.frame_before,
            "frame_after": self.frame_after,
            "ecl_frame_before": self.ecl_frame_before,
            "ecl_frame_after": self.ecl_frame_after,
            "status": self.status,
            "active": self.active,
            "evidence_label": "observed_native_enemy_flags",
            "coverage_authority": "trace_only",
        }


def observe_deferred_fire_state(
    *,
    spell_enemy_pointer: int,
    observed_enemy_pointer: int | None,
    enemy_flags: int | None,
    frame_before: int | None,
    frame_after: int | None,
    ecl_frame_before: int | None,
    ecl_frame_after: int | None,
) -> DeferredFireStateObservation:
    """Use enemy +0x3324 only when it is aligned to the ECL VM capture."""

    status = "aligned_complete"
    active: bool | None = None
    if (
        observed_enemy_pointer is None
        or enemy_flags is None
    ):
        status = "enemy_flags_unavailable"
    elif (
        spell_enemy_pointer <= 0
        or observed_enemy_pointer != spell_enemy_pointer
    ):
        status = "enemy_pointer_mismatch"
    elif any(
        value is None
        for value in (
            frame_before,
            frame_after,
            ecl_frame_before,
            ecl_frame_after,
        )
    ):
        status = "capture_frames_unavailable"
    elif not (
        frame_before
        == frame_after
        == ecl_frame_before
        == ecl_frame_after
    ):
        status = "capture_misaligned"
    else:
        active = bool(enemy_flags & ENEMY_DEFERRED_FIRE_FLAG)
    return DeferredFireStateObservation(
        spell_enemy_pointer=spell_enemy_pointer,
        observed_enemy_pointer=observed_enemy_pointer,
        enemy_flags=enemy_flags,
        frame_before=frame_before,
        frame_after=frame_after,
        ecl_frame_before=ecl_frame_before,
        ecl_frame_after=ecl_frame_after,
        status=status,
        active=active,
    )


@dataclass(frozen=True)
class DirectFireArguments:
    bullet_type: int
    color: int
    count1: int
    count2: int
    speed1: float
    speed2: float
    angle1: float
    angle2: float
    transform_flags: int

    @classmethod
    def decode(cls, payload: bytes) -> DirectFireArguments:
        if len(payload) != DIRECT_FIRE_ARGUMENT_SIZE:
            raise ValueError(
                "direct-fire payload must contain exactly 32 bytes"
            )
        (
            bullet_type,
            color,
            count1,
            count2,
            speed1,
            speed2,
            angle1,
            angle2,
            transform_flags,
        ) = struct.unpack("<hhii4fI", payload)

        def signed_low_word(value: int) -> int:
            return struct.unpack("<h", struct.pack("<H", value & 0xFFFF))[0]

        return cls(
            bullet_type,
            color,
            signed_low_word(count1),
            signed_low_word(count2),
            speed1,
            speed2,
            angle1,
            angle2,
            transform_flags,
        )

    def record(self) -> dict[str, object]:
        return {
            "bullet_type": self.bullet_type,
            "color": self.color,
            "count1": self.count1,
            "count2": self.count2,
            "speed1": self.speed1,
            "speed2": self.speed2,
            "angle1": self.angle1,
            "angle2": self.angle2,
            "transform_flags": self.transform_flags,
        }


@dataclass(frozen=True)
class EclBirthIntent:
    """One possible emission instruction and every unresolved dependency."""

    instruction_frame: int
    activation_frame_support: tuple[int, int] | None
    instruction_address: int
    instruction_time: int
    opcode: int
    mode: int | None
    parameter_mask: int
    intent_status: str
    arguments: DirectFireArguments | None
    requested_bullets: int | None
    dependencies: tuple[str, ...]

    def record(self) -> dict[str, object]:
        return {
            "instruction_frame": self.instruction_frame,
            "activation_frame_support": (
                list(self.activation_frame_support)
                if self.activation_frame_support is not None
                else None
            ),
            "instruction_address": self.instruction_address,
            "instruction_time": self.instruction_time,
            "opcode": self.opcode,
            "mode": self.mode,
            "parameter_mask": self.parameter_mask,
            "intent_status": self.intent_status,
            "arguments": (
                self.arguments.record()
                if self.arguments is not None
                else None
            ),
            "requested_bullets": self.requested_bullets,
            "dependencies": list(self.dependencies),
            "coverage_authority": "trace_only",
        }


@dataclass(frozen=True)
class EclBirthLookaheadResult:
    intents: tuple[EclBirthIntent, ...]
    instructions_scanned: int
    stop_reason: str
    horizon_covered: bool
    requested_horizon_frames: int
    stop_frame: int

    def __post_init__(self) -> None:
        if self.requested_horizon_frames < 0:
            raise ValueError("birth lookahead horizon cannot be negative")
        if not 0 <= self.stop_frame <= self.requested_horizon_frames:
            raise ValueError("birth lookahead stop frame is outside its horizon")
        complete_stop = self.stop_reason in {"horizon", "terminate"}
        if self.horizon_covered != complete_stop:
            raise ValueError(
                "birth lookahead completeness disagrees with its stop reason"
            )

    @property
    def coverage_status(self) -> str:
        return (
            LOOKAHEAD_COVERAGE_COMPLETE
            if self.horizon_covered
            else LOOKAHEAD_COVERAGE_UNKNOWN
        )

    @property
    def covered_through_frame(self) -> int:
        if self.horizon_covered:
            return self.requested_horizon_frames
        return max(0, self.stop_frame - 1)

    @property
    def unknown_from_frame(self) -> int | None:
        if self.horizon_covered:
            return None
        return self.covered_through_frame + 1

    def record(self) -> dict[str, object]:
        return {
            "role": "trace_only_no_action_authority",
            "intents": [intent.record() for intent in self.intents],
            "instructions_scanned": self.instructions_scanned,
            "stop_reason": self.stop_reason,
            "horizon_covered": self.horizon_covered,
            "coverage": {
                "status": self.coverage_status,
                "requested_horizon_frames": self.requested_horizon_frames,
                "stop_frame": self.stop_frame,
                "covered_through_frame": self.covered_through_frame,
                "unknown_from_frame": self.unknown_from_frame,
                "result_kind": (
                    "complete_schedule"
                    if self.horizon_covered
                    else "prefix_only"
                ),
            },
        }


def _eligible(
    instruction: RuntimeEclInstruction,
    active_difficulty_mask: int,
) -> bool:
    return (
        active_difficulty_mask & instruction.difficulty_mask
    ) == active_difficulty_mask


def _literal_jump(
    instruction: RuntimeEclInstruction,
) -> tuple[int, int] | None:
    if len(instruction.payload) < 8 or instruction.parameter_mask:
        return None
    return struct.unpack_from("<ii", instruction.payload)


def _parameter_dependencies(parameter_mask: int) -> tuple[str, ...]:
    dependencies = [
        f"vm_parameter:{name}"
        for bit, name in DIRECT_FIRE_PARAMETER_NAMES
        if parameter_mask & bit
    ]
    unknown_bits = parameter_mask & ~0xFF
    if unknown_bits:
        dependencies.append(f"unknown_parameter_bits:0x{unknown_bits:x}")
    return tuple(dependencies)


def _requested_bullets(
    arguments: DirectFireArguments,
    *,
    parameter_mask: int,
    spell_active: bool | None,
) -> int | None:
    if parameter_mask & (0x04 | 0x08) or spell_active is not True:
        return None
    if arguments.count1 <= 0 or arguments.count2 <= 0:
        return 0
    return arguments.count1 * arguments.count2


def _direct_fire_intent(
    instruction: RuntimeEclInstruction,
    *,
    physical_frame: int,
    deferred_fire_active: bool | None,
    spell_active: bool | None,
    minimum_fire_distance_clear: bool | None,
    fire_filter_clear: bool | None,
    available_slots: int | None,
    template_geometry_resolved: bool,
    emission_origin_resolved: bool,
) -> EclBirthIntent:
    arguments = DirectFireArguments.decode(instruction.payload)
    mode = instruction.opcode - ECL_OP_FIRST_DIRECT_FIRE
    dependencies = list(
        _parameter_dependencies(instruction.parameter_mask)
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
    if mode in PLAYER_AIM_MODES:
        dependencies.append("player_aim_at_emission")
    if mode in RNG_MODES:
        dependencies.append("gameplay_rng")
    if spell_active is None:
        dependencies.append("spell_rank_state")
    elif not spell_active:
        dependencies.append("rank_adjustment")
    if minimum_fire_distance_clear is not True:
        dependencies.append("minimum_fire_distance")
    if (
        arguments.transform_flags & (0x8000 | 0x10000)
        and fire_filter_clear is not True
    ):
        dependencies.append("route_or_enemy_fire_filter")
    if not template_geometry_resolved:
        dependencies.append("bullet_template_geometry")
    if not emission_origin_resolved:
        dependencies.append("emission_origin")
    if arguments.transform_flags:
        dependencies.append("transform_program")
    if deferred_fire_active is None:
        dependencies.append("deferred_state")
    elif deferred_fire_active:
        dependencies.append("deferred_emission")

    requested_bullets = _requested_bullets(
        arguments,
        parameter_mask=instruction.parameter_mask,
        spell_active=spell_active,
    )
    if requested_bullets is None or available_slots is None:
        dependencies.append("pool_capacity")
    elif requested_bullets > available_slots:
        dependencies.append("pool_exhaustion")

    if deferred_fire_active is not False:
        status = INTENT_DEFERRED
        activation_support = None
    else:
        activation_support = (physical_frame, physical_frame)
        if instruction.parameter_mask:
            status = INTENT_DYNAMIC_PARAMETER
        elif mode in RNG_MODES:
            status = INTENT_RNG
        elif mode in PLAYER_AIM_MODES:
            status = INTENT_PLAYER_AIM
        else:
            status = INTENT_LITERAL_SCHEDULE
    return EclBirthIntent(
        instruction_frame=physical_frame,
        activation_frame_support=activation_support,
        instruction_address=instruction.address,
        instruction_time=instruction.time,
        opcode=instruction.opcode,
        mode=mode,
        parameter_mask=instruction.parameter_mask,
        intent_status=status,
        arguments=arguments,
        requested_bullets=requested_bullets,
        dependencies=tuple(dict.fromkeys(dependencies)),
    )


def _current_pattern_intent(
    instruction: RuntimeEclInstruction,
    *,
    physical_frame: int,
) -> EclBirthIntent:
    return EclBirthIntent(
        instruction_frame=physical_frame,
        activation_frame_support=(physical_frame, physical_frame),
        instruction_address=instruction.address,
        instruction_time=instruction.time,
        opcode=instruction.opcode,
        mode=None,
        parameter_mask=instruction.parameter_mask,
        intent_status=INTENT_CURRENT_PATTERN,
        arguments=None,
        requested_bullets=None,
        dependencies=(
            "current_emission_descriptor",
            "minimum_fire_distance",
            "bullet_template_geometry",
            "pool_capacity",
        ),
    )


def analyze_ecl_birth_intents(
    snapshot: EclVmSnapshot,
    *,
    instruction_at: Callable[[int], RuntimeEclInstruction],
    horizon_frames: int,
    active_difficulty_mask: int,
    deferred_fire_active: bool | None = None,
    spell_active: bool | None = None,
    minimum_fire_distance_clear: bool | None = None,
    fire_filter_clear: bool | None = None,
    available_slots: int | None = None,
    template_geometry_resolved: bool = False,
    emission_origin_resolved: bool = False,
    max_instructions: int = 256,
) -> EclBirthLookaheadResult:
    """Classify one literal main-VM path without forecasting bullet geometry."""

    if horizon_frames < 0:
        raise ValueError("ECL birth lookahead horizon cannot be negative")
    if active_difficulty_mask <= 0:
        raise ValueError("active difficulty mask must be positive")
    if max_instructions <= 0:
        raise ValueError("instruction limit must be positive")
    if (
        available_slots is not None
        and not 0 <= available_slots <= 1536
    ):
        raise ValueError("available slots must be in the native pool range")

    pc = snapshot.instruction_pointer
    timer_value = snapshot.timer_value
    physical_frame = 0
    deferred = deferred_fire_active
    intents: list[EclBirthIntent] = []
    visited: set[tuple[int, int, int, bool | None]] = set()
    instructions_scanned = 0
    stop_reason = "instruction_limit"
    horizon_covered = False

    for _ in range(max_instructions):
        state = (
            pc,
            int(math.floor(timer_value * 256.0)),
            physical_frame,
            deferred,
        )
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

        eligible = _eligible(instruction, active_difficulty_mask)
        if not eligible:
            pc = instruction.address + instruction.size
            continue

        opcode = instruction.opcode
        if opcode == ECL_OP_TERMINATE:
            stop_reason = "terminate"
            horizon_covered = True
            break
        if opcode == ECL_OP_JUMP:
            target = _literal_jump(instruction)
            if target is None:
                stop_reason = "unsupported_jump"
                break
            target_time, relative_offset = target
            pc = instruction.address + relative_offset
            timer_value = float(target_time)
            continue
        if opcode == ECL_OP_RESET_TIMER:
            stop_reason = "unsupported_timer_reset"
            break
        if (
            opcode == ECL_OP_LOOP_DECREMENT_JUMP
            or ECL_OP_FIRST_CONDITIONAL_JUMP
            <= opcode
            <= ECL_OP_LAST_CONDITIONAL_JUMP
            or opcode in (ECL_OP_CALL_SUBROUTINE, ECL_OP_RETURN_SUBROUTINE)
        ):
            stop_reason = "unsupported_control_flow"
            break
        if (
            opcode == ECL_OP_CALL_SUBROUTINE_WITH_ENEMY
            or ECL_OP_FIRST_CHILD_SOURCE
            <= opcode
            <= ECL_OP_LAST_CHILD_SOURCE
        ):
            stop_reason = "source_topology_change"
            break
        if opcode in (
            ECL_OP_SET_MINIMUM_FIRE_DISTANCE,
            ECL_OP_SET_FIRE_DELAY,
            ECL_OP_SET_FIRE_DELAY_RANDOM_PHASE,
            ECL_OP_SET_EMISSION_OFFSET,
            ECL_OP_DEFINE_BULLET_TRANSFORM,
        ):
            stop_reason = "unsupported_emission_state_mutation"
            break
        if opcode in (
            ECL_OP_INVOKE_INTERRUPT,
            ECL_OP_START_AUXILIARY_VM,
            ECL_OP_INVOKE_CALLBACK,
            ECL_OP_SET_CALLBACK,
        ):
            stop_reason = "unsupported_auxiliary_or_callback"
            break
        if opcode_spec(opcode).confidence == "unknown":
            stop_reason = "unknown_opcode"
            break
        if opcode == ECL_OP_ENABLE_DEFERRED_FIRE:
            deferred = True
        elif opcode == ECL_OP_DISABLE_DEFERRED_FIRE:
            deferred = False
        elif ECL_OP_FIRST_DIRECT_FIRE <= opcode <= ECL_OP_LAST_DIRECT_FIRE:
            try:
                intent = _direct_fire_intent(
                    instruction,
                    physical_frame=physical_frame,
                    deferred_fire_active=deferred,
                    spell_active=spell_active,
                    minimum_fire_distance_clear=(
                        minimum_fire_distance_clear
                    ),
                    fire_filter_clear=fire_filter_clear,
                    available_slots=available_slots,
                    template_geometry_resolved=template_geometry_resolved,
                    emission_origin_resolved=emission_origin_resolved,
                )
            except (ValueError, struct.error):
                stop_reason = "invalid_direct_fire_payload"
                break
            intents.append(intent)
        elif opcode == ECL_OP_EMIT_CURRENT_PATTERN:
            intents.append(
                _current_pattern_intent(
                    instruction,
                    physical_frame=physical_frame,
                )
            )

        pc = instruction.address + instruction.size
    else:
        stop_reason = "instruction_limit"

    return EclBirthLookaheadResult(
        intents=tuple(intents),
        instructions_scanned=instructions_scanned,
        stop_reason=stop_reason,
        horizon_covered=horizon_covered,
        requested_horizon_frames=horizon_frames,
        stop_frame=physical_frame,
    )


__all__ = [
    "DIRECT_FIRE_ARGUMENT_SIZE",
    "DIRECT_FIRE_PARAMETER_NAMES",
    "DirectFireArguments",
    "EclBirthIntent",
    "EclBirthLookaheadResult",
    "INTENT_CURRENT_PATTERN",
    "INTENT_DEFERRED",
    "INTENT_DYNAMIC_PARAMETER",
    "INTENT_LITERAL_SCHEDULE",
    "INTENT_PLAYER_AIM",
    "INTENT_RNG",
    "PLAYER_AIM_MODES",
    "RNG_MODES",
    "analyze_ecl_birth_intents",
]
