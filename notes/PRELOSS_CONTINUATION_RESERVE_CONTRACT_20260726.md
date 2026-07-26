# Pre-Loss Continuation And Interior-Reserve Contract

Date: 2026-07-26

Status: proposed, default-off, offline/shadow only

## Decision And Scope

The next bounded strategy experiment is to preserve controllability before
the current Boolean viability kernel becomes empty.  It does not enlarge or
replace the live safe-action set.  It changes only the ordering of actions
that have already survived the current global query and the fresh local hard
certificate.

**Observed:** complete Hard Route-2 `184942` had 38/39 contacts after global
kernel exhaustion, with boundary factors on 30 contacts.  Hard Stage-4A
`202439` had boundary factors on 10/15 contacts.  The issue-time transaction
repair then passed two complete Stage-4A gates without a latency regression.
The remaining dominant failure is therefore loss of future feasible control,
not the old fresh/global transaction and not raw geometry throughput.

**Observed:** the current `ViabilityQuery` already returns, for every safe
root action, an exact `repair_volume` under the declared finite recurrence.
The final local selection uses that value late, after several soft columns,
but the Python and native beam reducers do not use it at all.  A
high-continuation first action can therefore disappear before final
selection.  Viable roots also do not enable the delay-scaled boundary
control-reserve column.

**Inference:** the first safe experiment should move the existing exact
finite-model continuation value earlier only after the historical beam has
finished and terminal threat scores are known.  A more aggressive
repair-aware beam was measured and rejected: on an 800-root hit-window sample
it regressed the terminal hard vector twice because future terminal threat was
not yet available at pruning time.  Final-only ranking does not close the
candidate-loss gap, but it can improve a retained action without discarding
the historical hard-terminal incumbent.

## Physical Problem Contract

### Objective

The physical objective is still hard no-Bomb survival: minimize native hit
events over the route.  At a decision whose authoritative viable action set
is nonempty, prefer an action that preserves more verified continuation
choices and reversible interior motion, before route/position/item soft
objectives.

### State And Observations

At plan time the experiment may use only:

- the current immutable global policy version and its exact-root query;
- the query's nonempty safe-action set and per-safe-action repair volumes;
- native player, input, bullet, laser, enemy-body, resource, and phase
  observations already available to the local planner;
- the current route target/deadline supplied by explicit strategy data;
- the declared delay support and local projected hazard volume.

It may not condition on a later hit, future replay row, hidden RNG, an
unobserved pickup delay, or a policy result that arrives after this root.
Issue-time enemy recertification remains a later transaction and may preserve,
restrict, or explicitly relax the planned global constraint under its
existing contract.

### Actions And Issue Semantics

The physical action alphabet and no-write semantics are unchanged.  This
experiment ranks complete direction/focus masks only inside the effective
nonempty global/fresh intersection.  It never emits Bomb.  It samples no new
delay and grants no authority to desired input: native active input and the
existing pipeline estimator retain their current meanings.

The proposal is active only if all of the following hold:

1. the caller explicitly enables it;
2. the original global action set is nonempty;
3. the effective post-prefix action set is nonempty and was not relaxed;
4. every effective action has an exact repair-volume value from the same
   policy query.

Otherwise the historical ordering is bit-for-bit authoritative.

### Uncertainty And Transition

`repair_volume(a)` is the minimum, across the policy's declared pickup-delay
branches, of the number of viable next-layer state/action pairs in the
configured repair neighborhood after selecting `a`.  It therefore preserves
the controller-exists/nature-for-all delay ordering already implemented by
the finite policy.  It does not add missing cadence histories, pending-input
histories, future bullet births, transform events, or semantic manager-clock
states.

The interior reserve distance is

```text
unfocused cardinal speed * maximum declared pickup delay
```

and its deficit is the total unavailable axis-wise distance caused by
playfield clamping at a candidate endpoint.  This is a reversible-control
proxy, not a reachable-set certificate.

### Horizon And Resources

