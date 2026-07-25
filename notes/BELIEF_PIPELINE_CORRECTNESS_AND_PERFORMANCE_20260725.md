# Belief-Pipeline Correctness And Performance Checkpoint

Status: verified offline research checkpoint, 2026-07-25.  No action authority
is granted.  This note applies the formal problem in
`AUGMENTED_PIPELINE_ROBUST_CONTROL_FORMALIZATION_20260725.md` to the existing
one-transition prewarm implementation and the new belief-state prototype.

## Outcome

The old “exact-root” implementation is exact only for a legacy hybrid model:

- every planner selection is treated as a newly issued command, even when the
  live actuator would hold the already-selected mask without writing;
- cadence uncertainty is applied on the public transition once;
- continuation cadence is fixed;
- exact remaining command delay is revealed to future maximization.

That model does not solve the stated physical information-set problem.  Two
independent scalar implementations, three minimized deterministic
counterexamples, and four 128-case cohorts falsify the stronger claim.

A new independent scalar oracle and C++ workspace now solve the recursively
variable-cadence, non-clairvoyant finite model with physical hold/no-write
semantics on bounded workloads.  C++ removes Python as the micro-kernel
bottleneck, but complete TH08 state growth is still prohibitive.  A
conservative policy-class reduction—every root action followed by
focused-only continuation—reduces a representative 32-frame `(4,5,6)` solve
from about 1.51 seconds to 29.52 milliseconds.  A wide `(2..9)` cadence
product remains too expensive and exposes the next semantic requirement: a
verified scheduler/cadence contract or a bounded cadence automaton.

## Correctness Audit

Retained artifact:
`artifacts/viability_audit/pipeline_formal_correctness_20260725.json`.

### Counterexample 1: hold is not a new issue

The complete lattice is three x-cells, two identical y-rows, and four frames.
All clearance is `+1` except frame 3 / x-cell 1, which is `-1`.

```text
actions: left(-1), stay(0)
start: frame 0, x-cell 1, observed stay, left pending with rho=2
command delay: {3}
decision cadence: {1}
```

The live controller selecting `left` emits no transition because `left` is
already its held desired input.  The old pending command becomes active in
time and the player survives all three future frames.  The legacy recurrence
invented a new write at every decision, replaced the pending command, and
reported only two surviving frames.

This is a conservative winning/losing error in this case.  The legacy model
also has fixed-cadence and clairvoyance errors, so it has no general bound
direction.

### Counterexample 2: one cadence branch is optimistic

The shrunk lattice has five x-cells, two identical y-rows, and ten future
frames.  Its only unsafe `(frame, x)` cells are:

```text
(5,0), (7,1), (9,2), (10,4)
actions: left(-1), stay(0), right(+1)
start: frame 0, x-cell 2, observed stay
command delay: {2,3}
decision cadence: {1,2}
legacy continuation: fixed 2
```

The no-write-correct one-transition recurrence reports complete ten-frame
survival.  Recursive cadence permits a phase-shifted sequence of shorter and
longer decision gaps that misses the observation/action opportunity assumed
by fixed continuation; the complete belief recurrence guarantees nine frames
and is losing.

Thus replacing recursive cadence by one public branch, a fixed maximum
interval, or a trace predictor is not generally exact.

### Counterexample 3: exact hidden delay grants clairvoyance

The complete lattice again has three x-cells and two identical y-rows.  All
clearance is `+1` except frame 4 / x-cell 1, which is `-1`.

```text
actions: stay(0), right(+1)
start: frame 0, x-cell 0, observed stay
command delay: {2, 3}
decision cadence: {1}
```

A recurrence that reveals the exact successor remaining delay reports both
`stay` and `right` as four-frame best actions.  The legal belief recurrence
must choose the next command before nature's indistinguishable remaining
delay is known; `right` then guarantees only three frames.  Only `stay`
remains best.

The state value happens to remain winning because `stay` is available, but
the optimistic tie would incorrectly authorize `right`.

### Deterministic cohort

Four 128-case synthetic cohorts use deterministic random clearance fields:

