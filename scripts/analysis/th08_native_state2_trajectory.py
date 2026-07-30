"""Validate production state-2 bullet lifecycle projection against native H=8."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from analysis.th08_native_model_consumable_h1 import (
    _canonical_bytes,
    _decode_bullets,
    _f32,
    _f32_bits,
    _integer,
    _list,
    _number,
    _object,
)
from th08_live.local_hazards import _build_bullet_frames
from th08_live.models import Bullet


SCHEMA = "th08-native-state2-lifecycle-trajectory-v1"
DEFAULT_WITNESS = Path(
    "artifacts/native_snapshot_rolling/raw/"
    "th08_model_capsule_h8_94_recorded_lifecycle_accepted_20260730.json"
)
DEFAULT_OUTPUT = Path(
    "artifacts/runtime_reports/"
    "th08_native_state2_lifecycle_root2129_h8_20260730.json"
)
DEFAULT_WITNESS_SHA256 = (
    "77d3a6ed431762e179473170e5658f60d434d90b82933266e7553527a9075d09"
)
COHORT_SLOTS = tuple(range(1192, 1220))
STATE2_COMPLETION_TIMER = 9


def _content_artifact(kind: str, payload: dict[str, object]) -> dict[str, object]:
    digest = hashlib.sha256(_canonical_bytes(payload)).hexdigest()
    return {
        "kind": kind,
        "artifact_id": f"sha256:{digest}",
        "payload": payload,
    }


def _load(path: Path, expected_sha256: str | None) -> tuple[
    dict[str, Any],
    dict[str, object],
]:
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if expected_sha256 is not None and digest != expected_sha256:
        raise ValueError(
            f"H8 witness SHA-256 mismatch: expected {expected_sha256}, got {digest}"
        )
    return _object(json.loads(data), "H8 witness"), {
        "path": path.as_posix(),
        "sha256": digest,
        "size_bytes": len(data),
    }


def _model_bullet(record: dict[str, object]) -> Bullet:
    return Bullet(
        x=_number(record["x"], "root x"),
        y=_number(record["y"], "root y"),
        vx=_number(record["vx"], "root vx"),
        vy=_number(record["vy"], "root vy"),
        half_width=_number(record["half_width"], "root half width"),
        half_height=_number(record["half_height"], "root half height"),
        transform_flags=_integer(
            record["transform_flags"],
            "root transform flags",
        ),
        slot=_integer(record["slot"], "root slot"),
        native_state=_integer(record["state"], "root state"),
        native_state_timer_elapsed=_integer(
            record["timer_d80_elapsed"],
            "root state timer",
        ),
    )


def _advance_expected_lifecycle(
    *,
    x: float,
    y: float,
    vx: float,
    vy: float,
    state: int,
    timer: int,
) -> tuple[float, float, int, int]:
    if state == 1:
        return _f32(x + vx), _f32(y + vy), 1, timer + 1
    if state != 2:
        raise ValueError(f"state-2 fixture reached unsupported state {state}")
    x = _f32(x + _f32(vx * _f32(0.5)))
    y = _f32(y + _f32(vy * _f32(0.5)))
    if timer < STATE2_COMPLETION_TIMER:
        return x, y, 2, timer + 1
    # Native stores the spawn half-step before ANM completion falls through
    # to the ordinary state-1 update in the same bullet-manager call.
    return _f32(x + vx), _f32(y + vy), 1, 1


def _validate_witness(
    witness: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    if witness.get("schema") != "th08-native-snapshot-rolling-trial-v3":
        raise ValueError("unexpected rolling-trial schema")
    if _integer(witness.get("horizon"), "H8 horizon") != 8:
        raise ValueError("state-2 witness is not H=8")
    if not bool(witness.get("retain_collision_control_payload")):
        raise ValueError("state-2 witness lacks retained model payloads")
    result = _object(witness.get("result"), "H8 result")
    if result.get("status") != "rolling_native_projection_snapshot_passed":
        raise ValueError("H8 native transaction did not pass")
    natural = _object(result.get("natural_reference"), "H8 natural reference")
    if natural.get("status") != "natural_frame_differential_passed":
        raise ValueError("H8 natural differential did not pass")
    if not bool(natural.get("root_collision_control_projection_exact")):
        raise ValueError("H8 natural reference did not recover the exact root")

    branches = _object(result.get("branches"), "H8 branches")
    a1_ticks = _list(
        _object(branches.get("a1"), "H8 A1").get("ticks"),
        "H8 A1 ticks",
    )
    a2_ticks = _list(
        _object(branches.get("a2"), "H8 A2").get("ticks"),
        "H8 A2 ticks",
    )
    b_ticks = [
        _object(tick, "H8 B tick")
        for tick in _list(
            _object(branches.get("b"), "H8 B").get("ticks"),
            "H8 B ticks",
        )
    ]
    natural_ticks = [
        _object(tick, "H8 natural tick")
        for tick in _list(natural.get("ticks"), "H8 natural ticks")
    ]
    if not (
        len(a1_ticks)
        == len(a2_ticks)
        == len(b_ticks)
        == len(natural_ticks)
        == 8
    ):
        raise ValueError("H8 branch/natural tick counts differ")
    for branch_name, ticks in (("A1", a1_ticks), ("A2", a2_ticks)):
        for tick in ticks:
            projection = _object(
                _object(tick, f"{branch_name} tick").get(
                    "collision_control_projection"
                ),
                f"{branch_name} collision projection",
            )
            if "model_payload" in projection:
                raise ValueError(
                    f"{branch_name} duplicate payload retention was not elided"
                )
    for index, (headless, natural_tick) in enumerate(zip(b_ticks, natural_ticks)):
        headless_projection = _object(
            headless.get("collision_control_projection"),
            f"H8 B projection {index}",
        )
        natural_projection = _object(
            natural_tick.get("collision_control_projection"),
            f"H8 natural projection {index}",
        )
        if "model_payload" not in headless_projection:
            raise ValueError(f"H8 B tick {index} lacks model payload")
        if "model_payload" not in natural_projection:
            raise ValueError(f"H8 natural tick {index} lacks model payload")
        if headless_projection.get("sha256") != natural_projection.get("sha256"):
            raise ValueError(f"H8 B/natural digest mismatch at tick {index}")
        if not bool(
            natural_tick.get("headless_collision_control_projection_exact")
        ):
            raise ValueError(f"H8 B/natural payload mismatch at tick {index}")
    return result, b_ticks, natural_ticks


def build_report(
    witness_path: Path,
    *,
    expected_witness_sha256: str | None = None,
) -> dict[str, object]:
    witness, source = _load(witness_path, expected_witness_sha256)
    result, b_ticks, _natural_ticks = _validate_witness(witness)
    root_projection = _object(
        result.get("root_collision_control_projection"),
        "H8 root collision projection",
    )
    root_payload = _object(
        root_projection.get("model_payload"),
        "H8 root model payload",
    )
    root = _decode_bullets(root_payload)
    if any(slot not in root for slot in COHORT_SLOTS):
        raise ValueError("H8 root omits the state-2 cohort")
    cohort = [root[slot] for slot in COHORT_SLOTS]
    if any(_integer(record["state"], "cohort root state") != 2 for record in cohort):
        raise ValueError("H8 cohort is not entirely state 2 at the root")
    timer_groups: dict[str, list[int]] = {}
    for record in cohort:
        timer = str(_integer(record["timer_d80_elapsed"], "cohort timer"))
        timer_groups.setdefault(timer, []).append(
            _integer(record["slot"], "cohort slot")
        )
    expected_groups = {
        "2": list(range(1213, 1220)),
        "4": list(range(1206, 1213)),
        "6": list(range(1199, 1206)),
        "8": list(range(1192, 1199)),
    }
    if timer_groups != expected_groups:
        raise ValueError(f"unexpected state-2 timer groups {timer_groups}")

    production_frames = _build_bullet_frames(
        tuple(_model_bullet(record) for record in cohort),
        horizon=8,
        snapshot_lag=0,
    )
    expected = {
        slot: {
            "x": _f32(_number(root[slot]["x"], "root x")),
            "y": _f32(_number(root[slot]["y"], "root y")),
            "vx": _f32(_number(root[slot]["vx"], "root vx")),
            "vy": _f32(_number(root[slot]["vy"], "root vy")),
            "state": _integer(root[slot]["state"], "root state"),
            "timer": _integer(
                root[slot]["timer_d80_elapsed"],
                "root timer",
            ),
        }
        for slot in COHORT_SLOTS
    }
    observations: list[dict[str, object]] = []
    production_compared = 0
    production_exact = 0
    lifecycle_compared = 0
    lifecycle_exact = 0
    first_production_mismatch = None
    first_lifecycle_mismatch = None
    transition_frames: dict[str, list[int]] = {}
    previous_native_state = {slot: 2 for slot in COHORT_SLOTS}

    for frame_index, (frame, tick) in enumerate(
        zip(production_frames, b_ticks)
    ):
        compact = _object(tick.get("compact_state"), "H8 compact state")
        manager_frame = _integer(
            compact.get("manager_frame"),
            "H8 manager frame",
        )
        projection = _object(
            tick.get("collision_control_projection"),
            "H8 tick collision projection",
        )
        native = _decode_bullets(
            _object(projection.get("model_payload"), "H8 tick model payload")
        )
        tick_observations: list[dict[str, object]] = []
        for cohort_index, slot in enumerate(COHORT_SLOTS):
            state = expected[slot]
            (
                state["x"],
                state["y"],
                state["state"],
                state["timer"],
            ) = _advance_expected_lifecycle(
                x=_number(state["x"], "expected x"),
                y=_number(state["y"], "expected y"),
                vx=_number(state["vx"], "expected vx"),
                vy=_number(state["vy"], "expected vy"),
                state=_integer(state["state"], "expected state"),
                timer=_integer(state["timer"], "expected timer"),
            )
            if slot not in native:
                tick_observations.append(
                    {
                        "slot": slot,
                        "status": "native_removed",
                    }
                )
                continue
            native_record = native[slot]
            model_x = float(frame[0][cohort_index])
            model_y = float(frame[1][cohort_index])
            native_x = _number(native_record["x"], "native x")
            native_y = _number(native_record["y"], "native y")
            position_exact = (
                _f32_bits(model_x) == _f32_bits(native_x)
                and _f32_bits(model_y) == _f32_bits(native_y)
            )
            lifecycle_match = (
                _integer(state["state"], "expected state")
                == _integer(native_record["state"], "native state")
                and _integer(state["timer"], "expected timer")
                == _integer(
                    native_record["timer_d80_elapsed"],
                    "native timer",
                )
            )
            production_compared += 1
            production_exact += int(position_exact)
            lifecycle_compared += 1
            lifecycle_exact += int(lifecycle_match)
            if not position_exact and first_production_mismatch is None:
                first_production_mismatch = {
                    "manager_frame": manager_frame,
                    "slot": slot,
                    "model_x_bits": _f32_bits(model_x),
                    "native_x_bits": _f32_bits(native_x),
                    "model_y_bits": _f32_bits(model_y),
                    "native_y_bits": _f32_bits(native_y),
                }
            if not lifecycle_match and first_lifecycle_mismatch is None:
                first_lifecycle_mismatch = {
                    "manager_frame": manager_frame,
                    "slot": slot,
                    "expected_state": state["state"],
                    "native_state": native_record["state"],
                    "expected_timer": state["timer"],
                    "native_timer": native_record["timer_d80_elapsed"],
                }
            native_state = _integer(native_record["state"], "native state")
            if previous_native_state[slot] == 2 and native_state == 1:
                transition_frames.setdefault(str(manager_frame), []).append(slot)
            previous_native_state[slot] = native_state
            tick_observations.append(
                {
                    "slot": slot,
                    "x": native_x,
                    "y": native_y,
                    "state": native_state,
                    "timer_d80_elapsed": native_record["timer_d80_elapsed"],
                }
            )
        observations.append(
            {
                "manager_frame": manager_frame,
                "cohort": tick_observations,
            }
        )

    if production_compared != 223 or production_exact != 223:
        raise ValueError(
            "production state-2 position recurrence is not 223/223 exact"
        )
    if lifecycle_compared != 223 or lifecycle_exact != 223:
        raise ValueError(
            "independent state-2 lifecycle recurrence is not 223/223 exact"
        )
    expected_transitions = {
        "2131": list(range(1192, 1199)),
        "2133": list(range(1199, 1206)),
        "2135": list(range(1206, 1213)),
        # Slot 1217 is natively removed on frame 2137 before a successor
        # lifecycle state can be observed.
        "2137": [1213, 1214, 1215, 1216, 1218, 1219],
    }
    if transition_frames != expected_transitions:
        raise ValueError(f"unexpected state-2 transition frames {transition_frames}")

    trajectory = _content_artifact(
        "NativeState2TrajectoryH8",
        {
            "root_manager_frame": 2129,
            "cohort_slots": list(COHORT_SLOTS),
            "root_timer_groups": timer_groups,
            "observations": observations,
        },
    )
    differential = _content_artifact(
        "ProductionState2DifferentialH8",
        {
            "native_trajectory_artifact_id": trajectory["artifact_id"],
            "status": "exact",
            "production_position_compared": production_compared,
            "production_position_exact": production_exact,
            "production_first_mismatch": first_production_mismatch,
            "independent_lifecycle_compared": lifecycle_compared,
            "independent_lifecycle_exact": lifecycle_exact,
            "independent_lifecycle_first_mismatch": first_lifecycle_mismatch,
            "transition_frames": transition_frames,
            "recurrence": (
                "state2 timer<9: float32(position + float32(velocity/2)); "
                "state2 timer>=9: that half-step then a separately rounded "
                "full step and state1/timer1; state1: full step"
            ),
        },
    )
    return {
        "schema": SCHEMA,
        "source": source,
        "artifacts": {
            "native_state2_trajectory": trajectory,
            "production_differential": differential,
        },
        "result": {
            "production_root_active_state2_h8": "exact",
            "production_position_exact": "223/223",
            "independent_lifecycle_exact": "223/223",
            "headless_natural_exact_ticks": 8,
            "a1_a2_duplicate_model_payloads_retained": False,
            "physical_trials_used": 0,
        },
        "authority": {
            "accepted_for": (
                "root2129 state-2 constant-velocity lifecycle and production "
                "position recurrence through H=8"
            ),
            "not_accepted_for": (
                "states 3/4/5, state-2 bullets with future transform "
                "activation, causal birth/removal generation, integrated "
                "planner parity, live action authority, or physical promotion"
            ),
            "next_gate": (
                "bind the H1 observed birth/removal ledger to its smallest "
                "enemy/ECL producer, then replay one production planner "
                "decision; do not broaden horizon first"
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
    print(f"native state-2 H8 report: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
