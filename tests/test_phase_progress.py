#!/usr/bin/env python3
"""Small regressions for game-neutral phase progress ordering."""

from __future__ import annotations

import unittest

from touhou_control.phase_progress import (
    PhaseProgressState,
    PhaseProgressTracker,
    ProgressCandidate,
    select_progress_action,
)


class PhaseProgressTests(unittest.TestCase):
    def test_tracker_distinguishes_damage_from_phase_reset(self) -> None:
        tracker = PhaseProgressTracker()
        first = PhaseProgressState("phase", 100, 1000, 1000, 0, 10.0, 600, True)
        second = PhaseProgressState("phase", 104, 940, 1000, 0, 14.0, 600, True)
        reset = PhaseProgressState("phase", 105, 1200, 1200, 0, 0.0, 600, True)
        self.assertEqual(tracker.observe(first).status, "initial")
        observed = tracker.observe(second)
        self.assertEqual(observed.status, "comparable")
        self.assertEqual(observed.health_delta, 60)
        self.assertEqual(observed.damage_per_frame, 15.0)
        self.assertEqual(tracker.observe(reset).status, "phase_reset")

    def test_progress_never_selects_an_unsafe_lower_cost(self) -> None:
        selected = select_progress_action(
            (
                ProgressCandidate("unsafe", 0.0, True, 1, -2.0, (0,)),
                ProgressCandidate("safe", 5.0, True, 0, 3.0, (1,)),
                ProgressCandidate("not_viable", 1.0, False, 0, 4.0, (2,)),
            )
        )
        self.assertIsNotNone(selected)
        self.assertEqual(selected.action, "safe")

    def test_tracker_attributes_phase_change_to_pending_native_boundary(self) -> None:
        tracker = PhaseProgressTracker()
        pending = PhaseProgressState(
            "phase-1",
            100,
            490,
            1000,
            500,
            100.0,
            1800,
            True,
            completion_pending="health",
            continuity_key=("epoch", 5, 0x1234),
        )
        successor = PhaseProgressState(
            "phase-2",
            101,
            500,
            500,
            100,
            101.0,
            None,
            True,
            continuity_key=("epoch", 5, 0x1234),
        )
        self.assertEqual(tracker.observe(pending).status, "initial")
        observation = tracker.observe(successor)
        self.assertEqual(observation.status, "phase_changed")
        self.assertEqual(observation.completion_cause, "health")

    def test_tracker_does_not_attribute_across_entity_change(self) -> None:
        tracker = PhaseProgressTracker()
        pending = PhaseProgressState(
            "phase-1",
            100,
            490,
            1000,
            500,
            100.0,
            1800,
            True,
            completion_pending="health",
            continuity_key=("epoch-1", 5, 0x1234),
        )
        other_entity = PhaseProgressState(
            "phase-2",
            101,
            500,
            500,
            100,
            101.0,
            None,
            True,
            continuity_key=("epoch-2", 5, 0x1234),
        )
        tracker.observe(pending)
        observation = tracker.observe(other_entity)
        self.assertEqual(observation.status, "phase_changed")
        self.assertIsNone(observation.completion_cause)


if __name__ == "__main__":
    unittest.main()
