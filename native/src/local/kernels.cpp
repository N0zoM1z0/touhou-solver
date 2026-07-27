#include <algorithm>
#include <atomic>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <functional>
#include <limits>
#include <memory>
#include <mutex>
#include <thread>
#include <unordered_map>
#include <vector>

#include "include/touhou_native/export.hpp"
#include "include/touhou_native/local_hazard_stop.hpp"

using touhou_native::local_hazard_stop_status;

TOUHOU_EXPORT int touhou_local_hazards_v1(
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
) {
    if (
        positions_x == nullptr
        || positions_y == nullptr
        || output_risk == nullptr
        || output_collisions == nullptr
        || output_minimum == nullptr
        || position_count <= 0
        || step <= 0
        || !std::isfinite(player_radius)
        || player_radius < 0.0F
        || bullet_count < 0
        || laser_count < 0
        || body_count < 0
    ) {
        return -1;
    }
    if (
        (
            bullet_count > 0
            && (
                bullet_x == nullptr
                || bullet_y == nullptr
                || bullet_half_width == nullptr
                || bullet_half_height == nullptr
                || bullet_transformed == nullptr
            )
        )
        || (
            laser_count > 0
            && (
                laser_start_x == nullptr
                || laser_start_y == nullptr
                || laser_segment_x == nullptr
                || laser_segment_y == nullptr
                || laser_collision_radius == nullptr
                || laser_base_uncertainty == nullptr
                || laser_uncertainty_per_frame == nullptr
            )
        )
        || (
            body_count > 0
            && (
                body_x == nullptr
                || body_y == nullptr
                || body_half_width == nullptr
                || body_half_height == nullptr
            )
        )
    ) {
        return -2;
    }

    float position_min_x = positions_x[0];
    float position_max_x = positions_x[0];
    float position_min_y = positions_y[0];
    float position_max_y = positions_y[0];
    for (int position = 0; position < position_count; ++position) {
        if ((position & 63) == 0) {
            const int stop = local_hazard_stop_status();
            if (stop != 0) {
                return stop;
            }
        }
        if (
            !std::isfinite(positions_x[position])
            || !std::isfinite(positions_y[position])
        ) {
            return -3;
        }
        position_min_x = std::min(
            position_min_x,
            positions_x[position]
        );
        position_max_x = std::max(
            position_max_x,
            positions_x[position]
        );
        position_min_y = std::min(
            position_min_y,
            positions_y[position]
        );
        position_max_y = std::max(
            position_max_y,
            positions_y[position]
        );
        output_risk[position] = 0.0;
        output_collisions[position] = 0;
        output_minimum[position] = std::numeric_limits<double>::infinity();
    }
    const double time_weight = 1.0 / (
        1.0 + 0.08 * static_cast<double>(step - 1)
    );

    const float bullet_margin = 84.0F;
    const float base_bullet_uncertainty = (
        0.2F * std::sqrt(static_cast<float>(step))
    );
    const float transformed_uncertainty = std::min(
        10.0F,
        3.0F + 0.35F * static_cast<float>(step)
    );
    std::vector<float> bullet_risk_sum(
        static_cast<std::size_t>(position_count),
        0.0F
    );
    for (int bullet = 0; bullet < bullet_count; ++bullet) {
        if ((bullet & 63) == 0) {
            const int stop = local_hazard_stop_status();
            if (stop != 0) {
                return stop;
            }
        }
        if (
            bullet_x[bullet] < position_min_x - bullet_margin
            || bullet_x[bullet] > position_max_x + bullet_margin
            || bullet_y[bullet] < position_min_y - bullet_margin
            || bullet_y[bullet] > position_max_y + bullet_margin
        ) {
            continue;
        }
        const float uncertainty = (
            base_bullet_uncertainty
            + (
                bullet_transformed[bullet] != 0
                ? transformed_uncertainty
                : 0.0F
            )
        );
        for (int position = 0; position < position_count; ++position) {
            if (
                bullet_x[bullet]
                    < positions_x[position] - bullet_margin
                || bullet_x[bullet]
                    > positions_x[position] + bullet_margin
                || bullet_y[bullet]
                    < positions_y[position] - bullet_margin
                || bullet_y[bullet]
                    > positions_y[position] + bullet_margin
            ) {
                continue;
            }
            const float dx = (
                std::fabs(positions_x[position] - bullet_x[bullet])
                - (player_radius + bullet_half_width[bullet])
            );
            const float dy = (
                std::fabs(positions_y[position] - bullet_y[bullet])
                - (player_radius + bullet_half_height[bullet])
            );
            const bool overlap = dx <= 0.0F && dy <= 0.0F;
            const float clearance = overlap
                ? std::max(dx, dy)
                : std::hypot(
                    std::max(dx, 0.0F),
                    std::max(dy, 0.0F)
                );
            if (clearance <= 0.0F) {
                ++output_collisions[position];
            }
            const float robust_clearance = clearance - uncertainty;
            output_minimum[position] = std::min(
                output_minimum[position],
                static_cast<double>(robust_clearance)
            );
            const float danger = std::max(
                44.0F - robust_clearance,
                0.0F
            );
            bullet_risk_sum[position] += danger * danger;
        }
    }
    for (int position = 0; position < position_count; ++position) {
        output_risk[position] += (
            static_cast<double>(bullet_risk_sum[position])
            * time_weight
        );
    }

    const float laser_margin = 56.0F;
    std::vector<float> laser_risk_sum(
        static_cast<std::size_t>(position_count),
        0.0F
    );
    for (int laser = 0; laser < laser_count; ++laser) {
        if ((laser & 63) == 0) {
            const int stop = local_hazard_stop_status();
            if (stop != 0) {
                return stop;
            }
        }
        const float uncertainty = (
            laser_base_uncertainty[laser]
            + std::min(
                6.0F,
                laser_uncertainty_per_frame[laser]
                    * static_cast<float>(step)
            )
        );
        const float occupied_radius = (
            laser_collision_radius[laser] + uncertainty
        );
        const float end_x = (
            laser_start_x[laser] + laser_segment_x[laser]
        );
        const float end_y = (
            laser_start_y[laser] + laser_segment_y[laser]
        );
        const float min_x = std::min(laser_start_x[laser], end_x);
        const float max_x = std::max(laser_start_x[laser], end_x);
        const float min_y = std::min(laser_start_y[laser], end_y);
        const float max_y = std::max(laser_start_y[laser], end_y);
        if (
            max_x + occupied_radius
                < position_min_x - laser_margin
            || min_x - occupied_radius
                > position_max_x + laser_margin
            || max_y + occupied_radius
                < position_min_y - laser_margin
            || min_y - occupied_radius
                > position_max_y + laser_margin
        ) {
            continue;
        }
        const float length_squared = (
            laser_segment_x[laser] * laser_segment_x[laser]
            + laser_segment_y[laser] * laser_segment_y[laser]
        );
        for (int position = 0; position < position_count; ++position) {
            if (
                max_x + occupied_radius
                    < positions_x[position] - laser_margin
                || min_x - occupied_radius
                    > positions_x[position] + laser_margin
                || max_y + occupied_radius
                    < positions_y[position] - laser_margin
                || min_y - occupied_radius
                    > positions_y[position] + laser_margin
            ) {
                continue;
            }
            float projection = 0.0F;
            if (length_squared > 1e-9F) {
                projection = (
                    (
                        positions_x[position] - laser_start_x[laser]
                    ) * laser_segment_x[laser]
                    + (
                        positions_y[position] - laser_start_y[laser]
                    ) * laser_segment_y[laser]
                ) / length_squared;
            }
            projection = std::min(
                1.0F,
                std::max(0.0F, projection)
            );
            const float distance = std::hypot(
                positions_x[position]
                    - (
                        laser_start_x[laser]
                        + projection * laser_segment_x[laser]
                    ),
                positions_y[position]
                    - (
                        laser_start_y[laser]
                        + projection * laser_segment_y[laser]
                    )
            );
            const float clearance = (
                distance - laser_collision_radius[laser]
            );
            if (clearance <= 0.0F) {
                ++output_collisions[position];
            }
            const float robust_clearance = clearance - uncertainty;
            output_minimum[position] = std::min(
                output_minimum[position],
                static_cast<double>(robust_clearance)
            );
            const float danger = std::max(
                56.0F - robust_clearance,
                0.0F
            );
            laser_risk_sum[position] += danger * danger;
        }
    }
    for (int position = 0; position < position_count; ++position) {
        output_risk[position] += (
            2.0
            * static_cast<double>(laser_risk_sum[position])
            * time_weight
        );
    }

    const float body_step_uncertainty = std::min(
        12.0F,
        0.5F * static_cast<float>(step)
    );
    std::vector<float> body_risk_sum(
        static_cast<std::size_t>(position_count),
        0.0F
    );
    for (int body = 0; body < body_count; ++body) {
        if ((body & 63) == 0) {
            const int stop = local_hazard_stop_status();
            if (stop != 0) {
                return stop;
            }
        }
        for (int position = 0; position < position_count; ++position) {
            const float dx = (
                std::fabs(positions_x[position] - body_x[body])
                - (player_radius + body_half_width[body])
            );
            const float dy = (
                std::fabs(positions_y[position] - body_y[body])
                - (player_radius + body_half_height[body])
            );
            const bool overlap = dx <= 0.0F && dy <= 0.0F;
            const float clearance = overlap
                ? std::max(dx, dy)
                : std::hypot(
                    std::max(dx, 0.0F),
                    std::max(dy, 0.0F)
                );
            if (clearance <= 0.0F) {
                ++output_collisions[position];
            }
            const float robust_clearance = (
                clearance - body_step_uncertainty
            );
            output_minimum[position] = std::min(
                output_minimum[position],
                static_cast<double>(robust_clearance)
            );
            const float danger = std::max(
                64.0F - robust_clearance,
                0.0F
            );
            body_risk_sum[position] += danger * danger;
        }
    }
    for (int position = 0; position < position_count; ++position) {
        output_risk[position] += (
            2.0
            * static_cast<double>(body_risk_sum[position])
            * time_weight
        );
    }
    return local_hazard_stop_status();
}

