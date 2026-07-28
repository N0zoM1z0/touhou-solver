# G5 Native Auxiliary-VM Batch Contract

Date: 2026-07-28

Status: fixed before implementation. This contract authorizes an explicit
default-off, post-issue, trace-only native batch and its independent scalar
oracle. It grants no future-hazard, source-completeness, feasibility,
publication, planner, cadence, or action authority.

This contract follows
`G5_AUXILIARY_VM_RUNTIME_IMAGE_OBSERVATION_CONTRACT_20260728.md` and the
retained Stage-5 pointer-density result. That checkpoint selected a native
compact batch because a physical capture contains
p50/p95/p99/max `4/26/32/34` non-null contexts and 56 of 57 heap pointer
values are reused across different `(slot, auxiliary-index)` observations.

## Physical Objective And Authority

The physical objective remains hard no-Bomb survival. The batch answers only:

> Under one unchanged ordinary-enemy manager-frame bracket, which first-64
> auxiliary contexts supplied coherent active VM bytes and the saved frames
> that the current call depth can actually restore?

The observation is produced after the input issue transaction. It may be
enabled only for an explicit research trial and initially no more often than
once per 16 changed enemy-manager frames. Its work and contention are
diagnostic contamination and must be measured separately. The issue thread
never waits for or consumes an auxiliary result.

On absence, error, churn, timeout, unsupported platform, or capacity failure,
the batch publishes no auxiliary VM state. The existing live Boolean policy
plus fresh local hard certificate remains unchanged.

## Revalidated Shipped-Game Layout

All names in this section were revalidated against instructions and dataflow;
none receives authority merely from an inherited IDA label.

**Observed statically:**

- opcode `0x87` at `0x0041CDF3..0x0041CF81` allocates and zeroes a
  `0x24B0`-byte context;
- context `+0x00` stores the selected subroutine index;
- context `+0x06` stores a signed 16-bit call depth;
- context `+0x08` begins the active `0x228`-byte VM;
- context `+0x230` begins saved-frame storage at a `0x228` stride;
- `0x24B0 = 0x230 + 16 * 0x228`, so physical saved slots are `0..15`;
- `ecl_call_subroutine` at `0x00421BD0` advances the caller PC, copies the
  complete active VM to `saved[depth]`, starts the callee, and increments
  depth only while depth is below 15;
- `ecl_return_subroutine` at `0x00421CB0` pre-decrements depth and restores
  `saved[depth]` when the result is nonnegative;
- therefore the maximum restorable depth is 15 and ordinary returns restore
  slots `0..14`; a call already at depth 15 still overwrites physical slot 15,
  but the next return restores slot 14 and does not restore slot 15;
- the scheduler at `0x0041EBB6..0x0041EC7C` restores depth from context
  `+0x06`, selects active VM `+0x08`, selects saved base `+0x230`, and writes
  `auxiliary_index + 1` to active VM `+0x220`;
- when root return underflows, `ecl_return_subroutine` uses active VM
  `+0x220 - 1` to free the owning auxiliary context; and
- integer/float/lvalue evaluators consume active-VM state beyond the prior
  104-byte projection, while call copies and return restore all `0x228`
  bytes.

IDA comments at `0x0041CF59`, `0x0041EBE9`, `0x00421C31`, and
`0x00421D02` were corrected to preserve the active/restorable/physical-slot
distinctions.

## Observation And State Contract

The batch input is one already captured first-64 ordinary-enemy blob with:

- exact pool base, record count, stride, active-flag offset and mask;
- auxiliary-pointer offset and four-pointer layout;
- expected enemy-manager frame;
- executable/problem version; and
- a process handle only for the explicit Windows physical backend.

For every active owner and non-null context, the batch retains:

- owner slot, deterministic enemy pointer, auxiliary index, and context
  pointer;
