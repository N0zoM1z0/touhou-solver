"""Independent scalar oracle retained for legacy survival-query audits."""

from __future__ import annotations

import math
from functools import lru_cache

import numpy as np

from .query_survival_lattice import (
    normalize_decision_frame_support,
    uniform_axis,
)
from .query_survival_types import PendingCommand, QueryLocalSurvivalResult
from .reachability_oracle import SurvivalLabel
from .viability import ControlAction, ViabilityConfig


def scalar_query_local_survival(
    *,
    x_axis: np.ndarray,
    y_axis: np.ndarray,
    clearance_volume: np.ndarray,
    actions: tuple[ControlAction, ...],
    delay_frames: tuple[int, ...],
    config: ViabilityConfig,
    start_frame: int,
    row: int,
    column: int,
    observed_action: str,
    pending_command: PendingCommand | None = None,
    decision_frame_support: tuple[int, ...] | None = None,
) -> QueryLocalSurvivalResult:
    """Solve the retained legacy always-issue hybrid recurrence.

    This historical oracle treats every selected action as a newly issued
    command, even when it equals the controller's already-held desired input.
    The live actuator emits no transition in that case, so this recurrence is
    not a physical input-pipeline specification and has no general upper- or
    lower-bound direction.  It also branches cadence only at the public root
    and reveals exact remaining delay to continuation maximization.  Retain it
    for regression/audit of old workspaces only; use the belief oracle for new
    correctness claims.
    """

    x_values, x_step = uniform_axis(x_axis, "x")
    y_values, y_step = uniform_axis(y_axis, "y")
    clearance = np.asarray(clearance_volume, dtype=np.float64)
    if clearance.ndim != 3 or clearance.shape[1:] != (
        len(y_values),
        len(x_values),
    ):
        raise ValueError("clearance volume does not match the lattice")
    horizon_frame = clearance.shape[0] - 1
    if not 0 <= start_frame <= horizon_frame:
        raise ValueError("start frame is outside the clearance horizon")
    if not 0 <= row < len(y_values) or not 0 <= column < len(x_values):
        raise ValueError("query cell is outside the lattice")
    if (
        not delay_frames
        or tuple(sorted(set(delay_frames))) != delay_frames
        or delay_frames[0] < 0
    ):
        raise ValueError("delay support is invalid")
    if not actions or len({action.name for action in actions}) != len(actions):
        raise ValueError("actions must be nonempty with unique names")
    action_indices = {
        action.name: index for index, action in enumerate(actions)
    }
    if observed_action not in action_indices:
        raise ValueError("observed action is absent from the action set")
    if (
        pending_command is not None
        and pending_command.action not in action_indices
    ):
        raise ValueError("pending action is absent from the action set")

    x_start = float(x_values[0])
    x_end = float(x_values[-1])
    y_start = float(y_values[0])
    y_end = float(y_values[-1])
    cadence_support = normalize_decision_frame_support(
        decision_frame_support,
        default=config.frames_per_layer,
    )

    def sample_cell(
        target_x: float,
        target_y: float,
    ) -> tuple[int, int, float] | None:
        inside = (
            x_start <= target_x <= x_end
            and y_start <= target_y <= y_end
        )
        if not inside and not config.clamp_to_bounds:
            return None
        target_x = min(x_end, max(x_start, target_x))
        target_y = min(y_end, max(y_start, target_y))
        target_column = min(
            len(x_values) - 1,
            max(0, int(round((target_x - x_start) / x_step))),
        )
        target_row = min(
            len(y_values) - 1,
            max(0, int(round((target_y - y_start) / y_step))),
        )
        error = math.hypot(
            target_x - float(x_values[target_column]),
            target_y - float(y_values[target_row]),
        )
        return target_row, target_column, error

    @lru_cache(maxsize=None)
    def solve_state(
        frame: int,
        active_index: int,
        pending_index: int,
        pending_remaining: int,
        state_row: int,
        state_column: int,
        root_transition: bool,
    ) -> tuple[SurvivalLabel, tuple[SurvivalLabel, ...]]:
        current_margin = (
            float(clearance[frame, state_row, state_column])
            - config.required_clearance
        )
        if frame == horizon_frame or current_margin <= 0.0:
            label = SurvivalLabel(0, current_margin)
            return label, tuple(label for _ in actions)

        state_x = float(x_values[state_column])
        state_y = float(y_values[state_row])
        active = actions[active_index]
        older_pending = (
            actions[pending_index] if pending_index >= 0 else None
        )
        selected_labels: list[SurvivalLabel] = []
        for selected_index, selected in enumerate(actions):
            branch_labels: list[SurvivalLabel] = []
            transition_support = (
                cadence_support
                if root_transition
                else (config.frames_per_layer,)
            )
            for decision_frames in transition_support:
                step_count = min(
                    decision_frames,
                    horizon_frame - frame,
                )
                for delay in delay_frames:
                    bottleneck = current_margin
                    terminal: tuple[int, int, float] | None = None
                    failed: SurvivalLabel | None = None
                    displacement_x = 0.0
                    displacement_y = 0.0
                    for physical_step in range(1, step_count + 1):
                        if physical_step > delay:
                            motion = selected
                        elif (
                            older_pending is not None
                            and physical_step > pending_remaining
                        ):
                            motion = older_pending
                        else:
                            motion = active
                        displacement_x += motion.velocity_x
                        displacement_y += motion.velocity_y
                        terminal = sample_cell(
                            state_x + displacement_x,
                            state_y + displacement_y,
                        )
                        if terminal is None:
                            failed = SurvivalLabel(
                                physical_step - 1,
                                -math.inf,
                            )
                            break
                        next_row, next_column, sample_error = terminal
                        margin = (
                            float(
                                clearance[
                                    frame + physical_step,
                                    next_row,
                                    next_column,
                                ]
                            )
                            - sample_error
                            - config.required_clearance
                        )
                        bottleneck = min(bottleneck, margin)
                        if margin <= 0.0:
                            failed = SurvivalLabel(
                                physical_step - 1,
                                bottleneck,
                            )
                            break
                    if failed is not None:
                        branch_labels.append(failed)
                        continue
                    assert terminal is not None
                    terminal_row, terminal_column, _ = terminal
                    if delay < step_count:
                        successor_active = selected_index
                        successor_pending = -1
                        successor_remaining = 0
                    else:
                        if (
                            older_pending is not None
                            and pending_remaining <= step_count
                        ):
                            successor_active = pending_index
                        else:
                            successor_active = active_index
                        successor_pending = selected_index
                        successor_remaining = delay - step_count
                        if successor_remaining == 0:
                            successor_active = selected_index
                            successor_pending = -1
                    successor, _ = solve_state(
                        frame + step_count,
                        successor_active,
                        successor_pending,
                        successor_remaining,
                        terminal_row,
                        terminal_column,
                        False,
                    )
                    branch_labels.append(
                        SurvivalLabel(
                            step_count + successor.guaranteed_frames,
                            min(
                                bottleneck,
                                successor.bottleneck_margin,
                            ),
                        )
                    )
            selected_labels.append(min(branch_labels))
        action_labels = tuple(selected_labels)
        return max(action_labels), action_labels

    active_index = action_indices[observed_action]
    if pending_command is None:
        root_states = ((-1, 0),)
    else:
        root_states = tuple(
            (
                action_indices[pending_command.action],
                remaining,
            )
            for remaining in pending_command.remaining_frames
        )
    root_results = tuple(
        solve_state(
            start_frame,
            active_index,
            pending_index,
            pending_remaining,
            row,
            column,
            True,
        )
        for pending_index, pending_remaining in root_states
    )
    robust_action_labels = tuple(
        min(result[1][action_index] for result in root_results)
        for action_index in range(len(actions))
    )
    state_label = max(robust_action_labels)
    best_actions = tuple(
        action.name
        for action, label in zip(actions, robust_action_labels)
        if label == state_label
    )
    return QueryLocalSurvivalResult(
        start_frame=start_frame,
        remaining_frames=horizon_frame - start_frame,
        row=row,
        column=column,
        observed_action=observed_action,
        pending_command=pending_command,
        state_label=state_label,
        action_labels=tuple(
            (action.name, label)
            for action, label in zip(actions, robust_action_labels)
        ),
        best_actions=best_actions,
        evaluated_state_count=solve_state.cache_info().currsize,
    )



__all__ = ["scalar_query_local_survival"]
