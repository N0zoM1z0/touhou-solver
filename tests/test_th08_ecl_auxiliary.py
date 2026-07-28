from __future__ import annotations

import hashlib
import math
import struct
import unittest
from pathlib import Path

from analysis.auxiliary_ecl_event import oracle_literal_fire_schedule
from th08_ecl_auxiliary import (
    PHYSICAL_TIMING_AVAILABLE,
    PHYSICAL_TIMING_BUDGET_EXHAUSTED,
    PHYSICAL_TIMING_UNAVAILABLE,
    AuxiliaryEclVmState,
    AuxiliaryLiteralFireRequest,
    build_exact_runtime_instruction_index,
    lower_auxiliary_literal_fire_batch,
    lower_auxiliary_literal_fire_cycle,
)
from th08_ecl_runtime import RuntimeEclInstruction
from th08_ecl_tool.core import parse_ecl


_BASE = 0x500000
_ROOT = _BASE + 0x100
_DIFFICULTY = 0x08


def _active_vm(
    pc: int,
    *,
    elapsed: int = 0,
    fraction: float = 0.0,
    marker: int = 1,
) -> bytes:
    vm = bytearray(0x228)
    struct.pack_into("<I", vm, 0, pc)
    struct.pack_into("<i", vm, 4, elapsed - 1)
    struct.pack_into("<f", vm, 8, fraction)
    struct.pack_into("<i", vm, 12, elapsed)
    struct.pack_into("<8i", vm, 0x18, *range(100, 108))
    struct.pack_into("<8f", vm, 0x38, *[float(value) for value in range(8)])
    struct.pack_into("<4i", vm, 0x58, 8, 7, 6, 5)
    struct.pack_into("<I", vm, 0x220, marker)
    return bytes(vm)


def _header(
    *,
    time: int,
    opcode: int,
    payload: bytes = b"",
    difficulty: int = 0xFF,
    parameter_mask: int = 0,
) -> bytes:
    return struct.pack(
        "<iHHBBH",
        time,
        opcode,
        12 + len(payload),
        0,
        difficulty,
        parameter_mask,
    ) + payload


def _synthetic_cycle(
    *,
    period: int = 8,
    transform_parameter_mask: int = 0,
    jump_parameter_mask: int = 0,
    jump_target_delta: int | None = None,
) -> tuple[bytes, dict[int, RuntimeEclInstruction], frozenset[int]]:
    transform_payload = struct.pack(
        "<iiiii2f",
        0,
        0x400000,
        1,
        900,
        -1,
        -1.0,
        -1.0,
    )
    fire_payload = struct.pack(
        "<hhii4fI",
        16,
        10007,
        2,
        1,
        1.3,
        0.5,
        math.pi / 2.0,
        0.0,
        0x501202,
    )
    transform = _header(
        time=0,
        opcode=0x6F,
        payload=transform_payload,
        parameter_mask=transform_parameter_mask,
    )
    fire = _header(
        time=0,
        opcode=0x63,
        payload=fire_payload,
        parameter_mask=0x02,
    )
    transform_address = _ROOT
    fire_address = transform_address + len(transform)
    jump_address = fire_address + len(fire)
    relative = (
        fire_address - jump_address
        if jump_target_delta is None
        else jump_target_delta
    )
    jump = _header(
        time=period,
        opcode=0x04,
        payload=struct.pack("<ii", 0, relative),
        parameter_mask=jump_parameter_mask,
    )
    image = bytearray(0x400)
    index: dict[int, RuntimeEclInstruction] = {}
    for address, raw in (
        (transform_address, transform),
        (fire_address, fire),
        (jump_address, jump),
    ):
        offset = address - _BASE
        image[offset : offset + len(raw)] = raw
        time, opcode, size, _, difficulty, parameter_mask = struct.unpack_from(
            "<iHHBBH",
            raw,
        )
        index[address] = RuntimeEclInstruction(
            address=address,
            time=time,
            opcode=opcode,
            size=size,
            difficulty_mask=difficulty,
            parameter_mask=parameter_mask,
            payload=raw[12:],
        )
    return bytes(image), index, frozenset(address - _BASE for address in index)


