"""Asynchronous exact-root preparation for one immutable policy version.

The service is deliberately narrower than a controller.  It owns one
``LatestPipelinePrewarmScheduler``, accepts newest-target-wins root batches,
and exposes lookup-only consumption.  Callers remain responsible for
constructing physically meaningful roots and for falling back on every miss.
"""

from __future__ import annotations

import concurrent.futures
import threading
import time
from dataclasses import dataclass
from typing import Hashable, Iterable

from .pipeline_prewarm import (
    LatestPipelinePrewarmScheduler,
    PipelinePrewarmSnapshot,
    enumerate_continuation_seed_roots,
)
from .query_survival import (
    QueryLocalSurvivalResult,
    ReachablePipelineRoot,
    SurvivalQueryProblem,
)


@dataclass(frozen=True)
class PipelinePrewarmServiceOutcome:
    """One initial or rolling target batch."""

    revision: int
    root_count: int
    seed_count: int
    status: str
    enumeration_ms: float
    seed_ms: float
    specialization_ms: float
    elapsed_ms: float
    error: str | None = None


@dataclass(frozen=True)
class PipelinePrewarmServiceSnapshot:
    """Nonblocking lifecycle and hit telemetry."""

    policy_version: Hashable
    worker_count: int
    background_low_priority: bool
    submitted_revision: int
    completed_revision: int
    ready_revision: int
    target_running: bool
    target_queued: bool
    target_replacement_count: int
    lookup_count: int
    lookup_hit_count: int
    lookup_miss_count: int
    created_elapsed_ms: float
    latest_outcome: PipelinePrewarmServiceOutcome | None
    scheduler: PipelinePrewarmSnapshot


def _root_sort_key(root: ReachablePipelineRoot) -> tuple[object, ...]:
    return (
        root.frame,
        root.row,
        root.column,
        root.observed_action,
        (
            ""
            if root.pending_command is None
            else root.pending_command.action
        ),
        (
            ()
            if root.pending_command is None
            else root.pending_command.remaining_frames
        ),
    )


def _normalize_roots(
    roots: Iterable[ReachablePipelineRoot],
) -> tuple[ReachablePipelineRoot, ...]:
    normalized = tuple(sorted(set(roots), key=_root_sort_key))
    if not normalized:
        raise ValueError("pipeline prewarm target cannot be empty")
    return normalized


