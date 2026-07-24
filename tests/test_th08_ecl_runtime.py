#!/usr/bin/env python3
"""Regression tests for TH08 live ECL callback lookahead."""

from __future__ import annotations

import math
import struct
import unittest
from pathlib import Path

from th08_ecl_runtime import (
    ECL_VM_CALLBACK_ANGLE_OFFSET,
    ECL_VM_CALLBACK_SPEED_OFFSET,
    ECL_VM_SNAPSHOT_SIZE,
    ECL_VM_TAG_MASK_OFFSET,
    ECL_VM_TIMER_ELAPSED_OFFSET,
    ECL_VM_TIMER_FRACTION_OFFSET,
    ENEMY_MAIN_ECL_VM_OFFSET,
    GAMEPLAY_TIME_SCALE_ADDRESS,
    ECL_OP_INVOKE_CALLBACK,
    ECL_OP_JUMP,
    ECL_OP_SET_INT,
    ECL_OP_TERMINATE,
    EclInstructionCache,
    EclVmSnapshot,
    TaggedVelocityToggle,
    analyze_tagged_velocity_toggles,
    predict_tagged_velocity_toggles,
    read_main_ecl_vm_snapshot,
    velocity_changes_for_tagged_bullet,
)


def _instruction(
    time: int,
    opcode: int,
    *arguments: int,
    parameter_mask: int = 0,
) -> bytes:
    size = 12 + 4 * len(arguments)
    return struct.pack(
        "<iHHBBH",
        time,
        opcode,
        size,
        0,
        0xFF,
        parameter_mask,
    ) + struct.pack(f"<{len(arguments)}i", *arguments)


class _Memory:
    def __init__(self, chunks: dict[int, bytes]) -> None:
        self.chunks = chunks

    def read(self, address: int, size: int) -> bytes:
        for base, data in self.chunks.items():
            if base <= address and address + size <= base + len(data):
                start = address - base
                return data[start : start + size]
        raise OSError(f"unmapped test address {address:#x}")


