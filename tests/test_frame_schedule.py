#!/usr/bin/env python3
"""Regression tests for the reusable frame-schedule core."""

from __future__ import annotations

import unittest

from frame_schedule import FrameEvent, FramePhase, FrameSchedule


class FrameScheduleTests(unittest.TestCase):
    def test_priority_order_is_stable_for_equal_priorities(self) -> None:
        schedule = FrameSchedule(
            (
                FramePhase("late", 9, 0, (FrameEvent("late_event"),)),
                FramePhase("same_b", 4, 2, (FrameEvent("same_b_event"),)),
                FramePhase("same_a", 4, 1, (FrameEvent("same_a_event"),)),
            )
        )
        self.assertEqual(
            tuple(phase.key for phase in schedule.phases_for("any")),
            ("same_a", "same_b", "late"),
        )

    def test_modes_and_solver_filter_are_adapter_driven(self) -> None:
        schedule = FrameSchedule(
            (
                FramePhase("common", 1, 0, (FrameEvent("physics"),)),
                FramePhase(
                    "mode_only",
                    2,
                    0,
                    (FrameEvent("visual", solver_relevant=False),),
                    modes=frozenset({"replay"}),
                ),
            )
        )
        self.assertEqual(
            tuple(event.key for event in schedule.events_for("live")),
            ("physics",),
        )
        self.assertEqual(
            tuple(
                event.key
                for event in schedule.events_for("replay", solver_only=True)
            ),
            ("physics",),
        )

    def test_happens_before_uses_internal_event_order(self) -> None:
        schedule = FrameSchedule(
            (
                FramePhase(
                    "phase", 1, 0, (FrameEvent("first"), FrameEvent("second"))
                ),
            )
        )
        self.assertTrue(schedule.happens_before("live", "first", "second"))


if __name__ == "__main__":
    unittest.main()
