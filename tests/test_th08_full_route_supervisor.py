#!/usr/bin/env python3
"""Regression for the unattended full-route completion boundary."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from th08_full_route_supervisor import _terminal_scene_record


class FullRouteSupervisorTests(unittest.TestCase):
    def test_terminal_unload_precedes_route_complete_summary(self) -> None:
        with TemporaryDirectory() as temporary:
            trace = Path(temporary) / "trial.jsonl"
            rows = [
                {
                    "kind": "scene_inactive",
                    "frame": 226864,
                    "engine_flags": 109072,
                    "stage_route_index": 7,
                    "transition_from_stage": 7,
                    "expected_stage": None,
                    "status": "terminal_unload",
                },
                {
                    "kind": "summary",
                    "last_frame": 226864,
                    "termination_reason": "route_complete",
                },
            ]
            trace.write_text(
                "".join(json.dumps(row) + "\n" for row in rows),
                encoding="utf-8",
            )
            completion = _terminal_scene_record(trace)
        self.assertEqual(completion["frame"], 226864)
        self.assertEqual(completion["engine_flags"], 109072)


if __name__ == "__main__":
    unittest.main()