namespace {

struct LocalBeamQuantizedKey {
    std::int64_t quantized_x;
    std::int64_t quantized_y;
    std::int32_t last_direction;
    std::uint8_t last_focused;
    std::uint32_t collected_mask;

    bool operator==(const LocalBeamQuantizedKey& other) const noexcept {
        return (
            quantized_x == other.quantized_x
            && quantized_y == other.quantized_y
            && last_direction == other.last_direction
            && last_focused == other.last_focused
            && collected_mask == other.collected_mask
        );
    }
};

struct LocalBeamQuantizedKeyHash {
    std::size_t operator()(
        const LocalBeamQuantizedKey& key
    ) const noexcept {
        std::size_t seed = std::hash<std::int64_t>{}(key.quantized_x);
        const auto combine = [&](std::size_t value) {
            seed ^= (
                value
                + static_cast<std::size_t>(0x9e3779b9U)
                + (seed << 6U)
                + (seed >> 2U)
            );
        };
        combine(std::hash<std::int64_t>{}(key.quantized_y));
        combine(std::hash<std::int32_t>{}(key.last_direction));
        combine(std::hash<std::uint8_t>{}(key.last_focused));
        combine(std::hash<std::uint32_t>{}(key.collected_mask));
        return seed;
    }
};

inline std::int64_t round_half_even(double value) {
    const double lower = std::floor(value);
    const double fraction = value - lower;
    if (fraction < 0.5) {
        return static_cast<std::int64_t>(lower);
    }
    if (fraction > 0.5) {
        return static_cast<std::int64_t>(lower + 1.0);
    }
    const auto lower_integer = static_cast<std::int64_t>(lower);
    return (
        lower_integer % 2 == 0
        ? lower_integer
        : lower_integer + 1
    );
}

template <std::size_t Size>
inline bool local_beam_key_less(
    const std::array<double, Size>& left,
    const std::array<double, Size>& right
) {
    for (std::size_t index = 0; index < left.size(); ++index) {
        if (left[index] < right[index]) {
            return true;
        }
        if (left[index] > right[index]) {
            return false;
        }
    }
    return false;
}

}  // namespace

