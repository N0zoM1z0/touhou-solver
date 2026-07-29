"""Fixed columnar transport for replay-capable auxiliary-VM evidence."""

from __future__ import annotations

from collections import Counter
import hashlib
from typing import Any

from .model import (
    AUXILIARY_VM_BATCH_LAYOUT_V1,
    AUXILIARY_VM_BATCH_LAYOUT_V2,
    SAVED_FRAME_BYTES,
    AuxiliaryVmBatchObservation,
)
from .replay_bundle import encode_replay_bundle


USABLE_RECORD_PROJECTION_SCHEMA = (
    "th08-auxiliary-vm-usable-record-projection-v2"
)
USABLE_RECORD_COLUMNS = (
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
)
REQUEST_PROJECTION_SCHEMA = "th08-auxiliary-ecl-request-projection-v1"
REQUEST_COLUMNS = (
    "source_record_index",
    "status",
    "result_index",
)
REQUEST_SOURCE_INDEX = 0
REQUEST_STATUS_INDEX = 1
REQUEST_RESULT_INDEX = 2


def empty_request_projection() -> dict[str, object]:
    return {
        "schema": REQUEST_PROJECTION_SCHEMA,
        "columns": list(REQUEST_COLUMNS),
        "rows": [],
    }


def request_projection(
    rows: list[list[object]],
) -> dict[str, object]:
    return {
        "schema": REQUEST_PROJECTION_SCHEMA,
        "columns": list(REQUEST_COLUMNS),
        "rows": rows,
    }


def compact_usable_observation(
    observation: AuxiliaryVmBatchObservation,
) -> dict[str, object]:
    """Encode one selected observation without repeated per-record keys."""

    rows: list[list[object]] = []
    referenced_blobs: list[tuple[str, bytes]] = []
    seen_blobs: set[str] = set()
    for source_record_index, source in enumerate(observation.records):
        if not source.usable:
            continue
        active_sha256 = hashlib.sha256(source.active_vm).hexdigest()
        saved_sha256 = [
            hashlib.sha256(frame).hexdigest()
            for frame in source.saved_frames
        ]
        rows.append(
            [
                source_record_index,
                source.slot,
                source.auxiliary_index,
                source.enemy_pointer,
                source.context_pointer,
                source.context_pointer_after,
                source.enemy_flags_before,
                source.enemy_flags_after,
                int(source.status),
                source.target_subroutine,
                source.call_depth,
                source.auxiliary_marker,
                active_sha256,
                saved_sha256,
            ]
        )
        for digest, blob in (
            [(active_sha256, source.active_vm)]
            + list(zip(saved_sha256, source.saved_frames))
        ):
            if digest in seen_blobs:
                continue
            seen_blobs.add(digest)
            referenced_blobs.append((digest, blob))

    statuses = Counter(int(item.status) for item in observation.records)
    record: dict[str, Any] = {
        "layout": observation.layout,
        "authority": "trace_only_no_action_authority",
        "batch_status_bits": int(observation.batch_status),
        "success": observation.success,
        "active_owner_count": observation.active_owner_count,
        "record_count": len(observation.records),
        "non_null_context_count": observation.non_null_context_count,
        "usable_context_count": observation.usable_context_count,
        "process_read_count": observation.process_read_count,
        "state_payload_bytes": observation.state_payload_bytes,
        "record_projection": {
            "schema": USABLE_RECORD_PROJECTION_SCHEMA,
            "record_status_bits": {
                str(key): value for key, value in sorted(statuses.items())
            },
            "columns": list(USABLE_RECORD_COLUMNS),
            "rows": rows,
        },
        "replay_state_bundle": encode_replay_bundle(
            referenced_blobs,
            blob_bytes=SAVED_FRAME_BYTES,
        ),
    }
    if observation.layout == AUXILIARY_VM_BATCH_LAYOUT_V1:
        record.update(
            {
                "expected_manager_frame": observation.expected_manager_frame,
                "manager_frame_before": observation.manager_frame_before,
                "manager_frame_after": observation.manager_frame_after,
            }
        )
    elif observation.layout == AUXILIARY_VM_BATCH_LAYOUT_V2:
        record.update(
            {
                "selected_manager_frame": observation.expected_manager_frame,
                "owner_manager_frame_after": (
                    observation.owner_manager_frame_after
                ),
                "context_manager_frame_before": (
                    observation.manager_frame_before
                ),
                "manager_frame_after": observation.manager_frame_after,
                "owner_blob_bytes": observation.owner_blob_bytes,
            }
        )
    else:
        raise ValueError(
            f"unknown auxiliary-VM layout {observation.layout!r}"
        )
    return record


__all__ = [
    "REQUEST_COLUMNS",
    "REQUEST_PROJECTION_SCHEMA",
    "REQUEST_RESULT_INDEX",
    "REQUEST_SOURCE_INDEX",
    "REQUEST_STATUS_INDEX",
    "USABLE_RECORD_COLUMNS",
    "USABLE_RECORD_PROJECTION_SCHEMA",
    "compact_usable_observation",
    "empty_request_projection",
    "request_projection",
]
