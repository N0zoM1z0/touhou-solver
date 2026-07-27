"""Immutable records and canonical payloads for partial witnesses."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Literal

from ..reachability_oracle import SurvivalLabel


POST_FINITE_MODEL_EMPTY_PARTIAL_WITNESS = (
    "POST_FINITE_MODEL_EMPTY_PARTIAL_WITNESS"
)
PARTIAL_WITNESS_ON_UNRESOLVED = "PARTIAL_WITNESS_ON_UNRESOLVED"
FINITE_MODEL_FEASIBILITY_WITNESS = "FINITE_MODEL_FEASIBILITY_WITNESS"
NO_POSITIVE_ATTAINABLE_WITNESS = "NO_POSITIVE_ATTAINABLE_WITNESS"


@dataclass(frozen=True)
class PartialWitnessRoot:
    """Exact public information state used by one witness portfolio."""

    frame: int
    row: int
    column: int
    observed_action: str
    pending_action: str | None
    remaining_delay_support: tuple[int, ...]


@dataclass(frozen=True)
class WorstNatureBranchStep:
    """One deterministic worst observation-compatible nature branch."""

    frame: int
    row: int
    column: int
    active_action: str
    pending_action: str | None
    remaining_delay_support: tuple[int, ...]
    selected_action: str
    hidden_remaining_before: int
    pickup_delay: int | None
    cadence: int
    prefix_bottleneck_margin: float
    state_label: SurvivalLabel
    failed: bool
    successor_frame: int | None
    successor_row: int | None
    successor_column: int | None
    successor_active_action: str | None
    successor_pending_action: str | None
    successor_remaining_delay_support: tuple[int, ...]
    successor_label: SurvivalLabel | None
    merged_hidden_branch_count: int


@dataclass(frozen=True)
class StationaryPolicyWitness:
    """A completed attainable label and worst path for one root action."""

    problem_digest: str
    root: PartialWitnessRoot
    root_action: str
    continuation_action: str
    policy_digest: str
    label: SurvivalLabel
    worst_branch: tuple[WorstNatureBranchStep, ...]
    evaluated_state_count: int
    witness_digest: str


@dataclass(frozen=True)
class StationaryWitnessPortfolio:
    """Best completed stationary witness for every unrestricted root action."""

    mode: str
    unrestricted_status: Literal["losing", "unresolved"]
    problem_digest: str
    root: PartialWitnessRoot
    continuation_candidates: tuple[str, ...]
    state_label: SurvivalLabel
    best_actions: tuple[str, ...]
    action_witnesses: tuple[StationaryPolicyWitness, ...]
    complete_root_actions: tuple[str, ...]
    portfolio_digest: str

    @property
    def complete(self) -> bool:
        witness_actions = tuple(
            witness.root_action for witness in self.action_witnesses
        )
        return (
            bool(self.complete_root_actions)
            and len(set(self.complete_root_actions))
            == len(self.complete_root_actions)
            and witness_actions == self.complete_root_actions
        )


def canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def float_key(value: float) -> str:
    return float(value).hex()


def label_payload(label: SurvivalLabel) -> dict[str, object]:
    return {
        "guaranteed_frames": label.guaranteed_frames,
        "bottleneck_margin_hex": float_key(label.bottleneck_margin),
    }


def root_payload(root: PartialWitnessRoot) -> dict[str, object]:
    return {
        "frame": root.frame,
        "row": root.row,
        "column": root.column,
        "observed_action": root.observed_action,
        "pending_action": root.pending_action,
        "remaining_delay_support": root.remaining_delay_support,
    }


def step_payload(step: WorstNatureBranchStep) -> dict[str, object]:
    return {
        "frame": step.frame,
        "row": step.row,
        "column": step.column,
        "active_action": step.active_action,
        "pending_action": step.pending_action,
        "remaining_delay_support": step.remaining_delay_support,
        "selected_action": step.selected_action,
        "hidden_remaining_before": step.hidden_remaining_before,
        "pickup_delay": step.pickup_delay,
        "cadence": step.cadence,
        "prefix_bottleneck_margin_hex": float_key(
            step.prefix_bottleneck_margin
        ),
        "state_label": label_payload(step.state_label),
        "failed": step.failed,
        "successor_frame": step.successor_frame,
        "successor_row": step.successor_row,
        "successor_column": step.successor_column,
        "successor_active_action": step.successor_active_action,
        "successor_pending_action": step.successor_pending_action,
        "successor_remaining_delay_support": (
            step.successor_remaining_delay_support
        ),
        "successor_label": (
            None
            if step.successor_label is None
            else label_payload(step.successor_label)
        ),
        "merged_hidden_branch_count": step.merged_hidden_branch_count,
    }


def policy_payload(
    root_action: str,
    continuation_action: str,
) -> dict[str, object]:
    return {
        "schema": "touhou-stationary-causal-policy-v1",
        "root_action": root_action,
        "continuation_action": continuation_action,
    }


def witness_payload(
    witness: StationaryPolicyWitness,
) -> dict[str, object]:
    policy = policy_payload(
        witness.root_action,
        witness.continuation_action,
    )
    return {
        "schema": "touhou-stationary-partial-witness-v1",
        "problem_digest": witness.problem_digest,
        "root": root_payload(witness.root),
        "policy": policy,
        "policy_digest": witness.policy_digest,
        "label": label_payload(witness.label),
        "worst_branch": [
            step_payload(step) for step in witness.worst_branch
        ],
        "evaluated_state_count": witness.evaluated_state_count,
    }
