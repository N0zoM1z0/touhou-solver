# G5 Auxiliary Literal Fire-Cycle Runtime Delivery Stage-5 Result

Date: 2026-07-29

Implementation checkpoint: `facefbc`

Workload: Lunatic Route-2 Stage-5 practice, spell 107 sampling

Authority: failed physical delivery gate; semantic replay evidence only

## Result

**Observed:** schema-v4 replay semantics passed, but the fixed physical
delivery gate failed. This run grants no runtime delivery, future-geometry,
planner, or action authority. The failed gate and thresholds remain immutable.

The accepted practice session
`lunatic_route2_stage5_unattended_20260729_014125` covered frames `2..41804`
and 11,805 decisions. The executable SHA-256 was
`330fbdbf58a710829d65277b4f312cfbb38d5448b3df523e79350b879213d924`;
the native no-life-decrement patch was observed at `0x44D0FA`; the route,
difficulty, team, stage, and gameplay state were native-verified; every input
was hard no-Bomb; termination was `route_complete`; the no-save action was
sent; and the exact target was terminated.

The run had 11 contacts at frames
`1481/11138/12721/13823/14468/24813/29980/35419/36449/40039/40717`.
The canonical fresh-attempt contact was a nonspell event at frame 1481 with
Power 128. Phase counts were nonspell 6, spells 103/107/111 each 1, and spell
115 2. This is one workload sample, not evidence of a policy regression:
the two immediately relevant retained Stage-5 runs had 10 contacts each.

## Exact Semantic Evidence

- 142/142 schema-v4 native transactions succeeded and passed the independent
  transport/coherence audit.
- Every row used the same route-2, Lunatic, Stage-5, gameplay-epoch-0 accepted
  runtime version.
- Runtime image normalization exactly matched the 47,224-byte shipped
  `ecldata5.ecl`, SHA-256
  `3148f45faf78bd8211a956edcdc353be73d2781995d3dadd36bdca8132f8fe19`.
- All 3,830 replayable requests were lowerable and complete; independent
  raw-byte oracle parity was 3,830/3,830 with zero unknown.
- Target counts were 69 = 950, 72 = 965, and 73 = 1,915.
- No event-layer process read was present. Transaction-total
  p95/p99/max `2.892/4.833/13.583 ms` passed `3.00/5.00/15.00`.
- Decision-frame cadence p95 remained 4 frames, equal to the accepted
  schema-v3 baseline.

These observations validate replay for captured literal timer-domain intent
only. Physical emission time, realized birth, source life, transform sharing,
geometry, collision coverage, and policy use remain unknown.

## Fixed Gate Failures

| Gate | Observed p95/p99/max ms | Fixed limits | Result |
| --- | ---: | ---: | --- |
| event derivation | 0.879 / 1.058 / 4.871 | 0.50 / 1.00 / 3.00 | fail |
| replay-state compacting | 0.381 / 0.503 / 11.335 | 0.50 / 1.00 / 3.00 | fail |
| preceding synchronous emit | 2.871 / 3.495 / 5.268 | 1.00 / 2.00 / 6.00 | fail |
| total transaction | 2.892 / 4.833 / 13.583 | 3.00 / 5.00 / 15.00 | pass |

The one-time exact-program bind consumed 4.783 ms on the first empty batch.
For all rows, inner state decode p95 was 0.318 ms, lower p95 0.465 ms, and
result compact p95 0.070 ms. The event service recalculated approximately
14 unique schedules per batch even though later batches reused many exact
intent states. Per-record hexadecimal raw state enlarged synchronous JSON
delivery. The 11.335 ms raw compact maximum at frame 29668 is retained as
unattributed live contention; it cannot be discarded as an outlier.

Six initial transactions at frames
`28667/28684/28703/28719/28734/28751` each had exactly zero native records,
usable contexts, requests, or unknowns. Schema v4 correctly exposed them as
`no_usable_contexts`, but its fixed all-`success` gate therefore failed.
Reinterpreting them after the run would invalidate the gate.

## Versioned Correction Direction

A new contract is required before implementation:

1. preserve schema v4 and this report as failed;
2. define an explicit empty-complete status only for an independently checked
   zero-record prefix before the first nonempty spell observation;
3. visibly prepare the exact runtime-base program after accepted identity,
   report its one-time timing, and keep it outside per-batch cold maxima
   without hiding it from end-to-end cadence;
4. use a bounded cache keyed by the complete immutable program version and
   exact intent-equivalence key; eviction may affect speed only;
5. store replay bytes once in a hash-addressed compressed bundle, require
   exact independent decompression/hash/reference coverage, and retain
   default schema v3 unchanged; and
6. keep the existing per-batch timing and cadence limits for the corrected
   physical gate.

Any cache mismatch, missing raw hash, non-prefix empty batch, decompression
failure, unknown request, timing miss, or cadence regression rejects the new
gate.

## Reproducibility

- raw trace SHA-256:
  `6d779046155d8c36fce9581d1a91389bf6a199212171e813f2766b55cf03c872`;
- session SHA-256:
  `c12cc9e8c17085a1536c86d507c516e9ce8128d585042bd40cf2033d88b03889`;
- failed compact report SHA-256:
  `780b8f62dee8eb1c179caf0d54964b090095a99e59634c1654fa7d0cc5aebb3e`;
- report-internal digest:
  `b9d4032e09f99a2f9777283e4e63370652812682bd8781918f791b7c37f75a7a`.

The strict report was regenerated twice byte-identically. CE-0168 retains the
durable failure.
