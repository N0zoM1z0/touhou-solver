# G5 Auxiliary Literal Fire-Cycle Runtime Delivery V2 Contract

Date: 2026-07-29

Status: fixed before implementation; implementation/preflight complete;
physical authority pending

Supersedes: no contract. Schema v4 and its failed physical report remain
immutable evidence under
`G5_AUXILIARY_LITERAL_FIRE_CYCLE_RUNTIME_DELIVERY_CONTRACT_20260728.md`.

## Decision

The corrected default-off trace delivery may use:

- one visible exact-program preparation after accepted runtime-ECL identity;
- one bounded result cache owned by that complete immutable program version;
- explicit independently verifiable empty-prefix completion; and
- one hash-addressed compressed replay bundle per selected transaction.

It must retain zero event-layer process reads, exact request order, raw-state
replay, fail-closed unknowns, post-issue trace-only execution, hard no-Bomb
control, unchanged action authority, and the existing per-batch
timing/cadence limits.

This contract grants no emission, physical-time, source-lifetime,
realized-birth, transform-sharing, geometry, hazard, viability, planner,
publication, Power, damage, targeting, or actuator authority.

## Why V2 Is Required

**Observed:** schema-v4 physical run `20260729_014125` passed exact transport,
version, and independent replay for all 3,830 requests but failed its fixed
delivery gate. CE-0168 retains:

- six zero-record prefix transactions labeled `no_usable_contexts`;
- event-derive p95/p99/max `0.879/1.058/4.871 ms`;
- replay compact p95/p99/max `0.381/0.503/11.335 ms`; and
- preceding emit p95/p99/max `2.871/3.495/5.268 ms`.

The retained raw states contain only 46 distinct intent-equivalence keys.
Sequential exact reuse would have 3,784 hits and 46 misses across 3,830
requests. This is observed workload structure, not yet a Windows or physical
performance result.

## Physical Problem Contract

### Objective

Deliver one independently replayable timer-domain literal-fire intent record
for every coherent selected auxiliary-VM transaction in the fixed Lunatic
Stage-5 spell-107 workload, before the next selected transaction, without
changing any game input or materially regressing controller cadence.

Survival remains hard no-Bomb under the unchanged live controller. This
trace-only service does not influence survival choices.

### State And Observations

The delivery state is:

```text
Q = (
  accepted_runtime_version,
  prepared_version_or_none,
  bounded_exact_result_cache,
  selected_coherent_auxiliary_batch,
  observed_empty_prefix_state
)
```

The accepted runtime version includes runtime base, image length, relocated,
normalized, and static SHA-256 values, route, difficulty, stage, gameplay
epoch, and acceptance frames.

The selected batch is the already captured native-owned coherent
owner/context transaction. V2 receives no process-reader capability and may
observe only its retained records and bytes.

### Actions And Issue Semantics

The service has no physical action. Its only outputs are:

- one preparation trace record;
- one schema-v5 auxiliary batch trace record; and
- one schema-v2 derived event record inside that batch.

It never emits a movement, Shot, Focus, Bomb, menu, or actuator command. It
never turns a held mask into a write and never samples input delay.

### Uncertainty And Transitions

Every mismatch in runtime version, program binding, route, difficulty, stage,
epoch, native coherence, record status, depth, target, marker, PC ownership,
replay bundle, lowerer result, or deadline is explicit unavailable/unknown.

Preparation transitions:

```text
unprepared --exact accepted version--> prepared(exact version, empty cache)
prepared(v) --same v--> prepared(v)
prepared(v) --different v--> unavailable until a visible new preparation
```

Cache transitions are deterministic LRU transitions under one prepared
version. Eviction may change computation time only; it may not change a
result, request ordering, result-index mapping, or status.

### Horizon And Resources

- fixed targets/horizons: 69/16, 72/16, 73/60 timer ticks;
- maximum lowerer instructions: 64;
- maximum physical-step search: 65,536, although physical timing remains
  unavailable in this workload;
- result-cache capacity: exactly 512 intent-equivalence keys;
- replay blob size: exactly `0x228` bytes;
- maximum replay blobs: the unique nonempty active/saved-frame hashes
  referenced by the bounded selected native transaction; and
- native visible retry remains at most three attempts under the accepted v3
  transport contract.

The cache key is the existing exact intent-equivalence tuple:

```text
(instruction_pointer, timer_previous, timer_fraction_bits,
 timer_elapsed, timer_tick_horizon)
```

The cache environment is immutable instruction mapping, runtime base,
difficulty mask, physical-time mode, instruction budget, and physical-step
budget. A new environment requires a new cache instance.

### Safety Invariants

1. Default schema v3 is byte/schema unchanged when V2 is disabled.
2. Schema v4 remains readable and reproducibly failed; it is never silently
   upgraded or reinterpreted.
3. Preparation and delivery add no process-memory read.
4. Only a complete exact accepted version may prepare or serve a cache.
5. Cache hits and misses produce the same immutable lowerer result.
6. The independent physical auditor never consumes the production cache.
7. Every referenced active/saved-frame SHA-256 resolves to exactly one
   decompressed `0x228`-byte blob; every bundled blob is referenced.
8. No per-record raw hexadecimal field is present in schema v5.
9. Empty completion is allowed only in one prefix before the first nonempty
   transaction. Each such row must have zero native records, zero non-null and
   usable contexts, zero payload bytes, zero requests, zero results, and zero
   unknown.
