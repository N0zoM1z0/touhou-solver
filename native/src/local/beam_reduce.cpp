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

#include "src/internal/abi_impl.hpp"
#include "include/touhou_native/local_hazard_stop.hpp"

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
