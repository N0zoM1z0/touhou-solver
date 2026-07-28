#!/usr/bin/env python3
"""Independent-oracle tests for offline TH08 ECL VM-local interpretation."""

from __future__ import annotations

import math
import struct
import unittest
from pathlib import Path

from th08_ecl_vm_local_oracle import oracle_interpret, raw_instruction
from th08_ecl_runtime import (
    ECL_OP_CALL_SUBROUTINE,
    ECL_OP_FIRST_CONDITIONAL_JUMP,
    ECL_OP_INVOKE_CALLBACK,
    ECL_OP_LOOP_DECREMENT_JUMP,
    ECL_OP_SET_FLOAT,
    ECL_OP_TERMINATE,
    EclInstructionCache,
    EclVmSnapshot,
    RuntimeEclInstruction,
)
from th08_ecl_shadow import interpret_vm_local_shadow
from th08_ecl_vm_state import EclVmLocalProjection


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_BASE = 0x0B1C1430


def _instruction(
    address: int,
    opcode: int,
    *arguments: int,
    time: int = 0,
    parameter_mask: int = 0,
    difficulty_mask: int = 0xFF,
) -> RuntimeEclInstruction:
    payload = struct.pack(f"<{len(arguments)}i", *arguments)
    return RuntimeEclInstruction(
        address=address,
        time=time,
        opcode=opcode,
        size=12 + len(payload),
        difficulty_mask=difficulty_mask,
        parameter_mask=parameter_mask,
        payload=payload,
    )


def _snapshot(
    instruction_pointer: int,
    counter: int,
    *,
    angle_bits: int = 0,
    speed_bits: int = 0,
) -> EclVmSnapshot:
    projection = EclVmLocalProjection(
        (16, 1, 2, 3, 4, 5, 6, 7),
        (angle_bits, speed_bits, 2, 3, 4, 5, 6, 7),
        (counter, 8, 7, 6),
    )
    angle = struct.unpack("<f", struct.pack("<I", angle_bits))[0]
    speed = struct.unpack("<f", struct.pack("<I", speed_bits))[0]
    return EclVmSnapshot(
        instruction_pointer,
        0.0,
        0,
        16,
        angle,
        speed,
        1.0,
        projection,
    )


class _MappedEcl:
    def __init__(self, code: bytes) -> None:
        self.code = code

    def read(self, address: int, size: int) -> bytes:
        start = address - RUNTIME_BASE
        end = start + size
        if size <= 0 or start < 0 or end > len(self.code):
            raise OSError(f"invalid mapped ECL read at {address:#x}")
        return self.code[start:end]


