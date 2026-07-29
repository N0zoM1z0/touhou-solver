# G5 Auxiliary Literal Fire-Cycle Runtime Delivery V3 Contract

Date: 2026-07-29

Status: fixed before implementation; physical authority pending

Supersedes: no evidence. Schema v4/event v1 and schema v5/event v2 remain
immutable failed delivery versions under CE-0168 and CE-0169.

## Decision

V3 corrects one conflated version boundary and one avoidable issue-loop cost:

- controller `gameplay_epoch` scopes observations but does not by itself
  invalidate an unchanged runtime ECL program identity;
- complete target instruction validation and descriptor construction occur
  before the gameplay loop;
- the visible post-identity preparation performs only a bounded
  runtime-base bind for the exact contracted target closure; and
- schema v6/event v3/preparation v2 make these semantics explicit.

All V2 replay-bundle, exact-cache, raw-oracle, empty-prefix, hard no-Bomb,
trace-only, timing, cadence, and fail-closed boundaries remain. No action,
planner, geometry, emission, source-lifetime, Power, damage, or targeting
authority is added.

## Triggering Counterexample

**Observed:** run `20260729_095849` prepared an exact accepted Stage-5 image
at controller epoch 0. All 142 selected spell-107 batches occurred at epoch
3 and failed as `runtime_identity_mismatch`; no request was lowered.

**Corrected interpretation:** the controller epoch increments on scene
resume, sensor-window discontinuity, and issue-alignment discontinuity. Those
events invalidate observation continuity and cached control evidence. They do
not assert a write to the already accepted Stage-5 instruction image.

The earlier accepted runtime-ECL identity contract already defines equivalent
program captures without `gameplay_epoch`: executable, route, difficulty,
stage, runtime base, length, relocated digest, normalized digest, and static
digest must agree. V3 follows that existing authority instead of silently
inventing a stronger lifetime rule.

## Physical Problem Contract

### Objective

Deliver independently replayable literal-fire timer-domain intents for the
fixed Lunatic Stage-5 spell-107 workload across ordinary controller
observation-epoch changes, before the next selected transaction, without
changing live action and without a measurable survival or cadence regression.

### State And Observations

Separate:

```text
program_identity = (
  executable/run identity,
  route, difficulty, stage,
  runtime_base, image_length,
  relocated_sha256, normalized_sha256, static_sha256
)

acceptance_provenance = (
  gameplay_epoch, decision_frame, snapshot_frame
)

transaction_observation = (
  current_gameplay_epoch,
  coherent native batch,
  exact raw state hashes and replay bundle
)
```

The acceptance-provenance epoch states when the one-shot program observation
was made. It is retained in every event record. A later transaction may have
a different controller epoch only when route, difficulty, native stage, PID,
runtime base, image length, and all three program digests still bind to the
same accepted program record.

Any scene transition to another native stage, process replacement, route or
difficulty mismatch, absent accepted identity, runtime-base/digest mismatch,
or selected-record mismatch remains unavailable.

### Actions And Issue Semantics

The service has no physical action. It emits one preparation record and
schema-v6 batch records only. It cannot read or write the actuator, choose a
mask, emit Bomb, change cadence, or consume a planner result.

The default schema-v3 auxiliary-batch path is unchanged when event derivation
is disabled.

### Program Preparation

Before the gameplay loop, using only the fixed static file:

1. hash and parse the exact file;
2. byte-revalidate every parsed instruction header and payload boundary;
3. construct immutable relative descriptors for the complete instruction
   closure of targets 69, 72, and 73;
4. prove every literal successor used by those targets remains in the
   retained closure or is fail-closed as unavailable; and
5. retain relative PC-to-owner membership for target validation.

After the one-shot exact runtime identity, preparation may only:

1. validate the accepted program-identity fields;
2. validate runtime-base addition and address bounds;
3. bind the prevalidated relative descriptors to that base; and
4. instantiate an empty 512-entry exact LRU.

Preparation schema v2 records:

- exact accepted runtime version and acceptance provenance;
- `program_identity_key` excluding controller epoch and acceptance frames;
- `observation_epoch_semantics=provenance_not_program_mutation`;
- prevalidated and bound instruction counts;
- cache/lowerer limits; and
- bind/total timing.

The fixed preparation maximum is `1.000 ms`. It remains post-issue and is
still charged to physical cadence; missing this tighter bound rejects V3.

### Cache And Epoch Semantics

The result-cache environment is instruction mapping/runtime base, difficulty
mask, physical-time mode, instruction limit, physical-step limit, and target
horizon. It does not include controller observation epoch.

