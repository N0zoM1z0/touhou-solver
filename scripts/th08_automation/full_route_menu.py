"""Native-state menu operations for continuous TH08 Route-2 trials."""

from __future__ import annotations

from collections.abc import Callable

from th08_automation.practice_menu import MenuTap, PracticeDifficulty
from th08_runtime_agent import Win32


TITLE_MODE_GAME_DIFFICULTY = 4
TITLE_MODE_GAME_TEAM = 5


def anchor_game_start(
    api: Win32,
    pid: int,
    *,
    hold_ms: int,
    tap_gap_ms: int,
    drive_plan: Callable[..., None],
    read_state: Callable[[Win32, int], dict[str, int]],
    title_mode_main: int,
) -> tuple[dict[str, int], tuple[MenuTap, ...]]:
    """Force a real native cursor transition before accepting the top entry."""

    taps = (
        MenuTap(
            "down",
            "leave possibly stale Game Start selection",
            tap_gap_ms,
        ),
        MenuTap("up", "return to Game Start", tap_gap_ms),
    )
    drive_plan(api, pid, taps, hold_ms=hold_ms)
    state = read_state(api, pid)
    if (
        state["mode"] != title_mode_main
        or state["substate"] != 1
        or state["cursor"] != 0
    ):
        raise RuntimeError(f"failed to anchor Game Start selection: {state}")
    return state, taps


def confirm_title_mode(
    api: Win32,
    pid: int,
    *,
    next_mode: int,
    purpose: str,
    hold_ms: int,
    screen_settle_ms: int,
    timeout_seconds: float,
    drive_plan: Callable[..., None],
    wait_for_menu: Callable[..., dict[str, int]],
) -> MenuTap:
    tap = MenuTap("confirm", purpose, screen_settle_ms)
    drive_plan(api, pid, (tap,), hold_ms=hold_ms)
    wait_for_menu(
        api,
        pid,
        mode=next_mode,
        timeout_seconds=timeout_seconds,
    )
    return tap


def validate_team_selection(
    api: Win32,
    pid: int,
    *,
    difficulty: PracticeDifficulty,
    read_state: Callable[[Win32, int], dict[str, int]],
) -> dict[str, int]:
    state = read_state(api, pid)
    if (
        state["mode"] != TITLE_MODE_GAME_TEAM
        or state["substate"] != 1
        or state["cursor"] != 2
        or state["difficulty_cursor"] != difficulty.menu_index
    ):
        raise RuntimeError(
            "native full-route selection mismatch before final confirm: "
            f"mode={state['mode']} substate={state['substate']} "
            f"cursor={state['cursor']} "
            f"difficulty_cursor={state['difficulty_cursor']} "
            f"expected_difficulty_cursor={difficulty.menu_index}"
        )
    return state


def retain_game_after_trial(
    *,
    accepted: bool,
    leave_game_running: bool,
) -> bool:
    """Only an explicitly requested accepted route may survive cleanup."""

    return accepted and leave_game_running
