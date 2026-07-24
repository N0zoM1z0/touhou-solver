"""Shared generators and reporting for separated clearance benchmarks."""

from __future__ import annotations

import json
import statistics
import time
from dataclasses import replace
from pathlib import Path
from typing import Sequence

from corridor_planner import (
    MovingAabbHazard,
    RobustControlSpec,
    SegmentHazard,
    plan_corridor,
)
from th08_corridor_adapter import (
    TH08_CORRIDOR_CONFIG,
    TH08_PLAYFIELD,
    TH08_VIABILITY_ACTIONS,
)
from touhou_control.packed_hazards import PackedSegmentFrames


def moving_aabbs(
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


def static_segments(
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


def packed_segment_trajectories(
    count: int,
    horizon_frames: int,
) -> PackedSegmentFrames:
    frames = []
    for frame in range(horizon_frames + 1):
        frames.append(
            tuple(
                (
                    192.0 + (index % 9 - 4) * 3.0,
                    100.0 + (index % 20) * 12.0,
                    (index % 32) * 0.17 + frame * 0.002,
                    0.0,
                    80.0 + (index % 5) * 30.0,
                    3.0 + index % 4,
                    frame * 0.05,
                    0.0,
                )
                for index in range(count)
                if (frame + index) % 17 != 0
            )
        )
    return PackedSegmentFrames.from_frame_rows(frames)


def run_corridor_benchmark(
    *,
    identity: str,
    aabbs: tuple[MovingAabbHazard, ...],
    segments: tuple[SegmentHazard, ...],
    packed_segments: PackedSegmentFrames | None,
    runs: int,
    delay_support: Sequence[int],
    nominal_delay: int,
    danger_radius: float,
    output: Path | None,
) -> dict[str, object]:
    robust_control = RobustControlSpec(
        actions=TH08_VIABILITY_ACTIONS,
        delay_frames=tuple(delay_support),
        nominal_delay=nominal_delay,
        active_action="stay",
    )
    config = replace(
        TH08_CORRIDOR_CONFIG,
        danger_radius=danger_radius,
    )
    samples = []
    phase_samples: dict[str, list[float]] = {}
    backend = None
    for _ in range(runs):
        started = time.perf_counter()
        plan = plan_corridor(
            start_x=192.0,
            start_y=400.0,
            bounds=TH08_PLAYFIELD,
            aabbs=aabbs,
            segments=segments,
            packed_segments=packed_segments,
            preferred_x=192.0,
            preferred_y=368.0,
            config=config,
            robust_control=robust_control,
        )
        samples.append((time.perf_counter() - started) * 1000.0)
        backend = plan.viability_backend
        for key, value in plan.solver_timing_ms:
            phase_samples.setdefault(key, []).append(value)
    report: dict[str, object] = {
        "schema": "touhou-clearance-benchmark-v2",
        "workload_identity": identity,
        "hazards": {
            "moving_aabbs": len(aabbs),
            "static_segments": len(segments),
            "packed_segment_samples": (
                0 if packed_segments is None else packed_segments.sample_count
            ),
            "maximum_segments_per_frame": (
                0
                if packed_segments is None
                else max(
                    (
                        int(
                            packed_segments.frame_offsets[frame + 1]
                            - packed_segments.frame_offsets[frame]
                        )
                        for frame in range(packed_segments.frame_count)
                    ),
                    default=0,
                )
            ),
        },
        "lattice": {
            "frames": config.horizon_frames + 1,
            "columns": (
                int(
                    round(
                        (TH08_PLAYFIELD.right - TH08_PLAYFIELD.left)
                        / config.grid_step
                    )
                )
                + 1
            ),
            "rows": (
                int(
                    round(
                        (TH08_PLAYFIELD.bottom - TH08_PLAYFIELD.top)
                        / config.grid_step
                    )
                )
                + 1
            ),
            "grid_step": config.grid_step,
            "danger_radius": config.danger_radius,
        },
        "runs": runs,
        "timing_boundary": (
            "hazards are pre-lowered; samples include the complete corridor "
            "solve but exclude workload generation and TH08 sensor decoding"
        ),
        "delay_support": list(delay_support),
        "nominal_delay": nominal_delay,
        "viability_backend": backend,
        "cold_ms": samples[0],
        "warm_median_ms": statistics.median(samples[1:] or samples),
        "samples_ms": samples,
        "phase_warm_median_ms": {
            key: statistics.median(values[1:] or values)
            for key, values in phase_samples.items()
        },
    }
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return report


def validate_common_arguments(
    *,
    counts: Sequence[int],
    runs: int,
    forecast_frames: int,
    delay_support: Sequence[int],
    nominal_delay: int,
    danger_radius: float,
) -> bool:
    return (
        all(count >= 0 for count in counts)
        and runs >= 1
        and forecast_frames >= 0
        and tuple(sorted(set(delay_support))) == tuple(delay_support)
        and bool(delay_support)
        and delay_support[0] >= 0
        and delay_support[-1] <= TH08_CORRIDOR_CONFIG.frames_per_layer
        and nominal_delay in delay_support
        and danger_radius > 0.0
    )
