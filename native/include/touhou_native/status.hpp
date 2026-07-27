#pragma once

#include <cstdint>
#include <limits>

namespace touhou_native {

inline constexpr int PIPELINE_MAX_ACTIONS = 32;
inline constexpr int BELIEF_PIPELINE_MAX_ACTIONS = 64;
inline constexpr int PIPELINE_MAX_DELAYS = 64;
inline constexpr int PIPELINE_MAX_DECISION_FRAMES = 16;
inline constexpr int PIPELINE_MAX_BRANCHES =
    PIPELINE_MAX_DELAYS * PIPELINE_MAX_DECISION_FRAMES;
inline constexpr int PIPELINE_RESULT_CANCELLED = 5;
inline constexpr int PIPELINE_RESULT_DEADLINE = 6;
inline constexpr std::uint64_t PIPELINE_EMPTY_KEY =
    std::numeric_limits<std::uint64_t>::max();

struct PipelineCancelledSignal {};
struct PipelineDeadlineSignal {};

}  // namespace touhou_native
