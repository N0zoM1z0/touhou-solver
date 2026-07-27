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

int touhou_native_impl_clearance_volume_v1(
    float x_start,
    float x_step,
    int column_count,
    float y_start,
    float y_step,
    int row_count,
    int frame_count,
    float player_radius,
    float clearance_cap,
    const float* aabb_x,
    const float* aabb_y,
    const float* aabb_velocity_x,
    const float* aabb_velocity_y,
    const float* aabb_half_width,
    const float* aabb_half_height,
    const float* aabb_base_uncertainty,
    const float* aabb_uncertainty_per_frame,
    int aabb_count,
    const float* segment_origin_x,
    const float* segment_origin_y,
    const float* segment_angle,
    const float* segment_tail,
    const float* segment_head,
    const float* segment_half_width,
    const float* segment_base_uncertainty,
    const float* segment_uncertainty_per_frame,
    int segment_count,
    float* output
) {
    if (
        output == nullptr || x_step <= 0.0F || y_step <= 0.0F
        || column_count < 2 || row_count < 2 || frame_count < 1
        || player_radius < 0.0F || clearance_cap <= 0.0F
        || aabb_count < 0 || segment_count < 0
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
        segment_count > 0
        && (
            segment_origin_x == nullptr || segment_origin_y == nullptr
            || segment_angle == nullptr || segment_tail == nullptr
            || segment_head == nullptr || segment_half_width == nullptr
            || segment_base_uncertainty == nullptr
            || segment_uncertainty_per_frame == nullptr
        )
    ) {
        return 3;
    }

    std::vector<SegmentGeometry> segment_geometry(segment_count);
    for (int index = 0; index < segment_count; ++index) {
        segment_geometry[index] = ::segment_geometry(
            segment_origin_x[index],
            segment_origin_y[index],
            segment_angle[index],
            segment_tail[index],
            segment_head[index]
        );
    }

    const int state_count = row_count * column_count;
    std::vector<float> best_negative(state_count);
    std::vector<float> best_positive_squared(state_count);
    for (int frame = 0; frame < frame_count; ++frame) {
        std::fill(
            best_negative.begin(),
            best_negative.end(),
            clearance_cap
        );
        std::fill(
            best_positive_squared.begin(),
            best_positive_squared.end(),
            clearance_cap * clearance_cap
        );
        for (int index = 0; index < aabb_count; ++index) {
            const float uncertainty = (
                aabb_base_uncertainty[index]
                + frame * aabb_uncertainty_per_frame[index]
            );
            const float position_x = (
                aabb_x[index] + frame * aabb_velocity_x[index]
            );
            const float position_y = (
                aabb_y[index] + frame * aabb_velocity_y[index]
            );
            const float occupied_half_width = (
                player_radius + aabb_half_width[index] + uncertainty
            );
            const float occupied_half_height = (
                player_radius + aabb_half_height[index] + uncertainty
            );
            // Outside this rectangle the AABB clearance cannot improve the
            // configured cap.  Keep a one-cell numeric guard around the
            // analytic bound so the optimized traversal retains the exact
            // scalar candidate set at floating-point boundaries.
            const int first_column = std::max(
                0,
                static_cast<int>(std::floor(
                    (
                        position_x
                        - occupied_half_width
                        - clearance_cap
                        - x_start
                    ) / x_step
                )) - 1
            );
            const int last_column = std::min(
                column_count - 1,
                static_cast<int>(std::ceil(
                    (
                        position_x
                        + occupied_half_width
                        + clearance_cap
                        - x_start
                    ) / x_step
                )) + 1
            );
            const int first_row = std::max(
                0,
                static_cast<int>(std::floor(
                    (
                        position_y
                        - occupied_half_height
                        - clearance_cap
                        - y_start
                    ) / y_step
                )) - 1
            );
            const int last_row = std::min(
                row_count - 1,
                static_cast<int>(std::ceil(
                    (
                        position_y
                        + occupied_half_height
                        + clearance_cap
                        - y_start
                    ) / y_step
                )) + 1
            );
            for (int row = first_row; row <= last_row; ++row) {
                const float sample_y = y_start + row * y_step;
                for (
                    int column = first_column;
                    column <= last_column;
                    ++column
                ) {
                    const float sample_x = x_start + column * x_step;
                    const int state = row * column_count + column;
                    const float dx = std::abs(sample_x - position_x) - (
                        occupied_half_width
                    );
                    const float dy = std::abs(sample_y - position_y) - (
                        occupied_half_height
                    );
                    if (dx <= 0.0F && dy <= 0.0F) {
                        best_negative[state] = std::min(
                            best_negative[state],
                            std::max(dx, dy)
                        );
                        continue;
                    }
                    if (best_negative[state] <= 0.0F) {
                        continue;
                    }
                    const float positive_x = std::max(dx, 0.0F);
                    const float positive_y = std::max(dy, 0.0F);
                    const float squared = (
                        positive_x * positive_x
                        + positive_y * positive_y
                    );
                    best_positive_squared[state] = std::min(
                        best_positive_squared[state],
                        squared
                    );
                }
            }
        }
        for (int row = 0; row < row_count; ++row) {
            for (int column = 0; column < column_count; ++column) {
                const int state = row * column_count + column;
                output[clearance_index(
                    frame,
                    row,
                    column,
                    row_count,
                    column_count
                )] = (
                    best_negative[state] <= 0.0F
                    ? best_negative[state]
                    : std::sqrt(best_positive_squared[state])
                );
            }
        }
        for (int index = 0; index < segment_count; ++index) {
            const SegmentGeometry& segment = segment_geometry[index];
            const float occupied_radius = (
                player_radius
                + segment_half_width[index]
                + segment_base_uncertainty[index]
                + frame * segment_uncertainty_per_frame[index]
            );
            // A segment cannot improve the cap outside its finite geometry
            // bounds expanded by the occupied radius and cap. Retain a
            // one-cell numeric guard at floating-point boundaries.
            const int first_column = std::max(
                0,
                static_cast<int>(std::floor(
                    (
                        segment.min_x
                        - occupied_radius
                        - clearance_cap
                        - x_start
                    ) / x_step
                )) - 1
            );
            const int last_column = std::min(
                column_count - 1,
                static_cast<int>(std::ceil(
                    (
                        segment.max_x
                        + occupied_radius
                        + clearance_cap
                        - x_start
                    ) / x_step
                )) + 1
            );
            const int first_row = std::max(
                0,
                static_cast<int>(std::floor(
                    (
                        segment.min_y
                        - occupied_radius
                        - clearance_cap
                        - y_start
                    ) / y_step
                )) - 1
            );
            const int last_row = std::min(
                row_count - 1,
                static_cast<int>(std::ceil(
                    (
                        segment.max_y
                        + occupied_radius
                        + clearance_cap
                        - y_start
                    ) / y_step
                )) + 1
            );
            for (int row = first_row; row <= last_row; ++row) {
                const float sample_y = y_start + row * y_step;
                for (
                    int column = first_column;
                    column <= last_column;
                    ++column
                ) {
                    const float sample_x = x_start + column * x_step;
                    const float clearance = segment_clearance(
                        sample_x,
                        sample_y,
                        segment,
                        occupied_radius
                    );
                    const std::size_t output_index = clearance_index(
                        frame,
                        row,
                        column,
                        row_count,
                        column_count
                    );
                    output[output_index] = std::min(
                        output[output_index],
                        clearance
                    );
                }
            }
        }
    }
    return 0;
}
