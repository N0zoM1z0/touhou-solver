#!/usr/bin/env python3
"""Retain deterministic SEM-SCALE-B authority and parity evidence."""

from __future__ import annotations

import argparse
import dataclasses
import json
import math
import platform
import sys
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import th08_live_dodge_agent as live
from th08_corridor_runtime import solve_corridor
from th08_local_planner import (
    ActuatorPipeline,
    LocalPlannerRequest,
    PhysicalHazardSnapshot,
    PlannerConfig,
)
from th08_time_scale import (
    IncompleteTimeScaleScheduleError,
    TH08_PLAYER_LASER_SCALE_SEMANTICS_VERSION,
    TH08_UNIT_TIME_SCALE_BITS,
    Th08TimeScaleSchedule,
    UnsupportedTimeScaleScheduleError,
)
from touhou_control import native_backend
from touhou_control.local_pipeline_oracle import (
    LocalPipelineRoot,
    scalar_local_pipeline_certificates,
)


def _decision_payload(decision: live.Decision) -> dict[str, object]:
    payload = dataclasses.asdict(decision)
    payload.pop("local_certificate_timing")
    return payload


def _root_only_local_unknown() -> bool:
    request = LocalPlannerRequest(
        physical=PhysicalHazardSnapshot(
            player_x=192.0,
            player_y=400.0,
            bullets=(),
            lasers=(),
            time_scale_schedule=Th08TimeScaleSchedule.root_observation(
                TH08_UNIT_TIME_SCALE_BITS,
                source_frame=100,
                provenance="sem_scale_b_root_only_probe",
            ),
        ),
        actuator=ActuatorPipeline(
            previous_direction=0,
            can_bomb=False,
        ),
        config=PlannerConfig(horizon=4, beam_width=8),
    )
    try:
        live.choose_action_request(request)
    except IncompleteTimeScaleScheduleError:
        return True
    return False


def _corridor_arguments() -> dict[str, object]:
    return {
        "source_frame": 110,
        "snapshot_frame": 100,
        "forecast_lead_frames": 10,
        "player_x": 192.0,
        "player_y": 400.0,
        "bullets": (),
        "lasers": (),
        "enemy_bodies": (),
        "snapshot_lag": 0,
        "control_delay_candidates": (1, 2),
        "nominal_control_delay": 1,
        "active_action": "stay",
    }


def _corridor_authority() -> dict[str, object]:
    arguments = _corridor_arguments()
    root_unknown = False
    try:
        solve_corridor(
            **arguments,
            time_scale_schedule=Th08TimeScaleSchedule.root_observation(
                TH08_UNIT_TIME_SCALE_BITS,
                source_frame=100,
                provenance="sem_scale_b_corridor_root_probe",
            ),
        )
    except IncompleteTimeScaleScheduleError:
        root_unknown = True

    nonunit_unknown = False
    try:
        solve_corridor(
            **arguments,
            time_scale_schedule=Th08TimeScaleSchedule.constant(
                0x3F000000,
                horizon=128,
                provenance="sem_scale_b_corridor_nonunit_probe",
            ),
        )
    except UnsupportedTimeScaleScheduleError:
        nonunit_unknown = True

    varying_values = tuple(
        0x3F800000 if index % 2 == 0 else 0x3F000000
        for index in range(128)
    )
    varying_unknown = False
    try:
        solve_corridor(
            **arguments,
            time_scale_schedule=Th08TimeScaleSchedule.explicit(
                root_scale_bits=varying_values[0],
                player_scale_bits=varying_values,
                laser_scale_bits=varying_values,
                complete=True,
                provenance="sem_scale_b_corridor_varying_probe",
                source_frame=100,
            ),
        )
    except UnsupportedTimeScaleScheduleError:
        varying_unknown = True

    unit = Th08TimeScaleSchedule.constant(
        TH08_UNIT_TIME_SCALE_BITS,
        horizon=128,
        provenance="sem_scale_b_corridor_unit_probe",
        source_frame=100,
    )
    unit_solution = solve_corridor(
        **arguments,
        time_scale_schedule=unit,
    )
    return {
        "root_only_unknown": root_unknown,
        "complete_nonunit_unknown": nonunit_unknown,
        "complete_varying_unknown": varying_unknown,
        "complete_unit_accepted": (
            unit_solution.time_scale_identity == unit.serialized_identity
        ),
        "unit_policy_reachable": unit_solution.plan.reachable,
    }


