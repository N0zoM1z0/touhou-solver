"""Independent scalar oracle for ordered complete-mask input transactions.

The controller still selects one final complete mask.  A physical write,
however, expands that choice into a deterministic sequence of single-key
edges: releases in ascending-bit order, then presses in ascending-bit order.
Between issue and final pickup, nature may expose a monotonically advancing
prefix of that sequence.

This is a deliberately conservative, game-neutral input-publication model.
It does not claim that an enemy-manager frame is an input clock, does not
model player movement or mode transitions, and does not bound the exact
Win32 queue/poll phase.  It is therefore an offline specification, not live
action authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


def _validate_mask(mask: int, *, name: str) -> None:
    if not isinstance(mask, int) or not 0 <= mask <= 0xFFFF:
        raise ValueError(f"{name} must be a 16-bit nonnegative integer")


def _validate_scope(
    masks: Iterable[int],
    *,
    supported_mask: int,
    forbidden_mask: int,
) -> None:
    _validate_mask(supported_mask, name="supported mask")
    _validate_mask(forbidden_mask, name="forbidden mask")
    if forbidden_mask & ~supported_mask:
        raise ValueError("forbidden mask must be a subset of supported mask")
    for mask in masks:
        unsupported = mask & ~supported_mask
        if unsupported:
            raise ValueError(f"unsupported input bits {unsupported:#06x}")
        forbidden = mask & forbidden_mask
        if forbidden:
            raise ValueError(f"forbidden input bits {forbidden:#06x}")


def ordered_mask_path(
    previous_mask: int,
    target_mask: int,
    *,
    supported_mask: int,
    forbidden_mask: int = 0,
) -> tuple[int, ...]:
    """Return masks after each ordered single-key edge, excluding the root."""

    _validate_mask(previous_mask, name="previous mask")
    _validate_mask(target_mask, name="target mask")
    _validate_scope(
        (previous_mask, target_mask),
        supported_mask=supported_mask,
        forbidden_mask=forbidden_mask,
    )
    changed = previous_mask ^ target_mask
    release_bits = tuple(
        1 << index for index in range(16) if changed & previous_mask & (1 << index)
    )
    press_bits = tuple(
        1 << index for index in range(16) if changed & target_mask & (1 << index)
    )
    path: list[int] = []
    current = previous_mask
    for bit in release_bits:
        current &= ~bit
        path.append(current)
    for bit in press_bits:
        current |= bit
        path.append(current)
    assert current == target_mask
    return tuple(path)


@dataclass(frozen=True, order=True)
class OrderedInputExactState:
    """One hidden ordered-transaction state at an observation boundary.

    ``queued_masks`` contains the remaining masks after each unobserved edge.
    Its final entry is the held desired mask.  ``completion_remaining`` is the
    positive number of future input-publication steps by which nature must
    publish that final mask.
    """

    active_mask: int
    held_desired_mask: int
    queued_masks: tuple[int, ...] = ()
    completion_remaining: int | None = None

    def __post_init__(self) -> None:
        _validate_mask(self.active_mask, name="active mask")
        _validate_mask(self.held_desired_mask, name="held desired mask")
        for queued_mask in self.queued_masks:
            _validate_mask(queued_mask, name="queued mask")
        if not self.queued_masks:
            if self.completion_remaining is not None:
                raise ValueError("settled state cannot retain a completion deadline")
            if self.active_mask != self.held_desired_mask:
                raise ValueError("settled state requires active to equal held desired")
            return
        if self.queued_masks[-1] != self.held_desired_mask:
            raise ValueError("queued transaction must end at held desired")
        if (
            not isinstance(self.completion_remaining, int)
            or self.completion_remaining <= 0
        ):
            raise ValueError(
                "pending transaction requires a positive completion deadline"
            )
        previous = self.active_mask
        for queued_mask in self.queued_masks:
            changed = previous ^ queued_mask
            if changed == 0 or changed & (changed - 1):
                raise ValueError("adjacent queued masks must differ by exactly one bit")
            previous = queued_mask

    @property
    def settled(self) -> bool:
        return not self.queued_masks

    @property
    def observation(self) -> OrderedInputObservation:
        return OrderedInputObservation(
            active_mask=self.active_mask,
            held_desired_mask=self.held_desired_mask,
        )


@dataclass(frozen=True, order=True)
class OrderedInputObservation:
    """The actuator identities available to the next controller decision."""

    active_mask: int
    held_desired_mask: int


@dataclass(frozen=True)
class OrderedInputBelief:
    """Observation-compatible set of exact hidden transaction states."""

    states: tuple[OrderedInputExactState, ...]

    def __post_init__(self) -> None:
        if not self.states:
            raise ValueError("ordered-input belief cannot be empty")
        canonical = tuple(sorted(set(self.states)))
        if canonical != self.states:
            raise ValueError("belief states must be sorted, unique, and canonical")
        observations = {state.observation for state in self.states}
        if len(observations) != 1:
            raise ValueError("belief states must share one controller observation")

    @classmethod
    def from_states(
        cls,
        states: Iterable[OrderedInputExactState],
    ) -> OrderedInputBelief:
        return cls(tuple(sorted(set(states))))

    @property
    def observation(self) -> OrderedInputObservation:
        return self.states[0].observation


@dataclass(frozen=True)
class OrderedInputIssueBranch:
    """One exact source/deadline branch after one uniform controller choice."""

    source_state: OrderedInputExactState
    selected_mask: int
    write_required: bool
    older_remaining: int | None
    new_delay: int | None
    successor_state: OrderedInputExactState


@dataclass(frozen=True, order=True)
class OrderedInputHistory:
    """One nature-selected sequence of active masks after publications."""

    active_masks_after_publication: tuple[int, ...]
    successor_state: OrderedInputExactState


def _validate_delay_support(delay_support: tuple[int, ...]) -> None:
    if (
        not delay_support
        or tuple(sorted(set(delay_support))) != delay_support
        or not all(isinstance(delay, int) and delay > 0 for delay in delay_support)
    ):
        raise ValueError(
            "completion-delay support must be sorted, unique, and positive"
        )


def _validate_state_scope(
    state: OrderedInputExactState,
    *,
    supported_mask: int,
    forbidden_mask: int,
) -> None:
    _validate_scope(
        (
            state.active_mask,
            state.held_desired_mask,
            *state.queued_masks,
        ),
        supported_mask=supported_mask,
        forbidden_mask=forbidden_mask,
    )


def issue_ordered_input_belief(
    belief: OrderedInputBelief,
    *,
    selected_mask: int,
    delay_support: tuple[int, ...],
    supported_mask: int,
    forbidden_mask: int = 0,
) -> tuple[OrderedInputIssueBranch, ...]:
    """Apply one final-mask choice uniformly to every hidden belief state.

    Selecting the already-held complete mask is no-write: no new delay is
    sampled and every hidden queue/deadline is preserved.  A real write
    appends its ordered edge path after any older unobserved suffix and
    replaces the final-completion deadline with the newly sampled delay.

    ``delay_support`` is measured in post-issue native publication steps in
    this oracle. TH08's current ``AdaptiveControlDelay`` values instead use a
    snapshot-to-observed-final-input enemy-manager-frame coordinate and must
    not be passed here without a separately validated phase adapter.
    """

    _validate_mask(selected_mask, name="selected mask")
    _validate_scope(
        (selected_mask,),
        supported_mask=supported_mask,
        forbidden_mask=forbidden_mask,
    )
    for state in belief.states:
        _validate_state_scope(
            state,
            supported_mask=supported_mask,
            forbidden_mask=forbidden_mask,
        )

    write_required = selected_mask != belief.observation.held_desired_mask
    if not write_required:
        return tuple(
            OrderedInputIssueBranch(
                source_state=state,
                selected_mask=selected_mask,
                write_required=False,
                older_remaining=state.completion_remaining,
                new_delay=None,
                successor_state=state,
            )
            for state in belief.states
        )

    _validate_delay_support(delay_support)
    branches: list[OrderedInputIssueBranch] = []
    for state in belief.states:
        appended = ordered_mask_path(
            state.held_desired_mask,
            selected_mask,
            supported_mask=supported_mask,
            forbidden_mask=forbidden_mask,
        )
        assert appended
        for new_delay in delay_support:
            successor = OrderedInputExactState(
                active_mask=state.active_mask,
                held_desired_mask=selected_mask,
                queued_masks=state.queued_masks + appended,
                completion_remaining=new_delay,
            )
            branches.append(
                OrderedInputIssueBranch(
                    source_state=state,
                    selected_mask=selected_mask,
                    write_required=True,
                    older_remaining=state.completion_remaining,
                    new_delay=new_delay,
                    successor_state=successor,
                )
            )
    return tuple(branches)


def merge_observation_equivalent_states(
    states: Iterable[OrderedInputExactState],
) -> tuple[OrderedInputBelief, ...]:
    """Merge hidden states before the next observation-conditioned choice."""

    groups: dict[OrderedInputObservation, list[OrderedInputExactState]] = {}
    for state in states:
        groups.setdefault(state.observation, []).append(state)
    return tuple(
        OrderedInputBelief.from_states(groups[observation])
        for observation in sorted(groups)
    )


def belief_after_issue(
    branches: Iterable[OrderedInputIssueBranch],
) -> OrderedInputBelief:
    """Merge exact issue branches that share the immediate observation."""

    branch_tuple = tuple(branches)
    if not branch_tuple:
        raise ValueError("issue branch set cannot be empty")
    return OrderedInputBelief.from_states(
        branch.successor_state for branch in branch_tuple
    )


def advance_ordered_input_state(
    state: OrderedInputExactState,
) -> tuple[OrderedInputExactState, ...]:
    """Enumerate nature's successors after one input-publication step.

    Before the final deadline, nature may stutter or consume any non-final
    ordered prefix.  At the deadline, the held final mask is forced.
    """

    if state.settled:
        return (state,)
    assert state.completion_remaining is not None
    if state.completion_remaining == 1:
        return (
            OrderedInputExactState(
                active_mask=state.held_desired_mask,
                held_desired_mask=state.held_desired_mask,
            ),
        )

    successors: list[OrderedInputExactState] = []
    for consumed in range(len(state.queued_masks)):
        if consumed == 0:
            active_mask = state.active_mask
            queued_masks = state.queued_masks
        else:
            active_mask = state.queued_masks[consumed - 1]
            queued_masks = state.queued_masks[consumed:]
        successors.append(
            OrderedInputExactState(
                active_mask=active_mask,
                held_desired_mask=state.held_desired_mask,
                queued_masks=queued_masks,
                completion_remaining=state.completion_remaining - 1,
            )
        )
    return tuple(sorted(set(successors)))


def advance_ordered_input_belief(
    belief: OrderedInputBelief,
) -> tuple[OrderedInputBelief, ...]:
    """Advance every hidden state, then merge by the newly seen observation."""

    successors = (
        successor
        for state in belief.states
        for successor in advance_ordered_input_state(state)
    )
    return merge_observation_equivalent_states(successors)


def enumerate_ordered_input_histories(
    state: OrderedInputExactState,
    *,
    publication_steps: int,
) -> tuple[OrderedInputHistory, ...]:
    """Enumerate exact active-mask histories for a bounded publication lease."""

    if publication_steps < 0:
        raise ValueError("publication step count must be nonnegative")
    histories = (OrderedInputHistory((), state),)
    for _ in range(publication_steps):
        histories = tuple(
            OrderedInputHistory(
                active_masks_after_publication=(
                    history.active_masks_after_publication + (successor.active_mask,)
                ),
                successor_state=successor,
            )
            for history in histories
            for successor in advance_ordered_input_state(history.successor_state)
        )
        histories = tuple(sorted(set(histories)))
    return histories


__all__ = [
    "OrderedInputBelief",
    "OrderedInputExactState",
    "OrderedInputHistory",
    "OrderedInputIssueBranch",
    "OrderedInputObservation",
    "advance_ordered_input_belief",
    "advance_ordered_input_state",
    "belief_after_issue",
    "enumerate_ordered_input_histories",
    "issue_ordered_input_belief",
    "merge_observation_equivalent_states",
    "ordered_mask_path",
]
