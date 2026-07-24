#!/usr/bin/env python3
"""Tests for the read-only boss-alignment strategy audit."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from th08_attack_alignment_audit import build_report


class Th08AttackAlignmentAuditTests(unittest.TestCase):
    def test_audit_separates_shot_held_from_boss_alignment(self) -> None:
        rows = (
            {"kind": "controller_config"},
            {
                "kind": "decision",
                "frame": 100,
                "mask": 1,
                "input_snapshot": {"current": 1},
                "hit_started": False,
                "player": {"x": 100.0, "phase": 3},
                "resources": {"power": 128.0},
                "spell": {"active": True, "spell_id": 57, "name": "test"},
                "spell_enemy_body_guard": {
                    "body": [0x1234, 120.0, 80.0]
                },
                "boss_phase": {
                    "pointer": 0x1234,
                    "stable": True,
                    "frame_damage": 0,
                },
                "boss_phase_progress": {
                    "status": "initial",
                    "damageable": True,
                },
                "damage_objective": {
                    "available": True,
                    "baseline_action": "stay",
                    "shadow_action": "right",
                    "live_selected": False,
                    "current_alignment_cost": 20.0,
                    "shadow_alignment_cost": 12.0,
                },
            },
            {
                "kind": "decision",
                "frame": 104,
                "mask": 1,
                "input_snapshot": {"current": 1},
                "hit_started": True,
                "player": {"x": 200.0, "phase": 3},
                "resources": {"power": 96.0},
                "spell": {"active": True, "spell_id": 57, "name": "test"},
                "spell_enemy_body_guard": {
                    "body": [0x1234, 120.0, 80.0]
                },
                "boss_phase": {
                    "pointer": 0x1234,
                    "stable": True,
                    "frame_damage": 60,
                },
                "boss_phase_progress": {
                    "status": "comparable",
                    "damageable": True,
                    "health_delta": 60,
                    "frame_delta": 4,
                },
                "damage_objective": {
                    "available": True,
                    "baseline_action": "right",
                    "shadow_action": "right",
                    "live_selected": False,
                    "current_alignment_cost": 0.0,
                    "shadow_alignment_cost": 0.0,
                },
            },
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trace.jsonl"
            path.write_text(
                "".join(json.dumps(row) + "\n" for row in rows),
                encoding="utf-8",
            )
            report = build_report((path,))
        trace = report["traces"][0]
        phase = trace["phases"][0]
        self.assertEqual(trace["output_shot_fraction"], 1.0)
        self.assertEqual(trace["active_shot_fraction"], 1.0)
        self.assertEqual(phase["hit_count"], 1)
        self.assertEqual(
            phase["normal_horizontal_alignment_error"]["median"],
            50.0,
        )
        self.assertEqual(phase["normal_alignment_fraction"]["16"], 0.0)
        self.assertEqual(phase["normal_alignment_fraction"]["32"], 0.5)
        self.assertEqual(phase["power"]["first"], 128.0)
        self.assertEqual(phase["power"]["last"], 96.0)
        self.assertEqual(
            phase["native_boss_telemetry"]["observed_damage_per_frame"],
            15.0,
        )
        self.assertEqual(
            phase["safe_damage_objective"]["shadow_action_change_count"],
            1,
        )


if __name__ == "__main__":
    unittest.main()
