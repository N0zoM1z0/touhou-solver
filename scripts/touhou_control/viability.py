"""Finite-horizon robust viability on a time-expanded control lattice."""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache

import numpy as np


@dataclass(frozen=True)
class ControlAction:
    """A named constant-velocity action in world units per physical frame."""

    name: str
    velocity_x: float
    velocity_y: float

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("control action name cannot be empty")
        if not math.isfinite(self.velocity_x) or not math.isfinite(self.velocity_y):
            raise ValueError("control action velocity must be finite")


@dataclass(frozen=True)
class ViabilityConfig:
    frames_per_layer: int
    required_clearance: float = 0.0
    clamp_to_bounds: bool = True
    repair_radius_cells: int = 1

    def __post_init__(self) -> None:
        if self.frames_per_layer <= 0:
            raise ValueError("frames per layer must be positive")
        if not math.isfinite(self.required_clearance):
            raise ValueError("required clearance must be finite")
        if self.repair_radius_cells < 0:
            raise ValueError("repair radius cannot be negative")


@dataclass(frozen=True)
class ViabilityQuery:
    available: bool
    layer: int | None
    row: int | None
    column: int | None
    active_action: str
    state_viable: bool
    safe_actions: tuple[str, ...]
    repair_volumes: tuple[tuple[str, int], ...]
    position_error: float
    reason: str

    @property
    def safe_action_count(self) -> int:
        return len(self.safe_actions)

    def repair_volume(self, action: str) -> int:
        for name, volume in self.repair_volumes:
            if name == action:
                return volume
        return 0


@dataclass(frozen=True)
class _TransitionBatch:
    sample_rows: np.ndarray
    sample_columns: np.ndarray
    sample_errors: np.ndarray
    sample_inside: np.ndarray
    terminal_rows: np.ndarray
    terminal_columns: np.ndarray
    terminal_inside: np.ndarray


