# G5 Capture-Aligned ECL VM-Local Shadow Contract

Date: 2026-07-28

Status: preimplementation contract; phase A authorizes capture and trace
projection only. Phase B offline interpretation and any live coverage change
remain unauthorized until the retained physical projection and independent
oracle gates pass.

This follows
`G5_ECL_CONTROL_FLOW_FAIL_CLOSED_PERFORMANCE_CONTRACT_20260728.md`.
The fresh physical correction correctly leaves 4,307/5,749 callback rows
`UNKNOWN` at hidden ECL control. The next question is not whether to guess
those branches, but which operands can be observed in the same capture and
then evolved exactly.

## Physical Problem And Authority

At one manager-frame-bracketed capture, observe the active enemy main-ECL VM
context that the shipped VM will resume. Retain enough raw local state to
test, offline, whether a declared subset of local assignments and opcode
`0x05` branches can be interpreted causally over the existing callback
horizon.

Phase A changes no physical objective, action, issue/no-write semantics,
cadence, delay support, hazard recurrence, callback lowering, or fallback.
It adds no process read call and may not change a `COMPLETE` or `UNKNOWN`
label. Its output is trace-only evidence.

Phase B, after a separately recorded implementation checkpoint, may compute a
shadow candidate schedule. It may not reach live lowering until exact
universal verification over every newly completed retained candidate and a
fresh physical metadata gate. Timeout, missing state, unsupported opcode, and
unvisited path remain `UNKNOWN`.

## Shipped-Game Static Evidence

The following is **observed statically** in the connected shipped TH08 IDA
database:

- the active main VM context is the `0x228`-byte object reached through
  `enemy+0x2CA0`; its root storage is `enemy+0x07F8`;
- `ecl_eval_int` at `0x0041F420` maps variables `10000..10007` to context
  `+0x18..+0x34`, and variables `10036..10039` to
  `+0x58..+0x64`;
- `ecl_eval_float` and `ecl_resolve_float_lvalue` map variables
  `10016..10023` to context `+0x38..+0x54`;
- opcode `0x05` at `0x0041869A` resolves argument 2 as an integer lvalue,
  decrements it, evaluates that same operand when parameter-mask bit 2 is
  set, and takes the encoded time/relative branch while the post-decrement
  value is positive;
- Stage-4A spell 57, 61, and 65 loop boundaries all use parameter mask
  `0x0004` and variable `10036`; and
- `ecl_call_subroutine`/`ecl_return_subroutine` save and restore the complete
  `0x228` context. The call path also installs `0x20` bytes of parameter
  state at context `+0x70..+0x8F`.

IDA comments at `0x0041F45C`, `0x0041F598`, `0x0041869A`,
`0x00421C31`, and `0x00421C62` retain these conclusions.

The existing live snapshot reads `0x40` bytes in one RPM call. It already
contains the first eight integer locals and the first two float locals used
as callback tag/angle/speed, but discards their general identity. Extending
that same call to `0x68` bytes includes all eight float locals and scratch
integers `10036..10039`. It does not observe call frames, call parameters,
interrupt slots, RNG state, future player/enemy position, or auxiliary VM
contexts.

## Phase A: Exact Observation Projection

Create a TH08-specific VM-state module behind the compatibility
`th08_ecl_runtime` facade. The immutable projection contains:

- signed int32 values for variables `10000..10007`;
- raw uint32 float bits for variables `10016..10023`; and
- signed int32 values for variables `10036..10039`.

Raw float bits are authoritative. JSON floats are not used for the projection
because dormant locals may contain non-finite bit patterns and because exact
float32 replay identity must survive serialization.

The existing `tag_mask`, `callback_angle`, and `callback_speed` fields remain
for compatibility. When a projection is present, construction validates that
the tag equals integer local 0 and that callback angle/speed match float-local
bits 0/1 exactly after float32 decoding. Historical and deterministic tests
may construct a snapshot with no projection; absence must be explicit and
cannot enable local interpretation.

The trace records one versioned local projection inside
`bullet_velocity_lookahead`. It records:

- layout/version identity;
- capture byte count;
- integer locals;
- float-local raw bits; and
- scratch integers.

No duplicate memory read is permitted. A test reader must prove one contiguous
VM read and the unchanged one time-scale read. Capture errors retain the
existing fail-closed behavior.

## Phase B: Proposed Exact Offline Subset

Phase B is not part of the first implementation commit. Its initial eligible
subset is:

- literal `set_int`/`set_float` assignments whose destination and source are
  represented exactly;
- exact finite float32 add/subtract and angle normalization for tracked
  locals, with shipped x87/float32 rounding behavior verified rather than
  assumed;
- opcode `0x05` only when parameter-mask bit 2 selects an observed supported
  integer lvalue; and
- the already supported literal jump, terminate, and callback-12 invocation.

The first interpreter must maintain the complete local projection in its
visited-state key. PC/timer/physical frame alone is insufficient after a
branch mutates a loop counter.

