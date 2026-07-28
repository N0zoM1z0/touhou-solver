# G5 Materialization-Tail Physical Attribution

Date: 2026-07-28

Status: retained schema-v9 physical attribution for CE-0152. The run fails
the fixed B4 wall gate. It changes no planner, worker, model, input, Bomb, or
physical action authority.

## Workload And Integrity

Lunatic Stage-4A run
`lunatic_route2_stage4a_unattended_20260728_083433` used the explicit native
`gil-held` bullet-birth observer with schema-v9 telemetry.

- **Observed:** executable SHA-256 was
  `330fbdbf58a710829d65277b4f312cfbb38d5448b3df523e79350b879213d924`;
  the no-life-decrement patch at `0x44D0FA` was active.
- **Observed:** the accepted scope is frames `1..43149`, 13,842 decisions,
  `route_complete`, 12 hits, and hard no-Bomb. The no-Bomb audit checks all
  13,842 decisions and finds no mask, flag, or action violation.
- **Observed:** the first hit is frame 4,166 after finite viability-kernel
  exhaustion at frame 3,926. All 12 contacts are classified
  `global_viability_kernel_exhausted_before_hit`. The run is not a clean
  survival sample or evidence that schema v9 improved or regressed hits.
- **Observed:** the supervisor completed artifact materialization, sent the
  post-stage no-save input, terminated the exact game target, and left no
  game, agent, or supervisor process. Auto-confirm wall pulses were automatic;
  no manual input was used.

## Schema-v9 Gate

All 13,842 successful native rows report
`windows_query_thread_cycle_time`; all three phase deltas are present.
Validation, callback lowering, timed-intent, and cycle-attribution gates pass.
No completed cyclic-GC collection overlaps any observer phase.

Observation p50/p95/p99/p99.9/max is
`0.1001/0.2039/0.3454/0.5545/5.1274 ms`. The fixed limits are
`0.20/0.40/2.00 ms`, so both p95 and maximum fail. Audit `passed` remains
false; telemetry cannot explain a wall failure into a pass.

The phase wall distributions are:

| Phase | p50 ms | p95 ms | p99 ms | p99.9 ms | max ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| prepare | 0.0039 | 0.0073 | 0.0099 | 0.0269 | 0.3477 |
| native call | 0.0361 | 0.0575 | 0.0848 | 0.3556 | 0.5239 |
| materialize | 0.0077 | 0.0814 | 0.1144 | 0.3326 | 5.0415 |
| controller residual | 0.0429 | 0.0739 | 0.1105 | 0.3701 | 0.5308 |

**Observed:** schema-v9 endpoint/cycle telemetry raises ordinary controller
residual cost relative to schema v8 and contributes to the marginal p95
failure. This diagnostic overhead stays inside the declared wall boundary
and may not be subtracted.

## Corridor-Completion Correlation

The endpoint classifications are:

- 6,092 `definite_known_future_overlap`;
- 7,747 `no_known_future_overlap`; and
- three `ambiguous_endpoint_overlap`.

All three ambiguous rows are exactly
`corridor_future: inflight -> done`. They are also exactly the three largest
materialization wall samples in the complete run:

| Frame | Evidence | Materialize ms | Materialize cycles | Corridor before/after |
| ---: | ---: | ---: | ---: | --- |
| 2,119 | 6 | 5.0415 | 271,960 | `inflight -> done` |
| 37,349 | 25 | 4.2546 | 646,576 | `inflight -> done` |
| 1,496 | 3 | 1.1657 | 311,714 | `inflight -> done` |

The next-largest materialization is `0.4756 ms` with no known overlap.
The largest definite-overlap materialization is `0.4270 ms`.

For the 1–8-evidence bucket, materialization cycles have
p50/p95/p99/p99.9/max
`192,756/315,002/386,894/513,384/569,248`. Frames 2,119 and 1,496 therefore
have ordinary-to-p95 cycle counts despite exceptional wall time. This
supports issue-thread descheduling or GIL handoff.

For the 9–32-evidence bucket, materialization cycles have
p50/p95/p99/p99.9/max
`188,962/308,584/390,238/501,876/646,576`. Frame 37,349 is the bucket and
run-wide cycle maximum, so it contains exceptional executed-thread work as
well as a long wall interval.

**Observed:** evidence count alone is again rejected. All completion
transitions correlate with the three largest tails, while merely running the
corridor future across the interval does not.

**Inferred:** the dominant mechanism is a corridor worker completion/GIL
handoff boundary, with one mixed executed-work sample. This is stronger than
the schema-v8 scheduler hypothesis but is not proof that the corridor worker
caused the operating-system scheduling decision.

**Hypothesized:** lowering only the corridor worker's priority can reduce the
completion handoff tail. It may also delay policy publication and worsen
viability freshness or survival, so it requires a separate intervention
contract and explicit publication-age gates.

## Callback Coverage

The schema-v8 fail-closed semantics remain intact: 3,444 active-main-VM rows
are complete and lowered, while 2,262 are unknown and not lowered. There are
878 incomplete rows with tagged bullets, maximum 1,360. This run does not
repair the unknown callback suffix or add future-hazard coverage.

## Evidence

- Raw trace: 477,513,549 bytes, local replay bundle, SHA-256
  `a01d0b172415b2c19759e11bfa03c68936f209827331dd8381d4bacf2232e82a`.
- Residual audit: schema v7, two deterministic generations, SHA-256
  `0b2dcad76644b90ce39c0922b5a82b41b5a09cd2c403ecd8048440c4462b9961`.
- Compact practice report:
  `notes/runs/lunatic_route2_stage4a_unattended_20260728_083433.md`.
- Compact runtime reports share the run prefix under
  `artifacts/runtime_reports/`.

## Authority And Next Gate

B4 remains open. Do not rerun-select a passing maximum and do not promote
Stage 5/6.

Before changing runtime behavior, fix a corridor-completion contention
intervention contract. The smallest existing mechanism is the already-tested
`background_low_priority` option in `th08_corridor_runtime.solve_corridor`;
the live controller currently hard-codes it false. Any explicit experiment
must:

1. change only the corridor worker's thread priority, with an immediate
   default-off rollback;
2. retain the recurrence, worker count, native worker limit, controller
   priority/affinity, GC, cadence, issue semantics, and hard no-Bomb rule;
3. prove priority application and retain it in solution/session/trace
   provenance;
4. measure solve completion time, first-observed age, policy age, expired and
   unavailable queries, observer wall tails, endpoint transitions, local
   latency, and action lag;
5. reject the intervention if publication freshness, viable-query coverage,
   or first-hit warning degrades materially; and
6. require two consecutive complete physical B4 passes before closing the
   performance regression.
