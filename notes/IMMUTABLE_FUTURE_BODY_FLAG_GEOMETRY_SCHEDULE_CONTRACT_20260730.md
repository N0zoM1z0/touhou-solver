# Immutable Future Body/Flag/Geometry Schedule Contract

Date: 2026-07-30

Status: **Offline immutable representation/body-set differential complete /
physical predictive producer absent**

## 1. Physical Objective And Audit Result

The physical objective is to supply every SEM-MODE transition before issue
with the complete enemy body identity, mode-independent flags, and geometry
at every reachable priority-11/contact-gate epoch.

The current repository has no such predictive producer.

**Observed:**

- `th08_live.pipeline_shadow._unknown_future_coverage` marks the entire
  root+1 finite horizon `UNKNOWN` because current snapshots do not exhaust
  unseen births or event geometry.
- `enemy_flag_frames` is supplied only by deterministic tests and post-hoc
  endpoint audits. No live caller produces it for a future decision.
- current enemy body memory extrapolates already observed bodies with growing
  uncertainty; it cannot enumerate unseen births, ECL flag writes, despawns,
  transforms, or exact future geometry.
- the G5 future-event work retains useful bullet/ECL-source hypotheses, but
  it does not cover the complete enemy body identity set, every non-mode flag,
  or per-update body geometry.
- the retained Stage-5 mode trace is decision-bracketed. It does not contain
  one complete body/geometry capture for every intervening player/enemy
  physical update, and its supervisor generated no compatible native replay.

**Inferred:** treating a current snapshot projection, stable endpoint pair,
or G5 birth subset as a complete immutable future schedule would be
optimistic with unknown direction. It remains outside hard safety authority.

## 2. Staged Representation

Version 1 is deliberately offline-only. It represents a complete finite
schedule supplied by a deterministic fixture or retrospective exact source;
it cannot declare physical predictive authority.

One body sample contains:

```text
b = (identity, base_flags, x, y, half_width, half_height, uncertainty)
```

Requirements:

- `identity` is a nonnegative native pointer/slot identity;
- geometry and uncertainty are finite canonical binary32 values;
- extents and uncertainty are nonnegative;
- identities are sorted and unique within one physical step;
- if active flag `0x100` requests route-2 character synchronization,
  `base_flags` has mode bit `0x800` cleared.

Clearing only `0x800` makes the schedule independent of the controller's
Focus history. Priority 11 restores that bit from the branch's delayed
secondary-character state. Every other flag bit, birth, death, and geometry
change belongs to the producer, not the mode projection.

One schedule branch is an ordered nonempty sequence of physical steps. One
schedule set is a sorted, unique set of equal-horizon branches plus:

- root physical-update identity;
- exact clock-version identity;
- source/provenance identity; and
- a canonical SHA-256 digest over every body, flag, and binary32 geometry
  word.

One branch means deterministic finite input. Multiple branches are one
declared finite nature support. The controller action is selected uniformly
before nature chooses a branch.

CE-0197 and
`CAUSAL_ACTION_CONDITIONED_FUTURE_BODY_PRODUCER_CONTRACT_20260730.md`
forbid promoting one exogenous schedule through an independent Cartesian
product with asynchronous active-mask histories. Version 1 remains valid for
explicitly action-independent supplied fixtures. A physical producer must
publish one immutable history-conditioned schedule family.

## 3. State, Observation, And Causality

The enclosing asynchronous actuator/mode state remains:

```text
(active mask, held final mask, ordered suffix, completion deadline,
 player mode tuple)
```

The immutable schedule-set version is part of the problem version and the
next controller observation key. The selected hidden schedule-branch digest
is not observable and must not be exposed to controller maximization.

For every physical step:

1. the prior native active mask drives priority 9;
2. the exact player mode tuple advances;
3. priority 11 overwrites only body flag `0x800`;
4. contact and player-shot-damage body sets are projected;
5. body geometry remains attached to the same identity for later collision
   composition; and
6. priority 17 may publish the next input mask.

No body/flag/geometry branch may depend on an action selected after that
step. If the native program makes future ECL or movement action-dependent,
that dependency must be represented causally in the producer rather than
preselected clairvoyantly.

## 4. Horizon, Resources, Safety, And Deadline

The schedule must cover the largest declared recursive cadence branch. A
short branch, missing physical step, duplicate identity, noncanonical
geometry, changed root/clock/source identity, or absent version is
`model_unknown`.

Survival remains hard. A schedule-set consumer may project body identities
offline, but version 1 has:

- no live action authority;
- no hard collision/viability authority;
- no damage or unfocused-combat authority;
- no publication/deadline authority; and
- no NMNB authority.

The live fallback remains the existing Boolean policy plus fresh local hard
certificate. A missing exact schedule must not be interpreted as an empty
body set or free space.

## 5. Approximation And Falsifiers

