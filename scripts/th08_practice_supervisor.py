#!/usr/bin/env python3
"""Launch, navigate, run, archive, and recycle original TH08 Practice Start."""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import shutil
import subprocess
import sys
import time
from ctypes import wintypes
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from runtime_agent import InputTransition
from th08_agent_hotkey import AgentHotkey
from th08_automation.practice_menu import (
    MenuTap,
    PracticeStage,
    build_practice_menu_plan,
    parse_practice_stage,
)
from analysis.th08_practice_compare import compare_dossiers
from analysis.th08_practice_dossier import main as build_practice_dossier
from th08_runtime_agent import (
    ADDR_DIFFICULTY_INDEX,
    ADDR_NO_LIFE_DECREMENT_PATCH,
    ADDR_ROUTE_ID,
    ADDR_STAGE_ROUTE_INDEX,
    TARGET_EXE,
    TAP_NAMES,
    ProcessReader,
    Win32,
    _require_foreground,
    release_injected_keys,
    send_scan_key,
    send_transitions,
    verify_target,
)


ROOT = Path(__file__).resolve().parent.parent
RUNTIME_REPORT_DIR = ROOT / "artifacts" / "runtime_reports"
RUN_NOTE_DIR = ROOT / "notes" / "runs"
DEFAULT_GAME_DIR = (
    Path("D:/Entertainment/Game/Touhou")
    / "[th08] \u4e1c\u65b9\u6c38\u591c\u6284 (\u65e5\u6587\u7248)"
)
DEFAULT_LAUNCH_BAT = "run_th08_no_life_decrement_attach.bat"

ADDR_TITLE_MENU_MANAGER = 0x018BDE08
ADDR_TITLE_DIFFICULTY_CURSOR = 0x017CE891
ADDR_PRACTICE_STAGE_AVAILABILITY = 0x0164B9AE
TITLE_CURSOR_OFFSET = 0
TITLE_SUBSTATE_OFFSET = 12
TITLE_MODE_OFFSET = 82_984
TITLE_SCREEN_AGE_OFFSET = 82_988
TITLE_MODE_MAIN = 0
TITLE_MODE_PRACTICE_DIFFICULTY = 8
TITLE_MODE_PRACTICE_TEAM = 9
TITLE_MODE_PRACTICE_STAGE = 11

VK_CAPITAL = 0x14
SW_RESTORE = 9
PROCESS_TERMINATE = 0x0001
SYNCHRONIZE = 0x00100000
WAIT_OBJECT_0 = 0
CREATE_NO_WINDOW = 0x08000000
WNDENUMPROC = getattr(ctypes, "WINFUNCTYPE", ctypes.CFUNCTYPE)(
    wintypes.BOOL,
    wintypes.HWND,
    wintypes.LPARAM,
)


@dataclass(frozen=True)
class TrialArtifacts:
    run_id: str
    trace: Path
    summary: Path
    dossier_json: Path
    dossier_markdown: Path
    death_csv: Path
    regressions_json: Path
    comparison_json: Path | None
    run_note: Path
    session_json: Path


def _same_path(left: Path, right: Path) -> bool:
    return os.path.normcase(str(left.resolve())) == os.path.normcase(
        str(right.resolve())
    )


def _configure_supervisor_api(api: Win32) -> None:
    api.user32.GetKeyState.argtypes = [ctypes.c_int]
    api.user32.GetKeyState.restype = ctypes.c_short
    api.user32.EnumWindows.argtypes = [WNDENUMPROC, wintypes.LPARAM]
    api.user32.EnumWindows.restype = wintypes.BOOL
    api.user32.IsWindowVisible.argtypes = [wintypes.HWND]
    api.user32.IsWindowVisible.restype = wintypes.BOOL
    api.user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    api.user32.ShowWindow.restype = wintypes.BOOL
    api.user32.BringWindowToTop.argtypes = [wintypes.HWND]
    api.user32.BringWindowToTop.restype = wintypes.BOOL
    api.kernel32.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
    api.kernel32.TerminateProcess.restype = wintypes.BOOL
    api.kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    api.kernel32.WaitForSingleObject.restype = wintypes.DWORD


def caps_lock_enabled(api: Win32) -> bool:
    return bool(api.user32.GetKeyState(VK_CAPITAL) & 1)


def ensure_caps_lock_enabled(api: Win32) -> bool:
    """Enable and verify Caps Lock without depending on the active IME."""

    if caps_lock_enabled(api):
        return False
    send_scan_key(api, scan_code=0x3A, pressed=True)
    send_scan_key(api, scan_code=0x3A, pressed=False)
    time.sleep(0.08)
    if not caps_lock_enabled(api):
        raise RuntimeError("Caps Lock did not become enabled")
    return True


