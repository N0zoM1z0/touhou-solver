"""Fresh-hazard issue transaction with explicit proposal/commit ownership."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Callable

from th08_time_scale import Th08TimeScaleSchedule

from .models import (
    IssueRecertification,
    IssuedDecision,
    LocalProposal,
    RobustActionCertificate,
)


@dataclass(frozen=True)
class IssueRequest:
    player_x: float
    player_y: float
    previous_mask: int
    delay_frames: tuple[int, ...]
    action_hold_frames: int
    bullets: tuple[Any, ...]
    lasers: tuple[Any, ...]
    enemy_bodies: tuple[Any, ...]
    snapshot_lag: int
    time_scale_schedule: Th08TimeScaleSchedule
    pipeline_root: Any | None = None
    allowed_first_actions: tuple[str, ...] | None = None
    viability_repair_volumes: tuple[tuple[str, int], ...] = ()
    viability_recovery_distances: tuple[tuple[str, float], ...] = ()
    viability_safety_actions: tuple[str, ...] = ()
    viability_survival_actions: tuple[str, ...] = ()
    preferred_action: str | None = None
    preference_reason: str | None = None


@dataclass(frozen=True)
class IssueAdapter:
    actions: tuple[Any, ...]
    certificate_provider: Callable[..., dict[str, RobustActionCertificate]]
    timing_factory: Callable[[], Any]
    shot_mask: int
    focus_mask: int
    bomb_mask: int


class IssueTransaction:
    """Commit one local proposal against one fresh immutable hazard snapshot."""

    def __init__(
        self,
        proposal: LocalProposal,
        request: IssueRequest,
        adapter: IssueAdapter,
    ) -> None:
        self._proposal = proposal
        self._request = request
        self._adapter = adapter
        self._committed: IssuedDecision | None = None

    def commit(self) -> IssuedDecision:
        if self._committed is not None:
            return self._committed

        decision = self._proposal.decision
        request = self._request
        adapter = self._adapter
        timing = adapter.timing_factory()
        certificate_horizon = (
            request.action_hold_frames + max(request.delay_frames)
        )
        certificates = adapter.certificate_provider(
            player_x=request.player_x,
            player_y=request.player_y,
            previous_mask=request.previous_mask,
            actions=adapter.actions,
            delay_frames=request.delay_frames,
            action_hold_frames=request.action_hold_frames,
            bullets=request.bullets,
            lasers=request.lasers,
            enemy_bodies=request.enemy_bodies,
            snapshot_lag=request.snapshot_lag,
            player_scale_bits=(
                request.time_scale_schedule.require_player_horizon(
                    certificate_horizon
                )
            ),
            laser_scale_bits=(
                request.time_scale_schedule.require_laser_horizon(
                    certificate_horizon
                )
            ),
            pipeline_root=request.pipeline_root,
            timing_accumulator=timing,
        )
        action_by_name = {
            action.name: action for action in adapter.actions
        }
        allowed = request.allowed_first_actions
        if allowed is not None:
            if not allowed:
                raise ValueError("allowed first actions cannot be empty")
            if len(set(allowed)) != len(allowed):
                raise ValueError("allowed first actions must be unique")
            unknown = set(allowed) - action_by_name.keys()
            if unknown:
                raise ValueError(
                    f"unknown allowed first actions: {sorted(unknown)}"
                )
        if (
            request.preferred_action is not None
            and request.preferred_action not in action_by_name
        ):
            raise ValueError(
                f"unknown preferred action: {request.preferred_action}"
            )
        if (
            request.preferred_action is None
            and request.preference_reason is not None
        ):
            raise ValueError(
                "preference reason requires a preferred action"
            )

        planned = certificates.get(decision.action)
        fresh_safe_actions = tuple(
            action.name
            for action in adapter.actions
            if (
                certificates[action.name].worst_collisions == 0
                and certificates[action.name].min_clearance >= 0.0
            )
        )
        nonfresh_relaxation = bool(
            decision.viability_constraint_relaxed
            and not decision.viability_fresh_prefix_relaxed
        )
        global_applicable = bool(
            allowed is not None and not nonfresh_relaxation
        )
        fresh_safe_set = set(fresh_safe_actions)
        intersection = tuple(
            action for action in (allowed or ()) if action in fresh_safe_set
        )
        empty_intersection_relaxation = bool(
            global_applicable and not intersection
        )
        if global_applicable and intersection:
            candidate_names = intersection
        elif fresh_safe_actions:
            candidate_names = fresh_safe_actions
        else:
            candidate_names = tuple(
                action.name for action in adapter.actions
            )

        planned_is_candidate_safe = bool(
            planned is not None
            and decision.action in candidate_names
            and planned.worst_collisions == 0
            and planned.min_clearance >= 0.0
        )
        preferred = (
            action_by_name.get(request.preferred_action)
            if (
                request.preferred_action in candidate_names
                and request.preferred_action in fresh_safe_set
                and (not global_applicable or bool(intersection))
            )
            else None
        )
        if preferred is not None:
            selected = preferred
            certificate = certificates[preferred.name]
            reason = (
                "prefer_requested_fresh_global_intersection"
                if global_applicable
                else "prefer_requested_fresh_safe"
            )
        elif planned_is_candidate_safe:
            selected = action_by_name[decision.action]
            certificate = planned
            if empty_intersection_relaxation:
                reason = (
                    "relax_empty_fresh_global_intersection_preserve_planned"
                )
            elif global_applicable:
                reason = "preserve_planned_in_fresh_global_intersection"
            else:
                reason = "preserve_fresh_safe_planned"
        else:
            selected_name = min(
                candidate_names,
                key=lambda action_name: (
                    certificates[action_name].worst_collisions,
                    max(
                        -certificates[action_name].min_clearance,
                        0.0,
                    ),
                    certificates[action_name].cvar_risk,
                    -certificates[action_name].min_clearance,
                    0 if action_name == decision.action else 1,
                    action_name,
                ),
            )
            selected = action_by_name[selected_name]
            certificate = certificates[selected_name]
            if empty_intersection_relaxation:
                reason = (
                    "relax_empty_fresh_global_intersection"
                    if fresh_safe_actions
                    else "relax_empty_fresh_global_intersection_least_bad"
                )
            elif global_applicable:
                reason = "replace_unsafe_from_fresh_global_intersection"
            elif fresh_safe_actions:
                reason = "replace_unsafe_with_fresh_safe"
            else:
                reason = "replace_unsafe_with_least_bad"

        selected_changed = selected.name != decision.action
        repair_by_action = dict(request.viability_repair_volumes)
        recovery_by_action = dict(request.viability_recovery_distances)
        transaction = IssueRecertification(
            planned_action=decision.action,
            global_allowed_actions=allowed,
            global_constraint_applicable=global_applicable,
            fresh_safe_actions=fresh_safe_actions,
            fresh_global_intersection=intersection,
            selected_action=selected.name,
            selection_reason=reason,
            global_constraint_relaxed=bool(
                nonfresh_relaxation or empty_intersection_relaxation
            ),
            planned_certificate=planned,
            selected_certificate=certificate,
            preferred_action=request.preferred_action,
            preference_reason=request.preference_reason,
            preference_applied=preferred is not None,
        )
        issued_mask = (
            adapter.shot_mask
            | (adapter.focus_mask if selected.focused else 0)
            | selected.direction
        )
        if issued_mask & adapter.bomb_mask:
            raise AssertionError("issue transaction cannot emit Bomb")
        issued = replace(
            decision,
            mask=issued_mask,
            action=selected.name,
            bomb=False,
            planned_focus=selected.focused,
            robust_override=(
                decision.robust_override or selected_changed
            ),
            robust_collisions=certificate.worst_collisions,
            robust_min_clearance=certificate.min_clearance,
            robust_cvar_risk=certificate.cvar_risk,
            robust_worst_delay=certificate.worst_delay,
            viability_constrained=bool(
                global_applicable and intersection
            ),
            viability_safe_action_count=len(allowed or ()),
            viability_repair_volume=repair_by_action.get(
                selected.name,
                0,
            ),
            viability_constraint_relaxed=bool(
                nonfresh_relaxation or empty_intersection_relaxation
            ),
            viability_recovery_distance=recovery_by_action.get(
                selected.name
            ),
            viability_control_reserve_valid=bool(
                decision.viability_control_reserve_valid
                and not selected_changed
            ),
            viability_safety_value_preferred=bool(
                request.viability_safety_actions
                and selected.name in request.viability_safety_actions
            ),
            viability_fresh_prefix_filtered=bool(
                global_applicable
                and intersection
                and len(intersection) != len(allowed or ())
            ),
            viability_fresh_prefix_relaxed=(
                empty_intersection_relaxation
            ),
            viability_survival_preferred=bool(
                request.viability_survival_actions
                and selected.name in request.viability_survival_actions
            ),
            issue_action_certificates=tuple(
                certificates[action.name] for action in adapter.actions
            ),
            issue_certificate_timing=timing.snapshot(),
            issue_recertification=transaction,
        )
        self._committed = IssuedDecision.from_decision(issued)
        return self._committed