def _single_instruction_program(
    raw: bytes,
) -> tuple[bytes, dict[int, RuntimeEclInstruction], frozenset[int]]:
    image = bytearray(0x400)
    image[_ROOT - _BASE : _ROOT - _BASE + len(raw)] = raw
    time, opcode, size, _, difficulty, parameter_mask = struct.unpack_from(
        "<iHHBBH",
        raw,
    )
    instruction = RuntimeEclInstruction(
        _ROOT,
        time,
        opcode,
        size,
        difficulty,
        parameter_mask,
        raw[12:size] if size >= 12 else b"",
    )
    return (
        bytes(image),
        {_ROOT: instruction},
        frozenset((_ROOT - _BASE,)),
    )


def _core_record(result: object) -> dict[str, object]:
    return {
        "events": tuple(
            (
                intent.timer_tick_offset,
                intent.physical_frame_offset,
                intent.instruction_address,
                intent.opcode,
                intent.parameter_mask,
            )
            for intent in result.intents
        ),
        "transforms": tuple(
            (
                definition.timer_tick_offset,
                definition.physical_frame_offset,
                definition.instruction_address,
                definition.index,
            )
            for definition in result.transform_definitions
        ),
        "instructions_scanned": result.instructions_scanned,
        "stop_reason": result.stop_reason,
        "horizon_covered": result.horizon_covered,
        "physical_timing_status": result.physical_timing_status,
        "requested_timer_tick_horizon": (
            result.requested_timer_tick_horizon
        ),
        "stop_timer_tick": result.stop_timer_tick,
    }


class AuxiliaryEclStateTests(unittest.TestCase):
    def test_active_vm_preserves_timer_bits_locals_and_marker(self) -> None:
        raw = _active_vm(_ROOT, elapsed=7, fraction=0.25, marker=3)
        state = AuxiliaryEclVmState.from_active_vm(raw)
        self.assertEqual(state.instruction_pointer, _ROOT)
        self.assertEqual(state.timer_previous, 6)
        self.assertEqual(state.timer_elapsed, 7)
        self.assertEqual(state.timer_fraction, 0.25)
        self.assertEqual(state.auxiliary_marker, 3)
        self.assertEqual(state.local_projection.integer_value(10007), 107)

    def test_invalid_active_vm_fails_before_lowering(self) -> None:
        with self.assertRaisesRegex(ValueError, "exactly"):
            AuxiliaryEclVmState.from_active_vm(b"\0" * 16)
        with self.assertRaisesRegex(ValueError, "scheduler marker"):
            AuxiliaryEclVmState.from_active_vm(_active_vm(_ROOT, marker=0))
        with self.assertRaisesRegex(ValueError, "timer fraction"):
            AuxiliaryEclVmState.from_active_vm(
                _active_vm(_ROOT, fraction=float("nan"))
            )


