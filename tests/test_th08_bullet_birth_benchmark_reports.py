from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTS = {
    "bullet_birth_observer_linux_20260728.json": (
        "b77ed72fd9e779f4b903d9caeaae7af1436e235885df4c9df96993f1dc4c2e18"
    ),
    "bullet_birth_observer_windows_20260728.json": (
        "4bb018a6c84839d93bbcb3b0da21cc50cacbff259208ce91d248eee9a428d56c"
    ),
}


class RetainedBulletBirthBenchmarkReportTests(unittest.TestCase):
    def test_retained_reports_pass_the_fixed_observation_gate(self) -> None:
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
                    "th08-bullet-birth-observer-benchmark-v1",
                )
                self.assertEqual(report["pool_size"], 1536)
                self.assertEqual(report["iterations"], 5000)
                self.assertEqual(report["decode_iterations"], 300)
                self.assertTrue(report["gate"]["passed"])
                self.assertTrue(report["gate"]["observer_pass"])
                self.assertTrue(report["gate"]["interleaved_pass"])
                full = next(
                    row
                    for row in report["density_results"]
                    if row["density"] == 1536
                )["observer"]
                self.assertLessEqual(
                    full["p95_ms"],
                    report["gate"]["p95_limit_ms"],
                )
                self.assertLessEqual(
                    full["p99_ms"],
                    report["gate"]["p99_limit_ms"],
                )
                self.assertLessEqual(
                    full["max_ms"],
                    report["gate"]["max_limit_ms"],
                )
                self.assertLessEqual(
                    report["interleaved_p95_ratio"],
                    report["gate"]["interleaved_p95_ratio_limit"],
                )


if __name__ == "__main__":
    unittest.main()
