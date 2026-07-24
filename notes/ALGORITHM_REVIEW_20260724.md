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

1. Physically cross-check CE-0089 on a randomized non-Stage-6B stage with the
   safety-value experiment disabled. Acceptance requires hard-certificate
   telemetry, cadence, and per-phase evidence, not a lower aggregate hit count.
2. Build a same-input offline differential over retained Stage-1, Stage-3,
   Stage-4A, Stage-5, and Stage-6B rows. Compare hard-vector counts before any
   soft recovery metric.
3. Calibrate motion uncertainty from stable same-slot one-step residuals,
   excluding phase boundaries, epoch discontinuities, callback events, and
   unmatched slots. Do not tune uncertainty from mixed raw residuals.
4. Prototype the robust recovery-band recurrence against a small independent
   scalar oracle and adversarial generated cases. Retain failing seeds and
   shrink them.
5. Re-profile live decode, local projection, policy lowering, and native solve
   p95. Move another boundary to C++ only if it remains a measured end-to-end
   limiter.
