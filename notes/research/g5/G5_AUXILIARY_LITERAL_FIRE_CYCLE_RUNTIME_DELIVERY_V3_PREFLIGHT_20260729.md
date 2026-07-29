# G5 Auxiliary Literal Fire-Cycle Runtime Delivery V3 Preflight

Date: 2026-07-29

Status: implementation and isolated cross-epoch replay pass; physical gate
pending

Contract:
`G5_AUXILIARY_LITERAL_FIRE_CYCLE_RUNTIME_DELIVERY_V3_CONTRACT_20260729.md`

## Result

**Observed:** schema-v6/event-v3 now separates immutable ECL program identity
from controller observation epoch. The exact 47,224-byte Stage-5 image is
fully byte-revalidated before gameplay, every executable successor of target
subroutines 69/72/73 is proved to remain in its same-target nine-instruction
closure, and only those nine prevalidated descriptors are bound after the
runtime base is accepted.

Five fresh service instances on Linux and Windows replay all 142 retained
physical schema-v4 transactions. Each repeat deliberately moves one accepted
epoch-0 program through current observation epochs 1, 2, and 3. All 710
transactions remain available, every request is classified complete, the
exact LRU survives the epoch transitions, and every fixed isolated gate
passes.

This is retained preflight evidence only. Static validation occurs before the
gameplay loop, but the replay does not reproduce live game/controller
contention, synchronous trace writes, or survival. Physical delivery and the
user-set Stage-5 regression boundary remain unaccepted.

## Fixed Workload

- source run: `20260729_014125`;
- source raw trace bytes/SHA-256:
  `497850128` /
  `6d779046155d8c36fce9581d1a91389bf6a199212171e813f2766b55cf03c872`;
- exact Stage-5 ECL bytes/SHA-256:
  `47224` /
  `3148f45faf78bd8211a956edcdc353be73d2781995d3dadd36bdca8132f8fe19`;
- 1,664 exact instructions prevalidated; nine target instructions bound;
- 142 transactions per repeat, five repeats, 710 samples;
- accepted epoch 0; observation epoch counts per repeat:
  `1:48, 2:47, 3:47`;
- 30 `empty_complete` and 680 `success` samples;
- first-repeat cache:
  46 misses, 1,797 persistent hits, 1,987 request-local hits, zero eviction;
  and
- no action, process read, planner, geometry, or physical-time authority.

## Timing

All values are milliseconds.

| Platform and phase | p95 | p99 | max | Fixed limits |
| --- | ---: | ---: | ---: | --- |
| Linux pre-game static validation | 12.294 | 13.073 | 13.268 | recorded, no issue-loop limit |
| Linux online preparation | 0.041 | 0.043 | 0.044 | max 1.000 |
| Linux event derivation | 0.366 | 0.522 | 0.683 | 0.500 / 1.000 / 3.000 |
| Linux replay compact | 0.295 | 0.384 | 0.554 | 0.500 / 1.000 / 3.000 |
| Linux JSON serialize, no write | 0.541 | 0.792 | 0.998 | 1.000 / 2.000 / 6.000 |
| Windows pre-game static validation | 42.358 | 42.637 | 42.707 | recorded, no issue-loop limit |
| Windows online preparation | 0.069 | 0.072 | 0.073 | max 1.000 |
| Windows event derivation | 0.436 | 0.694 | 0.843 | 0.500 / 1.000 / 3.000 |
| Windows replay compact | 0.445 | 0.546 | 0.769 | 0.500 / 1.000 / 3.000 |
| Windows JSON serialize, no write | 0.624 | 0.746 | 1.108 | 1.000 / 2.000 / 6.000 |

Retained reports:

- `artifacts/benchmarks/auxiliary_ecl_event_runtime_delivery_v3_linux_20260729.json`,
  SHA-256
  `1781f2df271570d4d25924d2cfc747b2de7490c23309fa21f2d6df7e685fae61`;
- `artifacts/benchmarks/auxiliary_ecl_event_runtime_delivery_v3_windows_20260729.json`,
  SHA-256
  `37f8477b56fcca6d834a1e8c065feb1581e3560a9b5f1ab9540c666ef816a242`.

## Independent Checks

- The strict V3 synthetic gate crosses epochs 0/1/2/3 and rejects epoch
  provenance, program-identity-key, preparation-deadline, and survival
  tampering.
- The target-closure unit rejects a direct-fire successor outside its
  retained owner closure.
- The frozen V2 test fixture remains schema v5/event v2.
- The immutable failed V1 report regenerates byte-identically at SHA-256
  `780b8f62dee8eb1c179caf0d54964b090095a99e59634c1654fa7d0cc5aebb3e`.
- Ruff passes.
- Complete Linux discovery passes 1,027 tests in 11.428 seconds.
- Complete Windows UNC discovery passes 1,027 tests in 22.223 seconds with
  three existing skips.

## Next Gate

Commit this exact implementation, then run the unchanged focused Lunatic
Stage-5 spell-107 workload. Retain every corrected run. A passing delivery
report must regenerate twice byte-identically and must separately report at
most ten hits. Handoff additionally requires two consecutive corrected
Stage-5 runs at that survival boundary and later cross-stage regression
evidence.
