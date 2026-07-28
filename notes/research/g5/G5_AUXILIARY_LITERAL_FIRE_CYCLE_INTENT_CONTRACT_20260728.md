# G5 Auxiliary Literal Fire-Cycle Intent Contract

Date: 2026-07-28

Status: **fixed for offline implementation and default-off trace-only
validation**. No future geometry, source-completeness, planner, feasibility,
publication, or live-action authority is granted.

This is the first one-event-class auxiliary-ECL lowering gate after:

- coherent bounded-retry auxiliary-context observation;
- exact shipped Stage-5 runtime-ECL byte identity; and
- static revalidation of the auxiliary scheduler and selected opcode handlers.

It deliberately models one small event class instead of claiming a general
auxiliary VM.

## Selected Event Class

The selected class is a **literal auxiliary direct-fire cycle intent**:

1. start from one coherent active auxiliary-VM snapshot;
2. follow only exact difficulty skips, literal bullet-transform definition
   `0x6F`, literal direct-fire `0x60..0x68`, and literal jump `0x04`;
3. report each reached direct-fire descriptor as an intent with all unresolved
   emission and geometry dependencies attached; and
4. stop at every instruction, state dependency, timing conversion, source
   transition, or version mismatch outside that closed subset.

An intent means only that the captured auxiliary VM's literal path reaches a
direct-fire opcode in ECL timer time. It is not a realized bullet birth, a
complete emission descriptor, a geometric forecast, or evidence that the
owner remains alive long enough to execute it.

## Pre-Contract Evidence

### Retained runtime observation

The accepted Stage-5 spell-107 trace
`lunatic_route2_stage5_unattended_20260728_200739` has:

- raw SHA-256 `953a5c3c...79e9`;
- 123 coherent selected auxiliary batches;
- 3,214 usable contexts, all at call depth zero;
- 1,058 unique active-VM hashes; and
- usable target-subroutine counts `69: 789`, `72: 818`, and `73: 1,607`.

The target histogram was obtained by a bounded streaming pass over compact
`auxiliary_vm_batch` records. It is **observed** trace evidence.

The old compact schema retains `target_subroutine`, call depth, marker, and
the active-VM SHA-256, but not the raw active PC, timer, or locals. Therefore
that trace cannot be replay-lowered into exact event times. A hash is equality
evidence only; it is not a reversible VM state. This limitation must remain
visible in every report.

### Exact Stage-5 instruction image

Run `lunatic_route2_stage5_unattended_20260728_212622` observed the complete
47,224-byte runtime image and normalized it byte for byte to
`artifacts/decoded/ecldata5.ecl`, SHA-256
`3148f45faf78bd8211a956edcdc353be73d2781995d3dadd36bdca8132f8fe19`.

This establishes an exact instruction-byte key for that immutable image. It
does not establish a reachable path, operand value, scheduler phase, or
physical emission.

### Shipped Stage-5 target programs

Parsing the exact decoded image gives:

| Subroutine | Literal sequence | Cycle timer |
| ---: | --- | ---: |
| 69 | `0x6F @ 0`, `0x63 @ 0`, `0x04 @ 8` | 8 |
| 72 | `0x6F @ 0`, `0x63 @ 0`, `0x04 @ 8` | 8 |
| 73 | `0x6F @ 0`, `0x63 @ 0`, `0x04 @ 30` | 30 |

Each jump has parameter mask zero, assigns integer timer elapsed zero while
preserving the fractional accumulator, and targets the direct-fire
instruction rather than the preceding transform definition. Each direct-fire
has literal count fields `2 x 1`; whether two slots are realized still depends
on spell/emission guards and pool state. Its color is VM-parameter `10007`;
transform-program, owner state, template, origin, pool, and later bullet
behavior remain unresolved.

These are exact static-image observations. Whether and when one physical
context executes them is a runtime question.

## Revalidated Native Semantics

