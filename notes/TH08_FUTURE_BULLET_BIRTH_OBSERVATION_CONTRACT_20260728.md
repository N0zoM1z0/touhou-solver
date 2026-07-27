# TH08 Future Bullet-Birth Observation Contract

Date: 2026-07-28

Status: fixed G5 observation-only problem contract. This note authorizes a
default-off trace and offline audit only. It adds no hazard-coverage,
planner, publication, issue, epoch-reset, or physical action authority.

This contract refines
`PIPELINE_ROOT_AND_HAZARD_COVERAGE_CONTRACT_20260727.md` for the first future
event class in G5. The augmented input-pipeline recurrence and the open
CE-0120 clock boundary remain unchanged.

## Outcome

The first bullet-birth checkpoint will establish a causal, reviewable join
between:

1. the enemy-ECL emission intent visible before a birth;
2. the native hostile-bullet slot that actually becomes active;
3. the native bullet age and capture interval that bound the activation
   frame; and
4. the update order under which a new bullet can move and collide in that
   same game update.

It will not yet turn a recognized ECL fire instruction into free-space or
future-geometry authority. A schedule match is retrospective evidence. Full
birth coverage additionally requires exhaustive source discovery, causal
branch support, conservative initial geometry, pool-allocation semantics,
and all same-frame transitions.

## Evidence Labels And Present Boundary

- **Observed:** the existing live sensor already captures the complete
  1,536-slot hostile-bullet pool into a persistent destination buffer between
  two manager-frame reads. Active state, position, velocity, geometry, and
  transform state are decoded from that same buffer.
- **Observed:** current physical G5 traces mark future coverage `UNKNOWN` from
  the first successor. No current result has bullet-birth authority.
- **Observed:** shipped Stage-4A ECL contains direct-fire opcodes and both
  literal and VM-derived parameters. Existing live ECL lookahead follows only
  one boss main VM and only enough literal flow to attach callback-12
  velocity toggles.
- **Inferred from the connected IDA database:** `enemy_ecl_emit_bullets`
  (`0x422720`) implements direct-fire opcodes `0x60..0x68`, evaluates the
  parameter mask, applies minimum-distance and rank-dependent changes, and
  calls the emitter. `bullet_emitter_spawn_pattern` (`0x430E10`) expands the
  descriptor into individual spawn calls.
- **Inferred from the connected IDA database:**
  `bullet_spawn_from_emission_descriptor` (`0x42F5F0`) allocates the first
  free slot from a wrapping 1,536-slot cursor, initializes the bullet timer
  and runtime fields, and has aimed and random mode dependencies.
- **Inferred from the connected IDA database:** `bullet_manager_update`
  (`0x431240`) runs after enemy emission at priority 14, scans slot 0 and then
  slots 1,535 down to 1, moves and collision-tests a newly active bullet in
  the same update, and advances its timer at the end. It passes bullet
  `+0x0D8C` to `timer_current` (`0x40D3B0`), whose accessor returns the signed
  integer at timer `+0x08`; the candidate native age is therefore bullet
  `+0x0D94`.
- **Observed in the executable base-state oracle:** new
  `spawns_before_update` participate in the same later bullet-pool pass and
  can collide immediately. This is a deterministic implementation fixture,
  not independent shipped-runtime proof.
- **Unknown:** the exact runtime interpretation of the candidate timer field
  across every bullet state, freeze, transform, cancel, and slot reuse has not
  yet been physically joined to ECL emission. That is the purpose of this
  gate.

Static conclusions above remain inferred until the native runtime trace
confirms them. No IDA database rename or type change was required because the
three functions already have strong local names and comments.

## Problem Contract

### Physical objective

Eventually cover every hostile-bullet birth that can enter a root-reachable
player tube during a claimed robust-survival horizon. The present checkpoint
has the narrower physical objective of measuring births and their causal ECL
preconditions without changing no-Bomb Sakuya/Remilia control.

### State and observations

One birth-audit observation is tied to an immutable capture identity:

```text
(
  gameplay epoch, route, difficulty, stage, spell,
  manager frame at policy source,
  bullet capture [frame_before, frame_after],
  ECL capture [frame_before, frame_after],
  exact enemy slot/pointer and main-VM snapshot identity,
  bullet-pool layout version,
  ECL/opcode model version
)
```

The TH08 observation adapter may derive two narrow records.

```text
BulletBirthObservation {
  slot,
  active state,
  candidate native age,
  capture frame interval,
  position, velocity, geometry,
  transform flags,
  evidence status and rejection reason
}
```

```text
EclBirthIntent {
  enemy slot/pointer,
  VM instruction pointer and timer,
  instruction address/time/opcode/mode,
  physical activation-frame support,
  parameter-mask/literal classification,
  flow stop reason,
  unsupported dependency set
}
```

The audit must retain source identity and uncertainty. It must not collapse an
interval to one frame merely because the manager frame was equal at two
reads.

The first implementation reads `BulletBirthObservation` from the already
captured pool blob. It does not add the age field to the planner `Bullet`
model and does not add another process-memory read. ECL intent scanning lives
in a separate TH08 adapter and cannot mutate the existing callback
lookahead.

