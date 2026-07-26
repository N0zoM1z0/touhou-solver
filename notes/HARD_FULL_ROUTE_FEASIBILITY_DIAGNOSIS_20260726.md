# Hard Full-Route Feasibility Diagnosis

Date: 2026-07-26

## Scope And Result

This note diagnoses the complete original-game Hard Route-2 run
`hard_route2_fullrun_unattended_20260726_184942`. It separates local
implementation performance from global feasibility and losing-state
strategy. It does not promote a new live policy.

**Observed:** the native decode/local-geometry path remained serviceable over
70,699 decisions, up to 1,231 bullets and 256 lasers. Per-stage local-plan
median/p95 stayed within `11.81..14.55/20.86..26.90 ms`; pool-read
median/p95 stayed within `4.09..4.71/7.02..8.15 ms`. The run had no stall,
foreground loss, runtime error, JSON error, or Bomb input.

**Observed:** 38/39 contacts followed global viability-kernel exhaustion.
The fresh local path already classified 23 contacts as a committed-prefix
collision. Boundary and fast-mode factors occurred on 30 and 29 contacts,
whereas only four contacts occurred above 1,000 bullets. The dominant failure
is therefore earlier feasibility preservation and post-loss behavior, not
raw dense-pool decoding or point/segment throughput.

**Still open:** one sensor-gap contact, one enemy-body contact absent from the
action snapshot, and six cached-global actions contradicted by the fresh local
prefix remain correctness defects. “Local performance is sufficient to move
on” does not mean the sensing/model boundary is complete.

## Physical And Model Contract

- Physical objective: minimize native player-hit edges under hard no-Bomb
  control while completing the selected route.
- State/observations: native player, resources, active input, pool snapshots,
  projected hazards, manager/stage/spell context, and published global policy
  available before each issue.
- Actions: the existing 17 movement/focus masks; selecting the held complete
  mask is no-write under the augmented pipeline contract.
- Uncertainty: measured pickup support, controller cadence, interpolation
  error, projected hazard motion, and explicitly unresolved future births,
  transforms, semantic clock blocks, and pending-command history.
- Horizon/resources: live global `16 px / 8 f / 80 f`; local ten-frame search
  plus fresh uncertain-delay certificate; hard no-Bomb.
- Safety: no soft objective may cross a fresh collision/certificate/
  terminal-threat ordering boundary.
- Deadline: a result must match immutable root/version/context and arrive
  before issue; misses fall back to the fresh local certificate.

## Five Review Questions

1. **Which histories merge?** The live Boolean policy merges continuous
   positions into 16-pixel lattice cells and cadence into eight-frame layers.
   It does not yet carry the full active/held/pending actuator belief.
   Therefore merged histories are not proven control-equivalent physically.
2. **Are all uncertainty branches causal?** The declared Boolean recurrence
   universally branches over its delay support, but future births, exact
   pending-command belief, and the unresolved semantic manager clock are
   outside it. Empty/non-empty labels remain finite-model claims.
3. **Does an exact solve answer the physical question?** No. It answers
   robust viability for the declared frozen finite hazard model. It is a
   conservative/unknown-direction proxy for native survival depending on the
   omitted mechanism.
4. **What does the candidate solve?** `losing_control_reserve` does not solve
   or relabel the recurrence. Only after the global safe mask is empty, it
   ranks actions with equal fresh local hard vectors by delay-scaled ability
   to issue a later reversal. A hard-vector regression falsifies it.
5. **Can it be consumed on time?** The reserve uses already available repair/
   recovery labels. Paired replay changed median/p95 local cost only
   `10.06/13.43 -> 10.14/13.26 ms`. This is offline evidence; a focused
   issue-time measurement is still required before default authority.

## Losing-Control-Reserve Replay

The benchmark streams the 1.84-GB raw trace with a fixed bounded reservoir
instead of retaining every large JSON decision. It selected 400 of 2,353
eligible empty-kernel repair/recovery decisions within 240 frames before a
native hit.

| Metric | Disabled | Enabled |
| --- | ---: | ---: |
| Local median/p95 | 10.06 / 13.43 ms | 10.14 / 13.26 ms |
| Zero reserve deficit | 192 / 400 | 222 / 400 |
| Median reserve deficit | 0.975 px | 0 px |
| Robust-collision selections | 38 | 38 |
| Negative robust-clearance selections | 64 | 64 |

**Observed:** 28 actions changed; 27 reduced reserve deficit, one tied, and
none worsened it. All 400 paired hard vectors were equal. Changed rows were
28--236 frames before the next hit and appeared in every stage
(`1/1/6/11/3/6`).

**Inference:** this is a credible first losing-state candidate because it
directly addresses the boundary-heavy failure shape without weakening the
fresh hard ordering.

**Limitation:** it cannot restore a genuinely empty kernel, prove a
collision-free bridge, or establish a hit-count effect from replayed
single-step actions. It remains opt-in/proposal-only pending focused physical
tests.

Artifact:
`artifacts/benchmarks/hard_full_route_losing_control_reserve_20260726.json`.

## CPU And Next Gate

The host exposes 20 logical CPUs on an i9-13900H. The native live viability
kernel currently caps itself at four workers; the completed run nevertheless
published policies at age median/p95 `2/8` frames. Raising thread count is not
the first fix for an empty finite-model kernel, and per-layer thread creation
may add overhead.

Use the additional CPU first for audit-only exact work:

1. capture a focused Hard Stage-4A capsule cohort with the live policy
   unchanged;
2. recompute identical roots at 16/8/4-pixel grids, shorter horizons, current
   delay support, and uncertainty ablations;
3. classify coarse false-empty, horizon-only, uncertainty-only, forecast/birth
   mismatch, and unresolved roots;
4. run losing-control-reserve as a separate opt-in physical experiment, never
   combined with the capsule writer when judging survival;
5. only then consider query-local refinement, a route-conditioned safe tube,
   or a larger/persistent native worker pool.

Fine-grid or survival-label work must publish after the authoritative Boolean
mask or in an isolated worker. Previous synchronous refinement caused
delivery contention; more available CPU does not remove the version/deadline
contract.
