#!/usr/bin/env python3
"""Tests for the scoped non-fail-close physical-observer scale proxy."""

from __future__ import annotations

import unittest

from th08_live.controller import (
    DIAGNOSTIC_ROOT_ONLY_SCALE_HORIZON,
    _diagnostic_constant_root_time_scale,
)
from th08_time_scale import (
    SCALE_COVERAGE_COMPLETE,
    Th08TimeScaleSchedule,
)


class DiagnosticTimeScaleFallbackTests(unittest.TestCase):
    def test_root_only_observation_becomes_explicit_constant_proxy(self) -> None:
        root = Th08TimeScaleSchedule.root_observation(
            0x3F000000,
            source_frame=123,
        )
        proxy = _diagnostic_constant_root_time_scale(root)

        self.assertEqual(proxy.coverage, SCALE_COVERAGE_COMPLETE)
        self.assertEqual(
            proxy.complete_horizon,
            DIAGNOSTIC_ROOT_ONLY_SCALE_HORIZON,
        )
        self.assertEqual(
            set(proxy.player_scale_bits),
            {0x3F000000},
        )
        self.assertEqual(
            set(proxy.laser_scale_bits),
            {0x3F000000},
        )
        self.assertEqual(proxy.source_frame, 123)
        self.assertIn("unknown_direction", proxy.provenance)
        self.assertIn("no_authority", proxy.provenance)

    def test_complete_schedule_cannot_enter_root_only_fallback(self) -> None:
        complete = Th08TimeScaleSchedule.constant(
            0x3F800000,
            horizon=4,
        )
        with self.assertRaisesRegex(ValueError, "root-only"):
            _diagnostic_constant_root_time_scale(complete)


if __name__ == "__main__":
    unittest.main()
