#include <cstdint>

#include "include/touhou_native/abi.h"
#include "include/touhou_native/export.hpp"
#include "src/internal/abi_impl.hpp"

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
    return touhou_native_impl_query_local_survival_v1(
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
        output_evaluated_state_count
    );
}
