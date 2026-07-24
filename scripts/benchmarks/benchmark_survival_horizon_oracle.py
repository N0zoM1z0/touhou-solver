#!/usr/bin/env python3
"""Offline comparison of margin and survival-horizon fallbacks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from touhou_control.adversarial import (
    generate_adversarial_scenario,
    reference_clearance_volume,
)
from touhou_control.reachability_oracle import (
    scalar_robust_survival_query,
)
from touhou_control.viability import (
    ControlAction,
    ViabilityConfig,
    build_robust_safety_value_policy,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-start", type=int, default=20260724)
    parser.add_argument("--seeds", type=int, default=24)
    parser.add_argument("--hazards", type=int, default=18)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if args.seeds <= 0 or args.hazards < 0:
        parser.error("seed count must be positive and hazards nonnegative")

    x_axis = np.arange(8.0, 72.1, 8.0, dtype=np.float32)
    y_axis = np.arange(16.0, 80.1, 8.0, dtype=np.float32)
    actions = (
        ControlAction("stay", 0.0, 0.0),
        ControlAction("left", -4.0, 0.0),
        ControlAction("right", 4.0, 0.0),
        ControlAction("up", 0.0, -4.0),
        ControlAction("down", 0.0, 4.0),
    )
    delays = (0, 1, 2)
    config = ViabilityConfig(
        frames_per_layer=2,
        clamp_to_bounds=True,
    )
    total_states = 0
    winning_states = 0
    losing_states = 0
    best_action_set_difference = 0
    margin_loses_guaranteed_frames = 0
    guaranteed_frame_gain = 0
    examples = []
    for seed in range(args.seed_start, args.seed_start + args.seeds):
        scenario = generate_adversarial_scenario(
            seed,
            hazard_count=args.hazards,
            horizon_frames=4,
            left=float(x_axis[0]),
            right=float(x_axis[-1]),
            top=float(y_axis[0]),
            bottom=float(y_axis[-1]),
            maximum_events=2,
        )
        clearance = reference_clearance_volume(
            x_axis=x_axis,
            y_axis=y_axis,
            scenario=scenario,
            player_radius=2.0,
            clearance_cap=48.0,
        )
        margin_policy = build_robust_safety_value_policy(
            x_axis=x_axis,
            y_axis=y_axis,
            clearance_volume=clearance,
            actions=actions,
            delay_frames=delays,
            nominal_delay=1,
            config=config,
            backend="numpy",
        )
        assert margin_policy.action_values is not None
        for active_index, active in enumerate(actions):
            for row in range(len(y_axis)):
                for column in range(len(x_axis)):
                    total_states += 1
                    scalar = scalar_robust_survival_query(
                        x_axis=x_axis,
                        y_axis=y_axis,
                        clearance_volume=clearance,
                        actions=actions,
                        delay_frames=delays,
                        config=config,
                        layer=0,
                        row=row,
                        column=column,
                        active_action=active.name,
                    )
                    if scalar.winning:
                        winning_states += 1
                        continue
                    losing_states += 1
                    margin_values = margin_policy.action_values[
                        0,
                        active_index,
                        :,
                        row,
                        column,
                    ]
                    best_margin = float(np.max(margin_values))
                    margin_actions = tuple(
                        action.name
                        for action, value in zip(actions, margin_values)
                        if float(value) == best_margin
                    )
                    if set(margin_actions) != set(scalar.best_actions):
                        best_action_set_difference += 1
                    margin_guarantee = max(
                        scalar.action_label(action).guaranteed_frames
                        for action in margin_actions
                    )
                    gain = (
                        scalar.state_label.guaranteed_frames
                        - margin_guarantee
                    )
                    if gain <= 0:
                        continue
                    margin_loses_guaranteed_frames += 1
                    guaranteed_frame_gain += gain
                    if len(examples) < 24:
                        examples.append(
                            {
                                "seed": seed,
                                "active_action": active.name,
                                "row": row,
                                "column": column,
                                "margin_actions": margin_actions,
                                "survival_actions": scalar.best_actions,
                                "margin_guaranteed_frames": (
                                    margin_guarantee
                                ),
                                "survival_guaranteed_frames": (
                                    scalar.state_label.guaranteed_frames
                                ),
                                "margin_value": best_margin,
                                "survival_bottleneck_margin": (
                                    scalar.state_label.bottleneck_margin
                                ),
                            }
                        )

    report = {
        "schema": "robust-survival-horizon-oracle-benchmark-v1",
        "seed_start": args.seed_start,
        "seed_count": args.seeds,
        "hazards_per_seed": args.hazards,
        "horizon_frames": 4,
        "frames_per_layer": config.frames_per_layer,
        "delay_frames": delays,
        "total_states": total_states,
        "winning_states": winning_states,
        "losing_states": losing_states,
        "losing_best_action_set_difference_count": (
            best_action_set_difference
        ),
        "margin_fallback_loses_guaranteed_frames_count": (
            margin_loses_guaranteed_frames
        ),
        "guaranteed_frame_gain_sum": guaranteed_frame_gain,
        "scope": (
            "Deterministic game-neutral adversarial lattice experiment. "
            "It validates fallback semantics for the discrete model; it is "
            "not a TH08 physical-survival result."
        ),
        "examples": examples,
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
