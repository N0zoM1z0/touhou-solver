#!/usr/bin/env python3
"""Build all 36 no-Bomb native-replay branches from one immutable prefix."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

from th08_movement_model import INPUT_BOMB
from th08_pipeline_actions import TH08_COMPLETE_MASK_ACTION_SPACE
from th08_replay import (
    ReplayStage,
    decode_replay,
    encode_replay,
    extract_stage_inputs,
    replace_stage_inputs,
)


SCHEMA = "th08-native-replay-causal-branch-corpus-v1"


def _input_sha256(inputs: tuple[int, ...]) -> str:
    payload = b"".join(struct.pack("<H", value) for value in inputs)
    return hashlib.sha256(payload).hexdigest()


def _stage(
    stages: tuple[ReplayStage, ...],
    stage_index: int,
) -> ReplayStage:
    matches = tuple(
        stage for stage in stages if stage.stage_index == stage_index
    )
    if len(matches) != 1:
        raise ValueError(
            f"replay must contain exactly one stage {stage_index} record"
        )
    return matches[0]


def build_causal_branch_corpus(
    source: Path,
    output_dir: Path,
    *,
    stage_index: int,
    root_frame: int,
    hold_frames: int,
) -> dict[str, object]:
    """Emit immutable replay inputs whose worlds are recomputed by TH08."""

    if root_frame < 0:
        raise ValueError("root frame must be nonnegative")
    if hold_frames <= 0:
        raise ValueError("hold frames must be positive")

    metadata, decoded = decode_replay(source)
    stage = _stage(metadata.stages, stage_index)
    if stage.bomb_press_frames:
        raise ValueError("source stage contains Bomb presses")
    if root_frame + hold_frames > stage.frame_count:
        raise ValueError("branch interval exceeds source stage")

    actions = TH08_COMPLETE_MASK_ACTION_SPACE.actions
    if len(actions) != 36 or len(
        {action.complete_mask for action in actions}
    ) != 36:
        raise RuntimeError("TH08 complete-mask alphabet is not exactly 36")
    if any(action.complete_mask & INPUT_BOMB for action in actions):
        raise RuntimeError("complete-mask alphabet contains Bomb")

    source_inputs = extract_stage_inputs(decoded, stage)
    prefix_sha256 = _input_sha256(source_inputs[:root_frame])
    suffix_sha256 = _input_sha256(
        source_inputs[root_frame + hold_frames :]
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    branches: list[dict[str, object]] = []

    for action in actions:
        masks = (action.complete_mask,) * hold_frames
        branch_decoded = replace_stage_inputs(
            decoded,
            stage,
            start_frame=root_frame,
            input_masks=masks,
        )
        branch_raw = encode_replay(branch_decoded)
        branch_path = output_dir / f"{action.token}.rpy"
        branch_path.write_bytes(branch_raw)

        verified_metadata, verified_decoded = decode_replay(branch_path)
        verified_stage = _stage(verified_metadata.stages, stage_index)
        verified_inputs = extract_stage_inputs(
            verified_decoded,
            verified_stage,
        )
        if verified_inputs[:root_frame] != source_inputs[:root_frame]:
            raise RuntimeError("branch changed its immutable input prefix")
        if (
            verified_inputs[root_frame : root_frame + hold_frames]
            != masks
        ):
            raise RuntimeError("branch input interval failed round trip")
        if (
            verified_inputs[root_frame + hold_frames :]
            != source_inputs[root_frame + hold_frames :]
        ):
            raise RuntimeError("branch changed its declared continuation")
        if any(mask & INPUT_BOMB for mask in verified_inputs):
            raise RuntimeError("branch replay contains Bomb")

        branches.append(
            {
                "token": action.token,
                "complete_mask": action.complete_mask,
                "movement_label": action.movement_label,
                "replay": branch_path.name,
                "replay_sha256": verified_metadata.sha256,
                "stage_input_sha256": verified_stage.input_sha256,
            }
        )

    return {
        "schema": SCHEMA,
        "source": source.as_posix(),
        "source_sha256": metadata.sha256,
        "route_id": metadata.route_id,
        "difficulty_index": metadata.difficulty_index,
        "stage_index": stage_index,
        "stage_rng_seed": stage.rng_seed,
        "stage_frame_count": stage.frame_count,
        "source_stage_input_sha256": stage.input_sha256,
        "root_frame": root_frame,
        "hold_frames": hold_frames,
        "immutable_prefix_input_sha256": prefix_sha256,
        "unchanged_continuation_input_sha256": suffix_sha256,
        "branch_count": len(branches),
        "recorded_future_world_reused": False,
        "future_world_executor": "original_th08_executable",
        "future_rng_contract": (
            "same root RNG; each native branch consumes RNG endogenously"
        ),
        "continuation_contract": (
            "selected complete mask is held for the declared interval; "
            "the source replay input stream is then an explicit open-loop "
            "continuation, while native world state is never replayed"
        ),
        "physical_authority": False,
        "branches": branches,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("report", type=Path)
    parser.add_argument("--stage-index", type=int, required=True)
    parser.add_argument("--root-frame", type=int, required=True)
    parser.add_argument("--hold-frames", type=int, default=1)
    args = parser.parse_args(argv)

    report = build_causal_branch_corpus(
        args.source,
        args.output_dir,
        stage_index=args.stage_index,
        root_frame=args.root_frame,
        hold_frames=args.hold_frames,
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
