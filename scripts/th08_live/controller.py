#!/usr/bin/env python3
"""TH08 route-2 live controller implementation and compatibility surface.

The controller is a receding-horizon smoke agent, not the final global solver.
It reads game state and projectile pools, then uses physical ``SendInput``
events. It never writes target memory and aborts on identity, route, gameplay,
or foreground-window divergence.
"""

from __future__ import annotations

import argparse
import math
import struct
import time
from collections import deque
from concurrent.futures import Future
from dataclasses import replace
from pathlib import Path

import numpy as np

from th08_boss_phase import (
    BossPhaseSnapshot,
    capture_boss_phase_snapshot,
    serialize_boss_phase_snapshot,
)
from th08_corridor_runtime import (
    CorridorCommitment,
    CorridorSolution,
    LIVE_REFINEMENT_GRID_STEPS,
    LIVE_SURVIVAL_LABELS,
    SHADOW_REFINEMENT_GRID_STEPS,
    SHADOW_SURVIVAL_LABELS,
    corridor_candidate_verifier_target as _corridor_candidate_verifier_target,
    corridor_policy_status as _corridor_policy_status,  # noqa: F401
    corridor_pipeline_prewarm_retarget as _corridor_pipeline_prewarm_retarget,
    corridor_submit_due as _corridor_submit_due,
    corridor_target as _corridor_target,  # noqa: F401 - compatibility export
    corridor_viability_query as _corridor_viability_query,  # noqa: F401
    require_corridor_background_priority,
    solve_corridor as _solve_corridor,
    solve_postpublished_survival as _solve_postpublished_survival,
    stage_corridor_solution as _stage_corridor_solution,
    close_retired_pipeline_prewarms as _close_retired_pipeline_prewarms,
)
from th08_corridor_adapter import TH08_CORRIDOR_CONFIG
from th08_ecl_birth import (
    analyze_ecl_birth_intents,
    observe_deferred_fire_state,
)
from th08_ecl_runtime import (
    EclLookaheadResult,
    EclInstructionCache,
    EclVmSnapshot,
    TaggedVelocityToggle,
)
from th08_laser_runtime import (
    Laser,
    PackedLaserFrame as _PackedLaserFrame,
    build_laser_collision_frames,  # noqa: F401 - compatibility export
    build_packed_laser_collision_frames as _build_packed_laser_collision_frames,
    pack_laser_frame as _pack_laser_frame,  # noqa: F401
    serialize_laser_trace,
)
from th08_live import (
    AutoConfirmPulse,  # noqa: F401 - compatibility export
    Bullet,
    BULLET_POOL_SIZE,  # noqa: F401 - compatibility export
    BULLET_STRIDE,  # noqa: F401 - compatibility export
    ENEMY_MAX_OBSERVED_WORLD_SPEED,
    EnemyBody,
    EnemyBodyModeMemory,
    EnemyPoolSnapshot,
    GameplaySceneGuard,  # noqa: F401 - compatibility export
    INPUT_CLOCK_SHADOW_ROLE,
    IssueController,
    Item,
    LiveServiceResources,
    LiveSession,
    PolicyCoordinator,
    PolicyQueryRequest,
    PackedBulletSnapshot,  # noqa: F401 - compatibility export
    SceneClockCoordinator,
    Sensor,
    SpellEnemyBodyGuard,
    TraceSink,
    auto_confirm_eligible as _auto_confirm_eligible,
    frozen_auto_confirm_eligible as _frozen_auto_confirm_eligible,
    input_clock_message_key as _input_clock_message_key,
    semantic_clock_observation as _semantic_clock_observation,
    serialize_bullet_trace,
    serialize_semantic_clock_event as _serialize_semantic_clock_event,
    serialize_semantic_clock_observation as _serialize_semantic_clock_observation,
)
from th08_live.birth_trace import (
    birth_trace_requires_immediate_flush,
    build_bullet_birth_trace_record,
)
from th08_live.birth_contention import (
    capture_birth_observer_future_states,
)
from th08_live.bullet_birth_stage import (
    BulletBirthStageDependencies,
    BulletBirthStageRequest,
    run_bullet_birth_stage,
)
from th08_live.enemy_combat_progress_stage import (
    EnemyCombatProgressStageRequest,
    run_enemy_combat_progress_stage,
)
from th08_live.runtime_ecl_identity import (
    RuntimeEclIdentityService,
    RuntimeEclPhysicalProvenance,
)
from th08_live.auxiliary_vm import (
    AuxiliaryVmBatchTraceService,
    native_auxiliary_vm_batch_available,
)
from th08_live.derived_pattern_source import observe_derived_pattern_sources
from th08_live.derived_pattern_source_native import (
    NativeDerivedPatternSourceObserver,
)
from th08_live.bullet_birth import (
    BulletBirthTracker,
)
from th08_live.bullet_birth_native import (
    NATIVE_CALL_MODES,
    NATIVE_CALL_MODE_GIL_HELD,
    NATIVE_CALL_MODE_GIL_RELEASED,
    NativeBulletBirthTracker,
    native_bullet_birth_available,
)
from th08_live.ecl_capture import capture_main_ecl
from th08_live.bullet_decode import (  # noqa: F401
    BULLET_ANGLE_OFFSET,
    BULLET_CALLBACK_AUX_STATE_OFFSET,
    BULLET_CALLBACK_PHASE_STATE_OFFSET,
    BULLET_GEOMETRY_OFFSET,
    BULLET_ORIGINAL_TRANSFORM_FLAGS_OFFSET,
    BULLET_POSITION_OFFSET,
    BULLET_SPEED_OFFSET,
    BULLET_STATE_OFFSET,
    BULLET_STOP_ANGLE_OPERAND_OFFSET,
    BULLET_STOP_DURATION_OFFSET,
    BULLET_STOP_REPEAT_COUNT_OFFSET,
    BULLET_STOP_REPEAT_LIMIT_OFFSET,
    BULLET_STOP_RESUME_SPEED_OFFSET,
    BULLET_STOP_TIMER_ELAPSED_OFFSET,
    BULLET_STOP_TIMER_FRACTION_OFFSET,
    BULLET_TRANSFORM_FLAGS_OFFSET,
    BULLET_TRANSFORM_PROGRAM_OFFSET,
    BULLET_TRANSFORM_QUEUE_CURSOR_OFFSET,
    BULLET_VELOCITY_OFFSET,
    NATIVE_PACKED_BULLET_MIN_COUNT,
    PLANNING_BULLET_VECTOR_THRESHOLD,
    attach_tagged_velocity_toggles,
    decode_bullets,
    decode_live_planning_bullets,
    decode_packed_bullets,
    decode_planning_bullets as _decode_planning_bullets,
    finite as _finite,
    native_bullet_half_extents as _native_bullet_half_extents,
    planning_bullet_active_slots as _planning_bullet_active_slots,
)
from th08_live.candidate_trace import (
    build_candidate_verifier_trace_record,
    candidate_outcome_record as _candidate_outcome_record,  # noqa: F401
    candidate_shadow_publications as _candidate_shadow_publications,
    candidate_snapshot_record as _candidate_snapshot_record,  # noqa: F401
)
from th08_live.corridor_trace import build_corridor_trace_record
from th08_live.decision_control_trace import (
    DecisionControlTraceInput,
    build_decision_control_trace_fields,
)
from th08_live.decision_trace import (
    DecisionTimingTraceInput,
    build_decision_timing_trace_fields,
    build_optional_hazard_trace_fields,
)
from th08_live.hazard_decode import (  # noqa: F401
    ITEM_ACTIVE_OFFSET,
    ITEM_FULL_VALUE_OFFSET,
    ITEM_MOTION_STATE_OFFSET,
    ITEM_POOL_SIZE,
    ITEM_POSITION_OFFSET,
    ITEM_STRIDE,
    ITEM_TYPE_OFFSET,
    ITEM_VELOCITY_OFFSET,
    LASER_ACTIVE_FRAMES_OFFSET,
    LASER_ACTIVE_OFFSET,
    LASER_ANGLE_OFFSET,
    LASER_COLLISION_DISABLE_FRAME_OFFSET,
    LASER_COLLISION_ENABLE_FRAME_OFFSET,
    LASER_COLLISION_FLAG_OFFSET,
    LASER_CURRENT_WIDTH_OFFSET,
    LASER_FADE_FRAMES_OFFSET,
    LASER_FLAGS_OFFSET,
    LASER_HEAD_OFFSET,
    LASER_MAXIMUM_LENGTH_OFFSET,
    LASER_ORIGIN_OFFSET,
    LASER_PHASE_OFFSET,
    LASER_POOL_SIZE,
    LASER_SPEED_OFFSET,
    LASER_STRIDE,
    LASER_TAIL_OFFSET,
    LASER_TIMER_FRACTION_OFFSET,
    LASER_TIMER_OFFSET,
    LASER_WARMUP_FRAMES_OFFSET,
    LASER_WIDTH_OFFSET,
    decode_items,
    decode_lasers,
)
from th08_live.fresh_issue import (
    FreshEnemyIssueDependencies,
    recertify_fresh_enemy_prefix,
)
from th08_live.iteration import (
    CapturedIteration,
    FreshIssueResult,  # noqa: F401 - compatibility export
    PublishedGuidance,
    ServiceUpdate,
)
from th08_live.issue_overrides import (
    apply_deadline_hold,
    apply_post_hit_input_overrides,
)
from th08_live.issue_stage import (
    PhysicalIssueRequest,
    commit_physical_issue,
    observe_action_issue,
)
from th08_live.local_certificates import (
    control_prefix_hazards as _control_prefix_hazards_impl,
    legacy_robust_action_certificates as _legacy_robust_action_certificates_impl,
    robust_action_certificates as _robust_action_certificates_impl,
)
from th08_live.local_hazards import (  # noqa: F401
    _aabb_clearance,
    _build_bullet_frames,
    _item_value,
    _native_hazards_for_positions,
    _numpy_hazards_for_positions,
    _project_item,
    _segment_clearance,
    _select_items,
)
from th08_live.local_objectives import (
    COLLECTION_HALF_WIDTH,
    ITEM_APPROACH_POTENTIAL_WEIGHT,  # noqa: F401 - compatibility export
    ITEM_OBJECTIVES_ENABLED,
    ITEM_SAFETY_CLEARANCE,
    ITEM_UTILITY_SATURATION,  # noqa: F401 - compatibility export
    ITEM_UTILITY_WEIGHT,  # noqa: F401 - compatibility export
    item_potential as _item_potential,  # noqa: F401
    node_key as _node_key,
    terminal_threat_degeneracy as _terminal_threat_degeneracy,
    terminal_threat_scores as _terminal_threat_scores_impl,
)
from th08_live.movement import (
    BOMB,
    DOWN,
    FOCUS,
    FOCUSED_CARDINAL_SPEED,  # noqa: F401 - compatibility export
    FOCUSED_DIAGONAL_SPEED,  # noqa: F401 - compatibility export
    LEFT,
    LOCAL_PIPELINE_STATE_ACTIONS as _LOCAL_PIPELINE_STATE_ACTIONS,  # noqa: F401
    PLANNER_ACTIONS as _PLANNER_ACTIONS,
    PLAYER_RADIUS,
    PLAYFIELD_BOTTOM,
    PLAYFIELD_LEFT,
    PLAYFIELD_RIGHT,
    PLAYFIELD_TOP,
    RIGHT,
    SHOT,
    UNFOCUSED_CARDINAL_SPEED,
    UNFOCUSED_DIAGONAL_SPEED,
    UP,
    action_name_from_mask as _action_name_from_mask,
    boundary_control_reserve_deficit as _boundary_control_reserve_deficit,
    boundary_risk as _boundary_risk,
    boundary_risk_for_positions as _boundary_risk_for_positions,  # noqa: F401
    directions_opposed as _directions_opposed,
    local_pipeline_action_from_mask as _local_pipeline_action_from_mask,
    minimum_travel_frames as _minimum_travel_frames,
    project_player_for_read_lag as _project_player_for_read_lag,
)
from th08_live.sensing_trace import (
    SensingTraceInput,
    build_sensing_trace_fields,
)
from th08_live.enemy_sensor import (  # noqa: F401
    ENEMY_ACTIVE_FLAG,
    ENEMY_BODY_READ_OFFSET,
    ENEMY_BODY_READ_SIZE,
    ENEMY_CONTACT_BLOCKING_FLAGS,
    ENEMY_CONTACT_ENABLED_FLAG,
    ENEMY_CONTACT_SIZE_OFFSET,
    ENEMY_FLAGS_OFFSET,
    ENEMY_LOCAL_PREFIX_SIZE,
    ENEMY_POOL_BASE,
    ENEMY_POOL_SIZE,
    ENEMY_POSITION_OFFSET,
    ENEMY_STRIDE,
    ENEMY_VELOCITY_OFFSET,
    PLAYER_LETHAL_AABB_OFFSET,
    PLAYER_LETHAL_AABB_SIZE,
    _serialized_enemy_bodies,
    capture_enemy_pool_prefix_contiguous,
    capture_enemy_pool_snapshot,
    capture_enemy_pool_snapshot_contiguous,
    capture_enemy_pool_snapshot_sparse,
    capture_hit_contact_observation,
    decode_enemy_bodies,
    decode_enemy_body,
    decode_player_lethal_aabb,
    decode_spell_enemy_body_guard,
    enemy_body_contact_enabled,
    enemy_pointer_in_scanned_pool,
    enemy_pool_snapshot_changes,
    issue_enemy_snapshot_changes,
    merge_enemy_pool_prefix,
    merge_spell_enemy_body_guard,
    project_enemy_pool_snapshot,
    read_enemy_bodies_sparse,
    read_enemy_body_guard,
    read_spell_enemy_bodies,
    read_spell_enemy_body_guard,
)
from th08_live.planner_pass import (
    LocalCertificateTimingAccumulator as _LocalCertificateTimingAccumulator,
    PlannerModeTransition as _PlannerModeTransition,
    PlannerPassDependencies,
    _run_local_planner_pass as _run_local_planner_pass_impl,
)
from th08_live.pipeline_shadow import build_pipeline_shadow_snapshot
from th08_local_planner import (  # noqa: F401
    ActuatorPipeline,
    BaselineBeamContext,
    CompletedServiceResults,
    CompletedSupplementalLookup,
    DamageDecisionFields,
    Decision,
    DecisionTelemetry,  # noqa: F401 - compatibility export
    EndpointRanker,
    GlobalGuidance,
    IssueAdapter,
    IssueRecertification,
    IssueRequest,
    IssueTransaction,
    IssuedDecision,
    LocalCertificateTiming,
    LocalPlannerRequest,
    LocalProposal,
    ObjectiveContext,
    PhysicalHazardSnapshot,
    PlannerAction,
    PlannerConfig,
    PlannerMode,
    PlannerPassPreparation,
    ProposalAssemblyContext,
    RobustActionCertificate,
    SearchNode,
    SupplementalDecisionFields,
    assemble_local_decision,
    prepare_planner_pass,
    run_baseline_beam,
    lookup_completed_supplemental,
)
from th08_runtime_agent import (
    ADDR_ENGINE_FLAGS,
    ADDR_ENEMY_MANAGER_FRAME,
    ADDR_PLAYER,
    ADDR_STAGE_ROUTE_INDEX,
    PLAYER_BOMB_ACTIVE_OFFSET,
    SUPPORTED_INPUT_MASK,
    TARGET_EXE,
    _require_foreground,
    capture_input_clock_shadow,
    observe_state,
    send_scan_key,
    verify_target,
)
from touhou_control import native_backend
from touhou_control.async_policy import (
    AsyncPolicyLead,
    delay_support_envelope,
)
from touhou_control.delay import AdaptiveControlDelay
from touhou_control.query_survival import PendingCommand
from touhou_control.candidate_verifier_service import (
    CandidateVerifierOutcome,
    CandidateVerifierSnapshot,
    CandidateVerifierTarget,
)
from touhou_control.epochs import (
    ActionIssueAlignment,  # noqa: F401 - compatibility export
    FrameWindow,
    HazardEpochAlignment,
)
from touhou_control.input_clock import (
    SemanticClockEvent,
    SemanticClockObservation,
)
from touhou_control.local_pipeline_oracle import LocalPipelineRoot
from touhou_control.phase_progress import (  # noqa: F401
    PhaseProgressObservation,
    PhaseProgressTracker,
    ProgressCandidate,
    select_progress_action,
)
from touhou_control.supplemental_local_beam import (  # noqa: F401
    ExactVersionSupplementalService,
    SupplementalAction,
    SupplementalNode,
    search_supplemental_local_beam,
    search_supplemental_local_beam_native,
)
ECL_CALLBACK_LOOKAHEAD_FRAMES = 256
ECL_BIRTH_LOOKAHEAD_FRAMES = 80
INPUT_CLOCK_SHADOW_WALL_CUT_SECONDS = 0.05

PLANNER_HORIZON = 10
PLANNER_THREAT_HORIZON = 32
PLANNER_BEAM_WIDTH = 24
PLANNER_ACTION_HOLD = 2
LIVE_ACTION_HOLD_DEFAULT = 3
LIVE_ACTION_HOLD_MAX = 6
# The previous input remains active while the current snapshot is read and
# planned. Live control estimates this prefix independently from action hold.
CONTROL_DELAY_FRAMES = 2
LIVE_CONTROL_DELAY_MIN = 1
LIVE_CONTROL_DELAY_MAX = 6
LIVE_CONTROL_DELAY_WINDOW = 120
LIVE_CONTROL_DELAY_GUARD_FRAMES = 600
# A native pool read normally spans zero or one manager update. A wider bound
# tolerates scheduler stalls but rejects known +1800 logical timer jumps that
# splice source state and hazard pools from different gameplay epochs.
MAX_SENSOR_EPOCH_EXTENT_FRAMES = 8
# A normal 60 Hz counter cannot advance this far during one local planning
# call. This catches logical +1800 jumps that occur after sensor capture but
# before input issue without mislabeling an ordinary 7..20-frame overrun as a
# new gameplay epoch.
MAX_ACTION_CONTIGUOUS_ADVANCE_FRAMES = 120
# Below this active-pool density, consolidated scalar unpacking is faster
# than allocating NumPy gather arrays. Retained synthetic sweeps place the
# crossover between 400 and 600 records on the current host.
# A rolling async policy can outlive several estimator updates. Cover the
# complete configured support instead of assuming only one-step drift.
ASYNC_POLICY_DELAY_PADDING = (
    LIVE_CONTROL_DELAY_MAX - LIVE_CONTROL_DELAY_MIN
)
ENEMY_SENSOR_INTERVAL_FRAMES = 4
# Keep the single worker work-conserving. There is never more than one queued
# solve, so native solve throughput remains the hard rate limit.
CORRIDOR_REPLAN_FRAMES = TH08_CORRIDOR_CONFIG.frames_per_layer
CORRIDOR_LOOKAHEAD_FRAMES = 16
CORRIDOR_MAX_AGE_FRAMES = (
    TH08_CORRIDOR_CONFIG.horizon_frames - 1
)
CORRIDOR_POLICY_LEAD_INITIAL_FRAMES = 80
CORRIDOR_POLICY_OVERLAP_FRAMES = 8
CORRIDOR_POLICY_MINIMUM_LEAD_FRAMES = max(
    2 * TH08_CORRIDOR_CONFIG.frames_per_layer,
    LIVE_CONTROL_DELAY_MAX + LIVE_ACTION_HOLD_MAX,
)
# An ordinary enemy slot can clear its active/contact mode while its geometry
# continues and later re-enable inside the current robust-policy horizon.
# Retain the last observed mode envelope for exactly that modeled horizon.
ENEMY_DORMANT_MEMORY_FRAMES = TH08_CORRIDOR_CONFIG.horizon_frames
CORRIDOR_MIN_COMMIT_FRAMES = 32
CORRIDOR_INITIAL_SUBMIT_FRAME = -1_000_000
CANDIDATE_VERIFIER_HORIZON_FRAMES = 32
CANDIDATE_VERIFIER_DECISION_FRAMES = (4, 5, 6)
CANDIDATE_VERIFIER_TIMEOUT_MS = 10
STAGE_TRANSITION_TIMEOUT_SECONDS = 90.0
TERMINAL_INACTIVE_GRACE_SECONDS = 5.0

