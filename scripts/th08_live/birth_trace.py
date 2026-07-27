"""Compact trace records for the default-off bullet-birth audit."""

from __future__ import annotations

from dataclasses import dataclass

from th08_ecl_birth import (
    DeferredFireStateObservation,
    EclBirthLookaheadResult,
)

from .bullet_birth import BulletBirthObservation


BULLET_BIRTH_TRACE_SCHEMA_VERSION = 2
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
    intent_ms: float
    previous_emit_ms: float | None


def build_bullet_birth_trace_record(
    trace_input: BulletBirthTraceInput,
) -> dict[str, object]:
    """Serialize birth evidence without inferring an intent-to-slot join."""

    observation = trace_input.observation
    intent = trace_input.intent
    omitted_sources = [
        "non_spell_enemy_main_vm",
        "child_enemy_or_auxiliary_vm",
        "callback_or_interrupt_source",
        "non_ecl_native_source",
    ]
    if trace_input.deferred_fire_state.active is None:
        omitted_sources.append("deferred_emission_runtime_state")
    return {
        "kind": "bullet_birth_audit",
        "schema_version": BULLET_BIRTH_TRACE_SCHEMA_VERSION,
        "role": BULLET_BIRTH_TRACE_ROLE,
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
            "boundary": "post_issue_before_trace_flush",
            "observation": trace_input.observation_ms,
            "intent": trace_input.intent_ms,
            "build": None,
            "pre_emit_total": None,
            "previous_emit": trace_input.previous_emit_ms,
        },
        "join": {
            "status": "unresolved_offline_join_required",
            "coverage_authority": "none",
        },
    }


__all__ = [
    "BULLET_BIRTH_INTENT_SCOPE",
    "BULLET_BIRTH_POOL_SCOPE",
    "BULLET_BIRTH_TRACE_ROLE",
    "BULLET_BIRTH_TRACE_SCHEMA_VERSION",
    "BulletBirthTraceInput",
    "build_bullet_birth_trace_record",
]
