"""Bounded exact-environment cache for auxiliary intent batches."""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Callable, Iterable
from dataclasses import dataclass

from th08_ecl_runtime import RuntimeEclInstruction

from .batch import AuxiliaryLiteralFireBatch, AuxiliaryLiteralFireRequest
from .lowerer import lower_auxiliary_literal_fire_cycle
from .model import AuxiliaryLiteralFireResult


IntentEquivalenceKey = tuple[int, int, int, int, int]


@dataclass(frozen=True, slots=True)
class AuxiliaryLiteralFireCacheStats:
    request_count: int
    request_local_hits: int
    persistent_hits: int
    misses: int
    evictions: int
    entries_after: int
    capacity: int

    def record(self) -> dict[str, int]:
        return {
            "request_count": self.request_count,
            "request_local_hits": self.request_local_hits,
            "persistent_hits": self.persistent_hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "entries_after": self.entries_after,
            "capacity": self.capacity,
        }


@dataclass(frozen=True, slots=True)
class CachedAuxiliaryLiteralFireBatch:
    batch: AuxiliaryLiteralFireBatch
    cache: AuxiliaryLiteralFireCacheStats


class AuxiliaryLiteralFireBatchLowerer:
    """Lower under one immutable environment with bounded exact LRU reuse."""

    def __init__(
        self,
        *,
        instruction_at: Callable[[int], RuntimeEclInstruction],
        active_difficulty_mask: int,
        time_scale: float | None = None,
        max_instructions: int = 64,
        max_physical_steps: int = 65536,
        cache_capacity: int = 512,
    ) -> None:
        if active_difficulty_mask <= 0:
            raise ValueError("active difficulty mask must be positive")
        if max_instructions <= 0:
            raise ValueError("instruction limit must be positive")
        if max_physical_steps <= 0:
            raise ValueError("physical-step limit must be positive")
        if cache_capacity <= 0:
            raise ValueError("cache capacity must be positive")
        self._instruction_at = instruction_at
        self._active_difficulty_mask = active_difficulty_mask
        self._time_scale = time_scale
        self._max_instructions = max_instructions
        self._max_physical_steps = max_physical_steps
        self._capacity = cache_capacity
        self._cache: OrderedDict[
            IntentEquivalenceKey,
            AuxiliaryLiteralFireResult,
        ] = OrderedDict()

    @property
    def cache_capacity(self) -> int:
        return self._capacity

    @property
    def cache_entries(self) -> int:
        return len(self._cache)

    def clear(self) -> None:
        self._cache.clear()

    def lower(
        self,
        requests: Iterable[AuxiliaryLiteralFireRequest],
    ) -> CachedAuxiliaryLiteralFireBatch:
        request_rows = tuple(requests)
        current_indices: dict[IntentEquivalenceKey, int] = {}
        unique_results: list[AuxiliaryLiteralFireResult] = []
        results: list[AuxiliaryLiteralFireResult] = []
        result_indices: list[int] = []
        request_local_hits = 0
        persistent_hits = 0
        misses = 0
        evictions = 0

        for request in request_rows:
            key = request.intent_equivalence_key()
            current_index = current_indices.get(key)
            if current_index is not None:
                request_local_hits += 1
                result = unique_results[current_index]
            else:
                result = self._cache.get(key)
                if result is None:
                    misses += 1
                    result = lower_auxiliary_literal_fire_cycle(
                        request.state,
                        instruction_at=self._instruction_at,
                        timer_tick_horizon=request.timer_tick_horizon,
                        active_difficulty_mask=(
                            self._active_difficulty_mask
                        ),
                        time_scale=self._time_scale,
                        max_instructions=self._max_instructions,
                        max_physical_steps=self._max_physical_steps,
                    )
                    self._cache[key] = result
                    if len(self._cache) > self._capacity:
                        self._cache.popitem(last=False)
                        evictions += 1
                else:
                    persistent_hits += 1
                    self._cache.move_to_end(key)
                current_index = len(unique_results)
                current_indices[key] = current_index
                unique_results.append(result)
            results.append(result)
            result_indices.append(current_index)

        batch = AuxiliaryLiteralFireBatch(
            results=tuple(results),
            unique_results=tuple(unique_results),
            result_indices=tuple(result_indices),
        )
        return CachedAuxiliaryLiteralFireBatch(
            batch=batch,
            cache=AuxiliaryLiteralFireCacheStats(
                request_count=len(request_rows),
                request_local_hits=request_local_hits,
                persistent_hits=persistent_hits,
                misses=misses,
                evictions=evictions,
                entries_after=len(self._cache),
                capacity=self._capacity,
            ),
        )


__all__ = [
    "AuxiliaryLiteralFireBatchLowerer",
    "AuxiliaryLiteralFireCacheStats",
    "CachedAuxiliaryLiteralFireBatch",
    "IntentEquivalenceKey",
]
