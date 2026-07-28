# G5 Auxiliary Literal Fire-Cycle Runtime Delivery Contract

Date: 2026-07-28

Status: implementation-complete and synthetic-gate-ready; physical delivery
authority pending one supervised Lunatic Stage-5 spell-107 trial

## Decision

The first auxiliary literal-fire event class may enter a default-off
post-issue trace only through schema v4. It consumes the already selected
coherent auxiliary-VM batch, adds no process-memory read, requires the exact
accepted runtime-ECL version from the same gameplay epoch, retains raw replay
state, and never changes an action.

This contract grants no future geometry, source-lifetime, realized-birth,
hazard-envelope, viability, planner, publication, targeting, Power, damage,
or actuator authority.

## Physical Problem Contract

### Objective

Measure whether the offline timer-domain event lowerer can be delivered under
real game contention without corrupting cadence or losing enough evidence to
replay every conclusion independently. The physical survival objective and
hard no-Bomb controller remain unchanged.

### State and observations

One delivered event batch is keyed by:

```text
(executable identity,
 route/difficulty/stage,
 gameplay epoch,
 accepted runtime ECL base/length/digests and identity frame,
 selected coherent auxiliary batch and all visible retry attempts,
 selected manager frame,
 owner/context identity and status,
 target subroutine and call depth,
 exact active VM and saved-frame bytes)
```

The exact accepted version exists only after the one-shot runtime image
observation reports `exact_match`. A byte mismatch, failed capture, different
epoch, stage, difficulty, normalized digest, or image length is unavailable,
not approximately compatible.

Two histories are not delivery-equivalent if any field above differs. Heap
pointer equality is not source identity. A hash proves byte equality only
when the raw bytes retained beside it reproduce that hash.

### Actions and issue semantics

The service has no action. Controller issue completes before the existing
auxiliary batch capture and event derivation. Schema v4 is enabled only by
`--trace-auxiliary-ecl-events`, which itself requires:

- `--trace-auxiliary-vm-batches`;
- one static image and immutable SHA-256;
- Lunatic difficulty;
- Stage 5; and
- the unchanged hard no-Bomb live path.

Default execution stays schema v3 and retains hash-only compact records. It
does not pay raw replay serialization or event lowering.

### Uncertainty and transitions

The runtime service does not create a new recurrence. It applies the
previously contracted deterministic literal-path transition only after:

1. the native-owned bounded retry selects one coherent batch;
2. exact runtime image identity is accepted;
3. raw VM state validates;
4. call depth is zero;
5. target is one of Stage-5 subroutines 69, 72, or 73;
6. the scheduler marker agrees with raw state; and
7. the active PC belongs to the declared target subroutine.

Any failed predicate is explicit `UNKNOWN` or unavailable. Unsupported
requests do not enter canonicalization. A completed request maps to exactly
one retained unique result, and the request-order mapping is preserved.

### Horizon and resources

- Target timer horizons are fixed at `69:16`, `72:16`, and `73:60`, covering
  two literal cycles for each target.
- The walker limit remains 64 instructions per unique request.
- Time scale is deliberately absent. All physical-frame offsets remain
  unavailable; only exact timer-domain offsets are delivered.
- The event service receives Python objects, not a process reader. Its added
  RPM count is structurally zero.
- Raw runtime JSONL remains ignored. Compact physical audit reports are the
  only tracked run evidence.

### Safety invariants and fallback

- Schema-v4 authority is always `trace_only_no_action_authority`.
- Missing identity cannot fall back to static-path guessing or an old
  gameplay epoch.
- `UNKNOWN` cannot mean no event or safe.
- The live hazard set, viable set, candidate ordering, input mask, cadence,
  and Bomb policy are unchanged.
- Native transaction failure, retry exhaustion, identity miss, invalid state,
  unsupported path, or audit mismatch leaves the current Boolean policy plus
  fresh local hard certificate unchanged.
- The controller never performs cold path expansion or replay verification
  on behalf of an action consumer.

## Delivery Architecture

Responsibilities remain outside the 4,000-line controller:

- `th08_live.runtime_ecl_identity` publishes one immutable accepted-version
  object only after exact byte identity;
- `th08_live.auxiliary_vm.trace_service` owns cadence, visible retry,
  selected-batch serialization, and the schema-v3/v4 boundary;
- `th08_live.auxiliary_vm.event_service` owns exact-version matching,
  PC-owner validation, request construction, lowering, and compact event
  output;
- `analysis.auxiliary_ecl_event.physical_replay` owns independent raw-state,
  hash, classification, canonicalization, and raw-byte-oracle replay; and
- `analysis.auxiliary_ecl_event.physical_report` owns fixed workload,
  session, cadence, timing, and authority gates.

The live controller only constructs these services and passes the accepted
version. The event layer has no process-reader parameter.

An import-order regression found during focused testing showed that exporting
the live service through `auxiliary_vm.__init__` created a cycle through the
game-neutral lowerer. The correction keeps the event service an explicit
submodule and makes trace delivery depend on a narrow Protocol. This is an
observed software dependency failure and its retained regression test, not
physical evidence.

## Replay Contract

Every schema-v4 selected observation includes:

