#include <cstddef>
#include <cstdint>
#include <cstring>

#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#endif

#include "include/touhou_native/export.hpp"
#include "src/trace/auxiliary_vm_batch_core.hpp"

namespace {

using touhou_trace_auxiliary_vm::BatchV1;
using touhou_trace_auxiliary_vm::RecordV1;

struct FixtureReader {
    const std::uint8_t* owner_after;
    std::uint64_t owner_after_size;
    const std::uint8_t* arena_before;
    std::uint64_t arena_before_size;
    const std::uint8_t* arena_after;
    std::uint64_t arena_after_size;
    std::uint32_t arena_base;
    int stride;
    std::int32_t manager_before;
    std::int32_t manager_after;
    std::uint32_t read_count = 0;

    bool read_arena(
        const std::uint8_t* arena,
        std::uint64_t arena_size,
        std::uint32_t address,
        void* destination,
        std::size_t size
    ) const {
        if (address < arena_base) {
            return false;
        }
        const auto offset = static_cast<std::uint64_t>(
            address - arena_base
        );
        if (
            offset + static_cast<std::uint64_t>(size) < offset
            || offset + static_cast<std::uint64_t>(size) > arena_size
        ) {
            return false;
        }
        std::memcpy(destination, arena + offset, size);
        return true;
    }

    bool read_manager_before(std::int32_t* output) const {
        *output = manager_before;
        return true;
    }

    bool read_manager_after(std::int32_t* output) const {
        *output = manager_after;
        return true;
    }

    bool read_context_before(
        std::uint32_t address,
        void* destination,
        std::size_t size
    ) const {
        return read_arena(
            arena_before,
            arena_before_size,
            address,
            destination,
            size
        );
    }

    bool read_context_after(
        std::uint32_t address,
        void* destination,
        std::size_t size
    ) const {
        return read_arena(
            arena_after,
            arena_after_size,
            address,
            destination,
            size
        );
    }

    bool read_owner_after(
        int slot,
        int offset,
        void* destination,
        std::size_t size
    ) const {
        if (slot < 0 || offset < 0) {
            return false;
        }
        const auto start = (
            static_cast<std::uint64_t>(slot)
                * static_cast<std::uint64_t>(stride)
            + static_cast<std::uint64_t>(offset)
        );
        if (
            start + static_cast<std::uint64_t>(size) < start
            || start + static_cast<std::uint64_t>(size)
                > owner_after_size
        ) {
            return false;
        }
        std::memcpy(destination, owner_after + start, size);
        return true;
    }
};

#ifdef _WIN32
struct ProcessReader {
    HANDLE process;
    std::uint32_t pool_base;
    std::uint32_t manager_frame_address;
    int stride;
    std::uint32_t read_count = 0;

    bool read_remote(
        std::uintptr_t address,
        void* destination,
        std::size_t size
    ) const {
        SIZE_T transferred = 0;
        return (
            ReadProcessMemory(
                process,
                reinterpret_cast<LPCVOID>(address),
                destination,
                size,
                &transferred
            )
            && transferred == size
        );
    }

    bool read_manager_before(std::int32_t* output) const {
        return read_remote(
            manager_frame_address,
            output,
            sizeof(*output)
        );
    }

    bool read_manager_after(std::int32_t* output) const {
        return read_manager_before(output);
    }

    bool read_context_before(
        std::uint32_t address,
        void* destination,
        std::size_t size
    ) const {
        return read_remote(address, destination, size);
    }

    bool read_context_after(
        std::uint32_t address,
        void* destination,
        std::size_t size
    ) const {
        return read_remote(address, destination, size);
    }

    bool read_owner_after(
        int slot,
        int offset,
        void* destination,
        std::size_t size
    ) const {
        const auto address = (
            static_cast<std::uintptr_t>(pool_base)
            + static_cast<std::uintptr_t>(slot)
                * static_cast<std::uintptr_t>(stride)
            + static_cast<std::uintptr_t>(offset)
        );
        return read_remote(address, destination, size);
    }
};
#endif

}  // namespace

TOUHOU_EXPORT int touhou_trace_auxiliary_vm_batch_fixture_v1(
    const std::uint8_t* owner_blob_before,
    std::uint64_t owner_blob_before_size,
    const std::uint8_t* owner_blob_after,
    std::uint64_t owner_blob_after_size,
    const std::uint8_t* arena_before,
    std::uint64_t arena_before_size,
    const std::uint8_t* arena_after,
    std::uint64_t arena_after_size,
    std::uint32_t arena_base,
    std::uint32_t pool_base,
    int record_count,
    int stride,
    int flags_offset,
    std::uint32_t active_flag,
    int context_pointer_offset,
    int expected_manager_frame,
    int manager_frame_before,
    int manager_frame_after,
    RecordV1* output_records,
    int output_record_capacity,
    std::uint8_t* output_payload,
    std::uint64_t output_payload_capacity,
    BatchV1* output_batch
) {
    if (
        owner_blob_after == nullptr
        || arena_before == nullptr
        || arena_after == nullptr
    ) {
        return -1;
    }
    FixtureReader reader{
        owner_blob_after,
        owner_blob_after_size,
        arena_before,
        arena_before_size,
        arena_after,
        arena_after_size,
        arena_base,
        stride,
        manager_frame_before,
        manager_frame_after,
    };
    return touhou_trace_auxiliary_vm::capture_batch(
        reader,
        owner_blob_before,
        owner_blob_before_size,
        pool_base,
        record_count,
        stride,
        flags_offset,
        active_flag,
        context_pointer_offset,
        expected_manager_frame,
        output_records,
        output_record_capacity,
        output_payload,
        output_payload_capacity,
        output_batch
    );
}

TOUHOU_EXPORT int touhou_trace_auxiliary_vm_batch_process_v1(
    std::uint64_t process_handle,
    const std::uint8_t* owner_blob_before,
    std::uint64_t owner_blob_before_size,
    std::uint32_t pool_base,
    std::uint32_t manager_frame_address,
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
#ifdef _WIN32
    if (process_handle == 0) {
        return -1;
    }
    ProcessReader reader{
        reinterpret_cast<HANDLE>(
            static_cast<std::uintptr_t>(process_handle)
        ),
        pool_base,
        manager_frame_address,
        stride,
    };
    return touhou_trace_auxiliary_vm::capture_batch(
        reader,
        owner_blob_before,
        owner_blob_before_size,
        pool_base,
        record_count,
        stride,
        flags_offset,
        active_flag,
        context_pointer_offset,
        expected_manager_frame,
        output_records,
        output_record_capacity,
        output_payload,
        output_payload_capacity,
        output_batch
    );
#else
    (void)process_handle;
    (void)owner_blob_before;
    (void)owner_blob_before_size;
    (void)pool_base;
    (void)manager_frame_address;
    (void)record_count;
    (void)stride;
    (void)flags_offset;
    (void)active_flag;
    (void)context_pointer_offset;
    (void)expected_manager_frame;
    (void)output_records;
    (void)output_record_capacity;
    (void)output_payload;
    (void)output_payload_capacity;
    if (output_batch == nullptr) {
        return -1;
    }
    std::memset(output_batch, 0, sizeof(*output_batch));
    output_batch->status_bits = (
        touhou_trace_auxiliary_vm::kUnsupportedPlatform
    );
    return 0;
#endif
}
