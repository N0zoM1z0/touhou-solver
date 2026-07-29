#!/usr/bin/env python3
"""Wait for Final-B spell 190 and retain one read-only scale-source trace."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from th08_live.scale_source_trace import (  # noqa: E402
    FINAL_B_ECL_STATIC_SHA256,
    FINAL_B_SCALE_SPELL_ID,
    FINAL_B_STAGE_ROUTE_INDEX,
    FinalBScaleSourceTraceConfiguration,
    FinalBScaleSourceTraceService,
)
from th08_runtime_agent import (  # noqa: E402
    ProcessReader,
    TARGET_EXE,
    Win32,
    observe_state,
    verify_target,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only Final-B spell-190 scale-source observer; this tool "
            "never sends input or changes foreground ownership"
        )
    )
    parser.add_argument("output", type=Path)
    parser.add_argument("--pid", type=int)
    parser.add_argument(
        "--static-ecl",
        type=Path,
        default=Path("artifacts/decoded/ecldata7.ecl"),
    )
    parser.add_argument(
        "--static-sha256",
        default=FINAL_B_ECL_STATIC_SHA256,
    )
    parser.add_argument("--timeout", type=float, default=1800.0)
    parser.add_argument("--poll-ms", type=float, default=2.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.timeout <= 0.0:
        raise ValueError("observer timeout must be positive")
    if args.poll_ms <= 0.0:
        raise ValueError("observer poll cadence must be positive")
    static_path = args.static_ecl
    if not static_path.is_absolute():
        static_path = Path(__file__).resolve().parents[2] / static_path
    service = FinalBScaleSourceTraceService(
        FinalBScaleSourceTraceConfiguration(
            static_path=static_path,
            expected_static_sha256=args.static_sha256,
        )
    )
    api = Win32()
    pid = args.pid if args.pid is not None else api.find_pid(TARGET_EXE)
    reader = ProcessReader(api, pid)
    started = time.perf_counter()
    identity: dict[str, object] | None = None
    record: dict[str, object] | None = None
    gameplay_epoch = 0
    prior_context: tuple[int, int] | None = None
    try:
        identity = verify_target(reader)
        deadline = started + args.timeout
        while time.perf_counter() < deadline:
            state = observe_state(reader)
            current_context = (
                int(state["route_id"]),
                int(state["stage_route_index"]),
            )
            if state["gameplay_active"] and current_context != prior_context:
                gameplay_epoch += 1
                prior_context = current_context
            elif not state["gameplay_active"]:
                prior_context = None
            spell = state["spell"]
            active_spell_id = (
                int(spell["spell_id"]) if spell["active"] else None
            )
            record = service.observe_if_due(
                reader,
                decision_frame=int(state["enemy_manager_frame"]),
                expected_manager_frame=int(state["enemy_manager_frame"]),
                gameplay_epoch=gameplay_epoch,
                route_id=int(state["route_id"]),
                difficulty_index=int(state["difficulty_index"]),
                stage_route_index=int(state["stage_route_index"]),
                spell_id=active_spell_id,
                observed_root_scale_bits=int(state["time_scale_bits"]),
                observed_player_bomb_active=int(
                    state["player"]["bomb_active"]
                ),
            )
            if record is not None:
                break
            time.sleep(args.poll_ms / 1000.0)
    finally:
        reader.close()
    if record is None:
        record = {
            "kind": "finalb_scale_source_trace",
            "status": "timeout",
            "authority": "trace_only_no_action_authority",
            "hard_action_authority": False,
            "changes_input": False,
            "target_stage_route_index": FINAL_B_STAGE_ROUTE_INDEX,
            "target_spell_id": FINAL_B_SCALE_SPELL_ID,
            "timeout_seconds": args.timeout,
        }
    envelope = {
        "observer": (
            "scripts/tools/th08_finalb_scale_source_observer.py"
        ),
        "pid": pid,
        "executable_identity": identity,
        "elapsed_seconds": time.perf_counter() - started,
        "record": record,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(envelope, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(envelope, sort_keys=True))
    return 0 if record.get("status") == "accepted_complete_source_trace" else 2


if __name__ == "__main__":
    raise SystemExit(main())
