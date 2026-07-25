#include <algorithm>
#include <atomic>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <limits>
#include <memory>
#include <mutex>
#include <thread>
#include <unordered_map>
#include <vector>

#if defined(_WIN32)
#define TOUHOU_EXPORT extern "C" __declspec(dllexport)
#else
#define TOUHOU_EXPORT extern "C" __attribute__((visibility("default")))
#endif

namespace {

inline std::size_t state_index(
    int layer,
    int action,
    int row,
    int column,
    int action_count,
    int row_count,
    int column_count
) {
    return (
        (
            static_cast<std::size_t>(layer) * action_count
            + static_cast<std::size_t>(action)
        )
        * row_count
        + static_cast<std::size_t>(row)
    )
        * column_count
        + static_cast<std::size_t>(column);
}

inline std::size_t action_value_index(
    int layer,
    int active,
    int selected,
    int row,
    int column,
    int action_count,
    int row_count,
    int column_count
) {
    return (
        (
            (
                (
                    static_cast<std::size_t>(layer) * action_count
                    + static_cast<std::size_t>(active)
                )
                * action_count
                + static_cast<std::size_t>(selected)
            )
            * row_count
            + static_cast<std::size_t>(row)
        )
        * column_count
        + static_cast<std::size_t>(column)
    );
}

inline std::size_t clearance_index(
    int frame,
    int row,
    int column,
    int row_count,
    int column_count
) {
    return (
        static_cast<std::size_t>(frame) * row_count
        + static_cast<std::size_t>(row)
    )
        * column_count
        + static_cast<std::size_t>(column);
}

struct Sample {
    int row;
    int column;
    double error;
    bool inside;
};

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

#include "robust_transition_table.hpp"

}  // namespace

