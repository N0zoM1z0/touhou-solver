"""Independent exhaustive oracles for a variable-cadence input pipeline.

These scalar implementations are deliberately unoptimized specifications for
tiny research workloads.  The belief oracle enforces non-anticipativity.  The
clairvoyant oracle is retained only to detect cases where conditioning future
actions on a hidden exact remaining delay changes the answer.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from .query_survival import PendingCommand, QueryLocalSurvivalResult
from .reachability_oracle import SurvivalLabel
from .viability import ControlAction, ViabilityConfig


@dataclass(frozen=True)
class _HiddenState:
    frame: int
    row: int
    column: int
    active: int
    pending: int
    remaining: int


@dataclass(frozen=True)
class _Transition:
    step_count: int
    bottleneck_margin: float
    failed_label: SurvivalLabel | None
    successor: _HiddenState | None


@dataclass(frozen=True)
class _OracleProblem:
    x_values: np.ndarray
    y_values: np.ndarray
    clearance: np.ndarray
    actions: tuple[ControlAction, ...]
    delay_frames: tuple[int, ...]
    cadence_frames: tuple[int, ...]
    config: ViabilityConfig

    @property
    def horizon_frame(self) -> int:
        return self.clearance.shape[0] - 1

    def margin(self, state: _HiddenState) -> float:
        return (
            float(self.clearance[state.frame, state.row, state.column])
            - self.config.required_clearance
        )

    def canonicalize(self, state: _HiddenState) -> _HiddenState:
        if state.pending < 0:
            return _HiddenState(
                state.frame,
                state.row,
                state.column,
                state.active,
                -1,
                0,
            )
        if state.pending == state.active:
            return _HiddenState(
                state.frame,
                state.row,
                state.column,
                state.active,
                -1,
                0,
            )
        return state

    def project(
        self,
        target_x: float,
        target_y: float,
    ) -> tuple[int, int, float] | None:
        x_start = float(self.x_values[0])
        x_end = float(self.x_values[-1])
        y_start = float(self.y_values[0])
        y_end = float(self.y_values[-1])
        inside = (
            x_start <= target_x <= x_end
            and y_start <= target_y <= y_end
        )
        if not inside and not self.config.clamp_to_bounds:
            return None
        target_x = min(x_end, max(x_start, target_x))
        target_y = min(y_end, max(y_start, target_y))
        x_step = float(self.x_values[1] - self.x_values[0])
        y_step = float(self.y_values[1] - self.y_values[0])
        column = min(
            len(self.x_values) - 1,
            max(0, int(round((target_x - x_start) / x_step))),
        )
        row = min(
            len(self.y_values) - 1,
            max(0, int(round((target_y - y_start) / y_step))),
        )
        return (
            row,
            column,
            math.hypot(
                target_x - float(self.x_values[column]),
                target_y - float(self.y_values[row]),
            ),
        )

    def transition(
        self,
        state: _HiddenState,
        *,
        selected: int,
        delay: int | None,
        cadence: int,
    ) -> _Transition:
        step_count = min(
            cadence,
            self.horizon_frame - state.frame,
        )
        bottleneck = self.margin(state)
        state_x = float(self.x_values[state.column])
        state_y = float(self.y_values[state.row])
        displacement_x = 0.0
        displacement_y = 0.0
        terminal: tuple[int, int, float] | None = None
        issued = delay is not None
        for physical_step in range(1, step_count + 1):
            if issued and physical_step > delay:
                motion_index = selected
            elif (
                state.pending >= 0
                and physical_step > state.remaining
            ):
                motion_index = state.pending
            else:
                motion_index = state.active
            motion = self.actions[motion_index]
            displacement_x += motion.velocity_x
            displacement_y += motion.velocity_y
            terminal = self.project(
                state_x + displacement_x,
                state_y + displacement_y,
            )
            if terminal is None:
                return _Transition(
                    step_count,
                    -math.inf,
                    SurvivalLabel(physical_step - 1, -math.inf),
                    None,
                )
            next_row, next_column, projection_error = terminal
            margin = (
                float(
                    self.clearance[
                        state.frame + physical_step,
                        next_row,
                        next_column,
                    ]
                )
                - projection_error
                - self.config.required_clearance
            )
            bottleneck = min(bottleneck, margin)
            if margin <= 0.0:
                return _Transition(
                    step_count,
                    bottleneck,
                    SurvivalLabel(physical_step - 1, bottleneck),
                    None,
                )

        assert terminal is not None
        terminal_row, terminal_column, _ = terminal
        if not issued:
            if (
                state.pending >= 0
                and state.remaining <= step_count
            ):
                successor_active = state.pending
                successor_pending = -1
                successor_remaining = 0
            else:
                successor_active = state.active
                successor_pending = state.pending
                successor_remaining = (
                    state.remaining - step_count
                    if state.pending >= 0
                    else 0
                )
        elif delay < step_count:
            successor_active = selected
            successor_pending = -1
            successor_remaining = 0
        else:
            successor_active = (
                state.pending
                if (
                    state.pending >= 0
                    and state.remaining <= step_count
                )
                else state.active
            )
            successor_pending = selected
            successor_remaining = delay - step_count
            if successor_remaining == 0:
                successor_active = selected
                successor_pending = -1
        successor = self.canonicalize(
            _HiddenState(
                state.frame + step_count,
                terminal_row,
                terminal_column,
                successor_active,
                successor_pending,
                successor_remaining,
            )
        )
        return _Transition(
            step_count,
            bottleneck,
            None,
            successor,
        )


def _prepare_problem(
    *,
    x_axis: np.ndarray,
    y_axis: np.ndarray,
    clearance_volume: np.ndarray,
    actions: tuple[ControlAction, ...],
    delay_frames: tuple[int, ...],
    decision_frame_support: tuple[int, ...],
    config: ViabilityConfig,
    start_frame: int,
    row: int,
    column: int,
    observed_action: str,
    pending_command: PendingCommand | None,
) -> tuple[_OracleProblem, int, int, tuple[int, ...]]:
    x_values = np.asarray(x_axis, dtype=np.float64)
    y_values = np.asarray(y_axis, dtype=np.float64)
    clearance = np.asarray(clearance_volume, dtype=np.float64)
    if x_values.ndim != 1 or len(x_values) < 2:
        raise ValueError("x axis must contain at least two points")
    if y_values.ndim != 1 or len(y_values) < 2:
        raise ValueError("y axis must contain at least two points")
    for name, values in (("x", x_values), ("y", y_values)):
        differences = np.diff(values)
        if (
            not np.all(differences > 0.0)
            or not np.allclose(
                differences,
                differences[0],
                rtol=0.0,
                atol=1e-6,
            )
        ):
            raise ValueError(
                f"{name} axis must be strictly increasing and uniform"
            )
    if clearance.ndim != 3 or clearance.shape != (
        clearance.shape[0],
        len(y_values),
        len(x_values),
    ):
        raise ValueError("clearance volume does not match the lattice")
    if clearance.shape[0] < 2:
        raise ValueError("clearance volume must contain multiple frames")
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
    if (
        not decision_frame_support
        or tuple(sorted(set(decision_frame_support)))
        != decision_frame_support
        or decision_frame_support[0] <= 0
    ):
        raise ValueError("decision-frame support is invalid")
    if not actions or len({action.name for action in actions}) != len(actions):
        raise ValueError("actions must be nonempty with unique names")
    action_indices = {
        action.name: action_index
        for action_index, action in enumerate(actions)
    }
    if observed_action not in action_indices:
        raise ValueError("observed action is absent from the action set")
    if (
        pending_command is not None
        and pending_command.action not in action_indices
    ):
        raise ValueError("pending action is absent from the action set")
    pending_index = (
        -1
        if pending_command is None
        else action_indices[pending_command.action]
    )
    pending_support = (
        (0,)
        if pending_command is None
        else pending_command.remaining_frames
    )
    return (
        _OracleProblem(
            x_values=x_values,
            y_values=y_values,
            clearance=clearance,
            actions=actions,
            delay_frames=delay_frames,
            cadence_frames=decision_frame_support,
            config=config,
        ),
        action_indices[observed_action],
        pending_index,
        pending_support,
    )


def _result(
    *,
    problem: _OracleProblem,
    start_frame: int,
    row: int,
    column: int,
    observed_action: str,
    pending_command: PendingCommand | None,
    action_labels: tuple[SurvivalLabel, ...],
    evaluated_states: int,
    backend: str,
) -> QueryLocalSurvivalResult:
    state_label = max(action_labels)
    return QueryLocalSurvivalResult(
        start_frame=start_frame,
        remaining_frames=problem.horizon_frame - start_frame,
        row=row,
        column=column,
        observed_action=observed_action,
        pending_command=pending_command,
        state_label=state_label,
        action_labels=tuple(
            (action.name, label)
            for action, label in zip(problem.actions, action_labels)
        ),
        best_actions=tuple(
            action.name
            for action, label in zip(problem.actions, action_labels)
            if label == state_label
        ),
        evaluated_state_count=evaluated_states,
        backend=backend,
    )


def scalar_clairvoyant_recursive_cadence_survival(
    *,
    x_axis: np.ndarray,
    y_axis: np.ndarray,
    clearance_volume: np.ndarray,
    actions: tuple[ControlAction, ...],
    delay_frames: tuple[int, ...],
    decision_frame_support: tuple[int, ...],
    config: ViabilityConfig,
    start_frame: int,
    row: int,
    column: int,
    observed_action: str,
    pending_command: PendingCommand | None = None,
) -> QueryLocalSurvivalResult:
    """Branch cadence recursively but reveal exact delay after each step."""

    problem, active_index, pending_index, pending_support = _prepare_problem(
        x_axis=x_axis,
        y_axis=y_axis,
        clearance_volume=clearance_volume,
        actions=actions,
        delay_frames=delay_frames,
        decision_frame_support=decision_frame_support,
        config=config,
        start_frame=start_frame,
        row=row,
        column=column,
        observed_action=observed_action,
        pending_command=pending_command,
    )

    @lru_cache(maxsize=None)
    def solve(
        state: _HiddenState,
    ) -> tuple[SurvivalLabel, tuple[SurvivalLabel, ...]]:
        state = problem.canonicalize(state)
        current_margin = problem.margin(state)
        if state.frame == problem.horizon_frame or current_margin <= 0.0:
            terminal = SurvivalLabel(0, current_margin)
            return terminal, tuple(terminal for _ in problem.actions)
        action_labels = []
        for selected in range(len(problem.actions)):
            branches = []
            desired = (
                state.pending if state.pending >= 0 else state.active
            )
            selected_delays: tuple[int | None, ...] = (
                (None,)
                if selected == desired
                else problem.delay_frames
            )
            for cadence in problem.cadence_frames:
                for delay in selected_delays:
                    transition = problem.transition(
                        state,
                        selected=selected,
                        delay=delay,
                        cadence=cadence,
                    )
                    if transition.failed_label is not None:
                        branches.append(transition.failed_label)
                        continue
                    assert transition.successor is not None
                    successor, _ = solve(transition.successor)
                    branches.append(
                        SurvivalLabel(
                            transition.step_count
                            + successor.guaranteed_frames,
                            min(
                                transition.bottleneck_margin,
                                successor.bottleneck_margin,
                            ),
                        )
                    )
            action_labels.append(min(branches))
        labels = tuple(action_labels)
        return max(labels), labels

    root_results = tuple(
        solve(
            _HiddenState(
                start_frame,
                row,
                column,
                active_index,
                pending_index,
                pending_remaining,
            )
        )
        for pending_remaining in pending_support
    )
    robust_action_labels = tuple(
        min(
            root_result[1][action_index]
            for root_result in root_results
        )
        for action_index in range(len(problem.actions))
    )
    return _result(
        problem=problem,
        start_frame=start_frame,
        row=row,
        column=column,
        observed_action=observed_action,
        pending_command=pending_command,
        action_labels=robust_action_labels,
        evaluated_states=solve.cache_info().currsize,
        backend="scalar_clairvoyant_recursive_cadence_pipeline",
    )


def scalar_belief_cadence_survival(
    *,
    x_axis: np.ndarray,
    y_axis: np.ndarray,
    clearance_volume: np.ndarray,
    actions: tuple[ControlAction, ...],
    delay_frames: tuple[int, ...],
    decision_frame_support: tuple[int, ...],
    config: ViabilityConfig,
    start_frame: int,
    row: int,
    column: int,
    observed_action: str,
    pending_command: PendingCommand | None = None,
    continuation_actions: tuple[str, ...] | None = None,
    recursive_cadence: bool = True,
) -> QueryLocalSurvivalResult:
    """Solve the non-clairvoyant variable-cadence information-set game.

    Every action remains available at the public root.  When
    ``continuation_actions`` is supplied, later decisions use only that
    declared policy class, producing an attainable lower bound on the
    unrestricted controller value.  Setting ``recursive_cadence`` false keeps
    the robust cadence support only at the public root and then uses the
    configured nominal layer interval.  That mode is an independent,
    no-write-correct specification of the older one-transition contract.
    """

    problem, active_index, pending_index, pending_support = _prepare_problem(
        x_axis=x_axis,
        y_axis=y_axis,
        clearance_volume=clearance_volume,
        actions=actions,
        delay_frames=delay_frames,
        decision_frame_support=decision_frame_support,
        config=config,
        start_frame=start_frame,
        row=row,
        column=column,
        observed_action=observed_action,
        pending_command=pending_command,
    )
    action_indices = {
        action.name: index
        for index, action in enumerate(problem.actions)
    }
    continuation_names = (
        tuple(action_indices)
        if continuation_actions is None
        else continuation_actions
    )
    if (
        not continuation_names
        or len(set(continuation_names)) != len(continuation_names)
        or any(name not in action_indices for name in continuation_names)
    ):
        raise ValueError(
            "continuation actions must be unique known actions"
        )
    continuation_indices = tuple(
        action_indices[name] for name in continuation_names
    )

    @lru_cache(maxsize=None)
    def solve(
        frame: int,
        state_row: int,
        state_column: int,
        active: int,
        pending: int,
        remaining_support: tuple[int, ...],
        public_root: bool,
    ) -> tuple[SurvivalLabel, tuple[SurvivalLabel, ...]]:
        representative = _HiddenState(
            frame,
            state_row,
            state_column,
            active,
            pending,
            remaining_support[0],
        )
        current_margin = problem.margin(representative)
        if frame == problem.horizon_frame or current_margin <= 0.0:
            terminal = SurvivalLabel(0, current_margin)
            return terminal, tuple(terminal for _ in problem.actions)

        action_labels: list[SurvivalLabel] = []
        selected_actions = (
            tuple(range(len(problem.actions)))
            if public_root
            else continuation_indices
        )
        for selected in selected_actions:
            failed_labels: list[SurvivalLabel] = []
            grouped: dict[
                tuple[int, int, int, int, int],
                tuple[set[int], float],
            ] = {}
            desired = pending if pending >= 0 else active
            selected_delays: tuple[int | None, ...] = (
                (None,)
                if selected == desired
                else problem.delay_frames
            )
            cadence_support = (
                problem.cadence_frames
                if public_root or recursive_cadence
                else (problem.config.frames_per_layer,)
            )
            for remaining in remaining_support:
                # Do not canonicalize one hidden branch before the
                # observation partition.  In particular, ``remaining >=
                # max(delay)`` makes that branch dynamically irrelevant but
                # does not reveal to the controller which member of the
                # current remaining-delay support nature selected.
                hidden = _HiddenState(
                    frame,
                    state_row,
                    state_column,
                    active,
                    pending,
                    remaining,
                )
                for cadence in cadence_support:
                    for delay in selected_delays:
                        transition = problem.transition(
                            hidden,
                            selected=selected,
                            delay=delay,
                            cadence=cadence,
                        )
                        if transition.failed_label is not None:
                            failed_labels.append(
                                transition.failed_label
                            )
                            continue
                        successor = transition.successor
                        assert successor is not None
                        observation = (
                            successor.frame,
                            successor.row,
                            successor.column,
                            successor.active,
                            successor.pending,
                        )
                        support, prefix_margin = grouped.get(
                            observation,
                            (set(), math.inf),
                        )
                        if successor.pending >= 0:
                            support.add(successor.remaining)
                        else:
                            support.add(0)
                        grouped[observation] = (
                            support,
                            min(
                                prefix_margin,
                                transition.bottleneck_margin,
                            ),
                        )

            branch_labels = list(failed_labels)
            for observation, (
                successor_support,
                prefix_margin,
            ) in grouped.items():
                (
                    successor_frame,
                    successor_row,
                    successor_column,
                    successor_active,
                    successor_pending,
                ) = observation
                successor, _ = solve(
                    successor_frame,
                    successor_row,
                    successor_column,
                    successor_active,
                    successor_pending,
                    tuple(sorted(successor_support)),
                    False,
                )
                branch_labels.append(
                    SurvivalLabel(
                        successor_frame - frame
                        + successor.guaranteed_frames,
                        min(
                            prefix_margin,
                            successor.bottleneck_margin,
                        ),
                    )
                )
            action_labels.append(min(branch_labels))

        labels = tuple(action_labels)
        return max(labels), labels

    _, root_action_labels = solve(
        start_frame,
        row,
        column,
        active_index,
        pending_index,
        pending_support,
        True,
    )
    return _result(
        problem=problem,
        start_frame=start_frame,
        row=row,
        column=column,
        observed_action=observed_action,
        pending_command=pending_command,
        action_labels=root_action_labels,
        evaluated_states=solve.cache_info().currsize,
        backend=(
            "scalar_belief_variable_cadence_pipeline"
            if recursive_cadence
            else "scalar_belief_one_transition_cadence_pipeline"
        ),
    )


__all__ = [
    "scalar_belief_cadence_survival",
    "scalar_clairvoyant_recursive_cadence_survival",
]
