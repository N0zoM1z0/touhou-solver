#!/usr/bin/env python3
"""Measure one native early-kill branch with the live global viability model."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from th08_corridor_adapter import (  # noqa: E402
    TH08_CORRIDOR_CONFIG,
    lower_th08_corridor_hazards,
    plan_prepared_lowered_th08_corridor,
    prepare_lowered_th08_corridor,
)
from th08_live.models import EnemyBody  # noqa: E402
from th08_live.movement import action_name_from_mask  # noqa: E402
from th08_time_scale import TH08_UNIT_TIME_SCALE_BITS  # noqa: E402
from th08_trace_replay import bullet_from_trace, laser_from_trace  # noqa: E402


SCHEMA = "th08-kill-before-saturation-viability-report-v1"
SOURCE_SCHEMA = "th08-native-snapshot-rolling-trial-v11"
BRANCHES = (("recorded", "a1"), ("refocus", "b"))


def _load(path: Path) -> tuple[dict[str, Any], dict[str, object]]:
    data = path.read_bytes()
    payload = json.loads(data)
    if not isinstance(payload, dict):
        raise ValueError("native early-kill source is not an object")
    return payload, {
        "path": path.as_posix(),
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
    }


def _tick(branch: dict[str, Any], frame: int) -> dict[str, Any]:
    matches = [
        tick
        for tick in branch["ticks"]
        if int(tick["compact_state"]["manager_frame"]) == frame
    ]
    if len(matches) != 1:
        raise ValueError(f"branch has {len(matches)} ticks at frame {frame}")
    return matches[0]


def _enemy_body(record: dict[str, Any]) -> EnemyBody:
    return EnemyBody(
        pointer=int(record["pointer"]),
        x=float(record["x"]),
        y=float(record["y"]),
        vx=float(record["vx"]),
        vy=float(record["vy"]),
        half_width=float(record["half_width"]),
        half_height=float(record["half_height"]),
        flags=int(record["flags"]),
        uncertainty=float(record["uncertainty"]),
        internal_vx=(
            None
            if record.get("internal_vx") is None
            else float(record["internal_vx"])
        ),
        internal_vy=(
            None
            if record.get("internal_vy") is None
            else float(record["internal_vy"])
        ),
    )


def _query_record(query: object) -> dict[str, object]:
    return {
        "available": bool(query.available),
        "state_viable": bool(query.state_viable),
        "safe_actions": list(query.safe_actions),
        "safe_action_count": int(query.safe_action_count),
        "repair_volumes": [
            [name, int(volume)] for name, volume in query.repair_volumes
        ],
        "recovery_distances": [
            [name, float(distance)]
            for name, distance in query.recovery_distances
        ],
        "position_error": float(query.position_error),
        "reason": str(query.reason),
    }


def _array_sha256(value: np.ndarray) -> str:
    array = np.ascontiguousarray(value)
    identity = (
        str(array.dtype).encode("ascii")
        + b"\0"
        + json.dumps(list(array.shape), separators=(",", ":")).encode("ascii")
        + b"\0"
        + array.tobytes()
    )
    return hashlib.sha256(identity).hexdigest()


def _measure_tick(
    tick: dict[str, Any],
    *,
    delay_frames: tuple[int, ...],
    nominal_delay: int,
) -> dict[str, object]:
    projection = tick["collision_control_projection"]
    payload = projection.get("model_payload")
    if not isinstance(payload, dict):
        raise ValueError("selected tick does not retain collision model payload")
    compact = tick["compact_state"]
    if int(compact["time_scale_bits"]) != TH08_UNIT_TIME_SCALE_BITS:
        raise ValueError("global viability comparison requires unit time scale")
    bullets = tuple(
        bullet_from_trace(values) for values in payload["bullets"]
    )
    lasers = tuple(
        laser_from_trace(values) for values in payload["lasers"]
    )
    enemy_bodies = tuple(
        _enemy_body(record) for record in payload["enemy_bodies"]
    )
    started = time.perf_counter()
    hazards = lower_th08_corridor_hazards(
        bullets=bullets,
        lasers=lasers,
        enemy_bodies=enemy_bodies,
        snapshot_lag=0,
        forecast_frames=0,
        horizon_frames=TH08_CORRIDOR_CONFIG.horizon_frames,
        laser_time_scale_bits=(
            (TH08_UNIT_TIME_SCALE_BITS,)
            * (TH08_CORRIDOR_CONFIG.horizon_frames + 1)
        ),
    )
    active_action = action_name_from_mask(int(compact["input_current"]))
    prepared = prepare_lowered_th08_corridor(
        hazards=hazards,
        control_delay_candidates=delay_frames,
        nominal_control_delay=nominal_delay,
        active_action=active_action,
        retain_query_survival_problem=False,
    )
    plan = plan_prepared_lowered_th08_corridor(
        player_x=float(compact["player_x"]),
        player_y=float(compact["player_y"]),
        prepared_problem=prepared,
    )
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    policy = plan.viability_policy
    if policy is None:
        raise ValueError("corridor plan did not retain its viability policy")
    query = policy.query(
        frame=0,
        x=float(compact["player_x"]),
        y=float(compact["player_y"]),
        active_action=active_action,
    )
    layer = np.asarray(policy.viable[0], dtype=np.bool_)
    nearest = projection["summary"]["nearest_bullets"][0]
    return {
        "manager_frame": int(compact["manager_frame"]),
        "player": {
            "x": float(compact["player_x"]),
            "y": float(compact["player_y"]),
            "phase": int(compact["player_phase"]),
        },
        "active_action": active_action,
        "active_bullet_count": len(bullets),
        "active_enemy_body_count": len(enemy_bodies),
        "nearest_signed_box_separation": float(
            nearest["signed_box_separation"]
        ),
        "plan": {
            "reachable": bool(plan.reachable),
            "reason": str(plan.reason),
            "initial_safe_action_count": int(
                plan.initial_safe_action_count
            ),
            "initial_repair_volume": int(plan.initial_repair_volume),
            "bottleneck_clearance": float(plan.bottleneck_clearance),
            "terminal_clearance": float(plan.terminal_clearance),
            "viability_backend": plan.viability_backend,
        },
        "query": _query_record(query),
        "kernel_layer0": {
            "viable_state_count": int(np.count_nonzero(layer)),
            "viable_position_union_count": int(
                np.count_nonzero(np.any(layer, axis=0))
            ),
            "total_state_count": int(layer.size),
            "total_position_count": int(layer.shape[1] * layer.shape[2]),
            "viable_sha256": _array_sha256(layer),
            "safe_action_masks_sha256": _array_sha256(
                policy.safe_action_masks[0]
            ),
        },
        "clearance_volume_sha256": _array_sha256(
            prepared.clearance_volume
        ),
        "timing_ms": elapsed_ms,
    }


def build_report(
    source: dict[str, Any],
    source_record: dict[str, object],
    *,
    frames: tuple[int, ...],
    delay_frames: tuple[int, ...],
    nominal_delay: int,
) -> dict[str, object]:
    if source.get("schema") != SOURCE_SCHEMA:
        raise ValueError("source is not a lifecycle-aware rolling trial")
    result = source.get("result")
    if not isinstance(result, dict):
        raise ValueError("source has no result object")
    if result.get("status") != "rolling_native_projection_snapshot_passed":
        raise ValueError("source rolling transaction did not pass")
    for field in (
        "same_action_enemy_lifecycle_exact",
        "same_action_collision_control_projection_exact",
        "same_action_native_combat_projection_exact",
    ):
        if result.get(field) is not True:
            raise ValueError(f"source does not satisfy {field}")
    branches = result["branches"]
    measurements: dict[str, list[dict[str, object]]] = {}
    for label, key in BRANCHES:
        branch = branches[key]
        measurements[label] = [
            _measure_tick(
                _tick(branch, frame),
                delay_frames=delay_frames,
                nominal_delay=nominal_delay,
            )
            for frame in frames
        ]

    comparisons = []
    for index, frame in enumerate(frames):
        recorded = measurements["recorded"][index]
        refocus = measurements["refocus"][index]
        comparisons.append(
            {
                "manager_frame": frame,
                "active_bullet_delta_refocus_minus_recorded": (
                    int(refocus["active_bullet_count"])
                    - int(recorded["active_bullet_count"])
                ),
                "viable_state_delta_refocus_minus_recorded": (
                    int(refocus["kernel_layer0"]["viable_state_count"])
                    - int(recorded["kernel_layer0"]["viable_state_count"])
                ),
                "viable_position_union_delta_refocus_minus_recorded": (
                    int(
                        refocus["kernel_layer0"][
                            "viable_position_union_count"
                        ]
                    )
                    - int(
                        recorded["kernel_layer0"][
                            "viable_position_union_count"
                        ]
                    )
                ),
                "recorded_state_viable": bool(
                    recorded["query"]["state_viable"]
                ),
                "refocus_state_viable": bool(
                    refocus["query"]["state_viable"]
                ),
                "safe_action_count_delta_refocus_minus_recorded": (
                    int(refocus["query"]["safe_action_count"])
                    - int(recorded["query"]["safe_action_count"])
                ),
                "clearance_volume_exact": (
                    refocus["clearance_volume_sha256"]
                    == recorded["clearance_volume_sha256"]
                ),
                "viable_mask_exact": (
                    refocus["kernel_layer0"]["viable_sha256"]
                    == recorded["kernel_layer0"]["viable_sha256"]
                ),
                "safe_action_masks_exact": (
                    refocus["kernel_layer0"]["safe_action_masks_sha256"]
                    == recorded["kernel_layer0"][
                        "safe_action_masks_sha256"
                    ]
                ),
            }
        )
    b_events = [
        event
        for tick in branches["b"]["ticks"]
        for event in (tick["enemy_lifecycle_batch"] or {}).get("events", ())
    ]
    return {
        "schema": SCHEMA,
        "status": "same_root_native_kill_with_live_viability_model_measured",
        "source": source_record,
        "root_manager_frame": int(result["root_compact_state"]["manager_frame"]),
        "frames": list(frames),
        "control_delay": {
            "support": list(delay_frames),
            "nominal": nominal_delay,
            "provenance": (
                "retained physical Stage-5 decisions around frames 4299..4331"
            ),
        },
        "planner_contract": {
            "grid_step": TH08_CORRIDOR_CONFIG.grid_step,
            "frames_per_layer": TH08_CORRIDOR_CONFIG.frames_per_layer,
            "horizon_frames": TH08_CORRIDOR_CONFIG.horizon_frames,
            "action_count": 17,
            "projection_authority": (
                "live global viability model applied independently to each "
                "exact native branch snapshot"
            ),
            "native_future_authority": False,
        },
        "native_causal_event": {
            "events": [
                event
                for event in b_events
                if int(event["manager_frame"]) == 4308
            ],
            "recorded_branch_event_count": sum(
                len((tick["enemy_lifecycle_batch"] or {}).get("events", ()))
                for tick in branches["a1"]["ticks"]
            ),
        },
        "measurements": measurements,
        "comparisons": comparisons,
        "authority": {
            "observed": (
                "same-root original-engine damage, defeat, and hostile "
                "projectile-state differences through manager frame 4332"
            ),
            "inferred": (
                "the killed enemy accounts for the 3/6/9 cadence-aligned "
                "active-bullet deficit"
            ),
            "modeled": (
                "80-frame global viability outcomes from each retained native "
                "snapshot under the current live planner contract"
            ),
            "not_proved": (
                "cross-root or physical full-route improvement"
            ),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--frames",
        default="4314,4323,4332",
        help="comma-separated retained manager frames",
    )
    parser.add_argument("--delay-frames", default="2,3,4")
    parser.add_argument("--nominal-delay", type=int, default=2)
    args = parser.parse_args(argv)
    frames = tuple(int(value) for value in args.frames.split(","))
    delay_frames = tuple(
        int(value) for value in args.delay_frames.split(",")
    )
    if not frames or tuple(sorted(set(frames))) != frames:
        raise ValueError("frames must be sorted and unique")
    if (
        not delay_frames
        or tuple(sorted(set(delay_frames))) != delay_frames
        or args.nominal_delay not in delay_frames
    ):
        raise ValueError("delay support and nominal delay are invalid")
    source, source_record = _load(args.source)
    report = build_report(
        source,
        source_record,
        frames=frames,
        delay_frames=delay_frames,
        nominal_delay=args.nominal_delay,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    print(f"kill-before-saturation report: {args.output}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
