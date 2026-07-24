"""Deterministic adversarial generators and a simple trajectory oracle."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

import numpy as np

from touhou_control.trajectory import (
    PiecewiseLinearTrajectory,
    VelocityChange,
)


@dataclass(frozen=True)
class AdversarialAabb:
    motion: PiecewiseLinearTrajectory
    half_width: float
    half_height: float

    def __post_init__(self) -> None:
        if self.half_width < 0.0 or self.half_height < 0.0:
            raise ValueError("adversarial AABB extents cannot be negative")


@dataclass(frozen=True)
class AdversarialScenario:
    seed: int
    horizon_frames: int
    hazards: tuple[AdversarialAabb, ...]

    def __post_init__(self) -> None:
        if self.horizon_frames < 0:
            raise ValueError("adversarial horizon cannot be negative")


def generate_adversarial_scenario(
    seed: int,
    *,
    hazard_count: int,
    horizon_frames: int,
    left: float = 8.0,
    right: float = 376.0,
    top: float = 16.0,
    bottom: float = 432.0,
    maximum_events: int = 3,
) -> AdversarialScenario:
    """Generate dense straight/stop/reverse/redirect motion without game IDs."""

    if hazard_count < 0 or horizon_frames < 0 or maximum_events < 0:
        raise ValueError("adversarial generator counts cannot be negative")
    rng = random.Random(seed)
    hazards: list[AdversarialAabb] = []
    edge_x = (left, right, (left + right) * 0.5)
    edge_y = (top, bottom, (top + bottom) * 0.5)
    for index in range(hazard_count):
        if index < len(edge_x):
            x = edge_x[index]
            y = edge_y[index]
        else:
            x = rng.uniform(left - 48.0, right + 48.0)
            y = rng.uniform(top - 48.0, bottom + 48.0)
        initial_velocity_x = rng.uniform(-6.0, 6.0)
        initial_velocity_y = rng.uniform(-6.0, 6.0)
        velocity_x = initial_velocity_x
        velocity_y = initial_velocity_y
        event_count = (
            rng.randrange(maximum_events + 1)
            if horizon_frames and maximum_events
            else 0
        )
        event_count = min(event_count, horizon_frames)
        event_frames = sorted(
            rng.sample(range(1, horizon_frames + 1), event_count)
        )
        changes: list[VelocityChange] = []
        for event_index, frame in enumerate(event_frames):
            mode = (index + event_index + seed) % 4
            if mode == 0:
                next_x = 0.0
                next_y = 0.0
            elif mode == 1:
                next_x = -velocity_x
                next_y = -velocity_y
            elif mode == 2:
                next_x = rng.uniform(-10.0, 10.0)
                next_y = rng.uniform(-10.0, 10.0)
            else:
                angle = rng.uniform(-math.pi, math.pi)
                speed = rng.uniform(0.0, 10.0)
                next_x = math.cos(angle) * speed
                next_y = math.sin(angle) * speed
            changes.append(VelocityChange(frame, next_x, next_y))
            velocity_x = next_x
            velocity_y = next_y
        hazards.append(
            AdversarialAabb(
                PiecewiseLinearTrajectory(
                    x,
                    y,
                    initial_velocity_x,
                    initial_velocity_y,
                    tuple(changes),
                ),
                half_width=rng.uniform(0.5, 12.0),
                half_height=rng.uniform(0.5, 12.0),
            )
        )
    return AdversarialScenario(seed, horizon_frames, tuple(hazards))


def reference_clearance_volume(
    *,
    x_axis: np.ndarray,
    y_axis: np.ndarray,
    scenario: AdversarialScenario,
    player_radius: float,
    clearance_cap: float,
) -> np.ndarray:
    """Simple dense per-frame oracle used for differential testing."""

    if player_radius < 0.0 or clearance_cap <= 0.0:
        raise ValueError("reference clearance dimensions are invalid")
    x_axis = np.asarray(x_axis, dtype=np.float64)
    y_axis = np.asarray(y_axis, dtype=np.float64)
    grid_x, grid_y = np.meshgrid(x_axis, y_axis)
    output = np.full(
        (scenario.horizon_frames + 1, len(y_axis), len(x_axis)),
        clearance_cap,
        dtype=np.float64,
    )
    if not scenario.hazards:
        return output.astype(np.float32)
    half_width = np.asarray(
        [hazard.half_width for hazard in scenario.hazards],
        dtype=np.float64,
    )
    half_height = np.asarray(
        [hazard.half_height for hazard in scenario.hazards],
        dtype=np.float64,
    )
    flat_x = grid_x.reshape(-1, 1)
    flat_y = grid_y.reshape(-1, 1)
    for frame in range(scenario.horizon_frames + 1):
        positions = [
            hazard.motion.position(frame)
            for hazard in scenario.hazards
        ]
        hazard_x = np.fromiter(
            (position[0] for position in positions),
            dtype=np.float64,
        )
        hazard_y = np.fromiter(
            (position[1] for position in positions),
            dtype=np.float64,
        )
        dx = np.abs(flat_x - hazard_x[None, :]) - (
            player_radius + half_width[None, :]
        )
        dy = np.abs(flat_y - hazard_y[None, :]) - (
            player_radius + half_height[None, :]
        )
        overlap = (dx <= 0.0) & (dy <= 0.0)
        clearance = np.where(
            overlap,
            np.maximum(dx, dy),
            np.hypot(np.maximum(dx, 0.0), np.maximum(dy, 0.0)),
        )
        output[frame] = np.minimum(
            clearance_cap,
            clearance.min(axis=1).reshape(grid_x.shape),
        )
    return output.astype(np.float32)
