"""Bounded local proposal lane that cannot consume incumbent beam capacity."""

from __future__ import annotations

from dataclasses import dataclass
import ctypes
import os
import threading
import time
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


_NATIVE_WORKSPACE: native_backend.LocalSupplementalNativeWorkspace | None = (
    None
)


def native_workspace() -> native_backend.LocalSupplementalNativeWorkspace:
    """Return the process-local reusable complete-rollout workspace."""

    global _NATIVE_WORKSPACE
    if _NATIVE_WORKSPACE is None or _NATIVE_WORKSPACE.closed:
        _NATIVE_WORKSPACE = (
            native_backend.LocalSupplementalNativeWorkspace()
        )
    return _NATIVE_WORKSPACE


@dataclass(frozen=True)
class SupplementalPublication:
    identity: tuple[object, ...]
    nodes: tuple[SupplementalNode, ...]
    terminal_threats: tuple[tuple[int, float], ...] | None
    compute_ms: float


@dataclass(frozen=True)
class SupplementalWorkResult:
    nodes: tuple[SupplementalNode, ...]
    terminal_threats: tuple[tuple[int, float], ...] | None = None


class ExactVersionSupplementalService:
    """Newest-wins worker with exact-identity lookup and no consumer wait."""

    def __init__(self) -> None:
        self._condition = threading.Condition()
        self._workspace = (
            native_backend.LocalSupplementalNativeWorkspace()
        )
        self._revision = 0
        self._pending: tuple[
            int,
            tuple[object, ...],
            Callable[
                [native_backend.LocalSupplementalNativeWorkspace],
                list[SupplementalNode] | SupplementalWorkResult,
            ],
        ] | None = None
        self._publication: SupplementalPublication | None = None
        self._active = False
        self._closed = False
        self._priority_lowered = False
        self._last_outcome = "idle"
        self._thread = threading.Thread(
            target=self._run,
            name="exact-version-supplemental",
            daemon=True,
        )
        self._thread.start()

    def submit(
        self,
        identity: tuple[object, ...],
        job: Callable[
            [native_backend.LocalSupplementalNativeWorkspace],
            list[SupplementalNode] | SupplementalWorkResult,
        ],
    ) -> int:
        with self._condition:
            if self._closed:
                raise RuntimeError("supplemental service is closed")
            self._revision += 1
            revision = self._revision
            self._pending = (revision, identity, job)
            self._publication = None
            self._last_outcome = "submitted"
            if self._active:
                self._workspace.cancel()
            self._condition.notify()
            return revision

    def lookup(
        self,
        identity: tuple[object, ...],
    ) -> SupplementalPublication | None:
        with self._condition:
            publication = self._publication
            if publication is None or publication.identity != identity:
                return None
            return publication

    def snapshot(self) -> dict[str, object]:
        with self._condition:
            return {
                "revision": self._revision,
                "active": self._active,
                "pending": self._pending is not None,
                "published": self._publication is not None,
                "closed": self._closed,
                "priority_lowered": self._priority_lowered,
                "last_outcome": self._last_outcome,
            }

    def close(self) -> None:
        with self._condition:
            if self._closed:
                return
            self._closed = True
            self._pending = None
            if self._active:
                self._workspace.cancel()
            self._condition.notify_all()
        self._thread.join()
        self._workspace.close()

    def _run(self) -> None:
        if os.name == "nt":
            try:
                kernel32 = ctypes.windll.kernel32
                kernel32.GetCurrentThread.restype = ctypes.c_void_p
                kernel32.SetThreadPriority.argtypes = [
                    ctypes.c_void_p,
                    ctypes.c_int,
                ]
                self._priority_lowered = bool(
                    kernel32.SetThreadPriority(
                        kernel32.GetCurrentThread(),
                        -1,  # THREAD_PRIORITY_BELOW_NORMAL
                    )
                )
            except (AttributeError, OSError):
                self._priority_lowered = False
        while True:
            with self._condition:
                while self._pending is None and not self._closed:
                    self._condition.wait()
                if self._closed:
                    return
                pending = self._pending
                self._pending = None
                self._active = True
            assert pending is not None
            revision, identity, job = pending
            started_ns = time.perf_counter_ns()
            nodes: tuple[SupplementalNode, ...] | None = None
            terminal_threats: tuple[tuple[int, float], ...] | None = None
            try:
                result = job(self._workspace)
                if isinstance(result, SupplementalWorkResult):
                    nodes = result.nodes
                    terminal_threats = result.terminal_threats
                else:
                    nodes = tuple(result)
            except native_backend.LocalSupplementalNativeCancelledError:
                nodes = None
                outcome = "cancelled"
            except native_backend.LocalSupplementalNativeDeadlineError:
                nodes = None
                outcome = "deadline"
            except Exception:
                nodes = None
                outcome = "error"
            else:
                outcome = "completed"
            compute_ms = (
                time.perf_counter_ns() - started_ns
            ) / 1_000_000.0
            with self._condition:
                self._active = False
                if (
                    not self._closed
                    and revision == self._revision
                    and self._pending is None
                    and nodes is not None
                ):
                    self._publication = SupplementalPublication(
                        identity,
                        nodes,
                        terminal_threats,
                        compute_ms,
                    )
                    self._last_outcome = "published"
                elif revision != self._revision:
                    self._last_outcome = "discarded_stale"
                else:
                    self._last_outcome = outcome
                self._condition.notify_all()