The following were re-read from shipped instructions in the connected IDA
database. Inherited names and comments were not treated as authority.

- `enemy_ecl_vm_step` begins at `0x004184B0`.
- At `0x0041850A..0x004185B6`, the interpreter reads the current instruction
  pointer, checks the VM timer against the instruction time, and dispatches
  only when the timer matches.
- Opcode `0x04` at `0x004186F1..0x0041870F` stores argument 0 into VM timer
  integer elapsed at active VM `+0x0C`, preserves the float32 fractional
  accumulator at `+0x08`, adds signed relative argument 1 to the current
  instruction pointer, and continues interpretation in the same update.
- `timer_elapsed_eq` at `0x0040D3F0` compares only integer elapsed. Timer
  advance reaches `sub_447421` through `0x00406660` and uses the gameplay
  time scale: values above `0.99000001` increment elapsed directly; smaller
  positive values accumulate in the float32 fraction and carry at one.
- Opcodes `0x60..0x68` share the handler at
  `0x0041B4E6..0x0041B51F`. A positive owner emission guard is required.
  Enemy flag `0x00020000` stages the 44-byte descriptor; otherwise the
  handler calls the bullet emitter.
- Opcode `0x6F` begins at `0x0041B535` and writes one of 18 shared
  enemy-owned 24-byte transform records. Parameter-mask bits resolve its
  seven arguments in order.
- Opcode `0x87` at `0x0041CDFF..0x0041CF7F` allocates and starts the
  auxiliary context and copies parent VM locals `+0x18..+0x8F`.
- At `0x0041EBBC..0x0041EC77`, the scheduler visits four auxiliary contexts
  after the main VM and records auxiliary marker `index + 1` in active VM
  `+0x220`.

These are **observed statically**. The physical trace must still establish
capture/version coherence and event-to-birth alignment.

## Physical Problem Contract

### Physical objective

Expose one previously invisible auxiliary source timing signal so later
research can test whether incomplete ECL source knowledge contributes to
kernel exhaustion. Full-route survival remains hard; this observer cannot
change input.

This also supports, but does not prove, the separate nonspell
kill-before-saturation hypothesis. A source intent can help attribute future
emission opportunities to a still-living ordinary enemy. Power collection,
enemy damage, and target selection remain in the Stage-5 combat research
contract rather than becoming fields of this event model.

### State and observations

One model root contains:

```text
(immutable executable identity,
 immutable exact runtime-ECL identity and runtime base,
 selected auxiliary-batch version,
 gameplay epoch / route / stage / difficulty,
 selected manager frame,
 owner slot and auxiliary index,
 owner flags before/after,
 context pointer before/after,
 target subroutine,
 call depth and saved-frame count,
 active 0x228-byte VM snapshot,
 optional capture-aligned positive finite gameplay time scale)
```

The active VM contributes raw instruction pointer, timer fraction and elapsed,
integer and float locals, and auxiliary marker. No field may be reconstructed
from the active-VM hash.

Two histories with the same active PC but different timer bits, locals,
owner/context generation, target subroutine, difficulty, runtime image,
transform state, deferred state, or time-scale information are not
control-equivalent for this event class.

### Actions and issue semantics

There are no model actions. Observation and lowering are post-issue,
default-off research work. Complete-mask issue/no-write semantics, cadence,
pickup delay, and hard no-Bomb behavior remain unchanged.

### Uncertainty and transitions

The lowerer is deterministic only on the closed literal subset. It must emit
`UNKNOWN` for:

- runtime-image or base mismatch;
- unusable, changed, or unowned context;
- invalid PC, instruction size, target, timer, local projection, or marker;
- missing or non-positive physical time scale when a physical-frame offset is
  requested;
- nonliteral or parameterized jump;
- timer reset, loop-decrement, conditional, call, return, interrupt,
  callback, auxiliary start, child source, or unknown opcode;
- any nonliteral `0x6F` argument;
- repeated state or instruction-budget exhaustion;
- deferred-versus-immediate emission not established by coherent owner flags;
  or