10. Any later empty row, return to empty after nonempty, or empty row with
    hidden records is a gate failure.
11. Unknown lowerer direction remains outside hard safety authority.
12. Bomb bit `0x02` remains forbidden.

### Preparation, Deadline, And Fallback

Preparation occurs post-issue immediately after the first exact runtime-ECL
identity observation, long before the spell-107 selection window. It emits:

- the complete accepted version;
- bind/cache configuration;
- preparation status; and
- measured bind/total milliseconds.

Preparation maximum is fixed at 8.00 ms. It is also charged to the full
decision-cadence distribution; it is not hidden from end-to-end contention.

Each selected schema-v5 transaction must finish capture, derive, replay
packing, and synchronous trace delivery before the next selected transaction.
The unchanged per-batch limits are:

| Phase | p95 | p99 | max |
| --- | ---: | ---: | ---: |
| event derivation | 0.50 ms | 1.00 ms | 3.00 ms |
| replay-state compacting | 0.50 ms | 1.00 ms | 3.00 ms |
| preceding synchronous emit | 1.00 ms | 2.00 ms | 6.00 ms |
| selected transaction total | 3.00 ms | 5.00 ms | 15.00 ms |

Decision cadence p95 may regress by at most one frame against the same
accepted schema-v3 baseline. A miss records failure and leaves all live
actions unchanged.

## Replay Bundle

Schema-v5 observation records retain the existing per-record active/saved
SHA-256 references. Raw blobs are stored once in first-reference order:

```text
schema: th08-auxiliary-vm-replay-bundle-v1
encoding: zlib-base64
compression_level: 1
blob_bytes: 552
blob_count: N
uncompressed_bytes: 552 * N
uncompressed_sha256: SHA256(concatenated blobs)
blob_sha256: [one exact hash per blob]
payload_base64: base64(zlib_level_1(concatenated blobs))
```

The independent decoder applies a bounded decompression limit derived from
`blob_count * blob_bytes`, rejects trailing/unconsumed data, rehashes the
concatenation and every chunk, checks uniqueness and exact reference
coverage, and rejects legacy raw fields.

Compression is transport encoding only. It cannot define state equality,
canonicalization, or lowerer authority.

## Cache Evidence

Every event row reports:

- request-local duplicate hits;
- persistent cache hits;
- cache misses;
- evictions; and
- entries after the transaction.

The independent auditor reconstructs each request from raw bytes and executes
the independent oracle regardless of cache classification. It also verifies
that reported cache transitions match an independent deterministic LRU
simulation over the observed intent keys. A production cache result mismatch
or reported-stat mismatch fails the gate.

## Fixed V2 Physical Gate

Workload remains:

- Sakuya/Remilia route 2;
- Lunatic Stage-5 practice;
- spell ID 107;
- hard no-Bomb;
- batch cadence 16 changed manager frames;
- `gil-held` native call mode; and
- exact 47,224-byte Stage-5 ECL SHA-256
  `3148f45faf78bd8211a956edcdc353be73d2781995d3dadd36bdca8132f8fe19`.

Every gate must pass:

- accepted route completion, no-save behavior, cleanup, and zero Bomb input;
- exactly one successful schema-v1 preparation record before all schema-v5
  batches and before spell 107;
- preparation exact-version identity and timing;
- all selected native transactions coherent with visible retry accounting;
- every batch bound to the prepared immutable version;
- valid zero-record empty prefix followed by at least one nonempty row and no
  later empty row;
- exact replay-bundle decoding and reference coverage;
- all nonempty requests limited to targets 69/72/73;
- zero unresolved request and independent raw-byte oracle parity;
- exact independent LRU/cache-stat parity;
- no event-layer process read;
- unchanged timing limits above; and
- decision cadence p95 regression at most one frame.

The strict report must regenerate twice byte-identically. Any failed gate
retains evidence but rejects delivery.

## Required Questions

1. **Which histories merge?** Only identical complete immutable program
   versions and identical intent-equivalence keys share a result. Request
   order, record identity, raw hashes, and owner/source dependencies remain
   distinct. Empty observations merge only as an explicit initial
   zero-record prefix class.
2. **Are all uncertainty branches represented?** Yes for the declared
   timer-domain proxy: mismatched identity, preparation, transport, record,
   target, depth, marker, PC owner, replay, cache transition, lowerer stop,
   timing, or empty placement is unavailable/unknown or a failed gate.
3. **What does an exact solution answer?** It answers the literal
   timer-domain intent schedule for each captured auxiliary VM under exact
   shipped instructions. It does not answer physical emission, lifetime,
   geometry, collision, damage, or action choice.
4. **What falsifies the algorithm?** Any production-cache result differing
   from independent replay, incorrect LRU statistic, missing/extra/corrupt
   raw blob, non-prefix empty row, immutable-version mismatch, hidden read,
   timing miss, cadence regression, or action change.
5. **Can it be consumed before issue?** No. Preparation and delivery remain
   post-issue and trace-only. Future guidance requires a separate causal
   physical-time/source/geometry/containment/deadline contract.

## Acceptance Boundary

One passing V2 physical run grants replay-capable action-neutral delivery only
for this exact Stage-5 spell-107 workload and immutable schema. It does not
promote the event into the planner. Repetition is required before any broader
performance stability claim, and Stage 3 requires its own Power-0
target/source inventory and physical contract.
