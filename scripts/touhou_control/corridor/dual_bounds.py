"""Sound spatial action-mask bounds and root-relevant transition tubes.

This module is deliberately separate from the legacy full-field refinement
path.  It provides the small, independently testable contracts needed by the
query-local dual-bound solver:

* a coarse cell is the set of fine lattice states that project to the same
  coarse lattice point under the viability kernel's round-to-even rule;
* the cell lower mask is the intersection of the fine masks;
* the cell upper mask is their union;
* leading axes, including time, active-input plane, and hidden branch, are
  never collapsed by the spatial aggregation; and
* root relevance is the intersection of a branch-exact forward kinematic tube
  and an optimistic terminal co-reachable tube.

The bounds are finite-reference statements.  They do not upgrade hazard-model
coverage or make an offline result live-authoritative.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from ..viability import ControlAction, ViabilityConfig
from .prepared import PreparedCorridorProblem


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
    "ActionMaskBounds",
    "PreparedDualBoundScope",
    "ReferenceInclusionReport",
    "ReferenceInclusionViolation",
    "RootBranchTube",
    "SpatialCellPartition",
    "TransitionLattice",
    "aggregate_fine_action_mask_bounds",
    "build_prepared_transition_lattice",
    "build_spatial_cell_partition",
    "build_transition_lattice",
    "check_fine_reference_inclusion",
    "forward_reachable_tube",
    "lift_coarse_action_masks",
    "prepare_dual_bound_scope",
    "root_branch_forward_tube",
    "terminal_coreachable_tube",
]
