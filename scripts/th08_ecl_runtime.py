#!/usr/bin/env python3
"""Minimal live TH08 ECL lookahead for pool-wide velocity callbacks.

This adapter reads the current enemy VM, follows only literal control flow,
and emits game-neutral velocity-change events. Unsupported expressions stop
the lookahead instead of guessing.
"""

from __future__ import annotations

import math
import struct
from dataclasses import dataclass
from typing import Callable, Protocol

from touhou_control.trajectory import VelocityChange


GAMEPLAY_TIME_SCALE_ADDRESS = 0x017CE8E0
ENEMY_MAIN_ECL_VM_OFFSET = 0x07F8
ECL_VM_TAG_MASK_OFFSET = 0x18
ECL_VM_CALLBACK_ANGLE_OFFSET = 0x38
ECL_VM_CALLBACK_SPEED_OFFSET = 0x3C
# The main VM timer begins immediately after the current-instruction pointer.
# Its root/previous value is +0x04, fractional elapsed is +0x08, and integer
# elapsed is +0x0C. VM +0x90 is a separate -999-gated wait timer.
ECL_VM_TIMER_OFFSET = 0x04
ECL_VM_TIMER_FRACTION_OFFSET = ECL_VM_TIMER_OFFSET + 0x04
ECL_VM_TIMER_ELAPSED_OFFSET = ECL_VM_TIMER_OFFSET + 0x08
ECL_VM_SNAPSHOT_SIZE = max(
    ECL_VM_TIMER_ELAPSED_OFFSET + 0x04,
    ECL_VM_CALLBACK_SPEED_OFFSET + 0x04,
)

ECL_HEADER_SIZE = 12
ECL_OP_TERMINATE = 0x01
ECL_OP_JUMP = 0x04
ECL_OP_SET_INT = 0x06
ECL_OP_SET_FLOAT = 0x07
ECL_OP_INVOKE_CALLBACK = 0x88

ECL_INT_TAG_MASK = 10000
ECL_FLOAT_CALLBACK_ANGLE = 10016
ECL_FLOAT_CALLBACK_SPEED = 10017
CALLBACK_TOGGLE_TAGGED_BULLET = 12


class ProcessMemoryReader(Protocol):
    def read(self, address: int, size: int) -> bytes: ...


@dataclass(frozen=True)
class EclVmSnapshot:
    instruction_pointer: int
    timer_fraction: float
    timer_elapsed: int
    tag_mask: int
    callback_angle: float
    callback_speed: float
    time_scale: float

    @property
    def timer_value(self) -> float:
        return self.timer_elapsed + self.timer_fraction


@dataclass(frozen=True)
class RuntimeEclInstruction:
    address: int
    time: int
    opcode: int
    size: int
    difficulty_mask: int
    parameter_mask: int
    payload: bytes


@dataclass(frozen=True)
class TaggedVelocityToggle:
    """One future callback that toggles bullets matching ``tag_mask``."""

    frame: int
    callback_index: int
    tag_mask: int
    alternate_velocity_x: float
    alternate_velocity_y: float


@dataclass(frozen=True)
class EclLookaheadResult:
    """Auditable result of following one live ECL control-flow path."""

    events: tuple[TaggedVelocityToggle, ...]
    instructions_scanned: int
    stop_reason: str
    horizon_covered: bool


class EclInstructionCache:
    """Cache immutable ECL instructions read from the target process."""

    def __init__(self) -> None:
        self._instructions: dict[int, RuntimeEclInstruction] = {}

    def clear(self) -> None:
        self._instructions.clear()

    def cached_instruction(self, address: int) -> RuntimeEclInstruction:
        """Return an immutable instruction without performing process I/O."""

        cached = self._instructions.get(address)
        if cached is None:
            raise RuntimeError(
                f"ECL instruction {address:#x} is absent from the warm cache"
            )
        return cached

    def instruction(
        self,
        read_memory: Callable[[int, int], bytes],
        address: int,
    ) -> RuntimeEclInstruction:
        cached = self._instructions.get(address)
        if cached is not None:
            return cached
        header = read_memory(address, ECL_HEADER_SIZE)
        time, opcode, size, _, difficulty_mask, parameter_mask = struct.unpack(
            "<iHHBBH",
            header,
        )
        if size < ECL_HEADER_SIZE or size > 0x400:
            raise ValueError(f"invalid live ECL instruction size {size}")
        payload = read_memory(
            address + ECL_HEADER_SIZE,
            size - ECL_HEADER_SIZE,
        )
        instruction = RuntimeEclInstruction(
            address,
            time,
            opcode,
            size,
            difficulty_mask,
            parameter_mask,
            payload,
        )
        self._instructions[address] = instruction
        return instruction


