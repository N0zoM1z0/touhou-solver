#!/usr/bin/env python3
"""Tests for fail-closed lifecycle trace lowering."""

from __future__ import annotations

import unittest

from analysis.th08_enemy_lifecycle_trace_audit import (
    audit_lifecycle_trace_rows,
)
from th08_runtime.enemy_lifecycle_probe import (
    ENEMY_POOL_BASE,
    ENEMY_STRIDE,
    FORCED_ZERO_RETURN_OPCODE_5F,
    PROBE_SCHEMA,
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
) -> dict[str, object]:
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
                _event(1, "allocate_timeline"),
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
