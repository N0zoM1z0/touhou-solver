"""Request-local canonicalization for auxiliary intent descriptors."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass

from th08_ecl_runtime import RuntimeEclInstruction

from .lowerer import lower_auxiliary_literal_fire_cycle
from .model import AuxiliaryEclVmState, AuxiliaryLiteralFireResult


BATCH_RECORD_SCHEMA = "th08-auxiliary-literal-fire-batch-v1"


@dataclass(frozen=True)
class AuxiliaryLiteralFireRequest:
    state: AuxiliaryEclVmState
    timer_tick_horizon: int

    def intent_equivalence_key(self) -> tuple[int, int, int, int, int]:
        """Return fields that affect the current unresolved intent schedule.

        Owner identity, scheduler marker, and VM locals remain explicit
        dependencies of later resolution; this lowerer does not resolve them.
        """

        return (
            self.state.instruction_pointer,
            self.state.timer_previous,
            self.state.timer_fraction_bits,
            self.state.timer_elapsed,
            self.timer_tick_horizon,
        )


@dataclass(frozen=True)
class AuxiliaryLiteralFireBatch:
    results: tuple[AuxiliaryLiteralFireResult, ...]
    unique_results: tuple[AuxiliaryLiteralFireResult, ...]
    result_indices: tuple[int, ...]

    def __post_init__(self) -> None:
        if len(self.results) != len(self.result_indices):
            raise ValueError("batch result mapping length mismatch")
        if any(
            index < 0 or index >= len(self.unique_results)
            for index in self.result_indices
        ):
            raise ValueError("batch result mapping index is invalid")
        if any(
            result != self.unique_results[index]
            for result, index in zip(self.results, self.result_indices)
        ):
            raise ValueError("batch result mapping does not reproduce results")

    def compact_record(self) -> dict[str, object]:
        return {
            "schema": BATCH_RECORD_SCHEMA,
            "request_count": len(self.results),
            "unique_result_count": len(self.unique_results),
            "result_indices": list(self.result_indices),
            "unique_results": [
                result.record() for result in self.unique_results
            ],
        }


def lower_auxiliary_literal_fire_batch(
    requests: Iterable[AuxiliaryLiteralFireRequest],
    *,
    instruction_at: Callable[[int], RuntimeEclInstruction],
    active_difficulty_mask: int,
    time_scale: float | None = None,
    max_instructions: int = 64,
    max_physical_steps: int = 65536,
) -> AuxiliaryLiteralFireBatch:
    """Lower equivalent intent schedules once and preserve request order."""

    cache: dict[tuple[int, int, int, int, int], int] = {}
    unique_results: list[AuxiliaryLiteralFireResult] = []
    results: list[AuxiliaryLiteralFireResult] = []
    result_indices: list[int] = []
    for request in requests:
        key = request.intent_equivalence_key()
        index = cache.get(key)
        if index is None:
            result = lower_auxiliary_literal_fire_cycle(
                request.state,
                instruction_at=instruction_at,
                timer_tick_horizon=request.timer_tick_horizon,
                active_difficulty_mask=active_difficulty_mask,
                time_scale=time_scale,
                max_instructions=max_instructions,
                max_physical_steps=max_physical_steps,
            )
            index = len(unique_results)
            cache[key] = index
            unique_results.append(result)
        else:
            result = unique_results[index]
        results.append(result)
        result_indices.append(index)
    return AuxiliaryLiteralFireBatch(
        results=tuple(results),
        unique_results=tuple(unique_results),
        result_indices=tuple(result_indices),
    )


__all__ = [
    "AuxiliaryLiteralFireBatch",
    "AuxiliaryLiteralFireRequest",
    "BATCH_RECORD_SCHEMA",
    "lower_auxiliary_literal_fire_batch",
]
