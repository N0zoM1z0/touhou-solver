"""Compact trace records for the default-off bullet-birth audit."""

from __future__ import annotations

from dataclasses import dataclass

from th08_ecl_birth import (
    DeferredFireStateObservation,
    EclBirthLookaheadResult,
)

from .bullet_birth import BulletBirthObservation
from .bullet_birth_native import NATIVE_CALL_MODES
from .birth_contention import BirthObserverContention
from .derived_pattern_source import DerivedPatternSourceObservation


BULLET_BIRTH_TRACE_SCHEMA_VERSION = 10
BULLET_BIRTH_BASE_TRACE_SCHEMA_VERSION = 9
BULLET_BIRTH_TRACE_ROLE = "trace_only_no_action_authority"
BULLET_BIRTH_INTENT_SCOPE = "active_spell_enemy_main_vm_only"
BULLET_BIRTH_POOL_SCOPE = "all_1536_hostile_bullet_slots"


@dataclass(frozen=True)
class BulletBirthTraceInput:
    """Already-observed values for one post-issue diagnostic record."""

    frame: int
    snapshot_frame: int
    gameplay_epoch: int
    stage_route_index: int
    observation: BulletBirthObservation | None
    observation_error: str | None
    intent: EclBirthLookaheadResult | None
    intent_error: str | None
    deferred_fire_state: DeferredFireStateObservation
    spell_enemy_pointer: int
    ecl_frame_before: int | None
    ecl_frame_after: int | None
    ecl_event_frame_offset: int | None
    ecl_event_frame_uncertainty: int | None
    observation_ms: float
    observation_cpu_ms: float
    intent_ms: float
    previous_emit_ms: float | None
    observer_contention: BirthObserverContention
    observation_backend: str = "python"
    native_call_mode: str | None = None
    observation_diagnostics: dict[str, object] | None = None
    derived_source_observation: DerivedPatternSourceObservation | None = None
    derived_source_error: str | None = None
    derived_source_ms: float = 0.0
    derived_source_diagnostics: dict[str, object] | None = None


def birth_trace_requires_immediate_flush(
    *,
    observation_error: str | None,
    intent_error: str | None,
    derived_source_error: str | None = None,
) -> bool:
    """Flush failures now; ordinary rows flush with the decision this loop."""

    return bool(
        observation_error or intent_error or derived_source_error
    )