def _certificate_scalar_parity() -> dict[str, object]:
    delay_frames = (1, 2, 3)
    action_hold_frames = 3
    horizon = action_hold_frames + max(delay_frames)
    scale_bits = (0x3F000000,) * horizon
    scale_values = (0.5,) * horizon
    root = LocalPipelineRoot(
        active_action="right",
        held_desired_action="right",
    )
    packed = live._robust_action_certificates(
        player_x=42.0,
        player_y=400.0,
        previous_mask=live.SHOT | live.FOCUS | live.RIGHT,
        actions=live._PLANNER_ACTIONS,
        delay_frames=delay_frames,
        action_hold_frames=action_hold_frames,
        bullets=(),
        lasers=(),
        enemy_bodies=(),
        snapshot_lag=0,
        player_scale_bits=scale_bits,
        laser_scale_bits=scale_bits,
        pipeline_root=root,
    )
    scalar = scalar_local_pipeline_certificates(
        root=root,
        selected_actions=tuple(
            action.name for action in live._PLANNER_ACTIONS
        ),
        action_velocities={
            **{
                action.name: (action.dx, action.dy)
                for action in live._PLANNER_ACTIONS
            },
            "stay_unfocused": (0.0, 0.0),
        },
        delay_frames=delay_frames,
        horizon_frames=horizon,
        start_x=42.0,
        start_y=400.0,
        bounds=(
            live.PLAYFIELD_LEFT,
            live.PLAYFIELD_RIGHT,
            live.PLAYFIELD_TOP,
            live.PLAYFIELD_BOTTOM,
        ),
        hazard_sample=lambda _x, _y, _step: (0.0, 0, math.inf),
        boundary_risk=live._boundary_risk,
        movement_scales=scale_values,
    )
    packed_safe = tuple(
        action.name
        for action in live._PLANNER_ACTIONS
        if (
            packed[action.name].worst_collisions == 0
            and packed[action.name].min_clearance >= 0.0
        )
    )
    scalar_safe = tuple(
        action.name
        for action in live._PLANNER_ACTIONS
        if (
            scalar[action.name].worst_collisions == 0
            and scalar[action.name].min_clearance >= 0.0
        )
    )
    maximum_cvar_delta = max(
        abs(
            packed[action.name].cvar_risk
            - scalar[action.name].cvar_risk
        )
        for action in live._PLANNER_ACTIONS
    )
    return {
        "safe_action_mask_parity": packed_safe == scalar_safe,
        "maximum_cvar_delta": maximum_cvar_delta,
        "cvar_parity_within_1e_4": maximum_cvar_delta <= 1e-4,
        "action_count": len(live._PLANNER_ACTIONS),
    }


def _native_local_beam_parity() -> dict[str, object]:
    native_available = (
        native_backend._load_local_beam_reduce_function() is not None
    )
    if not native_available:
        return {
            "native_available": False,
            "complete_constant_nonunit_parity": False,
        }
    arguments = {
        "player_x": 192.0,
        "player_y": 400.0,
        "bullets": (
            live.Bullet(192.0, 364.0, 0.0, 3.0, 3.0, 3.0),
        ),
        "lasers": (),
        "previous_direction": 0,
        "can_bomb": False,
        "control_delay_frames": 2,
        "control_delay_candidates": (1, 2, 3),
        "action_hold_frames": 3,
        "horizon": 8,
        "threat_horizon": 10,
        "beam_width": 24,
        "time_scale_schedule": Th08TimeScaleSchedule.constant(
            0x3F000000,
            horizon=64,
            provenance="sem_scale_b_native_beam_probe",
        ),
    }
    previous_backend = live._LOCAL_BEAM_REDUCER
    try:
        live._configure_local_beam_reducer("python")
        python_decision = live.choose_action(**arguments)
        live._configure_local_beam_reducer("native")
        native_decision = live.choose_action(**arguments)
    finally:
        live._configure_local_beam_reducer(previous_backend)
    return {
        "native_available": True,
        "complete_constant_nonunit_parity": (
            _decision_payload(native_decision)
            == _decision_payload(python_decision)
        ),
        "action": python_decision.action,
    }


def build_report() -> dict[str, object]:
    corridor = _corridor_authority()
    certificate = _certificate_scalar_parity()
    beam = _native_local_beam_parity()
    checks = {
        "local_root_only_unknown": _root_only_local_unknown(),
        "corridor_root_only_unknown": corridor["root_only_unknown"],
        "corridor_nonunit_unknown": corridor[
            "complete_nonunit_unknown"
        ],
        "corridor_varying_unknown": corridor[
            "complete_varying_unknown"
        ],
        "corridor_unit_identity": corridor[
            "complete_unit_accepted"
        ],
        "certificate_safe_action_mask_parity": certificate[
            "safe_action_mask_parity"
        ],
        "certificate_cvar_parity": certificate[
            "cvar_parity_within_1e_4"
        ],
        "native_local_beam_nonunit_parity": beam[
            "complete_constant_nonunit_parity"
        ],
    }
    return {
        "schema": "th08-sem-scale-b-authority-report-v1",
        "semantics_version": (
            TH08_PLAYER_LASER_SCALE_SEMANTICS_VERSION
        ),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python": platform.python_version(),
        },
        "checks": checks,
        "corridor": corridor,
        "certificate": certificate,
        "native_local_beam": beam,
        "passed": all(checks.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    report = build_report()
    encoded = json.dumps(
        report,
        indent=2,
        sort_keys=True,
        allow_nan=False,
    )
    if arguments.output is not None:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
