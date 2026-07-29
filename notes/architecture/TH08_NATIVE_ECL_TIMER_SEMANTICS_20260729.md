# TH08 Native ECL Timer Semantics

Status: **offline semantic gate passed; focused physical rebaseline pending**

Date: 2026-07-29

This note is the implementation and evidence contract for roadmap item
`SEM-TIMER`. It corrects the reduced timer abstraction used by the offline
Phase-B1 ECL shadow and the same reduction in the existing live callback and
trace-only birth lookaheads. It does not promote the offline shadow or expand
the live strategy's declared source coverage.

## Evidence labels

- **Observed**: read directly from the shipped-program instructions/dataflow,
  a retained runtime capture, or a deterministic native probe.
- **Inferred**: follows from multiple observed instructions or controlled
  comparisons but has not itself been observed at runtime.
- **Hypothesized**: plausible and explicitly outside authority until tested.

Inherited IDA names, types, comments, and pseudocode variable names remain
hypotheses until revalidated here. Every material IDB mutation made during
this slice must be recorded in the 2026-07-29 research-log shard.

## Problem contract

### Physical objective

Preserve the shipped TH08 ECL timer state and threshold behavior bit-for-bit
when the solver advances an ECL VM by one physical update or composes those
updates. A corrected timer may improve future-hazard prediction, but survival
authority remains unchanged until all downstream model versions and physical
gates are renewed.

### State and observations

At a decision-compatible snapshot, the timer state is:

- native signed integer elapsed field;
- native float32 fractional field, identified by its raw 32-bit payload;
- the float32 gameplay-time-scale input used by the relevant native path;
- instruction pointer and instruction-time threshold when interpreting ECL;
- any explicit opcode or control-flow operation that writes or preserves the
  timer fields.

The product representation must serialize the integer and fraction bits
separately. It must not use a Python binary64 sum as timer identity.

### Actions and issue semantics

This slice defines a deterministic state-transition primitive, not a player
action. It emits no input and has no write/no-write or command-delay choice.
Any planner action conditioned on its output remains governed by the frozen
manager/input-clock contract and existing live fallback.

### Uncertainty and transitions

For finite, supported native inputs the one-update transition must reproduce
native float32 rounding, scaled fractional addition, integer carry, signed
edge behavior, and opcode-specific reset/preserve behavior. Unsupported,
non-finite, or native-undefined cases fail closed and cannot acquire exactness
authority merely because Python or C++ returns a value.

The revalidated instruction-level recurrence and supported-domain boundary
are recorded below. Exactness covers finite binary32 component transitions
and the stated ECL equality/branch operations. Non-finite state fails closed.

### Horizon and resources

The primitive is specified first for one native update. Multi-update results
are repeated application of that primitive with no algebraic shortcut unless
the shortcut is separately proved bitwise equivalent. Focused tests must stay
small; broader route replay follows only after the primitive gate passes.

### Safety invariants

- no Bomb output or gameplay injection is part of SEM-TIMER;
- no Phase-B1 or live authority is expanded before the exit gate;
- timer identity retains exact elapsed and fraction bits;
- every ECL instruction-time comparison uses the native comparison state and
  ordering;
- invalid or unsupported native domains fail closed;
- stale model/candidate/certificate versions cannot consume the corrected
  transition under an old identity.

### Computation, publication, and fallback

The timer update must be cheap enough for existing offline lowering and future
live lookup deadlines, but semantic parity is the first gate. Until promoted,
the current live Boolean policy and its existing fail-closed fallback are
unchanged. Publication requires an immutable semantic-version component and
exact-version matching.

## Required model questions

1. **Which histories merge?** Histories may share a timer state only when
   elapsed, fraction bits, scale bits, PC/threshold, and relevant control-flow
   state are equal. Equal Python sums are not sufficient.
2. **Are all branches causal?** The timer primitive has no controller choice.
   ECL branches must be evaluated from the current observable timer state,
   never from a future scale or hidden post-branch value.
3. **What physical question does exact solution answer?** It answers the
   timer/threshold portion of native ECL evolution only. It does not by itself
   prove complete hazard prediction or physical survival.
4. **How is the claim falsified?** Any supported input for which product,
   independent oracle, and native probe disagree bitwise falsifies exactness.
   A retained runtime threshold crossing at a different update also falsifies
   it.