class EclVmLocalShadowTests(unittest.TestCase):
    def test_loop_counters_match_independent_scalar_oracle(self) -> None:
        base = 0x500000
        loop = _instruction(
            base,
            ECL_OP_LOOP_DECREMENT_JUMP,
            0,
            0,
            10036,
            parameter_mask=0x04,
        )
        terminate = _instruction(base + loop.size, ECL_OP_TERMINATE)
        instructions = {
            loop.address: loop,
            terminate.address: terminate,
        }
        raw = {
            address: raw_instruction(instruction)
            for address, instruction in instructions.items()
        }

        for counter in (0, 1, 2, 7):
            with self.subTest(counter=counter):
                result = interpret_vm_local_shadow(
                    _snapshot(base, counter),
                    instruction_at=instructions.__getitem__,
                    horizon_frames=20,
                    active_difficulty_mask=0x08,
                    max_instructions=64,
                )
                oracle = oracle_interpret(
                    raw,
                    start=base,
                    counter=counter,
                )
                assert result.final_projection is not None
                self.assertEqual(result.stop_reason, oracle["reason"])
                self.assertEqual(
                    result.instructions_scanned,
                    oracle["scanned"],
                )
                self.assertEqual(
                    result.final_instruction_pointer,
                    oracle["pc"],
                )
                self.assertEqual(result.final_timer_value, oracle["timer"])
                self.assertEqual(result.stop_frame, oracle["physical_frame"])
                self.assertEqual(
                    result.final_projection.scratch_integers[0],
                    oracle["variables"][10036],
                )

    def test_old_snapshot_aliases_distinct_loop_successors(self) -> None:
        base = 0x510000
        loop = _instruction(
            base,
            ECL_OP_LOOP_DECREMENT_JUMP,
            0,
            0,
            10036,
            parameter_mask=0x04,
        )
        terminate = _instruction(base + loop.size, ECL_OP_TERMINATE)
        instructions = {base: loop, terminate.address: terminate}

        one = interpret_vm_local_shadow(
            _snapshot(base, 1),
            instruction_at=instructions.__getitem__,
            horizon_frames=20,
            active_difficulty_mask=0x08,
        )
        two = interpret_vm_local_shadow(
            _snapshot(base, 2),
            instruction_at=instructions.__getitem__,
            horizon_frames=20,
            active_difficulty_mask=0x08,
        )

        self.assertEqual(one.instructions_scanned, 2)
        self.assertEqual(two.instructions_scanned, 3)
        self.assertEqual(one.stop_reason, "terminate")
        self.assertEqual(two.stop_reason, "terminate")

    def test_missing_and_literal_loop_state_remain_unknown(self) -> None:
        base = 0x520000
        literal_loop = _instruction(
            base,
            ECL_OP_LOOP_DECREMENT_JUMP,
            0,
            0,
            3,
            parameter_mask=0,
        )
        plain = EclVmSnapshot(base, 0.0, 0, 16, 0.0, 0.0, 1.0)

        missing = interpret_vm_local_shadow(
            plain,
            instruction_at=lambda _address: literal_loop,
            horizon_frames=20,
            active_difficulty_mask=0x08,
        )
        literal = interpret_vm_local_shadow(
            _snapshot(base, 3),
            instruction_at=lambda _address: literal_loop,
            horizon_frames=20,
            active_difficulty_mask=0x08,
        )

        self.assertEqual(missing.stop_reason, "missing_local_projection")
        self.assertEqual(missing.instructions_scanned, 0)
        self.assertEqual(
            literal.stop_reason,
            "unsupported_literal_lvalue_loop",
        )
        unsupported_lvalue = _instruction(
            base,
            ECL_OP_LOOP_DECREMENT_JUMP,
            0,
            0,
            10008,
            parameter_mask=0x04,
        )
        unsupported = interpret_vm_local_shadow(
            _snapshot(base, 3),
            instruction_at=lambda _address: unsupported_lvalue,
            horizon_frames=20,
            active_difficulty_mask=0x08,
        )
        self.assertEqual(unsupported.stop_reason, "unsupported_loop_lvalue")

    def test_rng_call_and_dynamic_branch_remain_unknown(self) -> None:
        base = 0x530000
        cases = (
            (_instruction(base, 0x18, 10037, 10032, 5), "unsupported_opcode_0018"),
            (
                _instruction(base, ECL_OP_CALL_SUBROUTINE, 1, 0),
                "unsupported_control_flow",
            ),
            (
                _instruction(
                    base,
                    ECL_OP_FIRST_CONDITIONAL_JUMP + 0x0B,
                    0,
                    0,
                    10050,
                ),
                "unsupported_control_flow",
            ),
        )
        for instruction, expected in cases:
            with self.subTest(opcode=instruction.opcode):
                result = interpret_vm_local_shadow(
                    _snapshot(base, 3),
                    instruction_at=lambda _address, item=instruction: item,
                    horizon_frames=20,
                    active_difficulty_mask=0x08,
                )
                self.assertEqual(result.stop_reason, expected)
                self.assertEqual(result.instructions_scanned, 1)

    def test_capture_after_rng_may_use_committed_counter_only_until_rng(
        self,
    ) -> None:
        base = 0x535000
        rng = _instruction(base, 0x18, 10037, 10032, 5)
        loop = _instruction(
            base + rng.size,
            ECL_OP_LOOP_DECREMENT_JUMP,
            0,
            0,
            10036,
            parameter_mask=0x04,
        )
        terminate = _instruction(loop.address + loop.size, ECL_OP_TERMINATE)
        instructions = {
            rng.address: rng,
            loop.address: loop,
            terminate.address: terminate,
        }

        before_rng = interpret_vm_local_shadow(
            _snapshot(base, 2),
            instruction_at=instructions.__getitem__,
            horizon_frames=20,
            active_difficulty_mask=0x08,
        )
        after_rng = interpret_vm_local_shadow(
            _snapshot(loop.address, 2),
            instruction_at=instructions.__getitem__,
            horizon_frames=20,
            active_difficulty_mask=0x08,
        )

        self.assertEqual(before_rng.stop_reason, "unsupported_opcode_0018")
        self.assertEqual(after_rng.stop_reason, "terminate")

    def test_int32_decrement_wraps_like_the_shipped_dword(self) -> None:
        base = 0x540000
        loop = _instruction(
            base,
            ECL_OP_LOOP_DECREMENT_JUMP,
            0,
            0x20,
            10036,
            parameter_mask=0x04,
        )
        unsupported = _instruction(base + 0x20, 0x63)
        result = interpret_vm_local_shadow(
            _snapshot(base, -(1 << 31)),
            instruction_at={
                base: loop,
                base + 0x20: unsupported,
            }.__getitem__,
            horizon_frames=20,
            active_difficulty_mask=0x08,
        )

        assert result.final_projection is not None
        self.assertEqual(
            result.final_projection.scratch_integers[0],
            (1 << 31) - 1,
        )
        self.assertEqual(result.final_instruction_pointer, base + 0x20)

    def test_float_literal_preserves_signed_zero_and_rejects_nan(self) -> None:
        base = 0x550000
        destination = struct.unpack("<i", struct.pack("<f", 10016.0))[0]
        negative_zero = _instruction(
            base,
            ECL_OP_SET_FLOAT,
            destination,
            -(1 << 31),
            parameter_mask=0x01,
        )
        terminate = _instruction(
            base + negative_zero.size,
            ECL_OP_TERMINATE,
        )
        instructions = {base: negative_zero, terminate.address: terminate}
        exact = interpret_vm_local_shadow(
            _snapshot(base, 1),
            instruction_at=instructions.__getitem__,
            horizon_frames=20,
            active_difficulty_mask=0x08,
        )
        assert exact.final_projection is not None
        self.assertEqual(exact.final_projection.float_local_bits[0], 0x80000000)

        nan_write = _instruction(
            base,
            ECL_OP_SET_FLOAT,
            destination,
            0x7FC12345,
            parameter_mask=0x01,
        )
        rejected = interpret_vm_local_shadow(
            _snapshot(base, 1),
            instruction_at=lambda _address: nan_write,
            horizon_frames=20,
            active_difficulty_mask=0x08,
        )
        assert rejected.final_projection is not None
        self.assertEqual(
            rejected.stop_reason,
            "unsupported_nonfinite_float_write",
        )
        self.assertEqual(rejected.final_projection.float_local_bits[0], 0)

    def test_angle_normalization_stays_unknown_at_both_pi_boundaries(
        self,
    ) -> None:
        base = 0x558000
        destination = struct.unpack("<i", struct.pack("<f", 10016.0))[0]
        normalize = _instruction(
            base,
            0x25,
            destination,
            parameter_mask=0x01,
        )
        for angle in (math.pi, -math.pi):
            bits = struct.unpack("<I", struct.pack("<f", angle))[0]
            with self.subTest(angle=angle):
                result = interpret_vm_local_shadow(
                    _snapshot(base, 1, angle_bits=bits),
                    instruction_at=lambda _address: normalize,
                    horizon_frames=20,
                    active_difficulty_mask=0x08,
                )
                assert result.final_projection is not None
                self.assertEqual(
                    result.stop_reason,
                    "unsupported_opcode_0025",
                )
                self.assertEqual(
                    result.final_projection.float_local_bits[0],
                    bits,
                )

    def test_callback_schedule_uses_mutated_projected_fields(self) -> None:
        base = 0x560000
        callback = _instruction(
            base,
            ECL_OP_INVOKE_CALLBACK,
            12,
            0,
            time=1,
        )
        terminate = _instruction(base + callback.size, ECL_OP_TERMINATE, time=1)
        instructions = {base: callback, terminate.address: terminate}

        result = interpret_vm_local_shadow(
            _snapshot(base, 1, angle_bits=0, speed_bits=0x3F800000),
            instruction_at=instructions.__getitem__,
            horizon_frames=20,
            active_difficulty_mask=0x08,
        )

        self.assertEqual(result.stop_reason, "terminate")
        self.assertEqual(len(result.events), 1)
        self.assertEqual(
            (result.events[0].frame, result.events[0].tag_mask),
            (1, 16),
        )
        self.assertAlmostEqual(result.events[0].alternate_velocity_x, 1.0)
        self.assertAlmostEqual(result.events[0].alternate_velocity_y, 0.0)

    def test_shipped_spell57_resolves_one_loop_then_stops_safely(self) -> None:
        code = (ROOT / "artifacts/decoded/ecldata4asp.ecl").read_bytes()
        mapped = _MappedEcl(code)
        cache = EclInstructionCache()

        def instruction_at(address: int) -> RuntimeEclInstruction:
            return cache.instruction(mapped.read, address)

        branch = interpret_vm_local_shadow(
            _snapshot(RUNTIME_BASE + 0x3510, 2),
            instruction_at=instruction_at,
            horizon_frames=256,
            active_difficulty_mask=0x08,
        )
        fallthrough = interpret_vm_local_shadow(
            _snapshot(RUNTIME_BASE + 0x3510, 1),
            instruction_at=instruction_at,
            horizon_frames=256,
            active_difficulty_mask=0x08,
        )

        assert branch.final_projection is not None
        assert fallthrough.final_projection is not None
        self.assertEqual(branch.stop_reason, "unsupported_opcode_0063")
        self.assertEqual(
            branch.final_instruction_pointer,
            RUNTIME_BASE + 0x34C0,
        )
        self.assertEqual(branch.final_projection.scratch_integers[0], 1)
        self.assertEqual(fallthrough.stop_reason, "unsupported_opcode_0018")
        self.assertEqual(
            fallthrough.final_instruction_pointer,
            RUNTIME_BASE + 0x353C,
        )
        self.assertEqual(fallthrough.final_projection.scratch_integers[0], 4)


if __name__ == "__main__":
    unittest.main()
