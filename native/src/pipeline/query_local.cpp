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
