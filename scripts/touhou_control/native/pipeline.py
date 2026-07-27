"""Native exact pipeline-survival workspace bindings."""

from __future__ import annotations

import ctypes

import numpy as np

from .library import (
    PipelineNativeCancelledError as PipelineNativeCancelledError,
    PipelineNativeDeadlineError as PipelineNativeDeadlineError,
    load_library as _load_library,
    raise_pipeline_result as _raise_pipeline_result,
)


_PIPELINE_WORKSPACE_CREATE_FUNCTION = None
_PIPELINE_WORKSPACE_QUERY_FUNCTION = None
_PIPELINE_WORKSPACE_CONTAINS_FUNCTION = None
_PIPELINE_WORKSPACE_PREWARM_FUNCTION = None
_PIPELINE_WORKSPACE_MERGE_FUNCTION = None
_PIPELINE_WORKSPACE_CANCEL_FUNCTION = None
_PIPELINE_WORKSPACE_DESTROY_FUNCTION = None


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
