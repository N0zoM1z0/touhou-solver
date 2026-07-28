# G5 ECL Control-Flow Fail-Closed Performance Contract

Date: 2026-07-28

Status: implemented and offline-validated correction; fresh physical runtime
validation remains open because the retained decoded file cannot replay 15
late transition rows.

This refines
`G5_CALLBACK_LOOKAHEAD_COMPLETENESS_CONTRACT_20260728.md`. It changes
neither the callback recurrence nor physical action authority. The first
checkpoint removes work that the callback scanner cannot justify: it stops
at an eligible control transfer whose branch state is absent instead of
following the encoded fallthrough and eventually exhausting the
256-instruction budget.

## Physical Question

Given one capture-aligned main-ECL VM snapshot, immutable instructions, active
difficulty, and an `H`-frame horizon, has the scanner established the exact
callback-12 schedule on the single physical main-VM history, or has it reached
a control choice whose operands are not in the observation?

The scanner may publish a complete schedule only for the former. Reaching the
latter produces an observed prefix followed by `UNKNOWN`. Stopping earlier at
the first unsupported transfer is also a performance correction when the old
fallthrough scan could not become authoritative.

## Native Static Evidence

The following conclusions are **observed in the connected shipped-game IDA
database**, not runtime observations:

- `enemy_ecl_vm_step` is `0x004184B0`. Opcodes `0x28..0x33` all dispatch
  through `ecl_conditional_jump` at `0x004197C9`.
- `ecl_conditional_jump` is `0x004215F0`. Opcode `0x33` evaluates both float
  operands and takes the encoded relative branch when `lhs >= rhs`; otherwise
  it falls through.
- `ecl_eval_float` is `0x00420120`. ECL variable `10050` enters at
  `0x0042074B`, subtracts the current enemy position at `enemy+0x2D88` from
  the global player position, and returns the Euclidean length.
- The vector helpers at `0x004090D0` and `0x0040B4C0` were renamed
  `vec3_subtract` and `vec3_length`. Comments at `0x0042074B` and
  `0x00421AB1` retain the recovered dependency and branch rule.
- Shipped Stage-4A spell 73 uses
  `jump_float_ge(10050, 64.0, ...)` at decoded ECL offset `0x7100`.
  Therefore its branch depends on the future player/enemy trajectory, not a
  missing scalar VM local that can be safely memoized.
- Opcode `0x05` decrements an integer lvalue and takes its branch while the
  resolved value remains positive. Spell 57 reaches such an instruction at
  decoded offset `0x3510`; its loop state includes VM locals and RNG-derived
  values absent from `EclVmSnapshot`.

The runtime base-to-decoded-offset mapping for the retained schema-v9 run is
**inferred** from multiple exact instruction matches:
`0x0B1C1430` maps to decoded offset zero. Under that mapping the retained
spell-57 PC `0x0B1C474C` is offset `0x331C`, and the spell-73 PC
`0x0B1C850C` is offset `0x70DC`.

## Observed Workload And Counterexample

Retained accepted Stage-4A run
`lunatic_route2_stage4a_unattended_20260728_092619` has:

- 1,345 spell-57 rows, all `instruction_limit`, each scanning exactly 256
  instructions, with zero complete lowering;
- 966 spell-73 `repeated_state` rows after the scanner ignored the dynamic
  `0x33` branch;
- spell-57 lookahead p50/p95/max
  `0.2808/0.5360/1.4769 ms`; and
- a representative spell-57 snapshot at frame 10,971, PC `0x0B1C474C`,
  timer 32, that scans 256 instructions and stops at relative frame 189.

The deterministic falsifier is smaller than the physical workload:

1. place an eligible opcode `0x05` or `0x28..0x35` before two divergent
   successors;
2. put a callback-12 invocation on the non-fallthrough successor;
3. omit the required branch operand from the snapshot; and
4. choose a fallthrough whose next timestamp lies beyond `H`.

