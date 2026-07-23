#!/usr/bin/env python3
"""Compare two retained TH08 practice dossiers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _reduction(before: float, after: float) -> float | None:
    if before == 0.0:
        return None
    return (before - after) / before


def compare_dossiers(
    baseline: dict[str, object],
    candidate: dict[str, object],
) -> dict[str, object]:
    for name, dossier in (("baseline", baseline), ("candidate", candidate)):
        if dossier.get("schema") != "th08-practice-dossier-v1":
            raise ValueError(f"{name} has an unsupported dossier schema")

    baseline_totals = baseline["totals"]
    candidate_totals = candidate["totals"]
    baseline_spell_50 = baseline_totals["latency_ms"]["corridor_solver"][
        "active_spell_50"
    ]
    candidate_spell_50 = candidate_totals["latency_ms"]["corridor_solver"][
        "active_spell_50"
    ]

    def active_spell_hits(dossier: dict[str, object], spell_id: int) -> int:
        return sum(
            death["spell_attribution"].get("spell_id") == spell_id
            for death in dossier["deaths"]
        )

    solve_changes = {}
    for key in ("median", "p95", "max"):
        before = float(baseline_spell_50["solve_ms"][key])
        after = float(candidate_spell_50["solve_ms"][key])
        solve_changes[key] = {
            "baseline": before,
            "candidate": after,
            "reduction_fraction": _reduction(before, after),
        }
    age_changes = {}
    for key in ("median", "p95", "max"):
        before = float(baseline_spell_50["age_frames"][key])
        after = float(candidate_spell_50["age_frames"][key])
        age_changes[key] = {
            "baseline": before,
            "candidate": after,
            "reduction_fraction": _reduction(before, after),
        }

    baseline_hits = int(baseline_totals["death_count"])
    candidate_hits = int(candidate_totals["death_count"])
    return {
        "schema": "th08-practice-comparison-v1",
        "baseline_run_id": baseline["run_id"],
        "candidate_run_id": candidate["run_id"],
        "no_bomb_passed": {
            "baseline": bool(
                baseline["control_policy"]["verification"]["passed"]
            ),
            "candidate": bool(
                candidate["control_policy"]["verification"]["passed"]
            ),
        },
        "death_count": {
            "baseline": baseline_hits,
            "candidate": candidate_hits,
            "reduction_fraction": _reduction(
                float(baseline_hits),
                float(candidate_hits),
            ),
        },
        "active_spell_hit_count": {
            "35": {
                "baseline": active_spell_hits(baseline, 35),
                "candidate": active_spell_hits(candidate, 35),
            },
            "50": {
                "baseline": active_spell_hits(baseline, 50),
                "candidate": active_spell_hits(candidate, 50),
            },
        },
        "spell_50_corridor": {
            "solve_ms": solve_changes,
            "age_frames": age_changes,
            "stale_solution_count": {
                "baseline": int(
                    baseline_spell_50["stale_solution_count"]
                ),
                "candidate": int(
                    candidate_spell_50["stale_solution_count"]
                ),
            },
        },
        "candidate_decision_cadence_frames": candidate_totals[
            "decision_cadence_frames"
        ],
        "candidate_behavior_context": candidate_totals["behavior_context"],
        "candidate_hit_contact_epoch": candidate_totals[
            "hit_contact_epoch"
        ],
        "candidate_primary_cause_counts": candidate_totals[
            "primary_cause_counts"
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args(argv)
    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
    comparison = compare_dossiers(baseline, candidate)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(comparison, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
