#!/usr/bin/env python3
"""Tests for fail-closed lifecycle trace lowering."""

from __future__ import annotations

from pathlib import Path
import unittest

from analysis.th08_enemy_lifecycle_trace_audit import (
    audit_lifecycle_trace_rows,
    join_candidate_board,
)
from th08_runtime.enemy_lifecycle_probe import (
    ENEMY_POOL_BASE,
    ENEMY_STRIDE,
    FORCED_ZERO_RETURN_OPCODE_5F,
    ITEM_POOL_BASE,
    ITEM_STRIDE,
    PROBE_SCHEMA,
)


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_BOARD = (
    ROOT
    / "artifacts"
    / "runtime_reports"
    / "th08_route2_combat_resource_candidate_board_20260731.json"
)


def _event(
    serial: int,
    kind: str,
    *,
    slot: int = 3,
    frame: int = 100,
    flags_before: int = 1,
    flags_after: int = 1,
    hp_before: int = 20,
    hp_after: int = 20,
    frame_damage: int = 0,
    caller: int | None = None,
    root_subroutine: int | None = None,
    stage_route_index: int = 5,
) -> dict[str, object]:
    encoded_root = (
        root_subroutine
        if root_subroutine is not None
        else (7 if kind.startswith("allocate_") else None)
    )
    return {
        "serial": serial,
        "manager_frame": frame,
        "kind": kind,
        "slot": slot,
        "enemy_pointer": ENEMY_POOL_BASE + slot * ENEMY_STRIDE,
        "flags_before": flags_before,
        "flags_after": flags_after,
        "hp_before": hp_before,
        "hp_after": hp_after,
        "frame_damage": frame_damage,
        "caller_return_address": caller,
        "root_subroutine": encoded_root,
        "stage_route_index": stage_route_index,
    }


def _item_event(
    serial: int,
    kind: str,
    *,
    slot: int = 4,
    frame: int = 100,
    item_type: int = 0,
    power_before: float = 7.0,
    power_after: float = 7.0,
    caller: int | None = None,
    source_enemy_pointer: int | None = None,
    stage_route_index: int = 5,
) -> dict[str, object]:
    rng = {"state": 0x1234, "calls": 200}
    return {
        "serial": serial,
        "manager_frame": frame,
        "kind": kind,
        "stage_route_index": stage_route_index,
        "item_slot": slot,
        "item_pointer": ITEM_POOL_BASE + slot * ITEM_STRIDE,
        "item_type": item_type,
        "motion_state": 1,
        "full_value": False,
        "item_position": {"x": 100.0, "y": 80.0},
        "item_velocity": {"x": 0.5, "y": -1.0},
        "player_position": {"x": 104.0, "y": 84.0},
        "player_state": 0,
        "focus_logic": 1,
        "input_current": 0x10,
        "resources_before": {
            "power": power_before,
            "lives": 2.0,
            "bombs": 3.0,
        },
        "resources_after": {
            "power": power_after,
            "lives": 2.0,
            "bombs": 3.0,
        },
        "rng_before": rng if kind == "item_pickup" else None,
        "rng_after": rng if kind in {"item_allocate", "item_pickup"} else None,
        "caller_return_address": caller,
        "active_previous_pointer": None,
        "source_enemy_pointer": source_enemy_pointer,
        "allocation_next_index": 5 if kind == "item_allocate" else None,
    }


def _batch(
    status: str,
    previous: int | None,
    observed: int | None,
    events: list[dict[str, object]] | None = None,
    *,
    dropped: int = 0,
    error: str | None = None,
) -> dict[str, object]:
    return {
        "schema": PROBE_SCHEMA,
        "role": "trace_only_no_action_authority",
        "status": status,
        "previous_serial": previous,
        "observed_serial": observed,
        "events": events or [],
        "dropped_event_count": dropped,
        "error": error,
        "action_authority": False,
    }


