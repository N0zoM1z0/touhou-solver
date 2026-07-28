from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTS = {
    "derived_pattern_source_observer_native_linux_20260728.json": (
        "cfe8a114abfb51dfdba00821ac99581d7be8270cedfd5802223273009cbdd80e"
    ),
    "derived_pattern_source_observer_native_windows_20260728.json": (
        "785f089180f15bdb3e6eb48c618aa59c0f662da40aa91c396c588f4da72c5e01"
    ),
}


class RetainedDerivedPatternSourceBenchmarkReportTests(
    unittest.TestCase
):
    def test_reports_pass_fixed_observer_gate(self) -> None:
        for name, expected_sha256 in REPORTS.items():
            with self.subTest(report=name):
                path = ROOT / "artifacts" / "benchmarks" / name
                raw = path.read_bytes()
                self.assertEqual(
                    hashlib.sha256(raw).hexdigest(),
                    expected_sha256,
                )
                report = json.loads(raw)
                self.assertEqual(
                    report["schema"],
                    "th08-derived-pattern-source-benchmark-v1",
                )
                self.assertEqual(report["workload"]["active_count"], 422)
                self.assertEqual(report["workload"]["source_count"], 5)
                self.assertEqual(report["workload"]["iterations"], 10_000)
                self.assertTrue(report["parity"]["passed"])
                self.assertTrue(report["gate"]["passed"])
                self.assertTrue(report["passed"])
                timing = report["timing_ms"]["observe_total"]
                self.assertLessEqual(
                    timing["p95"],
                    report["gate"]["p95_limit_ms"],
                )
                self.assertLessEqual(
                    timing["p99"],
                    report["gate"]["p99_limit_ms"],
                )
                self.assertLessEqual(
                    timing["max"],
                    report["gate"]["max_limit_ms"],
                )


if __name__ == "__main__":
    unittest.main()
