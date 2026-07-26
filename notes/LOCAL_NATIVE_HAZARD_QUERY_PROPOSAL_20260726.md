# Local Native Hazard Query Proposal

Date: 2026-07-26

Status: accepted live implementation optimization with the NumPy reference
as explicit rollback. It inherits, but does not enlarge, the existing local
certificate and beam authority.

## Measured Motivation

The direct Windows explicit-root replay and the Stage-4A physical telemetry
separate the local critical path:

- correct explicit-root certificate geometry is about 5.2 ms median and
  9.0--9.9 ms p95 on the retained Stage-4A/Stage-6B samples;
- full local beam expansion is about 11.7--12.3 ms median and 16.1--16.8 ms
  p95;
- the physical Stage-4A `observe -> SendInput` boundary is 37.4/56.1 ms
  median/p95 before the first hit and 38.8/57.8 ms over the complete run;
- one of 10,080 decisions missed its declared issue deadline.

The first exact Python key-cache proposal was rejected: Stage 6B beam p95
regressed by 20.8%. The next performance experiment therefore moves only the
repeated pointwise hazard query to the existing optional C ABI library. That
query is shared by the exact short certificate and by every beam layer.

## Physical Problem Contract

- **Objective:** reduce synchronous local planning time without changing any
  bullet, laser, enemy-body, collision, robust-clearance, risk, action, or
  issue semantics.
- **State/observations:** one vector of candidate player positions, one
  already-projected bullet frame, one packed laser frame, native enemy-body
  kinematics, the local rollout step, and the existing player radius.
- **Action semantics:** none. This kernel evaluates positions; it neither
  chooses nor writes an action.
- **Uncertainty/transition:** transformed-bullet uncertainty, laser base and
  per-frame uncertainty, and enemy-body uncertainty are passed unchanged.
  Projection and the controller/delay recurrence remain in independent
  Python.
- **Horizon/resources:** one call covers one existing local rollout step.
  Call count and horizons remain unchanged.
- **Safety invariants:** exact collision counts and the sign of minimum robust
  clearance must match the Python oracle. Risk must match within a declared
  floating-point tolerance. Missing native code, invalid input, or a native
  error falls back or fails closed in experiment code; it never silently
  changes live authority.
- **Deadline/fallback:** promotion required differential parity plus a
  measured Windows retained-root improvement and a focused physical gate.
  Those implementation gates passed. The existing Python query remains the
  explicit fallback.

## Five Model And Algorithm Questions

1. **Which histories merge?** None are newly merged. The native function sees
   the same per-step projected arrays as the Python query. History aliasing,
   active/held/pending state, and cadence/delay beliefs stay outside it.
2. **Are uncertainty branches and causality preserved?** The function has no
   controller/nature recurrence. It evaluates every supplied hazard against
   every supplied candidate position and uses the same per-step uncertainty
   formulas. The causal recurrence remains Python-owned.
3. **What decision does an exact solve answer?** Exact parity answers only the
   existing local pointwise hazard proxy. It does not prove the physical
   planner, the observation model, or unrestricted optimality.
4. **What does the algorithm solve and what falsifies it?** It is intended to
   be an implementation-equivalent scalar loop. Any collision mismatch,
   robust-clearance sign mismatch, non-finite disagreement, or risk error
   beyond tolerance on independent randomized/adversarial cases falsifies the
   implementation. Required cases include relevance-margin edges,
   transformed bullets, zero-length and moving lasers, dynamic uncertain
   AABBs, playfield-edge positions, and dense pools.
5. **Can it be consumed before issue time?** Retained Windows roots and the
   zero-deadline-miss Hard Stage-1 run establish the current implementation
   gate. Offline kernel speed alone is still not a Lunatic/Extra physical
   survival claim, and contention remains separately measured.

## Approximation And Authority Boundary

The C++ scalar evaluation may round in a different order from NumPy. That
error direction is unknown, so the native result has no hard authority until
hard-label parity is exhaustive over retained/adversarial corpora and
near-boundary cases are checked explicitly. Python/C++ agreement proves only
implementation parity. It does not validate the physical model.

The implementation gate required:

1. C ABI plus a game-neutral Python wrapper;
2. independent differential tests against `_hazards_for_positions`;
3. Linux and Windows timing by workload density;
4. a shadow full-planner benchmark.

The implementation subsequently passed those gates and is now the default
live query. See
`notes/LOCAL_NATIVE_GEOMETRY_AND_CONTENTION_20260726.md` for the hazard-major
loop, packed-laser cache, retained-root differential, planner-first worker
decision, and the reason dynamic BVH/grid work is deferred.

On 64 direct roots from each of Stage 4A `160712` and Stage 6B `165841`, the
native query produced zero action and hard-label mismatches against NumPy.
Stage-6B certificate geometry measured `1.337/2.304 ms` median/p95 native
versus `2.210/4.903 ms` NumPy; complete local planning measured
`12.540/17.223 ms` versus `14.441/23.110 ms`. The Python implementation
remains selectable with `--local-hazard-backend numpy`.
