#!/usr/bin/env python3
"""Live TH08 route-2 reactive dodge controller using native pool memory.

The controller is a receding-horizon smoke agent, not the final global solver.
It reads game state and projectile pools, then uses physical ``SendInput``
events. It never writes target memory and aborts on identity, route, gameplay,
or foreground-window divergence.
"""

from __future__ import annotations

import argparse
import functools
import json
import math
import struct
import time
from collections import deque
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np

from runtime_agent import input_transitions
from th08_bullet_transform_model import (
    BulletTransformRuntime,
    TransformRecord,
    parse_next_transform_record,
)
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
    corridor_policy_status as _corridor_policy_status,
    corridor_pipeline_prewarm_query as _corridor_pipeline_prewarm_query,
    corridor_pipeline_prewarm_retarget as _corridor_pipeline_prewarm_retarget,
    corridor_postpublished_survival_query as _corridor_postpublished_survival_query,
    corridor_safety_value_query as _corridor_safety_value_query,
    corridor_submit_due as _corridor_submit_due,
    corridor_target as _corridor_target,
    corridor_viability_query as _corridor_viability_query,
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
    velocity_changes_for_tagged_bullet,
)
from th08_laser_model import (
    LaserPhase,
    LaserState,
)
from th08_laser_runtime import (
    Laser,
    PackedLaserFrame as _PackedLaserFrame,
    build_laser_collision_frames,  # noqa: F401 - compatibility export
    build_packed_laser_collision_frames as _build_packed_laser_collision_frames,
    pack_laser_frame as _pack_laser_frame,
    serialize_laser_trace,
)
from th08_live import LiveSession
from th08_local_planner import (
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
    ProcessReader,
    _require_foreground,
    capture_input_clock_shadow,
    observe_state,
    send_scan_key,
    send_transitions,
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
    CandidateVerifierService,
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
    SemanticInputClockTracker,
)
from touhou_control.local_pipeline_oracle import LocalPipelineRoot
from touhou_control.policy_guidance import assemble_local_policy_guidance
from touhou_control.phase_progress import (
    PhaseProgressObservation,
    PhaseProgressTracker,
    ProgressCandidate,
    select_progress_action,
)
from touhou_control.supplemental_local_beam import (
    ExactVersionSupplementalService,
    SupplementalAction,
    SupplementalNode,
    search_supplemental_local_beam,
    search_supplemental_local_beam_native,
)
from touhou_control.trajectory import VelocityChange


BULLET_POOL_BASE = 0x00F6F710
BULLET_POOL_SIZE = 1536
BULLET_STRIDE = 0x10B8
BULLET_GEOMETRY_OFFSET = 0x0D34
BULLET_CALLBACK_PHASE_STATE_OFFSET = 0x01FC
BULLET_POSITION_OFFSET = 0x0D44
BULLET_VELOCITY_OFFSET = 0x0D50
BULLET_SPEED_OFFSET = 0x0D68
BULLET_ANGLE_OFFSET = 0x0D74
BULLET_TRANSFORM_FLAGS_OFFSET = 0x0DAC
BULLET_ORIGINAL_TRANSFORM_FLAGS_OFFSET = 0x0DB0
BULLET_STATE_OFFSET = 0x0DB8
BULLET_TRANSFORM_QUEUE_CURSOR_OFFSET = 0x0DCC
BULLET_TRANSFORM_PROGRAM_OFFSET = 0x0DD0
BULLET_STOP_TIMER_FRACTION_OFFSET = 0x1008
BULLET_STOP_TIMER_ELAPSED_OFFSET = 0x100C
BULLET_STOP_RESUME_SPEED_OFFSET = 0x1010
BULLET_STOP_ANGLE_OPERAND_OFFSET = 0x1014
BULLET_STOP_DURATION_OFFSET = 0x1024
BULLET_STOP_REPEAT_LIMIT_OFFSET = 0x1028
BULLET_STOP_REPEAT_COUNT_OFFSET = 0x102C
BULLET_CALLBACK_AUX_STATE_OFFSET = 0x10B4
ECL_CALLBACK_LOOKAHEAD_FRAMES = 256
INPUT_CLOCK_SHADOW_ROLE = "shadow_no_input_or_epoch_authority"
INPUT_CLOCK_SHADOW_WALL_CUT_SECONDS = 0.05

LASER_POOL_BASE = 0x015B57C8
LASER_POOL_SIZE = 256
LASER_STRIDE = 0x059C
LASER_ORIGIN_OFFSET = 0x0548
LASER_ANGLE_OFFSET = 0x0554
LASER_TAIL_OFFSET = 0x0558
LASER_HEAD_OFFSET = 0x055C
LASER_MAXIMUM_LENGTH_OFFSET = 0x0560
LASER_WIDTH_OFFSET = 0x0564
LASER_CURRENT_WIDTH_OFFSET = 0x0568
LASER_SPEED_OFFSET = 0x056C
LASER_WARMUP_FRAMES_OFFSET = 0x0570
LASER_COLLISION_ENABLE_FRAME_OFFSET = 0x0574
LASER_ACTIVE_FRAMES_OFFSET = 0x0578
LASER_FADE_FRAMES_OFFSET = 0x057C
LASER_COLLISION_DISABLE_FRAME_OFFSET = 0x0580
LASER_ACTIVE_OFFSET = 0x0584
LASER_TIMER_OFFSET = 0x0590
LASER_TIMER_FRACTION_OFFSET = 0x058C
LASER_FLAGS_OFFSET = 0x0594
LASER_PHASE_OFFSET = 0x0598
LASER_COLLISION_FLAG_OFFSET = 0x0599

ITEM_MANAGER_BASE = 0x01653648
ITEM_POOL_SIZE = 2096
ITEM_STRIDE = 0x02E4
ITEM_POSITION_OFFSET = 0x02A4
ITEM_VELOCITY_OFFSET = 0x02B0
ITEM_TYPE_OFFSET = 0x02D4
ITEM_ACTIVE_OFFSET = 0x02D5
ITEM_MOTION_STATE_OFFSET = 0x02D7
ITEM_FULL_VALUE_OFFSET = 0x02D8

# This vector advances the enemy's internal +0x2D34 motion component in
# sub_42DEB0.  It is not, in general, the derivative of the lethal world
# position at +0x2D88 because scripted/relative motion contributes separately.
ENEMY_VELOCITY_OFFSET = 0x2D4C
ENEMY_CONTACT_SIZE_OFFSET = 0x2D70
ENEMY_POSITION_OFFSET = 0x2D88
ENEMY_FLAGS_OFFSET = 0x3324
# This is the first of 480 ordinary timeline-enemy slots. Runtime spell-owner
# pointers are not guaranteed to belong to this range: Stage 5 Reisen was
# observed at 0x57D2F0, exactly one stride before this base.
ENEMY_POOL_BASE = 0x005826C0
ENEMY_POOL_SIZE = 480
ENEMY_STRIDE = 0x53D0
# Timeline allocation is contiguous from the front of the ordinary pool in
# every retained Stage 4A observation (highest active slot: 37).  Reading a
# guarded prefix in one ReadProcessMemory call on every local decision catches
# newly spawned contact bodies without paying 480 cross-process flag reads.
# The complete sparse scan remains the authoritative low-rate fallback.
ENEMY_LOCAL_PREFIX_SIZE = 64
ENEMY_BODY_READ_OFFSET = ENEMY_VELOCITY_OFFSET
ENEMY_BODY_READ_SIZE = ENEMY_FLAGS_OFFSET + 4 - ENEMY_BODY_READ_OFFSET
ENEMY_ACTIVE_FLAG = 0x00000001
ENEMY_CONTACT_ENABLED_FLAG = 0x00000004
ENEMY_CONTACT_BLOCKING_FLAGS = 0x00000830

PLAYER_LETHAL_AABB_OFFSET = 0x038C
PLAYER_LETHAL_AABB_SIZE = 0x14

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
PLANNING_BULLET_VECTOR_THRESHOLD = 512
NATIVE_PACKED_BULLET_MIN_COUNT = 16
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
ENEMY_MAX_OBSERVED_WORLD_SPEED = 32.0
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


@dataclass(frozen=True)
class Bullet:
    x: float
    y: float
    vx: float
    vy: float
    half_width: float
    half_height: float
    transform_flags: int = 0
    slot: int = -1
    speed: float | None = None
    angle: float | None = None
    transform_runtime: BulletTransformRuntime | None = None
    callback_phase_state: int = 0
    callback_aux_state: int = 0
    velocity_changes: tuple[VelocityChange, ...] = ()
    trajectory_uncertainty_x: float = 0.0
    trajectory_uncertainty_y: float = 0.0
    original_transform_flags: int = 0


@dataclass(frozen=True)
class PackedBulletSnapshot:
    """Owned planning fields with lazy compatibility materialization."""

    x: np.ndarray
    y: np.ndarray
    velocity_x: np.ndarray
    velocity_y: np.ndarray
    half_width: np.ndarray
    half_height: np.ndarray
    transform_flags: np.ndarray
    slots: np.ndarray
    speed: np.ndarray
    angle: np.ndarray
    callback_phase: np.ndarray
    callback_aux: np.ndarray
    original_transform_flags: np.ndarray

    def __len__(self) -> int:
        return len(self.x)

    def materialize(self, index: int) -> Bullet:
        speed = float(self.speed[index])
        angle = float(self.angle[index])
        return Bullet(
            x=float(self.x[index]),
            y=float(self.y[index]),
            vx=float(self.velocity_x[index]),
            vy=float(self.velocity_y[index]),
            half_width=float(self.half_width[index]),
            half_height=float(self.half_height[index]),
            transform_flags=int(self.transform_flags[index]),
            slot=int(self.slots[index]),
            speed=speed if math.isfinite(speed) else None,
            angle=angle if math.isfinite(angle) else None,
            callback_phase_state=int(self.callback_phase[index]),
            callback_aux_state=int(self.callback_aux[index]),
            original_transform_flags=int(
                self.original_transform_flags[index]
            ),
        )

    def __iter__(self):
        return (
            self.materialize(index)
            for index in range(len(self))
        )


def _serialize_transform_record(
    record: TransformRecord | None,
) -> list[float | int] | None:
    if record is None:
        return None
    return [
        record.index,
        record.kind,
        int(record.allow_while_active),
        float(record.float_0),
        float(record.float_1),
        record.int_0,
        record.int_1,
    ]


def serialize_bullet_trace(
    bullet: Bullet,
) -> list[object]:
    """Retain legacy geometry plus optional diagnostic/gameplay state.

    Fields 0..7 are the stable historical trace contract. Field 8 is either
    null or a compact transform payload:

    ``[speed, angle, original_flags, queue_cursor, next_record,
    timer_fraction, timer_elapsed, duration, resume_speed, angle_operand,
    repeat_limit, repeat_count, callback_phase_state, callback_aux_state,
    velocity_changes, trajectory_uncertainty_x,
    trajectory_uncertainty_y]``.

    When diagnostic runtime was not requested, field 8 remains null and an
    optional field 9 retains only gameplay projection state:

    ``[speed, angle, original_flags, callback_phase_state,
    callback_aux_state, velocity_changes, trajectory_uncertainty_x,
    trajectory_uncertainty_y]``.
    """

    legacy: list[object] = [
        bullet.slot,
        bullet.x,
        bullet.y,
        bullet.vx,
        bullet.vy,
        bullet.half_width,
        bullet.half_height,
        bullet.transform_flags,
    ]
    runtime = bullet.transform_runtime
    if runtime is None:
        if (
            bullet.original_transform_flags
            or bullet.velocity_changes
            or bullet.trajectory_uncertainty_x
            or bullet.trajectory_uncertainty_y
        ):
            return [
                *legacy,
                None,
                [
                    bullet.speed,
                    bullet.angle,
                    bullet.original_transform_flags,
                    bullet.callback_phase_state,
                    bullet.callback_aux_state,
                    [
                        [
                            change.frame,
                            change.velocity_x,
                            change.velocity_y,
                        ]
                        for change in bullet.velocity_changes
                    ],
                    bullet.trajectory_uncertainty_x,
                    bullet.trajectory_uncertainty_y,
                ],
            ]
        return [*legacy, None]
    return [
        *legacy,
        [
            bullet.speed,
            bullet.angle,
            runtime.original_flags,
            runtime.queue_cursor,
            _serialize_transform_record(runtime.next_record),
            runtime.timer_fraction,
            runtime.timer_elapsed,
            runtime.duration,
            runtime.resume_speed,
            runtime.angle_operand,
            runtime.repeat_limit,
            runtime.repeat_count,
            bullet.callback_phase_state,
            bullet.callback_aux_state,
            [
                [
                    change.frame,
                    change.velocity_x,
                    change.velocity_y,
                ]
                for change in bullet.velocity_changes
            ],
            bullet.trajectory_uncertainty_x,
            bullet.trajectory_uncertainty_y,
        ],
    ]


@dataclass(frozen=True)
class EnemyBody:
    pointer: int
    x: float
    y: float
    vx: float
    vy: float
    half_width: float
    half_height: float
    flags: int
    uncertainty: float = 0.0
    internal_vx: float | None = None
    internal_vy: float | None = None


@dataclass(frozen=True)
class SpellEnemyBodyGuard:
    """Current spell-owner geometry under an uncertain contact mode."""

    body: EnemyBody
    contact_enabled: bool


@dataclass(frozen=True)
class EnemyPoolSnapshot:
    frame_before: int
    frame_after: int
    bodies: tuple[EnemyBody, ...]
    read_ms: float
    attempts: int = 1

    @property
    def stable(self) -> bool:
        return self.frame_before == self.frame_after


class EnemyBodyModeMemory:
    """Estimate world motion and retain bodies hidden by native mode switches.

    Native +0x2D4C advances only one internal motion component.  The lethal
    +0x2D88 position can also contain scripted or relative motion, so its
    derivative must be estimated from consecutive world-position samples.
    Implausible secants are treated as hybrid jumps and preserve the last
    validated velocity.  Exact current-position measurements are not widened
    to pretend that an unobserved future mode has become known.
    """

    def __init__(
        self,
        *,
        maximum_age_frames: int,
        maximum_world_speed: float = ENEMY_MAX_OBSERVED_WORLD_SPEED,
    ) -> None:
        if maximum_age_frames <= 0:
            raise ValueError("enemy body memory age must be positive")
        if maximum_world_speed <= 0.0:
            raise ValueError("enemy world speed limit must be positive")
        self.maximum_age_frames = maximum_age_frames
        self.maximum_world_speed = maximum_world_speed
        self._context: object = None
        self._samples: dict[int, tuple[int, EnemyBody, bool]] = {}

    def set_context(self, context: object) -> bool:
        if context == self._context:
            return False
        self._context = context
        self._samples.clear()
        return True

    def clear(self) -> None:
        self._samples.clear()

    def merge_snapshot(
        self,
        snapshot: EnemyPoolSnapshot,
        *,
        frame: int,
    ) -> tuple[tuple[EnemyBody, ...], frozenset[int]]:
        """Merge current bodies with bounded projections of absent slots."""

        observed_pointers = {body.pointer for body in snapshot.bodies}
        for body in snapshot.bodies:
            previous = self._samples.get(body.pointer)
            velocity_known = body.internal_vx is None
            velocity_x = body.vx if velocity_known else 0.0
            velocity_y = body.vy if velocity_known else 0.0
            uncertainty = body.uncertainty
            if previous is not None:
                previous_frame, previous_body, previous_known = previous
                elapsed = snapshot.frame_after - previous_frame
                if elapsed > 0:
                    measured_x = (body.x - previous_body.x) / elapsed
                    measured_y = (body.y - previous_body.y) / elapsed
                    if (
                        abs(measured_x) <= self.maximum_world_speed
                        and abs(measured_y) <= self.maximum_world_speed
                    ):
                        velocity_x = measured_x
                        velocity_y = measured_y
                        velocity_known = True
                        uncertainty = body.uncertainty
                    else:
                        velocity_x = (
                            previous_body.vx if previous_known else 0.0
                        )
                        velocity_y = (
                            previous_body.vy if previous_known else 0.0
                        )
                        velocity_known = previous_known
                        uncertainty = body.uncertainty
                elif elapsed == 0:
                    velocity_x = previous_body.vx
                    velocity_y = previous_body.vy
                    velocity_known = previous_known
                    uncertainty = max(
                        body.uncertainty,
                        previous_body.uncertainty,
                    )
                else:
                    continue
            tracked = replace(
                body,
                vx=velocity_x,
                vy=velocity_y,
                uncertainty=uncertainty,
            )
            self._samples[body.pointer] = (
                snapshot.frame_after,
                tracked,
                velocity_known,
            )
        expired = [
            pointer
            for pointer, (
                sample_frame,
                _body,
                _velocity_known,
            ) in self._samples.items()
            if snapshot.frame_after - sample_frame > self.maximum_age_frames
        ]
        for pointer in expired:
            del self._samples[pointer]

        bodies = []
        dormant = set()
        for pointer, (
            sample_frame,
            body,
            _velocity_known,
        ) in sorted(self._samples.items()):
            age = frame - sample_frame
            if pointer not in observed_pointers:
                if age < 0 or age > self.maximum_age_frames:
                    continue
                dormant.add(pointer)
            bodies.append(
                replace(
                    body,
                    x=body.x + body.vx * age,
                    y=body.y + body.vy * age,
                    uncertainty=(
                        body.uncertainty
                        + min(16.0, 0.75 * abs(age))
                    ),
                )
            )
        return tuple(bodies), frozenset(dormant)


@dataclass(frozen=True)
class Item:
    slot: int
    x: float
    y: float
    vx: float
    vy: float
    item_type: int
    motion_state: int
    full_value: bool


@dataclass
class _LocalCertificateTimingAccumulator:
    calls: int = 0
    explicit_root_calls: int = 0
    maximum_branch_count: int = 0
    shared_laser_projection_ms: float = 0.0
    validation_ms: float = 0.0
    hazard_projection_ms: float = 0.0
    branch_setup_ms: float = 0.0
    geometry_kernel_ms: float = 0.0
    reduction_ms: float = 0.0
    certificate_total_ms: float = 0.0
    control_prefix_ms: float = 0.0
    planning_bullet_projection_ms: float = 0.0
    beam_search_ms: float = 0.0
    supplemental_beam_ms: float = 0.0
    terminal_threat_ms: float = 0.0
    selection_finalize_ms: float = 0.0

    def snapshot(self) -> LocalCertificateTiming:
        return LocalCertificateTiming(
            calls=self.calls,
            explicit_root_calls=self.explicit_root_calls,
            maximum_branch_count=self.maximum_branch_count,
            shared_laser_projection_ms=self.shared_laser_projection_ms,
            validation_ms=self.validation_ms,
            hazard_projection_ms=self.hazard_projection_ms,
            branch_setup_ms=self.branch_setup_ms,
            geometry_kernel_ms=self.geometry_kernel_ms,
            reduction_ms=self.reduction_ms,
            certificate_total_ms=self.certificate_total_ms,
            control_prefix_ms=self.control_prefix_ms,
            planning_bullet_projection_ms=(
                self.planning_bullet_projection_ms
            ),
            beam_search_ms=self.beam_search_ms,
            supplemental_beam_ms=self.supplemental_beam_ms,
            terminal_threat_ms=self.terminal_threat_ms,
            selection_finalize_ms=self.selection_finalize_ms,
        )


@dataclass(frozen=True)
class _PlannerModeTransition:
    current_decision: Decision
    next_request: LocalPlannerRequest
    original_allowed_action_count: int


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


