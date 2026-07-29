#!/usr/bin/env python3
"""Drive a bound Final-B replay, then run the read-only scale observer."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from th08_automation.finalb_replay_observer import (  # noqa: E402
    drive_finalb_replay_menu,
    validate_finalb_replay,
    wait_for_bound_replay_gameplay,
)
from th08_automation.practice_supervisor import (  # noqa: E402
    DEFAULT_GAME_DIR,
    DEFAULT_LAUNCH_BAT,
    _stop_batch_process,
)
from th08_automation.practice_windows import (  # noqa: E402
    focus_target_window,
    launch_patch_batch,
    matching_targets,
    terminate_exact_target,
    wait_for_patched_target,
)
from th08_live.scale_source_trace import (  # noqa: E402
    FINAL_B_ECL_STATIC_SHA256,
    FINAL_B_SCALE_SOURCE_TRACE_AUTHORITY,
    FINAL_B_SCALE_SPELL_ID,
    FINAL_B_STAGE_ROUTE_INDEX,
    FinalBScaleSourceTraceConfiguration,
    FinalBScaleSourceTraceService,
)
from th08_runtime_agent import (  # noqa: E402
    TARGET_EXE,
    Win32,
    observe_state,
    release_injected_keys,
    verify_target,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPLAY_SLOT = 13
DEFAULT_REPLAY_SHA256 = (
    "1026289ffec9f3dd1858378e81bbbbb84f568f041047a401dd86f74211c4a7f2"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Explicitly armed native-menu replay launch followed by a "
            "read-only Final-B spell-190 scale-source observation"
        )
    )
    parser.add_argument("--armed", action="store_true")
    parser.add_argument("--game-dir", type=Path, default=DEFAULT_GAME_DIR)
    parser.add_argument("--launch-bat", type=Path)
    parser.add_argument("--replay-slot", type=int, default=DEFAULT_REPLAY_SLOT)
    parser.add_argument(
        "--expected-replay-sha256",
        default=DEFAULT_REPLAY_SHA256,
    )
    parser.add_argument(
        "--static-ecl",
        type=Path,
        default=ROOT / "artifacts" / "decoded" / "ecldata7.ecl",
    )
    parser.add_argument(
        "--static-sha256",
        default=FINAL_B_ECL_STATIC_SHA256,
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--launch-timeout", type=float, default=30.0)
    parser.add_argument("--focus-timeout", type=float, default=10.0)
    parser.add_argument("--startup-settle", type=float, default=2.0)
    parser.add_argument("--menu-timeout", type=float, default=4.0)
    parser.add_argument("--tap-hold-ms", type=int, default=65)
    parser.add_argument("--tap-gap-ms", type=int, default=180)
    parser.add_argument("--screen-settle-ms", type=int, default=700)
    parser.add_argument("--gameplay-timeout", type=float, default=20.0)
    parser.add_argument("--observer-timeout", type=float, default=1200.0)
    parser.add_argument("--poll-ms", type=float, default=2.0)
    parser.add_argument("--status-seconds", type=float, default=30.0)
    return parser


def _failure_record(
    *,
    status: str,
    timeout_seconds: float | None = None,
    error: Exception | None = None,
) -> dict[str, object]:
    record: dict[str, object] = {
        "kind": "finalb_scale_source_trace",
        "status": status,
        "authority": FINAL_B_SCALE_SOURCE_TRACE_AUTHORITY,
        "hard_action_authority": False,
        "changes_input": False,
        "target_stage_route_index": FINAL_B_STAGE_ROUTE_INDEX,
        "target_spell_id": FINAL_B_SCALE_SPELL_ID,
    }
    if timeout_seconds is not None:
        record["timeout_seconds"] = timeout_seconds
    if error is not None:
        record["error_type"] = type(error).__name__
        record["error"] = str(error)
    return record


def _write_envelope(path: Path, envelope: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            envelope,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _observe(
    *,
    reader: object,
    service: FinalBScaleSourceTraceService,
    observer_timeout: float,
    poll_ms: float,
    status_seconds: float,
) -> dict[str, object]:
    deadline = time.perf_counter() + observer_timeout
    next_status = time.perf_counter()
    gameplay_epoch = 1
    last_state: dict[str, object] | None = None
    while time.perf_counter() < deadline:
        state = observe_state(reader)
        last_state = state
        if not state["gameplay_active"]:
            return _failure_record(status="gameplay_ended_before_target")
        if (
            state["route_id"] != 2
            or state["difficulty_index"] != 3
            or state["stage_route_index"] != 7
        ):
            return _failure_record(status="runtime_identity_drift")
        spell = state["spell"]
        active_spell_id = int(spell["spell_id"]) if spell["active"] else None
        record = service.observe_if_due(
            reader,
            decision_frame=int(state["enemy_manager_frame"]),
            expected_manager_frame=int(state["enemy_manager_frame"]),
            gameplay_epoch=gameplay_epoch,
            route_id=int(state["route_id"]),
            difficulty_index=int(state["difficulty_index"]),
            stage_route_index=int(state["stage_route_index"]),
            spell_id=active_spell_id,
        )
        if record is not None:
            return record
        now = time.perf_counter()
        if now >= next_status:
            print(
                "replay observer: "
                f"frame={state['enemy_manager_frame']} "
                f"spell={active_spell_id}",
                flush=True,
            )
            next_status = now + status_seconds
        time.sleep(poll_ms / 1000.0)
    record = _failure_record(
        status="timeout",
        timeout_seconds=observer_timeout,
    )
    if last_state is not None:
        record["last_manager_frame"] = last_state["enemy_manager_frame"]
        record["last_spell"] = last_state["spell"]
    return record


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.armed:
        raise RuntimeError(
            "physical replay menu input requires the explicit --armed flag"
        )
    if (
        args.launch_timeout <= 0.0
        or args.focus_timeout <= 0.0
        or args.startup_settle < 0.0
        or args.menu_timeout <= 0.0
        or args.gameplay_timeout <= 0.0
        or args.observer_timeout <= 0.0
        or args.poll_ms <= 0.0
        or args.status_seconds <= 0.0
    ):
        raise ValueError("all replay trial timing values must be positive")

    game_dir = args.game_dir.resolve()
    expected_exe = game_dir / TARGET_EXE
    launch_bat = args.launch_bat or game_dir / DEFAULT_LAUNCH_BAT
    contract = validate_finalb_replay(
        game_dir,
        slot=args.replay_slot,
        expected_sha256=args.expected_replay_sha256,
    )
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = args.output or (
        ROOT
        / "artifacts"
        / "runtime_reports"
        / f"finalb_scale_source_replay_{timestamp}.json"
    )
    launch_log = output.with_suffix(".launch.log")
    envelope: dict[str, object] = {
        "schema": "th08-finalb-scale-source-replay-trial-v1",
        "observer": (
            "scripts/tools/th08_finalb_scale_source_replay_trial.py"
        ),
        "started_at": datetime.now().astimezone().isoformat(),
        "replay_contract": contract.compact_record(),
        "menu_input_scope": "pre_gameplay_only",
        "gameplay_input": "native_replay_only",
        "record": _failure_record(status="not_started"),
    }

    api = Win32()
    batch_process: subprocess.Popen[bytes] | None = None
    batch_log = None
    reader = None
    try:
        matches = matching_targets(api, expected_exe)
        if matches:
            raise RuntimeError(
                "verified TH08 is already running; refusing ambiguous attach"
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
        envelope["pid"] = pid
        envelope["executable_identity"] = identity
        focus_target_window(api, pid, timeout_seconds=args.focus_timeout)
        time.sleep(args.startup_settle)
        envelope["menu_trace"] = list(
            drive_finalb_replay_menu(
                api,
                pid,
                contract=contract,
                hold_ms=args.tap_hold_ms,
                tap_gap_ms=args.tap_gap_ms,
                screen_settle_ms=args.screen_settle_ms,
                timeout_seconds=args.menu_timeout,
            )
        )
        reader, initial_state = wait_for_bound_replay_gameplay(
            api,
            pid,
            contract=contract,
            timeout_seconds=args.gameplay_timeout,
        )
        envelope["initial_gameplay_state"] = initial_state
        envelope["executable_identity"] = verify_target(reader)
        service = FinalBScaleSourceTraceService(
            FinalBScaleSourceTraceConfiguration(
                static_path=args.static_ecl,
                expected_static_sha256=args.static_sha256,
            )
        )
        envelope["record"] = _observe(
            reader=reader,
            service=service,
            observer_timeout=args.observer_timeout,
            poll_ms=args.poll_ms,
            status_seconds=args.status_seconds,
        )
    except Exception as exc:
        envelope["record"] = _failure_record(
            status="trial_error",
            error=exc,
        )
        raise
    finally:
        envelope["finished_at"] = datetime.now().astimezone().isoformat()
        _write_envelope(output, envelope)
        if reader is not None:
            reader.close()
        try:
            release_injected_keys(api)
        except OSError:
            pass
        terminate_exact_target(api, expected_exe)
        _stop_batch_process(batch_process)
        if batch_log is not None:
            batch_log.close()
        print(f"replay observer artifact: {output}", flush=True)
    record = envelope["record"]
    assert isinstance(record, dict)
    return (
        0
        if record.get("status") == "accepted_complete_source_trace"
        else 2
    )


if __name__ == "__main__":
    raise SystemExit(main())
