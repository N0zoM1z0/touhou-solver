"""TH08-specific reconstruction helpers for retained compact trace rows."""

from __future__ import annotations

from th08_laser_model import LaserPhase, LaserState
from th08_live_dodge_agent import Bullet, EnemyBody, Laser
from touhou_control.trajectory import VelocityChange


def laser_from_trace(values: list[object]) -> Laser:
    state = None
    if len(values) >= 22 and values[7] is not None:
        state = LaserState(
            origin_x=float(values[0]),
            origin_y=float(values[1]),
            angle=float(values[2]),
            tail_distance=float(values[3]),
            head_distance=float(values[4]),
            maximum_length=float(values[7]),
            width=float(values[8]),
            speed=float(values[10]),
            warmup_frames=int(values[15]),
            active_frames=int(values[17]),
            fade_frames=int(values[18]),
            collision_enable_frame=int(values[16]),
            collision_disable_frame=int(values[19]),
            flags=int(values[13]),
            current_width=float(values[9]),
            phase=LaserPhase(int(values[11])),
            timer=int(values[12]),
            timer_fraction=float(values[20]),
            active=True,
        )
    return Laser(
        origin_x=float(values[0]),
        origin_y=float(values[1]),
        angle=float(values[2]),
        tail=float(values[3]),
        head=float(values[4]),
        half_width=float(values[5]),
        state=state,
        slot=int(values[6]),
        collision_flag=int(values[14]) if len(values) > 14 else 0,
        uncertainty=float(values[21]) if len(values) > 21 else 0.0,
        uncertainty_per_frame=(
            float(values[22])
            if len(values) > 22
            else (0.0 if state is not None else 0.08)
        ),
    )


def bullet_from_trace(values: list[object]) -> Bullet:
    """Reconstruct the gameplay trajectory retained by the live trace."""

    runtime = values[8] if len(values) > 8 else None
    projection = values[9] if len(values) > 9 else None
    diagnostic_runtime = isinstance(runtime, list) and len(runtime) >= 12
    planning_projection = (
        not diagnostic_runtime
        and isinstance(projection, list)
        and len(projection) >= 8
    )
    payload = runtime if diagnostic_runtime else projection
    if diagnostic_runtime:
        callback_phase = int(runtime[12]) if len(runtime) > 12 else 0
        callback_aux = int(runtime[13]) if len(runtime) > 13 else 0
        raw_changes = runtime[14] if len(runtime) > 14 else ()
        uncertainty_x = float(runtime[15]) if len(runtime) > 15 else 0.0
        uncertainty_y = float(runtime[16]) if len(runtime) > 16 else 0.0
    elif planning_projection:
        assert isinstance(projection, list)
        callback_phase = int(projection[3])
        callback_aux = int(projection[4])
        raw_changes = projection[5]
        uncertainty_x = float(projection[6])
        uncertainty_y = float(projection[7])
    else:
        callback_phase = 0
        callback_aux = 0
        raw_changes = ()
        uncertainty_x = 0.0
        uncertainty_y = 0.0
    changes = tuple(
        VelocityChange(
            int(change[0]),
            float(change[1]),
            float(change[2]),
        )
        for change in raw_changes
    )
    return Bullet(
        x=float(values[1]),
        y=float(values[2]),
        vx=float(values[3]),
        vy=float(values[4]),
        half_width=float(values[5]),
        half_height=float(values[6]),
        transform_flags=int(values[7]),
        slot=int(values[0]),
        speed=(
            float(payload[0])
            if isinstance(payload, list) and payload[0] is not None
            else None
        ),
        angle=(
            float(payload[1])
            if isinstance(payload, list) and payload[1] is not None
            else None
        ),
        callback_phase_state=callback_phase,
        callback_aux_state=callback_aux,
        velocity_changes=changes,
        trajectory_uncertainty_x=uncertainty_x,
        trajectory_uncertainty_y=uncertainty_y,
        original_transform_flags=(
            int(payload[2]) if isinstance(payload, list) else 0
        ),
    )


def hazards_from_trace(
    row: dict[str, object],
) -> tuple[tuple[Bullet, ...], tuple[Laser, ...], tuple[EnemyBody, ...]]:
    return (
        tuple(
            bullet_from_trace(values)
            for values in row.get("nearby_bullets", ())
        ),
        tuple(
            laser_from_trace(values)
            for values in row.get("lasers", ())
        ),
        tuple(
            EnemyBody(*values)
            for values in row.get("enemy_bodies", ())
        ),
    )


__all__ = [
    "bullet_from_trace",
    "hazards_from_trace",
    "laser_from_trace",
]
