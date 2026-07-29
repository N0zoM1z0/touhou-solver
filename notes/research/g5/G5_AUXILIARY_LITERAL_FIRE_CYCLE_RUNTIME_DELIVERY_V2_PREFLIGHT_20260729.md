# G5 Auxiliary Literal Fire-Cycle Runtime Delivery V2 Preflight

Date: 2026-07-29

Status: implementation and isolated replay pass; physical gate pending

Contract:
`G5_AUXILIARY_LITERAL_FIRE_CYCLE_RUNTIME_DELIVERY_V2_CONTRACT_20260729.md`

## Result

**Observed:** the schema-v5 implementation replays all 142 immutable
schema-v4 physical transactions from run `20260729_014125` through the
corrected delivery path on both Linux and Windows. Five fresh service
instances per platform produce 710 timed samples. Every row is classified,
the first repeat has exactly 46 cache misses, 1,797 persistent hits, 1,987
request-local hits, and zero eviction, and all fixed isolated timing gates
pass.

This is retained preflight evidence only. JSON serialization excludes the
physical synchronous file write, the replay does not reproduce live game and
controller contention, and no result here satisfies the fixed physical gate.

## Fixed Workload

- source raw trace SHA-256:
  `6d779046155d8c36fce9581d1a91389bf6a199212171e813f2766b55cf03c872`;
- source trace bytes: `497850128`;
- exact Stage-5 ECL SHA-256:
  `3148f45faf78bd8211a956edcdc353be73d2781995d3dadd36bdca8132f8fe19`;
- 142 transactions per repeat, five repeats, 710 samples;
- 30 `empty_complete` and 680 `success` samples across repeats; and
- first-repeat serialized payload: 8,580,218 bytes total, 89,011-byte
  maximum on Linux and 8,580,170 bytes total, 89,008-byte maximum on
  Windows. The small JSON-size difference is attributable to measured
  floating-point timing text in the derived event records, not replay state.

## Timing

All values are milliseconds.

| Platform and phase | p95 | p99 | max | Fixed limits |
| --- | ---: | ---: | ---: | --- |
| Linux preparation total | 3.279 | 3.365 | 3.387 | max 8.000 |
| Linux event derivation | 0.371 | 0.538 | 0.653 | 0.500 / 1.000 / 3.000 |
| Linux replay compact | 0.329 | 0.458 | 0.683 | 0.500 / 1.000 / 3.000 |
| Linux JSON serialize, no write | 0.585 | 0.837 | 0.990 | 1.000 / 2.000 / 6.000 |
| Windows preparation total | 6.095 | 6.143 | 6.155 | max 8.000 |
| Windows event derivation | 0.408 | 0.597 | 0.769 | 0.500 / 1.000 / 3.000 |
| Windows replay compact | 0.433 | 0.495 | 1.607 | 0.500 / 1.000 / 3.000 |
| Windows JSON serialize, no write | 0.626 | 0.751 | 1.044 | 1.000 / 2.000 / 6.000 |

Retained reports:

- `artifacts/benchmarks/auxiliary_ecl_event_runtime_delivery_v2_linux_20260729.json`,
  SHA-256
  `bb9fb6e3c7634cc65529317479fdbb62192448e0f84e57cec1cb83ba0adae4cb`;
- `artifacts/benchmarks/auxiliary_ecl_event_runtime_delivery_v2_windows_20260729.json`,
  SHA-256
  `805ac6df4332a535875a1c360b512303831f92988b2101d3f24b65afd90ffea9`.

## Implementation Boundary

The production path now has:

- one visible, exact-version program preparation before selected batches;
- a 512-entry exact-environment LRU result cache;
- explicit `empty_complete` semantics for a strictly verified initial
  zero-record prefix;
- one hash-addressed zlib-level-1 replay bundle per transaction; and
- a schema-v5 independent auditor that replays every request from raw bytes
  and separately simulates cache transitions.

The default schema-v3 path is unchanged. Schema v4 remains an immutable failed
delivery version. The V2 service remains default-off, post-issue,
trace-only, and has no process-reader or action capability.

## Verification

- Ruff passes over all changed production, analysis, benchmark, and test
  modules.
- Focused cache, bundle, service, trace, V1/V2 physical-report, and tamper
  suites pass.
- Complete Linux discovery passes 1,020 tests in 11.561 seconds.
- Complete Windows UNC discovery passes 1,020 tests in 20.672 seconds with
  three existing platform skips.
- The immutable V1 physical report still regenerates byte-identically at
  SHA-256
  `780b8f62dee8eb1c179caf0d54964b090095a99e59634c1654fa7d0cc5aebb3e`.

## Next Gate

Run the unchanged focused Lunatic Stage-5 spell-107 physical workload and
audit schema v5 against the same schema-v3 cadence baseline. Retain failure
without loosening any threshold, or regenerate a passing report twice
byte-identically before granting replay-capable action-neutral delivery for
that exact workload.
