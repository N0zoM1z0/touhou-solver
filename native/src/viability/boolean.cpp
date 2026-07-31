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
    const std::uint32_t every_action_mask = (
        action_count == 32
        ? std::numeric_limits<std::uint32_t>::max()
        : (
            (std::uint32_t{1} << action_count)
            - std::uint32_t{1}
        )
    );
    // Use the maximum error from the same finite transition table consumed by
    // the recurrence.  If the entire requested hazard slab clears that bound
    // strictly, every clamped transition sample is safe and the unconstrained
    // terminal recurrence is exactly the all-action kernel.
    const double lattice_error_bound = std::hypot(
        *std::max_element(
            transitions->sample_x_errors.begin(),
            transitions->sample_x_errors.end()
        ),
        *std::max_element(
            transitions->sample_y_errors.begin(),
            transitions->sample_y_errors.end()
        )
    );
    if (terminal_viable == nullptr && clamp) {
        const std::size_t clearance_count = (
            static_cast<std::size_t>(frame_count)
            * row_count
            * column_count
        );
        const bool whole_slab_trivially_safe = std::all_of(
            clearance,
            clearance + clearance_count,
            [&](float value) {
                return (
                    static_cast<double>(value) - lattice_error_bound
                    > static_cast<double>(required_clearance)
                );
            }
        );
        if (whole_slab_trivially_safe) {
            std::fill(
                viable,
                viable + static_cast<std::size_t>(layer_count + 1)
                    * layer_state_count,
                std::uint8_t{1}
            );
            std::fill(
                safe_action_masks,
                safe_action_masks
                    + static_cast<std::size_t>(layer_count)
                        * layer_state_count,
                every_action_mask
            );
            return 0;
        }
    }

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

    const int layer_work = action_count * state_count;
    const int worker_count = touhou_native::viability_internal::worker_count();
    for (int layer = layer_count - 1; layer >= 0; --layer) {
        const int start_frame = layer * frames_per_layer;
        const std::uint8_t* next_layer = (
            viable
            + static_cast<std::size_t>(layer + 1)
                * layer_state_count
        );
        const bool next_layer_all_viable = std::all_of(
            next_layer,
            next_layer + layer_state_count,
            [](std::uint8_t value) { return value != 0; }
        );
        if (clamp && next_layer_all_viable) {
            bool layer_trivially_safe = true;
            for (
                int frame = start_frame;
                frame <= start_frame + frames_per_layer
                    && layer_trivially_safe;
                ++frame
            ) {
                const float* frame_clearance = (
                    clearance
                    + static_cast<std::size_t>(frame) * state_count
                );
                layer_trivially_safe = std::all_of(
                    frame_clearance,
                    frame_clearance + state_count,
                    [&](float value) {
                        return (
                            static_cast<double>(value)
                                - lattice_error_bound
                            > static_cast<double>(required_clearance)
                        );
                    }
                );
            }
            if (layer_trivially_safe) {
                std::fill(
                    viable
                        + static_cast<std::size_t>(layer)
                            * layer_state_count,
                    viable
                        + static_cast<std::size_t>(layer + 1)
                            * layer_state_count,
                    std::uint8_t{1}
                );
                std::fill(
                    safe_action_masks
                        + static_cast<std::size_t>(layer)
                            * layer_state_count,
                    safe_action_masks
                        + static_cast<std::size_t>(layer + 1)
                            * layer_state_count,
                    every_action_mask
                );
                continue;
            }
        }
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
                            // Terminal membership is a necessary condition
                            // for this hidden-delay branch.  Test it before
                            // walking the hazard samples: near exhaustion the
                            // next lower kernel is sparse, so most branches
                            // can be rejected without repeated clearance
                            // lookups and hypot calls.  This is only a
                            // recurrence-order change; every branch accepted
                            // here still checks the identical path below.
                            const Sample terminal_sample = transition_sample(
                                *transitions,
                                active,
                                selected,
                                delay,
                                row,
                                column,
                                frames_per_layer - 1,
                                action_count
                            );
                            const std::int32_t terminal_state = (
                                terminal_sample.inside
                                ? (
                                    terminal_sample.row * column_count
                                    + terminal_sample.column
                                )
                                : -1
                            );
                            if (
                                terminal_state < 0
                                || !viable[state_index(
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
                                break;
                            }
                            for (
                                int step = 1;
                                step <= frames_per_layer;
                                ++step
                            ) {
                                const Sample& sample = (
                                    step == frames_per_layer
                                    ? terminal_sample
                                    : transition_sample(
                                        *transitions,
                                        active,
                                        selected,
                                        delay,
                                        row,
                                        column,
                                        step - 1,
                                        action_count
                                    )
                                );
                                if (
                                    !sample.inside
                                    || clearance[clearance_index(
                                        start_frame + step,
                                        sample.row,
                                        sample.column,
                                        row_count,
                                        column_count
                                    )] - static_cast<float>(sample.error)
                                        <= required_clearance
                                ) {
                                    robust = false;
                                    break;
                                }
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
