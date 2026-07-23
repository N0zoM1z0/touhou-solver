# Phase-Exact Hazard Oracle And Adaptive Viability

Date: 2026-07-24

This note defines the next no-Bomb planning checkpoint. It separates observed
facts from architectural inferences and does not treat an external replay or a
single spell-specific path as an implementation dependency.

## Hard No-Bomb Feasibility

**Externally observed, retrieved 2026-07-24:**

- The Maribel Hearn LNN database lists 17 players for TH08 Final B Scarlet
  Team LNNFS (No Miss, No Bomb, Full Spell):
  <https://maribelhearn.com/lnn?hl=en-gb>.
- BlackSoup records a TH08 Lunatic Scarlet Team no-Bomb clear with three
  lives remaining:
  <https://blacksoup.xxxxxxxx.jp/log1207_1209.html>.
- A Japanese all-shot-type LNB write-up explicitly includes Scarlet Team:
  <https://note.com/tanihime_mayuri/n/n827a14c2c046>.
- An Extra write-up explicitly records Scarlet Team No Miss, No Bomb, Full
  Spell:
  <https://note.com/norbis/n/n10ea3323466f>.

These are existence witnesses, not proof that this controller's current delay
model or every game build admits the same robust policy. They are strong enough
to retain no-Bomb as a hard acceptance constraint for Lunatic Final B and
Extra. A computed empty set is therefore a model, discretization, or
reachability failure until phase-exact refinement demonstrates otherwise.

## Current Failure Evidence

**Observed** in the clean focused Final B trace
`20260723_234414`:

- 37 native hit edges and zero Bomb input.
- 911 native policies with 208/369/609 ms median/p95/max solve time.
- 16,813 queryable policy decisions, but 8,292 empty action sets.
- Median forecast lead was 48 frames. The policy horizon was 80 frames on a
  16-pixel grid with eight physical frames per layer.

Per-phase empty-set evidence:

| Phase | Max lasers | Queries | Empty | Empty rate |
| --- | ---: | ---: | ---: | ---: |
| nonspell | 52 | 8049 | 3298 | 40.97% |
| 150 | 0 | 840 | 68 | 8.10% |
| 154 | 250 | 731 | 504 | 68.95% |
| 158 | 66 | 701 | 590 | 84.17% |
| 162 | 32 | 1351 | 783 | 57.96% |
| 166 | 104 | 1131 | 1043 | 92.22% |
| 170 | 0 | 2124 | 873 | 41.10% |
| 174 | 0 | 343 | 197 | 57.43% |
| 178 | 0 | 231 | 137 | 59.31% |
| 182 | 0 | 438 | 348 | 79.45% |
| 186 | 0 | 335 | 169 | 50.45% |
| 190 | 0 | 539 | 282 | 52.32% |

Laser-heavy phases correlate with the most severe exhaustion, but the
zero-laser phases prove that laser geometry is not the only cause. Missing
future bullet emissions/transforms, a coarse lattice, and an unconstrained
finite-horizon terminal layer remain independent failure modes.

## Native Laser Geometry Correction

**Observed** in `bullet_manager_update` (`0x00431240`, laser loop
`0x00431B7A`) and `player_test_collision_and_graze` (`0x0044A6A0`):

- An allocated record at `+0x584` is not necessarily lethal. Collision depends
  on phase `+0x598`, timer `+0x588`, collision-enable/disable thresholds, and
  the phase branch.
- Active geometry starts with rectangle `size.x = head-tail`, or
  `0.7*(head-tail)` after `tail>0`.
- The caller initializes `size.y = target_width/2`. The player helper divides
  the incoming size vector by two before constructing min/max bounds.
  Therefore the active lethal transverse half-extent is
  `target_width/4`, before combining it with the player's SHT half extents.
- In the non-alpha warmup branch, `size.x` is overwritten with
  `ramped_current_width/2` before the collision-enable test.
- In the non-alpha fade branch, `size.x` is similarly overwritten with the
  fading width divided by two before the collision-disable test.
