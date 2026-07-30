#!/usr/bin/env python3
"""Tests for the extracted TH08 live-controller CLI schema."""

from __future__ import annotations

import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from th08_live import controller
from th08_live.cli import LiveParserDefaults, build_live_parser


class Th08LiveCliTests(unittest.TestCase):
    def test_pure_builder_uses_explicit_controller_defaults(self) -> None:
        defaults = LiveParserDefaults(
            planner_horizon=11,
            planner_threat_horizon=33,
            planner_beam_width=25,
            control_delay_frames=3,
            corridor_replan_frames=9,
            corridor_lookahead_frames=17,
            corridor_max_age_frames=73,
            stage_transition_timeout_seconds=91.0,
            terminal_inactive_grace_seconds=6.0,
            native_call_modes=("held", "released"),
            native_call_mode_gil_held="held",
            native_call_mode_gil_released="released",
        )

        arguments = build_live_parser(
            defaults,
            description="test parser",
        ).parse_args(["trace.jsonl"])

        self.assertEqual(arguments.output, Path("trace.jsonl"))
        self.assertEqual(arguments.horizon, 11)
        self.assertEqual(arguments.threat_horizon, 33)
        self.assertEqual(arguments.beam_width, 25)
        self.assertEqual(arguments.control_delay_frames, 3)
        self.assertEqual(arguments.corridor_every, 9)
        self.assertEqual(arguments.corridor_lookahead, 17)
        self.assertEqual(arguments.corridor_max_age, 73)
        self.assertEqual(arguments.stage_transition_timeout, 91.0)
        self.assertEqual(arguments.terminal_inactive_grace, 6.0)
        self.assertEqual(arguments.auxiliary_vm_native_call_mode, "held")
        self.assertFalse(arguments.trace_auxiliary_ecl_events)
        self.assertFalse(arguments.trace_priority17_publications)
        self.assertTrue(arguments.losing_control_reserve)
        self.assertEqual(
            arguments.bullet_birth_native_call_mode,
            "released",
        )

    def test_controller_wrapper_resolves_current_compatibility_values(
        self,
    ) -> None:
        with (
            patch.object(controller, "PLANNER_HORIZON", 19),
            patch.object(controller, "CORRIDOR_REPLAN_FRAMES", 13),
            patch.object(
                controller,
                "STAGE_TRANSITION_TIMEOUT_SECONDS",
                92.0,
            ),
        ):
            arguments = controller.build_parser().parse_args(["trace.jsonl"])

        self.assertEqual(arguments.horizon, 19)
        self.assertEqual(arguments.corridor_every, 13)
        self.assertEqual(arguments.stage_transition_timeout, 92.0)

    def test_bomb_options_remain_mutually_exclusive(self) -> None:
        parser = controller.build_parser()
        with (
            redirect_stderr(StringIO()),
            self.assertRaises(SystemExit),
        ):
            parser.parse_args(["trace.jsonl", "--normal-bomb", "--no-bomb"])

    def test_priority17_publication_probe_is_explicitly_opt_in(self) -> None:
        arguments = controller.build_parser().parse_args(
            ["trace.jsonl", "--trace-priority17-publications"]
        )

        self.assertTrue(arguments.trace_priority17_publications)

    def test_losing_control_reserve_has_explicit_rollback(self) -> None:
        arguments = controller.build_parser().parse_args(
            ["trace.jsonl", "--no-losing-control-reserve"]
        )

        self.assertFalse(arguments.losing_control_reserve)


if __name__ == "__main__":
    unittest.main()
