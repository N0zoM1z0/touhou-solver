#!/usr/bin/env python3
"""Gate supplemental direct-root replay under four-worker viability load."""

from __future__ import annotations

import argparse
import hashlib
import heapq
import json
import math
import os
import platform
import random
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import th08_live_dodge_agent as live
from benchmarks.benchmark_preloss_continuation_reserve import _eligible
from benchmarks.benchmark_recovery_control_reserve import _replay_decision
from benchmarks.local_issue_contention_benchmark import (
    _BackgroundViability,
    _viability_problem,
)
from th08_live_dodge_agent import Item, recertify_action_for_fresh_hazards
from th08_trace_replay import (
    hazards_from_trace,
    local_pipeline_root_from_trace,
)
from touhou_control import native_backend


FRAME_MS = 1000.0 / 60.0
LOCAL_DELTA_P95_LIMIT_MS = 5.0
LOCAL_DELTA_MAX_LIMIT_MS = FRAME_MS
BACKGROUND_P95_RATIO_LIMIT = 1.10
BACKGROUND_THROUGHPUT_RATIO_FLOOR = 0.90

VARIANTS = (
    ("historical_idle", False, False),
    ("supplemental_idle", True, False),
    ("historical_workers4", False, True),
    ("supplemental_workers4", True, True),
)


@dataclass(frozen=True)
class Sample:
    trace: Path
    row: dict[str, object]
    next_hit_frame: int | None

    @property
    def key(self) -> str:
        return "|".join(
            (
                str(self.trace),
                str(int(self.row.get("gameplay_epoch", 0))),
                str(int(self.row["frame"])),
            )
        )


@dataclass(frozen=True)
class ReplayResult:
    decision: object
    recertified: object
    total_ms: float
    trace_reconstruction_ms: float
    root_parse_ms: float
    choose_ms: float
    recertify_ms: float


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)]


def _summary(values: list[float]) -> dict[str, float | int] | None:
    finite = [float(value) for value in values if math.isfinite(value)]
    if not finite:
        return None
    return {
        "count": len(finite),
        "median": statistics.median(finite),
        "p95": _p95(finite),
        "max": max(finite),
        "mean": statistics.fmean(finite),
    }


def _nested_float(
    row: dict[str, object],
    *path: str,
) -> float | None:
    value: object = row
    for key in path:
        if not isinstance(value, dict) or key not in value:
            return None
        value = value[key]
    try:
        converted = float(value)
    except (TypeError, ValueError):
        return None
    return converted if math.isfinite(converted) else None


def _reservoir_add(
    reservoir: list[Sample],
    *,
    sample: Sample,
    seen: int,
    limit: int,
    generator: random.Random,
) -> None:
    if limit <= 0:
        return
    if len(reservoir) < limit:
        reservoir.append(sample)
        return
    slot = generator.randrange(seen)
    if slot < limit:
        reservoir[slot] = sample


def _next_hit(
    hit_frames: dict[int, list[int]],
    epoch: int,
    frame: int,
) -> int | None:
    return next(
        (
            hit_frame
            for hit_frame in hit_frames.get(epoch, ())
            if hit_frame >= frame
        ),
        None,
    )


def _physical_summary(
    rows: list[dict[str, object]],
) -> dict[str, object]:
    fields = {
        "observe_ms": ("timing_ms", "observe"),
        "read_pools_ms": ("timing_ms", "read_pools"),
        "decode_pools_ms": ("timing_ms", "decode_pools"),
        "local_plan_initial_ms": ("timing_ms", "local_plan_initial"),
        "issue_path_to_input_ms": (
            "timing_ms",
            "issue_path_to_input",
        ),
        "input_ms": ("timing_ms", "input"),
        "observe_to_input_ms": ("timing_ms", "observe_to_input"),
        "action_lag_frames": ("action_lag",),
        "policy_age_frames": ("corridor", "age"),
        "viability_age_frames": ("corridor", "viability", "age"),
        "support_high_frames": ("deadline_guard", "support_high"),
        "post_capture_advance_frames": (
            "deadline_guard",
            "post_capture_advance",
        ),
    }
    return {
        "row_count": len(rows),
        "chain": {
            name: _summary(
                [
                    value
                    for row in rows
                    if (value := _nested_float(row, *path)) is not None
                ]
            )
            for name, path in fields.items()
        },
        "deadline_missed_count": sum(
            bool(row.get("deadline_guard", {}).get("missed"))
            for row in rows
        ),
        "worker_limit_four_count": sum(
            row.get("corridor", {}).get(
                "native_viability_worker_limit"
            )
            == 4
            for row in rows
        ),
        "worker_limit_applied_count": sum(
            row.get("corridor", {}).get(
                "native_viability_worker_limit_applied"
            )
            is True
            for row in rows
        ),
    }


