"""Idle, contention, and rapid-replacement delivery measurements."""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from benchmarks.local_issue_contention_benchmark import (
    _BackgroundViability,
    _viability_problem,
)
from touhou_control.background_priority import preferred_performance_cpu

from .metrics import attempt_summary, timing_summary
from .native import NativeStationaryWitnessLibrary
from .service import NewestWitnessService, WitnessAttempt
from .workload import PreparedPhysicalReservoir


@dataclass
class _BackgroundSession:
    background: _BackgroundViability
    executor: ThreadPoolExecutor
    future: object

    @classmethod
    def start(cls) -> "_BackgroundSession":
        background = _BackgroundViability(
            4,
            _viability_problem(),
            low_priority=False,
        )
        executor = ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix="authoritative-viability-4",
        )
        future = executor.submit(background.run)
        if not background.ready.wait(timeout=10.0):
            raise TimeoutError("four-worker viability load did not start")
        while not background.solve_ms:
            if future.done():
                future.result()
            time.sleep(0.001)
        return cls(background, executor, future)

    def stop(self) -> None:
        self.background.stop.set()
        self.future.result(timeout=60.0)
        self.executor.shutdown(wait=True)

    def completed_between(
        self,
        started: float,
        finished: float,
    ) -> list[float]:
        return [
            (end - begin) * 1000.0
            for begin, end in self.background.solve_intervals
            if begin >= started and end <= finished
        ]


def _rotated_workloads(
    reservoir: PreparedPhysicalReservoir,
    round_index: int,
) -> tuple[object, ...]:
    workloads = reservoir.workloads
    offset = round_index % len(workloads)
    return workloads[offset:] + workloads[:offset]


def _per_root_attempts(
    reservoir: PreparedPhysicalReservoir,
    attempts: list[WitnessAttempt],
) -> list[dict[str, object]]:
    by_identity: dict[str, list[WitnessAttempt]] = {}
    for attempt in attempts:
        by_identity.setdefault(attempt.identity, []).append(attempt)
    return [
        {
            "identity": workload.identity,
            "decision_frame": workload.root.decision_frame,
            "query_frame": workload.root.query_frame,
            **attempt_summary(by_identity.get(workload.identity, [])),
        }
        for workload in reservoir.workloads
    ]


def run_delivery_variant(
    *,
    reservoir: PreparedPhysicalReservoir,
    library: NativeStationaryWitnessLibrary,
    minimum_rounds: int,
    background: _BackgroundSession | None,
    minimum_background_solves: int = 0,
    affinity_cpu: int | None = None,
) -> tuple[dict[str, object], float]:
    service = NewestWitnessService(
        library=library,
        affinity_cpu=affinity_cpu,
    )
    attempts: list[WitnessAttempt] = []
    lookup_failure_count = 0
    partial_publication_count = 0
    previous_identity: str | None = None
    measurement_started = time.perf_counter()
    background_start_index = (
        len(background.background.solve_intervals)
        if background is not None
        else 0
    )
    rounds = 0
    try:
        while True:
            for workload in _rotated_workloads(reservoir, rounds):
                revision = service.submit(workload)
                if (
                    previous_identity is not None
                    and service.lookup(previous_identity) is not None
                ):
                    lookup_failure_count += 1
                attempt = service.wait_for_attempt(revision, timeout=30.0)
                attempts.append(attempt)
                publication = service.lookup(workload.identity)
                if attempt.status == "complete":
                    if publication is None:
                        lookup_failure_count += 1
                    elif len(publication.actions) != 36:
                        partial_publication_count += 1
                elif publication is not None:
                    partial_publication_count += 1
                if service.lookup(workload.identity + "-altered") is not None:
                    lookup_failure_count += 1
                if service.lookup("missing-identity") is not None:
                    lookup_failure_count += 1
                previous_identity = workload.identity
            rounds += 1
            completed_background = (
                0
                if background is None
                else sum(
                    begin >= measurement_started
                    for begin, _end in (
                        background.background.solve_intervals[
                            background_start_index:
                        ]
                    )
                )
            )
            if (
                rounds >= minimum_rounds
                and completed_background >= minimum_background_solves
            ):
                break
            if rounds >= 256:
                raise TimeoutError(
                    "contention run did not collect enough viability solves"
                )
    finally:
        service.close()
    measurement_finished = time.perf_counter()
    elapsed = measurement_finished - measurement_started
    background_values = (
        []
        if background is None
        else background.completed_between(
            measurement_started,
            measurement_finished,
        )
    )
    return (
        {
            **attempt_summary(attempts),
            "round_count": rounds,
            "root_count": len(reservoir.workloads),
            "lookup_failure_count": lookup_failure_count,
            "partial_publication_count": partial_publication_count,
            "worker_priority_lowered": service.priority_lowered,
            "worker_affinity_cpu": service.affinity_cpu,
            "worker_affinity_applied": service.affinity_applied,
            "measurement_seconds": elapsed,
            "per_root": _per_root_attempts(reservoir, attempts),
            "background_viability": (
                None
                if background is None
                else {
                    "worker_limit": 4,
                    "worker_limit_applied": (
                        background.background.worker_limit_applied
                    ),
                    "priority_lowered": (
                        background.background.priority_lowered
                    ),
                    "solve": timing_summary(background_values),
                    "throughput_per_second": (
                        len(background_values) / elapsed
                    ),
                }
            ),
        },
        elapsed,
    )


