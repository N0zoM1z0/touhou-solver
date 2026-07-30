from __future__ import annotations

import unittest

from analysis.th08_native_combat_branch_report import (
    CAUSAL_SEARCH_SCHEMA,
    NativeCombatBranchReportError,
    ROLLING_ACCEPTED_STATUS,
    ROLLING_SCHEMA,
    build_report,
)


def _summary(
    frame: int,
    *,
    hp: int = 100,
    damage: int = 0,
    route_id: int = 2,
    bomb_active: bool = False,
    active_input: int = 0x05,
) -> dict[str, object]:
    return {
        "manager_frame": frame,
        "route_id": route_id,
        "bomb_active": bomb_active,
        "active_input": active_input,
        "active_shot_count": 3,
        "damage_eligible_shot_count": 2,
        "hit_state_shot_count": 1,
        "route2_normal_damage_path_compatible_active_shot_count": 3,
        "route2_normal_damage_path_incompatible_active_shot_count": 0,
        "route2_exact_normal_source_active_shot_count": 3,
        "route2_non_normal_or_unknown_source_active_shot_count": 0,
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
        "supported_primary_damage_region_contribution_sum": 3,
        "supported_alternate_damage_region_contribution_sum": 1,
        "supported_resolved_hp_damage_sum": 24,
    }


def _projection(
    frame: int,
    *,
    hp: int = 100,
    damage: int = 0,
    route_id: int = 2,
    bomb_active: bool = False,
    active_input: int = 0x05,
) -> dict[str, object]:
    return {
        "sha256": f"{frame:064x}",
        "summary": _summary(
            frame,
            hp=hp,
            damage=damage,
            route_id=route_id,
            bomb_active=bomb_active,
            active_input=active_input,
        ),
    }


def _compact_state(
    *,
    player_phase: int = 0,
    lives: float = 3.0,
    bombs: float = 3.0,
    power: float = 64.0,
) -> dict[str, object]:
    return {
        "player_phase": player_phase,
        "resources": {
            "lives": lives,
            "bombs": bombs,
            "power": power,
        },
    }


def _tick(
    frame: int,
    *,
    action: int,
    hp: int = 100,
    damage: int = 0,
    player_phase: int = 0,
    route_id: int = 2,
    bomb_active: bool = False,
    active_input: int = 0x05,
    lives: float = 3.0,
    bombs: float = 3.0,
    power: float = 64.0,
) -> dict[str, object]:
    return {
        "selected_action": action,
        "compact_state": {
            "manager_frame": frame,
            **_compact_state(
                player_phase=player_phase,
                lives=lives,
                bombs=bombs,
                power=power,
            ),
        },
        "native_combat_projection": _projection(
            frame,
            hp=hp,
            damage=damage,
            route_id=route_id,
            bomb_active=bomb_active,
            active_input=active_input,
        ),
    }


