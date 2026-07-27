"""Vectorized dense-rectangle data plane for retained refinement workloads."""

from __future__ import annotations

import time

import numpy as np

from ...viability import build_robust_viability_policy
from ..prepared import PreparedCorridorProblem
from .cells import lift_coarse_action_masks
from .clearance import build_patch_clearance
from .patch import QueryLocalRefinementPatch, _full_action_mask
from .result import QueryLocalDualBoundResult


def solve_query_local_dual_bounds_vectorized(
    *,
    prepared_problem: PreparedCorridorProblem,
    patch: QueryLocalRefinementPatch,
    backend: str = "native",
) -> QueryLocalDualBoundResult:
    """Solve rectangular lower/upper domains through the dense kernel.

    The hazard oracle is evaluated only inside the patch clearance rectangle.
    Outside clearance is negative infinity for the lower solve and positive
    infinity for the upper solve. This is an optimized finite-bound data
    plane, not an independent oracle; the scalar solver remains the oracle for
    branch-specific comparison.
    """

    if backend not in {"auto", "native", "numpy"}:
        raise ValueError("vectorized refinement backend is invalid")
    started = time.perf_counter()
    action_count = len(prepared_problem.robust_control.actions)
    full_mask = _full_action_mask(action_count)
    local_clearance = build_patch_clearance(
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


__all__ = ["solve_query_local_dual_bounds_vectorized"]
