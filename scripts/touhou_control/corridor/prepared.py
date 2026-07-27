"""Prepared, callback-free inputs for robust corridor solving."""

from __future__ import annotations

import time
from dataclasses import dataclass, replace

import numpy as np

from ..packed_hazards import PackedSegmentFrames
from ..query_survival import SurvivalQueryProblem
from ..viability import ViabilityConfig
from .clearance import hazard_clearance_volume
from .grid import axis
from .model import (
    AabbTrajectoryHazard,
    CorridorBounds,
    CorridorConfig,
    MovingAabbHazard,
    PiecewiseAabbHazard,
    RobustControlSpec,
    SegmentHazard,
    SegmentTrajectoryHazard,
)


@dataclass(frozen=True)
class PreparedCorridorProblem:
    """One complete coarse robust-planning value before induction.

    The problem deliberately owns no executor, future, service, or callback.
    Runtime orchestration may start optional work from
    ``survival_query_problem`` before invoking the Boolean solver.
    """

    bounds: CorridorBounds
    config: CorridorConfig
    robust_control: RobustControlSpec
    x_axis: np.ndarray
    y_axis: np.ndarray
    clearance_volume: np.ndarray
    viability_config: ViabilityConfig
    survival_query_problem: SurvivalQueryProblem | None
    aabbs: tuple[MovingAabbHazard, ...]
    aabb_trajectories: tuple[AabbTrajectoryHazard, ...]
    piecewise_aabbs: tuple[PiecewiseAabbHazard, ...]
    segments: tuple[SegmentHazard, ...]
    segment_trajectories: tuple[SegmentTrajectoryHazard, ...]
    packed_segments: PackedSegmentFrames | None
    clearance_ms: float
    query_problem_ms: float
    preparation_ms: float

    def __post_init__(self) -> None:
        if self.robust_control.pre_viability_problem_hook is not None:
            raise ValueError("prepared problems cannot retain runtime hooks")
        expected_shape = (
            self.config.horizon_frames + 1,
            len(self.y_axis),
            len(self.x_axis),
        )
        if self.clearance_volume.shape != expected_shape:
            raise ValueError(
                "prepared clearance volume does not match its grid/horizon"
            )


def prepare_corridor_problem(
    *,
    bounds: CorridorBounds,
    config: CorridorConfig,
    robust_control: RobustControlSpec,
    aabbs: tuple[MovingAabbHazard, ...] = (),
    aabb_trajectories: tuple[AabbTrajectoryHazard, ...] = (),
    piecewise_aabbs: tuple[PiecewiseAabbHazard, ...] = (),
    segments: tuple[SegmentHazard, ...] = (),
    segment_trajectories: tuple[SegmentTrajectoryHazard, ...] = (),
    packed_segments: PackedSegmentFrames | None = None,
) -> PreparedCorridorProblem:
    """Lower one complete coarse robust problem without starting services."""

    started = time.perf_counter()
    x_axis = axis(bounds.left, bounds.right, config.grid_step)
    y_axis = axis(bounds.top, bounds.bottom, config.grid_step)
    grid_x, grid_y = np.meshgrid(x_axis, y_axis)
    clearance_volume = hazard_clearance_volume(
        grid_x,
        grid_y,
        aabbs=aabbs,
        aabb_trajectories=aabb_trajectories,
        piecewise_aabbs=piecewise_aabbs,
        segments=segments,
        segment_trajectories=segment_trajectories,
        packed_segments=packed_segments,
        config=config,
    )
    clearance_finished = time.perf_counter()
    viability_config = ViabilityConfig(
        frames_per_layer=config.frames_per_layer,
        required_clearance=config.required_clearance,
        clamp_to_bounds=True,
        repair_radius_cells=1,
    )
    control = replace(
        robust_control,
        pre_viability_problem_hook=None,
    )
    survival_query_problem = (
        SurvivalQueryProblem(
            x_axis=x_axis,
            y_axis=y_axis,
            clearance_volume=clearance_volume,
            actions=control.actions,
            delay_frames=control.delay_frames,
            nominal_delay=control.nominal_delay,
            config=viability_config,
        )
        if (
            control.retain_query_survival_problem
            and control.terminal_viable is None
            and not control.refinement_grid_steps
        )
        else None
    )
    query_problem_finished = time.perf_counter()
    return PreparedCorridorProblem(
        bounds=bounds,
        config=config,
        robust_control=control,
        x_axis=x_axis,
        y_axis=y_axis,
        clearance_volume=clearance_volume,
        viability_config=viability_config,
        survival_query_problem=survival_query_problem,
        aabbs=aabbs,
        aabb_trajectories=aabb_trajectories,
        piecewise_aabbs=piecewise_aabbs,
        segments=segments,
        segment_trajectories=segment_trajectories,
        packed_segments=packed_segments,
        clearance_ms=(clearance_finished - started) * 1000.0,
        query_problem_ms=(
            query_problem_finished - clearance_finished
        )
        * 1000.0,
        preparation_ms=(query_problem_finished - started) * 1000.0,
    )


__all__ = ["PreparedCorridorProblem", "prepare_corridor_problem"]
