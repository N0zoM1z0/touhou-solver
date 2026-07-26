"""Optional C ABI backend for time-expanded hazards and viability."""

from __future__ import annotations

import ctypes
from dataclasses import dataclass
import os
from pathlib import Path
import time

import numpy as np

from .packed_hazards import PackedSegmentFrames


ROOT = Path(__file__).resolve().parents[2]
_DISABLE_ENV = "TOUHOU_DISABLE_NATIVE_PLANNER"
_LIBRARY = None
_VIABILITY_WORKER_LIMIT_FUNCTION = None
_VIABILITY_FUNCTION = None
_TERMINAL_VIABILITY_FUNCTION = None
_SAFETY_VALUE_FUNCTION = None
_SAFETY_POLICY_FUNCTION = None
_SURVIVAL_VIABILITY_FUNCTION = None
_QUERY_LOCAL_SURVIVAL_FUNCTION = None
_PIPELINE_WORKSPACE_CREATE_FUNCTION = None
_PIPELINE_WORKSPACE_QUERY_FUNCTION = None
_PIPELINE_WORKSPACE_CONTAINS_FUNCTION = None
_PIPELINE_WORKSPACE_PREWARM_FUNCTION = None
_PIPELINE_WORKSPACE_MERGE_FUNCTION = None
_PIPELINE_WORKSPACE_CANCEL_FUNCTION = None
_PIPELINE_WORKSPACE_DESTROY_FUNCTION = None
_BELIEF_PIPELINE_CREATE_FUNCTION = None
_BELIEF_PIPELINE_QUERY_FUNCTION = None
_BELIEF_PIPELINE_CERTIFY_FUNCTION = None
_BELIEF_PIPELINE_RECOMMEND_FUNCTION = None
_BELIEF_PIPELINE_CANCEL_FUNCTION = None
_BELIEF_PIPELINE_DESTROY_FUNCTION = None
_LOSING_SURVIVAL_LABELS_FUNCTION = None
_CLEARANCE_FUNCTION = None
_AABB_TRAJECTORY_CLEARANCE_FUNCTION = None
_PIECEWISE_AABB_CLEARANCE_FUNCTION = None
_TRAJECTORY_CLEARANCE_FUNCTION = None
_BULLET_POOL_DECODE_FUNCTION = None
_LOCAL_HAZARDS_FUNCTION = None
_LOCAL_BEAM_REDUCE_FUNCTION = None
_LOCAL_SUPPLEMENTAL_BEAM_REDUCE_FUNCTION = None
_LOCAL_SUPPLEMENTAL_WORKSPACE_FUNCTIONS = None
_LOAD_ERROR: OSError | None = None


@dataclass(frozen=True)
class DecodedBulletPool:
    """Owned structure-of-arrays output from the native slot decoder."""

    x: np.ndarray
    y: np.ndarray
    velocity_x: np.ndarray
    velocity_y: np.ndarray
    half_width: np.ndarray
    half_height: np.ndarray
    transform_flags: np.ndarray
    slots: np.ndarray
    speed: np.ndarray
    angle: np.ndarray
    callback_phase: np.ndarray
    callback_aux: np.ndarray
    original_transform_flags: np.ndarray

    def __len__(self) -> int:
        return len(self.x)


class LocalSupplementalNativeCancelledError(RuntimeError):
    """The complete native supplemental rollout was cancelled."""


class LocalSupplementalNativeDeadlineError(RuntimeError):
    """The complete native supplemental rollout missed its deadline."""


@dataclass(frozen=True)
class LocalSupplementalNativeResult:
    """Completed endpoint vectors from one all-or-nothing native rollout."""

    x: np.ndarray
    y: np.ndarray
    first_action: np.ndarray
    last_action: np.ndarray
    risk: np.ndarray
    collisions: np.ndarray
    minimum_clearance: np.ndarray
    immediate_clearance: np.ndarray

    def __len__(self) -> int:
        return len(self.x)


_C_FLOAT_POINTER = ctypes.POINTER(ctypes.c_float)
_C_DOUBLE_POINTER = ctypes.POINTER(ctypes.c_double)
_C_INT32_POINTER = ctypes.POINTER(ctypes.c_int32)
_C_UINT8_POINTER = ctypes.POINTER(ctypes.c_uint8)


class _LocalSupplementalQueryV1(ctypes.Structure):
    _fields_ = [
        ("struct_size", ctypes.c_uint32),
        ("horizon", ctypes.c_int),
        ("action_hold_frames", ctypes.c_int),
        ("beam_width", ctypes.c_int),
        ("control_delay_frames", ctypes.c_int),
        ("action_count", ctypes.c_int),
        ("initial_x", ctypes.c_double),
        ("initial_y", ctypes.c_double),
        ("initial_first_action", ctypes.c_int32),
        ("initial_last_action", ctypes.c_int32),
        ("initial_risk", ctypes.c_double),
        ("initial_collisions", ctypes.c_int32),
        ("initial_minimum_clearance", ctypes.c_double),
        ("initial_immediate_clearance", ctypes.c_double),
        ("action_direction", _C_INT32_POINTER),
        ("action_dx", _C_DOUBLE_POINTER),
        ("action_dy", _C_DOUBLE_POINTER),
        ("action_focused", _C_UINT8_POINTER),
        ("action_allowed", _C_UINT8_POINTER),
        ("certificate_collisions", _C_INT32_POINTER),
        ("certificate_minimum", _C_DOUBLE_POINTER),
        ("survival_preferred", _C_UINT8_POINTER),
        ("safety_preferred", _C_UINT8_POINTER),
        ("recovery_distance", _C_DOUBLE_POINTER),
        ("repair_volume", _C_INT32_POINTER),
        ("bullet_offsets", _C_INT32_POINTER),
        ("bullet_x", _C_FLOAT_POINTER),
        ("bullet_y", _C_FLOAT_POINTER),
        ("bullet_half_width", _C_FLOAT_POINTER),
        ("bullet_half_height", _C_FLOAT_POINTER),
        ("bullet_transformed", _C_UINT8_POINTER),
        ("laser_offsets", _C_INT32_POINTER),
        ("laser_start_x", _C_FLOAT_POINTER),
        ("laser_start_y", _C_FLOAT_POINTER),
        ("laser_segment_x", _C_FLOAT_POINTER),
        ("laser_segment_y", _C_FLOAT_POINTER),
        ("laser_collision_radius", _C_FLOAT_POINTER),
        ("laser_base_uncertainty", _C_FLOAT_POINTER),
        ("laser_uncertainty_per_frame", _C_FLOAT_POINTER),
        ("body_count", ctypes.c_int),
        ("body_base_x", _C_FLOAT_POINTER),
        ("body_base_y", _C_FLOAT_POINTER),
        ("body_velocity_x", _C_FLOAT_POINTER),
        ("body_velocity_y", _C_FLOAT_POINTER),
        ("body_half_width", _C_FLOAT_POINTER),
        ("body_half_height", _C_FLOAT_POINTER),
        ("player_radius", ctypes.c_float),
        ("preserve_previous_direction_inertia", ctypes.c_int),
        ("previous_direction", ctypes.c_int32),
        ("previous_focused", ctypes.c_uint8),
        ("target_enabled", ctypes.c_int),
        ("target_x", ctypes.c_double),
        ("target_y", ctypes.c_double),
        ("target_deadline", ctypes.c_int),
        ("item_safety_clearance", ctypes.c_double),
        ("playfield_left", ctypes.c_double),
        ("playfield_right", ctypes.c_double),
        ("playfield_top", ctypes.c_double),
        ("playfield_bottom", ctypes.c_double),
        ("recovery_reserve_distance", ctypes.c_double),
        ("supplemental_reserve_distance", ctypes.c_double),
        ("diagonal_speed", ctypes.c_double),
        ("cardinal_speed", ctypes.c_double),
        ("timeout_nanoseconds", ctypes.c_uint64),
    ]


class _LocalSupplementalOutputV1(ctypes.Structure):
    _fields_ = [
        ("struct_size", ctypes.c_uint32),
        ("capacity", ctypes.c_int),
        ("x", _C_DOUBLE_POINTER),
        ("y", _C_DOUBLE_POINTER),
        ("first_action", _C_INT32_POINTER),
        ("last_action", _C_INT32_POINTER),
        ("risk", _C_DOUBLE_POINTER),
        ("collisions", _C_INT32_POINTER),
        ("minimum_clearance", _C_DOUBLE_POINTER),
        ("immediate_clearance", _C_DOUBLE_POINTER),
        ("count", _C_INT32_POINTER),
    ]


def _library_path() -> Path:
    if os.name == "nt":
        return (
            ROOT
            / "native"
            / "build"
            / "windows-x86_64"
            / "touhou_viability.dll"
        )
    return (
        ROOT
        / "native"
        / "build"
        / "linux-x86_64"
        / "libtouhou_viability.so"
    )


def _load_library():
    global _LIBRARY, _LOAD_ERROR
    if _LIBRARY is not None or _LOAD_ERROR is not None:
        return _LIBRARY
    if os.environ.get(_DISABLE_ENV) == "1":
        return None
    try:
        _LIBRARY = ctypes.CDLL(str(_library_path()))
    except OSError as error:
        _LOAD_ERROR = error
        return None
    return _LIBRARY


def _load_viability_function():
    global _VIABILITY_FUNCTION
    if _VIABILITY_FUNCTION is not None:
        return _VIABILITY_FUNCTION
    library = _load_library()
    if library is None:
        return None
    function = library.touhou_robust_viability_v1
    function.argtypes = [
        ctypes.POINTER(ctypes.c_float),
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_int),
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_float,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.POINTER(ctypes.c_uint32),
    ]
    function.restype = ctypes.c_int
    _VIABILITY_FUNCTION = function
    return function


def _load_viability_worker_limit_function():
    global _VIABILITY_WORKER_LIMIT_FUNCTION
    if _VIABILITY_WORKER_LIMIT_FUNCTION is not None:
        return _VIABILITY_WORKER_LIMIT_FUNCTION
    library = _load_library()
    if library is None:
        return None
    try:
        function = (
            library
            .touhou_set_current_thread_viability_worker_limit_v1
        )
    except AttributeError:
        return None
    function.argtypes = [ctypes.c_int]
    function.restype = ctypes.c_int
    _VIABILITY_WORKER_LIMIT_FUNCTION = function
    return function


def set_current_thread_viability_worker_limit(
    worker_limit: int,
) -> bool:
    """Bound native viability fan-out on the calling Python thread."""

    if not 1 <= worker_limit <= 4:
        raise ValueError("native viability worker limit must be 1..4")
    function = _load_viability_worker_limit_function()
    if function is None:
        return False
    result = function(worker_limit)
    if result != 0:
        raise RuntimeError(
            f"native viability worker-limit setter returned {result}"
        )
    return True


def _load_terminal_viability_function():
    global _TERMINAL_VIABILITY_FUNCTION
    if _TERMINAL_VIABILITY_FUNCTION is not None:
        return _TERMINAL_VIABILITY_FUNCTION
    library = _load_library()
    if library is None:
        return None
    try:
        function = library.touhou_robust_viability_terminal_v1
    except AttributeError:
        return None
    function.argtypes = [
        ctypes.POINTER(ctypes.c_float),
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_int),
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_float,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.POINTER(ctypes.c_uint32),
    ]
    function.restype = ctypes.c_int
    _TERMINAL_VIABILITY_FUNCTION = function
    return function


def _load_safety_value_function():
    global _SAFETY_VALUE_FUNCTION
    if _SAFETY_VALUE_FUNCTION is not None:
        return _SAFETY_VALUE_FUNCTION
    library = _load_library()
    if library is None:
        return None
    try:
        function = library.touhou_robust_safety_value_v1
    except AttributeError:
        return None
    function.argtypes = [
        ctypes.POINTER(ctypes.c_float),
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_int),
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_float),
    ]
    function.restype = ctypes.c_int
    _SAFETY_VALUE_FUNCTION = function
    return function


def _load_safety_policy_function():
    global _SAFETY_POLICY_FUNCTION
    if _SAFETY_POLICY_FUNCTION is not None:
        return _SAFETY_POLICY_FUNCTION
    library = _load_library()
    if library is None:
        return None
    try:
        function = library.touhou_robust_safety_policy_v1
    except AttributeError:
        return None
    function.argtypes = [
        ctypes.POINTER(ctypes.c_float),
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_int),
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_uint32),
    ]
    function.restype = ctypes.c_int
    _SAFETY_POLICY_FUNCTION = function
    return function


def _load_survival_viability_function():
    global _SURVIVAL_VIABILITY_FUNCTION
    if _SURVIVAL_VIABILITY_FUNCTION is not None:
        return _SURVIVAL_VIABILITY_FUNCTION
    library = _load_library()
    if library is None:
        return None
    try:
        function = library.touhou_robust_survival_viability_v1
    except AttributeError:
        return None
    function.argtypes = [
        ctypes.POINTER(ctypes.c_float),
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_int),
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_float,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_uint16),
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_uint32),
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.POINTER(ctypes.c_uint32),
    ]
    function.restype = ctypes.c_int
    _SURVIVAL_VIABILITY_FUNCTION = function
    return function


def _load_query_local_survival_function():
    global _QUERY_LOCAL_SURVIVAL_FUNCTION
    if _QUERY_LOCAL_SURVIVAL_FUNCTION is not None:
        return _QUERY_LOCAL_SURVIVAL_FUNCTION
    library = _load_library()
    if library is None:
        return None
    try:
        function = library.touhou_query_local_survival_v1
    except AttributeError:
        return None
    function.argtypes = [
        ctypes.POINTER(ctypes.c_float),
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_int),
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_float,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_int),
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_uint16),
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_uint16),
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_uint32),
        ctypes.POINTER(ctypes.c_uint64),
    ]
    function.restype = ctypes.c_int
    _QUERY_LOCAL_SURVIVAL_FUNCTION = function
    return function


