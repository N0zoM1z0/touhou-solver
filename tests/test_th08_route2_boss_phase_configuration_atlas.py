from __future__ import annotations

import json
from pathlib import Path
import unittest

from analysis.th08_route2_boss_phase_configuration_atlas import (
    _program_subroutines,
    build_boss_phase_configuration_atlas,
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
    / "th08_route2_boss_phase_configuration_atlas_20260731.json"
)


class Route2BossPhaseConfigurationAtlasTests(unittest.TestCase):
    def test_same_enemy_program_includes_phase_edges_only(self) -> None:
        edges = (
            SubEdge(1, 0x10, 2, "call"),
            SubEdge(2, 0x20, 3, "aux_vm"),
            SubEdge(3, 0x30, 4, "interrupt_slot"),
            SubEdge(4, 0x40, 5, "health_phase"),
            SubEdge(5, 0x50, 6, "timeout_phase"),
            SubEdge(6, 0x60, 7, "enemy_end"),
            SubEdge(1, 0x70, 8, "child_spawn"),
            SubEdge(2, 0x80, 9, "call_with_enemy"),
        )
        self.assertEqual(
            _program_subroutines(1, edges),
            (1, 2, 3, 4, 5, 6, 7),
        )

    def test_route_atlas_retains_complete_literal_inventory(self) -> None:
        report = build_boss_phase_configuration_atlas(
            decoded_dir=ROOT / "artifacts" / "decoded",
            content_manifest_path=MANIFEST,
        )
        self.assertEqual(
            report["summary"],
            {
                "boss_root_program_count": 22,
                "boss_root_spawn_instance_count": 22,
                "dynamic_phase_control_site_count": 0,
                "effect_counts": {
                    "set_health": 40,
                    "set_health_phase_transition": 25,
                    "set_timeout_phase_transition": 78,
                    "set_timer_current": 37,
                },
                "eligible_phase_control_site_count": 189,
                "eligible_unreachable_phase_control_site_count": 9,
                "health_timeout_relation_counts": {
                    "partially_shared_successors": 4,
                    "same_successor_set": 17,
                    "timeout_only": 53,
                },
                "phase_subroutine_count": 88,
                "reachable_phase_control_site_count": 180,
                "transition_edge_count": 103,
            },
        )
        self.assertEqual(
            [stage["key"] for stage in report["stages"]],
            ["stage1", "stage2", "stage3", "stage4a", "stage5", "final_b"],
        )
        self.assertEqual(
            [
                stage["summary"]["eligible_unreachable_phase_control_site_count"]
                for stage in report["stages"]
            ],
            [0, 3, 6, 0, 0, 0],
        )
        self.assertTrue(
            all(
                not stage["flow"]["unresolved_dynamic_subroutine_edges"]
                for stage in report["stages"]
            )
        )

    def test_health_can_select_successors_absent_from_timeout(self) -> None:
        report = build_boss_phase_configuration_atlas(
            decoded_dir=ROOT / "artifacts" / "decoded",
            content_manifest_path=MANIFEST,
        )
        divergent = {
            (stage["key"], phase["subroutine"]): (
                phase["health_successor_subroutines"],
                phase["timeout_successor_subroutines"],
            )
            for stage in report["stages"]
            for phase in stage["phase_subroutines"]
            if phase["health_timeout_successor_relation"]
            == "partially_shared_successors"
        }
        self.assertEqual(
            divergent,
            {
                ("stage2", 29): ([44, 51], [44]),
                ("stage3", 35): ([44, 46], [44]),
                ("stage3", 38): ([62, 66], [62]),
                ("stage5", 56): ([63, 74], [63]),
            },
        )

    def test_divergent_configuration_sites_are_exact(self) -> None:
        report = build_boss_phase_configuration_atlas(
            decoded_dir=ROOT / "artifacts" / "decoded",
            content_manifest_path=MANIFEST,
        )
        stage2 = next(
            stage for stage in report["stages"] if stage["key"] == "stage2"
        )
        phase = next(
            item
            for item in stage2["phase_subroutines"]
            if item["subroutine"] == 29
        )
        transitions = {
            (
                site["offset_hex"],
                site["effect"]["kind"],
                site["effect"]["successor_subroutine"]["literal_value"],
            )
            for site in phase["sites"]
            if site["effect"]["kind"]
            in {
                "set_health_phase_transition",
                "set_timeout_phase_transition",
            }
        }
        self.assertEqual(
            transitions,
            {
                ("0x3d98", "set_timeout_phase_transition", 44),
                ("0x3dac", "set_health_phase_transition", 44),
                ("0x3dc4", "set_health_phase_transition", 51),
            },
        )
        transition_edges = [
            edge
            for edge in stage2["transition_edges"]
            if edge["source_subroutine"] == 29
        ]
        self.assertTrue(
            all(
                edge["successor_write_requires"]
                == "engine_flags_bit14_clear_or_mode_bits7_8_zero"
                for edge in transition_edges
            )
        )

    def test_successor_write_mode_gate_is_explicit(self) -> None:
        report = build_boss_phase_configuration_atlas(
            decoded_dir=ROOT / "artifacts" / "decoded",
            content_manifest_path=MANIFEST,
        )
        gate = report["native_ecl_write_semantics"]["successor_write_gate"]
        self.assertEqual(
            gate,
            {
                "symbolic_name": (
                    "engine_flags_bit14_clear_or_mode_bits7_8_zero"
                ),
                "full_configuration_when": (
                    "(engine_flags & 0x4000) == 0 or "
                    "((engine_flags >> 7) & 0x3) == 0"
                ),
                "retained_successor_when_suppressed": (
                    "(engine_flags & 0x4000) != 0 and "
                    "((engine_flags >> 7) & 0x3) != 0"
                ),
            },
        )

    def test_static_inventory_has_no_runtime_or_action_authority(self) -> None:
        report = build_boss_phase_configuration_atlas(
            decoded_dir=ROOT / "artifacts" / "decoded",
            content_manifest_path=MANIFEST,
        )
        self.assertTrue(
            report["authority"]["literal_phase_configuration_inventory"]
        )
        self.assertFalse(report["authority"]["runtime_instruction_execution"])
        self.assertFalse(report["authority"]["runtime_phase_sequence"])
        self.assertFalse(
            report["authority"]["unconditional_runtime_successor_registry"]
        )
        self.assertFalse(
            report["authority"]["physical_phase_duration_or_damage_benefit"]
        )
        self.assertFalse(report["authority"]["planner_or_action_authority"])
        self.assertFalse(report["authority"]["physical_trial_run"])

    def test_retained_atlas_regenerates_exactly(self) -> None:
        expected = json.loads(RETAINED.read_text(encoding="utf-8"))
        actual = build_boss_phase_configuration_atlas(
            decoded_dir=ROOT / "artifacts" / "decoded",
            content_manifest_path=MANIFEST,
        )
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
