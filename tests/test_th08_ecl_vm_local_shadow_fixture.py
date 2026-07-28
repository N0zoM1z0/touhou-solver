#!/usr/bin/env python3
"""Verify every retained physical opcode-0x05 case with both implementations."""

from __future__ import annotations

import hashlib
import json
import struct
import unittest
from pathlib import Path

from th08_ecl_vm_local_oracle import oracle_interpret, raw_instruction
from th08_ecl_runtime import EclVmSnapshot, RuntimeEclInstruction
from th08_ecl_shadow import interpret_vm_local_shadow
from th08_ecl_vm_state import EclVmLocalProjection


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = (
    ROOT
    / "artifacts/ecl_reports/stage4a_vm_local_op05_cases_20260728_110438.json"
)


class EclVmLocalShadowFixtureTests(unittest.TestCase):
    def test_all_unique_physical_op05_cases_match_independent_oracle(
        self,
    ) -> None:
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(
            fixture["schema"],
            "th08-ecl-vm-local-op05-cases-v1",
        )
        source = fixture["source"]
        runtime_base = int(source["runtime_base"])
        ecl = ROOT / "artifacts/decoded/ecldata4asp.ecl"
        self.assertEqual(
            hashlib.sha256(ecl.read_bytes()).hexdigest(),
            source["ecl_sha256"],
        )
        self.assertEqual(len(fixture["cases"]), 108)

        for case in fixture["cases"]:
            with self.subTest(
                offset=case["instruction_offset"],
                counter=case["counter_before"],
                timer_elapsed=case["timer_elapsed"],
                timer_fraction=case["timer_fraction"],
            ):
                address = runtime_base + int(case["instruction_offset"])
                arguments = tuple(int(value) for value in case["arguments"])
                payload = struct.pack("<3i", *arguments)
                instruction = RuntimeEclInstruction(
                    address=address,
                    time=int(case["instruction_time"]),
                    opcode=0x05,
                    size=int(case["instruction_size"]),
                    difficulty_mask=int(case["difficulty_mask"]),
                    parameter_mask=int(case["parameter_mask"]),
                    payload=payload,
                )
                projection = EclVmLocalProjection(
                    (16, 1, 2, 3, 4, 5, 6, 7),
                    (0, 0, 2, 3, 4, 5, 6, 7),
                    (int(case["counter_before"]), 8, 7, 6),
                )
                snapshot = EclVmSnapshot(
                    address,
                    float(case["timer_fraction"]),
                    int(case["timer_elapsed"]),
                    16,
                    0.0,
                    0.0,
                    float(case["time_scale"]),
                    projection,
                )

                result = interpret_vm_local_shadow(
                    snapshot,
                    instruction_at=lambda _address: instruction,
                    horizon_frames=256,
                    active_difficulty_mask=0x08,
                    max_instructions=1,
                )
                oracle = oracle_interpret(
                    {address: raw_instruction(instruction)},
                    start=address,
                    counter=int(case["counter_before"]),
                    timer_fraction=float(case["timer_fraction"]),
                    timer_elapsed=int(case["timer_elapsed"]),
                    time_scale=float(case["time_scale"]),
                    horizon_frames=256,
                    max_instructions=1,
                )

                assert result.final_projection is not None
                self.assertEqual(
                    result.final_instruction_pointer - runtime_base,
                    case["expected_pc_offset"],
                )
                self.assertEqual(
                    result.final_projection.integer_value(
                        int(case["variable"])
                    ),
                    case["counter_after"],
                )
                self.assertEqual(
                    result.final_timer_value,
                    case["expected_timer"],
                )
                self.assertEqual(
                    result.stop_frame,
                    case["expected_stop_frame"],
                )
                self.assertEqual(
                    result.final_instruction_pointer,
                    oracle["pc"],
                )
                self.assertEqual(
                    result.final_timer_value,
                    oracle["timer"],
                )
                self.assertEqual(
                    result.stop_frame,
                    oracle["physical_frame"],
                )
                self.assertEqual(
                    result.final_projection.scratch_integers[0],
                    oracle["variables"][10036],
                )


if __name__ == "__main__":
    unittest.main()
