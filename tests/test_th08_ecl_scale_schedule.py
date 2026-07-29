#!/usr/bin/env python3
"""Independent-oracle tests for causal TH08 ECL scale schedules."""

from __future__ import annotations

import struct
import unittest
from pathlib import Path

from analysis.th08_ecl_scale_schedule_raw_oracle import (
    oracle_ecl_scale_schedule_raw,
)
from analysis.th08_scale_transition_raw_oracle import (
    oracle_reciprocal_int32_bits,
)
from th08_ecl_runtime import (
    EclInstructionCache,
    EclVmSnapshot,
)
from th08_ecl_scale_schedule import (
    ECL_INT_SPELL_FINISH_RESULT,
    ECL_OP_FINISH_SPELL_CARD,
    ECL_OP_INSTALL_CALLBACK,
    EclScaleEnvironment,
    EclScaleSourceAuthority,
    synthesize_ecl_time_scale_schedule,
)
from th08_ecl_vm_state import EclVmLocalProjection
from th08_time_scale import (
    SCALE_COVERAGE_COMPLETE,
    SCALE_COVERAGE_ROOT_ONLY,
    reciprocal_int32_time_scale_bits,
)


ROOT = Path(__file__).resolve().parents[1]
QUARTER_BITS = 0x3E800000
UNIT_BITS = 0x3F800000


def _instruction(
    time: int,
    opcode: int,
    *arguments: int,
    parameter_mask: int = 0,
    difficulty_mask: int = 0xFF,
) -> bytes:
    size = 12 + 4 * len(arguments)
    return struct.pack(
        "<iHHBBH",
        time,
        opcode,
        size,
        0,
        difficulty_mask,
        parameter_mask,
    ) + struct.pack(f"<{len(arguments)}i", *arguments)


class _MappedBytes:
    def __init__(self, code: bytes, *, base: int) -> None:
        self.code = code
        self.base = base

    def read(self, address: int, size: int) -> bytes:
        start = address - self.base
        end = start + size
        if size <= 0 or start < 0 or end > len(self.code):
            raise OSError(f"unmapped ECL read at {address:#x}")
        return self.code[start:end]

    def instruction_bytes(self, address: int) -> bytes:
        header = self.read(address, 12)
        size = struct.unpack_from("<H", header, 6)[0]
        return self.read(address, size)


def _projection(counter: int = 0) -> EclVmLocalProjection:
    return EclVmLocalProjection(
        (0, 1, 2, 3, 4, 5, 6, 7),
        (0, 0, 2, 3, 4, 5, 6, 7),
        (counter, 8, 7, 6),
    )


def _snapshot(
    pc: int,
    *,
    scale: float,
    timer_elapsed: int = 0,
    timer_fraction: float = 0.0,
    counter: int = 0,
) -> EclVmSnapshot:
    return EclVmSnapshot(
        pc,
        timer_fraction,
        timer_elapsed,
        0,
        0.0,
        0.0,
        scale,
        _projection(counter),
    )


def _authority(
    source_id: int,
    *,
    complete: bool = True,
    no_hit_no_bomb: bool = True,
) -> EclScaleSourceAuthority:
    return EclScaleSourceAuthority(
        scale_writer_source_ids=(source_id,),
        writer_inventory_complete=complete,
        scheduler_order_complete=complete,
        installed_scale_callbacks_absent=complete,
        unmodeled_phase_transitions_absent=complete,
        post_update_capture=complete,
        external_state_coherent=complete,
        no_hit_no_bomb_continuation=no_hit_no_bomb,
        provenance="test_complete_writer_inventory",
    )


def _environment(flags: int = 0x825) -> EclScaleEnvironment:
    return EclScaleEnvironment(
        difficulty_index=3,
        route_id=2,
        spell_flags=flags,
    )


def _product(
    mapped: _MappedBytes,
    snapshot: EclVmSnapshot,
    *,
    horizon: int,
    source_id: int = 0x580000,
    authority: EclScaleSourceAuthority | None = None,
    environment: EclScaleEnvironment | None = None,
):
    cache = EclInstructionCache()
    return synthesize_ecl_time_scale_schedule(
        snapshot,
        source_id=source_id,
        source_frame=100,
        authority=authority or _authority(source_id),
        environment=environment or _environment(),
        instruction_at=lambda address: cache.instruction(
            mapped.read,
            address,
        ),
        horizon_frames=horizon,
        active_difficulty_mask=0x08,
    )


