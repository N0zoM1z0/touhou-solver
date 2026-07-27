"""Shared lattice-transition construction for viability policy builders."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from .viability_types import ControlAction, ViabilityConfig


@dataclass(frozen=True)
class _TransitionBatch:
    sample_rows: np.ndarray
    sample_columns: np.ndarray
    sample_errors: np.ndarray
    sample_inside: np.ndarray
    terminal_rows: np.ndarray
    terminal_columns: np.ndarray
    terminal_inside: np.ndarray



def _uniform_step(axis: np.ndarray, name: str) -> float:
    if axis.ndim != 1 or len(axis) < 2:
        raise ValueError(f"{name} axis must contain at least two coordinates")
    differences = np.diff(axis.astype(np.float64))
    if not np.all(differences > 0.0):
        raise ValueError(f"{name} axis must be strictly increasing")
    step = float(differences[0])
    if not np.allclose(differences, step, atol=1e-6):
        raise ValueError(f"{name} axis must be uniformly spaced")
    return step



def _nearest_indices(
    values: np.ndarray,
    *,
    start: float,
    step: float,
    count: int,
    clamp: bool,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    inside = (values >= start) & (values <= start + step * (count - 1))
    if clamp:
        values = np.clip(values, start, start + step * (count - 1))
        inside = np.ones(values.shape, dtype=np.bool_)
    indices = np.rint((values - start) / step).astype(np.int32)
    indices = np.clip(indices, 0, count - 1)
    centers = start + indices.astype(np.float64) * step
    return indices, np.abs(values - centers), inside



def _build_transition_batch(
    *,
    grid_x: np.ndarray,
    grid_y: np.ndarray,
    x_step: float,
    y_step: float,
    active: ControlAction,
    actions: tuple[ControlAction, ...],
    delay_frames: tuple[int, ...],
    config: ViabilityConfig,
) -> _TransitionBatch:
    physical_steps = np.arange(
        1,
        config.frames_per_layer + 1,
        dtype=np.float64,
    )[None, None, :, None, None]
    delays = np.asarray(delay_frames, dtype=np.float64)[
        None, :, None, None, None
    ]
    active_frames = np.minimum(physical_steps, delays)
    selected_frames = np.maximum(physical_steps - delays, 0.0)
    selected_velocity_x = np.asarray(
        [action.velocity_x for action in actions],
        dtype=np.float64,
    )[:, None, None, None, None]
    selected_velocity_y = np.asarray(
        [action.velocity_y for action in actions],
        dtype=np.float64,
    )[:, None, None, None, None]
    target_x = (
        grid_x[None, None, None, :, :]
        + active.velocity_x * active_frames
        + selected_velocity_x * selected_frames
    )
    target_y = (
        grid_y[None, None, None, :, :]
        + active.velocity_y * active_frames
        + selected_velocity_y * selected_frames
    )
    sample_columns, x_error, x_inside = _nearest_indices(
        target_x,
        start=float(grid_x[0, 0]),
        step=x_step,
        count=grid_x.shape[1],
        clamp=config.clamp_to_bounds,
    )
    sample_rows, y_error, y_inside = _nearest_indices(
        target_y,
        start=float(grid_y[0, 0]),
        step=y_step,
        count=grid_y.shape[0],
        clamp=config.clamp_to_bounds,
    )
    sample_rows = sample_rows.astype(np.int16)
    sample_columns = sample_columns.astype(np.int16)
    sample_errors = np.hypot(x_error, y_error).astype(np.float32)
    sample_inside = x_inside & y_inside
    return _TransitionBatch(
        sample_rows=sample_rows,
        sample_columns=sample_columns,
        sample_errors=sample_errors,
        sample_inside=sample_inside,
        terminal_rows=sample_rows[:, :, -1],
        terminal_columns=sample_columns[:, :, -1],
        terminal_inside=sample_inside[:, :, -1],
    )



@lru_cache(maxsize=4)
def _cached_transition_batches(
    *,
    x_start: float,
    x_step: float,
    x_count: int,
    y_start: float,
    y_step: float,
    y_count: int,
    actions: tuple[ControlAction, ...],
    config: ViabilityConfig,
) -> tuple[_TransitionBatch, ...]:
    x_axis = x_start + np.arange(x_count, dtype=np.float64) * x_step
    y_axis = y_start + np.arange(y_count, dtype=np.float64) * y_step
    grid_x, grid_y = np.meshgrid(x_axis, y_axis)
    return tuple(
        _build_transition_batch(
            grid_x=grid_x,
            grid_y=grid_y,
            x_step=x_step,
            y_step=y_step,
            active=active,
            actions=actions,
            delay_frames=tuple(range(config.frames_per_layer + 1)),
            config=config,
        )
        for active in actions
    )



__all__ = []
