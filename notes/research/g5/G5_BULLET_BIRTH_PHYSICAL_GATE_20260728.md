# G5 Bullet-Birth Physical Gate

Date: 2026-07-28

Status: the first six retained B4 attempts failed. Schema v6 attributed the
remaining tail to the native-call wall interval with no overlapping cyclic
GC. Two subsequent schema-v7 native `gil-held` Stage-4A runs pass every B4
limit over 28,907 observations with zero sample above 2 ms, closing this
specific native-call mechanism at that checkpoint. Schema v8 later reopened
B4 with a materialization tail. Schema v9 physically correlates all three
corridor Future completion transitions with the three largest
materialization walls and still fails p95/max, so B4 is currently open.
Callback unknown-suffix and omitted-source coverage remain open. No
future-hazard or physical action authority is granted.

## Outcome

Current retained status is detailed in
`notes/research/g5/G5_MATERIALIZATION_TAIL_PHYSICAL_ATTRIBUTION_20260728.md`: schema-v9 run
`20260728_083433` completes 13,842 native observations but fails B4 at
p95/max `0.2039/5.1274 ms`. The only three ambiguous endpoint rows are
corridor Future `inflight -> done`, exactly matching the three largest
materialization walls. Worker intervention remains unauthorized pending a
separate publication-age/contention contract.

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

The schema-v3 repeat
`lunatic_route2_stage4a_unattended_20260728_043724` validates the corrected
data path but still fails B4:

- all 6,101 active-spell main-VM rows produced a classifier result; the old
  2,386 zero-byte-read callback errors are absent;
- 2,148 timed intent sightings form 97 deduplicated events; unique temporal
  support matches increase to 5,989/99,937 activation edges (5.9928%),
  including 3,054 matches in spell 61 and 2,935 in spell 69;
- observer p95/p99/max improves again to
  `0.3413/0.6625/10.6158 ms`, but the unchanged gate remains
  `0.20/0.40/2.00 ms`;
- zero-evidence observer p95 is `0.1960 ms`, while non-empty buckets have
  p95 `0.3987..0.4626 ms`; scheduler/cold-buffer cost remains material;
- prior-record emit p95 is only `0.0724 ms` after a zero-evidence row but
  `1.3307..1.9791 ms` for non-empty rows because the controller immediately
  flushes every evidence record before the same-iteration decision flush;
- spell 57 reaches the 256-instruction callback-lookahead cap on all 1,261
  rows, scanning 322,816 instructions with zero reported events and without
  horizon coverage. Empty events are therefore not a complete no-callback
  certificate.

The schema-v4 repeat
`lunatic_route2_stage4a_unattended_20260728_050305` validates the flush
correction but again fails B4:

- previous birth-record emit p95 falls from `1.1783` to `0.1708 ms`;
  after 1..8 and 9..32 evidence rows it falls from `1.3307/1.3777` to
  `0.1009/0.1839 ms`;
- the remaining synchronous columnar JSON encode/write is still
  output-linear: the 321+ bucket has only 12 samples but p95/max is
  `5.3563 ms`;
- observer wall p95/p99/max improves to
  `0.2997/0.5772/10.2234 ms`, still above the unchanged
  `0.20/0.40/2.00 ms` limits;
- current-thread CPU samples are quantized at 15.625 ms on this Windows
  runtime, so they cannot separate sub-millisecond execution from scheduler
  delay and cannot substitute for the wall gate;
- all 6,008 active-spell rows classify. There are 2,114 timed sightings,
  103 deduplicated events, and 6,023 unique temporal supports over 95,532
  activation edges (6.3047%);
- every one of 1,330 spell-57 rows again reaches the 256-instruction callback
  cap without horizon coverage, independently reproducing CE-0147.

The explicit native schema-v5 repeat
`lunatic_route2_stage4a_unattended_20260728_055104` materially improves the
physical distribution but still fails B4:

- all 14,643 audit rows record `observation_backend=native`, with zero
  observation or intent errors;
- observer wall p50/p95/p99/p99.9/max is
  `0.0545/0.1393/0.2111/2.3779/9.0498 ms`; p95 and p99 pass the unchanged
  limits for the first time, but maximum remains above `2.00 ms`;
- 16 observations exceed `2.00 ms`; ten have zero evidence and the other six
  have only 4, 6, or 20 rows. This rejects 592-birth output-linear copying as
  an explanation for the remaining tail;