def _matching_targets(
    api: Win32,
    expected_exe: Path,
) -> list[tuple[int, dict[str, object]]]:
    matches: list[tuple[int, dict[str, object]]] = []
    for pid in api.find_pids(TARGET_EXE):
        reader = ProcessReader(api, pid)
        try:
            identity = verify_target(reader)
            if _same_path(Path(str(identity["image_path"])), expected_exe):
                matches.append((pid, identity))
        finally:
            reader.close()
    return matches


def terminate_exact_target(api: Win32, expected_exe: Path) -> bool:
    matches = _matching_targets(api, expected_exe)
    if not matches:
        return False
    if len(matches) != 1:
        raise RuntimeError(
            "refusing to terminate ambiguous exact TH08 targets: "
            + ", ".join(str(pid) for pid, _identity in matches)
        )
    pid, _identity = matches[0]
    release_injected_keys(api)
    handle = api.kernel32.OpenProcess(PROCESS_TERMINATE | SYNCHRONIZE, False, pid)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error(), "OpenProcess terminate")
    try:
        if not api.kernel32.TerminateProcess(handle, 0):
            raise ctypes.WinError(ctypes.get_last_error(), "TerminateProcess")
        wait_result = api.kernel32.WaitForSingleObject(handle, 10_000)
        if wait_result != WAIT_OBJECT_0:
            raise RuntimeError(f"TH08 process {pid} did not terminate")
    finally:
        api.kernel32.CloseHandle(handle)
    return True


def launch_patch_batch(
    *,
    game_dir: Path,
    launch_bat: Path,
    log_path: Path,
) -> tuple[subprocess.Popen[bytes], object]:
    if not launch_bat.is_file():
        raise FileNotFoundError(f"launch batch does not exist: {launch_bat}")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = log_path.open("wb")
    try:
        process = subprocess.Popen(
            build_patch_batch_command(launch_bat),
            cwd=game_dir,
            stdin=subprocess.DEVNULL,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            creationflags=CREATE_NO_WINDOW,
        )
    except Exception:
        log_file.close()
        raise
    return process, log_file


def build_patch_batch_command(launch_bat: Path) -> tuple[str, ...]:
    """Keep CALL and its path as separate argv items for cmd.exe quoting."""

    return (
        os.environ.get("COMSPEC", "cmd.exe"),
        "/d",
        "/c",
        "call",
        str(launch_bat),
    )


def wait_for_patched_target(
    api: Win32,
    *,
    expected_exe: Path,
    timeout_seconds: float,
) -> tuple[int, dict[str, object]]:
    deadline = time.perf_counter() + timeout_seconds
    reader: ProcessReader | None = None
    identity: dict[str, object] | None = None
    try:
        while time.perf_counter() < deadline and reader is None:
            matches = _matching_targets(api, expected_exe)
            if len(matches) > 1:
                raise RuntimeError("multiple exact TH08 targets appeared after launch")
            if matches:
                pid, identity = matches[0]
                reader = ProcessReader(api, pid)
                break
            time.sleep(0.1)
        if reader is None or identity is None:
            raise TimeoutError("timed out waiting for the exact TH08 executable")
        while time.perf_counter() < deadline:
            if reader.u8(ADDR_NO_LIFE_DECREMENT_PATCH) == 0:
                return reader.pid, verify_target(reader)
            time.sleep(0.05)
        raise TimeoutError("timed out waiting for the no-life-decrement patch")
    finally:
        if reader is not None:
            reader.close()


def _target_windows(api: Win32, pid: int) -> tuple[int, ...]:
    windows: list[int] = []

    @WNDENUMPROC
    def callback(window: int, _parameter: int) -> bool:
        owner = wintypes.DWORD()
        api.user32.GetWindowThreadProcessId(window, ctypes.byref(owner))
        if owner.value == pid and api.user32.IsWindowVisible(window):
            windows.append(int(window))
        return True

    if not api.user32.EnumWindows(callback, 0):
        raise ctypes.WinError(ctypes.get_last_error(), "EnumWindows")
    return tuple(windows)


