#!/usr/bin/env python3
"""Lower live TH08 projectile snapshots into the neutral corridor planner."""

from __future__ import annotations

import math
from typing import Protocol

from corridor_planner import (
    CorridorBounds,
    CorridorConfig,
    CorridorPlan,
    MovingAabbHazard,
    RobustControlSpec,
    SegmentHazard,
    SegmentTrajectoryHazard,
    plan_corridor,
)
from th08_laser_model import (
    LaserState,
    laser_collision_geometry_frames,
)
from th08_movement_model import ROUTE2_MOVEMENT_PROFILE
from touhou_control.viability import ControlAction


class BulletSnapshot(Protocol):
    x: float
    y: float
    vx: float
    vy: float
    half_width: float
    half_height: float
    transform_flags: int


class LaserSnapshot(Protocol):
    origin_x: float
    origin_y: float
    angle: float
    tail: float
    head: float
    half_width: float
    state: LaserState | None
    uncertainty: float


class EnemyBodySnapshot(Protocol):
    x: float
    y: float
    vx: float
    vy: float
    half_width: float
    half_height: float
    uncertainty: float


TH08_PLAYFIELD = CorridorBounds(8.0, 376.0, 16.0, 432.0)
TH08_CORRIDOR_CONFIG = CorridorConfig(
    # This layer preserves long-horizon connectivity. The local MPC retains
    # per-frame precision around the selected 16-pixel corridor tube.
    grid_step=16.0,
    frames_per_layer=8,
    horizon_frames=80,
    cardinal_speed=4.0,
    diagonal_axis_speed=2.8284270763397217,
    player_radius=2.0,
    required_clearance=0.0,
    preferred_clearance=10.0,
    danger_radius=48.0,
    boundary_danger_radius=24.0,
)

_DIRECTION_VECTORS = (
    ("left", -1.0, 0.0),
    ("right", 1.0, 0.0),
    ("up", 0.0, -1.0),
    ("down", 0.0, 1.0),
    ("up_left", -1.0, -1.0),
    ("up_right", 1.0, -1.0),
    ("down_left", -1.0, 1.0),
    ("down_right", 1.0, 1.0),
)


def _route2_control_action(
    name: str,
    unit_x: float,
    unit_y: float,
    *,
    focused: bool,
) -> ControlAction:
    diagonal = unit_x != 0.0 and unit_y != 0.0
    profile = ROUTE2_MOVEMENT_PROFILE
    if focused:
        speed = (
            profile.focused_diagonal_axis
            if diagonal
            else profile.focused_cardinal
        )
    else:
        speed = (
            profile.unfocused_diagonal_axis
            if diagonal
            else profile.unfocused_cardinal
        )
    return ControlAction(name, unit_x * speed, unit_y * speed)


TH08_VIABILITY_ACTIONS = (
    ControlAction("stay", 0.0, 0.0),
    *(
        _route2_control_action(name, unit_x, unit_y, focused=True)
        for name, unit_x, unit_y in _DIRECTION_VECTORS
    ),
    *(
        _route2_control_action(
            f"{name}_fast",
            unit_x,
            unit_y,
            focused=False,
        )
        for name, unit_x, unit_y in _DIRECTION_VECTORS
    ),
)


def lower_bullets(
    bullets: tuple[BulletSnapshot, ...],
    *,
    snapshot_lag: int,
    forecast_frames: int = 0,
) -> tuple[MovingAabbHazard, ...]:
    lag = max(0, snapshot_lag)
    forecast = max(0, forecast_frames)
    read_uncertainty = 0.2 * math.sqrt(lag)
    hazards = []
    for bullet in bullets:
        growth = 0.35 if bullet.transform_flags else 0.05
        hazards.append(
            MovingAabbHazard(
                x=bullet.x + bullet.vx * (lag + forecast),
                y=bullet.y + bullet.vy * (lag + forecast),
                velocity_x=bullet.vx,
                velocity_y=bullet.vy,
                half_width=bullet.half_width,
                half_height=bullet.half_height,
                base_uncertainty=(
                    read_uncertainty
                    + (3.0 if bullet.transform_flags else 0.0)
                    + growth * forecast
                ),
                uncertainty_per_frame=growth,
            )
        )
    return tuple(hazards)