class NativeCombatBranchReportTests(unittest.TestCase):
    def test_rolling_report_filters_survival_without_promoting_proxy(self) -> None:
        source = {
            "schema": ROLLING_SCHEMA,
            "result": {
                "status": ROLLING_ACCEPTED_STATUS,
                "root_native_combat_projection": _projection(100, hp=120),
                "root_compact_state": _compact_state(),
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
                "root_compact_state": _compact_state(player_phase=2),
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

    def test_nmnb_and_route_scope_fail_closed_before_combat_proxy(self) -> None:
        source = {
            "schema": ROLLING_SCHEMA,
            "result": {
                "status": ROLLING_ACCEPTED_STATUS,
                "root_native_combat_projection": _projection(100),
                "root_compact_state": _compact_state(),
                "branches": {
                    "a1": {"ticks": [_tick(101, action=0x05)]},
                    "a2": {"ticks": [_tick(101, action=0x07)]},
                    "b": {
                        "ticks": [
                            _tick(
                                101,
                                action=0x05,
                                bomb_active=True,
                                active_input=0x07,
                            )
                        ]
                    },
                },
            },
        }

        report = build_report(
            source,
            source_path="fixture.json",
            source_sha256="1" * 64,
        )

        self.assertEqual(report["survivor_count"], 3)
        self.assertEqual(report["route2_nmnb_eligible_count"], 1)
        self.assertEqual(
            report["route2_nmnb_filtered_candidate_ids"],
            ["a1"],
        )
        by_id = {row["branch_id"]: row for row in report["branches"]}
        self.assertEqual(
            by_id["a2"]["candidate_status"],
            "rejected_hard_no_bomb",
        )
        self.assertEqual(
            by_id["b"]["candidate_status"],
            "rejected_hard_no_bomb",
        )
        self.assertEqual(by_id["a2"]["bomb_action_tick_indices"], [0])
        self.assertEqual(
            by_id["b"]["bomb_active_manager_frames"],
            [101],
        )
        self.assertEqual(
            by_id["b"]["bomb_active_input_manager_frames"],
            [101],
        )

    def test_non_route2_branch_is_outside_combat_proxy_scope(self) -> None:
        source = {
            "schema": ROLLING_SCHEMA,
            "result": {
                "status": ROLLING_ACCEPTED_STATUS,
                "root_native_combat_projection": _projection(100),
                "root_compact_state": _compact_state(),
                "branches": {
                    branch_id: {
                        "ticks": [
                            _tick(101, action=0x05, route_id=1)
                        ]
                    }
                    for branch_id in ("a1", "a2", "b")
                },
            },
        }

        report = build_report(
            source,
            source_path="fixture.json",
            source_sha256="2" * 64,
        )

        self.assertEqual(report["survivor_count"], 3)
        self.assertEqual(report["route2_nmnb_eligible_count"], 0)
        self.assertTrue(
            all(
                row["candidate_status"] == "out_of_scope_non_route2"
                and not row["route2_scope"]
                for row in report["branches"]
            )
        )

    def test_resource_seams_close_life_and_bomb_temporal_gaps(self) -> None:
        source = {
            "schema": ROLLING_SCHEMA,
            "result": {
                "status": ROLLING_ACCEPTED_STATUS,
                "root_native_combat_projection": _projection(100),
                "root_compact_state": _compact_state(power=64.0),
                "branches": {
                    "a1": {
                        "ticks": [
                            _tick(101, action=0x05, power=65.0)
                        ]
                    },
                    "a2": {
                        "ticks": [
                            _tick(101, action=0x05, bombs=2.0)
                        ]
                    },
                    "b": {
                        "ticks": [
                            _tick(101, action=0x05, lives=2.0)
                        ]
                    },
                },
            },
        }

        report = build_report(
            source,
            source_path="fixture.json",
            source_sha256="4" * 64,
        )

        self.assertEqual(report["survivor_count"], 2)
        self.assertEqual(report["route2_nmnb_eligible_count"], 1)
        by_id = {row["branch_id"]: row for row in report["branches"]}
        self.assertEqual(
            by_id["a1"]["metrics"]["resource_delta"]["power"],
            1.0,
        )
        self.assertEqual(
            by_id["a2"]["candidate_status"],
            "rejected_hard_no_bomb",
        )
        self.assertEqual(
            by_id["a2"]["bomb_resource_decrease_tick_indices"],
            [0],
        )
        self.assertEqual(
            by_id["b"]["candidate_status"],
            "rejected_hard_survival",
        )
        self.assertEqual(by_id["b"]["life_decrease_tick_indices"], [0])
        self.assertTrue(by_id["b"]["player_phase_survived_to_endpoint"])

    def test_nonfinite_resource_state_fails_closed(self) -> None:
        source = {
            "schema": ROLLING_SCHEMA,
            "result": {
                "status": ROLLING_ACCEPTED_STATUS,
                "root_native_combat_projection": _projection(100),
                "root_compact_state": _compact_state(power=float("nan")),
                "branches": {
                    branch_id: {
                        "ticks": [_tick(101, action=0x05)]
                    }
                    for branch_id in ("a1", "a2", "b")
                },
            },
        }

        with self.assertRaisesRegex(
            NativeCombatBranchReportError,
            "power must be finite and nonnegative",
        ):
            build_report(
                source,
                source_path="fixture.json",
                source_sha256="5" * 64,
            )

    def test_non_normal_active_shot_keeps_content_boundary_open(self) -> None:
        source = {
            "schema": ROLLING_SCHEMA,
            "result": {
                "status": ROLLING_ACCEPTED_STATUS,
                "root_native_combat_projection": _projection(100),
                "root_compact_state": _compact_state(),
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

    def test_unknown_shot_source_keeps_exact_provenance_open(self) -> None:
        source = {
            "schema": ROLLING_SCHEMA,
            "result": {
                "status": ROLLING_ACCEPTED_STATUS,
                "root_native_combat_projection": _projection(100),
                "root_compact_state": _compact_state(),
                "branches": {
                    branch_id: {
                        "ticks": [_tick(101, action=0x05)]
                    }
                    for branch_id in ("a1", "a2", "b")
                },
            },
        }
        root_summary = source["result"]["root_native_combat_projection"][
            "summary"
        ]
        root_summary["route2_exact_normal_source_active_shot_count"] = 2
        root_summary[
            "route2_non_normal_or_unknown_source_active_shot_count"
        ] = 1

        report = build_report(
            source,
            source_path="fixture.json",
            source_sha256="f" * 64,
        )

        self.assertTrue(
            all(
                row["candidate_status"]
                == (
                    "survival_filtered_proxy_only_"
                    "non_normal_or_unknown_shot_source"
                )
                for row in report["branches"]
            )
        )
        self.assertTrue(
            all(
                not row["authority"][
                    "route2_exact_normal_source_provenance"
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

    def test_causal_prefix_bomb_rejects_inherited_continuation(self) -> None:
        source = {
            "schema": CAUSAL_SEARCH_SCHEMA,
            "result": {
                "status": "causal_secondary_search_passed",
                "origin": {
                    "native_combat_projection": _projection(100),
                    "compact_state": _compact_state(),
                },
                "prefixes": [
                    {
                        "prefix_mask": 0x05,
                        "prefix_action_schedule": [0x07],
                        "prefix": {
                            "ticks": [_tick(101, action=0x05)]
                        },
                        "subroot": {
                            "native_combat_projection": _projection(101),
                            "compact_state": _compact_state(),
                        },
                        "continuations": [
                            {
                                "complete_mask": 0x05,
                                "ticks": [_tick(102, action=0x05)],
                            }
                        ],
                    }
                ],
            },
        }

        report = build_report(
            source,
            source_path="fixture.json",
            source_sha256="3" * 64,
        )

        self.assertEqual(report["survivor_count"], 2)
        self.assertEqual(report["route2_nmnb_eligible_count"], 0)
        self.assertTrue(
            all(
                row["candidate_status"] == "rejected_hard_no_bomb"
                and row["bomb_declared_action_fields"]
                == ["prefix_action_schedule[0]"]
                for row in report["branches"]
            )
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
