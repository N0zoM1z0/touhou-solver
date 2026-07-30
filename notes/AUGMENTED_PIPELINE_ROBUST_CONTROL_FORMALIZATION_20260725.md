# Augmented-Pipeline Robust Control: Formal Problem And Proof Boundary

Status: active research specification, 2026-07-25.  This note defines the
problem that the losing-state value and exact-root prewarm work is intended to
solve.  It deliberately separates the physical game, the finite model, the
information available to the controller, and the delivery system.

## 1. Decision Problem

At each controller decision epoch, choose an input command that maximizes
finite-horizon modeled survival under:

- collision-clearance uncertainty already encoded in a frame-major clearance
  volume;
- uncertain command-observation delay;
- variable time until the next controller decision;
- a last-write-wins input pipeline in which an older pending command may
  become visible before the newly issued command;
- only the state information actually observable at the next decision; and
- a hard issue-time local collision certificate.

The exact value is lexicographic:

```text
V = (guaranteed surviving physical frames, worst bottleneck clearance)
```

Larger is better.  Survival membership is a hard constraint when the Boolean
viability set is nonempty.  The value in this note is used only when that set
is losing/empty, or as shadow evidence; it does not authorize an action that
fails the fresh local hard certificate.

## 2. Physical And Modeled State

Let physical frame be `t`, projected lattice cell be `q = (row, column)`, and
the finite clearance horizon end at `H`.

The hidden input-pipeline state is:

```text
h = (t, q, a, g, p, rho)
```

where:

- `a` is the action currently observed by the game;
- `g` is the complete desired input mask last held by the controller;
- `p` is the newest desired action that has not yet become visible, or none;
- `rho > 0` is the exact remaining observation delay for `p`.

In the current one-pending abstraction, `p` is either none or equals `g`.
Keeping `g` explicit is nevertheless essential: the live actuator compares a
new decision with its last held mask and sends key transitions only when they
differ.  A planner decision is therefore not automatically a command issue.

The controller knows `g` but generally does **not** observe `rho`.  Its
decision state is an information set:

```text
B = {h_1, ..., h_n}
```

whose members are indistinguishable under the native observation available at
that decision.  In the current one-pending model this can be represented
compactly as:

```text
b = (t, q, a, g, p, R)
R = sorted set of possible remaining delays
```

The controller observes `t`, `q`, and native `a`, remembers `g`, and carries
`(p,R)` from the delay estimator.  The current workspace API omits a separate
`g` argument and reconstructs it as `p` when pending, otherwise `a`.  This is
equivalent only under the estimator-consistency invariant:

```text
p != none => g == p
p == none => g == a
```

An overdue, dropped, multi-edge, or otherwise inconsistent input transition
violates that invariant and requires a larger root contract or a fail-closed
fallback.  If two hidden branches have the same observable tuple but
different `rho`, a valid policy must choose the same next command for both.

This non-anticipativity condition is essential.  A recurrence that calls
`max_action` separately for each hidden `rho` grants the controller
clairvoyance and can overestimate guaranteed survival.

### Physical-clock equivalence obligation

The physical step `t` above is a player-motion/hazard transition, not
unconditionally the native enemy-manager counter. Stage-4A physical evidence
shows that the manager counter can freeze during post-spell dialogue while a
held movement input continues to change player position. Histories with the
same manager frame, cell, and desired action before a freeze are therefore not
equivalent to histories after an unknown number of hidden wall-clock movement
updates.

The attempted live approximation did not add an unbounded hidden-time support
to the recurrence. It released movement and reset the gameplay epoch after 50
ms without manager-counter progress. Physical run `stage4a_103856` rejected
that observation predicate: it merged ordinary slow control iterations with
semantic freezes, fired 2,780 times, and starved the Boolean policy. The guard
has been removed. There is currently no live approximation with authority
across this boundary, so no exact or bounded claim in this note extends across
it. A successor must use semantic phase/dialogue or actual wall-pulse episode
evidence and first pass a shadow false-positive audit. See
`notes/FROZEN_MANAGER_INPUT_CLOCK_BOUNDARY_20260726.md`, CE-0120, and CE-0121.

