#!/usr/bin/env python3
"""Summarize physical shadow evidence for prepublication exact-root prewarm."""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter, defaultdict
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
    counts: Counter[str] = Counter()
    statuses: Counter[str] = Counter()
    policy_statuses: Counter[str] = Counter()
    ordinal_statuses: dict[int, Counter[str]] = defaultdict(Counter)
    root_frame_statuses: dict[int, Counter[str]] = defaultdict(Counter)
    policy_query_count: Counter[int] = Counter()
    policy_first_age: dict[int, float] = {}
    policy_last_age: dict[int, float] = {}
    policy_first_shadow: dict[int, dict[str, object]] = {}
    policy_max_revision: Counter[int] = Counter()
    policy_max_completed: Counter[int] = Counter()
    policy_max_ready: Counter[int] = Counter()
    policy_max_replacements: Counter[int] = Counter()
    outcome_seen: set[tuple[int, int]] = set()
    outcome_statuses: Counter[str] = Counter()
    outcome_ms: list[float] = []
    seed_ms: list[float] = []
    specialization_ms: list[float] = []
    lookup_ms: list[float] = []
    retarget_ms: list[float] = []
    retarget_root_count: list[float] = []
    solve_by_policy: dict[int, float] = {}
    solver_phase_by_policy: dict[str, dict[int, float]] = defaultdict(dict)
    forecast_by_policy: dict[int, float] = {}
    read_ms: list[float] = []
    previous_iteration_ms: list[float] = []
    before_trace_ms: list[float] = []
    corridor_bookkeeping_ms: list[float] = []
    action_lag: list[float] = []
    decision_frames: list[int] = []
    termination: dict[str, object] | None = None

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
            counts["decisions"] += 1
            frame = row.get("frame")
            if isinstance(frame, int):
                decision_frames.append(frame)
            for raw, destination in (
                (row.get("read_ms"), read_ms),
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
            if not isinstance(corridor, dict):
                continue
            source_frame = corridor.get("source_frame")
            if not isinstance(source_frame, int):
                continue
            policy_status = corridor.get("policy_status")
            if isinstance(policy_status, str):
                policy_statuses[policy_status] += 1
            age = _number(corridor.get("age"))
            if age is not None:
                policy_first_age.setdefault(source_frame, age)
                policy_last_age[source_frame] = age
            value = _number(corridor.get("solve_ms"))
            if value is not None:
                solve_by_policy.setdefault(source_frame, value)
            value = _number(corridor.get("forecast_lead_frames"))
            if value is not None:
                forecast_by_policy.setdefault(source_frame, value)
            phases = corridor.get("solver_timing_ms")
            if isinstance(phases, dict):
                for phase, raw in phases.items():
                    value = _number(raw)
                    if value is not None:
                        solver_phase_by_policy[str(phase)].setdefault(
                            source_frame,
                            value,
                        )

            shadow = corridor.get("pipeline_prewarm_shadow")
            if not isinstance(shadow, dict):
                continue
            counts["shadow_rows"] += 1
            status = shadow.get("status")
            if not isinstance(status, str):
                status = "missing_status"
            statuses[status] += 1
            policy_first_shadow.setdefault(source_frame, shadow)
            value = _number(shadow.get("lookup_ms"))
            if value is not None:
                lookup_ms.append(value)
            if status in ("hit", "miss"):
                policy_query_count[source_frame] += 1
                ordinal = policy_query_count[source_frame]
                ordinal_statuses[ordinal][status] += 1
                root = shadow.get("root")
                if isinstance(root, dict):
                    root_frame = root.get("frame")
                    if isinstance(root_frame, int):
                        root_frame_statuses[root_frame][status] += 1
                counts["exact_attempts"] += 1
                counts["exact_hits"] += int(status == "hit")
            if shadow.get("start_error"):
                counts["start_errors"] += 1

            retarget = shadow.get("retarget")
            if isinstance(retarget, dict):
                retarget_status = retarget.get("status")
                if isinstance(retarget_status, str):
                    counts[f"retarget_{retarget_status}"] += 1
                value = _number(retarget.get("elapsed_ms"))
                if value is not None:
                    retarget_ms.append(value)
                value = _number(retarget.get("root_count"))
                if value is not None:
                    retarget_root_count.append(value)

            service = shadow.get("service")
            if not isinstance(service, dict):
                continue
            for name, target in (
                ("submitted_revision", policy_max_revision),
                ("completed_revision", policy_max_completed),
                ("ready_revision", policy_max_ready),
                (
                    "target_replacement_count",
                    policy_max_replacements,
                ),
            ):
                raw = service.get(name)
                if isinstance(raw, int):
                    target[source_frame] = max(
                        target[source_frame],
                        raw,
                    )
            outcome = service.get("latest_outcome")
            if not isinstance(outcome, dict):
                continue
            revision = outcome.get("revision")
            if not isinstance(revision, int):
                continue
            outcome_key = (source_frame, revision)
            if outcome_key in outcome_seen:
                continue
            outcome_seen.add(outcome_key)
            outcome_status = outcome.get("status")
            if isinstance(outcome_status, str):
                outcome_statuses[outcome_status] += 1
            for raw, destination in (
                (outcome.get("elapsed_ms"), outcome_ms),
                (outcome.get("seed_ms"), seed_ms),
                (
                    outcome.get("specialization_ms"),
                    specialization_ms,
                ),
            ):
                value = _number(raw)
                if value is not None:
                    destination.append(value)

    decision_cadence = [
        float(current - previous)
        for previous, current in zip(
            decision_frames,
            decision_frames[1:],
        )
        if 0 < current - previous < 120
    ]
    exact_attempts = counts["exact_attempts"]
    first_ready = 0
    first_hit = 0
    for shadow in policy_first_shadow.values():
        service = shadow.get("service")
        if isinstance(service, dict):
            outcome = service.get("latest_outcome")
            first_ready += int(
                isinstance(outcome, dict)
                and outcome.get("status") == "ready"
            )
        first_hit += int(shadow.get("status") == "hit")

    lifetime_decisions = [
        float(value) for value in policy_query_count.values()
    ]
    lifetime_age_span = [
        policy_last_age[source_frame] - first_age
        for source_frame, first_age in policy_first_age.items()
        if source_frame in policy_last_age
    ]
    ordinal_report = {}
    for ordinal in sorted(ordinal_statuses):
        counter = ordinal_statuses[ordinal]
        total = counter["hit"] + counter["miss"]
        ordinal_report[str(ordinal)] = {
            "attempts": total,
            "hits": counter["hit"],
            "hit_rate": counter["hit"] / total,
        }
    root_frame_report = {}
    for frame in sorted(root_frame_statuses):
        counter = root_frame_statuses[frame]
        total = counter["hit"] + counter["miss"]
        root_frame_report[str(frame)] = {
            "attempts": total,
            "hits": counter["hit"],
            "hit_rate": counter["hit"] / total,
        }

    timing = {
        "read_ms": _summary(read_ms),
        "previous_iteration_ms": _summary(previous_iteration_ms),
        "before_trace_ms": _summary(before_trace_ms),
        "corridor_bookkeeping_ms": _summary(
            corridor_bookkeeping_ms
        ),
        "action_lag_frames": _summary(action_lag),
        "decision_cadence_frames": _summary(decision_cadence),
        "corridor_solve_ms": _summary(list(solve_by_policy.values())),
        "forecast_lead_frames": _summary(
            list(forecast_by_policy.values())
        ),
        "first_observed_policy_age_frames": _summary(
            list(policy_first_age.values())
        ),
        "lookup_ms": _summary(lookup_ms),
        "retarget_ms": _summary(retarget_ms),
        "retarget_root_count": _summary(retarget_root_count),
        "target_outcome_ms": _summary(outcome_ms),
        "target_seed_ms": _summary(seed_ms),
        "target_specialization_ms": _summary(specialization_ms),
        "solver_phase_ms": {
            phase: _summary(list(values.values()))
            for phase, values in sorted(solver_phase_by_policy.items())
        },
    }
    baseline = _baseline(baseline_dossier)
    comparison = None
    if baseline is not None:
        comparison = {
            name: _median_delta(timing[name], baseline.get(name))
            for name in (
                "read_ms",
                "previous_iteration_ms",
                "before_trace_ms",
                "corridor_bookkeeping_ms",
                "action_lag_frames",
                "corridor_solve_ms",
                "forecast_lead_frames",
                "first_observed_policy_age_frames",
                "decision_cadence_frames",
            )
        }
        for phase in ("clearance", "viability"):
            comparison[f"{phase}_ms"] = _median_delta(
                timing["solver_phase_ms"].get(phase, _summary([])),
                baseline.get(f"{phase}_ms"),
            )

    policy_count = len(policy_first_shadow)
    return {
        "schema": "pipeline-prewarm-physical-shadow-audit-v1",
        "scope": {
            "trace": str(trace),
            "baseline_dossier": (
                str(baseline_dossier)
                if baseline_dossier is not None
                else None
            ),
            "semantics": (
                "Lookup is exact on policy version, frame, lattice cell, "
                "observed action, pending action, and remaining-delay set. "
                "Every miss retained Boolean plus a fresh local hard "
                "certificate; shadow labels never controlled input."
            ),
        },
        "termination": termination,
        "counts": {
            **dict(counts),
            "unique_shadow_policy_count": policy_count,
            "unique_target_outcome_count": len(outcome_seen),
            "status_counts": dict(statuses),
            "policy_status_counts": dict(policy_statuses),
            "target_outcome_status_counts": dict(outcome_statuses),
        },
        "hit_rate": {
            "attempts": exact_attempts,
            "hits": counts["exact_hits"],
            "rate": (
                counts["exact_hits"] / exact_attempts
                if exact_attempts
                else None
            ),
            "first_observation_policy_count": policy_count,
            "ready_at_first_observation_count": first_ready,
            "ready_at_first_observation_rate": (
                first_ready / policy_count if policy_count else None
            ),
            "hit_at_first_observation_count": first_hit,
            "hit_at_first_observation_rate": (
                first_hit / policy_count if policy_count else None
            ),
            "by_decision_ordinal_within_policy": ordinal_report,
            "by_exact_root_frame": root_frame_report,
        },
        "policy_lifetime": {
            "query_decisions": _summary(lifetime_decisions),
            "observed_age_span_frames": _summary(lifetime_age_span),
        },
        "rolling": {
            "max_submitted_revision": _summary(
                [float(value) for value in policy_max_revision.values()]
            ),
            "max_completed_revision": _summary(
                [float(value) for value in policy_max_completed.values()]
            ),
            "max_ready_revision": _summary(
                [float(value) for value in policy_max_ready.values()]
            ),
            "target_replacements": _summary(
                [
                    float(value)
                    for value in policy_max_replacements.values()
                ]
            ),
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
    print(json.dumps(report["hit_rate"], indent=2))
    print(json.dumps(report["median_comparison"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