TOUHOU_EXPORT int touhou_decode_bullet_pool_v1(
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
) {
    if (
        blob == nullptr
        || output_x == nullptr
        || output_y == nullptr
        || output_velocity_x == nullptr
        || output_velocity_y == nullptr
        || output_half_width == nullptr
        || output_half_height == nullptr
        || output_transform_flags == nullptr
        || output_slots == nullptr
        || output_speed == nullptr
        || output_angle == nullptr
        || output_callback_phase == nullptr
        || output_callback_aux == nullptr
        || output_original_transform_flags == nullptr
        || output_count == nullptr
        || record_count < 0
        || stride <= 0
        || output_capacity < record_count
    ) {
        return -1;
    }

    const auto field_fits = [stride](
        int offset,
        std::size_t width
    ) {
        return (
            offset >= 0
            && static_cast<std::uint64_t>(offset) + width
                <= static_cast<std::uint64_t>(stride)
        );
    };
    if (
        !field_fits(state_offset, sizeof(std::uint16_t))
        || !field_fits(geometry_offset, 2U * sizeof(float))
        || !field_fits(position_offset, 2U * sizeof(float))
        || !field_fits(velocity_offset, 2U * sizeof(float))
        || !field_fits(speed_offset, sizeof(float))
        || !field_fits(angle_offset, sizeof(float))
        || !field_fits(transform_flags_offset, sizeof(std::uint32_t))
        || !field_fits(
            original_transform_flags_offset,
            sizeof(std::uint32_t)
        )
        || !field_fits(callback_phase_offset, sizeof(std::int16_t))
        || !field_fits(callback_aux_offset, sizeof(std::uint8_t))
    ) {
        return -2;
    }
    const auto required_size = (
        static_cast<std::uint64_t>(record_count)
        * static_cast<std::uint64_t>(stride)
    );
    if (required_size > blob_size) {
        return -3;
    }

    std::int32_t active_count = 0;
    for (int slot = 0; slot < record_count; ++slot) {
        const auto* record = (
            blob
            + static_cast<std::uint64_t>(slot)
                * static_cast<std::uint64_t>(stride)
        );
        std::uint16_t state = 0;
        std::memcpy(
            &state,
            record + state_offset,
            sizeof(state)
        );
        if (state == 0) {
            continue;
        }

        float geometry[2] = {};
        float position[2] = {};
        float velocity[2] = {};
        std::memcpy(
            geometry,
            record + geometry_offset,
            sizeof(geometry)
        );
        std::memcpy(
            position,
            record + position_offset,
            sizeof(position)
        );
        std::memcpy(
            velocity,
            record + velocity_offset,
            sizeof(velocity)
        );
        if (
            !std::isfinite(geometry[0])
            || !std::isfinite(geometry[1])
            || !std::isfinite(position[0])
            || !std::isfinite(position[1])
            || !std::isfinite(velocity[0])
            || !std::isfinite(velocity[1])
        ) {
            continue;
        }

        const auto output = static_cast<std::size_t>(active_count);
        output_x[output] = position[0];
        output_y[output] = position[1];
        output_velocity_x[output] = velocity[0];
        output_velocity_y[output] = velocity[1];
        output_half_width[output] = std::fabs(geometry[0]) * 0.5F;
        output_half_height[output] = std::fabs(geometry[1]) * 0.5F;
        output_slots[output] = slot;
        std::memcpy(
            output_transform_flags + output,
            record + transform_flags_offset,
            sizeof(std::uint32_t)
        );
        std::memcpy(
            output_speed + output,
            record + speed_offset,
            sizeof(float)
        );
        std::memcpy(
            output_angle + output,
            record + angle_offset,
            sizeof(float)
        );
        std::memcpy(
            output_callback_phase + output,
            record + callback_phase_offset,
            sizeof(std::int16_t)
        );
        std::memcpy(
            output_callback_aux + output,
            record + callback_aux_offset,
            sizeof(std::uint8_t)
        );
        std::memcpy(
            output_original_transform_flags + output,
            record + original_transform_flags_offset,
            sizeof(std::uint32_t)
        );
        ++active_count;
    }
    *output_count = active_count;
    return 0;
}

