# G5 Auxiliary Literal Fire-Cycle Runtime Delivery V5 Preflight

Date: 2026-07-29

Status: isolated Linux/Windows gate passed; physical delivery pending

Contract:
`G5_AUXILIARY_LITERAL_FIRE_CYCLE_RUNTIME_DELIVERY_V5_CONTRACT_20260729.md`

## Result

**Observed:** schema-v8/event-v5 maps usable native records and event requests
to fixed, versioned column rows. Five repeats of all 142 retained physical
transactions pass on Linux and Windows across accepted program epoch 0 and
observation epochs 1/2/3. Each platform classifies 30 `empty_complete` and
680 `success` batches.

The independent decoder validates exact schemas, columns, row arity, primitive
types, source order, status proof, and raw replay bundle before invoking the
existing independent V4 byte oracle. Each platform independently replays all
19,150 requests across five repeats with zero unknown:

- first-repeat targets 69/72/73: `950/965/1915`;
- misses: 46;
- persistent hits: 1,797;
- request-local hits: 1,987; and
- evictions: zero.

This is isolated replay and serialization evidence. It is not physical
contention, survival, planner, geometry, damage, Power, targeting, source-life,
transform, realized-birth, or action authority.

## Representation And Size

The V5 observation has no legacy `records` dictionaries. One exact column
schema owns all fourteen usable-record fields, including source index and
active/saved hashes. A separate three-column schema owns request status and
result identity. Full raw VM blobs, the complete native status histogram,
epochs, program identity, cache record, and recurrence-core commitment remain.

First-repeat output size:

| Platform | Total bytes | Minimum line | Maximum line |
| --- | ---: | ---: | ---: |
| Linux | 1,696,240 | 4,191 | 13,743 |
| Windows | 1,696,160 | 4,190 | 13,741 |

The fixed maximum remains 24,576 bytes. As a separate structural diagnostic,
projecting the actual failed V4 physical run `20260729_113124` without changing
its timing values yields 184 rows with p50/p95/p99/max
`13042/13552/13978/14038` bytes. This is evidence of line-size margin over
the fresh 34-record distribution, not physical V5 timing.

## Timing

All values are milliseconds.

| Platform and phase | p95 | p99 | max | Fixed limits |
| --- | ---: | ---: | ---: | --- |
| Linux online preparation | 0.035 | 0.035 | 0.035 | max 1.000 |
| Linux event derivation | 0.190 | 0.300 | 0.859 | 0.500 / 1.000 / 3.000 |
| Linux replay compact | 0.236 | 0.270 | 0.445 | 0.500 / 1.000 / 3.000 |
| Linux JSON serialize, no write | 0.100 | 0.132 | 0.165 | 0.250 / 0.500 / 1.500 |
| Windows online preparation | 0.069 | 0.075 | 0.077 | max 1.000 |
| Windows event derivation | 0.280 | 0.502 | 0.770 | 0.500 / 1.000 / 3.000 |
| Windows replay compact | 0.390 | 0.436 | 0.725 | 0.500 / 1.000 / 3.000 |
| Windows JSON serialize, no write | 0.149 | 0.175 | 0.226 | 0.250 / 0.500 / 1.500 |

Every immutable isolated gate passes with no threshold change.

Retained reports:

- `artifacts/benchmarks/auxiliary_ecl_event_runtime_delivery_v5_linux_20260729.json`,
  SHA-256
  `50aa904f4112d49c82505df572fe2228b48e27df6956e26e27ad0fb81027257c`;
- `artifacts/benchmarks/auxiliary_ecl_event_runtime_delivery_v5_windows_20260729.json`,
  LF-normalized SHA-256
  `cf2afdf03b3bdd471fa22a1fad1f5a5b434ff951ce8d77c59ed364b94bcc9650`.

## Verification

- Strict V5 tamper tests reject column name/order, row arity/type, legacy
  dictionaries, source index, status histogram, replay bundle, commitment,
  slow preparation, and more than ten hits.
- Historical V4 synthetic audit still passes through a frozen legacy
  transport fixture.
- The physical failed V4 report regenerates byte-identically at SHA-256
  `2d5ebcf862cb5ce9fc3af1b3c858ae95c7444727deaa959d188f94ed7d33ed29`.
- The immutable failed V1 report regenerates byte-identically at SHA-256
  `780b8f62dee8eb1c179caf0d54964b090095a99e59634c1654fa7d0cc5aebb3e`.
- Ruff passes.
- Complete Linux discovery passes 1,038 tests in 12.516 seconds.
- Complete Windows UNC discovery exits successfully over the same 1,038-test
  suite with its three existing platform skips.

## Next Gate

Commit this transport-only checkpoint, then run one fresh hard no-Bomb
Lunatic Stage-5 physical gate with schema 8/event V5. Retain every outcome.
Delivery requires exact semantic/oracle/cache parity, physical line size,
derive/compact/emit/total timing, cadence, accepted completion, and cleanup.

Survival remains independent. Handoff requires two consecutive corrected
Stage-5 runs at no more than ten hits plus later Stage-3 and cross-stage
checks. Do not combine the first V5 delivery run with the proposed unfocused
nonspell combat intervention.
