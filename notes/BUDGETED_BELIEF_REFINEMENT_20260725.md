# Budgeted Belief-Policy Refinement

Status: verified offline algorithm checkpoint, 2026-07-25.  This is a
conservative anytime approximation for the finite belief game defined in
`AUGMENTED_PIPELINE_ROBUST_CONTROL_FORMALIZATION_20260725.md`.  It has no live
input authority.

## Question

The corrected non-clairvoyant recurrence is meaningful, but unrestricted
future actions grow too quickly.  The representative TH08-shaped
32-frame/17-action/`(4,5,6)` solve visits 45,116 belief states and performs
14,112,336 hidden simulations.  It takes about 1.55 seconds even in C++.

The algorithmic requirement is not merely “make that call faster.”  At every
deadline it must return a policy that is physically executable under the
declared finite model.  An interrupted optimistic search must never become a
hard-safety certificate.

## Finite-Model Contract

At a decision epoch the public belief state is

```text
b = (t, row, column, active, pending, R)
```

where `R` is the support of indistinguishable pending-command remaining
delays.  Nature selects command pickup delay and the next admitted decision
cadence.  The controller observes only the resulting public state, so hidden
branches with the same observation are merged before the next maximization.
Selecting the already-held desired action is hold/no-write and preserves the
old pending command.

The value is lexicographic:

```text
V(b) = (guaranteed collision-free physical frames,
        worst-branch bottleneck signed clearance)
```

This note changes only the future controller policy class.  It does not
change transitions, uncertainty, observations, collision semantics, or the
value order.

## Policy Classes

Let:

- `A` be the complete action set;
- `F` be a declared base set, currently the nine stay/focused TH08 actions;
- `E = A \ F` be the extra, currently fast, actions;
- `B >= 0` be a per-history remaining extra-action budget.

Every public root still evaluates every action in `A`, without consuming
budget.  At later decision epochs the controller may always select an action
in `F`; it may select an action in `E` only when `B > 0`, after which that
history continues with `B - 1`.

Selecting an extra action consumes budget even when it happens to be
hold/no-write.  This is deliberately conservative relative to a possible
“number of fast command writes” contract and makes `B=0` exactly the retained
all-root/focused-continuation policy class.

Call the resulting policy set `Pi_B` and its robust value `L_B`.

## Correctness Argument

For the declared finite model:

```text
Pi_0 subset Pi_1 subset ... subset Pi_unrestricted
L_0 <= L_1 <= ... <= V_unrestricted
```

The first relation holds because every policy using at most `B` extra future
decisions is also legal with budget `B+1`.  The second follows because
maximizing the same robust objective over a larger policy set cannot lower
the value.  Every `L_B` is attainable: it is produced by a legal
non-anticipative policy, not by dropping an uncertainty branch or revealing
hidden delay.

If `F union E = A` and `B` is at least the maximum number of future decision
epochs on any admitted finite-horizon history, `Pi_B` equals the unrestricted
finite policy class.  Thus the sequence converges exactly in finite time.
This fact does not imply that a practically affordable small budget has
already converged.

Budget is controller-visible state.  It is decremented by the controller's
own selected action, so adding it to the memo and observation keys does not
grant hidden information.  Replanning at the next physical observation is
also conservative: the new root again permits all actions for free and its
future budget is no smaller than the continuation promised by the prior
root, provided the immutable model/version is unchanged.

## Implementation

The independent scalar specification is
`scripts/touhou_control/variable_cadence_oracle.py`.

The native implementation is
`native/belief_pipeline_survival_workspace.hpp`.  Its memo key is now:

```text
(frame, row, column, active, pending, remaining_mask, budget)
```

The C ABI v3 constructor declares disjoint base and budgeted action masks plus
a maximum budget. C ABI v4 additionally selects the revealed-remaining-delay
information relaxation. The v2 query can request any root budget up to that
maximum. ABI v1/v2/v3 constructors and v1 query remain compatibility wrappers.

A single maximum-budget workspace may be queried in order `0,1,...,B`.
Completed lower-budget state values are exact for those keys and can be
reused by higher-budget states.  Deadline expiry cannot corrupt a public
root; the last completed lower-budget result remains the anytime incumbent.

## Evidence

Observed:

- Linux and Windows quick unit suites pass 471 tests in `1.324/2.481 s`
  after the research-test reduction and the new monotonic/native-parity
  regression.
- A retained 128-case randomized scalar/native differential, including
  budgets 0, 1, and 2, has zero belief-label failures and zero
  revealed-information upper-bound failures. It also has zero cases where a
  lower action label exceeds its corresponding upper label. Schema v6 also
  has zero selective-certificate unresolved-mask mismatches against the
  complete independent scalar upper.
