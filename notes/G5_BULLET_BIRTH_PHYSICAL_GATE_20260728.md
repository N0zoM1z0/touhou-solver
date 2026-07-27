# G5 Bullet-Birth Physical Gate

Date: 2026-07-28

Status: B4/B5 failed with retained evidence. The current issue transaction is
now isolated and the omitted deferred-fire source state is corrected offline,
but CE-0143 physical performance and a schema-v2 runtime join still require a
focused repeat. No future-hazard or physical action authority is granted.

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

Repeat Lunatic Stage 4A from checkpoint `35f3502` or later with schema v2.
Require accepted completion, hard no-Bomb, exact deferred-state status counts,
timed intent sightings, deterministic B5 output, observation/build/emit tails,
and explicit unmatched residuals. Stage 5 or 6 follows only after this
Stage-4A semantic gate passes.
