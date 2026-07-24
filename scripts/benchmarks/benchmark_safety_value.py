#!/usr/bin/env python3
"""Offline benchmark of Boolean viability and max-min safety value."""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

import numpy as np

from th08_corridor_adapter import (
    TH08_CORRIDOR_CONFIG,
    TH08_VIABILITY_ACTIONS,
)
from touhou_control import native_backend
from touhou_control.viability import (
    ViabilityConfig,
    build_robust_safety_value_policy,
    build_robust_viability_policy,
)


def _summary(values: list[float]) -> dict[str, object]:
    ordered = sorted(values)
    p95_index = min(len(ordered) - 1, int(0.95 * len(ordered)))
    return {
        "median": statistics.median(ordered),
        "p95": ordered[p95_index],
        "minimum": ordered[0],
        "samples": ordered,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=87008)
    parser.add_argument("--repeats", type=int, default=7)
    parser.add_argument(
        "--horizon",
        type=int,
        default=TH08_CORRIDOR_CONFIG.horizon_frames,
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if (
        args.repeats <= 0
        or args.horizon <= 0
        or args.horizon % TH08_CORRIDOR_CONFIG.frames_per_layer
    ):
        parser.error(
            "repeats and horizon must be positive; horizon must divide "
            "into complete control layers"
        )

    config = TH08_CORRIDOR_CONFIG
    x_axis = np.arange(
        8.0,
        376.0 + 0.5 * config.grid_step,
        config.grid_step,
        dtype=np.float32,
    )
    y_axis = np.arange(
        16.0,
        432.0 + 0.5 * config.grid_step,
        config.grid_step,
        dtype=np.float32,
    )
    rng = np.random.default_rng(args.seed)
    clearance = rng.uniform(
        -16.0,
        64.0,
        size=(
            config.horizon_frames + 1,
            len(y_axis),
            len(x_axis),
        ),
    ).astype(np.float32)
    clearance = clearance[: args.horizon + 1]
    viability_config = ViabilityConfig(
        frames_per_layer=config.frames_per_layer,
        required_clearance=config.required_clearance,
        clamp_to_bounds=True,
    )
    delays = tuple(range(1, config.frames_per_layer - 1))
    nominal_delay = delays[len(delays) // 2]

    # Prewarm the shared transition table before measuring either recurrence.
    build_robust_viability_policy(
        x_axis=x_axis,
        y_axis=y_axis,
        clearance_volume=clearance,
        actions=TH08_VIABILITY_ACTIONS,
        delay_frames=delays,
        nominal_delay=nominal_delay,
        config=viability_config,
        backend="native",
    )

    boolean_times: list[float] = []
    value_times: list[float] = []
    pruned_policy_times: list[float] = []
    boolean = None
    value = None
    pruned_policy = None
    for _ in range(args.repeats):
        started = time.perf_counter()
        boolean = build_robust_viability_policy(
            x_axis=x_axis,
            y_axis=y_axis,
            clearance_volume=clearance,
            actions=TH08_VIABILITY_ACTIONS,
            delay_frames=delays,
            nominal_delay=nominal_delay,
            config=viability_config,
            backend="native",
        )
        boolean_times.append((time.perf_counter() - started) * 1000.0)

        started = time.perf_counter()
        value = build_robust_safety_value_policy(
            x_axis=x_axis,
            y_axis=y_axis,
            clearance_volume=clearance,
            actions=TH08_VIABILITY_ACTIONS,
            delay_frames=delays,
            nominal_delay=nominal_delay,
            config=viability_config,
            backend="native",
        )
        value_times.append((time.perf_counter() - started) * 1000.0)

        started = time.perf_counter()
        pruned_policy = native_backend.build_safety_policy_arrays(
            x_axis=x_axis,
            y_axis=y_axis,
            clearance_volume=clearance,
            velocity_x=np.asarray(
                [action.velocity_x for action in TH08_VIABILITY_ACTIONS],
                dtype=np.float64,
            ),
            velocity_y=np.asarray(
                [action.velocity_y for action in TH08_VIABILITY_ACTIONS],
                dtype=np.float64,
            ),
            delay_frames=np.asarray(delays, dtype=np.int32),
            frames_per_layer=config.frames_per_layer,
            clamp_to_bounds=True,
        )
        pruned_policy_times.append(
            (time.perf_counter() - started) * 1000.0
        )

    assert (
        boolean is not None
        and value is not None
        and pruned_policy is not None
    )
    pruned_values, pruned_masks = pruned_policy
    threshold_viable, threshold_masks = value.threshold_arrays(
        config.required_clearance
    )
    parity = bool(
        np.array_equal(threshold_viable, boolean.viable)
        and np.array_equal(threshold_masks, boolean.safe_action_masks)
    )
    value_parity = bool(
        np.allclose(
            pruned_values,
            value.state_values,
            rtol=0.0,
            atol=2e-6,
        )
    )
    best_values = np.max(value.action_values, axis=2)
    best_bits = np.left_shift(
        np.uint32(1),
        np.arange(len(TH08_VIABILITY_ACTIONS), dtype=np.uint32),
    )[None, None, :, None, None]
    expected_best_masks = np.bitwise_or.reduce(
        np.where(
            value.action_values == best_values[:, :, None],
            best_bits,
            np.uint32(0),
        ),
        axis=2,
    )
    best_action_parity = bool(
        np.array_equal(pruned_masks, expected_best_masks)
    )
    result = {
        "schema": "touhou_robust_safety_value_benchmark_v1",
        "configuration": {
            "seed": args.seed,
            "repeats": args.repeats,
            "grid_shape": [len(y_axis), len(x_axis)],
            "horizon_frames": args.horizon,
            "frames_per_layer": config.frames_per_layer,
            "action_count": len(TH08_VIABILITY_ACTIONS),
            "delay_support": delays,
        },
        "boolean_ms": _summary(boolean_times),
        "safety_value_ms": _summary(value_times),
        "pruned_safety_policy_ms": _summary(pruned_policy_times),
        "median_time_ratio": (
            statistics.median(value_times)
            / statistics.median(boolean_times)
        ),
        "pruned_median_time_ratio": (
            statistics.median(pruned_policy_times)
            / statistics.median(boolean_times)
        ),
        "threshold_parity": parity,
        "pruned_value_parity": value_parity,
        "pruned_best_action_parity": best_action_parity,
        "boolean_output_bytes": (
            boolean.viable.nbytes + boolean.safe_action_masks.nbytes
        ),
        "safety_value_output_bytes": (
            value.state_values.nbytes + value.action_values.nbytes
        ),
        "pruned_safety_policy_output_bytes": (
            pruned_values.nbytes + pruned_masks.nbytes
        ),
    }
    payload = json.dumps(result, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0 if parity and value_parity and best_action_parity else 1


if __name__ == "__main__":
    raise SystemExit(main())
