"""Compatibility facade for domain-oriented optional native bindings."""

from __future__ import annotations

from .native.arrays import (
    attribute_array as _attribute_array,  # noqa: F401
    attribute_array64 as _attribute_array64,  # noqa: F401
)
from .native.belief import (
    BeliefPipelineNativeWorkspace as BeliefPipelineNativeWorkspace,
    _load_belief_pipeline_workspace_functions as _load_belief_pipeline_workspace_functions,
    create_belief_pipeline_survival_workspace as create_belief_pipeline_survival_workspace,
)
from .native.geometry import (
    _load_aabb_trajectory_clearance_function as _load_aabb_trajectory_clearance_function,
    _load_clearance_function as _load_clearance_function,
    _load_piecewise_aabb_clearance_function as _load_piecewise_aabb_clearance_function,
    _load_trajectory_clearance_function as _load_trajectory_clearance_function,
    apply_aabb_trajectory_clearance as apply_aabb_trajectory_clearance,
    apply_packed_segment_clearance as apply_packed_segment_clearance,
    apply_piecewise_aabb_clearance as apply_piecewise_aabb_clearance,
    apply_segment_trajectory_clearance as apply_segment_trajectory_clearance,
    build_clearance_volume as build_clearance_volume,
)
from .native.library import (
    PipelineNativeCancelledError as PipelineNativeCancelledError,
    PipelineNativeDeadlineError as PipelineNativeDeadlineError,
    available as available,
    library_path as _library_path,  # noqa: F401 - compatibility export
    load_library as _load_library,  # noqa: F401 - compatibility export
    raise_pipeline_result as _raise_pipeline_result,  # noqa: F401
)
from .native.local import (
    DecodedBulletPool as DecodedBulletPool,
    _load_bullet_pool_decode_function as _load_bullet_pool_decode_function,
    _load_local_beam_reduce_function as _load_local_beam_reduce_function,
    _load_local_hazards_function as _load_local_hazards_function,
    decode_bullet_pool as decode_bullet_pool,
    query_local_hazards as query_local_hazards,
    reduce_local_beam as reduce_local_beam,
)
from .native.pipeline import (
    PipelineSurvivalNativeWorkspace as PipelineSurvivalNativeWorkspace,
    _load_pipeline_workspace_functions as _load_pipeline_workspace_functions,
    create_pipeline_survival_workspace as create_pipeline_survival_workspace,
)
from .native.viability import (
    _load_losing_survival_labels_function as _load_losing_survival_labels_function,
    _load_query_local_survival_function as _load_query_local_survival_function,
    _load_safety_policy_function as _load_safety_policy_function,
    _load_safety_value_function as _load_safety_value_function,
    _load_survival_viability_function as _load_survival_viability_function,
    _load_terminal_viability_function as _load_terminal_viability_function,
    _load_viability_function as _load_viability_function,
    _load_viability_worker_limit_function as _load_viability_worker_limit_function,
    build_losing_survival_label_arrays as build_losing_survival_label_arrays,
    build_safety_policy_arrays as build_safety_policy_arrays,
    build_safety_value_arrays as build_safety_value_arrays,
    build_survival_viability_arrays as build_survival_viability_arrays,
    build_viability_arrays as build_viability_arrays,
    query_local_survival_arrays as query_local_survival_arrays,
    set_current_thread_viability_worker_limit as set_current_thread_viability_worker_limit,
)
