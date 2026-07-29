"""Independent decoder and replay audit for schema-v8 columnar evidence."""

from __future__ import annotations

import re
from typing import Any

from .physical_replay import (
    EVENT_SCHEMA_V4,
    AuxiliaryEclEventReplayError,
    BatchReplaySummary,
    ReplayProgram,
    audit_event_batch_v4,
)
from .replay_evidence import array, mapping


EVENT_SCHEMA_V5 = "th08-auxiliary-ecl-event-derivation-v5"
RECORD_PROJECTION_SCHEMA_V1 = (
    "th08-auxiliary-vm-usable-record-projection-v1"
)
RECORD_PROJECTION_SCHEMA_V2 = (
    "th08-auxiliary-vm-usable-record-projection-v2"
)
RECORD_COLUMNS = [
    "source_record_index",
    "slot",
    "auxiliary_index",
    "enemy_pointer",
    "context_pointer",
    "context_pointer_after",
    "enemy_flags_before",
    "enemy_flags_after",
    "status_bits",
    "target_subroutine",
    "call_depth",
    "auxiliary_marker",
    "active_vm_sha256",
    "saved_frame_sha256",
]
REQUEST_PROJECTION_SCHEMA = "th08-auxiliary-ecl-request-projection-v1"
REQUEST_COLUMNS = [
    "source_record_index",
    "status",
    "result_index",
]
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def _strict_rows(
    projection: dict[str, Any],
    *,
    schema: str,
    columns: list[str],
    extra_keys: set[str],
    context: str,
) -> list[Any]:
    if set(projection) != {"schema", "columns", "rows"} | extra_keys:
        raise AuxiliaryEclEventReplayError(
            f"{context} projection fields are invalid"
        )
    if projection.get("schema") != schema:
        raise AuxiliaryEclEventReplayError(
            f"{context} projection schema is invalid"
        )
    if projection.get("columns") != columns:
        raise AuxiliaryEclEventReplayError(
            f"{context} projection columns are invalid"
        )
    return array(projection.get("rows"), f"{context}.rows")


def _decode_record_projection(
    observation: dict[str, Any],
    *,
    context: str,
) -> tuple[list[dict[str, Any]], object]:
    if "records" in observation:
        raise AuxiliaryEclEventReplayError(
            f"{context} legacy record dictionaries are present"
        )
    projection = mapping(
        observation.get("record_projection"),
        f"{context}.record_projection",
    )
    rows = _strict_rows(
        projection,
        schema=RECORD_PROJECTION_SCHEMA_V2,
        columns=RECORD_COLUMNS,
        extra_keys={"record_status_bits"},
        context=f"{context}.record_projection",
    )
    decoded: list[dict[str, Any]] = []
    for row_index, raw_row in enumerate(rows):
        row = array(
            raw_row,
            f"{context}.record_projection.rows[{row_index}]",
        )
        if len(row) != len(RECORD_COLUMNS):
            raise AuxiliaryEclEventReplayError(
                f"{context} record projection row arity is invalid"
            )
        if any(
            isinstance(value, bool) or not isinstance(value, int)
            for value in row[:12]
        ):
            raise AuxiliaryEclEventReplayError(
                f"{context} record projection integer field is invalid"
            )
        active_hash = row[12]
        if (
            not isinstance(active_hash, str)
            or _SHA256.fullmatch(active_hash) is None
        ):
            raise AuxiliaryEclEventReplayError(
                f"{context} record active hash is invalid"
            )
        saved_hashes = array(
            row[13],
            f"{context}.record_projection.rows[{row_index}].saved_hashes",
        )
        if any(
            not isinstance(digest, str)
            or _SHA256.fullmatch(digest) is None
            for digest in saved_hashes
        ):
            raise AuxiliaryEclEventReplayError(
                f"{context} record saved hash is invalid"
            )
        decoded.append(dict(zip(RECORD_COLUMNS, row)))
    return decoded, projection.get("record_status_bits")


def _decode_request_projection(
    event: dict[str, Any],
    *,
    context: str,
) -> list[dict[str, Any]]:
    projection = mapping(
        event.get("request_projection"),
        f"{context}.request_projection",
    )
    rows = _strict_rows(
        projection,
        schema=REQUEST_PROJECTION_SCHEMA,
        columns=REQUEST_COLUMNS,
        extra_keys=set(),
        context=f"{context}.request_projection",
    )
    decoded: list[dict[str, Any]] = []
    for row_index, raw_row in enumerate(rows):
        row = array(
            raw_row,
            f"{context}.request_projection.rows[{row_index}]",
        )
        if len(row) != len(REQUEST_COLUMNS):
            raise AuxiliaryEclEventReplayError(
                f"{context} request projection row arity is invalid"
            )
        source_index, status, result_index = row
        if (
            isinstance(source_index, bool)
            or not isinstance(source_index, int)
            or not isinstance(status, str)
            or (
                result_index is not None
                and (
                    isinstance(result_index, bool)
                    or not isinstance(result_index, int)
                    or result_index < 0
                )
            )
        ):
            raise AuxiliaryEclEventReplayError(
                f"{context} request projection value is invalid"
            )
        decoded.append(dict(zip(REQUEST_COLUMNS, row)))
    return decoded


def audit_event_batch_v5(
    row: dict[str, Any],
    *,
    expected_runtime_version: dict[str, object],
    program: ReplayProgram,
    context: str,
) -> BatchReplaySummary:
    """Strictly decode V5 columns, then reuse the independent byte oracle."""

    event = mapping(row.get("event_derivation"), f"{context}.event")
    if event.get("schema") != EVENT_SCHEMA_V5:
        raise AuxiliaryEclEventReplayError(
            f"{context} event schema is invalid"
        )
    observation = mapping(
        row.get("observation"),
        f"{context}.observation",
    )
    records, status_histogram = _decode_record_projection(
        observation,
        context=f"{context}.observation",
    )
    requests = _decode_request_projection(
        event,
        context=f"{context}.event",
    )

    legacy_observation = dict(observation)
    legacy_observation["records"] = records
    legacy_observation["record_projection"] = {
        "schema": RECORD_PROJECTION_SCHEMA_V1,
        "record_status_bits": status_histogram,
    }
    legacy_event = dict(event)
    legacy_event["schema"] = EVENT_SCHEMA_V4
    legacy_event["request_projection"] = requests
    legacy_row = dict(row)
    legacy_row["observation"] = legacy_observation
    legacy_row["event_derivation"] = legacy_event
    return audit_event_batch_v4(
        legacy_row,
        expected_runtime_version=expected_runtime_version,
        program=program,
        context=context,
    )


__all__ = [
    "EVENT_SCHEMA_V5",
    "RECORD_COLUMNS",
    "RECORD_PROJECTION_SCHEMA_V2",
    "REQUEST_COLUMNS",
    "REQUEST_PROJECTION_SCHEMA",
    "audit_event_batch_v5",
]
