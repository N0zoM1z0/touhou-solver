# G5 Native-Owned Auxiliary-VM Coherence Stage-5 Result

Date: 2026-07-28

Status: v2 implementation, independent scalar/native parity,
cross-platform preflight, and one focused physical Stage-5 spell-107 gate are
complete. The no-retry physical gate is **rejected**: 7 of 235 native-owned
transactions crossed an enemy-manager update boundary. Every timing, cadence,
hard no-Bomb, route, session, and cleanup gate passed. No future-hazard,
source-completeness, planner, feasibility, publication, cadence, or action
authority is added.

The governing contract is
`notes/research/g5/G5_NATIVE_AUXILIARY_VM_OWNED_COHERENCE_CONTRACT_20260728.md`. CE-0165
retains the remaining asynchronous-snapshot counterexample. The physical
workload is `lunatic_route2_stage5_unattended_20260728_193820`.

## Decision

V2 fixes CE-0164's Python/native transport gap:

- no Python owner-frame read or owner-prefix copy remains;
- one native call selects its own capture frame;
- the trigger snapshot is not treated as the expected capture frame;
- all four manager-frame observations are explicit; and
- owner/context state stays fail-closed with caller-owned storage.

Retain those corrections and the v1 context-record semantics. Reject the
no-retry v2 physical delivery claim. Five transactions crossed only at the
final frame after coherent owner/context capture; two crossed while closing
the initial owner copy. This is the expected phase-boundary risk of any
non-pausing external snapshot, not a Python/native gap or a performance tail.

Do not waive the seven attempts, call them skipped, or reinterpret 228 later
successes as a zero-failure gate. The next proposal must be separately
contracted. A bounded at-most-three-attempt transaction is the leading
option, provided every attempt's four frames/status/read count remains
visible, failed attempts publish no state, the final state is versioned at
the selected successful attempt, exhaustion remains failure, and the
unchanged full-transaction timing/cadence limits include all attempts.

Polling for the next frame edge would block post-issue work for up to one
game frame and is not selected. Pausing the shipped process would change
physical cadence and is not authorized.

## Implementation

The trace library adds packed 52-byte `BatchV2` plus:

- `touhou_trace_auxiliary_vm_batch_fixture_v2`; and
- `touhou_trace_auxiliary_vm_batch_process_v2`.

The process entry reads:

`m0 -> 1,373,184-byte owner prefix -> m1 -> m2 -> contexts -> owner rechecks
-> m3`.

It accepts no caller expected frame. `m0` selects the observation version;
`m1`, `m2`, and `m3` must equal it. Maximum logical read count is 837.
`OWNER_CAPTURE_FRAME_MISMATCH` is distinct from the existing inner
before/final mismatch statuses. A diagnostic-count regression found by the
complete suite now preserves the three outer reads even when inner owner
validation stops before its first read.

The Python wrapper allocates the 1,373,184-byte owner buffer, 256 record rows,
2,260,992-byte state payload, and v1/v2 batch outputs once. The v2 service
does not call Python `reader.read` or `reader.u32`; focused tests make either
call fail. It records schema v2 after input issue and retains the decision
snapshot only as trigger metadata.

The strict analyzer accepts retained v1 evidence but requires schema-v2-only
rows for the new physical gate. Native timing now includes the complete
owner-plus-context RPM transaction. No-call exception rows are excluded from
native-call distributions, while end-to-end timing retains every due
attempt.

## Independent And Cross-Platform Validation

The independent scalar v2 composition and native fixture agree on:

- owner-close, context-open, and final frame mismatches;
- depth 0/1/14/15;
- malformed owner/capacity/context/PC/marker/owner churn;
- 64 randomized v2 compositions in addition to the retained 128 v1 cases;
- explicit null rows; and
- the complete 64-owner/256-context/depth-15 bound.

The maximum coherent fixture has 837 logical reads and byte-identical scalar
and native output. Linux and MinGW release builds export all four v1/v2
fixture/process symbols. Warning-strict Linux compilation passes.

The retained v2 1,000-iteration fixture reports pass all required
observed-density cases:

| Platform/workload | End-to-end p95/p99/max ms | Native p95/p99/max ms |
| --- | ---: | ---: |
| Linux, 34 contexts depth 0 | 0.384/0.414/0.627 | 0.008/0.012/0.037 |
| Windows, 34 contexts depth 0 | 0.329/0.355/0.588 | 0.005/0.007/0.258 |
| Linux, 34 contexts depth 15 | 0.501/0.551/0.881 | 0.022/0.031/0.085 |
| Windows, 34 contexts depth 15 | 0.521/0.570/1.075 | 0.019/0.023/0.420 |
| Linux, 256 contexts depth 15 | 3.653/3.922/5.197 | 0.265/0.350/0.473 |
| Windows, 256 contexts depth 15 | 4.192/4.475/4.742 | 0.241/0.361/0.600 |

