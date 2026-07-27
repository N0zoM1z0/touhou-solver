"""Queryable Boolean and signed-clearance viability policy objects."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .viability_types import (
    ControlAction,
    SafetyValueQuery,
    ViabilityConfig,
    ViabilityQuery,
)


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
    backend: str = "numpy"
    survival_frames: np.ndarray | None = None
    survival_bottleneck_margins: np.ndarray | None = None
    survival_best_action_masks: np.ndarray | None = None

    @property
    def layer_count(self) -> int:
        return self.viable.shape[0] - 1

    @property
    def horizon_frames(self) -> int:
        return self.layer_count * self.config.frames_per_layer

    def project_to_lattice(
        self,
        *,
        x: float,
        y: float,
    ) -> tuple[float, float, int, int, float]:
        """Project with the same round-to-even rule used by the kernel."""

        x_start = float(self.x_axis[0])
        y_start = float(self.y_axis[0])
        x_step = float(self.x_axis[1] - self.x_axis[0])
        y_step = float(self.y_axis[1] - self.y_axis[0])
        column = int(np.rint((x - x_start) / x_step))
        row = int(np.rint((y - y_start) / y_step))
        column = min(len(self.x_axis) - 1, max(0, column))
        row = min(len(self.y_axis) - 1, max(0, row))
        projected_x = float(self.x_axis[column])
        projected_y = float(self.y_axis[row])
        return (
            projected_x,
            projected_y,
            row,
            column,
            math.hypot(x - projected_x, y - projected_y),
        )

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
        _, _, row, column, position_error = self.project_to_lattice(
            x=x,
            y=y,
        )
        mask = int(self.safe_action_masks[layer, action_index, row, column])
        safe_indices = tuple(
            index
            for index in range(len(self.actions))
            if mask & (1 << index)
        )
        safe_actions = tuple(self.actions[index].name for index in safe_indices)
        repair_indices = safe_indices or tuple(range(len(self.actions)))
        repair_candidates = tuple(
            (
                self.actions[index].name,
                self._repair_volume(
                    layer=layer,
                    row=row,
                    column=column,
                    active_action_index=action_index,
                    selected_action_index=index,
                ),
            )
            for index in repair_indices
        )
        repair_volumes = (
            repair_candidates
            if safe_indices
            else tuple(
                (name, volume)
                for name, volume in repair_candidates
                if volume > 0
            )
        )
        recovery_distances = ()
        if not safe_indices and not repair_volumes:
            recovery_distances = tuple(
                (self.actions[index].name, distance)
                for index in range(len(self.actions))
                if math.isfinite(
                    distance := self._recovery_distance(
                        layer=layer,
                        row=row,
                        column=column,
                        active_action_index=action_index,
                        selected_action_index=index,
                    )
                )
            )
        state_viable = bool(self.viable[layer, action_index, row, column])
        survival_frames = None
        survival_bottleneck_margin = None
        survival_best_actions = ()
        if (
            self.survival_frames is not None
            and self.survival_bottleneck_margins is not None
            and self.survival_best_action_masks is not None
        ):
            state_index = (layer, action_index, row, column)
            survival_frames = int(self.survival_frames[state_index])
            survival_bottleneck_margin = float(
                self.survival_bottleneck_margins[state_index]
            )
            best_mask = int(
                self.survival_best_action_masks[state_index]
            )
            survival_best_actions = tuple(
                action.name
                for index, action in enumerate(self.actions)
                if best_mask & (1 << index)
            )
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
                else (
                    "robust action set is empty; recovery neighborhoods found"
                    if repair_volumes
                    else (
                        "robust action set is empty; distant recovery found"
                        if recovery_distances
                        else (
                            "robust action set and recovery neighborhoods "
                            "are empty"
                        )
                    )
                )
            ),
            recovery_distances,
            survival_frames,
            survival_bottleneck_margin,
            survival_best_actions,
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

    def _recovery_distance(
        self,
        *,
        layer: int,
        row: int,
        column: int,
        active_action_index: int,
        selected_action_index: int,
    ) -> float:
        """Return worst-delay distance to the next-layer viable kernel.

        This is soft guidance for a state already outside the proof. It does
        not test the selected transition's collision safety; the exact local
        controller remains authoritative for that.
        """

        viable_rows, viable_columns = np.nonzero(
            self.viable[layer + 1, selected_action_index]
        )
        if not viable_rows.size:
            return math.inf
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
        viable_x = self.x_axis[viable_columns].astype(np.float64)
        viable_y = self.y_axis[viable_rows].astype(np.float64)
        branch_distances: list[float] = []
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
                return math.inf
            target_x = min(x_end, max(x_start, target_x))
            target_y = min(y_end, max(y_start, target_y))
            target_column = int(np.rint((target_x - x_start) / x_step))
            target_row = int(np.rint((target_y - y_start) / y_step))
            projected_x = float(self.x_axis[target_column])
            projected_y = float(self.y_axis[target_row])
            squared = (
                np.square(viable_x - projected_x)
                + np.square(viable_y - projected_y)
            )
            branch_distances.append(float(math.sqrt(float(np.min(squared)))))
        return max(branch_distances, default=math.inf)

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



@dataclass(frozen=True)
class RobustSafetyValuePolicy:
    """Max-min reach-avoid clearance values over the viability lattice."""

    x_axis: np.ndarray
    y_axis: np.ndarray
    actions: tuple[ControlAction, ...]
    delay_frames: tuple[int, ...]
    nominal_delay: int
    config: ViabilityConfig
    state_values: np.ndarray
    action_values: np.ndarray | None
    best_action_masks: np.ndarray | None = None
    backend: str = "numpy"

    @property
    def layer_count(self) -> int:
        return self.state_values.shape[0] - 1

    @property
    def horizon_frames(self) -> int:
        return self.layer_count * self.config.frames_per_layer

    def threshold_arrays(
        self,
        required_clearance: float,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Recover Boolean viability and safe-action masks at a threshold."""

        if not math.isfinite(required_clearance):
            raise ValueError("required clearance must be finite")
        if self.action_values is None:
            raise ValueError(
                "compact safety policy does not retain every action value"
            )
        action_safe = self.action_values > required_clearance
        action_bits = np.left_shift(
            np.uint32(1),
            np.arange(len(self.actions), dtype=np.uint32),
        )[None, None, :, None, None]
        masks = np.bitwise_or.reduce(
            np.where(action_safe, action_bits, np.uint32(0)),
            axis=2,
        )
        viable = self.state_values > required_clearance
        return viable, masks

    def project_to_lattice(
        self,
        *,
        x: float,
        y: float,
    ) -> tuple[int, int, float]:
        x_step = float(self.x_axis[1] - self.x_axis[0])
        y_step = float(self.y_axis[1] - self.y_axis[0])
        column = int(np.rint((x - float(self.x_axis[0])) / x_step))
        row = int(np.rint((y - float(self.y_axis[0])) / y_step))
        column = min(len(self.x_axis) - 1, max(0, column))
        row = min(len(self.y_axis) - 1, max(0, row))
        error = math.hypot(
            x - float(self.x_axis[column]),
            y - float(self.y_axis[row]),
        )
        return row, column, error

    def query(
        self,
        *,
        frame: int,
        x: float,
        y: float,
        active_action: str,
    ) -> SafetyValueQuery:
        if frame < 0:
            return SafetyValueQuery(
                False,
                None,
                None,
                None,
                active_action,
                -math.inf,
                (),
                (),
                math.inf,
                "query frame precedes policy source",
            )
        layer = frame // self.config.frames_per_layer
        if layer >= self.layer_count:
            return SafetyValueQuery(
                False,
                layer,
                None,
                None,
                active_action,
                -math.inf,
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
            return SafetyValueQuery(
                False,
                layer,
                None,
                None,
                active_action,
                -math.inf,
                (),
                (),
                math.inf,
                "active action is absent from policy",
            )
        if not (
            float(self.x_axis[0]) <= x <= float(self.x_axis[-1])
            and float(self.y_axis[0]) <= y <= float(self.y_axis[-1])
        ):
            return SafetyValueQuery(
                False,
                layer,
                None,
                None,
                active_action,
                -math.inf,
                (),
                (),
                math.inf,
                "query position is outside policy bounds",
            )
        row, column, position_error = self.project_to_lattice(x=x, y=y)
        state_value = float(
            self.state_values[layer, action_index, row, column]
        )
        if self.action_values is not None:
            values = self.action_values[
                layer,
                action_index,
                :,
                row,
                column,
            ]
            named_values = tuple(
                (action.name, float(values[index]))
                for index, action in enumerate(self.actions)
            )
            best_value = float(np.max(values))
            best_actions = tuple(
                action.name
                for index, action in enumerate(self.actions)
                if float(values[index]) == best_value
            )
        else:
            if self.best_action_masks is None:
                raise RuntimeError(
                    "compact safety policy is missing best-action masks"
                )
            mask = int(
                self.best_action_masks[
                    layer,
                    action_index,
                    row,
                    column,
                ]
            )
            named_values = ()
            best_actions = tuple(
                action.name
                for index, action in enumerate(self.actions)
                if mask & (1 << index)
            )
        return SafetyValueQuery(
            True,
            layer,
            row,
            column,
            active_action,
            state_value,
            named_values,
            best_actions,
            position_error,
            "robust max-min safety values found",
        )



__all__ = [
    "RobustSafetyValuePolicy",
    "RobustViabilityPolicy",
]
