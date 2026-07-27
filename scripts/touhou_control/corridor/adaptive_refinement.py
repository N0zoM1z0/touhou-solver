"""Compatibility facade for query-local dual-bound refinement.

New code should import focused modules from ``corridor.dual_refinement``.
"""

from .dual_refinement.patch import (
    QueryLocalRefinementPatch,
    build_query_local_refinement_patch,
    trivial_coarse_action_bounds,
)
from .dual_refinement.result import QueryLocalDualBoundResult
from .dual_refinement.scalar_solver import solve_query_local_dual_bounds
from .dual_refinement.vector_solver import solve_query_local_dual_bounds_vectorized

__all__ = [
    "QueryLocalDualBoundResult",
    "QueryLocalRefinementPatch",
    "build_query_local_refinement_patch",
    "solve_query_local_dual_bounds",
    "solve_query_local_dual_bounds_vectorized",
    "trivial_coarse_action_bounds",
]
