#!/usr/bin/env python3
"""Game-neutral time-expanded safe-corridor planner.

The local controller answers "which key now?". This module answers the slower
topological question: "which connected open region must remain reachable over
the next several dozen frames?". It uses a coarse reachable-set dynamic program
and returns a waypoint path. Game adapters provide moving AABBs and segments;
no TH08 address, opcode, or resource type appears here.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


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
            raise ValueError("hazard dimensions and uncertainty cannot be negative")


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
            raise ValueError("segment width and uncertainty cannot be negative")


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
            raise ValueError("horizon must be divisible by frames per layer")
        if min(
            self.cardinal_speed,
            self.diagonal_axis_speed,
            self.player_radius,
            self.danger_radius,
            self.boundary_danger_radius,
        ) < 0.0:
            raise ValueError("corridor speeds and radii cannot be negative")


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

    def waypoint(self, frame: int) -> CorridorPoint:
        if not self.path:
            raise ValueError("unreachable corridor has no waypoint")
        for point in self.path:
            if point.frame >= frame:
                return point
        return self.path[-1]


def _axis(start: float, end: float, step: float) -> np.ndarray:
    count = int(round((end - start) / step))
    if not math.isclose(start + count * step, end, abs_tol=1e-5):
        raise ValueError("bounds must be an integer number of grid steps")
    return np.linspace(start, end, count + 1, dtype=np.float32)


def _movement_offsets(config: CorridorConfig) -> tuple[tuple[int, int], ...]:
    max_cells = int(
        math.ceil(
            config.cardinal_speed * config.frames_per_layer / config.grid_step
        )
    )
    offsets: list[tuple[int, int]] = []
    for dy in range(-max_cells, max_cells + 1):
        for dx in range(-max_cells, max_cells + 1):
            horizontal = abs(dx) * config.grid_step
            vertical = abs(dy) * config.grid_step
            diagonal = min(horizontal, vertical)
            straight = max(horizontal, vertical) - diagonal
            required_frames = 0.0
            if diagonal:
                if config.diagonal_axis_speed == 0.0:
                    continue
                required_frames += diagonal / config.diagonal_axis_speed
            if straight:
                if config.cardinal_speed == 0.0:
                    continue
                required_frames += straight / config.cardinal_speed
            if required_frames <= config.frames_per_layer + 1e-6:
                offsets.append((dy, dx))
    offsets.sort(key=lambda item: (abs(item[0]) + abs(item[1]), item[0], item[1]))
    return tuple(offsets)


def _shift_from_source(
    values: np.ndarray, dy: int, dx: int, fill: float
) -> np.ndarray:
    shifted = np.full(values.shape, fill, dtype=values.dtype)
    height, width = values.shape
    source_y_start = max(0, -dy)
    source_y_end = min(height, height - dy)
    source_x_start = max(0, -dx)
    source_x_end = min(width, width - dx)
    destination_y_start = source_y_start + dy
    destination_y_end = source_y_end + dy
    destination_x_start = source_x_start + dx
    destination_x_end = source_x_end + dx
    shifted[
        destination_y_start:destination_y_end,
        destination_x_start:destination_x_end,
    ] = values[source_y_start:source_y_end, source_x_start:source_x_end]
    return shifted


def _aabb_clearance_field(
    grid_x: np.ndarray,
    grid_y: np.ndarray,
    hazards: tuple[MovingAabbHazard, ...],
    *,
    frame: int,
    player_radius: float,
) -> np.ndarray:
    if not hazards:
        return np.full(grid_x.shape, np.inf, dtype=np.float32)
    hazard_x = np.fromiter(
        (item.x + item.velocity_x * frame for item in hazards), dtype=np.float32
    )
    hazard_y = np.fromiter(
        (item.y + item.velocity_y * frame for item in hazards), dtype=np.float32
    )
    uncertainty = np.fromiter(
        (
            item.base_uncertainty + item.uncertainty_per_frame * frame
            for item in hazards
        ),
        dtype=np.float32,
    )
    half_width = np.fromiter(
        (item.half_width for item in hazards), dtype=np.float32
    )
    half_height = np.fromiter(
        (item.half_height for item in hazards), dtype=np.float32
    )
    flat_x = grid_x.reshape(-1, 1)
    flat_y = grid_y.reshape(-1, 1)
    dx = np.abs(flat_x - hazard_x[None, :]) - (
        player_radius + half_width[None, :] + uncertainty[None, :]
    )
    dy = np.abs(flat_y - hazard_y[None, :]) - (
        player_radius + half_height[None, :] + uncertainty[None, :]
    )
    overlap = (dx <= 0.0) & (dy <= 0.0)
    clearance = np.where(
        overlap,
        np.maximum(dx, dy),
        np.hypot(np.maximum(dx, 0.0), np.maximum(dy, 0.0)),
    )
    return clearance.min(axis=1).reshape(grid_x.shape).astype(np.float32)


def _segment_clearance_field(
    grid_x: np.ndarray,
    grid_y: np.ndarray,
    hazards: tuple[SegmentHazard, ...],
    *,
    frame: int,
    player_radius: float,
) -> np.ndarray:
    if not hazards:
        return np.full(grid_x.shape, np.inf, dtype=np.float32)
    origin_x = np.fromiter(
        (hazard.origin_x for hazard in hazards),
        dtype=np.float32,
    )
    origin_y = np.fromiter(
        (hazard.origin_y for hazard in hazards),
        dtype=np.float32,
    )
    angle = np.fromiter(
        (hazard.angle for hazard in hazards),
        dtype=np.float32,
    )
    tail = np.fromiter(
        (hazard.tail for hazard in hazards),
        dtype=np.float32,
    )
    head = np.fromiter(
        (hazard.head for hazard in hazards),
        dtype=np.float32,
    )
    cosine = np.cos(angle)
    sine = np.sin(angle)
    start_x = origin_x + cosine * tail
    start_y = origin_y + sine * tail
    segment_x = cosine * (head - tail)
    segment_y = sine * (head - tail)
    length_sq = segment_x * segment_x + segment_y * segment_y
    flat_x = grid_x.reshape(-1, 1)
    flat_y = grid_y.reshape(-1, 1)
    numerator = (
        (flat_x - start_x[None, :]) * segment_x[None, :]
        + (flat_y - start_y[None, :]) * segment_y[None, :]
    )
    projection = np.divide(
        numerator,
        length_sq[None, :],
        out=np.zeros_like(numerator),
        where=length_sq[None, :] > 1e-9,
    )
    projection = np.clip(projection, 0.0, 1.0)
    distance = np.hypot(
        flat_x - (start_x + projection * segment_x),
        flat_y - (start_y + projection * segment_y),
    )
    occupied_radius = np.fromiter(
        (
            hazard.half_width
            + player_radius
            + hazard.base_uncertainty
            + hazard.uncertainty_per_frame * frame
            for hazard in hazards
        ),
        dtype=np.float32,
    )
    clearance = distance - occupied_radius[None, :]
    return clearance.min(axis=1).reshape(grid_x.shape).astype(np.float32)


def _clearance_field(
    grid_x: np.ndarray,
    grid_y: np.ndarray,
    *,
    bounds: CorridorBounds,
    aabbs: tuple[MovingAabbHazard, ...],
    segments: tuple[SegmentHazard, ...],
    frame: int,
    config: CorridorConfig,
) -> tuple[np.ndarray, np.ndarray]:
    hazard_clearance = np.minimum(
        _aabb_clearance_field(
            grid_x,
            grid_y,
            aabbs,
            frame=frame,
            player_radius=config.player_radius,
        ),
        _segment_clearance_field(
            grid_x,
            grid_y,
            segments,
            frame=frame,
            player_radius=config.player_radius,
        ),
    )
    boundary_clearance = np.minimum.reduce(
        (
            grid_x - bounds.left,
            bounds.right - grid_x,
            grid_y - bounds.top,
            bounds.bottom - grid_y,
        )
    ).astype(np.float32)
    robust_clearance = np.minimum(hazard_clearance, boundary_clearance)
    return robust_clearance, boundary_clearance


def _lane(x: float, bounds: CorridorBounds) -> str:
    third = (bounds.right - bounds.left) / 3.0
    if x < bounds.left + third:
        return "left"
    if x > bounds.right - third:
        return "right"
    return "center"


def _trace_coordinates(
    terminal_row: int,
    terminal_column: int,
    *,
    predecessors: list[np.ndarray],
    offsets: tuple[tuple[int, int], ...],
) -> list[tuple[int, int]]:
    coordinates = [(terminal_row, terminal_column)]
    row = terminal_row
    column = terminal_column
    for layer in range(len(predecessors) - 1, -1, -1):
        move_index = int(predecessors[layer][row, column])
        if move_index < 0:
            raise RuntimeError("corridor predecessor chain is incomplete")
        dy, dx = offsets[move_index]
        row -= dy
        column -= dx
        coordinates.append((row, column))
    coordinates.reverse()
    return coordinates


def plan_corridor(
    *,
    start_x: float,
    start_y: float,
    bounds: CorridorBounds,
    aabbs: tuple[MovingAabbHazard, ...] = (),
    segments: tuple[SegmentHazard, ...] = (),
    preferred_x: float | None = None,
    preferred_y: float | None = None,
    required_gate_lane: str | None = None,
    config: CorridorConfig = CorridorConfig(),
) -> CorridorPlan:
    """Return a robust reachable path through a coarse time-expanded grid."""

    if required_gate_lane not in (None, "left", "center", "right"):
        raise ValueError("required gate lane must be left, center, or right")
    if not (
        bounds.left <= start_x <= bounds.right
        and bounds.top <= start_y <= bounds.bottom
    ):
        raise ValueError("corridor start is outside bounds")
    x_axis = _axis(bounds.left, bounds.right, config.grid_step)
    y_axis = _axis(bounds.top, bounds.bottom, config.grid_step)
    grid_x, grid_y = np.meshgrid(x_axis, y_axis)
    start_column = int(np.argmin(np.abs(x_axis - start_x)))
    start_row = int(np.argmin(np.abs(y_axis - start_y)))
    offsets = _movement_offsets(config)
    layer_count = config.horizon_frames // config.frames_per_layer

    bottleneck = np.full(grid_x.shape, -np.inf, dtype=np.float32)
    exposure = np.full(grid_x.shape, np.inf, dtype=np.float64)
    bottleneck[start_row, start_column] = np.inf
    exposure[start_row, start_column] = 0.0
    predecessors: list[np.ndarray] = []
    clearance_fields: list[np.ndarray] = []

    for layer in range(1, layer_count + 1):
        frame = layer * config.frames_per_layer
        clearance, boundary_clearance = _clearance_field(
            grid_x,
            grid_y,
            bounds=bounds,
            aabbs=aabbs,
            segments=segments,
            frame=frame,
            config=config,
        )
        clearance_fields.append(clearance)
        danger = np.square(np.maximum(config.danger_radius - clearance, 0.0))
        boundary_danger = np.square(
            np.maximum(config.boundary_danger_radius - boundary_clearance, 0.0)
        )
        layer_cost = danger + 2.0 * boundary_danger

        next_bottleneck = np.full(grid_x.shape, -np.inf, dtype=np.float32)
        next_exposure = np.full(grid_x.shape, np.inf, dtype=np.float64)
        predecessor = np.full(grid_x.shape, -1, dtype=np.int16)
        traversable = clearance > config.required_clearance
        for move_index, (dy, dx) in enumerate(offsets):
            source_bottleneck = _shift_from_source(
                bottleneck, dy, dx, -np.inf
            )
            source_exposure = _shift_from_source(exposure, dy, dx, np.inf)
            candidate_bottleneck = np.minimum(source_bottleneck, clearance)
            candidate_exposure = source_exposure + layer_cost
            valid = traversable & np.isfinite(source_exposure)
            better_bottleneck = valid & (
                candidate_bottleneck > next_bottleneck + 1e-5
            )
            tied_bottleneck = valid & np.isclose(
                candidate_bottleneck, next_bottleneck, atol=1e-5
            )
            better_exposure = tied_bottleneck & (
                candidate_exposure < next_exposure
            )
            better = better_bottleneck | better_exposure
            next_bottleneck[better] = candidate_bottleneck[better]
            next_exposure[better] = candidate_exposure[better]
            predecessor[better] = move_index
        bottleneck = next_bottleneck
        exposure = next_exposure
        predecessors.append(predecessor)

    reachable = np.isfinite(exposure)
    if not reachable.any():
        return CorridorPlan(
            reachable=False,
            path=(),
            bottleneck_clearance=-math.inf,
            terminal_clearance=-math.inf,
            lane="none",
            gate=None,
            reason="no collision-free time-expanded path",
        )

    maximum_bottleneck = float(np.max(bottleneck[reachable]))
    if required_gate_lane is None:
        acceptable_floor = min(config.preferred_clearance, maximum_bottleneck)
        acceptable = reachable & (bottleneck >= acceptable_floor - 1e-5)
    else:
        acceptable = reachable
    target_x = start_x if preferred_x is None else preferred_x
    target_y = start_y if preferred_y is None else preferred_y
    terminal_cost = exposure + config.preferred_position_weight * (
        np.square(grid_x - target_x) + np.square(grid_y - target_y)
    )
    terminal_cost[~acceptable] = np.inf
    if required_gate_lane is not None:
        for terminal_flat in np.flatnonzero(np.isfinite(terminal_cost)):
            candidate_row, candidate_column = np.unravel_index(
                int(terminal_flat),
                terminal_cost.shape,
            )
            coordinates = _trace_coordinates(
                candidate_row,
                candidate_column,
                predecessors=predecessors,
                offsets=offsets,
            )
            _, (gate_row, gate_column) = min(
                enumerate(coordinates[1:], start=1),
                key=lambda item: float(
                    clearance_fields[item[0] - 1][item[1][0], item[1][1]]
                ),
            )
            if _lane(float(x_axis[gate_column]), bounds) != required_gate_lane:
                terminal_cost[candidate_row, candidate_column] = np.inf
        if not np.isfinite(terminal_cost).any():
            return CorridorPlan(
                reachable=False,
                path=(),
                bottleneck_clearance=-math.inf,
                terminal_clearance=-math.inf,
                lane="none",
                gate=None,
                reason=(
                    "no collision-free path through required "
                    f"{required_gate_lane} gate lane"
                ),
            )
    terminal_flat = int(np.argmin(terminal_cost))
    terminal_row, terminal_column = np.unravel_index(
        terminal_flat, terminal_cost.shape
    )

    coordinates = _trace_coordinates(
        terminal_row,
        terminal_column,
        predecessors=predecessors,
        offsets=offsets,
    )

    path: list[CorridorPoint] = [
        CorridorPoint(0, float(x_axis[start_column]), float(y_axis[start_row]), math.inf)
    ]
    for layer, (row, column) in enumerate(coordinates[1:], start=1):
        path.append(
            CorridorPoint(
                frame=layer * config.frames_per_layer,
                x=float(x_axis[column]),
                y=float(y_axis[row]),
                clearance=float(clearance_fields[layer - 1][row, column]),
            )
        )
    terminal = path[-1]
    gate = min(path[1:], key=lambda point: point.clearance)
    return CorridorPlan(
        reachable=True,
        path=tuple(path),
        bottleneck_clearance=float(bottleneck[terminal_row, terminal_column]),
        terminal_clearance=terminal.clearance,
        lane=_lane(gate.x, bounds),
        gate=gate,
        reason=(
            "collision-free corridor found"
            if required_gate_lane is None
            else f"collision-free {required_gate_lane} gate commitment found"
        ),
    )
