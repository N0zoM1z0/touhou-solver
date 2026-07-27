"""Native local sensing, beam reduction, and rollout bindings."""

from __future__ import annotations

import ctypes
import time

import numpy as np

from .arrays import as_contiguous_array
from .local_abi import (
    DecodedBulletPool as DecodedBulletPool,
    LocalSupplementalNativeCancelledError,
    LocalSupplementalNativeDeadlineError,
    LocalSupplementalNativeResult,
    _C_DOUBLE_POINTER,
    _C_FLOAT_POINTER,
    _C_INT32_POINTER,
    _C_UINT8_POINTER,
    _LocalSupplementalOutputV1,
    _LocalSupplementalQueryV1,
)
from .local_sensing import (
    _load_bullet_pool_decode_function as _load_bullet_pool_decode_function,
    _load_local_hazards_function as _load_local_hazards_function,
    decode_bullet_pool as decode_bullet_pool,
    query_local_hazards as query_local_hazards,
)
from .library import (
    cache_function,
    cache_function_group,
    cached_function,
    cached_function_group,
    load_library as _load_library,
)










def _load_local_beam_reduce_function():
    cached = cached_function("touhou_local_beam_reduce_v1")
    if cached is not None:
        return cached
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
    return cache_function("touhou_local_beam_reduce_v1", function)


def _load_local_supplemental_beam_reduce_function():
    cached = cached_function("touhou_local_supplemental_beam_reduce_v1")
    if cached is not None:
        return cached
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
    return cache_function(
        "touhou_local_supplemental_beam_reduce_v1",
        function,
    )


def _load_local_supplemental_workspace_functions():
    key = "local_supplemental_workspace_v1"
    cached = cached_function_group(key)
    if cached is not None:
        return cached
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
    return cache_function_group(key, (
        create,
        query,
        cancel,
        active,
        destroy,
    ))




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
        as_contiguous_array(draft_x, dtype=np.float64),
        as_contiguous_array(draft_y, dtype=np.float64),
        as_contiguous_array(first_action, dtype=np.int32),
        as_contiguous_array(last_direction, dtype=np.int32),
        as_contiguous_array(last_focused, dtype=np.uint8),
        as_contiguous_array(collected_mask, dtype=np.uint32),
        as_contiguous_array(risk, dtype=np.float64),
        as_contiguous_array(collisions, dtype=np.int32),
        as_contiguous_array(minimum_clearance, dtype=np.float64),
    )
    draft_count = len(draft_fields[0])
    if (
        draft_count <= 0
        or any(values.ndim != 1 or len(values) != draft_count for values in draft_fields)
    ):
        raise ValueError("local beam draft fields must be nonempty 1D peers")
    action_fields = (
        as_contiguous_array(certificate_collisions, dtype=np.int32),
        as_contiguous_array(certificate_minimum, dtype=np.float64),
        as_contiguous_array(survival_preferred, dtype=np.uint8),
        as_contiguous_array(safety_preferred, dtype=np.uint8),
        as_contiguous_array(recovery_distance, dtype=np.float64),
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
        as_contiguous_array(draft_x, dtype=np.float64),
        as_contiguous_array(draft_y, dtype=np.float64),
        as_contiguous_array(first_action, dtype=np.int32),
        as_contiguous_array(last_direction, dtype=np.int32),
        as_contiguous_array(last_focused, dtype=np.uint8),
        as_contiguous_array(collected_mask, dtype=np.uint32),
        as_contiguous_array(risk, dtype=np.float64),
        as_contiguous_array(collisions, dtype=np.int32),
        as_contiguous_array(minimum_clearance, dtype=np.float64),
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
        as_contiguous_array(certificate_collisions, dtype=np.int32),
        as_contiguous_array(certificate_minimum, dtype=np.float64),
        as_contiguous_array(survival_preferred, dtype=np.uint8),
        as_contiguous_array(safety_preferred, dtype=np.uint8),
        as_contiguous_array(recovery_distance, dtype=np.float64),
        as_contiguous_array(repair_volume, dtype=np.int32),
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
            as_contiguous_array(values, dtype=dtypes[field])
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
            as_contiguous_array(action_direction, dtype=np.int32),
            as_contiguous_array(action_dx, dtype=np.float64),
            as_contiguous_array(action_dy, dtype=np.float64),
            as_contiguous_array(action_focused, dtype=np.uint8),
            as_contiguous_array(action_allowed, dtype=np.uint8),
            as_contiguous_array(
                certificate_collisions,
                dtype=np.int32,
            ),
            as_contiguous_array(certificate_minimum, dtype=np.float64),
            as_contiguous_array(survival_preferred, dtype=np.uint8),
            as_contiguous_array(safety_preferred, dtype=np.uint8),
            as_contiguous_array(recovery_distance, dtype=np.float64),
            as_contiguous_array(repair_volume, dtype=np.int32),
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
            as_contiguous_array(values, dtype=np.float32)
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
