#!/usr/bin/env python3
"""Tests for the prewarmed manual-to-agent handoff policy."""

from __future__ import annotations

import unittest
from pathlib import Path

from th08_agent_hotkey import (
    LONG_RUN_DURATION_SECONDS,
    build_long_run_arguments,
)
from th08_live_dodge_agent import build_parser


class AgentHotkeyTests(unittest.TestCase):
    def test_f8_long_run_does_not_stop_at_the_first_hit(self) -> None:
        arguments = build_long_run_arguments(
            output=Path("trial.jsonl"),
            stop_file=Path("trial.stop"),
            pid=1234,
            difficulty=3,
        )
        parsed = build_parser().parse_args(arguments)
        self.assertEqual(parsed.duration, LONG_RUN_DURATION_SECONDS)
        self.assertEqual(parsed.stop_after_hits, 0)
        self.assertEqual(parsed.post_hit_frames, 0)
        self.assertEqual(parsed.auto_confirm_every, 15)
        self.assertEqual(parsed.auto_confirm_idle_frames, 20)
        self.assertTrue(parsed.armed)


if __name__ == "__main__":
    unittest.main()
