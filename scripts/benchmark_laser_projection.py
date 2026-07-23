#!/usr/bin/env python3
"""Benchmark shared TH08 laser lifecycle templates from a retained trace."""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import time
from pathlib import Path

from th08_corridor_adapter import lower_lasers
from th08_laser_model import (
    LaserPhase,
    LaserState,
    _cached_collision_geometry_frames,
)
from th08_live_dodge_agent import Laser


def _laser(body: list[object]) -> Laser:
    (
        origin_x,
        origin_y,
        angle,
        tail,
        head,
        half_width,
        slot,
        maximum_length,
        width,
        current_width,
        speed,
        phase,
        timer,
        flags,
        collision_flag,
    ) = body
    state = LaserState(
        origin_x=float(origin_x),
        origin_y=float(origin_y),
        angle=float(angle),
        tail_distance=float(tail),
        head_distance=float(head),
        maximum_length=float(maximum_length),
        width=float(width),
        speed=float(speed),
        warmup_frames=0,
        active_frames=10_000,
        fade_frames=30,
        collision_enable_frame=0,
        collision_disable_frame=10_000,
        flags=int(flags),
        current_width=float(current_width),
        phase=LaserPhase(int(phase)),
        timer=int(timer),
    )
    return Laser(
        float(origin_x),
        float(origin_y),
        float(angle),
        float(tail),
        float(head),
        float(half_width),
        state,
        int(slot),
        int(collision_flag),
    )


def _measure(callable_) -> float:
    started = time.perf_counter()
    callable_()
    return (time.perf_counter() - started) * 1000.0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--minimum-lasers", type=int, default=200)
    parser.add_argument("--forecast-frames", type=int, default=27)
    parser.add_argument("--horizon-frames", type=int, default=80)
    args = parser.parse_args()

    digest = hashlib.sha256()
    selected = None
    with args.trace.open("rb") as source:
        for raw_line in source:
            digest.update(raw_line)
            row = json.loads(raw_line)
            if (
                selected is None
                and row.get("kind") == "decision"
                and int(row.get("active_lasers", 0))
                >= args.minimum_lasers
            ):
                selected = row
    if selected is None:
        raise SystemExit("trace has no sufficiently dense laser decision")
    lasers = tuple(_laser(body) for body in selected["lasers"])
    kwargs = {
        "snapshot_lag": 1,
        "forecast_frames": args.forecast_frames,
        "horizon_frames": args.horizon_frames,
    }

    uncached_samples = []
    for laser in lasers:
        _cached_collision_geometry_frames.cache_clear()
        uncached_samples.append(
            _measure(lambda laser=laser: lower_lasers((laser,), **kwargs))
        )
    uncached_ms = sum(uncached_samples)

    _cached_collision_geometry_frames.cache_clear()
    projected = ()
    started = time.perf_counter()
    projected = lower_lasers(lasers, **kwargs)
    cold_ms = (time.perf_counter() - started) * 1000.0
    cold_cache = _cached_collision_geometry_frames.cache_info()
    warm_ms = _measure(lambda: lower_lasers(lasers, **kwargs))

    result = {
        "schema": "th08-laser-projection-benchmark-v1",
        "trace": str(args.trace),
        "trace_sha256": digest.hexdigest(),
        "source_frame": int(selected["frame"]),
        "laser_count": len(lasers),
        "trajectory_count": len(projected),
        "forecast_frames": args.forecast_frames,
        "horizon_frames": args.horizon_frames,
        "uncached_sum_ms": uncached_ms,
        "uncached_per_laser_median_ms": statistics.median(
            uncached_samples
        ),
        "shared_template_cold_ms": cold_ms,
        "shared_template_warm_ms": warm_ms,
        "cold_speedup": uncached_ms / cold_ms,
        "cold_cache": {
            "hits": cold_cache.hits,
            "misses": cold_cache.misses,
            "size": cold_cache.currsize,
        },
        "interpretation": (
            "The retained trace lacks phase thresholds, so reconstructed "
            "states use a long active phase. This isolates exact lifecycle "
            "template sharing; it is not a collision-fidelity comparison."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2) + "\n",
        encoding="utf-8",
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
