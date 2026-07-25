# Incumbent-Seeded Upper Certification

Status: verified offline algorithm checkpoint, 2026-07-25. No live action
authority is granted.

## Problem

`BUDGETED_BELIEF_REFINEMENT_20260725.md` supplies attainable lower bounds

```text
L_0 <= L_1 <= ... <= V_unrestricted
```

and the revealed-remaining-delay information relaxation supplies a proved
upper bound `U`. On the retained 32-frame TH08-shaped problem, computing the
complete upper action labels costs about 1.5 seconds. That proves a bound but
cannot be delivered in the control loop.

For certification, complete upper labels are unnecessary. Given one completed
attainable lower state label `L`, the only question is:

```text
does any root action have U_action > L?
```

If the answer is no, then

```text
L <= V_unrestricted <= max_action U_action <= L
```

and the unrestricted finite-model state value is exactly `L`. Any root action
whose attainable lower label equals `L` is safe to select under that model.

## Threshold Game

Survival labels are lexicographic:

```text
(guaranteed physical frames, bottleneck signed clearance)
```

For a fixed public root and lower label `L`, convert its frame component to an
absolute endpoint:

```text
target_frame = root_frame + L.frames
target_margin = L.margin
```

At an internal state, the recurrence only needs one additional bit:

```text
prefix_margin_above =
    every already traversed prefix margin > target_margin
```

An internal label exceeds the threshold exactly when:

```text
endpoint_frame > target_frame
or
(endpoint_frame == target_frame
 and prefix_margin_above
 and local_bottleneck_margin > target_margin)
```

The threshold recurrence preserves the original game quantifiers:

- controller action selection is existential;
- command delay, decision cadence, and hidden branch selection are universal;
- indistinguishable successor branches are merged before the next controller
  action;
- the revealed-delay upper model partitions successors by exact remaining
  delay, exactly as the complete optimistic recurrence does.

For one controller action, any nature branch that cannot strictly beat `L`
immediately disproves that action. At a controller state, the first action
whose every branch can beat `L` proves that state unresolved. Otherwise the
state is certified not to beat the incumbent.

## Correctness Argument

For a fixed threshold, memoize:

```text
(belief state, prefix_margin_above) -> can_upper_value_exceed_L
```

The boolean result is exact by backward induction on remaining horizon:

1. Terminal/collision states compare their absolute endpoint and bottleneck
   directly with `L`.
2. A controller state exceeds `L` iff at least one legal action exceeds it.
3. An action exceeds `L` iff every admitted hidden branch exceeds it.
4. Branches with the same revealed upper-model observation are merged before
   recurrence, preserving non-anticipativity for that relaxed model.

The existing prepared-action label remains an admissible local upper bound.
If it is already `<= L`, the complete action subtree may be discarded without
simulation below that root.

This proves equivalence with testing the complete optimistic action label
against `L`; it does not assume adjacent budgets have converged.

For a full-horizon lower label, any nature branch whose traversed prefix
margin is already `<= target_margin` can never strictly beat the incumbent.
The implementation rejects that branch before expanding its successor. It
also uses

```text
min over future frames (max clearance over all lattice cells)
```

as a game-relaxed suffix-margin upper bound. This admits teleporting to the
best cell independently at every frame, so it can only overestimate the real
controller and is safe for rejection when it still cannot beat the target.

Deadline expiry is also one-sided. Completed action rejections remain proved;
the action being evaluated and every unvisited action are returned as
unresolved with `deadline_expired=true`. Thus a shorter deadline can only
enlarge the unresolved set, never create a certificate.

## Implementation

- C++ decision recurrence:
  `native/belief_pipeline_survival_workspace.hpp`
- C ABI:
  `touhou_belief_pipeline_workspace_certify_upper_v2` with a separate
  deadline output; v1 remains a compatibility wrapper
- Python/native bridge:
  `BeliefPipelineNativeWorkspace.certify_upper`
- Public research API:
  `BeliefPipelineSurvivalWorkspace.certify_upper_bound`

The public API rejects:

- a non-revealed workspace;
- a restricted continuation action set;
- stale policy versions.

The lower label and upper workspace must describe the same immutable axes,
clearance volume, action motion, delays, cadence support, root, and boundary
contract. The implementation does not infer cross-version equivalence.

Threshold memos are cleared between different lower labels. Completed exact
upper memo entries, when present, may answer a threshold state directly
because they belong to the same immutable workspace.

## Differential Evidence

Retained artifact:
`artifacts/benchmarks/budgeted_belief_refinement_20260725.json`, schema v6.

Across 128 deterministic randomized finite games:

