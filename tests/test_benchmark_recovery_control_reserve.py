#!/usr/bin/env python3
"""Tests for retained empty-kernel control-reserve ablation."""

from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from benchmarks.benchmark_recovery_control_reserve import (
    _bullet_from_trace,
    _laser_from_trace,
    main,
)


class RecoveryControlReserveBenchmarkTests(unittest.TestCase):
    def test_legacy_exact_laser_replay_does_not_restore_horizon_drift(
        self,
    ) -> None:
        laser = _laser_from_trace(
            [
                100.0,
                200.0,
                0.0,
                0.0,
                80.0,
                4.0,
                7,
                80.0,
                16.0,
                16.0,
                0.0,
                1,
                12,
                0,
                0,
                0,
                0,
                120,
                0,
                0,
                0.0,
                0.75,
            ]
        )
        self.assertIsNotNone(laser.state)
        self.assertEqual(laser.uncertainty_per_frame, 0.0)

    def test_replay_retains_lightweight_piecewise_projection(self) -> None:
        bullet = _bullet_from_trace(
            [
                7,
                100.0,
                200.0,
                1.0,
                0.0,
                2.0,
                3.0,
                0,
                None,
                [
                    1.0,
                    0.0,
                    0x00100202,
                    0,
                    1,
                    [[5, 0.0, 0.0], [8, -1.0, 0.5]],
                    0.25,
                    0.5,
                ],
            ]
        )
        self.assertEqual(bullet.original_transform_flags, 0x00100202)
        self.assertEqual(bullet.callback_aux_state, 1)
        self.assertEqual(
            [
                (change.frame, change.velocity_x, change.velocity_y)
                for change in bullet.velocity_changes
            ],
            [(5, 0.0, 0.0), (8, -1.0, 0.5)],
        )
        self.assertEqual(bullet.trajectory_uncertainty_x, 0.25)
        self.assertEqual(bullet.trajectory_uncertainty_y, 0.5)

    def test_main_compares_same_retained_decision(self) -> None:
        row = {
            "kind": "decision",
            "frame": 100,
            "hit_started": False,
            "snapshot_lag": 0,
            "control_delay_frames": 3,
            "control_delay_candidates": [3, 4, 5, 6],
            "action_hold_frames": 6,
            "player": {"x": 8.0, "y": 424.0},
            "resources": {"power": 128.0, "bombs": 3.0},
            "input_snapshot": {"current": 0x24},
            "nearby_bullets": [],
            "lasers": [],
            "enemy_bodies": [],
            "items": [],
            "corridor": {
                "viability": {
                    "safe_actions": [],
                    "repair_volumes": {},
                    "recovery_distances": {
                        "stay": 226.0,
                        "down": 164.0,
                        "up_right_fast": 315.0,
                    },
                    "position_error": 0.0,
                    "support_covers_current": True,
                }
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            trace = Path(directory) / "trace.jsonl"
            output = Path(directory) / "result.json"
            trace.write_text(json.dumps(row) + "\n", encoding="utf-8")
            with redirect_stdout(StringIO()):
                self.assertEqual(
                    main([str(trace), str(output), "--samples", "1"]),
                    0,
                )
            result = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(result["sample_count"], 1)
        self.assertEqual(result["action_change_count"], 1)
        self.assertEqual(
            result["action_changes"][0]["disabled"],
            "down",
        )
        self.assertEqual(
            result["action_changes"][0]["enabled"],
            "up_right_fast",
        )


if __name__ == "__main__":
    unittest.main()
