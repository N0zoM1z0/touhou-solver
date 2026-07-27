#!/usr/bin/env python3
"""Asynchronous TH08 corridor-policy runtime.

This module owns policy epochs, corridor commitments, capsule publication, and
optional shadow-policy queries.  The live agent should only coordinate these
results with its local issue-time controller.
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Protocol

from th08_corridor_adapter import (
    TH08_CORRIDOR_CONFIG,
    lower_th08_corridor_hazards,
    plan_prepared_lowered_th08_corridor,
    prepare_lowered_th08_corridor,
)
from th08_corridor_audit import submit_corridor_audit
from th08_corridor_prewarm import (
    PIPELINE_PREWARM_DECISION_FRAMES,
    PIPELINE_PREWARM_INITIAL_ROOT_FRAMES,
    PIPELINE_PREWARM_SCHEDULE_FRAMES,
    PIPELINE_PREWARM_SCHEDULE_ROOT_LIMIT,
    PIPELINE_PREWARM_WORKER_COUNT,
    PipelinePrewarmRetarget,
    PipelinePrewarmShadowQuery,
    close_pipeline_prewarm_owner,
    close_retired_pipeline_prewarm_owners,
    corridor_pipeline_prewarm_query,
    corridor_pipeline_prewarm_retarget,
    start_corridor_pipeline_prewarm,
)
from touhou_control import native_backend
from touhou_control.background_priority import (
    lower_current_thread_priority,
)
from touhou_control.corridor.runtime import (
    CorridorPolicyArtifact,
    CorridorPublication,
    CorridorRuntimeHandles,
    CorridorSolution,
)
from touhou_control.query_survival import (
    PendingCommand,
    QueryLocalSurvivalResult,
    ReachablePipelineRoot,
    StalePipelineWorkspaceError,
    SurvivalQueryProblem,
)
from touhou_control.candidate_verifier_service import (
    CandidateVerifierTarget,
)
from touhou_control.viability import SafetyValueQuery, ViabilityQuery


CORRIDOR_MIN_COMMIT_FRAMES = 32
# The full-horizon 8px policy is retained as an offline/shadow CE-0100 gate.
# A physical Stage-4A trial showed that enabling it on every coarse-empty
# source made rolling policies stale enough to harm the local controller.
LIVE_REFINEMENT_GRID_STEPS: tuple[float, ...] = ()
SHADOW_REFINEMENT_GRID_STEPS = (8.0,)
# Fused survival labels have scalar parity inside one frozen hazard model, but
# the Stage-4A live trial showed that their extra service time and stale-model
# authority are not yet acceptable.  Keep them available to replay/shadow
# callers without allowing them to rank live actions.
LIVE_SURVIVAL_LABELS = False
SHADOW_SURVIVAL_LABELS = True
class SlottedHazard(Protocol):
    slot: int


class PointerHazard(Protocol):
    pointer: int


@dataclass
class CorridorCommitment:
    """Retain a viable gate component across asynchronous replans."""

    lane: str | None = None
    expires_frame: int = -1
    context_key: tuple[int, int, int | None] | None = None

    def set_context(
        self,
        context_key: tuple[int, int, int | None],
    ) -> bool:
        if self.context_key == context_key:
            return False
        self.context_key = context_key
        self.lane = None
        self.expires_frame = -1
        return True

    def active_lane(self, frame: int) -> str | None:
        if self.lane is None or frame >= self.expires_frame:
            return None
        return self.lane

    def accept(self, solution: CorridorSolution, *, current_frame: int) -> None:
        if not solution.plan.reachable or solution.plan.gate is None:
            return
        active_lane = self.active_lane(current_frame)
        if (
            active_lane is not None
            and (
                (
                    solution.required_gate_lane == active_lane
                    and solution.constraint_honored
                )
                or solution.plan.lane == active_lane
            )
        ):
            return
        if active_lane is None and solution.required_gate_lane is not None:
            self.lane = None
            self.expires_frame = -1
            return
        self.lane = solution.plan.lane
        self.expires_frame = max(
            current_frame + CORRIDOR_MIN_COMMIT_FRAMES,
            solution.source_frame + solution.plan.gate.frame,
        )


def solve_corridor(
    *,
    source_frame: int,
    snapshot_frame: int,
    forecast_lead_frames: int,
    player_x: float,
    player_y: float,
    bullets: tuple[SlottedHazard, ...],
    lasers: tuple[SlottedHazard, ...],
    enemy_bodies: tuple[PointerHazard, ...],
    snapshot_lag: int,
    control_delay_candidates: tuple[int, ...],
    nominal_control_delay: int,
    active_action: str,
    observed_control_delay_candidates: tuple[int, ...] | None = None,
    safety_value_horizon_frames: int = 0,
    required_gate_lane: str | None = None,
    context_key: tuple[int, int, int | None] | None = None,
    audit_capsule_dir: Path | None = None,
    audit_executor: ThreadPoolExecutor | None = None,
    pipeline_prewarm_shadow: bool = False,
    background_low_priority: bool = False,
    native_viability_worker_limit: int | None = None,
) -> CorridorSolution:
    if (
        native_viability_worker_limit is not None
        and not 1 <= native_viability_worker_limit <= 4
    ):
        raise ValueError("native viability worker limit must be 1..4")
    background_priority_lowered = (
        lower_current_thread_priority()
        if background_low_priority
        else False
    )
    native_worker_limit_applied = (
        native_backend.set_current_thread_viability_worker_limit(
            native_viability_worker_limit
        )
        if native_viability_worker_limit is not None
        else False
    )
    started = time.perf_counter()
    hazards = lower_th08_corridor_hazards(
        bullets=bullets,
        lasers=lasers,
        enemy_bodies=enemy_bodies,
        snapshot_lag=snapshot_lag,
        forecast_frames=forecast_lead_frames,
        horizon_frames=TH08_CORRIDOR_CONFIG.horizon_frames,
    )
    prewarm_service = None
    prewarm_start_error: str | None = None
    policy_version = (
        source_frame,
        snapshot_frame,
        context_key,
    )

    try:
        prepared_problem = prepare_lowered_th08_corridor(
            hazards=hazards,
            control_delay_candidates=control_delay_candidates,
            nominal_control_delay=nominal_control_delay,
            active_action=active_action,
            safety_value_horizon_frames=safety_value_horizon_frames,
            survival_labels=LIVE_SURVIVAL_LABELS,
            retain_query_survival_problem=True,
            refinement_grid_steps=LIVE_REFINEMENT_GRID_STEPS,
        )
        prewarm_elapsed_ms = 0.0
        if pipeline_prewarm_shadow:
            assert prepared_problem.survival_query_problem is not None
            prewarm_start = start_corridor_pipeline_prewarm(
                problem=prepared_problem.survival_query_problem,
                player_x=player_x,
                player_y=player_y,
                active_action=active_action,
                policy_version=policy_version,
            )
            prewarm_service = prewarm_start.service
            prewarm_start_error = prewarm_start.error
            prewarm_elapsed_ms = prewarm_start.elapsed_ms
        plan = plan_prepared_lowered_th08_corridor(
            player_x=player_x,
            player_y=player_y,
            prepared_problem=prepared_problem,
            required_gate_lane=required_gate_lane,
            pre_viability_elapsed_ms=prewarm_elapsed_ms,
        )
    except BaseException:
        if prewarm_service is not None:
            prewarm_service.close()
        raise
    constraint_honored = (
        required_gate_lane is None
        or (plan.reachable and plan.lane == required_gate_lane)
    )
    solve_finished = time.perf_counter()
    audit = submit_corridor_audit(
        audit_capsule_dir=audit_capsule_dir,
        audit_executor=audit_executor,
        source_frame=source_frame,
        snapshot_frame=snapshot_frame,
        forecast_lead_frames=forecast_lead_frames,
        player_x=player_x,
        player_y=player_y,
        snapshot_lag=snapshot_lag,
        control_delay_candidates=control_delay_candidates,
        observed_control_delay_candidates=(
            observed_control_delay_candidates
        ),
        nominal_control_delay=nominal_control_delay,
        active_action=active_action,
        required_gate_lane=required_gate_lane,
        context_key=context_key,
        grid_step=TH08_CORRIDOR_CONFIG.grid_step,
        frames_per_layer=TH08_CORRIDOR_CONFIG.frames_per_layer,
        horizon_frames=TH08_CORRIDOR_CONFIG.horizon_frames,
        bullet_slots=tuple(bullet.slot for bullet in bullets),
        laser_slots=tuple(laser.slot for laser in lasers),
        enemy_pointers=tuple(
            body.pointer for body in enemy_bodies
        ),
        plan_reachable=plan.reachable,
        hazards=hazards,
    )
    return CorridorSolution(
        artifact=CorridorPolicyArtifact(
            source_frame=source_frame,
            plan=plan,
            solve_ms=(solve_finished - started) * 1000.0,
            snapshot_frame=snapshot_frame,
            forecast_lead_frames=forecast_lead_frames,
            required_gate_lane=required_gate_lane,
            constraint_honored=constraint_honored,
            context_key=context_key,
            worker_ms=(time.perf_counter() - started) * 1000.0,
            background_priority_lowered=(
                background_priority_lowered
            ),
            native_viability_worker_limit=(
                native_viability_worker_limit
            ),
            native_viability_worker_limit_applied=(
                native_worker_limit_applied
            ),
        ),
        publication=CorridorPublication(
            audit_capsule=audit.capsule,
            audit_write_ms=audit.write_ms,
            audit_error=audit.error,
            pipeline_prewarm_start_error=(
                prewarm_start_error
            ),
        ),
        handles=CorridorRuntimeHandles(
            audit_future=audit.future,
            pipeline_prewarm_service=prewarm_service,
        ),
    )


def corridor_target(
    solution: CorridorSolution | None,
    *,
    current_frame: int,
    lookahead_frames: int,
    max_age_frames: int,
) -> tuple[float, float, int] | None:
    if solution is None or not solution.plan.reachable:
        return None
    age = current_frame - solution.source_frame
    if age < 0 or age > max_age_frames:
        return None
    waypoint = solution.plan.waypoint(age + lookahead_frames)
    return waypoint.x, waypoint.y, max(waypoint.frame - age, 0)


def corridor_viability_query(
    solution: CorridorSolution | None,
    *,
    current_frame: int,
    player_x: float,
    player_y: float,
    active_action: str,
    max_age_frames: int,
) -> ViabilityQuery | None:
    if solution is None or solution.plan.viability_policy is None:
        return None
    age = current_frame - solution.source_frame
    if age < 0 or age > max_age_frames:
        return None
    query = solution.plan.viability_policy.query(
        frame=age,
        x=player_x,
        y=player_y,
        active_action=active_action,
    )
    survival_policy = solution.plan.survival_policy
    if (
        query.available
        and not query.state_viable
        and not query.survival_best_actions
        and survival_policy is not None
        and survival_policy is not solution.plan.viability_policy
    ):
        survival_query = survival_policy.query(
            frame=age,
            x=player_x,
            y=player_y,
            active_action=active_action,
        )
        if survival_query.available:
            query = replace(
                query,
                survival_frames=survival_query.survival_frames,
                survival_bottleneck_margin=(
                    survival_query.survival_bottleneck_margin
                ),
                survival_best_actions=(
                    survival_query.survival_best_actions
                ),
            )
    return query


def solve_postpublished_survival(
    solution: CorridorSolution,
) -> CorridorSolution:
    """Build dense survival labels only after the Boolean solution exists."""

    problem = solution.plan.survival_query_problem
    policy = solution.plan.viability_policy
    if problem is None or policy is None:
        return solution.with_publication(
            postpublished_survival_parity=False,
        )
    started = time.perf_counter()
    survival = problem.build_postpublished_policy(policy, worker_count=1)
    parity = (
        bool((survival.viable == policy.viable).all())
        and bool(
            (
                survival.safe_action_masks
                == policy.safe_action_masks
            ).all()
        )
    )
    return solution.with_publication(
        postpublished_survival_policy=survival,
        postpublished_survival_ms=(
            (time.perf_counter() - started) * 1000.0
        ),
        postpublished_survival_parity=parity,
    )


def corridor_postpublished_survival_query(
    solution: CorridorSolution | None,
    *,
    current_frame: int,
    player_x: float,
    player_y: float,
    observed_action: str,
    max_age_frames: int,
) -> ViabilityQuery | None:
    """Query shadow labels without attaching them to live policy guidance."""

    if solution is None or solution.postpublished_survival_policy is None:
        return None
    age = current_frame - solution.source_frame
    if age < 0 or age > max_age_frames:
        return None
    return solution.postpublished_survival_policy.query(
        frame=age,
        x=player_x,
        y=player_y,
        active_action=observed_action,
    )


def _pipeline_policy_version(
    solution: CorridorSolution,
) -> tuple[
    int,
    int | None,
    tuple[int, int, int | None] | None,
]:
    return (
        solution.source_frame,
        solution.snapshot_frame,
        solution.context_key,
    )


def corridor_candidate_verifier_target(
    solution: CorridorSolution | None,
    *,
    current_frame: int,
    player_x: float,
    player_y: float,
    observed_action: str,
    pending_command: PendingCommand | None,
    max_age_frames: int,
    horizon_frames: int,
) -> tuple[SurvivalQueryProblem, CandidateVerifierTarget] | None:
    """Construct one exact current root after Boolean publication."""

    if solution is None or solution.plan.survival_query_problem is None:
        return None
    problem = solution.plan.survival_query_problem
    age = current_frame - solution.source_frame
    if (
        age < 0
        or age > max_age_frames
        or age + horizon_frames > problem.horizon_frames
    ):
        return None
    row, column, _ = problem.project_to_lattice(
        x=player_x,
        y=player_y,
    )
    return (
        problem,
        CandidateVerifierTarget(
            policy_version=_pipeline_policy_version(solution),
            root=ReachablePipelineRoot(
                frame=age,
                row=row,
                column=column,
                observed_action=observed_action,
                pending_command=pending_command,
            ),
        ),
    )


def prepare_pipeline_survival_workspace(
    solution: CorridorSolution,
) -> CorridorSolution:
    """Attach a versioned exact-phase workspace without querying it."""

    if (
        solution.pipeline_survival_workspace is not None
        and not solution.pipeline_survival_workspace.closed
    ):
        return solution
    problem = solution.plan.survival_query_problem
    if problem is None:
        return solution
    started = time.perf_counter()
    workspace = problem.build_pipeline_workspace(
        policy_version=_pipeline_policy_version(solution),
    )
    return solution.with_handles(
        pipeline_survival_workspace=workspace,
    ).with_publication(
        pipeline_survival_workspace_ms=(
            (time.perf_counter() - started) * 1000.0
        ),
    )


def corridor_pipeline_survival_query(
    solution: CorridorSolution | None,
    *,
    current_frame: int,
    player_x: float,
    player_y: float,
    observed_action: str,
    pending_command: PendingCommand | None,
    max_age_frames: int,
) -> QueryLocalSurvivalResult | None:
    """Run an exact shadow query, with stale versions returning no result.

    This call may expand a cold reachable tube.  Live orchestration must run
    it on the isolated survival executor until a warm-deadline gate passes.
    """

    if solution is None or solution.pipeline_survival_workspace is None:
        return None
    age = current_frame - solution.source_frame
    if age < 0 or age > max_age_frames:
        return None
    try:
        return solution.pipeline_survival_workspace.query(
            policy_version=_pipeline_policy_version(solution),
            frame=age,
            x=player_x,
            y=player_y,
            observed_action=observed_action,
            pending_command=pending_command,
        )
    except StalePipelineWorkspaceError:
        return None


def close_pipeline_prewarm(
    solution: CorridorSolution | None,
) -> None:
    """Cancel and join one solution's shadow service, if present."""

    close_pipeline_prewarm_owner(solution)


