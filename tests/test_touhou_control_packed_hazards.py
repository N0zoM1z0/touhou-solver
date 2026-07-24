#!/usr/bin/env python3
"""Tests for frame-major native hazard contracts."""

from __future__ import annotations

import unittest

import numpy as np

from corridor_planner import SegmentHazard, SegmentTrajectoryHazard
from touhou_control.packed_hazards import PackedSegmentFrames


class PackedSegmentFramesTests(unittest.TestCase):
    def test_trajectory_objects_are_transposed_to_frame_major_order(self) -> None:
        left = SegmentHazard(1.0, 2.0, 0.1, 0.0, 10.0, 2.0)
        right = SegmentHazard(3.0, 4.0, 0.2, 0.0, 20.0, 3.0)
        packed = PackedSegmentFrames.from_trajectories(
            (
                SegmentTrajectoryHazard((None, left)),
                SegmentTrajectoryHazard((right, right)),
            ),
            frame_count=2,
        )
        np.testing.assert_array_equal(
            packed.frame_offsets,
            np.asarray([0, 1, 3], dtype=np.int32),
        )
        np.testing.assert_array_equal(
            packed.origin_x,
            np.asarray([3.0, 1.0, 3.0], dtype=np.float32),
        )

    def test_empty_batch_retains_requested_frame_count(self) -> None:
        packed = PackedSegmentFrames.empty(81)
        self.assertEqual(packed.frame_count, 81)
        self.assertEqual(packed.sample_count, 0)

    def test_mismatched_field_lengths_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "origin_x"):
            PackedSegmentFrames(
                np.asarray([0, 1], dtype=np.int32),
                np.empty(0, dtype=np.float32),
                *(np.zeros(1, dtype=np.float32) for _ in range(7)),
            )

    def test_negative_width_is_rejected(self) -> None:
        rows = (((0.0, 0.0, 0.0, 0.0, 1.0, -1.0, 0.0, 0.0),),)
        with self.assertRaisesRegex(ValueError, "cannot be negative"):
            PackedSegmentFrames.from_frame_rows(rows)


if __name__ == "__main__":
    unittest.main()
