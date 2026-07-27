"""Single-owner lifecycle for live executors and background services."""

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any, Callable, Iterable

from touhou_control.candidate_verifier_service import (
    CandidateVerifierService,
)


class LiveServiceResources:
    """Own every executor and closeable background service for a live run."""

    def __init__(
        self,
        *,
        local_only: bool,
        postpublished_survival_shadow: bool,
        pipeline_prewarm_shadow: bool,
        candidate_verifier_shadow: bool,
        viability_audit_enabled: bool,
        candidate_horizon_frames: int,
        candidate_decision_frames: tuple[int, ...],
        candidate_timeout_ms: int,
        close_pipeline_prewarms: Callable[[tuple[Any, ...]], None],
        executor_factory: Callable[..., Any] = ThreadPoolExecutor,
        candidate_verifier_factory: Callable[..., Any] = (
            CandidateVerifierService
        ),
    ) -> None:
        self._close_pipeline_prewarms = close_pipeline_prewarms
        self.corridor_executor: Any | None = None
        self.survival_executor: Any | None = None
        self.pipeline_retire_executor: Any | None = None
        self.candidate_verifier: Any | None = None
        self.audit_executor: Any | None = None
        self.enemy_executor: Any | None = None
        self._closed = False
        try:
            if not local_only:
                self.corridor_executor = executor_factory(
                    max_workers=1,
                    thread_name_prefix="th08-corridor",
                )
                if postpublished_survival_shadow:
                    self.survival_executor = executor_factory(
                        max_workers=1,
                        thread_name_prefix="th08-survival-shadow",
                    )
                if pipeline_prewarm_shadow:
                    self.pipeline_retire_executor = executor_factory(
                        max_workers=1,
                        thread_name_prefix="th08-pipeline-retire",
                    )
                if candidate_verifier_shadow:
                    self.candidate_verifier = candidate_verifier_factory(
                        horizon_frames=candidate_horizon_frames,
                        decision_frame_support=candidate_decision_frames,
                        timeout_ms_per_candidate=candidate_timeout_ms,
                    )
            if viability_audit_enabled:
                self.audit_executor = executor_factory(
                    max_workers=1,
                    thread_name_prefix="th08-viability-audit",
                )
            self.enemy_executor = executor_factory(
                max_workers=1,
                thread_name_prefix="th08-enemy-sensor",
            )
        except BaseException:
            self.close()
            raise

    def retire_pipeline_solutions(
        self,
        candidates: tuple[Any | None, ...],
        retained: tuple[Any | None, ...] = (),
    ) -> None:
        """Close candidate prewarm services not shared by retained values."""

        retained_services = {
            id(solution.pipeline_prewarm_service)
            for solution in retained
            if (
                solution is not None
                and solution.pipeline_prewarm_service is not None
            )
        }
        retired = tuple(
            solution
            for solution in candidates
            if (
                solution is not None
                and solution.pipeline_prewarm_service is not None
                and id(solution.pipeline_prewarm_service)
                not in retained_services
            )
        )
        if not retired:
            return
        if self.pipeline_retire_executor is not None:
            self.pipeline_retire_executor.submit(
                self._close_pipeline_prewarms,
                retired,
            )
        else:
            self._close_pipeline_prewarms(retired)

    def close(
        self,
        *,
        corridor_future: Future[Any] | None = None,
        survival_future: Future[Any] | None = None,
        enemy_future: Future[Any] | None = None,
    ) -> None:
        """Cancel pending work and idempotently close owners in live order."""

        if self._closed:
            return
        self._closed = True
        cleanup_errors: list[BaseException] = []

        def attempt(operation: Callable[[], object]) -> None:
            try:
                operation()
            except BaseException as error:
                cleanup_errors.append(error)

        if corridor_future is not None:
            attempt(corridor_future.cancel)
        if survival_future is not None:
            attempt(survival_future.cancel)
        if self.survival_executor is not None:
            attempt(
                lambda: self.survival_executor.shutdown(
                    wait=True,
                    cancel_futures=True,
                )
            )
        if self.candidate_verifier is not None:
            attempt(self.candidate_verifier.close)
        if self.corridor_executor is not None:
            attempt(
                lambda: self.corridor_executor.shutdown(
                    wait=True,
                    cancel_futures=True,
                )
            )
        if (
            corridor_future is not None
            and corridor_future.done()
            and not corridor_future.cancelled()
        ):
            try:
                completed_solution = corridor_future.result()
            except BaseException:
                pass
            else:
                attempt(
                    lambda: self.retire_pipeline_solutions(
                        (completed_solution,)
                    )
                )
        if self.pipeline_retire_executor is not None:
            attempt(
                lambda: self.pipeline_retire_executor.shutdown(
                    wait=True,
                    cancel_futures=False,
                )
            )
        if self.audit_executor is not None:
            attempt(lambda: self.audit_executor.shutdown(wait=True))
        if enemy_future is not None:
            attempt(enemy_future.cancel)
        if self.enemy_executor is not None:
            attempt(
                lambda: self.enemy_executor.shutdown(
                    wait=True,
                    cancel_futures=True,
                )
            )
        if cleanup_errors:
            raise cleanup_errors[0]


__all__: Iterable[str] = ["LiveServiceResources"]
