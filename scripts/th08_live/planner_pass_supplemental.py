"""Supplemental-lane lifecycle for one live local-planner pass."""

from __future__ import annotations

import functools
import math
import time
from dataclasses import dataclass, replace
from typing import Any

import numpy as np

from th08_local_planner import CompletedSupplementalLookup, SearchNode
from th08_live.planner_pass_baseline import BaselineStagePreparation
from th08_live.planner_pass_types import (
    LocalCertificateTimingAccumulator,
)
from touhou_control import native_backend
from touhou_control.supplemental_local_beam import (
    SupplementalAction,
    SupplementalNode,
)


@dataclass(frozen=True)
class NativeBodyArrays:
    base_x: np.ndarray
    base_y: np.ndarray
    velocity_x: np.ndarray
    velocity_y: np.ndarray
    half_width: np.ndarray
    half_height: np.ndarray


@dataclass(frozen=True)
class SupplementalSubmission:
    identity: tuple[object, ...] | None


@dataclass(frozen=True)
class SupplementalStageResult:
    baseline_beam: tuple[SearchNode, ...]
    supplemental_beam: tuple[SearchNode, ...]
    terminal_threats: dict[SearchNode, tuple[int, float]]
    supplemental_source_ids: frozenset[int]
    continuation_preference_active: bool
    supplemental_beam_active: bool
    failure: str | None
    status: str
    completed: bool
    historical_fallback: bool
    background_compute_ms: float | None


def _supplemental_actions(
    stage: BaselineStagePreparation,
) -> tuple[SupplementalAction, ...]:
    return tuple(
        SupplementalAction(
            name=action.name,
            direction=action.direction,
            dx=action.dx,
            dy=action.dy,
            focused=action.focused,
        )
        for action in stage.dependencies.planner_actions
    )


def _native_body_arrays(
    enemy_bodies: tuple[Any, ...],
) -> NativeBodyArrays:
    return NativeBodyArrays(
        base_x=np.fromiter(
            (body.x for body in enemy_bodies),
            dtype=np.float32,
            count=len(enemy_bodies),
        ),
        base_y=np.fromiter(
            (body.y for body in enemy_bodies),
            dtype=np.float32,
            count=len(enemy_bodies),
        ),
        velocity_x=np.fromiter(
            (body.vx for body in enemy_bodies),
            dtype=np.float32,
            count=len(enemy_bodies),
        ),
        velocity_y=np.fromiter(
            (body.vy for body in enemy_bodies),
            dtype=np.float32,
            count=len(enemy_bodies),
        ),
        half_width=np.fromiter(
            (
                body.half_width + body.uncertainty
                for body in enemy_bodies
            ),
            dtype=np.float32,
            count=len(enemy_bodies),
        ),
        half_height=np.fromiter(
            (
                body.half_height + body.uncertainty
                for body in enemy_bodies
            ),
            dtype=np.float32,
            count=len(enemy_bodies),
        ),
    )


def _supplemental_identity(
    stage: BaselineStagePreparation,
    *,
    player_x: float,
    player_y: float,
) -> tuple[object, ...]:
    request = stage.request
    actuator = request.actuator
    guidance = request.guidance
    config = request.config
    completed = request.completed_services
    return (
        completed.supplemental_version,
        actuator.local_pipeline_root,
        float(player_x).hex(),
        float(player_y).hex(),
        actuator.previous_direction,
        actuator.previous_focus,
        actuator.control_delay_frames,
        actuator.control_delay_candidates,
        actuator.action_hold_frames,
        config.horizon,
        config.preloss_supplemental_beam_width,
        config.beam_dedup_mode,
        guidance.target_x,
        guidance.target_y,
        stage.planner_preparation.validated.target_deadline,
        tuple(
            stage.planner_preparation.preflight
            .effective_allowed_first_actions
            or ()
        ),
        tuple(guidance.viability_repair_volumes),
        tuple(guidance.viability_recovery_distances),
        tuple(guidance.viability_safety_actions),
        tuple(guidance.viability_survival_actions),
    )


