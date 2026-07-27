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
    solve_corridor as _solve_corridor,
    solve_postpublished_survival as _solve_postpublished_survival,
    stage_corridor_solution as _stage_corridor_solution,
    close_retired_pipeline_prewarms as _close_retired_pipeline_prewarms,
)
from th08_corridor_adapter import TH08_CORRIDOR_CONFIG
from th08_ecl_runtime import (
    EclLookaheadResult,
    EclInstructionCache,
    EclVmSnapshot,
    TaggedVelocityToggle,
    analyze_tagged_velocity_toggles,
    read_main_ecl_vm_snapshot,
)
from th08_laser_runtime import (
    Laser,
    PackedLaserFrame as _PackedLaserFrame,
    build_laser_collision_frames,  # noqa: F401 - compatibility export
    build_packed_laser_collision_frames as _build_packed_laser_collision_frames,
    pack_laser_frame as _pack_laser_frame,
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
    PackedBulletSnapshot,
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
from th08_live.iteration import (
    CapturedIteration,
    FreshIssueResult,
    PublishedGuidance,
    ServiceUpdate,
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
    ActionIssueAlignment,
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
INPUT_CLOCK_SHADOW_WALL_CUT_SECONDS = 0.05

SHOT = 0x01
BOMB = 0x02
FOCUS = 0x04
UP = 0x10
DOWN = 0x20
LEFT = 0x40
RIGHT = 0x80

PLAYFIELD_LEFT = 8.0
PLAYFIELD_RIGHT = 376.0
PLAYFIELD_TOP = 16.0
PLAYFIELD_BOTTOM = 432.0
PLAYER_RADIUS = 2.0
FOCUSED_CARDINAL_SPEED = 2.299999952316284
FOCUSED_DIAGONAL_SPEED = 1.6263456344604492
UNFOCUSED_CARDINAL_SPEED = 4.0
UNFOCUSED_DIAGONAL_SPEED = 2.8284270763397217
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
COLLECTION_HALF_WIDTH = 24.0
ITEM_SAFETY_CLEARANCE = 8.0
# Item value is a bounded tie-breaker inside the viable action set. Raw item
# values range into the hundreds and previously overwhelmed the entire
# conservative-position cost, so a dense post-phase drop could pull the
# player through an incompletely observed boss-contact transition.
ITEM_UTILITY_WEIGHT = 0.25
ITEM_UTILITY_SATURATION = 32.0
ITEM_APPROACH_POTENTIAL_WEIGHT = 0.02
# Current acceptance work is survival-only.  Items may still be collected
# passively, but they cannot affect beam pruning, action choice, or reported
# predicted collections.  Resource-aware pickup can later be re-enabled only
# as a tie-breaker between independently certified survival-equivalent paths.
ITEM_OBJECTIVES_ENABLED = False
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


def _action(
    name: str,
    direction: int,
    unit_x: float,
    unit_y: float,
    *,
    focused: bool,
) -> PlannerAction:
    diagonal = unit_x != 0.0 and unit_y != 0.0
    if focused:
        speed = FOCUSED_DIAGONAL_SPEED if diagonal else FOCUSED_CARDINAL_SPEED
    else:
        speed = UNFOCUSED_DIAGONAL_SPEED if diagonal else UNFOCUSED_CARDINAL_SPEED
    return PlannerAction(name, direction, unit_x * speed, unit_y * speed, focused)


_DIRECTION_ACTIONS = (
    ("left", LEFT, -1.0, 0.0),
    ("right", RIGHT, 1.0, 0.0),
    ("up", UP, 0.0, -1.0),
    ("down", DOWN, 0.0, 1.0),
    ("up_left", UP | LEFT, -1.0, -1.0),
    ("up_right", UP | RIGHT, 1.0, -1.0),
    ("down_left", DOWN | LEFT, -1.0, 1.0),
    ("down_right", DOWN | RIGHT, 1.0, 1.0),
)

_PLANNER_ACTIONS = (
    PlannerAction("stay", 0, 0.0, 0.0, True),
    *(
        _action(name, direction, unit_x, unit_y, focused=True)
        for name, direction, unit_x, unit_y in _DIRECTION_ACTIONS
    ),
    *(
        _action(f"{name}_fast", direction, unit_x, unit_y, focused=False)
        for name, direction, unit_x, unit_y in _DIRECTION_ACTIONS
    ),
)
_LOCAL_PIPELINE_STATE_ACTIONS = (
    *_PLANNER_ACTIONS,
    PlannerAction("stay_unfocused", 0, 0.0, 0.0, False),
)


def _action_name_from_mask(input_mask: int) -> str:
    direction = input_mask & (UP | DOWN | LEFT | RIGHT)
    if direction & (UP | LEFT) == UP | LEFT:
        name = "up_left"
    elif direction & (DOWN | LEFT) == DOWN | LEFT:
        name = "down_left"
    elif direction & (UP | RIGHT) == UP | RIGHT:
        name = "up_right"
    elif direction & (DOWN | RIGHT) == DOWN | RIGHT:
        name = "down_right"
    elif direction & DOWN:
        name = "down"
    elif direction & UP:
        name = "up"
    elif direction & LEFT:
        name = "left"
    elif direction & RIGHT:
        name = "right"
    else:
        return "stay"
    return name if input_mask & FOCUS else f"{name}_fast"


def _local_pipeline_action_from_mask(input_mask: int) -> str:
    """Injective movement/focus projection for local actuator state."""

    direction = input_mask & (UP | DOWN | LEFT | RIGHT)
    if direction == 0 and not input_mask & FOCUS:
        return "stay_unfocused"
    return _action_name_from_mask(input_mask)


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


def _aabb_clearance(
    px: float, py: float, bullet_x: float, bullet_y: float, bullet: Bullet
) -> float:
    dx = abs(px - bullet_x) - (PLAYER_RADIUS + bullet.half_width)
    dy = abs(py - bullet_y) - (PLAYER_RADIUS + bullet.half_height)
    if dx <= 0.0 and dy <= 0.0:
        return max(dx, dy)
    return math.hypot(max(dx, 0.0), max(dy, 0.0))


def _segment_clearance(px: float, py: float, laser: Laser) -> float:
    cosine = math.cos(laser.angle)
    sine = math.sin(laser.angle)
    start_x = laser.origin_x + cosine * laser.tail
    start_y = laser.origin_y + sine * laser.tail
    end_x = laser.origin_x + cosine * laser.head
    end_y = laser.origin_y + sine * laser.head
    segment_x = end_x - start_x
    segment_y = end_y - start_y
    length_sq = segment_x * segment_x + segment_y * segment_y
    if length_sq <= 1e-9:
        distance = math.hypot(px - start_x, py - start_y)
    else:
        projection = max(
            0.0,
            min(
                1.0,
                ((px - start_x) * segment_x + (py - start_y) * segment_y)
                / length_sq,
            ),
        )
        nearest_x = start_x + projection * segment_x
        nearest_y = start_y + projection * segment_y
        distance = math.hypot(px - nearest_x, py - nearest_y)
    return distance - laser.half_width - PLAYER_RADIUS


def _project_item(item: Item, step: int) -> tuple[float, float, float]:
    """Short-horizon item estimate plus confidence in that estimate.

    State 2 stores interpolation endpoints in the velocity-area fields, so a
    live record without its timer/start/target tuple is deliberately treated
    as low confidence. States 3/5 are usable only as a coarse acceleration
    estimate until their state transition is observed on a later frame.
    """

    scale = 0.8
    if item.motion_state == 2:
        return item.x, item.y, 0.15
    acceleration = 0.0
    if item.motion_state == 0:
        acceleration = 0.03 * scale
    elif item.motion_state in (3, 5):
        acceleration = 0.05
    x = item.x + item.vx * scale * step
    y = item.y + item.vy * scale * step + 0.5 * acceleration * step * (step - 1)
    confidence = 1.0 if item.motion_state in (0, 1) else 0.4
    return x, y, confidence


def _item_value(item: Item, *, power: float, bombs: float) -> float:
    if item.item_type == 5:
        return 320.0
    if item.item_type == 3:
        return 240.0 if bombs < 8.0 else 0.0
    if item.item_type == 4:
        return 300.0 if power < 128.0 else 5.0
    if item.item_type == 2:
        return 90.0 if power < 128.0 else 3.0
    if item.item_type == 0:
        return 24.0 if power < 128.0 else 2.0
    if item.item_type == 7:
        return 10.0
    if item.item_type == 1:
        return 5.0 if item.full_value else 2.0
    if item.item_type in (6, 8):
        return 1.0
    return 0.0


def _select_items(
    items: tuple[Item, ...], *, power: float, bombs: float, limit: int = 12
) -> tuple[tuple[Item, float], ...]:
    ranked = [
        (item, _item_value(item, power=power, bombs=bombs))
        for item in items
        if item.motion_state in (0, 1, 2, 3, 5)
    ]
    ranked = [entry for entry in ranked if entry[1] > 0.0]
    ranked.sort(key=lambda entry: (-entry[1], entry[0].y, entry[0].slot))
    return tuple(ranked[:limit])


def _build_bullet_frames(
    bullets: tuple[Bullet, ...] | PackedBulletSnapshot,
    *,
    horizon: int,
    snapshot_lag: int,
) -> tuple[tuple[np.ndarray, ...], ...]:
    frames: list[tuple[np.ndarray, ...]] = []
    if isinstance(bullets, PackedBulletSnapshot):
        base_x = bullets.x
        base_y = bullets.y
        velocity_x = bullets.velocity_x
        velocity_y = bullets.velocity_y
        half_width = bullets.half_width
        half_height = bullets.half_height
        transformed = np.not_equal(bullets.transform_flags, 0)
    else:
        base_x = np.fromiter(
            (bullet.x for bullet in bullets),
            dtype=np.float32,
        )
        base_y = np.fromiter(
            (bullet.y for bullet in bullets),
            dtype=np.float32,
        )
        velocity_x = np.fromiter(
            (bullet.vx for bullet in bullets),
            dtype=np.float32,
        )
        velocity_y = np.fromiter(
            (bullet.vy for bullet in bullets),
            dtype=np.float32,
        )
        half_width = np.fromiter(
            (bullet.half_width for bullet in bullets),
            dtype=np.float32,
        )
        half_height = np.fromiter(
            (bullet.half_height for bullet in bullets),
            dtype=np.float32,
        )
        trajectory_uncertainty_x = np.fromiter(
            (
                bullet.trajectory_uncertainty_x
                for bullet in bullets
            ),
            dtype=np.float32,
        )
        trajectory_uncertainty_y = np.fromiter(
            (
                bullet.trajectory_uncertainty_y
                for bullet in bullets
            ),
            dtype=np.float32,
        )
        half_width = half_width + trajectory_uncertainty_x
        half_height = half_height + trajectory_uncertainty_y
        transformed = np.fromiter(
            (bool(bullet.transform_flags) for bullet in bullets),
            dtype=np.bool_,
        )
    event_indices: list[int] = []
    event_frames: list[int] = []
    event_delta_x: list[float] = []
    event_delta_y: list[float] = []
    if not isinstance(bullets, PackedBulletSnapshot):
        for bullet_index, bullet in enumerate(bullets):
            previous_x = bullet.vx
            previous_y = bullet.vy
            for change in bullet.velocity_changes:
                event_indices.append(bullet_index)
                event_frames.append(change.frame)
                event_delta_x.append(change.velocity_x - previous_x)
                event_delta_y.append(change.velocity_y - previous_y)
                previous_x = change.velocity_x
                previous_y = change.velocity_y
    packed_event_indices = np.asarray(event_indices, dtype=np.intp)
    packed_event_frames = np.asarray(event_frames, dtype=np.int32)
    packed_event_delta_x = np.asarray(event_delta_x, dtype=np.float32)
    packed_event_delta_y = np.asarray(event_delta_y, dtype=np.float32)
    for step in range(1, horizon + 1):
        elapsed = snapshot_lag + step
        projected_x = base_x + velocity_x * elapsed
        projected_y = base_y + velocity_y * elapsed
        if packed_event_indices.size:
            affected_updates = elapsed - packed_event_frames + 1
            active = affected_updates > 0
            if np.any(active):
                np.add.at(
                    projected_x,
                    packed_event_indices[active],
                    packed_event_delta_x[active]
                    * affected_updates[active],
                )
                np.add.at(
                    projected_y,
                    packed_event_indices[active],
                    packed_event_delta_y[active]
                    * affected_updates[active],
                )
        frames.append(
            (
                projected_x,
                projected_y,
                half_width,
                half_height,
                transformed,
            )
        )
    return tuple(frames)


def _numpy_hazards_for_positions(
    positions_x: np.ndarray,
    positions_y: np.ndarray,
    *,
    step: int,
    bullet_frame: tuple[np.ndarray, ...],
    lasers: tuple[Laser, ...] | _PackedLaserFrame,
    enemy_bodies: tuple[EnemyBody, ...],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    count = positions_x.size
    risk = np.zeros(count, dtype=np.float64)
    collisions = np.zeros(count, dtype=np.int32)
    minimum = np.full(count, np.inf, dtype=np.float64)
    time_weight = 1.0 / (1.0 + 0.08 * (step - 1))
    bullet_x, bullet_y, half_width, half_height, transformed = bullet_frame
    if bullet_x.size:
        margin = 84.0
        relevant = (
            (bullet_x >= float(positions_x.min()) - margin)
            & (bullet_x <= float(positions_x.max()) + margin)
            & (bullet_y >= float(positions_y.min()) - margin)
            & (bullet_y <= float(positions_y.max()) + margin)
        )
        bullet_x = bullet_x[relevant]
        bullet_y = bullet_y[relevant]
        half_width = half_width[relevant]
        half_height = half_height[relevant]
        transformed = transformed[relevant]
        if bullet_x.size:
            position_relevant = (
                (bullet_x[None, :] >= positions_x[:, None] - margin)
                & (bullet_x[None, :] <= positions_x[:, None] + margin)
                & (bullet_y[None, :] >= positions_y[:, None] - margin)
                & (bullet_y[None, :] <= positions_y[:, None] + margin)
            )
            dx = np.abs(positions_x[:, None] - bullet_x[None, :]) - (
                PLAYER_RADIUS + half_width[None, :]
            )
            dy = np.abs(positions_y[:, None] - bullet_y[None, :]) - (
                PLAYER_RADIUS + half_height[None, :]
            )
            overlap = (dx <= 0.0) & (dy <= 0.0)
            clearance = np.where(
                overlap,
                np.maximum(dx, dy),
                np.hypot(np.maximum(dx, 0.0), np.maximum(dy, 0.0)),
            )
            collisions += (
                (clearance <= 0.0) & position_relevant
            ).sum(axis=1, dtype=np.int32)
            uncertainty = 0.2 * math.sqrt(step) + transformed.astype(np.float32) * min(
                10.0, 3.0 + 0.35 * step
            )
            robust_clearance = np.where(
                position_relevant,
                clearance - uncertainty[None, :],
                np.inf,
            )
            minimum = np.minimum(minimum, robust_clearance.min(axis=1))
            danger = np.maximum(44.0 - robust_clearance, 0.0)
            risk += np.square(danger).sum(axis=1) * time_weight
    packed_lasers = (
        lasers
        if isinstance(lasers, _PackedLaserFrame)
        else _pack_laser_frame(lasers)
    )
    if packed_lasers.start_x.size:
        start_x = packed_lasers.start_x
        start_y = packed_lasers.start_y
        segment_x = packed_lasers.segment_x
        segment_y = packed_lasers.segment_y
        uncertainty = (
            packed_lasers.base_uncertainty
            + np.minimum(
                6.0,
                packed_lasers.uncertainty_per_frame * step,
            )
        )
        occupied_radius = packed_lasers.collision_radius + uncertainty
        margin = 56.0
        relevant = (
            (
                np.maximum(start_x, start_x + segment_x)
                + occupied_radius
                >= float(positions_x.min()) - margin
            )
            & (
                np.minimum(start_x, start_x + segment_x)
                - occupied_radius
                <= float(positions_x.max()) + margin
            )
            & (
                np.maximum(start_y, start_y + segment_y)
                + occupied_radius
                >= float(positions_y.min()) - margin
            )
            & (
                np.minimum(start_y, start_y + segment_y)
                - occupied_radius
                <= float(positions_y.max()) + margin
            )
        )
        if np.any(relevant):
            start_x = start_x[relevant]
            start_y = start_y[relevant]
            segment_x = segment_x[relevant]
            segment_y = segment_y[relevant]
            collision_radius = packed_lasers.collision_radius[relevant]
            uncertainty = uncertainty[relevant]
            occupied_radius = collision_radius + uncertainty
            position_relevant = (
                (
                    np.maximum(start_x, start_x + segment_x)[None, :]
                    + occupied_radius[None, :]
                    >= positions_x[:, None] - margin
                )
                & (
                    np.minimum(start_x, start_x + segment_x)[None, :]
                    - occupied_radius[None, :]
                    <= positions_x[:, None] + margin
                )
                & (
                    np.maximum(start_y, start_y + segment_y)[None, :]
                    + occupied_radius[None, :]
                    >= positions_y[:, None] - margin
                )
                & (
                    np.minimum(start_y, start_y + segment_y)[None, :]
                    - occupied_radius[None, :]
                    <= positions_y[:, None] + margin
                )
            )
            length_sq = segment_x * segment_x + segment_y * segment_y
            flat_x = positions_x[:, None]
            flat_y = positions_y[:, None]
            numerator = (
                (flat_x - start_x[None, :]) * segment_x[None, :]
                + (flat_y - start_y[None, :]) * segment_y[None, :]
            )
            projection = np.divide(
                numerator,
                length_sq[None, :],
                out=np.zeros_like(numerator),
                where=length_sq[None, :] > 1e-9,
            )
            projection = np.clip(projection, 0.0, 1.0)
            distance = np.hypot(
                flat_x - (start_x + projection * segment_x),
                flat_y - (start_y + projection * segment_y),
            )
            clearance = distance - collision_radius[None, :]
            collisions += (
                (clearance <= 0.0) & position_relevant
            ).sum(
                axis=1,
                dtype=np.int32,
            )
            robust_clearance = np.where(
                position_relevant,
                clearance - uncertainty[None, :],
                np.inf,
            )
            minimum = np.minimum(
                minimum,
                robust_clearance.min(axis=1),
            )
            danger = np.maximum(56.0 - robust_clearance, 0.0)
            risk += (
                2.0 * np.square(danger).sum(axis=1) * time_weight
            )
    if enemy_bodies:
        body_x = np.fromiter(
            (body.x + body.vx * step for body in enemy_bodies),
            dtype=np.float32,
        )
        body_y = np.fromiter(
            (body.y + body.vy * step for body in enemy_bodies),
            dtype=np.float32,
        )
        half_width = np.fromiter(
            (
                body.half_width + body.uncertainty
                for body in enemy_bodies
            ),
            dtype=np.float32,
        )
        half_height = np.fromiter(
            (
                body.half_height + body.uncertainty
                for body in enemy_bodies
            ),
            dtype=np.float32,
        )
        dx = np.abs(positions_x[:, None] - body_x[None, :]) - (
            PLAYER_RADIUS + half_width[None, :]
        )
        dy = np.abs(positions_y[:, None] - body_y[None, :]) - (
            PLAYER_RADIUS + half_height[None, :]
        )
        overlap = (dx <= 0.0) & (dy <= 0.0)
        clearance = np.where(
            overlap,
            np.maximum(dx, dy),
            np.hypot(np.maximum(dx, 0.0), np.maximum(dy, 0.0)),
        )
        collisions += (clearance <= 0.0).sum(axis=1, dtype=np.int32)
        robust_clearance = clearance - min(12.0, 0.5 * step)
        minimum = np.minimum(minimum, robust_clearance.min(axis=1))
        danger = np.maximum(64.0 - robust_clearance, 0.0)
        risk += 2.0 * np.square(danger).sum(axis=1) * time_weight
    return risk, collisions, minimum


def _native_hazards_for_positions(
    positions_x: np.ndarray,
    positions_y: np.ndarray,
    *,
    step: int,
    bullet_frame: tuple[np.ndarray, ...],
    lasers: tuple[Laser, ...] | _PackedLaserFrame,
    enemy_bodies: tuple[EnemyBody, ...],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Parity-gated native implementation of `_hazards_for_positions`."""

    bullet_x, bullet_y, half_width, half_height, transformed = bullet_frame
    packed_lasers = (
        lasers
        if isinstance(lasers, _PackedLaserFrame)
        else _pack_laser_frame(lasers)
    )
    (
        laser_start_x,
        laser_start_y,
        laser_segment_x,
        laser_segment_y,
        laser_collision_radius,
        laser_base_uncertainty,
        laser_uncertainty_per_frame,
    ) = packed_lasers.fields_for_native()
    body_x = np.fromiter(
        (body.x + body.vx * step for body in enemy_bodies),
        dtype=np.float32,
        count=len(enemy_bodies),
    )
    body_y = np.fromiter(
        (body.y + body.vy * step for body in enemy_bodies),
        dtype=np.float32,
        count=len(enemy_bodies),
    )
    body_half_width = np.fromiter(
        (
            body.half_width + body.uncertainty
            for body in enemy_bodies
        ),
        dtype=np.float32,
        count=len(enemy_bodies),
    )
    body_half_height = np.fromiter(
        (
            body.half_height + body.uncertainty
            for body in enemy_bodies
        ),
        dtype=np.float32,
        count=len(enemy_bodies),
    )
    result = native_backend.query_local_hazards(
        positions_x=positions_x,
        positions_y=positions_y,
        step=step,
        player_radius=PLAYER_RADIUS,
        bullet_x=bullet_x,
        bullet_y=bullet_y,
        bullet_half_width=half_width,
        bullet_half_height=half_height,
        bullet_transformed=transformed,
        laser_start_x=laser_start_x,
        laser_start_y=laser_start_y,
        laser_segment_x=laser_segment_x,
        laser_segment_y=laser_segment_y,
        laser_collision_radius=laser_collision_radius,
        laser_base_uncertainty=laser_base_uncertainty,
        laser_uncertainty_per_frame=laser_uncertainty_per_frame,
        body_x=body_x,
        body_y=body_y,
        body_half_width=body_half_width,
        body_half_height=body_half_height,
    )
    if result is None:
        raise RuntimeError("native local hazard kernel is unavailable")
    return result


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
    """Evaluate motion already committed before a new decision can take effect."""

    if frames <= 0:
        return 0.0, 0, math.inf
    bullet_frames = _build_bullet_frames(
        bullets,
        horizon=frames,
        snapshot_lag=-max(0, snapshot_lag),
    )
    if laser_frames is None:
        laser_frames = _build_packed_laser_collision_frames(
            lasers,
            horizon=frames,
        )
    if len(laser_frames) < frames:
        raise ValueError("laser timeline does not cover the control prefix")
    risk = 0.0
    collisions = 0
    minimum = math.inf
    for step in range(1, frames + 1):
        x, y = _project_player_for_read_lag(
            player_x,
            player_y,
            input_mask,
            step,
        )
        hazard_risk, hazard_collisions, hazard_clearance = _hazards_for_positions(
            np.asarray([x], dtype=np.float32),
            np.asarray([y], dtype=np.float32),
            step=step,
            bullet_frame=bullet_frames[step - 1],
            lasers=laser_frames[step - 1],
            enemy_bodies=enemy_bodies,
        )
        risk += _boundary_risk(x, y) + float(hazard_risk[0])
        collisions += int(hazard_collisions[0])
        minimum = min(minimum, float(hazard_clearance[0]))
    return risk, collisions, minimum


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
    """Legacy last-desired-as-active certificate retained for differential."""

    if not actions or not delay_frames:
        return {}
    maximum_step = action_hold_frames + max(delay_frames)
    bullet_frames = _build_bullet_frames(
        bullets,
        horizon=maximum_step,
        snapshot_lag=-max(0, snapshot_lag),
    )
    if laser_frames is None:
        laser_frames = _build_packed_laser_collision_frames(
            lasers,
            horizon=maximum_step,
        )
    if len(laser_frames) < maximum_step:
        raise ValueError("laser timeline does not cover robust certificates")
    action_count = len(actions)
    risk_by_delay: dict[int, np.ndarray] = {}
    collisions_by_delay: dict[int, np.ndarray] = {}
    clearance_by_delay: dict[int, np.ndarray] = {}
    for delay in delay_frames:
        risks = np.zeros(action_count, dtype=np.float64)
        collisions = np.zeros(action_count, dtype=np.int32)
        minimum = np.full(action_count, np.inf, dtype=np.float64)
        prefix_x = player_x
        prefix_y = player_y
        for step in range(1, delay + 1):
            prefix_x, prefix_y = _project_player_for_read_lag(
                player_x,
                player_y,
                previous_mask,
                step,
            )
            hazard_risk, hazard_collisions, hazard_clearance = (
                _hazards_for_positions(
                    np.asarray([prefix_x], dtype=np.float32),
                    np.asarray([prefix_y], dtype=np.float32),
                    step=step,
                    bullet_frame=bullet_frames[step - 1],
                    lasers=laser_frames[step - 1],
                    enemy_bodies=enemy_bodies,
                )
            )
            risks += _boundary_risk(prefix_x, prefix_y) + float(hazard_risk[0])
            collisions += int(hazard_collisions[0])
            minimum = np.minimum(minimum, float(hazard_clearance[0]))
        for step in range(delay + 1, maximum_step + 1):
            action_step = step - delay
            positions_x = np.fromiter(
                (
                    min(
                        PLAYFIELD_RIGHT,
                        max(PLAYFIELD_LEFT, prefix_x + action.dx * action_step),
                    )
                    for action in actions
                ),
                dtype=np.float32,
            )
            positions_y = np.fromiter(
                (
                    min(
                        PLAYFIELD_BOTTOM,
                        max(PLAYFIELD_TOP, prefix_y + action.dy * action_step),
                    )
                    for action in actions
                ),
                dtype=np.float32,
            )
            hazard_risk, hazard_collisions, hazard_clearance = (
                _hazards_for_positions(
                    positions_x,
                    positions_y,
                    step=step,
                    bullet_frame=bullet_frames[step - 1],
                    lasers=laser_frames[step - 1],
                    enemy_bodies=enemy_bodies,
                )
            )
            boundary = np.fromiter(
                (
                    _boundary_risk(float(x), float(y))
                    for x, y in zip(positions_x, positions_y)
                ),
                dtype=np.float64,
                count=action_count,
            )
            risks += boundary + hazard_risk
            collisions += hazard_collisions
            minimum = np.minimum(minimum, hazard_clearance)
        risk_by_delay[delay] = risks
        collisions_by_delay[delay] = collisions
        clearance_by_delay[delay] = minimum

    certificates: dict[str, RobustActionCertificate] = {}
    tail_count = max(1, math.ceil(0.5 * len(delay_frames)))
    for action_index, action in enumerate(actions):
        worst_delay = max(
            delay_frames,
            key=lambda delay: (
                int(collisions_by_delay[delay][action_index]),
                -float(clearance_by_delay[delay][action_index]),
                float(risk_by_delay[delay][action_index]),
            ),
        )
        tail_risks = sorted(
            (
                float(risk_by_delay[delay][action_index])
                for delay in delay_frames
            ),
            reverse=True,
        )[:tail_count]
        minimum = min(
            float(clearance_by_delay[delay][action_index])
            for delay in delay_frames
        )
        certificates[action.name] = RobustActionCertificate(
            action=action.name,
            delay_frames=delay_frames,
            worst_collisions=max(
                int(collisions_by_delay[delay][action_index])
                for delay in delay_frames
            ),
            min_clearance=9999.0 if math.isinf(minimum) else minimum,
            cvar_risk=sum(tail_risks) / len(tail_risks),
            worst_delay=worst_delay,
        )
    return certificates


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
    """Certify all candidate actions over one explicit finite pipeline lease.

    ``pipeline_root`` carries native active input separately from the
    controller's held desired input. Selecting the held desired action is a
    no-write branch and therefore does not sample a fresh pickup delay. When
    no root is supplied, active and held both come from ``previous_mask``.
    """

    total_started_ns = time.perf_counter_ns()
    explicit_root = pipeline_root is not None
    if not actions or not delay_frames:
        return {}
    if (
        tuple(sorted(set(delay_frames))) != delay_frames
        or delay_frames[0] < 0
    ):
        raise ValueError(
            "certificate delay support must be sorted, unique, and "
            "nonnegative"
        )
    if action_hold_frames <= 0:
        raise ValueError("certificate action hold must be positive")
    if pipeline_root is None:
        active_action = _local_pipeline_action_from_mask(previous_mask)
        pipeline_root = LocalPipelineRoot(
            active_action=active_action,
            held_desired_action=active_action,
        )

    validation_finished_ns = time.perf_counter_ns()
    projection_started_ns = validation_finished_ns
    maximum_step = action_hold_frames + max(delay_frames)
    bullet_frames = _build_bullet_frames(
        bullets,
        horizon=maximum_step,
        snapshot_lag=-max(0, snapshot_lag),
    )
    if laser_frames is None:
        laser_frames = _build_packed_laser_collision_frames(
            lasers,
            horizon=maximum_step,
        )
    if len(laser_frames) < maximum_step:
        raise ValueError("laser timeline does not cover robust certificates")
    projection_finished_ns = time.perf_counter_ns()

    branch_setup_started_ns = projection_finished_ns
    action_by_name = {
        action.name: action for action in _LOCAL_PIPELINE_STATE_ACTIONS
    }
    if len(action_by_name) != len(_LOCAL_PIPELINE_STATE_ACTIONS):
        raise RuntimeError("local pipeline action names are not unique")
    required_names = {
        pipeline_root.active_action,
        pipeline_root.held_desired_action,
        *(action.name for action in actions),
    }
    if pipeline_root.pending_action is not None:
        required_names.add(pipeline_root.pending_action)
    unknown_names = required_names - set(action_by_name)
    if unknown_names:
        raise ValueError(
            f"pipeline root contains unknown actions: {sorted(unknown_names)}"
        )

    branch_action_indices: list[int] = []
    branch_selected_dx: list[float] = []
    branch_selected_dy: list[float] = []
    branch_older_remaining: list[int] = []
    branch_new_delay: list[int] = []
    branch_write_required: list[bool] = []
    branch_metadata: list[tuple[int | None, int | None]] = []
    pending_support: tuple[int | None, ...] = (
        tuple(pipeline_root.remaining_delay_support)
        if pipeline_root.pending_action is not None
        else (None,)
    )
    no_activation = maximum_step + max(delay_frames) + 1
    for action_index, action in enumerate(actions):
        write_required = (
            action.name != pipeline_root.held_desired_action
        )
        new_delay_support: tuple[int | None, ...] = (
            tuple(delay_frames) if write_required else (None,)
        )
        for older_remaining in pending_support:
            for new_delay in new_delay_support:
                branch_action_indices.append(action_index)
                branch_selected_dx.append(action.dx)
                branch_selected_dy.append(action.dy)
                branch_older_remaining.append(
                    no_activation
                    if older_remaining is None
                    else older_remaining
                )
                branch_new_delay.append(
                    no_activation if new_delay is None else new_delay
                )
                branch_write_required.append(write_required)
                branch_metadata.append((new_delay, older_remaining))

    branch_count = len(branch_action_indices)
    selected_dx = np.asarray(branch_selected_dx, dtype=np.float32)
    selected_dy = np.asarray(branch_selected_dy, dtype=np.float32)
    older_remaining_values = np.asarray(
        branch_older_remaining,
        dtype=np.int32,
    )
    new_delay_values = np.asarray(branch_new_delay, dtype=np.int32)
    write_required_values = np.asarray(
        branch_write_required,
        dtype=np.bool_,
    )
    action_indices = np.asarray(branch_action_indices, dtype=np.int32)
    active = action_by_name[pipeline_root.active_action]
    pending = (
        action_by_name[pipeline_root.pending_action]
        if pipeline_root.pending_action is not None
        else active
    )
    has_pending = pipeline_root.pending_action is not None

    branch_setup_finished_ns = time.perf_counter_ns()
    geometry_started_ns = branch_setup_finished_ns
    positions_x = np.full(branch_count, player_x, dtype=np.float32)
    positions_y = np.full(branch_count, player_y, dtype=np.float32)
    risks = np.zeros(branch_count, dtype=np.float64)
    collisions = np.zeros(branch_count, dtype=np.int32)
    minimum = np.full(branch_count, np.inf, dtype=np.float64)
    for step in range(1, maximum_step + 1):
        selected_active = write_required_values & (
            step > new_delay_values
        )
        pending_active = (
            (~selected_active)
            & has_pending
            & (step > older_remaining_values)
        )
        motion_x = np.where(
            selected_active,
            selected_dx,
            np.where(pending_active, pending.dx, active.dx),
        )
        motion_y = np.where(
            selected_active,
            selected_dy,
            np.where(pending_active, pending.dy, active.dy),
        )
        positions_x = np.clip(
            positions_x + motion_x,
            PLAYFIELD_LEFT,
            PLAYFIELD_RIGHT,
        ).astype(np.float32, copy=False)
        positions_y = np.clip(
            positions_y + motion_y,
            PLAYFIELD_TOP,
            PLAYFIELD_BOTTOM,
        ).astype(np.float32, copy=False)
        hazard_risk, hazard_collisions, hazard_clearance = (
            _hazards_for_positions(
                positions_x,
                positions_y,
                step=step,
                bullet_frame=bullet_frames[step - 1],
                lasers=laser_frames[step - 1],
                enemy_bodies=enemy_bodies,
            )
        )
        boundary = _boundary_risk_for_positions(
            positions_x,
            positions_y,
        )
        risks += boundary + hazard_risk
        collisions += hazard_collisions
        minimum = np.minimum(minimum, hazard_clearance)

    geometry_finished_ns = time.perf_counter_ns()
    reduction_started_ns = geometry_finished_ns
    certificates: dict[str, RobustActionCertificate] = {}
    for action_index, action in enumerate(actions):
        indices = np.flatnonzero(action_indices == action_index)
        if not len(indices):
            raise RuntimeError("candidate action has no pipeline branch")
        worst_index = max(
            (int(index) for index in indices),
            key=lambda index: (
                int(collisions[index]),
                -float(minimum[index]),
                float(risks[index]),
            ),
        )
        tail_count = max(1, math.ceil(0.5 * len(indices)))
        tail_risks = sorted(
            (float(risks[index]) for index in indices),
            reverse=True,
        )[:tail_count]
        action_minimum = min(
            float(minimum[index]) for index in indices
        )
        worst_new_delay, worst_pending_remaining = branch_metadata[
            worst_index
        ]
        certificates[action.name] = RobustActionCertificate(
            action=action.name,
            delay_frames=delay_frames,
            worst_collisions=max(
                int(collisions[index]) for index in indices
            ),
            min_clearance=(
                9999.0
                if math.isinf(action_minimum)
                else action_minimum
            ),
            cvar_risk=sum(tail_risks) / len(tail_risks),
            worst_delay=worst_new_delay,
            write_required=(
                action.name != pipeline_root.held_desired_action
            ),
            pipeline_branch_count=len(indices),
            worst_pending_remaining=worst_pending_remaining,
        )
    finished_ns = time.perf_counter_ns()
    if timing_accumulator is not None:
        nanoseconds_to_ms = 1.0 / 1_000_000.0
        timing_accumulator.calls += 1
        timing_accumulator.explicit_root_calls += int(explicit_root)
        timing_accumulator.maximum_branch_count = max(
            timing_accumulator.maximum_branch_count,
            branch_count,
        )
        timing_accumulator.validation_ms += (
            validation_finished_ns - total_started_ns
        ) * nanoseconds_to_ms
        timing_accumulator.hazard_projection_ms += (
            projection_finished_ns - projection_started_ns
        ) * nanoseconds_to_ms
        timing_accumulator.branch_setup_ms += (
            branch_setup_finished_ns - branch_setup_started_ns
        ) * nanoseconds_to_ms
        timing_accumulator.geometry_kernel_ms += (
            geometry_finished_ns - geometry_started_ns
        ) * nanoseconds_to_ms
        timing_accumulator.reduction_ms += (
            finished_ns - reduction_started_ns
        ) * nanoseconds_to_ms
        timing_accumulator.certificate_total_ms += (
            finished_ns - total_started_ns
        ) * nanoseconds_to_ms
    return certificates


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


def _item_potential(
    x: float,
    y: float,
    *,
    step: int,
    selected_items: tuple[tuple[Item, float], ...],
    collected_mask: int,
) -> float:
    potential = 0.0
    for index, (item, value) in enumerate(selected_items):
        if collected_mask & (1 << index):
            continue
        item_x, item_y, confidence = _project_item(item, step)
        distance = math.hypot(x - item_x, y - item_y)
        if distance < 144.0:
            potential += value * confidence * (144.0 - distance) / 144.0
    return potential


def _node_key(
    node: SearchNode,
    *,
    step: int,
    selected_items: tuple[tuple[Item, float], ...],
    target_x: float | None = None,
    target_y: float | None = None,
    target_deadline: int | None = None,
) -> tuple[int, float, float, float, float]:
    usable_item_utility = (
        node.item_utility if node.min_clearance >= ITEM_SAFETY_CLEARANCE else 0.0
    )
    potential = (
        _item_potential(
            node.x,
            node.y,
            step=step,
            selected_items=selected_items,
            collected_mask=node.collected_mask,
        )
        if node.min_clearance >= ITEM_SAFETY_CLEARANCE
        else 0.0
    )
    raw_utility = (
        usable_item_utility
        + ITEM_APPROACH_POTENTIAL_WEIGHT * potential
    )
    utility = ITEM_UTILITY_SATURATION * (
        1.0 - math.exp(-raw_utility / ITEM_UTILITY_SATURATION)
    )
    safety_deficit = max(ITEM_SAFETY_CLEARANCE - node.min_clearance, 0.0)
    gate_deficit = 0.0
    if (
        target_x is not None
        and target_y is not None
        and target_deadline is not None
    ):
        required_frames = _minimum_travel_frames(
            node.x,
            node.y,
            target_x,
            target_y,
        )
        gate_deficit = max(
            required_frames - max(target_deadline - step, 0),
            0.0,
        )
    return (
        node.collisions,
        gate_deficit,
        safety_deficit,
        node.risk - ITEM_UTILITY_WEIGHT * utility,
        -node.min_clearance,
    )


def _minimum_travel_frames(
    x: float,
    y: float,
    target_x: float,
    target_y: float,
    *,
    tolerance: float = 6.0,
) -> float:
    horizontal = max(abs(x - target_x) - tolerance, 0.0)
    vertical = max(abs(y - target_y) - tolerance, 0.0)
    diagonal = min(horizontal, vertical)
    straight = max(horizontal, vertical) - diagonal
    return (
        diagonal / UNFOCUSED_DIAGONAL_SPEED
        + straight / UNFOCUSED_CARDINAL_SPEED
    )


def _boundary_risk(x: float, y: float) -> float:
    horizontal = min(x - PLAYFIELD_LEFT, PLAYFIELD_RIGHT - x)
    vertical = min(y - PLAYFIELD_TOP, PLAYFIELD_BOTTOM - y)
    risk = 0.0
    if horizontal < 12.0:
        risk += 2.0 * (12.0 - horizontal) ** 2
    if vertical < 12.0:
        risk += 3.0 * (12.0 - vertical) ** 2
    if horizontal < 20.0 and vertical < 20.0:
        risk += (20.0 - horizontal) * (20.0 - vertical)
    return risk


def _boundary_risk_for_positions(
    positions_x: np.ndarray,
    positions_y: np.ndarray,
) -> np.ndarray:
    """Vectorized form of ``_boundary_risk`` for packed branch batches."""

    horizontal = np.minimum(
        positions_x - PLAYFIELD_LEFT,
        PLAYFIELD_RIGHT - positions_x,
    ).astype(np.float64, copy=False)
    vertical = np.minimum(
        positions_y - PLAYFIELD_TOP,
        PLAYFIELD_BOTTOM - positions_y,
    ).astype(np.float64, copy=False)
    risk = np.zeros(positions_x.size, dtype=np.float64)
    horizontal_near = horizontal < 12.0
    vertical_near = vertical < 12.0
    corner_near = (horizontal < 20.0) & (vertical < 20.0)
    risk[horizontal_near] += (
        2.0 * np.square(12.0 - horizontal[horizontal_near])
    )
    risk[vertical_near] += (
        3.0 * np.square(12.0 - vertical[vertical_near])
    )
    risk[corner_near] += (
        (20.0 - horizontal[corner_near])
        * (20.0 - vertical[corner_near])
    )
    return risk


def _boundary_control_reserve_deficit(
    x: float,
    y: float,
    *,
    reserve_distance: float,
) -> float:
    """Measure lost axis-wise control range near clamped boundaries."""

    if reserve_distance <= 0.0:
        return 0.0
    return sum(
        (
            max(reserve_distance - (x - PLAYFIELD_LEFT), 0.0),
            max(reserve_distance - (PLAYFIELD_RIGHT - x), 0.0),
            max(reserve_distance - (y - PLAYFIELD_TOP), 0.0),
            max(reserve_distance - (PLAYFIELD_BOTTOM - y), 0.0),
        )
    )


def _directions_opposed(left: int, right: int) -> bool:
    horizontal = bool(left & LEFT and right & RIGHT) or bool(
        left & RIGHT and right & LEFT
    )
    vertical = bool(left & UP and right & DOWN) or bool(
        left & DOWN and right & UP
    )
    return horizontal or vertical


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
    """Extend terminal actions cheaply; this is a warning, not a certificate."""

    if not nodes or end_step <= start_step:
        return {node: (0, math.inf) for node in nodes}
    positions_x = np.asarray([node.x for node in nodes], dtype=np.float32)
    positions_y = np.asarray([node.y for node in nodes], dtype=np.float32)
    velocity_x = np.asarray(
        [node.last_action.dx for node in nodes],
        dtype=np.float32,
    )
    velocity_y = np.asarray(
        [node.last_action.dy for node in nodes],
        dtype=np.float32,
    )
    collisions = np.zeros(len(nodes), dtype=np.int32)
    minimum = np.full(len(nodes), np.inf, dtype=np.float64)
    for step in range(start_step + 1, end_step + 1):
        positions_x = np.clip(
            positions_x + velocity_x,
            PLAYFIELD_LEFT,
            PLAYFIELD_RIGHT,
        )
        positions_y = np.clip(
            positions_y + velocity_y,
            PLAYFIELD_TOP,
            PLAYFIELD_BOTTOM,
        )
        _, step_collisions, step_clearance = _hazards_for_positions(
            positions_x,
            positions_y,
            step=control_delay_frames + step,
            bullet_frame=bullet_frames[step - 1],
            lasers=laser_frames[step - 1],
            enemy_bodies=enemy_bodies,
        )
        collisions += step_collisions
        minimum = np.minimum(minimum, step_clearance)
    return {
        node: (int(collisions[index]), float(minimum[index]))
        for index, node in enumerate(nodes)
    }


def _terminal_threat_degeneracy(
    *,
    player_x: float,
    player_y: float,
    action_hold_frames: int,
    allowed_first_actions: tuple[str, ...] | None,
    viability_position_error: float,
) -> str | None:
    """Detect stale-policy control collapse near a clamped boundary."""

    if allowed_first_actions is None:
        return None
    allowed = set(allowed_first_actions)
    successors: set[tuple[float, float]] = set()
    action_count = 0
    clamped = False
    unclamped_motion = False
    for action in _PLANNER_ACTIONS:
        if action.name not in allowed:
            continue
        action_count += 1
        raw_x = player_x + action.dx * action_hold_frames
        raw_y = player_y + action.dy * action_hold_frames
        successor_x = min(PLAYFIELD_RIGHT, max(PLAYFIELD_LEFT, raw_x))
        successor_y = min(PLAYFIELD_BOTTOM, max(PLAYFIELD_TOP, raw_y))
        action_clamped = successor_x != raw_x or successor_y != raw_y
        clamped |= action_clamped
        unclamped_motion |= (
            not action_clamped
            and (abs(action.dx) > 1e-6 or abs(action.dy) > 1e-6)
        )
        successors.add((round(successor_x, 3), round(successor_y, 3)))
    off_grid_singleton = (
        action_count == 1 and viability_position_error > 1e-3
    )
    if off_grid_singleton:
        return "off_grid_singleton"
    if clamped and 0 < len(successors) < action_count:
        return (
            "partial_clamped_alias"
            if unclamped_motion
            else "complete_clamped_alias"
        )
    return None


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


def _project_player_for_read_lag(
    x: float, y: float, input_mask: int, frames: int
) -> tuple[float, float]:
    direction = input_mask & (UP | DOWN | LEFT | RIGHT)
    if not direction or frames <= 0:
        return x, y
    horizontal = (-1 if direction & LEFT else 0) + (1 if direction & RIGHT else 0)
    vertical = (-1 if direction & UP else 0) + (1 if direction & DOWN else 0)
    if horizontal == 0 and vertical == 0:
        return x, y
    focused = bool(input_mask & FOCUS)
    diagonal = horizontal != 0 and vertical != 0
    if focused:
        speed = FOCUSED_DIAGONAL_SPEED if diagonal else FOCUSED_CARDINAL_SPEED
    else:
        speed = UNFOCUSED_DIAGONAL_SPEED if diagonal else UNFOCUSED_CARDINAL_SPEED
    return (
        min(PLAYFIELD_RIGHT, max(PLAYFIELD_LEFT, x + horizontal * speed * frames)),
        min(PLAYFIELD_BOTTOM, max(PLAYFIELD_TOP, y + vertical * speed * frames)),
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
    _configure_local_hazard_backend(args.local_hazard_backend)
    _configure_local_beam_reducer(args.local_beam_reducer)
    _configure_local_bullet_decoder(args.bullet_decode_backend)
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
                    "corridor_background_low_priority": False,
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
                reader
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
                ecl_lookahead_read_started = time.perf_counter()
                ecl_frame_before = reader.u32(0x0164D30C)
                try:
                    ecl_vm_snapshot = read_main_ecl_vm_snapshot(
                        reader,
                        spell_enemy_pointer,
                    )
                    ecl_lookahead = analyze_tagged_velocity_toggles(
                        ecl_vm_snapshot,
                        instruction_at=lambda address: (
                            ecl_instruction_cache.instruction(
                                reader.read,
                                address,
                            )
                        ),
                        horizon_frames=ECL_CALLBACK_LOOKAHEAD_FRAMES,
                        active_difficulty_mask=(
                            1 << int(state["difficulty_index"])
                        ),
                    )
                    tagged_velocity_toggles = ecl_lookahead.events
                except (OSError, RuntimeError, ValueError, struct.error) as error:
                    ecl_vm_snapshot = None
                    ecl_lookahead = None
                    tagged_velocity_toggles = ()
                    ecl_lookahead_error = (
                        f"{type(error).__name__}: {error}"
                    )
                ecl_frame_after = reader.u32(0x0164D30C)
                ecl_lookahead_read_ms = (
                    time.perf_counter() - ecl_lookahead_read_started
                ) * 1000.0
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
            issue_enemy_read_started = issue_path_started
            issue_enemy_prefix_snapshot = (
                capture_enemy_pool_prefix_contiguous(reader)
            )
            issue_enemy_read_ms = (
                time.perf_counter() - issue_enemy_read_started
            ) * 1000.0
            (
                issue_enemy_prefix_bodies,
                issue_dormant_enemy_body_pointers,
            ) = enemy_body_memory.merge_snapshot(
                issue_enemy_prefix_snapshot,
                frame=int(state["enemy_manager_frame"]),
            )
            alignment_frame = int(state["enemy_manager_frame"])
            issue_enemy_changes = issue_enemy_snapshot_changes(
                enemy_prefix_snapshot,
                issue_enemy_prefix_snapshot,
                EnemyPoolSnapshot(
                    alignment_frame,
                    alignment_frame,
                    enemy_prefix_bodies,
                    enemy_prefix_snapshot.read_ms,
                    enemy_prefix_snapshot.attempts,
                ),
                EnemyPoolSnapshot(
                    alignment_frame,
                    alignment_frame,
                    issue_enemy_prefix_bodies,
                    issue_enemy_prefix_snapshot.read_ms,
                    issue_enemy_prefix_snapshot.attempts,
                ),
            )
            issue_enemy_recertificate_ms = 0.0
            issue_enemy_bodies_for_shadow = enemy_bodies
            if issue_enemy_changes:
                issue_enemy_bodies = merge_enemy_pool_prefix(
                    enemy_bodies,
                    issue_enemy_prefix_bodies,
                )
                issue_enemy_bodies_for_shadow = issue_enemy_bodies
                issue_recertificate_started = time.perf_counter()
                issued_decision = commit_local_proposal_for_fresh_hazards(
                    local_proposal,
                    player_x=float(player["x"]),
                    player_y=float(player["y"]),
                    previous_mask=previous_mask,
                    delay_frames=delay_estimate.support,
                    action_hold_frames=action_hold_frames,
                    bullets=bullets,
                    lasers=lasers,
                    enemy_bodies=issue_enemy_bodies,
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
                decision = issued_decision.decision
                issue_enemy_recertificate_ms = (
                    time.perf_counter() - issue_recertificate_started
                ) * 1000.0
                plan_ms += issue_enemy_recertificate_ms
            post_issue_guard_action = decision.action
            post_issue_guard_mask = decision.mask
            phase_now = reader.u8(0x017D5EF8)
            predeath_now = reader.i32(0x017D5EF8 + 0xE2A68)
            counter_at_action = reader.u32(0x0164D30C)
            action_alignment = ActionIssueAlignment(
                source_frame=int(state["enemy_manager_frame"]),
                capture_frame=counter_after_read,
                issue_frame=counter_at_action,
                delay_support=delay_estimate.support,
            )
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
            if action_deadline_missed:
                # Do not inject a newly selected direction after its robust
                # delay certificate has expired. Holding the last actuator
                # command avoids adding a second unmodeled transition; the
                # next iteration replans from a fresh native snapshot.
                decision = replace(
                    decision,
                    mask=previous_mask,
                    action=(
                        f"{_action_name_from_mask(previous_mask)}"
                        "+deadline_hold"
                    ),
                    bomb=False,
                    planned_focus=bool(previous_mask & FOCUS),
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
            can_deathbomb = (
                not args.no_bomb
                and phase_now == 2
                and predeath_now > 0
                and resources["bombs"] > 0
                and counter_at_action - last_bomb_counter > 30
            )
            if can_deathbomb:
                decision = replace(
                    decision,
                    mask=decision.mask | BOMB,
                    action=f"{decision.action}+deathbomb",
                    bomb=True,
                )
            if decision.bomb:
                last_bomb_counter = counter_at_action
            auto_confirm_mask, auto_confirm_event = auto_confirm.apply(
                frame=counter_at_action,
                eligible=_auto_confirm_eligible(
                    player_phase=phase_now,
                    bomb_active=bool(player["bomb_active"]),
                    active_bullets=len(bullets),
                    active_lasers=len(lasers),
                ),
                mask=decision.mask,
            )
            if auto_confirm_event is not None:
                decision = replace(decision, mask=auto_confirm_mask)
            if args.no_bomb and decision.mask & BOMB:
                raise RuntimeError("no-bomb policy produced a Bomb input")
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
            input_dispatch = issue_controller.dispatch(
                previous_mask,
                decision.mask,
            )
            transitions = input_dispatch.transitions
            input_ms = input_dispatch.input_ms
            issue_path_ms = (
                time.perf_counter() - issue_path_started
            ) * 1000.0
            observe_to_issue_ms = (
                time.perf_counter() - iteration_started
            ) * 1000.0
            fresh_issue_result = FreshIssueResult(
                capture=captured_iteration,
                proposal=local_proposal,
                decision=decision,
                alignment=action_alignment,
                dispatch=input_dispatch,
                issue_frame=counter_at_action,
                pre_issue_action=pre_issue_action,
                pre_issue_mask=pre_issue_mask,
                post_guard_action=post_issue_guard_action,
                post_guard_mask=post_issue_guard_mask,
                planned_action=planned_action,
                planned_mask=planned_mask,
                fresh_enemy_changed=bool(issue_enemy_changes),
                deadline_missed=action_deadline_missed,
                recertification_ms=issue_enemy_recertificate_ms,
                issue_path_ms=issue_path_ms,
                observe_to_issue_ms=observe_to_issue_ms,
            )
            if transitions:
                delay_estimator.issued(
                    snapshot_frame=fresh_issue_result.capture.source_frame,
                    issue_frame=fresh_issue_result.issue_frame,
                    expected_mask=fresh_issue_result.decision.mask,
                    support_high=delay_estimate.support[-1],
                    support=delay_estimate.support,
                )
            previous_mask = fresh_issue_result.decision.mask
            previous_direction = fresh_issue_result.decision.mask & (
                UP | DOWN | LEFT | RIGHT
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
            trace_ms = 0.0
            if (
                iterations % args.log_every == 0
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
                ecl_tagged_bullets = (
                    tuple(
                        bullet
                        for bullet in bullets
                        if (
                            ecl_vm_snapshot is not None
                            and (
                                (
                                    bullet.original_transform_flags
                                    or (
                                        bullet.transform_runtime.original_flags
                                        if bullet.transform_runtime is not None
                                        else 0
                                    )
                                )
                                & ecl_vm_snapshot.tag_mask
                            )
                        )
                    )
                    if ecl_vm_snapshot is not None
                    else ()
                )
                record = {
                    "kind": "decision",
                    "frame": counter_at_action,
                    "gameplay_epoch": gameplay_epoch,
                    "snapshot_frame": state["enemy_manager_frame"],
                    "snapshot_lag": snapshot_lag,
                    "action_lag": counter_at_action - int(state["enemy_manager_frame"]),
                    "read_ms": read_ms,
                    "plan_ms": plan_ms,
                    "timing_ms": {
                        "observe": observe_ms,
                        "read_pools": read_ms,
                        "read_enemy_background": enemy_background_ms,
                        "read_enemy_prefix_capture": (
                            enemy_prefix_capture_ms
                        ),
                        "read_enemy_prefix_merge": enemy_prefix_merge_ms,
                        "read_bullet_pool": bullet_pool_read_ms,
                        "read_laser_pool": laser_pool_read_ms,
                        "read_item_pool": item_pool_read_ms,
                        "read_boss_phase": boss_phase_read_ms,
                        "read_spell_enemy_guard": (
                            spell_enemy_guard_read_ms
                        ),
                        "read_ecl_lookahead": ecl_lookahead_read_ms,
                        "read_hazard_bookkeeping": (
                            hazard_read_bookkeeping_ms
                        ),
                        "read_enemy_pool": enemy_pool_read_ms,
                        "read_enemy_prefix": (
                            enemy_prefix_snapshot.read_ms
                        ),
                        "read_enemy_issue_prefix": issue_enemy_read_ms,
                        "decode_pools": decode_ms,
                        "decode_bullets": bullet_decode_ms,
                        "attach_bullet_events": bullet_event_attach_ms,
                        "decode_lasers": laser_decode_ms,
                        "decode_items": item_decode_ms,
                        "corridor_bookkeeping": corridor_overhead_ms,
                        "local_plan": plan_ms,
                        "local_plan_initial": (
                            plan_ms - issue_enemy_recertificate_ms
                        ),
                        "issue_enemy_recertificate": (
                            issue_enemy_recertificate_ms
                        ),
                        "issue_path_to_input": issue_path_ms,
                        "observe_to_input": observe_to_issue_ms,
                        "local_shared_laser_projection": (
                            decision.local_certificate_timing
                            .shared_laser_projection_ms
                        ),
                        "local_certificate_total": (
                            decision.local_certificate_timing
                            .certificate_total_ms
                        ),
                        "local_certificate_geometry": (
                            decision.local_certificate_timing
                            .geometry_kernel_ms
                        ),
                        "issue_certificate_total": (
                            decision.issue_certificate_timing
                            .certificate_total_ms
                        ),
                        "post_issue_root_shadow": (
                            float(
                                local_pipeline_certificate_shadow.get(
                                    "wall_ms",
                                    0.0,
                                )
                            )
                            if local_pipeline_certificate_shadow is not None
                            else 0.0
                        ),
                        "input": input_ms,
                        "before_trace": (
                            time.perf_counter() - iteration_started
                        )
                        * 1000.0,
                        "previous_trace": previous_trace_ms,
                        "previous_iteration": previous_iteration_ms,
                    },
                    "resources": resources,
                    "stage_route_index": state["stage_route_index"],
                    "spell": state["spell"],
                    "boss_phase": (
                        {
                            **(
                                serialize_boss_phase_snapshot(
                                    boss_phase_snapshot
                                )
                                or {}
                            ),
                            "error": boss_phase_error,
                        }
                        if (
                            boss_phase_snapshot is not None
                            or boss_phase_error is not None
                        )
                        else None
                    ),
                    "boss_phase_progress": (
                        {
                            "status": boss_phase_progress.status,
                            "frame_delta": boss_phase_progress.frame_delta,
                            "health_delta": boss_phase_progress.health_delta,
                            "damage_per_frame": (
                                boss_phase_progress.damage_per_frame
                            ),
                            "damage_per_second_60hz": (
                                boss_phase_progress.damage_per_frame * 60.0
                                if (
                                    boss_phase_progress.damage_per_frame
                                    is not None
                                )
                                else None
                            ),
                            "damageable": (
                                boss_phase_progress.state.damageable
                            ),
                        }
                        if boss_phase_progress is not None
                        else None
                    ),
                    "bullet_velocity_lookahead": (
                        {
                            "instruction_pointer": (
                                ecl_vm_snapshot.instruction_pointer
                            ),
                            "timer_fraction": ecl_vm_snapshot.timer_fraction,
                            "timer_elapsed": ecl_vm_snapshot.timer_elapsed,
                            "time_scale": ecl_vm_snapshot.time_scale,
                            "tag_mask": ecl_vm_snapshot.tag_mask,
                            "instructions_scanned": (
                                ecl_lookahead.instructions_scanned
                                if ecl_lookahead is not None
                                else 0
                            ),
                            "stop_reason": (
                                ecl_lookahead.stop_reason
                                if ecl_lookahead is not None
                                else None
                            ),
                            "horizon_covered": (
                                ecl_lookahead.horizon_covered
                                if ecl_lookahead is not None
                                else False
                            ),
                            "events": [
                                [
                                    event.frame,
                                    event.callback_index,
                                    event.tag_mask,
                                    event.alternate_velocity_x,
                                    event.alternate_velocity_y,
                                ]
                                for event in tagged_velocity_toggles
                            ],
                            "attached_bullets": sum(
                                bool(bullet.velocity_changes)
                                for bullet in bullets
                            ),
                            "tagged_bullets": len(ecl_tagged_bullets),
                            "stopped_tagged_bullets": sum(
                                bullet.callback_phase_state == 0
                                and bullet.callback_aux_state == 1
                                for bullet in ecl_tagged_bullets
                            ),
                            "event_frame_offset": (
                                ecl_event_frame_offset
                            ),
                            "event_frame_uncertainty": (
                                ecl_event_frame_uncertainty
                            ),
                            "error": ecl_lookahead_error,
                        }
                        if ecl_vm_snapshot is not None
                        else (
                            {"error": ecl_lookahead_error}
                            if ecl_lookahead_error is not None
                            else None
                        )
                    ),
                    "active_bullets": len(bullets),
                    "active_lasers": len(lasers),
                    "active_items": len(items),
                    "active_enemy_bodies": len(enemy_bodies),
                    "enemy_body_contact_enabled_count": sum(
                        body.pointer not in dormant_enemy_body_pointers
                        and enemy_body_contact_enabled(body)
                        for body in enemy_bodies
                    ),
                    "enemy_body_anticipatory_count": sum(
                        body.pointer not in dormant_enemy_body_pointers
                        and not enemy_body_contact_enabled(body)
                        for body in enemy_bodies
                    ),
                    "enemy_body_dormant_count": sum(
                        body.pointer in dormant_enemy_body_pointers
                        for body in enemy_bodies
                    ),
                    "hazard_alignment": {
                        "bullet_frame_before": bullet_frame_before,
                        "bullet_frame_after": bullet_frame_after,
                        "enemy_prefix_frame_before": (
                            enemy_prefix_snapshot.frame_before
                        ),
                        "enemy_prefix_frame_after": (
                            enemy_prefix_snapshot.frame_after
                        ),
                        "enemy_prefix_body_count": len(
                            enemy_prefix_bodies
                        ),
                        "enemy_prefix_observed_body_count": len(
                            enemy_prefix_snapshot.bodies
                        ),
                        "enemy_prefix_contact_enabled_count": sum(
                            body.pointer not in dormant_enemy_body_pointers
                            and enemy_body_contact_enabled(body)
                            for body in enemy_prefix_bodies
                        ),
                        "enemy_prefix_anticipatory_count": sum(
                            body.pointer not in dormant_enemy_body_pointers
                            and not enemy_body_contact_enabled(body)
                            for body in enemy_prefix_bodies
                        ),
                        "enemy_prefix_dormant_count": len(
                            dormant_enemy_body_pointers
                        ),
                        "enemy_prefix_attempts": (
                            enemy_prefix_snapshot.attempts
                        ),
                        "bullet_capture_span": bullet_capture_span,
                        "hazard_snapshot_age": hazard_snapshot_age,
                        "player_to_hazard_lag": player_to_hazard_lag,
                        "ecl_frame_before": ecl_frame_before,
                        "ecl_frame_after": ecl_frame_after,
                        "boss_guard_frame_before": (
                            boss_guard_frame_before
                        ),
                        "boss_guard_frame_after": (
                            boss_guard_frame_after
                        ),
                    },
                    "enemy_body_snapshot_frame": enemy_body_snapshot_frame,
                    "enemy_body_snapshot_age": (
                        counter_after_read - enemy_body_snapshot_frame
                        if enemy_body_snapshot_frame is not None
                        else None
                    ),
                    "issue_time_enemy_guard": {
                        "frame_before": (
                            issue_enemy_prefix_snapshot.frame_before
                        ),
                        "frame_after": (
                            issue_enemy_prefix_snapshot.frame_after
                        ),
                        "body_count": len(
                            issue_enemy_prefix_bodies
                        ),
                        "observed_body_count": len(
                            issue_enemy_prefix_snapshot.bodies
                        ),
                        "contact_enabled_count": sum(
                            enemy_body_contact_enabled(body)
                            for body in issue_enemy_prefix_snapshot.bodies
                        ),
                        "anticipatory_count": sum(
                            not enemy_body_contact_enabled(body)
                            for body in issue_enemy_prefix_snapshot.bodies
                        ),
                        "dormant_count": len(
                            issue_dormant_enemy_body_pointers
                        ),
                        "attempts": (
                            issue_enemy_prefix_snapshot.attempts
                        ),
                        "stable": (
                            issue_enemy_prefix_snapshot.stable
                        ),
                        "changes": list(issue_enemy_changes),
                        "recertified": bool(issue_enemy_changes),
                        "planned_action_before_guard": pre_issue_action,
                        "planned_mask_before_guard": pre_issue_mask,
                        "action_after_guard": post_issue_guard_action,
                        "mask_after_guard": post_issue_guard_mask,
                        "read_ms": issue_enemy_read_ms,
                        "recertificate_ms": (
                            issue_enemy_recertificate_ms
                        ),
                        "transaction": _issue_recertification_record(
                            decision.issue_recertification
                        ),
                    },
                    "spell_enemy_body_guard": (
                        {
                            "source": (
                                "boss_registry_or_spell_owner"
                            ),
                            "body": _serialized_enemy_bodies(
                                (spell_enemy_body_guard.body,)
                            )[0],
                            "contact_enabled": (
                                spell_enemy_body_guard.contact_enabled
                            ),
                            "anticipatory": (
                                not spell_enemy_body_guard.contact_enabled
                            ),
                            "covered_by_async_pool": (
                                enemy_pointer_in_scanned_pool(
                                    spell_enemy_body_guard.body.pointer
                                )
                            ),
                            "error": None,
                        }
                        if spell_enemy_body_guard is not None
                        else (
                            {"error": spell_enemy_body_guard_error}
                            if spell_enemy_body_guard_error is not None
                            else None
                        )
                    ),
                }
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
                if args.trace_radius > 0.0:
                    radius = args.trace_radius
                    record["nearby_bullets"] = [
                        serialize_bullet_trace(bullet)
                        for bullet in bullets
                        if abs(bullet.x - projected_player_x) <= radius
                        and abs(bullet.y - projected_player_y) <= radius
                    ]
                    record["lasers"] = [
                        serialize_laser_trace(laser)
                        for laser in lasers
                    ]
                    record["items"] = [
                        [
                            item.slot,
                            item.x,
                            item.y,
                            item.vx,
                            item.vy,
                            item.item_type,
                            item.motion_state,
                            item.full_value,
                        ]
                        for item in items
                    ]
                if args.trace_transform_runtime:
                    record["transform_bullets"] = [
                        serialize_bullet_trace(bullet)
                        for bullet in bullets
                        if bullet.transform_runtime is not None
                    ]
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
