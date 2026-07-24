#!/usr/bin/env python3
"""Tests for compact offline viability-audit inputs."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np

from corridor_planner import (
    MovingAabbHazard,
    PiecewiseAabbHazard,
    SegmentHazard,
    SegmentTrajectoryHazard,
)
from touhou_control.trajectory import (
    PiecewiseLinearTrajectory,
    VelocityChange,
)
from touhou_control.packed_hazards import PackedSegmentFrames
from touhou_control.viability_audit_capsule import (
    read_viability_audit_capsule,
    write_viability_audit_capsule,
)


class ViabilityAuditCapsuleTests(unittest.TestCase):
    def test_round_trip_preserves_neutral_hazard_epoch(self) -> None:
        aabbs = (
            MovingAabbHazard(
                x=10.5,
                y=20.25,
                velocity_x=-1.0,
                velocity_y=2.0,
                half_width=3.0,
                half_height=4.0,
                base_uncertainty=0.5,
                uncertainty_per_frame=0.25,
            ),
        )
        piecewise = (
            PiecewiseAabbHazard(
                motion=PiecewiseLinearTrajectory(
                    30.0,
                    40.0,
                    1.0,
                    0.0,
                    (
                        VelocityChange(3, 0.0, 0.0),
                        VelocityChange(7, -2.0, 1.0),
                    ),
                ),
                half_width=2.0,
                half_height=2.5,
                base_uncertainty=1.0,
                uncertainty_per_frame=0.1,
            ),
        )
        segments = (
            SegmentTrajectoryHazard(
                (
                    None,
                    SegmentHazard(
                        origin_x=50.0,
                        origin_y=60.0,
                        angle=0.5,
                        tail=-2.0,
                        head=80.0,
                        half_width=5.0,
                        base_uncertainty=0.75,
                        uncertainty_per_frame=0.0,
                    ),
                )
            ),
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "policy.npz"
            write_viability_audit_capsule(
                path,
                metadata={
                    "source_frame": 123,
                    "context": [0, 5, 107],
                },
                aabbs=aabbs,
                piecewise_aabbs=piecewise,
                segment_trajectories=segments,
            )
            retained = read_viability_audit_capsule(path)
        self.assertEqual(retained.metadata["source_frame"], 123)
        self.assertEqual(retained.metadata["context"], [0, 5, 107])
        self.assertEqual(retained.aabbs, aabbs)
        self.assertEqual(retained.piecewise_aabbs, piecewise)
        self.assertEqual(retained.segment_trajectories, segments)

    def test_empty_hazard_epoch_round_trips_without_object_arrays(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "empty.npz"
            write_viability_audit_capsule(
                path,
                metadata={},
                aabbs=(),
                piecewise_aabbs=(),
                segment_trajectories=(),
            )
            retained = read_viability_audit_capsule(path)
        self.assertEqual(retained.aabbs, ())
        self.assertEqual(retained.piecewise_aabbs, ())
        self.assertEqual(retained.segment_trajectories, ())

    def test_packed_frame_major_lasers_round_trip_losslessly(self) -> None:
        packed = PackedSegmentFrames.from_frame_rows(
            (
                (),
                (
                    (10.0, 20.0, 0.5, -2.0, 40.0, 3.0, 0.75, 0.0),
                    (30.0, 40.0, 1.0, 0.0, 20.0, 2.0, 0.25, 0.1),
                ),
            )
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "packed.npz"
            write_viability_audit_capsule(
                path,
                metadata={"source_frame": 7},
                aabbs=(),
                piecewise_aabbs=(),
                segment_trajectories=(),
                packed_segments=packed,
            )
            retained = read_viability_audit_capsule(path)
        self.assertIsNotNone(retained.packed_segments)
        assert retained.packed_segments is not None
        self.assertEqual(retained.packed_segments.frame_count, 2)
        self.assertEqual(retained.packed_segments.sample_count, 2)
        np.testing.assert_array_equal(
            retained.packed_segments.frame_offsets,
            packed.frame_offsets,
        )
        for field in (
            "origin_x",
            "origin_y",
            "angle",
            "tail",
            "head",
            "half_width",
            "base_uncertainty",
            "uncertainty_per_frame",
        ):
            np.testing.assert_array_equal(
                getattr(retained.packed_segments, field),
                getattr(packed, field),
            )


if __name__ == "__main__":
    unittest.main()
