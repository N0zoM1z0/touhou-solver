"""Exact captured instruction-to-successor transition detection."""

from __future__ import annotations

from collections import Counter
from collections.abc import Collection, Sequence

from .mapping import FIRE_OPCODES
from .model import (
    InstructionAdvance,
    InventoryCapture,
    StaticInstruction,
)


AUXILIARY_START_OPCODE = 0x87


def find_instruction_advances(
    captures: Sequence[InventoryCapture],
    *,
    instructions_by_pc: dict[int, StaticInstruction],
    accepted_opcodes: Collection[int],
) -> tuple[tuple[InstructionAdvance, ...], dict[str, int]]:
    """Find exact captured current-PC to sequential-successor transitions.

    Two stable consecutive inventory captures, the same slot/pointer, bounded
    monotone timer progress, one phase, and the exact sequential instruction
    address are required. An unobserved destroy/reuse cycle between captures
    remains possible, so the result is not physical identity proof.
    """

    accepted = {
        pc: instruction
        for pc, instruction in instructions_by_pc.items()
        if instruction.opcode in accepted_opcodes
    }
    advances: list[InstructionAdvance] = []
    diagnostics: Counter[str] = Counter()
    for previous, current in zip(captures, captures[1:], strict=False):
        if previous.scope.gameplay_epoch != current.scope.gameplay_epoch:
            diagnostics["epoch_discontinuity_pairs"] += 1
            continue
        previous_rows = tuple(
            row
            for row in previous.rows
            if row.instruction_pointer in accepted
        )
        diagnostics["pending_instruction_row_transitions_examined"] += len(
            previous_rows
        )
        if not previous_rows:
            continue
        if not previous.stable or not current.stable:
            diagnostics["unstable_capture"] += len(previous_rows)
            continue
        if (
            previous.scope.stage_route_index
            != current.scope.stage_route_index
            or previous.scope.spell_id != current.scope.spell_id
        ):
            diagnostics["scope_discontinuity"] += len(previous_rows)
            continue

        current_by_slot = {row.slot: row for row in current.rows}
        for source in previous_rows:
            successor = current_by_slot.get(source.slot)
            if successor is None:
                diagnostics["source_slot_absent"] += 1
                continue
            if successor.enemy_pointer != source.enemy_pointer:
                diagnostics["enemy_pointer_changed"] += 1
                continue
            instruction = accepted[source.instruction_pointer]
            expected_successor_pc = source.instruction_pointer + instruction.size
            if successor.instruction_pointer == source.instruction_pointer:
                diagnostics["still_pending"] += 1
                continue
            if successor.instruction_pointer != expected_successor_pc:
                diagnostics["nonsequential_successor"] += 1
                continue
            static_successor = instructions_by_pc.get(expected_successor_pc)
            if (
                static_successor is None
                or static_successor.offset
                != instruction.offset + instruction.size
                or static_successor.subroutine_index
                != instruction.subroutine_index
            ):
                diagnostics["static_successor_mismatch"] += 1
                continue
            timer_delta = successor.timer_elapsed - source.timer_elapsed
            maximum_timer_delta = (
                current.prefix_frame_before
                - previous.prefix_frame_after
                + 1
            )
            if timer_delta < 0:
                diagnostics["timer_regression"] += 1
                continue
            if timer_delta > maximum_timer_delta:
                diagnostics["timer_progress_exceeds_frame_support"] += 1
                continue
            support_start = previous.prefix_frame_after + 1
            support_end = current.prefix_frame_before
            if support_start > support_end:
                diagnostics["empty_execution_support"] += 1
                continue
            advances.append(
                InstructionAdvance(
                    gameplay_epoch=previous.scope.gameplay_epoch,
                    stage_route_index=previous.scope.stage_route_index,
                    spell_id=previous.scope.spell_id,
                    slot=source.slot,
                    enemy_pointer=source.enemy_pointer,
                    source_pc=source.instruction_pointer,
                    successor_pc=successor.instruction_pointer,
                    opcode=instruction.opcode,
                    instruction_time=instruction.time,
                    support_start=support_start,
                    support_end=support_end,
                    previous_decision_frame=previous.scope.frame,
                    current_decision_frame=current.scope.frame,
                    previous_timer_elapsed=source.timer_elapsed,
                    current_timer_elapsed=successor.timer_elapsed,
                )
            )
            diagnostics["accepted_exact_sequential_advance"] += 1
    return tuple(advances), dict(diagnostics)


def find_fire_advances(
    captures: Sequence[InventoryCapture],
    *,
    instructions_by_pc: dict[int, StaticInstruction],
) -> tuple[tuple[InstructionAdvance, ...], dict[str, int]]:
    return find_instruction_advances(
        captures,
        instructions_by_pc=instructions_by_pc,
        accepted_opcodes=FIRE_OPCODES,
    )


def find_auxiliary_start_advances(
    captures: Sequence[InventoryCapture],
    *,
    instructions_by_pc: dict[int, StaticInstruction],
) -> tuple[tuple[InstructionAdvance, ...], dict[str, int]]:
    return find_instruction_advances(
        captures,
        instructions_by_pc=instructions_by_pc,
        accepted_opcodes=(AUXILIARY_START_OPCODE,),
    )


__all__ = [
    "AUXILIARY_START_OPCODE",
    "find_auxiliary_start_advances",
    "find_fire_advances",
    "find_instruction_advances",
]