- all 16 tail samples report zero current-thread CPU because the same
  15.625-ms accounting quantum remains unresolved. The trace cannot yet
  distinguish a native call stall, Python materialization/GC, or scheduler
  preemption;
- previous birth-record emission p95/p99/max is
  `0.1723/1.1804/3.5352 ms`; same-iteration durability remains intact, but
  large-record serialization is still separate post-issue work;
- validation and timed-intent gates pass. There are 1,980 timed sightings,
  62 deduplicated events, and 5,944 unique temporal supports over 95,410
  activation edges (6.2300%);
- all 1,339 spell-57 rows again stop at the 256-instruction callback limit
  without horizon coverage.

The schema-v6 attribution repeat
`lunatic_route2_stage4a_unattended_20260728_062321` resolves the tail segment
but still fails B4:

- all 14,868 rows use schema v6 and explicit native provenance with zero
  observation or intent errors;
- observer p50/p95/p99/p99.9/max is
  `0.0648/0.1493/0.2245/2.1568/8.3514 ms`; p95 and p99 pass, maximum fails;
- all 17 observations above `2.00 ms` are dominated by native-call wall time;
  its p50/p95/p99/p99.9/max is
  `0.0365/0.0603/0.1125/2.1281/8.2585 ms`;
- prepare, materialization, and controller-residual maxima are only
  `0.0703/0.7076/0.2362 ms`;
- completed GC counts are zero for every phase and generation over all
  observations, so Python materialization and cyclic GC are rejected as the
  next correction target;
- 2,193 timed sightings form 120 deduplicated events and 5,925 unique
  temporal supports over 96,984 activation edges (6.1093%);
- all 1,324 spell-57 rows again hit the 256-instruction callback limit.

The native-call interval was observed; a Windows scheduler/preemption cause
was not. GIL-release interference was the bounded inference that motivated
the controlled GIL-held/released experiment.

The schema-v7 `gil-held` correction then passes twice:

- run `20260728_065316` completes 13,896 observations with
  p50/p95/p99/p99.9/max `0.0659/0.1475/0.2021/0.4001/1.0595 ms`,
  native-call maximum `0.5008 ms`, and zero sample above 2 ms;
- run `20260728_070838` completes 15,011 observations with
  p50/p95/p99/p99.9/max `0.0632/0.1420/0.1967/0.3999/0.9087 ms`,
  native-call maximum `0.4384 ms`, and zero sample above 2 ms;
- both runs retain native/`gil-held` provenance, validation, timed intent,
  hard no-Bomb, cadence, supervisor completion, accepted artifacts, cleanup,
  and zero completed cyclic-GC collections; and
- the two runs have 9 and 15 hits respectively. They are not controlled
  survival comparisons, and all 24 contacts follow global viability
  exhaustion.

This closes B4 for the declared retrospective observer boundary. It does not
close CE-0147, narrow first-successor `UNKNOWN`, or grant future geometry or
input authority.

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

The schema-v4 repeat report is:

- `artifacts/runtime_reports/lunatic_route2_stage4a_unattended_20260728_050305.birth_audit.json`
- SHA-256
  `bcd153b041c046ca1047181b62becdc8f144fc95a42076c94610576bbf23105e`;
- two generations from the same raw trace are byte-identical;
- `passed = false`;
- validation gate: pass;
- observer budget gate: fail;
- timed-intent-available gate: pass.

The run completed frames `2..44273` over 14,394 decisions with accepted
route completion, 12 hits at
`1743, 4261, 11456, 12075, 12924, 19000, 21350, 22433, 30479, 36975,
38631, 43525`, hard no-Bomb, supervisor completion, and no residual
game/controller process. The ignored 488,428,485-byte raw trace SHA-256 is
`cf5161cf34209fd44be85c177ddaf89c5cee7c3bb73be6103f95296a8c834a9f`.
The canonical fresh-attempt contact at frame 1,743 is an observed bullet
overlap after global viability exhaustion.

The schema-v5 native repeat report is:

- `artifacts/runtime_reports/lunatic_route2_stage4a_unattended_20260728_055104.birth_audit.json`
- canonical LF SHA-256
  `1689bf8468b9129b16aaf1aeacee7b569975a4302a92ab7860ef77c4665a84ec`;
