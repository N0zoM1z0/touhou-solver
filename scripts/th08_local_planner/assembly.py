"""Assembly of the flat compatibility decision from ranked planner output."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Callable

from .models import Decision, RobustActionCertificate, SearchNode
from .requests import LocalPlannerRequest
from .stages import HardPreflightResult, PreparedLocalHazards
from .validation import ValidatedPlannerRequest


@dataclass(frozen=True)
class DamageDecisionFields:
    available: bool
    baseline_action: str | None
    shadow_action: str | None
    current_alignment_cost: float | None
    shadow_alignment_cost: float | None
    eligible_action_count: int
    reason: str


@dataclass(frozen=True)
class ProposalAssemblyContext:
    request: LocalPlannerRequest
    validated: ValidatedPlannerRequest
    prepared: PreparedLocalHazards
    preflight: HardPreflightResult
    best: SearchNode
    robust_certificate: RobustActionCertificate | None
    robust_override: bool
    terminal_threat: tuple[int, float]
    prefix_clearance: float
    damage: DamageDecisionFields
    historical_action: str | None
    historical_route_gate_deficit: float
    route_gate_deficit: float
    local_collisions: int


def assemble_local_decision(
    context: ProposalAssemblyContext,
    *,
    actions: tuple[Any, ...],
    shot_mask: int,
    focus_mask: int,
    bomb_mask: int,
    boundary_control_reserve_deficit: Callable[..., float],
) -> Decision:
    request = context.request
    guidance = request.guidance
    actuator = request.actuator
    best = context.best
    action = best.first_action
    certificate = context.robust_certificate
    minimum = (
        9999.0 if math.isinf(best.min_clearance) else best.min_clearance
    )
    immediate = (
        9999.0
        if math.isinf(best.immediate_clearance)
        else best.immediate_clearance
    )
    use_bomb = actuator.can_bomb and (
        immediate <= 0.0
        or (
            certificate is not None
            and certificate.worst_collisions > 0
        )
    )
    threat_collisions, threat_clearance = context.terminal_threat
    predicted_collections = tuple(
        context.prepared.selected_items[index][0].slot
        for index in range(len(context.prepared.selected_items))
        if best.collected_mask & (1 << index)
    )
    pipeline_clearance = (
        9999.0
        if math.isinf(context.prefix_clearance)
        else context.prefix_clearance
    )
    damage = context.damage
    preflight = context.preflight
    validated = context.validated

    return Decision(
        shot_mask
        | (focus_mask if action.focused else 0)
        | action.direction
        | (bomb_mask if use_bomb else 0),
        action.name,
        minimum,
        immediate,
        best.risk,
        use_bomb,
        best.item_utility,
        action.focused,
        predicted_collections,
        pipeline_clearance,
        actuator.control_delay_candidates or (),
        context.robust_override,
        (
            certificate.worst_collisions
            if certificate is not None
            else 0
        ),
        (
            certificate.min_clearance
            if certificate is not None
            else 9999.0
        ),
        certificate.cvar_risk if certificate is not None else 0.0,
        certificate.worst_delay if certificate is not None else None,
        bool(
            preflight.effective_allowed_first_actions is not None
            and not preflight.viability_fresh_prefix_relaxed
        ),
        len(guidance.allowed_first_actions or ()),
        validated.repair_by_action.get(action.name, 0),
        preflight.viability_constraint_relaxed,
        context.prepared.potential_threat_horizon,
        threat_collisions,
        9999.0 if math.isinf(threat_clearance) else threat_clearance,
        validated.recovery_by_action.get(action.name),
        boundary_control_reserve_deficit(
            best.x,
            best.y,
            reserve_distance=(
                context.prepared.diagnostic_losing_reserve_distance
            ),
        ),
        bool(
            validated.safety_value_actions
            and action.name in validated.safety_value_actions
        ),
        guidance.viability_safety_state_value,
        preflight.viability_fresh_prefix_filtered,
        preflight.viability_fresh_prefix_relaxed,
        bool(
            validated.survival_actions
            and action.name in validated.survival_actions
        ),
        guidance.viability_survival_frames,
        guidance.viability_survival_bottleneck_margin,
        damage_objective_available=damage.available,
        damage_baseline_action=damage.baseline_action,
        damage_shadow_action=damage.shadow_action,
        damage_current_alignment_cost=damage.current_alignment_cost,
        damage_shadow_alignment_cost=damage.shadow_alignment_cost,
        damage_eligible_action_count=damage.eligible_action_count,
        damage_reason=damage.reason,
        issue_action_certificates=tuple(
            preflight.certificates[planner_action.name]
            for planner_action in actions
            if planner_action.name in preflight.certificates
        ),
        preloss_continuation_preference_active=(
            request.config.preloss_continuation_preference
            and context.historical_action is not None
        ),
        planned_route_gate_deficit=context.route_gate_deficit,
        preloss_historical_action=context.historical_action,
        preloss_historical_route_gate_deficit=(
            context.historical_route_gate_deficit
        ),
        local_collisions=context.local_collisions,
    )
