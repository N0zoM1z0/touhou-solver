// Backward-compatible belief-pipeline implementation adapters.

#include <cstdint>
#include <limits>

#include "src/internal/abi_impl.hpp"
#include "include/touhou_native/status.hpp"

using namespace touhou_native;

int touhou_native_impl_belief_pipeline_workspace_create_v6(
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
    std::uint32_t base_action_mask,
    std::uint32_t budgeted_action_mask,
    int continuation_budget,
    int remaining_delay_bucket_size,
    int continuation_policy_mode,
    const int* delay_frames,
    int delay_count,
    const int* cadence_frames,
    int cadence_count,
    float required_clearance,
    int clamp_to_bounds,
    void** output_workspace
) {
    if (action_count < 1 || action_count > PIPELINE_MAX_ACTIONS) {
        return 2;
    }
    return touhou_native_impl_belief_pipeline_workspace_create_v7(
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
        base_action_mask,
        budgeted_action_mask,
        continuation_budget,
        remaining_delay_bucket_size,
        continuation_policy_mode,
        delay_frames,
        delay_count,
        cadence_frames,
        cadence_count,
        required_clearance,
        clamp_to_bounds,
        output_workspace
    );
}

int touhou_native_impl_belief_pipeline_workspace_create_v5(
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
    std::uint32_t base_action_mask,
    std::uint32_t budgeted_action_mask,
    int continuation_budget,
    int reveal_remaining_delay,
    int continuation_policy_mode,
    const int* delay_frames,
    int delay_count,
    const int* cadence_frames,
    int cadence_count,
    float required_clearance,
    int clamp_to_bounds,
    void** output_workspace
) {
    return touhou_native_impl_belief_pipeline_workspace_create_v6(
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
        base_action_mask,
        budgeted_action_mask,
        continuation_budget,
        reveal_remaining_delay != 0 ? 1 : 0,
        continuation_policy_mode,
        delay_frames,
        delay_count,
        cadence_frames,
        cadence_count,
        required_clearance,
        clamp_to_bounds,
        output_workspace
    );
}

int touhou_native_impl_belief_pipeline_workspace_create_v4(
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
    std::uint32_t base_action_mask,
    std::uint32_t budgeted_action_mask,
    int continuation_budget,
    int reveal_remaining_delay,
    const int* delay_frames,
    int delay_count,
    const int* cadence_frames,
    int cadence_count,
    float required_clearance,
    int clamp_to_bounds,
    void** output_workspace
) {
    return touhou_native_impl_belief_pipeline_workspace_create_v6(
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
        base_action_mask,
        budgeted_action_mask,
        continuation_budget,
        reveal_remaining_delay != 0 ? 1 : 0,
        0,
        delay_frames,
        delay_count,
        cadence_frames,
        cadence_count,
        required_clearance,
        clamp_to_bounds,
        output_workspace
    );
}

int touhou_native_impl_belief_pipeline_workspace_create_v3(
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
    std::uint32_t base_action_mask,
    std::uint32_t budgeted_action_mask,
    int continuation_budget,
    const int* delay_frames,
    int delay_count,
    const int* cadence_frames,
    int cadence_count,
    float required_clearance,
    int clamp_to_bounds,
    void** output_workspace
) {
    return touhou_native_impl_belief_pipeline_workspace_create_v6(
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
        base_action_mask,
        budgeted_action_mask,
        continuation_budget,
        0,
        0,
        delay_frames,
        delay_count,
        cadence_frames,
        cadence_count,
        required_clearance,
        clamp_to_bounds,
        output_workspace
    );
}

int touhou_native_impl_belief_pipeline_workspace_create_v2(
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
    std::uint32_t continuation_action_mask,
    const int* delay_frames,
    int delay_count,
    const int* cadence_frames,
    int cadence_count,
    float required_clearance,
    int clamp_to_bounds,
    void** output_workspace
) {
    return touhou_native_impl_belief_pipeline_workspace_create_v6(
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
        continuation_action_mask,
        0,
        0,
        0,
        0,
        delay_frames,
        delay_count,
        cadence_frames,
        cadence_count,
        required_clearance,
        clamp_to_bounds,
        output_workspace
    );
}

int touhou_native_impl_belief_pipeline_workspace_create_v1(
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
    const int* cadence_frames,
    int cadence_count,
    float required_clearance,
    int clamp_to_bounds,
    void** output_workspace
) {
    if (action_count < 1 || action_count > PIPELINE_MAX_ACTIONS) {
        return 2;
    }
    const std::uint32_t every_action_mask = (
        action_count == 32
        ? std::numeric_limits<std::uint32_t>::max()
        : (
            (std::uint32_t{1} << action_count)
            - std::uint32_t{1}
        )
    );
    return touhou_native_impl_belief_pipeline_workspace_create_v6(
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
        every_action_mask,
        0,
        0,
        0,
        0,
        delay_frames,
        delay_count,
        cadence_frames,
        cadence_count,
        required_clearance,
        clamp_to_bounds,
        output_workspace
    );
}


int touhou_native_impl_belief_pipeline_workspace_query_v1(
    void* workspace,
    int start_frame,
    int start_row,
    int start_column,
    int observed_action,
    int pending_action,
    const int* pending_remaining_frames,
    int pending_remaining_count,
    int timeout_ms,
    std::uint16_t* output_state_frames,
    float* output_state_margin,
    std::uint16_t* output_action_frames,
    float* output_action_margins,
    std::uint32_t* output_best_action_mask,
    std::uint64_t* output_stats
) {
    return touhou_native_impl_belief_pipeline_workspace_query_v2(
        workspace,
        start_frame,
        start_row,
        start_column,
        observed_action,
        pending_action,
        pending_remaining_frames,
        pending_remaining_count,
        -1,
        timeout_ms,
        output_state_frames,
        output_state_margin,
        output_action_frames,
        output_action_margins,
        output_best_action_mask,
        output_stats
    );
}


int touhou_native_impl_belief_pipeline_workspace_certify_upper_v1(
    void* workspace,
    int start_frame,
    int start_row,
    int start_column,
    int observed_action,
    int pending_action,
    const int* pending_remaining_frames,
    int pending_remaining_count,
    int continuation_action_budget,
    std::uint16_t lower_frames,
    float lower_margin,
    int timeout_ms,
    std::uint32_t* output_unresolved_action_mask,
    std::uint64_t* output_stats
) {
    int deadline_expired = 0;
    return touhou_native_impl_belief_pipeline_workspace_certify_upper_v2(
        workspace,
        start_frame,
        start_row,
        start_column,
        observed_action,
        pending_action,
        pending_remaining_frames,
        pending_remaining_count,
        continuation_action_budget,
        lower_frames,
        lower_margin,
        timeout_ms,
        output_unresolved_action_mask,
        &deadline_expired,
        output_stats
    );
}
