#!/usr/bin/env python3
"""Pure trace records for the shadow candidate-verifier service."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from touhou_control.candidate_verifier_service import (
    CandidateVerifierOutcome,
    CandidateVerifierSnapshot,
    CandidateVerifierTarget,
)

if TYPE_CHECKING:
    from th08_live.planner_pass import RobustActionCertificate


def candidate_outcome_record(
    outcome: CandidateVerifierOutcome | None,
    *,
    issued_action: str | None = None,
) -> dict[str, object] | None:
    if outcome is None:
        return None
    label = outcome.state_label
    root = outcome.target.root
    witnesses_by_action = {
        witness.root_action: witness for witness in outcome.action_witnesses
    }

    def witness_record(action: str) -> dict[str, object] | None:
        witness = witnesses_by_action.get(action)
        if witness is None:
            return None
        return {
            "root_action": witness.root_action,
            "candidate_policy": witness.candidate_policy,
            "survival_frames": witness.label.guaranteed_frames,
            "bottleneck_margin": witness.label.bottleneck_margin,
        }

    return {
        "revision": outcome.revision,
        "policy_version": outcome.target.policy_version,
        "root": {
            "frame": root.frame,
            "row": root.row,
            "column": root.column,
            "observed_action": root.observed_action,
            "pending_action": (
                root.pending_command.action if root.pending_command is not None else None
            ),
            "pending_remaining_frames": (
                root.pending_command.remaining_frames
                if root.pending_command is not None
                else ()
            ),
        },
        "status": outcome.status,
        "queue_ms": outcome.queue_ms,
        "elapsed_ms": outcome.elapsed_ms,
        "horizon_frames": outcome.horizon_frames,
        "winning": outcome.winning,
        "survival_frames": label.guaranteed_frames if label is not None else None,
        "bottleneck_margin": label.bottleneck_margin if label is not None else None,
        "best_actions": outcome.best_actions,
        "best_action_witnesses": tuple(
            record
            for action in outcome.best_actions
            if (record := witness_record(action)) is not None
        ),
        "issued_action_label": (
            witness_record(issued_action) if issued_action is not None else None
        ),
        "completed_candidates": outcome.completed_candidates,
        "timed_out_candidates": outcome.timed_out_candidates,
        "unvisited_candidates": outcome.unvisited_candidates,
        "stopped_on_feasibility": outcome.stopped_on_feasibility,
        "budget_exhausted": outcome.budget_exhausted,
        "background_priority_lowered": outcome.background_priority_lowered,
        "stale_at_completion": outcome.stale_at_completion,
        "error": outcome.error,
    }


def candidate_shadow_publications(
    outcome: CandidateVerifierOutcome | None,
    *,
    issue_action_certificates: tuple[RobustActionCertificate, ...],
    issued_action: str,
    issue_frame: int,
    deadline_missed: bool,
    input_override: bool = False,
) -> tuple[dict[str, object], ...]:
    """Publish one-shot audit witnesses without changing the selected input."""

    if (
        outcome is None
        or outcome.status != "feasible"
        or outcome.winning is not True
        or outcome.stale_at_completion
    ):
        return ()
    root = outcome.target.root
    certificates = {
        certificate.action: certificate
        for certificate in issue_action_certificates
    }
    publications = []
    for witness in outcome.action_witnesses:
        if witness.root_action not in outcome.best_actions:
            continue
        certificate = certificates.get(witness.root_action)
        witness_matches_result = bool(
            witness.label == outcome.state_label
            and witness.candidate_policy in outcome.completed_candidates
        )
        certificate_safe = bool(
            certificate is not None
            and certificate.worst_collisions == 0
            and certificate.min_clearance >= 0.0
        )
        status = (
            "witness_result_mismatch"
            if not witness_matches_result
            else (
                "input_override"
                if input_override
                else (
                    "deadline_missed"
                    if deadline_missed
                    else (
                        "issue_certificate_missing"
                        if certificate is None
                        else (
                            "issue_eligible"
                            if certificate_safe
                            else "issue_certificate_unsafe"
                        )
                    )
                )
            )
        )
        publications.append(
            {
                "role": "shadow_no_action_authority",
                "status": status,
                "issue_eligible": status == "issue_eligible",
                "revision": outcome.revision,
                "policy_version": outcome.target.policy_version,
                "root": {
                    "frame": root.frame,
                    "row": root.row,
                    "column": root.column,
                    "observed_action": root.observed_action,
                    "pending_action": (
                        root.pending_command.action
                        if root.pending_command is not None
                        else None
                    ),
                    "pending_remaining_frames": (
                        root.pending_command.remaining_frames
                        if root.pending_command is not None
                        else ()
                    ),
                },
                "root_action": witness.root_action,
                "candidate_policy": witness.candidate_policy,
                "survival_frames": witness.label.guaranteed_frames,
                "bottleneck_margin": witness.label.bottleneck_margin,
                "horizon_frames": outcome.horizon_frames,
                "issued_action": issued_action,
                "would_change_action": witness.root_action != issued_action,
                "valid_for_issue_frame": issue_frame,
                "expires_after_issue_frame": issue_frame,
                "deadline_missed": deadline_missed,
                "input_override": input_override,
                "witness_matches_result": witness_matches_result,
                "issue_certificate": (
                    {
                        "delay_frames": certificate.delay_frames,
                        "worst_collisions": certificate.worst_collisions,
                        "min_clearance": certificate.min_clearance,
                        "cvar_risk": certificate.cvar_risk,
                        "worst_delay": certificate.worst_delay,
                    }
                    if certificate is not None
                    else None
                ),
            }
        )
    return tuple(publications)


def candidate_snapshot_record(
    snapshot: CandidateVerifierSnapshot | None,
) -> dict[str, object] | None:
    if snapshot is None:
        return None
    return {
        "horizon_frames": snapshot.horizon_frames,
        "decision_frame_support": snapshot.decision_frame_support,
        "timeout_ms_per_candidate": snapshot.timeout_ms_per_candidate,
        "total_timeout_ms": snapshot.total_timeout_ms,
        "submitted_revision": snapshot.submitted_revision,
        "completed_revision": snapshot.completed_revision,
        "ready_revision": snapshot.ready_revision,
        "target_running": snapshot.target_running,
        "target_queued": snapshot.target_queued,
        "target_replacement_count": snapshot.target_replacement_count,
        "target_discard_count": snapshot.target_discard_count,
        "stale_completion_count": snapshot.stale_completion_count,
        "lookup_count": snapshot.lookup_count,
        "lookup_hit_count": snapshot.lookup_hit_count,
        "lookup_miss_count": snapshot.lookup_miss_count,
        "latest_outcome": candidate_outcome_record(snapshot.latest_outcome),
    }


def build_candidate_verifier_trace_record(
    *,
    enabled: bool,
    target: CandidateVerifierTarget | None,
    eligibility: str | None,
    submit_revision: int | None,
    submit_ms: float | None,
    lookup_ms: float | None,
    publication_ms: float | None,
    submit_error: str | None,
    lookup_error: str | None,
    outcome: CandidateVerifierOutcome | None,
    snapshot: CandidateVerifierSnapshot | None,
    publications: tuple[dict[str, object], ...],
    issued_mask: int,
    action_name_from_mask: Callable[[int], str],
) -> dict[str, object] | None:
    """Serialize one already-completed shadow verifier observation."""

    if not enabled:
        return None
    root = target.root if target is not None else None
    if submit_error is not None:
        status = "submit_error"
    elif lookup_error is not None:
        status = "lookup_error"
    elif target is None:
        status = (
            "skipped_boolean_viable"
            if eligibility == "boolean_viable"
            else "unavailable"
        )
    elif outcome is not None:
        status = "hit"
    else:
        status = "miss"
    issued_action = action_name_from_mask(issued_mask)
    return {
        "role": "shadow_no_action_authority",
        "status": status,
        "eligibility": eligibility,
        "submit_revision": submit_revision,
        "submit_ms": submit_ms,
        "lookup_ms": lookup_ms,
        "publication_ms": publication_ms,
        "submit_error": submit_error,
        "lookup_error": lookup_error,
        "target": (
            {
                "policy_version": target.policy_version,
                "frame": root.frame,
                "row": root.row,
                "column": root.column,
                "observed_action": root.observed_action,
                "pending_action": (
                    root.pending_command.action
                    if root.pending_command is not None
                    else None
                ),
                "pending_remaining_frames": (
                    root.pending_command.remaining_frames
                    if root.pending_command is not None
                    else ()
                ),
            }
            if target is not None and root is not None
            else None
        ),
        "result": (
            {
                **(
                    candidate_outcome_record(
                        outcome,
                        issued_action=issued_action,
                    )
                    or {}
                ),
                "issued_in_best": issued_action in outcome.best_actions,
            }
            if outcome is not None
            else None
        ),
        "service": candidate_snapshot_record(snapshot),
        "publications": publications,
    }


__all__ = [
    "build_candidate_verifier_trace_record",
    "candidate_outcome_record",
    "candidate_shadow_publications",
    "candidate_snapshot_record",
]
