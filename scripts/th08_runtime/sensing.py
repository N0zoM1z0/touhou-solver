"""Pure TH08 state decoding over a narrow process-reader protocol."""

from __future__ import annotations

import struct
import time
from dataclasses import dataclass
from typing import Protocol

from th08_runtime.game_state import (
    ADDR_CURRENT_INPUT,
    ADDR_DIFFICULTY_INDEX,
    ADDR_ENEMY_MANAGER_FRAME,
    ADDR_ENGINE_FLAGS,
    ADDR_FRSCREEN_IMPL_POINTER,
    ADDR_FRSCREEN_UPDATE_SERIAL,
    ADDR_GAMEPLAY_RNG,
    ADDR_GAMEPLAY_TIME_SCALE,
    ADDR_PLAYER,
    ADDR_PREVIOUS_INPUT,
    ADDR_RAW_INPUT,
    ADDR_ROUTE_ID,
    ADDR_RUN_STATE_INNER_POINTER,
    ADDR_SCRIPTED_UPDATE_FREEZE,
    ADDR_SPELL_CARD_STATE,
    ADDR_STAGE_ROUTE_INDEX,
    FRSCREEN_MSG_PC_OFFSET,
    FRSCREEN_MSG_RESOURCE_OFFSET,
    FRSCREEN_MSG_STATE_OFFSET,
    PLAYER_BOMB_ACTIVE_OFFSET,
    PLAYER_BOMB_INDEX_OFFSET,
    PLAYER_BOMB_LOCKOUT_OFFSET,
    PLAYER_BOMB_TIMER_OFFSET,
    PLAYER_FOCUS_LOGIC_OFFSET,
    PLAYER_FOCUS_TRANSITION_COUNTER_OFFSET,
    PLAYER_POSITION_OFFSET,
    PLAYER_PREDEATH_COUNTER_OFFSET,
    PLAYER_SECONDARY_CHARACTER_ACTIVE_OFFSET,
    PLAYER_VELOCITY_OFFSET,
    RUN_STATE_BOMBS_OFFSET,
    RUN_STATE_LIVES_OFFSET,
    RUN_STATE_POWER_OFFSET,
    SPELL_STATE_ACTIVE_FLAG,
    SPELL_STATE_CAPTURE_SIZE,
    SPELL_STATE_PREFIX_SIZE,
    SPELL_STATE_TIMER_ELAPSED_OFFSET,
)


class StateReader(Protocol):
    def read(self, address: int, size: int) -> bytes: ...

    def u8(self, address: int) -> int: ...

    def u16(self, address: int) -> int: ...

    def u32(self, address: int) -> int: ...

    def i32(self, address: int) -> int: ...

    def f32(self, address: int) -> float: ...


@dataclass(frozen=True)
class TimeScaleRootCapture:
    """One scale dword bracketed by the native enemy-manager frame."""

    frame_before: int
    scale_bits: int
    frame_after: int

    @property
    def stable(self) -> bool:
        return self.frame_before == self.frame_after


def capture_time_scale_root(reader: StateReader) -> TimeScaleRootCapture:
    """Bind a raw global-scale observation to one stable manager frame."""

    return TimeScaleRootCapture(
        frame_before=reader.u32(ADDR_ENEMY_MANAGER_FRAME),
        scale_bits=reader.u32(ADDR_GAMEPLAY_TIME_SCALE),
        frame_after=reader.u32(ADDR_ENEMY_MANAGER_FRAME),
    )


def decode_spell_state(blob: bytes) -> dict[str, object]:
    if len(blob) < SPELL_STATE_PREFIX_SIZE:
        raise ValueError(
            f"spell state prefix requires {SPELL_STATE_PREFIX_SIZE} bytes"
        )
    flags, enemy_pointer, spell_id = struct.unpack_from("<III", blob)
    encoded_name = blob[20:68].split(b"\0", 1)[0]
    return {
        "active": bool(flags & SPELL_STATE_ACTIVE_FLAG),
        "flags": flags,
        "enemy_pointer": enemy_pointer,
        "spell_id": spell_id,
        "name": encoded_name.decode("shift_jis", errors="replace"),
        "timer_elapsed": (
            struct.unpack_from("<i", blob, SPELL_STATE_TIMER_ELAPSED_OFFSET)[0]
            if len(blob) >= SPELL_STATE_CAPTURE_SIZE
            else None
        ),
    }


def frscreen_blocks_enemy_clock(
    impl_pointer: int,
    msg_state: int | None,
) -> bool:
    """Mirror the shipped predicate at 0x4358BB."""

    return bool(
        impl_pointer
        and msg_state is not None
        and (msg_state >= 0 or msg_state == -2)
    )