## 3. Action, Nature, And Last-Write-Wins Transition

At belief state `b`, the controller selects desired action `u`.  This produces
an actual input write iff:

```text
w = (u != g)
```

Nature selects:

```text
k in K_t     frames until the next decision
h in B       one currently possible hidden state
d in D       new command delay, only when w is true
```

When `w` is false, no transition is sent and no new delay is sampled.  The
existing pending command continues its original countdown:

```text
p, if pending p exists and j > rho
a, otherwise
```

When `w` is true, physical substep `j = 1..k` follows:

```text
u, if j > d
p, if j <= d and an older pending p exists and j > rho
a, otherwise
```

Thus the observable motion sequence is:

```text
currently observed a -> possibly older pending p -> newly selected u
```

Only an actually written `u` supersedes `p` as the pending desired command.
If written `u` has not become visible by the next decision, the successor
carries remaining delay `d-k`; otherwise `u` becomes observed and no longer
remains pending.  For hold/no-write, `p` either becomes active when
`rho <= k`, or remains pending with `rho-k`.

### CE-0193 amendment: a write is an ordered transition transaction

The transition above remains exact for a single-key issue or for a runtime
that exposes only the old/final complete masks. It is **rejected as physical
authority for a multi-key TH08 issue**.

The actuator constructs a deterministic ordered edge list: releases in
ascending supported-bit order, followed by presses in ascending order, and
submits the list in one `SendInput` batch. Retained original-game Stage-5
evidence observes an intermediate prefix of that list:

```text
0x65 --release Focus 0x04--> 0x61
     --release Down  0x20--> 0x41
```

The next coherent native `input_current` is `0x61` while controller-held and
pending final desired mask is `0x41`. The implemented independent scalar
oracle now uses the exact hidden transaction state:

```text
z = (a, g, Q, r)

a = currently published native active mask
g = held final desired mask
Q = remaining masks after each ordered single-key edge
r = positive remaining final-completion publication deadline
```

`Q[-1] == g`; adjacent entries from `a` through `Q` differ by exactly one
bit. `Q` empty means settled `a == g` and no deadline. A nonempty queue may
still have `a == g`: an overwrite can temporarily return to the selected
mask before traversing an older suffix and the appended new transaction.

For a real write `u != g`, the actuator appends the deterministic ordered
path from the old held mask `g` to `u` after the remaining older queue,
updates held final desired to `u`, and nature samples a new positive
final-completion delay. For no-write `u == g`, it appends nothing, samples no
delay, and preserves the entire older queue/deadline.

At one abstract input-publication step:

- if `r == 1`, nature must publish final `g` and settle;
- if `r > 1`, nature may stutter or consume any monotone non-final prefix of
  `Q`, then decrements `r`; and
- the final mask cannot be published before the declared deadline.

This prefix/stutter set is a conservative abstraction of the observed
ordered transaction, not a measured Win32 queue scheduler. The exact finite
uncertainty set for edge delivery versus asynchronous capture/issue phase is
still not revalidated. Until it is, unobserved intermediate timing is
unknown-direction and outside hard authority. The corrected recurrence now:

- allow every physically attainable ordered prefix mask at the appropriate
  native input/player-update phase;
- distinguish final desired `g` from currently observed intermediate `a`;
- retain older pending state and causal overwrite/order semantics;
- merge only histories indistinguishable under the complete next-decision
  observation; and
- preserve `u == g` as a true no-write that emits no edge, samples no new
  delay, and does not erase older pending state.

The current live delay estimator does **not** instantiate `r`. Its
`control_delay_candidates` are enemy-manager-frame
snapshot-to-observed-final-input values. `pending_estimate` subtracts
snapshot age, while the issue-time manager frame is read before dispatch.
The oracle's `r` instead counts abstract post-issue native publication steps.
No adapter between these coordinates currently has authority.

