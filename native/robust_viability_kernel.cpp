#include <algorithm>
#include <cmath>
#include <cstdint>
#include <limits>
#include <memory>
#include <mutex>
#include <thread>
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

struct TransitionTable {
    double x_start;
    double x_step;
    int column_count;
    double y_start;
    double y_step;
    int row_count;
    std::vector<double> velocity_x;
    std::vector<double> velocity_y;
    int frames_per_layer;
    bool clamp_to_bounds;
    std::vector<std::int32_t> sample_indices;
    std::vector<float> sample_errors;

    bool matches(
        double requested_x_start,
        double requested_x_step,
        int requested_column_count,
        double requested_y_start,
        double requested_y_step,
        int requested_row_count,
        const double* requested_velocity_x,
        const double* requested_velocity_y,
        int requested_action_count,
        int requested_frames_per_layer,
        bool requested_clamp
    ) const {
        if (
            x_start != requested_x_start
            || x_step != requested_x_step
            || column_count != requested_column_count
            || y_start != requested_y_start
            || y_step != requested_y_step
            || row_count != requested_row_count
            || frames_per_layer != requested_frames_per_layer
            || clamp_to_bounds != requested_clamp
            || static_cast<int>(velocity_x.size())
                != requested_action_count
        ) {
            return false;
        }
        for (int index = 0; index < requested_action_count; ++index) {
            if (
                velocity_x[index] != requested_velocity_x[index]
                || velocity_y[index] != requested_velocity_y[index]
            ) {
                return false;
            }
        }
        return true;
    }
};

inline Sample sample_lattice(
    double x,
    double y,
    double x_start,
    double x_step,
    int column_count,
    double y_start,
    double y_step,
    int row_count,
    bool clamp_to_bounds
) {
    const double x_end = x_start + x_step * (column_count - 1);
    const double y_end = y_start + y_step * (row_count - 1);
    bool inside = (
        x >= x_start && x <= x_end && y >= y_start && y <= y_end
    );
    if (clamp_to_bounds) {
        x = std::min(x_end, std::max(x_start, x));
        y = std::min(y_end, std::max(y_start, y));
        inside = true;
    }
    int column = static_cast<int>(std::nearbyint((x - x_start) / x_step));
    int row = static_cast<int>(std::nearbyint((y - y_start) / y_step));
    column = std::min(column_count - 1, std::max(0, column));
    row = std::min(row_count - 1, std::max(0, row));
    const double center_x = x_start + column * x_step;
    const double center_y = y_start + row * y_step;
    return {
        row,
        column,
        std::hypot(x - center_x, y - center_y),
        inside,
    };
}

inline std::size_t transition_sample_index(
    int active,
    int selected,
    int delay,
    int state,
    int step,
    int action_count,
    int delay_slot_count,
    int state_count,
    int frames_per_layer
) {
    return (
        (
            (
                (
                    static_cast<std::size_t>(active) * action_count
                    + static_cast<std::size_t>(selected)
                )
                * delay_slot_count
                + static_cast<std::size_t>(delay)
            )
            * state_count
            + static_cast<std::size_t>(state)
        )
        * frames_per_layer
        + static_cast<std::size_t>(step)
    );
}

