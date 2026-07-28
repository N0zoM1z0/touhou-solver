# G5 Derived-Pattern Source Shadow Contract

Date: 2026-07-28

Status: fixed before implementation. This contract authorizes one default-off,
trace-only observation of already resident TH08 bullet transform state. It
adds no future-hazard coverage, planner, publication, issue, or physical action
authority.

This follows
`G5_REALIZED_BIRTH_TO_HIT_PROVENANCE_CONTRACT_20260728.md` and CE-0160.
The retained witness was first described as an omitted nonspell source because
it occurred outside a spell and had no main-VM intent. The evidence does not
yet identify an enemy VM as its source. This contract tests a narrower and
better-supported alternative: a visible bullet may itself emit the later
bullets through TH08's derived-pattern transform command.

## Evidence And Current Classification

**Observed retained runtime evidence:**

- Stage-5 run `20260728_124930` has a 30-bullet activation observation at
  trace frame 13870 with native support `13868..13869`;
- slots `1280..1294` have age two and slots `1295..1309` have age one, so the
  stable capture is compatible with 15 activations in each of two skipped game
  frames rather than one simultaneous event;
- the geometry forms ten spatial groups of three bullets; and
- the associated decision has no spell owner or boss-registry phase and
  retains only four ordinary enemy-body tracks. Current traces do not retain
  every non-contact enemy VM, so that count does not exclude an enemy source.

**Inferred from the connected IDA database and already documented static
analysis:**

- `bullet_emitter_spawn_pattern` (`0x430E10`) has call sites in
  `enemy_ecl_vm_step` (`0x41B8E7`), `enemy_ecl_emit_bullets`
  (`0x422B6D`), and `bullet_apply_next_transform` (`0x43077E`);
- `bullet_apply_next_transform` (`0x42FFC0`) recognizes transform kind
  `0x1000000`, consumes that record plus the adjacent `0x2000000` parameter
  record, copies the parent's transform program, and emits a child pattern
  from the parent's current position; and
- the pair contains child counts, angles, speeds, type/color, mode, child
  transform start index, and child original-transform flags.

**Hypothesized:** the retained five-groups-per-frame shape is produced by five
parent bullets executing this derived-pattern command on each of two frames.
Neither static xrefs nor shape agreement proves that runtime identity.

## Physical Problem Contract

### Objective

Determine whether a realized bullet activation wave can be joined to a
previously observed, causally available parent-bullet transform source before
the activation. Preserve exact negative results when no such source exists.

### State And Observations

At one controller observation the shadow may use only:

- the already captured immutable 1,536-slot bullet-pool blob and its
  manager-frame endpoints;
- each active parent slot's state, timer age, position, current transform
  flags, original transform flags, transform queue cursor, and the two records
  beginning at that cursor;
- the previous accepted shadow observation and its manager-frame support; and
- later native activation evidence only for retrospective evaluation, never
  for the earlier source decision.

The first implementation must not add process-memory reads. It must not scan
enemy VMs, infer an ECL owner from geometry, or condition an earlier source
label on a later hit.

### Actions And No-Write Semantics

There is no modeled or physical action in this experiment. The controller
continues issuing the unchanged live Boolean policy. The observer writes only
trace records. It must not alter input cadence, complete-mask no-write
semantics, worker scheduling, planner versions, or actuator state.

### Source Predicate

A bullet is a `derived_pattern_ready_candidate` only when the same native
snapshot establishes all of:

1. the parent slot is active;
2. queue cursor is in range for two complete records;
3. the first record kind is exactly `0x1000000`;
4. the second record kind is exactly `0x2000000`;
5. the first kind intersects the parent's original transform flags; and
6. either the first record permits execution while another transform is
   active or the parent's current transform-active mask is zero.

Failing any predicate produces no ready candidate, not a negative future-event
certificate. Malformed cursors, nonfinite geometry, unsupported modes, and
inconsistent records are explicit errors or unsupported classifications.

### Transitions And Uncertainty

The shadow does not yet claim an exact child transition. It retains:

- source capture support and skipped manager frames;
- parent slot and complete raw/decoded record pair;
- parent position and current queue/flag state;
- the exact predicted child count implied by the pair;
- later activation support, slots, ages, geometry, and flags; and
- all plausible parent/source matches when capture gaps or repeated geometry
  prevent a unique join.

Bullet update order, free-slot allocation, same-frame child update, player-aim
mode, RNG, time scale, parent motion before emission, capture span, and skipped
frames remain uncertainty until independently closed. A ready source without a
later activation is a falsifier or unresolved transition, not automatically a
false positive.

### Horizon And Resources

