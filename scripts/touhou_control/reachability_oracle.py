"""Independent scalar oracle for finite robust survival games.

This module is deliberately small and loop-based.  It is not a live backend;
it exists to check vectorized/native recurrences and to define a weight-free
fallback once the positive viability kernel is empty.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from .viability import ControlAction, ViabilityConfig


@dataclass(frozen=True, order=True)
class SurvivalLabel:
    """Lexicographic robust-survival value.

    More guaranteed collision-free physical frames always wins.  Only when
    that integer is tied does the bottleneck signed clearance break the tie.
    This prevents a shallow immediate collision from outranking a deeper
    collision that can be postponed.
    """

    guaranteed_frames: int
    bottleneck_margin: float


@dataclass(frozen=True)
class ScalarSurvivalQuery:
    """One state query from the scalar robust-game oracle."""

    layer: int
    row: int
    column: int
    active_action: str
    remaining_frames: int
    state_label: SurvivalLabel
    action_labels: tuple[tuple[str, SurvivalLabel], ...]
    best_actions: tuple[str, ...]

    @property
    def winning(self) -> bool:
        return (
            self.state_label.guaranteed_frames == self.remaining_frames
            and self.state_label.bottleneck_margin > 0.0
        )

    def action_label(self, action: str) -> SurvivalLabel:
        for name, label in self.action_labels:
            if name == action:
                return label
        raise KeyError(action)


def _uniform_axis(axis: np.ndarray, name: str) -> tuple[np.ndarray, float]:
    values = np.asarray(axis, dtype=np.float64)
    if values.ndim != 1 or len(values) < 2:
        raise ValueError(f"{name} axis must contain at least two points")
    differences = np.diff(values)
    if not np.all(differences > 0.0):
        raise ValueError(f"{name} axis must be strictly increasing")
    step = float(differences[0])
    if not np.allclose(differences, step, rtol=0.0, atol=1e-6):
        raise ValueError(f"{name} axis must be uniform")
    return values, step


def scalar_robust_survival_query(
    *,
    x_axis: np.ndarray,
    y_axis: np.ndarray,
    clearance_volume: np.ndarray,
    actions: tuple[ControlAction, ...],
    delay_frames: tuple[int, ...],
    config: ViabilityConfig,
    layer: int,
    row: int,
    column: int,
    active_action: str,
) -> ScalarSurvivalQuery:
    """Solve one lattice state with explicit ``max action / min delay`` loops.

    The first label component is the maximum number of future physical frames
    for which survival can be guaranteed against every modeled delay.  Signed
    bottleneck clearance is a tie-breaker only.  A label covering the complete
    remaining horizon is exactly a Boolean winning-state certificate for the
    same discrete model.
    """

    x_values, x_step = _uniform_axis(x_axis, "x")
    y_values, y_step = _uniform_axis(y_axis, "y")
    clearance = np.asarray(clearance_volume, dtype=np.float64)
    if clearance.ndim != 3 or clearance.shape[1:] != (
        len(y_values),
        len(x_values),
    ):
        raise ValueError("clearance volume does not match the lattice")
    horizon_frames = clearance.shape[0] - 1
    if horizon_frames <= 0 or horizon_frames % config.frames_per_layer:
        raise ValueError("clearance horizon must contain complete layers")
    layer_count = horizon_frames // config.frames_per_layer
    if not 0 <= layer <= layer_count:
        raise ValueError("query layer is outside the horizon")
    if not 0 <= row < len(y_values) or not 0 <= column < len(x_values):
        raise ValueError("query cell is outside the lattice")
    if (
        not delay_frames
        or tuple(sorted(set(delay_frames))) != delay_frames
        or delay_frames[0] < 0
        or delay_frames[-1] > config.frames_per_layer
    ):
        raise ValueError("delay support is invalid")
    if not actions or len({action.name for action in actions}) != len(actions):
        raise ValueError("actions must be nonempty with unique names")
    action_index = next(
        (
            index
            for index, action in enumerate(actions)
            if action.name == active_action
        ),
        None,
    )
    if action_index is None:
        raise ValueError("active action is absent from the action set")

    x_start = float(x_values[0])
    x_end = float(x_values[-1])
    y_start = float(y_values[0])
    y_end = float(y_values[-1])
    frames_per_layer = config.frames_per_layer

    def sample_cell(
        target_x: float,
        target_y: float,
    ) -> tuple[int, int, float] | None:
        inside = (
            x_start <= target_x <= x_end
            and y_start <= target_y <= y_end
        )
        if not inside and not config.clamp_to_bounds:
            return None
        target_x = min(x_end, max(x_start, target_x))
        target_y = min(y_end, max(y_start, target_y))
        target_column = min(
            len(x_values) - 1,
            max(0, int(round((target_x - x_start) / x_step))),
        )
        target_row = min(
            len(y_values) - 1,
            max(0, int(round((target_y - y_start) / y_step))),
        )
        error = math.hypot(
            target_x - float(x_values[target_column]),
            target_y - float(y_values[target_row]),
        )
        return target_row, target_column, error

    @lru_cache(maxsize=None)
    def solve_state(
        state_layer: int,
        state_active_index: int,
        state_row: int,
        state_column: int,
    ) -> tuple[SurvivalLabel, tuple[SurvivalLabel, ...]]:
        start_frame = state_layer * frames_per_layer
        current_margin = (
            float(clearance[start_frame, state_row, state_column])
            - config.required_clearance
        )
        if state_layer == layer_count or current_margin <= 0.0:
            label = SurvivalLabel(0, current_margin)
            return label, tuple(label for _ in actions)

        active = actions[state_active_index]
        state_x = float(x_values[state_column])
        state_y = float(y_values[state_row])
        selected_labels: list[SurvivalLabel] = []
        for selected_index, selected in enumerate(actions):
            branch_labels: list[SurvivalLabel] = []
            for delay in delay_frames:
                bottleneck = current_margin
                terminal: tuple[int, int, float] | None = None
                failed: SurvivalLabel | None = None
                for physical_step in range(1, frames_per_layer + 1):
                    active_frames = min(physical_step, delay)
                    selected_frames = max(physical_step - delay, 0)
                    target_x = (
                        state_x
                        + active.velocity_x * active_frames
                        + selected.velocity_x * selected_frames
                    )
                    target_y = (
                        state_y
                        + active.velocity_y * active_frames
                        + selected.velocity_y * selected_frames
                    )
                    terminal = sample_cell(target_x, target_y)
                    if terminal is None:
                        failed = SurvivalLabel(
                            physical_step - 1,
                            -math.inf,
                        )
                        break
                    next_row, next_column, sample_error = terminal
                    margin = (
                        float(
                            clearance[
                                start_frame + physical_step,
                                next_row,
                                next_column,
                            ]
                        )
                        - sample_error
                        - config.required_clearance
                    )
                    bottleneck = min(bottleneck, margin)
                    if margin <= 0.0:
                        failed = SurvivalLabel(
                            physical_step - 1,
                            bottleneck,
                        )
                        break
                if failed is not None:
                    branch_labels.append(failed)
                    continue
                assert terminal is not None
                terminal_row, terminal_column, _ = terminal
                successor, _ = solve_state(
                    state_layer + 1,
                    selected_index,
                    terminal_row,
                    terminal_column,
                )
                branch_labels.append(
                    SurvivalLabel(
                        frames_per_layer + successor.guaranteed_frames,
                        min(bottleneck, successor.bottleneck_margin),
                    )
                )
            selected_labels.append(min(branch_labels))
        action_labels = tuple(selected_labels)
        return max(action_labels), action_labels

    state_label, action_labels = solve_state(
        layer,
        action_index,
        row,
        column,
    )
    best_actions = tuple(
        action.name
        for action, label in zip(actions, action_labels)
        if label == state_label
    )
    return ScalarSurvivalQuery(
        layer=layer,
        row=row,
        column=column,
        active_action=active_action,
        remaining_frames=(layer_count - layer) * frames_per_layer,
        state_label=state_label,
        action_labels=tuple(
            (action.name, label)
            for action, label in zip(actions, action_labels)
        ),
        best_actions=best_actions,
    )


__all__ = [
    "ScalarSurvivalQuery",
    "SurvivalLabel",
    "scalar_robust_survival_query",
]
