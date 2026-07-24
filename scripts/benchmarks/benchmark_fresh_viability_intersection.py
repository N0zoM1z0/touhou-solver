#!/usr/bin/env python3
"""Offline replay of cached-global/fresh-local contract contradictions."""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import time
from pathlib import Path

from benchmarks.benchmark_recovery_control_reserve import _replay_decision


def _eligible(row: dict[str, object]) -> bool:
    corridor = row.get("corridor")
    viability = (
        corridor.get("viability")
        if isinstance(corridor, dict)
        else None
    )
    robust = row.get("robust_control")
    if (
        not isinstance(viability, dict)
        or not bool(viability.get("available"))
        or not bool(viability.get("support_covers_current", True))
        or not bool(viability.get("state_viable"))
        or not isinstance(robust, dict)
    ):
        return False
    player = row.get("player")
    if isinstance(player, dict) and (
        int(player.get("phase", 0)) != 0
        or int(player.get("phase_at_action", 0)) != 0
    ):
        return False
    return (
        str(row.get("action", ""))
        in {str(action) for action in viability.get("safe_actions", ())}
        and (
            int(robust.get("worst_collisions", 0)) > 0
            or float(robust.get("min_clearance", 0.0)) < 0.0
        )
    )


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[int(0.95 * (len(ordered) - 1))]


def _hard_key(decision) -> tuple[object, ...]:
    return (
        decision.robust_collisions,
        max(-decision.robust_min_clearance, 0.0),
        decision.terminal_threat_collisions,
        max(-decision.terminal_threat_min_clearance, 0.0),
        max(-decision.min_clearance, 0.0),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args(argv)

    digest = hashlib.sha256()
    rows: list[dict[str, object]] = []
    with args.trace.open("rb") as source:
        for raw_line in source:
            digest.update(raw_line)
            row = json.loads(raw_line)
            if row.get("kind") == "decision" and _eligible(row):
                rows.append(row)
    if not rows:
        raise RuntimeError("trace has no direct action-contract contradictions")

    variants: dict[bool, list[object]] = {False: [], True: []}
    durations: dict[bool, list[float]] = {False: [], True: []}
    for index, row in enumerate(rows):
        order = (False, True) if index % 2 == 0 else (True, False)
        for enabled in order:
            started = time.perf_counter()
            decision = _replay_decision(
                row,
                recovery_control_reserve=True,
                enforce_fresh_viability_intersection=enabled,
            )
            durations[enabled].append(
                (time.perf_counter() - started) * 1000.0
            )
            variants[enabled].append(decision)

    def summary(enabled: bool) -> dict[str, object]:
        decisions = variants[enabled]
        return {
            "median_ms": statistics.median(durations[enabled]),
            "p95_ms": _p95(durations[enabled]),
            "robust_collision_sum": sum(
                decision.robust_collisions for decision in decisions
            ),
            "robust_collision_decision_count": sum(
                decision.robust_collisions > 0 for decision in decisions
            ),
            "negative_robust_clearance_count": sum(
                decision.robust_min_clearance < 0.0
                for decision in decisions
            ),
            "terminal_collision_sum": sum(
                decision.terminal_threat_collisions
                for decision in decisions
            ),
            "fresh_prefix_filtered_count": sum(
                decision.viability_fresh_prefix_filtered
                for decision in decisions
            ),
            "fresh_prefix_relaxed_count": sum(
                decision.viability_fresh_prefix_relaxed
                for decision in decisions
            ),
        }

    changes = []
    improved = 0
    regressed = 0
    for row, disabled, enabled in zip(
        rows,
        variants[False],
        variants[True],
    ):
        disabled_key = _hard_key(disabled)
        enabled_key = _hard_key(enabled)
        improved += enabled_key < disabled_key
        regressed += enabled_key > disabled_key
        if disabled.action != enabled.action:
            changes.append(
                {
                    "frame": int(row["frame"]),
                    "disabled_action": disabled.action,
                    "enabled_action": enabled.action,
                    "disabled_hard_key": disabled_key,
                    "enabled_hard_key": enabled_key,
                }
            )

    report = {
        "schema": "th08-fresh-viability-intersection-replay-v1",
        "trace": str(args.trace),
        "trace_sha256": digest.hexdigest(),
        "scope": (
            "Paired offline replay over retained trace-radius hazards for "
            "rows where the selected cached-global action contradicted the "
            "fresh local prefix certificate. This is not physical survival "
            "evidence."
        ),
        "eligible_count": len(rows),
        "variants": {
            "disabled": summary(False),
            "enabled": summary(True),
        },
        "paired_hard_improvement_count": improved,
        "paired_hard_regression_count": regressed,
        "action_change_count": len(changes),
        "action_changes": changes,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "eligible_count",
                    "variants",
                    "paired_hard_improvement_count",
                    "paired_hard_regression_count",
                    "action_change_count",
                )
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
