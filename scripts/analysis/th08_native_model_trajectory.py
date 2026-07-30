#!/usr/bin/env python3
"""Replay one retained native capsule through explicit model layers."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from movement_model import MovementBounds
from numeric_model import binary32_store
from th08_ecl_vm_state import float32_bits
from th08_enemy_mode import step_route2_enemy_mode_state
from th08_live.local_hazards import _build_bullet_frames
from th08_live.models import Bullet
from th08_movement_model import (
    INPUT_BOMB,
    TH08_PLAYFIELD_BOUNDS,
    TH08_PLAYER_CENTER_BOUNDS_SEMANTICS_VERSION,
    TH08_ROUTE2_MOVEMENT_SCALE_SEMANTICS_VERSION,
    step_route2_movement,
)


SCHEMA = "th08-native-model-trajectory-differential-v1"
PLAYER_LAYER = "player_mechanics"
HAZARD_LAYER = "constant_velocity_bullet_forecast"
LEGACY_EXTENT_BOUNDS = MovementBounds(0.0, 0.0, 384.0, 448.0)
DEFAULT_CAUSAL_REPORT = Path(
    "artifacts/runtime_reports/"
    "th08_native_snapshot_causal_policy_root2129_h32_20260730.json"
)
DEFAULT_WITNESS = Path(
    "artifacts/native_snapshot_rolling/raw/"
    "th08_schedule_94_44_10_a4_h32_natural_20260730.json"
)
DEFAULT_OUTPUT = Path(
    "artifacts/runtime_reports/"
    "th08_native_model_trajectory_root2129_h32_20260730.json"
)
DEFAULT_CAUSAL_REPORT_SHA256 = (
    "69e6ec2db0f5415a6ee8231808be0669b0f80006faf299f2c90aeb27e221bbaa"
)
DEFAULT_WITNESS_SHA256 = (
    "97ed8c6006be09e6f68bf24c3722ecb74a110e57640940012ec8ee704a08b349"
)


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _content_artifact(kind: str, payload: dict[str, object]) -> dict[str, object]:
    body = {"kind": kind, "payload": payload}
    return {
        "artifact_id": f"sha256:{hashlib.sha256(_canonical_bytes(body)).hexdigest()}",
        **body,
    }


def _load_object(
    path: Path,
    *,
    expected_sha256: str | None,
) -> tuple[dict[str, Any], dict[str, object]]:
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if expected_sha256 is not None and digest != expected_sha256:
        raise ValueError(
            f"{path} sha256 mismatch: expected {expected_sha256}, got {digest}"
        )
    value = json.loads(data)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain one JSON object")
    return value, {"path": str(path), "sha256": digest, "bytes": len(data)}


def _object(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _list(value: object, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a list")
    return value


def _integer(value: object, label: str) -> int:
    if type(value) is not int:
        raise ValueError(f"{label} must be an integer")
    return value


def _number(value: object, label: str) -> float:
    if type(value) not in (int, float):
        raise ValueError(f"{label} must be a number")
    return float(value)


def _boolean(value: object, label: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{label} must be a Boolean")
    return value


def _validate_content_artifact(
    artifact: object,
    *,
    expected_kind: str,
) -> dict[str, Any]:
    value = _object(artifact, expected_kind)
    if value.get("kind") != expected_kind:
        raise ValueError(f"expected {expected_kind} content artifact")
    payload = _object(value.get("payload"), f"{expected_kind}.payload")
    expected = _content_artifact(expected_kind, payload)["artifact_id"]
    if value.get("artifact_id") != expected:
        raise ValueError(f"{expected_kind} artifact id does not match its payload")
    return value


def _collision_summary(tick: dict[str, Any]) -> dict[str, Any]:
    projection = _object(
        tick.get("collision_control_projection"),
        "native tick collision_control_projection",
    )
    return _object(projection.get("summary"), "collision projection summary")


def _find_bullet(summary: dict[str, Any], slot: int) -> dict[str, Any]:
    bullets = _list(summary.get("nearest_bullets"), "nearest_bullets")
    matches = [
        _object(bullet, "nearest bullet")
        for bullet in bullets
        if isinstance(bullet, dict) and bullet.get("slot") == slot
    ]
    if len(matches) != 1:
        raise ValueError(
            f"expected exactly one retained nearest-bullet sample for slot {slot}"
        )
    return matches[0]


def _bounds_payload(bounds: MovementBounds) -> dict[str, float]:
    return {
        "left": bounds.left,
        "top": bounds.top,
        "right": bounds.right,
        "bottom": bounds.bottom,
    }


def _float_value(value: float) -> dict[str, object]:
    stored = binary32_store(value)
    return {"value": stored, "bits": float32_bits(stored)}


def _first_tick_mismatch(ticks: list[dict[str, Any]]) -> dict[str, object] | None:
    for tick in ticks:
        fields = tick["mismatched_fields"]
        if fields:
            return {
                "tick_index": tick["tick_index"],
                "manager_frame": tick["manager_frame"],
                "fields": fields,
                "model": tick["model"],
                "native": tick["native"],
            }
    return None


def _resolve_inputs(
    schedule: list[Any],
    compact_ticks: list[dict[str, Any]],
    raw_ticks: list[dict[str, Any]],
) -> list[tuple[int, str]]:
    if not (len(schedule) == len(compact_ticks) == len(raw_ticks)):
        raise ValueError("schedule, NativeTrajectory, and raw witness lengths differ")
    resolved: list[tuple[int, str]] = []
    for index, (entry, compact_tick, raw_tick) in enumerate(
        zip(schedule, compact_ticks, raw_ticks, strict=True)
    ):
        selected = _integer(
            compact_tick.get("selected_action"),
            f"NativeTrajectory tick {index} selected_action",
        )
        raw_selected = _integer(
            raw_tick.get("selected_action"),
            f"raw tick {index} selected_action",
        )
        raw_recorded = _integer(
            raw_tick.get("recorded_action"),
            f"raw tick {index} recorded_action",
        )
        recorded = _integer(
            compact_tick.get("recorded_action"),
            f"NativeTrajectory tick {index} recorded_action",
        )
        if raw_selected != selected or raw_recorded != recorded:
            raise ValueError(f"raw/native action mismatch at tick {index}")
        if entry is None:
            action = selected
            source = "NativeTrajectory.selected_action"
            if selected != recorded:
                raise ValueError(
                    f"null schedule tick {index} does not resolve to recorded action"
                )
        else:
            action = _integer(entry, f"schedule tick {index}")
            source = "PolicySchedule.explicit_action"
            if action != selected:
                raise ValueError(
                    f"schedule action does not match NativeTrajectory at tick {index}"
                )
        if not 0 <= action <= 0xFFFF:
            raise ValueError(f"action at tick {index} is outside u16")
        if action & INPUT_BOMB:
            raise ValueError(f"Bomb action is forbidden at tick {index}")
        resolved.append((action, source))
    return resolved


def _player_trajectory(
    *,
    root: dict[str, Any],
    compact_ticks: list[dict[str, Any]],
    raw_ticks: list[dict[str, Any]],
    inputs: list[tuple[int, str]],
    bounds: MovementBounds,
) -> dict[str, object]:
    x = _number(root.get("player_x"), "root player_x")
    y = _number(root.get("player_y"), "root player_y")
    current_input = _integer(root.get("input_current"), "root input_current")
    phase = _integer(root.get("player_phase"), "root player_phase")
    time_scale_bits = _integer(root.get("time_scale_bits"), "root time_scale_bits")
    mode = (
        _integer(root.get("focus_logic"), "root focus_logic"),
        _boolean(
            root.get("secondary_character_active"),
            "root secondary_character_active",
        ),
        _integer(
            root.get("focus_transition_counter"),
            "root focus_transition_counter",
        ),
    )
    ticks: list[dict[str, Any]] = []
    for index, ((action, action_source), compact_tick, raw_tick) in enumerate(
        zip(inputs, compact_ticks, raw_ticks, strict=True)
    ):
        native = _object(raw_tick.get("compact_state"), f"raw tick {index} state")
        manager_frame = _integer(
            compact_tick.get("manager_frame"),
            f"NativeTrajectory tick {index} manager_frame",
        )
        native_manager_frame = _integer(
            native.get("manager_frame"), "native manager_frame"
        )
        if native_manager_frame != manager_frame:
            raise ValueError(f"manager-frame mismatch at tick {index}")
        for field in ("player_x", "player_y", "player_phase"):
            if compact_tick.get(field) != native.get(field):
                raise ValueError(
                    f"compact NativeTrajectory differs from raw {field} at tick {index}"
                )
        if native.get("time_scale_bits") != time_scale_bits:
            raise ValueError(
                "fixture leaves the root time-scale identity; an explicit model "
                f"schedule is required at tick {index}"
            )

        step = step_route2_movement(
            x=x,
            y=y,
            input_mask=action,
            time_scale_bits=time_scale_bits,
            bounds=bounds,
        )
        mode = step_route2_enemy_mode_state(
            mode,
            focused=bool(action & 0x04),
        )
        model = {
            "player_x": _float_value(step.x),
            "player_y": _float_value(step.y),
            "input_current": action,
            "input_previous": current_input,
            "focus_logic": mode[0],
            "secondary_character_active": mode[1],
            "focus_transition_counter": mode[2],
            "player_phase": phase,
        }
        native_subset = {
            "player_x": _float_value(
                _number(native.get("player_x"), "native player_x")
            ),
            "player_y": _float_value(
                _number(native.get("player_y"), "native player_y")
            ),
            "input_current": _integer(
                native.get("input_current"), "native input_current"
            ),
            "input_previous": _integer(
                native.get("input_previous"), "native input_previous"
            ),
            "focus_logic": _integer(
                native.get("focus_logic"), "native focus_logic"
            ),
            "secondary_character_active": _boolean(
                native.get("secondary_character_active"),
                "native secondary_character_active",
            ),
            "focus_transition_counter": _integer(
                native.get("focus_transition_counter"),
                "native focus_transition_counter",
            ),
            "player_phase": _integer(
                native.get("player_phase"), "native player_phase"
            ),
        }
        mismatched = [
            field
            for field in model
            if model[field] != native_subset[field]
        ]
        ticks.append(
            {
                "tick_index": index,
                "manager_frame": manager_frame,
                "resolved_action": action,
                "action_source": action_source,
                "model": model,
                "native": native_subset,
                "mismatched_fields": mismatched,
            }
        )
        x, y = step.x, step.y
        current_input = action
    first_mismatch = _first_tick_mismatch(ticks)
    return {
        "layer": PLAYER_LAYER,
        "bounds": _bounds_payload(bounds),
        "tick_count": len(ticks),
        "exact_tick_count": sum(not tick["mismatched_fields"] for tick in ticks),
        "status": "exact" if first_mismatch is None else "mismatch",
        "first_mismatch": first_mismatch,
        "ticks": ticks,
    }


def _hazard_probe(
    *,
    root_summary: dict[str, Any],
    raw_ticks: list[dict[str, Any]],
    slot: int = 45,
    horizon: int = 3,
) -> dict[str, object]:
    root_bullet = _find_bullet(root_summary, slot)
    native_bullets = [
        _find_bullet(_collision_summary(tick), slot)
        for tick in raw_ticks[:horizon]
    ]
    bullet = Bullet(
        x=_number(root_bullet.get("x"), "root bullet x"),
        y=_number(root_bullet.get("y"), "root bullet y"),
        vx=_number(root_bullet.get("vx"), "root bullet vx"),
        vy=_number(root_bullet.get("vy"), "root bullet vy"),
        half_width=_number(root_bullet.get("half_width"), "root bullet half_width"),
        half_height=_number(
            root_bullet.get("half_height"), "root bullet half_height"
        ),
        transform_flags=_integer(
            root_bullet.get("transform_flags"), "root bullet transform_flags"
        ),
        slot=slot,
    )
    production_frames = _build_bullet_frames(
        (bullet,),
        horizon=horizon,
        snapshot_lag=0,
    )
    base_x = binary32_store(bullet.x)
    base_y = binary32_store(bullet.y)
    velocity_x = binary32_store(bullet.vx)
    velocity_y = binary32_store(bullet.vy)
    repeated_x = base_x
    repeated_y = base_y
    ticks: list[dict[str, Any]] = []
    for index, (frame, native) in enumerate(
        zip(production_frames, native_bullets, strict=True)
    ):
        elapsed = index + 1
        legacy_x = binary32_store(
            base_x + binary32_store(velocity_x * elapsed)
        )
        legacy_y = binary32_store(
            base_y + binary32_store(velocity_y * elapsed)
        )
        repeated_x = binary32_store(repeated_x + velocity_x)
        repeated_y = binary32_store(repeated_y + velocity_y)
        manager_frame = _integer(
            raw_ticks[index]["compact_state"]["manager_frame"],
            "hazard manager_frame",
        )
        values = {
            "legacy_closed_form": {
                "x": _float_value(legacy_x),
                "y": _float_value(legacy_y),
            },
            "independent_repeated_binary32_oracle": {
                "x": _float_value(repeated_x),
                "y": _float_value(repeated_y),
            },
            "production": {
                "x": _float_value(float(frame[0][0])),
                "y": _float_value(float(frame[1][0])),
            },
            "native": {
                "x": _float_value(
                    _number(native.get("x"), "native bullet x")
                ),
                "y": _float_value(
                    _number(native.get("y"), "native bullet y")
                ),
            },
        }
        mismatch = {
            name: [
                axis
                for axis in ("x", "y")
                if projection[axis] != values["native"][axis]
            ]
            for name, projection in values.items()
            if name != "native"
        }
        ticks.append(
            {
                "tick_index": index,
                "manager_frame": manager_frame,
                "elapsed_updates": elapsed,
                **values,
                "mismatched_axes": mismatch,
            }
        )

    def first_mismatch(name: str) -> dict[str, object] | None:
        for tick in ticks:
            axes = tick["mismatched_axes"][name]
            if axes:
                return {
                    "tick_index": tick["tick_index"],
                    "manager_frame": tick["manager_frame"],
                    "axes": axes,
                    "projected": tick[name],
                    "native": tick["native"],
                }
        return None

    return {
        "layer": HAZARD_LAYER,
        "slot": slot,
        "root_manager_frame": _integer(
            raw_ticks[0]["compact_state"]["manager_frame"],
            "first hazard manager frame",
        )
        - 1,
        "horizon": horizon,
        "event_class": "constant_velocity_no_transform",
        "legacy_closed_form": {
            "status": "mismatch",
            "first_mismatch": first_mismatch("legacy_closed_form"),
            "error_safety_direction": "unknown_geometry_dependent",
        },
        "independent_repeated_binary32_oracle": {
            "status": (
                "exact"
                if first_mismatch("independent_repeated_binary32_oracle") is None
                else "mismatch"
            ),
            "first_mismatch": first_mismatch(
                "independent_repeated_binary32_oracle"
            ),
        },
        "production": {
            "status": (
                "exact" if first_mismatch("production") is None else "mismatch"
            ),
            "first_mismatch": first_mismatch("production"),
        },
        "ticks": ticks,
    }


def build_report(
    causal_report_path: Path,
    witness_path: Path,
    *,
    expected_causal_sha256: str | None = None,
    expected_witness_sha256: str | None = None,
) -> dict[str, object]:
    causal, causal_source = _load_object(
        causal_report_path,
        expected_sha256=expected_causal_sha256,
    )
    witness, witness_source = _load_object(
        witness_path,
        expected_sha256=expected_witness_sha256,
    )
    if causal.get("schema") != "th08-native-snapshot-causal-policy-evidence-v1":
        raise ValueError("unexpected causal evidence schema")
    if witness.get("schema") != "th08-native-snapshot-rolling-trial-v2":
        raise ValueError("unexpected native witness schema")

    sources = _list(causal.get("sources"), "causal sources")
    retained_witness = [
        _object(source, "causal source")
        for source in sources
        if isinstance(source, dict)
        and Path(str(source.get("path"))).name == witness_path.name
    ]
    if len(retained_witness) != 1:
        raise ValueError("causal report does not identify exactly one witness source")
    if retained_witness[0].get("sha256") != witness_source["sha256"]:
        raise ValueError("witness sha256 disagrees with causal report")

    artifacts = _object(causal.get("artifacts"), "causal artifacts")
    root_artifact = _validate_content_artifact(
        artifacts.get("native_root_capsule"),
        expected_kind="NativeRootCapsule",
    )
    native_artifact = _validate_content_artifact(
        artifacts.get("native_trajectory"),
        expected_kind="NativeTrajectory",
    )
    root_payload = _object(root_artifact["payload"], "NativeRootCapsule.payload")
    native_payload = _object(
        native_artifact["payload"], "NativeTrajectory.payload"
    )
    if native_payload.get("root_artifact_id") != root_artifact["artifact_id"]:
        raise ValueError("NativeTrajectory is not bound to NativeRootCapsule")

    result = _object(witness.get("result"), "witness result")
    root = _object(root_payload.get("root_compact_state"), "root compact state")
    if result.get("root_compact_state") != root:
        raise ValueError("raw witness root differs from NativeRootCapsule")
    branch = _object(
        _object(result.get("branches"), "witness branches").get("b"),
        "witness branch b",
    )
    schedule = _list(native_payload.get("action_schedule"), "action schedule")
    if branch.get("action_schedule") != schedule:
        raise ValueError("raw witness schedule differs from NativeTrajectory")
    compact_ticks = [
        _object(tick, "NativeTrajectory tick")
        for tick in _list(native_payload.get("ticks"), "NativeTrajectory ticks")
    ]
    raw_ticks = [
        _object(tick, "raw witness tick")
        for tick in _list(branch.get("ticks"), "raw witness ticks")
    ]
    inputs = _resolve_inputs(schedule, compact_ticks, raw_ticks)

    legacy_player = _player_trajectory(
        root=root,
        compact_ticks=compact_ticks,
        raw_ticks=raw_ticks,
        inputs=inputs,
        bounds=LEGACY_EXTENT_BOUNDS,
    )
    player = _player_trajectory(
        root=root,
        compact_ticks=compact_ticks,
        raw_ticks=raw_ticks,
        inputs=inputs,
        bounds=TH08_PLAYFIELD_BOUNDS,
    )
    hazard = _hazard_probe(
        root_summary=_object(
            _object(
                result.get("root_collision_control_projection"),
                "root collision projection",
            ).get("summary"),
            "root collision summary",
        ),
        raw_ticks=raw_ticks,
    )

    model_trajectory = _content_artifact(
        "ModelTrajectory",
        {
            "root_artifact_id": root_artifact["artifact_id"],
            "native_trajectory_artifact_id": native_artifact["artifact_id"],
            "layer": PLAYER_LAYER,
            "movement_semantics_version": (
                TH08_ROUTE2_MOVEMENT_SCALE_SEMANTICS_VERSION
            ),
            "bounds_semantics_version": (
                TH08_PLAYER_CENTER_BOUNDS_SEMANTICS_VERSION
            ),
            "action_resolution": (
                "explicit schedule entries are authoritative; null entries "
                "resolve only from NativeTrajectory.selected_action and must "
                "equal recorded_action"
            ),
            "phase_semantics": (
                "player-only layer carries the root normal phase; collision "
                "and resource transitions are outside this layer"
            ),
            **player,
        },
    )
    first_mismatch = _content_artifact(
        "FirstMismatchReport",
        {
            "player_legacy_extent_bounds": {
                key: legacy_player[key]
                for key in (
                    "bounds",
                    "status",
                    "exact_tick_count",
                    "first_mismatch",
                )
            },
            "player_corrected_center_bounds": {
                key: player[key]
                for key in (
                    "bounds",
                    "status",
                    "exact_tick_count",
                    "first_mismatch",
                )
            },
            "hazard_slot45": {
                key: hazard[key]
                for key in (
                    "event_class",
                    "slot",
                    "horizon",
                    "legacy_closed_form",
                    "independent_repeated_binary32_oracle",
                    "production",
                )
            },
            "integrated_collision_model": {
                "status": "UNKNOWN",
                "reason": (
                    "the retained compact capsule contains collision summaries "
                    "and digests, not a model-consumable full hostile-hazard "
                    "inventory and event ledger"
                ),
            },
        },
    )
    status = (
        "accepted_player_layer_exact"
        if player["status"] == "exact"
        else "player_layer_mismatch"
    )
    return {
        "schema": SCHEMA,
        "status": status,
        "root_manager_frame": _integer(
            root.get("manager_frame"), "root manager_frame"
        ),
        "endpoint_manager_frame": _integer(
            raw_ticks[-1]["compact_state"]["manager_frame"],
            "endpoint manager frame",
        ),
        "sources": [causal_source, witness_source],
        "artifacts": {
            "native_root_capsule": {
                "artifact_id": root_artifact["artifact_id"],
                "kind": root_artifact["kind"],
            },
            "native_trajectory": {
                "artifact_id": native_artifact["artifact_id"],
                "kind": native_artifact["kind"],
            },
            "model_trajectory": model_trajectory,
            "first_mismatch_report": first_mismatch,
            "hazard_forecast_probe": _content_artifact(
                "HazardForecastProbe", hazard
            ),
        },
        "authority": {
            "accepted_for": (
                "deterministic player-mechanics differential on this exact "
                "root/action schedule and slot-45 constant-velocity forecast"
            ),
            "not_accepted_for": (
                "full collision-model parity, planner correctness, live action "
                "authority, other roots, or physical promotion"
            ),
            "next_gate": (
                "add model-consumable hostile state and an event ledger before "
                "integrated planner replay; keep physical promotion behind a "
                "successful offline engine/planner differential"
            ),
        },
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--causal-report", type=Path, default=DEFAULT_CAUSAL_REPORT)
    parser.add_argument("--witness", type=Path, default=DEFAULT_WITNESS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--allow-unpinned-inputs",
        action="store_true",
        help=(
            "validate embedded artifact hashes but do not require checkpoint "
            "file hashes"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        args.causal_report,
        args.witness,
        expected_causal_sha256=(
            None if args.allow_unpinned_inputs else DEFAULT_CAUSAL_REPORT_SHA256
        ),
        expected_witness_sha256=(
            None if args.allow_unpinned_inputs else DEFAULT_WITNESS_SHA256
        ),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
