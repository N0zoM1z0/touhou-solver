#!/usr/bin/env python3
"""Tests for streaming TH08 long-run progress summaries."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from th08_longrun_status import load_rows, summarize_progress


class Th08LongrunStatusTests(unittest.TestCase):
    def test_tracks_stage_deaths_resources_and_completion(self) -> None:
        status = summarize_progress(
            [
                {
                    "kind": "decision",
                    "frame": 10,
                    "stage_route_index": 0,
                    "resources": {"lives": 2.0, "bombs": 3.0, "power": 1.0},
                    "player": {"phase": 0},
                    "active_bullets": 1,
                    "active_lasers": 0,
                    "active_items": 0,
                    "action": "left",
                    "hit_started": False,
                    "auto_confirm": None,
                },
                {
                    "kind": "decision",
                    "frame": 5000,
                    "stage_route_index": 1,
                    "resources": {"lives": 2.0, "bombs": 0.0, "power": 80.0},
                    "player": {"phase": 2},
                    "active_bullets": 900,
                    "active_lasers": 1,
                    "active_items": 3,
                    "action": "right+deathbomb",
                    "hit_started": True,
                    "auto_confirm": "press",
                },
                {
                    "kind": "summary",
                    "termination_reason": "gameplay_ended",
                },
                {
                    "kind": "scene_inactive",
                    "frame": 4990,
                    "transition_from_stage": 0,
                    "expected_stage": 1,
                },
                {
                    "kind": "auto_confirm_transition_pulse",
                    "frame": 4990,
                },
                {
                    "kind": "scene_resumed",
                    "frame": 5000,
                    "stage_route_index": 1,
                    "expected_stage_matched": True,
                },
                {
                    "kind": "auto_confirm_wall_pulse",
                    "frame": 5000,
                },
            ]
        )
        self.assertTrue(status["complete"])
        self.assertEqual(status["termination_reason"], "gameplay_ended")
        self.assertEqual(status["hit_frames"], [5000])
        self.assertEqual(status["latest"]["stage_label"], "Stage 2")
        self.assertEqual(status["latest"]["resources"]["power"], 80.0)
        self.assertEqual(status["auto_confirm_events"], 3)
        self.assertEqual(
            [event["kind"] for event in status["scene_events"]],
            [
                "scene_inactive",
                "auto_confirm_transition_pulse",
                "scene_resumed",
            ],
        )
        self.assertEqual(
            [entry["stage_route_index"] for entry in status["stage_transitions"]],
            [0, 1],
        )

    def test_stream_loader_counts_corrupt_json_lines(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "trial.jsonl"
            path.write_text(
                json.dumps({"kind": "decision", "frame": 1})
                + "\n"
                + '{"kind": broken}\n',
                encoding="utf-8",
            )
            diagnostics: dict[str, int] = {}
            rows = list(load_rows(path, diagnostics))
        self.assertEqual(len(rows), 1)
        self.assertEqual(diagnostics["json_decode_errors"], 1)


if __name__ == "__main__":
    unittest.main()