def _load_pipeline_workspace_functions():
    global _PIPELINE_WORKSPACE_CREATE_FUNCTION
    global _PIPELINE_WORKSPACE_QUERY_FUNCTION
    global _PIPELINE_WORKSPACE_CONTAINS_FUNCTION
    global _PIPELINE_WORKSPACE_PREWARM_FUNCTION
    global _PIPELINE_WORKSPACE_MERGE_FUNCTION
    global _PIPELINE_WORKSPACE_CANCEL_FUNCTION
    global _PIPELINE_WORKSPACE_DESTROY_FUNCTION
    if (
        _PIPELINE_WORKSPACE_CREATE_FUNCTION is not None
        and _PIPELINE_WORKSPACE_QUERY_FUNCTION is not None
        and _PIPELINE_WORKSPACE_CONTAINS_FUNCTION is not None
        and _PIPELINE_WORKSPACE_PREWARM_FUNCTION is not None
        and _PIPELINE_WORKSPACE_MERGE_FUNCTION is not None
        and _PIPELINE_WORKSPACE_CANCEL_FUNCTION is not None
        and _PIPELINE_WORKSPACE_DESTROY_FUNCTION is not None
    ):
        return (
            _PIPELINE_WORKSPACE_CREATE_FUNCTION,
            _PIPELINE_WORKSPACE_QUERY_FUNCTION,
            _PIPELINE_WORKSPACE_CONTAINS_FUNCTION,
            _PIPELINE_WORKSPACE_PREWARM_FUNCTION,
            _PIPELINE_WORKSPACE_MERGE_FUNCTION,
            _PIPELINE_WORKSPACE_CANCEL_FUNCTION,
            _PIPELINE_WORKSPACE_DESTROY_FUNCTION,
        )
    library = _load_library()
    if library is None:
        return None
    try:
        create = library.touhou_pipeline_survival_workspace_create_v2
        query = library.touhou_pipeline_survival_workspace_query_v2
        contains = (
            library.touhou_pipeline_survival_workspace_contains_root_v1
        )
        prewarm = (
            library
            .touhou_pipeline_survival_workspace_prewarm_continuation_v1
        )
        merge = (
            library.touhou_pipeline_survival_workspace_merge_continuation_v1
        )
        cancel = library.touhou_pipeline_survival_workspace_cancel_v1
        destroy = library.touhou_pipeline_survival_workspace_destroy_v1
    except AttributeError:
        return None
    create.argtypes = [
        ctypes.POINTER(ctypes.c_float),
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_int),
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_int),
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_float,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    create.restype = ctypes.c_int
    query.argtypes = [
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_int),
        ctypes.c_int,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_uint16),
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_uint16),
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_uint32),
        ctypes.POINTER(ctypes.c_uint64),
    ]
    query.restype = ctypes.c_int
    contains.argtypes = [
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_int),
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_int),
    ]
    contains.restype = ctypes.c_int
    prewarm.argtypes = [
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_int),
        ctypes.c_int,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_uint16),
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_uint64),
    ]
    prewarm.restype = ctypes.c_int
    merge.argtypes = [
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_uint64),
    ]
    merge.restype = ctypes.c_int
    cancel.argtypes = [ctypes.c_void_p]
    cancel.restype = ctypes.c_int
    destroy.argtypes = [ctypes.c_void_p]
    destroy.restype = None
    _PIPELINE_WORKSPACE_CREATE_FUNCTION = create
    _PIPELINE_WORKSPACE_QUERY_FUNCTION = query
    _PIPELINE_WORKSPACE_CONTAINS_FUNCTION = contains
    _PIPELINE_WORKSPACE_PREWARM_FUNCTION = prewarm
    _PIPELINE_WORKSPACE_MERGE_FUNCTION = merge
    _PIPELINE_WORKSPACE_CANCEL_FUNCTION = cancel
    _PIPELINE_WORKSPACE_DESTROY_FUNCTION = destroy
    return create, query, contains, prewarm, merge, cancel, destroy


def _load_belief_pipeline_workspace_functions():
    global _BELIEF_PIPELINE_CREATE_FUNCTION
    global _BELIEF_PIPELINE_QUERY_FUNCTION
    global _BELIEF_PIPELINE_CERTIFY_FUNCTION
    global _BELIEF_PIPELINE_RECOMMEND_FUNCTION
    global _BELIEF_PIPELINE_CANCEL_FUNCTION
    global _BELIEF_PIPELINE_DESTROY_FUNCTION
    if (
        _BELIEF_PIPELINE_CREATE_FUNCTION is not None
        and _BELIEF_PIPELINE_QUERY_FUNCTION is not None
        and _BELIEF_PIPELINE_CERTIFY_FUNCTION is not None
        and _BELIEF_PIPELINE_RECOMMEND_FUNCTION is not None
        and _BELIEF_PIPELINE_CANCEL_FUNCTION is not None
        and _BELIEF_PIPELINE_DESTROY_FUNCTION is not None
    ):
        return (
            _BELIEF_PIPELINE_CREATE_FUNCTION,
            _BELIEF_PIPELINE_QUERY_FUNCTION,
            _BELIEF_PIPELINE_CERTIFY_FUNCTION,
            _BELIEF_PIPELINE_RECOMMEND_FUNCTION,
            _BELIEF_PIPELINE_CANCEL_FUNCTION,
            _BELIEF_PIPELINE_DESTROY_FUNCTION,
        )
    library = _load_library()
    if library is None:
        return None
    try:
        create = library.touhou_belief_pipeline_workspace_create_v6
        query = library.touhou_belief_pipeline_workspace_query_v2
        certify = (
            library.touhou_belief_pipeline_workspace_certify_upper_v2
        )
        recommend = (
            library
            .touhou_belief_pipeline_workspace_recommend_action_column_v1
        )
        cancel = library.touhou_belief_pipeline_workspace_cancel_v1
        destroy = library.touhou_belief_pipeline_workspace_destroy_v1
    except AttributeError:
        return None
    create.argtypes = [
        ctypes.POINTER(ctypes.c_float),
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
        ctypes.c_int,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_int),
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_int),
        ctypes.c_int,
        ctypes.c_float,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    create.restype = ctypes.c_int
    query.argtypes = [
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_int),
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_uint16),
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_uint16),
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_uint32),
        ctypes.POINTER(ctypes.c_uint64),
    ]
    query.restype = ctypes.c_int
    certify.argtypes = [
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_int),
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_uint16,
        ctypes.c_float,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_uint32),
        ctypes.POINTER(ctypes.c_int),
        ctypes.POINTER(ctypes.c_uint64),
    ]
    certify.restype = ctypes.c_int
    recommend.argtypes = [
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_int),
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_int),
        ctypes.POINTER(ctypes.c_int),
        ctypes.POINTER(ctypes.c_int),
        ctypes.POINTER(ctypes.c_int),
        ctypes.POINTER(ctypes.c_int),
        ctypes.POINTER(ctypes.c_int),
        ctypes.POINTER(ctypes.c_uint64),
        ctypes.POINTER(ctypes.c_uint16),
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_uint16),
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_int),
        ctypes.POINTER(ctypes.c_uint64),
    ]
    recommend.restype = ctypes.c_int
    cancel.argtypes = [ctypes.c_void_p]
    cancel.restype = ctypes.c_int
    destroy.argtypes = [ctypes.c_void_p]
    destroy.restype = None
    _BELIEF_PIPELINE_CREATE_FUNCTION = create
    _BELIEF_PIPELINE_QUERY_FUNCTION = query
    _BELIEF_PIPELINE_CERTIFY_FUNCTION = certify
    _BELIEF_PIPELINE_RECOMMEND_FUNCTION = recommend
    _BELIEF_PIPELINE_CANCEL_FUNCTION = cancel
    _BELIEF_PIPELINE_DESTROY_FUNCTION = destroy
    return create, query, certify, recommend, cancel, destroy


def _load_losing_survival_labels_function():
    global _LOSING_SURVIVAL_LABELS_FUNCTION
    if _LOSING_SURVIVAL_LABELS_FUNCTION is not None:
        return _LOSING_SURVIVAL_LABELS_FUNCTION
    library = _load_library()
    if library is None:
        return None
    try:
        function = library.touhou_losing_survival_labels_v1
    except AttributeError:
        return None
    function.argtypes = [
        ctypes.POINTER(ctypes.c_float),
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_double),
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_int),
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_float,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.POINTER(ctypes.c_uint32),
        ctypes.POINTER(ctypes.c_uint16),
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_uint32),
    ]
    function.restype = ctypes.c_int
    _LOSING_SURVIVAL_LABELS_FUNCTION = function
    return function


def _load_clearance_function():
    global _CLEARANCE_FUNCTION
    if _CLEARANCE_FUNCTION is not None:
        return _CLEARANCE_FUNCTION
    library = _load_library()
    if library is None:
        return None
    function = library.touhou_clearance_volume_v1
    float_pointer = ctypes.POINTER(ctypes.c_float)
    function.argtypes = [
        ctypes.c_float,
        ctypes.c_float,
        ctypes.c_int,
        ctypes.c_float,
        ctypes.c_float,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_float,
        ctypes.c_float,
        float_pointer,
        float_pointer,
        float_pointer,
        float_pointer,
        float_pointer,
        float_pointer,
        float_pointer,
        float_pointer,
        ctypes.c_int,
        float_pointer,
        float_pointer,
        float_pointer,
        float_pointer,
        float_pointer,
        float_pointer,
        float_pointer,
        float_pointer,
        ctypes.c_int,
        float_pointer,
    ]
    function.restype = ctypes.c_int
    _CLEARANCE_FUNCTION = function
    return function


def _load_trajectory_clearance_function():
    global _TRAJECTORY_CLEARANCE_FUNCTION
    if _TRAJECTORY_CLEARANCE_FUNCTION is not None:
        return _TRAJECTORY_CLEARANCE_FUNCTION
    library = _load_library()
    if library is None:
        return None
    try:
        function = library.touhou_segment_trajectory_clearance_v1
    except AttributeError:
        return None
    float_pointer = ctypes.POINTER(ctypes.c_float)
    function.argtypes = [
        ctypes.c_float,
        ctypes.c_float,
        ctypes.c_int,
        ctypes.c_float,
        ctypes.c_float,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_float,
        ctypes.POINTER(ctypes.c_int32),
        float_pointer,
        float_pointer,
        float_pointer,
        float_pointer,
        float_pointer,
        float_pointer,
        float_pointer,
        float_pointer,
        ctypes.c_int,
        float_pointer,
    ]
    function.restype = ctypes.c_int
    _TRAJECTORY_CLEARANCE_FUNCTION = function
    return function


def _load_aabb_trajectory_clearance_function():
    global _AABB_TRAJECTORY_CLEARANCE_FUNCTION
    if _AABB_TRAJECTORY_CLEARANCE_FUNCTION is not None:
        return _AABB_TRAJECTORY_CLEARANCE_FUNCTION
    library = _load_library()
    if library is None:
        return None
    try:
        function = library.touhou_aabb_trajectory_clearance_v1
    except AttributeError:
        return None
    float_pointer = ctypes.POINTER(ctypes.c_float)
    function.argtypes = [
        ctypes.c_float,
        ctypes.c_float,
        ctypes.c_int,
        ctypes.c_float,
        ctypes.c_float,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_float,
        ctypes.POINTER(ctypes.c_int32),
        float_pointer,
        float_pointer,
        float_pointer,
        float_pointer,
        float_pointer,
        float_pointer,
        ctypes.c_int,
        float_pointer,
    ]
    function.restype = ctypes.c_int
    _AABB_TRAJECTORY_CLEARANCE_FUNCTION = function
    return function


def _load_piecewise_aabb_clearance_function():
    global _PIECEWISE_AABB_CLEARANCE_FUNCTION
    if _PIECEWISE_AABB_CLEARANCE_FUNCTION is not None:
        return _PIECEWISE_AABB_CLEARANCE_FUNCTION
    library = _load_library()
    if library is None:
        return None
    try:
        function = library.touhou_piecewise_aabb_clearance_v1
    except AttributeError:
        return None
    float_pointer = ctypes.POINTER(ctypes.c_float)
    double_pointer = ctypes.POINTER(ctypes.c_double)
    function.argtypes = [
        ctypes.c_float,
        ctypes.c_float,
        ctypes.c_int,
        ctypes.c_float,
        ctypes.c_float,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_float,
        double_pointer,
        double_pointer,
        double_pointer,
        double_pointer,
        float_pointer,
        float_pointer,
        float_pointer,
        float_pointer,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_int32),
        ctypes.POINTER(ctypes.c_int32),
        double_pointer,
        double_pointer,
        ctypes.c_int,
        float_pointer,
    ]
    function.restype = ctypes.c_int
    _PIECEWISE_AABB_CLEARANCE_FUNCTION = function
    return function


def _load_local_hazards_function():
    global _LOCAL_HAZARDS_FUNCTION
    if _LOCAL_HAZARDS_FUNCTION is not None:
        return _LOCAL_HAZARDS_FUNCTION
    library = _load_library()
    if library is None:
        return None
    try:
        function = library.touhou_local_hazards_v1
    except AttributeError:
        return None
    float_pointer = ctypes.POINTER(ctypes.c_float)
    function.argtypes = [
        float_pointer,
        float_pointer,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_float,
        float_pointer,
        float_pointer,
        float_pointer,
        float_pointer,
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_int,
        float_pointer,
        float_pointer,
        float_pointer,
        float_pointer,
        float_pointer,
        float_pointer,
        float_pointer,
        ctypes.c_int,
        float_pointer,
        float_pointer,
        float_pointer,
        float_pointer,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_double),
        ctypes.POINTER(ctypes.c_int32),
        ctypes.POINTER(ctypes.c_double),
    ]
    function.restype = ctypes.c_int
    _LOCAL_HAZARDS_FUNCTION = function
    return function


