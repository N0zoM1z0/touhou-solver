"""Post-issue orchestration for action-neutral bullet-birth trace rows."""

from __future__ import annotations

import struct
import time
from concurrent.futures import Future
from dataclasses import dataclass
from typing import Any, Callable

from th08_ecl_birth import (
    DeferredFireStateObservation,
    EclBirthLookaheadResult,
    analyze_ecl_birth_intents,
    observe_deferred_fire_state,
)
from th08_ecl_runtime import EclVmSnapshot

from .birth_contention import (
    BirthObserverContention,
    BirthObserverFutureStates,
    capture_birth_observer_future_states,
)
from .birth_trace import (
    BulletBirthTraceInput,
    birth_trace_requires_immediate_flush,
    build_bullet_birth_trace_record,
)
from .bullet_birth import BulletBirthObservation, BulletBirthTracker
from .bullet_birth_native import (
    NativeBulletBirthDiagnostics,
    NativeBulletBirthTracker,
)
from .derived_pattern_source import (
    DerivedPatternSourceObservation,
    observe_derived_pattern_sources,
)
from .derived_pattern_source_native import (
    NativeDerivedPatternSourceObserver,
)
from .enemy_ecl_inventory import EnemyMainEclVmInventory
from .trace import TraceSink


_OBSERVATION_ERRORS = (
    RuntimeError,
    TypeError,
    ValueError,
    struct.error,
)
_INTENT_ERRORS = (
    OSError,
    RuntimeError,
    TypeError,
    ValueError,
    struct.error,
)


@dataclass(frozen=True)
class BulletBirthStageRequest:
    """Already captured state for one post-issue diagnostic transaction."""

    trace_sink: TraceSink
    tracker: BulletBirthTracker | NativeBulletBirthTracker | None
    derived_source_observer: NativeDerivedPatternSourceObserver | None
    trace_derived_sources: bool
    bullet_blob: Any
    bullet_frame_before: int
    bullet_frame_after: int
    corridor_future: Future[Any] | None
    survival_future: Future[Any] | None
    enemy_future: Future[Any] | None
    ecl_vm_snapshot: EclVmSnapshot | None
    instruction_at: Callable[[int], object]
    intent_horizon_frames: int
    difficulty_index: int
    spell_enemy_pointer: int
    observed_enemy_pointer: int | None
    observed_enemy_flags: int | None
    boss_guard_frame_before: int | None
    boss_guard_frame_after: int | None
    ecl_frame_before: int | None
    ecl_frame_after: int | None
    ecl_event_frame_offset: int | None
    ecl_event_frame_uncertainty: int | None
    issue_frame: int
    snapshot_frame: int
    gameplay_epoch: int
    stage_route_index: int
    observation_backend: str
    native_call_mode: str
    previous_emit_ms: float | None
    nonspell_main_vm_inventory: EnemyMainEclVmInventory | None
    enemy_prefix_frame_before: int
    enemy_prefix_frame_after: int
    enemy_prefix_capture_ms: float


@dataclass(frozen=True)
class BulletBirthStageDependencies:
    observe_deferred_fire: Callable[..., DeferredFireStateObservation] = (
        observe_deferred_fire_state
    )
    capture_future_states: Callable[
        ..., BirthObserverFutureStates
    ] = capture_birth_observer_future_states
    observe_derived_sources: Callable[
        ..., DerivedPatternSourceObservation
    ] = observe_derived_pattern_sources
    analyze_intents: Callable[..., EclBirthLookaheadResult] = (
        analyze_ecl_birth_intents
    )
    build_record: Callable[
        [BulletBirthTraceInput], dict[str, object]
    ] = build_bullet_birth_trace_record
    requires_immediate_flush: Callable[..., bool] = (
        birth_trace_requires_immediate_flush
    )
    native_tracker_type: type = NativeBulletBirthTracker
    wall_clock: Callable[[], float] = time.perf_counter
    cpu_clock: Callable[[], float] = time.thread_time


@dataclass(frozen=True)
class BulletBirthStageResult:
    """Published row plus error/timing evidence needed by tests and audits."""

    record: dict[str, object]
    emit_ms: float
    observation_error: str | None
    intent_error: str | None
    derived_source_error: str | None