@dataclass
class AutoConfirmPulse:
    """Create fresh Z edges after a sustained projectile-free interval."""

    interval_frames: int
    idle_frames: int
    eligible_since: int | None = None
    next_release_frame: int = 0
    released: bool = False

    def apply(
        self,
        *,
        frame: int,
        eligible: bool,
        mask: int,
    ) -> tuple[int, str | None]:
        if self.released:
            self.released = False
            self.next_release_frame = frame + self.interval_frames
            if not eligible:
                self.eligible_since = None
            return mask | SHOT, "press"
        if self.interval_frames <= 0:
            return mask, None
        if not eligible:
            self.eligible_since = None
            return mask, None
        if self.eligible_since is None:
            self.eligible_since = frame
        if (
            frame - self.eligible_since < self.idle_frames
            or frame < self.next_release_frame
        ):
            return mask, None
        self.released = True
        return mask & ~SHOT, "release"

    def frozen_pulse_due(
        self,
        *,
        now: float,
        last_progress: float,
        last_pulse: float,
        eligible: bool,
    ) -> bool:
        if self.interval_frames <= 0 or not eligible:
            return False
        frame_seconds = 1.0 / 60.0
        return (
            now - last_progress >= self.idle_frames * frame_seconds
            and now - last_pulse
            >= max(0.05, self.interval_frames * frame_seconds)
        )

    def mark_full_pulse(self, *, frame: int) -> None:
        self.released = False
        self.next_release_frame = frame + self.interval_frames


def _auto_confirm_eligible(
    *,
    player_phase: int,
    bomb_active: bool,
    active_bullets: int,
    active_lasers: int,
) -> bool:
    """Allow residual collectible items; only live hazards make a Z edge unsafe."""

    return (
        player_phase in (0, 3)
        and not bomb_active
        and active_bullets == 0
        and active_lasers == 0
    )


def _frozen_auto_confirm_eligible(*, bomb_active: bool) -> bool:
    """A frozen timeline makes projectile/item state inert; only exclude Bomb."""

    return not bomb_active


def _semantic_clock_observation(
    sample: dict[str, object],
    *,
    fallback_frame: int,
    context: object,
) -> SemanticClockObservation:
    player_after = sample.get("player_after")
    input_after = sample.get("input_after")
    position = None
    active_input = None
    if isinstance(player_after, dict):
        x = player_after.get("x")
        y = player_after.get("y")
        if isinstance(x, (int, float)) and isinstance(y, (int, float)):
            position = (float(x), float(y))
    if isinstance(input_after, dict):
        current = input_after.get("current")
        if isinstance(current, int):
            active_input = current
    manager_frame = sample.get("manager_frame_after")
    monotonic_ns = sample.get("monotonic_end_ns")
    semantic_active = sample.get("native_manager_clock_blocked")
    return SemanticClockObservation(
        monotonic_ns=(
            int(monotonic_ns)
            if isinstance(monotonic_ns, int)
            else time.perf_counter_ns()
        ),
        physical_frame=(
            int(manager_frame)
            if isinstance(manager_frame, int)
            else fallback_frame
        ),
        semantic_active=(
            semantic_active if isinstance(semantic_active, bool) else None
        ),
        context=context,
        position=position,
        active_input=active_input,
    )


def _serialize_semantic_clock_observation(
    observation: SemanticClockObservation,
) -> dict[str, object]:
    return {
        "monotonic_ns": observation.monotonic_ns,
        "physical_frame": observation.physical_frame,
        "semantic_active": observation.semantic_active,
        "context": observation.context,
        "position": observation.position,
        "active_input": observation.active_input,
    }


def _serialize_semantic_clock_event(
    event: SemanticClockEvent,
) -> dict[str, object]:
    return {
        "kind": "input_clock_shadow_episode",
        "role": INPUT_CLOCK_SHADOW_ROLE,
        "status": event.kind,
        "episode_id": event.episode_id,
        "frame": event.start.physical_frame,
        "current_frame": event.observation.physical_frame,
        "reason": event.reason,
        "pulse_count": event.pulse_count,
        "duration_ns": event.duration_ns,
        "displacement": event.displacement,
        "start": _serialize_semantic_clock_observation(event.start),
        "observation": _serialize_semantic_clock_observation(
            event.observation
        ),
    }


def _input_clock_message_key(
    sample: dict[str, object],
) -> tuple[object, ...]:
    return (
        sample.get("read_valid"),
        sample.get("frscreen_impl_pointer_after"),
        sample.get("msg_state_after"),
        sample.get("native_manager_clock_blocked"),
        sample.get("scripted_update_freeze_after"),
    )


@dataclass(frozen=True)
class SceneGuardDecision:
    status: str
    current_stage: int
    transition_from_stage: int | None
    expected_stage: int | None
    inactive_seconds: float
    entered: bool = False


@dataclass
class GameplaySceneGuard:
    """Distinguish a stage-resource transition from the final scene unload."""

    stage_successors: dict[int, int]
    transition_timeout_seconds: float
    terminal_grace_seconds: float
    last_active_stage: int | None = None
    inactive_since: float | None = None
    transition_from_stage: int | None = None

    def observe(
        self,
        *,
        gameplay_active: bool,
        current_stage: int,
        now: float,
    ) -> SceneGuardDecision:
        if gameplay_active:
            was_inactive = self.inactive_since is not None
            inactive_seconds = (
                now - self.inactive_since if self.inactive_since is not None else 0.0
            )
            transition_from = self.transition_from_stage
            expected_stage = self.stage_successors.get(transition_from)
            # TH08 writes the next stage index before clearing the gameplay
            # bit. Commit a new identity only at initial arm or after the
            # inactive interval has completed.
            if self.last_active_stage is None or was_inactive:
                self.last_active_stage = current_stage
            self.inactive_since = None
            self.transition_from_stage = None
            return SceneGuardDecision(
                status="resumed" if was_inactive else "active",
                current_stage=current_stage,
                transition_from_stage=transition_from,
                expected_stage=expected_stage,
                inactive_seconds=inactive_seconds,
            )

        entered = self.inactive_since is None
        if entered:
            self.inactive_since = now
            self.transition_from_stage = (
                self.last_active_stage
                if self.last_active_stage is not None
                else current_stage
            )
        assert self.inactive_since is not None
        transition_from = self.transition_from_stage
        expected_stage = self.stage_successors.get(transition_from)
        inactive_seconds = now - self.inactive_since
        if expected_stage is not None:
            status = (
                "stage_transition_timeout"
                if inactive_seconds >= self.transition_timeout_seconds
                else "stage_transition"
            )
        else:
            status = (
                "route_complete"
                if inactive_seconds >= self.terminal_grace_seconds
                else "terminal_unload"
            )
        return SceneGuardDecision(
            status=status,
            current_stage=current_stage,
            transition_from_stage=transition_from,
            expected_stage=expected_stage,
            inactive_seconds=inactive_seconds,
            entered=entered,
        )


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


def _finite(values: tuple[float, ...]) -> bool:
    return all(math.isfinite(value) for value in values)


def _native_bullet_half_extents(
    width: float,
    height: float,
) -> tuple[float, float]:
    """Preserve the dimensions passed to native bullet collision.

    Native templates are expected to contain positive dimensions.  Absolute
    value remains a conservative guard for a malformed signed snapshot, but
    there is no native minimum/maximum clamp.
    """

    return abs(width) * 0.5, abs(height) * 0.5


def _planning_bullet_active_slots(
    blob: bytes | bytearray | memoryview,
) -> np.ndarray:
    return np.flatnonzero(
        np.ndarray(
            (BULLET_POOL_SIZE,),
            dtype="<u2",
            buffer=blob,
            offset=BULLET_STATE_OFFSET,
            strides=(BULLET_STRIDE,),
        )
    )


def _decode_planning_bullets(
    blob: bytes | bytearray | memoryview,
    *,
    active_slots: np.ndarray | None = None,
) -> tuple[Bullet, ...]:
    """Decode the gameplay fields in bulk without diagnostic queue objects."""

    required_size = BULLET_POOL_SIZE * BULLET_STRIDE
    if len(blob) < required_size:
        raise ValueError(f"bullet pool requires {required_size} bytes")

    def scalar_field(offset: int, dtype: str) -> np.ndarray:
        return np.ndarray(
            (BULLET_POOL_SIZE,),
            dtype=dtype,
            buffer=blob,
            offset=offset,
            strides=(BULLET_STRIDE,),
        )

    def pair_field(offset: int, dtype: str) -> np.ndarray:
        item_size = np.dtype(dtype).itemsize
        return np.ndarray(
            (BULLET_POOL_SIZE, 2),
            dtype=dtype,
            buffer=blob,
            offset=offset,
            strides=(BULLET_STRIDE, item_size),
        )

    slots = (
        _planning_bullet_active_slots(blob)
        if active_slots is None
        else active_slots
    )
    if not slots.size:
        return ()
    if slots.size < PLANNING_BULLET_VECTOR_THRESHOLD:
        bullets: list[Bullet] = []
        for slot in slots:
            base = int(slot) * BULLET_STRIDE
            width, height = struct.unpack_from(
                "<ff",
                blob,
                base + BULLET_GEOMETRY_OFFSET,
            )
            x, y = struct.unpack_from(
                "<ff",
                blob,
                base + BULLET_POSITION_OFFSET,
            )
            vx, vy = struct.unpack_from(
                "<ff",
                blob,
                base + BULLET_VELOCITY_OFFSET,
            )
            if not _finite((x, y, vx, vy, width, height)):
                continue
            half_width, half_height = _native_bullet_half_extents(
                width,
                height,
            )
            speed = struct.unpack_from(
                "<f",
                blob,
                base + BULLET_SPEED_OFFSET,
            )[0]
            angle = struct.unpack_from(
                "<f",
                blob,
                base + BULLET_ANGLE_OFFSET,
            )[0]
            bullets.append(
                Bullet(
                    x=x,
                    y=y,
                    vx=vx,
                    vy=vy,
                    half_width=half_width,
                    half_height=half_height,
                    transform_flags=struct.unpack_from(
                        "<I",
                        blob,
                        base + BULLET_TRANSFORM_FLAGS_OFFSET,
                    )[0],
                    slot=int(slot),
                    speed=speed if math.isfinite(speed) else None,
                    angle=angle if math.isfinite(angle) else None,
                    callback_phase_state=struct.unpack_from(
                        "<h",
                        blob,
                        base + BULLET_CALLBACK_PHASE_STATE_OFFSET,
                    )[0],
                    callback_aux_state=blob[
                        base + BULLET_CALLBACK_AUX_STATE_OFFSET
                    ],
                    original_transform_flags=struct.unpack_from(
                        "<I",
                        blob,
                        base + BULLET_ORIGINAL_TRANSFORM_FLAGS_OFFSET,
                    )[0],
                )
            )
        return tuple(bullets)
    geometry = pair_field(BULLET_GEOMETRY_OFFSET, "<f4")[slots]
    position = pair_field(BULLET_POSITION_OFFSET, "<f4")[slots]
    velocity = pair_field(BULLET_VELOCITY_OFFSET, "<f4")[slots]
    finite = np.isfinite(
        np.concatenate((geometry, position, velocity), axis=1)
    ).all(axis=1)
    if not np.all(finite):
        slots = slots[finite]
        geometry = geometry[finite]
        position = position[finite]
        velocity = velocity[finite]
    speed = scalar_field(BULLET_SPEED_OFFSET, "<f4")[slots]
    angle = scalar_field(BULLET_ANGLE_OFFSET, "<f4")[slots]
    transform_flags = scalar_field(
        BULLET_TRANSFORM_FLAGS_OFFSET,
        "<u4",
    )[slots]
    original_flags = scalar_field(
        BULLET_ORIGINAL_TRANSFORM_FLAGS_OFFSET,
        "<u4",
    )[slots]
    callback_phase = scalar_field(
        BULLET_CALLBACK_PHASE_STATE_OFFSET,
        "<i2",
    )[slots]
    callback_aux = scalar_field(
        BULLET_CALLBACK_AUX_STATE_OFFSET,
        "u1",
    )[slots]
    half_size = np.abs(geometry) * 0.5
    return tuple(
        Bullet(
            x=float(x),
            y=float(y),
            vx=float(vx),
            vy=float(vy),
            half_width=float(half_width),
            half_height=float(half_height),
            transform_flags=int(active_flags),
            slot=int(slot),
            speed=float(native_speed) if math.isfinite(native_speed) else None,
            angle=float(native_angle) if math.isfinite(native_angle) else None,
            callback_phase_state=int(phase),
            callback_aux_state=int(auxiliary),
            original_transform_flags=int(tag_flags),
        )
        for (
            slot,
            (x, y),
            (vx, vy),
            (half_width, half_height),
            active_flags,
            native_speed,
            native_angle,
            tag_flags,
            phase,
            auxiliary,
        ) in zip(
            slots,
            position,
            velocity,
            half_size,
            transform_flags,
            speed,
            angle,
            original_flags,
            callback_phase,
            callback_aux,
        )
    )


def decode_packed_bullets(
    blob: bytes | bytearray | memoryview,
) -> PackedBulletSnapshot:
    """Decode the live planning snapshot through the parity-gated C ABI."""

    decoded = native_backend.decode_bullet_pool(
        blob,
        record_count=BULLET_POOL_SIZE,
        stride=BULLET_STRIDE,
        state_offset=BULLET_STATE_OFFSET,
        geometry_offset=BULLET_GEOMETRY_OFFSET,
        position_offset=BULLET_POSITION_OFFSET,
        velocity_offset=BULLET_VELOCITY_OFFSET,
        speed_offset=BULLET_SPEED_OFFSET,
        angle_offset=BULLET_ANGLE_OFFSET,
        transform_flags_offset=BULLET_TRANSFORM_FLAGS_OFFSET,
        original_transform_flags_offset=(
            BULLET_ORIGINAL_TRANSFORM_FLAGS_OFFSET
        ),
        callback_phase_offset=BULLET_CALLBACK_PHASE_STATE_OFFSET,
        callback_aux_offset=BULLET_CALLBACK_AUX_STATE_OFFSET,
    )
    if decoded is None:
        raise RuntimeError("native packed bullet decoder is unavailable")
    return PackedBulletSnapshot(
        x=decoded.x,
        y=decoded.y,
        velocity_x=decoded.velocity_x,
        velocity_y=decoded.velocity_y,
        half_width=decoded.half_width,
        half_height=decoded.half_height,
        transform_flags=decoded.transform_flags,
        slots=decoded.slots,
        speed=decoded.speed,
        angle=decoded.angle,
        callback_phase=decoded.callback_phase,
        callback_aux=decoded.callback_aux,
        original_transform_flags=decoded.original_transform_flags,
    )


def decode_live_planning_bullets(
    blob: bytes | bytearray | memoryview,
    *,
    backend: str,
) -> tuple[Bullet, ...] | PackedBulletSnapshot:
    """Decode with the selected rollback and the measured sparse crossover."""

    if backend == "python":
        return _decode_planning_bullets(blob)
    if backend != "native":
        raise ValueError(f"unknown bullet decode backend {backend!r}")
    active_slots = _planning_bullet_active_slots(blob)
    if len(active_slots) < NATIVE_PACKED_BULLET_MIN_COUNT:
        return _decode_planning_bullets(
            blob,
            active_slots=active_slots,
        )
    return decode_packed_bullets(blob)


def decode_bullets(
    blob: bytes,
    *,
    retain_transform_runtime: bool = True,
) -> tuple[Bullet, ...]:
    """Decode active bullets, optionally retaining diagnostic queue state.

    Gameplay planning needs original tag flags, active transform flags, and
    callback state on every bullet. The larger queue/stop runtime is only an
    observation artifact until a separately validated transform projector
    consumes it.
    """

    if not retain_transform_runtime:
        return _decode_planning_bullets(blob)
    bullets: list[Bullet] = []
    for index in range(BULLET_POOL_SIZE):
        base = index * BULLET_STRIDE
        state = struct.unpack_from("<H", blob, base + BULLET_STATE_OFFSET)[0]
        if state == 0:
            continue
        width, height = struct.unpack_from("<ff", blob, base + BULLET_GEOMETRY_OFFSET)
        x, y = struct.unpack_from("<ff", blob, base + BULLET_POSITION_OFFSET)
        vx, vy = struct.unpack_from("<ff", blob, base + BULLET_VELOCITY_OFFSET)
        speed = struct.unpack_from("<f", blob, base + BULLET_SPEED_OFFSET)[0]
        angle = struct.unpack_from("<f", blob, base + BULLET_ANGLE_OFFSET)[0]
        callback_phase_state = struct.unpack_from(
            "<h",
            blob,
            base + BULLET_CALLBACK_PHASE_STATE_OFFSET,
        )[0]
        callback_aux_state = blob[
            base + BULLET_CALLBACK_AUX_STATE_OFFSET
        ]
        transform_flags = struct.unpack_from(
            "<I", blob, base + BULLET_TRANSFORM_FLAGS_OFFSET
        )[0]
        original_transform_flags = struct.unpack_from(
            "<I",
            blob,
            base + BULLET_ORIGINAL_TRANSFORM_FLAGS_OFFSET,
        )[0]
        if not _finite((x, y, vx, vy, width, height)):
            continue
        half_width, half_height = _native_bullet_half_extents(
            width,
            height,
        )
        transform_runtime = None
        if retain_transform_runtime:
            queue_cursor = struct.unpack_from(
                "<i",
                blob,
                base + BULLET_TRANSFORM_QUEUE_CURSOR_OFFSET,
            )[0]
            next_record = parse_next_transform_record(
                blob,
                program_offset=base + BULLET_TRANSFORM_PROGRAM_OFFSET,
                queue_cursor=queue_cursor,
            )
            if (
                transform_flags
                or original_transform_flags
                or (next_record is not None and next_record.kind)
            ):
                transform_runtime = BulletTransformRuntime(
                    original_flags=original_transform_flags,
                    queue_cursor=queue_cursor,
                    next_record=next_record,
                    timer_fraction=struct.unpack_from(
                        "<f",
                        blob,
                        base + BULLET_STOP_TIMER_FRACTION_OFFSET,
                    )[0],
                    timer_elapsed=struct.unpack_from(
                        "<i",
                        blob,
                        base + BULLET_STOP_TIMER_ELAPSED_OFFSET,
                    )[0],
                    resume_speed=struct.unpack_from(
                        "<f",
                        blob,
                        base + BULLET_STOP_RESUME_SPEED_OFFSET,
                    )[0],
                    angle_operand=struct.unpack_from(
                        "<f",
                        blob,
                        base + BULLET_STOP_ANGLE_OPERAND_OFFSET,
                    )[0],
                    duration=struct.unpack_from(
                        "<i",
                        blob,
                        base + BULLET_STOP_DURATION_OFFSET,
                    )[0],
                    repeat_limit=struct.unpack_from(
                        "<i",
                        blob,
                        base + BULLET_STOP_REPEAT_LIMIT_OFFSET,
                    )[0],
                    repeat_count=struct.unpack_from(
                        "<i",
                        blob,
                        base + BULLET_STOP_REPEAT_COUNT_OFFSET,
                    )[0],
                )
        bullets.append(
            Bullet(
                x=x,
                y=y,
                vx=vx,
                vy=vy,
                half_width=half_width,
                half_height=half_height,
                transform_flags=transform_flags,
                slot=index,
                speed=speed if math.isfinite(speed) else None,
                angle=angle if math.isfinite(angle) else None,
                transform_runtime=transform_runtime,
                callback_phase_state=callback_phase_state,
                callback_aux_state=callback_aux_state,
                original_transform_flags=original_transform_flags,
            )
        )
    return tuple(bullets)


