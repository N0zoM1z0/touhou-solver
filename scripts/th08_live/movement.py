"""TH08 input masks, movement geometry, and local planner actions."""

from __future__ import annotations

from th08_local_planner import PlannerAction

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
        speed = (
            FOCUSED_DIAGONAL_SPEED
            if diagonal
            else FOCUSED_CARDINAL_SPEED
        )
    else:
        speed = (
            UNFOCUSED_DIAGONAL_SPEED
            if diagonal
            else UNFOCUSED_CARDINAL_SPEED
        )
    return PlannerAction(
        name,
        direction,
        unit_x * speed,
        unit_y * speed,
        focused,
    )


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

PLANNER_ACTIONS = (
    PlannerAction("stay", 0, 0.0, 0.0, True),
    *(
        _action(name, direction, unit_x, unit_y, focused=True)
        for name, direction, unit_x, unit_y in _DIRECTION_ACTIONS
    ),
    *(
        _action(
            f"{name}_fast",
            direction,
            unit_x,
            unit_y,
            focused=False,
        )
        for name, direction, unit_x, unit_y in _DIRECTION_ACTIONS
    ),
)
LOCAL_PIPELINE_STATE_ACTIONS = (
    *PLANNER_ACTIONS,
    PlannerAction("stay_unfocused", 0, 0.0, 0.0, False),
)


def action_name_from_mask(input_mask: int) -> str:
    direction = input_mask & (UP | DOWN | LEFT | RIGHT)
    if direction & (UP | LEFT) == UP | LEFT:
        name = "up_left"
    elif direction & (DOWN | LEFT) == DOWN | LEFT:
        name = "down_left"
    elif direction & (UP | RIGHT) == UP | RIGHT:
        name = "up_right"
    elif direction & (DOWN | RIGHT) == DOWN | RIGHT:
        name = "down_right"
    elif direction & DOWN:
        name = "down"
    elif direction & UP:
        name = "up"
    elif direction & LEFT:
        name = "left"
    elif direction & RIGHT:
        name = "right"
    else:
        return "stay"
    return name if input_mask & FOCUS else f"{name}_fast"


def local_pipeline_action_from_mask(input_mask: int) -> str:
    """Return the injective movement/focus local actuator state."""

    direction = input_mask & (UP | DOWN | LEFT | RIGHT)
    if direction == 0 and not input_mask & FOCUS:
        return "stay_unfocused"
    return action_name_from_mask(input_mask)


__all__ = [
    "BOMB",
    "DOWN",
    "FOCUS",
    "FOCUSED_CARDINAL_SPEED",
    "FOCUSED_DIAGONAL_SPEED",
    "LEFT",
    "LOCAL_PIPELINE_STATE_ACTIONS",
    "PLANNER_ACTIONS",
    "PLAYER_RADIUS",
    "PLAYFIELD_BOTTOM",
    "PLAYFIELD_LEFT",
    "PLAYFIELD_RIGHT",
    "PLAYFIELD_TOP",
    "RIGHT",
    "SHOT",
    "UNFOCUSED_CARDINAL_SPEED",
    "UNFOCUSED_DIAGONAL_SPEED",
    "UP",
    "action_name_from_mask",
    "local_pipeline_action_from_mask",
]
