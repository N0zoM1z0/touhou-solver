"""Default-off post-issue delivery for auxiliary-VM batch telemetry."""

from __future__ import annotations

from collections import Counter
import time
from typing import Any, Protocol

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
from th08_live.runtime_ecl_identity import RuntimeEclAcceptedVersion
from th08_runtime_agent import ADDR_ENEMY_MANAGER_FRAME

from .native import (
    NATIVE_CALL_MODE_GIL_HELD,
    NativeAuxiliaryVmBatchCapture,
)
from .model import (
    AuxiliaryVmBatchObservation,
    BatchStatus,
    RecordStatus,
)


AUXILIARY_VM_BATCH_TRACE_SCHEMA_VERSION = 3
AUXILIARY_VM_BATCH_EVENT_TRACE_SCHEMA_VERSION = 4
AUXILIARY_VM_BATCH_EVENT_V2_TRACE_SCHEMA_VERSION = 5
AUXILIARY_VM_BATCH_EVENT_V3_TRACE_SCHEMA_VERSION = 6
AUXILIARY_VM_BATCH_EVENT_V4_TRACE_SCHEMA_VERSION = 7
AUXILIARY_VM_BATCH_TRACE_ROLE = "trace_only_no_action_authority"
AUXILIARY_VM_BATCH_MAXIMUM_ATTEMPTS = 3
_RETRYABLE_BATCH_BITS = (
    BatchStatus.FRAME_BEFORE_MISMATCH
    | BatchStatus.FRAME_AFTER_MISMATCH
    | BatchStatus.OWNER_CAPTURE_FRAME_MISMATCH
)
_RETRYABLE_RECORD_BITS = (
    RecordStatus.NULL
    | RecordStatus.CONTEXT_CHANGED
    | RecordStatus.OWNER_INACTIVE
    | RecordStatus.OWNER_FLAGS_CHANGED
    | RecordStatus.POINTER_CHANGED
)


class AuxiliaryEclEventDeriver(Protocol):
    def derive(
        self,
        observation: AuxiliaryVmBatchObservation | None,
        *,
        runtime_version: RuntimeEclAcceptedVersion | None,
        gameplay_epoch: int,
        stage_route_index: int,
    ) -> dict[str, object]: ...

    def unavailable_record(
        self,
        reason: str,
        *,
        runtime_version: RuntimeEclAcceptedVersion | None = None,
        total_ms: float = 0.0,
    ) -> dict[str, object]: ...


def auxiliary_vm_batch_attempt_retryable(
    observation: AuxiliaryVmBatchObservation,
) -> bool:
    """Return the fixed v3 retry decision for one completed v2 attempt."""

    batch_bits = int(observation.batch_status)
    if (
        observation.success
        or batch_bits == 0
        or batch_bits & ~int(_RETRYABLE_BATCH_BITS)
    ):
        return False
    allowed_record_bits = int(_RETRYABLE_RECORD_BITS)
    return all(
        not (int(record.status) & ~allowed_record_bits)
        for record in observation.records
    )


def _attempt_summary(
    observation: AuxiliaryVmBatchObservation,
    *,
    index: int,
    native_call_ms: float,
    materialize_ms: float,
) -> dict[str, object]:
    retryable = auxiliary_vm_batch_attempt_retryable(observation)
    record_statuses = Counter(
        int(record.status) for record in observation.records
    )
    return {
        "index": index,
        "success": observation.success,
        "retryable": retryable,
        "batch_status_bits": int(observation.batch_status),
        "selected_manager_frame": observation.expected_manager_frame,
        "owner_manager_frame_after": (
            observation.owner_manager_frame_after
        ),
        "context_manager_frame_before": observation.manager_frame_before,
        "manager_frame_after": observation.manager_frame_after,
        "process_read_count": observation.process_read_count,
        "owner_blob_bytes": observation.owner_blob_bytes,
        "active_owner_count": observation.active_owner_count,
        "record_count": len(observation.records),
        "non_null_context_count": observation.non_null_context_count,
        "usable_context_count": observation.usable_context_count,
        "state_payload_bytes": observation.state_payload_bytes,
        "record_status_bits": {
            str(key): value
            for key, value in sorted(record_statuses.items())
        },
        "timing_ms": {
            "native_call": native_call_ms,
            "materialize": materialize_ms,
        },
    }


