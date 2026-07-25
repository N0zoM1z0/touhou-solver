#!/usr/bin/env python3
"""Replay retained global-losing decisions with survival labels in shadow."""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

from benchmarks.benchmark_recovery_control_reserve import (
    _replay_decision,
)


BASE_VARIANT = "space16_time8_h80"


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[int(0.95 * (len(ordered) - 1))]


def _action_name(value: object) -> str:
    return str(value).split("+", 1)[0]


def _hard_vector(decision: object) -> tuple[object, ...]:
    return (
        decision.robust_collisions,
        max(-decision.robust_min_clearance, 0.0),
        max(-decision.min_clearance, 0.0),
        decision.terminal_threat_collisions,
        max(-decision.terminal_threat_min_clearance, 0.0),
    )


def _read_rows(
    trace: Path,
    frames: set[int],
) -> dict[int, dict[str, object]]:
    rows = {}
    with trace.open(encoding="utf-8") as source:
        for line in source:
            row = json.loads(line)
            if (
                row.get("kind") == "decision"
                and int(row["frame"]) in frames
            ):
                rows[int(row["frame"])] = row
    return rows


def benchmark(
    *,
    trace: Path,
    audit_path: Path,
) -> dict[str, object]:
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    observations = [
        observation
        for observation in audit["observations"]
        if not observation["trace_state_viable"]
    ]
    frames = {
        int(observation["decision_frame"])
        for observation in observations
    }
    rows = _read_rows(trace, frames)
    missing = sorted(frames - rows.keys())
    if missing:
        raise ValueError(f"trace is missing audited frames: {missing}")
    first_hit = min(
        int(observation["hit_frame"])
        for observation in observations
    )
    first_hit_by_spell: dict[int, int] = {}
    for observation in observations:
        first_hit_by_spell.setdefault(
            int(observation["spell_id"]),
            int(observation["hit_frame"]),
        )

    durations = {
        "baseline": [],
        "reserve_shadow": [],
        "survival_shadow": [],
        "combined_shadow": [],
    }
    cases = []
    for index, observation in enumerate(observations):
        row = rows[int(observation["decision_frame"])]
        base = observation["variants"][BASE_VARIANT]
        labels = {
            "viability_survival_actions": tuple(base["best_actions"]),
            "viability_survival_frames": int(base["survival_frames"]),
            "viability_survival_bottleneck_margin": float(
                base["bottleneck_margin"]
            ),
        }

        def replay(
            name: str,
            *,
            survival: bool,
            reserve: bool,
        ):
            started = time.perf_counter()
            decision = _replay_decision(
                row,
                recovery_control_reserve=True,
                losing_control_reserve=reserve,
                **(labels if survival else {}),
            )
            durations[name].append(
                (time.perf_counter() - started) * 1000.0
            )
            return decision

        if index % 2:
            combined = replay(
                "combined_shadow",
                survival=True,
                reserve=True,
            )
            shadow = replay(
                "survival_shadow",
                survival=True,
                reserve=False,
            )
            reserve = replay(
                "reserve_shadow",
                survival=False,
                reserve=True,
            )
            baseline = replay(
                "baseline",
                survival=False,
                reserve=False,
            )
        else:
            baseline = replay(
                "baseline",
                survival=False,
                reserve=False,
            )
            reserve = replay(
                "reserve_shadow",
                survival=False,
                reserve=True,
            )
            shadow = replay(
                "survival_shadow",
                survival=True,
                reserve=False,
            )
            combined = replay(
                "combined_shadow",
                survival=True,
                reserve=True,
            )
        best_actions = set(base["best_actions"])
        cases.append(
            {
                "hit_frame": int(observation["hit_frame"]),
                "decision_frame": int(observation["decision_frame"]),
                "query_frame": int(observation["query_frame"]),
                "time_to_hit": int(observation["time_to_hit"]),
                "spell_id": int(observation["spell_id"]),
                "role": (
                    "canonical_first_hit"
                    if int(observation["hit_frame"]) == first_hit
                    else (
                        "first_discovery_for_phase"
                        if int(observation["hit_frame"])
                        == first_hit_by_spell[int(observation["spell_id"])]
                        else "post_hit_discovery"
                    )
                ),
                "survival_frames": int(base["survival_frames"]),
                "survival_bottleneck_margin": float(
                    base["bottleneck_margin"]
                ),
                "survival_best_actions": sorted(best_actions),
                "recorded_action": _action_name(row["action"]),
                "baseline_action": baseline.action,
                "reserve_shadow_action": reserve.action,
                "shadow_action": shadow.action,
                "combined_shadow_action": combined.action,
                "baseline_matches_recorded": (
                    baseline.action == _action_name(row["action"])
                ),
                "action_changed": baseline.action != shadow.action,
                "reserve_action_changed": (
                    baseline.action != reserve.action
                ),
                "combined_action_changed": (
                    baseline.action != combined.action
                ),
                "baseline_in_best_mask": (
                    baseline.action in best_actions
                ),
                "shadow_in_best_mask": shadow.action in best_actions,
                "combined_in_best_mask": (
                    combined.action in best_actions
                ),
                "shadow_label_preferred": (
                    shadow.viability_survival_preferred
                ),
                "baseline_hard_vector": _hard_vector(baseline),
                "reserve_shadow_hard_vector": _hard_vector(reserve),
                "shadow_hard_vector": _hard_vector(shadow),
                "combined_shadow_hard_vector": _hard_vector(combined),
                "hard_vector_change": (
                    "improved"
                    if _hard_vector(shadow) < _hard_vector(baseline)
                    else (
                        "regressed"
                        if _hard_vector(shadow) > _hard_vector(baseline)
                        else "equal"
                    )
                ),
                "baseline_control_reserve_deficit": (
                    baseline.viability_control_reserve_deficit
                ),
                "reserve_shadow_control_reserve_deficit": (
                    reserve.viability_control_reserve_deficit
                ),
                "shadow_control_reserve_deficit": (
                    shadow.viability_control_reserve_deficit
                ),
                "combined_shadow_control_reserve_deficit": (
                    combined.viability_control_reserve_deficit
                ),
            }
        )

    changes = [case for case in cases if case["action_changed"]]
    canonical = [
        case for case in cases if case["role"] == "canonical_first_hit"
    ]
    covering = [
        case
        for case in cases
        if case["survival_frames"] >= case["time_to_hit"]
    ]

    def variant_summary(
        action_field: str,
        hard_field: str,
        reserve_field: str,
    ) -> dict[str, object]:
        changes = [
            case
            for case in cases
            if case[action_field] != case["baseline_action"]
        ]
        hard_changes = []
        for case in cases:
            candidate = tuple(case[hard_field])
            baseline = tuple(case["baseline_hard_vector"])
            hard_changes.append(
                "improved"
                if candidate < baseline
                else ("regressed" if candidate > baseline else "equal")
            )
        return {
            "action_change_count": len(changes),
            "hard_vector_change_counts": {
                name: hard_changes.count(name)
                for name in ("improved", "equal", "regressed")
            },
            "reserve_deficit_improved_count": sum(
                float(case[reserve_field])
                < float(case["baseline_control_reserve_deficit"])
                for case in cases
            ),
            "reserve_deficit_regressed_count": sum(
                float(case[reserve_field])
                > float(case["baseline_control_reserve_deficit"])
                for case in cases
            ),
        }

    return {
        "schema": "th08-losing-state-survival-shadow-replay-v2",
        "trace": str(trace),
        "audit": str(audit_path),
        "scope": (
            "Offline replay of exact retained local inputs. Survival labels "
            "rank only after fresh local collision terms and never control "
            "physical input in this experiment."
        ),
        "case_count": len(cases),
        "baseline_replay_match_count": sum(
            case["baseline_matches_recorded"] for case in cases
        ),
        "action_change_count": len(changes),
        "baseline_in_best_mask_count": sum(
            case["baseline_in_best_mask"] for case in cases
        ),
        "shadow_in_best_mask_count": sum(
            case["shadow_in_best_mask"] for case in cases
        ),
        "shadow_label_preferred_count": sum(
            case["shadow_label_preferred"] for case in cases
        ),
        "hard_vector_change_counts": {
            name: sum(
                case["hard_vector_change"] == name for case in cases
            )
            for name in ("improved", "equal", "regressed")
        },
        "variant_summary": {
            "reserve_shadow": variant_summary(
                "reserve_shadow_action",
                "reserve_shadow_hard_vector",
                "reserve_shadow_control_reserve_deficit",
            ),
            "survival_shadow": variant_summary(
                "shadow_action",
                "shadow_hard_vector",
                "shadow_control_reserve_deficit",
            ),
            "combined_shadow": variant_summary(
                "combined_shadow_action",
                "combined_shadow_hard_vector",
                "combined_shadow_control_reserve_deficit",
            ),
        },
        "covering_query_count": len(covering),
        "covering_query_action_change_count": sum(
            case["action_changed"] for case in covering
        ),
        "timing_ms": {
            name: {
                "median": statistics.median(values),
                "p95": _p95(values),
                "max": max(values),
            }
            for name, values in durations.items()
        },
        "canonical_first_hit_cases": canonical,
        "action_changes": changes,
        "cases": cases,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("audit", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args(argv)
    report = benchmark(trace=args.trace, audit_path=args.audit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