- two generations from the same raw trace are byte-identical;
- `passed = false`;
- validation gate: pass;
- observer budget gate: fail on maximum only;
- timed-intent-available gate: pass.

The exact command added `--bullet-birth-backend native` to the retained
Stage-4A trace invocation at code checkpoint `bc57168`. The run completed
frames `2..45092` over 14,643 decisions with accepted route completion, 13
hits at
`1487, 2360, 4491, 8991, 10451, 11611, 12215, 12803, 13822, 21964,
22714, 27323, 31202`, hard no-Bomb, supervisor completion, and no residual
game/controller process. The ignored 510,433,900-byte raw trace SHA-256 is
`ed4fbbb932e12ac7ef7f3e4b560fad1fa7dc8b0428c712edc5a02ec1c09b7a79`.
The canonical first hit at frame 1,487 is a modeled committed-prefix
collision after global viability exhaustion. Across the run, six hits are
observed bullet overlaps, five are modeled committed-prefix collisions, and
two are observed enemy-body overlaps.

The schema-v6 attribution repeat report is:

- `artifacts/runtime_reports/lunatic_route2_stage4a_unattended_20260728_062321.birth_audit.json`
- canonical LF SHA-256
  `c0e71b3660651e11e15e3a924bef0d1f22adc49a3513bbc7ab39b83528d3e008`;
- two generations from the same raw trace are byte-identical;
- `passed = false`;
- validation gate: pass;
- observer budget gate: fail on maximum only;
- timed-intent-available gate: pass.

At checkpoint `200c259`, the run completed frames `1..45170` over 14,868
decisions with accepted route completion, 17 hits at
`1255, 2725, 3986, 4346, 9849, 11689, 12084, 12736, 21864, 22323, 30066,
30711, 31907, 35498, 37755, 38928, 39662`, hard no-Bomb, supervisor
completion, and no residual process. The ignored 483,475,546-byte raw trace
SHA-256 is
`9f075f795327e6e1669b2cf18e0cfd28656a87ced1212cddf2ff3157b0dacc30`.
The canonical first hit at frame 1,255 is a modeled committed-prefix
collision after global viability exhaustion. Across the run, eight hits are
observed bullet overlaps, seven are modeled committed-prefix collisions, one
is an observed enemy-body overlap, and one is a sensor-gap or unmodeled
hazard.

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

### Columnar trace representation

Checkpoint `70077e2` makes the schema-v3 observer retain candidate slots,
transition/status codes,
current/previous state and age, six geometry values, transform flags, and
finite flags in read-only columns. Scalar `BulletBirthEvidence` objects are
materialized only when a test or reviewer indexes one witness. Trace
publication converts the columns directly to compact JSON; it does not omit,
sample, aggregate, or reorder candidates.

The independent 16-generation/all-1,536-slot scalar transition oracle still
passes. The residual analyzer accepts schema v1/v2 row objects and schema v3
columns, validates every column and code, and has an explicit v2/v3 semantic
parity test.

| Platform | Births | Observer p95 before/after | Record+JSON p95 before/after | JSON bytes before/after |
| --- | ---: | ---: | ---: | ---: |
| Linux | 33 | 0.2270 / 0.1004 ms | 0.1335 / 0.0940 ms | 9,007 / 2,071 |
| Linux | 592 | 2.4100 / 0.1704 ms | 2.3496 / 0.7763 ms | 160,077 / 32,956 |
| Windows | 33 | 0.2300 / 0.0941 ms | 0.1192 / 0.0857 ms | 9,007 / 2,071 |
| Windows | 592 | 2.5376 / 0.1528 ms | 2.3570 / 1.0727 ms | 160,077 / 32,956 |

The isolated 592-birth extraction gate now passes on both platforms and the
payload is 79.4% smaller. Record serialization remains separately measured
post-issue work; only another physical run can decide whether Windows
scheduler and file-write tails pass B4.

### Main-VM capture/classifier coupling

The enhanced deterministic source report attributes every audit/classifier
row and callback-lookahead error by phase. It identified 2,386 rows with:

```text
ValueError: process read buffer size must be positive
```

The ECL cache accepted the legal 12-byte instruction size, then still called
the Windows reader for a zero-byte payload. The broad controller exception
handler subsequently erased an already successful VM snapshot together with
the failed callback classification. This accounted for every active-main-VM
row in spells 61 and 65, plus 439 rows across spells 57, 69, and 73.

