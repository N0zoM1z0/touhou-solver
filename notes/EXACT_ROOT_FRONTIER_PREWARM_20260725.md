# Exact-Root Frontier And Phase-Skeleton Prewarm

Date: 2026-07-25
Status: verified offline prototype; shadow-only

Follow-up: `notes/ROLLING_PIPELINE_PREWARM_20260725.md` implements the
cancellation/newest-version scheduler proposed here and includes seed
enumeration in its timing boundary. It resolves stale native backlog, but
shows that the first two decisions of each immutable policy remain cold
misses; live cross-version hit rate is still unmeasured.

## Question

The augmented pending-input workspace made an identical exact root cheap
(`~0.1 ms`) but left a TH08 cold/incremental p95 of `104.46 ms`. The live
controller cannot synchronously ask the workspace to expand an unknown future
root. The question is therefore not merely how to make lookup faster:

> How can background work begin before the next exact frame, cell, observed
> action, pending action, and remaining-delay support are known?

The answer tested here has two levels:

1. After an action is issued, enumerate the *set* of physically reachable next
   roots instead of predicting one root.
2. Before that action is known, seed the expensive value skeleton for each
   possible next exact frame. After issuance, specialize those phase shards to
   the much smaller exact-root frontier.

This prototype does not enter live guidance.

## State And Root Contract

For one immutable policy version, an exact public root is

```text
R = (
  exact frame,
  lattice row/column,
  native observed action,
  pending action or none,
  sorted remaining-delay support
)
```

The workspace identity additionally fixes the clearance volume, axes, action
set, delay support, required clearance, boundary rule, continuation cadence,
and public-root cadence support. A cached result from another identity is not
an approximate hit.

After issuing action `u` from pipeline state `S`, the next-root frontier is

```text
F(S, u) = deduplicate {
  Phi(S, u, command_delay=d, next_decision=h)
  : d in D, h in H
}
```

`Phi` applies the same last-write-wins order as the exact survival recurrence:

```text
observed action -> older pending action -> newly issued action
```

It carries a newly issued command across the boundary when `d > h`, groups
branches with the same root by remaining-delay support, and removes
out-of-bounds branches when boundary clamping is disabled. This enumeration
is kinematic only. It is not a collision certificate.

## Cadence Semantics

### Rejected unbounded form

The mathematically direct robust recurrence lets nature choose both delay and
cadence at every future decision:

```text
V(S) = max_u min_(h,d) [
  safe prefix(S,u,h,d) + V(Phi(S,u,h,d))
]
```

This is coherent, but it is not a small extension of the fixed-eight-frame
workspace. Since `gcd(4,5,6) = 1`, it fills nearly every future phase instead
of one residue class and multiplies pending/action combinations as well.

- **Observed exploratory stop:** On one retained TH08-shaped seed, fixed
  eight-frame root expansion took `126.45 ms`; new roots at frames 4, 5, and
  6 took `100.96/95.14/90.75 ms`. The naive recursively variable
  `(4,5,6)` root did not complete after more than 60 seconds and was
  terminated. This probe is `discarded/external_stop`; it is a performance
  counterexample, not a timing benchmark.
- **Decision:** Do not retain or schedule unbounded cadence branching in the
  current sparse recursive workspace.

### Retained bounded form

The implemented experimental value is robust only on the public root's first
transition:

```text
Q_root(S,u) = min_(h in H, d in D) [
  safe prefix(S,u,h,d) + V_fixed(Phi(S,u,h,d))
]

V_root(S) = max_u Q_root(S,u)
```

`V_fixed` uses the configured continuation interval, currently eight frames
for the TH08 corridor model. Each new public query again receives the robust
first transition. This is useful as a receding-horizon shadow value, but it
is **not** a proof of full-horizon survival under arbitrarily varying future
decision cadence.

The prototype support `H=(4,5,6)` is a workload hypothesis derived from the
recent controller cadence, not an accepted delay envelope. Live telemetry
must calibrate its tails before any authority experiment.

## Phase Skeleton, Then Exact Specialization

The ablation that motivated the design showed that cold cost is dominated by
the exact future-frame residue. Once a phase is populated, nearby cells and
different active/pending variants share most continuation values.

The resulting scheduler is:

```text
policy v publishes
  -> rolling phase shards seed likely cells for future exact frames
  -> controller issues action u
  -> enumerate F(S,u)
  -> route each root to its exact-frame shard
  -> materialize full per-action root labels
  -> publish (v, full root key, labels)
  -> issue thread performs lookup-only exact match
       hit  -> shadow result is available
       miss -> Boolean policy + fresh local hard certificate
```

The phase seed is not itself a result. It may warm continuation state values,
but every publishable root must still be specialized so its full action-label
vector is present in the root cache.

