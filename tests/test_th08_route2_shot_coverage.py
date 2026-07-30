from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
ANALYSIS = SCRIPTS / "analysis"
for path in (SCRIPTS, ANALYSIS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from th08_route2_shot_coverage import (  # noqa: E402
    HorizontalInterval,
    merge_horizontal_intervals,
    normal_level_cadence_summary,
    normal_level_horizontal_coverage,
)
from th08_route2_shot_coverage_atlas import build_report  # noqa: E402
from th08_sht import parse_sht  # noqa: E402


class Route2ShotCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.primary_path = ROOT / "artifacts/decoded/ply02a.sht"
        cls.secondary_path = ROOT / "artifacts/decoded/ply02as.sht"
        cls.primary = parse_sht(cls.primary_path)
        cls.secondary = parse_sht(cls.secondary_path)

    def test_interval_merge_preserves_disjoint_support(self) -> None:
        self.assertEqual(
            merge_horizontal_intervals(
                (
                    HorizontalInterval(4.0, 7.0),
                    HorizontalInterval(0.0, 2.0),
                    HorizontalInterval(1.0, 5.0),
                    HorizontalInterval(9.0, 10.0),
                )
            ),
            (
                HorizontalInterval(0.0, 7.0),
                HorizontalInterval(9.0, 10.0),
            ),
        )

    def test_power0_unfocused_vertical_shot_has_exact_aabb_width(self) -> None:
        intervals = normal_level_horizontal_coverage(
            self.primary.levels[0],
            profile="unfocused_primary",
            target_rise=128.0,
        )
        self.assertEqual(len(intervals), 1)
        self.assertAlmostEqual(intervals[0].lower, -9.0, places=4)
        self.assertAlmostEqual(intervals[0].upper, 9.0, places=4)

    def test_focused_option_coverage_is_an_outer_envelope(self) -> None:
        intervals = normal_level_horizontal_coverage(
            self.secondary.levels[0],
            profile="focused_secondary",
            target_rise=128.0,
        )
        self.assertLess(intervals[0].lower, -30.0)
        self.assertGreater(intervals[-1].upper, 30.0)
        self.assertGreater(
            sum(interval.width for interval in intervals),
            18.0,
        )

    def test_empty_pool_cycle_counts_callback_rng(self) -> None:
        primary = normal_level_cadence_summary(self.primary.levels[0])
        secondary = normal_level_cadence_summary(self.secondary.levels[0])
        self.assertEqual(primary.emissions_per_cycle, 4)
        self.assertEqual(primary.base_damage_per_cycle, 192)
        self.assertEqual(primary.callback_rng_u16_calls_per_cycle, 0)
        self.assertEqual(secondary.emissions_per_cycle, 8)
        self.assertEqual(secondary.base_damage_per_cycle, 248)
        self.assertEqual(secondary.callback_rng_u16_calls_per_cycle, 8)

    def test_report_covers_every_normal_power_partition(self) -> None:
        report = build_report(
            primary_path=self.primary_path,
            secondary_path=self.secondary_path,
        )
        rows = report["power_profiles"]
        self.assertEqual(len(rows), 6)
        self.assertEqual(
            [
                row["power_interval"]["upper_exclusive"]
                for row in rows
            ],
            [8, 24, 48, 80, 128, 999],
        )
        aggregate = report["aggregate_static_width_relations"]
        self.assertEqual(aggregate["comparison_count"], 18)
        self.assertGreater(aggregate["unfocused_primary_wider"], 0)
        self.assertGreater(aggregate["focused_outer_envelope_wider"], 0)
        self.assertFalse(report["promotion"]["live_focus_ranking_enabled"])


if __name__ == "__main__":
    unittest.main()
