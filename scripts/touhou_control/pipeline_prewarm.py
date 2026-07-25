"""Bounded newest-version-wins prewarming for exact pipeline roots.

This module deliberately stays game-neutral.  A policy publication starts
fixed-cadence continuation seeds in phase-residue shards.  Once the issued
action determines a reachable exact-root frontier, completed continuation
memos are merged into short-lived public-root workspaces whose first
transition may use a wider cadence support.

Every replacement cancels the superseded native work.  Lookup never computes.
"""

from __future__ import annotations

import concurrent.futures
import threading
import time
from dataclasses import dataclass, field
from typing import Hashable, Iterable

from .background_priority import lower_current_thread_priority
from .query_survival import (
    PipelineSurvivalWorkspace,
    PipelineWorkspaceCancelledError,
    PipelineWorkspaceDeadlineError,
    QueryLocalSurvivalResult,
    ReachablePipelineRoot,
    SurvivalQueryProblem,
    _prepare_root_enumeration_context,
    enumerate_next_decision_roots,
)


@dataclass(frozen=True)
class PipelinePrewarmOutcome:
    """One completed, cancelled, expired, or failed root operation."""

    root: ReachablePipelineRoot
    operation: str
    status: str
    elapsed_ms: float
    new_state_count: int = 0
    merged_state_count: int = 0
    error: str | None = None


@dataclass(frozen=True)
class PipelinePrewarmSnapshot:
    """Nonblocking telemetry for the current publication generation."""

    generation: int
    policy_version: Hashable | None
    seed_submitted: int
    seed_completed: int
    seed_ready: bool
    seed_failed: int
    specialization_batch: int
    specialization_submitted: int
    specialization_completed: int
    specialization_ready: bool
    specialization_failed: int
    retired_generation_count: int


@dataclass
class _WorkspaceBatch:
    workspaces: dict[int, PipelineSurvivalWorkspace]
    executor: concurrent.futures.ThreadPoolExecutor
    futures: list[
        concurrent.futures.Future[list[PipelinePrewarmOutcome]]
    ] = field(default_factory=list)
    submitted_root_count: int = 0
    cancelled: bool = False
    closed: bool = False

    @property
    def done(self) -> bool:
        return all(future.done() for future in self.futures)

    def outcomes(self) -> list[PipelinePrewarmOutcome]:
        if not self.done:
            return []
        results = []
        for future in self.futures:
            if future.cancelled():
                continue
            try:
                results.extend(future.result())
            except Exception as error:  # pragma: no cover - defensive boundary
                results.append(
                    PipelinePrewarmOutcome(
                        root=ReachablePipelineRoot(
                            frame=0,
                            row=0,
                            column=0,
                            observed_action="<batch>",
                            pending_command=None,
                        ),
                        operation="batch",
                        status="error",
                        elapsed_ms=0.0,
                        error=repr(error),
                    )
                )
        return results

    def cancel(self) -> None:
        if self.cancelled:
            return
        self.cancelled = True
        for workspace in self.workspaces.values():
            workspace.cancel()
        for future in self.futures:
            future.cancel()
        self.executor.shutdown(wait=False, cancel_futures=True)

    def close(self, *, wait: bool) -> None:
        if self.closed:
            return
        if wait:
            self.executor.shutdown(wait=True, cancel_futures=True)
        elif not self.done:
            return
        else:
            self.executor.shutdown(wait=False, cancel_futures=True)
        for workspace in self.workspaces.values():
            workspace.close()
        self.closed = True


