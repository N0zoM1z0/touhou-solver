#include <cstdint>

#include "include/touhou_native/abi.h"
#include "include/touhou_native/export.hpp"
#include "src/internal/abi_impl.hpp"


TOUHOU_EXPORT int touhou_pipeline_survival_workspace_create_v2(
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
    const int* decision_frame_support,
    int decision_frame_count,
    int continuation_decision_frames,
    float required_clearance,
    int clamp_to_bounds,
    void** output_workspace
) {
    return touhou_native_impl_pipeline_survival_workspace_create_v2(
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
        decision_frame_support,
        decision_frame_count,
        continuation_decision_frames,
        required_clearance,
        clamp_to_bounds,
        output_workspace
    );
}

TOUHOU_EXPORT int touhou_pipeline_survival_workspace_create_v1(
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
    void** output_workspace
) {
    return touhou_native_impl_pipeline_survival_workspace_create_v1(
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
        decision_frames,
        required_clearance,
        clamp_to_bounds,
        output_workspace
    );
}

TOUHOU_EXPORT int touhou_pipeline_survival_workspace_query_v1(
    void* workspace,
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
    std::uint64_t* output_stats
) {
    return touhou_native_impl_pipeline_survival_workspace_query_v1(
        workspace,
        start_frame,
        start_row,
        start_column,
        observed_action,
        pending_action,
        pending_remaining_frames,
        pending_remaining_count,
        output_state_frames,
        output_state_margin,
        output_action_frames,
        output_action_margins,
        output_best_action_mask,
        output_stats
    );
}

TOUHOU_EXPORT int touhou_pipeline_survival_workspace_contains_root_v1(
    void* workspace,
    int start_frame,
    int start_row,
    int start_column,
    int observed_action,
    int pending_action,
    const int* pending_remaining_frames,
    int pending_remaining_count,
    int* output_present
) {
    return touhou_native_impl_pipeline_survival_workspace_contains_root_v1(
        workspace,
        start_frame,
        start_row,
        start_column,
        observed_action,
        pending_action,
        pending_remaining_frames,
        pending_remaining_count,
        output_present
    );
}

TOUHOU_EXPORT int touhou_pipeline_survival_workspace_query_v2(
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
    return touhou_native_impl_pipeline_survival_workspace_query_v2(
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

TOUHOU_EXPORT int touhou_pipeline_survival_workspace_prewarm_continuation_v1(
    void* workspace,
    int start_frame,
    int start_row,
    int start_column,
    int observed_action,
    int pending_action,
    const int* pending_remaining_frames,
    int pending_remaining_count,
    int timeout_ms,
    std::uint16_t* output_frames,
    float* output_margin,
    std::uint64_t* output_stats
) {
    return touhou_native_impl_pipeline_survival_workspace_prewarm_continuation_v1(
        workspace,
        start_frame,
        start_row,
        start_column,
        observed_action,
        pending_action,
        pending_remaining_frames,
        pending_remaining_count,
        timeout_ms,
        output_frames,
        output_margin,
        output_stats
    );
}

TOUHOU_EXPORT int touhou_pipeline_survival_workspace_merge_continuation_v1(
    void* destination_workspace,
    void* source_workspace,
    std::uint64_t* output_added_states
) {
    return touhou_native_impl_pipeline_survival_workspace_merge_continuation_v1(
        destination_workspace,
        source_workspace,
        output_added_states
    );
}

TOUHOU_EXPORT int touhou_pipeline_survival_workspace_cancel_v1(
    void* workspace
) {
    return touhou_native_impl_pipeline_survival_workspace_cancel_v1(
        workspace
    );
}

TOUHOU_EXPORT void touhou_pipeline_survival_workspace_destroy_v1(
    void* workspace
) {
    touhou_native_impl_pipeline_survival_workspace_destroy_v1(
        workspace
    );
}
