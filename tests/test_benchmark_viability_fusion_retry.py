#!/usr/bin/env python3
"""Tests for retained stale-viability fusion retry ablation."""

from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from benchmark_viability_fusion_retry import main


class ViabilityFusionRetryBenchmarkTests(unittest.TestCase):
    def test_main_replays_the_same_contradicted_safe_mask(self) -> None:
        row = {
            "kind": "decision",
            "frame": 100,
            "snapshot_lag": 0,
            "control_delay_frames": 3,
            "control_delay_candidates": [3, 4, 5, 6],
            "action_hold_frames": 5,
            "minimum_clearance": -1.0,
            "player": {"x": 192.0, "y": 432.0},
            "resources": {"power": 128.0, "bombs": 3.0},
            "input_snapshot": {"current": 0x05},
            "nearby_bullets": [
                [7, 160.0, 432.0, 4.0, 0.0, 2.0, 2.0, 0],
            ],
            "lasers": [],
            "enemy_bodies": [],
            "items": [],
            "terminal_threat": {
                "horizon_frames": 32,
                "collisions": 1,
            },
            "robust_control": {"worst_collisions": 1},
            "corridor": {
                "viability": {
                    "safe_actions": ["stay", "down", "left"],
                    "repair_volumes": {
                        "stay": 10,
                        "down": 10,
                        "left": 10,
                    },
                    "recovery_distances": {},
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
            result["action_changes"][0]["enabled"],
            "up_right_fast",
        )


if __name__ == "__main__":
    unittest.main()
