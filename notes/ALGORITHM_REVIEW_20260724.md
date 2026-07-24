# Robust Solver Algorithm Review After Stage 6B

Status: design review and experiment ordering. This note separates observed
runtime evidence from inferred algorithm defects and proposed work. It does
not claim a physical survival improvement.

## Observed State Of The System

Complete hard-no-Bomb Stage-6B run `20260724_135201` reached
`route_complete` with 27 native hits. The retained complete Stage-6B counts
are 42, 30, 18, and 27; different native RNG states prevent a causal
hit-count comparison. The current run is therefore a cross-stage regression
workload, not an acceptance baseline.

The run separates three bottlenecks:

1. The global policy was usually present and covered the live delay support,
   but 5,518 of 12,374 queries (44.6 percent) had an empty robust action set.
   Twenty-four of 27 hit windows followed global-kernel exhaustion.
2. Boundary loss is strongly associated with the failures: 17 of 27 hits
   have the playfield-boundary factor, bottom-eight-pixel occupancy was 0.307
   in pre-hit windows versus 0.132 elsewhere, and mean selected control-reserve
   deficit was 10.043 versus 1.422.
3. Runtime is still material. Local planning was 24.48/46.69 ms median/p95,
   global solves were 266.80/431.74 ms, and pool decoding was slower than the
   earlier Stage-6B comparison because diagnostic transform objects were
   constructed on every live decision.

These observations do not tell us whether every empty global kernel is a
true loss of controllability. Quantization, uncertainty inflation, incomplete
future motion, and entering the horizon too late can all collapse the finite
kernel. They must be measured separately.

## Mathematical Model

The control problem is a finite robust game, not a weighted shortest path.
At a physical state `s`, with active actuator command `u_old`, the controller
chooses one command before learning the realized delay:

```text
exists u_new, for every delay d in D:
    every committed-prefix and action-hold state is collision-free
    and the terminal state remains in the backward viability set
```

The useful objective is lexicographic:

```text
H = (
    modeled collision count,
    robust-prefix collision count,
    negative robust-prefix clearance,
    hard reachability/gate violation
)

S = (
    safety margin deficit,
    boundary control-reserve deficit,
    distance to a viable recovery set,
    risk, smoothness, item and position utility
)
```

`H` must dominate `S`. A scalar weighted sum cannot guarantee this for all
hazard scales. More subtly, every approximate operator must preserve the same
dominance—not only final action selection. Beam deduplication or truncation
that applies `S` before an available component of `H` can permanently erase
the safe first action.

Stage-6B paired replay exposed exactly that error. Boundary reserve was used
during beam pruning, while uncertain-delay certificates were computed only
after the beam. Enabling the soft reserve changed the 300-row replay from
24 to 26 robust-collision selections and from 39 to 42 negative-certificate
selections. Computing the certificate before pruning and ranking its hard
violations before all soft terms makes both variants select 22 robust
collisions and 36 negative certificates. In the 213 pre-hit rows, both
variants select 56/72. This is a correctness repair; equal offline certificate
counts are not physical survival evidence.

## Current Decomposition

The architecture remains appropriate:

- The TH08 adapter owns addresses, pool layouts, callback tags, laser
  lifecycle state, and gameplay epochs.
- The game-neutral global layer builds a delay-robust finite-lattice
  viability policy asynchronously.
- The local layer performs exact continuous-geometry MPC and certifies the
  emitted first action over the current delay support.
- Soft recovery is used only after the global Boolean kernel is empty.

The main algorithmic limitation is the recovery bridge. Current
`recovery_distance` measures a branch endpoint's distance to a viable
next-layer state. It does not prove a collision-free path from the current
state to that target.

A stronger fallback is a time-expanded robust recovery value:

```text
J[k, active, state] =
    min over issued action
    max over delay branch
      lexicographic_sum(
          intermediate collision/clearance violations,
          boundary controllability loss,
          J[k + 1, issued, successor]
      )
```

