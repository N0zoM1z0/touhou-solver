#!/usr/bin/env python3
"""Replay Hard roots through immutable-baseline supplemental beam widths."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import statistics
import time

import th08_live_dodge_agent as live
from benchmarks.benchmark_preloss_continuation_reserve import (
    _eligible,
    _hit_frames,
    _next_hit,
    _numeric_summary,
    _reservoir_add,
)
from benchmarks.benchmark_recovery_control_reserve import _replay_decision


def _hard_components(decision: object) -> tuple[int | float, ...]:
    return (
        decision.robust_collisions,
        max(-decision.robust_min_clearance, 0.0),
        decision.local_collisions,
        max(-decision.min_clearance, 0.0),
        decision.terminal_threat_collisions,
        max(-decision.terminal_threat_min_clearance, 0.0),
    )


def _componentwise_regression(
    candidate: tuple[int | float, ...],
    incumbent: tuple[int | float, ...],
) -> bool:
    return any(
        candidate_value > incumbent_value
        for candidate_value, incumbent_value in zip(
            candidate,
            incumbent,
        )
    )


def _variant_name(width: int | None) -> str:
    if width is None:
        return "historical"
    if width == 0:
        return "final_only"
    return f"supplemental_{width}"


def _parse_widths(value: str) -> tuple[int, ...]:
    widths = tuple(int(part) for part in value.split(",") if part)
    if not widths or any(width <= 0 for width in widths):
        raise argparse.ArgumentTypeError(
            "supplemental widths must be comma-separated positive integers"
        )
    if tuple(dict.fromkeys(widths)) != widths:
        raise argparse.ArgumentTypeError(
            "supplemental widths must be unique"
        )
    return widths


def _timing(values: list[float]) -> dict[str, float]:
    return _numeric_summary(values)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("traces", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=400)
    parser.add_argument("--prehit-window", type=int, default=0)
    parser.add_argument(
        "--widths",
        type=_parse_widths,
        default=(4, 8, 12, 24),
    )
    parser.add_argument(
        "--backend",
        choices=("native", "python"),
        default="native",
    )
    args = parser.parse_args(argv)
    if args.samples <= 0 or args.prehit_window < 0:
        raise ValueError("sample count must be positive and window nonnegative")
    if args.backend == "native":
        live._configure_local_hazard_backend("native")
        live._configure_local_beam_reducer("native")
    else:
        live._configure_local_hazard_backend("numpy")
        live._configure_local_beam_reducer("python")

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
    eligible_by_trace: dict[str, int] = {}
    generator = random.Random(0xCE0130)
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

    variants: tuple[int | None, ...] = (None, 0, *args.widths)
    decisions: dict[str, list[object]] = {
        _variant_name(width): [] for width in variants
    }
    durations: dict[str, list[float]] = {
        _variant_name(width): [] for width in variants
    }
    for root_index, (_trace, row, _next_hit_frame) in enumerate(reservoir):
        offset = root_index % len(variants)
        order = variants[offset:] + variants[:offset]
        root_results: dict[str, object] = {}
        root_durations: dict[str, float] = {}
        for width in order:
            name = _variant_name(width)
            started_ns = time.perf_counter_ns()
            root_results[name] = _replay_decision(
                row,
                recovery_control_reserve=True,
                preloss_continuation_preference=width is not None,
                preloss_supplemental_beam_width=width or 0,
            )
            root_durations[name] = (
                time.perf_counter_ns() - started_ns
            ) / 1_000_000.0
        for width in variants:
            name = _variant_name(width)
            decisions[name].append(root_results[name])
            durations[name].append(root_durations[name])

    historical = decisions["historical"]
    reports: dict[str, object] = {}
    failures: list[dict[str, object]] = []
    change_examples: list[dict[str, object]] = []
    for width in variants:
        name = _variant_name(width)
        variant = decisions[name]
        active_count = sum(
            decision.preloss_continuation_preference_active
            for decision in variant
        )
        action_change_count = 0
        selected_from_supplemental = 0
        historical_action_mismatch_count = 0
        global_membership_violation_count = 0
        hard_component_regression_count = 0
        route_gate_regression_count = 0
        continuation_contract_violation_count = 0
        failure_count = 0
        repair_improvement_count = 0
        reserve_improvement_count = 0
        for index, (
            (trace, row, next_hit_frame),
            baseline,
            candidate,
        ) in enumerate(zip(reservoir, historical, variant)):
            active = bool(
                candidate.preloss_continuation_preference_active
            )
            changed = candidate.action != baseline.action
            action_change_count += changed
            selected_from_supplemental += bool(
                candidate.preloss_selected_from_supplemental
            )
            failure_count += (
                candidate.preloss_supplemental_failure is not None
            )
            if active:
                historical_action_mismatch_count += (
                    candidate.preloss_historical_action
                    != baseline.action
                )
                safe_actions = set(
                    row["corridor"]["viability"]["safe_actions"]
                )
                global_membership_violation_count += (
                    candidate.action not in safe_actions
                )
                hard_regression = _componentwise_regression(
                    _hard_components(candidate),
                    _hard_components(baseline),
                )
                hard_component_regression_count += hard_regression
                route_regression = (
                    candidate.planned_route_gate_deficit
                    > baseline.planned_route_gate_deficit
                )
                route_gate_regression_count += route_regression
                candidate_continuation = (
                    -candidate.viability_repair_volume,
                    candidate.viability_control_reserve_deficit,
                )
                baseline_continuation = (
                    -baseline.viability_repair_volume,
                    baseline.viability_control_reserve_deficit,
                )
                continuation_violation = (
                    changed
                    and candidate_continuation
                    >= baseline_continuation
                )
                continuation_contract_violation_count += (
                    continuation_violation
                )
                repair_improvement_count += (
                    changed
                    and candidate.viability_repair_volume
                    > baseline.viability_repair_volume
                )
                reserve_improvement_count += (
                    changed
                    and candidate.viability_repair_volume
                    == baseline.viability_repair_volume
                    and candidate.viability_control_reserve_deficit
                    < baseline.viability_control_reserve_deficit
                )
                if (
                    hard_regression
                    or route_regression
                    or continuation_violation
                    or candidate.action not in safe_actions
                    or candidate.preloss_historical_action
                    != baseline.action
                ):
                    failures.append(
                        {
                            "variant": name,
                            "trace": str(trace),
                            "frame": int(row["frame"]),
                            "historical_action": baseline.action,
                            "candidate_action": candidate.action,
                            "historical_hard": _hard_components(
                                baseline
                            ),
                            "candidate_hard": _hard_components(
                                candidate
                            ),
                            "historical_route_gate_deficit": (
                                baseline.planned_route_gate_deficit
                            ),
                            "candidate_route_gate_deficit": (
                                candidate.planned_route_gate_deficit
                            ),
                        }
                    )
            if changed and len(change_examples) < 64:
                frame = int(row["frame"])
                change_examples.append(
                    {
                        "variant": name,
                        "trace": str(trace),
                        "frame": frame,
                        "time_to_hit": (
                            next_hit_frame - frame
                            if next_hit_frame is not None
                            else None
                        ),
                        "historical_action": baseline.action,
                        "candidate_action": candidate.action,
                        "selected_from_supplemental": (
                            candidate
                            .preloss_selected_from_supplemental
                        ),
                        "historical_repair_volume": (
                            baseline.viability_repair_volume
                        ),
                        "candidate_repair_volume": (
                            candidate.viability_repair_volume
                        ),
                        "historical_reserve_deficit": (
                            baseline.viability_control_reserve_deficit
                        ),
                        "candidate_reserve_deficit": (
                            candidate.viability_control_reserve_deficit
                        ),
                    }
                )
        reports[name] = {
            "width": width,
            "active_count": active_count,
            "action_change_count": action_change_count,
            "selected_from_supplemental_count": (
                selected_from_supplemental
            ),
            "historical_action_mismatch_count": (
                historical_action_mismatch_count
            ),
            "global_membership_violation_count": (
                global_membership_violation_count
            ),
            "hard_component_regression_count": (
                hard_component_regression_count
            ),
            "route_gate_regression_count": (
                route_gate_regression_count
            ),
            "continuation_contract_violation_count": (
                continuation_contract_violation_count
            ),
            "repair_improvement_count": repair_improvement_count,
            "reserve_improvement_at_equal_repair_count": (
                reserve_improvement_count
            ),
            "supplemental_failure_count": failure_count,
            "timing_ms": _timing(durations[name]),
            "supplemental_beam_ms": _timing(
                [
                    float(
                        decision.local_certificate_timing
                        .supplemental_beam_ms
                    )
                    for decision in variant
                ]
            ),
            "admitted_candidate_count": _numeric_summary(
                [
                    float(
                        decision
                        .preloss_supplemental_candidate_count
                    )
                    for decision in variant
                ]
            ),
        }

    result = {
        "schema": "th08-supplemental-continuation-lane-benchmark-v1",
        "scope": (
            "Paired same-root replay. Historical beam output remains the "
            "incumbent; no future physical trajectory is replayed."
        ),
        "backend": args.backend,
        "configuration": {
            "samples": args.samples,
            "prehit_window": args.prehit_window,
            "supplemental_widths": args.widths,
            "rotating_variant_order": True,
        },
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
        "variants": reports,
        "failure_count": len(failures),
        "failures": failures[:64],
        "change_examples": change_examples,
        "passed": not failures,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "sample_count": len(reservoir),
                "variants": reports,
                "failure_count": len(failures),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
