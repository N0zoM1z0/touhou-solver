#pragma once

// Included after pipeline_survival_workspace.hpp and the shared lattice
// helpers.  This workspace solves the recursively variable-cadence
// information-set game with physical hold/no-write semantics.  The held
// desired action is pending when pending >= 0, otherwise active.  Selecting
// that action sends no new command and carries the old pending countdown.
// A public continuation budget limits non-base future actions and produces
// nested attainable lower bounds.  The optional revealed-remaining partition
// is an explicit optimistic information relaxation.
// It is separate from the older always-issue/one-transition workspace so
// experiments cannot silently change either contract.
namespace {

constexpr int BELIEF_PIPELINE_MAX_REMAINING = 62;

struct BeliefPipelineState {
    int frame;
    int row;
    int column;
    int active;
    int pending;
    int continuation_budget;
    std::uint64_t remaining_mask;

    bool operator==(const BeliefPipelineState& other) const {
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

struct BeliefPipelineStateHash {
    std::size_t operator()(const BeliefPipelineState& state) const {
        std::uint64_t first = (
            static_cast<std::uint64_t>(state.frame)
            | (static_cast<std::uint64_t>(state.row) << 16)
            | (static_cast<std::uint64_t>(state.column) << 26)
            | (static_cast<std::uint64_t>(state.active) << 36)
            | (
                static_cast<std::uint64_t>(state.pending + 1)
                << 41
            )
            | (
                static_cast<std::uint64_t>(state.continuation_budget)
                << 47
            )
        );
        first += 0x9e3779b97f4a7c15ULL;
        first = (
            (first ^ (first >> 30))
            * 0xbf58476d1ce4e5b9ULL
        );
        first = (
            (first ^ (first >> 27))
            * 0x94d049bb133111ebULL
        );
        first ^= first >> 31;
        std::uint64_t second = (
            state.remaining_mask + 0x9e3779b97f4a7c15ULL
        );
        second = (
            (second ^ (second >> 30))
            * 0xbf58476d1ce4e5b9ULL
        );
        second = (
            (second ^ (second >> 27))
            * 0x94d049bb133111ebULL
        );
        second ^= second >> 31;
        return static_cast<std::size_t>(
            first ^ (
                second
                + 0x9e3779b97f4a7c15ULL
                + (first << 6)
                + (first >> 2)
            )
        );
    }
};

struct BeliefPipelineObservation {
    int frame;
    int row;
    int column;
    int active;
    int pending;
    int continuation_budget;
    std::uint64_t revealed_remaining_mask;

    bool operator==(const BeliefPipelineObservation& other) const {
        return (
            frame == other.frame
            && row == other.row
            && column == other.column
            && active == other.active
            && pending == other.pending
            && continuation_budget == other.continuation_budget
            && revealed_remaining_mask
                == other.revealed_remaining_mask
        );
    }
};

struct BeliefPipelineObservationHash {
    std::size_t operator()(
        const BeliefPipelineObservation& observation
    ) const {
        return BeliefPipelineStateHash{}(
            BeliefPipelineState{
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
};

struct BeliefPipelineTransition {
    int step_count;
    float bottleneck_margin;
    PipelineLabel failed_label;
    BeliefPipelineState successor;
    bool failed;
};

struct BeliefPipelineGroup {
    std::uint64_t remaining_mask = 0;
    float prefix_margin = std::numeric_limits<float>::infinity();
};

class BeliefPipelineSurvivalWorkspace {
private:
    using Clock = std::chrono::steady_clock;

    struct RootNode {
        PipelineLabel state;
        std::array<PipelineLabel, PIPELINE_MAX_ACTIONS> actions;
    };

    struct PreparedAction {
        PipelineLabel upper{
            std::numeric_limits<std::uint16_t>::max(),
            std::numeric_limits<float>::infinity(),
        };
        std::vector<BeliefPipelineTransition> transitions;
    };

    struct Counters {
        std::uint64_t memo_hits = 0;
        std::uint64_t action_upper_prunes = 0;
        std::uint64_t branch_incumbent_prunes = 0;
        std::uint64_t observation_merges = 0;
        std::uint64_t root_memo_hits = 0;
        std::uint64_t hidden_simulations = 0;
        std::uint64_t canonicalizations = 0;
    };

    class QueryScope {
    public:
        QueryScope(
            BeliefPipelineSurvivalWorkspace* owner,
            int timeout_ms
        ) : owner_(owner) {
            owner_->abort_poll_counter_ = 0;
            owner_->deadline_active_ = timeout_ms > 0;
            if (owner_->deadline_active_) {
                owner_->deadline_ = (
                    Clock::now() + std::chrono::milliseconds(timeout_ms)
                );
            }
        }

        ~QueryScope() {
            owner_->deadline_active_ = false;
        }

    private:
        BeliefPipelineSurvivalWorkspace* owner_;
    };

public:
    BeliefPipelineSurvivalWorkspace(
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
        std::uint32_t base_action_mask,
        std::uint32_t budgeted_action_mask,
        int continuation_budget,
        bool reveal_remaining_delay,
        const int* delay_frames,
        int delay_count,
        const int* cadence_frames,
        int cadence_count,
        float required_clearance,
        bool clamp_to_bounds
    )
        : clearance_(clearance),
          frame_count_(frame_count),
          row_count_(row_count),
          column_count_(column_count),
          x_start_(x_start),
          x_step_(x_step),
          y_start_(y_start),
          y_step_(y_step),
          action_count_(action_count),
          base_action_mask_(base_action_mask),
          budgeted_action_mask_(budgeted_action_mask),
          continuation_budget_(continuation_budget),
          reveal_remaining_delay_(reveal_remaining_delay),
          required_clearance_(required_clearance),
          clamp_to_bounds_(clamp_to_bounds),
          velocity_x_(velocity_x, velocity_x + action_count),
          velocity_y_(velocity_y, velocity_y + action_count),
          delay_frames_(delay_frames, delay_frames + delay_count),
          cadence_frames_(cadence_frames, cadence_frames + cadence_count) {
        memo_.reserve(4096);
        root_memo_.reserve(256);
    }

    int query(
        int start_frame,
        int start_row,
        int start_column,
        int observed_action,
        int pending_action,
        const int* pending_remaining_frames,
        int pending_remaining_count,
        int root_continuation_budget,
        int timeout_ms,
        std::uint16_t* output_state_frames,
        float* output_state_margin,
        std::uint16_t* output_action_frames,
        float* output_action_margins,
        std::uint32_t* output_best_action_mask,
        std::uint64_t* output_stats
    ) {
        const int query_budget = (
            root_continuation_budget < 0
            ? continuation_budget_
            : root_continuation_budget
        );
        if (
            start_frame < 0 || start_frame >= frame_count_
            || start_row < 0 || start_row >= row_count_
            || start_column < 0 || start_column >= column_count_
            || observed_action < 0 || observed_action >= action_count_
            || pending_action < -1 || pending_action >= action_count_
            || pending_remaining_count < 0
            || pending_remaining_count > BELIEF_PIPELINE_MAX_REMAINING
            || query_budget < 0
            || query_budget > continuation_budget_
            || timeout_ms < 0
            || (
                pending_action < 0
                && pending_remaining_count != 0
            )
            || (
                pending_action >= 0
                && (
                    pending_remaining_frames == nullptr
                    || pending_remaining_count == 0
                )
            )
        ) {
            return 1;
        }
        std::uint64_t remaining_mask = std::uint64_t{1};
        if (pending_action >= 0) {
            remaining_mask = 0;
            for (int index = 0; index < pending_remaining_count; ++index) {
                const int remaining = pending_remaining_frames[index];
                if (
                    remaining <= 0
                    || remaining > BELIEF_PIPELINE_MAX_REMAINING
                    || (
                        index > 0
                        && pending_remaining_frames[index - 1]
                            >= remaining
                    )
                ) {
                    return 1;
                }
                remaining_mask |= std::uint64_t{1} << remaining;
            }
        }

        std::lock_guard<std::mutex> guard(mutex_);
        QueryScope scope(this, timeout_ms);
        check_abort(true);
        const Counters before = counters_;
        const std::size_t memo_before = memo_.size();
        RootNode root = query_root(
            BeliefPipelineState{
                start_frame,
                start_row,
                start_column,
                observed_action,
                pending_action,
                query_budget,
                remaining_mask,
            }
        );
        *output_state_frames = root.state.frames;
        *output_state_margin = root.state.margin;
        std::uint32_t best_mask = 0;
        for (int action = 0; action < action_count_; ++action) {
            output_action_frames[action] = root.actions[action].frames;
            output_action_margins[action] = root.actions[action].margin;
            if (pipeline_label_equal(root.actions[action], root.state)) {
                best_mask |= std::uint32_t{1} << action;
            }
        }
        *output_best_action_mask = best_mask;
        output_stats[0] = static_cast<std::uint64_t>(memo_.size());
        output_stats[1] = static_cast<std::uint64_t>(
            memo_.size() - memo_before
        );
        output_stats[2] = counters_.memo_hits - before.memo_hits;
        output_stats[3] = (
            counters_.action_upper_prunes
            - before.action_upper_prunes
        );
        output_stats[4] = (
            counters_.branch_incumbent_prunes
            - before.branch_incumbent_prunes
        );
        output_stats[5] = (
            counters_.observation_merges - before.observation_merges
        );
        output_stats[6] = (
            counters_.root_memo_hits - before.root_memo_hits
        );
        output_stats[7] = (
            counters_.hidden_simulations - before.hidden_simulations
        );
        return 0;
    }

    void request_cancel() {
        cancel_requested_.store(true, std::memory_order_release);
    }

private:
    void check_abort(bool force = false) {
        ++abort_poll_counter_;
        if (cancel_requested_.load(std::memory_order_acquire)) {
            throw PipelineCancelledSignal{};
        }
        if (
            deadline_active_
            && (
                force
                || (abort_poll_counter_ & std::uint64_t{63}) == 0
            )
            && Clock::now() >= deadline_
        ) {
            throw PipelineDeadlineSignal{};
        }
    }

    float current_margin(const BeliefPipelineState& state) const {
        return (
            clearance_[clearance_index(
                state.frame,
                state.row,
                state.column,
                row_count_,
                column_count_
            )] - required_clearance_
        );
    }

    BeliefPipelineState canonicalize(
        BeliefPipelineState state
    ) {
        if (state.pending < 0) {
            state.pending = -1;
            state.remaining_mask = std::uint64_t{1};
            return state;
        }
        if (
            state.pending == state.active
        ) {
            state.pending = -1;
            state.remaining_mask = std::uint64_t{1};
            ++counters_.canonicalizations;
            return state;
        }
        return state;
    }

    BeliefPipelineTransition simulate(
        const BeliefPipelineState& state,
        int older_remaining,
        int selected,
        int delay,
        bool issued,
        int cadence,
        int successor_budget
    ) {
        check_abort();
        ++counters_.hidden_simulations;
        const int horizon = frame_count_ - 1;
        const int step_count = std::min(
            cadence,
            horizon - state.frame
        );
        const int older_pending = state.pending;
        const double state_x = x_start_ + state.column * x_step_;
        const double state_y = y_start_ + state.row * y_step_;
        double displacement_x = 0.0;
        double displacement_y = 0.0;
        float bottleneck = current_margin(state);
        Sample terminal{-1, -1, 0.0, false};
        for (int step = 1; step <= step_count; ++step) {
            check_abort();
            int motion = state.active;
            if (issued && step > delay) {
                motion = selected;
            } else if (
                older_pending >= 0 && step > older_remaining
            ) {
                motion = older_pending;
            }
            displacement_x += velocity_x_[motion];
            displacement_y += velocity_y_[motion];
            terminal = sample_lattice(
                state_x + displacement_x,
                state_y + displacement_y,
                x_start_,
                x_step_,
                column_count_,
                y_start_,
                y_step_,
                row_count_,
                clamp_to_bounds_
            );
            if (!terminal.inside) {
                const PipelineLabel failed{
                    static_cast<std::uint16_t>(step - 1),
                    -std::numeric_limits<float>::infinity(),
                };
                return BeliefPipelineTransition{
                    step_count,
                    failed.margin,
                    failed,
                    state,
                    true,
                };
            }
            const float margin = (
                clearance_[clearance_index(
                    state.frame + step,
                    terminal.row,
                    terminal.column,
                    row_count_,
                    column_count_
                )]
                - static_cast<float>(terminal.error)
                - required_clearance_
            );
            bottleneck = std::min(bottleneck, margin);
            if (margin <= 0.0F) {
                const PipelineLabel failed{
                    static_cast<std::uint16_t>(step - 1),
                    bottleneck,
                };
                return BeliefPipelineTransition{
                    step_count,
                    bottleneck,
                    failed,
                    state,
                    true,
                };
            }
        }

        int successor_active = state.active;
        int successor_pending = -1;
        int successor_remaining = 0;
        if (!issued) {
            if (
                older_pending >= 0
                && older_remaining <= step_count
            ) {
                successor_active = older_pending;
            } else if (older_pending >= 0) {
                successor_pending = older_pending;
                successor_remaining = older_remaining - step_count;
            }
        } else if (delay <= step_count) {
            successor_active = selected;
        } else {
            if (
                older_pending >= 0
                && older_remaining <= step_count
            ) {
                successor_active = older_pending;
            }
            successor_pending = selected;
            successor_remaining = delay - step_count;
        }
        BeliefPipelineState successor{
            state.frame + step_count,
            terminal.row,
            terminal.column,
            successor_active,
            successor_pending,
            successor_budget,
            std::uint64_t{1} << successor_remaining,
        };
        successor = canonicalize(successor);
        return BeliefPipelineTransition{
            step_count,
            bottleneck,
            PipelineLabel{0, 0.0F},
            successor,
            false,
        };
    }

    PipelineLabel evaluate_action(
        const BeliefPipelineState& state,
        const PreparedAction& prepared,
        const PipelineLabel* incumbent
    ) {
        std::unordered_map<
            BeliefPipelineObservation,
            BeliefPipelineGroup,
            BeliefPipelineObservationHash
        > groups;
        PipelineLabel robust{
            std::numeric_limits<std::uint16_t>::max(),
            std::numeric_limits<float>::infinity(),
        };
        bool have_branch = false;
        for (const BeliefPipelineTransition& transition :
             prepared.transitions) {
            have_branch = true;
            if (transition.failed) {
                if (
                    pipeline_label_less(
                        transition.failed_label,
                        robust
                    )
                ) {
                    robust = transition.failed_label;
                }
                if (
                    incumbent != nullptr
                    && pipeline_label_less_equal(robust, *incumbent)
                ) {
                    ++counters_.branch_incumbent_prunes;
                    return robust;
                }
                continue;
            }
            const BeliefPipelineState& successor = transition.successor;
            const BeliefPipelineObservation observation{
                successor.frame,
                successor.row,
                successor.column,
                successor.active,
                successor.pending,
                successor.continuation_budget,
                (
                    reveal_remaining_delay_
                    ? successor.remaining_mask
                    : std::uint64_t{0}
                ),
            };
            auto inserted = groups.emplace(
                observation,
                BeliefPipelineGroup{}
            );
            BeliefPipelineGroup& group = inserted.first->second;
            if (!inserted.second) {
                ++counters_.observation_merges;
            }
            group.remaining_mask |= successor.remaining_mask;
            group.prefix_margin = std::min(
                group.prefix_margin,
                transition.bottleneck_margin
            );
            const PipelineLabel group_upper{
                static_cast<std::uint16_t>(
                    frame_count_ - 1 - state.frame
                ),
                group.prefix_margin,
            };
            if (
                incumbent != nullptr
                && pipeline_label_less_equal(
                    group_upper,
                    *incumbent
                )
            ) {
                ++counters_.branch_incumbent_prunes;
                return group_upper;
            }
        }
        std::vector<
            const std::pair<
                const BeliefPipelineObservation,
                BeliefPipelineGroup
            >*
        > ordered_groups;
        ordered_groups.reserve(groups.size());
        for (const auto& item : groups) {
            ordered_groups.push_back(&item);
        }
        std::sort(
            ordered_groups.begin(),
            ordered_groups.end(),
            [&](const auto* left, const auto* right) {
                const PipelineLabel left_upper{
                    static_cast<std::uint16_t>(
                        frame_count_ - 1 - state.frame
                    ),
                    left->second.prefix_margin,
                };
                const PipelineLabel right_upper{
                    static_cast<std::uint16_t>(
                        frame_count_ - 1 - state.frame
                    ),
                    right->second.prefix_margin,
                };
                return pipeline_label_less(left_upper, right_upper);
            }
        );
        for (const auto* item : ordered_groups) {
            check_abort();
            const BeliefPipelineObservation& observation = item->first;
            const BeliefPipelineGroup& group = item->second;
            const PipelineLabel successor = solve(
                BeliefPipelineState{
                    observation.frame,
                    observation.row,
                    observation.column,
                    observation.active,
                    observation.pending,
                    observation.continuation_budget,
                    group.remaining_mask,
                }
            );
            const PipelineLabel label{
                static_cast<std::uint16_t>(
                    observation.frame - state.frame + successor.frames
                ),
                std::min(group.prefix_margin, successor.margin),
            };
            if (!have_branch || pipeline_label_less(label, robust)) {
                robust = label;
            }
            have_branch = true;
            if (
                incumbent != nullptr
                && pipeline_label_less_equal(robust, *incumbent)
            ) {
                ++counters_.branch_incumbent_prunes;
                return robust;
            }
        }
        return robust;
    }

    PreparedAction prepare_action(
        const BeliefPipelineState& state,
        int selected,
        bool public_root
    ) {
        PreparedAction prepared;
        const bool base_action = (
            base_action_mask_ & (std::uint32_t{1} << selected)
        ) != 0;
        const int successor_budget = (
            public_root || base_action
            ? state.continuation_budget
            : state.continuation_budget - 1
        );
        const std::uint16_t remaining_horizon =
            static_cast<std::uint16_t>(
                frame_count_ - 1 - state.frame
            );
        int remaining_count = 0;
        for (
            int remaining = 0;
            remaining <= BELIEF_PIPELINE_MAX_REMAINING;
            ++remaining
        ) {
            if (
                state.remaining_mask
                & (std::uint64_t{1} << remaining)
            ) {
                ++remaining_count;
            }
        }
        prepared.transitions.reserve(
            static_cast<std::size_t>(remaining_count)
            * cadence_frames_.size()
            * (
                selected == (
                    state.pending >= 0
                    ? state.pending
                    : state.active
                )
                ? std::size_t{1}
                : delay_frames_.size()
            )
        );
        const int desired = (
            state.pending >= 0 ? state.pending : state.active
        );
        const bool issued = selected != desired;
        for (
            int remaining = 0;
            remaining <= BELIEF_PIPELINE_MAX_REMAINING;
            ++remaining
        ) {
            if (
                (state.remaining_mask
                 & (std::uint64_t{1} << remaining)) == 0
            ) {
                continue;
            }
            for (int cadence : cadence_frames_) {
                const std::size_t delay_count = (
                    issued ? delay_frames_.size() : std::size_t{1}
                );
                for (
                    std::size_t delay_index = 0;
                    delay_index < delay_count;
                    ++delay_index
                ) {
                    const int delay = (
                        issued ? delay_frames_[delay_index] : 0
                    );
                    const BeliefPipelineTransition transition = simulate(
                        state,
                        remaining,
                        selected,
                        delay,
                        issued,
                        cadence,
                        successor_budget
                    );
                    prepared.transitions.push_back(transition);
                    const PipelineLabel branch_upper = (
                        transition.failed
                        ? transition.failed_label
                        : PipelineLabel{
                            remaining_horizon,
                            transition.bottleneck_margin,
                        }
                    );
                    if (
                        pipeline_label_less(
                            branch_upper,
                            prepared.upper
                        )
                    ) {
                        prepared.upper = branch_upper;
                    }
                }
            }
        }
        return prepared;
    }

    PipelineLabel solve(BeliefPipelineState state) {
        check_abort();
        state = canonicalize(state);
        const auto found = memo_.find(state);
        if (found != memo_.end()) {
            ++counters_.memo_hits;
            return found->second;
        }
        const float margin = current_margin(state);
        if (state.frame == frame_count_ - 1 || margin <= 0.0F) {
            const PipelineLabel terminal{0, margin};
            memo_.emplace(state, terminal);
            return terminal;
        }
        PipelineLabel best{
            0,
            -std::numeric_limits<float>::infinity(),
        };
        struct Candidate {
            int action;
            PipelineLabel upper;
        };
        std::array<PreparedAction, PIPELINE_MAX_ACTIONS> prepared;
        std::array<Candidate, PIPELINE_MAX_ACTIONS> candidates;
        int candidate_count = 0;
        for (int action = 0; action < action_count_; ++action) {
            const std::uint32_t bit = std::uint32_t{1} << action;
            const bool base_action = (base_action_mask_ & bit) != 0;
            const bool budgeted_action = (
                state.continuation_budget > 0
                && (budgeted_action_mask_ & bit) != 0
            );
            if (!base_action && !budgeted_action) {
                continue;
            }
            prepared[action] = prepare_action(state, action, false);
            candidates[candidate_count++] = Candidate{
                action,
                prepared[action].upper,
            };
        }
        std::sort(
            candidates.begin(),
            candidates.begin() + candidate_count,
            [](const Candidate& left, const Candidate& right) {
                return pipeline_label_less(right.upper, left.upper);
            }
        );
        bool have_best = false;
        for (int order = 0; order < candidate_count; ++order) {
            const Candidate& candidate = candidates[order];
            if (
                have_best
                && pipeline_label_less_equal(candidate.upper, best)
            ) {
                ++counters_.action_upper_prunes;
                continue;
            }
            const PipelineLabel label = evaluate_action(
                state,
                prepared[candidate.action],
                have_best ? &best : nullptr
            );
            if (!have_best || pipeline_label_less(best, label)) {
                best = label;
                have_best = true;
            }
        }
        memo_.emplace(state, best);
        return best;
    }

    RootNode query_root(BeliefPipelineState state) {
        check_abort();
        state = canonicalize(state);
        const auto found = root_memo_.find(state);
        if (found != root_memo_.end()) {
            ++counters_.root_memo_hits;
            return found->second;
        }
        RootNode node;
        const float margin = current_margin(state);
        if (state.frame == frame_count_ - 1 || margin <= 0.0F) {
            node.state = PipelineLabel{0, margin};
            node.actions.fill(node.state);
        } else {
            for (int action = 0; action < action_count_; ++action) {
                const PreparedAction prepared = prepare_action(
                    state,
                    action,
                    true
                );
                node.actions[action] = evaluate_action(
                    state,
                    prepared,
                    nullptr
                );
            }
            node.state = node.actions[0];
            for (int action = 1; action < action_count_; ++action) {
                if (
                    pipeline_label_less(
                        node.state,
                        node.actions[action]
                    )
                ) {
                    node.state = node.actions[action];
                }
            }
        }
        root_memo_.emplace(state, node);
        return node;
    }

    const float* clearance_;
    int frame_count_;
    int row_count_;
    int column_count_;
    double x_start_;
    double x_step_;
    double y_start_;
    double y_step_;
    int action_count_;
    std::uint32_t base_action_mask_;
    std::uint32_t budgeted_action_mask_;
    int continuation_budget_;
    bool reveal_remaining_delay_;
    float required_clearance_;
    bool clamp_to_bounds_;
    std::vector<double> velocity_x_;
    std::vector<double> velocity_y_;
    std::vector<int> delay_frames_;
    std::vector<int> cadence_frames_;
    std::unordered_map<
        BeliefPipelineState,
        PipelineLabel,
        BeliefPipelineStateHash
    > memo_;
    std::unordered_map<
        BeliefPipelineState,
        RootNode,
        BeliefPipelineStateHash
    > root_memo_;
    Counters counters_;
    std::atomic<bool> cancel_requested_{false};
    bool deadline_active_ = false;
    Clock::time_point deadline_{};
    std::uint64_t abort_poll_counter_ = 0;
    std::mutex mutex_;
};

}  // namespace

TOUHOU_EXPORT int touhou_belief_pipeline_workspace_create_v4(
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
    std::uint32_t base_action_mask,
    std::uint32_t budgeted_action_mask,
    int continuation_budget,
    int reveal_remaining_delay,
    const int* delay_frames,
    int delay_count,
    const int* cadence_frames,
    int cadence_count,
    float required_clearance,
    int clamp_to_bounds,
    void** output_workspace
) {
    if (
        clearance == nullptr || velocity_x == nullptr
        || velocity_y == nullptr || delay_frames == nullptr
        || cadence_frames == nullptr || output_workspace == nullptr
    ) {
        return 1;
    }
    if (
        frame_count < 2 || frame_count - 1 > 65535
        || row_count < 2 || row_count > 1024
        || column_count < 2 || column_count > 1024
        || x_step <= 0.0 || y_step <= 0.0
        || action_count < 1 || action_count > PIPELINE_MAX_ACTIONS
        || base_action_mask == 0
        || continuation_budget < 0 || continuation_budget > 65535
        || (
            (base_action_mask | budgeted_action_mask)
            & ~(
                action_count == 32
                ? std::numeric_limits<std::uint32_t>::max()
                : (
                    (std::uint32_t{1} << action_count)
                    - std::uint32_t{1}
                )
            )
        ) != 0
        || (base_action_mask & budgeted_action_mask) != 0
        || delay_count < 1 || delay_count > PIPELINE_MAX_DELAYS
        || cadence_count < 1
        || cadence_count > PIPELINE_MAX_DECISION_FRAMES
        || delay_frames[delay_count - 1]
            > BELIEF_PIPELINE_MAX_REMAINING
    ) {
        return 2;
    }
    for (int index = 0; index < delay_count; ++index) {
        if (
            delay_frames[index] < 0
            || (
                index > 0
                && delay_frames[index - 1] >= delay_frames[index]
            )
        ) {
            return 3;
        }
    }
    for (int index = 0; index < cadence_count; ++index) {
        if (
            cadence_frames[index] <= 0
            || (
                index > 0
                && cadence_frames[index - 1] >= cadence_frames[index]
            )
        ) {
            return 3;
        }
    }
    try {
        *output_workspace = new BeliefPipelineSurvivalWorkspace(
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
            budgeted_action_mask,
            continuation_budget,
            reveal_remaining_delay != 0,
            delay_frames,
            delay_count,
            cadence_frames,
            cadence_count,
            required_clearance,
            clamp_to_bounds != 0
        );
    } catch (...) {
        *output_workspace = nullptr;
        return 4;
    }
    return 0;
}

TOUHOU_EXPORT int touhou_belief_pipeline_workspace_create_v3(
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
    std::uint32_t base_action_mask,
    std::uint32_t budgeted_action_mask,
    int continuation_budget,
    const int* delay_frames,
    int delay_count,
    const int* cadence_frames,
    int cadence_count,
    float required_clearance,
    int clamp_to_bounds,
    void** output_workspace
) {
    return touhou_belief_pipeline_workspace_create_v4(
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
        budgeted_action_mask,
        continuation_budget,
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

TOUHOU_EXPORT int touhou_belief_pipeline_workspace_create_v2(
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
    std::uint32_t continuation_action_mask,
    const int* delay_frames,
    int delay_count,
    const int* cadence_frames,
    int cadence_count,
    float required_clearance,
    int clamp_to_bounds,
    void** output_workspace
) {
    return touhou_belief_pipeline_workspace_create_v3(
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
        continuation_action_mask,
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

TOUHOU_EXPORT int touhou_belief_pipeline_workspace_create_v1(
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
    const int* cadence_frames,
    int cadence_count,
    float required_clearance,
    int clamp_to_bounds,
    void** output_workspace
) {
    const std::uint32_t every_action_mask = (
        action_count == 32
        ? std::numeric_limits<std::uint32_t>::max()
        : (
            (std::uint32_t{1} << action_count)
            - std::uint32_t{1}
        )
    );
    return touhou_belief_pipeline_workspace_create_v2(
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
        every_action_mask,
        delay_frames,
        delay_count,
        cadence_frames,
        cadence_count,
        required_clearance,
        clamp_to_bounds,
        output_workspace
    );
}

TOUHOU_EXPORT int touhou_belief_pipeline_workspace_query_v2(
    void* workspace,
    int start_frame,
    int start_row,
    int start_column,
    int observed_action,
    int pending_action,
    const int* pending_remaining_frames,
    int pending_remaining_count,
    int continuation_action_budget,
    int timeout_ms,
    std::uint16_t* output_state_frames,
    float* output_state_margin,
    std::uint16_t* output_action_frames,
    float* output_action_margins,
    std::uint32_t* output_best_action_mask,
    std::uint64_t* output_stats
) {
    if (
        workspace == nullptr || output_state_frames == nullptr
        || output_state_margin == nullptr
        || output_action_frames == nullptr
        || output_action_margins == nullptr
        || output_best_action_mask == nullptr || output_stats == nullptr
    ) {
        return 1;
    }
    try {
        return static_cast<BeliefPipelineSurvivalWorkspace*>(
            workspace
        )->query(
            start_frame,
            start_row,
            start_column,
            observed_action,
            pending_action,
            pending_remaining_frames,
            pending_remaining_count,
            continuation_action_budget,
            timeout_ms,
            output_state_frames,
            output_state_margin,
            output_action_frames,
            output_action_margins,
            output_best_action_mask,
            output_stats
        );
    } catch (const PipelineCancelledSignal&) {
        return PIPELINE_RESULT_CANCELLED;
    } catch (const PipelineDeadlineSignal&) {
        return PIPELINE_RESULT_DEADLINE;
    } catch (...) {
        return 2;
    }
}

TOUHOU_EXPORT int touhou_belief_pipeline_workspace_query_v1(
    void* workspace,
    int start_frame,
    int start_row,
    int start_column,
    int observed_action,
    int pending_action,
    const int* pending_remaining_frames,
    int pending_remaining_count,
    int timeout_ms,
    std::uint16_t* output_state_frames,
    float* output_state_margin,
    std::uint16_t* output_action_frames,
    float* output_action_margins,
    std::uint32_t* output_best_action_mask,
    std::uint64_t* output_stats
) {
    return touhou_belief_pipeline_workspace_query_v2(
        workspace,
        start_frame,
        start_row,
        start_column,
        observed_action,
        pending_action,
        pending_remaining_frames,
        pending_remaining_count,
        -1,
        timeout_ms,
        output_state_frames,
        output_state_margin,
        output_action_frames,
        output_action_margins,
        output_best_action_mask,
        output_stats
    );
}

TOUHOU_EXPORT int touhou_belief_pipeline_workspace_cancel_v1(
    void* workspace
) {
    if (workspace == nullptr) {
        return 1;
    }
    static_cast<BeliefPipelineSurvivalWorkspace*>(
        workspace
    )->request_cancel();
    return 0;
}

TOUHOU_EXPORT void touhou_belief_pipeline_workspace_destroy_v1(
    void* workspace
) {
    delete static_cast<BeliefPipelineSurvivalWorkspace*>(workspace);
}
