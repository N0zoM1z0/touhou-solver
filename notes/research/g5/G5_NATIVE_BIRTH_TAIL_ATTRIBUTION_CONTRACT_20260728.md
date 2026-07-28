# G5 Native Birth-Tail Attribution Contract

Date: 2026-07-28

Status: physical attribution complete; B4 remains failed. This contract
authorized trace-only segmented timing and cyclic-GC overlap telemetry for
one explicit-native Stage-4A run. It adds no process read, planner state,
future-hazard coverage, Bomb, input, strategy, or physical action authority.

This contract follows CE-0149 and the failed schema-v5 physical gate in
`notes/research/g5/G5_BULLET_BIRTH_PHYSICAL_GATE_20260728.md`. Native extraction passed the
physical p95/p99 limits but retained a `9.0498 ms` maximum. Ten of sixteen
over-budget observations contained no evidence, so another data-plane
optimization would be speculation without attribution.

## Physical Question

For each native retrospective birth observation, where does wall time occur:

1. wrapper validation and persistent-pointer preparation;
2. the exact C ABI call;
3. Python count validation, column copies, and observation materialization;
4. controller call/return overhead not covered by the inner intervals; or
5. a cyclic-GC collection overlapping one of the first three phases?

If no collection overlaps a tail and the native call itself is long, the
remaining alternatives include native execution preemption and operating
system scheduling. This diagnostic does not claim to distinguish those two.

## State, Observation, And Recurrence

The hostile-bullet blob, previous slot state/age, candidate recurrence,
ordered output columns, capture support, and error behavior remain exactly
those fixed in `notes/research/g5/G5_NATIVE_BULLET_BIRTH_EXTRACTION_CONTRACT_20260728.md`.
No physical histories are newly merged or split for control. The additional
diagnostic state is:

- current phase: inactive, prepare, native call, or materialize;
- three fixed generation counters for each active phase;
- wall-clock endpoints for the three contiguous inner intervals; and
- the existing controller-observed total wall interval.

A process-global GC callback is installed only after an explicit native
trace tracker is constructed. It holds no tracker while observation is
inactive. During one observation, every completed collection increments the
counter for its observed phase and reported generation `0..2`. Concurrent
or nested observations are rejected because their attribution would not be
identifiable.

The diagnostic record contains:

- prepare, native-call, and materialization wall milliseconds;
- controller residual = existing observation total minus those intervals;
- completed GC counts by phase and generation; and
- the existing total wall and quantized thread-CPU measurements.

All fields are retrospective. They do not enter the birth recurrence,
planner, policy, action score, fallback, or issue transaction.

## Information And Actuation Boundary

- Observation still begins only after current input issue.
- No timing or GC field is available to the action already issued.
- The trace consumer remains offline; live control never reads the fields.
- The callback performs no process-memory access and issues no input.
- Native extraction errors retain the existing reset and immediate
  fail-closed trace path.
- Hard no-Bomb and same-mask no-write semantics are unchanged.
- The live Boolean policy plus fresh local certificate retain all action
  authority.

## Timing And GC Semantics

The inner phases are contiguous and use the same monotonic wall clock:

1. `prepare`: tracker entry through pointer readiness;
2. `native_call`: immediately before through immediately after the C ABI;
3. `materialize`: native return through completed immutable Python
   observation construction.

The controller total starts before tracker entry and ends after return.
Residual includes controller clock calls, Python dispatch/return, and final
diagnostic publication. It must be finite and non-negative.

The GC callback counts completed collections, not collection duration.
A positive phase count proves temporal overlap with that phase. Zero does
not prove absence of allocator, page fault, native preemption, GIL handoff,
or scheduler delay. GC generation is trusted only when the runtime supplies
an integer in `0..2`; malformed callback information is ignored and may not
raise into control.

GC remains enabled. The experiment must not:

- disable or freeze cyclic GC;
- force a collection outside the measured interval to move the tail;
- pin or raise the priority of the controller;
- weaken `0.20/0.40/2.00 ms`;
- omit slow samples; or
- reinterpret thread CPU as sub-millisecond evidence.

## Validation And Publication Gate

Schema v6 must fail closed when a successful native observation omits:

- explicit native backend provenance;
- any finite non-negative segment;
- a finite non-negative controller residual; or
- exactly three non-negative integer GC counts for every phase.

Python-backend schema-v6 rows must not fabricate native diagnostics. Schemas
v1 through v5 remain auditable under their original semantics.

Focused tests must cover:

- unchanged Python/native observation parity;
- segment presence and non-negative reconciliation;
- a forced generation-0 collection counted during the native-call phase;
- inactive collections not attributed to a later observation;
- malformed schema-v6 fields rejected by the deterministic audit; and
- older-schema report compatibility.

Linux and Windows quick suites, native ABI checks, and fixed isolated
observer profiles must pass before a physical run. The physical run retains
the unchanged validation, timing, cadence, durability, no-Bomb, supervisor,
and cleanup gates.

The first Windows telemetry recheck exposed a separate benchmark defect:
the decode baseline and interleaved distributions were measured as two
non-overlapping blocks. Identical adjacent runs flipped their p95 ratio from
`1.077` to `0.940` while every observer profile passed both times. CE-0150
rejects using that block-order ratio as stable nonregression evidence.

Decode nonregression will instead use one ABBA pair per iteration:
baseline, interleaved, interleaved, baseline. Each side contributes the mean
of its two adjacent measurements before distributions and the unchanged
`1.05` p95-ratio limit are computed. This cancels first-order block drift
without pinning, discarding a sample, weakening the limit, or changing the
observer profiles. Both rejected unpaired reports remain retained.

