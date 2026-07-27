# Stationary Witness Windows Delivery Contract

Date: 2026-07-28

Status: fixed before measurement; offline benchmark authority only

## Decision

Measure whether the internal native stationary-witness extractor can produce
a complete all-root-action publication early enough to justify a later
default-off shadow lookup experiment. Do not add a production ABI, live
consumer, or action authority in this gate.

The earlier supplemental experiments established that a fast native kernel is
not sufficient: native p95 was `1.365 ms`, while same-issue end-to-end p95
still failed at `7.054/8.139 ms` because optional work perturbed shared
execution. This gate therefore measures complete publication and four-worker
contention, not only one native function call.

## Physical Problem Contract

### Objective

Preserve no-Bomb survival by making optional exact restricted witnesses
available before a later decision without delaying the authoritative Boolean
policy, local hard certificate, or issue transaction.

This gate asks only whether delivery is technically viable. The retained
physical roots have `UNKNOWN` future-event coverage, so no delivered witness
may rank or issue an action.

### State and observations

Each job is bound to one immutable physical workload record:

```text
(canonical pipeline identity digest,
 hazard/policy/model/clock versions,
 exact float32 player root,
 active/held/pending complete masks and remaining-delay support,
 retained capsule digest,
 float32 clearance volume and lattice,
 all 36 no-Bomb complete-mask actions,
 delay support, cadence support (4,5,6), horizon 32)
```

The job receives no later observation. Different roots, capsules, float bits,
action tables, delay/cadence support, horizons, or versions cannot share a
publication.

### Actions, recurrence, and witness

Every public root action remains unrestricted. Later decisions use the exact
held desired complete-mask token as one declared stationary causal
continuation. Nature chooses every current hidden remaining delay, every new
pickup delay after a real write, and recursive cadence. Hidden branches merge
by the observation available before the next maximization.

A publication is complete only after all 36 root actions have:

- a completed label;
- a complete deterministic worst path;
- successful structural replay; and
- exact expected label parity for every retained correctness root.

No partial action set or partial path may publish.

### Workload reservoir

The fixed physical source is
`lunatic_route2_stage4a_unattended_20260728_005108`, raw trace SHA-256
`93037d9febe609accd44eb150150088c29610443783a4434328478409fee41b0`.

The deterministic reservoir is the union of:

1. the first eight accepted Boolean-empty roots in trace order; and
2. the last accepted Boolean-empty root strictly before each of the ten
   retained native hit frames.

Deduplicate by canonical identity digest and preserve trace order. A missing
capsule, invalid identity/coverage replay, query/coverage mismatch, invalid
complete mask, or horizon outside the capsule is an explicit workload
failure, not a skipped success.

The CE-0141 mixed-root rows remain rejected. The benchmark may not rewrite
the historical trace to manufacture valid roots.

### Resources and measurement boundary

The authoritative contention load is the existing deterministic
`81 x 27 x 24`, 17-action native viability problem at normal priority with
worker limit four. The optional stationary service has one below-normal
worker and at most one active job.

Completion latency begins immediately before creation of the native belief
workspace and ends after all 36 native paths are decoded into one immutable
publication record. It includes workspace construction, native extraction,
output validation, and publication locking. It excludes raw JSONL parsing,
capsule I/O, and hazard-to-clearance lowering because a future service would
consume the already-built immutable clearance/version at policy publication.
Those excluded preparation times must be reported separately.

Idle and four-worker variants use the same roots and rotate order across at
least three rounds. Report median, p95, p99, maximum, deadline status,
evaluated states, path steps, and completion ratio.

## Cancellation And Newest-Wins Semantics

Submit owns a monotonically increasing revision. Replacing a pending job
destroys it. Replacing an active job atomically requests cancellation on that
job's private workspace. The worker publishes only if:

```text
status == complete
and all 36 actions completed
and revision is still newest
and identity is still newest
```

Cancellation, deadline, invalid input, exception, incomplete output, or stale
revision publishes nothing. Lookup is nonblocking, exact-identity-only, and
never starts cold work.

The rapid-replacement test submits at least 64 older/newer pairs. It must
exercise an active cancellation rather than replacing only pending jobs.
Closing the service cancels active work, joins the worker, and destroys every
workspace before returning.

## Fixed Pass/Fail Gate

All conditions are required:

1. retained-workload construction has zero silent skip and zero missing
   capsule;
