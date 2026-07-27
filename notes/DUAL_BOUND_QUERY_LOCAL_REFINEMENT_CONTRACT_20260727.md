# Dual-Bound Query-Local Refinement Contract

Date: 2026-07-27

Status: **offline finite-reference contract and semantic gate passed; delivery
failed**. The six retained spatial roots satisfy the declared action
inclusion gate and have completed lower witnesses. The Python patch builder
and dense rectangle solver take seconds and are rejected for live delivery.
This document does not promote query-local refinement, change the live Boolean
policy, or close G1 model-coverage, input-pipeline, clock, publication, or
delivery gates.

## 1. Physical Objective And Authority

The physical objective remains no-Bomb survival while delivering an input
before its issue deadline. G2 addresses one narrower question:

> When a 16-pixel finite lattice reports no action, can local 8-pixel and then
> 4-pixel computation recover an action without ever calling an action safe
> that the declared exhaustive fine reference calls unsafe?

Only a completed lower mask may eventually contribute action authority.
Upper masks select unresolved work and may never authorize input. The first
implementation remains offline even when the lower mask is nonempty.

Hazard slabs with `UNKNOWN` future coverage, the frozen-manager clock boundary
in CE-0120, incomplete complete-mask publication, a stale policy version, or a
missed delivery deadline still block physical authority independently of this
spatial result.

## 2. State, Observations, Actions, And Uncertainty

For the current game-neutral corridor recurrence, a lattice state is

```text
s = (layer k, active-input plane p, spatial point q)
```

The prepared problem supplies:

- one immutable spatial domain and horizon;
- the signed clearance volume for the declared hazard model;
- a complete named action alphabet;
- supported input-pickup delays;
- constant-velocity layer transitions;
- an optional terminal viability contract.

The visible active-input plane is preserved. A selected root action is fixed
before nature selects its hidden pickup-delay branch. The next layer exposes
the selected action as the new active plane. No policy may select a different
root action after observing the hidden branch.

G2's initial finite reference retains the existing movement-action alphabet.
The 36-token complete-mask belief recurrence from the G1 correction remains a
separate offline pipeline model until the corridor viability state and ABI are
extended explicitly. Equal-velocity complete masks must not be silently
merged when those models are joined.

## 3. Spatial Cell Semantics

Let `Q_h` be a lattice with spacing `h`. Let `pi_H(q)` project a fine point
`q` to the nearest coarse lattice point at spacing `H`, using the same
round-to-even rule and boundary clamping as `RobustViabilityPolicy.query`.
The coarse cell represented by `c` is the finite set

```text
B_H(c) = {q in Q_h : pi_H(q) = c}.
```

This is a lattice partition, not a square inferred from a drawing. Midpoint
ties can make neighboring cells contain different numbers of fine points.
The implementation therefore records the exact fine-to-coarse row and column
maps and rejects a partition that leaves a coarse cell without a reference
point.

For an exhaustive fine safe-action mask `F(k,p,z,q)`, where `z` denotes any
retained hidden-branch or other comparison axis, define:

```text
L(k,p,z,c) = intersection over q in B_H(c) of F(k,p,z,q)
U(k,p,z,c) = union        over q in B_H(c) of F(k,p,z,q).
```

Consequently, for every fine point:

```text
L(k,p,z,pi_H(q)) subset F(k,p,z,q)
F(k,p,z,q) subset U(k,p,z,pi_H(q)).
```

Time, active-input plane, selected root action, and hidden branch are leading
axes. Spatial aggregation is forbidden from reducing any of them.

The independent Python seam in
`scripts/touhou_control/corridor/dual_bounds.py` implements exactly this
intersection/union oracle, supports up to 64 action bits, lifts cell masks
back to the fine lattice, and reports the first action-specific inclusion
failure. Comparing only `state_viable = (mask != 0)` is insufficient.

## 4. Transition Quantifiers

For an exact lattice point `q`, active plane `p`, selected action `a`, and
hidden delay `d`, let:

```text
T(q,p,a,d) = (q', a)
P(k,q,p,a,d) = every physical sample of that branch is safe.
```

The declared robust fine recurrence is:

```text
V_N(p,q) = terminal_safe(p,q)

F_k(p,q,a) =
    current_safe(k,q)
    and for every d:
        P(k,q,p,a,d)
        and V_(k+1)(T(q,p,a,d))

V_k(p,q) = exists a: F_k(p,q,a).
```

The universal delay quantifier stays inside one selected action. A diagnostic
branch predicate may be retained as an extra array axis, but it must be
intersected over the complete delay support before calling the action robust.

The intersection/union definition in Section 3 is the normative fine-reference
bound. A future accelerated coarse recurrence is acceptable only if it is
shown to enclose those masks. In particular:

- subtracting only nearest-lattice sampling error certifies a trajectory from
  its lattice center; it does not automatically certify every fine state in a
  coarse Voronoi cell;
- an upper recurrence using `forall delay, exists unrelated fine witness`
  may change its initial-state witness between nature branches and is not the
  normative cell union;
- a lower recurrence may conservatively require one common action and lower
  successor cells for every fine state, but it must still pass the exhaustive
  inclusion gate.

Until an accelerated recurrence passes that gate, an unresolved cell has:

```text
lower = 0
upper = ALL_DECLARED_ACTIONS.
```

This is expensive but sound. Completed exact local work may replace those
trivial bounds through the Section 3 aggregation.

## 5. Root-Relevant Tube

The refinement scope is branch-specific. For each declared root action `a`
and each root hidden delay `d`:

1. the forward tube starts from the exact projected root
   `(k=0,p_root,q_root)`;
2. its first transition fixes both `a` and `d`;
3. later layers expand all causal selected actions and all supported hidden
   delays;
