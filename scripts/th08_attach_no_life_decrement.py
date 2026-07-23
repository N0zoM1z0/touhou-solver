#!/usr/bin/env python3
"""Attach to the exact launched TH08 image and suppress life decrement.

This is an analysis-only runtime patch. It verifies the executable identity
and original opcode byte before changing process memory; the file on disk is
never modified.
"""

from __future__ import annotations

import ctypes
import os
import sys
import time
from ctypes import wintypes
from pathlib import Path

from th08_runtime_agent import (
    ADDR_NO_LIFE_DECREMENT_PATCH,
    ProcessReader,
    TARGET_EXE,
    Win32,
    _win_error,
    verify_target,
)


GAME_DIR = Path(os.environ.get("TH08_GAME_DIR", os.getcwd())).resolve()
LOG_PATH = GAME_DIR / "runtime_patch_log.txt"
EXPECTED_OLD = b"\xff"
PATCH_NEW = b"\x00"

PROCESS_VM_WRITE = 0x0020
PROCESS_VM_OPERATION = 0x0008
PROCESS_QUERY_INFORMATION = 0x0400
PAGE_EXECUTE_READWRITE = 0x40


def log(message: str) -> None:
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {message}"
    print(line, flush=True)
    with LOG_PATH.open("a", encoding="utf-8", newline="\n") as output:
        output.write(line + "\n")


def _same_path(left: Path, right: Path) -> bool:
    return os.path.normcase(str(left.resolve())) == os.path.normcase(str(right.resolve()))


def find_exact_target(api: Win32, timeout_seconds: float = 15.0) -> tuple[int, dict[str, object]]:
    expected_path = GAME_DIR / TARGET_EXE
    deadline = time.perf_counter() + timeout_seconds
    last_errors: list[str] = []
    while time.perf_counter() < deadline:
        matches: list[tuple[int, dict[str, object]]] = []
        last_errors.clear()
        for pid in api.find_pids(TARGET_EXE):
            reader = ProcessReader(api, pid)
            try:
                identity = verify_target(reader)
                if _same_path(Path(str(identity["image_path"])), expected_path):
                    matches.append((pid, identity))
            except Exception as exc:
                last_errors.append(f"pid={pid}: {exc}")
            finally:
                reader.close()
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise RuntimeError(
                "refusing ambiguous exact TH08 targets: "
                + ", ".join(str(pid) for pid, _identity in matches)
            )
        time.sleep(0.25)
    detail = "; ".join(last_errors) if last_errors else "no th08.exe candidate"
    raise RuntimeError(f"exact TH08 target not found: {detail}")


def configure_write_api(api: Win32) -> None:
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
    api.kernel32.FlushInstructionCache.argtypes = [
        wintypes.HANDLE,
        wintypes.LPCVOID,
        ctypes.c_size_t,
    ]
    api.kernel32.FlushInstructionCache.restype = wintypes.BOOL


def read_memory(api: Win32, handle: int, address: int, size: int) -> bytes:
    buffer = ctypes.create_string_buffer(size)
    count = ctypes.c_size_t()
    ok = api.kernel32.ReadProcessMemory(
        handle,
        ctypes.c_void_p(address),
        buffer,
        size,
        ctypes.byref(count),
    )
    if not ok or count.value != size:
        raise _win_error(f"ReadProcessMemory({address:#x}, {size})")
    return buffer.raw


def write_memory(api: Win32, handle: int, address: int, data: bytes) -> None:
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
        written = ctypes.c_size_t()
        if not api.kernel32.WriteProcessMemory(
            handle,
            ctypes.c_void_p(address),
            data,
            len(data),
            ctypes.byref(written),
        ) or written.value != len(data):
            raise _win_error("WriteProcessMemory")
        if not api.kernel32.FlushInstructionCache(
            handle, ctypes.c_void_p(address), len(data)
        ):
            raise _win_error("FlushInstructionCache")
    finally:
        restored = wintypes.DWORD()
        api.kernel32.VirtualProtectEx(
            handle,
            ctypes.c_void_p(address),
            len(data),
            old_protection.value,
            ctypes.byref(restored),
        )


def main() -> int:
    log("attach patcher started")
    api = Win32()
    configure_write_api(api)
    pid, identity = find_exact_target(api)
    log(
        f"verified {identity['image_path']} pid={pid} "
        f"sha256={identity['sha256']}"
    )
    access = PROCESS_QUERY_INFORMATION | PROCESS_VM_OPERATION | PROCESS_VM_WRITE | 0x0010
    handle = api.kernel32.OpenProcess(access, False, pid)
    if not handle:
        raise _win_error("OpenProcess")
    try:
        old = read_memory(api, handle, ADDR_NO_LIFE_DECREMENT_PATCH, 1)
        log(f"read 0x{ADDR_NO_LIFE_DECREMENT_PATCH:08X} = {old.hex()}")
        if old == PATCH_NEW:
            log("already patched")
            return 0
        if old != EXPECTED_OLD:
            raise RuntimeError(
                f"unexpected byte at 0x{ADDR_NO_LIFE_DECREMENT_PATCH:08X}: {old.hex()}"
            )
        write_memory(api, handle, ADDR_NO_LIFE_DECREMENT_PATCH, PATCH_NEW)
        new = read_memory(api, handle, ADDR_NO_LIFE_DECREMENT_PATCH, 1)
        if new != PATCH_NEW:
            raise RuntimeError(f"runtime patch verification failed: {new.hex()}")
        log(
            f"patched memory: 0x{ADDR_NO_LIFE_DECREMENT_PATCH:08X}: "
            "FF -> 00"
        )
        return 0
    finally:
        api.kernel32.CloseHandle(handle)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        log(f"error: {exc}")
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
