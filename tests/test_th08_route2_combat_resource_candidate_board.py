#!/usr/bin/env python3
"""Evidence regressions for the Route-2 combat/resource candidate board."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from analysis.th08_route2_combat_resource_candidate_board import (
    _candidate_families,
    build_combat_resource_candidate_board,
)


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "artifacts" / "runtime_reports"
SOURCE_ATLAS = REPORTS / "th08_source_emission_program_atlas_20260731.json"
ITEM_ATLAS = REPORTS / "th08_route2_item_drop_opportunity_atlas_20260731.json"
RETAINED = (
    REPORTS / "th08_route2_combat_resource_candidate_board_20260731.json"
)


class Route2CombatResourceCandidateBoardTests(unittest.TestCase):
    def test_candidate_families_are_named_cohorts_not_scalar_scores(
        self,
    ) -> None:
        self.assertEqual(
            _candidate_families(
                ordinary_emitter=True,
                direct_emission=True,
                child_emitter=True,
                periodic_control=True,
                default_small_power=True,
                configured_extra_power_counts=(2,),
                direct_power_bundle_counts=(8,),
                ordinary_compatible=True,
            ),
            (
                "ordinary_emitter_default_small_power",
                "ordinary_emitter_configured_extra_power",
                "ordinary_emitter_direct_power_bundle",
                "ordinary_emitter_power_intersection",
                "power_intersection_direct_emission",
                "power_intersection_child_emitter",
                "power_intersection_periodic_control",
            ),
        )
        self.assertEqual(
            _candidate_families(
                ordinary_emitter=False,
                direct_emission=False,
                child_emitter=False,
                periodic_control=False,
                default_small_power=True,
                configured_extra_power_counts=(),
                direct_power_bundle_counts=(),
                ordinary_compatible=True,
            ),
            ("ordinary_resource_without_emitter_candidate",),
        )

    def test_board_intersects_all_ordinary_emitter_candidates_fail_closed(
        self,
    ) -> None:
        report = build_combat_resource_candidate_board(
            source_atlas_path=SOURCE_ATLAS,
            item_atlas_path=ITEM_ATLAS,
        )
        self.assertEqual(
            report["summary"],
            {
                "candidate_family_counts": {
                    "ordinary_emitter_configured_extra_power": 16,
                    "ordinary_emitter_default_small_power": 39,
                    "ordinary_emitter_power_intersection": 39,
                    "ordinary_resource_without_emitter_candidate": 9,
                    "power_intersection_child_emitter": 14,
                    "power_intersection_direct_emission": 32,
                    "power_intersection_periodic_control": 13,
                },
                "intersection_timeline_spawn_instance_count": 909,
                "item_only_program_count": 148,
                "joined_source_program_count": 70,
                "ordinary_emitter_candidate_count": 39,
                "ordinary_emitter_power_intersection_count": 39,
            },
        )
        self.assertTrue(
            report["selection_contract"]["no_scalar_utility_ranking"]
        )
        self.assertFalse(report["authority"]["verified_kill_or_prevented_birth"])
        self.assertFalse(
            report["authority"]["verified_item_allocation_or_pickup"]
        )
        self.assertFalse(report["authority"]["causal_power_or_survival_benefit"])
        self.assertFalse(report["authority"]["phase_option_edge"])
        self.assertFalse(report["authority"]["planner_or_action_authority"])

    def test_retained_board_regenerates_exactly(self) -> None:
        expected = json.loads(RETAINED.read_text(encoding="utf-8"))
        actual = build_combat_resource_candidate_board(
            source_atlas_path=SOURCE_ATLAS,
            item_atlas_path=ITEM_ATLAS,
        )
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
