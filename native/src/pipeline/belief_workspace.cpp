// Exact recursive belief-pipeline workspace implementation and C ABI.

#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <limits>
#include <memory>
#include <mutex>
#include <unordered_map>
#include <utility>
#include <vector>

#include "src/internal/abi_impl.hpp"
#include "include/touhou_native/lattice.hpp"
#include "include/touhou_native/status.hpp"
#include "include/touhou_native/survival_label.hpp"
#include "robust_transition_table.hpp"

// Recursive variable-cadence belief workspace over the shared lattice
// helpers. This workspace solves the recursively variable-cadence
// information-set game with physical hold/no-write semantics.  The held
// desired action is pending when pending >= 0, otherwise active.  Selecting
// that action sends no new command and carries the old pending countdown.
// A public continuation budget limits non-base future actions and produces
// nested attainable lower bounds.  An optional remaining-delay bucket
// partition is an explicit optimistic information relaxation.  Bucket width
// one reveals exact remaining delay; wider buckets reveal less information
// and therefore provide tighter upper bounds.
// It is separate from the older always-issue/one-transition workspace so
// experiments cannot silently change either contract.
namespace {

using namespace touhou_native;

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
        std::array<PipelineLabel, BELIEF_PIPELINE_MAX_ACTIONS> actions;
    };

    struct PreparedAction {
        PipelineLabel upper{
            std::numeric_limits<std::uint16_t>::max(),
            std::numeric_limits<float>::infinity(),
        };
        PipelineLabel proposal{
            std::numeric_limits<std::uint16_t>::max(),
            std::numeric_limits<float>::infinity(),
        };
        std::vector<BeliefPipelineTransition> transitions;
        bool threshold_rejected = false;
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

    enum class ThresholdRootStatus : std::uint8_t {
        unknown = 0,
        rejected = 1,
        exceeds = 2,
    };

    static std::uint32_t float_bits(float value) {
        std::uint32_t bits = 0;
        std::memcpy(&bits, &value, sizeof(bits));
        return bits;
    }

    std::uint64_t remaining_delay_observation(
        std::uint64_t remaining_mask
    ) const {
        if (remaining_delay_bucket_size_ <= 0) {
            return 0;
        }
        std::uint64_t observation = 0;
        for (
            int remaining = 0;
            remaining <= BELIEF_PIPELINE_MAX_REMAINING;
            ++remaining
        ) {
            if (
                (remaining_mask
                 & (std::uint64_t{1} << remaining)) == 0
            ) {
                continue;
            }
            const int bucket = (
                remaining == 0
                ? 0
                : 1 + (
                    (remaining - 1)
                    / remaining_delay_bucket_size_
                )
            );
            observation |= std::uint64_t{1} << bucket;
        }
        return observation;
    }

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
        std::uint64_t base_action_mask,
        std::uint64_t budgeted_action_mask,
        int continuation_budget,
        int remaining_delay_bucket_size,
        int continuation_policy_mode,
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
          remaining_delay_bucket_size_(remaining_delay_bucket_size),
          continuation_policy_mode_(continuation_policy_mode),
          required_clearance_(required_clearance),
          clamp_to_bounds_(clamp_to_bounds),
          velocity_x_(velocity_x, velocity_x + action_count),
          velocity_y_(velocity_y, velocity_y + action_count),
          delay_frames_(delay_frames, delay_frames + delay_count),
          cadence_frames_(cadence_frames, cadence_frames + cadence_count) {
        future_global_margin_upper_.resize(frame_count_);
        float suffix_upper = std::numeric_limits<float>::infinity();
        for (int frame = frame_count_ - 1; frame >= 0; --frame) {
            float frame_upper =
                -std::numeric_limits<float>::infinity();
            for (int row = 0; row < row_count_; ++row) {
                for (int column = 0; column < column_count_; ++column) {
                    frame_upper = std::max(
                        frame_upper,
                        clearance_[clearance_index(
                            frame,
                            row,
                            column,
                            row_count_,
                            column_count_
                        )] - required_clearance_
                    );
                }
            }
            suffix_upper = std::min(suffix_upper, frame_upper);
            future_global_margin_upper_[frame] = suffix_upper;
        }
        memo_.reserve(4096);
        best_action_memo_.reserve(4096);
        root_memo_.reserve(256);
        threshold_memo_[0].reserve(4096);
        threshold_memo_[1].reserve(4096);
    }

    int action_count() const noexcept {
        return action_count_;
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
        std::uint64_t* output_best_action_mask,
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
        std::uint64_t best_mask = 0;
        for (int action = 0; action < action_count_; ++action) {
            output_action_frames[action] = root.actions[action].frames;
            output_action_margins[action] = root.actions[action].margin;
            if (pipeline_label_equal(root.actions[action], root.state)) {
                best_mask |= std::uint64_t{1} << action;
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

    int certify_upper(
        int start_frame,
        int start_row,
        int start_column,
        int observed_action,
        int pending_action,
        const int* pending_remaining_frames,
        int pending_remaining_count,
        int root_continuation_budget,
        std::uint16_t lower_frames,
        float lower_margin,
        int timeout_ms,
        std::uint64_t* output_unresolved_action_mask,
        int* output_deadline_expired,
        std::uint64_t* output_stats
    ) {
        const int query_budget = (
            root_continuation_budget < 0
            ? continuation_budget_
            : root_continuation_budget
        );
        if (
            remaining_delay_bucket_size_ <= 0
            || continuation_policy_mode_ != 0
            || start_frame < 0 || start_frame >= frame_count_
            || start_row < 0 || start_row >= row_count_
            || start_column < 0 || start_column >= column_count_
            || observed_action < 0 || observed_action >= action_count_
            || pending_action < -1 || pending_action >= action_count_
            || pending_remaining_count < 0
            || pending_remaining_count > BELIEF_PIPELINE_MAX_REMAINING
            || query_budget < 0
            || query_budget > continuation_budget_
            || lower_frames > frame_count_ - 1 - start_frame
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
        BeliefPipelineState state{
            start_frame,
            start_row,
            start_column,
            observed_action,
            pending_action,
            query_budget,
            remaining_mask,
        };
        state = canonicalize(state);
        // A deadline never memoizes its incomplete stack. Reuse only
        // completed threshold subproblems for this bit-identical session.
        const int target_frame = start_frame + lower_frames;
        const std::uint32_t target_margin_bits = float_bits(lower_margin);
        const bool same_threshold_session = (
            threshold_session_active_
            && threshold_session_root_ == state
            && threshold_session_target_frame_ == target_frame
            && threshold_session_target_margin_bits_
                == target_margin_bits
        );
        if (!same_threshold_session) {
            threshold_memo_[0].clear();
            threshold_memo_[1].clear();
            threshold_root_status_.fill(
                ThresholdRootStatus::unknown
            );
            threshold_session_active_ = true;
            threshold_session_root_ = state;
            threshold_session_target_frame_ = target_frame;
            threshold_session_target_margin_bits_ =
                target_margin_bits;
        }
        threshold_target_frame_ = target_frame;
        threshold_target_margin_ = lower_margin;
        const std::size_t threshold_memo_before = (
            threshold_memo_[0].size() + threshold_memo_[1].size()
        );

        std::uint64_t unresolved_mask = 0;
        bool deadline_expired = false;
        const float margin = current_margin(state);
        if (state.frame == frame_count_ - 1 || margin <= 0.0F) {
            const PipelineLabel terminal{0, margin};
            if (threshold_label_exceeds(
                    state.frame,
                    terminal,
                    true
                )) {
                unresolved_mask = (
                    action_count_ == 64
                    ? std::numeric_limits<std::uint64_t>::max()
                    : (
                        (std::uint64_t{1} << action_count_)
                        - std::uint64_t{1}
                    )
                );
            }
        } else {
            int action = 0;
            try {
                for (; action < action_count_; ++action) {
                    ThresholdRootStatus& status =
                        threshold_root_status_[action];
                    if (status == ThresholdRootStatus::rejected) {
                        continue;
                    }
                    if (status == ThresholdRootStatus::exceeds) {
                        continue;
                    }
                    check_abort();
                    const PreparedAction prepared = prepare_action(
                        state,
                        action,
                        true,
                        true,
                        true
                    );
                    if (prepared.threshold_rejected) {
                        ++counters_.branch_incumbent_prunes;
                        status = ThresholdRootStatus::rejected;
                        continue;
                    }
                    if (!threshold_label_exceeds(
                            state.frame,
                            prepared.upper,
                            true
                        )) {
                        ++counters_.action_upper_prunes;
                        status = ThresholdRootStatus::rejected;
                        continue;
                    }
                    if (threshold_action_exceeds(
                            state,
                            prepared,
                            true
                        )) {
                        status = ThresholdRootStatus::exceeds;
                    } else {
                        status = ThresholdRootStatus::rejected;
                    }
                }
            } catch (const PipelineDeadlineSignal&) {
                deadline_expired = true;
            }
            for (action = 0; action < action_count_; ++action) {
                const ThresholdRootStatus status =
                    threshold_root_status_[action];
                if (
                    status == ThresholdRootStatus::exceeds
                    || (
                        deadline_expired
                        && status == ThresholdRootStatus::unknown
                    )
                ) {
                    unresolved_mask |= std::uint64_t{1} << action;
                }
            }
        }
        *output_unresolved_action_mask = unresolved_mask;
        *output_deadline_expired = deadline_expired ? 1 : 0;
        output_stats[0] = static_cast<std::uint64_t>(
            threshold_memo_[0].size() + threshold_memo_[1].size()
        );
        output_stats[1] = static_cast<std::uint64_t>(
            output_stats[0] - threshold_memo_before
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
        output_stats[6] = 0;
        output_stats[7] = (
            counters_.hidden_simulations - before.hidden_simulations
        );
        return 0;
    }

    int recommend_action_column(
        int start_frame,
        int start_row,
        int start_column,
        int observed_action,
        int pending_action,
        const int* pending_remaining_frames,
        int pending_remaining_count,
        int target_root_action,
        int max_depth,
        int timeout_ms,
        int* output_recommended_action,
        int* output_witness_frame,
        int* output_witness_row,
        int* output_witness_column,
        int* output_witness_active,
        int* output_witness_pending,
        std::uint64_t* output_witness_remaining_mask,
        std::uint16_t* output_current_frames,
        float* output_current_margin,
        std::uint16_t* output_recommended_frames,
        float* output_recommended_margin,
        int* output_depth,
        std::uint64_t* output_stats
    ) {
        if (
            remaining_delay_bucket_size_ > 0
            || continuation_policy_mode_ != 0
            || budgeted_action_mask_ != 0
            || continuation_budget_ != 0
            || start_frame < 0 || start_frame >= frame_count_
            || start_row < 0 || start_row >= row_count_
            || start_column < 0 || start_column >= column_count_
            || observed_action < 0 || observed_action >= action_count_
            || pending_action < -1 || pending_action >= action_count_
            || target_root_action < 0
            || target_root_action >= action_count_
            || pending_remaining_count < 0
            || pending_remaining_count
                > BELIEF_PIPELINE_MAX_REMAINING
            || max_depth < 1 || timeout_ms < 0
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
        BeliefPipelineState root{
            start_frame,
            start_row,
            start_column,
            observed_action,
            pending_action,
            0,
            remaining_mask,
        };
        root = canonicalize(root);
        BeliefPipelineState witness{};
        const PipelineLabel root_label = evaluate_action(
            root,
            prepare_action(root, target_root_action, true),
            nullptr,
            &witness
        );
        PipelineLabel current_label = root_label;
        PipelineLabel recommended_label = root_label;
        int recommended_action = -1;
        int depth = 0;

        while (witness.frame >= 0 && depth < max_depth) {
            check_abort();
            witness = canonicalize(witness);
            current_label = solve(witness);
            recommended_label = current_label;
            for (int action = 0; action < action_count_; ++action) {
                const std::uint64_t bit =
                    std::uint64_t{1} << action;
                if ((base_action_mask_ & bit) != 0) {
                    continue;
                }
                const PipelineLabel deviation = evaluate_action(
                    witness,
                    prepare_action(
                        witness,
                        action,
                        false,
                        false,
                        true,
                        true
                    ),
                    nullptr
                );
                if (
                    pipeline_label_less(
                        recommended_label,
                        deviation
                    )
                ) {
                    recommended_action = action;
                    recommended_label = deviation;
                }
            }
            if (recommended_action >= 0) {
                break;
            }
            const auto selected = best_action_memo_.find(witness);
            if (
                selected == best_action_memo_.end()
                || selected->second < 0
            ) {
                witness.frame = -1;
                break;
            }
            BeliefPipelineState next_witness{};
            evaluate_action(
                witness,
                prepare_action(witness, selected->second, false),
                nullptr,
                &next_witness
            );
            witness = next_witness;
            ++depth;
        }

        *output_recommended_action = recommended_action;
        *output_witness_frame = witness.frame;
        *output_witness_row = witness.frame >= 0 ? witness.row : -1;
        *output_witness_column = (
            witness.frame >= 0 ? witness.column : -1
        );
        *output_witness_active = (
            witness.frame >= 0 ? witness.active : -1
        );
        *output_witness_pending = (
            witness.frame >= 0 ? witness.pending : -1
        );
        *output_witness_remaining_mask = (
            witness.frame >= 0 ? witness.remaining_mask : 0
        );
        *output_current_frames = current_label.frames;
        *output_current_margin = current_label.margin;
        *output_recommended_frames = recommended_label.frames;
        *output_recommended_margin = recommended_label.margin;
        *output_depth = depth;
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
        output_stats[6] = 0;
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
        const PipelineLabel* incumbent,
        BeliefPipelineState* output_worst_successor = nullptr
    ) {
        if (output_worst_successor != nullptr) {
            output_worst_successor->frame = -1;
        }
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
                    if (output_worst_successor != nullptr) {
                        output_worst_successor->frame = -1;
                    }
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
                remaining_delay_observation(
                    successor.remaining_mask
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
            const BeliefPipelineState successor_state{
                observation.frame,
                observation.row,
                observation.column,
                observation.active,
                observation.pending,
                observation.continuation_budget,
                group.remaining_mask,
            };
            const PipelineLabel successor = solve(successor_state);
            const PipelineLabel label{
                static_cast<std::uint16_t>(
                    observation.frame - state.frame + successor.frames
                ),
                std::min(group.prefix_margin, successor.margin),
            };
            if (!have_branch || pipeline_label_less(label, robust)) {
                robust = label;
                if (output_worst_successor != nullptr) {
                    *output_worst_successor = successor_state;
                }
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
        bool public_root,
        bool threshold_filter = false,
        bool prefix_margin_above = true,
        bool force_base_action = false
    ) {
        PreparedAction prepared;
        const bool base_action = (
            base_action_mask_ & (std::uint64_t{1} << selected)
        ) != 0;
        const int successor_budget = (
            public_root || base_action || force_base_action
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
                            std::min(
                                transition.bottleneck_margin,
                                future_global_margin_upper_[
                                    transition.successor.frame
                                ]
                            ),
                        }
                    );
                    const PipelineLabel branch_proposal = (
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
                    if (
                        pipeline_label_less(
                            branch_proposal,
                            prepared.proposal
                        )
                    ) {
                        prepared.proposal = branch_proposal;
                    }
                    if (threshold_filter) {
                        if (
                            transition.failed
                            && !threshold_label_exceeds(
                                state.frame,
                                transition.failed_label,
                                prefix_margin_above
                            )
                        ) {
                            prepared.threshold_rejected = true;
                            return prepared;
                        }
                        if (
                            !transition.failed
                            && threshold_target_frame_
                                == frame_count_ - 1
                            && (
                                !prefix_margin_above
                                || branch_upper.margin
                                    <= threshold_target_margin_
                            )
                        ) {
                            prepared.threshold_rejected = true;
                            return prepared;
                        }
                    }
                }
            }
        }
        return prepared;
    }

    bool threshold_label_exceeds(
        int state_frame,
        const PipelineLabel& label,
        bool prefix_margin_above
    ) const {
        const int endpoint_frame = state_frame + label.frames;
        if (endpoint_frame != threshold_target_frame_) {
            return endpoint_frame > threshold_target_frame_;
        }
        return (
            prefix_margin_above
            && label.margin > threshold_target_margin_
        );
    }

    bool threshold_action_exceeds(
        const BeliefPipelineState& state,
        const PreparedAction& prepared,
        bool prefix_margin_above
    ) {
        std::unordered_map<
            BeliefPipelineObservation,
            BeliefPipelineGroup,
            BeliefPipelineObservationHash
        > groups;
        for (const BeliefPipelineTransition& transition :
             prepared.transitions) {
            check_abort();
            if (transition.failed) {
                if (!threshold_label_exceeds(
                        state.frame,
                        transition.failed_label,
                        prefix_margin_above
                    )) {
                    ++counters_.branch_incumbent_prunes;
                    return false;
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
                remaining_delay_observation(
                    successor.remaining_mask
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
                const bool left_prefix = (
                    prefix_margin_above
                    && left->second.prefix_margin
                        > threshold_target_margin_
                );
                const bool right_prefix = (
                    prefix_margin_above
                    && right->second.prefix_margin
                        > threshold_target_margin_
                );
                if (left_prefix != right_prefix) {
                    return !left_prefix;
                }
                return (
                    left->first.frame < right->first.frame
                );
            }
        );
        for (const auto* item : ordered_groups) {
            check_abort();
            const BeliefPipelineObservation& observation = item->first;
            const BeliefPipelineGroup& group = item->second;
            const bool successor_prefix_above = (
                prefix_margin_above
                && group.prefix_margin > threshold_target_margin_
            );
            if (!threshold_state_exceeds(
                    BeliefPipelineState{
                        observation.frame,
                        observation.row,
                        observation.column,
                        observation.active,
                        observation.pending,
                        observation.continuation_budget,
                        group.remaining_mask,
                    },
                    successor_prefix_above
                )) {
                ++counters_.branch_incumbent_prunes;
                return false;
            }
        }
        return true;
    }

    bool threshold_state_exceeds(
        BeliefPipelineState state,
        bool prefix_margin_above
    ) {
        check_abort();
        state = canonicalize(state);
        auto& threshold_memo = threshold_memo_[
            prefix_margin_above ? 1 : 0
        ];
        const auto threshold_found = threshold_memo.find(state);
        if (threshold_found != threshold_memo.end()) {
            ++counters_.memo_hits;
            return threshold_found->second;
        }
        const auto exact_found = memo_.find(state);
        if (exact_found != memo_.end()) {
            ++counters_.memo_hits;
            const bool result = threshold_label_exceeds(
                state.frame,
                exact_found->second,
                prefix_margin_above
            );
            threshold_memo.emplace(state, result);
            return result;
        }

        const float margin = current_margin(state);
        if (
            threshold_target_frame_ == frame_count_ - 1
            && (
                !prefix_margin_above
                || margin <= threshold_target_margin_
                || future_global_margin_upper_[state.frame]
                    <= threshold_target_margin_
            )
        ) {
            threshold_memo.emplace(state, false);
            return false;
        }
        if (state.frame == frame_count_ - 1 || margin <= 0.0F) {
            const bool result = threshold_label_exceeds(
                state.frame,
                PipelineLabel{0, margin},
                prefix_margin_above
            );
            threshold_memo.emplace(state, result);
            return result;
        }

        bool result = false;
        for (int action = 0; action < action_count_; ++action) {
            const std::uint64_t bit = std::uint64_t{1} << action;
            const bool base_action = (base_action_mask_ & bit) != 0;
            const bool budgeted_action = (
                state.continuation_budget > 0
                && (budgeted_action_mask_ & bit) != 0
            );
            if (!base_action && !budgeted_action) {
                continue;
            }
            const PreparedAction prepared = prepare_action(
                state,
                action,
                false,
                true,
                prefix_margin_above
            );
            if (prepared.threshold_rejected) {
                ++counters_.branch_incumbent_prunes;
                continue;
            }
            if (!threshold_label_exceeds(
                    state.frame,
                    prepared.upper,
                    prefix_margin_above
                )) {
                ++counters_.action_upper_prunes;
                continue;
            }
            if (threshold_action_exceeds(
                    state,
                    prepared,
                    prefix_margin_above
                )) {
                result = true;
                break;
            }
        }
        threshold_memo.emplace(state, result);
        return result;
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
            best_action_memo_.emplace(state, -1);
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
        std::array<PreparedAction, BELIEF_PIPELINE_MAX_ACTIONS> prepared;
        std::array<Candidate, BELIEF_PIPELINE_MAX_ACTIONS> candidates;
        int candidate_count = 0;
        for (int action = 0; action < action_count_; ++action) {
            const std::uint64_t bit = std::uint64_t{1} << action;
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
        if (continuation_policy_mode_ > 0) {
            std::sort(
                candidates.begin(),
                candidates.begin() + candidate_count,
                [&](const Candidate& left, const Candidate& right) {
                    const PipelineLabel& left_proposal =
                        prepared[left.action].proposal;
                    const PipelineLabel& right_proposal =
                        prepared[right.action].proposal;
                    if (pipeline_label_equal(
                            left_proposal,
                            right_proposal
                        )) {
                        return left.action < right.action;
                    }
                    return pipeline_label_less(
                        right_proposal,
                        left_proposal
                    );
                }
            );
            PipelineLabel best{
                0,
                -std::numeric_limits<float>::infinity(),
            };
            bool have_best = false;
            int best_action = -1;
            const int selected_count = std::min(
                continuation_policy_mode_,
                candidate_count
            );
            for (int order = 0; order < selected_count; ++order) {
                const int action = candidates[order].action;
                const PipelineLabel label = evaluate_action(
                    state,
                    prepared[action],
                    have_best ? &best : nullptr
                );
                if (!have_best || pipeline_label_less(best, label)) {
                    best = label;
                    best_action = action;
                    have_best = true;
                }
            }
            memo_.emplace(state, best);
            best_action_memo_.emplace(state, best_action);
            return best;
        }
        std::sort(
            candidates.begin(),
            candidates.begin() + candidate_count,
            [&](const Candidate& left, const Candidate& right) {
                const PipelineLabel& left_proposal =
                    prepared[left.action].proposal;
                const PipelineLabel& right_proposal =
                    prepared[right.action].proposal;
                if (pipeline_label_equal(
                        left_proposal,
                        right_proposal
                    )) {
                    if (pipeline_label_equal(left.upper, right.upper)) {
                        return left.action < right.action;
                    }
                    return pipeline_label_less(
                        right.upper,
                        left.upper
                    );
                }
                return pipeline_label_less(
                    right_proposal,
                    left_proposal
                );
            }
        );
        bool have_best = false;
        int best_action = -1;
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
                best_action = candidate.action;
                have_best = true;
            }
        }
        memo_.emplace(state, best);
        best_action_memo_.emplace(state, best_action);
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
    std::uint64_t base_action_mask_;
    std::uint64_t budgeted_action_mask_;
    int continuation_budget_;
    int remaining_delay_bucket_size_;
    int continuation_policy_mode_;
    float required_clearance_;
    bool clamp_to_bounds_;
    std::vector<double> velocity_x_;
    std::vector<double> velocity_y_;
    std::vector<int> delay_frames_;
    std::vector<int> cadence_frames_;
    std::vector<float> future_global_margin_upper_;
    std::unordered_map<
        BeliefPipelineState,
        PipelineLabel,
        BeliefPipelineStateHash
    > memo_;
    std::unordered_map<
        BeliefPipelineState,
        int,
        BeliefPipelineStateHash
    > best_action_memo_;
    std::unordered_map<
        BeliefPipelineState,
        RootNode,
        BeliefPipelineStateHash
    > root_memo_;
    std::array<
        std::unordered_map<
            BeliefPipelineState,
            bool,
            BeliefPipelineStateHash
        >,
        2
    > threshold_memo_;
    int threshold_target_frame_ = 0;
    float threshold_target_margin_ = 0.0F;
    bool threshold_session_active_ = false;
    BeliefPipelineState threshold_session_root_{};
    int threshold_session_target_frame_ = 0;
    std::uint32_t threshold_session_target_margin_bits_ = 0;
    std::array<
        ThresholdRootStatus,
        BELIEF_PIPELINE_MAX_ACTIONS
    > threshold_root_status_{};
    Counters counters_;
    std::atomic<bool> cancel_requested_{false};
    bool deadline_active_ = false;
    Clock::time_point deadline_{};
    std::uint64_t abort_poll_counter_ = 0;
    std::mutex mutex_;
};

}  // namespace

int touhou_native_impl_belief_pipeline_workspace_create_v7(
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
    std::uint64_t base_action_mask,
    std::uint64_t budgeted_action_mask,
    int continuation_budget,
    int remaining_delay_bucket_size,
    int continuation_policy_mode,
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
        || action_count < 1
        || action_count > BELIEF_PIPELINE_MAX_ACTIONS
        || base_action_mask == 0
        || continuation_budget < 0 || continuation_budget > 65535
        || remaining_delay_bucket_size < 0
        || remaining_delay_bucket_size > BELIEF_PIPELINE_MAX_REMAINING
        || continuation_policy_mode < 0
        || continuation_policy_mode > action_count
        || (
            (base_action_mask | budgeted_action_mask)
            & ~(
                action_count == 64
                ? std::numeric_limits<std::uint64_t>::max()
                : (
                    (std::uint64_t{1} << action_count)
                    - std::uint64_t{1}
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
            remaining_delay_bucket_size,
            continuation_policy_mode,
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

int touhou_native_impl_belief_pipeline_workspace_create_v6(
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
    int remaining_delay_bucket_size,
    int continuation_policy_mode,
    const int* delay_frames,
    int delay_count,
    const int* cadence_frames,
    int cadence_count,
    float required_clearance,
    int clamp_to_bounds,
    void** output_workspace
) {
    if (action_count < 1 || action_count > PIPELINE_MAX_ACTIONS) {
        return 2;
    }
    return touhou_native_impl_belief_pipeline_workspace_create_v7(
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
        remaining_delay_bucket_size,
        continuation_policy_mode,
        delay_frames,
        delay_count,
        cadence_frames,
        cadence_count,
        required_clearance,
        clamp_to_bounds,
        output_workspace
    );
}

int touhou_native_impl_belief_pipeline_workspace_create_v5(
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
    int continuation_policy_mode,
    const int* delay_frames,
    int delay_count,
    const int* cadence_frames,
    int cadence_count,
    float required_clearance,
    int clamp_to_bounds,
    void** output_workspace
) {
    return touhou_native_impl_belief_pipeline_workspace_create_v6(
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
        reveal_remaining_delay != 0 ? 1 : 0,
        continuation_policy_mode,
        delay_frames,
        delay_count,
        cadence_frames,
        cadence_count,
        required_clearance,
        clamp_to_bounds,
        output_workspace
    );
}

int touhou_native_impl_belief_pipeline_workspace_create_v4(
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
    return touhou_native_impl_belief_pipeline_workspace_create_v6(
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
        reveal_remaining_delay != 0 ? 1 : 0,
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

int touhou_native_impl_belief_pipeline_workspace_create_v3(
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
    return touhou_native_impl_belief_pipeline_workspace_create_v6(
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

int touhou_native_impl_belief_pipeline_workspace_create_v2(
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
    return touhou_native_impl_belief_pipeline_workspace_create_v6(
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

int touhou_native_impl_belief_pipeline_workspace_create_v1(
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
    if (action_count < 1 || action_count > PIPELINE_MAX_ACTIONS) {
        return 2;
    }
    const std::uint32_t every_action_mask = (
        action_count == 32
        ? std::numeric_limits<std::uint32_t>::max()
        : (
            (std::uint32_t{1} << action_count)
            - std::uint32_t{1}
        )
    );
    return touhou_native_impl_belief_pipeline_workspace_create_v6(
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
        0,
        0,
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

int touhou_native_impl_belief_pipeline_workspace_query_v3(
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
    std::uint64_t* output_best_action_mask,
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

int touhou_native_impl_belief_pipeline_workspace_query_v2(
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
        workspace == nullptr || output_best_action_mask == nullptr
        || static_cast<BeliefPipelineSurvivalWorkspace*>(
            workspace
        )->action_count() > PIPELINE_MAX_ACTIONS
    ) {
        return 1;
    }
    std::uint64_t best_action_mask = 0;
    const int result =
        touhou_native_impl_belief_pipeline_workspace_query_v3(
            workspace,
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
            &best_action_mask,
            output_stats
        );
    if (result == 0) {
        *output_best_action_mask =
            static_cast<std::uint32_t>(best_action_mask);
    }
    return result;
}

int touhou_native_impl_belief_pipeline_workspace_query_v1(
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
    return touhou_native_impl_belief_pipeline_workspace_query_v2(
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

int touhou_native_impl_belief_pipeline_workspace_certify_upper_v3(
    void* workspace,
    int start_frame,
    int start_row,
    int start_column,
    int observed_action,
    int pending_action,
    const int* pending_remaining_frames,
    int pending_remaining_count,
    int continuation_action_budget,
    std::uint16_t lower_frames,
    float lower_margin,
    int timeout_ms,
    std::uint64_t* output_unresolved_action_mask,
    int* output_deadline_expired,
    std::uint64_t* output_stats
) {
    if (
        workspace == nullptr
        || output_unresolved_action_mask == nullptr
        || output_deadline_expired == nullptr
        || output_stats == nullptr
    ) {
        return 1;
    }
    try {
        return static_cast<BeliefPipelineSurvivalWorkspace*>(
            workspace
        )->certify_upper(
            start_frame,
            start_row,
            start_column,
            observed_action,
            pending_action,
            pending_remaining_frames,
            pending_remaining_count,
            continuation_action_budget,
            lower_frames,
            lower_margin,
            timeout_ms,
            output_unresolved_action_mask,
            output_deadline_expired,
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

int touhou_native_impl_belief_pipeline_workspace_certify_upper_v2(
    void* workspace,
    int start_frame,
    int start_row,
    int start_column,
    int observed_action,
    int pending_action,
    const int* pending_remaining_frames,
    int pending_remaining_count,
    int continuation_action_budget,
    std::uint16_t lower_frames,
    float lower_margin,
    int timeout_ms,
    std::uint32_t* output_unresolved_action_mask,
    int* output_deadline_expired,
    std::uint64_t* output_stats
) {
    if (
        workspace == nullptr || output_unresolved_action_mask == nullptr
        || static_cast<BeliefPipelineSurvivalWorkspace*>(
            workspace
        )->action_count() > PIPELINE_MAX_ACTIONS
    ) {
        return 1;
    }
    std::uint64_t unresolved_action_mask = 0;
    const int result =
        touhou_native_impl_belief_pipeline_workspace_certify_upper_v3(
            workspace,
            start_frame,
            start_row,
            start_column,
            observed_action,
            pending_action,
            pending_remaining_frames,
            pending_remaining_count,
            continuation_action_budget,
            lower_frames,
            lower_margin,
            timeout_ms,
            &unresolved_action_mask,
            output_deadline_expired,
            output_stats
        );
    if (result == 0) {
        *output_unresolved_action_mask =
            static_cast<std::uint32_t>(unresolved_action_mask);
    }
    return result;
}

int touhou_native_impl_belief_pipeline_workspace_certify_upper_v1(
    void* workspace,
    int start_frame,
    int start_row,
    int start_column,
    int observed_action,
    int pending_action,
    const int* pending_remaining_frames,
    int pending_remaining_count,
    int continuation_action_budget,
    std::uint16_t lower_frames,
    float lower_margin,
    int timeout_ms,
    std::uint32_t* output_unresolved_action_mask,
    std::uint64_t* output_stats
) {
    int deadline_expired = 0;
    return touhou_native_impl_belief_pipeline_workspace_certify_upper_v2(
        workspace,
        start_frame,
        start_row,
        start_column,
        observed_action,
        pending_action,
        pending_remaining_frames,
        pending_remaining_count,
        continuation_action_budget,
        lower_frames,
        lower_margin,
        timeout_ms,
        output_unresolved_action_mask,
        &deadline_expired,
        output_stats
    );
}

int touhou_native_impl_belief_pipeline_workspace_recommend_action_column_v1(
    void* workspace,
    int start_frame,
    int start_row,
    int start_column,
    int observed_action,
    int pending_action,
    const int* pending_remaining_frames,
    int pending_remaining_count,
    int target_root_action,
    int max_depth,
    int timeout_ms,
    int* output_recommended_action,
    int* output_witness_frame,
    int* output_witness_row,
    int* output_witness_column,
    int* output_witness_active,
    int* output_witness_pending,
    std::uint64_t* output_witness_remaining_mask,
    std::uint16_t* output_current_frames,
    float* output_current_margin,
    std::uint16_t* output_recommended_frames,
    float* output_recommended_margin,
    int* output_depth,
    std::uint64_t* output_stats
) {
    if (
        workspace == nullptr || output_recommended_action == nullptr
        || output_witness_frame == nullptr
        || output_witness_row == nullptr
        || output_witness_column == nullptr
        || output_witness_active == nullptr
        || output_witness_pending == nullptr
        || output_witness_remaining_mask == nullptr
        || output_current_frames == nullptr
        || output_current_margin == nullptr
        || output_recommended_frames == nullptr
        || output_recommended_margin == nullptr
        || output_depth == nullptr || output_stats == nullptr
    ) {
        return 1;
    }
    try {
        return static_cast<BeliefPipelineSurvivalWorkspace*>(
            workspace
        )->recommend_action_column(
            start_frame,
            start_row,
            start_column,
            observed_action,
            pending_action,
            pending_remaining_frames,
            pending_remaining_count,
            target_root_action,
            max_depth,
            timeout_ms,
            output_recommended_action,
            output_witness_frame,
            output_witness_row,
            output_witness_column,
            output_witness_active,
            output_witness_pending,
            output_witness_remaining_mask,
            output_current_frames,
            output_current_margin,
            output_recommended_frames,
            output_recommended_margin,
            output_depth,
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

int touhou_native_impl_belief_pipeline_workspace_cancel_v1(
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

void touhou_native_impl_belief_pipeline_workspace_destroy_v1(
    void* workspace
) {
    delete static_cast<BeliefPipelineSurvivalWorkspace*>(workspace);
}
