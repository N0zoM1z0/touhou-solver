"""Single-worker newest-wins publication service for offline measurement."""

from __future__ import annotations

import math
import threading
import time
from dataclasses import dataclass, replace

from touhou_control.background_priority import (
    lower_current_thread_priority,
    pin_current_thread_to_cpu,
)

from .native import (
    PIPELINE_RESULT_CANCELLED,
    PIPELINE_RESULT_DEADLINE,
    NativeStationaryWitnessLibrary,
    NativeStationaryWitnessWorkspace,
    NativeWitnessAction,
    validate_action_witness,
)
from .workload import PreparedWitnessWorkload


@dataclass(frozen=True)
class WitnessPublication:
    revision: int
    identity: str
    actions: tuple[NativeWitnessAction, ...]
    latency_ms: float
    workspace_create_ms: float
    native_query_decode_ms: float
    native_kernel_ms: float
    decode_ms: float
    validation_ms: float
    workspace_destroy_ms: float
    publication_lock_wait_ms: float
    evaluated_state_count: int
    path_step_count: int
    scalar_path_tie_divergence_count: int


@dataclass(frozen=True)
class WitnessAttempt:
    revision: int
    identity: str
    status: str
    latency_ms: float
    workspace_create_ms: float
    native_query_decode_ms: float
    native_kernel_ms: float
    decode_ms: float
    validation_ms: float
    workspace_destroy_ms: float
    publication_lock_wait_ms: float
    completed_action_count: int
    evaluated_state_count: int
    path_step_count: int
    scalar_path_tie_divergence_count: int
    cancel_ack_ms: float | None
    error: str | None


@dataclass(frozen=True)
class _Job:
    revision: int
    workload: PreparedWitnessWorkload


@dataclass
class _Active:
    job: _Job
    workspace: NativeStationaryWitnessWorkspace | None = None
    cancel_requested_at: float | None = None


