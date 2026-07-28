"""Independent scalar fixture oracle for auxiliary-ECL VM batch capture."""

from __future__ import annotations

from dataclasses import replace
import struct

from .model import (
    ACTIVE_VM_AUXILIARY_MARKER_OFFSET,
    ACTIVE_VM_BYTES,
    AUXILIARY_POINTERS_PER_OWNER,
    AUXILIARY_VM_BATCH_LAYOUT_V2,
    AuxiliaryVmBatchObservation,
    AuxiliaryVmBatchRecord,
    BatchStatus,
    CONTEXT_CALL_DEPTH_OFFSET,
    CONTEXT_PREFIX_BYTES,
    MAXIMUM_OWNERS,
    MAXIMUM_RESTORABLE_FRAMES,
    MAXIMUM_RUNTIME_ADDRESS,
    MAXIMUM_STATE_PAYLOAD_BYTES,
    MINIMUM_RUNTIME_ADDRESS,
    RecordStatus,
    SAVED_FRAME_BYTES,
    UNOBSERVED_MANAGER_FRAME,
)


def _read_arena(
    arena: bytes,
    *,
    arena_base: int,
    address: int,
    size: int,
) -> bytes | None:
    offset = address - arena_base
    if (
        size < 0
        or offset < 0
        or offset + size < offset
        or offset + size > len(arena)
    ):
        return None
    return arena[offset : offset + size]


def _valid_pc(value: int) -> bool:
    return MINIMUM_RUNTIME_ADDRESS <= value <= MAXIMUM_RUNTIME_ADDRESS


def _valid_runtime_range(address: int, size: int) -> bool:
    return (
        MINIMUM_RUNTIME_ADDRESS <= address <= MAXIMUM_RUNTIME_ADDRESS
        and size >= 0
        and address + size >= address
        and address + size <= MAXIMUM_RUNTIME_ADDRESS + 1
    )


def _invalidate_payload(
    record: AuxiliaryVmBatchRecord,
    *,
    status: RecordStatus,
    flags_after: int | None = None,
    pointer_after: int | None = None,
) -> AuxiliaryVmBatchRecord:
    return replace(
        record,
        enemy_flags_after=(
            record.enemy_flags_after
            if flags_after is None
            else flags_after
        ),
        context_pointer_after=(
            record.context_pointer_after
            if pointer_after is None
            else pointer_after
        ),
        status=status,
        active_vm=(
            record.active_vm
            if status in (RecordStatus.OK, RecordStatus.NULL)
            else b""
        ),
        saved_frames=(
            record.saved_frames
            if status in (RecordStatus.OK, RecordStatus.NULL)
            else ()
        ),
    )


def _with_owner_recheck_failure(
    record: AuxiliaryVmBatchRecord,
) -> AuxiliaryVmBatchRecord:
    return _invalidate_payload(
        record,
        status=record.status | RecordStatus.OWNER_RECHECK_READ_FAILED,
    )


def _with_owner_after(
    record: AuxiliaryVmBatchRecord,
    *,
    flags_after: int,
    pointer_after: int,
    active_flag: int,
) -> AuxiliaryVmBatchRecord:
    status = record.status
    if not flags_after & active_flag:
        status |= RecordStatus.OWNER_INACTIVE
    if flags_after != record.enemy_flags_before:
        status |= RecordStatus.OWNER_FLAGS_CHANGED
    if pointer_after != record.context_pointer:
        status |= RecordStatus.POINTER_CHANGED
    return _invalidate_payload(
        record,
        status=status,
        flags_after=flags_after,
        pointer_after=pointer_after,
    )