4. no collision assumption is used to shrink this kinematic tube.

The terminal co-reachable tube is a may-predecessor closure:

```text
C_N = declared external terminal scope, or all states when none exists
C_k(p,q) = exists a,d: T(q,p,a,d) is in C_(k+1).
```

This existential closure is deliberately optimistic. It may retain states
that cannot satisfy the robust safety recurrence, but it must not discard a
state merely because coarse hazard sampling is ambiguous.

The root-relevant lattice states for branch `(a,d)` are:

```text
R_(a,d) = Forward_(a,d) intersect C.
```

`PreparedDualBoundScope` builds this relation directly from a
`PreparedCorridorProblem`. The transition implementation is independent of
the private vectorized viability transition cache and preserves active plane,
selected action, and delay indices explicitly.

This first checkpoint covers layer endpoints. Before a patch solver may omit
clearance tiles, it must also include every physical transition sample read by
an edge whose source or successor can affect `R_(a,d)`, plus a conservative
spatial halo. The halo/edge closure is a required next checkpoint, not implied
by endpoint membership.

## 6. Mixed 16/8/4 Refinement And Completion

The intended work order is:

1. form 16-pixel trivial or proved bounds;
2. enumerate root-action/root-delay relevant ambiguity;
3. compute a closed 8-pixel patch only where `L != U` and the patch can affect
   a root action;
4. if the root mask remains unresolved, compute a closed 4-pixel patch with
   the conservative transition-sample halo;
5. stop once the completed root lower mask is sufficient for the declared
   offline experiment, rather than filling the entire field.

Each patch result records:

- immutable prepared-problem and root identity;
- coarse/fine axes and exact partition;
- action alphabet and action-bit mapping;
- active plane and hidden branch;
- completed spatial cells and transition-sample closure;
- lower and upper action masks;
- elapsed time, deadline, and completion status;
- exhaustive-reference inclusion report.

A timeout or cancellation publishes no partial upper-derived action. It may
publish only lower bits whose complete dependency closure was finished before
the deadline. All uncompleted lower bits remain zero; all uncompleted upper
bits remain one. Work is reusable only for the identical immutable problem
version and dependency content.

Uniform full-field 4-pixel induction remains rejected for live use by
CE-0102 and the retained delivery measurements.

## 7. Hard Gates

For deterministic fixtures and the six retained `SPATIAL_AMBIGUITY` roots:

```text
lift(L_mixed) subset exhaustive_fine_reference
exhaustive_fine_reference subset lift(U_mixed)
```

The report must have:

- zero false-safe action bits;
- zero missing upper action bits;
- comparisons for every root action;
- comparisons for every active/pipeline plane represented by the model;
- comparisons before universal reduction for every hidden branch;
- deterministic replay and content identity.

The 2026-07-27 offline semantic gate now establishes:

- six known spatial cases explained by a completed sound lower witness;
- bounded 16-to-8-to-4 work rather than uniform 4-pixel work;
- zero false-safe and zero missing-upper action bits on retained roots;
- independent scalar branch inclusion on generated stop, resume, redirect,
  and reversal cases.

G2 still requires:

- scalar/native parity if a sparse native kernel is added;
- Windows end-to-end solve, publication-age, contention, cancellation, and
  delivery measurements;
- shadow physical evidence before any authority proposal.

## 8. Approximation Direction And Falsification

Current approximations are:

- **lower:** conservative by exact fine-mask intersection;
- **upper:** optimistic by exact fine-mask union;
- **unresolved default:** conservative lower zero and optimistic upper all;
- **root relevance:** optimistic kinematic over-approximation because hazards
  are not used to prune;
- **physical interpretation:** unknown direction until hazard coverage,
  continuous-position error, clock, and actuator-model gates are closed.

The claim is falsified by any one of:

- a lower action bit absent from the exhaustive fine reference at a member
  point;
- a fine-reference action bit absent from the lifted upper mask;
- a mismatch hidden by reducing branches or active planes to one Boolean;
- a winning fine dependency outside the computed patch/halo;
- changing the selected root action after observing its hidden delay;
- a timeout publishing an unfinished lower dependency;
- a live issue from an offline, stale, model-unknown, or late result.

## 9. Five Formal Questions

1. **Which histories merge?** Fine lattice histories merge only when their
   positions project to the same declared cell and all retained leading state
   axes match. Active plane and hidden-branch comparisons are not merged.
   Physically distinct complete masks, future hazards, and frozen-clock
   histories remain outside this movement-only G2 state.
2. **Are the choices causal?** Yes for this finite contract: one root action is
   fixed before the hidden root delay, then later actions are chosen only at
   later decision layers. Robust action labels universally quantify delay.
3. **What does an exact solve answer?** Feasibility of the declared finite
   hazard, movement, delay, horizon, and terminal model at the exhaustive
   reference resolution. It does not by itself answer physical TH08 survival.
4. **What does the algorithm prove?** The completed offline implementation
   proves the hard action inclusion relation for generated scalar cases and
   the six retained roots under the declared finite model. The retained
   vectorized reference shares the dense native recurrence, so it is not an
   independent implementation oracle. A lower/reference or reference/upper
   inclusion counterexample falsifies soundness immediately.
5. **Can it be consumed before issue?** No. The retained patch builder takes
   `3160.63..14153.12 ms` and the vector solve takes
   `859.02..4008.67 ms` on Linux. This checkpoint has no publisher or
   consumer. A sparse/native successor must pass Windows age/delivery gates
   and retain the existing fail-closed local-certificate and exact-version
   transaction boundary before promotion can even be proposed.

The retained result and exact limitations are recorded in
`notes/G2_QUERY_LOCAL_REFINEMENT_GATE_20260727.md`.
