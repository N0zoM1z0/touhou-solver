#!/usr/bin/env python3
"""Benchmark the cheap terminal-threat rollout on retained live decisions."""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import time
from pathlib import Path

from th08_live_dodge_agent import Bullet, choose_action


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[int(0.95 * (len(ordered) - 1))]


def _decision(row: dict[str, object], threat_horizon: int):
    bullets = tuple(
        Bullet(
            float(body[1]),
            float(body[2]),
            float(body[3]),
            float(body[4]),
            float(body[5]),
            float(body[6]),
            int(body[7]),
            int(body[0]),
        )
        for body in row["nearby_bullets"]
    )
    viability = row["corridor"]["viability"]
    current_mask = int(row["input_snapshot"]["current"])
    return choose_action(
        player_x=float(row["player"]["x"]),
        player_y=float(row["player"]["y"]),
        bullets=bullets,
        lasers=(),
        previous_direction=current_mask & 0xF0,
        can_bomb=False,
        previous_focus=bool(current_mask & 0x04),
        snapshot_lag=int(row["snapshot_lag"]),
        control_delay_frames=int(row["control_delay_frames"]),
        control_delay_candidates=tuple(row["control_delay_candidates"]),
        action_hold_frames=int(row["action_hold_frames"]),
        horizon=10,
        threat_horizon=threat_horizon,
        allowed_first_actions=tuple(viability["safe_actions"]),
        viability_repair_volumes=tuple(
            viability["repair_volumes"].items()
        ),
        viability_position_error=float(
            viability.get("position_error", 0.0)
        ),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--samples", type=int, default=100)
    parser.add_argument("--minimum-bullets", type=int, default=100)
    args = parser.parse_args()

    rows = []
    digest = hashlib.sha256()
    with args.trace.open("rb") as source:
        for raw_line in source:
            digest.update(raw_line)
            row = json.loads(raw_line)
            viability = row.get("corridor", {}).get("viability", {})
            if (
                row.get("kind") == "decision"
                and len(row.get("nearby_bullets", ()))
                >= args.minimum_bullets
                and viability.get("safe_actions")
            ):
                rows.append(row)
    if not rows:
        raise SystemExit("no eligible decisions")
    stride = max(1, len(rows) // args.samples)
    rows = rows[::stride][: args.samples]

    durations = {10: [], 32: []}
    actions = {10: [""] * len(rows), 32: [""] * len(rows)}
    triggered = {10: 0, 32: 0}
    relaxed = {10: 0, 32: 0}
    for index, row in enumerate(rows):
        order = (10, 32) if index % 2 == 0 else (32, 10)
        for horizon in order:
            started = time.perf_counter()
            decision = _decision(row, horizon)
            durations[horizon].append(
                (time.perf_counter() - started) * 1000.0
            )
            actions[horizon][index] = decision.action
            triggered[horizon] += decision.terminal_threat_horizon > 10
            relaxed[horizon] += decision.viability_constraint_relaxed
    variants = {}
    for horizon in (10, 32):
        variants[str(horizon)] = {
            "median_ms": statistics.median(durations[horizon]),
            "p95_ms": _p95(durations[horizon]),
            "max_ms": max(durations[horizon]),
            "triggered_count": triggered[horizon],
            "constraint_relaxed_count": relaxed[horizon],
        }

    result = {
        "schema": "th08-terminal-threat-benchmark-v1",
        "trace": str(args.trace),
        "trace_sha256": digest.hexdigest(),
        "sample_count": len(rows),
        "minimum_bullets": args.minimum_bullets,
        "scope": (
            "Bullet-only local planner benchmark using retained player, "
            "latency, action-hold, and viability guidance."
        ),
        "variants": variants,
        "action_change_count": sum(
            left != right
            for left, right in zip(actions[10], actions[32])
        ),
        "interpretation": (
            "This measures offline compute and selected-action sensitivity; "
            "it is not physical survival acceptance."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2) + "\n",
        encoding="utf-8",
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
