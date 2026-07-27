"""Trace-only native TH08 hostile-bullet birth extraction."""

from __future__ import annotations

import ctypes
import gc
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from th08_live.bullet_birth import (
    BULLET_TIMER_CURRENT_OFFSET,
    BulletBirthEvidenceBatch,
    BulletBirthObservation,
)
from th08_live.bullet_decode import (
    BULLET_GEOMETRY_OFFSET,
    BULLET_POOL_SIZE,
    BULLET_POSITION_OFFSET,
    BULLET_STATE_OFFSET,
    BULLET_STRIDE,
    BULLET_TRANSFORM_FLAGS_OFFSET,
    BULLET_VELOCITY_OFFSET,
)


ROOT = Path(__file__).resolve().parents[2]
_LIBRARY: Any | None = None
_LOAD_ERROR: OSError | None = None
_FUNCTION: Any | None = None
_ACTIVE_GC_TRACKER: Any | None = None
_GC_CALLBACK_REGISTERED = False

_GC_PHASE_INACTIVE = -1
_GC_PHASE_PREPARE = 0
_GC_PHASE_NATIVE_CALL = 1
_GC_PHASE_MATERIALIZE = 2
_GC_PHASE_NAMES = ("prepare", "native_call", "materialize")


def _gc_collection_callback(
    phase: str,
    information: dict[str, Any],
) -> None:
    if phase != "stop":
        return
    tracker = _ACTIVE_GC_TRACKER
    if tracker is None:
        return
    generation = information.get("generation")
    if type(generation) is not int or not 0 <= generation <= 2:
        return
    tracker._record_completed_gc(generation)


def _ensure_gc_callback_registered() -> None:
    global _GC_CALLBACK_REGISTERED
    if _GC_CALLBACK_REGISTERED:
        return
    gc.callbacks.append(_gc_collection_callback)
    _GC_CALLBACK_REGISTERED = True


@dataclass(frozen=True)
class NativeBulletBirthDiagnostics:
    """Retrospective native-observer phase and GC-overlap telemetry."""

    prepare_ms: float
    native_call_ms: float
    materialize_ms: float
    gc_completed: tuple[
        tuple[int, int, int],
        tuple[int, int, int],
        tuple[int, int, int],
    ]

    def record(self, *, observation_ms: float) -> dict[str, object]:
        controller_residual_ms = observation_ms - (
            self.prepare_ms
            + self.native_call_ms
            + self.materialize_ms
        )
        return {
            "native_segments_ms": {
                "prepare": self.prepare_ms,
                "native_call": self.native_call_ms,
                "materialize": self.materialize_ms,
                "controller_residual": controller_residual_ms,
            },
            "gc_completed": {
                phase: list(counts)
                for phase, counts in zip(
                    _GC_PHASE_NAMES,
                    self.gc_completed,
                )
            },
        }


def native_bullet_birth_library_path() -> Path:
    if os.name == "nt":
        return (
            ROOT
            / "native"
            / "build"
            / "windows-x86_64"
            / "touhou_bullet_birth_trace.dll"
        )
    return (
        ROOT
        / "native"
        / "build"
        / "linux-x86_64"
        / "libtouhou_bullet_birth_trace.so"
    )


def _load_function():
    global _FUNCTION, _LIBRARY, _LOAD_ERROR
    if _FUNCTION is not None:
        return _FUNCTION
    if _LOAD_ERROR is not None:
        return None
    try:
        _LIBRARY = ctypes.CDLL(str(native_bullet_birth_library_path()))
    except OSError as error:
        _LOAD_ERROR = error
        return None
    try:
        function = _LIBRARY.touhou_trace_bullet_births_v1
    except AttributeError:
        return None
    uint8_pointer = ctypes.POINTER(ctypes.c_uint8)
    uint16_pointer = ctypes.POINTER(ctypes.c_uint16)
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
        uint16_pointer,
        int32_pointer,
        int32_pointer,
        uint8_pointer,
        uint16_pointer,
        int32_pointer,
        uint16_pointer,
        int32_pointer,
        ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_uint32),
        uint8_pointer,
        ctypes.c_int,
        int32_pointer,
        int32_pointer,
    ]
    function.restype = ctypes.c_int
    _FUNCTION = function
    return function


def native_bullet_birth_available() -> bool:
    return _load_function() is not None


