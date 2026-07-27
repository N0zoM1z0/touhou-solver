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

int touhou_native_impl_aabb_trajectory_clearance_v1(
    float x_start,
    float x_step,
    int column_count,
    float y_start,
    float y_step,
    int row_count,
    int frame_count,
    float player_radius,
    const std::int32_t* frame_offsets,
    const float* aabb_x,
    const float* aabb_y,
    const float* aabb_half_width,
    const float* aabb_half_height,
    const float* aabb_base_uncertainty,
    const float* aabb_uncertainty_per_frame,
    int aabb_sample_count,
    float* inout
) {
    if (
        inout == nullptr || frame_offsets == nullptr
        || x_step <= 0.0F || y_step <= 0.0F
        || column_count < 2 || row_count < 2 || frame_count < 1
        || player_radius < 0.0F || aabb_sample_count < 0
    ) {
        return 1;
    }
    if (
        frame_offsets[0] != 0
        || frame_offsets[frame_count] != aabb_sample_count
    ) {
        return 2;
    }
    if (
        aabb_sample_count > 0
        && (
            aabb_x == nullptr || aabb_y == nullptr
            || aabb_half_width == nullptr || aabb_half_height == nullptr
            || aabb_base_uncertainty == nullptr
            || aabb_uncertainty_per_frame == nullptr
        )
    ) {
        return 3;
    }

    for (int frame = 0; frame < frame_count; ++frame) {
        const int begin = frame_offsets[frame];
        const int end = frame_offsets[frame + 1];
        if (begin < 0 || end < begin || end > aabb_sample_count) {
            return 4;
        }
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
        for (int index = begin; index < end; ++index) {
            const float uncertainty = (
                aabb_base_uncertainty[index]
                + frame * aabb_uncertainty_per_frame[index]
            );
            const float occupied_half_width = (
                player_radius + aabb_half_width[index] + uncertainty
            );
            const float occupied_half_height = (
                player_radius + aabb_half_height[index] + uncertainty
            );
            const float improvement_radius = std::max(frame_maximum, 0.0F);
            const int first_column = std::max(
                0,
                static_cast<int>(std::floor(
                    (
                        aabb_x[index]
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
                        aabb_x[index]
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
                        aabb_y[index]
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
                        aabb_y[index]
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
                    const float sample_x = x_start + column * x_step;
                    const float dx = std::abs(
                        sample_x - aabb_x[index]
                    ) - occupied_half_width;
                    const float dy = std::abs(
                        sample_y - aabb_y[index]
                    ) - occupied_half_height;
                    const float clearance = (
                        dx <= 0.0F && dy <= 0.0F
                        ? std::max(dx, dy)
                        : std::hypot(
                            std::max(dx, 0.0F),
                            std::max(dy, 0.0F)
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
