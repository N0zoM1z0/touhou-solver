#!/usr/bin/env python3
"""Offline replay of CE-0100 coarse false-empties through refinement."""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from pathlib import Path

from th08_corridor_adapter import (
    LoweredCorridorHazards,
    plan_lowered_th08_corridor,
)
from touhou_control.viability_audit_capsule import (
    read_viability_audit_capsule,
)


@dataclass(frozen=True)
class Witness:
    capsule: str
    query_frame: int
    player_x: float
    player_y: float
    active_action: str


WITNESSES = (
    Witness(
        "policy_23832_23848.npz",
        23862,
        127.736572265625,
        421.863525390625,
        "down_fast",
    ),
    Witness(
        "policy_25516_25532.npz",
        25554,
        351.6048583984375,
        371.6048583984375,
        "up_fast",
    ),
    Witness(
        "policy_25539_25555.npz",
        25562,
        351.6048583984375,
        339.6048583984375,
        "up_fast",
    ),
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capsule_dir", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    results = []
    for witness in WITNESSES:
        path = args.capsule_dir / witness.capsule
        capsule = read_viability_audit_capsule(path)
        metadata = capsule.metadata

        def solve(
            *,
            survival_labels: bool,
            refinement_grid_steps: tuple[float, ...],
        ) -> dict[str, object]:
            started = time.perf_counter()
            plan = plan_lowered_th08_corridor(
                player_x=float(metadata["player_x"]),
                player_y=float(metadata["player_y"]),
                hazards=LoweredCorridorHazards(
                    capsule.aabbs,
                    capsule.piecewise_aabbs,
                    capsule.segment_trajectories,
                    capsule.packed_segments,
                ),
                control_delay_candidates=tuple(
                    int(value)
                    for value in metadata["control_delay_candidates"]
                ),
                nominal_control_delay=int(
                    metadata["nominal_control_delay"]
                ),
                active_action=str(metadata["active_action"]),
                survival_labels=survival_labels,
                refinement_grid_steps=refinement_grid_steps,
            )
            assert plan.viability_policy is not None
            query = plan.viability_policy.query(
                frame=(
                    witness.query_frame
                    - int(metadata["source_frame"])
                ),
                x=witness.player_x,
                y=witness.player_y,
                active_action=witness.active_action,
            )
            return {
                "selected_grid_step": plan.viability_grid_step,
                "source_reachable": plan.reachable,
                "query_viable": query.state_viable,
                "safe_actions": query.safe_actions,
                "viability_backend": plan.viability_backend,
                "survival_backend": (
                    plan.survival_policy.backend
                    if plan.survival_policy is not None
                    else None
                ),
                "wall_ms": (
                    time.perf_counter() - started
                ) * 1000.0,
                "timing_ms": dict(plan.solver_timing_ms),
            }

        live = solve(
            survival_labels=False,
            refinement_grid_steps=(),
        )
        shadow = solve(
            survival_labels=True,
            refinement_grid_steps=(8.0,),
        )
        results.append(
            {
                "capsule": witness.capsule,
                "source_frame": int(metadata["source_frame"]),
                "query_frame": witness.query_frame,
                "live_boolean": live,
                "shadow_refined_survival": shadow,
            }
        )
    report = {
        "schema": "ce-0100-adaptive-replay-v3",
        "method": (
            "compare restored live 16px Boolean policy with shadow coarse "
            "fused survival plus full-horizon 8px Boolean refinement"
        ),
        "model_scope": (
            "retained lowered-hazard counterfactual; not physical survival"
        ),
        "passing_witnesses": sum(
            bool(result["shadow_refined_survival"]["query_viable"])
            for result in results
        ),
        "witness_count": len(results),
        "results": results,
    }
    payload = json.dumps(report, indent=2) + "\n"
    if args.output is None:
        print(payload, end="")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    return 0 if report["passing_witnesses"] == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