- owner guard, minimum-distance gate, route/enemy fire filter, spell state,
  pool capacity, dynamic parameter, template, emission origin, transform
  program, aimed/RNG mode, and geometry not present in the observation.

Literal `0x6F` may be traversed only as an observed mutation on the current
path. The result records that mutation and preserves
`transform_program` as a residual dependency. It does not claim the
enemy-shared transform table is isolated from another main or auxiliary VM.

### Horizon and resource constraints

- The first offline profile uses timer-elapsed horizons `0`, `8`, `30`, and
  `80`. They are not physical-frame offsets without the authorized time-scale
  recurrence.
- The instruction budget is fixed and explicit; initial implementation uses
  at most 64 instructions per context.
- Repeated `(PC, exact timer bits, timer-domain offset)` state stops
  fail-closed.
- At most the 256 already bounded auxiliary records are considered.
- No additional process read is allowed for pure lowering of a selected
  auxiliary batch.

### Safety invariants

- Output is intent-only and contains no bullet geometry.
- `UNKNOWN` may never be consumed as empty or safe.
- Unsupported branches are merged into unresolved coverage, never maximized
  as if their hidden state were observed.
- Event rows are keyed by the complete selected observation version, not by a
  recycled heap pointer alone.
- No output changes a planner field, viable mask, score, target, key, cadence,
  or Bomb behavior.

### Deadline and fallback

Offline lowering has no issue deadline. A later live trace integration must
run after current issue and reuse the already captured active VM bytes.
Missing identity, time-scale, or dependency evidence produces an
unavailable/`UNKNOWN` record. The live fallback remains exactly the current
Boolean policy plus fresh local hard certificate.

## Lowering Semantics

The production lowerer has two explicitly separate outputs:

1. **timer-domain intent:** exact target integer elapsed and path order on the
   accepted literal path; and
2. **physical-frame intent:** present only when the captured time scale is
   positive, finite, and authorized by the exact observation version.

At each instruction:

1. compare instruction time to integer elapsed exactly as native
   `timer_elapsed_eq` does; a later instruction advances only the abstract
   timer-domain target unless the physical time-scale recurrence is present;
2. apply the active difficulty mask exactly;
3. for literal `0x6F`, validate and record its literal mutation, then advance;
4. for `0x60..0x68`, decode the descriptor, attach every unresolved
   dependency, publish one intent, then advance;
5. for literal `0x04`, assign target integer elapsed, preserve fractional
   state, and apply relative PC exactly; and
6. for `0x01`, publish exact terminal completion with no later event on this
   VM path; otherwise stop with the first precise unavailable reason.

An intent whose residual dependency set is nonempty is not a complete
emission. Even an empty descriptor dependency set would still require a
separate realized-birth and geometry contract.

## Independent Oracle And Falsifiers

The independent scalar oracle must parse raw VM and instruction bytes itself.
It may share constants and immutable fixtures, but not the production walker,
state-transition helper, or result serializer.

Required deterministic cases include:

- root at transform, fire, and waiting jump;
- the exact subroutine 69/72/73 programs and timer thresholds `8/8/30`;
- zero and nonzero timer fractions using exact float32 bits;
- difficulty skip;
- dynamic color dependency;
- nonliteral transform and jump rejection;
- call/return, conditional, reset, unknown opcode, invalid size, invalid PC,
  nonfinite timer/time-scale, repeated state, and instruction limit;
- active pointer/owner churn and runtime-image mismatch;
- timer-domain availability with physical-frame unavailability;
- no geometry in every result; and
- byte-identical deterministic report generation.

Minimal falsifiers are:

1. production and oracle disagree on one accepted transition or stop reason;
2. a retained raw active VM maps outside the exact image or target subroutine;
3. a reported literal event fails to align with a compatible realized
   activation window;
