#!/usr/bin/env python3
"""Replay viable Hard roots with the default-off pre-loss preference."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import statistics
import time
from typing import Any

from benchmarks.benchmark_recovery_control_reserve import _replay_decision


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[round(0.95 * (len(ordered) - 1))]


def _p05(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[round(0.05 * (len(ordered) - 1))]


def _hard_vector(decision: object) -> tuple[object, ...]:
    return (
        decision.robust_collisions,
        max(-decision.robust_min_clearance, 0.0),
        decision.terminal_threat_collisions,
        max(-decision.terminal_threat_min_clearance, 0.0),
        max(-decision.min_clearance, 0.0),
    )


def _comparison(left: object, right: object) -> str:
    if left < right:
        return "improved"
    if left > right:
        return "regressed"
    return "equal"


def _eligible(row: dict[str, object]) -> bool:
    corridor = row.get("corridor")
    if not isinstance(corridor, dict):
        return False
    viability = corridor.get("viability")
    if not isinstance(viability, dict):
        return False
    if not viability.get("support_covers_current", True):
        return False
    safe_actions = tuple(viability.get("safe_actions") or ())
    repairs = viability.get("repair_volumes") or {}
    return bool(
        safe_actions
        and isinstance(repairs, dict)
        and set(safe_actions) <= repairs.keys()
    )


def _reservoir_add(
    reservoir: list[tuple[Path, dict[str, object], int | None]],
    *,
    value: tuple[Path, dict[str, object], int | None],
    seen_count: int,
    sample_count: int,
    generator: random.Random,
) -> None:
    if len(reservoir) < sample_count:
        reservoir.append(value)
        return
    slot = generator.randrange(seen_count)
    if slot < sample_count:
        reservoir[slot] = value


def _hit_frames(trace: Path, digest: Any) -> list[int]:
    frames: list[int] = []
    with trace.open("rb") as source:
        for raw_line in source:
            digest.update(raw_line)
            row = json.loads(raw_line)
            if row.get("kind") == "decision" and row.get("hit_started"):
                frames.append(int(row["frame"]))
    return frames


def _next_hit(hit_frames: list[int], frame: int) -> int | None:
    return next(
        (hit_frame for hit_frame in hit_frames if hit_frame >= frame),
        None,
    )


def _numeric_summary(values: list[float]) -> dict[str, float]:
    return {
        "median": statistics.median(values),
        "p05": _p05(values),
        "p95": _p95(values),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("traces", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=800)
    parser.add_argument(
        "--prehit-window",
        type=int,
        default=0,
        help="retain only roots this many frames before the next hit",
    )
    args = parser.parse_args(argv)
    if args.samples <= 0 or args.prehit_window < 0:
        raise ValueError("sample count must be positive and window nonnegative")

    trace_metadata: dict[Path, dict[str, object]] = {}
    for trace in args.traces:
        digest = hashlib.sha256()
        hits = _hit_frames(trace, digest)
        trace_metadata[trace] = {
            "sha256": digest.hexdigest(),
            "hit_frames": hits,
        }

    reservoir: list[tuple[Path, dict[str, object], int | None]] = []
    eligible_count = 0
    generator = random.Random(0xCE0129)
    eligible_by_trace: dict[str, int] = {}
    for trace in args.traces:
        hit_frames = trace_metadata[trace]["hit_frames"]
        assert isinstance(hit_frames, list)
        trace_eligible = 0
        with trace.open(encoding="utf-8") as source:
            for line in source:
                row = json.loads(line)
                if row.get("kind") != "decision" or not _eligible(row):
                    continue
                frame = int(row["frame"])
                next_hit = _next_hit(hit_frames, frame)
                if (
                    args.prehit_window
                    and (
                        next_hit is None
                        or next_hit - frame > args.prehit_window
                    )
                ):
                    continue
                eligible_count += 1
                trace_eligible += 1
                _reservoir_add(
                    reservoir,
                    value=(trace, row, next_hit),
                    seen_count=eligible_count,
                    sample_count=args.samples,
                    generator=generator,
                )
        eligible_by_trace[str(trace)] = trace_eligible
    if not reservoir:
        raise RuntimeError("traces contain no eligible viable roots")

    decisions: dict[bool, list[object]] = {False: [], True: []}
    durations: dict[bool, list[float]] = {False: [], True: []}
    for index, (_trace, row, _next_hit_frame) in enumerate(reservoir):
        order = (False, True) if index % 2 == 0 else (True, False)
        for enabled in order:
            started = time.perf_counter_ns()
            decision = _replay_decision(
                row,
                recovery_control_reserve=True,
                preloss_continuation_preference=enabled,
            )
            durations[enabled].append(
                (time.perf_counter_ns() - started) / 1_000_000.0
            )
            decisions[enabled].append(decision)

    def summarize(enabled: bool) -> dict[str, object]:
        variant = decisions[enabled]
        return {
            "timing_ms": _numeric_summary(durations[enabled]),
            "selected_repair_volume": _numeric_summary(
                [float(decision.viability_repair_volume) for decision in variant]
            ),
            "selected_control_reserve_deficit": _numeric_summary(
                [
                    float(decision.viability_control_reserve_deficit)
                    for decision in variant
                ]
            ),
            "planned_route_gate_deficit": _numeric_summary(
                [
                    float(decision.planned_route_gate_deficit)
                    for decision in variant
                ]
            ),
            "robust_collision_count": sum(
                decision.robust_collisions > 0 for decision in variant
            ),
            "negative_robust_clearance_count": sum(
                decision.robust_min_clearance < 0.0 for decision in variant
            ),
            "terminal_collision_count": sum(
                decision.terminal_threat_collisions > 0
                for decision in variant
            ),
            "negative_terminal_clearance_count": sum(
                decision.terminal_threat_min_clearance < 0.0
                for decision in variant
            ),
            "bomb_count": sum(bool(decision.bomb) for decision in variant),
            "preloss_preference_active_count": sum(
                bool(decision.preloss_continuation_preference_active)
                for decision in variant
            ),
        }

    changes: list[dict[str, object]] = []
    hard_directions: list[str] = []
    repair_directions: list[str] = []
    reserve_directions: list[str] = []
    gate_directions: list[str] = []
    active_global_membership_violations = 0
    for (
        trace,
        row,
        next_hit_frame,
    ), baseline, proposal in zip(
        reservoir,
        decisions[False],
        decisions[True],
    ):
        viability = row["corridor"]["viability"]
        safe_actions = set(viability["safe_actions"])
        active_global_membership_violations += int(
            proposal.preloss_continuation_preference_active
            and proposal.action not in safe_actions
        )
        hard_direction = _comparison(
            _hard_vector(proposal),
            _hard_vector(baseline),
        )
        repair_direction = _comparison(
            -proposal.viability_repair_volume,
            -baseline.viability_repair_volume,
        )
        reserve_direction = _comparison(
            proposal.viability_control_reserve_deficit,
            baseline.viability_control_reserve_deficit,
        )
        gate_direction = _comparison(
            proposal.planned_route_gate_deficit,
            baseline.planned_route_gate_deficit,
        )
        if baseline.action == proposal.action:
            continue
        hard_directions.append(hard_direction)
        repair_directions.append(repair_direction)
        reserve_directions.append(reserve_direction)
        gate_directions.append(gate_direction)
        frame = int(row["frame"])
        changes.append(
            {
                "trace": str(trace),
                "frame": frame,
                "stage_route_index": int(row["stage_route_index"]),
                "next_hit_frame": next_hit_frame,
                "time_to_hit": (
                    next_hit_frame - frame
                    if next_hit_frame is not None
                    else None
                ),
                "baseline_action": baseline.action,
                "proposal_action": proposal.action,
                "baseline_repair_volume": (
                    baseline.viability_repair_volume
                ),
                "proposal_repair_volume": (
                    proposal.viability_repair_volume
                ),
                "baseline_reserve_deficit": (
                    baseline.viability_control_reserve_deficit
                ),
                "proposal_reserve_deficit": (
                    proposal.viability_control_reserve_deficit
                ),
                "baseline_route_gate_deficit": (
                    baseline.planned_route_gate_deficit
                ),
                "proposal_route_gate_deficit": (
                    proposal.planned_route_gate_deficit
                ),
                "hard_vector_direction": hard_direction,
            }
        )

    def counts(values: list[str]) -> dict[str, int]:
        return {
            name: values.count(name)
            for name in ("improved", "equal", "regressed")
        }

    result = {
        "schema": "th08-preloss-continuation-reserve-benchmark-v1",
        "scope": (
            "Paired same-root offline replay over retained trace-radius "
            "hazards and lifecycle state. This does not replay future "
            "controller state and is not physical survival evidence."
        ),
        "proposal": (
            "After unchanged beam pruning and complete terminal scoring, "
            "rank exact worst-delay repair volume and delay-scaled interior "
            "reserve before route and ordinary soft costs inside a complete "
            "nonrelaxed viable action set."
        ),
        "traces": [
            {
                "path": str(trace),
                "sha256": trace_metadata[trace]["sha256"],
                "hit_count": len(trace_metadata[trace]["hit_frames"]),
                "eligible_count": eligible_by_trace[str(trace)],
            }
            for trace in args.traces
        ],
        "eligible_count": eligible_count,
        "sample_count": len(reservoir),
        "prehit_window": args.prehit_window,
        "alternating_execution_order": True,
        "variants": {
            "baseline": summarize(False),
            "proposal": summarize(True),
        },
        "action_change_count": len(changes),
        "changed_action_hard_vector_counts": counts(hard_directions),
        "changed_action_repair_volume_counts": counts(repair_directions),
        "changed_action_reserve_deficit_counts": counts(
            reserve_directions
        ),
        "changed_action_route_gate_deficit_counts": counts(
            gate_directions
        ),
        "active_global_membership_violation_count": (
            active_global_membership_violations
        ),
        "proposal_inactive_count": sum(
            not decision.preloss_continuation_preference_active
            for decision in decisions[True]
        ),
        "action_change_stage_counts": {
            str(stage): sum(
                change["stage_route_index"] == stage for change in changes
            )
            for stage in sorted(
                {int(change["stage_route_index"]) for change in changes}
            )
        },
        "action_changes": changes,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "eligible_count": eligible_count,
                "sample_count": len(reservoir),
                "action_change_count": len(changes),
                "changed_action_hard_vector_counts": counts(
                    hard_directions
                ),
                "changed_action_repair_volume_counts": counts(
                    repair_directions
                ),
                "changed_action_reserve_deficit_counts": counts(
                    reserve_directions
                ),
                "changed_action_route_gate_deficit_counts": counts(
                    gate_directions
                ),
                "active_global_membership_violation_count": (
                    active_global_membership_violations
                ),
                "variants": result["variants"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