def focus_target_window(
    api: Win32,
    pid: int,
    *,
    timeout_seconds: float,
) -> int:
    deadline = time.perf_counter() + timeout_seconds
    last_windows: tuple[int, ...] = ()
    while time.perf_counter() < deadline:
        last_windows = _target_windows(api, pid)
        for window in last_windows:
            api.user32.ShowWindow(window, SW_RESTORE)
            api.user32.BringWindowToTop(window)
            api.user32.SetForegroundWindow(window)
            if api.foreground_pid() == pid:
                return window
        time.sleep(0.1)
    raise RuntimeError(
        f"could not acquire TH08 foreground ownership; windows={last_windows}"
    )


def drive_menu_plan(
    api: Win32,
    pid: int,
    plan: tuple[MenuTap, ...],
    *,
    hold_ms: int,
) -> None:
    if hold_ms <= 0:
        raise ValueError("menu hold time must be positive")
    _require_foreground(api, pid)
    release_injected_keys(api)
    for tap in plan:
        _require_foreground(api, pid)
        bit = TAP_NAMES[tap.key]
        send_transitions(api, (InputTransition(bit, True),))
        time.sleep(hold_ms / 1000.0)
        send_transitions(api, (InputTransition(bit, False),))
        time.sleep(tap.wait_after_ms / 1000.0)


def read_last_json_record(path: Path) -> dict[str, object] | None:
    if not path.is_file() or path.stat().st_size == 0:
        return None
    with path.open("rb") as source:
        source.seek(0, os.SEEK_END)
        position = source.tell()
        suffix = b""
        while position > 0:
            size = min(64 * 1024, position)
            position -= size
            source.seek(position)
            suffix = source.read(size) + suffix
            lines = [line for line in suffix.splitlines() if line.strip()]
            if len(lines) >= 2 or position == 0:
                for line in reversed(lines):
                    try:
                        return json.loads(line)
                    except json.JSONDecodeError:
                        continue
                return None
    return None


def _progress_text(record: dict[str, object] | None) -> str:
    if not record:
        return "waiting for trace output"
    spell_id = record.get("spell_id")
    spell = record.get("spell")
    if (
        spell_id is None
        and isinstance(spell, dict)
        and spell.get("active")
    ):
        spell_id = spell.get("spell_id")
    return (
        f"kind={record.get('kind')} frame={record.get('frame')} "
        f"stage={record.get('stage_route_index')} "
        f"spell={spell_id} hits={record.get('hit_count')} "
        f"bullets={record.get('active_bullets')} "
        f"lasers={record.get('active_lasers')}"
    )


def monitor_trial(
    agent: AgentHotkey,
    *,
    trace: Path,
    timeout_seconds: float,
    status_seconds: float,
    stall_timeout_seconds: float,
) -> Path:
    if agent.agent_thread is None:
        raise RuntimeError("agent was not started")
    deadline = time.perf_counter() + timeout_seconds
    last_trace_mtime = 0
    last_progress_at = time.perf_counter()
    while agent.agent_thread.is_alive():
        if trace.is_file():
            trace_mtime = trace.stat().st_mtime_ns
            if trace_mtime != last_trace_mtime:
                last_trace_mtime = trace_mtime
                last_progress_at = time.perf_counter()
        if time.perf_counter() - last_progress_at >= stall_timeout_seconds:
            agent.stop()
            agent.agent_thread.join(timeout=15.0)
            raise TimeoutError(
                "unattended practice trace made no progress for "
                f"{stall_timeout_seconds:.1f} seconds"
            )
        remaining = deadline - time.perf_counter()
        if remaining <= 0.0:
            agent.stop()
            agent.agent_thread.join(timeout=15.0)
            raise TimeoutError("unattended practice trial exceeded its timeout")
        agent.agent_thread.join(timeout=min(status_seconds, remaining))
        print("trial status:", _progress_text(read_last_json_record(trace)), flush=True)
    return agent.wait_for_trial()


def accepted_practice_termination(
    summary: dict[str, object] | None,
) -> bool:
    return (
        isinstance(summary, dict)
        and summary.get("termination_reason") == "route_complete"
    )


def select_no_save_before_termination(
    api: Win32,
    pid: int,
    *,
    hold_ms: int,
    tap_gap_ms: int,
) -> dict[str, object]:
    """Move the completed-stage save prompt to No; cleanup kills immediately."""

    result: dict[str, object] = {"attempted": True, "key": "right"}
    try:
        focus_target_window(api, pid, timeout_seconds=1.0)
        tap = MenuTap("right", "post-stage do not save", tap_gap_ms)
        drive_menu_plan(api, pid, (tap,), hold_ms=hold_ms)
        result["sent"] = True
    except (OSError, RuntimeError, TimeoutError) as exc:
        result["sent"] = False
        result["error"] = str(exc)
    return result


