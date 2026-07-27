# Stationary Witness Windows Delivery Gate

Date: 2026-07-28

Status: offline Windows delivery gate passed twice with the fixed P-core
isolation variant; no consumer or physical action authority

Implementation checkpoint: `f8621bd`

Formal contract:
`STATIONARY_WITNESS_WINDOWS_DELIVERY_CONTRACT_20260728.md`

## Result

**Observed:** a research-only DLL and modular Python service now measure the
internal native stationary witness in the same Windows process without adding
to the production ABI. For one immutable physical root, the service:

- creates one private native belief workspace;
- completes and decodes all 36 no-Bomb root actions;
- checks every root label against the independent Python scalar portfolio;
- structurally replays every returned stationary path;
- publishes only a complete, newest, exact-identity immutable record;
- cancels an active superseded workspace; and
- destroys all workspaces before shutdown.

The final resource boundary leaves the normal-priority authoritative
four-worker viability solve unchanged. The one optional below-normal witness
thread is pinned to logical CPU 11, the highest logical CPU in Windows'
maximum efficiency class. Process affinity and authoritative worker affinity
are unchanged.

Two consecutive complete P-core runs passed every precommitted condition:

| Metric | P-core run 1 | P-core run 2 | Fixed gate |
| --- | ---: | ---: | ---: |
| physical jobs complete | 162/162 | 162/162 | >= 95% |
| publication p95 | 6.913 ms | 6.203 ms | <= 8.000 ms |
| publication max | 11.358 ms | 7.977 ms | < 16.667 ms |
| viability p95 ratio | 1.034 | 0.938 | <= 1.10 |
| viability throughput ratio | 0.929 | 0.961 | >= 0.90 |
| active cancellation count | 59 | 54 | >= 1 |
| cancellation ack p95 | 0.164 ms | 0.168 ms | <= 2.000 ms |
| cancellation ack max | 3.184 ms | 2.359 ms | <= 5.000 ms |
| stale/partial publication | 0/0 | 0/0 | 0/0 |
| production ABI | 46/46 exact | 46/46 exact | unchanged |

This passes only the offline delivery/contention gate. It permits a separate
review of a default-off trace-only shadow consumer. It does not authorize a
consumer, action ranking, issue-time work, or physical input.

## Fixed Physical Reservoir

The source is physical Lunatic Stage-4A run
`lunatic_route2_stage4a_unattended_20260728_005108`, raw trace SHA-256:

```text
93037d9febe609accd44eb150150088c29610443783a4434328478409fee41b0
```

The exact reservoir rule selected 18 unique roots:

- the first eight accepted Boolean-empty roots; and
- the last accepted Boolean-empty root strictly before each of the ten
  physical hit frames.

The trace reader accepted 12,986 canonical root/capsule joins, retained 5,896
Boolean-empty roots, reported the 1,613 historical CE-0141 mixed-root rows,
and found zero missing selected capsules. Every selected root used horizon 32,
recursive cadence support `(4,5,6)`, all 36 no-Bomb complete-mask actions,
and the exact held desired mask as the stationary continuation.

Raw trace parsing, capsule I/O, lowering, and independent Python portfolio
construction were reported as preparation and excluded from the publication
clock. Workspace creation, native extraction, numeric path decoding, scalar
label/path validation, workspace cleanup, and publication-lock acquisition
were inside the clock.

## Exploration And Rejections

The thresholds were fixed in checkpoint `b5efb5b` before measurement. They
were not relaxed after failures.

| Variant | Publication p95 | Viability p95 ratio | Throughput ratio | Result |
| --- | ---: | ---: | ---: | --- |
| pre-optimization | 9.400 ms | 1.165 | 0.894 | rejected |
| component-profile repeat | 9.247 ms | 0.753 | 1.001 | rejected: publication |
| numeric decode, unpinned | 6.235 ms | 0.978 | 0.927 | passed once |
| numeric decode, unpinned repeat | 6.522 ms | 1.557 | 0.927 | rejected: viability tail |
| logical CPU 19 E-core | 12.156 ms | 0.978 | 0.963 | rejected: publication |
| logical CPU 11 P-core | 6.913 ms | 1.034 | 0.929 | passed |
| logical CPU 11 P-core repeat | 6.203 ms | 0.938 | 0.961 | passed |

