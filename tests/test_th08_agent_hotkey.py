#!/usr/bin/env python3
"""Tests for the prewarmed manual-to-agent handoff policy."""

from __future__ import annotations

import unittest
from pathlib import Path

from th08_agent_hotkey import (
    LONG_RUN_DURATION_SECONDS,
    build_long_run_arguments,
    one_shot_trial_finished,
)
from th08_live_dodge_agent import build_parser


class AgentHotkeyTests(unittest.TestCase):
    def test_f8_long_run_does_not_stop_at_the_first_hit(self) -> None:
        arguments = build_long_run_arguments(
            output=Path("trial.jsonl"),
            stop_file=Path("trial.stop"),
            pid=1234,
            difficulty=3,
            expected_stage=2,
            terminal_stage=2,
        )
        parsed = build_parser().parse_args(arguments)
        self.assertEqual(parsed.duration, LONG_RUN_DURATION_SECONDS)
        self.assertEqual(parsed.stop_after_hits, 0)
        self.assertEqual(parsed.post_hit_frames, 0)
        self.assertEqual(parsed.auto_confirm_every, 15)
        self.assertEqual(parsed.auto_confirm_idle_frames, 20)
        self.assertTrue(parsed.no_bomb)
        self.assertFalse(parsed.normal_bomb)
        self.assertTrue(parsed.armed)
        self.assertEqual(parsed.expected_stage, 2)
        self.assertEqual(parsed.terminal_stage, 2)
        self.assertFalse(parsed.trace_transform_runtime)

    def test_transform_runtime_trace_is_explicitly_opt_in(self) -> None:
        arguments = build_long_run_arguments(
            output=Path("trial.jsonl"),
            stop_file=Path("trial.stop"),
            pid=1234,
            difficulty=3,
            trace_transform_runtime=True,
        )
        parsed = build_parser().parse_args(arguments)
        self.assertTrue(parsed.trace_transform_runtime)

    def test_completed_trial_exits_before_a_second_f8_can_rearm(self) -> None:
        self.assertFalse(
            one_shot_trial_finished(agent_started=False, agent_alive=False)
        )
        self.assertFalse(
            one_shot_trial_finished(agent_started=True, agent_alive=True)
        )
        self.assertTrue(
            one_shot_trial_finished(agent_started=True, agent_alive=False)
        )


if __name__ == "__main__":
    unittest.main()
