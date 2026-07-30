from __future__ import annotations

import unittest

from analysis.th08_native_combat_branch_report import (
    CAUSAL_SEARCH_SCHEMA,
    NativeCombatBranchReportError,
    ROLLING_ACCEPTED_STATUS,
    ROLLING_SCHEMA,
    build_report,
)


def _summary(frame: int, *, hp: int = 100, damage: int = 0) -> dict[str, int]:
    return {
        "manager_frame": frame,
        "active_shot_count": 3,
        "damage_eligible_shot_count": 2,
        "hit_state_shot_count": 1,
        "route2_normal_damage_path_compatible_active_shot_count": 3,
        "route2_normal_damage_path_incompatible_active_shot_count": 0,
        "active_enemy_target_count": 1,
        "positive_hp_target_count": 1,
        "positive_hp_sum": hp,
        "published_frame_damage_sum": damage,
        "open_hp_gate_target_count": 1,
        "supported_primary_overlap_target_count": 1,
        "unresolved_overlap_target_count": 0,
        "supported_primary_contribution_sum": 20,
        "open_gate_supported_primary_contribution_sum": 20,
        "supported_alternate_contribution_sum": 0,
    }


def _projection(frame: int, *, hp: int = 100, damage: int = 0) -> dict[str, object]:
    return {
        "sha256": f"{frame:064x}",
        "summary": _summary(frame, hp=hp, damage=damage),
    }


def _tick(
    frame: int,
    *,
    action: int,
    hp: int = 100,
    damage: int = 0,
    player_phase: int = 0,
) -> dict[str, object]:
    return {
        "selected_action": action,
        "compact_state": {
            "manager_frame": frame,
            "player_phase": player_phase,
        },
        "native_combat_projection": _projection(
            frame,
            hp=hp,
            damage=damage,
        ),
    }


class NativeCombatBranchReportTests(unittest.TestCase):
    def test_rolling_report_filters_survival_without_promoting_proxy(self) -> None:
        source = {
            "schema": ROLLING_SCHEMA,
            "result": {
                "status": ROLLING_ACCEPTED_STATUS,
                "root_native_combat_projection": _projection(100, hp=120),
                "root_compact_state": {"player_phase": 0},
                "branches": {
                    "a1": {"ticks": [_tick(101, action=0x05, hp=110, damage=10)]},
                    "a2": {"ticks": [_tick(101, action=0x05, hp=110, damage=10)]},
                    "b": {
                        "ticks": [
                            _tick(
                                101,
                                action=0x15,
                                hp=105,
                                damage=15,
                                player_phase=2,
                            )
                        ]
                    },
                },
            },
        }

        report = build_report(
            source,
            source_path="fixture.json",
            source_sha256="a" * 64,
        )

        self.assertEqual(report["branch_count"], 3)
        self.assertEqual(report["survivor_count"], 2)
        self.assertEqual(
            report["survival_filtered_candidate_ids"],
            ["a1", "a2"],
        )
        by_id = {row["branch_id"]: row for row in report["branches"]}
        self.assertEqual(
            by_id["a1"]["metrics"]["observed_positive_hp_sum_change"],
            -10,
        )
        self.assertEqual(
            by_id["b"]["candidate_status"],
            "rejected_hard_survival",
        )
        self.assertFalse(report["result"]["candidate_ranking_authority"])

    def test_rolling_report_rejects_branch_from_hit_root(self) -> None:
        source = {
            "schema": ROLLING_SCHEMA,
            "result": {
                "status": ROLLING_ACCEPTED_STATUS,
                "root_native_combat_projection": _projection(100),
                "root_compact_state": {"player_phase": 2},
                "branches": {
                    branch_id: {
                        "ticks": [_tick(101, action=0x05)]
                    }
                    for branch_id in ("a1", "a2", "b")
                },
            },
        }

        report = build_report(
            source,
            source_path="fixture.json",
            source_sha256="d" * 64,
        )

        self.assertEqual(report["survivor_count"], 0)
        self.assertTrue(
            all(
                row["candidate_status"] == "rejected_hard_survival"
                for row in report["branches"]
            )
        )

    def test_non_normal_active_shot_keeps_content_boundary_open(self) -> None:
        source = {
            "schema": ROLLING_SCHEMA,
            "result": {
                "status": ROLLING_ACCEPTED_STATUS,
                "root_native_combat_projection": _projection(100),
                "root_compact_state": {"player_phase": 0},
                "branches": {
                    branch_id: {
                        "ticks": [_tick(101, action=0x05)]
                    }
                    for branch_id in ("a1", "a2", "b")
                },
            },
        }
        source["result"]["root_native_combat_projection"]["summary"][
            "route2_normal_damage_path_compatible_active_shot_count"
        ] = 2
        source["result"]["root_native_combat_projection"]["summary"][
            "route2_normal_damage_path_incompatible_active_shot_count"
        ] = 1

        report = build_report(
            source,
            source_path="fixture.json",
            source_sha256="e" * 64,
        )

        self.assertEqual(report["survivor_count"], 3)
        self.assertTrue(
            all(
                row["candidate_status"]
                == "survival_filtered_proxy_only_non_normal_shot_content"
                for row in report["branches"]
            )
        )
        self.assertTrue(
            all(
                not row["authority"][
                    "route2_normal_damage_path_content_compatible"
                ]
                for row in report["branches"]
            )
        )

    def test_causal_search_requires_new_combat_projection_schema(self) -> None:
        source = {
            "schema": CAUSAL_SEARCH_SCHEMA,
            "result": {
                "status": "causal_secondary_search_passed",
                "origin": {},
                "prefixes": [],
            },
        }

        with self.assertRaisesRegex(
            NativeCombatBranchReportError,
            "native_combat_projection",
        ):
            build_report(
                source,
                source_path="fixture.json",
                source_sha256="b" * 64,
            )

    def test_rejects_unaccepted_rolling_transaction(self) -> None:
        source = {
            "schema": ROLLING_SCHEMA,
            "result": {"status": "trial_error"},
        }

        with self.assertRaisesRegex(
            NativeCombatBranchReportError,
            "did not pass",
        ):
            build_report(
                source,
                source_path="fixture.json",
                source_sha256="c" * 64,
            )


if __name__ == "__main__":
    unittest.main()
