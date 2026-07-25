"""Anytime attainable policy portfolios for the belief-pipeline game."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Hashable

from .query_survival import (
    ActionColumnRecommendation,
    BeliefPipelineQueryStats,
    BeliefUpperCertification,
    PendingCommand,
    PipelineWorkspaceDeadlineError,
    QueryLocalSurvivalResult,
    SurvivalQueryProblem,
)
from .reachability_oracle import SurvivalLabel


@dataclass(frozen=True)
class CandidateContinuationPolicy:
    """One causal continuation policy class proposed for exact evaluation."""

    name: str
    continuation_actions: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("candidate policy name cannot be empty")
        if (
            not self.continuation_actions
            or len(set(self.continuation_actions))
            != len(self.continuation_actions)
        ):
            raise ValueError(
                "candidate continuation actions must be nonempty and unique"
            )


@dataclass(frozen=True)
class CandidateActionWitness:
    """The completed candidate attaining one merged root-action lower."""

    root_action: str
    label: SurvivalLabel
    candidate_policy: str


@dataclass(frozen=True)
class CandidatePolicyEvaluation:
    """One exactly verified candidate result, safe only for its version."""

    candidate_policy: str
    state_label: SurvivalLabel


@dataclass(frozen=True)
class CandidatePolicyPortfolioResult:
    """Merged attainable lower labels from completed candidate policies."""

    result: QueryLocalSurvivalResult
    action_witnesses: tuple[CandidateActionWitness, ...]
    candidate_evaluations: tuple[CandidatePolicyEvaluation, ...]
    completed_candidates: tuple[str, ...]
    timed_out_candidates: tuple[str, ...]
    stopped_on_feasibility: bool

    @property
    def feasibility_sufficient(self) -> bool:
        return self.result.winning


@dataclass(frozen=True)
class PolicyRefinementStep:
    """One completed lower class and optional worst-path proposal."""

    continuation_actions: tuple[str, ...]
    lower_result: QueryLocalSurvivalResult
    target_root_action: str
    recommendation: ActionColumnRecommendation | None
    upper_certification: BeliefUpperCertification


@dataclass(frozen=True)
class DualBoundPolicyRefinementResult:
    """Anytime lower portfolio plus gap-directed exact refinements."""

    portfolio: CandidatePolicyPortfolioResult
    final_lower_result: QueryLocalSurvivalResult
    final_continuation_actions: tuple[str, ...]
    final_upper_certification: BeliefUpperCertification
    refinement_steps: tuple[PolicyRefinementStep, ...]

    @property
    def feasibility_sufficient(self) -> bool:
        return self.final_lower_result.winning

    @property
    def optimality_certified(self) -> bool:
        return self.final_upper_certification.certified


def singleton_continuation_candidates(
    problem: SurvivalQueryProblem,
) -> tuple[CandidateContinuationPolicy, ...]:
    """Propose one stationary continuation policy per available action."""

    return tuple(
        CandidateContinuationPolicy(
            name=f"always_{action.name}",
            continuation_actions=(action.name,),
        )
        for action in problem.actions
    )


def prioritize_candidates_from_previous_version(
    *,
    candidates: tuple[CandidateContinuationPolicy, ...],
    previous: CandidatePolicyPortfolioResult,
) -> tuple[CandidateContinuationPolicy, ...]:
    """Reuse only prior candidate ordering; never transfer prior labels.

    A policy/model version change invalidates every prior lower certificate.
    Ranking the same proposers is nevertheless safe because each candidate is
    exactly re-solved before it contributes to the new incumbent.
    """

    prior_labels = {
        evaluation.candidate_policy: evaluation.state_label
        for evaluation in previous.candidate_evaluations
    }
    indexed = tuple(enumerate(candidates))
    return tuple(
        candidate
        for _, candidate in sorted(
            indexed,
            key=lambda item: (
                prior_labels.get(
                    item[1].name,
                    SurvivalLabel(-1, float("-inf")),
                ),
                -item[0],
            ),
            reverse=True,
        )
    )


def evaluate_candidate_policy_portfolio(
    *,
    problem: SurvivalQueryProblem,
    policy_version: Hashable,
    decision_frame_support: tuple[int, ...],
    candidates: tuple[CandidateContinuationPolicy, ...],
    frame: int,
    row: int,
    column: int,
    observed_action: str,
    pending_command: PendingCommand | None = None,
    timeout_ms_per_candidate: int = 0,
    stop_on_feasibility: bool = True,
) -> CandidatePolicyPortfolioResult:
    """Exactly verify candidates and merge their per-action lower bounds.

    Selecting a candidate policy is part of the public-root controller
    decision. Therefore the maximum completed label for each root action is
    attainable. A timed-out candidate contributes no label.
    """

    if not candidates:
        raise ValueError("candidate portfolio cannot be empty")
    known_actions = {action.name for action in problem.actions}
    if len({candidate.name for candidate in candidates}) != len(candidates):
        raise ValueError("candidate policy names must be unique")
    for candidate in candidates:
        if any(
            action not in known_actions
            for action in candidate.continuation_actions
        ):
            raise ValueError(
                f"candidate {candidate.name!r} has an unknown action"
            )

    merged_labels: list[SurvivalLabel | None] = [
        None for _ in problem.actions
    ]
    witnesses: list[str | None] = [None for _ in problem.actions]
    completed: list[str] = []
    evaluations: list[CandidatePolicyEvaluation] = []
    timed_out: list[str] = []
    aggregate_stats = [0] * 8
    stopped_on_feasibility = False

    for candidate_index, candidate in enumerate(candidates):
        candidate_version = (
            policy_version,
            "candidate",
            candidate_index,
            candidate.name,
        )
        with problem.build_belief_pipeline_workspace(
            policy_version=candidate_version,
            decision_frame_support=decision_frame_support,
            continuation_actions=candidate.continuation_actions,
        ) as workspace:
            try:
                candidate_result = workspace.query_cell(
                    policy_version=candidate_version,
                    frame=frame,
                    row=row,
                    column=column,
                    observed_action=observed_action,
                    pending_command=pending_command,
                    timeout_ms=timeout_ms_per_candidate,
                )
            except PipelineWorkspaceDeadlineError:
                timed_out.append(candidate.name)
                continue

        completed.append(candidate.name)
        evaluations.append(
            CandidatePolicyEvaluation(
                candidate_policy=candidate.name,
                state_label=candidate_result.state_label,
            )
        )
        stats = candidate_result.workspace_stats
        assert isinstance(stats, BeliefPipelineQueryStats)
        for index, value in enumerate(vars(stats).values()):
            aggregate_stats[index] += int(value)
        for action_index, (_, label) in enumerate(
            candidate_result.action_labels
        ):
            incumbent = merged_labels[action_index]
            if incumbent is None or incumbent < label:
                merged_labels[action_index] = label
                witnesses[action_index] = candidate.name

        if stop_on_feasibility and candidate_result.winning:
            stopped_on_feasibility = True
            break

    if not completed:
        raise PipelineWorkspaceDeadlineError(
            "every candidate policy exceeded its deadline"
        )
    assert all(label is not None for label in merged_labels)
    assert all(witness is not None for witness in witnesses)
    labels = tuple(label for label in merged_labels if label is not None)
    state_label = max(labels)
    action_labels = tuple(
        (action.name, label)
        for action, label in zip(problem.actions, labels)
    )
    result = QueryLocalSurvivalResult(
        start_frame=frame,
        remaining_frames=problem.horizon_frames - frame,
        row=row,
        column=column,
        observed_action=observed_action,
        pending_command=pending_command,
        state_label=state_label,
        action_labels=action_labels,
        best_actions=tuple(
            action.name
            for action, label in zip(problem.actions, labels)
            if label == state_label
        ),
        evaluated_state_count=aggregate_stats[0],
        backend="native_candidate_policy_portfolio",
        workspace_stats=BeliefPipelineQueryStats(*aggregate_stats),
    )
    return CandidatePolicyPortfolioResult(
        result=result,
        action_witnesses=tuple(
            CandidateActionWitness(
                root_action=action.name,
                label=label,
                candidate_policy=witness,
            )
            for action, label, witness in zip(
                problem.actions,
                labels,
                witnesses,
            )
            if witness is not None
        ),
        candidate_evaluations=tuple(evaluations),
        completed_candidates=tuple(completed),
        timed_out_candidates=tuple(timed_out),
        stopped_on_feasibility=stopped_on_feasibility,
    )


def refine_candidate_policy_gap(
    *,
    problem: SurvivalQueryProblem,
    policy_version: Hashable,
    decision_frame_support: tuple[int, ...],
    candidates: tuple[CandidateContinuationPolicy, ...],
    frame: int,
    row: int,
    column: int,
    observed_action: str,
    pending_command: PendingCommand | None = None,
    timeout_ms_per_lower: int = 0,
    timeout_ms_upper: int = 0,
    max_columns: int = 6,
    witness_max_depth: int = 64,
) -> DualBoundPolicyRefinementResult:
    """Close a lower/upper gap with verified policy columns.

    The upper unresolved root action seeds the restricted continuation class.
    A worst-path one-step deviation then proposes another column. Every
    proposal is re-solved as an exact attainable lower before it can improve
    the incumbent.
    """

    if max_columns < 1:
        raise ValueError("max_columns must be positive")
    portfolio = evaluate_candidate_policy_portfolio(
        problem=problem,
        policy_version=(policy_version, "portfolio"),
        decision_frame_support=decision_frame_support,
        candidates=candidates,
        frame=frame,
        row=row,
        column=column,
        observed_action=observed_action,
        pending_command=pending_command,
        timeout_ms_per_candidate=timeout_ms_per_lower,
        stop_on_feasibility=False,
    )
    candidate_by_name = {
        candidate.name: candidate for candidate in candidates
    }
    best_root_action = portfolio.result.best_actions[0]
    best_witness = next(
        witness
        for witness in portfolio.action_witnesses
        if witness.root_action == best_root_action
    )
    columns = list(
        candidate_by_name[
            best_witness.candidate_policy
        ].continuation_actions
    )
    incumbent = portfolio.result
    steps: list[PolicyRefinementStep] = []
    blocked_targets: set[str] = set()
    pending_refinement_target: str | None = None

    upper_version = (policy_version, "upper")
    with problem.build_belief_pipeline_workspace(
        policy_version=upper_version,
        decision_frame_support=decision_frame_support,
        # Width 62 maps every admitted positive remaining delay to one
        # redundant bucket. The public pending-action field already
        # distinguishes remaining zero, so this is exactly the physical
        # observation partition while enabling threshold certification.
        remaining_delay_bucket_size=62,
    ) as upper_workspace:
        certification = upper_workspace.certify_upper_bound(
            policy_version=upper_version,
            frame=frame,
            row=row,
            column=column,
            observed_action=observed_action,
            pending_command=pending_command,
            lower_bound=incumbent.state_label,
            timeout_ms=timeout_ms_upper,
        )
        while not certification.certified:
            target = pending_refinement_target
            pending_refinement_target = None
            if target is None:
                target = next(
                    (
                        action
                        for action in certification.unresolved_actions
                        if action not in blocked_targets
                    ),
                    None,
                )
            if target is None:
                break
            if target not in columns:
                if len(columns) >= max_columns:
                    break
                columns.append(target)

            lower_version = (
                policy_version,
                "lower",
                tuple(columns),
            )
            recommendation = None
            with problem.build_belief_pipeline_workspace(
                policy_version=lower_version,
                decision_frame_support=decision_frame_support,
                continuation_actions=tuple(columns),
            ) as lower_workspace:
                lower = lower_workspace.query_cell(
                    policy_version=lower_version,
                    frame=frame,
                    row=row,
                    column=column,
                    observed_action=observed_action,
                    pending_command=pending_command,
                    timeout_ms=timeout_ms_per_lower,
                )
                if incumbent.state_label < lower.state_label:
                    incumbent = lower
                certification = upper_workspace.certify_upper_bound(
                    policy_version=upper_version,
                    frame=frame,
                    row=row,
                    column=column,
                    observed_action=observed_action,
                    pending_command=pending_command,
                    lower_bound=incumbent.state_label,
                    timeout_ms=timeout_ms_upper,
                )
                if not certification.certified:
                    recommendation = (
                        lower_workspace.recommend_action_column(
                            policy_version=lower_version,
                            frame=frame,
                            row=row,
                            column=column,
                            observed_action=observed_action,
                            pending_command=pending_command,
                            target_root_action=target,
                            max_depth=witness_max_depth,
                            timeout_ms=timeout_ms_per_lower,
                        )
                    )
            steps.append(
                PolicyRefinementStep(
                    continuation_actions=tuple(columns),
                    lower_result=lower,
                    target_root_action=target,
                    recommendation=recommendation,
                    upper_certification=certification,
                )
            )
            if certification.certified:
                break
            proposed = (
                recommendation.recommended_action
                if recommendation is not None
                else None
            )
            if proposed is None or proposed in columns:
                blocked_targets.add(target)
            else:
                if len(columns) >= max_columns:
                    break
                columns.append(proposed)
                # Solve the appended proposal before considering a different
                # unresolved root action or exposing it in the final result.
                pending_refinement_target = target

    return DualBoundPolicyRefinementResult(
        portfolio=portfolio,
        final_lower_result=incumbent,
        final_continuation_actions=tuple(columns),
        final_upper_certification=certification,
        refinement_steps=tuple(steps),
    )


__all__ = [
    "CandidateActionWitness",
    "CandidateContinuationPolicy",
    "CandidatePolicyEvaluation",
    "CandidatePolicyPortfolioResult",
    "DualBoundPolicyRefinementResult",
    "PolicyRefinementStep",
    "evaluate_candidate_policy_portfolio",
    "prioritize_candidates_from_previous_version",
    "refine_candidate_policy_gap",
    "singleton_continuation_candidates",
]
