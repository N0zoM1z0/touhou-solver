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

#include "include/touhou_native/export.hpp"

#include "include/touhou_native/lattice.hpp"
#include "robust_transition_table.hpp"

using namespace touhou_native;

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
