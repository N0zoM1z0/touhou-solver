# G5 Native-Owned Auxiliary-VM Coherence Contract

Date: 2026-07-28

Status: fixed before v2 implementation. This contract corrects CE-0164 with
one versioned native-owned owner/context capture transaction. It authorizes
only an explicit default-off, post-issue, trace-only experiment. It grants no
future-hazard, source-completeness, planner, feasibility, publication,
cadence, or action authority.

This contract follows
`notes/research/g5/G5_NATIVE_AUXILIARY_VM_BATCH_CONTRACT_20260728.md` and its rejected physical
result. The v1 scalar/native record semantics remain the reference for
context decoding. Only physical transport ownership and bracket evidence
change in v2.

Implementation and the rejected no-retry physical gate are retained in
`notes/research/g5/G5_NATIVE_AUXILIARY_VM_OWNED_COHERENCE_STAGE5_RESULT_20260728.md`.
CE-0165 supersedes the assumption that one asynchronously started bounded
transaction will always fit between game updates; the contract remains the
historical preimplementation falsifier.

## Physical Objective And Falsifier

The physical objective remains hard no-Bomb survival. This experiment asks:

> Can one native call capture the first-64 ordinary-enemy owner prefix and
> every selected auxiliary context under one explicitly observed,
> unchanged enemy-manager frame, within the existing physical timing and
> cadence limits?

CE-0164 observed nine frame changes across the separate Python owner-prefix
copy. V2 passes only if a focused Stage-5 spell-107 run has:

- zero owner-capture, manager-bracket, context, owner, capacity, or native
  failure;
- full native transaction p95 `<= 2.0 ms`, p99 `<= 4.0 ms`, and max
  `<= 12.0 ms`;
- decision-cadence p95 no more than one frame worse than the compatible
  no-batch baseline; and
- hard no-Bomb, route, transition, key-release, and cleanup success.

Every due attempt remains visible. A failed attempt cannot be relabeled as a
skip, hidden by a later success, or retried inside native. Later scheduled
attempts may measure the failure rate, but the fixed zero-failure physical
gate remains failed.

## Scheduling And Observation Time

The decision's `enemy_manager_frame` is a **trigger observation only**. It
determines the once-per-16-changed-observed-manager-frame schedule. It can be
one or more frames older than the post-issue capture and is not an expected
capture frame.

After native entry, the transaction reads its own first manager frame `m0`.
That value selects the candidate observation version. No caller-supplied
expected frame is accepted by the v2 process ABI.

`enemy_manager_frame` remains only an enemy-source coherence guard. It is not
an input clock, wall-time clock, or controller-cadence automaton. CE-0120 and
CE-0121 remain open.

## Fixed Native Read Schedule

One v2 process call performs exactly this ordered schedule:

1. read the manager frame as selected frame `m0`;
2. read the complete declared first-64 owner prefix into a caller-owned
   reusable buffer;
3. read owner-capture closing frame `m1` and require `m1 == m0`;
4. read context-transaction opening frame `m2` and require `m2 == m0`;
5. derive active owners and four auxiliary pointers only from the captured
   owner buffer;
6. for each non-null context, read prefix, active/restorable payload, and
   prefix recheck exactly as v1;
7. reread flags and all four pointers for each selected active owner; and
8. read final manager frame `m3` and require `m3 == m0`.

The output exposes `m0`, `m1`, `m2`, and `m3` separately. A read failure
retains every frame already observed and a deterministic read count. Any
frame inequality, process-read failure, or v1 batch/record failure publishes
zero usable contexts.

There is no internal retry, alternate owner copy, per-context Python process
read, or full `0x24B0` copy. The residual exact-address ABA uncertainty from
v1 remains declared; equal frame/header/owner bits do not prove an impossible
same-address destroy/recreate cycle.

## State And Information Contract

For each active owner, v2 emits four ordered metadata rows, including explicit
null rows. Every non-null row retains the unchanged v1 evidence:

- slot, enemy pointer, auxiliary index, context pointer;
- owner flags and pointer before/after evidence;
- target subroutine and signed depth;
- complete active `0x228` VM;
- exactly `depth` restorable saved frames, slots `[0, depth)`;
- auxiliary-owner marker; and
- context prefix/active-PC recheck.

Depth remains `0..15`; the 16th physical saved slot is not a 16th restorable
frame. Active and saved PCs, marker, capacities, ranges, and arithmetic retain
the v1 fail-closed checks.

Two physical histories map to one successful v2 observation only when their
four manager-frame values, owner rows, retained context bytes, and all
published metadata are equal. This is sufficient for the declared captured
enemy-source state, subject to the stated ABA and omitted-source uncertainty.
It is not equivalence for the full game, input pipeline, or future hazard.

