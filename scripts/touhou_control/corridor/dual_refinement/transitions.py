"""Explicit active/selected/delay transition lattices and causal tubes."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ...viability import ControlAction, ViabilityConfig
from ..prepared import PreparedCorridorProblem
from .cells import _readonly_array, _uniform_step, _validated_axis


@dataclass(frozen=True)
class TransitionLattice:
    """One-layer terminal transition relation with explicit hidden branches."""

    x_axis: np.ndarray
    y_axis: np.ndarray
    actions: tuple[ControlAction, ...]
    delay_frames: tuple[int, ...]
    config: ViabilityConfig
    terminal_rows: np.ndarray
    terminal_columns: np.ndarray
    terminal_inside: np.ndarray

    def __post_init__(self) -> None:
        x_axis = _validated_axis(self.x_axis, "transition x")
        y_axis = _validated_axis(self.y_axis, "transition y")
        action_count = len(self.actions)
        expected_shape = (
            action_count,
            action_count,
            len(self.delay_frames),
            y_axis.size,
            x_axis.size,
        )
        rows = _readonly_array(self.terminal_rows, dtype=np.intp)
        columns = _readonly_array(self.terminal_columns, dtype=np.intp)
        inside = _readonly_array(self.terminal_inside, dtype=np.bool_)
        if (
            rows.shape != expected_shape
            or columns.shape != expected_shape
            or inside.shape != expected_shape
        ):
            raise ValueError(
                "transition arrays must have active, selected, branch, row, "
                "and column axes"
            )
        if (
            np.any(rows < 0)
            or np.any(rows >= y_axis.size)
            or np.any(columns < 0)
            or np.any(columns >= x_axis.size)
        ):
            raise ValueError("transition endpoint index is outside the lattice")
        object.__setattr__(self, "x_axis", x_axis)
        object.__setattr__(self, "y_axis", y_axis)
        object.__setattr__(self, "terminal_rows", rows)
        object.__setattr__(self, "terminal_columns", columns)
        object.__setattr__(self, "terminal_inside", inside)

    @property
    def state_shape(self) -> tuple[int, int, int]:
        return (len(self.actions), self.y_axis.size, self.x_axis.size)

    def action_index(self, name: str) -> int:
        index = next(
            (index for index, action in enumerate(self.actions) if action.name == name),
            None,
        )
        if index is None:
            raise ValueError(f"unknown transition action {name!r}")
        return index

    def delay_index(self, delay: int) -> int:
        try:
            return self.delay_frames.index(delay)
        except ValueError as error:
            raise ValueError(
                f"delay {delay} is absent from transition support"
            ) from error


def build_transition_lattice(
    *,
    x_axis: np.ndarray,
    y_axis: np.ndarray,
    actions: tuple[ControlAction, ...],
    delay_frames: tuple[int, ...],
    config: ViabilityConfig,
) -> TransitionLattice:
    """Build terminal indices independently from the viability implementation."""

    x_axis = _validated_axis(x_axis, "transition x")
    y_axis = _validated_axis(y_axis, "transition y")
    x_step = _uniform_step(x_axis, "transition x")
    y_step = _uniform_step(y_axis, "transition y")
    if not actions:
        raise ValueError("transition lattice requires at least one action")
    if len({action.name for action in actions}) != len(actions):
        raise ValueError("transition action names must be unique")
    if (
        not delay_frames
        or tuple(sorted(set(delay_frames))) != delay_frames
        or delay_frames[0] < 0
        or delay_frames[-1] > config.frames_per_layer
    ):
        raise ValueError(
            "transition delays must be sorted, unique, nonnegative, and fit "
            "one control layer"
        )

    grid_x, grid_y = np.meshgrid(x_axis, y_axis)
    action_count = len(actions)
    shape = (
        action_count,
        action_count,
        len(delay_frames),
        y_axis.size,
        x_axis.size,
    )
    rows = np.empty(shape, dtype=np.intp)
    columns = np.empty(shape, dtype=np.intp)
    inside = np.empty(shape, dtype=np.bool_)
    x_start = float(x_axis[0])
    x_end = float(x_axis[-1])
    y_start = float(y_axis[0])
    y_end = float(y_axis[-1])

    for active_index, active in enumerate(actions):
        for selected_index, selected in enumerate(actions):
            for branch_index, delay in enumerate(delay_frames):
                selected_frames = config.frames_per_layer - delay
                target_x = (
                    grid_x
                    + active.velocity_x * delay
                    + selected.velocity_x * selected_frames
                )
                target_y = (
                    grid_y
                    + active.velocity_y * delay
                    + selected.velocity_y * selected_frames
                )
                branch_inside = (
                    (target_x >= x_start)
                    & (target_x <= x_end)
                    & (target_y >= y_start)
                    & (target_y <= y_end)
                )
                if config.clamp_to_bounds:
                    target_x = np.clip(target_x, x_start, x_end)
                    target_y = np.clip(target_y, y_start, y_end)
                    branch_inside = np.ones(
                        target_x.shape,
                        dtype=np.bool_,
                    )
                columns[active_index, selected_index, branch_index] = np.clip(
                    np.rint((target_x - x_start) / x_step),
                    0,
                    x_axis.size - 1,
                ).astype(np.intp)
                rows[active_index, selected_index, branch_index] = np.clip(
                    np.rint((target_y - y_start) / y_step),
                    0,
                    y_axis.size - 1,
                ).astype(np.intp)
                inside[active_index, selected_index, branch_index] = branch_inside
    return TransitionLattice(
        x_axis=x_axis,
        y_axis=y_axis,
        actions=actions,
        delay_frames=delay_frames,
        config=config,
        terminal_rows=rows,
        terminal_columns=columns,
        terminal_inside=inside,
    )


def build_prepared_transition_lattice(
    prepared_problem: PreparedCorridorProblem,
) -> TransitionLattice:
    """Build the declared coarse transition relation of a prepared problem."""

    control = prepared_problem.robust_control
    return build_transition_lattice(
        x_axis=prepared_problem.x_axis,
        y_axis=prepared_problem.y_axis,
        actions=control.actions,
        delay_frames=control.delay_frames,
        config=prepared_problem.viability_config,
    )


def terminal_coreachable_tube(
    *,
    transitions: TransitionLattice,
    layer_count: int,
    terminal_scope: np.ndarray,
) -> np.ndarray:
    """Compute the optimistic may-predecessor closure of a terminal scope."""

    if layer_count <= 0:
        raise ValueError("tube layer count must be positive")
    terminal_scope = np.asarray(terminal_scope, dtype=np.bool_)
    if terminal_scope.shape != transitions.state_shape:
        raise ValueError("terminal scope must have active-action, row, and column axes")
    coreachable = np.zeros(
        (layer_count + 1,) + transitions.state_shape,
        dtype=np.bool_,
    )
    coreachable[layer_count] = terminal_scope
    action_count = len(transitions.actions)
    for layer in range(layer_count - 1, -1, -1):
        successor = coreachable[layer + 1]
        for active_index in range(action_count):
            may_reach = coreachable[layer, active_index]
            for selected_index in range(action_count):
                for branch_index in range(len(transitions.delay_frames)):
                    rows = transitions.terminal_rows[
                        active_index,
                        selected_index,
                        branch_index,
                    ]
                    columns = transitions.terminal_columns[
                        active_index,
                        selected_index,
                        branch_index,
                    ]
                    may_reach |= (
                        transitions.terminal_inside[
                            active_index,
                            selected_index,
                            branch_index,
                        ]
                        & successor[selected_index, rows, columns]
                    )
    coreachable.setflags(write=False)
    return coreachable


def root_branch_forward_tube(
    *,
    transitions: TransitionLattice,
    layer_count: int,
    root_active_index: int,
    root_row: int,
    root_column: int,
    root_selected_index: int,
    root_branch_index: int,
) -> np.ndarray:
    """Expand one fixed root action/branch, then all later causal choices."""

    if layer_count <= 0:
        raise ValueError("tube layer count must be positive")
    action_count, row_count, column_count = transitions.state_shape
    if not 0 <= root_active_index < action_count:
        raise ValueError("root active plane is outside the transition lattice")
    if not 0 <= root_selected_index < action_count:
        raise ValueError("root selected action is outside the transition lattice")
    if not 0 <= root_branch_index < len(transitions.delay_frames):
        raise ValueError("root hidden branch is outside delay support")
    if not 0 <= root_row < row_count or not 0 <= root_column < column_count:
        raise ValueError("root position is outside the transition lattice")

    forward = np.zeros(
        (layer_count + 1,) + transitions.state_shape,
        dtype=np.bool_,
    )
    forward[0, root_active_index, root_row, root_column] = True
    if transitions.terminal_inside[
        root_active_index,
        root_selected_index,
        root_branch_index,
        root_row,
        root_column,
    ]:
        successor_row = transitions.terminal_rows[
            root_active_index,
            root_selected_index,
            root_branch_index,
            root_row,
            root_column,
        ]
        successor_column = transitions.terminal_columns[
            root_active_index,
            root_selected_index,
            root_branch_index,
            root_row,
            root_column,
        ]
        forward[
            1,
            root_selected_index,
            successor_row,
            successor_column,
        ] = True

    for layer in range(1, layer_count):
        current = forward[layer]
        following = forward[layer + 1]
        for active_index in range(action_count):
            source_rows, source_columns = np.nonzero(current[active_index])
            for source_row, source_column in zip(
                source_rows,
                source_columns,
                strict=True,
            ):
                for selected_index in range(action_count):
                    for branch_index in range(len(transitions.delay_frames)):
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
                        following[
                            selected_index,
                            successor_row,
                            successor_column,
                        ] = True
    forward.setflags(write=False)
    return forward


def forward_reachable_tube(
    *,
    transitions: TransitionLattice,
    layer_count: int,
    initial_states: np.ndarray,
) -> np.ndarray:
    """Expand every declared causal action/branch from an initial state set."""

    if layer_count <= 0:
        raise ValueError("tube layer count must be positive")
    initial = np.asarray(initial_states, dtype=np.bool_)
    if initial.shape != transitions.state_shape:
        raise ValueError(
            "initial tube states must have active-action, row, and column axes"
        )
    forward = np.zeros(
        (layer_count + 1,) + transitions.state_shape,
        dtype=np.bool_,
    )
    forward[0] = initial
    action_count = len(transitions.actions)
    for layer in range(layer_count):
        current = forward[layer]
        following = forward[layer + 1]
        for active_index in range(action_count):
            source_rows, source_columns = np.nonzero(current[active_index])
            for source_row, source_column in zip(
                source_rows,
                source_columns,
                strict=True,
            ):
                for selected_index in range(action_count):
                    for branch_index in range(len(transitions.delay_frames)):
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
                        following[
                            selected_index,
                            successor_row,
                            successor_column,
                        ] = True
    forward.setflags(write=False)
    return forward


__all__ = [
    "TransitionLattice",
    "build_prepared_transition_lattice",
    "build_transition_lattice",
    "forward_reachable_tube",
    "root_branch_forward_tube",
    "terminal_coreachable_tube",
]
