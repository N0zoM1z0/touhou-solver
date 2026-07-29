# G5 Auxiliary Literal Fire-Cycle Runtime Delivery V4 Contract

Date: 2026-07-29

Status: fixed before implementation; physical authority pending

Supersedes: no evidence. Schema v6/event v3 remains the immutable CE-0170
physical failure and the first observed cross-epoch semantic delivery.

## Decision

V4 removes independently reconstructible JSON duplication without removing
raw replay evidence:

- only usable native records are projected, each with its exact source index;
- omitted selected records are proved `NULL` through the native status
  histogram and successful transaction contract;
- full active/saved VM bytes remain in the hash-addressed replay bundle;
- request classification is a narrow source-index/status/result-index
  projection;
- production lowering is committed by ordered canonical result hashes and
  result indices; and
- the event decoder uses only the exact timer fields consumed by this proxy.

Schema v7/event v4 keeps preparation v2 and every V3 program-identity, epoch,
cache, replay, empty-prefix, timing, cadence, hard no-Bomb, cleanup, and
survival boundary.

No action, planner, geometry, physical-time, source-lifetime, damage, Power,
targeting, or emission authority is added.

## Triggering Counterexample

**Observed:** V3 run `20260729_104222` delivered all 3,384 requests exactly
across program epoch 0 and observation epoch 2, but failed:

```text
event derive p95     0.620 ms > 0.500 ms
replay compact p95   0.564 ms > 0.500 ms
previous emit p95    2.862 ms > 1.000 ms
hits                 11       > 10
```

Batch JSON line p50/p95/max was `66080/92142/97166` bytes. Up to 164 selected
records were serialized although at most 34 carried usable replay state.
State decode also constructed a complete VM-local projection even though the
literal timer-domain recurrence never reads it.

## Physical Problem Contract

### Objective

Deliver the same independently replayable literal-fire timer-domain intents
for the fixed Lunatic Stage-5 spell-107 workload before the next selected
transaction, under one exact program across controller epochs, with no action
change, while meeting every unchanged delivery/cadence/survival gate.

### State And Observations

The model state consumed by this proxy is:

```text
timer_state = (
  instruction_pointer,
  timer_previous,
  timer_fraction_bits,
  timer_elapsed,
  timer_tick_horizon
)

source_provenance = (
  native selected-record index,
  owner slot, auxiliary index,
  target, call depth, scheduler marker,
  exact full raw VM and saved frames
)
```

The literal lowerer does not resolve VM locals. Dynamic parameters remain
explicit dependencies/unknowns in the intent result. Different raw local
histories are not merged as observations: their full bytes, hashes, source
indices, and request rows remain distinct. They may share only the same
unresolved timer-domain result under the already declared exact intent key.

### Usable-Record Projection

For one successful selected native transaction:

1. retain the attempt count, selected attempt, total record count, exact
   `record_status_bits` histogram, owner/context/coherence frames, read
   counts, and payload bytes;
2. project every and only `RecordStatus.OK` record;
3. attach its strictly increasing unique `source_record_index` in
   `[0, record_count)`;
4. retain all existing pointer/owner/target/depth/marker fields and exact
   active/saved-state hashes;
5. retain every unique referenced 552-byte state in the replay bundle; and
6. require every omitted record to be accounted for as `RecordStatus.NULL`.

Any other selected-record status, count mismatch, duplicate/out-of-range
source index, missing state, hash mismatch, or bundle mismatch fails closed.

This projection is lossless for the declared event recurrence and native
coherence audit. It does not assert that null contexts never matter to a
future source-lifetime model.

### Result Commitment

For each request, event v4 retains:

```text
(source_record_index, classification_status, result_index)
```

For each unique production result it retains SHA-256 of a fixed canonical
recurrence core:

```text
json.dumps(
  {
    events: [
      (timer_tick_offset, physical_frame_offset,
       instruction_address, opcode, parameter_mask)
    ],
    transforms: [
      (timer_tick_offset, physical_frame_offset,
       instruction_address, index)
    ],
    instructions_scanned,
    stop_reason,
    horizon_covered,
    requested_timer_tick_horizon,
    stop_timer_tick,
    physical_timing_status
  },
  sort_keys=True,
  separators=(",", ":"),
  allow_nan=False
).encode("utf-8")
```

