"""Allocation-stable current-thread cycle telemetry."""

from __future__ import annotations

import ctypes
import os
from typing import Protocol


THREAD_CYCLE_SOURCE_WINDOWS = "windows_query_thread_cycle_time"
THREAD_CYCLE_SOURCE_UNAVAILABLE = "unavailable_non_windows"
THREAD_CYCLE_SOURCE_QUERY_FAILED = "query_failed"


class ThreadCycleSampler(Protocol):
    """Narrow injectable interface for one thread's cumulative cycles."""

    @property
    def source(self) -> str: ...

    def read(self) -> int | None: ...


class CurrentThreadCycleSampler:
    """Reuse one Windows counter destination and keep the GIL held."""

    def __init__(self) -> None:
        self._source = THREAD_CYCLE_SOURCE_UNAVAILABLE
        self._query = None
        self._value = None
        self._value_pointer = None
        if os.name != "nt":
            return
        try:
            kernel32 = ctypes.PyDLL("kernel32", use_last_error=True)
            kernel32.GetCurrentThread.argtypes = []
            kernel32.GetCurrentThread.restype = ctypes.c_void_p
            kernel32.QueryThreadCycleTime.argtypes = [
                ctypes.c_void_p,
                ctypes.POINTER(ctypes.c_ulonglong),
            ]
            kernel32.QueryThreadCycleTime.restype = ctypes.c_int
            value = ctypes.c_ulonglong()
            self._kernel32 = kernel32
            self._thread = kernel32.GetCurrentThread()
            self._query = kernel32.QueryThreadCycleTime
            self._value = value
            self._value_pointer = ctypes.pointer(value)
            self._source = THREAD_CYCLE_SOURCE_WINDOWS
        except (AttributeError, OSError):
            self._source = THREAD_CYCLE_SOURCE_QUERY_FAILED

    @property
    def source(self) -> str:
        return self._source

    def read(self) -> int | None:
        if self._source != THREAD_CYCLE_SOURCE_WINDOWS:
            return None
        assert self._query is not None
        assert self._value is not None
        assert self._value_pointer is not None
        if not self._query(self._thread, self._value_pointer):
            self._source = THREAD_CYCLE_SOURCE_QUERY_FAILED
            return None
        return int(self._value.value)


__all__ = [
    "THREAD_CYCLE_SOURCE_QUERY_FAILED",
    "THREAD_CYCLE_SOURCE_UNAVAILABLE",
    "THREAD_CYCLE_SOURCE_WINDOWS",
    "CurrentThreadCycleSampler",
    "ThreadCycleSampler",
]