def read_main_ecl_vm_snapshot(
    reader: ProcessMemoryReader,
    enemy_pointer: int,
) -> EclVmSnapshot:
    if enemy_pointer <= 0:
        raise ValueError("enemy pointer must be positive")
    vm = reader.read(
        enemy_pointer + ENEMY_MAIN_ECL_VM_OFFSET,
        ECL_VM_SNAPSHOT_SIZE,
    )
    instruction_pointer = struct.unpack_from("<I", vm, 0)[0]
    tag_mask = struct.unpack_from("<I", vm, ECL_VM_TAG_MASK_OFFSET)[0]
    callback_angle = struct.unpack_from(
        "<f",
        vm,
        ECL_VM_CALLBACK_ANGLE_OFFSET,
    )[0]
    callback_speed = struct.unpack_from(
        "<f",
        vm,
        ECL_VM_CALLBACK_SPEED_OFFSET,
    )[0]
    timer_fraction = struct.unpack_from(
        "<f",
        vm,
        ECL_VM_TIMER_FRACTION_OFFSET,
    )[0]
    timer_elapsed = struct.unpack_from(
        "<i",
        vm,
        ECL_VM_TIMER_ELAPSED_OFFSET,
    )[0]
    time_scale = struct.unpack(
        "<f",
        reader.read(GAMEPLAY_TIME_SCALE_ADDRESS, 4),
    )[0]
    finite = (
        timer_fraction,
        callback_angle,
        callback_speed,
        time_scale,
    )
    if (
        instruction_pointer < 0x10000
        or not all(math.isfinite(value) for value in finite)
        or time_scale <= 0.0
    ):
        raise ValueError("invalid live ECL VM snapshot")
    return EclVmSnapshot(
        instruction_pointer,
        timer_fraction,
        timer_elapsed,
        tag_mask,
        callback_angle,
        callback_speed,
        time_scale,
    )


def _eligible(
    instruction: RuntimeEclInstruction,
    active_difficulty_mask: int,
) -> bool:
    return (
        active_difficulty_mask & instruction.difficulty_mask
    ) == active_difficulty_mask


def _literal_pair(instruction: RuntimeEclInstruction) -> tuple[int, int] | None:
    if len(instruction.payload) < 8:
        return None
    return struct.unpack_from("<ii", instruction.payload)


def predict_tagged_velocity_toggles(
    snapshot: EclVmSnapshot,
    *,
    instruction_at: Callable[[int], RuntimeEclInstruction],
    horizon_frames: int,
    active_difficulty_mask: int,
    max_instructions: int = 256,
) -> tuple[TaggedVelocityToggle, ...]:
    """Compatibility wrapper returning events from the audited lookahead."""

    return analyze_tagged_velocity_toggles(
        snapshot,
        instruction_at=instruction_at,
        horizon_frames=horizon_frames,
        active_difficulty_mask=active_difficulty_mask,
        max_instructions=max_instructions,
    ).events