@dataclass(frozen=True)
class RobustViabilityPolicy:
    """Backward-reachable states and admissible controls for live queries."""

    x_axis: np.ndarray
    y_axis: np.ndarray
    actions: tuple[ControlAction, ...]
    delay_frames: tuple[int, ...]
    nominal_delay: int
    config: ViabilityConfig
    viable: np.ndarray
    safe_action_masks: np.ndarray

    @property
    def layer_count(self) -> int:
        return self.viable.shape[0] - 1

    @property
    def horizon_frames(self) -> int:
        return self.layer_count * self.config.frames_per_layer

    def query(
        self,
        *,
        frame: int,
        x: float,
        y: float,
        active_action: str,
    ) -> ViabilityQuery:
        if frame < 0:
            return ViabilityQuery(
                False,
                None,
                None,
                None,
                active_action,
                False,
                (),
                (),
                math.inf,
                "query frame precedes policy source",
            )
        layer = frame // self.config.frames_per_layer
        if layer >= self.layer_count:
            return ViabilityQuery(
                False,
                layer,
                None,
                None,
                active_action,
                False,
                (),
                (),
                math.inf,
                "query is outside the finite policy horizon",
            )
        action_index = next(
            (
                index
                for index, action in enumerate(self.actions)
                if action.name == active_action
            ),
            None,
        )
        if action_index is None:
            return ViabilityQuery(
                False,
                layer,
                None,
                None,
                active_action,
                False,
                (),
                (),
                math.inf,
                "active action is absent from policy",
            )
        if not (
            float(self.x_axis[0]) <= x <= float(self.x_axis[-1])
            and float(self.y_axis[0]) <= y <= float(self.y_axis[-1])
        ):
            return ViabilityQuery(
                False,
                layer,
                None,
                None,
                active_action,
                False,
                (),
                (),
                math.inf,
                "query position is outside policy bounds",
            )
        column = int(np.argmin(np.abs(self.x_axis - x)))
        row = int(np.argmin(np.abs(self.y_axis - y)))
        position_error = math.hypot(
            x - float(self.x_axis[column]),
            y - float(self.y_axis[row]),
        )
        mask = int(self.safe_action_masks[layer, action_index, row, column])
        safe_actions = tuple(
            action.name
            for index, action in enumerate(self.actions)
            if mask & (1 << index)
        )
        repair_volumes = tuple(
            (
                action.name,
                self._repair_volume(
                    layer=layer,
                    row=row,
                    column=column,
                    active_action_index=action_index,
                    selected_action_index=index,
                ),
            )
            for index, action in enumerate(self.actions)
            if mask & (1 << index)
        )
        state_viable = bool(self.viable[layer, action_index, row, column])
        return ViabilityQuery(
            True,
            layer,
            row,
            column,
            active_action,
            state_viable,
            safe_actions,
            repair_volumes,
            position_error,
            (
                "robust viable actions found"
                if state_viable
                else "robust action set is empty"
            ),
        )

    def _repair_volume(
        self,
        *,
        layer: int,
        row: int,
        column: int,
        active_action_index: int,
        selected_action_index: int,
    ) -> int:
        """Compute the exact worst-branch repair score for one query."""

        active = self.actions[active_action_index]
        selected = self.actions[selected_action_index]
        x = float(self.x_axis[column])
        y = float(self.y_axis[row])
        x_start = float(self.x_axis[0])
        y_start = float(self.y_axis[0])
        x_end = float(self.x_axis[-1])
        y_end = float(self.y_axis[-1])
        x_step = float(self.x_axis[1] - self.x_axis[0])
        y_step = float(self.y_axis[1] - self.y_axis[0])
        branch_volumes = []
        for delay in self.delay_frames:
            selected_frames = self.config.frames_per_layer - delay
            target_x = (
                x
                + active.velocity_x * delay
                + selected.velocity_x * selected_frames
            )
            target_y = (
                y
                + active.velocity_y * delay
                + selected.velocity_y * selected_frames
            )
            inside = (
                x_start <= target_x <= x_end
                and y_start <= target_y <= y_end
            )
            if not inside and not self.config.clamp_to_bounds:
                branch_volumes.append(0)
                continue
            target_x = min(x_end, max(x_start, target_x))
            target_y = min(y_end, max(y_start, target_y))
            target_column = int(np.rint((target_x - x_start) / x_step))
            target_row = int(np.rint((target_y - y_start) / y_step))
            radius = self.config.repair_radius_cells
            row_start = max(0, target_row - radius)
            row_end = min(len(self.y_axis), target_row + radius + 1)
            column_start = max(0, target_column - radius)
            column_end = min(
                len(self.x_axis),
                target_column + radius + 1,
            )
            if layer + 1 == self.layer_count:
                branch_volumes.append(
                    int(
                        np.count_nonzero(
                            self.viable[
                                layer + 1,
                                selected_action_index,
                                row_start:row_end,
                                column_start:column_end,
                            ]
                        )
                    )
                )
                continue
            masks = self.safe_action_masks[
                layer + 1,
                selected_action_index,
                row_start:row_end,
                column_start:column_end,
            ]
            branch_volumes.append(
                sum(int(value).bit_count() for value in masks.flat)
            )
        return min(branch_volumes, default=0)

    def viable_state_count(self, layer: int) -> int:
        if not 0 <= layer <= self.layer_count:
            raise ValueError("layer is outside policy horizon")
        return int(np.count_nonzero(self.viable[layer]))

    def transition_endpoint(
        self,
        *,
        x: float,
        y: float,
        active_action: str,
        next_action: str,
        delay: int | None = None,
    ) -> tuple[float, float]:
        delay = self.nominal_delay if delay is None else delay
        if delay not in self.delay_frames:
            raise ValueError("delay is absent from policy support")
        actions_by_name = {action.name: action for action in self.actions}
        try:
            active = actions_by_name[active_action]
            selected = actions_by_name[next_action]
        except KeyError as error:
            raise ValueError(f"unknown policy action {error.args[0]!r}") from error
        selected_frames = self.config.frames_per_layer - delay
        target_x = (
            x
            + active.velocity_x * delay
            + selected.velocity_x * selected_frames
        )
        target_y = (
            y
            + active.velocity_y * delay
            + selected.velocity_y * selected_frames
        )
        if self.config.clamp_to_bounds:
            target_x = min(float(self.x_axis[-1]), max(float(self.x_axis[0]), target_x))
            target_y = min(float(self.y_axis[-1]), max(float(self.y_axis[0]), target_y))
        return target_x, target_y


def _uniform_step(axis: np.ndarray, name: str) -> float:
    if axis.ndim != 1 or len(axis) < 2:
        raise ValueError(f"{name} axis must contain at least two coordinates")
    differences = np.diff(axis.astype(np.float64))
    if not np.all(differences > 0.0):
        raise ValueError(f"{name} axis must be strictly increasing")
    step = float(differences[0])
    if not np.allclose(differences, step, atol=1e-6):
        raise ValueError(f"{name} axis must be uniformly spaced")
    return step


