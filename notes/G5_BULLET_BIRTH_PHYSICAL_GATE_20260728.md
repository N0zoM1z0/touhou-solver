# G5 Bullet-Birth Physical Gate

Date: 2026-07-28

Status: B4/B5 failed twice with retained evidence. The schema-v2 physical
repeat validates the deferred-fire state correction and exposes timed intent,
but CE-0143 physical performance and CE-0145 source coverage remain open. No
future-hazard or physical action authority is granted.

## Outcome

Lunatic Stage-4A run
`lunatic_route2_stage4a_unattended_20260728_031127` completed the route and
produced a deterministic residual report, but it did not pass the bullet-birth
gate:

- B4 performance failed: observer p95/p99/max was
  `1.7795/2.7495/10.9700 ms` against the fixed
  `0.20/0.40/2.00 ms` extraction budget.
- B5 temporal correlation failed: all 1,641 visible active-spell main-VM
  intent sightings were untimed because the v1 live integration supplied
  `deferred_fire_active=None`.
- All 86,396 activation edges were unmatched. This is a valid residual
  classification, not proof that no ECL source existed.

The run did successfully establish the shipped-runtime native-age workload:
86,396 inactive-to-active edges, 23 recent bootstrap candidates, 99 timer
regressions, 17 invalid active timers, capture spans 0/1 on 13,822/589 audit
rows, and native age p50/p95/p99/p99.9/max `0/0/0/0/8`.

The schema-v2 repeat
`lunatic_route2_stage4a_unattended_20260728_040144` confirms that the semantic
correction works, but it still fails the gate:

- 5,723/5,780 active-spell main-VM rows had exactly aligned, observed
  deferred-fire state; the other 57 were capture-spanned and remained
  unknown.
- The classifier produced 1,642 timed sightings in 58 deduplicated events.
  Temporal support uniquely matched 2,860 activation edges and ambiguously
  matched 73. Every match occurred during spell 69.
- 84,740/87,673 activation edges remained unmatched. Of those, 37,767 had no
  active-spell main VM and 46,973 had no overlapping timed main-VM intent.
- Physical observer p95/p99/max improved to
  `0.4496/0.9314/10.2189 ms`, but still failed the fixed
  `0.20/0.40/2.00 ms` extraction budget. Record emission p95/max was
  `1.2484/12.8322 ms`.

This is observed source-coverage and performance evidence. The 3.2621%
unique temporal match fraction is not birth prediction accuracy because
template geometry, origin, minimum-distance, player aim, pool capacity,
transform state, and omitted-source competition remain unresolved.

## Physical Scope And Provenance

The exact physical command was:

```text
run_th08_practice_agent.bat --stage 4a --trace-bullet-births
  --status-seconds 20 --stall-timeout 120
```

- Physical controller checkpoint: `4d5245a`, with default-off birth tracing
  explicitly enabled for this run.
- Executable SHA-256:
  `330fbdbf58a710829d65277b4f312cfbb38d5448b3df523e79350b879213d924`.
- Runtime no-life-decrement patch: address `0x44D0FA`, byte `0x00`, verified.
- PID: 47212.
- Accepted practice scope: frames `1..43931`, 14,411 decisions, one epoch,
  `route_complete`, zero parse errors, accepted supervisor artifacts and
  cleanup.
- Native hits: 11 at
  `3968, 4490, 8993, 9528, 12848, 13180, 14005, 22117, 22686, 36678,
  42817`.
- The canonical fresh-attempt hit is frame 3968. Every hit followed global
  viability exhaustion; later hits remain discovery evidence.
- Hard no-Bomb: passed over all 14,411 decisions with zero input-mask,
  decision-flag, or action violations.
- Resources: Power `128 -> 0` across deaths; patched lives remained 8; Bomb
  stock changes are respawn-state changes and not emitted Bomb input.
- Peak active bullets: 1,360.
- Raw trace: 489,082,159 bytes, SHA-256
  `7788114afb988536c9152fe0c9473379d28c59864e86cac4c3ee9b2a829922e5`.
  It remains local and ignored.

## Deterministic B5 Report

Checkpoint `360c79b` adds the streaming deterministic residual audit. Two
generations from the same raw trace are byte-identical. After adding explicit
build/pre-emit timing fields for future schema-v2 traces, the retained v1
report is:

