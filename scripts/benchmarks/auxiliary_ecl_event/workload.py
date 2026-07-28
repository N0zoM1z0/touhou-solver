"""Exact shipped-image workloads for auxiliary-ECL event lowering."""

from __future__ import annotations

import hashlib
import json
import struct
from dataclasses import dataclass
from pathlib import Path

from th08_ecl_auxiliary import (
    AuxiliaryEclVmState,
    build_exact_runtime_instruction_index,
)
from th08_ecl_runtime import RuntimeEclInstruction
from th08_ecl_tool.core import parse_ecl


EXPECTED_ECL_SHA256 = (
    "3148f45faf78bd8211a956edcdc353be7"
    "3d2781995d3dadd36bdca8132f8fe19"
)
RUNTIME_BASE = 0x00500000
ACTIVE_DIFFICULTY_MASK = 0x08
TARGETS = ((69, 8), (72, 8), (73, 30))
BATCH_COUNTS = ((69, 8), (72, 9), (73, 17))


@dataclass(frozen=True)
class BenchmarkContext:
    name: str
    subroutine_index: int
    timer_tick_horizon: int
    state: AuxiliaryEclVmState

    def identity_record(self) -> dict[str, object]:
        return {
            "name": self.name,
            "subroutine_index": self.subroutine_index,
            "timer_tick_horizon": self.timer_tick_horizon,
            "instruction_pointer": self.state.instruction_pointer,
            "timer_elapsed": self.state.timer_elapsed,
            "timer_fraction_bits": self.state.timer_fraction_bits,
            "auxiliary_marker": self.state.auxiliary_marker,
        }


@dataclass(frozen=True)
class BenchmarkFixture:
    ecl_path: Path
    ecl_sha256: str
    instruction_index: dict[int, RuntimeEclInstruction]
    workloads: dict[str, tuple[BenchmarkContext, ...]]
    identity_digest: str


def _active_vm(pc: int, marker: int) -> bytes:
    raw = bytearray(0x228)
    struct.pack_into("<I", raw, 0, pc)
    struct.pack_into("<i", raw, 4, -1)
    struct.pack_into("<f", raw, 8, 0.0)
    struct.pack_into("<i", raw, 12, 0)
    struct.pack_into("<I", raw, 0x220, marker)
    return bytes(raw)


def _digest(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_fixture(path: Path) -> BenchmarkFixture:
    image = path.read_bytes()
    actual_sha256 = hashlib.sha256(image).hexdigest()
    if actual_sha256 != EXPECTED_ECL_SHA256:
        raise ValueError(
            "Stage-5 ECL digest mismatch: "
            f"expected {EXPECTED_ECL_SHA256}, got {actual_sha256}"
        )
    ecl = parse_ecl(path)
    index = build_exact_runtime_instruction_index(
        ecl,
        image,
        runtime_base=RUNTIME_BASE,
        expected_sha256=EXPECTED_ECL_SHA256,
    )
    target_contexts: dict[int, BenchmarkContext] = {}
    for marker, (subroutine_index, period) in enumerate(TARGETS, start=1):
        first = ecl.subroutines[subroutine_index].instructions[0]
        target_contexts[subroutine_index] = BenchmarkContext(
            name=f"sub{subroutine_index}_one_context",
            subroutine_index=subroutine_index,
            timer_tick_horizon=period * 2,
            state=AuxiliaryEclVmState.from_active_vm(
                _active_vm(RUNTIME_BASE + first.offset, marker)
            ),
        )

    batch: list[BenchmarkContext] = []
    for subroutine_index, count in BATCH_COUNTS:
        template = target_contexts[subroutine_index]
        for ordinal in range(count):
            batch.append(
                BenchmarkContext(
                    name=f"sub{subroutine_index}_{ordinal:02d}",
                    subroutine_index=subroutine_index,
                    timer_tick_horizon=template.timer_tick_horizon,
                    state=template.state,
                )
            )
    workloads = {
        context.name: (context,)
        for context in target_contexts.values()
    }
    workloads["stage5_observed_mix_34_context"] = tuple(batch)
    identity = {
        "active_difficulty_mask": ACTIVE_DIFFICULTY_MASK,
        "ecl_sha256": actual_sha256,
        "runtime_base": RUNTIME_BASE,
        "workloads": {
            name: [context.identity_record() for context in contexts]
            for name, contexts in workloads.items()
        },
    }
    return BenchmarkFixture(
        ecl_path=path,
        ecl_sha256=actual_sha256,
        instruction_index=index,
        workloads=workloads,
        identity_digest=_digest(identity),
    )


__all__ = [
    "ACTIVE_DIFFICULTY_MASK",
    "BenchmarkContext",
    "BenchmarkFixture",
    "EXPECTED_ECL_SHA256",
    "load_fixture",
]
