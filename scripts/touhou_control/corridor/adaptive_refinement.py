"""Offline query-local dual-bound refinement over a prepared corridor problem.

The solver in this module is intentionally sparse in *work* while retaining
full-lattice arrays as a simple proof artifact.  States outside the requested
root-relevant patch keep their incoming sound bounds.  With trivial incoming
bounds this means lower zero and upper all actions.

Every recomputed transition samples the declared hazard geometry at the fine
lattice, subtracts nearest-lattice error exactly as the dense recurrence does,
and uses lower/upper successor viability separately.  A deadline can stop the
backward pass at any state boundary without making unfinished work look losing.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, replace

import numpy as np

from ..viability import build_robust_viability_policy
from .clearance import hazard_clearance_volume
from .dual_bounds import (
    ActionMaskBounds,
    PreparedDualBoundScope,
    SpatialCellPartition,
    aggregate_fine_action_mask_bounds,
    build_spatial_cell_partition,
    build_transition_lattice,
    forward_reachable_tube,
    lift_coarse_action_masks,
    terminal_coreachable_tube,
)
from .grid import axis
from .prepared import PreparedCorridorProblem


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


def _build_patch_clearance(
    *,
    prepared_problem: PreparedCorridorProblem,
    patch: QueryLocalRefinementPatch,
) -> np.ndarray:
    fine_config = replace(
        prepared_problem.config,
        grid_step=patch.fine_step,
    )
    clearance_x = patch.fine_x[
        patch.clearance_column_start : patch.clearance_column_end
    ].astype(np.float32)
    clearance_y = patch.fine_y[
        patch.clearance_row_start : patch.clearance_row_end
    ].astype(np.float32)
    grid_x, grid_y = np.meshgrid(clearance_x, clearance_y)
    return hazard_clearance_volume(
        grid_x,
        grid_y,
        aabbs=prepared_problem.aabbs,
        aabb_trajectories=prepared_problem.aabb_trajectories,
        piecewise_aabbs=prepared_problem.piecewise_aabbs,
        segments=prepared_problem.segments,
        segment_trajectories=prepared_problem.segment_trajectories,
        packed_segments=prepared_problem.packed_segments,
        config=fine_config,
    )


def _sample_branch(
    *,
    prepared_problem: PreparedCorridorProblem,
    patch: QueryLocalRefinementPatch,
    clearance_volume: np.ndarray,
    layer: int,
    source_row: int,
    source_column: int,
    active_index: int,
    selected_index: int,
    delay: int,
) -> tuple[bool, bool, int, int]:
    """Return known, path-safe, successor row, and successor column."""

    actions = prepared_problem.robust_control.actions
    active = actions[active_index]
    selected = actions[selected_index]
    x = float(patch.fine_x[source_column])
    y = float(patch.fine_y[source_row])
    x_start = float(patch.fine_x[0])
    x_end = float(patch.fine_x[-1])
    y_start = float(patch.fine_y[0])
    y_end = float(patch.fine_y[-1])
    start_frame = layer * prepared_problem.config.frames_per_layer
    successor_row = source_row
    successor_column = source_column
    path_safe = True
    for physical_step in range(
        1,
        prepared_problem.config.frames_per_layer + 1,
    ):
        active_frames = min(physical_step, delay)
        selected_frames = max(physical_step - delay, 0)
        target_x = (
            x
            + active.velocity_x * active_frames
            + selected.velocity_x * selected_frames
        )
        target_y = (
            y
            + active.velocity_y * active_frames
            + selected.velocity_y * selected_frames
        )
        inside = x_start <= target_x <= x_end and y_start <= target_y <= y_end
        if prepared_problem.viability_config.clamp_to_bounds:
            target_x = min(x_end, max(x_start, target_x))
            target_y = min(y_end, max(y_start, target_y))
            inside = True
        if not inside:
            return (True, False, successor_row, successor_column)
        successor_column = int(
            np.clip(
                np.rint((target_x - x_start) / patch.fine_step),
                0,
                patch.fine_x.size - 1,
            )
        )
        successor_row = int(
            np.clip(
                np.rint((target_y - y_start) / patch.fine_step),
                0,
                patch.fine_y.size - 1,
            )
        )
        if not (
            patch.clearance_row_start <= successor_row < patch.clearance_row_end
            and patch.clearance_column_start
            <= successor_column
            < patch.clearance_column_end
        ):
            return (False, False, successor_row, successor_column)
        projected_x = float(patch.fine_x[successor_column])
        projected_y = float(patch.fine_y[successor_row])
        sample_error = math.hypot(
            target_x - projected_x,
            target_y - projected_y,
        )
        clearance = float(
            clearance_volume[
                start_frame + physical_step,
                successor_row - patch.clearance_row_start,
                successor_column - patch.clearance_column_start,
            ]
        )
        if (
            clearance - sample_error
            <= prepared_problem.viability_config.required_clearance
        ):
            path_safe = False
    return (True, path_safe, successor_row, successor_column)


def solve_query_local_dual_bounds(
    *,
    prepared_problem: PreparedCorridorProblem,
    patch: QueryLocalRefinementPatch,
    deadline_monotonic: float | None = None,
    stop_when_root_sufficient: bool = True,
) -> QueryLocalDualBoundResult:
    """Tighten sound fine bounds inside one root-relevant patch."""

    started = time.perf_counter()
    if deadline_monotonic is not None and not math.isfinite(deadline_monotonic):
        raise ValueError("query-local deadline must be finite")
    action_count = len(prepared_problem.robust_control.actions)
    delay_frames = prepared_problem.robust_control.delay_frames
    layer_count = patch.incoming_bounds.lower.shape[0]
    full_mask = _full_action_mask(action_count)
    fine_shape = (patch.fine_y.size, patch.fine_x.size)
    action_shape = (layer_count, action_count) + fine_shape
    state_shape = (layer_count + 1, action_count) + fine_shape

    incoming_lower = lift_coarse_action_masks(
        patch.incoming_bounds.lower,
        partition=patch.partition,
    ).astype(np.uint64, copy=True)
    incoming_upper = lift_coarse_action_masks(
        patch.incoming_bounds.upper,
        partition=patch.partition,
    ).astype(np.uint64, copy=True)
    lower_masks = incoming_lower
    upper_masks = incoming_upper
    lower_viable = np.zeros(state_shape, dtype=np.bool_)
    upper_viable = np.ones(state_shape, dtype=np.bool_)
    lower_viable[:-1] = lower_masks != 0
    upper_viable[:-1] = upper_masks != 0
    lower_branches = np.zeros(
        (layer_count, action_count, len(delay_frames)) + fine_shape,
        dtype=np.uint64,
    )
    upper_branches = np.full(
        lower_branches.shape,
        full_mask,
        dtype=np.uint64,
    )
    exact_masks = np.zeros(action_shape, dtype=np.uint64)
    processed = np.zeros(state_shape, dtype=np.bool_)

    clearance_volume = _build_patch_clearance(
        prepared_problem=prepared_problem,
        patch=patch,
    )

    status = "complete"
    stopped = False
    terminal_layer = layer_count
    terminal_frame = prepared_problem.config.horizon_frames
    for active_index in range(action_count):
        rows, columns = np.nonzero(patch.requested_states[terminal_layer, active_index])
        for row, column in zip(rows, columns, strict=True):
            if (
                deadline_monotonic is not None
                and time.perf_counter() >= deadline_monotonic
            ):
                status = "deadline"
                stopped = True
                break
            terminal_clearance = float(
                clearance_volume[
                    terminal_frame,
                    row - patch.clearance_row_start,
                    column - patch.clearance_column_start,
                ]
            )
            terminal_safe = (
                terminal_clearance
                > prepared_problem.viability_config.required_clearance
            )
            lower_viable[terminal_layer, active_index, row, column] = terminal_safe
            upper_viable[terminal_layer, active_index, row, column] = terminal_safe
            processed[terminal_layer, active_index, row, column] = True
        if stopped:
            break

    for layer in range(layer_count - 1, -1, -1):
        if stopped:
            break
        start_frame = layer * prepared_problem.config.frames_per_layer
        for active_index in range(action_count):
            rows, columns = np.nonzero(patch.requested_states[layer, active_index])
            for row, column in zip(rows, columns, strict=True):
                if (
                    deadline_monotonic is not None
                    and time.perf_counter() >= deadline_monotonic
                ):
                    status = "deadline"
                    stopped = True
                    break
                current_clearance = float(
                    clearance_volume[
                        start_frame,
                        row - patch.clearance_row_start,
                        column - patch.clearance_column_start,
                    ]
                )
                current_safe = (
                    current_clearance
                    > prepared_problem.viability_config.required_clearance
                )
                computed_lower = np.uint64(0)
                computed_upper = np.uint64(0)
                exact = np.uint64(0)
                for selected_index in range(action_count):
                    action_bit = np.uint64(1 << selected_index)
                    action_lower = current_safe
                    action_upper = current_safe
                    action_exact = True
                    for branch_index, delay in enumerate(delay_frames):
                        known, path_safe, successor_row, successor_column = (
                            _sample_branch(
                                prepared_problem=prepared_problem,
                                patch=patch,
                                clearance_volume=clearance_volume,
                                layer=layer,
                                source_row=int(row),
                                source_column=int(column),
                                active_index=active_index,
                                selected_index=selected_index,
                                delay=delay,
                            )
                        )
                        if not current_safe or (known and not path_safe):
                            branch_lower = False
                            branch_upper = False
                            branch_exact = True
                        elif not known:
                            branch_lower = False
                            branch_upper = True
                            branch_exact = False
                        else:
                            branch_lower = bool(
                                lower_viable[
                                    layer + 1,
                                    selected_index,
                                    successor_row,
                                    successor_column,
                                ]
                            )
                            branch_upper = bool(
                                upper_viable[
                                    layer + 1,
                                    selected_index,
                                    successor_row,
                                    successor_column,
                                ]
                            )
                            branch_exact = branch_lower == branch_upper
                        if branch_lower:
                            lower_branches[
                                layer,
                                active_index,
                                branch_index,
                                row,
                                column,
                            ] |= action_bit
                        if branch_upper:
                            upper_branches[
                                layer,
                                active_index,
                                branch_index,
                                row,
                                column,
                            ] |= action_bit
                        else:
                            upper_branches[
                                layer,
                                active_index,
                                branch_index,
                                row,
                                column,
                            ] &= np.bitwise_not(action_bit)
                        action_lower &= branch_lower
                        action_upper &= branch_upper
                        action_exact &= branch_exact
                    if action_lower:
                        computed_lower |= action_bit
                    if action_upper:
                        computed_upper |= action_bit
                    if action_exact:
                        exact |= action_bit
                lower_masks[layer, active_index, row, column] |= computed_lower
                upper_masks[layer, active_index, row, column] &= computed_upper
                if lower_masks[layer, active_index, row, column] & np.bitwise_not(
                    upper_masks[layer, active_index, row, column]
                ):
                    raise RuntimeError(
                        "incoming and refined bounds disagree at one fine state"
                    )
                lower_viable[layer, active_index, row, column] = (
                    lower_masks[layer, active_index, row, column] != 0
                )
                upper_viable[layer, active_index, row, column] = (
                    upper_masks[layer, active_index, row, column] != 0
                )
                exact_masks[layer, active_index, row, column] = exact
                processed[layer, active_index, row, column] = True
            if stopped:
                break
        if not stopped and layer == patch.root_layer and stop_when_root_sufficient:
            root_rows = patch.partition.member_rows(patch.root_coarse_row)
            root_columns = patch.partition.member_columns(patch.root_coarse_column)
            root_members = lower_masks[
                patch.root_layer,
                patch.root_active_index,
                root_rows[:, None],
                root_columns[None, :],
            ]
            if int(np.bitwise_and.reduce(root_members.reshape(-1))) != 0:
                status = "root_sufficient"
                stopped = True

    if status == "complete" and not np.all(processed[patch.requested_states]):
        raise RuntimeError("query-local solve ended with unfinished requested work")
    return QueryLocalDualBoundResult(
        patch=patch,
        lower_viable=lower_viable,
        upper_viable=upper_viable,
        lower_action_masks=lower_masks,
        upper_action_masks=upper_masks,
        lower_branch_action_masks=lower_branches,
        upper_branch_action_masks=upper_branches,
        exact_action_masks=exact_masks,
        processed_states=processed,
        status=status,
        elapsed_ms=(time.perf_counter() - started) * 1000.0,
    )


def solve_query_local_dual_bounds_vectorized(
    *,
    prepared_problem: PreparedCorridorProblem,
    patch: QueryLocalRefinementPatch,
    backend: str = "native",
) -> QueryLocalDualBoundResult:
    """Solve rectangular lower/upper domains through the dense kernel.

    The hazard oracle is evaluated only inside the patch clearance rectangle.
    Outside clearance is negative infinity for the lower solve and positive
    infinity for the upper solve.  This is an optimized finite-bound data
    plane, not an independent oracle; the scalar solver remains the oracle for
    branch-specific comparison.
    """

    if backend not in {"auto", "native", "numpy"}:
        raise ValueError("vectorized refinement backend is invalid")
    started = time.perf_counter()
    action_count = len(prepared_problem.robust_control.actions)
    full_mask = _full_action_mask(action_count)
    local_clearance = _build_patch_clearance(
        prepared_problem=prepared_problem,
        patch=patch,
    )
    volume_shape = (
        prepared_problem.config.horizon_frames + 1,
        patch.fine_y.size,
        patch.fine_x.size,
    )
    finite_extreme = np.finfo(np.float32).max
    lower_clearance = np.full(
        volume_shape,
        -finite_extreme,
        dtype=np.float32,
    )
    upper_clearance = np.full(
        volume_shape,
        finite_extreme,
        dtype=np.float32,
    )
    rectangle = (
        slice(None),
        slice(patch.clearance_row_start, patch.clearance_row_end),
        slice(
            patch.clearance_column_start,
            patch.clearance_column_end,
        ),
    )
    lower_clearance[rectangle] = local_clearance
    upper_clearance[rectangle] = local_clearance
    policy_arguments = {
        "x_axis": patch.fine_x,
        "y_axis": patch.fine_y,
        "actions": prepared_problem.robust_control.actions,
        "delay_frames": prepared_problem.robust_control.delay_frames,
        "nominal_delay": prepared_problem.robust_control.nominal_delay,
        "config": prepared_problem.viability_config,
        "backend": backend,
    }
    lower_policy = build_robust_viability_policy(
        clearance_volume=lower_clearance,
        **policy_arguments,
    )
    upper_policy = build_robust_viability_policy(
        clearance_volume=upper_clearance,
        **policy_arguments,
    )
    incoming_lower = lift_coarse_action_masks(
        patch.incoming_bounds.lower,
        partition=patch.partition,
    ).astype(np.uint64, copy=False)
    incoming_upper = lift_coarse_action_masks(
        patch.incoming_bounds.upper,
        partition=patch.partition,
    ).astype(np.uint64, copy=False)
    lower_masks = lower_policy.safe_action_masks.astype(np.uint64) | incoming_lower
    upper_masks = upper_policy.safe_action_masks.astype(np.uint64) & incoming_upper
    if np.any(lower_masks & np.bitwise_not(upper_masks)):
        raise RuntimeError("vectorized refinement violated incoming bounds")
    layer_count = lower_masks.shape[0]
    state_shape = (
        layer_count + 1,
        action_count,
        patch.fine_y.size,
        patch.fine_x.size,
    )
    lower_viable = np.zeros(state_shape, dtype=np.bool_)
    upper_viable = np.ones(state_shape, dtype=np.bool_)
    lower_viable[:-1] = lower_masks != 0
    upper_viable[:-1] = upper_masks != 0
    lower_viable[-1] = lower_policy.viable[-1]
    upper_viable[-1] = upper_policy.viable[-1]
    branch_shape = (
        layer_count,
        action_count,
        len(prepared_problem.robust_control.delay_frames),
        patch.fine_y.size,
        patch.fine_x.size,
    )
    lower_branches = np.zeros(branch_shape, dtype=np.uint64)
    upper_branches = np.full(
        branch_shape,
        full_mask,
        dtype=np.uint64,
    )
    exact_masks = np.bitwise_not(lower_masks ^ upper_masks) & full_mask
    processed = np.array(patch.requested_states, copy=True)
    return QueryLocalDualBoundResult(
        patch=patch,
        lower_viable=lower_viable,
        upper_viable=upper_viable,
        lower_action_masks=lower_masks,
        upper_action_masks=upper_masks,
        lower_branch_action_masks=lower_branches,
        upper_branch_action_masks=upper_branches,
        exact_action_masks=exact_masks,
        processed_states=processed,
        status="complete",
        elapsed_ms=(time.perf_counter() - started) * 1000.0,
    )


__all__ = [
    "QueryLocalDualBoundResult",
    "QueryLocalRefinementPatch",
    "build_query_local_refinement_patch",
    "solve_query_local_dual_bounds",
    "solve_query_local_dual_bounds_vectorized",
    "trivial_coarse_action_bounds",
]
