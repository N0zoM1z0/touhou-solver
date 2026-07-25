#!/usr/bin/env python3
"""Measure whole-policy Boolean versus fused-survival delivery cost."""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

import numpy as np

from th08_corridor_adapter import (
    LoweredCorridorHazards,
    plan_lowered_th08_corridor,
)
from touhou_control.viability_audit_capsule import (
    read_viability_audit_capsule,
)


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[int(0.95 * (len(ordered) - 1))]


def _sample(paths: list[Path], count: int) -> list[Path]:
    if len(paths) <= count:
        return paths
    indices = np.rint(
        np.linspace(0, len(paths) - 1, count)
    ).astype(np.int64)
    return [paths[int(index)] for index in indices]


def benchmark(
    *,
    capsule_dir: Path,
    sample_count: int,
) -> dict[str, object]:
    paths = _sample(sorted(capsule_dir.glob("*.npz")), sample_count)
    if not paths:
        raise ValueError("capsule directory is empty")
    durations = {"boolean": [], "fused_survival": []}
    timings = {
        "boolean": {"clearance": [], "viability": []},
        "fused_survival": {"clearance": [], "viability": []},
    }
    parity_failures = []
    cases = []
    for index, path in enumerate(paths):
        capsule = read_viability_audit_capsule(path)
        metadata = capsule.metadata
        hazards = LoweredCorridorHazards(
            capsule.aabbs,
            capsule.piecewise_aabbs,
            capsule.segment_trajectories,
            capsule.packed_segments,
        )
        arguments = {
            "player_x": float(metadata["player_x"]),
            "player_y": float(metadata["player_y"]),
            "hazards": hazards,
            "control_delay_candidates": tuple(
                int(value)
                for value in metadata["control_delay_candidates"]
            ),
            "nominal_control_delay": int(
                metadata["nominal_control_delay"]
            ),
            "active_action": str(metadata["active_action"]),
        }

        def solve(name: str, *, labels: bool):
            started = time.perf_counter()
            plan = plan_lowered_th08_corridor(
                **arguments,
                survival_labels=labels,
            )
            durations[name].append(
                (time.perf_counter() - started) * 1000.0
            )
            stages = dict(plan.solver_timing_ms)
            timings[name]["clearance"].append(stages["clearance"])
            timings[name]["viability"].append(stages["viability"])
            return plan

        if index % 2:
            fused = solve("fused_survival", labels=True)
            boolean = solve("boolean", labels=False)
        else:
            boolean = solve("boolean", labels=False)
            fused = solve("fused_survival", labels=True)
        assert boolean.viability_policy is not None
        assert fused.viability_policy is not None
        viable_equal = np.array_equal(
            boolean.viability_policy.viable,
            fused.viability_policy.viable,
        )
        masks_equal = np.array_equal(
            boolean.viability_policy.safe_action_masks,
            fused.viability_policy.safe_action_masks,
        )
        if not viable_equal or not masks_equal:
            parity_failures.append(path.name)
        cases.append(
            {
                "capsule": path.name,
                "boolean_reachable": boolean.reachable,
                "fused_reachable": fused.reachable,
                "viable_equal": viable_equal,
                "safe_action_masks_equal": masks_equal,
                "boolean_ms": durations["boolean"][-1],
                "fused_survival_ms": durations["fused_survival"][-1],
            }
        )

    def summary(values: list[float]) -> dict[str, float]:
        return {
            "median": statistics.median(values),
            "p95": _p95(values),
            "max": max(values),
        }

    return {
        "schema": "survival-label-delivery-benchmark-v1",
        "capsule_dir": str(capsule_dir),
        "sample_count": len(paths),
        "scope": (
            "Whole offline TH08 policy solve including retained hazard "
            "lowering output, clearance construction, and viability "
            "induction. Capsule decode is outside the timed boundary."
        ),
        "parity_failure_count": len(parity_failures),
        "parity_failures": parity_failures,
        "wall_ms": {
            name: summary(values) for name, values in durations.items()
        },
        "stage_ms": {
            name: {
                stage: summary(values)
                for stage, values in stage_values.items()
            }
            for name, stage_values in timings.items()
        },
        "cases": cases,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capsule_dir", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--samples", type=int, default=40)
    args = parser.parse_args(argv)
    if args.samples <= 0:
        parser.error("sample count must be positive")
    report = benchmark(
        capsule_dir=args.capsule_dir,
        sample_count=args.samples,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    print(args.output)
    return 0 if report["parity_failure_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
