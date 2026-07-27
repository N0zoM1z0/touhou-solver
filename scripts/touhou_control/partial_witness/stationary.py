"""Exact scalar recurrence for one stationary continuation policy."""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from functools import lru_cache

from ..query_survival import PendingCommand, SurvivalQueryProblem
from ..reachability_oracle import SurvivalLabel
from ..variable_cadence_oracle import _HiddenState, _prepare_problem
from .digest import stationary_witness_problem_digest
from .types import (
    PartialWitnessRoot,
    StationaryPolicyWitness,
    WorstNatureBranchStep,
    canonical_sha256,
    policy_payload,
    witness_payload,
)


@dataclass(frozen=True)
class _NatureInput:
    hidden_remaining: int
    cadence: int
    pickup_delay: int | None

    @property
    def sort_key(self) -> tuple[int, int, int]:
        return (
            self.hidden_remaining,
            self.cadence,
            -1 if self.pickup_delay is None else self.pickup_delay,
        )


@dataclass(frozen=True)
class _BranchResult:
    label: SurvivalLabel
    nature: _NatureInput
    prefix_margin: float
    failed: bool
    successor_key: tuple[int, int, int, int, int, tuple[int, ...]] | None
    successor_label: SurvivalLabel | None
    hidden_branch_count: int
    child_path: tuple[WorstNatureBranchStep, ...]

    @property
    def tie_key(self) -> tuple[object, ...]:
        return (
            self.nature.sort_key,
            self.failed,
            self.successor_key or (),
        )


def build_stationary_policy_witness(
    *,
    problem: SurvivalQueryProblem,
    decision_frame_support: tuple[int, ...],
    frame: int,
    row: int,
    column: int,
    observed_action: str,
    root_action: str,
    continuation_action: str,
    pending_command: PendingCommand | None = None,
    problem_digest: str | None = None,
) -> StationaryPolicyWitness:
    """Solve and retain one exact stationary causal policy witness."""

    computed_digest = stationary_witness_problem_digest(
        problem,
        decision_frame_support=decision_frame_support,
    )
    if problem_digest is not None and problem_digest != computed_digest:
        raise ValueError("problem digest does not match the supplied problem")
    return _build_stationary_policy_witness(
        problem=problem,
        decision_frame_support=decision_frame_support,
        frame=frame,
        row=row,
        column=column,
        observed_action=observed_action,
        root_action=root_action,
        continuation_action=continuation_action,
        pending_command=pending_command,
        problem_digest=computed_digest,
    )