class NativeBulletBirthTracker:
    """Exact native data plane behind the Python observation contract."""

    def __init__(self, *, maximum_bootstrap_age: int = 8) -> None:
        if type(maximum_bootstrap_age) is not int or maximum_bootstrap_age < 0:
            raise ValueError("maximum bootstrap age must be a non-negative int")
        if _load_function() is None:
            detail = f": {_LOAD_ERROR}" if _LOAD_ERROR is not None else ""
            raise RuntimeError(
                "native bullet-birth trace library is unavailable" + detail
            )
        _ensure_gc_callback_registered()
        self._maximum_bootstrap_age = maximum_bootstrap_age
        self._previous_states = np.empty(BULLET_POOL_SIZE, dtype=np.uint16)
        self._previous_ages = np.empty(BULLET_POOL_SIZE, dtype=np.int32)
        self._slots = np.empty(BULLET_POOL_SIZE, dtype=np.int32)
        self._codes = np.empty(BULLET_POOL_SIZE, dtype=np.uint8)
        self._states = np.empty(BULLET_POOL_SIZE, dtype=np.uint16)
        self._ages = np.empty(BULLET_POOL_SIZE, dtype=np.int32)
        self._evidence_previous_states = np.empty(
            BULLET_POOL_SIZE,
            dtype=np.uint16,
        )
        self._evidence_previous_ages = np.empty(
            BULLET_POOL_SIZE,
            dtype=np.int32,
        )
        self._geometry = np.empty(
            (BULLET_POOL_SIZE, 6),
            dtype=np.float32,
        )
        self._transform_flags = np.empty(
            BULLET_POOL_SIZE,
            dtype=np.uint32,
        )
        self._geometry_finite = np.empty(
            BULLET_POOL_SIZE,
            dtype=np.uint8,
        )
        uint8_pointer = ctypes.POINTER(ctypes.c_uint8)
        uint16_pointer = ctypes.POINTER(ctypes.c_uint16)
        int32_pointer = ctypes.POINTER(ctypes.c_int32)
        self._previous_states_pointer = (
            self._previous_states.ctypes.data_as(uint16_pointer)
        )
        self._previous_ages_pointer = self._previous_ages.ctypes.data_as(
            int32_pointer
        )
        self._slots_pointer = self._slots.ctypes.data_as(int32_pointer)
        self._codes_pointer = self._codes.ctypes.data_as(uint8_pointer)
        self._states_pointer = self._states.ctypes.data_as(uint16_pointer)
        self._ages_pointer = self._ages.ctypes.data_as(int32_pointer)
        self._evidence_previous_states_pointer = (
            self._evidence_previous_states.ctypes.data_as(uint16_pointer)
        )
        self._evidence_previous_ages_pointer = (
            self._evidence_previous_ages.ctypes.data_as(int32_pointer)
        )
        self._geometry_pointer = self._geometry.ctypes.data_as(
            ctypes.POINTER(ctypes.c_float)
        )
        self._transform_flags_pointer = (
            self._transform_flags.ctypes.data_as(
                ctypes.POINTER(ctypes.c_uint32)
            )
        )
        self._geometry_finite_pointer = (
            self._geometry_finite.ctypes.data_as(uint8_pointer)
        )
        self._active_count = ctypes.c_int32()
        self._evidence_count = ctypes.c_int32()
        self._active_count_pointer = ctypes.pointer(self._active_count)
        self._evidence_count_pointer = ctypes.pointer(
            self._evidence_count
        )
        self._raw_owner: bytes | bytearray | memoryview | None = None
        self._raw_view: np.ndarray | None = None
        self._raw_pointer: Any | None = None
        self._has_previous = False
        self._previous_frame_before: int | None = None
        self._previous_frame_after: int | None = None
        self._gc_phase = _GC_PHASE_INACTIVE
        self._gc_completed = [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]
        self._last_prepare_ms: float | None = None
        self._last_native_call_ms: float | None = None
        self._last_materialize_ms: float | None = None

    def reset(self) -> None:
        self._has_previous = False
        self._previous_frame_before = None
        self._previous_frame_after = None
        self._last_prepare_ms = None
        self._last_native_call_ms = None
        self._last_materialize_ms = None

    def _record_completed_gc(self, generation: int) -> None:
        phase = self._gc_phase
        if 0 <= phase < len(self._gc_completed):
            self._gc_completed[phase][generation] += 1

    def diagnostics(self) -> NativeBulletBirthDiagnostics:
        if (
            self._last_prepare_ms is None
            or self._last_native_call_ms is None
            or self._last_materialize_ms is None
        ):
            raise RuntimeError(
                "native bullet-birth diagnostics are unavailable"
            )
        return NativeBulletBirthDiagnostics(
            prepare_ms=self._last_prepare_ms,
            native_call_ms=self._last_native_call_ms,
            materialize_ms=self._last_materialize_ms,
            gc_completed=tuple(
                tuple(counts) for counts in self._gc_completed
            ),
        )

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

    def _invoke(
        self,
        raw_pointer,
        *,
        required_size: int,
        output_capacity: int,
    ) -> int:
        function = _load_function()
        if function is None:
            raise RuntimeError("native bullet-birth trace library disappeared")
        return int(
            function(
                raw_pointer,
                required_size,
                BULLET_POOL_SIZE,
                BULLET_STRIDE,
                BULLET_STATE_OFFSET,
                BULLET_TIMER_CURRENT_OFFSET,
                BULLET_POSITION_OFFSET,
                BULLET_VELOCITY_OFFSET,
                BULLET_GEOMETRY_OFFSET,
                BULLET_TRANSFORM_FLAGS_OFFSET,
                int(self._has_previous),
                self._maximum_bootstrap_age,
                self._previous_states_pointer,
                self._previous_ages_pointer,
                self._slots_pointer,
                self._codes_pointer,
                self._states_pointer,
                self._ages_pointer,
                self._evidence_previous_states_pointer,
                self._evidence_previous_ages_pointer,
                self._geometry_pointer,
                self._transform_flags_pointer,
                self._geometry_finite_pointer,
                output_capacity,
                self._active_count_pointer,
                self._evidence_count_pointer,
            )
        )

    def observe(
        self,
        blob: bytes | bytearray | memoryview,
        *,
        frame_before: int,
        frame_after: int,
    ) -> BulletBirthObservation:
        global _ACTIVE_GC_TRACKER
        if _ACTIVE_GC_TRACKER is not None:
            raise RuntimeError(
                "native bullet-birth observations may not overlap"
            )
        self._last_prepare_ms = None
        self._last_native_call_ms = None
        self._last_materialize_ms = None
        for phase_counts in self._gc_completed:
            phase_counts[:] = (0, 0, 0)
        _ACTIVE_GC_TRACKER = self
        self._gc_phase = _GC_PHASE_PREPARE
        prepare_started = time.perf_counter()
        try:
            required_size = BULLET_POOL_SIZE * BULLET_STRIDE
            if len(blob) < required_size:
                raise ValueError(
                    f"bullet pool requires {required_size} bytes"
                )
            if (
                type(frame_before) is not int
                or type(frame_after) is not int
                or frame_before < 0
                or frame_after < frame_before
            ):
                raise ValueError("invalid bullet capture frame interval")
            if (
                self._previous_frame_before is not None
                and frame_before < self._previous_frame_before
            ):
                raise ValueError("bullet capture frame regressed")

            raw_pointer = self._raw_pointer_for(
                blob,
                required_size=required_size,
            )
            native_call_started = time.perf_counter()
            self._last_prepare_ms = (
                native_call_started - prepare_started
            ) * 1000.0
            self._gc_phase = _GC_PHASE_NATIVE_CALL
            result = self._invoke(
                raw_pointer,
                required_size=required_size,
                output_capacity=BULLET_POOL_SIZE,
            )
            materialize_started = time.perf_counter()
            self._last_native_call_ms = (
                materialize_started - native_call_started
            ) * 1000.0
            self._gc_phase = _GC_PHASE_MATERIALIZE
            if result != 0:
                raise RuntimeError(
                    f"native bullet-birth extractor returned {result}"
                )
            count = int(self._evidence_count.value)
            active = int(self._active_count.value)
            if (
                count < 0
                or count > BULLET_POOL_SIZE
                or active < 0
                or active > BULLET_POOL_SIZE
            ):
                self.reset()
                raise RuntimeError(
                    "native bullet-birth extractor returned invalid counts"
                )

            def prefix_copy(values: np.ndarray) -> np.ndarray:
                return values[:count].copy()

            evidence: tuple[()] | BulletBirthEvidenceBatch = ()
            if count:
                evidence = BulletBirthEvidenceBatch(
                    slots=prefix_copy(self._slots),
                    codes=prefix_copy(self._codes),
                    states=prefix_copy(self._states),
                    ages=prefix_copy(self._ages),
                    previous_states=(
                        prefix_copy(self._evidence_previous_states)
                        if self._has_previous
                        else None
                    ),
                    previous_ages=(
                        prefix_copy(self._evidence_previous_ages)
                        if self._has_previous
                        else None
                    ),
                    support_start=self._previous_frame_before,
                    support_end=frame_after,
                    geometry=prefix_copy(self._geometry),
                    transform_flags=prefix_copy(self._transform_flags),
                    geometry_finite=prefix_copy(
                        self._geometry_finite
                    ).astype(np.bool_),
                )
            observation = BulletBirthObservation(
                frame_before=frame_before,
                frame_after=frame_after,
                previous_frame_before=self._previous_frame_before,
                previous_frame_after=self._previous_frame_after,
                active_count=active,
                evidence=evidence,
            )
            self._has_previous = True
            self._previous_frame_before = frame_before
            self._previous_frame_after = frame_after
            self._last_materialize_ms = (
                time.perf_counter() - materialize_started
            ) * 1000.0
            return observation
        finally:
            self._gc_phase = _GC_PHASE_INACTIVE
            _ACTIVE_GC_TRACKER = None


__all__ = [
    "NativeBulletBirthDiagnostics",
    "NativeBulletBirthTracker",
    "native_bullet_birth_available",
    "native_bullet_birth_library_path",
]