def _load_bullet_pool_decode_function():
    global _BULLET_POOL_DECODE_FUNCTION
    if _BULLET_POOL_DECODE_FUNCTION is not None:
        return _BULLET_POOL_DECODE_FUNCTION
    library = _load_library()
    if library is None:
        return None
    try:
        function = library.touhou_decode_bullet_pool_v1
    except AttributeError:
        return None
    uint8_pointer = ctypes.POINTER(ctypes.c_uint8)
    float_pointer = ctypes.POINTER(ctypes.c_float)
    function.argtypes = [
        uint8_pointer,
        ctypes.c_uint64,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        float_pointer,
        float_pointer,
        float_pointer,
        float_pointer,
        float_pointer,
        float_pointer,
        ctypes.POINTER(ctypes.c_uint32),
        ctypes.POINTER(ctypes.c_int32),
        float_pointer,
        float_pointer,
        ctypes.POINTER(ctypes.c_int16),
        uint8_pointer,
        ctypes.POINTER(ctypes.c_uint32),
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_int32),
    ]
    function.restype = ctypes.c_int
    _BULLET_POOL_DECODE_FUNCTION = function
    return function


def _load_local_beam_reduce_function():
    global _LOCAL_BEAM_REDUCE_FUNCTION
    if _LOCAL_BEAM_REDUCE_FUNCTION is not None:
        return _LOCAL_BEAM_REDUCE_FUNCTION
    library = _load_library()
    if library is None:
        return None
    try:
        function = library.touhou_local_beam_reduce_v1
    except AttributeError:
        return None
    double_pointer = ctypes.POINTER(ctypes.c_double)
    int32_pointer = ctypes.POINTER(ctypes.c_int32)
    uint8_pointer = ctypes.POINTER(ctypes.c_uint8)
    function.argtypes = [
        double_pointer,
        double_pointer,
        int32_pointer,
        int32_pointer,
        uint8_pointer,
        ctypes.POINTER(ctypes.c_uint32),
        double_pointer,
        int32_pointer,
        double_pointer,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_double,
        ctypes.c_int,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_int,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        int32_pointer,
        double_pointer,
        uint8_pointer,
        uint8_pointer,
        double_pointer,
        ctypes.c_int,
        int32_pointer,
        int32_pointer,
    ]
    function.restype = ctypes.c_int
    _LOCAL_BEAM_REDUCE_FUNCTION = function
    return function


def _load_local_supplemental_beam_reduce_function():
    global _LOCAL_SUPPLEMENTAL_BEAM_REDUCE_FUNCTION
    if _LOCAL_SUPPLEMENTAL_BEAM_REDUCE_FUNCTION is not None:
        return _LOCAL_SUPPLEMENTAL_BEAM_REDUCE_FUNCTION
    library = _load_library()
    if library is None:
        return None
    try:
        function = library.touhou_local_supplemental_beam_reduce_v1
    except AttributeError:
        return None
    double_pointer = ctypes.POINTER(ctypes.c_double)
    int32_pointer = ctypes.POINTER(ctypes.c_int32)
    uint8_pointer = ctypes.POINTER(ctypes.c_uint8)
    function.argtypes = [
        double_pointer,
        double_pointer,
        int32_pointer,
        int32_pointer,
        uint8_pointer,
        ctypes.POINTER(ctypes.c_uint32),
        double_pointer,
        int32_pointer,
        double_pointer,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_double,
        ctypes.c_int,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_int,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        int32_pointer,
        double_pointer,
        uint8_pointer,
        uint8_pointer,
        double_pointer,
        int32_pointer,
        ctypes.c_int,
        int32_pointer,
        int32_pointer,
    ]
    function.restype = ctypes.c_int
    _LOCAL_SUPPLEMENTAL_BEAM_REDUCE_FUNCTION = function
    return function


def _load_local_supplemental_workspace_functions():
    global _LOCAL_SUPPLEMENTAL_WORKSPACE_FUNCTIONS
    if _LOCAL_SUPPLEMENTAL_WORKSPACE_FUNCTIONS is not None:
        return _LOCAL_SUPPLEMENTAL_WORKSPACE_FUNCTIONS
    library = _load_library()
    if library is None:
        return None
    try:
        create = library.touhou_local_supplemental_workspace_create_v1
        query = library.touhou_local_supplemental_workspace_query_v1
        cancel = library.touhou_local_supplemental_workspace_cancel_v1
        active = library.touhou_local_supplemental_workspace_active_v1
        destroy = library.touhou_local_supplemental_workspace_destroy_v1
    except AttributeError:
        return None
    create.argtypes = [ctypes.POINTER(ctypes.c_void_p)]
    create.restype = ctypes.c_int
    query.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(_LocalSupplementalQueryV1),
        ctypes.POINTER(_LocalSupplementalOutputV1),
    ]
    query.restype = ctypes.c_int
    cancel.argtypes = [ctypes.c_void_p]
    cancel.restype = ctypes.c_int
    active.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int)]
    active.restype = ctypes.c_int
    destroy.argtypes = [ctypes.c_void_p]
    destroy.restype = ctypes.c_int
    _LOCAL_SUPPLEMENTAL_WORKSPACE_FUNCTIONS = (
        create,
        query,
        cancel,
        active,
        destroy,
    )
    return _LOCAL_SUPPLEMENTAL_WORKSPACE_FUNCTIONS


def available() -> bool:
    return _load_library() is not None


def _attribute_array(items: tuple[object, ...], name: str) -> np.ndarray:
    return np.fromiter(
        (float(getattr(item, name)) for item in items),
        dtype=np.float32,
        count=len(items),
    )


def _attribute_array64(items: tuple[object, ...], name: str) -> np.ndarray:
    return np.fromiter(
        (float(getattr(item, name)) for item in items),
        dtype=np.float64,
        count=len(items),
    )


def query_local_hazards(
    *,
    positions_x: np.ndarray,
    positions_y: np.ndarray,
    step: int,
    player_radius: float,
    bullet_x: np.ndarray,
    bullet_y: np.ndarray,
    bullet_half_width: np.ndarray,
    bullet_half_height: np.ndarray,
    bullet_transformed: np.ndarray,
    laser_start_x: np.ndarray,
    laser_start_y: np.ndarray,
    laser_segment_x: np.ndarray,
    laser_segment_y: np.ndarray,
    laser_collision_radius: np.ndarray,
    laser_base_uncertainty: np.ndarray,
    laser_uncertainty_per_frame: np.ndarray,
    body_x: np.ndarray,
    body_y: np.ndarray,
    body_half_width: np.ndarray,
    body_half_height: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray] | None:
    """Evaluate one local hazard frame through the optional scalar C ABI."""

    function = _load_local_hazards_function()
    if function is None:
        return None
    positions_x = np.ascontiguousarray(positions_x, dtype=np.float32)
    positions_y = np.ascontiguousarray(positions_y, dtype=np.float32)
    if (
        positions_x.ndim != 1
        or positions_y.shape != positions_x.shape
        or not len(positions_x)
    ):
        raise ValueError("local hazard positions must be nonempty 1D peers")
    bullet_fields = tuple(
        np.ascontiguousarray(values, dtype=np.float32)
        for values in (
            bullet_x,
            bullet_y,
            bullet_half_width,
            bullet_half_height,
        )
    )
    bullet_transformed = np.ascontiguousarray(bullet_transformed)
    if bullet_transformed.dtype not in {
        np.dtype(np.bool_),
        np.dtype(np.uint8),
    }:
        bullet_transformed = np.ascontiguousarray(
            bullet_transformed,
            dtype=np.uint8,
        )
    bullet_count = len(bullet_fields[0])
    if any(
        values.ndim != 1 or len(values) != bullet_count
        for values in (*bullet_fields, bullet_transformed)
    ):
        raise ValueError("local bullet hazard fields must be 1D peers")
    laser_fields = tuple(
        np.ascontiguousarray(values, dtype=np.float32)
        for values in (
            laser_start_x,
            laser_start_y,
            laser_segment_x,
            laser_segment_y,
            laser_collision_radius,
            laser_base_uncertainty,
            laser_uncertainty_per_frame,
        )
    )
    laser_count = len(laser_fields[0])
    if any(
        values.ndim != 1 or len(values) != laser_count
        for values in laser_fields
    ):
        raise ValueError("local laser hazard fields must be 1D peers")
    body_fields = tuple(
        np.ascontiguousarray(values, dtype=np.float32)
        for values in (
            body_x,
            body_y,
            body_half_width,
            body_half_height,
        )
    )
    body_count = len(body_fields[0])
    if any(
        values.ndim != 1 or len(values) != body_count
        for values in body_fields
    ):
        raise ValueError("local body hazard fields must be 1D peers")
    risk = np.empty(len(positions_x), dtype=np.float64)
    collisions = np.empty(len(positions_x), dtype=np.int32)
    minimum = np.empty(len(positions_x), dtype=np.float64)
    float_pointer = ctypes.POINTER(ctypes.c_float)
    result = function(
        positions_x.ctypes.data_as(float_pointer),
        positions_y.ctypes.data_as(float_pointer),
        len(positions_x),
        step,
        player_radius,
        *(
            values.ctypes.data_as(float_pointer)
            for values in bullet_fields
        ),
        bullet_transformed.ctypes.data_as(
            ctypes.POINTER(ctypes.c_uint8)
        ),
        bullet_count,
        *(
            values.ctypes.data_as(float_pointer)
            for values in laser_fields
        ),
        laser_count,
        *(
            values.ctypes.data_as(float_pointer)
            for values in body_fields
        ),
        body_count,
        risk.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        collisions.ctypes.data_as(ctypes.POINTER(ctypes.c_int32)),
        minimum.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
    )
    if result != 0:
        raise RuntimeError(f"native local hazard kernel returned {result}")
    return risk, collisions, minimum


def decode_bullet_pool(
    blob: bytes | bytearray | memoryview,
    *,
    record_count: int,
    stride: int,
    state_offset: int,
    geometry_offset: int,
    position_offset: int,
    velocity_offset: int,
    speed_offset: int,
    angle_offset: int,
    transform_flags_offset: int,
    original_transform_flags_offset: int,
    callback_phase_offset: int,
    callback_aux_offset: int,
) -> DecodedBulletPool | None:
    """Decode active fixed-stride records into an owned packed snapshot."""

    function = _load_bullet_pool_decode_function()
    if function is None:
        return None
    if record_count < 0 or stride <= 0:
        raise ValueError("bullet record count and stride must be valid")
    required_size = record_count * stride
    if len(blob) < required_size:
        raise ValueError(f"bullet pool requires {required_size} bytes")
    raw = np.frombuffer(
        blob,
        dtype=np.uint8,
        count=required_size,
    )
    float_fields = tuple(
        np.empty(record_count, dtype=np.float32)
        for _ in range(8)
    )
    transform_flags = np.empty(record_count, dtype=np.uint32)
    slots = np.empty(record_count, dtype=np.int32)
    callback_phase = np.empty(record_count, dtype=np.int16)
    callback_aux = np.empty(record_count, dtype=np.uint8)
    original_transform_flags = np.empty(
        record_count,
        dtype=np.uint32,
    )
    output_count = ctypes.c_int32()
    float_pointer = ctypes.POINTER(ctypes.c_float)
    result = function(
        raw.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
        required_size,
        record_count,
        stride,
        state_offset,
        geometry_offset,
        position_offset,
        velocity_offset,
        speed_offset,
        angle_offset,
        transform_flags_offset,
        original_transform_flags_offset,
        callback_phase_offset,
        callback_aux_offset,
        *(
            values.ctypes.data_as(float_pointer)
            for values in float_fields[:6]
        ),
        transform_flags.ctypes.data_as(
            ctypes.POINTER(ctypes.c_uint32)
        ),
        slots.ctypes.data_as(ctypes.POINTER(ctypes.c_int32)),
        float_fields[6].ctypes.data_as(float_pointer),
        float_fields[7].ctypes.data_as(float_pointer),
        callback_phase.ctypes.data_as(
            ctypes.POINTER(ctypes.c_int16)
        ),
        callback_aux.ctypes.data_as(
            ctypes.POINTER(ctypes.c_uint8)
        ),
        original_transform_flags.ctypes.data_as(
            ctypes.POINTER(ctypes.c_uint32)
        ),
        record_count,
        ctypes.byref(output_count),
    )
    if result != 0:
        raise RuntimeError(f"native bullet decoder returned {result}")
    count = int(output_count.value)
    if count < 0 or count > record_count:
        raise RuntimeError(
            f"native bullet decoder returned invalid count {count}"
        )

    def prefix(values: np.ndarray) -> np.ndarray:
        return values[:count]

    return DecodedBulletPool(
        x=prefix(float_fields[0]),
        y=prefix(float_fields[1]),
        velocity_x=prefix(float_fields[2]),
        velocity_y=prefix(float_fields[3]),
        half_width=prefix(float_fields[4]),
        half_height=prefix(float_fields[5]),
        transform_flags=prefix(transform_flags),
        slots=prefix(slots),
        speed=prefix(float_fields[6]),
        angle=prefix(float_fields[7]),
        callback_phase=prefix(callback_phase),
        callback_aux=prefix(callback_aux),
        original_transform_flags=prefix(
            original_transform_flags
        ),
    )


