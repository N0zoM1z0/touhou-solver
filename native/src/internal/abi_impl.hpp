#pragma once

#include <cstdint>

struct TouhouLocalSupplementalQueryV1;
struct TouhouLocalSupplementalOutputV1;

int touhou_native_impl_clearance_volume_v1(
    float x_start,
    float x_step,
    int column_count,
    float y_start,
    float y_step,
    int row_count,
    int frame_count,
    float player_radius,
    float clearance_cap,
    const float* aabb_x,
    const float* aabb_y,
    const float* aabb_velocity_x,
    const float* aabb_velocity_y,
    const float* aabb_half_width,
    const float* aabb_half_height,
    const float* aabb_base_uncertainty,
    const float* aabb_uncertainty_per_frame,
    int aabb_count,
    const float* segment_origin_x,
    const float* segment_origin_y,
    const float* segment_angle,
    const float* segment_tail,
    const float* segment_head,
    const float* segment_half_width,
    const float* segment_base_uncertainty,
    const float* segment_uncertainty_per_frame,
    int segment_count,
    float* output
);

int touhou_native_impl_segment_trajectory_clearance_v1(
    float x_start,
    float x_step,
    int column_count,
    float y_start,
    float y_step,
    int row_count,
    int frame_count,
    float player_radius,
    const std::int32_t* frame_offsets,
    const float* segment_origin_x,
    const float* segment_origin_y,
    const float* segment_angle,
    const float* segment_tail,
    const float* segment_head,
    const float* segment_half_width,
    const float* segment_base_uncertainty,
    const float* segment_uncertainty_per_frame,
    int segment_sample_count,
    float* inout
);

int touhou_native_impl_aabb_trajectory_clearance_v1(
    float x_start,
    float x_step,
    int column_count,
    float y_start,
    float y_step,
    int row_count,
    int frame_count,
    float player_radius,
    const std::int32_t* frame_offsets,
    const float* aabb_x,
    const float* aabb_y,
    const float* aabb_half_width,
    const float* aabb_half_height,
    const float* aabb_base_uncertainty,
    const float* aabb_uncertainty_per_frame,
    int aabb_sample_count,
    float* inout
);

int touhou_native_impl_piecewise_aabb_clearance_v1(
    float x_start,
    float x_step,
    int column_count,
    float y_start,
    float y_step,
    int row_count,
    int frame_count,
    float player_radius,
    const double* aabb_x,
    const double* aabb_y,
    const double* aabb_velocity_x,
    const double* aabb_velocity_y,
    const float* aabb_half_width,
    const float* aabb_half_height,
    const float* aabb_base_uncertainty,
    const float* aabb_uncertainty_per_frame,
    int aabb_count,
    const std::int32_t* event_offsets,
    const std::int32_t* event_frames,
    const double* event_velocity_x,
    const double* event_velocity_y,
    int event_count,
    float* inout
);

int touhou_native_impl_local_hazards_v1(
    const float* positions_x,
    const float* positions_y,
    int position_count,
    int step,
    float player_radius,
    const float* bullet_x,
    const float* bullet_y,
    const float* bullet_half_width,
    const float* bullet_half_height,
    const std::uint8_t* bullet_transformed,
    int bullet_count,
    const float* laser_start_x,
    const float* laser_start_y,
    const float* laser_segment_x,
    const float* laser_segment_y,
    const float* laser_collision_radius,
    const float* laser_base_uncertainty,
    const float* laser_uncertainty_per_frame,
    int laser_count,
    const float* body_x,
    const float* body_y,
    const float* body_half_width,
    const float* body_half_height,
    int body_count,
    double* output_risk,
    std::int32_t* output_collisions,
    double* output_minimum
);

int touhou_native_impl_decode_bullet_pool_v1(
    const std::uint8_t* blob,
    std::uint64_t blob_size,
    int record_count,
    int stride,
    int state_offset,
    int geometry_offset,
    int position_offset,
    int velocity_offset,
    int speed_offset,
    int angle_offset,
    int transform_flags_offset,
    int original_transform_flags_offset,
    int callback_phase_offset,
    int callback_aux_offset,
    float* output_x,
    float* output_y,
    float* output_velocity_x,
    float* output_velocity_y,
    float* output_half_width,
    float* output_half_height,
    std::uint32_t* output_transform_flags,
    std::int32_t* output_slots,
    float* output_speed,
    float* output_angle,
    std::int16_t* output_callback_phase,
    std::uint8_t* output_callback_aux,
    std::uint32_t* output_original_transform_flags,
    int output_capacity,
    std::int32_t* output_count
);

int touhou_native_impl_local_beam_reduce_v1(
    const double* draft_x,
    const double* draft_y,
    const std::int32_t* first_action,
    const std::int32_t* last_direction,
    const std::uint8_t* last_focused,
    const std::uint32_t* collected_mask,
    const double* risk,
    const std::int32_t* collisions,
    const double* minimum_clearance,
    int draft_count,
    int step,
    int beam_width,
    double position_quantization,
    int target_enabled,
    double target_x,
    double target_y,
    int target_deadline,
    double item_safety_clearance,
    double playfield_left,
    double playfield_right,
    double playfield_top,
    double playfield_bottom,
    double reserve_distance,
    double diagonal_speed,
    double cardinal_speed,
    const std::int32_t* certificate_collisions,
    const double* certificate_minimum,
    const std::uint8_t* survival_preferred,
    const std::uint8_t* safety_preferred,
    const double* recovery_distance,
    int action_count,
    std::int32_t* output_indices,
    std::int32_t* output_count
);

int touhou_native_impl_local_supplemental_beam_reduce_v1(
    const double* draft_x,
    const double* draft_y,
    const std::int32_t* first_action,
    const std::int32_t* last_direction,
    const std::uint8_t* last_focused,
    const std::uint32_t* collected_mask,
    const double* risk,
    const std::int32_t* collisions,
    const double* minimum_clearance,
    int draft_count,
    int step,
    int beam_width,
    double position_quantization,
    int target_enabled,
    double target_x,
    double target_y,
    int target_deadline,
    double item_safety_clearance,
    double playfield_left,
    double playfield_right,
    double playfield_top,
    double playfield_bottom,
    double recovery_reserve_distance,
    double supplemental_reserve_distance,
    double diagonal_speed,
    double cardinal_speed,
    const std::int32_t* certificate_collisions,
    const double* certificate_minimum,
    const std::uint8_t* survival_preferred,
    const std::uint8_t* safety_preferred,
    const double* recovery_distance,
    const std::int32_t* repair_volume,
    int action_count,
    std::int32_t* output_indices,
    std::int32_t* output_count
);

int touhou_native_impl_local_supplemental_workspace_create_v1(
    void** output_workspace
);

int touhou_native_impl_local_supplemental_workspace_cancel_v1(
    void* workspace_pointer
);

int touhou_native_impl_local_supplemental_workspace_active_v1(
    void* workspace_pointer,
    int* output_active
);

int touhou_native_impl_local_supplemental_workspace_destroy_v1(
    void* workspace_pointer
);

int touhou_native_impl_local_supplemental_workspace_query_v1(
    void* workspace_pointer,
    const TouhouLocalSupplementalQueryV1* query,
    TouhouLocalSupplementalOutputV1* output
);

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

int touhou_native_impl_set_current_thread_viability_worker_limit_v1(
    int worker_limit
);

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
);

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
);

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
);

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
);

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
);

int touhou_native_impl_losing_survival_labels_v1(
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
);