def _hard_components(decision: object) -> tuple[int | float, ...]:
    return (
        decision.robust_collisions,
        max(-decision.robust_min_clearance, 0.0),
        decision.local_collisions,
        max(-decision.min_clearance, 0.0),
        decision.terminal_threat_collisions,
        max(-decision.terminal_threat_min_clearance, 0.0),
    )


def _finite_contract_checks(
    baseline: object,
    decision: object,
    recertified: object,
    *,
    safe_actions: set[str],
) -> dict[str, bool]:
    """Check the supplemental contract only where that lane is admissible."""

    active = bool(decision.preloss_continuation_preference_active)
    changed = decision.action != baseline.action
    issue_transaction = recertified.issue_recertification
    return {
        "historical_action_mismatch": bool(
            active
            and decision.preloss_historical_action != baseline.action
        ),
        "global_membership": bool(
            active and decision.action not in safe_actions
        ),
        "hard_component_regression": any(
            current > incumbent
            for current, incumbent in zip(
                _hard_components(decision),
                _hard_components(baseline),
            )
        ),
        "route_gate_regression": (
            decision.planned_route_gate_deficit
            > baseline.planned_route_gate_deficit
        ),
        "continuation_contract": bool(
            active
            and changed
            and (
                -decision.viability_repair_volume,
                decision.viability_control_reserve_deficit,
            )
            >= (
                -baseline.viability_repair_volume,
                baseline.viability_control_reserve_deficit,
            )
        ),
        "bomb": bool(
            baseline.bomb or decision.bomb or recertified.bomb
        ),
        "supplemental_failure": (
            decision.preloss_supplemental_failure is not None
        ),
        "issue_transaction_missing": issue_transaction is None,
        "issue_global_membership": bool(
            recertified.action not in safe_actions
            and not (
                issue_transaction.global_constraint_relaxed
                if issue_transaction is not None
                else False
            )
        ),
    }


def _deadline_proxy(
    *,
    recorded_observe_to_input_ms: float,
    compute_delta_ms: float,
    support_high: int,
    post_capture_advance: int,
) -> dict[str, object]:
    budget_ms = support_high * FRAME_MS
    historical_miss = recorded_observe_to_input_ms > budget_ms
    supplemental_estimate_ms = max(
        0.0,
        recorded_observe_to_input_ms + compute_delta_ms,
    )
    supplemental_miss = supplemental_estimate_ms > budget_ms
    added_frames = math.ceil(max(0.0, compute_delta_ms) / FRAME_MS)
    return {
        "recorded_observe_to_input_ms": recorded_observe_to_input_ms,
        "compute_delta_ms": compute_delta_ms,
        "supplemental_estimate_ms": supplemental_estimate_ms,
        "support_budget_ms": budget_ms,
        "historical_miss": historical_miss,
        "supplemental_miss": supplemental_miss,
        "new_miss": supplemental_miss and not historical_miss,
        "strict_added_frames": added_frames,
        "strict_worst_phase_miss": (
            post_capture_advance + added_frames > support_high
        ),
    }


