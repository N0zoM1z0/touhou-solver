#!/usr/bin/env python3
"""Tests for retained safety-value action ablation."""

from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from benchmark_safety_value_replay import main


class SafetyValueReplayBenchmarkTests(unittest.TestCase):
    def test_main_compares_same_retained_decision(self) -> None:
        row = {
            "kind": "decision",
            "frame": 100,
            "hit_started": False,
            "snapshot_lag": 0,
            "control_delay_frames": 3,
            "control_delay_candidates": [3, 4, 5, 6],
            "action_hold_frames": 6,
            "player": {"x": 192.0, "y": 400.0},
            "resources": {"power": 128.0, "bombs": 3.0},
            "input_snapshot": {"current": 0x24},
            "nearby_bullets": [],
            "lasers": [],
            "enemy_bodies": [],
            "items": [],
            "spell": {"spell_id": 50},
            "corridor": {
                "viability": {
                    "safe_actions": [],
                    "repair_volumes": {},
                    "recovery_distances": {},
                    "position_error": 0.0,
                    "support_covers_current": True,
                },
                "safety_value": {
                    "guidance_active": True,
                    "best_actions": ["left"],
                    "state_value": -2.0,
                    "selected_action": "left",
                },
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
            result["action_changes"][0]["enabled"]["action"],
            "left",
        )


if __name__ == "__main__":
    unittest.main()
