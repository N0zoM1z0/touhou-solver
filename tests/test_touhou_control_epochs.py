#!/usr/bin/env python3
"""Tests for asynchronous sensor frame alignment."""

from __future__ import annotations

import unittest

from touhou_control.epochs import FrameWindow, HazardEpochAlignment


class HazardEpochAlignmentTests(unittest.TestCase):
    def test_separates_old_player_lag_from_fresh_hazard_age(self) -> None:
        alignment = HazardEpochAlignment(
            source_frame=100,
            hazard_window=FrameWindow(104, 105),
            current_frame=106,
            event_window=FrameWindow(105, 106),
        )
        self.assertEqual(alignment.source_to_hazard_lag, 5)
        self.assertEqual(alignment.hazard_age, 1)
        self.assertEqual(alignment.event_frame_offset, 1)
        self.assertEqual(alignment.event_frame_uncertainty, 2)

    def test_same_epoch_capture_has_no_synthetic_projection(self) -> None:
        alignment = HazardEpochAlignment(
            source_frame=200,
            hazard_window=FrameWindow(205, 205),
            current_frame=205,
            event_window=FrameWindow(205, 205),
        )
        self.assertEqual(alignment.hazard_age, 0)
        self.assertEqual(alignment.event_frame_offset, 0)
        self.assertEqual(alignment.event_frame_uncertainty, 0)

    def test_invalid_capture_window_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            FrameWindow(9, 8)


if __name__ == "__main__":
    unittest.main()