The commitment also retains request count, unique-result count, and the
complete ordered result-index vector. Result commitments are cached only for
the lifetime of the same immutable program/lowerer environment.

The independent auditor reconstructs every request from raw bytes, executes
the independent raw-byte oracle regardless of production cache status,
reconstructs the complete canonical recurrence cores, and compares every
hash and index. This commitment deliberately excludes descriptive fire
arguments and transform literals that the independent oracle does not
reconstruct and this proxy does not consume. Those fields gain no authority
from V4; the exact VM and ECL bytes remain retained for a future richer
oracle. A hash match is implementation-parity evidence for the declared
recurrence on the retained raw input, not physical-model validity.

### Actions, Uncertainty, And Transitions

There is no physical action. All V3 fail-closed transitions remain:

```text
program/stage/route/difficulty mismatch -> unavailable
native transaction incoherence          -> unavailable
projection/count/source mismatch         -> audit failure
unknown PC/depth/marker/target            -> unknown
unsupported opcode/closure escape         -> unknown
raw bundle/hash/commitment mismatch        -> audit failure
deadline/timing/cadence miss               -> delivery failure
```

Controller epoch remains provenance, not program mutation.

### Timing And Size Gates

Unchanged physical limits, in milliseconds:

- preparation maximum: `1.000`;
- event derive p95/p99/max: `0.50/1.00/3.00`;
- replay compact p95/p99/max: `0.50/1.00/3.00`;
- previous synchronous emit p95/p99/max: `1.00/2.00/6.00`;
- total transaction p95/p99/max: `3.00/5.00/15.00`; and
- decision-cadence p95 regression: at most one frame.

The isolated transport gate additionally fixes:

- projected JSON line maximum: `24576` bytes;
- no-write JSON serialization p95/p99/max:
  `0.25/0.50/1.50 ms`; and
- at least three controller epoch transitions under one exact program.

These isolated limits do not replace the physical limits.

### Safety And Survival

- hard no-Bomb;
- route completion and exact cleanup;
- no change to live action or cadence;
- every run retained, pass or fail;
- at least two consecutive corrected Stage-5 runs at no more than ten hits;
  and
- later complete Lunatic and independent Stage-3 checks with no obvious
  per-stage regression.

## Fixed Schemas

- auxiliary batch schema: 7;
- event schema: `th08-auxiliary-ecl-event-derivation-v4`;
- observation projection:
  `th08-auxiliary-vm-usable-record-projection-v1`;
- lowering commitment:
  `th08-auxiliary-literal-fire-result-commitment-v1`;
- preparation schema remains:
  `th08-auxiliary-ecl-event-preparation-v2`;
- replay bundle remains:
  `th08-auxiliary-vm-replay-bundle-v1`; and
- physical report:
  `th08-g5-auxiliary-ecl-event-physical-gate-v4`.

## Required Questions

1. **Which histories merge?** Only exact timer states under one immutable
   lowerer environment share an unresolved result. Raw observations and
   source histories remain distinct and replayable.
2. **Are uncertainties represented?** Yes for this timer proxy: version,
   epoch provenance, native coherence, omitted-status proof, source mapping,
   raw bytes, classification, lowering, cache, commitment, timing, and
   transport all fail closed. Physical source lifetime and geometry remain
   unknown.
3. **What does an exact result answer?** The same literal timer-domain
   schedule as V3, not realized births, collision safety, or damage.
4. **What falsifies it?** Any omitted non-null record, source-index mismatch,
   commitment collision/mismatch, raw replay mismatch, timing miss, action
   change, or hidden survival regression.
5. **Can it be consumed before issue?** No. V4 remains post-issue trace-only.

## Acceptance Boundary

V4 may gain physical trace-delivery authority only after all semantic,
transport, timing, cadence, cleanup, and single-run survival gates pass and
the report regenerates twice byte-identically. Handoff still requires the
separate consecutive-run and cross-stage evidence.
