#!/usr/bin/env python3
"""Compatibility façade for game-neutral safe-corridor planning."""

from __future__ import annotations

import math
import time

from touhou_control.corridor.clearance import (
    _aabb_clearance_field,
    _aabb_clearance_volume,
    _aabb_sample_clearance_field,
    _clearance_field,
    _hazard_clearance_volume,
    _packed_segment_clearance_field,
    _segment_clearance_field,
)
from touhou_control.corridor.grid import (
    axis as _axis,
    lane as _lane,
    movement_offsets as _movement_offsets,
    shift_from_source as _shift_from_source,
)
from touhou_control.corridor.legacy_forward import (
    plan_legacy_forward_corridor,
)
from touhou_control.corridor.model import (
    AabbHazard,
    AabbTrajectoryHazard,
    CorridorBounds,
    CorridorConfig,
    CorridorPlan,
    CorridorPoint,
    MovingAabbHazard,
    PiecewiseAabbHazard,
    RobustControlSpec,
    SegmentHazard,
    SegmentTrajectoryHazard,
)
from touhou_control.corridor.prepared import (
    PreparedCorridorProblem,
    prepare_corridor_problem,
)
from touhou_control.corridor.robust import (
    build_robust_corridor_induction,
)
from touhou_control.corridor.rollout import rollout_robust_corridor
from touhou_control.packed_hazards import PackedSegmentFrames


def plan_prepared_corridor(
    *,
    start_x: float,
    start_y: float,
    prepared_problem: PreparedCorridorProblem,
    preferred_x: float | None = None,
    preferred_y: float | None = None,
    required_gate_lane: str | None = None,
    pre_viability_elapsed_ms: float = 0.0,
) -> CorridorPlan:
    """Solve one explicitly prepared robust corridor problem.

    Runtime services may be started before this call. The solver itself owns
    no callback or service lifecycle.
    """

    if required_gate_lane not in (None, "left", "center", "right"):
        raise ValueError("required gate lane must be left, center, or right")
    bounds = prepared_problem.bounds
    if not (
        bounds.left <= start_x <= bounds.right
        and bounds.top <= start_y <= bounds.bottom
    ):
        raise ValueError("corridor start is outside bounds")
    if (
        not math.isfinite(pre_viability_elapsed_ms)
        or pre_viability_elapsed_ms < 0.0
    ):
        raise ValueError(
            "pre-viability elapsed time must be finite and nonnegative"
        )
    induction = build_robust_corridor_induction(
        prepared_problem=prepared_problem,
        start_x=start_x,
        start_y=start_y,
        pre_viability_elapsed_ms=pre_viability_elapsed_ms,
    )
    return rollout_robust_corridor(
        prepared_problem=prepared_problem,
        induction=induction,
        start_x=start_x,
        start_y=start_y,
        preferred_x=preferred_x,
        preferred_y=preferred_y,
        required_gate_lane=required_gate_lane,
    )


def plan_corridor(
    *,
    start_x: float,
    start_y: float,
    bounds: CorridorBounds,
    aabbs: tuple[MovingAabbHazard, ...] = (),
    aabb_trajectories: tuple[AabbTrajectoryHazard, ...] = (),
    piecewise_aabbs: tuple[PiecewiseAabbHazard, ...] = (),
    segments: tuple[SegmentHazard, ...] = (),
    segment_trajectories: tuple[SegmentTrajectoryHazard, ...] = (),
    packed_segments: PackedSegmentFrames | None = None,
    preferred_x: float | None = None,
    preferred_y: float | None = None,
    required_gate_lane: str | None = None,
    config: CorridorConfig = CorridorConfig(),
    robust_control: RobustControlSpec | None = None,
) -> CorridorPlan:
    """Dispatch to legacy forward or robust prepared corridor planning."""

    if required_gate_lane not in (None, "left", "center", "right"):
        raise ValueError("required gate lane must be left, center, or right")
    if not (
        bounds.left <= start_x <= bounds.right
        and bounds.top <= start_y <= bounds.bottom
    ):
        raise ValueError("corridor start is outside bounds")
    if robust_control is not None:
        hook = robust_control.pre_viability_problem_hook
        prepared_problem = prepare_corridor_problem(
            bounds=bounds,
            config=config,
            robust_control=robust_control,
            aabbs=aabbs,
            aabb_trajectories=aabb_trajectories,
            piecewise_aabbs=piecewise_aabbs,
            segments=segments,
            segment_trajectories=segment_trajectories,
            packed_segments=packed_segments,
        )
        hook_elapsed_ms = 0.0
        if hook is not None:
            assert prepared_problem.survival_query_problem is not None
            hook_started = time.perf_counter()
            hook(prepared_problem.survival_query_problem)
            hook_elapsed_ms = (
                time.perf_counter() - hook_started
            ) * 1000.0
        return plan_prepared_corridor(
            start_x=start_x,
            start_y=start_y,
            prepared_problem=prepared_problem,
            preferred_x=preferred_x,
            preferred_y=preferred_y,
            required_gate_lane=required_gate_lane,
            pre_viability_elapsed_ms=hook_elapsed_ms,
        )
    return plan_legacy_forward_corridor(
        start_x=start_x,
        start_y=start_y,
        bounds=bounds,
        aabbs=aabbs,
        aabb_trajectories=aabb_trajectories,
        piecewise_aabbs=piecewise_aabbs,
        segments=segments,
        segment_trajectories=segment_trajectories,
        packed_segments=packed_segments,
        preferred_x=preferred_x,
        preferred_y=preferred_y,
        required_gate_lane=required_gate_lane,
        config=config,
    )