def _repair_volume(
    stage: BaselineStagePreparation,
) -> np.ndarray:
    repair_by_action = stage.planner_preparation.validated.repair_by_action
    actions = stage.dependencies.planner_actions
    return np.fromiter(
        (repair_by_action.get(action.name, 0) for action in actions),
        dtype=np.int32,
        count=len(actions),
    )


def _native_job(
    stage: BaselineStagePreparation,
    *,
    initial_node: SearchNode,
    bullet_frames: tuple[Any, ...] | list[Any],
    laser_frames: tuple[Any, ...] | list[Any],
    supplemental_reserve_distance: float,
    absolute_deadline_ns: int | None,
    certificate_collisions: np.ndarray,
    certificate_minimum: np.ndarray,
    survival_preferred: np.ndarray,
    safety_preferred: np.ndarray,
    recovery_distance: np.ndarray,
    repair_volume: np.ndarray,
) -> functools.partial[Any]:
    request = stage.request
    actuator = request.actuator
    guidance = request.guidance
    config = request.config
    prepared = stage.planner_preparation.hazards
    validated = stage.planner_preparation.validated
    dependencies = stage.dependencies
    actions = _supplemental_actions(stage)
    bodies = _native_body_arrays(request.physical.enemy_bodies)
    return functools.partial(
        dependencies.search_supplemental_local_beam_native,
        initial=SupplementalNode(
            x=initial_node.x,
            y=initial_node.y,
            first_action=0,
            last_action=0,
            risk=initial_node.risk,
            collisions=initial_node.collisions,
            min_clearance=initial_node.min_clearance,
            immediate_clearance=initial_node.immediate_clearance,
        ),
        actions=actions,
        allowed_first_actions=frozenset(
            stage.planner_preparation.preflight
            .effective_allowed_first_actions
            or ()
        ),
        action_hold_frames=actuator.action_hold_frames,
        horizon=config.horizon,
        beam_width=config.preloss_supplemental_beam_width,
        bullet_frames=bullet_frames[: config.horizon],
        laser_frames=tuple(
            frame.fields_for_native()
            for frame in laser_frames[: config.horizon]
        ),
        body_base_x=bodies.base_x,
        body_base_y=bodies.base_y,
        body_velocity_x=bodies.velocity_x,
        body_velocity_y=bodies.velocity_y,
        body_half_width=bodies.half_width,
        body_half_height=bodies.half_height,
        player_radius=dependencies.player_radius,
        control_delay_frames=actuator.control_delay_frames,
        previous_direction=actuator.previous_direction,
        previous_focused=actuator.previous_focus,
        preserve_previous_direction_inertia=(
            config.preserve_previous_direction_inertia
        ),
        target_x=guidance.target_x,
        target_y=guidance.target_y,
        target_deadline=validated.target_deadline,
        item_safety_clearance=dependencies.item_safety_clearance,
        playfield_left=dependencies.playfield_left,
        playfield_right=dependencies.playfield_right,
        playfield_top=dependencies.playfield_top,
        playfield_bottom=dependencies.playfield_bottom,
        recovery_reserve_distance=prepared.recovery_reserve_distance,
        supplemental_reserve_distance=supplemental_reserve_distance,
        diagonal_speed=dependencies.unfocused_diagonal_speed,
        cardinal_speed=dependencies.unfocused_cardinal_speed,
        certificate_collisions=certificate_collisions,
        certificate_minimum=certificate_minimum,
        survival_preferred=survival_preferred,
        safety_preferred=safety_preferred,
        recovery_distance=recovery_distance,
        repair_volume=repair_volume,
        absolute_deadline_ns=absolute_deadline_ns,
    )


