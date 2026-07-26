#!/usr/bin/env python3
"""Focused regressions for the TH08 semantic input-clock shadow audit."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from analysis.th08_input_clock_audit import audit


def _write_trace(directory: str, rows: list[dict[str, object]]) -> Path:
    path = Path(directory) / "trace.jsonl"
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )
    return path


class Th08InputClockAuditTests(unittest.TestCase):
    def test_legacy_72_pulses_form_five_groups_including_terminal(
        self,
    ) -> None:
        rows: list[dict[str, object]] = []
        counts = ((4963, 4), (6763, 34), (21467, 6), (30128, 8), (45836, 20))
        for frame, count in counts:
            rows.extend(
                {
                    "kind": "auto_confirm_wall_pulse",
                    "frame": frame,
                    "stage_route_index": 3,
                }
                for _ in range(count)
            )
        rows.extend(
            (
                {
                    "kind": "scene_inactive",
                    "frame": 45836,
                    "stage_route_index": 3,
                    "status": "terminal_unload",
                },
                {
                    "kind": "summary",
                    "last_frame": 45836,
                    "termination_reason": "route_complete",
                },
            )
        )

        with TemporaryDirectory() as directory:
            report = audit(_write_trace(directory, rows))

        self.assertEqual(report["semantic_status"], "not_observable")
        self.assertEqual(report["wall_pulses"]["pulse_count"], 72)
        self.assertEqual(report["wall_pulses"]["group_count"], 5)
        self.assertEqual(
            report["wall_pulses"]["right_censored_positive_count"],
            1,
        )
        final_group = report["wall_pulses"]["groups"][-1]
        self.assertEqual(final_group["pulse_count"], 20)
        self.assertEqual(final_group["status"], "positive_right_censored")
        self.assertEqual(
            final_group["terminal_statuses"],
            ["route_complete", "terminal_unload"],
        )
        # Missing semantic rows in a legacy trace are unknown evidence, not a
        # perfect zero-false-positive result.
        self.assertIsNone(
            report["classification"]["false_positive_episode_count"]
        )
        self.assertIsNone(
            report["classification"]["false_negative_pulse_group_count"]
        )
        self.assertIsNone(report["classification"]["precision"])

    def test_semantic_episode_matches_pulse_and_keeps_input_roles_separate(
        self,
    ) -> None:
        start = {
            "frame": 100,
            "triggers": ["semantic_episode_boundary"],
            "frozen_seconds": 0.02,
            "repeat_poll_count": 2,
            "gameplay_epoch": 7,
            "held_desired_mask": 0x41,
            "delay_support": [0, 1],
            "role": "shadow_no_input_or_epoch_authority",
            "sample": {
                "input_after": {"current": 0x01},
                "native_manager_clock_blocked": True,
                "msg_state_after": 12,
                "frscreen_update_serial_after": 100,
                "capture_us": 300.0,
                "read_valid": True,
                "message_snapshot_stable": True,
                "frscreen_special_pause": False,
            },
        }
        current = {
            **start,
            "frame": 101,
            "frozen_seconds": 0.40,
            "repeat_poll_count": 9,
            "sample": {
                "input_after": {"current": 0x01},
                "native_manager_clock_blocked": False,
                "msg_state_after": -1,
                "frscreen_update_serial_after": 223,
            },
        }
        rows = [
            {"kind": "input_clock_shadow_observation", **start},
            {
                "kind": "input_clock_shadow_episode",
                "status": "begin",
                "episode_id": "message-1",
                "reason": "message_clock_gate_active",
                "frame": 100,
                "stage_route_index": 3,
                "pulse_count": 0,
                "held_desired_mask": 0x41,
                "delay_support": [0, 1],
                "role": "shadow_no_input_or_epoch_authority",
                "sample": start["sample"],
                "start": {
                    "physical_frame": 100,
                    "semantic_active": True,
                    "active_input": 0x01,
                },
                "observation": {
                    "physical_frame": 100,
                    "semantic_active": True,
                    "active_input": 0x01,
                },
            },
            {
                "kind": "auto_confirm_wall_pulse",
                "frame": 100,
                "stage_route_index": 3,
                "held_desired_mask": 0x41,
                "input_clock_shadow_episode_id": "message-1",
                "input_clock_shadow": {
                    "input_after": {"current": 0x01},
                    "native_manager_clock_blocked": True,
                },
            },
            {
                "kind": "input_clock_shadow_episode",
                "status": "end",
                "episode_id": "message-1",
                "reason": "manager_frame_progressed",
                "frame": 101,
                "stage_route_index": 3,
                "pulse_count": 1,
                "duration_ns": 2_000_000_000,
                "displacement": 282.9,
                "held_desired_mask": 0x41,
                "sample": current["sample"],
                "start": {
                    "physical_frame": 100,
                    "semantic_active": True,
                    "active_input": 0x01,
                },
                "observation": {
                    "physical_frame": 101,
                    "semantic_active": False,
                    "active_input": 0x01,
                },
            },
            {
                "kind": "input_clock_shadow_observation",
                "frame": 200,
                "triggers": ["repeat_poll"],
                "frozen_seconds": 0.01,
                "repeat_poll_count": 1,
                "gameplay_epoch": 7,
                "held_desired_mask": 0x04,
                "delay_support": [],
                "role": "shadow_no_input_or_epoch_authority",
                "sample": {
                    "input_after": {"current": 0x04},
                    "native_manager_clock_blocked": False,
                    "msg_state_after": -1,
                },
            },
        ]

        with TemporaryDirectory() as directory:
            report = audit(_write_trace(directory, rows))

        self.assertEqual(report["semantic_status"], "observable")
        self.assertEqual(
            report["semantic_observations"]["observation_count"],
            2,
        )
        self.assertEqual(
            report["semantic_observations"][
                "message_clock_gate_active_counts"
            ],
            {"false": 1, "true": 1},
        )
        input_evidence = report["semantic_observations"]["input_evidence"]
        self.assertEqual(input_evidence["both_present_count"], 2)
        self.assertEqual(input_evidence["differing_count"], 1)
        self.assertEqual(
            input_evidence["pairs"],
            [
                {
                    "held_desired_mask": 4,
                    "native_input_current": 4,
                    "count": 1,
                },
                {
                    "held_desired_mask": 65,
                    "native_input_current": 1,
                    "count": 1,
                },
            ],
        )
        episode = report["semantic_episodes"]["episodes"][0]
        self.assertEqual(episode["status"], "ended")
        self.assertEqual(episode["duration_ns"], 2_000_000_000)
        self.assertEqual(episode["displacement"], 282.9)
        self.assertEqual(episode["frscreen_update_serial_delta"], 123)
        self.assertEqual(
            episode["start_observation"]["held_desired_mask"],
            0x41,
        )
        self.assertEqual(
            episode["start_observation"]["native_input_current"],
            0x01,
        )
        self.assertEqual(
            report["classification"]["true_positive_episode_count"],
            1,
        )
        self.assertEqual(
            report["classification"]["false_positive_episode_count"],
            0,
        )
        self.assertEqual(
            report["classification"]["false_negative_pulse_group_count"],
            0,
        )
        self.assertEqual(report["classification"]["precision"], 1.0)
        self.assertEqual(report["classification"]["recall"], 1.0)
        self.assertEqual(
            report["classification"]["reference_role"],
            "delayed_proxy_not_live_or_ground_truth",
        )
        self.assertEqual(
            report["semantic_observations"]["capture_us"]["median"],
            300.0,
        )
        self.assertEqual(
            report["semantic_observations"]["trigger_gate_counts"],
            {
                "repeat_poll": {"false": 1},
                "semantic_episode_boundary": {"true": 1},
            },
        )
        self.assertEqual(
            report["semantic_observations"]["trigger_frozen_seconds"][
                "semantic_episode_boundary"
            ]["true"]["minimum"],
            0.02,
        )

    def test_open_semantic_episode_is_censored_by_terminal_pulse(
        self,
    ) -> None:
        rows = [
            {
                "kind": "input_clock_shadow_episode",
                "status": "begin",
                "episode_id": 3,
                "reason": "message_clock_gate_active",
                "frame": 900,
                "stage_route_index": 3,
                "pulse_count": 0,
                "sample": {
                    "input_current": 0x04,
                    "message_clock_gate_active": True,
                },
            },
            {
                "kind": "auto_confirm_wall_pulse",
                "frame": 900,
                "stage_route_index": 3,
                "input_clock_shadow": {
                    "episode_id": 3,
                    "sample": {"input_current": 0x04},
                },
            },
            {
                "kind": "scene_inactive",
                "frame": 900,
                "stage_route_index": 3,
                "status": "terminal_unload",
            },
        ]
        with TemporaryDirectory() as directory:
            report = audit(_write_trace(directory, rows))

        self.assertEqual(
            report["semantic_episodes"]["episodes"][0]["status"],
            "inferred_censored",
        )
        self.assertEqual(
            report["classification"]["right_censored_true_positive_count"],
            1,
        )

    def test_same_frame_fallback_respects_episode_line_order(self) -> None:
        rows = [
            {
                "kind": "input_clock_shadow_episode",
                "status": "begin",
                "episode_id": "ended-before-pulse",
                "frame": 100,
                "stage_route_index": 3,
            },
            {
                "kind": "input_clock_shadow_episode",
                "status": "end",
                "episode_id": "ended-before-pulse",
                "frame": 100,
                "stage_route_index": 3,
            },
            {
                "kind": "input_clock_shadow_episode",
                "status": "begin",
                "episode_id": "active-at-pulse",
                "frame": 100,
                "stage_route_index": 3,
            },
            {
                "kind": "auto_confirm_wall_pulse",
                "frame": 100,
                "stage_route_index": 3,
            },
            {
                "kind": "input_clock_shadow_episode",
                "status": "end",
                "episode_id": "active-at-pulse",
                "frame": 101,
                "stage_route_index": 3,
            },
        ]
        with TemporaryDirectory() as directory:
            report = audit(_write_trace(directory, rows))

        self.assertEqual(
            report["classification"]["matches"][0]["episode_id"],
            "active-at-pulse",
        )
        self.assertEqual(
            report["classification"]["matches"][0]["method"],
            "same_frame",
        )


if __name__ == "__main__":
    unittest.main()