- Four additional scalar adversarial seeds satisfy
  `L_0 <= L_1 <= L_2 <= V_unrestricted` for every root action.
- Warm exact-root lookup remains about 0.03 ms on the tiny differential.

Retained artifact:
`artifacts/benchmarks/budgeted_belief_refinement_20260725.json`.

On the structured 32-frame, 17-root-action, nine-base-action,
six-delay, `(4,5,6)` workload:

| Policy class | Incremental wall | New states | Hidden simulations |
| --- | ---: | ---: | ---: |
| `B=0` | 32.30 ms | 1,625 | 270,189 |
| `B=1` after `B=0` | 687.54 ms | 24,414 | 5,195,652 |
| `B=2` after `B=0,1` | 1,054.42 ms | 36,368 | 9,607,020 |
| unrestricted belief | 1,488.38 ms | 45,116 | 14,112,336 |
| revealed-delay upper | 1,471.15 ms | 62,237 | 13,368,249 |

The complete `B=0 -> 1 -> 2` refinement took 1,661.88 ms. Memo reuse makes
the `B=2` increment materially cheaper than a separate approximately
1.5-second `B=2` solve, but total states across all budget layers still grow
to 62,407.  C++ has removed interpreter overhead; policy-state growth is the
remaining cost.

For this particular structured field, `B=0` and the proved revealed-delay
upper bound both have state label `(32, 8.9031067)`. Therefore `B=0` certifies
the unrestricted finite-model state value on this workload; any of its five
lower-best actions is unrestricted-optimal. The same labels also persist
through `B=1`, `B=2`, and the exact unrestricted belief solve. This is a
valid certificate for this one model instance, not a proof that `B=0` is
generally optimal.

## Offline Iteration Policy

Use three distinct gates:

1. Unit gate: deterministic counterexamples, monotonicity, and a small
   scalar/native smoke differential.
2. Quick research gate: 16-case scalar/native differential plus structured
   `B=0/1`; this runs in about `1.1` seconds.
3. Full retained gate: 128 differential cases, `B=2`, unrestricted,
   long-horizon, and wide-cadence timeout/scaling cases; this takes about
   twelve seconds and runs only when the recurrence or native kernel changes.

The formal audit remains an independent Python oracle.  Its default is 16
cases per cohort (about 1.3 seconds); use `--cases 128` for a retained full
audit.  Replacing it with the same C++ recurrence would make it faster but
would remove implementation independence.  Large JSONL dossier/replay scans
remain streaming post-trial analysis and are not quick-iteration gates.

## What This Solves

This checkpoint converts unrestricted growth into a deadline-safe sequence of
attainable lower bounds. It also gives an exact finite convergence condition,
allows incremental C++ memo reuse, and supplies a proved native optimistic
upper bound. The first structured workload is now formally bracketed rather
than accepted from adjacent-budget agreement.

## What Remains

The independent complete upper remains useful as an offline oracle, but it is
no longer required for routine certification. The incumbent-seeded threshold
recurrence in `INCUMBENT_UPPER_CERTIFICATION_20260725.md` determines exactly
which optimistic root actions can strictly beat the completed lower label.
On the structured workload it costs `0.223 ms`, reports no unresolved
actions, and replaces the roughly `1.5 s` complete upper. After the
full-horizon prefix/suffix shortcut it costs `0.062 ms`; combined
lower-plus-certificate time is `33.05 ms`.

Fresh Stage 6B capsules show why the service boundary remains necessary. In a
32-root cohort centered about 30 frames before 31 physical hits, an uncapped
query certified 31 roots but one completed root retained eight unresolved
actions, while two otherwise certified margin-only searches cost
`1907.33/540.83 ms`. A 100-ms deadline profile certified 29 roots, retained
the eight-action gap, and conservatively returned all 17 actions unresolved
for the two expired searches. Deadline expiry enlarges uncertainty; it never
publishes a partial optimistic label as a certificate.

The remaining research sequence is:

1. refine budgets only for the Stage 6B actions/states whose upper bound can
   change the selected set;
2. move pre-hit analysis earlier and determine why 28/31 sampled roots were
   already losing about 30 frames before contact;
3. measure total lower-plus-certificate CPU and physical delivery relevance
   before creating any live shadow executor;
4. infer and validate a finite cadence/workload automaton to avoid an
   unsupported Cartesian cadence product;
5. retain the complete scalar/native upper only as the independent
   differential and unresolved-case oracle.

Until those gates pass, budgeted belief values remain offline/shadow research
and the live controller continues to use Boolean viability plus the fresh
local hard certificate.
