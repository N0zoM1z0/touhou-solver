# Causal Action-Conditioned Future Body Producer Contract

Date: 2026-07-30

Status: **Causal finite family/differential complete / native event taxonomy
revalidated / complete physical producer absent**

## 1. Physical Objective

For one controller decision, produce every enemy body identity, non-mode
flag, and collision geometry at each reachable priority-11/contact-gate
epoch through the next decision. The result must cover every actuator timing,
cadence, scheduler, RNG, ECL, lifecycle, damage, and external-state branch
declared by the model.

The offline supplied-schedule representation in
`IMMUTABLE_FUTURE_BODY_FLAG_GEOMETRY_SCHEDULE_CONTRACT_20260730.md` is
necessary but not itself a predictive producer.

## 2. Corrected Causal Boundary

One future body schedule cannot generally be chosen independently of the
active input history.

**Observed native/solver dependencies:**

- delayed Focus changes player mode and enemy bit-`0x100 -> 0x800`
  contact/damage gates;
- direction changes player position, which is read by aimed enemy motion and
  other ECL expressions;
- Shot, route, Power, alignment, and damage change HP, phase completion,
  defeat mode, despawn timing, item/Power history, and later route state;
- route-2 SHT callbacks can consume the shared gameplay RNG, which is also
  consumed by timeline and ECL random operations; and
- asynchronous ordered input exposes different active masks before one final
  held action becomes visible.

Therefore the finite producer input is:

```text
(immutable physical root, one selected complete mask,
 one exact actuator active-mask history)
```

Nature may then choose a schedule branch compatible with that history. The
controller must select the root action before nature selects input timing or
schedule branch.

For a selected root action, the immutable producer result is a family:

```text
F = { h -> S_h | h in exact reachable active-mask histories }
```

where `S_h` is one finite schedule support conditioned on exact history `h`.
The family digest covers the selected action/mask, every history, every
schedule-set digest, root physical-update identity, clock version, and source
provenance.

The same `h` may map to multiple hidden world branches. Different histories
may merge at the next controller decision only when their complete native
observation, actuator belief, player/mode state, body flags/geometry, and
family version agree. Neither `h` nor the selected schedule-branch digest is
automatically observable.

An action-independent supplied fixture is valid only when independence is an
explicit premise of that fixture. It cannot be promoted by attaching a live
source later.

## 3. Native Update Order And Producer State

Connected IDA revalidation establishes this priority-11 order:

1. `enemy_manager_update` runs every active stage timeline in ascending
   index order.
2. A timeline spawn calls `enemy_spawn_from_timeline` (`0x0042A4E0`).
3. That helper chooses the first inactive one of 480 slots, copies the
   `0x53D0`-byte enemy template, writes slot/spawn fields, starts the selected
   ECL subroutine, and executes `enemy_ecl_vm_step` immediately. Immediate
   termination clears active bit 0.
4. The manager then scans all 480 slots in ascending order, including newly
   allocated slots. For each eligible active slot it performs the
   secondary-character sync, ECL VM step, motion/bounds/world-position
   composition, offscreen/lifecycle gates, phase transitions, contact, and
   player-shot damage.
5. Contact reads final world position `+0x2D88`, contact extent `+0x2D70`,
   and the post-ECL/post-mode flags.

Two inherited anonymous helpers were revalidated and corrected in the IDB:

- `0x0042C180 -> enemy_clamp_internal_motion_bounds`: when flag
  `0x00080000` is set, clamp internal motion position `+0x2D34/+0x2D38`
  against `+0x3340..+0x334C`;
- `0x0042DEB0 -> enemy_advance_internal_motion_component`: record
  previous/delta values and advance internal position `+0x2D34` from velocity
  `+0x2D4C` using gameplay time scale.

Neither helper alone advances final lethal world position `+0x2D88`.

A complete producer root must therefore bind at least:

- gameplay epoch, route/team, difficulty/rank, stage/phase, physical-update
  clock, immutable ECL image, and exact ECL runtime base;
- all 480 slot allocation states plus a producer allocation generation for
  each slot reuse;
- all live main/auxiliary ECL VM contexts and installed callbacks;
- timeline PCs/timers, markers, indexed-enemy registry, spawn-suppression and
  transition/message gates;
- gameplay RNG state/call count and every modeled consumer before the target
  epoch;
- player position, mode, active/held/pending input, Power/shot state, damage,
  phase/resource state, and relevant global gates; and
- every motion component, bound, parent/link dependency, contact extent,
  non-mode flag, health/timeout/defeat/end state needed by the recurrence.

Pointer or slot alone is not a cross-time body identity. A producer must use
`(slot, allocation_generation)` or an equivalent immutable generational
identity. Retrospective generation-zero fixtures may retain their old compact
integer IDs, but a physical producer must not merge two slot lifetimes.

## 4. Revalidated Event-Class Ledger