- belief scalar/native failures: `0`;
- complete revealed-upper scalar/native failures: `0`;
- lower-above-upper violations: `0`;
- threshold unresolved-mask mismatches against complete scalar upper: `0`.
- retained deterministic deadline case: the 1-ms result expires with all 17
  actions unresolved; the exact result has eight unresolved actions, so the
  partial set is a conservative superset.

Cold threshold certification:

| Metric | Median | p95 | Max |
| --- | ---: | ---: | ---: |
| wall time | 0.031 ms | 0.065 ms | 0.124 ms |
| memoized threshold states | 0 | 25 | 79 |
| hidden simulations | 14 | 230 | 680 |

The nonzero p95/max state counts exercise recursive threshold decisions; the
result is not only a root-prefilter smoke test.

## TH08-Shaped Result

Problem:

- 32-frame horizon;
- 17 root actions;
- nine focused base continuation actions for `L_0`;
- six command delays;
- recursive cadence `(4,5,6)`;
- 27x24 lattice.

Observed:

| Computation | Wall time |
| --- | ---: |
| attainable `L_0` | 32.99 ms |
| selective upper certificate | 0.062 ms |
| combined lower + certificate | 33.05 ms |
| previous complete optimistic upper | about 1,500 ms |

The certificate rejects all 17 root actions from a full-horizon prefix/suffix
bound, performs 17 root hidden simulations, expands zero recursive threshold
states, and returns no unresolved action. Therefore this workload's
unrestricted finite-model state value is certified by `L_0`.

The selective certificate is roughly four orders of magnitude cheaper than
the complete upper on this workload. The remaining cost is the attainable
lower solve, not upper certification.

## Stage 6B Physical-Capsule Result

Fresh instrumented hard-no-Bomb Lunatic Stage 6B run
`lunatic_route2_stage6b_unattended_20260725_204521` completed frames
`2..76235` with 15,536 decisions and 31 native hits. The established
Boolean/local controller remained authoritative; neither lower labels nor
upper certificates selected actions.

The offline cohort contains the root closest to 30 frames before each of the
31 hits plus one stratified non-hit root. It reconstructs exact observed
input, pending command, current delay support, `(4,5,6)` recursive cadence,
and a 32-frame capsule window.

Uncapped result:

- 32/32 lower queries completed;
- 31/32 state values certified;
- the remaining root retained eight unresolved actions;
- 30/31 pre-hit roots certified;
- certificate median/p95/max was `0.039/88.33/1907.33 ms`;
- the two longest otherwise certified searches cost
  `1907.33/540.83 ms`, expanding 111,901/22,134 threshold states.

Retained 100-ms anytime result:

- 29/32 roots certified;
- the same completed root retained eight unresolved actions;
- two deadline roots conservatively retained all 17 actions unresolved;
- certificate median/p95/max was `0.040/91.59/100.18 ms`;
- no lower query timed out.

The physical model was already losing at 28/31 sampled pre-hit roots around
30 frames before contact. The other three trace-Boolean viable roots had
full-horizon `L_0`. This separates the questions cleanly: the certificate can
bound unrestricted value without a complete upper solve, but it cannot rescue
a model whose viable set has already collapsed.

Retained evidence:

- `artifacts/viability_audit/stage6b_20260725_204521_belief_upper_certification.json`;
- `artifacts/viability_audit/stage6b_20260725_204521_belief_upper_certification_uncapped.json`;
- `notes/runs/lunatic_route2_stage6b_unattended_20260725_204521.md`.

## Boundaries

- This certifies the declared finite model, not hazard-model fidelity,
  cadence coverage, or physical delivery.
- A certificate is invalid if the lower result is stale, optimistic, from a
  different root/version, or not actually attainable.
- An unresolved result is not a failure; it requests a higher budget or more
  targeted lower refinement. A deadline-expired result must remain
  unresolved even if earlier actions were fully rejected.
- The result remains offline/shadow-only. Stage 6B established useful
  cross-stage coverage and a nontrivial tail, but did not measure an isolated
  shadow executor's CPU/read/local-plan contention.
- The fresh Stage 6B run correctly kept the established Boolean/local hard
  controller authoritative. No offline label in this note changed an action.

## Next Gate

1. For the one completed eight-action gap, refine only those actions and stop
   as soon as their lower value meets the upper threshold.
2. For the two deadline roots, evaluate action ordering and a stronger proved
   reachable-clearance relaxation; retain 100 ms as the service boundary.
3. Move the physical diagnosis earlier than the 30-frame losing roots and
   identify when control reserve/boundary pressure first makes `L_0` collapse.
4. Only then design an isolated shadow scheduler; no result in this checkpoint
   authorizes synchronous upper/lower work on the issue thread.
