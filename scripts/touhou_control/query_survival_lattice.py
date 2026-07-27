"""Shared lattice and controller-cadence validation for survival queries."""

from __future__ import annotations

import numpy as np


def normalize_decision_frame_support(
    support: tuple[int, ...] | None,
    *,
    default: int,
) -> tuple[int, ...]:
    normalized = (default,) if support is None else tuple(support)
    if (
        not normalized
        or tuple(sorted(set(normalized))) != normalized
        or normalized[0] <= 0
    ):
        raise ValueError(
            "decision-frame support must be sorted unique and positive"
        )
    return normalized


def uniform_axis(axis: np.ndarray, name: str) -> tuple[np.ndarray, float]:
    values = np.asarray(axis, dtype=np.float64)
    if values.ndim != 1 or len(values) < 2:
        raise ValueError(f"{name} axis must contain at least two points")
    differences = np.diff(values)
    if not np.all(differences > 0.0):
        raise ValueError(f"{name} axis must be strictly increasing")
    step = float(differences[0])
    if not np.allclose(differences, step, rtol=0.0, atol=1e-6):
        raise ValueError(f"{name} axis must be uniform")
    return values, step


__all__ = [
    "normalize_decision_frame_support",
    "uniform_axis",
]
