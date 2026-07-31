"""Causal predecessor into an already-computed future viability policy.

The predecessor is deliberately policy- and game-neutral.  It enumerates the
observable/estimated actuator pipeline for each complete selected action,
advances every pickup branch to one future publication epoch, and queries the
set-valued hazard-space policy at every terminal root.

This module never upgrades incomplete hazard coverage.  Candidate viable and
recovery actions remain auditable when coverage is unknown, but only complete
coverage may produce ``allowed_actions`` and action authority.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping, Protocol

from .hazard_coverage import HazardCoverageAssessment
from .local_pipeline_oracle import (
    LocalPipelineBranch,
    LocalPipelineRoot,
    enumerate_local_pipeline_branches,
)
from .pipeline_identity import VersionIdentity
from .viability_types import SafetyValueQuery, ViabilityQuery


class HazardSpaceSafetyPolicy(Protocol):
    """Signed-clearance query surface required for hard authority."""

    x_axis: object
    y_axis: object
    config: object
    horizon_frames: int

    def query(
        self,
        *,
        frame: int,
        x: float,
        y: float,
        active_action: str,
    ) -> SafetyValueQuery: ...


class RecoveryPolicy(Protocol):
    """Optional losing-state diagnostic query surface."""

    def query(
        self,
        *,
        frame: int,
        x: float,
        y: float,
        active_action: str,
    ) -> ViabilityQuery: ...


@dataclass(frozen=True)
class PrepublicationActionAssessment:
    """Worst terminal-set result for one complete selected action."""

    action: str
    branch_count: int
    viable_branch_count: int
    unavailable_branch_count: int
    worst_certified_margin: float
    worst_recovery_distance: float
    terminal_active_actions: tuple[str, ...]

    @property
    def all_branches_viable(self) -> bool:
        return (
            self.branch_count > 0
            and self.viable_branch_count == self.branch_count
            and self.unavailable_branch_count == 0
        )

    def record(self) -> dict[str, object]:
        return {
            "action": self.action,
            "branch_count": self.branch_count,
            "viable_branch_count": self.viable_branch_count,
            "unavailable_branch_count": self.unavailable_branch_count,
            "all_branches_viable": self.all_branches_viable,
            "worst_certified_margin": (
                self.worst_certified_margin
                if math.isfinite(self.worst_certified_margin)
                else None
            ),
            "worst_recovery_distance": (
                self.worst_recovery_distance
                if math.isfinite(self.worst_recovery_distance)
                else None
            ),
            "terminal_active_actions": list(self.terminal_active_actions),
        }


@dataclass(frozen=True)
class CausalPrepublicationFilter:
    """Auditable hard/diagnostic result for one future policy epoch."""

    enabled: bool
    state_eligible: bool
    coverage_complete: bool
    authority_eligible: bool
    applicable: bool
    reason: str
    allowed_actions: tuple[str, ...] | None
    candidate_viable_actions: tuple[str, ...]
    recovery_actions: tuple[str, ...]
    current_frame: int | None
    publication_frame: int | None
    publication_lead_frames: int | None
    policy_query_frame: int | None
    pickup_delay_frames: tuple[int, ...]
    prefix_certified_frames: int | None
    prefix_safe_actions: tuple[str, ...] | None
    root_active_action: str | None
    root_held_desired_action: str | None
    root_pending_action: str | None
    coverage: HazardCoverageAssessment | None
    required_hazard_version: VersionIdentity | None
    actions: tuple[PrepublicationActionAssessment, ...] = ()

    def record(self) -> dict[str, object]:
        return {
            "schema": "causal-prepublication-viability-predecessor-v1",
            "role": (
                "hazard_space_prepublication_action_authority"
                if self.authority_eligible
                else "no_action_authority"
            ),
            "enabled": self.enabled,
            "state_eligible": self.state_eligible,
            "coverage_complete": self.coverage_complete,
            "authority_eligible": self.authority_eligible,
            "applicable": self.applicable,
            "reason": self.reason,
            "allowed_actions": self.allowed_actions,
            "candidate_viable_actions": self.candidate_viable_actions,
            "recovery_actions": self.recovery_actions,
            "current_frame": self.current_frame,
            "publication_frame": self.publication_frame,
            "publication_lead_frames": self.publication_lead_frames,
            "policy_query_frame": self.policy_query_frame,
            "pickup_delay_frames": self.pickup_delay_frames,
            "prefix_certified_frames": self.prefix_certified_frames,
            "prefix_safe_actions": self.prefix_safe_actions,
            "pipeline_root": {
                "active_action": self.root_active_action,
                "held_desired_action": self.root_held_desired_action,
                "pending_action": self.root_pending_action,
            },
            "pickup_clock_authority": (
                "every_physical_pickup_order_before_publication_"
                "complete_mask_hold_is_no_write"
            ),
            "observation_merge": (
                "all_hidden_pickup_branches_universal_before_future_choice"
            ),
            "terminal_set": (
                "action_conditioned_hazard_space_viability_not_scalar_reserve"
            ),
            "coverage": (
                self.coverage.record() if self.coverage is not None else None
            ),
            "required_hazard_version": (
                self.required_hazard_version.record()
                if self.required_hazard_version is not None
                else None
            ),
            "actions": [action.record() for action in self.actions],
        }


def unavailable_causal_prepublication_filter(
    *,
    enabled: bool,
    reason: str,
    state_eligible: bool = False,
    pickup_delay_frames: tuple[int, ...] = (),
    coverage: HazardCoverageAssessment | None = None,
    required_hazard_version: VersionIdentity | None = None,
) -> CausalPrepublicationFilter:
    """Return an explicit no-authority result."""

    if not reason:
        raise ValueError("unavailable reason must not be empty")
    return CausalPrepublicationFilter(
        enabled=enabled,
        state_eligible=state_eligible,
        coverage_complete=bool(coverage is not None and coverage.complete),
        authority_eligible=False,
        applicable=False,
        reason=reason,
        allowed_actions=None,
        candidate_viable_actions=(),
        recovery_actions=(),
        current_frame=None,
        publication_frame=None,
        publication_lead_frames=None,
        policy_query_frame=None,
        pickup_delay_frames=pickup_delay_frames,
        prefix_certified_frames=None,
        prefix_safe_actions=None,
        root_active_action=None,
        root_held_desired_action=None,
        root_pending_action=None,
        coverage=coverage,
        required_hazard_version=required_hazard_version,
    )


def _axis_bounds(
    policy: HazardSpaceSafetyPolicy,
) -> tuple[float, float, float, float]:
    try:
        left = float(policy.x_axis[0])  # type: ignore[index]
        right = float(policy.x_axis[-1])  # type: ignore[index]
        top = float(policy.y_axis[0])  # type: ignore[index]
        bottom = float(policy.y_axis[-1])  # type: ignore[index]
    except (IndexError, TypeError, ValueError) as error:
        raise ValueError("future policy axes are unavailable") from error
    if not left < right or not top < bottom:
        raise ValueError("future policy axes must have positive area")
    return left, right, top, bottom


def _terminal_pending(
    branch: LocalPipelineBranch,
    *,
    root: LocalPipelineRoot,
    horizon_frames: int,
) -> bool:
    if branch.write_required:
        assert branch.new_delay is not None
        return horizon_frames <= branch.new_delay
    if root.pending_action is None:
        return False
    assert branch.older_remaining is not None
    return horizon_frames <= branch.older_remaining


def _query_recovery_distance(
    query: ViabilityQuery,
    *,
    held_action_pending: str | None,
) -> float:
    if not query.available:
        return math.inf
    if held_action_pending is not None:
        if held_action_pending in query.safe_actions:
            return 0.0
        return query.recovery_distance(held_action_pending)
    if query.state_viable:
        return 0.0
    distances = tuple(
        distance
        for _, distance in query.recovery_distances
        if math.isfinite(distance)
    )
    return min(distances, default=math.inf)


def build_causal_prepublication_filter(
    *,
    enabled: bool,
    root: LocalPipelineRoot | None,
    selected_actions: tuple[str, ...],
    action_velocities: Mapping[str, tuple[float, float]],
    delay_frames: tuple[int, ...],
    current_frame: int,
    publication_frame: int,
    prefix_certified_frames: int,
    prefix_safe_actions: tuple[str, ...] | None,
    start_x: float,
    start_y: float,
    future_safety_policy: HazardSpaceSafetyPolicy | None,
    future_recovery_policy: RecoveryPolicy | None,
    hazard_coverage: HazardCoverageAssessment | None,
    required_hazard_version: VersionIdentity | None = None,
) -> CausalPrepublicationFilter:
    """Compute the robust predecessor of one future hazard-space kernel.

    ``publication_frame`` is the first physical frame governed by
    ``future_safety_policy``.  The signed policy is queried at layer/frame
    zero after every action-conditioned pickup branch reaches that epoch.
    Every certificate subtracts the exact live-to-lattice projection error.
    A command still pending at the epoch is accepted only when that exact
    held command has positive certified action value; this preserves
    no-write semantics instead of resampling delay.
    """

    if not enabled:
        return unavailable_causal_prepublication_filter(
            enabled=False,
            reason="disabled",
            pickup_delay_frames=delay_frames,
            coverage=hazard_coverage,
            required_hazard_version=required_hazard_version,
        )
    if root is None:
        return unavailable_causal_prepublication_filter(
            enabled=True,
            reason="pipeline_root_unavailable",
            state_eligible=True,
            pickup_delay_frames=delay_frames,
            coverage=hazard_coverage,
            required_hazard_version=required_hazard_version,
        )
    if future_safety_policy is None:
        return unavailable_causal_prepublication_filter(
            enabled=True,
            reason="future_safety_policy_unavailable",
            state_eligible=True,
            pickup_delay_frames=delay_frames,
            coverage=hazard_coverage,
            required_hazard_version=required_hazard_version,
        )
    if (
        not selected_actions
        or len(set(selected_actions)) != len(selected_actions)
    ):
        raise ValueError("selected actions must be nonempty and unique")
    if (
        not delay_frames
        or tuple(sorted(set(delay_frames))) != delay_frames
        or delay_frames[0] < 0
    ):
        raise ValueError(
            "delay support must be sorted, unique, and nonnegative"
        )
    if current_frame < 0 or publication_frame <= current_frame:
        return unavailable_causal_prepublication_filter(
            enabled=True,
            reason="future_publication_epoch_unavailable",
            state_eligible=True,
            pickup_delay_frames=delay_frames,
            coverage=hazard_coverage,
            required_hazard_version=required_hazard_version,
        )
    if prefix_certified_frames < 0:
        raise ValueError("prefix certificate horizon cannot be negative")
    if not math.isfinite(start_x) or not math.isfinite(start_y):
        raise ValueError("player root must be finite")

    required_actions = {
        root.active_action,
        root.held_desired_action,
        *selected_actions,
    }
    if root.pending_action is not None:
        required_actions.add(root.pending_action)
    missing = required_actions - action_velocities.keys()
    if missing:
        raise ValueError(f"missing action velocities: {sorted(missing)}")

    left, right, top, bottom = _axis_bounds(future_safety_policy)
    try:
        required_clearance = float(
            future_safety_policy.config.required_clearance
        )
    except (AttributeError, TypeError, ValueError) as error:
        raise ValueError(
            "future safety policy clearance threshold is unavailable"
        ) from error
    if not math.isfinite(required_clearance):
        raise ValueError("future safety clearance threshold must be finite")
    if not left <= start_x <= right or not top <= start_y <= bottom:
        return unavailable_causal_prepublication_filter(
            enabled=True,
            reason="player_root_outside_future_policy",
            state_eligible=True,
            pickup_delay_frames=delay_frames,
            coverage=hazard_coverage,
            required_hazard_version=required_hazard_version,
        )

    lead_frames = publication_frame - current_frame
    assessments: list[PrepublicationActionAssessment] = []
    for selected_action in selected_actions:
        branches = enumerate_local_pipeline_branches(
            root=root,
            selected_action=selected_action,
            delay_frames=delay_frames,
            horizon_frames=lead_frames,
        )
        viable_count = 0
        unavailable_count = 0
        certified_margins: list[float] = []
        recovery_distances: list[float] = []
        terminal_actions: set[str] = set()
        for branch in branches:
            x = float(start_x)
            y = float(start_y)
            for active_action in branch.active_actions:
                velocity_x, velocity_y = action_velocities[active_action]
                x = min(right, max(left, x + velocity_x))
                y = min(bottom, max(top, y + velocity_y))
            terminal_active = branch.active_actions[-1]
            terminal_actions.add(terminal_active)
            safety_query = future_safety_policy.query(
                frame=0,
                x=x,
                y=y,
                active_action=terminal_active,
            )
            pending_action = (
                selected_action
                if _terminal_pending(
                    branch,
                    root=root,
                    horizon_frames=lead_frames,
                )
                else None
            )
            if pending_action is not None:
                certified_margin = (
                    safety_query.action_value(pending_action)
                    - safety_query.position_error
                    - required_clearance
                    if safety_query.available
                    and safety_query.action_values
                    else -math.inf
                )
            else:
                certified_margin = (
                    safety_query.state_value
                    - safety_query.position_error
                    - required_clearance
                    if safety_query.available
                    else -math.inf
                )
            branch_viable = bool(
                safety_query.available and certified_margin > 0.0
            )
            viable_count += int(branch_viable)
            unavailable_count += int(
                not safety_query.available
                or (
                    pending_action is not None
                    and not safety_query.action_values
                )
            )
            certified_margins.append(certified_margin)
            if future_recovery_policy is not None:
                recovery_distances.append(
                    _query_recovery_distance(
                        future_recovery_policy.query(
                            frame=0,
                            x=x,
                            y=y,
                            active_action=terminal_active,
                        ),
                        held_action_pending=pending_action,
                    )
                )
        assessments.append(
            PrepublicationActionAssessment(
                action=selected_action,
                branch_count=len(branches),
                viable_branch_count=viable_count,
                unavailable_branch_count=unavailable_count,
                worst_certified_margin=min(
                    certified_margins,
                    default=-math.inf,
                ),
                worst_recovery_distance=max(
                    recovery_distances,
                    default=math.inf,
                ),
                terminal_active_actions=tuple(sorted(terminal_actions)),
            )
        )

    terminal_viable = tuple(
        assessment.action
        for assessment in assessments
        if assessment.all_branches_viable
    )
    prefix_available = bool(
        prefix_safe_actions is not None
        and prefix_certified_frames >= lead_frames
    )
    prefix_set = set(prefix_safe_actions or ())
    candidate_viable = tuple(
        action
        for action in terminal_viable
        if prefix_available and action in prefix_set
    )
    finite_margins = tuple(
        assessment
        for assessment in assessments
        if math.isfinite(assessment.worst_certified_margin)
    )
    recovery_actions: tuple[str, ...] = ()
    if finite_margins:
        best_margin = max(
            assessment.worst_certified_margin
            for assessment in finite_margins
        )
        recovery_actions = tuple(
            assessment.action
            for assessment in finite_margins
            if assessment.worst_certified_margin == best_margin
        )
    else:
        finite_recovery = tuple(
            assessment
            for assessment in assessments
            if math.isfinite(assessment.worst_recovery_distance)
        )
        if finite_recovery:
            best_recovery = min(
                assessment.worst_recovery_distance
                for assessment in finite_recovery
            )
            recovery_actions = tuple(
                assessment.action
                for assessment in finite_recovery
                if assessment.worst_recovery_distance == best_recovery
            )

    coverage_complete = bool(
        hazard_coverage is not None and hazard_coverage.complete
    )
    required_coverage_horizon = (
        publication_frame + future_safety_policy.horizon_frames
    )
    coverage_interval_matches = bool(
        hazard_coverage is not None
        and hazard_coverage.root_frame == current_frame
        and hazard_coverage.horizon_frame >= required_coverage_horizon
    )
    coverage_version_matches = bool(
        coverage_complete
        and coverage_interval_matches
        and required_hazard_version is not None
        and hazard_coverage is not None
        and hazard_coverage.slabs
        and all(
            slab.version == required_hazard_version
            for slab in hazard_coverage.slabs
        )
    )
    authority_eligible = bool(
        coverage_complete
        and coverage_interval_matches
        and coverage_version_matches
        and prefix_available
    )
    allowed_actions = candidate_viable if authority_eligible else None
    applicable = bool(authority_eligible and candidate_viable)
    if not prefix_available:
        reason = "prefix_hazard_certificate_unavailable"
    elif not coverage_interval_matches:
        reason = "future_hazard_interval_mismatch"
    elif not coverage_complete:
        reason = "future_hazard_coverage_unknown"
    elif not coverage_version_matches:
        reason = "future_hazard_version_mismatch"
    elif not candidate_viable:
        reason = "prepublication_viable_predecessor_empty"
    elif len(candidate_viable) == len(selected_actions):
        reason = "all_actions_reach_future_viable_set"
    else:
        reason = "prepublication_viable_actions_found"

    return CausalPrepublicationFilter(
        enabled=True,
        state_eligible=True,
        coverage_complete=coverage_complete,
        authority_eligible=authority_eligible,
        applicable=applicable,
        reason=reason,
        allowed_actions=allowed_actions,
        candidate_viable_actions=candidate_viable,
        recovery_actions=recovery_actions,
        current_frame=current_frame,
        publication_frame=publication_frame,
        publication_lead_frames=lead_frames,
        policy_query_frame=0,
        pickup_delay_frames=delay_frames,
        prefix_certified_frames=prefix_certified_frames,
        prefix_safe_actions=prefix_safe_actions,
        root_active_action=root.active_action,
        root_held_desired_action=root.held_desired_action,
        root_pending_action=root.pending_action,
        coverage=hazard_coverage,
        required_hazard_version=required_hazard_version,
        actions=tuple(assessments),
    )


__all__ = [
    "CausalPrepublicationFilter",
    "HazardSpaceSafetyPolicy",
    "PrepublicationActionAssessment",
    "RecoveryPolicy",
    "build_causal_prepublication_filter",
    "unavailable_causal_prepublication_filter",
]
