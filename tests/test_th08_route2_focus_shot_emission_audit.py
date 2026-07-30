#!/usr/bin/env python3
"""Tests for the retained route-2 Focus/Shot emission audit."""

from __future__ import annotations

import unittest
from pathlib import Path

from analysis.th08_route2_focus_shot_emission_audit import build_report


ROOT = Path(__file__).resolve().parents[1]


class Route2FocusShotEmissionAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = build_report(
            primary_path=ROOT / "artifacts/decoded/ply02a.sht",
            secondary_path=ROOT / "artifacts/decoded/ply02as.sht",
            h1_report_path=(
                ROOT
                / "artifacts/runtime_reports"
                / "th08_native_h1_ecl_source_differential_root2129_20260730.json"
            ),
        )

    def test_root_prefix_is_compatible_but_not_promoted(self) -> None:
        root = self.report["root2129"]
        self.assertEqual(root["observed"]["pre_hostile_prefix_u16_calls"], 4)
        self.assertEqual(
            root["classification"],
            "compatible_player_shot_prefix_not_unique_causal_proof",
        )
        self.assertTrue(root["compatible_player_shot_states"])
        self.assertFalse(
            self.report["promotion"]["live_focus_ranking_enabled"],
        )

    def test_unfocused_profile_never_consumes_callback_rng(self) -> None:
        rows = self.report["focus_profile_comparison_at_power128"][
            "unfocused_primary"
        ]["cadence_rows"]
        self.assertTrue(all(row["rng_u16_calls"] == 0 for row in rows))

    def test_focused_cadence_zero_accounts_for_four_u16_calls(self) -> None:
        row = self.report["focus_profile_comparison_at_power128"][
            "focused_secondary"
        ]["cadence_rows"][0]
        self.assertEqual(row["record_offsets"], [1316, 1372, 1484, 1540])
        self.assertEqual(row["rng_u16_calls"], 4)


if __name__ == "__main__":
    unittest.main()
