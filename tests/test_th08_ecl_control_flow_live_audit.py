#!/usr/bin/env python3
"""Tests for live ECL fail-closed metadata auditing."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from analysis.th08_ecl_control_flow_live_audit import audit_live_trace


def _decision(
    frame: int,
    spell_id: int,
    *,
    phase_end: bool = False,
) -> dict[str, object]:
    return {
        "kind": "decision",
        "frame": frame,
        "spell": {
            "active": True,
            "spell_id": spell_id,
            "flags": 0x801 if phase_end else 1,
        },
        "bullet_velocity_lookahead": {
            "instruction_pointer": 0x500000,
            "timer_fraction": 0.0,
            "timer_elapsed": 0,
            "time_scale": 1.0,
            "tag_mask": 16,
            "instructions_scanned": 3,
            "stop_reason": "unsupported_control_flow",
            "horizon_covered": False,
            "coverage_status": "unknown",
            "requested_horizon_frames": 256,
            "covered_through_frame": 0,
            "unknown_from_frame": 1,
            "result_kind": "prefix_only",
            "prefix_events": [],
            "events": [],
            "lowering_status": "incomplete_prefix_not_lowered",
            "error": None,
        },
        "timing_ms": {
            "read_ecl_lookahead": 0.01,
        },
    }


class EclControlFlowLiveAuditTests(unittest.TestCase):
    def test_complete_fail_closed_runtime_scope_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            trace_path = Path(temporary) / "trace.jsonl"
            rows = [
                _decision(index, spell_id, phase_end=spell_id == 73)
                for index, spell_id in enumerate((57, 61, 65, 73), 1)
            ]
            timer_reset = _decision(5, 61)
            timer_reset["bullet_velocity_lookahead"][
                "stop_reason"
            ] = "unsupported_timer_reset"
            rows.append(timer_reset)
            trace_path.write_text(
                "".join(json.dumps(row) + "\n" for row in rows),
                encoding="utf-8",
            )
            report = audit_live_trace(trace_path)
        self.assertTrue(report["passed"])
        self.assertEqual(
            report["counts"]["stop_reason_rows"],
            {
                "unsupported_control_flow": 4,
                "unsupported_timer_reset": 1,
            },
        )
        self.assertEqual(report["counts"]["phase_end_rows"], 1)
        self.assertEqual(report["counts"]["phase_end_valid_rows"], 1)

    def test_malformed_unknown_boundary_is_reported_not_raised(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            trace_path = Path(temporary) / "trace.jsonl"
            row = _decision(1, 57)
            row["bullet_velocity_lookahead"]["covered_through_frame"] = None
            trace_path.write_text(
                json.dumps(row) + "\n",
                encoding="utf-8",
            )
            report = audit_live_trace(trace_path)
        self.assertFalse(report["passed"])
        self.assertEqual(report["counts"]["metadata_error_count"], 1)
        self.assertEqual(
            report["violations"]["metadata_error_samples"][0]["errors"],
            ["inconsistent_unknown_metadata"],
        )


if __name__ == "__main__":
    unittest.main()
