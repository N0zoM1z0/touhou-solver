"""Immutable state and result records for auxiliary-ECL event lowering."""

from __future__ import annotations

import math
import struct
from dataclasses import dataclass

from th08_ecl_birth import DirectFireArguments
from th08_ecl_vm_state import (
    EclVmLocalProjection,
    float32_from_bits,
)
from th08_live.auxiliary_vm.model import (
    ACTIVE_VM_AUXILIARY_MARKER_OFFSET,
    ACTIVE_VM_BYTES,
    MAXIMUM_RUNTIME_ADDRESS,
    MINIMUM_RUNTIME_ADDRESS,
)

from .constants import STOP_HORIZON, STOP_TERMINATE


@dataclass(frozen=True)
class AuxiliaryEclTimerState:
    """Exact capture fields consumed by the bounded timer recurrence."""

    instruction_pointer: int
    timer_previous: int
    timer_fraction_bits: int
    timer_elapsed: int
    auxiliary_marker: int

    @classmethod
    def from_active_vm(cls, active_vm: bytes) -> AuxiliaryEclTimerState:
        if len(active_vm) != ACTIVE_VM_BYTES:
            raise ValueError(
                "auxiliary active VM must contain exactly "
                f"{ACTIVE_VM_BYTES:#x} bytes"
            )
        (
            instruction_pointer,
            timer_previous,
            timer_fraction_bits,
            timer_elapsed,
        ) = struct.unpack_from("<IiIi", active_vm, 0)
        timer_fraction = float32_from_bits(timer_fraction_bits)
        auxiliary_marker = struct.unpack_from(
            "<I",
            active_vm,
            ACTIVE_VM_AUXILIARY_MARKER_OFFSET,
        )[0]
        if not (
            MINIMUM_RUNTIME_ADDRESS
            <= instruction_pointer
            <= MAXIMUM_RUNTIME_ADDRESS
        ):
            raise ValueError("auxiliary active VM has an invalid instruction pointer")
        if not math.isfinite(timer_fraction) or not 0.0 <= timer_fraction < 1.0:
            raise ValueError("auxiliary active VM has an invalid timer fraction")
        if timer_elapsed < 0:
            raise ValueError("auxiliary active VM has a negative timer elapsed")
        if not 1 <= auxiliary_marker <= 4:
            raise ValueError("auxiliary active VM has an invalid scheduler marker")
        return cls(
            instruction_pointer=instruction_pointer,
            timer_previous=timer_previous,
            timer_fraction_bits=timer_fraction_bits,
            timer_elapsed=timer_elapsed,
            auxiliary_marker=auxiliary_marker,
        )

    @property
    def timer_fraction(self) -> float:
        return float32_from_bits(self.timer_fraction_bits)

    def record(self) -> dict[str, object]:
        return {
            "instruction_pointer": self.instruction_pointer,
            "instruction_pointer_hex": f"{self.instruction_pointer:#010x}",
            "timer_previous": self.timer_previous,
            "timer_fraction_bits": self.timer_fraction_bits,
            "timer_fraction_bits_hex": f"{self.timer_fraction_bits:#010x}",
            "timer_elapsed": self.timer_elapsed,
            "auxiliary_marker": self.auxiliary_marker,
        }


@dataclass(frozen=True)
class AuxiliaryEclVmState(AuxiliaryEclTimerState):
    """Full capture-derived state retained by general VM-state callers."""

    local_projection: EclVmLocalProjection

    @classmethod
    def from_active_vm(cls, active_vm: bytes) -> AuxiliaryEclVmState:
        timer = AuxiliaryEclTimerState.from_active_vm(active_vm)
        return cls(
            instruction_pointer=timer.instruction_pointer,
            timer_previous=timer.timer_previous,
            timer_fraction_bits=timer.timer_fraction_bits,
            timer_elapsed=timer.timer_elapsed,
            auxiliary_marker=timer.auxiliary_marker,
            local_projection=EclVmLocalProjection.from_vm_bytes(active_vm),
        )

    def record(self) -> dict[str, object]:
        return {
            **super().record(),
            "local_projection": self.local_projection.trace_record(),
        }