5. **Can it be consumed before issue time?** The corrected transition is now
   propagated through the existing callback lookahead and its immutable trace
   identity. Offline and dual-platform gates pass. It still has no survival
   promotion: the next accepted consumer evidence must be the fixed
   observer-off Stage-5 physical falsifier, with unchanged cadence and
   fallback.

## Revalidated shipped semantics

The following conclusions are **observed statically** in the connected IDA
database for the shipped patched analysis image:

- image base `0x00400000`, IDB input size `840704`, MD5
  `454c96e08fe3c14df7064d104c26accf`, and SHA-256
  `ec101fcff80b77e717d43b54e326375487af19661bb7c8d11a19ee5e0fbf928b`;
- `0x00447421` reads the binary32 gameplay scale at timing-state offset
  `+0x188`;
- the threshold at `0x004B6944` has bits `0x3F7D70A4`, or
  `0.9900000095367432`;
- a finite scale above that threshold increments the signed dword elapsed
  field once and preserves the fractional dword;
- otherwise x87 adds scale to the fraction, stores it to a dword before the
  carry comparison, and, when the stored value is at least one, increments
  elapsed once and stores the x87 subtraction by one back to a dword;
- the helper performs at most one carry per call and dword elapsed increment
  wraps at signed-int32 representation boundaries;
- `0x00406660` is the only direct helper caller. It copies elapsed `+0x08`
  into previous `+0x00`, then passes elapsed `+0x08` and fraction `+0x04`;
- the core setter at `0x00406610` writes elapsed, zeros fraction, and sets
  previous to `-999`;
- the ECL dispatch gate at `0x004185AF` compares instruction time with the
  signed integer elapsed field for exact equality. It ignores fraction and
  does not use a scalar or greater-than gate; and
- taken opcode `0x05` and opcode `0x04` converge at `0x004186F1`, which writes
  only the active VM elapsed field at VM `+0x0C`, preserves fraction at
  `+0x08`, applies the relative PC, and continues the same VM update.

The native unordered scale branch is outside solver authority because live
sensing rejects non-finite scale. Finite negative and signed-edge component
transitions remain represented and differentially tested as native-mechanics
evidence, although the live snapshot contract requires positive scale.

## Exact product recurrence

Let state be `(e, f_bits)` and let `s` be the finite float32 decoded from
`scale_bits`.

1. If `s > f32(0x3F7D70A4)`, return
   `(wrap_i32(e + 1), f_bits)`.
2. Otherwise compute `r_bits = round_f32(f32(f_bits) + s)`.
3. If `f32(r_bits) >= 1.0`, return
   `(wrap_i32(e + 1), bits(round_f32(f32(r_bits) - 1.0)))`.
4. Otherwise return `(e, r_bits)`.

Instruction scheduling repeatedly applies that transition until
`e == instruction_time` or the declared physical-frame horizon expires.
Being numerically past an instruction time does not make it eligible.
Opcodes `0x04` and taken `0x05` replace `e` and preserve `f_bits`; the native
setter replaces `e` and sets `f_bits = 0`.

## Implementation and version propagation

- `scripts/th08_native_timer.py` owns
  `th08-native-timer-components-v1-00447421`, separate component identity,
  the one-frame transition, exact-equality bounded advance, branch
  preservation, and setter/reset components.
- `scripts/analysis/th08_ecl_timer_raw_oracle.py` is a structurally
  independent raw integer/bit oracle. It aligns integer significands and
  exponents and implements round-to-nearest-even directly; it does not import
  the product helper or representation and does not rely on Python floating
  addition for the transition.
- `native/tests/th08_ecl_timer_probe.cpp` independently executes the slow
  path with x87 `fadd`/`fsub` plus `fstp dword`.
- the offline VM-local shadow is versioned
  `th08-ecl-vm-local-shadow-v2-native-timer-components`;
- the existing live velocity lookahead is versioned
  `th08-ecl-velocity-lookahead-v2-native-timer-components`;
- the trace-only birth lookahead is versioned
  `th08-ecl-birth-lookahead-v2-native-timer-components`; and
- live decision traces now serialize fraction bits, scale bits, component
  timer identity, and lookahead semantic version. Old traces and candidates
  cannot silently claim the new timer identity.

The velocity lookahead correction can change the physical callback schedule
on a later run. The birth lookahead remains trace-only. Neither correction
adds an opcode, callback, source, planner action, or Bomb authority.

## Retained semantic evidence

