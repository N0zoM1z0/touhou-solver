#pragma once

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>

namespace touhou_trace_auxiliary_vm {

constexpr int kMaximumOwners = 64;
constexpr int kPointersPerOwner = 4;
constexpr int kMaximumRecords = kMaximumOwners * kPointersPerOwner;
constexpr std::size_t kContextPrefixBytes = 12;
constexpr std::size_t kActiveVmBytes = 0x228;
constexpr std::size_t kAuxiliaryMarkerOffset = 0x220;
constexpr int kMaximumRestorableFrames = 15;
constexpr std::size_t kMaximumPayloadPerRecord = (
    (1U + kMaximumRestorableFrames) * kActiveVmBytes
);
constexpr std::uint32_t kMinimumRuntimeAddress = 0x00010000U;
constexpr std::uint32_t kMaximumRuntimeAddress = 0x7FFFFFFFU;

enum BatchStatus : std::uint32_t {
    kBatchOk = 0,
    kFrameBeforeMismatch = 1U << 0,
    kFrameAfterMismatch = 1U << 1,
    kOutputCapacity = 1U << 2,
    kOwnerBlobInvalid = 1U << 3,
    kUnsupportedPlatform = 1U << 4,
    kProcessReadFailed = 1U << 5,
};

enum RecordStatus : std::uint32_t {
    kRecordOk = 0,
    kNull = 1U << 0,
    kContextAddressInvalid = 1U << 1,
    kContextPrefixReadFailed = 1U << 2,
    kCallDepthInvalid = 1U << 3,
    kPayloadCapacity = 1U << 4,
    kPayloadReadFailed = 1U << 5,
    kContextRecheckReadFailed = 1U << 6,
    kContextChanged = 1U << 7,
    kActivePcInvalid = 1U << 8,
    kSavedPcInvalid = 1U << 9,
    kAuxiliaryMarkerMismatch = 1U << 10,
    kOwnerInactive = 1U << 11,
    kOwnerFlagsChanged = 1U << 12,
    kPointerChanged = 1U << 13,
    kOwnerRecheckReadFailed = 1U << 14,
};

#pragma pack(push, 1)
struct RecordV1 {
    std::int32_t slot;
    std::uint8_t auxiliary_index;
    std::uint8_t reserved0[3];
    std::uint32_t enemy_pointer;
    std::uint32_t context_pointer;
    std::uint32_t context_pointer_after;
    std::uint32_t enemy_flags_before;
    std::uint32_t enemy_flags_after;
    std::uint32_t status_bits;
    std::uint32_t target_subroutine;
    std::int16_t call_depth;
    std::uint16_t reserved1;
    std::uint32_t auxiliary_marker;
    std::uint32_t payload_offset;
    std::uint32_t payload_size;
};

struct BatchV1 {
    std::uint32_t status_bits;
    std::int32_t expected_manager_frame;
    std::int32_t manager_frame_before;
    std::int32_t manager_frame_after;
    std::uint32_t process_read_count;
    std::uint32_t active_owner_count;
    std::uint32_t record_count;
    std::uint32_t non_null_context_count;
    std::uint32_t usable_context_count;
    std::uint64_t state_payload_bytes;
};
#pragma pack(pop)

static_assert(sizeof(RecordV1) == 52, "unexpected auxiliary record ABI");
static_assert(sizeof(BatchV1) == 44, "unexpected auxiliary batch ABI");

template <typename Value>
Value read_value(const std::uint8_t* bytes, std::size_t offset) {
    Value value{};
    std::memcpy(&value, bytes + offset, sizeof(value));
    return value;
}

inline bool field_fits(
    int stride,
    int offset,
    std::size_t width
) {
    return (
        stride > 0
        && offset >= 0
        && static_cast<std::uint64_t>(offset) + width
            <= static_cast<std::uint64_t>(stride)
    );
}

inline bool valid_runtime_address(std::uint32_t address) {
    return (
        address >= kMinimumRuntimeAddress
        && address <= kMaximumRuntimeAddress
    );
}

inline bool valid_runtime_range(
    std::uint32_t address,
    std::size_t size
) {
    const auto end = (
        static_cast<std::uint64_t>(address)
        + static_cast<std::uint64_t>(size)
    );
    return (
        valid_runtime_address(address)
        && end
            <= static_cast<std::uint64_t>(kMaximumRuntimeAddress) + 1U
    );
}

inline void initialize_record(
    RecordV1* record,
    int slot,
    int auxiliary_index,
    std::uint32_t pool_base,
    int stride,
    std::uint32_t flags_before,
    std::uint32_t pointer_before,
    int record_index
) {
    std::memset(record, 0, sizeof(*record));
    record->slot = slot;
    record->auxiliary_index = static_cast<std::uint8_t>(auxiliary_index);
    record->enemy_pointer = (
        pool_base
        + static_cast<std::uint32_t>(slot)
            * static_cast<std::uint32_t>(stride)
    );
    record->context_pointer = pointer_before;
    record->context_pointer_after = pointer_before;
    record->enemy_flags_before = flags_before;
    record->enemy_flags_after = flags_before;
    record->call_depth = -1;
    record->payload_offset = static_cast<std::uint32_t>(
        static_cast<std::size_t>(record_index)
        * kMaximumPayloadPerRecord
    );
}

template <typename Reader>
void capture_context(
    Reader& reader,
    RecordV1* record,
    std::uint8_t* payload,
    std::uint64_t payload_capacity
) {
    const auto pointer = record->context_pointer;
    if (pointer == 0) {
        record->status_bits |= kNull;
        return;
    }
    if (!valid_runtime_range(pointer, kContextPrefixBytes)) {
        record->status_bits |= kContextAddressInvalid;
        return;
    }
    ++reader.read_count;
    std::uint8_t prefix_before[kContextPrefixBytes]{};
    if (!reader.read_context_before(
            pointer,
            prefix_before,
            sizeof(prefix_before)
        )) {
        record->status_bits |= kContextPrefixReadFailed;
        return;
    }
    record->target_subroutine = read_value<std::uint32_t>(
        prefix_before,
        0
    );
    const auto depth = read_value<std::int16_t>(prefix_before, 6);
    record->call_depth = depth;
    if (depth < 0 || depth > kMaximumRestorableFrames) {
        record->status_bits |= kCallDepthInvalid;
    } else {
        const auto payload_size = (
            (1U + static_cast<std::size_t>(depth)) * kActiveVmBytes
        );
        const auto payload_address = (
            static_cast<std::uint64_t>(pointer) + 8U
        );
        const auto output_end = (
            static_cast<std::uint64_t>(record->payload_offset)
            + static_cast<std::uint64_t>(payload_size)
        );
        if (
            payload_address
                + static_cast<std::uint64_t>(payload_size)
                > static_cast<std::uint64_t>(
                    kMaximumRuntimeAddress
                ) + 1U
        ) {
            record->status_bits |= kContextAddressInvalid;
        } else if (output_end > payload_capacity) {
            record->status_bits |= kPayloadCapacity;
        } else {
            ++reader.read_count;
            auto* destination = payload + record->payload_offset;
            if (!reader.read_context_before(
                    pointer + 8U,
                    destination,
                    payload_size
                )) {
                record->status_bits |= kPayloadReadFailed;
            } else {
                record->payload_size = static_cast<std::uint32_t>(
                    payload_size
                );
                const auto prefix_pc = read_value<std::uint32_t>(
                    prefix_before,
                    8
                );
                const auto active_pc = read_value<std::uint32_t>(
                    destination,
                    0
                );
                if (active_pc != prefix_pc) {
                    record->status_bits |= kContextChanged;
                }
                if (!valid_runtime_address(active_pc)) {
                    record->status_bits |= kActivePcInvalid;
                }
                for (int frame = 0; frame < depth; ++frame) {
                    const auto saved_pc = read_value<std::uint32_t>(
                        destination,
                        kActiveVmBytes
                            + static_cast<std::size_t>(frame)
                                * kActiveVmBytes
                    );
                    if (!valid_runtime_address(saved_pc)) {
                        record->status_bits |= kSavedPcInvalid;
                    }
                }
                record->auxiliary_marker = read_value<std::uint32_t>(
                    destination,
                    kAuxiliaryMarkerOffset
                );
                if (
                    record->auxiliary_marker
                    != static_cast<std::uint32_t>(
                        record->auxiliary_index + 1
                    )
                ) {
                    record->status_bits |= kAuxiliaryMarkerMismatch;
                }
            }
        }
    }
    ++reader.read_count;
    std::uint8_t prefix_after[kContextPrefixBytes]{};
    if (!reader.read_context_after(
            pointer,
            prefix_after,
            sizeof(prefix_after)
        )) {
        record->status_bits |= kContextRecheckReadFailed;
    } else if (
        std::memcmp(
            prefix_before,
            prefix_after,
            sizeof(prefix_before)
        ) != 0
    ) {
        record->status_bits |= kContextChanged;
    }
}

inline void invalidate_payload(RecordV1* record) {
    if (record->status_bits != kRecordOk) {
        record->payload_size = 0;
    }
}

template <typename Reader>
int capture_batch(
    Reader& reader,
    const std::uint8_t* owner_blob_before,
    std::uint64_t owner_blob_before_size,
    std::uint32_t pool_base,
    int record_count,
    int stride,
    int flags_offset,
    std::uint32_t active_flag,
    int context_pointer_offset,
    int expected_manager_frame,
    RecordV1* output_records,
    int output_record_capacity,
    std::uint8_t* output_payload,
    std::uint64_t output_payload_capacity,
    BatchV1* output_batch
) {
    if (
        owner_blob_before == nullptr
        || output_records == nullptr
        || output_payload == nullptr
        || output_batch == nullptr
        || active_flag == 0
        || record_count < 0
        || record_count > kMaximumOwners
        || output_record_capacity < kMaximumRecords
    ) {
        return -1;
    }
    std::memset(output_batch, 0, sizeof(*output_batch));
    output_batch->expected_manager_frame = expected_manager_frame;
    output_batch->manager_frame_before = (
        std::numeric_limits<std::int32_t>::min()
    );
    output_batch->manager_frame_after = (
        std::numeric_limits<std::int32_t>::min()
    );
    if (
        !field_fits(stride, flags_offset, sizeof(std::uint32_t))
        || !field_fits(
            stride,
            context_pointer_offset,
            kPointersPerOwner * sizeof(std::uint32_t)
        )
        || flags_offset > context_pointer_offset
    ) {
        output_batch->status_bits |= kOwnerBlobInvalid;
        return 0;
    }
    const auto required_owner_bytes = (
        static_cast<std::uint64_t>(record_count)
        * static_cast<std::uint64_t>(stride)
    );
    if (
        required_owner_bytes > owner_blob_before_size
        || (
            record_count > 0
            && !valid_runtime_range(
                pool_base,
                static_cast<std::size_t>(required_owner_bytes)
            )
        )
    ) {
        output_batch->status_bits |= kOwnerBlobInvalid;
        return 0;
    }
    ++reader.read_count;
    if (!reader.read_manager_before(
            &output_batch->manager_frame_before
        )) {
        output_batch->status_bits |= kProcessReadFailed;
        output_batch->process_read_count = reader.read_count;
        return 0;
    }
    if (
        output_batch->manager_frame_before
        != expected_manager_frame
    ) {
        output_batch->status_bits |= kFrameBeforeMismatch;
        output_batch->process_read_count = reader.read_count;
        return 0;
    }

    int output_index = 0;
    for (int slot = 0; slot < record_count; ++slot) {
        const auto* owner = (
            owner_blob_before
            + static_cast<std::uint64_t>(slot)
                * static_cast<std::uint64_t>(stride)
        );
        const auto flags = read_value<std::uint32_t>(
            owner,
            static_cast<std::size_t>(flags_offset)
        );
        if ((flags & active_flag) == 0) {
            continue;
        }
        ++output_batch->active_owner_count;
        for (
            int auxiliary_index = 0;
            auxiliary_index < kPointersPerOwner;
            ++auxiliary_index
        ) {
            auto* record = output_records + output_index;
            const auto pointer = read_value<std::uint32_t>(
                owner,
                static_cast<std::size_t>(context_pointer_offset)
                    + static_cast<std::size_t>(auxiliary_index)
                        * sizeof(std::uint32_t)
            );
            initialize_record(
                record,
                slot,
                auxiliary_index,
                pool_base,
                stride,
                flags,
                pointer,
                output_index
            );
            if (pointer != 0) {
                ++output_batch->non_null_context_count;
            }
            capture_context(
                reader,
                record,
                output_payload,
                output_payload_capacity
            );
            ++output_index;
        }
    }
    output_batch->record_count = static_cast<std::uint32_t>(
        output_index
    );

    constexpr std::size_t kMaximumOwnerRecheckBytes = 256;
    std::uint8_t owner_after[kMaximumOwnerRecheckBytes]{};
    const auto owner_recheck_bytes = static_cast<std::size_t>(
        context_pointer_offset
        + kPointersPerOwner * static_cast<int>(sizeof(std::uint32_t))
        - flags_offset
    );
    if (owner_recheck_bytes > sizeof(owner_after)) {
        output_batch->status_bits |= kOwnerBlobInvalid;
    } else {
        for (int index = 0; index < output_index; index += 4) {
            auto* first = output_records + index;
            ++reader.read_count;
            if (!reader.read_owner_after(
                    first->slot,
                    flags_offset,
                    owner_after,
                    owner_recheck_bytes
                )) {
                for (
                    int auxiliary_index = 0;
                    auxiliary_index < 4;
                    ++auxiliary_index
                ) {
                    output_records[index + auxiliary_index].status_bits |= (
                        kOwnerRecheckReadFailed
                    );
                }
                continue;
            }
            const auto flags_after = read_value<std::uint32_t>(
                owner_after,
                0
            );
            for (
                int auxiliary_index = 0;
                auxiliary_index < 4;
                ++auxiliary_index
            ) {
                auto* record = output_records + index + auxiliary_index;
                const auto pointer_after = read_value<std::uint32_t>(
                    owner_after,
                    static_cast<std::size_t>(
                        context_pointer_offset - flags_offset
                    )
                        + static_cast<std::size_t>(auxiliary_index)
                            * sizeof(std::uint32_t)
                );
                record->enemy_flags_after = flags_after;
                record->context_pointer_after = pointer_after;
                if ((flags_after & active_flag) == 0) {
                    record->status_bits |= kOwnerInactive;
                }
                if (flags_after != record->enemy_flags_before) {
                    record->status_bits |= kOwnerFlagsChanged;
                }
                if (pointer_after != record->context_pointer) {
                    record->status_bits |= kPointerChanged;
                }
            }
        }
    }

    ++reader.read_count;
    if (!reader.read_manager_after(
            &output_batch->manager_frame_after
        )) {
        output_batch->status_bits |= kProcessReadFailed;
    } else if (
        output_batch->manager_frame_after
        != expected_manager_frame
    ) {
        output_batch->status_bits |= kFrameAfterMismatch;
    }

    std::uint32_t locally_usable_contexts = 0;
    bool row_failure = false;
    for (int index = 0; index < output_index; ++index) {
        auto* record = output_records + index;
        invalidate_payload(record);
        if (record->status_bits == kRecordOk) {
            ++locally_usable_contexts;
            output_batch->state_payload_bytes += record->payload_size;
        } else if (record->status_bits != kNull) {
            row_failure = true;
        }
    }
    if (output_batch->status_bits == kBatchOk && !row_failure) {
        output_batch->usable_context_count = locally_usable_contexts;
    }
    output_batch->process_read_count = reader.read_count;
    return 0;
}

}  // namespace touhou_trace_auxiliary_vm
