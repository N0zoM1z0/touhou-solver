#!/usr/bin/env python3
"""Tests for the game-neutral time-expanded corridor planner."""

from __future__ import annotations

import math
import unittest
from unittest.mock import Mock, patch

import numpy as np
import touhou_control.corridor.robust as robust_corridor_module

from corridor_planner import (
    AabbHazard,
    AabbTrajectoryHazard,
    CorridorBounds,
    CorridorConfig,
    MovingAabbHazard,
    PiecewiseAabbHazard,
    RobustControlSpec,
    SegmentHazard,
    SegmentTrajectoryHazard,
    _aabb_clearance_field,
    _aabb_clearance_volume,
    _aabb_sample_clearance_field,
    _hazard_clearance_volume,
    _segment_clearance_field,
    plan_corridor,
    plan_prepared_corridor,
)
from touhou_control.corridor import prepare_corridor_problem
from touhou_control.native_backend import available as native_available
from touhou_control.packed_hazards import PackedSegmentFrames
from touhou_control.trajectory import PiecewiseLinearTrajectory, VelocityChange
from touhou_control.viability import ControlAction, ViabilityQuery


BOUNDS = CorridorBounds(0.0, 96.0, 0.0, 96.0)
CONFIG = CorridorConfig(
    grid_step=8.0,
    frames_per_layer=4,
    horizon_frames=32,
    cardinal_speed=4.0,
    diagonal_axis_speed=2.8284270763397217,
    preferred_clearance=6.0,
)


