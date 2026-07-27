"""Phase-exact query-local robust survival with an explicit input pipeline.

The dense Boolean policy is still the authoritative global certificate.  This
module answers a narrower question only after that policy has been published:
for one current lattice state, which first actions maximize guaranteed modeled
survival?

Unlike the layer-indexed policy query, the recurrence starts at the exact
physical frame and distinguishes:

* the action observed by the game;
* an older desired action that is still pending;
* the remaining frames before that pending action may become visible; and
* the new selected action, its robust delay support, and an optional
  next-decision cadence support at the public root.

The original scalar/native workspace in this module is retained as a legacy
always-issue, one-transition-cadence audit target.  The physical no-write,
recursive-cadence, non-clairvoyant oracle lives in
``variable_cadence_oracle.py`` and has a separate native belief workspace.
Neither has live authority.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Hashable

import numpy as np

from . import native_backend
from .query_survival_belief_workspace import (
    BeliefPipelineSurvivalWorkspace,
)
from .query_survival_dispatch import query_local_survival
from .query_survival_roots import (
    _prepare_root_enumeration_context as _prepare_root_enumeration_context,
    enumerate_next_decision_roots,
)
from .query_survival_scalar import scalar_query_local_survival
from .query_survival_types import (
    ActionColumnRecommendation,
    BeliefPipelineQueryStats,
    BeliefUpperCertification,
    PendingCommand,
    PipelineSurvivalQueryStats,
    QueryLocalSurvivalResult,
    ReachablePipelineRoot,
)
from .query_survival_workspace import (
    PipelineSurvivalWorkspace,
    PipelineWorkspaceCancelledError,
    PipelineWorkspaceDeadlineError,
    StalePipelineWorkspaceError,
)
from .viability import (
    ControlAction,
    RobustViabilityPolicy,
    ViabilityConfig,
    build_robust_viability_policy,
)

@dataclass(frozen=True)
class SurvivalQueryProblem:
    """Immutable numeric problem retained after Boolean publication."""

    x_axis: np.ndarray
    y_axis: np.ndarray
    clearance_volume: np.ndarray
    actions: tuple[ControlAction, ...]
    delay_frames: tuple[int, ...]
    nominal_delay: int
    config: ViabilityConfig

    def __post_init__(self) -> None:
        x_axis = np.ascontiguousarray(self.x_axis, dtype=np.float32)
        y_axis = np.ascontiguousarray(self.y_axis, dtype=np.float32)
        clearance = np.ascontiguousarray(
            self.clearance_volume,
            dtype=np.float32,
        )
        if clearance.shape != (clearance.shape[0], len(y_axis), len(x_axis)):
            raise ValueError("survival problem clearance shape is invalid")
        if clearance.shape[0] < 2:
            raise ValueError("survival problem needs a future frame")
        x_axis.setflags(write=False)
        y_axis.setflags(write=False)
        clearance.setflags(write=False)
        object.__setattr__(self, "x_axis", x_axis)
        object.__setattr__(self, "y_axis", y_axis)
        object.__setattr__(self, "clearance_volume", clearance)

    @property
    def horizon_frames(self) -> int:
        return self.clearance_volume.shape[0] - 1

    def project_to_lattice(
        self,
        *,
        x: float,
        y: float,
    ) -> tuple[int, int, float]:
        x_start = float(self.x_axis[0])
        y_start = float(self.y_axis[0])
        x_step = float(self.x_axis[1] - self.x_axis[0])
        y_step = float(self.y_axis[1] - self.y_axis[0])
        column = min(
            len(self.x_axis) - 1,
            max(0, int(np.rint((x - x_start) / x_step))),
        )
        row = min(
            len(self.y_axis) - 1,
            max(0, int(np.rint((y - y_start) / y_step))),
        )
        return (
            row,
            column,
            math.hypot(
                x - float(self.x_axis[column]),
                y - float(self.y_axis[row]),
            ),
        )

    def query(
        self,
        *,
        frame: int,
        x: float,
        y: float,
        observed_action: str,
        pending_command: PendingCommand | None = None,
        backend: str = "auto",
    ) -> QueryLocalSurvivalResult:
        row, column, _ = self.project_to_lattice(x=x, y=y)
        return query_local_survival(
            x_axis=self.x_axis,
            y_axis=self.y_axis,
            clearance_volume=self.clearance_volume,
            actions=self.actions,
            delay_frames=self.delay_frames,
            config=self.config,
            start_frame=frame,
            row=row,
            column=column,
            observed_action=observed_action,
            pending_command=pending_command,
            backend=backend,
        )

    def build_full_policy(self) -> RobustViabilityPolicy:
        """Build dense fused labels after the Boolean result is publishable."""

        return build_robust_viability_policy(
            x_axis=self.x_axis,
            y_axis=self.y_axis,
            clearance_volume=self.clearance_volume,
            actions=self.actions,
            delay_frames=self.delay_frames,
            nominal_delay=self.nominal_delay,
            config=self.config,
            survival_labels=True,
        )

    def build_postpublished_policy(
        self,
        boolean_policy: RobustViabilityPolicy,
        *,
        worker_count: int = 1,
    ) -> RobustViabilityPolicy:
        """Reuse Boolean arrays and label only states already known losing."""

        arrays = native_backend.build_losing_survival_label_arrays(
            x_axis=self.x_axis,
            y_axis=self.y_axis,
            clearance_volume=self.clearance_volume,
            velocity_x=np.asarray(
                [action.velocity_x for action in self.actions],
                dtype=np.float64,
            ),
            velocity_y=np.asarray(
                [action.velocity_y for action in self.actions],
                dtype=np.float64,
            ),
            delay_frames=np.asarray(self.delay_frames, dtype=np.int32),
            frames_per_layer=self.config.frames_per_layer,
            required_clearance=self.config.required_clearance,
            clamp_to_bounds=self.config.clamp_to_bounds,
            viable=boolean_policy.viable,
            safe_action_masks=boolean_policy.safe_action_masks,
            worker_count=worker_count,
        )
        if arrays is None:
            return self.build_full_policy()
        frames, margins, masks = arrays
        return RobustViabilityPolicy(
            x_axis=self.x_axis,
            y_axis=self.y_axis,
            actions=self.actions,
            delay_frames=self.delay_frames,
            nominal_delay=self.nominal_delay,
            config=self.config,
            viable=boolean_policy.viable,
            safe_action_masks=boolean_policy.safe_action_masks,
            backend="native_postpublished_losing_survival",
            survival_frames=frames,
            survival_bottleneck_margins=margins,
            survival_best_action_masks=masks,
        )

    def build_pipeline_workspace(
        self,
        *,
        policy_version: Hashable,
        decision_frame_support: tuple[int, ...] | None = None,
    ) -> PipelineSurvivalWorkspace:
        """Create one persistent exact-root workspace for this policy."""

        return PipelineSurvivalWorkspace(
            problem=self,
            policy_version=policy_version,
            decision_frame_support=decision_frame_support,
        )

    def build_belief_pipeline_workspace(
        self,
        *,
        policy_version: Hashable,
        decision_frame_support: tuple[int, ...],
        continuation_actions: tuple[str, ...] | None = None,
        budgeted_continuation_actions: tuple[str, ...] | None = None,
        continuation_action_budget: int = 0,
        reveal_remaining_delay: bool = False,
        remaining_delay_bucket_size: int | None = None,
        continuation_policy: str = "optimal",
        candidate_policy_width: int = 1,
    ) -> BeliefPipelineSurvivalWorkspace:
        """Create a recursive belief or revealed-delay research workspace."""

        return BeliefPipelineSurvivalWorkspace(
            problem=self,
            policy_version=policy_version,
            decision_frame_support=decision_frame_support,
            continuation_actions=continuation_actions,
            budgeted_continuation_actions=(
                budgeted_continuation_actions
            ),
            continuation_action_budget=continuation_action_budget,
            reveal_remaining_delay=reveal_remaining_delay,
            remaining_delay_bucket_size=remaining_delay_bucket_size,
            continuation_policy=continuation_policy,
            candidate_policy_width=candidate_policy_width,
        )












__all__ = [
    "ActionColumnRecommendation",
    "BeliefPipelineQueryStats",
    "BeliefPipelineSurvivalWorkspace",
    "BeliefUpperCertification",
    "PendingCommand",
    "PipelineWorkspaceCancelledError",
    "PipelineWorkspaceDeadlineError",
    "PipelineSurvivalQueryStats",
    "PipelineSurvivalWorkspace",
    "QueryLocalSurvivalResult",
    "ReachablePipelineRoot",
    "StalePipelineWorkspaceError",
    "SurvivalQueryProblem",
    "enumerate_next_decision_roots",
    "query_local_survival",
    "scalar_query_local_survival",
]
