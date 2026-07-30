#!/usr/bin/env python3
"""Observe one bound native replay until its first hit or declared frame."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from collections import deque
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from th08_automation.finalb_replay_observer import (  # noqa: E402
    drive_native_stage_replay_menu,
    validate_native_stage_replay,
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
from th08_native_future_body_root import (  # noqa: E402
    capture_route2_native_future_body_root_slice,
    decode_route2_ordinary_pool_active_slots,
    route2_revalidated_native_root_component_specs,
)
from th08_replay import decode_replay, extract_stage_inputs  # noqa: E402
from th08_runtime_agent import (  # noqa: E402
    SUPPORTED_INPUT_MASK,
    TARGET_EXE,
    Win32,
    observe_state,
    release_injected_keys,
    send_scan_key,
    verify_target,
)
from touhou_control.pipeline_identity import VersionIdentity  # noqa: E402


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = "th08-native-replay-first-hit-trial-v1"
DEFAULT_STAGE5_SLOT = 15
DEFAULT_STAGE5_SHA256 = (
    "d83b98a23a2fd8f01c79c62f1aa824d56c05224449a5da1db2904f6022b68782"
)


def _stage_inputs(contract: object) -> tuple[int, ...]:
    metadata, decoded = decode_replay(contract.path)
    stage = next(
        stage
        for stage in metadata.stages
        if stage.stage_index == contract.stage_route_index
    )
    return extract_stage_inputs(decoded, stage)


def _compact_state(state: dict[str, object]) -> dict[str, object]:
    player = state["player"]
    spell = state["spell"]
    assert isinstance(player, dict)
    assert isinstance(spell, dict)
    return {
        "manager_frame": int(state["enemy_manager_frame"]),
        "input_raw": int(state["input_raw"]),
        "input_current": int(state["input_current"]),
        "input_previous": int(state["input_previous"]),
        "rng_state": int(state["rng_state"]),
        "rng_calls": int(state["rng_calls"]),
        "time_scale_bits": int(state["time_scale_bits"]),
        "spell_id": int(spell["spell_id"]) if spell["active"] else None,
        "player_phase": int(player["phase"]),
        "player_x": float(player["x"]),
        "player_y": float(player["y"]),
        "focus_logic": int(player["focus_logic"]),
        "secondary_character_active": bool(
            player["secondary_character_active"]
        ),
        "focus_transition_counter": int(
            player["focus_transition_counter"]
        ),
        "predeath_counter": int(player["predeath_counter"]),
        "resources": state["resources"],
    }


def _input_alignment(
    frames: tuple[dict[str, object], ...],
    stage_inputs: tuple[int, ...],
    *,
    radius: int = 16,
) -> list[dict[str, object]]:
    if not frames:
        return []
    consecutive_suffix = [frames[-1]]
    for frame in reversed(frames[:-1]):
        if (
            int(frame["manager_frame"])
            != int(consecutive_suffix[-1]["manager_frame"]) - 1
        ):
            break
        consecutive_suffix.append(frame)
    consecutive_suffix.reverse()
    exact_window = tuple(
        int(frame["input_current"]) & SUPPORTED_INPUT_MASK
        for frame in consecutive_suffix[-64:]
    )
    exact_start_manager_frame = int(
        consecutive_suffix[-len(exact_window)]["manager_frame"]
    )
    exact_offsets = {
        replay_start - exact_start_manager_frame
        for replay_start in range(
            0,
            len(stage_inputs) - len(exact_window) + 1,
        )
        if tuple(
            value & SUPPORTED_INPUT_MASK
            for value in stage_inputs[
                replay_start : replay_start + len(exact_window)
            ]
        )
        == exact_window
    }
    initial_offset = -int(frames[0]["manager_frame"])
    candidate_offsets = exact_offsets | set(
        range(initial_offset - radius, initial_offset + radius + 1)
    )
    candidates = []
    for offset in sorted(candidate_offsets):
        compared = 0
        matches = 0
        transition_compared = 0
        transition_matches = 0
        previous_native: int | None = None
        previous_replay: int | None = None
        for frame in frames:
            replay_frame = int(frame["manager_frame"]) + offset
            if not 0 <= replay_frame < len(stage_inputs):
                continue
            native = int(frame["input_current"]) & SUPPORTED_INPUT_MASK
            replay = stage_inputs[replay_frame] & SUPPORTED_INPUT_MASK
            compared += 1
            matches += native == replay
            if previous_native is not None and (
                native != previous_native or replay != previous_replay
            ):
                transition_compared += 1
                transition_matches += native == replay
            previous_native = native
            previous_replay = replay
        candidates.append(
            {
                "manager_to_replay_offset": offset,
                "compared": compared,
                "matches": matches,
                "match_fraction": matches / compared if compared else 0.0,
                "transition_compared": transition_compared,
                "transition_matches": transition_matches,
                "transition_match_fraction": (
                    transition_matches / transition_compared
                    if transition_compared
                    else 0.0
                ),
                "exact_consecutive_suffix_match": offset in exact_offsets,
                "exact_consecutive_suffix_length": len(exact_window),
            }
        )
    return sorted(
        candidates,
        key=lambda candidate: (
            -float(candidate["match_fraction"]),
            -int(candidate["transition_matches"]),
            abs(int(candidate["manager_to_replay_offset"])),
        ),
    )


def _capture_root(
    api: object,
    pid: int,
    reader: object,
    *,
    replay_contract: object,
    executable_sha256: str,
    output_dir: Path,
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    with api.suspend_process(pid) as suspension:
        root = capture_route2_native_future_body_root_slice(
            reader,
            root_identity=VersionIdentity.from_mapping(
                "th08-native-replay-root-v1",
                {
                    "executable_sha256": executable_sha256,
                    "replay_sha256": replay_contract.sha256,
                    "stage_input_sha256": (
                        replay_contract.stage_input_sha256
                    ),
                    "route_id": replay_contract.route_id,
                    "difficulty_index": replay_contract.difficulty_index,
                    "stage_route_index": replay_contract.stage_route_index,
                },
            ),
            clock_version=VersionIdentity.from_mapping(
                "th08-native-replay-manager-clock-v1",
                {"manager_frame_semantics": "native_u32"},
            ),
            component_specs=route2_revalidated_native_root_component_specs(),
            active_slots_from_components=(
                decode_route2_ordinary_pool_active_slots
            ),
            maximum_attempts=1,
        )
        files = []
        for component in root.components:
            path = output_dir / f"{component.spec.name}.bin"
            path.write_bytes(component.data)
            files.append(
                {
                    "name": component.spec.name,
                    "path": path.name,
                    "size": len(component.data),
                    "sha256": component.sha256,
                }
            )
    freeze_record = suspension.record()
    return {
        **root.record(),
        "atomic_capture": freeze_record,
        "local_component_files": files,
    }


def _observe(
    api: object,
    pid: int,
    reader: object,
    *,
    contract: object,
    stage_inputs: tuple[int, ...],
    timeout_seconds: float,
    poll_ms: float,
    history_frames: int,
    stop_frame: int | None,
    capture_root_at_frame: int | None,
    root_dir: Path,
    executable_sha256: str,
    fast_forward: bool,
) -> dict[str, object]:
    deadline = time.perf_counter() + timeout_seconds
    history: deque[dict[str, object]] = deque(maxlen=history_frames)
    all_frames: list[dict[str, object]] = []
    previous_manager_frame: int | None = None
    previous_phase: int | None = None
    root_record: dict[str, object] | None = None
    while time.perf_counter() < deadline:
        if fast_forward and api.foreground_pid() != pid:
            raise RuntimeError(
                "native replay lost foreground during fast-forward"
            )
        state = observe_state(reader)
        if not state["gameplay_active"]:
            return {
                "status": "gameplay_ended",
                "history": list(history),
                "input_alignment": _input_alignment(
                    tuple(all_frames),
                    stage_inputs,
                )[:5],
                "root": root_record,
            }
        if (
            state["route_id"] != contract.route_id
            or state["difficulty_index"] != contract.difficulty_index
            or state["stage_route_index"] != contract.stage_route_index
        ):
            raise RuntimeError("native replay identity drifted during observe")
        manager_frame = int(state["enemy_manager_frame"])
        if (
            capture_root_at_frame is not None
            and root_record is None
            and manager_frame >= capture_root_at_frame
        ):
            root_record = _capture_root(
                api,
                pid,
                reader,
                replay_contract=contract,
                executable_sha256=executable_sha256,
                output_dir=root_dir,
            )
        if manager_frame == previous_manager_frame:
            time.sleep(poll_ms / 1000.0)
            continue
        compact = _compact_state(state)
        history.append(compact)
        all_frames.append(compact)
        phase = int(compact["player_phase"])
        if phase == 2 and previous_phase != 2:
            return {
                "status": "first_hit_observed",
                "first_hit_manager_frame": manager_frame,
                "history": list(history),
                "input_alignment": _input_alignment(
                    tuple(all_frames),
                    stage_inputs,
                )[:5],
                "root": root_record,
            }
        if stop_frame is not None and manager_frame >= stop_frame:
            return {
                "status": "stop_frame_reached_without_hit",
                "stop_manager_frame": manager_frame,
                "history": list(history),
                "input_alignment": _input_alignment(
                    tuple(all_frames),
                    stage_inputs,
                )[:5],
                "root": root_record,
            }
        previous_manager_frame = manager_frame
        previous_phase = phase
        time.sleep(poll_ms / 1000.0)
    return {
        "status": "timeout",
        "history": list(history),
        "input_alignment": _input_alignment(
            tuple(all_frames),
            stage_inputs,
        )[:5],
        "root": root_record,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--armed", action="store_true")
    parser.add_argument("--game-dir", type=Path, default=DEFAULT_GAME_DIR)
    parser.add_argument("--launch-bat", type=Path)
    parser.add_argument("--replay-slot", type=int, default=DEFAULT_STAGE5_SLOT)
    parser.add_argument(
        "--expected-replay-sha256",
        default=DEFAULT_STAGE5_SHA256,
    )
    parser.add_argument("--route-id", type=int, default=2)
    parser.add_argument("--difficulty-index", type=int, default=3)
    parser.add_argument("--stage-route-index", type=int, default=5)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("--poll-ms", type=float, default=1.0)
    parser.add_argument("--history-frames", type=int, default=240)
    parser.add_argument("--stop-frame", type=int)
    parser.add_argument("--capture-root-at-frame", type=int)
    parser.add_argument(
        "--fast-forward",
        action="store_true",
        help="hold native Ctrl replay acceleration during gameplay",
    )
    parser.add_argument("--launch-timeout", type=float, default=30.0)
    parser.add_argument("--focus-timeout", type=float, default=10.0)
    parser.add_argument("--startup-settle", type=float, default=2.0)
    parser.add_argument("--menu-timeout", type=float, default=4.0)
    parser.add_argument("--tap-hold-ms", type=int, default=65)
    parser.add_argument("--tap-gap-ms", type=int, default=180)
    parser.add_argument("--screen-settle-ms", type=int, default=700)
    parser.add_argument("--gameplay-timeout", type=float, default=20.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.armed:
        raise RuntimeError("native replay launch requires --armed")
    if (
        args.timeout <= 0.0
        or args.poll_ms <= 0.0
        or args.history_frames <= 0
    ):
        raise ValueError("observer timing and history must be positive")

    game_dir = args.game_dir.resolve()
    expected_exe = game_dir / TARGET_EXE
    launch_bat = args.launch_bat or game_dir / DEFAULT_LAUNCH_BAT
    contract = validate_native_stage_replay(
        game_dir,
        slot=args.replay_slot,
        expected_sha256=args.expected_replay_sha256,
        expected_route_id=args.route_id,
        expected_difficulty_index=args.difficulty_index,
        expected_stage_route_index=args.stage_route_index,
    )
    stage_inputs = _stage_inputs(contract)
    envelope: dict[str, object] = {
        "schema": SCHEMA,
        "started_at": datetime.now().astimezone().isoformat(),
        "replay_contract": contract.compact_record(),
        "gameplay_input": "native_replay_only",
        "changes_gameplay_input": False,
        "native_replay_fast_forward": args.fast_forward,
        "recorded_future_world_reused": False,
        "result": {"status": "not_started"},
    }
    launch_log = args.output.with_suffix(".launch.log")
    root_dir = args.output.with_suffix(".root")
    api = Win32()
    batch_process: subprocess.Popen[bytes] | None = None
    batch_log = None
    reader = None
    try:
        if matching_targets(api, expected_exe):
            raise RuntimeError("verified TH08 is already running")
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
            drive_native_stage_replay_menu(
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
        identity = verify_target(reader)
        envelope["initial_gameplay_state"] = initial_state
        envelope["executable_identity"] = identity
        if args.fast_forward:
            if api.foreground_pid() != pid:
                raise RuntimeError(
                    "native replay is not foreground before fast-forward"
                )
            send_scan_key(api, scan_code=0x1D, pressed=True)
        envelope["result"] = _observe(
            api,
            pid,
            reader,
            contract=contract,
            stage_inputs=stage_inputs,
            timeout_seconds=args.timeout,
            poll_ms=args.poll_ms,
            history_frames=args.history_frames,
            stop_frame=args.stop_frame,
            capture_root_at_frame=args.capture_root_at_frame,
            root_dir=root_dir,
            executable_sha256=str(identity["sha256"]),
            fast_forward=args.fast_forward,
        )
    except Exception as exc:
        envelope["result"] = {
            "status": "trial_error",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        raise
    finally:
        envelope["finished_at"] = datetime.now().astimezone().isoformat()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(
                envelope,
                indent=2,
                ensure_ascii=False,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
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
        print(f"native replay artifact: {args.output}", flush=True)

    result = envelope["result"]
    assert isinstance(result, dict)
    return 0 if result["status"] in {
        "first_hit_observed",
        "stop_frame_reached_without_hit",
        "gameplay_ended",
    } else 2


if __name__ == "__main__":
    raise SystemExit(main())
