"""Structurally independent LRU/stat oracle for V2 event delivery."""

from __future__ import annotations

from dataclasses import dataclass


IntentKey = tuple[int, int, int, int, int]


@dataclass(frozen=True, slots=True)
class IndependentCacheStats:
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


class IndependentIntentLru:
    """Simulate LRU through explicit logical ages rather than production code."""

    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError("independent cache capacity must be positive")
        self.capacity = capacity
        self._last_used: dict[IntentKey, int] = {}
        self._logical_time = 0

    def observe(self, keys: tuple[IntentKey, ...]) -> IndependentCacheStats:
        local: set[IntentKey] = set()
        request_local_hits = 0
        persistent_hits = 0
        misses = 0
        evictions = 0
        for key in keys:
            if key in local:
                request_local_hits += 1
                continue
            local.add(key)
            self._logical_time += 1
            if key in self._last_used:
                persistent_hits += 1
            else:
                misses += 1
            self._last_used[key] = self._logical_time
            if len(self._last_used) > self.capacity:
                oldest = min(
                    self._last_used,
                    key=self._last_used.__getitem__,
                )
                del self._last_used[oldest]
                evictions += 1
        return IndependentCacheStats(
            request_count=len(keys),
            request_local_hits=request_local_hits,
            persistent_hits=persistent_hits,
            misses=misses,
            evictions=evictions,
            entries_after=len(self._last_used),
            capacity=self.capacity,
        )


__all__ = [
    "IndependentCacheStats",
    "IndependentIntentLru",
    "IntentKey",
]
