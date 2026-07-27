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

int touhou_native_impl_segment_trajectory_clearance_v1(
    float x_start,
    float x_step,
    int column_count,
    float y_start,
    float y_step,
    int row_count,
    int frame_count,
    float player_radius,
    const std::int32_t* frame_offsets,
    const float* segment_origin_x,
    const float* segment_origin_y,
    const float* segment_angle,
    const float* segment_tail,
    const float* segment_head,
    const float* segment_half_width,
    const float* segment_base_uncertainty,
    const float* segment_uncertainty_per_frame,
    int segment_sample_count,
    float* inout
) {
    if (
        inout == nullptr || frame_offsets == nullptr
        || x_step <= 0.0F || y_step <= 0.0F
        || column_count < 2 || row_count < 2 || frame_count < 1
        || player_radius < 0.0F || segment_sample_count < 0
    ) {
        return 1;
    }
    if (
        frame_offsets[0] != 0
        || frame_offsets[frame_count] != segment_sample_count
    ) {
        return 2;
    }
    if (
        segment_sample_count > 0
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

    std::vector<SegmentGeometry> geometry(segment_sample_count);
    std::vector<float> occupied_radius(segment_sample_count);
    for (int frame = 0; frame < frame_count; ++frame) {
        const int begin = frame_offsets[frame];
        const int end = frame_offsets[frame + 1];
        if (begin < 0 || end < begin || end > segment_sample_count) {
            return 4;
        }
        for (int index = begin; index < end; ++index) {
            geometry[index] = segment_geometry(
                segment_origin_x[index],
                segment_origin_y[index],
                segment_angle[index],
                segment_tail[index],
                segment_head[index]
            );
            occupied_radius[index] = (
                player_radius
                + segment_half_width[index]
                + segment_base_uncertainty[index]
                + frame * segment_uncertainty_per_frame[index]
            );
        }
    }

    for (int frame = 0; frame < frame_count; ++frame) {
        const int begin = frame_offsets[frame];
        const int end = frame_offsets[frame + 1];
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
            const SegmentGeometry& segment = geometry[index];
            const float improvement_radius = (
                frame_maximum + occupied_radius[index]
            );
            if (improvement_radius <= 0.0F) {
                continue;
            }
            int first_column = 0;
            int last_column = column_count - 1;
            int first_row = 0;
            int last_row = row_count - 1;
            if (std::isfinite(improvement_radius)) {
                first_column = std::max(
                    0,
                    static_cast<int>(std::floor(
                        (
                            segment.min_x
                            - improvement_radius
                            - x_start
                        ) / x_step
                    ))
                );
                last_column = std::min(
                    column_count - 1,
                    static_cast<int>(std::ceil(
                        (
                            segment.max_x
                            + improvement_radius
                            - x_start
                        ) / x_step
                    ))
                );
                first_row = std::max(
                    0,
                    static_cast<int>(std::floor(
                        (
                            segment.min_y
                            - improvement_radius
                            - y_start
                        ) / y_step
                    ))
                );
                last_row = std::min(
                    row_count - 1,
                    static_cast<int>(std::ceil(
                        (
                            segment.max_y
                            + improvement_radius
                            - y_start
                        ) / y_step
                    ))
                );
            }
            for (int row = first_row; row <= last_row; ++row) {
                const float sample_y = y_start + row * y_step;
                for (
                    int column = first_column;
                    column <= last_column;
                    ++column
                ) {
                    const float sample_x = x_start + column * x_step;
                    const std::size_t output_index = clearance_index(
                        frame,
                        row,
                        column,
                        row_count,
                        column_count
                    );
                    const float improvement_distance = (
                        inout[output_index] + occupied_radius[index]
                    );
                    if (improvement_distance <= 0.0F) {
                        continue;
                    }
                    const float distance_squared = segment_distance_squared(
                        sample_x,
                        sample_y,
                        segment
                    );
                    const float improvement_squared = (
                        improvement_distance * improvement_distance
                    );
                    const float rounding_guard = (
                        8.0F
                        * std::numeric_limits<float>::epsilon()
                        * (
                            std::abs(distance_squared)
                            + std::abs(improvement_squared)
                            + 1.0F
                        )
                    );
                    if (
                        distance_squared
                        > improvement_squared + rounding_guard
                    ) {
                        continue;
                    }
                    inout[output_index] = std::min(
                        inout[output_index],
                        segment_clearance(
                            sample_x,
                            sample_y,
                            segment,
                            occupied_radius[index]
                        )
                    );
                }
            }
        }
    }
    return 0;
}
