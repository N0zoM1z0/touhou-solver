#!/usr/bin/env python3
"""Regression tests for the pinned Sakuya/Remilia acceptance routes."""

from __future__ import annotations

import unittest
from pathlib import Path

from th08_route_manifest import PROFILES, build_manifest


ROOT = Path(__file__).resolve().parents[1]
DECODED = ROOT / "artifacts" / "decoded"

EXPECTED_SPELL_IDS = {
    "sakuya_remilia_lunatic_final_a": {
        1, 5, 9, 12, 16, 20, 24, 28, 31, 35, 38, 42, 46, 50, 53,
        57, 61, 65, 69, 73, 76, 103, 107, 111, 115, 118, 122, 126,
        130, 134, 138, 142, 146,
    },
    "sakuya_remilia_lunatic_final_b": {
        1, 5, 9, 12, 16, 20, 24, 28, 31, 35, 38, 42, 46, 50, 53,
        57, 61, 65, 69, 73, 76, 103, 107, 111, 115, 118, 150, 154,
        158, 162, 166, 170, 174, 178, 182, 186, 190,
    },
    "sakuya_remilia_extra": set(range(191, 205)),
    "sakuya_remilia_easy_final_b": {
        2, 6, 13, 17, 21, 25, 32, 39, 43, 47, 54, 58, 62, 66, 70,
        100, 104, 108, 112, 147, 151, 155, 159, 163, 167, 171, 175,
        179, 183, 187,
    },
    "sakuya_remilia_normal_final_b": {
        3, 7, 10, 14, 18, 22, 26, 29, 33, 36, 40, 44, 48, 51, 55,
        59, 63, 67, 71, 74, 101, 105, 109, 113, 116, 148, 152, 156,
        160, 164, 168, 172, 176, 180, 184, 188,
    },
    "sakuya_remilia_hard_final_b": {
        0, 4, 8, 11, 15, 19, 23, 27, 30, 34, 37, 41, 45, 49, 52,
        56, 60, 64, 68, 72, 75, 102, 106, 110, 114, 117, 149, 153,
        157, 161, 165, 169, 173, 177, 181, 185, 189,
    },
}

EXPECTED_CALLBACK_INDICES = {
    "sakuya_remilia_lunatic_final_a": {
        0, 1, 2, 5, 6, 7, 12, 13, 14, 15, 16, 17, 18, 20, 21,
    },
    "sakuya_remilia_lunatic_final_b": {
        0, 1, 2, 5, 6, 7, 12, 13, 14, 15, 18, 20, 21,
    },
    "sakuya_remilia_extra": {18, 22, 23, 24, 31},
    "sakuya_remilia_easy_final_b": {
        0, 1, 2, 3, 4, 5, 6, 7, 12, 13, 14, 15, 18,
    },
    "sakuya_remilia_normal_final_b": {
        0, 1, 2, 3, 4, 5, 6, 7, 12, 13, 14, 15, 18,
    },
    "sakuya_remilia_hard_final_b": {
        0, 1, 2, 5, 6, 7, 12, 13, 14, 15, 18, 20, 21,
    },
}


class RouteManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifests = {
            profile.name: build_manifest(DECODED, profile)
            for profile in PROFILES
        }

    def test_acceptance_route_spell_sets(self) -> None:
        for profile in PROFILES:
            with self.subTest(profile=profile.name):
                manifest = self.manifests[profile.name]
                self.assertEqual(
                    set(manifest["reachable_unique_spell_ids"]),
                    EXPECTED_SPELL_IDS[profile.name],
                )
                for stage in manifest["stages"]:
                    self.assertEqual(stage["unresolved_dynamic_subroutine_edges"], [])

    def test_acceptance_route_callback_sets(self) -> None:
        for profile in PROFILES:
            with self.subTest(profile=profile.name):
                manifest = self.manifests[profile.name]
                self.assertEqual(
                    set(manifest["reachable_callback_indices"]),
                    EXPECTED_CALLBACK_INDICES[profile.name],
                )
                for stage in manifest["stages"]:
                    self.assertFalse(
                        any(
                            occurrence["callback_index_dynamic"]
                            for occurrence in stage["reachable_callback_occurrences"]
                        )
                    )

    def test_lunatic_stage_three_selects_only_lunatic_variants(self) -> None:
        for profile in PROFILES[:2]:
            manifest = self.manifests[profile.name]
            stage_three = next(
                stage
                for stage in manifest["stages"]
                if stage["ecl_file"] == "ecldata3.ecl"
            )
            self.assertEqual(
                set(stage_three["candidate_unique_spell_ids"])
                - set(stage_three["reachable_unique_spell_ids"]),
                {43, 44, 45},
            )

    def test_extra_enemy_end_edges_reach_keine_sequence(self) -> None:
        profile = PROFILES[2]
        manifest = self.manifests[profile.name]
        extra = manifest["stages"][0]
        self.assertTrue({191, 192, 193}.issubset(extra["reachable_unique_spell_ids"]))

    def test_extra_spell_components_stop_at_phase_transitions(self) -> None:
        manifest = self.manifests[PROFILES[2].name]
        spells = {
            spell["spell_id"]: spell
            for spell in manifest["stages"][0]["reachable_spell_occurrences"]
        }

        spell_201 = spells[201]
        self.assertEqual(
            spell_201["component_subroutines"], [85, 126, 127, 128, 129, 130]
        )
        self.assertNotIn(82, spell_201["component_subroutines"])
        self.assertEqual(
            {
                (edge["kind"], edge["target_subroutine"])
                for edge in spell_201["phase_transition_edges"]
            },
            {("enemy_end", 82), ("timeout_phase", 82)},
        )

        spell_202 = spells[202]
        self.assertIn(141, spell_202["component_subroutines"])
        self.assertGreater(spell_202["feature_counts"]["transform_define"], 0)


if __name__ == "__main__":
    unittest.main()
