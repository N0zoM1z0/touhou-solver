#!/usr/bin/env python3
"""Tests for bounded live-trial CEGAR summaries."""

from __future__ import annotations

import unittest

from th08_trial_report import summarize_rows


def _decision(frame: int, slack: float, *, hit: bool = False) -> dict:
    return {
        "kind": "decision",
        "frame": frame,
        "read_ms": 2.0,
        "plan_ms": 5.0,
        "resources": {"bombs": 3.0, "lives": 2.0, "power": float(frame)},
        "player": {"x": 192.0, "y": 400.0},
        "hit_started": hit,
        "corridor": {
            "source_frame": frame,
            "solve_ms": 10.0,
            "reachable": True,
            "lane": "left",
            "bottleneck_clearance": 8.0,
            "stale": False,
            "target": {
                "deadline": 8,
                "travel_frames": 8.0 - slack,
                "slack": slack,
            },
        },
    }


class Th08TrialReportTests(unittest.TestCase):
    def test_first_hit_reports_gate_abandonment_not_only_collision(self) -> None:
        report = summarize_rows(
            [
                _decision(100, 2.0),
                _decision(101, -1.0),
                _decision(102, -3.0, hit=True),
                {
                    "kind": "summary",
                    "termination_reason": "hit_limit",
                    "counter_gaps": 0,
                },
            ]
        )
        analysis = report["first_hit_analysis"]
        self.assertEqual(analysis["hit_frame"], 102)
        self.assertEqual(analysis["last_nonnegative_gate"]["frame"], 100)
        self.assertEqual(analysis["first_negative_gate"]["frame"], 101)
        self.assertEqual(report["termination_reason"], "hit_limit")

    def test_corridor_latency_counts_each_solution_once(self) -> None:
        first = _decision(100, 2.0)
        repeated = _decision(101, 1.0)
        repeated["corridor"]["source_frame"] = 100
        report = summarize_rows([first, repeated])
        self.assertEqual(report["corridor"]["record_count"], 2)
        self.assertEqual(report["corridor"]["unique_solution_count"], 1)

    def test_hit_witness_and_pipeline_boundary_are_structured(self) -> None:
        safe = _decision(100, 2.0)
        safe.update(
            {
                "snapshot_lag": 1,
                "action_lag": 2,
                "control_delay_frames": 3,
                "pipeline_clearance": 4.0,
            }
        )
        hit = _decision(103, 1.0, hit=True)
        hit.update(
            {
                "snapshot_lag": 0,
                "action_lag": 3,
                "control_delay_frames": 3,
                "pipeline_clearance": -0.5,
                "nearby_bullets": [
                    [17, 194.0, 401.0, 0.0, 0.0, 2.0, 2.0, 0],
                    [99, 240.0, 400.0, 0.0, 0.0, 2.0, 2.0, 0],
                ],
            }
        )
        report = summarize_rows([safe, hit])
        analysis = report["first_hit_analysis"]
        self.assertEqual(analysis["first_nonpositive_pipeline"]["frame"], 103)
        self.assertEqual(analysis["nearest_bullet"]["slot"], 17)
        self.assertEqual(report["frame_lag"]["modeled_control_delays"], [3])
        self.assertEqual(report["frame_lag"]["action"]["max"], 3.0)


if __name__ == "__main__":
    unittest.main()
