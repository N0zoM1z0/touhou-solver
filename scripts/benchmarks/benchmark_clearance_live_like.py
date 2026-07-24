#!/usr/bin/env python3
"""Benchmark TH08 live-like moving AABBs plus packed laser trajectories."""

from __future__ import annotations

import argparse
from pathlib import Path

from benchmarks.clearance_benchmark_support import (
    moving_aabbs,
    packed_segment_trajectories,
    run_corridor_benchmark,
    validate_common_arguments,
)
from th08_corridor_adapter import TH08_CORRIDOR_CONFIG


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aabbs", type=int, default=800)
    parser.add_argument("--lasers", type=int, default=200)
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--forecast-frames", type=int, default=27)
    parser.add_argument(
        "--delay-support",
        type=int,
        nargs="+",
        default=(1, 2, 3, 4, 5, 6),
    )
    parser.add_argument("--nominal-delay", type=int, default=3)
    parser.add_argument(
        "--danger-radius",
        type=float,
        default=TH08_CORRIDOR_CONFIG.danger_radius,
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not validate_common_arguments(
        counts=(args.aabbs, args.lasers),
        runs=args.runs,
        forecast_frames=args.forecast_frames,
        delay_support=args.delay_support,
        nominal_delay=args.nominal_delay,
        danger_radius=args.danger_radius,
    ):
        parser.error("invalid hazard, run, cap, or delay arguments")
    run_corridor_benchmark(
        identity="th08_live_like_aabb_plus_packed_laser_trajectory",
        aabbs=moving_aabbs(args.aabbs, args.forecast_frames),
        segments=(),
        packed_segments=packed_segment_trajectories(
            args.lasers,
            TH08_CORRIDOR_CONFIG.horizon_frames,
        ),
        runs=args.runs,
        delay_support=args.delay_support,
        nominal_delay=args.nominal_delay,
        danger_radius=args.danger_radius,
        output=args.output,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
