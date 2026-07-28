"""Immutable records shared by the main-VM source join."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DecisionScope:
    gameplay_epoch: int
    frame: int
    stage_route_index: int
    spell_id: int | None


@dataclass(frozen=True, slots=True)
class VmRow:
    slot: int
    enemy_pointer: int
    enemy_flags: int
    instruction_pointer: int
    timer_fraction_bits: int
    timer_elapsed: int


@dataclass(frozen=True, slots=True)
class InventoryCapture:
    scope: DecisionScope
    prefix_frame_before: int
    prefix_frame_after: int
    rows: tuple[VmRow, ...]

    @property
    def stable(self) -> bool:
        return self.prefix_frame_before == self.prefix_frame_after


@dataclass(frozen=True, slots=True)
class ActivationBatch:
    scope: DecisionScope
    support_start: int | None
    support_end: int
    bullet_count: int
    ages: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class TraceScan:
    trace_sha256: str
    trace_bytes: int
    trace_lines: int
    schema11_rows: int
    captures: tuple[InventoryCapture, ...]
    activation_batches: tuple[ActivationBatch, ...]
    invalid_active_vm_rows: int


@dataclass(frozen=True, slots=True)
class StaticInstruction:
    subroutine_index: int
    offset: int
    time: int
    opcode: int
    size: int
    difficulty_mask: int
    parameter_mask: int
    arguments: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class RuntimeBaseCandidate:
    base: int
    mapped_unique_pcs: int


@dataclass(frozen=True, slots=True)
class RuntimeBaseInference:
    selected_base: int | None
    unique_observed_pcs: int
    mapped_unique_pcs: int
    runner_up_mapped_unique_pcs: int
    candidates: tuple[RuntimeBaseCandidate, ...]

    @property
    def unique_complete_match(self) -> bool:
        return (
            self.selected_base is not None
            and self.unique_observed_pcs > 0
            and self.mapped_unique_pcs == self.unique_observed_pcs
            and self.mapped_unique_pcs > self.runner_up_mapped_unique_pcs
        )


@dataclass(frozen=True, slots=True)
class InstructionAdvance:
    gameplay_epoch: int
    stage_route_index: int
    spell_id: int | None
    slot: int
    enemy_pointer: int
    source_pc: int
    successor_pc: int
    opcode: int
    instruction_time: int
    support_start: int
    support_end: int
    previous_decision_frame: int
    current_decision_frame: int
    previous_timer_elapsed: int
    current_timer_elapsed: int


__all__ = [
    "ActivationBatch",
    "DecisionScope",
    "InventoryCapture",
    "InstructionAdvance",
    "RuntimeBaseCandidate",
    "RuntimeBaseInference",
    "StaticInstruction",
    "TraceScan",
    "VmRow",
]
