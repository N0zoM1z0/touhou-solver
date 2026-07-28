"""Structurally independent byte oracle for literal auxiliary fire cycles."""

from __future__ import annotations

import math
import struct
from typing import AbstractSet


_ACTIVE_VM_BYTES = 0x228
_AUXILIARY_MARKER_OFFSET = 0x220
_MINIMUM_RUNTIME_ADDRESS = 0x00010000
_MAXIMUM_RUNTIME_ADDRESS = 0x7FFFFFFF
_HEADER_BYTES = 12
_OP_TERMINATE = 0x01
_OP_JUMP = 0x04
_FIRST_FIRE = 0x60
_LAST_FIRE = 0x68
_OP_TRANSFORM = 0x6F
_DIRECT_TIMER_THRESHOLD = 0.99000001


def _unknown(
    *,
    events: list[tuple[int, int | None, int, int, int]],
    transforms: list[tuple[int, int | None, int, int]],
    scanned: int,
    reason: str,
    horizon: int,
    tick: int,
    physical_timing_status: str,
) -> dict[str, object]:
    return {
        "events": tuple(events),
        "transforms": tuple(transforms),
        "instructions_scanned": scanned,
        "stop_reason": reason,
        "horizon_covered": reason in {"horizon", "terminate"},
        "requested_timer_tick_horizon": horizon,
        "stop_timer_tick": tick,
        "physical_timing_status": physical_timing_status,
    }


