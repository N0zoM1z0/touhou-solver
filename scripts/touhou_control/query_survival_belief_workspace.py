"""Versioned native workspace for the non-clairvoyant belief recurrence."""

from __future__ import annotations

from typing import TYPE_CHECKING, Hashable

import numpy as np

from . import native_backend
from .query_survival_lattice import normalize_decision_frame_support
from .query_survival_types import (
    ActionColumnRecommendation,
    BeliefPipelineQueryStats,
    BeliefUpperCertification,
    PendingCommand,
    QueryLocalSurvivalResult,
)
from .query_survival_workspace import StalePipelineWorkspaceError
from .reachability_oracle import SurvivalLabel

if TYPE_CHECKING:
    from .query_survival_problem import SurvivalQueryProblem


class BeliefPipelineSurvivalWorkspace:
    """Versioned native memo for the recursively variable-cadence game.

    This workspace treats selecting the already-held desired input as
    hold/no-write, and groups indistinguishable remaining-delay branches
    before each future maximization.  A root with a pending command identifies
    that command as the held desired input; a root without one assumes the
    observed action is also held.  It is an offline/shadow research backend;
    it has no live lookup or prewarm authority yet.

    A positive ``remaining_delay_bucket_size`` partitions successors by
    ranges of hidden remaining delay. Width one is exact revelation.
    Every positive width is an optimistic information relaxation, not the
    physical controller value. ``reveal_remaining_delay=True`` remains a
    compatibility alias for width one.
    """

    def __init__(
        self,
        *,
        problem: SurvivalQueryProblem,
        policy_version: Hashable,
        decision_frame_support: tuple[int, ...],
        continuation_actions: tuple[str, ...] | None = None,
        budgeted_continuation_actions: tuple[str, ...] | None = None,
        continuation_action_budget: int = 0,
        reveal_remaining_delay: bool = False,
        remaining_delay_bucket_size: int | None = None,
        continuation_policy: str = "optimal",
        candidate_policy_width: int = 1,
    ) -> None:
        self.problem = problem
        self.policy_version = policy_version
        self.decision_frame_support = normalize_decision_frame_support(
            decision_frame_support,
            default=problem.config.frames_per_layer,
        )
        self._action_indices = {
            action.name: index
            for index, action in enumerate(problem.actions)
        }
        continuation_names = (
            tuple(self._action_indices)
            if continuation_actions is None
            else continuation_actions
        )
        if (
            not continuation_names
            or len(set(continuation_names)) != len(continuation_names)
            or any(
                name not in self._action_indices
                for name in continuation_names
            )
        ):
            raise ValueError(
                "belief continuation actions must be unique known actions"
            )
        self.continuation_actions = continuation_names
        budgeted_names = (
            ()
            if budgeted_continuation_actions is None
            else budgeted_continuation_actions
        )
        if (
            continuation_action_budget < 0
            or len(set(budgeted_names)) != len(budgeted_names)
            or any(
                name not in self._action_indices
                for name in budgeted_names
            )
            or set(continuation_names).intersection(budgeted_names)
        ):
            raise ValueError(
                "budgeted belief continuation actions must be unique, "
                "known, disjoint from base actions, with a nonnegative "
                "budget"
            )
        self.budgeted_continuation_actions = budgeted_names
        self.continuation_action_budget = continuation_action_budget
        if remaining_delay_bucket_size is None:
            remaining_delay_bucket_size = (
                1 if reveal_remaining_delay else 0
            )
        if (
            remaining_delay_bucket_size < 0
            or remaining_delay_bucket_size > 62
            or (
                reveal_remaining_delay
                and remaining_delay_bucket_size != 1
            )
        ):
            raise ValueError(
                "remaining-delay bucket size must be in [0, 62], and "
                "the reveal alias requires exact width one"
            )
        self.remaining_delay_bucket_size = remaining_delay_bucket_size
        self.reveal_remaining_delay = remaining_delay_bucket_size > 0
        if continuation_policy not in ("optimal", "greedy_prefix"):
            raise ValueError(
                "belief continuation policy must be 'optimal' or "
                "'greedy_prefix'"
            )
        if self.reveal_remaining_delay and continuation_policy != "optimal":
            raise ValueError(
                "candidate policy lower bounds cannot reveal hidden delay"
            )
        if not 1 <= candidate_policy_width <= len(problem.actions):
            raise ValueError(
                "candidate policy width must fit the action set"
            )
        self.continuation_policy = continuation_policy
        self.candidate_policy_width = candidate_policy_width
        base_action_mask = 0
        for name in continuation_names:
            base_action_mask |= (
                1 << self._action_indices[name]
            )
        budgeted_action_mask = 0
        for name in budgeted_names:
            budgeted_action_mask |= 1 << self._action_indices[name]
        self._native = (
            native_backend.create_belief_pipeline_survival_workspace(
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
                base_action_mask=base_action_mask,
                budgeted_action_mask=budgeted_action_mask,
                continuation_action_budget=continuation_action_budget,
                remaining_delay_bucket_size=(
                    remaining_delay_bucket_size
                ),
                continuation_policy_mode=(
                    candidate_policy_width
                    if continuation_policy == "greedy_prefix"
                    else 0
                ),
                delay_frames=np.asarray(
                    problem.delay_frames,
                    dtype=np.int32,
                ),
                decision_frame_support=np.asarray(
                    self.decision_frame_support,
                    dtype=np.int32,
                ),
                required_clearance=problem.config.required_clearance,
                clamp_to_bounds=problem.config.clamp_to_bounds,
            )
        )
        if self._native is None:
            raise RuntimeError(
                "native belief pipeline workspace is unavailable"
            )

    @property
    def closed(self) -> bool:
        return self._native.closed

    def close(self) -> None:
        self._native.close()

    def cancel(self) -> None:
        self._native.cancel()

    def __enter__(self) -> BeliefPipelineSurvivalWorkspace:
        if self.closed:
            raise RuntimeError("belief pipeline workspace is closed")
        return self

    def __exit__(self, _exception_type, _exception, _traceback) -> None:
        self.close()

    def query_cell(
        self,
        *,
        policy_version: Hashable,
        frame: int,
        row: int,
        column: int,
        observed_action: str,
        pending_command: PendingCommand | None = None,
        continuation_action_budget: int | None = None,
        timeout_ms: int = 0,
    ) -> QueryLocalSurvivalResult:
        if policy_version != self.policy_version:
            raise StalePipelineWorkspaceError(
                "belief pipeline policy version does not match query"
            )
        if observed_action not in self._action_indices:
            raise ValueError("observed action is absent from the action set")
        if (
            pending_command is not None
            and pending_command.action not in self._action_indices
        ):
            raise ValueError("pending action is absent from the action set")
        if (
            continuation_action_budget is not None
            and (
                continuation_action_budget < 0
                or continuation_action_budget
                > self.continuation_action_budget
            )
        ):
            raise ValueError(
                "query continuation budget must be between zero and the "
                "workspace maximum"
            )
        (
            state_frames,
            state_margin,
            action_frames,
            action_margins,
            best_mask,
            raw_stats,
        ) = self._native.query(
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
            continuation_action_budget=continuation_action_budget,
            timeout_ms=timeout_ms,
        )
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
        stats = BeliefPipelineQueryStats(
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
                (
                    "native_clairvoyant_variable_cadence_pipeline"
                    if self.remaining_delay_bucket_size == 1
                    else "native_bucketed_upper_variable_cadence_pipeline"
                )
                if self.reveal_remaining_delay
                else (
                    "native_greedy_prefix_belief_pipeline"
                    if self.continuation_policy == "greedy_prefix"
                    else "native_belief_variable_cadence_pipeline"
                )
            ),
            workspace_stats=stats,
        )

    def certify_upper_bound(
        self,
        *,
        policy_version: Hashable,
        frame: int,
        row: int,
        column: int,
        observed_action: str,
        lower_bound: SurvivalLabel,
        pending_command: PendingCommand | None = None,
        timeout_ms: int = 0,
    ) -> BeliefUpperCertification:
        """Reject optimistic actions that cannot beat ``lower``.

        A deadline returns the in-flight and unvisited actions unresolved;
        it never converts unfinished optimistic work into certification.
        Repeating the exact same root and bit-identical lower threshold on
        this immutable workspace resumes completed threshold subproblems.
        """

        if policy_version != self.policy_version:
            raise StalePipelineWorkspaceError(
                "belief pipeline policy version does not match query"
            )
        if not self.reveal_remaining_delay:
            raise ValueError(
                "upper certification requires a remaining-delay "
                "information relaxation"
            )
        if self.continuation_policy != "optimal":
            raise ValueError(
                "upper certification requires optimal continuation"
            )
        if (
            self.continuation_actions != tuple(self._action_indices)
            or self.budgeted_continuation_actions
        ):
            raise ValueError(
                "upper certification requires unrestricted continuation "
                "actions"
            )
        if observed_action not in self._action_indices:
            raise ValueError("observed action is absent from the action set")
        if (
            pending_command is not None
            and pending_command.action not in self._action_indices
        ):
            raise ValueError("pending action is absent from the action set")
        (
            unresolved_mask,
            deadline_expired,
            raw_stats,
        ) = self._native.certify_upper(
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
            lower_frames=lower_bound.guaranteed_frames,
            lower_margin=lower_bound.bottleneck_margin,
            timeout_ms=timeout_ms,
        )
        stats = BeliefPipelineQueryStats(
            *[int(value) for value in raw_stats]
        )
        unresolved = tuple(
            action.name
            for index, action in enumerate(self.problem.actions)
            if unresolved_mask & (1 << index)
        )
        return BeliefUpperCertification(
            lower_bound=lower_bound,
            certified=not unresolved,
            unresolved_actions=unresolved,
            deadline_expired=deadline_expired,
            workspace_stats=stats,
        )

    def recommend_action_column(
        self,
        *,
        policy_version: Hashable,
        frame: int,
        row: int,
        column: int,
        observed_action: str,
        target_root_action: str,
        pending_command: PendingCommand | None = None,
        max_depth: int = 64,
        timeout_ms: int = 0,
    ) -> ActionColumnRecommendation:
        """Find one exact one-step deviation on a worst restricted path.

        The recommendation is only a proposer. Adding its action to the
        continuation class and completing a new lower solve is required
        before the result is attainable.
        """

        if policy_version != self.policy_version:
            raise StalePipelineWorkspaceError(
                "belief pipeline policy version does not match query"
            )
        if (
            self.reveal_remaining_delay
            or self.continuation_policy != "optimal"
            or self.budgeted_continuation_actions
            or self.continuation_action_budget != 0
        ):
            raise ValueError(
                "action-column recommendation requires an ordinary "
                "zero-budget restricted belief workspace"
            )
        if observed_action not in self._action_indices:
            raise ValueError("observed action is absent from the action set")
        if target_root_action not in self._action_indices:
            raise ValueError(
                "target root action is absent from the action set"
            )
        if (
            pending_command is not None
            and pending_command.action not in self._action_indices
        ):
            raise ValueError("pending action is absent from the action set")
        (
            recommended_index,
            witness,
            current,
            deviation,
            witness_depth,
            raw_stats,
        ) = self._native.recommend_action_column(
            start_frame=frame,
            start_row=row,
            start_column=column,
            observed_action_index=self._action_indices[observed_action],
            target_root_action_index=(
                self._action_indices[target_root_action]
            ),
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
            max_depth=max_depth,
            timeout_ms=timeout_ms,
        )
        (
            witness_frame,
            witness_row,
            witness_column,
            witness_active,
            witness_pending,
            witness_remaining_mask,
        ) = witness
        index_to_action = tuple(
            action.name for action in self.problem.actions
        )
        return ActionColumnRecommendation(
            target_root_action=target_root_action,
            recommended_action=(
                index_to_action[recommended_index]
                if recommended_index >= 0
                else None
            ),
            witness_frame=witness_frame,
            witness_row=witness_row,
            witness_column=witness_column,
            witness_active_action=(
                index_to_action[witness_active]
                if witness_active >= 0
                else None
            ),
            witness_pending_action=(
                index_to_action[witness_pending]
                if witness_pending >= 0
                else None
            ),
            witness_remaining_frames=tuple(
                remaining
                for remaining in range(1, 63)
                if witness_remaining_mask & (1 << remaining)
            ),
            current_label=SurvivalLabel(*current),
            deviation_label=SurvivalLabel(*deviation),
            witness_depth=witness_depth,
            workspace_stats=BeliefPipelineQueryStats(
                *[int(value) for value in raw_stats]
            ),
        )



__all__ = ["BeliefPipelineSurvivalWorkspace"]