def _evaluate_gate(
    *,
    violation_counts: dict[str, int],
    invalid_measured_root_count: int,
    worker_limit_applied: bool,
    workers4_deltas_ms: list[float],
    historical_background: dict[str, float],
    supplemental_background: dict[str, float],
    new_deadline_miss_count: int,
) -> dict[str, object]:
    reasons: list[str] = []
    nonzero = {
        name: count
        for name, count in violation_counts.items()
        if count
    }
    if nonzero:
        reasons.append(f"finite_contract_violations:{nonzero}")
    if invalid_measured_root_count:
        reasons.append(
            f"invalid_measured_roots:{invalid_measured_root_count}"
        )
    if not worker_limit_applied:
        reasons.append("worker_limit_four_not_applied")

    delta_p95 = _p95(workers4_deltas_ms) if workers4_deltas_ms else math.inf
    delta_max = max(workers4_deltas_ms) if workers4_deltas_ms else math.inf
    if delta_p95 > LOCAL_DELTA_P95_LIMIT_MS:
        reasons.append(f"workers4_delta_p95_ms:{delta_p95:.6f}")
    if delta_max >= LOCAL_DELTA_MAX_LIMIT_MS:
        reasons.append(f"workers4_delta_max_ms:{delta_max:.6f}")

    historical_p95 = historical_background.get("solve_p95_ms", 0.0)
    supplemental_p95 = supplemental_background.get("solve_p95_ms", 0.0)
    historical_throughput = historical_background.get(
        "solves_per_second",
        0.0,
    )
    supplemental_throughput = supplemental_background.get(
        "solves_per_second",
        0.0,
    )
    p95_ratio = (
        supplemental_p95 / historical_p95
        if historical_p95 > 0.0
        else math.inf
    )
    throughput_ratio = (
        supplemental_throughput / historical_throughput
        if historical_throughput > 0.0
        else 0.0
    )
    if p95_ratio > BACKGROUND_P95_RATIO_LIMIT:
        reasons.append(f"background_p95_ratio:{p95_ratio:.6f}")
    if throughput_ratio < BACKGROUND_THROUGHPUT_RATIO_FLOOR:
        reasons.append(
            f"background_throughput_ratio:{throughput_ratio:.6f}"
        )
    if new_deadline_miss_count:
        reasons.append(f"new_deadline_misses:{new_deadline_miss_count}")
    return {
        "passed": not reasons,
        "reasons": reasons,
        "thresholds": {
            "workers4_delta_p95_ms_max": LOCAL_DELTA_P95_LIMIT_MS,
            "workers4_delta_max_ms_exclusive": (
                LOCAL_DELTA_MAX_LIMIT_MS
            ),
            "background_solve_p95_ratio_max": (
                BACKGROUND_P95_RATIO_LIMIT
            ),
            "background_throughput_ratio_min": (
                BACKGROUND_THROUGHPUT_RATIO_FLOOR
            ),
            "new_deadline_miss_count_max": 0,
        },
        "observed": {
            "workers4_delta_p95_ms": delta_p95,
            "workers4_delta_max_ms": delta_max,
            "background_solve_p95_ratio": p95_ratio,
            "background_throughput_ratio": throughput_ratio,
            "new_deadline_miss_count": new_deadline_miss_count,
        },
    }