The component profile localized the initial miss. On the hardest physical
root, constructing hundreds of keyword-based Python step objects cost about
as much as the native recurrence. The final delivery record stores the same
23 fields as positional immutable numeric tuples. The research binding
converts action indices only when validation needs them. Native extraction
also writes directly to the caller's complete output buffer instead of
allocating and copying a second step vector. Neither change alters the
recurrence or public ABI.

Pinning to the highest visible logical CPU was not sufficient on this hybrid
processor: CPU 19 is an E-core. The explicitly measured E-core variant
stabilized authoritative viability but made the witness too slow. Windows
CPU-set evidence showed CPUs 0–11 in efficiency class 1 and CPUs 12–19 in
class 0. The final deterministic selector chooses the highest logical CPU in
the maximum efficiency class, CPU 11 on this host.

## CE-0142: Equivalent Hidden Tie Paths

**Observed:** physical decision/query/source `612/611/598`, identity
`8eb661e12d6ab81709ac91bca1a58c3dbf293227828b49ecfd1412af0ffef5cc`,
root action `th08_mask_54`, produced one equal-label path tie:

- native step 1 selected pickup delay 2;
- Python selected pickup delay 4;
- both used cadence 6, reached the same merged successor and retained the
  same guaranteed frames;
- native prefix margin was `0x1.3cd5220000000p+4`;
- scalar prefix margin was `0x1.3cd522339908fp+4`; and
- root bottleneck margins differed by one float32 ULP and remained inside the
  established `1e-5` parity tolerance.

This falsifies exact hidden tie-field equality on physical coordinates. It
does not falsify the label recurrence or either path. The gate therefore
requires exact guaranteed frames, margin tolerance, declared action/delay/
cadence membership, no-write semantics, state links, nested-label recurrence,
and complete path replay. It separately counts deterministic scalar/native
tie divergence: two action paths per occurrence of that root, 18 in each
nine-round final contention run.

## Evidence

The two accepted reports are:

- `artifacts/benchmarks/stationary_witness_windows_delivery_pcore_affinity_20260728.json`
  - report digest
    `ed9f60d8ce46c834bca54263d2c1ce03d3c9ddb377f597a91864ba896e71e11f`
  - file SHA-256
    `fda6a1a0997e30cf5bbe73b58c18cfe7ca7a9cfc464566b12a68f6d8eb8acd88`
- `artifacts/benchmarks/stationary_witness_windows_delivery_pcore_affinity_repeat2_20260728.json`
  - report digest
    `8e6c03a0b6221b5bf984b070762c25789ce8275940d93e83ebb248cac23ddb0b`
  - file SHA-256
    `10868c9595804bf7b4c4f39d9ee9223abd14e8816b83356dd202e1cbdc5556f7`

Rejected and intermediate reports are retained beside them so later work
cannot erase the scheduler and E-core counterexamples.

Linux and Windows quick suites pass `740/740` in `8.926/14.797 s`; Windows
has the three existing platform skips. Linux and Windows production binaries
match the checked-in sorted 46-symbol manifest exactly.

## Remaining Authority Gaps

Before any action authority:

1. recheck CE-0141 on a post-fix physical trace;
2. replace first-successor `UNKNOWN` future-event coverage with physical
   coverage or a conservative truncation;
3. close or explicitly contain CE-0120's frozen manager-clock boundary;
4. implement and separately review an earlier-version, default-off,
   trace-only shadow service;
5. prove real completion age and exact lookup from that earlier immutable
   version without sharing live publication or issue workers;
6. retain a fresh local hard intersection at consumption; and
7. run focused physical shadow evidence before any strategy-ledger promotion.

Timeout, cancellation, missing versions, and lookup misses remain unresolved
delivery states and fall back without starting cold issue-thread work.