The following remain unsupported:

- opcode `0x05` with a literal lvalue. The shipped VM mutates the instruction
  payload itself, while `EclInstructionCache` is immutable;
- any RNG read or RNG-mutating opcode not already reflected in the captured
  local state before the candidate path starts;
- conditional branches on dynamic player/enemy state, including spell-73
  variable `10050`;
- call/return, because they require the complete stack and `0x228` context;
- interrupt invocation or externally installed transition state;
- auxiliary VM topology unless a separate all-source contract proves its
  callback contribution; and
- any unknown destination, source, opcode, non-finite operation, division
  edge, or rounding behavior.

An unsupported relevant write must stop before it. It may not be ignored
because no callback happened in one retained sample.

## State Equivalence And Causality

Two physical histories map to one phase-A observation only if PC, timer,
time-scale, tag/angle/speed, and every projected raw local value agree.
They are not claimed control-equivalent at calls, interrupts, unobserved RNG,
dynamic spatial variables, auxiliary VMs, or unprojected locals.

For supported local opcode `0x05`, the controller does not choose a hidden
branch. It evaluates one post-decrement value already determined by the
capture and exact preceding supported mutations. If that dependency chain is
broken, all observation-compatible successors merge into `UNKNOWN`.

## Independent Oracle And Falsifiers

The formal oracle stays in independent Python test code and must not call the
production local resolver or transition helper. It operates on raw
instruction tuples and a plain variable dictionary.

Required deterministic cases are:

1. two snapshots with the same old seven fields but different `10036` values
   take different `0x05` successors, proving why the old snapshot aliases
   non-equivalent histories;
2. counter values 0, 1, 2, and a multi-iteration case agree on post-decrement
   branch, timer, events, and final state;
3. a missing or unsupported counter remains `UNKNOWN`;
4. a literal-lvalue `0x05` remains `UNKNOWN`;
5. RNG before local initialization remains `UNKNOWN`, while a capture taken
   after RNG has committed may use the observed local only if the future path
   never executes RNG again;
6. call/return and spell-73 `10050` remain `UNKNOWN`;
7. local state participates in repeated-state detection; and
8. float32 edge/adversarial cases cover signed zero, wrap at plus/minus pi,
   non-finite bits, and values around a branch threshold.

A callback mismatch, a candidate complete row that crosses an unsupported
dependency, a new event absent from the scalar oracle, or a changed phase-A
live status falsifies the checkpoint.

## Performance And Publication Gates

- VM RPM call count is unchanged; the contiguous VM payload grows
  `64 -> 104` bytes.
- Phase A reports snapshot decode p50/p95/max and total
  `read_ecl_lookahead` p50/p95/p99/p99.9/max by workload.
- Linux and Windows isolated tests compare the old seven-field decode with
  projection decode over identical buffers. Timing is descriptive; exact
  read-count/byte-count and field parity are hard gates.
- Trace payload growth is reported. No per-row nested variable-name objects
  are permitted; use fixed arrays and one layout identifier.
- Phase B separately reports logical VM instructions versus Python operations.
  A faster result cannot compensate for a coverage or oracle mismatch.
- The existing birth-observer `0.20/0.40/2.00 ms` B4 limits remain unchanged
  and include the projection overhead in the same physical wall boundary.
- Consumers remain lookup-only. Phase A has no candidate publication.

## Formal Review

1. **Control-equivalent histories:** the projection distinguishes the
   Stage-4 loop-counter histories that the old seven fields merged. It does
   not claim equivalence for unobserved sources.
2. **Uncertainty and causality:** only capture-time raw values and supported
   deterministic mutations may select a branch. No future motion or RNG is
   inserted.
3. **Physical versus proxy:** phase A answers only what local values the
   shipped active VM held at capture. Phase B initially remains an offline
   main-VM proxy until all relevant source topology is contracted.
4. **Algorithm and falsifier:** independent scalar transition/event replay
   checks every newly completed candidate; any unsupported dependency keeps
   the suffix unknown.
5. **Deadline and fallback:** phase A adds bytes to one existing read and
   compact trace serialization only. Live analysis and fallback are
   unchanged. A later phase-B miss retains the current fail-closed Boolean
   policy and fresh local hard certificate.

## Ordered Checkpoints

1. Implement and test the immutable local projection behind a narrow module;
   do not change live lookahead results.
2. Benchmark Linux/Windows projection overhead and run complete suites.
3. Take one focused normal-priority Stage-4A trace with the projection,
   unchanged hard no-Bomb controller, and existing B4 telemetry.
4. Retain a compact audit proving projection presence, layout invariants,
   physical workload distribution, performance, and unchanged
   `COMPLETE`/`UNKNOWN` counts.
5. Only then implement the independent scalar oracle and offline candidate
   interpreter.
6. Replay every candidate completion, retain counterexamples, and separately
   decide whether a live shadow is justified.