The global repair value uses the immutable policy horizon and layer cadence.
The local beam and terminal threat horizons remain unchanged.  Lives, Bombs,
Power, Boss HP, and route phase remain resource/profile state; this proposal
does not convert them into scalar safety weights.

### Safety Invariants

- Never add an action to the global safe set.
- Never retain a first action outside the effective global/fresh set.
- Local collision count and negative signed-clearance deficits dominate every
  continuation or reserve preference.
- Terminal collision count and negative terminal clearance dominate every
  continuation or reserve preference at final selection.
- Issue-time recertification of the action actually sent remains mandatory.
- Hard no-Bomb remains unconditional.
- A relaxed, missing, stale, partially covered, or losing global query cannot
  activate this proposal.

### Computation, Publication, And Fallback

No solve, allocation-heavy graph expansion, or cold cache fill is added to
the issue thread.  The repair volumes already exist in the published query.
The native beam reducer and its ABI remain unchanged.  Final selection inserts
two scalar lexicographic columns over at most the retained beam width.  The
disabled path supplies constant columns and preserves historical behavior.

The result is consumed only for the matching local decision.  Policy-version
and issue-time freshness rules are unchanged.  Any exception, missing value,
relaxation, or unsupported native path falls back to the historical policy.

## Lexicographic Experiment

The proposal inserts the following columns after collision and
negative-clearance authority, but before route and ordinary soft costs:

1. exact survival-label membership, when such a label is available;
2. descending exact `repair_volume`;
3. ascending delay-scaled boundary reserve deficit;
4. existing route gate/tube deficit;
5. existing positive-clearance, safety-value, recovery, risk, item, and
   positional preferences.

The columns are present only during final endpoint selection, after local and
terminal hard scores exist.  Quantized beam canonicalization and truncation
remain exactly historical.  Disabled columns are constant zero so the default
ordering is unchanged.

This ordering is intentionally lexicographic.  No arbitrary scalar converts
one repair cell into pixels, risk, items, or damage.

## Five Formal Review Questions

### 1. Which physical histories map to one model state?

The global query merges histories sharing policy version, layer, projected
lattice cell, and modeled active action.  The local planner additionally uses
the exact observed position and current hazard snapshot.  These histories are
not known to be fully control-equivalent: subcell position, explicit
active/held/pending input, future births, and frozen-manager-clock semantics
can differ.  Therefore the repair score has finite-model ranking authority
only and remains proposal-only.

### 2. Are all declared uncertainty branches present and nonclairvoyant?

Within the existing Boolean policy, repair volume takes the minimum over the
declared delay branches and uses one root action before nature's branch is
known.  No replay-future observation enters the choice.  This proposal does
not repair any missing recursive cadence, pending-command, semantic-clock, or
future-birth branch, so claims are limited to the unchanged recurrence.

### 3. What does an exact solution answer?

An exact repair value answers: under this finite lattice, horizon, hazard
volume, delay support, and repair radius, how many next-layer viable
state/action pairs remain in the worst delay branch near the selected
transition endpoint?  It does not answer unrestricted physical route
survival and does not prove that the largest count is the best physical
action.

### 4. What is solved or bounded, and what falsifies it?

The repair value is computed exactly for the existing finite arrays.  Beam
ranking is a heuristic use of that exact value; it is neither a lower nor an
upper bound on physical survival.  Falsifying cases include:

- a higher-volume action with a worse fresh hard vector;
- a higher-volume action that causes earlier exact kernel exhaustion on a
  comparable replay continuation;
- a route gate missed because reserve outranks a phase-hard deadline;
- a future birth or transform outside the policy volume that invalidates the
  apparent continuation;
- a changed issued action with a worse fresh or terminal hard vector;
- Python/native selected-action disagreement under the unchanged reducer.

Any fresh-hard regression rejects the ordering.  Route/profile regressions
keep it outside live authority even if the finite repair score improves.

### 5. Can the result arrive before issue time without changing the problem?