### Actions and actual issue semantics

There are no actions in this gate. The birth observer and ECL scanner:

- do not select or rank input;
- do not write input;
- do not emit Bomb bit `0x02`;
- do not change cadence, held/pending estimates, policy version, or scene
  state; and
- do not reclassify any `UNKNOWN` hazard slab.

When disabled, the controller executes the existing path without constructing
birth records. When enabled, any observation error drops only the audit
record and preserves the ordinary live fallback.

### Uncertainty and transitions

The audit explicitly carries:

- bullet-pool capture span and ECL capture span;
- the unresolved relation between manager frame and physical input time;
- timer-field interpretation and integer/fractional update ordering;
- slot release and reuse inside a capture interval;
- wrapping allocation cursor and pool exhaustion;
- multiple bullets emitted by one descriptor;
- minimum-fire-distance suppression;
- difficulty, route, rank, and time-scale dependencies;
- VM-valued parameters and conditional/call/interrupt control flow;
- player-aim and random-number dependencies;
- deferred fire and `emit_current_pattern`;
- enemy child/auxiliary VMs and callbacks;
- transform-bearing births; and
- same-frame movement, collision, clear, and cancel effects.

Unsupported control flow or a non-exhaustive dependency produces an explicit
residual reason. It never produces one guessed branch. The initial scanner
may recognize a fire instruction while classifying its geometry or schedule
as unsupported.

The audit is causal: an intent may be joined only if its VM snapshot was
captured no later than the supported birth interval. A later observation
cannot be used as if it had been available to the controller before birth.

### Horizon and resource constraints

The observation horizon is configurable and initially bounded by the current
80-frame global-planning horizon. Instruction scanning has a fixed maximum
count and stops fail-closed on repeated state, unsupported flow, invalid
memory, or the instruction limit.

The trace stores only compact birth/intention/residual records. It does not
duplicate full pool blobs. Raw physical JSONL remains local and ignored;
compact coverage reports and deterministic fixtures are retained.

### Safety invariants

- Survival remains hard and Bomb remains forbidden.
- Current live Boolean guidance and the fresh issue-time local certificate
  retain all action authority.
- A detected native birth is retrospective evidence, not a forecast.
- A recognized ECL opcode is not proof that it emits under the captured
  branch.
- A matched intent/birth pair is not proof that all birth sources were
  enumerated.
- A literal schedule is not a conservative spatial envelope.
- Missing enemies, VMs, instructions, timer evidence, or event classes remain
  `UNKNOWN`.
- Player-aim, RNG, rank mutation, deferred fire, callbacks, pool exhaustion,
  transforms, and unsupported flow are not filled with nominal values.
- The first native hit of a fresh attempt remains the canonical physical
  causal witness.

### Computation, publication, and fallback deadline

The age observer reuses the persistent bullet-pool destination buffer and
performs no additional RPM. Before physical use, its extraction-only gate is:

```text
p95 <= 0.20 ms
p99 <= 0.40 ms
max <= 2.00 ms
```

on the retained 1,536-slot density corpus. It must also preserve the existing
planning decode output bit-for-bit and add no more than 5% to interleaved
decode/trace p95. Every timing report states whether scan, ECL instruction
reads, join, serialization, and trace flush are included.

Cold ECL expansion is forbidden on the issue thread. The initial trace-only
scanner may use immutable cached instructions already available to the live
lookahead; a later all-enemy service requires a separate delivery/contention
gate.

An audit timeout, exception, invalid field, stale identity, or budget failure
omits the optional record. It cannot delay issue or alter the selected mask.

## Coverage Result Model

Birth work uses orthogonal statuses:

```text
ObservationStatus:
  COMPLETE | CAPTURE_SPANNED | INVALID_TIMER | SLOT_REUSE_AMBIGUOUS
  | UNAVAILABLE

IntentStatus:
  LITERAL_CAUSAL | FINITE_SUPPORT | DYNAMIC_PARAMETER | PLAYER_AIM
  | RNG | DEFERRED | UNSUPPORTED_FLOW | UNKNOWN_SOURCE

JoinStatus:
  EXACT | FRAME_SUPPORT_MATCH | AMBIGUOUS | UNMATCHED_BIRTH
  | UNREALIZED_INTENT | NOT_ATTEMPTED

CoverageAuthority:
  TRACE_ONLY | NONE
```

`TRACE_ONLY` never changes the G1 `HazardCoverageAssessment`. A later proposal
may define `DETERMINISTIC`, `FINITE_SUPPORT`, or `BOUNDED_ENVELOPE` birth
slabs only after every residual source class is closed or conservatively
contained.

## Formal Review

1. **Which histories map to one model state?** None are merged for control in
   this gate. Audit records can be compared only when their exact
   capture/epoch/layout/ECL identities match. A capture span, timer ambiguity,
   or unobserved slot reuse remains explicit.
