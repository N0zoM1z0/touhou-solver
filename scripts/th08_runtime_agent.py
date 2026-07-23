#!/usr/bin/env python3
"""Read-only TH08 runtime probe and fail-closed physical-key playback agent.

Run this script with Windows Python. ``probe`` and ``observe`` never write to
the target. ``play`` uses ordinary scan-code ``SendInput`` events; it never
patches process memory and requires an explicit ``--armed`` flag.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import struct
import sys
import time
from ctypes import wintypes
from pathlib import Path

from runtime_agent import (
    FrameSynchronizedPlayback,
    InputTransition,
    load_input_masks,
)


EXPECTED_EXE_SHA256 = "330fbdbf58a710829d65277b4f312cfbb38d5448b3df523e79350b879213d924"
TARGET_EXE = "th08.exe"
SUPPORTED_INPUT_MASK = 0x00F7

ADDR_GAMEPLAY_RNG = 0x0164D520
ADDR_NO_LIFE_DECREMENT_PATCH = 0x0044D0FA
ADDR_RAW_INPUT = 0x0164D528
ADDR_CURRENT_INPUT = 0x0164D52C
ADDR_PREVIOUS_INPUT = 0x0164D534
ADDR_ROUTE_ID = 0x0164D0B1
ADDR_ENGINE_FLAGS = 0x0164D0B4
ADDR_STAGE_ROUTE_INDEX = 0x0164D2CC
ADDR_ENEMY_MANAGER_FRAME = 0x0164D30C
ADDR_SPELL_CARD_STATE = 0x004EA670
ADDR_RUN_STATE_INNER_POINTER = 0x0160F510
ADDR_DIFFICULTY_INDEX = 0x0160F538
ADDR_PLAYER = 0x017D5EF8

RUN_STATE_LIVES_OFFSET = 0x74
RUN_STATE_BOMBS_OFFSET = 0x80
RUN_STATE_POWER_OFFSET = 0x98

PLAYER_POSITION_OFFSET = 0x2B4
PLAYER_BOMB_ACTIVE_OFFSET = 0xFDC
PLAYER_BOMB_INDEX_OFFSET = 0xFE0
PLAYER_BOMB_TIMER_OFFSET = 0xFF4
PLAYER_PREDEATH_COUNTER_OFFSET = 0xE2A68
PLAYER_BOMB_LOCKOUT_OFFSET = 0xE2A6C

SPELL_STATE_PREFIX_SIZE = 68
SPELL_STATE_ACTIVE_FLAG = 0x01

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
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]


class INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [("type", wintypes.DWORD), ("u", INPUT_UNION)]


SCAN_CODES = {
    0x01: (0x2C, False),  # Z: shot
    0x02: (0x2D, False),  # X: Bomb
    0x04: (0x2A, False),  # left Shift: focus
    0x10: (0x48, True),
    0x20: (0x50, True),
    0x40: (0x4B, True),
    0x80: (0x4D, True),
}

TAP_NAMES = {
    "z": 0x01,
    "confirm": 0x01,
    "x": 0x02,
    "cancel": 0x02,
    "focus": 0x04,
    "up": 0x10,
    "down": 0x20,
    "left": 0x40,
    "right": 0x80,
}


def _require_windows() -> None:
    if os.name != "nt":
        raise RuntimeError("th08_runtime_agent.py must run under Windows Python")


def _win_error(what: str) -> OSError:
    return ctypes.WinError(ctypes.get_last_error(), what)


class Win32:
    def __init__(self) -> None:
        _require_windows()
        self.kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self.user32 = ctypes.WinDLL("user32", use_last_error=True)
        self.kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
        self.kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
        self.kernel32.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
        self.kernel32.Process32FirstW.restype = wintypes.BOOL
        self.kernel32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
        self.kernel32.Process32NextW.restype = wintypes.BOOL
        self.kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
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
        self.user32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
        self.user32.SendInput.restype = wintypes.UINT
        self.user32.GetForegroundWindow.restype = wintypes.HWND
        self.user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
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
        snapshot = self.kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if snapshot == INVALID_HANDLE_VALUE:
            raise _win_error("CreateToolhelp32Snapshot")
        try:
            entry = PROCESSENTRY32W()
            entry.dwSize = ctypes.sizeof(entry)
            if not self.kernel32.Process32FirstW(snapshot, ctypes.byref(entry)):
                return ()
            matches: list[int] = []
            while True:
                if entry.szExeFile.lower() == exe_name.lower():
                    matches.append(int(entry.th32ProcessID))
                if not self.kernel32.Process32NextW(snapshot, ctypes.byref(entry)):
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
            raise _win_error("OpenProcess")

    def close(self) -> None:
        if self.handle:
            self.api.kernel32.CloseHandle(self.handle)
            self.handle = None

    def read(self, address: int, size: int) -> bytes:
        buffer = ctypes.create_string_buffer(size)
        count = ctypes.c_size_t()
        ok = self.api.kernel32.ReadProcessMemory(
            self.handle,
            ctypes.c_void_p(address),
            buffer,
            size,
            ctypes.byref(count),
        )
        if not ok or count.value != size:
            raise _win_error(f"ReadProcessMemory({address:#x}, {size})")
        return buffer.raw

    def image_path(self) -> Path:
        buffer = ctypes.create_unicode_buffer(32768)
        size = wintypes.DWORD(len(buffer))
        if not self.api.kernel32.QueryFullProcessImageNameW(
            self.handle, 0, buffer, ctypes.byref(size)
        ):
            raise _win_error("QueryFullProcessImageNameW")
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


def decode_spell_state(blob: bytes) -> dict[str, object]:
    if len(blob) < SPELL_STATE_PREFIX_SIZE:
        raise ValueError(
            f"spell state prefix requires {SPELL_STATE_PREFIX_SIZE} bytes"
        )
    flags, enemy_pointer, spell_id = struct.unpack_from("<III", blob)
    encoded_name = blob[20:68].split(b"\0", 1)[0]
    return {
        "active": bool(flags & SPELL_STATE_ACTIVE_FLAG),
        "flags": flags,
        "enemy_pointer": enemy_pointer,
        "spell_id": spell_id,
        "name": encoded_name.decode("shift_jis", errors="replace"),
    }


def observe_state(reader: ProcessReader) -> dict[str, object]:
    engine_flags = reader.u32(ADDR_ENGINE_FLAGS)
    inner = reader.u32(ADDR_RUN_STATE_INNER_POINTER)
    resources = None
    if inner and engine_flags & 0x04:
        resources = {
            "lives": reader.f32(inner + RUN_STATE_LIVES_OFFSET),
            "bombs": reader.f32(inner + RUN_STATE_BOMBS_OFFSET),
            "power": reader.f32(inner + RUN_STATE_POWER_OFFSET),
        }
    return {
        "wall_time_ns": time.time_ns(),
        "enemy_manager_frame": reader.u32(ADDR_ENEMY_MANAGER_FRAME),
        "engine_flags": engine_flags,
        "gameplay_active": bool(engine_flags & 0x04),
        "route_id": reader.u8(ADDR_ROUTE_ID),
        "stage_route_index": reader.u32(ADDR_STAGE_ROUTE_INDEX),
        "difficulty_index": reader.u32(ADDR_DIFFICULTY_INDEX),
        "input_raw": reader.u16(ADDR_RAW_INPUT),
        "input_current": reader.u16(ADDR_CURRENT_INPUT),
        "input_previous": reader.u16(ADDR_PREVIOUS_INPUT),
        "rng_state": reader.u16(ADDR_GAMEPLAY_RNG),
        "rng_calls": reader.u32(ADDR_GAMEPLAY_RNG + 4),
        "spell": decode_spell_state(
            reader.read(ADDR_SPELL_CARD_STATE, SPELL_STATE_PREFIX_SIZE)
        ),
        "player": {
            "phase": reader.u8(ADDR_PLAYER),
            "focus_logic": reader.u8(ADDR_PLAYER + 3),
            "deathbomb": reader.u8(ADDR_PLAYER + 4),
            "forced_bomb": reader.u8(ADDR_PLAYER + 6),
            "x": reader.f32(ADDR_PLAYER + PLAYER_POSITION_OFFSET),
            "y": reader.f32(ADDR_PLAYER + PLAYER_POSITION_OFFSET + 4),
            "bomb_active": reader.u32(ADDR_PLAYER + PLAYER_BOMB_ACTIVE_OFFSET),
            "bomb_index": reader.i32(ADDR_PLAYER + PLAYER_BOMB_INDEX_OFFSET),
            "bomb_timer": reader.i32(ADDR_PLAYER + PLAYER_BOMB_TIMER_OFFSET),
            "predeath_counter": reader.i32(ADDR_PLAYER + PLAYER_PREDEATH_COUNTER_OFFSET),
            "bomb_lockout": reader.i32(ADDR_PLAYER + PLAYER_BOMB_LOCKOUT_OFFSET),
        },
        "resources": resources,
    }


def _keyboard_input(transition: InputTransition) -> INPUT:
    try:
        scan_code, extended = SCAN_CODES[transition.bit]
    except KeyError as exc:
        raise ValueError(f"no TH08 key mapping for input bit {transition.bit:#x}") from exc
    return _scan_keyboard_input(scan_code, extended, transition.pressed)


def _scan_keyboard_input(scan_code: int, extended: bool, pressed: bool) -> INPUT:
    flags = KEYEVENTF_SCANCODE
    if extended:
        flags |= KEYEVENTF_EXTENDEDKEY
    if not pressed:
        flags |= KEYEVENTF_KEYUP
    return INPUT(INPUT_KEYBOARD, INPUT_UNION(ki=KEYBDINPUT(0, scan_code, flags, 0, INJECTION_MARKER)))


def send_transitions(api: Win32, transitions: tuple[InputTransition, ...]) -> None:
    if not transitions:
        return
    inputs = (INPUT * len(transitions))(*(_keyboard_input(item) for item in transitions))
    sent = api.user32.SendInput(len(inputs), inputs, ctypes.sizeof(INPUT))
    if sent != len(inputs):
        raise _win_error(f"SendInput sent {sent}/{len(inputs)} events")


def release_all(api: Win32) -> None:
    send_transitions(
        api,
        tuple(InputTransition(bit, False) for bit in SCAN_CODES),
    )


def release_injected_keys(api: Win32) -> None:
    """Release every key this bridge can hold, including replay fast-forward."""

    release_all(api)
    send_scan_key(api, scan_code=0x1D, pressed=False)


def send_scan_key(
    api: Win32, *, scan_code: int, extended: bool = False, pressed: bool
) -> None:
    item = _scan_keyboard_input(scan_code, extended, pressed)
    sent = api.user32.SendInput(1, ctypes.byref(item), ctypes.sizeof(INPUT))
    if sent != 1:
        raise _win_error("SendInput special scan key")


def _open_target(args: argparse.Namespace) -> tuple[Win32, ProcessReader, dict[str, object]]:
    api = Win32()
    pid = args.pid if args.pid is not None else api.find_pid(TARGET_EXE)
    reader = ProcessReader(api, pid)
    try:
        identity = verify_target(reader)
    except Exception:
        reader.close()
        raise
    return api, reader, identity


def command_probe(args: argparse.Namespace) -> int:
    _, reader, identity = _open_target(args)
    try:
        print(json.dumps({"identity": identity, "state": observe_state(reader)}))
    finally:
        reader.close()
    return 0


def command_observe(args: argparse.Namespace) -> int:
    _, reader, identity = _open_target(args)
    deadline = time.perf_counter() + args.duration
    previous_counter = None
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as output:
        output.write(json.dumps({"kind": "identity", **identity}) + "\n")
        try:
            while time.perf_counter() < deadline:
                state = observe_state(reader)
                counter = state["enemy_manager_frame"]
                if counter != previous_counter:
                    output.write(json.dumps({"kind": "frame", **state}) + "\n")
                    output.flush()
                    previous_counter = counter
                time.sleep(args.poll_ms / 1000.0)
        finally:
            reader.close()
    return 0


def _require_foreground(api: Win32, pid: int) -> None:
    if api.foreground_pid() != pid:
        raise RuntimeError("TH08 lost foreground; refusing to send or retain keys")


def command_play(args: argparse.Namespace) -> int:
    if not args.armed:
        raise RuntimeError("physical playback requires the explicit --armed flag")
    masks = load_input_masks(args.trace)
    api, reader, identity = _open_target(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output = args.output.open("w", encoding="utf-8", newline="\n")
    try:
        initial = observe_state(reader)
        if initial["route_id"] != 2:
            raise RuntimeError(f"route ID {initial['route_id']} is not Sakuya/Remilia route 2")
        if not initial["gameplay_active"]:
            raise RuntimeError("TH08 gameplay update flag is not active")
        if initial["input_current"] & SUPPORTED_INPUT_MASK:
            raise RuntimeError("player input is already held before agent arming")
        _require_foreground(api, reader.pid)

        playback = FrameSynchronizedPlayback(masks, supported_mask=SUPPORTED_INPUT_MASK)
        counter = int(initial["enemy_manager_frame"])
        output.write(json.dumps({"kind": "identity", **identity}) + "\n")
        output.write(json.dumps({"kind": "arm", "counter": counter, "state": initial}) + "\n")
        send_transitions(api, playback.arm(counter))

        last_change = time.perf_counter()
        while True:
            _require_foreground(api, reader.pid)
            current_counter = reader.u32(ADDR_ENEMY_MANAGER_FRAME)
            if current_counter == counter:
                if time.perf_counter() - last_change > args.frame_timeout:
                    raise RuntimeError("target frame counter stopped")
                time.sleep(args.poll_ms / 1000.0)
                continue
            state = observe_state(reader)
            current_counter = int(state["enemy_manager_frame"])
            advance = playback.observe(current_counter, int(state["input_current"]))
            output.write(
                json.dumps(
                    {
                        "kind": "verified_frame",
                        "trace_frame": advance.completed_frame_index,
                        "state": state,
                    }
                )
                + "\n"
            )
            output.flush()
            send_transitions(api, advance.transitions)
            counter = current_counter
            last_change = time.perf_counter()
            if advance.finished:
                break
    finally:
        try:
            release_all(api)
        finally:
            output.close()
            reader.close()
    return 0


def command_tap(args: argparse.Namespace) -> int:
    """Send bounded menu key taps after explicit operator arming."""

    if not args.armed:
        raise RuntimeError("physical menu taps require the explicit --armed flag")
    api, reader, _identity = _open_target(args)
    try:
        _require_foreground(api, reader.pid)
        release_injected_keys(api)
        for name in args.keys:
            _require_foreground(api, reader.pid)
            bit = TAP_NAMES[name]
            send_transitions(api, (InputTransition(bit, True),))
            time.sleep(args.hold_ms / 1000.0)
            send_transitions(api, (InputTransition(bit, False),))
            time.sleep(args.gap_ms / 1000.0)
    finally:
        try:
            release_injected_keys(api)
        finally:
            reader.close()
    return 0


def command_release_inputs(args: argparse.Namespace) -> int:
    """Recover from an interrupted controller without touching game memory."""

    if not args.armed:
        raise RuntimeError("physical input release requires the explicit --armed flag")
    api, reader, _identity = _open_target(args)
    try:
        _require_foreground(api, reader.pid)
        release_injected_keys(api)
    finally:
        reader.close()
    return 0


def command_capture_replay_bombs(args: argparse.Namespace) -> int:
    """Capture replay Bomb edges and accepted starts without screen analysis."""

    if args.fast_forward and not args.armed:
        raise RuntimeError("Ctrl fast-forward requires the explicit --armed flag")
    api, reader, identity = _open_target(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    control_held = False
    try:
        initial = observe_state(reader)
        if initial["route_id"] != 2 or not initial["gameplay_active"]:
            raise RuntimeError("capture requires active route-2 gameplay/replay")
        if initial["input_raw"] & SUPPORTED_INPUT_MASK:
            raise RuntimeError("physical gameplay input is already active")
        if args.fast_forward:
            _require_foreground(api, reader.pid)
            send_scan_key(api, scan_code=0x1D, pressed=True)
            control_held = True

        deadline = time.perf_counter() + args.timeout
        previous_counter = int(initial["enemy_manager_frame"])
        previous_input = int(initial["input_current"])
        previous_bomb_active = int(initial["player"]["bomb_active"])
        previous_bombs = initial["resources"]["bombs"] if initial["resources"] else None
        presses = 0
        starts = 0
        gaps = 0
        termination_reason = "timeout"
        with args.output.open("w", encoding="utf-8", newline="\n") as output:
            output.write(json.dumps({"kind": "identity", **identity}) + "\n")
            output.write(json.dumps({"kind": "initial", "state": initial}) + "\n")
            output.flush()
            while time.perf_counter() < deadline:
                if args.fast_forward:
                    _require_foreground(api, reader.pid)
                counter = reader.u32(ADDR_ENEMY_MANAGER_FRAME)
                if counter == previous_counter:
                    time.sleep(args.poll_ms / 1000.0)
                    continue
                state = observe_state(reader)
                counter = int(state["enemy_manager_frame"])
                delta = counter - previous_counter
                if delta != 1:
                    gaps += 1
                if state["route_id"] != 2 or not state["gameplay_active"]:
                    termination_reason = "gameplay_ended"
                    previous_counter = counter
                    break
                current_input = int(state["input_current"])
                bomb_active = int(state["player"]["bomb_active"])
                bombs = state["resources"]["bombs"] if state["resources"] else None
                kinds: list[str] = []
                if current_input & 0x02 and not previous_input & 0x02:
                    kinds.append("bomb_press")
                    presses += 1
                if bomb_active and not previous_bomb_active:
                    kinds.append("bomb_start")
                    starts += 1
                if bombs != previous_bombs:
                    kinds.append("bomb_stock_change")
                if kinds:
                    output.write(
                        json.dumps(
                            {
                                "kind": "event",
                                "events": kinds,
                                "counter_delta": delta,
                                "state": state,
                            }
                        )
                        + "\n"
                    )
                    output.flush()

                previous_counter = counter
                previous_input = current_input
                previous_bomb_active = bomb_active
                previous_bombs = bombs
                if counter >= args.stop_counter or (
                    presses >= args.expected_presses and counter > args.minimum_stop_counter
                ):
                    termination_reason = "target_reached"
                    break

            output.write(
                json.dumps(
                    {
                        "kind": "summary",
                        "presses": presses,
                        "starts": starts,
                        "counter_gaps": gaps,
                        "last_counter": previous_counter,
                        "termination_reason": termination_reason,
                    }
                )
                + "\n"
            )
    finally:
        if control_held:
            release_injected_keys(api)
        reader.close()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pid", type=int)
    subparsers = parser.add_subparsers(dest="command", required=True)

    probe = subparsers.add_parser("probe", help="emit one read-only state snapshot")
    probe.set_defaults(func=command_probe)

    observe = subparsers.add_parser("observe", help="record read-only frame snapshots")
    observe.add_argument("output", type=Path)
    observe.add_argument("--duration", type=float, default=10.0)
    observe.add_argument("--poll-ms", type=float, default=0.5)
    observe.set_defaults(func=command_observe)

    play = subparsers.add_parser("play", help="play one trace through physical keyboard input")
    play.add_argument("trace", type=Path)
    play.add_argument("output", type=Path)
    play.add_argument("--armed", action="store_true")
    play.add_argument("--poll-ms", type=float, default=0.25)
    play.add_argument("--frame-timeout", type=float, default=0.5)
    play.set_defaults(func=command_play)

    tap = subparsers.add_parser(
        "tap", help="send explicitly armed foreground-only menu key taps"
    )
    tap.add_argument("keys", nargs="+", choices=tuple(TAP_NAMES))
    tap.add_argument("--armed", action="store_true")
    tap.add_argument("--hold-ms", type=float, default=50.0)
    tap.add_argument("--gap-ms", type=float, default=100.0)
    tap.set_defaults(func=command_tap)

    release = subparsers.add_parser(
        "release-inputs",
        help="release every key this bridge may have injected",
    )
    release.add_argument("--armed", action="store_true")
    release.set_defaults(func=command_release_inputs)

    capture = subparsers.add_parser(
        "capture-replay-bombs",
        help="capture route-2 replay Bomb edges from read-only runtime state",
    )
    capture.add_argument("output", type=Path)
    capture.add_argument("--fast-forward", action="store_true")
    capture.add_argument("--armed", action="store_true")
    capture.add_argument("--timeout", type=float, default=900.0)
    capture.add_argument("--poll-ms", type=float, default=0.25)
    capture.add_argument("--expected-presses", type=int, default=5)
    capture.add_argument("--minimum-stop-counter", type=int, default=64086)
    capture.add_argument("--stop-counter", type=int, default=66386)
    capture.set_defaults(func=command_capture_replay_bombs)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