The retained Stage-5 phase audit makes this separation reproducible. Among
6,423 real writes it observes 677 intermediate latest-transaction masks and
2,760 sequential `previous -> current` edge pairs that also have
`raw == current` and a later coherent current-mask confirmation. The
canonical CE-0193 pair is trace lines `297 -> 298`, `0x65 -> 0x61`, before
final `0x41` is first observed. These are physical, post-hoc observations of
ordered publication behavior. They are not atomic native edge captures:
`raw/current/previous` are separate reads, decision capture is asynchronous,
and no priority-17 callback serial exists. The same report has zero atomic
publication-edge witnesses by construction and leaves `r` unidentified.

CE-0193 is not permission to treat each key edge as an independent controller
choice. The controller chooses one final complete mask before nature exposes
transaction timing; all intermediate masks belong to that one issue's hidden
physical transition. Hidden queue/deadline states are merged before the next
controller maximization exactly when observed active mask and held final mask
agree. The pre-amendment one-token recurrence remains an offline restricted
baseline after CE-0193.

#### Asynchronous dispatch refinement

`ASYNC_ORDERED_INPUT_PUBLICATION_CONTRACT_20260730.md` refines the issue
boundary using the retained priority-17 serial evidence. For one real write,
the older suffix and newly appended release/press path form one combined
suffix. Nature selects a declared in-dispatch callback count. At each such
callback:

1. the TH08 physical step consumes the active mask that existed before the
   callback;
2. priority 9/11 updates player mode and body gates;
3. priority 17 publishes a stutter or any monotone cut of the remaining
   suffix; and
4. the published mask becomes active only for the next physical step.

If the suffix settles during dispatch, no post-dispatch delay is sampled. If
it remains pending, nature samples a new positive deadline measured from the
post-dispatch boundary. A newer real write may retain an older unobserved
suffix while superseding the visibility requirement of its transient held
target. No-write has no dispatch microphase and preserves the exact state.

The independent scalar and bounded native implementations are exact for this
declared finite recurrence. The callback-count support, post-dispatch
deadline support, and their joint relation with recursive cadence remain
physical hypotheses. The observed `1..5` first-final values are positive
samples, not a universal support or an adapter from
`control_delay_candidates`.

This conditional issue rule is not cosmetic.  A retained three-frame
counterexample starts from `stay` with `left` pending at remaining delay two.
Holding `left` lets it become active in time and wins.  The legacy recurrence
invented a new delay at every decision, replaced the pending command, and
reported losing.

Each substep projects continuous displacement to the lattice.  The clearance
margin used by the current model is:

```text
m(t+j, q_j) =
    clearance[t+j, q_j] - projection_error - required_clearance
```

A nonpositive margin terminates the modeled branch before that frame is
credited as survived.  Leaving the lattice either fails or clamps according
to the immutable viability configuration.

## 4. Observation Partition

After simulating every `(h, d, k)` branch for selected action `u`, surviving
successors must be partitioned by what the controller will observe:

```text
o' = (t', q', observed_action', held_desired', known_pending_action')
```

All exact remaining delays in one observation class are unioned into the
successor support `R'`.  Only then may the controller select the next action.

This produces the robust finite-horizon recurrence:

```text
V(B) = max_u min(
    immediate failed-branch labels,
    labels of every observable successor class
)

class_label(C) =
    (k + V(C).survival_frames,
     min(worst_prefix_margin(C), V(C).bottleneck_margin))
```

The `max` is outside hidden delay choices.  At a successor it is inside the
observation partition, because the controller may react to a genuinely
different observed frame, cell, or active action.

Terminal conditions are `t == H` or current margin `<= 0`.

## 5. What “Exact” Can Mean

Four distinct claims must not be conflated:

1. **Kernel parity:** optimized C++ and an independent scalar implementation
   return the same labels for the same recurrence.
2. **Finite-model exactness:** the recurrence solves all actions, delay
   branches, cadence branches, and information sets in the declared finite
   model without unsound pruning.