def _oracle(
    mapped: _MappedBytes,
    snapshot: EclVmSnapshot,
    *,
    horizon: int,
    environment: EclScaleEnvironment | None = None,
    no_hit_no_bomb: bool = True,
) -> dict[str, object]:
    observed = environment or _environment()
    projection = snapshot.local_projection
    assert projection is not None
    integers = {
        **{
            10000 + index: value
            for index, value in enumerate(projection.integer_locals)
        },
        **{
            10036 + index: value
            for index, value in enumerate(projection.scratch_integers)
        },
    }
    return oracle_ecl_scale_schedule_raw(
        instruction_bytes_at=mapped.instruction_bytes,
        start_pc=snapshot.instruction_pointer,
        timer_elapsed=snapshot.timer_elapsed,
        timer_fraction_bits=snapshot.timer_fraction_bits,
        root_scale_bits=snapshot.time_scale_bits,
        integer_values=integers,
        difficulty_index=observed.difficulty_index,
        route_id=observed.route_id,
        spell_flags=observed.spell_flags,
        spell_timer_elapsed_by_frame=(
            observed.spell_timer_elapsed_by_frame
        ),
        horizon_frames=horizon,
        active_difficulty_mask=0x08,
        no_hit_no_bomb_continuation=no_hit_no_bomb,
    )


def _write_rows(result) -> tuple[tuple[object, ...], ...]:
    return tuple(
        (
            write.frame,
            write.callback_index,
            write.scale_bits_before,
            write.scale_bits_after,
            write.instruction_address,
            write.scales_active_bullet_velocity,
        )
        for write in result.writes
    )


