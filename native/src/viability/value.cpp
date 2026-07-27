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
#include "robust_transition_table.hpp"
#include "src/viability/workers.hpp"

using namespace touhou_native;

int touhou_native_impl_robust_safety_value_v1(
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

int touhou_native_impl_robust_safety_policy_v1(
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
    const int worker_count = touhou_native::viability_internal::worker_count();
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
