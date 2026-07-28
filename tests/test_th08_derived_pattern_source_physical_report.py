from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = (
    ROOT
    / "artifacts"
    / "viability_audit"
    / "g5_derived_source_stage5_20260728_150827.json"
)
REPORT_SHA256 = (
    "a08f137081e51b70994125f7c4a2d165541d936e61a924bde8d58a4f6f0c9bda"
)


class RetainedDerivedPatternSourcePhysicalReportTests(unittest.TestCase):
    def test_negative_source_and_combined_timing_gate_are_retained(
        self,
    ) -> None:
        raw = REPORT.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), REPORT_SHA256)
        report = json.loads(raw)
        self.assertTrue(report["gates"]["validation_passed"])
        self.assertFalse(report["gates"]["observer_budget_passed"])
        self.assertFalse(report["passed"])
        source = report["derived_pattern_source"]
        self.assertEqual(source["schema_v10_rows"], 11_801)
        self.assertEqual(source["candidate_rows"], 0)
        self.assertEqual(source["candidate_sightings"], 0)
        join = report["derived_pattern_source_join"]
        self.assertEqual(join["source_sightings"], 0)
        self.assertFalse(join["semantics"]["hit_outcome_used"])
        self.assertEqual(
            join["complete_edge_digest"],
            "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
        )


if __name__ == "__main__":
    unittest.main()