3. **Model fidelity:** native movement, collision, hazard transforms, births,
   delays, action observation, and sensing match the game closely enough.
4. **Delivered control correctness:** an exact label for the current immutable
   policy and exact observable root is ready before issue time and the final
   issued action passes a fresh local hard certificate.

Passing claim 1 does not establish claims 2--4.

## 6. Current Implementation Boundary

### Observed

- `scalar_query_local_survival` and the native
  `PipelineSurvivalWorkspace` branch over variable cadence only for the public
  root transition.  Every deeper transition uses
  `config.frames_per_layer` (TH08 currently uses 8).
- Both legacy implementations treat every selected action as a newly issued
  command.  Live code calls `send_transitions`/`delay_estimator.issued` only
  when the selected full mask differs from the last held mask.  The legacy
  recurrence is therefore not a physical actuator model and is neither a
  general optimistic nor conservative bound.
- The legacy implementations also carry one exact `pending_remaining`
  integer in their memo state.  A tuple of possible remaining delays is
  minimized at a public query root, but successor branches are solved
  separately before the next controller maximization.
- Existing 512-seed differentials therefore prove Python/C++ parity for this
  bounded hybrid recurrence, not the physical variable-cadence
  information-set game.
- The new scalar and C++ belief workspaces implement conditional no-write,
  recursively branch cadence, and merge indistinguishable remaining-delay
  supports before continuation maximization.  Another 128 retained randomized
  cases have zero scalar/native failures.
- `ordered_input_transaction_oracle.py` independently implements the CE-0193
  ordered state and asynchronous issue microphase above. Seventeen focused
  tests cover deterministic release/press order, the physical
  `0x65 -> 0x61 -> 0x41` witness, callbacks in dispatch, stutter/multi-edge
  cuts, final-in-dispatch, final-deadline forcing, no-write, overwrite,
  observation merging, uniform controller choice, unsupported bits, and
  Bomb.
- `th08_enemy_mode.py` retains its atomic APIs as an explicitly restricted
  baseline and adds ordered and asynchronous SEM-MODE decision primitives.
  The asynchronous primitive accounts for dispatch callbacks inside total
  cadence: priority 9 consumes current active input, priority 11 projects
  body gates, and priority 17 publishes a nature-selected transaction prefix
  for the next step. Nine focused tests cover composition and non-clairvoyant
  observation merging.
- Connected IDA revalidation records this native order at `0x0044AEE8` and
  the priority-17 range `0x00452339..0x00452483`: priority-9 player movement
  consumes the previously published `g_input_current`; priority-17 saves
  previous once, writes current from a first raw sample at `0x00452347`, and
  may overwrite current from a second raw sample at `0x004523C7` before all
  paths converge at the common epilogue `0x00452480`. The callback-exit
  current, not either store in isolation, is the next priority-9 input.
- `th08_ordered_input_phase_report.py` audits the complete retained Stage-5
  source. It source-hashes the raw trace, validates all 6,423 ordered
  dispatches, brackets first observed final masks, censors discontinuities
  and large manager gaps, and explicitly reports that the estimator-to-native
  publication adapter is unavailable. It finds 677 intermediate-mask
  observations and retains the CE-0193 `0x65 -> 0x61` edge. The 120 final
  masks first observed outside their issued snapshot support are capture
  observations, not measured deadline violations.
- `priority17_publication_probe.py` is a default-off, trace-only physical
  observer for the still-open adapter. It records one committed serial/event
  at the common callback exit and brackets only real ordered dispatches with
  pre/post serial reads. No-write performs no serial sampling. Ring
  overflow, unstable reads, and read errors mark intervals unknown without
  changing the action. Installation/cleanup suspend all target threads and
  verify no instruction pointer can consume the trampoline or remote stub
  before restoring/freeing executable memory. A batch cursor advances only
  after the decision row containing that batch is flushed; pre-issue early
  exits cannot consume unpublished ring evidence.
