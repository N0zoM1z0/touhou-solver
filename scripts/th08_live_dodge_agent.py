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
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np

from corridor_planner import CorridorPlan
from runtime_agent import input_transitions
from th08_corridor_adapter import plan_th08_corridor
from th08_runtime_agent import (
    ADDR_ENGINE_FLAGS,
    ADDR_ENEMY_MANAGER_FRAME,
    ADDR_PLAYER,
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


BULLET_POOL_BASE = 0x00F6F710
BULLET_POOL_SIZE = 1536
BULLET_STRIDE = 0x10B8
BULLET_GEOMETRY_OFFSET = 0x0D34
BULLET_POSITION_OFFSET = 0x0D44
BULLET_VELOCITY_OFFSET = 0x0D50
BULLET_TRANSFORM_FLAGS_OFFSET = 0x0DAC
BULLET_STATE_OFFSET = 0x0DB8

LASER_POOL_BASE = 0x015B57C8
LASER_POOL_SIZE = 256
LASER_STRIDE = 0x059C
LASER_ORIGIN_OFFSET = 0x0548
LASER_ANGLE_OFFSET = 0x0554
LASER_TAIL_OFFSET = 0x0558
LASER_HEAD_OFFSET = 0x055C
LASER_WIDTH_OFFSET = 0x0564
LASER_ACTIVE_OFFSET = 0x0584

ITEM_MANAGER_BASE = 0x01653648
ITEM_POOL_SIZE = 2096
ITEM_STRIDE = 0x02E4
ITEM_POSITION_OFFSET = 0x02A4
ITEM_VELOCITY_OFFSET = 0x02B0
ITEM_TYPE_OFFSET = 0x02D4
ITEM_ACTIVE_OFFSET = 0x02D5
ITEM_MOTION_STATE_OFFSET = 0x02D7
ITEM_FULL_VALUE_OFFSET = 0x02D8

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
PLANNER_BEAM_WIDTH = 24
PLANNER_ACTION_HOLD = 2
# From the player snapshot, the live loop spends roughly two game frames
# reading/planning and TH08 samples injected input on the following frame.
# Bullet memory is read later, so snapshot_lag is subtracted from its lead.
CONTROL_DELAY_FRAMES = 3
COLLECTION_HALF_WIDTH = 24.0
ITEM_SAFETY_CLEARANCE = 8.0
CORRIDOR_REPLAN_FRAMES = 24
CORRIDOR_LOOKAHEAD_FRAMES = 16
CORRIDOR_MAX_AGE_FRAMES = 48
CORRIDOR_MIN_COMMIT_FRAMES = 32


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


@dataclass(frozen=True)
class Laser:
    origin_x: float
    origin_y: float
    angle: float
    tail: float
    head: float
    half_width: float


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


@dataclass(frozen=True)
class PlannerAction:
    name: str
    direction: int
    dx: float
    dy: float
    focused: bool


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
    required_gate_lane: str | None = None
    constraint_honored: bool = False
    context_key: tuple[int, int | None] | None = None


@dataclass
class CorridorCommitment:
    """Retain a viable gate component across asynchronous replans."""

    lane: str | None = None
    expires_frame: int = -1
    context_key: tuple[int, int | None] | None = None

    def set_context(self, context_key: tuple[int, int | None]) -> bool:
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
        transform_flags = struct.unpack_from(
            "<I", blob, base + BULLET_TRANSFORM_FLAGS_OFFSET
        )[0]
        if not _finite((x, y, vx, vy, width, height)):
            continue
        half_width = min(max(abs(width) * 0.5, 1.0), 24.0)
        half_height = min(max(abs(height) * 0.5, 1.0), 24.0)
        bullets.append(
            Bullet(x, y, vx, vy, half_width, half_height, transform_flags, index)
        )
    return tuple(bullets)


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
        width = struct.unpack_from("<f", blob, base + LASER_WIDTH_OFFSET)[0]
        if not _finite((origin_x, origin_y, angle, tail, head, width)):
            continue
        lasers.append(
            Laser(origin_x, origin_y, angle, tail, head, min(abs(width) * 0.5, 64.0))
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
    transformed = np.fromiter(
        (bool(bullet.transform_flags) for bullet in bullets), dtype=np.bool_
    )
    for step in range(1, horizon + 1):
        elapsed = snapshot_lag + step
        frames.append(
            (
                base_x + velocity_x * elapsed,
                base_y + velocity_y * elapsed,
                half_width,
                half_height,
                transformed,
            )
        )
    return tuple(frames)


def _hazards_for_positions(
    positions_x: np.ndarray,
    positions_y: np.ndarray,
    *,
    step: int,
    bullet_frame: tuple[np.ndarray, ...],
    lasers: tuple[Laser, ...],
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
    for laser in lasers:
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
            distance = np.hypot(positions_x - start_x, positions_y - start_y)
        else:
            projection = np.clip(
                ((positions_x - start_x) * segment_x + (positions_y - start_y) * segment_y)
                / length_sq,
                0.0,
                1.0,
            )
            distance = np.hypot(
                positions_x - (start_x + projection * segment_x),
                positions_y - (start_y + projection * segment_y),
            )
        clearance = distance - laser.half_width - PLAYER_RADIUS
        collisions += (clearance <= 0.0).astype(np.int32)
        robust_clearance = clearance - min(12.0, 0.4 * step)
        minimum = np.minimum(minimum, robust_clearance)
        danger = np.maximum(56.0 - robust_clearance, 0.0)
        risk += 2.0 * np.square(danger) * time_weight
    return risk, collisions, minimum


def _control_prefix_hazards(
    *,
    player_x: float,
    player_y: float,
    input_mask: int,
    bullets: tuple[Bullet, ...],
    lasers: tuple[Laser, ...],
    snapshot_lag: int,
    frames: int,
) -> tuple[float, int, float]:
    """Evaluate motion already committed before a new decision can take effect."""

    if frames <= 0:
        return 0.0, 0, math.inf
    bullet_frames = _build_bullet_frames(
        bullets,
        horizon=frames,
        snapshot_lag=-max(0, snapshot_lag),
    )
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
            lasers=lasers,
        )
        risk += _boundary_risk(x, y) + float(hazard_risk[0])
        collisions += int(hazard_collisions[0])
        minimum = min(minimum, float(hazard_clearance[0]))
    return risk, collisions, minimum


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


def _directions_opposed(left: int, right: int) -> bool:
    horizontal = bool(left & LEFT and right & RIGHT) or bool(
        left & RIGHT and right & LEFT
    )
    vertical = bool(left & UP and right & DOWN) or bool(
        left & DOWN and right & UP
    )
    return horizontal or vertical


def choose_action(
    *,
    player_x: float,
    player_y: float,
    bullets: tuple[Bullet, ...],
    lasers: tuple[Laser, ...],
    previous_direction: int,
    can_bomb: bool,
    items: tuple[Item, ...] = (),
    power: float = 0.0,
    bombs: float = 0.0,
    previous_focus: bool = True,
    snapshot_lag: int = 0,
    control_delay_frames: int = CONTROL_DELAY_FRAMES,
    horizon: int = PLANNER_HORIZON,
    beam_width: int = PLANNER_BEAM_WIDTH,
    target_x: float | None = None,
    target_y: float | None = None,
    target_deadline: int | None = None,
) -> Decision:
    if horizon <= 0 or beam_width <= 0:
        raise ValueError("planner horizon and beam width must be positive")
    if control_delay_frames < 0:
        raise ValueError("control delay cannot be negative")
    if (target_x is None) != (target_y is None):
        raise ValueError("target_x and target_y must be supplied together")
    if target_x is not None:
        if target_deadline is None:
            target_deadline = horizon
        if target_deadline < 0:
            raise ValueError("target deadline cannot be negative")
    selected_items = _select_items(items, power=power, bombs=bombs)
    delayed_mask = previous_direction | (FOCUS if previous_focus else 0)
    prefix_risk, prefix_collisions, prefix_clearance = _control_prefix_hazards(
        player_x=player_x,
        player_y=player_y,
        input_mask=delayed_mask,
        bullets=bullets,
        lasers=lasers,
        snapshot_lag=snapshot_lag,
        frames=control_delay_frames,
    )
    player_x, player_y = _project_player_for_read_lag(
        player_x,
        player_y,
        delayed_mask,
        control_delay_frames,
    )
    bullet_frames = _build_bullet_frames(
        bullets,
        horizon=horizon,
        snapshot_lag=max(
            0,
            control_delay_frames - max(0, snapshot_lag),
        ),
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
    if (
        not bullets
        and not lasers
        and not selected_items
        and target_x is None
    ):
        return Decision(SHOT | FOCUS, "stay", 9999.0, 9999.0, 0.0, False)
    for step in range(1, horizon + 1):
        drafts: list[
            tuple[SearchNode, PlannerAction, float, float, float, int, float]
        ] = []
        draft_first_actions: list[PlannerAction] = []
        candidates: dict[tuple[int, int, int, bool, int], SearchNode] = {}
        for node in beam:
            actions = (
                _PLANNER_ACTIONS
                if (step - 1) % PLANNER_ACTION_HOLD == 0
                else (node.last_action,)
            )
            for action in actions:
                x = node.x + action.dx
                y = node.y + action.dy
                if not (
                    PLAYFIELD_LEFT <= x <= PLAYFIELD_RIGHT
                    and PLAYFIELD_TOP <= y <= PLAYFIELD_BOTTOM
                ):
                    continue
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
            lasers=lasers,
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
            if incumbent is None or _node_key(
                candidate,
                step=step,
                selected_items=selected_items,
                target_x=target_x,
                target_y=target_y,
                target_deadline=target_deadline,
            ) < _node_key(
                incumbent,
                step=step,
                selected_items=selected_items,
                target_x=target_x,
                target_y=target_y,
                target_deadline=target_deadline,
            ):
                candidates[quantized] = candidate
        if not candidates:
            break
        beam = sorted(
            candidates.values(),
            key=lambda node: _node_key(
                node,
                step=step,
                selected_items=selected_items,
                target_x=target_x,
                target_y=target_y,
                target_deadline=target_deadline,
            ),
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
    best = min(
        beam,
        key=lambda node: _node_key(
            node,
            step=horizon,
            selected_items=selected_items,
            target_x=target_x,
            target_y=target_y,
            target_deadline=target_deadline,
        ),
    )
    minimum = 9999.0 if math.isinf(best.min_clearance) else best.min_clearance
    immediate = (
        9999.0 if math.isinf(best.immediate_clearance) else best.immediate_clearance
    )
    action = best.first_action
    use_bomb = can_bomb and immediate <= 0.0
    direction_mask = action.direction
    focus_mask = FOCUS if action.focused else 0
    predicted_collections = tuple(
        selected_items[index][0].slot
        for index in range(len(selected_items))
        if best.collected_mask & (1 << index)
    )
    pipeline_clearance = (
        9999.0 if math.isinf(prefix_clearance) else prefix_clearance
    )
    return Decision(
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


def _solve_corridor(
    *,
    source_frame: int,
    player_x: float,
    player_y: float,
    bullets: tuple[Bullet, ...],
    lasers: tuple[Laser, ...],
    snapshot_lag: int,
    required_gate_lane: str | None = None,
    context_key: tuple[int, int | None] | None = None,
) -> CorridorSolution:
    started = time.perf_counter()
    plan = plan_th08_corridor(
        player_x=player_x,
        player_y=player_y,
        bullets=bullets,
        lasers=lasers,
        snapshot_lag=snapshot_lag,
        required_gate_lane=required_gate_lane,
    )
    constraint_honored = (
        required_gate_lane is None
        or (plan.reachable and plan.lane == required_gate_lane)
    )
    if required_gate_lane is not None and not constraint_honored:
        plan = plan_th08_corridor(
            player_x=player_x,
            player_y=player_y,
            bullets=bullets,
            lasers=lasers,
            snapshot_lag=snapshot_lag,
        )
    return CorridorSolution(
        source_frame=source_frame,
        plan=plan,
        solve_ms=(time.perf_counter() - started) * 1000.0,
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
    if args.auto_confirm_every < 0 or args.auto_confirm_idle_frames < 0:
        raise ValueError("auto-confirm timing arguments cannot be negative")
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
    corridor_solution: CorridorSolution | None = None
    corridor_last_submit = -1000000
    corridor_commitment = CorridorCommitment()
    corridor_context: tuple[int, int | None] | None = None
    auto_confirm = AutoConfirmPulse(
        interval_frames=args.auto_confirm_every,
        idle_frames=args.auto_confirm_idle_frames,
    )
    last_frame_progress = time.perf_counter()
    last_frozen_confirm = float("-inf")
    frozen_confirm_eligible = False
    if not args.local_only:
        corridor_executor = ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix="th08-corridor",
        )
    try:
        identity = verify_target(reader)
        output.write(json.dumps({"kind": "identity", **identity}) + "\n")
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
        if state["input_raw"]:
            raise RuntimeError("physical gameplay input is already active")
        _require_foreground(api, pid)
        gameplay_armed = True
        deadline = time.perf_counter() + args.duration
        while time.perf_counter() < deadline:
            if args.stop_file is not None and args.stop_file.exists():
                termination_reason = "external_stop"
                break
            counter = reader.u32(ADDR_ENEMY_MANAGER_FRAME)
            if counter == previous_counter:
                now = time.perf_counter()
                engine_flags = reader.u32(ADDR_ENGINE_FLAGS)
                if not engine_flags & 0x04:
                    termination_reason = "gameplay_ended"
                    break
                bomb_active = reader.u32(
                    ADDR_PLAYER + PLAYER_BOMB_ACTIVE_OFFSET
                )
                if auto_confirm.frozen_pulse_due(
                    now=now,
                    last_progress=last_frame_progress,
                    last_pulse=last_frozen_confirm,
                    eligible=frozen_confirm_eligible and not bomb_active,
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
            if previous_counter is not None and counter != previous_counter + 1:
                gaps += 1
            state = observe_state(reader)
            if not state["gameplay_active"] or state["route_id"] != 2:
                termination_reason = "gameplay_ended"
                break
            spell_state = state["spell"]
            corridor_context = (
                int(state["stage_route_index"]),
                (
                    int(spell_state["spell_id"])
                    if spell_state["active"]
                    else None
                ),
            )
            if corridor_commitment.set_context(corridor_context):
                corridor_solution = None
                if (
                    corridor_future is not None
                    and corridor_future.cancel()
                ):
                    corridor_future = None
            iterations += 1
            if iterations % 30 == 0:
                _require_foreground(api, pid)
            read_started = time.perf_counter()
            bullet_blob = reader.read(BULLET_POOL_BASE, BULLET_POOL_SIZE * BULLET_STRIDE)
            laser_blob = reader.read(LASER_POOL_BASE, LASER_POOL_SIZE * LASER_STRIDE)
            item_blob = reader.read(
                ITEM_MANAGER_BASE, ITEM_POOL_SIZE * ITEM_STRIDE
            )
            counter_after_read = reader.u32(0x0164D30C)
            read_ms = (time.perf_counter() - read_started) * 1000.0
            snapshot_lag = max(0, counter_after_read - int(state["enemy_manager_frame"]))
            bullets = decode_bullets(bullet_blob)
            lasers = decode_lasers(laser_blob)
            items = decode_items(item_blob)
            player = state["player"]
            resources = state["resources"]
            if resources is None:
                termination_reason = "resources_unavailable"
                break
            can_bomb = (
                args.normal_bomb
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
            control_origin_x, control_origin_y = _project_player_for_read_lag(
                float(player["x"]),
                float(player["y"]),
                previous_mask,
                args.control_delay_frames,
            )
            corridor_updated = False
            if corridor_future is not None and corridor_future.done():
                completed_solution = corridor_future.result()
                corridor_future = None
                if completed_solution.context_key == corridor_context:
                    corridor_solution = completed_solution
                    corridor_commitment.accept(
                        completed_solution,
                        current_frame=counter_after_read,
                    )
                    corridor_updated = True
            if (
                corridor_executor is not None
                and corridor_future is None
                and counter_after_read - corridor_last_submit
                >= args.corridor_every
            ):
                corridor_future = corridor_executor.submit(
                    _solve_corridor,
                    source_frame=counter_after_read,
                    player_x=projected_player_x,
                    player_y=projected_player_y,
                    bullets=bullets,
                    lasers=lasers,
                    snapshot_lag=snapshot_lag,
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
                    + args.control_delay_frames
                ),
                lookahead_frames=args.corridor_lookahead,
                max_age_frames=args.corridor_max_age,
            )
            plan_started = time.perf_counter()
            decision = choose_action(
                player_x=float(player["x"]),
                player_y=float(player["y"]),
                bullets=bullets,
                lasers=lasers,
                previous_direction=previous_direction,
                can_bomb=can_bomb,
                items=items,
                power=float(resources["power"]),
                bombs=float(resources["bombs"]),
                previous_focus=bool(previous_mask & FOCUS),
                snapshot_lag=snapshot_lag,
                control_delay_frames=args.control_delay_frames,
                horizon=args.horizon,
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
            )
            plan_ms = (time.perf_counter() - plan_started) * 1000.0
            phase_now = reader.u8(0x017D5EF8)
            predeath_now = reader.i32(0x017D5EF8 + 0xE2A68)
            counter_at_action = reader.u32(0x0164D30C)
            hit_started = phase_now == 2 and previous_action_phase != 2
            if hit_started:
                hit_count += 1
                if (
                    args.stop_after_hits
                    and hit_count >= args.stop_after_hits
                    and stop_after_frame is None
                ):
                    stop_after_frame = counter_at_action + args.post_hit_frames
            can_deathbomb = (
                phase_now == 2
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
                eligible=(
                    phase_now in (0, 3)
                    and not player["bomb_active"]
                    and not bullets
                    and not lasers
                    and not items
                ),
                mask=decision.mask,
            )
            if auto_confirm_event is not None:
                decision = replace(decision, mask=auto_confirm_mask)
            frozen_confirm_eligible = (
                phase_now in (0, 3)
                and not player["bomb_active"]
                and not bullets
                and not lasers
                and not items
            )
            transitions = input_transitions(
                previous_mask,
                decision.mask,
                supported_mask=SUPPORTED_INPUT_MASK,
            )
            send_transitions(api, transitions)
            previous_mask = decision.mask
            previous_direction = decision.mask & (UP | DOWN | LEFT | RIGHT)
            current_phase = int(player["phase"])
            current_bombs = resources["bombs"]
            current_power = resources["power"]
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
                record = {
                    "kind": "decision",
                    "frame": counter_at_action,
                    "snapshot_frame": state["enemy_manager_frame"],
                    "snapshot_lag": snapshot_lag,
                    "action_lag": counter_at_action - int(state["enemy_manager_frame"]),
                    "control_delay_frames": args.control_delay_frames,
                    "read_ms": read_ms,
                    "plan_ms": plan_ms,
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
                    "active_bullets": len(bullets),
                    "active_lasers": len(lasers),
                    "active_items": len(items),
                    "action": decision.action,
                    "mask": decision.mask,
                    "focused": decision.planned_focus,
                    "minimum_clearance": decision.min_clearance,
                    "immediate_clearance": decision.immediate_clearance,
                    "pipeline_clearance": decision.pipeline_clearance,
                    "score": decision.score,
                    "item_utility": decision.item_utility,
                    "predicted_collections": decision.predicted_collections,
                    "bomb": decision.bomb,
                    "hit_started": hit_started,
                    "hit_count": hit_count,
                    "auto_confirm": auto_confirm_event,
                }
                if corridor_solution is not None:
                    corridor_record = {
                        "source_frame": corridor_solution.source_frame,
                        "age": counter_at_action
                        - corridor_solution.source_frame,
                        "solve_ms": corridor_solution.solve_ms,
                        "reachable": corridor_solution.plan.reachable,
                        "lane": corridor_solution.plan.lane,
                        "bottleneck_clearance": (
                            corridor_solution.plan.bottleneck_clearance
                        ),
                        "stale": corridor_target is None
                        and corridor_solution.plan.reachable,
                        "commitment": {
                            "active_lane": corridor_commitment.active_lane(
                                counter_at_action
                            ),
                            "expires_frame": (
                                corridor_commitment.expires_frame
                            ),
                            "required_gate_lane": (
                                corridor_solution.required_gate_lane
                            ),
                            "constraint_honored": (
                                corridor_solution.constraint_honored
                            ),
                            "context": corridor_context,
                        },
                    }
                    if corridor_solution.plan.gate is not None:
                        corridor_record["gate"] = {
                            "frame": corridor_solution.plan.gate.frame,
                            "x": corridor_solution.plan.gate.x,
                            "y": corridor_solution.plan.gate.y,
                            "clearance": corridor_solution.plan.gate.clearance,
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
                        [
                            bullet.slot,
                            bullet.x,
                            bullet.y,
                            bullet.vx,
                            bullet.vy,
                            bullet.half_width,
                            bullet.half_height,
                            bullet.transform_flags,
                        ]
                        for bullet in bullets
                        if abs(bullet.x - projected_player_x) <= radius
                        and abs(bullet.y - projected_player_y) <= radius
                    ]
                    record["lasers"] = [
                        [
                            laser.origin_x,
                            laser.origin_y,
                            laser.angle,
                            laser.tail,
                            laser.head,
                            laser.half_width,
                        ]
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
                output.write(
                    json.dumps(record) + "\n"
                )
                output.flush()
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
    parser.add_argument("--beam-width", type=int, default=PLANNER_BEAM_WIDTH)
    parser.add_argument(
        "--control-delay-frames",
        type=int,
        default=CONTROL_DELAY_FRAMES,
        help="player-snapshot-to-actuation delay under the previous input",
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
        "--normal-bomb",
        action="store_true",
        help="permit a pre-hit Bomb when every next-frame move overlaps",
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
    parser.add_argument("--armed", action="store_true")
    return parser


if __name__ == "__main__":
    try:
        raise SystemExit(run(build_parser().parse_args()))
    except Exception as exc:
        print(f"error: {exc}")
        raise SystemExit(1)
