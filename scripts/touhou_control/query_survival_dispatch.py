"""One-shot native query dispatch with the independent scalar fallback."""

from __future__ import annotations

import numpy as np

from . import native_backend
from .query_survival_scalar import scalar_query_local_survival
from .query_survival_types import PendingCommand, QueryLocalSurvivalResult
from .reachability_oracle import SurvivalLabel
from .viability import ControlAction, ViabilityConfig


def query_local_survival(
    *,
    x_axis: np.ndarray,
    y_axis: np.ndarray,
    clearance_volume: np.ndarray,
    actions: tuple[ControlAction, ...],
    delay_frames: tuple[int, ...],
    config: ViabilityConfig,
    start_frame: int,
    row: int,
    column: int,
    observed_action: str,
    pending_command: PendingCommand | None = None,
    backend: str = "auto",
) -> QueryLocalSurvivalResult:
    """Use the query-local native kernel with scalar fallback."""

    if backend not in {"auto", "native", "scalar"}:
        raise ValueError("query survival backend must be auto, native, or scalar")
    action_indices = {
        action.name: index for index, action in enumerate(actions)
    }
    if observed_action not in action_indices:
        raise ValueError("observed action is absent from the action set")
    if (
        pending_command is not None
        and pending_command.action not in action_indices
    ):
        raise ValueError("pending action is absent from the action set")
    native_result = (
        native_backend.query_local_survival_arrays(
            x_axis=x_axis,
            y_axis=y_axis,
            clearance_volume=clearance_volume,
            velocity_x=np.asarray(
                [action.velocity_x for action in actions],
                dtype=np.float64,
            ),
            velocity_y=np.asarray(
                [action.velocity_y for action in actions],
                dtype=np.float64,
            ),
            delay_frames=np.asarray(delay_frames, dtype=np.int32),
            decision_frames=config.frames_per_layer,
            required_clearance=config.required_clearance,
            clamp_to_bounds=config.clamp_to_bounds,
            start_frame=start_frame,
            start_row=row,
            start_column=column,
            observed_action_index=action_indices[observed_action],
            pending_action_index=(
                action_indices[pending_command.action]
                if pending_command is not None
                else -1
            ),
            pending_remaining_frames=(
                np.asarray(
                    pending_command.remaining_frames,
                    dtype=np.int32,
                )
                if pending_command is not None
                else None
            ),
        )
        if backend in {"auto", "native"}
        else None
    )
    if native_result is None:
        if backend == "native":
            raise RuntimeError("native query-local survival backend unavailable")
        return scalar_query_local_survival(
            x_axis=x_axis,
            y_axis=y_axis,
            clearance_volume=clearance_volume,
            actions=actions,
            delay_frames=delay_frames,
            config=config,
            start_frame=start_frame,
            row=row,
            column=column,
            observed_action=observed_action,
            pending_command=pending_command,
        )
    (
        state_frames,
        state_margin,
        action_frames,
        action_margins,
        best_mask,
        evaluated_states,
    ) = native_result
    action_labels = tuple(
        (
            action.name,
            SurvivalLabel(
                int(action_frames[index]),
                float(action_margins[index]),
            ),
        )
        for index, action in enumerate(actions)
    )
    return QueryLocalSurvivalResult(
        start_frame=start_frame,
        remaining_frames=clearance_volume.shape[0] - 1 - start_frame,
        row=row,
        column=column,
        observed_action=observed_action,
        pending_command=pending_command,
        state_label=SurvivalLabel(state_frames, state_margin),
        action_labels=action_labels,
        best_actions=tuple(
            action.name
            for index, action in enumerate(actions)
            if best_mask & (1 << index)
        ),
        evaluated_state_count=evaluated_states,
        backend="native_pending_pipeline",
    )



__all__ = ["query_local_survival"]
