"""Optional C ABI backend for time-expanded hazards and viability."""

from __future__ import annotations

import ctypes
import os
from pathlib import Path

import numpy as np

from .packed_hazards import PackedSegmentFrames


ROOT = Path(__file__).resolve().parents[2]
_DISABLE_ENV = "TOUHOU_DISABLE_NATIVE_PLANNER"
_LIBRARY = None
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
_BELIEF_PIPELINE_CANCEL_FUNCTION = None
_BELIEF_PIPELINE_DESTROY_FUNCTION = None
_LOSING_SURVIVAL_LABELS_FUNCTION = None
_CLEARANCE_FUNCTION = None
_AABB_TRAJECTORY_CLEARANCE_FUNCTION = None
_PIECEWISE_AABB_CLEARANCE_FUNCTION = None
_TRAJECTORY_CLEARANCE_FUNCTION = None
_LOAD_ERROR: OSError | None = None


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
    global _BELIEF_PIPELINE_CANCEL_FUNCTION
    global _BELIEF_PIPELINE_DESTROY_FUNCTION
    if (
        _BELIEF_PIPELINE_CREATE_FUNCTION is not None
        and _BELIEF_PIPELINE_QUERY_FUNCTION is not None
        and _BELIEF_PIPELINE_CERTIFY_FUNCTION is not None
        and _BELIEF_PIPELINE_CANCEL_FUNCTION is not None
        and _BELIEF_PIPELINE_DESTROY_FUNCTION is not None
    ):
        return (
            _BELIEF_PIPELINE_CREATE_FUNCTION,
            _BELIEF_PIPELINE_QUERY_FUNCTION,
            _BELIEF_PIPELINE_CERTIFY_FUNCTION,
            _BELIEF_PIPELINE_CANCEL_FUNCTION,
            _BELIEF_PIPELINE_DESTROY_FUNCTION,
        )
    library = _load_library()
    if library is None:
        return None
    try:
        create = library.touhou_belief_pipeline_workspace_create_v4
        query = library.touhou_belief_pipeline_workspace_query_v2
        certify = (
            library.touhou_belief_pipeline_workspace_certify_upper_v1
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
        ctypes.POINTER(ctypes.c_uint64),
    ]
    certify.restype = ctypes.c_int
    cancel.argtypes = [ctypes.c_void_p]
    cancel.restype = ctypes.c_int
    destroy.argtypes = [ctypes.c_void_p]
    destroy.restype = None
    _BELIEF_PIPELINE_CREATE_FUNCTION = create
    _BELIEF_PIPELINE_QUERY_FUNCTION = query
    _BELIEF_PIPELINE_CERTIFY_FUNCTION = certify
    _BELIEF_PIPELINE_CANCEL_FUNCTION = cancel
    _BELIEF_PIPELINE_DESTROY_FUNCTION = destroy
    return create, query, certify, cancel, destroy


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
        reveal_remaining_delay: bool,
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
            int(reveal_remaining_delay),
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
    ) -> tuple[int, np.ndarray]:
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
            stats.ctypes.data_as(ctypes.POINTER(ctypes.c_uint64)),
        )
        if result != 0:
            _raise_pipeline_result("belief upper certification", result)
        return int(unresolved_mask.value), stats


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
    reveal_remaining_delay: bool = False,
    delay_frames: np.ndarray,
    decision_frame_support: np.ndarray,
    required_clearance: float,
    clamp_to_bounds: bool,
) -> BeliefPipelineNativeWorkspace | None:
    """Create the recursive belief-state workspace when native code exists."""

    functions = _load_belief_pipeline_workspace_functions()
    if functions is None:
        return None
    create, query, certify, cancel, destroy = functions
    return BeliefPipelineNativeWorkspace(
        create=create,
        query=query,
        certify=certify,
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
        reveal_remaining_delay=reveal_remaining_delay,
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