- `th08_priority17_publication_report.py` accepts a negative publication
  claim only when every serial in the interval is retained. It separately
  counts native callback exits during a dispatch, intermediate ordered masks,
  and serial advances while `enemy_manager_frame` is unchanged. Physical
  Stage-5 run `083416` retains 30,904 exits and 6,565 complete issue
  brackets: 1,223 brackets contain a callback, 478 callbacks expose a
  non-final ordered mask, and 122 consecutive callbacks advance without a
  manager-frame advance. Four overflow batches remain explicit unknown
  intervals.
- Across complete serial prefixes, first observed final-mask publication
  steps are `{1:4893, 2:1648, 3:17, 4:2, 5:1}`. One transaction is replaced
  after one complete callback interval without its transient target being
  observed. The physical trace therefore supplies positive support samples
  and replacement censoring, but not a universal finite upper bound for
  `r`.
- `touhou_async_ordered_input_issue_v1` is an independent bounded C++
  exact-state enumerator. It adds the 47th checked production ABI symbol but
  has no live consumer. Linux/Windows retained reports match the scalar
  oracle on 115 state/action cases and all 2,405 exact branch histories,
  including the two physical witnesses. The report SHA-256 values are
  `f9fbe98bac5fe9481e8baf4bc09c51b328b12fb744d724132dd0d7adb7e3e4b0`
  and
  `91df49e10f919e4c1681cb617563c311c55902b0500ee2ba5b379a23b391885a`.
- `th08_future_body_schedule.py` now supplies an offline-only immutable
  body/flag/geometry schedule set. Its digest covers root physical update,
  exact clock/provenance identity, every finite nature branch, body identity,
  mode-independent flags, and binary32 geometry. The asynchronous
  composition carries that version through hidden histories and includes
  exact projected body flags/geometry in the next observation key. A
  deterministic Linux/Windows-byte-identical report covers three supplied
  schedule cases, eight branches, and 27 scalar/body-set comparisons with
  zero mismatch. This is representation and composition authority only:
  no predictive producer exists and physical future coverage remains
  `UNKNOWN` from root+1.
- Lookup-only version/root checks are exact.  In the first physical shadow,
  every root that was both covered and completed was consumed; miss delivery,
  not lookup corruption, caused the low hit rate.
- A bounded physical top-2 scheduler increased exact-root hits from `4.49%`
  to `12.47%`, but Stage-5 shadow timing and hits remained worse than the clean
  control.  This scheduler is probabilistic work selection, not a proof.

### Inferred

- Conditional issue/no-write, recursive cadence, and observation-compatible
  belief merging are all necessary.  Separate minimized counterexamples flip
  winning classification for the first two and add a false best action for
  hidden-delay clairvoyance.
- Ordered prefix masks are physically necessary model states, but the
  current prefix/stutter support is conservative and its publication deadline
  is exact only relative to the oracle's abstract publication clock.
- Callback publication during the asynchronous controller issue is now
  physically observed and represented by an exact finite causal transition.
  What remains open is the physical completeness of its callback/deadline
  supports and their joint scheduler/cadence automaton. Enemy-manager frame
  cannot supply that authority.
- Replacing recursive cadence by one robust public transition followed by a
  fixed interval has unknown direction.  It matched one small cohort but was
  optimistic on a retained wider ten-frame counterexample; “use only maximum
  cadence” is not a valid general reduction.
- Full-frontier background work contends with native reads/local planning.
  Moving Python orchestration to C++ alone cannot remove that algorithmic
  work.

### Hypothesized

- A verified cadence automaton containing workload/scheduler state can be much
  smaller than the current independent Cartesian cadence support without
  losing physical schedules.
- A batch/incremental C++ solver can share transition geometry and successor
  belief values across roots and dependency-compatible policy updates more
  effectively than independent root prewarm.
- A conservative restricted policy supplies an attainable lower bound, while
  a clairvoyant information relaxation supplies an optimistic upper bound;
  refining only when the upper bound can beat the incumbent lower bound may
  avoid unrestricted state explosion.

