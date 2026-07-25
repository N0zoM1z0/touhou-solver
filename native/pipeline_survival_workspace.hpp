#pragma once

// Included after the shared lattice-sampling helpers.
namespace {

constexpr int PIPELINE_MAX_ACTIONS = 32;
constexpr int PIPELINE_MAX_DELAYS = 64;
constexpr int PIPELINE_MAX_DECISION_FRAMES = 16;
constexpr int PIPELINE_MAX_BRANCHES =
    PIPELINE_MAX_DELAYS * PIPELINE_MAX_DECISION_FRAMES;
constexpr std::uint64_t PIPELINE_EMPTY_KEY =
    std::numeric_limits<std::uint64_t>::max();

struct PipelineLabel {
    std::uint16_t frames;
    float margin;
};

inline bool pipeline_label_less(
    const PipelineLabel& left,
    const PipelineLabel& right
) {
    return (
        left.frames < right.frames
        || (
            left.frames == right.frames
            && left.margin < right.margin
        )
    );
}

inline bool pipeline_label_equal(
    const PipelineLabel& left,
    const PipelineLabel& right
) {
    return left.frames == right.frames && left.margin == right.margin;
}

inline bool pipeline_label_less_equal(
    const PipelineLabel& left,
    const PipelineLabel& right
) {
    return (
        pipeline_label_less(left, right)
        || pipeline_label_equal(left, right)
    );
}

struct PipelineState {
    int frame;
    int active;
    int pending;
    int pending_remaining;
    int row;
    int column;
};

class PipelineFlatMemo {
public:
    PipelineFlatMemo() {
        rehash(1024);
    }

    bool find(std::uint64_t key, PipelineLabel* output) const {
        std::size_t slot = hash_key(key) & (entries_.size() - 1);
        while (true) {
            const Entry& entry = entries_[slot];
            if (entry.key == PIPELINE_EMPTY_KEY) {
                return false;
            }
            if (entry.key == key) {
                *output = entry.label;
                return true;
            }
            slot = (slot + 1) & (entries_.size() - 1);
        }
    }

    void insert(std::uint64_t key, const PipelineLabel& label) {
        if ((size_ + 1) * 10 >= entries_.size() * 7) {
            rehash(entries_.size() * 2);
        }
        insert_without_growth(key, label);
    }

    std::size_t size() const {
        return size_;
    }

private:
    struct Entry {
        std::uint64_t key = PIPELINE_EMPTY_KEY;
        PipelineLabel label{0, 0.0F};
    };

    static std::uint64_t hash_key(std::uint64_t value) {
        value += 0x9e3779b97f4a7c15ULL;
        value = (value ^ (value >> 30)) * 0xbf58476d1ce4e5b9ULL;
        value = (value ^ (value >> 27)) * 0x94d049bb133111ebULL;
        return value ^ (value >> 31);
    }

    void insert_without_growth(
        std::uint64_t key,
        const PipelineLabel& label
    ) {
        std::size_t slot = hash_key(key) & (entries_.size() - 1);
        while (true) {
            Entry& entry = entries_[slot];
            if (entry.key == PIPELINE_EMPTY_KEY) {
                entry.key = key;
                entry.label = label;
                ++size_;
                return;
            }
            if (entry.key == key) {
                entry.label = label;
                return;
            }
            slot = (slot + 1) & (entries_.size() - 1);
        }
    }

    void rehash(std::size_t capacity) {
        std::vector<Entry> previous = std::move(entries_);
        entries_.assign(capacity, Entry{});
        size_ = 0;
        for (const Entry& entry : previous) {
            if (entry.key != PIPELINE_EMPTY_KEY) {
                insert_without_growth(entry.key, entry.label);
            }
        }
    }