def analyze_tagged_velocity_toggles(
    snapshot: EclVmSnapshot,
    *,
    instruction_at: Callable[[int], RuntimeEclInstruction],
    horizon_frames: int,
    active_difficulty_mask: int,
    max_instructions: int = 256,
) -> EclLookaheadResult:
    """Follow literal main-VM control flow and report why scanning stopped."""

    if horizon_frames < 0:
        raise ValueError("ECL lookahead horizon cannot be negative")
    if active_difficulty_mask <= 0:
        raise ValueError("active difficulty mask must be positive")
    pc = snapshot.instruction_pointer
    timer_value = snapshot.timer_value
    physical_frame = 0
    tag_mask = snapshot.tag_mask
    callback_angle = snapshot.callback_angle
    callback_speed = snapshot.callback_speed
    events: list[TaggedVelocityToggle] = []
    visited: set[tuple[int, int, int]] = set()
    instructions_scanned = 0
    stop_reason = "instruction_limit"
    horizon_covered = False

    for _ in range(max_instructions):
        state = (pc, int(math.floor(timer_value * 256.0)), physical_frame)
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
                break
            physical_frame += delta
            timer_value += delta * snapshot.time_scale

        eligible = _eligible(instruction, active_difficulty_mask)
        if eligible and instruction.opcode == ECL_OP_TERMINATE:
            stop_reason = "terminate"
            horizon_covered = True
            break
        if eligible and instruction.opcode == ECL_OP_JUMP:
            pair = _literal_pair(instruction)
            if pair is None or instruction.parameter_mask:
                stop_reason = "unsupported_jump"
                break
            target_time, relative_offset = pair
            pc = instruction.address + relative_offset
            timer_value = float(target_time)
            continue
        if eligible and instruction.opcode == ECL_OP_SET_INT:
            pair = _literal_pair(instruction)
            if pair is not None:
                destination, value = pair
                if (
                    destination == ECL_INT_TAG_MASK
                    and instruction.parameter_mask & 0x01
                    and not instruction.parameter_mask & 0x02
                ):
                    tag_mask = value & 0xFFFFFFFF
        elif eligible and instruction.opcode == ECL_OP_SET_FLOAT:
            pair = _literal_pair(instruction)
            if pair is not None:
                destination_bits, value_bits = pair
                destination = struct.unpack(
                    "<f",
                    struct.pack("<I", destination_bits & 0xFFFFFFFF),
                )[0]
                value = struct.unpack(
                    "<f",
                    struct.pack("<I", value_bits & 0xFFFFFFFF),
                )[0]
                if (
                    instruction.parameter_mask & 0x01
                    and not instruction.parameter_mask & 0x02
                    and math.isfinite(value)
                ):
                    if math.isclose(
                        destination,
                        float(ECL_FLOAT_CALLBACK_ANGLE),
                    ):
                        callback_angle = value
                    elif math.isclose(
                        destination,
                        float(ECL_FLOAT_CALLBACK_SPEED),
                    ):
                        callback_speed = value
        elif eligible and instruction.opcode == ECL_OP_INVOKE_CALLBACK:
            pair = _literal_pair(instruction)
            if pair is None or instruction.parameter_mask & 0x01:
                stop_reason = "unsupported_callback"
                break
            callback_index, _ = pair
            if (
                callback_index == CALLBACK_TOGGLE_TAGGED_BULLET
                and physical_frame > 0
                and tag_mask
                and all(
                    math.isfinite(value)
                    for value in (callback_angle, callback_speed)
                )
            ):
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
        pc = instruction.address + instruction.size
    else:
        stop_reason = "instruction_limit"
    return EclLookaheadResult(
        tuple(events),
        instructions_scanned,
        stop_reason,
        horizon_covered,
    )


def velocity_changes_for_tagged_bullet(
    *,
    tag_flags: int,
    phase_state: int,
    base_speed: float | None,
    base_angle: float | None,
    time_scale: float,
    toggles: tuple[TaggedVelocityToggle, ...],
) -> tuple[VelocityChange, ...]:
    """Lower TH08 callback-12 toggles to game-neutral velocity changes."""

    if (
        base_speed is None
        or base_angle is None
        or not math.isfinite(base_speed)
        or not math.isfinite(base_angle)
        or not math.isfinite(time_scale)
        or time_scale <= 0.0
    ):
        return ()
    state = phase_state
    changes: list[VelocityChange] = []
    for toggle in toggles:
        if toggle.callback_index != CALLBACK_TOGGLE_TAGGED_BULLET:
            continue
        if not tag_flags & toggle.tag_mask:
            continue
        if state == 1:
            state = 0
            velocity_x = toggle.alternate_velocity_x
            velocity_y = toggle.alternate_velocity_y
        else:
            state = 1
            speed = base_speed * time_scale
            velocity_x = math.cos(base_angle) * speed
            velocity_y = math.sin(base_angle) * speed
        changes.append(
            VelocityChange(toggle.frame, velocity_x, velocity_y)
        )
    return tuple(changes)