## 7. Correctness Obligations

Before any losing-state value gains action authority:

1. Define the observation function from native input/action telemetry.
2. Carry or soundly reconstruct the held desired mask `g`.  Selecting `g`
   must be a no-write transition that preserves the old pending countdown;
   only selecting `u != g` samples a new delay.
3. Verify the one-pending last-write-wins abstraction.  If two unobserved
   issued commands or sequential per-key edges can both still affect future
   motion, expand the state.
4. Implement the exhaustive belief-state scalar oracle on tiny workloads.
5. Show the fixed-cadence/no-carried-command special case matches the legacy
   numeric recurrence when `K = {frames_per_layer}`; do not demand parity in
   cases where the legacy always-issue semantics are wrong.
6. Produce and retain adversarial cases for:
   variable cadence, indistinguishable remaining-delay branches, boundary
   clamping, projection error, hold/no-write, stop/resume/reversal motion, and
   horizon tails.
7. Differential-test every C++ optimization against the independent oracle.
8. Prove every prune:
   - terminal infeasibility is exact;
   - pipeline canonicalization preserves every possible motion trace;
   - dominance compares states with compatible observations and future branch
     sets;
   - action upper bounds are truly optimistic;
   - incumbent pruning cannot discard a lexicographically better action.
9. Keep model-fidelity counterexamples separate from recurrence bugs.
10. Keep physical action authority gated by current policy version, exact
   observable root, deadline, and fresh issue-time local certificate.
11. Before the ordered oracle consumes a physical delay support, derive a
    conservative callback-step and joint scheduler/cadence contract across
    the mandatory Stage-3/4A/5/Final-B workloads. A manager-frame residual or
    first later capture is not that support. Retained Stage-5 counts establish
    observed values `1..5`, not an upper bound: explicit replacement
    censoring and trace gaps must remain branches or unresolved evidence.

## 8. Performance Problem

The target is not merely a fast lookup.  A usable system must produce the
correct current-root value before it is needed without materially slowing the
controller.

Measure separately:

```text
clearance publication
belief-state seed / continuation induction
root specialization
Python scheduling
FFI
lookup
telemetry serialization
native read
local planning
action lag
stale/cancelled work
```

Current evidence:

- warm exact lookup is about `0.03--0.1 ms` and is not the bottleneck;
- corrected native belief cold/warm medians on tiny cases are about
  `0.105/0.028 ms`, versus `5.94 ms` for Python;
- a TH08-shaped 32-frame `(4,5,6)` solve with all 17 root actions and nine
  focused continuation actions takes about `29.52 ms`;
- unrestricted 17-action continuation takes about `1.51 s`, and a 32-frame
  `(2..9)` support still exceeds three seconds;
- bounded top-2 legacy scheduling is about `0.62 ms`;
- physical seed/specialization medians are about `29.13/7.68 ms`;
- extra shadow telemetry costs roughly `3 ms`;
- background contention raised local planning and action lag;
- only `23%` of same-policy retarget revisions completed by the next decision
  in the bounded physical run.

C++ is justified for the recurrence, belief canonicalization, batched
successor construction, memo tables, dependency tracking, and cooperative
cancellation.  Python remains suitable for experiment orchestration and
compact reporting.  Rewriting lookup or top-level scheduling in C++ cannot by
itself solve state explosion or CPU contention.

## 9. Algorithmic Paths To Evaluate

### A. Exact finite-horizon belief dynamic program

Memo key:

```text
(frame, row, column, active_action, pending_action, remaining_delay_mask)
```

Transition all actions, delays, and cadence values; group by successor
observation; recurse on the grouped belief.  This is the correctness reference
and may be practical only for focused horizons or sparse reachable tubes.

### B. Backward reachable belief tube

Start from the small set of roots reachable from recent physical observations,
construct only reachable observation classes, and perform exact backward
induction.  Root availability is complete only if the constructed tube covers
every admissible action/delay/cadence branch.

