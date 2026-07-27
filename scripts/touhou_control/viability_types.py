"""Immutable public contracts for robust viability policies and queries."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class ControlAction:
    """A named constant-velocity action in world units per physical frame."""

    name: str
    velocity_x: float
    velocity_y: float

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("control action name cannot be empty")
        if not math.isfinite(self.velocity_x) or not math.isfinite(self.velocity_y):
            raise ValueError("control action velocity must be finite")



@dataclass(frozen=True)
class ViabilityConfig:
    frames_per_layer: int
    required_clearance: float = 0.0
    clamp_to_bounds: bool = True
    repair_radius_cells: int = 1

    def __post_init__(self) -> None:
        if self.frames_per_layer <= 0:
            raise ValueError("frames per layer must be positive")
        if not math.isfinite(self.required_clearance):
            raise ValueError("required clearance must be finite")
        if self.repair_radius_cells < 0:
            raise ValueError("repair radius cannot be negative")



@dataclass(frozen=True)
class ViabilityQuery:
    available: bool
    layer: int | None
    row: int | None
    column: int | None
    active_action: str
    state_viable: bool
    safe_actions: tuple[str, ...]
    repair_volumes: tuple[tuple[str, int], ...]
    position_error: float
    reason: str
    recovery_distances: tuple[tuple[str, float], ...] = ()
    survival_frames: int | None = None
    survival_bottleneck_margin: float | None = None
    survival_best_actions: tuple[str, ...] = ()

    @property
    def safe_action_count(self) -> int:
        return len(self.safe_actions)

    def repair_volume(self, action: str) -> int:
        for name, volume in self.repair_volumes:
            if name == action:
                return volume
        return 0

    def recovery_distance(self, action: str) -> float:
        for name, distance in self.recovery_distances:
            if name == action:
                return distance
        return math.inf



@dataclass(frozen=True)
class SafetyValueQuery:
    """Threshold-free robust clearance margins at one policy state."""

    available: bool
    layer: int | None
    row: int | None
    column: int | None
    active_action: str
    state_value: float
    action_values: tuple[tuple[str, float], ...]
    best_actions: tuple[str, ...]
    position_error: float
    reason: str

    def action_value(self, action: str) -> float:
        for name, value in self.action_values:
            if name == action:
                return value
        return -math.inf

    def certified_actions(
        self,
        *,
        required_clearance: float = 0.0,
        additional_position_error: float = 0.0,
    ) -> tuple[str, ...]:
        """Return actions whose margin covers the off-grid query error.

        Euclidean hazard clearance is 1-Lipschitz in player position and the
        clamped constant-velocity dynamics are nonexpansive.  Subtracting the
        live-to-lattice projection distance therefore turns the lattice value
        into a continuous-position certificate for this model.  Additional
        adapter/model error can be supplied separately.
        """

        if not math.isfinite(required_clearance):
            raise ValueError("required clearance must be finite")
        if (
            not math.isfinite(additional_position_error)
            or additional_position_error < 0.0
        ):
            raise ValueError(
                "additional position error must be finite and nonnegative"
            )
        if not self.available:
            return ()
        if not self.action_values:
            raise ValueError(
                "certified actions require retained per-action values"
            )
        threshold = (
            required_clearance
            + self.position_error
            + additional_position_error
        )
        return tuple(
            name
            for name, value in self.action_values
            if value > threshold
        )



__all__ = [
    "ControlAction",
    "SafetyValueQuery",
    "ViabilityConfig",
    "ViabilityQuery",
]
