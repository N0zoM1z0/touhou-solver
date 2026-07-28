"""ctypes boundary for the trace-only native auxiliary-VM batch."""

from __future__ import annotations

import ctypes
from dataclasses import dataclass
import time
from typing import Any

from th08_live.bullet_birth_native import (
    NATIVE_CALL_MODE_GIL_HELD,
    NATIVE_CALL_MODE_GIL_RELEASED,
    NATIVE_CALL_MODES,
    native_bullet_birth_library_path,
)

from .model import (
    ACTIVE_VM_BYTES,
    AuxiliaryVmBatchObservation,
    AuxiliaryVmBatchRecord,
    BatchStatus,
    MAXIMUM_RECORDS,
    MAXIMUM_RESTORABLE_FRAMES,
    MAXIMUM_STATE_PAYLOAD_BYTES,
    RecordStatus,
    SAVED_FRAME_BYTES,
)


class NativeAuxiliaryVmBatchError(RuntimeError):
    """The native ABI rejected a call or returned malformed metadata."""


@dataclass(frozen=True, slots=True)
class NativeAuxiliaryVmBatchDiagnostics:
    native_call_ms: float
    materialize_ms: float


class _NativeRecordV1(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("slot", ctypes.c_int32),
        ("auxiliary_index", ctypes.c_uint8),
        ("reserved0", ctypes.c_uint8 * 3),
        ("enemy_pointer", ctypes.c_uint32),
        ("context_pointer", ctypes.c_uint32),
        ("context_pointer_after", ctypes.c_uint32),
        ("enemy_flags_before", ctypes.c_uint32),
        ("enemy_flags_after", ctypes.c_uint32),
        ("status_bits", ctypes.c_uint32),
        ("target_subroutine", ctypes.c_uint32),
        ("call_depth", ctypes.c_int16),
        ("reserved1", ctypes.c_uint16),
        ("auxiliary_marker", ctypes.c_uint32),
        ("payload_offset", ctypes.c_uint32),
        ("payload_size", ctypes.c_uint32),
    ]


class _NativeBatchV1(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("status_bits", ctypes.c_uint32),
        ("expected_manager_frame", ctypes.c_int32),
        ("manager_frame_before", ctypes.c_int32),
        ("manager_frame_after", ctypes.c_int32),
        ("process_read_count", ctypes.c_uint32),
        ("active_owner_count", ctypes.c_uint32),
        ("record_count", ctypes.c_uint32),
        ("non_null_context_count", ctypes.c_uint32),
        ("usable_context_count", ctypes.c_uint32),
        ("state_payload_bytes", ctypes.c_uint64),
    ]


if ctypes.sizeof(_NativeRecordV1) != 52:
    raise AssertionError("unexpected native auxiliary record ABI")
if ctypes.sizeof(_NativeBatchV1) != 44:
    raise AssertionError("unexpected native auxiliary batch ABI")


_LIBRARIES: dict[str, Any] = {}
_FUNCTIONS: dict[tuple[str, str], Any] = {}
_LOAD_ERRORS: dict[str, OSError | AttributeError] = {}
_UINT8_POINTER = ctypes.POINTER(ctypes.c_uint8)


def _load_functions(call_mode: str) -> tuple[Any, Any] | None:
    if call_mode not in NATIVE_CALL_MODES:
        raise ValueError(f"unknown native auxiliary-VM call mode {call_mode!r}")
    fixture = _FUNCTIONS.get((call_mode, "fixture"))
    process = _FUNCTIONS.get((call_mode, "process"))
    if fixture is not None and process is not None:
        return fixture, process
    if call_mode in _LOAD_ERRORS:
        return None
    loader = (
        ctypes.CDLL
        if call_mode == NATIVE_CALL_MODE_GIL_RELEASED
        else ctypes.PyDLL
    )
    try:
        library = loader(str(native_bullet_birth_library_path()))
        fixture = library.touhou_trace_auxiliary_vm_batch_fixture_v1
        process = library.touhou_trace_auxiliary_vm_batch_process_v1
    except (OSError, AttributeError) as error:
        _LOAD_ERRORS[call_mode] = error
        return None

    fixture.argtypes = [
        _UINT8_POINTER,
        ctypes.c_uint64,
        _UINT8_POINTER,
        ctypes.c_uint64,
        _UINT8_POINTER,
        ctypes.c_uint64,
        _UINT8_POINTER,
        ctypes.c_uint64,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_uint32,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.POINTER(_NativeRecordV1),
        ctypes.c_int,
        _UINT8_POINTER,
        ctypes.c_uint64,
        ctypes.POINTER(_NativeBatchV1),
    ]
    fixture.restype = ctypes.c_int
    process.argtypes = [
        ctypes.c_uint64,
        _UINT8_POINTER,
        ctypes.c_uint64,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_uint32,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.POINTER(_NativeRecordV1),
        ctypes.c_int,
        _UINT8_POINTER,
        ctypes.c_uint64,
        ctypes.POINTER(_NativeBatchV1),
    ]
    process.restype = ctypes.c_int
    _LIBRARIES[call_mode] = library
    _FUNCTIONS[(call_mode, "fixture")] = fixture
    _FUNCTIONS[(call_mode, "process")] = process
    return fixture, process