### C. Sound lower/upper bounds with anytime refinement

Maintain:

- a conservative controller lower bound from one admissible non-clairvoyant
  policy; and
- an optimistic upper bound from a relaxed/clairvoyant problem.

Refine states until the best action is certified or the issue deadline
expires.  On expiry, authority falls back to Boolean viability plus the fresh
local certificate.  A top-K scheduler can prioritize refinement but must not
be described as complete.

### D. Incremental policy-version repair

When a new clearance volume differs only in new tail frames or changed cells,
invalidate memo entries whose dependency cone intersects the change.  Reusing
values by version number or geometric proximity alone is unsound.

## 10. Immediate Experiment Sequence

1. Treat the scalar belief oracle as the specification and keep
   scalar/native differential parity.
2. Infer a finite cadence/workload automaton from traces, then adversarially
   test that its admitted schedules cover the physical controller.  A
   trace-predicted interval is not a hard contract.
3. Seed the unrestricted solve with the all-root/focused-continuation lower
   bound and add a proven clairvoyant upper bound.  Refine only unresolved
   actions/states before the deadline.
4. Measure action certification rate, bound gaps, state counts, and
   whole-controller CPU delivery on retained capsules.
5. Do not spend another physical trial until offline correctness and delivery
   gates identify a configuration with a plausible no-contention budget.

## 11. First Audit Result

The corrected audit is complete. CE-0111 disproves one-transition cadence as a
full winning certificate, CE-0112 disproves future maximization over an exact
hidden remaining delay, and CE-0114 records the legacy decision-as-write
error. The independent belief oracle and native bitmask workspace implement
conditional no-write plus the observation-partition recurrence.

Full results, performance scaling, physical prewarm rejection, and the
conservative all-root/focused-continuation policy class are recorded in
`BELIEF_PIPELINE_CORRECTNESS_AND_PERFORMANCE_20260725.md`. The remaining
formal question is no longer whether Python and C++ agree. It is which
cadence/workload process the controller can actually guarantee, whether the
one-pending estimator invariant matches multi-key native input, and which
bounded policy class can be delivered without perturbing the hard-safety
loop.

## 12. Budgeted Policy-Class Refinement

The first bounded policy family is now implemented and specified in
`BUDGETED_BELIEF_REFINEMENT_20260725.md`. With complete root actions `A`,
base continuation actions `F`, extra actions `E = A \ F`, and per-history
budget `B`, the controller may choose `E` at no more than `B` future decision
epochs. This changes only the policy set, not the belief transition:

```text
Pi_0 subset Pi_1 subset ... subset Pi_unrestricted
L_0 <= L_1 <= ... <= V_unrestricted
```

Each completed `L_B` is an attainable non-clairvoyant lower bound. If `B`
covers every possible remaining decision epoch, the finite policy class is
unrestricted. A small `B` is not an optimality certificate, even when two
adjacent labels agree. Native memo identity includes `B`, and progressive
queries may reuse completed lower-budget states without mixing their values.

The revealed-remaining-delay recurrence is implemented as a proved optimistic
native upper bound and matches its independent scalar oracle. The
incumbent-seeded threshold recurrence in
`INCUMBENT_UPPER_CERTIFICATION_20260725.md` now determines, without complete
upper labels, exactly which upper root actions can strictly beat a completed
attainable lower label. Its boolean recursion retains controller existential,
nature universal, and observation-merge semantics. Across 128 deterministic
finite games its unresolved mask matches the complete scalar upper; on the
structured workload it reduces upper certification from about `1.5 s` to
`0.062 ms`. Fresh Stage 6B capsules contain exact margin-only certificates
lasting up to `1907.33 ms`, so the native deadline now conservatively marks
the in-flight and unvisited root actions unresolved. Shortening the deadline
may only enlarge that set. Until bounds meet on a particular root, publication
may contain only the last completed lower-bound policy or the existing
fail-closed fallback.