def _rows(
    captures: list[dict[str, object]],
    *,
    baseline_serial: int = 0,
    final: dict[str, object] | None = None,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = [
        {
            "kind": "controller_config",
            "enemy_lifecycle_probe": {"status": "installed"},
        },
        {
            "kind": "enemy_lifecycle_probe_baseline",
            **_batch("baseline", None, baseline_serial),
        },
    ]
    rows.extend(
        {
            "kind": "decision",
            "enemy_lifecycle_probe": {
                "installation_status": "installed",
                "capture": capture,
                "action_authority": False,
            },
        }
        for capture in captures
    )
    if final is not None:
        rows.append({"kind": "enemy_lifecycle_probe_final", **final})
    return rows


class EnemyLifecycleTraceAuditTests(unittest.TestCase):
    def test_exact_generations_distinguish_forced_zero_and_lethal_damage(
        self,
    ) -> None:
        first = _batch(
            "exact",
            0,
            3,
            [
                _event(1, "allocate_timeline", root_subroutine=7),
                _event(
                    2,
                    "forced_hp_zero",
                    frame=110,
                    hp_before=10,
                    hp_after=0,
                    caller=FORCED_ZERO_RETURN_OPCODE_5F,
                ),
                _event(
                    3,
                    "retire_defeat_mode0",
                    frame=110,
                    flags_after=0,
                    hp_before=0,
                    hp_after=0,
                ),
            ],
        )
        second = _batch(
            "exact",
            3,
            5,
            [
                _event(
                    4,
                    "allocate_inherited_registers",
                    frame=120,
                    hp_before=5,
                    hp_after=5,
                    root_subroutine=19,
                ),
                _event(
                    5,
                    "retire_defeat_mode0",
                    frame=130,
                    flags_after=0,
                    hp_before=-2,
                    hp_after=-2,
                    frame_damage=7,
                ),
            ],
        )
        report = audit_lifecycle_trace_rows(
            _rows(
                [first, second],
                final=_batch("no_events", 5, 5),
            )
        )

        self.assertTrue(
            report["authority"]["generation_stream_complete"]
        )
        self.assertEqual(report["accepted_prefix_event_count"], 5)
        self.assertEqual(report["summary"]["completed_lifetime_count"], 2)
        self.assertEqual(
            report["summary"]["end_reason_counts"],
            {
                "forced_hp_zero_defeat": 1,
                "player_shot_lethal_damage": 1,
            },
        )
        self.assertEqual(
            report["summary"]["verified_player_shot_kill_count"],
            1,
        )
        self.assertEqual(
            [
                lifetime["observed_generation_index"]
                for lifetime in report["lifetimes"]
            ],
            [1, 2],
        )
        self.assertEqual(
            [lifetime["root_subroutine"] for lifetime in report["lifetimes"]],
            [7, 19],
        )
        self.assertEqual(
            report["summary"]["observed_root_subroutine_counts"],
            {"7": 1, "19": 1},
        )
        self.assertEqual(
            report["summary"]["observed_program_counts"],
            {"stage-5:root-7": 1, "stage-5:root-19": 1},
        )
        self.assertTrue(
            report["authority"]["accepted_allocation_root_identity_exact"]
        )
        self.assertTrue(
            report["authority"]["accepted_program_identity_exact"]
        )

    def test_transient_read_error_is_recovered_by_later_exact_batch(
        self,
    ) -> None:
        report = audit_lifecycle_trace_rows(
            _rows(
                [
                    _batch(
                        "read_error",
                        0,
                        None,
                        error="temporary",
                    ),
                    _batch(
                        "exact",
                        0,
                        2,
                        [
                            _event(1, "allocate_timeline"),
                            _event(
                                2,
                                "retire_main_vm",
                                flags_after=0,
                            ),
                        ],
                    ),
                ],
                final=_batch("no_events", 2, 2),
            )
        )

        self.assertTrue(
            report["serial_chain"]["continuous_after_baseline"]
        )
        self.assertFalse(
            report["serial_chain"]["pending_nonadvancing_read"]
        )
        self.assertEqual(
            report["serial_chain"]["status_counts"]["read_error"],
            1,
        )
        self.assertTrue(
            report["authority"]["generation_stream_complete"]
        )

    def test_overflow_retains_only_the_exact_prefix(self) -> None:
        report = audit_lifecycle_trace_rows(
            _rows(
                [
                    _batch(
                        "exact",
                        0,
                        2,
                        [
                            _event(1, "allocate_timeline"),
                            _event(
                                2,
                                "retire_offscreen_cull",
                                flags_after=0,
                            ),
                        ],
                    ),
                    _batch(
                        "overflow_or_trace_truncation",
                        2,
                        8,
                        [_event(8, "allocate_timeline", slot=4)],
                        dropped=5,
                    ),
                ],
                final=_batch("no_events", 8, 8),
            )
        )

        self.assertFalse(
            report["authority"]["generation_stream_complete"]
        )
        self.assertEqual(report["accepted_prefix_event_count"], 2)
        self.assertEqual(report["summary"]["completed_lifetime_count"], 1)
        self.assertEqual(
            report["serial_chain"]["irrecoverable_gap"]["reason"],
            "overflow_or_trace_truncation",
        )

    def test_uint32_wrap_preserves_exact_serial_order(self) -> None:
        report = audit_lifecycle_trace_rows(
            _rows(
                [
                    _batch(
                        "exact",
                        0xFFFFFFFF,
                        1,
                        [
                            _event(0, "allocate_timeline"),
                            _event(
                                1,
                                "retire_initial_vm_timeline",
                                flags_after=0,
                            ),
                        ],
                    )
                ],
                baseline_serial=0xFFFFFFFF,
                final=_batch("no_events", 1, 1),
            )
        )

        self.assertTrue(
            report["authority"]["generation_stream_complete"]
        )
        self.assertFalse(
            report["serial_chain"]["prefix_complete_from_install"]
        )
        self.assertEqual(report["accepted_prefix_event_count"], 2)

    def test_missing_allocation_is_retained_as_partial_start(self) -> None:
        report = audit_lifecycle_trace_rows(
            _rows(
                [
                    _batch(
                        "exact",
                        7,
                        8,
                        [
                            _event(
                                8,
                                "retire_main_vm",
                                flags_after=0,
                            )
                        ],
                    )
                ],
                baseline_serial=7,
                final=_batch("no_events", 8, 8),
            )
        )

        self.assertTrue(
            report["authority"]["generation_stream_complete"]
        )
        self.assertEqual(report["summary"]["partial_start_lifetime_count"], 1)
        self.assertFalse(report["lifetimes"][0]["start_observed"])
        self.assertIsNone(report["lifetimes"][0]["root_subroutine"])
        self.assertEqual(
            report["lifetimes"][0]["end_classification"]["reason"],
            "scripted_main_vm_end",
        )

    def test_malformed_event_invalidates_its_entire_batch(self) -> None:
        bad = _event(2, "retire_main_vm", flags_after=0)
        bad["enemy_pointer"] = ENEMY_POOL_BASE
        report = audit_lifecycle_trace_rows(
            _rows(
                [
                    _batch(
                        "exact",
                        0,
                        2,
                        [
                            _event(1, "allocate_timeline"),
                            bad,
                        ],
                    )
                ],
                final=_batch("no_events", 2, 2),
            )
        )

        self.assertEqual(report["accepted_prefix_event_count"], 0)
        self.assertEqual(report["summary"]["lifetime_count"], 0)
        self.assertEqual(
            report["serial_chain"]["irrecoverable_gap"]["reason"],
            "invalid_event",
        )

    def test_allocation_without_root_identity_invalidates_its_batch(self) -> None:
        allocation = _event(1, "allocate_timeline")
        allocation["root_subroutine"] = None
        report = audit_lifecycle_trace_rows(
            _rows(
                [
                    _batch(
                        "exact",
                        0,
                        1,
                        [allocation],
                    )
                ],
                final=_batch("no_events", 1, 1),
            )
        )

        self.assertEqual(report["accepted_prefix_event_count"], 0)
        self.assertEqual(
            report["serial_chain"]["irrecoverable_gap"]["reason"],
            "invalid_event",
        )

    def test_lifetime_cannot_cross_native_stage_route_identity(self) -> None:
        report = audit_lifecycle_trace_rows(
            _rows(
                [
                    _batch(
                        "exact",
                        0,
                        2,
                        [
                            _event(
                                1,
                                "allocate_timeline",
                                stage_route_index=5,
                            ),
                            _event(
                                2,
                                "retire_main_vm",
                                flags_after=0,
                                stage_route_index=7,
                            ),
                        ],
                    )
                ],
                final=_batch("no_events", 2, 2),
            )
        )

        self.assertFalse(
            report["authority"]["generation_stream_complete"]
        )
        self.assertIn(
            "changes stage-route index",
            report["serial_chain"]["errors"][-1],
        )

    def test_exact_program_identity_joins_the_immutable_candidate_board(
        self,
    ) -> None:
        report = audit_lifecycle_trace_rows(
            _rows(
                [
                    _batch(
                        "exact",
                        0,
                        3,
                        [
                            _event(
                                1,
                                "allocate_timeline",
                                root_subroutine=2,
                                stage_route_index=5,
                            ),
                            _event(
                                2,
                                "retire_main_vm",
                                flags_after=0,
                                stage_route_index=5,
                            ),
                            _event(
                                3,
                                "allocate_timeline",
                                root_subroutine=7,
                                stage_route_index=5,
                            ),
                        ],
                    )
                ],
                final=_batch("no_events", 3, 3),
            )
        )
        joined = join_candidate_board(report, CANDIDATE_BOARD)

        self.assertEqual(joined["summary"]["matched_lifetime_count"], 1)
        self.assertEqual(
            joined["matched_lifetimes"][0]["candidate_id"],
            "ecldata5.ecl:root:2",
        )
        self.assertIn(
            "ordinary_emitter_configured_extra_power",
            joined["matched_lifetimes"][0]["candidate_families"],
        )
        self.assertEqual(
            joined["unmatched_programs"],
            [
                {
                    "stage_route_index": 5,
                    "root_subroutine": 7,
                    "lifetime_count": 1,
                    "reason": "program_not_timeline_rooted_in_candidate_board",
                }
            ],
        )
        self.assertTrue(
            joined["authority"]["matched_program_identity_exact"]
        )
        self.assertFalse(joined["authority"]["candidate_benefit_verified"])

    def test_item_allocation_pickup_and_enemy_owner_join_are_exact(self) -> None:
        enemy_pointer = ENEMY_POOL_BASE + 3 * ENEMY_STRIDE
        report = audit_lifecycle_trace_rows(
            _rows(
                [
                    _batch(
                        "exact",
                        0,
                        4,
                        [
                            _event(
                                1,
                                "allocate_timeline",
                                root_subroutine=2,
                            ),
                            _item_event(
                                2,
                                "item_allocate",
                                caller=0x0042BF0B,
                                source_enemy_pointer=enemy_pointer,
                            ),
                            _event(
                                3,
                                "retire_defeat_mode0",
                                flags_after=0,
                                hp_before=0,
                                hp_after=0,
                            ),
                            _item_event(
                                4,
                                "item_pickup",
                                power_before=7.0,
                                power_after=8.0,
                            ),
                        ],
                    )
                ],
                final=_batch("no_events", 4, 4),
            )
        )

        self.assertEqual(report["summary"]["item_generation_count"], 1)
        self.assertEqual(report["summary"]["item_pickup_count"], 1)
        self.assertEqual(
            report["summary"]["defeat_item_generation_join_count"],
            1,
        )
        self.assertEqual(
            report["summary"]["power_threshold_crossing_count"],
            1,
        )
        item = report["item_generations"][0]
        self.assertEqual(
            item["source_enemy_generation_key"],
            "slot-3:observed-1",
        )
        self.assertEqual(
            item["pickup_transaction"]["resource_delta"]["power"],
            1.0,
        )
        self.assertEqual(
            item["pickup_transaction"]["power_thresholds_crossed"],
            [8],
        )
        self.assertTrue(
            report["authority"]["accepted_item_generation_identity_exact"]
        )
        joined = join_candidate_board(report, CANDIDATE_BOARD)
        self.assertEqual(
            joined["summary"]["matched_lifetime_item_allocation_count"],
            1,
        )
        self.assertEqual(
            joined["summary"]["matched_lifetime_item_pickup_count"],
            1,
        )
        self.assertEqual(
            joined["summary"]["matched_lifetime_power_delta"],
            1.0,
        )
        self.assertEqual(
            joined["matched_lifetimes"][0][
                "observed_power_thresholds_crossed"
            ],
            [8],
        )

    def test_item_cull_closes_generation_before_slot_reuse(self) -> None:
        report = audit_lifecycle_trace_rows(
            _rows(
                [
                    _batch(
                        "exact",
                        0,
                        3,
                        [
                            _item_event(
                                1,
                                "item_allocate",
                                caller=0x00417622,
                            ),
                            _item_event(2, "item_cull"),
                            _item_event(
                                3,
                                "item_allocate",
                                caller=0x00417622,
                            ),
                        ],
                    )
                ],
                final=_batch("no_events", 3, 3),
            )
        )

        self.assertEqual(report["summary"]["item_generation_count"], 2)
        self.assertEqual(report["summary"]["item_cull_count"], 1)
        self.assertFalse(report["serial_chain"]["errors"])

    def test_final_read_failure_leaves_stream_incomplete(self) -> None:
        report = audit_lifecycle_trace_rows(
            _rows(
                [],
                final=_batch(
                    "race_unknown",
                    0,
                    None,
                    error="unstable",
                ),
            )
        )

        self.assertTrue(report["final_batch_present"])
        self.assertTrue(
            report["serial_chain"]["pending_nonadvancing_read"]
        )
        self.assertFalse(
            report["authority"]["generation_stream_complete"]
        )


if __name__ == "__main__":
    unittest.main()
