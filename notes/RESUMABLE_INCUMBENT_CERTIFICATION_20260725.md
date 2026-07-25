# Resumable Incumbent Certification

Status: verified offline algorithm checkpoint, 2026-07-25. It grants no live
action authority and is not a physical acceptance result.

## Decision

Use repeated short service slices only as a resumable exact threshold search,
not as independent simulations and not as a Monte Carlo safety certificate.
For one bit-identical lower threshold and one exact immutable root, retain
only completed proof subproblems and completed root-action results. Any
interrupted branch remains unresolved.

This changes a hard optimistic-upper query from one synchronous roughly
110-ms call into about 21--23 individually bounded 5-ms calls while preserving
the exact final unresolved-action mask. It does not reduce asymptotic search,
does not transfer work across a changed root or policy version, and does not
close a genuine lower/upper gap.

## Formal Problem

Let:

- `M` be one immutable finite upper model: axes, clearance volume, motion,
  delay support, recursive cadence support, boundary behavior, horizon, and
  unrestricted action class;
- `v` be the policy/model version identifying `M`;
- `r` be the canonical public root, including frame, position, active action,
  pending action, remaining-delay support, and continuation budget;
- `L = (f, m)` be a completed attainable lower label;
- `U_a(r)` be the exact revealed-remaining-delay optimistic value of root
  action `a`.

The threshold query returns

```text
E(r, L) = {a | U_a(r) > L}
```

under the lexicographic order

```text
(guaranteed physical frames, bottleneck signed clearance).
```

The exact session identity is

```text
K = (
    immutable workspace/version,
    canonical root r,
    root_frame + L.frames,
    bit_pattern(float32(L.margin))
)
```

Bit identity is intentional. Approximate equality is not enough to reuse a
proof made against another threshold.

## Persistent State

For a fixed `K`, the native workspace retains:

```text
threshold_memo[prefix_margin_above][belief_state] -> bool
root_status[action] in {unknown, rejected, exceeds}
```

Meanings:

- `rejected`: the exact optimistic action value cannot strictly exceed `L`;
- `exceeds`: the exact optimistic action value can strictly exceed `L`;
- `unknown`: the action has not completed under this session.

Only a recursively completed call inserts a threshold memo entry. A deadline
exception unwinds without inserting a result for its incomplete state. Fully
completed descendants below that interrupted spine remain reusable because
their truth value is independent of the caller's completion.

If any component of `K` changes, both threshold memos and all root statuses
are cleared. The Python API separately rejects a stale `policy_version`; the
C++ workspace itself is immutable.

## Slice Semantics

One slice:

1. skips root actions already marked `rejected` or `exceeds`;
2. resumes the first `unknown` action using completed threshold memos;
3. records a root status only after that action returns normally;
4. on deadline, leaves the in-flight action `unknown`;
5. returns every known `exceeds` action plus every still-`unknown` action as
   unresolved.

Therefore an expired slice returns

```text
reported_unresolved = proved_exceeds union unknown
```

and a completed session returns exactly `proved_exceeds`.

The implementation currently preserves completed memo descendants but not
the explicit native DFS call stack. A later slice may traverse the incomplete
spine again. This is a measured limitation, not a correctness gap.

## Correctness Argument

The threshold recurrence itself is proved equivalent to comparing the
complete optimistic upper action label with `L` in
`INCUMBENT_UPPER_CERTIFICATION_20260725.md`.

Resumption preserves that result:

1. Every retained threshold memo was produced by a normally completed exact
   recurrence on the same `M`, threshold, and prefix bit.
2. No incomplete state is assigned a Boolean result.
3. A completed `rejected` or `exceeds` root status is therefore exact and may
   be reused.
4. At deadline, including every `unknown` action can only enlarge the exact
   unresolved set.
5. Repeated slices monotonically replace `unknown` with an exact root status.
   Once no deadline expires, the returned mask equals a one-shot exact query.

The proof does not depend on slice duration or scheduler timing. Cancellation
has the same fail-closed behavior as before; it does not publish a partial
certificate.

## Why This Is Not Monte Carlo

Hard safety is a worst-case game. A rare delay, cadence, or hidden-state
branch is still part of nature's universal choice. Sampling may miss that
branch, so independent Monte Carlo, MCTS, or beam rollouts have unknown error
direction and cannot certify survival or unrestricted optimality.

Sampling or heuristic search may still be useful as:

- a candidate-policy proposer;
- a root-action/branch ordering heuristic;
- a counterexample-guided proposal step followed by an exact adversarial
  verifier.

Such a heuristic must not prune a branch or publish hard safety unless the
exact verifier proves the same result.

## Retained Experiment

Executable:

```bash
PYTHONPATH=scripts python \
  scripts/benchmarks/benchmark_resumable_upper_certification.py \
  artifacts/benchmarks/resumable_upper_certification_20260725.json
```

