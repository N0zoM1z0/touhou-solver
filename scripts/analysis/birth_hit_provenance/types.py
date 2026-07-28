"""Immutable records for the birth-to-hit provenance audit."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ActivationEvidence:
    trace_line: int
    frame: int
    snapshot_frame: int | None
    gameplay_epoch: int | None
    stage_route_index: int | None
    slot: int
    code: int
    status_code: int
    state: int
    age: int
    previous_state: int
    previous_age: int
    support_start: int | None
    support_end: int
    geometry: tuple[float, float, float, float, float, float]
    transform_flags: int
    intent_available: bool
    spell_enemy_pointer: int | None
    intent_scope: str | None
    omitted_sources: tuple[str, ...]
    wave_evidence_count: int


@dataclass(frozen=True)
class TraceScan:
    activations: dict[int, tuple[ActivationEvidence, ...]]
    hit_gameplay_epochs: dict[int, int]
    trace_bytes: int
    trace_sha256: str
    row_count: int
    birth_row_count: int
    invalid_timer_evidence_count: int


__all__ = ["ActivationEvidence", "TraceScan"]
