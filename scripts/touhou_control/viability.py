"""Finite-horizon robust viability on a time-expanded control lattice."""

from __future__ import annotations

import numpy as np

from . import native_backend
from .viability_policy import RobustSafetyValuePolicy, RobustViabilityPolicy
from .viability_transitions import (
    _TransitionBatch,
    _cached_transition_batches,
    _uniform_step,
)
from .viability_types import (
    ControlAction,
    SafetyValueQuery,
    ViabilityConfig,
    ViabilityQuery,
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
    backend: str = "auto",
    terminal_viable: np.ndarray | None = None,
    survival_labels: bool = False,
) -> RobustViabilityPolicy:
    """Compute ``exists action, forall delay`` backward reachability.

    ``clearance_volume`` contains frames ``0..horizon`` inclusive. A transition
    checks every physical frame in its layer and conservatively subtracts the
    nearest-lattice sampling distance from clearance. ``terminal_viable`` can
    further restrict the final safe cells to an externally certified
    continuation set, indexed by active action, row, and column.
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
    if backend not in {"auto", "numpy", "native"}:
        raise ValueError("viability backend must be auto, numpy, or native")
    clearance_volume = np.asarray(clearance_volume, dtype=np.float32)
    if clearance_volume.ndim != 3:
        raise ValueError("clearance volume must have frame, row, and column axes")
    if clearance_volume.shape[1:] != (len(y_axis), len(x_axis)):
        raise ValueError("clearance volume does not match lattice axes")
    horizon_frames = clearance_volume.shape[0] - 1
    if horizon_frames <= 0 or horizon_frames % config.frames_per_layer:
        raise ValueError("clearance horizon must divide into complete layers")
    terminal_mask = None
    if terminal_viable is not None:
        terminal_mask = np.asarray(terminal_viable, dtype=np.bool_)
        expected_terminal_shape = (
            len(actions),
            len(y_axis),
            len(x_axis),
        )
        if terminal_mask.shape != expected_terminal_shape:
            raise ValueError(
                "terminal viability mask must have shape "
                f"{expected_terminal_shape}, got {terminal_mask.shape}"
            )
    if survival_labels and terminal_mask is not None:
        raise ValueError(
            "survival labels do not yet support an external terminal mask"
        )
    if survival_labels and backend == "numpy":
        raise ValueError(
            "fused survival labels currently require the native backend"
        )

    if backend in {"auto", "native"}:
        velocity_x = np.asarray(
            [action.velocity_x for action in actions],
            dtype=np.float64,
        )
        velocity_y = np.asarray(
            [action.velocity_y for action in actions],
            dtype=np.float64,
        )
        native_survival = (
            native_backend.build_survival_viability_arrays(
                x_axis=x_axis,
                y_axis=y_axis,
                clearance_volume=clearance_volume,
                velocity_x=velocity_x,
                velocity_y=velocity_y,
                delay_frames=np.asarray(delay_frames, dtype=np.int32),
                frames_per_layer=config.frames_per_layer,
                required_clearance=config.required_clearance,
                clamp_to_bounds=config.clamp_to_bounds,
            )
            if survival_labels
            else None
        )
        if native_survival is not None:
            (
                survival_frames,
                survival_bottleneck_margins,
                survival_best_action_masks,
                viable,
                safe_action_masks,
            ) = native_survival
            return RobustViabilityPolicy(
                x_axis=x_axis,
                y_axis=y_axis,
                actions=actions,
                delay_frames=delay_frames,
                nominal_delay=nominal_delay,
                config=config,
                viable=viable,
                safe_action_masks=safe_action_masks,
                backend="native_fused_survival",
                survival_frames=survival_frames,
                survival_bottleneck_margins=(
                    survival_bottleneck_margins
                ),
                survival_best_action_masks=survival_best_action_masks,
            )
        if survival_labels:
            raise RuntimeError(
                "native fused survival-label backend is unavailable"
            )
        native_arrays = (
            native_backend.build_viability_arrays(
                x_axis=x_axis,
                y_axis=y_axis,
                clearance_volume=clearance_volume,
                velocity_x=velocity_x,
                velocity_y=velocity_y,
                delay_frames=np.asarray(delay_frames, dtype=np.int32),
                frames_per_layer=config.frames_per_layer,
                required_clearance=config.required_clearance,
                clamp_to_bounds=config.clamp_to_bounds,
                terminal_viable=terminal_mask,
            )
            if not survival_labels
            else None
        )
        if native_arrays is not None:
            viable, safe_action_masks = native_arrays
            return RobustViabilityPolicy(
                x_axis=x_axis,
                y_axis=y_axis,
                actions=actions,
                delay_frames=delay_frames,
                nominal_delay=nominal_delay,
                config=config,
                viable=viable,
                safe_action_masks=safe_action_masks,
                backend="native",
            )
        if backend == "native":
            raise RuntimeError("native viability backend is unavailable")

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
    if terminal_mask is not None:
        viable[layer_count] &= terminal_mask

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


def build_robust_safety_value_policy(
    *,
    x_axis: np.ndarray,
    y_axis: np.ndarray,
    clearance_volume: np.ndarray,
    actions: tuple[ControlAction, ...],
    delay_frames: tuple[int, ...],
    nominal_delay: int,
    config: ViabilityConfig,
    backend: str = "auto",
    compact: bool = False,
) -> RobustSafetyValuePolicy:
    """Compute the threshold-free robust max-min reach-avoid value.

    For a selected action, the value is the minimum over all modeled delay
    branches, every physical transition sample, and the next-layer value.
    The state value is the maximum over selected actions. Consequently,
    thresholding at ``required_clearance`` must reproduce the Boolean
    ``exists action / forall delay`` policy exactly.
    """

    x_axis = np.asarray(x_axis, dtype=np.float32)
    y_axis = np.asarray(y_axis, dtype=np.float32)
    x_step = _uniform_step(x_axis, "x")
    y_step = _uniform_step(y_axis, "y")
    if not actions:
        raise ValueError("safety value requires at least one action")
    if len(actions) > 32:
        raise ValueError("safety-value action masks support at most 32 actions")
    if len({action.name for action in actions}) != len(actions):
        raise ValueError("safety-value action names must be unique")
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
    if backend not in {"auto", "numpy", "native"}:
        raise ValueError("safety-value backend must be auto, numpy, or native")
    clearance_volume = np.asarray(clearance_volume, dtype=np.float32)
    if clearance_volume.ndim != 3:
        raise ValueError("clearance volume must have frame, row, and column axes")
    if clearance_volume.shape[1:] != (len(y_axis), len(x_axis)):
        raise ValueError("clearance volume does not match lattice axes")
    horizon_frames = clearance_volume.shape[0] - 1
    if horizon_frames <= 0 or horizon_frames % config.frames_per_layer:
        raise ValueError("clearance horizon must divide into complete layers")

    if backend in {"auto", "native"}:
        native_arguments = {
            "x_axis": x_axis,
            "y_axis": y_axis,
            "clearance_volume": clearance_volume,
            "velocity_x": np.asarray(
                [action.velocity_x for action in actions],
                dtype=np.float64,
            ),
            "velocity_y": np.asarray(
                [action.velocity_y for action in actions],
                dtype=np.float64,
            ),
            "delay_frames": np.asarray(delay_frames, dtype=np.int32),
            "frames_per_layer": config.frames_per_layer,
            "clamp_to_bounds": config.clamp_to_bounds,
        }
        native_arrays = (
            native_backend.build_safety_policy_arrays(**native_arguments)
            if compact
            else native_backend.build_safety_value_arrays(**native_arguments)
        )
        if native_arrays is not None:
            state_values, second_output = native_arrays
            return RobustSafetyValuePolicy(
                x_axis=x_axis,
                y_axis=y_axis,
                actions=actions,
                delay_frames=delay_frames,
                nominal_delay=nominal_delay,
                config=config,
                state_values=state_values,
                action_values=None if compact else second_output,
                best_action_masks=second_output if compact else None,
                backend="native",
            )
        if backend == "native":
            raise RuntimeError("native safety-value backend is unavailable")

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
    state_values = np.full(
        (layer_count + 1, action_count, rows, columns),
        -np.inf,
        dtype=np.float32,
    )
    action_values = np.full(
        (
            layer_count,
            action_count,
            action_count,
            rows,
            columns,
        ),
        -np.inf,
        dtype=np.float32,
    )
    state_values[layer_count] = clearance_volume[horizon_frames][
        None, :, :
    ]
    selected_indices = np.arange(action_count, dtype=np.int32)[
        :, None, None, None
    ]

    for layer in range(layer_count - 1, -1, -1):
        start_frame = layer * config.frames_per_layer
        current_value = clearance_volume[start_frame]
        physical_frames = (
            start_frame
            + np.arange(
                1,
                config.frames_per_layer + 1,
                dtype=np.int32,
            )[None, None, :, None, None]
        )
        for active_index, transition in enumerate(transition_batches):
            sampled_values = (
                clearance_volume[
                    physical_frames,
                    transition.sample_rows,
                    transition.sample_columns,
                ]
                - transition.sample_errors
            )
            sampled_values = np.where(
                transition.sample_inside,
                sampled_values,
                -np.inf,
            )
            branch_values = np.min(sampled_values, axis=2)
            successor_values = state_values[
                layer + 1,
                selected_indices,
                transition.terminal_rows,
                transition.terminal_columns,
            ]
            successor_values = np.where(
                transition.terminal_inside,
                successor_values,
                -np.inf,
            )
            robust_values = np.min(
                np.minimum(branch_values, successor_values),
                axis=1,
            )
            robust_values = np.minimum(
                robust_values,
                current_value[None, :, :],
            )
            action_values[layer, active_index] = robust_values
            state_values[layer, active_index] = np.max(
                robust_values,
                axis=0,
            )

    best_action_masks = None
    retained_action_values: np.ndarray | None = action_values
    if compact:
        best_values = np.max(action_values, axis=2)
        action_bits = np.left_shift(
            np.uint32(1),
            np.arange(action_count, dtype=np.uint32),
        )[None, None, :, None, None]
        best_action_masks = np.bitwise_or.reduce(
            np.where(
                action_values == best_values[:, :, None],
                action_bits,
                np.uint32(0),
            ),
            axis=2,
        )
        retained_action_values = None
    return RobustSafetyValuePolicy(
        x_axis=x_axis,
        y_axis=y_axis,
        actions=actions,
        delay_frames=delay_frames,
        nominal_delay=nominal_delay,
        config=config,
        state_values=state_values,
        action_values=retained_action_values,
        best_action_masks=best_action_masks,
    )


__all__ = [
    "ControlAction",
    "RobustSafetyValuePolicy",
    "RobustViabilityPolicy",
    "SafetyValueQuery",
    "ViabilityConfig",
    "ViabilityQuery",
    "build_robust_safety_value_policy",
    "build_robust_viability_policy",
]
