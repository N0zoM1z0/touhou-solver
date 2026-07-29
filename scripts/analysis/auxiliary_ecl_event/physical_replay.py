"""Independent replay validation for schema-v4 live event batches."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .replay_evidence import (
    ACCEPTED_VERSION_SCHEMA,
    ACTIVE_VM_BYTES,
    EVENT_AUTHORITY,
    EVENT_SCHEMA,
    TARGET_HORIZONS,
    AuxiliaryEclEventReplayError,
    array,
    decoded_state,
    integer,
    mapping,
    validate_replay_record,
)
from .replay_bundle_evidence import (
    decode_replay_bundle,
    validate_bundled_replay_record,
)
from .replay_oracle import ReplayProgram, oracle_core, production_core


EVENT_SCHEMA_V2 = "th08-auxiliary-ecl-event-derivation-v2"


@dataclass(frozen=True, slots=True)
class BatchReplaySummary:
    request_count: int
    lowerable_count: int
    complete_count: int
    unknown_count: int
    replayable_record_count: int
    target_counts: tuple[tuple[int, int], ...]
    intent_keys: tuple[tuple[int, int, int, int, int], ...]


def _classify_request(
    *,
    target: int,
    depth: int,
    marker: int,
    state: dict[str, int],
    program: ReplayProgram,
) -> str:
    if depth != 0:
        return "unsupported_call_depth"
    if target not in TARGET_HORIZONS:
        return "unsupported_target"
    if state["auxiliary_marker"] != marker:
        return "auxiliary_marker_mismatch"
    if (
        program.instruction_owner.get(state["instruction_pointer"])
        != target
    ):
        return "target_pc_mismatch"
    return "pending"


def _validate_requests(
    requests: list[Any],
    usable: list[tuple[int, dict[str, Any], bytes]],
    *,
    program: ReplayProgram,
    context: str,
) -> tuple[
    list[tuple[dict[str, Any], bytes, int, tuple[int, int, int, int, int]]],
    int,
    dict[int, int],
]:
    if len(requests) != len(usable):
        raise AuxiliaryEclEventReplayError(
            f"{context} request/usable-record count mismatch"
        )
    pending: list[
        tuple[dict[str, Any], bytes, int, tuple[int, int, int, int, int]]
    ] = []
    unknown_count = 0
    target_counts: dict[int, int] = {}
    for request_index, (
        (record_index, record, active_vm),
        raw_request,
    ) in enumerate(zip(usable, requests)):
        request = mapping(
            raw_request,
            f"{context}.event.requests[{request_index}]",
        )
        if request.get("observation_record_index") != record_index:
            raise AuxiliaryEclEventReplayError(
                f"{context} request order is not capture order"
            )
        for key in ("target_subroutine", "call_depth", "auxiliary_marker"):
            if request.get(key) != record.get(key):
                raise AuxiliaryEclEventReplayError(
                    f"{context} request {key} differs from capture"
                )
        target = integer(
            record.get("target_subroutine"),
            f"{context}.record.target_subroutine",
        )
        depth = integer(
            record.get("call_depth"),
            f"{context}.record.call_depth",
        )
        marker = integer(
            record.get("auxiliary_marker"),
            f"{context}.record.auxiliary_marker",
        )
        target_counts[target] = target_counts.get(target, 0) + 1
        state = decoded_state(active_vm)
        if state is None:
            if not str(request.get("status")).startswith("invalid_state:"):
                raise AuxiliaryEclEventReplayError(
                    f"{context} invalid state was not rejected"
                )
            if "state" in request:
                raise AuxiliaryEclEventReplayError(
                    f"{context} invalid state was published as decoded"
                )
            unknown_count += 1
            continue
        if request.get("state") != state:
            raise AuxiliaryEclEventReplayError(
                f"{context} decoded state differs from raw bytes"
            )
        expected_status = _classify_request(
            target=target,
            depth=depth,
            marker=marker,
            state=state,
            program=program,
        )
        if expected_status != "pending":
            if request.get("status") != expected_status:
                raise AuxiliaryEclEventReplayError(
                    f"{context} fail-closed request classification differs"
                )
            if request.get("result_index") is not None:
                raise AuxiliaryEclEventReplayError(
                    f"{context} rejected request has a result"
                )
            unknown_count += 1
            continue
        horizon = TARGET_HORIZONS[target]
        key = (
            state["instruction_pointer"],
            state["timer_previous"],
            state["timer_fraction_bits"],
            state["timer_elapsed"],
            horizon,
        )
        pending.append((request, active_vm, horizon, key))
    return pending, unknown_count, target_counts


def _validate_canonical_results(
    lowering: dict[str, Any],
    pending: list[
        tuple[dict[str, Any], bytes, int, tuple[int, int, int, int, int]]
    ],
    *,
    program: ReplayProgram,
    context: str,
) -> tuple[int, int]:
    result_indices = array(
        lowering.get("result_indices"),
        f"{context}.event.lowering.result_indices",
    )
    unique_results = array(
        lowering.get("unique_results"),
        f"{context}.event.lowering.unique_results",
    )
    if lowering.get("request_count") != len(pending):
        raise AuxiliaryEclEventReplayError(
            f"{context} lowering request count mismatch"
        )
    canonical: dict[tuple[int, int, int, int, int], int] = {}
    expected_indices: list[int] = []
    for _request, _active_vm, _horizon, key in pending:
        expected_indices.append(canonical.setdefault(key, len(canonical)))
    if result_indices != expected_indices:
        raise AuxiliaryEclEventReplayError(
            f"{context} canonical result mapping differs"
        )
    if lowering.get("unique_result_count") != len(canonical) or (
        len(unique_results) != len(canonical)
    ):
        raise AuxiliaryEclEventReplayError(
            f"{context} unique result count mismatch"
        )

    complete_count = 0
    lowering_unknown_count = 0
    for pending_index, (request, active_vm, horizon, _key) in enumerate(
        pending
    ):
        result_index = expected_indices[pending_index]
        if request.get("result_index") != result_index:
            raise AuxiliaryEclEventReplayError(
                f"{context} request result index mismatch"
            )
        result = mapping(
            unique_results[result_index],
            f"{context}.event.unique_results[{result_index}]",
        )
        oracle = oracle_core(active_vm, program, horizon=horizon)
        if production_core(result) != oracle:
            raise AuxiliaryEclEventReplayError(
                f"{context} production result differs from byte oracle"
            )
        if oracle["horizon_covered"]:
            expected_status = "complete"
            complete_count += 1
        else:
            expected_status = f"lowering_unknown:{oracle['stop_reason']}"
            lowering_unknown_count += 1
        if request.get("status") != expected_status:
            raise AuxiliaryEclEventReplayError(
                f"{context} request completion status differs"
            )
    return complete_count, lowering_unknown_count


def _audit_event_batch(
    row: dict[str, Any],
    *,
    expected_runtime_version: dict[str, object],
    program: ReplayProgram,
    context: str,
    event_schema: str,
    empty_status: str,
    replay_blobs: dict[str, bytes] | None,
) -> BatchReplaySummary:
    event = mapping(row.get("event_derivation"), f"{context}.event")
    if event.get("schema") != event_schema:
        raise AuxiliaryEclEventReplayError(
            f"{context} event schema is invalid"
        )
    if event.get("authority") != EVENT_AUTHORITY:
        raise AuxiliaryEclEventReplayError(
            f"{context} event authority is invalid"
        )
    if event.get("runtime_version") != expected_runtime_version:
        raise AuxiliaryEclEventReplayError(
            f"{context} runtime version differs from exact identity"
        )
    if event.get("active_difficulty_mask") != 0x08:
        raise AuxiliaryEclEventReplayError(
            f"{context} difficulty mask is not Lunatic"
        )
    expected_horizons = {
        str(target): horizon
        for target, horizon in sorted(TARGET_HORIZONS.items())
    }
    if event.get("target_horizons") != expected_horizons:
        raise AuxiliaryEclEventReplayError(
            f"{context} target horizons changed"
        )

    observation = mapping(
        row.get("observation"),
        f"{context}.observation",
    )
    records = array(
        observation.get("records"),
        f"{context}.observation.records",
    )
    usable: list[tuple[int, dict[str, Any], bytes]] = []
    replayable = 0
    for index, raw_record in enumerate(records):
        record = mapping(
            raw_record,
            f"{context}.observation.records[{index}]",
        )
        active_vm = (
            validate_replay_record(
                record,
                context=f"{context}.observation.records[{index}]",
            )
            if replay_blobs is None
            else validate_bundled_replay_record(
                record,
                replay_blobs,
                context=f"{context}.observation.records[{index}]",
            )
        )
        if active_vm is not None:
            replayable += 1
        status_bits = integer(
            record.get("status_bits"),
            f"{context}.observation.records[{index}].status_bits",
        )
        if status_bits == 0:
            if active_vm is None:
                raise AuxiliaryEclEventReplayError(
                    f"{context} usable record lacks replay state"
                )
            usable.append((index, record, active_vm))

    requests = array(event.get("requests"), f"{context}.event.requests")
    pending, unknown_count, target_counts = _validate_requests(
        requests,
        usable,
        program=program,
        context=context,
    )
    lowering = mapping(event.get("lowering"), f"{context}.event.lowering")
    complete_count, lowering_unknown = _validate_canonical_results(
        lowering,
        pending,
        program=program,
        context=context,
    )
    unknown_count += lowering_unknown

    expected_counts = {
        "request_count": len(requests),
        "complete_count": complete_count,
        "unknown_count": unknown_count,
    }
    for key, expected in expected_counts.items():
        if event.get(key) != expected:
            raise AuxiliaryEclEventReplayError(
                f"{context} event {key} mismatch"
            )
    expected_status = (
        empty_status
        if not requests
        else (
            "success"
            if unknown_count == 0
            else ("partial_unknown" if complete_count else "unknown")
        )
    )
    if event.get("status") != expected_status:
        raise AuxiliaryEclEventReplayError(
            f"{context} aggregate event status differs"
        )
    return BatchReplaySummary(
        request_count=len(requests),
        lowerable_count=len(pending),
        complete_count=complete_count,
        unknown_count=unknown_count,
        replayable_record_count=replayable,
        target_counts=tuple(sorted(target_counts.items())),
        intent_keys=tuple(item[3] for item in pending),
    )


def audit_event_batch(
    row: dict[str, Any],
    *,
    expected_runtime_version: dict[str, object],
    program: ReplayProgram,
    context: str,
) -> BatchReplaySummary:
    """Reproduce the immutable schema-v4 hexadecimal replay gate."""

    return _audit_event_batch(
        row,
        expected_runtime_version=expected_runtime_version,
        program=program,
        context=context,
        event_schema=EVENT_SCHEMA,
        empty_status="no_usable_contexts",
        replay_blobs=None,
    )


def audit_event_batch_v2(
    row: dict[str, Any],
    *,
    expected_runtime_version: dict[str, object],
    program: ReplayProgram,
    context: str,
) -> BatchReplaySummary:
    """Independently decode and replay one schema-v5 bundled transaction."""

    observation = mapping(
        row.get("observation"),
        f"{context}.observation",
    )
    replay_blobs = decode_replay_bundle(
        observation,
        context=f"{context}.observation",
    )
    return _audit_event_batch(
        row,
        expected_runtime_version=expected_runtime_version,
        program=program,
        context=context,
        event_schema=EVENT_SCHEMA_V2,
        empty_status="empty_complete",
        replay_blobs=replay_blobs,
    )


__all__ = [
    "ACCEPTED_VERSION_SCHEMA",
    "ACTIVE_VM_BYTES",
    "AuxiliaryEclEventReplayError",
    "BatchReplaySummary",
    "EVENT_SCHEMA_V2",
    "EVENT_AUTHORITY",
    "EVENT_SCHEMA",
    "ReplayProgram",
    "TARGET_HORIZONS",
    "audit_event_batch",
    "audit_event_batch_v2",
]
