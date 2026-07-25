# Cancellable Rolling Exact-Root Prewarm

Date: 2026-07-25
Status: verified offline scheduler; shadow-only

## Question And Outcome

The exact augmented pipeline workspace already made an identical root a
`~0.1 ms` lookup, but cold roots and phase seeds were too slow for the
control thread. This checkpoint asks whether background work can:

1. compute the fixed-cadence continuation states needed by the next robust
   public roots;
2. discard an obsolete policy without leaving native work in front of the
   newest policy;
3. publish only complete, exact `(policy version, root key)` results; and
4. enter a four-frame service budget after rolling reuse.

The answer is split:

- **Observed:** cooperative cancellation, bounded newest-version scheduling,
  exact specialization, and lookup-only consumption now work and pass their
  offline differentials.
- **Observed:** within one immutable policy, decisions 4 and 5 met the
  four-frame budget in all ten retained samples, while the first two cold
  decisions missed in all ten.
- **Not established:** a live Boolean policy may be replaced before this
  per-version memo reaches its steady regime. Cross-version cold start and
  physical exact-hit rate remain the actual promotion blockers.

No game process was started and no live objective or controller authority was
changed.

## Exact Decomposition

For a public-root frontier `F` and one-step cadence support `H`, define the
continuation seed set

```text
C(F) = union over root in F and action u of Phi(root, u, delay D, cadence H)
```

Every state in `C(F)` is solved under the configured fixed continuation
cadence. Seeds are sharded by exact frame residue, because fixed-cadence
descendants stay in that residue. Once all seed shards are complete:

```text
fixed-cadence continuation memos
    -> exact-compatible merge
    -> short-lived public-root workspace
    -> one-transition robust H x D labels
    -> exact root cache
    -> lookup-only consumption
```

The retained experiment requires every specialization query to add zero
continuation states. Therefore the short exact query is evidence that the
complete required continuation bank existed; it is not a hidden cold solve.

This remains one-transition cadence robustness. It does not prove survival
under recursively variable controller cadence.

## Native Cancellation And Deadlines

`native/pipeline_survival_workspace.hpp` now has:

- an atomic, permanent cancellation flag checked during state expansion,
  branch construction, and physical-step simulation;
- a per-call relative deadline, sampled every 64 abort polls and at forced
  boundaries;
- distinct C ABI results for cancellation and deadline expiry;
- continuation-only prewarm and exact-compatible memo merge entry points; and
- a branch scratch arena that reuses the branch simulations computed for
  action upper bounds instead of constructing them again during exact action
  evaluation.

A cancelled workspace is retired; it is never reset or reused. A deadline may
leave only fully computed state memo entries. Root labels are inserted only
after the whole public root is complete, so an interrupted root cannot appear
as a cache hit.

Continuation merge is allowed only when dimensions, axes, velocities, delay
support, fixed continuation cadence, clearance threshold, boundary rule, and
every clearance value are equal. Python additionally requires the same
immutable `SurvivalQueryProblem` object and policy version. Public-root
cadence may differ because it is not part of a continuation-state value.

## Newest-Version-Wins Scheduler

`scripts/touhou_control/pipeline_prewarm.py` owns one authoritative generation:

- `publish` atomically retires the prior generation, requests native
  cancellation, and gives the new version a fresh executor. Old FIFO work
  cannot remain ahead of the new version.
- `extend_seeds` accepts one rolling extension only after the previous seed
  round is complete. A busy call is rejected instead of queued.
- `submit_frontier` cancels the previous specialization batch and creates
  short-lived exact-root workspaces after all seeds are complete.
- `lookup` checks the complete current batch and exact policy version. It
  never expands a native state.
- retired handles are destroyed only after their futures have stopped, which
  avoids freeing native storage while C++ is still executing.

Every miss, incomplete batch, deadline, cancellation, or version mismatch
must fall back to the published Boolean policy plus a fresh local hard
certificate.

## Retained Validation

Artifact:
`artifacts/benchmarks/rolling_pipeline_prewarm_20260725.json`

### Correctness

- **Observed:** 256 randomized small scheduler workloads matched the
  independent scalar pending-pipeline recurrence with zero failures.
- **Observed:** five TH08-shaped fields and 25 rolling decisions matched a
  separate monolithic cadence-robust workspace for every public root.
- **Observed:** every exact specialization reported zero new continuation
  states.
- **Observed:** the pre-existing 512-seed augmented-workspace differential
  plus ten full TH08-size v1 cases were rerun after branch reuse with zero
  failures.
- **Observed:** the pre-existing 512-seed one-transition differential plus 70
  TH08-shaped phase-specialized roots were rerun with zero failures.
