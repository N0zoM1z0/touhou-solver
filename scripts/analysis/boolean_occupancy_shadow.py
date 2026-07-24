#!/usr/bin/env python3
"""Test Boolean occupancy semantics before adding a live native kernel."""

from __future__ import annotations

import argparse
import json
import math
import statistics
import time
from pathlib import Path

import numpy as np

from benchmarks.clearance_benchmark_support import (
    moving_aabbs,
    packed_segment_trajectories,
)
from corridor_planner import _axis, _hazard_clearance_volume
from th08_corridor_adapter import (
    TH08_CORRIDOR_CONFIG,
    TH08_PLAYFIELD,
    TH08_VIABILITY_ACTIONS,
)
from touhou_control.viability import (
    RobustViabilityPolicy,
    ViabilityConfig,
    build_robust_viability_policy,
)


def _bit_count(values: np.ndarray) -> int:
    return sum(int(value).bit_count() for value in values.flat)


def _compare_policies(
    exact: RobustViabilityPolicy,
    candidate: RobustViabilityPolicy,
) -> dict[str, int]:
    false_positive_masks = np.bitwise_and(
        candidate.safe_action_masks,
        np.bitwise_not(exact.safe_action_masks),
    )
    false_negative_masks = np.bitwise_and(
        exact.safe_action_masks,
        np.bitwise_not(candidate.safe_action_masks),
    )
    return {
        "false_positive_action_bits": _bit_count(false_positive_masks),
        "false_negative_action_bits": _bit_count(false_negative_masks),
        "false_positive_viable_states": int(
            np.count_nonzero(candidate.viable & ~exact.viable)
        ),
        "false_negative_viable_states": int(
            np.count_nonzero(exact.viable & ~candidate.viable)
        ),
    }


def _build_policy(
    *,
    x_axis: np.ndarray,
    y_axis: np.ndarray,
    clearance: np.ndarray,
    delay_support: tuple[int, ...],
    nominal_delay: int,
) -> tuple[RobustViabilityPolicy, float]:
    started = time.perf_counter()
    policy = build_robust_viability_policy(
        x_axis=x_axis,
        y_axis=y_axis,
        clearance_volume=clearance,
        actions=TH08_VIABILITY_ACTIONS,
        delay_frames=delay_support,
        nominal_delay=nominal_delay,
        config=ViabilityConfig(
            frames_per_layer=TH08_CORRIDOR_CONFIG.frames_per_layer,
            required_clearance=0.0,
            clamp_to_bounds=True,
            repair_radius_cells=1,
        ),
    )
    return policy, (time.perf_counter() - started) * 1000.0


