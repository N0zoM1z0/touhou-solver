# Anytime Dual-Bound Policy Synthesis

Status: implemented and validated as an offline finite-model prototype,
2026-07-25. No live action authority. Physical delivery and Stage-6B capsule
coverage remain open.

## 1. Decision Contract

For public belief root `b` and each root action `a`, maintain:

```text
L_a <= V_a <= U_a
```

where:

- `V_a` is the unrestricted non-clairvoyant finite-model value after choosing
  root action `a`;
- `L_a` is the exact robust value of an executable causal candidate policy or
  a declared restricted policy class;
- `U_a` is an admissible optimistic value under the same physical
  transitions, uncertainty support, clearance, and horizon.

All values use the existing lexicographic order:

```text
(guaranteed physical survival frames, worst bottleneck clearance).
```

The bounds answer two different stopping questions.

Feasibility sufficiency:

```text
exists a: L_a.frames == remaining_horizon and L_a.margin > 0
```

This proves that at least one modeled policy survives the requested horizon.
It does not require proving every other action inferior. The selected action
still needs the fresh issue-time hard certificate and a current immutable
model/version.

Optimality sufficiency for lower-best action `a*`:

```text
L_a* >= max_{a != a*} U_a
```

Only the second question requires closing every action gap. Survival research
must not pay an unrestricted-optimality cost when a completed attainable
lower policy already proves the required horizon.

If every lower action is losing, maximize the completed lower label first.
Upper work then determines which actions can still beat that incumbent and
where targeted refinement is useful.

## 2. Candidate Policy As A Safe Lower Bound

A proposer supplies a deterministic causal continuation policy:

```text
pi(observable belief state) -> action
```

The exact policy verifier preserves:

- conditional hold/no-write;
- every admitted command delay;
- every recursive decision cadence;
- observation-compatible remaining-delay merging;
- every collision/clearance branch.

It replaces only the controller recurrence:

```text
max over every continuation action
```

with:

```text
the single action selected by pi at that public observation.
```

The verifier therefore computes `V^pi` exactly for the declared finite model,
and `V^pi <= V_unrestricted`. A bad proposer weakens the lower bound; it
cannot manufacture safety.

The first proposed policy is `greedy_prefix`: at each continuation belief
state, choose the action with the best robust one-transition prefix label.
Every hidden remaining delay, new-write delay, and cadence branch participates
in that proposal score. The complete horizon is then verified under that
fixed causal rule. Root actions remain exhaustive so the result supplies
per-action attainable labels.

Monte Carlo, MCTS, beam search, learned ranking, or the previous-version
policy may later propose `pi`. None of them gains hard authority without this
universal verifier.

## 3. Counterexample-Guided Lower Improvement

Proposed after the fixed-policy verifier passes parity and performance gates:

1. Evaluate candidate `pi` exactly.
2. Retain the worst nature branch and first decision observation at which a
   one-step action deviation can improve the verified label.
3. Patch only that observable policy state.
4. Re-evaluate exactly.
5. Accept the patch only when its completed robust lower label improves.
6. Repeat under a total CPU/state budget.

Every accepted iteration remains an executable causal lower policy. The
algorithm never treats an unfinished proposal or a sampled rollout as a
certificate.

This is policy-space CEGIS: heuristic work proposes a small policy change;
the adversarial verifier either raises the incumbent or returns the next
counterexample. It avoids enumerating every controller action at every
belief state unless counterexamples require them.

## 4. Gap-Directed Upper Refinement

The existing revealed-exact-remaining-delay recurrence is an upper bound, but
an unresolved action may exploit information unavailable to the physical
controller. It is not proof that the unrestricted belief policy beats the
lower incumbent.

For actions still satisfying `U_a > max L`, refine in two directions:

- raise `L` using targeted candidate-policy changes;
- lower `U` by replacing exact delay revelation with a coarser artificial
  observation partition that still reveals at least as much as the physical
  observation.

Candidate upper partitions include:

- remaining-delay buckets;
- reveal exact delay only after a declared future epoch;
- split only the observation class used by an optimistic witness.

Any intermediate partition is a valid upper only if every physical
observation class is contained in one artificial class or is further
partitioned by extra information. Accidentally merging distinct physical
observations would not be an upper bound. Independent scalar comparison to
the exact belief value is mandatory.

## 5. Cross-Version Reuse

Two reuse levels have different proof obligations.

Safe warm proposal:

