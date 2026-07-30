#!/usr/bin/env python3
"""Tests for first-hit-bounded natural Power-0 route evidence."""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from analysis.th08_power0_clean_prefix_audit import (
    EXPECTED_EXE_SHA256,
    Power0CleanPrefixAuditError,
    Power0RunInput,
    build_power0_clean_prefix_report,
)


def _write_json(path: Path, value: object) -> str:
    payload = json.dumps(value, sort_keys=True).encode("utf-8")
    path.write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> str:
    payload = b"".join(
        (json.dumps(row, sort_keys=True) + "\n").encode("utf-8")
        for row in rows
    )
    path.write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()


def _session(run_id: str) -> dict[str, object]:
    return {
        "schema": "th08-unattended-full-route-session-v1",
        "run_id": run_id,
        "status": "completed",
        "trial_accepted": True,
        "hard_no_bomb": True,
        "route_id": 2,
        "difficulty_index": 3,
        "expected_stage_sequence": [0, 1, 2, 3, 5, 7],
        "target": {
            "sha256": EXPECTED_EXE_SHA256,
            "runtime_patch": {"no_life_decrement": True},
        },
        "completion_scene": {"status": "terminal_unload"},
        "error_type": None,
    }


def _decision(
    frame: int,
    *,
    power: int,
    items: list[list[object]],
    hit_started: bool = False,
    item_objectives_enabled: bool = False,
) -> dict[str, object]:
    return {
        "kind": "decision",
        "frame": frame,
        "stage_route_index": 0,
        "gameplay_epoch": 0,
        "hit_started": hit_started,
        "hit_count": int(hit_started),
        "mask": 0x05,
        "bomb": False,
        "planner_objective": {
            "item_objectives_enabled": item_objectives_enabled,
        },
        "predicted_collections": [],
        "item_utility": 0.0,
        "resources": {"power": float(power), "lives": 2.0, "bombs": 3.0},
        "items": items,
        "active_items": len(items),
        "player": {"projected_x": 100.0, "projected_y": 100.0},
        "focused": True,
        "robust_control": {"viability_safe_action_count": 3},
    }


def _trace_rows(*decisions: dict[str, object]) -> list[dict[str, object]]:
    return [
        {
            "kind": "identity",
            "sha256": EXPECTED_EXE_SHA256,
            "runtime_patch": {"no_life_decrement": True},
        },
        {
            "kind": "controller_config",
            "bomb_policy": "disabled",
            "item_policy": "survival_only_passive_collection",
        },
        {
            "kind": "runtime_ecl_identity",
            "route_id": 2,
            "difficulty_index": 3,
            "stage_route_index": 0,
        },
        *decisions,
    ]


def _input(
    directory: Path,
    run_id: str,
    decisions: list[dict[str, object]],
) -> Power0RunInput:
    trace = directory / f"{run_id}.jsonl"
    session = directory / f"{run_id}.session.json"
    trace_sha256 = _write_jsonl(trace, _trace_rows(*decisions))
    session_sha256 = _write_json(session, _session(run_id))
    return Power0RunInput(trace, session, trace_sha256, session_sha256)


class Power0CleanPrefixAuditTests(unittest.TestCase):
    def test_report_stops_before_hit_and_keeps_pickup_source_unverified(self) -> None:
        power_item = [4, 110.0, 100.0, 0.0, 0.0, 0, 1, False]
        with TemporaryDirectory() as directory_name:
            directory = Path(directory_name)
            first = _input(
                directory,
                "first",
                [
                    _decision(1, power=0, items=[power_item]),
                    _decision(3, power=1, items=[]),
                    _decision(5, power=1, items=[], hit_started=True),
                    _decision(7, power=128, items=[]),
                ],
            )
            second = _input(
                directory,
                "second",
                [
                    _decision(1, power=0, items=[power_item]),
                    _decision(2, power=0, items=[power_item]),
                    _decision(4, power=0, items=[], hit_started=True),
                ],
            )
            report = build_power0_clean_prefix_report((first, second))
            repeated = build_power0_clean_prefix_report((first, second))

        self.assertEqual(report, repeated)
        first_report = report["traces"][0]
        self.assertEqual(first_report["clean_decision_count"], 2)
        self.assertEqual(first_report["last_clean_power"], 1)
        self.assertEqual(first_report["post_hit_rows_used"], 0)
        event = first_report["observed_power_gain_events"][0]
        self.assertEqual(event["delta"], 1)
        self.assertEqual(
            event["source_classification"],
            "single_visible_disappeared_small_power_candidate",
        )
        self.assertFalse(event["verified_item_source"])
        self.assertEqual(first_report["shot_threshold_crossings"], [])
        self.assertFalse(
            report["classification"][
                "survival_feasible_collection_policy_gate_passed"
            ]
        )
        self.assertEqual(
            report["comparison"]["power_at_or_before_common_frame"],
            {"first": 1, "second": 0},
        )

    def test_enabled_item_objective_fails_closed(self) -> None:
        with TemporaryDirectory() as directory_name:
            directory = Path(directory_name)
            bad = _input(
                directory,
                "bad",
                [
                    _decision(
                        1,
                        power=0,
                        items=[],
                        item_objectives_enabled=True,
                    ),
                    _decision(2, power=0, items=[], hit_started=True),
                ],
            )
            good = _input(
                directory,
                "good",
                [
                    _decision(1, power=0, items=[]),
                    _decision(2, power=0, items=[], hit_started=True),
                ],
            )
            with self.assertRaises(Power0CleanPrefixAuditError):
                build_power0_clean_prefix_report((bad, good))


if __name__ == "__main__":
    unittest.main()
