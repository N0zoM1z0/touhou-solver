"""Native data plane for trace-only TH08 derived-pattern sources."""

from __future__ import annotations

import ctypes
import time
from dataclasses import dataclass
from typing import Any

import numpy as np

from .bullet_birth import BULLET_TIMER_CURRENT_OFFSET
from .bullet_birth_native import (
    NATIVE_CALL_MODES,
    NATIVE_CALL_MODE_GIL_RELEASED,
    native_bullet_birth_library_path,
)
from .bullet_decode import (
    BULLET_ORIGINAL_TRANSFORM_FLAGS_OFFSET,
    BULLET_POSITION_OFFSET,
    BULLET_STATE_OFFSET,
    BULLET_STRIDE,
    BULLET_TRANSFORM_FLAGS_OFFSET,
    BULLET_TRANSFORM_PROGRAM_OFFSET,
    BULLET_TRANSFORM_QUEUE_CURSOR_OFFSET,
)
from .derived_pattern_source import (
    TRANSFORM_PROGRAM_LENGTH,
    TRANSFORM_RECORD_SIZE,
    DerivedPatternSourceEvidence,
    DerivedPatternSourceObservation,
)
from .sensor import BULLET_POOL_SIZE


_LIBRARIES: dict[str, Any] = {}
_FUNCTIONS: dict[str, Any] = {}
_LOAD_ERRORS: dict[str, OSError | AttributeError] = {}


@dataclass(frozen=True)
class NativeDerivedPatternSourceDiagnostics:
    prepare_ms: float
    native_call_ms: float
    materialize_ms: float

    def record(self, *, observation_ms: float) -> dict[str, object]:
        segments = {
            "prepare": self.prepare_ms,
            "native_call": self.native_call_ms,
            "materialize": self.materialize_ms,
            "controller_residual": max(
                0.0,
                observation_ms
                - self.prepare_ms
                - self.native_call_ms
                - self.materialize_ms,
            ),
        }
        return {
            "native_segments_ms": segments,
        }


def _load_function(
    call_mode: str = NATIVE_CALL_MODE_GIL_RELEASED,
):
    if call_mode not in NATIVE_CALL_MODES:
        raise ValueError(
            f"unknown native derived-source call mode {call_mode!r}"
        )
    function = _FUNCTIONS.get(call_mode)
    if function is not None:
        return function
    if call_mode in _LOAD_ERRORS:
        return None
    loader = (
        ctypes.CDLL
        if call_mode == NATIVE_CALL_MODE_GIL_RELEASED
        else ctypes.PyDLL
    )
    try:
        library = loader(str(native_bullet_birth_library_path()))
        function = library.touhou_trace_derived_pattern_sources_v1
    except (OSError, AttributeError) as error:
        _LOAD_ERRORS[call_mode] = error
        return None
    uint8_pointer = ctypes.POINTER(ctypes.c_uint8)
    uint16_pointer = ctypes.POINTER(ctypes.c_uint16)
    uint32_pointer = ctypes.POINTER(ctypes.c_uint32)
    int32_pointer = ctypes.POINTER(ctypes.c_int32)
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
        int32_pointer,
        uint16_pointer,
        int32_pointer,
        ctypes.POINTER(ctypes.c_float),
        uint32_pointer,
        uint32_pointer,
        int32_pointer,
        uint32_pointer,
        uint8_pointer,
        ctypes.c_int,
        int32_pointer,
        int32_pointer,
    ]
    function.restype = ctypes.c_int
    _LIBRARIES[call_mode] = library
    _FUNCTIONS[call_mode] = function
    return function


def native_derived_pattern_source_available(
    call_mode: str = NATIVE_CALL_MODE_GIL_RELEASED,
) -> bool:
    return _load_function(call_mode) is not None


