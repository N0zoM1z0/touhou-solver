"""Versioned native workspace for the legacy always-issue recurrence."""

from __future__ import annotations

from typing import TYPE_CHECKING, Hashable

import numpy as np

from . import native_backend
from .query_survival_lattice import normalize_decision_frame_support
from .query_survival_types import (
    PendingCommand,
    PipelineSurvivalQueryStats,
    QueryLocalSurvivalResult,
)
from .reachability_oracle import SurvivalLabel

if TYPE_CHECKING:
    from .query_survival_problem import SurvivalQueryProblem


PipelineWorkspaceCancelledError = (
    native_backend.PipelineNativeCancelledError
)
PipelineWorkspaceDeadlineError = native_backend.PipelineNativeDeadlineError


class StalePipelineWorkspaceError(RuntimeError):
    """A query attempted to use a workspace from another policy version."""


class PipelineSurvivalWorkspace:
    """Versioned native memo for the legacy always-issue hybrid.

    Like ``scalar_query_local_survival``, it does not implement live no-write
    semantics when the selected action equals the held desired input.  A
    public query branches over ``decision_frame_support`` once and continuation
    states retain the configured fixed interval.  Keep this workspace
    shadow/offline and use ``BeliefPipelineSurvivalWorkspace`` for the declared
    recursive non-clairvoyant finite model.
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
        self.decision_frame_support = normalize_decision_frame_support(
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

    def cancel(self) -> None:
        """Cooperatively invalidate native work for this policy version."""

        self._native.cancel()

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
        timeout_ms: int = 0,
    ) -> QueryLocalSurvivalResult:
        row, column, _ = self.problem.project_to_lattice(x=x, y=y)
        return self.query_cell(
            policy_version=policy_version,
            frame=frame,
            row=row,
            column=column,
            observed_action=observed_action,
            pending_command=pending_command,
            timeout_ms=timeout_ms,
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
        timeout_ms: int = 0,
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
            timeout_ms=timeout_ms,
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

    def prewarm_continuation_cell(
        self,
        *,
        policy_version: Hashable,
        frame: int,
        row: int,
        column: int,
        observed_action: str,
        pending_command: PendingCommand | None = None,
        timeout_ms: int = 0,
    ) -> tuple[SurvivalLabel, PipelineSurvivalQueryStats]:
        """Populate fixed-cadence state values without public root labels."""

        if policy_version != self.policy_version:
            raise StalePipelineWorkspaceError(
                "pipeline workspace policy version does not match prewarm"
            )
        if observed_action not in self._action_indices:
            raise ValueError("observed action is absent from the action set")
        if (
            pending_command is not None
            and pending_command.action not in self._action_indices
        ):
            raise ValueError("pending action is absent from the action set")
        frames, margin, raw_stats = self._native.prewarm_continuation(
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
            timeout_ms=timeout_ms,
        )
        return (
            SurvivalLabel(frames, margin),
            PipelineSurvivalQueryStats(
                *[int(value) for value in raw_stats]
            ),
        )

    def merge_continuation_from(
        self,
        source: PipelineSurvivalWorkspace,
    ) -> int:
        """Merge exact fixed-continuation values from the same problem."""

        if self.policy_version != source.policy_version:
            raise StalePipelineWorkspaceError(
                "cannot merge pipeline workspaces from different versions"
            )
        if self.problem is not source.problem:
            raise ValueError(
                "continuation merge requires the same immutable problem"
            )
        return self._native.merge_continuation_from(source._native)

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



__all__ = [
    "PipelineSurvivalWorkspace",
    "PipelineWorkspaceCancelledError",
    "PipelineWorkspaceDeadlineError",
    "StalePipelineWorkspaceError",
]