- reuse the previous candidate policy, action ordering, or search tree;
- recompute its exact value under the new immutable model/version.

This reuses no truth claim and is always safe.

Proof-state reuse requires a content identity:

```text
(belief state,
 horizon endpoint,
 transition contract,
 hashes of every clearance frame/tile read by the subproblem)
```

A global version number or geometric proximity is insufficient. A new
clearance volume may reuse a completed memo node only when all dependencies
are bit-identical. Otherwise invalidate the node and its predecessor cone.
The first implementation should prefer warm proposals over complex
dependency tracking.

## 6. Performance Accounting

For every workload report:

- time/states/simulations to first completed candidate lower;
- time to full-horizon feasibility;
- time to decision optimality, when achieved;
- lower-best action and label versus unrestricted exact belief;
- upper unresolved actions;
- candidate-policy evaluation versus restricted `B=0` and unrestricted
  action search;
- proposal time separate from exact verification;
- current-version/root reuse rate;
- native read, local planning, and action lag before physical promotion.

The current 113-ms hard upper root is the first deterministic stress case.
Success is not “upper finishes faster” alone. Useful outcomes include a
full-horizon candidate lower before upper completion, a certified
decision-equivalent action, or a smaller exact verifier workload.

## 7. Ordered Experiment

1. Add independent scalar and native `greedy_prefix` fixed-policy
   verification. Require per-action label parity.
2. Compare it with `B=0`, unrestricted belief, and revealed-delay upper on
   deterministic randomized games and the retained hard structured root.
3. If the candidate is materially cheaper but weak, add exact
   counterexample-guided policy patches.
4. Refine upper information only for gaps that lower policy improvement does
   not close.
5. Measure previous-policy proposal reuse on dependency-changed roots before
   implementing proof-memo transfer.
6. Keep all work offline/shadow until whole-controller contention and fresh
   issue-time delivery are measured.

## 8. Falsification Conditions

Stop or revise the approach if:

- scalar/native candidate labels differ;
- a candidate label exceeds the unrestricted exact belief value;
- the policy selector conditions on exact hidden remaining delay;
- timeout publishes an incomplete candidate value;
- candidate verification performs work comparable to unrestricted search
  without improving time to a useful lower bound;
- an intermediate upper falls below the independent exact belief value;
- cross-version proof reuse survives a changed dependency hash.

## 9. Implemented Algorithm

Observed implementation:

1. `greedy_prefix` supplies nested top-K causal lower policy classes in the
   independent scalar oracle and C++ kernel.
2. A singleton portfolio evaluates one stationary continuation class per
   action. Each candidate is solved exactly over every modeled hidden delay
   and cadence branch.
3. Per-root-action labels are merged by maximum. This is attainable because
   the controller may publicly choose the pair `(root action, continuation
   class)` before nature branches.
4. If any completed candidate survives the full horizon with positive
   margin, feasibility stops immediately. Unvisited or timed-out candidates
   contribute no label.
5. For optimality work, the best candidate witness and one unresolved upper
   root action seed a restricted action-column class.
6. The C++ verifier follows the target action's worst restricted path and
   proposes one excluded one-step deviation. The proposal has no authority;
   only a completed exact re-solve of the expanded class raises `L`.
7. The upper threshold is recomputed against the raised incumbent until no
   action can strictly exceed it or the declared column budget is exhausted.

This is currently action-column CEGIS, not arbitrary per-observation policy
patching. A column permits an action at every future public belief state, so
it is a larger but simpler causal policy class. It remains a sound attainable
lower bound.

The exact unrestricted solver also orders continuation actions by a robust
one-transition proposal before applying its existing admissible upper bound.
This changes expansion order only. It does not remove actions or change the
finite-game value.

## 10. Retained Evidence

Observed differential evidence in
`artifacts/benchmarks/dual_bound_policy_synthesis_20260725.json`:

- 128 deterministic scalar/native games: zero exact parity failures, zero
  candidate parity failures, zero candidate-above-exact violations, zero
  singleton-portfolio-above-exact violations, and zero upper-certificate
  mismatches.
- Candidate greedy-prefix native median was `0.0827 ms` and 31.5 memoized
  states, versus unrestricted native median `0.1472 ms` and 43.5 states on
  the small cohort.
- On structured hard seed 0, unrestricted exact belief cost
  `4379.39 ms`; the old nine-action `B=0` lower cost `733.42 ms`.
- Seed-0 full-horizon feasibility arrived after two singleton candidates in
  median `4.01 ms`. It is a valid survival witness even though its
  `(32, 9.44357)` label is not optimal.
