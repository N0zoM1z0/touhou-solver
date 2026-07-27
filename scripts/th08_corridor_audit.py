#!/usr/bin/env python3
"""TH08 corridor audit-capsule submission and write ownership."""

from __future__ import annotations

import time
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from th08_corridor_adapter import LoweredCorridorHazards
from touhou_control.viability_audit_capsule import (
    write_viability_audit_capsule,
)


@dataclass(frozen=True)
class CorridorAuditSubmission:
    capsule: str | None = None
    write_ms: float | None = None
    error: str | None = None
    future: Future[tuple[float, str | None]] | None = None


def _write_corridor_audit_capsule(
    *,
    capsule_path: Path,
    metadata: dict[str, object],
    hazards: LoweredCorridorHazards,
) -> tuple[float, str | None]:
    """Write one diagnostic capsule without delaying policy publication."""

    started = time.perf_counter()
    error_text = None
    try:
        write_viability_audit_capsule(
            capsule_path,
            metadata=metadata,
            aabbs=hazards.aabbs,
            piecewise_aabbs=hazards.piecewise_aabbs,
            segment_trajectories=hazards.segment_trajectories,
            packed_segments=hazards.packed_segments,
        )
    except Exception as error:
        error_text = f"{type(error).__name__}: {error}"
    return (time.perf_counter() - started) * 1000.0, error_text


def submit_corridor_audit(
    *,
    audit_capsule_dir: Path | None,
    audit_executor: ThreadPoolExecutor | None,
    source_frame: int,
    snapshot_frame: int,
    forecast_lead_frames: int,
    player_x: float,
    player_y: float,
    snapshot_lag: int,
    control_delay_candidates: tuple[int, ...],
    observed_control_delay_candidates: tuple[int, ...] | None,
    nominal_control_delay: int,
    active_action: str,
    required_gate_lane: str | None,
    context_key: tuple[int, int, int | None] | None,
    grid_step: float,
    frames_per_layer: int,
    horizon_frames: int,
    bullet_slots: tuple[int, ...],
    laser_slots: tuple[int, ...],
    enemy_pointers: tuple[int, ...],
    plan_reachable: bool,
    hazards: LoweredCorridorHazards,
) -> CorridorAuditSubmission:
    """Submit one optional diagnostic write and return separated state."""

    if audit_capsule_dir is None:
        return CorridorAuditSubmission()
    capsule_path = audit_capsule_dir / (
        f"policy_{snapshot_frame}_{source_frame}.npz"
    )
    metadata = {
        "source_frame": source_frame,
        "snapshot_frame": snapshot_frame,
        "forecast_lead_frames": forecast_lead_frames,
        "player_x": player_x,
        "player_y": player_y,
        "snapshot_lag": snapshot_lag,
        "control_delay_candidates": control_delay_candidates,
        "observed_control_delay_candidates": (
            observed_control_delay_candidates
            if observed_control_delay_candidates is not None
            else control_delay_candidates
        ),
        "nominal_control_delay": nominal_control_delay,
        "active_action": active_action,
        "required_gate_lane": required_gate_lane,
        "context_key": context_key,
        "grid_step": grid_step,
        "frames_per_layer": frames_per_layer,
        "horizon_frames": horizon_frames,
        "bullet_slots": list(bullet_slots),
        "laser_slots": list(laser_slots),
        "enemy_pointers": list(enemy_pointers),
        "plan_reachable": plan_reachable,
    }
    writer_arguments = {
        "capsule_path": capsule_path,
        "metadata": metadata,
        "hazards": hazards,
    }
    if audit_executor is None:
        write_ms, error = _write_corridor_audit_capsule(
            **writer_arguments
        )
        return CorridorAuditSubmission(
            capsule=str(capsule_path),
            write_ms=write_ms,
            error=error,
        )
    future = audit_executor.submit(
        _write_corridor_audit_capsule,
        **writer_arguments,
    )
    return CorridorAuditSubmission(
        capsule=str(capsule_path),
        future=future,
    )


__all__ = [
    "CorridorAuditSubmission",
    "submit_corridor_audit",
]
