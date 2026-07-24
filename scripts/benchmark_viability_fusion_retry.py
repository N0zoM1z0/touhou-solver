#!/usr/bin/env python3
"""Ablate exact local retry when a cached viability mask is contradicted."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import time
from pathlib import Path

from benchmark_recovery_control_reserve import _replay_decision


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[int(0.95 * (len(ordered) - 1))]


def _eligible(row: dict[str, object]) -> bool:
    corridor = row.get("corridor")
    if not isinstance(corridor, dict):
        return False
    viability = corridor.get("viability")
    terminal = row.get("terminal_threat")
    robust = row.get("robust_control")
    return (
        isinstance(viability, dict)
        and bool(viability.get("safe_actions"))
        and isinstance(terminal, dict)
        and int(terminal.get("horizon_frames", 0)) > 10
        and isinstance(robust, dict)
        and (
            int(terminal.get("collisions", 0)) > 0
            or int(robust.get("worst_collisions", 0)) > 0
            or float(row.get("minimum_clearance", math.inf)) <= 0.0
        )
    )


def _sample_rows(
    rows: list[dict[str, object]],
    sample_count: int,
) -> list[dict[str, object]]:
    if len(rows) <= sample_count:
        return rows
    return [
        rows[math.floor(index * len(rows) / sample_count)]
        for index in range(sample_count)
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--samples", type=int, default=200)
    args = parser.parse_args(argv)
    if args.samples <= 0:
        raise ValueError("sample count must be positive")

    digest = hashlib.sha256()
    decisions: list[dict[str, object]] = []
    with args.trace.open("rb") as source:
        for raw_line in source:
            digest.update(raw_line)
            row = json.loads(raw_line)
            if row.get("kind") == "decision" and _eligible(row):
                decisions.append(row)
    decisions = _sample_rows(decisions, args.samples)
    if not decisions:
        raise RuntimeError(
            "trace contains no viability/terminal contradictions"
        )

    variants = {False: [], True: []}
    durations = {False: [], True: []}
    for index, row in enumerate(decisions):
        order = (False, True) if index % 2 == 0 else (True, False)
        for enabled in order:
            started = time.perf_counter()
            variants[enabled].append(
                _replay_decision(
                    row,
                    recovery_control_reserve=True,
                    relax_stale_viability_contradiction=enabled,
                )
            )
            durations[enabled].append(
                (time.perf_counter() - started) * 1000.0
            )

    def summarize(enabled: bool) -> dict[str, object]:
        selected = variants[enabled]
        return {
            "median_ms": statistics.median(durations[enabled]),
            "p95_ms": _p95(durations[enabled]),
            "constraint_relaxed_count": sum(
                decision.viability_constraint_relaxed
                for decision in selected
            ),
            "robust_collision_count": sum(
                decision.robust_collisions for decision in selected
            ),
            "terminal_collision_count": sum(
                decision.terminal_threat_collisions
                for decision in selected
            ),
            "negative_min_clearance_count": sum(
                decision.min_clearance <= 0.0 for decision in selected
            ),
        }

    changes = [
        {
            "frame": int(row["frame"]),
            "disabled": disabled.action,
            "enabled": enabled.action,
            "disabled_robust_collisions": disabled.robust_collisions,
            "enabled_robust_collisions": enabled.robust_collisions,
            "disabled_terminal_collisions": (
                disabled.terminal_threat_collisions
            ),
            "enabled_terminal_collisions": (
                enabled.terminal_threat_collisions
            ),
        }
        for row, disabled, enabled in zip(
            decisions,
            variants[False],
            variants[True],
        )
        if disabled.action != enabled.action
    ]
    result = {
        "schema": "th08-viability-fusion-retry-benchmark-v1",
        "trace": str(args.trace),
        "trace_sha256": digest.hexdigest(),
        "sample_count": len(decisions),
        "scope": (
            "Offline ablation over retained trace-radius hazards and exact "
            "laser lifecycle state; this is not physical survival evidence."
        ),
        "variants": {
            "disabled": summarize(False),
            "enabled": summarize(True),
        },
        "action_change_count": len(changes),
        "action_changes": changes,
    }
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result["variants"], indent=2))
    print(f"action changes: {len(changes)}/{len(decisions)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