## Decision Rule

For observations above `2.00 ms`:

- materialization tail plus overlapping GC supports allocation/GC
  correction;
- native-call tail plus overlapping GC means the callback or another Python
  thread collected while ctypes released the GIL;
- native-call tail without overlapping GC supports a scheduling/native-call
  investigation, not a Python-copy rewrite;
- prepare tail supports pointer/validation investigation;
- residual tail supports controller-boundary instrumentation; and
- mixed evidence remains unresolved and requires another narrower probe.

No single run proves that a correction reduces hits. Survival, cadence, and
input visibility remain separately reported.

## Formal Questions

1. **Control-equivalent histories:** no control state changes. Histories
   differing only in telemetry remain identical to the live policy.
2. **Uncertainty and causality:** all timing and collection values are
   observed after issue. No future or hidden branch is maximized
   separately.
3. **Physical answer:** the diagnostic can attribute observed wall intervals
   and collection overlap in the shipped runtime. It cannot identify an OS
   scheduling cause from a collection-free native-call tail.
4. **Algorithm and falsifier:** interval arithmetic is exact for the sampled
   clocks; callback counters are exact only for completed collections seen
   while a phase is active. Negative residual, nested use, malformed
   generation, missing field, or changed birth output falsifies the
   implementation.
5. **Deadline and fallback:** telemetry is trace-only after issue. Missing or
   invalid diagnostics fails the audit and leaves B4 failed; the controller
   never waits for offline analysis or consumes the result.

## Offline Gate Result

Schema v6 now records the three contiguous segments, controller residual,
and completed GC counts by phase/generation. Successful native rows require
finite non-negative reconciled fields; Python rows may not fabricate native
diagnostics. Residual-audit schema v4 reports segment distributions, GC/no-GC
wall distributions, dominant over-budget segments, and bounded exact tail
samples.

Five Linux and five Windows native tests pass, including exact observation
parity and a forced generation-0 collection attributed to the native-call
phase. Inactive collection does not leak into the next observation. Trace
and audit tests reject missing, negative, unreconciled, or backend-invalid
telemetry while retaining schemas v1 through v5.

The first two unpaired Windows reports reproduce CE-0150 at ratios
`1.0772` and `0.9398`. After the fixed ABBA correction:

| Platform/run | Full p95 ms | 592-birth p95 ms | All-profile max ms | Decode ratio |
| --- | ---: | ---: | ---: | ---: |
| Linux | `0.0118` | `0.0614` | `0.2676` | `1.0123` |
| Windows | `0.0116` | `0.0466` | `0.1598` | `1.0156` |
| Windows repeat | `0.0127` | `0.0425` | `0.6472` | `1.0248` |

All observer and paired combined gates pass unpinned. Complete
Linux/Windows quick suites pass `797/797` in `9.134/15.767 s`, with three
existing Windows skips. The physical attribution run is now eligible; B4
and CE-0149 remain failed until its evidence identifies and corrects the
tail.

## Physical Gate Result

Run `lunatic_route2_stage4a_unattended_20260728_062321` completed Stage 4A
over frames `1..45170` with 14,868 decisions, 17 hits, hard no-Bomb,
accepted artifacts, supervisor completion, and cleanup. All rows use trace
schema v6 and the explicit native backend; observation and intent errors are
zero. Validation and timed-intent gates pass. The observer budget fails only
the unchanged maximum:

| Interval | p50 ms | p95 ms | p99 ms | p99.9 ms | max ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| total observation | `0.0648` | `0.1493` | `0.2245` | `2.1568` | `8.3514` |
| prepare | `0.0021` | `0.0034` | `0.0042` | `0.0113` | `0.0703` |
| native call | `0.0365` | `0.0603` | `0.1125` | `2.1281` | `8.2585` |
| materialize | `0.0066` | `0.0771` | `0.1072` | `0.2326` | `0.7076` |
| controller residual | `0.0130` | `0.0212` | `0.0270` | `0.0707` | `0.2362` |

**Observed:** all 17 observations above `2.00 ms` have `native_call` as the
dominant segment. Their evidence counts are only
`0, 4, 10, 20, 33, 48`; no large output burst explains them. All nine
prepare/native-call/materialize generation counters total zero, so no
completed cyclic-GC collection overlapped any of the 14,868 observations.
This resolves CE-0149's requested attribution and rejects Python
materialization or cyclic GC as the next optimization target.

**Inferred:** because the exact scan normally takes only `0.0365 ms` at p50
and ctypes calls through `CDLL` release the GIL, call-boundary scheduling is
a plausible source of the collection-free wall tail. **Hypothesized:** a
GIL-held call may suppress interference from other Python threads. The trace
does not directly observe Windows scheduler or preemption events, so neither
is claimed as the physical cause.

The raw 483,475,546-byte trace remains local and ignored; SHA-256 is
`9f075f795327e6e1669b2cf18e0cfd28656a87ced1212cddf2ff3157b0dacc30`.
Two audit generations are byte-identical at canonical LF SHA-256
`c0e71b3660651e11e15e3a924bef0d1f22adc49a3513bbc7ab39b83528d3e008`.
The compact run dossier and review are retained under
`artifacts/runtime_reports/` and `notes/runs/`.

B4 remains failed. The next correction must preserve the exact C++ scan,
ordered columns, ABI, independent scalar oracle, GC, unpinned controller,
post-issue placement, and `0.20/0.40/2.00 ms` wall limits while explicitly
comparing GIL-held and GIL-released calls. It grants no future-event or action
authority.