- Warmup-to-active and active-to-fade fall through in the same manager update,
  so the size vector left by the earlier branch matters at a boundary call.

REA independently exposes the same record offsets, phase branches, size-vector
division calls, and collision calls:

- binary overview:
  `ev_d0f27bd5ad4f901c2cc242681ed1658f5f790af3994d42dcd56c6eea69eee9e5`
- laser manager:
  `ev_3703fc10b6c9874992d83e523870471a871517461e81f21cd4c1bc9d8480f48a`
- rotated player collision:
  `ev_1d2d488e8cb1f98bcddeaf0d124c1445884ef4bcb3d163bf19546cc069493a63`

**Observed implementation gap:**

`th08_live_dodge_agent.decode_lasers` retains only allocation, origin, angle,
tail, head, and `target_width/2`. Both the local controller and corridor
lowering then model every retained record as a static finite capsule.
`lower_lasers` adds

```text
min(12, 0.4*snapshot_lag) + 0.4*forecast + 0.4*future_frame
```

to every segment. At median lead 48 and horizon 80, this contributes 51.2
pixels at the horizon, before the already doubled transverse half-width.
Dozens or hundreds of such static bands can erase the whole playfield even
when many records are warnings, not yet collision-enabled, fading, or rotating
under ECL handle updates.

This does not invalidate all nine same-frame laser-contact witnesses in the
run. It means:

1. same-frame contact classification uses an approximate capsule and must be
   revalidated with the complete native record; and
2. future occupancy is substantially less trustworthy than the same-frame
   witness because it ignores phase, gates, kinematics, and ECL mutations.

## Why A Longer Uniform Horizon Is Not The Fix

**Inferred from the observed model and trace:** increasing the current 80-frame
horizon alone would propagate stale geometry and arbitrary uncertainty farther,
create more false empty sets, and increase solve cost. Long-term control needs
both a better environment model and a terminal invariant, not merely more
uniform layers.

The robust viability recurrence remains:

```text
V_t = Safe_t intersect {
    state s:
    exists action a,
    for every supported input delay d,
    successor(s, a, d) is in V_(t+d)
}
```

The missing condition is that the last layer is not "safe for one instant".
Its terminal set must be a basin that overlaps the next policy's kernel. A
rolling policy is accepted only when every delay branch reaches that overlap.
This stitches finite policies into a controlled-invariant funnel.

## Phase-Exact Hazard Oracle

The game-neutral planner should consume a time-indexed occupancy oracle:

```text
HazardTimeline.snapshot(frame, player_state, branch_state)
HazardTimeline.events(start_frame, end_frame)
HazardTimeline.lethal_geometry(frame)
HazardTimeline.uncertainty(frame)
```

The TH08 adapter should own ECL, pool layouts, RNG, transforms, callbacks,
damage, and shot-type semantics. The oracle is built in three layers.

### 1. Offline compilation

Compile data that does not depend on the live attempt:

- decoded ECL/STD resources and route selection;
- timeline spawn records and statically folded difficulty/route branches;
- enemy subroutine bytecode, call/interrupt/phase graphs, and literal laser or
  bullet descriptors;
- bullet transform programs and native ECL callback semantics;
- laser lifecycle state machines and collision geometry;
- spell IDs, phase transitions, nominal timeouts, and static item emissions.

The existing decoded corpus, flow analyzer, callback models, transform IR, and
route manifests already cover much of this layer.

### 2. Phase instantiation

At stage or spell entry, initialize an executable enemy ECL VM from the native
snapshot:

- active enemies and every VM/auxiliary VM frame;
- gameplay RNG state/call count;
- laser records including phase, timer, flags, current/target width, speed,
  and collision thresholds;
- bullet transform queue state;
- boss HP, damage rate, shot state, and phase timers.

Execute native frame order to emit future bullet, laser, enemy-body, and item
events. A single prerecorded movie is insufficient: player-relative aim,
damage-dependent phase duration, RNG consumption, and some callbacks depend on
the candidate control trajectory. Those values must remain parameters or
bounded branches.

