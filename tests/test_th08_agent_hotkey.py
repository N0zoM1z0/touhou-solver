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
        self.assertFalse(parsed.trace_bullet_births)
        self.assertFalse(parsed.trace_auxiliary_vm_batches)
        self.assertEqual(parsed.safety_value_horizon, 0)
        self.assertIsNone(parsed.viability_audit_dir)
        self.assertFalse(parsed.postpublished_survival_shadow)
        self.assertFalse(parsed.pipeline_prewarm_shadow)
        self.assertFalse(parsed.candidate_verifier_shadow)
        self.assertFalse(parsed.input_clock_boundary_shadow)
        self.assertEqual(parsed.input_clock_shadow_sample_ms, 1.0)

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

    def test_bullet_birth_trace_is_explicitly_opt_in(self) -> None:
        arguments = build_long_run_arguments(
            output=Path("trial.jsonl"),
            stop_file=Path("trial.stop"),
            pid=1234,
            difficulty=3,
            trace_bullet_births=True,
        )
        parsed = build_parser().parse_args(arguments)
        self.assertTrue(parsed.trace_bullet_births)
        self.assertEqual(parsed.bullet_birth_backend, "python")
        self.assertEqual(
            parsed.bullet_birth_native_call_mode,
            "gil-released",
        )

        native_arguments = build_long_run_arguments(
            output=Path("trial.jsonl"),
            stop_file=Path("trial.stop"),
            pid=1234,
            difficulty=3,
            trace_bullet_births=True,
            bullet_birth_backend="native",
            bullet_birth_native_call_mode="gil-held",
        )
        native_parsed = build_parser().parse_args(native_arguments)
        self.assertEqual(native_parsed.bullet_birth_backend, "native")
        self.assertEqual(
            native_parsed.bullet_birth_native_call_mode,
            "gil-held",
        )

        derived_arguments = build_long_run_arguments(
            output=Path("trial.jsonl"),
            stop_file=Path("trial.stop"),
            pid=1234,
            difficulty=3,
            trace_bullet_births=True,
            trace_derived_pattern_sources=True,
        )
        derived_parsed = build_parser().parse_args(derived_arguments)
        self.assertTrue(derived_parsed.trace_derived_pattern_sources)

        main_vm_arguments = build_long_run_arguments(
            output=Path("trial.jsonl"),
            stop_file=Path("trial.stop"),
            pid=1234,
            difficulty=3,
            trace_bullet_births=True,
            trace_nonspell_main_vms=True,
        )
        main_vm_parsed = build_parser().parse_args(main_vm_arguments)
        self.assertTrue(main_vm_parsed.trace_nonspell_main_vms)

        auxiliary_arguments = build_long_run_arguments(
            output=Path("trial.jsonl"),
            stop_file=Path("trial.stop"),
            pid=1234,
            difficulty=3,
            trace_auxiliary_vm_batches=True,
            auxiliary_vm_batch_every=16,
            auxiliary_vm_batch_spell_id=107,
            auxiliary_vm_native_call_mode="gil-held",
        )
        auxiliary_parsed = build_parser().parse_args(auxiliary_arguments)
        self.assertTrue(auxiliary_parsed.trace_auxiliary_vm_batches)
        self.assertEqual(auxiliary_parsed.auxiliary_vm_batch_every, 16)
        self.assertEqual(auxiliary_parsed.auxiliary_vm_batch_spell_id, 107)
        self.assertEqual(
            auxiliary_parsed.auxiliary_vm_native_call_mode,
            "gil-held",
        )

        with self.assertRaisesRegex(ValueError, "requires"):
            build_long_run_arguments(
                output=Path("trial.jsonl"),
                stop_file=Path("trial.stop"),
                pid=1234,
                difficulty=3,
                trace_derived_pattern_sources=True,
            )
        with self.assertRaisesRegex(ValueError, "requires"):
            build_long_run_arguments(
                output=Path("trial.jsonl"),
                stop_file=Path("trial.stop"),
                pid=1234,
                difficulty=3,
                trace_nonspell_main_vms=True,
            )

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

    def test_normal_and_hard_runtime_difficulties_are_supported(self) -> None:
        for difficulty in (1, 2):
            with self.subTest(difficulty=difficulty):
                arguments = build_long_run_arguments(
                    output=Path("trial.jsonl"),
                    stop_file=Path("trial.stop"),
                    pid=1234,
                    difficulty=difficulty,
                )
                parsed = build_parser().parse_args(arguments)
                self.assertEqual(parsed.difficulty, difficulty)

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

    def test_shadow_services_are_explicitly_opt_in(self) -> None:
        cases = (
            (
                {"pipeline_prewarm_shadow": True},
                "pipeline_prewarm_shadow",
            ),
            (
                {"candidate_verifier_shadow": True},
                "candidate_verifier_shadow",
            ),
            (
                {
                    "input_clock_boundary_shadow": True,
                    "input_clock_shadow_sample_ms": 2.5,
                },
                "input_clock_boundary_shadow",
            ),
        )
        for overrides, attribute in cases:
            with self.subTest(attribute=attribute):
                arguments = build_long_run_arguments(
                    output=Path("trial.jsonl"),
                    stop_file=Path("trial.stop"),
                    pid=1234,
                    difficulty=3,
                    **overrides,
                )
                parsed = build_parser().parse_args(arguments)
                self.assertTrue(getattr(parsed, attribute))
                if attribute == "input_clock_boundary_shadow":
                    self.assertEqual(
                        parsed.input_clock_shadow_sample_ms,
                        2.5,
                    )

    def test_corridor_background_priority_is_explicitly_opt_in(self) -> None:
        default_arguments = build_long_run_arguments(
            output=Path("trial.jsonl"),
            stop_file=Path("trial.stop"),
            pid=1234,
            difficulty=3,
        )
        enabled_arguments = build_long_run_arguments(
            output=Path("trial.jsonl"),
            stop_file=Path("trial.stop"),
            pid=1234,
            difficulty=3,
            corridor_background_low_priority=True,
        )

        self.assertNotIn(
            "--corridor-background-low-priority",
            default_arguments,
        )
        self.assertIn(
            "--corridor-background-low-priority",
            enabled_arguments,
        )
        self.assertFalse(
            build_parser()
            .parse_args(default_arguments)
            .corridor_background_low_priority
        )
        self.assertTrue(
            build_parser()
            .parse_args(enabled_arguments)
            .corridor_background_low_priority
        )

    def test_direct_root_certificate_shadow_is_explicitly_opt_in(
        self,
    ) -> None:
        arguments = build_long_run_arguments(
            output=Path("trial.jsonl"),
            stop_file=Path("trial.stop"),
            pid=1234,
            difficulty=3,
            local_pipeline_root_shadow_every=16,
        )

        parsed = build_parser().parse_args(arguments)

        self.assertEqual(parsed.local_pipeline_root_shadow_every, 16)

    def test_native_backends_default_with_explicit_rollbacks(self) -> None:
        cases = (
            ("local_hazard_backend", "numpy"),
            ("local_beam_reducer", "python"),
            ("bullet_decode_backend", "python"),
        )
        for attribute, rollback in cases:
            with self.subTest(attribute=attribute):
                default_arguments = build_long_run_arguments(
                    output=Path("trial.jsonl"),
                    stop_file=Path("trial.stop"),
                    pid=1234,
                    difficulty=3,
                )
                rollback_arguments = build_long_run_arguments(
                    output=Path("trial.jsonl"),
                    stop_file=Path("trial.stop"),
                    pid=1234,
                    difficulty=3,
                    **{attribute: rollback},
                )
                self.assertEqual(
                    getattr(
                        build_parser().parse_args(default_arguments),
                        attribute,
                    ),
                    "native",
                )
                self.assertEqual(
                    getattr(
                        build_parser().parse_args(rollback_arguments),
                        attribute,
                    ),
                    rollback,
                )

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