def search_supplemental_local_beam_native(
    *,
    initial: SupplementalNode,
    actions: tuple[SupplementalAction, ...],
    allowed_first_actions: frozenset[str],
    action_hold_frames: int,
    horizon: int,
    beam_width: int,
    bullet_frames: tuple[tuple[np.ndarray, ...], ...],
    laser_frames: tuple[tuple[np.ndarray, ...], ...],
    body_base_x: np.ndarray,
    body_base_y: np.ndarray,
    body_velocity_x: np.ndarray,
    body_velocity_y: np.ndarray,
    body_half_width: np.ndarray,
    body_half_height: np.ndarray,
    player_radius: float,
    control_delay_frames: int,
    previous_direction: int,
    previous_focused: bool,
    preserve_previous_direction_inertia: bool,
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
    absolute_deadline_ns: int | None = None,
    workspace: (
        native_backend.LocalSupplementalNativeWorkspace | None
    ) = None,
) -> list[SupplementalNode]:
    """Run the exact quantized lane behind one all-or-nothing C++ call."""

    action_count = len(actions)
    result = (workspace or native_workspace()).query(
        horizon=horizon,
        action_hold_frames=action_hold_frames,
        beam_width=beam_width,
        control_delay_frames=control_delay_frames,
        initial_x=initial.x,
        initial_y=initial.y,
        initial_first_action=initial.first_action,
        initial_last_action=initial.last_action,
        initial_risk=initial.risk,
        initial_collisions=initial.collisions,
        initial_minimum_clearance=initial.min_clearance,
        initial_immediate_clearance=initial.immediate_clearance,
        action_direction=np.fromiter(
            (action.direction for action in actions),
            dtype=np.int32,
            count=action_count,
        ),
        action_dx=np.fromiter(
            (action.dx for action in actions),
            dtype=np.float64,
            count=action_count,
        ),
        action_dy=np.fromiter(
            (action.dy for action in actions),
            dtype=np.float64,
            count=action_count,
        ),
        action_focused=np.fromiter(
            (action.focused for action in actions),
            dtype=np.uint8,
            count=action_count,
        ),
        action_allowed=np.fromiter(
            (
                action.name in allowed_first_actions
                for action in actions
            ),
            dtype=np.uint8,
            count=action_count,
        ),
        certificate_collisions=certificate_collisions,
        certificate_minimum=certificate_minimum,
        survival_preferred=survival_preferred,
        safety_preferred=safety_preferred,
        recovery_distance=recovery_distance,
        repair_volume=repair_volume,
        bullet_frames=bullet_frames,
        laser_frames=laser_frames,
        body_base_x=body_base_x,
        body_base_y=body_base_y,
        body_velocity_x=body_velocity_x,
        body_velocity_y=body_velocity_y,
        body_half_width=body_half_width,
        body_half_height=body_half_height,
        player_radius=player_radius,
        preserve_previous_direction_inertia=(
            preserve_previous_direction_inertia
        ),
        previous_direction=previous_direction,
        previous_focused=previous_focused,
        target_x=target_x,
        target_y=target_y,
        target_deadline=target_deadline,
        item_safety_clearance=item_safety_clearance,
        playfield_left=playfield_left,
        playfield_right=playfield_right,
        playfield_top=playfield_top,
        playfield_bottom=playfield_bottom,
        recovery_reserve_distance=recovery_reserve_distance,
        supplemental_reserve_distance=supplemental_reserve_distance,
        diagonal_speed=diagonal_speed,
        cardinal_speed=cardinal_speed,
        absolute_deadline_ns=absolute_deadline_ns,
    )
    return [
        SupplementalNode(
            x=float(result.x[index]),
            y=float(result.y[index]),
            first_action=int(result.first_action[index]),
            last_action=int(result.last_action[index]),
            risk=float(result.risk[index]),
            collisions=int(result.collisions[index]),
            min_clearance=float(result.minimum_clearance[index]),
            immediate_clearance=float(result.immediate_clearance[index]),
        )
        for index in range(len(result))
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
