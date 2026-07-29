"""Frozen schema-v2/v3 event fixture producer for historical auditors."""

from __future__ import annotations

from th08_ecl_auxiliary import (
    AuxiliaryEclVmState,
    AuxiliaryLiteralFireRequest,
)
from th08_live.auxiliary_vm.event_service import (
    AuxiliaryEclEventConfiguration,
    AuxiliaryEclEventTraceService,
)
from th08_live.auxiliary_vm.model import AuxiliaryVmBatchObservation
from th08_live.runtime_ecl_identity import RuntimeEclAcceptedVersion


class LegacyAuxiliaryEclEventTraceService:
    """Emit the full legacy record while using the same exact lowerer."""

    def __init__(
        self,
        configuration: AuxiliaryEclEventConfiguration,
    ) -> None:
        self._current = AuxiliaryEclEventTraceService(configuration)

    def prepare_if_needed(
        self,
        runtime_version: RuntimeEclAcceptedVersion,
        **arguments: int,
    ) -> dict[str, object] | None:
        return self._current.prepare_if_needed(
            runtime_version,
            **arguments,
        )

    def derive(
        self,
        observation: AuxiliaryVmBatchObservation,
        *,
        runtime_version: RuntimeEclAcceptedVersion,
        gameplay_epoch: int,
        stage_route_index: int,
    ) -> dict[str, object]:
        program = self._current._program
        bound = self._current._bound_program
        lowerer = self._current._lowerer
        assert bound is not None
        assert lowerer is not None
        request_records: list[dict[str, object]] = []
        requests: list[AuxiliaryLiteralFireRequest] = []
        pending_indices: list[int] = []
        unknown_count = 0
        for record_index, record in enumerate(observation.records):
            if not record.usable:
                continue
            request: dict[str, object] = {
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
                request["status"] = f"invalid_state:{error}"
                request_records.append(request)
                unknown_count += 1
                continue
            request["state"] = {
                "instruction_pointer": state.instruction_pointer,
                "timer_previous": state.timer_previous,
                "timer_fraction_bits": state.timer_fraction_bits,
                "timer_elapsed": state.timer_elapsed,
                "auxiliary_marker": state.auxiliary_marker,
            }
            target = record.target_subroutine
            if record.call_depth != 0:
                status = "unsupported_call_depth"
            elif target not in program.target_horizons:
                status = "unsupported_target"
            elif state.auxiliary_marker != record.auxiliary_marker:
                status = "auxiliary_marker_mismatch"
            elif bound.instruction_owner.get(state.instruction_pointer) != target:
                status = "target_pc_mismatch"
            else:
                status = "pending"
            request["status"] = status
            request_records.append(request)
            if status != "pending":
                unknown_count += 1
                continue
            pending_indices.append(len(request_records) - 1)
            requests.append(
                AuxiliaryLiteralFireRequest(
                    state=state,
                    timer_tick_horizon=program.target_horizons[target],
                )
            )
        cached = lowerer.lower(requests)
        complete_count = 0
        for request_index, record_index in enumerate(pending_indices):
            result = cached.batch.results[request_index]
            request = request_records[record_index]
            request["result_index"] = cached.batch.result_indices[
                request_index
            ]
            if result.horizon_covered:
                request["status"] = "complete"
                complete_count += 1
            else:
                request["status"] = (
                    f"lowering_unknown:{result.stop_reason}"
                )
                unknown_count += 1
        if not request_records:
            status = "empty_complete"
        elif unknown_count == 0:
            status = "success"
        elif complete_count:
            status = "partial_unknown"
        else:
            status = "unknown"
        return {
            "schema": "th08-auxiliary-ecl-event-derivation-v3",
            "authority": "trace_only_no_action_authority",
            "status": status,
            "runtime_version": runtime_version.record(),
            "accepted_gameplay_epoch": runtime_version.gameplay_epoch,
            "observation_gameplay_epoch": gameplay_epoch,
            "observation_epoch_semantics": (
                "provenance_not_program_mutation"
            ),
            "program_identity": program.program_identity_record(
                runtime_version
            ),
            "program_identity_key": program.program_identity_key(
                runtime_version
            ),
            "active_difficulty_mask": 0x08,
            "target_horizons": {
                str(target): horizon
                for target, horizon in sorted(
                    program.target_horizons.items()
                )
            },
            "request_count": len(request_records),
            "complete_count": complete_count,
            "unknown_count": unknown_count,
            "requests": request_records,
            "lowering": cached.batch.compact_record(),
            "cache": cached.cache.record(),
            "timing_ms": {
                "state_decode": 0.0,
                "lower": 0.0,
                "compact": 0.0,
                "total": 0.0,
            },
        }


__all__ = ["LegacyAuxiliaryEclEventTraceService"]
