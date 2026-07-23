#include <algorithm>
#include <cmath>
#include <cstdint>
#include <limits>
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

    struct SegmentGeometry {
        float start_x;
        float start_y;
        float vector_x;
        float vector_y;
        float length_squared;
    };
    std::vector<SegmentGeometry> segment_geometry(segment_count);
    for (int index = 0; index < segment_count; ++index) {
        const float cosine = std::cos(segment_angle[index]);
        const float sine = std::sin(segment_angle[index]);
        const float length = segment_head[index] - segment_tail[index];
        const float vector_x = cosine * length;
        const float vector_y = sine * length;
        segment_geometry[index] = {
            segment_origin_x[index] + cosine * segment_tail[index],
            segment_origin_y[index] + sine * segment_tail[index],
            vector_x,
            vector_y,
            vector_x * vector_x + vector_y * vector_y,
        };
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
                    float projection = 0.0F;
                    if (segment.length_squared > 1e-9F) {
                        projection = (
                            (sample_x - segment.start_x) * segment.vector_x
                            + (sample_y - segment.start_y) * segment.vector_y
                        ) / segment.length_squared;
                        projection = std::min(
                            1.0F,
                            std::max(0.0F, projection)
                        );
                    }
                    const float closest_x = (
                        segment.start_x + projection * segment.vector_x
                    );
                    const float closest_y = (
                        segment.start_y + projection * segment.vector_y
                    );
                    const float clearance = std::hypot(
                        sample_x - closest_x,
                        sample_y - closest_y
                    ) - (
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
    for (int layer = layer_count - 1; layer >= 0; --layer) {
        const int start_frame = layer * frames_per_layer;
        for (int active = 0; active < action_count; ++active) {
            for (int row = 0; row < row_count; ++row) {
                const double start_y = y_start + row * y_step;
                for (int column = 0; column < column_count; ++column) {
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
                    const double start_x = x_start + column * x_step;
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
                            Sample terminal{
                                row,
                                column,
                                0.0,
                                true,
                            };
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
                                terminal = sample_lattice(
                                    start_x
                                        + velocity_x[active] * active_frames
                                        + velocity_x[selected]
                                            * selected_frames,
                                    start_y
                                        + velocity_y[active] * active_frames
                                        + velocity_y[selected]
                                            * selected_frames,
                                    x_start,
                                    x_step,
                                    column_count,
                                    y_start,
                                    y_step,
                                    row_count,
                                    clamp
                                );
                                if (
                                    !terminal.inside
                                    || clearance[clearance_index(
                                        start_frame + step,
                                        terminal.row,
                                        terminal.column,
                                        row_count,
                                        column_count
                                    )] - terminal.error
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
                                    terminal.row,
                                    terminal.column,
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
