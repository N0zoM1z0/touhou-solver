"""Build the first model-consumable TH08 native H=1 hazard differential.

The retained raw witness is process/session evidence.  This report extracts a
content-addressed, cross-session offline artifact for the deliberately narrow
root-active-bullet layer and stops at the first unsupported inventory event.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path
from typing import Any


SCHEMA = "th08-native-model-consumable-h1-differential-v1"
ROOT_KIND = "NativeHazardRootH1"
ENDPOINT_KIND = "NativeHazardEndpointH1"
EVENT_KIND = "NativeHazardEventLedgerH1"
MODEL_KIND = "ModelTrajectoryH1"
MISMATCH_KIND = "FirstMismatchReportH1"

DEFAULT_WITNESS = Path(
    "artifacts/native_snapshot_rolling/raw/"
    "th08_model_capsule_h1_94_lifecycle_20260730.json"
)
DEFAULT_OUTPUT = Path(
    "artifacts/runtime_reports/"
    "th08_native_model_consumable_h1_root2129_20260730.json"
)
DEFAULT_WITNESS_SHA256 = (
    "c1fac68da8894c037d0bd561f76bb42856d223908889f302096cd1e75101c805"
)

STATE_MOTION_DIVISOR = {
    1: 1.0,
    2: 2.0,
    3: 2.5,
    4: 3.0,
    5: 2.0,
}


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


def _content_artifact(kind: str, payload: dict[str, object]) -> dict[str, object]:
    digest = hashlib.sha256(_canonical_bytes(payload)).hexdigest()
    return {
        "kind": kind,
        "artifact_id": f"sha256:{digest}",
        "payload": payload,
    }


def _object(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _list(value: object, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a list")
    return value


def _integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    return value


def _number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be numeric")
    return float(value)


def _load_witness(
    path: Path,
    *,
    expected_sha256: str | None,
) -> tuple[dict[str, Any], dict[str, object]]:
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if expected_sha256 is not None and digest != expected_sha256:
        raise ValueError(
            f"witness SHA-256 mismatch: expected {expected_sha256}, got {digest}"
        )
    value = json.loads(data)
    return _object(value, "witness"), {
        "path": path.as_posix(),
        "sha256": digest,
        "size_bytes": len(data),
    }


def _f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def _f32_bits(value: float) -> str:
    return f"0x{struct.unpack('<I', struct.pack('<f', value))[0]:08X}"


def _predict_state_local_step(
    position: float,
    velocity: float,
    state: int,
) -> float:
    try:
        divisor = STATE_MOTION_DIVISOR[state]
    except KeyError as error:
        raise ValueError(f"unsupported native bullet state {state}") from error
    scaled_velocity = (
        _f32(velocity)
        if divisor == 1.0
        else _f32(_f32(velocity) * _f32(1.0 / divisor))
    )
    return _f32(_f32(position) + scaled_velocity)


def _decode_bullets(payload: dict[str, Any]) -> dict[int, dict[str, object]]:
    traces = _list(payload.get("bullets"), "collision payload bullets")
    lifecycle = _list(
        payload.get("bullet_lifecycle"),
        "collision payload bullet_lifecycle",
    )
    lifecycle_by_slot: dict[int, dict[str, Any]] = {}
    for item in lifecycle:
        record = _object(item, "bullet lifecycle record")
        slot = _integer(record.get("slot"), "bullet lifecycle slot")
        if slot in lifecycle_by_slot:
            raise ValueError(f"duplicate bullet lifecycle slot {slot}")
        lifecycle_by_slot[slot] = record

    decoded: dict[int, dict[str, object]] = {}
    for item in traces:
        trace = _list(item, "serialized bullet trace")
        if len(trace) != 9:
            raise ValueError("serialized bullet trace must have nine fields")
        slot = _integer(trace[0], "bullet trace slot")
        if slot in decoded:
            raise ValueError(f"duplicate bullet trace slot {slot}")
        lifecycle_record = lifecycle_by_slot.pop(slot, None)
        if lifecycle_record is None:
            raise ValueError(f"bullet slot {slot} lacks lifecycle state")
        runtime = trace[8]
        if not isinstance(runtime, list) or len(runtime) < 3:
            raise ValueError(
                f"bullet slot {slot} lacks retained transform runtime"
            )
        decoded[slot] = {
            "slot": slot,
            "x": _number(trace[1], "bullet x"),
            "y": _number(trace[2], "bullet y"),
            "vx": _number(trace[3], "bullet vx"),
            "vy": _number(trace[4], "bullet vy"),
            "half_width": _number(trace[5], "bullet half width"),
            "half_height": _number(trace[6], "bullet half height"),
            "transform_flags": _integer(trace[7], "bullet transform flags"),
            "original_transform_flags": _integer(
                runtime[2],
                "bullet original transform flags",
            ),
            "state": _integer(lifecycle_record.get("state"), "bullet state"),
            "timer_d80_fraction_bits": _integer(
                lifecycle_record.get("timer_d80_fraction_bits"),
                "bullet timer D80 fraction bits",
            ),
            "timer_d80_elapsed": _integer(
                lifecycle_record.get("timer_d80_elapsed"),
                "bullet timer D80 elapsed",
            ),
            "timer_d8c_fraction_bits": _integer(
                lifecycle_record.get("timer_d8c_fraction_bits"),
                "bullet timer D8C fraction bits",
            ),
            "timer_d8c_elapsed": _integer(
                lifecycle_record.get("timer_d8c_elapsed"),
                "bullet timer D8C elapsed",
            ),
        }
    if lifecycle_by_slot:
        raise ValueError(
            "lifecycle slots lack matching bullet traces: "
            f"{sorted(lifecycle_by_slot)[:8]}"
        )
    return decoded


def _payload(record: dict[str, Any], label: str) -> dict[str, Any]:
    projection = _object(record.get("collision_control_projection"), label)
    payload = _object(projection.get("model_payload"), f"{label} model payload")
    if payload.get("schema") != (
        "th08-native-snapshot-collision-control-projection-v2"
    ):
        raise ValueError(f"{label} does not contain lifecycle projection v2")
    return payload


def _position_result(
    *,
    slot: int,
    root: dict[str, object],
    native: dict[str, object],
    state_aware: bool,
) -> dict[str, object]:
    state = _integer(root["state"], "root bullet state")
    divisor = STATE_MOTION_DIVISOR.get(state)
    if divisor is None:
        raise ValueError(f"unsupported root bullet state {state}")
    prediction_x = (
        _predict_state_local_step(
            _number(root["x"], "root bullet x"),
            _number(root["vx"], "root bullet vx"),
            state,
        )
        if state_aware
        else _predict_state_local_step(
            _number(root["x"], "root bullet x"),
            _number(root["vx"], "root bullet vx"),
            1,
        )
    )
    prediction_y = (
        _predict_state_local_step(
            _number(root["y"], "root bullet y"),
            _number(root["vy"], "root bullet vy"),
            state,
        )
        if state_aware
        else _predict_state_local_step(
            _number(root["y"], "root bullet y"),
            _number(root["vy"], "root bullet vy"),
            1,
        )
    )
    native_x = _number(native["x"], "native bullet x")
    native_y = _number(native["y"], "native bullet y")
    exact = (
        _f32_bits(prediction_x) == _f32_bits(native_x)
        and _f32_bits(prediction_y) == _f32_bits(native_y)
    )
    return {
        "slot": slot,
        "root_state": state,
        "motion_divisor": divisor,
        "root_timer_d80_elapsed": root["timer_d80_elapsed"],
        "prediction": {
            "x": prediction_x,
            "x_bits": _f32_bits(prediction_x),
            "y": prediction_y,
            "y_bits": _f32_bits(prediction_y),
        },
        "native": {
            "x": native_x,
            "x_bits": _f32_bits(native_x),
            "y": native_y,
            "y_bits": _f32_bits(native_y),
        },
        "exact": exact,
    }


def _endpoint_observation(bullet: dict[str, object]) -> dict[str, object]:
    return {
        "slot": bullet["slot"],
        "x": bullet["x"],
        "y": bullet["y"],
        "state": bullet["state"],
    }


def _validate_transaction(result: dict[str, Any]) -> tuple[
    dict[str, Any],
    dict[str, Any],
]:
    if result.get("status") != "rolling_native_projection_snapshot_passed":
        raise ValueError("native H1 transaction did not pass")
    for path, value in (
        ("barrier root", _object(result.get("barrier_root"), "barrier root")),
        (
            "restore after A1",
            _object(
                _object(
                    _object(result.get("restores"), "restores").get("after_a1"),
                    "restore after A1",
                ).get("header"),
                "restore after A1 header",
            ),
        ),
        (
            "restore after A2",
            _object(
                _object(
                    _object(result.get("restores"), "restores").get("after_a2"),
                    "restore after A2",
                ).get("header"),
                "restore after A2 header",
            ),
        ),
        (
            "restore after B",
            _object(
                _object(
                    _object(result.get("restores"), "restores").get("after_b"),
                    "restore after B",
                ).get("header"),
                "restore after B header",
            ),
        ),
    ):
        if _integer(value.get("error_code"), f"{path} error code") != 0:
            raise ValueError(f"{path} reports an error")

    branches = _object(result.get("branches"), "branches")
    a1 = _object(branches.get("a1"), "A1")
    a2 = _object(branches.get("a2"), "A2")
    branch_b = _object(branches.get("b"), "B")
    a1_tick = _object(_list(a1.get("ticks"), "A1 ticks")[0], "A1 tick")
    a2_tick = _object(_list(a2.get("ticks"), "A2 ticks")[0], "A2 tick")
    b_tick = _object(_list(branch_b.get("ticks"), "B ticks")[0], "B tick")
    a1_projection = _object(
        a1_tick.get("collision_control_projection"),
        "A1 collision projection",
    )
    a2_projection = _object(
        a2_tick.get("collision_control_projection"),
        "A2 collision projection",
    )
    if a1_projection.get("sha256") != a2_projection.get("sha256"):
        raise ValueError("same-action A1/A2 collision projections differ")
    if (
        _integer(a1_tick.get("selected_action"), "A1 selected action") != 0x05
        or _integer(a1_tick.get("recorded_action"), "A1 recorded action") != 0x05
        or _integer(a2_tick.get("selected_action"), "A2 selected action") != 0x05
        or _integer(a2_tick.get("recorded_action"), "A2 recorded action") != 0x05
    ):
        raise ValueError("same-action controls do not preserve replay action 0x05")
    if (
        _integer(b_tick.get("selected_action"), "B selected action") != 0x94
        or _integer(b_tick.get("recorded_action"), "B recorded action") != 0x05
    ):
        raise ValueError("B branch action provenance is not 0x94 versus replay 0x05")
    if _integer(b_tick.get("selected_action"), "B selected action") & 0x02:
        raise ValueError("B branch contains Bomb")

    natural = _object(result.get("natural_reference"), "natural reference")
    if natural.get("status") != "natural_frame_differential_passed":
        raise ValueError("natural B reference did not pass")
    natural_tick = _object(
        _list(natural.get("ticks"), "natural ticks")[0],
        "natural tick",
    )
    if not bool(natural_tick.get("headless_collision_control_projection_exact")):
        raise ValueError("headless B and natural B collision projections differ")
    if _integer(natural_tick.get("manager_frame"), "natural manager frame") != 2130:
        raise ValueError("natural endpoint is not manager frame 2130")
    b_projection = _object(
        b_tick.get("collision_control_projection"),
        "B collision projection",
    )
    natural_projection = _object(
        natural_tick.get("collision_control_projection"),
        "natural collision projection",
    )
    if b_projection.get("sha256") != natural_projection.get("sha256"):
        raise ValueError("B/native projection digest disagreement")
    if b_projection.get("model_payload") != natural_projection.get("model_payload"):
        raise ValueError("B/native retained model payload disagreement")
    return b_tick, natural_tick


def build_report(
    witness_path: Path,
    *,
    expected_witness_sha256: str | None = None,
) -> dict[str, object]:
    witness, source = _load_witness(
        witness_path,
        expected_sha256=expected_witness_sha256,
    )
    if witness.get("schema") != "th08-native-snapshot-rolling-trial-v3":
        raise ValueError("unexpected native snapshot witness schema")
    if not bool(witness.get("retain_collision_control_payload")):
        raise ValueError("witness did not retain model payload")
    if _integer(witness.get("horizon"), "witness horizon") != 1:
        raise ValueError("witness is not H=1")
    result = _object(witness.get("result"), "result")
    b_tick, natural_tick = _validate_transaction(result)

    root_projection = _object(
        result.get("root_collision_control_projection"),
        "root collision projection",
    )
    root_payload = _object(
        root_projection.get("model_payload"),
        "root model payload",
    )
    endpoint_payload = _payload(b_tick, "B tick")
    if root_payload.get("schema") != endpoint_payload.get("schema"):
        raise ValueError("root/endpoint collision schemas differ")
    root_compact = _object(root_payload.get("compact_state"), "root compact state")
    endpoint_compact = _object(
        endpoint_payload.get("compact_state"),
        "endpoint compact state",
    )
    if _integer(root_compact.get("manager_frame"), "root manager frame") != 2129:
        raise ValueError("root manager frame is not 2129")
    if _integer(endpoint_compact.get("manager_frame"), "endpoint manager frame") != 2130:
        raise ValueError("endpoint manager frame is not 2130")

    root_bullets = _decode_bullets(root_payload)
    endpoint_bullets = _decode_bullets(endpoint_payload)
    root_slots = set(root_bullets)
    endpoint_slots = set(endpoint_bullets)
    common_slots = sorted(root_slots & endpoint_slots)
    birth_slots = sorted(endpoint_slots - root_slots)
    removal_slots = sorted(root_slots - endpoint_slots)

    baseline = [
        _position_result(
            slot=slot,
            root=root_bullets[slot],
            native=endpoint_bullets[slot],
            state_aware=False,
        )
        for slot in common_slots
    ]
    corrected = [
        _position_result(
            slot=slot,
            root=root_bullets[slot],
            native=endpoint_bullets[slot],
            state_aware=True,
        )
        for slot in common_slots
    ]
    baseline_mismatches = [record for record in baseline if not record["exact"]]
    corrected_mismatches = [record for record in corrected if not record["exact"]]
    if [record["slot"] for record in baseline_mismatches] != list(
        range(1192, 1220)
    ):
        raise ValueError("legacy mismatch cohort is not slots 1192..1219")
    if corrected_mismatches:
        raise ValueError("state-local H1 prediction is not exact")

    state_counts: dict[str, int] = {}
    for bullet in root_bullets.values():
        key = str(_integer(bullet["state"], "root bullet state"))
        state_counts[key] = state_counts.get(key, 0) + 1
    if state_counts != {"1": 668, "2": 28}:
        raise ValueError(f"unexpected root bullet state inventory {state_counts}")

    root_artifact = _content_artifact(
        ROOT_KIND,
        {
            "layer": "root_active_bullets",
            "manager_frame": 2129,
            "collision_projection_schema": root_payload["schema"],
            "compact_state": root_compact,
            "player_lethal_aabb": root_payload.get("player_lethal_aabb"),
            "bullets": [root_bullets[slot] for slot in sorted(root_bullets)],
            "lasers": root_payload.get("lasers"),
            "state_counts": state_counts,
            "scope_exclusions": (
                "enemy/ECL future emission, bullet allocation/deactivation, "
                "laser birth, collision/resource transition"
            ),
        },
    )
    endpoint_artifact = _content_artifact(
        ENDPOINT_KIND,
        {
            "root_artifact_id": root_artifact["artifact_id"],
            "manager_frame": 2130,
            "selected_action": _integer(
                b_tick.get("selected_action"),
                "B selected action",
            ),
            "recorded_action": _integer(
                b_tick.get("recorded_action"),
                "B recorded action",
            ),
            "compact_state": endpoint_compact,
            "bullets": [
                _endpoint_observation(endpoint_bullets[slot])
                for slot in sorted(endpoint_bullets)
            ],
            "lasers": endpoint_payload.get("lasers"),
            "natural_reference_manager_frame": _integer(
                natural_tick.get("manager_frame"),
                "natural manager frame",
            ),
        },
    )
    event_artifact = _content_artifact(
        EVENT_KIND,
        {
            "root_artifact_id": root_artifact["artifact_id"],
            "endpoint_artifact_id": endpoint_artifact["artifact_id"],
            "from_manager_frame": 2129,
            "to_manager_frame": 2130,
            "births": [endpoint_bullets[slot] for slot in birth_slots],
            "removals": [root_bullets[slot] for slot in removal_slots],
            "common_slot_count": len(common_slots),
            "birth_slots": birth_slots,
            "removal_slots": removal_slots,
            "generation_authority": (
                "observed native event ledger only; not predicted by the "
                "rebuilt enemy/ECL/bullet allocator"
            ),
        },
    )
    model_artifact = _content_artifact(
        MODEL_KIND,
        {
            "root_artifact_id": root_artifact["artifact_id"],
            "native_endpoint_artifact_id": endpoint_artifact["artifact_id"],
            "event_ledger_artifact_id": event_artifact["artifact_id"],
            "layer": "root_active_bullet_position_h1",
            "status": "exact",
            "semantics": {
                "binary32_store_after_scaled_velocity_and_position_add": True,
                "state_motion_divisors": {
                    str(state): divisor
                    for state, divisor in STATE_MOTION_DIVISOR.items()
                },
                "native_addresses": {
                    "bullet_manager_update": "0x00431240",
                    "vector_divide": "0x0040C7D0",
                    "vector_add": "0x00410A70",
                },
                "same_update_animation_completion": (
                    "outside H1 exact claim unless its ANM VM is modeled"
                ),
            },
            "legacy_full_velocity": {
                "exact_common_slots": len(common_slots) - len(baseline_mismatches),
                "common_slot_count": len(common_slots),
                "first_mismatch": baseline_mismatches[0],
                "mismatch_slots": [
                    record["slot"] for record in baseline_mismatches
                ],
            },
            "state_local_h1": {
                "exact_common_slots": len(common_slots),
                "common_slot_count": len(common_slots),
                "first_mismatch": None,
            },
        },
    )
    mismatch_artifact = _content_artifact(
        MISMATCH_KIND,
        {
            "legacy_root_active_bullet_forecast": {
                "status": "mismatch",
                "manager_frame": 2130,
                "cause": (
                    "native lifecycle state omitted; state-2 spawn animation "
                    "moves by velocity/2 instead of ordinary full velocity"
                ),
                "first_mismatch": baseline_mismatches[0],
            },
            "corrected_root_active_bullet_h1": {
                "status": "no_mismatch_through_declared_horizon",
                "manager_frame": 2130,
                "exact_common_slots": len(common_slots),
            },
            "integrated_hazard_inventory_h1": {
                "status": "UNKNOWN",
                "manager_frame": 2130,
                "first_missing_transition": {
                    "event_class": "bullet_birth_and_removal",
                    "birth_slots": birth_slots,
                    "removal_slots": removal_slots,
                },
                "reason": (
                    "the event ledger is observed, but the rebuilt "
                    "enemy/ECL/allocator path did not generate it causally"
                ),
            },
        },
    )
    return {
        "schema": SCHEMA,
        "source": source,
        "artifacts": {
            "native_hazard_root": root_artifact,
            "native_hazard_endpoint": endpoint_artifact,
            "native_event_ledger": event_artifact,
            "model_trajectory": model_artifact,
            "first_mismatch_report": mismatch_artifact,
        },
        "result": {
            "root_active_bullet_h1": "exact",
            "legacy_exact_common_slots": (
                len(common_slots) - len(baseline_mismatches)
            ),
            "corrected_exact_common_slots": len(common_slots),
            "common_slot_count": len(common_slots),
            "birth_count": len(birth_slots),
            "removal_count": len(removal_slots),
            "integrated_hazard_inventory_h1": "UNKNOWN",
            "physical_trials_used": 0,
        },
        "authority": {
            "accepted_for": (
                "same-witness offline H1 root-active bullet differential, "
                "lifecycle-field regression, and first-gap localization"
            ),
            "not_accepted_for": (
                "predictive bullet birth/removal, H>1 spawn-state transition, "
                "full planner parity, live action authority, or physical "
                "promotion"
            ),
            "next_gate": (
                "use the observed H1 event ledger to add one causal "
                "birth/removal event class or stop at its first unsupported "
                "enemy/ECL producer; only then replay a production planner "
                "decision"
            ),
        },
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--witness", type=Path, default=DEFAULT_WITNESS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--expected-witness-sha256",
        default=DEFAULT_WITNESS_SHA256,
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = build_report(
        args.witness,
        expected_witness_sha256=args.expected_witness_sha256,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"native model-consumable H1 report: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