def reduce_local_beam(
    *,
    draft_x: np.ndarray,
    draft_y: np.ndarray,
    first_action: np.ndarray,
    last_direction: np.ndarray,
    last_focused: np.ndarray,
    collected_mask: np.ndarray,
    risk: np.ndarray,
    collisions: np.ndarray,
    minimum_clearance: np.ndarray,
    step: int,
    beam_width: int,
    position_quantization: float,
    target_x: float | None,
    target_y: float | None,
    target_deadline: int | None,
    item_safety_clearance: float,
    playfield_left: float,
    playfield_right: float,
    playfield_top: float,
    playfield_bottom: float,
    reserve_distance: float,
    diagonal_speed: float,
    cardinal_speed: float,
    certificate_collisions: np.ndarray,
    certificate_minimum: np.ndarray,
    survival_preferred: np.ndarray,
    safety_preferred: np.ndarray,
    recovery_distance: np.ndarray,
) -> np.ndarray | None:
    """Return exact retained draft indices for the quantized beam reducer."""

    function = _load_local_beam_reduce_function()
    if function is None:
        return None
    draft_fields = (
        np.ascontiguousarray(draft_x, dtype=np.float64),
        np.ascontiguousarray(draft_y, dtype=np.float64),
        np.ascontiguousarray(first_action, dtype=np.int32),
        np.ascontiguousarray(last_direction, dtype=np.int32),
        np.ascontiguousarray(last_focused, dtype=np.uint8),
        np.ascontiguousarray(collected_mask, dtype=np.uint32),
        np.ascontiguousarray(risk, dtype=np.float64),
        np.ascontiguousarray(collisions, dtype=np.int32),
        np.ascontiguousarray(minimum_clearance, dtype=np.float64),
    )
    draft_count = len(draft_fields[0])
    if (
        draft_count <= 0
        or any(values.ndim != 1 or len(values) != draft_count for values in draft_fields)
    ):
        raise ValueError("local beam draft fields must be nonempty 1D peers")
    action_fields = (
        np.ascontiguousarray(certificate_collisions, dtype=np.int32),
        np.ascontiguousarray(certificate_minimum, dtype=np.float64),
        np.ascontiguousarray(survival_preferred, dtype=np.uint8),
        np.ascontiguousarray(safety_preferred, dtype=np.uint8),
        np.ascontiguousarray(recovery_distance, dtype=np.float64),
    )
    action_count = len(action_fields[0])
    if (
        action_count <= 0
        or any(values.ndim != 1 or len(values) != action_count for values in action_fields)
    ):
        raise ValueError("local beam action fields must be nonempty 1D peers")
    if step <= 0 or beam_width <= 0:
        raise ValueError("local beam step and width must be positive")
    target_enabled = target_x is not None
    if target_enabled != (target_y is not None and target_deadline is not None):
        raise ValueError("local beam target fields must be all present or absent")

    retained = np.empty(min(beam_width, draft_count), dtype=np.int32)
    retained_count = ctypes.c_int32()
    double_pointer = ctypes.POINTER(ctypes.c_double)
    int32_pointer = ctypes.POINTER(ctypes.c_int32)
    uint8_pointer = ctypes.POINTER(ctypes.c_uint8)
    result = function(
        draft_fields[0].ctypes.data_as(double_pointer),
        draft_fields[1].ctypes.data_as(double_pointer),
        draft_fields[2].ctypes.data_as(int32_pointer),
        draft_fields[3].ctypes.data_as(int32_pointer),
        draft_fields[4].ctypes.data_as(uint8_pointer),
        draft_fields[5].ctypes.data_as(ctypes.POINTER(ctypes.c_uint32)),
        draft_fields[6].ctypes.data_as(double_pointer),
        draft_fields[7].ctypes.data_as(int32_pointer),
        draft_fields[8].ctypes.data_as(double_pointer),
        draft_count,
        step,
        beam_width,
        position_quantization,
        int(target_enabled),
        0.0 if target_x is None else target_x,
        0.0 if target_y is None else target_y,
        0 if target_deadline is None else target_deadline,
        item_safety_clearance,
        playfield_left,
        playfield_right,
        playfield_top,
        playfield_bottom,
        reserve_distance,
        diagonal_speed,
        cardinal_speed,
        action_fields[0].ctypes.data_as(int32_pointer),
        action_fields[1].ctypes.data_as(double_pointer),
        action_fields[2].ctypes.data_as(uint8_pointer),
        action_fields[3].ctypes.data_as(uint8_pointer),
        action_fields[4].ctypes.data_as(double_pointer),
        action_count,
        retained.ctypes.data_as(int32_pointer),
        ctypes.byref(retained_count),
    )
    if result != 0:
        raise RuntimeError(f"native local beam reducer returned {result}")
    count = int(retained_count.value)
    if count <= 0 or count > len(retained):
        raise RuntimeError(
            f"native local beam reducer returned invalid count {count}"
        )
    return retained[:count].copy()


def reduce_local_supplemental_beam(
    *,
    draft_x: np.ndarray,
    draft_y: np.ndarray,
    first_action: np.ndarray,
    last_direction: np.ndarray,
    last_focused: np.ndarray,
    collected_mask: np.ndarray,
    risk: np.ndarray,
    collisions: np.ndarray,
    minimum_clearance: np.ndarray,
    step: int,
    beam_width: int,
    position_quantization: float,
    target_x: float | None,
    target_y: float | None,
    target_deadline: int | None,
    item_safety_clearance: float,
    playfield_left: float,
    playfield_right: float,
    playfield_top: float,
    playfield_bottom: float,
    recovery_reserve_distance: float,
    supplemental_reserve_distance: float,
    diagonal_speed: float,
    cardinal_speed: float,
    certificate_collisions: np.ndarray,
    certificate_minimum: np.ndarray,
    survival_preferred: np.ndarray,
    safety_preferred: np.ndarray,
    recovery_distance: np.ndarray,
    repair_volume: np.ndarray,
) -> np.ndarray | None:
    """Return supplemental proposal indices under its independent order."""

    function = _load_local_supplemental_beam_reduce_function()
    if function is None:
        return None
    draft_fields = (
        np.ascontiguousarray(draft_x, dtype=np.float64),
        np.ascontiguousarray(draft_y, dtype=np.float64),
        np.ascontiguousarray(first_action, dtype=np.int32),
        np.ascontiguousarray(last_direction, dtype=np.int32),
        np.ascontiguousarray(last_focused, dtype=np.uint8),
        np.ascontiguousarray(collected_mask, dtype=np.uint32),
        np.ascontiguousarray(risk, dtype=np.float64),
        np.ascontiguousarray(collisions, dtype=np.int32),
        np.ascontiguousarray(minimum_clearance, dtype=np.float64),
    )
    draft_count = len(draft_fields[0])
    if (
        draft_count <= 0
        or any(
            values.ndim != 1 or len(values) != draft_count
            for values in draft_fields
        )
    ):
        raise ValueError(
            "supplemental beam draft fields must be nonempty 1D peers"
        )
    action_fields = (
        np.ascontiguousarray(certificate_collisions, dtype=np.int32),
        np.ascontiguousarray(certificate_minimum, dtype=np.float64),
        np.ascontiguousarray(survival_preferred, dtype=np.uint8),
        np.ascontiguousarray(safety_preferred, dtype=np.uint8),
        np.ascontiguousarray(recovery_distance, dtype=np.float64),
        np.ascontiguousarray(repair_volume, dtype=np.int32),
    )
    action_count = len(action_fields[0])
    if (
        action_count <= 0
        or any(
            values.ndim != 1 or len(values) != action_count
            for values in action_fields
        )
    ):
        raise ValueError(
            "supplemental beam action fields must be nonempty 1D peers"
        )
    if np.any(action_fields[5] < 0):
        raise ValueError("supplemental repair volume cannot be negative")
    if step <= 0 or beam_width <= 0:
        raise ValueError(
            "supplemental beam step and width must be positive"
        )
    target_enabled = target_x is not None
    if target_enabled != (
        target_y is not None and target_deadline is not None
    ):
        raise ValueError(
            "supplemental beam target fields must be all present or absent"
        )

    retained = np.empty(min(beam_width, draft_count), dtype=np.int32)
    retained_count = ctypes.c_int32()
    double_pointer = ctypes.POINTER(ctypes.c_double)
    int32_pointer = ctypes.POINTER(ctypes.c_int32)
    uint8_pointer = ctypes.POINTER(ctypes.c_uint8)
    result = function(
        draft_fields[0].ctypes.data_as(double_pointer),
        draft_fields[1].ctypes.data_as(double_pointer),
        draft_fields[2].ctypes.data_as(int32_pointer),
        draft_fields[3].ctypes.data_as(int32_pointer),
        draft_fields[4].ctypes.data_as(uint8_pointer),
        draft_fields[5].ctypes.data_as(
            ctypes.POINTER(ctypes.c_uint32)
        ),
        draft_fields[6].ctypes.data_as(double_pointer),
        draft_fields[7].ctypes.data_as(int32_pointer),
        draft_fields[8].ctypes.data_as(double_pointer),
        draft_count,
        step,
        beam_width,
        position_quantization,
        int(target_enabled),
        0.0 if target_x is None else target_x,
        0.0 if target_y is None else target_y,
        0 if target_deadline is None else target_deadline,
        item_safety_clearance,
        playfield_left,
        playfield_right,
        playfield_top,
        playfield_bottom,
        recovery_reserve_distance,
        supplemental_reserve_distance,
        diagonal_speed,
        cardinal_speed,
        action_fields[0].ctypes.data_as(int32_pointer),
        action_fields[1].ctypes.data_as(double_pointer),
        action_fields[2].ctypes.data_as(uint8_pointer),
        action_fields[3].ctypes.data_as(uint8_pointer),
        action_fields[4].ctypes.data_as(double_pointer),
        action_fields[5].ctypes.data_as(int32_pointer),
        action_count,
        retained.ctypes.data_as(int32_pointer),
        ctypes.byref(retained_count),
    )
    if result != 0:
        raise RuntimeError(
            f"native supplemental beam reducer returned {result}"
        )
    count = int(retained_count.value)
    if count <= 0 or count > len(retained):
        raise RuntimeError(
            "native supplemental beam reducer returned invalid count "
            f"{count}"
        )
    return retained[:count].copy()


def _frame_major_fields(
    frames: tuple[tuple[np.ndarray, ...], ...],
    *,
    field_count: int,
    dtypes: tuple[np.dtype, ...],
) -> tuple[np.ndarray, tuple[np.ndarray, ...]]:
    """Pack peer fields with one offset table without changing frame order."""

    if len(dtypes) != field_count:
        raise ValueError("frame-major field dtype count mismatch")
    offsets = np.empty(len(frames) + 1, dtype=np.int32)
    offsets[0] = 0
    normalized: list[tuple[np.ndarray, ...]] = []
    for frame_index, frame in enumerate(frames):
        if len(frame) != field_count:
            raise ValueError("frame-major field count mismatch")
        converted = tuple(
            np.ascontiguousarray(values, dtype=dtypes[field])
            for field, values in enumerate(frame)
        )
        count = len(converted[0])
        if any(
            values.ndim != 1 or len(values) != count
            for values in converted
        ):
            raise ValueError("frame-major fields must be 1D peers")
        if offsets[frame_index] > np.iinfo(np.int32).max - count:
            raise ValueError("frame-major hazard count exceeds int32")
        offsets[frame_index + 1] = offsets[frame_index] + count
        normalized.append(converted)
    flattened = tuple(
        (
            np.concatenate(
                [frame[field] for frame in normalized],
            )
            if offsets[-1]
            else np.empty(0, dtype=dtypes[field])
        )
        for field in range(field_count)
    )
    return offsets, flattened


