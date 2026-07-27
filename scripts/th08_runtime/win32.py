"""Win32 process discovery, guarded memory reads, and target verification."""

from __future__ import annotations

import ctypes
import hashlib
import os
import struct
from ctypes import wintypes
from pathlib import Path

from th08_runtime.game_state import (
    ADDR_NO_LIFE_DECREMENT_PATCH,
    EXPECTED_EXE_SHA256,
    TARGET_EXE,
)

PROCESS_VM_READ = 0x0010
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
TH32CS_SNAPPROCESS = 0x00000002
INVALID_HANDLE_VALUE = wintypes.HANDLE(-1).value

INPUT_KEYBOARD = 1
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008
INJECTION_MARKER = 0x54483038


class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.c_void_p),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", wintypes.LONG),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", wintypes.WCHAR * 260),
    ]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT),
    ]


class INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [("type", wintypes.DWORD), ("u", INPUT_UNION)]


def require_windows() -> None:
    if os.name != "nt":
        raise RuntimeError("th08_runtime_agent.py must run under Windows Python")


def win_error(what: str) -> OSError:
    return ctypes.WinError(ctypes.get_last_error(), what)


class Win32:
    def __init__(self) -> None:
        require_windows()
        self.kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self.user32 = ctypes.WinDLL("user32", use_last_error=True)
        self.kernel32.CreateToolhelp32Snapshot.argtypes = [
            wintypes.DWORD,
            wintypes.DWORD,
        ]
        self.kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
        self.kernel32.Process32FirstW.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(PROCESSENTRY32W),
        ]
        self.kernel32.Process32FirstW.restype = wintypes.BOOL
        self.kernel32.Process32NextW.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(PROCESSENTRY32W),
        ]
        self.kernel32.Process32NextW.restype = wintypes.BOOL
        self.kernel32.OpenProcess.argtypes = [
            wintypes.DWORD,
            wintypes.BOOL,
            wintypes.DWORD,
        ]
        self.kernel32.OpenProcess.restype = wintypes.HANDLE
        self.kernel32.ReadProcessMemory.argtypes = [
            wintypes.HANDLE,
            wintypes.LPCVOID,
            wintypes.LPVOID,
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_size_t),
        ]
        self.kernel32.ReadProcessMemory.restype = wintypes.BOOL
        self.kernel32.QueryFullProcessImageNameW.argtypes = [
            wintypes.HANDLE,
            wintypes.DWORD,
            wintypes.LPWSTR,
            ctypes.POINTER(wintypes.DWORD),
        ]
        self.kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
        self.kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        self.user32.SendInput.argtypes = [
            wintypes.UINT,
            ctypes.POINTER(INPUT),
            ctypes.c_int,
        ]
        self.user32.SendInput.restype = wintypes.UINT
        self.user32.GetForegroundWindow.restype = wintypes.HWND
        self.user32.GetWindowThreadProcessId.argtypes = [
            wintypes.HWND,
            ctypes.POINTER(wintypes.DWORD),
        ]
        self.user32.GetWindowThreadProcessId.restype = wintypes.DWORD
        self.user32.SetForegroundWindow.argtypes = [wintypes.HWND]
        self.user32.SetForegroundWindow.restype = wintypes.BOOL
        expected_input_size = 40 if ctypes.sizeof(ctypes.c_void_p) == 8 else 28
        if ctypes.sizeof(INPUT) != expected_input_size:
            raise RuntimeError(
                f"unexpected Win32 INPUT layout {ctypes.sizeof(INPUT)}; "
                f"expected {expected_input_size}"
            )

    def find_pids(self, exe_name: str) -> tuple[int, ...]:
        snapshot = self.kernel32.CreateToolhelp32Snapshot(
            TH32CS_SNAPPROCESS,
            0,
        )
        if snapshot == INVALID_HANDLE_VALUE:
            raise win_error("CreateToolhelp32Snapshot")
        try:
            entry = PROCESSENTRY32W()
            entry.dwSize = ctypes.sizeof(entry)
            if not self.kernel32.Process32FirstW(
                snapshot,
                ctypes.byref(entry),
            ):
                return ()
            matches: list[int] = []
            while True:
                if entry.szExeFile.lower() == exe_name.lower():
                    matches.append(int(entry.th32ProcessID))
                if not self.kernel32.Process32NextW(
                    snapshot,
                    ctypes.byref(entry),
                ):
                    return tuple(matches)
        finally:
            self.kernel32.CloseHandle(snapshot)

    def find_pid(self, exe_name: str) -> int:
        matches = self.find_pids(exe_name)
        if not matches:
            raise RuntimeError(f"{exe_name} is not running")
        if len(matches) != 1:
            raise RuntimeError(
                f"refusing ambiguous {exe_name} target; running PIDs={matches}"
            )
        return matches[0]

    def foreground_pid(self) -> int:
        pid = wintypes.DWORD()
        window = self.user32.GetForegroundWindow()
        self.user32.GetWindowThreadProcessId(window, ctypes.byref(pid))
        return int(pid.value)


