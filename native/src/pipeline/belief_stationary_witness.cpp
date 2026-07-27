// Deterministic worst-branch extraction for an exact stationary policy.

#include "src/pipeline/belief_stationary_witness.hpp"

#include <algorithm>
#include <tuple>
#include <unordered_map>

namespace touhou_native::belief_pipeline {
namespace {

std::uint64_t mix_hash(std::uint64_t value) {
    value += 0x9e3779b97f4a7c15ULL;
    value = (
        (value ^ (value >> 30))
        * 0xbf58476d1ce4e5b9ULL
    );
    value = (
        (value ^ (value >> 27))
        * 0x94d049bb133111ebULL
    );
    return value ^ (value >> 31);
}

bool state_key_less(const State& left, const State& right) {
    return std::tie(
        left.frame,
        left.row,
        left.column,
        left.active,
        left.pending,
        left.continuation_budget,
        left.remaining_mask
    ) < std::tie(
        right.frame,
        right.row,
        right.column,
        right.active,
        right.pending,
        right.continuation_budget,
        right.remaining_mask
    );
}

bool branch_tie_less(
    const WorstBranch& left,
    const WorstBranch& right
) {
    if (nature_input_less(left.nature, right.nature)) {
        return true;
    }
    if (nature_input_less(right.nature, left.nature)) {
        return false;
    }
    if (left.failed != right.failed) {
        return !left.failed;
    }
    if (!left.failed) {
        return state_key_less(left.successor, right.successor);
    }
    return false;
}

bool branch_less(
    const WorstBranch& left,
    const WorstBranch& right
) {
    if (pipeline_label_less(left.label, right.label)) {
        return true;
    }
    if (pipeline_label_less(right.label, left.label)) {
        return false;
    }
    return branch_tie_less(left, right);
}

}  // namespace

std::size_t StateHash::operator()(const State& state) const {
    const std::uint64_t first = mix_hash(
        static_cast<std::uint64_t>(state.frame)
        | (static_cast<std::uint64_t>(state.row) << 16)
        | (static_cast<std::uint64_t>(state.column) << 26)
        | (static_cast<std::uint64_t>(state.active) << 36)
        | (static_cast<std::uint64_t>(state.pending + 1) << 41)
        | (
            static_cast<std::uint64_t>(state.continuation_budget)
            << 47
        )
    );
    const std::uint64_t second = mix_hash(state.remaining_mask);
    return static_cast<std::size_t>(
        first ^ (
            second
            + 0x9e3779b97f4a7c15ULL
            + (first << 6)
            + (first >> 2)
        )
    );
}

std::size_t ObservationHash::operator()(
    const Observation& observation
) const {
    return StateHash{}(
        State{
            observation.frame,
            observation.row,
            observation.column,
            observation.active,
            observation.pending,
            observation.continuation_budget,
            observation.revealed_remaining_mask,
        }
    );
}

bool nature_input_less(
    const NatureInput& left,
    const NatureInput& right
) {
    return std::tie(
        left.hidden_remaining,
        left.cadence,
        left.pickup_delay
    ) < std::tie(
        right.hidden_remaining,
        right.cadence,
        right.pickup_delay
    );
}

WorstBranch select_stationary_worst_branch(
    const State& state,
    const std::vector<Transition>& transitions,
    const SuccessorEvaluator& evaluate_successor
) {
    std::vector<WorstBranch> branches;
    branches.reserve(transitions.size());
    std::unordered_map<Observation, Group, ObservationHash> groups;

    for (const Transition& transition : transitions) {
        if (transition.failed) {
            branches.push_back(
                WorstBranch{
                    transition.failed_label,
                    transition.nature,
                    transition.bottleneck_margin,
                    true,
                    State{-1, -1, -1, -1, -1, 0, 0},
                    PipelineLabel{0, 0.0F},
                    1,
                }
            );
            continue;
        }
        const State& successor = transition.successor;
        const Observation observation{
            successor.frame,
            successor.row,
            successor.column,
            successor.active,
            successor.pending,
            successor.continuation_budget,
            0,
        };
        Group& group = groups[observation];
        group.remaining_mask |= successor.remaining_mask;
        if (
            !group.have_prefix
            || transition.bottleneck_margin < group.prefix_margin
            || (
                transition.bottleneck_margin == group.prefix_margin
                && nature_input_less(
                    transition.nature,
                    group.prefix_nature
                )
            )
        ) {
            group.prefix_margin = transition.bottleneck_margin;
            group.prefix_nature = transition.nature;
            group.have_prefix = true;
        }
        ++group.hidden_branch_count;
    }

    std::vector<
        const std::pair<const Observation, Group>*
    > ordered_groups;
    ordered_groups.reserve(groups.size());
    for (const auto& item : groups) {
        ordered_groups.push_back(&item);
    }
    std::sort(
        ordered_groups.begin(),
        ordered_groups.end(),
        [](const auto* left, const auto* right) {
            return std::tie(
                left->first.frame,
                left->first.row,
                left->first.column,
                left->first.active,
                left->first.pending,
                left->first.continuation_budget,
                left->first.revealed_remaining_mask
            ) < std::tie(
                right->first.frame,
                right->first.row,
                right->first.column,
                right->first.active,
                right->first.pending,
                right->first.continuation_budget,
                right->first.revealed_remaining_mask
            );
        }
    );
    for (const auto* item : ordered_groups) {
        const Observation& observation = item->first;
        const Group& group = item->second;
        const State successor{
            observation.frame,
            observation.row,
            observation.column,
            observation.active,
            observation.pending,
            observation.continuation_budget,
            group.remaining_mask,
        };
        const PipelineLabel successor_label = evaluate_successor(successor);
        branches.push_back(
            WorstBranch{
                PipelineLabel{
                    static_cast<std::uint16_t>(
                        observation.frame
                        - state.frame
                        + successor_label.frames
                    ),
                    std::min(
                        group.prefix_margin,
                        successor_label.margin
                    ),
                },
                group.prefix_nature,
                group.prefix_margin,
                false,
                successor,
                successor_label,
                group.hidden_branch_count,
            }
        );
    }

    return *std::min_element(
        branches.begin(),
        branches.end(),
        branch_less
    );
}

WitnessPath extract_stationary_witness_path(
    State root,
    int root_action,
    int continuation_action,
    int horizon_frame,
    const MarginReader& read_margin,
    const StateCanonicalizer& canonicalize,
    const ActionExpander& expand_action,
    const SuccessorEvaluator& evaluate_successor
) {
    State state = canonicalize(root);
    WitnessPath path{
        PipelineLabel{0, read_margin(state)},
        {},
        true,
    };
    path.steps.reserve(
        static_cast<std::size_t>(horizon_frame + 1)
    );
    bool public_root = true;
    while (
        state.frame < horizon_frame
        && read_margin(state) > 0.0F
    ) {
        const int selected = (
            public_root ? root_action : continuation_action
        );
        ActionExpansion expansion = expand_action(
            state,
            selected,
            public_root
        );
        const WorstBranch worst = select_stationary_worst_branch(
            state,
            expansion.transitions,
            evaluate_successor
        );
        if (!pipeline_label_equal(expansion.label, worst.label)) {
            path.label_consistent = false;
            return path;
        }
        if (public_root) {
            path.label = expansion.label;
        }
        path.steps.push_back(
            WitnessPathStep{state, selected, worst}
        );
        if (worst.failed) {
            break;
        }
        state = canonicalize(worst.successor);
        public_root = false;
    }
    return path;
}

}  // namespace touhou_native::belief_pipeline