def attach_tagged_velocity_toggles(
    bullets: tuple[Bullet, ...],
    *,
    vm_snapshot: EclVmSnapshot,
    toggles: tuple[TaggedVelocityToggle, ...],
    frame_offset: int = 0,
    event_frame_uncertainty: int = 0,
) -> tuple[Bullet, ...]:
    """Attach callback-12 events in each bullet snapshot's time coordinate."""

    if frame_offset < 0 or event_frame_uncertainty < 0:
        raise ValueError("ECL event alignment values cannot be negative")
    if not toggles:
        return bullets
    aligned_toggles = tuple(
        replace(toggle, frame=toggle.frame + frame_offset)
        for toggle in toggles
    )
    attached: list[Bullet] = []
    for bullet in bullets:
        runtime = bullet.transform_runtime
        tag_flags = (
            bullet.original_transform_flags
            or (runtime.original_flags if runtime is not None else 0)
        )
        changes = velocity_changes_for_tagged_bullet(
            tag_flags=tag_flags,
            phase_state=bullet.callback_phase_state,
            base_speed=bullet.speed,
            base_angle=bullet.angle,
            time_scale=vm_snapshot.time_scale,
            toggles=aligned_toggles,
        )
        uncertainty_x = bullet.trajectory_uncertainty_x
        uncertainty_y = bullet.trajectory_uncertainty_y
        previous_x = bullet.vx
        previous_y = bullet.vy
        for change in changes:
            uncertainty_x += (
                abs(change.velocity_x - previous_x)
                * event_frame_uncertainty
            )
            uncertainty_y += (
                abs(change.velocity_y - previous_y)
                * event_frame_uncertainty
            )
            previous_x = change.velocity_x
            previous_y = change.velocity_y
        attached.append(
            replace(
                bullet,
                velocity_changes=changes,
                trajectory_uncertainty_x=uncertainty_x,
                trajectory_uncertainty_y=uncertainty_y,
            )
            if changes
            else bullet
        )
    return tuple(attached)


def decode_lasers(blob: bytes) -> tuple[Laser, ...]:
    lasers: list[Laser] = []
    for index in range(LASER_POOL_SIZE):
        base = index * LASER_STRIDE
        if not struct.unpack_from("<I", blob, base + LASER_ACTIVE_OFFSET)[0]:
            continue
        origin_x, origin_y = struct.unpack_from("<ff", blob, base + LASER_ORIGIN_OFFSET)
        angle = struct.unpack_from("<f", blob, base + LASER_ANGLE_OFFSET)[0]
        tail = struct.unpack_from("<f", blob, base + LASER_TAIL_OFFSET)[0]
        head = struct.unpack_from("<f", blob, base + LASER_HEAD_OFFSET)[0]
        maximum_length, width, current_width, speed = struct.unpack_from(
            "<ffff",
            blob,
            base + LASER_MAXIMUM_LENGTH_OFFSET,
        )
        (
            warmup_frames,
            collision_enable_frame,
            active_frames,
            fade_frames,
            collision_disable_frame,
        ) = struct.unpack_from(
            "<iiiii",
            blob,
            base + LASER_WARMUP_FRAMES_OFFSET,
        )
        timer = struct.unpack_from("<i", blob, base + LASER_TIMER_OFFSET)[0]
        timer_fraction = struct.unpack_from(
            "<f",
            blob,
            base + LASER_TIMER_FRACTION_OFFSET,
        )[0]
        flags = struct.unpack_from("<H", blob, base + LASER_FLAGS_OFFSET)[0]
        phase_value = blob[base + LASER_PHASE_OFFSET]
        collision_flag = blob[base + LASER_COLLISION_FLAG_OFFSET]
        if not _finite(
            (
                origin_x,
                origin_y,
                angle,
                tail,
                head,
                maximum_length,
                width,
                current_width,
                speed,
                timer_fraction,
            )
        ):
            continue
        if (
            phase_value not in tuple(int(phase) for phase in LaserPhase)
            or min(
                maximum_length,
                width,
                warmup_frames,
                collision_enable_frame,
                active_frames,
                fade_frames,
                collision_disable_frame,
                timer,
            )
            < 0
        ):
            continue
        state = LaserState(
            origin_x=origin_x,
            origin_y=origin_y,
            angle=angle,
            tail_distance=tail,
            head_distance=head,
            maximum_length=maximum_length,
            width=width,
            speed=speed,
            warmup_frames=warmup_frames,
            active_frames=active_frames,
            fade_frames=fade_frames,
            collision_enable_frame=collision_enable_frame,
            collision_disable_frame=collision_disable_frame,
            flags=flags,
            current_width=current_width,
            phase=LaserPhase(phase_value),
            timer=timer,
            timer_fraction=timer_fraction,
        )
        lasers.append(
            Laser(
                origin_x,
                origin_y,
                angle,
                tail,
                head,
                min(abs(width) * 0.25, 64.0),
                state,
                index,
                collision_flag,
                0.75,
                0.0,
            )
        )
    return tuple(lasers)


def decode_items(blob: bytes) -> tuple[Item, ...]:
    items: list[Item] = []
    for index in range(ITEM_POOL_SIZE):
        base = index * ITEM_STRIDE
        if not blob[base + ITEM_ACTIVE_OFFSET]:
            continue
        x, y = struct.unpack_from("<ff", blob, base + ITEM_POSITION_OFFSET)
        vx, vy = struct.unpack_from("<ff", blob, base + ITEM_VELOCITY_OFFSET)
        if not _finite((x, y, vx, vy)):
            continue
        items.append(
            Item(
                slot=index,
                x=x,
                y=y,
                vx=vx,
                vy=vy,
                item_type=blob[base + ITEM_TYPE_OFFSET],
                motion_state=blob[base + ITEM_MOTION_STATE_OFFSET],
                full_value=bool(blob[base + ITEM_FULL_VALUE_OFFSET]),
            )
        )
    return tuple(items)


def _decode_enemy_body_geometry(
    blob: bytes,
    *,
    pointer: int,
) -> EnemyBody | None:
    if len(blob) < ENEMY_BODY_READ_SIZE:
        raise ValueError(
            f"enemy body window requires {ENEMY_BODY_READ_SIZE} bytes"
        )
    velocity_offset = ENEMY_VELOCITY_OFFSET - ENEMY_BODY_READ_OFFSET
    contact_offset = ENEMY_CONTACT_SIZE_OFFSET - ENEMY_BODY_READ_OFFSET
    position_offset = ENEMY_POSITION_OFFSET - ENEMY_BODY_READ_OFFSET
    flags_offset = ENEMY_FLAGS_OFFSET - ENEMY_BODY_READ_OFFSET
    internal_vx, internal_vy = struct.unpack_from(
        "<ff",
        blob,
        velocity_offset,
    )
    contact_width, contact_height = struct.unpack_from(
        "<ff",
        blob,
        contact_offset,
    )
    x, y = struct.unpack_from("<ff", blob, position_offset)
    flags = struct.unpack_from("<I", blob, flags_offset)[0]
    if not flags & ENEMY_ACTIVE_FLAG:
        return None
    if not _finite(
        (
            x,
            y,
            internal_vx,
            internal_vy,
            contact_width,
            contact_height,
        )
    ):
        return None
    if contact_width < 0.0 or contact_height < 0.0:
        return None
    return EnemyBody(
        pointer=pointer,
        x=x,
        y=y,
        # +0x2D4C advances an internal motion component, not necessarily the
        # collision position.  EnemyBodyModeMemory supplies the observed
        # world-position derivative before this body reaches planning.
        vx=0.0,
        vy=0.0,
        # Native path: full contact size * 1.5, then center +/- size/2.
        half_width=0.75 * contact_width,
        half_height=0.75 * contact_height,
        flags=flags,
        internal_vx=internal_vx,
        internal_vy=internal_vy,
    )


def decode_enemy_body(blob: bytes, *, pointer: int) -> EnemyBody | None:
    body = _decode_enemy_body_geometry(blob, pointer=pointer)
    if body is None or (
        not body.flags & ENEMY_CONTACT_ENABLED_FLAG
        or body.flags & ENEMY_CONTACT_BLOCKING_FLAGS
    ):
        return None
    return body


def enemy_body_contact_enabled(body: EnemyBody) -> bool:
    """Return the native contact-mode gate represented by one body sample."""

    return bool(
        body.flags & ENEMY_CONTACT_ENABLED_FLAG
        and not body.flags & ENEMY_CONTACT_BLOCKING_FLAGS
    )


def enemy_pointer_in_scanned_pool(pointer: int) -> bool:
    """Return whether an enemy pointer is one of the 480 async-scanned slots."""

    offset = pointer - ENEMY_POOL_BASE
    return (
        0 <= offset < ENEMY_POOL_SIZE * ENEMY_STRIDE
        and offset % ENEMY_STRIDE == 0
    )


def decode_spell_enemy_body_guard(
    blob: bytes,
    *,
    pointer: int,
) -> SpellEnemyBodyGuard | None:
    """Retain the spell owner even when the async pool cannot observe it.

    The owner may live outside the 480-slot timeline-enemy pool. Even for an
    owner inside that pool, the asynchronous reader observes only bodies whose
    contact mode is already enabled. Survival planning therefore reads the
    authoritative owner pointer synchronously and takes the union of enabled
    and disabled contact-mode geometries.
    """

    body = _decode_enemy_body_geometry(blob, pointer=pointer)
    if body is None:
        return None
    return SpellEnemyBodyGuard(
        body=body,
        contact_enabled=bool(
            body.flags & ENEMY_CONTACT_ENABLED_FLAG
            and not body.flags & ENEMY_CONTACT_BLOCKING_FLAGS
        ),
    )


def decode_enemy_bodies(
    blob: bytes,
    *,
    pool_size: int = ENEMY_POOL_SIZE,
    include_contact_disabled: bool = False,
) -> tuple[EnemyBody, ...]:
    """Decode ordinary enemy collision geometry from a contiguous pool.

    The default preserves the exact currently-enabled native contact set.
    A synchronous safety guard may instead request active, non-blocked bodies
    whose contact bit is currently disabled.  Those bodies represent the
    robust union over a contact mode that can toggle before actuator pickup.
    """

    if not 0 <= pool_size <= ENEMY_POOL_SIZE:
        raise ValueError("enemy pool size must belong to the native pool")
    expected_size = pool_size * ENEMY_STRIDE
    if len(blob) < expected_size:
        raise ValueError(
            f"enemy pool requires {expected_size} bytes"
        )
    bodies: list[EnemyBody] = []
    for slot in range(pool_size):
        base = slot * ENEMY_STRIDE
        flags = struct.unpack_from(
            "<I",
            blob,
            base + ENEMY_FLAGS_OFFSET,
        )[0]
        if (
            not flags & ENEMY_ACTIVE_FLAG
            or flags & ENEMY_CONTACT_BLOCKING_FLAGS
            or (
                not include_contact_disabled
                and not flags & ENEMY_CONTACT_ENABLED_FLAG
            )
        ):
            continue
        internal_vx, internal_vy = struct.unpack_from(
            "<ff",
            blob,
            base + ENEMY_VELOCITY_OFFSET,
        )
        contact_width, contact_height = struct.unpack_from(
            "<ff",
            blob,
            base + ENEMY_CONTACT_SIZE_OFFSET,
        )
        x, y = struct.unpack_from(
            "<ff",
            blob,
            base + ENEMY_POSITION_OFFSET,
        )
        if not _finite(
            (
                x,
                y,
                internal_vx,
                internal_vy,
                contact_width,
                contact_height,
            )
        ):
            continue
        if contact_width < 0.0 or contact_height < 0.0:
            continue
        if (
            include_contact_disabled
            and not flags & ENEMY_CONTACT_ENABLED_FLAG
            and (contact_width == 0.0 or contact_height == 0.0)
        ):
            continue
        bodies.append(
            EnemyBody(
                pointer=ENEMY_POOL_BASE + base,
                x=x,
                y=y,
                vx=0.0,
                vy=0.0,
                half_width=0.75 * contact_width,
                half_height=0.75 * contact_height,
                flags=flags,
                internal_vx=internal_vx,
                internal_vy=internal_vy,
            )
        )
    return tuple(bodies)


def capture_enemy_pool_snapshot_contiguous(
    reader: ProcessReader,
) -> EnemyPoolSnapshot:
    started = time.perf_counter()
    frame_before = reader.u32(ADDR_ENEMY_MANAGER_FRAME)
    blob = reader.read(
        ENEMY_POOL_BASE,
        ENEMY_POOL_SIZE * ENEMY_STRIDE,
    )
    frame_after = reader.u32(ADDR_ENEMY_MANAGER_FRAME)
    return EnemyPoolSnapshot(
        frame_before,
        frame_after,
        decode_enemy_bodies(blob),
        (time.perf_counter() - started) * 1000.0,
    )


def capture_enemy_pool_prefix_contiguous(
    reader: ProcessReader,
    *,
    pool_size: int = ENEMY_LOCAL_PREFIX_SIZE,
    maximum_attempts: int = 2,
) -> EnemyPoolSnapshot:
    """Capture the allocation head once per local decision.

    This is a freshness fast path, not a complete-pool assumption.  The
    background sparse scanner still supplies slots outside the prefix.
    """

    if not 0 < pool_size <= ENEMY_POOL_SIZE:
        raise ValueError("enemy prefix size must belong to the native pool")
    if maximum_attempts <= 0:
        raise ValueError("enemy prefix attempts must be positive")
    started = time.perf_counter()
    snapshot = None
    for attempt in range(1, maximum_attempts + 1):
        frame_before = reader.u32(ADDR_ENEMY_MANAGER_FRAME)
        blob = reader.read(ENEMY_POOL_BASE, pool_size * ENEMY_STRIDE)
        frame_after = reader.u32(ADDR_ENEMY_MANAGER_FRAME)
        snapshot = EnemyPoolSnapshot(
            frame_before,
            frame_after,
            decode_enemy_bodies(
                blob,
                pool_size=pool_size,
                include_contact_disabled=True,
            ),
            (time.perf_counter() - started) * 1000.0,
            attempt,
        )
        if snapshot.stable:
            return snapshot
    assert snapshot is not None
    return snapshot


def read_enemy_bodies_sparse(
    reader: ProcessReader,
) -> tuple[EnemyBody, ...]:
    """Read flags for every slot, then fetch only enabled body windows."""

    bodies = []
    for slot in range(ENEMY_POOL_SIZE):
        pointer = ENEMY_POOL_BASE + slot * ENEMY_STRIDE
        flags = reader.u32(pointer + ENEMY_FLAGS_OFFSET)
        if (
            not flags & ENEMY_ACTIVE_FLAG
            or not flags & ENEMY_CONTACT_ENABLED_FLAG
            or flags & ENEMY_CONTACT_BLOCKING_FLAGS
        ):
            continue
        body = decode_enemy_body(
            reader.read(
                pointer + ENEMY_BODY_READ_OFFSET,
                ENEMY_BODY_READ_SIZE,
            ),
            pointer=pointer,
        )
        if body is not None:
            bodies.append(body)
    return tuple(bodies)


def capture_enemy_pool_snapshot_sparse(
    reader: ProcessReader,
) -> EnemyPoolSnapshot:
    started = time.perf_counter()
    frame_before = reader.u32(ADDR_ENEMY_MANAGER_FRAME)
    bodies = read_enemy_bodies_sparse(reader)
    frame_after = reader.u32(ADDR_ENEMY_MANAGER_FRAME)
    return EnemyPoolSnapshot(
        frame_before,
        frame_after,
        bodies,
        (time.perf_counter() - started) * 1000.0,
    )


# Sparse reads retained the same bodies in paused multi-enemy runtime
# differentials while reducing capture latency enough to scan four times as
# often at approximately the old bandwidth duty cycle.
capture_enemy_pool_snapshot = capture_enemy_pool_snapshot_sparse


def project_enemy_pool_snapshot(
    snapshot: EnemyPoolSnapshot | None,
    *,
    frame: int,
) -> tuple[EnemyBody, ...]:
    if snapshot is None:
        return ()
    age = frame - snapshot.frame_after
    uncertainty = min(16.0, 0.75 * abs(age))
    return tuple(
        replace(
            body,
            x=body.x + body.vx * age,
            y=body.y + body.vy * age,
            uncertainty=body.uncertainty + uncertainty,
        )
        for body in snapshot.bodies
    )


def merge_enemy_pool_prefix(
    background_bodies: tuple[EnemyBody, ...],
    prefix_bodies: tuple[EnemyBody, ...],
    *,
    pool_size: int = ENEMY_LOCAL_PREFIX_SIZE,
) -> tuple[EnemyBody, ...]:
    """Replace stale background copies in the synchronously read prefix."""

    if not 0 < pool_size <= ENEMY_POOL_SIZE:
        raise ValueError("enemy prefix size must belong to the native pool")
    prefix_end = ENEMY_POOL_BASE + pool_size * ENEMY_STRIDE
    tail = tuple(
        body
        for body in background_bodies
        if not ENEMY_POOL_BASE <= body.pointer < prefix_end
    )
    return prefix_bodies + tail


def enemy_pool_snapshot_changes(
    planned: EnemyPoolSnapshot,
    current: EnemyPoolSnapshot,
    *,
    position_tolerance: float = 2.0,
    velocity_tolerance: float = 0.25,
    size_tolerance: float = 0.25,
) -> tuple[str, ...]:
    """Detect contact-topology or non-linear geometry changes during planning."""

    if not planned.stable or not current.stable:
        return ("unstable_capture",)
    if current.frame_after < planned.frame_after:
        return ("frame_reversed",)
    planned_by_pointer = {body.pointer: body for body in planned.bodies}
    current_by_pointer = {body.pointer: body for body in current.bodies}
    changes = []
    for pointer in sorted(current_by_pointer.keys() - planned_by_pointer.keys()):
        changes.append(f"added:{pointer:#x}")
    for pointer in sorted(planned_by_pointer.keys() - current_by_pointer.keys()):
        changes.append(f"removed:{pointer:#x}")
    frame_delta = current.frame_after - planned.frame_after
    relevant_flags = (
        ENEMY_ACTIVE_FLAG
        | ENEMY_CONTACT_ENABLED_FLAG
        | ENEMY_CONTACT_BLOCKING_FLAGS
    )
    for pointer in sorted(planned_by_pointer.keys() & current_by_pointer.keys()):
        before = planned_by_pointer[pointer]
        after = current_by_pointer[pointer]
        expected_x = before.x + before.vx * frame_delta
        expected_y = before.y + before.vy * frame_delta
        if (
            abs(after.x - expected_x) > position_tolerance
            or abs(after.y - expected_y) > position_tolerance
        ):
            changes.append(f"trajectory:{pointer:#x}")
        if (
            abs(after.vx - before.vx) > velocity_tolerance
            or abs(after.vy - before.vy) > velocity_tolerance
        ):
            changes.append(f"velocity:{pointer:#x}")
        if (
            abs(after.half_width - before.half_width) > size_tolerance
            or abs(after.half_height - before.half_height) > size_tolerance
        ):
            changes.append(f"size:{pointer:#x}")
        if (after.flags ^ before.flags) & relevant_flags:
            changes.append(f"contact_mode:{pointer:#x}")
    return tuple(changes)


