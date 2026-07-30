#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <utility>
#include <vector>

#include "include/touhou_native/abi.h"
#include "src/internal/ordered_input_impl.hpp"

namespace {

constexpr int MAX_QUEUED_MASKS = 1024;
constexpr int MAX_SUPPORT_VALUES = 64;
constexpr int MAX_DISPATCH_CALLBACKS = 16;
constexpr std::size_t MAX_ENUMERATED_BRANCHES = 100000;

struct DispatchHistory {
    std::vector<std::uint32_t> consumed;
    std::vector<std::uint32_t> published;
    std::uint32_t active = 0;
    std::vector<std::uint32_t> remaining;
};

struct Branch {
    std::uint32_t selected_mask = 0;
    bool write_required = false;
    int older_remaining = 0;
    int new_delay = 0;
    std::vector<std::uint32_t> consumed;
    std::vector<std::uint32_t> published;
    std::uint32_t successor_active_mask = 0;
    std::uint32_t successor_held_desired_mask = 0;
    std::vector<std::uint32_t> successor_queue;
    int successor_completion_remaining = 0;
};

bool dispatch_history_less(
    const DispatchHistory& left,
    const DispatchHistory& right
) {
    if (left.consumed != right.consumed) {
        return left.consumed < right.consumed;
    }
    if (left.published != right.published) {
        return left.published < right.published;
    }
    if (left.active != right.active) {
        return left.active < right.active;
    }
    return left.remaining < right.remaining;
}

bool dispatch_history_equal(
    const DispatchHistory& left,
    const DispatchHistory& right
) {
    return left.consumed == right.consumed
        && left.published == right.published
        && left.active == right.active
        && left.remaining == right.remaining;
}

bool valid_mask(std::uint32_t mask) {
    return mask <= 0xffffU;
}

bool valid_scoped_mask(
    std::uint32_t mask,
    std::uint32_t supported_mask,
    std::uint32_t forbidden_mask
) {
    return valid_mask(mask)
        && (mask & ~supported_mask) == 0
        && (mask & forbidden_mask) == 0;
}

bool differs_by_one_bit(std::uint32_t left, std::uint32_t right) {
    const std::uint32_t changed = left ^ right;
    return changed != 0 && (changed & (changed - 1U)) == 0;
}

bool valid_support(
    const std::int32_t* values,
    int count,
    bool permit_zero
) {
    if (values == nullptr || count <= 0) {
        return false;
    }
    int previous = -1;
    for (int index = 0; index < count; ++index) {
        const int value = values[index];
        if ((permit_zero ? value < 0 : value <= 0) || value <= previous) {
            return false;
        }
        previous = value;
    }
    return true;
}

std::vector<std::uint32_t> ordered_path(
    std::uint32_t previous_mask,
    std::uint32_t selected_mask
) {
    std::vector<std::uint32_t> path;
    std::uint32_t current = previous_mask;
    const std::uint32_t changed = previous_mask ^ selected_mask;
    for (int bit_index = 0; bit_index < 16; ++bit_index) {
        const std::uint32_t bit = 1U << bit_index;
        if ((changed & previous_mask & bit) != 0) {
            current &= ~bit;
            path.push_back(current);
        }
    }
    for (int bit_index = 0; bit_index < 16; ++bit_index) {
        const std::uint32_t bit = 1U << bit_index;
        if ((changed & selected_mask & bit) != 0) {
            current |= bit;
            path.push_back(current);
        }
    }
    return path;
}

std::vector<DispatchHistory> dispatch_histories(
    std::uint32_t active_mask,
    const std::vector<std::uint32_t>& queued_masks,
    int callback_count
) {
    std::vector<DispatchHistory> histories(1);
    histories[0].active = active_mask;
    histories[0].remaining = queued_masks;
    for (int callback = 0; callback < callback_count; ++callback) {
        std::vector<DispatchHistory> successors;
        for (const DispatchHistory& history : histories) {
            for (
                std::size_t consumed_count = 0;
                consumed_count <= history.remaining.size();
                ++consumed_count
            ) {
                DispatchHistory successor;
                successor.consumed = history.consumed;
                successor.consumed.push_back(history.active);
                successor.published = history.published;
                if (consumed_count == 0) {
                    successor.active = history.active;
                    successor.remaining = history.remaining;
                } else {
                    successor.active = history.remaining[consumed_count - 1];
                    successor.remaining.assign(
                        history.remaining.begin()
                            + static_cast<std::ptrdiff_t>(consumed_count),
                        history.remaining.end()
                    );
                }
                successor.published.push_back(successor.active);
                successors.push_back(std::move(successor));
            }
        }
        std::sort(
            successors.begin(),
            successors.end(),
            dispatch_history_less
        );
        successors.erase(
            std::unique(
                successors.begin(),
                successors.end(),
                dispatch_history_equal
            ),
            successors.end()
        );
        histories = std::move(successors);
    }
    return histories;
}

bool checked_add(std::size_t& total, std::size_t increment) {
    if (increment > (
        static_cast<std::size_t>(std::numeric_limits<std::int32_t>::max())
        - total
    )) {
        return false;
    }
    total += increment;
    return true;
}

bool add_history_upper_bound(
    int queue_count,
    int callback_count,
    int delay_count,
    std::size_t& branch_upper_bound
) {
    std::size_t history_count = 1;
    for (int index = 1; index <= callback_count; ++index) {
        const std::size_t numerator = static_cast<std::size_t>(
            queue_count + index
        );
        const std::size_t denominator = static_cast<std::size_t>(index);
        if (
            history_count
            > (MAX_ENUMERATED_BRANCHES * denominator) / numerator
        ) {
            return false;
        }
        history_count = (history_count * numerator) / denominator;
    }
    const std::size_t multiplier = static_cast<std::size_t>(
        std::max(1, delay_count)
    );
    if (
        history_count
        > (MAX_ENUMERATED_BRANCHES - branch_upper_bound) / multiplier
    ) {
        return false;
    }
    branch_upper_bound += history_count * multiplier;
    return true;
}

}  // namespace

