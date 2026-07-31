"""Native viability, safety-value, and survival-label bindings."""

from __future__ import annotations

import ctypes

import numpy as np

from .arrays import as_contiguous_array
from .library import (
    cache_function,
    cached_function,
    load_library as _load_library,
)


def _load_viability_function():
    cached = cached_function("touhou_robust_viability_v1")
    if cached is not None:
        return cached
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
    return cache_function("touhou_robust_viability_v1", function)


def _load_viability_worker_limit_function():
    cached = cached_function(
        "touhou_set_current_thread_viability_worker_limit_v1"
    )
    if cached is not None:
        return cached
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
    return cache_function(
        "touhou_set_current_thread_viability_worker_limit_v1",
        function,
    )


def set_current_thread_viability_worker_limit(
    worker_limit: int,
) -> bool:
    """Bound native viability fan-out on the calling Python thread."""

    if not 1 <= worker_limit <= 16:
        raise ValueError("native viability worker limit must be 1..16")
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
    cached = cached_function("touhou_robust_viability_terminal_v1")
    if cached is not None:
        return cached
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
    return cache_function(
        "touhou_robust_viability_terminal_v1",
        function,
    )


def _load_safety_value_function():
    cached = cached_function("touhou_robust_safety_value_v1")
    if cached is not None:
        return cached
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
    return cache_function("touhou_robust_safety_value_v1", function)


def _load_safety_policy_function():
    cached = cached_function("touhou_robust_safety_policy_v1")
    if cached is not None:
        return cached
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
    return cache_function("touhou_robust_safety_policy_v1", function)


def _load_survival_viability_function():
    cached = cached_function("touhou_robust_survival_viability_v1")
    if cached is not None:
        return cached
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
    return cache_function(
        "touhou_robust_survival_viability_v1",
        function,
    )


def _load_query_local_survival_function():
    cached = cached_function("touhou_query_local_survival_v1")
    if cached is not None:
        return cached
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
    return cache_function("touhou_query_local_survival_v1", function)


def _load_losing_survival_labels_function():
    cached = cached_function("touhou_losing_survival_labels_v1")
    if cached is not None:
        return cached
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
    return cache_function("touhou_losing_survival_labels_v1", function)


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
    x_axis = as_contiguous_array(x_axis, dtype=np.float32)
    y_axis = as_contiguous_array(y_axis, dtype=np.float32)
    clearance = as_contiguous_array(clearance_volume, dtype=np.float32)
    velocity_x = as_contiguous_array(velocity_x, dtype=np.float64)
    velocity_y = as_contiguous_array(velocity_y, dtype=np.float64)
    delays = as_contiguous_array(delay_frames, dtype=np.int32)
    layer_count = (clearance.shape[0] - 1) // frames_per_layer
    action_count = len(velocity_x)
    rows = len(y_axis)
    columns = len(x_axis)
    terminal = None
    if terminal_viable is not None:
        terminal = as_contiguous_array(terminal_viable, dtype=np.bool_)
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
    x_axis = as_contiguous_array(x_axis, dtype=np.float32)
    y_axis = as_contiguous_array(y_axis, dtype=np.float32)
    clearance = as_contiguous_array(clearance_volume, dtype=np.float32)
    velocity_x = as_contiguous_array(velocity_x, dtype=np.float64)
    velocity_y = as_contiguous_array(velocity_y, dtype=np.float64)
    delays = as_contiguous_array(delay_frames, dtype=np.int32)
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
    x_axis = as_contiguous_array(x_axis, dtype=np.float32)
    y_axis = as_contiguous_array(y_axis, dtype=np.float32)
    clearance = as_contiguous_array(clearance_volume, dtype=np.float32)
    velocity_x = as_contiguous_array(velocity_x, dtype=np.float64)
    velocity_y = as_contiguous_array(velocity_y, dtype=np.float64)
    delays = as_contiguous_array(delay_frames, dtype=np.int32)
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
    x_axis = as_contiguous_array(x_axis, dtype=np.float32)
    y_axis = as_contiguous_array(y_axis, dtype=np.float32)
    clearance = as_contiguous_array(clearance_volume, dtype=np.float32)
    velocity_x = as_contiguous_array(velocity_x, dtype=np.float64)
    velocity_y = as_contiguous_array(velocity_y, dtype=np.float64)
    delays = as_contiguous_array(delay_frames, dtype=np.int32)
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
    x_axis = as_contiguous_array(x_axis, dtype=np.float32)
    y_axis = as_contiguous_array(y_axis, dtype=np.float32)
    clearance = as_contiguous_array(clearance_volume, dtype=np.float32)
    velocity_x = as_contiguous_array(velocity_x, dtype=np.float64)
    velocity_y = as_contiguous_array(velocity_y, dtype=np.float64)
    delays = as_contiguous_array(delay_frames, dtype=np.int32)
    pending = as_contiguous_array(
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
    x_axis = as_contiguous_array(x_axis, dtype=np.float32)
    y_axis = as_contiguous_array(y_axis, dtype=np.float32)
    clearance = as_contiguous_array(clearance_volume, dtype=np.float32)
    velocity_x = as_contiguous_array(velocity_x, dtype=np.float64)
    velocity_y = as_contiguous_array(velocity_y, dtype=np.float64)
    delays = as_contiguous_array(delay_frames, dtype=np.int32)
    viable = as_contiguous_array(viable, dtype=np.bool_)
    masks = as_contiguous_array(safe_action_masks, dtype=np.uint32)
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
