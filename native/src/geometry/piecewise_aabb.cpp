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
#include "include/touhou_native/lattice.hpp"

using touhou_native::clearance_index;
#include "src/geometry/segment_geometry.hpp"

int touhou_native_impl_piecewise_aabb_clearance_v1(
    float x_start,
    float x_step,
    int column_count,
    float y_start,
    float y_step,
    int row_count,
    int frame_count,
    float player_radius,
    const double* aabb_x,
    const double* aabb_y,
    const double* aabb_velocity_x,
    const double* aabb_velocity_y,
    const float* aabb_half_width,
    const float* aabb_half_height,
    const float* aabb_base_uncertainty,
    const float* aabb_uncertainty_per_frame,
    int aabb_count,
    const std::int32_t* event_offsets,
    const std::int32_t* event_frames,
    const double* event_velocity_x,
    const double* event_velocity_y,
    int event_count,
    float* inout
) {
    if (
        inout == nullptr || event_offsets == nullptr
        || x_step <= 0.0F || y_step <= 0.0F
        || column_count < 2 || row_count < 2 || frame_count < 1
        || player_radius < 0.0F || aabb_count < 0 || event_count < 0
    ) {
        return 1;
    }
    if (
        aabb_count > 0
        && (
            aabb_x == nullptr || aabb_y == nullptr
            || aabb_velocity_x == nullptr || aabb_velocity_y == nullptr
            || aabb_half_width == nullptr || aabb_half_height == nullptr
            || aabb_base_uncertainty == nullptr
            || aabb_uncertainty_per_frame == nullptr
        )
    ) {
        return 2;
    }
    if (
        event_offsets[0] != 0
        || event_offsets[aabb_count] != event_count
    ) {
        return 3;
    }
    if (
        event_count > 0
        && (
            event_frames == nullptr || event_velocity_x == nullptr
            || event_velocity_y == nullptr
        )
    ) {
        return 4;
    }
    for (int hazard = 0; hazard < aabb_count; ++hazard) {
        const int begin = event_offsets[hazard];
        const int end = event_offsets[hazard + 1];
        if (begin < 0 || end < begin || end > event_count) {
            return 5;
        }
        int previous_frame = 0;
        for (int event = begin; event < end; ++event) {
            if (event_frames[event] <= previous_frame) {
                return 6;
            }
            previous_frame = event_frames[event];
        }
    }

    for (int frame = 0; frame < frame_count; ++frame) {
        float frame_maximum = -std::numeric_limits<float>::infinity();
        for (int row = 0; row < row_count; ++row) {
            for (int column = 0; column < column_count; ++column) {
                frame_maximum = std::max(
                    frame_maximum,
                    inout[clearance_index(
                        frame,
                        row,
                        column,
                        row_count,
                        column_count
                    )]
                );
            }
        }
        const float improvement_radius = std::max(frame_maximum, 0.0F);
        for (int hazard = 0; hazard < aabb_count; ++hazard) {
            double position_x = (
                aabb_x[hazard] + aabb_velocity_x[hazard] * frame
            );
            double position_y = (
                aabb_y[hazard] + aabb_velocity_y[hazard] * frame
            );
            double previous_velocity_x = aabb_velocity_x[hazard];
            double previous_velocity_y = aabb_velocity_y[hazard];
            const int event_begin = event_offsets[hazard];
            const int event_end = event_offsets[hazard + 1];
            for (int event = event_begin; event < event_end; ++event) {
                const int event_frame = event_frames[event];
                if (event_frame > frame) {
                    break;
                }
                const double affected_updates = static_cast<double>(
                    frame - event_frame + 1
                );
                position_x += (
                    event_velocity_x[event] - previous_velocity_x
                ) * affected_updates;
                position_y += (
                    event_velocity_y[event] - previous_velocity_y
                ) * affected_updates;
                previous_velocity_x = event_velocity_x[event];
                previous_velocity_y = event_velocity_y[event];
            }

            const float uncertainty = (
                aabb_base_uncertainty[hazard]
                + frame * aabb_uncertainty_per_frame[hazard]
            );
            const float occupied_half_width = (
                player_radius + aabb_half_width[hazard] + uncertainty
            );
            const float occupied_half_height = (
                player_radius + aabb_half_height[hazard] + uncertainty
            );
            const int first_column = std::max(
                0,
                static_cast<int>(std::floor(
                    (
                        position_x
                        - occupied_half_width
                        - improvement_radius
                        - x_start
                    ) / x_step
                ))
            );
            const int last_column = std::min(
                column_count - 1,
                static_cast<int>(std::ceil(
                    (
                        position_x
                        + occupied_half_width
                        + improvement_radius
                        - x_start
                    ) / x_step
                ))
            );
            const int first_row = std::max(
                0,
                static_cast<int>(std::floor(
                    (
                        position_y
                        - occupied_half_height
                        - improvement_radius
                        - y_start
                    ) / y_step
                ))
            );
            const int last_row = std::min(
                row_count - 1,
                static_cast<int>(std::ceil(
                    (
                        position_y
                        + occupied_half_height
                        + improvement_radius
                        - y_start
                    ) / y_step
                ))
            );
            for (int row = first_row; row <= last_row; ++row) {
                const float sample_y = y_start + row * y_step;
                for (
                    int column = first_column;
                    column <= last_column;
                    ++column
                ) {
                    const double sample_x = x_start + column * x_step;
                    const double dx = std::abs(sample_x - position_x)
                        - occupied_half_width;
                    const double dy = std::abs(sample_y - position_y)
                        - occupied_half_height;
                    const float clearance = static_cast<float>(
                        dx <= 0.0F && dy <= 0.0F
                        ? std::max(dx, dy)
                        : std::hypot(
                            std::max(dx, 0.0),
                            std::max(dy, 0.0)
                        )
                    );
                    const std::size_t output_index = clearance_index(
                        frame,
                        row,
                        column,
                        row_count,
                        column_count
                    );
                    inout[output_index] = std::min(
                        inout[output_index],
                        clearance
                    );
                }
            }
        }
    }
    return 0;
}
