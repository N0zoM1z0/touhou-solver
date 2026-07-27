#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <limits>
#include <mutex>
#include <vector>

#include "include/touhou_native/export.hpp"
#include "include/touhou_native/local_hazard_stop.hpp"

using touhou_native::ScopedLocalHazardStopContext;
using touhou_native::local_hazard_stop_status;

extern "C" int touhou_local_hazards_v1(
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

extern "C" int touhou_local_supplemental_beam_reduce_v1(
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

namespace {

struct LocalSupplementalNode {
    double x;
    double y;
    std::int32_t first_action;
    std::int32_t last_action;
    double risk;
    std::int32_t collisions;
    double minimum_clearance;
    double immediate_clearance;
};

struct LocalSupplementalWorkspace {
    std::atomic<std::uint64_t> cancel_generation{0};
    std::atomic<bool> active{false};
    std::mutex query_mutex;
    std::vector<LocalSupplementalNode> beam;
    std::vector<LocalSupplementalNode> candidates;
    std::vector<float> positions_x;
    std::vector<float> positions_y;
    std::vector<double> candidate_x;
    std::vector<double> candidate_y;
    std::vector<std::int32_t> first_action;
    std::vector<std::int32_t> last_direction;
    std::vector<std::uint8_t> last_focused;
    std::vector<std::uint32_t> collected_mask;
    std::vector<double> risk;
    std::vector<std::int32_t> collisions;
    std::vector<double> minimum_clearance;
    std::vector<double> hazard_risk;
    std::vector<std::int32_t> hazard_collisions;
    std::vector<double> hazard_minimum;
    std::vector<std::int32_t> retained_indices;
    std::vector<float> body_x;
    std::vector<float> body_y;
};

class ScopedLocalSupplementalActive {
public:
    explicit ScopedLocalSupplementalActive(
        LocalSupplementalWorkspace& workspace
    )
        : workspace_(workspace) {
        workspace_.active.store(true, std::memory_order_release);
    }

    ~ScopedLocalSupplementalActive() {
        workspace_.active.store(false, std::memory_order_release);
    }

private:
    LocalSupplementalWorkspace& workspace_;
};

inline bool local_directions_opposed(
    std::int32_t left,
    std::int32_t right
) {
    constexpr std::int32_t up_bit = 0x10;
    constexpr std::int32_t down_bit = 0x20;
    constexpr std::int32_t left_bit = 0x40;
    constexpr std::int32_t right_bit = 0x80;
    return (
        ((left & left_bit) != 0 && (right & right_bit) != 0)
        || ((left & right_bit) != 0 && (right & left_bit) != 0)
        || ((left & up_bit) != 0 && (right & down_bit) != 0)
        || ((left & down_bit) != 0 && (right & up_bit) != 0)
    );
}

inline double local_supplemental_boundary_risk(
    double x,
    double y,
    double playfield_left,
    double playfield_right,
    double playfield_top,
    double playfield_bottom
) {
    const double horizontal = std::min(
        x - playfield_left,
        playfield_right - x
    );
    const double vertical = std::min(
        y - playfield_top,
        playfield_bottom - y
    );
    double risk = 0.0;
    if (horizontal < 12.0) {
        const double distance = 12.0 - horizontal;
        risk += 2.0 * distance * distance;
    }
    if (vertical < 12.0) {
        const double distance = 12.0 - vertical;
        risk += 3.0 * distance * distance;
    }
    if (horizontal < 20.0 && vertical < 20.0) {
        risk += (20.0 - horizontal) * (20.0 - vertical);
    }
    return risk;
}

inline bool local_supplemental_offsets_valid(
    const std::int32_t* offsets,
    int horizon
) {
    if (offsets == nullptr || offsets[0] != 0) {
        return false;
    }
    for (int step = 0; step < horizon; ++step) {
        if (offsets[step] < 0 || offsets[step + 1] < offsets[step]) {
            return false;
        }
    }
    return true;
}

template <typename Value>
inline const Value* local_supplemental_offset_pointer(
    const Value* values,
    std::int32_t offset,
    int count
) {
    return count == 0 ? nullptr : values + offset;
}

}  // namespace

struct TouhouLocalSupplementalQueryV1 {
    std::uint32_t struct_size;
    int horizon;
    int action_hold_frames;
    int beam_width;
    int control_delay_frames;
    int action_count;
    double initial_x;
    double initial_y;
    std::int32_t initial_first_action;
    std::int32_t initial_last_action;
    double initial_risk;
    std::int32_t initial_collisions;
    double initial_minimum_clearance;
    double initial_immediate_clearance;
    const std::int32_t* action_direction;
    const double* action_dx;
    const double* action_dy;
    const std::uint8_t* action_focused;
    const std::uint8_t* action_allowed;
    const std::int32_t* certificate_collisions;
    const double* certificate_minimum;
    const std::uint8_t* survival_preferred;
    const std::uint8_t* safety_preferred;
    const double* recovery_distance;
    const std::int32_t* repair_volume;
    const std::int32_t* bullet_offsets;
    const float* bullet_x;
    const float* bullet_y;
    const float* bullet_half_width;
    const float* bullet_half_height;
    const std::uint8_t* bullet_transformed;
    const std::int32_t* laser_offsets;
    const float* laser_start_x;
    const float* laser_start_y;
    const float* laser_segment_x;
    const float* laser_segment_y;
    const float* laser_collision_radius;
    const float* laser_base_uncertainty;
    const float* laser_uncertainty_per_frame;
    int body_count;
    const float* body_base_x;
    const float* body_base_y;
    const float* body_velocity_x;
    const float* body_velocity_y;
    const float* body_half_width;
    const float* body_half_height;
    float player_radius;
    int preserve_previous_direction_inertia;
    std::int32_t previous_direction;
    std::uint8_t previous_focused;
    int target_enabled;
    double target_x;
    double target_y;
    int target_deadline;
    double item_safety_clearance;
    double playfield_left;
    double playfield_right;
    double playfield_top;
    double playfield_bottom;
    double recovery_reserve_distance;
    double supplemental_reserve_distance;
    double diagonal_speed;
    double cardinal_speed;
    std::uint64_t timeout_nanoseconds;
};

struct TouhouLocalSupplementalOutputV1 {
    std::uint32_t struct_size;
    int capacity;
    double* x;
    double* y;
    std::int32_t* first_action;
    std::int32_t* last_action;
    double* risk;
    std::int32_t* collisions;
    double* minimum_clearance;
    double* immediate_clearance;
    std::int32_t* count;
};

TOUHOU_EXPORT int touhou_local_supplemental_workspace_create_v1(
    void** output_workspace
) {
    if (output_workspace == nullptr) {
        return -1;
    }
    try {
        *output_workspace = new LocalSupplementalWorkspace();
    } catch (...) {
        *output_workspace = nullptr;
        return -2;
    }
    return 0;
}

TOUHOU_EXPORT int touhou_local_supplemental_workspace_cancel_v1(
    void* workspace_pointer
) {
    if (workspace_pointer == nullptr) {
        return -1;
    }
    auto* workspace = static_cast<LocalSupplementalWorkspace*>(
        workspace_pointer
    );
    workspace->cancel_generation.fetch_add(1, std::memory_order_relaxed);
    return 0;
}

TOUHOU_EXPORT int touhou_local_supplemental_workspace_active_v1(
    void* workspace_pointer,
    int* output_active
) {
    if (workspace_pointer == nullptr || output_active == nullptr) {
        return -1;
    }
    auto* workspace = static_cast<LocalSupplementalWorkspace*>(
        workspace_pointer
    );
    *output_active = (
        workspace->active.load(std::memory_order_acquire) ? 1 : 0
    );
    return 0;
}

TOUHOU_EXPORT int touhou_local_supplemental_workspace_destroy_v1(
    void* workspace_pointer
) {
    if (workspace_pointer == nullptr) {
        return 0;
    }
    auto* workspace = static_cast<LocalSupplementalWorkspace*>(
        workspace_pointer
    );
    workspace->query_mutex.lock();
    workspace->query_mutex.unlock();
    delete workspace;
    return 0;
}

TOUHOU_EXPORT int touhou_local_supplemental_workspace_query_v1(
    void* workspace_pointer,
    const TouhouLocalSupplementalQueryV1* query,
    TouhouLocalSupplementalOutputV1* output
) {
    if (
        workspace_pointer == nullptr
        || query == nullptr
        || output == nullptr
        || query->struct_size != sizeof(TouhouLocalSupplementalQueryV1)
        || output->struct_size != sizeof(TouhouLocalSupplementalOutputV1)
        || output->count == nullptr
    ) {
        return -1;
    }
    *output->count = 0;
    const auto deadline = (
        query->timeout_nanoseconds == 0
        ? std::chrono::steady_clock::time_point::max()
        : std::chrono::steady_clock::now()
            + std::chrono::nanoseconds(query->timeout_nanoseconds)
    );
    auto* workspace = static_cast<LocalSupplementalWorkspace*>(
        workspace_pointer
    );
    std::lock_guard<std::mutex> lock(workspace->query_mutex);
    const std::uint64_t generation = workspace->cancel_generation.load(
        std::memory_order_relaxed
    );
    const ScopedLocalSupplementalActive active_scope(*workspace);
    const ScopedLocalHazardStopContext scoped_stop(
        {
            &workspace->cancel_generation,
            generation,
            query->timeout_nanoseconds != 0,
            deadline,
        }
    );
    const auto stopped = []() {
        return local_hazard_stop_status();
    };
    {
        const int status = stopped();
        if (status != 0) {
            return status;
        }
    }
    if (
        query->horizon <= 0
        || query->action_hold_frames <= 0
        || query->beam_width <= 0
        || query->action_count <= 0
        || query->action_count > 64
        || query->control_delay_frames < 0
        || query->body_count < 0
        || output->capacity < query->beam_width
        || output->x == nullptr
        || output->y == nullptr
        || output->first_action == nullptr
        || output->last_action == nullptr
        || output->risk == nullptr
        || output->collisions == nullptr
        || output->minimum_clearance == nullptr
        || output->immediate_clearance == nullptr
        || query->action_direction == nullptr
        || query->action_dx == nullptr
        || query->action_dy == nullptr
        || query->action_focused == nullptr
        || query->action_allowed == nullptr
        || query->certificate_collisions == nullptr
        || query->certificate_minimum == nullptr
        || query->survival_preferred == nullptr
        || query->safety_preferred == nullptr
        || query->recovery_distance == nullptr
        || query->repair_volume == nullptr
        || !local_supplemental_offsets_valid(
            query->bullet_offsets,
            query->horizon
        )
        || !local_supplemental_offsets_valid(
            query->laser_offsets,
            query->horizon
        )
        || !std::isfinite(query->player_radius)
        || query->player_radius < 0.0F
        || !std::isfinite(query->initial_x)
        || !std::isfinite(query->initial_y)
        || !std::isfinite(query->initial_risk)
        || query->initial_collisions < 0
        || std::isnan(query->initial_minimum_clearance)
        || std::isnan(query->initial_immediate_clearance)
        || query->initial_last_action < 0
        || query->initial_last_action >= query->action_count
        || query->initial_first_action < 0
        || query->initial_first_action >= query->action_count
        || !std::isfinite(query->playfield_left)
        || !std::isfinite(query->playfield_right)
        || !std::isfinite(query->playfield_top)
        || !std::isfinite(query->playfield_bottom)
        || query->playfield_left > query->playfield_right
        || query->playfield_top > query->playfield_bottom
        || !std::isfinite(query->item_safety_clearance)
        || !std::isfinite(query->recovery_reserve_distance)
        || query->recovery_reserve_distance < 0.0
        || !std::isfinite(query->supplemental_reserve_distance)
        || query->supplemental_reserve_distance < 0.0
        || !std::isfinite(query->diagonal_speed)
        || query->diagonal_speed <= 0.0
        || !std::isfinite(query->cardinal_speed)
        || query->cardinal_speed <= 0.0
        || (
            query->target_enabled != 0
            && (
                !std::isfinite(query->target_x)
                || !std::isfinite(query->target_y)
                || query->target_deadline < 0
            )
        )
    ) {
        return -2;
    }
    const int bullet_total = query->bullet_offsets[query->horizon];
    const int laser_total = query->laser_offsets[query->horizon];
    if (
        (
            bullet_total > 0
            && (
                query->bullet_x == nullptr
                || query->bullet_y == nullptr
                || query->bullet_half_width == nullptr
                || query->bullet_half_height == nullptr
                || query->bullet_transformed == nullptr
            )
        )
        || (
            laser_total > 0
            && (
                query->laser_start_x == nullptr
                || query->laser_start_y == nullptr
                || query->laser_segment_x == nullptr
                || query->laser_segment_y == nullptr
                || query->laser_collision_radius == nullptr
                || query->laser_base_uncertainty == nullptr
                || query->laser_uncertainty_per_frame == nullptr
            )
        )
        || (
            query->body_count > 0
            && (
                query->body_base_x == nullptr
                || query->body_base_y == nullptr
                || query->body_velocity_x == nullptr
                || query->body_velocity_y == nullptr
                || query->body_half_width == nullptr
                || query->body_half_height == nullptr
            )
        )
    ) {
        return -3;
    }
    bool any_allowed = false;
    for (int action = 0; action < query->action_count; ++action) {
        any_allowed = any_allowed || query->action_allowed[action] != 0;
        if (
            !std::isfinite(query->action_dx[action])
            || !std::isfinite(query->action_dy[action])
            || query->certificate_collisions[action] < 0
            || std::isnan(query->certificate_minimum[action])
            || std::isnan(query->recovery_distance[action])
            || query->repair_volume[action] < 0
        ) {
            return -4;
        }
    }
    if (!any_allowed) {
        return -5;
    }

    try {
        workspace->beam.clear();
        workspace->beam.push_back(
            {
                query->initial_x,
                query->initial_y,
                query->initial_first_action,
                query->initial_last_action,
                query->initial_risk,
                query->initial_collisions,
                query->initial_minimum_clearance,
                query->initial_immediate_clearance,
            }
        );
        workspace->body_x.resize(
            static_cast<std::size_t>(query->body_count)
        );
        workspace->body_y.resize(
            static_cast<std::size_t>(query->body_count)
        );
        for (int step = 1; step <= query->horizon; ++step) {
            {
                const int status = stopped();
                if (status != 0) {
                    return status;
                }
            }
            workspace->candidates.clear();
            workspace->candidates.reserve(
                workspace->beam.size()
                * static_cast<std::size_t>(query->action_count)
            );
            for (const LocalSupplementalNode& node : workspace->beam) {
                for (
                    int action_index = 0;
                    action_index < query->action_count;
                    ++action_index
                ) {
                    const bool action_boundary = (
                        (step - 1) % query->action_hold_frames == 0
                    );
                    const bool rejected = (
                        step == 1
                        ? query->action_allowed[action_index] == 0
                        : (
                            !action_boundary
                            && action_index != node.last_action
                        )
                    );
                    if (rejected) {
                        continue;
                    }
                    if (
                        (workspace->candidates.size() & 63U) == 0U
                    ) {
                        const int status = stopped();
                        if (status != 0) {
                            return status;
                        }
                    }
                    const double x = std::min(
                        query->playfield_right,
                        std::max(
                            query->playfield_left,
                            node.x + query->action_dx[action_index]
                        )
                    );
                    const double y = std::min(
                        query->playfield_bottom,
                        std::max(
                            query->playfield_top,
                            node.y + query->action_dy[action_index]
                        )
                    );
                    double transition_risk = (
                        local_supplemental_boundary_risk(
                            x,
                            y,
                            query->playfield_left,
                            query->playfield_right,
                            query->playfield_top,
                            query->playfield_bottom
                        )
                    );
                    const std::int32_t direction = (
                        query->action_direction[action_index]
                    );
                    const std::int32_t last_direction = (
                        query->action_direction[node.last_action]
                    );
                    if (direction != last_direction) {
                        transition_risk += 0.08;
                    }
                    if (
                        local_directions_opposed(
                            direction,
                            last_direction
                        )
                    ) {
                        transition_risk += 24.0;
                    }
                    if (
                        query->action_focused[action_index]
                        != query->action_focused[node.last_action]
                    ) {
                        transition_risk += 0.12;
                    }
                    if (
                        step == 1
                        && query->preserve_previous_direction_inertia != 0
                    ) {
                        if (direction != query->previous_direction) {
                            transition_risk += 0.08;
                        }
                        if (
                            local_directions_opposed(
                                direction,
                                query->previous_direction
                            )
                        ) {
                            transition_risk += 24.0;
                        }
                        if (
                            query->action_focused[action_index]
                            != query->previous_focused
                        ) {
                            transition_risk += 0.12;
                        }
                    }
                    workspace->candidates.push_back(
                        {
                            x,
                            y,
                            step == 1
                                ? action_index
                                : node.first_action,
                            action_index,
                            node.risk + transition_risk,
                            node.collisions,
                            node.minimum_clearance,
                            node.immediate_clearance,
                        }
                    );
                }
            }
            const std::size_t draft_count = workspace->candidates.size();
            if (draft_count == 0) {
                return -6;
            }
            workspace->positions_x.resize(draft_count);
            workspace->positions_y.resize(draft_count);
            workspace->hazard_risk.resize(draft_count);
            workspace->hazard_collisions.resize(draft_count);
            workspace->hazard_minimum.resize(draft_count);
            for (std::size_t draft = 0; draft < draft_count; ++draft) {
                workspace->positions_x[draft] = static_cast<float>(
                    workspace->candidates[draft].x
                );
                workspace->positions_y[draft] = static_cast<float>(
                    workspace->candidates[draft].y
                );
            }
            const int absolute_step = query->control_delay_frames + step;
            for (int body = 0; body < query->body_count; ++body) {
                workspace->body_x[static_cast<std::size_t>(body)] = (
                    query->body_base_x[body]
                    + query->body_velocity_x[body]
                        * static_cast<float>(absolute_step)
                );
                workspace->body_y[static_cast<std::size_t>(body)] = (
                    query->body_base_y[body]
                    + query->body_velocity_y[body]
                        * static_cast<float>(absolute_step)
                );
            }
            const std::int32_t bullet_begin = (
                query->bullet_offsets[step - 1]
            );
            const int bullet_count = (
                query->bullet_offsets[step] - bullet_begin
            );
            const std::int32_t laser_begin = (
                query->laser_offsets[step - 1]
            );
            const int laser_count = (
                query->laser_offsets[step] - laser_begin
            );
            const int hazard_result = touhou_local_hazards_v1(
                workspace->positions_x.data(),
                workspace->positions_y.data(),
                static_cast<int>(draft_count),
                absolute_step,
                query->player_radius,
                local_supplemental_offset_pointer(
                    query->bullet_x,
                    bullet_begin,
                    bullet_count
                ),
                local_supplemental_offset_pointer(
                    query->bullet_y,
                    bullet_begin,
                    bullet_count
                ),
                local_supplemental_offset_pointer(
                    query->bullet_half_width,
                    bullet_begin,
                    bullet_count
                ),
                local_supplemental_offset_pointer(
                    query->bullet_half_height,
                    bullet_begin,
                    bullet_count
                ),
                local_supplemental_offset_pointer(
                    query->bullet_transformed,
                    bullet_begin,
                    bullet_count
                ),
                bullet_count,
                local_supplemental_offset_pointer(
                    query->laser_start_x,
                    laser_begin,
                    laser_count
                ),
                local_supplemental_offset_pointer(
                    query->laser_start_y,
                    laser_begin,
                    laser_count
                ),
                local_supplemental_offset_pointer(
                    query->laser_segment_x,
                    laser_begin,
                    laser_count
                ),
                local_supplemental_offset_pointer(
                    query->laser_segment_y,
                    laser_begin,
                    laser_count
                ),
                local_supplemental_offset_pointer(
                    query->laser_collision_radius,
                    laser_begin,
                    laser_count
                ),
                local_supplemental_offset_pointer(
                    query->laser_base_uncertainty,
                    laser_begin,
                    laser_count
                ),
                local_supplemental_offset_pointer(
                    query->laser_uncertainty_per_frame,
                    laser_begin,
                    laser_count
                ),
                laser_count,
                query->body_count == 0
                    ? nullptr
                    : workspace->body_x.data(),
                query->body_count == 0
                    ? nullptr
                    : workspace->body_y.data(),
                query->body_half_width,
                query->body_half_height,
                query->body_count,
                workspace->hazard_risk.data(),
                workspace->hazard_collisions.data(),
                workspace->hazard_minimum.data()
            );
            if (hazard_result != 0) {
                return hazard_result;
            }

            workspace->candidate_x.resize(draft_count);
            workspace->candidate_y.resize(draft_count);
            workspace->first_action.resize(draft_count);
            workspace->last_direction.resize(draft_count);
            workspace->last_focused.resize(draft_count);
            workspace->collected_mask.assign(draft_count, 0);
            workspace->risk.resize(draft_count);
            workspace->collisions.resize(draft_count);
            workspace->minimum_clearance.resize(draft_count);
            for (std::size_t draft = 0; draft < draft_count; ++draft) {
                LocalSupplementalNode& node = (
                    workspace->candidates[draft]
                );
                node.risk += workspace->hazard_risk[draft];
                node.collisions += workspace->hazard_collisions[draft];
                node.minimum_clearance = std::min(
                    node.minimum_clearance,
                    workspace->hazard_minimum[draft]
                );
                if (step == 1) {
                    node.immediate_clearance = std::min(
                        node.immediate_clearance,
                        workspace->hazard_minimum[draft]
                    );
                }
                workspace->candidate_x[draft] = node.x;
                workspace->candidate_y[draft] = node.y;
                workspace->first_action[draft] = node.first_action;
                workspace->last_direction[draft] = (
                    query->action_direction[node.last_action]
                );
                workspace->last_focused[draft] = (
                    query->action_focused[node.last_action]
                );
                workspace->risk[draft] = node.risk;
                workspace->collisions[draft] = node.collisions;
                workspace->minimum_clearance[draft] = (
                    node.minimum_clearance
                );
            }
            workspace->retained_indices.resize(
                static_cast<std::size_t>(
                    std::min(
                        query->beam_width,
                        static_cast<int>(draft_count)
                    )
                )
            );
            std::int32_t retained_count = 0;
            const int reduce_result = (
                touhou_local_supplemental_beam_reduce_v1(
                    workspace->candidate_x.data(),
                    workspace->candidate_y.data(),
                    workspace->first_action.data(),
                    workspace->last_direction.data(),
                    workspace->last_focused.data(),
                    workspace->collected_mask.data(),
                    workspace->risk.data(),
                    workspace->collisions.data(),
                    workspace->minimum_clearance.data(),
                    static_cast<int>(draft_count),
                    step,
                    query->beam_width,
                    0.5,
                    query->target_enabled,
                    query->target_x,
                    query->target_y,
                    query->target_deadline,
                    query->item_safety_clearance,
                    query->playfield_left,
                    query->playfield_right,
                    query->playfield_top,
                    query->playfield_bottom,
                    query->recovery_reserve_distance,
                    query->supplemental_reserve_distance,
                    query->diagonal_speed,
                    query->cardinal_speed,
                    query->certificate_collisions,
                    query->certificate_minimum,
                    query->survival_preferred,
                    query->safety_preferred,
                    query->recovery_distance,
                    query->repair_volume,
                    query->action_count,
                    workspace->retained_indices.data(),
                    &retained_count
                )
            );
            if (reduce_result != 0) {
                return -100 + reduce_result;
            }
            {
                const int status = stopped();
                if (status != 0) {
                    return status;
                }
            }
            workspace->beam.clear();
            workspace->beam.reserve(
                static_cast<std::size_t>(retained_count)
            );
            for (int retained = 0; retained < retained_count; ++retained) {
                const std::int32_t candidate = (
                    workspace->retained_indices[
                        static_cast<std::size_t>(retained)
                    ]
                );
                if (
                    candidate < 0
                    || static_cast<std::size_t>(candidate) >= draft_count
                ) {
                    return -7;
                }
                workspace->beam.push_back(
                    workspace->candidates[
                        static_cast<std::size_t>(candidate)
                    ]
                );
            }
        }
    } catch (...) {
        return -8;
    }

    {
        const int status = stopped();
        if (status != 0) {
            return status;
        }
    }
    if (
        workspace->beam.empty()
        || static_cast<int>(workspace->beam.size()) > output->capacity
    ) {
        return -9;
    }
    for (std::size_t index = 0; index < workspace->beam.size(); ++index) {
        const LocalSupplementalNode& node = workspace->beam[index];
        output->x[index] = node.x;
        output->y[index] = node.y;
        output->first_action[index] = node.first_action;
        output->last_action[index] = node.last_action;
        output->risk[index] = node.risk;
        output->collisions[index] = node.collisions;
        output->minimum_clearance[index] = node.minimum_clearance;
        output->immediate_clearance[index] = node.immediate_clearance;
    }
    *output->count = static_cast<std::int32_t>(workspace->beam.size());
    return 0;
}