| Cohort | Comparison | Action-label mismatch | Best-action mismatch | Winning mismatch |
| --- | --- | ---: | ---: | ---: |
| fixed cadence / singleton delay | always-issue vs no-write | 30/128 | 15/128 | 30/128 |
| small recursive cadence | one-transition vs recursive | 0/128 | 0/128 | 0/128 |
| wider/longer recursive cadence | one-transition vs recursive | 3/128 | 2/128 | 1/128 |
| fixed cadence / hidden delay | clairvoyant vs belief | 15/128 | 11/128 | 0/128 |

In the first cohort, all 30 legacy state-value disagreements were
conservative.  This does not make the legacy workspace a lower bound because
its other relaxations can be optimistic.  The small cadence cohort is useful
negative evidence only; the wider counterexample and cohort disprove a
general fixed-maximum equivalence.  The hidden-delay cohort demonstrates that
action errors can exist even when the maximum state label is unchanged.

These rates characterize the retained synthetic distribution only; they are
not estimates of Stage-5 frequency.

## Correct Recurrence Implemented

The scalar oracle is
`scripts/touhou_control/variable_cadence_oracle.py`.  Its memo state is:

```text
(frame, row, column, observed_action, held_desired_action,
 known_pending_action, remaining_delay_support, public_root)
```

The compact API reconstructs `held_desired_action` as the pending action when
pending exists, otherwise the observed action.  This relies on the explicit
estimator-consistency invariant in the formal note.  Selecting the held
desired action is no-write: it preserves and decrements the old pending delay
without sampling a new one.  Only a different selection simulates new command
delays.  All current hidden remaining delays and cadence values are branched;
surviving branches are grouped by the next observation before the next
controller maximization.  A successor support is the union of remaining
delays inside that observation class.

The native implementation is
`native/belief_pipeline_survival_workspace.hpp`.  It stores a remaining-delay
bitmask directly in the memo key and has:

- recursive cadence branching;
- conditional issue/no-write transitions;
- observation-compatible support merging;
- immutable clearance/action/delay/cadence ownership;
- exact public-root labels for every action;
- cooperative deadlines and cancellation;
- admissible action upper bounds;
- incumbent pruning only after a partial robust value or observation-class
  upper bound cannot beat the incumbent;
- an optional continuation-action mask.

The last feature defines a smaller admissible controller policy class; it
does not delete root actions and does not claim unrestricted optimality.

### Differential evidence

- 24 focused randomized unit cases compare native labels and all root action
  labels with the independent scalar oracle, including pending supports and
  restricted continuation classes.
- The retained benchmark compares another 128 randomized cases with zero
  failures.
- The fixed-cadence/no-carried-delay special case matches the prior scalar
  recurrence.
- Minimized regressions retain hold/no-write, phase-shifted cadence, and
  hidden-delay non-anticipativity failures.
- Randomized tests verify that the clairvoyant relaxation never lowers an
  action value relative to the belief policy.

This establishes implementation parity for the declared finite model.  It
does not establish TH08 hazard-model fidelity or physical delivery.

## Performance Audit

Retained artifact:
`artifacts/benchmarks/belief_pipeline_workspace_20260725.json`.

### Python versus C++

On 128 tiny differential cases:

| Backend | Median | p95 |
| --- | ---: | ---: |
| scalar belief Python | 5.94 ms | 12.67 ms |
| native belief cold | 0.105 ms | 0.198 ms |
| native exact-root warm | 0.028 ms | 0.043 ms |

C++ is about 56 times faster at the median.  Moving this recurrence to native
code was warranted.  Warm lookup remains negligible.

### TH08-shaped scaling

The structured workload uses a 27x24 lattice, six command delays, real TH08
movement actions, and the stated horizon.

| Horizon | Root actions | Continuation actions | Cadence | Wall time |
| ---: | ---: | ---: | --- | ---: |
| 32 | 9 focused | 9 focused | `(4,5,6)` | 10.06 ms |
| 32 | all 17 | 9 focused | `(4,5,6)` | 29.52 ms |
| 32 | all 17 | all 17 | `(4,5,6)` | 1507.74 ms |
| 80 | all 17 | 9 focused | `(4,5,6)` | >3000 ms |
| 8 | all 17 | 9 focused | `(2..9)` | 54.94 ms |
| 16 | all 17 | 9 focused | `(2..9)` | 552.69 ms |
| 32 | all 17 | 9 focused | `(2..9)` | >3000 ms |