@dataclass
class _Generation:
    number: int
    problem: SurvivalQueryProblem
    policy_version: Hashable
    decision_frame_support: tuple[int, ...]
    seed_batch: _WorkspaceBatch
    specialization_batch_number: int = 0
    specialization_batch: _WorkspaceBatch | None = None
    retired_batches: list[_WorkspaceBatch] = field(default_factory=list)
    seeded_roots: set[ReachablePipelineRoot] = field(default_factory=set)

    def cancel(self) -> None:
        self.seed_batch.cancel()
        if self.specialization_batch is not None:
            self.specialization_batch.cancel()
        for batch in self.retired_batches:
            batch.cancel()

    def close(self, *, wait: bool) -> None:
        self.seed_batch.close(wait=wait)
        if self.specialization_batch is not None:
            self.specialization_batch.close(wait=wait)
        for batch in self.retired_batches:
            batch.close(wait=wait)


def _group_by_residue(
    roots: Iterable[ReachablePipelineRoot],
    modulus: int,
) -> dict[int, tuple[ReachablePipelineRoot, ...]]:
    grouped: dict[int, list[ReachablePipelineRoot]] = {}
    seen = set()
    for root in roots:
        if root in seen:
            continue
        seen.add(root)
        grouped.setdefault(root.frame % modulus, []).append(root)
    return {
        residue: tuple(
            sorted(
                values,
                key=lambda root: (
                    root.frame,
                    root.row,
                    root.column,
                    root.observed_action,
                    repr(root.pending_command),
                ),
            )
        )
        for residue, values in grouped.items()
    }


def enumerate_continuation_seed_roots(
    *,
    problem: SurvivalQueryProblem,
    public_roots: Iterable[ReachablePipelineRoot],
    decision_frame_support: tuple[int, ...],
) -> tuple[ReachablePipelineRoot, ...]:
    """Return every one-step successor needed for full public-root labels."""

    context = _prepare_root_enumeration_context(
        x_axis=problem.x_axis,
        y_axis=problem.y_axis,
        actions=problem.actions,
        delay_frames=problem.delay_frames,
        decision_frame_support=decision_frame_support,
        config=problem.config,
    )
    seeds = set()
    for root in public_roots:
        for action in problem.actions:
            seeds.update(
                enumerate_next_decision_roots(
                    x_axis=problem.x_axis,
                    y_axis=problem.y_axis,
                    actions=problem.actions,
                    delay_frames=problem.delay_frames,
                    decision_frame_support=decision_frame_support,
                    config=problem.config,
                    start_frame=root.frame,
                    horizon_frame=problem.horizon_frames,
                    row=root.row,
                    column=root.column,
                    observed_action=root.observed_action,
                    selected_action=action.name,
                    pending_command=root.pending_command,
                    _context=context,
                )
            )
    return tuple(
        sorted(
            seeds,
            key=lambda root: (
                root.frame,
                root.row,
                root.column,
                root.observed_action,
                repr(root.pending_command),
            ),
        )
    )


