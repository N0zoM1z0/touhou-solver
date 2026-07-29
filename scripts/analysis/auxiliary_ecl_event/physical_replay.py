"""Independent replay validation for schema-v4 live event batches."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
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
EVENT_SCHEMA_V3 = "th08-auxiliary-ecl-event-derivation-v3"
EVENT_SCHEMA_V4 = "th08-auxiliary-ecl-event-derivation-v4"
OBSERVATION_EPOCH_SEMANTICS = "provenance_not_program_mutation"
RECORD_PROJECTION_SCHEMA = (
    "th08-auxiliary-vm-usable-record-projection-v1"
)
RESULT_COMMITMENT_SCHEMA = (
    "th08-auxiliary-literal-fire-result-commitment-v1"
)


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


def audit_event_batch_v3(
    row: dict[str, Any],
    *,
    expected_runtime_version: dict[str, object],
    program: ReplayProgram,
    context: str,
) -> BatchReplaySummary:
    """Replay schema-v6 delivery with explicit program/epoch separation."""

    event = mapping(row.get("event_derivation"), f"{context}.event")
    expected_program_identity = {
        key: expected_runtime_version[key]
        for key in (
            "runtime_base",
            "image_length",
            "relocated_sha256",
            "normalized_sha256",
            "static_sha256",
            "route_id",
            "difficulty_index",
            "stage_route_index",
        )
    }
    if event.get("program_identity") != expected_program_identity:
        raise AuxiliaryEclEventReplayError(
            f"{context} program identity differs from exact acceptance"
        )
    if event.get("program_identity_key") != [
        expected_program_identity[key]
        for key in (
            "runtime_base",
            "image_length",
            "relocated_sha256",
            "normalized_sha256",
            "static_sha256",
            "route_id",
            "difficulty_index",
            "stage_route_index",
        )
    ]:
        raise AuxiliaryEclEventReplayError(
            f"{context} program identity key differs from exact acceptance"
        )
    if (
        event.get("accepted_gameplay_epoch")
        != expected_runtime_version["gameplay_epoch"]
        or event.get("observation_gameplay_epoch")
        != row.get("gameplay_epoch")
        or event.get("observation_epoch_semantics")
        != OBSERVATION_EPOCH_SEMANTICS
    ):
        raise AuxiliaryEclEventReplayError(
            f"{context} observation epoch provenance is invalid"
        )
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
        event_schema=EVENT_SCHEMA_V3,
        empty_status="empty_complete",
        replay_blobs=replay_blobs,
    )


def _status_histogram(
    value: object,
    *,
    context: str,
) -> dict[int, int]:
    raw = mapping(value, context)
    result: dict[int, int] = {}
    for raw_bits, raw_count in raw.items():
        try:
            bits = int(raw_bits)
        except (TypeError, ValueError) as error:
            raise AuxiliaryEclEventReplayError(
                f"{context} has an invalid status key"
            ) from error
        if (
            str(bits) != raw_bits
            or bits < 0
            or isinstance(raw_count, bool)
            or not isinstance(raw_count, int)
            or raw_count <= 0
        ):
            raise AuxiliaryEclEventReplayError(
                f"{context} has an invalid status count"
            )
        result[bits] = raw_count
    return result


def _core_sha256(core: dict[str, object]) -> str:
    encoded = json.dumps(
        core,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_epoch_safe_identity(
    row: dict[str, Any],
    event: dict[str, Any],
    *,
    expected_runtime_version: dict[str, object],
    context: str,
) -> None:
    identity_keys = (
        "runtime_base",
        "image_length",
        "relocated_sha256",
        "normalized_sha256",
        "static_sha256",
        "route_id",
        "difficulty_index",
        "stage_route_index",
    )
    expected_program_identity = {
        key: expected_runtime_version[key] for key in identity_keys
    }
    if event.get("program_identity") != expected_program_identity:
        raise AuxiliaryEclEventReplayError(
            f"{context} program identity differs from exact acceptance"
        )
    if event.get("program_identity_key") != [
        expected_program_identity[key] for key in identity_keys
    ]:
        raise AuxiliaryEclEventReplayError(
            f"{context} program identity key differs from exact acceptance"
        )
    if (
        event.get("accepted_gameplay_epoch")
        != expected_runtime_version["gameplay_epoch"]
        or event.get("observation_gameplay_epoch")
        != row.get("gameplay_epoch")
        or event.get("observation_epoch_semantics")
        != OBSERVATION_EPOCH_SEMANTICS
    ):
        raise AuxiliaryEclEventReplayError(
            f"{context} observation epoch provenance is invalid"
        )


def audit_event_batch_v4(
    row: dict[str, Any],
    *,
    expected_runtime_version: dict[str, object],
    program: ReplayProgram,
    context: str,
) -> BatchReplaySummary:
    """Replay compact schema-v7 evidence against the raw-byte oracle."""

    event = mapping(row.get("event_derivation"), f"{context}.event")
    if event.get("schema") != EVENT_SCHEMA_V4:
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
    if event.get("target_horizons") != {
        str(target): horizon
        for target, horizon in sorted(TARGET_HORIZONS.items())
    }:
        raise AuxiliaryEclEventReplayError(
            f"{context} target horizons changed"
        )
    _validate_epoch_safe_identity(
        row,
        event,
        expected_runtime_version=expected_runtime_version,
        context=context,
    )

    observation = mapping(
        row.get("observation"),
        f"{context}.observation",
    )
    projection = mapping(
        observation.get("record_projection"),
        f"{context}.observation.record_projection",
    )
    if projection.get("schema") != RECORD_PROJECTION_SCHEMA:
        raise AuxiliaryEclEventReplayError(
            f"{context} record projection schema is invalid"
        )
    statuses = _status_histogram(
        projection.get("record_status_bits"),
        context=f"{context}.observation.record_status_bits",
    )
    record_count = integer(
        observation.get("record_count"),
        f"{context}.observation.record_count",
    )
    if (
        sum(statuses.values()) != record_count
        or any(bits not in (0, 1) for bits in statuses)
    ):
        raise AuxiliaryEclEventReplayError(
            f"{context} omitted record status proof is invalid"
        )
    records = array(
        observation.get("records"),
        f"{context}.observation.records",
    )
    if len(records) != statuses.get(0, 0):
        raise AuxiliaryEclEventReplayError(
            f"{context} usable projection count differs"
        )
    if (
        observation.get("non_null_context_count") != len(records)
        or observation.get("usable_context_count") != len(records)
    ):
        raise AuxiliaryEclEventReplayError(
            f"{context} usable projection aggregate differs"
        )
    replay_blobs = decode_replay_bundle(
        observation,
        context=f"{context}.observation",
    )
    usable: list[tuple[int, dict[str, Any], bytes]] = []
    source_indices: list[int] = []
    for projection_index, raw_record in enumerate(records):
        record = mapping(
            raw_record,
            f"{context}.observation.records[{projection_index}]",
        )
        source_index = integer(
            record.get("source_record_index"),
            f"{context}.record.source_record_index",
        )
        source_indices.append(source_index)
        if integer(
            record.get("status_bits"),
            f"{context}.record.status_bits",
        ) != 0:
            raise AuxiliaryEclEventReplayError(
                f"{context} projected record is not usable"
            )
        active_vm = validate_bundled_replay_record(
            record,
            replay_blobs,
            context=(
                f"{context}.observation.records[{projection_index}]"
            ),
        )
        if active_vm is None:
            raise AuxiliaryEclEventReplayError(
                f"{context} usable record lacks replay state"
            )
        usable.append((source_index, record, active_vm))
    if (
        source_indices != sorted(source_indices)
        or len(source_indices) != len(set(source_indices))
        or any(index < 0 or index >= record_count for index in source_indices)
    ):
        raise AuxiliaryEclEventReplayError(
            f"{context} projected source indices are invalid"
        )

    request_projection = array(
        event.get("request_projection"),
        f"{context}.event.request_projection",
    )
    if len(request_projection) != len(usable):
        raise AuxiliaryEclEventReplayError(
            f"{context} request/usable-record count mismatch"
        )
    pending: list[
        tuple[dict[str, Any], bytes, int, tuple[int, int, int, int, int]]
    ] = []
    target_counts: dict[int, int] = {}
    unknown_count = 0
    for request_index, (raw_request, usable_record) in enumerate(
        zip(request_projection, usable)
    ):
        request = mapping(
            raw_request,
            f"{context}.event.request_projection[{request_index}]",
        )
        if set(request) != {
            "source_record_index",
            "status",
            "result_index",
        }:
            raise AuxiliaryEclEventReplayError(
                f"{context} request projection is not narrow"
            )
        source_index, record, active_vm = usable_record
        if request.get("source_record_index") != source_index:
            raise AuxiliaryEclEventReplayError(
                f"{context} request order is not capture order"
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
            if (
                not str(request.get("status")).startswith(
                    "invalid_state:"
                )
                or request.get("result_index") is not None
            ):
                raise AuxiliaryEclEventReplayError(
                    f"{context} invalid state classification differs"
                )
            unknown_count += 1
            continue
        classification = _classify_request(
            target=target,
            depth=depth,
            marker=marker,
            state=state,
            program=program,
        )
        if classification != "pending":
            if (
                request.get("status") != classification
                or request.get("result_index") is not None
            ):
                raise AuxiliaryEclEventReplayError(
                    f"{context} fail-closed classification differs"
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

    commitment = mapping(
        event.get("lowering_commitment"),
        f"{context}.event.lowering_commitment",
    )
    if commitment.get("schema") != RESULT_COMMITMENT_SCHEMA:
        raise AuxiliaryEclEventReplayError(
            f"{context} result commitment schema is invalid"
        )
    indices = array(
        commitment.get("result_indices"),
        f"{context}.commitment.result_indices",
    )
    hashes = array(
        commitment.get("unique_result_sha256"),
        f"{context}.commitment.unique_result_sha256",
    )
    canonical: dict[tuple[int, int, int, int, int], int] = {}
    expected_indices = [
        canonical.setdefault(item[3], len(canonical)) for item in pending
    ]
    if (
        commitment.get("request_count") != len(pending)
        or commitment.get("unique_result_count") != len(canonical)
        or indices != expected_indices
        or len(hashes) != len(canonical)
    ):
        raise AuxiliaryEclEventReplayError(
            f"{context} canonical result commitment mapping differs"
        )
    expected_hashes = [""] * len(canonical)
    complete_count = 0
    lowering_unknown = 0
    for pending_index, (request, active_vm, horizon, key) in enumerate(
        pending
    ):
        result_index = canonical[key]
        if request.get("result_index") != result_index:
            raise AuxiliaryEclEventReplayError(
                f"{context} request result index mismatch"
            )
        oracle = oracle_core(active_vm, program, horizon=horizon)
        digest = _core_sha256(oracle)
        current = expected_hashes[result_index]
        if current and current != digest:
            raise AuxiliaryEclEventReplayError(
                f"{context} equivalent requests differ in the oracle"
            )
        expected_hashes[result_index] = digest
        if oracle["horizon_covered"]:
            expected_status = "complete"
            complete_count += 1
        else:
            expected_status = f"lowering_unknown:{oracle['stop_reason']}"
            lowering_unknown += 1
        if request.get("status") != expected_status:
            raise AuxiliaryEclEventReplayError(
                f"{context} request completion status differs"
            )
    if hashes != expected_hashes:
        raise AuxiliaryEclEventReplayError(
            f"{context} result commitment differs from byte oracle"
        )
    unknown_count += lowering_unknown
    for key, expected in (
        ("request_count", len(request_projection)),
        ("complete_count", complete_count),
        ("unknown_count", unknown_count),
    ):
        if event.get(key) != expected:
            raise AuxiliaryEclEventReplayError(
                f"{context} event {key} mismatch"
            )
    expected_status = (
        "empty_complete"
        if not request_projection
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
        request_count=len(request_projection),
        lowerable_count=len(pending),
        complete_count=complete_count,
        unknown_count=unknown_count,
        replayable_record_count=len(records),
        target_counts=tuple(sorted(target_counts.items())),
        intent_keys=tuple(item[3] for item in pending),
    )


__all__ = [
    "ACCEPTED_VERSION_SCHEMA",
    "ACTIVE_VM_BYTES",
    "AuxiliaryEclEventReplayError",
    "BatchReplaySummary",
    "EVENT_SCHEMA_V2",
    "EVENT_SCHEMA_V3",
    "EVENT_SCHEMA_V4",
    "EVENT_AUTHORITY",
    "EVENT_SCHEMA",
    "ReplayProgram",
    "TARGET_HORIZONS",
    "audit_event_batch",
    "audit_event_batch_v2",
    "audit_event_batch_v3",
    "audit_event_batch_v4",
]
