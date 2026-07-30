"""Bounded trace-only hook for TH08 priority-17 input publication.

The shipped callback has two possible ``input_current`` stores and five
control-flow paths to one common epilogue. The probe detours that epilogue,
records callback-exit state in a bounded remote ring, and restores the exact
shipped bytes on close. It has no action authority.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass
import struct
import time
from typing import Any

from .game_state import (
    ADDR_CURRENT_INPUT,
    ADDR_ENEMY_MANAGER_FRAME,
    ADDR_ENGINE_FLAGS,
    ADDR_PREVIOUS_INPUT,
    ADDR_RAW_INPUT,
)


PROBE_SCHEMA = "th08-priority17-publication-probe-v1"
PROBE_MAGIC = b"P17R"
PROBE_VERSION = 1
PROBE_CAPACITY = 256
PROBE_EVENT_SIZE = 24
PROBE_ALLOCATION_SIZE = 0x2000
PROBE_STUB_OFFSET = 0x40
PROBE_EVENT_OFFSET = 0x100
PROBE_HEADER_SIZE = 32
PROBE_SERIAL_OFFSET = 16

PRIORITY17_EPILOGUE_ADDRESS = 0x00452480
PRIORITY17_EPILOGUE_ORIGINAL = b"\x8b\xe5"
PRIORITY17_PADDING_ADDRESS = 0x00452484
PRIORITY17_PADDING_ORIGINAL = b"\xcc" * 5

PROCESS_VM_OPERATION = 0x0008
PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020
PROCESS_QUERY_INFORMATION = 0x0400
THREAD_SUSPEND_RESUME = 0x0002
THREAD_GET_CONTEXT = 0x0008
THREAD_QUERY_INFORMATION = 0x0040
TH32CS_SNAPTHREAD = 0x00000004
MEM_COMMIT = 0x1000
MEM_RESERVE = 0x2000
MEM_RELEASE = 0x8000
PAGE_EXECUTE_READWRITE = 0x40
WOW64_CONTEXT_CONTROL = 0x00010001
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

_HEADER = struct.Struct("<4s7I")
_EVENT = struct.Struct("<IIIHHHHI")


class _ThreadEntry32(ctypes.Structure):
    _fields_ = [
        ("dwSize", ctypes.c_uint32),
        ("cntUsage", ctypes.c_uint32),
        ("th32ThreadID", ctypes.c_uint32),
        ("th32OwnerProcessID", ctypes.c_uint32),
        ("tpBasePri", ctypes.c_int32),
        ("tpDeltaPri", ctypes.c_int32),
        ("dwFlags", ctypes.c_uint32),
    ]


class _Wow64FloatingSaveArea(ctypes.Structure):
    _fields_ = [
        ("ControlWord", ctypes.c_uint32),
        ("StatusWord", ctypes.c_uint32),
        ("TagWord", ctypes.c_uint32),
        ("ErrorOffset", ctypes.c_uint32),
        ("ErrorSelector", ctypes.c_uint32),
        ("DataOffset", ctypes.c_uint32),
        ("DataSelector", ctypes.c_uint32),
        ("RegisterArea", ctypes.c_ubyte * 80),
        ("Cr0NpxState", ctypes.c_uint32),
    ]


class _Wow64Context(ctypes.Structure):
    _fields_ = [
        ("ContextFlags", ctypes.c_uint32),
        ("Dr0", ctypes.c_uint32),
        ("Dr1", ctypes.c_uint32),
        ("Dr2", ctypes.c_uint32),
        ("Dr3", ctypes.c_uint32),
        ("Dr6", ctypes.c_uint32),
        ("Dr7", ctypes.c_uint32),
        ("FloatSave", _Wow64FloatingSaveArea),
        ("SegGs", ctypes.c_uint32),
        ("SegFs", ctypes.c_uint32),
        ("SegEs", ctypes.c_uint32),
        ("SegDs", ctypes.c_uint32),
        ("Edi", ctypes.c_uint32),
        ("Esi", ctypes.c_uint32),
        ("Ebx", ctypes.c_uint32),
        ("Edx", ctypes.c_uint32),
        ("Ecx", ctypes.c_uint32),
        ("Eax", ctypes.c_uint32),
        ("Ebp", ctypes.c_uint32),
        ("Eip", ctypes.c_uint32),
        ("SegCs", ctypes.c_uint32),
        ("EFlags", ctypes.c_uint32),
        ("Esp", ctypes.c_uint32),
        ("SegSs", ctypes.c_uint32),
        ("ExtendedRegisters", ctypes.c_ubyte * 512),
    ]


@dataclass(frozen=True)
class _SuspendedThread:
    handle: int
    thread_id: int
    instruction_pointer: int


class Priority17ProbeUnsafeStateError(RuntimeError):
    """The activation detour could not be proven removed."""


def _u32(value: int) -> bytes:
    if not 0 <= value <= 0xFFFFFFFF:
        raise ValueError(f"value is outside uint32: {value:#x}")
    return struct.pack("<I", value)


def _relative_jump(source: int, target: int) -> bytes:
    displacement = target - (source + 5)
    if not -(1 << 31) <= displacement < (1 << 31):
        raise ValueError("relative jump target is outside rel32 range")
    return b"\xe9" + struct.pack("<i", displacement)


def build_probe_stub(remote_base: int) -> bytes:
    """Build the position-specific x86 callback-exit recorder."""

    serial_address = remote_base + PROBE_SERIAL_OFFSET
    event_base = remote_base + PROBE_EVENT_OFFSET
    code = bytearray()
    code += b"\x9c\x60"  # pushfd; pushad
    code += b"\xa1" + _u32(serial_address)  # mov eax, [serial]
    code += b"\x40"  # inc eax
    code += b"\x89\xc1\x49"  # mov ecx, eax; dec ecx
    code += b"\x81\xe1" + _u32(PROBE_CAPACITY - 1)  # and ecx, 255
    code += b"\x6b\xc9" + bytes((PROBE_EVENT_SIZE,))  # imul ecx, 24
    code += b"\x81\xc1" + _u32(event_base)  # add ecx, event_base

    code += b"\x8b\x15" + _u32(ADDR_ENEMY_MANAGER_FRAME)
    code += b"\x89\x51\x04"  # event.manager_frame
    code += b"\x8b\x15" + _u32(ADDR_ENGINE_FLAGS)
    code += b"\x89\x51\x08"  # event.engine_flags
    code += b"\x0f\xb7\x15" + _u32(ADDR_RAW_INPUT)
    code += b"\x66\x89\x51\x0c"  # event.raw
    code += b"\x0f\xb7\x15" + _u32(ADDR_CURRENT_INPUT)
    code += b"\x66\x89\x51\x0e"  # event.current
    code += b"\x0f\xb7\x15" + _u32(ADDR_PREVIOUS_INPUT)
    code += b"\x66\x89\x51\x10"  # event.previous
    code += b"\x31\xd2\x66\x89\x51\x12"  # event.reserved = 0
    code += b"\x8b\x55\xf4\x8b\x12"  # edx = **(ebp - 0x0c)
    code += b"\x89\x51\x14"  # event.replay_frame_counter

    # Commit the event slot before publishing the new header serial.
    code += b"\x89\x01"  # event.serial = eax
    code += b"\xa3" + _u32(serial_address)  # [serial] = eax
    code += b"\x61\x9d"  # popad; popfd
    code += b"\x8b\xe5\x5d\xc3"  # shipped common epilogue
    return bytes(code)


def build_probe_image(remote_base: int, pid: int) -> bytes:
    """Build initialized header and recorder stub for remote allocation."""

    stub = build_probe_stub(remote_base)
    if PROBE_STUB_OFFSET + len(stub) > PROBE_EVENT_OFFSET:
        raise ValueError("priority-17 probe stub overlaps the event ring")
    image = bytearray(PROBE_EVENT_OFFSET)
    image[:PROBE_HEADER_SIZE] = _HEADER.pack(
        PROBE_MAGIC,
        PROBE_VERSION,
        PROBE_CAPACITY,
        PROBE_EVENT_SIZE,
        0,
        pid,
        PRIORITY17_EPILOGUE_ADDRESS,
        len(stub),
    )
    image[PROBE_STUB_OFFSET : PROBE_STUB_OFFSET + len(stub)] = stub
    return bytes(image)


def build_probe_patches(remote_base: int) -> tuple[bytes, bytes]:
    """Return activation-last epilogue and padding-trampoline patches."""

    epilogue = b"\xeb\x02"
    padding = _relative_jump(
        PRIORITY17_PADDING_ADDRESS,
        remote_base + PROBE_STUB_OFFSET,
    )
    return epilogue, padding


@dataclass(frozen=True)
class Priority17PublicationEvent:
    serial: int
    manager_frame: int
    engine_flags: int
    raw_mask: int
    current_mask: int
    previous_mask: int
    replay_frame_counter: int

    @classmethod
    def decode(cls, payload: bytes) -> Priority17PublicationEvent:
        if len(payload) != PROBE_EVENT_SIZE:
            raise ValueError("priority-17 event size is invalid")
        (
            serial,
            manager_frame,
            engine_flags,
            raw_mask,
            current_mask,
            previous_mask,
            reserved,
            replay_frame_counter,
        ) = _EVENT.unpack(payload)
        if reserved:
            raise ValueError("priority-17 event reserved field is nonzero")
        return cls(
            serial=serial,
            manager_frame=manager_frame,
            engine_flags=engine_flags,
            raw_mask=raw_mask,
            current_mask=current_mask,
            previous_mask=previous_mask,
            replay_frame_counter=replay_frame_counter,
        )

    def compact_record(self) -> dict[str, int]:
        return {
            "serial": self.serial,
            "manager_frame": self.manager_frame,
            "engine_flags": self.engine_flags,
            "raw": self.raw_mask,
            "current": self.current_mask,
            "previous": self.previous_mask,
            "replay_frame_counter": self.replay_frame_counter,
        }


@dataclass(frozen=True)
class Priority17PublicationBatch:
    status: str
    previous_serial: int | None
    observed_serial: int | None
    events: tuple[Priority17PublicationEvent, ...]
    dropped_event_count: int
    error: str | None = None

    def compact_record(self) -> dict[str, object]:
        return {
            "schema": PROBE_SCHEMA,
            "role": "trace_only_no_action_authority",
            "status": self.status,
            "previous_serial": self.previous_serial,
            "observed_serial": self.observed_serial,
            "events": [event.compact_record() for event in self.events],
            "dropped_event_count": self.dropped_event_count,
            "error": self.error,
            "action_authority": False,
        }


def _parse_header(payload: bytes, *, pid: int) -> int:
    if len(payload) != PROBE_HEADER_SIZE:
        raise ValueError("priority-17 probe header size is invalid")
    (
        magic,
        version,
        capacity,
        event_size,
        serial,
        recorded_pid,
        hook_address,
        stub_size,
    ) = _HEADER.unpack(payload)
    if (
        magic != PROBE_MAGIC
        or version != PROBE_VERSION
        or capacity != PROBE_CAPACITY
        or event_size != PROBE_EVENT_SIZE
        or recorded_pid != pid
        or hook_address != PRIORITY17_EPILOGUE_ADDRESS
        or not 0 < stub_size <= PROBE_EVENT_OFFSET - PROBE_STUB_OFFSET
    ):
        raise ValueError("priority-17 probe header identity is invalid")
    return serial


def _probe_owned_instruction_pointer(
    instruction_pointer: int,
    *,
    remote_base: int,
    stub_size: int,
) -> bool:
    """Return whether a suspended thread could still consume probe code."""

    in_padding_trampoline = (
        PRIORITY17_PADDING_ADDRESS
        <= instruction_pointer
        < PRIORITY17_PADDING_ADDRESS + len(PRIORITY17_PADDING_ORIGINAL)
    )
    in_remote_stub = (
        remote_base + PROBE_STUB_OFFSET
        <= instruction_pointer
        < remote_base + PROBE_STUB_OFFSET + stub_size
    )
    return in_padding_trampoline or in_remote_stub


def _release_suspended_threads(
    api: Any,
    suspended: tuple[_SuspendedThread, ...] | list[_SuspendedThread],
) -> tuple[str, ...]:
    errors: list[str] = []
    for thread in reversed(suspended):
        if api.kernel32.ResumeThread(thread.handle) == 0xFFFFFFFF:
            errors.append(
                f"ResumeThread({thread.thread_id}) failed: {_win_error('ResumeThread')}"
            )
        api.kernel32.CloseHandle(thread.handle)
    return tuple(errors)


def _suspend_target_threads(
    api: Any,
    pid: int,
) -> tuple[_SuspendedThread, ...]:
    """Suspend and snapshot every existing target thread or leave none held."""

    snapshot = api.kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0)
    if snapshot == INVALID_HANDLE_VALUE:
        raise _win_error("CreateToolhelp32Snapshot(threads)")
    suspended: list[_SuspendedThread] = []
    try:
        entry = _ThreadEntry32()
        entry.dwSize = ctypes.sizeof(entry)
        if not api.kernel32.Thread32First(snapshot, ctypes.byref(entry)):
            raise _win_error("Thread32First")
        while True:
            if int(entry.th32OwnerProcessID) == pid:
                thread_id = int(entry.th32ThreadID)
                handle = api.kernel32.OpenThread(
                    THREAD_SUSPEND_RESUME
                    | THREAD_GET_CONTEXT
                    | THREAD_QUERY_INFORMATION,
                    False,
                    thread_id,
                )
                if not handle:
                    raise _win_error(f"OpenThread({thread_id})")
                if api.kernel32.SuspendThread(handle) == 0xFFFFFFFF:
                    api.kernel32.CloseHandle(handle)
                    raise _win_error(f"SuspendThread({thread_id})")
                suspended.append(
                    _SuspendedThread(
                        handle=handle,
                        thread_id=thread_id,
                        instruction_pointer=0,
                    )
                )
                context = _Wow64Context()
                context.ContextFlags = WOW64_CONTEXT_CONTROL
                context_reader = (
                    api.kernel32.Wow64GetThreadContext
                    if ctypes.sizeof(ctypes.c_void_p) == 8
                    else api.kernel32.GetThreadContext
                )
                if not context_reader(handle, ctypes.byref(context)):
                    raise _win_error(f"GetThreadContext({thread_id})")
                suspended[-1] = _SuspendedThread(
                    handle=handle,
                    thread_id=thread_id,
                    instruction_pointer=int(context.Eip),
                )
            if not api.kernel32.Thread32Next(snapshot, ctypes.byref(entry)):
                break
        if not suspended:
            raise RuntimeError("target has no enumerable threads")
        return tuple(suspended)
    except Exception as error:
        release_errors = _release_suspended_threads(api, suspended)
        if release_errors:
            raise Priority17ProbeUnsafeStateError(
                "priority-17 probe could not restore target thread suspension: "
                + "; ".join(release_errors)
            ) from error
        raise
    finally:
        api.kernel32.CloseHandle(snapshot)


class Priority17PublicationProbe:
    """Installed remote probe with fail-open bounded trace reads."""

    def __init__(
        self,
        *,
        api: Any,
        pid: int,
        handle: int,
        remote_base: int,
    ) -> None:
        self.api = api
        self.pid = pid
        self.handle = handle
        self.remote_base = remote_base
        self._installed = True
        self._closed = False

    @classmethod
    def install(cls, api: Any, pid: int) -> Priority17PublicationProbe:
        _configure_api(api)
        access = (
            PROCESS_QUERY_INFORMATION
            | PROCESS_VM_OPERATION
            | PROCESS_VM_READ
            | PROCESS_VM_WRITE
        )
        handle = api.kernel32.OpenProcess(access, False, pid)
        if not handle:
            raise _win_error("OpenProcess(priority-17 probe)")
        remote_base = 0
        epilogue_active = False
        padding_active = False
        target_suspend_unsafe = False
        try:
            if (
                _read_memory(
                    api,
                    handle,
                    PRIORITY17_EPILOGUE_ADDRESS,
                    len(PRIORITY17_EPILOGUE_ORIGINAL),
                )
                != PRIORITY17_EPILOGUE_ORIGINAL
            ):
                raise RuntimeError(
                    "priority-17 epilogue does not match shipped bytes"
                )
            if (
                _read_memory(
                    api,
                    handle,
                    PRIORITY17_PADDING_ADDRESS,
                    len(PRIORITY17_PADDING_ORIGINAL),
                )
                != PRIORITY17_PADDING_ORIGINAL
            ):
                raise RuntimeError(
                    "priority-17 padding does not match shipped bytes"
                )

            allocated = api.kernel32.VirtualAllocEx(
                handle,
                None,
                PROBE_ALLOCATION_SIZE,
                MEM_COMMIT | MEM_RESERVE,
                PAGE_EXECUTE_READWRITE,
            )
            remote_base = int(allocated or 0)
            if not remote_base or remote_base > 0xFFFFFFFF:
                raise _win_error("VirtualAllocEx(priority-17 probe)")
            image = build_probe_image(remote_base, pid)
            _write_memory(api, handle, remote_base, image, executable=True)
            epilogue_patch, padding_patch = build_probe_patches(remote_base)
            suspended = _suspend_target_threads(api, pid)
            activation_error: Exception | None = None
            cleanup_errors: list[str] = []
            try:
                if (
                    _read_memory(
                        api,
                        handle,
                        PRIORITY17_EPILOGUE_ADDRESS,
                        len(PRIORITY17_EPILOGUE_ORIGINAL),
                    )
                    != PRIORITY17_EPILOGUE_ORIGINAL
                    or _read_memory(
                        api,
                        handle,
                        PRIORITY17_PADDING_ADDRESS,
                        len(PRIORITY17_PADDING_ORIGINAL),
                    )
                    != PRIORITY17_PADDING_ORIGINAL
                ):
                    raise RuntimeError(
                        "priority-17 hook bytes changed before suspended activation"
                    )
                padding_active = True
                _write_code(
                    api,
                    handle,
                    PRIORITY17_PADDING_ADDRESS,
                    padding_patch,
                )
                # Treat any activation attempt as live until exact rollback is
                # verified; WriteProcessMemory may succeed before a later cache
                # flush/protection restoration error is reported.
                epilogue_active = True
                _write_code(
                    api,
                    handle,
                    PRIORITY17_EPILOGUE_ADDRESS,
                    epilogue_patch,
                )
                if (
                    _read_memory(
                        api,
                        handle,
                        PRIORITY17_EPILOGUE_ADDRESS,
                        len(epilogue_patch),
                    )
                    != epilogue_patch
                    or _read_memory(
                        api,
                        handle,
                        PRIORITY17_PADDING_ADDRESS,
                        len(padding_patch),
                    )
                    != padding_patch
                ):
                    raise RuntimeError(
                        "priority-17 probe patch verification failed"
                    )
            except Exception as error:
                activation_error = error
                if epilogue_active:
                    try:
                        _write_code(
                            api,
                            handle,
                            PRIORITY17_EPILOGUE_ADDRESS,
                            PRIORITY17_EPILOGUE_ORIGINAL,
                        )
                        epilogue_active = (
                            _read_memory(
                                api,
                                handle,
                                PRIORITY17_EPILOGUE_ADDRESS,
                                len(PRIORITY17_EPILOGUE_ORIGINAL),
                            )
                            != PRIORITY17_EPILOGUE_ORIGINAL
                        )
                    except Exception as rollback_error:
                        epilogue_active = True
                        cleanup_errors.append(
                            "epilogue rollback failed: "
                            f"{type(rollback_error).__name__}: {rollback_error}"
                        )
                if padding_active and not epilogue_active:
                    try:
                        _write_code(
                            api,
                            handle,
                            PRIORITY17_PADDING_ADDRESS,
                            PRIORITY17_PADDING_ORIGINAL,
                        )
                        padding_active = (
                            _read_memory(
                                api,
                                handle,
                                PRIORITY17_PADDING_ADDRESS,
                                len(PRIORITY17_PADDING_ORIGINAL),
                            )
                            != PRIORITY17_PADDING_ORIGINAL
                        )
                    except Exception as rollback_error:
                        padding_active = True
                        cleanup_errors.append(
                            "padding rollback failed: "
                            f"{type(rollback_error).__name__}: {rollback_error}"
                        )
            release_errors = _release_suspended_threads(api, suspended)
            if release_errors:
                target_suspend_unsafe = True
                cleanup_errors.extend(release_errors)
            if activation_error is not None:
                if epilogue_active or target_suspend_unsafe:
                    raise Priority17ProbeUnsafeStateError(
                        "priority-17 activation cleanup is unsafe: "
                        + "; ".join(cleanup_errors or [str(activation_error)])
                    ) from activation_error
                if cleanup_errors:
                    raise RuntimeError(
                        f"{activation_error}; " + "; ".join(cleanup_errors)
                    ) from activation_error
                raise activation_error
            if target_suspend_unsafe:
                raise Priority17ProbeUnsafeStateError(
                    "priority-17 activation left a target thread suspended: "
                    + "; ".join(cleanup_errors)
                )
            return cls(
                api=api,
                pid=pid,
                handle=handle,
                remote_base=remote_base,
            )
        except Exception as install_error:
            if remote_base and not epilogue_active and not padding_active:
                api.kernel32.VirtualFreeEx(
                    handle,
                    ctypes.c_void_p(remote_base),
                    0,
                    MEM_RELEASE,
                )
            api.kernel32.CloseHandle(handle)
            if epilogue_active or target_suspend_unsafe:
                raise Priority17ProbeUnsafeStateError(
                    "priority-17 probe activation or thread rollback was not verified; "
                    "the target must be terminated before gameplay"
                ) from install_error
            raise

    def installation_record(self) -> dict[str, object]:
        return {
            "schema": PROBE_SCHEMA,
            "role": "trace_only_no_action_authority",
            "status": "installed",
            "hook": "replay_record_input_frame_common_epilogue",
            "hook_address": PRIORITY17_EPILOGUE_ADDRESS,
            "remote_base": self.remote_base,
            "capacity": PROBE_CAPACITY,
            "event_size": PROBE_EVENT_SIZE,
            "callback_exit_fields": [
                "serial",
                "manager_frame",
                "engine_flags",
                "raw",
                "current",
                "previous",
                "replay_frame_counter",
            ],
            "action_authority": False,
        }

    def sample_serial(self) -> int:
        header = _read_memory(
            self.api,
            self.handle,
            self.remote_base,
            PROBE_HEADER_SIZE,
        )
        return _parse_header(header, pid=self.pid)

    def read_since(
        self,
        previous_serial: int | None,
        *,
        maximum_events: int = 32,
        retries: int = 3,
    ) -> Priority17PublicationBatch:
        if maximum_events <= 0 or maximum_events > PROBE_CAPACITY:
            raise ValueError("maximum_events is outside probe capacity")
        if previous_serial is None:
            try:
                serial = self.sample_serial()
            except Exception as error:
                return Priority17PublicationBatch(
                    status="read_error",
                    previous_serial=None,
                    observed_serial=None,
                    events=(),
                    dropped_event_count=0,
                    error=f"{type(error).__name__}: {error}",
                )
            return Priority17PublicationBatch(
                status="baseline",
                previous_serial=None,
                observed_serial=serial,
                events=(),
                dropped_event_count=0,
            )

        for _attempt in range(retries):
            try:
                serial_before = self.sample_serial()
                distance = (serial_before - previous_serial) & 0xFFFFFFFF
                if distance >= 1 << 31:
                    raise ValueError("priority-17 serial moved backward")
                retained = min(distance, PROBE_CAPACITY, maximum_events)
                dropped = distance - retained
                first = (serial_before - retained + 1) & 0xFFFFFFFF
                events: list[Priority17PublicationEvent] = []
                for offset in range(retained):
                    expected = (first + offset) & 0xFFFFFFFF
                    slot = (expected - 1) & (PROBE_CAPACITY - 1)
                    payload = _read_memory(
                        self.api,
                        self.handle,
                        self.remote_base
                        + PROBE_EVENT_OFFSET
                        + slot * PROBE_EVENT_SIZE,
                        PROBE_EVENT_SIZE,
                    )
                    event = Priority17PublicationEvent.decode(payload)
                    if event.serial != expected:
                        raise RuntimeError(
                            "priority-17 event slot changed during read"
                        )
                    events.append(event)
                serial_after = self.sample_serial()
                if serial_after != serial_before:
                    continue
                status = (
                    "no_events"
                    if not distance
                    else "exact"
                    if not dropped
                    else "overflow_or_trace_truncation"
                )
                return Priority17PublicationBatch(
                    status=status,
                    previous_serial=previous_serial,
                    observed_serial=serial_after,
                    events=tuple(events),
                    dropped_event_count=dropped,
                )
            except (OSError, RuntimeError):
                continue
            except Exception as error:
                return Priority17PublicationBatch(
                    status="read_error",
                    previous_serial=previous_serial,
                    observed_serial=None,
                    events=(),
                    dropped_event_count=0,
                    error=f"{type(error).__name__}: {error}",
                )
        return Priority17PublicationBatch(
            status="race_unknown",
            previous_serial=previous_serial,
            observed_serial=None,
            events=(),
            dropped_event_count=0,
            error="priority-17 ring did not stabilize within retry budget",
        )

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        errors: list[Exception] = []
        unsafe_errors: list[str] = []
        try:
            if self._installed:
                suspended: tuple[_SuspendedThread, ...] | None = None
                stub_size = len(build_probe_stub(self.remote_base))
                for _attempt in range(3):
                    try:
                        candidate = _suspend_target_threads(self.api, self.pid)
                    except Exception as error:
                        unsafe_errors.append(
                            "target suspension for cleanup failed: "
                            f"{type(error).__name__}: {error}"
                        )
                        break
                    if not any(
                        _probe_owned_instruction_pointer(
                            thread.instruction_pointer,
                            remote_base=self.remote_base,
                            stub_size=stub_size,
                        )
                        for thread in candidate
                    ):
                        suspended = candidate
                        break
                    release_errors = _release_suspended_threads(
                        self.api,
                        candidate,
                    )
                    if release_errors:
                        unsafe_errors.extend(release_errors)
                        break
                    time.sleep(0.001)
                if suspended is None and not unsafe_errors:
                    unsafe_errors.append(
                        "probe code remained in flight across cleanup retries"
                    )
                if suspended is not None:
                    try:
                        _write_code(
                            self.api,
                            self.handle,
                            PRIORITY17_EPILOGUE_ADDRESS,
                            PRIORITY17_EPILOGUE_ORIGINAL,
                        )
                    except Exception as error:
                        errors.append(error)
                    try:
                        self._installed = (
                            _read_memory(
                                self.api,
                                self.handle,
                                PRIORITY17_EPILOGUE_ADDRESS,
                                len(PRIORITY17_EPILOGUE_ORIGINAL),
                            )
                            != PRIORITY17_EPILOGUE_ORIGINAL
                        )
                    except Exception as error:
                        self._installed = True
                        errors.append(error)
                    padding_restored = False
                    if not self._installed:
                        try:
                            _write_code(
                                self.api,
                                self.handle,
                                PRIORITY17_PADDING_ADDRESS,
                                PRIORITY17_PADDING_ORIGINAL,
                            )
                            padding_restored = (
                                _read_memory(
                                    self.api,
                                    self.handle,
                                    PRIORITY17_PADDING_ADDRESS,
                                    len(PRIORITY17_PADDING_ORIGINAL),
                                )
                                == PRIORITY17_PADDING_ORIGINAL
                            )
                            if not padding_restored:
                                errors.append(
                                    RuntimeError(
                                        "priority-17 padding restore verification failed"
                                    )
                                )
                        except Exception as error:
                            errors.append(error)
                        if (
                            padding_restored
                            and not self.api.kernel32.VirtualFreeEx(
                                self.handle,
                                ctypes.c_void_p(self.remote_base),
                                0,
                                MEM_RELEASE,
                            )
                        ):
                            errors.append(
                                _win_error("VirtualFreeEx(priority-17 probe)")
                            )
                    release_errors = _release_suspended_threads(
                        self.api,
                        suspended,
                    )
                    if release_errors:
                        unsafe_errors.extend(release_errors)
        finally:
            self.api.kernel32.CloseHandle(self.handle)
        if self._installed:
            unsafe_errors.append("activation detour remains installed")
        if unsafe_errors:
            raise Priority17ProbeUnsafeStateError(
                "priority-17 probe cleanup is unsafe; terminate the target: "
                + "; ".join(unsafe_errors)
            )
        if errors:
            raise RuntimeError(
                "priority-17 probe cleanup failed: "
                + "; ".join(str(error) for error in errors)
            )


def _configure_api(api: Any) -> None:
    api.kernel32.WriteProcessMemory.argtypes = [
        wintypes.HANDLE,
        wintypes.LPVOID,
        wintypes.LPCVOID,
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_size_t),
    ]
    api.kernel32.WriteProcessMemory.restype = wintypes.BOOL
    api.kernel32.VirtualProtectEx.argtypes = [
        wintypes.HANDLE,
        wintypes.LPVOID,
        ctypes.c_size_t,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
    ]
    api.kernel32.VirtualProtectEx.restype = wintypes.BOOL
    api.kernel32.VirtualAllocEx.argtypes = [
        wintypes.HANDLE,
        wintypes.LPVOID,
        ctypes.c_size_t,
        wintypes.DWORD,
        wintypes.DWORD,
    ]
    api.kernel32.VirtualAllocEx.restype = wintypes.LPVOID
    api.kernel32.VirtualFreeEx.argtypes = [
        wintypes.HANDLE,
        wintypes.LPVOID,
        ctypes.c_size_t,
        wintypes.DWORD,
    ]
    api.kernel32.VirtualFreeEx.restype = wintypes.BOOL
    api.kernel32.FlushInstructionCache.argtypes = [
        wintypes.HANDLE,
        wintypes.LPCVOID,
        ctypes.c_size_t,
    ]
    api.kernel32.FlushInstructionCache.restype = wintypes.BOOL
    api.kernel32.CreateToolhelp32Snapshot.argtypes = [
        wintypes.DWORD,
        wintypes.DWORD,
    ]
    api.kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    api.kernel32.Thread32First.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(_ThreadEntry32),
    ]
    api.kernel32.Thread32First.restype = wintypes.BOOL
    api.kernel32.Thread32Next.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(_ThreadEntry32),
    ]
    api.kernel32.Thread32Next.restype = wintypes.BOOL
    api.kernel32.OpenThread.argtypes = [
        wintypes.DWORD,
        wintypes.BOOL,
        wintypes.DWORD,
    ]
    api.kernel32.OpenThread.restype = wintypes.HANDLE
    api.kernel32.SuspendThread.argtypes = [wintypes.HANDLE]
    api.kernel32.SuspendThread.restype = wintypes.DWORD
    api.kernel32.ResumeThread.argtypes = [wintypes.HANDLE]
    api.kernel32.ResumeThread.restype = wintypes.DWORD
    context_reader = (
        api.kernel32.Wow64GetThreadContext
        if ctypes.sizeof(ctypes.c_void_p) == 8
        else api.kernel32.GetThreadContext
    )
    context_reader.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(_Wow64Context),
    ]
    context_reader.restype = wintypes.BOOL


def _win_error(what: str) -> OSError:
    return OSError(ctypes.get_last_error(), what)


def _read_memory(
    api: Any,
    handle: int,
    address: int,
    size: int,
) -> bytes:
    buffer = ctypes.create_string_buffer(size)
    count = ctypes.c_size_t()
    if (
        not api.kernel32.ReadProcessMemory(
            handle,
            ctypes.c_void_p(address),
            buffer,
            size,
            ctypes.byref(count),
        )
        or count.value != size
    ):
        raise _win_error(f"ReadProcessMemory({address:#x}, {size})")
    return buffer.raw


def _write_memory(
    api: Any,
    handle: int,
    address: int,
    data: bytes,
    *,
    executable: bool,
) -> None:
    payload = ctypes.create_string_buffer(data)
    written = ctypes.c_size_t()
    if not api.kernel32.WriteProcessMemory(
        handle,
        ctypes.c_void_p(address),
        payload,
        len(data),
        ctypes.byref(written),
    ) or written.value != len(data):
        raise _win_error(f"WriteProcessMemory({address:#x}, {len(data)})")
    if executable and not api.kernel32.FlushInstructionCache(
        handle,
        ctypes.c_void_p(address),
        len(data),
    ):
        raise _win_error("FlushInstructionCache")


def _write_code(
    api: Any,
    handle: int,
    address: int,
    data: bytes,
) -> None:
    old_protection = wintypes.DWORD()
    if not api.kernel32.VirtualProtectEx(
        handle,
        ctypes.c_void_p(address),
        len(data),
        PAGE_EXECUTE_READWRITE,
        ctypes.byref(old_protection),
    ):
        raise _win_error("VirtualProtectEx")
    try:
        _write_memory(
            api,
            handle,
            address,
            data,
            executable=True,
        )
    finally:
        restored = wintypes.DWORD()
        if not api.kernel32.VirtualProtectEx(
            handle,
            ctypes.c_void_p(address),
            len(data),
            old_protection.value,
            ctypes.byref(restored),
        ):
            raise _win_error("VirtualProtectEx(restore)")


__all__ = [
    "PRIORITY17_EPILOGUE_ADDRESS",
    "PRIORITY17_EPILOGUE_ORIGINAL",
    "PRIORITY17_PADDING_ADDRESS",
    "PRIORITY17_PADDING_ORIGINAL",
    "PROBE_CAPACITY",
    "PROBE_EVENT_OFFSET",
    "PROBE_EVENT_SIZE",
    "PROBE_HEADER_SIZE",
    "PROBE_SCHEMA",
    "PROBE_SERIAL_OFFSET",
    "PROBE_STUB_OFFSET",
    "Priority17PublicationBatch",
    "Priority17PublicationEvent",
    "Priority17PublicationProbe",
    "Priority17ProbeUnsafeStateError",
    "build_probe_image",
    "build_probe_patches",
    "build_probe_stub",
]
