"""Root-relevant patch selection and conservative dependency closure."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from ..grid import axis
from ..prepared import PreparedCorridorProblem
from .cells import (
    ActionMaskBounds,
    SpatialCellPartition,
    build_spatial_cell_partition,
    lift_coarse_action_masks,
)
from .scope import PreparedDualBoundScope
from .transitions import (
    build_transition_lattice,
    forward_reachable_tube,
    terminal_coreachable_tube,
)


def _readonly(values: np.ndarray, dtype: np.dtype | type) -> np.ndarray:
    result = np.array(values, dtype=dtype, copy=True)
    result.setflags(write=False)
    return result


def _full_action_mask(action_count: int) -> np.uint64:
    if not 1 <= action_count <= 64:
        raise ValueError("adaptive action masks support one to 64 actions")
    return np.uint64((1 << action_count) - 1)


def trivial_coarse_action_bounds(
    *,
    prepared_problem: PreparedCorridorProblem,
) -> ActionMaskBounds:
    """Return the sound unresolved default for every nonterminal coarse state."""

    action_count = len(prepared_problem.robust_control.actions)
    layer_count = (
        prepared_problem.config.horizon_frames
        // prepared_problem.config.frames_per_layer
    )
    shape = (
        layer_count,
        action_count,
        prepared_problem.y_axis.size,
        prepared_problem.x_axis.size,
    )
    return ActionMaskBounds(
        lower=np.zeros(shape, dtype=np.uint64),
        upper=np.full(
            shape,
            _full_action_mask(action_count),
            dtype=np.uint64,
        ),
        action_count=action_count,
    )


def _dilate_spatial(states: np.ndarray, radius: int) -> np.ndarray:
    if radius < 0:
        raise ValueError("refinement halo cannot be negative")
    result = np.array(states, dtype=np.bool_, copy=True)
    if radius == 0:
        return result
    source = np.asarray(states, dtype=np.bool_)
    rows = source.shape[-2]
    columns = source.shape[-1]
    for row_offset in range(-radius, radius + 1):
        source_row_start = max(0, -row_offset)
        source_row_end = min(rows, rows - row_offset)
        target_row_start = source_row_start + row_offset
        target_row_end = source_row_end + row_offset
        for column_offset in range(-radius, radius + 1):
            source_column_start = max(0, -column_offset)
            source_column_end = min(columns, columns - column_offset)
            target_column_start = source_column_start + column_offset
            target_column_end = source_column_end + column_offset
            result[
                ...,
                target_row_start:target_row_end,
                target_column_start:target_column_end,
            ] |= source[
                ...,
                source_row_start:source_row_end,
                source_column_start:source_column_end,
            ]
    return result


@dataclass(frozen=True)
class QueryLocalRefinementPatch:
    fine_step: float
    fine_x: np.ndarray
    fine_y: np.ndarray
    partition: SpatialCellPartition
    incoming_bounds: ActionMaskBounds
    requested_states: np.ndarray
    clearance_row_start: int
    clearance_row_end: int
    clearance_column_start: int
    clearance_column_end: int
    dependency_halo_cells: int
    state_halo_cells: int
    root_layer: int
    root_active_index: int
    root_coarse_row: int
    root_coarse_column: int
    root_fine_row: int
    root_fine_column: int

    def __post_init__(self) -> None:
        fine_x = _readonly(self.fine_x, np.float64)
        fine_y = _readonly(self.fine_y, np.float64)
        requested = _readonly(self.requested_states, np.bool_)
        expected_state_shape = (
            self.incoming_bounds.lower.shape[0] + 1,
            self.incoming_bounds.lower.shape[1],
            fine_y.size,
            fine_x.size,
        )
        if requested.shape != expected_state_shape:
            raise ValueError(
                "requested refinement states do not match fine horizon/planes"
            )
        if not np.any(requested):
            raise ValueError("query-local refinement patch cannot be empty")
        if not 0 <= self.root_layer < self.incoming_bounds.lower.shape[0]:
            raise ValueError("refinement root layer is outside the horizon")
        if not (
            0 <= self.clearance_row_start < self.clearance_row_end <= fine_y.size
            and 0
            <= self.clearance_column_start
            < self.clearance_column_end
            <= fine_x.size
        ):
            raise ValueError("clearance rectangle is outside the fine lattice")
        if self.dependency_halo_cells < 0 or self.state_halo_cells < 0:
            raise ValueError("refinement halo sizes must be nonnegative")
        object.__setattr__(self, "fine_x", fine_x)
        object.__setattr__(self, "fine_y", fine_y)
        object.__setattr__(self, "requested_states", requested)

    @property
    def spatial_fraction(self) -> float:
        rows = self.clearance_row_end - self.clearance_row_start
        columns = self.clearance_column_end - self.clearance_column_start
        return (rows * columns) / (self.fine_y.size * self.fine_x.size)


def build_query_local_refinement_patch(
    *,
    prepared_problem: PreparedCorridorProblem,
    scope: PreparedDualBoundScope,
    incoming_bounds: ActionMaskBounds,
    fine_step: float,
    coarse_candidate_states: np.ndarray | None = None,
    coarse_candidate_halo_cells: int = 0,
    state_halo_cells: int = 1,
    allow_full_field: bool = False,
) -> QueryLocalRefinementPatch:
    """Select ambiguous root-relevant states and their clearance dependency halo."""

    if (
        not math.isfinite(fine_step)
        or fine_step <= 0.0
        or fine_step >= prepared_problem.config.grid_step
    ):
        raise ValueError(
            "fine refinement step must be positive and below the coarse step"
        )
    if coarse_candidate_halo_cells < 0:
        raise ValueError("coarse candidate halo cannot be negative")
    if prepared_problem.robust_control.terminal_viable is not None:
        raise ValueError(
            "query-local refinement requires an explicit fine terminal remap"
        )
    action_count = len(prepared_problem.robust_control.actions)
    layer_count = scope.layer_count
    expected_bounds_shape = (
        layer_count,
        action_count,
        prepared_problem.y_axis.size,
        prepared_problem.x_axis.size,
    )
    if (
        incoming_bounds.action_count != action_count
        or incoming_bounds.lower.shape != expected_bounds_shape
    ):
        raise ValueError("incoming bounds do not match the prepared coarse problem")

    fine_x = axis(
        prepared_problem.bounds.left,
        prepared_problem.bounds.right,
        fine_step,
    )
    fine_y = axis(
        prepared_problem.bounds.top,
        prepared_problem.bounds.bottom,
        fine_step,
    )
    partition = build_spatial_cell_partition(
        coarse_x=prepared_problem.x_axis,
        coarse_y=prepared_problem.y_axis,
        fine_x=fine_x,
        fine_y=fine_y,
    )

    fine_transitions = build_transition_lattice(
        x_axis=fine_x,
        y_axis=fine_y,
        actions=prepared_problem.robust_control.actions,
        delay_frames=prepared_problem.robust_control.delay_frames,
        config=prepared_problem.viability_config,
    )
    fine_coreachable = terminal_coreachable_tube(
        transitions=fine_transitions,
        layer_count=layer_count,
        terminal_scope=np.ones(
            fine_transitions.state_shape,
            dtype=np.bool_,
        ),
    )
    initial_fine_states = np.zeros(
        fine_transitions.state_shape,
        dtype=np.bool_,
    )
    root_fine_rows = partition.member_rows(scope.root_row)
    root_fine_columns = partition.member_columns(scope.root_column)
    initial_fine_states[
        scope.root_active_index,
        root_fine_rows[:, None],
        root_fine_columns[None, :],
    ] = True
    local_fine_forward = forward_reachable_tube(
        transitions=fine_transitions,
        layer_count=layer_count - scope.root_layer,
        initial_states=initial_fine_states,
    )
    fine_forward = np.zeros(
        (layer_count + 1,) + fine_transitions.state_shape,
        dtype=np.bool_,
    )
    fine_forward[scope.root_layer :] = local_fine_forward
    fine_relevant = fine_forward & fine_coreachable

    coarse_ambiguous = incoming_bounds.ambiguous
    if coarse_candidate_states is None:
        coarse_candidates = np.ones(
            (layer_count + 1,) + incoming_bounds.lower.shape[1:],
            dtype=np.bool_,
        )
    else:
        coarse_candidates = np.asarray(
            coarse_candidate_states,
            dtype=np.bool_,
        )
        expected_candidates_shape = (layer_count + 1,) + incoming_bounds.lower.shape[1:]
        if coarse_candidates.shape != expected_candidates_shape:
            raise ValueError(
                "coarse candidate states do not match the prepared horizon"
            )
        coarse_candidates = _dilate_spatial(
            coarse_candidates,
            coarse_candidate_halo_cells,
        )
        coarse_candidates[
            scope.root_layer,
            scope.root_active_index,
            scope.root_row,
            scope.root_column,
        ] = True
    fine_candidates = lift_coarse_action_masks(
        coarse_candidates,
        partition=partition,
    )
    fine_ambiguous = lift_coarse_action_masks(
        coarse_ambiguous,
        partition=partition,
    )
    requested = np.zeros_like(fine_relevant)
    requested[:-1] = fine_relevant[:-1] & fine_ambiguous & fine_candidates[:-1]
    if not np.any(requested[:-1]):
        raise ValueError("no ambiguous root-relevant state requires refinement")
    requested[-1] = fine_relevant[-1] & fine_candidates[-1]
    requested = _dilate_spatial(requested, state_halo_cells)

    footprint = np.any(requested, axis=(0, 1))
    footprint_rows, footprint_columns = np.nonzero(footprint)
    if not footprint_rows.size:
        raise ValueError("query-local refinement patch cannot be empty")
    maximum_speed = max(
        max(abs(action.velocity_x), abs(action.velocity_y))
        for action in prepared_problem.robust_control.actions
    )
    dependency_halo_cells = (
        int(
            math.ceil(
                maximum_speed * prepared_problem.config.frames_per_layer / fine_step
            )
        )
        + 1
    )
    row_start = max(
        0,
        int(np.min(footprint_rows)) - dependency_halo_cells,
    )
    row_end = min(
        fine_y.size,
        int(np.max(footprint_rows)) + dependency_halo_cells + 1,
    )
    column_start = max(
        0,
        int(np.min(footprint_columns)) - dependency_halo_cells,
    )
    column_end = min(
        fine_x.size,
        int(np.max(footprint_columns)) + dependency_halo_cells + 1,
    )
    if (
        not allow_full_field
        and row_start == 0
        and row_end == fine_y.size
        and column_start == 0
        and column_end == fine_x.size
    ):
        raise ValueError("query-local refinement expanded to a forbidden full field")
    return QueryLocalRefinementPatch(
        fine_step=fine_step,
        fine_x=fine_x,
        fine_y=fine_y,
        partition=partition,
        incoming_bounds=incoming_bounds,
        requested_states=requested,
        clearance_row_start=row_start,
        clearance_row_end=row_end,
        clearance_column_start=column_start,
        clearance_column_end=column_end,
        dependency_halo_cells=dependency_halo_cells,
        state_halo_cells=state_halo_cells,
        root_layer=scope.root_layer,
        root_active_index=scope.root_active_index,
        root_coarse_row=scope.root_row,
        root_coarse_column=scope.root_column,
        root_fine_row=int(
            np.clip(
                np.rint((scope.root_y - float(fine_y[0])) / fine_step),
                0,
                fine_y.size - 1,
            )
        ),
        root_fine_column=int(
            np.clip(
                np.rint((scope.root_x - float(fine_x[0])) / fine_step),
                0,
                fine_x.size - 1,
            )
        ),
    )


__all__ = [
    "QueryLocalRefinementPatch",
    "build_query_local_refinement_patch",
    "trivial_coarse_action_bounds",
]
