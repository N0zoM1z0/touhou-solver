#!/usr/bin/env python3
"""Ablate safety-value guidance on retained live decisions."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import time
from pathlib import Path

from benchmark_recovery_control_reserve import _replay_decision


def _percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    return ordered[round(fraction * (len(ordered) - 1))]


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


def _decision_metrics(decision) -> dict[str, object]:
    return {
        "action": decision.action,
        "robust_collisions": decision.robust_collisions,
        "robust_min_clearance": decision.robust_min_clearance,
        "terminal_threat_collisions": decision.terminal_threat_collisions,
        "terminal_threat_clearance": (
            decision.terminal_threat_min_clearance
        ),
        "minimum_clearance": decision.min_clearance,
        "immediate_clearance": decision.immediate_clearance,
        "recovery_distance": decision.viability_recovery_distance,
        "control_reserve_deficit": (
            decision.viability_control_reserve_deficit
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--samples", type=int, default=200)
    parser.add_argument(
        "--prehit-window",
        type=int,
        default=0,
        help="retain only decisions this many frames before a native hit",
    )
    parser.add_argument(
        "--spell",
        type=int,
        help="retain only decisions attributed to this spell id",
    )
    args = parser.parse_args(argv)
    if args.samples <= 0 or args.prehit_window < 0:
        raise ValueError("sample count must be positive and window nonnegative")

    digest = hashlib.sha256()
    decisions: list[dict[str, object]] = []
    hit_frames: list[int] = []
    with args.trace.open("rb") as source:
        for raw_line in source:
            digest.update(raw_line)
            row = json.loads(raw_line)
            if row.get("kind") != "decision":
                continue
            if row.get("hit_started"):
                hit_frames.append(int(row["frame"]))
            safety_value = row.get("corridor", {}).get("safety_value", {})
            viability = row.get("corridor", {}).get("viability", {})
            if (
                safety_value.get("guidance_active")
                and safety_value.get("best_actions")
                and viability.get("support_covers_current", True)
            ):
                decisions.append(row)
    if args.spell is not None:
        decisions = [
            row
            for row in decisions
            if row.get("spell", {}).get("spell_id") == args.spell
        ]
    if args.prehit_window:
        decisions = [
            row
            for row in decisions
            if any(
                0 <= hit_frame - int(row["frame"]) <= args.prehit_window
                for hit_frame in hit_frames
            )
        ]
    eligible_count = len(decisions)
    decisions = _sample_rows(decisions, args.samples)
    if not decisions:
        raise RuntimeError("trace contains no eligible safety-value decisions")

    variants: dict[bool, list[object]] = {False: [], True: []}
    durations: dict[bool, list[float]] = {False: [], True: []}
    for index, row in enumerate(decisions):
        safety_value = row["corridor"]["safety_value"]
        order = (False, True) if index % 2 == 0 else (True, False)
        for enabled in order:
            started = time.perf_counter()
            decision = _replay_decision(
                row,
                recovery_control_reserve=True,
                viability_safety_actions=(
                    tuple(safety_value["best_actions"]) if enabled else ()
                ),
                viability_safety_state_value=(
                    float(safety_value["state_value"])
                    if enabled
                    else None
                ),
            )
            durations[enabled].append(
                (time.perf_counter() - started) * 1000.0
            )
            variants[enabled].append(decision)

    changes = []
    for row, disabled, enabled in zip(
        decisions,
        variants[False],
        variants[True],
    ):
        if disabled.action == enabled.action:
            continue
        changes.append(
            {
                "frame": int(row["frame"]),
                "spell_id": row.get("spell", {}).get("spell_id"),
                "safety_state_value": row["corridor"]["safety_value"][
                    "state_value"
                ],
                "best_actions": row["corridor"]["safety_value"][
                    "best_actions"
                ],
                "disabled": _decision_metrics(disabled),
                "enabled": _decision_metrics(enabled),
            }
        )

    def summarize(enabled: bool) -> dict[str, object]:
        selected = variants[enabled]
        return {
            "median_ms": statistics.median(durations[enabled]),
            "p95_ms": _percentile(durations[enabled], 0.95),
            "robust_collision_count": sum(
                decision.robust_collisions > 0 for decision in selected
            ),
            "negative_robust_clearance_count": sum(
                decision.robust_min_clearance < 0.0 for decision in selected
            ),
            "terminal_collision_count": sum(
                decision.terminal_threat_collisions > 0
                for decision in selected
            ),
            "negative_terminal_clearance_count": sum(
                decision.terminal_threat_min_clearance < 0.0
                for decision in selected
            ),
            "minimum_clearance": {
                "median": statistics.median(
                    decision.min_clearance for decision in selected
                ),
                "p05": _percentile(
                    [decision.min_clearance for decision in selected],
                    0.05,
                ),
            },
        }

    enabled_by_frame = {
        int(row["frame"]): decision
        for row, decision in zip(decisions, variants[True])
    }
    physical_match = sum(
        enabled_by_frame[int(row["frame"])].action
        == str(row["corridor"]["safety_value"]["selected_action"])
        for row in decisions
    )
    result = {
        "schema": "th08-safety-value-replay-v1",
        "trace": str(args.trace),
        "trace_sha256": digest.hexdigest(),
        "scope": (
            "Offline paired ablation over retained trace-radius hazards and "
            "exact laser lifecycle state. It is not physical survival "
            "evidence, and replay can diverge from the live full-hazard "
            "decision."
        ),
        "eligible_count": eligible_count,
        "sample_count": len(decisions),
        "prehit_window": args.prehit_window,
        "spell_id": args.spell,
        "variants": {
            "disabled": summarize(False),
            "enabled": summarize(True),
        },
        "action_change_count": len(changes),
        "enabled_live_action_match_count": physical_match,
        "action_changes": changes,
    }
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "eligible_count": eligible_count,
                "sample_count": len(decisions),
                "variants": result["variants"],
                "action_change_count": len(changes),
                "enabled_live_action_match_count": physical_match,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
