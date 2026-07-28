"""Static opcode-0x87 auxiliary-VM source availability reporting."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from th08_ecl_tool.core import EclFile

from .advance import (
    AUXILIARY_START_OPCODE,
    find_auxiliary_start_advances,
)
from .join import event_record, join_activation_support
from .mapping import FIRE_OPCODES
from .model import StaticInstruction, TraceScan


@dataclass(frozen=True, slots=True)
class AuxiliaryAnalysis:
    section: dict[str, object]
    start_pc_observed: bool
    exact_start_observed: bool
    every_immediate_candidate_matched: bool


def auxiliary_static_semantics() -> dict[str, object]:
    """Return the revalidated auxiliary-context layout used by reports."""

    return {
        "opcode": "0x87",
        "handler": "0x0041CDF3..0x0041CF81",
        "enemy_pointer_slots": "enemy+0x3384, four pointers",
        "allocated_context_bytes": 0x24B0,
        "vm_offset_in_context": 0x08,
        "active_vm_bytes": 0x228,
        "live_local_offsets_in_vm": "0x18..0x64",
        "call_depth_offset_in_context": 0x06,
        "call_depth_semantics": "signed_i16_saturates_at_15",
        "saved_call_frame_area_offset_in_context": 0x230,
        "saved_call_frame_stride": 0x228,
        "maximum_restorable_saved_call_frames": 15,
        "physical_saved_call_frame_slots": 16,
        "saturated_slot_15_semantics": (
            "written_by_calls_at_depth_15_but_next_return_restores_slot_14"
        ),
        "scheduler": "0x0041EBB6..0x0041EC7C",
    }


def _unsigned_to_signed(value: int) -> int:
    return value - (1 << 32) if value & 0x80000000 else value


def static_auxiliary_target(
    instruction: StaticInstruction,
    *,
    subroutine_count: int,
) -> int | None:
    if (
        instruction.opcode != AUXILIARY_START_OPCODE
        or len(instruction.arguments) != 2
        or instruction.parameter_mask & 0x03
    ):
        return None
    target = _unsigned_to_signed(instruction.arguments[1])
    return target if 0 <= target < subroutine_count else None


def build_auxiliary_analysis(
    *,
    trace: TraceScan,
    ecl: EclFile,
    runtime_instructions: dict[int, StaticInstruction],
    pc_occurrences: Counter[int],
    max_samples: int,
) -> AuxiliaryAnalysis:
    pc_counts = {
        pc: pc_occurrences[pc]
        for pc, instruction in runtime_instructions.items()
        if (
            instruction.opcode == AUXILIARY_START_OPCODE
            and pc in pc_occurrences
        )
    }
    targets = {
        pc: static_auxiliary_target(
            runtime_instructions[pc],
            subroutine_count=len(ecl.subroutines),
        )
        for pc in pc_counts
    }
    advances, diagnostics = find_auxiliary_start_advances(
        trace.captures,
        instructions_by_pc=runtime_instructions,
    )
    immediate_advances = [
        event
        for event in advances
        if (
            targets.get(event.source_pc) is not None
            and any(
                instruction.time == 0
                and instruction.opcode in FIRE_OPCODES
                for instruction in ecl.subroutines[
                    targets[event.source_pc]
                ].instructions
            )
        )
    ]
    support_join = join_activation_support(
        immediate_advances,
        trace.activation_batches,
    )
    target_advance_counts: Counter[int] = Counter(
        target
        for event in advances
        if (target := targets.get(event.source_pc)) is not None
    )
    every_matched = (
        bool(immediate_advances)
        and len(support_join.matched_event_indices) == len(immediate_advances)
    )
    section: dict[str, object] = {
        "static_ida_semantics": auxiliary_static_semantics(),
        "interpretation": (
            "Static opcode 0x87 argument 1 selects a subroutine for a "
            "heap auxiliary VM. A contained time-zero fire instruction "
            "is availability evidence, not an interpreted reachable-path "
            "or runtime-byte proof."
        ),
        "observed_start_pcs": [
            {
                "runtime_pc": pc,
                "runtime_pc_hex": f"{pc:#010x}",
                "file_offset": runtime_instructions[pc].offset,
                "file_offset_hex": f"{runtime_instructions[pc].offset:#x}",
                "main_subroutine_index": (
                    runtime_instructions[pc].subroutine_index
                ),
                "instruction_time": runtime_instructions[pc].time,
                "parameter_mask": runtime_instructions[pc].parameter_mask,
                "static_arguments": list(
                    runtime_instructions[pc].arguments
                ),
                "static_target_subroutine": targets[pc],
                "target_fire_instructions": (
                    [
                        {
                            "file_offset": instruction.offset,
                            "time": instruction.time,
                            "opcode": instruction.opcode,
                            "parameter_mask": instruction.parameter_mask,
                        }
                        for instruction in ecl.subroutines[
                            targets[pc]
                        ].instructions
                        if instruction.opcode in FIRE_OPCODES
                    ]
                    if targets[pc] is not None
                    else []
                ),
                "observation_occurrences": count,
            }
            for pc, count in sorted(pc_counts.items())
        ],
        "exact_sequential_start_advances": len(advances),
        "start_advances_by_static_target": {
            str(target): count
            for target, count in sorted(target_advance_counts.items())
        },
        "immediate_fire_candidate_advances": len(immediate_advances),
        "immediate_candidates_with_compatible_activation": len(
            support_join.matched_event_indices
        ),
        "compatible_activation_batches": len(
            support_join.matched_batch_indices
        ),
        "compatible_activation_bullets": (
            support_join.matched_activation_bullets
        ),
        "all_immediate_candidates_have_compatible_activation": every_matched,
        "advance_diagnostics": diagnostics,
        "event_samples": [
            {
                **event_record(
                    immediate_advances[index],
                    matching_batches=support_join.event_matches[index],
                ),
                "static_target_subroutine": targets[
                    immediate_advances[index].source_pc
                ],
            }
            for index in support_join.matched_event_indices[:max_samples]
        ],
    }
    return AuxiliaryAnalysis(
        section=section,
        start_pc_observed=bool(pc_counts),
        exact_start_observed=bool(advances),
        every_immediate_candidate_matched=every_matched,
    )


__all__ = [
    "AuxiliaryAnalysis",
    "build_auxiliary_analysis",
    "static_auxiliary_target",
]
