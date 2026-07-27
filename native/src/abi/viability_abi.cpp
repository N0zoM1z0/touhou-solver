#include <cstdint>

#include "include/touhou_native/abi.h"
#include "include/touhou_native/export.hpp"
#include "src/internal/abi_impl.hpp"


TOUHOU_EXPORT int touhou_set_current_thread_viability_worker_limit_v1(
    int worker_limit
) {
    return touhou_native_impl_set_current_thread_viability_worker_limit_v1(
        worker_limit
    );
}

TOUHOU_EXPORT int touhou_robust_viability_v1(
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
    return touhou_native_impl_robust_viability_v1(
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
        viable,
        safe_action_masks
    );
}

TOUHOU_EXPORT int touhou_robust_viability_terminal_v1(
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
    return touhou_native_impl_robust_viability_terminal_v1(
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

TOUHOU_EXPORT int touhou_robust_safety_value_v1(
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
    return touhou_native_impl_robust_safety_value_v1(
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
        clamp_to_bounds,
        state_values,
        action_values
    );
}

TOUHOU_EXPORT int touhou_robust_safety_policy_v1(
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
    return touhou_native_impl_robust_safety_policy_v1(
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
        clamp_to_bounds,
        state_values,
        best_action_masks
    );
}

TOUHOU_EXPORT int touhou_robust_survival_viability_v1(
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
    return touhou_native_impl_robust_survival_viability_v1(
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
        state_survival_frames,
        state_bottleneck_margins,
        best_action_masks,
        viable,
        safe_action_masks
    );
}

TOUHOU_EXPORT int touhou_losing_survival_labels_v1(
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
) {
    return touhou_native_impl_losing_survival_labels_v1(
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
        requested_worker_count,
        viable,
        safe_action_masks,
        state_survival_frames,
        state_bottleneck_margins,
        best_action_masks
    );
}
