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

namespace {

struct SegmentGeometry {
    float start_x;
    float start_y;
    float vector_x;
    float vector_y;
    float length_squared;
    float min_x;
    float max_x;
    float min_y;
    float max_y;
};

inline SegmentGeometry segment_geometry(
    float origin_x,
    float origin_y,
    float angle,
    float tail,
    float head
) {
    const float cosine = std::cos(angle);
    const float sine = std::sin(angle);
    const float length = head - tail;
    const float vector_x = cosine * length;
    const float vector_y = sine * length;
    const float start_x = origin_x + cosine * tail;
    const float start_y = origin_y + sine * tail;
    const float end_x = start_x + vector_x;
    const float end_y = start_y + vector_y;
    return {
        start_x,
        start_y,
        vector_x,
        vector_y,
        vector_x * vector_x + vector_y * vector_y,
        std::min(start_x, end_x),
        std::max(start_x, end_x),
        std::min(start_y, end_y),
        std::max(start_y, end_y),
    };
}

inline float segment_clearance(
    float sample_x,
    float sample_y,
    const SegmentGeometry& segment,
    float occupied_radius
) {
    float projection = 0.0F;
    if (segment.length_squared > 1e-9F) {
        projection = (
            (sample_x - segment.start_x) * segment.vector_x
            + (sample_y - segment.start_y) * segment.vector_y
        ) / segment.length_squared;
        projection = std::min(1.0F, std::max(0.0F, projection));
    }
    const float closest_x = segment.start_x + projection * segment.vector_x;
    const float closest_y = segment.start_y + projection * segment.vector_y;
    return std::hypot(
        sample_x - closest_x,
        sample_y - closest_y
    ) - occupied_radius;
}

inline float segment_distance_squared(
    float sample_x,
    float sample_y,
    const SegmentGeometry& segment
) {
    float projection = 0.0F;
    if (segment.length_squared > 1e-9F) {
        projection = (
            (sample_x - segment.start_x) * segment.vector_x
            + (sample_y - segment.start_y) * segment.vector_y
        ) / segment.length_squared;
        projection = std::min(1.0F, std::max(0.0F, projection));
    }
    const float delta_x = (
        sample_x - (segment.start_x + projection * segment.vector_x)
    );
    const float delta_y = (
        sample_y - (segment.start_y + projection * segment.vector_y)
    );
    return delta_x * delta_x + delta_y * delta_y;
}

}  // namespace

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
