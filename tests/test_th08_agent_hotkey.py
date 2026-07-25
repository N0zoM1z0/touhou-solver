#!/usr/bin/env python3
"""Tests for the prewarmed manual-to-agent handoff policy."""

from __future__ import annotations

import unittest
from tempfile import TemporaryDirectory
from pathlib import Path

from th08_agent_hotkey import (
    LONG_RUN_DURATION_SECONDS,
    build_long_run_arguments,
    one_shot_trial_finished,
    read_runtime_summary,
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
        self.assertEqual(parsed.safety_value_horizon, 0)
        self.assertIsNone(parsed.viability_audit_dir)
        self.assertFalse(parsed.postpublished_survival_shadow)
        self.assertFalse(parsed.pipeline_prewarm_shadow)
        self.assertFalse(parsed.candidate_verifier_shadow)

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

    def test_full_route_can_extend_the_worker_deadline(self) -> None:
        arguments = build_long_run_arguments(
            output=Path("trial.jsonl"),
            stop_file=Path("trial.stop"),
            pid=1234,
            difficulty=3,
            duration_seconds=4500.0,
        )
        parsed = build_parser().parse_args(arguments)
        self.assertEqual(parsed.duration, 4500.0)

    def test_full_route_summary_reads_only_the_terminal_contract(self) -> None:
        with TemporaryDirectory() as temporary:
            trace = Path(temporary) / "trial.jsonl"
            trace.write_text(
                '{"kind":"decision","frame":2}\n'
                '{"kind":"summary","last_frame":225973,'
                '"counter_gaps":4,"hit_count":9,'
                '"termination_reason":"route_complete"}\n',
                encoding="utf-8",
            )
            summary = read_runtime_summary(trace)
        self.assertEqual(summary["last_frame"], 225973)
        self.assertEqual(summary["hit_count"], 9)
        self.assertEqual(summary["termination_reason"], "route_complete")

    def test_safety_value_fallback_is_explicitly_opt_in(self) -> None:
        arguments = build_long_run_arguments(
            output=Path("trial.jsonl"),
            stop_file=Path("trial.stop"),
            pid=1234,
            difficulty=3,
            safety_value_horizon=32,
        )
        parsed = build_parser().parse_args(arguments)
        self.assertEqual(parsed.safety_value_horizon, 32)

    def test_viability_audit_capsules_are_explicitly_opt_in(self) -> None:
        arguments = build_long_run_arguments(
            output=Path("trial.jsonl"),
            stop_file=Path("trial.stop"),
            pid=1234,
            difficulty=3,
            viability_audit_dir=Path("audit-capsules"),
        )
        parsed = build_parser().parse_args(arguments)
        self.assertEqual(
            parsed.viability_audit_dir,
            Path("audit-capsules"),
        )

    def test_postpublished_survival_shadow_is_explicitly_opt_in(self) -> None:
        arguments = build_long_run_arguments(
            output=Path("trial.jsonl"),
            stop_file=Path("trial.stop"),
            pid=1234,
            difficulty=3,
            postpublished_survival_shadow=True,
        )
        parsed = build_parser().parse_args(arguments)
        self.assertTrue(parsed.postpublished_survival_shadow)

    def test_pipeline_prewarm_shadow_is_explicitly_opt_in(self) -> None:
        arguments = build_long_run_arguments(
            output=Path("trial.jsonl"),
            stop_file=Path("trial.stop"),
            pid=1234,
            difficulty=3,
            pipeline_prewarm_shadow=True,
        )
        parsed = build_parser().parse_args(arguments)
        self.assertTrue(parsed.pipeline_prewarm_shadow)

    def test_candidate_verifier_shadow_is_explicitly_opt_in(self) -> None:
        arguments = build_long_run_arguments(
            output=Path("trial.jsonl"),
            stop_file=Path("trial.stop"),
            pid=1234,
            difficulty=3,
            candidate_verifier_shadow=True,
        )
        parsed = build_parser().parse_args(arguments)
        self.assertTrue(parsed.candidate_verifier_shadow)

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
