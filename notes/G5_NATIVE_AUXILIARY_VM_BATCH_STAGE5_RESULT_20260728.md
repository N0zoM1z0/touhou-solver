# G5 Native Auxiliary-VM Batch Stage-5 Result

Date: 2026-07-28

Status: Phase-B v1 scalar/native semantics, cross-platform preflight, and one
focused physical Stage-5 spell-107 gate are complete. The physical gate is
**rejected** because the separate Python owner-pool capture crossed the enemy
manager frame in 9 of 124 due attempts. All 115 batches that reached the
native context transaction passed semantic checks and the native timing gate.
No future-hazard, source-completeness, planner, feasibility, publication,
cadence, or action authority is added.

The governing contract is
`G5_NATIVE_AUXILIARY_VM_BATCH_CONTRACT_20260728.md`. CE-0164 retains the
delivery counterexample. The physical workload is
`lunatic_route2_stage5_unattended_20260728_185838`.

## Decision

Retain the bounded v1 record semantics, independent scalar oracle, native
decoder, compact trace schema, and physical evidence. Reject the v1 physical
delivery composition:

1. Python brackets and copies the 64-record owner prefix;
2. Python enters one native context-capture call; and
3. native independently brackets context and owner rechecks.

The first bracket alone copies about 1.37 MiB and took p50/p95/max
`1.372/1.952/3.215 ms`. Nine captures observed an exact one-frame change
between their before/after reads. Relabeling those attempts as skipped,
waiving the zero-failure gate, or retrying without a new contract would hide
selection and contention rather than solve coherence.

The next proposal is a separately versioned native-owned transport
transaction. One FFI call will read and bracket the owner prefix, derive the
context set from that exact buffer, capture/recheck contexts and owners, and
close the manager bracket. It must use caller-owned fixed buffers, preserve
the v1 fail-closed record semantics, expose every attempted bracket, and pass
the unchanged physical gate before broader capture.

## Revalidated Model

IDA and native-layout review establish:

- auxiliary context `+0x00`: target subroutine;
- context `+0x06`: signed 16-bit call depth, saturating at 15;
- context `+0x08`: active `0x228`-byte VM;
- context `+0x230 + i * 0x228`: physical saved slot `i`;
- allocation `0x24B0 = 0x230 + 16 * 0x228`;
- at most 15 restorable frames, slots `[0, depth)`; and
- a saturated call can write physical slot 15, but the next ordinary return
  restores slot 14.

The capture therefore retains one active VM plus exactly the restorable
frames. It does not mislabel physical slot 15 as a sixteenth restorable
frame. These conclusions were revalidated from instructions and dataflow,
not inherited IDA names or comments.

## Implementation

The trace-only native library now contains a bounded decoder in:

- `native/src/trace/auxiliary_vm_batch_core.hpp`; and
- `native/src/trace/auxiliary_vm_batch.cpp`.

It exports fixture and Windows-process v1 entries. Packed record/batch rows
are 52/44 bytes. The fixed capacities are 64 owners, 256 pointer rows, and
2,260,992 payload bytes. Address arithmetic, capacities, depth, active and
saved PCs, auxiliary marker, context prefix, owner flags/pointers, and
manager brackets fail closed. One bad non-null row makes the whole batch
publish zero usable contexts. The Windows process entry is explicitly
unsupported on Linux.

The independent Python scalar oracle and ctypes boundary live under
`scripts/th08_live/auxiliary_vm/`. The wrapper allocates records and payload
once, holds the GIL by default, and materializes outside the native timing
boundary. `trace_service.py` owns the default-off once-per-16-manager-frame,
spell-filtered, post-issue service. The long live controller only constructs
and invokes that service; auxiliary decoding and trace construction are not
embedded in the controller.

`scripts/analysis/auxiliary_vm_batch_trace.py` streams the raw trace, rejects
schema/authority/coherence errors, compares decision cadence with a compatible
baseline, and reports native-call timing only for rows that actually entered
native code. `scripts/benchmarks/benchmark_auxiliary_vm_batch.py` retains
cross-platform fixture parity and timing.

## Independent And Cross-Platform Validation

The scalar/native fixture suite covers deterministic depth 0/1/15 cases,
nulls, invalid depth/PC/marker, prefix and owner churn, frame changes,
unreadable/capacity failures, 128 randomized cases, and the full
64-owner/256-context/depth-15 bound. Linux and MinGW release builds pass and
export both v1 entries. Warning-strict Linux compilation passes.

The retained 1,000-iteration-per-case reports are:

