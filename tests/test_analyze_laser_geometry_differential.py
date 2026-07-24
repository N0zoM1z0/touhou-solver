#!/usr/bin/env python3
"""Tests for retained TH08 laser geometry differential analysis."""

from __future__ import annotations

import unittest

from analysis.analyze_laser_geometry_differential import analyze


def _laser(
    *,
    head: float,
    tail: float,
    timer: int,
    origin_x: float = 100.0,
) -> list[object]:
    return [
        origin_x,
        200.0,
        0.25,
        tail,
        head,
        4.0,
        7,
        80.0,
        16.0,
        16.0,
        2.5,
        1,
        timer,
        0,
        0,
    ]


class LaserGeometryDifferentialTests(unittest.TestCase):
    def test_same_phase_native_timer_reproduces_head_and_tail(self) -> None:
        rows = (
            {
                "kind": "decision",
                "snapshot_frame": 100,
                "spell": {"spell_id": 50},
                "lasers": [_laser(head=80.0, tail=0.0, timer=10)],
            },
            {
                "kind": "decision",
                "snapshot_frame": 103,
                "spell": {"spell_id": 50},
                "lasers": [_laser(head=87.5, tail=7.5, timer=13)],
            },
            {
                "kind": "decision",
                "snapshot_frame": 106,
                "spell": {"spell_id": 50},
                "lasers": [
                    _laser(
                        head=95.0,
                        tail=15.0,
                        timer=16,
                        origin_x=101.0,
                    )
                ],
            },
        )
        report = analyze(
            rows,
            spell_id=50,
            max_frame_gap=10,
            tolerance=1e-4,
        )
        self.assertEqual(report["matched_pair_count"], 1)
        self.assertEqual(report["head_error"]["maximum"], 0.0)
        self.assertEqual(report["tail_error"]["maximum"], 0.0)
        self.assertEqual(report["origin_error"]["maximum"], 0.0)


if __name__ == "__main__":
    unittest.main()
