# G5 Auxiliary Literal Fire-Cycle Runtime Delivery V4 Preflight

Date: 2026-07-29

Status: isolated Linux/Windows gate passed; physical delivery pending

Contract:
`G5_AUXILIARY_LITERAL_FIRE_CYCLE_RUNTIME_DELIVERY_V4_CONTRACT_20260729.md`

## Result

**Observed:** schema v7/event v4 replays all 142 retained physical
transactions five times on both Linux and Windows under one exact accepted
program and observation epochs 1/2/3. All 710 samples per platform classify
as 30 `empty_complete` and 680 `success`.

The first repeat preserves the V3 computation identity:

- 46 cache misses;
- 1,797 persistent hits;
- 1,987 request-local hits;
- zero eviction; and
- every request remains independently replayable from retained raw VM/ECL
  bytes.

This is isolated replay and serialization evidence. It is not physical
contention, survival, planner, geometry, damage, Power, targeting, or action
authority.

## Contract Correction Before Implementation

**Inferred and corrected:** the existing independent byte oracle reconstructs
the declared timer recurrence but does not reconstruct every descriptive fire
argument or transform literal in `result.record()`. Hashing the complete
production record would therefore have made production output part of its own
purported proof.

The fixed V4 contract was narrowed before implementation. The commitment now
covers exactly the oracle-compatible recurrence core: ordered fire and
transform event identities, instruction count, stop reason, coverage,
requested/stop ticks, and physical-timing status. Full VM and ECL bytes remain
retained. Excluded descriptive fields gain no authority.

## Implementation Boundary

- `AuxiliaryEclTimerState` decodes only the five fields consumed by the
  recurrence; the full `AuxiliaryEclVmState` remains available to callers that
  explicitly need local projections.
- Successful selected observations retain their full native count and status
  histogram but serialize only `RecordStatus.OK` rows, each with a strictly
  increasing original `source_record_index`.
- All referenced active and saved 552-byte VM states remain in the
  hash-addressed replay bundle. Every omitted row must be proved `NULL`.
- Event request output is limited to
  `(source_record_index, status, result_index)`.
- Repeated full result dictionaries are replaced by ordered SHA-256
  commitments and the complete canonical result-index vector.
- The schema-v7 scanner and V4 physical auditor independently reject
  source-index, status-histogram, raw-bundle, result-commitment, epoch,
  program-identity, preparation-deadline, and survival tampering.
- Historical V1/V2/V3 auditor fixtures use a frozen full-record fixture
  producer. The V1 failed report still regenerates byte-identically.

## Timing And Size

All timing values are milliseconds.

| Platform and phase | p95 | p99 | max | Fixed limits |
| --- | ---: | ---: | ---: | --- |
| Linux online preparation | 0.035 | 0.036 | 0.036 | max 1.000 |
| Linux event derivation | 0.251 | 0.337 | 0.548 | 0.500 / 1.000 / 3.000 |
| Linux replay compact | 0.290 | 0.366 | 0.480 | 0.500 / 1.000 / 3.000 |
| Linux JSON serialize, no write | 0.185 | 0.235 | 0.308 | 0.250 / 0.500 / 1.500 |
| Windows online preparation | 0.051 | 0.053 | 0.053 | max 1.000 |
| Windows event derivation | 0.277 | 0.460 | 0.690 | 0.500 / 1.000 / 3.000 |
| Windows replay compact | 0.387 | 0.447 | 0.538 | 0.500 / 1.000 / 3.000 |
| Windows JSON serialize, no write | 0.191 | 0.224 | 0.257 | 0.250 / 0.500 / 1.500 |

Projected maximum JSON line size is 23,495 bytes on Linux and 23,494 bytes on
Windows, below the fixed 24,576-byte limit. The first-repeat total falls from
the V3 Linux value 8,686,741 bytes to 2,783,636 bytes.

Retained reports:

- `artifacts/benchmarks/auxiliary_ecl_event_runtime_delivery_v4_linux_20260729.json`,
  SHA-256
  `93b629b08aec03467afead22d5a63d9f9c16b6b3700bcb0d05be25960fe4195e`;
- `artifacts/benchmarks/auxiliary_ecl_event_runtime_delivery_v4_windows_20260729.json`,
  SHA-256
  `1517441210e21a7011d5e3ef7558210eccd7ccd625a574ee8ad7c35f6a2ddd88`.

## Verification

- Ruff passes over changed production, analysis, benchmark, and test modules.
- Complete Linux discovery passes 1,032 tests in 12.072 seconds.
- Complete Windows UNC discovery passes 1,032 tests in 26.189 seconds with
  three existing skips.
- The immutable failed V1 report regenerates byte-identically at SHA-256
  `780b8f62dee8eb1c179caf0d54964b090095a99e59634c1654fa7d0cc5aebb3e`.

## Next Gate

Commit this isolated checkpoint, then run one fresh hard no-Bomb Lunatic
Stage-5 spell-107 trace with schema v7/event v4. Retain pass or failure.
Delivery requires every semantic, timing, line-size, cadence, cleanup, and
single-run `<=10`-hit gate. Handoff still requires two consecutive corrected
Stage-5 results at no more than ten hits and separate cross-stage checks.