def _build_stationary_policy_witness(
    *,
    problem: SurvivalQueryProblem,
    decision_frame_support: tuple[int, ...],
    frame: int,
    row: int,
    column: int,
    observed_action: str,
    root_action: str,
    continuation_action: str,
    pending_command: PendingCommand | None,
    problem_digest: str,
) -> StationaryPolicyWitness:
    (
        oracle,
        active_index,
        pending_index,
        pending_support,
    ) = _prepare_problem(
        x_axis=problem.x_axis,
        y_axis=problem.y_axis,
        clearance_volume=problem.clearance_volume,
        actions=problem.actions,
        delay_frames=problem.delay_frames,
        decision_frame_support=decision_frame_support,
        config=problem.config,
        start_frame=frame,
        row=row,
        column=column,
        observed_action=observed_action,
        pending_command=pending_command,
    )
    action_indices = {
        action.name: index for index, action in enumerate(oracle.actions)
    }
    try:
        root_action_index = action_indices[root_action]
        continuation_action_index = action_indices[continuation_action]
    except KeyError as error:
        raise ValueError(f"witness action is unknown: {error.args[0]}") from error

    root = PartialWitnessRoot(
        frame=frame,
        row=row,
        column=column,
        observed_action=observed_action,
        pending_action=(
            None if pending_command is None else pending_command.action
        ),
        remaining_delay_support=pending_support,
    )
    policy = policy_payload(root_action, continuation_action)
    policy_digest = canonical_sha256(policy)

    def action_name(index: int) -> str:
        return oracle.actions[index].name

    @lru_cache(maxsize=None)
    def solve(
        state_frame: int,
        state_row: int,
        state_column: int,
        active: int,
        pending: int,
        remaining_support: tuple[int, ...],
        public_root: bool,
    ) -> tuple[
        SurvivalLabel,
        tuple[WorstNatureBranchStep, ...],
    ]:
        representative = _HiddenState(
            state_frame,
            state_row,
            state_column,
            active,
            pending,
            remaining_support[0],
        )
        current_margin = oracle.margin(representative)
        if state_frame == oracle.horizon_frame or current_margin <= 0.0:
            return SurvivalLabel(0, current_margin), ()

        selected = (
            root_action_index if public_root else continuation_action_index
        )
        desired = pending if pending >= 0 else active
        selected_delays: tuple[int | None, ...] = (
            (None,) if selected == desired else oracle.delay_frames
        )
        failed: list[_BranchResult] = []
        grouped: dict[
            tuple[int, int, int, int, int],
            tuple[set[int], float, _NatureInput, int],
        ] = {}
        for remaining in remaining_support:
            hidden = _HiddenState(
                state_frame,
                state_row,
                state_column,
                active,
                pending,
                remaining,
            )
            for cadence in oracle.cadence_frames:
                for delay in selected_delays:
                    nature = _NatureInput(remaining, cadence, delay)
                    transition = oracle.transition(
                        hidden,
                        selected=selected,
                        delay=delay,
                        cadence=cadence,
                    )
                    if transition.failed_label is not None:
                        failed.append(
                            _BranchResult(
                                label=transition.failed_label,
                                nature=nature,
                                prefix_margin=(
                                    transition.bottleneck_margin
                                ),
                                failed=True,
                                successor_key=None,
                                successor_label=None,
                                hidden_branch_count=1,
                                child_path=(),
                            )
                        )
                        continue
                    successor = transition.successor
                    assert successor is not None
                    observation = (
                        successor.frame,
                        successor.row,
                        successor.column,
                        successor.active,
                        successor.pending,
                    )
                    (
                        successor_support,
                        prefix_margin,
                        prefix_nature,
                        branch_count,
                    ) = grouped.get(
                        observation,
                        (set(), math.inf, nature, 0),
                    )
                    successor_support.add(
                        successor.remaining
                        if successor.pending >= 0
                        else 0
                    )
                    candidate_margin = transition.bottleneck_margin
                    if (
                        candidate_margin < prefix_margin
                        or (
                            candidate_margin == prefix_margin
                            and nature.sort_key < prefix_nature.sort_key
                        )
                    ):
                        prefix_margin = candidate_margin
                        prefix_nature = nature
                    grouped[observation] = (
                        successor_support,
                        prefix_margin,
                        prefix_nature,
                        branch_count + 1,
                    )

        branches = list(failed)
        for observation in sorted(grouped):
            (
                successor_support_set,
                prefix_margin,
                prefix_nature,
                hidden_branch_count,
            ) = grouped[observation]
            successor_support = tuple(sorted(successor_support_set))
            successor_key = (*observation, successor_support)
            successor_label, child_path = solve(
                *observation,
                successor_support,
                False,
            )
            successor_frame = observation[0]
            branch_label = SurvivalLabel(
                successor_frame
                - state_frame
                + successor_label.guaranteed_frames,
                min(
                    prefix_margin,
                    successor_label.bottleneck_margin,
                ),
            )
            branches.append(
                _BranchResult(
                    label=branch_label,
                    nature=prefix_nature,
                    prefix_margin=prefix_margin,
                    failed=False,
                    successor_key=successor_key,
                    successor_label=successor_label,
                    hidden_branch_count=hidden_branch_count,
                    child_path=child_path,
                )
            )

        worst = min(branches, key=lambda branch: (branch.label, branch.tie_key))
        successor_key = worst.successor_key
        step = WorstNatureBranchStep(
            frame=state_frame,
            row=state_row,
            column=state_column,
            active_action=action_name(active),
            pending_action=(
                None if pending < 0 else action_name(pending)
            ),
            remaining_delay_support=remaining_support,
            selected_action=action_name(selected),
            hidden_remaining_before=worst.nature.hidden_remaining,
            pickup_delay=worst.nature.pickup_delay,
            cadence=worst.nature.cadence,
            prefix_bottleneck_margin=worst.prefix_margin,
            state_label=worst.label,
            failed=worst.failed,
            successor_frame=(
                None if successor_key is None else successor_key[0]
            ),
            successor_row=(
                None if successor_key is None else successor_key[1]
            ),
            successor_column=(
                None if successor_key is None else successor_key[2]
            ),
            successor_active_action=(
                None
                if successor_key is None
                else action_name(successor_key[3])
            ),
            successor_pending_action=(
                None
                if successor_key is None or successor_key[4] < 0
                else action_name(successor_key[4])
            ),
            successor_remaining_delay_support=(
                () if successor_key is None else successor_key[5]
            ),
            successor_label=worst.successor_label,
            merged_hidden_branch_count=worst.hidden_branch_count,
        )
        return worst.label, (step, *worst.child_path)

    label, worst_branch = solve(
        frame,
        row,
        column,
        active_index,
        pending_index,
        pending_support,
        True,
    )
    witness = StationaryPolicyWitness(
        problem_digest=problem_digest,
        root=root,
        root_action=root_action,
        continuation_action=continuation_action,
        policy_digest=policy_digest,
        label=label,
        worst_branch=worst_branch,
        evaluated_state_count=solve.cache_info().currsize,
        witness_digest="",
    )
    return replace(
        witness,
        witness_digest=canonical_sha256(witness_payload(witness)),
    )
