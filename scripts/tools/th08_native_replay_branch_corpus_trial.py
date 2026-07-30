#!/usr/bin/env python3
"""Execute a replay branch corpus through original TH08, restoring its slot."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from th08_automation.practice_supervisor import DEFAULT_GAME_DIR  # noqa: E402
from th08_replay import decode_replay  # noqa: E402


SCHEMA = "th08-native-replay-branch-corpus-trial-v1"


def _copy_verified(source: Path, target: Path, expected_sha256: str) -> None:
    shutil.copy2(source, target)
    metadata, _decoded = decode_replay(target)
    if metadata.sha256 != expected_sha256:
        raise RuntimeError(
            f"replay slot copy identity mismatch: {metadata.sha256}"
        )


def _endpoint(result: dict[str, object]) -> dict[str, object] | None:
    history = result.get("history")
    if not isinstance(history, list) or not history:
        return None
    state = history[-1]
    if not isinstance(state, dict):
        return None
    keys = (
        "manager_frame",
        "input_current",
        "input_previous",
        "rng_state",
        "rng_calls",
        "time_scale_bits",
        "spell_id",
        "player_phase",
        "player_x",
        "player_y",
        "focus_logic",
        "secondary_character_active",
        "focus_transition_counter",
    )
    return {key: state.get(key) for key in keys}


def _trial_summary(
    branch: dict[str, object],
    envelope: dict[str, object],
    *,
    report_path: Path,
) -> dict[str, object]:
    replay_contract = envelope.get("replay_contract")
    if (
        not isinstance(replay_contract, dict)
        or replay_contract.get("sha256") != branch["replay_sha256"]
    ):
        raise RuntimeError("native branch trial replay identity mismatch")
    result = envelope.get("result")
    if not isinstance(result, dict):
        raise RuntimeError("native branch trial has no result object")
    status = str(result.get("status"))
    if status not in (
        "first_hit_observed",
        "stop_frame_reached_without_hit",
    ):
        raise RuntimeError(f"native branch trial did not close: {status}")
    return {
        "token": branch["token"],
        "complete_mask": branch["complete_mask"],
        "movement_label": branch["movement_label"],
        "branch_replay_sha256": branch["replay_sha256"],
        "trial_report": report_path.as_posix(),
        "status": status,
        "first_hit_manager_frame": result.get(
            "first_hit_manager_frame"
        ),
        "stop_manager_frame": result.get("stop_manager_frame"),
        "endpoint": _endpoint(result),
        "changes_gameplay_input": envelope.get(
            "changes_gameplay_input"
        ),
        "recorded_future_world_reused": envelope.get(
            "recorded_future_world_reused"
        ),
    }


def _write_report(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--armed", action="store_true")
    parser.add_argument("--corpus-report", type=Path, required=True)
    parser.add_argument("--branch-dir", type=Path, required=True)
    parser.add_argument("--canonical-replay", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--game-dir", type=Path, default=DEFAULT_GAME_DIR)
    parser.add_argument("--replay-slot", type=int, default=15)
    parser.add_argument("--stop-frame", type=int, required=True)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--history-frames", type=int, default=16)
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "--token",
        action="append",
        dest="tokens",
        help="execute only this exact corpus token; repeat as needed",
    )
    args = parser.parse_args(argv)

    if not args.armed:
        raise RuntimeError("native branch corpus execution requires --armed")
    if not 1 <= args.replay_slot <= 15:
        raise ValueError("replay slot must be in 1..15")
    if args.stop_frame <= 0 or args.timeout <= 0.0:
        raise ValueError("native branch trial bounds must be positive")
    corpus = json.loads(args.corpus_report.read_text(encoding="utf-8"))
    canonical_metadata, _ = decode_replay(args.canonical_replay)
    if canonical_metadata.sha256 != corpus["source_sha256"]:
        raise RuntimeError("canonical replay does not match corpus source")
    branches = corpus.get("branches")
    if not isinstance(branches, list) or len(branches) != 36:
        raise RuntimeError("native branch corpus must contain all 36 masks")
    if args.limit is not None and args.tokens:
        raise ValueError("--limit and --token cannot be combined")
    if args.tokens:
        requested = set(args.tokens)
        selected = [
            branch for branch in branches if branch.get("token") in requested
        ]
        found = {str(branch["token"]) for branch in selected}
        if found != requested:
            raise ValueError(
                f"unknown native branch tokens: {sorted(requested - found)}"
            )
    else:
        selected = (
            branches[: args.limit] if args.limit is not None else branches
        )
    if not selected:
        raise ValueError("native branch corpus selection is empty")

    slot = (
        args.game_dir
        / "replay"
        / f"th8_{args.replay_slot:02d}.rpy"
    )
    child_tool = Path(__file__).with_name(
        "th08_native_replay_first_hit_trial.py"
    )
    report: dict[str, object] = {
        "schema": SCHEMA,
        "started_at": datetime.now().astimezone().isoformat(),
        "corpus_report": args.corpus_report.as_posix(),
        "source_sha256": corpus["source_sha256"],
        "root_frame": corpus["root_frame"],
        "hold_frames": corpus["hold_frames"],
        "stop_manager_frame": args.stop_frame,
        "selected_tokens": [branch["token"] for branch in selected],
        "executor": "original_th08_executable_from_replay_prefix",
        "explicit_native_root_executor": False,
        "physical_authority": False,
        "canonical_slot_restore_sha256": canonical_metadata.sha256,
        "isolated_game_dir": args.game_dir.as_posix(),
        "branches": [],
        "status": "running",
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    completed: list[dict[str, object]] = []
    try:
        _copy_verified(
            args.canonical_replay,
            slot,
            canonical_metadata.sha256,
        )
        for index, branch in enumerate(selected, 1):
            branch_path = args.branch_dir / str(branch["replay"])
            expected_sha256 = str(branch["replay_sha256"])
            output = args.output_dir / f"{branch['token']}.json"
            log = args.output_dir / f"{branch['token']}.log"
            if output.is_file():
                envelope = json.loads(output.read_text(encoding="utf-8"))
                compact = _trial_summary(
                    branch,
                    envelope,
                    report_path=output,
                )
                completed.append(compact)
                print(
                    f"resume {index}/{len(selected)} "
                    f"{branch['token']}: {compact['status']}",
                    flush=True,
                )
                continue

            _copy_verified(branch_path, slot, expected_sha256)
            command = (
                sys.executable,
                str(child_tool),
                "--armed",
                "--replay-slot",
                str(args.replay_slot),
                "--game-dir",
                str(args.game_dir),
                "--expected-replay-sha256",
                expected_sha256,
                "--output",
                str(output),
                "--timeout",
                str(args.timeout),
                "--poll-ms",
                "1",
                "--history-frames",
                str(args.history_frames),
                "--stop-frame",
                str(args.stop_frame),
            )
            try:
                with log.open("w", encoding="utf-8") as stream:
                    process = subprocess.run(
                        command,
                        stdout=stream,
                        stderr=subprocess.STDOUT,
                        check=False,
                    )
            finally:
                _copy_verified(
                    args.canonical_replay,
                    slot,
                    canonical_metadata.sha256,
                )
            if process.returncode != 0:
                raise RuntimeError(
                    f"native branch child failed for {branch['token']}; "
                    f"see {log}"
                )
            envelope = json.loads(output.read_text(encoding="utf-8"))
            compact = _trial_summary(
                branch,
                envelope,
                report_path=output,
            )
            completed.append(compact)
            report["branches"] = completed
            _write_report(args.report, report)
            print(
                f"completed {index}/{len(selected)} "
                f"{branch['token']}: {compact['status']}",
                flush=True,
            )
        report["finished_at"] = datetime.now().astimezone().isoformat()
        report["status"] = "completed"
        report["branch_count"] = len(completed)
        report["no_hit_witnesses"] = [
            branch["token"]
            for branch in completed
            if branch["status"] == "stop_frame_reached_without_hit"
        ]
        report["branches"] = completed
        _write_report(args.report, report)
        return 0
    except Exception as exc:
        report["finished_at"] = datetime.now().astimezone().isoformat()
        report["status"] = "failed"
        report["error_type"] = type(exc).__name__
        report["error"] = str(exc)
        report["branches"] = completed
        _write_report(args.report, report)
        raise
    finally:
        _copy_verified(
            args.canonical_replay,
            slot,
            canonical_metadata.sha256,
        )


if __name__ == "__main__":
    raise SystemExit(main())
