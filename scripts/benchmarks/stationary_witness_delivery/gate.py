"""Fixed pass/fail evaluation for the 2026-07-28 delivery contract."""

from __future__ import annotations

import math
from typing import Mapping


def _nested(record: Mapping[str, object], *path: str) -> object:
    value: object = record
    for name in path:
        if not isinstance(value, Mapping):
            raise ValueError(f"report path is not a mapping: {path}")
        value = value[name]
    return value


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _float(
    record: Mapping[str, object],
    name: str,
    *,
    default: float,
) -> float:
    value = record.get(name)
    return (
        float(value)
        if isinstance(value, (int, float)) and not isinstance(value, bool)
        else default
    )


def evaluate_gate(
    *,
    preparation: Mapping[str, object],
    measurements: Mapping[str, object],
    abi: Mapping[str, object],
    authoritative_windows_run: bool,
) -> dict[str, object]:
    idle = _nested(measurements, "idle")
    workers = _nested(measurements, "workers4")
    control = _nested(measurements, "workers4_idle_witness_control")
    cancellation = _nested(measurements, "rapid_replacement")
    assert isinstance(idle, Mapping)
    assert isinstance(workers, Mapping)
    assert isinstance(control, Mapping)
    assert isinstance(cancellation, Mapping)
    workers_complete = _mapping(workers.get("complete_publication"))
    worker_background = _mapping(workers.get("background_viability"))
    worker_solve = _mapping(worker_background.get("solve"))
    control_solve = _mapping(control.get("solve"))
    cancel_ack = _mapping(cancellation.get("cancellation_ack"))
    control_p95 = _float(control_solve, "p95_ms", default=0.0)
    control_throughput = _float(
        control,
        "throughput_per_second",
        default=0.0,
    )
    worker_p95_ratio = (
        _float(worker_solve, "p95_ms", default=float("inf"))
        / control_p95
        if control_p95 > 0.0
        else float("inf")
    )
    worker_throughput_ratio = (
        _float(
            worker_background,
            "throughput_per_second",
            default=0.0,
        )
        / control_throughput
        if control_throughput > 0.0
        else 0.0
    )

    conditions = {
        "authoritative_windows_run": authoritative_windows_run,
        "fixed_18_root_reservoir_complete": (
            int(preparation["selected_root_count"]) == 18
        ),
        "idle_oracle_and_path_validation_complete": (
            float(idle["completion_ratio"]) == 1.0
            and int(idle["partial_publication_count"]) == 0
            and not idle["errors"]
        ),
        "workers4_completion_ratio_at_least_0_95": (
            float(workers["completion_ratio"]) >= 0.95
        ),
        "workers4_publication_p95_at_most_8_ms": (
            _float(
                workers_complete,
                "p95_ms",
                default=float("inf"),
            )
            <= 8.0
        ),
        "workers4_publication_max_below_one_frame": (
            _float(
                workers_complete,
                "max_ms",
                default=float("inf"),
            )
            < (1000.0 / 60.0)
        ),
        "workers4_lookup_exact_and_no_partial": (
            int(workers["lookup_failure_count"]) == 0
            and int(workers["partial_publication_count"]) == 0
        ),
        "authoritative_worker_limit_four_applied": bool(
            worker_background["worker_limit_applied"]
        ),
        "authoritative_background_remains_normal_priority": (
            not bool(worker_background["priority_lowered"])
        ),
        "optional_worker_below_normal": bool(
            workers["worker_priority_lowered"]
        ),
        "optional_worker_affinity_applied": bool(
            workers.get("worker_affinity_applied")
        ),
        "active_cancellation_observed": (
            int(cancellation["active_cancellation_count"]) >= 1
        ),
        "cancellation_ack_p95_at_most_2_ms": (
            _float(cancel_ack, "p95_ms", default=float("inf")) <= 2.0
        ),
        "cancellation_ack_max_at_most_5_ms": (
            _float(cancel_ack, "max_ms", default=float("inf")) <= 5.0
        ),
        "rapid_replacement_zero_stale_or_partial": (
            int(cancellation["stale_lookup_count"]) == 0
            and int(cancellation["partial_publication_count"]) == 0
        ),
        "viability_p95_ratio_at_most_1_10": worker_p95_ratio <= 1.10,
        "viability_throughput_ratio_at_least_0_90": (
            worker_throughput_ratio >= 0.90
        ),
        "production_abi_unchanged": bool(abi["passed"]),
    }
    return {
        "passed": all(conditions.values()),
        "conditions": conditions,
        "derived": {
            "viability_p95_ratio": (
                worker_p95_ratio
                if math.isfinite(worker_p95_ratio)
                else None
            ),
            "viability_throughput_ratio": worker_throughput_ratio,
        },
        "authority": (
            "offline delivery gate only; physical action authority remains none"
        ),
    }


__all__ = ["evaluate_gate"]
