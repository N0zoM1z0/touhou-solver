"""Validated lower/upper result artifact for one query-local patch."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .cells import ActionMaskBounds, aggregate_fine_action_mask_bounds
from .patch import QueryLocalRefinementPatch, _full_action_mask, _readonly


@dataclass(frozen=True)
class QueryLocalDualBoundResult:
    patch: QueryLocalRefinementPatch
    lower_viable: np.ndarray
    upper_viable: np.ndarray
    lower_action_masks: np.ndarray
    upper_action_masks: np.ndarray
    lower_branch_action_masks: np.ndarray
    upper_branch_action_masks: np.ndarray
    exact_action_masks: np.ndarray
    processed_states: np.ndarray
    status: str
    elapsed_ms: float

    def __post_init__(self) -> None:
        lower_viable = _readonly(self.lower_viable, np.bool_)
        upper_viable = _readonly(self.upper_viable, np.bool_)
        lower_masks = _readonly(self.lower_action_masks, np.uint64)
        upper_masks = _readonly(self.upper_action_masks, np.uint64)
        lower_branches = _readonly(
            self.lower_branch_action_masks,
            np.uint64,
        )
        upper_branches = _readonly(
            self.upper_branch_action_masks,
            np.uint64,
        )
        exact_masks = _readonly(self.exact_action_masks, np.uint64)
        processed = _readonly(self.processed_states, np.bool_)
        action_count = self.patch.incoming_bounds.action_count
        layer_count = self.patch.incoming_bounds.lower.shape[0]
        state_shape = (
            layer_count + 1,
            action_count,
            self.patch.fine_y.size,
            self.patch.fine_x.size,
        )
        action_shape = (
            layer_count,
            action_count,
            self.patch.fine_y.size,
            self.patch.fine_x.size,
        )
        if (
            lower_viable.shape != state_shape
            or upper_viable.shape != state_shape
            or processed.shape != state_shape
            or lower_masks.shape != action_shape
            or upper_masks.shape != action_shape
            or exact_masks.shape != action_shape
        ):
            raise ValueError("query-local result arrays have inconsistent shapes")
        if (
            lower_branches.ndim != 5
            or upper_branches.shape != lower_branches.shape
            or lower_branches.shape[:2] != action_shape[:2]
            or lower_branches.shape[3:] != action_shape[2:]
        ):
            raise ValueError(
                "branch masks must have layer, active, delay, row, column axes"
            )
        full_mask = _full_action_mask(action_count)
        if (
            np.any(lower_masks & np.bitwise_not(upper_masks))
            or np.any(lower_branches & np.bitwise_not(upper_branches))
            or np.any(exact_masks & np.bitwise_not(full_mask))
        ):
            raise ValueError("query-local result violates its mask bounds")
        if np.any(lower_viable & np.logical_not(upper_viable)):
            raise ValueError("lower viability must be a subset of upper")
        if self.status not in {"complete", "deadline", "root_sufficient"}:
            raise ValueError("unknown query-local completion status")
        if not math.isfinite(self.elapsed_ms) or self.elapsed_ms < 0.0:
            raise ValueError("query-local elapsed time must be nonnegative")
        object.__setattr__(self, "lower_viable", lower_viable)
        object.__setattr__(self, "upper_viable", upper_viable)
        object.__setattr__(self, "lower_action_masks", lower_masks)
        object.__setattr__(self, "upper_action_masks", upper_masks)
        object.__setattr__(
            self,
            "lower_branch_action_masks",
            lower_branches,
        )
        object.__setattr__(
            self,
            "upper_branch_action_masks",
            upper_branches,
        )
        object.__setattr__(self, "exact_action_masks", exact_masks)
        object.__setattr__(self, "processed_states", processed)

    @property
    def root_lower_mask(self) -> int:
        rows = self.patch.partition.member_rows(self.patch.root_coarse_row)
        columns = self.patch.partition.member_columns(self.patch.root_coarse_column)
        members = self.lower_action_masks[
            self.patch.root_layer,
            self.patch.root_active_index,
            rows[:, None],
            columns[None, :],
        ]
        return int(np.bitwise_and.reduce(members.reshape(-1)))

    @property
    def root_upper_mask(self) -> int:
        rows = self.patch.partition.member_rows(self.patch.root_coarse_row)
        columns = self.patch.partition.member_columns(self.patch.root_coarse_column)
        members = self.upper_action_masks[
            self.patch.root_layer,
            self.patch.root_active_index,
            rows[:, None],
            columns[None, :],
        ]
        return int(np.bitwise_or.reduce(members.reshape(-1)))

    @property
    def root_point_lower_mask(self) -> int:
        return int(
            self.lower_action_masks[
                self.patch.root_layer,
                self.patch.root_active_index,
                self.patch.root_fine_row,
                self.patch.root_fine_column,
            ]
        )

    @property
    def root_point_upper_mask(self) -> int:
        return int(
            self.upper_action_masks[
                self.patch.root_layer,
                self.patch.root_active_index,
                self.patch.root_fine_row,
                self.patch.root_fine_column,
            ]
        )

    def aggregate_to_coarse(self) -> ActionMaskBounds:
        lower = aggregate_fine_action_mask_bounds(
            fine_action_masks=self.lower_action_masks,
            partition=self.patch.partition,
            action_count=self.patch.incoming_bounds.action_count,
        ).lower
        upper = aggregate_fine_action_mask_bounds(
            fine_action_masks=self.upper_action_masks,
            partition=self.patch.partition,
            action_count=self.patch.incoming_bounds.action_count,
        ).upper
        return ActionMaskBounds(
            lower=lower,
            upper=upper,
            action_count=self.patch.incoming_bounds.action_count,
        )


__all__ = ["QueryLocalDualBoundResult"]