Separate phase workspaces were used in the experiment. This avoids the
current workspace's mutex serializing all phases and permits genuine
three-worker concurrency while preserving an immutable policy per shard.

## Implementation

- `scripts/touhou_control/query_survival.py`
  - `ReachablePipelineRoot`
  - `enumerate_next_decision_roots`
  - public-root `decision_frame_support`
  - `PipelineSurvivalWorkspace.lookup_cell`, which returns `None` on a miss
    and cannot trigger cold expansion
- `native/pipeline_survival_workspace.hpp`
  - C ABI v2 for root cadence support plus fixed continuation cadence
  - robust delay/cadence branching at public roots
  - exact-root cache-presence query
  - v1 constructor compatibility
- `scripts/benchmarks/benchmark_exact_root_frontier.py`
- retained report:
  `artifacts/benchmarks/exact_root_frontier_20260725.json`

The reusable contract contains no TH08 addresses, spell IDs, or stage
branches. TH08 actions and field dimensions appear only in the validation
workload.

## Deterministic Results

### Numeric correctness

- **Observed:** 512 randomized workloads matched the independent scalar
  recurrence with zero state-label, action-label, or best-action failures.
  They vary clearance, start phase, boundary rule, fixed continuation cadence,
  public-root cadence support, command delay, observed action, and older
  pending support.
- **Observed:** Five TH08-shaped structured fields produced 14 frontier roots
  each. All 70 phase-specialized roots matched a separately cold exact-root
  workspace. Post-specialization lookup missed zero times.
- **Observed:** A phase seed alone happened to equal zero of the 70 exact
  frontier roots. Exact specialization is necessary.

### Timing

Clearance and workspace construction are excluded. Cold roots are sequential.
Phase seeding and specialization use three concurrent phase-shard workspaces.

| Operation | Median ms | p95 ms | Max ms |
| --- | ---: | ---: | ---: |
| Cold exact TH08 root | 90.37 | 131.95 | 135.84 |
| Individual phase seed | 102.13 | 136.41 | 139.73 |
| Concurrent three-phase seed wall | 112.51 | 122.02 | 140.69 |
| Individual exact-root specialization | 5.72 | 24.95 | 26.19 |
| Concurrent post-issue frontier wall | 39.61 | 49.35 | 62.50 |
| Lookup-only exact consumption | 0.061 | 0.100 | 0.143 |

- **Observed conclusion:** If the correct phase skeleton already exists,
  action-dependent exact frontier materialization fits below 63 ms on these
  five workloads, and controller-side consumption is effectively constant
  time.
- **Observed blocker:** Phase seeding itself still has a 122 ms p95 and cannot
  reliably begin only after a decision whose next epoch may be 4--6 frames
  away. It must be rolling work begun from policy publication, and misses must
  remain normal.
- **Inferred:** The expensive/cheap decomposition is real on the retained
  workloads, but only a live shadow can measure whether rolling seeds stay
  close enough in cell/action/pending space to produce a useful exact hit
  rate.

## Safety And Failure Boundaries

1. No physical run was performed and no live objective changed.
2. `lookup_cell` is fail-closed with respect to compute: a miss returns
   `None`. The caller must then use the published Boolean policy plus the
   fresh issue-time hard certificate.
3. The one-step cadence value is not full variable-cadence robustness.
4. Frontier enumeration starts from a lattice cell. The continuous-to-lattice
   projection error is still not paid in the exact-root key or margin and must
   be certified before authority.
5. This checkpoint originally lacked cooperative native cancellation. The
   rolling follow-up adds atomic cancellation and deadlines; this item is
   retained as historical motivation, not a current implementation limit.
6. Three workers can compete with Boolean publication and local planning.
   Offline wall time does not prove side-effect-free live delivery.
7. `H=(4,5,6)` omits cadence tails until calibrated from native traces.
8. A policy version change invalidates every phase shard and exact result. The
   rolling follow-up now prevents stale backlog, but cannot make an obsolete
   exact memo valid for the new clearance volume.

## Next Experiment

This experiment was completed offline in
`notes/ROLLING_PIPELINE_PREWARM_20260725.md`. The remaining physical-shadow
experiment is:

1. Start exact continuation work when the clearance volume exists, overlapping
   Boolean induction rather than waiting for publication.
2. Measure immutable policy lifetime and current-version exact hit rate.
3. Record CPU contention, Boolean expiry, local p95, action lag, discarded
   work, and shadow action changes on retained Stage-5 cohorts.
4. Keep lookup-only exact matching and Boolean plus fresh-certificate fallback
   on every cold, stale, deadline, or root miss.

Only after useful hit rate and zero delivery regression should the existing
veto-only gate be reconsidered.