def _record(
    *,
    slot: int,
    auxiliary_index: int,
    pool_base: int,
    enemy_stride: int,
    flags_before: int,
    pointer_before: int,
    arena_before: bytes,
    arena_after: bytes,
    arena_base: int,
    payload_offset: int,
    payload_capacity: int,
) -> tuple[AuxiliaryVmBatchRecord, int, int]:
    status = RecordStatus.OK
    target: int | None = None
    depth: int | None = None
    marker: int | None = None
    active_vm = b""
    saved_frames: tuple[bytes, ...] = ()
    payload_size = 0

    read_count = 0
    if pointer_before == 0:
        status |= RecordStatus.NULL
    elif not _valid_runtime_range(pointer_before, CONTEXT_PREFIX_BYTES):
        status |= RecordStatus.CONTEXT_ADDRESS_INVALID
    else:
        read_count += 1
        prefix_before = _read_arena(
            arena_before,
            arena_base=arena_base,
            address=pointer_before,
            size=CONTEXT_PREFIX_BYTES,
        )
        if prefix_before is None:
            status |= RecordStatus.CONTEXT_PREFIX_READ_FAILED
        else:
            target = struct.unpack_from("<I", prefix_before, 0)[0]
            depth = struct.unpack_from(
                "<h",
                prefix_before,
                CONTEXT_CALL_DEPTH_OFFSET,
            )[0]
            if not 0 <= depth <= MAXIMUM_RESTORABLE_FRAMES:
                status |= RecordStatus.CALL_DEPTH_INVALID
            else:
                payload_size = (1 + depth) * ACTIVE_VM_BYTES
                if not _valid_runtime_range(
                    pointer_before + 8,
                    payload_size,
                ):
                    status |= RecordStatus.CONTEXT_ADDRESS_INVALID
                elif payload_offset + payload_size > payload_capacity:
                    status |= RecordStatus.PAYLOAD_CAPACITY
                else:
                    read_count += 1
                    payload = _read_arena(
                        arena_before,
                        arena_base=arena_base,
                        address=pointer_before + 8,
                        size=payload_size,
                    )
                    if payload is None:
                        status |= RecordStatus.PAYLOAD_READ_FAILED
                    else:
                        payload_size = len(payload)
                        active_vm = payload[:ACTIVE_VM_BYTES]
                        saved_frames = tuple(
                            payload[
                                ACTIVE_VM_BYTES
                                + index * SAVED_FRAME_BYTES :
                                ACTIVE_VM_BYTES
                                + (index + 1) * SAVED_FRAME_BYTES
                            ]
                            for index in range(depth)
                        )
                        active_pc = struct.unpack_from("<I", active_vm, 0)[0]
                        if not _valid_pc(active_pc):
                            status |= RecordStatus.ACTIVE_PC_INVALID
                        if any(
                            not _valid_pc(struct.unpack_from("<I", frame, 0)[0])
                            for frame in saved_frames
                        ):
                            status |= RecordStatus.SAVED_PC_INVALID
                        marker = struct.unpack_from(
                            "<I",
                            active_vm,
                            ACTIVE_VM_AUXILIARY_MARKER_OFFSET,
                        )[0]
                        if marker != auxiliary_index + 1:
                            status |= RecordStatus.AUXILIARY_MARKER_MISMATCH
            read_count += 1
            prefix_after = _read_arena(
                arena_after,
                arena_base=arena_base,
                address=pointer_before,
                size=CONTEXT_PREFIX_BYTES,
            )
            if prefix_after is None:
                status |= RecordStatus.CONTEXT_RECHECK_READ_FAILED
            elif prefix_after != prefix_before:
                status |= RecordStatus.CONTEXT_CHANGED

    if status not in (RecordStatus.OK, RecordStatus.NULL):
        active_vm = b""
        saved_frames = ()
        payload_size = 0
    return (
        AuxiliaryVmBatchRecord(
            slot=slot,
            auxiliary_index=auxiliary_index,
            enemy_pointer=pool_base + slot * enemy_stride,
            context_pointer=pointer_before,
            context_pointer_after=pointer_before,
            enemy_flags_before=flags_before,
            enemy_flags_after=flags_before,
            status=status,
            target_subroutine=target,
            call_depth=depth,
            auxiliary_marker=marker,
            active_vm=active_vm,
            saved_frames=saved_frames,
        ),
        payload_size,
        read_count,
    )