# Route-2 stage resource indices. Stage 4B can feed Stage 5 but is not reached
# by Sakuya/Remilia; retaining it makes the scene guard valid for either branch.
ROUTE2_STAGE_SUCCESSORS = {
    0: 1,
    1: 2,
    2: 3,
    3: 5,
    4: 5,
    5: 7,
}



def _local_certificate_timing_record(
    timing: LocalCertificateTiming,
) -> dict[str, int | float]:
    segmented_ms = (
        timing.validation_ms
        + timing.hazard_projection_ms
        + timing.branch_setup_ms
        + timing.geometry_kernel_ms
        + timing.reduction_ms
    )
    return {
        "calls": timing.calls,
        "explicit_root_calls": timing.explicit_root_calls,
        "maximum_branch_count": timing.maximum_branch_count,
        "shared_laser_projection_ms": (
            timing.shared_laser_projection_ms
        ),
        "validation_ms": timing.validation_ms,
        "hazard_projection_ms": timing.hazard_projection_ms,
        "branch_setup_ms": timing.branch_setup_ms,
        "geometry_kernel_ms": timing.geometry_kernel_ms,
        "reduction_ms": timing.reduction_ms,
        "certificate_total_ms": timing.certificate_total_ms,
        "control_prefix_ms": timing.control_prefix_ms,
        "planning_bullet_projection_ms": (
            timing.planning_bullet_projection_ms
        ),
        "beam_search_ms": timing.beam_search_ms,
        "supplemental_beam_ms": timing.supplemental_beam_ms,
        "terminal_threat_ms": timing.terminal_threat_ms,
        "selection_finalize_ms": timing.selection_finalize_ms,
        "project_and_certify_ms": (
            timing.shared_laser_projection_ms
            + timing.certificate_total_ms
        ),
        "certificate_unattributed_ms": max(
            0.0,
            timing.certificate_total_ms - segmented_ms,
        ),
    }


def _robust_action_certificate_record(
    certificate: RobustActionCertificate,
) -> dict[str, object]:
    return {
        "action": certificate.action,
        "delay_frames": certificate.delay_frames,
        "worst_collisions": certificate.worst_collisions,
        "min_clearance": certificate.min_clearance,
        "cvar_risk": certificate.cvar_risk,
        "worst_delay": certificate.worst_delay,
        "write_required": certificate.write_required,
        "pipeline_branch_count": certificate.pipeline_branch_count,
        "worst_pending_remaining": (
            certificate.worst_pending_remaining
        ),
    }


def _issue_recertification_record(
    recertification: IssueRecertification | None,
) -> dict[str, object] | None:
    if recertification is None:
        return None
    global_allowed = recertification.global_allowed_actions
    selected_outside_global_without_relaxation = bool(
        global_allowed is not None
        and recertification.selected_action not in global_allowed
        and not recertification.global_constraint_relaxed
    )
    return {
        "planned_action": recertification.planned_action,
        "global_allowed_actions": global_allowed,
        "global_constraint_applicable": (
            recertification.global_constraint_applicable
        ),
        "fresh_safe_actions": recertification.fresh_safe_actions,
        "fresh_global_intersection": (
            recertification.fresh_global_intersection
        ),
        "selected_action": recertification.selected_action,
        "selection_reason": recertification.selection_reason,
        "global_constraint_relaxed": (
            recertification.global_constraint_relaxed
        ),
        "selected_outside_global_without_relaxation": (
            selected_outside_global_without_relaxation
        ),
        "planned_certificate": (
            _robust_action_certificate_record(
                recertification.planned_certificate
            )
            if recertification.planned_certificate is not None
            else None
        ),
        "selected_certificate": _robust_action_certificate_record(
            recertification.selected_certificate
        ),
    }


def commit_local_proposal_for_fresh_hazards(
    proposal: LocalProposal,
    *,
    player_x: float,
    player_y: float,
    previous_mask: int,
    delay_frames: tuple[int, ...],
    action_hold_frames: int,
    bullets: tuple[Bullet, ...],
    lasers: tuple[Laser, ...],
    enemy_bodies: tuple[EnemyBody, ...],
    snapshot_lag: int,
    pipeline_root: LocalPipelineRoot | None = None,
    allowed_first_actions: tuple[str, ...] | None = None,
    viability_repair_volumes: tuple[tuple[str, int], ...] = (),
    viability_recovery_distances: tuple[tuple[str, float], ...] = (),
    viability_safety_actions: tuple[str, ...] = (),
    viability_survival_actions: tuple[str, ...] = (),
) -> IssuedDecision:
    """Commit a proposal against fresh hazards and retained global authority."""

    return IssueTransaction(
        proposal,
        IssueRequest(
            player_x=player_x,
            player_y=player_y,
            previous_mask=previous_mask,
            delay_frames=delay_frames,
            action_hold_frames=action_hold_frames,
            bullets=bullets,
            lasers=lasers,
            enemy_bodies=enemy_bodies,
            snapshot_lag=snapshot_lag,
            pipeline_root=pipeline_root,
            allowed_first_actions=allowed_first_actions,
            viability_repair_volumes=viability_repair_volumes,
            viability_recovery_distances=(
                viability_recovery_distances
            ),
            viability_safety_actions=viability_safety_actions,
            viability_survival_actions=viability_survival_actions,
        ),
        IssueAdapter(
            actions=_PLANNER_ACTIONS,
            certificate_provider=_robust_action_certificates,
            timing_factory=_LocalCertificateTimingAccumulator,
            shot_mask=SHOT,
            focus_mask=FOCUS,
            bomb_mask=BOMB,
        ),
    ).commit()


def issue_transaction_for_fresh_hazards(
    decision: Decision,
    *,
    player_x: float,
    player_y: float,
    previous_mask: int,
    delay_frames: tuple[int, ...],
    action_hold_frames: int,
    bullets: tuple[Bullet, ...],
    lasers: tuple[Laser, ...],
    enemy_bodies: tuple[EnemyBody, ...],
    snapshot_lag: int,
    pipeline_root: LocalPipelineRoot | None = None,
    allowed_first_actions: tuple[str, ...] | None = None,
    viability_repair_volumes: tuple[tuple[str, int], ...] = (),
    viability_recovery_distances: tuple[tuple[str, float], ...] = (),
    viability_safety_actions: tuple[str, ...] = (),
    viability_survival_actions: tuple[str, ...] = (),
) -> IssuedDecision:
    """Compatibility adapter from a flat decision to a proposal."""

    return commit_local_proposal_for_fresh_hazards(
        LocalProposal.from_decision(decision),
        player_x=player_x,
        player_y=player_y,
        previous_mask=previous_mask,
        delay_frames=delay_frames,
        action_hold_frames=action_hold_frames,
        bullets=bullets,
        lasers=lasers,
        enemy_bodies=enemy_bodies,
        snapshot_lag=snapshot_lag,
        pipeline_root=pipeline_root,
        allowed_first_actions=allowed_first_actions,
        viability_repair_volumes=viability_repair_volumes,
        viability_recovery_distances=viability_recovery_distances,
        viability_safety_actions=viability_safety_actions,
        viability_survival_actions=viability_survival_actions,
    )


def recertify_action_for_fresh_hazards(
    decision: Decision,
    *,
    player_x: float,
    player_y: float,
    previous_mask: int,
    delay_frames: tuple[int, ...],
    action_hold_frames: int,
    bullets: tuple[Bullet, ...],
    lasers: tuple[Laser, ...],
    enemy_bodies: tuple[EnemyBody, ...],
    snapshot_lag: int,
    pipeline_root: LocalPipelineRoot | None = None,
    allowed_first_actions: tuple[str, ...] | None = None,
    viability_repair_volumes: tuple[tuple[str, int], ...] = (),
    viability_recovery_distances: tuple[tuple[str, float], ...] = (),
    viability_safety_actions: tuple[str, ...] = (),
    viability_survival_actions: tuple[str, ...] = (),
) -> Decision:
    """Compatibility wrapper for the explicit issue transaction."""

    return issue_transaction_for_fresh_hazards(
        decision,
        player_x=player_x,
        player_y=player_y,
        previous_mask=previous_mask,
        delay_frames=delay_frames,
        action_hold_frames=action_hold_frames,
        bullets=bullets,
        lasers=lasers,
        enemy_bodies=enemy_bodies,
        snapshot_lag=snapshot_lag,
        pipeline_root=pipeline_root,
        allowed_first_actions=allowed_first_actions,
        viability_repair_volumes=viability_repair_volumes,
        viability_recovery_distances=viability_recovery_distances,
        viability_safety_actions=viability_safety_actions,
        viability_survival_actions=viability_survival_actions,
    ).decision


_LOCAL_HAZARD_BACKEND = "numpy"
_LOCAL_BEAM_REDUCER = "python"
_LOCAL_SUPPLEMENTAL_BACKEND = "python"
_LOCAL_BULLET_DECODER = "python"


def _configure_local_hazard_backend(backend: str) -> None:
    global _LOCAL_HAZARD_BACKEND
    if backend not in {"numpy", "native"}:
        raise ValueError(f"unknown local hazard backend: {backend}")
    if (
        backend == "native"
        and native_backend._load_local_hazards_function() is None
    ):
        raise RuntimeError("native local hazard kernel is unavailable")
    _LOCAL_HAZARD_BACKEND = backend


def _configure_local_beam_reducer(backend: str) -> None:
    global _LOCAL_BEAM_REDUCER
    if backend not in {"python", "native"}:
        raise ValueError(f"unknown local beam reducer {backend!r}")
    if (
        backend == "native"
        and native_backend._load_local_beam_reduce_function() is None
    ):
        raise RuntimeError("native local beam reducer is unavailable")
    _LOCAL_BEAM_REDUCER = backend


def _configure_local_supplemental_backend(backend: str) -> None:
    global _LOCAL_SUPPLEMENTAL_BACKEND
    if backend not in {"python", "native"}:
        raise ValueError(
            f"unknown local supplemental backend {backend!r}"
        )
    if (
        backend == "native"
        and native_backend._load_local_supplemental_workspace_functions()
        is None
    ):
        raise RuntimeError(
            "native supplemental rollout workspace is unavailable"
        )
    _LOCAL_SUPPLEMENTAL_BACKEND = backend


def _configure_local_bullet_decoder(backend: str) -> None:
    global _LOCAL_BULLET_DECODER
    if backend not in {"python", "native"}:
        raise ValueError(f"unknown local bullet decoder {backend!r}")
    if (
        backend == "native"
        and native_backend._load_bullet_pool_decode_function() is None
    ):
        raise RuntimeError("native packed bullet decoder is unavailable")
    _LOCAL_BULLET_DECODER = backend