class CorridorPlannerTests(unittest.TestCase):
    def test_prepared_problem_is_callback_free_and_solve_equivalent(
        self,
    ) -> None:
        callbacks: list[str] = []
        bounds = CorridorBounds(0.0, 24.0, 0.0, 24.0)
        config = CorridorConfig(
            grid_step=8.0,
            frames_per_layer=4,
            horizon_frames=8,
        )
        control = RobustControlSpec(
            actions=(
                ControlAction("stay", 0.0, 0.0),
                ControlAction("right", 2.0, 0.0),
            ),
            delay_frames=(1, 2),
            nominal_delay=1,
            active_action="stay",
            retain_query_survival_problem=True,
            pre_viability_problem_hook=lambda problem: callbacks.append(
                "unexpected"
            ),
        )
        prepared = prepare_corridor_problem(
            bounds=bounds,
            config=config,
            robust_control=control,
        )

        self.assertEqual(callbacks, [])
        self.assertIsNone(
            prepared.robust_control.pre_viability_problem_hook
        )
        self.assertIsNotNone(prepared.survival_query_problem)
        self.assertEqual(prepared.clearance_volume.shape, (9, 4, 4))
        self.assertGreaterEqual(prepared.clearance_ms, 0.0)
        self.assertGreaterEqual(prepared.query_problem_ms, 0.0)
        self.assertGreaterEqual(
            prepared.preparation_ms,
            prepared.clearance_ms,
        )

        split = plan_prepared_corridor(
            start_x=8.0,
            start_y=8.0,
            prepared_problem=prepared,
            preferred_x=16.0,
        )
        direct = plan_corridor(
            start_x=8.0,
            start_y=8.0,
            bounds=bounds,
            config=config,
            preferred_x=16.0,
            robust_control=RobustControlSpec(
                actions=control.actions,
                delay_frames=control.delay_frames,
                nominal_delay=control.nominal_delay,
                active_action=control.active_action,
                retain_query_survival_problem=True,
            ),
        )

        self.assertEqual(callbacks, [])
        self.assertEqual(split.reachable, direct.reachable)
        self.assertEqual(split.path, direct.path)
        self.assertEqual(split.lane, direct.lane)
        self.assertEqual(split.reason, direct.reason)
        self.assertEqual(
            split.initial_safe_action_count,
            direct.initial_safe_action_count,
        )
        self.assertEqual(
            split.initial_repair_volume,
            direct.initial_repair_volume,
        )
        self.assertEqual(
            tuple(name for name, _ in split.solver_timing_ms),
            tuple(name for name, _ in direct.solver_timing_ms),
        )

    def test_retained_query_hook_runs_after_clearance_before_viability(
        self,
    ) -> None:
        events: list[str] = []
        original_builder = (
            robust_corridor_module.build_robust_viability_policy
        )

        def hook(problem) -> None:
            self.assertEqual(problem.clearance_volume.shape[0], 9)
            events.append("hook")

        def checked_builder(*args, **kwargs):
            self.assertEqual(events, ["hook"])
            events.append("viability")
            return original_builder(*args, **kwargs)

        with patch(
            "touhou_control.corridor.robust."
            "build_robust_viability_policy",
            side_effect=checked_builder,
        ):
            plan = plan_corridor(
                start_x=8.0,
                start_y=8.0,
                bounds=CorridorBounds(0.0, 16.0, 0.0, 16.0),
                config=CorridorConfig(
                    grid_step=8.0,
                    frames_per_layer=4,
                    horizon_frames=8,
                ),
                robust_control=RobustControlSpec(
                    actions=(ControlAction("stay", 0.0, 0.0),),
                    delay_frames=(1,),
                    nominal_delay=1,
                    active_action="stay",
                    retain_query_survival_problem=True,
                    pre_viability_problem_hook=hook,
                ),
            )

        self.assertEqual(events, ["hook", "viability"])
        self.assertIsNotNone(plan.survival_query_problem)
        timing = dict(plan.solver_timing_ms)
        self.assertIn("pre_viability_hook", timing)
        self.assertGreaterEqual(timing["pre_viability_hook"], 0.0)

    @unittest.skipUnless(
        native_available(),
        "native planner backend is not built",
    )
    def test_native_time_volume_matches_numpy_mixed_hazards(self) -> None:
        grid_x, grid_y = np.meshgrid(
            np.arange(0.0, 49.0, 8.0, dtype=np.float32),
            np.arange(0.0, 41.0, 8.0, dtype=np.float32),
        )
        aabbs = (
            MovingAabbHazard(
                x=-5.0,
                y=4.0,
                velocity_x=2.5,
                velocity_y=1.25,
                half_width=3.0,
                half_height=5.0,
                base_uncertainty=0.5,
                uncertainty_per_frame=0.25,
            ),
            MovingAabbHazard(
                x=52.0,
                y=36.0,
                velocity_x=-1.5,
                velocity_y=-2.0,
                half_width=7.0,
                half_height=2.0,
            ),
        )
        segments = (
            SegmentHazard(
                0.0,
                0.0,
                0.0,
                0.0,
                20.0,
                2.0,
                1.0,
                0.5,
            ),
            SegmentHazard(
                10.0,
                -10.0,
                math.pi / 2.0,
                0.0,
                20.0,
                1.0,
            ),
        )
        config = CorridorConfig(
            grid_step=8.0,
            frames_per_layer=4,
            horizon_frames=8,
            danger_radius=12.0,
        )
        native = _hazard_clearance_volume(
            grid_x,
            grid_y,
            aabbs=aabbs,
            segments=segments,
            segment_trajectories=(),
            config=config,
        )
        reference = _aabb_clearance_volume(
            grid_x,
            grid_y,
            aabbs,
            horizon_frames=8,
            player_radius=config.player_radius,
            clearance_cap=config.danger_radius,
        )
        for frame in range(9):
            reference[frame] = np.minimum(
                reference[frame],
                _segment_clearance_field(
                    grid_x,
                    grid_y,
                    segments,
                    frame=frame,
                    player_radius=config.player_radius,
                ),
            )
        np.testing.assert_allclose(native, reference, atol=3e-5)

    @unittest.skipUnless(
        native_available(),
        "native planner backend is not built",
    )
    def test_native_bounded_aabb_traversal_matches_adversarial_dense_oracle(
        self,
    ) -> None:
        rng = np.random.default_rng(9292)
        grid_x, grid_y = np.meshgrid(
            np.arange(8.0, 377.0, 16.0, dtype=np.float32),
            np.arange(16.0, 433.0, 16.0, dtype=np.float32),
        )
        aabbs = tuple(
            MovingAabbHazard(
                x=float(rng.uniform(-100.0, 476.0)),
                y=float(rng.uniform(-100.0, 532.0)),
                velocity_x=float(rng.uniform(-5.0, 5.0)),
                velocity_y=float(rng.uniform(-5.0, 5.0)),
                half_width=float(rng.uniform(0.0, 18.0)),
                half_height=float(rng.uniform(0.0, 18.0)),
                base_uncertainty=float(rng.uniform(0.0, 2.0)),
                uncertainty_per_frame=float(rng.uniform(0.0, 0.2)),
            )
            for _ in range(200)
        )
        config = CorridorConfig(
            grid_step=16.0,
            frames_per_layer=8,
            horizon_frames=16,
            danger_radius=48.0,
        )
        actual = _hazard_clearance_volume(
            grid_x,
            grid_y,
            aabbs=aabbs,
            segments=(),
            segment_trajectories=(),
            config=config,
        )
        expected = _aabb_clearance_volume(
            grid_x,
            grid_y,
            aabbs,
            horizon_frames=config.horizon_frames,
            player_radius=config.player_radius,
            clearance_cap=config.danger_radius,
        )
        np.testing.assert_allclose(actual, expected, atol=5e-6)

    @unittest.skipUnless(
        native_available(),
        "native planner backend is not built",
    )
    def test_native_static_segment_cap_bounds_keep_finite_capsules(self) -> None:
        grid_x, grid_y = np.meshgrid(
            np.arange(-24.0, 73.0, 8.0, dtype=np.float32),
            np.arange(-16.0, 65.0, 8.0, dtype=np.float32),
        )
        segments = (
            SegmentHazard(-200.0, -200.0, 0.0, 0.0, 20.0, 2.0),
            SegmentHazard(8.0, 12.0, 0.7, 45.0, -30.0, 3.0, 0.5, 0.2),
            SegmentHazard(40.0, 24.0, 1.2, 0.0, 0.0, 6.0, 1.0, 0.4),
            SegmentHazard(300.0, 300.0, 2.0, -120.0, 150.0, 4.0),
        )
        config = CorridorConfig(
            grid_step=8.0,
            frames_per_layer=1,
            horizon_frames=6,
            danger_radius=12.0,
        )
        actual = _hazard_clearance_volume(
            grid_x,
            grid_y,
            aabbs=(),
            segments=segments,
            segment_trajectories=(),
            config=config,
        )
        expected = np.stack(
            [
                np.minimum(
                    _segment_clearance_field(
                        grid_x,
                        grid_y,
                        segments,
                        frame=frame,
                        player_radius=config.player_radius,
                    ),
                    config.danger_radius,
                )
                for frame in range(config.horizon_frames + 1)
            ]
        )
        np.testing.assert_allclose(actual, expected, atol=3e-5)

    def test_sparse_aabb_volume_matches_dense_geometry_below_cap(
        self,
    ) -> None:
        grid_x, grid_y = np.meshgrid(
            np.arange(0.0, 49.0, 8.0, dtype=np.float32),
            np.arange(0.0, 41.0, 8.0, dtype=np.float32),
        )
        hazards = (
            MovingAabbHazard(
                x=-5.0,
                y=4.0,
                velocity_x=2.5,
                velocity_y=1.25,
                half_width=3.0,
                half_height=5.0,
                base_uncertainty=0.5,
                uncertainty_per_frame=0.25,
            ),
            MovingAabbHazard(
                x=52.0,
                y=36.0,
                velocity_x=-1.5,
                velocity_y=-2.0,
                half_width=7.0,
                half_height=2.0,
            ),
        )
        cap = 12.0
        actual = _aabb_clearance_volume(
            grid_x,
            grid_y,
            hazards,
            horizon_frames=8,
            player_radius=2.0,
            clearance_cap=cap,
        )
        dense = np.stack(
            [
                _aabb_clearance_field(
                    grid_x,
                    grid_y,
                    hazards,
                    frame=frame,
                    player_radius=2.0,
                )
                for frame in range(9)
            ]
        )
        np.testing.assert_allclose(
            actual,
            np.minimum(dense, cap),
            atol=2e-5,
        )

    def test_vectorized_segment_field_matches_scalar_finite_geometry(
        self,
    ) -> None:
        grid_x, grid_y = np.meshgrid(
            np.asarray([0.0, 10.0, 20.0], dtype=np.float32),
            np.asarray([0.0, 10.0], dtype=np.float32),
        )
        hazards = (
            SegmentHazard(0.0, 0.0, 0.0, 0.0, 20.0, 2.0, 1.0, 0.5),
            SegmentHazard(
                10.0,
                -10.0,
                math.pi / 2.0,
                0.0,
                20.0,
                1.0,
            ),
            SegmentHazard(20.0, 10.0, 0.0, 0.0, 0.0, 3.0),
        )
        actual = _segment_clearance_field(
            grid_x,
            grid_y,
            hazards,
            frame=4,
            player_radius=2.0,
        )
        expected = np.full(grid_x.shape, np.inf, dtype=np.float64)
        for hazard in hazards:
            cosine = math.cos(hazard.angle)
            sine = math.sin(hazard.angle)
            start_x = hazard.origin_x + cosine * hazard.tail
            start_y = hazard.origin_y + sine * hazard.tail
            end_x = hazard.origin_x + cosine * hazard.head
            end_y = hazard.origin_y + sine * hazard.head
            segment_x = end_x - start_x
            segment_y = end_y - start_y
            length_sq = segment_x**2 + segment_y**2
            if length_sq <= 1e-9:
                distance = np.hypot(grid_x - start_x, grid_y - start_y)
            else:
                projection = np.clip(
                    (
                        (grid_x - start_x) * segment_x
                        + (grid_y - start_y) * segment_y
                    )
                    / length_sq,
                    0.0,
                    1.0,
                )
                distance = np.hypot(
                    grid_x - (start_x + projection * segment_x),
                    grid_y - (start_y + projection * segment_y),
                )
            expected = np.minimum(
                expected,
                distance
                - hazard.half_width
                - 2.0
                - hazard.base_uncertainty
                - hazard.uncertainty_per_frame * 4,
            )
        np.testing.assert_allclose(actual, expected, atol=2e-5)

    def test_time_indexed_segment_only_blocks_present_frames(self) -> None:
        segment = SegmentHazard(0.0, 48.0, 0.0, 0.0, 96.0, 2.0)
        trajectory = SegmentTrajectoryHazard((None, segment, None))
        grid_x, grid_y = np.meshgrid(
            np.asarray([40.0, 48.0], dtype=np.float32),
            np.asarray([40.0, 48.0], dtype=np.float32),
        )
        config = CorridorConfig(
            grid_step=8.0,
            frames_per_layer=1,
            horizon_frames=2,
            danger_radius=12.0,
        )
        volume = _hazard_clearance_volume(
            grid_x,
            grid_y,
            aabbs=(),
            segments=(),
            segment_trajectories=(trajectory,),
            config=config,
        )
        self.assertGreater(volume[0, 1, 1], 0.0)
        self.assertLessEqual(volume[1, 1, 1], 0.0)
        self.assertGreater(volume[2, 1, 1], 0.0)

    def test_time_indexed_aabb_follows_piecewise_samples(self) -> None:
        trajectory = AabbTrajectoryHazard(
            (
                AabbHazard(8.0, 8.0, 2.0, 3.0),
                AabbHazard(40.0, 40.0, 2.0, 3.0),
                None,
            )
        )
        grid_x, grid_y = np.meshgrid(
            np.asarray([8.0, 40.0], dtype=np.float32),
            np.asarray([8.0, 40.0], dtype=np.float32),
        )
        config = CorridorConfig(
            grid_step=32.0,
            frames_per_layer=1,
            horizon_frames=2,
            danger_radius=12.0,
        )
        volume = _hazard_clearance_volume(
            grid_x,
            grid_y,
            aabbs=(),
            aabb_trajectories=(trajectory,),
            segments=(),
            segment_trajectories=(),
            config=config,
        )
        self.assertLessEqual(volume[0, 0, 0], 0.0)
        self.assertGreater(volume[0, 1, 1], 0.0)
        self.assertGreater(volume[1, 0, 0], 0.0)
        self.assertLessEqual(volume[1, 1, 1], 0.0)
        self.assertGreater(volume[2, 0, 0], 0.0)
        self.assertGreater(volume[2, 1, 1], 0.0)

    @unittest.skipUnless(
        native_available(),
        "native planner backend is not built",
    )
    def test_native_time_indexed_aabbs_match_framewise_geometry(self) -> None:
        grid_x, grid_y = np.meshgrid(
            np.arange(0.0, 49.0, 8.0, dtype=np.float32),
            np.arange(0.0, 41.0, 8.0, dtype=np.float32),
        )
        trajectories = (
            AabbTrajectoryHazard(
                (
                    None,
                    AabbHazard(8.0, 8.0, 2.0, 3.0),
                    AabbHazard(16.0, 14.0, 4.0, 1.0, 0.5, 0.1),
                    None,
                    AabbHazard(36.0, 28.0, 3.0, 5.0, 0.25),
                )
            ),
            AabbTrajectoryHazard(
                tuple(
                    AabbHazard(
                        42.0 - frame * 2.0,
                        4.0 + frame * 3.0,
                        1.0 + frame * 0.25,
                        2.0,
                        0.2,
                    )
                    for frame in range(5)
                )
            ),
        )
        config = CorridorConfig(
            grid_step=8.0,
            frames_per_layer=1,
            horizon_frames=4,
            danger_radius=12.0,
        )
        reference = np.full(
            (5, *grid_x.shape),
            config.danger_radius,
            dtype=np.float32,
        )
        for frame in range(5):
            samples = tuple(
                sample
                for trajectory in trajectories
                if (sample := trajectory.sample(frame)) is not None
            )
            reference[frame] = np.minimum(
                reference[frame],
                _aabb_sample_clearance_field(
                    grid_x,
                    grid_y,
                    samples,
                    frame=frame,
                    player_radius=config.player_radius,
                ),
            )
        with patch(
            (
                "touhou_control.corridor.clearance."
                "_aabb_sample_clearance_field"
            ),
            side_effect=AssertionError(
                "native AABB trajectory path fell back to Python geometry"
            ),
        ):
            actual = _hazard_clearance_volume(
                grid_x,
                grid_y,
                aabbs=(),
                aabb_trajectories=trajectories,
                segments=(),
                segment_trajectories=(),
                config=config,
            )
        np.testing.assert_allclose(actual, reference, atol=3e-5)

    @unittest.skipUnless(
        native_available(),
        "native planner backend is not built",
    )
    def test_native_sparse_piecewise_aabbs_match_scalar_samples(self) -> None:
        grid_x, grid_y = np.meshgrid(
            np.arange(0.0, 49.0, 8.0, dtype=np.float32),
            np.arange(0.0, 41.0, 8.0, dtype=np.float32),
        )
        trajectories = (
            PiecewiseAabbHazard(
                motion=PiecewiseLinearTrajectory(
                    8.0,
                    8.0,
                    3.0,
                    1.0,
                    (
                        VelocityChange(2, 0.0, 0.0),
                        VelocityChange(4, -2.0, 3.0),
                    ),
                ),
                half_width=2.0,
                half_height=3.0,
                base_uncertainty=0.25,
                uncertainty_per_frame=0.1,
            ),
            PiecewiseAabbHazard(
                motion=PiecewiseLinearTrajectory(
                    44.0,
                    36.0,
                    -1.5,
                    -2.0,
                    (VelocityChange(3, 2.0, -1.0),),
                ),
                half_width=4.0,
                half_height=1.0,
            ),
        )
        config = CorridorConfig(
            grid_step=8.0,
            frames_per_layer=1,
            horizon_frames=5,
            danger_radius=12.0,
        )
        reference = np.full(
            (6, *grid_x.shape),
            config.danger_radius,
            dtype=np.float32,
        )
        for frame in range(6):
            reference[frame] = np.minimum(
                reference[frame],
                _aabb_sample_clearance_field(
                    grid_x,
                    grid_y,
                    tuple(trajectory.sample(frame) for trajectory in trajectories),
                    frame=frame,
                    player_radius=config.player_radius,
                ),
            )
        with patch(
            (
                "touhou_control.corridor.clearance."
                "_aabb_sample_clearance_field"
            ),
            side_effect=AssertionError(
                "native piecewise path fell back to Python geometry"
            ),
        ):
            actual = _hazard_clearance_volume(
                grid_x,
                grid_y,
                aabbs=(),
                piecewise_aabbs=trajectories,
                segments=(),
                segment_trajectories=(),
                config=config,
            )
        np.testing.assert_allclose(actual, reference, atol=3e-5)

    @unittest.skipUnless(
        native_available(),
        "native planner backend is not built",
    )
    def test_native_time_indexed_segments_match_framewise_geometry(self) -> None:
        grid_x, grid_y = np.meshgrid(
            np.arange(0.0, 49.0, 8.0, dtype=np.float32),
            np.arange(0.0, 41.0, 8.0, dtype=np.float32),
        )
        aabbs = (
            MovingAabbHazard(
                x=20.0,
                y=4.0,
                velocity_x=-0.5,
                velocity_y=1.25,
                half_width=2.0,
                half_height=3.0,
                base_uncertainty=0.25,
                uncertainty_per_frame=0.2,
            ),
        )
        static_segments = (
            SegmentHazard(
                4.0,
                32.0,
                0.0,
                0.0,
                38.0,
                1.5,
                0.5,
                0.1,
            ),
        )
        trajectories = (
            SegmentTrajectoryHazard(
                (
                    None,
                    SegmentHazard(8.0, 8.0, 0.2, -4.0, 22.0, 2.0),
                    SegmentHazard(
                        10.0,
                        10.0,
                        0.5,
                        -2.0,
                        28.0,
                        2.5,
                        0.4,
                        0.3,
                    ),
                    None,
                    SegmentHazard(24.0, 16.0, 1.2, 0.0, 0.0, 4.0),
                )
            ),
            SegmentTrajectoryHazard(
                tuple(
                    SegmentHazard(
                        42.0 - frame,
                        4.0 + frame * 3.0,
                        1.8 - frame * 0.13,
                        -8.0,
                        30.0,
                        1.0 + frame * 0.2,
                        0.2,
                    )
                    for frame in range(5)
                )
            ),
        )
        config = CorridorConfig(
            grid_step=8.0,
            frames_per_layer=1,
            horizon_frames=4,
            danger_radius=12.0,
        )
        reference = _aabb_clearance_volume(
            grid_x,
            grid_y,
            aabbs,
            horizon_frames=4,
            player_radius=config.player_radius,
            clearance_cap=config.danger_radius,
        )
        for frame in range(5):
            frame_segments = static_segments + tuple(
                sample
                for trajectory in trajectories
                if (sample := trajectory.sample(frame)) is not None
            )
            reference[frame] = np.minimum(
                reference[frame],
                _segment_clearance_field(
                    grid_x,
                    grid_y,
                    frame_segments,
                    frame=frame,
                    player_radius=config.player_radius,
                ),
            )
        with patch(
            (
                "touhou_control.corridor.clearance."
                "_segment_clearance_field"
            ),
            side_effect=AssertionError(
                "native trajectory path fell back to Python geometry"
            ),
        ):
            actual = _hazard_clearance_volume(
                grid_x,
                grid_y,
                aabbs=aabbs,
                segments=static_segments,
                segment_trajectories=trajectories,
                config=config,
            )
        np.testing.assert_allclose(actual, reference, atol=3e-5)

    @unittest.skipUnless(
        native_available(),
        "native planner backend is not built",
    )
    def test_packed_segments_are_bit_identical_to_object_adapter(self) -> None:
        grid_x, grid_y = np.meshgrid(
            np.arange(0.0, 65.0, 4.0, dtype=np.float32),
            np.arange(0.0, 49.0, 4.0, dtype=np.float32),
        )
        trajectories = (
            SegmentTrajectoryHazard(
                (
                    None,
                    SegmentHazard(8.0, 8.0, 0.2, -4.0, 22.0, 2.0),
                    SegmentHazard(10.0, 12.0, 0.5, -2.0, 28.0, 2.5),
                    None,
                )
            ),
            SegmentTrajectoryHazard(
                tuple(
                    SegmentHazard(
                        52.0 - frame,
                        4.0 + frame * 3.0,
                        1.8 - frame * 0.13,
                        -8.0,
                        30.0,
                        1.0 + frame * 0.2,
                        0.2,
                    )
                    for frame in range(4)
                )
            ),
        )
        config = CorridorConfig(
            grid_step=4.0,
            frames_per_layer=1,
            horizon_frames=3,
            danger_radius=16.0,
        )
        object_volume = _hazard_clearance_volume(
            grid_x,
            grid_y,
            aabbs=(),
            segments=(),
            segment_trajectories=trajectories,
            config=config,
        )
        packed_volume = _hazard_clearance_volume(
            grid_x,
            grid_y,
            aabbs=(),
            segments=(),
            segment_trajectories=(),
            packed_segments=PackedSegmentFrames.from_trajectories(
                trajectories,
                frame_count=4,
            ),
            config=config,
        )
        np.testing.assert_array_equal(packed_volume, object_volume)

    def test_packed_and_object_segments_produce_same_policy_and_rollout(
        self,
    ) -> None:
        trajectories = (
            SegmentTrajectoryHazard(
                tuple(
                    SegmentHazard(
                        8.0 + frame,
                        16.0,
                        0.15,
                        0.0,
                        30.0,
                        1.0,
                    )
                    for frame in range(9)
                )
            ),
        )
        config = CorridorConfig(
            grid_step=8.0,
            frames_per_layer=2,
            horizon_frames=8,
            cardinal_speed=4.0,
            diagonal_axis_speed=2.8284270763397217,
            danger_radius=16.0,
        )
        robust = RobustControlSpec(
            actions=(
                ControlAction("stay", 0.0, 0.0),
                ControlAction("left", -4.0, 0.0),
                ControlAction("right", 4.0, 0.0),
            ),
            delay_frames=(0, 1),
            nominal_delay=1,
            active_action="stay",
        )
        object_plan = plan_corridor(
            start_x=48.0,
            start_y=88.0,
            bounds=BOUNDS,
            segment_trajectories=trajectories,
            preferred_x=32.0,
            preferred_y=64.0,
            config=config,
            robust_control=robust,
        )
        packed_plan = plan_corridor(
            start_x=48.0,
            start_y=88.0,
            bounds=BOUNDS,
            packed_segments=PackedSegmentFrames.from_trajectories(
                trajectories,
                frame_count=9,
            ),
            preferred_x=32.0,
            preferred_y=64.0,
            config=config,
            robust_control=robust,
        )
        self.assertEqual(packed_plan.path, object_plan.path)
        self.assertEqual(
            (
                packed_plan.reachable,
                packed_plan.bottleneck_clearance,
                packed_plan.terminal_clearance,
                packed_plan.lane,
                packed_plan.gate,
                packed_plan.initial_safe_action_count,
                packed_plan.initial_repair_volume,
            ),
            (
                object_plan.reachable,
                object_plan.bottleneck_clearance,
                object_plan.terminal_clearance,
                object_plan.lane,
                object_plan.gate,
                object_plan.initial_safe_action_count,
                object_plan.initial_repair_volume,
            ),
        )
        assert packed_plan.viability_policy is not None
        assert object_plan.viability_policy is not None
        np.testing.assert_array_equal(
            packed_plan.viability_policy.viable,
            object_plan.viability_policy.viable,
        )
        np.testing.assert_array_equal(
            packed_plan.viability_policy.safe_action_masks,
            object_plan.viability_policy.safe_action_masks,
        )

    def test_packed_segment_horizon_mismatch_is_rejected(self) -> None:
        grid_x, grid_y = np.meshgrid(
            np.asarray([0.0, 8.0], dtype=np.float32),
            np.asarray([0.0, 8.0], dtype=np.float32),
        )
        with self.assertRaisesRegex(ValueError, "planning horizon"):
            _hazard_clearance_volume(
                grid_x,
                grid_y,
                aabbs=(),
                segments=(),
                segment_trajectories=(),
                packed_segments=PackedSegmentFrames.empty(2),
                config=CorridorConfig(
                    grid_step=8.0,
                    frames_per_layer=1,
                    horizon_frames=2,
                ),
            )

    def test_clear_field_reaches_preferred_region_without_touching_boundary(self) -> None:
        plan = plan_corridor(
            start_x=48.0,
            start_y=88.0,
            bounds=BOUNDS,
            preferred_x=48.0,
            preferred_y=64.0,
            config=CONFIG,
        )
        self.assertTrue(plan.reachable)
        self.assertGreater(plan.path[-1].y, 0.0)
        self.assertLess(plan.path[-1].y, 96.0)
        self.assertGreater(plan.bottleneck_clearance, 0.0)

    def test_future_wall_commits_to_open_left_corridor(self) -> None:
        hazards = tuple(
            MovingAabbHazard(
                x=float(x),
                y=30.0,
                velocity_x=0.0,
                velocity_y=1.5,
                half_width=5.0,
                half_height=5.0,
            )
            for x in range(32, 97, 8)
        )
        plan = plan_corridor(
            start_x=48.0,
            start_y=88.0,
            bounds=BOUNDS,
            aabbs=hazards,
            preferred_x=48.0,
            preferred_y=64.0,
            config=CONFIG,
        )
        self.assertTrue(plan.reachable)
        self.assertEqual(plan.lane, "left")
        self.assertIsNotNone(plan.gate)
        assert plan.gate is not None
        self.assertLess(plan.gate.x, 32.0)
        self.assertTrue(any(point.x < 32.0 for point in plan.path))

    def test_long_horizon_sees_gate_before_local_horizon_does(self) -> None:
        hazards = tuple(
            MovingAabbHazard(
                x=float(x),
                y=30.0,
                velocity_x=0.0,
                velocity_y=1.5,
                half_width=5.0,
                half_height=5.0,
            )
            for x in range(32, 97, 8)
        )
        local = plan_corridor(
            start_x=48.0,
            start_y=88.0,
            bounds=BOUNDS,
            aabbs=hazards,
            preferred_x=48.0,
            preferred_y=64.0,
            config=CorridorConfig(
                grid_step=8.0,
                frames_per_layer=4,
                horizon_frames=8,
                cardinal_speed=4.0,
                diagonal_axis_speed=2.8284270763397217,
                preferred_clearance=6.0,
            ),
        )
        global_plan = plan_corridor(
            start_x=48.0,
            start_y=88.0,
            bounds=BOUNDS,
            aabbs=hazards,
            preferred_x=48.0,
            preferred_y=64.0,
            config=CONFIG,
        )
        self.assertEqual(local.lane, "center")
        self.assertTrue(all(point.x >= 32.0 for point in local.path))
        self.assertEqual(global_plan.lane, "left")
        self.assertTrue(any(point.x < 32.0 for point in global_plan.path))

    def test_closed_sweeping_wall_proves_corridor_unreachable(self) -> None:
        hazards = tuple(
            MovingAabbHazard(
                x=float(x),
                y=48.0,
                velocity_x=0.0,
                velocity_y=0.0,
                half_width=6.0,
                half_height=50.0,
            )
            for x in range(0, 97, 8)
        )
        plan = plan_corridor(
            start_x=48.0,
            start_y=88.0,
            bounds=BOUNDS,
            aabbs=hazards,
            config=CONFIG,
        )
        self.assertFalse(plan.reachable)
        self.assertEqual(plan.path, ())
        self.assertIsNone(plan.gate)

    def test_required_gate_lane_selects_a_stable_component(self) -> None:
        constrained_config = CorridorConfig(
            grid_step=8.0,
            frames_per_layer=4,
            horizon_frames=32,
            cardinal_speed=4.0,
            diagonal_axis_speed=2.8284270763397217,
            preferred_clearance=20.0,
        )
        plan = plan_corridor(
            start_x=48.0,
            start_y=88.0,
            bounds=BOUNDS,
            preferred_x=48.0,
            preferred_y=64.0,
            required_gate_lane="right",
            config=constrained_config,
        )
        self.assertTrue(plan.reachable)
        self.assertEqual(plan.lane, "right")
        self.assertLess(
            plan.bottleneck_clearance,
            constrained_config.preferred_clearance,
        )
        self.assertIn("commitment", plan.reason)

    def test_required_closed_gate_lane_fails_instead_of_switching(self) -> None:
        hazards = tuple(
            MovingAabbHazard(
                x=float(x),
                y=48.0,
                velocity_x=0.0,
                velocity_y=0.0,
                half_width=4.0,
                half_height=50.0,
            )
            for x in range(32, 65, 8)
        )
        plan = plan_corridor(
            start_x=16.0,
            start_y=88.0,
            bounds=BOUNDS,
            aabbs=hazards,
            required_gate_lane="center",
            config=CONFIG,
        )
        self.assertFalse(plan.reachable)
        self.assertIn("required center", plan.reason)

    def test_waypoint_uses_first_point_at_or_after_requested_frame(self) -> None:
        plan = plan_corridor(
            start_x=48.0,
            start_y=88.0,
            bounds=BOUNDS,
            preferred_x=48.0,
            preferred_y=64.0,
            config=CONFIG,
        )
        self.assertEqual(plan.waypoint(9).frame, 12)
        self.assertEqual(plan.waypoint(999), plan.path[-1])

    def test_robust_mode_returns_backward_policy_not_only_waypoint(self) -> None:
        actions = (
            ControlAction("stay", 0.0, 0.0),
            ControlAction("left", -4.0, 0.0),
            ControlAction("right", 4.0, 0.0),
        )
        plan = plan_corridor(
            start_x=48.0,
            start_y=88.0,
            bounds=BOUNDS,
            preferred_x=32.0,
            preferred_y=64.0,
            config=CONFIG,
            robust_control=RobustControlSpec(
                actions=actions,
                delay_frames=(0, 1, 2),
                nominal_delay=1,
                active_action="stay",
            ),
        )
        self.assertTrue(plan.reachable)
        self.assertEqual(plan.planning_mode, "robust_viability")
        self.assertIsNotNone(plan.viability_policy)
        self.assertGreater(plan.initial_safe_action_count, 0)
        self.assertGreater(plan.initial_repair_volume, 0)
        assert plan.viability_policy is not None
        query = plan.viability_policy.query(
            frame=4,
            x=plan.path[1].x,
            y=plan.path[1].y,
            active_action=plan.path[1].x < 48.0 and "left" or "stay",
        )
        self.assertTrue(query.available)

    def test_robust_mode_can_attach_compact_safety_value_fallback(
        self,
    ) -> None:
        actions = (
            ControlAction("stay", 0.0, 0.0),
            ControlAction("left", -4.0, 0.0),
            ControlAction("right", 4.0, 0.0),
        )
        plan = plan_corridor(
            start_x=48.0,
            start_y=88.0,
            bounds=BOUNDS,
            config=CONFIG,
            robust_control=RobustControlSpec(
                actions=actions,
                delay_frames=(0, 1, 2),
                nominal_delay=1,
                active_action="stay",
                safety_value_horizon_frames=16,
            ),
        )
        self.assertIsNotNone(plan.safety_value_policy)
        assert plan.safety_value_policy is not None
        query = plan.safety_value_policy.query(
            frame=0,
            x=48.0,
            y=88.0,
            active_action="stay",
        )
        self.assertTrue(query.available)
        self.assertTrue(query.best_actions)
        self.assertEqual(query.action_values, ())
        self.assertIn(
            "safety_value",
            dict(plan.solver_timing_ms),
        )

    def test_robust_mode_proves_initial_action_set_empty(self) -> None:
        wall = (
            MovingAabbHazard(
                x=48.0,
                y=88.0,
                velocity_x=0.0,
                velocity_y=0.0,
                half_width=8.0,
                half_height=8.0,
            ),
        )
        plan = plan_corridor(
            start_x=48.0,
            start_y=88.0,
            bounds=BOUNDS,
            aabbs=wall,
            config=CONFIG,
            robust_control=RobustControlSpec(
                actions=(ControlAction("stay", 0.0, 0.0),),
                delay_frames=(0,),
                nominal_delay=0,
                active_action="stay",
            ),
        )
        self.assertFalse(plan.reachable)
        self.assertEqual(plan.planning_mode, "robust_viability")
        self.assertIsNotNone(plan.viability_policy)
        self.assertIn("action set is empty", plan.reason)

    def test_ce_0100_coarse_empty_triggers_generic_full_horizon_refinement(
        self,
    ) -> None:
        bounds = CorridorBounds(0.0, 4.0, 0.0, 2.0)
        config = CorridorConfig(
            grid_step=2.0,
            frames_per_layer=1,
            horizon_frames=2,
            cardinal_speed=1.0,
            diagonal_axis_speed=1.0,
            player_radius=0.0,
            required_clearance=0.0,
        )
        walls = (
            MovingAabbHazard(
                x=0.0,
                y=1.0,
                velocity_x=0.0,
                velocity_y=0.0,
                half_width=0.4,
                half_height=4.0,
            ),
            MovingAabbHazard(
                x=3.0,
                y=1.0,
                velocity_x=0.0,
                velocity_y=0.0,
                half_width=1.4,
                half_height=4.0,
            ),
        )
        plan = plan_corridor(
            start_x=1.0,
            start_y=1.0,
            bounds=bounds,
            aabbs=walls,
            config=config,
            robust_control=RobustControlSpec(
                actions=(ControlAction("stay", 0.0, 0.0),),
                delay_frames=(0,),
                nominal_delay=0,
                active_action="stay",
                refinement_grid_steps=(1.0,),
            ),
        )
        self.assertTrue(plan.reachable)
        self.assertEqual(plan.viability_grid_step, 1.0)
        self.assertIsNotNone(plan.viability_policy)
        assert plan.viability_policy is not None
        self.assertTrue(
            plan.viability_policy.query(
                frame=0,
                x=1.0,
                y=1.0,
                active_action="stay",
            ).state_viable
        )
        self.assertGreater(
            dict(plan.solver_timing_ms)["refinement_clearance"],
            0.0,
        )

    def test_representative_rollout_mismatch_degrades_without_crashing(
        self,
    ) -> None:
        start = ViabilityQuery(
            True,
            0,
            1,
            1,
            "stay",
            True,
            ("stay",),
            (("stay", 1),),
            0.0,
            "robust viable actions found",
        )
        mismatch = ViabilityQuery(
            True,
            0,
            1,
            1,
            "stay",
            False,
            (),
            (),
            0.0,
            "robust action set is empty",
        )
        policy = Mock()
        policy.query.side_effect = (start, mismatch)
        policy.backend = "test"
        policy.layer_count = 1
        with patch(
            "touhou_control.corridor.robust."
            "build_robust_viability_policy",
            return_value=policy,
        ):
            plan = plan_corridor(
                start_x=48.0,
                start_y=48.0,
                bounds=BOUNDS,
                config=CONFIG,
                robust_control=RobustControlSpec(
                    actions=(ControlAction("stay", 0.0, 0.0),),
                    delay_frames=(0,),
                    nominal_delay=0,
                    active_action="stay",
                ),
            )
        self.assertFalse(plan.reachable)
        self.assertIs(plan.viability_policy, policy)
        self.assertIn("representative rollout", plan.reason)


if __name__ == "__main__":
    unittest.main()
