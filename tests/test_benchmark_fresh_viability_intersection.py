#!/usr/bin/env python3
"""Tests for cached-global/fresh-local contract replay."""

from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from benchmark_fresh_viability_intersection import main


class FreshViabilityIntersectionBenchmarkTests(unittest.TestCase):
    def test_main_replays_one_direct_action_contract_contradiction(
        self,
    ) -> None:
        row = {
            "kind": "decision",
            "frame": 100,
            "action": "stay",
            "snapshot_lag": 0,
            "control_delay_frames": 3,
            "control_delay_candidates": [3, 4, 5, 6],
            "action_hold_frames": 5,
            "minimum_clearance": -1.0,
            "player": {
                "x": 192.0,
                "y": 432.0,
                "phase": 0,
                "phase_at_action": 0,
            },
            "resources": {"power": 128.0, "bombs": 3.0},
            "input_snapshot": {"current": 0x05},
            "nearby_bullets": [
                [7, 160.0, 432.0, 4.0, 0.0, 2.0, 2.0, 0],
            ],
            "lasers": [],
            "enemy_bodies": [],
            "items": [],
            "terminal_threat": {
                "horizon_frames": 10,
                "collisions": 0,
            },
            "robust_control": {
                "worst_collisions": 1,
                "min_clearance": -1.0,
            },
            "corridor": {
                "viability": {
                    "available": True,
                    "state_viable": True,
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
                self.assertEqual(main([str(trace), str(output)]), 0)
            result = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(result["eligible_count"], 1)
        self.assertEqual(
            result["variants"]["enabled"]["fresh_prefix_relaxed_count"],
            1,
        )
        self.assertEqual(result["paired_hard_regression_count"], 0)


if __name__ == "__main__":
    unittest.main()
