#!/usr/bin/env python3
"""Focused regressions for the retained H32 model/native wind tunnel."""

from __future__ import annotations

import unittest

from analysis.th08_native_model_trajectory import (
    DEFAULT_CAUSAL_REPORT,
    DEFAULT_CAUSAL_REPORT_SHA256,
    DEFAULT_WITNESS,
    DEFAULT_WITNESS_SHA256,
    _resolve_inputs,
    build_report,
)


class NativeModelTrajectoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = build_report(
            DEFAULT_CAUSAL_REPORT,
            DEFAULT_WITNESS,
            expected_causal_sha256=DEFAULT_CAUSAL_REPORT_SHA256,
            expected_witness_sha256=DEFAULT_WITNESS_SHA256,
        )

    def test_corrected_player_layer_is_exact_for_all_h32_ticks(self) -> None:
        model = self.report["artifacts"]["model_trajectory"]["payload"]
        self.assertEqual(model["layer"], "player_mechanics")
        self.assertEqual(model["status"], "exact")
        self.assertEqual(model["exact_tick_count"], 32)
        self.assertIsNone(model["first_mismatch"])
        self.assertEqual(
            model["bounds"],
            {"left": 8.0, "top": 16.0, "right": 376.0, "bottom": 432.0},
        )
        self.assertTrue(all(not tick["mismatched_fields"] for tick in model["ticks"]))

    def test_legacy_extent_bounds_retain_first_causal_mismatch(self) -> None:
        mismatch = self.report["artifacts"]["first_mismatch_report"]["payload"][
            "player_legacy_extent_bounds"
        ]
        self.assertEqual(mismatch["status"], "mismatch")
        self.assertEqual(mismatch["exact_tick_count"], 0)
        self.assertEqual(mismatch["first_mismatch"]["manager_frame"], 2130)
        self.assertEqual(mismatch["first_mismatch"]["fields"], ["player_x"])
        self.assertEqual(
            mismatch["first_mismatch"]["model"]["player_x"]["bits"],
            0x43BCD02C,
        )
        self.assertEqual(
            mismatch["first_mismatch"]["native"]["player_x"]["bits"],
            0x43BC0000,
        )

    def test_null_actions_resolve_only_from_native_selected_action(self) -> None:
        model = self.report["artifacts"]["model_trajectory"]["payload"]
        self.assertEqual(
            model["ticks"][3]["action_source"],
            "NativeTrajectory.selected_action",
        )
        self.assertEqual(model["ticks"][3]["resolved_action"], 0x05)
        with self.assertRaisesRegex(ValueError, "null schedule"):
            _resolve_inputs(
                [None],
                [{"selected_action": 0x04, "recorded_action": 0x05}],
                [{"selected_action": 0x04, "recorded_action": 0x05}],
            )
        with self.assertRaisesRegex(ValueError, "Bomb"):
            _resolve_inputs(
                [0x02],
                [{"selected_action": 0x02, "recorded_action": 0x05}],
                [{"selected_action": 0x02, "recorded_action": 0x05}],
            )

    def test_slot45_fixture_separates_closed_form_from_native_recurrence(
        self,
    ) -> None:
        probe = self.report["artifacts"]["hazard_forecast_probe"]["payload"]
        legacy = probe["legacy_closed_form"]
        oracle = probe["independent_repeated_binary32_oracle"]
        production = probe["production"]
        self.assertEqual(legacy["status"], "mismatch")
        self.assertEqual(legacy["first_mismatch"]["manager_frame"], 2132)
        self.assertEqual(legacy["first_mismatch"]["axes"], ["x"])
        self.assertEqual(
            legacy["first_mismatch"]["projected"]["x"]["bits"],
            0x43B97BCA,
        )
        self.assertEqual(
            legacy["first_mismatch"]["native"]["x"]["bits"],
            0x43B97BCB,
        )
        self.assertEqual(oracle["status"], "exact")
        self.assertIsNone(oracle["first_mismatch"])
        self.assertEqual(production["status"], "exact")
        self.assertIsNone(production["first_mismatch"])

    def test_report_generation_is_deterministic_and_content_addressed(self) -> None:
        rebuilt = build_report(
            DEFAULT_CAUSAL_REPORT,
            DEFAULT_WITNESS,
            expected_causal_sha256=DEFAULT_CAUSAL_REPORT_SHA256,
            expected_witness_sha256=DEFAULT_WITNESS_SHA256,
        )
        self.assertEqual(rebuilt, self.report)
        for name in (
            "model_trajectory",
            "first_mismatch_report",
            "hazard_forecast_probe",
        ):
            self.assertRegex(
                rebuilt["artifacts"][name]["artifact_id"],
                r"^sha256:[0-9a-f]{64}$",
            )


if __name__ == "__main__":
    unittest.main()