@dataclass(frozen=True)
class LiteralTransformDefinition:
    instruction_address: int
    timer_tick_offset: int
    physical_frame_offset: int | None
    index: int
    kind: int
    wait_for_active_clear: int
    integer_0: int
    integer_1: int
    float_0_bits: int
    float_1_bits: int

    def record(self) -> dict[str, object]:
        return {
            "instruction_address": self.instruction_address,
            "instruction_address_hex": f"{self.instruction_address:#010x}",
            "timer_tick_offset": self.timer_tick_offset,
            "physical_frame_offset": self.physical_frame_offset,
            "index": self.index,
            "kind": self.kind,
            "wait_for_active_clear": self.wait_for_active_clear,
            "integer_0": self.integer_0,
            "integer_1": self.integer_1,
            "float_0_bits": self.float_0_bits,
            "float_0_bits_hex": f"{self.float_0_bits:#010x}",
            "float_1_bits": self.float_1_bits,
            "float_1_bits_hex": f"{self.float_1_bits:#010x}",
        }


@dataclass(frozen=True)
class AuxiliaryDirectFireIntent:
    timer_tick_offset: int
    physical_frame_offset: int | None
    instruction_address: int
    instruction_time: int
    opcode: int
    mode: int
    parameter_mask: int
    intent_status: str
    arguments: DirectFireArguments
    requested_bullets: int | None
    dependencies: tuple[str, ...]

    def record(self) -> dict[str, object]:
        return {
            "timer_tick_offset": self.timer_tick_offset,
            "physical_frame_offset": self.physical_frame_offset,
            "instruction_address": self.instruction_address,
            "instruction_address_hex": f"{self.instruction_address:#010x}",
            "instruction_time": self.instruction_time,
            "opcode": self.opcode,
            "opcode_hex": f"{self.opcode:#04x}",
            "mode": self.mode,
            "parameter_mask": self.parameter_mask,
            "parameter_mask_hex": f"{self.parameter_mask:#06x}",
            "intent_status": self.intent_status,
            "arguments": self.arguments.record(),
            "requested_bullets": self.requested_bullets,
            "dependencies": list(self.dependencies),
        }


@dataclass(frozen=True)
class AuxiliaryLiteralFireResult:
    intents: tuple[AuxiliaryDirectFireIntent, ...]
    transform_definitions: tuple[LiteralTransformDefinition, ...]
    instructions_scanned: int
    stop_reason: str
    horizon_covered: bool
    requested_timer_tick_horizon: int
    stop_timer_tick: int
    physical_timing_status: str

    def __post_init__(self) -> None:
        if self.requested_timer_tick_horizon < 0:
            raise ValueError("auxiliary timer-tick horizon cannot be negative")
        if not 0 <= self.stop_timer_tick <= self.requested_timer_tick_horizon:
            raise ValueError("auxiliary stop tick is outside its horizon")
        complete_stop = self.stop_reason in {STOP_HORIZON, STOP_TERMINATE}
        if self.horizon_covered != complete_stop:
            raise ValueError(
                "auxiliary coverage disagrees with its stop reason"
            )

    @property
    def coverage_status(self) -> str:
        return "complete" if self.horizon_covered else "unknown"

    @property
    def complete_intents(
        self,
    ) -> tuple[AuxiliaryDirectFireIntent, ...] | None:
        return self.intents if self.horizon_covered else None

    def record(self) -> dict[str, object]:
        return {
            "coverage_status": self.coverage_status,
            "stop_reason": self.stop_reason,
            "horizon_covered": self.horizon_covered,
            "requested_timer_tick_horizon": (
                self.requested_timer_tick_horizon
            ),
            "stop_timer_tick": self.stop_timer_tick,
            "instructions_scanned": self.instructions_scanned,
            "physical_timing_status": self.physical_timing_status,
            "intents": [intent.record() for intent in self.intents],
            "transform_definitions": [
                definition.record()
                for definition in self.transform_definitions
            ],
        }