| Platform/workload | End-to-end p95/p99/max ms | Native p95/p99/max ms |
| --- | ---: | ---: |
| Linux, 34 contexts depth 0 | 0.355/0.386/0.635 | 0.008/0.009/0.037 |
| Windows, 34 contexts depth 0 | 0.353/0.366/0.685 | 0.006/0.006/0.024 |
| Linux, 34 contexts depth 15 | 0.489/0.523/0.708 | 0.023/0.029/0.072 |
| Windows, 34 contexts depth 15 | 0.594/0.640/1.107 | 0.018/0.020/0.054 |
| Linux, 256 contexts depth 15 | 3.567/4.561/19.192 | 0.267/0.366/0.447 |
| Windows, 256 contexts depth 15 | 4.331/4.608/5.304 | 0.254/0.373/0.730 |

The observed-density and 34-context maximum-depth required preflight cases
pass. The deliberately non-required 256-context/depth-15 end-to-end stress
case fails p95/p99 on both platforms and Linux maximum; the native call
itself remains within the physical native-call limits. This distinction is
retained rather than representing the theoretical maximum as a passing live
workload.

Report digests are:

- Linux:
  `e3a0472eefb56d33ad996e805785607ecb34078f79bf75b4c406f9e8f3444b2f`;
- Windows:
  `2113b412c3bdebf692c7c3e59e6a32ab8c826f624ffb694a9499ec066676c912`.

Complete deterministic discovery passes 933 tests on Linux and 933 tests
with three platform skips on Windows.

## Physical Stage-5 Gate

The explicit trace-only run completed frames `1..41601` with 12,216
decisions, ten hits at
`[1490, 2041, 4021, 10980, 11634, 12330, 29670, 36941, 38218, 40914]`,
hard no-Bomb, `route_complete`, accepted supervisor/session gates, exact key
release, and no residual game or controller process. The batch was enabled
only for spell 107, after input issue, once per 16 changed manager frames.
The live action policy was unchanged; ten hits versus the compatible
baseline's eight is not a causal performance conclusion.

The strict batch audit observes:

- 124 due attempts: 115 success and 9 `owner_frame_changed`;
- the nine owner brackets changed by exactly one frame:
  `28818->28819`, `29361->29362`, `29475->29476`,
  `29532->29533`, `29970->29971`, `30147->30148`,
  `30642->30643`, `30899->30900`, and `31122->31123`;
- 115/115 native batch statuses equal zero;
- 3,028 usable non-null records with status zero and 5,848 explicit null rows;
- zero invalid depth, PC, marker, context, owner, frame, capacity, or native
  failure after native entry;
- all 3,028 physically observed call depths are zero, so nonzero-depth
  authority remains fixture-only;
- 1,022 unique active-VM hashes;
- active owners p50/p95/max `16/40/41`;
- usable contexts p50/p95/p99/max `30/32/34/34`;
- state payload p50/p95/max `16,560/17,664/18,768` bytes; and
- native process reads p50/p95/max `114/132.3/139`.

Native call p50/p95/p99/max is
`0.118/0.154/0.185/0.301 ms`, passing every fixed timing limit.
Owner-capture p50/p95/p99/max is
`1.372/1.952/2.299/3.215 ms`; total p50/p95/p99/max is
`2.219/2.964/3.534/3.894 ms`. Decision-frame delta remains
p50/p95/p99 `2/4/4`, equal to the compatible baseline. Hard no-Bomb,
route/transition, session, and cleanup gates pass. The precommitted
zero-coherence-failure gate fails, so the overall report correctly has
`passed: false`.

The strict report digest is
`440bf0ba3c653714a0b53a17f98c2413e5f592ebe85ac7e709b011901ab5bc18`.

## Evidence Provenance And Authority

The physical run executed from parent checkpoint `997335b` plus the exact
working-tree changes enclosed by the commit containing this note. The
enclosing commit, run ID, and digests are the checkpoint-to-physical mapping.

The replay-capable raw trace remains local and ignored:

- path:
  `artifacts/runtime_reports/lunatic_route2_stage5_unattended_20260728_185838.jsonl`;
- bytes: `583565067`;
- SHA-256:
  `734878ffe0bfe891767621971b8d220ec2f5c4108d516a4776a2396f6e0a6927`.

The compatible baseline is
`lunatic_route2_stage5_unattended_20260728_171633`, SHA-256
`de697d66bac26ac4ba59185a55c1432249e10111f275299f9c78085d363e78ec`.
Both replay-capable bundles and their compact tracked reports remain
retained; no prior bundle was deleted.

This checkpoint proves implementation parity, bounded useful physical state,
and a specific delivery failure. It does not prove runtime ECL byte identity,
future instruction/geometry completeness, hit causality, robust feasibility,
or survival improvement. Unknown auxiliary state remains unresolved and
cannot be treated as absent, safe, or losing.

The proposed native-owned v2 transaction was subsequently implemented and
physically rejected under its no-retry gate in
`G5_NATIVE_AUXILIARY_VM_OWNED_COHERENCE_STAGE5_RESULT_20260728.md`. It fixes
CE-0164's Python/native gap but exposes CE-0165 at the asynchronous game-frame
boundary.
