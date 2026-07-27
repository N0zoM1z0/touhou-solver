"""Clearance-volume construction for one refinement rectangle."""

from __future__ import annotations

from dataclasses import replace

import numpy as np

from ..clearance import hazard_clearance_volume
from ..prepared import PreparedCorridorProblem
from .patch import QueryLocalRefinementPatch


def build_patch_clearance(
    *,
    prepared_problem: PreparedCorridorProblem,
    patch: QueryLocalRefinementPatch,
) -> np.ndarray:
    fine_config = replace(
        prepared_problem.config,
        grid_step=patch.fine_step,
    )
    clearance_x = patch.fine_x[
        patch.clearance_column_start : patch.clearance_column_end
    ].astype(np.float32)
    clearance_y = patch.fine_y[
        patch.clearance_row_start : patch.clearance_row_end
    ].astype(np.float32)
    grid_x, grid_y = np.meshgrid(clearance_x, clearance_y)
    return hazard_clearance_volume(
        grid_x,
        grid_y,
        aabbs=prepared_problem.aabbs,
        aabb_trajectories=prepared_problem.aabb_trajectories,
        piecewise_aabbs=prepared_problem.piecewise_aabbs,
        segments=prepared_problem.segments,
        segment_trajectories=prepared_problem.segment_trajectories,
        packed_segments=prepared_problem.packed_segments,
        config=fine_config,
    )


__all__ = ["build_patch_clearance"]
