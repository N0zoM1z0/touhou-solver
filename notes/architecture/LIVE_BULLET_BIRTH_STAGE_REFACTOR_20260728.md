# Live Bullet-Birth Stage Refactor

Date: 2026-07-28

Status: behavior-preserving structural checkpoint with Linux/Windows tests,
deterministic trace-audit regeneration, and one supervised Hard Stage-1
physical retention workload complete. No sensing model, ECL interpretation,
future-hazard authority, recurrence, planner, action selection, cadence,
Bomb policy, trace schema, or strategy authority changed.

## Boundary Extracted

`scripts/th08_live/bullet_birth_stage.py` now owns one optional,
action-neutral post-issue diagnostic transaction:

1. observe the bounded deferred-fire state from already captured enemy/ECL
   guards;
2. bracket the bullet-pool observer with the three existing worker-future
   endpoint observations;
3. run the configured Python or native bullet-birth observer and reset the
   tracker on a known observation failure;
4. optionally observe derived-pattern sources;
5. optionally run the active-spell main-VM birth-intent lookahead;
6. construct the existing bullet-birth trace record and timing fields; and
7. publish exactly one row with the historical failure-triggered flush policy.

The immutable `BulletBirthStageRequest` carries only already captured state
and explicit version/provenance fields. `BulletBirthStageDependencies`
preserves the controller's current monkeypatch and backend seams by injecting
the live callbacks and clock functions on every call. The result returns the
published record, measured emit time, and diagnostic errors.

The controller still owns:

- the physical action transaction and all actuator state;
- capture, issue, gameplay-epoch, session, and resource lifecycle;
- creation/reset of the observer services;
- the previous-emit chain across iterations and its discontinuity reset;
- worker-future ownership and cancellation;
- all remaining post-issue shadows and the outer decision trace; and
- every stop/error key-release path.

This is a behavior-owning stage extraction, not a new physical authority.

## Preserved Ordering And Failure Semantics

- The stage is invoked only after physical send/no-write, at the same point
  as the removed inline block.
- Deferred-fire observation remains first.
- Worker future state is sampled immediately before and after the birth
  observer. No observer clock is sampled when the tracker is absent.
- Native diagnostics are read only after a successful native observation.
- Derived-source observation remains after birth observation and before ECL
  intent analysis.
- The lookahead still uses the controller's current
  `ECL_BIRTH_LOOKAHEAD_FRAMES`, difficulty bit, deferred-fire state, and
  fail-closed unresolved geometry/origin/resource arguments.
- The known observation and intent exception sets are unchanged. A birth
  observer failure still resets its tracker and forces an immediate trace
  flush; failed diagnostic rows are not silently dropped.
- `timing_ms.build`, `pre_emit_total`, and `previous_emit` retain their
  historical definitions. The controller stores the returned measured emit
  duration for the next row.
- Python/native backend identity and native GIL call mode remain explicit
  record fields. The stage has no action consumer.

## Automated Validation

Focused stage tests prove:

- exact deferred/future/observer/derived/intent/build/emit order;
- immutable issue/snapshot/epoch/stage identity propagation;
- explicit lookahead-horizon and previous-emit propagation;
- observation, derived, intent, build, and pre-emit timing accounting;
- observer failure reset plus failure-row flush;
- absent-tracker contention bracketing without an observation CPU clock; and
- native and derived diagnostics reach the trace input in order.

Focused Ruff and `git diff --check` pass. Complete discovery passes:

- Linux: 949 tests in 10.218 seconds;
- Windows UNC: 949 tests in 17.505 seconds, with three existing platform
  skips.

The deterministic v9 bullet-birth audit was generated twice from the physical
raw trace and was byte-identical both times:

- SHA-256:
  `459ef12077391415e15953e6822191bf916b332ffa56df48461ec6069b043939`.

## Physical Retention

Supervised run `hard_route2_stage1_unattended_20260728_205207` completed:

- frames `1..20448`;
- 7,401 decisions;
- zero native hits;
- lives `8.0..8.0` and Bombs `3.0..3.0`;
- hard no-Bomb;
- `route_complete`;
- accepted session/artifact gates;
- exact key release and identity-scoped game-process cleanup; and
- no residual game, controller, or supervisor process.

The action policy and physical model did not change. Zero hits is useful
structural smoke evidence, not causal evidence that moving the trace block
improved survival.

The strict residual audit reports:

- 7,401 audit rows and 7,401 decision scopes;
- trace schema v9 for every row;
- native backend and `gil-held` call mode for every row;
- zero observation, intent, or derived-source errors;
- complete Windows thread-cycle attribution for all 7,401 rows;
- one absent `previous_emit` on the first row and 7,400 measured successors;
- observer p50/p95/p99/max
  `0.0887/0.1743/0.3295/0.7970` ms;
- accepted observer limits p95/p99/max `0.2/0.4/2.0` ms;
- pre-emit p50/p95/p99/max
  `0.1444/0.2863/0.4298/0.9835` ms; and
- `validation_passed`, `observer_budget_passed`, and overall `passed`.

The audit still declares future-geometry, hazard-coverage, causal, and
physical-action authority as none. Its 1,654 temporal-support joins and
10,643 unmatched activation edges remain trace evidence, not solved
future-bullet geometry.

The replay-capable raw trace remains local and ignored:

- bytes: `178496273`;
- SHA-256:
  `de92777b5d6745972b5ad3c489e351859bd87ba713257b25a053200b76f3efef`.

Retained compact hashes:

- session:
  `0d26170a6bb831f760c98bf62611a2b1583391f6be95a269b67207f766405351`;
- summary:
  `11df2d3ab7d9bd7d9f3af9def3f88e1ddd5468ca5397a76b57244e5d29f449bf`;
- birth audit:
  `459ef12077391415e15953e6822191bf916b332ffa56df48461ec6069b043939`.

## Structural Result And Next Work

Removing the historical inline block reduces
`scripts/th08_live/controller.py` from 4,751 to 4,554 lines. The 350-line
stage now has one request/result boundary and independent tests. The controller
is still too long; this checkpoint does not declare the decomposition done.

The next research checkpoint returns to immutable shipped-runtime ECL
identity, because better future-birth planning requires proving that the
captured instruction image and VM source really correspond to the executing
game state. In parallel with that research sequence, the next controller
extraction should characterize a complete remaining post-issue shadow or
outer-trace ownership boundary before moving it. Small blocks will not be
moved merely to reduce line count, and `_run_live_session` will not be
relocated wholesale into another monolith.