class NewestWitnessService:
    """At most one active private workspace and one replaceable pending job."""

    def __init__(
        self,
        *,
        library: NativeStationaryWitnessLibrary,
        decision_frame_support: tuple[int, ...] = (4, 5, 6),
        deadline_ms: float = 1000.0 / 60.0,
        lower_priority: bool = True,
        affinity_cpu: int | None = None,
    ) -> None:
        self._library = library
        self._decision_frame_support = decision_frame_support
        self._deadline_ms = deadline_ms
        self._lower_priority = lower_priority
        self._affinity_cpu = affinity_cpu
        self._condition = threading.Condition()
        self._pending: _Job | None = None
        self._active: _Active | None = None
        self._newest_revision = 0
        self._newest_identity: str | None = None
        self._publication: WitnessPublication | None = None
        self._attempts: dict[int, WitnessAttempt] = {}
        self._closed = False
        self._priority_lowered = False
        self._affinity_applied = False
        self._thread = threading.Thread(
            target=self._run,
            name="stationary-witness-delivery",
            daemon=False,
        )
        self._thread.start()

    @property
    def priority_lowered(self) -> bool:
        return self._priority_lowered

    @property
    def affinity_cpu(self) -> int | None:
        return self._affinity_cpu

    @property
    def affinity_applied(self) -> bool:
        return self._affinity_applied

    def submit(self, workload: PreparedWitnessWorkload) -> int:
        with self._condition:
            if self._closed:
                raise RuntimeError("stationary witness service is closed")
            self._newest_revision += 1
            revision = self._newest_revision
            self._newest_identity = workload.identity
            self._publication = None
            self._pending = _Job(revision, workload)
            if self._active is not None:
                requested = time.perf_counter()
                self._active.cancel_requested_at = requested
                if self._active.workspace is not None:
                    status = self._active.workspace.cancel()
                    if status != 0:
                        raise RuntimeError(
                            f"native cancellation request failed with {status}"
                        )
            self._condition.notify_all()
            return revision

    def lookup(self, identity: str) -> WitnessPublication | None:
        with self._condition:
            publication = self._publication
            if (
                identity != self._newest_identity
                or publication is None
                or publication.identity != identity
                or publication.revision != self._newest_revision
            ):
                return None
            return publication

    def wait_until_workspace_active(
        self,
        revision: int,
        *,
        timeout: float,
    ) -> bool:
        deadline = time.monotonic() + timeout
        with self._condition:
            while True:
                if (
                    self._active is not None
                    and self._active.job.revision == revision
                    and self._active.workspace is not None
                ):
                    return True
                if revision in self._attempts:
                    return False
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return False
                self._condition.wait(remaining)

    def wait_for_attempt(
        self,
        revision: int,
        *,
        timeout: float,
    ) -> WitnessAttempt:
        deadline = time.monotonic() + timeout
        with self._condition:
            while revision not in self._attempts:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError(
                        f"stationary witness revision {revision} timed out"
                    )
                self._condition.wait(remaining)
            return self._attempts[revision]

    def close(self) -> None:
        with self._condition:
            if self._closed:
                return
            self._closed = True
            self._pending = None
            if self._active is not None:
                self._active.cancel_requested_at = time.perf_counter()
                if self._active.workspace is not None:
                    self._active.workspace.cancel()
            self._condition.notify_all()
        self._thread.join()

    def _run(self) -> None:
        self._priority_lowered = (
            lower_current_thread_priority()
            if self._lower_priority
            else False
        )
        self._affinity_applied = (
            pin_current_thread_to_cpu(self._affinity_cpu)
            if self._affinity_cpu is not None
            else False
        )
        while True:
            with self._condition:
                while self._pending is None and not self._closed:
                    self._condition.wait()
                if self._closed and self._pending is None:
                    return
                assert self._pending is not None
                job = self._pending
                self._pending = None
                active = _Active(job)
                self._active = active
            attempt, publication, delivery_started = self._execute(active)
            with self._condition:
                locked_latency_ms = (
                    time.perf_counter() - delivery_started
                ) * 1000.0
                attempt = replace(
                    attempt,
                    latency_ms=locked_latency_ms,
                    publication_lock_wait_ms=max(
                        0.0,
                        locked_latency_ms - attempt.latency_ms,
                    ),
                )
                if (
                    publication is not None
                    and locked_latency_ms > self._deadline_ms
                ):
                    publication = None
                    attempt = replace(
                        attempt,
                        status="deadline",
                        error=(
                            "complete result reached publication lock after "
                            "the absolute deadline"
                        ),
                    )
                elif publication is not None:
                    publication = replace(
                        publication,
                        latency_ms=locked_latency_ms,
                        publication_lock_wait_ms=(
                            attempt.publication_lock_wait_ms
                        ),
                    )
                if (
                    publication is not None
                    and job.revision == self._newest_revision
                    and job.workload.identity == self._newest_identity
                ):
                    self._publication = publication
                elif publication is not None:
                    attempt = replace(
                        attempt,
                        status="stale",
                        error="completed revision is no longer newest",
                    )
                self._attempts[job.revision] = attempt
                if self._active is active:
                    self._active = None
                self._condition.notify_all()

    def _execute(
        self,
        active: _Active,
    ) -> tuple[
        WitnessAttempt,
        WitnessPublication | None,
        float,
    ]:
        job = active.job
        started = time.perf_counter()
        workspace: NativeStationaryWitnessWorkspace | None = None
        actions: list[NativeWitnessAction] = []
        evaluated = 0
        steps = 0
        tie_divergences = 0
        status = "error"
        error: str | None = None
        create_ms = 0.0
        query_decode_ms = 0.0
        native_kernel_ms = 0.0
        decode_ms = 0.0
        validation_ms = 0.0
        destroy_ms = 0.0
        cancel_ack_ms: float | None = None
        try:
            create_started = time.perf_counter()
            workspace = self._library.create_workspace(
                problem=job.workload.problem,
                decision_frame_support=self._decision_frame_support,
                continuation_action=job.workload.root.held_token,
            )
            create_ms = (time.perf_counter() - create_started) * 1000.0
            with self._condition:
                active.workspace = workspace
                stale_after_create = (
                    job.revision != self._newest_revision
                    or self._closed
                )
                if stale_after_create:
                    if active.cancel_requested_at is None:
                        active.cancel_requested_at = time.perf_counter()
                    workspace.cancel()
                self._condition.notify_all()

            query = job.workload.query
            expected_by_action = {
                witness.root_action: witness
                for witness in job.workload.expected.action_witnesses
            }
            for root_action in job.workload.expected.complete_root_actions:
                elapsed_ms = (time.perf_counter() - started) * 1000.0
                remaining_ms = self._deadline_ms - elapsed_ms
                if remaining_ms <= 0:
                    status = "deadline"
                    error = "absolute publication deadline elapsed"
                    break
                query_started = time.perf_counter()
                native = workspace.query(
                    frame=int(query["frame"]),
                    row=int(query["row"]),
                    column=int(query["column"]),
                    observed_action=str(query["observed_action"]),
                    pending_command=query["pending_command"],
                    root_action=root_action,
                    timeout_ms=max(1, math.ceil(remaining_ms)),
                )
                query_decode_ms += (
                    time.perf_counter() - query_started
                ) * 1000.0
                native_kernel_ms += native.native_call_ms
                decode_ms += native.decode_ms
                if native.status == PIPELINE_RESULT_CANCELLED:
                    status = "cancelled"
                    error = "native workspace acknowledged cancellation"
                    if active.cancel_requested_at is not None:
                        cancel_ack_ms = (
                            time.perf_counter()
                            - active.cancel_requested_at
                        ) * 1000.0
                    break
                if native.status == PIPELINE_RESULT_DEADLINE:
                    status = "deadline"
                    error = "native workspace deadline expired"
                    break
                if native.status != 0:
                    status = "error"
                    error = f"native witness returned status {native.status}"
                    break
                validation_started = time.perf_counter()
                validation = validate_action_witness(
                    native,
                    expected_by_action[root_action],
                    problem=job.workload.problem,
                    decision_frame_support=self._decision_frame_support,
                )
                validation_ms += (
                    time.perf_counter() - validation_started
                ) * 1000.0
                if not validation.exact_scalar_path:
                    tie_divergences += 1
                actions.append(native)
                evaluated += native.evaluated_state_count
                steps += len(native.steps)
            else:
                status = "complete"
        except Exception as caught:
            status = "error"
            error = f"{type(caught).__name__}: {caught}"
        finally:
            if workspace is not None:
                destroy_started = time.perf_counter()
                workspace.close()
                destroy_ms = (
                    time.perf_counter() - destroy_started
                ) * 1000.0

        latency_ms = (time.perf_counter() - started) * 1000.0
        if status == "complete" and latency_ms > self._deadline_ms:
            status = "deadline"
            error = "complete result arrived after absolute deadline"
        publication = (
            WitnessPublication(
                revision=job.revision,
                identity=job.workload.identity,
                actions=tuple(actions),
                latency_ms=latency_ms,
                workspace_create_ms=create_ms,
                native_query_decode_ms=query_decode_ms,
                native_kernel_ms=native_kernel_ms,
                decode_ms=decode_ms,
                validation_ms=validation_ms,
                workspace_destroy_ms=destroy_ms,
                publication_lock_wait_ms=0.0,
                evaluated_state_count=evaluated,
                path_step_count=steps,
                scalar_path_tie_divergence_count=tie_divergences,
            )
            if status == "complete" and len(actions) == 36
            else None
        )
        return (
            WitnessAttempt(
                revision=job.revision,
                identity=job.workload.identity,
                status=status,
                latency_ms=latency_ms,
                workspace_create_ms=create_ms,
                native_query_decode_ms=query_decode_ms,
                native_kernel_ms=native_kernel_ms,
                decode_ms=decode_ms,
                validation_ms=validation_ms,
                workspace_destroy_ms=destroy_ms,
                publication_lock_wait_ms=0.0,
                completed_action_count=len(actions),
                evaluated_state_count=evaluated,
                path_step_count=steps,
                scalar_path_tie_divergence_count=tie_divergences,
                cancel_ack_ms=cancel_ack_ms,
                error=error,
            ),
            publication,
            started,
        )


__all__ = [
    "NewestWitnessService",
    "WitnessAttempt",
    "WitnessPublication",
]
