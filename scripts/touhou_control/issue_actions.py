"""Complete issue-action identities for delayed input pipelines."""

from __future__ import annotations

import math
from dataclasses import dataclass

from .viability import ControlAction


@dataclass(frozen=True)
class CompleteMaskAction:
    """One actuator token whose identity is the complete desired input mask."""

    token: str
    complete_mask: int
    movement_label: str
    velocity_x: float
    velocity_y: float

    def __post_init__(self) -> None:
        if not self.token:
            raise ValueError("complete-mask action token cannot be empty")
        if self.complete_mask < 0:
            raise ValueError("complete input mask cannot be negative")
        if not self.movement_label:
            raise ValueError("movement label cannot be empty")
        if not math.isfinite(self.velocity_x) or not math.isfinite(
            self.velocity_y
        ):
            raise ValueError("complete-mask action velocity must be finite")

    def as_control_action(self) -> ControlAction:
        """Expose the unique issue token to an existing pipeline recurrence."""

        return ControlAction(self.token, self.velocity_x, self.velocity_y)


@dataclass(frozen=True)
class CompleteMaskActionSpace:
    """A finite, injective complete-mask alphabet.

    The pipeline recurrence may contain several actions with identical
    velocities.  Equality is deliberately defined by ``token`` / complete
    mask, never by the movement projection.
    """

    supported_mask: int
    actions: tuple[CompleteMaskAction, ...]

    def __post_init__(self) -> None:
        if self.supported_mask < 0:
            raise ValueError("supported input mask cannot be negative")
        if not self.actions:
            raise ValueError("complete-mask action space cannot be empty")
        tokens: set[str] = set()
        masks: set[int] = set()
        for action in self.actions:
            if action.complete_mask & ~self.supported_mask:
                raise ValueError(
                    f"action {action.token!r} uses unsupported input bits"
                )
            if action.token in tokens:
                raise ValueError(
                    f"duplicate complete-mask action token {action.token!r}"
                )
            if action.complete_mask in masks:
                raise ValueError(
                    "complete-mask action masks must be injective"
                )
            tokens.add(action.token)
            masks.add(action.complete_mask)

    @property
    def control_actions(self) -> tuple[ControlAction, ...]:
        return tuple(action.as_control_action() for action in self.actions)

    def action_for_mask(self, complete_mask: int) -> CompleteMaskAction:
        for action in self.actions:
            if action.complete_mask == complete_mask:
                return action
        raise ValueError(
            f"input mask {complete_mask:#x} is outside the action alphabet"
        )

    def action_for_token(self, token: str) -> CompleteMaskAction:
        for action in self.actions:
            if action.token == token:
                return action
        raise ValueError(f"unknown complete-mask action token {token!r}")

    def token_for_mask(self, complete_mask: int) -> str:
        return self.action_for_mask(complete_mask).token

    def mask_for_token(self, token: str) -> int:
        return self.action_for_token(token).complete_mask

    def is_no_write(self, *, held_mask: int, selected_token: str) -> bool:
        """Apply the physical no-write rule to complete desired input."""

        return self.mask_for_token(selected_token) == held_mask


__all__ = [
    "CompleteMaskAction",
    "CompleteMaskActionSpace",
]