Following the encoded fallthrough then returns a complete empty schedule even
though an observation-compatible physical branch invokes callback 12. This
falsifies completeness; increasing or memoizing the same scan does not fix
the missing information.

## Fixed Algorithm Boundary

The existing 256-instruction cap and physical-frame calculation remain
unchanged. After timestamp advancement and difficulty filtering:

- literal opcode `0x04` remains supported only with literal target time and
  relative offset;
- opcode `0x01` remains a complete termination;
- opcode `0x05`, conditional jumps `0x28..0x33`, call/return `0x34..0x35`,
  and any other immediate control transfer lacking complete observed state
  stop as `unsupported_control_flow`;
- an unsupported timer reset stops as `unsupported_timer_reset`;
- no scanner branch may choose a value for ECL variable `10050`, an
  unobserved VM local, RNG state, call stack, or interrupt state; and
- the returned prefix remains trace evidence only. `complete_events` and live
  velocity lowering stay unavailable.

This checkpoint does not implement a transfer summary. A later summary is
eligible only for an immutable basic block or closed component with an exact
read/write/control dependency set. It must preserve the logical instruction
count separately from executed Python work and must invalidate on any
unknown dependency. A spell ID, decoded offset, or historically empty output
is not a proof.

## State, Causality, And Equivalence

The current snapshot observes PC, timer, tag mask, callback angle/speed, and
time scale. It omits VM locals, RNG, call-stack frames, interrupt state, player
future positions, and enemy future positions.

Two histories with the same current snapshot are not control-equivalent at
opcode `0x05` or spell-73 opcode `0x33` when those omitted values select
different successors. They must merge into one `UNKNOWN` suffix; the scanner
may not maximize or follow either hidden successor as if observed.

## Resource And Performance Gate

- No additional RPM, process, worker, cold expansion, native ABI, or issue
  write is authorized.
- The scanner still admits at most 256 decoded instructions.
- The primary deterministic performance metric is instructions actually
  inspected before the unsupported boundary.
- For the retained spell-57 representative, the corrected scan must inspect
  fewer than 64 instructions, return `UNKNOWN`, and emit no lowered events.
- Linux and Windows shipped-code benchmarks record p50/p95/max wall time,
  instruction count, stop reason, code SHA-256, and exact snapshot.
  Timing is descriptive; semantic acceptance does not depend on a noisy
  sub-millisecond ratio.
- The full deterministic Linux and Windows suites must pass.

## Safety And Authority

- Survival remains hard and Bomb bit `0x02` remains forbidden.
- `UNKNOWN` is not free space and is not an empty-event certificate.
- No old `instruction_limit` or `repeated_state` row is reinterpreted as
  complete.
- The change may shrink a declared covered prefix; it may never enlarge
  schedule authority.
- A callback observed after the new `unknown_from_frame`, a complete result
  crossing unsupported control, or any lowered incomplete prefix falsifies
  the implementation.
- Offline instruction/timing improvement is not physical survival evidence.
  A physical run is required only if a later intervention changes live
  lowering or seeks promotion.

## Formal Review

1. **Control-equivalent histories:** hidden branch operands are not in the
   snapshot, so their histories merge into `UNKNOWN` rather than a selected
   successor.
2. **Uncertainty and causality:** no future player/enemy position, RNG value,
   local, or callback observation is inserted into the current decision.
3. **Physical answer:** a complete result answers only the declared captured
   main-VM source. This correction deliberately answers less when the path is
   not observed.
4. **Algorithm and falsifier:** the first unsupported transfer ends the exact
   prefix. The divergent-successor callback fixture above falsifies the old
   fallthrough rule and protects the correction.
5. **Deadline and fallback:** earlier fail-closed termination reduces issue
   work. Existing lookup/lowering fallback is unchanged.

## Ordered Gates