def _float32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def oracle_literal_fire_schedule(
    active_vm: bytes,
    image: bytes,
    *,
    runtime_base: int,
    instruction_offsets: AbstractSet[int],
    timer_tick_horizon: int,
    active_difficulty_mask: int,
    time_scale: float | None = None,
    max_instructions: int = 64,
    max_physical_steps: int = 65536,
) -> dict[str, object]:
    """Interpret raw bytes without importing the production transition code."""

    if timer_tick_horizon < 0:
        raise ValueError("oracle timer-tick horizon cannot be negative")
    if active_difficulty_mask <= 0:
        raise ValueError("oracle difficulty mask must be positive")
    if max_instructions <= 0:
        raise ValueError("oracle instruction limit must be positive")
    if max_physical_steps <= 0:
        raise ValueError("oracle physical-step limit must be positive")

    events: list[tuple[int, int | None, int, int, int]] = []
    transforms: list[tuple[int, int | None, int, int]] = []
    if time_scale is None:
        physical_status = "time_scale_unavailable"
        normalized_scale = None
    elif not math.isfinite(time_scale) or time_scale <= 0.0:
        physical_status = "time_scale_invalid"
        normalized_scale = None
    else:
        physical_status = "available"
        normalized_scale = _float32(time_scale)
    if len(active_vm) != _ACTIVE_VM_BYTES:
        return _unknown(
            events=events,
            transforms=transforms,
            scanned=0,
            reason="invalid_active_vm",
            horizon=timer_tick_horizon,
            tick=0,
            physical_timing_status=physical_status,
        )
    pc = struct.unpack_from("<I", active_vm, 0)[0]
    fraction = struct.unpack_from("<f", active_vm, 8)[0]
    elapsed = struct.unpack_from("<i", active_vm, 12)[0]
    marker = struct.unpack_from("<I", active_vm, _AUXILIARY_MARKER_OFFSET)[0]
    if not (
        _MINIMUM_RUNTIME_ADDRESS <= pc <= _MAXIMUM_RUNTIME_ADDRESS
        and math.isfinite(fraction)
        and 0.0 <= fraction < 1.0
        and elapsed >= 0
        and 1 <= marker <= 4
    ):
        return _unknown(
            events=events,
            transforms=transforms,
            scanned=0,
            reason="invalid_active_vm",
            horizon=timer_tick_horizon,
            tick=0,
            physical_timing_status=physical_status,
        )

    tick = 0
    physical_steps = 0
    scanned = 0
    visited: set[tuple[int, int, int | None, int]] = set()
    for _ in range(max_instructions):
        fraction_key = (
            struct.unpack("<I", struct.pack("<f", fraction))[0]
            if physical_status == "available"
            else None
        )
        state = (pc, elapsed, fraction_key, tick)
        if state in visited:
            return _unknown(
                events=events,
                transforms=transforms,
                scanned=scanned,
                reason="repeated_state",
                horizon=timer_tick_horizon,
                tick=tick,
                physical_timing_status=physical_status,
            )
        visited.add(state)

        offset = pc - runtime_base
        if offset not in instruction_offsets:
            return _unknown(
                events=events,
                transforms=transforms,
                scanned=scanned,
                reason="instruction_unavailable",
                horizon=timer_tick_horizon,
                tick=tick,
                physical_timing_status=physical_status,
            )
        if offset < 0 or offset + _HEADER_BYTES > len(image):
            return _unknown(
                events=events,
                transforms=transforms,
                scanned=scanned,
                reason="instruction_unavailable",
                horizon=timer_tick_horizon,
                tick=tick,
                physical_timing_status=physical_status,
            )
        (
            instruction_time,
            opcode,
            size,
            _byte_08,
            difficulty_mask,
            parameter_mask,
        ) = struct.unpack_from("<iHHBBH", image, offset)
        scanned += 1
        if (
            size < _HEADER_BYTES
            or size > 0x400
            or offset + size > len(image)
        ):
            return _unknown(
                events=events,
                transforms=transforms,
                scanned=scanned,
                reason="invalid_instruction",
                horizon=timer_tick_horizon,
                tick=tick,
                physical_timing_status=physical_status,
            )
        payload = image[offset + _HEADER_BYTES : offset + size]
        if instruction_time < elapsed:
            return _unknown(
                events=events,
                transforms=transforms,
                scanned=scanned,
                reason="instruction_time_before_elapsed",
                horizon=timer_tick_horizon,
                tick=tick,
                physical_timing_status=physical_status,
            )
        wait = instruction_time - elapsed
        if tick + wait > timer_tick_horizon:
            return _unknown(
                events=events,
                transforms=transforms,
                scanned=scanned,
                reason="horizon",
                horizon=timer_tick_horizon,
                tick=timer_tick_horizon,
                physical_timing_status=physical_status,
            )
        tick += wait
        if (
            wait
            and physical_status == "available"
            and normalized_scale is not None
        ):
            while elapsed < instruction_time:
                if physical_steps >= max_physical_steps:
                    physical_status = "physical_step_budget_exhausted"
                    elapsed = instruction_time
                    break
                if normalized_scale > _DIRECT_TIMER_THRESHOLD:
                    elapsed += 1
                else:
                    fraction = _float32(fraction + normalized_scale)
                    if fraction >= 1.0:
                        elapsed += 1
                        fraction = _float32(fraction - 1.0)
                physical_steps += 1
        else:
            elapsed = instruction_time
        physical_frame = (
            physical_steps if physical_status == "available" else None
        )

        eligible = (
            active_difficulty_mask & difficulty_mask
        ) == active_difficulty_mask
        if not eligible:
            pc += size
            continue
        if opcode == _OP_TERMINATE:
            return _unknown(
                events=events,
                transforms=transforms,
                scanned=scanned,
                reason="terminate",
                horizon=timer_tick_horizon,
                tick=tick,
                physical_timing_status=physical_status,
            )
        if opcode == _OP_JUMP:
            if parameter_mask or len(payload) != 8:
                reason = "nonliteral_jump"
            else:
                target_elapsed, relative = struct.unpack("<ii", payload)
                target_pc = pc + relative
                if target_elapsed < 0:
                    reason = "invalid_jump_timer"
                elif not (
                    _MINIMUM_RUNTIME_ADDRESS
                    <= target_pc
                    <= _MAXIMUM_RUNTIME_ADDRESS
                ):
                    reason = "invalid_jump_target"
                else:
                    elapsed = target_elapsed
                    pc = target_pc
                    continue
            return _unknown(
                events=events,
                transforms=transforms,
                scanned=scanned,
                reason=reason,
                horizon=timer_tick_horizon,
                tick=tick,
                physical_timing_status=physical_status,
            )
        if opcode == _OP_TRANSFORM:
            if parameter_mask:
                reason = "nonliteral_transform"
            elif len(payload) != 28:
                reason = "invalid_transform_payload"
            else:
                index = struct.unpack_from("<i", payload, 0)[0]
                float_0, float_1 = struct.unpack_from("<ff", payload, 20)
                if not 0 <= index <= 17:
                    reason = "invalid_transform_index"
                elif not math.isfinite(float_0) or not math.isfinite(float_1):
                    reason = "nonfinite_transform_literal"
                else:
                    transforms.append((tick, physical_frame, pc, index))
                    pc += size
                    continue
            return _unknown(
                events=events,
                transforms=transforms,
                scanned=scanned,
                reason=reason,
                horizon=timer_tick_horizon,
                tick=tick,
                physical_timing_status=physical_status,
            )
        if _FIRST_FIRE <= opcode <= _LAST_FIRE:
            if len(payload) != 32:
                return _unknown(
                    events=events,
                    transforms=transforms,
                    scanned=scanned,
                    reason="invalid_direct_fire_payload",
                    horizon=timer_tick_horizon,
                    tick=tick,
                    physical_timing_status=physical_status,
                )
            events.append(
                (tick, physical_frame, pc, opcode, parameter_mask)
            )
            pc += size
            continue
        return _unknown(
            events=events,
            transforms=transforms,
            scanned=scanned,
            reason=f"unsupported_opcode:0x{opcode:02x}",
            horizon=timer_tick_horizon,
            tick=tick,
            physical_timing_status=physical_status,
        )

    return _unknown(
        events=events,
        transforms=transforms,
        scanned=scanned,
        reason="instruction_limit",
        horizon=timer_tick_horizon,
        tick=tick,
        physical_timing_status=physical_status,
    )


__all__ = ["oracle_literal_fire_schedule"]
