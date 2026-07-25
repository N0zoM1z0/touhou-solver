#!/usr/bin/env python3
"""Benchmark full versus physically ranked bounded rolling root targets."""

from __future__ import annotations

import argparse
import json
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
from touhou_control.pipeline_root_schedule import (
    schedule_pipeline_frontier,
)
from touhou_control.query_survival import (
    ReachablePipelineRoot,
    SurvivalQueryProblem,
)
from touhou_control.viability import ViabilityConfig


VALUE_CADENCE = (4, 5, 6)
SCHEDULING_CADENCE = (2, 3, 4, 5, 6, 7, 8, 9)
DELAY_SUPPORT = (1, 2, 3, 4, 5, 6)


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[int(0.95 * (len(ordered) - 1))]


def _summary(values: list[float]) -> dict[str, float]:
    return {
        "median": statistics.median(values),
        "p95": _p95(values),
        "max": max(values),
    }


def benchmark(case_count: int) -> dict[str, object]:
    config = ViabilityConfig(
        frames_per_layer=TH08_CORRIDOR_CONFIG.frames_per_layer,
        required_clearance=TH08_CORRIDOR_CONFIG.required_clearance,
        clamp_to_bounds=True,
        repair_radius_cells=1,
    )
    timings = {
        mode: {
            "target_ms": [],
            "seed_ms": [],
            "specialization_ms": [],
            "root_count": [],
            "seed_count": [],
        }
        for mode in ("full_physical_frontier", "bounded_top_2")
    }
    failures: list[dict[str, object]] = []
    cases = []
    for case_index in range(case_count):
        seed = 3 + case_index * 8
        x_axis, y_axis, clearance = _structured_clearance(seed)
        problem = SurvivalQueryProblem(
            x_axis=x_axis,
            y_axis=y_axis,
            clearance_volume=clearance,
            actions=TH08_VIABILITY_ACTIONS,
            delay_frames=DELAY_SUPPORT,
            nominal_delay=4,
            config=config,
        )
        initial = ReachablePipelineRoot(
            frame=4,
            row=13 + case_index % 3,
            column=12 + case_index % 4,
            observed_action="stay",
            pending_command=None,
        )
        physical_x = float(problem.x_axis[initial.column]) + 5.5
        physical_y = float(problem.y_axis[initial.row]) - 3.0
        schedule_started = time.perf_counter()
        schedule = schedule_pipeline_frontier(
            problem=problem,
            root=initial,
            selected_action="down_right_fast",
            physical_x=physical_x,
            physical_y=physical_y,
            command_issue_offset=2,
            preferred_decision_frame=4,
            scheduling_frame_support=SCHEDULING_CADENCE,
            root_limit=2,
        )
        schedule_ms = (time.perf_counter() - schedule_started) * 1000.0
        case_record = {
            "seed": seed,
            "schedule_ms": schedule_ms,
            "candidate_root_count": schedule.candidate_count,
            "scheduled_root_count": len(schedule.roots),
            "modes": {},
        }
        expected = {}
        for root_index, root in enumerate(schedule.roots):
            version = f"oracle-{seed}-{root_index}"
            with problem.build_pipeline_workspace(
                policy_version=version,
                decision_frame_support=VALUE_CADENCE,
            ) as workspace:
                expected[root] = workspace.query_cell(
                    policy_version=version,
                    frame=root.frame,
                    row=root.row,
                    column=root.column,
                    observed_action=root.observed_action,
                    pending_command=root.pending_command,
                )

        for mode, targets in (
            ("full_physical_frontier", schedule.candidates),
            ("bounded_top_2", schedule.roots),
        ):
            service = PipelinePrewarmService(
                problem=problem,
                policy_version=(seed, mode),
                initial_roots=(initial,),
                decision_frame_support=VALUE_CADENCE,
                worker_count=3,
                background_low_priority=True,
            )
            try:
                if not service.wait_until_idle(3.0):
                    failures.append(
                        {
                            "seed": seed,
                            "mode": mode,
                            "reason": "initial_timeout",
                        }
                    )
                    continue
                revision = service.retarget(targets)
                idle = service.wait_until_idle(3.0)
                outcomes = service.outcomes()
                outcome = next(
                    (
                        item
                        for item in outcomes
                        if item.revision == revision
                    ),
                    None,
                )
                lookup_hits = sum(
                    service.lookup(root) is not None for root in targets
                )
                parity = True
                if mode == "bounded_top_2":
                    for root in targets:
                        actual = service.lookup(root)
                        parity = (
                            parity
                            and actual is not None
                            and _results_equal(actual, expected[root])
                            and actual.workspace_stats.new_state_count == 0
                        )
                passed = (
                    idle
                    and outcome is not None
                    and outcome.status == "ready"
                    and lookup_hits == len(targets)
                    and parity
                )
                if not passed:
                    failures.append(
                        {
                            "seed": seed,
                            "mode": mode,
                            "idle": idle,
                            "outcome": (
                                outcome.status
                                if outcome is not None
                                else None
                            ),
                            "lookup_hits": lookup_hits,
                            "target_count": len(targets),
                            "parity": parity,
                        }
                    )
                assert outcome is not None
                record = {
                    "revision": revision,
                    "status": outcome.status,
                    "root_count": outcome.root_count,
                    "seed_count": outcome.seed_count,
                    "target_ms": outcome.elapsed_ms,
                    "seed_ms": outcome.seed_ms,
                    "specialization_ms": outcome.specialization_ms,
                    "lookup_hits": lookup_hits,
                    "parity": parity,
                }
                case_record["modes"][mode] = record
                values = timings[mode]
                values["target_ms"].append(outcome.elapsed_ms)
                values["seed_ms"].append(outcome.seed_ms)
                values["specialization_ms"].append(
                    outcome.specialization_ms
                )
                values["root_count"].append(float(outcome.root_count))
                values["seed_count"].append(float(outcome.seed_count))
            finally:
                service.close()
        cases.append(case_record)

    summaries = {
        mode: {
            name: _summary(values)
            for name, values in measurements.items()
        }
        for mode, measurements in timings.items()
    }
    full_median = summaries["full_physical_frontier"]["target_ms"][
        "median"
    ]
    bounded_median = summaries["bounded_top_2"]["target_ms"]["median"]
    return {
        "schema": "bounded-pipeline-root-schedule-benchmark-v1",
        "scope": (
            "TH08 structured 16px/80-frame problems. Both modes reuse the "
            "same completed frame-4 seed generation. The full mode schedules "
            "every physically reachable 2..9-frame root; bounded mode "
            "schedules the top two using subcell position, a two-frame issue "
            "offset, four-frame cadence, and one-frame nominal pickup."
        ),
        "case_count": case_count,
        "failure_count": len(failures),
        "failures": failures,
        "timing": summaries,
        "bounded_target_median_ratio": bounded_median / full_median,
        "cases": cases,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--cases", type=int, default=5)
    args = parser.parse_args(argv)
    if args.cases <= 0:
        raise ValueError("case count must be positive")
    report = benchmark(args.cases)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report["timing"], indent=2))
    print(
        f"bounded_target_median_ratio="
        f"{report['bounded_target_median_ratio']:.3f}"
    )
    print(f"failure_count={report['failure_count']}")
    return 1 if report["failure_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