def decode_auxiliary_vm_batch_fixture(
    owner_blob_before: bytes,
    owner_blob_after: bytes,
    arena_before: bytes,
    arena_after: bytes,
    *,
    arena_base: int,
    pool_base: int,
    record_count: int,
    enemy_stride: int,
    enemy_flags_offset: int,
    enemy_active_flag: int,
    context_pointer_offset: int,
    expected_manager_frame: int,
    manager_frame_before: int,
    manager_frame_after: int,
    output_payload_capacity: int = MAXIMUM_STATE_PAYLOAD_BYTES,
) -> AuxiliaryVmBatchObservation:
    """Decode independent before/after fixture bytes with native ABI semantics."""

    batch_status = BatchStatus.OK
    required_owner_bytes = record_count * enemy_stride
    if (
        not 0 <= record_count <= MAXIMUM_OWNERS
        or enemy_stride <= 0
        or enemy_flags_offset < 0
        or context_pointer_offset < 0
        or enemy_flags_offset + 4 > enemy_stride
        or context_pointer_offset
        + 4 * AUXILIARY_POINTERS_PER_OWNER
        > enemy_stride
        or len(owner_blob_before) < required_owner_bytes
        or enemy_flags_offset > context_pointer_offset
        or (
            record_count > 0
            and not _valid_runtime_range(
                pool_base,
                required_owner_bytes,
            )
        )
    ):
        batch_status |= BatchStatus.OWNER_BLOB_INVALID
        return AuxiliaryVmBatchObservation(
            expected_manager_frame=expected_manager_frame,
            manager_frame_before=UNOBSERVED_MANAGER_FRAME,
            manager_frame_after=UNOBSERVED_MANAGER_FRAME,
            batch_status=batch_status,
            records=(),
            process_read_count=0,
            state_payload_bytes=0,
        )
    if output_payload_capacity < 0:
        batch_status |= BatchStatus.OUTPUT_CAPACITY
        return AuxiliaryVmBatchObservation(
            expected_manager_frame=expected_manager_frame,
            manager_frame_before=UNOBSERVED_MANAGER_FRAME,
            manager_frame_after=UNOBSERVED_MANAGER_FRAME,
            batch_status=batch_status,
            records=(),
            process_read_count=0,
            state_payload_bytes=0,
        )
    if manager_frame_before != expected_manager_frame:
        batch_status |= BatchStatus.FRAME_BEFORE_MISMATCH
        return AuxiliaryVmBatchObservation(
            expected_manager_frame=expected_manager_frame,
            manager_frame_before=manager_frame_before,
            manager_frame_after=UNOBSERVED_MANAGER_FRAME,
            batch_status=batch_status,
            records=(),
            process_read_count=1,
            state_payload_bytes=0,
        )

    records: list[AuxiliaryVmBatchRecord] = []
    active_owners = 0
    context_reads = 0
    for slot in range(record_count):
        base = slot * enemy_stride
        flags_before = struct.unpack_from(
            "<I",
            owner_blob_before,
            base + enemy_flags_offset,
        )[0]
        if not flags_before & enemy_active_flag:
            continue
        active_owners += 1
        pointers_before = struct.unpack_from(
            "<4I",
            owner_blob_before,
            base + context_pointer_offset,
        )
        for auxiliary_index, pointer_before in enumerate(pointers_before):
            record_index = len(records)
            record, _payload_size, record_reads = _record(
                slot=slot,
                auxiliary_index=auxiliary_index,
                pool_base=pool_base,
                enemy_stride=enemy_stride,
                flags_before=flags_before,
                pointer_before=pointer_before,
                arena_before=arena_before,
                arena_after=arena_after,
                arena_base=arena_base,
                payload_offset=(
                    record_index
                    * (1 + MAXIMUM_RESTORABLE_FRAMES)
                    * ACTIVE_VM_BYTES
                ),
                payload_capacity=output_payload_capacity,
            )
            records.append(record)
            context_reads += record_reads

    owner_recheck_bytes = (
        context_pointer_offset
        + 4 * AUXILIARY_POINTERS_PER_OWNER
        - enemy_flags_offset
    )
    for owner_index in range(active_owners):
        record_index = owner_index * AUXILIARY_POINTERS_PER_OWNER
        slot = records[record_index].slot
        start = slot * enemy_stride + enemy_flags_offset
        owner_after = owner_blob_after[start : start + owner_recheck_bytes]
        if len(owner_after) != owner_recheck_bytes:
            for index in range(
                record_index,
                record_index + AUXILIARY_POINTERS_PER_OWNER,
            ):
                records[index] = _with_owner_recheck_failure(records[index])
            continue
        flags_after = struct.unpack_from("<I", owner_after, 0)[0]
        for auxiliary_index in range(AUXILIARY_POINTERS_PER_OWNER):
            index = record_index + auxiliary_index
            pointer_after = struct.unpack_from(
                "<I",
                owner_after,
                context_pointer_offset
                - enemy_flags_offset
                + auxiliary_index * 4,
            )[0]
            records[index] = _with_owner_after(
                records[index],
                flags_after=flags_after,
                pointer_after=pointer_after,
                active_flag=enemy_active_flag,
            )

    if manager_frame_after != expected_manager_frame:
        batch_status |= BatchStatus.FRAME_AFTER_MISMATCH
    return AuxiliaryVmBatchObservation(
        expected_manager_frame=expected_manager_frame,
        manager_frame_before=manager_frame_before,
        manager_frame_after=manager_frame_after,
        batch_status=batch_status,
        records=tuple(records),
        process_read_count=2 + active_owners + context_reads,
        state_payload_bytes=sum(
            len(record.active_vm)
            + len(record.saved_frames) * SAVED_FRAME_BYTES
            for record in records
            if record.usable
        ),
    )