- `active_vm_hex` and its SHA-256;
- every saved-frame hex payload and SHA-256;
- original record identity/status fields;
- the exact accepted runtime-version record;
- one event request per usable record in capture order; and
- canonical unique results plus one result index per lowerable request.

The strict auditor independently:

1. rechecks the complete shipped ECL SHA-256 and length;
2. revalidates the physical one-shot identity row;
3. revalidates native retry/read-count/coherence semantics;
4. hashes every retained active VM and saved frame;
5. decodes PC/timer/marker directly from raw bytes;
6. reconstructs PC-to-subroutine ownership from the exact ECL;
7. reproduces every fail-closed classification;
8. reconstructs the expected canonical mapping; and
9. runs the structurally independent raw-byte oracle for every accepted
   request.

The auditor does not import the production transition/lowerer. Its parity
comparison covers event/transform addresses and timer offsets, instruction
count, stop reason, horizon completeness, and physical-timing status.
Descriptor-field decoding remains covered by the accepted offline independent
tests; the physical gate does not claim realized emission semantics.

## Fixed Physical Gate

Workload:

- Sakuya/Remilia route 2;
- Lunatic Stage-5 practice;
- spell ID 107 filter;
- hard no-Bomb;
- batch cadence 16 changed manager frames;
- native call mode `gil-held`;
- exact `artifacts/decoded/ecldata5.ecl`, 47,224 bytes, SHA-256
  `3148f45faf78bd8211a956edcdc353be73d2781995d3dadd36bdca8132f8fe19`;
  and
- the accepted schema-v3 spell-107 run as cadence/read-cost baseline.

Every gate must pass:

- accepted session, route completion, cleanup, and zero Bomb decisions;
- exactly one accepted runtime-ECL identity;
- schema-v4 batches present and all native selected transactions coherent;
- every selected batch bound to the exact same accepted runtime version;
- all usable records replayable;
- all requests limited to targets 69/72/73 and independently oracle-equal;
- zero unresolved request in this focused workload;
- reported process reads equal the visible native-attempt sum;
- decision-cadence p95 regresses by at most one frame; and
- fixed p95/p99/max milliseconds:

| Phase | p95 | p99 | max |
| --- | ---: | ---: | ---: |
| event derivation | 0.50 | 1.00 | 3.00 |
| replay-state compacting | 0.50 | 1.00 | 3.00 |
| preceding synchronous trace emit | 1.00 | 2.00 | 6.00 |
| selected native transaction plus derivation/compact | 3.00 | 5.00 | 15.00 |

The preceding-emit field is absent only on the first batch. A timing failure
retains useful semantic evidence but rejects delivery acceptance; limits do
not change after seeing the run.

## Required Questions

1. **Which histories merge?** Only histories with the complete immutable ECL
   version and identical captured request state merge for the current
   timer-domain intent. Owner/source histories remain distinct unresolved
   dependencies.
2. **Are all uncertainty branches represented?** Every unsupported identity,
   context, target, depth, state, PC-owner, or lowerer result becomes
   unavailable/`UNKNOWN`; no hidden branch is optimized separately.
3. **What does an exact solution answer?** It answers only the timer-domain
   literal intent schedule of the observed auxiliary VM. It does not answer
   whether bullets are emitted, survive, transform, hit, or should affect an
   action.
4. **What falsifies the algorithm?** Any raw hash mismatch, version mismatch,
   request-order or canonical-map mismatch, raw-byte oracle mismatch,
   unsupported context reported complete, extra read, deadline failure, or
   cadence regression.
5. **Can it be consumed before issue?** No. It is deliberately post-issue and
   trace-only. Any future consumer requires a new versioned delivery,
   causality, geometry, containment, and deadline contract.

## Promotion Boundary

One passing physical run accepts replay-capable action-neutral delivery for
this exact workload. It does not justify planner consumption. A later gate
must separately establish owner/source lifetime, deferred/immediate emission,
dynamic parameter resolution, shared transform state, realized birth,
geometry, and conservative hazard coverage.

Lunatic Stage 3 remains a separate later workload. It starts from a new
Power-0 baseline and needs its own target/source inventory; Stage-5 ECL
subroutines, target mix, timing, and strategy do not transfer.

## Pre-Physical Verification

- exact-version and event-service tests: 9 passed;
- auxiliary-VM trace-service family: 27 passed;
- strict physical replay/report tests: 5 passed, including forged raw hash,
  production result, runtime base, and static digest rejection;
- Linux quick discovery: 1,011 passed in 11.843 seconds;
- Windows UNC quick discovery: 1,011 passed in 19.660 seconds with three
  existing skips; and
- Ruff passes over every changed production, analysis, automation, and test
  file.

## Physical Disposition

The fixed schema-v4 gate was executed on 2026-07-29 and failed. Exact
transport/version/raw-byte replay passed for all 3,830 requests, while six
initial zero-context rows failed the all-success status gate and event
derivation, replay compact maximum, and synchronous emit timing missed their
fixed limits. The thresholds and result are not revised.

See
`G5_AUXILIARY_LITERAL_FIRE_CYCLE_RUNTIME_DELIVERY_STAGE5_RESULT_20260729.md`
and CE-0168. A corrected delivery requires a new contract and physical run;
this contract grants no physical delivery authority.
