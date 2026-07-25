"""Newest-target-wins background verification of attainable policies.

The service has no control authority.  It exactly evaluates a small causal
candidate-policy portfolio for one immutable Boolean-policy version and one
public root.  Callers may consume a result only through an exact
``(policy_version, root)`` lookup; every miss keeps the established Boolean
policy and issue-time hard certificate authoritative.
"""

from __future__ import annotations

import concurrent.futures
import threading
import time
from dataclasses import dataclass, replace
from typing import Hashable

from .background_priority import lower_current_thread_priority
from .policy_synthesis import (
    CandidatePolicyPortfolioResult,
    evaluate_candidate_policy_portfolio,
    singleton_continuation_candidates,
)
from .query_survival import (
    PipelineWorkspaceDeadlineError,
    ReachablePipelineRoot,
    SurvivalQueryProblem,
)
from .reachability_oracle import SurvivalLabel


@dataclass(frozen=True)
class CandidateVerifierTarget:
    """Exact public root inside one immutable policy version."""

    policy_version: Hashable
    root: ReachablePipelineRoot


@dataclass(frozen=True)
class CandidateVerifierOutcome:
    """One completed, timed-out, stale, or failed target."""

    revision: int
    target: CandidateVerifierTarget
    status: str
    queue_ms: float
    elapsed_ms: float
    horizon_frames: int
    state_label: SurvivalLabel | None = None
    best_actions: tuple[str, ...] = ()
    completed_candidates: tuple[str, ...] = ()
    timed_out_candidates: tuple[str, ...] = ()
    unvisited_candidates: tuple[str, ...] = ()
    stopped_on_feasibility: bool = False
    budget_exhausted: bool = False
    background_priority_lowered: bool = False
    stale_at_completion: bool = False
    error: str | None = None

    @property
    def winning(self) -> bool | None:
        if self.state_label is None:
            return None
        return (
            self.state_label.guaranteed_frames
            == self.horizon_frames
            and self.state_label.bottleneck_margin > 0.0
        )


@dataclass(frozen=True)
class CandidateVerifierSnapshot:
    """Nonblocking lifecycle and delivery telemetry."""

    horizon_frames: int
    decision_frame_support: tuple[int, ...]
    timeout_ms_per_candidate: int
    total_timeout_ms: int
    submitted_revision: int
    completed_revision: int
    ready_revision: int
    target_running: bool
    target_queued: bool
    target_replacement_count: int
    target_discard_count: int
    stale_completion_count: int
    lookup_count: int
    lookup_hit_count: int
    lookup_miss_count: int
    latest_outcome: CandidateVerifierOutcome | None


@dataclass(frozen=True)
class _Work:
    revision: int
    problem: SurvivalQueryProblem
    target: CandidateVerifierTarget
    submitted_at: float


