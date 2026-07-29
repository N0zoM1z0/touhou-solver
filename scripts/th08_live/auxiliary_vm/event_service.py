"""Default-off replay-capable auxiliary literal-fire derivation."""

from __future__ import annotations

import time
from collections.abc import Callable

from th08_ecl_auxiliary import (
    AuxiliaryEclVmState,
    AuxiliaryLiteralFireBatchLowerer,
    AuxiliaryLiteralFireRequest,
)
from th08_live.runtime_ecl_identity import RuntimeEclAcceptedVersion

from .event_program import (
    DEFAULT_TARGET_HORIZONS,
    AuxiliaryEclEventConfiguration,
    AuxiliaryEclEventProgram,
    BoundAuxiliaryEclProgram,
)
from .model import AuxiliaryVmBatchObservation


AUXILIARY_ECL_EVENT_SCHEMA = "th08-auxiliary-ecl-event-derivation-v2"
AUXILIARY_ECL_EVENT_PREPARATION_SCHEMA = (
    "th08-auxiliary-ecl-event-preparation-v1"
)
AUXILIARY_ECL_EVENT_AUTHORITY = "trace_only_no_action_authority"


class AuxiliaryEclEventTraceService:
    """Lower one exact Stage-5 auxiliary event class after coherent capture."""

    def __init__(
        self,
        configuration: AuxiliaryEclEventConfiguration,
        *,
        clock: Callable[[], float] = time.perf_counter,
    ) -> None:
        self._program = AuxiliaryEclEventProgram(configuration)
        self._clock = clock
        self._bound_program: BoundAuxiliaryEclProgram | None = None
        self._lowerer: AuxiliaryLiteralFireBatchLowerer | None = None
        self._prepared_version_key: tuple[object, ...] | None = None
        self._preparation_attempt: tuple[object, ...] | None = None

    def unavailable_record(
        self,
        reason: str,
        *,
        runtime_version: RuntimeEclAcceptedVersion | None = None,
        total_ms: float = 0.0,
    ) -> dict[str, object]:
        return {
            "schema": AUXILIARY_ECL_EVENT_SCHEMA,
            "authority": AUXILIARY_ECL_EVENT_AUTHORITY,
            "status": reason,
            "runtime_version": (
                runtime_version.record()
                if runtime_version is not None
                else None
            ),
            "request_count": 0,
            "complete_count": 0,
            "unknown_count": 0,
            "requests": [],
            "lowering": None,
            "cache": None,
            "timing_ms": {
                "program_bind": 0.0,
                "state_decode": 0.0,
                "lower": 0.0,
                "compact": 0.0,
                "total": total_ms,
            },
        }

    def prepare_if_needed(
        self,
        runtime_version: RuntimeEclAcceptedVersion | None,
        *,
        gameplay_epoch: int,
        stage_route_index: int,
        decision_frame: int,
        snapshot_frame: int,
    ) -> dict[str, object] | None:
        """Bind one accepted version once and expose the cold preparation."""

        if runtime_version is None:
            return None
        version_key = self._program.version_key(runtime_version)
        attempt = (
            *version_key,
            gameplay_epoch,
            stage_route_index,
        )
        if (
            self._prepared_version_key == version_key
            or self._preparation_attempt == attempt
        ):
            return None
        self._preparation_attempt = attempt
        total_started = self._clock()
        status = "success"
        error: str | None = None
        bind_ms = 0.0
        if not self._program.version_matches(
            runtime_version,
            gameplay_epoch=gameplay_epoch,
            stage_route_index=stage_route_index,
        ):
            status = "runtime_identity_mismatch"
        else:
            bind_started = self._clock()
            try:
                bound = self._program.bind(runtime_version)
            except ValueError as exc:
                status = "runtime_program_bind_failed"
                error = f"{type(exc).__name__}: {exc}"
            else:
                bind_ms = (self._clock() - bind_started) * 1000.0
                configuration = self._program.configuration
                self._bound_program = bound
                self._lowerer = AuxiliaryLiteralFireBatchLowerer(
                    instruction_at=bound.instruction_index.__getitem__,
                    active_difficulty_mask=(
                        1 << configuration.expected_difficulty_index
                    ),
                    time_scale=None,
                    max_instructions=configuration.maximum_instructions,
                    max_physical_steps=(
                        configuration.maximum_physical_steps
                    ),
                    cache_capacity=configuration.cache_capacity,
                )
                self._prepared_version_key = version_key
        total_ms = (self._clock() - total_started) * 1000.0
        configuration = self._program.configuration
        return {
            "kind": "auxiliary_ecl_event_preparation",
            "schema": AUXILIARY_ECL_EVENT_PREPARATION_SCHEMA,
            "authority": AUXILIARY_ECL_EVENT_AUTHORITY,
            "status": status,
            "error": error,
            "runtime_version": runtime_version.record(),
            "gameplay_epoch": gameplay_epoch,
            "stage_route_index": stage_route_index,
            "decision_frame": decision_frame,
            "snapshot_frame": snapshot_frame,
            "configuration": {
                "active_difficulty_mask": (
                    1 << configuration.expected_difficulty_index
                ),
                "maximum_instructions": (
                    configuration.maximum_instructions
                ),
                "maximum_physical_steps": (
                    configuration.maximum_physical_steps
                ),
                "cache_capacity": configuration.cache_capacity,
                "target_horizons": {
                    str(target): horizon
                    for target, horizon in sorted(
                        self._program.target_horizons.items()
                    )
                },
            },
            "timing_ms": {
                "program_bind": bind_ms,
                "total": total_ms,
            },
        }

    def derive(
        self,
        observation: AuxiliaryVmBatchObservation | None,
        *,
        runtime_version: RuntimeEclAcceptedVersion | None,
        gameplay_epoch: int,
        stage_route_index: int,
    ) -> dict[str, object]:
        total_started = self._clock()
        if observation is None or not observation.success:
            return self.unavailable_record(
                "auxiliary_batch_unavailable",
                runtime_version=runtime_version,
                total_ms=(self._clock() - total_started) * 1000.0,
            )
        if runtime_version is None:
            return self.unavailable_record(
                "runtime_identity_unavailable",
                total_ms=(self._clock() - total_started) * 1000.0,
            )
        if not self._program.version_matches(
            runtime_version,
            gameplay_epoch=gameplay_epoch,
            stage_route_index=stage_route_index,
        ):
            return self.unavailable_record(
                "runtime_identity_mismatch",
                runtime_version=runtime_version,
                total_ms=(self._clock() - total_started) * 1000.0,
            )

        version_key = self._program.version_key(runtime_version)
        program = self._bound_program
        lowerer = self._lowerer
        if (
            program is None
            or lowerer is None
            or self._prepared_version_key != version_key
        ):
            return self.unavailable_record(
                "runtime_program_unprepared",
                runtime_version=runtime_version,
                total_ms=(self._clock() - total_started) * 1000.0,
            )
        decode_started = self._clock()
        request_records: list[dict[str, object]] = []
        requests: list[AuxiliaryLiteralFireRequest] = []
        request_record_indices: list[int] = []
        unknown_count = 0
        for record_index, record in enumerate(observation.records):
            if not record.usable:
                continue
            request_record: dict[str, object] = {
                "observation_record_index": record_index,
                "target_subroutine": record.target_subroutine,
                "call_depth": record.call_depth,
                "auxiliary_marker": record.auxiliary_marker,
                "status": None,
                "result_index": None,
            }
            try:
                state = AuxiliaryEclVmState.from_active_vm(record.active_vm)
            except ValueError as error:
                request_record["status"] = f"invalid_state:{error}"
                unknown_count += 1
                request_records.append(request_record)
                continue
            request_record["state"] = {
                "instruction_pointer": state.instruction_pointer,
                "timer_previous": state.timer_previous,
                "timer_fraction_bits": state.timer_fraction_bits,
                "timer_elapsed": state.timer_elapsed,
                "auxiliary_marker": state.auxiliary_marker,
            }
            target = record.target_subroutine
            if record.call_depth != 0:
                status = "unsupported_call_depth"
            elif target not in self._program.target_horizons:
                status = "unsupported_target"
            elif state.auxiliary_marker != record.auxiliary_marker:
                status = "auxiliary_marker_mismatch"
            elif (
                program.instruction_owner.get(state.instruction_pointer)
                != target
            ):
                status = "target_pc_mismatch"
            else:
                status = "pending"
            request_record["status"] = status
            request_records.append(request_record)
            if status != "pending":
                unknown_count += 1
                continue
            request_record_indices.append(len(request_records) - 1)
            requests.append(
                AuxiliaryLiteralFireRequest(
                    state=state,
                    timer_tick_horizon=self._program.target_horizons[target],
                )
            )
        state_decode_ms = (self._clock() - decode_started) * 1000.0

        lower_started = self._clock()
        cached_batch = lowerer.lower(requests)
        batch = cached_batch.batch
        lower_ms = (self._clock() - lower_started) * 1000.0
        complete_count = 0
        for request_index, request_record_index in enumerate(
            request_record_indices
        ):
            result = batch.results[request_index]
            result_index = batch.result_indices[request_index]
            request_record = request_records[request_record_index]
            request_record["result_index"] = result_index
            if result.horizon_covered:
                request_record["status"] = "complete"
                complete_count += 1
            else:
                request_record["status"] = (
                    f"lowering_unknown:{result.stop_reason}"
                )
                unknown_count += 1

        compact_started = self._clock()
        compact = batch.compact_record()
        compact_ms = (self._clock() - compact_started) * 1000.0
        if not request_records:
            status = "empty_complete"
        elif unknown_count == 0:
            status = "success"
        elif complete_count:
            status = "partial_unknown"
        else:
            status = "unknown"
        total_ms = (self._clock() - total_started) * 1000.0
        return {
            "schema": AUXILIARY_ECL_EVENT_SCHEMA,
            "authority": AUXILIARY_ECL_EVENT_AUTHORITY,
            "status": status,
            "runtime_version": runtime_version.record(),
            "active_difficulty_mask": (
                1 << self._program.configuration.expected_difficulty_index
            ),
            "target_horizons": {
                str(target): horizon
                for target, horizon in sorted(
                    self._program.target_horizons.items()
                )
            },
            "request_count": len(request_records),
            "complete_count": complete_count,
            "unknown_count": unknown_count,
            "requests": request_records,
            "lowering": compact,
            "cache": cached_batch.cache.record(),
            "timing_ms": {
                "state_decode": state_decode_ms,
                "lower": lower_ms,
                "compact": compact_ms,
                "total": total_ms,
            },
        }


__all__ = [
    "AUXILIARY_ECL_EVENT_AUTHORITY",
    "AUXILIARY_ECL_EVENT_PREPARATION_SCHEMA",
    "AUXILIARY_ECL_EVENT_SCHEMA",
    "AuxiliaryEclEventConfiguration",
    "AuxiliaryEclEventTraceService",
    "DEFAULT_TARGET_HORIZONS",
]
