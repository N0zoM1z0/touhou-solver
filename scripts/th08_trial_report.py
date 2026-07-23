#!/usr/bin/env python3
"""Summarize one TH08 live-agent JSONL trial into CEGAR evidence."""

from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path
from typing import Iterable


def _latency(values: Iterable[float]) -> dict[str, float] | None:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return None
    p95_index = int(0.95 * (len(ordered) - 1))
    return {
        "median": statistics.median(ordered),
        "p95": ordered[p95_index],
        "max": ordered[-1],
    }


def _nearest_bullet(row: dict[str, object]) -> dict[str, float | int] | None:
    player = row.get("player")
    bullets = row.get("nearby_bullets")
    if not isinstance(player, dict) or not isinstance(bullets, list):
        return None
    player_x = float(player["x"])
    player_y = float(player["y"])
    candidates = []
    for bullet in bullets:
        if not isinstance(bullet, list) or len(bullet) < 7:
            continue
        dx = abs(float(bullet[1]) - player_x)
        dy = abs(float(bullet[2]) - player_y)
        clearance_x = dx - (2.0 + float(bullet[5]))
        clearance_y = dy - (2.0 + float(bullet[6]))
        if clearance_x <= 0.0 and clearance_y <= 0.0:
            aabb_clearance = max(clearance_x, clearance_y)
        else:
            aabb_clearance = math.hypot(
                max(clearance_x, 0.0),
                max(clearance_y, 0.0),
            )
        candidates.append(
            {
                "slot": int(bullet[0]),
                "x": float(bullet[1]),
                "y": float(bullet[2]),
                "center_distance": math.hypot(dx, dy),
                "aabb_clearance": aabb_clearance,
            }
        )
    return min(candidates, key=lambda item: item["center_distance"]) if candidates else None


def summarize_rows(rows: list[dict[str, object]]) -> dict[str, object]:
    decisions = [row for row in rows if row.get("kind") == "decision"]
    summaries = [row for row in rows if row.get("kind") == "summary"]
    if not decisions:
        raise ValueError("trial contains no decision records")

    first = decisions[0]
    last = decisions[-1]
    hit_frames = [
        int(row["frame"])
        for row in decisions
        if row.get("hit_started")
        or "+deathbomb" in str(row.get("action", ""))
    ]
    unique_solutions: dict[int, dict[str, object]] = {}
    corridor_records = []
    gate_samples = []
    for row in decisions:
        corridor = row.get("corridor")
        if not isinstance(corridor, dict):
            continue
        corridor_records.append(corridor)
        unique_solutions.setdefault(int(corridor["source_frame"]), corridor)
        target = corridor.get("target")
        if isinstance(target, dict) and "slack" in target:
            gate_samples.append(
                {
                    "frame": int(row["frame"]),
                    "source_frame": int(corridor["source_frame"]),
                    "lane": corridor["lane"],
                    "slack": float(target["slack"]),
                    "deadline": int(target["deadline"]),
                    "travel_frames": float(target["travel_frames"]),
                }
            )

    lane_transitions = []
    previous_lane = None
    for source_frame, solution in sorted(unique_solutions.items()):
        lane = str(solution["lane"])
        if lane != previous_lane:
            lane_transitions.append(
                {
                    "source_frame": source_frame,
                    "lane": lane,
                    "bottleneck_clearance": float(
                        solution["bottleneck_clearance"]
                    ),
                }
            )
            previous_lane = lane

    first_hit_analysis = None
    if hit_frames:
        hit_frame = hit_frames[0]
        hit_row = next(
            row for row in decisions if int(row["frame"]) == hit_frame
        )
        window = [
            sample
            for sample in gate_samples
            if hit_frame - 240 <= sample["frame"] <= hit_frame
        ]
        nonnegative = [sample for sample in window if sample["slack"] >= 0.0]
        negative = [sample for sample in window if sample["slack"] < 0.0]
        pipeline_samples = [
            {
                "frame": int(row["frame"]),
                "clearance": float(row["pipeline_clearance"]),
            }
            for row in decisions
            if hit_frame - 240 <= int(row["frame"]) <= hit_frame
            and row.get("pipeline_clearance") is not None
        ]
        nonpositive_pipeline = [
            sample
            for sample in pipeline_samples
            if sample["clearance"] <= 0.0
        ]
        first_hit_analysis = {
            "hit_frame": hit_frame,
            "window_start": hit_frame - 240,
            "last_nonnegative_gate": nonnegative[-1] if nonnegative else None,
            "first_negative_gate": negative[0] if negative else None,
            "minimum_gate_slack": (
                min(sample["slack"] for sample in window)
                if window
                else None
            ),
            "first_nonpositive_pipeline": (
                nonpositive_pipeline[0] if nonpositive_pipeline else None
            ),
            "minimum_pipeline_clearance": (
                min(sample["clearance"] for sample in pipeline_samples)
                if pipeline_samples
                else None
            ),
            "nearest_bullet": _nearest_bullet(hit_row),
        }

    resources_first = first["resources"]
    resources_last = last["resources"]
    summary = summaries[-1] if summaries else {}
    stale_count = sum(
        bool(record.get("stale")) for record in corridor_records
    )
    return {
        "decision_count": len(decisions),
        "first_frame": int(first["frame"]),
        "last_frame": int(last["frame"]),
        "frame_span": int(last["frame"]) - int(first["frame"]),
        "termination_reason": summary.get("termination_reason", "missing_summary"),
        "counter_gaps": summary.get("counter_gaps"),
        "hit_frames": hit_frames,
        "resources": {
            "bombs": [
                float(resources_first["bombs"]),
                float(resources_last["bombs"]),
            ],
            "lives": [
                float(resources_first["lives"]),
                float(resources_last["lives"]),
            ],
            "power": [
                float(resources_first["power"]),
                float(resources_last["power"]),
            ],
        },
        "local_latency_ms": {
            "read": _latency(row["read_ms"] for row in decisions),
            "plan": _latency(row["plan_ms"] for row in decisions),
        },
        "frame_lag": {
            "snapshot": _latency(
                row["snapshot_lag"]
                for row in decisions
                if row.get("snapshot_lag") is not None
            ),
            "action": _latency(
                row["action_lag"]
                for row in decisions
                if row.get("action_lag") is not None
            ),
            "modeled_control_delays": sorted(
                {
                    int(row["control_delay_frames"])
                    for row in decisions
                    if row.get("control_delay_frames") is not None
                }
            ),
        },
        "corridor": {
            "record_count": len(corridor_records),
            "unique_solution_count": len(unique_solutions),
            "stale_record_count": stale_count,
            "stale_fraction": (
                stale_count / len(corridor_records)
                if corridor_records
                else math.nan
            ),
            "solve_latency_ms": _latency(
                solution["solve_ms"] for solution in unique_solutions.values()
            ),
            "lane_transitions": lane_transitions,
        },
        "boundary_occupancy": {
            "bottom_frames": sum(
                float(row["player"]["y"]) >= 428.0 for row in decisions
            ),
            "side_frames": sum(
                float(row["player"]["x"]) <= 12.0
                or float(row["player"]["x"]) >= 372.0
                for row in decisions
            ),
        },
        "first_hit_analysis": first_hit_analysis,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path, nargs="?")
    args = parser.parse_args(argv)
    rows = [
        json.loads(line)
        for line in args.input.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    report = summarize_rows(rows)
    rendered = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output is None:
        print(rendered, end="")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