def _rollout_endpoint_queries(
    policy: RobustViabilityPolicy,
    clearance: np.ndarray,
) -> dict[str, int]:
    """Count exact values needed only for representative endpoint ranking."""

    bounds = TH08_PLAYFIELD
    target_x = 192.0
    target_y = 368.0
    query = policy.query(
        frame=0,
        x=192.0,
        y=400.0,
        active_action="stay",
    )
    if not query.state_viable:
        return {"layers": 0, "endpoint_queries": 0, "unique_queries": 0}
    current_x = float(policy.x_axis[query.column])
    current_y = float(policy.y_axis[query.row])
    active_action = "stay"
    exact_queries: list[tuple[int, int, int]] = []
    completed_layers = 0
    for layer in range(policy.layer_count):
        query = policy.query(
            frame=layer * policy.config.frames_per_layer,
            x=current_x,
            y=current_y,
            active_action=active_action,
        )
        if not query.safe_actions:
            break
        candidates = []
        for action_name in query.safe_actions:
            endpoint_x, endpoint_y = policy.transition_endpoint(
                x=current_x,
                y=current_y,
                active_action=active_action,
                next_action=action_name,
            )
            endpoint_x, endpoint_y, row, column, _ = (
                policy.project_to_lattice(x=endpoint_x, y=endpoint_y)
            )
            next_frame = (layer + 1) * policy.config.frames_per_layer
            exact_queries.append((next_frame, row, column))
            hazard_clearance = float(clearance[next_frame, row, column])
            boundary_clearance = min(
                endpoint_x - bounds.left,
                bounds.right - endpoint_x,
                endpoint_y - bounds.top,
                bounds.bottom - endpoint_y,
            )
            robust_clearance = min(hazard_clearance, boundary_clearance)
            candidates.append(
                (
                    (
                        -float(query.repair_volume(action_name)),
                        -robust_clearance,
                        (endpoint_x - target_x) ** 2
                        + (endpoint_y - target_y) ** 2,
                        0.0 if action_name == active_action else 1.0,
                    ),
                    action_name,
                    endpoint_x,
                    endpoint_y,
                )
            )
        _, active_action, current_x, current_y = min(candidates)
        completed_layers += 1
    return {
        "layers": completed_layers,
        "endpoint_queries": len(exact_queries),
        "unique_queries": len(set(exact_queries)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aabbs", type=int, default=50)
    parser.add_argument("--lasers", type=int, default=10)
    parser.add_argument("--forecast-frames", type=int, default=27)
    parser.add_argument(
        "--delay-support",
        type=int,
        nargs="+",
        default=(1, 2, 3),
    )
    parser.add_argument("--nominal-delay", type=int, default=2)
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    delay_support = tuple(args.delay_support)
    if (
        args.aabbs < 0
        or args.lasers < 0
        or args.forecast_frames < 0
        or args.runs < 1
        or tuple(sorted(set(delay_support))) != delay_support
        or not delay_support
        or delay_support[0] < 0
        or delay_support[-1] > TH08_CORRIDOR_CONFIG.frames_per_layer
        or args.nominal_delay not in delay_support
    ):
        parser.error("invalid workload or delay arguments")

    x_axis = _axis(
        TH08_PLAYFIELD.left,
        TH08_PLAYFIELD.right,
        TH08_CORRIDOR_CONFIG.grid_step,
    )
    y_axis = _axis(
        TH08_PLAYFIELD.top,
        TH08_PLAYFIELD.bottom,
        TH08_CORRIDOR_CONFIG.grid_step,
    )
    grid_x, grid_y = np.meshgrid(x_axis, y_axis)
    aabbs = moving_aabbs(args.aabbs, args.forecast_frames)
    packed_segments = packed_segment_trajectories(
        args.lasers,
        TH08_CORRIDOR_CONFIG.horizon_frames,
    )
    clearance_times = []
    clearance = None
    for _ in range(args.runs):
        started = time.perf_counter()
        clearance = _hazard_clearance_volume(
            grid_x,
            grid_y,
            aabbs=aabbs,
            segments=(),
            segment_trajectories=(),
            packed_segments=packed_segments,
            config=TH08_CORRIDOR_CONFIG,
        )
        clearance_times.append((time.perf_counter() - started) * 1000.0)
    assert clearance is not None

    # The current recurrence subtracts nearest-lattice sampling error. A
    # single sign bit therefore cannot preserve its decision boundary.
    maximum_sampling_error = (
        TH08_CORRIDOR_CONFIG.grid_step / math.sqrt(2.0)
    )
    safe_proxy_value = np.float32(maximum_sampling_error + 1.0)
    optimistic_occupancy = np.where(
        clearance > 0.0,
        safe_proxy_value,
        np.float32(-1.0),
    ).astype(np.float32)
    conservative_occupancy = np.where(
        clearance > maximum_sampling_error,
        safe_proxy_value,
        np.float32(-1.0),
    ).astype(np.float32)

    exact, exact_policy_ms = _build_policy(
        x_axis=x_axis,
        y_axis=y_axis,
        clearance=clearance,
        delay_support=delay_support,
        nominal_delay=args.nominal_delay,
    )
    optimistic, optimistic_policy_ms = _build_policy(
        x_axis=x_axis,
        y_axis=y_axis,
        clearance=optimistic_occupancy,
        delay_support=delay_support,
        nominal_delay=args.nominal_delay,
    )
    conservative, conservative_policy_ms = _build_policy(
        x_axis=x_axis,
        y_axis=y_axis,
        clearance=conservative_occupancy,
        delay_support=delay_support,
        nominal_delay=args.nominal_delay,
    )
    result = {
        "schema": "touhou-boolean-occupancy-shadow-v1",
        "status": "shadow_rejected_for_live_parity",
        "configuration": {
            "aabbs": args.aabbs,
            "lasers": args.lasers,
            "forecast_frames": args.forecast_frames,
            "frames": clearance.shape[0],
            "rows": clearance.shape[1],
            "columns": clearance.shape[2],
            "grid_step": TH08_CORRIDOR_CONFIG.grid_step,
            "delay_support": list(delay_support),
            "nominal_delay": args.nominal_delay,
        },
        "maximum_lattice_sampling_error": maximum_sampling_error,
        "exact_clearance_bytes": clearance.nbytes,
        "theoretical_boolean_bytes": clearance.size,
        "clearance_warm_median_ms": statistics.median(
            clearance_times[1:] or clearance_times
        ),
        "policy_ms": {
            "exact": exact_policy_ms,
            "optimistic_sign_only": optimistic_policy_ms,
            "conservative_uniform_margin": conservative_policy_ms,
        },
        "exact_safe_action_bits": _bit_count(exact.safe_action_masks),
        "optimistic_sign_only": _compare_policies(exact, optimistic),
        "conservative_uniform_margin": _compare_policies(
            exact,
            conservative,
        ),
        "query_local_exact_rollout": _rollout_endpoint_queries(
            exact,
            clearance,
        ),
        "interpretation": (
            "The robust recurrence subtracts a transition-specific "
            "nearest-lattice error from clearance. Sign-only occupancy is "
            "optimistic; uniformly inflating occupancy is conservative but "
            "drops valid actions. Exact endpoint ranking touches few cells "
            "but cannot reconstruct intermediate transition admissibility."
        ),
        "timing_boundary": (
            "The Boolean arrays are derived from the exact dense volume to "
            "test semantics only; this artifact makes no occupancy-build "
            "speed claim."
        ),
    }
    if (
        result["conservative_uniform_margin"][
            "false_positive_action_bits"
        ]
        != 0
    ):
        raise RuntimeError("conservative Boolean shadow became optimistic")
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
