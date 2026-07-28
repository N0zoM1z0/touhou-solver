#!/usr/bin/env python3
"""Capture-aligned TH08 main-ECL VM-local state.

The projection deliberately preserves raw float32 bits.  It is observation
data only; interpreting ECL mutations belongs to a separately verified layer.
"""

from __future__ import annotations

from dataclasses import dataclass
import struct


ECL_VM_INTEGER_LOCALS_OFFSET = 0x18
ECL_VM_INTEGER_LOCAL_FIRST = 10000
ECL_VM_INTEGER_LOCAL_COUNT = 8

ECL_VM_FLOAT_LOCALS_OFFSET = 0x38
ECL_VM_FLOAT_LOCAL_FIRST = 10016
ECL_VM_FLOAT_LOCAL_COUNT = 8

ECL_VM_SCRATCH_INTEGERS_OFFSET = 0x58
ECL_VM_SCRATCH_INTEGER_FIRST = 10036
ECL_VM_SCRATCH_INTEGER_COUNT = 4

ECL_VM_LOCAL_PROJECTION_SIZE = 0x68
ECL_VM_LOCAL_PROJECTION_LAYOUT = "th08-ecl-vm-local-projection-v1"


def float32_bits(value: float) -> int:
    """Return the IEEE-754 binary32 representation of ``value``."""

    return struct.unpack("<I", struct.pack("<f", value))[0]


def float32_from_bits(bits: int) -> float:
    """Decode one validated uint32 as an IEEE-754 binary32 value."""

    if not 0 <= bits <= 0xFFFFFFFF:
        raise ValueError("float32 bits must be a uint32")
    return struct.unpack("<f", struct.pack("<I", bits))[0]


def _validate_signed_int32(values: tuple[int, ...], *, field: str) -> None:
    if not all(-(1 << 31) <= value < (1 << 31) for value in values):
        raise ValueError(f"{field} values must be signed int32")


@dataclass(frozen=True)
class EclVmLocalProjection:
    """Immutable local-variable projection from one contiguous VM capture."""

    integer_locals: tuple[int, ...]
    float_local_bits: tuple[int, ...]
    scratch_integers: tuple[int, ...]

    def __post_init__(self) -> None:
        if len(self.integer_locals) != ECL_VM_INTEGER_LOCAL_COUNT:
            raise ValueError("integer_locals must contain eight values")
        if len(self.float_local_bits) != ECL_VM_FLOAT_LOCAL_COUNT:
            raise ValueError("float_local_bits must contain eight values")
        if len(self.scratch_integers) != ECL_VM_SCRATCH_INTEGER_COUNT:
            raise ValueError("scratch_integers must contain four values")
        _validate_signed_int32(self.integer_locals, field="integer_locals")
        _validate_signed_int32(
            self.scratch_integers,
            field="scratch_integers",
        )
        if not all(0 <= bits <= 0xFFFFFFFF for bits in self.float_local_bits):
            raise ValueError("float_local_bits values must be uint32")

    @classmethod
    def from_vm_bytes(cls, vm: bytes) -> EclVmLocalProjection:
        """Decode the projection from a full main-VM prefix."""

        if len(vm) < ECL_VM_LOCAL_PROJECTION_SIZE:
            raise ValueError(
                "ECL VM capture is shorter than the local projection layout"
            )
        return cls(
            integer_locals=struct.unpack_from(
                f"<{ECL_VM_INTEGER_LOCAL_COUNT}i",
                vm,
                ECL_VM_INTEGER_LOCALS_OFFSET,
            ),
            float_local_bits=struct.unpack_from(
                f"<{ECL_VM_FLOAT_LOCAL_COUNT}I",
                vm,
                ECL_VM_FLOAT_LOCALS_OFFSET,
            ),
            scratch_integers=struct.unpack_from(
                f"<{ECL_VM_SCRATCH_INTEGER_COUNT}i",
                vm,
                ECL_VM_SCRATCH_INTEGERS_OFFSET,
            ),
        )

    def integer_value(self, variable: int) -> int | None:
        """Resolve one projected ECL integer variable, if represented."""

        local_index = variable - ECL_VM_INTEGER_LOCAL_FIRST
        if 0 <= local_index < ECL_VM_INTEGER_LOCAL_COUNT:
            return self.integer_locals[local_index]
        scratch_index = variable - ECL_VM_SCRATCH_INTEGER_FIRST
        if 0 <= scratch_index < ECL_VM_SCRATCH_INTEGER_COUNT:
            return self.scratch_integers[scratch_index]
        return None

    def float_bits_value(self, variable: int) -> int | None:
        """Resolve raw bits for one projected ECL float variable."""

        index = variable - ECL_VM_FLOAT_LOCAL_FIRST
        if 0 <= index < ECL_VM_FLOAT_LOCAL_COUNT:
            return self.float_local_bits[index]
        return None

    def float_value(self, variable: int) -> float | None:
        """Resolve one projected ECL float variable without normalizing bits."""

        bits = self.float_bits_value(variable)
        return float32_from_bits(bits) if bits is not None else None

    def trace_record(self) -> dict[str, object]:
        """Return the compact, versioned trace representation."""

        return {
            "layout": ECL_VM_LOCAL_PROJECTION_LAYOUT,
            "capture_bytes": ECL_VM_LOCAL_PROJECTION_SIZE,
            "integer_locals": list(self.integer_locals),
            "float_local_bits": list(self.float_local_bits),
            "scratch_integers": list(self.scratch_integers),
        }


__all__ = [
    "ECL_VM_FLOAT_LOCAL_COUNT",
    "ECL_VM_FLOAT_LOCAL_FIRST",
    "ECL_VM_FLOAT_LOCALS_OFFSET",
    "ECL_VM_INTEGER_LOCAL_COUNT",
    "ECL_VM_INTEGER_LOCAL_FIRST",
    "ECL_VM_INTEGER_LOCALS_OFFSET",
    "ECL_VM_LOCAL_PROJECTION_LAYOUT",
    "ECL_VM_LOCAL_PROJECTION_SIZE",
    "ECL_VM_SCRATCH_INTEGER_COUNT",
    "ECL_VM_SCRATCH_INTEGER_FIRST",
    "ECL_VM_SCRATCH_INTEGERS_OFFSET",
    "EclVmLocalProjection",
    "float32_bits",
    "float32_from_bits",
]
