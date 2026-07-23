#!/usr/bin/env python3
"""Tests for schedule execution and exact differential state traces."""

from __future__ import annotations

import unittest
from dataclasses import replace

from deterministic_sim import DeterministicFrameExecutor
from frame_schedule import FrameEvent, FramePhase, FrameSchedule
from state_trace import (
    FloatEncoding,
    ProjectionField,
    StateProjection,
    TraceCollector,
    TraceRecord,
    first_trace_difference,
)
from th08_movement_model import INPUT_RIGHT
from th08_route2_player_runtime import step_route2_player
from th08_simulator import (
    TH08_ROUTE2_PLAYER_PROJECTION,
    Th08Route2FrameControl,
    initial_route2_simulation_state,
    route2_player_executor,
)


class DeterministicSimulationTests(unittest.TestCase):
    def test_executor_uses_schedule_order_not_handler_mapping_order(self) -> None:
        schedule = FrameSchedule(
            (
                FramePhase("late", 2, 0, (FrameEvent("b"),)),
                FramePhase("early", 1, 0, (FrameEvent("a"),)),
            )
        )
        executor = DeterministicFrameExecutor(
            schedule=schedule,
            mode="test",
            handlers={
                "b": lambda state, control, context: state + "b",
                "a": lambda state, control, context: state + "a",
            },
        )
        result = executor.step("", None, frame_index=0)
        self.assertEqual(result.state, "ab")
        self.assertEqual(result.executed_events, ("a", "b"))

    def test_selected_event_without_handler_is_rejected(self) -> None:
        schedule = FrameSchedule(
            (FramePhase("phase", 1, 0, (FrameEvent("required"),)),)
        )
        with self.assertRaises(ValueError):
            DeterministicFrameExecutor(
                schedule=schedule,
                mode="test",
                handlers={},
            )

    def test_binary32_projection_reports_first_event_field_difference(self) -> None:
        projection = StateProjection(
            (ProjectionField("x", ("x",), FloatEncoding.BINARY32_BITS),)
        )
        self.assertEqual(
            projection.capture({"x": 1.0})["x"],
            0x3F800000,
        )
        expected = (TraceRecord(4, "move", {"x": 0x3F800000}),)
        actual = (TraceRecord(4, "move", {"x": 0x3F800001}),)
        mismatch = first_trace_difference(expected, actual)
        self.assertEqual(mismatch.frame_index, 4)
        self.assertEqual(mismatch.event_key, "move")
        self.assertEqual(mismatch.field, "x")

    def test_route2_player_subset_runs_at_real_schedule_positions(self) -> None:
        state = initial_route2_simulation_state()
        control = Th08Route2FrameControl(INPUT_RIGHT)
        collector = TraceCollector(TH08_ROUTE2_PLAYER_PROJECTION)
        result = route2_player_executor().step(
            state,
            control,
            frame_index=0,
            observer=collector.observe,
        )
        direct = step_route2_player(state.player, input_mask=INPUT_RIGHT)
        self.assertEqual(result.state.player, direct.state)
        self.assertEqual(
            result.executed_events,
            ("replay_publish_input", "player_input_movement"),
        )
        self.assertEqual(len(collector.records), 2)
        self.assertEqual(collector.records[0].values["player.frame"], 0)
        self.assertEqual(collector.records[1].values["player.frame"], 1)

        changed = list(collector.records)
        changed[1] = replace(
            changed[1],
            values={**changed[1].values, "player.x": 0},
        )
        mismatch = first_trace_difference(collector.records, changed)
        self.assertEqual(mismatch.record_index, 1)
        self.assertEqual(mismatch.field, "player.x")


if __name__ == "__main__":
    unittest.main()