def close_retired_pipeline_prewarms(
    candidates: tuple[CorridorSolution | None, ...],
    retained: tuple[CorridorSolution | None, ...] = (),
) -> None:
    """Close candidate services that are not shared by retained solutions."""

    close_retired_pipeline_prewarm_owners(candidates, retained)


def corridor_safety_value_query(
    solution: CorridorSolution | None,
    *,
    current_frame: int,
    player_x: float,
    player_y: float,
    active_action: str,
    max_age_frames: int,
) -> SafetyValueQuery | None:
    if solution is None or solution.plan.safety_value_policy is None:
        return None
    age = current_frame - solution.source_frame
    if age < 0 or age > max_age_frames:
        return None
    return solution.plan.safety_value_policy.query(
        frame=age,
        x=player_x,
        y=player_y,
        active_action=active_action,
    )


def corridor_policy_status(
    solution: CorridorSolution | None,
    *,
    current_frame: int,
    max_age_frames: int,
) -> str:
    if solution is None or solution.plan.viability_policy is None:
        return "unavailable"
    age = current_frame - solution.source_frame
    if age < 0:
        return "pending_future_epoch"
    if age > max_age_frames:
        return "expired"
    if age >= solution.plan.viability_policy.horizon_frames:
        return "outside_policy_horizon"
    return "queryable"


