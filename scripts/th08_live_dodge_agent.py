#!/usr/bin/env python3
"""Live TH08 route-2 reactive dodge controller using native pool memory.

The controller is a receding-horizon smoke agent, not the final global solver.
It reads game state and projectile pools, then uses physical ``SendInput``
events. It never writes target memory and aborts on identity, route, gameplay,
or foreground-window divergence.
"""

from __future__ import annotations

import argparse
import json
import math
import struct
import time
from collections import deque
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np

from corridor_planner import CorridorPlan
from runtime_agent import input_transitions
from th08_bullet_transform_model import (
    BulletTransformRuntime,
    TransformRecord,
    parse_next_transform_record,
)
from th08_corridor_adapter import TH08_CORRIDOR_CONFIG, plan_th08_corridor
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
    laser_collision_geometry_frames,
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
    Win32,
    _require_foreground,
    observe_state,
    release_injected_keys,
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
from touhou_control.epochs import FrameWindow, HazardEpochAlignment
from touhou_control.trajectory import VelocityChange
from touhou_control.viability import ViabilityQuery


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

ENEMY_VELOCITY_OFFSET = 0x2D4C
ENEMY_CONTACT_SIZE_OFFSET = 0x2D70
ENEMY_POSITION_OFFSET = 0x2D88
ENEMY_FLAGS_OFFSET = 0x3324
ENEMY_POOL_BASE = 0x005826C0
ENEMY_POOL_SIZE = 480
ENEMY_STRIDE = 0x53D0
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
# A rolling async policy can outlive several estimator updates. Cover the
# complete configured support instead of assuming only one-step drift.
ASYNC_POLICY_DELAY_PADDING = (
    LIVE_CONTROL_DELAY_MAX - LIVE_CONTROL_DELAY_MIN
)
ENEMY_SENSOR_INTERVAL_FRAMES = 4
COLLECTION_HALF_WIDTH = 24.0
ITEM_SAFETY_CLEARANCE = 8.0
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
CORRIDOR_MIN_COMMIT_FRAMES = 32
CORRIDOR_INITIAL_SUBMIT_FRAME = -1_000_000
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
    """Retain legacy geometry plus optional native transform runtime.

    Fields 0..7 are the stable historical trace contract. Field 8 is either
    null or a compact transform payload:

    ``[speed, angle, original_flags, queue_cursor, next_record,
    timer_fraction, timer_elapsed, duration, resume_speed, angle_operand,
    repeat_limit, repeat_count, callback_phase_state, callback_aux_state,
    velocity_changes, trajectory_uncertainty_x,
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
class Laser:
    origin_x: float
    origin_y: float
    angle: float
    tail: float
    head: float
    half_width: float
    state: LaserState | None = None
    slot: int = -1
    collision_flag: int = 0
    uncertainty: float = 0.0


def serialize_laser_trace(laser: Laser) -> list[float | int | None]:
    """Retain enough native lifecycle state for offline reprojection."""

    state = laser.state
    return [
        laser.origin_x,
        laser.origin_y,
        laser.angle,
        laser.tail,
        laser.head,
        laser.half_width,
        laser.slot,
        state.maximum_length if state is not None else None,
        state.width if state is not None else None,
        state.current_width if state is not None else None,
        state.speed if state is not None else None,
        int(state.phase) if state is not None else None,
        state.timer if state is not None else None,
        state.flags if state is not None else None,
        laser.collision_flag,
        state.warmup_frames if state is not None else None,
        state.collision_enable_frame if state is not None else None,
        state.active_frames if state is not None else None,
        state.fade_frames if state is not None else None,
        state.collision_disable_frame if state is not None else None,
        state.timer_fraction if state is not None else None,
        laser.uncertainty,
    ]


@dataclass(frozen=True)
class _PackedLaserFrame:
    start_x: np.ndarray
    start_y: np.ndarray
    segment_x: np.ndarray
    segment_y: np.ndarray
    collision_radius: np.ndarray
    base_uncertainty: np.ndarray


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


@dataclass(frozen=True)
class EnemyPoolSnapshot:
    frame_before: int
    frame_after: int
    bodies: tuple[EnemyBody, ...]
    read_ms: float

    @property
    def stable(self) -> bool:
        return self.frame_before == self.frame_after


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


@dataclass(frozen=True)
class Decision:
    mask: int
    action: str
    min_clearance: float
    immediate_clearance: float
    score: float
    bomb: bool
    item_utility: float = 0.0
    planned_focus: bool = True
    predicted_collections: tuple[int, ...] = ()
    pipeline_clearance: float = 9999.0
    robust_delay_frames: tuple[int, ...] = ()
    robust_override: bool = False
    robust_collisions: int = 0
    robust_min_clearance: float = 9999.0
    robust_cvar_risk: float = 0.0
    robust_worst_delay: int | None = None
    viability_constrained: bool = False
    viability_safe_action_count: int = 0
    viability_repair_volume: int = 0
    viability_constraint_relaxed: bool = False
    terminal_threat_horizon: int = 0
    terminal_threat_collisions: int = 0
    terminal_threat_min_clearance: float = 9999.0
    viability_recovery_distance: float | None = None
    viability_control_reserve_deficit: float = 0.0


@dataclass(frozen=True)
class PlannerAction:
    name: str
    direction: int
    dx: float
    dy: float
    focused: bool


@dataclass(frozen=True)
class RobustActionCertificate:
    action: str
    delay_frames: tuple[int, ...]
    worst_collisions: int
    min_clearance: float
    cvar_risk: float
    worst_delay: int


@dataclass(frozen=True)
class SearchNode:
    x: float
    y: float
    first_action: PlannerAction
    last_action: PlannerAction
    risk: float
    collisions: int
    min_clearance: float
    immediate_clearance: float
    collected_mask: int
    item_utility: float


@dataclass(frozen=True)
class CorridorSolution:
    source_frame: int
    plan: CorridorPlan
    solve_ms: float
    snapshot_frame: int | None = None
    forecast_lead_frames: int = 0
    required_gate_lane: str | None = None
    constraint_honored: bool = False
    context_key: tuple[int, int, int | None] | None = None


@dataclass
class CorridorCommitment:
    """Retain a viable gate component across asynchronous replans."""

    lane: str | None = None
    expires_frame: int = -1
    context_key: tuple[int, int, int | None] | None = None

    def set_context(
        self,
        context_key: tuple[int, int, int | None],
    ) -> bool:
        if self.context_key == context_key:
            return False
        self.context_key = context_key
        self.lane = None
        self.expires_frame = -1
        return True

    def active_lane(self, frame: int) -> str | None:
        if self.lane is None or frame >= self.expires_frame:
            return None
        return self.lane

    def accept(self, solution: CorridorSolution, *, current_frame: int) -> None:
        if not solution.plan.reachable or solution.plan.gate is None:
            return
        active_lane = self.active_lane(current_frame)
        if (
            active_lane is not None
            and (
                (
                    solution.required_gate_lane == active_lane
                    and solution.constraint_honored
                )
                or solution.plan.lane == active_lane
            )
        ):
            return
        if active_lane is None and solution.required_gate_lane is not None:
            self.lane = None
            self.expires_frame = -1
            return
        self.lane = solution.plan.lane
        self.expires_frame = max(
            current_frame + CORRIDOR_MIN_COMMIT_FRAMES,
            solution.source_frame + solution.plan.gate.frame,
        )


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


def _finite(values: tuple[float, ...]) -> bool:
    return all(math.isfinite(value) for value in values)


def decode_bullets(blob: bytes) -> tuple[Bullet, ...]:
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
        if not _finite((x, y, vx, vy, width, height)):
            continue
        half_width = min(max(abs(width) * 0.5, 1.0), 24.0)
        half_height = min(max(abs(height) * 0.5, 1.0), 24.0)
        transform_runtime = None
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
        tag_flags = runtime.original_flags if runtime is not None else 0
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


def decode_enemy_body(blob: bytes, *, pointer: int) -> EnemyBody | None:
    if len(blob) < ENEMY_BODY_READ_SIZE:
        raise ValueError(
            f"enemy body window requires {ENEMY_BODY_READ_SIZE} bytes"
        )
    velocity_offset = ENEMY_VELOCITY_OFFSET - ENEMY_BODY_READ_OFFSET
    contact_offset = ENEMY_CONTACT_SIZE_OFFSET - ENEMY_BODY_READ_OFFSET
    position_offset = ENEMY_POSITION_OFFSET - ENEMY_BODY_READ_OFFSET
    flags_offset = ENEMY_FLAGS_OFFSET - ENEMY_BODY_READ_OFFSET
    vx, vy = struct.unpack_from("<ff", blob, velocity_offset)
    contact_width, contact_height = struct.unpack_from(
        "<ff",
        blob,
        contact_offset,
    )
    x, y = struct.unpack_from("<ff", blob, position_offset)
    flags = struct.unpack_from("<I", blob, flags_offset)[0]
    if (
        not flags & ENEMY_ACTIVE_FLAG
        or not flags & ENEMY_CONTACT_ENABLED_FLAG
        or flags & ENEMY_CONTACT_BLOCKING_FLAGS
    ):
        return None
    if not _finite((x, y, vx, vy, contact_width, contact_height)):
        return None
    if contact_width < 0.0 or contact_height < 0.0:
        return None
    return EnemyBody(
        pointer=pointer,
        x=x,
        y=y,
        vx=vx,
        vy=vy,
        # Native path: full contact size * 1.5, then center +/- size/2.
        half_width=0.75 * contact_width,
        half_height=0.75 * contact_height,
        flags=flags,
    )


def decode_enemy_bodies(blob: bytes) -> tuple[EnemyBody, ...]:
    """Decode every contact-enabled slot from the native 480-enemy pool."""

    expected_size = ENEMY_POOL_SIZE * ENEMY_STRIDE
    if len(blob) < expected_size:
        raise ValueError(
            f"enemy pool requires {expected_size} bytes"
        )
    bodies: list[EnemyBody] = []
    for slot in range(ENEMY_POOL_SIZE):
        base = slot * ENEMY_STRIDE
        flags = struct.unpack_from(
            "<I",
            blob,
            base + ENEMY_FLAGS_OFFSET,
        )[0]
        if (
            not flags & ENEMY_ACTIVE_FLAG
            or not flags & ENEMY_CONTACT_ENABLED_FLAG
            or flags & ENEMY_CONTACT_BLOCKING_FLAGS
        ):
            continue
        vx, vy = struct.unpack_from(
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
        if not _finite((x, y, vx, vy, contact_width, contact_height)):
            continue
        if contact_width < 0.0 or contact_height < 0.0:
            continue
        bodies.append(
            EnemyBody(
                pointer=ENEMY_POOL_BASE + base,
                x=x,
                y=y,
                vx=vx,
                vy=vy,
                half_width=0.75 * contact_width,
                half_height=0.75 * contact_height,
                flags=flags,
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
    age = max(0, frame - snapshot.frame_after)
    uncertainty = min(16.0, 0.75 * age)
    return tuple(
        replace(
            body,
            x=body.x + body.vx * age,
            y=body.y + body.vy * age,
            uncertainty=body.uncertainty + uncertainty,
        )
        for body in snapshot.bodies
    )


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
) -> list[list[float | int]]:
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
    bullets: tuple[Bullet, ...], *, horizon: int, snapshot_lag: int
) -> tuple[tuple[np.ndarray, ...], ...]:
    frames: list[tuple[np.ndarray, ...]] = []
    base_x = np.fromiter((bullet.x for bullet in bullets), dtype=np.float32)
    base_y = np.fromiter((bullet.y for bullet in bullets), dtype=np.float32)
    velocity_x = np.fromiter((bullet.vx for bullet in bullets), dtype=np.float32)
    velocity_y = np.fromiter((bullet.vy for bullet in bullets), dtype=np.float32)
    half_width = np.fromiter((bullet.half_width for bullet in bullets), dtype=np.float32)
    half_height = np.fromiter((bullet.half_height for bullet in bullets), dtype=np.float32)
    trajectory_uncertainty_x = np.fromiter(
        (bullet.trajectory_uncertainty_x for bullet in bullets),
        dtype=np.float32,
    )
    trajectory_uncertainty_y = np.fromiter(
        (bullet.trajectory_uncertainty_y for bullet in bullets),
        dtype=np.float32,
    )
    half_width = half_width + trajectory_uncertainty_x
    half_height = half_height + trajectory_uncertainty_y
    transformed = np.fromiter(
        (bool(bullet.transform_flags) for bullet in bullets), dtype=np.bool_
    )
    event_indices: list[int] = []
    event_frames: list[int] = []
    event_delta_x: list[float] = []
    event_delta_y: list[float] = []
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


def build_laser_collision_frames(
    lasers: tuple[Laser, ...],
    *,
    horizon: int,
    snapshot_lag: int = 0,
) -> tuple[tuple[Laser, ...], ...]:
    """Project allocated records into the lethal segments for each update."""

    if horizon < 0 or snapshot_lag < 0:
        raise ValueError("laser projection horizon and lag cannot be negative")
    frames: list[list[Laser]] = [[] for _ in range(horizon)]
    total_frames = snapshot_lag + horizon
    for laser in lasers:
        state = laser.state
        if state is None:
            for projected in frames:
                projected.append(laser)
            continue
        geometry_frames = laser_collision_geometry_frames(
            state,
            frame_count=total_frames,
        )[snapshot_lag:]
        for projected, geometry in zip(frames, geometry_frames):
            projected.extend(
                Laser(
                    origin_x=state.origin_x,
                    origin_y=state.origin_y,
                    angle=state.angle,
                    tail=tail,
                    head=head,
                    half_width=half_width,
                    slot=laser.slot,
                    collision_flag=laser.collision_flag,
                    uncertainty=laser.uncertainty,
                )
                for tail, head, half_width in geometry
            )
    return tuple(tuple(frame) for frame in frames)


def _pack_laser_frame(
    lasers: tuple[Laser, ...],
) -> _PackedLaserFrame:
    angle = np.fromiter(
        (laser.angle for laser in lasers),
        dtype=np.float64,
        count=len(lasers),
    )
    tail = np.fromiter(
        (laser.tail for laser in lasers),
        dtype=np.float64,
        count=len(lasers),
    )
    head = np.fromiter(
        (laser.head for laser in lasers),
        dtype=np.float64,
        count=len(lasers),
    )
    cosine = np.cos(angle)
    sine = np.sin(angle)
    origin_x = np.fromiter(
        (laser.origin_x for laser in lasers),
        dtype=np.float64,
        count=len(lasers),
    )
    origin_y = np.fromiter(
        (laser.origin_y for laser in lasers),
        dtype=np.float64,
        count=len(lasers),
    )
    return _PackedLaserFrame(
        start_x=origin_x + cosine * tail,
        start_y=origin_y + sine * tail,
        segment_x=cosine * (head - tail),
        segment_y=sine * (head - tail),
        collision_radius=np.fromiter(
            (
                laser.half_width + PLAYER_RADIUS
                for laser in lasers
            ),
            dtype=np.float64,
            count=len(lasers),
        ),
        base_uncertainty=np.fromiter(
            (
                laser.uncertainty
                for laser in lasers
            ),
            dtype=np.float64,
            count=len(lasers),
        ),
    )


def _hazards_for_positions(
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
            collisions += (clearance <= 0.0).sum(axis=1, dtype=np.int32)
            uncertainty = 0.2 * math.sqrt(step) + transformed.astype(np.float32) * min(
                10.0, 3.0 + 0.35 * step
            )
            robust_clearance = clearance - uncertainty[None, :]
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
            + min(6.0, 0.08 * step)
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
            collisions += (clearance <= 0.0).sum(
                axis=1,
                dtype=np.int32,
            )
            robust_clearance = clearance - uncertainty[None, :]
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
        laser_frames = tuple(
            _pack_laser_frame(frame)
            for frame in build_laser_collision_frames(
                lasers,
                horizon=frames,
            )
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
) -> dict[str, RobustActionCertificate]:
    """Certify the emitted action until the following command can take effect."""

    if not actions or not delay_frames:
        return {}
    maximum_step = action_hold_frames + max(delay_frames)
    bullet_frames = _build_bullet_frames(
        bullets,
        horizon=maximum_step,
        snapshot_lag=-max(0, snapshot_lag),
    )
    if laser_frames is None:
        laser_frames = tuple(
            _pack_laser_frame(frame)
            for frame in build_laser_collision_frames(
                lasers,
                horizon=maximum_step,
            )
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
    utility = usable_item_utility + 0.18 * potential
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
        node.risk - 6.0 * utility,
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
    viability_position_error: float = 0.0,
    recovery_control_reserve: bool = True,
    relax_stale_viability_contradiction: bool = False,
    _force_terminal_threat: bool = False,
    _viability_retry: bool = False,
) -> Decision:
    if horizon <= 0 or beam_width <= 0:
        raise ValueError("planner horizon and beam width must be positive")
    if threat_horizon is None:
        threat_horizon = horizon
    if threat_horizon < horizon:
        raise ValueError("threat horizon cannot be shorter than planner horizon")
    if control_delay_frames < 0:
        raise ValueError("control delay cannot be negative")
    if control_delay_candidates is not None:
        if (
            not control_delay_candidates
            or any(delay < 0 for delay in control_delay_candidates)
            or tuple(sorted(set(control_delay_candidates)))
            != control_delay_candidates
        ):
            raise ValueError(
                "control delay candidates must be sorted unique nonnegative frames"
            )
        if control_delay_frames not in control_delay_candidates:
            raise ValueError("nominal control delay must belong to its candidates")
    if action_hold_frames <= 0:
        raise ValueError("action hold must be positive")
    if (
        not math.isfinite(viability_position_error)
        or viability_position_error < 0.0
    ):
        raise ValueError("viability position error must be finite and nonnegative")
    planner_action_names = {action.name for action in _PLANNER_ACTIONS}
    if allowed_first_actions is not None:
        if not allowed_first_actions:
            raise ValueError("allowed first actions cannot be empty")
        if len(set(allowed_first_actions)) != len(allowed_first_actions):
            raise ValueError("allowed first actions must be unique")
        unknown_actions = set(allowed_first_actions) - planner_action_names
        if unknown_actions:
            raise ValueError(
                f"unknown allowed first actions: {sorted(unknown_actions)}"
            )
    viability_degeneracy = (
        _terminal_threat_degeneracy(
            player_x=player_x,
            player_y=player_y,
            action_hold_frames=action_hold_frames,
            allowed_first_actions=allowed_first_actions,
            viability_position_error=viability_position_error,
        )
        if threat_horizon > horizon
        else None
    )
    viability_relaxation_candidate = viability_degeneracy is not None
    repair_by_action = dict(viability_repair_volumes)
    if len(repair_by_action) != len(viability_repair_volumes):
        raise ValueError("viability repair action names must be unique")
    if set(repair_by_action) - planner_action_names:
        raise ValueError("viability repair contains unknown action")
    if any(volume < 0 for volume in repair_by_action.values()):
        raise ValueError("viability repair volume cannot be negative")
    recovery_by_action = dict(viability_recovery_distances)
    if len(recovery_by_action) != len(viability_recovery_distances):
        raise ValueError("viability recovery action names must be unique")
    if set(recovery_by_action) - planner_action_names:
        raise ValueError("viability recovery contains unknown action")
    if any(
        not math.isfinite(distance) or distance < 0.0
        for distance in recovery_by_action.values()
    ):
        raise ValueError(
            "viability recovery distance must be finite and nonnegative"
        )
    if (target_x is None) != (target_y is None):
        raise ValueError("target_x and target_y must be supplied together")
    if target_x is not None:
        if target_deadline is None:
            target_deadline = horizon
        if target_deadline < 0:
            raise ValueError("target deadline cannot be negative")
    observed_player_x = player_x
    observed_player_y = player_y
    selected_items = _select_items(items, power=power, bombs=bombs)
    delayed_mask = previous_direction | (FOCUS if previous_focus else 0)
    main_laser_offset = max(
        0,
        control_delay_frames - max(0, snapshot_lag),
    )
    certificate_delay_frames = (
        control_delay_candidates
        if control_delay_candidates is not None
        else (control_delay_frames,)
    )
    diagnostic_recovery_reserve_distance = (
        UNFOCUSED_CARDINAL_SPEED * max(certificate_delay_frames)
        if recovery_by_action
        else 0.0
    )
    recovery_reserve_distance = (
        diagnostic_recovery_reserve_distance
        if recovery_control_reserve
        else 0.0
    )
    certificate_horizon = (
        action_hold_frames + max(certificate_delay_frames)
        if control_delay_candidates is not None or viability_relaxation_candidate
        else 0
    )
    potential_threat_horizon = (
        threat_horizon
        if viability_relaxation_candidate or _force_terminal_threat
        else horizon
    )
    laser_timeline_horizon = max(
        control_delay_frames,
        main_laser_offset + potential_threat_horizon,
        certificate_horizon,
    )
    laser_timeline = tuple(
        _pack_laser_frame(frame)
        for frame in build_laser_collision_frames(
            lasers,
            horizon=laser_timeline_horizon,
        )
    )
    viability_preflight_certificates: dict[
        str, RobustActionCertificate
    ] = {}
    if viability_degeneracy == "off_grid_singleton":
        assert allowed_first_actions is not None
        allowed_names = set(allowed_first_actions)
        allowed_actions = tuple(
            action
            for action in _PLANNER_ACTIONS
            if action.name in allowed_names
        )
        viability_preflight_certificates = _robust_action_certificates(
            player_x=observed_player_x,
            player_y=observed_player_y,
            previous_mask=delayed_mask,
            actions=allowed_actions,
            delay_frames=certificate_delay_frames,
            action_hold_frames=action_hold_frames,
            bullets=bullets,
            lasers=lasers,
            enemy_bodies=enemy_bodies,
            snapshot_lag=snapshot_lag,
            laser_frames=laser_timeline[:certificate_horizon],
        )
    viability_constraint_relaxed = (
        viability_degeneracy == "complete_clamped_alias"
        or (
            viability_degeneracy == "off_grid_singleton"
            and not any(
                certificate.worst_collisions == 0
                and certificate.min_clearance >= 0.0
                and repair_by_action.get(action_name, 0) > 1
                for action_name, certificate
                in viability_preflight_certificates.items()
            )
        )
    )
    effective_allowed_first_actions = (
        None if viability_constraint_relaxed else allowed_first_actions
    )
    effective_threat_horizon = potential_threat_horizon
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
    player_x, player_y = _project_player_for_read_lag(
        player_x,
        player_y,
        delayed_mask,
        control_delay_frames,
    )
    bullet_frames = _build_bullet_frames(
        bullets,
        horizon=effective_threat_horizon,
        snapshot_lag=max(
            0,
            control_delay_frames - max(0, snapshot_lag),
        ),
    )
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
        return (
            base[0],
            base[1],
            base[2],
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
    ):
        return Decision(
            SHOT | FOCUS,
            "stay",
            9999.0,
            9999.0,
            0.0,
            False,
            robust_delay_frames=control_delay_candidates or (),
        )
    for step in range(1, horizon + 1):
        drafts: list[
            tuple[SearchNode, PlannerAction, float, float, float, int, float]
        ] = []
        draft_first_actions: list[PlannerAction] = []
        candidates: dict[tuple[int, int, int, bool, int], SearchNode] = {}
        for node in beam:
            actions = (
                _PLANNER_ACTIONS
                if (step - 1) % action_hold_frames == 0
                else (node.last_action,)
            )
            if step == 1 and effective_allowed_first_actions is not None:
                allowed = set(effective_allowed_first_actions)
                actions = tuple(
                    action for action in actions if action.name in allowed
                )
            for action in actions:
                x = min(
                    PLAYFIELD_RIGHT,
                    max(PLAYFIELD_LEFT, node.x + action.dx),
                )
                y = min(
                    PLAYFIELD_BOTTOM,
                    max(PLAYFIELD_TOP, node.y + action.dy),
                )
                transition_risk = 0.0
                transition_risk += _boundary_risk(x, y)
                if action.direction != node.last_action.direction:
                    transition_risk += 0.08
                if _directions_opposed(action.direction, node.last_action.direction):
                    transition_risk += 24.0
                if action.focused != node.last_action.focused:
                    transition_risk += 0.12
                if step == 1:
                    if action.direction != previous_direction:
                        transition_risk += 0.08
                    if _directions_opposed(action.direction, previous_direction):
                        transition_risk += 24.0
                    if action.focused != previous_focus:
                        transition_risk += 0.12
                collected_mask = node.collected_mask
                item_utility = node.item_utility
                for index, (item, value) in enumerate(selected_items):
                    bit = 1 << index
                    if collected_mask & bit:
                        continue
                    item_x, item_y, confidence = _project_item(item, step)
                    collection_allowed = item.motion_state != 3 and not (
                        item.motion_state == 5 and item.vy <= 0.0
                    )
                    if (
                        collection_allowed
                        and abs(x - item_x) <= COLLECTION_HALF_WIDTH
                        and abs(y - item_y) <= COLLECTION_HALF_WIDTH
                    ):
                        collected_mask |= bit
                        item_utility += value * confidence
                first_action = action if step == 1 else node.first_action
                drafts.append(
                    (
                        node,
                        action,
                        x,
                        y,
                        transition_risk,
                        collected_mask,
                        item_utility,
                    )
                )
                draft_first_actions.append(first_action)
        if not drafts:
            break
        positions_x = np.fromiter((draft[2] for draft in drafts), dtype=np.float32)
        positions_y = np.fromiter((draft[3] for draft in drafts), dtype=np.float32)
        hazard_risk, hazard_collisions, hazard_clearance = _hazards_for_positions(
            positions_x,
            positions_y,
            step=control_delay_frames + step,
            bullet_frame=bullet_frames[step - 1],
            lasers=laser_frames[step - 1],
            enemy_bodies=enemy_bodies,
        )
        for draft_index, draft in enumerate(drafts):
            node, action, x, y, transition_risk, collected_mask, item_utility = draft
            clearance = float(hazard_clearance[draft_index])
            first_action = draft_first_actions[draft_index]
            candidate = SearchNode(
                x=x,
                y=y,
                first_action=first_action,
                last_action=action,
                risk=node.risk + transition_risk + float(hazard_risk[draft_index]),
                collisions=node.collisions + int(hazard_collisions[draft_index]),
                min_clearance=min(node.min_clearance, clearance),
                immediate_clearance=(
                    min(node.immediate_clearance, clearance)
                    if step == 1
                    else node.immediate_clearance
                ),
                collected_mask=collected_mask,
                item_utility=item_utility,
            )
            quantized = (
                int(round(x * 0.5)),
                int(round(y * 0.5)),
                action.direction,
                action.focused,
                collected_mask,
            )
            incumbent = candidates.get(quantized)
            if incumbent is None or pruning_key(
                candidate,
                step=step,
            ) < pruning_key(incumbent, step=step):
                candidates[quantized] = candidate
        if not candidates:
            break
        beam = sorted(
            candidates.values(),
            key=lambda node: pruning_key(node, step=step),
        )[:beam_width]

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
    terminal_threats = _terminal_threat_scores(
        beam,
        start_step=horizon,
        end_step=effective_threat_horizon,
        control_delay_frames=control_delay_frames,
        bullet_frames=bullet_frames,
        laser_frames=laser_frames,
        enemy_bodies=enemy_bodies,
    )

    def selection_key(node: SearchNode) -> tuple[object, ...]:
        threat_collisions, threat_clearance = terminal_threats[node]
        return (
            node.collisions,
            max(-node.min_clearance, 0.0),
            threat_collisions,
            max(-threat_clearance, 0.0),
            max(ITEM_SAFETY_CLEARANCE - threat_clearance, 0.0),
            _boundary_control_reserve_deficit(
                node.x,
                node.y,
                reserve_distance=recovery_reserve_distance,
            ),
            recovery_by_action.get(node.first_action.name, math.inf),
            -repair_by_action.get(node.first_action.name, 0),
            _node_key(
                node,
                step=horizon,
                selected_items=selected_items,
                target_x=target_x,
                target_y=target_y,
                target_deadline=target_deadline,
            ),
        )

    best = min(
        beam,
        key=selection_key,
    )
    robust_certificates: dict[str, RobustActionCertificate] = {}
    robust_override = False
    robust_certificate: RobustActionCertificate | None = None
    if control_delay_candidates is not None:
        nodes_by_action: dict[str, SearchNode] = {}
        actions_by_name: dict[str, PlannerAction] = {}
        for node in beam:
            action_name = node.first_action.name
            actions_by_name[action_name] = node.first_action
            incumbent = nodes_by_action.get(action_name)
            if incumbent is None or selection_key(node) < selection_key(
                incumbent
            ):
                nodes_by_action[action_name] = node
        if (
            viability_preflight_certificates
            and not viability_constraint_relaxed
            and actions_by_name.keys()
            <= viability_preflight_certificates.keys()
        ):
            robust_certificates = {
                action_name: viability_preflight_certificates[action_name]
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
            )
        nominal_certificate = robust_certificates[best.first_action.name]
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
                    robust_certificates[node.first_action.name].cvar_risk,
                    -robust_certificates[
                        node.first_action.name
                    ].min_clearance,
                    selection_key(node),
                ),
            )
            robust_override = robust_best.first_action != best.first_action
            best = robust_best
        robust_certificate = robust_certificates[best.first_action.name]
    minimum = 9999.0 if math.isinf(best.min_clearance) else best.min_clearance
    immediate = (
        9999.0 if math.isinf(best.immediate_clearance) else best.immediate_clearance
    )
    action = best.first_action
    use_bomb = can_bomb and (
        immediate <= 0.0
        or (
            robust_certificate is not None
            and robust_certificate.worst_collisions > 0
        )
    )
    direction_mask = action.direction
    focus_mask = FOCUS if action.focused else 0
    threat_collisions, threat_clearance = terminal_threats[best]
    predicted_collections = tuple(
        selected_items[index][0].slot
        for index in range(len(selected_items))
        if best.collected_mask & (1 << index)
    )
    pipeline_clearance = (
        9999.0 if math.isinf(prefix_clearance) else prefix_clearance
    )
    decision = Decision(
        SHOT | focus_mask | direction_mask | (BOMB if use_bomb else 0),
        action.name,
        minimum,
        immediate,
        best.risk,
        use_bomb,
        best.item_utility,
        action.focused,
        predicted_collections,
        pipeline_clearance,
        control_delay_candidates or (),
        robust_override,
        (
            robust_certificate.worst_collisions
            if robust_certificate is not None
            else 0
        ),
        (
            robust_certificate.min_clearance
            if robust_certificate is not None
            else 9999.0
        ),
        (
            robust_certificate.cvar_risk
            if robust_certificate is not None
            else 0.0
        ),
        (
            robust_certificate.worst_delay
            if robust_certificate is not None
            else None
        ),
        effective_allowed_first_actions is not None,
        len(allowed_first_actions or ()),
        repair_by_action.get(action.name, 0),
        viability_constraint_relaxed,
        effective_threat_horizon,
        threat_collisions,
        9999.0 if math.isinf(threat_clearance) else threat_clearance,
        recovery_by_action.get(action.name),
        _boundary_control_reserve_deficit(
            best.x,
            best.y,
            reserve_distance=diagnostic_recovery_reserve_distance,
        ),
    )
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
        retry = choose_action(
            player_x=observed_player_x,
            player_y=observed_player_y,
            bullets=bullets,
            lasers=lasers,
            previous_direction=previous_direction,
            can_bomb=can_bomb,
            enemy_bodies=enemy_bodies,
            items=items,
            power=power,
            bombs=bombs,
            previous_focus=previous_focus,
            snapshot_lag=snapshot_lag,
            control_delay_frames=control_delay_frames,
            control_delay_candidates=control_delay_candidates,
            action_hold_frames=action_hold_frames,
            horizon=horizon,
            threat_horizon=threat_horizon,
            beam_width=beam_width,
            target_x=target_x,
            target_y=target_y,
            target_deadline=target_deadline,
            allowed_first_actions=None,
            viability_repair_volumes=viability_repair_volumes,
            viability_recovery_distances=viability_recovery_distances,
            viability_position_error=viability_position_error,
            recovery_control_reserve=recovery_control_reserve,
            relax_stale_viability_contradiction=(
                relax_stale_viability_contradiction
            ),
            _force_terminal_threat=True,
            _viability_retry=True,
        )

        def contradiction_key(candidate: Decision) -> tuple[object, ...]:
            return (
                candidate.robust_collisions,
                max(-candidate.robust_min_clearance, 0.0),
                -candidate.robust_min_clearance,
                candidate.terminal_threat_collisions,
                max(
                    -candidate.terminal_threat_min_clearance,
                    0.0,
                ),
                max(-candidate.min_clearance, 0.0),
                candidate.score,
            )

        if contradiction_key(retry) < contradiction_key(decision):
            return replace(
                retry,
                viability_safe_action_count=len(
                    allowed_first_actions or ()
                ),
                viability_constraint_relaxed=True,
            )
    return decision


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


def _solve_corridor(
    *,
    source_frame: int,
    snapshot_frame: int,
    forecast_lead_frames: int,
    player_x: float,
    player_y: float,
    bullets: tuple[Bullet, ...],
    lasers: tuple[Laser, ...],
    enemy_bodies: tuple[EnemyBody, ...],
    snapshot_lag: int,
    control_delay_candidates: tuple[int, ...],
    nominal_control_delay: int,
    active_action: str,
    required_gate_lane: str | None = None,
    context_key: tuple[int, int, int | None] | None = None,
) -> CorridorSolution:
    started = time.perf_counter()
    plan = plan_th08_corridor(
        player_x=player_x,
        player_y=player_y,
        bullets=bullets,
        lasers=lasers,
        enemy_bodies=enemy_bodies,
        snapshot_lag=snapshot_lag,
        forecast_frames=forecast_lead_frames,
        required_gate_lane=required_gate_lane,
        control_delay_candidates=control_delay_candidates,
        nominal_control_delay=nominal_control_delay,
        active_action=active_action,
    )
    constraint_honored = (
        required_gate_lane is None
        or (plan.reachable and plan.lane == required_gate_lane)
    )
    if (
        required_gate_lane is not None
        and not constraint_honored
        and plan.planning_mode != "robust_viability"
    ):
        plan = plan_th08_corridor(
            player_x=player_x,
            player_y=player_y,
            bullets=bullets,
            lasers=lasers,
            enemy_bodies=enemy_bodies,
            snapshot_lag=snapshot_lag,
            forecast_frames=forecast_lead_frames,
            control_delay_candidates=control_delay_candidates,
            nominal_control_delay=nominal_control_delay,
            active_action=active_action,
        )
    return CorridorSolution(
        source_frame=source_frame,
        plan=plan,
        solve_ms=(time.perf_counter() - started) * 1000.0,
        snapshot_frame=snapshot_frame,
        forecast_lead_frames=forecast_lead_frames,
        required_gate_lane=required_gate_lane,
        constraint_honored=constraint_honored,
        context_key=context_key,
    )


def _corridor_target(
    solution: CorridorSolution | None,
    *,
    current_frame: int,
    lookahead_frames: int,
    max_age_frames: int,
) -> tuple[float, float, int] | None:
    if solution is None or not solution.plan.reachable:
        return None
    age = current_frame - solution.source_frame
    if age < 0 or age > max_age_frames:
        return None
    waypoint = solution.plan.waypoint(age + lookahead_frames)
    return waypoint.x, waypoint.y, max(waypoint.frame - age, 0)


def _corridor_viability_query(
    solution: CorridorSolution | None,
    *,
    current_frame: int,
    player_x: float,
    player_y: float,
    active_action: str,
    max_age_frames: int,
) -> ViabilityQuery | None:
    if solution is None or solution.plan.viability_policy is None:
        return None
    age = current_frame - solution.source_frame
    if age < 0 or age > max_age_frames:
        return None
    return solution.plan.viability_policy.query(
        frame=age,
        x=player_x,
        y=player_y,
        active_action=active_action,
    )


def _corridor_policy_status(
    solution: CorridorSolution | None,
    *,
    current_frame: int,
    max_age_frames: int,
) -> str:
    if solution is None or solution.plan.viability_policy is None:
        return "unavailable"
    age = current_frame - solution.source_frame
    if age < 0:
        return "pending_future_epoch"
    if age > max_age_frames:
        return "expired"
    if age >= solution.plan.viability_policy.horizon_frames:
        return "outside_policy_horizon"
    return "queryable"


def _stage_corridor_solution(
    active: CorridorSolution | None,
    candidate: CorridorSolution,
    *,
    current_frame: int,
    context_key: tuple[int, int, int | None],
) -> tuple[CorridorSolution | None, CorridorSolution | None]:
    """Keep the active policy until a matching future epoch is reached."""

    if candidate.context_key != context_key:
        return active, None
    if candidate.source_frame <= current_frame:
        return candidate, None
    return active, candidate


def _corridor_submit_due(
    *,
    current_frame: int,
    last_submit_frame: int,
    interval_frames: int,
) -> bool:
    return current_frame - last_submit_frame >= interval_frames


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


def run(args: argparse.Namespace) -> int:
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
    if (
        args.stage_transition_timeout <= 0.0
        or args.terminal_inactive_grace <= 0.0
    ):
        raise ValueError("scene transition timing arguments must be positive")
    api = Win32()
    pid = args.pid if args.pid is not None else api.find_pid(TARGET_EXE)
    reader = ProcessReader(api, pid)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output = args.output.open("w", encoding="utf-8", newline="\n")
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
    enemy_executor: ThreadPoolExecutor | None = None
    enemy_future: Future[EnemyPoolSnapshot] | None = None
    enemy_snapshot: EnemyPoolSnapshot | None = None
    enemy_last_submit = CORRIDOR_INITIAL_SUBMIT_FRAME
    corridor_solution: CorridorSolution | None = None
    corridor_pending_solution: CorridorSolution | None = None
    corridor_last_submit = CORRIDOR_INITIAL_SUBMIT_FRAME
    corridor_commitment = CorridorCommitment()
    corridor_context: tuple[int, int, int | None] | None = None
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
    enemy_executor = ThreadPoolExecutor(
        max_workers=1,
        thread_name_prefix="th08-enemy-sensor",
    )
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
                    "global_planner": (
                        "finite_horizon_robust_backward_viability"
                        if not args.local_only
                        else "disabled"
                    ),
                    "viability_grid_step": TH08_CORRIDOR_CONFIG.grid_step,
                    "viability_frames_per_layer": (
                        TH08_CORRIDOR_CONFIG.frames_per_layer
                    ),
                    "viability_horizon_frames": (
                        TH08_CORRIDOR_CONFIG.horizon_frames
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
                    "native_planner_backend": native_backend.available(),
                    "viability_quantifiers": (
                        "exists_action_forall_delay"
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
                    corridor_solution = None
                    corridor_pending_solution = None
                    if corridor_future is not None and corridor_future.cancel():
                        corridor_future = None
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
                corridor_solution = None
                corridor_pending_solution = None
                corridor_last_submit = CORRIDOR_INITIAL_SUBMIT_FRAME
                corridor_context = None
                corridor_commitment = CorridorCommitment()
                ecl_instruction_cache.clear()
                if corridor_future is not None and corridor_future.cancel():
                    corridor_future = None
                auto_confirm.eligible_since = None
                auto_confirm.released = False
                last_frame_progress = now
            if counter == previous_counter:
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
                    _require_foreground(api, pid)
                    send_scan_key(api, scan_code=0x2C, pressed=False)
                    time.sleep(0.04)
                    send_scan_key(api, scan_code=0x2C, pressed=True)
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
                            }
                        )
                        + "\n"
                    )
                    output.flush()
                time.sleep(args.poll_ms / 1000.0)
                continue
            last_frame_progress = time.perf_counter()
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
            if corridor_commitment.set_context(corridor_context):
                corridor_solution = None
                corridor_pending_solution = None
                if (
                    corridor_future is not None
                    and corridor_future.cancel()
                ):
                    corridor_future = None
            iterations += 1
            if iterations % 30 == 0:
                _require_foreground(api, pid)
            read_started = time.perf_counter()
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
            enemy_bodies = project_enemy_pool_snapshot(
                enemy_snapshot,
                frame=counter,
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
            bullet_frame_before = reader.u32(0x0164D30C)
            bullet_blob = reader.read(
                BULLET_POOL_BASE,
                BULLET_POOL_SIZE * BULLET_STRIDE,
            )
            bullet_frame_after = reader.u32(0x0164D30C)
            laser_blob = reader.read(LASER_POOL_BASE, LASER_POOL_SIZE * LASER_STRIDE)
            item_blob = reader.read(
                ITEM_MANAGER_BASE, ITEM_POOL_SIZE * ITEM_STRIDE
            )
            ecl_vm_snapshot: EclVmSnapshot | None = None
            ecl_lookahead: EclLookaheadResult | None = None
            tagged_velocity_toggles: tuple[TaggedVelocityToggle, ...] = ()
            ecl_lookahead_error: str | None = None
            ecl_frame_before: int | None = None
            ecl_frame_after: int | None = None
            spell_enemy_pointer = int(spell_state.get("enemy_pointer", 0))
            if spell_state.get("active") and spell_enemy_pointer:
                try:
                    ecl_frame_before = reader.u32(0x0164D30C)
                    ecl_vm_snapshot = read_main_ecl_vm_snapshot(
                        reader,
                        spell_enemy_pointer,
                    )
                    ecl_frame_after = reader.u32(0x0164D30C)
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
            counter_after_read = reader.u32(0x0164D30C)
            read_ms = (time.perf_counter() - read_started) * 1000.0
            if (
                bullet_frame_after < bullet_frame_before
                or counter_after_read < bullet_frame_after
                or (
                    ecl_frame_before is not None
                    and ecl_frame_after is not None
                    and ecl_frame_after < ecl_frame_before
                )
            ):
                gaps += 1
                continue
            snapshot_lag = max(0, counter_after_read - int(state["enemy_manager_frame"]))
            hazard_alignment = HazardEpochAlignment(
                source_frame=int(state["enemy_manager_frame"]),
                hazard_window=FrameWindow(
                    bullet_frame_before,
                    bullet_frame_after,
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
                corridor_solution = None
                corridor_pending_solution = None
                corridor_context = None
                corridor_commitment = CorridorCommitment()
                ecl_instruction_cache.clear()
                if corridor_future is not None:
                    corridor_future.cancel()
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
            bullets = decode_bullets(bullet_blob)
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
            lasers = decode_lasers(laser_blob)
            items = decode_items(item_blob)
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
            control_delay_frames = delay_estimate.nominal
            control_origin_x, control_origin_y = _project_player_for_read_lag(
                float(player["x"]),
                float(player["y"]),
                previous_mask,
                control_delay_frames,
            )
            corridor_started = time.perf_counter()
            corridor_updated = False
            if corridor_pending_solution is not None:
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
            if corridor_future is not None and corridor_future.done():
                completed_solution = corridor_future.result()
                corridor_future = None
                corridor_policy_lead.observe(completed_solution.solve_ms)
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
                    nominal_control_delay=control_delay_frames,
                    active_action=_action_name_from_mask(previous_mask),
                    required_gate_lane=(
                        corridor_commitment.active_lane(counter_after_read)
                    ),
                    context_key=corridor_context,
                )
                corridor_last_submit = counter_after_read
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
            viability_policy = (
                corridor_solution.plan.viability_policy
                if corridor_solution is not None
                else None
            )
            viability_support_covers_current = (
                viability_policy is not None
                and set(delay_estimate.support).issubset(
                    viability_policy.delay_frames
                )
            )
            viability_guidance = (
                viability_query
                if (
                    viability_query is not None
                    and viability_query.available
                    and viability_query.state_viable
                    and viability_query.safe_actions
                    and viability_support_covers_current
                )
                else None
            )
            viability_repair_guidance = (
                viability_query.repair_volumes
                if (
                    viability_query is not None
                    and viability_query.available
                    and viability_support_covers_current
                )
                else ()
            )
            viability_recovery_guidance = (
                viability_query.recovery_distances
                if (
                    viability_query is not None
                    and viability_query.available
                    and viability_support_covers_current
                )
                else ()
            )
            corridor_overhead_ms = (
                time.perf_counter() - corridor_started
            ) * 1000.0
            action_hold_frames = _estimate_live_action_hold(
                tuple(decision_frame_deltas)
            )
            plan_started = time.perf_counter()
            decision = choose_action(
                player_x=float(player["x"]),
                player_y=float(player["y"]),
                bullets=bullets,
                lasers=lasers,
                enemy_bodies=enemy_bodies,
                previous_direction=previous_direction,
                can_bomb=can_bomb,
                items=items,
                power=float(resources["power"]),
                bombs=float(resources["bombs"]),
                previous_focus=bool(previous_mask & FOCUS),
                snapshot_lag=player_to_hazard_lag,
                control_delay_frames=control_delay_frames,
                control_delay_candidates=delay_estimate.support,
                action_hold_frames=action_hold_frames,
                horizon=args.horizon,
                threat_horizon=args.threat_horizon,
                beam_width=args.beam_width,
                target_x=(
                    corridor_target[0] if corridor_target is not None else None
                ),
                target_y=(
                    corridor_target[1] if corridor_target is not None else None
                ),
                target_deadline=(
                    corridor_target[2] if corridor_target is not None else None
                ),
                allowed_first_actions=(
                    viability_guidance.safe_actions
                    if viability_guidance is not None
                    else None
                ),
                viability_repair_volumes=(
                    viability_repair_guidance
                ),
                viability_recovery_distances=(
                    viability_recovery_guidance
                ),
                viability_position_error=(
                    viability_guidance.position_error
                    if viability_guidance is not None
                    else 0.0
                ),
            )
            plan_ms = (time.perf_counter() - plan_started) * 1000.0
            phase_now = reader.u8(0x017D5EF8)
            predeath_now = reader.i32(0x017D5EF8 + 0xE2A68)
            counter_at_action = reader.u32(0x0164D30C)
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
            transitions = input_transitions(
                previous_mask,
                decision.mask,
                supported_mask=SUPPORTED_INPUT_MASK,
            )
            input_started = time.perf_counter()
            send_transitions(api, transitions)
            input_ms = (time.perf_counter() - input_started) * 1000.0
            if transitions:
                delay_estimator.issued(
                    snapshot_frame=int(state["enemy_manager_frame"]),
                    issue_frame=counter_at_action,
                    expected_mask=decision.mask,
                    support_high=delay_estimate.support[-1],
                )
            previous_mask = decision.mask
            previous_direction = decision.mask & (UP | DOWN | LEFT | RIGHT)
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
            ):
                ecl_tagged_bullets = (
                    tuple(
                        bullet
                        for bullet in bullets
                        if (
                            ecl_vm_snapshot is not None
                            and bullet.transform_runtime is not None
                            and (
                                bullet.transform_runtime.original_flags
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
                        "read_enemy_pool": enemy_pool_read_ms,
                        "decode_pools": decode_ms,
                        "corridor_bookkeeping": corridor_overhead_ms,
                        "local_plan": plan_ms,
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
                    "hazard_alignment": {
                        "bullet_frame_before": bullet_frame_before,
                        "bullet_frame_after": bullet_frame_after,
                        "bullet_capture_span": bullet_capture_span,
                        "hazard_snapshot_age": hazard_snapshot_age,
                        "player_to_hazard_lag": player_to_hazard_lag,
                        "ecl_frame_before": ecl_frame_before,
                        "ecl_frame_after": ecl_frame_after,
                    },
                    "enemy_body_snapshot_frame": enemy_body_snapshot_frame,
                    "enemy_body_snapshot_age": (
                        counter_after_read - enemy_body_snapshot_frame
                        if enemy_body_snapshot_frame is not None
                        else None
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
                        "reachable": corridor_report_solution.plan.reachable,
                        "planning_mode": (
                            corridor_report_solution.plan.planning_mode
                        ),
                        "viability_backend": (
                            corridor_report_solution.plan.viability_backend
                        ),
                        "solver_timing_ms": dict(
                            corridor_report_solution.plan.solver_timing_ms
                        ),
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
                            "selected_action": decision.action,
                            "selected_repair_volume": (
                                decision.viability_repair_volume
                            ),
                            "selected_recovery_distance": (
                                decision.viability_recovery_distance
                            ),
                            "position_error": (
                                viability_query.position_error
                            ),
                            "delay_frames": policy.delay_frames,
                            "current_delay_frames": (
                                delay_estimate.support
                            ),
                            "support_covers_current": (
                                viability_support_covers_current
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
            release_injected_keys(api)
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
                if corridor_future is not None:
                    corridor_future.cancel()
                if corridor_executor is not None:
                    corridor_executor.shutdown(wait=True, cancel_futures=True)
                if enemy_future is not None:
                    enemy_future.cancel()
                if enemy_executor is not None:
                    enemy_executor.shutdown(wait=True, cancel_futures=True)
            finally:
                output.close()
                reader.close()


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
        choices=(3, 4),
        default=3,
        help="required runtime difficulty index: 3 Lunatic, 4 Extra",
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
