"""Data contracts for game-neutral corridor planning."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

import numpy as np

from ..query_survival import SurvivalQueryProblem
from ..trajectory import PiecewiseLinearTrajectory
from ..viability import (
    ControlAction,
    RobustSafetyValuePolicy,
    RobustViabilityPolicy,
)


@dataclass(frozen=True)
class CorridorBounds:
    left: float
    right: float
    top: float
    bottom: float

    def __post_init__(self) -> None:
        if self.left >= self.right or self.top >= self.bottom:
            raise ValueError("corridor bounds must have positive area")


@dataclass(frozen=True)
class MovingAabbHazard:
    x: float
    y: float
    velocity_x: float
    velocity_y: float
    half_width: float
    half_height: float
    base_uncertainty: float = 0.0
    uncertainty_per_frame: float = 0.0

    def __post_init__(self) -> None:
        if min(
            self.half_width,
            self.half_height,
            self.base_uncertainty,
            self.uncertainty_per_frame,
        ) < 0.0:
            raise ValueError(
                "hazard dimensions and uncertainty cannot be negative"
            )


@dataclass(frozen=True)
class AabbHazard:
    """One time-indexed axis-aligned hazard sample."""

    x: float
    y: float
    half_width: float
    half_height: float
    base_uncertainty: float = 0.0
    uncertainty_per_frame: float = 0.0

    def __post_init__(self) -> None:
        if min(
            self.half_width,
            self.half_height,
            self.base_uncertainty,
            self.uncertainty_per_frame,
        ) < 0.0:
            raise ValueError(
                "hazard dimensions and uncertainty cannot be negative"
            )


@dataclass(frozen=True)
class AabbTrajectoryHazard:
    """A finite time-indexed AABB trajectory supplied by a game adapter."""

    samples: tuple[AabbHazard | None, ...]

    def __post_init__(self) -> None:
        if not self.samples:
            raise ValueError("AABB trajectory must contain at least one frame")

    def sample(self, frame: int) -> AabbHazard | None:
        if frame < 0 or frame >= len(self.samples):
            return None
        return self.samples[frame]


@dataclass(frozen=True)
class PiecewiseAabbHazard:
    """A sparse piecewise-linear AABB trajectory.

    Keeping velocity replacements sparse lets native backends project hazards
    without adapters materializing one Python object per hazard per frame.
    """

    motion: PiecewiseLinearTrajectory
    half_width: float
    half_height: float
    base_uncertainty: float = 0.0
    uncertainty_per_frame: float = 0.0

    def __post_init__(self) -> None:
        if min(
            self.half_width,
            self.half_height,
            self.base_uncertainty,
            self.uncertainty_per_frame,
        ) < 0.0:
            raise ValueError(
                "hazard dimensions and uncertainty cannot be negative"
            )

    def sample(self, frame: int) -> AabbHazard | None:
        if frame < 0:
            return None
        x, y = self.motion.position(frame)
        return AabbHazard(
            x=x,
            y=y,
            half_width=self.half_width,
            half_height=self.half_height,
            base_uncertainty=self.base_uncertainty,
            uncertainty_per_frame=self.uncertainty_per_frame,
        )


@dataclass(frozen=True)
class SegmentHazard:
    origin_x: float
    origin_y: float
    angle: float
    tail: float
    head: float
    half_width: float
    base_uncertainty: float = 0.0
    uncertainty_per_frame: float = 0.0

    def __post_init__(self) -> None:
        if min(
            self.half_width,
            self.base_uncertainty,
            self.uncertainty_per_frame,
        ) < 0.0:
            raise ValueError(
                "segment width and uncertainty cannot be negative"
            )


@dataclass(frozen=True)
class SegmentTrajectoryHazard:
    """A finite time-indexed segment trajectory supplied by a game adapter."""

    samples: tuple[SegmentHazard | None, ...]

    def __post_init__(self) -> None:
        if not self.samples:
            raise ValueError(
                "segment trajectory must contain at least one frame"
            )

    def sample(self, frame: int) -> SegmentHazard | None:
        if frame < 0 or frame >= len(self.samples):
            return None
        return self.samples[frame]


@dataclass(frozen=True)
class CorridorConfig:
    grid_step: float = 8.0
    frames_per_layer: int = 4
    horizon_frames: int = 80
    cardinal_speed: float = 4.0
    diagonal_axis_speed: float = 2.8284270763397217
    player_radius: float = 2.0
    required_clearance: float = 0.0
    preferred_clearance: float = 10.0
    danger_radius: float = 48.0
    boundary_danger_radius: float = 24.0
    preferred_position_weight: float = 0.05

    def __post_init__(self) -> None:
        if self.grid_step <= 0.0:
            raise ValueError("grid step must be positive")
        if self.frames_per_layer <= 0 or self.horizon_frames <= 0:
            raise ValueError("corridor horizon fields must be positive")
        if self.horizon_frames % self.frames_per_layer:
            raise ValueError(
                "horizon must be divisible by frames per layer"
            )
        if min(
            self.cardinal_speed,
            self.diagonal_axis_speed,
            self.player_radius,
            self.danger_radius,
            self.boundary_danger_radius,
        ) < 0.0:
            raise ValueError(
                "corridor speeds and radii cannot be negative"
            )


@dataclass(frozen=True)
class CorridorPoint:
    frame: int
    x: float
    y: float
    clearance: float


@dataclass(frozen=True)
class CorridorPlan:
    reachable: bool
    path: tuple[CorridorPoint, ...]
    bottleneck_clearance: float
    terminal_clearance: float
    lane: str
    gate: CorridorPoint | None
    reason: str
    planning_mode: str = "forward_reachability"
    viability_policy: RobustViabilityPolicy | None = None
    safety_value_policy: RobustSafetyValuePolicy | None = None
    survival_policy: RobustViabilityPolicy | None = None
    survival_query_problem: SurvivalQueryProblem | None = None
    initial_safe_action_count: int = 0
    initial_repair_volume: int = 0
    viability_backend: str | None = None
    viability_grid_step: float | None = None
    solver_timing_ms: tuple[tuple[str, float], ...] = ()

    def waypoint(self, frame: int) -> CorridorPoint:
        if not self.path:
            raise ValueError("unreachable corridor has no waypoint")
        for point in self.path:
            if point.frame >= frame:
                return point
        return self.path[-1]


@dataclass(frozen=True)
class RobustControlSpec:
    actions: tuple[ControlAction, ...]
    delay_frames: tuple[int, ...]
    nominal_delay: int
    active_action: str
    safety_value_horizon_frames: int = 0
    terminal_viable: np.ndarray | None = None
    survival_labels: bool = False
    retain_query_survival_problem: bool = False
    refinement_grid_steps: tuple[float, ...] = ()
    pre_viability_problem_hook: (
        Callable[[SurvivalQueryProblem], None] | None
    ) = None

    def __post_init__(self) -> None:
        if not self.actions:
            raise ValueError("robust control requires at least one action")
        if self.active_action not in {
            action.name for action in self.actions
        }:
            raise ValueError(
                "active action is absent from robust action set"
            )
        if self.safety_value_horizon_frames < 0:
            raise ValueError("safety-value horizon cannot be negative")
        if (
            any(
                not math.isfinite(step) or step <= 0.0
                for step in self.refinement_grid_steps
            )
            or tuple(
                sorted(set(self.refinement_grid_steps), reverse=True)
            )
            != self.refinement_grid_steps
        ):
            raise ValueError(
                "refinement grid steps must be unique positive descending"
            )
        if self.refinement_grid_steps and self.terminal_viable is not None:
            raise ValueError(
                "adaptive refinement does not yet remap terminal masks"
            )
        if (
            self.pre_viability_problem_hook is not None
            and (
                self.refinement_grid_steps
                or self.terminal_viable is not None
                or not self.retain_query_survival_problem
            )
        ):
            raise ValueError(
                "pre-viability query hooks require one retained, "
                "unrefined policy without an external terminal mask"
            )


__all__ = [
    "AabbHazard",
    "AabbTrajectoryHazard",
    "CorridorBounds",
    "CorridorConfig",
    "CorridorPlan",
    "CorridorPoint",
    "MovingAabbHazard",
    "PiecewiseAabbHazard",
    "RobustControlSpec",
    "SegmentHazard",
    "SegmentTrajectoryHazard",
]
