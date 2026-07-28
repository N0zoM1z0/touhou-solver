"""Observation-support joins shared by direct and auxiliary source reports."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass

from .model import ActivationBatch, InstructionAdvance


@dataclass(frozen=True, slots=True)
class ActivationSupportJoin:
    event_matches: tuple[tuple[int, ...], ...]
    batch_matches: tuple[tuple[int, ...], ...]
    matched_event_indices: tuple[int, ...]
    matched_batch_indices: tuple[int, ...]
    one_to_one_event_indices: tuple[int, ...]
    matched_activation_bullets: int


def supports_overlap(
    event: InstructionAdvance,
    batch: ActivationBatch,
) -> bool:
    return (
        batch.support_start is not None
        and event.gameplay_epoch == batch.scope.gameplay_epoch
        and event.stage_route_index == batch.scope.stage_route_index
        and event.spell_id == batch.scope.spell_id
        and max(event.support_start, batch.support_start)
        <= min(event.support_end, batch.support_end)
    )


def join_activation_support(
    events: Sequence[InstructionAdvance],
    batches: Sequence[ActivationBatch],
) -> ActivationSupportJoin:
    event_matches: list[list[int]] = [[] for _event in events]
    batch_matches: list[list[int]] = [[] for _batch in batches]
    for event_index, event in enumerate(events):
        for batch_index, batch in enumerate(batches):
            if supports_overlap(event, batch):
                event_matches[event_index].append(batch_index)
                batch_matches[batch_index].append(event_index)

    matched_events = tuple(
        index for index, matches in enumerate(event_matches) if matches
    )
    matched_batches = tuple(
        index for index, matches in enumerate(batch_matches) if matches
    )
    one_to_one = tuple(
        event_index
        for event_index, matches in enumerate(event_matches)
        if len(matches) == 1
        and len(batch_matches[matches[0]]) == 1
    )
    return ActivationSupportJoin(
        event_matches=tuple(tuple(matches) for matches in event_matches),
        batch_matches=tuple(tuple(matches) for matches in batch_matches),
        matched_event_indices=matched_events,
        matched_batch_indices=matched_batches,
        one_to_one_event_indices=one_to_one,
        matched_activation_bullets=sum(
            batches[index].bullet_count for index in matched_batches
        ),
    )


def event_record(
    event: InstructionAdvance,
    *,
    matching_batches: Sequence[int],
) -> dict[str, object]:
    return {
        "gameplay_epoch": event.gameplay_epoch,
        "stage_route_index": event.stage_route_index,
        "spell_id": event.spell_id,
        "slot": event.slot,
        "enemy_pointer": event.enemy_pointer,
        "source_pc": event.source_pc,
        "successor_pc": event.successor_pc,
        "opcode": event.opcode,
        "instruction_time": event.instruction_time,
        "execution_support": [event.support_start, event.support_end],
        "decision_support": [
            event.previous_decision_frame,
            event.current_decision_frame,
        ],
        "timer_elapsed": [
            event.previous_timer_elapsed,
            event.current_timer_elapsed,
        ],
        "matching_activation_batch_indices": list(matching_batches),
    }


def activation_batch_record(
    batch: ActivationBatch,
    *,
    matching_events: Sequence[int],
) -> dict[str, object]:
    return {
        "gameplay_epoch": batch.scope.gameplay_epoch,
        "decision_frame": batch.scope.frame,
        "stage_route_index": batch.scope.stage_route_index,
        "spell_id": batch.scope.spell_id,
        "activation_support": [batch.support_start, batch.support_end],
        "bullet_count": batch.bullet_count,
        "ages": {
            str(key): value
            for key, value in sorted(
                Counter(batch.ages).items(),
                key=lambda item: str(item[0]),
            )
        },
        "matching_fire_advance_indices": list(matching_events),
    }


__all__ = [
    "ActivationSupportJoin",
    "activation_batch_record",
    "event_record",
    "join_activation_support",
    "supports_overlap",
]
