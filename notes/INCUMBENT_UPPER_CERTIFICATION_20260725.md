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

## Implementation

- C++ decision recurrence:
  `native/belief_pipeline_survival_workspace.hpp`
- C ABI:
  `touhou_belief_pipeline_workspace_certify_upper_v1`
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

Cold threshold certification:

| Metric | Median | p95 | Max |
| --- | ---: | ---: | ---: |
| wall time | 0.030 ms | 0.072 ms | 0.143 ms |
| memoized threshold states | 0 | 25 | 79 |
| hidden simulations | 42 | 294 | 858 |

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
| attainable `L_0` | 32.35 ms |
| selective upper certificate | 0.223 ms |
| combined lower + certificate | 32.57 ms |
| previous complete optimistic upper | about 1,500 ms |

The certificate prunes all 17 root actions by their admissible prepared upper
labels, performs 1,746 root hidden simulations, expands zero recursive
threshold states, and returns no unresolved action. Therefore this workload's
unrestricted finite-model state value is certified by `L_0`.

The selective certificate is roughly four orders of magnitude cheaper than
the complete upper on this workload. The remaining cost is the attainable
lower solve, not upper certification.

## Boundaries

- This certifies the declared finite model, not hazard-model fidelity,
  cadence coverage, or physical delivery.
- A certificate is invalid if the lower result is stale, optimistic, from a
  different root/version, or not actually attainable.
- An unresolved result is not a failure; it requests a higher budget or more
  targeted lower refinement.
- The result remains offline/shadow-only until retained physical capsules show
  useful certification coverage without CPU/read/local-plan contention.
- A physical Stage 6B run should keep the established Boolean/local hard
  controller authoritative. Apply this certificate to retained Stage 6B
  workloads offline before considering a shadow executor.

## Next Gate

1. Run a fresh Lunatic Stage 6B hard-no-Bomb workload to avoid Stage-5-only
   selection.
2. Retain its normal physical dossier and counterexamples.
3. If exact corridor capsules are available without changing delivery, replay
   `L_0` plus threshold certification offline.
4. Measure certification rate, unresolved action masks, lower wall time, and
   whole-controller relevance.
5. Only then design an isolated shadow scheduler; no result in this checkpoint
   authorizes synchronous upper/lower work on the issue thread.
