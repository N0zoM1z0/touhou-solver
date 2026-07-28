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

## Matched-Path Baseline Checkpoint

Benchmark schema v8 now measures the exact controller wrapper separately
from the core observer. It uses one persistent blob owner, toggles only the
declared active slots outside the timed interval, and covers
`1/8/32/33/592` activation edges under absent, done, and inflight future
states. The reported wall contains `thread_time` start, both future endpoint
captures, native observation, and diagnostic snapshot exactly as declared.

All 23 core/controller profiles and the interleaved decode gate pass on
Linux and Windows. The largest controller-path p95 is `0.06643 ms` on Linux
and `0.04872 ms` on Windows. These offline values are far below the physical
`0.2059 ms` p95 and therefore characterize implementation floor only; they
cannot close B4 or reproduce game/worker/OS contention.

The retained reports are:

- `artifacts/benchmarks/bullet_birth_observer_native_linux_matched_baseline_20260728.json`,
  SHA-256
  `7caf09e8807b03b19cd341b752b112a31bc78cfa30b4404d880bec81de418654`;
  and
- `artifacts/benchmarks/bullet_birth_observer_native_windows_matched_baseline_20260728.json`,
  SHA-256
  `d89e0497a54ca20ea8df69f52c7b5181d1a2be47475aa29728e2536bb13893ca`.

Complete Linux/Windows suites pass 850 tests; Windows retains three existing
platform skips. Production remains unchanged. The first optimization
candidate and fresh physical requirement are unchanged.

## Cycle-Delta Optimization Checkpoint

`NativeBulletBirthTracker._record_thread_cycles` now directly unpacks the
four existing samples and computes the same three adjacent differences. It
preserves exact-int checks, non-negative validation, Windows/query-failed/
unavailable source classification, and the three-value diagnostic record.
It removes only transient generator, `zip`, and conversion work.

Focused tests now explicitly cover valid, decreasing, mixed-availability,
and unsupported-source boundaries. A diagnostic Windows 4,000-observation
profile falls from 268,076 calls / `0.406 s` to 188,056 calls / `0.219 s`;
the `_record_thread_cycles` cumulative profile attribution falls from about
`0.054 s` to `0.004 s`. Profiler totals are attribution evidence, not
acceptance timings.

The complete schema-v8 benchmarks pass all 23 profiles after the change:

- Linux maximum controller-path p95 is
  `0.06643 -> 0.06603 ms`, as expected for a non-Windows cycle source;
- Windows maximum controller-path p95 is
  `0.04872 -> 0.04680 ms`; and
- an independent Windows optimized repeat reports `0.04410 ms`.

The retained optimized reports have SHA-256 values:

- Linux:
  `9e7e45cfbc1bb92cfb044866e736f68e917be167c74a96e046f26d6a0f040235`;
  and
- Windows:
  `d0f9bbca41ccc210e3fbe80db914c7465f120080564f4f5441ac6d5fe4c3dbd1`.

Ruff and complete Linux/Windows suites pass 850 tests; Windows retains three
existing skips. The improvement is similar in scale to the physical
`0.0059 ms` p95 miss, but offline timing cannot establish the result under
game/worker contention. B4 remains open pending one fresh unchanged
normal-priority Stage-4A trace.

## Fresh Physical Gate And Static-Mapping Correction

Fresh normal-priority GIL-held Stage-4A run
`lunatic_route2_stage4a_unattended_20260728_121028` completed frames
`1..44270` over 14,066 decisions with hard no-Bomb, accepted route
completion, key release, supervisor/game cleanup, and no residual process.
All rows retain schema-v9 native/GIL-held provenance.

The optimization improves the fixed physical percentile but does not close
B4:

- observation p50/p95/p99/p99.9/max is
  `0.0983/0.1986/0.3400/0.5439/8.3269 ms`;
- prepare/native/materialize/controller-residual p95 is
  `0.0071/0.0593/0.0852/0.0675 ms`;
- frame 11969 spends `8.2328 ms` of `8.3269 ms` in materialization for four
  evidence rows while its materialization cycle count is ordinary for that
  cohort; and
- frame 38043 spends `4.9519 ms` of `5.0455 ms` in materialization for 48
  evidence rows, has the run-wide maximum materialization cycle count
  (`681916`), and coincides with a corridor Future
  `inflight -> done` transition.

No completed GC overlaps either tail. The first row supports external
descheduling/contention; the second supports a mixture of executed work and
Future-completion/GIL handoff. Neither identifies one removable owner.
Therefore the fixed p95/p99 limits pass but the `2.00 ms` maximum fails.
B4 remains open. The rejected corridor-priority intervention stays rejected.
Dropping native-output validation or moving work outside the measured
interval requires a separate invariant/failure contract; process isolation
requires its own causal delivery experiment.

The same run has ten physical contacts at
`[4280, 11544, 12158, 12645, 13476, 22354, 22941, 37188, 38358, 43150]`.
All follow global viability exhaustion. This is descriptively fewer than the
immediately preceding projection run's 14 contacts, but earlier same-stage
GIL-held evidence includes a nine-contact run. RNG, phase timing, density,
and post-death resources differ, so there is no survival-regression or
improvement claim.

The VM projection audit passes all 5,663 callback rows. Static control replay
encounters its first decoded-file/runtime-image mismatch at frame 44212.
Because the trace retained neither raw instruction bytes nor a replacement
image identity, the auditor now invalidates that static mapping for every
later callback row. It conservatively excludes 27 late spell-73 rows, reports
no `unknown -> complete` transition, and still fails its all-rows and
no-unknown-exclusion gates. This is a correction to evidence accounting, not
additional ECL coverage.

Evidence SHA-256 values are:

- raw local JSONL:
  `e15fc270fdb2afe188987aa8f22798f36cbc6da8e07192a2c4af0aed132fe43d`;
- birth audit:
  `c4a715c0e50f6af8b0d712cfe36ae1a2697173aec49369b3dd93601b91382e9d`;
- projection audit:
  `bf3126b0259e2a9a0e60238fe843cf731cc6e4043db796b1ac6bda2bc2ae964d`;
  and
- corrected static control audit:
  `b8b8695fcf710c693201a87ecb99840c33e569fbf68e8236653e7b213142d839`.

The three compact audits regenerate byte-identically. This checkpoint changes
neither live callback interpretation nor action authority. Ruff and complete
Linux/Windows suites pass 851 tests in `9.398/16.771 s`; Windows retains three
existing skips.
