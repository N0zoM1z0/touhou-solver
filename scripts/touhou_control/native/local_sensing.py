"""Native local hazard queries and raw bullet-pool decoding."""

from __future__ import annotations

import ctypes

import numpy as np

from .arrays import as_contiguous_array
from .local_abi import DecodedBulletPool
from .library import (
    cache_function,
    cached_function,
    load_library as _load_library,
)


def _load_local_hazards_function():
    cached = cached_function("touhou_local_hazards_v1")
    if cached is not None:
        return cached
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
    return cache_function("touhou_local_hazards_v1", function)



def _load_bullet_pool_decode_function():
    cached = cached_function("touhou_decode_bullet_pool_v1")
    if cached is not None:
        return cached
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
    return cache_function("touhou_decode_bullet_pool_v1", function)



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
    positions_x = as_contiguous_array(positions_x, dtype=np.float32)
    positions_y = as_contiguous_array(positions_y, dtype=np.float32)
    if (
        positions_x.ndim != 1
        or positions_y.shape != positions_x.shape
        or not len(positions_x)
    ):
        raise ValueError("local hazard positions must be nonempty 1D peers")
    bullet_fields = tuple(
        as_contiguous_array(values, dtype=np.float32)
        for values in (
            bullet_x,
            bullet_y,
            bullet_half_width,
            bullet_half_height,
        )
    )
    bullet_transformed = as_contiguous_array(bullet_transformed)
    if bullet_transformed.dtype not in {
        np.dtype(np.bool_),
        np.dtype(np.uint8),
    }:
        bullet_transformed = as_contiguous_array(
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
        as_contiguous_array(values, dtype=np.float32)
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
        as_contiguous_array(values, dtype=np.float32)
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



__all__ = [
    "DecodedBulletPool",
    "decode_bullet_pool",
    "query_local_hazards",
]