The parser now maps a zero-length payload to `b""` without an RPM. Main-VM
capture is an independently tested `th08_live.ecl_capture` seam: callback
lookahead failure keeps the observed snapshot for post-issue birth
classification while callback events remain empty/fail-closed. A strict
reader fixture rejects every non-positive read. This may restore callback
hazard events as well as diagnostic coverage, so physical geometry/action
effects remain unpromoted until the next Stage-4A run.

The schema-v3 run physically validates that correction: spells 57/61/65/69/73
retain `1261/1307/1051/1389/1093` classifier rows with no callback read error.
Spell 61 now contributes 434 timed sightings and 3,054 temporal birth
matches. This closes the specific snapshot-loss defect, not the omitted
source, geometry, or callback-horizon problem.

## Authority And Next Gate

The following remain unchanged:

- every future-event coverage slab is `UNKNOWN` from the first successor;
- the observer and intent classifier are trace-only;
- the live Boolean policy and fresh local certificate retain all input
  authority;
- Bomb remains forbidden;
- no B6 conservative birth envelope may be proposed.

The fourth and fifth runs are valid physical correction gates, not controlled
survival comparisons. Their 12 and 13 hits are RNG-, density-, phase-,
resource-, and trajectory-distinct. The schema-v5 run is one hit worse than
schema v4 and does not support a survival-improvement claim. Every contact in
both runs followed global viability exhaustion. Schema-v5 decision cadence
remains 2 frames median and 3 frames p95, while next-observation input
visibility is 0.9311 versus 0.9388 in schema v4.

The bounded flush and native extraction changes are retained. Thread CPU
timing remains rejected as a useful Windows sub-millisecond diagnostic. The
two consecutive `gil-held` physical runs close the wall gate under the
declared boundary.

That diagnostic was implemented under
`notes/research/g5/G5_NATIVE_BIRTH_TAIL_ATTRIBUTION_CONTRACT_20260728.md`. Schema v6 and
residual-audit v4 pass focused validation and complete Linux/Windows suites.
CE-0150 rejects the old block-ordered decode ratio; ABBA-paired Linux and two
adjacent Windows runs pass at `1.0123/1.0156/1.0248` while all isolated
observer profiles remain inside the fixed limits. The physical repeat now
observes a collection-free native-call wall tail. Therefore the next
correction gate is an explicit GIL-held/released call-boundary comparison,
not another Python materialization rewrite. It must preserve the same native
recurrence and output, independent Python oracle, GC, unpinned controller,
same-iteration durability, no added RPM, default-off/no-action authority, and
fixed maximum.

That experiment is now implemented and fixed by
`notes/research/g5/G5_NATIVE_BIRTH_GIL_BOUNDARY_EXPERIMENT_20260728.md`. Mode-specific
`CDLL`/`PyDLL` loaders, schema-v7 provenance, exact three-way parity, all
fixed Linux/Windows observer profiles, ABBA decode ratios, and complete
`801/801` suites pass.

The first held run `20260728_065316` passes all B4 limits over 13,896
observations: p50/p95/p99/p99.9/max is
`0.0659/0.1475/0.2021/0.4001/1.0595 ms`; native-call maximum is
`0.5008 ms`, no observation exceeds 2 ms, and no completed GC overlaps a
phase. The run completed frames `2..43253`, 9 hits, hard no-Bomb, accepted
artifacts, and cleanup. CE-0151 fixed a report-only schema-v7 aggregation
omission before publication.

The second held run `20260728_070838` passes all B4 limits over 15,011
observations: p50/p95/p99/p99.9/max is
`0.0632/0.1420/0.1967/0.3999/0.9087 ms`; native-call maximum is
`0.4384 ms`, no observation exceeds 2 ms, and no completed GC overlaps a
phase. It completed frames `2..45454`, 15 hits, hard no-Bomb, accepted
artifacts, and cleanup. The two consecutive passes close B4 over 28,907
observations, but do not establish survival improvement or future-event
authority.

In parallel, callback lookahead must expose an explicit incomplete result; an
instruction-limit row cannot authorize an empty future event set. Stage 5 or
6 follows only after Stage-4A semantics and performance pass.
