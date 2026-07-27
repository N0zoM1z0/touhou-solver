"""Query-local dual-bound refinement primitives.

The package separates spatial aggregation, transition geometry, exact-root
scope, patch construction, and solver backends. Public compatibility imports
remain available from ``corridor.dual_bounds`` and
``corridor.adaptive_refinement``.
"""

from .cells import (
    ActionMaskBounds,
    ReferenceInclusionReport,
    ReferenceInclusionViolation,
    SpatialCellPartition,
    aggregate_fine_action_mask_bounds,
    build_spatial_cell_partition,
    check_fine_reference_inclusion,
    lift_coarse_action_masks,
)
from .guides import build_policy_candidate_guide
from .patch import (
    QueryLocalRefinementPatch,
    build_query_local_refinement_patch,
    trivial_coarse_action_bounds,
)
from .result import QueryLocalDualBoundResult
from .scalar_solver import solve_query_local_dual_bounds
from .scope import PreparedDualBoundScope, RootBranchTube, prepare_dual_bound_scope
from .transitions import (
    TransitionLattice,
    build_prepared_transition_lattice,
    build_transition_lattice,
    forward_reachable_tube,
    root_branch_forward_tube,
    terminal_coreachable_tube,
)
from .vector_solver import solve_query_local_dual_bounds_vectorized

__all__ = [
    "ActionMaskBounds",
    "PreparedDualBoundScope",
    "QueryLocalDualBoundResult",
    "QueryLocalRefinementPatch",
    "ReferenceInclusionReport",
    "ReferenceInclusionViolation",
    "RootBranchTube",
    "SpatialCellPartition",
    "TransitionLattice",
    "aggregate_fine_action_mask_bounds",
    "build_policy_candidate_guide",
    "build_prepared_transition_lattice",
    "build_query_local_refinement_patch",
    "build_spatial_cell_partition",
    "build_transition_lattice",
    "check_fine_reference_inclusion",
    "forward_reachable_tube",
    "lift_coarse_action_masks",
    "prepare_dual_bound_scope",
    "root_branch_forward_tube",
    "solve_query_local_dual_bounds",
    "solve_query_local_dual_bounds_vectorized",
    "terminal_coreachable_tube",
    "trivial_coarse_action_bounds",
]
