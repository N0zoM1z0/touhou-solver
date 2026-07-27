"""Capture one TH08 main ECL VM without coupling it to lookahead success."""

from __future__ import annotations

import struct
import time
from dataclasses import dataclass
from typing import Any, Callable

from th08_ecl_runtime import (
    EclInstructionCache,
    EclLookaheadResult,
    EclVmSnapshot,
    TaggedVelocityToggle,
    analyze_tagged_velocity_toggles,
    read_main_ecl_vm_snapshot,
)


ENEMY_MANAGER_FRAME_ADDRESS = 0x0164D30C
_CAPTURE_ERRORS = (OSError, RuntimeError, ValueError, struct.error)


@dataclass(frozen=True)
class MainEclCapture:
    """Capture result whose VM snapshot survives classifier rejection."""

    snapshot: EclVmSnapshot | None
    lookahead: EclLookaheadResult | None
    tagged_velocity_toggles: tuple[TaggedVelocityToggle, ...]
    error: str | None
    frame_before: int
    frame_after: int
    elapsed_ms: float


def capture_main_ecl(
    reader: Any,
    *,
    enemy_pointer: int,
    instruction_cache: EclInstructionCache,
    horizon_frames: int,
    active_difficulty_mask: int,
    clock: Callable[[], float] = time.perf_counter,
    snapshot_reader: Callable[
        [Any, int],
        EclVmSnapshot,
    ] = read_main_ecl_vm_snapshot,
    lookahead_analyzer: Callable[..., EclLookaheadResult] = (
        analyze_tagged_velocity_toggles
    ),
) -> MainEclCapture:
    """Read the VM once; classify callbacks without erasing that observation."""

    started = clock()
    frame_before = int(reader.u32(ENEMY_MANAGER_FRAME_ADDRESS))
    snapshot: EclVmSnapshot | None = None
    lookahead: EclLookaheadResult | None = None
    tagged_velocity_toggles: tuple[TaggedVelocityToggle, ...] = ()
    error: str | None = None
    try:
        snapshot = snapshot_reader(reader, enemy_pointer)
    except _CAPTURE_ERRORS as caught:
        error = f"{type(caught).__name__}: {caught}"
    if snapshot is not None:
        try:
            lookahead = lookahead_analyzer(
                snapshot,
                instruction_at=lambda address: instruction_cache.instruction(
                    reader.read,
                    address,
                ),
                horizon_frames=horizon_frames,
                active_difficulty_mask=active_difficulty_mask,
            )
            tagged_velocity_toggles = lookahead.events
        except _CAPTURE_ERRORS as caught:
            error = f"{type(caught).__name__}: {caught}"
    frame_after = int(reader.u32(ENEMY_MANAGER_FRAME_ADDRESS))
    elapsed_ms = (clock() - started) * 1000.0
    return MainEclCapture(
        snapshot=snapshot,
        lookahead=lookahead,
        tagged_velocity_toggles=tagged_velocity_toggles,
        error=error,
        frame_before=frame_before,
        frame_after=frame_after,
        elapsed_ms=elapsed_ms,
    )


__all__ = [
    "ENEMY_MANAGER_FRAME_ADDRESS",
    "MainEclCapture",
    "capture_main_ecl",
]