def lower_lasers(
    lasers: tuple[LaserSnapshot, ...],
    *,
    snapshot_lag: int,
    forecast_frames: int = 0,
    horizon_frames: int = TH08_CORRIDOR_CONFIG.horizon_frames,
) -> tuple[SegmentTrajectoryHazard, ...]:
    lag = max(0, snapshot_lag)
    forecast = max(0, forecast_frames)
    if horizon_frames < 0:
        raise ValueError("laser trajectory horizon cannot be negative")
    trajectories: list[SegmentTrajectoryHazard] = []
    for laser in lasers:
        state = laser.state
        if state is None:
            sample = SegmentHazard(
                origin_x=laser.origin_x,
                origin_y=laser.origin_y,
                angle=laser.angle,
                tail=laser.tail,
                head=laser.head,
                half_width=laser.half_width,
                base_uncertainty=(
                    laser.uncertainty
                    + min(12.0, 0.4 * lag)
                    + 0.4 * forecast
                ),
                uncertainty_per_frame=0.4,
            )
            trajectories.append(
                SegmentTrajectoryHazard((sample,) * (horizon_frames + 1))
            )
            continue
        geometry_frames = laser_collision_geometry_frames(
            state,
            frame_count=lag + forecast + horizon_frames + 1,
        )[lag + forecast:]
        per_frame = [
            tuple(
                (
                    SegmentHazard(
                        origin_x=state.origin_x,
                        origin_y=state.origin_y,
                        angle=state.angle,
                        tail=tail,
                        head=head,
                        half_width=half_width,
                        base_uncertainty=(
                            laser.uncertainty
                            + min(6.0, 0.08 * (forecast + frame))
                        ),
                    )
                )
                for tail, head, half_width in geometry
            )
            for frame, geometry in enumerate(geometry_frames)
        ]
        for check_index in range(max(map(len, per_frame), default=0)):
            trajectories.append(
                SegmentTrajectoryHazard(
                    tuple(
                        (
                            frame_segments[check_index]
                            if check_index < len(frame_segments)
                            else None
                        )
                        for frame_segments in per_frame
                    )
                )
            )
    return tuple(trajectories)


def lower_enemy_bodies(
    bodies: tuple[EnemyBodySnapshot, ...],
    *,
    snapshot_lag: int,
    forecast_frames: int = 0,
) -> tuple[MovingAabbHazard, ...]:
    lag = max(0, snapshot_lag)
    forecast = max(0, forecast_frames)
    return tuple(
        MovingAabbHazard(
            x=body.x + body.vx * (lag + forecast),
            y=body.y + body.vy * (lag + forecast),
            velocity_x=body.vx,
            velocity_y=body.vy,
            half_width=body.half_width,
            half_height=body.half_height,
            base_uncertainty=(
                body.uncertainty
                + 0.5 * math.sqrt(lag)
                + 0.5 * forecast
            ),
            uncertainty_per_frame=0.5,
        )
        for body in bodies
    )


def plan_th08_corridor(
    *,
    player_x: float,
    player_y: float,
    bullets: tuple[BulletSnapshot, ...],
    lasers: tuple[LaserSnapshot, ...],
    enemy_bodies: tuple[EnemyBodySnapshot, ...] = (),
    snapshot_lag: int = 0,
    forecast_frames: int = 0,
    preferred_x: float = 192.0,
    preferred_y: float = 368.0,
    required_gate_lane: str | None = None,
    config: CorridorConfig = TH08_CORRIDOR_CONFIG,
    control_delay_candidates: tuple[int, ...] | None = None,
    nominal_control_delay: int | None = None,
    active_action: str = "stay",
) -> CorridorPlan:
    robust_control = None
    if control_delay_candidates is not None:
        if nominal_control_delay is None:
            raise ValueError(
                "nominal control delay is required for robust viability"
            )
        robust_control = RobustControlSpec(
            actions=TH08_VIABILITY_ACTIONS,
            delay_frames=control_delay_candidates,
            nominal_delay=nominal_control_delay,
            active_action=active_action,
        )
    return plan_corridor(
        start_x=player_x,
        start_y=player_y,
        bounds=TH08_PLAYFIELD,
        aabbs=(
            lower_bullets(
                bullets,
                snapshot_lag=snapshot_lag,
                forecast_frames=forecast_frames,
            )
            + lower_enemy_bodies(
                enemy_bodies,
                snapshot_lag=snapshot_lag,
                forecast_frames=forecast_frames,
            )
        ),
        segment_trajectories=lower_lasers(
            lasers,
            snapshot_lag=snapshot_lag,
            forecast_frames=forecast_frames,
            horizon_frames=config.horizon_frames,
        ),
        preferred_x=preferred_x,
        preferred_y=preferred_y,
        required_gate_lane=required_gate_lane,
        config=config,
        robust_control=robust_control,
    )


def prewarm_th08_corridor() -> None:
    """Populate transition geometry before the F8 gameplay handoff."""

    plan_th08_corridor(
        player_x=192.0,
        player_y=400.0,
        bullets=(),
        lasers=(),
        control_delay_candidates=(1, 2, 3),
        nominal_control_delay=2,
        active_action="stay",
    )
