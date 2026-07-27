#pragma once

#include <cstddef>
#include <cstdint>
#include <functional>
#include <limits>
#include <vector>

#include "include/touhou_native/survival_label.hpp"

namespace touhou_native::belief_pipeline {

struct State {
    int frame;
    int row;
    int column;
    int active;
    int pending;
    int continuation_budget;
    std::uint64_t remaining_mask;

    bool operator==(const State& other) const {
        return (
            frame == other.frame
            && row == other.row
            && column == other.column
            && active == other.active
            && pending == other.pending
            && continuation_budget == other.continuation_budget
            && remaining_mask == other.remaining_mask
        );
    }
};

struct StateHash {
    std::size_t operator()(const State& state) const;
};

struct Observation {
    int frame;
    int row;
    int column;
    int active;
    int pending;
    int continuation_budget;
    std::uint64_t revealed_remaining_mask;

    bool operator==(const Observation& other) const {
        return (
            frame == other.frame
            && row == other.row
            && column == other.column
            && active == other.active
            && pending == other.pending
            && continuation_budget == other.continuation_budget
            && revealed_remaining_mask == other.revealed_remaining_mask
        );
    }
};

struct ObservationHash {
    std::size_t operator()(const Observation& observation) const;
};

struct NatureInput {
    int hidden_remaining;
    int cadence;
    int pickup_delay;
};

struct Transition {
    int step_count;
    float bottleneck_margin;
    PipelineLabel failed_label;
    State successor;
    NatureInput nature;
    bool failed;
};

struct Group {
    std::uint64_t remaining_mask = 0;
    float prefix_margin = std::numeric_limits<float>::infinity();
    NatureInput prefix_nature{0, 0, -1};
    std::uint64_t hidden_branch_count = 0;
    bool have_prefix = false;
};

struct WorstBranch {
    PipelineLabel label{0, -std::numeric_limits<float>::infinity()};
    NatureInput nature{0, 0, -1};
    float prefix_margin = -std::numeric_limits<float>::infinity();
    bool failed = true;
    State successor{-1, -1, -1, -1, -1, 0, 0};
    PipelineLabel successor_label{0, 0.0F};
    std::uint64_t hidden_branch_count = 0;
};

struct ActionExpansion {
    PipelineLabel label;
    std::vector<Transition> transitions;
};

struct WitnessPathStep {
    State state;
    int selected_action;
    WorstBranch worst;
};

struct WitnessPath {
    PipelineLabel label;
    std::vector<WitnessPathStep> steps;
    bool label_consistent;
};

using SuccessorEvaluator = std::function<PipelineLabel(const State&)>;
using MarginReader = std::function<float(const State&)>;
using StateCanonicalizer = std::function<State(State)>;
using ActionExpander = std::function<ActionExpansion(
    const State&,
    int,
    bool
)>;

bool nature_input_less(
    const NatureInput& left,
    const NatureInput& right
);

WorstBranch select_stationary_worst_branch(
    const State& state,
    const std::vector<Transition>& transitions,
    const SuccessorEvaluator& evaluate_successor
);

WitnessPath extract_stationary_witness_path(
    State root,
    int root_action,
    int continuation_action,
    int horizon_frame,
    const MarginReader& read_margin,
    const StateCanonicalizer& canonicalize,
    const ActionExpander& expand_action,
    const SuccessorEvaluator& evaluate_successor
);

}  // namespace touhou_native::belief_pipeline