std::shared_ptr<const TransitionTable> transition_table(
    double x_start,
    double x_step,
    int column_count,
    double y_start,
    double y_step,
    int row_count,
    const double* velocity_x,
    const double* velocity_y,
    int action_count,
    int frames_per_layer,
    bool clamp_to_bounds
) {
    static std::mutex cache_mutex;
    static std::shared_ptr<const TransitionTable> cached;
    std::lock_guard<std::mutex> lock(cache_mutex);
    if (
        cached
        && cached->matches(
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
            clamp_to_bounds
        )
    ) {
        return cached;
    }

    auto table = std::make_shared<TransitionTable>();
    table->x_start = x_start;
    table->x_step = x_step;
    table->column_count = column_count;
    table->y_start = y_start;
    table->y_step = y_step;
    table->row_count = row_count;
    table->velocity_x.assign(velocity_x, velocity_x + action_count);
    table->velocity_y.assign(velocity_y, velocity_y + action_count);
    table->frames_per_layer = frames_per_layer;
    table->clamp_to_bounds = clamp_to_bounds;

    const int state_count = row_count * column_count;
    const int delay_slot_count = frames_per_layer + 1;
    const std::size_t sample_count = (
        static_cast<std::size_t>(action_count)
        * action_count
        * delay_slot_count
        * state_count
        * frames_per_layer
    );
    table->sample_indices.resize(sample_count);
    table->sample_errors.resize(sample_count);
    for (int active = 0; active < action_count; ++active) {
        for (int selected = 0; selected < action_count; ++selected) {
            for (int delay = 0; delay <= frames_per_layer; ++delay) {
                for (int row = 0; row < row_count; ++row) {
                    const double start_y = y_start + row * y_step;
                    for (int column = 0; column < column_count; ++column) {
                        const double start_x = x_start + column * x_step;
                        const int state = row * column_count + column;
                        for (
                            int step = 1;
                            step <= frames_per_layer;
                            ++step
                        ) {
                            const int active_frames = std::min(step, delay);
                            const int selected_frames = std::max(
                                step - delay,
                                0
                            );
                            const Sample sample = sample_lattice(
                                start_x
                                    + velocity_x[active] * active_frames
                                    + velocity_x[selected] * selected_frames,
                                start_y
                                    + velocity_y[active] * active_frames
                                    + velocity_y[selected] * selected_frames,
                                x_start,
                                x_step,
                                column_count,
                                y_start,
                                y_step,
                                row_count,
                                clamp_to_bounds
                            );
                            const std::size_t output_index = (
                                transition_sample_index(
                                    active,
                                    selected,
                                    delay,
                                    state,
                                    step - 1,
                                    action_count,
                                    delay_slot_count,
                                    state_count,
                                    frames_per_layer
                                )
                            );
                            table->sample_indices[output_index] = (
                                sample.inside
                                ? sample.row * column_count + sample.column
                                : -1
                            );
                            table->sample_errors[output_index] = (
                                static_cast<float>(sample.error)
                            );
                        }
                    }
                }
            }
        }
    }
    cached = table;
    return cached;
}

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

    for (int frame = 0; frame < frame_count; ++frame) {
        for (int row = 0; row < row_count; ++row) {
            const float sample_y = y_start + row * y_step;
            for (int column = 0; column < column_count; ++column) {
                const float sample_x = x_start + column * x_step;
                float best = clearance_cap;
                float best_positive_squared = clearance_cap * clearance_cap;
                for (int index = 0; index < aabb_count; ++index) {
                    const float uncertainty = (
                        aabb_base_uncertainty[index]
                        + frame * aabb_uncertainty_per_frame[index]
                    );
                    const float dx = std::abs(
                        sample_x
                        - (
                            aabb_x[index]
                            + frame * aabb_velocity_x[index]
                        )
                    ) - (
                        player_radius
                        + aabb_half_width[index]
                        + uncertainty
                    );
                    const float dy = std::abs(
                        sample_y
                        - (
                            aabb_y[index]
                            + frame * aabb_velocity_y[index]
                        )
                    ) - (
                        player_radius
                        + aabb_half_height[index]
                        + uncertainty
                    );
                    if (dx <= 0.0F && dy <= 0.0F) {
                        best = std::min(best, std::max(dx, dy));
                        continue;
                    }
                    if (best <= 0.0F) {
                        continue;
                    }
                    const float positive_x = std::max(dx, 0.0F);
                    const float positive_y = std::max(dy, 0.0F);
                    const float squared = (
                        positive_x * positive_x
                        + positive_y * positive_y
                    );
                    best_positive_squared = std::min(
                        best_positive_squared,
                        squared
                    );
                }
                if (best > 0.0F) {
                    best = std::sqrt(best_positive_squared);
                }
                for (int index = 0; index < segment_count; ++index) {
                    const SegmentGeometry& segment = segment_geometry[index];
                    const float clearance = segment_clearance(
                        sample_x,
                        sample_y,
                        segment,
                        player_radius
                        + segment_half_width[index]
                        + segment_base_uncertainty[index]
                        + frame * segment_uncertainty_per_frame[index]
                    );
                    best = std::min(best, clearance);
                }
                output[clearance_index(
                    frame,
                    row,
                    column,
                    row_count,
                    column_count
                )] = best;
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
                viable[state_index(
                    layer_count,
                    action,
                    row,
                    column,
                    action_count,
                    row_count,
                    column_count
                )] = (
                    clearance[clearance_index(
                        horizon_frame,
                        row,
                        column,
                        row_count,
                        column_count
                    )] > required_clearance
                );
            }
        }
    }

    const bool clamp = clamp_to_bounds != 0;
    const int state_count = row_count * column_count;
    const int delay_slot_count = frames_per_layer + 1;
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
                    const int state = row * column_count + column;
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
                                const std::size_t sample_offset = (
                                    transition_sample_index(
                                        active,
                                        selected,
                                        delay,
                                        state,
                                        step - 1,
                                        action_count,
                                        delay_slot_count,
                                        state_count,
                                        frames_per_layer
                                    )
                                );
                                terminal_state = transitions->sample_indices[
                                    sample_offset
                                ];
                                if (
                                    terminal_state < 0
                                    || clearance[clearance_index(
                                        start_frame + step,
                                        terminal_state / column_count,
                                        terminal_state % column_count,
                                        row_count,
                                        column_count
                                    )] - transitions->sample_errors[
                                        sample_offset
                                    ]
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
            }
        }
    }
    return 0;
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
    const int state_count = row_count * column_count;
    const int delay_slot_count = frames_per_layer + 1;
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
                    const int state = row * column_count + column;
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
                                const std::size_t sample_offset = (
                                    transition_sample_index(
                                        active,
                                        selected,
                                        delay,
                                        state,
                                        step - 1,
                                        action_count,
                                        delay_slot_count,
                                        state_count,
                                        frames_per_layer
                                    )
                                );
                                terminal_state = transitions->sample_indices[
                                    sample_offset
                                ];
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
                                    )] - transitions->sample_errors[
                                        sample_offset
                                    ]
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
    const int state_count = row_count * column_count;
    const int delay_slot_count = frames_per_layer + 1;
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
                                const std::size_t sample_offset = (
                                    transition_sample_index(
                                        active,
                                        selected,
                                        delay,
                                        state,
                                        step - 1,
                                        action_count,
                                        delay_slot_count,
                                        state_count,
                                        frames_per_layer
                                    )
                                );
                                terminal_state = transitions->sample_indices[
                                    sample_offset
                                ];
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
                                    )] - transitions->sample_errors[
                                        sample_offset
                                    ]
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