TOUHOU_EXPORT int touhou_clearance_volume_v1(
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

TOUHOU_EXPORT int touhou_segment_trajectory_clearance_v1(
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

TOUHOU_EXPORT int touhou_aabb_trajectory_clearance_v1(
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

TOUHOU_EXPORT int touhou_piecewise_aabb_clearance_v1(
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

static int robust_viability(
    const float* clearance,
    int frame_count,
    int row_count,
    int column_count,
    double x_start,
    double x_step,
    double y_start,
    double y_step,
    const double* velocity_x,
    const double* velocity_y,
    int action_count,
    const int* delay_frames,
    int delay_count,
    int frames_per_layer,
    float required_clearance,
    int clamp_to_bounds,
    const std::uint8_t* terminal_viable,
    std::uint8_t* viable,
    std::uint32_t* safe_action_masks
) {
    if (
        clearance == nullptr || velocity_x == nullptr
        || velocity_y == nullptr || delay_frames == nullptr
        || viable == nullptr || safe_action_masks == nullptr
    ) {
        return 1;
    }
    if (
        frame_count < 2 || row_count < 2 || column_count < 2
        || x_step <= 0.0 || y_step <= 0.0
        || action_count < 1 || action_count > 32
        || delay_count < 1 || frames_per_layer < 1
        || (frame_count - 1) % frames_per_layer != 0
    ) {
        return 2;
    }
    for (int index = 0; index < delay_count; ++index) {
        if (
            delay_frames[index] < 0
            || delay_frames[index] > frames_per_layer
            || (index > 0 && delay_frames[index - 1] >= delay_frames[index])
        ) {
            return 3;
        }
    }

    const int layer_count = (frame_count - 1) / frames_per_layer;
    const std::size_t layer_state_count = (
        static_cast<std::size_t>(action_count)
        * row_count
        * column_count
    );
    std::fill(
        viable,
        viable + static_cast<std::size_t>(layer_count + 1)
            * layer_state_count,
        std::uint8_t{0}
    );
    std::fill(
        safe_action_masks,
        safe_action_masks + static_cast<std::size_t>(layer_count)
            * layer_state_count,
        std::uint32_t{0}
    );

    const int horizon_frame = frame_count - 1;
    for (int action = 0; action < action_count; ++action) {
        for (int row = 0; row < row_count; ++row) {
            for (int column = 0; column < column_count; ++column) {
                const std::size_t output_index = state_index(
                    layer_count,
                    action,
                    row,
                    column,
                    action_count,
                    row_count,
                    column_count
                );
                const std::size_t terminal_index = state_index(
                    0,
                    action,
                    row,
                    column,
                    action_count,
                    row_count,
                    column_count
                );
                viable[output_index] = (
                    clearance[clearance_index(
                        horizon_frame,
                        row,
                        column,
                        row_count,
                        column_count
                    )] > required_clearance
                    && (
                        terminal_viable == nullptr
                        || terminal_viable[terminal_index] != 0
                    )
                );
            }
        }
    }

    const bool clamp = clamp_to_bounds != 0;
    const int state_count = row_count * column_count;
    const auto transitions = transition_table(
        x_start,
        x_step,
        column_count,
        y_start,
        y_step,
        row_count,
        velocity_x,
        velocity_y,
        action_count,
        frames_per_layer,
        clamp
    );
    const int layer_work = action_count * state_count;
    const unsigned hardware_threads = std::thread::hardware_concurrency();
    const int worker_count = std::max(
        1,
        std::min(
            4,
            static_cast<int>(
                hardware_threads == 0 ? 1 : hardware_threads
            )
        )
    );
    for (int layer = layer_count - 1; layer >= 0; --layer) {
        const int start_frame = layer * frames_per_layer;
        const auto solve_range = [&](int begin, int end) {
            for (int work_index = begin; work_index < end; ++work_index) {
                    const int active = work_index / state_count;
                    const int state = work_index % state_count;
                    const int row = state / column_count;
                    const int column = state % column_count;
                    if (
                        clearance[clearance_index(
                            start_frame,
                            row,
                            column,
                            row_count,
                            column_count
                        )] <= required_clearance
                    ) {
                        continue;
                    }
                    std::uint32_t mask = 0;
                    for (
                        int selected = 0;
                        selected < action_count;
                        ++selected
                    ) {
                        bool robust = true;
                        for (
                            int delay_index = 0;
                            delay_index < delay_count && robust;
                            ++delay_index
                        ) {
                            const int delay = delay_frames[delay_index];
                            std::int32_t terminal_state = -1;
                            for (
                                int step = 1;
                                step <= frames_per_layer;
                                ++step
                            ) {
                                const Sample sample = transition_sample(
                                    *transitions,
                                    active,
                                    selected,
                                    delay,
                                    row,
                                    column,
                                    step - 1,
                                    action_count
                                );
                                terminal_state = (
                                    sample.inside
                                    ? (
                                        sample.row * column_count
                                        + sample.column
                                    )
                                    : -1
                                );
                                if (
                                    terminal_state < 0
                                    || clearance[clearance_index(
                                        start_frame + step,
                                        terminal_state / column_count,
                                        terminal_state % column_count,
                                        row_count,
                                        column_count
                                    )] - static_cast<float>(sample.error)
                                        <= required_clearance
                                ) {
                                    robust = false;
                                    break;
                                }
                            }
                            if (
                                robust
                                && !viable[state_index(
                                    layer + 1,
                                    selected,
                                    terminal_state / column_count,
                                    terminal_state % column_count,
                                    action_count,
                                    row_count,
                                    column_count
                                )]
                            ) {
                                robust = false;
                            }
                        }
                        if (robust) {
                            mask |= std::uint32_t{1} << selected;
                        }
                    }
                    const std::size_t output_index = state_index(
                        layer,
                        active,
                        row,
                        column,
                        action_count,
                        row_count,
                        column_count
                    );
                    safe_action_masks[output_index] = mask;
                    viable[output_index] = mask != 0;
            }
        };
        if (worker_count == 1) {
            solve_range(0, layer_work);
            continue;
        }
        std::vector<std::thread> workers;
        workers.reserve(worker_count);
        for (int worker = 0; worker < worker_count; ++worker) {
            const int begin = layer_work * worker / worker_count;
            const int end = layer_work * (worker + 1) / worker_count;
            workers.emplace_back(solve_range, begin, end);
        }
        for (auto& worker : workers) {
            worker.join();
        }
    }
    return 0;
}

TOUHOU_EXPORT int touhou_robust_viability_v1(
    const float* clearance,
    int frame_count,
    int row_count,
    int column_count,
    double x_start,
    double x_step,
    double y_start,
    double y_step,
    const double* velocity_x,
    const double* velocity_y,
    int action_count,
    const int* delay_frames,
    int delay_count,
    int frames_per_layer,
    float required_clearance,
    int clamp_to_bounds,
    std::uint8_t* viable,
    std::uint32_t* safe_action_masks
) {
    return robust_viability(
        clearance,
        frame_count,
        row_count,
        column_count,
        x_start,
        x_step,
        y_start,
        y_step,
        velocity_x,
        velocity_y,
        action_count,
        delay_frames,
        delay_count,
        frames_per_layer,
        required_clearance,
        clamp_to_bounds,
        nullptr,
        viable,
        safe_action_masks
    );
}

TOUHOU_EXPORT int touhou_robust_viability_terminal_v1(
    const float* clearance,
    int frame_count,
    int row_count,
    int column_count,
    double x_start,
    double x_step,
    double y_start,
    double y_step,
    const double* velocity_x,
    const double* velocity_y,
    int action_count,
    const int* delay_frames,
    int delay_count,
    int frames_per_layer,
    float required_clearance,
    int clamp_to_bounds,
    const std::uint8_t* terminal_viable,
    std::uint8_t* viable,
    std::uint32_t* safe_action_masks
) {
    if (terminal_viable == nullptr) {
        return 1;
    }
    return robust_viability(
        clearance,
        frame_count,
        row_count,
        column_count,
        x_start,
        x_step,
        y_start,
        y_step,
        velocity_x,
        velocity_y,
        action_count,
        delay_frames,
        delay_count,
        frames_per_layer,
        required_clearance,
        clamp_to_bounds,
        terminal_viable,
        viable,
        safe_action_masks
    );
}

TOUHOU_EXPORT int touhou_robust_safety_value_v1(
    const float* clearance,
    int frame_count,
    int row_count,
    int column_count,
    double x_start,
    double x_step,
    double y_start,
    double y_step,
    const double* velocity_x,
    const double* velocity_y,
    int action_count,
    const int* delay_frames,
    int delay_count,
    int frames_per_layer,
    int clamp_to_bounds,
    float* state_values,
    float* action_values
) {
    if (
        clearance == nullptr || velocity_x == nullptr
        || velocity_y == nullptr || delay_frames == nullptr
        || state_values == nullptr || action_values == nullptr
    ) {
        return 1;
    }
    if (
        frame_count < 2 || row_count < 2 || column_count < 2
        || x_step <= 0.0 || y_step <= 0.0
        || action_count < 1 || action_count > 32
        || delay_count < 1 || frames_per_layer < 1
        || (frame_count - 1) % frames_per_layer != 0
    ) {
        return 2;
    }
    for (int index = 0; index < delay_count; ++index) {
        if (
            delay_frames[index] < 0
            || delay_frames[index] > frames_per_layer
            || (index > 0 && delay_frames[index - 1] >= delay_frames[index])
        ) {
            return 3;
        }
    }

    const int layer_count = (frame_count - 1) / frames_per_layer;
    const std::size_t layer_state_count = (
        static_cast<std::size_t>(action_count)
        * row_count
        * column_count
    );
    const float negative_infinity =
        -std::numeric_limits<float>::infinity();
    std::fill(
        state_values,
        state_values + static_cast<std::size_t>(layer_count + 1)
            * layer_state_count,
        negative_infinity
    );
    std::fill(
        action_values,
        action_values + static_cast<std::size_t>(layer_count)
            * action_count
            * action_count
            * row_count
            * column_count,
        negative_infinity
    );

    const int horizon_frame = frame_count - 1;
    for (int action = 0; action < action_count; ++action) {
        for (int row = 0; row < row_count; ++row) {
            for (int column = 0; column < column_count; ++column) {
                state_values[state_index(
                    layer_count,
                    action,
                    row,
                    column,
                    action_count,
                    row_count,
                    column_count
                )] = clearance[clearance_index(
                    horizon_frame,
                    row,
                    column,
                    row_count,
                    column_count
                )];
            }
        }
    }

    const bool clamp = clamp_to_bounds != 0;
    const auto transitions = transition_table(
        x_start,
        x_step,
        column_count,
        y_start,
        y_step,
        row_count,
        velocity_x,
        velocity_y,
        action_count,
        frames_per_layer,
        clamp
    );
    for (int layer = layer_count - 1; layer >= 0; --layer) {
        const int start_frame = layer * frames_per_layer;
        for (int active = 0; active < action_count; ++active) {
            for (int row = 0; row < row_count; ++row) {
                for (int column = 0; column < column_count; ++column) {
                    const float current_value = clearance[
                        clearance_index(
                            start_frame,
                            row,
                            column,
                            row_count,
                            column_count
                        )
                    ];
                    float best_value = negative_infinity;
                    for (
                        int selected = 0;
                        selected < action_count;
                        ++selected
                    ) {
                        float robust_value = current_value;
                        for (
                            int delay_index = 0;
                            delay_index < delay_count;
                            ++delay_index
                        ) {
                            const int delay = delay_frames[delay_index];
                            float branch_value = current_value;
                            std::int32_t terminal_state = -1;
                            for (
                                int step = 1;
                                step <= frames_per_layer;
                                ++step
                            ) {
                                const Sample sample = transition_sample(
                                    *transitions,
                                    active,
                                    selected,
                                    delay,
                                    row,
                                    column,
                                    step - 1,
                                    action_count
                                );
                                terminal_state = (
                                    sample.inside
                                    ? (
                                        sample.row * column_count
                                        + sample.column
                                    )
                                    : -1
                                );
                                if (terminal_state < 0) {
                                    branch_value = negative_infinity;
                                    break;
                                }
                                branch_value = std::min(
                                    branch_value,
                                    clearance[clearance_index(
                                        start_frame + step,
                                        terminal_state / column_count,
                                        terminal_state % column_count,
                                        row_count,
                                        column_count
                                    )] - static_cast<float>(sample.error)
                                );
                            }
                            if (terminal_state >= 0) {
                                branch_value = std::min(
                                    branch_value,
                                    state_values[state_index(
                                        layer + 1,
                                        selected,
                                        terminal_state / column_count,
                                        terminal_state % column_count,
                                        action_count,
                                        row_count,
                                        column_count
                                    )]
                                );
                            }
                            robust_value = std::min(
                                robust_value,
                                branch_value
                            );
                        }
                        action_values[action_value_index(
                            layer,
                            active,
                            selected,
                            row,
                            column,
                            action_count,
                            row_count,
                            column_count
                        )] = robust_value;
                        best_value = std::max(best_value, robust_value);
                    }
                    state_values[state_index(
                        layer,
                        active,
                        row,
                        column,
                        action_count,
                        row_count,
                        column_count
                    )] = best_value;
                }
            }
        }
    }
    return 0;
}

TOUHOU_EXPORT int touhou_robust_safety_policy_v1(
    const float* clearance,
    int frame_count,
    int row_count,
    int column_count,
    double x_start,
    double x_step,
    double y_start,
    double y_step,
    const double* velocity_x,
    const double* velocity_y,
    int action_count,
    const int* delay_frames,
    int delay_count,
    int frames_per_layer,
    int clamp_to_bounds,
    float* state_values,
    std::uint32_t* best_action_masks
) {
    if (
        clearance == nullptr || velocity_x == nullptr
        || velocity_y == nullptr || delay_frames == nullptr
        || state_values == nullptr || best_action_masks == nullptr
    ) {
        return 1;
    }
    if (
        frame_count < 2 || row_count < 2 || column_count < 2
        || x_step <= 0.0 || y_step <= 0.0
        || action_count < 1 || action_count > 32
        || delay_count < 1 || frames_per_layer < 1
        || (frame_count - 1) % frames_per_layer != 0
    ) {
        return 2;
    }
    for (int index = 0; index < delay_count; ++index) {
        if (
            delay_frames[index] < 0
            || delay_frames[index] > frames_per_layer
            || (index > 0 && delay_frames[index - 1] >= delay_frames[index])
        ) {
            return 3;
        }
    }

    const int layer_count = (frame_count - 1) / frames_per_layer;
    const std::size_t layer_state_count = (
        static_cast<std::size_t>(action_count)
        * row_count
        * column_count
    );
    const float negative_infinity =
        -std::numeric_limits<float>::infinity();
    std::fill(
        state_values,
        state_values + static_cast<std::size_t>(layer_count + 1)
            * layer_state_count,
        negative_infinity
    );
    std::fill(
        best_action_masks,
        best_action_masks + static_cast<std::size_t>(layer_count)
            * layer_state_count,
        std::uint32_t{0}
    );

    const int horizon_frame = frame_count - 1;
    for (int action = 0; action < action_count; ++action) {
        for (int row = 0; row < row_count; ++row) {
            for (int column = 0; column < column_count; ++column) {
                state_values[state_index(
                    layer_count,
                    action,
                    row,
                    column,
                    action_count,
                    row_count,
                    column_count
                )] = clearance[clearance_index(
                    horizon_frame,
                    row,
                    column,
                    row_count,
                    column_count
                )];
            }
        }
    }

    const bool clamp = clamp_to_bounds != 0;
    const auto transitions = transition_table(
        x_start,
        x_step,
        column_count,
        y_start,
        y_step,
        row_count,
        velocity_x,
        velocity_y,
        action_count,
        frames_per_layer,
        clamp
    );
    const int layer_work = action_count * row_count * column_count;
    const unsigned hardware_threads = std::thread::hardware_concurrency();
    const int worker_count = std::max(
        1,
        std::min(
            4,
            static_cast<int>(
                hardware_threads == 0 ? 1 : hardware_threads
            )
        )
    );
    for (int layer = layer_count - 1; layer >= 0; --layer) {
        const int start_frame = layer * frames_per_layer;
        const auto solve_range = [&](int begin, int end) {
            for (int work_index = begin; work_index < end; ++work_index) {
                const int active = (
                    work_index / (row_count * column_count)
                );
                const int state = (
                    work_index % (row_count * column_count)
                );
                const int row = state / column_count;
                const int column = state % column_count;
                    const float current_value = clearance[
                        clearance_index(
                            start_frame,
                            row,
                            column,
                            row_count,
                            column_count
                        )
                    ];
                    float best_value = negative_infinity;
                    std::uint32_t best_mask = 0;
                    for (
                        int selected_slot = 0;
                        selected_slot < action_count;
                        ++selected_slot
                    ) {
                        // Evaluate the active action first. Besides improving
                        // temporal stability on exact ties, it supplies a
                        // useful lower bound for max-min pruning.
                        const int selected = (
                            selected_slot == 0
                            ? active
                            : (
                                selected_slot <= active
                                ? selected_slot - 1
                                : selected_slot
                            )
                        );
                        float robust_value = current_value;
                        bool dominated = false;
                        for (
                            int delay_index = 0;
                            delay_index < delay_count;
                            ++delay_index
                        ) {
                            const int delay = delay_frames[delay_index];
                            float branch_value = current_value;
                            std::int32_t terminal_state = -1;
                            for (
                                int step = 1;
                                step <= frames_per_layer;
                                ++step
                            ) {
                                const Sample sample = transition_sample(
                                    *transitions,
                                    active,
                                    selected,
                                    delay,
                                    row,
                                    column,
                                    step - 1,
                                    action_count
                                );
                                terminal_state = (
                                    sample.inside
                                    ? (
                                        sample.row * column_count
                                        + sample.column
                                    )
                                    : -1
                                );
                                if (terminal_state < 0) {
                                    branch_value = negative_infinity;
                                    break;
                                }
                                branch_value = std::min(
                                    branch_value,
                                    clearance[clearance_index(
                                        start_frame + step,
                                        terminal_state / column_count,
                                        terminal_state % column_count,
                                        row_count,
                                        column_count
                                    )] - static_cast<float>(sample.error)
                                );
                                if (branch_value < best_value) {
                                    dominated = true;
                                    break;
                                }
                            }
                            if (!dominated && terminal_state >= 0) {
                                branch_value = std::min(
                                    branch_value,
                                    state_values[state_index(
                                        layer + 1,
                                        selected,
                                        terminal_state / column_count,
                                        terminal_state % column_count,
                                        action_count,
                                        row_count,
                                        column_count
                                    )]
                                );
                            }
                            robust_value = std::min(
                                robust_value,
                                branch_value
                            );
                            if (robust_value < best_value) {
                                dominated = true;
                            }
                            if (dominated) {
                                break;
                            }
                        }
                        if (dominated) {
                            continue;
                        }
                        const std::uint32_t action_bit = (
                            std::uint32_t{1} << selected
                        );
                        if (robust_value > best_value) {
                            best_value = robust_value;
                            best_mask = action_bit;
                        } else if (robust_value == best_value) {
                            best_mask |= action_bit;
                        }
                    }
                    const std::size_t output_index = state_index(
                        layer,
                        active,
                        row,
                        column,
                        action_count,
                        row_count,
                        column_count
                    );
                    state_values[output_index] = best_value;
                    best_action_masks[output_index] = best_mask;
            }
        };
        if (worker_count == 1) {
            solve_range(0, layer_work);
            continue;
        }
        std::vector<std::thread> workers;
        workers.reserve(worker_count);
        for (int worker = 0; worker < worker_count; ++worker) {
            const int begin = layer_work * worker / worker_count;
            const int end = layer_work * (worker + 1) / worker_count;
            workers.emplace_back(solve_range, begin, end);
        }
        for (auto& worker : workers) {
            worker.join();
        }
    }
    return 0;
}

TOUHOU_EXPORT int touhou_robust_survival_viability_v1(
    const float* clearance,
    int frame_count,
    int row_count,
    int column_count,
    double x_start,
    double x_step,
    double y_start,
    double y_step,
    const double* velocity_x,
    const double* velocity_y,
    int action_count,
    const int* delay_frames,
    int delay_count,
    int frames_per_layer,
    float required_clearance,
    int clamp_to_bounds,
    std::uint16_t* state_survival_frames,
    float* state_bottleneck_margins,
    std::uint32_t* best_action_masks,
    std::uint8_t* viable,
    std::uint32_t* safe_action_masks
) {
    if (
        clearance == nullptr || velocity_x == nullptr
        || velocity_y == nullptr || delay_frames == nullptr
        || state_survival_frames == nullptr
        || state_bottleneck_margins == nullptr
        || best_action_masks == nullptr || viable == nullptr
        || safe_action_masks == nullptr
    ) {
        return 1;
    }
    if (
        frame_count < 2 || row_count < 2 || column_count < 2
        || x_step <= 0.0 || y_step <= 0.0
        || action_count < 1 || action_count > 32
        || delay_count < 1 || frames_per_layer < 1
        || (frame_count - 1) % frames_per_layer != 0
        || frame_count - 1 > std::numeric_limits<std::uint16_t>::max()
    ) {
        return 2;
    }
    for (int index = 0; index < delay_count; ++index) {
        if (
            delay_frames[index] < 0
            || delay_frames[index] > frames_per_layer
            || (index > 0 && delay_frames[index - 1] >= delay_frames[index])
        ) {
            return 3;
        }
    }

    const int layer_count = (frame_count - 1) / frames_per_layer;
    const std::size_t layer_state_count = (
        static_cast<std::size_t>(action_count)
        * row_count
        * column_count
    );
    const std::size_t state_output_count = (
        static_cast<std::size_t>(layer_count + 1) * layer_state_count
    );
    const std::size_t action_output_count = (
        static_cast<std::size_t>(layer_count) * layer_state_count
    );
    std::fill(
        state_survival_frames,
        state_survival_frames + state_output_count,
        std::uint16_t{0}
    );
    std::fill(
        state_bottleneck_margins,
        state_bottleneck_margins + state_output_count,
        -std::numeric_limits<float>::infinity()
    );
    std::fill(
        best_action_masks,
        best_action_masks + action_output_count,
        std::uint32_t{0}
    );
    std::fill(
        viable,
        viable + state_output_count,
        std::uint8_t{0}
    );
    std::fill(
        safe_action_masks,
        safe_action_masks + action_output_count,
        std::uint32_t{0}
    );

    const int horizon_frame = frame_count - 1;
    for (int action = 0; action < action_count; ++action) {
        for (int row = 0; row < row_count; ++row) {
            for (int column = 0; column < column_count; ++column) {
                const std::size_t output_index = state_index(
                    layer_count,
                    action,
                    row,
                    column,
                    action_count,
                    row_count,
                    column_count
                );
                const float margin = clearance[clearance_index(
                    horizon_frame,
                    row,
                    column,
                    row_count,
                    column_count
                )] - required_clearance;
                state_bottleneck_margins[output_index] = margin;
                viable[output_index] = margin > 0.0F;
            }
        }
    }

    const bool clamp = clamp_to_bounds != 0;
    const int state_count = row_count * column_count;
    const auto transitions = transition_table(
        x_start,
        x_step,
        column_count,
        y_start,
        y_step,
        row_count,
        velocity_x,
        velocity_y,
        action_count,
        frames_per_layer,
        clamp
    );
    const int layer_work = action_count * state_count;
    const unsigned hardware_threads = std::thread::hardware_concurrency();
    const int worker_count = std::max(
        1,
        std::min(
            4,
            static_cast<int>(
                hardware_threads == 0 ? 1 : hardware_threads
            )
        )
    );

    const auto label_less = [](
        std::uint16_t left_frames,
        float left_margin,
        std::uint16_t right_frames,
        float right_margin
    ) {
        return (
            left_frames < right_frames
            || (
                left_frames == right_frames
                && left_margin < right_margin
            )
        );
    };
    const std::uint32_t every_action_mask = (
        action_count == 32
        ? std::numeric_limits<std::uint32_t>::max()
        : (std::uint32_t{1} << action_count) - 1
    );

    for (int layer = layer_count - 1; layer >= 0; --layer) {
        const int start_frame = layer * frames_per_layer;
        const std::uint16_t remaining_frames = static_cast<std::uint16_t>(
            (layer_count - layer) * frames_per_layer
        );
        const auto solve_range = [&](int begin, int end) {
            for (int work_index = begin; work_index < end; ++work_index) {
                const int active = work_index / state_count;
                const int state = work_index % state_count;
                const int row = state / column_count;
                const int column = state % column_count;
                const std::size_t output_index = state_index(
                    layer,
                    active,
                    row,
                    column,
                    action_count,
                    row_count,
                    column_count
                );
                const float current_margin = clearance[clearance_index(
                    start_frame,
                    row,
                    column,
                    row_count,
                    column_count
                )] - required_clearance;
                if (current_margin <= 0.0F) {
                    state_bottleneck_margins[output_index] = current_margin;
                    best_action_masks[output_index] = every_action_mask;
                    continue;
                }

                std::uint16_t best_frames = 0;
                float best_margin = -std::numeric_limits<float>::infinity();
                std::uint32_t best_mask = 0;
                std::uint32_t winning_mask = 0;
                for (int selected = 0; selected < action_count; ++selected) {
                    std::uint16_t robust_frames =
                        std::numeric_limits<std::uint16_t>::max();
                    float robust_margin =
                        std::numeric_limits<float>::infinity();
                    for (
                        int delay_index = 0;
                        delay_index < delay_count;
                        ++delay_index
                    ) {
                        const int delay = delay_frames[delay_index];
                        std::uint16_t branch_frames = 0;
                        float branch_margin = current_margin;
                        std::int32_t terminal_state = -1;
                        bool failed = false;
                        for (
                            int step = 1;
                            step <= frames_per_layer;
                            ++step
                        ) {
                            const Sample sample = transition_sample(
                                *transitions,
                                active,
                                selected,
                                delay,
                                row,
                                column,
                                step - 1,
                                action_count
                            );
                            terminal_state = (
                                sample.inside
                                ? sample.row * column_count + sample.column
                                : -1
                            );
                            if (terminal_state < 0) {
                                branch_frames = static_cast<std::uint16_t>(
                                    step - 1
                                );
                                branch_margin =
                                    -std::numeric_limits<float>::infinity();
                                failed = true;
                                break;
                            }
                            const float margin = (
                                clearance[clearance_index(
                                    start_frame + step,
                                    terminal_state / column_count,
                                    terminal_state % column_count,
                                    row_count,
                                    column_count
                                )]
                                - static_cast<float>(sample.error)
                                - required_clearance
                            );
                            branch_margin = std::min(branch_margin, margin);
                            if (margin <= 0.0F) {
                                branch_frames = static_cast<std::uint16_t>(
                                    step - 1
                                );
                                failed = true;
                                break;
                            }
                        }
                        if (!failed) {
                            const std::size_t successor_index = state_index(
                                layer + 1,
                                selected,
                                terminal_state / column_count,
                                terminal_state % column_count,
                                action_count,
                                row_count,
                                column_count
                            );
                            branch_frames = static_cast<std::uint16_t>(
                                frames_per_layer
                                + state_survival_frames[successor_index]
                            );
                            branch_margin = std::min(
                                branch_margin,
                                state_bottleneck_margins[successor_index]
                            );
                        }
                        if (
                            label_less(
                                branch_frames,
                                branch_margin,
                                robust_frames,
                                robust_margin
                            )
                        ) {
                            robust_frames = branch_frames;
                            robust_margin = branch_margin;
                        }
                    }
                    const std::uint32_t action_bit = (
                        std::uint32_t{1} << selected
                    );
                    if (
                        robust_frames == remaining_frames
                        && robust_margin > 0.0F
                    ) {
                        winning_mask |= action_bit;
                    }
                    if (
                        best_mask == 0
                        || label_less(
                            best_frames,
                            best_margin,
                            robust_frames,
                            robust_margin
                        )
                    ) {
                        best_frames = robust_frames;
                        best_margin = robust_margin;
                        best_mask = action_bit;
                    } else if (
                        best_frames == robust_frames
                        && best_margin == robust_margin
                    ) {
                        best_mask |= action_bit;
                    }
                }
                state_survival_frames[output_index] = best_frames;
                state_bottleneck_margins[output_index] = best_margin;
                best_action_masks[output_index] = best_mask;
                safe_action_masks[output_index] = winning_mask;
                viable[output_index] = winning_mask != 0;
            }
        };
        if (worker_count == 1) {
            solve_range(0, layer_work);
            continue;
        }
        std::vector<std::thread> workers;
        workers.reserve(worker_count);
        for (int worker = 0; worker < worker_count; ++worker) {
            const int begin = layer_work * worker / worker_count;
            const int end = layer_work * (worker + 1) / worker_count;
            workers.emplace_back(solve_range, begin, end);
        }
        for (auto& worker : workers) {
            worker.join();
        }
    }
    return 0;
}

TOUHOU_EXPORT int touhou_query_local_survival_v1(
    const float* clearance,
    int frame_count,
    int row_count,
    int column_count,
    double x_start,
    double x_step,
    double y_start,
    double y_step,
    const double* velocity_x,
    const double* velocity_y,
    int action_count,
    const int* delay_frames,
    int delay_count,
    int decision_frames,
    float required_clearance,
    int clamp_to_bounds,
    int start_frame,
    int start_row,
    int start_column,
    int observed_action,
    int pending_action,
    const int* pending_remaining_frames,
    int pending_remaining_count,
    std::uint16_t* output_state_frames,
    float* output_state_margin,
    std::uint16_t* output_action_frames,
    float* output_action_margins,
    std::uint32_t* output_best_action_mask,
    std::uint64_t* output_evaluated_state_count
) {
    if (
        clearance == nullptr || velocity_x == nullptr
        || velocity_y == nullptr || delay_frames == nullptr
        || output_state_frames == nullptr || output_state_margin == nullptr
        || output_action_frames == nullptr
        || output_action_margins == nullptr
        || output_best_action_mask == nullptr
        || output_evaluated_state_count == nullptr
    ) {
        return 1;
    }
    if (
        frame_count < 2 || row_count < 2 || column_count < 2
        || x_step <= 0.0 || y_step <= 0.0
        || action_count < 1 || action_count > 32
        || delay_count < 1 || decision_frames < 1
        || start_frame < 0 || start_frame >= frame_count
        || start_row < 0 || start_row >= row_count
        || start_column < 0 || start_column >= column_count
        || observed_action < 0 || observed_action >= action_count
        || pending_action < -1 || pending_action >= action_count
        || frame_count - 1 > std::numeric_limits<std::uint16_t>::max()
    ) {
        return 2;
    }
    for (int index = 0; index < delay_count; ++index) {
        if (
            delay_frames[index] < 0
            || delay_frames[index] > frame_count - 1
            || (index > 0 && delay_frames[index - 1] >= delay_frames[index])
        ) {
            return 3;
        }
    }
    if (
        (pending_action < 0 && pending_remaining_count != 0)
        || (
            pending_action >= 0
            && (
                pending_remaining_frames == nullptr
                || pending_remaining_count < 1
            )
        )
    ) {
        return 4;
    }
    for (int index = 0; index < pending_remaining_count; ++index) {
        if (
            pending_remaining_frames[index] <= 0
            || pending_remaining_frames[index] > frame_count - 1
            || (
                index > 0
                && pending_remaining_frames[index - 1]
                    >= pending_remaining_frames[index]
            )
        ) {
            return 5;
        }
    }

    struct Label {
        std::uint16_t frames;
        float margin;
    };
    const auto label_less = [](
        const Label& left,
        const Label& right
    ) {
        return (
            left.frames < right.frames
            || (
                left.frames == right.frames
                && left.margin < right.margin
            )
        );
    };
    const auto label_equal = [](
        const Label& left,
        const Label& right
    ) {
        return left.frames == right.frames && left.margin == right.margin;
    };
    struct State {
        int frame;
        int active;
        int pending;
        int pending_remaining;
        int row;
        int column;

        bool operator==(const State& other) const {
            return (
                frame == other.frame
                && active == other.active
                && pending == other.pending
                && pending_remaining == other.pending_remaining
                && row == other.row
                && column == other.column
            );
        }
    };
    struct StateHash {
        std::size_t operator()(const State& state) const {
            std::size_t value = static_cast<std::size_t>(state.frame);
            const auto mix = [&value](int item) {
                value ^= (
                    static_cast<std::size_t>(item + 2)
                    + 0x9e3779b9U
                    + (value << 6)
                    + (value >> 2)
                );
            };
            mix(state.active);
            mix(state.pending);
            mix(state.pending_remaining);
            mix(state.row);
            mix(state.column);
            return value;
        }
    };
    struct Node {
        Label state;
        std::vector<Label> actions;
    };

    const int horizon_frame = frame_count - 1;
    const bool clamp = clamp_to_bounds != 0;
    std::unordered_map<State, Node, StateHash> memo;
    const auto solve = [&](const auto& self, const State& state) -> Node {
        const auto found = memo.find(state);
        if (found != memo.end()) {
            return found->second;
        }
        const float current_margin = (
            clearance[clearance_index(
                state.frame,
                state.row,
                state.column,
                row_count,
                column_count
            )] - required_clearance
        );
        if (state.frame == horizon_frame || current_margin <= 0.0F) {
            const Label label{0, current_margin};
            Node terminal{
                label,
                std::vector<Label>(action_count, label),
            };
            memo.emplace(state, terminal);
            return terminal;
        }

        const int step_count = std::min(
            decision_frames,
            horizon_frame - state.frame
        );
        const double state_x = x_start + state.column * x_step;
        const double state_y = y_start + state.row * y_step;
        std::vector<Label> action_labels;
        action_labels.reserve(action_count);
        for (int selected = 0; selected < action_count; ++selected) {
            Label robust{
                std::numeric_limits<std::uint16_t>::max(),
                std::numeric_limits<float>::infinity(),
            };
            for (int delay_index = 0; delay_index < delay_count; ++delay_index) {
                const int delay = delay_frames[delay_index];
                Label branch{0, current_margin};
                Sample terminal{-1, -1, 0.0, false};
                double displacement_x = 0.0;
                double displacement_y = 0.0;
                bool failed = false;
                for (int step = 1; step <= step_count; ++step) {
                    int motion = state.active;
                    if (step > delay) {
                        motion = selected;
                    } else if (
                        state.pending >= 0
                        && step > state.pending_remaining
                    ) {
                        motion = state.pending;
                    }
                    displacement_x += velocity_x[motion];
                    displacement_y += velocity_y[motion];
                    terminal = sample_lattice(
                        state_x + displacement_x,
                        state_y + displacement_y,
                        x_start,
                        x_step,
                        column_count,
                        y_start,
                        y_step,
                        row_count,
                        clamp
                    );
                    if (!terminal.inside) {
                        branch.frames = static_cast<std::uint16_t>(step - 1);
                        branch.margin =
                            -std::numeric_limits<float>::infinity();
                        failed = true;
                        break;
                    }
                    const float margin = (
                        clearance[clearance_index(
                            state.frame + step,
                            terminal.row,
                            terminal.column,
                            row_count,
                            column_count
                        )]
                        - static_cast<float>(terminal.error)
                        - required_clearance
                    );
                    branch.margin = std::min(branch.margin, margin);
                    if (margin <= 0.0F) {
                        branch.frames = static_cast<std::uint16_t>(step - 1);
                        failed = true;
                        break;
                    }
                }
                if (!failed) {
                    int successor_active = state.active;
                    int successor_pending = selected;
                    int successor_remaining = delay - step_count;
                    if (delay < step_count || successor_remaining == 0) {
                        successor_active = selected;
                        successor_pending = -1;
                        successor_remaining = 0;
                    } else if (
                        state.pending >= 0
                        && state.pending_remaining <= step_count
                    ) {
                        successor_active = state.pending;
                    }
                    const Node successor = self(
                        self,
                        State{
                            state.frame + step_count,
                            successor_active,
                            successor_pending,
                            successor_remaining,
                            terminal.row,
                            terminal.column,
                        }
                    );
                    branch.frames = static_cast<std::uint16_t>(
                        step_count + successor.state.frames
                    );
                    branch.margin = std::min(
                        branch.margin,
                        successor.state.margin
                    );
                }
                if (label_less(branch, robust)) {
                    robust = branch;
                }
            }
            action_labels.push_back(robust);
        }
        Label best = action_labels.front();
        for (int action = 1; action < action_count; ++action) {
            if (label_less(best, action_labels[action])) {
                best = action_labels[action];
            }
        }
        Node result{best, std::move(action_labels)};
        memo.emplace(state, result);
        return result;
    };

    std::vector<Node> roots;
    if (pending_action < 0) {
        roots.push_back(
            solve(
                solve,
                State{
                    start_frame,
                    observed_action,
                    -1,
                    0,
                    start_row,
                    start_column,
                }
            )
        );
    } else {
        roots.reserve(pending_remaining_count);
        for (int index = 0; index < pending_remaining_count; ++index) {
            roots.push_back(
                solve(
                    solve,
                    State{
                        start_frame,
                        observed_action,
                        pending_action,
                        pending_remaining_frames[index],
                        start_row,
                        start_column,
                    }
                )
            );
        }
    }

    std::uint32_t best_mask = 0;
    Label state_best{0, -std::numeric_limits<float>::infinity()};
    for (int action = 0; action < action_count; ++action) {
        Label robust = roots.front().actions[action];
        for (std::size_t root = 1; root < roots.size(); ++root) {
            if (label_less(roots[root].actions[action], robust)) {
                robust = roots[root].actions[action];
            }
        }
        output_action_frames[action] = robust.frames;
        output_action_margins[action] = robust.margin;
        if (action == 0 || label_less(state_best, robust)) {
            state_best = robust;
            best_mask = std::uint32_t{1} << action;
        } else if (label_equal(state_best, robust)) {
            best_mask |= std::uint32_t{1} << action;
        }
    }
    *output_state_frames = state_best.frames;
    *output_state_margin = state_best.margin;
    *output_best_action_mask = best_mask;
    *output_evaluated_state_count = static_cast<std::uint64_t>(memo.size());
    return 0;
}

#include "pipeline_survival_workspace.hpp"

TOUHOU_EXPORT int touhou_losing_survival_labels_v1(
    const float* clearance,
    int frame_count,
    int row_count,
    int column_count,
    double x_start,
    double x_step,
    double y_start,
    double y_step,
    const double* velocity_x,
    const double* velocity_y,
    int action_count,
    const int* delay_frames,
    int delay_count,
    int frames_per_layer,
    float required_clearance,
    int clamp_to_bounds,
    int requested_worker_count,
    const std::uint8_t* viable,
    const std::uint32_t* safe_action_masks,
    std::uint16_t* state_survival_frames,
    float* state_bottleneck_margins,
    std::uint32_t* best_action_masks
) {
    if (
        clearance == nullptr || velocity_x == nullptr
        || velocity_y == nullptr || delay_frames == nullptr
        || viable == nullptr || safe_action_masks == nullptr
        || state_survival_frames == nullptr
        || state_bottleneck_margins == nullptr
        || best_action_masks == nullptr
    ) {
        return 1;
    }
    if (
        frame_count < 2 || row_count < 2 || column_count < 2
        || x_step <= 0.0 || y_step <= 0.0
        || action_count < 1 || action_count > 32
        || delay_count < 1 || frames_per_layer < 1
        || requested_worker_count < 1 || requested_worker_count > 4
        || (frame_count - 1) % frames_per_layer != 0
        || frame_count - 1 > std::numeric_limits<std::uint16_t>::max()
    ) {
        return 2;
    }
    for (int index = 0; index < delay_count; ++index) {
        if (
            delay_frames[index] < 0
            || delay_frames[index] > frames_per_layer
            || (index > 0 && delay_frames[index - 1] >= delay_frames[index])
        ) {
            return 3;
        }
    }

    const int layer_count = (frame_count - 1) / frames_per_layer;
    const std::size_t layer_state_count = (
        static_cast<std::size_t>(action_count)
        * row_count
        * column_count
    );
    const std::size_t state_output_count = (
        static_cast<std::size_t>(layer_count + 1) * layer_state_count
    );
    const std::size_t action_output_count = (
        static_cast<std::size_t>(layer_count) * layer_state_count
    );
    std::fill(
        state_survival_frames,
        state_survival_frames + state_output_count,
        std::uint16_t{0}
    );
    std::fill(
        state_bottleneck_margins,
        state_bottleneck_margins + state_output_count,
        -std::numeric_limits<float>::infinity()
    );
    std::fill(
        best_action_masks,
        best_action_masks + action_output_count,
        std::uint32_t{0}
    );

    const int horizon_frame = frame_count - 1;
    for (int action = 0; action < action_count; ++action) {
        for (int row = 0; row < row_count; ++row) {
            for (int column = 0; column < column_count; ++column) {
                const std::size_t output_index = state_index(
                    layer_count,
                    action,
                    row,
                    column,
                    action_count,
                    row_count,
                    column_count
                );
                state_bottleneck_margins[output_index] = (
                    clearance[clearance_index(
                        horizon_frame,
                        row,
                        column,
                        row_count,
                        column_count
                    )] - required_clearance
                );
            }
        }
    }

    const bool clamp = clamp_to_bounds != 0;
    const int state_count = row_count * column_count;
    const auto transitions = transition_table(
        x_start,
        x_step,
        column_count,
        y_start,
        y_step,
        row_count,
        velocity_x,
        velocity_y,
        action_count,
        frames_per_layer,
        clamp
    );
    const int layer_work = action_count * state_count;
    const unsigned hardware_threads = std::thread::hardware_concurrency();
    const int worker_count = std::max(
        1,
        std::min(
            requested_worker_count,
            static_cast<int>(
                hardware_threads == 0 ? 1 : hardware_threads
            )
        )
    );
    const auto label_less = [](
        std::uint16_t left_frames,
        float left_margin,
        std::uint16_t right_frames,
        float right_margin
    ) {
        return (
            left_frames < right_frames
            || (
                left_frames == right_frames
                && left_margin < right_margin
            )
        );
    };
    const std::uint32_t every_action_mask = (
        action_count == 32
        ? std::numeric_limits<std::uint32_t>::max()
        : (std::uint32_t{1} << action_count) - 1
    );

    for (int layer = layer_count - 1; layer >= 0; --layer) {
        const int start_frame = layer * frames_per_layer;
        const std::uint16_t remaining_frames = static_cast<std::uint16_t>(
            (layer_count - layer) * frames_per_layer
        );
        const auto solve_range = [&](int begin, int end) {
            for (int work_index = begin; work_index < end; ++work_index) {
                const int active = work_index / state_count;
                const int state = work_index % state_count;
                const int row = state / column_count;
                const int column = state % column_count;
                const std::size_t output_index = state_index(
                    layer,
                    active,
                    row,
                    column,
                    action_count,
                    row_count,
                    column_count
                );
                if (viable[output_index] != 0) {
                    state_survival_frames[output_index] = remaining_frames;
                    state_bottleneck_margins[output_index] =
                        std::numeric_limits<float>::infinity();
                    best_action_masks[output_index] =
                        safe_action_masks[output_index];
                    continue;
                }
                const float current_margin = clearance[clearance_index(
                    start_frame,
                    row,
                    column,
                    row_count,
                    column_count
                )] - required_clearance;
                if (current_margin <= 0.0F) {
                    state_bottleneck_margins[output_index] = current_margin;
                    best_action_masks[output_index] = every_action_mask;
                    continue;
                }

                std::uint16_t best_frames = 0;
                float best_margin = -std::numeric_limits<float>::infinity();
                std::uint32_t best_mask = 0;
                for (int selected = 0; selected < action_count; ++selected) {
                    std::uint16_t robust_frames =
                        std::numeric_limits<std::uint16_t>::max();
                    float robust_margin =
                        std::numeric_limits<float>::infinity();
                    for (
                        int delay_index = 0;
                        delay_index < delay_count;
                        ++delay_index
                    ) {
                        const int delay = delay_frames[delay_index];
                        std::uint16_t branch_frames = 0;
                        float branch_margin = current_margin;
                        std::int32_t terminal_state = -1;
                        bool failed = false;
                        for (
                            int step = 1;
                            step <= frames_per_layer;
                            ++step
                        ) {
                            const Sample sample = transition_sample(
                                *transitions,
                                active,
                                selected,
                                delay,
                                row,
                                column,
                                step - 1,
                                action_count
                            );
                            terminal_state = (
                                sample.inside
                                ? sample.row * column_count + sample.column
                                : -1
                            );
                            if (terminal_state < 0) {
                                branch_frames = static_cast<std::uint16_t>(
                                    step - 1
                                );
                                branch_margin =
                                    -std::numeric_limits<float>::infinity();
                                failed = true;
                                break;
                            }
                            const float margin = (
                                clearance[clearance_index(
                                    start_frame + step,
                                    terminal_state / column_count,
                                    terminal_state % column_count,
                                    row_count,
                                    column_count
                                )]
                                - static_cast<float>(sample.error)
                                - required_clearance
                            );
                            branch_margin = std::min(branch_margin, margin);
                            if (margin <= 0.0F) {
                                branch_frames = static_cast<std::uint16_t>(
                                    step - 1
                                );
                                failed = true;
                                break;
                            }
                        }
                        if (!failed) {
                            const std::size_t successor_index = state_index(
                                layer + 1,
                                selected,
                                terminal_state / column_count,
                                terminal_state % column_count,
                                action_count,
                                row_count,
                                column_count
                            );
                            branch_frames = static_cast<std::uint16_t>(
                                frames_per_layer
                                + state_survival_frames[successor_index]
                            );
                            branch_margin = std::min(
                                branch_margin,
                                state_bottleneck_margins[successor_index]
                            );
                        }
                        if (
                            label_less(
                                branch_frames,
                                branch_margin,
                                robust_frames,
                                robust_margin
                            )
                        ) {
                            robust_frames = branch_frames;
                            robust_margin = branch_margin;
                        }
                    }
                    const std::uint32_t action_bit = (
                        std::uint32_t{1} << selected
                    );
                    if (
                        best_mask == 0
                        || label_less(
                            best_frames,
                            best_margin,
                            robust_frames,
                            robust_margin
                        )
                    ) {
                        best_frames = robust_frames;
                        best_margin = robust_margin;
                        best_mask = action_bit;
                    } else if (
                        best_frames == robust_frames
                        && best_margin == robust_margin
                    ) {
                        best_mask |= action_bit;
                    }
                }
                state_survival_frames[output_index] = best_frames;
                state_bottleneck_margins[output_index] = best_margin;
                best_action_masks[output_index] = best_mask;
            }
        };
        if (worker_count == 1) {
            solve_range(0, layer_work);
            continue;
        }
        std::vector<std::thread> workers;
        workers.reserve(worker_count);
        for (int worker = 0; worker < worker_count; ++worker) {
            const int begin = layer_work * worker / worker_count;
            const int end = layer_work * (worker + 1) / worker_count;
            workers.emplace_back(solve_range, begin, end);
        }
        for (auto& worker : workers) {
            worker.join();
        }
    }
    return 0;
}