### 3. Online correction

Use native state as a rolling correction, not as the only forecast source:

- align oracle frame, RNG, enemy VM, and pool state to each coherent snapshot;
- compare predicted and observed spawns/mutations;
- repair the earliest divergent component;
- learn bounded residual error per event/field.

Input delay uncertainty and environment-model uncertainty remain separate.
The former branches control successors; the latter expands only fields with
measured prediction residuals. It must not be a universal linear
`0.4 px/frame` band.

## Adaptive Multi-Resolution Viability

Use spatial and temporal resolution where topology demands it:

1. A coarse global lattice identifies connected safe components, bottlenecks,
   and macro routes across a phase.
2. Refine reachable tubes, component gates, and alleged empty regions from
   16 pixels to 4 and then 2 pixels.
3. Insert time layers at hazard events such as spawn, collision-enable,
   transform, reflection, laser angle/origin mutation, phase transition, and
   fade-disable. Do not force every interval into the same eight-frame layer.
4. Declare a kernel genuinely empty only after exact geometry and local
   refinement agree.
5. Score clearance, item/power collection, damage, and graze only inside the
   surviving robust action set.

For long phases, the global layer should search a graph of safe connected
components and time-dependent gates. The dense viability kernel is needed only
around the selected component path. This gives longer reach without making
the entire playfield a fine grid for thousands of frames.

The phase planner must retain multiple homotopy classes when uncertainty has
not resolved which side of a wall or laser fan will remain open. Committing to
one lane is allowed only when all alternatives have a lower robust survival
margin or can no longer be reached.

## General Interfaces

Reusable code belongs in `scripts/touhou_control/`:

- `HazardTimeline`: time-indexed exact/uncertain lethal geometry and events;
- `AdaptiveOccupancy`: coarse cells plus local refinements;
- `InvariantFunnel`: terminal kernels and overlap certificates;
- `PolicyChain`: epoch delivery and robust delay-branch stitching;
- `ModelResiduals`: field-specific prediction error calibration.

TH08-specific lowering should implement:

- `Th08EclExecutor`;
- `Th08LaserOracle`;
- `Th08BulletTransformOracle`;
- `Th08EnemyDamageAndPhaseOracle`;
- `Th08NativeSnapshotSynchronizer`.

A later Touhou game then replaces its bytecode, record layouts, callbacks, and
movement constants while retaining the occupancy, refinement, viability, and
policy-chain algorithms.

## Implementation Order And Gates

1. **Code-complete, physical differential pending.** Live laser snapshots now
   retain all collision-relevant lifecycle fields and flags.
   `th08_laser_model.py` covers active, warmup, fade, and boundary-call size
   vectors. Retained native differential fixtures are still required.
2. **Code-complete for instantiated records.** Static lowering is replaced by
   game-neutral `SegmentTrajectoryHazard` samples generated from the native
   lifecycle. Future ECL-driven origin/angle mutation remains an oracle input,
   so a small bounded field uncertainty remains until step 3 supplies it.
3. Implement the enemy ECL VM executor that turns the existing static route
   graph into actual frame-ordered spawn/mutation events. Connect its output to
   the existing bullet, laser, item, and player executor.
4. Add adaptive 16/4/2-pixel refinement and refuse to report a true empty set
   from the coarse lattice alone.
5. Add terminal-kernel overlap and policy-chain certificates.
6. Run shadow prediction on retained traces, then focused thprac trials for
   spells 154, 158, 162, 166, and 170. Retain exact false-positive,
   false-negative, and first-divergence artifacts.
7. Require repeated clean focused passes before Final B, then full Lunatic,
   then Extra physical acceptance.

The next code checkpoint is step 3 plus the adaptive refinement in step 4.
The implementation remains phase-generic; there is no spell-specific
coordinate or timing exception.

## Recovery Outside The Strict Kernel