The terminal set has zero cost inside the Boolean viability kernel and a
positive recovery cost outside it. This is a min-max shortest-path problem on
the same transition graph. It can be solved backward with small integer
collision layers and a continuous bottleneck/distance label. Until the entire
bridge is represented, the value is guidance rather than a certificate.

## Beam Search Requirements

The immediate repair precomputes the already-existing first-action robust
certificate and reuses it after the beam. This is intentionally smaller than
introducing a new heuristic.

A future beam change should be tested as a multi-label approximation:

- discard a node only when another node dominates its hard vector and is no
  worse in the relevant soft prefix;
- retain first-action identity in the label until the action decision is
  finalized;
- measure whether a small per-first-action reserve improves hard-vector
  coverage before granting it beam capacity;
- never force dominated labels into a fixed-width beam merely to obtain
  action diversity.

A naive stratified-beam experiment failed existing terminal-threat
counterexamples and was removed. Action diversity is not itself a proof.

## Performance Boundary And C++

The right native boundary is a compact numerical batch, not "all Python is
slow." C++ is justified when it removes high-volume object materialization or
per-cell/per-hazard loops and passes all of these gates:

1. independent scalar-oracle parity, including adversarial stop/resume/
   redirect/reversal workloads;
2. exact action or full-decision parity, unless a numeric tolerance and its
   behavioral consequences are explicitly accepted;
3. at least a material whole-decision or background-service p95 gain, not
   only a micro-kernel speedup;
4. Linux and Windows builds and regressions;
5. no new GIL-holding conversion stage that moves the bottleneck back into
   Python.

The sparse piecewise global projector met those gates and remains native.
The fused laser lifecycle path removed the Python object pipeline before a
small C++ local-laser kernel was considered; the residual native experiment
changed one of 100 decisions for a small gain and was removed.

The same rule applies to bullets. A C++ decoder that returns one Python
`Bullet` object per native slot still pays the object boundary. The current
correction keeps full queue/stop runtime only for explicit diagnostics and
uses consolidated scalar or structure-of-arrays reads for gameplay fields.
The retained synthetic benchmark reports 1.25x to 2.24x median decode speedup
at 200--1,200 active records with exact gameplay-field parity. If bullet
projection remains hot after a physical run, the next useful native boundary
is decode-plus-projection into packed frame arrays, not a C++ reimplementation
that immediately reconstructs the same Python objects.

## Ordered Experiments

1. Physically validate CE-0090 on Stage 5. The trace must expose synchronous
   owner geometry and whether the contact mode was observed or anticipated.
   The repeated zero-projectile upper-center collision is the primary gate.
2. Cross-check the latent-owner union on a randomized non-Stage-5 stage for
   timing and false empty-kernel regressions. Do not judge it only on Reisen.
3. Build a same-input offline differential over retained Stage-1, Stage-3,
   Stage-4A, Stage-5, and Stage-6B rows. Compare hard-vector counts before any
   soft recovery metric.
4. Calibrate motion uncertainty from stable same-slot one-step residuals,
   excluding phase boundaries, epoch discontinuities, callback events, and
   unmatched slots. Do not tune uncertainty from mixed raw residuals.
5. Prototype the robust recovery-band recurrence against a small independent
   scalar oracle and adversarial generated cases. Retain failing seeds and
   shrink them.
6. Re-profile live decode, local projection, policy lowering, and native solve
   p95. Move another boundary to C++ only if it remains a measured end-to-end
   limiter.

## Stage-5 Cross-Check, Observation Completeness, And Hidden Contact Mode

Stage-5 run `20260724_144805` physically closes the sparse piecewise
performance gate, not the survival gate. Spell-107/111 local-plan p95 and
decision-cadence tails fell sharply, and lightweight planning traces prove
that stop/resume events remained attached without diagnostic queue objects.
Fifteen of 16 hits still followed global-kernel exhaustion.

