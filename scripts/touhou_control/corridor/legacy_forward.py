"""Legacy forward-reachability corridor planning."""

from __future__ import annotations

import math

import numpy as np

from ..packed_hazards import PackedSegmentFrames
from .clearance import clearance_field
from .grid import axis, lane, movement_offsets, shift_from_source
from .model import (
    AabbTrajectoryHazard,
    CorridorBounds,
    CorridorConfig,
    CorridorPlan,
    CorridorPoint,
    MovingAabbHazard,
    PiecewiseAabbHazard,
    SegmentHazard,
    SegmentTrajectoryHazard,
)


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
    for predecessor in reversed(predecessors):
        move_index = int(predecessor[row, column])
        if move_index < 0:
            raise RuntimeError("corridor predecessor chain is incomplete")
        dy, dx = offsets[move_index]
        row -= dy
        column -= dx
        coordinates.append((row, column))
    coordinates.reverse()
    return coordinates


def plan_legacy_forward_corridor(
    *,
    start_x: float,
    start_y: float,
    bounds: CorridorBounds,
    aabbs: tuple[MovingAabbHazard, ...],
    aabb_trajectories: tuple[AabbTrajectoryHazard, ...],
    piecewise_aabbs: tuple[PiecewiseAabbHazard, ...],
    segments: tuple[SegmentHazard, ...],
    segment_trajectories: tuple[SegmentTrajectoryHazard, ...],
    packed_segments: PackedSegmentFrames | None,
    preferred_x: float | None,
    preferred_y: float | None,
    required_gate_lane: str | None,
    config: CorridorConfig,
) -> CorridorPlan:
    """Run the historical forward dynamic program unchanged."""

    x_axis = axis(bounds.left, bounds.right, config.grid_step)
    y_axis = axis(bounds.top, bounds.bottom, config.grid_step)
    grid_x, grid_y = np.meshgrid(x_axis, y_axis)
    start_column = int(np.argmin(np.abs(x_axis - start_x)))
    start_row = int(np.argmin(np.abs(y_axis - start_y)))
    offsets = movement_offsets(config)
    layer_count = config.horizon_frames // config.frames_per_layer

    bottleneck = np.full(grid_x.shape, -np.inf, dtype=np.float32)
    exposure = np.full(grid_x.shape, np.inf, dtype=np.float64)
    bottleneck[start_row, start_column] = np.inf
    exposure[start_row, start_column] = 0.0
    predecessors: list[np.ndarray] = []
    clearance_fields: list[np.ndarray] = []

    for layer_index in range(1, layer_count + 1):
        frame = layer_index * config.frames_per_layer
        clearance, boundary_clearance = clearance_field(
            grid_x,
            grid_y,
            bounds=bounds,
            aabbs=aabbs,
            aabb_trajectories=aabb_trajectories,
            piecewise_aabbs=piecewise_aabbs,
            segments=segments,
            segment_trajectories=segment_trajectories,
            packed_segments=packed_segments,
            frame=frame,
            config=config,
        )
        clearance_fields.append(clearance)
        danger = np.square(
            np.maximum(config.danger_radius - clearance, 0.0)
        )
        boundary_danger = np.square(
            np.maximum(
                config.boundary_danger_radius - boundary_clearance,
                0.0,
            )
        )
        layer_cost = danger + 2.0 * boundary_danger

        next_bottleneck = np.full(
            grid_x.shape,
            -np.inf,
            dtype=np.float32,
        )
        next_exposure = np.full(
            grid_x.shape,
            np.inf,
            dtype=np.float64,
        )
        predecessor = np.full(grid_x.shape, -1, dtype=np.int16)
        traversable = clearance > config.required_clearance
        for move_index, (dy, dx) in enumerate(offsets):
            source_bottleneck = shift_from_source(
                bottleneck,
                dy,
                dx,
                -np.inf,
            )
            source_exposure = shift_from_source(
                exposure,
                dy,
                dx,
                np.inf,
            )
            candidate_bottleneck = np.minimum(
                source_bottleneck,
                clearance,
            )
            candidate_exposure = source_exposure + layer_cost
            valid = traversable & np.isfinite(source_exposure)
            better_bottleneck = valid & (
                candidate_bottleneck > next_bottleneck + 1e-5
            )
            tied_bottleneck = valid & np.isclose(
                candidate_bottleneck,
                next_bottleneck,
                atol=1e-5,
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
        acceptable_floor = min(
            config.preferred_clearance,
            maximum_bottleneck,
        )
        acceptable = reachable & (
            bottleneck >= acceptable_floor - 1e-5
        )
    else:
        acceptable = reachable
    target_x = start_x if preferred_x is None else preferred_x
    target_y = start_y if preferred_y is None else preferred_y
    terminal_cost = exposure + config.preferred_position_weight * (
        np.square(grid_x - target_x) + np.square(grid_y - target_y)
    )
    terminal_cost[~acceptable] = np.inf
    if required_gate_lane is not None:
        for terminal_flat in np.flatnonzero(
            np.isfinite(terminal_cost)
        ):
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
                    clearance_fields[item[0] - 1][
                        item[1][0],
                        item[1][1],
                    ]
                ),
            )
            if (
                lane(float(x_axis[gate_column]), bounds)
                != required_gate_lane
            ):
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
        terminal_flat,
        terminal_cost.shape,
    )

    coordinates = _trace_coordinates(
        terminal_row,
        terminal_column,
        predecessors=predecessors,
        offsets=offsets,
    )

    path: list[CorridorPoint] = [
        CorridorPoint(
            0,
            float(x_axis[start_column]),
            float(y_axis[start_row]),
            math.inf,
        )
    ]
    for layer_index, (row, column) in enumerate(
        coordinates[1:],
        start=1,
    ):
        path.append(
            CorridorPoint(
                frame=layer_index * config.frames_per_layer,
                x=float(x_axis[column]),
                y=float(y_axis[row]),
                clearance=float(
                    clearance_fields[layer_index - 1][row, column]
                ),
            )
        )
    terminal = path[-1]
    gate = min(path[1:], key=lambda point: point.clearance)
    return CorridorPlan(
        reachable=True,
        path=tuple(path),
        bottleneck_clearance=float(
            bottleneck[terminal_row, terminal_column]
        ),
        terminal_clearance=terminal.clearance,
        lane=lane(gate.x, bounds),
        gate=gate,
        reason=(
            "collision-free corridor found"
            if required_gate_lane is None
            else (
                f"collision-free {required_gate_lane} "
                "gate commitment found"
            )
        ),
    )


__all__ = ["plan_legacy_forward_corridor"]
