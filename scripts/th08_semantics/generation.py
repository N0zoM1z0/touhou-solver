"""Deterministic generators for replayable TH08 semantic cases."""

from __future__ import annotations

import math

import numpy as np

import th08_live_dodge_agent as live
from th08_laser_model import LaserPhase, LaserState
from th08_laser_runtime import Laser
from th08_semantics.model import DIFFICULTIES, FAMILIES, SemanticCase
from touhou_control.trajectory import VelocityChange


def _profile_limits(profile: str) -> tuple[int, int, int, int]:
    if profile == "quick":
        return 64, 8, 4, 12
    if profile == "gate":
        return 1536, 256, 16, 48
    if profile == "research":
        return 4096, 2048, 64, 128
    raise ValueError(f"unknown semantic profile {profile!r}")


def _density(
    generator: np.random.Generator,
    *,
    maximum: int,
    difficulty_index: int,
    minimum: int = 0,
) -> int:
    scale = (0.18, 0.38, 0.68, 1.0)[difficulty_index]
    lower = min(maximum, minimum)
    upper = max(lower, int(maximum * scale))
    if upper == lower:
        return upper
    # Bias ordinary cases below the maximum while retaining regular tails.
    fraction = max(
        float(generator.beta(1.5, 2.5)),
        0.82 if generator.random() < 0.08 else 0.0,
    )
    return lower + int((upper - lower) * fraction)