def presubmit_supplemental_stage(
    stage: BaselineStagePreparation,
    *,
    active: bool,
    initial_node: SearchNode,
    bullet_frames: tuple[Any, ...] | list[Any],
    laser_frames: tuple[Any, ...] | list[Any],
    supplemental_reserve_distance: float,
    timing: LocalCertificateTimingAccumulator,
) -> SupplementalSubmission:
    """Submit eligible native work before the historical baseline starts."""

    completed = stage.request.completed_services
    service = completed.supplemental_async_service
    if not (
        active
        and service is not None
        and stage.dependencies.local_supplemental_backend == "native"
        and stage.native_beam_enabled
    ):
        return SupplementalSubmission(identity=None)
    started_ns = time.perf_counter_ns()
    deadline_ms = completed.supplemental_deadline_ms
    absolute_deadline_ns = (
        None
        if deadline_ms is None
        else started_ns + int(deadline_ms * 1_000_000.0)
    )
    job = _native_job(
        stage,
        initial_node=initial_node,
        bullet_frames=bullet_frames,
        laser_frames=laser_frames,
        supplemental_reserve_distance=supplemental_reserve_distance,
        absolute_deadline_ns=absolute_deadline_ns,
        certificate_collisions=stage.native_certificate_collisions,
        certificate_minimum=stage.native_certificate_minimum,
        survival_preferred=stage.native_survival_preferred,
        safety_preferred=stage.native_safety_preferred,
        recovery_distance=stage.native_recovery_distance,
        repair_volume=_repair_volume(stage),
    )
    identity = _supplemental_identity(
        stage,
        player_x=initial_node.x,
        player_y=initial_node.y,
    )
    service.submit(
        identity,
        lambda workspace: job(workspace=workspace),
    )
    time.sleep(0)
    timing.supplemental_beam_ms += (
        time.perf_counter_ns() - started_ns
    ) / 1_000_000.0
    return SupplementalSubmission(identity=identity)


