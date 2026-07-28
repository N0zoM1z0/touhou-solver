"""Default-off post-issue delivery for auxiliary-VM batch telemetry."""

from __future__ import annotations

import time
from typing import Any

from th08_live.enemy_sensor import (
    ENEMY_ACTIVE_FLAG,
    ENEMY_FLAGS_OFFSET,
    ENEMY_LOCAL_PREFIX_SIZE,
    ENEMY_POOL_BASE,
    ENEMY_STRIDE,
)
from th08_live.enemy_ecl_inventory import (
    ENEMY_AUXILIARY_ECL_CONTEXT_POINTERS_OFFSET,
)
from th08_runtime_agent import ADDR_ENEMY_MANAGER_FRAME

from .native import (
    NATIVE_CALL_MODE_GIL_HELD,
    NativeAuxiliaryVmBatchCapture,
)


AUXILIARY_VM_BATCH_TRACE_SCHEMA_VERSION = 2
AUXILIARY_VM_BATCH_TRACE_ROLE = "trace_only_no_action_authority"


class AuxiliaryVmBatchTraceService:
    """Schedule bounded post-issue observations by changed manager frame."""

    def __init__(
        self,
        *,
        cadence_frames: int = 16,
        spell_id_filter: int | None = None,
        native_call_mode: str = NATIVE_CALL_MODE_GIL_HELD,
        capture: Any | None = None,
    ) -> None:
        if cadence_frames <= 0:
            raise ValueError("auxiliary-VM batch cadence must be positive")
        if spell_id_filter is not None and spell_id_filter < 0:
            raise ValueError("auxiliary-VM spell filter cannot be negative")
        self.cadence_frames = cadence_frames
        self.spell_id_filter = spell_id_filter
        self.capture = (
            NativeAuxiliaryVmBatchCapture(call_mode=native_call_mode)
            if capture is None
            else capture
        )
        self.native_call_mode = native_call_mode
        self._context: tuple[int, int, int | None] | None = None
        self._last_attempt_frame: int | None = None

    def reset(self) -> None:
        self._context = None
        self._last_attempt_frame = None

    def _due(
        self,
        *,
        manager_frame: int,
        gameplay_epoch: int,
        stage_route_index: int,
        spell_id: int | None,
    ) -> bool:
        if (
            self.spell_id_filter is not None
            and spell_id != self.spell_id_filter
        ):
            return False
        context = (gameplay_epoch, stage_route_index, spell_id)
        if context != self._context:
            self._context = context
            self._last_attempt_frame = None
        last = self._last_attempt_frame
        if (
            last is not None
            and manager_frame >= last
            and manager_frame - last < self.cadence_frames
        ):
            return False
        self._last_attempt_frame = manager_frame
        return True

    def observe_if_due(
        self,
        reader: Any,
        *,
        decision_frame: int,
        manager_frame: int,
        gameplay_epoch: int,
        stage_route_index: int,
        spell_id: int | None,
    ) -> dict[str, object] | None:
        if not self._due(
            manager_frame=manager_frame,
            gameplay_epoch=gameplay_epoch,
            stage_route_index=stage_route_index,
            spell_id=spell_id,
        ):
            return None

        total_started = time.perf_counter()
        observation_started = total_started
        try:
            observation = self.capture.capture_process(
                reader,
                pool_base=ENEMY_POOL_BASE,
                manager_frame_address=ADDR_ENEMY_MANAGER_FRAME,
                record_count=ENEMY_LOCAL_PREFIX_SIZE,
                enemy_stride=ENEMY_STRIDE,
                enemy_flags_offset=ENEMY_FLAGS_OFFSET,
                enemy_active_flag=ENEMY_ACTIVE_FLAG,
                context_pointer_offset=(
                    ENEMY_AUXILIARY_ECL_CONTEXT_POINTERS_OFFSET
                ),
            )
        except (OSError, RuntimeError, TypeError, ValueError) as error:
            return self._error_record(
                decision_frame=decision_frame,
                manager_frame=manager_frame,
                gameplay_epoch=gameplay_epoch,
                stage_route_index=stage_route_index,
                spell_id=spell_id,
                error=f"{type(error).__name__}: {error}",
                status="native_transaction_failed",
                total_started=total_started,
            )
        observation_ms = (
            time.perf_counter() - observation_started
        ) * 1000.0
        compact_started = time.perf_counter()
        compact = observation.compact_record()
        compact_ms = (time.perf_counter() - compact_started) * 1000.0
        diagnostics = self.capture.diagnostics()
        total_ms = (time.perf_counter() - total_started) * 1000.0
        return {
            "kind": "auxiliary_vm_batch",
            "schema_version": AUXILIARY_VM_BATCH_TRACE_SCHEMA_VERSION,
            "authority": AUXILIARY_VM_BATCH_TRACE_ROLE,
            "frame": decision_frame,
            "snapshot_frame": manager_frame,
            "gameplay_epoch": gameplay_epoch,
            "stage_route_index": stage_route_index,
            "spell_id": spell_id,
            "cadence_frames": self.cadence_frames,
            "spell_id_filter": self.spell_id_filter,
            "native_call_mode": self.native_call_mode,
            "status": "success" if observation.success else "rejected",
            "error": None,
            "selected_manager_frame": observation.expected_manager_frame,
            "owner_manager_frame_after": (
                observation.owner_manager_frame_after
            ),
            "context_manager_frame_before": (
                observation.manager_frame_before
            ),
            "manager_frame_after": observation.manager_frame_after,
            "process_read_count": observation.process_read_count,
            "observation": compact,
            "timing_ms": {
                "native_call": diagnostics.native_call_ms,
                "materialize": diagnostics.materialize_ms,
                "observation": observation_ms,
                "compact": compact_ms,
                "total": total_ms,
            },
        }

    def _error_record(
        self,
        *,
        decision_frame: int,
        manager_frame: int,
        gameplay_epoch: int,
        stage_route_index: int,
        spell_id: int | None,
        error: str,
        status: str,
        total_started: float,
    ) -> dict[str, object]:
        return {
            "kind": "auxiliary_vm_batch",
            "schema_version": AUXILIARY_VM_BATCH_TRACE_SCHEMA_VERSION,
            "authority": AUXILIARY_VM_BATCH_TRACE_ROLE,
            "frame": decision_frame,
            "snapshot_frame": manager_frame,
            "gameplay_epoch": gameplay_epoch,
            "stage_route_index": stage_route_index,
            "spell_id": spell_id,
            "cadence_frames": self.cadence_frames,
            "spell_id_filter": self.spell_id_filter,
            "native_call_mode": self.native_call_mode,
            "status": status,
            "error": error,
            "selected_manager_frame": None,
            "owner_manager_frame_after": None,
            "context_manager_frame_before": None,
            "manager_frame_after": None,
            "process_read_count": None,
            "observation": None,
            "timing_ms": {
                "native_call": 0.0,
                "materialize": 0.0,
                "observation": 0.0,
                "compact": 0.0,
                "total": (
                    time.perf_counter() - total_started
                )
                * 1000.0,
            },
        }


__all__ = [
    "AUXILIARY_VM_BATCH_TRACE_ROLE",
    "AUXILIARY_VM_BATCH_TRACE_SCHEMA_VERSION",
    "AuxiliaryVmBatchTraceService",
]
