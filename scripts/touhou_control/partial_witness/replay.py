"""Structural replay for a retained stationary witness path."""

from __future__ import annotations

from ..reachability_oracle import SurvivalLabel
from .types import (
    StationaryPolicyWitness,
    canonical_sha256,
    policy_payload,
    witness_payload,
)


def replay_stationary_worst_branch(
    witness: StationaryPolicyWitness,
) -> SurvivalLabel:
    """Validate digests, policy choices, state links, and nested labels."""

    policy = policy_payload(
        witness.root_action,
        witness.continuation_action,
    )
    if canonical_sha256(policy) != witness.policy_digest:
        raise ValueError("stationary policy digest does not replay")
    if canonical_sha256(witness_payload(witness)) != witness.witness_digest:
        raise ValueError("stationary witness digest does not replay")
    if not witness.worst_branch:
        return witness.label

    for index, step in enumerate(witness.worst_branch):
        expected_action = (
            witness.root_action
            if index == 0
            else witness.continuation_action
        )
        if step.selected_action != expected_action:
            raise ValueError("worst branch violates the stationary policy")
        if index == 0 and (
            step.frame,
            step.row,
            step.column,
            step.active_action,
            step.pending_action,
            step.remaining_delay_support,
        ) != (
            witness.root.frame,
            witness.root.row,
            witness.root.column,
            witness.root.observed_action,
            witness.root.pending_action,
            witness.root.remaining_delay_support,
        ):
            raise ValueError("worst branch does not start at the witness root")
        if index == 0 and step.state_label != witness.label:
            raise ValueError("root worst-branch label differs from witness")
        if step.failed:
            if step.successor_label is not None:
                raise ValueError("failed branch cannot retain a successor label")
            if index + 1 != len(witness.worst_branch):
                raise ValueError("failed branch must terminate the worst path")
            continue

        successor = step.successor_label
        if (
            successor is None
            or step.successor_frame is None
            or step.successor_row is None
            or step.successor_column is None
            or step.successor_active_action is None
        ):
            raise ValueError("successful branch is missing its successor")
        expected = SurvivalLabel(
            step.successor_frame
            - step.frame
            + successor.guaranteed_frames,
            min(
                step.prefix_bottleneck_margin,
                successor.bottleneck_margin,
            ),
        )
        if expected != step.state_label:
            raise ValueError("worst-branch recurrence does not replay")
        if index + 1 < len(witness.worst_branch):
            child = witness.worst_branch[index + 1]
            if child.state_label != successor or (
                child.frame,
                child.row,
                child.column,
                child.active_action,
                child.pending_action,
                child.remaining_delay_support,
            ) != (
                step.successor_frame,
                step.successor_row,
                step.successor_column,
                step.successor_active_action,
                step.successor_pending_action,
                step.successor_remaining_delay_support,
            ):
                raise ValueError("worst-branch child label is inconsistent")
    return witness.worst_branch[0].state_label
