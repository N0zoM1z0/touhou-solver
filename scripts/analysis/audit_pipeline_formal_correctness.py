#!/usr/bin/env python3
"""Audit the hybrid pipeline value against complete tiny-model oracles."""

from __future__ import annotations

import argparse
import json
import statistics
import time
from dataclasses import asdict
from pathlib import Path
from typing import Callable

import numpy as np

from touhou_control.query_survival import (
    PendingCommand,
    QueryLocalSurvivalResult,
    scalar_query_local_survival,
)
from touhou_control.variable_cadence_oracle import (
    scalar_belief_cadence_survival,
    scalar_clairvoyant_recursive_cadence_survival,
)
from touhou_control.viability import ControlAction, ViabilityConfig


def _percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    index = int(round((len(ordered) - 1) * fraction))
    return ordered[index]


def _result_json(result: QueryLocalSurvivalResult) -> dict[str, object]:
    return {
        "state_label": asdict(result.state_label),
        "action_labels": {
            action: asdict(label)
            for action, label in result.action_labels
        },
        "best_actions": list(result.best_actions),
        "winning": result.winning,
        "evaluated_state_count": result.evaluated_state_count,
        "backend": result.backend,
    }


def _timed(
    solve: Callable[..., QueryLocalSurvivalResult],
    arguments: dict[str, object],
) -> tuple[QueryLocalSurvivalResult, float]:
    started = time.perf_counter()
    result = solve(**arguments)
    return result, (time.perf_counter() - started) * 1000.0


