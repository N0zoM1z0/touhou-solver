from __future__ import annotations

import unittest
from dataclasses import replace
from pathlib import Path

from analysis.th08_route2_normal_shot_content_audit import (
    audit_route2_normal_shot_content,
    build_report,
)
from th08_sht import parse_sht


ROOT = Path(__file__).resolve().parents[1]
PRIMARY = ROOT / "artifacts" / "decoded" / "ply02a.sht"
SECONDARY = ROOT / "artifacts" / "decoded" / "ply02as.sht"


class Route2NormalShotContentAuditTests(unittest.TestCase):
    def test_pinned_route2_normal_damage_path_is_content_closed(self) -> None:
        report = build_report(
            primary_path=PRIMARY,
            secondary_path=SECONDARY,
        )

        self.assertEqual(
            report["result"]["status"],
            "route2_normal_damage_path_content_closed",
        )
        self.assertEqual(report["aggregate"]["normal_record_count"], 53)
        self.assertEqual(
            report["aggregate"][
                "damage_path_incompatible_normal_record_count"
            ],
            0,
        )
        primary, secondary = report["profiles"]
        self.assertEqual(primary["normal_record_count"], 26)
        self.assertEqual(secondary["normal_record_count"], 27)
        self.assertEqual(primary["normal_shot_types"], [0])
        self.assertEqual(secondary["normal_shot_types"], [0])
        self.assertEqual(
            primary["normal_callback_indices"]["callback_0"],
            [0],
        )
        self.assertEqual(
            secondary["normal_callback_indices"]["callback_0"],
            [0, 7],
        )
        for profile in (primary, secondary):
            self.assertEqual(
                profile["normal_callback_indices"]["callback_1"],
                [0],
            )
            self.assertEqual(
                profile["normal_callback_indices"]["callback_3"],
                [0],
            )
        self.assertEqual(secondary["special_level_indices"], [6, 7])
        self.assertEqual(secondary["special_record_count"], 34)

    def test_mutated_normal_type_is_reported_open(self) -> None:
        primary = parse_sht(PRIMARY)
        secondary = parse_sht(SECONDARY)
        level = primary.levels[0]
        mutated_level = replace(
            level,
            shots=(replace(level.shots[0], shot_type=4),),
        )
        mutated_primary = replace(
            primary,
            levels=(mutated_level, *primary.levels[1:]),
        )

        report = audit_route2_normal_shot_content(
            mutated_primary,
            secondary,
        )

        self.assertEqual(
            report["result"]["status"],
            "route2_normal_damage_path_content_open",
        )
        self.assertTrue(
            report["result"]["type45_reachable_from_normal_selector"]
        )
        self.assertEqual(
            report["aggregate"][
                "damage_path_incompatible_normal_record_count"
            ],
            1,
        )

    def test_unexpected_normal_power_partition_fails_closed(self) -> None:
        primary = parse_sht(PRIMARY)
        secondary = parse_sht(SECONDARY)
        mutated_primary = replace(
            primary,
            levels=(
                replace(primary.levels[0], power_upper_bound=9),
                *primary.levels[1:],
            ),
        )

        with self.assertRaisesRegex(ValueError, "normal Power bounds"):
            audit_route2_normal_shot_content(
                mutated_primary,
                secondary,
            )


if __name__ == "__main__":
    unittest.main()
