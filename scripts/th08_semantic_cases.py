"""Replayable TH08-semantic generated cases and deterministic shrinking."""

from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
import math
from typing import Callable

import numpy as np

import th08_live_dodge_agent as live
from th08_laser_model import LaserPhase, LaserState
from th08_laser_runtime import Laser
from touhou_control.trajectory import VelocityChange


SCHEMA = "th08-semantic-case-v1"
FAMILIES = (
    "aimed_fan",
    "radial_ring",
    "spiral",
    "wave_lanes",
    "wall",
    "crossfire",
    "random_cloud",
    "boundary_tangent",
    "laser_storm",
    "transform_adversarial",
    "off_tube",
    "mixed_phase",
)
DIFFICULTIES = ("normal", "hard", "lunatic", "beyond_pool")


@dataclass(frozen=True)
class SemanticCase:
    seed: int
    index: int
    profile: str
    family: str
    difficulty: str
    player_x: float
    player_y: float
    previous_direction: int
    previous_focused: bool
    control_delay_frames: int
    action_hold_frames: int
    horizon: int
    beam_width: int
    allowed_first_actions: tuple[str, ...]
    positions_x: tuple[float, ...]
    positions_y: tuple[float, ...]
    bullets: tuple[live.Bullet, ...]
    lasers: tuple[Laser, ...]
    enemy_bodies: tuple[live.EnemyBody, ...]

    def __post_init__(self) -> None:
        if self.family not in FAMILIES:
            raise ValueError(f"unknown semantic family {self.family!r}")
        if self.difficulty not in DIFFICULTIES:
            raise ValueError(
                f"unknown semantic difficulty {self.difficulty!r}"
            )
        if (
            self.horizon <= 0
            or self.action_hold_frames <= 0
            or self.beam_width <= 0
            or len(self.positions_x) != len(self.positions_y)
            or not self.positions_x
            or not self.allowed_first_actions
        ):
            raise ValueError("invalid semantic case dimensions")

    @property
    def identity(self) -> str:
        return (
            f"{self.profile}:{self.seed:016x}:{self.index}:"
            f"{self.family}:{self.difficulty}"
        )

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema": SCHEMA,
            "seed": self.seed,
            "index": self.index,
            "profile": self.profile,
            "family": self.family,
            "difficulty": self.difficulty,
            "player": [
                self.player_x,
                self.player_y,
                self.previous_direction,
                int(self.previous_focused),
            ],
            "planner": [
                self.control_delay_frames,
                self.action_hold_frames,
                self.horizon,
                self.beam_width,
                list(self.allowed_first_actions),
            ],
            "positions": [
                list(self.positions_x),
                list(self.positions_y),
            ],
            "bullets": [_bullet_payload(bullet) for bullet in self.bullets],
            "lasers": [_laser_payload(laser) for laser in self.lasers],
            "enemy_bodies": [
                _body_payload(body) for body in self.enemy_bodies
            ],
        }
        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode()
        payload["sha256"] = hashlib.sha256(canonical).hexdigest()
        return payload

    @classmethod
    def from_payload(cls, payload: dict[str, object]) -> "SemanticCase":
        if payload.get("schema") != SCHEMA:
            raise ValueError("unsupported TH08 semantic case schema")
        unsigned = dict(payload)
        digest = unsigned.pop("sha256", None)
        if digest is not None:
            canonical = json.dumps(
                unsigned,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode()
            if hashlib.sha256(canonical).hexdigest() != digest:
                raise ValueError("semantic case digest mismatch")
        player = unsigned["player"]
        planner = unsigned["planner"]
        positions = unsigned["positions"]
        assert isinstance(player, list)
        assert isinstance(planner, list)
        assert isinstance(positions, list)
        return cls(
            seed=int(unsigned["seed"]),
            index=int(unsigned["index"]),
            profile=str(unsigned["profile"]),
            family=str(unsigned["family"]),
            difficulty=str(unsigned["difficulty"]),
            player_x=float(player[0]),
            player_y=float(player[1]),
            previous_direction=int(player[2]),
            previous_focused=bool(player[3]),
            control_delay_frames=int(planner[0]),
            action_hold_frames=int(planner[1]),
            horizon=int(planner[2]),
            beam_width=int(planner[3]),
            allowed_first_actions=tuple(str(v) for v in planner[4]),
            positions_x=tuple(float(v) for v in positions[0]),
            positions_y=tuple(float(v) for v in positions[1]),
            bullets=tuple(
                _bullet_from_payload(values)
                for values in unsigned["bullets"]
            ),
            lasers=tuple(
                _laser_from_payload(values)
                for values in unsigned["lasers"]
            ),
            enemy_bodies=tuple(
                _body_from_payload(values)
                for values in unsigned["enemy_bodies"]
            ),
        )


def _bullet_payload(bullet: live.Bullet) -> list[object]:
    return [
        bullet.x,
        bullet.y,
        bullet.vx,
        bullet.vy,
        bullet.half_width,
        bullet.half_height,
        bullet.transform_flags,
        bullet.slot,
        bullet.speed,
        bullet.angle,
        bullet.callback_phase_state,
        bullet.callback_aux_state,
        [
            [change.frame, change.velocity_x, change.velocity_y]
            for change in bullet.velocity_changes
        ],
        bullet.trajectory_uncertainty_x,
        bullet.trajectory_uncertainty_y,
        bullet.original_transform_flags,
    ]


def _bullet_from_payload(values: list[object]) -> live.Bullet:
    return live.Bullet(
        x=float(values[0]),
        y=float(values[1]),
        vx=float(values[2]),
        vy=float(values[3]),
        half_width=float(values[4]),
        half_height=float(values[5]),
        transform_flags=int(values[6]),
        slot=int(values[7]),
        speed=None if values[8] is None else float(values[8]),
        angle=None if values[9] is None else float(values[9]),
        callback_phase_state=int(values[10]),
        callback_aux_state=int(values[11]),
        velocity_changes=tuple(
            VelocityChange(int(change[0]), float(change[1]), float(change[2]))
            for change in values[12]
        ),
        trajectory_uncertainty_x=float(values[13]),
        trajectory_uncertainty_y=float(values[14]),
        original_transform_flags=int(values[15]),
    )


def _laser_payload(laser: Laser) -> list[object]:
    state = laser.state
    return [
        laser.origin_x,
        laser.origin_y,
        laser.angle,
        laser.tail,
        laser.head,
        laser.half_width,
        laser.slot,
        laser.collision_flag,
        laser.uncertainty,
        laser.uncertainty_per_frame,
        (
            None
            if state is None
            else [
                state.origin_x,
                state.origin_y,
                state.angle,
                state.tail_distance,
                state.head_distance,
                state.maximum_length,
                state.width,
                state.speed,
                state.warmup_frames,
                state.active_frames,
                state.fade_frames,
                state.collision_enable_frame,
                state.collision_disable_frame,
                state.flags,
                state.current_width,
                int(state.phase),
                state.timer,
                state.timer_fraction,
                int(state.active),
            ]
        ),
    ]


def _laser_from_payload(values: list[object]) -> Laser:
    state_values = values[10]
    state = None
    if state_values is not None:
        state = LaserState(
            origin_x=float(state_values[0]),
            origin_y=float(state_values[1]),
            angle=float(state_values[2]),
            tail_distance=float(state_values[3]),
            head_distance=float(state_values[4]),
            maximum_length=float(state_values[5]),
            width=float(state_values[6]),
            speed=float(state_values[7]),
            warmup_frames=int(state_values[8]),
            active_frames=int(state_values[9]),
            fade_frames=int(state_values[10]),
            collision_enable_frame=int(state_values[11]),
            collision_disable_frame=int(state_values[12]),
            flags=int(state_values[13]),
            current_width=float(state_values[14]),
            phase=LaserPhase(int(state_values[15])),
            timer=int(state_values[16]),
            timer_fraction=float(state_values[17]),
            active=bool(state_values[18]),
        )
    return Laser(
        origin_x=float(values[0]),
        origin_y=float(values[1]),
        angle=float(values[2]),
        tail=float(values[3]),
        head=float(values[4]),
        half_width=float(values[5]),
        slot=int(values[6]),
        collision_flag=int(values[7]),
        uncertainty=float(values[8]),
        uncertainty_per_frame=float(values[9]),
        state=state,
    )


def _body_payload(body: live.EnemyBody) -> list[object]:
    return [
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


def _body_from_payload(values: list[object]) -> live.EnemyBody:
    return live.EnemyBody(
        pointer=int(values[0]),
        x=float(values[1]),
        y=float(values[2]),
        vx=float(values[3]),
        vy=float(values[4]),
        half_width=float(values[5]),
        half_height=float(values[6]),
        flags=int(values[7]),
        uncertainty=float(values[8]),
    )


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


def _ddmin_tuple(
    values: tuple[object, ...],
    *,
    update: Callable[[tuple[object, ...]], SemanticCase],
    fails: Callable[[SemanticCase], bool],
    attempts: list[int],
    maximum_attempts: int,
) -> tuple[object, ...]:
    current = values
    granularity = 2
    while current and attempts[0] < maximum_attempts:
        chunk = max(1, math.ceil(len(current) / granularity))
        reduced = False
        for start in range(0, len(current), chunk):
            candidate = current[:start] + current[start + chunk :]
            attempts[0] += 1
            if fails(update(candidate)):
                current = candidate
                granularity = max(2, granularity - 1)
                reduced = True
                break
            if attempts[0] >= maximum_attempts:
                break
        if reduced:
            continue
        if granularity >= len(current):
            break
        granularity = min(len(current), granularity * 2)
    return current


def shrink_case(
    case: SemanticCase,
    *,
    fails: Callable[[SemanticCase], bool],
    maximum_attempts: int = 256,
) -> tuple[SemanticCase, int]:
    """Deterministically shrink hazards and planner dimensions."""

    if maximum_attempts <= 0 or not fails(case):
        return case, 0
    attempts = [0]
    current = case

    def retain(candidate: SemanticCase) -> bool:
        nonlocal current
        if attempts[0] >= maximum_attempts or candidate == current:
            return False
        attempts[0] += 1
        if not fails(candidate):
            return False
        current = candidate
        return True

    for field in ("bullets", "lasers", "enemy_bodies"):
        original = getattr(current, field)

        def update(
            values: tuple[object, ...],
            *,
            field_name: str = field,
        ) -> SemanticCase:
            return replace(current, **{field_name: values})

        reduced = _ddmin_tuple(
            original,
            update=update,
            fails=fails,
            attempts=attempts,
            maximum_attempts=maximum_attempts,
        )
        current = replace(current, **{field: reduced})
        if attempts[0] >= maximum_attempts:
            return current, attempts[0]

    # Remove individual piecewise transform events before simplifying their
    # numeric state.  Each accepted edit is based on the latest current case,
    # so a later edit cannot silently restore a previous reduction.
    for bullet_index in range(len(current.bullets)):
        if attempts[0] >= maximum_attempts:
            return current, attempts[0]
        changes = current.bullets[bullet_index].velocity_changes
        if not changes:
            continue

        def update_changes(
            values: tuple[object, ...],
            *,
            index: int = bullet_index,
        ) -> SemanticCase:
            bullets = list(current.bullets)
            bullets[index] = replace(
                bullets[index],
                velocity_changes=tuple(values),
            )
            return replace(current, bullets=tuple(bullets))

        reduced_changes = _ddmin_tuple(
            tuple(changes),
            update=update_changes,
            fails=fails,
            attempts=attempts,
            maximum_attempts=maximum_attempts,
        )
        current = update_changes(reduced_changes)

    retain(
        replace(
            current,
            horizon=max(1, current.horizon // 2),
            action_hold_frames=min(
                current.action_hold_frames,
                max(1, current.horizon // 2),
            ),
        )
    )
    retain(replace(current, beam_width=1))
    retain(
        replace(
            current,
            allowed_first_actions=current.allowed_first_actions[:1],
        )
    )
    retain(replace(current, control_delay_frames=1))
    retain(replace(current, player_x=192.0, player_y=400.0))

    # Axis/zero and tangent simplifications make geometry failures readable.
    for bullet_index in range(len(current.bullets)):
        if attempts[0] >= maximum_attempts:
            break

        def retain_bullet(variant: live.Bullet) -> None:
            bullets = list(current.bullets)
            bullets[bullet_index] = variant
            retain(replace(current, bullets=tuple(bullets)))

        bullet = current.bullets[bullet_index]
        retain_bullet(
            replace(
                bullet,
                velocity_changes=(),
                trajectory_uncertainty_x=0.0,
                trajectory_uncertainty_y=0.0,
            )
        )
        retain_bullet(replace(current.bullets[bullet_index], vx=0.0))
        retain_bullet(replace(current.bullets[bullet_index], vy=0.0))
        retain_bullet(
            replace(current.bullets[bullet_index], vx=0.0, vy=0.0)
        )
        retain_bullet(
            replace(current.bullets[bullet_index], x=0.0, y=0.0)
        )
        bullet = current.bullets[bullet_index]
        retain_bullet(
            replace(
                bullet,
                x=(
                    current.player_x
                    + live.PLAYER_RADIUS
                    + max(bullet.half_width, 0.0)
                ),
                y=current.player_y,
                vx=0.0,
                vy=0.0,
            )
        )

    for laser_index in range(len(current.lasers)):
        if attempts[0] >= maximum_attempts:
            break

        def retain_laser(variant: Laser) -> None:
            lasers = list(current.lasers)
            lasers[laser_index] = variant
            retain(replace(current, lasers=tuple(lasers)))

        laser = current.lasers[laser_index]
        retain_laser(
            replace(
                laser,
                angle=0.0,
                uncertainty=0.0,
                uncertainty_per_frame=0.0,
            )
        )
        laser = current.lasers[laser_index]
        retain_laser(replace(laser, head=laser.tail))
        retain_laser(replace(current.lasers[laser_index], state=None))
        retain_laser(
            replace(
                current.lasers[laser_index],
                origin_x=current.player_x,
                origin_y=current.player_y,
                angle=0.0,
                tail=0.0,
                head=0.0,
            )
        )

    for body_index in range(len(current.enemy_bodies)):
        if attempts[0] >= maximum_attempts:
            break

        def retain_body(variant: live.EnemyBody) -> None:
            bodies = list(current.enemy_bodies)
            bodies[body_index] = variant
            retain(replace(current, enemy_bodies=tuple(bodies)))

        retain_body(
            replace(
                current.enemy_bodies[body_index],
                vx=0.0,
                vy=0.0,
                uncertainty=0.0,
            )
        )
        body = current.enemy_bodies[body_index]
        retain_body(
            replace(
                body,
                x=(
                    current.player_x
                    + live.PLAYER_RADIUS
                    + max(body.half_width, 0.0)
                ),
                y=current.player_y,
                vx=0.0,
                vy=0.0,
                uncertainty=0.0,
            )
        )

    retain(
        replace(
            current,
            positions_x=(current.player_x,),
            positions_y=(current.player_y,),
        )
    )
    return current, attempts[0]
