#pragma once

#include <atomic>
#include <chrono>
#include <cstdint>

namespace touhou_native {

struct LocalHazardStopContext {
    const std::atomic<std::uint64_t>* cancel_generation = nullptr;
    std::uint64_t expected_generation = 0;
    bool deadline_enabled = false;
    std::chrono::steady_clock::time_point deadline{};
};

inline thread_local LocalHazardStopContext local_hazard_stop_context;

inline int local_hazard_stop_status() {
    if (
        local_hazard_stop_context.cancel_generation != nullptr
        && local_hazard_stop_context.cancel_generation->load(
            std::memory_order_relaxed
        ) != local_hazard_stop_context.expected_generation
    ) {
        return 5;
    }
    if (
        local_hazard_stop_context.deadline_enabled
        && std::chrono::steady_clock::now()
            >= local_hazard_stop_context.deadline
    ) {
        return 6;
    }
    return 0;
}

class ScopedLocalHazardStopContext {
public:
    explicit ScopedLocalHazardStopContext(
        LocalHazardStopContext context
    )
        : previous_(local_hazard_stop_context) {
        local_hazard_stop_context = context;
    }

    ~ScopedLocalHazardStopContext() {
        local_hazard_stop_context = previous_;
    }

private:
    LocalHazardStopContext previous_;
};

}  // namespace touhou_native

