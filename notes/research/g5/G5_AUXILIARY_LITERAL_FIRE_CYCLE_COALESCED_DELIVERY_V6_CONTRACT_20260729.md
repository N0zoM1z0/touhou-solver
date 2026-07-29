# G5 Auxiliary Literal Fire-Cycle Coalesced Delivery V6 Contract

Date: 2026-07-29

Status: fixed before implementation; trace-only proposal, no action authority

Predecessors:

- `G5_AUXILIARY_LITERAL_FIRE_CYCLE_RUNTIME_DELIVERY_V5_CONTRACT_20260729.md`
- `G5_AUXILIARY_LITERAL_FIRE_CYCLE_RUNTIME_DELIVERY_V5_STAGE5_FAILURE_20260729.md`
- CE-0173

## Problem

Physical V5 run `20260729_120859` accepts exact schema-v8 semantics and the
15,453-byte maximum line. It rejects the still-separate auxiliary trace
publication: previous emit p95 is `1.412 ms` against the fixed `1.000 ms`
limit. The controller writes that row, later serializes the ordinary decision
row from the same iteration, then writes and flushes the decision row.

**Observed diagnostic:** V5 rows with 16 or more records have approximately
`1.03 ms` median separate emit. Rows with at most 15 records have
`0.101 ms` median. Emit/line-size correlation is `0.730`.

**Inferred:** further field removal does not address the two-publication
structure. V6 changes only evidence representation and publication
composition: carry the exact canonical V5 row inside the already-required
same-iteration decision publication and issue no standalone auxiliary batch
write.

This contract does not change capture cadence, process reads, ECL identity,
event recurrence, cache, sensing, planner, issued mask, Focus, Bomb, Power,
damage, or survival policy.

## Physical Objective

For every due auxiliary observation in the selected trace-only workload:

1. retain all schema-v8 V5 evidence exactly after canonical decoding;
2. bind it to the decision from the same physical controller iteration;
3. publish it with that decision's one existing synchronous flushed write;
4. add bounded packing work and no second batch write; and
5. independently recover, validate, and replay it before granting trace-only
   semantic authority.

The hard physical objective remains survival with no Bomb. V6 is accepted
only if delivery gates pass and the run has at most ten hits. Handoff still
requires two consecutive corrected Stage-5 runs at at most ten hits.

## State, Observation, Action, And Time

The V6 publication state for one due observation is:

`(run trace, sequence, decision frame, gameplay epoch, manager snapshot
frame, stage-route index, canonical V5 row, parent decision row)`.

The inner V5 row is completed post-issue in the current controller iteration.
The parent decision row is constructed later in that same iteration. V6 has
no action. It neither writes process memory nor emits input. The actual
decision publication duration is unavailable until its synchronous write
returns, so the next decision row's existing `timing_ms.previous_trace`
field is the causal measurement of the preceding V6-bearing decision.

No decision may report its own not-yet-observed publication duration.
Missing next-decision measurement leaves the final envelope unresolved and
fails the physical gate.

## Canonical Inner Evidence

Before packing, the producer must:

- retain `kind = auxiliary_vm_batch`;
- retain `schema_version = 8`;
- retain every V5 field and nested value;
- set `timing_ms.previous_emit = null`, because V6 performs no standalone
  auxiliary emit; and
- serialize with UTF-8, sorted keys, separators `,` and `:`, no NaN or
  Infinity, and no trailing newline.

The resulting bytes are the canonical inner evidence. Decoding must parse
exactly one JSON object and reserialize it canonically to the identical byte
sequence before invoking the existing independent V5 column/byte oracle.

V6 does not claim the canonical bytes are the historical V5 source-line
bytes. It claims exact preservation of the complete schema-v8 evidence
object under one unambiguous encoding.

## Outer Envelope

The parent decision owns at most one field named
`auxiliary_vm_batch_envelope`. Its value is exactly:

```text
schema
encoding
compression_level
sequence
decision_frame
gameplay_epoch
snapshot_frame
stage_route_index
inner_schema_version
uncompressed_bytes
compressed_bytes
uncompressed_sha256
compressed_sha256
payload_base64
timing_ms.pack
```

Fixed values:

- `schema = th08-auxiliary-vm-batch-coalesced-envelope-v1`;
- `encoding = canonical-json-zlib-base64`;
- `compression_level = 6`; and
- `inner_schema_version = 8`.

Integers must be nonnegative, booleans are not integers, SHA-256 values are
lower-case hexadecimal, base64 decoding is strict, zlib must reach a clean
end with no unused or unconsumed data, decompressed size is bounded before
allocation, and compressed/decompressed lengths and hashes must agree.

The outer `decision_frame`, `gameplay_epoch`, `snapshot_frame`, and
`stage_route_index` must each equal both the corresponding inner V5 value and
the parent decision value. Sequences start at zero, occur in strict trace
order, and have no duplicates or gaps. A decision without an envelope does
not consume a sequence.

## Causality And Publication Invariants

- Capture and event derivation remain after input issue and before decision
  trace construction, exactly as in V5.
- The envelope is created and attached only to the later decision record in
  that same Python loop iteration.
- No top-level `kind = auxiliary_vm_batch` row may appear in a V6 trace.
- The V6-bearing decision is emitted exactly once through the existing
  synchronous `flush=True` decision publication.
- An envelope may not be queued for a future frame, reused, split, partially
  published, or attached across gameplay epoch/reset.