Physical traces can start a policy epoch outside the strict robust kernel even
when a nearby successor state remains recoverable. An empty safe-action mask
must retain its safety meaning: no action may be relabeled safe. It should not,
however, erase all global directional information.

For every action at an empty query, the policy now evaluates the minimum over
delay branches of the viable action-volume in the successor neighborhood. The
local controller applies this as a soft lexicographic term after exact
collision and clearance:

1. minimize exact local collisions;
2. minimize negative local clearance;
3. maximize worst-branch kernel-repair volume;
4. apply waypoint, item, and movement smoothness costs.

Thus an unavoidable or already nonviable state is steered toward kernel
re-entry without weakening `exists action, forall delay` safety. This is
game-neutral and applies to any discrete action lattice.

## Sparse Native Body Synchronization

TH08's enemy pool is fixed-stride but its collision fields occupy only a
1,500-byte window near the end of each 21,456-byte slot. Reading all 480 slots
contiguously transfers 9.8 MiB even when only a boss and a few helpers are
contact-enabled.

The synchronizer now performs a two-level observation:

1. probe the native active/contact/blocking flags for every slot;
2. fetch and decode the collision window only for slots that pass the exact
   native gate.

A fixed-frame, eight-body differential retained equal pointer sets for 30
pairs while reducing median capture from 14.06 to 3.34 ms. This permits a
four-frame observation interval at approximately the prior 16-frame
contiguous reader's bandwidth duty cycle.

This is still observation, not prediction. A helper whose contact bit becomes
enabled after the last scan remains absent from the oracle until the next
snapshot. ECL event execution is required to turn that boundary into a
future hazard before activation.

The Stage-4A physical differential `20260724_040019` accepted the observation
half of this design: snapshot age improved from 11/20 to 5/8 frames
median/p95 without worsening 3/4-frame control cadence. It also supplied the
prediction counterexample. Three of four stable enemy-body overlaps involved
pointers absent from the action snapshot, including two hits with positive
modeled pipeline clearance. The fourth pointer was visible inside an already
nonviable crowd. Accordingly, sensor freshness and future ECL execution are
separate gates; neither may be reported as a substitute for the other.

## Observation-To-Policy Blind Interval

An asynchronous policy built from snapshot `s` for future epoch `e` cannot
contain a hazard created in `(s, e]`. ECL execution is the complete solution,
but the runtime must also avoid making this blind interval larger than its
measured compute latency.

Stage-2 frame 1,582 is the retained witness. Bullet slot 637 was absent at
snapshot 1,498, present at 1,545, and collided before the next policy epoch
1,594. The worker's rolling p90 solve duration was about 25 frames, while the
lead estimator was clamped to 48. A general asynchronous scheduler should
therefore:

1. start conservatively before timing samples exist;
2. estimate a high solve-time quantile in game frames;
3. permit only an explicit bounded late-arrival overlap;
4. retain enough policy horizon after arrival for a useful query;
5. expose ECL events during the remaining irreducible interval.

Reducing the scheduling interval is not evidence that ECL prediction is
complete. It is a separate latency correction that increases the fraction of
new native hazards included in the next rolling snapshot.

Stage-2 differential `20260724_043310` physically accepted this scheduling
change: observed lead was 16/18 frames median/p95, policy age halved, and
nonspell hits fell from eight to four without cadence regression. The one new
spell-20 hit also exposed the remaining fusion rule: an older global safe
action mask may contain only boundary-clamped aliases while a live hazard
outside the short local horizon approaches. Global certificates, local exact
geometry, and future ECL events must carry explicit provenance and freshness;
an older global repair volume cannot outrank a newer locally predicted
collision.

An always-on 32-frame terminal warning was tested and rejected in Stage 4A:
it increased cadence p95 from four to five frames and did not reduce total
hits. The warning is now activated only for the observed fusion failure:
within four pixels of a boundary, an older global safe mask maps to at most
three distinct clamped physical successors. This keeps the exact current
geometry authoritative at control-collapse boundaries without turning a
single-action rollout into a global policy or paying its cost everywhere.
