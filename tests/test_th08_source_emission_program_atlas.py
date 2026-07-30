#!/usr/bin/env python3
"""Evidence regressions for the Route-2 source/emission program atlas."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from analysis.th08_source_emission_program_atlas import (
    _source_owned_subroutines,
    build_source_emission_atlas,
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
    / "th08_source_emission_program_atlas_20260731.json"
)


class SourceEmissionProgramAtlasTests(unittest.TestCase):
    def test_source_component_excludes_cross_source_and_phase_edges(self) -> None:
        edges = (
            SubEdge(1, 0x10, 2, "call"),
            SubEdge(2, 0x20, 3, "aux_vm"),
            SubEdge(3, 0x30, 4, "interrupt_slot"),
            SubEdge(1, 0x40, 5, "child_spawn"),
            SubEdge(2, 0x50, 6, "call_with_enemy"),
            SubEdge(3, 0x60, 7, "enemy_end"),
            SubEdge(4, 0x70, 8, "health_phase"),
        )
        self.assertEqual(
            _source_owned_subroutines(1, edges),
            (1, 2, 3, 4),
        )

    def test_route_atlas_retains_candidates_without_kill_authority(self) -> None:
        report = build_source_emission_atlas(
            decoded_dir=ROOT / "artifacts" / "decoded",
            content_manifest_path=MANIFEST,
        )
        self.assertEqual(
            report["summary"],
            {
                "boss_possible_program_count": 22,
                "child_emitter_site_count": 143,
                "direct_emission_site_count": 200,
                "ordinary_compatible_program_count": 48,
                "ordinary_candidate_child_emitter_site_count": 88,
                "ordinary_candidate_direct_emission_site_count": 65,
                "ordinary_candidate_periodic_control_site_count": 39,
                "ordinary_static_emitter_candidate_program_count": 39,
                "ordinary_static_emitter_candidate_spawn_count": 909,
                "periodic_control_site_count": 49,
                "spawn_instance_count": 991,
                "unique_source_program_count": 70,
            },
        )
        self.assertEqual(
            [stage["key"] for stage in report["stages"]],
            ["stage1", "stage2", "stage3", "stage4a", "stage5", "final_b"],
        )
        self.assertTrue(
            all(
                not stage["flow"]["unresolved_dynamic_subroutine_edges"]
                for stage in report["stages"]
            )
        )
        candidates = [
            program
            for stage in report["stages"]
            for program in stage["source_programs"]
            if program["classification"]["ordinary_static_emitter_candidate"]
        ]
        self.assertEqual(len(candidates), 39)
        self.assertTrue(
            all(
                not program["classification"]["boss_control_possible"]
                for program in candidates
            )
        )
        self.assertTrue(
            any(
                program["classification"]["child_emitter_site_count"] > 0
                for program in candidates
            )
        )
        self.assertFalse(report["authority"]["runtime_instruction_execution"])
        self.assertFalse(report["authority"]["absolute_kill_deadline"])
        self.assertFalse(report["authority"]["prevented_birth_count"])
        self.assertFalse(report["authority"]["planner_or_action_authority"])

    def test_retained_atlas_regenerates_exactly(self) -> None:
        expected = json.loads(RETAINED.read_text(encoding="utf-8"))
        actual = build_source_emission_atlas(
            decoded_dir=ROOT / "artifacts" / "decoded",
            content_manifest_path=MANIFEST,
        )
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
