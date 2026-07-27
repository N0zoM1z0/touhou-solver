"""One complete local-planner pass behind an explicit controller boundary."""

from __future__ import annotations

import math
import time
from dataclasses import replace

from th08_local_planner import (
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
from th08_live.planner_pass_baseline import (
    prepare_baseline_stage,
    run_baseline_stage,
)
from th08_live.planner_pass_supplemental import (
    presubmit_supplemental_stage,
    run_supplemental_stage,
)
from th08_live.planner_pass_types import (
    LocalCertificateTimingAccumulator,
    PlannerModeTransition,
    PlannerPassDependencies,
)
from touhou_control.phase_progress import ProgressCandidate


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
    BOMB = dependencies.bomb_mask
    FOCUS = dependencies.focus_mask
    SHOT = dependencies.shot_mask
    ITEM_SAFETY_CLEARANCE = dependencies.item_safety_clearance
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
    select_progress_action = dependencies.select_progress_action

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

    local_pipeline_root = actuator.local_pipeline_root
    control_delay_frames = actuator.control_delay_frames
    control_delay_candidates = actuator.control_delay_candidates
    action_hold_frames = actuator.action_hold_frames

    target_x = guidance.target_x
    target_y = guidance.target_y
    target_deadline = guidance.target_deadline
    allowed_first_actions = guidance.allowed_first_actions

    horizon = config.horizon
    preloss_continuation_preference = (
        config.preloss_continuation_preference
    )
    preloss_supplemental_beam_width = (
        config.preloss_supplemental_beam_width
    )
    relax_stale_viability_contradiction = (
        config.relax_stale_viability_contradiction
    )

    power = objective.power
    bombs = objective.bombs
    damage_target_x = objective.damage_target_x
    damage_target_half_width = objective.damage_target_half_width
    damageable = objective.damageable

    preloss_supplemental_async_service = (
        completed.supplemental_async_service
    )
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
    supplemental_submission = presubmit_supplemental_stage(
        baseline_stage,
        active=preloss_supplemental_beam_active,
        initial_node=initial_node,
        bullet_frames=bullet_frames,
        laser_frames=laser_frames,
        supplemental_reserve_distance=preloss_reserve_distance,
        timing=_certificate_timing_accumulator,
    )
    baseline_result = run_baseline_stage(
        baseline_stage,
        initial_beam=beam,
        bullet_frames=bullet_frames,
        laser_frames=laser_frames,
        pruning_key=pruning_key,
    )
    beam_started_ns = baseline_result.started_ns
    beam = list(baseline_result.beam)

    supplemental_result = run_supplemental_stage(
        baseline_stage,
        submission=supplemental_submission,
        baseline_beam=beam,
        initial_node=initial_node,
        bullet_frames=bullet_frames,
        laser_frames=laser_frames,
        beam_started_ns=beam_started_ns,
        continuation_preference_active=(
            preloss_continuation_preference_active
        ),
        supplemental_beam_active=preloss_supplemental_beam_active,
        supplemental_reserve_distance=preloss_reserve_distance,
        effective_threat_horizon=effective_threat_horizon,
        timing=_certificate_timing_accumulator,
    )
    beam = list(supplemental_result.baseline_beam)
    supplemental_beam = list(supplemental_result.supplemental_beam)
    terminal_threats = supplemental_result.terminal_threats
    supplemental_source_ids = supplemental_result.supplemental_source_ids
    preloss_continuation_preference_active = (
        supplemental_result.continuation_preference_active
    )
    preloss_supplemental_beam_active = (
        supplemental_result.supplemental_beam_active
    )
    supplemental_failure = supplemental_result.failure
    supplemental_status = supplemental_result.status
    supplemental_completed = supplemental_result.completed
    supplemental_historical_fallback = (
        supplemental_result.historical_fallback
    )
    supplemental_background_compute_ms = (
        supplemental_result.background_compute_ms
    )
    endpoint_pool = [*beam, *supplemental_beam]
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
                    else dependencies.local_supplemental_backend
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
