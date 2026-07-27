"""TH08 complete-mask action alphabet for delayed-pipeline reasoning."""

from __future__ import annotations

from th08_movement_model import (
    INPUT_BOMB,
    INPUT_DOWN,
    INPUT_FOCUS,
    INPUT_LEFT,
    INPUT_RIGHT,
    INPUT_SHOT,
    INPUT_UP,
    ROUTE2_MOVEMENT_PROFILE,
)
from touhou_control.issue_actions import (
    CompleteMaskAction,
    CompleteMaskActionSpace,
)


TH08_DIRECTION_MASK = INPUT_UP | INPUT_DOWN | INPUT_LEFT | INPUT_RIGHT
TH08_ISSUE_SUPPORTED_MASK = (
    INPUT_SHOT | INPUT_FOCUS | TH08_DIRECTION_MASK
)

_DIRECTIONS = (
    ("stay", 0, 0.0, 0.0),
    ("up", INPUT_UP, 0.0, -1.0),
    ("down", INPUT_DOWN, 0.0, 1.0),
    ("left", INPUT_LEFT, -1.0, 0.0),
    ("right", INPUT_RIGHT, 1.0, 0.0),
    ("up_left", INPUT_UP | INPUT_LEFT, -1.0, -1.0),
    ("up_right", INPUT_UP | INPUT_RIGHT, 1.0, -1.0),
    ("down_left", INPUT_DOWN | INPUT_LEFT, -1.0, 1.0),
    ("down_right", INPUT_DOWN | INPUT_RIGHT, 1.0, 1.0),
)


def _movement(
    label: str,
    unit_x: float,
    unit_y: float,
    *,
    focused: bool,
) -> tuple[str, float, float]:
    diagonal = unit_x != 0.0 and unit_y != 0.0
    profile = ROUTE2_MOVEMENT_PROFILE
    if focused:
        speed = (
            profile.focused_diagonal_axis
            if diagonal
            else profile.focused_cardinal
        )
        movement_label = label
    else:
        speed = (
            profile.unfocused_diagonal_axis
            if diagonal
            else profile.unfocused_cardinal
        )
        movement_label = (
            "stay_unfocused" if label == "stay" else f"{label}_fast"
        )
    return movement_label, unit_x * speed, unit_y * speed


def _build_th08_complete_mask_actions() -> tuple[CompleteMaskAction, ...]:
    actions: list[CompleteMaskAction] = []
    for focused in (False, True):
        focus_mask = INPUT_FOCUS if focused else 0
        for label, direction_mask, unit_x, unit_y in _DIRECTIONS:
            movement_label, velocity_x, velocity_y = _movement(
                label,
                unit_x,
                unit_y,
                focused=focused,
            )
            for shooting in (False, True):
                complete_mask = (
                    direction_mask
                    | focus_mask
                    | (INPUT_SHOT if shooting else 0)
                )
                actions.append(
                    CompleteMaskAction(
                        token=f"th08_mask_{complete_mask:02x}",
                        complete_mask=complete_mask,
                        movement_label=movement_label,
                        velocity_x=velocity_x,
                        velocity_y=velocity_y,
                    )
                )
    return tuple(sorted(actions, key=lambda action: action.complete_mask))


TH08_COMPLETE_MASK_ACTION_SPACE = CompleteMaskActionSpace(
    supported_mask=TH08_ISSUE_SUPPORTED_MASK,
    actions=_build_th08_complete_mask_actions(),
)


def th08_complete_mask_token(input_mask: int) -> str:
    """Return the exact no-Bomb issue token or fail closed."""

    if input_mask & INPUT_BOMB:
        raise ValueError("Bomb input is outside physical no-Bomb authority")
    return TH08_COMPLETE_MASK_ACTION_SPACE.token_for_mask(input_mask)


__all__ = [
    "TH08_COMPLETE_MASK_ACTION_SPACE",
    "TH08_DIRECTION_MASK",
    "TH08_ISSUE_SUPPORTED_MASK",
    "th08_complete_mask_token",
]