- exact owner flags and four pointers before and after context capture;
- target subroutine word/dword header evidence;
- signed call depth;
- complete active `0x228` VM bytes;
- exactly `depth` restorable saved frames, slots `[0, depth)`;
- active VM `+0x220` auxiliary-owner marker; and
- context header plus active-PC recheck before publication.

Existing physical slot 15 is not captured at depth 15 because the next
saturated call overwrites it and the next return restores slot 14. The
complete active VM is captured so a later exact recurrence can model that
overwrite. Any future interpreter that needs non-restorable historical slot
15 must define a new observation version; it may not infer it.

Valid depth is `0..15`. Active and every retained saved-frame PC must be a
bounded non-null 32-bit process address. The auxiliary marker must equal
`auxiliary_index + 1`. A newly observed exception remains unresolved rather
than weakening these gates.

## Coherence And Read Schedule

The Windows batch performs this fixed read schedule:

1. read enemy-manager frame and require the expected value;
2. for each non-null context, read its 12-byte header/active-PC prefix;
3. read `0x228 * (1 + depth)` contiguous bytes from context `+0x08`, covering
   the active VM and all currently restorable saved frames;
4. reread the 12-byte header/active-PC prefix and require exact equality;
5. for each active owner, reread one `0x70`-byte span from
   enemy `+0x3324..+0x3393`, covering flags and all four pointers;
6. require exact flags/pointers and active status; and
7. reread enemy-manager frame and require the same expected value.

`enemy_manager_frame` is used only as an enemy-source coherence guard. It is
not promoted to an input clock or wall-time guard; CE-0120/0121 remain
unchanged.

The schedule cannot eliminate a theoretical same-address ABA that restores
the exact checked header, PC, flags, and pointer bits without advancing the
manager frame. That branch remains a stated residual uncertainty. Runtime
exact-image versioning and later slot-generation joins further constrain it;
pointer equality alone never does.

## Fixed Resource Budget

The declared scope is:

- owners: at most `64`;
- pointers per owner: exactly `4`;
- context records: at most `256`;
- active VM bytes per valid record: `0x228 = 552`;
- restorable saved frames: at most `15`;
- maximum payload per record: `16 * 552 = 8832` bytes;
- maximum state payload: `256 * 8832 = 2260992` bytes;
- fixed metadata arrays: capacity 256, allocated once by the Python wrapper;
- process reads: at most
  `2 + 3 * 256 + 64 = 834`;
- process bytes: at most
  `2 * 4 + 256 * (12 + 8832 + 12) + 64 * 0x70
  = 2274312` bytes; and
- native result: one synchronous FFI call with no output allocation inside
  the call.

The native code never reads beyond the declared owner span, context prefix,
active/restorable frame payload, or manager counter. Integer multiplication,
address addition, output offsets, and capacities are checked before access.

## Native ABI And Status

The native trace library exposes separate v1 entries:

- a fixture entry consuming independent before/after owner blobs and
  before/after addressed context arenas; and
- a Windows process entry consuming an existing process handle and the same
  fixed output arrays.

Both entries share one bounded decoder and output:

- batch status, frame bracket, read count, owner/context/valid/error counts;
- one fixed metadata row per pointer position on every active owner, including
  explicit null-pointer diagnostic rows;
- prefix offsets into one caller-owned payload buffer; and
- per-context status sufficient to shrink a deterministic failure.

Success requires every non-null context row to be coherent. A batch with one
invalid row may retain diagnostic status/counts but publishes zero usable VM
records. Timeout is measured outside the native function and cannot convert
partial output to success.

The first ABI version is trace-library-local. It does not change the stable
46-symbol solver ABI or any viability/publication workspace.

## Information, Causality, And Equivalence

Two successful batch observations are identical only when:

- gameplay epoch, stage/route, expected manager frame, executable identity,
  and immutable problem version agree;
- all first-64 owner active flags and auxiliary pointers agree;
- every context header, depth, active VM, and restorable saved frame agrees;
  and
- the exact batch schema and runtime ECL image version agree.