int touhou_native_impl_async_ordered_input_issue_v1(
    const TouhouAsyncOrderedInputIssueQueryV1* query,
    TouhouAsyncOrderedInputIssueOutputV1* output
) {
    if (
        query == nullptr
        || output == nullptr
        || query->struct_size != sizeof(TouhouAsyncOrderedInputIssueQueryV1)
        || output->struct_size != sizeof(TouhouAsyncOrderedInputIssueOutputV1)
        || output->branch_count == nullptr
        || output->dispatch_history_count == nullptr
        || output->successor_queue_count == nullptr
        || query->queued_mask_count < 0
        || output->branch_capacity < 0
        || output->dispatch_history_capacity < 0
        || output->successor_queue_capacity < 0
        || query->queued_mask_count > MAX_QUEUED_MASKS
        || query->post_dispatch_delay_count > MAX_SUPPORT_VALUES
        || query->dispatch_callback_count > MAX_SUPPORT_VALUES
        || !valid_mask(query->supported_mask)
        || !valid_mask(query->forbidden_mask)
        || (query->forbidden_mask & ~query->supported_mask) != 0
    ) {
        return 1;
    }
    if (
        !valid_scoped_mask(
            query->active_mask,
            query->supported_mask,
            query->forbidden_mask
        )
        || !valid_scoped_mask(
            query->held_desired_mask,
            query->supported_mask,
            query->forbidden_mask
        )
        || !valid_scoped_mask(
            query->selected_mask,
            query->supported_mask,
            query->forbidden_mask
        )
    ) {
        return 1;
    }
    if (
        (query->queued_mask_count > 0 && query->queued_masks == nullptr)
        || (query->queued_mask_count == 0
            && (
                query->completion_remaining != 0
                || query->active_mask != query->held_desired_mask
            ))
        || (query->queued_mask_count > 0 && query->completion_remaining <= 0)
    ) {
        return 1;
    }

    std::vector<std::uint32_t> queued_masks;
    queued_masks.reserve(static_cast<std::size_t>(query->queued_mask_count));
    std::uint32_t previous = query->active_mask;
    for (int index = 0; index < query->queued_mask_count; ++index) {
        const std::uint32_t queued = query->queued_masks[index];
        if (
            !valid_scoped_mask(
                queued,
                query->supported_mask,
                query->forbidden_mask
            )
            || !differs_by_one_bit(previous, queued)
        ) {
            return 1;
        }
        queued_masks.push_back(queued);
        previous = queued;
    }
    if (
        !queued_masks.empty()
        && queued_masks.back() != query->held_desired_mask
    ) {
        return 1;
    }

    std::vector<Branch> branches;
    const bool write_required =
        query->selected_mask != query->held_desired_mask;
    if (!write_required) {
        Branch branch;
        branch.selected_mask = query->selected_mask;
        branch.older_remaining = query->completion_remaining;
        branch.successor_active_mask = query->active_mask;
        branch.successor_held_desired_mask = query->held_desired_mask;
        branch.successor_queue = queued_masks;
        branch.successor_completion_remaining =
            query->completion_remaining;
        branches.push_back(std::move(branch));
    } else {
        if (
            !valid_support(
                query->post_dispatch_delay_support,
                query->post_dispatch_delay_count,
                false
            )
            || !valid_support(
                query->dispatch_callback_count_support,
                query->dispatch_callback_count,
                true
            )
        ) {
            return 1;
        }
        for (
            int index = 0;
            index < query->dispatch_callback_count;
            ++index
        ) {
            if (
                query->dispatch_callback_count_support[index]
                > MAX_DISPATCH_CALLBACKS
            ) {
                return 1;
            }
        }
        std::vector<std::uint32_t> combined_suffix = queued_masks;
        std::vector<std::uint32_t> appended = ordered_path(
            query->held_desired_mask,
            query->selected_mask
        );
        if (appended.empty()) {
            return 1;
        }
        combined_suffix.insert(
            combined_suffix.end(),
            appended.begin(),
            appended.end()
        );
        std::size_t branch_upper_bound = 0;
        for (
            int support_index = 0;
            support_index < query->dispatch_callback_count;
            ++support_index
        ) {
            if (
                !add_history_upper_bound(
                    static_cast<int>(combined_suffix.size()),
                    query->dispatch_callback_count_support[support_index],
                    query->post_dispatch_delay_count,
                    branch_upper_bound
                )
            ) {
                return 3;
            }
        }

        for (
            int support_index = 0;
            support_index < query->dispatch_callback_count;
            ++support_index
        ) {
            const int callback_count =
                query->dispatch_callback_count_support[support_index];
            for (
                DispatchHistory& history : dispatch_histories(
                    query->active_mask,
                    combined_suffix,
                    callback_count
                )
            ) {
                if (history.remaining.empty()) {
                    Branch branch;
                    branch.selected_mask = query->selected_mask;
                    branch.write_required = true;
                    branch.older_remaining = query->completion_remaining;
                    branch.consumed = std::move(history.consumed);
                    branch.published = std::move(history.published);
                    branch.successor_active_mask = query->selected_mask;
                    branch.successor_held_desired_mask =
                        query->selected_mask;
                    branches.push_back(std::move(branch));
                    continue;
                }
                for (
                    int delay_index = 0;
                    delay_index < query->post_dispatch_delay_count;
                    ++delay_index
                ) {
                    Branch branch;
                    branch.selected_mask = query->selected_mask;
                    branch.write_required = true;
                    branch.older_remaining = query->completion_remaining;
                    branch.new_delay =
                        query->post_dispatch_delay_support[delay_index];
                    branch.consumed = history.consumed;
                    branch.published = history.published;
                    branch.successor_active_mask = history.active;
                    branch.successor_held_desired_mask =
                        query->selected_mask;
                    branch.successor_queue = history.remaining;
                    branch.successor_completion_remaining = branch.new_delay;
                    branches.push_back(std::move(branch));
                }
            }
        }
    }

    std::size_t dispatch_count = 0;
    std::size_t successor_queue_count = 0;
    for (const Branch& branch : branches) {
        if (
            !checked_add(dispatch_count, branch.consumed.size())
            || !checked_add(
                successor_queue_count,
                branch.successor_queue.size()
            )
        ) {
            return 1;
        }
    }
    if (
        branches.size() > static_cast<std::size_t>(
            std::numeric_limits<std::int32_t>::max()
        )
    ) {
        return 1;
    }

    *output->branch_count = static_cast<std::int32_t>(branches.size());
    *output->dispatch_history_count =
        static_cast<std::int32_t>(dispatch_count);
    *output->successor_queue_count =
        static_cast<std::int32_t>(successor_queue_count);

    const bool count_only =
        output->branch_capacity == 0
        && output->dispatch_history_capacity == 0
        && output->successor_queue_capacity == 0
        && output->branches == nullptr
        && output->active_masks_consumed_during_dispatch == nullptr
        && output->publications_during_dispatch == nullptr
        && output->successor_queued_masks == nullptr;
    if (count_only) {
        return 0;
    }
    if (
        output->branch_capacity < static_cast<int>(branches.size())
        || output->dispatch_history_capacity
            < static_cast<int>(dispatch_count)
        || output->successor_queue_capacity
            < static_cast<int>(successor_queue_count)
        || (branches.size() > 0 && output->branches == nullptr)
        || (
            dispatch_count > 0
            && (
                output->active_masks_consumed_during_dispatch == nullptr
                || output->publications_during_dispatch == nullptr
            )
        )
        || (
            successor_queue_count > 0
            && output->successor_queued_masks == nullptr
        )
    ) {
        return 2;
    }

    std::size_t dispatch_offset = 0;
    std::size_t queue_offset = 0;
    for (std::size_t index = 0; index < branches.size(); ++index) {
        const Branch& branch = branches[index];
        TouhouAsyncOrderedInputIssueBranchV1& destination =
            output->branches[index];
        destination = {};
        destination.selected_mask = branch.selected_mask;
        destination.write_required = branch.write_required ? 1U : 0U;
        destination.older_remaining = branch.older_remaining;
        destination.new_delay = branch.new_delay;
        destination.dispatch_history_offset =
            static_cast<std::int32_t>(dispatch_offset);
        destination.dispatch_history_count =
            static_cast<std::int32_t>(branch.consumed.size());
        destination.successor_active_mask =
            branch.successor_active_mask;
        destination.successor_held_desired_mask =
            branch.successor_held_desired_mask;
        destination.successor_queue_offset =
            static_cast<std::int32_t>(queue_offset);
        destination.successor_queue_count =
            static_cast<std::int32_t>(branch.successor_queue.size());
        destination.successor_completion_remaining =
            branch.successor_completion_remaining;
        if (!branch.consumed.empty()) {
            std::copy(
                branch.consumed.begin(),
                branch.consumed.end(),
                output->active_masks_consumed_during_dispatch
                    + dispatch_offset
            );
            std::copy(
                branch.published.begin(),
                branch.published.end(),
                output->publications_during_dispatch + dispatch_offset
            );
        }
        if (!branch.successor_queue.empty()) {
            std::copy(
                branch.successor_queue.begin(),
                branch.successor_queue.end(),
                output->successor_queued_masks + queue_offset
            );
        }
        dispatch_offset += branch.consumed.size();
        queue_offset += branch.successor_queue.size();
    }
    return 0;
}
