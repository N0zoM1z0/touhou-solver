"""Phase-exact query-local robust survival with an explicit input pipeline.

The dense Boolean policy is still the authoritative global certificate.  This
module answers a narrower question only after that policy has been published:
for one current lattice state, which first actions maximize guaranteed modeled
survival?

Unlike the layer-indexed policy query, the recurrence starts at the exact
physical frame and distinguishes:

* the action observed by the game;
* an older desired action that is still pending;
* the remaining frames before that pending action may become visible; and
* the new selected action, its robust delay support, and an optional
  next-decision cadence support at the public root.

The scalar implementation is the independent oracle.  A memoized native
implementation shares the contract, but its worst-case service time does not
yet make it a live backend.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache
from typing import Hashable

import numpy as np

from . import native_backend
from .reachability_oracle import SurvivalLabel
from .viability import (
    ControlAction,
    RobustViabilityPolicy,
    ViabilityConfig,
    build_robust_viability_policy,
)


@dataclass(frozen=True)
class PendingCommand:
    """One desired action not yet observed by the controlled process."""

    action: str
    remaining_frames: tuple[int, ...]

    def __post_init__(self) -> None:
        if not self.action:
            raise ValueError("pending action cannot be empty")
        if (
            not self.remaining_frames
            or tuple(sorted(set(self.remaining_frames)))
            != self.remaining_frames
            or self.remaining_frames[0] <= 0
        ):
            raise ValueError(
                "pending remaining frames must be sorted unique and positive"
            )


@dataclass(frozen=True)
class ReachablePipelineRoot:
    """One deduplicated exact root at a possible next decision epoch."""

    frame: int
    row: int
    column: int
    observed_action: str
    pending_command: PendingCommand | None


@dataclass(frozen=True)
class PipelineSurvivalQueryStats:
    """Per-query work performed by a persistent augmented-state workspace."""

    memoized_state_count: int
    new_state_count: int
    memo_hit_count: int
    action_upper_bound_prune_count: int
    delay_incumbent_prune_count: int
    canonicalization_count: int
    root_memo_hit_count: int
    branch_simulation_count: int


@dataclass(frozen=True)
class QueryLocalSurvivalResult:
    """Lexicographic survival labels for one exact physical-frame state."""

    start_frame: int
    remaining_frames: int
    row: int
    column: int
    observed_action: str
    pending_command: PendingCommand | None
    state_label: SurvivalLabel
    action_labels: tuple[tuple[str, SurvivalLabel], ...]
    best_actions: tuple[str, ...]
    evaluated_state_count: int
    backend: str = "scalar_pending_pipeline"
    workspace_stats: PipelineSurvivalQueryStats | None = None

    @property
    def winning(self) -> bool:
        return (
            self.state_label.guaranteed_frames == self.remaining_frames
            and self.state_label.bottleneck_margin > 0.0
        )

    def action_label(self, action: str) -> SurvivalLabel:
        for name, label in self.action_labels:
            if name == action:
                return label
        raise KeyError(action)


@dataclass(frozen=True)
class SurvivalQueryProblem:
    """Immutable numeric problem retained after Boolean publication."""

    x_axis: np.ndarray
    y_axis: np.ndarray
    clearance_volume: np.ndarray
    actions: tuple[ControlAction, ...]
    delay_frames: tuple[int, ...]
    nominal_delay: int
    config: ViabilityConfig

    def __post_init__(self) -> None:
        x_axis = np.ascontiguousarray(self.x_axis, dtype=np.float32)
        y_axis = np.ascontiguousarray(self.y_axis, dtype=np.float32)
        clearance = np.ascontiguousarray(
            self.clearance_volume,
            dtype=np.float32,
        )
        if clearance.shape != (clearance.shape[0], len(y_axis), len(x_axis)):
            raise ValueError("survival problem clearance shape is invalid")
        if clearance.shape[0] < 2:
            raise ValueError("survival problem needs a future frame")
        x_axis.setflags(write=False)
        y_axis.setflags(write=False)
        clearance.setflags(write=False)
        object.__setattr__(self, "x_axis", x_axis)
        object.__setattr__(self, "y_axis", y_axis)
        object.__setattr__(self, "clearance_volume", clearance)

    @property
    def horizon_frames(self) -> int:
        return self.clearance_volume.shape[0] - 1

    def project_to_lattice(
        self,
        *,
        x: float,
        y: float,
    ) -> tuple[int, int, float]:
        x_start = float(self.x_axis[0])
        y_start = float(self.y_axis[0])
        x_step = float(self.x_axis[1] - self.x_axis[0])
        y_step = float(self.y_axis[1] - self.y_axis[0])
        column = min(
            len(self.x_axis) - 1,
            max(0, int(np.rint((x - x_start) / x_step))),
        )
        row = min(
            len(self.y_axis) - 1,
            max(0, int(np.rint((y - y_start) / y_step))),
        )
        return (
            row,
            column,
            math.hypot(
                x - float(self.x_axis[column]),
                y - float(self.y_axis[row]),
            ),
        )

    def query(
        self,
        *,
        frame: int,
        x: float,
        y: float,
        observed_action: str,
        pending_command: PendingCommand | None = None,
        backend: str = "auto",
    ) -> QueryLocalSurvivalResult:
        row, column, _ = self.project_to_lattice(x=x, y=y)
        return query_local_survival(
            x_axis=self.x_axis,
            y_axis=self.y_axis,
            clearance_volume=self.clearance_volume,
            actions=self.actions,
            delay_frames=self.delay_frames,
            config=self.config,
            start_frame=frame,
            row=row,
            column=column,
            observed_action=observed_action,
            pending_command=pending_command,
            backend=backend,
        )

    def build_full_policy(self) -> RobustViabilityPolicy:
        """Build dense fused labels after the Boolean result is publishable."""

        return build_robust_viability_policy(
            x_axis=self.x_axis,
            y_axis=self.y_axis,
            clearance_volume=self.clearance_volume,
            actions=self.actions,
            delay_frames=self.delay_frames,
            nominal_delay=self.nominal_delay,
            config=self.config,
            survival_labels=True,
        )

    def build_postpublished_policy(
        self,
        boolean_policy: RobustViabilityPolicy,
        *,
        worker_count: int = 1,
    ) -> RobustViabilityPolicy:
        """Reuse Boolean arrays and label only states already known losing."""

        arrays = native_backend.build_losing_survival_label_arrays(
            x_axis=self.x_axis,
            y_axis=self.y_axis,
            clearance_volume=self.clearance_volume,
            velocity_x=np.asarray(
                [action.velocity_x for action in self.actions],
                dtype=np.float64,
            ),
            velocity_y=np.asarray(
                [action.velocity_y for action in self.actions],
                dtype=np.float64,
            ),
            delay_frames=np.asarray(self.delay_frames, dtype=np.int32),
            frames_per_layer=self.config.frames_per_layer,
            required_clearance=self.config.required_clearance,
            clamp_to_bounds=self.config.clamp_to_bounds,
            viable=boolean_policy.viable,
            safe_action_masks=boolean_policy.safe_action_masks,
            worker_count=worker_count,
        )
        if arrays is None:
            return self.build_full_policy()
        frames, margins, masks = arrays
        return RobustViabilityPolicy(
            x_axis=self.x_axis,
            y_axis=self.y_axis,
            actions=self.actions,
            delay_frames=self.delay_frames,
            nominal_delay=self.nominal_delay,
            config=self.config,
            viable=boolean_policy.viable,
            safe_action_masks=boolean_policy.safe_action_masks,
            backend="native_postpublished_losing_survival",
            survival_frames=frames,
            survival_bottleneck_margins=margins,
            survival_best_action_masks=masks,
        )

    def build_pipeline_workspace(
        self,
        *,
        policy_version: Hashable,
        decision_frame_support: tuple[int, ...] | None = None,
    ) -> PipelineSurvivalWorkspace:
        """Create one persistent exact-root workspace for this policy."""

        return PipelineSurvivalWorkspace(
            problem=self,
            policy_version=policy_version,
            decision_frame_support=decision_frame_support,
        )


class StalePipelineWorkspaceError(RuntimeError):
    """A query attempted to use a workspace from another policy version."""


class PipelineSurvivalWorkspace:
    """Versioned memo with a robust public-root cadence transition.

    A public query branches over ``decision_frame_support`` once.  Continuation
    states retain the planner's configured fixed interval.  This bounded
    contract is deliberate: recursively branching cadence at every future
    decision is a different, much larger robust-control problem.
    """

    def __init__(
        self,
        *,
        problem: SurvivalQueryProblem,
        policy_version: Hashable,
        decision_frame_support: tuple[int, ...] | None = None,
    ) -> None:
        self.problem = problem
        self.policy_version = policy_version
        self.decision_frame_support = _normalize_decision_frame_support(
            decision_frame_support,
            default=problem.config.frames_per_layer,
        )
        self._action_indices = {
            action.name: index
            for index, action in enumerate(problem.actions)
        }
        self._native = native_backend.create_pipeline_survival_workspace(
            x_axis=problem.x_axis,
            y_axis=problem.y_axis,
            clearance_volume=problem.clearance_volume,
            velocity_x=np.asarray(
                [action.velocity_x for action in problem.actions],
                dtype=np.float64,
            ),
            velocity_y=np.asarray(
                [action.velocity_y for action in problem.actions],
                dtype=np.float64,
            ),
            delay_frames=np.asarray(
                problem.delay_frames,
                dtype=np.int32,
            ),
            decision_frame_support=np.asarray(
                self.decision_frame_support,
                dtype=np.int32,
            ),
            continuation_decision_frames=problem.config.frames_per_layer,
            required_clearance=problem.config.required_clearance,
            clamp_to_bounds=problem.config.clamp_to_bounds,
        )
        if self._native is None:
            raise RuntimeError(
                "native augmented pipeline workspace is unavailable"
            )

    @property
    def closed(self) -> bool:
        return self._native.closed

    def close(self) -> None:
        self._native.close()

    def __enter__(self) -> PipelineSurvivalWorkspace:
        if self.closed:
            raise RuntimeError("pipeline survival workspace is closed")
        return self

    def __exit__(self, _exception_type, _exception, _traceback) -> None:
        self.close()

    def query(
        self,
        *,
        policy_version: Hashable,
        frame: int,
        x: float,
        y: float,
        observed_action: str,
        pending_command: PendingCommand | None = None,
    ) -> QueryLocalSurvivalResult:
        row, column, _ = self.problem.project_to_lattice(x=x, y=y)
        return self.query_cell(
            policy_version=policy_version,
            frame=frame,
            row=row,
            column=column,
            observed_action=observed_action,
            pending_command=pending_command,
        )

    def query_cell(
        self,
        *,
        policy_version: Hashable,
        frame: int,
        row: int,
        column: int,
        observed_action: str,
        pending_command: PendingCommand | None = None,
    ) -> QueryLocalSurvivalResult:
        if policy_version != self.policy_version:
            raise StalePipelineWorkspaceError(
                "pipeline workspace policy version does not match query"
            )
        if observed_action not in self._action_indices:
            raise ValueError("observed action is absent from the action set")
        if (
            pending_command is not None
            and pending_command.action not in self._action_indices
        ):
            raise ValueError("pending action is absent from the action set")
        native_result = self._native.query(
            start_frame=frame,
            start_row=row,
            start_column=column,
            observed_action_index=self._action_indices[observed_action],
            pending_action_index=(
                self._action_indices[pending_command.action]
                if pending_command is not None
                else -1
            ),
            pending_remaining_frames=(
                np.asarray(
                    pending_command.remaining_frames,
                    dtype=np.int32,
                )
                if pending_command is not None
                else None
            ),
        )
        (
            state_frames,
            state_margin,
            action_frames,
            action_margins,
            best_mask,
            raw_stats,
        ) = native_result
        action_labels = tuple(
            (
                action.name,
                SurvivalLabel(
                    int(action_frames[index]),
                    float(action_margins[index]),
                ),
            )
            for index, action in enumerate(self.problem.actions)
        )
        stats = PipelineSurvivalQueryStats(
            *[int(value) for value in raw_stats]
        )
        return QueryLocalSurvivalResult(
            start_frame=frame,
            remaining_frames=self.problem.horizon_frames - frame,
            row=row,
            column=column,
            observed_action=observed_action,
            pending_command=pending_command,
            state_label=SurvivalLabel(state_frames, state_margin),
            action_labels=action_labels,
            best_actions=tuple(
                action.name
                for index, action in enumerate(self.problem.actions)
                if best_mask & (1 << index)
            ),
            evaluated_state_count=stats.memoized_state_count,
            backend=(
                "native_one_step_cadence_pipeline_workspace"
                if len(self.decision_frame_support) > 1
                else "native_augmented_pipeline_workspace"
            ),
            workspace_stats=stats,
        )

    def lookup_cell(
        self,
        *,
        policy_version: Hashable,
        frame: int,
        row: int,
        column: int,
        observed_action: str,
        pending_command: PendingCommand | None = None,
    ) -> QueryLocalSurvivalResult | None:
        """Consume a cached exact root without permitting cold expansion."""

        if policy_version != self.policy_version:
            raise StalePipelineWorkspaceError(
                "pipeline workspace policy version does not match lookup"
            )
        if observed_action not in self._action_indices:
            raise ValueError("observed action is absent from the action set")
        if (
            pending_command is not None
            and pending_command.action not in self._action_indices
        ):
            raise ValueError("pending action is absent from the action set")
        pending_remaining = (
            np.asarray(
                pending_command.remaining_frames,
                dtype=np.int32,
            )
            if pending_command is not None
            else None
        )
        if not self._native.contains_root(
            start_frame=frame,
            start_row=row,
            start_column=column,
            observed_action_index=self._action_indices[observed_action],
            pending_action_index=(
                self._action_indices[pending_command.action]
                if pending_command is not None
                else -1
            ),
            pending_remaining_frames=pending_remaining,
        ):
            return None
        return self.query_cell(
            policy_version=policy_version,
            frame=frame,
            row=row,
            column=column,
            observed_action=observed_action,
            pending_command=pending_command,
        )


def _normalize_decision_frame_support(
    support: tuple[int, ...] | None,
    *,
    default: int,
) -> tuple[int, ...]:
    normalized = (default,) if support is None else tuple(support)
    if (
        not normalized
        or tuple(sorted(set(normalized))) != normalized
        or normalized[0] <= 0
    ):
        raise ValueError(
            "decision-frame support must be sorted unique and positive"
        )
    return normalized


def _uniform_axis(axis: np.ndarray, name: str) -> tuple[np.ndarray, float]:
    values = np.asarray(axis, dtype=np.float64)
    if values.ndim != 1 or len(values) < 2:
        raise ValueError(f"{name} axis must contain at least two points")
    differences = np.diff(values)
    if not np.all(differences > 0.0):
        raise ValueError(f"{name} axis must be strictly increasing")
    step = float(differences[0])
    if not np.allclose(differences, step, rtol=0.0, atol=1e-6):
        raise ValueError(f"{name} axis must be uniform")
    return values, step


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
    """Solve one exact state with a robust last-write-wins input pipeline.

    At every decision epoch a newly selected desired action supersedes the
    older pending desired action.  Before the new action becomes visible, the
    older pending action may still become active.  A physical branch therefore
    follows ``observed -> older pending -> newly selected``.  If the new delay
    exceeds the next decision interval, its remaining delay is carried
    explicitly into the successor state.  At the public root, nature chooses
    both command delay and the next decision interval from their declared
    supports.  Deeper continuation values use ``config.frames_per_layer``;
    this is a one-transition robust value, not an unbounded variable-cadence
    survival proof.
    """

    x_values, x_step = _uniform_axis(x_axis, "x")
    y_values, y_step = _uniform_axis(y_axis, "y")
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
    cadence_support = _normalize_decision_frame_support(
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
) -> tuple[ReachablePipelineRoot, ...]:
    """Enumerate the exact-root frontier after issuing one selected action.

    This is kinematic reachability only.  It intentionally does not certify
    collision safety; a consumer must still use a fresh local certificate.
    Branches that produce the same exact root are grouped by the remaining
    delay support of their pending command.
    """

    x_values, x_step = _uniform_axis(x_axis, "x")
    y_values, y_step = _uniform_axis(y_axis, "y")
    cadence_support = _normalize_decision_frame_support(
        decision_frame_support,
        default=config.frames_per_layer,
    )
    if (
        not delay_frames
        or tuple(sorted(set(delay_frames))) != delay_frames
        or delay_frames[0] < 0
    ):
        raise ValueError("delay support is invalid")
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

    x_start = float(x_values[0])
    x_end = float(x_values[-1])
    y_start = float(y_values[0])
    y_end = float(y_values[-1])
    state_x = float(x_values[column])
    state_y = float(y_values[row])
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
            if step_count <= 0:
                continue
            for delay in delay_frames:
                displacement_x = 0.0
                displacement_y = 0.0
                terminal_row = row
                terminal_column = column
                reachable = True
                for physical_step in range(1, step_count + 1):
                    if physical_step > delay:
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
                    target_x = min(x_end, max(x_start, target_x))
                    target_y = min(y_end, max(y_start, target_y))
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
                if not reachable:
                    continue

                if delay < step_count or delay == step_count:
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
                    successor_remaining = delay - step_count
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


def query_local_survival(
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
    backend: str = "auto",
) -> QueryLocalSurvivalResult:
    """Use the query-local native kernel with scalar fallback."""

    if backend not in {"auto", "native", "scalar"}:
        raise ValueError("query survival backend must be auto, native, or scalar")
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
    native_result = (
        native_backend.query_local_survival_arrays(
            x_axis=x_axis,
            y_axis=y_axis,
            clearance_volume=clearance_volume,
            velocity_x=np.asarray(
                [action.velocity_x for action in actions],
                dtype=np.float64,
            ),
            velocity_y=np.asarray(
                [action.velocity_y for action in actions],
                dtype=np.float64,
            ),
            delay_frames=np.asarray(delay_frames, dtype=np.int32),
            decision_frames=config.frames_per_layer,
            required_clearance=config.required_clearance,
            clamp_to_bounds=config.clamp_to_bounds,
            start_frame=start_frame,
            start_row=row,
            start_column=column,
            observed_action_index=action_indices[observed_action],
            pending_action_index=(
                action_indices[pending_command.action]
                if pending_command is not None
                else -1
            ),
            pending_remaining_frames=(
                np.asarray(
                    pending_command.remaining_frames,
                    dtype=np.int32,
                )
                if pending_command is not None
                else None
            ),
        )
        if backend in {"auto", "native"}
        else None
    )
    if native_result is None:
        if backend == "native":
            raise RuntimeError("native query-local survival backend unavailable")
        return scalar_query_local_survival(
            x_axis=x_axis,
            y_axis=y_axis,
            clearance_volume=clearance_volume,
            actions=actions,
            delay_frames=delay_frames,
            config=config,
            start_frame=start_frame,
            row=row,
            column=column,
            observed_action=observed_action,
            pending_command=pending_command,
        )
    (
        state_frames,
        state_margin,
        action_frames,
        action_margins,
        best_mask,
        evaluated_states,
    ) = native_result
    action_labels = tuple(
        (
            action.name,
            SurvivalLabel(
                int(action_frames[index]),
                float(action_margins[index]),
            ),
        )
        for index, action in enumerate(actions)
    )
    return QueryLocalSurvivalResult(
        start_frame=start_frame,
        remaining_frames=clearance_volume.shape[0] - 1 - start_frame,
        row=row,
        column=column,
        observed_action=observed_action,
        pending_command=pending_command,
        state_label=SurvivalLabel(state_frames, state_margin),
        action_labels=action_labels,
        best_actions=tuple(
            action.name
            for index, action in enumerate(actions)
            if best_mask & (1 << index)
        ),
        evaluated_state_count=evaluated_states,
        backend="native_pending_pipeline",
    )


__all__ = [
    "PendingCommand",
    "PipelineSurvivalQueryStats",
    "PipelineSurvivalWorkspace",
    "QueryLocalSurvivalResult",
    "ReachablePipelineRoot",
    "StalePipelineWorkspaceError",
    "SurvivalQueryProblem",
    "enumerate_next_decision_roots",
    "query_local_survival",
    "scalar_query_local_survival",
]