The ranking consumes the already published same-version repair array and is
computed only over the completed beam.  It does not launch background work,
change the native reducer, or wait for a newer policy.  Timing gates must
nevertheless show Python/native parity and no material local-plan p95
regression.  Issue recertification still decides whether the plan remains
consumable.

## Full-Screen Hazard Pruning And Aftereffects

Screen-space cropping is not valid by itself.  A far hazard can enter a later
reachable tube, and a stopped, redirected, resumed, transformed, or
not-yet-born hazard can have an effect after its current geometry is distant.

A hazard or hazard group may be removed from a query only if a conservative
space-time exclusion proves, for every queried frame and every state reachable
by every retained action/history branch, that its swept collision volume
cannot intersect the player volume after adding:

- player hitbox radius;
- lattice and projection error;
- trajectory/decode uncertainty;
- delay/cadence reachable displacement;
- every declared stop/resume/redirect/transform envelope; and
- every birth that the recurrence claims to cover.

Equivalently, pruning must preserve every clearance sample, viable-state bit,
and safe-action mask that the unpruned recurrence could query.  A proof-backed
reachable action-column/tube filter can therefore be useful.  An
`x/y` viewport crop, present-velocity cone, or "currently far away" test is
proposal-only and cannot receive hard safety authority.

The first Option-A experiment does not change hazard membership.  Selective
geometry pruning remains a later performance optimization only if profiling
shows geometry again dominates and complete parity is established on
live-like, static-segment, and transform-adversarial workloads.

## Evidence Gates

Before any physical A/B:

1. deterministic retained-root regression showing that the final-only flag
   changes an issued action only after equal hard scores;
2. unchanged randomized Python/native reducer parity and end-to-end
   selected-action parity with the final-only flag;
3. same-root paired Hard replay with zero global-set and fresh-hard
   regressions;
4. report action changes, repair-volume changes, reserve-deficit changes,
   route-gate changes, distance to the next hit, and alternating-order
   latency;
5. quick Linux and Windows suites;
6. only if the offline direction is favorable, repeated clean focused Hard
   trials with separate baseline/proposal captures and no audit workload.

Single-step replay cannot claim prevented hits.  RNG-distinct physical totals
cannot by themselves establish a causal effect.

## First Offline Result

**Observed:** the initially implemented repair-aware beam was effective at
changing behavior but failed the hard gate.  Across 800 broad roots it changed
303 actions, improved repair volume on 288, and had no sampled hard
regression.  Across 800 roots within 300 frames of the next recorded hit it
changed 392 actions, improved repair volume on 356, but produced 2 terminal
hard regressions.  The concrete roots were Stage-4A `202439` frame `28412`
and Stage-4A `212756` frame `12843`.  The native-v2 experiment was removed;
the retained rejected artifacts are:

- `artifacts/benchmarks/hard_preloss_beam_preference_rejected_broad_20260726.json`;
- `artifacts/benchmarks/hard_preloss_beam_preference_rejected_prehit300_20260726.json`.

**Observed:** final-only ranking over the same fixed reservoirs changed 7/800
broad actions and 13/800 pre-hit actions.  Every changed action had an equal
fresh/terminal hard vector and remained inside the authoritative global set.
In the pre-hit cohort, 11/13 changed actions reduced boundary reserve deficit,
2/13 increased exact repair volume, and none regressed either value; route
gate deficit improved once, tied eleven times, and regressed once.  Baseline
versus proposal median/p95 was `10.60/17.19 ms` versus `10.61/17.26 ms` under
the deliberately concurrent two-process replay workload.  This is directional
offline evidence, not a prevented-hit claim.

**Inference:** final-only ranking is safe enough to keep as a default-off
proposal, but its action coverage is too small to call it the main solution
to early kernel exhaustion.  The next algorithmic experiment should preserve
the complete historical beam as an immutable incumbent and add a bounded
continuation-biased supplemental lane.  Final hard comparison over the union
can then improve candidate coverage without making a baseline hard endpoint
unavailable.  The extra lane must be independently budgeted and must not
delay authoritative publication.
