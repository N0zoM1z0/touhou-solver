"""Immutable records used by the derived-pattern source join."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SourceCandidate:
    row_index: int
    frame: int
    gameplay_epoch: int
    stage_route_index: int
    capture_end: int
    slot: int
    x: float | None
    y: float | None
    predicted_child_count: int


@dataclass(frozen=True, slots=True)
class ActivationMember:
    slot: int
    age: int
    origin_x: float
    origin_y: float


@dataclass(frozen=True, slots=True)
class ActivationGroup:
    frame: int
    gameplay_epoch: int
    stage_route_index: int
    support_start: int
    support_end: int
    age: int
    origin_x: float
    origin_y: float
    members: tuple[ActivationMember, ...]


__all__ = [
    "ActivationGroup",
    "ActivationMember",
    "SourceCandidate",
]
