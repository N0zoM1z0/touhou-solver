#!/usr/bin/env python3
"""Tests for TH08's Windows-host input bridge helpers."""

from __future__ import annotations

import unittest
from unittest.mock import patch

import th08_runtime_agent


class Th08RuntimeAgentTests(unittest.TestCase):
    def test_recovery_releases_gameplay_keys_and_fast_forward_control(self) -> None:
        api = object()
        with (
            patch.object(th08_runtime_agent, "release_all") as release_all,
            patch.object(th08_runtime_agent, "send_scan_key") as send_scan_key,
        ):
            th08_runtime_agent.release_injected_keys(api)

        release_all.assert_called_once_with(api)
        send_scan_key.assert_called_once_with(api, scan_code=0x1D, pressed=False)

    def test_release_command_requires_explicit_arming(self) -> None:
        args = th08_runtime_agent.build_parser().parse_args(["release-inputs"])
        with self.assertRaisesRegex(RuntimeError, "explicit --armed"):
            args.func(args)

    def test_release_command_is_registered(self) -> None:
        args = th08_runtime_agent.build_parser().parse_args(
            ["release-inputs", "--armed"]
        )
        self.assertIs(args.func, th08_runtime_agent.command_release_inputs)


if __name__ == "__main__":
    unittest.main()