- `artifacts/runtime_reports/lunatic_route2_stage4a_unattended_20260728_031127.birth_audit.json`
- SHA-256
  `65ff30f5363a13ed77df676fe8f829ed8a55948f987191b92915de23c6da2c34`
- `passed = false`
- validation gate: pass
- observer budget gate: fail
- timed-intent-available gate: fail

Activation edges by capture phase were 36,870 nonspell; 8,437 spell 57;
9,982 spell 61; 14,067 spell 65; 5,956 spell 69; and 11,084 spell 73.
Residual unmatched reasons were 36,870 rows without an active-spell main-VM
source and 49,526 rows without a temporally overlapping timed intent.

The schema-v2 repeat report is:

- `artifacts/runtime_reports/lunatic_route2_stage4a_unattended_20260728_040144.birth_audit.json`
- SHA-256
  `9ce122552d0b35e4379a4accad712ba5960671e2fac6d345a6687b0826a4890c`
- two generations from the same raw trace are byte-identical;
- `passed = false`;
- validation gate: pass;
- observer budget gate: fail;
- timed-intent-available gate: pass.

The repeat completed frames `1..44215` over 14,642 decisions with accepted
route completion, 17 hits, hard no-Bomb, and no residual game/controller
process. The raw 492,656,459-byte trace remains local and ignored; its SHA-256
is `c8d25c8b638794db93c1490a07829658d42bc707d1b65f8c674ec499458dec83`.
The canonical fresh-attempt hit is frame 2,608, classified as an observed
bullet overlap after global viability exhaustion.

## Corrections After The Failed Run

### Issue boundary

CE-0143 showed that the first integration ran optional work before current
input dispatch. Checkpoint `9f5b37c` moves all birth observation,
classification, record construction, and trace emission after the current
action transaction. Post-issue ECL traversal is lookup-only against the
already warmed immutable instruction cache; a cold miss drops the optional
intent instead of issuing RPM.

This protects the current action. It does not prove that optional work cannot
perturb the next cadence, so physical timing remains open.

### Deferred-fire state

Connected IDA decompilation inferred:

- `0x41B4FF`: direct-fire `0x60..0x68` stages the 44-byte descriptor when
  enemy flags `+0x3324` bit `0x20000` is set; otherwise it emits immediately;
- `0x41B878`: opcode `0x6B` sets the bit;
- `0x41B895`: opcode `0x6C` clears the bit;
- `0x41B8E7`: opcode `0x6D` emits the current descriptor.

The existing boss-body guard already reads `+0x3324`, so schema v2 propagates
this observed state without another RPM only when the spell pointer and all
guard/ECL manager-frame endpoints match exactly. Missing, spanned, or
mismatched captures remain unknown. IDA comments were added at all four
addresses.

### Observer data plane

Checkpoint `35f3502` replaces repeated 6.3-MiB strided scans with one state
copy, one age copy, compact double buffers, fixed contiguous scratch, one
ordered candidate scan, and candidate-only geometry gathers. The fixed v2
benchmark reports:

| Platform | Full-pool p95 | Decode ratio | 33-birth p95 | 592-birth p95 |
| --- | ---: | ---: | ---: | ---: |
| Linux | 0.0171 ms | 0.922 | 0.2051 ms | 2.2671 ms |
| Windows | 0.0242 ms | 0.969 | 0.2226 ms | 2.7465 ms |

The steady gate passes and improves over the old `0.0318/0.0339 ms` p95.
The 592-birth output-linear path still exceeds 2 ms, and neither isolated
report reproduces live planner contention. The next trace therefore also
records record-build and pre-emit totals rather than omitting serialization
between extraction and trace emission.

## Authority And Next Gate

The following remain unchanged:

- every future-event coverage slab is `UNKNOWN` from the first successor;
- the observer and intent classifier are trace-only;
- the live Boolean policy and fresh local certificate retain all input
  authority;
- Bomb remains forbidden;
- no B6 conservative birth envelope may be proposed.

The next implementation gate is an equivalent compact/columnar observation
record that removes per-birth Python object and repeated-key construction
without omitting any slot evidence. It must retain an independent scalar
transition oracle, deterministic old/new schema analyzer parity, isolated
Linux/Windows burst benchmarks, complete quick suites, and a third focused
Stage-4A physical report. In parallel, extend the diagnostic report so
main-VM control-flow stops and timed-intent coverage are attributed per phase;
do not call an unmatched edge a classifier error until source ownership is
observed. Stage 5 or 6 follows only after the Stage-4A semantic and performance
gates pass.
