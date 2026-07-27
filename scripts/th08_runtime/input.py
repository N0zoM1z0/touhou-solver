"""Physical TH08 scan-code translation and fail-closed key release."""

from __future__ import annotations

import ctypes

from runtime_agent import InputTransition
from th08_runtime.win32 import (
    INJECTION_MARKER,
    INPUT,
    INPUT_KEYBOARD,
    INPUT_UNION,
    KEYBDINPUT,
    KEYEVENTF_EXTENDEDKEY,
    KEYEVENTF_KEYUP,
    KEYEVENTF_SCANCODE,
    Win32,
    win_error,
)

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


def keyboard_input(transition: InputTransition) -> INPUT:
    try:
        scan_code, extended = SCAN_CODES[transition.bit]
    except KeyError as exc:
        raise ValueError(
            f"no TH08 key mapping for input bit {transition.bit:#x}"
        ) from exc
    return scan_keyboard_input(scan_code, extended, transition.pressed)


def scan_keyboard_input(
    scan_code: int,
    extended: bool,
    pressed: bool,
) -> INPUT:
    flags = KEYEVENTF_SCANCODE
    if extended:
        flags |= KEYEVENTF_EXTENDEDKEY
    if not pressed:
        flags |= KEYEVENTF_KEYUP
    return INPUT(
        INPUT_KEYBOARD,
        INPUT_UNION(
            ki=KEYBDINPUT(0, scan_code, flags, 0, INJECTION_MARKER)
        ),
    )


def send_transitions(
    api: Win32,
    transitions: tuple[InputTransition, ...],
) -> None:
    if not transitions:
        return
    inputs = (INPUT * len(transitions))(
        *(keyboard_input(item) for item in transitions)
    )
    sent = api.user32.SendInput(len(inputs), inputs, ctypes.sizeof(INPUT))
    if sent != len(inputs):
        raise win_error(f"SendInput sent {sent}/{len(inputs)} events")


def release_all(api: Win32) -> None:
    send_transitions(
        api,
        tuple(InputTransition(bit, False) for bit in SCAN_CODES),
    )


def send_scan_key(
    api: Win32,
    *,
    scan_code: int,
    extended: bool = False,
    pressed: bool,
) -> None:
    item = scan_keyboard_input(scan_code, extended, pressed)
    sent = api.user32.SendInput(1, ctypes.byref(item), ctypes.sizeof(INPUT))
    if sent != 1:
        raise win_error("SendInput special scan key")