def native_auxiliary_vm_batch_available(
    call_mode: str = NATIVE_CALL_MODE_GIL_HELD,
) -> bool:
    return _load_functions(call_mode) is not None


def _bytes_pointer(blob: bytes) -> tuple[Any, Any]:
    owner = ctypes.c_char_p(blob)
    return owner, ctypes.cast(owner, _UINT8_POINTER)


def _process_handle_value(reader: Any) -> int:
    handle = reader.handle
    if isinstance(handle, int):
        return handle
    value = getattr(handle, "value", None)
    if value is None:
        value = ctypes.cast(handle, ctypes.c_void_p).value
    if value is None:
        raise NativeAuxiliaryVmBatchError("process handle is null")
    return int(value)


class NativeAuxiliaryVmBatchCapture:
    """Reusable caller-owned metadata and payload buffers."""

    def __init__(
        self,
        *,
        call_mode: str = NATIVE_CALL_MODE_GIL_HELD,
    ) -> None:
        functions = _load_functions(call_mode)
        if functions is None:
            error = _LOAD_ERRORS.get(call_mode)
            raise NativeAuxiliaryVmBatchError(
                f"native auxiliary-VM batch unavailable: {error}"
            )
        self.call_mode = call_mode
        self._fixture_function, self._process_function = functions
        self._records = (_NativeRecordV1 * MAXIMUM_RECORDS)()
        self._payload = (ctypes.c_uint8 * MAXIMUM_STATE_PAYLOAD_BYTES)()
        self._batch = _NativeBatchV1()
        self._diagnostics = NativeAuxiliaryVmBatchDiagnostics(0.0, 0.0)

    def diagnostics(self) -> NativeAuxiliaryVmBatchDiagnostics:
        return self._diagnostics

    def _finish_call(
        self,
        *,
        result: int,
        native_started: float,
        operation: str,
    ) -> AuxiliaryVmBatchObservation:
        native_finished = time.perf_counter()
        if result != 0:
            raise NativeAuxiliaryVmBatchError(
                f"native {operation} batch rejected arguments ({result})"
            )
        observation = self._materialize()
        materialize_finished = time.perf_counter()
        self._diagnostics = NativeAuxiliaryVmBatchDiagnostics(
            native_call_ms=(native_finished - native_started) * 1000.0,
            materialize_ms=(
                materialize_finished - native_finished
            )
            * 1000.0,
        )
        return observation

    def _materialize(self) -> AuxiliaryVmBatchObservation:
        batch = self._batch
        if batch.record_count > MAXIMUM_RECORDS:
            raise NativeAuxiliaryVmBatchError(
                f"native record count {batch.record_count} exceeds capacity"
            )
        records: list[AuxiliaryVmBatchRecord] = []
        for index in range(batch.record_count):
            raw = self._records[index]
            status = RecordStatus(raw.status_bits)
            target: int | None = raw.target_subroutine
            depth: int | None = raw.call_depth
            marker: int | None = raw.auxiliary_marker
            if status & (
                RecordStatus.NULL
                | RecordStatus.CONTEXT_ADDRESS_INVALID
                | RecordStatus.CONTEXT_PREFIX_READ_FAILED
            ):
                target = None
                depth = None
            if (
                depth is None
                or not 0 <= depth <= MAXIMUM_RESTORABLE_FRAMES
                or status
                & (
                    RecordStatus.CONTEXT_ADDRESS_INVALID
                    | RecordStatus.PAYLOAD_CAPACITY
                    | RecordStatus.PAYLOAD_READ_FAILED
                )
            ):
                marker = None

            active_vm = b""
            saved_frames: tuple[bytes, ...] = ()
            if status == RecordStatus.OK:
                if depth is None:
                    raise NativeAuxiliaryVmBatchError(
                        "usable native row omitted its call depth"
                    )
                expected_size = (1 + depth) * ACTIVE_VM_BYTES
                end = raw.payload_offset + raw.payload_size
                if (
                    raw.payload_size != expected_size
                    or end < raw.payload_offset
                    or end > MAXIMUM_STATE_PAYLOAD_BYTES
                ):
                    raise NativeAuxiliaryVmBatchError(
                        "native payload metadata violated v1 bounds"
                    )
                payload = ctypes.string_at(
                    ctypes.addressof(self._payload) + raw.payload_offset,
                    raw.payload_size,
                )
                active_vm = payload[:ACTIVE_VM_BYTES]
                saved_frames = tuple(
                    payload[
                        ACTIVE_VM_BYTES
                        + frame * SAVED_FRAME_BYTES :
                        ACTIVE_VM_BYTES
                        + (frame + 1) * SAVED_FRAME_BYTES
                    ]
                    for frame in range(depth)
                )
            records.append(
                AuxiliaryVmBatchRecord(
                    slot=raw.slot,
                    auxiliary_index=raw.auxiliary_index,
                    enemy_pointer=raw.enemy_pointer,
                    context_pointer=raw.context_pointer,
                    context_pointer_after=raw.context_pointer_after,
                    enemy_flags_before=raw.enemy_flags_before,
                    enemy_flags_after=raw.enemy_flags_after,
                    status=status,
                    target_subroutine=target,
                    call_depth=depth,
                    auxiliary_marker=marker,
                    active_vm=active_vm,
                    saved_frames=saved_frames,
                )
            )
        observation = AuxiliaryVmBatchObservation(
            expected_manager_frame=batch.expected_manager_frame,
            manager_frame_before=batch.manager_frame_before,
            manager_frame_after=batch.manager_frame_after,
            batch_status=BatchStatus(batch.status_bits),
            records=tuple(records),
            process_read_count=batch.process_read_count,
            state_payload_bytes=batch.state_payload_bytes,
        )
        if batch.active_owner_count != observation.active_owner_count:
            raise NativeAuxiliaryVmBatchError(
                "native active-owner count disagrees with its rows"
            )
        if (
            batch.non_null_context_count
            != observation.non_null_context_count
        ):
            raise NativeAuxiliaryVmBatchError(
                "native non-null count disagrees with its rows"
            )
        if (
            batch.usable_context_count
            != observation.usable_context_count
        ):
            raise NativeAuxiliaryVmBatchError(
                "native usable count disagrees with fail-closed publication"
            )
        return observation

    def decode_fixture(
        self,
        owner_blob_before: bytes,
        owner_blob_after: bytes,
        arena_before: bytes,
        arena_after: bytes,
        *,
        arena_base: int,
        pool_base: int,
        record_count: int,
        enemy_stride: int,
        enemy_flags_offset: int,
        enemy_active_flag: int,
        context_pointer_offset: int,
        expected_manager_frame: int,
        manager_frame_before: int,
        manager_frame_after: int,
        output_payload_capacity: int = MAXIMUM_STATE_PAYLOAD_BYTES,
    ) -> AuxiliaryVmBatchObservation:
        if not 0 <= output_payload_capacity <= MAXIMUM_STATE_PAYLOAD_BYTES:
            raise ValueError("native fixture payload capacity is out of range")
        before_owner, before_pointer = _bytes_pointer(owner_blob_before)
        after_owner, after_pointer = _bytes_pointer(owner_blob_after)
        before_arena, before_arena_pointer = _bytes_pointer(arena_before)
        after_arena, after_arena_pointer = _bytes_pointer(arena_after)
        native_started = time.perf_counter()
        result = self._fixture_function(
            before_pointer,
            len(owner_blob_before),
            after_pointer,
            len(owner_blob_after),
            before_arena_pointer,
            len(arena_before),
            after_arena_pointer,
            len(arena_after),
            arena_base,
            pool_base,
            record_count,
            enemy_stride,
            enemy_flags_offset,
            enemy_active_flag,
            context_pointer_offset,
            expected_manager_frame,
            manager_frame_before,
            manager_frame_after,
            self._records,
            MAXIMUM_RECORDS,
            self._payload,
            output_payload_capacity,
            ctypes.byref(self._batch),
        )
        _ = before_owner, after_owner, before_arena, after_arena
        return self._finish_call(
            result=result,
            native_started=native_started,
            operation="fixture",
        )

    def capture_process(
        self,
        reader: Any,
        owner_blob_before: bytes,
        *,
        pool_base: int,
        manager_frame_address: int,
        record_count: int,
        enemy_stride: int,
        enemy_flags_offset: int,
        enemy_active_flag: int,
        context_pointer_offset: int,
        expected_manager_frame: int,
    ) -> AuxiliaryVmBatchObservation:
        owner, owner_pointer = _bytes_pointer(owner_blob_before)
        native_started = time.perf_counter()
        result = self._process_function(
            _process_handle_value(reader),
            owner_pointer,
            len(owner_blob_before),
            pool_base,
            manager_frame_address,
            record_count,
            enemy_stride,
            enemy_flags_offset,
            enemy_active_flag,
            context_pointer_offset,
            expected_manager_frame,
            self._records,
            MAXIMUM_RECORDS,
            self._payload,
            MAXIMUM_STATE_PAYLOAD_BYTES,
            ctypes.byref(self._batch),
        )
        _ = owner
        return self._finish_call(
            result=result,
            native_started=native_started,
            operation="process",
        )


__all__ = [
    "NATIVE_CALL_MODE_GIL_HELD",
    "NATIVE_CALL_MODE_GIL_RELEASED",
    "NativeAuxiliaryVmBatchCapture",
    "NativeAuxiliaryVmBatchDiagnostics",
    "NativeAuxiliaryVmBatchError",
    "native_auxiliary_vm_batch_available",
]
