# G5 Auxiliary Literal Fire-Cycle Runtime Delivery V5 Contract

Date: 2026-07-29

Status: fixed before implementation

Predecessor:
`G5_AUXILIARY_LITERAL_FIRE_CYCLE_RUNTIME_DELIVERY_V4_STAGE5_FAILURE_20260729.md`

## Physical Question

Can the already observed, independently replayable auxiliary literal
fire-cycle evidence cross the live trace boundary before the next issue time
without changing controller cadence or physical action?

V5 changes only JSON ownership and representation. It adds no process read,
changes no native capture, timer recurrence, uncertainty branch, cache,
planner, policy, actuator, or firing mode. The physical objective remains
survival under hard no-Bomb control. Auxiliary event evidence remains
default-off, trace-only, and outside action authority.

## State, Observations, Actions, And Timing

- The physical history and observation available at the event decision are
  exactly the selected coherent auxiliary-VM observation, accepted immutable
  runtime-ECL version, observation gameplay epoch, route/stage identity, and
  prevalidated event program used by V4.
- V5 maps each V4 usable-record dictionary and request dictionary to one
  ordered fixed-arity row. No histories are newly merged. Column order and
  schema identity are part of the immutable observation.
- The controller action set, held/no-write semantics, pickup delay, cadence,
  horizon, resources, and safety invariants are unchanged. Event delivery
  emits no action.
- Publication is synchronous trace emission. The fixed gate measures
  derivation, compact projection, previous emit, total transaction, line size,
  and decision cadence under physical contention. On any projection error,
  the evidence is unavailable; live control continues through its existing
  hard certificate/fallback and never consumes this trace.

## Immutable V5 Schemas

The outer trace is schema version 8. The event schema is
`th08-auxiliary-ecl-event-derivation-v5`. Preparation remains
`th08-auxiliary-ecl-event-preparation-v2`; program identity and the
`th08-auxiliary-literal-fire-result-commitment-v1` recurrence commitment do
not change.

### Usable-record projection

`observation.record_projection` is:

```json
{
  "schema": "th08-auxiliary-vm-usable-record-projection-v2",
  "record_status_bits": {"0": 1, "1": 2},
  "columns": [
    "source_record_index",
    "slot",
    "auxiliary_index",
    "enemy_pointer",
    "context_pointer",
    "context_pointer_after",
    "enemy_flags_before",
    "enemy_flags_after",
    "status_bits",
    "target_subroutine",
    "call_depth",
    "auxiliary_marker",
    "active_vm_sha256",
    "saved_frame_sha256"
  ],
  "rows": [[0, 3, 2, 5777088, 34603008, 34603008, 1, 1, 0, 69, 0, 1,
            "<sha256>", []]]
}
```

The old `observation.records` key is absent. Every row has exactly fourteen
values. Source indices are strictly increasing, unique, and inside the full
native record count. Every projected status is exactly zero. Integer fields
reject booleans; the three semantic timer metadata fields are integers for a
usable record. The active hash is lowercase SHA-256 and saved-frame hashes
are an ordered lowercase SHA-256 array. The existing hash-addressed
`replay_state_bundle` still contains every referenced 552-byte blob.

The full native status histogram remains canonical, positive-count only, and
sums to `record_count`. Only statuses 0 (`OK`) and 1 (`NULL`) are accepted in
a successful selected batch. The row count must equal the status-0 count;
therefore every omitted row is still proved null.

### Event-request projection

`event_derivation.request_projection` is:

```json
{
  "schema": "th08-auxiliary-ecl-request-projection-v1",
  "columns": ["source_record_index", "status", "result_index"],
  "rows": [[0, "complete", 0]]
}
```

Every row has exactly three values and capture order must equal the usable
record order. `result_index` is either a non-negative integer or null.
Status remains a string and is independently reconstructed from raw bytes,
record metadata, exact program ownership, and the recurrence oracle.

Empty complete batches use both exact schemas with empty rows and an empty
replay bundle/commitment. Unavailable records use the exact request schema
with empty rows and no lowering commitment.

## Independent Audit

The V5 decoder must reject before oracle reuse:

- schema, column name/order, row arity, or primitive-type mismatch;
- missing legacy-equivalent field, unexpected row, duplicate/reordered/
  out-of-range source index, nonzero usable status, or histogram mismatch;
- active/saved hash, replay bundle, epoch, program identity, target horizon,
  request order/status/result index, commitment, or cache mismatch; and
- missing/forged empty-prefix evidence.

After strict column decoding, the independent V4 raw-byte oracle may be
reused by constructing an in-memory V4-equivalent view. This does not make
production its own oracle: the decoder fixes every field and the V4 auditor
still derives timer state, classification, canonical result identity, and
result hashes independently from retained VM/ECL bytes.

Historical V1/V2/V3/V4 fixtures and failed reports remain their original
schemas and must regenerate byte-identically.

## Fixed Gates

No limit is loosened:

- online preparation maximum: `1.000 ms`;
- event derive p95/p99/max: `0.500/1.000/3.000 ms`;
- replay compact p95/p99/max: `0.500/1.000/3.000 ms`;
- no-write JSON serialize p95/p99/max:
  `0.250/0.500/1.500 ms`;
- physical previous emit p95/p99/max: `1.000/2.000/6.000 ms`;
- physical transaction total p95/p99/max:
  `3.000/5.000/15.000 ms`;
- projected physical batch-line maximum: 24,576 bytes;
- decision-cadence p95 regression: at most one frame;
- hard no-Bomb, accepted route completion, and exact cleanup; and
- focused Stage-5 survival: at most ten hits.

Before physical use, five complete retained-trace repeats must pass on Linux
and Windows across multiple observation epochs. The first repeat must retain
exact request/cache totals and the maximum line must pass with useful margin,
not equality alone.

## Authority Answers

1. V5 represents exactly the same selected physical histories as V4; fixed
   row order is a bijection, not a control-state merge.
2. The recurrence and declared uncertainty are unchanged. No hidden branch or
   future observation enters the event choice, and the event emits no action.
3. Exact solving answers only the declared literal timer-schedule proxy. It
   does not answer realized birth geometry, source lifetime, dynamic
   parameters, transforms, damage, Power, targeting, or survival.
4. The raw-byte oracle exactly checks that proxy. Malformed projection,
   commitment mismatch, unsupported instruction/state, physical deadline
   failure, and a later realized-birth mismatch falsify broader use.
5. Only a passing isolated Linux/Windows gate plus fresh physical timing can
   establish delivery. Timeout or malformed evidence becomes unavailable and
   cannot affect cadence, sensing state, or physical action.

The later unfocused-Sakuya combat experiment is explicitly outside this
contract and must not be combined with the V5 transport checkpoint.