def capture_input_clock_shadow(reader: StateReader) -> dict[str, object]:
    """Capture a read-only interval around the native FRScreen clock gate."""

    monotonic_start_ns = time.perf_counter_ns()
    wall_time_ns = time.time_ns()
    try:
        manager_frame_before = reader.u32(ADDR_ENEMY_MANAGER_FRAME)
        update_serial_before = reader.u32(ADDR_FRSCREEN_UPDATE_SERIAL)
        impl_pointer_before = reader.u32(ADDR_FRSCREEN_IMPL_POINTER)
        engine_flags_before = reader.u32(ADDR_ENGINE_FLAGS)
        scripted_freeze_before = reader.u8(ADDR_SCRIPTED_UPDATE_FREEZE)
        msg_resource_before = (
            reader.u32(impl_pointer_before + FRSCREEN_MSG_RESOURCE_OFFSET)
            if impl_pointer_before
            else None
        )
        msg_pc_before = (
            reader.u32(impl_pointer_before + FRSCREEN_MSG_PC_OFFSET)
            if impl_pointer_before
            else None
        )
        msg_state_before = (
            reader.i32(impl_pointer_before + FRSCREEN_MSG_STATE_OFFSET)
            if impl_pointer_before
            else None
        )
        input_before = {
            "raw": reader.u16(ADDR_RAW_INPUT),
            "current": reader.u16(ADDR_CURRENT_INPUT),
            "previous": reader.u16(ADDR_PREVIOUS_INPUT),
        }
        player_before = {
            "phase": reader.u8(ADDR_PLAYER),
            "x": reader.f32(ADDR_PLAYER + PLAYER_POSITION_OFFSET),
            "y": reader.f32(ADDR_PLAYER + PLAYER_POSITION_OFFSET + 4),
            "dx": reader.f32(ADDR_PLAYER + PLAYER_VELOCITY_OFFSET),
            "dy": reader.f32(ADDR_PLAYER + PLAYER_VELOCITY_OFFSET + 4),
        }

        player_after = {
            "phase": reader.u8(ADDR_PLAYER),
            "x": reader.f32(ADDR_PLAYER + PLAYER_POSITION_OFFSET),
            "y": reader.f32(ADDR_PLAYER + PLAYER_POSITION_OFFSET + 4),
            "dx": reader.f32(ADDR_PLAYER + PLAYER_VELOCITY_OFFSET),
            "dy": reader.f32(ADDR_PLAYER + PLAYER_VELOCITY_OFFSET + 4),
        }
        input_after = {
            "raw": reader.u16(ADDR_RAW_INPUT),
            "current": reader.u16(ADDR_CURRENT_INPUT),
            "previous": reader.u16(ADDR_PREVIOUS_INPUT),
        }
        impl_pointer_after = reader.u32(ADDR_FRSCREEN_IMPL_POINTER)
        msg_resource_after = (
            reader.u32(impl_pointer_after + FRSCREEN_MSG_RESOURCE_OFFSET)
            if impl_pointer_after
            else None
        )
        msg_pc_after = (
            reader.u32(impl_pointer_after + FRSCREEN_MSG_PC_OFFSET)
            if impl_pointer_after
            else None
        )
        msg_state_after = (
            reader.i32(impl_pointer_after + FRSCREEN_MSG_STATE_OFFSET)
            if impl_pointer_after
            else None
        )
        scripted_freeze_after = reader.u8(ADDR_SCRIPTED_UPDATE_FREEZE)
        engine_flags_after = reader.u32(ADDR_ENGINE_FLAGS)
        update_serial_after = reader.u32(ADDR_FRSCREEN_UPDATE_SERIAL)
        manager_frame_after = reader.u32(ADDR_ENEMY_MANAGER_FRAME)
    except (OSError, RuntimeError, struct.error, ValueError) as error:
        monotonic_end_ns = time.perf_counter_ns()
        return {
            "read_valid": False,
            "error": f"{type(error).__name__}: {error}",
            "wall_time_ns": wall_time_ns,
            "monotonic_start_ns": monotonic_start_ns,
            "monotonic_end_ns": monotonic_end_ns,
            "capture_us": (monotonic_end_ns - monotonic_start_ns) / 1000.0,
            "dialogue_active": None,
            "frscreen_special_pause": None,
            "native_manager_clock_blocked": None,
        }

    monotonic_end_ns = time.perf_counter_ns()
    message_available = bool(
        impl_pointer_before
        and impl_pointer_after
        and msg_state_before is not None
        and msg_state_after is not None
    )
    message_snapshot_stable = bool(
        message_available
        and impl_pointer_before == impl_pointer_after
        and msg_state_before == msg_state_after
    )
    stable_msg_state = msg_state_after if message_snapshot_stable else None
    native_manager_clock_blocked = (
        frscreen_blocks_enemy_clock(impl_pointer_after, stable_msg_state)
        if message_snapshot_stable
        else None
    )
    return {
        "read_valid": True,
        "error": None,
        "wall_time_ns": wall_time_ns,
        "monotonic_start_ns": monotonic_start_ns,
        "monotonic_end_ns": monotonic_end_ns,
        "capture_us": (monotonic_end_ns - monotonic_start_ns) / 1000.0,
        "manager_frame_before": manager_frame_before,
        "manager_frame_after": manager_frame_after,
        "manager_frame_stable": manager_frame_before == manager_frame_after,
        "frscreen_update_serial_before": update_serial_before,
        "frscreen_update_serial_after": update_serial_after,
        "frscreen_update_serial_delta": (
            update_serial_after - update_serial_before
        )
        & 0xFFFFFFFF,
        "frscreen_impl_pointer_before": impl_pointer_before,
        "frscreen_impl_pointer_after": impl_pointer_after,
        "msg_resource_before": msg_resource_before,
        "msg_resource_after": msg_resource_after,
        "msg_pc_before": msg_pc_before,
        "msg_pc_after": msg_pc_after,
        "msg_state_before": msg_state_before,
        "msg_state_after": msg_state_after,
        "message_available": message_available,
        "message_snapshot_stable": message_snapshot_stable,
        "dialogue_active": (
            stable_msg_state >= 0 if stable_msg_state is not None else None
        ),
        "frscreen_special_pause": (
            stable_msg_state == -2 if stable_msg_state is not None else None
        ),
        "native_manager_clock_blocked": native_manager_clock_blocked,
        "scripted_update_freeze_before": scripted_freeze_before,
        "scripted_update_freeze_after": scripted_freeze_after,
        "engine_flags_before": engine_flags_before,
        "engine_flags_after": engine_flags_after,
        "engine_flags_stable": engine_flags_before == engine_flags_after,
        "input_before": input_before,
        "input_after": input_after,
        "input_stable": input_before == input_after,
        "player_before": player_before,
        "player_after": player_after,
    }


