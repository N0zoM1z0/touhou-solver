#!/usr/bin/env python3
"""Tests for retained-trace ECL VM-local shadow replay."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from analysis.th08_ecl_vm_local_shadow_replay import (
    audit_vm_local_shadow_replay,
)
from th08_ecl_vm_state import EclVmLocalProjection


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_BASE = 0x0B1C1430


def _row(counter: int) -> dict[str, object]:
    projection = EclVmLocalProjection(
        (16, 1, 2, 3, 4, 5, 6, 7),
        tuple(range(8)),
        (counter, 8, 7, 6),
    )
    return {
        "kind": "decision",
        "frame": counter,
        "spell": {"active": True, "spell_id": 57, "flags": 1},
        "bullet_velocity_lookahead": {
            "instruction_pointer": RUNTIME_BASE + 0x3510,
            "timer_fraction": 0.0,
            "timer_elapsed": 191,
            "time_scale": 1.0,
            "tag_mask": 16,
            "vm_local_projection": projection.trace_record(),
            "coverage_status": "unknown",
            "requested_horizon_frames": 256,
        },
    }


class EclVmLocalShadowReplayTests(unittest.TestCase):
    def test_shipped_op05_rows_produce_exact_cases_without_completion(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            trace = Path(temporary) / "trace.jsonl"
            trace.write_text(
                json.dumps(_row(1)) + "\n" + json.dumps(_row(2)) + "\n",
                encoding="utf-8",
            )
            report, cases = audit_vm_local_shadow_replay(
                trace_path=trace,
                ecl_path=ROOT / "artifacts/decoded/ecldata4asp.ecl",
                runtime_base=RUNTIME_BASE,
            )

        self.assertTrue(report["passed"])
        self.assertEqual(report["counts"]["initial_op05_rows"], 2)
        self.assertEqual(report["counts"]["unique_op05_cases"], 2)
        self.assertEqual(
            report["counts"]["unverified_new_complete_rows"],
            0,
        )
        self.assertEqual(cases["cases"][0]["counter_before"], 1)
        self.assertEqual(cases["cases"][1]["counter_before"], 2)

    def test_missing_projection_fails_the_decode_gate(self) -> None:
        row = _row(2)
        row["bullet_velocity_lookahead"]["vm_local_projection"] = None
        with tempfile.TemporaryDirectory() as temporary:
            trace = Path(temporary) / "trace.jsonl"
            trace.write_text(json.dumps(row) + "\n", encoding="utf-8")
            report, _cases = audit_vm_local_shadow_replay(
                trace_path=trace,
                ecl_path=ROOT / "artifacts/decoded/ecldata4asp.ecl",
                runtime_base=RUNTIME_BASE,
            )

        self.assertFalse(report["passed"])
        self.assertEqual(report["counts"]["decode_errors"], 1)


if __name__ == "__main__":
    unittest.main()
