"""Bounded physical scheduling for exact augmented-pipeline roots.

This module chooses where scarce background compute should go.  It does not
change the exact public-root value contract and it never certifies safety.
"""

from __future__ import annotations

from dataclasses import dataclass

from .query_survival import (
    PendingCommand,
    ReachablePipelineRoot,
    SurvivalQueryProblem,
    enumerate_next_decision_roots,
)


@dataclass(frozen=True)
class PipelineRootSchedule:
    """One ranked subset of a physically reachable exact-root frontier."""

    roots: tuple[ReachablePipelineRoot, ...]
    candidates: tuple[ReachablePipelineRoot, ...]
    candidate_count: int
    preferred_decision_frame: int
    preferred_pickup_delay: int


def _pending_distance(
    left: PendingCommand | None,
    right: PendingCommand | None,
) -> float:
    if left is None or right is None:
        return 0.0 if left is right else 2.0
    action_cost = 0.0 if left.action == right.action else 1.0
    left_mean = sum(left.remaining_frames) / len(left.remaining_frames)
    right_mean = sum(right.remaining_frames) / len(
        right.remaining_frames
    )
    return action_cost + abs(left_mean - right_mean)


def schedule_pipeline_frontier(
    *,
    problem: SurvivalQueryProblem,
    root: ReachablePipelineRoot,
    selected_action: str,
    physical_x: float,
    physical_y: float,
    command_issue_offset: int,
    preferred_decision_frame: int,
    scheduling_frame_support: tuple[int, ...],
    root_limit: int,
    preferred_pickup_delay: int | None = None,
) -> PipelineRootSchedule:
    """Rank exact roots by a nominal physical delivery branch.

    All delay/cadence branches remain candidates.  The bounded result merely
    prioritizes roots nearest the predicted next observation: actual subcell
    position, time already spent before issue, expected decision frame, and
    expected pickup delay.  A miss remains a normal outcome.
    """

    if root_limit <= 0:
        raise ValueError("pipeline schedule root limit must be positive")
    if (
        not scheduling_frame_support
        or tuple(sorted(set(scheduling_frame_support)))
        != scheduling_frame_support
        or scheduling_frame_support[0] <= 0
    ):
        raise ValueError(
            "pipeline scheduling frames must be sorted unique and positive"
        )
    delay = (
        problem.delay_frames[0]
        if preferred_pickup_delay is None
        else preferred_pickup_delay
    )
    if delay not in problem.delay_frames:
        raise ValueError(
            "preferred pickup delay is outside the policy support"
        )
    candidates = enumerate_next_decision_roots(
        x_axis=problem.x_axis,
        y_axis=problem.y_axis,
        actions=problem.actions,
        delay_frames=problem.delay_frames,
        decision_frame_support=scheduling_frame_support,
        config=problem.config,
        start_frame=root.frame,
        horizon_frame=problem.horizon_frames,
        row=root.row,
        column=root.column,
        observed_action=root.observed_action,
        selected_action=selected_action,
        pending_command=root.pending_command,
        physical_start_x=physical_x,
        physical_start_y=physical_y,
        command_issue_offset=command_issue_offset,
    )
    if not candidates:
        return PipelineRootSchedule(
            roots=(),
            candidates=(),
            candidate_count=0,
            preferred_decision_frame=preferred_decision_frame,
            preferred_pickup_delay=delay,
        )
    preferred_frame = min(
        scheduling_frame_support[-1],
        max(
            command_issue_offset + 1,
            preferred_decision_frame,
        ),
    )
    nominal_roots = enumerate_next_decision_roots(
        x_axis=problem.x_axis,
        y_axis=problem.y_axis,
        actions=problem.actions,
        delay_frames=(delay,),
        decision_frame_support=(preferred_frame,),
        config=problem.config,
        start_frame=root.frame,
        horizon_frame=problem.horizon_frames,
        row=root.row,
        column=root.column,
        observed_action=root.observed_action,
        selected_action=selected_action,
        pending_command=root.pending_command,
        physical_start_x=physical_x,
        physical_start_y=physical_y,
        command_issue_offset=command_issue_offset,
    )
    if not nominal_roots:
        raise RuntimeError(
            "nonempty frontier has no nominal scheduling root"
        )

    def scheduling_distance(
        candidate: ReachablePipelineRoot,
    ) -> tuple[object, ...]:
        distance = min(
            (
                abs(candidate.frame - nominal.frame) * 16.0
                + (
                    candidate.observed_action
                    != nominal.observed_action
                )
                * 12.0
                + _pending_distance(
                    candidate.pending_command,
                    nominal.pending_command,
                )
                * 8.0
                + abs(candidate.row - nominal.row) * 2.0
                + abs(candidate.column - nominal.column) * 2.0
            )
            for nominal in nominal_roots
        )
        return (
            distance,
            candidate.frame,
            candidate.row,
            candidate.column,
            candidate.observed_action,
            repr(candidate.pending_command),
        )

    return PipelineRootSchedule(
        roots=tuple(
            sorted(candidates, key=scheduling_distance)[:root_limit]
        ),
        candidates=candidates,
        candidate_count=len(candidates),
        preferred_decision_frame=preferred_frame,
        preferred_pickup_delay=delay,
    )


__all__ = [
    "PipelineRootSchedule",
    "schedule_pipeline_frontier",
]
