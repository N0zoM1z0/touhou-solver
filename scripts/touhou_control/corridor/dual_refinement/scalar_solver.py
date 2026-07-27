"""Independent scalar lower/upper recurrence for query-local refinement."""

from __future__ import annotations

import math
import time

import numpy as np

from ..prepared import PreparedCorridorProblem
from .cells import lift_coarse_action_masks
from .clearance import build_patch_clearance
from .patch import (
    QueryLocalRefinementPatch,
    _full_action_mask,
)
from .result import QueryLocalDualBoundResult


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

    clearance_volume = build_patch_clearance(
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


__all__ = ["solve_query_local_dual_bounds"]
