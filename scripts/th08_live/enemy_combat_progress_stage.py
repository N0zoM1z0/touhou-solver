"""Post-issue, action-neutral enemy combat-progress trace stage."""

from __future__ import annotations

from dataclasses import dataclass
import math
import time
from typing import Callable

from .enemy_combat_progress import (
    EnemyCombatProgressInventory,
    build_enemy_combat_progress_record,
)
from .trace import TraceSink


@dataclass(frozen=True, slots=True)
class EnemyCombatProgressStageRequest:
    trace_sink: TraceSink
    inventory: EnemyCombatProgressInventory
    route_id: int
    difficulty_index: int
    stage_route_index: int
    gameplay_epoch: int
    decision_frame: int
    frame_before: int
    frame_after: int
    capture_attempts: int
    capture_ms: float
    previous_emit_ms: float | None


@dataclass(frozen=True, slots=True)
class EnemyCombatProgressStageDependencies:
    build_record: Callable[
        [EnemyCombatProgressInventory],
        dict[str, object],
    ] = build_enemy_combat_progress_record


@dataclass(frozen=True, slots=True)
class EnemyCombatProgressStageResult:
    record: dict[str, object]
    stage_ms: float
    emit_ms: float


def run_enemy_combat_progress_stage(
    request: EnemyCombatProgressStageRequest,
    *,
    dependencies: EnemyCombatProgressStageDependencies = (
        EnemyCombatProgressStageDependencies()
    ),
    clock: Callable[[], float] = time.perf_counter,
) -> EnemyCombatProgressStageResult:
    """Build and enqueue one capture-bound inventory after physical issue."""

    if request.inventory.scanned_slots != 64:
        raise ValueError("enemy combat-progress physical stage requires 64 slots")
    if request.capture_attempts <= 0:
        raise ValueError("enemy combat-progress capture attempts must be positive")
    if not math.isfinite(request.capture_ms) or request.capture_ms < 0.0:
        raise ValueError("enemy combat-progress capture timing must be finite")
    if (
        request.previous_emit_ms is not None
        and (
            not math.isfinite(request.previous_emit_ms)
            or request.previous_emit_ms < 0.0
        )
    ):
        raise ValueError("enemy combat-progress emit timing must be finite")
    started = clock()
    inventory_record = dependencies.build_record(request.inventory)
    record: dict[str, object] = {
        "schema": "th08-enemy-combat-progress-observation-v1",
        "kind": "enemy_combat_progress",
        "route_id": request.route_id,
        "difficulty_index": request.difficulty_index,
        "stage_route_index": request.stage_route_index,
        "gameplay_epoch": request.gameplay_epoch,
        "decision_frame": request.decision_frame,
        "frame_before": request.frame_before,
        "frame_after": request.frame_after,
        "capture_attempts": request.capture_attempts,
        "capture_ms": request.capture_ms,
        "previous_emit_ms": request.previous_emit_ms,
        "stable": request.frame_before == request.frame_after,
        "inventory": inventory_record,
    }
    stage_ms = (clock() - started) * 1000.0
    if not math.isfinite(stage_ms) or stage_ms < 0.0:
        raise ValueError("enemy combat-progress stage timing must be finite")
    record["stage_ms"] = stage_ms
    emit_ms = request.trace_sink.emit(record, measure=True)
    return EnemyCombatProgressStageResult(
        record=record,
        stage_ms=stage_ms,
        emit_ms=emit_ms,
    )


__all__ = [
    "EnemyCombatProgressStageDependencies",
    "EnemyCombatProgressStageRequest",
    "EnemyCombatProgressStageResult",
    "run_enemy_combat_progress_stage",
]
