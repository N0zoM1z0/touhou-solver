"""Shared Win32 process-memory and thread-suspension support for native probes."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass
from typing import Any


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


class ProbeUnsafeStateError(RuntimeError):
    """A probe could not prove that invasive target state was restored."""


def _win_error(what: str) -> OSError:
    return OSError(ctypes.get_last_error(), what)


def _release_suspended_threads(
    api: Any,
    suspended: tuple[_SuspendedThread, ...] | list[_SuspendedThread],
) -> tuple[str, ...]:
    errors: list[str] = []
    for thread in reversed(suspended):
        if api.kernel32.ResumeThread(thread.handle) == 0xFFFFFFFF:
            errors.append(
                f"ResumeThread({thread.thread_id}) failed: "
                f"{_win_error('ResumeThread')}"
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
                    _SuspendedThread(handle, thread_id, 0)
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
                    handle,
                    thread_id,
                    int(context.Eip),
                )
            if not api.kernel32.Thread32Next(snapshot, ctypes.byref(entry)):
                break
        if not suspended:
            raise RuntimeError("target has no enumerable threads")
        return tuple(suspended)
    except Exception as error:
        release_errors = _release_suspended_threads(api, suspended)
        if release_errors:
            raise ProbeUnsafeStateError(
                "native probe could not restore target thread suspension: "
                + "; ".join(release_errors)
            ) from error
        raise
    finally:
        api.kernel32.CloseHandle(snapshot)


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
        _write_memory(api, handle, address, data, executable=True)
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


__all__ = ["ProbeUnsafeStateError"]
