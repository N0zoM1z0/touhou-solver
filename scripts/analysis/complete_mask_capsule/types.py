"""Immutable joined trace/capsule root records."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from touhou_control.hazard_coverage import HazardCoverageAssessment
from touhou_control.pipeline_identity import PipelineQueryIdentity


@dataclass(frozen=True)
class CompleteMaskCapsuleRoot:
    trace_line: int
    decision_frame: int
    source_frame: int
    capsule: str
    identity: PipelineQueryIdentity
    coverage: HazardCoverageAssessment
    active_token: str
    held_token: str
    pending_token: str | None
    remaining_delay_support: tuple[int, ...]
    delay_frames: tuple[int, ...]
    nominal_delay: int
    trace_state_viable: bool
    issued_mask: int

    @property
    def query_frame(self) -> int:
        return self.identity.observation.query_frame

    @property
    def player_x(self) -> float:
        return _float32_from_bits(self.identity.observation.player_x_bits)

    @property
    def player_y(self) -> float:
        return _float32_from_bits(self.identity.observation.player_y_bits)


@dataclass(frozen=True)
class CompleteMaskWorkload:
    name: str
    stage: str
    trace: Path
    capsule_dir: Path
    physical_interpretation: str


def _float32_from_bits(value: str) -> float:
    import struct

    return struct.unpack("<f", int(value, 16).to_bytes(4, "little"))[0]


__all__ = ["CompleteMaskCapsuleRoot", "CompleteMaskWorkload"]