def run_background_control(duration_seconds: float) -> dict[str, object]:
    session = _BackgroundSession.start()
    started = time.perf_counter()
    try:
        time.sleep(duration_seconds)
    finally:
        finished = time.perf_counter()
        session.stop()
    values = session.completed_between(started, finished)
    elapsed = finished - started
    return {
        "worker_limit": 4,
        "worker_limit_applied": session.background.worker_limit_applied,
        "priority_lowered": session.background.priority_lowered,
        "measurement_seconds": elapsed,
        "solve": timing_summary(values),
        "throughput_per_second": len(values) / elapsed,
    }


def run_rapid_replacement(
    *,
    reservoir: PreparedPhysicalReservoir,
    library: NativeStationaryWitnessLibrary,
    pair_count: int = 64,
    affinity_cpu: int | None = None,
) -> dict[str, object]:
    service = NewestWitnessService(
        library=library,
        affinity_cpu=affinity_cpu,
    )
    old_attempts: list[WitnessAttempt] = []
    new_attempts: list[WitnessAttempt] = []
    active_workspace_miss_count = 0
    stale_lookup_count = 0
    partial_publication_count = 0
    try:
        for index in range(pair_count):
            old = reservoir.workloads[index % len(reservoir.workloads)]
            newer = reservoir.workloads[
                (index + 1) % len(reservoir.workloads)
            ]
            old_revision = service.submit(old)
            if not service.wait_until_workspace_active(
                old_revision,
                timeout=5.0,
            ):
                active_workspace_miss_count += 1
            new_revision = service.submit(newer)
            if service.lookup(old.identity) is not None:
                stale_lookup_count += 1
            old_attempt = service.wait_for_attempt(
                old_revision,
                timeout=30.0,
            )
            if service.lookup(old.identity) is not None:
                stale_lookup_count += 1
            new_attempt = service.wait_for_attempt(
                new_revision,
                timeout=30.0,
            )
            old_attempts.append(old_attempt)
            new_attempts.append(new_attempt)
            publication = service.lookup(newer.identity)
            if new_attempt.status == "complete":
                if publication is None or len(publication.actions) != 36:
                    partial_publication_count += 1
            elif publication is not None:
                partial_publication_count += 1
    finally:
        service.close()
    acknowledgements = [
        attempt.cancel_ack_ms
        for attempt in old_attempts
        if attempt.cancel_ack_ms is not None
    ]
    return {
        "pair_count": pair_count,
        "old_attempts": attempt_summary(old_attempts),
        "new_attempts": attempt_summary(new_attempts),
        "active_workspace_miss_count": active_workspace_miss_count,
        "active_cancellation_count": len(acknowledgements),
        "cancellation_ack": timing_summary(
            [float(value) for value in acknowledgements]
        ),
        "stale_lookup_count": stale_lookup_count,
        "partial_publication_count": partial_publication_count,
        "worker_priority_lowered": service.priority_lowered,
        "worker_affinity_cpu": service.affinity_cpu,
        "worker_affinity_applied": service.affinity_applied,
    }


def run_all(
    *,
    reservoir: PreparedPhysicalReservoir,
    library: NativeStationaryWitnessLibrary,
    minimum_background_solves: int = 24,
) -> dict[str, object]:
    affinity_cpu = preferred_performance_cpu()
    idle, _idle_elapsed = run_delivery_variant(
        reservoir=reservoir,
        library=library,
        minimum_rounds=3,
        background=None,
        affinity_cpu=affinity_cpu,
    )
    background = _BackgroundSession.start()
    try:
        workers4, workers_elapsed = run_delivery_variant(
            reservoir=reservoir,
            library=library,
            minimum_rounds=3,
            background=background,
            minimum_background_solves=minimum_background_solves,
            affinity_cpu=affinity_cpu,
        )
    finally:
        background.stop()
    control = run_background_control(workers_elapsed)
    cancellation = run_rapid_replacement(
        reservoir=reservoir,
        library=library,
        affinity_cpu=affinity_cpu,
    )
    return {
        "idle": idle,
        "workers4": workers4,
        "workers4_idle_witness_control": control,
        "rapid_replacement": cancellation,
    }


__all__ = [
    "run_all",
    "run_background_control",
    "run_delivery_variant",
    "run_rapid_replacement",
]
