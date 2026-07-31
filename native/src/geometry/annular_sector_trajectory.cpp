#include <algorithm>
#include <cmath>
#include <cstdint>
#include <limits>

#include "src/internal/abi_impl.hpp"
#include "include/touhou_native/lattice.hpp"

using touhou_native::clearance_index;

namespace {

constexpr double two_pi = 6.283185307179586476925286766559;
constexpr double numeric_guard = 2.0e-5;

double boundary_segment_distance(
    double dx,
    double dy,
    double angle,
    double minimum_radius,
    double maximum_radius
) {
    const double cosine = std::cos(angle);
    const double sine = std::sin(angle);
    const double projection = std::clamp(
        dx * cosine + dy * sine,
        minimum_radius,
        maximum_radius
    );
    return std::hypot(
        dx - projection * cosine,
        dy - projection * sine
    );
}

double annular_sector_distance(
    double sample_x,
    double sample_y,
    double origin_x,
    double origin_y,
    double minimum_angle,
    double maximum_angle,
    double minimum_radius,
    double maximum_radius
) {
    const double dx = sample_x - origin_x;
    const double dy = sample_y - origin_y;
    const double radius = std::hypot(dx, dy);
    const double angle_span = maximum_angle - minimum_angle;
    bool inside_angle = angle_span >= two_pi;
    if (!inside_angle) {
        double phase = std::fmod(
            std::atan2(dy, dx) - minimum_angle,
            two_pi
        );
        if (phase < 0.0) {
            phase += two_pi;
        }
        inside_angle = phase <= angle_span;
    }
    if (inside_angle) {
        return std::max(
            std::max(minimum_radius - radius, radius - maximum_radius),
            0.0
        );
    }
    return std::min(
        boundary_segment_distance(
            dx,
            dy,
            minimum_angle,
            minimum_radius,
            maximum_radius
        ),
        boundary_segment_distance(
            dx,
            dy,
            maximum_angle,
            minimum_radius,
            maximum_radius
        )
    );
}

}  // namespace

int touhou_native_impl_annular_sector_trajectory_clearance_v1(
    float x_start,
    float x_step,
    int column_count,
    float y_start,
    float y_step,
    int row_count,
    int frame_count,
    float player_radius,
    const std::int32_t* frame_offsets,
    const double* origin_x,
    const double* origin_y,
    const double* minimum_angle,
    const double* maximum_angle,
    const double* minimum_radius,
    const double* maximum_radius,
    const double* half_extent_radius,
    const double* origin_uncertainty,
    const double* base_uncertainty,
    const double* uncertainty_per_frame,
    int sample_count,
    float* inout
) {
    if (
        inout == nullptr || frame_offsets == nullptr
        || x_step <= 0.0F || y_step <= 0.0F
        || column_count < 2 || row_count < 2 || frame_count < 1
        || player_radius < 0.0F || sample_count < 0
    ) {
        return 1;
    }
    if (
        frame_offsets[0] != 0
        || frame_offsets[frame_count] != sample_count
    ) {
        return 2;
    }
    if (
        sample_count > 0
        && (
            origin_x == nullptr || origin_y == nullptr
            || minimum_angle == nullptr || maximum_angle == nullptr
            || minimum_radius == nullptr || maximum_radius == nullptr
            || half_extent_radius == nullptr
            || origin_uncertainty == nullptr
            || base_uncertainty == nullptr
            || uncertainty_per_frame == nullptr
        )
    ) {
        return 3;
    }

    for (int frame = 0; frame < frame_count; ++frame) {
        const int begin = frame_offsets[frame];
        const int end = frame_offsets[frame + 1];
        if (begin < 0 || end < begin || end > sample_count) {
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
            if (
                !std::isfinite(origin_x[index])
                || !std::isfinite(origin_y[index])
                || !std::isfinite(minimum_angle[index])
                || !std::isfinite(maximum_angle[index])
                || !std::isfinite(minimum_radius[index])
                || !std::isfinite(maximum_radius[index])
                || minimum_angle[index] > maximum_angle[index]
                || minimum_radius[index] < 0.0
                || minimum_radius[index] > maximum_radius[index]
            ) {
                return 5;
            }
            const double occupied_radius = (
                static_cast<double>(player_radius)
                + half_extent_radius[index]
                + origin_uncertainty[index]
                + base_uncertainty[index]
                + static_cast<double>(frame)
                    * uncertainty_per_frame[index]
            );
            if (!std::isfinite(occupied_radius) || occupied_radius < 0.0) {
                return 6;
            }
            const double improvement_radius = (
                std::max(static_cast<double>(frame_maximum), 0.0)
                + occupied_radius
            );
            const double bound_radius = (
                maximum_radius[index] + improvement_radius
            );
            int first_column = 0;
            int last_column = column_count - 1;
            int first_row = 0;
            int last_row = row_count - 1;
            if (std::isfinite(bound_radius)) {
                first_column = std::max(
                    0,
                    static_cast<int>(std::floor(
                        (
                            origin_x[index] - bound_radius
                            - static_cast<double>(x_start)
                        ) / static_cast<double>(x_step)
                    ))
                );
                last_column = std::min(
                    column_count - 1,
                    static_cast<int>(std::ceil(
                        (
                            origin_x[index] + bound_radius
                            - static_cast<double>(x_start)
                        ) / static_cast<double>(x_step)
                    ))
                );
                first_row = std::max(
                    0,
                    static_cast<int>(std::floor(
                        (
                            origin_y[index] - bound_radius
                            - static_cast<double>(y_start)
                        ) / static_cast<double>(y_step)
                    ))
                );
                last_row = std::min(
                    row_count - 1,
                    static_cast<int>(std::ceil(
                        (
                            origin_y[index] + bound_radius
                            - static_cast<double>(y_start)
                        ) / static_cast<double>(y_step)
                    ))
                );
            }
            for (int row = first_row; row <= last_row; ++row) {
                const double sample_y = (
                    static_cast<double>(y_start)
                    + static_cast<double>(row) * y_step
                );
                for (
                    int column = first_column;
                    column <= last_column;
                    ++column
                ) {
                    const double sample_x = (
                        static_cast<double>(x_start)
                        + static_cast<double>(column) * x_step
                    );
                    const std::size_t output_index = clearance_index(
                        frame,
                        row,
                        column,
                        row_count,
                        column_count
                    );
                    const double distance = annular_sector_distance(
                        sample_x,
                        sample_y,
                        origin_x[index],
                        origin_y[index],
                        minimum_angle[index],
                        maximum_angle[index],
                        minimum_radius[index],
                        maximum_radius[index]
                    );
                    const float clearance = static_cast<float>(
                        distance - occupied_radius - numeric_guard
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
