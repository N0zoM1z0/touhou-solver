#!/usr/bin/env python3
"""Benchmark the TH08 robust corridor solve with deterministic heavy hazards."""

from __future__ import annotations

import argparse
import json
import statistics
import time
from dataclasses import replace
from pathlib import Path

from corridor_planner import (
    MovingAabbHazard,
    RobustControlSpec,
    SegmentHazard,
    SegmentTrajectoryHazard,
)
from corridor_planner import plan_corridor
from th08_corridor_adapter import (
    TH08_CORRIDOR_CONFIG,
    TH08_PLAYFIELD,
    TH08_VIABILITY_ACTIONS,
)


def _aabbs(
    count: int,
    forecast_frames: int,
) -> tuple[MovingAabbHazard, ...]:
    hazards = []
    for index in range(count):
        velocity_x = ((index % 7) - 3) * 0.31
        velocity_y = 0.55 + (index % 5) * 0.17
        growth = 0.35 if index % 11 == 0 else 0.05
        hazards.append(
            MovingAabbHazard(
                x=8.0 + (index * 17) % 369 + velocity_x * forecast_frames,
                y=16.0 + (index * 29) % 417 + velocity_y * forecast_frames,
                velocity_x=velocity_x,
                velocity_y=velocity_y,
                half_width=2.0 + index % 3,
                half_height=2.0 + index % 4,
                base_uncertainty=(
                    (3.0 if index % 11 == 0 else 0.0)
                    + growth * forecast_frames
                ),
                uncertainty_per_frame=growth,
            )
        )
    return tuple(hazards)


def _segments(
    count: int,
    forecast_frames: int,
) -> tuple[SegmentHazard, ...]:
    return tuple(
        SegmentHazard(
            origin_x=192.0,
            origin_y=100.0 + (index % 20) * 12.0,
            angle=(index % 32) * 0.17,
            tail=0.0,
            head=80.0 + (index % 5) * 30.0,
            half_width=3.0 + index % 4,
            base_uncertainty=0.4 * forecast_frames,
            uncertainty_per_frame=0.4,
        )
        for index in range(count)
    )


def _segment_trajectories(
    count: int,
    horizon_frames: int,
) -> tuple[SegmentTrajectoryHazard, ...]:
    trajectories = []
    for index in range(count):
        samples = []
        for frame in range(horizon_frames + 1):
            if (frame + index) % 17 == 0:
                samples.append(None)
                continue
            samples.append(
                SegmentHazard(
                    origin_x=192.0 + (index % 9 - 4) * 3.0,
                    origin_y=100.0 + (index % 20) * 12.0,
                    angle=(index % 32) * 0.17 + frame * 0.002,
                    tail=0.0,
                    head=80.0 + (index % 5) * 30.0,
                    half_width=3.0 + index % 4,
                    base_uncertainty=frame * 0.05,
                )
            )
        trajectories.append(SegmentTrajectoryHazard(tuple(samples)))
    return tuple(trajectories)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aabbs", type=int, default=1500)
    parser.add_argument("--segments", type=int, default=250)
    parser.add_argument("--trajectory-segments", type=int, default=0)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--forecast-frames", type=int, default=80)
    parser.add_argument(
        "--delay-support",
        type=int,
        nargs="+",
        default=(1, 2, 3),
    )
    parser.add_argument("--nominal-delay", type=int, default=2)
    parser.add_argument(
        "--danger-radius",
        type=float,
        default=TH08_CORRIDOR_CONFIG.danger_radius,
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if (
        args.aabbs < 0
        or args.segments < 0
        or args.trajectory_segments < 0
        or args.runs < 1
        or args.forecast_frames < 0
        or tuple(sorted(set(args.delay_support)))
        != tuple(args.delay_support)
        or not args.delay_support
        or args.delay_support[0] < 0
        or args.delay_support[-1] > TH08_CORRIDOR_CONFIG.frames_per_layer
        or args.nominal_delay not in args.delay_support
    ):
        parser.error("invalid hazard, run, or delay arguments")

    aabbs = _aabbs(args.aabbs, args.forecast_frames)
    segments = _segments(args.segments, args.forecast_frames)
    segment_trajectories = _segment_trajectories(
        args.trajectory_segments,
        TH08_CORRIDOR_CONFIG.horizon_frames,
    )
    robust_control = RobustControlSpec(
        actions=TH08_VIABILITY_ACTIONS,
        delay_frames=tuple(args.delay_support),
        nominal_delay=args.nominal_delay,
        active_action="stay",
    )
    config = replace(
        TH08_CORRIDOR_CONFIG,
        danger_radius=args.danger_radius,
    )
    samples = []
    phase_samples: dict[str, list[float]] = {}
    backend = None
    for _ in range(args.runs):
        started = time.perf_counter()
        plan = plan_corridor(
            start_x=192.0,
            start_y=400.0,
            bounds=TH08_PLAYFIELD,
            aabbs=aabbs,
            segments=segments,
            segment_trajectories=segment_trajectories,
            preferred_x=192.0,
            preferred_y=368.0,
            config=config,
            robust_control=robust_control,
        )
        samples.append((time.perf_counter() - started) * 1000.0)
        backend = plan.viability_backend
        for key, value in plan.solver_timing_ms:
            phase_samples.setdefault(key, []).append(value)

    report = {
        "aabbs": args.aabbs,
        "segments": args.segments,
        "trajectory_segments": args.trajectory_segments,
        "runs": args.runs,
        "forecast_frames": args.forecast_frames,
        "danger_radius": args.danger_radius,
        "delay_support": args.delay_support,
        "nominal_delay": args.nominal_delay,
        "viability_backend": backend,
        "cold_ms": samples[0],
        "warm_median_ms": statistics.median(samples[1:] or samples),
        "samples_ms": samples,
        "phase_warm_median_ms": {
            key: statistics.median(values[1:] or values)
            for key, values in phase_samples.items()
        },
    }
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
