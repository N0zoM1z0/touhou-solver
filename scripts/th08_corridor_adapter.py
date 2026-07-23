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
    SegmentHazard,
    plan_corridor,
)


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


class EnemyBodySnapshot(Protocol):
    x: float
    y: float
    vx: float
    vy: float
    half_width: float
    half_height: float


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


def lower_bullets(
    bullets: tuple[BulletSnapshot, ...], *, snapshot_lag: int
) -> tuple[MovingAabbHazard, ...]:
    lag = max(0, snapshot_lag)
    read_uncertainty = 0.2 * math.sqrt(lag)
    return tuple(
        MovingAabbHazard(
            x=bullet.x + bullet.vx * lag,
            y=bullet.y + bullet.vy * lag,
            velocity_x=bullet.vx,
            velocity_y=bullet.vy,
            half_width=bullet.half_width,
            half_height=bullet.half_height,
            base_uncertainty=read_uncertainty
            + (3.0 if bullet.transform_flags else 0.0),
            uncertainty_per_frame=0.35 if bullet.transform_flags else 0.05,
        )
        for bullet in bullets
    )


def lower_lasers(
    lasers: tuple[LaserSnapshot, ...], *, snapshot_lag: int
) -> tuple[SegmentHazard, ...]:
    lag = max(0, snapshot_lag)
    return tuple(
        SegmentHazard(
            origin_x=laser.origin_x,
            origin_y=laser.origin_y,
            angle=laser.angle,
            tail=laser.tail,
            head=laser.head,
            half_width=laser.half_width,
            base_uncertainty=min(12.0, 0.4 * lag),
            uncertainty_per_frame=0.4,
        )
        for laser in lasers
    )


def lower_enemy_bodies(
    bodies: tuple[EnemyBodySnapshot, ...],
    *,
    snapshot_lag: int,
) -> tuple[MovingAabbHazard, ...]:
    lag = max(0, snapshot_lag)
    return tuple(
        MovingAabbHazard(
            x=body.x + body.vx * lag,
            y=body.y + body.vy * lag,
            velocity_x=body.vx,
            velocity_y=body.vy,
            half_width=body.half_width,
            half_height=body.half_height,
            base_uncertainty=0.5 * math.sqrt(lag),
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
    preferred_x: float = 192.0,
    preferred_y: float = 368.0,
    required_gate_lane: str | None = None,
    config: CorridorConfig = TH08_CORRIDOR_CONFIG,
) -> CorridorPlan:
    return plan_corridor(
        start_x=player_x,
        start_y=player_y,
        bounds=TH08_PLAYFIELD,
        aabbs=(
            lower_bullets(bullets, snapshot_lag=snapshot_lag)
            + lower_enemy_bodies(
                enemy_bodies,
                snapshot_lag=snapshot_lag,
            )
        ),
        segments=lower_lasers(lasers, snapshot_lag=snapshot_lag),
        preferred_x=preferred_x,
        preferred_y=preferred_y,
        required_gate_lane=required_gate_lane,
        config=config,
    )