def build_bullet_birth_trace_record(
    trace_input: BulletBirthTraceInput,
) -> dict[str, object]:
    """Serialize birth evidence without inferring an intent-to-slot join."""

    observation = trace_input.observation
    intent = trace_input.intent
    derived_source = trace_input.derived_source_observation
    derived_source_enabled = (
        derived_source is not None
        or trace_input.derived_source_error is not None
    )
    if (
        derived_source is not None
        and trace_input.derived_source_error is not None
    ):
        raise ValueError(
            "derived-source observation may not accompany an error"
        )
    if trace_input.observation_backend not in {"python", "native"}:
        raise ValueError("unknown bullet-birth observation backend")
    if (
        trace_input.observation_backend == "native"
        and trace_input.native_call_mode not in NATIVE_CALL_MODES
    ):
        raise ValueError("native observation requires an explicit call mode")
    if (
        trace_input.observation_backend == "python"
        and trace_input.native_call_mode is not None
    ):
        raise ValueError("Python observation may not publish a native call mode")
    if (
        trace_input.observation_backend == "native"
        and observation is not None
        and trace_input.observation_error is None
        and trace_input.observation_diagnostics is None
    ):
        raise ValueError(
            "successful native observation requires diagnostics"
        )
    if (
        trace_input.observation_backend == "native"
        and observation is not None
        and trace_input.observation_error is None
        and (
            not isinstance(trace_input.observation_diagnostics, dict)
            or not isinstance(
                trace_input.observation_diagnostics.get("thread_cycles"),
                dict,
            )
        )
    ):
        raise ValueError(
            "schema-v9 native observation requires thread cycles"
        )
    if (
        trace_input.observation_backend == "python"
        and trace_input.observation_diagnostics is not None
    ):
        raise ValueError(
            "Python observation may not publish native diagnostics"
        )
    if (
        derived_source_enabled
        and trace_input.observation_backend == "native"
        and derived_source is not None
        and trace_input.derived_source_error is None
        and trace_input.derived_source_diagnostics is None
    ):
        raise ValueError(
            "successful native derived-source observation requires diagnostics"
        )
    if (
        trace_input.observation_backend == "python"
        and trace_input.derived_source_diagnostics is not None
    ):
        raise ValueError(
            "Python derived-source observation may not publish native diagnostics"
        )
    omitted_sources = [
        "non_spell_enemy_main_vm",
        "child_enemy_or_auxiliary_vm",
        "callback_or_interrupt_source",
        "non_ecl_native_source",
    ]
    if trace_input.deferred_fire_state.active is None:
        omitted_sources.append("deferred_emission_runtime_state")
    record: dict[str, object] = {
        "kind": "bullet_birth_audit",
        "schema_version": (
            BULLET_BIRTH_TRACE_SCHEMA_VERSION
            if derived_source_enabled
            else BULLET_BIRTH_BASE_TRACE_SCHEMA_VERSION
        ),
        "role": BULLET_BIRTH_TRACE_ROLE,
        "observation_backend": trace_input.observation_backend,
        "native_call_mode": trace_input.native_call_mode,
        "observation_diagnostics": trace_input.observation_diagnostics,
        "observer_contention": trace_input.observer_contention.record(),
        "frame": trace_input.frame,
        "snapshot_frame": trace_input.snapshot_frame,
        "gameplay_epoch": trace_input.gameplay_epoch,
        "stage_route_index": trace_input.stage_route_index,
        "scope": {
            "pool": BULLET_BIRTH_POOL_SCOPE,
            "intent": BULLET_BIRTH_INTENT_SCOPE,
            "omitted_sources": omitted_sources,
        },
        "alignment": {
            "ecl_frame_before": trace_input.ecl_frame_before,
            "ecl_frame_after": trace_input.ecl_frame_after,
            "ecl_event_frame_offset": trace_input.ecl_event_frame_offset,
            "ecl_event_frame_uncertainty": (
                trace_input.ecl_event_frame_uncertainty
            ),
        },
        "spell_enemy_pointer": trace_input.spell_enemy_pointer,
        "deferred_fire_state": trace_input.deferred_fire_state.record(),
        "observation": (
            observation.record() if observation is not None else None
        ),
        "observation_error": trace_input.observation_error,
        "intent": intent.record() if intent is not None else None,
        "intent_error": trace_input.intent_error,
        "counts": {
            "observed_evidence": (
                len(observation.evidence)
                if observation is not None
                else 0
            ),
            "visible_intents": len(intent.intents) if intent is not None else 0,
        },
        "timing_ms": {
            "boundary": "post_issue_before_same_iteration_decision_flush",
            "observation": trace_input.observation_ms,
            "observation_cpu": trace_input.observation_cpu_ms,
            "intent": trace_input.intent_ms,
            "build": None,
            "pre_emit_total": None,
            "previous_emit": trace_input.previous_emit_ms,
        },
        "flush_policy": (
            "errors_immediate_otherwise_same_iteration_decision_flush"
        ),
        "join": {
            "status": "unresolved_offline_join_required",
            "coverage_authority": "none",
        },
    }
    if derived_source_enabled:
        counts = record["counts"]
        timing = record["timing_ms"]
        assert isinstance(counts, dict)
        assert isinstance(timing, dict)
        record.update(
            {
                "derived_source_observation": (
                    derived_source.record()
                    if derived_source is not None
                    else None
                ),
                "derived_source_error": trace_input.derived_source_error,
                "derived_source_diagnostics": (
                    trace_input.derived_source_diagnostics
                ),
            }
        )
        counts["ready_derived_sources"] = (
            len(derived_source.candidates)
            if derived_source is not None
            else 0
        )
        timing["derived_source_observation"] = (
            trace_input.derived_source_ms
        )
        timing["combined_pool_observation"] = (
            trace_input.observation_ms + trace_input.derived_source_ms
        )
    return record


__all__ = [
    "BULLET_BIRTH_INTENT_SCOPE",
    "BULLET_BIRTH_BASE_TRACE_SCHEMA_VERSION",
    "BULLET_BIRTH_POOL_SCOPE",
    "BULLET_BIRTH_TRACE_ROLE",
    "BULLET_BIRTH_TRACE_SCHEMA_VERSION",
    "BulletBirthTraceInput",
    "birth_trace_requires_immediate_flush",
    "build_bullet_birth_trace_record",
]
