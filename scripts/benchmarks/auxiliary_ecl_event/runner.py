"""Timing runner and deadline gate for the fixed auxiliary-ECL workload."""

from __future__ import annotations

import gc
import hashlib
import json
import platform
import time
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any

from th08_ecl_auxiliary import (
    AuxiliaryLiteralFireRequest,
    lower_auxiliary_literal_fire_batch,
)

from .workload import (
    ACTIVE_DIFFICULTY_MASK,
    BenchmarkContext,
    load_fixture,
)


REPORT_SCHEMA = "th08-g5-auxiliary-ecl-event-benchmark-v1"
REPORT_AUTHORITY = "offline_timing_no_action_authority"
BATCH_WORKLOAD = "stage5_observed_mix_34_context"
P95_LIMIT_MS = 0.50
P99_LIMIT_MS = 1.00
MAX_LIMIT_MS = 3.00


def _percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("cannot summarize an empty timing sample")
    rank = (len(ordered) - 1) * percentile
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = rank - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _summary(values: list[float]) -> dict[str, float | int]:
    return {
        "count": len(values),
        "p50_ms": _percentile(values, 0.50),
        "p95_ms": _percentile(values, 0.95),
        "p99_ms": _percentile(values, 0.99),
        "max_ms": max(values),
    }


def _measure(
    callback: Callable[[], object],
    *,
    iterations: int,
    warmup: int,
) -> dict[str, object]:
    for _ in range(warmup):
        callback()
    samples: list[float] = []
    active_sample: int | None = None
    gc_overlap_samples: set[int] = set()
    gc_starts: Counter[int] = Counter()

    def observe_gc(phase: str, info: dict[str, int]) -> None:
        if active_sample is None:
            return
        gc_overlap_samples.add(active_sample)
        if phase == "start":
            gc_starts[info["generation"]] += 1

    gc.callbacks.append(observe_gc)
    try:
        for sample_index in range(iterations):
            active_sample = sample_index
            started = time.perf_counter_ns()
            callback()
            samples.append(
                (time.perf_counter_ns() - started) / 1_000_000.0
            )
            active_sample = None
    finally:
        active_sample = None
        gc.callbacks.remove(observe_gc)

    gc_samples = [
        sample
        for index, sample in enumerate(samples)
        if index in gc_overlap_samples
    ]
    non_gc_samples = [
        sample
        for index, sample in enumerate(samples)
        if index not in gc_overlap_samples
    ]
    return {
        **_summary(samples),
        "gc_overlap_sample_count": len(gc_overlap_samples),
        "gc_start_counts": {
            str(generation): count
            for generation, count in sorted(gc_starts.items())
        },
        "gc_overlap_max_ms": max(gc_samples) if gc_samples else None,
        "non_gc_max_ms": max(non_gc_samples) if non_gc_samples else None,
    }


def _lower(
    requests: tuple[AuxiliaryLiteralFireRequest, ...],
    instruction_at: Callable[[int], Any],
) -> object:
    return lower_auxiliary_literal_fire_batch(
        requests,
        instruction_at=instruction_at,
        active_difficulty_mask=ACTIVE_DIFFICULTY_MASK,
        time_scale=1.0,
    )


def _serialize(batch: object) -> bytes:
    return json.dumps(
        batch.compact_record(),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _workload_result(
    contexts: tuple[BenchmarkContext, ...],
    instruction_at: Callable[[int], Any],
    *,
    iterations: int,
    warmup: int,
) -> dict[str, object]:
    requests = tuple(
        AuxiliaryLiteralFireRequest(
            state=context.state,
            timer_tick_horizon=context.timer_tick_horizon,
        )
        for context in contexts
    )
    baseline = _lower(requests, instruction_at)
    if not all(result.horizon_covered for result in baseline.results):
        raise RuntimeError("fixed auxiliary benchmark failed to cover its horizon")
    serialized = _serialize(baseline)
    lower_timing = _measure(
        lambda: _lower(requests, instruction_at),
        iterations=iterations,
        warmup=warmup,
    )
    serialization_timing = _measure(
        lambda: _serialize(baseline),
        iterations=iterations,
        warmup=warmup,
    )
    end_to_end_timing = _measure(
        lambda: _serialize(_lower(requests, instruction_at)),
        iterations=iterations,
        warmup=warmup,
    )
    intent_count = sum(len(result.intents) for result in baseline.results)
    transform_count = sum(
        len(result.transform_definitions) for result in baseline.results
    )
    return {
        "context_count": len(contexts),
        "unique_result_count": len(baseline.unique_results),
        "intent_count": intent_count,
        "transform_definition_count": transform_count,
        "serialized_bytes": len(serialized),
        "serialized_sha256": hashlib.sha256(serialized).hexdigest(),
        "timing": {
            "lower": lower_timing,
            "serialization": serialization_timing,
            "lower_and_serialize": end_to_end_timing,
        },
    }


def run_benchmark(
    ecl_path: Path,
    *,
    iterations: int,
    warmup: int,
) -> dict[str, object]:
    if iterations <= 0:
        raise ValueError("iterations must be positive")
    if warmup < 0:
        raise ValueError("warmup cannot be negative")
    fixture = load_fixture(ecl_path)
    instruction_at = fixture.instruction_index.__getitem__
    workloads = {
        name: _workload_result(
            contexts,
            instruction_at,
            iterations=iterations,
            warmup=warmup,
        )
        for name, contexts in fixture.workloads.items()
    }
    batch_timing = workloads[BATCH_WORKLOAD]["timing"]["lower_and_serialize"]
    checks = {
        "p95": batch_timing["p95_ms"] <= P95_LIMIT_MS,
        "p99": batch_timing["p99_ms"] <= P99_LIMIT_MS,
        "max": batch_timing["max_ms"] <= MAX_LIMIT_MS,
    }
    return {
        "schema": REPORT_SCHEMA,
        "authority": REPORT_AUTHORITY,
        "platform": {
            "implementation": platform.python_implementation(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "system": platform.system(),
        },
        "fixture": {
            "ecl_path": str(ecl_path),
            "ecl_sha256": fixture.ecl_sha256,
            "identity_digest": fixture.identity_digest,
            "batch_workload": BATCH_WORKLOAD,
        },
        "configuration": {
            "iterations": iterations,
            "warmup": warmup,
            "time_scale": 1.0,
        },
        "workloads": workloads,
        "gate": {
            "metric": f"{BATCH_WORKLOAD}.timing.lower_and_serialize",
            "limits_ms": {
                "p95": P95_LIMIT_MS,
                "p99": P99_LIMIT_MS,
                "max": MAX_LIMIT_MS,
            },
            "checks": checks,
            "passed": all(checks.values()),
        },
    }


__all__ = [
    "BATCH_WORKLOAD",
    "MAX_LIMIT_MS",
    "P95_LIMIT_MS",
    "P99_LIMIT_MS",
    "REPORT_AUTHORITY",
    "REPORT_SCHEMA",
    "run_benchmark",
]
