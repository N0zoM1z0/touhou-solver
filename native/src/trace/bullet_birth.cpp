#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstring>

#include "include/touhou_native/export.hpp"

namespace {

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

TOUHOU_EXPORT int touhou_trace_bullet_births_v1(
    const std::uint8_t* blob,
    std::uint64_t blob_size,
    int record_count,
    int stride,
    int state_offset,
    int age_offset,
    int position_offset,
    int velocity_offset,
    int geometry_offset,
    int transform_flags_offset,
    int has_previous,
    int maximum_bootstrap_age,
    std::uint16_t* previous_states,
    std::int32_t* previous_ages,
    std::int32_t* output_slots,
    std::uint8_t* output_codes,
    std::uint16_t* output_states,
    std::int32_t* output_ages,
    std::uint16_t* output_previous_states,
    std::int32_t* output_previous_ages,
    float* output_geometry,
    std::uint32_t* output_transform_flags,
    std::uint8_t* output_geometry_finite,
    int output_capacity,
    std::int32_t* output_active_count,
    std::int32_t* output_evidence_count
) {
    if (
        blob == nullptr
        || previous_states == nullptr
        || previous_ages == nullptr
        || output_slots == nullptr
        || output_codes == nullptr
        || output_states == nullptr
        || output_ages == nullptr
        || output_previous_states == nullptr
        || output_previous_ages == nullptr
        || output_geometry == nullptr
        || output_transform_flags == nullptr
        || output_geometry_finite == nullptr
        || output_active_count == nullptr
        || output_evidence_count == nullptr
        || record_count < 0
        || stride <= 0
        || (has_previous != 0 && has_previous != 1)
        || maximum_bootstrap_age < 0
        || output_capacity < record_count
    ) {
        return -1;
    }
    if (
        !field_fits(stride, state_offset, sizeof(std::uint16_t))
        || !field_fits(stride, age_offset, sizeof(std::int32_t))
        || !field_fits(stride, position_offset, 2U * sizeof(float))
        || !field_fits(stride, velocity_offset, 2U * sizeof(float))
        || !field_fits(stride, geometry_offset, 2U * sizeof(float))
        || !field_fits(
            stride,
            transform_flags_offset,
            sizeof(std::uint32_t)
        )
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
    std::int32_t evidence_count = 0;
    for (int slot = 0; slot < record_count; ++slot) {
        const auto* record = (
            blob
            + static_cast<std::uint64_t>(slot)
                * static_cast<std::uint64_t>(stride)
        );
        const auto state = read_field<std::uint16_t>(record, state_offset);
        const auto age = read_field<std::int32_t>(record, age_offset);
        const auto previous_state = previous_states[slot];
        const auto previous_age = previous_ages[slot];

        std::uint8_t code = 0;
        if (state != 0) {
            ++active_count;
            if (age < 0) {
                code = 1;
            } else if (has_previous == 0) {
                if (age <= maximum_bootstrap_age) {
                    code = 2;
                }
            } else if (previous_state == 0) {
                code = 3;
            } else if (age < previous_age) {
                code = 4;
            }
        }

        if (code != 0) {
            const auto output = static_cast<std::size_t>(evidence_count);
            output_slots[output] = slot;
            output_codes[output] = code;
            output_states[output] = state;
            output_ages[output] = age;
            output_previous_states[output] = previous_state;
            output_previous_ages[output] = previous_age;

            float* geometry = output_geometry + 6U * output;
            std::memcpy(
                geometry,
                record + position_offset,
                2U * sizeof(float)
            );
            std::memcpy(
                geometry + 2,
                record + velocity_offset,
                2U * sizeof(float)
            );
            std::memcpy(
                geometry + 4,
                record + geometry_offset,
                2U * sizeof(float)
            );
            output_transform_flags[output] = (
                read_field<std::uint32_t>(
                    record,
                    transform_flags_offset
                )
            );
            output_geometry_finite[output] = static_cast<std::uint8_t>(
                std::isfinite(geometry[0])
                && std::isfinite(geometry[1])
                && std::isfinite(geometry[2])
                && std::isfinite(geometry[3])
                && std::isfinite(geometry[4])
                && std::isfinite(geometry[5])
            );
            ++evidence_count;
        }
        // All validation and capacity checks precede the scan. A rejected
        // call therefore cannot partially advance observation history.
        previous_states[slot] = state;
        previous_ages[slot] = age;
    }
    *output_active_count = active_count;
    *output_evidence_count = evidence_count;
    return 0;
}