## Versioned ABI

The trace library adds:

- `touhou_trace_auxiliary_vm_batch_fixture_v2`, which accepts independently
  supplied owner/context bytes and four manager frames while reproducing the
  logical v2 read count; and
- `touhou_trace_auxiliary_vm_batch_process_v2`, which accepts a process
  handle, pool/layout parameters, caller-owned owner/record/payload buffers,
  and one packed v2 batch output.

The process ABI has no expected-manager-frame input.

Records retain packed 52-byte `RecordV1`. Packed `BatchV2` is 52 bytes and
contains:

- status bits;
- selected frame `m0`;
- owner-closing frame `m1`;
- context-opening frame `m2`;
- final frame `m3`;
- process-read count and owner-blob byte count;
- active-owner, record, non-null, and usable counts; and
- usable state-payload bytes.

V2 adds one explicit owner-capture-frame-mismatch batch status. Invalid ABI
pointers return `-1`; readable semantic/capacity/platform failures return a
zero-usable diagnostic batch. V1 exports remain for retained evidence and
fixture parity, but the live trace service consumes only the v2 process
entry.

The trace schema increments to v2 and names all four frames. A v2 native-call
timing covers the complete owner-plus-context transaction. It excludes ctypes
argument preparation, Python materialization, compact hashing, JSON
serialization, trace writes, planning, and input.

## Fixed Resource Budget

The declared TH08 scope remains 64 owners, four pointers per owner, 256 rows,
15 restorable frames, and 2,260,992 state-payload bytes.

Additional caller-owned storage:

- owner buffer:
  `64 * 0x53D0 = 1373184` bytes; and
- packed `BatchV2`: 52 bytes.

Maximum successful-process schedule:

- process reads:
  `3 + (2 + 3 * 256 + 64) = 837`; and
- process bytes:
  `1373192 + 2274312 = 3647504` bytes.

The first term is `m0 + owner blob + m1`; the second is the unchanged v1
context-opening/context/owner/final schedule. All output storage is allocated
once by the Python wrapper. No native output allocation or Python bytes copy
is inside the call.

The theoretical 256-context/depth-15 materialization stress remains
diagnostic and not representative of observed Stage-5 density. Its prior
end-to-end failure is not waived. The unchanged physical timing gate now
measures the full v2 native transaction, including owner capture.

## Independent Oracle And Tests

The independent scalar v2 composition must:

- select `m0` internally rather than compare with the trigger snapshot;
- reject `m1 != m0`, `m2 != m0`, or `m3 != m0`;
- add the logical three outer reads to the unchanged scalar v1 read count;
- retain zero records on an outer owner-bracket failure; and
- preserve exact v1 records/payload/status when all four frames agree.

Native fixture parity covers all four frame mismatch positions, null/active
owners, depth 0/1/15, owner/context churn, invalid PC/marker/capacity, random
cases, and the maximum bound. Linux process v2 must report unsupported rather
than emulate Windows. Windows invalid-handle/capacity checks must fail
deterministically without partial success.

The service tests prove one native call per due attempt, no Python owner read,
trigger/capture frame separation, reset/context cadence, error visibility,
and default-off behavior.

## Formal Review

1. **Merged histories:** Only equal complete v2 observations merge. Hidden
   full-game, unobserved-source, and ABA differences remain unresolved.
2. **Uncertainty/causality:** This is observation only. No controller choice
   conditions on hidden branches or on the post-issue result.
3. **Physical question:** Exact solution would answer only coherent bounded
   auxiliary-state capture, not future geometry or survival.
4. **Approximation:** First-64 owners, four known pointers, retained frames,
   and equality guards are exact inside scope. Omitted owners/sources,
   manager-counter insufficiency, and ABA have unknown direction and no hard
   authority.
5. **Deadline/fallback:** The trace is post-issue and default-off. Failure
   publishes zero state; live Boolean guidance plus a fresh local certificate
   remains unchanged.

## Ordered Checkpoints

1. Add the packed v2 batch/status and independent scalar composition.
2. Add fixture-v2 parity before the Windows process implementation.
3. Add one-call process v2 with a reusable caller-owned owner buffer.
4. Switch only the default-off trace service and strict analyzer to schema v2.
5. Run warning-strict Linux and release Linux/Windows builds, focused parity,
   complete Linux/Windows suites, and retained isolated timing.
6. Run the unchanged focused Stage-5 spell-107 physical gate.
7. If and only if every fixed gate passes, retain v2 transport for later exact
   runtime-image/instruction-lowering work.
