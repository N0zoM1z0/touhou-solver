"""Immutable records for auxiliary-context pointer dynamics."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ObservedPointerRun:
    slot: int
    auxiliary_index: int
    pointer: int
    first_frame: int
    last_frame: int
    observation_count: int
    left_censored: bool
    right_censored: bool

    @property
    def observed_frame_span(self) -> int:
        return self.last_frame - self.first_frame


@dataclass(frozen=True, slots=True)
class PointerDynamics:
    comparable_capture_pairs: int
    capture_frame_gaps: tuple[int, ...]
    owner_transitions: dict[str, int]
    pointer_transitions: dict[str, int]
    observed_runs: tuple[ObservedPointerRun, ...]
    pointer_tokens: dict[int, frozenset[tuple[int, int]]]


__all__ = [
    "ObservedPointerRun",
    "PointerDynamics",
]