def _nearest_indices(
    values: np.ndarray,
    *,
    start: float,
    step: float,
    count: int,
    clamp: bool,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    inside = (values >= start) & (values <= start + step * (count - 1))
    if clamp:
        values = np.clip(values, start, start + step * (count - 1))
        inside = np.ones(values.shape, dtype=np.bool_)
    indices = np.rint((values - start) / step).astype(np.int32)
    indices = np.clip(indices, 0, count - 1)
    centers = start + indices.astype(np.float64) * step
    return indices, np.abs(values - centers), inside


def _build_transition_batch(
    *,
    grid_x: np.ndarray,
    grid_y: np.ndarray,
    x_step: float,
    y_step: float,
    active: ControlAction,
    actions: tuple[ControlAction, ...],
    delay_frames: tuple[int, ...],
    config: ViabilityConfig,
) -> _TransitionBatch:
    physical_steps = np.arange(
        1,
        config.frames_per_layer + 1,
        dtype=np.float64,
    )[None, None, :, None, None]
    delays = np.asarray(delay_frames, dtype=np.float64)[
        None, :, None, None, None
    ]
    active_frames = np.minimum(physical_steps, delays)
    selected_frames = np.maximum(physical_steps - delays, 0.0)
    selected_velocity_x = np.asarray(
        [action.velocity_x for action in actions],
        dtype=np.float64,
    )[:, None, None, None, None]
    selected_velocity_y = np.asarray(
        [action.velocity_y for action in actions],
        dtype=np.float64,
    )[:, None, None, None, None]
    target_x = (
        grid_x[None, None, None, :, :]
        + active.velocity_x * active_frames
        + selected_velocity_x * selected_frames
    )
    target_y = (
        grid_y[None, None, None, :, :]
        + active.velocity_y * active_frames
        + selected_velocity_y * selected_frames
    )
    sample_columns, x_error, x_inside = _nearest_indices(
        target_x,
        start=float(grid_x[0, 0]),
        step=x_step,
        count=grid_x.shape[1],
        clamp=config.clamp_to_bounds,
    )
    sample_rows, y_error, y_inside = _nearest_indices(
        target_y,
        start=float(grid_y[0, 0]),
        step=y_step,
        count=grid_y.shape[0],
        clamp=config.clamp_to_bounds,
    )
    sample_rows = sample_rows.astype(np.int16)
    sample_columns = sample_columns.astype(np.int16)
    sample_errors = np.hypot(x_error, y_error).astype(np.float32)
    sample_inside = x_inside & y_inside
    return _TransitionBatch(
        sample_rows=sample_rows,
        sample_columns=sample_columns,
        sample_errors=sample_errors,
        sample_inside=sample_inside,
        terminal_rows=sample_rows[:, :, -1],
        terminal_columns=sample_columns[:, :, -1],
        terminal_inside=sample_inside[:, :, -1],
    )


@lru_cache(maxsize=4)
def _cached_transition_batches(
    *,
    x_start: float,
    x_step: float,
    x_count: int,
    y_start: float,
    y_step: float,
    y_count: int,
    actions: tuple[ControlAction, ...],
    config: ViabilityConfig,
) -> tuple[_TransitionBatch, ...]:
    x_axis = x_start + np.arange(x_count, dtype=np.float64) * x_step
    y_axis = y_start + np.arange(y_count, dtype=np.float64) * y_step
    grid_x, grid_y = np.meshgrid(x_axis, y_axis)
    return tuple(
        _build_transition_batch(
            grid_x=grid_x,
            grid_y=grid_y,
            x_step=x_step,
            y_step=y_step,
            active=active,
            actions=actions,
            delay_frames=tuple(range(config.frames_per_layer + 1)),
            config=config,
        )
        for active in actions
    )


def build_robust_viability_policy(
    *,
    x_axis: np.ndarray,
    y_axis: np.ndarray,
    clearance_volume: np.ndarray,
    actions: tuple[ControlAction, ...],
    delay_frames: tuple[int, ...],
    nominal_delay: int,
    config: ViabilityConfig,
) -> RobustViabilityPolicy:
    """Compute ``exists action, forall delay`` backward reachability.

    ``clearance_volume`` contains frames ``0..horizon`` inclusive. A transition
    checks every physical frame in its layer and conservatively subtracts the
    nearest-lattice sampling distance from clearance.
    """

    x_axis = np.asarray(x_axis, dtype=np.float32)
    y_axis = np.asarray(y_axis, dtype=np.float32)
    x_step = _uniform_step(x_axis, "x")
    y_step = _uniform_step(y_axis, "y")
    if not actions:
        raise ValueError("viability requires at least one action")
    if len(actions) > 32:
        raise ValueError("viability action masks support at most 32 actions")
    if len({action.name for action in actions}) != len(actions):
        raise ValueError("viability action names must be unique")
    if (
        not delay_frames
        or tuple(sorted(set(delay_frames))) != delay_frames
        or delay_frames[0] < 0
    ):
        raise ValueError("delay support must be sorted, unique, and nonnegative")
    if delay_frames[-1] > config.frames_per_layer:
        raise ValueError("delay cannot exceed frames per control layer")
    if nominal_delay not in delay_frames:
        raise ValueError("nominal delay must belong to delay support")
    clearance_volume = np.asarray(clearance_volume, dtype=np.float32)
    if clearance_volume.ndim != 3:
        raise ValueError("clearance volume must have frame, row, and column axes")
    if clearance_volume.shape[1:] != (len(y_axis), len(x_axis)):
        raise ValueError("clearance volume does not match lattice axes")
    horizon_frames = clearance_volume.shape[0] - 1
    if horizon_frames <= 0 or horizon_frames % config.frames_per_layer:
        raise ValueError("clearance horizon must divide into complete layers")

    complete_transition_batches = _cached_transition_batches(
        x_start=float(x_axis[0]),
        x_step=x_step,
        x_count=len(x_axis),
        y_start=float(y_axis[0]),
        y_step=y_step,
        y_count=len(y_axis),
        actions=actions,
        config=config,
    )
    delay_indices = np.asarray(delay_frames, dtype=np.intp)
    contiguous_delays = delay_frames == tuple(
        range(delay_frames[0], delay_frames[-1] + 1)
    )
    delay_selection: slice | np.ndarray = (
        slice(delay_frames[0], delay_frames[-1] + 1)
        if contiguous_delays
        else delay_indices
    )
    transition_batches = tuple(
        _TransitionBatch(
            sample_rows=batch.sample_rows[:, delay_selection],
            sample_columns=batch.sample_columns[:, delay_selection],
            sample_errors=batch.sample_errors[:, delay_selection],
            sample_inside=batch.sample_inside[:, delay_selection],
            terminal_rows=batch.terminal_rows[:, delay_selection],
            terminal_columns=batch.terminal_columns[:, delay_selection],
            terminal_inside=batch.terminal_inside[:, delay_selection],
        )
        for batch in complete_transition_batches
    )

    layer_count = horizon_frames // config.frames_per_layer
    action_count = len(actions)
    rows = len(y_axis)
    columns = len(x_axis)
    viable = np.zeros(
        (layer_count + 1, action_count, rows, columns),
        dtype=np.bool_,
    )
    safe_action_masks = np.zeros(
        (layer_count, action_count, rows, columns),
        dtype=np.uint32,
    )
    terminal_safe = (
        clearance_volume[horizon_frames] > config.required_clearance
    )
    viable[layer_count] = terminal_safe[None, :, :]

    for layer in range(layer_count - 1, -1, -1):
        start_frame = layer * config.frames_per_layer
        current_safe = (
            clearance_volume[start_frame] > config.required_clearance
        )
        physical_frames = (
            start_frame
            + np.arange(
                1,
                config.frames_per_layer + 1,
                dtype=np.int32,
            )[None, None, :, None, None]
        )
        selected_indices = np.arange(action_count, dtype=np.int32)[
            :, None, None, None
        ]
        action_bits = (
            np.left_shift(
                np.uint32(1),
                np.arange(action_count, dtype=np.uint32),
            )
        )[:, None, None]
        for active_index, transition in enumerate(transition_batches):
            sampled_clearance = clearance_volume[
                physical_frames,
                transition.sample_rows,
                transition.sample_columns,
            ]
            branch_safe = np.all(
                transition.sample_inside
                & (
                    sampled_clearance - transition.sample_errors
                    > config.required_clearance
                ),
                axis=2,
            )
            successor_viable = viable[
                layer + 1,
                selected_indices,
                transition.terminal_rows,
                transition.terminal_columns,
            ]
            robust = np.all(
                branch_safe
                & transition.terminal_inside
                & successor_viable,
                axis=1,
            )
            robust &= current_safe[None, :, :]
            safe_action_masks[layer, active_index] = np.bitwise_or.reduce(
                np.where(robust, action_bits, np.uint32(0)),
                axis=0,
            )
            viable[layer, active_index] = (
                safe_action_masks[layer, active_index] != 0
            )

    return RobustViabilityPolicy(
        x_axis=x_axis,
        y_axis=y_axis,
        actions=actions,
        delay_frames=delay_frames,
        nominal_delay=nominal_delay,
        config=config,
        viable=viable,
        safe_action_masks=safe_action_masks,
    )


__all__ = [
    "ControlAction",
    "RobustViabilityPolicy",
    "ViabilityConfig",
    "ViabilityQuery",
    "build_robust_viability_policy",
]