class AuxiliaryVmBatchTraceService:
    """Schedule bounded post-issue observations by changed manager frame."""

    def __init__(
        self,
        *,
        cadence_frames: int = 16,
        spell_id_filter: int | None = None,
        native_call_mode: str = NATIVE_CALL_MODE_GIL_HELD,
        capture: Any | None = None,
        event_service: AuxiliaryEclEventDeriver | None = None,
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
        self.event_service = event_service
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
        runtime_ecl_version: RuntimeEclAcceptedVersion | None = None,
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
        attempts: list[dict[str, object]] = []
        selected: AuxiliaryVmBatchObservation | None = None
        selected_attempt_index: int | None = None
        native_call_ms = 0.0
        materialize_ms = 0.0
        status = "retry_exhausted"
        for attempt_index in range(AUXILIARY_VM_BATCH_MAXIMUM_ATTEMPTS):
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
                    attempts=attempts,
                    native_call_ms=native_call_ms,
                    materialize_ms=materialize_ms,
                )
            diagnostics = self.capture.diagnostics()
            native_call_ms += diagnostics.native_call_ms
            materialize_ms += diagnostics.materialize_ms
            attempt = _attempt_summary(
                observation,
                index=attempt_index,
                native_call_ms=diagnostics.native_call_ms,
                materialize_ms=diagnostics.materialize_ms,
            )
            attempts.append(attempt)
            if observation.success:
                selected = observation
                selected_attempt_index = attempt_index
                status = "success"
                break
            if not attempt["retryable"]:
                status = "terminal_rejected"
                break
        observation_ms = (
            time.perf_counter() - observation_started
        ) * 1000.0
        event_started = time.perf_counter()
        event_derivation = (
            self.event_service.derive(
                selected,
                runtime_version=runtime_ecl_version,
                gameplay_epoch=gameplay_epoch,
                stage_route_index=stage_route_index,
            )
            if self.event_service is not None
            else None
        )
        event_ms = (time.perf_counter() - event_started) * 1000.0
        compact_started = time.perf_counter()
        compact = (
            selected.compact_record(
                include_replay_bundle=self.event_service is not None,
                usable_projection=self.event_service is not None,
            )
            if selected is not None
            else None
        )
        compact_ms = (time.perf_counter() - compact_started) * 1000.0
        total_ms = (time.perf_counter() - total_started) * 1000.0
        record: dict[str, object] = {
            "kind": "auxiliary_vm_batch",
            "schema_version": (
                AUXILIARY_VM_BATCH_EVENT_V4_TRACE_SCHEMA_VERSION
                if self.event_service is not None
                else AUXILIARY_VM_BATCH_TRACE_SCHEMA_VERSION
            ),
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
            "error": None,
            "attempt_limit": AUXILIARY_VM_BATCH_MAXIMUM_ATTEMPTS,
            "attempt_count": len(attempts),
            "selected_attempt_index": selected_attempt_index,
            "attempts": attempts,
            "selected_manager_frame": (
                selected.expected_manager_frame
                if selected is not None
                else None
            ),
            "owner_manager_frame_after": (
                selected.owner_manager_frame_after
                if selected is not None
                else None
            ),
            "context_manager_frame_before": (
                selected.manager_frame_before
                if selected is not None
                else None
            ),
            "manager_frame_after": (
                selected.manager_frame_after
                if selected is not None
                else None
            ),
            "process_read_count": sum(
                int(attempt["process_read_count"])
                for attempt in attempts
            ),
            "observation": compact,
            "timing_ms": {
                "native_call": native_call_ms,
                "materialize": materialize_ms,
                "observation": observation_ms,
                "compact": compact_ms,
                "total": total_ms,
            },
        }
        if self.event_service is not None:
            record["event_derivation"] = event_derivation
            timing = record["timing_ms"]
            assert isinstance(timing, dict)
            timing["event_derive"] = event_ms
        return record

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
        attempts: list[dict[str, object]],
        native_call_ms: float,
        materialize_ms: float,
    ) -> dict[str, object]:
        record: dict[str, object] = {
            "kind": "auxiliary_vm_batch",
            "schema_version": (
                AUXILIARY_VM_BATCH_EVENT_V4_TRACE_SCHEMA_VERSION
                if self.event_service is not None
                else AUXILIARY_VM_BATCH_TRACE_SCHEMA_VERSION
            ),
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
            "attempt_limit": AUXILIARY_VM_BATCH_MAXIMUM_ATTEMPTS,
            "attempt_count": len(attempts),
            "selected_attempt_index": None,
            "attempts": attempts,
            "selected_manager_frame": None,
            "owner_manager_frame_after": None,
            "context_manager_frame_before": None,
            "manager_frame_after": None,
            "process_read_count": sum(
                int(attempt["process_read_count"])
                for attempt in attempts
            ),
            "observation": None,
            "timing_ms": {
                "native_call": native_call_ms,
                "materialize": materialize_ms,
                "observation": 0.0,
                "compact": 0.0,
                "total": (
                    time.perf_counter() - total_started
                )
                * 1000.0,
            },
        }
        if self.event_service is not None:
            record["event_derivation"] = (
                self.event_service.unavailable_record(status)
            )
            timing = record["timing_ms"]
            assert isinstance(timing, dict)
            timing["event_derive"] = 0.0
        return record


__all__ = [
    "AUXILIARY_VM_BATCH_EVENT_TRACE_SCHEMA_VERSION",
    "AUXILIARY_VM_BATCH_EVENT_V2_TRACE_SCHEMA_VERSION",
    "AUXILIARY_VM_BATCH_EVENT_V3_TRACE_SCHEMA_VERSION",
    "AUXILIARY_VM_BATCH_EVENT_V4_TRACE_SCHEMA_VERSION",
    "AUXILIARY_VM_BATCH_MAXIMUM_ATTEMPTS",
    "AUXILIARY_VM_BATCH_TRACE_ROLE",
    "AUXILIARY_VM_BATCH_TRACE_SCHEMA_VERSION",
    "AuxiliaryEclEventDeriver",
    "AuxiliaryVmBatchTraceService",
    "auxiliary_vm_batch_attempt_retryable",
]
