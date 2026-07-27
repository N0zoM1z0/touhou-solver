"""Spatial cell partitions and lower/reference/upper action-mask checks."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


def _readonly_array(
    values: np.ndarray,
    *,
    dtype: np.dtype | type,
) -> np.ndarray:
    result = np.array(values, dtype=dtype, copy=True)
    result.setflags(write=False)
    return result


def _validated_axis(values: np.ndarray, name: str) -> np.ndarray:
    axis = _readonly_array(values, dtype=np.float64)
    if axis.ndim != 1 or axis.size < 2:
        raise ValueError(f"{name} axis must contain at least two points")
    if not np.all(np.isfinite(axis)) or np.any(np.diff(axis) <= 0.0):
        raise ValueError(f"{name} axis must be finite and strictly increasing")
    return axis


def _uniform_step(values: np.ndarray, name: str) -> float:
    differences = np.diff(values)
    step = float(differences[0])
    if not np.allclose(differences, step, rtol=0.0, atol=1e-6):
        raise ValueError(f"{name} axis must be uniformly spaced")
    return step


def _full_action_mask(action_count: int) -> np.uint64:
    if not 1 <= action_count <= 64:
        raise ValueError("action masks require between one and 64 actions")
    return np.uint64((1 << action_count) - 1)


@dataclass(frozen=True)
class SpatialCellPartition:
    """Map every fine lattice state to one coarse round-to-even cell."""

    coarse_x: np.ndarray
    coarse_y: np.ndarray
    fine_x: np.ndarray
    fine_y: np.ndarray
    fine_columns_to_coarse: np.ndarray
    fine_rows_to_coarse: np.ndarray

    def __post_init__(self) -> None:
        coarse_x = _validated_axis(self.coarse_x, "coarse x")
        coarse_y = _validated_axis(self.coarse_y, "coarse y")
        fine_x = _validated_axis(self.fine_x, "fine x")
        fine_y = _validated_axis(self.fine_y, "fine y")
        columns = _readonly_array(
            self.fine_columns_to_coarse,
            dtype=np.intp,
        )
        rows = _readonly_array(self.fine_rows_to_coarse, dtype=np.intp)
        if columns.shape != fine_x.shape or rows.shape != fine_y.shape:
            raise ValueError("fine-to-coarse maps must match their fine axes")
        if (
            np.any(columns < 0)
            or np.any(columns >= coarse_x.size)
            or np.any(rows < 0)
            or np.any(rows >= coarse_y.size)
        ):
            raise ValueError("fine-to-coarse map contains an invalid cell")
        if np.unique(columns).size != coarse_x.size:
            raise ValueError("every coarse column must contain a fine point")
        if np.unique(rows).size != coarse_y.size:
            raise ValueError("every coarse row must contain a fine point")
        object.__setattr__(self, "coarse_x", coarse_x)
        object.__setattr__(self, "coarse_y", coarse_y)
        object.__setattr__(self, "fine_x", fine_x)
        object.__setattr__(self, "fine_y", fine_y)
        object.__setattr__(self, "fine_columns_to_coarse", columns)
        object.__setattr__(self, "fine_rows_to_coarse", rows)

    @property
    def coarse_shape(self) -> tuple[int, int]:
        return (self.coarse_y.size, self.coarse_x.size)

    @property
    def fine_shape(self) -> tuple[int, int]:
        return (self.fine_y.size, self.fine_x.size)

    def member_rows(self, coarse_row: int) -> np.ndarray:
        if not 0 <= coarse_row < self.coarse_y.size:
            raise ValueError("coarse row is outside the partition")
        return np.flatnonzero(self.fine_rows_to_coarse == coarse_row)

    def member_columns(self, coarse_column: int) -> np.ndarray:
        if not 0 <= coarse_column < self.coarse_x.size:
            raise ValueError("coarse column is outside the partition")
        return np.flatnonzero(self.fine_columns_to_coarse == coarse_column)


def build_spatial_cell_partition(
    *,
    coarse_x: np.ndarray,
    coarse_y: np.ndarray,
    fine_x: np.ndarray,
    fine_y: np.ndarray,
) -> SpatialCellPartition:
    """Build the exact lattice projection partition used by policy queries."""

    coarse_x = _validated_axis(coarse_x, "coarse x")
    coarse_y = _validated_axis(coarse_y, "coarse y")
    fine_x = _validated_axis(fine_x, "fine x")
    fine_y = _validated_axis(fine_y, "fine y")
    coarse_x_step = _uniform_step(coarse_x, "coarse x")
    coarse_y_step = _uniform_step(coarse_y, "coarse y")
    if (
        not math.isclose(float(fine_x[0]), float(coarse_x[0]), abs_tol=1e-6)
        or not math.isclose(
            float(fine_x[-1]),
            float(coarse_x[-1]),
            abs_tol=1e-6,
        )
        or not math.isclose(
            float(fine_y[0]),
            float(coarse_y[0]),
            abs_tol=1e-6,
        )
        or not math.isclose(
            float(fine_y[-1]),
            float(coarse_y[-1]),
            abs_tol=1e-6,
        )
    ):
        raise ValueError("coarse and fine axes must cover identical bounds")
    fine_columns_to_coarse = np.rint((fine_x - coarse_x[0]) / coarse_x_step).astype(
        np.intp
    )
    fine_rows_to_coarse = np.rint((fine_y - coarse_y[0]) / coarse_y_step).astype(
        np.intp
    )
    np.clip(
        fine_columns_to_coarse,
        0,
        coarse_x.size - 1,
        out=fine_columns_to_coarse,
    )
    np.clip(
        fine_rows_to_coarse,
        0,
        coarse_y.size - 1,
        out=fine_rows_to_coarse,
    )
    return SpatialCellPartition(
        coarse_x=coarse_x,
        coarse_y=coarse_y,
        fine_x=fine_x,
        fine_y=fine_y,
        fine_columns_to_coarse=fine_columns_to_coarse,
        fine_rows_to_coarse=fine_rows_to_coarse,
    )


@dataclass(frozen=True)
class ActionMaskBounds:
    """Per-cell lower and upper masks for one declared action alphabet."""

    lower: np.ndarray
    upper: np.ndarray
    action_count: int

    def __post_init__(self) -> None:
        full_mask = _full_action_mask(self.action_count)
        lower = _readonly_array(self.lower, dtype=np.uint64)
        upper = _readonly_array(self.upper, dtype=np.uint64)
        if lower.shape != upper.shape or lower.ndim < 2:
            raise ValueError("lower and upper masks must share at least two dimensions")
        outside_mask = np.bitwise_not(full_mask)
        if np.any(lower & outside_mask) or np.any(upper & outside_mask):
            raise ValueError("action mask contains a bit outside the alphabet")
        if np.any(lower & np.bitwise_not(upper)):
            raise ValueError("lower action masks must be subsets of upper")
        object.__setattr__(self, "lower", lower)
        object.__setattr__(self, "upper", upper)

    @property
    def ambiguous(self) -> np.ndarray:
        result = self.lower != self.upper
        result.setflags(write=False)
        return result


def aggregate_fine_action_mask_bounds(
    *,
    fine_action_masks: np.ndarray,
    partition: SpatialCellPartition,
    action_count: int,
) -> ActionMaskBounds:
    """Intersect/union fine masks without collapsing any leading dimension."""

    full_mask = _full_action_mask(action_count)
    fine_masks = np.asarray(fine_action_masks)
    if fine_masks.ndim < 2 or fine_masks.shape[-2:] != partition.fine_shape:
        raise ValueError("fine action masks must end with the partition fine shape")
    if not np.issubdtype(fine_masks.dtype, np.unsignedinteger):
        raise ValueError("fine action masks must use an unsigned integer dtype")
    fine_masks = fine_masks.astype(np.uint64, copy=False)
    if np.any(fine_masks & np.bitwise_not(full_mask)):
        raise ValueError("fine action mask contains an unknown action bit")

    leading_shape = fine_masks.shape[:-2]
    coarse_shape = leading_shape + partition.coarse_shape
    lower = np.zeros(coarse_shape, dtype=np.uint64)
    upper = np.zeros(coarse_shape, dtype=np.uint64)
    for coarse_row in range(partition.coarse_shape[0]):
        rows = partition.member_rows(coarse_row)
        for coarse_column in range(partition.coarse_shape[1]):
            columns = partition.member_columns(coarse_column)
            members = fine_masks[..., rows[:, None], columns[None, :]]
            flattened = members.reshape(leading_shape + (-1,))
            lower[..., coarse_row, coarse_column] = np.bitwise_and.reduce(
                flattened,
                axis=-1,
            )
            upper[..., coarse_row, coarse_column] = np.bitwise_or.reduce(
                flattened,
                axis=-1,
            )
    return ActionMaskBounds(
        lower=lower,
        upper=upper,
        action_count=action_count,
    )


def lift_coarse_action_masks(
    masks: np.ndarray,
    *,
    partition: SpatialCellPartition,
) -> np.ndarray:
    """Lift cell masks to fine points through the exact partition map."""

    masks = np.asarray(masks)
    if masks.ndim < 2 or masks.shape[-2:] != partition.coarse_shape:
        raise ValueError("coarse masks must end with the partition coarse shape")
    lifted = masks[
        ...,
        partition.fine_rows_to_coarse[:, None],
        partition.fine_columns_to_coarse[None, :],
    ]
    lifted.setflags(write=False)
    return lifted


@dataclass(frozen=True)
class ReferenceInclusionViolation:
    index: tuple[int, ...]
    action_bits: int


@dataclass(frozen=True)
class ReferenceInclusionReport:
    false_safe_action_count: int
    missing_upper_action_count: int
    first_false_safe: ReferenceInclusionViolation | None
    first_missing_upper: ReferenceInclusionViolation | None

    @property
    def passed(self) -> bool:
        return (
            self.false_safe_action_count == 0 and self.missing_upper_action_count == 0
        )


def _first_violation(
    values: np.ndarray,
) -> ReferenceInclusionViolation | None:
    locations = np.argwhere(values != 0)
    if not locations.size:
        return None
    index = tuple(int(value) for value in locations[0])
    return ReferenceInclusionViolation(
        index=index,
        action_bits=int(values[index]),
    )


def _count_action_bits(values: np.ndarray) -> int:
    return sum(int(value).bit_count() for value in values.flat)


def check_fine_reference_inclusion(
    *,
    bounds: ActionMaskBounds,
    fine_reference_masks: np.ndarray,
    partition: SpatialCellPartition,
) -> ReferenceInclusionReport:
    """Check ``lift(lower) subset reference subset lift(upper)`` pointwise."""

    reference = np.asarray(fine_reference_masks)
    expected_shape = bounds.lower.shape[:-2] + partition.fine_shape
    if reference.shape != expected_shape:
        raise ValueError(
            f"fine reference shape must be {expected_shape}, got {reference.shape}"
        )
    if not np.issubdtype(reference.dtype, np.unsignedinteger):
        raise ValueError("fine reference masks must be unsigned integers")
    reference = reference.astype(np.uint64, copy=False)
    full_mask = _full_action_mask(bounds.action_count)
    if np.any(reference & np.bitwise_not(full_mask)):
        raise ValueError("fine reference contains an unknown action bit")
    lifted_lower = lift_coarse_action_masks(
        bounds.lower,
        partition=partition,
    )
    lifted_upper = lift_coarse_action_masks(
        bounds.upper,
        partition=partition,
    )
    false_safe = lifted_lower & np.bitwise_not(reference) & full_mask
    missing_upper = reference & np.bitwise_not(lifted_upper) & full_mask
    return ReferenceInclusionReport(
        false_safe_action_count=_count_action_bits(false_safe),
        missing_upper_action_count=_count_action_bits(missing_upper),
        first_false_safe=_first_violation(false_safe),
        first_missing_upper=_first_violation(missing_upper),
    )


__all__ = [
    "ActionMaskBounds",
    "ReferenceInclusionReport",
    "ReferenceInclusionViolation",
    "SpatialCellPartition",
    "aggregate_fine_action_mask_bounds",
    "build_spatial_cell_partition",
    "check_fine_reference_inclusion",
    "lift_coarse_action_masks",
]
