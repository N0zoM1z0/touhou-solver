#!/usr/bin/env python3
"""Emit the deterministic behavior baseline for corridor refactoring."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

import corridor_planner as compatibility
from corridor_planner import (
    CorridorBounds,
    CorridorConfig,
    CorridorPlan,
    MovingAabbHazard,
    RobustControlSpec,
    SegmentHazard,
    _aabb_clearance_volume,
    _axis,
    _segment_clearance_field,
    plan_corridor,
)
from touhou_control.viability import ControlAction, ViabilityQuery


SCHEMA = "touhou-corridor-refactor-characterization-v1"
PUBLIC_COMPATIBILITY_NAMES = (
    "AabbHazard",
    "AabbTrajectoryHazard",
    "CorridorBounds",
    "CorridorConfig",
    "CorridorPlan",
    "CorridorPoint",
    "MovingAabbHazard",
    "PiecewiseAabbHazard",
    "RobustControlSpec",
    "SegmentHazard",
    "SegmentTrajectoryHazard",
    "plan_corridor",
)


def _array_digest(values: np.ndarray) -> str:
    array = np.ascontiguousarray(values)
    canonical = array.astype(array.dtype.newbyteorder("<"), copy=False)
    shape = ",".join(str(value) for value in canonical.shape)
    digest = hashlib.sha256()
    digest.update(f"{canonical.dtype.str}|{shape}\0".encode("ascii"))
    digest.update(canonical.tobytes(order="C"))
    return digest.hexdigest()


def _float_record(value: float | np.floating[Any]) -> dict[str, object]:
    numeric = float(value)
    bits = int(
        np.asarray(numeric, dtype=np.float32).view(np.uint32).item()
    )
    if math.isfinite(numeric):
        display: float | str = numeric
    elif numeric > 0.0:
        display = "inf"
    else:
        display = "-inf"
    return {"value": display, "float32_bits": f"{bits:08x}"}


def _point_record(point: object | None) -> dict[str, object] | None:
    if point is None:
        return None
    return {
        "frame": int(getattr(point, "frame")),
        "x": _float_record(getattr(point, "x")),
        "y": _float_record(getattr(point, "y")),
        "clearance": _float_record(getattr(point, "clearance")),
    }


def _plan_record(plan: CorridorPlan) -> dict[str, object]:
    return {
        "reachable": plan.reachable,
        "path": [_point_record(point) for point in plan.path],
        "bottleneck_clearance": _float_record(
            plan.bottleneck_clearance
        ),
        "terminal_clearance": _float_record(plan.terminal_clearance),
        "lane": plan.lane,
        "gate": _point_record(plan.gate),
        "reason": plan.reason,
        "planning_mode": plan.planning_mode,
        "initial_safe_action_count": plan.initial_safe_action_count,
        "initial_repair_volume": plan.initial_repair_volume,
        "viability_grid_step": (
            None
            if plan.viability_grid_step is None
            else _float_record(plan.viability_grid_step)
        ),
    }


def _query_record(query: ViabilityQuery) -> dict[str, object]:
    return {
        "available": query.available,
        "layer": query.layer,
        "row": query.row,
        "column": query.column,
        "active_action": query.active_action,
        "state_viable": query.state_viable,
        "safe_actions": list(query.safe_actions),
        "repair_volumes": [
            [name, volume] for name, volume in query.repair_volumes
        ],
        "recovery_distances": [
            [name, _float_record(distance)]
            for name, distance in query.recovery_distances
        ],
        "position_error": _float_record(query.position_error),
        "reason": query.reason,
        "survival_frames": query.survival_frames,
        "survival_bottleneck_margin": (
            None
            if query.survival_bottleneck_margin is None
            else _float_record(query.survival_bottleneck_margin)
        ),
        "survival_best_actions": list(query.survival_best_actions),
    }


def _clearance_report() -> dict[str, object]:
    x_axis = _axis(0.0, 32.0, 8.0)
    y_axis = _axis(0.0, 32.0, 8.0)
    grid_x, grid_y = np.meshgrid(x_axis, y_axis)
    horizon_frames = 8
    aabb_volume = _aabb_clearance_volume(
        grid_x,
        grid_y,
        (
            MovingAabbHazard(
                x=8.0,
                y=8.0,
                velocity_x=2.0,
                velocity_y=1.0,
                half_width=2.0,
                half_height=3.0,
                base_uncertainty=0.5,
                uncertainty_per_frame=0.125,
            ),
            MovingAabbHazard(
                x=24.0,
                y=24.0,
                velocity_x=-1.0,
                velocity_y=0.0,
                half_width=3.0,
                half_height=2.0,
                base_uncertainty=0.25,
            ),
        ),
        horizon_frames=horizon_frames,
        player_radius=1.0,
        clearance_cap=32.0,
    )
    segment = (
        SegmentHazard(
            origin_x=16.0,
            origin_y=16.0,
            angle=0.0,
            tail=-6.0,
            head=6.0,
            half_width=1.5,
            base_uncertainty=0.25,
            uncertainty_per_frame=0.125,
        ),
    )
    volume = aabb_volume.copy()
    for frame in range(horizon_frames + 1):
        volume[frame] = np.minimum(
            volume[frame],
            _segment_clearance_field(
                grid_x,
                grid_y,
                segment,
                frame=frame,
                player_radius=1.0,
            ),
        )
    selected_coordinates = (
        (0, 0, 0),
        (0, 1, 1),
        (2, 2, 2),
        (4, 3, 2),
        (8, 3, 3),
        (8, 4, 4),
    )
    return {
        "shape": list(volume.shape),
        "dtype": volume.dtype.str,
        "array_sha256": _array_digest(volume),
        "selected_samples": [
            {
                "frame": frame,
                "row": row,
                "column": column,
                "clearance": _float_record(volume[frame, row, column]),
            }
            for frame, row, column in selected_coordinates
        ],
        "sign_counts_by_frame": [
            {
                "negative": int(np.count_nonzero(frame < 0.0)),
                "zero": int(np.count_nonzero(frame == 0.0)),
                "positive": int(np.count_nonzero(frame > 0.0)),
            }
            for frame in volume
        ],
    }


def _legacy_plan() -> CorridorPlan:
    bounds = CorridorBounds(0.0, 96.0, 0.0, 96.0)
    config = CorridorConfig(
        grid_step=8.0,
        frames_per_layer=4,
        horizon_frames=32,
        cardinal_speed=4.0,
        diagonal_axis_speed=2.8284270763397217,
        preferred_clearance=6.0,
    )
    hazards = tuple(
        MovingAabbHazard(
            x=float(x),
            y=30.0,
            velocity_x=0.0,
            velocity_y=1.5,
            half_width=5.0,
            half_height=5.0,
        )
        for x in range(32, 97, 8)
    )
    return plan_corridor(
        start_x=48.0,
        start_y=88.0,
        bounds=bounds,
        aabbs=hazards,
        preferred_x=48.0,
        preferred_y=64.0,
        config=config,
    )


def _robust_report() -> dict[str, object]:
    actions = (
        ControlAction("stay", 0.0, 0.0),
        ControlAction("left", -4.0, 0.0),
        ControlAction("right", 4.0, 0.0),
        ControlAction("up", 0.0, -4.0),
        ControlAction("down", 0.0, 4.0),
    )
    plan = plan_corridor(
        start_x=8.0,
        start_y=28.0,
        bounds=CorridorBounds(0.0, 32.0, 0.0, 32.0),
        aabbs=(
            MovingAabbHazard(
                x=16.0,
                y=16.0,
                velocity_x=0.0,
                velocity_y=0.0,
                half_width=4.0,
                half_height=4.0,
                base_uncertainty=0.5,
            ),
        ),
        preferred_x=4.0,
        preferred_y=8.0,
        config=CorridorConfig(
            grid_step=4.0,
            frames_per_layer=2,
            horizon_frames=8,
            cardinal_speed=4.0,
            diagonal_axis_speed=2.8284270763397217,
            player_radius=1.0,
            required_clearance=0.0,
            preferred_clearance=4.0,
            danger_radius=16.0,
        ),
        robust_control=RobustControlSpec(
            actions=actions,
            delay_frames=(0, 1),
            nominal_delay=1,
            active_action="stay",
            survival_labels=True,
        ),
    )
    if plan.viability_policy is None:
        raise AssertionError("characterization robust policy is missing")
    policy = plan.viability_policy
    root = policy.query(
        frame=0,
        x=8.0,
        y=28.0,
        active_action="stay",
    )
    path_query = policy.query(
        frame=plan.path[1].frame,
        x=plan.path[1].x,
        y=plan.path[1].y,
        active_action=plan.path[1].x < 8.0 and "left" or "stay",
    )
    return {
        "plan": _plan_record(plan),
        "viable_shape": list(policy.viable.shape),
        "viable_sha256": _array_digest(policy.viable),
        "safe_action_masks_shape": list(policy.safe_action_masks.shape),
        "safe_action_masks_sha256": _array_digest(
            policy.safe_action_masks
        ),
        "viable_states_by_layer": [
            int(np.count_nonzero(policy.viable[layer]))
            for layer in range(policy.viable.shape[0])
        ],
        "safe_action_bits_by_layer": [
            sum(
                int(value).bit_count()
                for value in policy.safe_action_masks[layer].flat
            )
            for layer in range(policy.safe_action_masks.shape[0])
        ],
        "root_query": _query_record(root),
        "path_query": _query_record(path_query),
    }


def build_report() -> dict[str, object]:
    missing = [
        name
        for name in PUBLIC_COMPATIBILITY_NAMES
        if not hasattr(compatibility, name)
    ]
    if missing:
        raise AssertionError(f"missing compatibility imports: {missing}")
    payload: dict[str, object] = {
        "schema": SCHEMA,
        "public_compatibility_names": list(PUBLIC_COMPATIBILITY_NAMES),
        "clearance": _clearance_report(),
        "legacy_plan": _plan_record(_legacy_plan()),
        "robust": _robust_report(),
    }
    canonical = json.dumps(
        payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    payload["canonical_sha256"] = hashlib.sha256(canonical).hexdigest()
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", nargs="?", type=Path)
    args = parser.parse_args(argv)
    rendered = json.dumps(
        build_report(),
        allow_nan=False,
        indent=2,
        sort_keys=True,
    )
    if args.output is None:
        print(rendered)
    else:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
