"""Mutable working registers for the offline TH08 ECL local shadow."""

from __future__ import annotations

import math

from th08_ecl_vm_state import (
    ECL_VM_FLOAT_LOCAL_COUNT,
    ECL_VM_FLOAT_LOCAL_FIRST,
    ECL_VM_INTEGER_LOCAL_COUNT,
    ECL_VM_INTEGER_LOCAL_FIRST,
    ECL_VM_SCRATCH_INTEGER_COUNT,
    ECL_VM_SCRATCH_INTEGER_FIRST,
    EclVmLocalProjection,
    float32_from_bits,
)


def signed_int32(value: int) -> int:
    value &= 0xFFFFFFFF
    return value - (1 << 32) if value & (1 << 31) else value


def float_destination_variable(bits: int) -> int | None:
    value = float32_from_bits(bits & 0xFFFFFFFF)
    if not math.isfinite(value) or not value.is_integer():
        return None
    variable = int(value)
    index = variable - ECL_VM_FLOAT_LOCAL_FIRST
    return variable if 0 <= index < ECL_VM_FLOAT_LOCAL_COUNT else None


class LocalRegisters:
    """Mutable copy that freezes back to one immutable projection."""

    def __init__(self, projection: EclVmLocalProjection) -> None:
        self.integer_locals = list(projection.integer_locals)
        self.float_local_bits = list(projection.float_local_bits)
        self.scratch_integers = list(projection.scratch_integers)

    def freeze(self) -> EclVmLocalProjection:
        return EclVmLocalProjection(
            tuple(self.integer_locals),
            tuple(self.float_local_bits),
            tuple(self.scratch_integers),
        )

    def read_integer(self, variable: int) -> int | None:
        index = variable - ECL_VM_INTEGER_LOCAL_FIRST
        if 0 <= index < ECL_VM_INTEGER_LOCAL_COUNT:
            return self.integer_locals[index]
        index = variable - ECL_VM_SCRATCH_INTEGER_FIRST
        if 0 <= index < ECL_VM_SCRATCH_INTEGER_COUNT:
            return self.scratch_integers[index]
        return None

    def write_integer(self, variable: int, value: int) -> bool:
        value = signed_int32(value)
        index = variable - ECL_VM_INTEGER_LOCAL_FIRST
        if 0 <= index < ECL_VM_INTEGER_LOCAL_COUNT:
            self.integer_locals[index] = value
            return True
        index = variable - ECL_VM_SCRATCH_INTEGER_FIRST
        if 0 <= index < ECL_VM_SCRATCH_INTEGER_COUNT:
            self.scratch_integers[index] = value
            return True
        return False

    def write_float_bits(self, variable: int, bits: int) -> bool:
        index = variable - ECL_VM_FLOAT_LOCAL_FIRST
        if not 0 <= index < ECL_VM_FLOAT_LOCAL_COUNT:
            return False
        self.float_local_bits[index] = bits & 0xFFFFFFFF
        return True


__all__ = ["LocalRegisters", "float_destination_variable", "signed_int32"]
