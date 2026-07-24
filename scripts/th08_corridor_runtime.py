#!/usr/bin/env python3
"""Asynchronous TH08 corridor-policy runtime.

This module owns policy epochs, corridor commitments, capsule publication, and
optional shadow-policy queries.  The live agent should only coordinate these
results with its local issue-time controller.
"""

from __future__ import annotations

import time
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Protocol

from corridor_planner import CorridorPlan
from th08_corridor_adapter import (
    LoweredCorridorHazards,
    TH08_CORRIDOR_CONFIG,
    lower_th08_corridor_hazards,
    plan_lowered_th08_corridor,
)
from touhou_control.viability import SafetyValueQuery, ViabilityQuery
from touhou_control.viability_audit_capsule import (
    write_viability_audit_capsule,
)


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


@dataclass(frozen=True)
class CorridorSolution:
    source_frame: int
    plan: CorridorPlan
    solve_ms: float
    snapshot_frame: int | None = None
    forecast_lead_frames: int = 0
    required_gate_lane: str | None = None
    constraint_honored: bool = False
    context_key: tuple[int, int, int | None] | None = None
    audit_capsule: str | None = None
    audit_write_ms: float | None = None
    audit_error: str | None = None
    worker_ms: float | None = None
    audit_future: Future[tuple[float, str | None]] | None = None


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


def _write_corridor_audit_capsule(
    *,
    capsule_path: Path,
    metadata: dict[str, object],
    hazards: LoweredCorridorHazards,
) -> tuple[float, str | None]:
    """Write one diagnostic capsule without delaying policy publication."""

    started = time.perf_counter()
    error_text = None
    try:
        write_viability_audit_capsule(
            capsule_path,
            metadata=metadata,
            aabbs=hazards.aabbs,
            piecewise_aabbs=hazards.piecewise_aabbs,
            segment_trajectories=hazards.segment_trajectories,
            packed_segments=hazards.packed_segments,
        )
    except Exception as error:
        error_text = f"{type(error).__name__}: {error}"
    return (time.perf_counter() - started) * 1000.0, error_text


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
    safety_value_horizon_frames: int = 0,
    required_gate_lane: str | None = None,
    context_key: tuple[int, int, int | None] | None = None,
    audit_capsule_dir: Path | None = None,
    audit_executor: ThreadPoolExecutor | None = None,
) -> CorridorSolution:
    started = time.perf_counter()
    hazards = lower_th08_corridor_hazards(
        bullets=bullets,
        lasers=lasers,
        enemy_bodies=enemy_bodies,
        snapshot_lag=snapshot_lag,
        forecast_frames=forecast_lead_frames,
        horizon_frames=TH08_CORRIDOR_CONFIG.horizon_frames,
    )
    plan = plan_lowered_th08_corridor(
        player_x=player_x,
        player_y=player_y,
        hazards=hazards,
        required_gate_lane=required_gate_lane,
        control_delay_candidates=control_delay_candidates,
        nominal_control_delay=nominal_control_delay,
        active_action=active_action,
        safety_value_horizon_frames=safety_value_horizon_frames,
        survival_labels=LIVE_SURVIVAL_LABELS,
        refinement_grid_steps=LIVE_REFINEMENT_GRID_STEPS,
    )
    constraint_honored = (
        required_gate_lane is None
        or (plan.reachable and plan.lane == required_gate_lane)
    )
    solve_finished = time.perf_counter()
    audit_capsule = None
    audit_write_ms = None
    audit_error = None
    audit_future = None
    if audit_capsule_dir is not None:
        capsule_path = audit_capsule_dir / (
            f"policy_{snapshot_frame}_{source_frame}.npz"
        )
        metadata = {
            "source_frame": source_frame,
            "snapshot_frame": snapshot_frame,
            "forecast_lead_frames": forecast_lead_frames,
            "player_x": player_x,
            "player_y": player_y,
            "snapshot_lag": snapshot_lag,
            "control_delay_candidates": control_delay_candidates,
            "nominal_control_delay": nominal_control_delay,
            "active_action": active_action,
            "required_gate_lane": required_gate_lane,
            "context_key": context_key,
            "grid_step": TH08_CORRIDOR_CONFIG.grid_step,
            "frames_per_layer": TH08_CORRIDOR_CONFIG.frames_per_layer,
            "horizon_frames": TH08_CORRIDOR_CONFIG.horizon_frames,
            "bullet_slots": [bullet.slot for bullet in bullets],
            "laser_slots": [laser.slot for laser in lasers],
            "enemy_pointers": [body.pointer for body in enemy_bodies],
            "plan_reachable": plan.reachable,
        }
        writer_arguments = {
            "capsule_path": capsule_path,
            "metadata": metadata,
            "hazards": hazards,
        }
        if audit_executor is None:
            audit_write_ms, audit_error = (
                _write_corridor_audit_capsule(**writer_arguments)
            )
        else:
            audit_future = audit_executor.submit(
                _write_corridor_audit_capsule,
                **writer_arguments,
            )
        audit_capsule = str(capsule_path)
    return CorridorSolution(
        source_frame=source_frame,
        plan=plan,
        solve_ms=(solve_finished - started) * 1000.0,
        snapshot_frame=snapshot_frame,
        forecast_lead_frames=forecast_lead_frames,
        required_gate_lane=required_gate_lane,
        constraint_honored=constraint_honored,
        context_key=context_key,
        audit_capsule=audit_capsule,
        audit_write_ms=audit_write_ms,
        audit_error=audit_error,
        worker_ms=(time.perf_counter() - started) * 1000.0,
        audit_future=audit_future,
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
    "CorridorSolution",
    "LIVE_REFINEMENT_GRID_STEPS",
    "LIVE_SURVIVAL_LABELS",
    "SHADOW_REFINEMENT_GRID_STEPS",
    "SHADOW_SURVIVAL_LABELS",
    "corridor_policy_status",
    "corridor_safety_value_query",
    "corridor_submit_due",
    "corridor_target",
    "corridor_viability_query",
    "solve_corridor",
    "stage_corridor_solution",
]
