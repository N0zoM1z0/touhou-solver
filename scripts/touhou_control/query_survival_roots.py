"""Exact kinematic root-frontier enumeration for pipeline planning."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .query_survival_lattice import (
    normalize_decision_frame_support,
    uniform_axis,
)
from .query_survival_types import PendingCommand, ReachablePipelineRoot
from .viability import ControlAction, ViabilityConfig


@dataclass(frozen=True)
class _RootEnumerationContext:
    x_values: np.ndarray
    y_values: np.ndarray
    x_step: float
    y_step: float
    cadence_support: tuple[int, ...]
    action_by_name: dict[str, ControlAction]



def _prepare_root_enumeration_context(
    *,
    x_axis: np.ndarray,
    y_axis: np.ndarray,
    actions: tuple[ControlAction, ...],
    delay_frames: tuple[int, ...],
    decision_frame_support: tuple[int, ...],
    config: ViabilityConfig,
) -> _RootEnumerationContext:
    x_values, x_step = uniform_axis(x_axis, "x")
    y_values, y_step = uniform_axis(y_axis, "y")
    cadence_support = normalize_decision_frame_support(
        decision_frame_support,
        default=config.frames_per_layer,
    )
    if (
        not delay_frames
        or tuple(sorted(set(delay_frames))) != delay_frames
        or delay_frames[0] < 0
    ):
        raise ValueError("delay support is invalid")
    action_by_name = {action.name: action for action in actions}
    if len(action_by_name) != len(actions) or not actions:
        raise ValueError("actions must be nonempty with unique names")
    return _RootEnumerationContext(
        x_values=x_values,
        y_values=y_values,
        x_step=x_step,
        y_step=y_step,
        cadence_support=cadence_support,
        action_by_name=action_by_name,
    )



def enumerate_next_decision_roots(
    *,
    x_axis: np.ndarray,
    y_axis: np.ndarray,
    actions: tuple[ControlAction, ...],
    delay_frames: tuple[int, ...],
    decision_frame_support: tuple[int, ...],
    config: ViabilityConfig,
    start_frame: int,
    horizon_frame: int,
    row: int,
    column: int,
    observed_action: str,
    selected_action: str,
    pending_command: PendingCommand | None = None,
    physical_start_x: float | None = None,
    physical_start_y: float | None = None,
    command_issue_offset: int = 0,
    _context: _RootEnumerationContext | None = None,
) -> tuple[ReachablePipelineRoot, ...]:
    """Enumerate the exact-root frontier after issuing one selected action.

    This is kinematic reachability only.  It intentionally does not certify
    collision safety; a consumer must still use a fresh local certificate.
    Branches that produce the same exact root are grouped by the remaining
    delay support of their pending command.

    The optional physical anchor and issue offset are scheduling evidence,
    not a change to the lattice value recurrence.  They let a controller
    predict the next projected root from the observed subcell position when
    several game frames elapse between reading state and issuing the newly
    selected command.  Solver/oracle callers omit them and retain the public
    root's exact lattice-center, immediate-issue semantics.
    """

    context = (
        _prepare_root_enumeration_context(
            x_axis=x_axis,
            y_axis=y_axis,
            actions=actions,
            delay_frames=delay_frames,
            decision_frame_support=decision_frame_support,
            config=config,
        )
        if _context is None
        else _context
    )
    x_values = context.x_values
    y_values = context.y_values
    x_step = context.x_step
    y_step = context.y_step
    cadence_support = context.cadence_support
    action_by_name = context.action_by_name
    if not 0 <= start_frame <= horizon_frame:
        raise ValueError("start frame is outside the requested horizon")
    if not 0 <= row < len(y_values) or not 0 <= column < len(x_values):
        raise ValueError("query cell is outside the lattice")
    action_by_name = {action.name: action for action in actions}
    if len(action_by_name) != len(actions) or not actions:
        raise ValueError("actions must be nonempty with unique names")
    if observed_action not in action_by_name:
        raise ValueError("observed action is absent from the action set")
    if selected_action not in action_by_name:
        raise ValueError("selected action is absent from the action set")
    if (
        pending_command is not None
        and pending_command.action not in action_by_name
    ):
        raise ValueError("pending action is absent from the action set")
    if (physical_start_x is None) != (physical_start_y is None):
        raise ValueError(
            "physical root prediction requires both x and y"
        )
    if command_issue_offset < 0:
        raise ValueError("command issue offset cannot be negative")

    x_start = float(x_values[0])
    x_end = float(x_values[-1])
    y_start = float(y_values[0])
    y_end = float(y_values[-1])
    state_x = (
        float(x_values[column])
        if physical_start_x is None
        else min(x_end, max(x_start, float(physical_start_x)))
    )
    state_y = (
        float(y_values[row])
        if physical_start_y is None
        else min(y_end, max(y_start, float(physical_start_y)))
    )
    active = action_by_name[observed_action]
    selected = action_by_name[selected_action]
    older_pending = (
        action_by_name[pending_command.action]
        if pending_command is not None
        else None
    )
    older_remaining_support = (
        pending_command.remaining_frames
        if pending_command is not None
        else (0,)
    )

    grouped: dict[
        tuple[int, int, int, str, str | None],
        set[int],
    ] = {}
    for older_remaining in older_remaining_support:
        for decision_frames in cadence_support:
            step_count = min(
                decision_frames,
                horizon_frame - start_frame,
            )
            if step_count <= command_issue_offset:
                continue
            for delay in delay_frames:
                displacement_x = 0.0
                displacement_y = 0.0
                terminal_row = row
                terminal_column = column
                reachable = True
                for physical_step in range(1, step_count + 1):
                    selected_elapsed = (
                        physical_step - command_issue_offset
                    )
                    if selected_elapsed > delay:
                        motion = selected
                    elif (
                        older_pending is not None
                        and physical_step > older_remaining
                    ):
                        motion = older_pending
                    else:
                        motion = active
                    displacement_x += motion.velocity_x
                    displacement_y += motion.velocity_y
                    target_x = state_x + displacement_x
                    target_y = state_y + displacement_y
                    inside = (
                        x_start <= target_x <= x_end
                        and y_start <= target_y <= y_end
                    )
                    if not inside and not config.clamp_to_bounds:
                        reachable = False
                        break
                if not reachable:
                    continue
                target_x = min(
                    x_end,
                    max(x_start, state_x + displacement_x),
                )
                target_y = min(
                    y_end,
                    max(y_start, state_y + displacement_y),
                )
                terminal_column = min(
                    len(x_values) - 1,
                    max(
                        0,
                        int(round((target_x - x_start) / x_step)),
                    ),
                )
                terminal_row = min(
                    len(y_values) - 1,
                    max(
                        0,
                        int(round((target_y - y_start) / y_step)),
                    ),
                )

                elapsed_after_issue = max(
                    step_count - command_issue_offset,
                    0,
                )
                if delay <= elapsed_after_issue:
                    successor_active = selected_action
                    successor_pending: str | None = None
                    successor_remaining = 0
                else:
                    if (
                        older_pending is not None
                        and older_remaining <= step_count
                    ):
                        successor_active = older_pending.name
                    else:
                        successor_active = observed_action
                    successor_pending = selected_action
                    successor_remaining = delay - elapsed_after_issue
                    if (
                        successor_pending == successor_active
                        or (
                            action_by_name[successor_pending].velocity_x
                            == action_by_name[successor_active].velocity_x
                            and action_by_name[successor_pending].velocity_y
                            == action_by_name[successor_active].velocity_y
                        )
                        or successor_remaining >= delay_frames[-1]
                    ):
                        successor_pending = None
                        successor_remaining = 0

                key = (
                    start_frame + step_count,
                    terminal_row,
                    terminal_column,
                    successor_active,
                    successor_pending,
                )
                grouped.setdefault(key, set())
                if successor_pending is not None:
                    grouped[key].add(successor_remaining)

    roots = []
    for (
        root_frame,
        root_row,
        root_column,
        root_active,
        root_pending,
    ), remaining in grouped.items():
        roots.append(
            ReachablePipelineRoot(
                frame=root_frame,
                row=root_row,
                column=root_column,
                observed_action=root_active,
                pending_command=(
                    PendingCommand(
                        root_pending,
                        tuple(sorted(remaining)),
                    )
                    if root_pending is not None
                    else None
                ),
            )
        )
    return tuple(
        sorted(
            roots,
            key=lambda root: (
                root.frame,
                root.row,
                root.column,
                root.observed_action,
                (
                    ""
                    if root.pending_command is None
                    else root.pending_command.action
                ),
                (
                    ()
                    if root.pending_command is None
                    else root.pending_command.remaining_frames
                ),
            ),
        )
    )



__all__ = ["enumerate_next_decision_roots"]