    std::vector<Entry> entries_;
    std::size_t size_ = 0;
};

class PipelineSurvivalWorkspace {
public:
    PipelineSurvivalWorkspace(
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
        const int* decision_frame_support,
        int decision_frame_count,
        int continuation_decision_frames,
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
          continuation_decision_frames_(continuation_decision_frames),
          required_clearance_(required_clearance),
          clamp_to_bounds_(clamp_to_bounds),
          velocity_x_(velocity_x, velocity_x + action_count),
          velocity_y_(velocity_y, velocity_y + action_count),
          delay_frames_(delay_frames, delay_frames + delay_count),
          decision_frame_support_(
              decision_frame_support,
              decision_frame_support + decision_frame_count
          ) {
        root_memo_.reserve(1024);
    }

    int query(
        int start_frame,
        int start_row,
        int start_column,
        int observed_action,
        int pending_action,
        const int* pending_remaining_frames,
        int pending_remaining_count,
        std::uint16_t* output_state_frames,
        float* output_state_margin,
        std::uint16_t* output_action_frames,
        float* output_action_margins,
        std::uint32_t* output_best_action_mask,
        std::uint64_t* output_stats
    ) {
        if (
            start_frame < 0 || start_frame >= frame_count_
            || start_row < 0 || start_row >= row_count_
            || start_column < 0 || start_column >= column_count_
            || observed_action < 0 || observed_action >= action_count_
            || pending_action < -1 || pending_action >= action_count_
            || pending_remaining_count < 0
            || pending_remaining_count > PIPELINE_MAX_DELAYS
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
        for (int index = 0; index < pending_remaining_count; ++index) {
            if (
                pending_remaining_frames[index] <= 0
                || pending_remaining_frames[index] > frame_count_ - 1
                || (
                    index > 0
                    && pending_remaining_frames[index - 1]
                        >= pending_remaining_frames[index]
                )
            ) {
                return 1;
            }
        }
        std::lock_guard<std::mutex> guard(mutex_);
        const Counters before = counters_;
        const std::size_t memo_before = memo_.size();

        std::array<RootNode, PIPELINE_MAX_DELAYS> roots;
        int root_count = 0;
        if (pending_action < 0) {
            roots[root_count++] = query_root(
                PipelineState{
                    start_frame,
                    observed_action,
                    -1,
                    0,
                    start_row,
                    start_column,
                }
            );
        } else {
            for (int index = 0; index < pending_remaining_count; ++index) {
                roots[root_count++] = query_root(
                    PipelineState{
                        start_frame,
                        observed_action,
                        pending_action,
                        pending_remaining_frames[index],
                        start_row,
                        start_column,
                    }
                );
            }
        }

        PipelineLabel state_best{
            0,
            -std::numeric_limits<float>::infinity(),
        };
        std::uint32_t best_mask = 0;
        for (int action = 0; action < action_count_; ++action) {
            PipelineLabel robust = roots[0].actions[action];
            for (int root = 1; root < root_count; ++root) {
                if (pipeline_label_less(roots[root].actions[action], robust)) {
                    robust = roots[root].actions[action];
                }
            }
            output_action_frames[action] = robust.frames;
            output_action_margins[action] = robust.margin;
            if (action == 0 || pipeline_label_less(state_best, robust)) {
                state_best = robust;
                best_mask = std::uint32_t{1} << action;
            } else if (pipeline_label_equal(state_best, robust)) {
                best_mask |= std::uint32_t{1} << action;
            }
        }
        *output_state_frames = state_best.frames;
        *output_state_margin = state_best.margin;
        *output_best_action_mask = best_mask;

        output_stats[0] = static_cast<std::uint64_t>(memo_.size());
        output_stats[1] = static_cast<std::uint64_t>(
            memo_.size() - memo_before
        );
        output_stats[2] = counters_.memo_hits - before.memo_hits;
        output_stats[3] = (
            counters_.action_upper_prunes - before.action_upper_prunes
        );
        output_stats[4] = (
            counters_.delay_incumbent_prunes
            - before.delay_incumbent_prunes
        );
        output_stats[5] = (
            counters_.canonicalizations - before.canonicalizations
        );
        output_stats[6] = (
            counters_.root_memo_hits - before.root_memo_hits
        );
        output_stats[7] = (
            counters_.branch_simulations - before.branch_simulations
        );
        return 0;
    }

    int contains_root(
        int start_frame,
        int start_row,
        int start_column,
        int observed_action,
        int pending_action,
        const int* pending_remaining_frames,
        int pending_remaining_count,
        int* output_present
    ) {
        if (
            output_present == nullptr
            || start_frame < 0 || start_frame >= frame_count_
            || start_row < 0 || start_row >= row_count_
            || start_column < 0 || start_column >= column_count_
            || observed_action < 0 || observed_action >= action_count_
            || pending_action < -1 || pending_action >= action_count_
            || pending_remaining_count < 0
            || pending_remaining_count > PIPELINE_MAX_DELAYS
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
        for (int index = 0; index < pending_remaining_count; ++index) {
            if (
                pending_remaining_frames[index] <= 0
                || pending_remaining_frames[index] > frame_count_ - 1
                || (
                    index > 0
                    && pending_remaining_frames[index - 1]
                        >= pending_remaining_frames[index]
                )
            ) {
                return 1;
            }
        }

        std::lock_guard<std::mutex> guard(mutex_);
        auto present = [&](int pending, int remaining) {
            PipelineState state{
                start_frame,
                observed_action,
                pending,
                remaining,
                start_row,
                start_column,
            };
            state = canonicalize(state);
            return root_memo_.find(state_key(state)) != root_memo_.end();
        };
        if (pending_action < 0) {
            *output_present = present(-1, 0) ? 1 : 0;
            return 0;
        }
        for (int index = 0; index < pending_remaining_count; ++index) {
            if (!present(
                    pending_action,
                    pending_remaining_frames[index]
                )) {
                *output_present = 0;
                return 0;
            }
        }
        *output_present = 1;
        return 0;
    }

private:
    struct Counters {
        std::uint64_t memo_hits = 0;
        std::uint64_t action_upper_prunes = 0;
        std::uint64_t delay_incumbent_prunes = 0;
        std::uint64_t canonicalizations = 0;
        std::uint64_t root_memo_hits = 0;
        std::uint64_t branch_simulations = 0;
    };

    struct Branch {
        PipelineLabel upper;
        PipelineLabel failed_label;
        PipelineLabel prefix;
        PipelineState successor;
        int step_count;
        bool failed;
    };

    struct ActionCandidate {
        int action;
        PipelineLabel upper;
    };

    struct RootNode {
        PipelineLabel state;
        std::array<PipelineLabel, PIPELINE_MAX_ACTIONS> actions;
    };

    static std::uint64_t state_key(const PipelineState& state) {
        return (
            static_cast<std::uint64_t>(state.frame)
            | (static_cast<std::uint64_t>(state.row) << 16)
            | (static_cast<std::uint64_t>(state.column) << 26)
            | (static_cast<std::uint64_t>(state.active) << 36)
            | (
                static_cast<std::uint64_t>(state.pending + 1)
                << 41
            )
            | (
                static_cast<std::uint64_t>(state.pending_remaining)
                << 47
            )
        );
    }

    PipelineState canonicalize(PipelineState state) {
        if (state.pending < 0) {
            state.pending_remaining = 0;
            return state;
        }
        if (
            state.pending == state.active
            || (
                velocity_x_[state.pending] == velocity_x_[state.active]
                && velocity_y_[state.pending] == velocity_y_[state.active]
            )
            || state.pending_remaining >= delay_frames_.back()
        ) {
            state.pending = -1;
            state.pending_remaining = 0;
            ++counters_.canonicalizations;
        }
        return state;
    }

    float current_margin(const PipelineState& state) const {
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

    Branch prepare_branch(
        const PipelineState& state,
        int selected,
        int delay,
        int decision_frames
    ) {
        ++counters_.branch_simulations;
        const int horizon_frame = frame_count_ - 1;
        const int step_count = std::min(
            decision_frames,
            horizon_frame - state.frame
        );
        const float initial_margin = current_margin(state);
        PipelineLabel prefix{0, initial_margin};
        Sample terminal{-1, -1, 0.0, false};
        double displacement_x = 0.0;
        double displacement_y = 0.0;
        const double state_x = x_start_ + state.column * x_step_;
        const double state_y = y_start_ + state.row * y_step_;
        for (int step = 1; step <= step_count; ++step) {
            int motion = state.active;
            if (step > delay) {
                motion = selected;
            } else if (
                state.pending >= 0
                && step > state.pending_remaining
            ) {
                motion = state.pending;
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
                return Branch{
                    failed,
                    failed,
                    prefix,
                    state,
                    step_count,
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
            prefix.margin = std::min(prefix.margin, margin);
            if (margin <= 0.0F) {
                const PipelineLabel failed{
                    static_cast<std::uint16_t>(step - 1),
                    prefix.margin,
                };
                return Branch{
                    failed,
                    failed,
                    prefix,
                    state,
                    step_count,
                    true,
                };
            }
        }

        int successor_active = state.active;
        int successor_pending = selected;
        int successor_remaining = delay - step_count;
        if (delay < step_count || successor_remaining == 0) {
            successor_active = selected;
            successor_pending = -1;
            successor_remaining = 0;
        } else if (
            state.pending >= 0
            && state.pending_remaining <= step_count
        ) {
            successor_active = state.pending;
        }
        PipelineState successor{
            state.frame + step_count,
            successor_active,
            successor_pending,
            successor_remaining,
            terminal.row,
            terminal.column,
        };
        successor = canonicalize(successor);
        const PipelineLabel upper{
            static_cast<std::uint16_t>(horizon_frame - state.frame),
            prefix.margin,
        };
        return Branch{
            upper,
            PipelineLabel{0, 0.0F},
            prefix,
            successor,
            step_count,
            false,
        };
    }

    PipelineLabel action_upper(
        const PipelineState& state,
        int selected,
        bool root_transition
    ) {
        PipelineLabel upper{
            std::numeric_limits<std::uint16_t>::max(),
            std::numeric_limits<float>::infinity(),
        };
        const int decision_count = (
            root_transition
            ? static_cast<int>(decision_frame_support_.size())
            : 1
        );
        for (int decision_index = 0; decision_index < decision_count;
             ++decision_index) {
            const int decision_frames = (
                root_transition
                ? decision_frame_support_[decision_index]
                : continuation_decision_frames_
            );
            for (int delay : delay_frames_) {
                const Branch branch = prepare_branch(
                    state,
                    selected,
                    delay,
                    decision_frames
                );
                if (pipeline_label_less(branch.upper, upper)) {
                    upper = branch.upper;
                }
            }
        }
        return upper;
    }

    PipelineLabel evaluate_action(
        const PipelineState& state,
        int selected,
        const PipelineLabel* incumbent,
        bool root_transition
    ) {
        std::array<Branch, PIPELINE_MAX_BRANCHES> branches;
        std::array<int, PIPELINE_MAX_BRANCHES> order;
        const int delay_count = static_cast<int>(delay_frames_.size());
        const int decision_count = static_cast<int>(
            root_transition ? decision_frame_support_.size() : 1
        );
        const int branch_count = delay_count * decision_count;
        int branch_index = 0;
        for (int decision_index = 0; decision_index < decision_count;
             ++decision_index) {
            const int decision_frames = (
                root_transition
                ? decision_frame_support_[decision_index]
                : continuation_decision_frames_
            );
            for (int delay : delay_frames_) {
                branches[branch_index] = prepare_branch(
                    state,
                    selected,
                    delay,
                    decision_frames
                );
                order[branch_index] = branch_index;
                ++branch_index;
            }
        }
        std::sort(
            order.begin(),
            order.begin() + branch_count,
            [&](int left, int right) {
                return pipeline_label_less(
                    branches[left].upper,
                    branches[right].upper
                );
            }
        );

        PipelineLabel robust{
            std::numeric_limits<std::uint16_t>::max(),
            std::numeric_limits<float>::infinity(),
        };
        for (int rank = 0; rank < branch_count; ++rank) {
            const Branch& branch = branches[order[rank]];
            PipelineLabel label;
            if (branch.failed) {
                label = branch.failed_label;
            } else {
                const PipelineLabel successor = solve(branch.successor);
                label = PipelineLabel{
                    static_cast<std::uint16_t>(
                        branch.step_count + successor.frames
                    ),
                    std::min(branch.prefix.margin, successor.margin),
                };
            }
            if (pipeline_label_less(label, robust)) {
                robust = label;
            }
            if (
                incumbent != nullptr
                && pipeline_label_less_equal(robust, *incumbent)
                && rank + 1 < branch_count
            ) {
                counters_.delay_incumbent_prunes += (
                    branch_count - rank - 1
                );
                break;
            }
        }
        return robust;
    }

    PipelineLabel solve(PipelineState state) {
        state = canonicalize(state);
        const std::uint64_t key = state_key(state);
        PipelineLabel cached;
        if (memo_.find(key, &cached)) {
            ++counters_.memo_hits;
            return cached;
        }

        const float margin = current_margin(state);
        if (state.frame == frame_count_ - 1 || margin <= 0.0F) {
            const PipelineLabel terminal{0, margin};
            memo_.insert(key, terminal);
            return terminal;
        }

        std::array<ActionCandidate, PIPELINE_MAX_ACTIONS> candidates;
        for (int action = 0; action < action_count_; ++action) {
            candidates[action] = ActionCandidate{
                action,
                action_upper(state, action, false),
            };
        }
        std::sort(
            candidates.begin(),
            candidates.begin() + action_count_,
            [](const ActionCandidate& left, const ActionCandidate& right) {
                return pipeline_label_less(right.upper, left.upper);
            }
        );

        PipelineLabel best{
            0,
            -std::numeric_limits<float>::infinity(),
        };
        bool have_best = false;
        for (int index = 0; index < action_count_; ++index) {
            const ActionCandidate& candidate = candidates[index];
            if (
                have_best
                && pipeline_label_less_equal(candidate.upper, best)
            ) {
                ++counters_.action_upper_prunes;
                continue;
            }
            const PipelineLabel action_label = evaluate_action(
                state,
                candidate.action,
                have_best ? &best : nullptr,
                false
            );
            if (!have_best || pipeline_label_less(best, action_label)) {
                best = action_label;
                have_best = true;
            }
        }
        memo_.insert(key, best);
        return best;
    }

    RootNode query_root(PipelineState state) {
        state = canonicalize(state);
        const std::uint64_t key = state_key(state);
        const auto found = root_memo_.find(key);
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
                node.actions[action] = evaluate_action(
                    state,
                    action,
                    nullptr,
                    true
                );
            }
            node.state = node.actions[0];
            for (int action = 1; action < action_count_; ++action) {
                if (pipeline_label_less(node.state, node.actions[action])) {
                    node.state = node.actions[action];
                }
            }
        }
        root_memo_.emplace(key, node);
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
    int continuation_decision_frames_;
    float required_clearance_;
    bool clamp_to_bounds_;
    std::vector<double> velocity_x_;
    std::vector<double> velocity_y_;
    std::vector<int> delay_frames_;
    std::vector<int> decision_frame_support_;
    PipelineFlatMemo memo_;
    std::unordered_map<std::uint64_t, RootNode> root_memo_;
    Counters counters_;
    std::mutex mutex_;
};

}  // namespace

TOUHOU_EXPORT int touhou_pipeline_survival_workspace_create_v2(
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
    const int* decision_frame_support,
    int decision_frame_count,
    int continuation_decision_frames,
    float required_clearance,
    int clamp_to_bounds,
    void** output_workspace
) {
    if (
        clearance == nullptr || velocity_x == nullptr
        || velocity_y == nullptr || delay_frames == nullptr
        || decision_frame_support == nullptr
        || output_workspace == nullptr
    ) {
        return 1;
    }
    if (
        frame_count < 2 || frame_count - 1 > 65535
        || row_count < 2 || row_count > 1024
        || column_count < 2 || column_count > 1024
        || x_step <= 0.0 || y_step <= 0.0
        || action_count < 1 || action_count > PIPELINE_MAX_ACTIONS
        || delay_count < 1 || delay_count > PIPELINE_MAX_DELAYS
        || decision_frame_count < 1
        || decision_frame_count > PIPELINE_MAX_DECISION_FRAMES
        || continuation_decision_frames < 1
    ) {
        return 2;
    }
    for (int index = 0; index < delay_count; ++index) {
        if (
            delay_frames[index] < 0
            || delay_frames[index] > frame_count - 1
            || (
                index > 0
                && delay_frames[index - 1] >= delay_frames[index]
            )
        ) {
            return 3;
        }
    }
    for (int index = 0; index < decision_frame_count; ++index) {
        if (
            decision_frame_support[index] < 1
            || (
                index > 0
                && decision_frame_support[index - 1]
                    >= decision_frame_support[index]
            )
        ) {
            return 3;
        }
    }
    try {
        *output_workspace = new PipelineSurvivalWorkspace(
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
            delay_frames,
            delay_count,
            decision_frame_support,
            decision_frame_count,
            continuation_decision_frames,
            required_clearance,
            clamp_to_bounds != 0
        );
    } catch (...) {
        *output_workspace = nullptr;
        return 4;
    }
    return 0;
}

TOUHOU_EXPORT int touhou_pipeline_survival_workspace_create_v1(
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
    int decision_frames,
    float required_clearance,
    int clamp_to_bounds,
    void** output_workspace
) {
    return touhou_pipeline_survival_workspace_create_v2(
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
        delay_frames,
        delay_count,
        &decision_frames,
        1,
        decision_frames,
        required_clearance,
        clamp_to_bounds,
        output_workspace
    );
}

TOUHOU_EXPORT int touhou_pipeline_survival_workspace_query_v1(
    void* workspace,
    int start_frame,
    int start_row,
    int start_column,
    int observed_action,
    int pending_action,
    const int* pending_remaining_frames,
    int pending_remaining_count,
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
    PipelineSurvivalWorkspace* typed =
        static_cast<PipelineSurvivalWorkspace*>(workspace);
    try {
        return typed->query(
            start_frame,
            start_row,
            start_column,
            observed_action,
            pending_action,
            pending_remaining_frames,
            pending_remaining_count,
            output_state_frames,
            output_state_margin,
            output_action_frames,
            output_action_margins,
            output_best_action_mask,
            output_stats
        );
    } catch (...) {
        return 2;
    }
}

TOUHOU_EXPORT int touhou_pipeline_survival_workspace_contains_root_v1(
    void* workspace,
    int start_frame,
    int start_row,
    int start_column,
    int observed_action,
    int pending_action,
    const int* pending_remaining_frames,
    int pending_remaining_count,
    int* output_present
) {
    if (workspace == nullptr || output_present == nullptr) {
        return 1;
    }
    PipelineSurvivalWorkspace* typed =
        static_cast<PipelineSurvivalWorkspace*>(workspace);
    try {
        return typed->contains_root(
            start_frame,
            start_row,
            start_column,
            observed_action,
            pending_action,
            pending_remaining_frames,
            pending_remaining_count,
            output_present
        );
    } catch (...) {
        return 2;
    }
}

TOUHOU_EXPORT void touhou_pipeline_survival_workspace_destroy_v1(
    void* workspace
) {
    delete static_cast<PipelineSurvivalWorkspace*>(workspace);
}
