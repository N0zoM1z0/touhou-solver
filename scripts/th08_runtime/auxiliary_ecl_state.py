"""Minimal auxiliary-ECL state used by native snapshot projection."""

from __future__ import annotations

import math
import struct
from dataclasses import dataclass

from th08_ecl_vm_state import EclVmLocalProjection, float32_from_bits


CONTEXT_TARGET_OFFSET = 0x00
CONTEXT_CALL_DEPTH_OFFSET = 0x06
CONTEXT_ACTIVE_VM_OFFSET = 0x08
ACTIVE_VM_BYTES = 0x228
ACTIVE_VM_AUXILIARY_MARKER_OFFSET = 0x220
MAXIMUM_RESTORABLE_FRAMES = 15
MINIMUM_RUNTIME_ADDRESS = 0x00010000
MAXIMUM_RUNTIME_ADDRESS = 0x7FFFFFFF


@dataclass(frozen=True)
class AuxiliaryEclTimerState:
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
            raise ValueError(
                "auxiliary active VM has an invalid instruction pointer"
            )
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


__all__ = [
    "ACTIVE_VM_AUXILIARY_MARKER_OFFSET",
    "ACTIVE_VM_BYTES",
    "AuxiliaryEclTimerState",
    "AuxiliaryEclVmState",
    "CONTEXT_ACTIVE_VM_OFFSET",
    "CONTEXT_CALL_DEPTH_OFFSET",
    "CONTEXT_TARGET_OFFSET",
    "MAXIMUM_RESTORABLE_FRAMES",
]
