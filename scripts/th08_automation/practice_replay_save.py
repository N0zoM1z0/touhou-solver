"""Native-state-guided replay saving after an accepted practice stage."""

from __future__ import annotations

import shutil
import time
from dataclasses import asdict
from pathlib import Path
from typing import Callable

from th08_automation.practice_menu import MenuTap
from th08_automation.practice_windows import drive_menu_plan
from th08_replay import ReplayError, decode_replay
from th08_replay_archive import archive_replay
from th08_runtime_agent import ProcessReader, Win32


UPDATE_CHAIN_HEAD = 0x0164F548
UPDATE_CHAIN_NEXT_OFFSET = 0x14
UPDATE_NODE_CALLBACK_OFFSET = 0x04
UPDATE_NODE_CONTEXT_OFFSET = 0x1C
RESULT_MENU_UPDATE_CALLBACK = 0x004584B0
RESULT_MENU_UPDATE_NODE_OFFSET = 0x46468
REPLAY_SAVE_AGE_OFFSET = 0x04
REPLAY_SAVE_STATE_OFFSET = 0x08
REPLAY_SAVE_CURSOR_OFFSET = 0x1C
REPLAY_SAVE_SELECTED_SLOT_OFFSET = 0x28
REPLAY_SAVE_NAME_GRID_CURSOR_OFFSET = 0x2C
REPLAY_SAVE_NAME_BUFFER_OFFSET = 0x58
REPLAY_SAVE_NAME_LENGTH = 8

REPLAY_SAVE_STATE_PROMPT = 10
REPLAY_SAVE_STATE_SLOT_LIST = 12
REPLAY_SAVE_STATE_NAME = 13
REPLAY_SAVE_STATE_OVERWRITE = 14
REPLAY_SAVE_STATE_DONE = 2
REPLAY_SAVE_SLOT_COUNT = 15
REPLAY_SAVE_NAME_END = 95


def find_replay_save_menu_base(
    api: Win32,
    pid: int,
) -> int:
    """Resolve the heap ResultSysInf object through its registered update node."""

    reader = ProcessReader(api, pid)
    try:
        node = reader.u32(UPDATE_CHAIN_HEAD + UPDATE_CHAIN_NEXT_OFFSET)
        seen: set[int] = set()
        candidates: list[int] = []
        while node:
            if node in seen or len(seen) >= 1024:
                raise RuntimeError("native update chain is cyclic or unbounded")
            seen.add(node)
            callback = reader.u32(node + UPDATE_NODE_CALLBACK_OFFSET)
            if callback == RESULT_MENU_UPDATE_CALLBACK:
                context = reader.u32(node + UPDATE_NODE_CONTEXT_OFFSET)
                if (
                    context >= 0x10000
                    and reader.u32(
                        context + RESULT_MENU_UPDATE_NODE_OFFSET
                    )
                    == node
                    and reader.i32(
                        context + REPLAY_SAVE_STATE_OFFSET
                    )
                    in (
                        REPLAY_SAVE_STATE_PROMPT,
                        11,
                        REPLAY_SAVE_STATE_SLOT_LIST,
                        REPLAY_SAVE_STATE_NAME,
                        REPLAY_SAVE_STATE_OVERWRITE,
                    )
                ):
                    candidates.append(context)
            node = reader.u32(node + UPDATE_CHAIN_NEXT_OFFSET)
        if len(candidates) != 1:
            raise RuntimeError(
                "expected exactly one live ResultSysInf replay-save object; "
                f"found {tuple(hex(candidate) for candidate in candidates)}"
            )
        return candidates[0]
    finally:
        reader.close()


def read_replay_save_menu_state(
    api: Win32,
    pid: int,
    *,
    menu_base: int | None = None,
) -> dict[str, object]:
    base = (
        find_replay_save_menu_base(api, pid)
        if menu_base is None
        else menu_base
    )
    reader = ProcessReader(api, pid)
    try:
        raw_name = reader.read(
            base + REPLAY_SAVE_NAME_BUFFER_OFFSET,
            REPLAY_SAVE_NAME_LENGTH,
        )
        return {
            "menu_base": base,
            "state": reader.i32(
                base + REPLAY_SAVE_STATE_OFFSET
            ),
            "age": reader.i32(
                base + REPLAY_SAVE_AGE_OFFSET
            ),
            "cursor": reader.i32(
                base + REPLAY_SAVE_CURSOR_OFFSET
            ),
            "selected_slot": reader.i32(
                base + REPLAY_SAVE_SELECTED_SLOT_OFFSET
            ),
            "name_grid_cursor": reader.i32(
                base + REPLAY_SAVE_NAME_GRID_CURSOR_OFFSET
            ),
            "name_bytes_hex": raw_name.hex(),
        }
    finally:
        reader.close()


