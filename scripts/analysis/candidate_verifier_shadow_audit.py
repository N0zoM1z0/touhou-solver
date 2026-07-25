#!/usr/bin/env python3
"""Summarize physical candidate-verifier delivery and CPU contention."""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter
from pathlib import Path


def _p95(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[int(0.95 * (len(ordered) - 1))]


def _summary(values: list[float]) -> dict[str, float | None]:
    return {
        "median": statistics.median(values) if values else None,
        "p95": _p95(values),
        "max": max(values) if values else None,
    }


def _number(value: object) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return None


def _baseline(path: Path | None) -> dict[str, object] | None:
    if path is None:
        return None
    document = json.loads(path.read_text(encoding="utf-8"))
    totals = document.get("totals", {})
    latency = totals.get("latency_ms", {})
    runtime = totals.get("runtime_timing_ms", {})
    frame_lag = totals.get("frame_lag", {})
    robust = totals.get("robust_viability", {})
    return {
        "source": str(path),
        "read_ms": latency.get("read"),
        "local_plan_ms": runtime.get("local_plan"),
        "previous_iteration_ms": runtime.get("previous_iteration"),
        "before_trace_ms": runtime.get("before_trace"),
        "corridor_bookkeeping_ms": runtime.get(
            "corridor_bookkeeping"
        ),
        "action_lag_frames": frame_lag.get("action"),
        "corridor_solve_ms": robust.get("solve_ms"),
        "clearance_ms": robust.get("solver_phase_ms", {}).get(
            "clearance"
        ),
        "viability_ms": robust.get("solver_phase_ms", {}).get(
            "viability"
        ),
        "first_observed_policy_age_frames": robust.get(
            "first_observed_age_frames"
        ),
        "forecast_lead_frames": robust.get("forecast_lead_frames"),
        "decision_cadence_frames": totals.get(
            "decision_cadence_frames"
        ),
    }


def _median_delta(
    current: dict[str, float | None],
    baseline: object,
) -> dict[str, float | None] | None:
    if not isinstance(baseline, dict):
        return None
    current_median = current.get("median")
    baseline_median = _number(baseline.get("median"))
    if current_median is None or baseline_median is None:
        return None
    return {
        "current_median": current_median,
        "baseline_median": baseline_median,
        "delta": current_median - baseline_median,
        "ratio": (
            current_median / baseline_median
            if baseline_median
            else None
        ),
    }


def audit(
    trace: Path,
    *,
    baseline_dossier: Path | None,
) -> dict[str, object]:
    statuses: Counter[str] = Counter()
    outcome_statuses: Counter[str] = Counter()
    policy_statuses: Counter[str] = Counter()
    seen_outcomes: set[int] = set()
    hit_winning = 0
    hit_issued_best = 0
    attempts_by_boolean: Counter[str] = Counter()
    hits_by_boolean: Counter[str] = Counter()
    winning_hits_by_boolean: Counter[str] = Counter()
    target_attempts = 0
    exact_hits = 0
    submit_ms: list[float] = []
    lookup_ms: list[float] = []
    outcome_queue_ms: list[float] = []
    outcome_elapsed_ms: list[float] = []
    outcome_completed_candidates: list[float] = []
    outcome_timed_out_candidates: list[float] = []
    outcome_unvisited_candidates: list[float] = []
    priority_lowered_count = 0
    read_ms: list[float] = []
    local_plan_ms: list[float] = []
    previous_iteration_ms: list[float] = []
    before_trace_ms: list[float] = []
    corridor_bookkeeping_ms: list[float] = []
    action_lag: list[float] = []
    decision_frames: list[int] = []
    solve_by_policy: dict[int, float] = {}
    first_age_by_policy: dict[int, float] = {}
    forecast_by_policy: dict[int, float] = {}
    phase_by_policy: dict[str, dict[int, float]] = {
        "clearance": {},
        "viability": {},
    }
    termination = None
    final_service = None
    decision_count = 0

    with trace.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"invalid JSON at {trace}:{line_number}: {error}"
                ) from error
            if row.get("kind") == "summary":
                termination = row
                continue
            if row.get("kind") != "decision":
                continue
            decision_count += 1
            frame = row.get("frame")
            if isinstance(frame, int):
                decision_frames.append(frame)
            for raw, destination in (
                (row.get("read_ms"), read_ms),
                (row.get("plan_ms"), local_plan_ms),
                (row.get("action_lag"), action_lag),
            ):
                value = _number(raw)
                if value is not None:
                    destination.append(value)
            timing = row.get("timing_ms")
            if isinstance(timing, dict):
                for name, destination in (
                    ("previous_iteration", previous_iteration_ms),
                    ("before_trace", before_trace_ms),
                    ("corridor_bookkeeping", corridor_bookkeeping_ms),
                ):
                    value = _number(timing.get(name))
                    if value is not None:
                        destination.append(value)

            corridor = row.get("corridor")
            boolean_class = "unavailable"
            if isinstance(corridor, dict):
                viability = corridor.get("viability")
                if isinstance(viability, dict):
                    if viability.get("state_viable") is True:
                        boolean_class = "viable"
                    elif viability.get("state_viable") is False:
                        boolean_class = "losing"
                source_frame = corridor.get("source_frame")
                if isinstance(source_frame, int):
                    status = corridor.get("policy_status")
                    if isinstance(status, str):
                        policy_statuses[status] += 1
                    value = _number(corridor.get("solve_ms"))
                    if value is not None:
                        solve_by_policy.setdefault(source_frame, value)
                    value = _number(corridor.get("age"))
                    if value is not None:
                        first_age_by_policy.setdefault(
                            source_frame,
                            value,
                        )
                    value = _number(
                        corridor.get("forecast_lead_frames")
                    )
                    if value is not None:
                        forecast_by_policy.setdefault(
                            source_frame,
                            value,
                        )
                    phases = corridor.get("solver_timing_ms")
                    if isinstance(phases, dict):
                        for phase in phase_by_policy:
                            value = _number(phases.get(phase))
                            if value is not None:
                                phase_by_policy[phase].setdefault(
                                    source_frame,
                                    value,
                                )

            shadow = row.get("candidate_verifier_shadow")
            if not isinstance(shadow, dict):
                continue
            status = shadow.get("status")
            if not isinstance(status, str):
                status = "missing_status"
            statuses[status] += 1
            for raw, destination in (
                (shadow.get("submit_ms"), submit_ms),
                (shadow.get("lookup_ms"), lookup_ms),
            ):
                value = _number(raw)
                if value is not None:
                    destination.append(value)
            if status in ("hit", "miss"):
                target_attempts += 1
                exact_hits += int(status == "hit")
                attempts_by_boolean[boolean_class] += 1
                if status == "hit":
                    hits_by_boolean[boolean_class] += 1
            result = shadow.get("result")
            if isinstance(result, dict):
                hit_winning += int(result.get("winning") is True)
                if result.get("winning") is True:
                    winning_hits_by_boolean[boolean_class] += 1
                hit_issued_best += int(
                    result.get("issued_in_best") is True
                )
            service = shadow.get("service")
            if not isinstance(service, dict):
                continue
            final_service = service
            outcome = service.get("latest_outcome")
            if not isinstance(outcome, dict):
                continue
            revision = outcome.get("revision")
            if not isinstance(revision, int) or revision in seen_outcomes:
                continue
            seen_outcomes.add(revision)
            outcome_status = outcome.get("status")
            if not isinstance(outcome_status, str):
                outcome_status = "missing_status"
            outcome_statuses[outcome_status] += 1
            priority_lowered_count += int(
                outcome.get("background_priority_lowered") is True
            )
            for raw, destination in (
                (outcome.get("queue_ms"), outcome_queue_ms),
                (outcome.get("elapsed_ms"), outcome_elapsed_ms),
            ):
                value = _number(raw)
                if value is not None:
                    destination.append(value)
            completed = outcome.get("completed_candidates")
            if isinstance(completed, list):
                outcome_completed_candidates.append(float(len(completed)))
            timed_out = outcome.get("timed_out_candidates")
            if isinstance(timed_out, list):
                outcome_timed_out_candidates.append(float(len(timed_out)))
            unvisited = outcome.get("unvisited_candidates")
            if isinstance(unvisited, list):
                outcome_unvisited_candidates.append(
                    float(len(unvisited))
                )

    cadence = [
        float(current - previous)
        for previous, current in zip(
            decision_frames,
            decision_frames[1:],
        )
        if 0 < current - previous < 120
    ]
    timing = {
        "read_ms": _summary(read_ms),
        "local_plan_ms": _summary(local_plan_ms),
        "previous_iteration_ms": _summary(previous_iteration_ms),
        "before_trace_ms": _summary(before_trace_ms),
        "corridor_bookkeeping_ms": _summary(
            corridor_bookkeeping_ms
        ),
        "action_lag_frames": _summary(action_lag),
        "decision_cadence_frames": _summary(cadence),
        "corridor_solve_ms": _summary(
            list(solve_by_policy.values())
        ),
        "clearance_ms": _summary(
            list(phase_by_policy["clearance"].values())
        ),
        "viability_ms": _summary(
            list(phase_by_policy["viability"].values())
        ),
        "first_observed_policy_age_frames": _summary(
            list(first_age_by_policy.values())
        ),
        "forecast_lead_frames": _summary(
            list(forecast_by_policy.values())
        ),
        "candidate_submit_ms": _summary(submit_ms),
        "candidate_lookup_ms": _summary(lookup_ms),
        "candidate_queue_ms": _summary(outcome_queue_ms),
        "candidate_elapsed_ms": _summary(outcome_elapsed_ms),
        "candidate_completed_count": _summary(
            outcome_completed_candidates
        ),
        "candidate_timed_out_count": _summary(
            outcome_timed_out_candidates
        ),
        "candidate_unvisited_count": _summary(
            outcome_unvisited_candidates
        ),
    }
    baseline = _baseline(baseline_dossier)
    comparison = None
    if baseline is not None:
        comparison = {
            name: _median_delta(timing[name], baseline.get(name))
            for name in (
                "read_ms",
                "local_plan_ms",
                "previous_iteration_ms",
                "before_trace_ms",
                "corridor_bookkeeping_ms",
                "action_lag_frames",
                "decision_cadence_frames",
                "corridor_solve_ms",
                "clearance_ms",
                "viability_ms",
                "first_observed_policy_age_frames",
                "forecast_lead_frames",
            )
        }
    return {
        "schema": "candidate-verifier-physical-shadow-audit-v1",
        "scope": {
            "trace": str(trace),
            "baseline_dossier": (
                str(baseline_dossier)
                if baseline_dossier is not None
                else None
            ),
            "authority": "shadow only",
            "delivery_contract": (
                "submit current exact root after Boolean publication and "
                "before local planning; issue-time lookup is nonblocking and "
                "requires exact policy-version/root equality"
            ),
        },
        "termination": termination,
        "counts": {
            "decisions": decision_count,
            "shadow_statuses": dict(statuses),
            "unique_outcomes": len(seen_outcomes),
            "outcome_statuses": dict(outcome_statuses),
            "background_priority_lowered_outcomes": (
                priority_lowered_count
            ),
            "policy_statuses": dict(policy_statuses),
        },
        "delivery": {
            "attempts": target_attempts,
            "exact_hits": exact_hits,
            "exact_hit_rate": (
                exact_hits / target_attempts if target_attempts else None
            ),
            "hit_winning_count": hit_winning,
            "hit_issued_in_best_count": hit_issued_best,
            "by_boolean_state": {
                name: {
                    "attempts": attempts_by_boolean[name],
                    "hits": hits_by_boolean[name],
                    "hit_rate": (
                        hits_by_boolean[name]
                        / attempts_by_boolean[name]
                        if attempts_by_boolean[name]
                        else None
                    ),
                    "winning_hits": winning_hits_by_boolean[name],
                }
                for name in ("viable", "losing", "unavailable")
            },
            "final_service": final_service,
        },
        "timing": timing,
        "baseline": baseline,
        "median_comparison": comparison,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--baseline-dossier", type=Path)
    args = parser.parse_args(argv)
    report = audit(
        args.trace,
        baseline_dossier=args.baseline_dossier,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