class LatestPipelinePrewarmScheduler:
    """Own at most one authoritative generation and one frontier batch.

    Publishing a newer policy immediately requests native cancellation on the
    old generation and gives the new generation a separate executor, so stale
    work cannot remain ahead of it in a FIFO queue.
    """

    def __init__(
        self,
        *,
        worker_count: int = 3,
        seed_timeout_ms: int = 160,
        specialization_timeout_ms: int = 80,
        background_low_priority: bool = False,
    ) -> None:
        if worker_count <= 0:
            raise ValueError("prewarm worker count must be positive")
        if seed_timeout_ms <= 0 or specialization_timeout_ms <= 0:
            raise ValueError("prewarm timeouts must be positive")
        self.worker_count = worker_count
        self.seed_timeout_ms = seed_timeout_ms
        self.specialization_timeout_ms = specialization_timeout_ms
        self.background_low_priority = background_low_priority
        self._lock = threading.RLock()
        self._generation_number = 0
        self._current: _Generation | None = None
        self._retired: list[_Generation] = []
        self._closed = False

    def publish(
        self,
        *,
        problem: SurvivalQueryProblem,
        policy_version: Hashable,
        seed_roots: Iterable[ReachablePipelineRoot],
        decision_frame_support: tuple[int, ...],
    ) -> int:
        """Start rolling continuation seeds for a new immutable policy."""

        roots_by_residue = _group_by_residue(
            seed_roots,
            problem.config.frames_per_layer,
        )
        if not roots_by_residue:
            raise ValueError("at least one phase seed root is required")
        with self._lock:
            self._require_open()
            if self._current is not None:
                self._current.cancel()
                self._retired.append(self._current)
            self._generation_number += 1
            generation_number = self._generation_number
            executor = concurrent.futures.ThreadPoolExecutor(
                max_workers=min(self.worker_count, len(roots_by_residue)),
                thread_name_prefix=f"pipeline-seed-{generation_number}",
            )
            workspaces = {
                residue: problem.build_pipeline_workspace(
                    policy_version=policy_version,
                    decision_frame_support=decision_frame_support,
                )
                for residue in roots_by_residue
            }
            batch = _WorkspaceBatch(
                workspaces=workspaces,
                executor=executor,
                submitted_root_count=sum(
                    len(roots) for roots in roots_by_residue.values()
                ),
            )
            generation = _Generation(
                number=generation_number,
                problem=problem,
                policy_version=policy_version,
                decision_frame_support=decision_frame_support,
                seed_batch=batch,
                seeded_roots={
                    root
                    for roots in roots_by_residue.values()
                    for root in roots
                },
            )
            self._current = generation
            for residue, roots in roots_by_residue.items():
                batch.futures.append(
                    executor.submit(
                        self._seed_residue,
                        generation,
                        residue,
                        roots,
                    )
                )
            self._reap_locked()
            return generation_number

    def extend_seeds(
        self,
        *,
        policy_version: Hashable,
        roots: Iterable[ReachablePipelineRoot],
    ) -> bool:
        """Append one bounded rolling seed round when the prior round is done.

        Calls made while seed work is still running are rejected instead of
        building a FIFO backlog.  The caller may retry with its newest tube.
        """

        with self._lock:
            self._require_open()
            generation = self._current
            if (
                generation is None
                or generation.policy_version != policy_version
                or not generation.seed_batch.done
            ):
                return False
            new_roots = tuple(
                root
                for root in roots
                if root not in generation.seeded_roots
            )
            roots_by_residue = _group_by_residue(
                new_roots,
                generation.problem.config.frames_per_layer,
            )
            if not roots_by_residue:
                return True
            for residue in roots_by_residue:
                if residue not in generation.seed_batch.workspaces:
                    generation.seed_batch.workspaces[residue] = (
                        generation.problem.build_pipeline_workspace(
                            policy_version=policy_version,
                            decision_frame_support=(
                                generation.decision_frame_support
                            ),
                        )
                    )
            for residue, residue_roots in roots_by_residue.items():
                generation.seeded_roots.update(residue_roots)
                generation.seed_batch.submitted_root_count += len(
                    residue_roots
                )
                generation.seed_batch.futures.append(
                    generation.seed_batch.executor.submit(
                        self._seed_residue,
                        generation,
                        residue,
                        residue_roots,
                    )
                )
            return True

    def submit_frontier(
        self,
        *,
        policy_version: Hashable,
        roots: Iterable[ReachablePipelineRoot],
    ) -> bool:
        """Specialize the newest frontier only when all seeds are complete."""

        with self._lock:
            self._require_open()
            generation = self._current
            if (
                generation is None
                or generation.policy_version != policy_version
                or not self._seed_ready(generation)
            ):
                return False
            roots_by_residue = _group_by_residue(
                roots,
                generation.problem.config.frames_per_layer,
            )
            if not roots_by_residue:
                return False
            if generation.specialization_batch is not None:
                generation.specialization_batch.cancel()
                generation.retired_batches.append(
                    generation.specialization_batch
                )
            generation.specialization_batch_number += 1
            batch_number = generation.specialization_batch_number
            executor = concurrent.futures.ThreadPoolExecutor(
                max_workers=min(self.worker_count, len(roots_by_residue)),
                thread_name_prefix=(
                    f"pipeline-root-{generation.number}-{batch_number}"
                ),
            )
            workspaces = {
                residue: generation.problem.build_pipeline_workspace(
                    policy_version=policy_version,
                    decision_frame_support=(
                        generation.decision_frame_support
                    ),
                )
                for residue in roots_by_residue
            }
            batch = _WorkspaceBatch(
                workspaces=workspaces,
                executor=executor,
                submitted_root_count=sum(
                    len(values) for values in roots_by_residue.values()
                ),
            )
            generation.specialization_batch = batch
            for residue, residue_roots in roots_by_residue.items():
                batch.futures.append(
                    executor.submit(
                        self._specialize_residue,
                        generation,
                        batch,
                        residue,
                        residue_roots,
                    )
                )
            self._reap_locked()
            return True

    def lookup(
        self,
        *,
        policy_version: Hashable,
        root: ReachablePipelineRoot,
    ) -> QueryLocalSurvivalResult | None:
        """Return one exact cached root; never start expansion."""

        with self._lock:
            generation = self._current
            if (
                generation is None
                or generation.policy_version != policy_version
                or generation.specialization_batch is None
                or not generation.specialization_batch.done
            ):
                return None
            workspace = generation.specialization_batch.workspaces.get(
                root.frame % generation.problem.config.frames_per_layer
            )
            if workspace is None:
                return None
            result = workspace.lookup_cell(
                policy_version=policy_version,
                frame=root.frame,
                row=root.row,
                column=root.column,
                observed_action=root.observed_action,
                pending_command=root.pending_command,
            )
            self._reap_locked()
            return result

    def wait_for_seed(
        self,
        *,
        policy_version: Hashable,
        timeout: float,
    ) -> bool:
        """Wait only for the requested current generation's phase seeds."""

        deadline = time.monotonic() + timeout
        while True:
            with self._lock:
                generation = self._current
                if (
                    generation is None
                    or generation.policy_version != policy_version
                ):
                    return False
                if self._seed_ready(generation):
                    return True
                if generation.seed_batch.done:
                    return False
            remaining = deadline - time.monotonic()
            if remaining <= 0.0:
                return False
            time.sleep(min(0.002, remaining))

    def wait_for_frontier(
        self,
        *,
        policy_version: Hashable,
        timeout: float,
    ) -> bool:
        """Wait for the current frontier without accepting an older batch."""

        deadline = time.monotonic() + timeout
        while True:
            with self._lock:
                generation = self._current
                if (
                    generation is None
                    or generation.policy_version != policy_version
                    or generation.specialization_batch is None
                ):
                    return False
                batch = generation.specialization_batch
                if batch.done:
                    return not any(
                        outcome.status != "completed"
                        for outcome in batch.outcomes()
                    )
            remaining = deadline - time.monotonic()
            if remaining <= 0.0:
                return False
            time.sleep(min(0.002, remaining))

    def snapshot(self) -> PipelinePrewarmSnapshot:
        with self._lock:
            self._reap_locked()
            generation = self._current
            if generation is None:
                return PipelinePrewarmSnapshot(
                    generation=self._generation_number,
                    policy_version=None,
                    seed_submitted=0,
                    seed_completed=0,
                    seed_ready=False,
                    seed_failed=0,
                    specialization_batch=0,
                    specialization_submitted=0,
                    specialization_completed=0,
                    specialization_ready=False,
                    specialization_failed=0,
                    retired_generation_count=len(self._retired),
                )
            seed_outcomes = generation.seed_batch.outcomes()
            specialization = generation.specialization_batch
            specialization_outcomes = (
                specialization.outcomes()
                if specialization is not None
                else []
            )
            return PipelinePrewarmSnapshot(
                generation=generation.number,
                policy_version=generation.policy_version,
                seed_submitted=generation.seed_batch.submitted_root_count,
                seed_completed=sum(
                    outcome.status == "completed"
                    for outcome in seed_outcomes
                ),
                seed_ready=self._seed_ready(generation),
                seed_failed=sum(
                    outcome.status != "completed"
                    for outcome in seed_outcomes
                ),
                specialization_batch=(
                    generation.specialization_batch_number
                ),
                specialization_submitted=(
                    specialization.submitted_root_count
                    if specialization is not None
                    else 0
                ),
                specialization_completed=sum(
                    outcome.status == "completed"
                    for outcome in specialization_outcomes
                ),
                specialization_ready=(
                    specialization is not None
                    and specialization.done
                    and all(
                        outcome.status == "completed"
                        for outcome in specialization_outcomes
                    )
                ),
                specialization_failed=sum(
                    outcome.status != "completed"
                    for outcome in specialization_outcomes
                ),
                retired_generation_count=len(self._retired),
            )

    def seed_outcomes(self) -> tuple[PipelinePrewarmOutcome, ...]:
        with self._lock:
            if self._current is None:
                return ()
            return tuple(self._current.seed_batch.outcomes())

    def specialization_outcomes(
        self,
    ) -> tuple[PipelinePrewarmOutcome, ...]:
        with self._lock:
            if (
                self._current is None
                or self._current.specialization_batch is None
            ):
                return ()
            return tuple(
                self._current.specialization_batch.outcomes()
            )

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
            generations = list(self._retired)
            if self._current is not None:
                generations.append(self._current)
                self._current = None
            self._retired = []
            for generation in generations:
                generation.cancel()
        for generation in generations:
            generation.close(wait=True)

    def __enter__(self) -> LatestPipelinePrewarmScheduler:
        self._require_open()
        return self

    def __exit__(self, _exception_type, _exception, _traceback) -> None:
        self.close()

    def _seed_residue(
        self,
        generation: _Generation,
        residue: int,
        roots: tuple[ReachablePipelineRoot, ...],
    ) -> list[PipelinePrewarmOutcome]:
        if self.background_low_priority:
            lower_current_thread_priority()
        workspace = generation.seed_batch.workspaces[residue]
        outcomes = []
        for root in roots:
            started = time.perf_counter()
            try:
                _, stats = workspace.prewarm_continuation_cell(
                    policy_version=generation.policy_version,
                    frame=root.frame,
                    row=root.row,
                    column=root.column,
                    observed_action=root.observed_action,
                    pending_command=root.pending_command,
                    timeout_ms=self.seed_timeout_ms,
                )
                outcomes.append(
                    PipelinePrewarmOutcome(
                        root=root,
                        operation="seed",
                        status="completed",
                        elapsed_ms=(
                            time.perf_counter() - started
                        ) * 1000.0,
                        new_state_count=stats.new_state_count,
                    )
                )
            except PipelineWorkspaceCancelledError:
                outcomes.append(
                    PipelinePrewarmOutcome(
                        root=root,
                        operation="seed",
                        status="cancelled",
                        elapsed_ms=(
                            time.perf_counter() - started
                        ) * 1000.0,
                    )
                )
                break
            except PipelineWorkspaceDeadlineError:
                outcomes.append(
                    PipelinePrewarmOutcome(
                        root=root,
                        operation="seed",
                        status="deadline",
                        elapsed_ms=(
                            time.perf_counter() - started
                        ) * 1000.0,
                    )
                )
            except Exception as error:  # pragma: no cover - boundary telemetry
                outcomes.append(
                    PipelinePrewarmOutcome(
                        root=root,
                        operation="seed",
                        status="error",
                        elapsed_ms=(
                            time.perf_counter() - started
                        ) * 1000.0,
                        error=repr(error),
                    )
                )
                break
        return outcomes

    def _specialize_residue(
        self,
        generation: _Generation,
        batch: _WorkspaceBatch,
        residue: int,
        roots: tuple[ReachablePipelineRoot, ...],
    ) -> list[PipelinePrewarmOutcome]:
        if self.background_low_priority:
            lower_current_thread_priority()
        workspace = batch.workspaces[residue]
        merge_started = time.perf_counter()
        merged_states = 0
        try:
            for source in generation.seed_batch.workspaces.values():
                merged_states += workspace.merge_continuation_from(source)
        except PipelineWorkspaceCancelledError:
            return [
                PipelinePrewarmOutcome(
                    root=root,
                    operation="specialize",
                    status="cancelled",
                    elapsed_ms=(
                        time.perf_counter() - merge_started
                    ) * 1000.0,
                )
                for root in roots
            ]
        merge_ms = (time.perf_counter() - merge_started) * 1000.0
        outcomes = []
        for index, root in enumerate(roots):
            started = time.perf_counter()
            try:
                result = workspace.query_cell(
                    policy_version=generation.policy_version,
                    frame=root.frame,
                    row=root.row,
                    column=root.column,
                    observed_action=root.observed_action,
                    pending_command=root.pending_command,
                    timeout_ms=self.specialization_timeout_ms,
                )
                outcomes.append(
                    PipelinePrewarmOutcome(
                        root=root,
                        operation="specialize",
                        status="completed",
                        elapsed_ms=(
                            time.perf_counter() - started
                        ) * 1000.0,
                        new_state_count=(
                            result.workspace_stats.new_state_count
                        ),
                        merged_state_count=(
                            merged_states if index == 0 else 0
                        ),
                        error=(
                            f"merge_ms={merge_ms:.6f}"
                            if index == 0
                            else None
                        ),
                    )
                )
            except PipelineWorkspaceCancelledError:
                outcomes.append(
                    PipelinePrewarmOutcome(
                        root=root,
                        operation="specialize",
                        status="cancelled",
                        elapsed_ms=(
                            time.perf_counter() - started
                        ) * 1000.0,
                    )
                )
                break
            except PipelineWorkspaceDeadlineError:
                outcomes.append(
                    PipelinePrewarmOutcome(
                        root=root,
                        operation="specialize",
                        status="deadline",
                        elapsed_ms=(
                            time.perf_counter() - started
                        ) * 1000.0,
                    )
                )
            except Exception as error:  # pragma: no cover - boundary telemetry
                outcomes.append(
                    PipelinePrewarmOutcome(
                        root=root,
                        operation="specialize",
                        status="error",
                        elapsed_ms=(
                            time.perf_counter() - started
                        ) * 1000.0,
                        error=repr(error),
                    )
                )
                break
        return outcomes

    @staticmethod
    def _seed_ready(generation: _Generation) -> bool:
        if not generation.seed_batch.done:
            return False
        outcomes = generation.seed_batch.outcomes()
        return (
            len(outcomes) == generation.seed_batch.submitted_root_count
            and all(outcome.status == "completed" for outcome in outcomes)
        )

    def _reap_locked(self) -> None:
        survivors = []
        for generation in self._retired:
            if (
                generation.seed_batch.done
                and (
                    generation.specialization_batch is None
                    or generation.specialization_batch.done
                )
                and all(batch.done for batch in generation.retired_batches)
            ):
                generation.close(wait=False)
            else:
                survivors.append(generation)
        self._retired = survivors
        if self._current is not None:
            current_batches = []
            for batch in self._current.retired_batches:
                if batch.done:
                    batch.close(wait=False)
                else:
                    current_batches.append(batch)
            self._current.retired_batches = current_batches

    def _require_open(self) -> None:
        if self._closed:
            raise RuntimeError("pipeline prewarm scheduler is closed")


__all__ = [
    "LatestPipelinePrewarmScheduler",
    "PipelinePrewarmOutcome",
    "PipelinePrewarmSnapshot",
    "enumerate_continuation_seed_roots",
]
