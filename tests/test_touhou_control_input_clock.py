#!/usr/bin/env python3
"""Tests for authority-free semantic input-clock episode grouping."""

from __future__ import annotations

import unittest

from touhou_control.input_clock import (
    SemanticClockObservation,
    SemanticInputClockTracker,
)


def observation(
    sample: int,
    active: bool | None,
    *,
    frame: int = 100,
    context: object = ("stage4a", 0),
) -> SemanticClockObservation:
    return SemanticClockObservation(
        monotonic_ns=sample * 1_000_000,
        physical_frame=frame,
        semantic_active=active,
        context=context,
        position=(float(sample), 0.0),
        active_input=0x40,
    )


class SemanticInputClockTrackerTests(unittest.TestCase):
    def test_slow_inactive_samples_do_not_create_ce0121_episodes(self) -> None:
        tracker = SemanticInputClockTracker()

        events = tuple(
            event
            for sample in range(2780)
            for event in tracker.observe(observation(sample, False))
        )

        self.assertEqual(events, ())
        self.assertIsNone(tracker.active_episode_id)

    def test_sustained_active_span_emits_one_begin_and_one_end(self) -> None:
        tracker = SemanticInputClockTracker()

        begin = tracker.observe(observation(1, True))
        middle = tracker.observe(observation(2, True))
        episode_id = tracker.mark_pulse()
        end = tracker.observe(observation(5, False))

        self.assertEqual([event.kind for event in begin], ["begin"])
        self.assertEqual(middle, ())
        self.assertEqual(episode_id, 1)
        self.assertEqual([event.kind for event in end], ["end"])
        self.assertEqual(end[0].pulse_count, 1)
        self.assertEqual(end[0].duration_ns, 4_000_000)
        self.assertEqual(end[0].displacement, 4.0)

    def test_active_state_changes_do_not_split_one_semantic_span(self) -> None:
        tracker = SemanticInputClockTracker()

        first = tracker.observe(observation(1, True))
        special_to_message = tracker.observe(observation(2, True))

        self.assertEqual(len(first), 1)
        self.assertEqual(special_to_message, ())
        self.assertEqual(tracker.active_episode_id, 1)

    def test_unknown_does_not_close_an_episode(self) -> None:
        tracker = SemanticInputClockTracker()
        tracker.observe(observation(1, True))

        self.assertEqual(tracker.observe(observation(2, None)), ())
        end = tracker.observe(observation(3, False))

        self.assertEqual(end[0].kind, "end")
        self.assertEqual(end[0].duration_ns, 2_000_000)

    def test_context_change_censors_before_starting_new_episode(self) -> None:
        tracker = SemanticInputClockTracker()
        tracker.observe(observation(1, True, context="old"))

        events = tracker.observe(observation(2, True, context="new"))

        self.assertEqual([event.kind for event in events], ["censored", "begin"])
        self.assertEqual(events[0].reason, "context_changed")
        self.assertNotEqual(events[0].episode_id, events[1].episode_id)
        self.assertEqual(events[0].observation.monotonic_ns, 1_000_000)
        self.assertEqual(events[1].observation.monotonic_ns, 2_000_000)

    def test_manager_frame_change_censors_an_unobserved_inactive_edge(
        self,
    ) -> None:
        tracker = SemanticInputClockTracker()
        tracker.observe(observation(1, True, frame=100))

        events = tracker.observe(observation(2, True, frame=1800))

        self.assertEqual([event.kind for event in events], ["censored", "begin"])
        self.assertEqual(events[0].reason, "physical_frame_changed")
        self.assertEqual(events[0].start.physical_frame, 100)
        self.assertEqual(events[0].observation.physical_frame, 100)
        self.assertEqual(events[1].start.physical_frame, 1800)

    def test_tracker_exposes_no_actuation_or_epoch_directive(self) -> None:
        tracker = SemanticInputClockTracker()

        public_names = set(dir(tracker))

        self.assertFalse(
            public_names
            & {
                "mask",
                "desired_mask",
                "reset_epoch",
                "retire_policy",
                "send_transitions",
            }
        )


if __name__ == "__main__":
    unittest.main()
