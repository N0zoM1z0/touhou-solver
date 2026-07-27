"""Historical full-field robust-corridor refinement."""

from __future__ import annotations

import time
from dataclasses import dataclass, replace

import numpy as np

from ..viability import (
    RobustViabilityPolicy,
    ViabilityConfig,
    ViabilityQuery,
    build_robust_viability_policy,
)
from .clearance import hazard_clearance_volume
from .grid import axis
from .model import CorridorConfig
from .prepared import PreparedCorridorProblem


@dataclass(frozen=True)
class LegacyFullFieldRefinementResult:
    config: CorridorConfig
    x_axis: np.ndarray
    y_axis: np.ndarray
    clearance_volume: np.ndarray
    policy: RobustViabilityPolicy
    start_query: ViabilityQuery
    clearance_ms: float
    viability_ms: float


@dataclass(frozen=True)
class LegacyFullFieldRefinement:
    """Uniform whole-field false-empty recovery retained for shadow use."""

    grid_steps: tuple[float, ...]

    def run(
        self,
        *,
        prepared_problem: PreparedCorridorProblem,
        start_x: float,
        start_y: float,
        policy: RobustViabilityPolicy,
        start_query: ViabilityQuery,
    ) -> LegacyFullFieldRefinementResult:
        control = prepared_problem.robust_control
        bounds = prepared_problem.bounds
        config = prepared_problem.config
        x_axis = prepared_problem.x_axis
        y_axis = prepared_problem.y_axis
        clearance_volume = prepared_problem.clearance_volume
        refinement_clearance_ms = 0.0
        refinement_viability_ms = 0.0

        for refinement_step in self.grid_steps:
            if start_query.state_viable:
                break
            if refinement_step >= config.grid_step:
                raise ValueError(
                    "refinement grid step must be smaller than the active grid"
                )
            refined_config = replace(
                config,
                grid_step=refinement_step,
            )
            refinement_started = time.perf_counter()
            refined_x_axis = axis(
                bounds.left,
                bounds.right,
                refined_config.grid_step,
            )
            refined_y_axis = axis(
                bounds.top,
                bounds.bottom,
                refined_config.grid_step,
            )
            refined_grid_x, refined_grid_y = np.meshgrid(
                refined_x_axis,
                refined_y_axis,
            )
            refined_clearance = hazard_clearance_volume(
                refined_grid_x,
                refined_grid_y,
                aabbs=prepared_problem.aabbs,
                aabb_trajectories=(
                    prepared_problem.aabb_trajectories
                ),
                piecewise_aabbs=prepared_problem.piecewise_aabbs,
                segments=prepared_problem.segments,
                segment_trajectories=(
                    prepared_problem.segment_trajectories
                ),
                packed_segments=prepared_problem.packed_segments,
                config=refined_config,
            )
            refinement_clearance_finished = time.perf_counter()
            refined_policy = build_robust_viability_policy(
                x_axis=refined_x_axis,
                y_axis=refined_y_axis,
                clearance_volume=refined_clearance,
                actions=control.actions,
                delay_frames=control.delay_frames,
                nominal_delay=control.nominal_delay,
                config=ViabilityConfig(
                    frames_per_layer=(
                        refined_config.frames_per_layer
                    ),
                    required_clearance=(
                        refined_config.required_clearance
                    ),
                    clamp_to_bounds=True,
                    repair_radius_cells=1,
                ),
                # Fine refinement recovers Boolean false-empties. Retain the
                # coarse fused policy for losing-state labels instead of
                # paying the all-state survival recurrence twice.
                survival_labels=False,
            )
            refinement_finished = time.perf_counter()
            refinement_clearance_ms += (
                refinement_clearance_finished - refinement_started
            ) * 1000.0
            refinement_viability_ms += (
                refinement_finished
                - refinement_clearance_finished
            ) * 1000.0
            config = refined_config
            x_axis = refined_x_axis
            y_axis = refined_y_axis
            clearance_volume = refined_clearance
            policy = refined_policy
            start_query = policy.query(
                frame=0,
                x=start_x,
                y=start_y,
                active_action=control.active_action,
            )

        return LegacyFullFieldRefinementResult(
            config=config,
            x_axis=x_axis,
            y_axis=y_axis,
            clearance_volume=clearance_volume,
            policy=policy,
            start_query=start_query,
            clearance_ms=refinement_clearance_ms,
            viability_ms=refinement_viability_ms,
        )


__all__ = [
    "LegacyFullFieldRefinement",
    "LegacyFullFieldRefinementResult",
]