| Event class | Existing exact slice | Missing producer boundary |
| --- | --- | --- |
| Stage-timeline births | `th08_timeline_model.py` executes decoded timeline records, RNG, markers, indexed waits, and suppression inputs | live timeline root capture; allocation/template/initial-VM result |
| Allocation and initial VM | native `enemy_spawn_from_timeline` dataflow is observed | solver slot generation, template state, complete initial ECL execution |
| Main VM control/arithmetic | bounded VM-local shadow handles a small exact prefix and returns explicit stop reasons | calls/stack, external variables, random expressions, full opcode effects |
| Child/VM births | opcode catalog identifies `0x5A..0x5E` | exact child allocation/link/relative-position recurrence |
| Motion and geometry | opcode `0xB2`, timers, scale, and some movement primitives are exact offline | opcodes `0x3F..0x4E`, parent/relative composition, callbacks, final `+0x2D88` recurrence |
| Non-mode flags | route-2 `0x100/0x800` synchronization is exact | `0x4F..0x51`, defeat/offscreen/native synthesized bits, `0x8A/0x97/0x9C/0xAD/0xB0/0xB7`, callback writes |
| Despawn/phase reuse | native manager paths and opcode identities are catalogued | terminate/offscreen/clear/HP/timeout/defeat/end execution and slot generation |
| Damage/resource coupling | trace-only HP/damage fields and gate semantics are observed | exact player shots, target intersection, Power, kill/phase timing |
| Shared RNG/action coupling | native SHT callback and timeline/ECL RNG consumers are observed | one ordered joint RNG recurrence across player, timeline, and enemy VM |
| Auxiliary/built-in callbacks | inventories and bounded trace-only observers exist | complete callback semantics and action-dependent effects |
| External scheduler gates | native gates are identified | causal joint support for FRScreen, transition, Bomb/player state, cadence, and issue |

The table is a coverage ledger, not a claim that the right column is small.

## 5. COMPLETE, CONSERVATIVE, And UNKNOWN

A family is `COMPLETE_EXACT` only if:

1. every reachable actuator active-mask history has exactly one family
   member;
2. every member covers the full cadence horizon;
3. every reachable world/RNG/scheduler branch is represented;
4. every native event class affecting identity, flags, or geometry is
   executed exactly; and
5. all body lifetimes have generational identity.

A producer may return `COMPLETE_CONSERVATIVE` only if each omitted effect has
a proved enclosing residual contact volume and lifecycle horizon. The
residual is separate from exact body identities and must be consumed by hard
collision/viability. An empirical speed cap or current-body TTL is not a
proof.

If either condition is unavailable, the result is `UNKNOWN`. `UNKNOWN` is
not an empty schedule, a zero-size residual, a losing certificate, or
permission to maximize separately on hidden histories.

The always-full-playfield residual is conservative but generally destroys
future viability. It is a valid correctness baseline, not an NMNB strategy.

## 6. State, Observation, And Recurrence Questions

1. **Control equivalence:** histories merge only after complete observable
   actuator/player/body state and the immutable family version agree.
2. **Quantifiers:** controller chooses one action; nature chooses compatible
   input timing, world/RNG branch, and cadence; only then may the next
   observation permit another controller choice.
3. **Physical question:** exact solution over a complete family answers the
   declared finite physical recurrence. A fixture family answers only its
   supplied data.
4. **Algorithm:** family enumeration is exact only if it covers the scalar
   actuator history set and never forms incompatible input/schedule Cartesian
   pairs. Missing histories are a falsifier.
5. **Delivery:** the complete family and version must exist before issue.
   Consumers are lookup-only; miss or stale version returns `UNKNOWN` and
   uses the existing live fallback.

## 7. Exit Gates

1. Implement the immutable action-conditioned family and an independent
   differential proving incompatible input/schedule pairs are absent.
2. Add exact generational body identity at the producer boundary.
3. Define and capture the minimum full native root above without changing
   input.
4. Extend the exact-prefix executor one event class at a time. Every
   unsupported opcode/callback/external dependency must stop before mutation
   and publish a named coverage gap.
5. Retain scalar/product differentials for allocation, initial VM,
   child birth, movement/world composition, flags, offscreen/despawn,
   damage/phase, and shared RNG.
6. Only after all relevant classes are exact or conservatively enveloped,
   compose collision/viability and run one non-fail-close stage-level
   falsifier.
7. Revalidate the fixed version on Lunatic Stage 3, Stage 4A, Stage 5, and
   Final B, retaining a native replay whenever the original game naturally
   produces one. Then attempt the full route from Power 0.

No THPRAC or exact-spell activation is required or authorized by this
contract. Physical research units remain complete original-game stages.

## 8. Retained Causal-Family Checkpoint

Exit gate 1 is implemented in
`scripts/th08_causal_future_body_schedule.py`.

- The scalar asynchronous actuator recurrence first enumerates every exact
  reachable active-mask history.
- One immutable family must supply exactly one conditioned schedule set for
  every distinct history. Missing and extra histories fail closed.
- Projection reruns the supplied finite schedule only for the matching input
  history. It never forms the independent actuator/schedule Cartesian
  product rejected by CE-0197.
- The family digest covers the selected action/mask, physical root, clock
  version, and every history-to-schedule mapping.
- The next controller key contains the family version and complete scheduled
  body observation, not the hidden history or member schedule digest.

The deterministic report
`artifacts/runtime_reports/th08_causal_future_body_schedule_differential_20260730.json`
has SHA-256
`d9f4c6202f87b2fd1515bb779284bb2cb4f51f37c08982faa092c1f43ba1898e`.
Linux and Windows generate byte-identical output. A two-edge direction
reversal and asynchronous Focus acquisition contain eight exact actuator
branches. Independent Cartesian composition would admit 24 pairs; the causal
family retains eight and rejects 16 incompatible pairs, with zero mismatch.

Nine focused tests cover compatible pairing, complete history support,
action/mask identity, family digest mutation, immutable containers, horizon
coverage, observation merging, retained-report identity, and cross-family
rejection.
Complete Linux/Windows discovery passes 1,266/1,266 in 14.471/31.192
seconds; Windows retains the three existing skips.

This is still an offline supplied-family representation. It does not
implement allocation generation, native root capture, enemy VM/motion/
lifecycle execution, shared RNG, physical publication, collision/viability,
or live action. Exit gates 2–7 remain open.