def _hazards_for_positions(
    positions_x: np.ndarray,
    positions_y: np.ndarray,
    *,
    step: int,
    bullet_frame: tuple[np.ndarray, ...],
    lasers: tuple[Laser, ...] | _PackedLaserFrame,
    enemy_bodies: tuple[EnemyBody, ...],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    implementation = (
        _native_hazards_for_positions
        if _LOCAL_HAZARD_BACKEND == "native"
        else _numpy_hazards_for_positions
    )
    return implementation(
        positions_x,
        positions_y,
        step=step,
        bullet_frame=bullet_frame,
        lasers=lasers,
        enemy_bodies=enemy_bodies,
    )


def _control_prefix_hazards(
    *,
    player_x: float,
    player_y: float,
    input_mask: int,
    bullets: tuple[Bullet, ...],
    lasers: tuple[Laser, ...],
    enemy_bodies: tuple[EnemyBody, ...],
    snapshot_lag: int,
    frames: int,
    laser_frames: tuple[_PackedLaserFrame, ...] | None = None,
) -> tuple[float, int, float]:
    return _control_prefix_hazards_impl(
        hazards_for_positions=_hazards_for_positions,
        player_x=player_x,
        player_y=player_y,
        input_mask=input_mask,
        bullets=bullets,
        lasers=lasers,
        enemy_bodies=enemy_bodies,
        snapshot_lag=snapshot_lag,
        frames=frames,
        laser_frames=laser_frames,
    )


def _legacy_robust_action_certificates(
    *,
    player_x: float,
    player_y: float,
    previous_mask: int,
    actions: tuple[PlannerAction, ...],
    delay_frames: tuple[int, ...],
    action_hold_frames: int,
    bullets: tuple[Bullet, ...],
    lasers: tuple[Laser, ...],
    enemy_bodies: tuple[EnemyBody, ...],
    snapshot_lag: int,
    laser_frames: tuple[_PackedLaserFrame, ...] | None = None,
) -> dict[str, RobustActionCertificate]:
    return _legacy_robust_action_certificates_impl(
        hazards_for_positions=_hazards_for_positions,
        player_x=player_x,
        player_y=player_y,
        previous_mask=previous_mask,
        actions=actions,
        delay_frames=delay_frames,
        action_hold_frames=action_hold_frames,
        bullets=bullets,
        lasers=lasers,
        enemy_bodies=enemy_bodies,
        snapshot_lag=snapshot_lag,
        laser_frames=laser_frames,
    )


def _robust_action_certificates(
    *,
    player_x: float,
    player_y: float,
    previous_mask: int,
    actions: tuple[PlannerAction, ...],
    delay_frames: tuple[int, ...],
    action_hold_frames: int,
    bullets: tuple[Bullet, ...],
    lasers: tuple[Laser, ...],
    enemy_bodies: tuple[EnemyBody, ...],
    snapshot_lag: int,
    laser_frames: tuple[_PackedLaserFrame, ...] | None = None,
    pipeline_root: LocalPipelineRoot | None = None,
    timing_accumulator: _LocalCertificateTimingAccumulator | None = None,
) -> dict[str, RobustActionCertificate]:
    return _robust_action_certificates_impl(
        hazards_for_positions=_hazards_for_positions,
        player_x=player_x,
        player_y=player_y,
        previous_mask=previous_mask,
        actions=actions,
        delay_frames=delay_frames,
        action_hold_frames=action_hold_frames,
        bullets=bullets,
        lasers=lasers,
        enemy_bodies=enemy_bodies,
        snapshot_lag=snapshot_lag,
        laser_frames=laser_frames,
        pipeline_root=pipeline_root,
        timing_accumulator=timing_accumulator,
    )


def _direct_root_certificate_shadow(
    *,
    root: LocalPipelineRoot,
    player_x: float,
    player_y: float,
    previous_mask: int,
    delay_frames: tuple[int, ...],
    action_hold_frames: int,
    bullets: tuple[Bullet, ...],
    lasers: tuple[Laser, ...],
    enemy_bodies: tuple[EnemyBody, ...],
    snapshot_lag: int,
    authoritative_certificates: tuple[
        RobustActionCertificate, ...
    ] = (),
) -> dict[str, object]:
    """Late, counterfactual explicit-root certificate with no action authority."""

    timing_accumulator = _LocalCertificateTimingAccumulator()
    started_ns = time.perf_counter_ns()
    certificates = _robust_action_certificates(
        player_x=player_x,
        player_y=player_y,
        previous_mask=previous_mask,
        actions=_PLANNER_ACTIONS,
        delay_frames=delay_frames,
        action_hold_frames=action_hold_frames,
        bullets=bullets,
        lasers=lasers,
        enemy_bodies=enemy_bodies,
        snapshot_lag=snapshot_lag,
        pipeline_root=root,
        timing_accumulator=timing_accumulator,
    )
    wall_ms = (time.perf_counter_ns() - started_ns) / 1_000_000.0
    authoritative_by_action = {
        certificate.action: certificate
        for certificate in authoritative_certificates
    }
    direct_safe_actions = tuple(
        action.name
        for action in _PLANNER_ACTIONS
        if (
            certificates[action.name].worst_collisions == 0
            and certificates[action.name].min_clearance >= 0.0
        )
    )
    authoritative_safe_actions = tuple(
        action.name
        for action in _PLANNER_ACTIONS
        if (
            action.name in authoritative_by_action
            and authoritative_by_action[action.name].worst_collisions == 0
            and authoritative_by_action[action.name].min_clearance >= 0.0
        )
    )
    return {
        "role": "post_issue_shadow_no_action_authority",
        "status": "complete",
        "computed_after_input": True,
        "wall_ms": wall_ms,
        "timing": _local_certificate_timing_record(
            timing_accumulator.snapshot()
        ),
        "direct_safe_actions": direct_safe_actions,
        "authoritative_safe_actions": authoritative_safe_actions,
        "safe_action_set_changed": (
            bool(authoritative_by_action)
            and direct_safe_actions != authoritative_safe_actions
        ),
        "certificates": tuple(
            _robust_action_certificate_record(certificates[action.name])
            for action in _PLANNER_ACTIONS
        ),
    }


def _estimate_live_action_hold(frame_deltas: tuple[int, ...]) -> int:
    operational = sorted(delta for delta in frame_deltas if 0 < delta < 120)
    if not operational:
        return LIVE_ACTION_HOLD_DEFAULT
    rank = max(0, math.ceil(0.9 * len(operational)) - 1)
    return max(
        PLANNER_ACTION_HOLD,
        min(LIVE_ACTION_HOLD_MAX, operational[rank]),
    )


def _terminal_threat_scores(
    nodes: list[SearchNode],
    *,
    start_step: int,
    end_step: int,
    control_delay_frames: int,
    bullet_frames: tuple[tuple[np.ndarray, ...], ...],
    laser_frames: tuple[tuple[Laser, ...], ...],
    enemy_bodies: tuple[EnemyBody, ...],
) -> dict[SearchNode, tuple[int, float]]:
    return _terminal_threat_scores_impl(
        nodes,
        hazards_for_positions=_hazards_for_positions,
        start_step=start_step,
        end_step=end_step,
        control_delay_frames=control_delay_frames,
        bullet_frames=bullet_frames,
        laser_frames=laser_frames,
        enemy_bodies=enemy_bodies,
    )


def _prepare_local_planner_pass(
    request: LocalPlannerRequest,
    *,
    timing_accumulator: _LocalCertificateTimingAccumulator,
) -> PlannerPassPreparation:
    return prepare_planner_pass(
        request,
        planner_action_names=frozenset(
            action.name for action in _PLANNER_ACTIONS
        ),
        terminal_threat_degeneracy=_terminal_threat_degeneracy,
        item_objectives_enabled=ITEM_OBJECTIVES_ENABLED,
        select_items=_select_items,
        focus_mask=FOCUS,
        unfocused_cardinal_speed=UNFOCUSED_CARDINAL_SPEED,
        build_laser_timeline=_build_packed_laser_collision_frames,
        actions=_PLANNER_ACTIONS,
        certificate_provider=_robust_action_certificates,
        timing_accumulator=timing_accumulator,
    )


def _planner_pass_dependencies() -> PlannerPassDependencies:
    """Bind the current controller backends and patch seams for one pass."""

    return PlannerPassDependencies(
        planner_actions=_PLANNER_ACTIONS,
        local_beam_reducer=_LOCAL_BEAM_REDUCER,
        local_supplemental_backend=_LOCAL_SUPPLEMENTAL_BACKEND,
        bomb_mask=BOMB,
        focus_mask=FOCUS,
        shot_mask=SHOT,
        collection_half_width=COLLECTION_HALF_WIDTH,
        item_safety_clearance=ITEM_SAFETY_CLEARANCE,
        player_radius=PLAYER_RADIUS,
        playfield_left=PLAYFIELD_LEFT,
        playfield_right=PLAYFIELD_RIGHT,
        playfield_top=PLAYFIELD_TOP,
        playfield_bottom=PLAYFIELD_BOTTOM,
        unfocused_cardinal_speed=UNFOCUSED_CARDINAL_SPEED,
        unfocused_diagonal_speed=UNFOCUSED_DIAGONAL_SPEED,
        boundary_control_reserve_deficit=(
            _boundary_control_reserve_deficit
        ),
        boundary_risk=_boundary_risk,
        build_bullet_frames=_build_bullet_frames,
        control_prefix_hazards=_control_prefix_hazards,
        directions_opposed=_directions_opposed,
        hazards_for_positions=_hazards_for_positions,
        minimum_travel_frames=_minimum_travel_frames,
        node_key=_node_key,
        project_item=_project_item,
        project_player_for_read_lag=_project_player_for_read_lag,
        robust_action_certificates=_robust_action_certificates,
        terminal_threat_scores=_terminal_threat_scores,
        assemble_local_decision=assemble_local_decision,
        lookup_completed_supplemental=lookup_completed_supplemental,
        run_baseline_beam=run_baseline_beam,
        select_progress_action=select_progress_action,
        search_supplemental_local_beam=search_supplemental_local_beam,
        search_supplemental_local_beam_native=(
            search_supplemental_local_beam_native
        ),
    )


def _run_local_planner_pass(
    request: LocalPlannerRequest,
    preparation: PlannerPassPreparation,
    *,
    _certificate_timing_accumulator: (
        _LocalCertificateTimingAccumulator
    ),
) -> Decision | _PlannerModeTransition:
    """Preserve the historical controller patch seam for one planner pass."""

    return _run_local_planner_pass_impl(
        request,
        preparation,
        dependencies=_planner_pass_dependencies(),
        _certificate_timing_accumulator=(
            _certificate_timing_accumulator
        ),
    )


def _contradiction_key(candidate: Decision) -> tuple[object, ...]:
    return (
        candidate.robust_collisions,
        max(-candidate.robust_min_clearance, 0.0),
        -candidate.robust_min_clearance,
        candidate.terminal_threat_collisions,
        max(-candidate.terminal_threat_min_clearance, 0.0),
        max(-candidate.min_clearance, 0.0),
        candidate.score,
    )


def _choose_action_decision_request(
    request: LocalPlannerRequest,
) -> Decision:
    """Execute planner passes and return the compatibility decision."""

    timing = _LocalCertificateTimingAccumulator()
    preparation = _prepare_local_planner_pass(
        request,
        timing_accumulator=timing,
    )
    result = _run_local_planner_pass(
        request,
        preparation,
        _certificate_timing_accumulator=timing,
    )
    if isinstance(result, _PlannerModeTransition):
        retry_preparation = _prepare_local_planner_pass(
            result.next_request,
            timing_accumulator=timing,
        )
        retry = _run_local_planner_pass(
            result.next_request,
            retry_preparation,
            _certificate_timing_accumulator=timing,
        )
        if isinstance(retry, _PlannerModeTransition):
            raise AssertionError("relaxed planner mode cannot transition again")
        if _contradiction_key(retry) < _contradiction_key(
            result.current_decision
        ):
            decision = replace(
                retry,
                viability_safe_action_count=(
                    result.original_allowed_action_count
                ),
                viability_constraint_relaxed=True,
            )
        else:
            decision = result.current_decision
        return replace(
            decision,
            local_certificate_timing=timing.snapshot(),
        )
    return result


def choose_local_proposal_request(
    request: LocalPlannerRequest,
) -> LocalProposal:
    """Build a proposal that has not yet crossed the issue boundary."""

    return LocalProposal.from_decision(
        _choose_action_decision_request(request)
    )


def choose_action_request(request: LocalPlannerRequest) -> Decision:
    """Compatibility view of a grouped local proposal."""

    return choose_local_proposal_request(request).decision


def choose_action(
    *,
    player_x: float,
    player_y: float,
    bullets: tuple[Bullet, ...],
    lasers: tuple[Laser, ...],
    previous_direction: int,
    can_bomb: bool,
    enemy_bodies: tuple[EnemyBody, ...] = (),
    items: tuple[Item, ...] = (),
    power: float = 0.0,
    bombs: float = 0.0,
    previous_focus: bool = True,
    local_pipeline_root: LocalPipelineRoot | None = None,
    snapshot_lag: int = 0,
    control_delay_frames: int = CONTROL_DELAY_FRAMES,
    control_delay_candidates: tuple[int, ...] | None = None,
    action_hold_frames: int = PLANNER_ACTION_HOLD,
    horizon: int = PLANNER_HORIZON,
    threat_horizon: int | None = None,
    beam_width: int = PLANNER_BEAM_WIDTH,
    target_x: float | None = None,
    target_y: float | None = None,
    target_deadline: int | None = None,
    allowed_first_actions: tuple[str, ...] | None = None,
    viability_repair_volumes: tuple[tuple[str, int], ...] = (),
    viability_recovery_distances: tuple[tuple[str, float], ...] = (),
    viability_safety_actions: tuple[str, ...] = (),
    viability_safety_state_value: float | None = None,
    viability_survival_actions: tuple[str, ...] = (),
    viability_survival_frames: int | None = None,
    viability_survival_bottleneck_margin: float | None = None,
    viability_position_error: float = 0.0,
    damage_target_x: float | None = None,
    damage_target_half_width: float = 0.0,
    damageable: bool = False,
    recovery_control_reserve: bool = True,
    losing_control_reserve: bool = False,
    preloss_continuation_preference: bool = False,
    preloss_supplemental_beam_width: int = 0,
    preloss_supplemental_deadline_ms: float | None = None,
    preloss_supplemental_async_service: (
        ExactVersionSupplementalService | None
    ) = None,
    preloss_supplemental_version: object | None = None,
    preserve_previous_direction_inertia: bool = True,
    beam_dedup_mode: str = "quantized",
    relax_stale_viability_contradiction: bool = False,
    enforce_fresh_viability_intersection: bool = True,
) -> Decision:
    """Compatibility wrapper for callers not yet migrated to grouped input."""

    return choose_action_request(
        LocalPlannerRequest(
            physical=PhysicalHazardSnapshot(
                player_x=player_x,
                player_y=player_y,
                bullets=bullets,
                lasers=lasers,
                enemy_bodies=enemy_bodies,
                items=items,
                snapshot_lag=snapshot_lag,
            ),
            actuator=ActuatorPipeline(
                previous_direction=previous_direction,
                can_bomb=can_bomb,
                previous_focus=previous_focus,
                local_pipeline_root=local_pipeline_root,
                control_delay_frames=control_delay_frames,
                control_delay_candidates=control_delay_candidates,
                action_hold_frames=action_hold_frames,
            ),
            guidance=GlobalGuidance(
                target_x=target_x,
                target_y=target_y,
                target_deadline=target_deadline,
                allowed_first_actions=allowed_first_actions,
                viability_repair_volumes=viability_repair_volumes,
                viability_recovery_distances=(
                    viability_recovery_distances
                ),
                viability_safety_actions=viability_safety_actions,
                viability_safety_state_value=(
                    viability_safety_state_value
                ),
                viability_survival_actions=viability_survival_actions,
                viability_survival_frames=viability_survival_frames,
                viability_survival_bottleneck_margin=(
                    viability_survival_bottleneck_margin
                ),
                viability_position_error=viability_position_error,
            ),
            config=PlannerConfig(
                horizon=horizon,
                threat_horizon=threat_horizon,
                beam_width=beam_width,
                recovery_control_reserve=recovery_control_reserve,
                losing_control_reserve=losing_control_reserve,
                preloss_continuation_preference=(
                    preloss_continuation_preference
                ),
                preloss_supplemental_beam_width=(
                    preloss_supplemental_beam_width
                ),
                preserve_previous_direction_inertia=(
                    preserve_previous_direction_inertia
                ),
                beam_dedup_mode=beam_dedup_mode,
                relax_stale_viability_contradiction=(
                    relax_stale_viability_contradiction
                ),
                enforce_fresh_viability_intersection=(
                    enforce_fresh_viability_intersection
                ),
            ),
            objective=ObjectiveContext(
                power=power,
                bombs=bombs,
                damage_target_x=damage_target_x,
                damage_target_half_width=damage_target_half_width,
                damageable=damageable,
            ),
            completed_services=CompletedServiceResults(
                supplemental_deadline_ms=(
                    preloss_supplemental_deadline_ms
                ),
                supplemental_async_service=(
                    preloss_supplemental_async_service
                ),
                supplemental_version=preloss_supplemental_version,
            ),
        )
    )


def _enemy_sensor_submit_due(
    *,
    current_frame: int,
    last_submit_frame: int,
    pending: bool,
    interval_frames: int = ENEMY_SENSOR_INTERVAL_FRAMES,
) -> bool:
    if interval_frames <= 0:
        raise ValueError("enemy sensor interval must be positive")
    return (
        not pending
        and current_frame - last_submit_frame >= interval_frames
    )


def _write_run_summary(
    trace_sink: TraceSink,
    *,
    last_frame: int | None,
    counter_gaps: int,
    hit_count: int,
    termination_reason: str,
) -> None:
    trace_sink.summary(
        last_frame=last_frame,
        counter_gaps=counter_gaps,
        hit_count=hit_count,
        termination_reason=termination_reason,
    )


def _prepare_live_run(args: argparse.Namespace) -> None:
    if not args.armed:
        raise RuntimeError("live control requires the explicit --armed flag")
    if min(
        args.corridor_every,
        args.corridor_lookahead,
        args.corridor_max_age,
    ) <= 0:
        raise ValueError("corridor timing arguments must be positive")
    if args.wait_timeout <= 0.0:
        raise ValueError("wait timeout must be positive")
    if args.stop_after_hits < 0 or args.post_hit_frames < 0:
        raise ValueError("hit stopping arguments cannot be negative")
    if (
        args.safety_value_horizon < 0
        or args.safety_value_horizon > TH08_CORRIDOR_CONFIG.horizon_frames
        or (
            args.safety_value_horizon
            % TH08_CORRIDOR_CONFIG.frames_per_layer
        )
    ):
        raise ValueError(
            "safety-value horizon must be zero or complete corridor layers "
            "within the global horizon"
        )
    if not (
        LIVE_CONTROL_DELAY_MIN
        <= args.control_delay_frames
        <= LIVE_CONTROL_DELAY_MAX
    ):
        raise ValueError(
            "initial control delay must be within the live estimator bounds"
        )
    if args.auto_confirm_every < 0 or args.auto_confirm_idle_frames < 0:
        raise ValueError("auto-confirm timing arguments cannot be negative")
    if args.input_clock_shadow_sample_ms <= 0.0:
        raise ValueError("input-clock shadow sample cadence must be positive")
    if args.local_pipeline_root_shadow_every < 0:
        raise ValueError(
            "local pipeline root shadow cadence cannot be negative"
        )
    if args.auxiliary_vm_batch_every <= 0:
        raise ValueError("auxiliary-VM batch cadence must be positive")
    if (
        args.auxiliary_vm_batch_spell_id is not None
        and args.auxiliary_vm_batch_spell_id < 0
    ):
        raise ValueError("auxiliary-VM spell filter cannot be negative")
    runtime_ecl_static_image = getattr(
        args,
        "runtime_ecl_static_image",
        None,
    )
    runtime_ecl_static_sha256 = getattr(
        args,
        "runtime_ecl_static_sha256",
        None,
    )
    if (runtime_ecl_static_image is None) != (
        runtime_ecl_static_sha256 is None
    ):
        raise ValueError(
            "runtime ECL identity requires both a static image and SHA-256"
        )
    if (
        runtime_ecl_static_image is not None
        and args.expected_stage is None
    ):
        raise ValueError(
            "runtime ECL identity requires an explicit expected stage"
        )
    _configure_local_hazard_backend(args.local_hazard_backend)
    _configure_local_beam_reducer(args.local_beam_reducer)
    _configure_local_bullet_decoder(args.bullet_decode_backend)
    if (
        getattr(args, "trace_bullet_births", False)
        and getattr(args, "bullet_birth_backend", "python") == "native"
        and not native_bullet_birth_available(
            getattr(
                args,
                "bullet_birth_native_call_mode",
                NATIVE_CALL_MODE_GIL_RELEASED,
            )
        )
    ):
        raise RuntimeError(
            "native bullet-birth backend was selected but its trace "
            "library is unavailable"
        )
    if (
        getattr(args, "trace_derived_pattern_sources", False)
        and not getattr(args, "trace_bullet_births", False)
    ):
        raise ValueError(
            "derived-pattern source tracing requires bullet-birth tracing"
        )
    if (
        getattr(args, "trace_nonspell_main_vms", False)
        and not getattr(args, "trace_bullet_births", False)
    ):
        raise ValueError(
            "nonspell main-VM tracing requires bullet-birth tracing"
        )
    if (
        getattr(args, "trace_auxiliary_vm_batches", False)
        and not native_auxiliary_vm_batch_available(
            getattr(
                args,
                "auxiliary_vm_native_call_mode",
                "gil-held",
            )
        )
    ):
        raise RuntimeError(
            "auxiliary-VM batch tracing was selected but its native "
            "trace library is unavailable"
        )
    if (
        args.stage_transition_timeout <= 0.0
        or args.terminal_inactive_grace <= 0.0
    ):
        raise ValueError("scene transition timing arguments must be positive")


def run(args: argparse.Namespace) -> int:
    _prepare_live_run(args)
    with LiveSession(
        output_path=args.output,
        requested_pid=args.pid,
        target_exe=TARGET_EXE,
    ) as session:
        return _run_live_session(args, session)


def _build_birth_trace_observers(
    *,
    trace_bullet_births: bool,
    trace_derived_pattern_sources: bool,
    backend: str,
    native_call_mode: str,
) -> tuple[
    BulletBirthTracker | NativeBulletBirthTracker | None,
    NativeDerivedPatternSourceObserver | None,
]:
    if trace_derived_pattern_sources and not trace_bullet_births:
        raise ValueError(
            "derived-pattern source tracing requires bullet-birth tracing"
        )
    tracker = (
        (
            NativeBulletBirthTracker(native_call_mode=native_call_mode)
            if backend == "native"
            else BulletBirthTracker()
        )
        if trace_bullet_births
        else None
    )
    source = (
        (
            NativeDerivedPatternSourceObserver(
                native_call_mode=native_call_mode,
            )
            if backend == "native"
            else None
        )
        if trace_derived_pattern_sources
        else None
    )
    return tracker, source


def _run_live_session(
    args: argparse.Namespace,
    session: LiveSession,
) -> int:
    api = session.api
    pid = session.pid
    reader = session.reader
    output = session.output
    trace_sink = TraceSink(output)
    previous_mask = 0
    previous_direction = 0
    previous_counter: int | None = None
    previous_phase: int | None = None
    previous_bombs: float | None = None
    previous_power: float | None = None
    previous_action_phase: int | None = None
    last_bomb_counter = -10000
    gaps = 0
    iterations = 0
    hit_count = 0
    stop_after_frame: int | None = None
    gameplay_armed = False
    termination_reason = "duration"
    corridor_future: Future[CorridorSolution] | None = None
    corridor_survival_future: Future[CorridorSolution] | None = None
    enemy_future: Future[EnemyPoolSnapshot] | None = None
    enemy_snapshot: EnemyPoolSnapshot | None = None
    enemy_last_submit = CORRIDOR_INITIAL_SUBMIT_FRAME
    corridor_solution: CorridorSolution | None = None
    corridor_pending_solution: CorridorSolution | None = None
    corridor_last_submit = CORRIDOR_INITIAL_SUBMIT_FRAME
    corridor_commitment = CorridorCommitment()
    corridor_context: tuple[int, int, int | None] | None = None
    enemy_body_memory = EnemyBodyModeMemory(
        maximum_age_frames=ENEMY_DORMANT_MEMORY_FRAMES
    )
    enemy_background_memory = EnemyBodyModeMemory(
        maximum_age_frames=ENEMY_DORMANT_MEMORY_FRAMES
    )
    spell_enemy_body_memory = EnemyBodyModeMemory(
        maximum_age_frames=ENEMY_DORMANT_MEMORY_FRAMES
    )
    enemy_body_memories = (
        enemy_body_memory,
        enemy_background_memory,
        spell_enemy_body_memory,
    )
    boss_phase_tracker = PhaseProgressTracker()
    gameplay_epoch = 0
    stage_successors = dict(ROUTE2_STAGE_SUCCESSORS)
    if args.terminal_stage is not None:
        stage_successors.pop(args.terminal_stage, None)
    scene_clock = SceneClockCoordinator.create(
        auto_confirm_interval_frames=args.auto_confirm_every,
        auto_confirm_idle_frames=args.auto_confirm_idle_frames,
        stage_successors=stage_successors,
        transition_timeout_seconds=args.stage_transition_timeout,
        terminal_grace_seconds=args.terminal_inactive_grace,
        input_clock_shadow=args.input_clock_boundary_shadow,
    )
    auto_confirm = scene_clock.auto_confirm
    scene_guard = scene_clock.scene_guard
    input_clock_tracker = scene_clock.input_clock_tracker
    last_frame_progress = time.perf_counter()
    last_frozen_confirm = float("-inf")
    input_clock_repeat_frame: int | None = None
    input_clock_repeat_polls = 0
    input_clock_wall_cut_frame: int | None = None
    input_clock_last_sample_ns = 0
    input_clock_last_message_key: tuple[object, ...] | None = None
    input_clock_delay_support: tuple[int, ...] = (
        args.control_delay_frames,
    )
    decision_frame_deltas: deque[int] = deque(maxlen=120)
    delay_estimator = AdaptiveControlDelay(
        supported_mask=SUPPORTED_INPUT_MASK,
        minimum=LIVE_CONTROL_DELAY_MIN,
        maximum=LIVE_CONTROL_DELAY_MAX,
        window=LIVE_CONTROL_DELAY_WINDOW,
        guard_frames=LIVE_CONTROL_DELAY_GUARD_FRAMES,
    )
    corridor_policy_lead = AsyncPolicyLead(
        initial_frames=CORRIDOR_POLICY_LEAD_INITIAL_FRAMES,
        overlap_frames=CORRIDOR_POLICY_OVERLAP_FRAMES,
        minimum_frames=CORRIDOR_POLICY_MINIMUM_LEAD_FRAMES,
    )
    ecl_instruction_cache = EclInstructionCache()
    trace_bullet_births = bool(
        getattr(args, "trace_bullet_births", False)
    )
    trace_derived_pattern_sources = bool(
        getattr(args, "trace_derived_pattern_sources", False)
    )
    trace_nonspell_main_vms = bool(
        getattr(args, "trace_nonspell_main_vms", False)
    )
    trace_enemy_combat_progress = bool(
        getattr(args, "trace_enemy_combat_progress", False)
    )
    trace_auxiliary_vm_batches = bool(
        getattr(args, "trace_auxiliary_vm_batches", False)
    )
    runtime_ecl_identity_service: RuntimeEclIdentityService | None = None
    runtime_ecl_static_image = getattr(
        args,
        "runtime_ecl_static_image",
        None,
    )
    if runtime_ecl_static_image is not None:
        runtime_ecl_static_path = runtime_ecl_static_image
        if not runtime_ecl_static_path.is_absolute():
            runtime_ecl_static_path = (
                Path(__file__).resolve().parents[2]
                / runtime_ecl_static_path
            )
        runtime_ecl_identity_service = RuntimeEclIdentityService(
            static_image=runtime_ecl_static_path.read_bytes(),
            static_label=runtime_ecl_static_image.as_posix(),
            expected_static_sha256=args.runtime_ecl_static_sha256,
            expected_route_id=2,
            expected_difficulty_index=args.difficulty,
            expected_stage_route_index=args.expected_stage,
        )
    auxiliary_vm_batch_service = (
        AuxiliaryVmBatchTraceService(
            cadence_frames=args.auxiliary_vm_batch_every,
            spell_id_filter=args.auxiliary_vm_batch_spell_id,
            native_call_mode=args.auxiliary_vm_native_call_mode,
        )
        if trace_auxiliary_vm_batches
        else None
    )
    previous_auxiliary_vm_batch_emit_ms: float | None = None
    previous_enemy_combat_progress_emit_ms: float | None = None
    bullet_birth_backend = getattr(
        args,
        "bullet_birth_backend",
        "python",
    )
    bullet_birth_native_call_mode = getattr(
        args,
        "bullet_birth_native_call_mode",
        NATIVE_CALL_MODE_GIL_RELEASED,
    )
    (
        bullet_birth_tracker,
        derived_pattern_source_observer,
    ) = _build_birth_trace_observers(
        trace_bullet_births=trace_bullet_births,
        trace_derived_pattern_sources=trace_derived_pattern_sources,
        backend=bullet_birth_backend,
        native_call_mode=bullet_birth_native_call_mode,
    )
    previous_birth_trace_emit_ms: float | None = None
    previous_iteration_ms: float | None = None
    previous_trace_ms: float | None = None
    service_resources = LiveServiceResources(
        local_only=args.local_only,
        postpublished_survival_shadow=(
            args.postpublished_survival_shadow
        ),
        pipeline_prewarm_shadow=args.pipeline_prewarm_shadow,
        candidate_verifier_shadow=args.candidate_verifier_shadow,
        viability_audit_enabled=args.viability_audit_dir is not None,
        candidate_horizon_frames=CANDIDATE_VERIFIER_HORIZON_FRAMES,
        candidate_decision_frames=CANDIDATE_VERIFIER_DECISION_FRAMES,
        candidate_timeout_ms=CANDIDATE_VERIFIER_TIMEOUT_MS,
        close_pipeline_prewarms=_close_retired_pipeline_prewarms,
    )
    corridor_executor = service_resources.corridor_executor
    survival_executor = service_resources.survival_executor
    candidate_verifier = service_resources.candidate_verifier
    audit_executor = service_resources.audit_executor
    enemy_executor = service_resources.enemy_executor
    issue_controller = IssueController(
        api=api,
        pid=pid,
        supported_mask=SUPPORTED_INPUT_MASK,
        forbidden_mask=BOMB if args.no_bomb else 0,
    )
    policy_coordinator = PolicyCoordinator()

    def retire_pipeline_solutions(
        candidates: tuple[CorridorSolution | None, ...],
        retained: tuple[CorridorSolution | None, ...] = (),
    ) -> None:
        service_resources.retire_pipeline_solutions(
            candidates,
            retained=retained,
        )

    def input_clock_policy_snapshot() -> dict[str, object]:
        return {
            "published_solution_present": corridor_solution is not None,
            "pending_solution_present": corridor_pending_solution is not None,
            "solve_future_pending": (
                corridor_future is not None and not corridor_future.done()
            ),
            "survival_future_pending": (
                corridor_survival_future is not None
                and not corridor_survival_future.done()
            ),
            "would_retire_solution_count": sum(
                solution is not None
                for solution in (
                    corridor_solution,
                    corridor_pending_solution,
                )
            ),
        }

    def record_input_clock_sample(
        *,
        sample: dict[str, object],
        observation: SemanticClockObservation,
        events: tuple[SemanticClockEvent, ...],
        frame: int,
        stage_route_index: int,
        frozen_seconds: float,
        repeat_poll_count: int,
        triggers: tuple[str, ...],
    ) -> None:
        record = {
            "kind": "input_clock_shadow_observation",
            "role": INPUT_CLOCK_SHADOW_ROLE,
            "frame": frame,
            "stage_route_index": stage_route_index,
            "gameplay_epoch": gameplay_epoch,
            "frozen_seconds": frozen_seconds,
            "repeat_poll_count": repeat_poll_count,
            "triggers": triggers,
            "held_desired_mask": previous_mask,
            "delay_support": input_clock_delay_support,
            "active_episode_id": (
                input_clock_tracker.active_episode_id
                if input_clock_tracker is not None
                else None
            ),
            "policy_retirement_hypothesis": input_clock_policy_snapshot(),
            "observation": _serialize_semantic_clock_observation(
                observation
            ),
            "sample": sample,
        }
        records = [record]
        for event in events:
            event_record = _serialize_semantic_clock_event(event)
            event_record.update(
                {
                    "stage_route_index": stage_route_index,
                    "gameplay_epoch": gameplay_epoch,
                    "held_desired_mask": previous_mask,
                    "delay_support": input_clock_delay_support,
                    "policy_retirement_hypothesis": (
                        input_clock_policy_snapshot()
                    ),
                    "sample": sample,
                }
            )
            records.append(event_record)
        trace_sink.emit_many(records, flush=True)

    try:
        identity = verify_target(reader)
        trace_sink.emit({"kind": "identity", **identity})
        trace_sink.emit(
            {
                    "kind": "controller_config",
                    "bomb_policy": (
                        "disabled"
                        if args.no_bomb
                        else (
                            "normal_and_deathbomb"
                            if args.normal_bomb
                            else "deathbomb_only"
                        )
                    ),
                    "item_policy": (
                        "survival_only_passive_collection"
                        if not ITEM_OBJECTIVES_ENABLED
                        else "certified_viable_tiebreaker"
                    ),
                    "boss_phase_sensor": (
                        "native_registry_health_timer_and_damage_gate"
                    ),
                    "damage_objective": (
                        "shadow_lexicographic_inside_fresh_safe_set"
                    ),
                    "enemy_body_sensor": (
                        "synchronous_latent_contact_prefix_plus_"
                        "async_enabled_tail_with_observed_world_motion"
                    ),
                    "enemy_body_synchronous_prefix_slots": (
                        ENEMY_LOCAL_PREFIX_SIZE
                    ),
                    "enemy_body_dormant_memory_frames": (
                        ENEMY_DORMANT_MEMORY_FRAMES
                    ),
                    "enemy_body_max_observed_world_speed": (
                        ENEMY_MAX_OBSERVED_WORLD_SPEED
                    ),
                    "control_delay_policy": (
                        "adaptive_end_to_end_distribution_robust_mpc"
                    ),
                    "control_delay_default": args.control_delay_frames,
                    "control_delay_min": LIVE_CONTROL_DELAY_MIN,
                    "control_delay_max": LIVE_CONTROL_DELAY_MAX,
                    "control_delay_window": LIVE_CONTROL_DELAY_WINDOW,
                    "control_delay_guard_frames": (
                        LIVE_CONTROL_DELAY_GUARD_FRAMES
                    ),
                    "maximum_sensor_epoch_extent_frames": (
                        MAX_SENSOR_EPOCH_EXTENT_FRAMES
                    ),
                    "maximum_action_contiguous_advance_frames": (
                        MAX_ACTION_CONTIGUOUS_ADVANCE_FRAMES
                    ),
                    "input_clock_boundary_shadow": (
                        args.input_clock_boundary_shadow
                    ),
                    "input_clock_shadow_role": (
                        INPUT_CLOCK_SHADOW_ROLE
                        if args.input_clock_boundary_shadow
                        else "disabled"
                    ),
                    "input_clock_shadow_sample_ms": (
                        args.input_clock_shadow_sample_ms
                    ),
                    "input_clock_shadow_predicate": (
                        "frscreen_msg_state_ge_0_or_eq_minus_2"
                        if args.input_clock_boundary_shadow
                        else "disabled"
                    ),
                    "local_hazard_backend": args.local_hazard_backend,
                    "local_hazard_backend_authority": (
                        "parity_gated_native_default_exact_implementation"
                        if args.local_hazard_backend == "native"
                        else "explicit_python_reference_rollback"
                    ),
                    "local_beam_reducer": args.local_beam_reducer,
                    "local_beam_reducer_authority": (
                        "parity_gated_native_quantized_reduction"
                        if args.local_beam_reducer == "native"
                        else "explicit_python_reference_rollback"
                    ),
                    "bullet_decode_backend": (
                        args.bullet_decode_backend
                    ),
                    "bullet_decode_backend_authority": (
                        "python_diagnostic_transform_override"
                        if args.trace_transform_runtime
                        else (
                            "parity_gated_native_packed_with_sparse_python_crossover"
                            if args.bullet_decode_backend == "native"
                            else "explicit_python_object_reference_rollback"
                        )
                    ),
                    "pool_read_buffers": (
                        "persistent_ctypes_destination_unsigned_byte_view"
                    ),
                    "global_planner": (
                        "finite_horizon_robust_backward_viability"
                        if not args.local_only
                        else "disabled"
                    ),
                    "viability_grid_step": TH08_CORRIDOR_CONFIG.grid_step,
                    "viability_refinement_grid_steps": (
                        LIVE_REFINEMENT_GRID_STEPS
                    ),
                    "viability_shadow_refinement_grid_steps": (
                        SHADOW_REFINEMENT_GRID_STEPS
                    ),
                    "viability_refinement_trigger": (
                        "shadow_only_after_stage4a_latency_rejection"
                    ),
                    "viability_survival_labels": (
                        {
                            "live": LIVE_SURVIVAL_LABELS,
                            "shadow": SHADOW_SURVIVAL_LABELS,
                            "postpublished_compute": (
                                args.postpublished_survival_shadow
                            ),
                            "pipeline_prepublication_shadow": (
                                args.pipeline_prewarm_shadow
                            ),
                            "candidate_verifier_shadow": (
                                args.candidate_verifier_shadow
                            ),
                            "reason": (
                                "shadow_isolated_after_serialized_delivery_"
                                "rejection"
                            ),
                        }
                    ),
                    "viability_frames_per_layer": (
                        TH08_CORRIDOR_CONFIG.frames_per_layer
                    ),
                    "viability_horizon_frames": (
                        TH08_CORRIDOR_CONFIG.horizon_frames
                    ),
                    "corridor_background_low_priority": (
                        args.corridor_background_low_priority
                    ),
                    "corridor_native_viability_workers": (
                        args.corridor_native_workers
                    ),
                    "local_planner_horizon_frames": args.horizon,
                    "local_terminal_threat_horizon_frames": (
                        args.threat_horizon
                    ),
                    "viability_max_query_age_frames": (
                        args.corridor_max_age
                    ),
                    "async_policy_epoch": "forecasted_solve_completion",
                    "async_policy_context": (
                        "gameplay_epoch_stage_spell"
                    ),
                    "async_policy_initial_lead_frames": (
                        corridor_policy_lead.frames
                    ),
                    "async_policy_overlap_frames": (
                        corridor_policy_lead.overlap_frames
                    ),
                    "async_policy_minimum_lead_frames": (
                        corridor_policy_lead.minimum_frames
                    ),
                    "async_policy_delay_support_padding": (
                        ASYNC_POLICY_DELAY_PADDING
                    ),
                    "async_policy_submit_interval_frames": (
                        args.corridor_every
                    ),
                    "safety_value_horizon_frames": (
                        args.safety_value_horizon
                    ),
                    "safety_value_role": (
                        "empty_kernel_soft_preference"
                        if args.safety_value_horizon
                        else "disabled"
                    ),
                    "native_planner_backend": native_backend.available(),
                    "viability_quantifiers": (
                        "exists_action_forall_delay"
                    ),
                    "viability_audit_capsules": (
                        str(args.viability_audit_dir)
                        if args.viability_audit_dir is not None
                        else None
                    ),
            },
            flush=True,
        )
        state = observe_state(reader)
        if args.wait_gameplay:
            trace_sink.emit(
                {
                    "kind": "wait_ready",
                    "frame": state["enemy_manager_frame"],
                },
                flush=True,
            )
            wait_deadline = time.perf_counter() + args.wait_timeout
            while True:
                if state["gameplay_active"]:
                    gameplay_armed = True
                    if (
                        state["route_id"] != 2
                        or state["difficulty_index"] != args.difficulty
                    ):
                        raise RuntimeError(
                            "manual selection mismatch after confirm: "
                            f"difficulty={state['difficulty_index']} "
                            f"route={state['route_id']}"
                        )
                    if (
                        args.expected_stage is not None
                        and state["stage_route_index"] != args.expected_stage
                    ):
                        raise RuntimeError(
                            "practice stage mismatch after confirm: "
                            f"expected={args.expected_stage} "
                            f"got={state['stage_route_index']}"
                        )
                    if not state["input_raw"]:
                        break
                if args.stop_file is not None and args.stop_file.exists():
                    termination_reason = "external_stop"
                    return 0
                if time.perf_counter() >= wait_deadline:
                    raise RuntimeError(
                        "timed out waiting for idle route-2 gameplay"
                    )
                _require_foreground(api, pid)
                time.sleep(0.005)
                state = observe_state(reader)
        if not state["gameplay_active"] or state["route_id"] != 2:
            raise RuntimeError("agent requires active route-2 gameplay")
        if state["difficulty_index"] != args.difficulty:
            raise RuntimeError(
                "difficulty mismatch: "
                f"expected {args.difficulty}, got {state['difficulty_index']}"
            )
        if (
            args.expected_stage is not None
            and state["stage_route_index"] != args.expected_stage
        ):
            raise RuntimeError(
                "stage mismatch: "
                f"expected {args.expected_stage}, "
                f"got {state['stage_route_index']}"
            )
        if state["input_raw"]:
            raise RuntimeError("physical gameplay input is already active")
        _require_foreground(api, pid)
        gameplay_armed = True
        scene_guard.observe(
            gameplay_active=True,
            current_stage=int(state["stage_route_index"]),
            now=time.perf_counter(),
        )
        enemy_future = enemy_executor.submit(
            capture_enemy_pool_snapshot,
            reader,
        )
        enemy_last_submit = int(state["enemy_manager_frame"])
        sensor = Sensor(reader)
        deadline = time.perf_counter() + args.duration
        while time.perf_counter() < deadline:
            if args.stop_file is not None and args.stop_file.exists():
                termination_reason = "external_stop"
                break
            counter = reader.u32(ADDR_ENEMY_MANAGER_FRAME)
            now = time.perf_counter()
            engine_flags = reader.u32(ADDR_ENGINE_FLAGS)
            stage_route_index = reader.u32(ADDR_STAGE_ROUTE_INDEX)
            scene_decision = scene_guard.observe(
                gameplay_active=bool(engine_flags & 0x04),
                current_stage=stage_route_index,
                now=now,
            )
            if not engine_flags & 0x04:
                if (
                    input_clock_tracker is not None
                    and input_clock_tracker.active_episode_id is not None
                ):
                    input_clock_sample = capture_input_clock_shadow(reader)
                    input_clock_observation = _semantic_clock_observation(
                        input_clock_sample,
                        fallback_frame=counter,
                        context=(gameplay_epoch, stage_route_index),
                    )
                    input_clock_event = input_clock_tracker.censor(
                        input_clock_observation,
                        reason=f"scene_inactive:{scene_decision.status}",
                    )
                    record_input_clock_sample(
                        sample=input_clock_sample,
                        observation=input_clock_observation,
                        events=(
                            (input_clock_event,)
                            if input_clock_event is not None
                            else ()
                        ),
                        frame=counter,
                        stage_route_index=stage_route_index,
                        frozen_seconds=max(0.0, now - last_frame_progress),
                        repeat_poll_count=input_clock_repeat_polls,
                        triggers=("scene_inactive",),
                    )
                if scene_decision.entered:
                    issue_controller.dispatch(
                        previous_mask,
                        0,
                        require_foreground=True,
                    )
                    previous_mask = 0
                    previous_direction = 0
                    retire_pipeline_solutions(
                        (corridor_solution, corridor_pending_solution)
                    )
                    corridor_solution = None
                    corridor_pending_solution = None
                    for memory in enemy_body_memories:
                        memory.clear()
                    if bullet_birth_tracker is not None:
                        bullet_birth_tracker.reset()
                    if corridor_future is not None and corridor_future.cancel():
                        corridor_future = None
                    if (
                        corridor_survival_future is not None
                        and corridor_survival_future.cancel()
                    ):
                        corridor_survival_future = None
                    trace_sink.emit(
                        {
                                "kind": "scene_inactive",
                                "frame": counter,
                                "engine_flags": engine_flags,
                                "stage_route_index": stage_route_index,
                                "transition_from_stage": (
                                    scene_decision.transition_from_stage
                                ),
                                "expected_stage": scene_decision.expected_stage,
                                "status": scene_decision.status,
                        },
                        flush=True,
                    )
                if scene_decision.status in (
                    "stage_transition_timeout",
                    "route_complete",
                ):
                    termination_reason = scene_decision.status
                    break
                assert scene_guard.inactive_since is not None
                if auto_confirm.frozen_pulse_due(
                    now=now,
                    last_progress=scene_guard.inactive_since,
                    last_pulse=last_frozen_confirm,
                    eligible=scene_decision.expected_stage is not None,
                ):
                    _require_foreground(api, pid)
                    send_scan_key(api, scan_code=0x2C, pressed=False)
                    time.sleep(0.04)
                    send_scan_key(api, scan_code=0x2C, pressed=True)
                    previous_mask = SHOT
                    auto_confirm.mark_full_pulse(frame=counter)
                    last_frozen_confirm = time.perf_counter()
                    trace_sink.emit(
                        {
                                "kind": "auto_confirm_transition_pulse",
                                "frame": counter,
                                "stage_route_index": stage_route_index,
                                "transition_from_stage": (
                                    scene_decision.transition_from_stage
                                ),
                                "expected_stage": scene_decision.expected_stage,
                                "inactive_seconds": (
                                    scene_decision.inactive_seconds
                                ),
                        },
                        flush=True,
                    )
                time.sleep(args.poll_ms / 1000.0)
                continue
            if scene_decision.status == "resumed":
                gameplay_epoch += 1
                boss_phase_tracker.reset()
                trace_sink.emit(
                    {
                            "kind": "scene_resumed",
                            "frame": counter,
                            "engine_flags": engine_flags,
                            "stage_route_index": stage_route_index,
                            "transition_from_stage": (
                                scene_decision.transition_from_stage
                            ),
                            "expected_stage": scene_decision.expected_stage,
                            "inactive_seconds": scene_decision.inactive_seconds,
                            "expected_stage_matched": (
                                scene_decision.expected_stage is None
                                or scene_decision.expected_stage
                                == stage_route_index
                            ),
                            "gameplay_epoch": gameplay_epoch,
                    },
                    flush=True,
                )
                previous_counter = None
                previous_phase = None
                previous_action_phase = None
                decision_frame_deltas.clear()
                delay_estimator.reset()
                previous_iteration_ms = None
                previous_trace_ms = None
                previous_birth_trace_emit_ms = None
                retire_pipeline_solutions(
                    (corridor_solution, corridor_pending_solution)
                )
                corridor_solution = None
                corridor_pending_solution = None
                corridor_last_submit = CORRIDOR_INITIAL_SUBMIT_FRAME
                corridor_context = None
                corridor_commitment = CorridorCommitment()
                for memory in enemy_body_memories:
                    memory.clear()
                ecl_instruction_cache.clear()
                if bullet_birth_tracker is not None:
                    bullet_birth_tracker.reset()
                if corridor_future is not None and corridor_future.cancel():
                    corridor_future = None
                if (
                    corridor_survival_future is not None
                    and corridor_survival_future.cancel()
                ):
                    corridor_survival_future = None
                auto_confirm.eligible_since = None
                auto_confirm.released = False
                last_frame_progress = now
            if counter == previous_counter:
                input_clock_sample: dict[str, object] | None = None
                if input_clock_tracker is not None:
                    if input_clock_repeat_frame != counter:
                        input_clock_repeat_frame = counter
                        input_clock_repeat_polls = 0
                        input_clock_wall_cut_frame = None
                    input_clock_repeat_polls += 1
                    sample_now_ns = time.perf_counter_ns()
                    sample_due = (
                        input_clock_repeat_polls == 1
                        or (
                            sample_now_ns - input_clock_last_sample_ns
                            >= int(
                                args.input_clock_shadow_sample_ms
                                * 1_000_000.0
                            )
                        )
                    )
                    if sample_due:
                        input_clock_sample = capture_input_clock_shadow(reader)
                        input_clock_last_sample_ns = int(
                            input_clock_sample.get(
                                "monotonic_end_ns",
                                sample_now_ns,
                            )
                        )
                        input_clock_observation = (
                            _semantic_clock_observation(
                                input_clock_sample,
                                fallback_frame=counter,
                                context=(gameplay_epoch, stage_route_index),
                            )
                        )
                        input_clock_events = input_clock_tracker.observe(
                            input_clock_observation
                        )
                        triggers: list[str] = []
                        if input_clock_repeat_polls == 1:
                            triggers.append("first_repeat")
                        input_clock_message_key = (
                            _input_clock_message_key(input_clock_sample)
                        )
                        if (
                            input_clock_message_key
                            != input_clock_last_message_key
                        ):
                            triggers.append("message_state_changed")
                            input_clock_last_message_key = (
                                input_clock_message_key
                            )
                        frozen_seconds = max(
                            0.0,
                            now - last_frame_progress,
                        )
                        if (
                            frozen_seconds
                            >= INPUT_CLOCK_SHADOW_WALL_CUT_SECONDS
                            and input_clock_wall_cut_frame != counter
                        ):
                            triggers.append("wall_50ms_audit_cut")
                            input_clock_wall_cut_frame = counter
                        if input_clock_events:
                            triggers.append("semantic_episode_boundary")
                        if triggers:
                            record_input_clock_sample(
                                sample=input_clock_sample,
                                observation=input_clock_observation,
                                events=input_clock_events,
                                frame=counter,
                                stage_route_index=stage_route_index,
                                frozen_seconds=frozen_seconds,
                                repeat_poll_count=(
                                    input_clock_repeat_polls
                                ),
                                triggers=tuple(triggers),
                            )
                bomb_active = reader.u32(
                    ADDR_PLAYER + PLAYER_BOMB_ACTIVE_OFFSET
                )
                if auto_confirm.frozen_pulse_due(
                    now=now,
                    last_progress=last_frame_progress,
                    last_pulse=last_frozen_confirm,
                    eligible=_frozen_auto_confirm_eligible(
                        bomb_active=bool(bomb_active),
                    ),
                ):
                    input_clock_held_desired_mask = previous_mask
                    _require_foreground(api, pid)
                    send_scan_key(api, scan_code=0x2C, pressed=False)
                    time.sleep(0.04)
                    send_scan_key(api, scan_code=0x2C, pressed=True)
                    input_clock_episode_id = (
                        input_clock_tracker.mark_pulse()
                        if input_clock_tracker is not None
                        else None
                    )
                    if input_clock_tracker is not None:
                        input_clock_sample = capture_input_clock_shadow(reader)
                        input_clock_last_sample_ns = int(
                            input_clock_sample.get(
                                "monotonic_end_ns",
                                time.perf_counter_ns(),
                            )
                        )
                        input_clock_observation = (
                            _semantic_clock_observation(
                                input_clock_sample,
                                fallback_frame=counter,
                                context=(gameplay_epoch, stage_route_index),
                            )
                        )
                        input_clock_events = input_clock_tracker.observe(
                            input_clock_observation
                        )
                        record_input_clock_sample(
                            sample=input_clock_sample,
                            observation=input_clock_observation,
                            events=input_clock_events,
                            frame=counter,
                            stage_route_index=stage_route_index,
                            frozen_seconds=max(
                                0.0,
                                time.perf_counter()
                                - last_frame_progress,
                            ),
                            repeat_poll_count=input_clock_repeat_polls,
                            triggers=("wall_pulse_after",),
                        )
                    previous_mask |= SHOT
                    auto_confirm.mark_full_pulse(frame=counter)
                    last_frozen_confirm = time.perf_counter()
                    trace_sink.emit(
                        {
                                "kind": "auto_confirm_wall_pulse",
                                "frame": counter,
                                "stage_route_index": state[
                                    "stage_route_index"
                                ],
                                "player_phase": state["player"]["phase"],
                                "spell": state["spell"],
                                "input_clock_shadow_role": (
                                    INPUT_CLOCK_SHADOW_ROLE
                                    if input_clock_tracker is not None
                                    else None
                                ),
                                "held_desired_mask": (
                                    input_clock_held_desired_mask
                                ),
                                "held_desired_mask_after_pulse": (
                                    previous_mask
                                ),
                                "input_clock_shadow_episode_id": (
                                    input_clock_episode_id
                                ),
                                "input_clock_shadow": input_clock_sample,
                        },
                        flush=True,
                    )
                time.sleep(args.poll_ms / 1000.0)
                continue
            last_frame_progress = time.perf_counter()
            input_clock_repeat_frame = None
            input_clock_repeat_polls = 0
            input_clock_wall_cut_frame = None
            iteration_started = time.perf_counter()
            observe_started = iteration_started
            state = observe_state(reader)
            observe_ms = (time.perf_counter() - observe_started) * 1000.0
            if not state["gameplay_active"]:
                time.sleep(args.poll_ms / 1000.0)
                continue
            if state["route_id"] != 2:
                termination_reason = "gameplay_ended"
                break
            if (
                input_clock_tracker is not None
                and input_clock_tracker.active_episode_id is not None
            ):
                input_clock_sample = capture_input_clock_shadow(reader)
                input_clock_last_sample_ns = int(
                    input_clock_sample.get(
                        "monotonic_end_ns",
                        time.perf_counter_ns(),
                    )
                )
                input_clock_observation = _semantic_clock_observation(
                    input_clock_sample,
                    fallback_frame=counter,
                    context=(gameplay_epoch, stage_route_index),
                )
                input_clock_events = input_clock_tracker.observe(
                    input_clock_observation
                )
                input_clock_message_key = _input_clock_message_key(
                    input_clock_sample
                )
                triggers = ["manager_progress"]
                if (
                    input_clock_message_key
                    != input_clock_last_message_key
                ):
                    triggers.append("message_state_changed")
                    input_clock_last_message_key = input_clock_message_key
                if input_clock_events:
                    triggers.append("semantic_episode_boundary")
                record_input_clock_sample(
                    sample=input_clock_sample,
                    observation=input_clock_observation,
                    events=input_clock_events,
                    frame=counter,
                    stage_route_index=stage_route_index,
                    frozen_seconds=0.0,
                    repeat_poll_count=0,
                    triggers=tuple(triggers),
                )
            delay_estimator.observe(
                frame=int(state["enemy_manager_frame"]),
                input_mask=int(state["input_current"]),
            )
            if previous_counter is not None and counter != previous_counter + 1:
                gaps += 1
            spell_state = state["spell"]
            corridor_context = (
                gameplay_epoch,
                int(state["stage_route_index"]),
                (
                    int(spell_state["spell_id"])
                    if spell_state["active"]
                    else None
                ),
            )
            corridor_context_changed = corridor_commitment.set_context(
                corridor_context
            )
            for memory in enemy_body_memories:
                memory.set_context(corridor_context)
            if corridor_context_changed:
                boss_phase_tracker.reset()
                retire_pipeline_solutions(
                    (corridor_solution, corridor_pending_solution)
                )
                corridor_solution = None
                corridor_pending_solution = None
                if (
                    corridor_future is not None
                    and corridor_future.cancel()
                ):
                    corridor_future = None
                if (
                    corridor_survival_future is not None
                    and corridor_survival_future.cancel()
                ):
                    corridor_survival_future = None
            iterations += 1
            if iterations % 30 == 0:
                _require_foreground(api, pid)
            read_started = time.perf_counter()
            enemy_background_started = read_started
            if enemy_future is not None and enemy_future.done():
                enemy_snapshot = enemy_future.result()
                enemy_future = None
            if (
                _enemy_sensor_submit_due(
                    current_frame=counter,
                    last_submit_frame=enemy_last_submit,
                    pending=enemy_future is not None,
                )
            ):
                enemy_future = enemy_executor.submit(
                    capture_enemy_pool_snapshot,
                    reader,
                )
                enemy_last_submit = counter
            if enemy_snapshot is None:
                enemy_bodies = ()
                background_dormant_enemy_body_pointers = frozenset()
            else:
                (
                    enemy_bodies,
                    background_dormant_enemy_body_pointers,
                ) = enemy_background_memory.merge_snapshot(
                    enemy_snapshot,
                    frame=int(state["enemy_manager_frame"]),
                )
            enemy_pool_read_ms = (
                enemy_snapshot.read_ms
                if enemy_snapshot is not None
                else None
            )
            enemy_body_snapshot_frame = (
                enemy_snapshot.frame_after
                if enemy_snapshot is not None
                else None
            )
            enemy_background_ms = (
                time.perf_counter() - enemy_background_started
            ) * 1000.0
            enemy_prefix_capture_started = time.perf_counter()
            enemy_prefix_snapshot = capture_enemy_pool_prefix_contiguous(
                reader,
                include_main_ecl_vms=trace_nonspell_main_vms,
                include_combat_progress=trace_enemy_combat_progress,
            )
            enemy_prefix_capture_ms = (
                time.perf_counter() - enemy_prefix_capture_started
            ) * 1000.0
            enemy_prefix_merge_started = time.perf_counter()
            (
                enemy_prefix_bodies,
                prefix_dormant_enemy_body_pointers,
            ) = enemy_body_memory.merge_snapshot(
                enemy_prefix_snapshot,
                frame=int(state["enemy_manager_frame"]),
            )
            prefix_end = (
                ENEMY_POOL_BASE + ENEMY_LOCAL_PREFIX_SIZE * ENEMY_STRIDE
            )
            dormant_enemy_body_pointers = frozenset(
                set(prefix_dormant_enemy_body_pointers)
                | {
                    pointer
                    for pointer in background_dormant_enemy_body_pointers
                    if pointer >= prefix_end
                }
            )
            enemy_bodies = merge_enemy_pool_prefix(
                enemy_bodies,
                enemy_prefix_bodies,
            )
            enemy_prefix_merge_ms = (
                time.perf_counter() - enemy_prefix_merge_started
            ) * 1000.0
            raw_pools = sensor.capture_raw_pools()
            bullet_blob = raw_pools.bullet_blob
            laser_blob = raw_pools.laser_blob
            item_blob = raw_pools.item_blob
            bullet_frame_before = raw_pools.bullet_frame_before
            bullet_frame_after = raw_pools.bullet_frame_after
            bullet_pool_read_ms = raw_pools.bullet_pool_read_ms
            laser_pool_read_ms = raw_pools.laser_pool_read_ms
            item_pool_read_ms = raw_pools.item_pool_read_ms
            ecl_vm_snapshot: EclVmSnapshot | None = None
            ecl_lookahead: EclLookaheadResult | None = None
            tagged_velocity_toggles: tuple[TaggedVelocityToggle, ...] = ()
            ecl_lookahead_error: str | None = None
            ecl_frame_before: int | None = None
            ecl_frame_after: int | None = None
            spell_enemy_body_guard: SpellEnemyBodyGuard | None = None
            spell_enemy_body_guard_error: str | None = None
            boss_guard_frame_before: int | None = None
            boss_guard_frame_after: int | None = None
            boss_phase_snapshot: BossPhaseSnapshot | None = None
            boss_phase_error: str | None = None
            boss_phase_progress: PhaseProgressObservation | None = None
            spell_enemy_pointer = int(spell_state.get("enemy_pointer", 0))
            boss_phase_read_started = time.perf_counter()
            try:
                boss_phase_snapshot = capture_boss_phase_snapshot(
                    reader,
                    preferred_pointer=(
                        spell_enemy_pointer
                        if spell_state.get("active")
                        else 0
                    ),
                )
            except (OSError, RuntimeError, ValueError, struct.error) as error:
                boss_phase_error = f"{type(error).__name__}: {error}"
            boss_phase_read_ms = (
                time.perf_counter() - boss_phase_read_started
            ) * 1000.0
            boss_enemy_pointer = (
                boss_phase_snapshot.pointer
                if boss_phase_snapshot is not None
                else (
                    spell_enemy_pointer
                    if spell_state.get("active")
                    else 0
                )
            )
            spell_enemy_guard_read_ms = 0.0
            if boss_enemy_pointer:
                spell_enemy_guard_read_started = time.perf_counter()
                boss_guard_frame_before = reader.u32(
                    ADDR_ENEMY_MANAGER_FRAME
                )
                try:
                    spell_enemy_body_guard = read_enemy_body_guard(
                        reader,
                        pointer=boss_enemy_pointer,
                    )
                except (OSError, RuntimeError, ValueError, struct.error) as error:
                    spell_enemy_body_guard_error = (
                        f"{type(error).__name__}: {error}"
                    )
                boss_guard_frame_after = reader.u32(
                    ADDR_ENEMY_MANAGER_FRAME
                )
                spell_enemy_guard_read_ms = (
                    time.perf_counter() - spell_enemy_guard_read_started
                ) * 1000.0
            ecl_lookahead_read_ms = 0.0
            if spell_state.get("active") and spell_enemy_pointer:
                ecl_capture = capture_main_ecl(
                    reader,
                    enemy_pointer=spell_enemy_pointer,
                    instruction_cache=ecl_instruction_cache,
                    horizon_frames=ECL_CALLBACK_LOOKAHEAD_FRAMES,
                    active_difficulty_mask=(
                        1 << int(state["difficulty_index"])
                    ),
                )
                ecl_vm_snapshot = ecl_capture.snapshot
                ecl_lookahead = ecl_capture.lookahead
                tagged_velocity_toggles = (
                    ecl_capture.tagged_velocity_toggles
                )
                ecl_lookahead_error = ecl_capture.error
                ecl_frame_before = ecl_capture.frame_before
                ecl_frame_after = ecl_capture.frame_after
                ecl_lookahead_read_ms = ecl_capture.elapsed_ms
            hazard_read_bookkeeping_started = time.perf_counter()
            if (
                spell_enemy_body_guard is not None
                and boss_guard_frame_before is not None
                and boss_guard_frame_after is not None
            ):
                tracked_spell_bodies, _dormant = (
                    spell_enemy_body_memory.merge_snapshot(
                        EnemyPoolSnapshot(
                            boss_guard_frame_before,
                            boss_guard_frame_after,
                            (spell_enemy_body_guard.body,),
                            0.0,
                        ),
                        frame=int(state["enemy_manager_frame"]),
                    )
                )
                if tracked_spell_bodies:
                    spell_enemy_body_guard = replace(
                        spell_enemy_body_guard,
                        body=tracked_spell_bodies[0],
                    )
            boss_phase_progress = boss_phase_tracker.observe(
                (
                    boss_phase_snapshot.as_progress_state(
                        context=corridor_context,
                        bomb_active=bool(
                            state["player"]["bomb_active"]
                        ),
                    )
                    if boss_phase_snapshot is not None
                    else None
                )
            )
            enemy_bodies = merge_spell_enemy_body_guard(
                enemy_bodies,
                spell_enemy_body_guard,
            )
            counter_after_read = reader.u32(0x0164D30C)
            hazard_read_bookkeeping_ms = (
                time.perf_counter() - hazard_read_bookkeeping_started
            ) * 1000.0
            read_ms = (time.perf_counter() - read_started) * 1000.0
            if (
                enemy_prefix_snapshot.frame_after
                < enemy_prefix_snapshot.frame_before
                or counter_after_read < enemy_prefix_snapshot.frame_after
                or bullet_frame_after < bullet_frame_before
                or counter_after_read < bullet_frame_after
                or (
                    ecl_frame_before is not None
                    and ecl_frame_after is not None
                    and ecl_frame_after < ecl_frame_before
                )
                or (
                    boss_guard_frame_before is not None
                    and boss_guard_frame_after is not None
                    and boss_guard_frame_after < boss_guard_frame_before
                )
            ):
                gaps += 1
                continue
            snapshot_lag = max(0, counter_after_read - int(state["enemy_manager_frame"]))
            hazard_frame_before = min(
                enemy_prefix_snapshot.frame_before,
                bullet_frame_before,
                (
                    boss_guard_frame_before
                    if boss_guard_frame_before is not None
                    else bullet_frame_before
                ),
            )
            hazard_frame_after = max(
                enemy_prefix_snapshot.frame_after,
                bullet_frame_after,
                (
                    boss_guard_frame_after
                    if boss_guard_frame_after is not None
                    else bullet_frame_after
                ),
            )
            hazard_alignment = HazardEpochAlignment(
                source_frame=int(state["enemy_manager_frame"]),
                hazard_window=FrameWindow(
                    hazard_frame_before,
                    hazard_frame_after,
                ),
                current_frame=counter_after_read,
                event_window=(
                    FrameWindow(ecl_frame_before, ecl_frame_after)
                    if (
                        ecl_frame_before is not None
                        and ecl_frame_after is not None
                    )
                    else None
                ),
            )
            if not hazard_alignment.fits_epoch(
                maximum_extent=MAX_SENSOR_EPOCH_EXTENT_FRAMES
            ):
                gaps += 1
                gameplay_epoch += 1
                safe_mask = previous_mask & SHOT
                issue_controller.dispatch(
                    previous_mask,
                    safe_mask,
                    require_foreground=True,
                )
                previous_mask = safe_mask
                previous_direction = 0
                decision_frame_deltas.clear()
                delay_estimator.reset()
                retire_pipeline_solutions(
                    (corridor_solution, corridor_pending_solution)
                )
                corridor_solution = None
                corridor_pending_solution = None
                corridor_context = None
                corridor_commitment = CorridorCommitment()
                for memory in enemy_body_memories:
                    memory.clear()
                boss_phase_tracker.reset()
                ecl_instruction_cache.clear()
                if bullet_birth_tracker is not None:
                    bullet_birth_tracker.reset()
                if corridor_future is not None:
                    corridor_future.cancel()
                if corridor_survival_future is not None:
                    corridor_survival_future.cancel()
                trace_sink.emit(
                    {
                            "kind": "sensor_epoch_discontinuity",
                            "frame": counter_after_read,
                            "source_frame": state["enemy_manager_frame"],
                            "gameplay_epoch": gameplay_epoch,
                            "maximum_extent": (
                                MAX_SENSOR_EPOCH_EXTENT_FRAMES
                            ),
                            "observed_extent": (
                                hazard_alignment.total_frame_extent
                            ),
                            "hazard_window": [
                                bullet_frame_before,
                                bullet_frame_after,
                            ],
                            "event_window": (
                                [ecl_frame_before, ecl_frame_after]
                                if (
                                    ecl_frame_before is not None
                                    and ecl_frame_after is not None
                                )
                                else None
                            ),
                            "spell": state["spell"],
                            "released_to_mask": safe_mask,
                    },
                    flush=True,
                )
                continue
            player_to_hazard_lag = (
                hazard_alignment.source_to_hazard_lag
            )
            hazard_snapshot_age = hazard_alignment.hazard_age
            bullet_capture_span = hazard_alignment.hazard_window.span
            ecl_event_frame_offset: int | None = None
            ecl_event_frame_uncertainty: int | None = None
            if ecl_vm_snapshot is not None:
                ecl_event_frame_offset = (
                    hazard_alignment.event_frame_offset
                )
                ecl_event_frame_uncertainty = (
                    hazard_alignment.event_frame_uncertainty
                )
            decode_started = time.perf_counter()
            bullet_decode_started = decode_started
            bullets = (
                decode_bullets(
                    bullet_blob,
                    retain_transform_runtime=True,
                )
                if args.trace_transform_runtime
                else decode_live_planning_bullets(
                    bullet_blob,
                    backend=args.bullet_decode_backend,
                )
            )
            bullet_decode_ms = (
                time.perf_counter() - bullet_decode_started
            ) * 1000.0
            bullet_event_attach_started = time.perf_counter()
            if ecl_vm_snapshot is not None and tagged_velocity_toggles:
                bullets = attach_tagged_velocity_toggles(
                    bullets,
                    vm_snapshot=ecl_vm_snapshot,
                    toggles=tagged_velocity_toggles,
                    frame_offset=ecl_event_frame_offset or 0,
                    event_frame_uncertainty=(
                        ecl_event_frame_uncertainty or 0
                    ),
                )
            bullet_event_attach_ms = (
                time.perf_counter() - bullet_event_attach_started
            ) * 1000.0
            laser_decode_started = time.perf_counter()
            lasers = decode_lasers(laser_blob)
            laser_decode_ms = (
                time.perf_counter() - laser_decode_started
            ) * 1000.0
            item_decode_started = time.perf_counter()
            items = decode_items(item_blob)
            item_decode_ms = (
                time.perf_counter() - item_decode_started
            ) * 1000.0
            decode_ms = (time.perf_counter() - decode_started) * 1000.0
            player = state["player"]
            resources = state["resources"]
            if resources is None:
                termination_reason = "resources_unavailable"
                break
            can_bomb = (
                not args.no_bomb
                and args.normal_bomb
                and player["phase"] == 0
                and not player["bomb_active"]
                and resources["bombs"] > 0
                and counter_after_read - last_bomb_counter > 30
            )
            projected_player_x, projected_player_y = _project_player_for_read_lag(
                float(player["x"]),
                float(player["y"]),
                previous_mask,
                snapshot_lag,
            )
            delay_estimate = delay_estimator.estimate(
                frame=counter_after_read,
                default=args.control_delay_frames,
            )
            input_clock_delay_support = tuple(delay_estimate.support)
            control_delay_frames = delay_estimate.nominal
            control_origin_x, control_origin_y = _project_player_for_read_lag(
                float(player["x"]),
                float(player["y"]),
                previous_mask,
                control_delay_frames,
            )
            held_desired_mask = previous_mask & SUPPORTED_INPUT_MASK
            captured_iteration = CapturedIteration(
                gameplay_epoch=gameplay_epoch,
                stage_route_index=int(state["stage_route_index"]),
                spell_id=(
                    int(spell_state["spell_id"])
                    if spell_state["active"]
                    else None
                ),
                context_key=corridor_context,
                source_frame=int(state["enemy_manager_frame"]),
                snapshot_frame=counter_after_read,
                player_x=float(player["x"]),
                player_y=float(player["y"]),
                projected_player_x=projected_player_x,
                projected_player_y=projected_player_y,
                native_active_mask=int(state["input_current"]),
                held_desired_mask=held_desired_mask,
                previous_direction=previous_direction,
                can_bomb=can_bomb,
                power=float(resources["power"]),
                bombs=float(resources["bombs"]),
                bullets=bullets,
                lasers=lasers,
                enemy_bodies=enemy_bodies,
                items=items,
                hazard_alignment=hazard_alignment,
                snapshot_lag=snapshot_lag,
                player_to_hazard_lag=player_to_hazard_lag,
                hazard_snapshot_age=hazard_snapshot_age,
                delay_estimate=delay_estimate,
                control_delay_frames=control_delay_frames,
                context_changed=corridor_context_changed,
            )
            corridor_started = time.perf_counter()
            corridor_updated = False
            if (
                corridor_survival_future is not None
                and corridor_survival_future.done()
            ):
                labeled_solution = corridor_survival_future.result()
                corridor_survival_future = None
                if (
                    corridor_solution is not None
                    and corridor_solution.source_frame
                    == labeled_solution.source_frame
                    and corridor_solution.context_key
                    == labeled_solution.context_key
                ):
                    corridor_solution = labeled_solution
                elif (
                    corridor_pending_solution is not None
                    and corridor_pending_solution.source_frame
                    == labeled_solution.source_frame
                    and corridor_pending_solution.context_key
                    == labeled_solution.context_key
                ):
                    corridor_pending_solution = labeled_solution
            if corridor_pending_solution is not None:
                prior_active = corridor_solution
                pending_candidate = corridor_pending_solution
                (
                    corridor_solution,
                    corridor_pending_solution,
                ) = _stage_corridor_solution(
                    corridor_solution,
                    corridor_pending_solution,
                    current_frame=counter_after_read,
                    context_key=corridor_context,
                )
                if corridor_solution is pending_candidate:
                    corridor_commitment.accept(
                        corridor_solution,
                        current_frame=counter_after_read,
                    )
                    corridor_updated = True
                retire_arguments = (
                    (prior_active, pending_candidate),
                    (corridor_solution, corridor_pending_solution),
                )
                retire_pipeline_solutions(*retire_arguments)
            if corridor_future is not None and corridor_future.done():
                completed_solution = corridor_future.result()
                corridor_future = None
                require_corridor_background_priority(
                    completed_solution,
                    requested=args.corridor_background_low_priority,
                )
                corridor_policy_lead.observe(
                    completed_solution.worker_ms
                    if completed_solution.worker_ms is not None
                    else completed_solution.solve_ms
                )
                prior_active = corridor_solution
                prior_pending = corridor_pending_solution
                (
                    corridor_solution,
                    corridor_pending_solution,
                ) = _stage_corridor_solution(
                    corridor_solution,
                    completed_solution,
                    current_frame=counter_after_read,
                    context_key=corridor_context,
                )
                if (
                    corridor_pending_solution is None
                    and corridor_solution is completed_solution
                ):
                    corridor_commitment.accept(
                        completed_solution,
                        current_frame=counter_after_read,
                    )
                    corridor_updated = True
                retire_arguments = (
                    (
                        prior_active,
                        prior_pending,
                        completed_solution,
                    ),
                    (corridor_solution, corridor_pending_solution),
                )
                retire_pipeline_solutions(*retire_arguments)
            if (
                corridor_executor is not None
                and corridor_future is None
                and corridor_pending_solution is None
                and _corridor_submit_due(
                    current_frame=counter_after_read,
                    last_submit_frame=corridor_last_submit,
                    interval_frames=args.corridor_every,
                )
            ):
                forecast_lead_frames = corridor_policy_lead.frames
                policy_delay_support = delay_support_envelope(
                    delay_estimate.support,
                    minimum=LIVE_CONTROL_DELAY_MIN,
                    maximum=LIVE_CONTROL_DELAY_MAX,
                    padding=ASYNC_POLICY_DELAY_PADDING,
                )
                forecast_player_x, forecast_player_y = (
                    _project_player_for_read_lag(
                        float(player["x"]),
                        float(player["y"]),
                        previous_mask,
                        snapshot_lag + forecast_lead_frames,
                    )
                )
                corridor_future = corridor_executor.submit(
                    _solve_corridor,
                    source_frame=(
                        counter_after_read + forecast_lead_frames
                    ),
                    snapshot_frame=counter_after_read,
                    forecast_lead_frames=forecast_lead_frames,
                    player_x=forecast_player_x,
                    player_y=forecast_player_y,
                    bullets=bullets,
                    lasers=lasers,
                    enemy_bodies=enemy_bodies,
                    snapshot_lag=hazard_snapshot_age,
                    control_delay_candidates=policy_delay_support,
                    observed_control_delay_candidates=(
                        delay_estimate.support
                    ),
                    nominal_control_delay=control_delay_frames,
                    active_action=_action_name_from_mask(previous_mask),
                    safety_value_horizon_frames=(
                        args.safety_value_horizon
                    ),
                    required_gate_lane=(
                        corridor_commitment.active_lane(counter_after_read)
                    ),
                    context_key=corridor_context,
                    audit_capsule_dir=args.viability_audit_dir,
                    audit_executor=audit_executor,
                    pipeline_prewarm_shadow=(
                        args.pipeline_prewarm_shadow
                    ),
                    background_low_priority=(
                        args.corridor_background_low_priority
                    ),
                    native_viability_worker_limit=(
                        args.corridor_native_workers
                    ),
                )
                corridor_last_submit = counter_after_read
            if (
                args.postpublished_survival_shadow
                and survival_executor is not None
                and corridor_survival_future is None
            ):
                survival_candidate = (
                    corridor_pending_solution or corridor_solution
                )
                if (
                    survival_candidate is not None
                    and survival_candidate.context_key == corridor_context
                    and survival_candidate.postpublished_survival_parity
                    is None
                ):
                    corridor_survival_future = survival_executor.submit(
                        _solve_postpublished_survival,
                        survival_candidate,
                    )
            observed_input_action = _action_name_from_mask(
                captured_iteration.native_active_mask
            )
            pending_command_estimate = delay_estimator.pending_estimate(
                frame=counter_after_read,
            )
            pipeline_pending_command = (
                PendingCommand(
                    _action_name_from_mask(
                        pending_command_estimate.expected_mask
                    ),
                    pending_command_estimate.remaining_frames,
                )
                if (
                    pending_command_estimate is not None
                    and pending_command_estimate.remaining_frames
                )
                else None
            )
            policy_query_request = PolicyQueryRequest(
                solution=corridor_solution,
                target_frame=(
                    captured_iteration.source_frame
                    + captured_iteration.control_delay_frames
                ),
                query_frame=captured_iteration.snapshot_frame,
                player_x=captured_iteration.projected_player_x,
                player_y=captured_iteration.projected_player_y,
                active_action=_action_name_from_mask(
                    captured_iteration.held_desired_mask
                ),
                observed_action=observed_input_action,
                pending_command=pipeline_pending_command,
                lookahead_frames=args.corridor_lookahead,
                max_age_frames=args.corridor_max_age,
                current_delay_frames=(
                    captured_iteration.delay_estimate.support
                ),
                pipeline_prewarm_shadow=args.pipeline_prewarm_shadow,
            )
            primary_policy_query = policy_coordinator.query_primary(
                policy_query_request
            )
            corridor_target = primary_policy_query.target
            viability_query = primary_policy_query.viability_query
            pipeline_shadow_snapshot = build_pipeline_shadow_snapshot(
                supported_mask=SUPPORTED_INPUT_MASK,
                native_active_mask=captured_iteration.native_active_mask,
                held_desired_mask=captured_iteration.held_desired_mask,
                pending_estimate=pending_command_estimate,
                action_from_mask=_local_pipeline_action_from_mask,
                gameplay_epoch=captured_iteration.gameplay_epoch,
                stage_route_index=(
                    captured_iteration.stage_route_index
                ),
                spell_id=captured_iteration.spell_id,
                manager_frame=captured_iteration.source_frame,
                query_frame=captured_iteration.snapshot_frame,
                target_frame=policy_query_request.target_frame,
                player_x=captured_iteration.projected_player_x,
                player_y=captured_iteration.projected_player_y,
                hazard_horizon_frames=PLANNER_THREAT_HORIZON,
                corridor_solution=corridor_solution,
            )
            observed_local_pipeline_root = (
                pipeline_shadow_snapshot.local_root
            )
            local_pipeline_root_record = pipeline_shadow_snapshot.record
            candidate_verifier_target: (
                CandidateVerifierTarget | None
            ) = None
            candidate_verifier_revision: int | None = None
            candidate_verifier_submit_ms = 0.0
            candidate_verifier_submit_error: str | None = None
            candidate_verifier_eligibility = (
                "boolean_losing"
                if (
                    viability_query is not None
                    and viability_query.available
                    and not viability_query.state_viable
                )
                else (
                    "boolean_viable"
                    if (
                        viability_query is not None
                        and viability_query.available
                    )
                    else "policy_unavailable"
                )
            )
            if (
                candidate_verifier is not None
                and candidate_verifier_eligibility == "boolean_losing"
            ):
                candidate_request = (
                    _corridor_candidate_verifier_target(
                        corridor_solution,
                        current_frame=counter_after_read,
                        player_x=projected_player_x,
                        player_y=projected_player_y,
                        observed_action=observed_input_action,
                        pending_command=pipeline_pending_command,
                        max_age_frames=args.corridor_max_age,
                        horizon_frames=(
                            CANDIDATE_VERIFIER_HORIZON_FRAMES
                        ),
                    )
                )
                if candidate_request is not None:
                    (
                        candidate_problem,
                        candidate_verifier_target,
                    ) = candidate_request
                    candidate_submit_started = time.perf_counter()
                    try:
                        candidate_verifier_revision = (
                            candidate_verifier.submit(
                                problem=candidate_problem,
                                target=candidate_verifier_target,
                            )
                        )
                    except Exception as error:
                        candidate_verifier_submit_error = (
                            f"{type(error).__name__}: {error}"
                        )
                    candidate_verifier_submit_ms = (
                        time.perf_counter() - candidate_submit_started
                    ) * 1000.0
            elif candidate_verifier is not None:
                candidate_submit_started = time.perf_counter()
                try:
                    candidate_verifier.discard_target()
                except Exception as error:
                    candidate_verifier_submit_error = (
                        f"{type(error).__name__}: {error}"
                    )
                candidate_verifier_submit_ms = (
                    time.perf_counter() - candidate_submit_started
                ) * 1000.0
            policy_queries = policy_coordinator.complete_query(
                policy_query_request,
                primary_policy_query,
            )
            pipeline_prewarm_query = (
                policy_queries.pipeline_prewarm_query
            )
            postpublished_survival_query = (
                policy_queries.postpublished_survival_query
            )
            safety_value_query = policy_queries.safety_value_query
            policy_guidance = policy_queries.guidance
            corridor_overhead_ms = (
                time.perf_counter() - corridor_started
            ) * 1000.0
            service_update = ServiceUpdate(
                context_key=captured_iteration.context_key,
                query_frame=captured_iteration.snapshot_frame,
                active_solution=corridor_solution,
                pending_solution=corridor_pending_solution,
                corridor_updated=corridor_updated,
                elapsed_ms=corridor_overhead_ms,
            )
            published_guidance = PublishedGuidance(
                capture=captured_iteration,
                service_update=service_update,
                request=policy_query_request,
                primary_query=primary_policy_query,
                completed_query=policy_queries,
                pipeline_shadow=pipeline_shadow_snapshot,
            )
            action_hold_frames = _estimate_live_action_hold(
                tuple(decision_frame_deltas)
            )
            damage_target_x: float | None = None
            damage_target_half_width = 0.0
            damageable = False
            if (
                boss_phase_snapshot is not None
                and boss_phase_progress is not None
                and spell_enemy_body_guard is not None
                and spell_enemy_body_guard.body.pointer
                == boss_phase_snapshot.pointer
            ):
                boss_body = spell_enemy_body_guard.body
                damage_target_x = (
                    boss_body.x
                    + boss_body.vx
                    * (player_to_hazard_lag + args.horizon)
                )
                # Enemy-body contact expands the native full size by 1.5.
                # Player-shot damage uses the unexpanded AABB.
                damage_target_half_width = (
                    spell_enemy_body_guard.body.half_width * (2.0 / 3.0)
            )
                damageable = boss_phase_progress.state.damageable
            plan_started = time.perf_counter()
            local_proposal = choose_local_proposal_request(
                LocalPlannerRequest(
                    physical=PhysicalHazardSnapshot(
                        player_x=(
                            published_guidance.capture.player_x
                        ),
                        player_y=(
                            published_guidance.capture.player_y
                        ),
                        bullets=published_guidance.capture.bullets,
                        lasers=published_guidance.capture.lasers,
                        enemy_bodies=(
                            published_guidance.capture.enemy_bodies
                        ),
                        items=published_guidance.capture.items,
                        snapshot_lag=(
                            published_guidance.capture.player_to_hazard_lag
                        ),
                    ),
                    actuator=ActuatorPipeline(
                        previous_direction=(
                            published_guidance.capture.previous_direction
                        ),
                        can_bomb=published_guidance.capture.can_bomb,
                        previous_focus=bool(
                            published_guidance.capture.held_desired_mask
                            & FOCUS
                        ),
                        control_delay_frames=(
                            published_guidance.capture.control_delay_frames
                        ),
                        control_delay_candidates=(
                            published_guidance.capture.delay_estimate.support
                        ),
                        action_hold_frames=action_hold_frames,
                    ),
                    guidance=GlobalGuidance(
                        target_x=(
                            corridor_target[0]
                            if corridor_target is not None
                            else None
                        ),
                        target_y=(
                            corridor_target[1]
                            if corridor_target is not None
                            else None
                        ),
                        target_deadline=(
                            corridor_target[2]
                            if corridor_target is not None
                            else None
                        ),
                        allowed_first_actions=(
                            policy_guidance.allowed_first_actions
                        ),
                        viability_repair_volumes=(
                            policy_guidance.repair_volumes
                        ),
                        viability_recovery_distances=(
                            policy_guidance.recovery_distances
                        ),
                        viability_safety_actions=(
                            policy_guidance.safety_actions
                        ),
                        viability_safety_state_value=(
                            policy_guidance.safety_state_value
                        ),
                        viability_survival_actions=(
                            policy_guidance.survival_actions
                        ),
                        viability_survival_frames=(
                            policy_guidance.survival_frames
                        ),
                        viability_survival_bottleneck_margin=(
                            policy_guidance.survival_bottleneck_margin
                        ),
                        viability_position_error=(
                            policy_guidance.position_error
                        ),
                    ),
                    config=PlannerConfig(
                        horizon=args.horizon,
                        threat_horizon=args.threat_horizon,
                        beam_width=args.beam_width,
                        preserve_previous_direction_inertia=(
                            not corridor_context_changed
                        ),
                    ),
                    objective=ObjectiveContext(
                        power=published_guidance.capture.power,
                        bombs=published_guidance.capture.bombs,
                        damage_target_x=damage_target_x,
                        damage_target_half_width=(
                            damage_target_half_width
                        ),
                        damageable=damageable,
                    ),
                )
            )
            decision = local_proposal.decision
            plan_ms = (time.perf_counter() - plan_started) * 1000.0
            pre_issue_action = decision.action
            pre_issue_mask = decision.mask
            issue_path_started = time.perf_counter()
            alignment_frame = int(state["enemy_manager_frame"])
            fresh_enemy_issue = recertify_fresh_enemy_prefix(
                proposal=local_proposal,
                reader=reader,
                memory=enemy_body_memory,
                alignment_frame=alignment_frame,
                planned_prefix_snapshot=enemy_prefix_snapshot,
                planned_prefix_bodies=enemy_prefix_bodies,
                enemy_bodies=enemy_bodies,
                commit=lambda proposal, fresh_enemy_bodies: (
                    commit_local_proposal_for_fresh_hazards(
                        proposal,
                        player_x=float(player["x"]),
                        player_y=float(player["y"]),
                        previous_mask=previous_mask,
                        delay_frames=delay_estimate.support,
                        action_hold_frames=action_hold_frames,
                        bullets=bullets,
                        lasers=lasers,
                        enemy_bodies=fresh_enemy_bodies,
                        snapshot_lag=player_to_hazard_lag,
                        allowed_first_actions=(
                            policy_guidance.allowed_first_actions
                        ),
                        viability_repair_volumes=(
                            policy_guidance.repair_volumes
                        ),
                        viability_recovery_distances=(
                            policy_guidance.recovery_distances
                        ),
                        viability_safety_actions=(
                            policy_guidance.safety_actions
                        ),
                        viability_survival_actions=(
                            policy_guidance.survival_actions
                        ),
                    )
                ),
                read_started=issue_path_started,
                dependencies=FreshEnemyIssueDependencies(
                    capture_prefix=capture_enemy_pool_prefix_contiguous,
                    detect_changes=issue_enemy_snapshot_changes,
                    merge_prefix=merge_enemy_pool_prefix,
                    monotonic=time.perf_counter,
                ),
            )
            issue_enemy_prefix_snapshot = fresh_enemy_issue.prefix_snapshot
            issue_enemy_prefix_bodies = fresh_enemy_issue.prefix_bodies
            issue_dormant_enemy_body_pointers = (
                fresh_enemy_issue.dormant_pointers
            )
            issue_enemy_changes = fresh_enemy_issue.changes
            issue_enemy_read_ms = fresh_enemy_issue.read_ms
            issue_enemy_recertificate_ms = (
                fresh_enemy_issue.recertification_ms
            )
            issue_enemy_bodies_for_shadow = (
                fresh_enemy_issue.enemy_bodies_for_shadow
            )
            decision = fresh_enemy_issue.decision
            plan_ms += issue_enemy_recertificate_ms
            post_issue_guard_action = decision.action
            post_issue_guard_mask = decision.mask
            action_issue_observation = observe_action_issue(
                reader,
                source_frame=int(state["enemy_manager_frame"]),
                capture_frame=counter_after_read,
                delay_support=delay_estimate.support,
            )
            phase_now = action_issue_observation.player_phase
            predeath_now = action_issue_observation.predeath_counter
            counter_at_action = action_issue_observation.issue_frame
            action_alignment = action_issue_observation.alignment
            if action_alignment.crosses_contiguous_epoch(
                maximum_post_capture_advance=(
                    MAX_ACTION_CONTIGUOUS_ADVANCE_FRAMES
                )
            ):
                gaps += 1
                gameplay_epoch += 1
                safe_mask = previous_mask & SHOT
                issue_controller.dispatch(
                    previous_mask,
                    safe_mask,
                    require_foreground=True,
                )
                previous_mask = safe_mask
                previous_direction = 0
                decision_frame_deltas.clear()
                delay_estimator.reset()
                retire_pipeline_solutions(
                    (corridor_solution, corridor_pending_solution)
                )
                corridor_solution = None
                corridor_pending_solution = None
                corridor_context = None
                corridor_commitment = CorridorCommitment()
                for memory in enemy_body_memories:
                    memory.clear()
                boss_phase_tracker.reset()
                ecl_instruction_cache.clear()
                if bullet_birth_tracker is not None:
                    bullet_birth_tracker.reset()
                if corridor_future is not None:
                    corridor_future.cancel()
                if corridor_survival_future is not None:
                    corridor_survival_future.cancel()
                trace_sink.emit(
                    {
                            "kind": "action_epoch_discontinuity",
                            "frame": counter_at_action,
                            "source_frame": state["enemy_manager_frame"],
                            "capture_frame": counter_after_read,
                            "gameplay_epoch": gameplay_epoch,
                            "action_lag": action_alignment.action_lag,
                            "post_capture_advance": (
                                action_alignment.post_capture_advance
                            ),
                            "maximum_contiguous_advance": (
                                MAX_ACTION_CONTIGUOUS_ADVANCE_FRAMES
                            ),
                            "control_delay_candidates": (
                                delay_estimate.support
                            ),
                            "planned_action": decision.action,
                            "planned_mask": decision.mask,
                            "spell": state["spell"],
                            "released_to_mask": safe_mask,
                    },
                    flush=True,
                )
                continue
            planned_action = decision.action
            planned_mask = decision.mask
            action_deadline_missed = action_alignment.deadline_missed
            decision = apply_deadline_hold(
                decision,
                deadline_missed=action_deadline_missed,
                previous_mask=previous_mask,
                focus_bit=FOCUS,
                action_name_from_mask=_action_name_from_mask,
            )
            hit_started = phase_now == 2 and previous_action_phase != 2
            hit_contact_observation = None
            if hit_started:
                hit_count += 1
                delay_estimator.register_hit(counter_at_action)
                hit_contact_observation = capture_hit_contact_observation(
                    reader,
                    state["spell"],
                )
                if (
                    args.stop_after_hits
                    and hit_count >= args.stop_after_hits
                    and stop_after_frame is None
                ):
                    stop_after_frame = counter_at_action + args.post_hit_frames
            issue_overrides = apply_post_hit_input_overrides(
                decision,
                no_bomb=args.no_bomb,
                phase_now=phase_now,
                predeath_now=predeath_now,
                bomb_stock=float(resources["bombs"]),
                counter_at_action=counter_at_action,
                last_bomb_counter=last_bomb_counter,
                bomb_bit=BOMB,
                auto_confirm_eligible=_auto_confirm_eligible(
                    player_phase=phase_now,
                    bomb_active=bool(player["bomb_active"]),
                    active_bullets=len(bullets),
                    active_lasers=len(lasers),
                ),
                auto_confirm_apply=auto_confirm.apply,
            )
            decision = issue_overrides.decision
            can_deathbomb = issue_overrides.can_deathbomb
            auto_confirm_event = issue_overrides.auto_confirm_event
            last_bomb_counter = issue_overrides.last_bomb_counter
            candidate_verifier_outcome: (
                CandidateVerifierOutcome | None
            ) = None
            candidate_verifier_snapshot: (
                CandidateVerifierSnapshot | None
            ) = None
            candidate_verifier_lookup_ms = 0.0
            candidate_publication_ms = 0.0
            candidate_verifier_lookup_error: str | None = None
            candidate_shadow_publications: tuple[
                dict[str, object], ...
            ] = ()
            if candidate_verifier is not None:
                candidate_lookup_started = time.perf_counter()
                try:
                    if candidate_verifier_target is not None:
                        candidate_verifier_outcome = (
                            candidate_verifier.lookup(
                                candidate_verifier_target
                            )
                        )
                    candidate_verifier_snapshot = (
                        candidate_verifier.snapshot()
                    )
                except Exception as error:
                    candidate_verifier_lookup_error = (
                        f"{type(error).__name__}: {error}"
                    )
                candidate_verifier_lookup_ms = (
                    time.perf_counter() - candidate_lookup_started
                ) * 1000.0
                candidate_publication_started = time.perf_counter()
                candidate_shadow_publications = (
                    _candidate_shadow_publications(
                        candidate_verifier_outcome,
                        issue_action_certificates=(
                            decision.issue_action_certificates
                        ),
                        issued_action=_action_name_from_mask(
                            decision.mask
                        ),
                        issue_frame=counter_at_action,
                        deadline_missed=action_deadline_missed,
                        input_override=bool(
                            can_deathbomb
                            or auto_confirm_event is not None
                        ),
                    )
                )
                candidate_publication_ms = (
                    time.perf_counter() - candidate_publication_started
                ) * 1000.0
            physical_issue = commit_physical_issue(
                PhysicalIssueRequest(
                    capture=captured_iteration,
                    proposal=local_proposal,
                    decision=decision,
                    alignment=action_alignment,
                    previous_mask=previous_mask,
                    direction_mask=UP | DOWN | LEFT | RIGHT,
                    pre_issue_action=pre_issue_action,
                    pre_issue_mask=pre_issue_mask,
                    post_guard_action=post_issue_guard_action,
                    post_guard_mask=post_issue_guard_mask,
                    planned_action=planned_action,
                    planned_mask=planned_mask,
                    fresh_enemy_changed=bool(issue_enemy_changes),
                    recertification_ms=issue_enemy_recertificate_ms,
                    issue_path_started=issue_path_started,
                    iteration_started=iteration_started,
                ),
                issue_controller=issue_controller,
                delay_recorder=delay_estimator,
                clock=time.perf_counter,
            )
            fresh_issue_result = physical_issue.issue
            input_dispatch = fresh_issue_result.dispatch
            input_ms = input_dispatch.input_ms
            issue_path_ms = fresh_issue_result.issue_path_ms
            observe_to_issue_ms = fresh_issue_result.observe_to_issue_ms
            previous_mask = physical_issue.previous_mask
            previous_direction = physical_issue.previous_direction
            if trace_enemy_combat_progress:
                enemy_combat_progress_inventory = (
                    enemy_prefix_snapshot.combat_progress_inventory
                )
                if enemy_combat_progress_inventory is None:
                    raise RuntimeError(
                        "combat-progress tracing omitted its capture inventory"
                    )
                enemy_combat_progress_stage = (
                    run_enemy_combat_progress_stage(
                        EnemyCombatProgressStageRequest(
                            trace_sink=trace_sink,
                            inventory=enemy_combat_progress_inventory,
                            route_id=int(state["route_id"]),
                            difficulty_index=int(
                                state["difficulty_index"]
                            ),
                            stage_route_index=int(
                                state["stage_route_index"]
                            ),
                            gameplay_epoch=gameplay_epoch,
                            decision_frame=counter_at_action,
                            frame_before=(
                                enemy_prefix_snapshot.frame_before
                            ),
                            frame_after=(
                                enemy_prefix_snapshot.frame_after
                            ),
                            capture_attempts=(
                                enemy_prefix_snapshot.attempts
                            ),
                            capture_ms=enemy_prefix_capture_ms,
                            previous_emit_ms=(
                                previous_enemy_combat_progress_emit_ms
                            ),
                        )
                    )
                )
                previous_enemy_combat_progress_emit_ms = (
                    enemy_combat_progress_stage.emit_ms
                )
            if runtime_ecl_identity_service is not None:
                runtime_ecl_identity_service.observe_if_due(
                    reader,
                    trace_sink,
                    provenance=RuntimeEclPhysicalProvenance(
                        pid=pid,
                        executable_sha256=str(identity["sha256"]),
                        route_id=int(state["route_id"]),
                        difficulty_index=int(
                            state["difficulty_index"]
                        ),
                        stage_route_index=int(
                            state["stage_route_index"]
                        ),
                        gameplay_epoch=gameplay_epoch,
                        decision_frame=counter_at_action,
                        snapshot_frame=int(
                            state["enemy_manager_frame"]
                        ),
                        gameplay_active=bool(
                            state["gameplay_active"]
                        ),
                    ),
                )
            if auxiliary_vm_batch_service is not None:
                current_spell_id = (
                    int(spell_state["spell_id"])
                    if spell_state["active"]
                    else None
                )
                auxiliary_vm_batch_record = (
                    auxiliary_vm_batch_service.observe_if_due(
                        reader,
                        decision_frame=counter_at_action,
                        manager_frame=int(
                            state["enemy_manager_frame"]
                        ),
                        gameplay_epoch=gameplay_epoch,
                        stage_route_index=int(
                            state["stage_route_index"]
                        ),
                        spell_id=current_spell_id,
                    )
                )
                if auxiliary_vm_batch_record is not None:
                    timing = auxiliary_vm_batch_record.get("timing_ms")
                    if isinstance(timing, dict):
                        timing["previous_emit"] = (
                            previous_auxiliary_vm_batch_emit_ms
                        )
                    previous_auxiliary_vm_batch_emit_ms = (
                        trace_sink.emit(
                            auxiliary_vm_batch_record,
                            flush=(
                                auxiliary_vm_batch_record["status"]
                                != "success"
                            ),
                            measure=True,
                        )
                    )
            local_pipeline_certificate_shadow: (
                dict[str, object] | None
            ) = None
            if (
                args.local_pipeline_root_shadow_every > 0
                and iterations % args.local_pipeline_root_shadow_every == 0
            ):
                if observed_local_pipeline_root is None:
                    local_pipeline_certificate_shadow = {
                        "role": "post_issue_shadow_no_action_authority",
                        "status": "estimator_inconsistent",
                        "computed_after_input": True,
                        "wall_ms": 0.0,
                    }
                else:
                    local_pipeline_certificate_shadow = (
                        _direct_root_certificate_shadow(
                            root=observed_local_pipeline_root,
                            player_x=float(player["x"]),
                            player_y=float(player["y"]),
                            previous_mask=held_desired_mask,
                            delay_frames=delay_estimate.support,
                            action_hold_frames=action_hold_frames,
                            bullets=bullets,
                            lasers=lasers,
                            enemy_bodies=issue_enemy_bodies_for_shadow,
                            snapshot_lag=player_to_hazard_lag,
                            authoritative_certificates=(
                                decision.issue_action_certificates
                            ),
                        )
                    )
                    local_pipeline_certificate_shadow.update(
                        {
                            "source_frame": int(
                                state["enemy_manager_frame"]
                            ),
                            "capture_frame": counter_after_read,
                            "issue_frame": counter_at_action,
                            "post_capture_advance": (
                                action_alignment.post_capture_advance
                            ),
                            "fresh_enemy_prefix_changed": bool(
                                issue_enemy_changes
                            ),
                        }
                    )
            pipeline_prewarm_retarget = (
                _corridor_pipeline_prewarm_retarget(
                    corridor_solution,
                    root=(
                        pipeline_prewarm_query.root
                        if pipeline_prewarm_query is not None
                        else None
                    ),
                    selected_action=_action_name_from_mask(decision.mask),
                    physical_x=projected_player_x,
                    physical_y=projected_player_y,
                    command_issue_offset=(
                        action_alignment.post_capture_advance
                    ),
                    preferred_decision_frame=max(
                        2,
                        min(
                            9,
                            round(
                                (
                                    previous_iteration_ms
                                    if previous_iteration_ms is not None
                                    else 50.0
                                )
                                / (1000.0 / 60.0)
                            )
                            + 1,
                        ),
                    ),
                )
                if args.pipeline_prewarm_shadow
                else None
            )
            current_phase = int(player["phase"])
            current_bombs = resources["bombs"]
            current_power = resources["power"]
            if trace_bullet_births:
                bullet_birth_stage = run_bullet_birth_stage(
                    BulletBirthStageRequest(
                        trace_sink=trace_sink,
                        tracker=bullet_birth_tracker,
                        derived_source_observer=(
                            derived_pattern_source_observer
                        ),
                        trace_derived_sources=(
                            trace_derived_pattern_sources
                        ),
                        bullet_blob=bullet_blob,
                        bullet_frame_before=bullet_frame_before,
                        bullet_frame_after=bullet_frame_after,
                        corridor_future=corridor_future,
                        survival_future=corridor_survival_future,
                        enemy_future=enemy_future,
                        ecl_vm_snapshot=ecl_vm_snapshot,
                        instruction_at=(
                            ecl_instruction_cache.cached_instruction
                        ),
                        intent_horizon_frames=(
                            ECL_BIRTH_LOOKAHEAD_FRAMES
                        ),
                        difficulty_index=int(
                            state["difficulty_index"]
                        ),
                        spell_enemy_pointer=spell_enemy_pointer,
                        observed_enemy_pointer=(
                            spell_enemy_body_guard.body.pointer
                            if spell_enemy_body_guard is not None
                            else None
                        ),
                        observed_enemy_flags=(
                            spell_enemy_body_guard.body.flags
                            if spell_enemy_body_guard is not None
                            else None
                        ),
                        boss_guard_frame_before=boss_guard_frame_before,
                        boss_guard_frame_after=boss_guard_frame_after,
                        ecl_frame_before=ecl_frame_before,
                        ecl_frame_after=ecl_frame_after,
                        ecl_event_frame_offset=ecl_event_frame_offset,
                        ecl_event_frame_uncertainty=(
                            ecl_event_frame_uncertainty
                        ),
                        issue_frame=counter_at_action,
                        snapshot_frame=int(
                            state["enemy_manager_frame"]
                        ),
                        gameplay_epoch=gameplay_epoch,
                        stage_route_index=int(
                            state["stage_route_index"]
                        ),
                        observation_backend=bullet_birth_backend,
                        native_call_mode=(
                            bullet_birth_native_call_mode
                        ),
                        previous_emit_ms=(
                            previous_birth_trace_emit_ms
                        ),
                        nonspell_main_vm_inventory=(
                            enemy_prefix_snapshot
                            .main_ecl_vm_inventory
                        ),
                        enemy_prefix_frame_before=(
                            enemy_prefix_snapshot.frame_before
                        ),
                        enemy_prefix_frame_after=(
                            enemy_prefix_snapshot.frame_after
                        ),
                        enemy_prefix_capture_ms=(
                            enemy_prefix_capture_ms
                        ),
                    ),
                    dependencies=BulletBirthStageDependencies(
                        observe_deferred_fire=(
                            observe_deferred_fire_state
                        ),
                        capture_future_states=(
                            capture_birth_observer_future_states
                        ),
                        observe_derived_sources=(
                            observe_derived_pattern_sources
                        ),
                        analyze_intents=analyze_ecl_birth_intents,
                        build_record=build_bullet_birth_trace_record,
                        requires_immediate_flush=(
                            birth_trace_requires_immediate_flush
                        ),
                        native_tracker_type=(
                            NativeBulletBirthTracker
                        ),
                        wall_clock=time.perf_counter,
                        cpu_clock=time.thread_time,
                    ),
                )
                previous_birth_trace_emit_ms = (
                    bullet_birth_stage.emit_ms
                )
            trace_ms = 0.0
            if (
                trace_bullet_births
                or trace_auxiliary_vm_batches
                or iterations % args.log_every == 0
                or decision.bomb
                or current_phase != previous_phase
                or current_bombs != previous_bombs
                or current_power != previous_power
                or corridor_updated
                or hit_started
                or auto_confirm_event is not None
                or action_deadline_missed
                or local_pipeline_certificate_shadow is not None
            ):
                record = {
                    "kind": "decision",
                    "frame": counter_at_action,
                    "gameplay_epoch": gameplay_epoch,
                    "snapshot_frame": state["enemy_manager_frame"],
                    "snapshot_lag": snapshot_lag,
                    "action_lag": counter_at_action - int(state["enemy_manager_frame"]),
                }
                sensing_trace_fields = build_sensing_trace_fields(
                    SensingTraceInput(
                        resources=resources,
                        stage_route_index=state["stage_route_index"],
                        spell=state["spell"],
                        boss_phase_snapshot=boss_phase_snapshot,
                        boss_phase_error=boss_phase_error,
                        boss_phase_progress=boss_phase_progress,
                        ecl_vm_snapshot=ecl_vm_snapshot,
                        ecl_lookahead=ecl_lookahead,
                        tagged_velocity_toggles=(
                            tagged_velocity_toggles
                        ),
                        bullets=bullets,
                        ecl_event_frame_offset=ecl_event_frame_offset,
                        ecl_event_frame_uncertainty=(
                            ecl_event_frame_uncertainty
                        ),
                        ecl_lookahead_error=ecl_lookahead_error,
                        lasers=lasers,
                        items=items,
                        enemy_bodies=enemy_bodies,
                        dormant_enemy_body_pointers=(
                            dormant_enemy_body_pointers
                        ),
                        bullet_frame_before=bullet_frame_before,
                        bullet_frame_after=bullet_frame_after,
                        enemy_prefix_snapshot=enemy_prefix_snapshot,
                        enemy_prefix_bodies=enemy_prefix_bodies,
                        bullet_capture_span=bullet_capture_span,
                        hazard_snapshot_age=hazard_snapshot_age,
                        player_to_hazard_lag=player_to_hazard_lag,
                        ecl_frame_before=ecl_frame_before,
                        ecl_frame_after=ecl_frame_after,
                        boss_guard_frame_before=boss_guard_frame_before,
                        boss_guard_frame_after=boss_guard_frame_after,
                        enemy_body_snapshot_frame=(
                            enemy_body_snapshot_frame
                        ),
                        query_frame=counter_after_read,
                        issue_enemy_prefix_snapshot=(
                            issue_enemy_prefix_snapshot
                        ),
                        issue_enemy_prefix_bodies=(
                            issue_enemy_prefix_bodies
                        ),
                        issue_dormant_enemy_body_pointers=(
                            issue_dormant_enemy_body_pointers
                        ),
                        issue_enemy_changes=issue_enemy_changes,
                        issue_enemy_read_ms=issue_enemy_read_ms,
                        issue_enemy_recertificate_ms=(
                            issue_enemy_recertificate_ms
                        ),
                        issue=fresh_issue_result,
                        spell_enemy_body_guard=spell_enemy_body_guard,
                        spell_enemy_body_guard_error=(
                            spell_enemy_body_guard_error
                        ),
                    ),
                    serialize_boss_phase_snapshot=(
                        serialize_boss_phase_snapshot
                    ),
                    serialize_enemy_bodies=_serialized_enemy_bodies,
                    enemy_body_contact_enabled=(
                        enemy_body_contact_enabled
                    ),
                    enemy_pointer_in_scanned_pool=(
                        enemy_pointer_in_scanned_pool
                    ),
                    issue_recertification_record=(
                        _issue_recertification_record
                    ),
                )
                record.update(sensing_trace_fields)
                control_trace_fields = build_decision_control_trace_fields(
                    DecisionControlTraceInput(
                        issue=fresh_issue_result,
                        delay_estimate=delay_estimate,
                        control_delay_frames=control_delay_frames,
                        action_hold_frames=action_hold_frames,
                        input_state=state,
                        local_pipeline_root_record=(
                            local_pipeline_root_record
                        ),
                        local_pipeline_certificate_shadow=(
                            local_pipeline_certificate_shadow
                        ),
                        corridor_target=corridor_target,
                        damage_target_x=damage_target_x,
                        damage_target_half_width=(
                            damage_target_half_width
                        ),
                        damageable=damageable,
                        active_item_count=len(items),
                        item_objectives_enabled=ITEM_OBJECTIVES_ENABLED,
                        corridor_context_changed=(
                            corridor_context_changed
                        ),
                        policy_guidance=policy_guidance,
                        player=player,
                        projected_player_x=projected_player_x,
                        projected_player_y=projected_player_y,
                        control_origin_x=control_origin_x,
                        control_origin_y=control_origin_y,
                        phase_at_action=phase_now,
                        predeath_at_action=predeath_now,
                        local_horizon=args.horizon,
                        serialized_enemy_bodies=(
                            _serialized_enemy_bodies(enemy_bodies)
                        ),
                        hit_started=hit_started,
                        hit_count=hit_count,
                        auto_confirm_event=auto_confirm_event,
                    ),
                    local_certificate_timing_record=(
                        _local_certificate_timing_record
                    ),
                )
                record.update(control_trace_fields)
                timing_trace_fields = build_decision_timing_trace_fields(
                    DecisionTimingTraceInput(
                        observe_ms=observe_ms,
                        read_ms=read_ms,
                        enemy_background_ms=enemy_background_ms,
                        enemy_prefix_capture_ms=(
                            enemy_prefix_capture_ms
                        ),
                        enemy_prefix_merge_ms=enemy_prefix_merge_ms,
                        bullet_pool_read_ms=bullet_pool_read_ms,
                        laser_pool_read_ms=laser_pool_read_ms,
                        item_pool_read_ms=item_pool_read_ms,
                        boss_phase_read_ms=boss_phase_read_ms,
                        spell_enemy_guard_read_ms=(
                            spell_enemy_guard_read_ms
                        ),
                        ecl_lookahead_read_ms=ecl_lookahead_read_ms,
                        hazard_read_bookkeeping_ms=(
                            hazard_read_bookkeeping_ms
                        ),
                        enemy_pool_read_ms=enemy_pool_read_ms,
                        enemy_prefix_read_ms=(
                            enemy_prefix_snapshot.read_ms
                        ),
                        issue_enemy_read_ms=issue_enemy_read_ms,
                        decode_ms=decode_ms,
                        bullet_decode_ms=bullet_decode_ms,
                        bullet_event_attach_ms=bullet_event_attach_ms,
                        laser_decode_ms=laser_decode_ms,
                        item_decode_ms=item_decode_ms,
                        corridor_overhead_ms=corridor_overhead_ms,
                        plan_ms=plan_ms,
                        issue_enemy_recertificate_ms=(
                            issue_enemy_recertificate_ms
                        ),
                        issue_path_ms=issue_path_ms,
                        observe_to_issue_ms=observe_to_issue_ms,
                        decision=decision,
                        local_pipeline_certificate_shadow=(
                            local_pipeline_certificate_shadow
                        ),
                        input_ms=input_ms,
                        before_trace_ms=(
                            time.perf_counter() - iteration_started
                        )
                        * 1000.0,
                        previous_trace_ms=previous_trace_ms,
                        previous_iteration_ms=previous_iteration_ms,
                    )
                )
                record.update(timing_trace_fields)
                candidate_record = build_candidate_verifier_trace_record(
                    enabled=candidate_verifier is not None,
                    target=candidate_verifier_target,
                    eligibility=candidate_verifier_eligibility,
                    submit_revision=candidate_verifier_revision,
                    submit_ms=candidate_verifier_submit_ms,
                    lookup_ms=candidate_verifier_lookup_ms,
                    publication_ms=candidate_publication_ms,
                    submit_error=candidate_verifier_submit_error,
                    lookup_error=candidate_verifier_lookup_error,
                    outcome=candidate_verifier_outcome,
                    snapshot=candidate_verifier_snapshot,
                    publications=candidate_shadow_publications,
                    issued_mask=decision.mask,
                    action_name_from_mask=_action_name_from_mask,
                )
                if candidate_record is not None:
                    record["candidate_verifier_shadow"] = candidate_record
                if hit_contact_observation is not None:
                    record["hit_contact_observation"] = (
                        hit_contact_observation
                    )
                corridor_record = build_corridor_trace_record(
                    active_solution=corridor_solution,
                    pending_solution=corridor_pending_solution,
                    issue_frame=counter_at_action,
                    query_frame=counter_after_read,
                    max_age_frames=args.corridor_max_age,
                    viability_query=viability_query,
                    postpublished_survival_query=(
                        postpublished_survival_query
                    ),
                    pipeline_prewarm_query=pipeline_prewarm_query,
                    pipeline_prewarm_retarget=(
                        pipeline_prewarm_retarget
                    ),
                    safety_value_query=safety_value_query,
                    policy_lead=corridor_policy_lead,
                    commitment=corridor_commitment,
                    context_key=corridor_context,
                    observed_input_action=observed_input_action,
                    decision=decision,
                    delay_support=delay_estimate.support,
                    guidance=policy_guidance,
                    pending_command_estimate=(
                        pending_command_estimate
                    ),
                    target=corridor_target,
                    control_origin_x=control_origin_x,
                    control_origin_y=control_origin_y,
                    action_name_from_mask=_action_name_from_mask,
                    minimum_travel_frames=_minimum_travel_frames,
                )
                if corridor_record is not None:
                    record["corridor"] = corridor_record
                optional_hazard_fields = (
                    build_optional_hazard_trace_fields(
                        trace_radius=args.trace_radius,
                        trace_transform_runtime=(
                            args.trace_transform_runtime
                        ),
                        bullets=bullets,
                        lasers=lasers,
                        items=items,
                        projected_player_x=projected_player_x,
                        projected_player_y=projected_player_y,
                        serialize_bullet_trace=serialize_bullet_trace,
                        serialize_laser_trace=serialize_laser_trace,
                    )
                )
                record.update(optional_hazard_fields)
                trace_ms = trace_sink.emit(
                    record,
                    flush=True,
                    measure=True,
                )
            if previous_counter is not None:
                decision_delta = counter_at_action - previous_counter
                if 0 < decision_delta < 120:
                    decision_frame_deltas.append(decision_delta)
            action_lag = counter_at_action - int(state["enemy_manager_frame"])
            delay_estimator.record_computation_lag(action_lag)
            previous_trace_ms = trace_ms
            previous_iteration_ms = (
                time.perf_counter() - iteration_started
            ) * 1000.0
            previous_phase = current_phase
            previous_bombs = current_bombs
            previous_power = current_power
            previous_action_phase = phase_now
            previous_counter = counter_at_action
            if (
                stop_after_frame is not None
                and counter_at_action >= stop_after_frame
            ):
                termination_reason = "hit_limit"
                break
        if (
            input_clock_tracker is not None
            and input_clock_tracker.active_episode_id is not None
        ):
            input_clock_sample = capture_input_clock_shadow(reader)
            input_clock_frame = int(
                input_clock_sample.get(
                    "manager_frame_after",
                    previous_counter
                    if previous_counter is not None
                    else state["enemy_manager_frame"],
                )
            )
            input_clock_stage = int(state["stage_route_index"])
            input_clock_observation = _semantic_clock_observation(
                input_clock_sample,
                fallback_frame=input_clock_frame,
                context=(gameplay_epoch, input_clock_stage),
            )
            input_clock_event = input_clock_tracker.censor(
                input_clock_observation,
                reason=f"run_ended:{termination_reason}",
            )
            record_input_clock_sample(
                sample=input_clock_sample,
                observation=input_clock_observation,
                events=(
                    (input_clock_event,)
                    if input_clock_event is not None
                    else ()
                ),
                frame=input_clock_frame,
                stage_route_index=input_clock_stage,
                frozen_seconds=max(
                    0.0,
                    time.perf_counter() - last_frame_progress,
                ),
                repeat_poll_count=input_clock_repeat_polls,
                triggers=("run_ended",),
            )
        _write_run_summary(
            trace_sink,
            last_frame=previous_counter,
            counter_gaps=gaps,
            hit_count=hit_count,
            termination_reason=termination_reason,
        )
        return 0
    except OSError as exc:
        termination_reason = "process_unreadable"
        trace_sink.runtime_error(exc, last_frame=previous_counter)
        _write_run_summary(
            trace_sink,
            last_frame=previous_counter,
            counter_gaps=gaps,
            hit_count=hit_count,
            termination_reason=termination_reason,
        )
        return 0
    except Exception as exc:
        termination_reason = "agent_error"
        trace_sink.runtime_error(exc, last_frame=previous_counter)
        _write_run_summary(
            trace_sink,
            last_frame=previous_counter,
            counter_gaps=gaps,
            hit_count=hit_count,
            termination_reason=termination_reason,
        )
        raise
    finally:
        try:
            session.release_keys()
        finally:
            try:
                should_pause = False
                try:
                    should_pause = bool(
                        args.pause_on_exit
                        and gameplay_armed
                        and api.foreground_pid() == pid
                        and reader.u32(0x0164D0B4) & 0x04
                    )
                except OSError:
                    pass
                if should_pause:
                    send_scan_key(api, scan_code=0x01, pressed=True)
                    try:
                        time.sleep(0.06)
                    finally:
                        send_scan_key(api, scan_code=0x01, pressed=False)
                retire_pipeline_solutions(
                    (corridor_solution, corridor_pending_solution)
                )
                service_resources.close(
                    corridor_future=corridor_future,
                    survival_future=corridor_survival_future,
                    enemy_future=enemy_future,
                )
            finally:
                session.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--pid", type=int)
    parser.add_argument("--duration", type=float, default=120.0)
    parser.add_argument("--poll-ms", type=float, default=0.2)
    parser.add_argument("--log-every", type=int, default=30)
    parser.add_argument("--horizon", type=int, default=PLANNER_HORIZON)
    parser.add_argument(
        "--threat-horizon",
        type=int,
        default=PLANNER_THREAT_HORIZON,
        help=(
            "cheap terminal-action hazard rollout; heuristic only, never a "
            "viability certificate"
        ),
    )
    parser.add_argument("--beam-width", type=int, default=PLANNER_BEAM_WIDTH)
    parser.add_argument(
        "--control-delay-frames",
        type=int,
        default=CONTROL_DELAY_FRAMES,
        help="initial rolling-p90 previous-input prefix estimate",
    )
    parser.add_argument(
        "--difficulty",
        type=int,
        choices=(0, 1, 2, 3, 4),
        default=3,
        help=(
            "required runtime difficulty index: 0 Easy, 1 Normal, 2 Hard, "
            "3 Lunatic, 4 Extra"
        ),
    )
    parser.add_argument(
        "--corridor-every",
        type=int,
        default=CORRIDOR_REPLAN_FRAMES,
        help="game frames between asynchronous global corridor submissions",
    )
    parser.add_argument(
        "--corridor-lookahead",
        type=int,
        default=CORRIDOR_LOOKAHEAD_FRAMES,
        help="frames ahead on the corridor used as the local waypoint",
    )
    parser.add_argument(
        "--corridor-max-age",
        type=int,
        default=CORRIDOR_MAX_AGE_FRAMES,
        help="discard a corridor result after this many game frames",
    )
    parser.add_argument(
        "--corridor-native-workers",
        type=int,
        choices=(1, 2, 3, 4),
        default=4,
        help=(
            "native viability worker cap on the asynchronous corridor "
            "thread; four preserves authoritative plan throughput, while "
            "smaller values are explicit contention ablations"
        ),
    )
    parser.add_argument(
        "--corridor-background-low-priority",
        action="store_true",
        help=(
            "run only the Python corridor parent below normal priority; "
            "default-off G5 contention experiment"
        ),
    )
    parser.add_argument(
        "--safety-value-horizon",
        type=int,
        default=0,
        help=(
            "optional compact max-min fallback horizon in game frames; "
            "zero disables the research policy"
        ),
    )
    parser.add_argument(
        "--postpublished-survival-shadow",
        action="store_true",
        help=(
            "compute dense survival labels only after Boolean publication; "
            "labels use an isolated executor and have no action authority"
        ),
    )
    parser.add_argument(
        "--pipeline-prewarm-shadow",
        action="store_true",
        help=(
            "start exact-root seeds when clearance is ready and record "
            "lookup-only current-version hits; never changes live actions"
        ),
    )
    parser.add_argument(
        "--candidate-verifier-shadow",
        action="store_true",
        help=(
            "verify a bounded attainable policy portfolio beside local "
            "planning and consume only exact-root shadow hits; never changes "
            "live actions"
        ),
    )
    parser.add_argument(
        "--input-clock-boundary-shadow",
        action="store_true",
        help=(
            "record the native FRScreen enemy-clock gate, active input, and "
            "player motion as read-only telemetry; never changes input, "
            "epochs, estimator state, or policy publication"
        ),
    )
    parser.add_argument(
        "--input-clock-shadow-sample-ms",
        type=float,
        default=1.0,
        help=(
            "minimum repeated-frame telemetry sampling cadence; this controls "
            "trace cost only and is never an episode classifier"
        ),
    )
    parser.add_argument(
        "--local-pipeline-root-shadow-every",
        type=int,
        default=0,
        metavar="DECISIONS",
        help=(
            "after input issue, sample an explicit observed/estimated-root "
            "certificate every N decisions; zero disables it, results never "
            "change the issued action, and the measured work may perturb the "
            "next controller cadence"
        ),
    )
    parser.add_argument(
        "--local-hazard-backend",
        choices=("numpy", "native"),
        default="native",
        help=(
            "local hazard-query implementation; the parity-gated native C "
            "ABI is the default and numpy is the explicit reference rollback"
        ),
    )
    parser.add_argument(
        "--local-beam-reducer",
        choices=("python", "native"),
        default="native",
        help=(
            "quantized beam deduplication and pruning implementation; the "
            "parity-gated native reducer is the default and python is the "
            "explicit reference rollback"
        ),
    )
    parser.add_argument(
        "--bullet-decode-backend",
        choices=("python", "native"),
        default="native",
        help=(
            "planning bullet-pool decoder; the parity-gated native packed "
            "snapshot is the default above its measured sparse crossover, "
            "python objects are the explicit reference rollback, and "
            "transform-runtime tracing always uses the diagnostic Python "
            "decoder"
        ),
    )
    parser.add_argument(
        "--viability-audit-dir",
        type=Path,
        help=(
            "write ignored neutral policy-input capsules for offline "
            "differential audit; diagnostic I/O may perturb timing"
        ),
    )
    parser.add_argument(
        "--local-only",
        action="store_true",
        help="disable the corridor layer for controlled A/B runs",
    )
    parser.add_argument(
        "--wait-gameplay",
        action="store_true",
        help="warm up at the menu and arm when idle route-2 gameplay begins",
    )
    parser.add_argument(
        "--wait-timeout",
        type=float,
        default=60.0,
        help="seconds allowed for --wait-gameplay",
    )
    parser.add_argument(
        "--expected-stage",
        type=int,
        choices=range(9),
        help="required stage-route index after menu confirmation",
    )
    parser.add_argument(
        "--terminal-stage",
        type=int,
        choices=range(9),
        help="treat this stage's first stable scene unload as trial completion",
    )
    parser.add_argument(
        "--stop-after-hits",
        type=int,
        default=1,
        help="stop after this many hits; zero keeps running",
    )
    parser.add_argument(
        "--post-hit-frames",
        type=int,
        default=30,
        help="trace frames retained after the hit limit is reached",
    )
    parser.add_argument(
        "--leave-running",
        action="store_false",
        dest="pause_on_exit",
        help="do not press Escape when a gameplay trial exits",
    )
    parser.add_argument(
        "--stop-file",
        type=Path,
        help="exit safely when this file appears",
    )
    parser.set_defaults(pause_on_exit=True)
    parser.add_argument(
        "--trace-radius",
        type=float,
        default=0.0,
        help="include native projectile/item geometry within this player radius",
    )
    parser.add_argument(
        "--trace-transform-runtime",
        action="store_true",
        help="include transform-relevant bullets from the full native pool",
    )
    parser.add_argument(
        "--trace-bullet-births",
        action="store_true",
        help=(
            "record default-off hostile-bullet activation evidence and "
            "fail-closed active-spell main-VM fire intent; diagnostic trace "
            "only, never changes live actions"
        ),
    )
    parser.add_argument(
        "--bullet-birth-backend",
        choices=("python", "native"),
        default="python",
        help=(
            "select the explicit retrospective birth observer backend; "
            "used only with --trace-bullet-births"
        ),
    )
    parser.add_argument(
        "--trace-derived-pattern-sources",
        action="store_true",
        help=(
            "add the failed-gate ready-parent transform shadow to an "
            "explicit bullet-birth trace; diagnostic only"
        ),
    )
    parser.add_argument(
        "--trace-nonspell-main-vms",
        action="store_true",
        help=(
            "decode first-64 ordinary-enemy main VMs from the existing "
            "prefix capture into an explicit bullet-birth trace; "
            "diagnostic only, no instruction reads"
        ),
    )
    parser.add_argument(
        "--trace-enemy-combat-progress",
        action="store_true",
        help=(
            "decode first-64 ordinary-enemy raw HP/damage fields from the "
            "existing prefix capture; trace only, never changes live actions"
        ),
    )
    parser.add_argument(
        "--trace-auxiliary-vm-batches",
        action="store_true",
        help=(
            "capture a bounded post-issue first-64 auxiliary ECL VM batch "
            "at an explicit changed-manager-frame cadence; trace only"
        ),
    )
    parser.add_argument(
        "--auxiliary-vm-batch-every",
        type=int,
        default=16,
        metavar="MANAGER_FRAMES",
        help=(
            "changed enemy-manager frames between post-issue auxiliary-VM "
            "batch attempts"
        ),
    )
    parser.add_argument(
        "--auxiliary-vm-batch-spell-id",
        type=int,
        help=(
            "optional exact spell-id filter for auxiliary-VM batch tracing"
        ),
    )
    parser.add_argument(
        "--auxiliary-vm-native-call-mode",
        choices=NATIVE_CALL_MODES,
        default=NATIVE_CALL_MODE_GIL_HELD,
        help=(
            "select whether the trace-only native auxiliary-VM batch call "
            "releases or holds the Python GIL"
        ),
    )
    parser.add_argument(
        "--runtime-ecl-static-image",
        type=Path,
        help=(
            "one decoded static ECL image for a default-off post-issue "
            "one-shot runtime byte-identity observation"
        ),
    )
    parser.add_argument(
        "--runtime-ecl-static-sha256",
        help=(
            "required immutable SHA-256 for --runtime-ecl-static-image"
        ),
    )
    parser.add_argument(
        "--bullet-birth-native-call-mode",
        choices=NATIVE_CALL_MODES,
        default=NATIVE_CALL_MODE_GIL_RELEASED,
        help=(
            "select whether the trace-only native birth call releases or "
            "holds the Python GIL"
        ),
    )
    bomb_group = parser.add_mutually_exclusive_group()
    bomb_group.add_argument(
        "--normal-bomb",
        action="store_true",
        help="permit a pre-hit Bomb when every next-frame move overlaps",
    )
    bomb_group.add_argument(
        "--no-bomb",
        action="store_true",
        help="forbid normal Bomb and deathbomb input",
    )
    parser.add_argument(
        "--auto-confirm-every",
        type=int,
        default=0,
        help="pulse a fresh Z edge this often in sustained empty scenes; zero disables",
    )
    parser.add_argument(
        "--auto-confirm-idle-frames",
        type=int,
        default=20,
        help="empty-scene frames required before automatic Z pulsing",
    )
    parser.add_argument(
        "--stage-transition-timeout",
        type=float,
        default=STAGE_TRANSITION_TIMEOUT_SECONDS,
        help="seconds allowed for a non-final stage resource transition",
    )
    parser.add_argument(
        "--terminal-inactive-grace",
        type=float,
        default=TERMINAL_INACTIVE_GRACE_SECONDS,
        help="stable inactive seconds required after the final stage",
    )
    parser.add_argument("--armed", action="store_true")
    return parser


if __name__ == "__main__":
    try:
        raise SystemExit(run(build_parser().parse_args()))
    except Exception as exc:
        print(f"error: {exc}")
        raise SystemExit(1)
