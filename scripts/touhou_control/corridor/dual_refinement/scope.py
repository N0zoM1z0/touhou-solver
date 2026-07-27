"""Exact-root query scope and branch-preserving relevance construction."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from ..prepared import PreparedCorridorProblem
from .cells import _readonly_array
from .transitions import (
    TransitionLattice,
    build_prepared_transition_lattice,
    root_branch_forward_tube,
    terminal_coreachable_tube,
)


@dataclass(frozen=True)
class RootBranchTube:
    root_action: str
    hidden_delay: int
    forward: np.ndarray
    terminal_coreachable: np.ndarray
    relevant: np.ndarray

    def __post_init__(self) -> None:
        forward = _readonly_array(self.forward, dtype=np.bool_)
        coreachable = _readonly_array(
            self.terminal_coreachable,
            dtype=np.bool_,
        )
        relevant = _readonly_array(self.relevant, dtype=np.bool_)
        if forward.shape != coreachable.shape or relevant.shape != forward.shape:
            raise ValueError("root tube arrays must share one state shape")
        if not np.array_equal(relevant, forward & coreachable):
            raise ValueError("relevant tube must equal forward intersect co-reachable")
        object.__setattr__(self, "forward", forward)
        object.__setattr__(self, "terminal_coreachable", coreachable)
        object.__setattr__(self, "relevant", relevant)


@dataclass(frozen=True)
class PreparedDualBoundScope:
    """Prepared-problem transition and relevance contract for one exact root."""

    transitions: TransitionLattice
    layer_count: int
    root_layer: int
    root_active_index: int
    root_row: int
    root_column: int
    root_position_error: float
    root_x: float
    root_y: float
    terminal_coreachable: np.ndarray

    def branch_tube(
        self,
        *,
        root_action: str,
        hidden_delay: int,
    ) -> RootBranchTube:
        selected_index = self.transitions.action_index(root_action)
        branch_index = self.transitions.delay_index(hidden_delay)
        local_forward = root_branch_forward_tube(
            transitions=self.transitions,
            layer_count=self.layer_count - self.root_layer,
            root_active_index=self.root_active_index,
            root_row=self.root_row,
            root_column=self.root_column,
            root_selected_index=selected_index,
            root_branch_index=branch_index,
        )
        forward = np.zeros_like(self.terminal_coreachable)
        forward[self.root_layer :] = local_forward
        relevant = forward & self.terminal_coreachable
        return RootBranchTube(
            root_action=root_action,
            hidden_delay=hidden_delay,
            forward=forward,
            terminal_coreachable=self.terminal_coreachable,
            relevant=relevant,
        )


def prepare_dual_bound_scope(
    *,
    prepared_problem: PreparedCorridorProblem,
    start_x: float,
    start_y: float,
    root_frame: int = 0,
    root_active_action: str | None = None,
) -> PreparedDualBoundScope:
    """Prepare branch-preserving G2 tube data without solving or publishing."""

    x_axis = prepared_problem.x_axis
    y_axis = prepared_problem.y_axis
    if not (
        float(x_axis[0]) <= start_x <= float(x_axis[-1])
        and float(y_axis[0]) <= start_y <= float(y_axis[-1])
    ):
        raise ValueError("dual-bound root is outside prepared problem bounds")
    x_step = float(x_axis[1] - x_axis[0])
    y_step = float(y_axis[1] - y_axis[0])
    root_column = int(np.rint((start_x - float(x_axis[0])) / x_step))
    root_row = int(np.rint((start_y - float(y_axis[0])) / y_step))
    root_column = min(x_axis.size - 1, max(0, root_column))
    root_row = min(y_axis.size - 1, max(0, root_row))
    root_position_error = math.hypot(
        start_x - float(x_axis[root_column]),
        start_y - float(y_axis[root_row]),
    )

    transitions = build_prepared_transition_lattice(prepared_problem)
    control = prepared_problem.robust_control
    root_active_index = transitions.action_index(
        control.active_action if root_active_action is None else root_active_action
    )
    terminal_scope = (
        np.asarray(control.terminal_viable, dtype=np.bool_)
        if control.terminal_viable is not None
        else np.ones(transitions.state_shape, dtype=np.bool_)
    )
    layer_count = (
        prepared_problem.config.horizon_frames
        // prepared_problem.config.frames_per_layer
    )
    if root_frame < 0:
        raise ValueError("dual-bound root frame cannot be negative")
    root_layer = root_frame // prepared_problem.config.frames_per_layer
    if root_layer >= layer_count:
        raise ValueError("dual-bound root is outside the prepared horizon")
    coreachable = terminal_coreachable_tube(
        transitions=transitions,
        layer_count=layer_count,
        terminal_scope=terminal_scope,
    )
    return PreparedDualBoundScope(
        transitions=transitions,
        layer_count=layer_count,
        root_layer=root_layer,
        root_active_index=root_active_index,
        root_row=root_row,
        root_column=root_column,
        root_position_error=root_position_error,
        root_x=start_x,
        root_y=start_y,
        terminal_coreachable=coreachable,
    )


__all__ = [
    "PreparedDualBoundScope",
    "RootBranchTube",
    "prepare_dual_bound_scope",
]
