"""All-root-action stationary witness portfolio construction."""

from __future__ import annotations

from typing import Literal

from ..query_survival import PendingCommand, SurvivalQueryProblem
from .digest import stationary_witness_problem_digest
from .stationary import _build_stationary_policy_witness
from .types import (
    FINITE_MODEL_FEASIBILITY_WITNESS,
    NO_POSITIVE_ATTAINABLE_WITNESS,
    PARTIAL_WITNESS_ON_UNRESOLVED,
    POST_FINITE_MODEL_EMPTY_PARTIAL_WITNESS,
    StationaryPolicyWitness,
    StationaryWitnessPortfolio,
    canonical_sha256,
    label_payload,
    root_payload,
)


def build_stationary_witness_portfolio(
    *,
    problem: SurvivalQueryProblem,
    decision_frame_support: tuple[int, ...],
    continuation_candidates: tuple[str, ...],
    frame: int,
    row: int,
    column: int,
    observed_action: str,
    unrestricted_status: Literal["losing", "unresolved"],
    pending_command: PendingCommand | None = None,
) -> StationaryWitnessPortfolio:
    """Evaluate all root actions and retain the best stationary lower witness."""

    if unrestricted_status not in ("losing", "unresolved"):
        raise ValueError("unrestricted status must be losing or unresolved")
    known_actions = tuple(action.name for action in problem.actions)
    if (
        not continuation_candidates
        or len(set(continuation_candidates))
        != len(continuation_candidates)
        or any(
            candidate not in known_actions
            for candidate in continuation_candidates
        )
    ):
        raise ValueError(
            "continuation candidates must be unique known actions"
        )

    problem_digest = stationary_witness_problem_digest(
        problem,
        decision_frame_support=decision_frame_support,
    )
    best_by_action: list[StationaryPolicyWitness] = []
    for root_action in known_actions:
        candidates = tuple(
            _build_stationary_policy_witness(
                problem=problem,
                decision_frame_support=decision_frame_support,
                frame=frame,
                row=row,
                column=column,
                observed_action=observed_action,
                root_action=root_action,
                continuation_action=continuation_action,
                pending_command=pending_command,
                problem_digest=problem_digest,
            )
            for continuation_action in continuation_candidates
        )
        best_by_action.append(
            max(
                enumerate(candidates),
                key=lambda item: (item[1].label, -item[0]),
            )[1]
        )

    action_witnesses = tuple(best_by_action)
    state_label = max(
        witness.label for witness in action_witnesses
    )
    best_actions = tuple(
        witness.root_action
        for witness in action_witnesses
        if witness.label == state_label
    )
    remaining_frames = problem.horizon_frames - frame
    if (
        state_label.guaranteed_frames == remaining_frames
        and state_label.bottleneck_margin > 0.0
    ):
        mode = FINITE_MODEL_FEASIBILITY_WITNESS
    elif state_label.guaranteed_frames <= 0:
        mode = NO_POSITIVE_ATTAINABLE_WITNESS
    elif unrestricted_status == "losing":
        mode = POST_FINITE_MODEL_EMPTY_PARTIAL_WITNESS
    else:
        mode = PARTIAL_WITNESS_ON_UNRESOLVED

    root = action_witnesses[0].root
    complete_root_actions = tuple(
        witness.root_action for witness in action_witnesses
    )
    portfolio_payload = {
        "schema": "touhou-stationary-witness-portfolio-v1",
        "mode": mode,
        "unrestricted_status": unrestricted_status,
        "problem_digest": problem_digest,
        "root": root_payload(root),
        "continuation_candidates": continuation_candidates,
        "state_label": label_payload(state_label),
        "best_actions": best_actions,
        "complete_root_actions": complete_root_actions,
        "action_witness_digests": [
            witness.witness_digest for witness in action_witnesses
        ],
    }
    return StationaryWitnessPortfolio(
        mode=mode,
        unrestricted_status=unrestricted_status,
        problem_digest=problem_digest,
        root=root,
        continuation_candidates=continuation_candidates,
        state_label=state_label,
        best_actions=best_actions,
        action_witnesses=action_witnesses,
        complete_root_actions=complete_root_actions,
        portfolio_digest=canonical_sha256(portfolio_payload),
    )
