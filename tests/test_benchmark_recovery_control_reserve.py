#!/usr/bin/env python3
"""Tests for retained empty-kernel control-reserve ablation."""

from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from benchmark_recovery_control_reserve import main


class RecoveryControlReserveBenchmarkTests(unittest.TestCase):
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
