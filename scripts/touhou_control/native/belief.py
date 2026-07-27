"""Native recursive belief-pipeline workspace bindings."""

from __future__ import annotations

import ctypes

import numpy as np

from .arrays import as_contiguous_array
from .library import (
    cache_function_group,
    cached_function_group,
    load_library as _load_library,
    raise_pipeline_result as _raise_pipeline_result,
)


def _load_belief_pipeline_workspace_functions():
    key = "belief_pipeline_workspace_v6"
    cached = cached_function_group(key)
    if cached is not None:
        return cached
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
    return cache_function_group(
        key,
        (create, query, certify, recommend, cancel, destroy),
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
        self._x_axis = as_contiguous_array(x_axis, dtype=np.float32)
        self._y_axis = as_contiguous_array(y_axis, dtype=np.float32)
        self._clearance = as_contiguous_array(
            clearance_volume,
            dtype=np.float32,
        )
        self._velocity_x = as_contiguous_array(
            velocity_x,
            dtype=np.float64,
        )
        self._velocity_y = as_contiguous_array(
            velocity_y,
            dtype=np.float64,
        )
        self._delays = as_contiguous_array(
            delay_frames,
            dtype=np.int32,
        )
        self._decision_frames = as_contiguous_array(
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
        pending = as_contiguous_array(
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
        pending = as_contiguous_array(
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
        pending = as_contiguous_array(
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