def observe_state(reader: StateReader) -> dict[str, object]:
    engine_flags = reader.u32(ADDR_ENGINE_FLAGS)
    inner = reader.u32(ADDR_RUN_STATE_INNER_POINTER)
    resources = None
    if inner and engine_flags & 0x04:
        resources = {
            "lives": reader.f32(inner + RUN_STATE_LIVES_OFFSET),
            "bombs": reader.f32(inner + RUN_STATE_BOMBS_OFFSET),
            "power": reader.f32(inner + RUN_STATE_POWER_OFFSET),
        }
    return {
        "wall_time_ns": time.time_ns(),
        "enemy_manager_frame": reader.u32(ADDR_ENEMY_MANAGER_FRAME),
        "time_scale_bits": reader.u32(ADDR_GAMEPLAY_TIME_SCALE),
        "engine_flags": engine_flags,
        "gameplay_active": bool(engine_flags & 0x04),
        "route_id": reader.u8(ADDR_ROUTE_ID),
        "stage_route_index": reader.u32(ADDR_STAGE_ROUTE_INDEX),
        "difficulty_index": reader.u32(ADDR_DIFFICULTY_INDEX),
        "input_raw": reader.u16(ADDR_RAW_INPUT),
        "input_current": reader.u16(ADDR_CURRENT_INPUT),
        "input_previous": reader.u16(ADDR_PREVIOUS_INPUT),
        "rng_state": reader.u16(ADDR_GAMEPLAY_RNG),
        "rng_calls": reader.u32(ADDR_GAMEPLAY_RNG + 4),
        "spell": decode_spell_state(
            reader.read(ADDR_SPELL_CARD_STATE, SPELL_STATE_CAPTURE_SIZE)
        ),
        "player": {
            "phase": reader.u8(ADDR_PLAYER),
            "focus_logic": reader.u8(
                ADDR_PLAYER + PLAYER_FOCUS_LOGIC_OFFSET
            ),
            "deathbomb": reader.u8(ADDR_PLAYER + 4),
            "secondary_character_active": bool(
                reader.u8(
                    ADDR_PLAYER
                    + PLAYER_SECONDARY_CHARACTER_ACTIVE_OFFSET
                )
                & 1
            ),
            "forced_bomb": reader.u8(ADDR_PLAYER + 6),
            "focus_transition_counter": reader.i32(
                ADDR_PLAYER + PLAYER_FOCUS_TRANSITION_COUNTER_OFFSET
            ),
            "x": reader.f32(ADDR_PLAYER + PLAYER_POSITION_OFFSET),
            "y": reader.f32(ADDR_PLAYER + PLAYER_POSITION_OFFSET + 4),
            "bomb_active": reader.u32(
                ADDR_PLAYER + PLAYER_BOMB_ACTIVE_OFFSET
            ),
            "bomb_index": reader.i32(ADDR_PLAYER + PLAYER_BOMB_INDEX_OFFSET),
            "bomb_timer": reader.i32(ADDR_PLAYER + PLAYER_BOMB_TIMER_OFFSET),
            "predeath_counter": reader.i32(
                ADDR_PLAYER + PLAYER_PREDEATH_COUNTER_OFFSET
            ),
            "bomb_lockout": reader.i32(
                ADDR_PLAYER + PLAYER_BOMB_LOCKOUT_OFFSET
            ),
        },
        "resources": resources,
    }