- Encoder, serialization, write, or binding failure follows the existing
  controller exception path, releases keys, and leaves the run unaccepted.
- A trace ending before the next decision supplies no publication timing for
  its final envelope and fails the physical gate.
- Preparation remains a separate one-time, pre-game/early-game record. V6
  does not change that already accepted boundary.

## Independent Decoder And Oracle

The analysis decoder must not import the production encoder. It validates the
complete outer key set and every bound/type/value above, then:

1. strict-base64 decodes;
2. verifies compressed length and SHA-256;
3. bounded-zlib decompresses and rejects trailing/unconsumed data;
4. verifies uncompressed length and SHA-256;
5. parses one JSON object;
6. proves canonical byte equality;
7. proves parent/envelope/inner frame, epoch, snapshot, stage, and sequence
   equality; and
8. calls `audit_event_batch_v5` unchanged.

The physical report streams the source trace, retains its independent digest,
rejects every standalone schema-v8 batch, and associates each V6-bearing
decision with the immediately following decision's
`timing_ms.previous_trace`. Preparations and runtime identity retain their
existing independent validation.

## Fixed Limits

All values are milliseconds unless stated otherwise.

| Boundary | p95 | p99 | max |
| --- | ---: | ---: | ---: |
| pack canonical JSON + zlib + base64 | 0.750 | 1.250 | 3.000 |
| inner transaction total + pack | 3.500 | 6.000 | 18.000 |

Additional fixed gates:

- base64 payload maximum: 12,288 bytes;
- decompressed canonical inner maximum: 24,576 bytes;
- compressed payload maximum before base64: 9,216 bytes;
- V6-bearing decision emit p95 no more than retained baseline decision emit
  p95 plus `0.500 ms`;
- V6-bearing decision emit p99 no more than retained baseline decision emit
  p99 plus `1.000 ms`;
- all-decision emit p95 no more than retained baseline plus `0.500 ms`;
- decision-frame-delta p95 no more than baseline plus one frame; and
- exact accepted completion, hard no-Bomb, and cleanup.

The retained baseline is
`lunatic_route2_stage5_unattended_20260728_200739`, SHA-256
`953a5c3cb4bef84a809c9d2681aedcc081f67cc7f8dc39aa942bc42f0da779e9`.

**Observed sizing diagnostic, not a physical pass:** ten Linux passes over all
154 V5 physical rows produce canonical inner p95/max
`13934/14448` bytes, base64 p95/max `7024/7196` bytes, and pack
p95/p99/max `0.365/0.416/0.825 ms`. This justifies the fixed bounds but is not
Windows or live contention evidence.

The historical V5 limits remain immutable. V6 does not reinterpret the absent
standalone emit as a V5 pass.

## Formal Questions

1. **Which histories map to one model state?** V6 maps exactly one completed
   post-issue V5 observation and the later decision publication from the same
   controller iteration. Equal envelope fields without equal canonical bytes
   are not merged. V6 does not merge physical control histories or alter
   their actions.
2. **Are all uncertainty branches and causal choices represented?** V6 adds
   no controller/nature recurrence and makes no choice. It preserves the
   complete V5 uncertainty evidence. Publication duration is observed only by
   the next decision; missing evidence is unresolved, never guessed.
3. **Does exact solution answer the physical question?** Exact decoding
   answers whether the selected observed auxiliary contexts and their V5
   recurrence evidence were preserved and delivered under this publication
   path. It does not prove future-birth completeness, source lifetime,
   geometry, survival, or action safety.
4. **Is the algorithm exact or a bound?** Envelope reconstruction, canonical
   equality, binding, and V5 replay are exact for retained bytes. Timing and
   survival are empirical physical gates. Corruption, truncation,
   recompression ambiguity, frame/epoch/version/order substitution, a
   standalone auxiliary write, missing next-decision timing, or oracle/cache
   mismatch falsifies the claim.
5. **Can it be consumed before issue time?** No consumer exists and no action
   may depend on V6. Evidence is produced post-issue and published at the end
   of that iteration. V6 cannot change cadence, phase, sensor state, immutable
   problem version, or fallback.

## Required Verification

Before a physical run:

- production encode and independent decode reproduce exact canonical V5
  objects across empty, populated, maximum retained, and error rows;
- corruption, truncation, extra zlib members/data, wrong length/hash/schema,
  noncanonical JSON, parent mismatch, inner mismatch, duplicate/gapped
  sequence, stale/deferred attachment, missing timing, and standalone batch
  rows fail closed;
- the unchanged independent V5 oracle and cache oracle pass after decode;
- retained V1 through V5 reports remain byte-identical;
- isolated Linux and Windows packing/decoding gates pass;
- focused and complete Linux/Windows suites pass; and
- source inspection confirms the controller has no separate auxiliary batch
  `TraceSink.emit`.

Then run one fresh hard no-Bomb Lunatic Stage-5 physical gate and retain every
outcome. Do not combine its first delivery run with Focus/unfocused combat,
targeting, Power, or planner changes.

## Authority

Passing V6 grants only physical trace-delivery authority for the selected
observed auxiliary contexts. It grants no live guidance or action authority.
Unsupported emission, dynamic operands, transforms, source life, realized
births, geometry, and planner use remain `UNKNOWN`.

The later survival-filtered Sakuya experiment is separate. Releasing
Focus/Shift for wider nonspell coverage requires native shot/damage/kill and
unchanged hard-margin evidence before any shadow or live rule.
