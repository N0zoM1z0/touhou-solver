"""Public value contracts for query-local survival solvers."""

from __future__ import annotations

from dataclasses import dataclass

from .reachability_oracle import SurvivalLabel


@dataclass(frozen=True)
class PendingCommand:
    """One desired action not yet observed by the controlled process."""

    action: str
    remaining_frames: tuple[int, ...]

    def __post_init__(self) -> None:
        if not self.action:
            raise ValueError("pending action cannot be empty")
        if (
            not self.remaining_frames
            or tuple(sorted(set(self.remaining_frames)))
            != self.remaining_frames
            or self.remaining_frames[0] <= 0
        ):
            raise ValueError(
                "pending remaining frames must be sorted unique and positive"
            )


@dataclass(frozen=True)
class ReachablePipelineRoot:
    """One deduplicated exact root at a possible next decision epoch."""

    frame: int
    row: int
    column: int
    observed_action: str
    pending_command: PendingCommand | None


@dataclass(frozen=True)
class PipelineSurvivalQueryStats:
    """Per-query work performed by a persistent augmented-state workspace."""

    memoized_state_count: int
    new_state_count: int
    memo_hit_count: int
    action_upper_bound_prune_count: int
    delay_incumbent_prune_count: int
    canonicalization_count: int
    root_memo_hit_count: int
    branch_simulation_count: int


@dataclass(frozen=True)
class BeliefPipelineQueryStats:
    """Work performed by the recursive information-set workspace."""

    memoized_state_count: int
    new_state_count: int
    memo_hit_count: int
    action_upper_bound_prune_count: int
    branch_incumbent_prune_count: int
    observation_merge_count: int
    root_memo_hit_count: int
    hidden_simulation_count: int


@dataclass(frozen=True)
class BeliefUpperCertification:
    """Threshold result from a proved optimistic information relaxation."""

    lower_bound: SurvivalLabel
    certified: bool
    unresolved_actions: tuple[str, ...]
    deadline_expired: bool
    workspace_stats: BeliefPipelineQueryStats


@dataclass(frozen=True)
class ActionColumnRecommendation:
    """Heuristic policy column found on an exact worst restricted path."""

    target_root_action: str
    recommended_action: str | None
    witness_frame: int
    witness_row: int
    witness_column: int
    witness_active_action: str | None
    witness_pending_action: str | None
    witness_remaining_frames: tuple[int, ...]
    current_label: SurvivalLabel
    deviation_label: SurvivalLabel
    witness_depth: int
    workspace_stats: BeliefPipelineQueryStats


@dataclass(frozen=True)
class QueryLocalSurvivalResult:
    """Lexicographic survival labels for one exact physical-frame state."""

    start_frame: int
    remaining_frames: int
    row: int
    column: int
    observed_action: str
    pending_command: PendingCommand | None
    state_label: SurvivalLabel
    action_labels: tuple[tuple[str, SurvivalLabel], ...]
    best_actions: tuple[str, ...]
    evaluated_state_count: int
    backend: str = "scalar_pending_pipeline"
    workspace_stats: (
        PipelineSurvivalQueryStats | BeliefPipelineQueryStats | None
    ) = None

    @property
    def winning(self) -> bool:
        return (
            self.state_label.guaranteed_frames == self.remaining_frames
            and self.state_label.bottleneck_margin > 0.0
        )

    def action_label(self, action: str) -> SurvivalLabel:
        for name, label in self.action_labels:
            if name == action:
                return label
        raise KeyError(action)


__all__ = [
    "ActionColumnRecommendation",
    "BeliefPipelineQueryStats",
    "BeliefUpperCertification",
    "PendingCommand",
    "PipelineSurvivalQueryStats",
    "QueryLocalSurvivalResult",
    "ReachablePipelineRoot",
]