TOUHOU_EXPORT int touhou_local_beam_reduce_v1(
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
) {
    if (
        draft_x == nullptr
        || draft_y == nullptr
        || first_action == nullptr
        || last_direction == nullptr
        || last_focused == nullptr
        || collected_mask == nullptr
        || risk == nullptr
        || collisions == nullptr
        || minimum_clearance == nullptr
        || certificate_collisions == nullptr
        || certificate_minimum == nullptr
        || survival_preferred == nullptr
        || safety_preferred == nullptr
        || recovery_distance == nullptr
        || output_indices == nullptr
        || output_count == nullptr
        || draft_count <= 0
        || step <= 0
        || beam_width <= 0
        || action_count <= 0
        || !std::isfinite(position_quantization)
        || position_quantization <= 0.0
        || !std::isfinite(item_safety_clearance)
        || !std::isfinite(playfield_left)
        || !std::isfinite(playfield_right)
        || !std::isfinite(playfield_top)
        || !std::isfinite(playfield_bottom)
        || playfield_left > playfield_right
        || playfield_top > playfield_bottom
        || !std::isfinite(reserve_distance)
        || reserve_distance < 0.0
        || !std::isfinite(diagonal_speed)
        || diagonal_speed <= 0.0
        || !std::isfinite(cardinal_speed)
        || cardinal_speed <= 0.0
        || (target_enabled != 0 && target_enabled != 1)
        || (
            target_enabled != 0
            && (
                !std::isfinite(target_x)
                || !std::isfinite(target_y)
                || target_deadline < 0
            )
        )
    ) {
        return -1;
    }

    for (int action = 0; action < action_count; ++action) {
        if (
            certificate_collisions[action] < 0
            || std::isnan(certificate_minimum[action])
            || std::isnan(recovery_distance[action])
        ) {
            return -2;
        }
    }

    std::vector<std::array<double, 12>> keys(
        static_cast<std::size_t>(draft_count)
    );
    for (int draft = 0; draft < draft_count; ++draft) {
        const int action = first_action[draft];
        if (
            action < 0
            || action >= action_count
            || !std::isfinite(draft_x[draft])
            || !std::isfinite(draft_y[draft])
            || !std::isfinite(risk[draft])
            || collisions[draft] < 0
            || std::isnan(minimum_clearance[draft])
        ) {
            return -3;
        }
        double gate_deficit = 0.0;
        if (target_enabled != 0) {
            const double horizontal = std::max(
                std::fabs(draft_x[draft] - target_x) - 6.0,
                0.0
            );
            const double vertical = std::max(
                std::fabs(draft_y[draft] - target_y) - 6.0,
                0.0
            );
            const double diagonal = std::min(horizontal, vertical);
            const double straight = (
                std::max(horizontal, vertical) - diagonal
            );
            const double required_frames = (
                diagonal / diagonal_speed
                + straight / cardinal_speed
            );
            gate_deficit = std::max(
                required_frames
                    - static_cast<double>(
                        std::max(target_deadline - step, 0)
                    ),
                0.0
            );
        }
        double boundary_deficit = 0.0;
        if (reserve_distance > 0.0) {
            boundary_deficit = (
                std::max(
                    reserve_distance
                        - (draft_x[draft] - playfield_left),
                    0.0
                )
                + std::max(
                    reserve_distance
                        - (playfield_right - draft_x[draft]),
                    0.0
                )
                + std::max(
                    reserve_distance
                        - (draft_y[draft] - playfield_top),
                    0.0
                )
                + std::max(
                    reserve_distance
                        - (playfield_bottom - draft_y[draft]),
                    0.0
                )
            );
        }
        keys[static_cast<std::size_t>(draft)] = {
            static_cast<double>(collisions[draft]),
            static_cast<double>(certificate_collisions[action]),
            std::max(-certificate_minimum[action], 0.0),
            std::max(-minimum_clearance[draft], 0.0),
            survival_preferred[action] != 0 ? 0.0 : 1.0,
            gate_deficit,
            std::max(
                item_safety_clearance - minimum_clearance[draft],
                0.0
            ),
            safety_preferred[action] != 0 ? 0.0 : 1.0,
            boundary_deficit,
            recovery_distance[action],
            risk[draft],
            -minimum_clearance[draft],
        };
    }

    std::vector<std::int32_t> winners;
    winners.reserve(static_cast<std::size_t>(draft_count));
    std::unordered_map<
        LocalBeamQuantizedKey,
        std::size_t,
        LocalBeamQuantizedKeyHash
    > group_indices;
    group_indices.reserve(static_cast<std::size_t>(draft_count));
    for (int draft = 0; draft < draft_count; ++draft) {
        const LocalBeamQuantizedKey quantized{
            round_half_even(draft_x[draft] * position_quantization),
            round_half_even(draft_y[draft] * position_quantization),
            last_direction[draft],
            last_focused[draft],
            collected_mask[draft],
        };
        const auto insertion = group_indices.emplace(
            quantized,
            winners.size()
        );
        if (insertion.second) {
            winners.push_back(draft);
        } else if (
            local_beam_key_less(
                keys[static_cast<std::size_t>(draft)],
                keys[
                    static_cast<std::size_t>(
                        winners[insertion.first->second]
                    )
                ]
            )
        ) {
            winners[insertion.first->second] = draft;
        }
    }

    std::stable_sort(
        winners.begin(),
        winners.end(),
        [&](std::int32_t left, std::int32_t right) {
            return local_beam_key_less(
                keys[static_cast<std::size_t>(left)],
                keys[static_cast<std::size_t>(right)]
            );
        }
    );
    const int retained_count = std::min(
        beam_width,
        static_cast<int>(winners.size())
    );
    for (int index = 0; index < retained_count; ++index) {
        output_indices[index] = winners[static_cast<std::size_t>(index)];
    }
    *output_count = retained_count;
    return 0;
}

