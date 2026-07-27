"""Proposal-only state guides for sound query-local refinement.

A guide selects where the expensive lower-bound oracle should try to complete
work.  It is never a feasibility bound: omitted states keep lower zero and
upper unresolved, so a poor guide can miss a witness but cannot create one.
"""

from __future__ import annotations

import numpy as np

from ..viability import RobustViabilityPolicy
from .dual_bounds import PreparedDualBoundScope


def build_policy_candidate_guide(
    *,
    policy: RobustViabilityPolicy,
    scope: PreparedDualBoundScope,
    empty_expansion_layers: int = 1,
) -> np.ndarray:
    """Follow coarse safe masks after unrestricted empty-root expansion."""

    if empty_expansion_layers < 0:
        raise ValueError("empty expansion layer count cannot be negative")
    transitions = scope.transitions
    if (
        tuple(action.name for action in policy.actions)
        != tuple(action.name for action in transitions.actions)
        or policy.delay_frames != transitions.delay_frames
        or not np.array_equal(policy.x_axis, transitions.x_axis)
        or not np.array_equal(policy.y_axis, transitions.y_axis)
        or policy.layer_count != scope.layer_count
    ):
        raise ValueError("candidate policy does not match the dual-bound scope")

    guide = np.zeros(
        (scope.layer_count + 1,) + transitions.state_shape,
        dtype=np.bool_,
    )
    guide[
        scope.root_layer,
        scope.root_active_index,
        scope.root_row,
        scope.root_column,
    ] = True
    action_count = len(policy.actions)
    for layer in range(scope.root_layer, scope.layer_count):
        for active_index in range(action_count):
            source_rows, source_columns = np.nonzero(guide[layer, active_index])
            for source_row, source_column in zip(
                source_rows,
                source_columns,
                strict=True,
            ):
                action_mask = int(
                    policy.safe_action_masks[
                        layer,
                        active_index,
                        source_row,
                        source_column,
                    ]
                )
                if action_mask:
                    selected_indices = tuple(
                        index
                        for index in range(action_count)
                        if action_mask & (1 << index)
                    )
                elif layer - scope.root_layer < empty_expansion_layers:
                    selected_indices = tuple(range(action_count))
                else:
                    continue
                for selected_index in selected_indices:
                    for branch_index in range(len(policy.delay_frames)):
                        if not transitions.terminal_inside[
                            active_index,
                            selected_index,
                            branch_index,
                            source_row,
                            source_column,
                        ]:
                            continue
                        successor_row = transitions.terminal_rows[
                            active_index,
                            selected_index,
                            branch_index,
                            source_row,
                            source_column,
                        ]
                        successor_column = transitions.terminal_columns[
                            active_index,
                            selected_index,
                            branch_index,
                            source_row,
                            source_column,
                        ]
                        guide[
                            layer + 1,
                            selected_index,
                            successor_row,
                            successor_column,
                        ] = True
    guide.setflags(write=False)
    return guide


__all__ = ["build_policy_candidate_guide"]