class CandidateVerifierService:
    """Run one bounded candidate verifier beside local planning."""

    def __init__(
        self,
        *,
        horizon_frames: int = 32,
        decision_frame_support: tuple[int, ...] = (4, 5, 6),
        timeout_ms_per_candidate: int = 10,
        total_timeout_ms: int = 12,
    ) -> None:
        if horizon_frames <= 0:
            raise ValueError("candidate horizon must be positive")
        if (
            not decision_frame_support
            or min(decision_frame_support) <= 0
            or tuple(sorted(set(decision_frame_support)))
            != decision_frame_support
        ):
            raise ValueError(
                "candidate decision support must be positive and sorted"
            )
        if timeout_ms_per_candidate <= 0:
            raise ValueError("candidate timeout must be positive")
        if total_timeout_ms <= 0:
            raise ValueError("candidate total timeout must be positive")
        self.horizon_frames = horizon_frames
        self.decision_frame_support = decision_frame_support
        self.timeout_ms_per_candidate = timeout_ms_per_candidate
        self.total_timeout_ms = total_timeout_ms
        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix="candidate-verifier-shadow",
        )
        self._lock = threading.RLock()
        self._condition = threading.Condition(self._lock)
        self._closed = False
        self._submitted_revision = 0
        self._completed_revision = 0
        self._ready_revision = 0
        self._target_replacement_count = 0
        self._target_discard_count = 0
        self._stale_completion_count = 0
        self._lookup_count = 0
        self._lookup_hit_count = 0
        self._lookup_miss_count = 0
        self._desired_target: CandidateVerifierTarget | None = None
        self._future: concurrent.futures.Future[
            tuple[CandidateVerifierOutcome, CandidatePolicyPortfolioResult | None]
        ] | None = None
        self._queued: _Work | None = None
        self._ready: tuple[
            CandidateVerifierOutcome,
            CandidatePolicyPortfolioResult,
        ] | None = None
        self._outcomes: list[CandidateVerifierOutcome] = []

    @property
    def closed(self) -> bool:
        with self._lock:
            return self._closed

    def submit(
        self,
        *,
        problem: SurvivalQueryProblem,
        target: CandidateVerifierTarget,
    ) -> int | None:
        """Submit one exact root, replacing only queued older work."""

        root = target.root
        if (
            root.frame < 0
            or root.frame + self.horizon_frames
            > problem.horizon_frames
        ):
            return None
        with self._lock:
            self._require_open_locked()
            if target == self._desired_target:
                return self._submitted_revision
            self._submitted_revision += 1
            revision = self._submitted_revision
            self._desired_target = target
            work = _Work(
                revision=revision,
                problem=problem,
                target=target,
                submitted_at=time.perf_counter(),
            )
            if self._future is None:
                self._submit_locked(work)
            else:
                if self._queued is not None:
                    self._target_replacement_count += 1
                self._queued = work
            return revision

    def discard_target(self) -> bool:
        """Invalidate obsolete work and drop any not-yet-running target."""

        with self._lock:
            self._require_open_locked()
            changed = (
                self._desired_target is not None
                or self._queued is not None
            )
            if not changed:
                return False
            self._desired_target = None
            if self._queued is not None:
                self._queued = None
            self._target_discard_count += 1
            return True

    def lookup(
        self,
        target: CandidateVerifierTarget,
    ) -> CandidateVerifierOutcome | None:
        """Return a completed result only for the exact requested root."""

        with self._lock:
            if self._closed:
                return None
            self._lookup_count += 1
            ready = self._ready
            if (
                ready is None
                or ready[0].target != target
                or ready[0].stale_at_completion
            ):
                self._lookup_miss_count += 1
                return None
            self._lookup_hit_count += 1
            return ready[0]

    def snapshot(self) -> CandidateVerifierSnapshot:
        with self._lock:
            return CandidateVerifierSnapshot(
                horizon_frames=self.horizon_frames,
                decision_frame_support=self.decision_frame_support,
                timeout_ms_per_candidate=self.timeout_ms_per_candidate,
                total_timeout_ms=self.total_timeout_ms,
                submitted_revision=self._submitted_revision,
                completed_revision=self._completed_revision,
                ready_revision=self._ready_revision,
                target_running=(
                    self._future is not None
                    and not self._future.done()
                ),
                target_queued=self._queued is not None,
                target_replacement_count=self._target_replacement_count,
                target_discard_count=self._target_discard_count,
                stale_completion_count=self._stale_completion_count,
                lookup_count=self._lookup_count,
                lookup_hit_count=self._lookup_hit_count,
                lookup_miss_count=self._lookup_miss_count,
                latest_outcome=(
                    self._outcomes[-1] if self._outcomes else None
                ),
            )

    def outcomes(self) -> tuple[CandidateVerifierOutcome, ...]:
        with self._lock:
            return tuple(self._outcomes)

    def wait_until_idle(self, timeout: float) -> bool:
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
        self._executor.shutdown(wait=True, cancel_futures=True)
        with self._condition:
            self._future = None
            self._condition.notify_all()

    def __enter__(self) -> CandidateVerifierService:
        with self._lock:
            self._require_open_locked()
        return self

    def __exit__(self, _exception_type, _exception, _traceback) -> None:
        self.close()

    def _submit_locked(self, work: _Work) -> None:
        future = self._executor.submit(self._run, work)
        self._future = future
        future.add_done_callback(self._done)

    def _done(
        self,
        future: concurrent.futures.Future[
            tuple[CandidateVerifierOutcome, CandidatePolicyPortfolioResult | None]
        ],
    ) -> None:
        try:
            outcome, portfolio = future.result()
        except Exception as error:  # pragma: no cover - service boundary
            with self._lock:
                target = self._desired_target
                revision = self._submitted_revision
            if target is None:
                return
            outcome = CandidateVerifierOutcome(
                revision=revision,
                target=target,
                status="error",
                queue_ms=0.0,
                elapsed_ms=0.0,
                horizon_frames=self.horizon_frames,
                error=repr(error),
            )
            portfolio = None
        with self._condition:
            if future is not self._future:
                return
            stale = (
                outcome.revision != self._submitted_revision
                or outcome.target != self._desired_target
            )
            if stale:
                outcome = replace(outcome, stale_at_completion=True)
                self._stale_completion_count += 1
            self._outcomes.append(outcome)
            self._completed_revision = max(
                self._completed_revision,
                outcome.revision,
            )
            if (
                not stale
                and portfolio is not None
                and outcome.status
                in (
                    "feasible",
                    "candidate_exhausted",
                    "budget_exhausted",
                )
            ):
                self._ready = (outcome, portfolio)
                self._ready_revision = outcome.revision
            self._future = None
            queued = self._queued
            self._queued = None
            if not self._closed and queued is not None:
                self._submit_locked(queued)
            self._condition.notify_all()

    def _run(
        self,
        work: _Work,
    ) -> tuple[
        CandidateVerifierOutcome,
        CandidatePolicyPortfolioResult | None,
    ]:
        started = time.perf_counter()
        priority_lowered = lower_current_thread_priority()
        root = work.target.root
        window = SurvivalQueryProblem(
            x_axis=work.problem.x_axis,
            y_axis=work.problem.y_axis,
            clearance_volume=work.problem.clearance_volume[
                root.frame : root.frame + self.horizon_frames + 1
            ],
            actions=work.problem.actions,
            delay_frames=work.problem.delay_frames,
            nominal_delay=work.problem.nominal_delay,
            config=work.problem.config,
        )
        window_root = ReachablePipelineRoot(
            frame=0,
            row=root.row,
            column=root.column,
            observed_action=root.observed_action,
            pending_command=root.pending_command,
        )
        portfolio = None
        status = "error"
        error_text = None
        try:
            portfolio = evaluate_candidate_policy_portfolio(
                problem=window,
                policy_version=(
                    "candidate-verifier-shadow",
                    work.target.policy_version,
                    work.revision,
                ),
                decision_frame_support=self.decision_frame_support,
                candidates=singleton_continuation_candidates(window),
                frame=window_root.frame,
                row=window_root.row,
                column=window_root.column,
                observed_action=window_root.observed_action,
                pending_command=window_root.pending_command,
                timeout_ms_per_candidate=self.timeout_ms_per_candidate,
                total_timeout_ms=self.total_timeout_ms,
                stop_on_feasibility=True,
            )
            status = (
                "feasible"
                if portfolio.feasibility_sufficient
                else (
                    "budget_exhausted"
                    if portfolio.budget_exhausted
                    else "candidate_exhausted"
                )
            )
        except PipelineWorkspaceDeadlineError as error:
            status = "timeout"
            error_text = str(error)
        except Exception as error:  # retained shadow diagnostic boundary
            status = "error"
            error_text = f"{type(error).__name__}: {error}"
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        result = portfolio.result if portfolio is not None else None
        outcome = CandidateVerifierOutcome(
            revision=work.revision,
            target=work.target,
            status=status,
            queue_ms=(started - work.submitted_at) * 1000.0,
            elapsed_ms=elapsed_ms,
            horizon_frames=self.horizon_frames,
            state_label=(
                result.state_label if result is not None else None
            ),
            best_actions=(
                result.best_actions if result is not None else ()
            ),
            completed_candidates=(
                portfolio.completed_candidates
                if portfolio is not None
                else ()
            ),
            timed_out_candidates=(
                portfolio.timed_out_candidates
                if portfolio is not None
                else ()
            ),
            unvisited_candidates=(
                portfolio.unvisited_candidates
                if portfolio is not None
                else ()
            ),
            stopped_on_feasibility=(
                portfolio.stopped_on_feasibility
                if portfolio is not None
                else False
            ),
            budget_exhausted=(
                portfolio.budget_exhausted
                if portfolio is not None
                else False
            ),
            background_priority_lowered=priority_lowered,
            error=error_text,
        )
        return outcome, portfolio

    def _require_open_locked(self) -> None:
        if self._closed:
            raise RuntimeError("candidate verifier service is closed")


__all__ = [
    "CandidateVerifierOutcome",
    "CandidateVerifierService",
    "CandidateVerifierSnapshot",
    "CandidateVerifierTarget",
]
