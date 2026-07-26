#!/usr/bin/env python3
"""Launch and retain one continuous original-TH08 Route-2 run."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from analysis.th08_fullrun_regression import load_and_validate
from analysis.th08_run_dossier import main as build_run_dossier
from th08_agent_hotkey import AgentHotkey
from th08_automation.practice_menu import (
    MenuTap,
    PracticeDifficulty,
    parse_practice_difficulty,
)
from th08_practice_supervisor import (
    DEFAULT_GAME_DIR,
    DEFAULT_LAUNCH_BAT,
    RUNTIME_REPORT_DIR,
    RUN_NOTE_DIR,
    TITLE_MODE_MAIN,
    _configure_supervisor_api,
    _matching_targets,
    _navigate_title_cursor,
    _read_title_menu_state,
    _stop_batch_process,
    drive_menu_plan,
    ensure_caps_lock_enabled,
    focus_target_window,
    launch_patch_batch,
    monitor_trial,
    terminate_exact_target,
    wait_for_patched_target,
    wait_for_title_menu,
)
from th08_runtime_agent import TARGET_EXE, Win32, release_injected_keys


ROOT = Path(__file__).resolve().parent.parent
TITLE_MODE_GAME_DIFFICULTY = 4
TITLE_MODE_GAME_TEAM = 5
EXPECTED_ROUTE_STAGES = (0, 1, 2, 3, 5, 7)
DEFAULT_AGENT_DURATION_SECONDS = 4500.0
DEFAULT_TRIAL_TIMEOUT_SECONDS = 4650.0


def anchor_game_start(
    api: Win32,
    pid: int,
    *,
    hold_ms: int,
    tap_gap_ms: int,
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
    drive_menu_plan(api, pid, taps, hold_ms=hold_ms)
    state = _read_title_menu_state(api, pid)
    if (
        state["mode"] != TITLE_MODE_MAIN
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


def validate_team_selection(
    api: Win32,
    pid: int,
    *,
    difficulty: PracticeDifficulty,
) -> dict[str, int]:
    state = _read_title_menu_state(api, pid)
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


def _terminal_scene_record(trace: Path) -> dict[str, object]:
    with trace.open("rb") as source:
        source.seek(0, os.SEEK_END)
        end = source.tell()
        source.seek(max(0, end - 1024 * 1024))
        tail = source.read()
    for binary_line in reversed(tail.splitlines()):
        try:
            row = json.loads(binary_line)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if (
            row.get("kind") == "scene_inactive"
            and row.get("status") == "terminal_unload"
            and row.get("transition_from_stage") == 7
            and row.get("expected_stage") is None
        ):
            return row
    raise ValueError("trace has no Final-B terminal_unload scene record")


def _change(before: float | int, after: float | int) -> dict[str, float | int]:
    return {
        "baseline": before,
        "candidate": after,
        "delta": after - before,
    }


def _percentile_change(
    before: dict[str, object],
    after: dict[str, object],
) -> dict[str, object]:
    return {
        key: _change(float(before[key]), float(after[key]))
        for key in ("median", "p95", "max")
    }


def _optional_change(
    before: object,
    after: object,
) -> dict[str, object]:
    if before is None or after is None:
        return {"baseline": before, "candidate": after, "delta": None}
    return _change(float(before), float(after))


def compare_full_dossiers(
    baseline: dict[str, object],
    candidate: dict[str, object],
) -> dict[str, object]:
    before_totals = baseline["totals"]
    after_totals = candidate["totals"]
    before_stages = {
        int(stage["stage_route_index"]): stage for stage in baseline["stages"]
    }
    after_stages = {
        int(stage["stage_route_index"]): stage for stage in candidate["stages"]
    }
    per_stage = {}
    for stage_index in EXPECTED_ROUTE_STAGES:
        before = before_stages.get(stage_index)
        after = after_stages.get(stage_index)
        if before is None or after is None:
            continue
        per_stage[str(stage_index)] = {
            "stage_label": after["stage_label"],
            "death_count": _change(
                int(before["death_count"]),
                int(after["death_count"]),
            ),
            "decision_count": _change(
                int(before["decision_count"]),
                int(after["decision_count"]),
            ),
            "max_active_bullets": _change(
                int(before["max_active_bullets"]),
                int(after["max_active_bullets"]),
            ),
            "max_active_lasers": _change(
                int(before["max_active_lasers"]),
                int(after["max_active_lasers"]),
            ),
            "power_end": _change(
                float(before["resources"]["power"]["end"]),
                float(after["resources"]["power"]["end"]),
            ),
            "read_ms": _percentile_change(
                before["latency_ms"]["read"],
                after["latency_ms"]["read"],
            ),
            "plan_ms": _percentile_change(
                before["latency_ms"]["plan"],
                after["latency_ms"]["plan"],
            ),
            "action_lag_frames": _percentile_change(
                before["frame_lag"]["action"],
                after["frame_lag"]["action"],
            ),
        }
    before_solver = baseline["control_policy"]["robust_viability"]
    after_solver = candidate["control_policy"]["robust_viability"]
    return {
        "schema": "th08-full-route-comparison-v1",
        "baseline_run_id": baseline["run_id"],
        "candidate_run_id": candidate["run_id"],
        "route_complete": {
            "baseline": (
                baseline["provenance"][-1]["summary"][
                    "termination_reason"
                ]
                == "route_complete"
            ),
            "candidate": (
                candidate["provenance"][-1]["summary"][
                    "termination_reason"
                ]
                == "route_complete"
            ),
        },
        "hard_no_bomb_passed": {
            "baseline": bool(
                baseline["control_policy"]["no_bomb_verification"]["passed"]
            ),
            "candidate": bool(
                candidate["control_policy"]["no_bomb_verification"]["passed"]
            ),
        },
        "death_count": _change(
            int(before_totals["death_count"]),
            int(after_totals["death_count"]),
        ),
        "decision_count": _change(
            int(before_totals["decision_count"]),
            int(after_totals["decision_count"]),
        ),
        "post_hit_bomb_stock_decrease": _change(
            float(before_totals.get("post_hit_bomb_stock_decrease", 0.0)),
            float(after_totals.get("post_hit_bomb_stock_decrease", 0.0)),
        ),
        "primary_cause_counts": {
            key: _change(
                int(before_totals["primary_cause_counts"].get(key, 0)),
                int(after_totals["primary_cause_counts"].get(key, 0)),
            )
            for key in sorted(
                set(before_totals["primary_cause_counts"])
                | set(after_totals["primary_cause_counts"])
            )
        },
        "solver_delivery": {
            "solve_ms": _percentile_change(
                before_solver["solve_ms"],
                after_solver["solve_ms"],
            ),
            "first_observed_age_frames": _percentile_change(
                before_solver["first_observed_age_frames"],
                after_solver["first_observed_age_frames"],
            ),
            "unique_solution_count": _change(
                int(before_solver["unique_solution_count"]),
                int(after_solver["unique_solution_count"]),
            ),
            "query_count": _change(
                int(before_solver["query_count"]),
                int(after_solver["query_count"]),
            ),
            "reported_stale_solution_count": _change(
                int(before_solver["reported_stale_solution_count"]),
                int(after_solver["reported_stale_solution_count"]),
            ),
            "serial_worker_serviceable_count": _optional_change(
                before_solver.get("serial_worker_serviceable_count"),
                after_solver.get("serial_worker_serviceable_count"),
            ),
            "candidate_backend_counts": after_solver.get(
                "backend_counts",
                {},
            ),
            "candidate_solver_phase_ms": after_solver.get(
                "solver_phase_ms",
                {},
            ),
        },
        "per_stage": per_stage,
    }


def _previous_full_dossier(
    current: Path,
    difficulty_key: str = "lunatic",
) -> Path | None:
    candidates = sorted(
        RUNTIME_REPORT_DIR.glob(
            f"{difficulty_key}_route2_fullrun*.dossier.json"
        ),
        key=lambda path: path.stat().st_mtime_ns,
        reverse=True,
    )
    for path in candidates:
        if path == current:
            continue
        try:
            dossier = json.loads(path.read_text(encoding="utf-8"))
            verification = dossier["control_policy"]["no_bomb_verification"]
            summary = dossier["provenance"][-1]["summary"]
        except (OSError, KeyError, IndexError, json.JSONDecodeError):
            continue
        if (
            dossier.get("schema")
            in {
                "th08-lunatic-run-dossier-v2",
                "th08-route-run-dossier-v3",
            }
            and verification.get("passed")
            and summary
            and summary.get("termination_reason") == "route_complete"
        ):
            return path
    return None


def write_compact_full_route_summary(
    *,
    path: Path,
    dossier: dict[str, object],
) -> None:
    existing = (
        json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    )
    stages = dossier["stages"]
    existing.update(
        {
            "decision_count": int(dossier["totals"]["decision_count"]),
            "first_frame": int(dossier["totals"]["first_frame"]),
            "last_frame": int(dossier["totals"]["last_frame"]),
            "termination_reason": "route_complete",
            "hit_count": int(dossier["totals"]["death_count"]),
            "hit_frames": [
                int(death["frame"]) for death in dossier["deaths"]
            ],
            "stage_progress": {
                "transitions": [
                    {
                        "frame": int(stage["first_frame"]),
                        "stage_route_index": int(
                            stage["stage_route_index"]
                        ),
                        "stage_label": stage["stage_label"],
                    }
                    for stage in stages
                ],
                "last_stage_route_index": int(
                    stages[-1]["stage_route_index"]
                ),
                "last_stage_label": stages[-1]["stage_label"],
            },
        }
    )
    path.write_text(
        json.dumps(existing, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def materialize_artifacts(
    *,
    run_id: str,
    trace: Path,
    completion: dict[str, object],
    difficulty_key: str = "lunatic",
    difficulty_index: int = 3,
) -> dict[str, object]:
    prefix = RUNTIME_REPORT_DIR / run_id
    dossier_json = prefix.with_suffix(".dossier.json")
    dossier_markdown = prefix.with_suffix(".dossier.md")
    deaths_csv = prefix.with_suffix(".deaths.csv")
    regressions_json = prefix.with_suffix(".regressions.json")
    comparison_json = prefix.with_suffix(".comparison.json")
    build_run_dossier(
        [
            "--run-id",
            run_id,
            "--trace",
            str(trace),
            "--manifest",
            str(
                ROOT
                / "artifacts"
                / "route_manifests"
                / f"sakuya_remilia_{difficulty_key}_final_b.json"
            ),
            "--json-output",
            str(dossier_json),
            "--markdown-output",
            str(dossier_markdown),
            "--death-csv",
            str(deaths_csv),
            "--regression-output",
            str(regressions_json),
            "--completion-frame",
            str(int(completion["frame"])),
            "--completion-engine-flags",
            str(int(completion["engine_flags"])),
        ]
    )
    dossier = json.loads(dossier_json.read_text(encoding="utf-8"))
    acceptance_target = dossier["acceptance_target"]
    if (
        int(acceptance_target["difficulty_index"]) != difficulty_index
        or str(acceptance_target["difficulty"]).lower() != difficulty_key
    ):
        raise RuntimeError(
            "full-route dossier difficulty mismatch: "
            f"expected={difficulty_key}/{difficulty_index} "
            f"observed={acceptance_target['difficulty']}/"
            f"{acceptance_target['difficulty_index']}"
        )
    observed_stages = tuple(
        int(stage["stage_route_index"]) for stage in dossier["stages"]
    )
    if observed_stages != EXPECTED_ROUTE_STAGES:
        raise RuntimeError(
            f"full-route dossier stage sequence mismatch: {observed_stages}"
        )
    if not dossier["control_policy"]["no_bomb_verification"]["passed"]:
        raise RuntimeError("full-route dossier failed the hard no-Bomb gate")
    if (
        dossier["provenance"][-1]["summary"]["termination_reason"]
        != "route_complete"
    ):
        raise RuntimeError("full-route dossier did not retain route completion")
    summary_json = trace.with_suffix(".summary.json")
    write_compact_full_route_summary(path=summary_json, dossier=dossier)
    regression_summary = asdict(load_and_validate(regressions_json))

    baseline = _previous_full_dossier(dossier_json, difficulty_key)
    if baseline is not None:
        comparison_json.write_text(
            json.dumps(
                compare_full_dossiers(
                    json.loads(baseline.read_text(encoding="utf-8")),
                    dossier,
                ),
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
    else:
        comparison_json = None

    RUN_NOTE_DIR.mkdir(parents=True, exist_ok=True)
    run_note = RUN_NOTE_DIR / f"{run_id}.md"
    shutil.copyfile(dossier_markdown, run_note)
    return {
        "dossier_json": str(dossier_json),
        "dossier_markdown": str(dossier_markdown),
        "deaths_csv": str(deaths_csv),
        "regressions_json": str(regressions_json),
        "regression_summary": regression_summary,
        "comparison_json": (
            str(comparison_json) if comparison_json is not None else None
        ),
        "comparison_baseline": str(baseline) if baseline is not None else None,
        "run_note": str(run_note),
        "summary_json": str(summary_json),
    }


def _write_session(path: Path, session: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(session, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def run_trial(args: argparse.Namespace, *, api: Win32) -> str:
    game_dir = args.game_dir.resolve()
    expected_exe = game_dir / TARGET_EXE
    launch_bat = args.launch_bat or game_dir / DEFAULT_LAUNCH_BAT
    if args.kill_existing:
        if terminate_exact_target(api, expected_exe):
            print("terminated previous verified TH08 process", flush=True)
    elif _matching_targets(api, expected_exe):
        raise RuntimeError("verified TH08 is already running")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    difficulty = args.difficulty
    run_id = (
        f"{difficulty.key}_route2_fullrun_unattended_{timestamp}"
    )
    trace = RUNTIME_REPORT_DIR / f"{run_id}.jsonl"
    session_path = RUNTIME_REPORT_DIR / f"{run_id}.session.json"
    launch_log = RUNTIME_REPORT_DIR / f"{run_id}.launch.log"
    session: dict[str, object] = {
        "schema": "th08-unattended-full-route-session-v1",
        "run_id": run_id,
        "game_dir": str(game_dir),
        "launch_bat": str(launch_bat),
        "difficulty": difficulty.label,
        "difficulty_key": difficulty.key,
        "difficulty_index": difficulty.menu_index,
        "team": "Sakuya/Remilia",
        "route_id": 2,
        "expected_stage_sequence": list(EXPECTED_ROUTE_STAGES),
        "hard_no_bomb": True,
        "safety_value_horizon": 0,
        "trace_transform_runtime": False,
        "viability_audit": False,
        "agent_duration_seconds": args.agent_duration,
        "leave_game_running": args.leave_game_running,
        "started_at": datetime.now().astimezone().isoformat(),
    }
    batch_process: subprocess.Popen[bytes] | None = None
    batch_log = None
    agent: AgentHotkey | None = None
    accepted = False
    try:
        session["caps_lock_changed"] = ensure_caps_lock_enabled(api)
        agent = AgentHotkey(
            expected_difficulty=difficulty.menu_index,
            expected_stage=0,
            terminal_stage=None,
            safety_value_horizon=0,
            duration_seconds=args.agent_duration,
            detailed_summary=False,
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

        menu_trace: list[dict[str, object]] = []
        menu_taps: list[dict[str, object]] = []

        def capture(label: str) -> None:
            menu_trace.append({"label": label, **_read_title_menu_state(api, pid)})
            session["menu_native_trace"] = menu_trace

        def retain(taps: tuple[MenuTap, ...]) -> None:
            menu_taps.extend(asdict(tap) for tap in taps)
            session["executed_menu_taps"] = menu_taps

        transition_timeout = max(
            3.0,
            args.screen_settle_ms / 1000.0 + 1.0,
        )
        wait_for_title_menu(
            api,
            pid,
            mode=TITLE_MODE_MAIN,
            timeout_seconds=transition_timeout,
        )
        capture("main")
        _state, taps = anchor_game_start(
            api,
            pid,
            hold_ms=args.tap_hold_ms,
            tap_gap_ms=args.tap_gap_ms,
        )
        retain(taps)
        capture("game_start_selected")
        tap = confirm_title_mode(
            api,
            pid,
            next_mode=TITLE_MODE_GAME_DIFFICULTY,
            purpose="enter Game Start",
            hold_ms=args.tap_hold_ms,
            screen_settle_ms=args.screen_settle_ms,
            timeout_seconds=transition_timeout,
        )
        retain((tap,))
        capture("difficulty_screen_entered")
        _state, taps = _navigate_title_cursor(
            api,
            pid,
            mode=TITLE_MODE_GAME_DIFFICULTY,
            target=difficulty.menu_index,
            option_count=4,
            purpose=f"select {difficulty.label}",
            hold_ms=args.tap_hold_ms,
            tap_gap_ms=args.tap_gap_ms,
            timeout_seconds=transition_timeout,
        )
        retain(taps)
        capture(f"{difficulty.key}_selected")
        tap = confirm_title_mode(
            api,
            pid,
            next_mode=TITLE_MODE_GAME_TEAM,
            purpose=f"accept native-verified {difficulty.label}",
            hold_ms=args.tap_hold_ms,
            screen_settle_ms=args.screen_settle_ms,
            timeout_seconds=transition_timeout,
        )
        retain((tap,))
        capture("team_screen_entered")
        _state, taps = _navigate_title_cursor(
            api,
            pid,
            mode=TITLE_MODE_GAME_TEAM,
            target=2,
            option_count=4,
            purpose="select Sakuya/Remilia",
            hold_ms=args.tap_hold_ms,
            tap_gap_ms=args.tap_gap_ms,
            timeout_seconds=transition_timeout,
            direction_key="right",
        )
        retain(taps)
        capture("team_selected")
        session["menu_native_state"] = validate_team_selection(
            api,
            pid,
            difficulty=difficulty,
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
        accepted = bool(
            isinstance(agent.last_summary, dict)
            and agent.last_summary.get("termination_reason")
            == "route_complete"
        )
        session["trial_accepted"] = accepted
        if not accepted:
            raise RuntimeError(
                "full route did not terminate with route_complete: "
                f"{agent.last_summary}"
            )
        completion = _terminal_scene_record(trace)
        session["completion_scene"] = completion
        if retain_game_after_trial(
            accepted=accepted,
            leave_game_running=args.leave_game_running,
        ):
            release_injected_keys(api)
            agent.close()
            agent = None
            session["game_terminated_after_trial"] = False
            session["game_left_running_after_trial"] = True
            session["input_released_before_handoff"] = True
            print(
                "GAME LEFT RUNNING: automation stopped and all injected "
                "keys were released; no post-route save choice or process "
                "termination was issued.",
                flush=True,
            )
        else:
            session["game_terminated_after_trial"] = (
                terminate_exact_target(api, expected_exe)
            )
            session["game_left_running_after_trial"] = False
        session["status"] = "completed_pending_artifacts"
        session["finished_at"] = datetime.now().astimezone().isoformat()
        _write_session(session_path, session)
        session["artifacts"] = materialize_artifacts(
            run_id=run_id,
            trace=trace,
            completion=completion,
            difficulty_key=difficulty.key,
            difficulty_index=difficulty.menu_index,
        )
        session["status"] = "completed"
        session["finished_at"] = datetime.now().astimezone().isoformat()
        _write_session(session_path, session)
        print(f"full-route artifacts: {session['artifacts']}", flush=True)
        return run_id
    except Exception as exc:
        session["trial_accepted"] = accepted
        session["status"] = (
            "completed_pending_artifacts"
            if accepted
            else ("discarded" if trace.exists() else "failed")
        )
        session["finished_at"] = datetime.now().astimezone().isoformat()
        session["error_type"] = type(exc).__name__
        session["error"] = str(exc)
        _write_session(session_path, session)
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
        if not retain_game_after_trial(
            accepted=accepted,
            leave_game_running=args.leave_game_running,
        ):
            terminate_exact_target(api, expected_exe)
        _stop_batch_process(batch_process)
        if batch_log is not None:
            batch_log.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--game-dir",
        type=Path,
        default=Path(os.environ.get("TH08_GAME_DIR", DEFAULT_GAME_DIR)),
    )
    parser.add_argument("--launch-bat", type=Path)
    parser.add_argument("--launch-timeout", type=float, default=25.0)
    parser.add_argument("--focus-timeout", type=float, default=10.0)
    parser.add_argument("--startup-settle", type=float, default=1.0)
    parser.add_argument("--tap-hold-ms", type=int, default=65)
    parser.add_argument("--tap-gap-ms", type=int, default=180)
    parser.add_argument("--screen-settle-ms", type=int, default=700)
    parser.add_argument(
        "--agent-duration",
        type=float,
        default=DEFAULT_AGENT_DURATION_SECONDS,
    )
    parser.add_argument(
        "--trial-timeout",
        type=float,
        default=DEFAULT_TRIAL_TIMEOUT_SECONDS,
    )
    parser.add_argument("--stall-timeout", type=float, default=120.0)
    parser.add_argument("--status-seconds", type=float, default=30.0)
    parser.add_argument(
        "--difficulty",
        type=parse_practice_difficulty,
        default=parse_practice_difficulty("lunatic"),
        metavar="{easy,normal,hard,lunatic}",
        help="original Game Start difficulty; defaults to lunatic",
    )
    parser.add_argument(
        "--leave-game-running",
        action="store_true",
        help=(
            "after accepted route completion, release injected keys but do "
            "not choose a save option or terminate the verified game"
        ),
    )
    parser.add_argument(
        "--refuse-existing",
        action="store_false",
        dest="kill_existing",
    )
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
        raise RuntimeError(
            "th08_full_route_supervisor.py requires Windows Python"
        )
    if not args.armed:
        raise RuntimeError("unattended physical control requires --armed")
    if min(
        args.launch_timeout,
        args.focus_timeout,
        args.startup_settle,
        args.agent_duration,
        args.trial_timeout,
        args.stall_timeout,
        args.status_seconds,
    ) <= 0.0:
        raise ValueError("supervisor timing arguments must be positive")
    if args.trial_timeout <= args.agent_duration:
        raise ValueError("trial timeout must exceed the agent duration")
    api = Win32()
    _configure_supervisor_api(api)
    run_id = run_trial(args, api=api)
    print(f"completed full route: {run_id}", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr, flush=True)
        raise SystemExit(1)