class EclScaleScheduleTests(unittest.TestCase):
    def assert_oracle_parity(
        self,
        product,
        oracle: dict[str, object],
    ) -> None:
        self.assertEqual(
            product.schedule.player_scale_bits,
            oracle["player_scale_bits"],
        )
        self.assertEqual(
            product.schedule.laser_scale_bits,
            oracle["laser_scale_bits"],
        )
        self.assertEqual(_write_rows(product), oracle["writes"])
        self.assertEqual(product.instructions_scanned, oracle["instructions_scanned"])
        self.assertEqual(product.stop_reason, oracle["stop_reason"])
        self.assertEqual(product.horizon_covered, oracle["horizon_covered"])
        self.assertEqual(product.stop_frame, oracle["stop_frame"])
        self.assertEqual(
            product.consumed_external_variables,
            oracle["consumed_external_variables"],
        )
        self.assertEqual(product.final_instruction_pointer, oracle["pc"])
        self.assertEqual(product.final_timer_elapsed, oracle["timer_elapsed"])
        self.assertEqual(
            product.final_timer_fraction_bits,
            oracle["timer_fraction_bits"],
        )

    def test_same_update_callback_separates_player_and_laser_scale(self) -> None:
        base = 0x500000
        code = b"".join(
            (
                _instruction(0, 0x88, 18, 4),
                _instruction(10, 0x01),
            )
        )
        mapped = _MappedBytes(code, base=base)
        snapshot = _snapshot(base, scale=1.0)

        product = _product(mapped, snapshot, horizon=2)
        oracle = _oracle(mapped, snapshot, horizon=2)

        self.assertEqual(
            product.schedule.player_scale_bits,
            (UNIT_BITS, QUARTER_BITS),
        )
        self.assertEqual(
            product.schedule.laser_scale_bits,
            (QUARTER_BITS, QUARTER_BITS),
        )
        self.assertEqual(product.writes[0].frame, 1)
        self.assert_oracle_parity(product, oracle)

    def test_incomplete_source_inventory_retains_root_only(self) -> None:
        base = 0x510000
        mapped = _MappedBytes(_instruction(0, 0x88, 18, 4), base=base)
        source_id = 0x580000

        result = _product(
            mapped,
            _snapshot(base, scale=1.0),
            horizon=8,
            source_id=source_id,
            authority=_authority(source_id, complete=False),
        )

        self.assertEqual(result.schedule.coverage, SCALE_COVERAGE_ROOT_ONLY)
        self.assertEqual(result.schedule.player_scale_bits, (UNIT_BITS,))
        self.assertEqual(result.schedule.laser_scale_bits, ())
        self.assertIn("writer_inventory_complete", result.stop_reason)

    def test_future_callback_install_truncates_before_laser_phase(self) -> None:
        base = 0x520000
        mapped = _MappedBytes(
            _instruction(0, ECL_OP_INSTALL_CALLBACK, 18, 4),
            base=base,
        )

        result = _product(
            mapped,
            _snapshot(base, scale=1.0),
            horizon=4,
        )

        self.assertEqual(result.stop_reason, "unsupported_callback_install")
        self.assertEqual(result.schedule.coverage, SCALE_COVERAGE_ROOT_ONLY)

    def test_finish_spell_branch_uses_no_hit_no_bomb_continuation(self) -> None:
        base = 0x530000
        finish = _instruction(0, ECL_OP_FINISH_SPELL_CARD)
        branch_address = base + len(finish)
        branch = _instruction(
            0,
            0x2A,
            ECL_INT_SPELL_FINISH_RESULT,
            0,
            70,
            28,
            parameter_mask=0x01,
        )
        restore_address = branch_address + 28
        restore = _instruction(70, 0x88, 18, 1)
        terminate = _instruction(70, 0x01)
        mapped = _MappedBytes(
            finish + branch + restore + terminate,
            base=base,
        )
        snapshot = _snapshot(base, scale=0.25)

        product = _product(mapped, snapshot, horizon=2)
        oracle = _oracle(mapped, snapshot, horizon=2)

        self.assertEqual(restore_address, product.writes[0].instruction_address)
        self.assertEqual(product.schedule.player_scale_bits[0], QUARTER_BITS)
        self.assertEqual(product.schedule.laser_scale_bits[0], UNIT_BITS)
        self.assertIn(
            ECL_INT_SPELL_FINISH_RESULT,
            product.consumed_external_variables,
        )
        self.assert_oracle_parity(product, oracle)

        denied = _product(
            mapped,
            snapshot,
            horizon=2,
            authority=_authority(0x580000, no_hit_no_bomb=False),
        )
        self.assertEqual(
            denied.stop_reason,
            "missing_no_hit_no_bomb_continuation",
        )
        self.assertEqual(denied.schedule.coverage, SCALE_COVERAGE_ROOT_ONLY)

    def test_product_reciprocals_match_exact_rational_oracle(self) -> None:
        for divisor in range(1, 8193):
            with self.subTest(divisor=divisor):
                self.assertEqual(
                    reciprocal_int32_time_scale_bits(divisor),
                    oracle_reciprocal_int32_bits(divisor),
                )

    def test_static_final_b_and_extra_restore_schedules_match_oracle(self) -> None:
        workloads = (
            ("ecldata7.ecl", 0x5C58, 0x6018, 241),
            ("ecldata8.ecl", 0x87E8, 0x8B58, 241),
        )
        for filename, start_offset, restore_offset, horizon in workloads:
            with self.subTest(workload=filename):
                base = 0x600000
                mapped = _MappedBytes(
                    (ROOT / "artifacts" / "decoded" / filename).read_bytes(),
                    base=base,
                )
                snapshot = _snapshot(
                    base + start_offset,
                    scale=0.25,
                    counter=0,
                )

                product = _product(mapped, snapshot, horizon=horizon)
                oracle = _oracle(mapped, snapshot, horizon=horizon)

                self.assertEqual(product.schedule.coverage, SCALE_COVERAGE_COMPLETE)
                self.assertEqual(len(product.writes), 1)
                self.assertEqual(
                    product.writes[0].instruction_address,
                    base + restore_offset,
                )
                self.assertEqual(product.writes[0].callback_index, 18)
                self.assertEqual(product.writes[0].scale_bits_after, UNIT_BITS)
                self.assertEqual(product.bullet_velocity_rescale_frames, ())
                self.assert_oracle_parity(product, oracle)


if __name__ == "__main__":
    unittest.main()