1. Add deterministic divergent `0x05` and `0x33` counterexamples.
2. Stop callback traversal at unsupported timer/control instructions without
   changing the 256-instruction cap.
3. Verify existing complete literal-jump/callback fixtures remain exact.
4. Replay retained Stage-4A callback snapshots and classify every semantic
   status change; no `UNKNOWN -> COMPLETE` transition is allowed.
5. Retain Linux/Windows shipped-code timing reports and run both complete
   suites.
6. Update `START_HERE.md`, `STRATEGY.md`, `COUNTEREXAMPLES.md`,
   `RESEARCH_LOG.md`, and the consolidated roadmap in one verified
   checkpoint.
7. Only then reconsider dependency-complete block summaries or a conservative
   spatial envelope.

## Implementation And Offline Evidence

The callback scanner now stops on unsupported timer reset, loop-decrement
branch, conditional branch, and call/return opcodes. The 256-instruction cap,
literal jump, termination, callback lowering API, native ABI, RPM boundary,
and action path are unchanged. Two deterministic divergent-successor
fixtures prevent an omitted branch operand from becoming a complete empty
schedule. Shipped spell-57/spell-73 fixtures require
`unsupported_control_flow`, `UNKNOWN`, and fewer than `64/16` inspected
instructions.

Post-hoc control replay over retained run `20260728_092619` accounts for all
5,803 callback rows and exactly replays 5,788 (`99.7415%`) against the
retained decoded Stage-4A image:

- no `UNKNOWN -> COMPLETE` transition occurs;
- 1,480 horizon rows and one termination remain complete;
- all 1,345 spell-57 instruction-limit rows and all 966 spell-73
  repeated-state rows become earlier `unsupported_control_flow` unknowns;
- 1,996 old complete horizon rows also correctly lose completeness:
  997 in spell 61 and 999 in spell 65 crossed unmodeled `0x05` or `0x34`
  transfers;
- total inspected instructions fall
  `563,466 -> 58,204` (`89.6704%`);
- spell-57 instructions fall
  `344,320 -> 3,155` (`99.0837%`), maximum 26 per row; and
- replay emits zero prefix events, so it does not insert a new schedule.

Fifteen late spell-73 transition rows cannot be replayed because the retained
runtime instruction image is no longer byte-aligned with
`artifacts/decoded/ecldata4asp.ecl`, and raw instruction bytes were not
retained. All 15 were old declared-complete horizon rows; no old unknown row
is excluded. The deterministic report therefore deliberately has
`passed=false` on `all_callback_rows_replayed`, despite passing every semantic
gate on the replayable scope. Two generations are byte-identical at SHA-256
`99f17fbc0a98a5bb9c2711c98e52bef00f3703566d97a26a0e59cfbb10f1edd1`.
This is an evidence limitation, not permission to infer those rows.

Ten-thousand-iteration shipped-code benchmarks pass on Linux/Windows. The
representative spell-57 result is 26 instructions with p50/p95
`0.0196/0.0223 ms` and `0.0241/0.0307 ms`; spell 73 is three instructions
with p50/p95 `0.0035/0.0039 ms` and `0.0042/0.0043 ms`. Report SHA-256
values are
`c4ab3cd721b7cf9ce9cb8c62f17366f4b3527a8f780af8be749ef72bfe6ceaaa`
and
`89174afc0565dacda7345bb128face3b4ad3892dece153b8d05f092cf522aaa7`.
Timing is descriptive; deterministic control/status/instruction gates carry
acceptance.

Focused ECL tests pass 46/46. Complete Linux/Windows suites pass 823/823 in
`9.877/16.371 s`, with three existing Windows platform skips.

Ordered gates 1–3 and 5 are complete. Gate 4 remains open for the 15 unmapped
runtime rows and must be closed by a fresh physical trace before this
checkpoint can claim complete runtime-workload validation. No transfer
summary or callback/action authority is promoted meanwhile.
