"""Typed NumPy coercion helpers shared by native binding domains."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, DTypeLike


def as_contiguous_array(
    values: ArrayLike,
    dtype: DTypeLike | None = None,
) -> np.ndarray:
    """Apply NumPy's existing contiguous/dtype coercion without extra policy."""

    return np.ascontiguousarray(values, dtype=dtype)


def attribute_array(
    items: tuple[object, ...],
    name: str,
) -> np.ndarray:
    """Copy one float32 object attribute into a contiguous native array."""

    return np.fromiter(
        (float(getattr(item, name)) for item in items),
        dtype=np.float32,
        count=len(items),
    )


def attribute_array64(
    items: tuple[object, ...],
    name: str,
) -> np.ndarray:
    """Copy one float64 object attribute into a contiguous native array."""

    return np.fromiter(
        (float(getattr(item, name)) for item in items),
        dtype=np.float64,
        count=len(items),
    )