class AuxiliaryLiteralFireTests(unittest.TestCase):
    def _lower_single(
        self,
        raw: bytes,
        *,
        elapsed: int = 0,
        horizon: int = 8,
        time_scale: float | None = None,
        max_instructions: int = 64,
    ):
        image, index, offsets = _single_instruction_program(raw)
        vm = _active_vm(_ROOT, elapsed=elapsed)
        result = lower_auxiliary_literal_fire_cycle(
            AuxiliaryEclVmState.from_active_vm(vm),
            instruction_at=index.__getitem__,
            timer_tick_horizon=horizon,
            active_difficulty_mask=_DIFFICULTY,
            time_scale=time_scale,
            max_instructions=max_instructions,
        )
        oracle = oracle_literal_fire_schedule(
            vm,
            image,
            runtime_base=_BASE,
            instruction_offsets=offsets,
            timer_tick_horizon=horizon,
            active_difficulty_mask=_DIFFICULTY,
            time_scale=time_scale,
            max_instructions=max_instructions,
        )
        return result, oracle

    def _lower(
        self,
        *,
        period: int = 8,
        horizon: int = 16,
        fraction: float = 0.0,
        time_scale: float | None = None,
        max_physical_steps: int = 65536,
        transform_parameter_mask: int = 0,
    ):
        image, index, offsets = _synthetic_cycle(
            period=period,
            transform_parameter_mask=transform_parameter_mask,
        )
        vm = _active_vm(_ROOT, fraction=fraction)
        result = lower_auxiliary_literal_fire_cycle(
            AuxiliaryEclVmState.from_active_vm(vm),
            instruction_at=index.__getitem__,
            timer_tick_horizon=horizon,
            active_difficulty_mask=_DIFFICULTY,
            time_scale=time_scale,
            max_physical_steps=max_physical_steps,
        )
        oracle = oracle_literal_fire_schedule(
            vm,
            image,
            runtime_base=_BASE,
            instruction_offsets=offsets,
            timer_tick_horizon=horizon,
            active_difficulty_mask=_DIFFICULTY,
            time_scale=time_scale,
            max_physical_steps=max_physical_steps,
        )
        return result, oracle

    def test_literal_cycle_matches_independent_byte_oracle(self) -> None:
        result, oracle = self._lower()
        self.assertEqual(_core_record(result), oracle)
        self.assertEqual([intent.timer_tick_offset for intent in result.intents], [0, 8, 16])
        self.assertEqual(len(result.transform_definitions), 1)
        self.assertTrue(result.horizon_covered)
        self.assertEqual(result.physical_timing_status, PHYSICAL_TIMING_UNAVAILABLE)
        self.assertTrue(
            all(intent.physical_frame_offset is None for intent in result.intents)
        )
        first = result.intents[0]
        self.assertEqual(first.requested_bullets, 2)
        self.assertIn("vm_parameter:color", first.dependencies)
        self.assertIn("shared_transform_state", first.dependencies)
        self.assertIn("physical_time_scale", first.dependencies)
        self.assertEqual(first.intent_status, "dynamic_parameter")

    def test_native_direct_timer_maps_ticks_to_same_physical_frames(self) -> None:
        result, oracle = self._lower(time_scale=1.0)
        self.assertEqual(_core_record(result), oracle)
        self.assertEqual(result.physical_timing_status, PHYSICAL_TIMING_AVAILABLE)
        self.assertEqual(
            [intent.physical_frame_offset for intent in result.intents],
            [0, 8, 16],
        )
        self.assertNotIn("physical_time_scale", result.intents[0].dependencies)

    def test_fraction_is_preserved_across_jump_for_slow_timer(self) -> None:
        result, oracle = self._lower(
            fraction=0.75,
            time_scale=0.5,
            horizon=8,
        )
        self.assertEqual(_core_record(result), oracle)
        self.assertEqual(
            [intent.physical_frame_offset for intent in result.intents],
            [0, 15],
        )

    def test_physical_budget_exhaustion_does_not_erase_timer_events(self) -> None:
        result, oracle = self._lower(
            time_scale=0.5,
            horizon=8,
            max_physical_steps=1,
        )
        self.assertEqual(_core_record(result), oracle)
        self.assertEqual(
            result.physical_timing_status,
            PHYSICAL_TIMING_BUDGET_EXHAUSTED,
        )
        self.assertEqual([intent.timer_tick_offset for intent in result.intents], [0, 8])
        self.assertEqual(
            [intent.physical_frame_offset for intent in result.intents],
            [0, None],
        )

    def test_nonliteral_transform_stops_before_fire(self) -> None:
        result, oracle = self._lower(transform_parameter_mask=1)
        self.assertEqual(_core_record(result), oracle)
        self.assertEqual(result.stop_reason, "nonliteral_transform")
        self.assertEqual(result.intents, ())
        self.assertFalse(result.horizon_covered)

    def test_nonliteral_jump_and_invalid_instruction_fail_closed(self) -> None:
        nonliteral = _header(
            time=0,
            opcode=0x04,
            payload=struct.pack("<ii", 0, 0),
            parameter_mask=1,
        )
        result, oracle = self._lower_single(nonliteral)
        self.assertEqual(_core_record(result), oracle)
        self.assertEqual(result.stop_reason, "nonliteral_jump")

        malformed = struct.pack("<iHHBBH", 0, 0x63, 11, 0, 0xFF, 0)
        result, oracle = self._lower_single(malformed)
        self.assertEqual(_core_record(result), oracle)
        self.assertEqual(result.stop_reason, "invalid_instruction")

    def test_unsupported_control_and_past_timer_fail_closed(self) -> None:
        for opcode in (0x05, 0x28, 0x34, 0x35):
            with self.subTest(opcode=opcode):
                raw = _header(
                    time=0,
                    opcode=opcode,
                    payload=struct.pack("<iii", 0, 0, 0),
                )
                unsupported, oracle = self._lower_single(raw)
                self.assertEqual(_core_record(unsupported), oracle)
                self.assertEqual(
                    unsupported.stop_reason,
                    f"unsupported_opcode:0x{opcode:02x}",
                )
                self.assertIsNone(unsupported.complete_intents)

        past_instruction = RuntimeEclInstruction(
            _ROOT,
            1,
            0x01,
            12,
            0xFF,
            0,
            b"",
        )
        past = lower_auxiliary_literal_fire_cycle(
            AuxiliaryEclVmState.from_active_vm(
                _active_vm(_ROOT, elapsed=2)
            ),
            instruction_at={_ROOT: past_instruction}.__getitem__,
            timer_tick_horizon=8,
            active_difficulty_mask=_DIFFICULTY,
        )
        self.assertEqual(past.stop_reason, "instruction_time_before_elapsed")

    def test_terminate_is_complete_and_invalid_time_scale_is_not(self) -> None:
        terminate = _header(time=0, opcode=0x01)
        result, oracle = self._lower_single(
            terminate,
            horizon=80,
            time_scale=float("nan"),
        )
        self.assertEqual(_core_record(result), oracle)
        self.assertTrue(result.horizon_covered)
        self.assertEqual(result.stop_reason, "terminate")
        self.assertEqual(
            result.physical_timing_status,
            "time_scale_invalid",
        )

    def test_ineligible_instruction_is_skipped_at_its_timer(self) -> None:
        skipped = _header(time=0, opcode=0x6F, difficulty=0x04)
        terminate = _header(time=0, opcode=0x01)
        image = bytearray(0x400)
        image[0x100 : 0x100 + len(skipped)] = skipped
        image[
            0x100 + len(skipped) : 0x100 + len(skipped) + len(terminate)
        ] = terminate
        second = _ROOT + len(skipped)
        index = {
            _ROOT: RuntimeEclInstruction(
                _ROOT,
                0,
                0x6F,
                len(skipped),
                0x04,
                0,
                b"",
            ),
            second: RuntimeEclInstruction(
                second,
                0,
                0x01,
                len(terminate),
                0xFF,
                0,
                b"",
            ),
        }
        offsets = frozenset((_ROOT - _BASE, second - _BASE))
        vm = _active_vm(_ROOT)
        result = lower_auxiliary_literal_fire_cycle(
            AuxiliaryEclVmState.from_active_vm(vm),
            instruction_at=index.__getitem__,
            timer_tick_horizon=8,
            active_difficulty_mask=_DIFFICULTY,
        )
        oracle = oracle_literal_fire_schedule(
            vm,
            bytes(image),
            runtime_base=_BASE,
            instruction_offsets=offsets,
            timer_tick_horizon=8,
            active_difficulty_mask=_DIFFICULTY,
        )
        self.assertEqual(_core_record(result), oracle)
        self.assertEqual(result.stop_reason, "terminate")
        self.assertEqual(result.transform_definitions, ())

    def test_instruction_limit_remains_unknown(self) -> None:
        image, index, offsets = _synthetic_cycle()
        vm = _active_vm(_ROOT)
        result = lower_auxiliary_literal_fire_cycle(
            AuxiliaryEclVmState.from_active_vm(vm),
            instruction_at=index.__getitem__,
            timer_tick_horizon=80,
            active_difficulty_mask=_DIFFICULTY,
            max_instructions=2,
        )
        oracle = oracle_literal_fire_schedule(
            vm,
            image,
            runtime_base=_BASE,
            instruction_offsets=offsets,
            timer_tick_horizon=80,
            active_difficulty_mask=_DIFFICULTY,
            max_instructions=2,
        )
        self.assertEqual(_core_record(result), oracle)
        self.assertEqual(result.stop_reason, "instruction_limit")
        self.assertFalse(result.horizon_covered)

    def test_zero_tick_literal_loop_is_rejected_as_repeated_state(self) -> None:
        jump = _header(
            time=0,
            opcode=0x04,
            payload=struct.pack("<ii", 0, 0),
        )
        instruction = RuntimeEclInstruction(
            _ROOT,
            0,
            0x04,
            len(jump),
            0xFF,
            0,
            jump[12:],
        )
        result = lower_auxiliary_literal_fire_cycle(
            AuxiliaryEclVmState.from_active_vm(_active_vm(_ROOT)),
            instruction_at={_ROOT: instruction}.__getitem__,
            timer_tick_horizon=8,
            active_difficulty_mask=_DIFFICULTY,
        )
        self.assertEqual(result.stop_reason, "repeated_state")
        self.assertEqual(result.instructions_scanned, 1)

    def test_batch_canonicalizes_only_intent_equivalent_requests(self) -> None:
        _, index, _ = _synthetic_cycle()
        first_raw = bytearray(_active_vm(_ROOT))
        second_raw = bytearray(first_raw)
        struct.pack_into("<i", second_raw, 0x18, 91)
        third_raw = _active_vm(_ROOT, elapsed=1)
        requests = tuple(
            AuxiliaryLiteralFireRequest(
                state=AuxiliaryEclVmState.from_active_vm(raw),
                timer_tick_horizon=16,
            )
            for raw in (bytes(first_raw), bytes(second_raw), third_raw)
        )
        batch = lower_auxiliary_literal_fire_batch(
            requests,
            instruction_at=index.__getitem__,
            active_difficulty_mask=_DIFFICULTY,
            time_scale=1.0,
        )
        self.assertEqual(batch.result_indices, (0, 0, 1))
        self.assertEqual(len(batch.unique_results), 2)
        self.assertIs(batch.results[0], batch.results[1])
        self.assertEqual(batch.results[2].stop_reason, "instruction_time_before_elapsed")
        record = batch.compact_record()
        self.assertEqual(record["request_count"], 3)
        self.assertEqual(record["unique_result_count"], 2)


class ShippedAuxiliaryLiteralFireTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.path = (
            Path(__file__).resolve().parents[1]
            / "artifacts"
            / "decoded"
            / "ecldata5.ecl"
        )
        cls.image = cls.path.read_bytes()
        cls.ecl = parse_ecl(cls.path)
        cls.index = build_exact_runtime_instruction_index(
            cls.ecl,
            cls.image,
            runtime_base=_BASE,
            expected_sha256=hashlib.sha256(cls.image).hexdigest(),
        )
        cls.offsets = frozenset(
            address - _BASE for address in cls.index
        )

    def test_exact_stage5_targets_match_oracle_and_declared_periods(self) -> None:
        for subroutine_index, period in ((69, 8), (72, 8), (73, 30)):
            with self.subTest(subroutine=subroutine_index):
                first = self.ecl.subroutines[subroutine_index].instructions[0]
                vm = _active_vm(_BASE + first.offset)
                result = lower_auxiliary_literal_fire_cycle(
                    AuxiliaryEclVmState.from_active_vm(vm),
                    instruction_at=self.index.__getitem__,
                    timer_tick_horizon=period * 2,
                    active_difficulty_mask=_DIFFICULTY,
                    time_scale=1.0,
                )
                oracle = oracle_literal_fire_schedule(
                    vm,
                    self.image,
                    runtime_base=_BASE,
                    instruction_offsets=self.offsets,
                    timer_tick_horizon=period * 2,
                    active_difficulty_mask=_DIFFICULTY,
                    time_scale=1.0,
                )
                self.assertEqual(_core_record(result), oracle)
                self.assertEqual(
                    [intent.timer_tick_offset for intent in result.intents],
                    [0, period, period * 2],
                )
                self.assertEqual(
                    [intent.opcode for intent in result.intents],
                    [0x63, 0x63, 0x63],
                )
                self.assertEqual(
                    [intent.requested_bullets for intent in result.intents],
                    [2, 2, 2],
                )

    def test_exact_index_rejects_identity_and_byte_mutation(self) -> None:
        with self.assertRaisesRegex(ValueError, "digest"):
            build_exact_runtime_instruction_index(
                self.ecl,
                self.image,
                runtime_base=_BASE,
                expected_sha256="0" * 64,
            )
        mutated = bytearray(self.image)
        mutated[self.ecl.subroutines[69].instructions[0].offset] ^= 1
        with self.assertRaisesRegex(ValueError, "identity"):
            build_exact_runtime_instruction_index(
                self.ecl,
                bytes(mutated),
                runtime_base=_BASE,
            )


if __name__ == "__main__":
    unittest.main()
