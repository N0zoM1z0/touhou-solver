from __future__ import annotations

import json
import unittest
from pathlib import Path

from analysis.th08_future_body_schedule_differential import build_report


ROOT = Path(__file__).resolve().parents[1]
REPORT = (
    ROOT
    / "artifacts"
    / "runtime_reports"
    / "th08_future_body_schedule_differential_20260730.json"
)


class FutureBodyScheduleDifferentialReportTests(unittest.TestCase):
    def test_report_is_deterministic_and_explicitly_offline(self) -> None:
        first = build_report()
        second = build_report()

        self.assertEqual(first, second)
        self.assertTrue(first["integrity"]["passed"])
        self.assertEqual(first["integrity"]["mismatch_count"], 0)
        self.assertEqual(first["scope"]["case_count"], 3)
        self.assertGreater(first["scope"]["branch_count"], 3)
        self.assertGreater(first["scope"]["frame_comparison_count"], 8)
        self.assertFalse(
            first["authority"]["physical_predictive_authority"]
        )
        self.assertFalse(
            first["producer_audit"][
                "complete_predictive_producer_available"
            ]
        )

    def test_retained_report_is_current(self) -> None:
        with REPORT.open(encoding="utf-8") as source:
            retained = json.load(source)
        self.assertEqual(retained, build_report())

    def test_ce0176_capsule_opens_all_sixteen_body_gates(self) -> None:
        report = build_report()
        ce0176 = next(
            case
            for case in report["cases"]
            if case["identity"].startswith("ce0176_")
        )
        final_frames = [
            branch["frames"][-1] for branch in ce0176["branches"]
        ]

        self.assertTrue(
            report["integrity"]["ce0176_semantic_capsule_passed"]
        )
        self.assertTrue(final_frames)
        self.assertTrue(
            all(
                frame["contact_body_ids"] == list(range(16))
                and frame["damage_body_ids"] == list(range(16))
                for frame in final_frames
            )
        )


if __name__ == "__main__":
    unittest.main()