- **Observed:** focused tests cover cancellation before use, cancellation of
  a running native expansion, deterministic deadline expiry, exact
  continuation merge, and stale-version rejection.

### Whole Prewarm Timing

Five fields each execute five rolling decisions with `H=(4,5,6)`,
delay support `[1..6]`, and five workers. Clearance construction and oracle
queries are excluded. Frontier and continuation-seed enumeration, workspace
creation, native expansion, memo merge, and exact specialization are included
in the end-to-end deadline measurement.

| Operation | Median ms | p95 ms | Max ms |
| --- | ---: | ---: | ---: |
| Issued-action frontier enumeration | 0.278 | 0.318 | 0.361 |
| Continuation-seed enumeration | 8.894 | 12.729 | 15.771 |
| Complete preparation | 9.173 | 13.028 | 16.060 |
| Native continuation seed wall | 42.024 | 207.123 | 269.021 |
| Exact specialization | 8.205 | 10.812 | 11.057 |
| Preparation + seed + specialization | 59.125 | 228.992 | 295.904 |
| Exact lookup | 0.066 | 0.135 | 0.445 |

The four-frame budget is `66.667 ms`:

- decisions 1--2 after a fresh policy: `0/10` hits;
- decision 3: `4/5` hits; the miss was `67.086 ms`;
- decisions 4--5: `10/10` hits;
- total: `14/25` hits and `11/25` misses.

These are service-budget misses, not numeric failures. Lookup remains
fail-closed.

The Python seed enumerator originally took roughly `15--32 ms` in the
TH08-shaped probe because it repeated shared axis/action validation and
lattice rounding for every `(root, action)` request. Shared preparation and
terminal-only rounding reduced the retained median/p95 to
`8.894/12.729 ms`. This cost is now inside, not outside, the reported
end-to-end boundary.

### Stale Replacement

Five old generations were replaced 10 ms after starting:

| Operation | Median ms | p95 ms | Max ms |
| --- | ---: | ---: | ---: |
| Publish replacement | 5.265 | 5.348 | 6.312 |
| Reap cancelled generation | 0.026 | 0.027 | 0.033 |
| New generation seed ready | 213.598 | 215.378 | 272.608 |

- **Observed:** no old result was consumable after replacement.
- **Observed:** the new executor began without waiting for the old executor's
  queue.
- **Observed:** cooperative native cancellation let the retired generation
  finish before the first telemetry poll in these five cases.

## What Was Solved

The earlier `112.51/122.02 ms` phase-seed result mixed two questions. This
checkpoint resolves the scheduling part:

- Python future cancellation is no longer mistaken for native cancellation.
- Obsolete native work no longer creates a FIFO delay for the newest policy.
- A continuation phase memo can be merged without publishing an inexact root.
- Robust exact roots can be produced from the bank in roughly 8--11 ms and
  consumed in roughly 0.1 ms.
- Complete timing now includes Python root preparation.

This converts “how do we safely precompute?” into a measurable hit/miss
service with an exact fallback boundary.

## What Remains

The retained rolling workload deliberately keeps one immutable policy for five
decisions. The live controller previously measured global solve
median/p95 near `99.99/386.09 ms` and solution age `3/9` frames. It is
therefore plausible that many live versions survive only one or two control
decisions—the exact region in which this benchmark always misses.

That is not another cancellation bug. It is a **cross-version cold-start
problem**:

```text
new clearance/policy version
    -> exact memo is correctly empty
    -> cold continuation work begins
    -> newer clearance/policy arrives
    -> old exact memo must be discarded for correctness
```

Unsafe reuse across changed clearance volumes is not an acceptable fix.

The next shadow experiment should start continuation work as soon as a new
clearance volume exists, overlapping it with Boolean viability induction
before publication. It must then measure:

1. immutable policy lifetime in decisions and milliseconds;
2. seed readiness at publication and at each issue epoch;
3. exact current-version root hit rate;
4. cancelled/deadline/discarded state work;
5. Boolean publication age, local read/plan latency, action lag, and CPU
   contention; and
6. shadow action changes, with no authority on a miss.

If overlap still produces negligible current-version hits, the next algorithm
must reduce cold continuation construction or introduce a sound incremental
clearance-update certificate. It must not broaden an old exact memo's version
identity.

## Decision

Accept the cancellable scheduler, exact continuation-bank contract, and
branch-reuse optimization as offline reusable infrastructure. Keep S09
shadow-only. Do not claim that rolling exact-root delivery is solved for the
physical controller until current-version hit rate and whole-pipeline
contention are measured.
