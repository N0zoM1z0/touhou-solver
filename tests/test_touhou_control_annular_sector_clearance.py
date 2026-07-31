"""Tests for compact set-valued annular-sector hazard clearance."""

from __future__ import annotations

import math
import unittest

import numpy as np

from touhou_control.corridor import (
    AnnularSectorTrajectoryHazard,
    annular_sector_clearance_field,
    packed_annular_sector_clearance_field,
)
from touhou_control import native_backend
from touhou_control.packed_hazards import PackedAnnularSectorFrames


class AnnularSectorClearanceTests(unittest.TestCase):
    def _field(
        self,
        points: tuple[tuple[float, float], ...],
        hazard: AnnularSectorTrajectoryHazard,
        *,
        player_radius: float = 0.0,
    ) -> np.ndarray:
        grid_x = np.asarray([[point[0] for point in points]], dtype=np.float32)
        grid_y = np.asarray([[point[1] for point in points]], dtype=np.float32)
        return annular_sector_clearance_field(
            grid_x,
            grid_y,
            (hazard,),
            frame=0,
            player_radius=player_radius,
        )[0]

    def test_continuous_sector_preserves_far_empty_side(self) -> None:
        hazard = AnnularSectorTrajectoryHazard(
            origin_x=0.0,
            origin_y=0.0,
            minimum_angle=-0.1,
            maximum_angle=0.1,
            minimum_radii=(9.0,),
            maximum_radii=(11.0,),
            half_extent_radius=1.0,
        )
        clearance = self._field(((10.0, 0.0), (-10.0, 0.0)), hazard)
        self.assertLess(clearance[0], 0.0)
        self.assertGreater(clearance[1], 17.0)

    def test_boundary_ray_distance_uses_clamped_radial_segment(self) -> None:
        hazard = AnnularSectorTrajectoryHazard(
            origin_x=0.0,
            origin_y=0.0,
            minimum_angle=0.0,
            maximum_angle=math.pi * 0.5,
            minimum_radii=(5.0,),
            maximum_radii=(10.0,),
            half_extent_radius=0.0,
        )
        clearance = self._field(((6.0, -4.0),), hazard)
        self.assertAlmostEqual(float(clearance[0]), 4.0, places=4)

    def test_origin_and_shape_inflation_is_conservative(self) -> None:
        hazard = AnnularSectorTrajectoryHazard(
            origin_x=0.0,
            origin_y=0.0,
            minimum_angle=0.0,
            maximum_angle=0.0,
            minimum_radii=(10.0,),
            maximum_radii=(10.0,),
            half_extent_radius=2.0,
            origin_uncertainty=1.0,
        )
        clearance = self._field(
            ((14.0, 0.0),),
            hazard,
            player_radius=1.0,
        )
        self.assertLess(clearance[0], 0.0)

    def test_absent_frame_has_infinite_clearance(self) -> None:
        hazard = AnnularSectorTrajectoryHazard(
            origin_x=0.0,
            origin_y=0.0,
            minimum_angle=0.0,
            maximum_angle=0.0,
            minimum_radii=(None,),
            maximum_radii=(None,),
            half_extent_radius=1.0,
        )
        clearance = self._field(((0.0, 0.0),), hazard)
        self.assertTrue(np.isinf(clearance[0]))

    def test_packed_frame_field_matches_object_reference(self) -> None:
        hazards = (
            AnnularSectorTrajectoryHazard(
                origin_x=1.25,
                origin_y=-2.5,
                minimum_angle=-0.7,
                maximum_angle=1.2,
                minimum_radii=(None, 3.0, 5.0),
                maximum_radii=(None, 5.0, 8.0),
                half_extent_radius=1.5,
                origin_uncertainty=0.25,
                base_uncertainty=0.5,
                uncertainty_per_frame=0.125,
            ),
            AnnularSectorTrajectoryHazard(
                origin_x=-3.0,
                origin_y=4.0,
                minimum_angle=2.8,
                maximum_angle=2.8 + 2.0 * math.pi,
                minimum_radii=(2.0, 4.0, None),
                maximum_radii=(4.0, 7.0, None),
                half_extent_radius=0.75,
            ),
        )
        grid_x, grid_y = np.meshgrid(
            np.arange(-16.0, 17.0, 4.0, dtype=np.float32),
            np.arange(-16.0, 17.0, 4.0, dtype=np.float32),
        )
        packed = PackedAnnularSectorFrames.from_trajectories(
            hazards,
            frame_count=3,
        )
        for frame in (-1, 0, 1, 2, 3):
            expected = annular_sector_clearance_field(
                grid_x,
                grid_y,
                hazards,
                frame=frame,
                player_radius=2.0,
            )
            actual = packed_annular_sector_clearance_field(
                grid_x,
                grid_y,
                packed,
                frame=frame,
                player_radius=2.0,
            )
            np.testing.assert_allclose(actual, expected, rtol=0.0, atol=2e-5)

    def test_native_volume_matches_independent_python_field(self) -> None:
        hazards = (
            AnnularSectorTrajectoryHazard(
                origin_x=1.25,
                origin_y=-2.5,
                minimum_angle=-0.7,
                maximum_angle=1.2,
                minimum_radii=(None, 3.0, 5.0),
                maximum_radii=(None, 5.0, 8.0),
                half_extent_radius=1.5,
                origin_uncertainty=0.25,
            ),
            AnnularSectorTrajectoryHazard(
                origin_x=-3.0,
                origin_y=4.0,
                minimum_angle=2.8,
                maximum_angle=2.8 + 2.0 * math.pi,
                minimum_radii=(2.0, 4.0, 6.0),
                maximum_radii=(4.0, 7.0, 9.0),
                half_extent_radius=0.75,
            ),
        )
        x_axis = np.arange(-16.0, 17.0, 4.0, dtype=np.float32)
        y_axis = np.arange(-16.0, 17.0, 4.0, dtype=np.float32)
        grid_x, grid_y = np.meshgrid(x_axis, y_axis)
        expected = np.full((3, len(y_axis), len(x_axis)), 48.0, np.float32)
        for frame in range(3):
            expected[frame] = np.minimum(
                expected[frame],
                annular_sector_clearance_field(
                    grid_x,
                    grid_y,
                    hazards,
                    frame=frame,
                    player_radius=2.0,
                ),
            )
        actual = native_backend.apply_annular_sector_trajectory_clearance(
            x_axis=x_axis,
            y_axis=y_axis,
            player_radius=2.0,
            annular_sector_trajectories=hazards,
            clearance_volume=np.full_like(expected, 48.0),
        )
        if actual is None:
            self.skipTest("optional native geometry backend is unavailable")
        np.testing.assert_allclose(actual, expected, rtol=0.0, atol=2.0e-5)

    def test_native_grouped_angular_union_matches_independent_field(
        self,
    ) -> None:
        intervals = (
            (-0.4, 0.2),
            (0.1, 0.8),
            (1.4, 1.6),
            (2.9, 3.8),
            (2.0 * math.pi - 0.2, 2.0 * math.pi + 0.3),
        )
        hazards = tuple(
            AnnularSectorTrajectoryHazard(
                origin_x=1.25,
                origin_y=-2.5,
                minimum_angle=minimum_angle,
                maximum_angle=maximum_angle,
                minimum_radii=(None, 3.0, 5.0),
                maximum_radii=(None, 7.0, 10.0),
                half_extent_radius=1.5,
                origin_uncertainty=0.25,
            )
            for minimum_angle, maximum_angle in intervals
        )
        x_axis = np.arange(-20.0, 21.0, 2.0, dtype=np.float32)
        y_axis = np.arange(-20.0, 21.0, 2.0, dtype=np.float32)
        grid_x, grid_y = np.meshgrid(x_axis, y_axis)
        expected = np.full((3, len(y_axis), len(x_axis)), 48.0, np.float32)
        for frame in range(3):
            expected[frame] = np.minimum(
                expected[frame],
                annular_sector_clearance_field(
                    grid_x,
                    grid_y,
                    hazards,
                    frame=frame,
                    player_radius=2.0,
                ),
            )
        actual = native_backend.apply_annular_sector_trajectory_clearance(
            x_axis=x_axis,
            y_axis=y_axis,
            player_radius=2.0,
            annular_sector_trajectories=hazards,
            clearance_volume=np.full_like(expected, 48.0),
        )
        if actual is None:
            self.skipTest("optional native geometry backend is unavailable")
        np.testing.assert_allclose(actual, expected, rtol=0.0, atol=2.0e-5)


if __name__ == "__main__":
    unittest.main()
