"""Best-effort priority isolation for research-only background workers."""

from __future__ import annotations

import ctypes
import os
import threading


def lower_current_thread_priority() -> bool:
    """Yield CPU without changing the game or issue-time controller thread."""

    try:
        if os.name == "nt":
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel32.GetCurrentThread.restype = ctypes.c_void_p
            kernel32.SetThreadPriority.argtypes = [
                ctypes.c_void_p,
                ctypes.c_int,
            ]
            kernel32.SetThreadPriority.restype = ctypes.c_int
            # BELOW_NORMAL preserves progress while yielding to the game,
            # sensor, Boolean publication, and issue-time controller.
            return bool(
                kernel32.SetThreadPriority(
                    kernel32.GetCurrentThread(),
                    -1,
                )
            )
        if hasattr(os, "setpriority") and hasattr(os, "PRIO_PROCESS"):
            native_id = threading.get_native_id()
            current = os.getpriority(os.PRIO_PROCESS, native_id)
            os.setpriority(
                os.PRIO_PROCESS,
                native_id,
                max(current, 5),
            )
            return True
    except (AttributeError, OSError):
        return False
    return False


def pin_current_thread_to_cpu(cpu_index: int) -> bool:
    """Pin only the calling research worker; never alter process affinity."""

    if cpu_index < 0:
        raise ValueError("CPU index must be nonnegative")
    try:
        if os.name == "nt":
            if cpu_index >= 64:
                return False
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel32.GetCurrentThread.restype = ctypes.c_void_p
            kernel32.SetThreadAffinityMask.argtypes = [
                ctypes.c_void_p,
                ctypes.c_size_t,
            ]
            kernel32.SetThreadAffinityMask.restype = ctypes.c_size_t
            return bool(
                kernel32.SetThreadAffinityMask(
                    kernel32.GetCurrentThread(),
                    ctypes.c_size_t(1 << cpu_index),
                )
            )
        if hasattr(os, "sched_setaffinity"):
            os.sched_setaffinity(threading.get_native_id(), {cpu_index})
            return True
    except (AttributeError, OSError):
        return False
    return False


def preferred_performance_cpu() -> int | None:
    """Choose the highest logical CPU in the highest Windows efficiency class."""

    visible = os.cpu_count() or 0
    if visible <= 0:
        return None
    if os.name != "nt":
        return visible - 1
    try:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        required = ctypes.c_ulong()
        kernel32.GetSystemCpuSetInformation(
            None,
            0,
            ctypes.byref(required),
            None,
            0,
        )
        if required.value == 0:
            return None
        buffer = (ctypes.c_ubyte * required.value)()
        if not kernel32.GetSystemCpuSetInformation(
            buffer,
            required.value,
            ctypes.byref(required),
            None,
            0,
        ):
            return None
        raw = bytes(buffer)
        records: list[tuple[int, int]] = []
        offset = 0
        while offset + 8 <= len(raw):
            size = int.from_bytes(raw[offset : offset + 4], "little")
            record_type = int.from_bytes(
                raw[offset + 4 : offset + 8],
                "little",
            )
            if size < 8 or offset + size > len(raw):
                return None
            if record_type == 0 and size >= 32:
                group = int.from_bytes(
                    raw[offset + 12 : offset + 14],
                    "little",
                )
                logical = raw[offset + 14]
                efficiency = raw[offset + 18]
                if group == 0 and logical < visible:
                    records.append((efficiency, logical))
            offset += size
        if not records:
            return None
        maximum_efficiency = max(efficiency for efficiency, _ in records)
        return max(
            logical
            for efficiency, logical in records
            if efficiency == maximum_efficiency
        )
    except (AttributeError, OSError):
        return None


__all__ = [
    "lower_current_thread_priority",
    "pin_current_thread_to_cpu",
    "preferred_performance_cpu",
]
