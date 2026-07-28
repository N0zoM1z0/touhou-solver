"""Immutable first-loss selection records."""

from __future__ import annotations

from dataclasses import dataclass

from analysis.complete_mask_capsule.types import CompleteMaskCapsuleRoot


@dataclass(frozen=True)
class FirstLossBracket:
    last_viable: CompleteMaskCapsuleRoot
    first_losing: CompleteMaskCapsuleRoot


@dataclass(frozen=True)
class FirstLossSelection:
    status: str
    bracket: FirstLossBracket | None
    interruption_counts: tuple[tuple[str, int], ...]
    root_validation_failures: tuple[str, ...]
    recovered_loss_episodes: int
    target_hit_frame: int | None
    unresolved: dict[str, object] | None = None


__all__ = [
    "FirstLossBracket",
    "FirstLossSelection",
]
