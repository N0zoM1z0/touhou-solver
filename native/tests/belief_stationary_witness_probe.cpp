// Standalone internal-API probe for Python/native stationary witness parity.

#include <cstdint>
#include <iomanip>
#include <iostream>
#include <limits>
#include <vector>

#include "src/internal/pipeline_impl.hpp"

namespace {

template <typename Value>
bool read_values(std::vector<Value>* output, int count) {
    if (count < 0) {
        return false;
    }
    output->resize(static_cast<std::size_t>(count));
    for (Value& value : *output) {
        if (!(std::cin >> value)) {
            return false;
        }
    }
    return true;
}

}  // namespace

int main() {
    int frame_count = 0;
    int row_count = 0;
    int column_count = 0;
    int action_count = 0;
    double x_start = 0.0;
    double x_step = 0.0;
    double y_start = 0.0;
    double y_step = 0.0;
    float required_clearance = 0.0F;
    int clamp_to_bounds = 0;
    std::uint64_t base_action_mask = 0;
    if (!(
        std::cin
        >> frame_count >> row_count >> column_count >> action_count
        >> x_start >> x_step >> y_start >> y_step
        >> required_clearance >> clamp_to_bounds >> base_action_mask
    )) {
        return 2;
    }

    int delay_count = 0;
    std::cin >> delay_count;
    std::vector<int> delays;
    if (!read_values(&delays, delay_count)) {
        return 2;
    }
    int cadence_count = 0;
    std::cin >> cadence_count;
    std::vector<int> cadences;
    if (!read_values(&cadences, cadence_count)) {
        return 2;
    }
    std::vector<double> velocity_x;
    std::vector<double> velocity_y;
    if (
        !read_values(&velocity_x, action_count)
        || !read_values(&velocity_y, action_count)
    ) {
        return 2;
    }
    const int clearance_count = (
        frame_count * row_count * column_count
    );
    std::vector<float> clearance;
    if (!read_values(&clearance, clearance_count)) {
        return 2;
    }

    int start_frame = 0;
    int start_row = 0;
    int start_column = 0;
    int observed_action = 0;
    int pending_action = -1;
    int pending_remaining_count = 0;
    if (!(
        std::cin
        >> start_frame >> start_row >> start_column
        >> observed_action >> pending_action >> pending_remaining_count
    )) {
        return 2;
    }
    std::vector<int> pending_remaining;
    if (!read_values(&pending_remaining, pending_remaining_count)) {
        return 2;
    }
    int root_action = 0;
    if (!(std::cin >> root_action)) {
        return 2;
    }

    void* workspace = nullptr;
    const int create_status =
        touhou_native_impl_belief_pipeline_workspace_create_v7(
            clearance.data(),
            frame_count,
            row_count,
            column_count,
            x_start,
            x_step,
            y_start,
            y_step,
            velocity_x.data(),
            velocity_y.data(),
            action_count,
            base_action_mask,
            0,
            0,
            0,
            0,
            delays.data(),
            delay_count,
            cadences.data(),
            cadence_count,
            required_clearance,
            clamp_to_bounds,
            &workspace
        );
    if (create_status != 0) {
        std::cout << create_status << '\n';
        return 0;
    }

    std::vector<BeliefStationaryWitnessStepV1> steps(
        static_cast<std::size_t>(frame_count)
    );
    int step_count = 0;
    std::uint16_t frames = 0;
    float margin = 0.0F;
    std::uint64_t evaluated_state_count = 0;
    const int status =
        touhou_native_impl_belief_pipeline_workspace_stationary_witness_v1(
            workspace,
            start_frame,
            start_row,
            start_column,
            observed_action,
            pending_action,
            pending_remaining.empty()
                ? nullptr
                : pending_remaining.data(),
            pending_remaining_count,
            root_action,
            0,
            steps.data(),
            frame_count,
            &step_count,
            &frames,
            &margin,
            &evaluated_state_count
        );
    std::cout << std::setprecision(
        std::numeric_limits<float>::max_digits10
    );
    std::cout
        << status << ' ' << frames << ' ' << margin << ' '
        << step_count << ' ' << evaluated_state_count << '\n';
    if (status == 0) {
        for (int index = 0; index < step_count; ++index) {
            const BeliefStationaryWitnessStepV1& step = steps[index];
            std::cout
                << step.frame << ' '
                << step.row << ' '
                << step.column << ' '
                << step.active_action << ' '
                << step.pending_action << ' '
                << step.remaining_delay_mask << ' '
                << step.selected_action << ' '
                << step.hidden_remaining_before << ' '
                << step.pickup_delay << ' '
                << step.cadence << ' '
                << step.prefix_bottleneck_margin << ' '
                << step.state_frames << ' '
                << step.state_margin << ' '
                << step.failed << ' '
                << step.successor_frame << ' '
                << step.successor_row << ' '
                << step.successor_column << ' '
                << step.successor_active_action << ' '
                << step.successor_pending_action << ' '
                << step.successor_remaining_delay_mask << ' '
                << step.successor_frames << ' '
                << step.successor_margin << ' '
                << step.merged_hidden_branch_count
                << '\n';
        }
    }
    touhou_native_impl_belief_pipeline_workspace_destroy_v1(workspace);
    return 0;
}
