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

using namespace touhou_native;

namespace {

using namespace touhou_native;

thread_local int viability_worker_limit = 4;

inline int viability_worker_count() {
    const unsigned hardware_threads = std::thread::hardware_concurrency();
    return std::max(
        1,
        std::min(
            viability_worker_limit,
            static_cast<int>(
                hardware_threads == 0 ? 1 : hardware_threads
            )
        )
    );
}

}  // namespace

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
    const int worker_count = viability_worker_count();
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

int touhou_native_impl_set_current_thread_viability_worker_limit_v1(
    int worker_limit
) {
    if (worker_limit < 1 || worker_limit > 4) {
        return -1;
    }
    viability_worker_limit = worker_limit;
    return 0;
}

int touhou_native_impl_robust_viability_v1(
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

int touhou_native_impl_robust_viability_terminal_v1(
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
    const int worker_count = viability_worker_count();
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

int touhou_native_impl_robust_survival_viability_v1(
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
    const int worker_count = viability_worker_count();

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