Workload:

- deterministic structured seed `0`;
- 32-frame horizon;
- 17 root/upper actions;
- nine continuation actions in the attainable lower policy;
- delay support `[1..6]`;
- recursive cadence `(4,5,6)`;
- root row/column `13/12`, active `stay`, and a pending command with remaining
  support `[1..6]`;
- lower label `(32, 10.1491794586)`.

The lower solve took `755.00 ms` once. Five independent upper repetitions
gave:

| Mode | Median | p95 | Max |
| --- | ---: | ---: | ---: |
| one-shot exact | 109.39 ms | 110.36 ms | 112.92 ms |
| resumable 5-ms slices, total | 112.92 ms | 113.61 ms | 114.17 ms |
| resumable slice count | 23 | 23 | 23 |
| fresh 5-ms restarts, same count total | 116.28 ms | 116.32 ms | 116.46 ms |

All five resumable runs:

- completed in 21 to 23 slices;
- returned a conservative superset on every intermediate slice;
- had monotonically non-increasing unresolved counts;
- ended at the exact eight-action unresolved mask;
- produced exactly the same `11,436` completed threshold states as one-shot
  exact.

Median hidden simulations were approximately `622,259` one-shot and
`632,584` resumable, about 1.7 percent extra work from repeated incomplete
spines and slice checks. The wall-time overhead was about 3 percent.

Fresh restart was the falsifying control. After the same 21--23 attempts,
every 5-ms call still returned all 17 actions unresolved. Median cumulative
work was `24,517` newly constructed states and `679,156` hidden simulations:
the short calls repeated work rather than converging.

A one-shot timeout equal to the resumable nominal service budget
(`105--115 ms`) still reported deadline expiry in one of five runs. This is
ordinary runtime jitter: one large call does not provide the same bounded
service granularity.

Retained artifact:
`artifacts/benchmarks/resumable_upper_certification_20260725.json`.

## What Was Solved

Observed:

- repeated short calls now accumulate exact work instead of restarting;
- each call may be scheduled as a small background service quantum;
- intermediate results remain conservative;
- the completed result has exact parity with one-shot upper certification;
- C++ already owns the expensive recurrence, so rewriting this layer from
  Python would not address the remaining state growth.

This solves the synchronous-delivery form of the hard-root problem for a root
that remains valid long enough.

## What Remains

Observed:

- the hard root needs roughly 112 ms of cumulative CPU even after resumption;
- its externally visible unresolved mask first shrinks only around slice nine;
- exact completion still leaves eight actions unresolved because the lower
  policy class is genuinely weaker than the optimistic upper;
- resumable work is invalidated by a changed canonical root, threshold, or
  policy version.

Therefore this checkpoint does **not** solve cross-version cold start. If a
live Boolean policy/root is replaced every one or two decisions, the correct
session may expire before accumulating enough CPU. Reusing its memo under a
“nearby” root or changed clearance volume would be unsound without a proved
equivalence or reusable transition contract.

It also does not prove physical hazard-model accuracy, restore Stage 6B
viability, or authorize the upper worker to contend with native read/local
planning.

## Formal Review

1. **State equivalence:** the session key contains the complete canonical
   model root. It merges no additional physical histories.
2. **Causal uncertainty:** the resumed recurrence preserves the existing
   controller-exists/nature-for-all quantifiers and observation grouping.
   Scheduling does not reveal hidden delay or cadence.
3. **Physical relevance:** completion certifies the declared finite upper
   threshold question, not the fidelity or freshness of the hazard model.
4. **Solver validity:** completed results are exact for that finite threshold
   game; expired outputs are conservative supersets. Independent complete
   upper comparisons remain the differential oracle.
5. **Delivery:** 5-ms service slices bound individual blocking work, but the
   root must remain bit-identical for roughly 115 ms in this workload. No
   physical contention measurement has yet been made.

## Next Gate

1. Put the resumable session in an isolated newest-version-wins executor with
   a total per-root CPU/lifetime limit; measure exact-session lifetime,
   current-version hit rate, first useful mask time, and read/local/action-lag
   contention in shadow.
2. Refine attainable lower policies only for the exact eight unresolved root
   actions. Completing the optimistic upper is not useful if the bound gap
   remains.
3. Prefer proved action/branch ordering and dominance rules that expose
   rejections earlier. Ordering may change anytime usefulness but not delete
   branches.
4. Add an explicit iterative frontier only if new workloads show material
   incomplete-spine repetition. The current excess simulation work is small.
5. Investigate cross-version transfer only through a written equivalence,
   re-rooting, or versioned reusable-transition proof. Otherwise reset.
6. Keep Monte Carlo/MCTS/beam proposals shadow-only and require an exact
   adversarial verifier before any hard-safety claim.
