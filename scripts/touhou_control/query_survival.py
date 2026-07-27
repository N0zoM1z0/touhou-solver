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

from .query_survival_belief_workspace import (
    BeliefPipelineSurvivalWorkspace,
)
from .query_survival_dispatch import query_local_survival
from .query_survival_problem import SurvivalQueryProblem
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
