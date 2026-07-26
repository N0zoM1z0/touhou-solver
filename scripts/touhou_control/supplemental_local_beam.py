"""Bounded local proposal lane that cannot consume incumbent beam capacity."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

from . import native_backend


@dataclass(frozen=True)
class SupplementalAction:
    name: str
    direction: int
    dx: float
    dy: float
    focused: bool


@dataclass(frozen=True)
class SupplementalNode:
    x: float
    y: float
    first_action: int
    last_action: int
    risk: float
    collisions: int
    min_clearance: float
    immediate_clearance: float


HazardQuery = Callable[
    [np.ndarray, np.ndarray, int],
    tuple[np.ndarray, np.ndarray, np.ndarray],
]
TransitionRisk = Callable[
    [SupplementalNode, SupplementalAction, float, float, int],
    float,
]


def _minimum_travel_frames(
    x: float,
    y: float,
    target_x: float,
    target_y: float,
    *,
    diagonal_speed: float,
    cardinal_speed: float,
) -> float:
    horizontal = max(abs(x - target_x) - 6.0, 0.0)
    vertical = max(abs(y - target_y) - 6.0, 0.0)
    diagonal = min(horizontal, vertical)
    straight = max(horizontal, vertical) - diagonal
    return diagonal / diagonal_speed + straight / cardinal_speed


def _boundary_deficit(
    x: float,
    y: float,
    *,
    reserve_distance: float,
    left: float,
    right: float,
    top: float,
    bottom: float,
) -> float:
    if reserve_distance <= 0.0:
        return 0.0
    return sum(
        (
            max(reserve_distance - (x - left), 0.0),
            max(reserve_distance - (right - x), 0.0),
            max(reserve_distance - (y - top), 0.0),
            max(reserve_distance - (bottom - y), 0.0),
        )
    )


def search_supplemental_local_beam(
    *,
    initial: SupplementalNode,
    actions: tuple[SupplementalAction, ...],
    allowed_first_actions: frozenset[str],
    action_hold_frames: int,
    horizon: int,
    beam_width: int,
    beam_dedup_mode: str,
    hazard_query: HazardQuery,
    transition_risk: TransitionRisk,
    control_delay_frames: int,
    target_x: float | None,
    target_y: float | None,
    target_deadline: int | None,
    item_safety_clearance: float,
    playfield_left: float,
    playfield_right: float,
    playfield_top: float,
    playfield_bottom: float,
    recovery_reserve_distance: float,
    supplemental_reserve_distance: float,
    diagonal_speed: float,
    cardinal_speed: float,
    certificate_collisions: np.ndarray,
    certificate_minimum: np.ndarray,
    survival_preferred: np.ndarray,
    safety_preferred: np.ndarray,
    recovery_distance: np.ndarray,
    repair_volume: np.ndarray,
    use_native_reducer: bool,
) -> list[SupplementalNode]:
    """Search one independent proposal lane over already-projected hazards."""

    action_count = len(actions)
    action_fields = (
        np.asarray(certificate_collisions, dtype=np.int32),
        np.asarray(certificate_minimum, dtype=np.float64),
        np.asarray(survival_preferred, dtype=np.uint8),
        np.asarray(safety_preferred, dtype=np.uint8),
        np.asarray(recovery_distance, dtype=np.float64),
        np.asarray(repair_volume, dtype=np.int32),
    )
    if (
        action_count <= 0
        or horizon <= 0
        or beam_width <= 0
        or action_hold_frames <= 0
        or any(
            values.ndim != 1 or len(values) != action_count
            for values in action_fields
        )
    ):
        raise ValueError("invalid supplemental local beam dimensions")
    if beam_dedup_mode not in {
        "quantized",
        "first_action",
        "exact_first_action",
    }:
        raise ValueError("unknown supplemental beam deduplication mode")
    if not allowed_first_actions:
        raise ValueError(
            "supplemental beam requires allowed first actions"
        )

    def key(node: SupplementalNode, *, step: int) -> tuple[object, ...]:
        action = node.first_action
        gate_deficit = 0.0
        if target_x is not None:
            assert target_y is not None
            assert target_deadline is not None
            gate_deficit = max(
                _minimum_travel_frames(
                    node.x,
                    node.y,
                    target_x,
                    target_y,
                    diagonal_speed=diagonal_speed,
                    cardinal_speed=cardinal_speed,
                )
                - max(target_deadline - step, 0),
                0.0,
            )
        return (
            node.collisions,
            int(action_fields[0][action]),
            max(-float(action_fields[1][action]), 0.0),
            max(-node.min_clearance, 0.0),
            0 if action_fields[2][action] else 1,
            gate_deficit,
            -int(action_fields[5][action]),
            _boundary_deficit(
                node.x,
                node.y,
                reserve_distance=supplemental_reserve_distance,
                left=playfield_left,
                right=playfield_right,
                top=playfield_top,
                bottom=playfield_bottom,
            ),
            max(item_safety_clearance - node.min_clearance, 0.0),
            0 if action_fields[3][action] else 1,
            _boundary_deficit(
                node.x,
                node.y,
                reserve_distance=recovery_reserve_distance,
                left=playfield_left,
                right=playfield_right,
                top=playfield_top,
                bottom=playfield_bottom,
            ),
            float(action_fields[4][action]),
            node.risk,
            -node.min_clearance,
        )

    beam = [initial]
    allowed_indices = tuple(
        index
        for index, action in enumerate(actions)
        if action.name in allowed_first_actions
    )
    for step in range(1, horizon + 1):
        drafts: list[
            tuple[
                SupplementalNode,
                int,
                float,
                float,
                float,
            ]
        ] = []
        first_actions: list[int] = []
        for node in beam:
            action_indices = (
                tuple(range(action_count))
                if (step - 1) % action_hold_frames == 0
                else (node.last_action,)
            )
            if step == 1:
                action_indices = allowed_indices
            for action_index in action_indices:
                action = actions[action_index]
                x = min(
                    playfield_right,
                    max(playfield_left, node.x + action.dx),
                )
                y = min(
                    playfield_bottom,
                    max(playfield_top, node.y + action.dy),
                )
                drafts.append(
                    (
                        node,
                        action_index,
                        x,
                        y,
                        transition_risk(
                            node,
                            action,
                            x,
                            y,
                            step,
                        ),
                    )
                )
                first_actions.append(
                    action_index if step == 1 else node.first_action
                )
        if not drafts:
            break
        positions_x = np.fromiter(
            (draft[2] for draft in drafts),
            dtype=np.float32,
            count=len(drafts),
        )
        positions_y = np.fromiter(
            (draft[3] for draft in drafts),
            dtype=np.float32,
            count=len(drafts),
        )
        hazard_risk, hazard_collisions, hazard_clearance = (
            hazard_query(
                positions_x,
                positions_y,
                control_delay_frames + step,
            )
        )
        candidate_risk = np.fromiter(
            (
                draft[0].risk
                + draft[4]
                + float(hazard_risk[index])
                for index, draft in enumerate(drafts)
            ),
            dtype=np.float64,
            count=len(drafts),
        )
        candidate_collisions = np.fromiter(
            (
                draft[0].collisions
                + int(hazard_collisions[index])
                for index, draft in enumerate(drafts)
            ),
            dtype=np.int32,
            count=len(drafts),
        )
        candidate_minimum = np.fromiter(
            (
                min(
                    draft[0].min_clearance,
                    float(hazard_clearance[index]),
                )
                for index, draft in enumerate(drafts)
            ),
            dtype=np.float64,
            count=len(drafts),
        )
        retained_indices = None
        if use_native_reducer and beam_dedup_mode == "quantized":
            retained_indices = (
                native_backend.reduce_local_supplemental_beam(
                    draft_x=np.fromiter(
                        (draft[2] for draft in drafts),
                        dtype=np.float64,
                        count=len(drafts),
                    ),
                    draft_y=np.fromiter(
                        (draft[3] for draft in drafts),
                        dtype=np.float64,
                        count=len(drafts),
                    ),
                    first_action=np.asarray(
                        first_actions,
                        dtype=np.int32,
                    ),
                    last_direction=np.fromiter(
                        (
                            actions[draft[1]].direction
                            for draft in drafts
                        ),
                        dtype=np.int32,
                        count=len(drafts),
                    ),
                    last_focused=np.fromiter(
                        (
                            actions[draft[1]].focused
                            for draft in drafts
                        ),
                        dtype=np.uint8,
                        count=len(drafts),
                    ),
                    collected_mask=np.zeros(
                        len(drafts),
                        dtype=np.uint32,
                    ),
                    risk=candidate_risk,
                    collisions=candidate_collisions,
                    minimum_clearance=candidate_minimum,
                    step=step,
                    beam_width=beam_width,
                    position_quantization=0.5,
                    target_x=target_x,
                    target_y=target_y,
                    target_deadline=target_deadline,
                    item_safety_clearance=item_safety_clearance,
                    playfield_left=playfield_left,
                    playfield_right=playfield_right,
                    playfield_top=playfield_top,
                    playfield_bottom=playfield_bottom,
                    recovery_reserve_distance=(
                        recovery_reserve_distance
                    ),
                    supplemental_reserve_distance=(
                        supplemental_reserve_distance
                    ),
                    diagonal_speed=diagonal_speed,
                    cardinal_speed=cardinal_speed,
                    certificate_collisions=action_fields[0],
                    certificate_minimum=action_fields[1],
                    survival_preferred=action_fields[2],
                    safety_preferred=action_fields[3],
                    recovery_distance=action_fields[4],
                    repair_volume=action_fields[5],
                )
            )

        candidates = [
            SupplementalNode(
                x=draft[2],
                y=draft[3],
                first_action=first_actions[index],
                last_action=draft[1],
                risk=float(candidate_risk[index]),
                collisions=int(candidate_collisions[index]),
                min_clearance=float(candidate_minimum[index]),
                immediate_clearance=(
                    min(
                        draft[0].immediate_clearance,
                        float(hazard_clearance[index]),
                    )
                    if step == 1
                    else draft[0].immediate_clearance
                ),
            )
            for index, draft in enumerate(drafts)
        ]
        if retained_indices is not None:
            beam = [
                candidates[int(index)]
                for index in retained_indices
            ]
            continue

        winners: dict[tuple[object, ...], SupplementalNode] = {}
        for node in candidates:
            action = actions[node.last_action]
            quantized: tuple[object, ...] = (
                int(round(node.x * 0.5)),
                int(round(node.y * 0.5)),
                action.direction,
                action.focused,
                0,
            )
            if beam_dedup_mode == "first_action":
                quantized = (*quantized, node.first_action)
            elif beam_dedup_mode == "exact_first_action":
                quantized = (
                    node.x,
                    node.y,
                    action.direction,
                    action.focused,
                    0,
                    node.first_action,
                )
            incumbent = winners.get(quantized)
            if (
                incumbent is None
                or key(node, step=step) < key(incumbent, step=step)
            ):
                winners[quantized] = node
        if not winners:
            break
        beam = sorted(
            winners.values(),
            key=lambda node: key(node, step=step),
        )[:beam_width]
    return beam