TOUHOU_EXPORT int touhou_local_supplemental_beam_reduce_v1(
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
) {
    if (
        draft_x == nullptr
        || draft_y == nullptr
        || first_action == nullptr
        || last_direction == nullptr
        || last_focused == nullptr
        || collected_mask == nullptr
        || risk == nullptr
        || collisions == nullptr
        || minimum_clearance == nullptr
        || certificate_collisions == nullptr
        || certificate_minimum == nullptr
        || survival_preferred == nullptr
        || safety_preferred == nullptr
        || recovery_distance == nullptr
        || repair_volume == nullptr
        || output_indices == nullptr
        || output_count == nullptr
        || draft_count <= 0
        || step <= 0
        || beam_width <= 0
        || action_count <= 0
        || !std::isfinite(position_quantization)
        || position_quantization <= 0.0
        || !std::isfinite(item_safety_clearance)
        || !std::isfinite(playfield_left)
        || !std::isfinite(playfield_right)
        || !std::isfinite(playfield_top)
        || !std::isfinite(playfield_bottom)
        || playfield_left > playfield_right
        || playfield_top > playfield_bottom
        || !std::isfinite(recovery_reserve_distance)
        || recovery_reserve_distance < 0.0
        || !std::isfinite(supplemental_reserve_distance)
        || supplemental_reserve_distance < 0.0
        || !std::isfinite(diagonal_speed)
        || diagonal_speed <= 0.0
        || !std::isfinite(cardinal_speed)
        || cardinal_speed <= 0.0
        || (target_enabled != 0 && target_enabled != 1)
        || (
            target_enabled != 0
            && (
                !std::isfinite(target_x)
                || !std::isfinite(target_y)
                || target_deadline < 0
            )
        )
    ) {
        return -1;
    }

    for (int action = 0; action < action_count; ++action) {
        if (
            certificate_collisions[action] < 0
            || std::isnan(certificate_minimum[action])
            || std::isnan(recovery_distance[action])
            || repair_volume[action] < 0
        ) {
            return -2;
        }
    }

    std::vector<std::array<double, 14>> keys(
        static_cast<std::size_t>(draft_count)
    );
    for (int draft = 0; draft < draft_count; ++draft) {
        const int action = first_action[draft];
        if (
            action < 0
            || action >= action_count
            || !std::isfinite(draft_x[draft])
            || !std::isfinite(draft_y[draft])
            || !std::isfinite(risk[draft])
            || collisions[draft] < 0
            || std::isnan(minimum_clearance[draft])
        ) {
            return -3;
        }
        double gate_deficit = 0.0;
        if (target_enabled != 0) {
            const double horizontal = std::max(
                std::fabs(draft_x[draft] - target_x) - 6.0,
                0.0
            );
            const double vertical = std::max(
                std::fabs(draft_y[draft] - target_y) - 6.0,
                0.0
            );
            const double diagonal = std::min(horizontal, vertical);
            const double straight = (
                std::max(horizontal, vertical) - diagonal
            );
            const double required_frames = (
                diagonal / diagonal_speed
                + straight / cardinal_speed
            );
            gate_deficit = std::max(
                required_frames
                    - static_cast<double>(
                        std::max(target_deadline - step, 0)
                    ),
                0.0
            );
        }
        const auto boundary_deficit = [&](double distance) {
            if (distance <= 0.0) {
                return 0.0;
            }
            return (
                std::max(
                    distance - (draft_x[draft] - playfield_left),
                    0.0
                )
                + std::max(
                    distance - (playfield_right - draft_x[draft]),
                    0.0
                )
                + std::max(
                    distance - (draft_y[draft] - playfield_top),
                    0.0
                )
                + std::max(
                    distance - (playfield_bottom - draft_y[draft]),
                    0.0
                )
            );
        };
        keys[static_cast<std::size_t>(draft)] = {
            static_cast<double>(collisions[draft]),
            static_cast<double>(certificate_collisions[action]),
            std::max(-certificate_minimum[action], 0.0),
            std::max(-minimum_clearance[draft], 0.0),
            survival_preferred[action] != 0 ? 0.0 : 1.0,
            gate_deficit,
            -static_cast<double>(repair_volume[action]),
            boundary_deficit(supplemental_reserve_distance),
            std::max(
                item_safety_clearance - minimum_clearance[draft],
                0.0
            ),
            safety_preferred[action] != 0 ? 0.0 : 1.0,
            boundary_deficit(recovery_reserve_distance),
            recovery_distance[action],
            risk[draft],
            -minimum_clearance[draft],
        };
    }

    std::vector<std::int32_t> winners;
    winners.reserve(static_cast<std::size_t>(draft_count));
    std::unordered_map<
        LocalBeamQuantizedKey,
        std::size_t,
        LocalBeamQuantizedKeyHash
    > group_indices;
    group_indices.reserve(static_cast<std::size_t>(draft_count));
    for (int draft = 0; draft < draft_count; ++draft) {
        const LocalBeamQuantizedKey quantized{
            round_half_even(draft_x[draft] * position_quantization),
            round_half_even(draft_y[draft] * position_quantization),
            last_direction[draft],
            last_focused[draft],
            collected_mask[draft],
        };
        const auto insertion = group_indices.emplace(
            quantized,
            winners.size()
        );
        if (insertion.second) {
            winners.push_back(draft);
        } else if (
            local_beam_key_less(
                keys[static_cast<std::size_t>(draft)],
                keys[
                    static_cast<std::size_t>(
                        winners[insertion.first->second]
                    )
                ]
            )
        ) {
            winners[insertion.first->second] = draft;
        }
    }

    std::stable_sort(
        winners.begin(),
        winners.end(),
        [&](std::int32_t left, std::int32_t right) {
            return local_beam_key_less(
                keys[static_cast<std::size_t>(left)],
                keys[static_cast<std::size_t>(right)]
            );
        }
    );
    const int retained_count = std::min(
        beam_width,
        static_cast<int>(winners.size())
    );
    for (int index = 0; index < retained_count; ++index) {
        output_indices[index] = winners[static_cast<std::size_t>(index)];
    }
    *output_count = retained_count;
    return 0;
}