def _load_samples(
    traces: list[Path],
    *,
    broad_limit: int,
    prehit_limit: int,
    stress_limit: int,
    prehit_window: int,
) -> tuple[
    list[Sample],
    dict[str, object],
    list[dict[str, object]],
]:
    metadata: dict[Path, dict[str, object]] = {}
    for trace in traces:
        digest = hashlib.sha256()
        hit_frames: dict[int, list[int]] = {}
        with trace.open("rb") as source:
            for raw_line in source:
                digest.update(raw_line)
                row = json.loads(raw_line)
                if row.get("kind") == "decision" and row.get("hit_started"):
                    hit_frames.setdefault(
                        int(row.get("gameplay_epoch", 0)),
                        [],
                    ).append(int(row["frame"]))
        metadata[trace] = {
            "sha256": digest.hexdigest(),
            "hit_frames": hit_frames,
            "decision_count": 0,
            "eligible_count": 0,
            "valid_direct_root_count": 0,
            "invalid_direct_root_count": 0,
            "overdue_root_count": 0,
        }

    broad: list[Sample] = []
    prehit: list[Sample] = []
    stress: list[tuple[float, float, int, Sample]] = []
    broad_seen = 0
    prehit_seen = 0
    sequence = 0
    broad_generator = random.Random(0xCE0131)
    prehit_generator = random.Random(0xCE0132)
    all_valid_rows: list[dict[str, object]] = []
    for trace in traces:
        trace_meta = metadata[trace]
        hit_frames = trace_meta["hit_frames"]
        assert isinstance(hit_frames, dict)
        with trace.open(encoding="utf-8") as source:
            for line in source:
                row = json.loads(line)
                if row.get("kind") != "decision":
                    continue
                trace_meta["decision_count"] += 1
                if not _eligible(row):
                    continue
                player = row.get("player", {})
                deadline = row.get("deadline_guard", {})
                if (
                    not isinstance(player, dict)
                    or int(player.get("phase_at_action", 0)) == 2
                    or bool(row.get("bomb"))
                    or (
                        isinstance(deadline, dict)
                        and bool(deadline.get("input_suppressed"))
                    )
                ):
                    continue
                trace_meta["eligible_count"] += 1
                try:
                    _root, _held, _issue_age, overdue = (
                        local_pipeline_root_from_trace(row)
                    )
                except ValueError:
                    trace_meta["invalid_direct_root_count"] += 1
                    continue
                if overdue:
                    trace_meta["overdue_root_count"] += 1
                    continue
                trace_meta["valid_direct_root_count"] += 1
                all_valid_rows.append(row)

                epoch = int(row.get("gameplay_epoch", 0))
                frame = int(row["frame"])
                next_hit_frame = _next_hit(hit_frames, epoch, frame)
                sample = Sample(trace, row, next_hit_frame)
                broad_seen += 1
                _reservoir_add(
                    broad,
                    sample=sample,
                    seen=broad_seen,
                    limit=broad_limit,
                    generator=broad_generator,
                )
                if (
                    next_hit_frame is not None
                    and 0 <= next_hit_frame - frame <= prehit_window
                ):
                    prehit_seen += 1
                    _reservoir_add(
                        prehit,
                        sample=sample,
                        seen=prehit_seen,
                        limit=prehit_limit,
                        generator=prehit_generator,
                    )
                observe_to_input = _nested_float(
                    row,
                    "timing_ms",
                    "observe_to_input",
                )
                density = (
                    float(row.get("active_bullets", 0))
                    + 4.0 * len(row.get("lasers", ()))
                    + 4.0 * len(row.get("enemy_bodies", ()))
                )
                entry = (
                    observe_to_input
                    if observe_to_input is not None
                    else -1.0,
                    density,
                    sequence,
                    sample,
                )
                sequence += 1
                if stress_limit > 0:
                    if len(stress) < stress_limit:
                        heapq.heappush(stress, entry)
                    elif entry[:3] > stress[0][:3]:
                        heapq.heapreplace(stress, entry)

    selected: dict[str, dict[str, object]] = {}
    cohorts = {
        "broad": broad,
        "prehit": prehit,
        "stress": [entry[3] for entry in sorted(stress, reverse=True)],
    }
    for cohort, samples in cohorts.items():
        for sample in samples:
            selected.setdefault(
                sample.key,
                {"sample": sample, "cohorts": []},
            )["cohorts"].append(cohort)
    selected_samples = [
        record["sample"]
        for record in selected.values()
        if isinstance(record["sample"], Sample)
    ]
    selected_samples.sort(key=lambda sample: sample.key)
    selected_rows = [sample.row for sample in selected_samples]
    report = {
        "traces": [
            {
                "path": str(trace),
                **{
                    key: value
                    for key, value in metadata[trace].items()
                    if key != "hit_frames"
                },
                "hit_count": sum(
                    len(frames)
                    for frames in metadata[trace]["hit_frames"].values()
                ),
            }
            for trace in traces
        ],
        "cohort_requested": {
            "broad": broad_limit,
            "prehit": prehit_limit,
            "stress": stress_limit,
            "prehit_window": prehit_window,
        },
        "cohort_retained_before_dedup": {
            name: len(samples) for name, samples in cohorts.items()
        },
        "deduplicated_sample_count": len(selected_samples),
        "cohorts_by_root": {
            key: record["cohorts"] for key, record in selected.items()
        },
        "physical_all_valid_direct_roots": _physical_summary(
            all_valid_rows
        ),
        "physical_selected_roots": _physical_summary(selected_rows),
    }
    return selected_samples, report, all_valid_rows


def _run_one(sample: Sample, *, supplemental: bool) -> ReplayResult:
    row = sample.row
    total_started = time.perf_counter_ns()
    decode_started = time.perf_counter_ns()
    hazards = hazards_from_trace(row)
    items = tuple(Item(*values) for values in row.get("items", ()))
    trace_reconstruction_ms = (
        time.perf_counter_ns() - decode_started
    ) / 1_000_000.0

    root_started = time.perf_counter_ns()
    root, _held_mask, _issue_age, overdue = (
        local_pipeline_root_from_trace(row)
    )
    root_parse_ms = (
        time.perf_counter_ns() - root_started
    ) / 1_000_000.0
    if overdue:
        raise ValueError("measured direct root is overdue")

    choose_started = time.perf_counter_ns()
    decision = _replay_decision(
        row,
        recovery_control_reserve=True,
        preloss_continuation_preference=supplemental,
        preloss_supplemental_beam_width=4 if supplemental else 0,
        local_pipeline_root=root,
        replay_hazards=hazards,
        replay_items=items,
    )
    choose_ms = (
        time.perf_counter_ns() - choose_started
    ) / 1_000_000.0

    viability = row["corridor"]["viability"]
    recertify_started = time.perf_counter_ns()
    recertified = recertify_action_for_fresh_hazards(
        decision,
        player_x=float(row["player"]["x"]),
        player_y=float(row["player"]["y"]),
        previous_mask=int(row["input_snapshot"]["current"]),
        delay_frames=tuple(row["control_delay_candidates"]),
        action_hold_frames=int(row["action_hold_frames"]),
        bullets=hazards[0],
        lasers=hazards[1],
        enemy_bodies=hazards[2],
        snapshot_lag=int(row["snapshot_lag"]),
        pipeline_root=root,
        allowed_first_actions=tuple(viability["safe_actions"]),
        viability_repair_volumes=tuple(
            viability["repair_volumes"].items()
        ),
        viability_recovery_distances=tuple(
            viability["recovery_distances"].items()
        ),
    )
    recertify_ms = (
        time.perf_counter_ns() - recertify_started
    ) / 1_000_000.0
    return ReplayResult(
        decision=decision,
        recertified=recertified,
        total_ms=(time.perf_counter_ns() - total_started) / 1_000_000.0,
        trace_reconstruction_ms=trace_reconstruction_ms,
        root_parse_ms=root_parse_ms,
        choose_ms=choose_ms,
        recertify_ms=recertify_ms,
    )


