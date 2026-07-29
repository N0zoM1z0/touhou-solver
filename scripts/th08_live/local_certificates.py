"""Fresh local hazard certificates over explicit actuator-pipeline roots."""

from __future__ import annotations

import math
import time
from collections.abc import Callable

import numpy as np

from th08_laser_runtime import (
    Laser,
    PackedLaserFrame as _PackedLaserFrame,
    build_packed_laser_collision_frames as _build_packed_laser_collision_frames,
)
from th08_ecl_vm_state import float32_from_bits
from th08_live.local_hazards import _build_bullet_frames
from th08_live.models import Bullet, EnemyBody
from th08_live.movement import (
    LOCAL_PIPELINE_STATE_ACTIONS as _LOCAL_PIPELINE_STATE_ACTIONS,
    PLAYFIELD_BOTTOM,
    PLAYFIELD_LEFT,
    PLAYFIELD_RIGHT,
    PLAYFIELD_TOP,
    boundary_risk as _boundary_risk,
    boundary_risk_for_positions as _boundary_risk_for_positions,
    local_pipeline_action_from_mask as _local_pipeline_action_from_mask,
    project_player_for_read_lag as _project_player_for_read_lag,
)
from th08_live.planner_pass_types import LocalCertificateTimingAccumulator
from th08_local_planner import PlannerAction, RobustActionCertificate
from touhou_control.local_pipeline_oracle import LocalPipelineRoot

HazardQuery = Callable[..., tuple[np.ndarray, np.ndarray, np.ndarray]]
_LocalCertificateTimingAccumulator = LocalCertificateTimingAccumulator


def control_prefix_hazards(
    *,
    hazards_for_positions: HazardQuery,
    player_x: float,
    player_y: float,
    input_mask: int,
    bullets: tuple[Bullet, ...],
    lasers: tuple[Laser, ...],
    enemy_bodies: tuple[EnemyBody, ...],
    snapshot_lag: int,
    frames: int,
    player_scale_bits: tuple[int, ...],
    laser_scale_bits: tuple[int, ...],
    laser_frames: tuple[_PackedLaserFrame, ...] | None = None,
) -> tuple[float, int, float]:
    """Evaluate motion already committed before a new decision can take effect."""

    if frames <= 0:
        return 0.0, 0, math.inf
    if len(player_scale_bits) < frames or len(laser_scale_bits) < frames:
        raise ValueError(
            "time-scale schedules do not cover the control prefix"
        )
    bullet_frames = _build_bullet_frames(
        bullets,
        horizon=frames,
        snapshot_lag=-max(0, snapshot_lag),
    )
    if laser_frames is None:
        laser_frames = _build_packed_laser_collision_frames(
            lasers,
            horizon=frames,
            time_scale_schedule_bits=laser_scale_bits[:frames],
        )
    if len(laser_frames) < frames:
        raise ValueError("laser timeline does not cover the control prefix")
    risk = 0.0
    collisions = 0
    minimum = math.inf
    x = player_x
    y = player_y
    for step in range(1, frames + 1):
        x, y = _project_player_for_read_lag(
            x,
            y,
            input_mask,
            1,
            player_scale_bits=(player_scale_bits[step - 1],),
        )
        hazard_risk, hazard_collisions, hazard_clearance = hazards_for_positions(
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


def legacy_robust_action_certificates(
    *,
    hazards_for_positions: HazardQuery,
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
    player_scale_bits: tuple[int, ...],
    laser_scale_bits: tuple[int, ...],
    laser_frames: tuple[_PackedLaserFrame, ...] | None = None,
) -> dict[str, RobustActionCertificate]:
    """Legacy last-desired-as-active certificate retained for differential."""

    if not actions or not delay_frames:
        return {}
    maximum_step = action_hold_frames + max(delay_frames)
    if (
        len(player_scale_bits) < maximum_step
        or len(laser_scale_bits) < maximum_step
    ):
        raise ValueError(
            "time-scale schedules do not cover robust certificates"
        )
    bullet_frames = _build_bullet_frames(
        bullets,
        horizon=maximum_step,
        snapshot_lag=-max(0, snapshot_lag),
    )
    if laser_frames is None:
        laser_frames = _build_packed_laser_collision_frames(
            lasers,
            horizon=maximum_step,
            time_scale_schedule_bits=laser_scale_bits[:maximum_step],
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
                prefix_x,
                prefix_y,
                previous_mask,
                1,
                player_scale_bits=(player_scale_bits[step - 1],),
            )
            hazard_risk, hazard_collisions, hazard_clearance = (
                hazards_for_positions(
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
        positions_x = np.full(action_count, prefix_x, dtype=np.float32)
        positions_y = np.full(action_count, prefix_y, dtype=np.float32)
        action_dx = np.fromiter(
            (action.dx for action in actions),
            dtype=np.float32,
            count=action_count,
        )
        action_dy = np.fromiter(
            (action.dy for action in actions),
            dtype=np.float32,
            count=action_count,
        )
        for step in range(delay + 1, maximum_step + 1):
            scale = np.float32(
                float32_from_bits(player_scale_bits[step - 1])
            )
            positions_x = np.clip(
                positions_x + action_dx * scale,
                PLAYFIELD_LEFT,
                PLAYFIELD_RIGHT,
            ).astype(np.float32, copy=False)
            positions_y = np.clip(
                positions_y + action_dy * scale,
                PLAYFIELD_TOP,
                PLAYFIELD_BOTTOM,
            ).astype(np.float32, copy=False)
            hazard_risk, hazard_collisions, hazard_clearance = (
                hazards_for_positions(
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


def robust_action_certificates(
    *,
    hazards_for_positions: HazardQuery,
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
    player_scale_bits: tuple[int, ...],
    laser_scale_bits: tuple[int, ...],
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
    if (
        len(player_scale_bits) < maximum_step
        or len(laser_scale_bits) < maximum_step
    ):
        raise ValueError(
            "time-scale schedules do not cover robust certificates"
        )
    bullet_frames = _build_bullet_frames(
        bullets,
        horizon=maximum_step,
        snapshot_lag=-max(0, snapshot_lag),
    )
    if laser_frames is None:
        laser_frames = _build_packed_laser_collision_frames(
            lasers,
            horizon=maximum_step,
            time_scale_schedule_bits=laser_scale_bits[:maximum_step],
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
        scale = np.float32(
            float32_from_bits(player_scale_bits[step - 1])
        )
        positions_x = np.clip(
            positions_x + motion_x * scale,
            PLAYFIELD_LEFT,
            PLAYFIELD_RIGHT,
        ).astype(np.float32, copy=False)
        positions_y = np.clip(
            positions_y + motion_y * scale,
            PLAYFIELD_TOP,
            PLAYFIELD_BOTTOM,
        ).astype(np.float32, copy=False)
        hazard_risk, hazard_collisions, hazard_clearance = (
            hazards_for_positions(
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