def issue_enemy_snapshot_changes(
    planned_raw: EnemyPoolSnapshot,
    current_raw: EnemyPoolSnapshot,
    planned_aligned: EnemyPoolSnapshot,
    current_aligned: EnemyPoolSnapshot,
) -> tuple[str, ...]:
    """Version an issue guard by topology and aligned world trajectories."""

    raw_changes = enemy_pool_snapshot_changes(planned_raw, current_raw)
    aligned_changes = enemy_pool_snapshot_changes(
        planned_aligned,
        current_aligned,
    )
    topology_kinds = {
        "added",
        "removed",
        "size",
        "contact_mode",
        "unstable_capture",
        "frame_reversed",
    }
    return tuple(
        dict.fromkeys(
            change
            for change in (*raw_changes, *aligned_changes)
            if change.split(":", 1)[0] in topology_kinds
            or change in aligned_changes
        )
    )


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


def read_spell_enemy_bodies(
    reader: ProcessReader,
    spell: dict[str, object],
) -> tuple[EnemyBody, ...]:
    if not bool(spell.get("active")):
        return ()
    pointer = int(spell.get("enemy_pointer", 0))
    if pointer == 0:
        return ()
    blob = reader.read(
        pointer + ENEMY_BODY_READ_OFFSET,
        ENEMY_BODY_READ_SIZE,
    )
    body = decode_enemy_body(blob, pointer=pointer)
    return (body,) if body is not None else ()


def read_spell_enemy_body_guard(
    reader: ProcessReader,
    spell: dict[str, object],
) -> SpellEnemyBodyGuard | None:
    if not bool(spell.get("active")):
        return None
    pointer = int(spell.get("enemy_pointer", 0))
    if pointer == 0:
        return None
    return read_enemy_body_guard(reader, pointer=pointer)


def read_enemy_body_guard(
    reader: ProcessReader,
    *,
    pointer: int,
) -> SpellEnemyBodyGuard | None:
    """Read one active enemy body, including latent contact mode geometry."""

    return decode_spell_enemy_body_guard(
        reader.read(
            pointer + ENEMY_BODY_READ_OFFSET,
            ENEMY_BODY_READ_SIZE,
        ),
        pointer=pointer,
    )


def merge_spell_enemy_body_guard(
    bodies: tuple[EnemyBody, ...],
    guard: SpellEnemyBodyGuard | None,
) -> tuple[EnemyBody, ...]:
    if guard is None:
        return bodies
    return tuple(
        body for body in bodies if body.pointer != guard.body.pointer
    ) + (guard.body,)


def decode_player_lethal_aabb(
    blob: bytes,
) -> tuple[float, float, float, float] | None:
    if len(blob) < PLAYER_LETHAL_AABB_SIZE:
        raise ValueError(
            f"player lethal AABB requires {PLAYER_LETHAL_AABB_SIZE} bytes"
        )
    left, top = struct.unpack_from("<ff", blob, 0)
    right, bottom = struct.unpack_from("<ff", blob, 0x0C)
    if not _finite((left, top, right, bottom)):
        return None
    if left > right or top > bottom:
        return None
    return left, top, right, bottom


def _serialized_enemy_bodies(
    bodies: tuple[EnemyBody, ...],
) -> list[list[float | int | None]]:
    return [
        [
            body.pointer,
            body.x,
            body.y,
            body.vx,
            body.vy,
            body.half_width,
            body.half_height,
            body.flags,
            body.uncertainty,
            body.internal_vx,
            body.internal_vy,
        ]
        for body in bodies
    ]


def capture_hit_contact_observation(
    reader: ProcessReader,
    spell: dict[str, object],
    *,
    attempts: int = 3,
) -> dict[str, object]:
    observation: dict[str, object] = {}
    for _ in range(max(1, attempts)):
        frame_before = reader.u32(ADDR_ENEMY_MANAGER_FRAME)
        player_blob = reader.read(
            ADDR_PLAYER + PLAYER_LETHAL_AABB_OFFSET,
            PLAYER_LETHAL_AABB_SIZE,
        )
        enemy_blob = reader.read(
            ENEMY_POOL_BASE,
            ENEMY_POOL_SIZE * ENEMY_STRIDE,
        )
        enemy_bodies = decode_enemy_bodies(enemy_blob)
        frame_after = reader.u32(ADDR_ENEMY_MANAGER_FRAME)
        player_aabb = decode_player_lethal_aabb(player_blob)
        observation = {
            "frame_before": frame_before,
            "frame_after": frame_after,
            "stable": frame_before == frame_after,
            "player_lethal_aabb": (
                list(player_aabb) if player_aabb is not None else None
            ),
            "enemy_bodies": _serialized_enemy_bodies(enemy_bodies),
        }
        if observation["stable"]:
            break
    return observation


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


