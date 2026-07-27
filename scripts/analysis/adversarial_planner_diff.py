#!/usr/bin/env python3
"""Offline differential of dense random trajectories and the scalar oracle."""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import replace
from pathlib import Path

import numpy as np

from corridor_planner import (
    CorridorConfig,
    PiecewiseAabbHazard,
)
from touhou_control import native_backend
from touhou_control.corridor.clearance import hazard_clearance_volume
from touhou_control.adversarial import (
    AdversarialScenario,
    generate_adversarial_scenario,
    reference_clearance_volume,
)


def _lower(scenario: AdversarialScenario) -> tuple[PiecewiseAabbHazard, ...]:
    if any(
        hazard.active_from_frame != 0
        or hazard.inactive_from_frame is not None
        for hazard in scenario.hazards
    ):
        raise ValueError(
            "piecewise differential lowering does not encode birth windows"
        )
    return tuple(
        PiecewiseAabbHazard(
            motion=hazard.motion,
            half_width=hazard.half_width,
            half_height=hazard.half_height,
        )
        for hazard in scenario.hazards
    )


def compare_scenario(
    scenario: AdversarialScenario,
    *,
    grid_step: float,
    player_radius: float = 2.0,
    clearance_cap: float = 48.0,
    tolerance: float = 5e-5,
) -> dict[str, object]:
    x_axis = np.arange(8.0, 376.0 + 0.5 * grid_step, grid_step, dtype=np.float32)
    y_axis = np.arange(16.0, 432.0 + 0.5 * grid_step, grid_step, dtype=np.float32)
    grid_x, grid_y = np.meshgrid(x_axis, y_axis)
    config = CorridorConfig(
        grid_step=grid_step,
        frames_per_layer=1,
        horizon_frames=max(1, scenario.horizon_frames),
        player_radius=player_radius,
        danger_radius=clearance_cap,
    )
    lower_started = time.perf_counter()
    lowered = _lower(scenario)
    lower_ms = (time.perf_counter() - lower_started) * 1000.0
    solve_started = time.perf_counter()
    actual = hazard_clearance_volume(
        grid_x,
        grid_y,
        aabbs=(),
        piecewise_aabbs=lowered,
        segments=(),
        segment_trajectories=(),
        config=config,
    )
    solve_ms = (time.perf_counter() - solve_started) * 1000.0
    if scenario.horizon_frames == 0:
        actual = actual[:1]
    reference = reference_clearance_volume(
        x_axis=x_axis,
        y_axis=y_axis,
        scenario=scenario,
        player_radius=player_radius,
        clearance_cap=clearance_cap,
    )
    difference = np.abs(actual - reference)
    maximum = float(difference.max(initial=0.0))
    mismatch = np.argwhere(difference > tolerance)
    first = mismatch[0].tolist() if mismatch.size else None
    return {
        "seed": scenario.seed,
        "hazard_count": len(scenario.hazards),
        "horizon_frames": scenario.horizon_frames,
        "grid_step": grid_step,
        "backend": "native" if native_backend.available() else "python",
        "representation": "sparse_piecewise",
        "lower_ms": lower_ms,
        "clearance_ms": solve_ms,
        "maximum_absolute_error": maximum,
        "tolerance": tolerance,
        "first_mismatch": first,
        "passed": first is None,
    }


def shrink_failure(
    scenario: AdversarialScenario,
    *,
    grid_step: float,
    tolerance: float,
) -> AdversarialScenario:
    """Delta-debug a mismatch down to a smaller hazard subset."""

    hazards = list(scenario.hazards)
    granularity = 2
    while len(hazards) >= 2:
        chunk_size = max(1, (len(hazards) + granularity - 1) // granularity)
        reduced = False
        for start in range(0, len(hazards), chunk_size):
            candidate = hazards[:start] + hazards[start + chunk_size :]
            if not candidate:
                continue
            candidate_scenario = replace(scenario, hazards=tuple(candidate))
            if not compare_scenario(
                candidate_scenario,
                grid_step=grid_step,
                tolerance=tolerance,
            )["passed"]:
                hazards = candidate
                granularity = max(2, granularity - 1)
                reduced = True
                break
        if reduced:
            continue
        if granularity >= len(hazards):
            break
        granularity = min(len(hazards), granularity * 2)
    return replace(scenario, hazards=tuple(hazards))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=8008)
    parser.add_argument("--seeds", type=int, default=4)
    parser.add_argument("--hazards", type=int, default=2048)
    parser.add_argument("--horizon", type=int, default=32)
    parser.add_argument("--grid-step", type=float, default=32.0)
    parser.add_argument("--maximum-events", type=int, default=3)
    parser.add_argument("--tolerance", type=float, default=5e-5)
    parser.add_argument("--output", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    reports: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []
    for offset in range(args.seeds):
        scenario = generate_adversarial_scenario(
            args.seed + offset,
            hazard_count=args.hazards,
            horizon_frames=args.horizon,
            maximum_events=args.maximum_events,
        )
        report = compare_scenario(
            scenario,
            grid_step=args.grid_step,
            tolerance=args.tolerance,
        )
        reports.append(report)
        if not report["passed"]:
            reduced = shrink_failure(
                scenario,
                grid_step=args.grid_step,
                tolerance=args.tolerance,
            )
            failures.append(
                {
                    **report,
                    "reduced_hazard_count": len(reduced.hazards),
                }
            )
    result = {
        "schema": "touhou_adversarial_planner_diff_v1",
        "configuration": {
            "seed": args.seed,
            "seeds": args.seeds,
            "hazards": args.hazards,
            "horizon": args.horizon,
            "grid_step": args.grid_step,
            "maximum_events": args.maximum_events,
            "tolerance": args.tolerance,
        },
        "reports": reports,
        "failures": failures,
        "passed": not failures,
    }
    payload = json.dumps(result, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
