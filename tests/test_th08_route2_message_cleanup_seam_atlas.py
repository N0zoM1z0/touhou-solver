#!/usr/bin/env python3
"""Tests for the Route-2 message-cleanup/item-homing seam atlas."""

from __future__ import annotations

import unittest
from pathlib import Path

from analysis.th08_route2_message_cleanup_seam_atlas import (
    SCHEMA,
    build_message_cleanup_atlas,
)


ROOT = Path(__file__).resolve().parents[1]


class Route2MessageCleanupSeamAtlasTests(unittest.TestCase):
    def test_route_wide_seams_include_power0_history_and_fail_closed_debt(
        self,
    ) -> None:
        report = build_message_cleanup_atlas(
            decoded_dir=ROOT / "artifacts" / "decoded",
            content_manifest_path=(
                ROOT
                / "artifacts"
                / "runtime_reports"
                / "th08_immutable_content_manifest_20260731.json"
            ),
        )

        self.assertEqual(report["schema"], SCHEMA)
        self.assertEqual(report["stage_count"], 6)
        self.assertEqual(report["occurrence_count"], 23)
        self.assertEqual(
            report["stage_occurrence_counts"],
            {
                "stage1": 2,
                "stage2": 2,
                "stage3": 4,
                "stage4a": 4,
                "stage5": 2,
                "final_b": 9,
            },
        )
        self.assertTrue(
            report["classification"][
                "stage1_and_stage2_route_history_included"
            ]
        )
        self.assertTrue(
            report["classification"][
                "post_allocation_item_subtransition_exact"
            ]
        )
        self.assertFalse(
            report["classification"][
                "full_message_enemy_item_transition_exact"
            ]
        )
        self.assertTrue(
            report["next_gate"]["integrated_simulator_remains_fail_closed"]
        )

        occurrences = [
            occurrence
            for stage in report["stages"]
            for occurrence in stage["occurrences"]
        ]
        self.assertTrue(
            all(
                occurrence["native_semantics_key"] == "timeline:0x06"
                and occurrence["runtime_execution_observed"] is False
                for occurrence in occurrences
            )
        )
        self.assertEqual(
            [
                occurrence["message_script_selector"]
                for occurrence in report["stages"][0]["occurrences"]
            ],
            [0, 1],
        )
        self.assertEqual(
            report["post_allocation_item_subtransition"]["writes"],
            {
                "motion_state": 1,
                "velocity_x": 0.0,
                "velocity_y": -0.5,
            },
        )
        self.assertFalse(
            report["post_allocation_item_subtransition"][
                "immediate_pickup_or_resource_commit"
            ]
        )

    def test_generation_is_deterministic(self) -> None:
        kwargs = {
            "decoded_dir": ROOT / "artifacts" / "decoded",
            "content_manifest_path": (
                ROOT
                / "artifacts"
                / "runtime_reports"
                / "th08_immutable_content_manifest_20260731.json"
            ),
        }
        self.assertEqual(
            build_message_cleanup_atlas(**kwargs),
            build_message_cleanup_atlas(**kwargs),
        )


if __name__ == "__main__":
    unittest.main()