class LocalSupplementalNativeWorkspace:
    """Persistent allocation/cancellation scope for complete local rollouts."""

    def __init__(self) -> None:
        functions = _load_local_supplemental_workspace_functions()
        if functions is None:
            raise RuntimeError(
                "native supplemental rollout workspace is unavailable"
            )
        (
            self._create,
            self._query,
            self._cancel,
            self._active,
            self._destroy,
        ) = functions
        self._handle = ctypes.c_void_p()
        result = self._create(ctypes.byref(self._handle))
        if result != 0 or not self._handle.value:
            self._handle = ctypes.c_void_p()
            raise RuntimeError(
                "native supplemental workspace create returned "
                f"{result}"
            )

    @property
    def closed(self) -> bool:
        return not bool(self._handle.value)

    def close(self) -> None:
        if self._handle.value:
            result = self._destroy(self._handle)
            self._handle = ctypes.c_void_p()
            if result != 0:
                raise RuntimeError(
                    "native supplemental workspace destroy returned "
                    f"{result}"
                )

    def __enter__(self):
        if self.closed:
            raise RuntimeError("native supplemental workspace is closed")
        return self

    def __exit__(self, _type, _exception, _traceback) -> None:
        self.close()

    def __del__(self) -> None:
        try:
            self.close()
        except (AttributeError, OSError, RuntimeError):
            pass

    def cancel(self) -> None:
        if self.closed:
            return
        result = self._cancel(self._handle)
        if result != 0:
            raise RuntimeError(
                f"native supplemental workspace cancel returned {result}"
            )

    @property
    def active(self) -> bool:
        if self.closed:
            return False
        value = ctypes.c_int()
        result = self._active(self._handle, ctypes.byref(value))
        if result != 0:
            raise RuntimeError(
                f"native supplemental workspace active returned {result}"
            )
        return bool(value.value)

    def query(
        self,
        *,
        horizon: int,
        action_hold_frames: int,
        beam_width: int,
        control_delay_frames: int,
        initial_x: float,
        initial_y: float,
        initial_first_action: int,
        initial_last_action: int,
        initial_risk: float,
        initial_collisions: int,
        initial_minimum_clearance: float,
        initial_immediate_clearance: float,
        action_direction: np.ndarray,
        action_dx: np.ndarray,
        action_dy: np.ndarray,
        action_focused: np.ndarray,
        action_allowed: np.ndarray,
        certificate_collisions: np.ndarray,
        certificate_minimum: np.ndarray,
        survival_preferred: np.ndarray,
        safety_preferred: np.ndarray,
        recovery_distance: np.ndarray,
        repair_volume: np.ndarray,
        bullet_frames: tuple[tuple[np.ndarray, ...], ...],
        laser_frames: tuple[tuple[np.ndarray, ...], ...],
        body_base_x: np.ndarray,
        body_base_y: np.ndarray,
        body_velocity_x: np.ndarray,
        body_velocity_y: np.ndarray,
        body_half_width: np.ndarray,
        body_half_height: np.ndarray,
        player_radius: float,
        preserve_previous_direction_inertia: bool,
        previous_direction: int,
        previous_focused: bool,
        target_x: float | None,
        target_y: float | None,
        target_deadline: int | None,
        item_safety_clearance: float,
        playfield_left: float,
        playfield_right: float,
        playfield_top: float,
        playfield_bottom: float,
        recovery_reserve_distance: float,
        supplemental_reserve_distance: float,
        diagonal_speed: float,
        cardinal_speed: float,
        absolute_deadline_ns: int | None = None,
    ) -> LocalSupplementalNativeResult:
        """Return only a complete endpoint vector; never expose partial work."""

        if self.closed:
            raise RuntimeError("native supplemental workspace is closed")
        if len(bullet_frames) != horizon or len(laser_frames) != horizon:
            raise ValueError(
                "supplemental hazard frame count must equal horizon"
            )
        action_fields = (
            np.ascontiguousarray(action_direction, dtype=np.int32),
            np.ascontiguousarray(action_dx, dtype=np.float64),
            np.ascontiguousarray(action_dy, dtype=np.float64),
            np.ascontiguousarray(action_focused, dtype=np.uint8),
            np.ascontiguousarray(action_allowed, dtype=np.uint8),
            np.ascontiguousarray(
                certificate_collisions,
                dtype=np.int32,
            ),
            np.ascontiguousarray(certificate_minimum, dtype=np.float64),
            np.ascontiguousarray(survival_preferred, dtype=np.uint8),
            np.ascontiguousarray(safety_preferred, dtype=np.uint8),
            np.ascontiguousarray(recovery_distance, dtype=np.float64),
            np.ascontiguousarray(repair_volume, dtype=np.int32),
        )
        action_count = len(action_fields[0])
        if (
            action_count <= 0
            or any(
                values.ndim != 1 or len(values) != action_count
                for values in action_fields
            )
        ):
            raise ValueError(
                "native supplemental action fields must be nonempty peers"
            )
        bullet_offsets, bullets = _frame_major_fields(
            bullet_frames,
            field_count=5,
            dtypes=(
                np.dtype(np.float32),
                np.dtype(np.float32),
                np.dtype(np.float32),
                np.dtype(np.float32),
                np.dtype(np.uint8),
            ),
        )
        laser_offsets, lasers = _frame_major_fields(
            laser_frames,
            field_count=7,
            dtypes=(np.dtype(np.float32),) * 7,
        )
        body_fields = tuple(
            np.ascontiguousarray(values, dtype=np.float32)
            for values in (
                body_base_x,
                body_base_y,
                body_velocity_x,
                body_velocity_y,
                body_half_width,
                body_half_height,
            )
        )
        body_count = len(body_fields[0])
        if any(
            values.ndim != 1 or len(values) != body_count
            for values in body_fields
        ):
            raise ValueError("native supplemental body fields must be peers")
        target_enabled = target_x is not None
        if target_enabled != (
            target_y is not None and target_deadline is not None
        ):
            raise ValueError(
                "native supplemental target fields must be all present"
            )
        timeout_nanoseconds = 0
        if absolute_deadline_ns is not None:
            timeout_nanoseconds = absolute_deadline_ns - time.perf_counter_ns()
            if timeout_nanoseconds <= 0:
                raise LocalSupplementalNativeDeadlineError(
                    "native supplemental packing exceeded its deadline"
                )

        capacity = beam_width
        x = np.empty(capacity, dtype=np.float64)
        y = np.empty(capacity, dtype=np.float64)
        first_action = np.empty(capacity, dtype=np.int32)
        last_action = np.empty(capacity, dtype=np.int32)
        risk = np.empty(capacity, dtype=np.float64)
        collisions = np.empty(capacity, dtype=np.int32)
        minimum = np.empty(capacity, dtype=np.float64)
        immediate = np.empty(capacity, dtype=np.float64)
        count = ctypes.c_int32()
        query = _LocalSupplementalQueryV1(
            ctypes.sizeof(_LocalSupplementalQueryV1),
            horizon,
            action_hold_frames,
            beam_width,
            control_delay_frames,
            action_count,
            initial_x,
            initial_y,
            initial_first_action,
            initial_last_action,
            initial_risk,
            initial_collisions,
            initial_minimum_clearance,
            initial_immediate_clearance,
            action_fields[0].ctypes.data_as(_C_INT32_POINTER),
            action_fields[1].ctypes.data_as(_C_DOUBLE_POINTER),
            action_fields[2].ctypes.data_as(_C_DOUBLE_POINTER),
            action_fields[3].ctypes.data_as(_C_UINT8_POINTER),
            action_fields[4].ctypes.data_as(_C_UINT8_POINTER),
            action_fields[5].ctypes.data_as(_C_INT32_POINTER),
            action_fields[6].ctypes.data_as(_C_DOUBLE_POINTER),
            action_fields[7].ctypes.data_as(_C_UINT8_POINTER),
            action_fields[8].ctypes.data_as(_C_UINT8_POINTER),
            action_fields[9].ctypes.data_as(_C_DOUBLE_POINTER),
            action_fields[10].ctypes.data_as(_C_INT32_POINTER),
            bullet_offsets.ctypes.data_as(_C_INT32_POINTER),
            bullets[0].ctypes.data_as(_C_FLOAT_POINTER),
            bullets[1].ctypes.data_as(_C_FLOAT_POINTER),
            bullets[2].ctypes.data_as(_C_FLOAT_POINTER),
            bullets[3].ctypes.data_as(_C_FLOAT_POINTER),
            bullets[4].ctypes.data_as(_C_UINT8_POINTER),
            laser_offsets.ctypes.data_as(_C_INT32_POINTER),
            lasers[0].ctypes.data_as(_C_FLOAT_POINTER),
            lasers[1].ctypes.data_as(_C_FLOAT_POINTER),
            lasers[2].ctypes.data_as(_C_FLOAT_POINTER),
            lasers[3].ctypes.data_as(_C_FLOAT_POINTER),
            lasers[4].ctypes.data_as(_C_FLOAT_POINTER),
            lasers[5].ctypes.data_as(_C_FLOAT_POINTER),
            lasers[6].ctypes.data_as(_C_FLOAT_POINTER),
            body_count,
            body_fields[0].ctypes.data_as(_C_FLOAT_POINTER),
            body_fields[1].ctypes.data_as(_C_FLOAT_POINTER),
            body_fields[2].ctypes.data_as(_C_FLOAT_POINTER),
            body_fields[3].ctypes.data_as(_C_FLOAT_POINTER),
            body_fields[4].ctypes.data_as(_C_FLOAT_POINTER),
            body_fields[5].ctypes.data_as(_C_FLOAT_POINTER),
            player_radius,
            int(preserve_previous_direction_inertia),
            previous_direction,
            int(previous_focused),
            int(target_enabled),
            0.0 if target_x is None else target_x,
            0.0 if target_y is None else target_y,
            0 if target_deadline is None else target_deadline,
            item_safety_clearance,
            playfield_left,
            playfield_right,
            playfield_top,
            playfield_bottom,
            recovery_reserve_distance,
            supplemental_reserve_distance,
            diagonal_speed,
            cardinal_speed,
            timeout_nanoseconds,
        )
        output = _LocalSupplementalOutputV1(
            ctypes.sizeof(_LocalSupplementalOutputV1),
            capacity,
            x.ctypes.data_as(_C_DOUBLE_POINTER),
            y.ctypes.data_as(_C_DOUBLE_POINTER),
            first_action.ctypes.data_as(_C_INT32_POINTER),
            last_action.ctypes.data_as(_C_INT32_POINTER),
            risk.ctypes.data_as(_C_DOUBLE_POINTER),
            collisions.ctypes.data_as(_C_INT32_POINTER),
            minimum.ctypes.data_as(_C_DOUBLE_POINTER),
            immediate.ctypes.data_as(_C_DOUBLE_POINTER),
            ctypes.pointer(count),
        )
        result = self._query(
            self._handle,
            ctypes.byref(query),
            ctypes.byref(output),
        )
        if result == 5:
            raise LocalSupplementalNativeCancelledError(
                "native supplemental rollout was cancelled"
            )
        if result == 6:
            raise LocalSupplementalNativeDeadlineError(
                "native supplemental rollout exceeded its deadline"
            )
        if result != 0:
            raise RuntimeError(
                f"native supplemental rollout returned {result}"
            )
        retained = int(count.value)
        if retained <= 0 or retained > capacity:
            raise RuntimeError(
                "native supplemental rollout returned invalid count "
                f"{retained}"
            )
        return LocalSupplementalNativeResult(
            x=x[:retained].copy(),
            y=y[:retained].copy(),
            first_action=first_action[:retained].copy(),
            last_action=last_action[:retained].copy(),
            risk=risk[:retained].copy(),
            collisions=collisions[:retained].copy(),
            minimum_clearance=minimum[:retained].copy(),
            immediate_clearance=immediate[:retained].copy(),
        )


def build_clearance_volume(
    *,
    x_axis: np.ndarray,
    y_axis: np.ndarray,
    frame_count: int,
    player_radius: float,
    clearance_cap: float,
    aabbs: tuple[object, ...],
    segments: tuple[object, ...],
) -> np.ndarray | None:
    function = _load_clearance_function()
    if function is None:
        return None
    x_axis = np.ascontiguousarray(x_axis, dtype=np.float32)
    y_axis = np.ascontiguousarray(y_axis, dtype=np.float32)
    aabb_fields = tuple(
        _attribute_array(aabbs, name)
        for name in (
            "x",
            "y",
            "velocity_x",
            "velocity_y",
            "half_width",
            "half_height",
            "base_uncertainty",
            "uncertainty_per_frame",
        )
    )
    segment_fields = tuple(
        _attribute_array(segments, name)
        for name in (
            "origin_x",
            "origin_y",
            "angle",
            "tail",
            "head",
            "half_width",
            "base_uncertainty",
            "uncertainty_per_frame",
        )
    )
    output = np.empty(
        (frame_count, len(y_axis), len(x_axis)),
        dtype=np.float32,
    )
    float_pointer = ctypes.POINTER(ctypes.c_float)
    result = function(
        float(x_axis[0]),
        float(x_axis[1] - x_axis[0]),
        len(x_axis),
        float(y_axis[0]),
        float(y_axis[1] - y_axis[0]),
        len(y_axis),
        frame_count,
        player_radius,
        clearance_cap,
        *(
            values.ctypes.data_as(float_pointer)
            for values in aabb_fields
        ),
        len(aabbs),
        *(
            values.ctypes.data_as(float_pointer)
            for values in segment_fields
        ),
        len(segments),
        output.ctypes.data_as(float_pointer),
    )
    if result != 0:
        raise RuntimeError(f"native clearance kernel returned {result}")
    return output


def apply_segment_trajectory_clearance(
    *,
    x_axis: np.ndarray,
    y_axis: np.ndarray,
    player_radius: float,
    segment_trajectories: tuple[object, ...],
    clearance_volume: np.ndarray,
) -> np.ndarray | None:
    """Apply finite segment samples to an existing clearance volume."""

    if _load_trajectory_clearance_function() is None:
        return None
    packed = PackedSegmentFrames.from_trajectories(
        segment_trajectories,
        frame_count=clearance_volume.shape[0],
    )
    return apply_packed_segment_clearance(
        x_axis=x_axis,
        y_axis=y_axis,
        player_radius=player_radius,
        packed_segments=packed,
        clearance_volume=clearance_volume,
    )


def apply_packed_segment_clearance(
    *,
    x_axis: np.ndarray,
    y_axis: np.ndarray,
    player_radius: float,
    packed_segments: PackedSegmentFrames,
    clearance_volume: np.ndarray,
) -> np.ndarray | None:
    """Apply an already frame-major segment batch without object repacking."""

    function = _load_trajectory_clearance_function()
    if function is None:
        return None
    x_axis = np.ascontiguousarray(x_axis, dtype=np.float32)
    y_axis = np.ascontiguousarray(y_axis, dtype=np.float32)
    output = np.ascontiguousarray(clearance_volume, dtype=np.float32)
    frame_count = output.shape[0]
    if output.shape[1:] != (len(y_axis), len(x_axis)):
        raise ValueError("clearance volume does not match the supplied axes")
    if packed_segments.frame_count != frame_count:
        raise ValueError(
            "packed segment frame count does not match clearance volume"
        )
    segment_fields = (
        packed_segments.origin_x,
        packed_segments.origin_y,
        packed_segments.angle,
        packed_segments.tail,
        packed_segments.head,
        packed_segments.half_width,
        packed_segments.base_uncertainty,
        packed_segments.uncertainty_per_frame,
    )
    float_pointer = ctypes.POINTER(ctypes.c_float)
    result = function(
        float(x_axis[0]),
        float(x_axis[1] - x_axis[0]),
        len(x_axis),
        float(y_axis[0]),
        float(y_axis[1] - y_axis[0]),
        len(y_axis),
        frame_count,
        player_radius,
        packed_segments.frame_offsets.ctypes.data_as(
            ctypes.POINTER(ctypes.c_int32)
        ),
        *(
            values.ctypes.data_as(float_pointer)
            for values in segment_fields
        ),
        packed_segments.sample_count,
        output.ctypes.data_as(float_pointer),
    )
    if result != 0:
        raise RuntimeError(
            f"native segment trajectory clearance kernel returned {result}"
        )
    return output