def _audit_cohort(
    *,
    name: str,
    seed_start: int,
    case_count: int,
    horizon: int,
    actions: tuple[ControlAction, ...],
    delay_frames: tuple[int, ...],
    cadence_frames: tuple[int, ...],
    continuation_frames: int,
    start_column: int,
    column_count: int = 3,
    hazard_probability: float = 0.2,
) -> dict[str, object]:
    x_axis = np.arange(column_count, dtype=np.float32)
    y_axis = np.arange(2, dtype=np.float32)
    config = ViabilityConfig(
        frames_per_layer=continuation_frames,
        required_clearance=0.0,
        clamp_to_bounds=True,
    )
    timing: dict[str, list[float]] = {
        "legacy_always_issue_hybrid": [],
        "belief_one_transition": [],
        "clairvoyant_recursive": [],
        "belief_recursive": [],
    }
    states: dict[str, list[int]] = {
        "legacy_always_issue_hybrid": [],
        "belief_one_transition": [],
        "clairvoyant_recursive": [],
        "belief_recursive": [],
    }
    counts = {
        "legacy_vs_no_write_action_label_mismatch": 0,
        "legacy_vs_no_write_best_action_mismatch": 0,
        "legacy_vs_no_write_winning_mismatch": 0,
        "legacy_optimistic_state_value": 0,
        "legacy_conservative_state_value": 0,
        "one_transition_vs_recursive_action_label_mismatch": 0,
        "one_transition_vs_recursive_best_action_mismatch": 0,
        "one_transition_vs_recursive_winning_mismatch": 0,
        "one_transition_optimistic_state_value": 0,
        "one_transition_conservative_state_value": 0,
        "hybrid_vs_belief_action_label_mismatch": 0,
        "hybrid_vs_belief_best_action_mismatch": 0,
        "hybrid_vs_belief_winning_mismatch": 0,
        "hybrid_optimistic_state_value": 0,
        "hybrid_conservative_state_value": 0,
        "clairvoyant_vs_belief_action_label_mismatch": 0,
        "clairvoyant_vs_belief_best_action_mismatch": 0,
        "clairvoyant_vs_belief_winning_mismatch": 0,
        "clairvoyant_optimistic_state_value": 0,
        "clairvoyant_conservative_state_value": 0,
    }
    first_mismatch_seeds: dict[str, list[int]] = {
        "legacy_vs_no_write": [],
        "one_transition_vs_recursive": [],
        "hybrid_vs_belief": [],
        "clairvoyant_vs_belief": [],
    }
    for seed in range(seed_start, seed_start + case_count):
        random = np.random.default_rng(seed)
        clearance = np.where(
            random.random((horizon + 1, 2, column_count))
            < hazard_probability,
            -1.0,
            1.0,
        ).astype(np.float32)
        clearance[0, :, start_column] = 1.0
        arguments = {
            "x_axis": x_axis,
            "y_axis": y_axis,
            "clearance_volume": clearance,
            "actions": actions,
            "delay_frames": delay_frames,
            "decision_frame_support": cadence_frames,
            "config": config,
            "start_frame": 0,
            "row": 0,
            "column": start_column,
            "observed_action": "stay",
        }
        hybrid, hybrid_ms = _timed(
            scalar_query_local_survival,
            arguments,
        )
        one_transition_arguments = dict(arguments)
        one_transition_arguments["recursive_cadence"] = False
        belief_one, belief_one_ms = _timed(
            scalar_belief_cadence_survival,
            one_transition_arguments,
        )
        clairvoyant, clairvoyant_ms = _timed(
            scalar_clairvoyant_recursive_cadence_survival,
            arguments,
        )
        belief, belief_ms = _timed(
            scalar_belief_cadence_survival,
            arguments,
        )
        results = {
            "legacy_always_issue_hybrid": (hybrid, hybrid_ms),
            "belief_one_transition": (
                belief_one,
                belief_one_ms,
            ),
            "clairvoyant_recursive": (clairvoyant, clairvoyant_ms),
            "belief_recursive": (belief, belief_ms),
        }
        for result_name, (result, elapsed_ms) in results.items():
            timing[result_name].append(elapsed_ms)
            states[result_name].append(result.evaluated_state_count)

        if hybrid.action_labels != belief_one.action_labels:
            counts["legacy_vs_no_write_action_label_mismatch"] += 1
        if hybrid.best_actions != belief_one.best_actions:
            counts["legacy_vs_no_write_best_action_mismatch"] += 1
        if hybrid.winning != belief_one.winning:
            counts["legacy_vs_no_write_winning_mismatch"] += 1
        if hybrid.state_label > belief_one.state_label:
            counts["legacy_optimistic_state_value"] += 1
        if hybrid.state_label < belief_one.state_label:
            counts["legacy_conservative_state_value"] += 1
        if (
            hybrid.action_labels != belief_one.action_labels
            and len(first_mismatch_seeds["legacy_vs_no_write"]) < 8
        ):
            first_mismatch_seeds["legacy_vs_no_write"].append(seed)

        if belief_one.action_labels != belief.action_labels:
            counts[
                "one_transition_vs_recursive_action_label_mismatch"
            ] += 1
        if belief_one.best_actions != belief.best_actions:
            counts[
                "one_transition_vs_recursive_best_action_mismatch"
            ] += 1
        if belief_one.winning != belief.winning:
            counts[
                "one_transition_vs_recursive_winning_mismatch"
            ] += 1
        if belief_one.state_label > belief.state_label:
            counts["one_transition_optimistic_state_value"] += 1
        if belief_one.state_label < belief.state_label:
            counts["one_transition_conservative_state_value"] += 1
        if (
            belief_one.action_labels != belief.action_labels
            and len(
                first_mismatch_seeds["one_transition_vs_recursive"]
            ) < 8
        ):
            first_mismatch_seeds[
                "one_transition_vs_recursive"
            ].append(seed)

        if hybrid.action_labels != belief.action_labels:
            counts["hybrid_vs_belief_action_label_mismatch"] += 1
        if hybrid.best_actions != belief.best_actions:
            counts["hybrid_vs_belief_best_action_mismatch"] += 1
        if hybrid.winning != belief.winning:
            counts["hybrid_vs_belief_winning_mismatch"] += 1
        if hybrid.state_label > belief.state_label:
            counts["hybrid_optimistic_state_value"] += 1
        if hybrid.state_label < belief.state_label:
            counts["hybrid_conservative_state_value"] += 1
        if (
            hybrid.action_labels != belief.action_labels
            and len(first_mismatch_seeds["hybrid_vs_belief"]) < 8
        ):
            first_mismatch_seeds["hybrid_vs_belief"].append(seed)

        if clairvoyant.action_labels != belief.action_labels:
            counts[
                "clairvoyant_vs_belief_action_label_mismatch"
            ] += 1
        if clairvoyant.best_actions != belief.best_actions:
            counts[
                "clairvoyant_vs_belief_best_action_mismatch"
            ] += 1
        if clairvoyant.winning != belief.winning:
            counts["clairvoyant_vs_belief_winning_mismatch"] += 1
        if clairvoyant.state_label > belief.state_label:
            counts["clairvoyant_optimistic_state_value"] += 1
        if clairvoyant.state_label < belief.state_label:
            counts["clairvoyant_conservative_state_value"] += 1
        if (
            clairvoyant.action_labels != belief.action_labels
            and len(
                first_mismatch_seeds["clairvoyant_vs_belief"]
            ) < 8
        ):
            first_mismatch_seeds[
                "clairvoyant_vs_belief"
            ].append(seed)

    return {
        "name": name,
        "case_count": case_count,
        "seed_start": seed_start,
        "problem": {
            "horizon": horizon,
            "shape": [horizon + 1, 2, column_count],
            "actions": [action.name for action in actions],
            "delay_frames": list(delay_frames),
            "cadence_frames": list(cadence_frames),
            "hybrid_continuation_frames": continuation_frames,
            "hazard_probability": hazard_probability,
            "start_column": start_column,
        },
        "counts": counts,
        "first_mismatch_seeds": first_mismatch_seeds,
        "timing_ms": {
            result_name: {
                "median": statistics.median(values),
                "p95": _percentile(values, 0.95),
                "max": max(values),
            }
            for result_name, values in timing.items()
        },
        "evaluated_states": {
            result_name: {
                "median": statistics.median(values),
                "p95": _percentile(
                    [float(value) for value in values],
                    0.95,
                ),
                "max": max(values),
            }
            for result_name, values in states.items()
        },
    }


