#!/usr/bin/env python3
"""Evidence regressions for the Route-2 item/drop opportunity atlas."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from analysis.th08_route2_item_drop_opportunity_atlas import (
    _source_owned_subroutines,
    build_item_drop_opportunity_atlas,
)
from th08_ecl_flow import SubEdge


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = (
    ROOT
    / "artifacts"
    / "runtime_reports"
    / "th08_immutable_content_manifest_20260731.json"
)
RETAINED = (
    ROOT
    / "artifacts"
    / "runtime_reports"
    / "th08_route2_item_drop_opportunity_atlas_20260731.json"
)


class Route2ItemDropOpportunityAtlasTests(unittest.TestCase):
    def test_source_component_stops_at_new_enemy_and_phase_boundaries(self) -> None:
        edges = (
            SubEdge(1, 0x10, 2, "call"),
            SubEdge(2, 0x20, 3, "aux_vm"),
            SubEdge(3, 0x30, 4, "interrupt_slot"),
            SubEdge(1, 0x40, 5, "child_spawn"),
            SubEdge(2, 0x50, 6, "call_with_enemy"),
            SubEdge(3, 0x60, 7, "enemy_end"),
            SubEdge(4, 0x70, 8, "health_phase"),
            SubEdge(4, 0x80, 9, "timeout_phase"),
        )
        self.assertEqual(
            _source_owned_subroutines(1, edges),
            (1, 2, 3, 4),
        )

    def test_route_atlas_retains_opportunities_without_pickup_authority(
        self,
    ) -> None:
        report = build_item_drop_opportunity_atlas(
            decoded_dir=ROOT / "artifacts" / "decoded",
            content_manifest_path=MANIFEST,
        )
        self.assertEqual(
            report["summary"],
            {
                "allocation_program_count": 151,
                "dynamic_item_operand_site_count": 0,
                "eligible_item_site_count": 60,
                "ordinary_compatible_program_count": 80,
                "ordinary_default_small_power_candidate_program_count": 56,
                "program_root_count": 218,
                "reachable_item_opcode_histogram": {
                    "0x8d": 3,
                    "0x8e": 8,
                    "0x90": 41,
                    "0xa8": 8,
                },
                "reachable_item_site_count": 60,
                "reachable_primary_drop_override_site_count": 0,
                "timeline_spawn_instance_count": 991,
                "unreachable_item_site_count": 0,
            },
        )
        self.assertEqual(
            [stage["key"] for stage in report["stages"]],
            ["stage1", "stage2", "stage3", "stage4a", "stage5", "final_b"],
        )
        stage2 = report["stages"][1]
        root7 = next(
            program
            for program in stage2["programs"]
            if program["root_subroutine"] == 7
        )
        self.assertEqual(
            root7["classification"]["configured_extra_power_count_candidates"],
            [2],
        )
        self.assertTrue(
            root7["classification"][
                "ordinary_default_small_power_on_eligible_hp_defeat_candidate"
            ]
        )
        self.assertTrue(
            all(
                not stage["flow"]["unresolved_dynamic_subroutine_edges"]
                for stage in report["stages"]
            )
        )
        self.assertFalse(report["authority"]["runtime_instruction_execution"])
        self.assertFalse(
            report["authority"]["runtime_enemy_generation_or_end_reason"]
        )
        self.assertFalse(
            report["authority"]["successful_item_allocation_or_pickup"]
        )
        self.assertFalse(
            report["authority"]["causal_power_or_later_combat_benefit"]
        )
        self.assertFalse(report["authority"]["planner_or_action_authority"])

    def test_retained_atlas_regenerates_exactly(self) -> None:
        expected = json.loads(RETAINED.read_text(encoding="utf-8"))
        actual = build_item_drop_opportunity_atlas(
            decoded_dir=ROOT / "artifacts" / "decoded",
            content_manifest_path=MANIFEST,
        )
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