def stage_corridor_solution(
    active: CorridorSolution | None,
    candidate: CorridorSolution,
    *,
    current_frame: int,
    context_key: tuple[int, int, int | None],
) -> tuple[CorridorSolution | None, CorridorSolution | None]:
    """Keep the active policy until a matching future epoch is reached."""

    if candidate.context_key != context_key:
        return active, None
    if candidate.source_frame <= current_frame:
        return candidate, None
    return active, candidate


def corridor_submit_due(
    *,
    current_frame: int,
    last_submit_frame: int,
    interval_frames: int,
) -> bool:
    return current_frame - last_submit_frame >= interval_frames


__all__ = [
    "CorridorCommitment",
    "CorridorPolicyArtifact",
    "CorridorPublication",
    "CorridorRuntimeHandles",
    "CorridorSolution",
    "LIVE_REFINEMENT_GRID_STEPS",
    "LIVE_SURVIVAL_LABELS",
    "PIPELINE_PREWARM_DECISION_FRAMES",
    "PIPELINE_PREWARM_INITIAL_ROOT_FRAMES",
    "PIPELINE_PREWARM_SCHEDULE_FRAMES",
    "PIPELINE_PREWARM_SCHEDULE_ROOT_LIMIT",
    "PIPELINE_PREWARM_WORKER_COUNT",
    "SHADOW_REFINEMENT_GRID_STEPS",
    "SHADOW_SURVIVAL_LABELS",
    "PipelinePrewarmRetarget",
    "PipelinePrewarmShadowQuery",
    "close_pipeline_prewarm",
    "close_retired_pipeline_prewarms",
    "corridor_candidate_verifier_target",
    "corridor_pipeline_prewarm_query",
    "corridor_pipeline_prewarm_retarget",
    "corridor_pipeline_survival_query",
    "corridor_policy_status",
    "corridor_postpublished_survival_query",
    "corridor_safety_value_query",
    "corridor_submit_due",
    "corridor_target",
    "corridor_viability_query",
    "prepare_pipeline_survival_workspace",
    "solve_corridor",
    "solve_postpublished_survival",
    "stage_corridor_solution",
]
