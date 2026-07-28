#!/usr/bin/env python3
"""Tests for deterministic ECL control-flow coverage replay."""

from __future__ import annotations

import json
import struct
import tempfile
import unittest
from pathlib import Path

from analysis.th08_ecl_control_flow_audit import audit_trace


def _instruction(time: int, opcode: int, *arguments: int) -> bytes:
    return struct.pack(
        "<iHHBBH",
        time,
        opcode,
        12 + 4 * len(arguments),
        0,
        0xFF,
        0,
    ) + struct.pack(f"<{len(arguments)}i", *arguments)


def _decision(frame: int, pc: int, spell_id: int) -> dict[str, object]:
    return {
        "kind": "decision",
        "frame": frame,
        "spell": {
            "active": True,
            "spell_id": spell_id,
        },
        "bullet_velocity_lookahead": {
            "instruction_pointer": pc,
            "timer_fraction": 0.0,
            "timer_elapsed": 0,
            "time_scale": 1.0,
            "tag_mask": 16,
            "instructions_scanned": 256,
            "stop_reason": "instruction_limit",
            "horizon_covered": False,
            "coverage_status": "unknown",
            "error": None,
        },
    }


class EclControlFlowAuditTests(unittest.TestCase):
    def test_unknown_control_replay_never_promotes_complete(self) -> None:
        base = 0x500000
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            ecl_path = root / "fixture.ecl"
            trace_path = root / "trace.jsonl"
            ecl_path.write_bytes(
                _instruction(0, 0x05, 0, 0, 10000)
            )
            rows = (
                _decision(1, base, 57),
                _decision(2, base, 73),
            )
            trace_path.write_text(
                "".join(json.dumps(row) + "\n" for row in rows),
                encoding="utf-8",
            )
            report = audit_trace(
                trace_path,
                ecl_path=ecl_path,
                runtime_base=base,
            )
        self.assertTrue(report["passed"])
        self.assertEqual(
            report["counts"]["new_stop_counts"],
            {"unsupported_control_flow": 2},
        )
        self.assertEqual(
            report["violations"]["unknown_to_complete"],
            [],
        )
        self.assertEqual(
            report["per_spell"]["57"]["new_max_instructions"],
            1,
        )

    def test_mapping_failure_invalidates_later_plausible_bytes(self) -> None:
        base = 0x500000
        invalid_header = struct.pack(
            "<iHHBBH",
            0,
            0,
            0,
            0,
            0xFF,
            0,
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            ecl_path = root / "fixture.ecl"
            trace_path = root / "trace.jsonl"
            ecl_path.write_bytes(
                invalid_header
                + _instruction(300, 0x00)
            )
            rows = (
                _decision(1, base, 73),
                _decision(2, base + len(invalid_header), 73),
            )
            trace_path.write_text(
                "".join(json.dumps(row) + "\n" for row in rows),
                encoding="utf-8",
            )
            report = audit_trace(
                trace_path,
                ecl_path=ecl_path,
                runtime_base=base,
            )

        self.assertFalse(report["passed"])
        self.assertEqual(report["counts"]["replayed_rows"], 0)
        self.assertEqual(report["mapping_exclusions"]["count"], 2)
        self.assertEqual(
            report["mapping_exclusions"]["invalidation"]["frame"],
            1,
        )
        self.assertIn(
            "invalidated by earlier runtime-image mismatch",
            report["mapping_exclusions"]["samples"][1]["error"],
        )
        self.assertEqual(
            report["violations"]["unknown_to_complete"],
            [],
        )


if __name__ == "__main__":
    unittest.main()
