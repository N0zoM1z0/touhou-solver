#!/usr/bin/env python3
"""Project TH08 route-2 replay controls through the recovered player runtime.

The output is a compact, derived state summary. Accepted Bomb starts are
explicit because the replay stream cannot reveal hit/Last-Spell state or item
stock changes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

from th08_movement_model import INPUT_BOMB
from th08_replay import ReplayStage, decode_replay, extract_stage_inputs
from th08_route2_player_runtime import (
    BombStartKind,
    Route2PlayerState,
)
from th08_simulator import (
    Th08Route2FrameControl,
    initial_route2_simulation_state,
    route2_player_executor,
)


def _bomb_press_frames(inputs: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(
        frame
        for frame, mask in enumerate(inputs)
        if mask & INPUT_BOMB and (frame == 0 or not inputs[frame - 1] & INPUT_BOMB)
    )


def _checkpoint(state: Route2PlayerState, input_mask: int) -> dict[str, object]:
    return {
        "frame_exclusive": state.frame_index,
        "input_mask": input_mask,
        "x": state.x,
        "y": state.y,
        "phase": int(state.phase),
        "state_timer": state.state_timer_elapsed,
        "focus_logic_value": state.focus.focus_logic_value,
        "remilia_character_active": state.focus.remilia_character_active,
        "bomb_index": int(state.bomb.profile.index) if state.bomb else None,
        "bomb_timer": state.bomb.timer_elapsed if state.bomb else None,
        "bomb_stock": state.bombs,
    }


def project_route2_inputs(
    inputs: tuple[int, ...],
    *,
    starting_bombs: int,
    bomb_starts: dict[int, BombStartKind] | None = None,
    short_spawn_mode: bool = False,
    checkpoint_period: int = 600,
) -> dict[str, object]:
    """Return a deterministic summary of one explicit external-event scenario."""

    if checkpoint_period <= 0:
        raise ValueError("checkpoint period must be positive")
    starts = dict(bomb_starts or {})
    invalid_frames = sorted(frame for frame in starts if not 0 <= frame < len(inputs))
    if invalid_frames:
        raise ValueError(f"Bomb start frames outside input extent: {invalid_frames}")

    press_frames = _bomb_press_frames(inputs)
    non_press_events = sorted(frame for frame in starts if frame not in press_frames)
    if non_press_events:
        raise ValueError(
            f"accepted Bomb starts are not input rising edges: {non_press_events}"
        )

    simulation_state = initial_route2_simulation_state(
        bombs=starting_bombs, short_spawn_mode=short_spawn_mode
    )
    executor = route2_player_executor()
    state = simulation_state.player
    position_hash = hashlib.sha256()
    min_x = max_x = state.x
    min_y = max_y = state.y
    checkpoint_frames = {
        0,
        len(inputs) - 1,
        *(frame for frame in range(0, len(inputs), checkpoint_period)),
        *(nearby for frame in press_frames for nearby in (frame - 1, frame, frame + 1)),
    }
    checkpoint_frames = {
        frame for frame in checkpoint_frames if 0 <= frame < len(inputs)
    }
    checkpoints = []
    observed_starts = []
    observed_ends = []

    for frame, input_mask in enumerate(inputs):
        requested = starts.get(frame)
        execution = executor.step(
            simulation_state,
            Th08Route2FrameControl(input_mask, requested),
            frame_index=frame,
        )
        simulation_state = execution.state
        if requested is not None and simulation_state.last_bomb_started is None:
            raise ValueError(f"Bomb start at frame {frame} occurs while one is active")
        state = simulation_state.player
        position_hash.update(struct.pack("<ff", state.x, state.y))
        min_x = min(min_x, state.x)
        max_x = max(max_x, state.x)
        min_y = min(min_y, state.y)
        max_y = max(max_y, state.y)
        if simulation_state.last_bomb_started is not None:
            observed_starts.append(
                {
                    "frame": frame,
                    "kind": requested.value,
                    "index": int(simulation_state.last_bomb_started.index),
                    "name": simulation_state.last_bomb_started.display_name,
                }
            )
        if simulation_state.last_bomb_ended is not None:
            observed_ends.append(
                {
                    "frame": frame,
                    "index": int(simulation_state.last_bomb_ended.index),
                }
            )
        if frame in checkpoint_frames:
            checkpoints.append(_checkpoint(state, input_mask))

    unresolved = sorted(set(press_frames) - set(starts))
    return {
        "model": "th08_integrated_route2_player_v2",
        "frame_count": len(inputs),
        "starting_bombs": starting_bombs,
        "short_spawn_mode": short_spawn_mode,
        "position_f32_sha256": position_hash.hexdigest(),
        "position_bounds": {
            "min_x": min_x,
            "max_x": max_x,
            "min_y": min_y,
            "max_y": max_y,
        },
        "accepted_bomb_starts": observed_starts,
        "bomb_ends": observed_ends,
        "unresolved_bomb_press_frames": unresolved,
        "assumptions": [
            "time_scale remains 1.0",
            "no hostile-hit, death, respawn, or item-stock event is injected",
            "an unresolved Bomb press is treated as not accepted",
        ],
        "final_state": _checkpoint(state, inputs[-1] if inputs else 0),
        "checkpoints": checkpoints,
    }


def _parse_bomb_start(value: str) -> tuple[int, BombStartKind]:
    try:
        frame_text, kind_text = value.split(":", 1)
        return int(frame_text, 0), BombStartKind(kind_text)
    except (ValueError, KeyError) as exc:
        kinds = ", ".join(kind.value for kind in BombStartKind)
        raise argparse.ArgumentTypeError(
            f"Bomb start must be FRAME:KIND where KIND is {kinds}"
        ) from exc


def _find_stage(stages: tuple[ReplayStage, ...], index: int) -> ReplayStage:
    try:
        return next(stage for stage in stages if stage.stage_index == index)
    except StopIteration as exc:
        raise ValueError(f"replay has no stage index {index}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("replay", type=Path)
    parser.add_argument("stage_index", type=int)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--bomb-start",
        action="append",
        default=[],
        type=_parse_bomb_start,
        metavar="FRAME:KIND",
    )
    parser.add_argument("--short-spawn-mode", action="store_true")
    args = parser.parse_args(argv)

    metadata, decoded = decode_replay(args.replay)
    if metadata.route_id != 2:
        parser.error(f"route ID {metadata.route_id} is not Sakuya/Remilia route 2")
    stage = _find_stage(metadata.stages, args.stage_index)
    starts = dict(args.bomb_start)
    if len(starts) != len(args.bomb_start):
        parser.error("a Bomb start frame was specified more than once")
    projection = project_route2_inputs(
        extract_stage_inputs(decoded, stage),
        starting_bombs=stage.bombs,
        bomb_starts=starts,
        short_spawn_mode=args.short_spawn_mode,
    )
    report = {
        "source_replay": metadata.name,
        "source_sha256": metadata.sha256,
        "route_id": metadata.route_id,
        "difficulty_index": metadata.difficulty_index,
        "stage_index": stage.stage_index,
        "rng_seed": stage.rng_seed,
        "input_sha256": stage.input_sha256,
        **projection,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(
        f"{metadata.name} stage {stage.stage_index}: {stage.frame_count} frames, "
        f"{len(report['unresolved_bomb_press_frames'])} unresolved Bomb presses"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