def wait_for_replay_save_state(
    api: Win32,
    pid: int,
    *,
    menu_base: int | None = None,
    states: tuple[int, ...],
    timeout_seconds: float,
    minimum_age: int = 0,
    clock: Callable[[], float] = time.perf_counter,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict[str, object]:
    if not states or any(type(state) is not int for state in states):
        raise ValueError("replay-save states must be an exact nonempty tuple")
    if timeout_seconds <= 0.0 or minimum_age < 0:
        raise ValueError("replay-save wait bounds are invalid")
    deadline = clock() + timeout_seconds
    last: dict[str, object] | None = None
    while clock() < deadline:
        if menu_base is None:
            last = read_replay_save_menu_state(api, pid)
        else:
            last = read_replay_save_menu_state(
                api,
                pid,
                menu_base=menu_base,
            )
        if (
            int(last["state"]) in states
            and int(last["age"]) >= minimum_age
        ):
            return last
        sleeper(0.02)
    raise TimeoutError(
        f"replay-save menu did not reach {states}; last={last}"
    )


def _tap(
    api: Win32,
    pid: int,
    key: str,
    purpose: str,
    *,
    hold_ms: int,
    tap_gap_ms: int,
) -> MenuTap:
    tap = MenuTap(key, purpose, tap_gap_ms)
    drive_menu_plan(api, pid, (tap,), hold_ms=hold_ms)
    return tap


def _navigate_cursor(
    api: Win32,
    pid: int,
    *,
    menu_base: int,
    state_id: int,
    target: int,
    option_count: int,
    hold_ms: int,
    tap_gap_ms: int,
    timeout_seconds: float,
) -> tuple[dict[str, object], tuple[MenuTap, ...]]:
    if not 0 <= target < option_count:
        raise ValueError("replay-save target cursor is out of range")
    state = wait_for_replay_save_state(
        api,
        pid,
        menu_base=menu_base,
        states=(state_id,),
        minimum_age=20,
        timeout_seconds=timeout_seconds,
    )
    taps = []
    for attempt in range(option_count * 3):
        if int(state["cursor"]) == target:
            return state, tuple(taps)
        taps.append(
            _tap(
                api,
                pid,
                "down",
                f"replay-save cursor step {attempt + 1}",
                hold_ms=hold_ms,
                tap_gap_ms=tap_gap_ms,
            )
        )
        state = read_replay_save_menu_state(
            api,
            pid,
            menu_base=menu_base,
        )
        if int(state["state"]) != state_id:
            raise RuntimeError("replay-save navigation changed menu state")
    raise RuntimeError(
        f"replay-save cursor {target} was not reachable; last={state}"
    )


def _navigate_name_end(
    api: Win32,
    pid: int,
    *,
    menu_base: int,
    hold_ms: int,
    tap_gap_ms: int,
    timeout_seconds: float,
) -> tuple[dict[str, object], tuple[MenuTap, ...]]:
    state = wait_for_replay_save_state(
        api,
        pid,
        menu_base=menu_base,
        states=(REPLAY_SAVE_STATE_NAME,),
        minimum_age=30,
        timeout_seconds=timeout_seconds,
    )
    taps = []
    for attempt in range(32):
        cursor = int(state["name_grid_cursor"])
        if cursor == REPLAY_SAVE_NAME_END:
            return state, tuple(taps)
        if not 0 <= cursor <= REPLAY_SAVE_NAME_END:
            raise RuntimeError(
                f"invalid replay-save name cursor {cursor}"
            )
        key = "down" if cursor // 16 < 5 else "right"
        taps.append(
            _tap(
                api,
                pid,
                key,
                f"replay-save name End step {attempt + 1}",
                hold_ms=hold_ms,
                tap_gap_ms=tap_gap_ms,
            )
        )
        state = read_replay_save_menu_state(
            api,
            pid,
            menu_base=menu_base,
        )
        if int(state["state"]) != REPLAY_SAVE_STATE_NAME:
            raise RuntimeError("replay name navigation left name state")
    raise RuntimeError("replay-save name End was not reachable")


def _validate_saved_replay(
    path: Path,
    *,
    expected_route_id: int,
    expected_difficulty_index: int,
    expected_stage_route_index: int,
) -> dict[str, object]:
    metadata, _decoded = decode_replay(path)
    if metadata.route_id != expected_route_id:
        raise RuntimeError("saved replay route identity mismatch")
    if metadata.difficulty_index != expected_difficulty_index:
        raise RuntimeError("saved replay difficulty identity mismatch")
    if tuple(stage.stage_index for stage in metadata.stages) != (
        expected_stage_route_index,
    ):
        raise RuntimeError("saved practice replay stage identity mismatch")
    stage = metadata.stages[0]
    if stage.bomb_press_frames:
        raise RuntimeError("saved replay contains a Bomb press")
    return asdict(metadata)


def _restore_replay_after_failed_write(
    replay_path: Path,
    previous_archive: dict[str, object] | None,
) -> str:
    if previous_archive is None:
        replay_path.unlink(missing_ok=True)
        return "invalid_new_slot_removed"
    archived_path = Path(str(previous_archive["archive"]))
    archived_metadata = previous_archive.get("metadata")
    if not isinstance(archived_metadata, dict):
        raise RuntimeError("previous replay archive metadata is malformed")
    expected_sha256 = str(archived_metadata["sha256"])
    shutil.copy2(archived_path, replay_path)
    restored_metadata, _ = decode_replay(replay_path)
    if restored_metadata.sha256 != expected_sha256:
        raise RuntimeError(
            "saved replay validation failed and archived slot restoration "
            "did not preserve identity"
        )
    return f"previous replay restored from {archived_path.as_posix()}"


def save_completed_practice_replay(
    api: Win32,
    pid: int,
    *,
    game_dir: Path,
    slot: int,
    archive_dir: Path,
    expected_route_id: int,
    expected_difficulty_index: int,
    expected_stage_route_index: int,
    hold_ms: int,
    tap_gap_ms: int,
    timeout_seconds: float,
) -> dict[str, object]:
    """Save one accepted practice replay and retain both slot generations."""

    if not 1 <= slot <= REPLAY_SAVE_SLOT_COUNT:
        raise ValueError("replay save slot must be in 1..15")
    replay_path = game_dir / "replay" / f"th8_{slot:02d}.rpy"
    previous_archive = (
        archive_replay(replay_path, archive_dir)
        if replay_path.is_file()
        else None
    )
    previous_mtime_ns = (
        replay_path.stat().st_mtime_ns if replay_path.is_file() else None
    )
    trace: list[dict[str, object]] = []
    menu_base = find_replay_save_menu_base(api, pid)
    trace.append(
        {
            "label": "result_menu_object_resolved",
            "menu_base": menu_base,
            "evidence": (
                "update-chain callback 0x004584B0, node context +0x1C, "
                "and ResultSysInf node back-reference +0x46468"
            ),
        }
    )

    state, taps = _navigate_cursor(
        api,
        pid,
        menu_base=menu_base,
        state_id=REPLAY_SAVE_STATE_PROMPT,
        target=0,
        option_count=2,
        hold_ms=hold_ms,
        tap_gap_ms=tap_gap_ms,
        timeout_seconds=timeout_seconds,
    )
    trace.append(
        {
            "label": "save_yes_selected",
            "state": state,
            "taps": [asdict(tap) for tap in taps],
        }
    )
    tap = _tap(
        api,
        pid,
        "confirm",
        "enter replay slot list",
        hold_ms=hold_ms,
        tap_gap_ms=tap_gap_ms,
    )
    state = wait_for_replay_save_state(
        api,
        pid,
        menu_base=menu_base,
        states=(REPLAY_SAVE_STATE_SLOT_LIST,),
        minimum_age=20,
        timeout_seconds=timeout_seconds,
    )
    trace.append(
        {
            "label": "slot_list_entered",
            "state": state,
            "taps": [asdict(tap)],
        }
    )

    state, taps = _navigate_cursor(
        api,
        pid,
        menu_base=menu_base,
        state_id=REPLAY_SAVE_STATE_SLOT_LIST,
        target=slot - 1,
        option_count=REPLAY_SAVE_SLOT_COUNT,
        hold_ms=hold_ms,
        tap_gap_ms=tap_gap_ms,
        timeout_seconds=timeout_seconds,
    )
    trace.append(
        {
            "label": "target_slot_selected",
            "state": state,
            "taps": [asdict(tap) for tap in taps],
        }
    )
    tap = _tap(
        api,
        pid,
        "confirm",
        f"open replay save slot {slot}",
        hold_ms=hold_ms,
        tap_gap_ms=tap_gap_ms,
    )
    state = wait_for_replay_save_state(
        api,
        pid,
        menu_base=menu_base,
        states=(REPLAY_SAVE_STATE_NAME, REPLAY_SAVE_STATE_OVERWRITE),
        timeout_seconds=timeout_seconds,
    )
    trace.append(
        {
            "label": "slot_opened",
            "state": state,
            "taps": [asdict(tap)],
        }
    )
    if int(state["state"]) == REPLAY_SAVE_STATE_OVERWRITE:
        state, taps = _navigate_cursor(
            api,
            pid,
            menu_base=menu_base,
            state_id=REPLAY_SAVE_STATE_OVERWRITE,
            target=0,
            option_count=2,
            hold_ms=hold_ms,
            tap_gap_ms=tap_gap_ms,
            timeout_seconds=timeout_seconds,
        )
        trace.append(
            {
                "label": "overwrite_yes_selected",
                "state": state,
                "taps": [asdict(tap) for tap in taps],
            }
        )
        tap = _tap(
            api,
            pid,
            "confirm",
            f"confirm replay slot {slot} overwrite",
            hold_ms=hold_ms,
            tap_gap_ms=tap_gap_ms,
        )
        state = wait_for_replay_save_state(
            api,
            pid,
            menu_base=menu_base,
            states=(REPLAY_SAVE_STATE_NAME,),
            minimum_age=30,
            timeout_seconds=timeout_seconds,
        )
        trace.append(
            {
                "label": "overwrite_confirmed",
                "state": state,
                "taps": [asdict(tap)],
            }
        )

    state, taps = _navigate_name_end(
        api,
        pid,
        menu_base=menu_base,
        hold_ms=hold_ms,
        tap_gap_ms=tap_gap_ms,
        timeout_seconds=timeout_seconds,
    )
    trace.append(
        {
            "label": "name_end_selected",
            "state": state,
            "taps": [asdict(tap) for tap in taps],
        }
    )
    tap = _tap(
        api,
        pid,
        "confirm",
        f"write replay slot {slot}",
        hold_ms=hold_ms,
        tap_gap_ms=tap_gap_ms,
    )

    deadline = time.perf_counter() + timeout_seconds
    metadata_record: dict[str, object] | None = None
    last_error: Exception | None = None
    while time.perf_counter() < deadline:
        try:
            if not replay_path.is_file():
                raise FileNotFoundError(replay_path)
            if (
                previous_mtime_ns is not None
                and replay_path.stat().st_mtime_ns == previous_mtime_ns
            ):
                raise RuntimeError("replay slot mtime has not changed")
            metadata_record = _validate_saved_replay(
                replay_path,
                expected_route_id=expected_route_id,
                expected_difficulty_index=expected_difficulty_index,
                expected_stage_route_index=expected_stage_route_index,
            )
            break
        except (OSError, ReplayError, RuntimeError) as exc:
            last_error = exc
            time.sleep(0.05)
    if metadata_record is None:
        restore_status = _restore_replay_after_failed_write(
            replay_path,
            previous_archive,
        )
        raise RuntimeError(
            "saved replay did not pass identity validation; "
            f"{restore_status}: {last_error}"
        )
    try:
        final_state: dict[str, object] = read_replay_save_menu_state(
            api,
            pid,
            menu_base=menu_base,
        )
    except OSError as exc:
        final_state = {
            "state": "unavailable_after_verified_write",
            "error": str(exc),
        }
    trace.append(
        {
            "label": "replay_write_verified",
            "state": final_state,
            "taps": [asdict(tap)],
        }
    )
    current_archive = archive_replay(replay_path, archive_dir)
    return {
        "schema": "th08-accepted-practice-replay-save-v1",
        "slot": slot,
        "path": replay_path.as_posix(),
        "previous_archive": previous_archive,
        "saved_metadata": metadata_record,
        "current_archive": current_archive,
        "native_menu_trace": trace,
    }


__all__ = [
    "REPLAY_SAVE_STATE_NAME",
    "REPLAY_SAVE_STATE_OVERWRITE",
    "REPLAY_SAVE_STATE_PROMPT",
    "REPLAY_SAVE_STATE_SLOT_LIST",
    "find_replay_save_menu_base",
    "read_replay_save_menu_state",
    "save_completed_practice_replay",
    "wait_for_replay_save_state",
]