The follow-up isolated a more basic error before the robust-game dimension:
the active owner pointer `0x0057D2F0` is exactly one `0x53D0` enemy stride
before the ordinary asynchronous pool at `0x005826C0`. The sensor's
observation set excluded the boss entirely. A planner cannot compensate for a
hazard missing from every state estimate, regardless of search quality or
native throughput.

After repairing observation completeness, CE-0090 still adds a second
robust-game dimension. The spell owner has a discrete contact mode that can
change between observation and actuator pickup. When that transition is not
yet observable, the survival set is the intersection of viable sets for both
modes:

```text
K_robust = K(contact disabled) intersect K(contact enabled)
```

For geometry this is equivalent to lowering the owner body while its mode is
latent. TH08 owns the owner pointer and layout; the local/global planners
remain game-neutral.

The same failure exposed soft-objective scale. Raw item values previously
entered the node cost with an effective multiplier of six and unbounded
aggregate approach potential. Item influence is now saturating and bounded,
and approach shaping is an order of magnitude smaller. Context transitions
also separate physical actuator state from preference memory: the old command
still defines the uncontrollable delay prefix, but its reversal penalty does
not survive into a new spell context. This is a hybrid-system reset rule, not
a spell-115 route.

Physical Stage-5 run `20260724_152719` retained 2,658 error-free synchronous
owner samples: 2,640 contact-enabled and 18 anticipatory. All pointers were
outside the ordinary pool. The old zero-projectile upper-center spell-115
cluster disappeared once, while total hits increased `16 -> 21` under a
different RNG/respawn history. This accepts observation completeness for the
targeted failure only. Remaining failures still concentrate on global-kernel
exhaustion and motivate the generated recovery-band/oracle work rather than
more spell-specific weights.

## Stage-4A Cross-Control: Local Stability And Observation Timing

The complete randomized Stage-4A run
`lunatic_route2_stage4a_unattended_20260724_155932` retained 8,293 decisions,
19 hits, and zero Bomb input. The preceding complete Stage-4A run also had 19
hits, but per-phase counts moved in both directions. This is a cross-stage
workload, not an aggregate causal comparison.

The input path itself is not the dominant local defect. Of 4,843 unambiguous
issued-mask transitions, 4,052 were visible on the next decision; for visible
transitions the native snapshot delta was median/p95 `1/1` frame and maximum
4. The controller observation cadence was instead median/p95 `4/6` frames,
with local planning `29.09/48.38 ms`. Replacing `SendInput` with C++ would not
remove that closed-loop sampling interval.

CE-0092 distinguishes sensor age from computation-window freshness. The
causal frame-35,415 decision read projectile time 35,412 and only a frame-
35,410 boss body, but its action was not issued until frame 35,415. The next
async result was stamped 35,413 and contained an 18-body ring whose slot 18
made exact contact at frame 35,420. A synchronous read only at the beginning
of the old decision would still precede the spawn. The correction therefore
uses two adapter-level observations:

```text
source state -> synchronous 64-slot prefix -> local plan
             -> synchronous prefix version check -> robust recertificate
             -> issue-time deadline check -> input
```

The first read merges fresh allocation-head bodies with the complete async
tail. The second compares pointer set, contact mode, size, velocity, and
linear-motion residual. Only a change pays the all-action recertificate cost.
This closes one observed class of during-plan spawn/teleport/contact changes;
it does not predict a hazard that spawns after the second check.

Item objectives are disabled during the survival acceptance phase. Items can
still be collected passively, but they do not enter pruning, final ranking, or
predicted collections. On a deterministic 180-bullet/24-item local workload,
median/p95 changed from `11.68/19.44 ms` to `8.10/12.54 ms`. This deliberately
invalidates the old expectation that a safe power item must remain an eventual
rollout objective. Resource-aware pickup may return only inside a separately
certified survival-equivalent action class.

