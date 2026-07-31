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

The ordinary-stage root-only continuation may compute and query a rolling
global policy for diagnostic evidence, but that publication has no action
authority: its target, repair labels, and survival labels are removed before
baseline local planning. `--ordinary-preexhaustion-authority` does not change
that rule or promote the shadow future-hazard slab. Its scalar
player-control-reserve experiment is now physically rejected and is not
ordinary global action authority.

The rejected pre-exhaustion implementation observes native active input, held
complete desired input, player position/phase, player `+0xE2A68`, root time
scale, and the current action lease. If active and held differ, held is the
one pending complete action.
Within a six-physical-update lease, nature may choose every pending/new pickup
order, including next-step pickup and no pickup within the lease; this does
not use `enemy_manager_frame` as a pickup clock. Selecting held remains
no-write and samples no new delay. Future player movement scale is universally
bounded in `[0,1]`.

It attempts to activate when signed playfield-boundary reserve is within the
player radius plus maximum axis travel over the current lease and one
additional hostile-birth reaction lease. It retains actions whose minimum
reserve across every pipeline branch and every lease step does not decrease.
If an already-pending motion forces loss for every action, only actions with
maximum worst-lease reserve remain.

Physical run `20260731_152921` found two independent invalidations. First,
`player+0xE2A68` retains the deathbomb-window limit installed by
`0x0044AB40`; it is not a zero-when-alive predeath predicate, so all 7,202
nonspell decisions were rejected. Second, counterfactual roots with only that
gate removed still permit the losing `down_left`, then alias all actions when
an uncontrollable prefix or playfield clamp dominates scalar minimum reserve.
This finite boundary calculation may remain diagnostic, but its allowed set
must not be treated as survival authority.

The missing ordinary contract is a set-valued, hazard-space causal
predecessor that spans active/held/pending pickup order and policy publication
lead, preserves directional recovery, and includes bounded future hostile
birth/event coverage. Until that exists, fresh issue-time collision
certificates remain local-prefix authority only; they do not repair the
missing global viable set.

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
`--kill-before-saturation`. At a nonspell decision with Power at least 100 it
may use the coherent first-64 enemy prefix to select any living ordinary
non-boss enemy above the player and within bounded horizontal separation.
Full-health enemies are eligible; small enemies retain deterministic
selection priority. Horizontal alignment and same-direction unfocus remain
objective proposals only. They have no live eligibility source until exact
ordinary survival membership exists; the rejected scalar-reserve set and an
unconstrained interior state do not supply that membership.

Physical Stage-4A run `20260731_142342` falsified the current forecast
implementation as a later-wave observer. Its 376 observations all named the
same timeline-0 time-1 x=30 startup instruction. The zero-pointer fallback
does not distinguish not-yet-started from completed timeline state. Until
that lifecycle is made causal, forecast output has no objective authority and
the live path does not call it; full-health currently observed bodies remain
eligible under the other gates.

These are objective proposals, not hard safety authority. A missing or losing
ordinary viable root, no improving action, deadline expiry, or fresh issue
rejection must preserve the baseline action. Any future chosen complete
action must still pass the issue-time fresh certificate and hard no-Bomb
transaction. Selecting the held complete mask retains the ordinary no-write
semantics.

This rule is experimental, not promoted route-wide authority. Its first
physical Stage-5 gate applied 27 preferences with zero Bomb/deadline
violations, but global guidance was unavailable throughout and total hits did
not improve on a different RNG root.

The rotated Stage-4A gate made the diagnostic global policy queryable but did
not promote it to action authority. It observed 39 actual fresh-safe
preferences; 26 occurred in an already-losing shadow-global state and only
nine were also members of a winning shadow-global action set. Therefore
fresh-local safety alone is not the intended “inside the viable set” rule.
Move the combat objective earlier and require exact global membership before
promotion; retain the current default-off rule as a physical probe.

The following Stage-4A gate exercised that pre-exhaustion membership check:
124 preferences were applied before first hit 4148, all after a winning query
and fresh issue certification. The last winning query was frame 3679. A
200-HP middle-wave body appeared near x=320 at frame 3864, but the old HP gate
selected it only at frame 3900 at 15 HP. The new full-health and byte-verified
spawn observations directly addressed this delay.

The later scalar-reserve physical gate did not re-evaluate early killing:
zero reserve decisions became eligible and zero early-kill preferences were
applied. Its 17-hit/first-914 outcome is therefore evidence against the
eligibility/authority design, not against observed-body early kill.

The authorized follow-up physically rejected the forecast implementation and
exposed the larger authority failure. It completed with 18 hits and zero
Bombs. Of 11,947 available global queries, 5,341 were winning and 4,119 losing
queries exposed distant recovery, yet zero decisions were
viability-constrained and zero recoveries were selected. At canonical
nonspell hit 1915, the last winning query at 1707 allowed only
`stay/up/up_fast`; the fresh-local transaction selected `down_left`. The
global set became empty at 1710, while the fresh issue set became empty only
at 1912. Ordinary-stage global action authority, or a causally equivalent
pre-exhaustion filter, was therefore the next hard contract gap.

**Physically rejected:** run `20260731_152921` proved that the filter reached
configuration but never reached action authority. Native semantics invalidate
its zero-`+0xE2A68` gate, and retained-root counterfactuals invalidate scalar
boundary reserve as an equivalent global filter. No Stage-5 follow-up or
local-ranking evaluation is authorized from this result. The replacement
must be a set-valued hazard-space predecessor with pickup, publication, and
future-birth coverage.

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