Even identical batches are not source-equivalent or control-equivalent.
Ordinary slots `64..479`, callbacks, transforms, RNG, native emitters,
origin/template state, instruction reachability, runtime image identity, and
realized slot-generation causality remain unresolved.

The batch observes state after the issued action. A policy may not condition
that action on the result. Later offline joins use only recorded decision and
manager-frame support and keep hidden branches merged.

## Deadline, Performance, And Fallback Gates

Before physical use:

- scalar/native fixture parity must pass all deterministic and randomized
  cases;
- isolated 34-context depth-0 and 256-context depth-15 fixture p95/p99/max
  must be reported on Linux and Windows;
- no native allocation, Python object materialization, JSON serialization, or
  trace write is inside the native-call timing boundary; and
- the Windows process entry must be unavailable, not emulated, on Linux.

Initial physical acceptance at once per 16 changed manager frames requires:

- batch native-call p95 `<= 2.0 ms`, p99 `<= 4.0 ms`, max `<= 12.0 ms`;
- zero capacity, invalid-depth, invalid-PC, marker, context-recheck, owner-
  recheck, frame-bracket, or native-call failures;
- decision-cadence p95 no more than one frame worse than a compatible
  no-batch workload; and
- exact hard no-Bomb, route, transition, key-release, and cleanup gates.

Failure retains diagnostic evidence, disables repeated physical batch
capture, and returns to pointer-only schema 12. It does not reject auxiliary
source value; a background immutable-version transport may be contracted
later using the same batch semantics.

## Independent Oracle And Adversarial Tests

The Python scalar oracle does not call the native implementation. Fixtures
must cover:

1. zero active owners and zero pointers;
2. all 64 owners and all 256 pointers;
3. depths 0, 1, 14, and saturated 15;
4. active plus exact saved-frame byte/PC preservation;
5. physical slot 15 excluded from restorable payload at depth 15;
6. active-PC, saved-PC, depth, auxiliary-marker, and capacity rejection;
7. context pointer below/above the address range;
8. context header/PC churn between reads;
9. owner active-flag, full flags, and each pointer changing independently;
10. context release and same-address reuse;
11. reversed/changed manager-frame brackets;
12. address/size multiplication and output-capacity overflow;
13. deterministic record ordering and byte-identical output;
14. randomized scalar/native parity with failure shrinking; and
15. Windows process-handle failure without key/input side effects.

Tests protect raw bytes, status, bounds, and authority. They may not replace
the scalar oracle with a native round trip.

## Formal Review

1. **Control-equivalent histories:** no omitted source state is declared
   equivalent; exact observed bytes and all residual classes remain separate.
2. **Uncertainty and causality:** frame, owner, pointer, context, depth,
   address, capacity, and ABA uncertainty either fail closed or remain
   explicit. The current action cannot see the post-issue result.
3. **Physical versus proxy:** the batch answers coherent source-state
   availability only. It does not answer future geometry or survival.
4. **Algorithm and falsifier:** an independent scalar oracle defines the
   bounded extraction; any byte/status/order mismatch, missed churn, or
   out-of-bounds access falsifies native parity.
5. **Deadline and fallback:** the result is diagnostic after issue, sampled at
   fixed low cadence, never awaited by a consumer, and disabled on gate
   failure. Live fallback is unchanged.

## Ordered Checkpoints

1. Correct every source of truth to distinguish 15 restorable frames from 16
   physical slots and retain the new source-report digest.
2. Implement the independent scalar fixture decoder and adversarial tests.
3. Implement shared native fixture/process decoding and caller-owned output.
4. Add the Python native wrapper with one-time buffers and strict
   materialization outside the native timing boundary.
5. Build Linux/Windows, run parity/fuzz, and retain isolated timing reports.
6. Only if those pass, integrate a once-per-16-manager-frame post-issue trace
   option and run one focused Stage-5 spell-107 physical gate.
7. Keep exact runtime-image capture and later instruction lowering separate.
