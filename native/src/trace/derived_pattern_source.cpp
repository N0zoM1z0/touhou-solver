#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstring>

#include "include/touhou_native/export.hpp"

namespace {

constexpr std::uint32_t kEmitDerivedPattern = 0x01000000U;
constexpr std::uint32_t kDerivedPatternParameters = 0x02000000U;
constexpr int kTransformRecordWords = 6;
constexpr int kTransformKindWord = 4;
constexpr int kTransformAllowWhileActiveWord = 5;

bool field_fits(int stride, int offset, std::size_t width) {
    return (
        offset >= 0
        && static_cast<std::uint64_t>(offset) + width
            <= static_cast<std::uint64_t>(stride)
    );
}

template <typename Value>
Value read_field(const std::uint8_t* record, int offset) {
    Value value{};
    std::memcpy(&value, record + offset, sizeof(value));
    return value;
}

}  // namespace

TOUHOU_EXPORT int touhou_trace_derived_pattern_sources_v1(
    const std::uint8_t* blob,
    std::uint64_t blob_size,
    int record_count,
    int stride,
    int state_offset,
    int age_offset,
    int position_offset,
    int transform_flags_offset,
    int original_transform_flags_offset,
    int queue_cursor_offset,
    int transform_program_offset,
    int transform_program_length,
    int transform_record_size,
    std::int32_t* output_slots,
    std::uint16_t* output_states,
    std::int32_t* output_ages,
    float* output_positions,
    std::uint32_t* output_transform_flags,
    std::uint32_t* output_original_transform_flags,
    std::int32_t* output_queue_cursors,
    std::uint32_t* output_record_words,
    std::uint8_t* output_geometry_finite,
    int output_capacity,
    std::int32_t* output_active_count,
    std::int32_t* output_candidate_count
) {
    if (
        blob == nullptr
        || output_slots == nullptr
        || output_states == nullptr
        || output_ages == nullptr
        || output_positions == nullptr
        || output_transform_flags == nullptr
        || output_original_transform_flags == nullptr
        || output_queue_cursors == nullptr
        || output_record_words == nullptr
        || output_geometry_finite == nullptr
        || output_active_count == nullptr
        || output_candidate_count == nullptr
        || record_count < 0
        || stride <= 0
        || transform_program_length < 2
        || transform_record_size < (
            kTransformRecordWords * static_cast<int>(sizeof(std::uint32_t))
        )
        || output_capacity < record_count
    ) {
        return -1;
    }
    const auto program_width = (
        static_cast<std::uint64_t>(transform_program_length)
        * static_cast<std::uint64_t>(transform_record_size)
    );
    if (
        !field_fits(stride, state_offset, sizeof(std::uint16_t))
        || !field_fits(stride, age_offset, sizeof(std::int32_t))
        || !field_fits(stride, position_offset, 2U * sizeof(float))
        || !field_fits(
            stride,
            transform_flags_offset,
            sizeof(std::uint32_t)
        )
        || !field_fits(
            stride,
            original_transform_flags_offset,
            sizeof(std::uint32_t)
        )
        || !field_fits(stride, queue_cursor_offset, sizeof(std::int32_t))
        || program_width > static_cast<std::uint64_t>(stride)
        || transform_program_offset < 0
        || static_cast<std::uint64_t>(transform_program_offset)
                + program_width
            > static_cast<std::uint64_t>(stride)
    ) {
        return -2;
    }
    const auto required_size = (
        static_cast<std::uint64_t>(record_count)
        * static_cast<std::uint64_t>(stride)
    );
    if (required_size > blob_size) {
        return -3;
    }

    std::int32_t active_count = 0;
    std::int32_t candidate_count = 0;
    for (int slot = 0; slot < record_count; ++slot) {
        const auto* record = (
            blob
            + static_cast<std::uint64_t>(slot)
                * static_cast<std::uint64_t>(stride)
        );
        const auto state = read_field<std::uint16_t>(record, state_offset);
        if (state == 0) {
            continue;
        }
        ++active_count;
        const auto cursor = read_field<std::int32_t>(
            record,
            queue_cursor_offset
        );
        if (cursor < 0 || cursor + 1 >= transform_program_length) {
            continue;
        }
        const auto* first = (
            record
            + transform_program_offset
            + static_cast<std::uint64_t>(cursor)
                * static_cast<std::uint64_t>(transform_record_size)
        );
        const auto* second = first + transform_record_size;
        const auto first_kind = read_field<std::uint32_t>(
            first,
            kTransformKindWord * static_cast<int>(sizeof(std::uint32_t))
        );
        const auto second_kind = read_field<std::uint32_t>(
            second,
            kTransformKindWord * static_cast<int>(sizeof(std::uint32_t))
        );
        if (
            first_kind != kEmitDerivedPattern
            || second_kind != kDerivedPatternParameters
        ) {
            continue;
        }
        const auto original_flags = read_field<std::uint32_t>(
            record,
            original_transform_flags_offset
        );
        if ((first_kind & original_flags) == 0) {
            continue;
        }
        const auto transform_flags = read_field<std::uint32_t>(
            record,
            transform_flags_offset
        );
        const auto allow_while_active = read_field<std::uint32_t>(
            first,
            kTransformAllowWhileActiveWord
                * static_cast<int>(sizeof(std::uint32_t))
        );
        if (allow_while_active == 0 && transform_flags != 0) {
            continue;
        }

        const auto output = static_cast<std::size_t>(candidate_count);
        output_slots[output] = slot;
        output_states[output] = state;
        output_ages[output] = read_field<std::int32_t>(record, age_offset);
        std::memcpy(
            output_positions + 2U * output,
            record + position_offset,
            2U * sizeof(float)
        );
        output_transform_flags[output] = transform_flags;
        output_original_transform_flags[output] = original_flags;
        output_queue_cursors[output] = cursor;
        auto* words = (
            output_record_words
            + 2U * kTransformRecordWords * output
        );
        std::memcpy(
            words,
            first,
            kTransformRecordWords * sizeof(std::uint32_t)
        );
        std::memcpy(
            words + kTransformRecordWords,
            second,
            kTransformRecordWords * sizeof(std::uint32_t)
        );
        const auto* position = output_positions + 2U * output;
        output_geometry_finite[output] = static_cast<std::uint8_t>(
            std::isfinite(position[0]) && std::isfinite(position[1])
        );
        ++candidate_count;
    }
    *output_active_count = active_count;
    *output_candidate_count = candidate_count;
    return 0;
}
