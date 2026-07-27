"""Game-neutral corridor planning components."""

from .clearance import (
    aabb_clearance_field,
    aabb_clearance_volume,
    aabb_sample_clearance_field,
    clearance_field,
    hazard_clearance_volume,
    packed_segment_clearance_field,
    segment_clearance_field,
)
from .grid import axis, lane, movement_offsets, shift_from_source
from .legacy_forward import plan_legacy_forward_corridor
from .model import (
    AabbHazard,
    AabbTrajectoryHazard,
    CorridorBounds,
    CorridorConfig,
    CorridorPlan,
    CorridorPoint,
    MovingAabbHazard,
    PiecewiseAabbHazard,
    RobustControlSpec,
    SegmentHazard,
    SegmentTrajectoryHazard,
)
from .prepared import PreparedCorridorProblem, prepare_corridor_problem
from .refinement import LegacyFullFieldRefinement
from .robust import (
    RobustCorridorInduction,
    build_robust_corridor_induction,
)
from .rollout import rollout_robust_corridor

__all__ = [
    "AabbHazard",
    "AabbTrajectoryHazard",
    "CorridorBounds",
    "CorridorConfig",
    "CorridorPlan",
    "CorridorPoint",
    "MovingAabbHazard",
    "PiecewiseAabbHazard",
    "PreparedCorridorProblem",
    "LegacyFullFieldRefinement",
    "RobustCorridorInduction",
    "RobustControlSpec",
    "SegmentHazard",
    "SegmentTrajectoryHazard",
    "aabb_clearance_field",
    "aabb_clearance_volume",
    "aabb_sample_clearance_field",
    "axis",
    "clearance_field",
    "hazard_clearance_volume",
    "lane",
    "movement_offsets",
    "packed_segment_clearance_field",
    "prepare_corridor_problem",
    "plan_legacy_forward_corridor",
    "build_robust_corridor_induction",
    "rollout_robust_corridor",
    "segment_clearance_field",
    "shift_from_source",
]