For the 32-frame, all-root/focused-continuation case, the native solver
memoized 1,625 belief states and simulated 270,189 exact hidden branches.
Allowing fast actions recursively expanded this to 45,116 states and
14,112,336 simulations.

Therefore:

- Python is no longer the relevant blocker.
- Repeated fast-action reachability and a Cartesian cadence envelope dominate
  state growth.
- Narrowing the policy class is effective and conservative.
- Merely widening cadence support from `(4,5,6)` to `(2..9)` destroys the
  service budget even at short horizons.

## Policy-Class Lower Bound

Let `A` be all 17 TH08 actions and `F` be the 9 stay/focused actions.  The new
workspace can solve:

```text
root action in A
every later action in F
```

This policy class is a subset of the unrestricted controller, so its value is
an attainable lower bound:

```text
V_root-A_then-F <= V_unrestricted-A
```

It preserves an immediate fast escape because all 17 root labels are still
computed.  It avoids assuming that fast motion can be chosen at every hidden
future branch.  At the next real observation a fresh receding query again
allows all 17 root actions.

This is an engineering approximation with a known conservative direction,
not a proof that focused continuation is globally optimal.

## Physical Prewarm Result

Three complete hard-no-Bomb Stage-5 runs were retained:

| Run | Shadow | Hits | Iteration median | Local-plan median | Action lag median |
| --- | --- | ---: | ---: | ---: | ---: |
| `171023` | none | 14 | 45.63 ms | 20.35 ms | 2 frames |
| `171925` | full frontier | 32 | 71.82 ms | 30.83 ms | 4 frames |
| `175339` | top-2 + low priority | 27 | 65.98 ms | 29.22 ms | 3 frames |

The RNG-distinct hit totals are adverse evidence, not causal survival
estimates.  The timing regression is direct: background work competed with
native reads and local planning.

Full-frontier exact hits were 285/6,347 (`4.49%`).  Bounded top-2 scheduling
raised them to 881/7,067 (`12.47%`) but did not restore the clean controller
budget.  In forensic same-policy pairs, every covered root that completed was
consumed; lookup/version logic was not the failure.

The old prewarm therefore remains disabled by default and shadow-only.

## Current Decision

1. Retire “exact” as an unqualified description of the old
   always-issue/one-transition/fixed-continuation workspace.  Its error
   direction is unknown and it is not a usable lower or upper bound.
2. Accept the scalar belief oracle and native belief workspace as correct
   offline infrastructure for their declared finite model.
3. Accept all-root/focused-continuation as a conservative policy-class lower
   bound worth further testing.
4. Do not attach the new workspace to live control or launch another physical
   trial yet.
5. Do not spend more effort optimizing top-K prewarm against the invalid
   hybrid value.

## Next Algorithmic Gate

The next work is cadence semantics, then bounded optimality:

1. Determine whether a dedicated/paced issue loop can enforce a narrow
   cadence/workload automaton.  If yes, model and adversarially validate that
   scheduler invariant rather than an arbitrary independent `(2..9)` nature
   choice.
2. If cadence remains variable, represent it with a verified finite automaton
   or workload state; do not assume every cadence can follow every other one
   unless runtime evidence requires that product.
3. Use the conservative root-all/focused-continuation belief value as a lower
   bound.
4. Build an explicit optimistic upper bound by relaxing hidden-delay
   information (clairvoyance) or other proved relaxations.  Do not use the old
   hybrid as an upper bound: its invented writes can also be conservative.
5. Refine full-action belief states only while upper bounds can beat the best
   attainable lower bound.  Deadline expiry publishes the lower-bound policy
   or falls back; it never publishes an unfinished optimistic label.
6. Re-run Stage-5 capsules offline before any physical shadow.  Require
   action-label parity where exact completion is available, explicit bound
   gaps where it is not, and a whole-controller CPU budget.
