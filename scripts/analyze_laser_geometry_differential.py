#!/usr/bin/env python3
"""Measure same-allocation TH08 laser geometry drift in a runtime trace."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Iterable


def _percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[round((len(ordered) - 1) * fraction)]


def _statistics(values: list[float], *, tolerance: float) -> dict[str, object]:
    return {
        "count": len(values),
        "median": _percentile(values, 0.5),
        "p95": _percentile(values, 0.95),
        "p99": _percentile(values, 0.99),
        "maximum": max(values, default=None),
        "over_tolerance_count": sum(value > tolerance for value in values),
    }


def _same_allocation(left: list[object], right: list[object]) -> bool:
    if len(left) < 15 or len(right) < 15:
        return False
    if any(left[index] is None or right[index] is None for index in range(7, 14)):
        return False
    return (
        abs(float(left[0]) - float(right[0])) <= 1e-3
        and abs(float(left[1]) - float(right[1])) <= 1e-3
        and abs(float(left[2]) - float(right[2])) <= 1e-5
        and float(left[7]) == float(right[7])
        and float(left[8]) == float(right[8])
        and float(left[10]) == float(right[10])
        and int(left[11]) == int(right[11])
        and int(left[13]) == int(right[13])
        and int(right[12]) > int(left[12])
    )


def analyze(
    rows: Iterable[dict[str, object]],
    *,
    spell_id: int | None,
    max_frame_gap: int,
    tolerance: float,
) -> dict[str, object]:
    previous_frame: int | None = None
    previous_lasers: dict[int, list[object]] = {}
    decision_count = 0
    pair_count = 0
    head_errors: list[float] = []
    tail_errors: list[float] = []
    origin_errors: list[float] = []
    angle_errors: list[float] = []
    frame_gaps: list[float] = []
    timer_gaps: list[float] = []

    for row in rows:
        if row.get("kind") != "decision":
            continue
        spell = row.get("spell")
        if spell_id is not None and (
            not isinstance(spell, dict)
            or int(spell.get("spell_id", -1)) != spell_id
        ):
            continue
        frame = int(row["snapshot_frame"])
        lasers = {
            int(laser[6]): laser
            for laser in row.get("lasers", ())
            if isinstance(laser, list) and len(laser) >= 15
        }
        decision_count += 1
        if (
            previous_frame is not None
            and 0 < frame - previous_frame <= max_frame_gap
        ):
            for slot, current in lasers.items():
                previous = previous_lasers.get(slot)
                if previous is None or not _same_allocation(previous, current):
                    continue
                timer_delta = int(current[12]) - int(previous[12])
                head = float(previous[4])
                tail = float(previous[3])
                speed = float(previous[10])
                maximum_length = float(previous[7])
                for _ in range(timer_delta):
                    head += speed
                    if head - tail > maximum_length:
                        tail = head - maximum_length
                    tail = max(tail, 0.0)
                head_errors.append(abs(float(current[4]) - head))
                tail_errors.append(abs(float(current[3]) - tail))
                origin_errors.append(
                    math.hypot(
                        float(current[0]) - float(previous[0]),
                        float(current[1]) - float(previous[1]),
                    )
                )
                angle_errors.append(
                    abs(float(current[2]) - float(previous[2]))
                )
                frame_gaps.append(float(frame - previous_frame))
                timer_gaps.append(float(timer_delta))
                pair_count += 1
        previous_frame = frame
        previous_lasers = lasers

    return {
        "schema": "th08-laser-same-phase-differential-v1",
        "spell_id": spell_id,
        "max_frame_gap": max_frame_gap,
        "tolerance": tolerance,
        "decision_count": decision_count,
        "matched_pair_count": pair_count,
        "head_error": _statistics(head_errors, tolerance=tolerance),
        "tail_error": _statistics(tail_errors, tolerance=tolerance),
        "origin_error": _statistics(origin_errors, tolerance=tolerance),
        "angle_error": _statistics(angle_errors, tolerance=tolerance),
        "frame_gap": _statistics(frame_gaps, tolerance=tolerance),
        "timer_gap": _statistics(timer_gaps, tolerance=tolerance),
        "evidence_boundary": (
            "Pairs are restricted to the same slot, allocation fields, phase, "
            "flags, and increasing native timer. Lifecycle transitions and "
            "collision-width parity require the extended trace schema."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("--spell-id", type=int)
    parser.add_argument("--max-frame-gap", type=int, default=10)
    parser.add_argument("--tolerance", type=float, default=1e-4)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.max_frame_gap < 1 or args.tolerance < 0.0:
        parser.error("frame gap must be positive and tolerance non-negative")

    with args.trace.open(encoding="utf-8-sig") as source:
        report = analyze(
            (json.loads(line) for line in source),
            spell_id=args.spell_id,
            max_frame_gap=args.max_frame_gap,
            tolerance=args.tolerance,
        )
    report["trace"] = args.trace.name
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