def _previous_dossier(
    stage: PracticeStage,
    current: Path,
) -> Path | None:
    def accepted_session(dossier: Path) -> bool:
        suffix = ".dossier.json"
        if not dossier.name.endswith(suffix):
            return False
        session_path = dossier.with_name(
            dossier.name[: -len(suffix)] + ".session.json"
        )
        try:
            session = json.loads(session_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return False
        if session.get("status") != "completed":
            return False
        if session.get("trial_accepted") is not None:
            return session.get("trial_accepted") is True
        summary = session.get("agent_summary")
        return accepted_practice_termination(
            summary if isinstance(summary, dict) else None
        )

    candidates = sorted(
        RUNTIME_REPORT_DIR.glob(
            f"lunatic_route2_stage{stage.key}_unattended_*.dossier.json"
        ),
        key=lambda path: path.stat().st_mtime_ns,
        reverse=True,
    )
    return next(
        (
            path
            for path in candidates
            if path != current and accepted_session(path)
        ),
        None,
    )


def materialize_artifacts(
    *,
    run_id: str,
    stage: PracticeStage,
    trace: Path,
    session_json: Path,
) -> TrialArtifacts:
    prefix = RUNTIME_REPORT_DIR / run_id
    dossier_json = prefix.with_suffix(".dossier.json")
    dossier_markdown = prefix.with_suffix(".dossier.md")
    death_csv = prefix.with_suffix(".deaths.csv")
    regressions_json = prefix.with_suffix(".regressions.json")
    build_practice_dossier(
        [
            "--run-id",
            run_id,
            "--trace",
            str(trace),
            "--json-output",
            str(dossier_json),
            "--markdown-output",
            str(dossier_markdown),
            "--death-csv",
            str(death_csv),
            "--regression-output",
            str(regressions_json),
        ]
    )
    comparison_json = None
    baseline = _previous_dossier(stage, dossier_json)
    if baseline is not None:
        comparison_json = prefix.with_suffix(".comparison.json")
        before = json.loads(baseline.read_text(encoding="utf-8"))
        after = json.loads(dossier_json.read_text(encoding="utf-8"))
        comparison_json.write_text(
            json.dumps(
                compare_dossiers(before, after),
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
    RUN_NOTE_DIR.mkdir(parents=True, exist_ok=True)
    run_note = RUN_NOTE_DIR / f"{run_id}.md"
    shutil.copyfile(dossier_markdown, run_note)
    return TrialArtifacts(
        run_id=run_id,
        trace=trace,
        summary=trace.with_suffix(".summary.json"),
        dossier_json=dossier_json,
        dossier_markdown=dossier_markdown,
        death_csv=death_csv,
        regressions_json=regressions_json,
        comparison_json=comparison_json,
        run_note=run_note,
        session_json=session_json,
    )


def _read_menu_selection(api: Win32, pid: int) -> dict[str, int]:
    reader = ProcessReader(api, pid)
    try:
        difficulty = reader.u32(ADDR_DIFFICULTY_INDEX)
        route = reader.u8(ADDR_ROUTE_ID)
    finally:
        reader.close()
    return {"difficulty_index": difficulty, "route_id": route}


def _read_title_menu_state(api: Win32, pid: int) -> dict[str, int]:
    reader = ProcessReader(api, pid)
    try:
        manager = reader.u32(ADDR_TITLE_MENU_MANAGER)
        if not manager:
            raise RuntimeError("title menu manager is not allocated")
        difficulty_cursor = reader.u8(ADDR_TITLE_DIFFICULTY_CURSOR)
        route_id = reader.u8(ADDR_ROUTE_ID)
        return {
            "manager": manager,
            "mode": reader.u32(manager + TITLE_MODE_OFFSET),
            "substate": reader.u32(manager + TITLE_SUBSTATE_OFFSET),
            "screen_age": reader.u32(manager + TITLE_SCREEN_AGE_OFFSET),
            "cursor": reader.u32(manager + TITLE_CURSOR_OFFSET),
            "difficulty_cursor": difficulty_cursor,
            "difficulty_index": reader.u32(ADDR_DIFFICULTY_INDEX),
            "route_id": route_id,
            "stage_route_index": reader.u32(ADDR_STAGE_ROUTE_INDEX),
            "practice_stage_availability_mask": reader.u16(
                ADDR_PRACTICE_STAGE_AVAILABILITY
                + 2 * (18 * route_id + difficulty_cursor)
            ),
        }
    finally:
        reader.close()


def wait_for_title_menu(
    api: Win32,
    pid: int,
    *,
    mode: int,
    timeout_seconds: float,
) -> dict[str, int]:
    deadline = time.perf_counter() + timeout_seconds
    last: dict[str, int] | None = None
    while time.perf_counter() < deadline:
        last = _read_title_menu_state(api, pid)
        if last["mode"] == mode and last["substate"] == 1:
            return last
        time.sleep(0.02)
    raise TimeoutError(
        f"title menu mode {mode} did not become interactive; last={last}"
    )


def practice_stage_available(mask: int, stage_index: int) -> bool:
    return bool(mask & (1 << stage_index))


def _navigate_title_cursor(
    api: Win32,
    pid: int,
    *,
    mode: int,
    target: int,
    option_count: int,
    purpose: str,
    hold_ms: int,
    tap_gap_ms: int,
    timeout_seconds: float,
    direction_key: str = "down",
) -> tuple[dict[str, int], tuple[MenuTap, ...]]:
    state = wait_for_title_menu(
        api,
        pid,
        mode=mode,
        timeout_seconds=timeout_seconds,
    )
    if not 0 <= target < option_count:
        raise ValueError(f"target cursor {target} outside menu option count")
    if (
        mode == TITLE_MODE_PRACTICE_STAGE
        and not practice_stage_available(
            state["practice_stage_availability_mask"],
            target,
        )
    ):
        raise RuntimeError(
            f"title cursor {target} is disabled in mode {mode}; "
            "practice_stage_availability_mask="
            f"0x{state['practice_stage_availability_mask']:04X} "
            f"state={state}"
        )
    taps: list[MenuTap] = []
    visited = [state["cursor"]]
    deadline = time.perf_counter() + timeout_seconds
    max_attempts = option_count * 3
    for attempt in range(max_attempts):
        if state["cursor"] == target:
            return state, tuple(taps)
        tap = MenuTap(
            direction_key,
            f"{purpose} feedback step {attempt + 1}",
            tap_gap_ms,
        )
        drive_menu_plan(api, pid, (tap,), hold_ms=hold_ms)
        taps.append(tap)
        state = _read_title_menu_state(api, pid)
        visited.append(state["cursor"])
        if (
            state["mode"] == mode
            and state["substate"] == 1
            and state["cursor"] == target
        ):
            return state, tuple(taps)
        if time.perf_counter() >= deadline:
            break
    raise RuntimeError(
        f"title cursor {target} is not reachable in mode {mode}; "
        f"visited={visited} last={state}"
    )


def _confirm_title_menu(
    api: Win32,
    pid: int,
    *,
    next_mode: int,
    purpose: str,
    hold_ms: int,
    screen_settle_ms: int,
    timeout_seconds: float,
) -> MenuTap:
    tap = MenuTap("confirm", purpose, screen_settle_ms)
    drive_menu_plan(api, pid, (tap,), hold_ms=hold_ms)
    wait_for_title_menu(
        api,
        pid,
        mode=next_mode,
        timeout_seconds=timeout_seconds,
    )
    return tap


def _validate_practice_selection(
    api: Win32,
    pid: int,
    *,
    stage: PracticeStage,
) -> dict[str, int]:
    state = _read_title_menu_state(api, pid)
    if (
        state["mode"] != TITLE_MODE_PRACTICE_STAGE
        or state["substate"] != 1
        or state["cursor"] != stage.menu_index
        or state["difficulty_cursor"] != 3
        or state["route_id"] != 2
    ):
        raise RuntimeError(
            "native Practice selection mismatch before final confirm: "
            f"mode={state['mode']} substate={state['substate']} "
            f"cursor={state['cursor']} difficulty_cursor="
            f"{state['difficulty_cursor']} route={state['route_id']}"
        )
    return state


def _stop_batch_process(process: subprocess.Popen[bytes] | None) -> None:
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5.0)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5.0)


def run_trial(
    args: argparse.Namespace,
    *,
    api: Win32,
    stage: PracticeStage,
    iteration: int,
) -> TrialArtifacts:
    game_dir = args.game_dir.resolve()
    expected_exe = game_dir / TARGET_EXE
    launch_bat = args.launch_bat or game_dir / DEFAULT_LAUNCH_BAT
    if args.kill_existing:
        if terminate_exact_target(api, expected_exe):
            print("terminated previous verified TH08 process", flush=True)
    elif _matching_targets(api, expected_exe):
        raise RuntimeError("verified TH08 is already running")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = f"lunatic_route2_stage{stage.key}_unattended_{timestamp}"
    trace = RUNTIME_REPORT_DIR / f"{run_id}.jsonl"
    session_json = RUNTIME_REPORT_DIR / f"{run_id}.session.json"
    launch_log = RUNTIME_REPORT_DIR / f"{run_id}.launch.log"
    menu_plan = build_practice_menu_plan(
        stage,
        tap_gap_ms=args.tap_gap_ms,
        screen_settle_ms=args.screen_settle_ms,
    )
    session: dict[str, object] = {
        "schema": "th08-unattended-practice-session-v1",
        "run_id": run_id,
        "iteration": iteration,
        "stage": asdict(stage),
        "game_dir": str(game_dir),
        "launch_bat": str(launch_bat),
        "menu_plan": [asdict(tap) for tap in menu_plan],
        "hard_no_bomb": True,
        "trace_transform_runtime": args.trace_transform_runtime,
        "viability_audit": args.viability_audit,
        "postpublished_survival_shadow": (
            args.postpublished_survival_shadow
        ),
        "pipeline_prewarm_shadow": args.pipeline_prewarm_shadow,
        "candidate_verifier_shadow": (
            args.candidate_verifier_shadow
        ),
        "input_clock_boundary_shadow": (
            args.input_clock_boundary_shadow
        ),
        "input_clock_shadow_sample_ms": (
            args.input_clock_shadow_sample_ms
        ),
        "started_at": datetime.now().astimezone().isoformat(),
    }
    batch_process: subprocess.Popen[bytes] | None = None
    batch_log = None
    agent: AgentHotkey | None = None
    try:
        session["caps_lock_changed"] = ensure_caps_lock_enabled(api)
        agent = AgentHotkey(
            expected_stage=stage.route_index,
            terminal_stage=stage.route_index,
            trace_transform_runtime=args.trace_transform_runtime,
            safety_value_horizon=args.safety_value_horizon,
            viability_audit_dir=(
                ROOT
                / "artifacts"
                / "viability_audit"
                / "raw"
                / run_id
                if args.viability_audit
                else None
            ),
            postpublished_survival_shadow=(
                args.postpublished_survival_shadow
            ),
            pipeline_prewarm_shadow=args.pipeline_prewarm_shadow,
            candidate_verifier_shadow=(
                args.candidate_verifier_shadow
            ),
            input_clock_boundary_shadow=(
                args.input_clock_boundary_shadow
            ),
            input_clock_shadow_sample_ms=(
                args.input_clock_shadow_sample_ms
            ),
        )
        batch_process, batch_log = launch_patch_batch(
            game_dir=game_dir,
            launch_bat=launch_bat,
            log_path=launch_log,
        )
        pid, identity = wait_for_patched_target(
            api,
            expected_exe=expected_exe,
            timeout_seconds=args.launch_timeout,
        )
        session["target"] = identity
        session["pid"] = pid
        focus_target_window(api, pid, timeout_seconds=args.focus_timeout)
        time.sleep(args.startup_settle)
        menu_native_trace: list[dict[str, object]] = []
        executed_menu_taps: list[dict[str, object]] = []

        def capture_menu_state(label: str) -> dict[str, int]:
            state = _read_title_menu_state(api, pid)
            menu_native_trace.append({"label": label, **state})
            session["menu_native_trace"] = menu_native_trace
            return state

        def retain_taps(taps: tuple[MenuTap, ...] | list[MenuTap]) -> None:
            executed_menu_taps.extend(asdict(tap) for tap in taps)
            session["executed_menu_taps"] = executed_menu_taps

        transition_timeout = max(3.0, args.screen_settle_ms / 1000.0 + 1.0)
        wait_for_title_menu(
            api,
            pid,
            mode=TITLE_MODE_MAIN,
            timeout_seconds=transition_timeout,
        )
        state, taps = _navigate_title_cursor(
            api,
            pid,
            mode=TITLE_MODE_MAIN,
            target=3,
            option_count=9,
            purpose="select Practice Start",
            hold_ms=args.tap_hold_ms,
            tap_gap_ms=args.tap_gap_ms,
            timeout_seconds=transition_timeout,
        )
        retain_taps(taps)
        capture_menu_state("practice_start_selected")
        tap = _confirm_title_menu(
            api,
            pid,
            next_mode=TITLE_MODE_PRACTICE_DIFFICULTY,
            purpose="enter Practice Start",
            hold_ms=args.tap_hold_ms,
            screen_settle_ms=args.screen_settle_ms,
            timeout_seconds=transition_timeout,
        )
        retain_taps((tap,))
        capture_menu_state("difficulty_screen_entered")
        state, taps = _navigate_title_cursor(
            api,
            pid,
            mode=TITLE_MODE_PRACTICE_DIFFICULTY,
            target=3,
            option_count=4,
            purpose="select Lunatic",
            hold_ms=args.tap_hold_ms,
            tap_gap_ms=args.tap_gap_ms,
            timeout_seconds=transition_timeout,
        )
        retain_taps(taps)
        capture_menu_state("difficulty_selected")
        tap = _confirm_title_menu(
            api,
            pid,
            next_mode=TITLE_MODE_PRACTICE_TEAM,
            purpose="accept native-verified Lunatic",
            hold_ms=args.tap_hold_ms,
            screen_settle_ms=args.screen_settle_ms,
            timeout_seconds=transition_timeout,
        )
        retain_taps((tap,))
        capture_menu_state("team_screen_entered")
        state, taps = _navigate_title_cursor(
            api,
            pid,
            mode=TITLE_MODE_PRACTICE_TEAM,
            target=2,
            option_count=4,
            purpose="select Sakuya/Remilia",
            hold_ms=args.tap_hold_ms,
            tap_gap_ms=args.tap_gap_ms,
            timeout_seconds=transition_timeout,
            direction_key="right",
        )
        retain_taps(taps)
        capture_menu_state("team_selected")
        tap = _confirm_title_menu(
            api,
            pid,
            next_mode=TITLE_MODE_PRACTICE_STAGE,
            purpose="accept native-verified Sakuya/Remilia",
            hold_ms=args.tap_hold_ms,
            screen_settle_ms=args.screen_settle_ms,
            timeout_seconds=transition_timeout,
        )
        retain_taps((tap,))
        capture_menu_state("stage_screen_entered")
        state, taps = _navigate_title_cursor(
            api,
            pid,
            mode=TITLE_MODE_PRACTICE_STAGE,
            target=stage.menu_index,
            option_count=8,
            purpose=f"select {stage.label}",
            hold_ms=args.tap_hold_ms,
            tap_gap_ms=args.tap_gap_ms,
            timeout_seconds=transition_timeout,
        )
        retain_taps(taps)
        capture_menu_state("stage_selected")
        session["menu_native_state"] = _validate_practice_selection(
            api,
            pid,
            stage=stage,
        )
        agent.arm(output_path=trace)
        session["agent_armed_at"] = datetime.now().astimezone().isoformat()
        monitor_trial(
            agent,
            trace=trace,
            timeout_seconds=args.trial_timeout,
            status_seconds=args.status_seconds,
            stall_timeout_seconds=args.stall_timeout,
        )
        session["agent_summary"] = agent.last_summary
        accepted = accepted_practice_termination(agent.last_summary)
        session["trial_accepted"] = accepted
        if not args.leave_game_running:
            if accepted:
                session["post_stage_no_save"] = (
                    select_no_save_before_termination(
                        api,
                        pid,
                        hold_ms=args.tap_hold_ms,
                        tap_gap_ms=args.tap_gap_ms,
                    )
                )
            else:
                session["post_stage_no_save"] = {
                    "attempted": False,
                    "reason": (
                        "trial did not terminate with route_complete"
                    ),
                }
            session["game_terminated_after_trial"] = terminate_exact_target(
                api,
                expected_exe,
            )
        session["finished_at"] = datetime.now().astimezone().isoformat()
        session["status"] = "completed" if accepted else "discarded"
        session_json.write_text(
            json.dumps(session, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        artifacts = materialize_artifacts(
            run_id=run_id,
            stage=stage,
            trace=trace,
            session_json=session_json,
        )
        print(f"trial artifacts: {artifacts.dossier_markdown}", flush=True)
        return artifacts
    except Exception as exc:
        session["finished_at"] = datetime.now().astimezone().isoformat()
        session["status"] = "failed"
        session["error_type"] = type(exc).__name__
        session["error"] = str(exc)
        session_json.parent.mkdir(parents=True, exist_ok=True)
        session_json.write_text(
            json.dumps(session, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        raise
    finally:
        if agent is not None:
            if agent.agent_thread is not None and agent.agent_thread.is_alive():
                agent.stop()
                agent.agent_thread.join(timeout=15.0)
            agent.close()
        try:
            release_injected_keys(api)
        except OSError:
            pass
        if not args.leave_game_running:
            terminate_exact_target(api, expected_exe)
        _stop_batch_process(batch_process)
        if batch_log is not None:
            batch_log.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stage",
        type=parse_practice_stage,
        default=parse_practice_stage("1"),
        metavar="{1,2,3,4a,4b,5,6a,6b}",
    )
    parser.add_argument(
        "--game-dir",
        type=Path,
        default=Path(os.environ.get("TH08_GAME_DIR", DEFAULT_GAME_DIR)),
    )
    parser.add_argument("--launch-bat", type=Path)
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--forever", action="store_true")
    parser.add_argument("--cooldown", type=float, default=2.0)
    parser.add_argument("--launch-timeout", type=float, default=25.0)
    parser.add_argument("--focus-timeout", type=float, default=10.0)
    parser.add_argument("--startup-settle", type=float, default=1.0)
    parser.add_argument("--tap-hold-ms", type=int, default=65)
    parser.add_argument("--tap-gap-ms", type=int, default=180)
    parser.add_argument("--screen-settle-ms", type=int, default=700)
    parser.add_argument("--trial-timeout", type=float, default=4500.0)
    parser.add_argument(
        "--stall-timeout",
        type=float,
        default=120.0,
        help="stop and kill when the runtime trace makes no progress",
    )
    parser.add_argument("--status-seconds", type=float, default=30.0)
    parser.add_argument(
        "--trace-transform-runtime",
        action="store_true",
        help="retain transform-relevant bullets from the complete native pool",
    )
    parser.add_argument(
        "--safety-value-horizon",
        type=int,
        default=0,
        help=(
            "enable the compact max-min empty-kernel preference for this "
            "many game frames"
        ),
    )
    parser.add_argument(
        "--viability-audit",
        action="store_true",
        help=(
            "retain ignored neutral policy capsules for offline "
            "multi-resolution audit; do not treat timing as a baseline"
        ),
    )
    parser.add_argument(
        "--postpublished-survival-shadow",
        action="store_true",
        help=(
            "compute post-Boolean survival labels for telemetry only; "
            "an isolated executor prevents worker serialization"
        ),
    )
    parser.add_argument(
        "--pipeline-prewarm-shadow",
        action="store_true",
        help=(
            "start exact-root prewarm after clearance and record lookup-only "
            "telemetry; never changes live actions"
        ),
    )
    parser.add_argument(
        "--candidate-verifier-shadow",
        action="store_true",
        help=(
            "run bounded exact candidate verification beside local planning "
            "for telemetry only; never changes live actions"
        ),
    )
    parser.add_argument(
        "--input-clock-boundary-shadow",
        action="store_true",
        help=(
            "record native FRScreen/input/player clock-boundary telemetry; "
            "never changes input, epochs, estimator state, or policies"
        ),
    )
    parser.add_argument(
        "--input-clock-shadow-sample-ms",
        type=float,
        default=1.0,
        help=(
            "minimum repeated-frame telemetry sampling cadence; never used "
            "as a semantic classifier"
        ),
    )
    parser.add_argument(
        "--refuse-existing",
        action="store_false",
        dest="kill_existing",
        help="fail instead of terminating a verified existing TH08 process",
    )
    parser.add_argument("--leave-game-running", action="store_true")
    parser.add_argument(
        "--armed",
        action="store_true",
        help="required acknowledgement for unattended physical input/process control",
    )
    parser.set_defaults(kill_existing=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if os.name != "nt":
        raise RuntimeError("th08_practice_supervisor.py requires Windows Python")
    if not args.armed:
        raise RuntimeError("unattended physical control requires --armed")
    if args.repeat <= 0:
        raise ValueError("--repeat must be positive")
    if args.safety_value_horizon < 0:
        raise ValueError("--safety-value-horizon cannot be negative")
    if args.input_clock_shadow_sample_ms <= 0.0:
        raise ValueError(
            "--input-clock-shadow-sample-ms must be positive"
        )
    if min(
        args.cooldown,
        args.launch_timeout,
        args.focus_timeout,
        args.startup_settle,
        args.trial_timeout,
        args.stall_timeout,
        args.status_seconds,
    ) <= 0:
        raise ValueError("supervisor timing arguments must be positive")
    api = Win32()
    _configure_supervisor_api(api)
    iteration = 0
    try:
        while args.forever or iteration < args.repeat:
            iteration += 1
            artifacts = run_trial(
                args,
                api=api,
                stage=args.stage,
                iteration=iteration,
            )
            print(
                f"completed iteration {iteration}: {artifacts.run_id}",
                flush=True,
            )
            if args.forever or iteration < args.repeat:
                time.sleep(args.cooldown)
    except KeyboardInterrupt:
        print("supervisor interrupted; inputs released", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr, flush=True)
        raise SystemExit(1)
