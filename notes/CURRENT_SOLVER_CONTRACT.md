# Current TH08 Solver Contract

Last updated: 2026-07-31.

This is the compact authority boundary for the active solver. Historical
derivations are recoverable from tag `pre-workspace-prune-20260731`.

## Physical Problem

Control Sakuya/Remilia through original TH08 Lunatic Route 2, then Extra,
without misses or Bombs. Survival is a hard constraint. Within the viable set,
prefer useful position, damage, Power collection, and shorter dangerous
nonspell exposure.

A state includes the native player state, complete active hazards, relevant
enemy/phase state, resources, active input, held desired input, pending issue
belief, timing/cadence support, and immutable model/content version.

An action is one complete no-Bomb mask. Choosing the held mask is no-write:
there is no new pickup-delay sample and any pending command remains pending.
The policy sees only observations available before issue. Hidden states with
the same next observation are merged before the next controller choice.

## Live Stack

The promoted live path is:

1. native process sensing and complete hazard projection;
2. packed native bullet decoding with Python rollback;
3. robust Boolean backward viability over declared timing/delay uncertainty;
4. baseline local beam reduction and pre-loss continuation preference;
5. a fresh issue-time local collision certificate;
6. version-checked publication and the fresh/global action transaction;
7. hard no-Bomb actuation.

The exact Final-B player-laser global-time-scale schedule is live only inside
its pinned Route-2 content identity. Unknown or mismatched schedule state
fails closed unless a diagnostic explicitly authorizes the root-only
unknown-direction continuation.

Removed supplemental, candidate-verifier, prewarm, G5, and priority-17 lanes
have no active code or strategy authority.

## Transition And Information Rules

- Cadence uncertainty is recursive; it is not one root branch or the maximum
  interval.
- Command pickup delay is an information set, not independent exact-delay
  roots available to the controller.
- Desired/last-issued input is not native active input.
- `enemy_manager_frame` is not a universal physical input clock. During
  dialogue/post-spell freezes, held input may continue moving the player.
- Signed clearance is the safety quantity. Lattice transitions subtract
  nearest-sample error.
- A recorded replay future is valid only for the action history that created
  it. Alternative actions require original-engine execution or a causal
  reconstructed transition.
- RNG state belongs to the root. After actions change native execution, future
  RNG may diverge and must not be forced equal.
- Timeout/exhaustion leaves an unresolved action set. It is never a losing
  certificate.

## Finite-Model Claims

An exact causal witness establishes feasibility only for its declared root,
action partition, uncertainty set, horizon, resource state, and model
version. Global optimality requires accounting for all root actions with the
controller-exists/nature-for-all quantifiers and observation merging intact.

Native/Python parity proves that two implementations agree. It does not prove
that the finite model contains every physical event. Unknown-direction
approximations never gain hard-safety authority.

Every published candidate is immutable over:

- canonical root and target frame;
- action set and actual issue/no-write semantics;
- float32 margin bits and clearance volume;
- cadence/delay support and continuation contract;
- content, model, and policy version.

Consumers do lookup-only exact-version matching. A miss uses the promoted
live Boolean policy plus a fresh local certificate.

## Combat And Resource Scope

Current offline WS-H reconstruction is fail-closed and Route-2/no-Bomb
specific:

- player-shot selection/emission, loaded SHT provenance, binary32 motion, and
  supported ordinary damage;
- enemy allocation/generation, HP mutation, defeat/forced-zero distinction,
  phase successor state, and active-clear events;
- item request/allocation/cull/pickup and exact Power/lives/Bombs deltas;
- mandatory timeline events and message-cleanup item homing.

It may compare only completed, generation-safe native transactions. Special
or unknown shot records, unsupported callbacks, dropped ring events,
unconsumed timeline engine events, Bomb state, non-Route-2 state, or resource
inconsistency return `UNKNOWN`.

Spell survival normally remains the primary objective. For ordinary stage
enemies, “kill before saturation” is a serious hypothesis: maximize damage
or shorten exposure only inside the survival-feasible action set. Focus is an
action factor, not a permanent mode. Unfocused movement/shot spread and
focused micro-control must be compared by native same-root outcomes; static
width alone is not a valid ranking. Power collection is valuable early only
when the collection path remains survival-feasible and produces a causal
later combat/survival benefit. Post-death Power recovery is outside NMNB.

The detailed current combat/resource boundary is
`CURRENT_COMBAT_RESOURCE_MODEL.md`.

The only current physical combat experiment is default-off
`--kill-before-saturation`. At a nonspell decision it may use the coherent
first-64 enemy prefix to select an ordinary enemy with observed HP `1..22`,
Power at least 100, positive vertical lead, and bounded horizontal separation.
It may then request only the unfocused peer of the planner's complete focused
movement action. The issue transaction applies that preference only when the
peer is fresh-safe and, when global allowed actions exist, inside their
intersection. No fresh transaction, an unsafe peer, deadline expiry, spell
state, low Power, missing combat rows, stay, or an already-unfocused action
preserves the baseline action. The option requires explicit hard no-Bomb.

This rule is experimental, not promoted route-wide authority. Its first
physical Stage-5 gate applied 27 preferences with zero Bomb/deadline
violations, but global guidance was unavailable throughout and total hits did
not improve on a different RNG root.

## Falsification And Promotion

The fastest valid loop is:

1. capture one canonical first-hit or resource/combat root;
2. reproduce the parent exactly in original TH08;
3. run action-conditioned native branches or a fail-closed model;
4. stop at the first native/model mismatch;
5. change one general mechanic;
6. show same-root improvement or mismatch closure;
7. validate the immutable winner in original native replay;
8. run one focused physical workload;
9. rotate to another stage/root before promotion.

Physical promotion additionally requires timing/deadline evidence, safe
fallback, no Bombs, correct transition/menu behavior, and repeat evidence.
Major integrated improvements earn a fresh full-route Lunatic diagnostic.
