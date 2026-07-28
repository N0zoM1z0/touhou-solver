# G5 Auxiliary-VM Bounded Visible Retry Contract

Date: 2026-07-28

Status: fixed before v3 implementation. This contract corrects CE-0165 by
composing at most three complete native-owned v2 attempts inside one
default-off post-issue trace-service transaction. It grants no future-hazard,
source-completeness, planner, feasibility, publication, cadence, or action
authority.

The v2 process ABI, owner/context state semantics, four-frame evidence, and
caller-owned buffers remain unchanged. V3 changes only the trace-service
composition and trace/audit schema; it does not add another native export.

## Physical Objective And Acceptance

The physical objective remains hard no-Bomb survival. The bounded transaction
asks:

> Can every due Stage-5 spell-107 observation obtain one coherent
> native-owned v2 state within at most three immediately consecutive,
> fully visible attempts, without violating the existing timing/cadence
> gates?

Physical acceptance requires:

- at least one transaction actually exercises a retry path;
- every transaction selects one coherent v2 attempt;
- zero retry exhaustion, terminal rejection, exception, selected batch
  failure, selected record failure, or validation error;
- attempt count `<= 3`;
- sum of native-call time across all attempts per due transaction p95
  `<= 2.0 ms`, p99 `<= 4.0 ms`, max `<= 12.0 ms`;
- decision-cadence p95 no more than one frame worse than the compatible
  no-batch baseline; and
- hard no-Bomb, route, transition, key-release, and cleanup success.

A run with no retryable boundary event is useful timing evidence but does not
validate this correction and cannot pass the v3 physical gate.

## Attempt And Retry Semantics

One due service transaction performs attempt indices `0..2`. Each attempt is
one complete `touhou_trace_auxiliary_vm_batch_process_v2` call and therefore
selects its own `m0`, owner-close `m1`, context-open `m2`, and final `m3`.

An attempt succeeds only under the unchanged v2 success predicate.

An unsuccessful attempt is retryable only when:

1. its batch status is nonzero and contains only:
   - `FRAME_BEFORE_MISMATCH`,
   - `FRAME_AFTER_MISMATCH`, and/or
   - `OWNER_CAPTURE_FRAME_MISMATCH`; and
2. every record status contains only:
   - `NULL`,
   - `CONTEXT_CHANGED`,
   - `OWNER_INACTIVE`,
   - `OWNER_FLAGS_CHANGED`, and/or
   - `POINTER_CHANGED`.

The second guard permits only churn evidence that can accompany a declared
frame-boundary crossing. Invalid depth/PC/marker/address, capacity, payload,
context/owner read failure, unsupported platform, process-read failure, and
any unknown bit are terminal. Batch status zero with a bad record is
terminal, not retryable.

After a retryable failure, the next attempt begins immediately. There is no
sleep, frame polling, busy wait, game pause, action change, or reuse of failed
state. The selected observation version is the successful attempt's `m0`,
which may be later than the trigger snapshot and every failed attempt.

If attempt 2 remains retryable but fails, the transaction is
`retry_exhausted` and publishes no state. A terminal failure publishes no
state and performs no later attempt.

## Visibility And Trace Schema

Trace schema v3 emits one row per due service transaction with:

- trigger decision frame and decision-observed manager frame;
- fixed attempt limit 3;
- exact attempt count and selected attempt index;
- one ordered summary per attempted v2 capture:
  - all four frames;
  - batch status and success;
  - active/record/non-null/usable counts;
  - record-status histogram;
  - owner bytes and process-read count;
  - native-call and Python materialization time; and
  - retryable classification;
- sum of process reads and native/materialization time across attempts;
- one full compact selected v2 observation on success; and
- explicit `success`, `retry_exhausted`, `terminal_rejected`, or
  `native_transaction_failed` status.

Failed attempts never contribute VM hashes or state bytes to the selected
observation. Their diagnostic counts remain visible. A successful selected
observation is stored once rather than duplicated in its attempt summary.

The strict analyzer independently recomputes retryability from batch and
record bits. A producer-supplied retryable flag disagreement fails
validation. Missing/reordered indices, more than three attempts, retry after
terminal failure, retry after success, a non-final selected index, mismatched
selected frames/counts, or timing/read-count sum disagreement fails the gate.

## Information, Causality, And Histories

The result is a later coherent observation, not a reconstruction of the
failed attempt's state. Physical histories merge only when the complete
selected v2 observation and preceding ordered attempt summaries are equal.
Failed hidden branches are not maximized or interpreted as safe; they remain
explicit diagnostic history.

No live action consumes the post-issue result. The attempt loop cannot change
the action already issued for the decision. It can add contention before the
next decision, which is why all attempts are charged to timing and cadence
gates.

`enemy_manager_frame` remains an enemy-source coherence guard, not an input
clock. CE-0120/0121 are unchanged.

## Resource And Deadline Bound

One v2 attempt uses at most 837 reads and 3,647,504 process bytes. V3 therefore
has hard maxima:

- attempts: 3;
- process reads: `3 * 837 = 2511`;
- process bytes: `3 * 3647504 = 10942512`; and
- caller-owned native buffers: unchanged and reused sequentially.

Python retains at most three immutable observation objects until the v3 row
is summarized. Failed-attempt state bytes are not compact-hashed or serialized.
There is no new native allocation or pool copy.

Performance authority comes from the physical sum of native-call time, not
the local fixture benchmark. Materialization, attempt-summary construction,
selected compaction, trace emission, and total service time remain separately
reported. Cadence is the final contention falsifier.

## Independent Tests

The retry classifier independently covers:

- each single allowed frame bit and their combinations;
- allowed null/context/owner churn bits;
- every forbidden semantic/read/capacity bit;
- batch-zero record failure;
- unknown bits; and
- success, first-retry success, second-retry success, exhaustion, and
  terminal stop sequences.

The service tests use a scripted capture and prove exact call count/order,
selected version, no call after success/terminal failure, three-attempt bound,
timing/read-count sums, trigger/capture separation, and absence of Python
owner/frame reads.

The analyzer tests reject forged retryability, hidden attempts, exhausted
transactions, invalid selected indices, and sum mismatches. Retained v1/v2
traces remain parseable under their historical schemas, but only schema-v3
rows can pass the new physical gate.

## Formal Review

1. **Merged histories:** Complete selected v2 state plus ordered failed
   summaries define the finite observation. Omitted game/source/ABA state
   remains unresolved.
2. **Uncertainty/causality:** Retry conditions use only completed attempt
   evidence available before the next attempt. No action depends on the
   result.
3. **Physical question:** Exact success answers bounded coherent observation
   delivery only, not future geometry or survival.
4. **Approximation:** Three attempts are an empirical delivery bound, not a
   proof that a coherent interval exists. Exhaustion fails closed.
5. **Deadline/fallback:** All work is default-off and post-issue. Failure
   publishes no state; live Boolean guidance plus fresh local certification
   remains unchanged.

## Ordered Checkpoints

1. Implement and independently test retry classification/composition.
2. Add schema-v3 service summaries and strict analyzer validation.
3. Run focused and complete Linux/Windows suites with the unchanged v2 DLL.
4. Run the same Stage-5 spell-107 physical gate.
5. Retain v3 only if retry is physically exercised and every fixed gate
   passes; otherwise record the next counterexample without weakening it.
