"""Robust corridor induction and optional legacy refinement."""

from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np

from ..query_survival import SurvivalQueryProblem
from ..viability import (
    RobustSafetyValuePolicy,
    RobustViabilityPolicy,
    ViabilityConfig,
    ViabilityQuery,
    build_robust_safety_value_policy,
    build_robust_viability_policy,
)
from .model import CorridorConfig
from .prepared import PreparedCorridorProblem
from .refinement import LegacyFullFieldRefinement


@dataclass(frozen=True)
class RobustCorridorInduction:
    """Boolean kernel and retained inputs before representative rollout."""

    config: CorridorConfig
    x_axis: np.ndarray
    y_axis: np.ndarray
    clearance_volume: np.ndarray
    policy: RobustViabilityPolicy
    safety_value_policy: RobustSafetyValuePolicy | None
    survival_policy: RobustViabilityPolicy | None
    survival_query_problem: SurvivalQueryProblem | None
    start_query: ViabilityQuery
    base_timing_ms: tuple[tuple[str, float], ...]
    rollout_started_at: float


def build_robust_corridor_induction(
    *,
    prepared_problem: PreparedCorridorProblem,
    start_x: float,
    start_y: float,
    pre_viability_elapsed_ms: float = 0.0,
) -> RobustCorridorInduction:
    """Build the robust kernel without selecting a representative path."""

    control = prepared_problem.robust_control
    config = prepared_problem.config
    x_axis = prepared_problem.x_axis
    y_axis = prepared_problem.y_axis
    clearance_volume = prepared_problem.clearance_volume
    survival_query_problem = prepared_problem.survival_query_problem

    viability_started = time.perf_counter()
    policy = build_robust_viability_policy(
        x_axis=x_axis,
        y_axis=y_axis,
        clearance_volume=clearance_volume,
        actions=control.actions,
        delay_frames=control.delay_frames,
        nominal_delay=control.nominal_delay,
        config=prepared_problem.viability_config,
        terminal_viable=control.terminal_viable,
        survival_labels=control.survival_labels,
    )
    viability_finished = time.perf_counter()
    survival_policy = policy if control.survival_labels else None
    start_query = policy.query(
        frame=0,
        x=start_x,
        y=start_y,
        active_action=control.active_action,
    )

    refinement = LegacyFullFieldRefinement(
        control.refinement_grid_steps
    ).run(
        prepared_problem=prepared_problem,
        start_x=start_x,
        start_y=start_y,
        policy=policy,
        start_query=start_query,
    )
    config = refinement.config
    x_axis = refinement.x_axis
    y_axis = refinement.y_axis
    clearance_volume = refinement.clearance_volume
    policy = refinement.policy
    start_query = refinement.start_query

    if (
        survival_query_problem is None
        and control.retain_query_survival_problem
        and control.terminal_viable is None
    ):
        survival_query_problem = SurvivalQueryProblem(
            x_axis=x_axis,
            y_axis=y_axis,
            clearance_volume=clearance_volume,
            actions=control.actions,
            delay_frames=control.delay_frames,
            nominal_delay=control.nominal_delay,
            config=ViabilityConfig(
                frames_per_layer=config.frames_per_layer,
                required_clearance=config.required_clearance,
                clamp_to_bounds=True,
                repair_radius_cells=1,
            ),
        )

    safety_value_policy = None
    safety_value_started = time.perf_counter()
    safety_value_finished = safety_value_started
    safety_value_horizon = control.safety_value_horizon_frames
    if safety_value_horizon:
        if (
            safety_value_horizon > config.horizon_frames
            or safety_value_horizon % config.frames_per_layer
        ):
            raise ValueError(
                "safety-value horizon must fit the corridor horizon and "
                "contain complete control layers"
            )
        safety_value_policy = build_robust_safety_value_policy(
            x_axis=x_axis,
            y_axis=y_axis,
            clearance_volume=clearance_volume[
                : safety_value_horizon + 1
            ],
            actions=control.actions,
            delay_frames=control.delay_frames,
            nominal_delay=control.nominal_delay,
            config=ViabilityConfig(
                frames_per_layer=config.frames_per_layer,
                required_clearance=config.required_clearance,
                clamp_to_bounds=True,
            ),
            compact=True,
        )
        safety_value_finished = time.perf_counter()

    return RobustCorridorInduction(
        config=config,
        x_axis=x_axis,
        y_axis=y_axis,
        clearance_volume=clearance_volume,
        policy=policy,
        safety_value_policy=safety_value_policy,
        survival_policy=survival_policy,
        survival_query_problem=survival_query_problem,
        start_query=start_query,
        base_timing_ms=(
            ("clearance", prepared_problem.clearance_ms),
            (
                "viability",
                (viability_finished - viability_started) * 1000.0,
            ),
            (
                "pre_viability_hook",
                prepared_problem.query_problem_ms
                + pre_viability_elapsed_ms,
            ),
            (
                "safety_value",
                (
                    safety_value_finished - safety_value_started
                )
                * 1000.0,
            ),
            (
                "refinement_clearance",
                refinement.clearance_ms,
            ),
            (
                "refinement_viability",
                refinement.viability_ms,
            ),
        ),
        rollout_started_at=safety_value_finished,
    )


__all__ = [
    "RobustCorridorInduction",
    "build_robust_corridor_induction",
]
