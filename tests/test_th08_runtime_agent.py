#!/usr/bin/env python3
"""Tests for TH08's Windows-host input bridge helpers."""

from __future__ import annotations

import ctypes
import struct
import unittest
from unittest.mock import patch

import th08_runtime_agent


class _InputClockReader:
    def __init__(
        self,
        *,
        pointer: int = 0x20000000,
        msg_states: tuple[int, int] = (7, 7),
        manager_frames: tuple[int, int] = (123, 123),
        x_positions: tuple[float, float] = (10.0, 11.0),
        current_inputs: tuple[int, int] = (0x40, 0x40),
        time_scale_bits: int = 0x3F800000,
    ) -> None:
        self.pointer = pointer
        self.msg_states = list(msg_states)
        self.manager_frames = list(manager_frames)
        self.x_positions = list(x_positions)
        self.current_inputs = list(current_inputs)
        self.time_scale_bits = time_scale_bits

    @staticmethod
    def _take(values: list[int] | list[float]) -> int | float:
        return values.pop(0) if len(values) > 1 else values[0]

    def u32(self, address: int) -> int:
        if address == th08_runtime_agent.ADDR_ENEMY_MANAGER_FRAME:
            return int(self._take(self.manager_frames))
        if address == th08_runtime_agent.ADDR_GAMEPLAY_TIME_SCALE:
            return self.time_scale_bits
        if address == th08_runtime_agent.ADDR_FRSCREEN_UPDATE_SERIAL:
            return 500
        if address == th08_runtime_agent.ADDR_FRSCREEN_IMPL_POINTER:
            return self.pointer
        if address == th08_runtime_agent.ADDR_ENGINE_FLAGS:
            return 0x04
        if self.pointer and address == (
            self.pointer + th08_runtime_agent.FRSCREEN_MSG_RESOURCE_OFFSET
        ):
            return 0x30000000
        if self.pointer and address == (
            self.pointer + th08_runtime_agent.FRSCREEN_MSG_PC_OFFSET
        ):
            return 0x30000100
        raise AssertionError(f"unexpected u32 address {address:#x}")

    def i32(self, address: int) -> int:
        expected = self.pointer + th08_runtime_agent.FRSCREEN_MSG_STATE_OFFSET
        if address != expected:
            raise AssertionError(f"unexpected i32 address {address:#x}")
        return int(self._take(self.msg_states))

    def u16(self, address: int) -> int:
        if address == th08_runtime_agent.ADDR_CURRENT_INPUT:
            return int(self._take(self.current_inputs))
        if address in (
            th08_runtime_agent.ADDR_RAW_INPUT,
            th08_runtime_agent.ADDR_PREVIOUS_INPUT,
        ):
            return 0x40
        raise AssertionError(f"unexpected u16 address {address:#x}")

    def u8(self, address: int) -> int:
        if address == th08_runtime_agent.ADDR_SCRIPTED_UPDATE_FREEZE:
            return 0
        if address == th08_runtime_agent.ADDR_PLAYER:
            return 0
        raise AssertionError(f"unexpected u8 address {address:#x}")

    def f32(self, address: int) -> float:
        if address == (
            th08_runtime_agent.ADDR_PLAYER
            + th08_runtime_agent.PLAYER_POSITION_OFFSET
        ):
            return float(self._take(self.x_positions))
        if address == (
            th08_runtime_agent.ADDR_PLAYER
            + th08_runtime_agent.PLAYER_POSITION_OFFSET
            + 4
        ):
            return 20.0
        if address in (
            th08_runtime_agent.ADDR_PLAYER
            + th08_runtime_agent.PLAYER_VELOCITY_OFFSET,
            th08_runtime_agent.ADDR_PLAYER
            + th08_runtime_agent.PLAYER_VELOCITY_OFFSET
            + 4,
        ):
            return 1.0
        raise AssertionError(f"unexpected f32 address {address:#x}")