def run_bullet_birth_stage(
    request: BulletBirthStageRequest,
    *,
    dependencies: BulletBirthStageDependencies = (
        BulletBirthStageDependencies()
    ),
) -> BulletBirthStageResult:
    """Observe and publish one birth row after the current action is issued."""

    observation: BulletBirthObservation | None = None
    observation_error: str | None = None
    native_diagnostics: NativeBulletBirthDiagnostics | None = None
    observation_ms = 0.0
    observation_cpu_ms = 0.0
    derived_observation: DerivedPatternSourceObservation | None = None
    derived_error: str | None = None
    derived_ms = 0.0
    derived_diagnostics: dict[str, object] | None = None
    intent: EclBirthLookaheadResult | None = None
    intent_error: str | None = None
    intent_ms = 0.0

    deferred_fire_state = dependencies.observe_deferred_fire(
        spell_enemy_pointer=request.spell_enemy_pointer,
        observed_enemy_pointer=request.observed_enemy_pointer,
        enemy_flags=request.observed_enemy_flags,
        frame_before=request.boss_guard_frame_before,
        frame_after=request.boss_guard_frame_after,
        ecl_frame_before=request.ecl_frame_before,
        ecl_frame_after=request.ecl_frame_after,
    )
    if request.tracker is not None:
        observation_started = dependencies.wall_clock()
        observation_cpu_started = dependencies.cpu_clock()
        contention_before = dependencies.capture_future_states(
            corridor_future=request.corridor_future,
            survival_future=request.survival_future,
            enemy_future=request.enemy_future,
        )
        try:
            observation = request.tracker.observe(
                request.bullet_blob,
                frame_before=request.bullet_frame_before,
                frame_after=request.bullet_frame_after,
            )
            if isinstance(
                request.tracker,
                dependencies.native_tracker_type,
            ):
                native_diagnostics = request.tracker.diagnostics()
        except _OBSERVATION_ERRORS as error:
            request.tracker.reset()
            observation_error = f"{type(error).__name__}: {error}"
        contention_after = dependencies.capture_future_states(
            corridor_future=request.corridor_future,
            survival_future=request.survival_future,
            enemy_future=request.enemy_future,
        )
        observation_ms = (
            dependencies.wall_clock() - observation_started
        ) * 1000.0
        observation_cpu_ms = (
            dependencies.cpu_clock() - observation_cpu_started
        ) * 1000.0
    else:
        contention_before = dependencies.capture_future_states(
            corridor_future=request.corridor_future,
            survival_future=request.survival_future,
            enemy_future=request.enemy_future,
        )
        contention_after = dependencies.capture_future_states(
            corridor_future=request.corridor_future,
            survival_future=request.survival_future,
            enemy_future=request.enemy_future,
        )
    contention = BirthObserverContention(
        contention_before,
        contention_after,
    )

    if request.trace_derived_sources:
        derived_started = dependencies.wall_clock()
        try:
            if request.derived_source_observer is not None:
                derived_observation = (
                    request.derived_source_observer.observe(
                        request.bullet_blob,
                        frame_before=request.bullet_frame_before,
                        frame_after=request.bullet_frame_after,
                    )
                )
            else:
                derived_observation = (
                    dependencies.observe_derived_sources(
                        request.bullet_blob,
                        frame_before=request.bullet_frame_before,
                        frame_after=request.bullet_frame_after,
                    )
                )
        except _OBSERVATION_ERRORS as error:
            derived_error = f"{type(error).__name__}: {error}"
        derived_ms = (
            dependencies.wall_clock() - derived_started
        ) * 1000.0
        if (
            request.derived_source_observer is not None
            and derived_observation is not None
            and derived_error is None
        ):
            derived_diagnostics = (
                request.derived_source_observer.diagnostics().record(
                    observation_ms=derived_ms,
                )
            )

    if request.ecl_vm_snapshot is not None:
        intent_started = dependencies.wall_clock()
        try:
            intent = dependencies.analyze_intents(
                request.ecl_vm_snapshot,
                instruction_at=request.instruction_at,
                horizon_frames=request.intent_horizon_frames,
                active_difficulty_mask=1 << request.difficulty_index,
                deferred_fire_active=deferred_fire_state.active,
                spell_active=True,
                minimum_fire_distance_clear=None,
                fire_filter_clear=None,
                available_slots=None,
                template_geometry_resolved=False,
                emission_origin_resolved=False,
            )
        except _INTENT_ERRORS as error:
            intent_error = f"{type(error).__name__}: {error}"
        intent_ms = (
            dependencies.wall_clock() - intent_started
        ) * 1000.0

    build_started = dependencies.wall_clock()
    record = dependencies.build_record(
        BulletBirthTraceInput(
            frame=request.issue_frame,
            snapshot_frame=request.snapshot_frame,
            gameplay_epoch=request.gameplay_epoch,
            stage_route_index=request.stage_route_index,
            observation=observation,
            observation_error=observation_error,
            intent=intent,
            intent_error=intent_error,
            deferred_fire_state=deferred_fire_state,
            spell_enemy_pointer=request.spell_enemy_pointer,
            ecl_frame_before=request.ecl_frame_before,
            ecl_frame_after=request.ecl_frame_after,
            ecl_event_frame_offset=request.ecl_event_frame_offset,
            ecl_event_frame_uncertainty=(
                request.ecl_event_frame_uncertainty
            ),
            observation_ms=observation_ms,
            observation_cpu_ms=observation_cpu_ms,
            intent_ms=intent_ms,
            previous_emit_ms=request.previous_emit_ms,
            observer_contention=contention,
            observation_backend=request.observation_backend,
            native_call_mode=(
                request.native_call_mode
                if request.observation_backend == "native"
                else None
            ),
            observation_diagnostics=(
                native_diagnostics.record(observation_ms=observation_ms)
                if native_diagnostics is not None
                else None
            ),
            derived_source_observation=derived_observation,
            derived_source_error=derived_error,
            derived_source_ms=derived_ms,
            derived_source_diagnostics=derived_diagnostics,
            nonspell_main_vm_inventory=(
                request.nonspell_main_vm_inventory
            ),
            enemy_prefix_frame_before=request.enemy_prefix_frame_before,
            enemy_prefix_frame_after=request.enemy_prefix_frame_after,
            enemy_prefix_capture_ms=request.enemy_prefix_capture_ms,
        )
    )
    build_ms = (dependencies.wall_clock() - build_started) * 1000.0
    timing = record["timing_ms"]
    assert isinstance(timing, dict)
    timing["build"] = build_ms
    timing["pre_emit_total"] = (
        observation_ms + derived_ms + intent_ms + build_ms
    )
    emit_ms = request.trace_sink.emit(
        record,
        flush=dependencies.requires_immediate_flush(
            observation_error=observation_error,
            intent_error=intent_error,
            derived_source_error=derived_error,
        ),
        measure=True,
    )
    return BulletBirthStageResult(
        record=record,
        emit_ms=emit_ms,
        observation_error=observation_error,
        intent_error=intent_error,
        derived_source_error=derived_error,
    )


__all__ = [
    "BulletBirthStageDependencies",
    "BulletBirthStageRequest",
    "BulletBirthStageResult",
    "run_bullet_birth_stage",
]
