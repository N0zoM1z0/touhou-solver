#!/usr/bin/env python3
"""Benchmark the TH08 robust corridor solve with deterministic heavy hazards."""

from __future__ import annotations

import argparse
import json
import statistics
import time
from dataclasses import replace

from corridor_planner import MovingAabbHazard, RobustControlSpec, SegmentHazard
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aabbs", type=int, default=1500)
    parser.add_argument("--segments", type=int, default=250)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--forecast-frames", type=int, default=80)
    parser.add_argument(
        "--danger-radius",
        type=float,
        default=TH08_CORRIDOR_CONFIG.danger_radius,
    )
    args = parser.parse_args()
    if (
        args.aabbs < 0
        or args.segments < 0
        or args.runs < 1
        or args.forecast_frames < 0
    ):
        parser.error("hazard counts must be nonnegative and runs positive")

    aabbs = _aabbs(args.aabbs, args.forecast_frames)
    segments = _segments(args.segments, args.forecast_frames)
    robust_control = RobustControlSpec(
        actions=TH08_VIABILITY_ACTIONS,
        delay_frames=(1, 2, 3),
        nominal_delay=2,
        active_action="stay",
    )
    config = replace(
        TH08_CORRIDOR_CONFIG,
        danger_radius=args.danger_radius,
    )
    samples = []
    for _ in range(args.runs):
        started = time.perf_counter()
        plan_corridor(
            start_x=192.0,
            start_y=400.0,
            bounds=TH08_PLAYFIELD,
            aabbs=aabbs,
            segments=segments,
            preferred_x=192.0,
            preferred_y=368.0,
            config=config,
            robust_control=robust_control,
        )
        samples.append((time.perf_counter() - started) * 1000.0)

    print(
        json.dumps(
            {
                "aabbs": args.aabbs,
                "segments": args.segments,
                "runs": args.runs,
                "forecast_frames": args.forecast_frames,
                "danger_radius": args.danger_radius,
                "cold_ms": samples[0],
                "warm_median_ms": statistics.median(samples[1:] or samples),
                "samples_ms": samples,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
