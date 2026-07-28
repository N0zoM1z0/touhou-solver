"""Static ECL indexing and conservative runtime-PC affine mapping."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Sequence

from th08_ecl_tool.core import EclFile

from .model import (
    RuntimeBaseCandidate,
    RuntimeBaseInference,
    StaticInstruction,
)


FIRE_OPCODES = frozenset(range(0x60, 0x69))
MAX_REPORTED_BASE_CANDIDATES = 12


def static_instructions(ecl: EclFile) -> tuple[StaticInstruction, ...]:
    """Flatten parsed subroutines without changing file-offset identity."""

    return tuple(
        StaticInstruction(
            subroutine_index=subroutine.index,
            offset=instruction.offset,
            time=instruction.time,
            opcode=instruction.opcode,
            size=instruction.size,
            difficulty_mask=instruction.difficulty_mask,
            parameter_mask=instruction.parameter_mask,
            arguments=instruction.arguments,
        )
        for subroutine in ecl.subroutines
        for instruction in subroutine.instructions
    )


def infer_runtime_base(
    observed_pcs: Iterable[int],
    instructions: Sequence[StaticInstruction],
) -> RuntimeBaseInference:
    """Find one affine base that maps PCs to exact instruction boundaries.

    The selected base is an address-correlation result only. It does not prove
    that the static file bytes are the bytes used by the live process.
    """

    pcs = tuple(sorted(set(observed_pcs)))
    offsets = tuple(sorted({instruction.offset for instruction in instructions}))
    if not pcs or not offsets:
        return RuntimeBaseInference(
            selected_base=None,
            unique_observed_pcs=len(pcs),
            mapped_unique_pcs=0,
            runner_up_mapped_unique_pcs=0,
            candidates=(),
        )

    candidate_counts: Counter[int] = Counter(
        pc - offset
        for pc in pcs
        for offset in offsets
        if 0 <= pc - offset <= 0xFFFFFFFF
    )
    ranked = sorted(
        candidate_counts.items(),
        key=lambda item: (-item[1], item[0]),
    )
    best_count = ranked[0][1]
    best_bases = [base for base, count in ranked if count == best_count]
    selected_base = best_bases[0] if len(best_bases) == 1 else None
    runner_up = next(
        (count for _base, count in ranked if count < best_count),
        0,
    )
    return RuntimeBaseInference(
        selected_base=selected_base,
        unique_observed_pcs=len(pcs),
        mapped_unique_pcs=best_count if selected_base is not None else 0,
        runner_up_mapped_unique_pcs=runner_up,
        candidates=tuple(
            RuntimeBaseCandidate(base=base, mapped_unique_pcs=count)
            for base, count in ranked[:MAX_REPORTED_BASE_CANDIDATES]
        ),
    )


def instructions_by_runtime_pc(
    instructions: Sequence[StaticInstruction],
    *,
    runtime_base: int,
) -> dict[int, StaticInstruction]:
    return {
        runtime_base + instruction.offset: instruction
        for instruction in instructions
    }


__all__ = [
    "FIRE_OPCODES",
    "infer_runtime_base",
    "instructions_by_runtime_pc",
    "static_instructions",
]