def decode_auxiliary_vm_batch_owned_fixture(
    owner_blob: bytes,
    owner_blob_after: bytes,
    arena_before: bytes,
    arena_after: bytes,
    *,
    arena_base: int,
    pool_base: int,
    record_count: int,
    enemy_stride: int,
    enemy_flags_offset: int,
    enemy_active_flag: int,
    context_pointer_offset: int,
    selected_manager_frame: int,
    owner_manager_frame_after: int,
    context_manager_frame_before: int,
    manager_frame_after: int,
    output_payload_capacity: int = MAXIMUM_STATE_PAYLOAD_BYTES,
) -> AuxiliaryVmBatchObservation:
    """Compose the v2 native-owned read schedule over independent bytes."""

    owner_blob_bytes = 0
    if record_count >= 0 and enemy_stride >= 0:
        required = record_count * enemy_stride
        if required <= len(owner_blob) and required <= 0xFFFFFFFF:
            owner_blob_bytes = required
    if owner_manager_frame_after != selected_manager_frame:
        return AuxiliaryVmBatchObservation(
            expected_manager_frame=selected_manager_frame,
            manager_frame_before=UNOBSERVED_MANAGER_FRAME,
            manager_frame_after=UNOBSERVED_MANAGER_FRAME,
            batch_status=BatchStatus.OWNER_CAPTURE_FRAME_MISMATCH,
            records=(),
            process_read_count=3,
            state_payload_bytes=0,
            layout=AUXILIARY_VM_BATCH_LAYOUT_V2,
            owner_manager_frame_after=owner_manager_frame_after,
            owner_blob_bytes=owner_blob_bytes,
        )

    inner = decode_auxiliary_vm_batch_fixture(
        owner_blob,
        owner_blob_after,
        arena_before,
        arena_after,
        arena_base=arena_base,
        pool_base=pool_base,
        record_count=record_count,
        enemy_stride=enemy_stride,
        enemy_flags_offset=enemy_flags_offset,
        enemy_active_flag=enemy_active_flag,
        context_pointer_offset=context_pointer_offset,
        expected_manager_frame=selected_manager_frame,
        manager_frame_before=context_manager_frame_before,
        manager_frame_after=manager_frame_after,
        output_payload_capacity=output_payload_capacity,
    )
    return replace(
        inner,
        process_read_count=inner.process_read_count + 3,
        layout=AUXILIARY_VM_BATCH_LAYOUT_V2,
        owner_manager_frame_after=owner_manager_frame_after,
        owner_blob_bytes=owner_blob_bytes,
    )


__all__ = [
    "decode_auxiliary_vm_batch_fixture",
    "decode_auxiliary_vm_batch_owned_fixture",
]