def _background_start(
    problem: dict[str, object],
) -> tuple[
    _BackgroundViability,
    ThreadPoolExecutor,
    object,
]:
    background = _BackgroundViability(4, problem, low_priority=False)
    executor = ThreadPoolExecutor(
        max_workers=1,
        thread_name_prefix="direct-root-viability-4",
    )
    future = executor.submit(background.run)
    if not background.ready.wait(timeout=10.0):
        raise TimeoutError("four-worker viability parent did not start")
    deadline = time.monotonic() + 60.0
    while not background.solve_ms:
        if future.done():
            future.result()
        if time.monotonic() > deadline:
            raise TimeoutError("four-worker viability warm solve timed out")
        time.sleep(0.001)
    return background, executor, future


def _background_stop(
    background: _BackgroundViability,
    executor: ThreadPoolExecutor,
    future: object,
) -> None:
    background.stop.set()
    future.result(timeout=120.0)
    executor.shutdown(wait=True)


def _timing_segments(result: ReplayResult) -> dict[str, float]:
    timing = result.decision.local_certificate_timing
    issue = result.recertified.issue_certificate_timing
    return {
        "total_ms": result.total_ms,
        "trace_reconstruction_ms": result.trace_reconstruction_ms,
        "root_parse_ms": result.root_parse_ms,
        "choose_ms": result.choose_ms,
        "recertify_ms": result.recertify_ms,
        "shared_laser_projection_ms": timing.shared_laser_projection_ms,
        "control_prefix_ms": timing.control_prefix_ms,
        "planning_bullet_projection_ms": (
            timing.planning_bullet_projection_ms
        ),
        "certificate_total_ms": timing.certificate_total_ms,
        "beam_search_inclusive_ms": timing.beam_search_ms,
        "supplemental_beam_ms": timing.supplemental_beam_ms,
        "terminal_threat_ms": timing.terminal_threat_ms,
        "selection_finalize_ms": timing.selection_finalize_ms,
        "issue_certificate_total_ms": issue.certificate_total_ms,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("traces", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--broad-samples", type=int, default=128)
    parser.add_argument("--prehit-samples", type=int, default=64)
    parser.add_argument("--stress-samples", type=int, default=64)
    parser.add_argument("--prehit-window", type=int, default=300)
    parser.add_argument("--rounds", type=int, default=3)
    args = parser.parse_args(argv)
    if (
        args.broad_samples < 0
        or args.prehit_samples < 0
        or args.stress_samples < 0
        or args.prehit_window < 0
        or args.rounds <= 0
        or (
            args.broad_samples
            + args.prehit_samples
            + args.stress_samples
            <= 0
        )
    ):
        raise ValueError("invalid sample, window, or round count")
    if not native_backend.available():
        raise RuntimeError("native backend is unavailable")
    live._configure_local_hazard_backend("native")
    live._configure_local_beam_reducer("native")

    samples, selection_report, _all_rows = _load_samples(
        args.traces,
        broad_limit=args.broad_samples,
        prehit_limit=args.prehit_samples,
        stress_limit=args.stress_samples,
        prehit_window=args.prehit_window,
    )
    if not samples:
        raise RuntimeError("no valid direct roots were selected")

    # Load native code and caches outside every timed variant.
    _run_one(samples[0], supplemental=False)
    _run_one(samples[0], supplemental=True)

    problem = _viability_problem()
    results: dict[tuple[int, str, str], ReplayResult] = {}
    variant_reports: dict[str, dict[str, object]] = {
        name: {
            "supplemental": supplemental,
            "workers4": workers4,
            "timings": [],
            "background_solve_ms": [],
            "background_wall_seconds": 0.0,
            "background_process_seconds": 0.0,
            "worker_limit_applied": [],
            "priority_lowered": [],
            "preloss_active_count": 0,
            "issue_global_relaxation_count": 0,
        }
        for name, supplemental, workers4 in VARIANTS
    }
    round_orders: list[list[str]] = []
    for round_index in range(args.rounds):
        offset = round_index % len(VARIANTS)
        round_variants = VARIANTS[offset:] + VARIANTS[:offset]
        round_orders.append([variant[0] for variant in round_variants])
        for variant_index, (name, supplemental, workers4) in enumerate(
            round_variants
        ):
            background = None
            executor = None
            future = None
            solve_start = 0
            if workers4:
                background, executor, future = _background_start(problem)
                solve_start = len(background.solve_ms)
            wall_started = time.perf_counter()
            process_started = time.process_time()
            try:
                root_offset = (
                    round_index + variant_index
                ) % len(samples)
                root_order = samples[root_offset:] + samples[:root_offset]
                for sample in root_order:
                    result = _run_one(
                        sample,
                        supplemental=supplemental,
                    )
                    results[(round_index, name, sample.key)] = result
                    variant_reports[name]["timings"].append(
                        _timing_segments(result)
                    )
                    variant_reports[name]["preloss_active_count"] += bool(
                        result.decision
                        .preloss_continuation_preference_active
                    )
                    issue_transaction = (
                        result.recertified.issue_recertification
                    )
                    variant_reports[name][
                        "issue_global_relaxation_count"
                    ] += bool(
                        issue_transaction is not None
                        and issue_transaction.global_constraint_relaxed
                    )
            finally:
                if workers4:
                    assert (
                        background is not None
                        and executor is not None
                        and future is not None
                    )
                    _background_stop(background, executor, future)
                process_seconds = time.process_time() - process_started
                wall_seconds = time.perf_counter() - wall_started
                if workers4:
                    variant_reports[name]["background_solve_ms"].extend(
                        background.solve_ms[solve_start:]
                    )
                    variant_reports[name]["worker_limit_applied"].append(
                        background.worker_limit_applied
                    )
                    variant_reports[name]["priority_lowered"].append(
                        background.priority_lowered
                    )
                    variant_reports[name][
                        "background_wall_seconds"
                    ] += wall_seconds
                    variant_reports[name][
                        "background_process_seconds"
                    ] += process_seconds

    aggregate_variants: dict[str, object] = {}
    for name, _supplemental, workers4 in VARIANTS:
        raw = variant_reports[name]
        timings = raw["timings"]
        assert isinstance(timings, list)
        timing_names = tuple(timings[0])
        background_solve_ms = raw["background_solve_ms"]
        assert isinstance(background_solve_ms, list)
        background_wall = float(raw["background_wall_seconds"])
        background_process = float(raw["background_process_seconds"])
        aggregate_variants[name] = {
            "sample_count": len(timings),
            "preloss_active_count": raw["preloss_active_count"],
            "issue_global_relaxation_count": (
                raw["issue_global_relaxation_count"]
            ),
            "timing_ms": {
                timing_name: _summary(
                    [
                        float(timing[timing_name])
                        for timing in timings
                    ]
                )
                for timing_name in timing_names
            },
            "background_viability": (
                {
                    "solve_ms": _summary(background_solve_ms),
                    "solve_count": len(background_solve_ms),
                    "wall_seconds": background_wall,
                    "solves_per_second": (
                        len(background_solve_ms) / background_wall
                        if background_wall > 0.0
                        else 0.0
                    ),
                    "process_cpu_to_wall_ratio": (
                        background_process / background_wall
                        if background_wall > 0.0
                        else 0.0
                    ),
                    "worker_limit_applied_every_round": all(
                        raw["worker_limit_applied"]
                    ),
                    "priority_lowered_any_round": any(
                        raw["priority_lowered"]
                    ),
                }
                if workers4
                else None
            ),
        }

    violation_counts = {
        "historical_action_mismatch": 0,
        "global_membership": 0,
        "hard_component_regression": 0,
        "route_gate_regression": 0,
        "continuation_contract": 0,
        "bomb": 0,
        "supplemental_failure": 0,
        "issue_transaction_missing": 0,
        "issue_global_membership": 0,
    }
    failure_examples: list[dict[str, object]] = []
    action_change_count = 0
    recertified_action_change_count = 0
    paired_deltas: dict[str, list[float]] = {
        "idle": [],
        "workers4": [],
    }
    paired_component_deltas: dict[
        str,
        dict[str, list[float]],
    ] = {
        suffix: {
            name: []
            for name in (
                "total",
                "trace_reconstruction",
                "root_parse",
                "choose",
                "recertify",
                "supplemental_beam",
            )
        }
        for suffix in ("idle", "workers4")
    }
    workers4_delta_records: list[dict[str, object]] = []
    deadline_records: list[dict[str, object]] = []
    for round_index in range(args.rounds):
        for suffix in ("idle", "workers4"):
            historical_name = f"historical_{suffix}"
            supplemental_name = f"supplemental_{suffix}"
            for sample in samples:
                historical = results[
                    (round_index, historical_name, sample.key)
                ]
                candidate = results[
                    (round_index, supplemental_name, sample.key)
                ]
                baseline = historical.decision
                decision = candidate.decision
                changed = decision.action != baseline.action
                action_change_count += changed
                recertified_action_change_count += (
                    candidate.recertified.action != decision.action
                )
                safe_actions = set(
                    sample.row["corridor"]["viability"]["safe_actions"]
                )
                checks = _finite_contract_checks(
                    baseline,
                    decision,
                    candidate.recertified,
                    safe_actions=safe_actions,
                )
                for check, failed in checks.items():
                    violation_counts[check] += bool(failed)
                if any(checks.values()) and len(failure_examples) < 64:
                    failure_examples.append(
                        {
                            "round": round_index,
                            "contention": suffix,
                            "root": sample.key,
                            "checks": checks,
                            "historical_action": baseline.action,
                            "supplemental_action": decision.action,
                            "recertified_action": (
                                candidate.recertified.action
                            ),
                        }
                    )

                delta_ms = candidate.total_ms - historical.total_ms
                paired_deltas[suffix].append(delta_ms)
                component_values = {
                    "total": delta_ms,
                    "trace_reconstruction": (
                        candidate.trace_reconstruction_ms
                        - historical.trace_reconstruction_ms
                    ),
                    "root_parse": (
                        candidate.root_parse_ms - historical.root_parse_ms
                    ),
                    "choose": (
                        candidate.choose_ms - historical.choose_ms
                    ),
                    "recertify": (
                        candidate.recertify_ms
                        - historical.recertify_ms
                    ),
                    "supplemental_beam": (
                        decision.local_certificate_timing
                        .supplemental_beam_ms
                    ),
                }
                for component, value in component_values.items():
                    paired_component_deltas[suffix][component].append(
                        value
                    )
                if suffix == "workers4":
                    recorded = _nested_float(
                        sample.row,
                        "timing_ms",
                        "observe_to_input",
                    )
                    support_high = _nested_float(
                        sample.row,
                        "deadline_guard",
                        "support_high",
                    )
                    post_advance = _nested_float(
                        sample.row,
                        "deadline_guard",
                        "post_capture_advance",
                    )
                    if (
                        recorded is not None
                        and support_high is not None
                        and post_advance is not None
                    ):
                        deadline_records.append(
                            {
                                "round": round_index,
                                "root": sample.key,
                                **_deadline_proxy(
                                    recorded_observe_to_input_ms=recorded,
                                    compute_delta_ms=delta_ms,
                                    support_high=int(support_high),
                                    post_capture_advance=int(post_advance),
                                ),
                            }
                        )
                    workers4_delta_records.append(
                        {
                            "round": round_index,
                            "root": sample.key,
                            "cohorts": selection_report[
                                "cohorts_by_root"
                            ].get(sample.key, ()),
                            "supplemental_active": bool(
                                decision
                                .preloss_continuation_preference_active
                            ),
                            "active_bullets": int(
                                sample.row.get("active_bullets", 0)
                            ),
                            "laser_count": len(
                                sample.row.get("lasers", ())
                            ),
                            "recorded_observe_to_input_ms": recorded,
                            "support_high": support_high,
                            "post_capture_advance": post_advance,
                            "historical_action": baseline.action,
                            "supplemental_action": decision.action,
                            "recertified_action": (
                                candidate.recertified.action
                            ),
                            "delta_ms": component_values,
                            "historical_total_ms": historical.total_ms,
                            "supplemental_total_ms": candidate.total_ms,
                        }
                    )

    historical_background_report = aggregate_variants[
        "historical_workers4"
    ]["background_viability"]
    supplemental_background_report = aggregate_variants[
        "supplemental_workers4"
    ]["background_viability"]
    assert (
        isinstance(historical_background_report, dict)
        and isinstance(supplemental_background_report, dict)
    )
    historical_solve = historical_background_report["solve_ms"]
    supplemental_solve = supplemental_background_report["solve_ms"]
    assert isinstance(historical_solve, dict)
    assert isinstance(supplemental_solve, dict)
    gate = _evaluate_gate(
        violation_counts=violation_counts,
        invalid_measured_root_count=0,
        worker_limit_applied=bool(
            historical_background_report[
                "worker_limit_applied_every_round"
            ]
            and supplemental_background_report[
                "worker_limit_applied_every_round"
            ]
        ),
        workers4_deltas_ms=paired_deltas["workers4"],
        historical_background={
            "solve_p95_ms": float(historical_solve["p95"]),
            "solves_per_second": float(
                historical_background_report["solves_per_second"]
            ),
        },
        supplemental_background={
            "solve_p95_ms": float(supplemental_solve["p95"]),
            "solves_per_second": float(
                supplemental_background_report["solves_per_second"]
            ),
        },
        new_deadline_miss_count=sum(
            bool(record["new_miss"]) for record in deadline_records
        ),
    )
    report = {
        "schema": "th08-supplemental-direct-root-contention-gate-v1",
        "platform": platform.platform(),
        "python": platform.python_version(),
        "logical_cpu_count": os.cpu_count(),
        "native_library": str(native_backend._library_path()),
        "scope": {
            "physical": (
                "Retained game-process telemetry includes observe, "
                "ReadProcessMemory pool reads, raw decode, local plan, "
                "issue path, and SendInput."
            ),
            "replay": (
                "Windows rows are already parsed JSON. Measured trace-list "
                "reconstruction, explicit-root planning, and forced "
                "same-snapshot recertification are offline proxies, not "
                "pool decode or physical input issue."
            ),
            "hybrid_deadline": (
                "recorded physical observe_to_input plus paired Windows "
                "supplemental-minus-historical direct-root compute delta"
            ),
            "authority": "offline gate; no input injection or action authority",
        },
        "configuration": {
            "rounds": args.rounds,
            "supplemental_width": 4,
            "background_worker_limit": 4,
            "background_parent_priority": "normal",
            "rotating_variant_order": True,
            "rotating_root_order": True,
            "round_orders": round_orders,
            "viability_shape": list(problem["clearance_volume"].shape),
            "viability_action_count": len(problem["actions"]),
        },
        "selection": selection_report,
        "variants": aggregate_variants,
        "paired_compute_delta_ms": {
            name: _summary(values)
            for name, values in paired_deltas.items()
        },
        "paired_component_delta_ms": {
            suffix: {
                component: _summary(values)
                for component, values in components.items()
            }
            for suffix, components in paired_component_deltas.items()
        },
        "workers4_largest_delta_examples": sorted(
            workers4_delta_records,
            key=lambda record: float(record["delta_ms"]["total"]),
            reverse=True,
        )[:64],
        "finite_contract": {
            "comparison_count": (
                args.rounds * len(samples) * 2
            ),
            "action_change_count": action_change_count,
            "recertified_action_change_count": (
                recertified_action_change_count
            ),
            "violation_counts": violation_counts,
            "failure_examples": failure_examples,
        },
        "deadline_proxy": {
            "assumed_hz": 60,
            "record_count": len(deadline_records),
            "historical_miss_count": sum(
                bool(record["historical_miss"])
                for record in deadline_records
            ),
            "supplemental_miss_count": sum(
                bool(record["supplemental_miss"])
                for record in deadline_records
            ),
            "new_miss_count": sum(
                bool(record["new_miss"]) for record in deadline_records
            ),
            "strict_worst_phase_miss_count": sum(
                bool(record["strict_worst_phase_miss"])
                for record in deadline_records
            ),
            "estimate_ms": _summary(
                [
                    float(record["supplemental_estimate_ms"])
                    for record in deadline_records
                ]
            ),
            "new_miss_examples": [
                record
                for record in deadline_records
                if record["new_miss"]
            ][:64],
        },
        "gate": gate,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "sample_count": len(samples),
                "violation_counts": violation_counts,
                "workers4_delta_ms": report[
                    "paired_compute_delta_ms"
                ]["workers4"],
                "deadline_proxy": {
                    key: report["deadline_proxy"][key]
                    for key in (
                        "record_count",
                        "historical_miss_count",
                        "supplemental_miss_count",
                        "new_miss_count",
                        "strict_worst_phase_miss_count",
                    )
                },
                "gate": gate,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if gate["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
