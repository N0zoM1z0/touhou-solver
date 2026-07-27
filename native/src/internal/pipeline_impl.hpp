#pragma once

#include <cstdint>

int touhou_native_impl_pipeline_survival_workspace_create_v2(
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
);

int touhou_native_impl_pipeline_survival_workspace_create_v1(
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
);

int touhou_native_impl_pipeline_survival_workspace_query_v1(
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
);

int touhou_native_impl_pipeline_survival_workspace_contains_root_v1(
    void* workspace,
    int start_frame,
    int start_row,
    int start_column,
    int observed_action,
    int pending_action,
    const int* pending_remaining_frames,
    int pending_remaining_count,
    int* output_present
);

int touhou_native_impl_pipeline_survival_workspace_query_v2(
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
);

int touhou_native_impl_pipeline_survival_workspace_prewarm_continuation_v1(
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
);

int touhou_native_impl_pipeline_survival_workspace_merge_continuation_v1(
    void* destination_workspace,
    void* source_workspace,
    std::uint64_t* output_added_states
);

int touhou_native_impl_pipeline_survival_workspace_cancel_v1(
    void* workspace
);

void touhou_native_impl_pipeline_survival_workspace_destroy_v1(
    void* workspace
);

bool belief_pipeline_workspace_supports_u32_masks(
    void* workspace
) noexcept;

int touhou_native_impl_belief_pipeline_workspace_create_v7(
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
);

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
);

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
);

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
);

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
);

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
);

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
);

int touhou_native_impl_belief_pipeline_workspace_query_v3(
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
);

int touhou_native_impl_belief_pipeline_workspace_query_v2(
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
);

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
);

int touhou_native_impl_belief_pipeline_workspace_certify_upper_v3(
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
);

int touhou_native_impl_belief_pipeline_workspace_certify_upper_v2(
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
);

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
);

int touhou_native_impl_belief_pipeline_workspace_recommend_action_column_v1(
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
);

struct BeliefStationaryWitnessStepV1 {
    int frame;
    int row;
    int column;
    int active_action;
    int pending_action;
    std::uint64_t remaining_delay_mask;
    int selected_action;
    int hidden_remaining_before;
    int pickup_delay;
    int cadence;
    float prefix_bottleneck_margin;
    std::uint16_t state_frames;
    float state_margin;
    int failed;
    int successor_frame;
    int successor_row;
    int successor_column;
    int successor_active_action;
    int successor_pending_action;
    std::uint64_t successor_remaining_delay_mask;
    std::uint16_t successor_frames;
    float successor_margin;
    std::uint64_t merged_hidden_branch_count;
};

// Internal-only exact stationary witness extraction. This declaration is
// intentionally absent from include/touhou_native/abi.h and exports.map.
int touhou_native_impl_belief_pipeline_workspace_stationary_witness_v1(
    void* workspace,
    int start_frame,
    int start_row,
    int start_column,
    int observed_action,
    int pending_action,
    const int* pending_remaining_frames,
    int pending_remaining_count,
    int root_action,
    int timeout_ms,
    BeliefStationaryWitnessStepV1* output_steps,
    int step_capacity,
    int* output_step_count,
    std::uint16_t* output_frames,
    float* output_margin,
    std::uint64_t* output_evaluated_state_count
);

int touhou_native_impl_belief_pipeline_workspace_cancel_v1(
    void* workspace
);

void touhou_native_impl_belief_pipeline_workspace_destroy_v1(
    void* workspace
);

int touhou_native_impl_query_local_survival_v1(
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
);
