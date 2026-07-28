# G5 Corridor-Completion Priority Experiment

Date: 2026-07-28

Status: fixed pre-implementation, default-off physical contention experiment
for CE-0152. It changes delivery scheduling only. It grants no new
finite-model, future-hazard, planner, Bomb, or physical action authority.

## Trigger And Decision

Schema-v9 Stage-4A run `20260728_083433` retained three and only three
ambiguous background-Future endpoints. All were
`corridor_future: inflight -> done`, and they were exactly the run's three
largest birth-observer materialization walls:

```text
frame 2119:  6 evidence, 5.0415 ms, 271960 cycles
frame 37349: 25 evidence, 4.2546 ms, 646576 cycles
frame 1496:  3 evidence, 1.1657 ms, 311714 cycles
```

The next-largest materialization was `0.4756 ms`; the largest sample with a
known Future inflight at both endpoints was `0.4270 ms`. Two transition rows
had ordinary-to-p95 same-bucket cycles, while one had the run-wide maximum.

**Observed:** completion transition, not evidence count or merely concurrent
solve execution, is the strongest retained correlate.

**Inferred:** the Python corridor worker's completion/Future publication
competes at a GIL/scheduler boundary. This is not causal proof and does not
exclude allocator, game, OS, or another omitted source.

**Decision:** test one existing narrow intervention: lower only the Python
corridor parent worker to below-normal priority. Do not change copy packing,
worker count, native worker limit, affinity, GC, controller priority, cadence,
publication logic, planner recurrence, or issue behavior in the same
experiment.

## Physical Problem Contract

### Objective

Reduce corridor-completion interference with the issue-thread
materialization interval while preserving timely authoritative Boolean
policy delivery and hard no-Bomb survival behavior.

### State And Observations

The robust policy state, hazard snapshot, active/held/pending input root,
delay and cadence support, route context, resources, clearance volume, action
set, and query semantics remain unchanged.

The intervention adds only explicit configuration/provenance:

```text
corridor_background_low_priority_requested: bool
background_priority_lowered on every completed CorridorSolution
```

Retrospective schema-v9 cycle/Future telemetry remains outside controller
state and cannot influence an action.

### Action And Actual Issue Semantics

The controller action alphabet, complete masks, held/no-write behavior,
pending pickup support, issue recertification, fallback, and `SendInput`
path remain identical. Bomb bit `0x02` remains forbidden.

The live option is explicit and default-off. If requested priority cannot be
applied, the physical experiment fails loud and is ineligible; it must not
silently claim the normal-priority run as an intervention.

### Uncertainty And Transitions

The finite recurrence and all nature branches are unchanged. Scheduling may
change which exact already-computed policy version is available at a later
decision. Consumers keep the existing exact context/version and freshness
checks; missing, pending, stale, or expired policies retain the current
fallback.

Lowering the Python parent does not claim to lower the native viability
worker threads. The native worker limit remains four. This separation is
intentional: the observed endpoint transition is published by the Python
ThreadPoolExecutor worker after its native solve returns.

### Horizon, Resources, Deadline, And Fallback

- one existing corridor ThreadPoolExecutor worker;
- native viability worker limit four;
- controller/game/other workers retain current priority and affinity;
- no process or thread affinity change;
- GC enabled;
- current controller cadence, corridor submit cadence, forecast lead, policy
  age limit, and issue deadlines unchanged;
- a missing/late policy follows the current live Boolean fallback; and
- stop/error cleanup releases keys and terminates the exact supervised game
  target.

## Implementation Boundary

Reuse the already-tested
`th08_corridor_runtime.solve_corridor(background_low_priority=True)` path.
That function lowers the calling Python worker once per job before native
work and retains both `background_priority_lowered` and native-worker-limit
provenance in `CorridorSolution`.

The implementation may only:

1. add one explicit controller/supervisor CLI option;
2. pass it unchanged to every corridor solve;
3. retain request/application provenance in session, configuration, corridor
   trace, and a deterministic audit; and
4. fail the experiment if any completed requested solution reports that
   priority was not lowered.

It may not alter the solver, future consumption order, submission timing,
pool reads, birth observer, planner weights, route profile, or action
selection.

## Fixed Offline Gates

Before physical use:

1. default-off argument generation remains byte-for-byte behaviorally
   equivalent;
2. explicit-on arguments reach controller, practice, and full-route entry
   points;
3. deterministic injected-solver tests prove requested true/false forwarding
   and fail-loud application checks;
4. corridor solution and trace provenance remain intact;
5. Linux and Windows focused and complete suites pass;
6. native observer parity and the schema-v9 overhead/ABBA gate remain
   unchanged; and
7. no native source or 46-symbol production ABI changes.

### Offline gate result

Implemented after this contract:

- `--corridor-background-low-priority` remains absent from default argument
  generation and propagates explicitly through the practice/full-route
  supervisors, hotkey launcher, and controller only when requested;
- every completed corridor solution is checked before publication; an
  unapplied explicit request raises and enters the existing cleanup path;
- session, controller configuration, and corridor records retain requested
  priority, applied priority, configured native worker count, and worker-limit
  application;