## Stage-4A Global/Local Consistency Audit

The dossier compares only alive, action-eligible rows with an available global
query and a local uncertain-delay certificate. The first report incorrectly
treated their Boolean values as the same proposition. Global viability covers
the remaining 48--80-frame policy horizon; the local certificate covers only
the selected action's 8--12-frame delay-plus-hold prefix.

Of 6,613 comparable decisions:

- 4,048 had a winning global state and safe selected prefix;
- 32 had a winning global state but unsafe selected prefix;
- 2,395 had a losing global state but safe short prefix;
- 138 were losing globally and unsafe locally;
- 99 selected actions lay outside the global winning set under an explicitly
  recorded local degeneracy relaxation;
- 30 selected actions belonged to the cached global winning set but were
  contradicted by the fresh local prefix checker.

The 2,395 rows are not false-empty evidence: surviving 8--12 frames does not
prove that a policy exists for another 48--80. The 30 action-aligned rows are
direct contract contradictions. Their underlying hazard snapshots were
19--48 frames old, and several local clearances were `-10..-22`, so missing
births/later geometry are more plausible than a small nearest-cell margin;
per-row source-snapshot differentials are still required for causal
allocation.

The Boolean recurrence itself remains correct for its discrete model:
`exists issued action / forall delay`, every physical frame is checked, and
transition sampling error is subtracted. Two theory/practice gaps remain:

1. A live continuous position is mapped to its nearest lattice cell, but the
   query does not have a clearance value with which to subtract the initial
   off-grid error. The local certificate must remain authoritative.
2. Outside the Boolean kernel, `recovery_distance` measures only the
   next-layer endpoint's distance to a viable cell. It does not certify the
   bridge. On the same exact graph, a safe robust bridge into the future
   kernel would already make its predecessor viable.

The implemented hard fusion now intersects cached winning actions with the
fresh local prefix-safe set. If the intersection is empty, every action is
recertified and the cached mask is relaxed. On the 30 retained contradictions,
paired trace-radius replay improved the hard vector on 10 rows, regressed on
zero, and changed robust-collision decisions `29 -> 23`; this is not physical
evidence.

The next exact fallback is not a risk weight or endpoint recovery distance.
It lexicographically maximizes guaranteed collision-free frames and then
bottleneck clearance. The independent scalar recurrence matched Boolean
winning sets/action masks on generated games. Across 4,905 losing states,
margin-only action selection forfeited guaranteed survival frames on 190
states. Full rationale and implementation order are in
`notes/VERSIONED_REACH_AVOID_ARCHITECTURE.md`.

## Native Clearance Traversal Checkpoint

The ordinary moving-AABB clearance phase was already C++, but its loop order
still evaluated every hazard at every lattice cell:

```text
frame x row x column x hazard
```

With 81 frames, 648 cells, and 1,360 hazards this is roughly 71 million AABB
tests even though the clearance cap is 48 pixels. The retained native kernel
now traverses hazard-first and updates only the analytically bounded cells
where that hazard can lower the cap. It keeps separate negative overlap and
positive squared-distance buffers, so the final reduction has the same
semantics as the dense oracle. A one-cell numeric guard protects the bound.

On fixed seed `20260724`, 1,360 moving AABBs, the TH08 24x27 grid, 81 frames,
and 48-pixel cap:

- dense native median/p95: `342.67/372.69 ms`;
- bounded native median/p95: `59.68/97.40 ms`;
- speedup by median: `5.74x`;
- the float64 checksum of the float32 output remained exactly
  `-133779.12470752`, with identical min/max
  `-15.9373226/19.7757092`.

The existing mixed-hazard differential plus a new randomized 200-AABB
off-playfield/boundary oracle pass. Both Linux and Windows x86-64 libraries
build. This is a meaningful C++ optimization of an existing compact numerical
boundary; it does not justify translating orchestration, tracing, or TH08
memory adapters into C++.