def apply_aabb_trajectory_clearance(
    *,
    x_axis: np.ndarray,
    y_axis: np.ndarray,
    player_radius: float,
    aabb_trajectories: tuple[object, ...],
    clearance_volume: np.ndarray,
) -> np.ndarray | None:
    """Apply finite AABB samples to an existing clearance volume."""

    function = _load_aabb_trajectory_clearance_function()
    if function is None:
        return None
    x_axis = np.ascontiguousarray(x_axis, dtype=np.float32)
    y_axis = np.ascontiguousarray(y_axis, dtype=np.float32)
    output = np.ascontiguousarray(clearance_volume, dtype=np.float32)
    frame_count = output.shape[0]
    if output.shape[1:] != (len(y_axis), len(x_axis)):
        raise ValueError("clearance volume does not match the supplied axes")

    frame_offsets = np.empty(frame_count + 1, dtype=np.int32)
    samples: list[object] = []
    for frame in range(frame_count):
        frame_offsets[frame] = len(samples)
        samples.extend(
            sample
            for trajectory in aabb_trajectories
            if (sample := trajectory.sample(frame)) is not None
        )
    frame_offsets[frame_count] = len(samples)
    packed_samples = tuple(samples)
    aabb_fields = tuple(
        _attribute_array(packed_samples, name)
        for name in (
            "x",
            "y",
            "half_width",
            "half_height",
            "base_uncertainty",
            "uncertainty_per_frame",
        )
    )
    float_pointer = ctypes.POINTER(ctypes.c_float)
    result = function(
        float(x_axis[0]),
        float(x_axis[1] - x_axis[0]),
        len(x_axis),
        float(y_axis[0]),
        float(y_axis[1] - y_axis[0]),
        len(y_axis),
        frame_count,
        player_radius,
        frame_offsets.ctypes.data_as(ctypes.POINTER(ctypes.c_int32)),
        *(
            values.ctypes.data_as(float_pointer)
            for values in aabb_fields
        ),
        len(packed_samples),
        output.ctypes.data_as(float_pointer),
    )
    if result != 0:
        raise RuntimeError(
            f"native AABB trajectory clearance kernel returned {result}"
        )
    return output


def apply_piecewise_aabb_clearance(
    *,
    x_axis: np.ndarray,
    y_axis: np.ndarray,
    player_radius: float,
    piecewise_aabbs: tuple[object, ...],
    clearance_volume: np.ndarray,
) -> np.ndarray | None:
    """Project sparse velocity events and apply their AABBs natively."""

    function = _load_piecewise_aabb_clearance_function()
    if function is None:
        return None
    x_axis = np.ascontiguousarray(x_axis, dtype=np.float32)
    y_axis = np.ascontiguousarray(y_axis, dtype=np.float32)
    output = np.ascontiguousarray(clearance_volume, dtype=np.float32)
    if output.shape[1:] != (len(y_axis), len(x_axis)):
        raise ValueError("clearance volume does not match the supplied axes")

    motions = tuple(hazard.motion for hazard in piecewise_aabbs)
    hazard_fields = (
        _attribute_array64(motions, "x"),
        _attribute_array64(motions, "y"),
        _attribute_array64(motions, "velocity_x"),
        _attribute_array64(motions, "velocity_y"),
        *(
            _attribute_array(piecewise_aabbs, name)
            for name in (
                "half_width",
                "half_height",
                "base_uncertainty",
                "uncertainty_per_frame",
            )
        ),
    )
    event_offsets = np.empty(len(motions) + 1, dtype=np.int32)
    event_offsets[0] = 0
    event_frames: list[int] = []
    event_velocity_x: list[float] = []
    event_velocity_y: list[float] = []
    for index, motion in enumerate(motions):
        for change in motion.changes:
            event_frames.append(change.frame)
            event_velocity_x.append(change.velocity_x)
            event_velocity_y.append(change.velocity_y)
        event_offsets[index + 1] = len(event_frames)
    packed_event_frames = np.asarray(event_frames, dtype=np.int32)
    packed_event_velocity_x = np.asarray(event_velocity_x, dtype=np.float64)
    packed_event_velocity_y = np.asarray(event_velocity_y, dtype=np.float64)

    float_pointer = ctypes.POINTER(ctypes.c_float)
    double_pointer = ctypes.POINTER(ctypes.c_double)
    result = function(
        float(x_axis[0]),
        float(x_axis[1] - x_axis[0]),
        len(x_axis),
        float(y_axis[0]),
        float(y_axis[1] - y_axis[0]),
        len(y_axis),
        output.shape[0],
        player_radius,
        *(
            values.ctypes.data_as(double_pointer)
            for values in hazard_fields[:4]
        ),
        *(
            values.ctypes.data_as(float_pointer)
            for values in hazard_fields[4:]
        ),
        len(motions),
        event_offsets.ctypes.data_as(ctypes.POINTER(ctypes.c_int32)),
        packed_event_frames.ctypes.data_as(
            ctypes.POINTER(ctypes.c_int32)
        ),
        packed_event_velocity_x.ctypes.data_as(double_pointer),
        packed_event_velocity_y.ctypes.data_as(double_pointer),
        len(event_frames),
        output.ctypes.data_as(float_pointer),
    )
    if result != 0:
        raise RuntimeError(
            f"native piecewise AABB clearance kernel returned {result}"
        )
    return output


def build_viability_arrays(
    *,
    x_axis: np.ndarray,
    y_axis: np.ndarray,
    clearance_volume: np.ndarray,
    velocity_x: np.ndarray,
    velocity_y: np.ndarray,
    delay_frames: np.ndarray,
    frames_per_layer: int,
    required_clearance: float,
    clamp_to_bounds: bool,
    terminal_viable: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray] | None:
    function = (
        _load_terminal_viability_function()
        if terminal_viable is not None
        else _load_viability_function()
    )
    if function is None:
        return None
    x_axis = np.ascontiguousarray(x_axis, dtype=np.float32)
    y_axis = np.ascontiguousarray(y_axis, dtype=np.float32)
    clearance = np.ascontiguousarray(clearance_volume, dtype=np.float32)
    velocity_x = np.ascontiguousarray(velocity_x, dtype=np.float64)
    velocity_y = np.ascontiguousarray(velocity_y, dtype=np.float64)
    delays = np.ascontiguousarray(delay_frames, dtype=np.int32)
    layer_count = (clearance.shape[0] - 1) // frames_per_layer
    action_count = len(velocity_x)
    rows = len(y_axis)
    columns = len(x_axis)
    terminal = None
    if terminal_viable is not None:
        terminal = np.ascontiguousarray(terminal_viable, dtype=np.bool_)
        expected_shape = (action_count, rows, columns)
        if terminal.shape != expected_shape:
            raise ValueError(
                "terminal viability mask must have shape "
                f"{expected_shape}, got {terminal.shape}"
            )
    viable = np.zeros(
        (layer_count + 1, action_count, rows, columns),
        dtype=np.bool_,
    )
    masks = np.zeros(
        (layer_count, action_count, rows, columns),
        dtype=np.uint32,
    )
    arguments = [
        clearance.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        clearance.shape[0],
        rows,
        columns,
        float(x_axis[0]),
        float(x_axis[1] - x_axis[0]),
        float(y_axis[0]),
        float(y_axis[1] - y_axis[0]),
        velocity_x.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        velocity_y.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        action_count,
        delays.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
        len(delays),
        frames_per_layer,
        required_clearance,
        int(clamp_to_bounds),
    ]
    if terminal is not None:
        arguments.append(
            terminal.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8))
        )
    arguments.extend((
        viable.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
        masks.ctypes.data_as(ctypes.POINTER(ctypes.c_uint32)),
    ))
    result = function(*arguments)
    if result != 0:
        raise RuntimeError(f"native viability kernel returned {result}")
    return viable, masks


def build_safety_value_arrays(
    *,
    x_axis: np.ndarray,
    y_axis: np.ndarray,
    clearance_volume: np.ndarray,
    velocity_x: np.ndarray,
    velocity_y: np.ndarray,
    delay_frames: np.ndarray,
    frames_per_layer: int,
    clamp_to_bounds: bool,
) -> tuple[np.ndarray, np.ndarray] | None:
    """Build threshold-free robust state and action clearance values."""

    function = _load_safety_value_function()
    if function is None:
        return None
    x_axis = np.ascontiguousarray(x_axis, dtype=np.float32)
    y_axis = np.ascontiguousarray(y_axis, dtype=np.float32)
    clearance = np.ascontiguousarray(clearance_volume, dtype=np.float32)
    velocity_x = np.ascontiguousarray(velocity_x, dtype=np.float64)
    velocity_y = np.ascontiguousarray(velocity_y, dtype=np.float64)
    delays = np.ascontiguousarray(delay_frames, dtype=np.int32)
    layer_count = (clearance.shape[0] - 1) // frames_per_layer
    action_count = len(velocity_x)
    rows = len(y_axis)
    columns = len(x_axis)
    state_values = np.empty(
        (layer_count + 1, action_count, rows, columns),
        dtype=np.float32,
    )
    action_values = np.empty(
        (
            layer_count,
            action_count,
            action_count,
            rows,
            columns,
        ),
        dtype=np.float32,
    )
    result = function(
        clearance.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        clearance.shape[0],
        rows,
        columns,
        float(x_axis[0]),
        float(x_axis[1] - x_axis[0]),
        float(y_axis[0]),
        float(y_axis[1] - y_axis[0]),
        velocity_x.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        velocity_y.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        action_count,
        delays.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
        len(delays),
        frames_per_layer,
        int(clamp_to_bounds),
        state_values.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        action_values.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
    )
    if result != 0:
        raise RuntimeError(f"native safety-value kernel returned {result}")
    return state_values, action_values


def build_safety_policy_arrays(
    *,
    x_axis: np.ndarray,
    y_axis: np.ndarray,
    clearance_volume: np.ndarray,
    velocity_x: np.ndarray,
    velocity_y: np.ndarray,
    delay_frames: np.ndarray,
    frames_per_layer: int,
    clamp_to_bounds: bool,
) -> tuple[np.ndarray, np.ndarray] | None:
    """Build exact state values and max-min optimal action masks."""

    function = _load_safety_policy_function()
    if function is None:
        return None
    x_axis = np.ascontiguousarray(x_axis, dtype=np.float32)
    y_axis = np.ascontiguousarray(y_axis, dtype=np.float32)
    clearance = np.ascontiguousarray(clearance_volume, dtype=np.float32)
    velocity_x = np.ascontiguousarray(velocity_x, dtype=np.float64)
    velocity_y = np.ascontiguousarray(velocity_y, dtype=np.float64)
    delays = np.ascontiguousarray(delay_frames, dtype=np.int32)
    layer_count = (clearance.shape[0] - 1) // frames_per_layer
    action_count = len(velocity_x)
    rows = len(y_axis)
    columns = len(x_axis)
    state_values = np.empty(
        (layer_count + 1, action_count, rows, columns),
        dtype=np.float32,
    )
    best_action_masks = np.empty(
        (layer_count, action_count, rows, columns),
        dtype=np.uint32,
    )
    result = function(
        clearance.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        clearance.shape[0],
        rows,
        columns,
        float(x_axis[0]),
        float(x_axis[1] - x_axis[0]),
        float(y_axis[0]),
        float(y_axis[1] - y_axis[0]),
        velocity_x.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        velocity_y.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        action_count,
        delays.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
        len(delays),
        frames_per_layer,
        int(clamp_to_bounds),
        state_values.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        best_action_masks.ctypes.data_as(
            ctypes.POINTER(ctypes.c_uint32)
        ),
    )
    if result != 0:
        raise RuntimeError(f"native safety policy kernel returned {result}")
    return state_values, best_action_masks


def build_survival_viability_arrays(
    *,
    x_axis: np.ndarray,
    y_axis: np.ndarray,
    clearance_volume: np.ndarray,
    velocity_x: np.ndarray,
    velocity_y: np.ndarray,
    delay_frames: np.ndarray,
    frames_per_layer: int,
    required_clearance: float,
    clamp_to_bounds: bool,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
] | None:
    """Build lexicographic survival labels and Boolean certificates once."""

    function = _load_survival_viability_function()
    if function is None:
        return None
    x_axis = np.ascontiguousarray(x_axis, dtype=np.float32)
    y_axis = np.ascontiguousarray(y_axis, dtype=np.float32)
    clearance = np.ascontiguousarray(clearance_volume, dtype=np.float32)
    velocity_x = np.ascontiguousarray(velocity_x, dtype=np.float64)
    velocity_y = np.ascontiguousarray(velocity_y, dtype=np.float64)
    delays = np.ascontiguousarray(delay_frames, dtype=np.int32)
    layer_count = (clearance.shape[0] - 1) // frames_per_layer
    action_count = len(velocity_x)
    rows = len(y_axis)
    columns = len(x_axis)
    state_shape = (
        layer_count + 1,
        action_count,
        rows,
        columns,
    )
    action_shape = (
        layer_count,
        action_count,
        rows,
        columns,
    )
    survival_frames = np.empty(state_shape, dtype=np.uint16)
    bottleneck_margins = np.empty(state_shape, dtype=np.float32)
    best_action_masks = np.empty(action_shape, dtype=np.uint32)
    viable = np.empty(state_shape, dtype=np.bool_)
    safe_action_masks = np.empty(action_shape, dtype=np.uint32)
    result = function(
        clearance.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        clearance.shape[0],
        rows,
        columns,
        float(x_axis[0]),
        float(x_axis[1] - x_axis[0]),
        float(y_axis[0]),
        float(y_axis[1] - y_axis[0]),
        velocity_x.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        velocity_y.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        action_count,
        delays.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
        len(delays),
        frames_per_layer,
        required_clearance,
        int(clamp_to_bounds),
        survival_frames.ctypes.data_as(
            ctypes.POINTER(ctypes.c_uint16)
        ),
        bottleneck_margins.ctypes.data_as(
            ctypes.POINTER(ctypes.c_float)
        ),
        best_action_masks.ctypes.data_as(
            ctypes.POINTER(ctypes.c_uint32)
        ),
        viable.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
        safe_action_masks.ctypes.data_as(
            ctypes.POINTER(ctypes.c_uint32)
        ),
    )
    if result != 0:
        raise RuntimeError(
            f"native survival-viability kernel returned {result}"
        )
    return (
        survival_frames,
        bottleneck_margins,
        best_action_masks,
        viable,
        safe_action_masks,
    )


