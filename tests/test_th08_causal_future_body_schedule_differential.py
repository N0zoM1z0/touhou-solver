from __future__ import annotations

import json
import unittest
from pathlib import Path

from analysis.th08_causal_future_body_schedule_differential import (
    build_report,
)


ROOT = Path(__file__).resolve().parents[1]
REPORT = (
    ROOT
    / "artifacts"
    / "runtime_reports"
    / "th08_causal_future_body_schedule_differential_20260730.json"
)


class CausalFutureBodyScheduleDifferentialTests(unittest.TestCase):
    def test_report_is_deterministic_and_rejects_cartesian_pairs(
        self,
    ) -> None:
        first = build_report()
        second = build_report()

        self.assertEqual(first, second)
        self.assertTrue(first["integrity"]["passed"])
        self.assertEqual(first["integrity"]["mismatch_count"], 0)
        self.assertEqual(first["scope"]["case_count"], 2)
        self.assertGreater(
            first["scope"]["naive_cartesian_pair_count"],
            first["scope"]["causal_pair_count"],
        )
        self.assertEqual(
            first["scope"]["rejected_incompatible_pair_count"],
            first["scope"]["naive_cartesian_pair_count"]
            - first["scope"]["causal_pair_count"],
        )
        self.assertFalse(
            first["native_boundary"][
                "predictive_producer_available"
            ]
        )

    def test_every_retained_branch_has_one_compatible_pair(self) -> None:
        report = build_report()
        for case in report["cases"]:
            self.assertEqual(case["incompatible_pair_count"], 0)
            self.assertTrue(
                all(branch["matches"] for branch in case["branches"])
            )

    def test_retained_report_is_current(self) -> None:
        with REPORT.open(encoding="utf-8") as source:
            retained = json.load(source)
        self.assertEqual(retained, build_report())


if __name__ == "__main__":
    unittest.main()
