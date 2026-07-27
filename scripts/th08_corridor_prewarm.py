#!/usr/bin/env python3
"""TH08 query-pipeline prewarm startup and lifecycle ownership."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Hashable, Protocol

from touhou_control.pipeline_prewarm_service import (
    PipelinePrewarmService,
    PipelinePrewarmServiceSnapshot,
)
from touhou_control.pipeline_root_schedule import (
    schedule_pipeline_frontier,
)
from touhou_control.query_survival import (
    PendingCommand,
    QueryLocalSurvivalResult,
    ReachablePipelineRoot,
    SurvivalQueryProblem,
)


PIPELINE_PREWARM_DECISION_FRAMES = (4, 5, 6)
PIPELINE_PREWARM_INITIAL_ROOT_FRAMES = (4,)
PIPELINE_PREWARM_WORKER_COUNT = 3
PIPELINE_PREWARM_SCHEDULE_FRAMES = (2, 3, 4, 5, 6, 7, 8, 9)
PIPELINE_PREWARM_SCHEDULE_ROOT_LIMIT = 2


class HasPipelinePrewarmService(Protocol):
    pipeline_prewarm_service: PipelinePrewarmService | None


class PipelinePrewarmSolution(HasPipelinePrewarmService, Protocol):
    source_frame: int
    snapshot_frame: int | None
    context_key: tuple[int, int, int | None] | None


@dataclass(frozen=True)
class CorridorPrewarmStart:
    service: PipelinePrewarmService | None
    error: str | None
    elapsed_ms: float


@dataclass(frozen=True)
class PipelinePrewarmShadowQuery:
    """One lookup-only current-version shadow observation."""

    status: str
    root: ReachablePipelineRoot | None
    result: QueryLocalSurvivalResult | None
    lookup_ms: float
    service: PipelinePrewarmServiceSnapshot | None


@dataclass(frozen=True)
class PipelinePrewarmRetarget:
    """One non-authoritative post-issue rolling target request."""

    status: str
    revision: int | None
    root_count: int
    candidate_root_count: int
    elapsed_ms: float


def _policy_version(
    solution: PipelinePrewarmSolution,
) -> tuple[int, int | None, tuple[int, int, int | None] | None]:
    return (
        solution.source_frame,
        solution.snapshot_frame,
        solution.context_key,
    )


def start_corridor_pipeline_prewarm(
    *,
    problem: SurvivalQueryProblem,
    player_x: float,
    player_y: float,
    active_action: str,
    policy_version: Hashable,
) -> CorridorPrewarmStart:
    """Start one optional shadow service from an already prepared problem."""

    started = time.perf_counter()
    row, column, _ = problem.project_to_lattice(
        x=player_x,
        y=player_y,
    )
    roots = tuple(
        ReachablePipelineRoot(
            frame=frame,
            row=row,
            column=column,
            observed_action=active_action,
            pending_command=None,
        )
        for frame in PIPELINE_PREWARM_INITIAL_ROOT_FRAMES
        if frame < problem.horizon_frames
    )
    if not roots:
        return CorridorPrewarmStart(
            service=None,
            error="no initial root inside policy horizon",
            elapsed_ms=(time.perf_counter() - started) * 1000.0,
        )
    try:
        service = PipelinePrewarmService(
            problem=problem,
            policy_version=policy_version,
            initial_roots=roots,
            decision_frame_support=PIPELINE_PREWARM_DECISION_FRAMES,
            worker_count=PIPELINE_PREWARM_WORKER_COUNT,
        )
        error = None
    except Exception as caught:
        service = None
        error = f"{type(caught).__name__}: {caught}"
    return CorridorPrewarmStart(
        service=service,
        error=error,
        elapsed_ms=(time.perf_counter() - started) * 1000.0,
    )


def close_pipeline_prewarm_owner(
    owner: HasPipelinePrewarmService | None,
) -> None:
    """Cancel and join one owner's shadow service, if present."""

    if owner is not None and owner.pipeline_prewarm_service is not None:
        owner.pipeline_prewarm_service.close()


def close_retired_pipeline_prewarm_owners(
    candidates: tuple[HasPipelinePrewarmService | None, ...],
    retained: tuple[HasPipelinePrewarmService | None, ...] = (),
) -> None:
    """Close candidate services that are not shared by retained owners."""

    retained_services = {
        id(owner.pipeline_prewarm_service)
        for owner in retained
        if (
            owner is not None
            and owner.pipeline_prewarm_service is not None
        )
    }
    closed_services: set[int] = set()
    for owner in candidates:
        if owner is None or owner.pipeline_prewarm_service is None:
            continue
        identity = id(owner.pipeline_prewarm_service)
        if identity in retained_services or identity in closed_services:
            continue
        owner.pipeline_prewarm_service.close()
        closed_services.add(identity)


