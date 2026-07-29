# G5 Auxiliary Literal Fire-Cycle Runtime Delivery V4 Stage-5 Failure

Date: 2026-07-29

Status: physical semantics accepted; delivery and survival rejected

Contract:
`G5_AUXILIARY_LITERAL_FIRE_CYCLE_RUNTIME_DELIVERY_V4_CONTRACT_20260729.md`

## Scope

**Observed:** checkpoint `a31f74d` completed unattended Lunatic Route-2
Stage-5 practice run `20260729_113124` over frames `1..42928` with 11,797
decisions, route completion, hard no-Bomb input, accepted artifacts, and exact
process/input cleanup. The run took 14 hits:

- nonspell: 8;
- spell 103: 2;
- spell 107: 3;
- spell 111: 1; and
- spell 115: 0.

The raw trace is 503,762,582 bytes with SHA-256
`9385f9dcc9859e44fc9256df3bac811aec1973d38e86e63605f951290bb4fe8c`.
It remains local and ignored. The compact run dossier and strict failed report
are retained.

## What Passed

**Observed:** all 184 schema-v7 native batches were coherent and successful.
The independent raw-byte auditor completed all 5,124 requests with zero
unknown, including six independently verified empty prefixes. Target counts
were 1,262/1,300/2,562 for subroutines 69/72/73. Exact program identity,
observation epochs, source indices, status proof, replay blobs, recurrence-core
commitments, cache behavior, preparation, hard no-Bomb, route completion,
cleanup, and decision-cadence gates passed.

Online preparation took `0.0785 ms`. Event derive p50/p95/p99/max was
`0.245/0.362/0.443/0.530 ms`, replay compact was
`0.350/0.424/0.475/2.811 ms`, and transaction total was
`1.692/2.299/2.830/3.920 ms`. These meet their immutable component limits.

This is physical trace semantics only. It grants no future-geometry, planner,
action, source-lifetime, dynamic-parameter, transform, or realized-birth
authority.

## What Failed

**Observed:** the strict V4 physical report fails three independent gates:

1. Projected batch-line p50/p95/p99/max is
   `22964/24142/25230/25296` bytes. The maximum exceeds the fixed 24,576-byte
   limit.
2. Previous synchronous trace emit p50/p95/p99/max is
   `1.058/1.366/1.650/1.916 ms`. The p95 exceeds the fixed 1.000-ms limit.
3. Fourteen hits exceed the user-set Stage-5 boundary of ten.

The largest row contains 34 usable records. Repeated keys in the usable-record
dictionary projection and event request dictionaries dominate the residual
size. The isolated retained-trace maximum of 23,495 bytes was therefore not a
valid upper bound for the fresh physical context distribution.

The survival failure is separate from evidence serialization. Every hit
followed global viability-kernel exhaustion. Eight hits occurred in nonspell,
and the canonical first hit was a nonspell committed-prefix collision at
frame 1,567. This strengthens, but does not prove, the separate hypothesis that
distributed nonspell enemies may require earlier kill/despawn and firing-mode
control inside the viable set.

## Fixed Next Correction

Do not loosen any timing, size, cadence, hard no-Bomb, cleanup, or survival
threshold.

Before implementation, freeze a V5 transport-only contract that:

- preserves the complete status histogram, exact source indices, every
  selected raw active/saved VM byte, hashes, epochs, and program identity;
- replaces repeated usable-record and request dictionary keys with fixed,
  versioned column schemas and ordered rows;
- independently rejects missing, reordered, duplicated, out-of-range, or
  type-invalid columns and rows before reusing the V4 byte oracle;
- keeps the event recurrence commitment unchanged; and
- changes no sensing read, ECL recurrence, cache, planner, policy, actuator,
  firing mode, or physical action.

Only after Linux/Windows replay, tamper, serialization, and historical
immutability gates pass may V5 receive a fresh physical delivery run.
Survival changes remain a separate intervention. Handoff still requires two
consecutive corrected Stage-5 runs at no more than ten hits, followed by the
cross-stage matrix.

## Retained Evidence

- strict failed V4 report:
  `artifacts/viability_audit/g5_auxiliary_ecl_event_runtime_delivery_v4_stage5_20260729_113124_failure.json`,
  SHA-256
  `2d5ebcf862cb5ce9fc3af1b3c858ae95c7444727deaa959d188f94ed7d33ed29`;
- run note:
  `notes/runs/lunatic_route2_stage5_unattended_20260729_113124.md`;
- compact summary SHA-256
  `1d39c5df529c384fe5f15860fee5c66d7b397d5eb346173109ce1a66898c2823`;
- compact dossier JSON SHA-256
  `2704157901eccda3baf427469dbdfa8c4c8c619d45f7959db5139d998b77d31d`;
- normalized session SHA-256
  `61242e1afba0289c5a3e571070d699ddccd8396ff177b29d2e4f06798f5c67ce`.
