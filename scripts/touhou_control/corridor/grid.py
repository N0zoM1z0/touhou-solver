"""Lattice helpers for game-neutral corridor planning."""

from __future__ import annotations

import math

import numpy as np

from .model import CorridorBounds, CorridorConfig


def axis(start: float, end: float, step: float) -> np.ndarray:
    count = int(round((end - start) / step))
    if not math.isclose(start + count * step, end, abs_tol=1e-5):
        raise ValueError("bounds must be an integer number of grid steps")
    return np.linspace(start, end, count + 1, dtype=np.float32)


def lane(x: float, bounds: CorridorBounds) -> str:
    third = (bounds.right - bounds.left) / 3.0
    if x < bounds.left + third:
        return "left"
    if x > bounds.right - third:
        return "right"
    return "center"


def movement_offsets(
    config: CorridorConfig,
) -> tuple[tuple[int, int], ...]:
    max_cells = int(
        math.ceil(
            config.cardinal_speed
            * config.frames_per_layer
            / config.grid_step
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
    offsets.sort(
        key=lambda item: (
            abs(item[0]) + abs(item[1]),
            item[0],
            item[1],
        )
    )
    return tuple(offsets)


def shift_from_source(
    values: np.ndarray,
    dy: int,
    dx: int,
    fill: float,
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


__all__ = ["axis", "lane", "movement_offsets", "shift_from_source"]