def _run_local_planner_pass(
    request: LocalPlannerRequest,
    preparation: PlannerPassPreparation,
    *,
    _certificate_timing_accumulator: (
        _LocalCertificateTimingAccumulator
    ),
) -> Decision | _PlannerModeTransition:
    physical = request.physical
    actuator = request.actuator
    guidance = request.guidance
    config = request.config
    objective = request.objective
    completed = request.completed_services

    player_x = physical.player_x
    player_y = physical.player_y
    bullets = physical.bullets
    lasers = physical.lasers
    enemy_bodies = physical.enemy_bodies
    snapshot_lag = physical.snapshot_lag

    previous_direction = actuator.previous_direction
    previous_focus = actuator.previous_focus
    local_pipeline_root = actuator.local_pipeline_root
    control_delay_frames = actuator.control_delay_frames
    control_delay_candidates = actuator.control_delay_candidates
    action_hold_frames = actuator.action_hold_frames

    target_x = guidance.target_x
    target_y = guidance.target_y
    target_deadline = guidance.target_deadline
    allowed_first_actions = guidance.allowed_first_actions
    viability_repair_volumes = guidance.viability_repair_volumes
    viability_recovery_distances = (
        guidance.viability_recovery_distances
    )
    viability_safety_actions = guidance.viability_safety_actions
    viability_survival_actions = guidance.viability_survival_actions

    horizon = config.horizon
    beam_width = config.beam_width
    preloss_continuation_preference = (
        config.preloss_continuation_preference
    )
    preloss_supplemental_beam_width = (
        config.preloss_supplemental_beam_width
    )
    preserve_previous_direction_inertia = (
        config.preserve_previous_direction_inertia
    )
    beam_dedup_mode = config.beam_dedup_mode
    relax_stale_viability_contradiction = (
        config.relax_stale_viability_contradiction
    )

    power = objective.power
    bombs = objective.bombs
    damage_target_x = objective.damage_target_x
    damage_target_half_width = objective.damage_target_half_width
    damageable = objective.damageable

    preloss_supplemental_deadline_ms = (
        completed.supplemental_deadline_ms
    )
    preloss_supplemental_async_service = (
        completed.supplemental_async_service
    )
    preloss_supplemental_version = completed.supplemental_version
    _viability_retry = (
        request.mode is PlannerMode.RELAXED_VIABILITY
    )

    validated = preparation.validated
    target_deadline = validated.target_deadline
    repair_by_action = validated.repair_by_action
    recovery_by_action = validated.recovery_by_action
    safety_value_actions = validated.safety_value_actions
    survival_actions = validated.survival_actions
    observed_player_x = player_x
    observed_player_y = player_y
    prepared = preparation.hazards
    selected_items = prepared.selected_items
    delayed_mask = prepared.delayed_mask
    main_laser_offset = prepared.main_laser_offset
    diagnostic_losing_reserve_distance = (
        prepared.diagnostic_losing_reserve_distance
    )
    recovery_reserve_distance = prepared.recovery_reserve_distance
    certificate_horizon = prepared.certificate_horizon
    potential_threat_horizon = prepared.potential_threat_horizon
    laser_timeline = prepared.laser_timeline
    preflight = preparation.preflight
    robust_preflight_certificates = preflight.certificates
    viability_constraint_relaxed = (
        preflight.viability_constraint_relaxed
    )
    effective_allowed_first_actions = (
        preflight.effective_allowed_first_actions
    )
    viability_fresh_prefix_relaxed = (
        preflight.viability_fresh_prefix_relaxed
    )
    effective_action_names = set(effective_allowed_first_actions or ())
    preloss_continuation_preference_active = bool(
        preloss_continuation_preference
        and allowed_first_actions is not None
        and effective_action_names
        and not viability_constraint_relaxed
        and not viability_fresh_prefix_relaxed
        and effective_action_names <= repair_by_action.keys()
    )
    preloss_reserve_distance = (
        diagnostic_losing_reserve_distance
        if preloss_continuation_preference_active
        else 0.0
    )
    preloss_supplemental_beam_active = bool(
        preloss_continuation_preference_active
        and preloss_supplemental_beam_width > 0
        and not selected_items
    )
    effective_threat_horizon = potential_threat_horizon
    control_prefix_started_ns = time.perf_counter_ns()
    prefix_risk, prefix_collisions, prefix_clearance = _control_prefix_hazards(
        player_x=player_x,
        player_y=player_y,
        input_mask=delayed_mask,
        bullets=bullets,
        lasers=lasers,
        enemy_bodies=enemy_bodies,
        snapshot_lag=snapshot_lag,
        frames=control_delay_frames,
        laser_frames=laser_timeline[:control_delay_frames],
    )
    _certificate_timing_accumulator.control_prefix_ms += (
        time.perf_counter_ns() - control_prefix_started_ns
    ) / 1_000_000.0
    player_x, player_y = _project_player_for_read_lag(
        player_x,
        player_y,
        delayed_mask,
        control_delay_frames,
    )
    planning_projection_started_ns = time.perf_counter_ns()
    bullet_frames = _build_bullet_frames(
        bullets,
        horizon=effective_threat_horizon,
        snapshot_lag=max(
            0,
            control_delay_frames - max(0, snapshot_lag),
        ),
    )
    _certificate_timing_accumulator.planning_bullet_projection_ms += (
        time.perf_counter_ns() - planning_projection_started_ns
    ) / 1_000_000.0
    laser_frames = laser_timeline[
        main_laser_offset:
        main_laser_offset + effective_threat_horizon
    ]
    if len(laser_frames) < effective_threat_horizon:
        raise RuntimeError(
            "shared laser timeline does not cover local planning horizon"
        )
    neutral = _PLANNER_ACTIONS[0]
    beam = [
        SearchNode(
            player_x,
            player_y,
            neutral,
            neutral,
            prefix_risk,
            prefix_collisions,
            prefix_clearance,
            prefix_clearance,
            0,
            0.0,
        )
    ]
    initial_node = beam[0]

    def pruning_key(
        node: SearchNode,
        *,
        step: int,
    ) -> tuple[object, ...]:
        base = _node_key(
            node,
            step=step,
            selected_items=selected_items,
            target_x=target_x,
            target_y=target_y,
            target_deadline=target_deadline,
        )
        certificate = robust_preflight_certificates.get(
            node.first_action.name
        )
        return (
            base[0],
            (
                certificate.worst_collisions
                if certificate is not None
                else 0
            ),
            (
                max(-certificate.min_clearance, 0.0)
                if certificate is not None
                else 0.0
            ),
            max(-node.min_clearance, 0.0),
            (
                0
                if (
                    not survival_actions
                    or node.first_action.name in survival_actions
                )
                else 1
            ),
            base[1],
            base[2],
            (
                0
                if (
                    not safety_value_actions
                    or node.first_action.name in safety_value_actions
                )
                else 1
            ),
            _boundary_control_reserve_deficit(
                node.x,
                node.y,
                reserve_distance=recovery_reserve_distance,
            ),
            recovery_by_action.get(node.first_action.name, math.inf),
            *base[3:],
        )

    if (
        not bullets
        and not lasers
        and not enemy_bodies
        and not selected_items
        and target_x is None
        and allowed_first_actions is None
        and not repair_by_action
        and not recovery_by_action
        and not safety_value_actions
        and not survival_actions
    ):
        return Decision(
            SHOT | FOCUS,
            "stay",
            9999.0,
            9999.0,
            0.0,
            False,
            robust_delay_frames=control_delay_candidates or (),
            local_certificate_timing=(
                _certificate_timing_accumulator.snapshot()
            ),
        )
    native_beam_enabled = (
        _LOCAL_BEAM_REDUCER == "native"
        and beam_dedup_mode == "quantized"
        and not selected_items
    )
    planner_action_indices: dict[str, int] = {}
    native_certificate_collisions = np.empty(0, dtype=np.int32)
    native_certificate_minimum = np.empty(0, dtype=np.float64)
    native_survival_preferred = np.empty(0, dtype=np.uint8)
    native_safety_preferred = np.empty(0, dtype=np.uint8)
    native_recovery_distance = np.empty(0, dtype=np.float64)
    if native_beam_enabled:
        planner_action_indices = {
            action.name: index
            for index, action in enumerate(_PLANNER_ACTIONS)
        }
        native_certificate_collisions = np.fromiter(
            (
                robust_preflight_certificates[
                    action.name
                ].worst_collisions
                if action.name in robust_preflight_certificates
                else 0
                for action in _PLANNER_ACTIONS
            ),
            dtype=np.int32,
            count=len(_PLANNER_ACTIONS),
        )
        native_certificate_minimum = np.fromiter(
            (
                robust_preflight_certificates[
                    action.name
                ].min_clearance
                if action.name in robust_preflight_certificates
                else 0.0
                for action in _PLANNER_ACTIONS
            ),
            dtype=np.float64,
            count=len(_PLANNER_ACTIONS),
        )
        native_survival_preferred = np.fromiter(
            (
                not survival_actions or action.name in survival_actions
                for action in _PLANNER_ACTIONS
            ),
            dtype=np.uint8,
            count=len(_PLANNER_ACTIONS),
        )
        native_safety_preferred = np.fromiter(
            (
                not safety_value_actions
                or action.name in safety_value_actions
                for action in _PLANNER_ACTIONS
            ),
            dtype=np.uint8,
            count=len(_PLANNER_ACTIONS),
        )
        native_recovery_distance = np.fromiter(
            (
                recovery_by_action.get(action.name, math.inf)
                for action in _PLANNER_ACTIONS
            ),
            dtype=np.float64,
            count=len(_PLANNER_ACTIONS),
        )
    presubmitted_async_identity: tuple[object, ...] | None = None
    if (
        preloss_supplemental_beam_active
        and preloss_supplemental_async_service is not None
        and _LOCAL_SUPPLEMENTAL_BACKEND == "native"
        and native_beam_enabled
    ):
        async_submit_started_ns = time.perf_counter_ns()
        async_actions = tuple(
            SupplementalAction(
                name=action.name,
                direction=action.direction,
                dx=action.dx,
                dy=action.dy,
                focused=action.focused,
            )
            for action in _PLANNER_ACTIONS
        )
        async_repair_volume = np.fromiter(
            (
                repair_by_action.get(action.name, 0)
                for action in _PLANNER_ACTIONS
            ),
            dtype=np.int32,
            count=len(_PLANNER_ACTIONS),
        )
        body_base_x = np.fromiter(
            (body.x for body in enemy_bodies),
            dtype=np.float32,
            count=len(enemy_bodies),
        )
        body_base_y = np.fromiter(
            (body.y for body in enemy_bodies),
            dtype=np.float32,
            count=len(enemy_bodies),
        )
        body_velocity_x = np.fromiter(
            (body.vx for body in enemy_bodies),
            dtype=np.float32,
            count=len(enemy_bodies),
        )
        body_velocity_y = np.fromiter(
            (body.vy for body in enemy_bodies),
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
        async_absolute_deadline_ns = (
            None
            if preloss_supplemental_deadline_ms is None
            else async_submit_started_ns
            + int(preloss_supplemental_deadline_ms * 1_000_000.0)
        )
        async_native_job = functools.partial(
            search_supplemental_local_beam_native,
            initial=SupplementalNode(
                x=initial_node.x,
                y=initial_node.y,
                first_action=0,
                last_action=0,
                risk=initial_node.risk,
                collisions=initial_node.collisions,
                min_clearance=initial_node.min_clearance,
                immediate_clearance=initial_node.immediate_clearance,
            ),
            actions=async_actions,
            allowed_first_actions=frozenset(
                effective_allowed_first_actions or ()
            ),
            action_hold_frames=action_hold_frames,
            horizon=horizon,
            beam_width=preloss_supplemental_beam_width,
            bullet_frames=bullet_frames[:horizon],
            laser_frames=tuple(
                frame.fields_for_native()
                for frame in laser_frames[:horizon]
            ),
            body_base_x=body_base_x,
            body_base_y=body_base_y,
            body_velocity_x=body_velocity_x,
            body_velocity_y=body_velocity_y,
            body_half_width=body_half_width,
            body_half_height=body_half_height,
            player_radius=PLAYER_RADIUS,
            control_delay_frames=control_delay_frames,
            previous_direction=previous_direction,
            previous_focused=previous_focus,
            preserve_previous_direction_inertia=(
                preserve_previous_direction_inertia
            ),
            target_x=target_x,
            target_y=target_y,
            target_deadline=target_deadline,
            item_safety_clearance=ITEM_SAFETY_CLEARANCE,
            playfield_left=PLAYFIELD_LEFT,
            playfield_right=PLAYFIELD_RIGHT,
            playfield_top=PLAYFIELD_TOP,
            playfield_bottom=PLAYFIELD_BOTTOM,
            recovery_reserve_distance=recovery_reserve_distance,
            supplemental_reserve_distance=preloss_reserve_distance,
            diagonal_speed=UNFOCUSED_DIAGONAL_SPEED,
            cardinal_speed=UNFOCUSED_CARDINAL_SPEED,
            certificate_collisions=native_certificate_collisions,
            certificate_minimum=native_certificate_minimum,
            survival_preferred=native_survival_preferred,
            safety_preferred=native_safety_preferred,
            recovery_distance=native_recovery_distance,
            repair_volume=async_repair_volume,
            absolute_deadline_ns=async_absolute_deadline_ns,
        )
        presubmitted_async_identity = (
            preloss_supplemental_version,
            local_pipeline_root,
            float(player_x).hex(),
            float(player_y).hex(),
            previous_direction,
            previous_focus,
            control_delay_frames,
            control_delay_candidates,
            action_hold_frames,
            horizon,
            preloss_supplemental_beam_width,
            beam_dedup_mode,
            target_x,
            target_y,
            target_deadline,
            tuple(effective_allowed_first_actions or ()),
            tuple(viability_repair_volumes),
            tuple(viability_recovery_distances),
            tuple(viability_safety_actions),
            tuple(viability_survival_actions),
        )
        preloss_supplemental_async_service.submit(
            presubmitted_async_identity,
            lambda workspace: async_native_job(workspace=workspace),
        )
        time.sleep(0)
        _certificate_timing_accumulator.supplemental_beam_ms += (
            time.perf_counter_ns() - async_submit_started_ns
        ) / 1_000_000.0
    beam_started_ns = time.perf_counter_ns()
    beam = run_baseline_beam(
        BaselineBeamContext(
            initial_beam=tuple(beam),
            actions=_PLANNER_ACTIONS,
            action_hold_frames=action_hold_frames,
            horizon=horizon,
            effective_allowed_first_actions=(
                effective_allowed_first_actions
            ),
            preserve_previous_direction_inertia=(
                preserve_previous_direction_inertia
            ),
            previous_direction=previous_direction,
            previous_focus=previous_focus,
            selected_items=selected_items,
            control_delay_frames=control_delay_frames,
            bullet_frames=bullet_frames,
            laser_frames=laser_frames,
            enemy_bodies=enemy_bodies,
            native_beam_enabled=native_beam_enabled,
            planner_action_indices=planner_action_indices,
            native_certificate_collisions=(
                native_certificate_collisions
            ),
            native_certificate_minimum=native_certificate_minimum,
            native_survival_preferred=native_survival_preferred,
            native_safety_preferred=native_safety_preferred,
            native_recovery_distance=native_recovery_distance,
            beam_width=beam_width,
            beam_dedup_mode=beam_dedup_mode,
            target_x=target_x,
            target_y=target_y,
            target_deadline=target_deadline,
            item_safety_clearance=ITEM_SAFETY_CLEARANCE,
            collection_half_width=COLLECTION_HALF_WIDTH,
            playfield_left=PLAYFIELD_LEFT,
            playfield_right=PLAYFIELD_RIGHT,
            playfield_top=PLAYFIELD_TOP,
            playfield_bottom=PLAYFIELD_BOTTOM,
            recovery_reserve_distance=recovery_reserve_distance,
            diagonal_speed=UNFOCUSED_DIAGONAL_SPEED,
            cardinal_speed=UNFOCUSED_CARDINAL_SPEED,
        ),
        boundary_risk=_boundary_risk,
        directions_opposed=_directions_opposed,
        project_item=_project_item,
        hazard_query=_hazards_for_positions,
        pruning_key=pruning_key,
        native_reducer=native_backend.reduce_local_beam,
    )

    supplemental_beam: list[SearchNode] = []
    supplemental_failure: str | None = None
    supplemental_status = (
        "not_eligible"
        if not preloss_supplemental_beam_active
        else "pending"
    )
    supplemental_completed = False
    supplemental_historical_fallback = False
    supplemental_async_identity = presubmitted_async_identity
    supplemental_background_compute_ms: float | None = None
    supplemental_published_terminal_labels: (
        tuple[tuple[int, float], ...] | None
    ) = None
    if (
        preloss_supplemental_beam_active
        and presubmitted_async_identity is not None
    ):
        supplemental_status = "async_submitted"
        supplemental_historical_fallback = True
    elif preloss_supplemental_beam_active:
        supplemental_started_ns = time.perf_counter_ns()
        supplemental_actions = tuple(
            SupplementalAction(
                name=action.name,
                direction=action.direction,
                dx=action.dx,
                dy=action.dy,
                focused=action.focused,
            )
            for action in _PLANNER_ACTIONS
        )

        def supplemental_transition_risk(
            node: SupplementalNode,
            action: SupplementalAction,
            x: float,
            y: float,
            step: int,
        ) -> float:
            last_action = supplemental_actions[node.last_action]
            risk = _boundary_risk(x, y)
            if action.direction != last_action.direction:
                risk += 0.08
            if _directions_opposed(
                action.direction,
                last_action.direction,
            ):
                risk += 24.0
            if action.focused != last_action.focused:
                risk += 0.12
            if step == 1 and preserve_previous_direction_inertia:
                if action.direction != previous_direction:
                    risk += 0.08
                if _directions_opposed(
                    action.direction,
                    previous_direction,
                ):
                    risk += 24.0
                if action.focused != previous_focus:
                    risk += 0.12
            return risk

        def supplemental_hazard_query(
            positions_x: np.ndarray,
            positions_y: np.ndarray,
            absolute_step: int,
        ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
            local_step = absolute_step - control_delay_frames
            return _hazards_for_positions(
                positions_x,
                positions_y,
                step=absolute_step,
                bullet_frame=bullet_frames[local_step - 1],
                lasers=laser_frames[local_step - 1],
                enemy_bodies=enemy_bodies,
            )

        initial_supplemental = SupplementalNode(
            x=initial_node.x,
            y=initial_node.y,
            first_action=0,
            last_action=0,
            risk=initial_node.risk,
            collisions=initial_node.collisions,
            min_clearance=initial_node.min_clearance,
            immediate_clearance=initial_node.immediate_clearance,
        )
        certificate_collisions = np.fromiter(
            (
                robust_preflight_certificates[
                    action.name
                ].worst_collisions
                if action.name in robust_preflight_certificates
                else 0
                for action in _PLANNER_ACTIONS
            ),
            dtype=np.int32,
            count=len(_PLANNER_ACTIONS),
        )
        certificate_minimum = np.fromiter(
            (
                robust_preflight_certificates[
                    action.name
                ].min_clearance
                if action.name in robust_preflight_certificates
                else 0.0
                for action in _PLANNER_ACTIONS
            ),
            dtype=np.float64,
            count=len(_PLANNER_ACTIONS),
        )
        survival_preferred = np.fromiter(
            (
                not survival_actions
                or action.name in survival_actions
                for action in _PLANNER_ACTIONS
            ),
            dtype=np.uint8,
            count=len(_PLANNER_ACTIONS),
        )
        safety_preferred = np.fromiter(
            (
                not safety_value_actions
                or action.name in safety_value_actions
                for action in _PLANNER_ACTIONS
            ),
            dtype=np.uint8,
            count=len(_PLANNER_ACTIONS),
        )
        recovery_distance = np.fromiter(
            (
                recovery_by_action.get(action.name, math.inf)
                for action in _PLANNER_ACTIONS
            ),
            dtype=np.float64,
            count=len(_PLANNER_ACTIONS),
        )
        repair_volume = np.fromiter(
            (
                repair_by_action.get(action.name, 0)
                for action in _PLANNER_ACTIONS
            ),
            dtype=np.int32,
            count=len(_PLANNER_ACTIONS),
        )
        absolute_supplemental_deadline_ns = (
            None
            if preloss_supplemental_deadline_ms is None
            else supplemental_started_ns
            + int(preloss_supplemental_deadline_ms * 1_000_000.0)
        )
        try:
            if (
                _LOCAL_SUPPLEMENTAL_BACKEND == "native"
                and beam_dedup_mode == "quantized"
            ):
                native_job = functools.partial(
                    search_supplemental_local_beam_native,
                    initial=initial_supplemental,
                    actions=supplemental_actions,
                    allowed_first_actions=frozenset(
                        effective_allowed_first_actions or ()
                    ),
                    action_hold_frames=action_hold_frames,
                    horizon=horizon,
                    beam_width=preloss_supplemental_beam_width,
                    bullet_frames=bullet_frames[:horizon],
                    laser_frames=tuple(
                        frame.fields_for_native()
                        for frame in laser_frames[:horizon]
                    ),
                    body_base_x=np.fromiter(
                        (body.x for body in enemy_bodies),
                        dtype=np.float32,
                        count=len(enemy_bodies),
                    ),
                    body_base_y=np.fromiter(
                        (body.y for body in enemy_bodies),
                        dtype=np.float32,
                        count=len(enemy_bodies),
                    ),
                    body_velocity_x=np.fromiter(
                        (body.vx for body in enemy_bodies),
                        dtype=np.float32,
                        count=len(enemy_bodies),
                    ),
                    body_velocity_y=np.fromiter(
                        (body.vy for body in enemy_bodies),
                        dtype=np.float32,
                        count=len(enemy_bodies),
                    ),
                    body_half_width=np.fromiter(
                        (
                            body.half_width + body.uncertainty
                            for body in enemy_bodies
                        ),
                        dtype=np.float32,
                        count=len(enemy_bodies),
                    ),
                    body_half_height=np.fromiter(
                        (
                            body.half_height + body.uncertainty
                            for body in enemy_bodies
                        ),
                        dtype=np.float32,
                        count=len(enemy_bodies),
                    ),
                    player_radius=PLAYER_RADIUS,
                    control_delay_frames=control_delay_frames,
                    previous_direction=previous_direction,
                    previous_focused=previous_focus,
                    preserve_previous_direction_inertia=(
                        preserve_previous_direction_inertia
                    ),
                    target_x=target_x,
                    target_y=target_y,
                    target_deadline=target_deadline,
                    item_safety_clearance=ITEM_SAFETY_CLEARANCE,
                    playfield_left=PLAYFIELD_LEFT,
                    playfield_right=PLAYFIELD_RIGHT,
                    playfield_top=PLAYFIELD_TOP,
                    playfield_bottom=PLAYFIELD_BOTTOM,
                    recovery_reserve_distance=(
                        recovery_reserve_distance
                    ),
                    supplemental_reserve_distance=(
                        preloss_reserve_distance
                    ),
                    diagonal_speed=UNFOCUSED_DIAGONAL_SPEED,
                    cardinal_speed=UNFOCUSED_CARDINAL_SPEED,
                    certificate_collisions=certificate_collisions,
                    certificate_minimum=certificate_minimum,
                    survival_preferred=survival_preferred,
                    safety_preferred=safety_preferred,
                    recovery_distance=recovery_distance,
                    repair_volume=repair_volume,
                    absolute_deadline_ns=(
                        absolute_supplemental_deadline_ns
                    ),
                )
                if preloss_supplemental_async_service is not None:
                    supplemental_async_identity = (
                        preloss_supplemental_version,
                        local_pipeline_root,
                        float(player_x).hex(),
                        float(player_y).hex(),
                        previous_direction,
                        previous_focus,
                        control_delay_frames,
                        control_delay_candidates,
                        action_hold_frames,
                        horizon,
                        preloss_supplemental_beam_width,
                        beam_dedup_mode,
                        target_x,
                        target_y,
                        target_deadline,
                        tuple(effective_allowed_first_actions or ()),
                        tuple(viability_repair_volumes),
                        tuple(viability_recovery_distances),
                        tuple(viability_safety_actions),
                        tuple(viability_survival_actions),
                    )
                    preloss_supplemental_async_service.submit(
                        supplemental_async_identity,
                        lambda workspace: native_job(
                            workspace=workspace
                        ),
                    )
                    # Give the dedicated newest-wins worker one scheduling
                    # opportunity; the consumer still performs lookup-only
                    # publication with no completion wait.
                    time.sleep(0)
                    lane_nodes = []
                    supplemental_status = "async_submitted"
                    supplemental_historical_fallback = True
                else:
                    lane_nodes = native_job()
            else:
                lane_nodes = search_supplemental_local_beam(
                    initial=initial_supplemental,
                    actions=supplemental_actions,
                    allowed_first_actions=frozenset(
                        effective_allowed_first_actions or ()
                    ),
                    action_hold_frames=action_hold_frames,
                    horizon=horizon,
                    beam_width=preloss_supplemental_beam_width,
                    beam_dedup_mode=beam_dedup_mode,
                    hazard_query=supplemental_hazard_query,
                    transition_risk=supplemental_transition_risk,
                    control_delay_frames=control_delay_frames,
                    target_x=target_x,
                    target_y=target_y,
                    target_deadline=target_deadline,
                    item_safety_clearance=ITEM_SAFETY_CLEARANCE,
                    playfield_left=PLAYFIELD_LEFT,
                    playfield_right=PLAYFIELD_RIGHT,
                    playfield_top=PLAYFIELD_TOP,
                    playfield_bottom=PLAYFIELD_BOTTOM,
                    recovery_reserve_distance=(
                        recovery_reserve_distance
                    ),
                    supplemental_reserve_distance=(
                        preloss_reserve_distance
                    ),
                    diagonal_speed=UNFOCUSED_DIAGONAL_SPEED,
                    cardinal_speed=UNFOCUSED_CARDINAL_SPEED,
                    certificate_collisions=certificate_collisions,
                    certificate_minimum=certificate_minimum,
                    survival_preferred=survival_preferred,
                    safety_preferred=safety_preferred,
                    recovery_distance=recovery_distance,
                    repair_volume=repair_volume,
                    use_native_reducer=native_beam_enabled,
                )
            if supplemental_status != "async_submitted":
                supplemental_status = "completed"
                supplemental_completed = True
            supplemental_beam = [
                SearchNode(
                    x=node.x,
                    y=node.y,
                    first_action=_PLANNER_ACTIONS[
                        node.first_action
                    ],
                    last_action=_PLANNER_ACTIONS[node.last_action],
                    risk=node.risk,
                    collisions=node.collisions,
                    min_clearance=node.min_clearance,
                    immediate_clearance=node.immediate_clearance,
                    collected_mask=0,
                    item_utility=0.0,
                )
                for node in lane_nodes
            ]
        except native_backend.LocalSupplementalNativeDeadlineError:
            supplemental_beam = []
            supplemental_status = "deadline"
            supplemental_historical_fallback = True
        except native_backend.LocalSupplementalNativeCancelledError:
            supplemental_beam = []
            supplemental_status = "cancelled"
            supplemental_historical_fallback = True
        except Exception as error:
            supplemental_beam = []
            supplemental_status = "error"
            supplemental_historical_fallback = True
            supplemental_failure = (
                f"{type(error).__name__}: {error}"
            )
        finally:
            _certificate_timing_accumulator.supplemental_beam_ms += (
                time.perf_counter_ns() - supplemental_started_ns
            ) / 1_000_000.0
    if supplemental_failure is not None:
        preloss_continuation_preference_active = False
        preloss_supplemental_beam_active = False

    if not beam:
        beam = [
            SearchNode(
                player_x,
                player_y,
                neutral,
                neutral,
                1e12,
                1,
                -9999.0,
                -9999.0,
                0,
                0.0,
            )
        ]
    supplemental_source_ids = {id(node) for node in supplemental_beam}
    for index, node in enumerate(beam):
        if target_x is None or target_y is None:
            position_cost = (
                ((node.x - 192.0) / 96.0) ** 2
                + ((node.y - 400.0) / 128.0) ** 2
            )
        else:
            position_cost = 0.25 * (
                ((node.x - target_x) / 8.0) ** 2
                + ((node.y - target_y) / 8.0) ** 2
            )
        beam[index] = replace(node, risk=node.risk + position_cost)
    async_terminal_started_ns: int | None = None
    terminal_threats: dict[SearchNode, tuple[int, float]] = {}
    if supplemental_async_identity is not None:
        assert preloss_supplemental_async_service is not None
        async_terminal_started_ns = time.perf_counter_ns()
        terminal_threats.update(
            _terminal_threat_scores(
                beam,
                start_step=horizon,
                end_step=effective_threat_horizon,
                control_delay_frames=control_delay_frames,
                bullet_frames=bullet_frames,
                laser_frames=laser_frames,
                enemy_bodies=enemy_bodies,
            )
        )
        completed_lookup: CompletedSupplementalLookup = (
            lookup_completed_supplemental(
                service=preloss_supplemental_async_service,
                identity=supplemental_async_identity,
                actions=_PLANNER_ACTIONS,
            )
        )
        supplemental_status = completed_lookup.status
        supplemental_completed = completed_lookup.completed
        supplemental_historical_fallback = (
            completed_lookup.historical_fallback
        )
        supplemental_background_compute_ms = (
            completed_lookup.background_compute_ms
        )
        supplemental_published_terminal_labels = (
            completed_lookup.terminal_labels
        )
        supplemental_beam = list(completed_lookup.beam)
    for index, node in enumerate(supplemental_beam):
        if target_x is None or target_y is None:
            position_cost = (
                ((node.x - 192.0) / 96.0) ** 2
                + ((node.y - 400.0) / 128.0) ** 2
            )
        else:
            position_cost = 0.25 * (
                ((node.x - target_x) / 8.0) ** 2
                + ((node.y - target_y) / 8.0) ** 2
            )
        replaced_node = replace(node, risk=node.risk + position_cost)
        supplemental_source_ids.discard(id(node))
        supplemental_source_ids.add(id(replaced_node))
        supplemental_beam[index] = replaced_node
    if supplemental_published_terminal_labels is not None:
        if (
            len(supplemental_published_terminal_labels)
            != len(supplemental_beam)
        ):
            supplemental_failure = (
                "RuntimeError: async terminal publication count mismatch"
            )
            supplemental_status = "error"
            supplemental_completed = False
            supplemental_historical_fallback = True
            supplemental_beam = []
            supplemental_source_ids.clear()
        else:
            terminal_threats.update(
                zip(
                    supplemental_beam,
                    supplemental_published_terminal_labels,
                )
            )
    _certificate_timing_accumulator.beam_search_ms += (
        time.perf_counter_ns() - beam_started_ns
    ) / 1_000_000.0
    terminal_threat_started_ns = (
        async_terminal_started_ns
        if async_terminal_started_ns is not None
        else time.perf_counter_ns()
    )
    endpoint_pool = [*beam, *supplemental_beam]
    if async_terminal_started_ns is None:
        terminal_threats = _terminal_threat_scores(
            endpoint_pool,
            start_step=horizon,
            end_step=effective_threat_horizon,
            control_delay_frames=control_delay_frames,
            bullet_frames=bullet_frames,
            laser_frames=laser_frames,
            enemy_bodies=enemy_bodies,
        )
    elif (
        supplemental_beam
        and supplemental_published_terminal_labels is None
    ):
        terminal_threats.update(
            _terminal_threat_scores(
                supplemental_beam,
                start_step=horizon,
                end_step=effective_threat_horizon,
                control_delay_frames=control_delay_frames,
                bullet_frames=bullet_frames,
                laser_frames=laser_frames,
                enemy_bodies=enemy_bodies,
            )
        )
    _certificate_timing_accumulator.terminal_threat_ms += (
        time.perf_counter_ns() - terminal_threat_started_ns
    ) / 1_000_000.0
    selection_started_ns = time.perf_counter_ns()
    endpoint_ranker = EndpointRanker(
        terminal_threats=terminal_threats,
        survival_actions=survival_actions,
        safety_value_actions=safety_value_actions,
        recovery_by_action=recovery_by_action,
        repair_by_action=repair_by_action,
        recovery_reserve_distance=recovery_reserve_distance,
        preloss_reserve_distance=preloss_reserve_distance,
        preloss_continuation_preference_active=(
            preloss_continuation_preference_active
        ),
        item_safety_clearance=ITEM_SAFETY_CLEARANCE,
        horizon=horizon,
        selected_items=selected_items,
        target_x=target_x,
        target_y=target_y,
        target_deadline=target_deadline,
        boundary_control_reserve_deficit=(
            _boundary_control_reserve_deficit
        ),
        node_key=_node_key,
        minimum_travel_frames=_minimum_travel_frames,
    )
    historical_selection_key = endpoint_ranker.historical_key
    selection_key = endpoint_ranker.selection_key
    route_gate_deficit = endpoint_ranker.route_gate_deficit

    robust_certificates: dict[str, RobustActionCertificate] = {}
    nodes_by_action: dict[str, SearchNode] = {}
    robust_override = False
    robust_certificate: RobustActionCertificate | None = None
    historical_best = min(beam, key=historical_selection_key)
    historical_route_gate_deficit = route_gate_deficit(historical_best)
    preloss_selected_from_supplemental = False
    preloss_candidate_count = 0

    if preloss_continuation_preference_active:
        actions_by_name: dict[str, PlannerAction] = {}
        for node in endpoint_pool:
            action_name = node.first_action.name
            actions_by_name[action_name] = node.first_action
        if control_delay_candidates is not None:
            if actions_by_name.keys() <= robust_preflight_certificates.keys():
                robust_certificates = {
                    action_name: robust_preflight_certificates[action_name]
                    for action_name in actions_by_name
                }
            else:
                robust_certificates = _robust_action_certificates(
                    player_x=observed_player_x,
                    player_y=observed_player_y,
                    previous_mask=delayed_mask,
                    actions=tuple(actions_by_name.values()),
                    delay_frames=control_delay_candidates,
                    action_hold_frames=action_hold_frames,
                    bullets=bullets,
                    lasers=lasers,
                    enemy_bodies=enemy_bodies,
                    snapshot_lag=snapshot_lag,
                    laser_frames=laser_timeline[:certificate_horizon],
                    pipeline_root=local_pipeline_root,
                    timing_accumulator=_certificate_timing_accumulator,
                )

        historical_nodes_by_action: dict[str, SearchNode] = {}
        for node in beam:
            action_name = node.first_action.name
            incumbent = historical_nodes_by_action.get(action_name)
            if (
                incumbent is None
                or historical_selection_key(node)
                < historical_selection_key(incumbent)
            ):
                historical_nodes_by_action[action_name] = node
        historical_provisional = historical_best
        if robust_certificates:
            nominal_certificate = robust_certificates[
                historical_best.first_action.name
            ]
            if (
                nominal_certificate.worst_collisions > 0
                or nominal_certificate.min_clearance < 0.0
            ):
                historical_best = min(
                    historical_nodes_by_action.values(),
                    key=lambda node: (
                        robust_certificates[
                            node.first_action.name
                        ].worst_collisions,
                        max(
                            -robust_certificates[
                                node.first_action.name
                            ].min_clearance,
                            0.0,
                        ),
                        robust_certificates[
                            node.first_action.name
                        ].cvar_risk,
                        -robust_certificates[
                            node.first_action.name
                        ].min_clearance,
                        historical_selection_key(node),
                    ),
                )
                robust_override = (
                    historical_best.first_action
                    != historical_provisional.first_action
                )
        historical_route_gate_deficit = route_gate_deficit(
            historical_best
        )

        def hard_components(node: SearchNode) -> tuple[int | float, ...]:
            threat_collisions, threat_clearance = terminal_threats[node]
            certificate = robust_certificates.get(
                node.first_action.name
            )
            return (
                (
                    certificate.worst_collisions
                    if certificate is not None
                    else 0
                ),
                (
                    max(-certificate.min_clearance, 0.0)
                    if certificate is not None
                    else 0.0
                ),
                node.collisions,
                max(-node.min_clearance, 0.0),
                threat_collisions,
                max(-threat_clearance, 0.0),
            )

        historical_hard = hard_components(historical_best)
        historical_survival_deficit = (
            0
            if (
                not survival_actions
                or historical_best.first_action.name in survival_actions
            )
            else 1
        )
        historical_continuation_key = (
            -repair_by_action.get(
                historical_best.first_action.name,
                0,
            ),
            _boundary_control_reserve_deficit(
                historical_best.x,
                historical_best.y,
                reserve_distance=preloss_reserve_distance,
            ),
        )
        effective_set = set(effective_allowed_first_actions or ())
        admitted: list[SearchNode] = []
        for node in endpoint_pool:
            node_hard = hard_components(node)
            if not all(
                candidate <= incumbent
                for candidate, incumbent in zip(
                    node_hard,
                    historical_hard,
                )
            ):
                continue
            if (
                route_gate_deficit(node)
                > historical_route_gate_deficit
            ):
                continue
            if (
                effective_set
                and node.first_action.name not in effective_set
            ):
                continue
            survival_deficit = (
                0
                if (
                    not survival_actions
                    or node.first_action.name in survival_actions
                )
                else 1
            )
            if survival_deficit > historical_survival_deficit:
                continue
            continuation_key = (
                -repair_by_action.get(node.first_action.name, 0),
                _boundary_control_reserve_deficit(
                    node.x,
                    node.y,
                    reserve_distance=preloss_reserve_distance,
                ),
            )
            if continuation_key >= historical_continuation_key:
                continue
            admitted.append(node)
        preloss_candidate_count = len(admitted)
        best = (
            min(
                admitted,
                key=lambda node: (
                    hard_components(node),
                    (
                        0
                        if (
                            not survival_actions
                            or node.first_action.name
                            in survival_actions
                        )
                        else 1
                    ),
                    -repair_by_action.get(
                        node.first_action.name,
                        0,
                    ),
                    _boundary_control_reserve_deficit(
                        node.x,
                        node.y,
                        reserve_distance=preloss_reserve_distance,
                    ),
                    historical_selection_key(node),
                ),
            )
            if admitted
            else historical_best
        )
        preloss_selected_from_supplemental = (
            id(best) in supplemental_source_ids
        )
        for node in endpoint_pool:
            action_name = node.first_action.name
            incumbent = nodes_by_action.get(action_name)
            if (
                incumbent is None
                or selection_key(node) < selection_key(incumbent)
            ):
                nodes_by_action[action_name] = node
        robust_certificate = robust_certificates.get(
            best.first_action.name
        )
    else:
        best = min(beam, key=selection_key)
        if control_delay_candidates is not None:
            actions_by_name: dict[str, PlannerAction] = {}
            for node in beam:
                action_name = node.first_action.name
                actions_by_name[action_name] = node.first_action
                incumbent = nodes_by_action.get(action_name)
                if incumbent is None or selection_key(
                    node
                ) < selection_key(incumbent):
                    nodes_by_action[action_name] = node
            if actions_by_name.keys() <= (
                robust_preflight_certificates.keys()
            ):
                robust_certificates = {
                    action_name: robust_preflight_certificates[action_name]
                    for action_name in actions_by_name
                }
            else:
                robust_certificates = _robust_action_certificates(
                    player_x=observed_player_x,
                    player_y=observed_player_y,
                    previous_mask=delayed_mask,
                    actions=tuple(actions_by_name.values()),
                    delay_frames=control_delay_candidates,
                    action_hold_frames=action_hold_frames,
                    bullets=bullets,
                    lasers=lasers,
                    enemy_bodies=enemy_bodies,
                    snapshot_lag=snapshot_lag,
                    laser_frames=laser_timeline[:certificate_horizon],
                    pipeline_root=local_pipeline_root,
                    timing_accumulator=_certificate_timing_accumulator,
                )
            nominal_certificate = robust_certificates[
                best.first_action.name
            ]
            if (
                nominal_certificate.worst_collisions > 0
                or nominal_certificate.min_clearance < 0.0
            ):
                robust_best = min(
                    nodes_by_action.values(),
                    key=lambda node: (
                        robust_certificates[
                            node.first_action.name
                        ].worst_collisions,
                        max(
                            -robust_certificates[
                                node.first_action.name
                            ].min_clearance,
                            0.0,
                        ),
                        robust_certificates[
                            node.first_action.name
                        ].cvar_risk,
                        -robust_certificates[
                            node.first_action.name
                        ].min_clearance,
                        selection_key(node),
                    ),
                )
                robust_override = (
                    robust_best.first_action != best.first_action
                )
                best = robust_best
            robust_certificate = robust_certificates[
                best.first_action.name
            ]
    damage_reason = "boss_not_damageable"
    if damageable:
        damage_reason = "boss_geometry_unavailable"
    if damageable and damage_target_x is not None:
        damage_reason = "fresh_viability_unavailable"
    if (
        damageable
        and damage_target_x is not None
        and effective_allowed_first_actions is not None
    ):
        damage_reason = (
            "viability_constraint_relaxed"
            if viability_fresh_prefix_relaxed
            else "issue_certificate_unavailable"
        )
    damage_shadow_action: str | None = None
    damage_baseline_action = best.first_action.name
    damage_current_alignment_cost: float | None = None
    damage_shadow_alignment_cost: float | None = None
    damage_eligible_action_count = 0
    damage_objective_available = bool(
        damageable
        and damage_target_x is not None
        and effective_allowed_first_actions is not None
        and not viability_fresh_prefix_relaxed
        and robust_certificates
        and nodes_by_action
    )
    if damage_objective_available:
        viable_actions = set(effective_allowed_first_actions or ())
        progress_candidates = tuple(
            ProgressCandidate(
                action=action_name,
                progress_cost=max(
                    abs(node.x - damage_target_x)
                    - damage_target_half_width,
                    0.0,
                ),
                viable=action_name in viable_actions,
                issue_collisions=robust_certificates[
                    action_name
                ].worst_collisions,
                issue_min_clearance=robust_certificates[
                    action_name
                ].min_clearance,
                baseline_rank=selection_key(node),
            )
            for action_name, node in nodes_by_action.items()
        )
        damage_eligible_action_count = sum(
            candidate.viable
            and candidate.issue_collisions == 0
            and candidate.issue_min_clearance >= 0.0
            for candidate in progress_candidates
        )
        damage_candidate = select_progress_action(progress_candidates)
        if damage_candidate is None:
            damage_objective_available = False
            damage_reason = "no_issue_safe_viable_action"
        else:
            damage_reason = "shadow_lexicographic_tiebreak"
            damage_shadow_action = damage_candidate.action
            damage_current_alignment_cost = max(
                abs(best.x - damage_target_x) - damage_target_half_width,
                0.0,
            )
            damage_shadow_alignment_cost = damage_candidate.progress_cost
    threat_collisions, threat_clearance = terminal_threats[best]
    decision = assemble_local_decision(
        ProposalAssemblyContext(
            request=request,
            validated=validated,
            prepared=prepared,
            preflight=preflight,
            best=best,
            robust_certificate=robust_certificate,
            robust_override=robust_override,
            terminal_threat=(threat_collisions, threat_clearance),
            prefix_clearance=prefix_clearance,
            damage=DamageDecisionFields(
                available=damage_objective_available,
                baseline_action=damage_baseline_action,
                shadow_action=damage_shadow_action,
                current_alignment_cost=damage_current_alignment_cost,
                shadow_alignment_cost=damage_shadow_alignment_cost,
                eligible_action_count=damage_eligible_action_count,
                reason=damage_reason,
            ),
            supplemental=SupplementalDecisionFields(
                active=preloss_supplemental_beam_active,
                selected_from_supplemental=(
                    preloss_selected_from_supplemental
                ),
                candidate_count=preloss_candidate_count,
                failure=supplemental_failure,
                backend=(
                    "exact_async_native"
                    if preloss_supplemental_async_service is not None
                    else _LOCAL_SUPPLEMENTAL_BACKEND
                ),
                status=supplemental_status,
                completed=supplemental_completed,
                historical_fallback=(
                    supplemental_historical_fallback
                ),
                background_compute_ms=(
                    supplemental_background_compute_ms
                ),
                historical_action=(
                    historical_best.first_action.name
                    if preloss_continuation_preference_active
                    else None
                ),
                historical_route_gate_deficit=(
                    historical_route_gate_deficit
                ),
            ),
            route_gate_deficit=route_gate_deficit(best),
            local_collisions=best.collisions,
        ),
        actions=_PLANNER_ACTIONS,
        shot_mask=SHOT,
        focus_mask=FOCUS,
        bomb_mask=BOMB,
        boundary_control_reserve_deficit=(
            _boundary_control_reserve_deficit
        ),
    )
    _certificate_timing_accumulator.selection_finalize_ms += (
        time.perf_counter_ns() - selection_started_ns
    ) / 1_000_000.0
    if (
        effective_allowed_first_actions is not None
        and effective_threat_horizon > horizon
        and (
            threat_collisions > 0
            or decision.robust_collisions > 0
            or decision.min_clearance <= 0.0
        )
        and relax_stale_viability_contradiction
        and not _viability_retry
    ):
        return _PlannerModeTransition(
            current_decision=decision,
            next_request=replace(
                request,
                physical=replace(
                    physical,
                    player_x=observed_player_x,
                    player_y=observed_player_y,
                ),
                guidance=replace(
                    guidance,
                    allowed_first_actions=None,
                ),
                # Preserve the historical retry contract: damage guidance was
                # not forwarded into the relaxed pass.
                objective=ObjectiveContext(
                    power=power,
                    bombs=bombs,
                ),
                mode=PlannerMode.RELAXED_VIABILITY,
            ),
            original_allowed_action_count=len(
                allowed_first_actions or ()
            ),
        )
    return replace(
        decision,
        local_certificate_timing=(
            _certificate_timing_accumulator.snapshot()
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
    output,
    *,
    last_frame: int | None,
    counter_gaps: int,
    hit_count: int,
    termination_reason: str,
) -> None:
    output.write(
        json.dumps(
            {
                "kind": "summary",
                "last_frame": last_frame,
                "counter_gaps": counter_gaps,
                "hit_count": hit_count,
                "termination_reason": termination_reason,
            }
        )
        + "\n"
    )
    output.flush()


def _candidate_outcome_record(
    outcome: CandidateVerifierOutcome | None,
    *,
    issued_action: str | None = None,
) -> dict[str, object] | None:
    if outcome is None:
        return None
    label = outcome.state_label
    root = outcome.target.root
    witnesses_by_action = {
        witness.root_action: witness
        for witness in outcome.action_witnesses
    }

    def witness_record(action: str) -> dict[str, object] | None:
        witness = witnesses_by_action.get(action)
        if witness is None:
            return None
        return {
            "root_action": witness.root_action,
            "candidate_policy": witness.candidate_policy,
            "survival_frames": witness.label.guaranteed_frames,
            "bottleneck_margin": witness.label.bottleneck_margin,
        }

    return {
        "revision": outcome.revision,
        "policy_version": outcome.target.policy_version,
        "root": {
            "frame": root.frame,
            "row": root.row,
            "column": root.column,
            "observed_action": root.observed_action,
            "pending_action": (
                root.pending_command.action
                if root.pending_command is not None
                else None
            ),
            "pending_remaining_frames": (
                root.pending_command.remaining_frames
                if root.pending_command is not None
                else ()
            ),
        },
        "status": outcome.status,
        "queue_ms": outcome.queue_ms,
        "elapsed_ms": outcome.elapsed_ms,
        "horizon_frames": outcome.horizon_frames,
        "winning": outcome.winning,
        "survival_frames": (
            label.guaranteed_frames if label is not None else None
        ),
        "bottleneck_margin": (
            label.bottleneck_margin if label is not None else None
        ),
        "best_actions": outcome.best_actions,
        "best_action_witnesses": tuple(
            record
            for action in outcome.best_actions
            if (record := witness_record(action)) is not None
        ),
        "issued_action_label": (
            witness_record(issued_action)
            if issued_action is not None
            else None
        ),
        "completed_candidates": outcome.completed_candidates,
        "timed_out_candidates": outcome.timed_out_candidates,
        "unvisited_candidates": outcome.unvisited_candidates,
        "stopped_on_feasibility": outcome.stopped_on_feasibility,
        "budget_exhausted": outcome.budget_exhausted,
        "background_priority_lowered": (
            outcome.background_priority_lowered
        ),
        "stale_at_completion": outcome.stale_at_completion,
        "error": outcome.error,
    }


def _candidate_shadow_publications(
    outcome: CandidateVerifierOutcome | None,
    *,
    issue_action_certificates: tuple[RobustActionCertificate, ...],
    issued_action: str,
    issue_frame: int,
    deadline_missed: bool,
    input_override: bool = False,
) -> tuple[dict[str, object], ...]:
    """Publish one-shot, shadow-only candidate witnesses for audit.

    This function never changes the selected input.  A publication is marked
    issue-eligible only when the exact delivered outcome is a completed
    full-horizon win and the already-computed local hard certificate for that
    alternate root action is safe at this issue.
    """

    if (
        outcome is None
        or outcome.status != "feasible"
        or outcome.winning is not True
        or outcome.stale_at_completion
    ):
        return ()
    root = outcome.target.root
    certificates = {
        certificate.action: certificate
        for certificate in issue_action_certificates
    }
    publications = []
    for witness in outcome.action_witnesses:
        if witness.root_action not in outcome.best_actions:
            continue
        certificate = certificates.get(witness.root_action)
        witness_matches_result = bool(
            witness.label == outcome.state_label
            and witness.candidate_policy
            in outcome.completed_candidates
        )
        certificate_safe = bool(
            certificate is not None
            and certificate.worst_collisions == 0
            and certificate.min_clearance >= 0.0
        )
        status = (
            "witness_result_mismatch"
            if not witness_matches_result
            else (
                "input_override"
                if input_override
                else (
                    "deadline_missed"
                    if deadline_missed
                    else (
                        "issue_certificate_missing"
                        if certificate is None
                        else (
                            "issue_eligible"
                            if certificate_safe
                            else "issue_certificate_unsafe"
                        )
                    )
                )
            )
        )
        publications.append(
            {
                "role": "shadow_no_action_authority",
                "status": status,
                "issue_eligible": status == "issue_eligible",
                "revision": outcome.revision,
                "policy_version": outcome.target.policy_version,
                "root": {
                    "frame": root.frame,
                    "row": root.row,
                    "column": root.column,
                    "observed_action": root.observed_action,
                    "pending_action": (
                        root.pending_command.action
                        if root.pending_command is not None
                        else None
                    ),
                    "pending_remaining_frames": (
                        root.pending_command.remaining_frames
                        if root.pending_command is not None
                        else ()
                    ),
                },
                "root_action": witness.root_action,
                "candidate_policy": witness.candidate_policy,
                "survival_frames": witness.label.guaranteed_frames,
                "bottleneck_margin": witness.label.bottleneck_margin,
                "horizon_frames": outcome.horizon_frames,
                "issued_action": issued_action,
                "would_change_action": witness.root_action != issued_action,
                "valid_for_issue_frame": issue_frame,
                "expires_after_issue_frame": issue_frame,
                "deadline_missed": deadline_missed,
                "input_override": input_override,
                "witness_matches_result": witness_matches_result,
                "issue_certificate": (
                    {
                        "delay_frames": certificate.delay_frames,
                        "worst_collisions": (
                            certificate.worst_collisions
                        ),
                        "min_clearance": certificate.min_clearance,
                        "cvar_risk": certificate.cvar_risk,
                        "worst_delay": certificate.worst_delay,
                    }
                    if certificate is not None
                    else None
                ),
            }
        )
    return tuple(publications)


def _candidate_snapshot_record(
    snapshot: CandidateVerifierSnapshot | None,
) -> dict[str, object] | None:
    if snapshot is None:
        return None
    return {
        "horizon_frames": snapshot.horizon_frames,
        "decision_frame_support": snapshot.decision_frame_support,
        "timeout_ms_per_candidate": (
            snapshot.timeout_ms_per_candidate
        ),
        "total_timeout_ms": snapshot.total_timeout_ms,
        "submitted_revision": snapshot.submitted_revision,
        "completed_revision": snapshot.completed_revision,
        "ready_revision": snapshot.ready_revision,
        "target_running": snapshot.target_running,
        "target_queued": snapshot.target_queued,
        "target_replacement_count": (
            snapshot.target_replacement_count
        ),
        "target_discard_count": snapshot.target_discard_count,
        "stale_completion_count": snapshot.stale_completion_count,
        "lookup_count": snapshot.lookup_count,
        "lookup_hit_count": snapshot.lookup_hit_count,
        "lookup_miss_count": snapshot.lookup_miss_count,
        "latest_outcome": _candidate_outcome_record(
            snapshot.latest_outcome
        ),
    }


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
    corridor_executor: ThreadPoolExecutor | None = None
    corridor_future: Future[CorridorSolution] | None = None
    survival_executor: ThreadPoolExecutor | None = None
    corridor_survival_future: Future[CorridorSolution] | None = None
    candidate_verifier: CandidateVerifierService | None = None
    audit_executor: ThreadPoolExecutor | None = None
    pipeline_retire_executor: ThreadPoolExecutor | None = None
    enemy_executor: ThreadPoolExecutor | None = None
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
    auto_confirm = AutoConfirmPulse(
        interval_frames=args.auto_confirm_every,
        idle_frames=args.auto_confirm_idle_frames,
    )
    stage_successors = dict(ROUTE2_STAGE_SUCCESSORS)
    if args.terminal_stage is not None:
        stage_successors.pop(args.terminal_stage, None)
    scene_guard = GameplaySceneGuard(
        stage_successors=stage_successors,
        transition_timeout_seconds=args.stage_transition_timeout,
        terminal_grace_seconds=args.terminal_inactive_grace,
    )
    last_frame_progress = time.perf_counter()
    last_frozen_confirm = float("-inf")
    input_clock_tracker = (
        SemanticInputClockTracker()
        if args.input_clock_boundary_shadow
        else None
    )
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
    if not args.local_only:
        corridor_executor = ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix="th08-corridor",
        )
        if args.postpublished_survival_shadow:
            survival_executor = ThreadPoolExecutor(
                max_workers=1,
                thread_name_prefix="th08-survival-shadow",
            )
        if args.pipeline_prewarm_shadow:
            pipeline_retire_executor = ThreadPoolExecutor(
                max_workers=1,
                thread_name_prefix="th08-pipeline-retire",
            )
        if args.candidate_verifier_shadow:
            candidate_verifier = CandidateVerifierService(
                horizon_frames=CANDIDATE_VERIFIER_HORIZON_FRAMES,
                decision_frame_support=(
                    CANDIDATE_VERIFIER_DECISION_FRAMES
                ),
                timeout_ms_per_candidate=(
                    CANDIDATE_VERIFIER_TIMEOUT_MS
                ),
            )
    if args.viability_audit_dir is not None:
        audit_executor = ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix="th08-viability-audit",
        )
    enemy_executor = ThreadPoolExecutor(
        max_workers=1,
        thread_name_prefix="th08-enemy-sensor",
    )

    def retire_pipeline_solutions(
        candidates: tuple[CorridorSolution | None, ...],
        retained: tuple[CorridorSolution | None, ...] = (),
    ) -> None:
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
        if pipeline_retire_executor is not None:
            pipeline_retire_executor.submit(
                _close_retired_pipeline_prewarms,
                retired,
            )
        else:
            _close_retired_pipeline_prewarms(retired)

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
        output.write(json.dumps(record) + "\n")
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
            output.write(json.dumps(event_record) + "\n")
        output.flush()

    try:
        identity = verify_target(reader)
        output.write(json.dumps({"kind": "identity", **identity}) + "\n")
        output.write(
            json.dumps(
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
                }
            )
            + "\n"
        )
        output.flush()
        state = observe_state(reader)
        if args.wait_gameplay:
            output.write(
                json.dumps(
                    {
                        "kind": "wait_ready",
                        "frame": state["enemy_manager_frame"],
                    }
                )
                + "\n"
            )
            output.flush()
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
        bullet_pool_buffer = reader.allocate_buffer(
            BULLET_POOL_SIZE * BULLET_STRIDE
        )
        bullet_blob = memoryview(bullet_pool_buffer).cast("B")
        laser_pool_buffer = reader.allocate_buffer(
            LASER_POOL_SIZE * LASER_STRIDE
        )
        laser_blob = memoryview(laser_pool_buffer).cast("B")
        item_pool_buffer = reader.allocate_buffer(
            ITEM_POOL_SIZE * ITEM_STRIDE
        )
        item_blob = memoryview(item_pool_buffer).cast("B")
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
                    _require_foreground(api, pid)
                    transitions = input_transitions(
                        previous_mask,
                        0,
                        supported_mask=SUPPORTED_INPUT_MASK,
                    )
                    send_transitions(api, transitions)
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
                    output.write(
                        json.dumps(
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
                            }
                        )
                        + "\n"
                    )
                    output.flush()
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
                    output.write(
                        json.dumps(
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
                            }
                        )
                        + "\n"
                    )
                    output.flush()
                time.sleep(args.poll_ms / 1000.0)
                continue
            if scene_decision.status == "resumed":
                gameplay_epoch += 1
                boss_phase_tracker.reset()
                output.write(
                    json.dumps(
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
                        }
                    )
                    + "\n"
                )
                output.flush()
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
                    output.write(
                        json.dumps(
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
                            }
                        )
                        + "\n"
                    )
                    output.flush()
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
            bullet_frame_before = reader.u32(0x0164D30C)
            bullet_pool_read_started = time.perf_counter()
            reader.read_into(
                BULLET_POOL_BASE,
                bullet_pool_buffer,
            )
            bullet_pool_read_ms = (
                time.perf_counter() - bullet_pool_read_started
            ) * 1000.0
            bullet_frame_after = reader.u32(0x0164D30C)
            laser_pool_read_started = time.perf_counter()
            reader.read_into(LASER_POOL_BASE, laser_pool_buffer)
            laser_pool_read_ms = (
                time.perf_counter() - laser_pool_read_started
            ) * 1000.0
            item_pool_read_started = time.perf_counter()
            reader.read_into(ITEM_MANAGER_BASE, item_pool_buffer)
            item_pool_read_ms = (
                time.perf_counter() - item_pool_read_started
            ) * 1000.0
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
                _require_foreground(api, pid)
                send_transitions(
                    api,
                    input_transitions(
                        previous_mask,
                        safe_mask,
                        supported_mask=SUPPORTED_INPUT_MASK,
                    ),
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
                output.write(
                    json.dumps(
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
                        }
                    )
                    + "\n"
                )
                output.flush()
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
            corridor_target = _corridor_target(
                corridor_solution,
                current_frame=(
                    int(state["enemy_manager_frame"])
                    + control_delay_frames
                ),
                lookahead_frames=args.corridor_lookahead,
                max_age_frames=args.corridor_max_age,
            )
            viability_query = _corridor_viability_query(
                corridor_solution,
                current_frame=counter_after_read,
                player_x=projected_player_x,
                player_y=projected_player_y,
                active_action=_action_name_from_mask(previous_mask),
                max_age_frames=args.corridor_max_age,
            )
            observed_input_action = _action_name_from_mask(
                int(state["input_current"])
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
            held_desired_action = _local_pipeline_action_from_mask(
                previous_mask
            )
            active_supported_mask = (
                int(state["input_current"]) & SUPPORTED_INPUT_MASK
            )
            held_desired_mask = previous_mask & SUPPORTED_INPUT_MASK
            pending_supported_mask = (
                pending_command_estimate.expected_mask
                & SUPPORTED_INPUT_MASK
                if pipeline_pending_command is not None
                and pending_command_estimate is not None
                else None
            )
            local_pipeline_estimator_consistent = (
                (
                    pipeline_pending_command is None
                    and held_desired_mask == active_supported_mask
                )
                or (
                    pipeline_pending_command is not None
                    and pending_supported_mask == held_desired_mask
                )
            )
            observed_local_pipeline_root = (
                LocalPipelineRoot(
                    active_action=_local_pipeline_action_from_mask(
                        active_supported_mask
                    ),
                    held_desired_action=held_desired_action,
                    pending_action=(
                        _local_pipeline_action_from_mask(
                            int(pending_supported_mask)
                        )
                        if pending_supported_mask is not None
                        else None
                    ),
                    remaining_delay_support=(
                        pipeline_pending_command.remaining_frames
                        if pipeline_pending_command is not None
                        else ()
                    ),
                )
                if local_pipeline_estimator_consistent
                else None
            )
            local_pipeline_root_record = {
                "role": "shadow_no_action_authority",
                "active_action": _local_pipeline_action_from_mask(
                    active_supported_mask
                ),
                "active_mask": active_supported_mask,
                "held_desired_action": held_desired_action,
                "held_desired_mask": held_desired_mask,
                "pending_action": (
                    _local_pipeline_action_from_mask(
                        int(pending_supported_mask)
                    )
                    if pending_supported_mask is not None
                    else None
                ),
                "pending_mask": pending_supported_mask,
                "remaining_delay_support": (
                    pipeline_pending_command.remaining_frames
                    if pipeline_pending_command is not None
                    else ()
                ),
                "snapshot_age": (
                    pending_command_estimate.snapshot_age
                    if pending_command_estimate is not None
                    else None
                ),
                "issue_age": (
                    pending_command_estimate.issue_age
                    if pending_command_estimate is not None
                    else None
                ),
                "overdue": (
                    pending_command_estimate.overdue
                    if pending_command_estimate is not None
                    else False
                ),
                "estimator_consistent": (
                    local_pipeline_estimator_consistent
                ),
            }
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
            pipeline_prewarm_query = (
                _corridor_pipeline_prewarm_query(
                    corridor_solution,
                    current_frame=counter_after_read,
                    player_x=projected_player_x,
                    player_y=projected_player_y,
                    observed_action=observed_input_action,
                    pending_command=pipeline_pending_command,
                    max_age_frames=args.corridor_max_age,
                )
                if args.pipeline_prewarm_shadow
                else None
            )
            postpublished_survival_query = (
                _corridor_postpublished_survival_query(
                    corridor_solution,
                    current_frame=counter_after_read,
                    player_x=projected_player_x,
                    player_y=projected_player_y,
                    observed_action=observed_input_action,
                    max_age_frames=args.corridor_max_age,
                )
            )
            safety_value_query = _corridor_safety_value_query(
                corridor_solution,
                current_frame=counter_after_read,
                player_x=projected_player_x,
                player_y=projected_player_y,
                active_action=_action_name_from_mask(previous_mask),
                max_age_frames=args.corridor_max_age,
            )
            viability_policy = (
                corridor_solution.plan.viability_policy
                if corridor_solution is not None
                else None
            )
            policy_guidance = assemble_local_policy_guidance(
                viability_query=viability_query,
                safety_value_query=safety_value_query,
                policy_delay_frames=(
                    viability_policy.delay_frames
                    if viability_policy is not None
                    else None
                ),
                current_delay_frames=delay_estimate.support,
            )
            corridor_overhead_ms = (
                time.perf_counter() - corridor_started
            ) * 1000.0
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
                        player_x=float(player["x"]),
                        player_y=float(player["y"]),
                        bullets=bullets,
                        lasers=lasers,
                        enemy_bodies=enemy_bodies,
                        items=items,
                        snapshot_lag=player_to_hazard_lag,
                    ),
                    actuator=ActuatorPipeline(
                        previous_direction=previous_direction,
                        can_bomb=can_bomb,
                        previous_focus=bool(previous_mask & FOCUS),
                        control_delay_frames=control_delay_frames,
                        control_delay_candidates=delay_estimate.support,
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
                        power=float(resources["power"]),
                        bombs=float(resources["bombs"]),
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
                _require_foreground(api, pid)
                send_transitions(
                    api,
                    input_transitions(
                        previous_mask,
                        safe_mask,
                        supported_mask=SUPPORTED_INPUT_MASK,
                    ),
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
                output.write(
                    json.dumps(
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
                        }
                    )
                    + "\n"
                )
                output.flush()
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
            transitions = input_transitions(
                previous_mask,
                decision.mask,
                supported_mask=SUPPORTED_INPUT_MASK,
            )
            input_started = time.perf_counter()
            send_transitions(api, transitions)
            input_ms = (time.perf_counter() - input_started) * 1000.0
            issue_path_ms = (
                time.perf_counter() - issue_path_started
            ) * 1000.0
            observe_to_issue_ms = (
                time.perf_counter() - iteration_started
            ) * 1000.0
            if transitions:
                delay_estimator.issued(
                    snapshot_frame=int(state["enemy_manager_frame"]),
                    issue_frame=counter_at_action,
                    expected_mask=decision.mask,
                    support_high=delay_estimate.support[-1],
                    support=delay_estimate.support,
                )
            previous_mask = decision.mask
            previous_direction = decision.mask & (UP | DOWN | LEFT | RIGHT)
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
                    "deadline_guard": {
                        "missed": action_deadline_missed,
                        "support_high": action_alignment.support_high,
                        "post_capture_advance": (
                            action_alignment.post_capture_advance
                        ),
                        "input_suppressed": action_deadline_missed,
                        "planned_action": planned_action,
                        "planned_mask": planned_mask,
                        "issued_action": decision.action,
                        "issued_mask": decision.mask,
                    },
                    "control_delay_frames": control_delay_frames,
                    "control_delay_candidates": delay_estimate.support,
                    "control_delay_sample_count": (
                        delay_estimate.end_to_end_samples
                    ),
                    "control_delay_estimator": {
                        "computation_samples": (
                            delay_estimate.computation_samples
                        ),
                        "pickup_samples": delay_estimate.pickup_samples,
                        "end_to_end_samples": (
                            delay_estimate.end_to_end_samples
                        ),
                        "guard_active": delay_estimate.guard_active,
                        "overruns": delay_estimate.overruns,
                        "censored": delay_estimate.censored,
                    },
                    "action_hold_frames": action_hold_frames,
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
                    "input_snapshot": {
                        "raw": state["input_raw"],
                        "current": state["input_current"],
                        "previous": state["input_previous"],
                    },
                    "local_pipeline_root": local_pipeline_root_record,
                    "local_pipeline_timing": {
                        "planning": _local_certificate_timing_record(
                            decision.local_certificate_timing
                        ),
                        "issue_recertificate": (
                            _local_certificate_timing_record(
                                decision.issue_certificate_timing
                            )
                        ),
                    },
                    "local_pipeline_certificate_shadow": (
                        local_pipeline_certificate_shadow
                    ),
                    "planner_objective": {
                        "corridor_target": (
                            {
                                "x": corridor_target[0],
                                "y": corridor_target[1],
                                "deadline": corridor_target[2],
                            }
                            if corridor_target is not None
                            else None
                        ),
                        "damage_target_x": damage_target_x,
                        "damage_target_half_width": (
                            damage_target_half_width
                        ),
                        "damageable": damageable,
                        "active_items": len(items),
                        "item_objectives_enabled": (
                            ITEM_OBJECTIVES_ENABLED
                        ),
                        "damage_action_authority": False,
                        "preserve_previous_direction_inertia": (
                            not corridor_context_changed
                        ),
                        "corridor_context_changed": (
                            corridor_context_changed
                        ),
                    },
                    "planner_guidance": {
                        "support_covers_current": (
                            policy_guidance.support_covers_current
                        ),
                        "allowed_first_actions": (
                            policy_guidance.allowed_first_actions
                        ),
                        "repair_volumes": dict(
                            policy_guidance.repair_volumes
                        ),
                        "recovery_distances": dict(
                            policy_guidance.recovery_distances
                        ),
                        "safety_actions": policy_guidance.safety_actions,
                        "safety_state_value": (
                            policy_guidance.safety_state_value
                        ),
                        "survival_actions": (
                            policy_guidance.survival_actions
                        ),
                        "survival_frames": policy_guidance.survival_frames,
                        "survival_bottleneck_margin": (
                            policy_guidance.survival_bottleneck_margin
                        ),
                        "position_error": policy_guidance.position_error,
                    },
                    "player": {
                        "x": player["x"],
                        "y": player["y"],
                        "projected_x": projected_player_x,
                        "projected_y": projected_player_y,
                        "control_origin_x": control_origin_x,
                        "control_origin_y": control_origin_y,
                        "phase": player["phase"],
                        "phase_at_action": phase_now,
                        "predeath_at_action": predeath_now,
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
                    "damage_objective": {
                        "role": (
                            "shadow"
                        ),
                        "available": decision.damage_objective_available,
                        "reason": decision.damage_reason,
                        "target_x": damage_target_x,
                        "target_half_width": damage_target_half_width,
                        "baseline_action": decision.damage_baseline_action,
                        "shadow_action": decision.damage_shadow_action,
                        "issued_action": decision.action,
                        "live_selected": False,
                        "current_alignment_cost": (
                            decision.damage_current_alignment_cost
                        ),
                        "shadow_alignment_cost": (
                            decision.damage_shadow_alignment_cost
                        ),
                        "eligible_action_count": (
                            decision.damage_eligible_action_count
                        ),
                    },
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
                    "action": decision.action,
                    "mask": decision.mask,
                    "focused": decision.planned_focus,
                    "minimum_clearance": decision.min_clearance,
                    "immediate_clearance": decision.immediate_clearance,
                    "pipeline_clearance": decision.pipeline_clearance,
                    "robust_control": {
                        "delay_frames": decision.robust_delay_frames,
                        "override": decision.robust_override,
                        "worst_collisions": decision.robust_collisions,
                        "min_clearance": decision.robust_min_clearance,
                        "cvar_risk": decision.robust_cvar_risk,
                        "worst_delay": decision.robust_worst_delay,
                        "viability_constrained": (
                            decision.viability_constrained
                        ),
                        "viability_safe_action_count": (
                            decision.viability_safe_action_count
                        ),
                        "viability_repair_volume": (
                            decision.viability_repair_volume
                        ),
                        "viability_constraint_relaxed": (
                            decision.viability_constraint_relaxed
                        ),
                        "viability_recovery_distance": (
                            decision.viability_recovery_distance
                        ),
                        "viability_control_reserve_deficit": (
                            decision.viability_control_reserve_deficit
                        ),
                        "viability_control_reserve_valid": (
                            decision.viability_control_reserve_valid
                        ),
                        "preloss_continuation_preference_active": (
                            decision.preloss_continuation_preference_active
                        ),
                        "planned_route_gate_deficit": (
                            decision.planned_route_gate_deficit
                        ),
                        "local_collisions": decision.local_collisions,
                        "preloss_supplemental_beam_active": (
                            decision.preloss_supplemental_beam_active
                        ),
                        "preloss_supplemental_beam_width": (
                            decision.preloss_supplemental_beam_width
                        ),
                        "preloss_historical_action": (
                            decision.preloss_historical_action
                        ),
                        "preloss_selected_from_supplemental": (
                            decision.preloss_selected_from_supplemental
                        ),
                        "preloss_supplemental_candidate_count": (
                            decision.preloss_supplemental_candidate_count
                        ),
                        "preloss_historical_route_gate_deficit": (
                            decision.preloss_historical_route_gate_deficit
                        ),
                        "preloss_supplemental_failure": (
                            decision.preloss_supplemental_failure
                        ),
                        "preloss_supplemental_backend": (
                            decision.preloss_supplemental_backend
                        ),
                        "preloss_supplemental_status": (
                            decision.preloss_supplemental_status
                        ),
                        "preloss_supplemental_completed": (
                            decision.preloss_supplemental_completed
                        ),
                        "preloss_supplemental_historical_fallback": (
                            decision
                            .preloss_supplemental_historical_fallback
                        ),
                        "preloss_supplemental_background_compute_ms": (
                            decision
                            .preloss_supplemental_background_compute_ms
                        ),
                        "viability_safety_value_preferred": (
                            decision.viability_safety_value_preferred
                        ),
                        "viability_safety_state_value": (
                            decision.viability_safety_state_value
                        ),
                        "viability_fresh_prefix_filtered": (
                            decision.viability_fresh_prefix_filtered
                        ),
                        "viability_fresh_prefix_relaxed": (
                            decision.viability_fresh_prefix_relaxed
                        ),
                        "viability_survival_preferred": (
                            decision.viability_survival_preferred
                        ),
                        "viability_survival_frames": (
                            decision.viability_survival_frames
                        ),
                        "viability_survival_bottleneck_margin": (
                            decision.viability_survival_bottleneck_margin
                        ),
                    },
                    "terminal_threat": {
                        "mode": (
                            "constant_terminal_action_heuristic"
                            if decision.terminal_threat_horizon > args.horizon
                            else "disabled_no_degenerate_boundary"
                        ),
                        "horizon_frames": (
                            decision.terminal_threat_horizon
                        ),
                        "collisions": (
                            decision.terminal_threat_collisions
                        ),
                        "min_clearance": (
                            decision.terminal_threat_min_clearance
                        ),
                    },
                    "score": decision.score,
                    "item_utility": decision.item_utility,
                    "predicted_collections": decision.predicted_collections,
                    "bomb": decision.bomb,
                    "hit_started": hit_started,
                    "hit_count": hit_count,
                    "auto_confirm": auto_confirm_event,
                    "enemy_bodies": _serialized_enemy_bodies(enemy_bodies),
                }
                if candidate_verifier is not None:
                    candidate_root = (
                        candidate_verifier_target.root
                        if candidate_verifier_target is not None
                        else None
                    )
                    if candidate_verifier_submit_error is not None:
                        candidate_status = "submit_error"
                    elif candidate_verifier_lookup_error is not None:
                        candidate_status = "lookup_error"
                    elif candidate_verifier_target is None:
                        candidate_status = (
                            "skipped_boolean_viable"
                            if candidate_verifier_eligibility
                            == "boolean_viable"
                            else "unavailable"
                        )
                    elif candidate_verifier_outcome is not None:
                        candidate_status = "hit"
                    else:
                        candidate_status = "miss"
                    record["candidate_verifier_shadow"] = {
                        "role": "shadow_no_action_authority",
                        "status": candidate_status,
                        "eligibility": (
                            candidate_verifier_eligibility
                        ),
                        "submit_revision": (
                            candidate_verifier_revision
                        ),
                        "submit_ms": candidate_verifier_submit_ms,
                        "lookup_ms": candidate_verifier_lookup_ms,
                        "publication_ms": candidate_publication_ms,
                        "submit_error": (
                            candidate_verifier_submit_error
                        ),
                        "lookup_error": (
                            candidate_verifier_lookup_error
                        ),
                        "target": (
                            {
                                "policy_version": (
                                    candidate_verifier_target
                                    .policy_version
                                ),
                                "frame": candidate_root.frame,
                                "row": candidate_root.row,
                                "column": candidate_root.column,
                                "observed_action": (
                                    candidate_root.observed_action
                                ),
                                "pending_action": (
                                    candidate_root
                                    .pending_command.action
                                    if (
                                        candidate_root.pending_command
                                        is not None
                                    )
                                    else None
                                ),
                                "pending_remaining_frames": (
                                    candidate_root.pending_command
                                    .remaining_frames
                                    if (
                                        candidate_root.pending_command
                                        is not None
                                    )
                                    else ()
                                ),
                            }
                            if (
                                candidate_verifier_target is not None
                                and candidate_root is not None
                            )
                            else None
                        ),
                        "result": (
                            {
                                **(
                                    _candidate_outcome_record(
                                        candidate_verifier_outcome,
                                        issued_action=(
                                            _action_name_from_mask(
                                                decision.mask
                                            )
                                        ),
                                    )
                                    or {}
                                ),
                                "issued_in_best": (
                                    _action_name_from_mask(decision.mask)
                                    in candidate_verifier_outcome
                                    .best_actions
                                ),
                            }
                            if candidate_verifier_outcome is not None
                            else None
                        ),
                        "service": _candidate_snapshot_record(
                            candidate_verifier_snapshot
                        ),
                        "publications": (
                            candidate_shadow_publications
                        ),
                    }
                if hit_contact_observation is not None:
                    record["hit_contact_observation"] = (
                        hit_contact_observation
                    )
                corridor_report_solution = (
                    corridor_solution or corridor_pending_solution
                )
                if corridor_report_solution is not None:
                    corridor_policy_status = _corridor_policy_status(
                        corridor_report_solution,
                        current_frame=counter_at_action,
                        max_age_frames=args.corridor_max_age,
                    )
                    audit_write_ms = (
                        corridor_report_solution.audit_write_ms
                    )
                    audit_error = corridor_report_solution.audit_error
                    audit_pending = False
                    if corridor_report_solution.audit_future is not None:
                        audit_pending = (
                            not corridor_report_solution.audit_future.done()
                        )
                        if not audit_pending:
                            audit_write_ms, audit_error = (
                                corridor_report_solution.audit_future.result()
                            )
                    corridor_record = {
                        "source_frame": corridor_report_solution.source_frame,
                        "snapshot_frame": (
                            corridor_report_solution.snapshot_frame
                        ),
                        "forecast_lead_frames": (
                            corridor_report_solution.forecast_lead_frames
                        ),
                        "age": counter_at_action
                        - corridor_report_solution.source_frame,
                        "solve_ms": corridor_report_solution.solve_ms,
                        "worker_ms": corridor_report_solution.worker_ms,
                        "background_priority_lowered": (
                            corridor_report_solution
                            .background_priority_lowered
                        ),
                        "native_viability_worker_limit": (
                            corridor_report_solution
                            .native_viability_worker_limit
                        ),
                        "native_viability_worker_limit_applied": (
                            corridor_report_solution
                            .native_viability_worker_limit_applied
                        ),
                        "reachable": corridor_report_solution.plan.reachable,
                        "planning_mode": (
                            corridor_report_solution.plan.planning_mode
                        ),
                        "viability_backend": (
                            corridor_report_solution.plan.viability_backend
                        ),
                        "viability_grid_step": (
                            corridor_report_solution.plan.viability_grid_step
                        ),
                        "survival_backend": (
                            corridor_report_solution.plan
                            .survival_policy.backend
                            if corridor_report_solution.plan
                            .survival_policy is not None
                            else None
                        ),
                        "postpublished_survival_ms": (
                            corridor_report_solution
                            .postpublished_survival_ms
                        ),
                        "postpublished_survival_parity": (
                            corridor_report_solution
                            .postpublished_survival_parity
                        ),
                        "solver_timing_ms": dict(
                            corridor_report_solution.plan.solver_timing_ms
                        ),
                        "audit_capsule": (
                            corridor_report_solution.audit_capsule
                        ),
                        "audit_write_ms": audit_write_ms,
                        "audit_error": audit_error,
                        "audit_pending": audit_pending,
                        "lane": corridor_report_solution.plan.lane,
                        "bottleneck_clearance": (
                            corridor_report_solution.plan.bottleneck_clearance
                        ),
                        "initial_safe_action_count": (
                            corridor_report_solution.plan
                            .initial_safe_action_count
                        ),
                        "initial_repair_volume": (
                            corridor_report_solution.plan
                            .initial_repair_volume
                        ),
                        "policy_status": corridor_policy_status,
                        "stale": corridor_policy_status
                        in ("expired", "outside_policy_horizon"),
                        "guidance_unavailable": viability_query is None,
                        "lead_estimate_frames": corridor_policy_lead.frames,
                        "lead_sample_count": (
                            corridor_policy_lead.sample_count
                        ),
                        "lead_p90_solve_frames": (
                            corridor_policy_lead.p90_solve_frames
                        ),
                        "serial_coverage_margin_frames": (
                            corridor_policy_lead.serial_coverage_margin(
                                corridor_report_solution.plan
                                .viability_policy.horizon_frames
                            )
                            if corridor_report_solution.plan
                            .viability_policy is not None
                            else None
                        ),
                        "serial_worker_serviceable": (
                            corridor_policy_lead.serial_worker_serviceable(
                                corridor_report_solution.plan
                                .viability_policy.horizon_frames
                            )
                            if corridor_report_solution.plan
                            .viability_policy is not None
                            else False
                        ),
                        "commitment": {
                            "active_lane": corridor_commitment.active_lane(
                                counter_at_action
                            ),
                            "expires_frame": (
                                corridor_commitment.expires_frame
                            ),
                            "required_gate_lane": (
                                corridor_report_solution.required_gate_lane
                            ),
                            "constraint_honored": (
                                corridor_report_solution.constraint_honored
                            ),
                            "context": corridor_context,
                        },
                    }
                    if (
                        corridor_solution is not None
                        and corridor_pending_solution is not None
                    ):
                        corridor_record["next_policy"] = {
                            "source_frame": (
                                corridor_pending_solution.source_frame
                            ),
                            "frames_until_epoch": max(
                                0,
                                corridor_pending_solution.source_frame
                                - counter_at_action,
                            ),
                            "solve_ms": corridor_pending_solution.solve_ms,
                        }
                    if viability_query is not None:
                        assert corridor_solution is not None
                        policy = corridor_solution.plan.viability_policy
                        assert policy is not None
                        corridor_record["viability"] = {
                            "query_frame": counter_after_read,
                            "age": counter_after_read
                            - corridor_solution.source_frame,
                            "phase_frames": (
                                (
                                    counter_after_read
                                    - corridor_solution.source_frame
                                )
                                % policy.config.frames_per_layer
                            ),
                            "layer": viability_query.layer,
                            "available": viability_query.available,
                            "state_viable": viability_query.state_viable,
                            "active_action": viability_query.active_action,
                            "observed_input_action": (
                                observed_input_action
                            ),
                            "safe_action_count": (
                                viability_query.safe_action_count
                            ),
                            "safe_actions": viability_query.safe_actions,
                            "repair_volumes": dict(
                                viability_query.repair_volumes
                            ),
                            "recovery_distances": dict(
                                viability_query.recovery_distances
                            ),
                            "survival_frames": (
                                viability_query.survival_frames
                            ),
                            "survival_bottleneck_margin": (
                                viability_query
                                .survival_bottleneck_margin
                            ),
                            "survival_best_actions": (
                                viability_query.survival_best_actions
                            ),
                            "selected_action": decision.action,
                            "selected_repair_volume": (
                                decision.viability_repair_volume
                            ),
                            "selected_recovery_distance": (
                                decision.viability_recovery_distance
                            ),
                            "selected_survival_preferred": (
                                decision.viability_survival_preferred
                            ),
                            "position_error": (
                                viability_query.position_error
                            ),
                            "delay_frames": policy.delay_frames,
                            "current_delay_frames": (
                                delay_estimate.support
                            ),
                            "support_covers_current": (
                                policy_guidance.support_covers_current
                            ),
                            "nominal_delay": policy.nominal_delay,
                            "horizon_frames": policy.horizon_frames,
                            "viable_state_count": (
                                policy.viable_state_count(
                                    viability_query.layer
                                )
                                if viability_query.layer is not None
                                and 0
                                <= viability_query.layer
                                <= policy.layer_count
                                else 0
                            ),
                            "reason": viability_query.reason,
                        }
                    if postpublished_survival_query is not None:
                        corridor_record["postpublished_survival_shadow"] = {
                            "role": "shadow_no_action_authority",
                            "available": (
                                postpublished_survival_query.available
                            ),
                            "state_viable": (
                                postpublished_survival_query.state_viable
                            ),
                            "survival_frames": (
                                postpublished_survival_query.survival_frames
                            ),
                            "survival_bottleneck_margin": (
                                postpublished_survival_query
                                .survival_bottleneck_margin
                            ),
                            "survival_best_actions": (
                                postpublished_survival_query
                                .survival_best_actions
                            ),
                            "observed_input_action": (
                                observed_input_action
                            ),
                            "issued_action": decision.action,
                        }
                    if pipeline_prewarm_query is not None:
                        pipeline_result = pipeline_prewarm_query.result
                        pipeline_root = pipeline_prewarm_query.root
                        pipeline_service = pipeline_prewarm_query.service
                        latest_outcome = (
                            pipeline_service.latest_outcome
                            if pipeline_service is not None
                            else None
                        )
                        scheduler_snapshot = (
                            pipeline_service.scheduler
                            if pipeline_service is not None
                            else None
                        )
                        corridor_record[
                            "pipeline_prewarm_shadow"
                        ] = {
                            "role": "shadow_no_action_authority",
                            "start_error": (
                                corridor_report_solution
                                .pipeline_prewarm_start_error
                            ),
                            "status": pipeline_prewarm_query.status,
                            "lookup_ms": pipeline_prewarm_query.lookup_ms,
                            "root": (
                                {
                                    "frame": pipeline_root.frame,
                                    "row": pipeline_root.row,
                                    "column": pipeline_root.column,
                                    "observed_action": (
                                        pipeline_root.observed_action
                                    ),
                                    "pending_action": (
                                        pipeline_root.pending_command.action
                                        if (
                                            pipeline_root.pending_command
                                            is not None
                                        )
                                        else None
                                    ),
                                    "pending_remaining_frames": (
                                        pipeline_root.pending_command
                                        .remaining_frames
                                        if (
                                            pipeline_root.pending_command
                                            is not None
                                        )
                                        else ()
                                    ),
                                }
                                if pipeline_root is not None
                                else None
                            ),
                            "result": (
                                {
                                    "winning": pipeline_result.winning,
                                    "survival_frames": (
                                        pipeline_result.state_label
                                        .guaranteed_frames
                                    ),
                                    "bottleneck_margin": (
                                        pipeline_result.state_label
                                        .bottleneck_margin
                                    ),
                                    "best_actions": (
                                        pipeline_result.best_actions
                                    ),
                                    "issued_in_best": (
                                        _action_name_from_mask(decision.mask)
                                        in pipeline_result.best_actions
                                    ),
                                }
                                if pipeline_result is not None
                                else None
                            ),
                            "retarget": (
                                {
                                    "status": (
                                        pipeline_prewarm_retarget.status
                                    ),
                                    "revision": (
                                        pipeline_prewarm_retarget.revision
                                    ),
                                    "root_count": (
                                        pipeline_prewarm_retarget.root_count
                                    ),
                                    "candidate_root_count": (
                                        pipeline_prewarm_retarget
                                        .candidate_root_count
                                    ),
                                    "elapsed_ms": (
                                        pipeline_prewarm_retarget.elapsed_ms
                                    ),
                                }
                                if pipeline_prewarm_retarget is not None
                                else None
                            ),
                            "service": (
                                {
                                    "worker_count": (
                                        pipeline_service.worker_count
                                    ),
                                    "background_low_priority": (
                                        pipeline_service
                                        .background_low_priority
                                    ),
                                    "submitted_revision": (
                                        pipeline_service
                                        .submitted_revision
                                    ),
                                    "completed_revision": (
                                        pipeline_service
                                        .completed_revision
                                    ),
                                    "ready_revision": (
                                        pipeline_service.ready_revision
                                    ),
                                    "target_running": (
                                        pipeline_service.target_running
                                    ),
                                    "target_queued": (
                                        pipeline_service.target_queued
                                    ),
                                    "target_replacement_count": (
                                        pipeline_service
                                        .target_replacement_count
                                    ),
                                    "lookup_count": (
                                        pipeline_service.lookup_count
                                    ),
                                    "lookup_hit_count": (
                                        pipeline_service.lookup_hit_count
                                    ),
                                    "lookup_miss_count": (
                                        pipeline_service.lookup_miss_count
                                    ),
                                    "created_elapsed_ms": (
                                        pipeline_service.created_elapsed_ms
                                    ),
                                    "latest_outcome": (
                                        {
                                            "revision": (
                                                latest_outcome.revision
                                            ),
                                            "root_count": (
                                                latest_outcome.root_count
                                            ),
                                            "seed_count": (
                                                latest_outcome.seed_count
                                            ),
                                            "status": latest_outcome.status,
                                            "enumeration_ms": (
                                                latest_outcome
                                                .enumeration_ms
                                            ),
                                            "seed_ms": (
                                                latest_outcome.seed_ms
                                            ),
                                            "specialization_ms": (
                                                latest_outcome
                                                .specialization_ms
                                            ),
                                            "elapsed_ms": (
                                                latest_outcome.elapsed_ms
                                            ),
                                            "error": latest_outcome.error,
                                        }
                                        if latest_outcome is not None
                                        else None
                                    ),
                                    "seed_submitted": (
                                        scheduler_snapshot.seed_submitted
                                        if scheduler_snapshot is not None
                                        else 0
                                    ),
                                    "seed_completed": (
                                        scheduler_snapshot.seed_completed
                                        if scheduler_snapshot is not None
                                        else 0
                                    ),
                                    "seed_ready": (
                                        scheduler_snapshot.seed_ready
                                        if scheduler_snapshot is not None
                                        else False
                                    ),
                                }
                                if pipeline_service is not None
                                else None
                            ),
                        }
                    corridor_record["pending_command"] = (
                        {
                            "desired_action": _action_name_from_mask(
                                pending_command_estimate.expected_mask
                            ),
                            "remaining_frames": (
                                pending_command_estimate.remaining_frames
                            ),
                            "snapshot_age": (
                                pending_command_estimate.snapshot_age
                            ),
                            "issue_age": (
                                pending_command_estimate.issue_age
                            ),
                            "overdue": pending_command_estimate.overdue,
                        }
                        if pending_command_estimate is not None
                        else None
                    )
                    if safety_value_query is not None:
                        assert corridor_solution is not None
                        safety_policy = (
                            corridor_solution.plan.safety_value_policy
                        )
                        assert safety_policy is not None
                        corridor_record["safety_value"] = {
                            "query_frame": counter_after_read,
                            "age": (
                                counter_after_read
                                - corridor_solution.source_frame
                            ),
                            "layer": safety_value_query.layer,
                            "available": safety_value_query.available,
                            "active_action": (
                                safety_value_query.active_action
                            ),
                            "state_value": safety_value_query.state_value,
                            "best_actions": (
                                safety_value_query.best_actions
                            ),
                            "selected_action": decision.action,
                            "selected_preferred": (
                                decision.viability_safety_value_preferred
                            ),
                            "position_error": (
                                safety_value_query.position_error
                            ),
                            "horizon_frames": (
                                safety_policy.horizon_frames
                            ),
                            "guidance_active": bool(
                                policy_guidance.safety_actions
                            ),
                            "reason": safety_value_query.reason,
                        }
                    if corridor_report_solution.plan.gate is not None:
                        corridor_record["gate"] = {
                            "frame": corridor_report_solution.plan.gate.frame,
                            "x": corridor_report_solution.plan.gate.x,
                            "y": corridor_report_solution.plan.gate.y,
                            "clearance": (
                                corridor_report_solution.plan.gate.clearance
                            ),
                        }
                    if corridor_target is not None:
                        travel_frames = _minimum_travel_frames(
                            control_origin_x,
                            control_origin_y,
                            corridor_target[0],
                            corridor_target[1],
                        )
                        corridor_record["target"] = {
                            "x": corridor_target[0],
                            "y": corridor_target[1],
                            "deadline": corridor_target[2],
                            "travel_frames": travel_frames,
                            "slack": corridor_target[2] - travel_frames,
                        }
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
                trace_started = time.perf_counter()
                output.write(json.dumps(record) + "\n")
                output.flush()
                trace_ms = (time.perf_counter() - trace_started) * 1000.0
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
            output,
            last_frame=previous_counter,
            counter_gaps=gaps,
            hit_count=hit_count,
            termination_reason=termination_reason,
        )
        return 0
    except OSError as exc:
        termination_reason = "process_unreadable"
        output.write(
            json.dumps(
                {
                    "kind": "runtime_error",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "last_frame": previous_counter,
                }
            )
            + "\n"
        )
        _write_run_summary(
            output,
            last_frame=previous_counter,
            counter_gaps=gaps,
            hit_count=hit_count,
            termination_reason=termination_reason,
        )
        return 0
    except Exception as exc:
        termination_reason = "agent_error"
        output.write(
            json.dumps(
                {
                    "kind": "runtime_error",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "last_frame": previous_counter,
                }
            )
            + "\n"
        )
        _write_run_summary(
            output,
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
                if corridor_future is not None:
                    corridor_future.cancel()
                if corridor_survival_future is not None:
                    corridor_survival_future.cancel()
                if survival_executor is not None:
                    survival_executor.shutdown(
                        wait=True,
                        cancel_futures=True,
                    )
                if candidate_verifier is not None:
                    candidate_verifier.close()
                if corridor_executor is not None:
                    corridor_executor.shutdown(wait=True, cancel_futures=True)
                if (
                    corridor_future is not None
                    and corridor_future.done()
                    and not corridor_future.cancelled()
                ):
                    try:
                        retire_pipeline_solutions(
                            (corridor_future.result(),)
                        )
                    except Exception:
                        pass
                if pipeline_retire_executor is not None:
                    pipeline_retire_executor.shutdown(
                        wait=True,
                        cancel_futures=False,
                    )
                if audit_executor is not None:
                    audit_executor.shutdown(wait=True)
                if enemy_future is not None:
                    enemy_future.cancel()
                if enemy_executor is not None:
                    enemy_executor.shutdown(wait=True, cancel_futures=True)
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
