"""Planner proposal, certificate, issue, and telemetry value objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LocalCertificateTiming:
    calls: int = 0
    explicit_root_calls: int = 0
    maximum_branch_count: int = 0
    shared_laser_projection_ms: float = 0.0
    validation_ms: float = 0.0
    hazard_projection_ms: float = 0.0
    branch_setup_ms: float = 0.0
    geometry_kernel_ms: float = 0.0
    reduction_ms: float = 0.0
    certificate_total_ms: float = 0.0
    control_prefix_ms: float = 0.0
    planning_bullet_projection_ms: float = 0.0
    beam_search_ms: float = 0.0
    supplemental_beam_ms: float = 0.0
    terminal_threat_ms: float = 0.0
    selection_finalize_ms: float = 0.0


@dataclass(frozen=True)
class RobustActionCertificate:
    action: str
    delay_frames: tuple[int, ...]
    worst_collisions: int
    min_clearance: float
    cvar_risk: float
    worst_delay: int | None
    write_required: bool = True
    pipeline_branch_count: int = 0
    worst_pending_remaining: int | None = None


@dataclass(frozen=True)
class ActionCertificateSet:
    certificates: tuple[RobustActionCertificate, ...] = ()

    def get(self, action: str) -> RobustActionCertificate | None:
        return next(
            (
                certificate
                for certificate in self.certificates
                if certificate.action == action
            ),
            None,
        )

    @property
    def safe_actions(self) -> tuple[str, ...]:
        return tuple(
            certificate.action
            for certificate in self.certificates
            if (
                certificate.worst_collisions == 0
                and certificate.min_clearance >= 0.0
            )
        )


@dataclass(frozen=True)
class IssueRecertification:
    """Auditable fresh/global action transaction at input issue."""

    planned_action: str
    global_allowed_actions: tuple[str, ...] | None
    global_constraint_applicable: bool
    fresh_safe_actions: tuple[str, ...]
    fresh_global_intersection: tuple[str, ...]
    selected_action: str
    selection_reason: str
    global_constraint_relaxed: bool
    planned_certificate: RobustActionCertificate | None
    selected_certificate: RobustActionCertificate


@dataclass(frozen=True)
class DecisionTelemetry:
    """Canonical hard fields and timing, independent of issue ownership."""

    planner_action: str
    planner_mask: int
    bomb: bool
    hard_vector: tuple[int | float | None, ...]
    local_certificate_timing: LocalCertificateTiming
    issue_certificate_timing: LocalCertificateTiming
    issue_recertification: IssueRecertification | None

    @classmethod
    def from_decision(cls, decision: Any) -> DecisionTelemetry:
        return cls(
            planner_action=decision.action,
            planner_mask=decision.mask,
            bomb=decision.bomb,
            hard_vector=(
                decision.robust_collisions,
                decision.robust_min_clearance,
                decision.terminal_threat_collisions,
                decision.terminal_threat_min_clearance,
                decision.local_collisions,
                decision.min_clearance,
                decision.immediate_clearance,
                decision.viability_control_reserve_valid,
            ),
            local_certificate_timing=decision.local_certificate_timing,
            issue_certificate_timing=decision.issue_certificate_timing,
            issue_recertification=decision.issue_recertification,
        )


@dataclass(frozen=True)
class LocalProposal:
    """Planner output before fresh issue-time sensing and certification."""

    decision: Any
    action_certificates: ActionCertificateSet
    telemetry: DecisionTelemetry

    @classmethod
    def from_decision(cls, decision: Any) -> LocalProposal:
        return cls(
            decision=decision,
            action_certificates=ActionCertificateSet(
                decision.issue_action_certificates
            ),
            telemetry=DecisionTelemetry.from_decision(decision),
        )


@dataclass(frozen=True)
class IssuedDecision:
    """Decision after the fresh/global issue transaction has committed."""

    decision: Any
    action_certificates: ActionCertificateSet
    telemetry: DecisionTelemetry
    transaction: IssueRecertification

    @classmethod
    def from_decision(cls, decision: Any) -> IssuedDecision:
        transaction = decision.issue_recertification
        if transaction is None:
            raise ValueError("issued decision requires transaction telemetry")
        return cls(
            decision=decision,
            action_certificates=ActionCertificateSet(
                decision.issue_action_certificates
            ),
            telemetry=DecisionTelemetry.from_decision(decision),
            transaction=transaction,
        )
