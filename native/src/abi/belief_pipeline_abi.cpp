#include <cstdint>

#include "include/touhou_native/abi.h"
#include "include/touhou_native/export.hpp"
#include "src/internal/abi_impl.hpp"

TOUHOU_EXPORT int touhou_belief_pipeline_workspace_create_v7(
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
    std::uint64_t base_action_mask,
    std::uint64_t budgeted_action_mask,
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

TOUHOU_EXPORT int touhou_belief_pipeline_workspace_create_v8(
    const float* clearance,
    const float* terminal_state_margins,
    const float* terminal_action_margins,
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
    std::uint64_t base_action_mask,
    std::uint64_t budgeted_action_mask,
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
    return touhou_native_impl_belief_pipeline_workspace_create_v8(
        clearance,
        terminal_state_margins,
        terminal_action_margins,
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

TOUHOU_EXPORT int touhou_belief_pipeline_workspace_create_v6(
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

TOUHOU_EXPORT int touhou_belief_pipeline_workspace_create_v5(
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
    return touhou_native_impl_belief_pipeline_workspace_create_v5(
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
        reveal_remaining_delay,
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

TOUHOU_EXPORT int touhou_belief_pipeline_workspace_create_v4(
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
    return touhou_native_impl_belief_pipeline_workspace_create_v4(
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
        reveal_remaining_delay,
        delay_frames,
        delay_count,
        cadence_frames,
        cadence_count,
        required_clearance,
        clamp_to_bounds,
        output_workspace
    );
}

TOUHOU_EXPORT int touhou_belief_pipeline_workspace_create_v3(
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
    return touhou_native_impl_belief_pipeline_workspace_create_v3(
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
        delay_frames,
        delay_count,
        cadence_frames,
        cadence_count,
        required_clearance,
        clamp_to_bounds,
        output_workspace
    );
}

TOUHOU_EXPORT int touhou_belief_pipeline_workspace_create_v2(
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
    return touhou_native_impl_belief_pipeline_workspace_create_v2(
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
        delay_frames,
        delay_count,
        cadence_frames,
        cadence_count,
        required_clearance,
        clamp_to_bounds,
        output_workspace
    );
}

TOUHOU_EXPORT int touhou_belief_pipeline_workspace_create_v1(
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
    return touhou_native_impl_belief_pipeline_workspace_create_v1(
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
        cadence_frames,
        cadence_count,
        required_clearance,
        clamp_to_bounds,
        output_workspace
    );
}

TOUHOU_EXPORT int touhou_belief_pipeline_workspace_query_v3(
    void* workspace,
    int start_frame,
    int start_row,
    int start_column,
    int observed_action,
    int pending_action,
    const int* pending_remaining_frames,
    int pending_remaining_count,
    int continuation_action_budget,
    int timeout_ms,
    std::uint16_t* output_state_frames,
    float* output_state_margin,
    std::uint16_t* output_action_frames,
    float* output_action_margins,
    std::uint64_t* output_best_action_mask,
    std::uint64_t* output_stats
) {
    return touhou_native_impl_belief_pipeline_workspace_query_v3(
        workspace,
        start_frame,
        start_row,
        start_column,
        observed_action,
        pending_action,
        pending_remaining_frames,
        pending_remaining_count,
        continuation_action_budget,
        timeout_ms,
        output_state_frames,
        output_state_margin,
        output_action_frames,
        output_action_margins,
        output_best_action_mask,
        output_stats
    );
}

TOUHOU_EXPORT int touhou_belief_pipeline_workspace_query_v2(
    void* workspace,
    int start_frame,
    int start_row,
    int start_column,
    int observed_action,
    int pending_action,
    const int* pending_remaining_frames,
    int pending_remaining_count,
    int continuation_action_budget,
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
        continuation_action_budget,
        timeout_ms,
        output_state_frames,
        output_state_margin,
        output_action_frames,
        output_action_margins,
        output_best_action_mask,
        output_stats
    );
}

TOUHOU_EXPORT int touhou_belief_pipeline_workspace_query_v1(
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
    return touhou_native_impl_belief_pipeline_workspace_query_v1(
        workspace,
        start_frame,
        start_row,
        start_column,
        observed_action,
        pending_action,
        pending_remaining_frames,
        pending_remaining_count,
        timeout_ms,
        output_state_frames,
        output_state_margin,
        output_action_frames,
        output_action_margins,
        output_best_action_mask,
        output_stats
    );
}

TOUHOU_EXPORT int touhou_belief_pipeline_workspace_certify_upper_v3(
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
    std::uint64_t* output_unresolved_action_mask,
    int* output_deadline_expired,
    std::uint64_t* output_stats
) {
    return touhou_native_impl_belief_pipeline_workspace_certify_upper_v3(
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
        output_deadline_expired,
        output_stats
    );
}

TOUHOU_EXPORT int touhou_belief_pipeline_workspace_certify_exact_v1(
    void* workspace,
    int start_frame,
    int start_row,
    int start_column,
    int observed_action,
    int pending_action,
    const int* pending_remaining_frames,
    int pending_remaining_count,
    int continuation_action_budget,
    std::uint16_t target_frames,
    float target_margin,
    int timeout_ms,
    std::uint64_t* output_winning_action_mask,
    std::uint64_t* output_unresolved_action_mask,
    int* output_deadline_expired,
    std::uint64_t* output_stats
) {
    return touhou_native_impl_belief_pipeline_workspace_certify_exact_v1(
        workspace,
        start_frame,
        start_row,
        start_column,
        observed_action,
        pending_action,
        pending_remaining_frames,
        pending_remaining_count,
        continuation_action_budget,
        target_frames,
        target_margin,
        timeout_ms,
        output_winning_action_mask,
        output_unresolved_action_mask,
        output_deadline_expired,
        output_stats
    );
}

TOUHOU_EXPORT int touhou_belief_pipeline_workspace_certify_upper_v2(
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
    int* output_deadline_expired,
    std::uint64_t* output_stats
) {
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
        output_deadline_expired,
        output_stats
    );
}

TOUHOU_EXPORT int touhou_belief_pipeline_workspace_certify_upper_v1(
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
    return touhou_native_impl_belief_pipeline_workspace_certify_upper_v1(
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
        output_stats
    );
}

TOUHOU_EXPORT int touhou_belief_pipeline_workspace_recommend_action_column_v1(
    void* workspace,
    int start_frame,
    int start_row,
    int start_column,
    int observed_action,
    int pending_action,
    const int* pending_remaining_frames,
    int pending_remaining_count,
    int target_root_action,
    int max_depth,
    int timeout_ms,
    int* output_recommended_action,
    int* output_witness_frame,
    int* output_witness_row,
    int* output_witness_column,
    int* output_witness_active,
    int* output_witness_pending,
    std::uint64_t* output_witness_remaining_mask,
    std::uint16_t* output_current_frames,
    float* output_current_margin,
    std::uint16_t* output_recommended_frames,
    float* output_recommended_margin,
    int* output_depth,
    std::uint64_t* output_stats
) {
    return touhou_native_impl_belief_pipeline_workspace_recommend_action_column_v1(
        workspace,
        start_frame,
        start_row,
        start_column,
        observed_action,
        pending_action,
        pending_remaining_frames,
        pending_remaining_count,
        target_root_action,
        max_depth,
        timeout_ms,
        output_recommended_action,
        output_witness_frame,
        output_witness_row,
        output_witness_column,
        output_witness_active,
        output_witness_pending,
        output_witness_remaining_mask,
        output_current_frames,
        output_current_margin,
        output_recommended_frames,
        output_recommended_margin,
        output_depth,
        output_stats
    );
}

TOUHOU_EXPORT int touhou_belief_pipeline_workspace_cancel_v1(
    void* workspace
) {
    return touhou_native_impl_belief_pipeline_workspace_cancel_v1(
        workspace
    );
}

TOUHOU_EXPORT void touhou_belief_pipeline_workspace_destroy_v1(
    void* workspace
) {
    touhou_native_impl_belief_pipeline_workspace_destroy_v1(
        workspace
    );
}
