// Research-only C ABI for same-process stationary-witness benchmarks.
//
// This translation unit is built into a separate test library.  None of
// these symbols belong to the production touhou_native ABI.

#include <cstdint>

#include "src/internal/pipeline_impl.hpp"

#if defined(_WIN32)
#define TOUHOU_BENCHMARK_EXPORT extern "C" __declspec(dllexport)
#else
#define TOUHOU_BENCHMARK_EXPORT \
    extern "C" __attribute__((visibility("default")))
#endif

TOUHOU_BENCHMARK_EXPORT int
touhou_benchmark_belief_workspace_create_v1(
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

TOUHOU_BENCHMARK_EXPORT int
touhou_benchmark_belief_workspace_stationary_witness_v1(
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
) {
    return touhou_native_impl_belief_pipeline_workspace_stationary_witness_v1(
        workspace,
        start_frame,
        start_row,
        start_column,
        observed_action,
        pending_action,
        pending_remaining_frames,
        pending_remaining_count,
        root_action,
        timeout_ms,
        output_steps,
        step_capacity,
        output_step_count,
        output_frames,
        output_margin,
        output_evaluated_state_count
    );
}

TOUHOU_BENCHMARK_EXPORT int
touhou_benchmark_belief_workspace_cancel_v1(void* workspace) {
    return touhou_native_impl_belief_pipeline_workspace_cancel_v1(workspace);
}

TOUHOU_BENCHMARK_EXPORT void
touhou_benchmark_belief_workspace_destroy_v1(void* workspace) {
    touhou_native_impl_belief_pipeline_workspace_destroy_v1(workspace);
}

TOUHOU_BENCHMARK_EXPORT int
touhou_benchmark_stationary_witness_step_size_v1() {
    return static_cast<int>(sizeof(BeliefStationaryWitnessStepV1));
}
