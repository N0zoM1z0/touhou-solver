from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from analysis.th08_future_body_generation_differential import (
    REPORT_SCHEMA,
    build_report,
    main,
)

ROOT = Path(__file__).resolve().parents[1]
RETAINED_REPORT = (
    ROOT
    / "artifacts"
    / "runtime_reports"
    / "th08_future_body_generation_differential_20260730.json"
)


class FutureBodyGenerationDifferentialTests(unittest.TestCase):
    def test_product_matches_independent_ordered_event_oracle(self) -> None:
        report = build_report()

        self.assertEqual(report["schema"], REPORT_SCHEMA)
        self.assertTrue(report["summary"]["all_product_oracle_matches"])
        self.assertEqual(report["summary"]["oracle_mismatch_count"], 0)
        self.assertEqual(report["summary"]["case_count"], 4)

    def test_boundary_only_identity_loses_hidden_same_update_reuse(
        self,
    ) -> None:
        report = build_report()
        cases = {case["name"]: case for case in report["cases"]}

        self.assertEqual(report["summary"]["boundary_only_mismatch_count"], 3)
        self.assertFalse(
            cases[
                "inactive_allocate_immediate_end_reallocate"
            ]["boundary_only_matches"]
        )
        self.assertFalse(
            cases["root_active_retire_reallocate"]["boundary_only_matches"]
        )
        self.assertTrue(
            cases["root_active_unchanged"]["boundary_only_matches"]
        )

    def test_root_slice_fixture_retains_no_predictive_authority(self) -> None:
        root = build_report()["native_root_slice_fixture"]

        self.assertEqual(root["frame_bracket"], [500, 500])
        self.assertEqual(
            root["authority_status"],
            "partial_native_root_inventory",
        )
        self.assertFalse(root["physical_predictive_authority"])
        self.assertIn("timeline_runtime_state", root["missing_requirements"])

    def test_cli_render_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.json"
            second = Path(directory) / "second.json"
            with mock.patch(
                "sys.argv",
                ["differential", str(first)],
            ):
                self.assertEqual(main(), 0)
            with mock.patch(
                "sys.argv",
                ["differential", str(second)],
            ):
                self.assertEqual(main(), 0)

            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(json.loads(first.read_text()), build_report())

    def test_retained_report_is_current(self) -> None:
        self.assertEqual(
            json.loads(RETAINED_REPORT.read_text(encoding="utf-8")),
            build_report(),
        )


if __name__ == "__main__":
    unittest.main()
