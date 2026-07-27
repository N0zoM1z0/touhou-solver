"""Deterministic nearest-rank timing summaries."""

from __future__ import annotations

import math
import statistics
from collections import Counter

from .service import WitnessAttempt


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        raise ValueError("cannot summarize an empty timing sample")
    ordered = sorted(values)
    return ordered[max(0, math.ceil(fraction * len(ordered)) - 1)]


def timing_summary(values: list[float]) -> dict[str, float | int] | None:
    if not values:
        return None
    return {
        "count": len(values),
        "median_ms": statistics.median(values),
        "p95_ms": percentile(values, 0.95),
        "p99_ms": percentile(values, 0.99),
        "max_ms": max(values),
    }


def attempt_summary(
    attempts: list[WitnessAttempt],
) -> dict[str, object]:
    complete = [
        attempt for attempt in attempts if attempt.status == "complete"
    ]
    return {
        "job_count": len(attempts),
        "status_counts": dict(
            sorted(Counter(attempt.status for attempt in attempts).items())
        ),
        "completion_ratio": (
            len(complete) / len(attempts) if attempts else 0.0
        ),
        "complete_publication": timing_summary(
            [attempt.latency_ms for attempt in complete]
        ),
        "workspace_create": timing_summary(
            [attempt.workspace_create_ms for attempt in attempts]
        ),
        "native_query_decode": timing_summary(
            [attempt.native_query_decode_ms for attempt in attempts]
        ),
        "native_kernel": timing_summary(
            [attempt.native_kernel_ms for attempt in attempts]
        ),
        "decode": timing_summary(
            [attempt.decode_ms for attempt in attempts]
        ),
        "validation": timing_summary(
            [attempt.validation_ms for attempt in attempts]
        ),
        "workspace_destroy": timing_summary(
            [attempt.workspace_destroy_ms for attempt in attempts]
        ),
        "publication_lock_wait": timing_summary(
            [attempt.publication_lock_wait_ms for attempt in attempts]
        ),
        "evaluated_state_count": sum(
            attempt.evaluated_state_count for attempt in attempts
        ),
        "path_step_count": sum(
            attempt.path_step_count for attempt in attempts
        ),
        "scalar_path_tie_divergence_count": sum(
            attempt.scalar_path_tie_divergence_count
            for attempt in attempts
        ),
        "errors": [
            {
                "revision": attempt.revision,
                "identity": attempt.identity,
                "status": attempt.status,
                "error": attempt.error,
            }
            for attempt in attempts
            if attempt.status not in ("complete", "cancelled")
        ][:32],
    }


__all__ = ["attempt_summary", "percentile", "timing_summary"]
