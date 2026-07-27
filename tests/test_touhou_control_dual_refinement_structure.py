#!/usr/bin/env python3
"""Compatibility and package-boundary tests for the G2 module split."""

from __future__ import annotations

import unittest

from touhou_control.corridor import adaptive_refinement, dual_bounds
from touhou_control.corridor import refinement_guides
from touhou_control.corridor.dual_refinement import cells, guides, patch
from touhou_control.corridor.dual_refinement import result, scalar_solver
from touhou_control.corridor.dual_refinement import scope, transitions, vector_solver


class DualRefinementStructureTests(unittest.TestCase):
    def test_dual_bound_facade_preserves_public_symbol_identity(self) -> None:
        self.assertIs(dual_bounds.ActionMaskBounds, cells.ActionMaskBounds)
        self.assertIs(
            dual_bounds.PreparedDualBoundScope,
            scope.PreparedDualBoundScope,
        )
        self.assertIs(
            dual_bounds.build_transition_lattice,
            transitions.build_transition_lattice,
        )

    def test_adaptive_facade_preserves_public_symbol_identity(self) -> None:
        self.assertIs(
            adaptive_refinement.QueryLocalRefinementPatch,
            patch.QueryLocalRefinementPatch,
        )
        self.assertIs(
            adaptive_refinement.QueryLocalDualBoundResult,
            result.QueryLocalDualBoundResult,
        )
        self.assertIs(
            adaptive_refinement.solve_query_local_dual_bounds,
            scalar_solver.solve_query_local_dual_bounds,
        )
        self.assertIs(
            adaptive_refinement.solve_query_local_dual_bounds_vectorized,
            vector_solver.solve_query_local_dual_bounds_vectorized,
        )

    def test_guide_facade_preserves_public_symbol_identity(self) -> None:
        self.assertIs(
            refinement_guides.build_policy_candidate_guide,
            guides.build_policy_candidate_guide,
        )


if __name__ == "__main__":
    unittest.main()