def query_local_survival_arrays(
    *,
    x_axis: np.ndarray,
    y_axis: np.ndarray,
    clearance_volume: np.ndarray,
    velocity_x: np.ndarray,
    velocity_y: np.ndarray,
    delay_frames: np.ndarray,
    decision_frames: int,
    required_clearance: float,
    clamp_to_bounds: bool,
    start_frame: int,
    start_row: int,
    start_column: int,
    observed_action_index: int,
    pending_action_index: int = -1,
    pending_remaining_frames: np.ndarray | None = None,
) -> tuple[int, float, np.ndarray, np.ndarray, int, int] | None:
    """Return one phase-exact survival query from the native sparse kernel."""

    function = _load_query_local_survival_function()
    if function is None:
        return None
    x_axis = np.ascontiguousarray(x_axis, dtype=np.float32)
    y_axis = np.ascontiguousarray(y_axis, dtype=np.float32)
    clearance = np.ascontiguousarray(clearance_volume, dtype=np.float32)
    velocity_x = np.ascontiguousarray(velocity_x, dtype=np.float64)
    velocity_y = np.ascontiguousarray(velocity_y, dtype=np.float64)
    delays = np.ascontiguousarray(delay_frames, dtype=np.int32)
    pending = np.ascontiguousarray(
        (
            np.empty(0, dtype=np.int32)
            if pending_remaining_frames is None
            else pending_remaining_frames
        ),
        dtype=np.int32,
    )
    action_count = len(velocity_x)
    state_frames = ctypes.c_uint16()
    state_margin = ctypes.c_float()
    action_frames = np.empty(action_count, dtype=np.uint16)
    action_margins = np.empty(action_count, dtype=np.float32)
    best_mask = ctypes.c_uint32()
    evaluated_states = ctypes.c_uint64()
    result = function(
        clearance.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        clearance.shape[0],
        len(y_axis),
        len(x_axis),
        float(x_axis[0]),
        float(x_axis[1] - x_axis[0]),
        float(y_axis[0]),
        float(y_axis[1] - y_axis[0]),
        velocity_x.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        velocity_y.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        action_count,
        delays.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
        len(delays),
        decision_frames,
        required_clearance,
        int(clamp_to_bounds),
        start_frame,
        start_row,
        start_column,
        observed_action_index,
        pending_action_index,
        (
            pending.ctypes.data_as(ctypes.POINTER(ctypes.c_int))
            if len(pending)
            else None
        ),
        len(pending),
        ctypes.byref(state_frames),
        ctypes.byref(state_margin),
        action_frames.ctypes.data_as(ctypes.POINTER(ctypes.c_uint16)),
        action_margins.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        ctypes.byref(best_mask),
        ctypes.byref(evaluated_states),
    )
    if result != 0:
        raise RuntimeError(
            f"native query-local survival kernel returned {result}"
        )
    return (
        int(state_frames.value),
        float(state_margin.value),
        action_frames,
        action_margins,
        int(best_mask.value),
        int(evaluated_states.value),
    )


class PipelineNativeCancelledError(RuntimeError):
    """A native workspace was invalidated while expanding."""


class PipelineNativeDeadlineError(RuntimeError):
    """A native workspace query exceeded its cooperative deadline."""


def _raise_pipeline_result(operation: str, result: int) -> None:
    if result == 5:
        raise PipelineNativeCancelledError(
            f"native pipeline workspace {operation} was cancelled"
        )
    if result == 6:
        raise PipelineNativeDeadlineError(
            f"native pipeline workspace {operation} exceeded its deadline"
        )
    raise RuntimeError(
        f"native pipeline workspace {operation} returned {result}"
    )


class PipelineSurvivalNativeWorkspace:
    """Persistent native memo for one immutable clearance policy version."""

    def __init__(
        self,
        *,
        create,
        query,
        contains,
        prewarm,
        merge,
        cancel,
        destroy,
        x_axis: np.ndarray,
        y_axis: np.ndarray,
        clearance_volume: np.ndarray,
        velocity_x: np.ndarray,
        velocity_y: np.ndarray,
        delay_frames: np.ndarray,
        decision_frame_support: np.ndarray,
        continuation_decision_frames: int,
        required_clearance: float,
        clamp_to_bounds: bool,
    ) -> None:
        self._x_axis = np.ascontiguousarray(x_axis, dtype=np.float32)
        self._y_axis = np.ascontiguousarray(y_axis, dtype=np.float32)
        self._clearance = np.ascontiguousarray(
            clearance_volume,
            dtype=np.float32,
        )
        self._velocity_x = np.ascontiguousarray(
            velocity_x,
            dtype=np.float64,
        )
        self._velocity_y = np.ascontiguousarray(
            velocity_y,
            dtype=np.float64,
        )
        self._delays = np.ascontiguousarray(delay_frames, dtype=np.int32)
        self._decision_frames = np.ascontiguousarray(
            decision_frame_support,
            dtype=np.int32,
        )
        self._query = query
        self._contains = contains
        self._prewarm = prewarm
        self._merge = merge
        self._cancel = cancel
        self._destroy = destroy
        self._handle = ctypes.c_void_p()
        result = create(
            self._clearance.ctypes.data_as(
                ctypes.POINTER(ctypes.c_float)
            ),
            self._clearance.shape[0],
            len(self._y_axis),
            len(self._x_axis),
            float(self._x_axis[0]),
            float(self._x_axis[1] - self._x_axis[0]),
            float(self._y_axis[0]),
            float(self._y_axis[1] - self._y_axis[0]),
            self._velocity_x.ctypes.data_as(
                ctypes.POINTER(ctypes.c_double)
            ),
            self._velocity_y.ctypes.data_as(
                ctypes.POINTER(ctypes.c_double)
            ),
            len(self._velocity_x),
            self._delays.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
            len(self._delays),
            self._decision_frames.ctypes.data_as(
                ctypes.POINTER(ctypes.c_int)
            ),
            len(self._decision_frames),
            continuation_decision_frames,
            required_clearance,
            int(clamp_to_bounds),
            ctypes.byref(self._handle),
        )
        if result != 0 or not self._handle.value:
            self._handle = ctypes.c_void_p()
            raise RuntimeError(
                f"native pipeline workspace create returned {result}"
            )

    @property
    def closed(self) -> bool:
        return not bool(self._handle.value)

    def close(self) -> None:
        if self._handle.value:
            self._destroy(self._handle)
            self._handle = ctypes.c_void_p()

    def __enter__(self):
        if self.closed:
            raise RuntimeError("native pipeline workspace is closed")
        return self

    def __exit__(self, _exception_type, _exception, _traceback) -> None:
        self.close()

    def __del__(self) -> None:
        try:
            self.close()
        except (AttributeError, OSError):
            pass

    def query(
        self,
        *,
        start_frame: int,
        start_row: int,
        start_column: int,
        observed_action_index: int,
        pending_action_index: int = -1,
        pending_remaining_frames: np.ndarray | None = None,
        timeout_ms: int = 0,
    ) -> tuple[
        int,
        float,
        np.ndarray,
        np.ndarray,
        int,
        np.ndarray,
    ]:
        if self.closed:
            raise RuntimeError("native pipeline workspace is closed")
        pending = np.ascontiguousarray(
            (
                np.empty(0, dtype=np.int32)
                if pending_remaining_frames is None
                else pending_remaining_frames
            ),
            dtype=np.int32,
        )
        action_count = len(self._velocity_x)
        state_frames = ctypes.c_uint16()
        state_margin = ctypes.c_float()
        action_frames = np.empty(action_count, dtype=np.uint16)
        action_margins = np.empty(action_count, dtype=np.float32)
        best_mask = ctypes.c_uint32()
        stats = np.empty(8, dtype=np.uint64)
        result = self._query(
            self._handle,
            start_frame,
            start_row,
            start_column,
            observed_action_index,
            pending_action_index,
            (
                pending.ctypes.data_as(ctypes.POINTER(ctypes.c_int))
                if len(pending)
                else None
            ),
            len(pending),
            timeout_ms,
            ctypes.byref(state_frames),
            ctypes.byref(state_margin),
            action_frames.ctypes.data_as(
                ctypes.POINTER(ctypes.c_uint16)
            ),
            action_margins.ctypes.data_as(
                ctypes.POINTER(ctypes.c_float)
            ),
            ctypes.byref(best_mask),
            stats.ctypes.data_as(ctypes.POINTER(ctypes.c_uint64)),
        )
        if result != 0:
            _raise_pipeline_result("query", result)
        return (
            int(state_frames.value),
            float(state_margin.value),
            action_frames,
            action_margins,
            int(best_mask.value),
            stats,
        )

    def contains_root(
        self,
        *,
        start_frame: int,
        start_row: int,
        start_column: int,
        observed_action_index: int,
        pending_action_index: int = -1,
        pending_remaining_frames: np.ndarray | None = None,
    ) -> bool:
        """Return whether every branch of an exact public root is cached."""

        if self.closed:
            raise RuntimeError("native pipeline workspace is closed")
        pending = np.ascontiguousarray(
            (
                np.empty(0, dtype=np.int32)
                if pending_remaining_frames is None
                else pending_remaining_frames
            ),
            dtype=np.int32,
        )
        present = ctypes.c_int()
        result = self._contains(
            self._handle,
            start_frame,
            start_row,
            start_column,
            observed_action_index,
            pending_action_index,
            (
                pending.ctypes.data_as(ctypes.POINTER(ctypes.c_int))
                if len(pending)
                else None
            ),
            len(pending),
            ctypes.byref(present),
        )
        if result != 0:
            raise RuntimeError(
                f"native pipeline workspace lookup returned {result}"
            )
        return bool(present.value)

    def prewarm_continuation(
        self,
        *,
        start_frame: int,
        start_row: int,
        start_column: int,
        observed_action_index: int,
        pending_action_index: int = -1,
        pending_remaining_frames: np.ndarray | None = None,
        timeout_ms: int = 0,
    ) -> tuple[int, float, np.ndarray]:
        """Populate fixed-cadence continuation values without root labels."""

        if self.closed:
            raise RuntimeError("native pipeline workspace is closed")
        pending = np.ascontiguousarray(
            (
                np.empty(0, dtype=np.int32)
                if pending_remaining_frames is None
                else pending_remaining_frames
            ),
            dtype=np.int32,
        )
        state_frames = ctypes.c_uint16()
        state_margin = ctypes.c_float()
        stats = np.empty(8, dtype=np.uint64)
        result = self._prewarm(
            self._handle,
            start_frame,
            start_row,
            start_column,
            observed_action_index,
            pending_action_index,
            (
                pending.ctypes.data_as(ctypes.POINTER(ctypes.c_int))
                if len(pending)
                else None
            ),
            len(pending),
            timeout_ms,
            ctypes.byref(state_frames),
            ctypes.byref(state_margin),
            stats.ctypes.data_as(ctypes.POINTER(ctypes.c_uint64)),
        )
        if result != 0:
            _raise_pipeline_result("prewarm", result)
        return int(state_frames.value), float(state_margin.value), stats

    def merge_continuation_from(
        self,
        source: PipelineSurvivalNativeWorkspace,
    ) -> int:
        """Merge completed continuation labels from a compatible workspace."""

        if self.closed or source.closed:
            raise RuntimeError("cannot merge a closed pipeline workspace")
        added = ctypes.c_uint64()
        result = self._merge(
            self._handle,
            source._handle,
            ctypes.byref(added),
        )
        if result != 0:
            _raise_pipeline_result("merge", result)
        return int(added.value)

    def cancel(self) -> None:
        """Cooperatively invalidate current and future native expansion."""

        if self.closed:
            return
        result = self._cancel(self._handle)
        if result != 0:
            _raise_pipeline_result("cancel", result)


def create_pipeline_survival_workspace(
    *,
    x_axis: np.ndarray,
    y_axis: np.ndarray,
    clearance_volume: np.ndarray,
    velocity_x: np.ndarray,
    velocity_y: np.ndarray,
    delay_frames: np.ndarray,
    decision_frame_support: np.ndarray,
    continuation_decision_frames: int,
    required_clearance: float,
    clamp_to_bounds: bool,
) -> PipelineSurvivalNativeWorkspace | None:
    """Create a persistent exact pipeline memo, or None without native code."""

    functions = _load_pipeline_workspace_functions()
    if functions is None:
        return None
    create, query, contains, prewarm, merge, cancel, destroy = functions
    return PipelineSurvivalNativeWorkspace(
        create=create,
        query=query,
        contains=contains,
        prewarm=prewarm,
        merge=merge,
        cancel=cancel,
        destroy=destroy,
        x_axis=x_axis,
        y_axis=y_axis,
        clearance_volume=clearance_volume,
        velocity_x=velocity_x,
        velocity_y=velocity_y,
        delay_frames=delay_frames,
        decision_frame_support=decision_frame_support,
        continuation_decision_frames=continuation_decision_frames,
        required_clearance=required_clearance,
        clamp_to_bounds=clamp_to_bounds,
    )