def _minimal_counterexamples() -> dict[str, object]:
    x_axis = np.arange(3, dtype=np.float32)
    y_axis = np.arange(2, dtype=np.float32)

    no_write_clearance = np.ones((4, 2, 3), dtype=np.float32)
    no_write_clearance[3, :, 1] = -1.0
    no_write_arguments = {
        "x_axis": x_axis,
        "y_axis": y_axis,
        "clearance_volume": no_write_clearance,
        "actions": (
            ControlAction("left", -1.0, 0.0),
            ControlAction("stay", 0.0, 0.0),
        ),
        "delay_frames": (3,),
        "decision_frame_support": (1,),
        "config": ViabilityConfig(
            frames_per_layer=1,
            required_clearance=0.0,
            clamp_to_bounds=True,
        ),
        "start_frame": 0,
        "row": 0,
        "column": 1,
        "observed_action": "stay",
        "pending_command": PendingCommand("left", (2,)),
    }
    legacy_always_issue = scalar_query_local_survival(
        **no_write_arguments
    )
    no_write_belief = scalar_belief_cadence_survival(
        **no_write_arguments
    )

    cadence_x_axis = np.arange(5, dtype=np.float32)
    cadence_clearance = np.ones((11, 2, 5), dtype=np.float32)
    for frame, column in ((5, 0), (7, 1), (9, 2), (10, 4)):
        cadence_clearance[frame, :, column] = -1.0
    cadence_arguments = {
        "x_axis": cadence_x_axis,
        "y_axis": y_axis,
        "clearance_volume": cadence_clearance,
        "actions": (
            ControlAction("left", -1.0, 0.0),
            ControlAction("stay", 0.0, 0.0),
            ControlAction("right", 1.0, 0.0),
        ),
        "delay_frames": (2, 3),
        "decision_frame_support": (1, 2),
        "config": ViabilityConfig(
            frames_per_layer=2,
            required_clearance=0.0,
            clamp_to_bounds=True,
        ),
        "start_frame": 0,
        "row": 0,
        "column": 2,
        "observed_action": "stay",
    }
    cadence_one_transition = scalar_belief_cadence_survival(
        **cadence_arguments,
        recursive_cadence=False,
    )
    cadence_recursive = scalar_belief_cadence_survival(
        **cadence_arguments
    )

    information_clearance = np.ones((5, 2, 3), dtype=np.float32)
    information_clearance[4, :, 1] = -1.0
    information_arguments = {
        "x_axis": x_axis,
        "y_axis": y_axis,
        "clearance_volume": information_clearance,
        "actions": (
            ControlAction("stay", 0.0, 0.0),
            ControlAction("right", 1.0, 0.0),
        ),
        "delay_frames": (2, 3),
        "decision_frame_support": (1,),
        "config": ViabilityConfig(
            frames_per_layer=1,
            required_clearance=0.0,
            clamp_to_bounds=True,
        ),
        "start_frame": 0,
        "row": 0,
        "column": 0,
        "observed_action": "stay",
    }
    information_clairvoyant = (
        scalar_clairvoyant_recursive_cadence_survival(
            **information_arguments
        )
    )
    information_belief = scalar_belief_cadence_survival(
        **information_arguments
    )
    return {
        "selecting_same_desired_is_hold_not_reissue": {
            "problem": {
                "x_axis": x_axis.tolist(),
                "clearance_x_by_frame": (
                    no_write_clearance[:, 0, :].tolist()
                ),
                "actions": ["left:-1", "stay:0"],
                "delay_frames": [3],
                "cadence_frames": [1],
                "fixed_continuation_frames": 1,
                "start": [0, 1, "stay", "pending:left:remaining=2"],
            },
            "legacy_always_issue": _result_json(legacy_always_issue),
            "belief_no_write": _result_json(no_write_belief),
        },
        "one_transition_cadence_can_be_optimistic": {
            "problem": {
                "x_axis": cadence_x_axis.tolist(),
                "clearance_x_by_frame": (
                    cadence_clearance[:, 0, :].tolist()
                ),
                "unsafe_cells": [
                    [5, 0],
                    [7, 1],
                    [9, 2],
                    [10, 4],
                ],
                "actions": ["left:-1", "stay:0", "right:+1"],
                "delay_frames": [2, 3],
                "cadence_frames": [1, 2],
                "fixed_continuation_frames": 2,
                "start": [0, 2, "stay"],
            },
            "belief_one_transition": _result_json(
                cadence_one_transition
            ),
            "belief_recursive": _result_json(cadence_recursive),
        },
        "exact_hidden_remaining_is_clairvoyant": {
            "problem": {
                "x_axis": x_axis.tolist(),
                "clearance_x_by_frame": (
                    information_clearance[:, 0, :].tolist()
                ),
                "actions": ["stay:0", "right:+1"],
                "delay_frames": [2, 3],
                "cadence_frames": [1],
                "start": [0, 0, "stay"],
            },
            "clairvoyant_recursive": _result_json(
                information_clairvoyant
            ),
            "belief_recursive": _result_json(information_belief),
        },
    }


