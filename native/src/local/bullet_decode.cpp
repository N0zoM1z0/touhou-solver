#include <algorithm>
#include <atomic>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <functional>
#include <limits>
#include <memory>
#include <mutex>
#include <thread>
#include <unordered_map>
#include <vector>

#include "src/internal/abi_impl.hpp"
#include "include/touhou_native/local_hazard_stop.hpp"

int touhou_native_impl_decode_bullet_pool_v1(
    const std::uint8_t* blob,
    std::uint64_t blob_size,
    int record_count,
    int stride,
    int state_offset,
    int geometry_offset,
    int position_offset,
    int velocity_offset,
    int speed_offset,
    int angle_offset,
    int transform_flags_offset,
    int original_transform_flags_offset,
    int callback_phase_offset,
    int callback_aux_offset,
    float* output_x,
    float* output_y,
    float* output_velocity_x,
    float* output_velocity_y,
    float* output_half_width,
    float* output_half_height,
    std::uint32_t* output_transform_flags,
    std::int32_t* output_slots,
    float* output_speed,
    float* output_angle,
    std::int16_t* output_callback_phase,
    std::uint8_t* output_callback_aux,
    std::uint32_t* output_original_transform_flags,
    int output_capacity,
    std::int32_t* output_count
) {
    if (
        blob == nullptr
        || output_x == nullptr
        || output_y == nullptr
        || output_velocity_x == nullptr
        || output_velocity_y == nullptr
        || output_half_width == nullptr
        || output_half_height == nullptr
        || output_transform_flags == nullptr
        || output_slots == nullptr
        || output_speed == nullptr
        || output_angle == nullptr
        || output_callback_phase == nullptr
        || output_callback_aux == nullptr
        || output_original_transform_flags == nullptr
        || output_count == nullptr
        || record_count < 0
        || stride <= 0
        || output_capacity < record_count
    ) {
        return -1;
    }

    const auto field_fits = [stride](
        int offset,
        std::size_t width
    ) {
        return (
            offset >= 0
            && static_cast<std::uint64_t>(offset) + width
                <= static_cast<std::uint64_t>(stride)
        );
    };
    if (
        !field_fits(state_offset, sizeof(std::uint16_t))
        || !field_fits(geometry_offset, 2U * sizeof(float))
        || !field_fits(position_offset, 2U * sizeof(float))
        || !field_fits(velocity_offset, 2U * sizeof(float))
        || !field_fits(speed_offset, sizeof(float))
        || !field_fits(angle_offset, sizeof(float))
        || !field_fits(transform_flags_offset, sizeof(std::uint32_t))
        || !field_fits(
            original_transform_flags_offset,
            sizeof(std::uint32_t)
        )
        || !field_fits(callback_phase_offset, sizeof(std::int16_t))
        || !field_fits(callback_aux_offset, sizeof(std::uint8_t))
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
    for (int slot = 0; slot < record_count; ++slot) {
        const auto* record = (
            blob
            + static_cast<std::uint64_t>(slot)
                * static_cast<std::uint64_t>(stride)
        );
        std::uint16_t state = 0;
        std::memcpy(
            &state,
            record + state_offset,
            sizeof(state)
        );
        if (state == 0) {
            continue;
        }

        float geometry[2] = {};
        float position[2] = {};
        float velocity[2] = {};
        std::memcpy(
            geometry,
            record + geometry_offset,
            sizeof(geometry)
        );
        std::memcpy(
            position,
            record + position_offset,
            sizeof(position)
        );
        std::memcpy(
            velocity,
            record + velocity_offset,
            sizeof(velocity)
        );
        if (
            !std::isfinite(geometry[0])
            || !std::isfinite(geometry[1])
            || !std::isfinite(position[0])
            || !std::isfinite(position[1])
            || !std::isfinite(velocity[0])
            || !std::isfinite(velocity[1])
        ) {
            continue;
        }

        const auto output = static_cast<std::size_t>(active_count);
        output_x[output] = position[0];
        output_y[output] = position[1];
        output_velocity_x[output] = velocity[0];
        output_velocity_y[output] = velocity[1];
        output_half_width[output] = std::fabs(geometry[0]) * 0.5F;
        output_half_height[output] = std::fabs(geometry[1]) * 0.5F;
        output_slots[output] = slot;
        std::memcpy(
            output_transform_flags + output,
            record + transform_flags_offset,
            sizeof(std::uint32_t)
        );
        std::memcpy(
            output_speed + output,
            record + speed_offset,
            sizeof(float)
        );
        std::memcpy(
            output_angle + output,
            record + angle_offset,
            sizeof(float)
        );
        std::memcpy(
            output_callback_phase + output,
            record + callback_phase_offset,
            sizeof(std::int16_t)
        );
        std::memcpy(
            output_callback_aux + output,
            record + callback_aux_offset,
            sizeof(std::uint8_t)
        );
        std::memcpy(
            output_original_transform_flags + output,
            record + original_transform_flags_offset,
            sizeof(std::uint32_t)
        );
        ++active_count;
    }
    *output_count = active_count;
    return 0;
}
