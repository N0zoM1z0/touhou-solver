"""One complete local-planner pass behind an explicit controller boundary."""

from __future__ import annotations

import functools
import math
import time
from dataclasses import replace

import numpy as np

from th08_local_planner import (
    CompletedSupplementalLookup,
    DamageDecisionFields,
    Decision,
    EndpointRanker,
    LocalPlannerRequest,
    ObjectiveContext,
    PlannerAction,
    PlannerMode,
    PlannerPassPreparation,
    ProposalAssemblyContext,
    RobustActionCertificate,
    SearchNode,
    SupplementalDecisionFields,
)
from touhou_control import native_backend
from touhou_control.phase_progress import ProgressCandidate
from touhou_control.supplemental_local_beam import (
    SupplementalAction,
    SupplementalNode,
)
from th08_live.planner_pass_baseline import (
    prepare_baseline_stage,
    run_baseline_stage,
)
from th08_live.planner_pass_types import (
    LocalCertificateTimingAccumulator,
    PlannerModeTransition,
    PlannerPassDependencies,
)


def _run_local_planner_pass(
    request: LocalPlannerRequest,
    preparation: PlannerPassPreparation,
    *,
    dependencies: PlannerPassDependencies,
    _certificate_timing_accumulator: (
        LocalCertificateTimingAccumulator
    ),
) -> Decision | PlannerModeTransition:
    _PlannerModeTransition = PlannerModeTransition
    _PLANNER_ACTIONS = dependencies.planner_actions
    _LOCAL_SUPPLEMENTAL_BACKEND = dependencies.local_supplemental_backend
    BOMB = dependencies.bomb_mask
    FOCUS = dependencies.focus_mask
    SHOT = dependencies.shot_mask
    ITEM_SAFETY_CLEARANCE = dependencies.item_safety_clearance
    PLAYER_RADIUS = dependencies.player_radius
    PLAYFIELD_LEFT = dependencies.playfield_left
    PLAYFIELD_RIGHT = dependencies.playfield_right
    PLAYFIELD_TOP = dependencies.playfield_top
    PLAYFIELD_BOTTOM = dependencies.playfield_bottom
    UNFOCUSED_CARDINAL_SPEED = dependencies.unfocused_cardinal_speed
    UNFOCUSED_DIAGONAL_SPEED = dependencies.unfocused_diagonal_speed
    _boundary_control_reserve_deficit = (
        dependencies.boundary_control_reserve_deficit
    )
    _boundary_risk = dependencies.boundary_risk
    _build_bullet_frames = dependencies.build_bullet_frames
    _control_prefix_hazards = dependencies.control_prefix_hazards
    _directions_opposed = dependencies.directions_opposed
    _hazards_for_positions = dependencies.hazards_for_positions
    _minimum_travel_frames = dependencies.minimum_travel_frames
    _node_key = dependencies.node_key
    _project_player_for_read_lag = (
        dependencies.project_player_for_read_lag
    )
    _robust_action_certificates = dependencies.robust_action_certificates
    _terminal_threat_scores = dependencies.terminal_threat_scores
    assemble_local_decision = dependencies.assemble_local_decision
    lookup_completed_supplemental = (
        dependencies.lookup_completed_supplemental
    )
    select_progress_action = dependencies.select_progress_action
    search_supplemental_local_beam = (
        dependencies.search_supplemental_local_beam
    )
    search_supplemental_local_beam_native = (
        dependencies.search_supplemental_local_beam_native
    )

    physical = request.physical
    actuator = request.actuator
    guidance = request.guidance
    config = request.config
    objective = request.objective
    completed = request.completed_services

    player_x = physical.player_x
    player_y = physical.player_y
    bullets = physical.bullets
    lasers = physical.lasers
    enemy_bodies = physical.enemy_bodies
    snapshot_lag = physical.snapshot_lag

    previous_direction = actuator.previous_direction
    previous_focus = actuator.previous_focus
    local_pipeline_root = actuator.local_pipeline_root
    control_delay_frames = actuator.control_delay_frames
    control_delay_candidates = actuator.control_delay_candidates
    action_hold_frames = actuator.action_hold_frames

    target_x = guidance.target_x
    target_y = guidance.target_y
    target_deadline = guidance.target_deadline
    allowed_first_actions = guidance.allowed_first_actions
    viability_repair_volumes = guidance.viability_repair_volumes
    viability_recovery_distances = (
        guidance.viability_recovery_distances
    )
    viability_safety_actions = guidance.viability_safety_actions
    viability_survival_actions = guidance.viability_survival_actions

    horizon = config.horizon
    preloss_continuation_preference = (
        config.preloss_continuation_preference
    )
    preloss_supplemental_beam_width = (
        config.preloss_supplemental_beam_width
    )
    preserve_previous_direction_inertia = (
        config.preserve_previous_direction_inertia
    )
    beam_dedup_mode = config.beam_dedup_mode
    relax_stale_viability_contradiction = (
        config.relax_stale_viability_contradiction
    )

    power = objective.power
    bombs = objective.bombs
    damage_target_x = objective.damage_target_x
    damage_target_half_width = objective.damage_target_half_width
    damageable = objective.damageable

    preloss_supplemental_deadline_ms = (
        completed.supplemental_deadline_ms
    )
    preloss_supplemental_async_service = (
        completed.supplemental_async_service
    )
    preloss_supplemental_version = completed.supplemental_version
    _viability_retry = (
        request.mode is PlannerMode.RELAXED_VIABILITY
    )

    validated = preparation.validated
    target_deadline = validated.target_deadline
    repair_by_action = validated.repair_by_action
    recovery_by_action = validated.recovery_by_action
    safety_value_actions = validated.safety_value_actions
    survival_actions = validated.survival_actions
    observed_player_x = player_x
    observed_player_y = player_y
    prepared = preparation.hazards
    selected_items = prepared.selected_items
    delayed_mask = prepared.delayed_mask
    main_laser_offset = prepared.main_laser_offset
    diagnostic_losing_reserve_distance = (
        prepared.diagnostic_losing_reserve_distance
    )
    recovery_reserve_distance = prepared.recovery_reserve_distance
    certificate_horizon = prepared.certificate_horizon
    potential_threat_horizon = prepared.potential_threat_horizon
    laser_timeline = prepared.laser_timeline
    preflight = preparation.preflight
    robust_preflight_certificates = preflight.certificates
    viability_constraint_relaxed = (
        preflight.viability_constraint_relaxed
    )
    effective_allowed_first_actions = (
        preflight.effective_allowed_first_actions
    )
    viability_fresh_prefix_relaxed = (
        preflight.viability_fresh_prefix_relaxed
    )
    effective_action_names = set(effective_allowed_first_actions or ())
    preloss_continuation_preference_active = bool(
        preloss_continuation_preference
        and allowed_first_actions is not None
        and effective_action_names
        and not viability_constraint_relaxed
        and not viability_fresh_prefix_relaxed
        and effective_action_names <= repair_by_action.keys()
    )
    preloss_reserve_distance = (
        diagnostic_losing_reserve_distance
        if preloss_continuation_preference_active
        else 0.0
    )
    preloss_supplemental_beam_active = bool(
        preloss_continuation_preference_active
        and preloss_supplemental_beam_width > 0
        and not selected_items
    )
    effective_threat_horizon = potential_threat_horizon
    control_prefix_started_ns = time.perf_counter_ns()
    prefix_risk, prefix_collisions, prefix_clearance = _control_prefix_hazards(
        player_x=player_x,
        player_y=player_y,
        input_mask=delayed_mask,
        bullets=bullets,
        lasers=lasers,
        enemy_bodies=enemy_bodies,
        snapshot_lag=snapshot_lag,
        frames=control_delay_frames,
        laser_frames=laser_timeline[:control_delay_frames],
    )
    _certificate_timing_accumulator.control_prefix_ms += (
        time.perf_counter_ns() - control_prefix_started_ns
    ) / 1_000_000.0
    player_x, player_y = _project_player_for_read_lag(
        player_x,
        player_y,
        delayed_mask,
        control_delay_frames,
    )
    planning_projection_started_ns = time.perf_counter_ns()
    bullet_frames = _build_bullet_frames(
        bullets,
        horizon=effective_threat_horizon,
        snapshot_lag=max(
            0,
            control_delay_frames - max(0, snapshot_lag),
        ),
    )
    _certificate_timing_accumulator.planning_bullet_projection_ms += (
        time.perf_counter_ns() - planning_projection_started_ns
    ) / 1_000_000.0
    laser_frames = laser_timeline[
        main_laser_offset:
        main_laser_offset + effective_threat_horizon
    ]
    if len(laser_frames) < effective_threat_horizon:
        raise RuntimeError(
            "shared laser timeline does not cover local planning horizon"
        )
    neutral = _PLANNER_ACTIONS[0]
    beam = [
        SearchNode(
            player_x,
            player_y,
            neutral,
            neutral,
            prefix_risk,
            prefix_collisions,
            prefix_clearance,
            prefix_clearance,
            0,
            0.0,
        )
    ]
    initial_node = beam[0]

    def pruning_key(
        node: SearchNode,
        *,
        step: int,
    ) -> tuple[object, ...]:
        base = _node_key(
            node,
            step=step,
            selected_items=selected_items,
            target_x=target_x,
            target_y=target_y,
            target_deadline=target_deadline,
        )
        certificate = robust_preflight_certificates.get(
            node.first_action.name
        )
        return (
            base[0],
            (
                certificate.worst_collisions
                if certificate is not None
                else 0
            ),
            (
                max(-certificate.min_clearance, 0.0)
                if certificate is not None
                else 0.0
            ),
            max(-node.min_clearance, 0.0),
            (
                0
                if (
                    not survival_actions
                    or node.first_action.name in survival_actions
                )
                else 1
            ),
            base[1],
            base[2],
            (
                0
                if (
                    not safety_value_actions
                    or node.first_action.name in safety_value_actions
                )
                else 1
            ),
            _boundary_control_reserve_deficit(
                node.x,
                node.y,
                reserve_distance=recovery_reserve_distance,
            ),
            recovery_by_action.get(node.first_action.name, math.inf),
            *base[3:],
        )

    if (
        not bullets
        and not lasers
        and not enemy_bodies
        and not selected_items
        and target_x is None
        and allowed_first_actions is None
        and not repair_by_action
        and not recovery_by_action
        and not safety_value_actions
        and not survival_actions
    ):
        return Decision(
            SHOT | FOCUS,
            "stay",
            9999.0,
            9999.0,
            0.0,
            False,
            robust_delay_frames=control_delay_candidates or (),
            local_certificate_timing=(
                _certificate_timing_accumulator.snapshot()
            ),
        )
    baseline_stage = prepare_baseline_stage(
        request=request,
        planner_preparation=preparation,
        dependencies=dependencies,
    )
    native_beam_enabled = baseline_stage.native_beam_enabled
    native_certificate_collisions = (
        baseline_stage.native_certificate_collisions
    )
    native_certificate_minimum = baseline_stage.native_certificate_minimum
    native_survival_preferred = baseline_stage.native_survival_preferred
    native_safety_preferred = baseline_stage.native_safety_preferred
    native_recovery_distance = baseline_stage.native_recovery_distance
    presubmitted_async_identity: tuple[object, ...] | None = None
    if (
        preloss_supplemental_beam_active
        and preloss_supplemental_async_service is not None
        and _LOCAL_SUPPLEMENTAL_BACKEND == "native"
        and native_beam_enabled
    ):
        async_submit_started_ns = time.perf_counter_ns()
        async_actions = tuple(
            SupplementalAction(
                name=action.name,
                direction=action.direction,
                dx=action.dx,
                dy=action.dy,
                focused=action.focused,
            )
            for action in _PLANNER_ACTIONS
        )
        async_repair_volume = np.fromiter(
            (
                repair_by_action.get(action.name, 0)
                for action in _PLANNER_ACTIONS
            ),
            dtype=np.int32,
            count=len(_PLANNER_ACTIONS),
        )
        body_base_x = np.fromiter(
            (body.x for body in enemy_bodies),
            dtype=np.float32,
            count=len(enemy_bodies),
        )
        body_base_y = np.fromiter(
            (body.y for body in enemy_bodies),
            dtype=np.float32,
            count=len(enemy_bodies),
        )
        body_velocity_x = np.fromiter(
            (body.vx for body in enemy_bodies),
            dtype=np.float32,
            count=len(enemy_bodies),
        )
        body_velocity_y = np.fromiter(
            (body.vy for body in enemy_bodies),
            dtype=np.float32,
            count=len(enemy_bodies),
        )
        body_half_width = np.fromiter(
            (
                body.half_width + body.uncertainty
                for body in enemy_bodies
            ),
            dtype=np.float32,
            count=len(enemy_bodies),
        )
        body_half_height = np.fromiter(
            (
                body.half_height + body.uncertainty
                for body in enemy_bodies
            ),
            dtype=np.float32,
            count=len(enemy_bodies),
        )
        async_absolute_deadline_ns = (
            None
            if preloss_supplemental_deadline_ms is None
            else async_submit_started_ns
            + int(preloss_supplemental_deadline_ms * 1_000_000.0)
        )
        async_native_job = functools.partial(
            search_supplemental_local_beam_native,
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
            actions=async_actions,
            allowed_first_actions=frozenset(
                effective_allowed_first_actions or ()
            ),
            action_hold_frames=action_hold_frames,
            horizon=horizon,
            beam_width=preloss_supplemental_beam_width,
            bullet_frames=bullet_frames[:horizon],
            laser_frames=tuple(
                frame.fields_for_native()
                for frame in laser_frames[:horizon]
            ),
            body_base_x=body_base_x,
            body_base_y=body_base_y,
            body_velocity_x=body_velocity_x,
            body_velocity_y=body_velocity_y,
            body_half_width=body_half_width,
            body_half_height=body_half_height,
            player_radius=PLAYER_RADIUS,
            control_delay_frames=control_delay_frames,
            previous_direction=previous_direction,
            previous_focused=previous_focus,
            preserve_previous_direction_inertia=(
                preserve_previous_direction_inertia
            ),
            target_x=target_x,
            target_y=target_y,
            target_deadline=target_deadline,
            item_safety_clearance=ITEM_SAFETY_CLEARANCE,
            playfield_left=PLAYFIELD_LEFT,
            playfield_right=PLAYFIELD_RIGHT,
            playfield_top=PLAYFIELD_TOP,
            playfield_bottom=PLAYFIELD_BOTTOM,
            recovery_reserve_distance=recovery_reserve_distance,
            supplemental_reserve_distance=preloss_reserve_distance,
            diagonal_speed=UNFOCUSED_DIAGONAL_SPEED,
            cardinal_speed=UNFOCUSED_CARDINAL_SPEED,
            certificate_collisions=native_certificate_collisions,
            certificate_minimum=native_certificate_minimum,
            survival_preferred=native_survival_preferred,
            safety_preferred=native_safety_preferred,
            recovery_distance=native_recovery_distance,
            repair_volume=async_repair_volume,
            absolute_deadline_ns=async_absolute_deadline_ns,
        )
        presubmitted_async_identity = (
            preloss_supplemental_version,
            local_pipeline_root,
            float(player_x).hex(),
            float(player_y).hex(),
            previous_direction,
            previous_focus,
            control_delay_frames,
            control_delay_candidates,
            action_hold_frames,
            horizon,
            preloss_supplemental_beam_width,
            beam_dedup_mode,
            target_x,
            target_y,
            target_deadline,
            tuple(effective_allowed_first_actions or ()),
            tuple(viability_repair_volumes),
            tuple(viability_recovery_distances),
            tuple(viability_safety_actions),
            tuple(viability_survival_actions),
        )
        preloss_supplemental_async_service.submit(
            presubmitted_async_identity,
            lambda workspace: async_native_job(workspace=workspace),
        )
        time.sleep(0)
        _certificate_timing_accumulator.supplemental_beam_ms += (
            time.perf_counter_ns() - async_submit_started_ns
        ) / 1_000_000.0
    baseline_result = run_baseline_stage(
        baseline_stage,
        initial_beam=beam,
        bullet_frames=bullet_frames,
        laser_frames=laser_frames,
        pruning_key=pruning_key,
    )
    beam_started_ns = baseline_result.started_ns
    beam = list(baseline_result.beam)

    supplemental_beam: list[SearchNode] = []
    supplemental_failure: str | None = None
    supplemental_status = (
        "not_eligible"
        if not preloss_supplemental_beam_active
        else "pending"
    )
    supplemental_completed = False
    supplemental_historical_fallback = False
    supplemental_async_identity = presubmitted_async_identity
    supplemental_background_compute_ms: float | None = None
    supplemental_published_terminal_labels: (
        tuple[tuple[int, float], ...] | None
    ) = None
    if (
        preloss_supplemental_beam_active
        and presubmitted_async_identity is not None
    ):
        supplemental_status = "async_submitted"
        supplemental_historical_fallback = True
    elif preloss_supplemental_beam_active:
        supplemental_started_ns = time.perf_counter_ns()
        supplemental_actions = tuple(
            SupplementalAction(
                name=action.name,
                direction=action.direction,
                dx=action.dx,
                dy=action.dy,
                focused=action.focused,
            )
            for action in _PLANNER_ACTIONS
        )

        def supplemental_transition_risk(
            node: SupplementalNode,
            action: SupplementalAction,
            x: float,
            y: float,
            step: int,
        ) -> float:
            last_action = supplemental_actions[node.last_action]
            risk = _boundary_risk(x, y)
            if action.direction != last_action.direction:
                risk += 0.08
            if _directions_opposed(
                action.direction,
                last_action.direction,
            ):
                risk += 24.0
            if action.focused != last_action.focused:
                risk += 0.12
            if step == 1 and preserve_previous_direction_inertia:
                if action.direction != previous_direction:
                    risk += 0.08
                if _directions_opposed(
                    action.direction,
                    previous_direction,
                ):
                    risk += 24.0
                if action.focused != previous_focus:
                    risk += 0.12
            return risk

        def supplemental_hazard_query(
            positions_x: np.ndarray,
            positions_y: np.ndarray,
            absolute_step: int,
        ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
            local_step = absolute_step - control_delay_frames
            return _hazards_for_positions(
                positions_x,
                positions_y,
                step=absolute_step,
                bullet_frame=bullet_frames[local_step - 1],
                lasers=laser_frames[local_step - 1],
                enemy_bodies=enemy_bodies,
            )

        initial_supplemental = SupplementalNode(
            x=initial_node.x,
            y=initial_node.y,
            first_action=0,
            last_action=0,
            risk=initial_node.risk,
            collisions=initial_node.collisions,
            min_clearance=initial_node.min_clearance,
            immediate_clearance=initial_node.immediate_clearance,
        )
        certificate_collisions = np.fromiter(
            (
                robust_preflight_certificates[
                    action.name
                ].worst_collisions
                if action.name in robust_preflight_certificates
                else 0
                for action in _PLANNER_ACTIONS
            ),
            dtype=np.int32,
            count=len(_PLANNER_ACTIONS),
        )
        certificate_minimum = np.fromiter(
            (
                robust_preflight_certificates[
                    action.name
                ].min_clearance
                if action.name in robust_preflight_certificates
                else 0.0
                for action in _PLANNER_ACTIONS
            ),
            dtype=np.float64,
            count=len(_PLANNER_ACTIONS),
        )
        survival_preferred = np.fromiter(
            (
                not survival_actions
                or action.name in survival_actions
                for action in _PLANNER_ACTIONS
            ),
            dtype=np.uint8,
            count=len(_PLANNER_ACTIONS),
        )
        safety_preferred = np.fromiter(
            (
                not safety_value_actions
                or action.name in safety_value_actions
                for action in _PLANNER_ACTIONS
            ),
            dtype=np.uint8,
            count=len(_PLANNER_ACTIONS),
        )
        recovery_distance = np.fromiter(
            (
                recovery_by_action.get(action.name, math.inf)
                for action in _PLANNER_ACTIONS
            ),
            dtype=np.float64,
            count=len(_PLANNER_ACTIONS),
        )
        repair_volume = np.fromiter(
            (
                repair_by_action.get(action.name, 0)
                for action in _PLANNER_ACTIONS
            ),
            dtype=np.int32,
            count=len(_PLANNER_ACTIONS),
        )
        absolute_supplemental_deadline_ns = (
            None
            if preloss_supplemental_deadline_ms is None
            else supplemental_started_ns
            + int(preloss_supplemental_deadline_ms * 1_000_000.0)
        )
        try:
            if (
                _LOCAL_SUPPLEMENTAL_BACKEND == "native"
                and beam_dedup_mode == "quantized"
            ):
                native_job = functools.partial(
                    search_supplemental_local_beam_native,
                    initial=initial_supplemental,
                    actions=supplemental_actions,
                    allowed_first_actions=frozenset(
                        effective_allowed_first_actions or ()
                    ),
                    action_hold_frames=action_hold_frames,
                    horizon=horizon,
                    beam_width=preloss_supplemental_beam_width,
                    bullet_frames=bullet_frames[:horizon],
                    laser_frames=tuple(
                        frame.fields_for_native()
                        for frame in laser_frames[:horizon]
                    ),
                    body_base_x=np.fromiter(
                        (body.x for body in enemy_bodies),
                        dtype=np.float32,
                        count=len(enemy_bodies),
                    ),
                    body_base_y=np.fromiter(
                        (body.y for body in enemy_bodies),
                        dtype=np.float32,
                        count=len(enemy_bodies),
                    ),
                    body_velocity_x=np.fromiter(
                        (body.vx for body in enemy_bodies),
                        dtype=np.float32,
                        count=len(enemy_bodies),
                    ),
                    body_velocity_y=np.fromiter(
                        (body.vy for body in enemy_bodies),
                        dtype=np.float32,
                        count=len(enemy_bodies),
                    ),
                    body_half_width=np.fromiter(
                        (
                            body.half_width + body.uncertainty
                            for body in enemy_bodies
                        ),
                        dtype=np.float32,
                        count=len(enemy_bodies),
                    ),
                    body_half_height=np.fromiter(
                        (
                            body.half_height + body.uncertainty
                            for body in enemy_bodies
                        ),
                        dtype=np.float32,
                        count=len(enemy_bodies),
                    ),
                    player_radius=PLAYER_RADIUS,
                    control_delay_frames=control_delay_frames,
                    previous_direction=previous_direction,
                    previous_focused=previous_focus,
                    preserve_previous_direction_inertia=(
                        preserve_previous_direction_inertia
                    ),
                    target_x=target_x,
                    target_y=target_y,
                    target_deadline=target_deadline,
                    item_safety_clearance=ITEM_SAFETY_CLEARANCE,
                    playfield_left=PLAYFIELD_LEFT,
                    playfield_right=PLAYFIELD_RIGHT,
                    playfield_top=PLAYFIELD_TOP,
                    playfield_bottom=PLAYFIELD_BOTTOM,
                    recovery_reserve_distance=(
                        recovery_reserve_distance
                    ),
                    supplemental_reserve_distance=(
                        preloss_reserve_distance
                    ),
                    diagonal_speed=UNFOCUSED_DIAGONAL_SPEED,
                    cardinal_speed=UNFOCUSED_CARDINAL_SPEED,
                    certificate_collisions=certificate_collisions,
                    certificate_minimum=certificate_minimum,
                    survival_preferred=survival_preferred,
                    safety_preferred=safety_preferred,
                    recovery_distance=recovery_distance,
                    repair_volume=repair_volume,
                    absolute_deadline_ns=(
                        absolute_supplemental_deadline_ns
                    ),
                )
                if preloss_supplemental_async_service is not None:
                    supplemental_async_identity = (
                        preloss_supplemental_version,
                        local_pipeline_root,
                        float(player_x).hex(),
                        float(player_y).hex(),
                        previous_direction,
                        previous_focus,
                        control_delay_frames,
                        control_delay_candidates,
                        action_hold_frames,
                        horizon,
                        preloss_supplemental_beam_width,
                        beam_dedup_mode,
                        target_x,
                        target_y,
                        target_deadline,
                        tuple(effective_allowed_first_actions or ()),
                        tuple(viability_repair_volumes),
                        tuple(viability_recovery_distances),
                        tuple(viability_safety_actions),
                        tuple(viability_survival_actions),
                    )
                    preloss_supplemental_async_service.submit(
                        supplemental_async_identity,
                        lambda workspace: native_job(
                            workspace=workspace
                        ),
                    )
                    # Give the dedicated newest-wins worker one scheduling
                    # opportunity; the consumer still performs lookup-only
                    # publication with no completion wait.
                    time.sleep(0)
                    lane_nodes = []
                    supplemental_status = "async_submitted"
                    supplemental_historical_fallback = True
                else:
                    lane_nodes = native_job()
            else:
                lane_nodes = search_supplemental_local_beam(
                    initial=initial_supplemental,
                    actions=supplemental_actions,
                    allowed_first_actions=frozenset(
                        effective_allowed_first_actions or ()
                    ),
                    action_hold_frames=action_hold_frames,
                    horizon=horizon,
                    beam_width=preloss_supplemental_beam_width,
                    beam_dedup_mode=beam_dedup_mode,
                    hazard_query=supplemental_hazard_query,
                    transition_risk=supplemental_transition_risk,
                    control_delay_frames=control_delay_frames,
                    target_x=target_x,
                    target_y=target_y,
                    target_deadline=target_deadline,
                    item_safety_clearance=ITEM_SAFETY_CLEARANCE,
                    playfield_left=PLAYFIELD_LEFT,
                    playfield_right=PLAYFIELD_RIGHT,
                    playfield_top=PLAYFIELD_TOP,
                    playfield_bottom=PLAYFIELD_BOTTOM,
                    recovery_reserve_distance=(
                        recovery_reserve_distance
                    ),
                    supplemental_reserve_distance=(
                        preloss_reserve_distance
                    ),
                    diagonal_speed=UNFOCUSED_DIAGONAL_SPEED,
                    cardinal_speed=UNFOCUSED_CARDINAL_SPEED,
                    certificate_collisions=certificate_collisions,
                    certificate_minimum=certificate_minimum,
                    survival_preferred=survival_preferred,
                    safety_preferred=safety_preferred,
                    recovery_distance=recovery_distance,
                    repair_volume=repair_volume,
                    use_native_reducer=native_beam_enabled,
                )
            if supplemental_status != "async_submitted":
                supplemental_status = "completed"
                supplemental_completed = True
            supplemental_beam = [
                SearchNode(
                    x=node.x,
                    y=node.y,
                    first_action=_PLANNER_ACTIONS[
                        node.first_action
                    ],
                    last_action=_PLANNER_ACTIONS[node.last_action],
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
            supplemental_beam = []
            supplemental_status = "deadline"
            supplemental_historical_fallback = True
        except native_backend.LocalSupplementalNativeCancelledError:
            supplemental_beam = []
            supplemental_status = "cancelled"
            supplemental_historical_fallback = True
        except Exception as error:
            supplemental_beam = []
            supplemental_status = "error"
            supplemental_historical_fallback = True
            supplemental_failure = (
                f"{type(error).__name__}: {error}"
            )
        finally:
            _certificate_timing_accumulator.supplemental_beam_ms += (
                time.perf_counter_ns() - supplemental_started_ns
            ) / 1_000_000.0
    if supplemental_failure is not None:
        preloss_continuation_preference_active = False
        preloss_supplemental_beam_active = False

    if not beam:
        beam = [
            SearchNode(
                player_x,
                player_y,
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
    supplemental_source_ids = {id(node) for node in supplemental_beam}
    for index, node in enumerate(beam):
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
        beam[index] = replace(node, risk=node.risk + position_cost)
    async_terminal_started_ns: int | None = None
    terminal_threats: dict[SearchNode, tuple[int, float]] = {}
    if supplemental_async_identity is not None:
        assert preloss_supplemental_async_service is not None
        async_terminal_started_ns = time.perf_counter_ns()
        terminal_threats.update(
            _terminal_threat_scores(
                beam,
                start_step=horizon,
                end_step=effective_threat_horizon,
                control_delay_frames=control_delay_frames,
                bullet_frames=bullet_frames,
                laser_frames=laser_frames,
                enemy_bodies=enemy_bodies,
            )
        )
        completed_lookup: CompletedSupplementalLookup = (
            lookup_completed_supplemental(
                service=preloss_supplemental_async_service,
                identity=supplemental_async_identity,
                actions=_PLANNER_ACTIONS,
            )
        )
        supplemental_status = completed_lookup.status
        supplemental_completed = completed_lookup.completed
        supplemental_historical_fallback = (
            completed_lookup.historical_fallback
        )
        supplemental_background_compute_ms = (
            completed_lookup.background_compute_ms
        )
        supplemental_published_terminal_labels = (
            completed_lookup.terminal_labels
        )
        supplemental_beam = list(completed_lookup.beam)
    for index, node in enumerate(supplemental_beam):
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
        replaced_node = replace(node, risk=node.risk + position_cost)
        supplemental_source_ids.discard(id(node))
        supplemental_source_ids.add(id(replaced_node))
        supplemental_beam[index] = replaced_node
    if supplemental_published_terminal_labels is not None:
        if (
            len(supplemental_published_terminal_labels)
            != len(supplemental_beam)
        ):
            supplemental_failure = (
                "RuntimeError: async terminal publication count mismatch"
            )
            supplemental_status = "error"
            supplemental_completed = False
            supplemental_historical_fallback = True
            supplemental_beam = []
            supplemental_source_ids.clear()
        else:
            terminal_threats.update(
                zip(
                    supplemental_beam,
                    supplemental_published_terminal_labels,
                )
            )
    _certificate_timing_accumulator.beam_search_ms += (
        time.perf_counter_ns() - beam_started_ns
    ) / 1_000_000.0
    terminal_threat_started_ns = (
        async_terminal_started_ns
        if async_terminal_started_ns is not None
        else time.perf_counter_ns()
    )
    endpoint_pool = [*beam, *supplemental_beam]
    if async_terminal_started_ns is None:
        terminal_threats = _terminal_threat_scores(
            endpoint_pool,
            start_step=horizon,
            end_step=effective_threat_horizon,
            control_delay_frames=control_delay_frames,
            bullet_frames=bullet_frames,
            laser_frames=laser_frames,
            enemy_bodies=enemy_bodies,
        )
    elif (
        supplemental_beam
        and supplemental_published_terminal_labels is None
    ):
        terminal_threats.update(
            _terminal_threat_scores(
                supplemental_beam,
                start_step=horizon,
                end_step=effective_threat_horizon,
                control_delay_frames=control_delay_frames,
                bullet_frames=bullet_frames,
                laser_frames=laser_frames,
                enemy_bodies=enemy_bodies,
            )
        )
    _certificate_timing_accumulator.terminal_threat_ms += (
        time.perf_counter_ns() - terminal_threat_started_ns
    ) / 1_000_000.0
    selection_started_ns = time.perf_counter_ns()
    endpoint_ranker = EndpointRanker(
        terminal_threats=terminal_threats,
        survival_actions=survival_actions,
        safety_value_actions=safety_value_actions,
        recovery_by_action=recovery_by_action,
        repair_by_action=repair_by_action,
        recovery_reserve_distance=recovery_reserve_distance,
        preloss_reserve_distance=preloss_reserve_distance,
        preloss_continuation_preference_active=(
            preloss_continuation_preference_active
        ),
        item_safety_clearance=ITEM_SAFETY_CLEARANCE,
        horizon=horizon,
        selected_items=selected_items,
        target_x=target_x,
        target_y=target_y,
        target_deadline=target_deadline,
        boundary_control_reserve_deficit=(
            _boundary_control_reserve_deficit
        ),
        node_key=_node_key,
        minimum_travel_frames=_minimum_travel_frames,
    )
    historical_selection_key = endpoint_ranker.historical_key
    selection_key = endpoint_ranker.selection_key
    route_gate_deficit = endpoint_ranker.route_gate_deficit

    robust_certificates: dict[str, RobustActionCertificate] = {}
    nodes_by_action: dict[str, SearchNode] = {}
    robust_override = False
    robust_certificate: RobustActionCertificate | None = None
    historical_best = min(beam, key=historical_selection_key)
    historical_route_gate_deficit = route_gate_deficit(historical_best)
    preloss_selected_from_supplemental = False
    preloss_candidate_count = 0

    if preloss_continuation_preference_active:
        actions_by_name: dict[str, PlannerAction] = {}
        for node in endpoint_pool:
            action_name = node.first_action.name
            actions_by_name[action_name] = node.first_action
        if control_delay_candidates is not None:
            if actions_by_name.keys() <= robust_preflight_certificates.keys():
                robust_certificates = {
                    action_name: robust_preflight_certificates[action_name]
                    for action_name in actions_by_name
                }
            else:
                robust_certificates = _robust_action_certificates(
                    player_x=observed_player_x,
                    player_y=observed_player_y,
                    previous_mask=delayed_mask,
                    actions=tuple(actions_by_name.values()),
                    delay_frames=control_delay_candidates,
                    action_hold_frames=action_hold_frames,
                    bullets=bullets,
                    lasers=lasers,
                    enemy_bodies=enemy_bodies,
                    snapshot_lag=snapshot_lag,
                    laser_frames=laser_timeline[:certificate_horizon],
                    pipeline_root=local_pipeline_root,
                    timing_accumulator=_certificate_timing_accumulator,
                )

        historical_nodes_by_action: dict[str, SearchNode] = {}
        for node in beam:
            action_name = node.first_action.name
            incumbent = historical_nodes_by_action.get(action_name)
            if (
                incumbent is None
                or historical_selection_key(node)
                < historical_selection_key(incumbent)
            ):
                historical_nodes_by_action[action_name] = node
        historical_provisional = historical_best
        if robust_certificates:
            nominal_certificate = robust_certificates[
                historical_best.first_action.name
            ]
            if (
                nominal_certificate.worst_collisions > 0
                or nominal_certificate.min_clearance < 0.0
            ):
                historical_best = min(
                    historical_nodes_by_action.values(),
                    key=lambda node: (
                        robust_certificates[
                            node.first_action.name
                        ].worst_collisions,
                        max(
                            -robust_certificates[
                                node.first_action.name
                            ].min_clearance,
                            0.0,
                        ),
                        robust_certificates[
                            node.first_action.name
                        ].cvar_risk,
                        -robust_certificates[
                            node.first_action.name
                        ].min_clearance,
                        historical_selection_key(node),
                    ),
                )
                robust_override = (
                    historical_best.first_action
                    != historical_provisional.first_action
                )
        historical_route_gate_deficit = route_gate_deficit(
            historical_best
        )

        def hard_components(node: SearchNode) -> tuple[int | float, ...]:
            threat_collisions, threat_clearance = terminal_threats[node]
            certificate = robust_certificates.get(
                node.first_action.name
            )
            return (
                (
                    certificate.worst_collisions
                    if certificate is not None
                    else 0
                ),
                (
                    max(-certificate.min_clearance, 0.0)
                    if certificate is not None
                    else 0.0
                ),
                node.collisions,
                max(-node.min_clearance, 0.0),
                threat_collisions,
                max(-threat_clearance, 0.0),
            )

        historical_hard = hard_components(historical_best)
        historical_survival_deficit = (
            0
            if (
                not survival_actions
                or historical_best.first_action.name in survival_actions
            )
            else 1
        )
        historical_continuation_key = (
            -repair_by_action.get(
                historical_best.first_action.name,
                0,
            ),
            _boundary_control_reserve_deficit(
                historical_best.x,
                historical_best.y,
                reserve_distance=preloss_reserve_distance,
            ),
        )
        effective_set = set(effective_allowed_first_actions or ())
        admitted: list[SearchNode] = []
        for node in endpoint_pool:
            node_hard = hard_components(node)
            if not all(
                candidate <= incumbent
                for candidate, incumbent in zip(
                    node_hard,
                    historical_hard,
                )
            ):
                continue
            if (
                route_gate_deficit(node)
                > historical_route_gate_deficit
            ):
                continue
            if (
                effective_set
                and node.first_action.name not in effective_set
            ):
                continue
            survival_deficit = (
                0
                if (
                    not survival_actions
                    or node.first_action.name in survival_actions
                )
                else 1
            )
            if survival_deficit > historical_survival_deficit:
                continue
            continuation_key = (
                -repair_by_action.get(node.first_action.name, 0),
                _boundary_control_reserve_deficit(
                    node.x,
                    node.y,
                    reserve_distance=preloss_reserve_distance,
                ),
            )
            if continuation_key >= historical_continuation_key:
                continue
            admitted.append(node)
        preloss_candidate_count = len(admitted)
        best = (
            min(
                admitted,
                key=lambda node: (
                    hard_components(node),
                    (
                        0
                        if (
                            not survival_actions
                            or node.first_action.name
                            in survival_actions
                        )
                        else 1
                    ),
                    -repair_by_action.get(
                        node.first_action.name,
                        0,
                    ),
                    _boundary_control_reserve_deficit(
                        node.x,
                        node.y,
                        reserve_distance=preloss_reserve_distance,
                    ),
                    historical_selection_key(node),
                ),
            )
            if admitted
            else historical_best
        )
        preloss_selected_from_supplemental = (
            id(best) in supplemental_source_ids
        )
        for node in endpoint_pool:
            action_name = node.first_action.name
            incumbent = nodes_by_action.get(action_name)
            if (
                incumbent is None
                or selection_key(node) < selection_key(incumbent)
            ):
                nodes_by_action[action_name] = node
        robust_certificate = robust_certificates.get(
            best.first_action.name
        )
    else:
        best = min(beam, key=selection_key)
        if control_delay_candidates is not None:
            actions_by_name: dict[str, PlannerAction] = {}
            for node in beam:
                action_name = node.first_action.name
                actions_by_name[action_name] = node.first_action
                incumbent = nodes_by_action.get(action_name)
                if incumbent is None or selection_key(
                    node
                ) < selection_key(incumbent):
                    nodes_by_action[action_name] = node
            if actions_by_name.keys() <= (
                robust_preflight_certificates.keys()
            ):
                robust_certificates = {
                    action_name: robust_preflight_certificates[action_name]
                    for action_name in actions_by_name
                }
            else:
                robust_certificates = _robust_action_certificates(
                    player_x=observed_player_x,
                    player_y=observed_player_y,
                    previous_mask=delayed_mask,
                    actions=tuple(actions_by_name.values()),
                    delay_frames=control_delay_candidates,
                    action_hold_frames=action_hold_frames,
                    bullets=bullets,
                    lasers=lasers,
                    enemy_bodies=enemy_bodies,
                    snapshot_lag=snapshot_lag,
                    laser_frames=laser_timeline[:certificate_horizon],
                    pipeline_root=local_pipeline_root,
                    timing_accumulator=_certificate_timing_accumulator,
                )
            nominal_certificate = robust_certificates[
                best.first_action.name
            ]
            if (
                nominal_certificate.worst_collisions > 0
                or nominal_certificate.min_clearance < 0.0
            ):
                robust_best = min(
                    nodes_by_action.values(),
                    key=lambda node: (
                        robust_certificates[
                            node.first_action.name
                        ].worst_collisions,
                        max(
                            -robust_certificates[
                                node.first_action.name
                            ].min_clearance,
                            0.0,
                        ),
                        robust_certificates[
                            node.first_action.name
                        ].cvar_risk,
                        -robust_certificates[
                            node.first_action.name
                        ].min_clearance,
                        selection_key(node),
                    ),
                )
                robust_override = (
                    robust_best.first_action != best.first_action
                )
                best = robust_best
            robust_certificate = robust_certificates[
                best.first_action.name
            ]
    damage_reason = "boss_not_damageable"
    if damageable:
        damage_reason = "boss_geometry_unavailable"
    if damageable and damage_target_x is not None:
        damage_reason = "fresh_viability_unavailable"
    if (
        damageable
        and damage_target_x is not None
        and effective_allowed_first_actions is not None
    ):
        damage_reason = (
            "viability_constraint_relaxed"
            if viability_fresh_prefix_relaxed
            else "issue_certificate_unavailable"
        )
    damage_shadow_action: str | None = None
    damage_baseline_action = best.first_action.name
    damage_current_alignment_cost: float | None = None
    damage_shadow_alignment_cost: float | None = None
    damage_eligible_action_count = 0
    damage_objective_available = bool(
        damageable
        and damage_target_x is not None
        and effective_allowed_first_actions is not None
        and not viability_fresh_prefix_relaxed
        and robust_certificates
        and nodes_by_action
    )
    if damage_objective_available:
        viable_actions = set(effective_allowed_first_actions or ())
        progress_candidates = tuple(
            ProgressCandidate(
                action=action_name,
                progress_cost=max(
                    abs(node.x - damage_target_x)
                    - damage_target_half_width,
                    0.0,
                ),
                viable=action_name in viable_actions,
                issue_collisions=robust_certificates[
                    action_name
                ].worst_collisions,
                issue_min_clearance=robust_certificates[
                    action_name
                ].min_clearance,
                baseline_rank=selection_key(node),
            )
            for action_name, node in nodes_by_action.items()
        )
        damage_eligible_action_count = sum(
            candidate.viable
            and candidate.issue_collisions == 0
            and candidate.issue_min_clearance >= 0.0
            for candidate in progress_candidates
        )
        damage_candidate = select_progress_action(progress_candidates)
        if damage_candidate is None:
            damage_objective_available = False
            damage_reason = "no_issue_safe_viable_action"
        else:
            damage_reason = "shadow_lexicographic_tiebreak"
            damage_shadow_action = damage_candidate.action
            damage_current_alignment_cost = max(
                abs(best.x - damage_target_x) - damage_target_half_width,
                0.0,
            )
            damage_shadow_alignment_cost = damage_candidate.progress_cost
    threat_collisions, threat_clearance = terminal_threats[best]
    decision = assemble_local_decision(
        ProposalAssemblyContext(
            request=request,
            validated=validated,
            prepared=prepared,
            preflight=preflight,
            best=best,
            robust_certificate=robust_certificate,
            robust_override=robust_override,
            terminal_threat=(threat_collisions, threat_clearance),
            prefix_clearance=prefix_clearance,
            damage=DamageDecisionFields(
                available=damage_objective_available,
                baseline_action=damage_baseline_action,
                shadow_action=damage_shadow_action,
                current_alignment_cost=damage_current_alignment_cost,
                shadow_alignment_cost=damage_shadow_alignment_cost,
                eligible_action_count=damage_eligible_action_count,
                reason=damage_reason,
            ),
            supplemental=SupplementalDecisionFields(
                active=preloss_supplemental_beam_active,
                selected_from_supplemental=(
                    preloss_selected_from_supplemental
                ),
                candidate_count=preloss_candidate_count,
                failure=supplemental_failure,
                backend=(
                    "exact_async_native"
                    if preloss_supplemental_async_service is not None
                    else _LOCAL_SUPPLEMENTAL_BACKEND
                ),
                status=supplemental_status,
                completed=supplemental_completed,
                historical_fallback=(
                    supplemental_historical_fallback
                ),
                background_compute_ms=(
                    supplemental_background_compute_ms
                ),
                historical_action=(
                    historical_best.first_action.name
                    if preloss_continuation_preference_active
                    else None
                ),
                historical_route_gate_deficit=(
                    historical_route_gate_deficit
                ),
            ),
            route_gate_deficit=route_gate_deficit(best),
            local_collisions=best.collisions,
        ),
        actions=_PLANNER_ACTIONS,
        shot_mask=SHOT,
        focus_mask=FOCUS,
        bomb_mask=BOMB,
        boundary_control_reserve_deficit=(
            _boundary_control_reserve_deficit
        ),
    )
    _certificate_timing_accumulator.selection_finalize_ms += (
        time.perf_counter_ns() - selection_started_ns
    ) / 1_000_000.0
    if (
        effective_allowed_first_actions is not None
        and effective_threat_horizon > horizon
        and (
            threat_collisions > 0
            or decision.robust_collisions > 0
            or decision.min_clearance <= 0.0
        )
        and relax_stale_viability_contradiction
        and not _viability_retry
    ):
        return _PlannerModeTransition(
            current_decision=decision,
            next_request=replace(
                request,
                physical=replace(
                    physical,
                    player_x=observed_player_x,
                    player_y=observed_player_y,
                ),
                guidance=replace(
                    guidance,
                    allowed_first_actions=None,
                ),
                # Preserve the historical retry contract: damage guidance was
                # not forwarded into the relaxed pass.
                objective=ObjectiveContext(
                    power=power,
                    bombs=bombs,
                ),
                mode=PlannerMode.RELAXED_VIABILITY,
            ),
            original_allowed_action_count=len(
                allowed_first_actions or ()
            ),
        )
    return replace(
        decision,
        local_certificate_timing=(
            _certificate_timing_accumulator.snapshot()
        ),
    )