class EclRuntimeTests(unittest.TestCase):
    def test_reads_native_main_vm_timer_at_plus_04_08_0c(self) -> None:
        enemy = 0x580000
        vm = bytearray(ECL_VM_SNAPSHOT_SIZE)
        struct.pack_into("<I", vm, 0, 0x0B1D6FCC)
        struct.pack_into("<i", vm, 0x04, 199)
        struct.pack_into("<f", vm, ECL_VM_TIMER_FRACTION_OFFSET, 0.25)
        struct.pack_into("<i", vm, ECL_VM_TIMER_ELAPSED_OFFSET, 200)
        struct.pack_into("<I", vm, ECL_VM_TAG_MASK_OFFSET, 0x100000)
        struct.pack_into(
            "<f",
            vm,
            ECL_VM_CALLBACK_ANGLE_OFFSET,
            math.pi / 4,
        )
        struct.pack_into(
            "<f",
            vm,
            ECL_VM_CALLBACK_SPEED_OFFSET,
            1.5,
        )
        memory = _Memory(
            {
                enemy + ENEMY_MAIN_ECL_VM_OFFSET: bytes(vm),
                GAMEPLAY_TIME_SCALE_ADDRESS: struct.pack("<f", 1.0),
            }
        )
        snapshot = read_main_ecl_vm_snapshot(memory, enemy)
        self.assertEqual(snapshot.instruction_pointer, 0x0B1D6FCC)
        self.assertEqual(snapshot.timer_elapsed, 200)
        self.assertAlmostEqual(snapshot.timer_fraction, 0.25)
        self.assertEqual(snapshot.tag_mask, 0x100000)
        self.assertAlmostEqual(snapshot.callback_speed, 1.5)

    def test_predicts_literal_callback_after_current_timer(self) -> None:
        base = 0x500000
        code = b"".join(
            (
                _instruction(
                    450,
                    ECL_OP_SET_INT,
                    10000,
                    0x100000,
                    parameter_mask=1,
                ),
                _instruction(450, ECL_OP_INVOKE_CALLBACK, 12, 0),
                _instruction(451, ECL_OP_TERMINATE),
            )
        )
        memory = _Memory({base: code})
        cache = EclInstructionCache()
        snapshot = EclVmSnapshot(
            base,
            0.0,
            351,
            0,
            math.pi,
            0.0,
            1.0,
        )
        events = predict_tagged_velocity_toggles(
            snapshot,
            instruction_at=lambda address: cache.instruction(
                memory.read,
                address,
            ),
            horizon_frames=120,
            active_difficulty_mask=0x08,
        )
        self.assertEqual(len(events), 1)
        self.assertEqual((events[0].frame, events[0].tag_mask), (99, 0x100000))
        self.assertAlmostEqual(events[0].alternate_velocity_x, 0.0)
        self.assertAlmostEqual(events[0].alternate_velocity_y, 0.0)

    def test_literal_jump_preserves_periodic_callback_timing(self) -> None:
        callback_address = 0x600000
        jump_address = callback_address + 0x100
        relative = callback_address - jump_address
        memory = _Memory(
            {
                callback_address: b"".join(
                    (
                        _instruction(
                            350,
                            ECL_OP_INVOKE_CALLBACK,
                            12,
                            0,
                        ),
                        _instruction(351, ECL_OP_TERMINATE),
                    )
                ),
                jump_address: _instruction(
                    710,
                    ECL_OP_JUMP,
                    350,
                    relative,
                ),
            }
        )
        cache = EclInstructionCache()
        snapshot = EclVmSnapshot(
            jump_address,
            0.0,
            650,
            0x100000,
            0.0,
            0.0,
            1.0,
        )
        events = predict_tagged_velocity_toggles(
            snapshot,
            instruction_at=lambda address: cache.instruction(
                memory.read,
                address,
            ),
            horizon_frames=80,
            active_difficulty_mask=0x08,
        )
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].frame, 60)

    def test_real_spell111_sub63_loop_predicts_stop_and_resume(self) -> None:
        path = (
            Path(__file__).resolve().parents[1]
            / "artifacts"
            / "decoded"
            / "ecldata5.ecl"
        )
        code = path.read_bytes()
        base = 0x500000
        memory = _Memory({base: code})
        cache = EclInstructionCache()
        snapshot = EclVmSnapshot(
            base + 0x6FE8,
            0.0,
            600,
            0x100000,
            2.356194,
            0.0,
            1.0,
        )
        result = analyze_tagged_velocity_toggles(
            snapshot,
            instruction_at=lambda address: cache.instruction(
                memory.read,
                address,
            ),
            horizon_frames=256,
            active_difficulty_mask=0x08,
        )
        self.assertEqual(
            [(event.frame, event.tag_mask) for event in result.events],
            [(110, 0x100000), (210, 0x100000)],
        )
        self.assertEqual(result.stop_reason, "horizon")
        self.assertTrue(result.horizon_covered)

    def test_callback_toggle_lowers_to_stop_then_original_velocity(self) -> None:
        snapshot = EclVmSnapshot(
            0x500000,
            0.0,
            0,
            0x100000,
            0.0,
            0.0,
            1.0,
        )
        changes = velocity_changes_for_tagged_bullet(
            tag_flags=0x100202,
            phase_state=1,
            base_speed=2.0,
            base_angle=math.pi / 2,
            time_scale=snapshot.time_scale,
            toggles=(
                TaggedVelocityToggle(10, 12, 0x100000, 0.0, 0.0),
                TaggedVelocityToggle(110, 12, 0x100000, 0.0, 0.0),
            ),
        )
        self.assertEqual(len(changes), 2)
        self.assertEqual(
            (changes[0].frame, changes[0].velocity_x, changes[0].velocity_y),
            (10, 0.0, 0.0),
        )
        self.assertEqual(changes[1].frame, 110)
        self.assertAlmostEqual(changes[1].velocity_x, 0.0, places=6)
        self.assertAlmostEqual(changes[1].velocity_y, 2.0)


if __name__ == "__main__":
    unittest.main()