def audit(case_count: int) -> dict[str, object]:
    return {
        "schema": "th08.pipeline_formal_correctness_audit.v2",
        "claim_boundary": {
            "legacy_always_issue_hybrid": (
                "every selected action is modeled as a new write; "
                "variable cadence at the public root, then fixed cadence; "
                "future exact remaining delay is revealed"
            ),
            "belief_one_transition": (
                "same desired action is hold/no-write; variable cadence "
                "at the public root, then fixed cadence; remaining-delay "
                "information sets are preserved"
            ),
            "clairvoyant_recursive": (
                "variable cadence recursively, but future exact remaining "
                "delay is revealed"
            ),
            "belief_recursive": (
                "variable cadence recursively; indistinguishable remaining "
                "delays are merged before future maximization"
            ),
        },
        "minimal_counterexamples": _minimal_counterexamples(),
        "cohorts": [
            _audit_cohort(
                name="hold_vs_always_issue_fixed_cadence",
                seed_start=20_000,
                case_count=case_count,
                horizon=6,
                actions=(
                    ControlAction("left", -1.0, 0.0),
                    ControlAction("stay", 0.0, 0.0),
                    ControlAction("right", 1.0, 0.0),
                ),
                delay_frames=(3,),
                cadence_frames=(1,),
                continuation_frames=1,
                start_column=1,
            ),
            _audit_cohort(
                name="recursive_cadence_and_information",
                seed_start=0,
                case_count=case_count,
                horizon=6,
                actions=(
                    ControlAction("left", -1.0, 0.0),
                    ControlAction("stay", 0.0, 0.0),
                    ControlAction("right", 1.0, 0.0),
                ),
                delay_frames=(0, 1, 2, 3),
                cadence_frames=(1, 2),
                continuation_frames=2,
                start_column=1,
            ),
            _audit_cohort(
                name="variable_cadence_wider_longer_adversarial",
                seed_start=90_300,
                case_count=case_count,
                horizon=10,
                actions=(
                    ControlAction("left", -1.0, 0.0),
                    ControlAction("stay", 0.0, 0.0),
                    ControlAction("right", 1.0, 0.0),
                ),
                delay_frames=(2, 3),
                cadence_frames=(1, 2),
                continuation_frames=2,
                start_column=2,
                column_count=5,
                hazard_probability=0.27,
            ),
            _audit_cohort(
                name="fixed_cadence_hidden_remaining_information",
                seed_start=10_000,
                case_count=case_count,
                horizon=5,
                actions=(
                    ControlAction("stay", 0.0, 0.0),
                    ControlAction("right", 1.0, 0.0),
                ),
                delay_frames=(2, 3),
                cadence_frames=(1,),
                continuation_frames=1,
                start_column=0,
            ),
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--cases", type=int, default=128)
    arguments = parser.parse_args()
    if arguments.cases <= 0:
        raise SystemExit("--cases must be positive")
    report = audit(arguments.cases)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report["cohorts"], indent=2))


if __name__ == "__main__":
    main()