Version 1 omits:

- a predictive native/ECL producer;
- physical completeness proof across unseen births and flag writes;
- body motion/transform recurrence;
- joint uncertainty with asynchronous input/cadence;
- collision-volume lowering; and
- delivery before issue.

Its physical error direction is unknown. Offline exact fixtures can validate
composition and version identity only.

Concrete falsifiers:

1. changing one body/flag/geometry word leaves the schedule digest unchanged;
2. two hidden schedule branches reach separate controller maximizations
   before their observations differ;
3. priority 11 consumes an action-conditioned `0x800` already baked into the
   schedule;
4. a schedule shorter than cadence is silently padded;
5. a missing or unknown schedule becomes an empty body frame;
6. projected contact/damage body sets disagree with an independent scalar
   flag oracle; or
7. physical runtime produces a body identity, non-mode flag, or geometry
   outside a future schedule that claimed complete predictive authority.

## 6. Formal Review Questions

1. **Control equivalence:** hidden schedule branches merge only when complete
   native observation, actuator/mode state, and immutable schedule-set version
   agree. Branch identity remains hidden.
2. **Quantifiers:** the controller selects one action before nature chooses
   input timing, cadence, and schedule branch. No hidden branch receives a
   separate controller choice.
3. **Physical question:** an exact solution over version 1 answers only a
   supplied finite fixture/retrospective schedule. It does not answer the
   physical predictive game.
4. **Algorithm:** canonical serialization and exhaustive branch composition
   are exact for supplied data. An independent scalar body-set oracle and
   digest-mutation tests are required.
5. **Delivery:** version 1 is offline. A later physical producer must publish
   one exact immutable set before issue or return `UNKNOWN`.

## 7. Exit Gates

1. Implement the offline immutable schedule/body/geometry representation.
2. Carry schedule-set identity through asynchronous SEM-MODE branches and
   non-clairvoyant observation merging.
3. Publish deterministic body-set/digest differentials for adversarial
   fixture branches and the retained `10065 -> 10075` semantic capsule.
4. Define a predictive producer whose omitted event classes are either
   exhausted or conservatively enveloped.
5. Revalidate that producer on Lunatic Stage 3, 4A, 5, and Final B physical
   workloads, retaining native replay when naturally available.
6. Only then compose movement/collision, viable-state, and safe-action-mask
   differentials and consider a newly versioned physical survival falsifier.

Gates 1–3 are finite implementation work. Gates 4–6 remain the physical
promotion boundary.

## 8. Retained Offline Checkpoint

Gates 1–3 are implemented without changing live input:

- `scripts/th08_future_body_schedule.py` validates sorted unique body
  identities, mode-independent flags, canonical binary32 geometry,
  equal-horizon nature branches, exact clock/provenance identity, and one
  content SHA-256 over the complete schedule set.
- every asynchronous SEM-MODE branch carries the schedule-set digest and
  hidden branch digest. The next observation key always contains the exact
  projected body flags and binary32 geometry visible at that decision; a
  caller cannot accidentally merge different observed geometry by omitting
  it from an auxiliary observation.
- hidden schedules that differ only before converging to the same next
  observation merge into one controller information set. The controller
  never maximizes separately on the hidden branch digest.
- short cadence coverage, baked-in action-conditioned bit `0x800`,
  noncanonical geometry, duplicate identity, and cross-version merging fail
  closed offline.

The deterministic report
`artifacts/runtime_reports/th08_future_body_schedule_differential_20260730.json`
has SHA-256
`66f0105028451f84b01cdef7c7fe198d9a50d6114ca72df693aa0242da062ee8`.
Linux and Windows generate byte-identical output. Three cases contain eight
exact branches and 27 per-update comparisons with zero mismatch against a
separate scalar mode/body-set oracle:

1. the retained CE-0176 semantic capsule opens contact and player-shot
   damage for all 16 final bodies with flags `0x0100114D`;
2. asynchronous Focus acquisition covers five input/mode histories; and
3. two hidden geometry histories converge before the next observation and
   merge into one information set.

The CE-0176 geometry is explicitly synthetic. Its native trace contributes
only retained flags, count, and endpoint semantics. This checkpoint proves
finite representation, version identity, exact composition, and
implementation/oracle agreement for supplied schedules. It does not produce
future physical schedules, does not change root+1 `UNKNOWN`, and grants no
collision, viability, damage, live action, or NMNB authority.

Ten focused schedule/report tests pass on Linux and Windows. Complete
discovery passes 1,257/1,257 in 14.286/31.013 seconds; Windows retains the
three existing skips.

The next implementation problem is gate 4: enumerate or conservatively
envelope unseen enemy births, future non-mode flag writes, despawns,
transforms, per-update geometry, and their joint scheduler/cadence support.
No new physical run is justified until one immutable predictive producer
version is ready to falsify.
