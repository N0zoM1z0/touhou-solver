"""Immutable records and revalidated TH08 auxiliary-VM layout constants."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntFlag
import hashlib


MAXIMUM_OWNERS = 64
AUXILIARY_POINTERS_PER_OWNER = 4
MAXIMUM_RECORDS = MAXIMUM_OWNERS * AUXILIARY_POINTERS_PER_OWNER
CONTEXT_TARGET_OFFSET = 0x00
CONTEXT_CALL_DEPTH_OFFSET = 0x06
CONTEXT_ACTIVE_VM_OFFSET = 0x08
ACTIVE_VM_BYTES = 0x228
ACTIVE_VM_AUXILIARY_MARKER_OFFSET = 0x220
SAVED_FRAME_BASE_OFFSET = 0x230
SAVED_FRAME_BYTES = 0x228
MAXIMUM_RESTORABLE_FRAMES = 15
PHYSICAL_SAVED_FRAME_SLOTS = 16
CONTEXT_BYTES = 0x24B0
CONTEXT_PREFIX_BYTES = 12
MAXIMUM_STATE_PAYLOAD_BYTES = (
    MAXIMUM_RECORDS
    * (1 + MAXIMUM_RESTORABLE_FRAMES)
    * ACTIVE_VM_BYTES
)
MINIMUM_RUNTIME_ADDRESS = 0x00010000
MAXIMUM_RUNTIME_ADDRESS = 0x7FFFFFFF
UNOBSERVED_MANAGER_FRAME = -(1 << 31)


class BatchStatus(IntFlag):
    OK = 0
    FRAME_BEFORE_MISMATCH = 1 << 0
    FRAME_AFTER_MISMATCH = 1 << 1
    OUTPUT_CAPACITY = 1 << 2
    OWNER_BLOB_INVALID = 1 << 3
    UNSUPPORTED_PLATFORM = 1 << 4
    PROCESS_READ_FAILED = 1 << 5


class RecordStatus(IntFlag):
    OK = 0
    NULL = 1 << 0
    CONTEXT_ADDRESS_INVALID = 1 << 1
    CONTEXT_PREFIX_READ_FAILED = 1 << 2
    CALL_DEPTH_INVALID = 1 << 3
    PAYLOAD_CAPACITY = 1 << 4
    PAYLOAD_READ_FAILED = 1 << 5
    CONTEXT_RECHECK_READ_FAILED = 1 << 6
    CONTEXT_CHANGED = 1 << 7
    ACTIVE_PC_INVALID = 1 << 8
    SAVED_PC_INVALID = 1 << 9
    AUXILIARY_MARKER_MISMATCH = 1 << 10
    OWNER_INACTIVE = 1 << 11
    OWNER_FLAGS_CHANGED = 1 << 12
    POINTER_CHANGED = 1 << 13
    OWNER_RECHECK_READ_FAILED = 1 << 14


@dataclass(frozen=True, slots=True)
class AuxiliaryVmBatchRecord:
    slot: int
    auxiliary_index: int
    enemy_pointer: int
    context_pointer: int
    context_pointer_after: int
    enemy_flags_before: int
    enemy_flags_after: int
    status: RecordStatus
    target_subroutine: int | None
    call_depth: int | None
    auxiliary_marker: int | None
    active_vm: bytes
    saved_frames: tuple[bytes, ...]

    @property
    def usable(self) -> bool:
        return self.status == RecordStatus.OK

    def compact_record(self) -> dict[str, object]:
        return {
            "slot": self.slot,
            "auxiliary_index": self.auxiliary_index,
            "enemy_pointer": self.enemy_pointer,
            "context_pointer": self.context_pointer,
            "context_pointer_after": self.context_pointer_after,
            "enemy_flags_before": self.enemy_flags_before,
            "enemy_flags_after": self.enemy_flags_after,
            "status_bits": int(self.status),
            "target_subroutine": self.target_subroutine,
            "call_depth": self.call_depth,
            "auxiliary_marker": self.auxiliary_marker,
            "active_vm_sha256": (
                hashlib.sha256(self.active_vm).hexdigest()
                if self.active_vm
                else None
            ),
            "saved_frame_sha256": [
                hashlib.sha256(frame).hexdigest()
                for frame in self.saved_frames
            ],
        }


@dataclass(frozen=True, slots=True)
class AuxiliaryVmBatchObservation:
    expected_manager_frame: int
    manager_frame_before: int
    manager_frame_after: int
    batch_status: BatchStatus
    records: tuple[AuxiliaryVmBatchRecord, ...]
    process_read_count: int
    state_payload_bytes: int

    @property
    def active_owner_count(self) -> int:
        return len({record.slot for record in self.records})

    @property
    def non_null_context_count(self) -> int:
        return sum(record.context_pointer != 0 for record in self.records)

    @property
    def usable_context_count(self) -> int:
        if not self.success:
            return 0
        return sum(record.usable for record in self.records)

    @property
    def success(self) -> bool:
        return (
            self.batch_status == BatchStatus.OK
            and all(
                record.status
                in (RecordStatus.OK, RecordStatus.NULL)
                for record in self.records
            )
        )

    def compact_record(self) -> dict[str, object]:
        return {
            "layout": "th08-auxiliary-vm-batch-v1",
            "authority": "trace_only_no_action_authority",
            "expected_manager_frame": self.expected_manager_frame,
            "manager_frame_before": self.manager_frame_before,
            "manager_frame_after": self.manager_frame_after,
            "batch_status_bits": int(self.batch_status),
            "success": self.success,
            "active_owner_count": self.active_owner_count,
            "record_count": len(self.records),
            "non_null_context_count": self.non_null_context_count,
            "usable_context_count": self.usable_context_count,
            "process_read_count": self.process_read_count,
            "state_payload_bytes": self.state_payload_bytes,
            "records": [record.compact_record() for record in self.records],
        }


__all__ = [
    "ACTIVE_VM_AUXILIARY_MARKER_OFFSET",
    "ACTIVE_VM_BYTES",
    "AUXILIARY_POINTERS_PER_OWNER",
    "AuxiliaryVmBatchObservation",
    "AuxiliaryVmBatchRecord",
    "BatchStatus",
    "CONTEXT_ACTIVE_VM_OFFSET",
    "CONTEXT_BYTES",
    "CONTEXT_CALL_DEPTH_OFFSET",
    "CONTEXT_PREFIX_BYTES",
    "CONTEXT_TARGET_OFFSET",
    "MAXIMUM_OWNERS",
    "MAXIMUM_RECORDS",
    "MAXIMUM_RESTORABLE_FRAMES",
    "MAXIMUM_RUNTIME_ADDRESS",
    "MAXIMUM_STATE_PAYLOAD_BYTES",
    "MINIMUM_RUNTIME_ADDRESS",
    "PHYSICAL_SAVED_FRAME_SLOTS",
    "RecordStatus",
    "SAVED_FRAME_BASE_OFFSET",
    "SAVED_FRAME_BYTES",
    "UNOBSERVED_MANAGER_FRAME",
]