def _run_direct_supplemental(
    stage: BaselineStagePreparation,
    *,
    initial_node: SearchNode,
    bullet_frames: tuple[Any, ...] | list[Any],
    laser_frames: tuple[Any, ...] | list[Any],
    supplemental_reserve_distance: float,
    deadline_ns: int | None,
) -> tuple[list[SupplementalNode], tuple[object, ...] | None, str]:
    request = stage.request
    actuator = request.actuator
    guidance = request.guidance
    config = request.config
    completed = request.completed_services
    prepared = stage.planner_preparation.hazards
    validated = stage.planner_preparation.validated
    dependencies = stage.dependencies
    actions = _supplemental_actions(stage)
    initial = SupplementalNode(
        x=initial_node.x,
        y=initial_node.y,
        first_action=0,
        last_action=0,
        risk=initial_node.risk,
        collisions=initial_node.collisions,
        min_clearance=initial_node.min_clearance,
        immediate_clearance=initial_node.immediate_clearance,
    )
    robust_certificates = stage.planner_preparation.preflight.certificates
    planner_actions = dependencies.planner_actions
    certificate_collisions = np.fromiter(
        (
            robust_certificates[action.name].worst_collisions
            if action.name in robust_certificates
            else 0
            for action in planner_actions
        ),
        dtype=np.int32,
        count=len(planner_actions),
    )
    certificate_minimum = np.fromiter(
        (
            robust_certificates[action.name].min_clearance
            if action.name in robust_certificates
            else 0.0
            for action in planner_actions
        ),
        dtype=np.float64,
        count=len(planner_actions),
    )
    survival_preferred = np.fromiter(
        (
            not validated.survival_actions
            or action.name in validated.survival_actions
            for action in planner_actions
        ),
        dtype=np.uint8,
        count=len(planner_actions),
    )
    safety_preferred = np.fromiter(
        (
            not validated.safety_value_actions
            or action.name in validated.safety_value_actions
            for action in planner_actions
        ),
        dtype=np.uint8,
        count=len(planner_actions),
    )
    recovery_distance = np.fromiter(
        (
            validated.recovery_by_action.get(action.name, math.inf)
            for action in planner_actions
        ),
        dtype=np.float64,
        count=len(planner_actions),
    )
    repair_volume = _repair_volume(stage)

    if (
        dependencies.local_supplemental_backend == "native"
        and config.beam_dedup_mode == "quantized"
    ):
        job = _native_job(
            stage,
            initial_node=initial_node,
            bullet_frames=bullet_frames,
            laser_frames=laser_frames,
            supplemental_reserve_distance=supplemental_reserve_distance,
            absolute_deadline_ns=deadline_ns,
            certificate_collisions=certificate_collisions,
            certificate_minimum=certificate_minimum,
            survival_preferred=survival_preferred,
            safety_preferred=safety_preferred,
            recovery_distance=recovery_distance,
            repair_volume=repair_volume,
        )
        service = completed.supplemental_async_service
        if service is not None:
            identity = _supplemental_identity(
                stage,
                player_x=initial_node.x,
                player_y=initial_node.y,
            )
            service.submit(
                identity,
                lambda workspace: job(workspace=workspace),
            )
            time.sleep(0)
            return [], identity, "async_submitted"
        return list(job()), None, "completed"

    def transition_risk(
        node: SupplementalNode,
        action: SupplementalAction,
        x: float,
        y: float,
        step: int,
    ) -> float:
        last_action = actions[node.last_action]
        risk = dependencies.boundary_risk(x, y)
        if action.direction != last_action.direction:
            risk += 0.08
        if dependencies.directions_opposed(
            action.direction,
            last_action.direction,
        ):
            risk += 24.0
        if action.focused != last_action.focused:
            risk += 0.12
        if step == 1 and config.preserve_previous_direction_inertia:
            if action.direction != actuator.previous_direction:
                risk += 0.08
            if dependencies.directions_opposed(
                action.direction,
                actuator.previous_direction,
            ):
                risk += 24.0
            if action.focused != actuator.previous_focus:
                risk += 0.12
        return risk

    def hazard_query(
        positions_x: np.ndarray,
        positions_y: np.ndarray,
        absolute_step: int,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        local_step = absolute_step - actuator.control_delay_frames
        return dependencies.hazards_for_positions(
            positions_x,
            positions_y,
            step=absolute_step,
            bullet_frame=bullet_frames[local_step - 1],
            lasers=laser_frames[local_step - 1],
            enemy_bodies=request.physical.enemy_bodies,
        )

    nodes = dependencies.search_supplemental_local_beam(
        initial=initial,
        actions=actions,
        allowed_first_actions=frozenset(
            stage.planner_preparation.preflight
            .effective_allowed_first_actions
            or ()
        ),
        action_hold_frames=actuator.action_hold_frames,
        horizon=config.horizon,
        beam_width=config.preloss_supplemental_beam_width,
        beam_dedup_mode=config.beam_dedup_mode,
        hazard_query=hazard_query,
        transition_risk=transition_risk,
        control_delay_frames=actuator.control_delay_frames,
        target_x=guidance.target_x,
        target_y=guidance.target_y,
        target_deadline=validated.target_deadline,
        item_safety_clearance=dependencies.item_safety_clearance,
        playfield_left=dependencies.playfield_left,
        playfield_right=dependencies.playfield_right,
        playfield_top=dependencies.playfield_top,
        playfield_bottom=dependencies.playfield_bottom,
        recovery_reserve_distance=prepared.recovery_reserve_distance,
        supplemental_reserve_distance=supplemental_reserve_distance,
        diagonal_speed=dependencies.unfocused_diagonal_speed,
        cardinal_speed=dependencies.unfocused_cardinal_speed,
        certificate_collisions=certificate_collisions,
        certificate_minimum=certificate_minimum,
        survival_preferred=survival_preferred,
        safety_preferred=safety_preferred,
        recovery_distance=recovery_distance,
        repair_volume=repair_volume,
        use_native_reducer=stage.native_beam_enabled,
    )
    return list(nodes), None, "completed"


def _position_costed(
    nodes: list[SearchNode],
    *,
    target_x: float | None,
    target_y: float | None,
) -> list[SearchNode]:
    result: list[SearchNode] = []
    for node in nodes:
        if target_x is None or target_y is None:
            position_cost = (
                ((node.x - 192.0) / 96.0) ** 2
                + ((node.y - 400.0) / 128.0) ** 2
            )
        else:
            position_cost = 0.25 * (
                ((node.x - target_x) / 8.0) ** 2
                + ((node.y - target_y) / 8.0) ** 2
            )
        result.append(replace(node, risk=node.risk + position_cost))
    return result


def run_supplemental_stage(
    stage: BaselineStagePreparation,
    *,
    submission: SupplementalSubmission,
    baseline_beam: list[SearchNode],
    initial_node: SearchNode,
    bullet_frames: tuple[Any, ...] | list[Any],
    laser_frames: tuple[Any, ...] | list[Any],
    beam_started_ns: int,
    continuation_preference_active: bool,
    supplemental_beam_active: bool,
    supplemental_reserve_distance: float,
    effective_threat_horizon: int,
    timing: LocalCertificateTimingAccumulator,
) -> SupplementalStageResult:
    """Complete supplemental work and terminal labeling without waiting."""

    request = stage.request
    config = request.config
    completed_services = request.completed_services
    dependencies = stage.dependencies
    planner_actions = dependencies.planner_actions
    supplemental_beam: list[SearchNode] = []
    failure: str | None = None
    status = "not_eligible" if not supplemental_beam_active else "pending"
    completed = False
    historical_fallback = False
    async_identity = submission.identity
    background_compute_ms: float | None = None
    published_terminal_labels: tuple[tuple[int, float], ...] | None = None

    if supplemental_beam_active and async_identity is not None:
        status = "async_submitted"
        historical_fallback = True
    elif supplemental_beam_active:
        started_ns = time.perf_counter_ns()
        deadline_ms = completed_services.supplemental_deadline_ms
        deadline_ns = (
            None
            if deadline_ms is None
            else started_ns + int(deadline_ms * 1_000_000.0)
        )
        try:
            lane_nodes, async_identity, status = _run_direct_supplemental(
                stage,
                initial_node=initial_node,
                bullet_frames=bullet_frames,
                laser_frames=laser_frames,
                supplemental_reserve_distance=(
                    supplemental_reserve_distance
                ),
                deadline_ns=deadline_ns,
            )
            if status == "async_submitted":
                historical_fallback = True
            else:
                completed = True
            supplemental_beam = [
                SearchNode(
                    x=node.x,
                    y=node.y,
                    first_action=planner_actions[node.first_action],
                    last_action=planner_actions[node.last_action],
                    risk=node.risk,
                    collisions=node.collisions,
                    min_clearance=node.min_clearance,
                    immediate_clearance=node.immediate_clearance,
                    collected_mask=0,
                    item_utility=0.0,
                )
                for node in lane_nodes
            ]
        except native_backend.LocalSupplementalNativeDeadlineError:
            status = "deadline"
            historical_fallback = True
        except native_backend.LocalSupplementalNativeCancelledError:
            status = "cancelled"
            historical_fallback = True
        except Exception as error:
            status = "error"
            historical_fallback = True
            failure = f"{type(error).__name__}: {error}"
        finally:
            timing.supplemental_beam_ms += (
                time.perf_counter_ns() - started_ns
            ) / 1_000_000.0

    if failure is not None:
        continuation_preference_active = False
        supplemental_beam_active = False

    neutral = planner_actions[0]
    if not baseline_beam:
        baseline_beam = [
            SearchNode(
                initial_node.x,
                initial_node.y,
                neutral,
                neutral,
                1e12,
                1,
                -9999.0,
                -9999.0,
                0,
                0.0,
            )
        ]
    baseline_beam = _position_costed(
        baseline_beam,
        target_x=request.guidance.target_x,
        target_y=request.guidance.target_y,
    )
    source_ids = {id(node) for node in supplemental_beam}
    async_terminal_started_ns: int | None = None
    terminal_threats: dict[SearchNode, tuple[int, float]] = {}
    if async_identity is not None:
        service = completed_services.supplemental_async_service
        assert service is not None
        async_terminal_started_ns = time.perf_counter_ns()
        terminal_threats.update(
            dependencies.terminal_threat_scores(
                baseline_beam,
                start_step=config.horizon,
                end_step=effective_threat_horizon,
                control_delay_frames=(
                    request.actuator.control_delay_frames
                ),
                bullet_frames=bullet_frames,
                laser_frames=laser_frames,
                enemy_bodies=request.physical.enemy_bodies,
            )
        )
        lookup: CompletedSupplementalLookup = (
            dependencies.lookup_completed_supplemental(
                service=service,
                identity=async_identity,
                actions=planner_actions,
            )
        )
        status = lookup.status
        completed = lookup.completed
        historical_fallback = lookup.historical_fallback
        background_compute_ms = lookup.background_compute_ms
        published_terminal_labels = lookup.terminal_labels
        supplemental_beam = list(lookup.beam)

    original_supplemental = supplemental_beam
    supplemental_beam = _position_costed(
        supplemental_beam,
        target_x=request.guidance.target_x,
        target_y=request.guidance.target_y,
    )
    for original, replaced_node in zip(
        original_supplemental,
        supplemental_beam,
    ):
        source_ids.discard(id(original))
        source_ids.add(id(replaced_node))

    if published_terminal_labels is not None:
        if len(published_terminal_labels) != len(supplemental_beam):
            failure = (
                "RuntimeError: async terminal publication count mismatch"
            )
            status = "error"
            completed = False
            historical_fallback = True
            supplemental_beam = []
            source_ids.clear()
        else:
            terminal_threats.update(
                zip(supplemental_beam, published_terminal_labels)
            )

    timing.beam_search_ms += (
        time.perf_counter_ns() - beam_started_ns
    ) / 1_000_000.0
    terminal_started_ns = (
        async_terminal_started_ns
        if async_terminal_started_ns is not None
        else time.perf_counter_ns()
    )
    endpoint_pool = [*baseline_beam, *supplemental_beam]
    if async_terminal_started_ns is None:
        terminal_threats = dependencies.terminal_threat_scores(
            endpoint_pool,
            start_step=config.horizon,
            end_step=effective_threat_horizon,
            control_delay_frames=request.actuator.control_delay_frames,
            bullet_frames=bullet_frames,
            laser_frames=laser_frames,
            enemy_bodies=request.physical.enemy_bodies,
        )
    elif supplemental_beam and published_terminal_labels is None:
        terminal_threats.update(
            dependencies.terminal_threat_scores(
                supplemental_beam,
                start_step=config.horizon,
                end_step=effective_threat_horizon,
                control_delay_frames=(
                    request.actuator.control_delay_frames
                ),
                bullet_frames=bullet_frames,
                laser_frames=laser_frames,
                enemy_bodies=request.physical.enemy_bodies,
            )
        )
    timing.terminal_threat_ms += (
        time.perf_counter_ns() - terminal_started_ns
    ) / 1_000_000.0
    return SupplementalStageResult(
        baseline_beam=tuple(baseline_beam),
        supplemental_beam=tuple(supplemental_beam),
        terminal_threats=terminal_threats,
        supplemental_source_ids=frozenset(source_ids),
        continuation_preference_active=(
            continuation_preference_active
        ),
        supplemental_beam_active=supplemental_beam_active,
        failure=failure,
        status=status,
        completed=completed,
        historical_fallback=historical_fallback,
        background_compute_ms=background_compute_ms,
    )


__all__ = [
    "SupplementalStageResult",
    "SupplementalSubmission",
    "presubmit_supplemental_stage",
    "run_supplemental_stage",
]