class Th08RuntimeAgentTests(unittest.TestCase):
    def test_time_scale_root_capture_is_frame_bracketed(self) -> None:
        stable = th08_runtime_agent.capture_time_scale_root(
            _InputClockReader(
                manager_frames=(123, 123),
                time_scale_bits=0x3F000000,
            )
        )
        self.assertTrue(stable.stable)
        self.assertEqual(stable.frame_before, 123)
        self.assertEqual(stable.frame_after, 123)
        self.assertEqual(stable.scale_bits, 0x3F000000)

        unstable = th08_runtime_agent.capture_time_scale_root(
            _InputClockReader(manager_frames=(123, 124))
        )
        self.assertFalse(unstable.stable)

    def test_process_reader_reuses_exact_read_buffer_without_copy(self) -> None:
        payloads = [b"abcd", b"WXYZ"]

        class Kernel32:
            @staticmethod
            def ReadProcessMemory(
                _handle, _address, buffer, size, count
            ) -> int:
                payload = payloads.pop(0)
                self.assertEqual(size, len(payload))
                ctypes.memmove(buffer, payload, size)
                count._obj.value = size
                return 1

        reader = th08_runtime_agent.ProcessReader.__new__(
            th08_runtime_agent.ProcessReader
        )
        reader.api = type("Api", (), {"kernel32": Kernel32()})()
        reader.handle = object()
        buffer = reader.allocate_buffer(4)

        returned = reader.read_into(0x1234, buffer)
        self.assertIs(returned, buffer)
        self.assertEqual(buffer.raw, b"abcd")
        self.assertIs(reader.read_into(0x1234, buffer), buffer)
        self.assertEqual(buffer.raw, b"WXYZ")

    def test_process_reader_read_keeps_bytes_compatibility(self) -> None:
        class Kernel32:
            @staticmethod
            def ReadProcessMemory(
                _handle, _address, buffer, size, count
            ) -> int:
                ctypes.memmove(buffer, b"data", size)
                count._obj.value = size
                return 1

        reader = th08_runtime_agent.ProcessReader.__new__(
            th08_runtime_agent.ProcessReader
        )
        reader.api = type("Api", (), {"kernel32": Kernel32()})()
        reader.handle = object()

        result = reader.read(0x5678, 4)

        self.assertIsInstance(result, bytes)
        self.assertEqual(result, b"data")

    def test_process_reader_rejects_nonpositive_buffer(self) -> None:
        with self.assertRaisesRegex(ValueError, "must be positive"):
            th08_runtime_agent.ProcessReader.allocate_buffer(0)

    def test_decode_spell_state_exposes_active_id_and_shift_jis_name(self) -> None:
        blob = bytearray(th08_runtime_agent.SPELL_STATE_PREFIX_SIZE)
        struct.pack_into("<III", blob, 0, 0x05, 0x12345678, 145)
        name = "禁薬「蓬莱の薬」".encode("shift_jis")
        blob[20 : 20 + len(name)] = name

        state = th08_runtime_agent.decode_spell_state(bytes(blob))

        self.assertTrue(state["active"])
        self.assertEqual(state["flags"], 0x05)
        self.assertEqual(state["enemy_pointer"], 0x12345678)
        self.assertEqual(state["spell_id"], 145)
        self.assertEqual(state["name"], "禁薬「蓬莱の薬」")
        self.assertIsNone(state["timer_elapsed"])

    def test_decode_spell_state_exposes_ecl_variable_10100_timer(self) -> None:
        blob = bytearray(th08_runtime_agent.SPELL_STATE_CAPTURE_SIZE)
        struct.pack_into("<III", blob, 0, 0x825, 0x12345678, 190)
        struct.pack_into(
            "<i",
            blob,
            th08_runtime_agent.SPELL_STATE_TIMER_ELAPSED_OFFSET,
            577,
        )

        state = th08_runtime_agent.decode_spell_state(bytes(blob))

        self.assertEqual(state["flags"], 0x825)
        self.assertEqual(state["timer_elapsed"], 577)
        self.assertEqual(th08_runtime_agent.SPELL_STATE_CAPTURE_SIZE, 0x114)

    def test_decode_spell_state_rejects_truncated_prefix(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires 68 bytes"):
            th08_runtime_agent.decode_spell_state(b"\0" * 67)

    def test_native_frscreen_clock_predicate_keeps_special_state_separate(
        self,
    ) -> None:
        self.assertFalse(
            th08_runtime_agent.frscreen_blocks_enemy_clock(0, 0)
        )
        self.assertFalse(
            th08_runtime_agent.frscreen_blocks_enemy_clock(1, -3)
        )
        self.assertFalse(
            th08_runtime_agent.frscreen_blocks_enemy_clock(1, -1)
        )
        self.assertTrue(
            th08_runtime_agent.frscreen_blocks_enemy_clock(1, -2)
        )
        self.assertTrue(
            th08_runtime_agent.frscreen_blocks_enemy_clock(1, 0)
        )
        self.assertTrue(
            th08_runtime_agent.frscreen_blocks_enemy_clock(1, 17)
        )

    def test_input_clock_capture_preserves_same_frame_displacement(self) -> None:
        sample = th08_runtime_agent.capture_input_clock_shadow(
            _InputClockReader()
        )

        self.assertTrue(sample["read_valid"])
        self.assertTrue(sample["manager_frame_stable"])
        self.assertTrue(sample["message_snapshot_stable"])
        self.assertTrue(sample["dialogue_active"])
        self.assertFalse(sample["frscreen_special_pause"])
        self.assertTrue(sample["native_manager_clock_blocked"])
        self.assertEqual(sample["player_before"]["x"], 10.0)
        self.assertEqual(sample["player_after"]["x"], 11.0)

    def test_input_clock_capture_marks_transition_interval_unknown(self) -> None:
        sample = th08_runtime_agent.capture_input_clock_shadow(
            _InputClockReader(msg_states=(-1, 0))
        )

        self.assertTrue(sample["read_valid"])
        self.assertFalse(sample["message_snapshot_stable"])
        self.assertIsNone(sample["native_manager_clock_blocked"])

    def test_input_clock_capture_does_not_hide_input_transition(self) -> None:
        sample = th08_runtime_agent.capture_input_clock_shadow(
            _InputClockReader(current_inputs=(0x40, 0x41))
        )

        self.assertFalse(sample["input_stable"])
        self.assertEqual(sample["input_before"]["current"], 0x40)
        self.assertEqual(sample["input_after"]["current"], 0x41)

    def test_null_message_pointer_is_unknown_for_shadow_classification(
        self,
    ) -> None:
        sample = th08_runtime_agent.capture_input_clock_shadow(
            _InputClockReader(pointer=0)
        )

        self.assertTrue(sample["read_valid"])
        self.assertFalse(sample["message_available"])
        self.assertIsNone(sample["native_manager_clock_blocked"])

    def test_optional_input_clock_read_failure_is_reported_not_raised(
        self,
    ) -> None:
        class BrokenReader:
            @staticmethod
            def u32(_address: int) -> int:
                raise OSError("probe unavailable")

        sample = th08_runtime_agent.capture_input_clock_shadow(BrokenReader())

        self.assertFalse(sample["read_valid"])
        self.assertIsNone(sample["native_manager_clock_blocked"])
        self.assertIn("probe unavailable", sample["error"])

    def test_recovery_releases_gameplay_keys_and_fast_forward_control(self) -> None:
        api = object()
        with (
            patch.object(th08_runtime_agent, "release_all") as release_all,
            patch.object(th08_runtime_agent, "send_scan_key") as send_scan_key,
        ):
            th08_runtime_agent.release_injected_keys(api)

        release_all.assert_called_once_with(api)
        send_scan_key.assert_called_once_with(api, scan_code=0x1D, pressed=False)

    def test_release_command_requires_explicit_arming(self) -> None:
        args = th08_runtime_agent.build_parser().parse_args(["release-inputs"])
        with self.assertRaisesRegex(RuntimeError, "explicit --armed"):
            args.func(args)

    def test_release_command_is_registered(self) -> None:
        args = th08_runtime_agent.build_parser().parse_args(
            ["release-inputs", "--armed"]
        )
        self.assertIs(args.func, th08_runtime_agent.command_release_inputs)


if __name__ == "__main__":
    unittest.main()