The last row remains a deliberately non-required materialization stress case
and fails the 2/4-ms end-to-end p95/p99 boundary. Fixture timing excludes
game-process RPM; only the physical result below measures the complete
native-owned transaction.

Report digests are:

- Linux:
  `caadd8b48188d12f9b070e20df6b9da2a34ccf36192fa2524ac0bf8a0979c442`;
- Windows:
  `56530701b3b8609f7a0a9a4192d8d9fd34e2ea385cdeaa23fa66261073ac15d8`.

Complete discovery passes 935 tests on Linux and 935 tests with three
platform skips on Windows.

## Physical Stage-5 Gate

The explicit trace-only run completed frames `2..45403` with 13,586
decisions, twenty hits at
`[1489, 2482, 3544, 3869, 4408, 6958, 11344, 11668, 12321, 13041, 14090,
23701, 24360, 25438, 30612, 31847, 33466, 42019, 42969, 43690]`, hard
no-Bomb, `route_complete`, accepted supervisor/session gates, exact key
release, and no residual game or controller process. The action policy was
unchanged; twenty hits versus the compatible baseline's eight is
RNG/workload evidence, not a causal survival regression.

The strict spell-107 audit observes:

- 235 schema-v2 due attempts: 228 success and 7 rejected;
- batch status zero: 228;
- owner-close mismatch bit `64`: 2;
- final-frame mismatch bit `2`: 5;
- zero context-open mismatch, process-read, capacity, invalid-depth, invalid-
  PC, marker, or unaccompanied owner/context failure;
- 6,634 physically observed non-null contexts, all at depth zero;
- 12,674 explicit null rows;
- four null rows also carry owner-inactive/flags-changed diagnostics inside
  one already final-frame-rejected transaction;
- 1,964 unique active-VM hashes;
- active owners p50/p95/max `16/39/41`;
- non-null contexts p50/p95/p99/max `30/32/34/34`; and
- process reads p50/p95/max `117/134.3/142`.

The exact rejected brackets are:

- owner close:
  `30871->30872` and `33360->33361`;
- final close:
  `30888->30889`, `31946->31947`, `32975->32976`,
  `33135->33136`, and `33549->33550`.

Full native transaction p50/p95/p99/max is
`0.330/0.463/0.584/0.894 ms`, comfortably passing every fixed limit.
Materialization p50/p95/p99/max is
`0.575/1.077/1.275/1.581 ms`; total is
`1.054/1.658/2.156/2.729 ms`. Decision-frame delta remains
p50/p95/p99 `2/4/4`, equal in p95/p99 to the compatible baseline. Hard
no-Bomb, route/transition, session, and cleanup gates pass. The fixed
zero-batch-failure gate fails, so overall `passed: false` is correct.

The strict report digest is
`23313712483c80c3a8323f18f31d19abbf2ed00e3bd2efcf8ef02f9b03712634`.

## Evidence Provenance And Authority

The physical run executed from parent checkpoint `4dec6c2` plus the exact
working-tree changes enclosed by the commit containing this note. The
enclosing commit, run ID, and digests are the checkpoint-to-physical mapping.

The replay-capable raw trace remains local and ignored:

- path:
  `artifacts/runtime_reports/lunatic_route2_stage5_unattended_20260728_193820.jsonl`;
- bytes: `683879277`;
- SHA-256:
  `76472605d19b32b875b33d918527f0e6d13169ba862362451bc0f0ae015d8f13`.

The compatible no-batch baseline remains
`lunatic_route2_stage5_unattended_20260728_171633`, SHA-256
`de697d66bac26ac4ba59185a55c1432249e10111f275299f9c78085d363e78ec`.
The two newest compatible auxiliary-batch raw bundles and compact tracked
reports remain local/retained; no prior bundle was deleted.

This checkpoint proves a corrected one-call transport, bounded useful state,
and the unavoidable no-retry phase-boundary failure. It does not prove
runtime ECL byte identity, future instruction/geometry completeness, hit
causality, robust feasibility, or survival improvement. Unknown or rejected
auxiliary state remains unresolved and cannot be treated as absent, safe, or
losing.
