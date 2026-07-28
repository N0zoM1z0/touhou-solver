# G5 Birth-Observer Matched-Path Performance Contract

Date: 2026-07-28

Status: fixed pre-implementation performance-only contract.

This contract follows the capture-aligned VM-local physical run
`lunatic_route2_stage4a_unattended_20260728_110438` and the exact offline
opcode-`0x05` replay. It changes no hostile-bullet recurrence, ECL
interpretation, callback coverage, hazard geometry, planner, worker
configuration, cadence, publication, input, Bomb rule, or physical action
authority.

## Physical Question

The unchanged native birth-observer B4 limits are:

```text
p95 <= 0.20 ms
p99 <= 0.40 ms
max <= 2.00 ms
```

Run `20260728_110438` reports
`0.1038/0.2059/0.3486/0.5555/1.2276 ms` at
p50/p95/p99/p99.9/max. There is no over-budget p99 or max tail, completed
cyclic GC, or single dominant over-budget segment. The present question is
therefore:

> Which routine costs on the exact successful physical observation path
> account for the narrow p95 miss, and can they be reduced without changing
> the observation, provenance, timing boundary, or live workload?

## Retained Matched-Cohort Evidence

The following values are **observed** by regrouping the same 13,525 physical
schema-v9 rows. They do not compare different RNG runs:

| Cohort | Rows | p50 ms | p95 ms | p99 ms | max ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| zero evidence | 9,240 | 0.0912 | 0.1553 | 0.2882 | 0.6139 |
| nonzero evidence | 4,285 | 0.1493 | 0.2516 | 0.4232 | 1.2276 |
| no known future overlap | 7,622 | 0.1037 | 0.2015 | 0.3816 | 0.6985 |
| definite known future overlap | 5,902 | 0.1038 | 0.2112 | 0.2882 | 0.8924 |
| ambiguous endpoint transition | 1 | 1.2276 | 1.2276 | 1.2276 | 1.2276 |

Within the nonzero cohort, no-known-future p95 is `0.2385 ms`; definite
overlap p95 is `0.2618 ms`. Across all rows, segment p95 is
`0.0068/0.0590/0.0816/0.0749 ms` for
prepare/native-call/materialize/controller-residual.

**Inference:** nonzero materialization plus fixed telemetry is the systematic
p95 pressure. Known future overlap adds measurable pressure but does not
explain the majority of the nonzero-versus-zero gap.

**Hypothesis:** the current Windows thread-cycle bookkeeping and validated
column materialization contain avoidable Python control/allocation work.
They are candidates only because profiling identifies them; neither may be
changed semantically.

## Exact Controller Timing Boundary

The authoritative physical observation interval remains:

1. sample wall start;
2. sample `time.thread_time()` start;
3. capture the three lookup-only future states;
4. execute `NativeBulletBirthTracker.observe`;
5. snapshot native diagnostics;
6. capture the same three future states again; and
7. sample wall end.

All current work in steps 2 through 6 remains inside `observation_ms`.
In particular:

- no diagnostic construction moves after the wall end;
- no future endpoint is omitted, sampled conditionally, or copied from its
  other endpoint;
- no timing sample is subtracted from the reported wall;
- no GIL-held call becomes GIL-released;
- no controller or worker priority changes;
- GC remains enabled and the controller remains unpinned; and
- record build and emit retain their existing separate boundaries.

The thread-cycle boundaries inside the tracker remain entry, pre-native,
post-native, and post-materialization. Raw deltas remain non-negative
integers from `QueryThreadCycleTime` on Windows and explicitly unavailable on
Linux.

## First Optimization Candidate

The first allowed patch is a mechanically equivalent rewrite of
`NativeBulletBirthTracker._record_thread_cycles`:

- unpack the four already captured boundaries once;
- validate the same exact-int availability condition;
- compute the same three adjacent differences directly;
- accept only the same non-negative triples; and
- preserve the current unavailable/query-failed fallback.

It may remove transient tuples, `zip`, and generator traversals. It may not
change cycle sampling, source classification, wall timing, GC tracking, or
diagnostic schema.

Skipping `BulletBirthEvidenceBatch` validation is not part of this
checkpoint. That more invasive candidate remains blocked unless the first
patch is insufficient and a separate native-output invariant/failure gate is
fixed.

## State, Histories, And Authority

The observer state remains:

```text
(
  previous full-slot state and age,
  previous capture interval,
  current immutable pool blob and capture interval,
  maximum bootstrap age,
  native call mode,
  current GC phase/counters,
  current thread-cycle sampler
)
```

Every physical history that previously produced one
`BulletBirthObservation`, diagnostic record, and contention record must
produce byte-equivalent semantic records after the patch. Timing values and
raw cycle counts naturally differ by measurement.

There are no actions. The experiment is post-issue, trace-only, performs no
RPM, submits no work, consumes no future result, issues no input, and cannot
reclassify any future-hazard `UNKNOWN`.

## Matched-Path Benchmark And Correctness Gates

Before and after the optimization:

1. run the native GIL-held observer on Linux and Windows over the existing
   density and `1/8/32/33/592` birth profiles;
2. add an exact controller-wrapper profile that includes both future
   endpoint captures and diagnostics inside the measured interval;
3. use stable absent, done, and inflight future combinations without waiting
   on or consuming a result;
4. compare observation records, diagnostic source/status, contention
   records, and tracker continuation across identical transitions;
5. run fake-cycle cases for valid, unavailable, mixed, decreasing, and
   query-failed boundaries;
6. retain Python/native observation parity and atomic-error tests; and
7. run the complete Linux and Windows suites.

The benchmark must report p50/p95/p99/p99.9/max, evidence count, native call
mode, cycle source, and whether the full controller wrapper is inside the
timed region. A before/after claim requires identical workload counts and
gates. Cross-version Python bytecode counts are descriptive, not work parity.

## Promotion And Stop Rules

The patch remains performance-only even if all offline gates pass. One fresh
normal-priority Stage-4A physical trace is required to close B4. The fixed
physical p95/p99/max limits are not relaxed.

Stop and retain a counterexample if any of the following occurs:

- Python/native evidence or canonical record mismatch;
- tracker continuation differs after a transition;
- valid cycle deltas or source classification differ;
- future endpoint or contention classification differs;
- GC counts or phase attribution differ;
- wall work is moved outside `observation_ms`;
- callback coverage/lowering changes;
- cadence, policy age, issue lag, or worker behavior regresses; or
- a native hit, Bomb, transition, or cleanup failure occurs during the
  eventual physical gate.

Passing B4 proves only that this default-off retrospective observer meets its
declared delivery budget. It does not add future-birth geometry or reduce
hits by itself.
