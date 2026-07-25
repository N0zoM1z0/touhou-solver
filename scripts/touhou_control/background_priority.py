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


__all__ = ["lower_current_thread_priority"]