2. **Does the recurrence include every uncertainty branch?** This gate adds no
   control recurrence. Intent scanning keeps finite branches only when they
   are exhaustively enumerated; otherwise it records the unsupported
   dependency and stops. It never maximizes separately over a hidden branch.
3. **What physical question does an exact result answer?** It can answer
   retrospectively which native slots were newly born in a bounded capture
   interval and whether an earlier supported ECL intent can explain them. It
   does not answer whether the future hazard field is complete.
4. **What is solved or bounded, and what falsifies it?** Timer extraction and
   intent/birth joins are measured, not safety proofs. Falsifiers include a
   runtime birth with an impossible reported age, a slot reuse hidden by the
   decoder, a birth without a retained residual source, an ECL prediction
   outside the observed interval, pool-exhaustion disagreement, or shipped
   same-frame collision behavior that differs from the fixture.
5. **Can the result be consumed before issue time?** No. It is default-off
   trace-only evidence. Any future consumer requires a new immutable
   coverage version, background completion, lookup-only exact-version
   delivery, a fresh local intersection, and explicit strategy promotion.

## B1 Result

Checkpoint `4260113 Add trace-only bullet birth observer` implements the
native-age observation seam without integrating it into the live controller:

- a focused `th08_live.bullet_birth` module reads state and signed timer
  current at bullet `+0x0D94` from the existing persistent pool blob;
- a compact tracker retains first-capture recent candidates, inactive-to-active
  edges, active-slot timer regressions, invalid timers, capture support,
  geometry, velocity, and transform flags;
- the tracker copies only the 1,536 state and age fields between captures and
  neither retains another 6.3-MiB pool blob nor mutates it;
- malformed pools, invalid capture intervals, negative active timers,
  non-finite geometry, release/reuse, and deterministic serialization are
  covered by ten focused tests;
- existing planning decode is byte/object unchanged; and
- the module is not constructed by the controller yet, so disabled-path cost
  and action behavior are exactly unchanged.

The fixed 5,000-iteration retained gates pass:

| Platform | Full-pool p95 | p99 | max | decode+observer/decode p95 |
| --- | ---: | ---: | ---: | ---: |
| Linux | 0.0318 ms | 0.0540 ms | 0.3199 ms | 0.998 |
| Windows | 0.0339 ms | 0.0453 ms | 0.1005 ms | 1.007 |

Reports:

- `artifacts/benchmarks/bullet_birth_observer_linux_20260728.json`,
  SHA-256
  `b77ed72fd9e779f4b903d9caeaae7af1436e235885df4c9df96993f1dc4c2e18`;
- `artifacts/benchmarks/bullet_birth_observer_windows_20260728.json`,
  SHA-256
  `4bb018a6c84839d93bbcb3b0da21cc50cacbff259208ce91d248eee9a428d56c`.

Complete Linux/Windows quick suites pass `752/752` in `9.227/14.904 s`, with
three existing Windows skips. B1 establishes cheap retrospective evidence
only. B2–B5 and the first physical trace remain open.

## Ordered Gates

### B0 — Contract and static evidence

- Fix this problem contract before code.
- Retain the IDA addresses, inferred call chain, timer candidate, allocation
  order, and update-order conclusion.

### B1 — Native-age observation

- **Implemented and offline-gated by checkpoint `4260113`; physical
  integration remains open.**
- Add a narrow TH08 pool-blob observer, independent of planner `Bullet`.
- Test empty/full pools, malformed blobs, inactive stale timers, age zero,
  capture spans, slot release/reuse ambiguity, and deterministic output.
- Prove existing Python/native planning decode output is unchanged.
- Benchmark sparse and 1,536-active cases against the fixed budget.

### B2 — Update-order fixture

- Extend deterministic adversarial cases for spawn, pool full/drop, scan
  order, same-frame movement/contact, graze threshold, cancel, and slot reuse.
- Keep the game-neutral scalar fixture independent of any future optimized
  implementation.

### B3 — ECL intent classification

- Add a separate main-VM birth scanner with explicit stop reasons.
- Cover direct, deferred, current-pattern, child/aux-VM, callback, aimed, RNG,
  rank, dynamic-parameter, pool-full, and transform residual classes.
- Do not implement an unrestricted ECL simulator.

### B4 — Focused physical trace

- Run a hard-no-Bomb Lunatic Stage-4A focused trial with the observer enabled.
- Retain accepted-session provenance, first-hit witness, timer distributions,
  capture spans, extraction/serialization tails, observed births, and zero
  action differences.
- Repeat on Stage 5 or 6 only after Stage-4A trace semantics pass.

### B5 — Residual report

- Join earlier ECL intents to observed births.
- Report total births, exact/support/ambiguous/unmatched joins, every residual
  reason, and event/source coverage by stage/phase.
- Two generations from the same inputs must be byte-identical.

### B6 — Separate coverage proposal

Only after B0–B5 pass may a new note propose a conservative birth envelope or
finite support for a narrowly declared event subset. The proposal must still
show that uncovered sources cannot enter the reachable tube, pass the
semantic differential/fuzzer and physical repetition gates, meet delivery,
and leave all other event classes `UNKNOWN`.