class ProcessReader:
    def __init__(self, api: Win32, pid: int) -> None:
        self.api = api
        self.pid = pid
        access = PROCESS_VM_READ | PROCESS_QUERY_LIMITED_INFORMATION
        self.handle = api.kernel32.OpenProcess(access, False, pid)
        if not self.handle:
            raise win_error("OpenProcess")

    def close(self) -> None:
        if self.handle:
            self.api.kernel32.CloseHandle(self.handle)
            self.handle = None

    @staticmethod
    def allocate_buffer(size: int):
        if size <= 0:
            raise ValueError("process read buffer size must be positive")
        return ctypes.create_string_buffer(size)

    def read_into(self, address: int, buffer):
        size = ctypes.sizeof(buffer)
        count = ctypes.c_size_t()
        ok = self.api.kernel32.ReadProcessMemory(
            self.handle,
            ctypes.c_void_p(address),
            buffer,
            size,
            ctypes.byref(count),
        )
        if not ok or count.value != size:
            raise win_error(f"ReadProcessMemory({address:#x}, {size})")
        return buffer

    def read(self, address: int, size: int) -> bytes:
        buffer = self.allocate_buffer(size)
        self.read_into(address, buffer)
        return buffer.raw

    def image_path(self) -> Path:
        buffer = ctypes.create_unicode_buffer(32768)
        size = wintypes.DWORD(len(buffer))
        if not self.api.kernel32.QueryFullProcessImageNameW(
            self.handle,
            0,
            buffer,
            ctypes.byref(size),
        ):
            raise win_error("QueryFullProcessImageNameW")
        return Path(buffer.value)

    def u8(self, address: int) -> int:
        return self.read(address, 1)[0]

    def u16(self, address: int) -> int:
        return struct.unpack("<H", self.read(address, 2))[0]

    def u32(self, address: int) -> int:
        return struct.unpack("<I", self.read(address, 4))[0]

    def i32(self, address: int) -> int:
        return struct.unpack("<i", self.read(address, 4))[0]

    def f32(self, address: int) -> float:
        return struct.unpack("<f", self.read(address, 4))[0]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_target(reader: ProcessReader) -> dict[str, object]:
    image_path = reader.image_path()
    digest = _sha256(image_path)
    if image_path.name.lower() != TARGET_EXE or digest != EXPECTED_EXE_SHA256:
        raise RuntimeError(
            f"target identity mismatch: path={image_path}, sha256={digest}"
        )
    if reader.read(0x00400000, 2) != b"MZ":
        raise RuntimeError("target base does not contain the expected PE header")
    life_patch_byte = reader.u8(ADDR_NO_LIFE_DECREMENT_PATCH)
    if life_patch_byte not in (0xFF, 0x00):
        raise RuntimeError(
            "unexpected no-life-decrement patch site byte: "
            f"{life_patch_byte:#04x}"
        )
    return {
        "pid": reader.pid,
        "image_path": str(image_path),
        "sha256": digest,
        "runtime_patch": {
            "address": ADDR_NO_LIFE_DECREMENT_PATCH,
            "byte": life_patch_byte,
            "no_life_decrement": life_patch_byte == 0x00,
        },
    }