def _velocity_changes(
    index: int,
    vx: float,
    vy: float,
    horizon: int,
) -> tuple[VelocityChange, ...]:
    first = max(1, min(horizon, 2 + index % max(1, horizon // 2)))
    second = min(horizon, first + max(1, horizon // 3))
    mode = index % 5
    if mode == 0 and second > first:
        return (
            VelocityChange(first, 0.0, 0.0),
            VelocityChange(second, vx, vy),
        )
    if mode == 1:
        return (VelocityChange(first, -vx, -vy),)
    if mode == 2:
        return (VelocityChange(first, vy, -vx),)
    if mode == 3 and second > first:
        return (
            VelocityChange(first, 1.5 * vx, 1.5 * vy),
            VelocityChange(second, -0.5 * vx, -0.5 * vy),
        )
    return ()


def _generate_bullets(
    generator: np.random.Generator,
    *,
    family: str,
    count: int,
    player_x: float,
    player_y: float,
    horizon: int,
) -> tuple[live.Bullet, ...]:
    output: list[live.Bullet] = []
    for index in range(count):
        phase = 2.0 * math.pi * index / max(1, count)
        speed = float(generator.uniform(0.4, 6.5))
        if family == "aimed_fan":
            x = float(generator.uniform(24.0, 360.0))
            y = float(generator.uniform(-64.0, 80.0))
            aimed = math.atan2(player_y - y, player_x - x)
            angle = aimed + float(generator.normal(0.0, 0.24))
        elif family in {"radial_ring", "spiral"}:
            radius = float(generator.uniform(8.0, 220.0))
            x = player_x + math.cos(phase) * radius
            y = player_y + math.sin(phase) * radius
            angle = phase + (
                math.pi / 2.0 if family == "spiral" else 0.0
            )
        elif family in {"wave_lanes", "wall"}:
            columns = max(1, int(math.sqrt(max(1, count))))
            x = 8.0 + (
                (index % columns) + 0.5
            ) * (368.0 / columns)
            y = -48.0 + (index // columns) * 9.0
            angle = math.pi / 2.0 + (
                0.22 * math.sin(index * 0.35)
                if family == "wave_lanes"
                else 0.0
            )
        elif family == "crossfire":
            from_left = index % 2 == 0
            x = -32.0 if from_left else 416.0
            y = float(generator.uniform(32.0, 432.0))
            angle = (
                float(generator.uniform(-0.28, 0.28))
                if from_left
                else math.pi + float(generator.uniform(-0.28, 0.28))
            )
        elif family == "boundary_tangent":
            side = index % 4
            half_width = 1.0 + index % 7
            half_height = 1.0 + (index // 7) % 7
            epsilon = (-1e-5, 0.0, 1e-5, 0.25, -0.25)[index % 5]
            x, y = player_x, player_y
            if side == 0:
                x += live.PLAYER_RADIUS + half_width + epsilon
            elif side == 1:
                x -= live.PLAYER_RADIUS + half_width + epsilon
            elif side == 2:
                y += live.PLAYER_RADIUS + half_height + epsilon
            else:
                y -= live.PLAYER_RADIUS + half_height + epsilon
            angle = 0.0
            speed = 0.0
        elif family == "off_tube":
            x = float(generator.uniform(800.0, 1800.0))
            y = float(generator.uniform(800.0, 1800.0))
            angle = float(generator.uniform(-math.pi, math.pi))
        else:
            x = float(generator.uniform(-96.0, 480.0))
            y = float(generator.uniform(-96.0, 544.0))
            angle = float(generator.uniform(-math.pi, math.pi))
        vx = speed * math.cos(angle)
        vy = speed * math.sin(angle)
        half_width = float(generator.uniform(0.5, 10.0))
        half_height = float(generator.uniform(0.5, 10.0))
        transformed = (
            family in {"transform_adversarial", "mixed_phase"}
            or index % 7 == 0
        )
        output.append(
            live.Bullet(
                x=float(x),
                y=float(y),
                vx=vx,
                vy=vy,
                half_width=half_width,
                half_height=half_height,
                transform_flags=0x202 if transformed else 0,
                slot=index,
                speed=speed,
                angle=angle,
                callback_phase_state=index % 6,
                callback_aux_state=index % 4,
                velocity_changes=(
                    _velocity_changes(index, vx, vy, horizon)
                    if transformed
                    else ()
                ),
                trajectory_uncertainty_x=0.125 * (index % 5),
                trajectory_uncertainty_y=0.125 * (index % 7),
                original_transform_flags=(
                    0x202 if transformed else 0
                ),
            )
        )
    return tuple(output)


def _generate_lasers(
    generator: np.random.Generator,
    *,
    family: str,
    count: int,
) -> tuple[Laser, ...]:
    output: list[Laser] = []
    for index in range(count):
        distant = family == "off_tube"
        origin_x = float(
            generator.uniform(850.0, 1800.0)
            if distant
            else generator.uniform(-128.0, 512.0)
        )
        origin_y = float(
            generator.uniform(850.0, 1800.0)
            if distant
            else generator.uniform(-128.0, 576.0)
        )
        angle = float(generator.uniform(-math.pi, math.pi))
        tail = float(generator.uniform(-64.0, 64.0))
        degenerate = (
            family in {"laser_storm", "boundary_tangent"}
            and index % 5 == 0
        )
        head = tail + (
            (0.0 if index % 2 else 1e-7)
            if degenerate
            else float(generator.uniform(48.0, 900.0))
        )
        half_width = float(generator.uniform(0.5, 20.0))
        state = None
        if family in {"laser_storm", "mixed_phase"} or index % 6 == 0:
            phase = (
                LaserPhase.WARMUP,
                LaserPhase.ACTIVE,
                LaserPhase.FADE,
            )[index % 3]
            state = LaserState(
                origin_x=origin_x,
                origin_y=origin_y,
                angle=angle,
                tail_distance=tail,
                head_distance=head,
                maximum_length=float(generator.uniform(64.0, 900.0)),
                width=2.0 * half_width,
                speed=float(generator.uniform(-8.0, 14.0)),
                warmup_frames=24,
                active_frames=90,
                fade_frames=24,
                collision_enable_frame=4,
                collision_disable_frame=18,
                flags=index & 3,
                current_width=2.0 * half_width,
                phase=phase,
                timer=index % 22,
                timer_fraction=0.5 if index % 2 else 0.0,
                active=True,
            )
        output.append(
            Laser(
                origin_x=origin_x,
                origin_y=origin_y,
                angle=angle,
                tail=tail,
                head=head,
                half_width=half_width,
                state=state,
                slot=index,
                collision_flag=1,
                uncertainty=0.25 * (index % 5),
                uncertainty_per_frame=0.04 * (index % 4),
            )
        )
    return tuple(output)


def generate_case(
    *,
    seed: int,
    index: int,
    profile: str,
) -> SemanticCase:
    """Generate one case independently so ordering/sharding changes nothing."""

    maximum_bullets, maximum_lasers, maximum_bodies, positions = (
        _profile_limits(profile)
    )
    sequence = np.random.SeedSequence(
        [seed & 0xFFFFFFFF, seed >> 32, index, 0xCE0132]
    )
    generator = np.random.default_rng(sequence)
    family = FAMILIES[index % len(FAMILIES)]
    difficulty_index = (index // len(FAMILIES)) % len(DIFFICULTIES)
    difficulty = DIFFICULTIES[difficulty_index]
    player_x = float(generator.uniform(16.0, 368.0))
    player_y = float(generator.uniform(48.0, 424.0))
    bullet_minimum = 1 if family != "laser_storm" else 0
    bullet_count = _density(
        generator,
        maximum=maximum_bullets,
        difficulty_index=difficulty_index,
        minimum=bullet_minimum,
    )
    laser_scale = (
        maximum_lasers
        if family in {"laser_storm", "mixed_phase", "off_tube"}
        else max(2, maximum_lasers // 8)
    )
    laser_count = _density(
        generator,
        maximum=laser_scale,
        difficulty_index=difficulty_index,
        minimum=(
            1
            if family in {"laser_storm", "mixed_phase"}
            else 0
        ),
    )
    body_count = _density(
        generator,
        maximum=maximum_bodies,
        difficulty_index=difficulty_index,
    )
    horizon = (
        int(generator.integers(3, 7))
        if profile == "quick"
        else int(generator.integers(4, 13))
    )
    if profile == "research":
        horizon = int(generator.integers(6, 25))
    if family == "boundary_tangent":
        pattern_x = (
            live.PLAYFIELD_LEFT,
            live.PLAYFIELD_RIGHT,
            player_x,
            player_x,
        )
        pattern_y = (
            player_y,
            player_y,
            live.PLAYFIELD_TOP,
            live.PLAYFIELD_BOTTOM,
        )
        query_x = tuple(float(pattern_x[i % 4]) for i in range(positions))
        query_y = tuple(float(pattern_y[i % 4]) for i in range(positions))
    else:
        query_x = tuple(
            float(value)
            for value in generator.uniform(8.0, 376.0, positions)
        )
        query_y = tuple(
            float(value)
            for value in generator.uniform(16.0, 432.0, positions)
        )
    bullets = _generate_bullets(
        generator,
        family=family,
        count=bullet_count,
        player_x=player_x,
        player_y=player_y,
        horizon=horizon,
    )
    lasers = _generate_lasers(
        generator,
        family=family,
        count=laser_count,
    )
    bodies = tuple(
        live.EnemyBody(
            pointer=slot + 1,
            x=float(
                generator.uniform(800.0, 1400.0)
                if family == "off_tube"
                else generator.uniform(0.0, 384.0)
            ),
            y=float(
                generator.uniform(800.0, 1400.0)
                if family == "off_tube"
                else generator.uniform(16.0, 448.0)
            ),
            vx=float(generator.uniform(-4.0, 4.0)),
            vy=float(generator.uniform(-4.0, 4.0)),
            half_width=float(generator.uniform(2.0, 24.0)),
            half_height=float(generator.uniform(2.0, 24.0)),
            flags=0,
            uncertainty=float(generator.uniform(0.0, 8.0)),
        )
        for slot in range(body_count)
    )
    action_names = tuple(action.name for action in live._PLANNER_ACTIONS)
    allowed_count = int(generator.integers(1, min(8, len(action_names)) + 1))
    allowed = tuple(
        action_names[int(slot)]
        for slot in generator.choice(
            len(action_names),
            size=allowed_count,
            replace=False,
        )
    )
    return SemanticCase(
        seed=seed,
        index=index,
        profile=profile,
        family=family,
        difficulty=difficulty,
        player_x=player_x,
        player_y=player_y,
        previous_direction=int(
            generator.choice(
                (0, live.LEFT, live.RIGHT, live.UP, live.DOWN)
            )
        ),
        previous_focused=bool(generator.integers(0, 2)),
        control_delay_frames=int(generator.integers(1, 4)),
        action_hold_frames=int(generator.integers(2, 6)),
        horizon=horizon,
        beam_width=int(generator.integers(1, 9)),
        allowed_first_actions=allowed,
        positions_x=query_x,
        positions_y=query_y,
        bullets=bullets,
        lasers=lasers,
        enemy_bodies=bodies,
    )


def generate_cases(
    *,
    seed: int,
    count: int,
    profile: str,
) -> tuple[SemanticCase, ...]:
    if count <= 0:
        raise ValueError("semantic case count must be positive")
    return tuple(
        generate_case(seed=seed, index=index, profile=profile)
        for index in range(count)
    )
