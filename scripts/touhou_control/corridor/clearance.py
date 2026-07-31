"""Signed-clearance construction for corridor planning."""

from __future__ import annotations

import math

import numpy as np

from .. import native_backend
from ..packed_hazards import PackedSegmentFrames
from .model import (
    AabbHazard,
    AabbTrajectoryHazard,
    AnnularSectorTrajectoryHazard,
    CorridorBounds,
    CorridorConfig,
    MovingAabbHazard,
    PiecewiseAabbHazard,
    SegmentHazard,
    SegmentTrajectoryHazard,
)

_TWO_PI = 2.0 * math.pi
_SECTOR_NUMERIC_GUARD = 2.0e-5


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
        (item.x + item.velocity_x * frame for item in hazards),
        dtype=np.float32,
    )
    hazard_y = np.fromiter(
        (item.y + item.velocity_y * frame for item in hazards),
        dtype=np.float32,
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


def _aabb_sample_clearance_field(
    grid_x: np.ndarray,
    grid_y: np.ndarray,
    hazards: tuple[AabbHazard, ...],
    *,
    frame: int,
    player_radius: float,
) -> np.ndarray:
    if not hazards:
        return np.full(grid_x.shape, np.inf, dtype=np.float32)
    hazard_x = np.fromiter(
        (item.x for item in hazards), dtype=np.float32
    )
    hazard_y = np.fromiter(
        (item.y for item in hazards), dtype=np.float32
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


def _annular_sector_clearance_field(
    grid_x: np.ndarray,
    grid_y: np.ndarray,
    hazards: tuple[AnnularSectorTrajectoryHazard, ...],
    *,
    frame: int,
    player_radius: float,
) -> np.ndarray:
    """Conservative distance to a union of continuous annular sectors.

    The exact point-to-sector distance is reduced by the player radius and
    each adapter-supplied Minkowski inflation.  The resulting field is a
    lower bound on native AABB clearance, including uncertain source origins.
    """

    active = tuple(
        (hazard, radial)
        for hazard in hazards
        if (radial := hazard.radial_sample(frame)) is not None
    )
    if not active:
        return np.full(grid_x.shape, np.inf, dtype=np.float32)

    origin_x = np.asarray(
        [hazard.origin_x for hazard, _ in active],
        dtype=np.float64,
    )
    origin_y = np.asarray(
        [hazard.origin_y for hazard, _ in active],
        dtype=np.float64,
    )
    minimum_angle = np.asarray(
        [hazard.minimum_angle for hazard, _ in active],
        dtype=np.float64,
    )
    maximum_angle = np.asarray(
        [hazard.maximum_angle for hazard, _ in active],
        dtype=np.float64,
    )
    minimum_radius = np.asarray(
        [radial[0] for _, radial in active],
        dtype=np.float64,
    )
    maximum_radius = np.asarray(
        [radial[1] for _, radial in active],
        dtype=np.float64,
    )
    inflation = np.asarray(
        [
            player_radius
            + hazard.half_extent_radius
            + hazard.origin_uncertainty
            + hazard.base_uncertainty
            + hazard.uncertainty_per_frame * frame
            for hazard, _ in active
        ],
        dtype=np.float64,
    )

    dx = grid_x.reshape(-1, 1).astype(np.float64) - origin_x[None, :]
    dy = grid_y.reshape(-1, 1).astype(np.float64) - origin_y[None, :]
    radius = np.hypot(dx, dy)
    angle = np.arctan2(dy, dx)
    angle_span = maximum_angle - minimum_angle
    phase = np.remainder(angle - minimum_angle[None, :], _TWO_PI)
    inside_angle = (angle_span[None, :] >= _TWO_PI) | (
        phase <= angle_span[None, :]
    )

    radial_distance = np.maximum(
        np.maximum(
            minimum_radius[None, :] - radius,
            radius - maximum_radius[None, :],
        ),
        0.0,
    )

    lower_cos = np.cos(minimum_angle)[None, :]
    lower_sin = np.sin(minimum_angle)[None, :]
    upper_cos = np.cos(maximum_angle)[None, :]
    upper_sin = np.sin(maximum_angle)[None, :]
    lower_projection = np.clip(
        dx * lower_cos + dy * lower_sin,
        minimum_radius[None, :],
        maximum_radius[None, :],
    )
    upper_projection = np.clip(
        dx * upper_cos + dy * upper_sin,
        minimum_radius[None, :],
        maximum_radius[None, :],
    )
    lower_distance = np.hypot(
        dx - lower_projection * lower_cos,
        dy - lower_projection * lower_sin,
    )
    upper_distance = np.hypot(
        dx - upper_projection * upper_cos,
        dy - upper_projection * upper_sin,
    )
    center_distance = np.where(
        inside_angle,
        radial_distance,
        np.minimum(lower_distance, upper_distance),
    )
    clearance = center_distance - inflation[None, :] - _SECTOR_NUMERIC_GUARD
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
        raise ValueError(
            "clearance volume requires a two-dimensional lattice"
        )
    x_step = float(x_axis[1] - x_axis[0])
    y_step = float(y_axis[1] - y_axis[0])

    base_x = np.fromiter(
        (item.x for item in hazards), dtype=np.float32
    )
    base_y = np.fromiter(
        (item.y for item in hazards), dtype=np.float32
    )
    velocity_x = np.fromiter(
        (item.velocity_x for item in hazards),
        dtype=np.float32,
    )
    velocity_y = np.fromiter(
        (item.velocity_y for item in hazards),
        dtype=np.float32,
    )
    half_width = np.fromiter(
        (item.half_width for item in hazards), dtype=np.float32
    )
    half_height = np.fromiter(
        (item.half_height for item in hazards), dtype=np.float32
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
    maximum_offset = np.maximum(
        column_offset_limits, row_offset_limits
    )
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
        max_column_offset = int(
            np.max(column_offset_limits[selected])
        )
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


def _packed_segment_clearance_field(
    grid_x: np.ndarray,
    grid_y: np.ndarray,
    packed_segments: PackedSegmentFrames,
    *,
    frame: int,
    player_radius: float,
) -> np.ndarray:
    selected = packed_segments.frame_slice(frame)
    if selected.start == selected.stop:
        return np.full(grid_x.shape, np.inf, dtype=np.float32)
    origin_x = packed_segments.origin_x[selected]
    origin_y = packed_segments.origin_y[selected]
    angle = packed_segments.angle[selected]
    tail = packed_segments.tail[selected]
    head = packed_segments.head[selected]
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
    occupied_radius = (
        packed_segments.half_width[selected]
        + player_radius
        + packed_segments.base_uncertainty[selected]
        + packed_segments.uncertainty_per_frame[selected] * frame
    )
    clearance = distance - occupied_radius[None, :]
    return clearance.min(axis=1).reshape(grid_x.shape).astype(np.float32)


def _clearance_field(
    grid_x: np.ndarray,
    grid_y: np.ndarray,
    *,
    bounds: CorridorBounds,
    aabbs: tuple[MovingAabbHazard, ...],
    aabb_trajectories: tuple[AabbTrajectoryHazard, ...],
    piecewise_aabbs: tuple[PiecewiseAabbHazard, ...],
    segments: tuple[SegmentHazard, ...],
    segment_trajectories: tuple[SegmentTrajectoryHazard, ...],
    packed_segments: PackedSegmentFrames | None,
    frame: int,
    config: CorridorConfig,
    annular_sector_trajectories: tuple[
        AnnularSectorTrajectoryHazard, ...
    ] = (),
) -> tuple[np.ndarray, np.ndarray]:
    frame_aabbs = tuple(
        sample
        for trajectory in aabb_trajectories
        if (sample := trajectory.sample(frame)) is not None
    ) + tuple(
        sample
        for trajectory in piecewise_aabbs
        if (sample := trajectory.sample(frame)) is not None
    )
    frame_segments = segments + tuple(
        sample
        for trajectory in segment_trajectories
        if (sample := trajectory.sample(frame)) is not None
    )
    segment_clearance = _segment_clearance_field(
        grid_x,
        grid_y,
        frame_segments,
        frame=frame,
        player_radius=config.player_radius,
    )
    if packed_segments is not None:
        segment_clearance = np.minimum(
            segment_clearance,
            _packed_segment_clearance_field(
                grid_x,
                grid_y,
                packed_segments,
                frame=frame,
                player_radius=config.player_radius,
            ),
        )
    hazard_clearance = np.minimum(
        np.minimum(
            _aabb_clearance_field(
                grid_x,
                grid_y,
                aabbs,
                frame=frame,
                player_radius=config.player_radius,
            ),
            _aabb_sample_clearance_field(
                grid_x,
                grid_y,
                frame_aabbs,
                frame=frame,
                player_radius=config.player_radius,
            ),
        ),
        segment_clearance,
    )
    hazard_clearance = np.minimum(
        hazard_clearance,
        _annular_sector_clearance_field(
            grid_x,
            grid_y,
            annular_sector_trajectories,
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
    robust_clearance = np.minimum(
        hazard_clearance, boundary_clearance
    )
    return robust_clearance, boundary_clearance


def _hazard_clearance_volume(
    grid_x: np.ndarray,
    grid_y: np.ndarray,
    *,
    aabbs: tuple[MovingAabbHazard, ...],
    segments: tuple[SegmentHazard, ...],
    segment_trajectories: tuple[SegmentTrajectoryHazard, ...],
    config: CorridorConfig,
    aabb_trajectories: tuple[AabbTrajectoryHazard, ...] = (),
    piecewise_aabbs: tuple[PiecewiseAabbHazard, ...] = (),
    packed_segments: PackedSegmentFrames | None = None,
    annular_sector_trajectories: tuple[
        AnnularSectorTrajectoryHazard, ...
    ] = (),
) -> np.ndarray:
    """Build physical-frame clearance without treating bounds as hazards."""

    expected_frame_count = config.horizon_frames + 1
    if (
        packed_segments is not None
        and packed_segments.frame_count != expected_frame_count
    ):
        raise ValueError(
            "packed segment frame count does not match planning horizon"
        )
    native_volume = native_backend.build_clearance_volume(
        x_axis=grid_x[0],
        y_axis=grid_y[:, 0],
        frame_count=expected_frame_count,
        player_radius=config.player_radius,
        clearance_cap=config.danger_radius,
        aabbs=aabbs,
        segments=segments,
    )
    if native_volume is not None:
        if aabb_trajectories:
            trajectory_volume = (
                native_backend.apply_aabb_trajectory_clearance(
                    x_axis=grid_x[0],
                    y_axis=grid_y[:, 0],
                    player_radius=config.player_radius,
                    aabb_trajectories=aabb_trajectories,
                    clearance_volume=native_volume,
                )
            )
            if trajectory_volume is not None:
                native_volume = trajectory_volume
            else:
                for frame in range(config.horizon_frames + 1):
                    frame_aabbs = tuple(
                        sample
                        for trajectory in aabb_trajectories
                        if (
                            sample := trajectory.sample(frame)
                        )
                        is not None
                    )
                    native_volume[frame] = np.minimum(
                        native_volume[frame],
                        _aabb_sample_clearance_field(
                            grid_x,
                            grid_y,
                            frame_aabbs,
                            frame=frame,
                            player_radius=config.player_radius,
                        ),
                    )
        if piecewise_aabbs:
            piecewise_volume = (
                native_backend.apply_piecewise_aabb_clearance(
                    x_axis=grid_x[0],
                    y_axis=grid_y[:, 0],
                    player_radius=config.player_radius,
                    piecewise_aabbs=piecewise_aabbs,
                    clearance_volume=native_volume,
                )
            )
            if piecewise_volume is not None:
                native_volume = piecewise_volume
            else:
                for frame in range(config.horizon_frames + 1):
                    frame_aabbs = tuple(
                        sample
                        for trajectory in piecewise_aabbs
                        if (
                            sample := trajectory.sample(frame)
                        )
                        is not None
                    )
                    native_volume[frame] = np.minimum(
                        native_volume[frame],
                        _aabb_sample_clearance_field(
                            grid_x,
                            grid_y,
                            frame_aabbs,
                            frame=frame,
                            player_radius=config.player_radius,
                        ),
                    )
        if segment_trajectories:
            trajectory_volume = (
                native_backend.apply_segment_trajectory_clearance(
                    x_axis=grid_x[0],
                    y_axis=grid_y[:, 0],
                    player_radius=config.player_radius,
                    segment_trajectories=segment_trajectories,
                    clearance_volume=native_volume,
                )
            )
            if trajectory_volume is not None:
                native_volume = trajectory_volume
            else:
                for frame in range(config.horizon_frames + 1):
                    frame_segments = tuple(
                        sample
                        for trajectory in segment_trajectories
                        if (
                            sample := trajectory.sample(frame)
                        )
                        is not None
                    )
                    native_volume[frame] = np.minimum(
                        native_volume[frame],
                        _segment_clearance_field(
                            grid_x,
                            grid_y,
                            frame_segments,
                            frame=frame,
                            player_radius=config.player_radius,
                        ),
                    )
        if packed_segments is not None:
            packed_volume = (
                native_backend.apply_packed_segment_clearance(
                    x_axis=grid_x[0],
                    y_axis=grid_y[:, 0],
                    player_radius=config.player_radius,
                    packed_segments=packed_segments,
                    clearance_volume=native_volume,
                )
            )
            if packed_volume is not None:
                native_volume = packed_volume
            else:
                for frame in range(config.horizon_frames + 1):
                    native_volume[frame] = np.minimum(
                        native_volume[frame],
                        _packed_segment_clearance_field(
                            grid_x,
                            grid_y,
                            packed_segments,
                            frame=frame,
                            player_radius=config.player_radius,
                        ),
                    )
        if annular_sector_trajectories:
            sector_volume = (
                native_backend.apply_annular_sector_trajectory_clearance(
                    x_axis=grid_x[0],
                    y_axis=grid_y[:, 0],
                    player_radius=config.player_radius,
                    annular_sector_trajectories=(
                        annular_sector_trajectories
                    ),
                    clearance_volume=native_volume,
                )
            )
            if sector_volume is not None:
                native_volume = sector_volume
            else:
                for frame in range(config.horizon_frames + 1):
                    native_volume[frame] = np.minimum(
                        native_volume[frame],
                        _annular_sector_clearance_field(
                            grid_x,
                            grid_y,
                            annular_sector_trajectories,
                            frame=frame,
                            player_radius=config.player_radius,
                        ),
                    )
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
        frame_aabbs = tuple(
            sample
            for trajectory in aabb_trajectories
            if (sample := trajectory.sample(frame)) is not None
        ) + tuple(
            sample
            for trajectory in piecewise_aabbs
            if (sample := trajectory.sample(frame)) is not None
        )
        volume[frame] = np.minimum(
            volume[frame],
            _aabb_sample_clearance_field(
                grid_x,
                grid_y,
                frame_aabbs,
                frame=frame,
                player_radius=config.player_radius,
            ),
        )
        frame_segments = segments + tuple(
            sample
            for trajectory in segment_trajectories
            if (sample := trajectory.sample(frame)) is not None
        )
        volume[frame] = np.minimum(
            volume[frame],
            _segment_clearance_field(
                grid_x,
                grid_y,
                frame_segments,
                frame=frame,
                player_radius=config.player_radius,
            ),
        )
        if packed_segments is not None:
            volume[frame] = np.minimum(
                volume[frame],
                _packed_segment_clearance_field(
                    grid_x,
                    grid_y,
                    packed_segments,
                    frame=frame,
                    player_radius=config.player_radius,
                ),
            )
        if annular_sector_trajectories:
            volume[frame] = np.minimum(
                volume[frame],
                _annular_sector_clearance_field(
                    grid_x,
                    grid_y,
                    annular_sector_trajectories,
                    frame=frame,
                    player_radius=config.player_radius,
                ),
            )
    return volume


aabb_clearance_field = _aabb_clearance_field
aabb_sample_clearance_field = _aabb_sample_clearance_field
annular_sector_clearance_field = _annular_sector_clearance_field
aabb_clearance_volume = _aabb_clearance_volume
segment_clearance_field = _segment_clearance_field
packed_segment_clearance_field = _packed_segment_clearance_field
clearance_field = _clearance_field
hazard_clearance_volume = _hazard_clearance_volume


__all__ = [
    "aabb_clearance_field",
    "aabb_clearance_volume",
    "aabb_sample_clearance_field",
    "annular_sector_clearance_field",
    "clearance_field",
    "hazard_clearance_volume",
    "packed_segment_clearance_field",
    "segment_clearance_field",
]
