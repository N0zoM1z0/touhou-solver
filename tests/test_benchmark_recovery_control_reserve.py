#!/usr/bin/env python3
"""Focused eligibility regressions for reserve replay."""

from __future__ import annotations

import unittest

from benchmarks.benchmark_recovery_control_reserve import (
    _eligible_reserve_row,
)


class RecoveryControlReserveBenchmarkTests(unittest.TestCase):
    def test_losing_mode_includes_empty_repair_volume(self) -> None:
        row = {
            "corridor": {
                "viability": {
                    "safe_actions": [],
                    "repair_volumes": {"stay": 5},
                    "recovery_distances": {},
                    "support_covers_current": True,
                }
            }
        }
        self.assertTrue(
            _eligible_reserve_row(row, losing_state_reserve=True)
        )
        self.assertFalse(
            _eligible_reserve_row(row, losing_state_reserve=False)
        )

    def test_uncovered_support_is_never_sampled(self) -> None:
        row = {
            "corridor": {
                "viability": {
                    "safe_actions": [],
                    "repair_volumes": {"stay": 5},
                    "recovery_distances": {"stay": 16.0},
                    "support_covers_current": False,
                }
            }
        }
        for losing_state_reserve in (False, True):
            self.assertFalse(
                _eligible_reserve_row(
                    row,
                    losing_state_reserve=losing_state_reserve,
                )
            )


if __name__ == "__main__":
    unittest.main()
