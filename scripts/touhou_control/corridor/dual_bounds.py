"""Compatibility facade for query-local dual-bound primitives.

New code should import focused modules from ``corridor.dual_refinement``.
"""

from .dual_refinement import (
    ActionMaskBounds,
    PreparedDualBoundScope,
    ReferenceInclusionReport,
    ReferenceInclusionViolation,
    RootBranchTube,
    SpatialCellPartition,
    TransitionLattice,
    aggregate_fine_action_mask_bounds,
    build_prepared_transition_lattice,
    build_spatial_cell_partition,
    build_transition_lattice,
    check_fine_reference_inclusion,
    forward_reachable_tube,
    lift_coarse_action_masks,
    prepare_dual_bound_scope,
    root_branch_forward_tube,
    terminal_coreachable_tube,
)

__all__ = [
    "ActionMaskBounds",
    "PreparedDualBoundScope",
    "ReferenceInclusionReport",
    "ReferenceInclusionViolation",
    "RootBranchTube",
    "SpatialCellPartition",
    "TransitionLattice",
    "aggregate_fine_action_mask_bounds",
    "build_prepared_transition_lattice",
    "build_spatial_cell_partition",
    "build_transition_lattice",
    "check_fine_reference_inclusion",
    "forward_reachable_tube",
    "lift_coarse_action_masks",
    "prepare_dual_bound_scope",
    "root_branch_forward_tube",
    "terminal_coreachable_tube",
]