def corridor_pipeline_prewarm_query(
    solution: PipelinePrewarmSolution | None,
    *,
    current_frame: int,
    player_x: float,
    player_y: float,
    observed_action: str,
    pending_command: PendingCommand | None,
    max_age_frames: int,
) -> PipelinePrewarmShadowQuery:
    """Lookup one current exact root without starting synchronous work."""

    started = time.perf_counter()
    if solution is None or solution.pipeline_prewarm_service is None:
        return PipelinePrewarmShadowQuery(
            status="unavailable",
            root=None,
            result=None,
            lookup_ms=(time.perf_counter() - started) * 1000.0,
            service=None,
        )
    service = solution.pipeline_prewarm_service
    if service.policy_version != _policy_version(solution):
        return PipelinePrewarmShadowQuery(
            status="stale_policy_version",
            root=None,
            result=None,
            lookup_ms=(time.perf_counter() - started) * 1000.0,
            service=service.snapshot(),
        )
    age = current_frame - solution.source_frame
    problem = service.problem
    if age < 0:
        return PipelinePrewarmShadowQuery(
            status="pending_future_epoch",
            root=None,
            result=None,
            lookup_ms=(time.perf_counter() - started) * 1000.0,
            service=service.snapshot(),
        )
    if age > max_age_frames or age >= problem.horizon_frames:
        return PipelinePrewarmShadowQuery(
            status="outside_policy_horizon",
            root=None,
            result=None,
            lookup_ms=(time.perf_counter() - started) * 1000.0,
            service=service.snapshot(),
        )
    row, column, _ = problem.project_to_lattice(
        x=player_x,
        y=player_y,
    )
    root = ReachablePipelineRoot(
        frame=age,
        row=row,
        column=column,
        observed_action=observed_action,
        pending_command=pending_command,
    )
    result = service.lookup(root)
    return PipelinePrewarmShadowQuery(
        status="hit" if result is not None else "miss",
        root=root,
        result=result,
        lookup_ms=(time.perf_counter() - started) * 1000.0,
        service=service.snapshot(),
    )


def corridor_pipeline_prewarm_retarget(
    solution: PipelinePrewarmSolution | None,
    *,
    root: ReachablePipelineRoot | None,
    selected_action: str,
    physical_x: float,
    physical_y: float,
    command_issue_offset: int,
    preferred_decision_frame: int,
) -> PipelinePrewarmRetarget:
    """Queue a bounded, physically ranked next-root frontier."""

    started = time.perf_counter()
    if (
        solution is None
        or solution.pipeline_prewarm_service is None
        or root is None
    ):
        return PipelinePrewarmRetarget(
            status="unavailable",
            revision=None,
            root_count=0,
            candidate_root_count=0,
            elapsed_ms=(time.perf_counter() - started) * 1000.0,
        )
    service = solution.pipeline_prewarm_service
    if service.policy_version != _policy_version(solution):
        return PipelinePrewarmRetarget(
            status="stale_policy_version",
            revision=None,
            root_count=0,
            candidate_root_count=0,
            elapsed_ms=(time.perf_counter() - started) * 1000.0,
        )
    schedule = schedule_pipeline_frontier(
        problem=service.problem,
        root=root,
        selected_action=selected_action,
        physical_x=physical_x,
        physical_y=physical_y,
        command_issue_offset=command_issue_offset,
        preferred_decision_frame=preferred_decision_frame,
        scheduling_frame_support=PIPELINE_PREWARM_SCHEDULE_FRAMES,
        root_limit=PIPELINE_PREWARM_SCHEDULE_ROOT_LIMIT,
    )
    if not schedule.roots:
        return PipelinePrewarmRetarget(
            status="empty_frontier",
            revision=None,
            root_count=0,
            candidate_root_count=0,
            elapsed_ms=(time.perf_counter() - started) * 1000.0,
        )
    revision = service.retarget(schedule.roots)
    return PipelinePrewarmRetarget(
        status="queued",
        revision=revision,
        root_count=len(schedule.roots),
        candidate_root_count=schedule.candidate_count,
        elapsed_ms=(time.perf_counter() - started) * 1000.0,
    )


__all__ = [
    "CorridorPrewarmStart",
    "PIPELINE_PREWARM_DECISION_FRAMES",
    "PIPELINE_PREWARM_INITIAL_ROOT_FRAMES",
    "PIPELINE_PREWARM_SCHEDULE_FRAMES",
    "PIPELINE_PREWARM_SCHEDULE_ROOT_LIMIT",
    "PIPELINE_PREWARM_WORKER_COUNT",
    "PipelinePrewarmRetarget",
    "PipelinePrewarmShadowQuery",
    "close_pipeline_prewarm_owner",
    "close_retired_pipeline_prewarm_owners",
    "corridor_pipeline_prewarm_query",
    "corridor_pipeline_prewarm_retarget",
    "start_corridor_pipeline_prewarm",
]
