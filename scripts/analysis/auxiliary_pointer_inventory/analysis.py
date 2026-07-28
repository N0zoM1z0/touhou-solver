"""Observation-level dynamics for first-64 auxiliary ECL pointers."""

from __future__ import annotations

from collections import Counter, defaultdict

from analysis.main_vm_source_join.model import (
    AuxiliaryPointerOwner,
    InventoryCapture,
)

from .model import ObservedPointerRun, PointerDynamics


_OWNER_EVENT_NAMES = (
    "same_slot_present",
    "slot_appeared",
    "slot_disappeared",
    "enemy_flags_changed",
)
_POINTER_EVENT_NAMES = (
    "same_null",
    "same_non_null",
    "null_to_non_null",
    "non_null_to_null",
    "non_null_replaced",
)


def _owner_map(
    capture: InventoryCapture,
) -> dict[int, AuxiliaryPointerOwner]:
    return {owner.slot: owner for owner in capture.auxiliary_pointer_owners}


def _nonnull_map(capture: InventoryCapture) -> dict[tuple[int, int], int]:
    return {
        (owner.slot, auxiliary_index): pointer
        for owner in capture.auxiliary_pointer_owners
        for auxiliary_index, pointer in enumerate(owner.context_pointers)
        if pointer
    }


def _same_segment(
    previous: InventoryCapture,
    current: InventoryCapture,
) -> bool:
    return (
        previous.scope.gameplay_epoch == current.scope.gameplay_epoch
        and previous.scope.stage_route_index
        == current.scope.stage_route_index
        and previous.scope.frame < current.scope.frame
    )


def _pointer_event(previous: int, current: int) -> str:
    if previous == current:
        return "same_non_null" if previous else "same_null"
    if previous == 0:
        return "null_to_non_null"
    if current == 0:
        return "non_null_to_null"
    return "non_null_replaced"


def analyze_pointer_dynamics(
    captures: tuple[InventoryCapture, ...],
) -> PointerDynamics:
    owner_events: Counter[str] = Counter()
    pointer_events: Counter[str] = Counter()
    capture_frame_gaps: list[int] = []
    pointer_tokens: dict[int, set[tuple[int, int]]] = defaultdict(set)
    observed_runs: list[ObservedPointerRun] = []
    active_runs: dict[
        tuple[int, int],
        tuple[int, int, int, int, bool],
    ] = {}
    comparable_pairs = 0

    def finish_run(
        token: tuple[int, int],
        state: tuple[int, int, int, int, bool],
        *,
        right_censored: bool,
    ) -> None:
        pointer, first_frame, last_frame, count, left_censored = state
        observed_runs.append(
            ObservedPointerRun(
                slot=token[0],
                auxiliary_index=token[1],
                pointer=pointer,
                first_frame=first_frame,
                last_frame=last_frame,
                observation_count=count,
                left_censored=left_censored,
                right_censored=right_censored,
            )
        )

    previous: InventoryCapture | None = None
    for capture in captures:
        current_nonnull = _nonnull_map(capture)
        for token, pointer in current_nonnull.items():
            pointer_tokens[pointer].add(token)

        continuing_segment = (
            previous is not None and _same_segment(previous, capture)
        )
        if continuing_segment:
            assert previous is not None
            comparable_pairs += 1
            capture_frame_gaps.append(
                capture.scope.frame - previous.scope.frame
            )
            previous_owners = _owner_map(previous)
            current_owners = _owner_map(capture)
            for slot in previous_owners.keys() | current_owners.keys():
                previous_owner = previous_owners.get(slot)
                current_owner = current_owners.get(slot)
                if previous_owner is None:
                    owner_events["slot_appeared"] += 1
                    continue
                if current_owner is None:
                    owner_events["slot_disappeared"] += 1
                    continue
                owner_events["same_slot_present"] += 1
                if previous_owner.enemy_flags != current_owner.enemy_flags:
                    owner_events["enemy_flags_changed"] += 1
                for old_pointer, new_pointer in zip(
                    previous_owner.context_pointers,
                    current_owner.context_pointers,
                    strict=True,
                ):
                    pointer_events[
                        _pointer_event(old_pointer, new_pointer)
                    ] += 1
        else:
            for token, state in active_runs.items():
                finish_run(token, state, right_censored=True)
            active_runs.clear()

        for token, state in tuple(active_runs.items()):
            pointer, first_frame, _, count, left_censored = state
            if current_nonnull.get(token) == pointer:
                active_runs[token] = (
                    pointer,
                    first_frame,
                    capture.scope.frame,
                    count + 1,
                    left_censored,
                )
            else:
                finish_run(token, state, right_censored=False)
                del active_runs[token]
        for token, pointer in current_nonnull.items():
            if token not in active_runs:
                active_runs[token] = (
                    pointer,
                    capture.scope.frame,
                    capture.scope.frame,
                    1,
                    not continuing_segment,
                )
        previous = capture

    for token, state in active_runs.items():
        finish_run(token, state, right_censored=True)

    return PointerDynamics(
        comparable_capture_pairs=comparable_pairs,
        capture_frame_gaps=tuple(capture_frame_gaps),
        owner_transitions={
            name: owner_events[name] for name in _OWNER_EVENT_NAMES
        },
        pointer_transitions={
            name: pointer_events[name] for name in _POINTER_EVENT_NAMES
        },
        observed_runs=tuple(observed_runs),
        pointer_tokens={
            pointer: frozenset(tokens)
            for pointer, tokens in pointer_tokens.items()
        },
    )


__all__ = ["analyze_pointer_dynamics"]
