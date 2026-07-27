"""Issue-time deadline, deathbomb, and auto-confirm input overrides."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Callable

from th08_local_planner import Decision


AutoConfirmApply = Callable[..., tuple[int, object | None]]


@dataclass(frozen=True)
class IssueInputOverrideResult:
    decision: Decision
    can_deathbomb: bool
    auto_confirm_event: object | None
    last_bomb_counter: int


def apply_deadline_hold(
    decision: Decision,
    *,
    deadline_missed: bool,
    previous_mask: int,
    focus_bit: int,
    action_name_from_mask: Callable[[int], str],
) -> Decision:
    """Hold the actuator command when a proposal's issue window expired."""
    if not deadline_missed:
        return decision
    return replace(
        decision,
        mask=previous_mask,
        action=f"{action_name_from_mask(previous_mask)}+deadline_hold",
        bomb=False,
        planned_focus=bool(previous_mask & focus_bit),
    )


def apply_post_hit_input_overrides(
    decision: Decision,
    *,
    no_bomb: bool,
    phase_now: int,
    predeath_now: int,
    bomb_stock: float,
    counter_at_action: int,
    last_bomb_counter: int,
    bomb_bit: int,
    auto_confirm_eligible: bool,
    auto_confirm_apply: AutoConfirmApply,
) -> IssueInputOverrideResult:
    """Apply the historical deathbomb/confirm sequence before dispatch."""
    can_deathbomb = (
        not no_bomb
        and phase_now == 2
        and predeath_now > 0
        and bomb_stock > 0
        and counter_at_action - last_bomb_counter > 30
    )
    if can_deathbomb:
        decision = replace(
            decision,
            mask=decision.mask | bomb_bit,
            action=f"{decision.action}+deathbomb",
            bomb=True,
        )
    if decision.bomb:
        last_bomb_counter = counter_at_action
    auto_confirm_mask, auto_confirm_event = auto_confirm_apply(
        frame=counter_at_action,
        eligible=auto_confirm_eligible,
        mask=decision.mask,
    )
    if auto_confirm_event is not None:
        decision = replace(decision, mask=auto_confirm_mask)
    if no_bomb and decision.mask & bomb_bit:
        raise RuntimeError("no-bomb policy produced a Bomb input")
    return IssueInputOverrideResult(
        decision=decision,
        can_deathbomb=can_deathbomb,
        auto_confirm_event=auto_confirm_event,
        last_bomb_counter=last_bomb_counter,
    )


__all__ = [
    "IssueInputOverrideResult",
    "apply_deadline_hold",
    "apply_post_hit_input_overrides",
]