The first join horizon is the next accepted bullet-pool observation, with an
explicit manager-frame gap. Longer scheduling is out of scope. The native
scan uses bounded fixed-capacity output no larger than the 1,536-slot pool and
must perform no heap allocation on the scan path.

### Safety Invariants

- hard no-Bomb remains unchanged;
- output is trace-only and strict JSON;
- nearest-only hit candidates never become exact colliders;
- unsupported source or transition semantics remain `UNKNOWN`;
- no child is published into planner hazards; and
- no survival, feasibility, optimality, or hit-reduction claim follows from a
  source match alone.

### Deadline And Fallback

The observer is not consumed before issue time, but its contention is still a
physical property. It reuses the existing bullet blob, materializes only
candidate rows, and records native-call/materialization/build/emit timing.
The unchanged combined G5 observer gate remains:

```text
p95 <= 0.20 ms
p99 <= 0.40 ms
max <= 2.00 ms
```

No percentile may be hidden outside the measured boundary. Failure disables
the new shadow and retains a performance counterexample; the live controller
continues unchanged.

## Implementation Boundary

The smallest implementation is:

1. an independent scalar Python oracle over synthetic fixed-stride records;
2. a bounded native scanner in a dedicated trace module, not in the viability
   kernel;
3. a narrow Python wrapper with reusable output storage;
4. a source trace record separated from activation evidence; and
5. an offline join that compares source candidates to later activation waves
   without using hit outcome.

The native result must retain parent slot, source-frame endpoints, queue
cursor, current/original flags, both raw records, decoded count/mode fields,
parent geometry, and a finite-geometry bit. It must not allocate one Python
object per active bullet.

If a separate second pool pass fails the unchanged combined performance gate,
the next candidate is a reviewed fusion with the existing native birth scan.
The performance limit is not relaxed to accommodate the feature.

## Deterministic And Physical Gates

Before physical use:

1. scalar/native parity over ready, active-blocked, flag-ineligible,
   wrong-second-record, end-of-program, inactive, malformed, and nonfinite
   cases;
2. exact count and raw-record parity across randomized pool layouts;
3. no tracker-state mutation after a rejected call;
4. stable strict-JSON serialization and offline join digest;
5. focused tests, Ruff, complete Linux tests, native build, and Windows tests;
   and
6. an isolated timing benchmark reporting p50/p95/p99/p99.9/max.

The first physical falsifier is a normal-priority, hard no-Bomb Stage-5 trace
with both activation and derived-source shadows enabled. Acceptance requires:

- executable/foreground/route/difficulty/patch preflight;
- no controller or game process left running at cleanup;
- exact source candidates retained before the target activation wave;
- a deterministic same-session join or an explicit rejected hypothesis;
- native-call and combined observer timing under the unchanged limits; and
- compact retained provenance, timing, hit/Bomb/resources, and phase report.

One matching run establishes only observed source attribution for that wave.
It does not establish complete derived-pattern coverage or strategy promotion.

## Formal Questions

1. **Which histories map to one state?** Only histories with identical parent
   slot generation, capture support, queue cursor, current/original flags,
   record pair, parent geometry, and declared uncertainty may merge. Because
   the shadow has no action, this is provenance equivalence, not yet control
   equivalence for a future planner.
2. **Are all uncertainty branches represented?** The first experiment does
   not solve a recurrence. It explicitly retains capture gaps, multiple source
   matches, update/allocation ambiguity, aim/RNG/motion uncertainty, and
   unsupported modes instead of selecting one hidden branch.
3. **What physical question would exact solution answer?** Exact joining would
   answer whether one realized activation wave came from an earlier visible
   parent source. It would not answer whether all future hazards were covered
   or whether another action survived.
4. **What does the algorithm prove, and what falsifies it?** It recognizes the
   exact static readiness predicate and retrospectively tests its realized
   consequence. A missing ready parent for the target wave, mismatched child
   counts/geometry, scalar/native disagreement, or timing failure falsifies
   the current hypothesis or implementation.
5. **Can it be consumed before issue?** No consumer exists in this contract.
   Any later consumer requires a new immutable source/transition version,
   conservative uncertainty semantics, deadline proof, and fresh local hard
   certificate.

## Stop Rules And Next Decision

Stop without broadening scope if the Stage-5 wave has no derived parent
candidate. Retain that negative result and then investigate ordinary enemy
main VMs, auxiliary VMs, callbacks/interrupts, deferred enemy state, and
non-ECL native sources in that order.

If the wave matches, the next contract may model only the observed
derived-pattern transition class. Enemy source coverage remains open, and the
canonical first hit's much earlier bullet still requires parallel
viability-preservation work.
