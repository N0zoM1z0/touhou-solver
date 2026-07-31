#include <algorithm>
#include <atomic>
#include <cmath>
#include <cstdint>
#include <limits>
#include <thread>
#include <vector>

#include "src/internal/abi_impl.hpp"
#include "include/touhou_native/lattice.hpp"

using touhou_native::clearance_index;

namespace {

constexpr double two_pi = 6.283185307179586476925286766559;
constexpr double numeric_guard = 2.0e-5;
constexpr unsigned int maximum_worker_count = 16;

struct AngularInterval {
    double start;
    double end;
};

bool same_geometry(
    int left,
    int right,
    const double* origin_x,
    const double* origin_y,
    const double* minimum_radius,
    const double* maximum_radius,
    const double* half_extent_radius,
    const double* origin_uncertainty,
    const double* base_uncertainty,
    const double* uncertainty_per_frame
) {
    return (
        origin_x[left] == origin_x[right]
        && origin_y[left] == origin_y[right]
        && minimum_radius[left] == minimum_radius[right]
        && maximum_radius[left] == maximum_radius[right]
        && half_extent_radius[left] == half_extent_radius[right]
        && origin_uncertainty[left] == origin_uncertainty[right]
        && base_uncertainty[left] == base_uncertainty[right]
        && uncertainty_per_frame[left] == uncertainty_per_frame[right]
    );
}

std::vector<AngularInterval> angular_union(
    const std::vector<int>& order,
    std::size_t begin,
    std::size_t end,
    const double* minimum_angle,
    const double* maximum_angle
) {
    std::vector<AngularInterval> pieces;
    pieces.reserve((end - begin) * 2);
    for (std::size_t position = begin; position < end; ++position) {
        const int index = order[position];
        const double span = maximum_angle[index] - minimum_angle[index];
        if (span >= two_pi) {
            return {{0.0, two_pi}};
        }
        double start = std::fmod(minimum_angle[index], two_pi);
        if (start < 0.0) {
            start += two_pi;
        }
        const double interval_end = start + span;
        if (interval_end <= two_pi) {
            pieces.push_back({start, interval_end});
        } else {
            pieces.push_back({start, two_pi});
            pieces.push_back({0.0, interval_end - two_pi});
        }
    }
    std::sort(
        pieces.begin(),
        pieces.end(),
        [](const AngularInterval& left, const AngularInterval& right) {
            if (left.start != right.start) {
                return left.start < right.start;
            }
            return left.end < right.end;
        }
    );
    std::vector<AngularInterval> merged;
    merged.reserve(pieces.size());
    for (const AngularInterval& interval : pieces) {
        if (
            !merged.empty()
            && interval.start <= merged.back().end
        ) {
            merged.back().end = std::max(
                merged.back().end,
                interval.end
            );
        } else {
            merged.push_back(interval);
        }
    }
    return merged;
}

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

double annular_sector_union_distance(
    double sample_x,
    double sample_y,
    double origin_x,
    double origin_y,
    double minimum_radius,
    double maximum_radius,
    const std::vector<AngularInterval>& intervals
) {
    const double dx = sample_x - origin_x;
    const double dy = sample_y - origin_y;
    const double radius = std::hypot(dx, dy);
    const double radial_distance = std::max(
        std::max(minimum_radius - radius, radius - maximum_radius),
        0.0
    );
    if (
        intervals.size() == 1
        && intervals.front().start <= 0.0
        && intervals.front().end >= two_pi
    ) {
        return radial_distance;
    }
    double angle = std::atan2(dy, dx);
    if (angle < 0.0) {
        angle += two_pi;
    }
    const auto next = std::upper_bound(
        intervals.begin(),
        intervals.end(),
        angle,
        [](double value, const AngularInterval& interval) {
            return value < interval.start;
        }
    );
    if (next != intervals.begin()) {
        const AngularInterval& previous = *(next - 1);
        if (angle <= previous.end) {
            return radial_distance;
        }
    }
    const double next_boundary = (
        next == intervals.end()
        ? intervals.front().start + two_pi
        : next->start
    );
    const double previous_boundary = (
        next == intervals.begin()
        ? intervals.back().end - two_pi
        : (next - 1)->end
    );
    return std::min(
        boundary_segment_distance(
            dx,
            dy,
            previous_boundary,
            minimum_radius,
            maximum_radius
        ),
        boundary_segment_distance(
            dx,
            dy,
            next_boundary,
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
        }
    }

    auto process_frame = [&](int frame) {
        const int begin = frame_offsets[frame];
        const int end = frame_offsets[frame + 1];
        if (begin == end) {
            return;
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
        std::vector<int> order;
        order.reserve(static_cast<std::size_t>(end - begin));
        for (int index = begin; index < end; ++index) {
            order.push_back(index);
        }
        std::sort(order.begin(), order.end(), [&](int left, int right) {
            const double* fields[] = {
                origin_x,
                origin_y,
                minimum_radius,
                maximum_radius,
                half_extent_radius,
                origin_uncertainty,
                base_uncertainty,
                uncertainty_per_frame,
            };
            for (const double* field : fields) {
                if (field[left] != field[right]) {
                    return field[left] < field[right];
                }
            }
            if (minimum_angle[left] != minimum_angle[right]) {
                return minimum_angle[left] < minimum_angle[right];
            }
            return maximum_angle[left] < maximum_angle[right];
        });
        std::size_t group_begin = 0;
        while (group_begin < order.size()) {
            std::size_t group_end = group_begin + 1;
            while (
                group_end < order.size()
                && same_geometry(
                    order[group_begin],
                    order[group_end],
                    origin_x,
                    origin_y,
                    minimum_radius,
                    maximum_radius,
                    half_extent_radius,
                    origin_uncertainty,
                    base_uncertainty,
                    uncertainty_per_frame
                )
            ) {
                ++group_end;
            }
            const int index = order[group_begin];
            const std::vector<AngularInterval> intervals = angular_union(
                order,
                group_begin,
                group_end,
                minimum_angle,
                maximum_angle
            );
            const double occupied_radius = (
                static_cast<double>(player_radius)
                + half_extent_radius[index]
                + origin_uncertainty[index]
                + base_uncertainty[index]
                + static_cast<double>(frame)
                    * uncertainty_per_frame[index]
            );
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
                    const double distance = annular_sector_union_distance(
                        sample_x,
                        sample_y,
                        origin_x[index],
                        origin_y[index],
                        minimum_radius[index],
                        maximum_radius[index],
                        intervals
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
            group_begin = group_end;
        }
    };

    const unsigned int hardware_workers = std::max(
        1U,
        std::thread::hardware_concurrency()
    );
    const unsigned int worker_count = std::min(
        {
            maximum_worker_count,
            hardware_workers,
            static_cast<unsigned int>(frame_count),
        }
    );
    if (worker_count == 1 || sample_count < 128) {
        for (int frame = 0; frame < frame_count; ++frame) {
            process_frame(frame);
        }
        return 0;
    }
    std::atomic<int> next_frame{0};
    std::vector<std::thread> workers;
    workers.reserve(worker_count);
    for (unsigned int worker = 0; worker < worker_count; ++worker) {
        workers.emplace_back([&]() {
            while (true) {
                const int frame = next_frame.fetch_add(
                    1,
                    std::memory_order_relaxed
                );
                if (frame >= frame_count) {
                    return;
                }
                process_frame(frame);
            }
        });
    }
    for (std::thread& worker : workers) {
        worker.join();
    }
    return 0;
}

int touhou_native_impl_annular_sector_frame_clearance_v1(
    const float* positions_x,
    const float* positions_y,
    int position_count,
    int frame,
    float player_radius,
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
    float* output
) {
    if (
        positions_x == nullptr || positions_y == nullptr || output == nullptr
        || position_count < 1 || frame < 0 || player_radius < 0.0F
        || sample_count < 0
    ) {
        return 1;
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
        return 2;
    }
    for (int position = 0; position < position_count; ++position) {
        if (
            !std::isfinite(positions_x[position])
            || !std::isfinite(positions_y[position])
        ) {
            return 3;
        }
        output[position] = std::numeric_limits<float>::infinity();
    }
    for (int index = 0; index < sample_count; ++index) {
        if (
            !std::isfinite(origin_x[index])
            || !std::isfinite(origin_y[index])
            || !std::isfinite(minimum_angle[index])
            || !std::isfinite(maximum_angle[index])
            || !std::isfinite(minimum_radius[index])
            || !std::isfinite(maximum_radius[index])
            || !std::isfinite(half_extent_radius[index])
            || !std::isfinite(origin_uncertainty[index])
            || !std::isfinite(base_uncertainty[index])
            || !std::isfinite(uncertainty_per_frame[index])
            || minimum_angle[index] > maximum_angle[index]
            || minimum_radius[index] < 0.0
            || minimum_radius[index] > maximum_radius[index]
            || half_extent_radius[index] < 0.0
            || origin_uncertainty[index] < 0.0
            || base_uncertainty[index] < 0.0
            || uncertainty_per_frame[index] < 0.0
        ) {
            return 4;
        }
        const double occupied_radius = (
            static_cast<double>(player_radius)
            + half_extent_radius[index]
            + origin_uncertainty[index]
            + base_uncertainty[index]
            + static_cast<double>(frame) * uncertainty_per_frame[index]
        );
        if (!std::isfinite(occupied_radius) || occupied_radius < 0.0) {
            return 5;
        }
    }

    std::vector<int> order;
    order.reserve(static_cast<std::size_t>(sample_count));
    for (int index = 0; index < sample_count; ++index) {
        order.push_back(index);
    }
    std::sort(order.begin(), order.end(), [&](int left, int right) {
        const double* fields[] = {
            origin_x,
            origin_y,
            minimum_radius,
            maximum_radius,
            half_extent_radius,
            origin_uncertainty,
            base_uncertainty,
            uncertainty_per_frame,
        };
        for (const double* field : fields) {
            if (field[left] != field[right]) {
                return field[left] < field[right];
            }
        }
        if (minimum_angle[left] != minimum_angle[right]) {
            return minimum_angle[left] < minimum_angle[right];
        }
        return maximum_angle[left] < maximum_angle[right];
    });

    std::size_t group_begin = 0;
    while (group_begin < order.size()) {
        std::size_t group_end = group_begin + 1;
        while (
            group_end < order.size()
            && same_geometry(
                order[group_begin],
                order[group_end],
                origin_x,
                origin_y,
                minimum_radius,
                maximum_radius,
                half_extent_radius,
                origin_uncertainty,
                base_uncertainty,
                uncertainty_per_frame
            )
        ) {
            ++group_end;
        }
        const int index = order[group_begin];
        const std::vector<AngularInterval> intervals = angular_union(
            order,
            group_begin,
            group_end,
            minimum_angle,
            maximum_angle
        );
        const double occupied_radius = (
            static_cast<double>(player_radius)
            + half_extent_radius[index]
            + origin_uncertainty[index]
            + base_uncertainty[index]
            + static_cast<double>(frame) * uncertainty_per_frame[index]
        );
        for (int position = 0; position < position_count; ++position) {
            const double distance = annular_sector_union_distance(
                positions_x[position],
                positions_y[position],
                origin_x[index],
                origin_y[index],
                minimum_radius[index],
                maximum_radius[index],
                intervals
            );
            const float clearance = static_cast<float>(
                distance - occupied_radius - numeric_guard
            );
            output[position] = std::min(output[position], clearance);
        }
        group_begin = group_end;
    }
    return 0;
}
