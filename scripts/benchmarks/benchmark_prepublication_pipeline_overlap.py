#!/usr/bin/env python3
"""Measure clearance-time exact-root prewarm against Boolean induction.

The workload deliberately uses the retained TH08 lattice and delay/cadence
contracts.  It answers three separate questions:

* does background work change the published Boolean policy;
* is the predicted first exact root bit-for-bit equivalent to a cold query;
* how much Boolean delivery contention buys readiness before publication and
  before the retained 16-frame physical forecast lead expires.

This is an offline scheduling proxy.  Current-version hit rate and actual
policy lifetime require physical shadow telemetry.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import time
from pathlib import Path

from benchmarks.benchmark_augmented_pipeline_workspace import _results_equal
from benchmarks.benchmark_postpublished_survival import _structured_clearance
from th08_corridor_adapter import (
    TH08_CORRIDOR_CONFIG,
    TH08_VIABILITY_ACTIONS,
)
from touhou_control.pipeline_prewarm_service import PipelinePrewarmService
from touhou_control.query_survival import (
    ReachablePipelineRoot,
    SurvivalQueryProblem,
)
from touhou_control.viability import (
    ViabilityConfig,
    build_robust_viability_policy,
)


DELAY_SUPPORT = (1, 2, 3, 4, 5, 6)
DECISION_FRAME_SUPPORT = (4, 5, 6)
INITIAL_ROOT_FRAME = 4
RETAINED_MEDIAN_FORECAST_LEAD_FRAMES = 16
FRAME_MS = 1000.0 / 60.0


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[int(0.95 * (len(ordered) - 1))]


def _summary(values: list[float]) -> dict[str, float]:
    return {
        "median": statistics.median(values),
        "p95": _p95(values),
        "max": max(values),
    }


def benchmark(
    *,
    case_count: int,
    worker_counts: tuple[int, ...],
) -> dict[str, object]:
    config = ViabilityConfig(
        frames_per_layer=TH08_CORRIDOR_CONFIG.frames_per_layer,
        required_clearance=TH08_CORRIDOR_CONFIG.required_clearance,
        clamp_to_bounds=True,
        repair_radius_cells=1,
    )
    cases: list[dict[str, object]] = []
    parity_failures: list[dict[str, object]] = []
    timing_by_workers = {
        workers: {
            "boolean_ms": [],
            "slowdown_ratio": [],
            "service_ms": [],
            "seed_ms": [],
            "specialization_ms": [],
        }
        for workers in worker_counts
    }
    readiness_by_workers = {
        workers: {
            "ready_at_publication": 0,
            "ready_within_retained_lead": 0,
            "case_count": 0,
        }
        for workers in worker_counts
    }

    # Force lazy native initialization outside all measured cases.
    warm_x, warm_y, warm_clearance = _structured_clearance(1_000_003)
    build_robust_viability_policy(
        x_axis=warm_x,
        y_axis=warm_y,
        clearance_volume=warm_clearance,
        actions=TH08_VIABILITY_ACTIONS,
        delay_frames=DELAY_SUPPORT,
        nominal_delay=4,
        config=config,
    )

    for case_index in range(case_count):
        seed = 3 + case_index * 8
        x_axis, y_axis, clearance = _structured_clearance(seed)
        policy_arguments = {
            "x_axis": x_axis,
            "y_axis": y_axis,
            "clearance_volume": clearance,
            "actions": TH08_VIABILITY_ACTIONS,
            "delay_frames": DELAY_SUPPORT,
            "nominal_delay": 4,
            "config": config,
        }
        problem = SurvivalQueryProblem(**policy_arguments)
        root = ReachablePipelineRoot(
            frame=INITIAL_ROOT_FRAME,
            row=13 + case_index % 3,
            column=12 + case_index % 4,
            observed_action="stay",
            pending_command=None,
        )

        baseline_times = []
        baseline = None
        for _ in range(2):
            started = time.perf_counter()
            candidate = build_robust_viability_policy(**policy_arguments)
            baseline_times.append(
                (time.perf_counter() - started) * 1000.0
            )
            if baseline is None:
                baseline = candidate
            else:
                if not (
                    (baseline.viable == candidate.viable).all()
                    and (
                        baseline.safe_action_masks
                        == candidate.safe_action_masks
                    ).all()
                ):
                    parity_failures.append(
                        {
                            "seed": seed,
                            "workers": 0,
                            "reason": "baseline_nondeterminism",
                        }
                    )
        assert baseline is not None
        baseline_ms = statistics.median(baseline_times)

        validation_version = f"validation-{seed}"
        with problem.build_pipeline_workspace(
            policy_version=validation_version,
            decision_frame_support=DECISION_FRAME_SUPPORT,
        ) as validation:
            expected = validation.query_cell(
                policy_version=validation_version,
                frame=root.frame,
                row=root.row,
                column=root.column,
                observed_action=root.observed_action,
                pending_command=root.pending_command,
            )

        case_record: dict[str, object] = {
            "seed": seed,
            "baseline_boolean_ms": baseline_ms,
            "baseline_boolean_samples_ms": baseline_times,
            "workers": {},
        }
        for workers in worker_counts:
            service = PipelinePrewarmService(
                problem=problem,
                policy_version=(seed, workers),
                initial_roots=(root,),
                decision_frame_support=DECISION_FRAME_SUPPORT,
                worker_count=workers,
            )
            try:
                overlap_started = time.perf_counter()
                overlap_policy = build_robust_viability_policy(
                    **policy_arguments
                )
                overlap_boolean_ms = (
                    time.perf_counter() - overlap_started
                ) * 1000.0
                publication_snapshot = service.snapshot()
                ready_at_publication = (
                    publication_snapshot.latest_outcome is not None
                    and publication_snapshot.latest_outcome.status == "ready"
                    and not publication_snapshot.target_running
                    and not publication_snapshot.target_queued
                )
                idle = service.wait_until_idle(3.0)
                final_snapshot = service.snapshot()
                actual = service.lookup(root)
                outcome = final_snapshot.latest_outcome
                boolean_equal = (
                    (baseline.viable == overlap_policy.viable).all()
                    and (
                        baseline.safe_action_masks
                        == overlap_policy.safe_action_masks
                    ).all()
                )
                exact_equal = (
                    actual is not None
                    and _results_equal(actual, expected)
                    and actual.workspace_stats.new_state_count == 0
                )
                service_ms = (
                    outcome.elapsed_ms
                    if outcome is not None
                    else float("inf")
                )
                ready_within_lead = (
                    idle
                    and outcome is not None
                    and outcome.status == "ready"
                    and service_ms
                    <= (
                        RETAINED_MEDIAN_FORECAST_LEAD_FRAMES
                        * FRAME_MS
                    )
                )
                if not (
                    idle
                    and boolean_equal
                    and exact_equal
                    and outcome is not None
                    and outcome.status == "ready"
                ):
                    parity_failures.append(
                        {
                            "seed": seed,
                            "workers": workers,
                            "idle": idle,
                            "boolean_equal": bool(boolean_equal),
                            "exact_equal": bool(exact_equal),
                            "outcome": (
                                outcome.status
                                if outcome is not None
                                else None
                            ),
                        }
                    )
                worker_record = {
                    "boolean_ms": overlap_boolean_ms,
                    "boolean_slowdown_ratio": (
                        overlap_boolean_ms / baseline_ms
                    ),
                    "ready_at_publication": ready_at_publication,
                    "ready_within_retained_median_lead": ready_within_lead,
                    "idle": idle,
                    "boolean_equal": bool(boolean_equal),
                    "exact_equal": bool(exact_equal),
                    "lookup_hit": actual is not None,
                    "root_count": (
                        outcome.root_count
                        if outcome is not None
                        else None
                    ),
                    "seed_count": (
                        outcome.seed_count
                        if outcome is not None
                        else None
                    ),
                    "enumeration_ms": (
                        outcome.enumeration_ms
                        if outcome is not None
                        else None
                    ),
                    "seed_ms": (
                        outcome.seed_ms
                        if outcome is not None
                        else None
                    ),
                    "specialization_ms": (
                        outcome.specialization_ms
                        if outcome is not None
                        else None
                    ),
                    "service_ms": service_ms,
                    "service_status": (
                        outcome.status
                        if outcome is not None
                        else None
                    ),
                }
                case_record["workers"][str(workers)] = worker_record
                timings = timing_by_workers[workers]
                timings["boolean_ms"].append(overlap_boolean_ms)
                timings["slowdown_ratio"].append(
                    overlap_boolean_ms / baseline_ms
                )
                timings["service_ms"].append(service_ms)
                if outcome is not None:
                    timings["seed_ms"].append(outcome.seed_ms)
                    timings["specialization_ms"].append(
                        outcome.specialization_ms
                    )
                readiness = readiness_by_workers[workers]
                readiness["case_count"] += 1
                readiness["ready_at_publication"] += int(
                    ready_at_publication
                )
                readiness["ready_within_retained_lead"] += int(
                    ready_within_lead
                )
            finally:
                service.close()
        cases.append(case_record)

    worker_summaries = {}
    for workers in worker_counts:
        timings = timing_by_workers[workers]
        readiness = readiness_by_workers[workers]
        count = readiness["case_count"]
        worker_summaries[str(workers)] = {
            "boolean_ms": _summary(timings["boolean_ms"]),
            "boolean_slowdown_ratio": _summary(
                timings["slowdown_ratio"]
            ),
            "service_ms": _summary(timings["service_ms"]),
            "seed_ms": _summary(timings["seed_ms"]),
            "specialization_ms": _summary(
                timings["specialization_ms"]
            ),
            "ready_at_publication_count": (
                readiness["ready_at_publication"]
            ),
            "ready_at_publication_rate": (
                readiness["ready_at_publication"] / count
            ),
            "ready_within_retained_median_lead_count": (
                readiness["ready_within_retained_lead"]
            ),
            "ready_within_retained_median_lead_rate": (
                readiness["ready_within_retained_lead"] / count
            ),
        }

    return {
        "schema": "prepublication-pipeline-overlap-benchmark-v1",
        "scope": (
            "TH08 16px, 80-frame structured moving-hazard clearance; "
            "delay envelope 1..6; cadence envelope 4..6; one predicted "
            "frame-4 public root started immediately before Boolean "
            "viability induction."
        ),
        "limitation": (
            "Offline structured fields measure delivery contention and exact "
            "predicted-root parity. They do not estimate physical "
            "current-version hit rate or the player's source-epoch root."
        ),
        "cpu_count": os.cpu_count(),
        "case_count": case_count,
        "worker_counts": worker_counts,
        "retained_physical_proxy": {
            "median_forecast_lead_frames": (
                RETAINED_MEDIAN_FORECAST_LEAD_FRAMES
            ),
            "median_forecast_lead_ms_at_60hz": (
                RETAINED_MEDIAN_FORECAST_LEAD_FRAMES * FRAME_MS
            ),
            "source": (
                "stage5_20260725_125037_pending_pipeline compact audit"
            ),
        },
        "failure_count": len(parity_failures),
        "failures": parity_failures,
        "workers": worker_summaries,
        "cases": cases,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--cases", type=int, default=5)
    parser.add_argument(
        "--workers",
        type=int,
        nargs="+",
        default=(1, 2, 3),
    )
    args = parser.parse_args(argv)
    if args.cases <= 0:
        raise ValueError("case count must be positive")
    worker_counts = tuple(dict.fromkeys(args.workers))
    if not worker_counts or min(worker_counts) <= 0:
        raise ValueError("worker counts must be positive")
    report = benchmark(
        case_count=args.cases,
        worker_counts=worker_counts,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report["workers"], indent=2))
    print(f"failure_count={report['failure_count']}")
    return 1 if report["failure_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