2. every completed root matches the independent Python expected label for all
   36 root actions at exact guaranteed frames and within the existing
   `1e-5` margin tolerance;
3. every publication contains exactly 36 complete paths and every path
   structurally replays;
4. under four-worker contention, at least 95% of jobs complete within the
   fixed `16.667 ms` absolute job deadline;
5. four-worker complete-publication latency is at most `8.000 ms` at p95 and
   strictly below `16.667 ms` at maximum;
6. rapid replacement produces zero stale/partial publication, at least one
   observed active cancellation, cancellation acknowledgement p95 at most
   `2.000 ms`, and maximum at most `5.000 ms`;
7. exact newest lookup returns the completed newest identity, while every
   older, altered, or missing identity lookup misses;
8. authoritative four-worker viability solve p95 regresses by no more than
   10% and throughput by no more than 10% relative to the idle-witness
   contention control; and
9. the checked-in 46-symbol production ABI remains unchanged on Linux and
   Windows.

These thresholds are fixed before building or running the benchmark. A
failure does not authorize a looser deadline or fewer authoritative workers.

## Fallback And Promotion Boundary

A pass permits only a separately reviewed, default-off, trace-only shadow
service that:

- starts from an earlier already-immutable clearance/version;
- publishes complete newest exact versions only;
- performs lookup without waiting;
- never starts cold work on the issue thread; and
- records but does not consume the witness.

Before action authority, the system still requires:

- physical future-event coverage or conservative truncation;
- CE-0141 and CE-0120 physical closure;
- exact issue-time version/root matching;
- fresh local hard intersection;
- focused shadow evidence with real completion age and no contention
  regression; and
- a strategy-ledger promotion.

A failed gate keeps the extractor internal/offline. Timeout and cancellation
remain unresolved delivery outcomes, never finite-model losing results.

## Post-Failure Resource-Isolation Variant

The first optimized Windows run passed complete publication and throughput,
but an exact repeat exposed two authoritative viability tail solves and
failed the unchanged p95-ratio condition. Before another measurement, the
next variant is fixed as follows:

- the one optional below-normal stationary worker is pinned to the highest
  logical CPU visible to the process;
- the authoritative viability caller and all four native workers retain
  normal priority, their existing affinity, and the same workload;
- process affinity, the game, sensor, issue thread, action set, recurrence,
  deadlines, and all gate thresholds remain unchanged; and
- the report must prove that thread-only affinity was applied. Failure to
  apply it fails this variant.

This is resource isolation for a proposal worker, not a reduction of
authoritative work. It was specified after observing the repeat failure and
before measuring the affinity variant.

**Observed after that measurement:** logical CPU 19 was an efficiency-class
`0` E-core and the variant failed complete-publication p95 at `12.156 ms`,
despite stabilizing authoritative viability. That exact variant is rejected.

Before measuring a second affinity variant, the selection rule is fixed to
the highest logical CPU in the maximum efficiency class returned by
`GetSystemCpuSetInformation`. On this machine that is logical CPU 11,
efficiency class `1`; CPUs 0–11 are the six SMT P-cores and CPUs 12–19 are
single-threaded efficiency-class `0` cores. All other boundaries and
thresholds above remain unchanged.

**Observed result:** the CPU-11 P-core variant passed twice. Full details,
rejected variants, report digests, CE-0142, and remaining authority gaps are
retained in `STATIONARY_WITNESS_WINDOWS_DELIVERY_GATE_20260728.md`.

## Five Formal Review Questions

1. **Which histories merge?** Only the histories already merged by the exact
   augmented recurrence for one immutable physical root. Job scheduling
   merges no roots or versions.
2. **Is the recurrence causal?** Yes for the declared stationary class. The
   worker receives no later observation, and nature branches remain inside
   each completed witness.
3. **What does an exact result answer?** It supplies an attainable lower
   witness for the retained finite model and declared stationary policy, not
   unrestricted or physical feasibility.
4. **What proves the algorithm?** Python/native label parity, complete path
   replay, all-36-action completion, cancellation tests, and exact
   publication identity. Any mismatch, partial/stale publication, or silent
   workload omission falsifies the gate.
5. **Can it be consumed in time?** Not yet. This offline Windows gate measures
   whether a later shadow experiment is justified. A later consumer must
   demonstrate real pre-issue completion age without changing cadence or
   authoritative publication.
