#!/usr/bin/env python3
"""Compare fused and object-based local laser projection on a live trace."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import time
from pathlib import Path
from unittest.mock import patch

import th08_live_dodge_agent as live_agent
from benchmark_recovery_control_reserve import _replay_decision


def _legacy_laser_frames(
    lasers,
    *,
    horizon: int,
    snapshot_lag: int = 0,
):
    return tuple(
        live_agent._pack_laser_frame(frame)
        for frame in live_agent.build_laser_collision_frames(
            lasers,
            horizon=horizon,
            snapshot_lag=snapshot_lag,
        )
    )


def _percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    return ordered[round(fraction * (len(ordered) - 1))]


def _sample_rows(rows: list[dict[str, object]], count: int):
    if len(rows) <= count:
        return rows
    return [
        rows[math.floor(index * len(rows) / count)]
        for index in range(count)
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--samples", type=int, default=100)
    parser.add_argument("--spell", type=int, default=50)
    args = parser.parse_args(argv)
    if args.samples <= 0:
        raise ValueError("sample count must be positive")

    digest = hashlib.sha256()
    rows: list[dict[str, object]] = []
    with args.trace.open("rb") as source:
        for raw_line in source:
            digest.update(raw_line)
            row = json.loads(raw_line)
            if (
                row.get("kind") == "decision"
                and row.get("active_lasers", 0) > 0
                and row.get("corridor", {}).get("viability")
                and (
                    args.spell is None
                    or row.get("spell", {}).get("spell_id") == args.spell
                )
            ):
                rows.append(row)
    eligible_count = len(rows)
    rows = _sample_rows(rows, args.samples)
    if not rows:
        raise RuntimeError("trace contains no eligible laser decisions")

    durations: dict[str, list[float]] = {"legacy": [], "fused": []}
    decisions: dict[str, list[object]] = {"legacy": [], "fused": []}
    for index, row in enumerate(rows):
        order = (
            ("legacy", "fused")
            if index % 2 == 0
            else ("fused", "legacy")
        )
        for variant in order:
            started = time.perf_counter()
            if variant == "legacy":
                with patch.object(
                    live_agent,
                    "_build_packed_laser_collision_frames",
                    _legacy_laser_frames,
                ):
                    decision = _replay_decision(
                        row,
                        recovery_control_reserve=True,
                    )
            else:
                decision = _replay_decision(
                    row,
                    recovery_control_reserve=True,
                )
            durations[variant].append(
                (time.perf_counter() - started) * 1000.0
            )
            decisions[variant].append(decision)

    differences = [
        {
            "frame": int(row["frame"]),
            "legacy_action": legacy.action,
            "fused_action": fused.action,
            "full_decision_equal": legacy == fused,
        }
        for row, legacy, fused in zip(
            rows,
            decisions["legacy"],
            decisions["fused"],
        )
        if legacy != fused
    ]

    def summary(variant: str) -> dict[str, float]:
        values = durations[variant]
        return {
            "median_ms": statistics.median(values),
            "p95_ms": _percentile(values, 0.95),
            "max_ms": max(values),
        }

    legacy = summary("legacy")
    fused = summary("fused")
    result = {
        "schema": "th08-local-laser-fusion-benchmark-v1",
        "trace": str(args.trace),
        "trace_sha256": digest.hexdigest(),
        "scope": (
            "Offline paired replay over retained trace-radius hazards and "
            "exact TH08 laser lifecycle state; this is performance and "
            "semantic-parity evidence, not physical survival evidence."
        ),
        "spell_id": args.spell,
        "eligible_count": eligible_count,
        "sample_count": len(rows),
        "variants": {
            "legacy_object_pipeline": legacy,
            "fused_numeric_pipeline": fused,
        },
        "median_speedup": legacy["median_ms"] / fused["median_ms"],
        "p95_speedup": legacy["p95_ms"] / fused["p95_ms"],
        "action_difference_count": sum(
            legacy.action != fused.action
            for legacy, fused in zip(
                decisions["legacy"],
                decisions["fused"],
            )
        ),
        "full_decision_difference_count": len(differences),
        "differences": differences,
    }
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                key: result[key]
                for key in (
                    "sample_count",
                    "variants",
                    "median_speedup",
                    "p95_speedup",
                    "action_difference_count",
                    "full_decision_difference_count",
                )
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