class BeliefPipelineNativeWorkspace:
    """Persistent native memo for the recursive information-set game."""

    def __init__(
        self,
        *,
        create,
        query,
        certify,
        recommend,
        cancel,
        destroy,
        x_axis: np.ndarray,
        y_axis: np.ndarray,
        clearance_volume: np.ndarray,
        velocity_x: np.ndarray,
        velocity_y: np.ndarray,
        base_action_mask: int,
        budgeted_action_mask: int,
        continuation_action_budget: int,
        remaining_delay_bucket_size: int,
        continuation_policy_mode: int,
        delay_frames: np.ndarray,
        decision_frame_support: np.ndarray,
        required_clearance: float,
        clamp_to_bounds: bool,
    ) -> None:
        self._x_axis = np.ascontiguousarray(x_axis, dtype=np.float32)
        self._y_axis = np.ascontiguousarray(y_axis, dtype=np.float32)
        self._clearance = np.ascontiguousarray(
            clearance_volume,
            dtype=np.float32,
        )
        self._velocity_x = np.ascontiguousarray(
            velocity_x,
            dtype=np.float64,
        )
        self._velocity_y = np.ascontiguousarray(
            velocity_y,
            dtype=np.float64,
        )
        self._delays = np.ascontiguousarray(
            delay_frames,
            dtype=np.int32,
        )
        self._decision_frames = np.ascontiguousarray(
            decision_frame_support,
            dtype=np.int32,
        )
        self._query = query
        self._certify = certify
        self._recommend = recommend
        self._cancel = cancel
        self._destroy = destroy
        self._handle = ctypes.c_void_p()
        result = create(
            self._clearance.ctypes.data_as(
                ctypes.POINTER(ctypes.c_float)
            ),
            self._clearance.shape[0],
            len(self._y_axis),
            len(self._x_axis),
            float(self._x_axis[0]),
            float(self._x_axis[1] - self._x_axis[0]),
            float(self._y_axis[0]),
            float(self._y_axis[1] - self._y_axis[0]),
            self._velocity_x.ctypes.data_as(
                ctypes.POINTER(ctypes.c_double)
            ),
            self._velocity_y.ctypes.data_as(
                ctypes.POINTER(ctypes.c_double)
            ),
            len(self._velocity_x),
            base_action_mask,
            budgeted_action_mask,
            continuation_action_budget,
            remaining_delay_bucket_size,
            continuation_policy_mode,
            self._delays.ctypes.data_as(
                ctypes.POINTER(ctypes.c_int)
            ),
            len(self._delays),
            self._decision_frames.ctypes.data_as(
                ctypes.POINTER(ctypes.c_int)
            ),
            len(self._decision_frames),
            required_clearance,
            int(clamp_to_bounds),
            ctypes.byref(self._handle),
        )
        if result != 0 or not self._handle.value:
            self._handle = ctypes.c_void_p()
            raise RuntimeError(
                f"native belief pipeline create returned {result}"
            )

    @property
    def closed(self) -> bool:
        return not bool(self._handle.value)

    def close(self) -> None:
        if self._handle.value:
            self._destroy(self._handle)
            self._handle = ctypes.c_void_p()

    def __enter__(self):
        if self.closed:
            raise RuntimeError("belief pipeline workspace is closed")
        return self

    def __exit__(self, _exception_type, _exception, _traceback) -> None:
        self.close()

    def __del__(self) -> None:
        try:
            self.close()
        except (AttributeError, OSError):
            pass

    def query(
        self,
        *,
        start_frame: int,
        start_row: int,
        start_column: int,
        observed_action_index: int,
        pending_action_index: int = -1,
        pending_remaining_frames: np.ndarray | None = None,
        continuation_action_budget: int | None = None,
        timeout_ms: int = 0,
    ) -> tuple[
        int,
        float,
        np.ndarray,
        np.ndarray,
        int,
        np.ndarray,
    ]:
        if self.closed:
            raise RuntimeError("belief pipeline workspace is closed")
        pending = np.ascontiguousarray(
            (
                np.empty(0, dtype=np.int32)
                if pending_remaining_frames is None
                else pending_remaining_frames
            ),
            dtype=np.int32,
        )
        action_count = len(self._velocity_x)
        state_frames = ctypes.c_uint16()
        state_margin = ctypes.c_float()
        action_frames = np.empty(action_count, dtype=np.uint16)
        action_margins = np.empty(action_count, dtype=np.float32)
        best_mask = ctypes.c_uint32()
        stats = np.empty(8, dtype=np.uint64)
        result = self._query(
            self._handle,
            start_frame,
            start_row,
            start_column,
            observed_action_index,
            pending_action_index,
            (
                pending.ctypes.data_as(ctypes.POINTER(ctypes.c_int))
                if len(pending)
                else None
            ),
            len(pending),
            (
                -1
                if continuation_action_budget is None
                else continuation_action_budget
            ),
            timeout_ms,
            ctypes.byref(state_frames),
            ctypes.byref(state_margin),
            action_frames.ctypes.data_as(
                ctypes.POINTER(ctypes.c_uint16)
            ),
            action_margins.ctypes.data_as(
                ctypes.POINTER(ctypes.c_float)
            ),
            ctypes.byref(best_mask),
            stats.ctypes.data_as(ctypes.POINTER(ctypes.c_uint64)),
        )
        if result != 0:
            _raise_pipeline_result("belief query", result)
        return (
            int(state_frames.value),
            float(state_margin.value),
            action_frames,
            action_margins,
            int(best_mask.value),
            stats,
        )

    def cancel(self) -> None:
        if self.closed:
            return
        result = self._cancel(self._handle)
        if result != 0:
            _raise_pipeline_result("belief cancel", result)

    def certify_upper(
        self,
        *,
        start_frame: int,
        start_row: int,
        start_column: int,
        observed_action_index: int,
        lower_frames: int,
        lower_margin: float,
        pending_action_index: int = -1,
        pending_remaining_frames: np.ndarray | None = None,
        continuation_action_budget: int | None = None,
        timeout_ms: int = 0,
    ) -> tuple[int, bool, np.ndarray]:
        """Return actions whose optimistic value can exceed the lower."""

        if self.closed:
            raise RuntimeError("belief pipeline workspace is closed")
        pending = np.ascontiguousarray(
            (
                np.empty(0, dtype=np.int32)
                if pending_remaining_frames is None
                else pending_remaining_frames
            ),
            dtype=np.int32,
        )
        unresolved_mask = ctypes.c_uint32()
        deadline_expired = ctypes.c_int()
        stats = np.empty(8, dtype=np.uint64)
        result = self._certify(
            self._handle,
            start_frame,
            start_row,
            start_column,
            observed_action_index,
            pending_action_index,
            (
                pending.ctypes.data_as(ctypes.POINTER(ctypes.c_int))
                if len(pending)
                else None
            ),
            len(pending),
            (
                -1
                if continuation_action_budget is None
                else continuation_action_budget
            ),
            lower_frames,
            lower_margin,
            timeout_ms,
            ctypes.byref(unresolved_mask),
            ctypes.byref(deadline_expired),
            stats.ctypes.data_as(ctypes.POINTER(ctypes.c_uint64)),
        )
        if result != 0:
            _raise_pipeline_result("belief upper certification", result)
        return (
            int(unresolved_mask.value),
            bool(deadline_expired.value),
            stats,
        )

    def recommend_action_column(
        self,
        *,
        start_frame: int,
        start_row: int,
        start_column: int,
        observed_action_index: int,
        target_root_action_index: int,
        pending_action_index: int = -1,
        pending_remaining_frames: np.ndarray | None = None,
        max_depth: int = 64,
        timeout_ms: int = 0,
    ) -> tuple[
        int,
        tuple[int, int, int, int, int, int],
        tuple[int, float],
        tuple[int, float],
        int,
        np.ndarray,
    ]:
        """Find one excluded action improving a worst restricted path."""

        if self.closed:
            raise RuntimeError("belief pipeline workspace is closed")
        pending = np.ascontiguousarray(
            (
                np.empty(0, dtype=np.int32)
                if pending_remaining_frames is None
                else pending_remaining_frames
            ),
            dtype=np.int32,
        )
        recommended_action = ctypes.c_int()
        witness_frame = ctypes.c_int()
        witness_row = ctypes.c_int()
        witness_column = ctypes.c_int()
        witness_active = ctypes.c_int()
        witness_pending = ctypes.c_int()
        witness_remaining_mask = ctypes.c_uint64()
        current_frames = ctypes.c_uint16()
        current_margin = ctypes.c_float()
        recommended_frames = ctypes.c_uint16()
        recommended_margin = ctypes.c_float()
        depth = ctypes.c_int()
        stats = np.empty(8, dtype=np.uint64)
        result = self._recommend(
            self._handle,
            start_frame,
            start_row,
            start_column,
            observed_action_index,
            pending_action_index,
            (
                pending.ctypes.data_as(ctypes.POINTER(ctypes.c_int))
                if len(pending)
                else None
            ),
            len(pending),
            target_root_action_index,
            max_depth,
            timeout_ms,
            ctypes.byref(recommended_action),
            ctypes.byref(witness_frame),
            ctypes.byref(witness_row),
            ctypes.byref(witness_column),
            ctypes.byref(witness_active),
            ctypes.byref(witness_pending),
            ctypes.byref(witness_remaining_mask),
            ctypes.byref(current_frames),
            ctypes.byref(current_margin),
            ctypes.byref(recommended_frames),
            ctypes.byref(recommended_margin),
            ctypes.byref(depth),
            stats.ctypes.data_as(ctypes.POINTER(ctypes.c_uint64)),
        )
        if result != 0:
            _raise_pipeline_result(
                "belief action-column recommendation",
                result,
            )
        return (
            int(recommended_action.value),
            (
                int(witness_frame.value),
                int(witness_row.value),
                int(witness_column.value),
                int(witness_active.value),
                int(witness_pending.value),
                int(witness_remaining_mask.value),
            ),
            (int(current_frames.value), float(current_margin.value)),
            (
                int(recommended_frames.value),
                float(recommended_margin.value),
            ),
            int(depth.value),
            stats,
        )


def create_belief_pipeline_survival_workspace(
    *,
    x_axis: np.ndarray,
    y_axis: np.ndarray,
    clearance_volume: np.ndarray,
    velocity_x: np.ndarray,
    velocity_y: np.ndarray,
    base_action_mask: int,
    budgeted_action_mask: int = 0,
    continuation_action_budget: int = 0,
    remaining_delay_bucket_size: int = 0,
    continuation_policy_mode: int = 0,
    delay_frames: np.ndarray,
    decision_frame_support: np.ndarray,
    required_clearance: float,
    clamp_to_bounds: bool,
) -> BeliefPipelineNativeWorkspace | None:
    """Create the recursive belief-state workspace when native code exists."""

    functions = _load_belief_pipeline_workspace_functions()
    if functions is None:
        return None
    create, query, certify, recommend, cancel, destroy = functions
    return BeliefPipelineNativeWorkspace(
        create=create,
        query=query,
        certify=certify,
        recommend=recommend,
        cancel=cancel,
        destroy=destroy,
        x_axis=x_axis,
        y_axis=y_axis,
        clearance_volume=clearance_volume,
        velocity_x=velocity_x,
        velocity_y=velocity_y,
        base_action_mask=base_action_mask,
        budgeted_action_mask=budgeted_action_mask,
        continuation_action_budget=continuation_action_budget,
        remaining_delay_bucket_size=remaining_delay_bucket_size,
        continuation_policy_mode=continuation_policy_mode,
        delay_frames=delay_frames,
        decision_frame_support=decision_frame_support,
        required_clearance=required_clearance,
        clamp_to_bounds=clamp_to_bounds,
    )


def build_losing_survival_label_arrays(
    *,
    x_axis: np.ndarray,
    y_axis: np.ndarray,
    clearance_volume: np.ndarray,
    velocity_x: np.ndarray,
    velocity_y: np.ndarray,
    delay_frames: np.ndarray,
    frames_per_layer: int,
    required_clearance: float,
    clamp_to_bounds: bool,
    viable: np.ndarray,
    safe_action_masks: np.ndarray,
    worker_count: int = 1,
) -> tuple[np.ndarray, np.ndarray, np.ndarray] | None:
    """Label only Boolean-losing states after policy publication."""

    function = _load_losing_survival_labels_function()
    if function is None:
        return None
    x_axis = np.ascontiguousarray(x_axis, dtype=np.float32)
    y_axis = np.ascontiguousarray(y_axis, dtype=np.float32)
    clearance = np.ascontiguousarray(clearance_volume, dtype=np.float32)
    velocity_x = np.ascontiguousarray(velocity_x, dtype=np.float64)
    velocity_y = np.ascontiguousarray(velocity_y, dtype=np.float64)
    delays = np.ascontiguousarray(delay_frames, dtype=np.int32)
    viable = np.ascontiguousarray(viable, dtype=np.bool_)
    masks = np.ascontiguousarray(safe_action_masks, dtype=np.uint32)
    survival_frames = np.empty(viable.shape, dtype=np.uint16)
    bottleneck_margins = np.empty(viable.shape, dtype=np.float32)
    best_action_masks = np.empty(masks.shape, dtype=np.uint32)
    result = function(
        clearance.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        clearance.shape[0],
        len(y_axis),
        len(x_axis),
        float(x_axis[0]),
        float(x_axis[1] - x_axis[0]),
        float(y_axis[0]),
        float(y_axis[1] - y_axis[0]),
        velocity_x.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        velocity_y.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        len(velocity_x),
        delays.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
        len(delays),
        frames_per_layer,
        required_clearance,
        int(clamp_to_bounds),
        worker_count,
        viable.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
        masks.ctypes.data_as(ctypes.POINTER(ctypes.c_uint32)),
        survival_frames.ctypes.data_as(
            ctypes.POINTER(ctypes.c_uint16)
        ),
        bottleneck_margins.ctypes.data_as(
            ctypes.POINTER(ctypes.c_float)
        ),
        best_action_masks.ctypes.data_as(
            ctypes.POINTER(ctypes.c_uint32)
        ),
    )
    if result != 0:
        raise RuntimeError(
            f"native losing-survival label kernel returned {result}"
        )
    return survival_frames, bottleneck_margins, best_action_masks