- All 17 singleton candidates cost median `36.68 ms` and raised the incumbent
  to `(32, 17.02608)`, leaving only `up_left_fast` unresolved.
- Gap-directed columns
  `down_right_fast -> up_left_fast -> up` reached the unrestricted exact
  label `(32, 18.80272)` and closed the upper certificate. End-to-end median
  was `287.64 ms`, about 15.2 times faster than constructing the unrestricted
  exact value.
- On structured seed 3, the first `always_stay` candidate proved feasibility
  in median `1.90 ms`; dual optimality cost median `38.36 ms` versus
  `209.30 ms` unrestricted exact.

The important delivery result is not the `287.64 ms` optimality time. It is
that a current finite-model feasibility certificate exists in `1.90--4.01
ms` on the two retained hard roots. Routine synchronous control therefore
does not need the 113-ms upper. Upper work is for optional optimality,
diagnosis, or lower-policy refinement.

## 11. Upper Information Hierarchy Result

Implemented remaining-delay observation buckets have width:

```text
0 = physical hidden delay
1 = exact remaining-delay revelation
k > 1 = reveal ceil(remaining / k)
```

Power-of-two widths form nested observation refinements. Six randomized
scalar/native cohorts verify:

```text
V_physical <= U_4 <= U_2 <= U_1
```

with exact per-action scalar/native parity.

Observed hard-root evidence in
`artifacts/benchmarks/upper_hierarchy_cross_version_20260725.json` rejects
bucket coarsening as the next primary performance lever:

- against singleton incumbent `(32, 17.02608)`, every width `62..1` correctly
  leaves only `up_left_fast` unresolved;
- median threshold time remains `114.25--120.99 ms`;
- against the refined exact incumbent, every width certifies all actions in
  `55.79--63.43 ms`.

Width 62 is exactly the physical observation for the admitted contract:
positive remaining delay is bounded by 62 and maps to one constant bucket,
while the already-public pending-action field distinguishes the no-pending
case. Scalar/native regression requires width 62 and width 0 to have
bit-identical per-action labels. The gap-directed synthesizer therefore uses
width 62, not the clairvoyant width 1, to choose refinement targets. The first
threshold must genuinely establish that `up_left_fast` can beat the singleton
incumbent; its gap is not an information-relaxation artifact.

## 12. Cross-Version Cold-Start Result

Implemented reuse transfers only candidate order:

```text
previous verified candidate labels -> proposer ranking
new version -> exact re-verification -> new labels
```

No memo state, label, feasibility claim, or certificate crosses the version
boundary.

On a retained seed-0 root with every future clearance cell changed by
`+0.125`, seven repetitions measured:

- default order: median `3.980 ms`, two completed candidates, feasible label
  `(32, 9.56857)`;
- previous-version order: median `2.200 ms`, one newly verified candidate,
  feasible label `(32, 17.15108)`;
- full current-version portfolios in both orders produced identical
  per-action labels.

This is a 45-percent time-to-feasibility improvement on one adjacent-version
workload, not a general hit-rate claim. The safe reusable object is a search
preference. Content-addressed proof-memo transfer remains unimplemented and
is not needed for the current feasibility-first path.

## 13. Current Decision And Remaining Gates

Observed:

- The previous “hard root must synchronously accumulate about 113 ms” premise
  is false for roots where a short candidate portfolio proves full-horizon
  feasibility.
- Monte Carlo/MCTS/beam search can be added as candidate generators without
  changing safety semantics, but the retained deterministic stationary
  portfolio is already sufficient on both structured roots.
- Exact unrestricted belief growth remains real if unique optimality is
  demanded. The algorithm has not made exponential belief growth disappear;
  it has changed which decision questions require paying for it.

Still required before live influence:

1. replay the feasibility-first portfolio on retained Stage-6B roots,
   especially genuinely losing roots where no candidate can survive;
2. measure candidate verification concurrently with Boolean publication,
   native reads, local planning, and issue-time action delivery;
3. publish the root action together with its candidate witness, immutable
   model version, horizon, and expiry;
4. fall back to Boolean policy plus a fresh local hard certificate on every
   miss, timeout, stale version, or non-winning candidate;
5. only then run a physical shadow and compare policy age/action lag before
   considering authority.

Checkpoint validation rebuilt both native libraries. Linux and Windows
complete quick suites pass 475 tests in `2.270/4.056 s`.
