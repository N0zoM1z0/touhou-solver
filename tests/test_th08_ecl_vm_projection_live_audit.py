#!/usr/bin/env python3
"""Tests for capture-aligned ECL VM-local live-trace auditing."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from analysis.th08_ecl_vm_projection_live_audit import (
    audit_vm_projection_trace,
)
from th08_ecl_vm_state import EclVmLocalProjection


def _decision(
    frame: int,
    spell_id: int,
    *,
    complete: bool,
) -> dict[str, object]:
    projection = EclVmLocalProjection(
        (16, 1, 2, 3, 4, 5, 6, 7),
        tuple(range(8)),
        (spell_id, 8, 7, 6),
    )
    return {
        "kind": "decision",
        "frame": frame,
        "spell": {"active": True, "spell_id": spell_id, "flags": 1},
        "bullet_velocity_lookahead": {
            "instruction_pointer": 0x500000,
            "timer_fraction": 0.0,
            "timer_elapsed": 0,
            "time_scale": 1.0,
            "tag_mask": 16,
            "vm_local_projection": projection.trace_record(),
            "instructions_scanned": 3,
            "stop_reason": (
                "horizon" if complete else "unsupported_control_flow"
            ),
            "horizon_covered": complete,
            "coverage_status": "complete" if complete else "unknown",
            "requested_horizon_frames": 256,
            "covered_through_frame": 256 if complete else 0,
            "unknown_from_frame": None if complete else 1,
            "result_kind": (
                "complete_schedule" if complete else "prefix_only"
            ),
            "prefix_events": [],
            "events": [],
            "lowering_status": (
                "complete_schedule_lowered"
                if complete
                else "incomplete_prefix_not_lowered"
            ),
        },
        "timing_ms": {"read_ecl_lookahead": frame / 1000.0},
    }


class EclVmProjectionLiveAuditTests(unittest.TestCase):
    def test_valid_stage4_projection_scope_passes(self) -> None:
        rows = [
            _decision(1, 57, complete=False),
            _decision(2, 61, complete=False),
            _decision(3, 65, complete=False),
            _decision(4, 69, complete=True),
            _decision(5, 73, complete=False),
        ]
        with tempfile.TemporaryDirectory() as temporary:
            trace = Path(temporary) / "trace.jsonl"
            trace.write_text(
                "".join(json.dumps(row) + "\n" for row in rows),
                encoding="utf-8",
            )
            report = audit_vm_projection_trace(trace)

        self.assertTrue(report["passed"])
        self.assertEqual(report["counts"]["projection_rows"], 5)
        self.assertEqual(
            report["counter_10036_by_spell"]["57"]["median"],
            57,
        )
        self.assertEqual(
            report["read_ecl_lookahead_ms_by_spell"]["69"]["p99_9"],
            0.004,
        )

    def test_missing_projection_and_tag_mismatch_fail_closed(self) -> None:
        missing = _decision(1, 57, complete=False)
        missing["bullet_velocity_lookahead"]["vm_local_projection"] = None
        mismatch = _decision(2, 61, complete=False)
        mismatch["bullet_velocity_lookahead"]["tag_mask"] = 17
        with tempfile.TemporaryDirectory() as temporary:
            trace = Path(temporary) / "trace.jsonl"
            trace.write_text(
                json.dumps(missing) + "\n" + json.dumps(mismatch) + "\n",
                encoding="utf-8",
            )
            report = audit_vm_projection_trace(trace)

        self.assertFalse(report["passed"])
        self.assertEqual(
            report["counts"]["projection_errors"],
            {"missing_projection": 1, "tag_mask_mismatch": 1},
        )
        self.assertEqual(len(report["violations"]), 2)


if __name__ == "__main__":
    unittest.main()
