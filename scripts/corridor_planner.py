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
import time
from dataclasses import dataclass

import numpy as np

from touhou_control import native_backend
from touhou_control.viability import (
    ControlAction,
    RobustViabilityPolicy,
    ViabilityConfig,
    build_robust_viability_policy,
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
    planning_mode: str = "forward_reachability"
    viability_policy: RobustViabilityPolicy | None = None
    initial_safe_action_count: int = 0
    initial_repair_volume: int = 0
    viability_backend: str | None = None
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

    def __post_init__(self) -> None:
        if not self.actions:
            raise ValueError("robust control requires at least one action")
        if self.active_action not in {action.name for action in self.actions}:
            raise ValueError("active action is absent from robust action set")


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


def _aabb_clearance_volume(
    grid_x: np.ndarray,
    grid_y: np.ndarray,
    hazards: tuple[MovingAabbHazard, ...],
    *,
    horizon_frames: int,
    player_radius: float,
    clearance_cap: float,
) -> np.ndarray:
    """Build an exact-below-cap moving-AABB distance volume.

    The dense formulation evaluates every lattice point against every hazard.
    Viability only distinguishes clearances near zero, while corridor ranking
    saturates beyond ``danger_radius``. Map each moving hazard to nearby
    lattice cells and scatter exact distances there; cells that no hazard can
    bring below the cap remain at the cap.
    """

    if horizon_frames < 0:
        raise ValueError("clearance horizon cannot be negative")
    if not math.isfinite(clearance_cap) or clearance_cap <= 0.0:
        raise ValueError("clearance cap must be positive and finite")
    frame_count = horizon_frames + 1
    if not hazards:
        return np.full(
            (frame_count, *grid_x.shape),
            clearance_cap,
            dtype=np.float32,
        )

    x_axis = grid_x[0].astype(np.float32, copy=False)
    y_axis = grid_y[:, 0].astype(np.float32, copy=False)
    if len(x_axis) < 2 or len(y_axis) < 2:
        raise ValueError("clearance volume requires a two-dimensional lattice")
    x_step = float(x_axis[1] - x_axis[0])
    y_step = float(y_axis[1] - y_axis[0])

    base_x = np.fromiter((item.x for item in hazards), dtype=np.float32)
    base_y = np.fromiter((item.y for item in hazards), dtype=np.float32)
    velocity_x = np.fromiter(
        (item.velocity_x for item in hazards),
        dtype=np.float32,
    )
    velocity_y = np.fromiter(
        (item.velocity_y for item in hazards),
        dtype=np.float32,
    )
    half_width = np.fromiter(
        (item.half_width for item in hazards),
        dtype=np.float32,
    )
    half_height = np.fromiter(
        (item.half_height for item in hazards),
        dtype=np.float32,
    )
    base_uncertainty = np.fromiter(
        (item.base_uncertainty for item in hazards),
        dtype=np.float32,
    )
    uncertainty_per_frame = np.fromiter(
        (item.uncertainty_per_frame for item in hazards),
        dtype=np.float32,
    )

    frames = np.arange(frame_count, dtype=np.float32)[:, None]
    hazard_x = base_x[None, :] + frames * velocity_x[None, :]
    hazard_y = base_y[None, :] + frames * velocity_y[None, :]
    uncertainty = (
        base_uncertainty[None, :]
        + frames * uncertainty_per_frame[None, :]
    )
    nearest_columns = np.rint(
        (hazard_x - float(x_axis[0])) / x_step
    ).astype(np.int16)
    nearest_rows = np.rint(
        (hazard_y - float(y_axis[0])) / y_step
    ).astype(np.int16)
    volume = np.full(
        (frame_count, len(y_axis), len(x_axis)),
        clearance_cap,
        dtype=np.float32,
    )
    maximum_uncertainty = (
        base_uncertainty + horizon_frames * uncertainty_per_frame
    )
    column_offset_limits = (
        np.ceil(
            (
                half_width
                + maximum_uncertainty
                + player_radius
                + clearance_cap
            )
            / x_step
        ).astype(np.int16)
        + 1
    )
    row_offset_limits = (
        np.ceil(
            (
                half_height
                + maximum_uncertainty
                + player_radius
                + clearance_cap
            )
            / y_step
        ).astype(np.int16)
        + 1
    )
    maximum_offset = np.maximum(column_offset_limits, row_offset_limits)
    offset_buckets = ((maximum_offset + 1) // 2) * 2
    for bucket in np.unique(offset_buckets):
        selected = np.flatnonzero(offset_buckets == bucket)
        group_x = hazard_x[:, selected]
        group_y = hazard_y[:, selected]
        group_uncertainty = uncertainty[:, selected]
        group_columns = nearest_columns[:, selected]
        group_rows = nearest_rows[:, selected]
        expanded_half_width = (
            player_radius
            + half_width[selected][None, :]
            + group_uncertainty
        )
        expanded_half_height = (
            player_radius
            + half_height[selected][None, :]
            + group_uncertainty
        )
        frame_indices = np.broadcast_to(
            np.arange(frame_count, dtype=np.intp)[:, None],
            group_x.shape,
        )
        max_column_offset = int(np.max(column_offset_limits[selected]))
        max_row_offset = int(np.max(row_offset_limits[selected]))
        for row_offset in range(-max_row_offset, max_row_offset + 1):
            rows = group_rows + row_offset
            row_inside = (rows >= 0) & (rows < len(y_axis))
            sample_y = (
                float(y_axis[0]) + rows.astype(np.float32) * y_step
            )
            dy = np.abs(sample_y - group_y) - expanded_half_height
            for column_offset in range(
                -max_column_offset,
                max_column_offset + 1,
            ):
                columns = group_columns + column_offset
                sample_x = (
                    float(x_axis[0])
                    + columns.astype(np.float32) * x_step
                )
                dx = np.abs(sample_x - group_x) - expanded_half_width
                relevant = (
                    row_inside
                    & (columns >= 0)
                    & (columns < len(x_axis))
                    & (dx < clearance_cap)
                    & (dy < clearance_cap)
                )
                if not np.any(relevant):
                    continue
                overlap = (dx <= 0.0) & (dy <= 0.0)
                clearance = np.where(
                    overlap,
                    np.maximum(dx, dy),
                    np.hypot(
                        np.maximum(dx, 0.0),
                        np.maximum(dy, 0.0),
                    ),
                )
                np.minimum.at(
                    volume,
                    (
                        frame_indices[relevant],
                        rows[relevant],
                        columns[relevant],
                    ),
                    clearance[relevant],
                )
    return volume


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


def _hazard_clearance_volume(
    grid_x: np.ndarray,
    grid_y: np.ndarray,
    *,
    aabbs: tuple[MovingAabbHazard, ...],
    segments: tuple[SegmentHazard, ...],
    config: CorridorConfig,
) -> np.ndarray:
    """Build physical-frame clearance without treating legal bounds as hazards."""

    native_volume = native_backend.build_clearance_volume(
        x_axis=grid_x[0],
        y_axis=grid_y[:, 0],
        frame_count=config.horizon_frames + 1,
        player_radius=config.player_radius,
        clearance_cap=config.danger_radius,
        aabbs=aabbs,
        segments=segments,
    )
    if native_volume is not None:
        return native_volume

    volume = _aabb_clearance_volume(
        grid_x,
        grid_y,
        aabbs,
        horizon_frames=config.horizon_frames,
        player_radius=config.player_radius,
        clearance_cap=config.danger_radius,
    )
    for frame in range(config.horizon_frames + 1):
        volume[frame] = np.minimum(
            volume[frame],
            _segment_clearance_field(
                grid_x,
                grid_y,
                segments,
                frame=frame,
                player_radius=config.player_radius,
            ),
        )
    return volume


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


def _robust_lane_target(
    required_gate_lane: str | None,
    *,
    bounds: CorridorBounds,
    preferred_x: float | None,
) -> float:
    if required_gate_lane == "left":
        return bounds.left + (bounds.right - bounds.left) / 6.0
    if required_gate_lane == "right":
        return bounds.right - (bounds.right - bounds.left) / 6.0
    if required_gate_lane == "center":
        return (bounds.left + bounds.right) * 0.5
    if preferred_x is not None:
        return preferred_x
    return (bounds.left + bounds.right) * 0.5


def _plan_robust_corridor(
    *,
    start_x: float,
    start_y: float,
    bounds: CorridorBounds,
    aabbs: tuple[MovingAabbHazard, ...],
    segments: tuple[SegmentHazard, ...],
    preferred_x: float | None,
    preferred_y: float | None,
    required_gate_lane: str | None,
    config: CorridorConfig,
    robust_control: RobustControlSpec,
) -> CorridorPlan:
    solve_started = time.perf_counter()
    x_axis = _axis(bounds.left, bounds.right, config.grid_step)
    y_axis = _axis(bounds.top, bounds.bottom, config.grid_step)
    grid_x, grid_y = np.meshgrid(x_axis, y_axis)
    clearance_volume = _hazard_clearance_volume(
        grid_x,
        grid_y,
        aabbs=aabbs,
        segments=segments,
        config=config,
    )
    clearance_finished = time.perf_counter()
    policy = build_robust_viability_policy(
        x_axis=x_axis,
        y_axis=y_axis,
        clearance_volume=clearance_volume,
        actions=robust_control.actions,
        delay_frames=robust_control.delay_frames,
        nominal_delay=robust_control.nominal_delay,
        config=ViabilityConfig(
            frames_per_layer=config.frames_per_layer,
            required_clearance=config.required_clearance,
            clamp_to_bounds=True,
            repair_radius_cells=1,
        ),
    )
    viability_finished = time.perf_counter()
    base_timing = (
        (
            "clearance",
            (clearance_finished - solve_started) * 1000.0,
        ),
        (
            "viability",
            (viability_finished - clearance_finished) * 1000.0,
        ),
    )
    start_query = policy.query(
        frame=0,
        x=start_x,
        y=start_y,
        active_action=robust_control.active_action,
    )
    if not start_query.state_viable:
        return CorridorPlan(
            reachable=False,
            path=(),
            bottleneck_clearance=-math.inf,
            terminal_clearance=-math.inf,
            lane="none",
            gate=None,
            reason="initial robust viability action set is empty",
            planning_mode="robust_viability",
            viability_policy=policy,
            viability_backend=policy.backend,
            solver_timing_ms=(
                *base_timing,
                ("rollout", 0.0),
            ),
        )

    target_x = _robust_lane_target(
        required_gate_lane,
        bounds=bounds,
        preferred_x=preferred_x,
    )
    target_y = start_y if preferred_y is None else preferred_y
    current_x = float(x_axis[start_query.column])
    current_y = float(y_axis[start_query.row])
    active_action = robust_control.active_action
    path = [CorridorPoint(0, current_x, current_y, math.inf)]
    bottleneck = math.inf
    initial_repair_volume = 0
    for layer in range(policy.layer_count):
        frame = layer * config.frames_per_layer
        query = policy.query(
            frame=frame,
            x=current_x,
            y=current_y,
            active_action=active_action,
        )
        if not query.safe_actions:
            raise RuntimeError("viability rollout left its own backward kernel")
        candidates: list[
            tuple[tuple[float, ...], str, float, float, int, float]
        ] = []
        for action_name in query.safe_actions:
            endpoint_x, endpoint_y = policy.transition_endpoint(
                x=current_x,
                y=current_y,
                active_action=active_action,
                next_action=action_name,
            )
            column = int(np.argmin(np.abs(x_axis - endpoint_x)))
            row = int(np.argmin(np.abs(y_axis - endpoint_y)))
            endpoint_x = float(x_axis[column])
            endpoint_y = float(y_axis[row])
            next_frame = (layer + 1) * config.frames_per_layer
            hazard_clearance = float(clearance_volume[next_frame, row, column])
            boundary_clearance = min(
                endpoint_x - bounds.left,
                bounds.right - endpoint_x,
                endpoint_y - bounds.top,
                bounds.bottom - endpoint_y,
            )
            clearance = min(hazard_clearance, boundary_clearance)
            repair_volume = query.repair_volume(action_name)
            position_cost = (
                (endpoint_x - target_x) ** 2
                + (endpoint_y - target_y) ** 2
            )
            candidates.append(
                (
                    (
                        -float(repair_volume),
                        -clearance,
                        position_cost,
                        0.0 if action_name == active_action else 1.0,
                    ),
                    action_name,
                    endpoint_x,
                    endpoint_y,
                    repair_volume,
                    clearance,
                )
            )
        (
            _,
            selected_action,
            current_x,
            current_y,
            repair_volume,
            clearance,
        ) = min(candidates, key=lambda candidate: candidate[0])
        if layer == 0:
            initial_repair_volume = repair_volume
        bottleneck = min(bottleneck, clearance)
        active_action = selected_action
        path.append(
            CorridorPoint(
                frame=(layer + 1) * config.frames_per_layer,
                x=current_x,
                y=current_y,
                clearance=clearance,
            )
        )

    terminal = path[-1]
    gate = min(path[1:], key=lambda point: point.clearance)
    lane = _lane(gate.x, bounds)
    if required_gate_lane is not None and lane != required_gate_lane:
        return CorridorPlan(
            reachable=False,
            path=(),
            bottleneck_clearance=-math.inf,
            terminal_clearance=-math.inf,
            lane="none",
            gate=None,
            reason=(
                "robust policy has no representative path through required "
                f"{required_gate_lane} gate lane"
            ),
            planning_mode="robust_viability",
            viability_policy=policy,
            initial_safe_action_count=start_query.safe_action_count,
            initial_repair_volume=initial_repair_volume,
            viability_backend=policy.backend,
            solver_timing_ms=(
                *base_timing,
                (
                    "rollout",
                    (time.perf_counter() - viability_finished) * 1000.0,
                ),
            ),
        )
    return CorridorPlan(
        reachable=True,
        path=tuple(path),
        bottleneck_clearance=bottleneck,
        terminal_clearance=terminal.clearance,
        lane=lane,
        gate=gate,
        reason=(
            "delay-robust viable corridor found"
            if required_gate_lane is None
            else f"delay-robust {required_gate_lane} gate policy found"
        ),
        planning_mode="robust_viability",
        viability_policy=policy,
        initial_safe_action_count=start_query.safe_action_count,
        initial_repair_volume=initial_repair_volume,
        viability_backend=policy.backend,
        solver_timing_ms=(
            *base_timing,
            (
                "rollout",
                (time.perf_counter() - viability_finished) * 1000.0,
            ),
        ),
    )


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
    robust_control: RobustControlSpec | None = None,
) -> CorridorPlan:
    """Return a reachable path or a delay-robust backward viability policy."""

    if required_gate_lane not in (None, "left", "center", "right"):
        raise ValueError("required gate lane must be left, center, or right")
    if not (
        bounds.left <= start_x <= bounds.right
        and bounds.top <= start_y <= bounds.bottom
    ):
        raise ValueError("corridor start is outside bounds")
    if robust_control is not None:
        return _plan_robust_corridor(
            start_x=start_x,
            start_y=start_y,
            bounds=bounds,
            aabbs=aabbs,
            segments=segments,
            preferred_x=preferred_x,
            preferred_y=preferred_y,
            required_gate_lane=required_gate_lane,
            config=config,
            robust_control=robust_control,
        )
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