- `th08-corridor-priority-audit-v1` streams the raw trace and deterministically
  evaluates the application, solve/publication-age, queryability, support,
  local-plan, and action-lag gates. Re-auditing normal-priority run
  `20260728_083433` exactly reproduces its 1,791 unique solutions, solve
  median/p95/max `110.3032/308.4683/401.3608 ms`, first-observed age
  median/p95/max `2/4/1789` frames, no-query fraction `0.6843%`, queryable
  fraction `99.3230%`, local-plan p95 `17.6320 ms`, and action-lag p95/max
  `2/3`. Delivery passes and the intentionally absent priority request fails
  only the application gate;
- complete Linux and Windows suites pass `820/820` in `8.943/16.230 s`, with
  three existing Windows skips;
- fresh schema-v9 observer/ABBA reports pass all eight profiles. Linux and
  Windows interleaved p95 ratios are `1.0232` and `1.0469`; Windows retains
  `windows_query_thread_cycle_time` provenance; and
- no file below `native/` and no production ABI changed.

One first Linux complete-suite invocation saw the existing one-millisecond
native cold-expansion deadline test complete before expiry. The focused test
and immediate complete rerun passed. This was unrelated to the intervention
and was not counted as the passing gate. A subsequent test-only checkpoint
enlarged the cold reachable region from `20x20` to `64x64`; 128/128 repeated
deadline cases and fresh Linux/Windows complete suites pass.

## Fixed Physical Gates

The first explicit low-priority Stage-4A run is an intervention diagnostic.
It is eligible only when:

- accepted `route_complete`, exact executable/foreground/patch checks, hard
  no-Bomb, artifact retention, supervisor completion, and cleanup pass;
- every completed corridor solution reports
  `background_priority_lowered=true`;
- every reported native corridor solve retains worker limit four applied;
- schema-v9 validation and cycle attribution pass; and
- at least one corridor `inflight -> done` observer endpoint is retained.

The intervention is rejected immediately for priority-application failure,
Bomb, action-authority drift, malformed provenance, missing cleanup, or a
hit whose fresh exact policy reports a non-empty safe action set but issues
outside it.

For performance and delivery, all of these absolute gates are fixed:

| Metric | Required |
| --- | ---: |
| birth observer p95 | `<= 0.200 ms` |
| birth observer p99 | `<= 0.400 ms` |
| birth observer maximum | `<= 2.000 ms` |
| corridor-completion-transition materialization maximum | `<= 2.000 ms` |
| first-observed corridor age median/p95 | `<= 3 / 5 frames` |
| expired policy fraction | `<= 0.20%` of decisions |
| decision-without-query fraction | `<= 1.00%` |
| queryable policy fraction | `>= 98.0%` |
| corridor solve p95/maximum | `<= 385.6 / 500.0 ms` |
| local plan p95 | `<= 20.0 ms` |
| action lag p95/maximum | `<= 2 / 3 frames` |
| delay-support uncovered queries | `0` |

The solve p95 is the baseline `308.468 ms` plus a precommitted 25% delivery
allowance. Counts are normalized by accepted decisions so different physical
frame lengths do not manufacture a pass.

Hit count is reported but is not a one-RNG pass criterion. Every hit remains
a causal counterexample. The run is rejected for survival authority if the
canonical first hit lacks positive prior viability-exhaustion warning or
exposes a fresh viable-policy/action contradiction. Power, resources, phase,
position, and first-hit warning are retained for comparison.

One eligible passing run is only a candidate. B4 closes only after two
consecutive complete low-priority Stage-4A runs pass every fixed observer,
delivery, support, issue, no-Bomb, acceptance, and cleanup gate. Do not
repeat-select around an intervening failure.

## Interpretation And Follow-Up

- Passing transition tails with preserved publication gates supports the
  corridor-completion contention hypothesis.
- Passing tail but failing publication/viability freshness rejects the
  intervention even if aggregate hits fall.
- Remaining transition tails with ordinary cycles reject priority as an
  adequate isolation mechanism and require scheduler-native evidence or a
  different completion boundary.
- Remaining exceptional cycles require a separately fixed packed
  materialization/allocator experiment.
- A run with no transition endpoint is physically valid workload evidence
  but cannot count toward the two-pass causal intervention gate.
- The schema-v9 telemetry p95 overhead remains real. It may be optimized only
  under a separate observation-equivalence contract; it may not be
  subtracted from B4.

## Five Formal Review Questions

1. **Which histories merge?** The intervention merges no additional physical
   histories. Exact policy context/version and existing observation-compatible
   recurrence determine control equivalence; worker priority is retrospective
   delivery provenance only.
2. **Is the recurrence causal?** Yes, unchanged. The worker receives one
   immutable snapshot and no later observation. The controller consumes only
   an already-complete exact-context policy and never waits.
3. **What does an exact result answer?** The same finite robust Boolean
   problem as baseline. Priority changes availability time, not feasibility
   meaning, future-hazard completeness, or physical optimality.
4. **What falsifies the claim?** Failed priority application, changed solver
   output, stale/context-mismatched consumption, missing support, publication
   aging beyond the fixed gates, surviving observer tails, viable-policy hit
   contradiction, Bomb, or cleanup failure.
5. **Can it be consumed before issue?** Only through the existing
   lookup/age/fallback path. The physical gates measure completion age,
   queryability, local/issue timing, and action lag; late work cannot alter
   the fallback.