class NativeDerivedPatternSourceObserver:
    """Reusable bounded native source scanner with candidate-only materialization."""

    def __init__(
        self,
        *,
        native_call_mode: str = NATIVE_CALL_MODE_GIL_RELEASED,
    ) -> None:
        function = _load_function(native_call_mode)
        if function is None:
            error = _LOAD_ERRORS.get(native_call_mode)
            detail = f": {error}" if error is not None else ""
            raise RuntimeError(
                "native derived-pattern source scanner is unavailable"
                + detail
            )
        self.native_call_mode = native_call_mode
        self._function = function
        self._slots = np.empty(BULLET_POOL_SIZE, dtype=np.int32)
        self._states = np.empty(BULLET_POOL_SIZE, dtype=np.uint16)
        self._ages = np.empty(BULLET_POOL_SIZE, dtype=np.int32)
        self._positions = np.empty(
            (BULLET_POOL_SIZE, 2),
            dtype=np.float32,
        )
        self._transform_flags = np.empty(BULLET_POOL_SIZE, dtype=np.uint32)
        self._original_flags = np.empty(BULLET_POOL_SIZE, dtype=np.uint32)
        self._cursors = np.empty(BULLET_POOL_SIZE, dtype=np.int32)
        self._record_words = np.empty(
            (BULLET_POOL_SIZE, 12),
            dtype=np.uint32,
        )
        self._finite = np.empty(BULLET_POOL_SIZE, dtype=np.uint8)
        self._active_count = ctypes.c_int32()
        self._count = ctypes.c_int32()
        self._raw_owner: bytes | bytearray | memoryview | None = None
        self._raw_view: np.ndarray | None = None
        self._raw_pointer: Any | None = None
        self._last_diagnostics: NativeDerivedPatternSourceDiagnostics | None = (
            None
        )
        uint8_pointer = ctypes.POINTER(ctypes.c_uint8)
        uint16_pointer = ctypes.POINTER(ctypes.c_uint16)
        uint32_pointer = ctypes.POINTER(ctypes.c_uint32)
        int32_pointer = ctypes.POINTER(ctypes.c_int32)
        self._slots_pointer = self._slots.ctypes.data_as(int32_pointer)
        self._states_pointer = self._states.ctypes.data_as(uint16_pointer)
        self._ages_pointer = self._ages.ctypes.data_as(int32_pointer)
        self._positions_pointer = self._positions.ctypes.data_as(
            ctypes.POINTER(ctypes.c_float)
        )
        self._transform_flags_pointer = self._transform_flags.ctypes.data_as(
            uint32_pointer
        )
        self._original_flags_pointer = self._original_flags.ctypes.data_as(
            uint32_pointer
        )
        self._cursors_pointer = self._cursors.ctypes.data_as(int32_pointer)
        self._record_words_pointer = self._record_words.ctypes.data_as(
            uint32_pointer
        )
        self._finite_pointer = self._finite.ctypes.data_as(uint8_pointer)
        self._active_count_pointer = ctypes.pointer(self._active_count)
        self._count_pointer = ctypes.pointer(self._count)

    def diagnostics(self) -> NativeDerivedPatternSourceDiagnostics:
        if self._last_diagnostics is None:
            raise RuntimeError("derived-source diagnostics are unavailable")
        return self._last_diagnostics

    def _raw_pointer_for(
        self,
        blob: bytes | bytearray | memoryview,
        *,
        required_size: int,
    ):
        if blob is not self._raw_owner:
            self._raw_owner = blob
            self._raw_view = np.frombuffer(
                blob,
                dtype=np.uint8,
                count=required_size,
            )
            self._raw_pointer = self._raw_view.ctypes.data_as(
                ctypes.POINTER(ctypes.c_uint8)
            )
        assert self._raw_pointer is not None
        return self._raw_pointer

    def observe(
        self,
        blob: bytes | bytearray | memoryview,
        *,
        frame_before: int,
        frame_after: int,
    ) -> DerivedPatternSourceObservation:
        prepare_started = time.perf_counter()
        required_size = BULLET_POOL_SIZE * BULLET_STRIDE
        if len(blob) < required_size:
            raise ValueError(f"bullet pool requires {required_size} bytes")
        if (
            type(frame_before) is not int
            or type(frame_after) is not int
            or frame_before < 0
            or frame_after < frame_before
        ):
            raise ValueError("invalid bullet capture frame interval")
        raw_pointer = self._raw_pointer_for(
            blob,
            required_size=required_size,
        )
        native_started = time.perf_counter()
        prepare_ms = (native_started - prepare_started) * 1000.0
        result = int(
            self._function(
                raw_pointer,
                required_size,
                BULLET_POOL_SIZE,
                BULLET_STRIDE,
                BULLET_STATE_OFFSET,
                BULLET_TIMER_CURRENT_OFFSET,
                BULLET_POSITION_OFFSET,
                BULLET_TRANSFORM_FLAGS_OFFSET,
                BULLET_ORIGINAL_TRANSFORM_FLAGS_OFFSET,
                BULLET_TRANSFORM_QUEUE_CURSOR_OFFSET,
                BULLET_TRANSFORM_PROGRAM_OFFSET,
                TRANSFORM_PROGRAM_LENGTH,
                TRANSFORM_RECORD_SIZE,
                self._slots_pointer,
                self._states_pointer,
                self._ages_pointer,
                self._positions_pointer,
                self._transform_flags_pointer,
                self._original_flags_pointer,
                self._cursors_pointer,
                self._record_words_pointer,
                self._finite_pointer,
                BULLET_POOL_SIZE,
                self._active_count_pointer,
                self._count_pointer,
            )
        )
        materialize_started = time.perf_counter()
        native_ms = (materialize_started - native_started) * 1000.0
        if result != 0:
            raise RuntimeError(
                f"native derived-pattern source scanner returned {result}"
            )
        count = int(self._count.value)
        active_count = int(self._active_count.value)
        if (
            not 0 <= count <= BULLET_POOL_SIZE
            or not 0 <= active_count <= BULLET_POOL_SIZE
        ):
            raise RuntimeError(
                "native derived-pattern source scanner returned invalid count"
            )
        candidates = tuple(
            DerivedPatternSourceEvidence(
                slot=int(self._slots[index]),
                state=int(self._states[index]),
                age=int(self._ages[index]),
                x=float(self._positions[index, 0]),
                y=float(self._positions[index, 1]),
                transform_flags=int(self._transform_flags[index]),
                original_transform_flags=int(self._original_flags[index]),
                queue_cursor=int(self._cursors[index]),
                first_words=tuple(
                    int(value) for value in self._record_words[index, :6]
                ),
                second_words=tuple(
                    int(value) for value in self._record_words[index, 6:]
                ),
                geometry_finite=bool(self._finite[index]),
            )
            for index in range(count)
        )
        observation = DerivedPatternSourceObservation(
            frame_before=frame_before,
            frame_after=frame_after,
            active_count=active_count,
            candidates=candidates,
        )
        materialize_ms = (
            time.perf_counter() - materialize_started
        ) * 1000.0
        self._last_diagnostics = NativeDerivedPatternSourceDiagnostics(
            prepare_ms=prepare_ms,
            native_call_ms=native_ms,
            materialize_ms=materialize_ms,
        )
        return observation


__all__ = [
    "NativeDerivedPatternSourceDiagnostics",
    "NativeDerivedPatternSourceObserver",
    "native_derived_pattern_source_available",
]