An exact intent key may be reused across controller epochs because it includes
the complete lowerer VM/timer state and the program environment is unchanged.
Request order, source record, raw hashes, epoch, and transaction identity are
still separately retained. Cache reuse cannot merge observations or grant
source lifetime.

The independent auditor reconstructs every intent from raw bytes and executes
the independent oracle on every request regardless of cache hit/miss. It
simulates the cross-epoch LRU transitions separately.

### Uncertainty And Fail-Closed Transitions

```text
accepted program mismatch             -> unavailable
same program, any controller epoch     -> eligible observation
stage/route/difficulty/process change  -> unavailable
unknown PC/depth/marker/target         -> unknown
closure escape/unsupported opcode      -> unknown
corrupt/missing replay blob            -> audit failure
deadline/timing/cadence miss           -> delivery failure
```

Controller epoch never authorizes a program. It only ceases to reject an
otherwise exact accepted program.

### Horizons, Resources, And Timing

- target/horizon: 69/16, 72/16, 73/60 timer ticks;
- maximum instructions: 64;
- maximum physical steps: 65,536;
- cache capacity: 512;
- native visible attempts: at most three;
- replay blob: exactly 552 bytes;
- preparation maximum: 1.000 ms; and
- unchanged per-batch p95/p99/max:
  derive `0.50/1.00/3.00 ms`, compact `0.50/1.00/3.00 ms`, previous emit
  `1.00/2.00/6.00 ms`, total `3.00/5.00/15.00 ms`.

Decision-cadence p95 may regress at most one frame against the retained
schema-v3 baseline.

### Safety And Survival Acceptance

Delivery acceptance still requires route completion, hard no-Bomb, exact
cleanup, byte-identical report regeneration, and every semantic/timing gate.

The user-set handoff regression boundary adds:

- every corrected physical run is retained, pass or fail;
- no hidden repeat selection;
- at least two consecutive corrected Stage-5 runs must each have at most ten
  hits before handoff;
- phase, Power, first-hit, boundary occupancy, viability exhaustion, and
  cadence remain reported;
- a lower hit count is descriptive, not proof that a trace-only observer
  improved survival; and
- a high hit count cannot be dismissed solely as RNG.

The later complete Lunatic route and independent Stage-3 baseline must show
no obvious per-stage regression before handoff.

## Fixed Schemas And Physical Gate

- auxiliary batch schema version: 6;
- event schema: `th08-auxiliary-ecl-event-derivation-v3`;
- preparation schema:
  `th08-auxiliary-ecl-event-preparation-v2`;
- replay bundle schema remains v1; and
- report schema:
  `th08-g5-auxiliary-ecl-event-physical-gate-v3`.

Every V3 physical gate requires:

1. exactly one successful preparation before selected batches;
2. exact program identity and explicit acceptance/current epoch separation;
3. at least one nonempty batch and only a valid empty prefix;
4. all coherent native transactions and visible retry accounting;
5. all requests independently replayed complete with zero unknown;
6. exact independent cross-epoch LRU parity;
7. contracted targets only and no added event-layer process read;
8. all preparation/per-batch/cadence limits;
9. hard no-Bomb route completion and cleanup;
10. report regenerated twice byte-identically; and
11. the separately reported Stage-5 survival-regression boundary.

If all batches happen in the acceptance epoch, delivery may pass but
cross-epoch physical coverage remains explicitly unobserved. Synthetic and
retained-trace replay must still exercise at least three epoch transitions.

## Required Questions

1. **Which histories merge?** Exact intent states may share a cached result
   only under one identical program environment. Controller epoch does not
   change that environment. Observation/source histories never merge.
2. **Are uncertainty branches represented?** Yes for the timer-domain proxy:
   program/stage/process mismatch, record coherence, replay, target/depth/
   marker/PC, closure, lowerer, cache, timing, and transport all fail closed.
3. **What does an exact solution answer?** Only literal timer-domain intent
   schedules under exact accepted instructions. It does not answer physical
   birth, geometry, lifetime, damage, or safety.
4. **What falsifies it?** A program mutation accepted across epochs, closure
   escape treated complete, cache/oracle mismatch, corrupt replay, timing
   miss, action change, or hidden physical regression.
5. **Can it be consumed before issue?** No. V3 remains post-issue trace-only
   evidence. Any planner consumer needs a separate causal publication and
   physical-event contract.

## Acceptance Boundary

One delivery pass grants no planner or action authority. Cross-epoch
semantics gain physical evidence only when a passing run actually contains a
different current batch epoch. Survival stability requires the separate
consecutive-run and cross-stage evidence above.