The Linux and Windows differential reports each pass 17/17 adversarial cases
covering nonzero fraction, non-unit and negative scale, carry/no-carry,
threshold-adjacent values, subnormals, signed wrap, repeated slow ticks,
branch preservation including opcode `0x05`, and reset:

- `artifacts/ecl_reports/th08_native_ecl_timer_differential_linux_20260729.json`
  SHA-256
  `cd9504623ec7ca13649d11525899b1578d6590b7d3658572ccb2fae023881162`;
- `artifacts/ecl_reports/th08_native_ecl_timer_differential_windows_20260729.json`
  SHA-256
  `15ab29a52a1dc5c149d7599bcae0d75a2b8929c07ae1996786d050c6722adff4`.

A seeded 4,096-case raw-bit product/oracle sweep additionally covers broad
finite exponent/significand combinations and matching fail-closed overflow.
It is implementation evidence, not a replacement for the native probe.

The original 108-case fixture remains immutable at SHA-256
`6c34d09752abb7805c84e537b8df52ad24a1aea90614c8b5a2687d730d73ab3c`
and is explicitly only an observed zero-fraction/unit-scale slice. A new
component-versioned 108-case fixture has SHA-256
`112e58b4866faed7a1bed76b91e489aea9e627a8216b7c1ce0a2f17921788e6a`;
its replay report has SHA-256
`b52eeb18cbe1d53e7ba773f3d5c0dfea8e73ce5478a6382c359d934cce9466ce`.
It decodes all 3,117 in-scope retained Stage-4A rows, sees 1,730 opcode-`0x05`
roots and 108 unique cases, produces zero mismatches, and does not convert a
previously unknown row into a complete schedule. The retained physical slice
still contains no nonzero fraction or non-unit scale; general transition
authority comes from the independent oracle/native-probe gate, not that
capture.

Focused timer, shadow, live callback, birth, sensing-trace, fixture/replay,
control-flow, and birth-audit tests pass. Final complete Linux discovery
passes 1,075 tests in 12.845 seconds. The first Windows full discovery
encountered the already-retained CE-0166 auxiliary-event timing-tail gate;
its isolated 2-test repeat passed, subsequent full discoveries passed, and
the final suite passed all 1,075 tests in 28.568 seconds with three existing
platform skips. This timing
incident neither changes the fixed benchmark threshold nor supplies timer
semantic evidence.

## IDA database corrections

After revalidating instructions, dataflow, the direct caller, and ECL
consumers, the connected database now:

- declares the partial `Th08GameTimingState` layout through
  `gameplay_time_scale` at `+0x188`;
- renames `sub_447421` to `advance_scaled_timer_components`;
- assigns its narrow `__thiscall` component prototype; and
- records evidence comments at `0x00447421`, `0x0044743C`, `0x0044744F`,
  `0x00447461`, `0x00406660`, and `0x004186F1`.

These are material database mutations, not inherited authority. Exact changes
are also recorded chronologically in the 2026-07-29 research-log shard.

## Audit and implementation checklist

- [x] Revalidate the native timer helper/path, fields, callers, comparisons,
      resets, and opcode `0x05` behavior from instructions and dataflow.
- [x] Record exact supported-domain and float32 operation order.
- [x] Apply only evidence-backed IDA rename/type/comment corrections and log
      every database mutation.
- [x] Replace the reduced Phase-B1 timer identity with separate elapsed and
      fraction-bit state.
- [x] Build an independent raw-transition oracle that does not import or share
      the product timer representation or helper.
- [x] Build a tiny native probe for bitwise comparison.
- [x] Cover nonzero fractions, nonunit scales, carry, signed/negative edges,
      resets/preservation, and instruction-threshold crossings.
- [x] Invalidate every affected model/candidate/certificate identity.
- [x] Pass focused Linux and Windows gates.
- [x] Reconcile Phase-B1 authority, CE-0175, roadmap, strategy, handoff, and
      chronological evidence.

## Exit gate

Product, structurally independent Python oracle, and a tiny native probe must
agree bitwise over deterministic and adversarial supported cases. The retained
Phase-B1 fixtures remain explicitly a zero-fraction, observed-scale slice.
This offline gate is passed. Because the corrected existing velocity
lookahead is a live hazard consumer, the fixed observer-off Stage-5 trial is
the next physical falsifier. A hit or accepted pass is evidence about that
whole physical history, not proof that timer rows were active; component
trace telemetry must state whether the corrected path was exercised.
