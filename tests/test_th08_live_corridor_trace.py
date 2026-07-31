#!/usr/bin/env python3
"""Tests for post-issue corridor trace serialization."""

from __future__ import annotations

import json
import math
import unittest
from types import SimpleNamespace

from th08_live.corridor_trace import build_corridor_trace_record


class CorridorTraceTests(unittest.TestCase):
    def _solution(self):
        plan = SimpleNamespace(
            reachable=True,
            planning_mode="robust",
            viability_backend="native",
            viability_grid_step=16.0,
            viability_policy=None,
            survival_policy=None,
            safety_value_policy=None,
            solver_timing_ms=(("solve", 1.0),),
            lane=2,
            bottleneck_clearance=4.5,
            initial_safe_action_count=3,
            initial_repair_volume=8,
            gate=None,
        )
        return SimpleNamespace(
            source_frame=100,
            snapshot_frame=98,
            forecast_lead_frames=2,
            solve_ms=3.0,
            worker_ms=4.0,
            background_priority_lowered=True,
            native_viability_worker_limit=4,
            native_viability_worker_limit_applied=True,
            plan=plan,
            audit_capsule=None,
            audit_write_ms=0.25,
            audit_error=None,
            audit_future=None,
            required_gate_lane=2,
            constraint_honored=True,
        )

    def test_no_publication_has_no_corridor_record(self) -> None:
        record = build_corridor_trace_record(
            active_solution=None,
            pending_solution=None,
            issue_frame=10,
            query_frame=9,
            max_age_frames=30,
            viability_query=None,
            safety_value_query=None,
            policy_lead=object(),
            commitment=object(),
            context_key=(0, 0, None),
            observed_input_action="stay",
            decision=object(),
            delay_support=(1,),
            guidance=object(),
            pending_command_estimate=None,
            target=None,
            control_origin_x=0.0,
            control_origin_y=0.0,
            action_name_from_mask=lambda _mask: "stay",
            minimum_travel_frames=lambda *_args: 0.0,
        )
        self.assertIsNone(record)

    def test_base_record_preserves_publication_and_target_fields(self) -> None:
        lead = SimpleNamespace(
            frames=80,
            sample_count=5,
            p90_solve_frames=12,
        )
        commitment = SimpleNamespace(
            active_lane=lambda _frame: 2,
            expires_frame=150,
        )
        decision = SimpleNamespace(action="left", mask=0x45)
        guidance = SimpleNamespace(safety_actions=())
        pending = SimpleNamespace(
            expected_mask=0x45,
            remaining_frames=(1, 2),
            snapshot_age=2,
            issue_age=1,
            overdue=False,
        )

        record = build_corridor_trace_record(
            active_solution=self._solution(),
            pending_solution=None,
            issue_frame=110,
            query_frame=108,
            max_age_frames=64,
            viability_query=None,
            safety_value_query=None,
            policy_lead=lead,
            commitment=commitment,
            context_key=(3, 1, 7),
            observed_input_action="stay",
            decision=decision,
            delay_support=(1, 2),
            guidance=guidance,
            pending_command_estimate=pending,
            target=(20.0, 30.0, 12),
            control_origin_x=10.0,
            control_origin_y=30.0,
            action_name_from_mask=lambda _mask: "left",
            minimum_travel_frames=lambda *_args: 4.0,
        )

        assert record is not None
        self.assertEqual(record["policy_status"], "unavailable")
        self.assertEqual(record["age"], 10)
        self.assertEqual(record["commitment"]["context"], (3, 1, 7))
        self.assertEqual(record["pending_command"]["desired_action"], "left")
        self.assertEqual(
            record["target"],
            {
                "x": 20.0,
                "y": 30.0,
                "deadline": 12,
                "travel_frames": 4.0,
                "slack": 8.0,
            },
        )

    def test_unreachable_clearance_is_strict_json_null(self) -> None:
        solution = self._solution()
        solution.plan.bottleneck_clearance = -math.inf
        lead = SimpleNamespace(
            frames=80,
            sample_count=5,
            p90_solve_frames=12,
        )
        commitment = SimpleNamespace(
            active_lane=lambda _frame: None,
            expires_frame=None,
        )
        record = build_corridor_trace_record(
            active_solution=solution,
            pending_solution=None,
            issue_frame=110,
            query_frame=108,
            max_age_frames=64,
            viability_query=None,
            safety_value_query=None,
            policy_lead=lead,
            commitment=commitment,
            context_key=(3, 1, None),
            observed_input_action="stay",
            decision=SimpleNamespace(action="stay", mask=0),
            delay_support=(1, 2),
            guidance=SimpleNamespace(safety_actions=()),
            pending_command_estimate=None,
            target=None,
            control_origin_x=0.0,
            control_origin_y=0.0,
            action_name_from_mask=lambda _mask: "stay",
            minimum_travel_frames=lambda *_args: 0.0,
        )

        assert record is not None
        self.assertIsNone(record["bottleneck_clearance"])
        json.dumps(record, allow_nan=False)


if __name__ == "__main__":
    unittest.main()
