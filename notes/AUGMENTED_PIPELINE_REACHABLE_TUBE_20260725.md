# Sparse Augmented Pipeline Reachable Tube

Date: 2026-07-25

## Decision

Keep the published dense Boolean policy authoritative.  Add a separate,
versioned native workspace that computes lexicographic survival labels over
the exact physical-frame input-pipeline state:

```text
(frame, row, column,
 observed active action,
 older pending action or none,
 pending remaining-delay branch)
```

The workspace is a shadow research backend.  It is not attached to local
guidance and has no live input authority.  A policy-version mismatch or an
expired horizon produces no runtime result rather than reusing an old memo.

The implementation is split into
`native/pipeline_survival_workspace.hpp`, its narrow ctypes owner in
`touhou_control.native_backend`, and the game-neutral
`PipelineSurvivalWorkspace` contract in `touhou_control.query_survival`.
TH08 runtime code only attaches a workspace to one immutable
`CorridorSolution` version and exposes an explicit shadow query.

## Evidence Labels

- **Observed:** measured by deterministic differential or timing runs.
- **Inferred:** supported by those observations but not directly measured.
- **Hypothesized:** proposed live behavior that has not passed a physical
  shadow or authority gate.

## Exact Recurrence

The scalar oracle and native v1 query remain unchanged.  The new workspace
uses the same physical branch:

```text
observed active -> older pending -> newly selected
```

For each selected action, the environment chooses the worst supported new
command delay.  For a robust pending-delay support, it also chooses the worst
root.  Labels are ordered lexicographically:

```text
(guaranteed survival frames, bottleneck signed-clearance margin)
```

Every root returns the exact label for every action and the complete best
action mask.  Optimization is allowed only in non-root states where a parent
needs the maximum state value, not every dominated action's private label.

## Sound State Reduction And Pruning

### Sparse reachable tube

Top-down expansion visits only augmented states reachable from queried roots.
The memo persists across queries for the same immutable policy, so phase- and
position-nearby roots can share their future tube.  A compact 63-bit key packs
frame, cell, active action, pending action, and remaining delay.  A flat
open-addressed table stores only the state label; non-root per-action vectors
and `unordered_map` node allocations from v1 are eliminated.

An exact-root cache retains the full action-label vector.  Repeating the same
root therefore performs no branch simulation.

### Feasibility pruning

Out-of-bounds samples and non-positive signed margin terminate a branch at
the first failing physical frame.  These are the same hard feasibility
conditions as the scalar oracle.

### Pipeline canonicalization

A pending state is equivalent to no pending state when:

1. pending and observed actions have identical velocity; or
2. pending remaining delay is at least the maximum new-command delay.

In case 2 the newly selected command can never become active later than the
older pending command.  The recurrence gives the newly selected command
priority on an equal activation boundary, so the older command cannot affect
motion or the successor.  Canonicalization is exact for the current
last-write-wins model.

### Admissible action upper bound

Before recursive expansion, every action receives an optimistic label:

```text
(all remaining horizon frames, minimum margin in the current prefix)
```

An actual continuation cannot survive longer than the remaining horizon and
cannot improve a margin already encountered.  A prefix collision is already
an exact upper bound.  Therefore an action whose optimistic label is no
better than a completed incumbent cannot change the non-root maximum and is
skipped.

### Incumbent delay pruning

An action value is the minimum over delay branches.  Once a completed branch
makes that partial minimum no better than the incumbent action, unvisited
delays can only preserve or lower it.  The remaining delay branches are
skipped.  Root calls disable this optimization because the public contract
requires exact labels for every action, including dominated ones.

These proofs concern the discrete recurrence only.  They do not prove that
the clearance forecast or one-pending last-write-wins model matches every
native runtime event.

## Deterministic Evidence

Retained artifact:
`artifacts/benchmarks/augmented_pipeline_workspace_20260725.json`.

### Correctness

- **Observed:** 512 randomized scalar differentials passed with zero state
  label, per-action label, or best-mask failures.  Workloads vary phase,
  boundary clamping, decision interval, action, delay support, pending
  support, and signed-clearance geometry.
- **Observed:** ten `81 x 27 x 24`, 17-action, six-delay structured TH08
  cases matched native v1 on every root and action label with zero failures.
- **Observed:** the focused unit suite protects exact-root memo reuse, stale
  version rejection, phase offset, pending activation, and the inclusive
  successor-boundary case.

### Performance

Clearance construction and workspace creation are outside the retained query
timings.  TH08 cases reuse a workspace only inside one immutable policy seed.

| Query backend | Median ms | p95 ms | Max ms |
| --- | ---: | ---: | ---: |
| v1 independent cold query | 819.90 | 986.61 | 1052.68 |
| workspace cold/incremental root | 38.76 | 104.46 | 119.76 |
| repeated identical exact root | 0.103 | 0.128 | 0.142 |

Median evaluated/new state counts fell from `54,982` to `2,621.5`; p95 fell
from `428,069` to `6,642`.  Individual cases recorded 8,118--99,085 admissible
action-upper-bound prunes and 67--20,030 incumbent-delay prunes.

The 512 small scalar workloads measured `0.050/0.685/2.339 ms`
median/p95/max for a cold workspace query.

- **Observed conclusion:** exact augmented-state computation is no longer an
  unavoidable second-scale operation, and an already materialized exact root
  is effectively constant-time.
- **Observed blocker:** `104.46 ms` TH08 cold/incremental p95 is still too
  large for synchronous issue-time use.
- **Inferred direction:** background reachable-tube prewarming plus
  exact-root publication can move expensive expansion off the controller
  thread without weakening the recurrence.

## Limitations

1. No physical run was performed and no live objective changed.
2. The workspace models one older pending command.  Under the current TH08
   support, new-command delay is `1..6` while a normal policy interval is
   eight frames, so two pending commands do not cross a normal successor
   boundary.  The generic recurrence is not yet a proof for an arbitrary
   FIFO containing several commands whose delays all exceed one interval.
3. The memo is valid only for the exact immutable clearance volume, axes,
   action set, delay support, and policy version retained by its Python owner.
4. A warm exact-root result is useful only if frame, cell, observed action,
   pending action, and remaining-delay support still match at consumption.
5. Admissible pruning preserves the discrete oracle; it does not correct
   future-birth, transform, sensing, or collision-geometry errors.

## Next Gate

1. On the isolated survival executor, create the workspace immediately after
   Boolean publication rather than after dense losing-label induction.
2. Prewarm a small root tube from the latest native player cell, exact phase,
   observed action, and pending-delay support.  Measure neighborhood size
   versus hit rate; do not precompute the full augmented field.
3. Publish query results with both policy version and full root key.  The
   controller may consume only an exact match; a miss falls back to the
   existing Boolean plus fresh local hard certificate.
4. Collect shadow hit/miss, new-state count, cold/warm latency, policy age,
   expiry, local p95, and action-lag telemetry on the retained Stage-5
   cohorts, canonical decision 1,680, and cross-stage losing witnesses.
5. If delivery passes, try veto-only authority:

   ```text
   dense Boolean-safe
   intersect pipeline-aware winning/best set
   intersect fresh issue-time hard-safe set
   ```

   The first authority experiment may remove a dense false-winning action; it
   must not rescue a dense false-losing state.  Losing-state ranking remains
   `survival frames -> bottleneck -> control reserve -> recovery` inside the
   fresh hard-safe set.