4. an omitted dependency changes whether or what the native handler emits;
5. another VM overwrites shared transform state before the event and the
   report labels geometry complete; or
6. trace integration changes issue timing, cadence, mask, or physical action.

## Architecture Boundary

- Keep `scripts/th08_ecl_auxiliary.py` as a narrow stable facade and split the
  reusable TH08 implementation by state, exact image, timer, descriptor,
  traversal, and batch responsibilities under
  `scripts/th08_ecl_auxiliary_core/`.
- Put the structurally independent oracle and retained-trace/report logic
  under `scripts/analysis/auxiliary_ecl_event/`.
- Keep `scripts/th08_live/auxiliary_vm/trace_service.py` responsible only for
  coherent capture orchestration and compact trace delivery.
- Do not add the interpreter, static image parser, or report logic to
  `scripts/th08_live/controller.py`.
- If runtime integration is later accepted, expose one narrow stage/service
  call and one immutable configuration object.
- Keep exact workload construction and timing under
  `scripts/benchmarks/auxiliary_ecl_event/`; compact batch canonicalization
  may merge only states equivalent for the declared unresolved intent
  recurrence and must preserve a result mapping for every request.

## Performance Gates

Offline Linux and Windows reports must include p50/p95/p99/max for:

- one-context lowering;
- the retained maximum-density 34-context batch;
- result serialization; and
- combined lower-plus-serialize time.

For the 34-context batch, fixed initial post-issue limits are:

- lower-plus-serialize p95 at most `0.50 ms`;
- p99 at most `1.00 ms`; and
- max at most `3.00 ms`.

A later physical gate retains the accepted bounded-retry native limits and
requires at most one-frame cadence p95 regression. No extra process read,
hidden cold file read, issue-thread work, or unbounded allocation is allowed.
A small bounded post-issue regression may be weighed against source signal,
but an action-path or coherence regression fails.

## Ordered Gates

1. **This checkpoint:** freeze the event class, residual dependencies,
   authority, independent oracle, and fixed gates.
2. Implement production and independent scalar lowerers with synthetic and
   exact Stage-5 fixtures.
3. Add a streaming compact inventory/report. It must state that the retained
   `200739` hashes cannot recover PC/timer state.
4. Pass focused tests, differential/adversarial cases, Ruff, and complete
   Linux/Windows suites.
5. Benchmark one-context and 34-context profiles on both platforms.
6. Integrate default-off post-issue trace derivation from the selected raw
   batch without an extra process read.
7. Run one focused Stage-5 spell-107 physical gate retaining PC/timer-derived
   rows, complete version identity, timing, cadence, hard no-Bomb behavior,
   and exact cleanup.
8. Join reached intent windows to realized activation batches. Nonmatches and
   unresolved dependencies remain counterexamples or unavailable rows.
9. Only after repeated physical evidence, separately contract one geometry
   or source-life extension. Do not promote this intent class directly into
   live guidance.

## Formal Review

1. **Control-equivalent histories:** image, observation version, owner/context
   identity, PC, timer, locals, target, difficulty, and dependency state are
   explicit; hashes and recycled pointers do not merge histories.
2. **Uncertainty and causality:** only a single observed literal path is
   traversed. Every hidden branch or emission dependency terminates or remains
   explicit, so no hidden nature branch becomes a controller choice.
3. **Physical versus proxy:** exact lowering answers the target integer timer
   state at which one captured VM reaches a direct-fire opcode. A physical
   frame offset additionally requires the native time-scale recurrence. It
   still does not answer whether bullets are emitted, what geometry results,
   or whether an action survives.
4. **Algorithm and falsifier:** a bounded deterministic interpreter is checked
   against an independently written scalar byte oracle, exact shipped
   fixtures, adversarial malformed cases, and later birth alignment.
5. **Deadline and fallback:** offline work has no issue authority; later
   tracing is post-issue and exact-version-only. Misses remain `UNKNOWN`, and
   live control falls back without starting cold work.