class PipelinePrewarmService:
    """Prepare exact roots without placing work on the issue-time thread."""

    def __init__(
        self,
        *,
        problem: SurvivalQueryProblem,
        policy_version: Hashable,
        initial_roots: Iterable[ReachablePipelineRoot],
        decision_frame_support: tuple[int, ...],
        worker_count: int = 5,
        background_low_priority: bool = True,
        seed_timeout_ms: int = 500,
        specialization_timeout_ms: int = 150,
        target_timeout_seconds: float = 3.0,
    ) -> None:
        if target_timeout_seconds <= 0.0:
            raise ValueError("target timeout must be positive")
        self.problem = problem
        self.policy_version = policy_version
        self.decision_frame_support = decision_frame_support
        self.target_timeout_seconds = target_timeout_seconds
        self.worker_count = worker_count
        self.background_low_priority = background_low_priority
        self._scheduler = LatestPipelinePrewarmScheduler(
            worker_count=worker_count,
            seed_timeout_ms=seed_timeout_ms,
            specialization_timeout_ms=specialization_timeout_ms,
            background_low_priority=background_low_priority,
        )
        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix="pipeline-prewarm-service",
        )
        self._lock = threading.RLock()
        self._condition = threading.Condition(self._lock)
        self._created = time.perf_counter()
        self._closed = False
        self._submitted_revision = 0
        self._completed_revision = 0
        self._ready_revision = 0
        self._target_replacement_count = 0
        self._lookup_count = 0
        self._lookup_hit_count = 0
        self._lookup_miss_count = 0
        self._future: concurrent.futures.Future[
            PipelinePrewarmServiceOutcome
        ] | None = None
        self._queued: tuple[
            int,
            tuple[ReachablePipelineRoot, ...],
        ] | None = None
        self._desired_roots: tuple[ReachablePipelineRoot, ...] | None = None
        self._outcomes: list[PipelinePrewarmServiceOutcome] = []
        with self._lock:
            self._queue_locked(_normalize_roots(initial_roots))

    @property
    def closed(self) -> bool:
        with self._lock:
            return self._closed

    def retarget(
        self,
        roots: Iterable[ReachablePipelineRoot],
    ) -> int:
        """Retain only the newest not-yet-running exact-root target."""

        normalized = _normalize_roots(roots)
        with self._lock:
            self._require_open_locked()
            if normalized == self._desired_roots:
                return self._submitted_revision
            return self._queue_locked(normalized)

    def lookup(
        self,
        root: ReachablePipelineRoot,
    ) -> QueryLocalSurvivalResult | None:
        """Consume one exact root; never enumerate, seed, or specialize."""

        with self._lock:
            if self._closed:
                return None
            self._lookup_count += 1
        result = self._scheduler.lookup(
            policy_version=self.policy_version,
            root=root,
        )
        with self._lock:
            if result is None:
                self._lookup_miss_count += 1
            else:
                self._lookup_hit_count += 1
        return result

    def snapshot(self) -> PipelinePrewarmServiceSnapshot:
        with self._lock:
            latest = self._outcomes[-1] if self._outcomes else None
            return PipelinePrewarmServiceSnapshot(
                policy_version=self.policy_version,
                worker_count=self.worker_count,
                background_low_priority=self.background_low_priority,
                submitted_revision=self._submitted_revision,
                completed_revision=self._completed_revision,
                ready_revision=self._ready_revision,
                target_running=(
                    self._future is not None
                    and not self._future.done()
                ),
                target_queued=self._queued is not None,
                target_replacement_count=self._target_replacement_count,
                lookup_count=self._lookup_count,
                lookup_hit_count=self._lookup_hit_count,
                lookup_miss_count=self._lookup_miss_count,
                created_elapsed_ms=(
                    time.perf_counter() - self._created
                ) * 1000.0,
                latest_outcome=latest,
                scheduler=self._scheduler.snapshot(),
            )

    def outcomes(self) -> tuple[PipelinePrewarmServiceOutcome, ...]:
        with self._lock:
            return tuple(self._outcomes)

    def wait_until_idle(self, timeout: float) -> bool:
        """Wait for the active target and any retained newest target."""

        deadline = time.monotonic() + timeout
        with self._condition:
            while self._future is not None or self._queued is not None:
                remaining = deadline - time.monotonic()
                if remaining <= 0.0:
                    return False
                self._condition.wait(timeout=remaining)
            return True

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
            self._queued = None
        self._scheduler.close()
        self._executor.shutdown(wait=True, cancel_futures=True)
        with self._condition:
            self._future = None
            self._condition.notify_all()

    def __enter__(self) -> PipelinePrewarmService:
        with self._lock:
            self._require_open_locked()
        return self

    def __exit__(self, _exception_type, _exception, _traceback) -> None:
        self.close()

    def _queue_locked(
        self,
        roots: tuple[ReachablePipelineRoot, ...],
    ) -> int:
        self._submitted_revision += 1
        revision = self._submitted_revision
        self._desired_roots = roots
        if self._future is None:
            self._submit_locked(revision, roots)
        else:
            if self._queued is not None:
                self._target_replacement_count += 1
            self._queued = (revision, roots)
        return revision

    def _submit_locked(
        self,
        revision: int,
        roots: tuple[ReachablePipelineRoot, ...],
    ) -> None:
        future = self._executor.submit(
            self._run_target,
            revision,
            roots,
        )
        self._future = future
        future.add_done_callback(self._target_done)

    def _target_done(
        self,
        future: concurrent.futures.Future[
            PipelinePrewarmServiceOutcome
        ],
    ) -> None:
        try:
            outcome = future.result()
        except Exception as error:  # pragma: no cover - service boundary
            outcome = PipelinePrewarmServiceOutcome(
                revision=0,
                root_count=0,
                seed_count=0,
                status="error",
                enumeration_ms=0.0,
                seed_ms=0.0,
                specialization_ms=0.0,
                elapsed_ms=0.0,
                error=repr(error),
            )
        with self._condition:
            if future is not self._future:
                return
            self._outcomes.append(outcome)
            self._completed_revision = max(
                self._completed_revision,
                outcome.revision,
            )
            if outcome.status == "ready":
                self._ready_revision = max(
                    self._ready_revision,
                    outcome.revision,
                )
            self._future = None
            queued = self._queued
            self._queued = None
            if not self._closed and queued is not None:
                self._submit_locked(*queued)
            self._condition.notify_all()

    def _run_target(
        self,
        revision: int,
        roots: tuple[ReachablePipelineRoot, ...],
    ) -> PipelinePrewarmServiceOutcome:
        started = time.perf_counter()
        enumeration_started = time.perf_counter()
        seeds = enumerate_continuation_seed_roots(
            problem=self.problem,
            public_roots=roots,
            decision_frame_support=self.decision_frame_support,
        )
        enumeration_ms = (
            time.perf_counter() - enumeration_started
        ) * 1000.0
        seed_started = time.perf_counter()
        if revision == 1:
            self._scheduler.publish(
                problem=self.problem,
                policy_version=self.policy_version,
                seed_roots=seeds,
                decision_frame_support=self.decision_frame_support,
            )
            accepted = True
        else:
            accepted = self._scheduler.extend_seeds(
                policy_version=self.policy_version,
                roots=seeds,
            )
        seed_ready = (
            accepted
            and self._scheduler.wait_for_seed(
                policy_version=self.policy_version,
                timeout=self.target_timeout_seconds,
            )
        )
        seed_ms = (time.perf_counter() - seed_started) * 1000.0
        specialization_started = time.perf_counter()
        submitted = (
            seed_ready
            and self._scheduler.submit_frontier(
                policy_version=self.policy_version,
                roots=roots,
            )
        )
        specialized = (
            submitted
            and self._scheduler.wait_for_frontier(
                policy_version=self.policy_version,
                timeout=self.target_timeout_seconds,
            )
        )
        specialization_ms = (
            time.perf_counter() - specialization_started
        ) * 1000.0
        if not accepted:
            status = "seed_rejected"
        elif not seed_ready:
            status = "seed_incomplete"
        elif not submitted:
            status = "specialization_rejected"
        elif not specialized:
            status = "specialization_incomplete"
        else:
            status = "ready"
        return PipelinePrewarmServiceOutcome(
            revision=revision,
            root_count=len(roots),
            seed_count=len(seeds),
            status=status,
            enumeration_ms=enumeration_ms,
            seed_ms=seed_ms,
            specialization_ms=specialization_ms,
            elapsed_ms=(time.perf_counter() - started) * 1000.0,
        )

    def _require_open_locked(self) -> None:
        if self._closed:
            raise RuntimeError("pipeline prewarm service is closed")


__all__ = [
    "PipelinePrewarmService",
    "PipelinePrewarmServiceOutcome",
    "PipelinePrewarmServiceSnapshot",
]
