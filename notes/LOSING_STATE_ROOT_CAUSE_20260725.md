# Losing-State Planning Root-Cause Audit

Date: 2026-07-25

Status: the fallback defect is reproduced and two repairs have passed offline
shadow replay. Neither repair has live authority.

## Question

The continuous Lunatic run made global policies fresh enough to expose a
semantic problem: the Boolean kernel often becomes empty long before a hit,
while the local controller can still issue a short safe prefix. This audit
separates:

1. false emptiness from grid, delay envelope, uncertainty, or horizon;
2. a genuinely losing state inside the retained discrete model;
3. the action chosen after the kernel is empty;
4. the delivery cost of a better losing-state label.

## Physical Capture

**Observed:** Focused Stage-5 hard-no-Bomb run
`lunatic_route2_stage5_unattended_20260725_103655` reached
`route_complete`. It retained 6,884 decisions, 34 hit edges, zero Bomb-input
violations, and 1,666 exact lowered-hazard capsules. The supervisor verified
the original executable, Lunatic, route 2, Sakuya/Remilia, foreground
ownership, and the no-life-decrement patch, then terminated the game.

The run used the unchanged live coarse Boolean policy. Audit metadata now
records both the full asynchronous policy support and the estimator support
observed at policy submission. Capsule writing remained outside policy
authority.

Only hit 1,804 is a fresh Stage-5 attempt. Later hits are useful geometry and
planner counterexamples after death/respawn, but they are not independent
clean-route trials. In particular, the 97 sampled empty queries attributed to
spell 107 must not dominate a claim about clean Stage-5 survival.

## Exact Differential

The audit selected eight stratified policy queries from each 240-frame
pre-hit window. All 272 queries found their exact capsule. The 16-pixel base
reconstruction agreed with the physical trace on all 272; no policy-version
or reconstruction mismatch was relabeled as a false empty.

Of 195 base-empty queries:

| Independent counterfactual | Empty queries made viable |
| --- | ---: |
| Query-time estimator support instead of full `[1..6]` | 6 |
| 8/4-pixel spatial refinement | 7/16 |
| Remove only uncertainty growth | 24 |
| Remove all retained uncertainty inflation | 34 |
| Shorten the requirement to 32/48/64 frames | 40/28/14 |
| No tested single factor | 147 |

These are independent ablations, not additive causal counts. Some queries are
rescued by several individual variants.

**Observed scope correction:** In the canonical first-hit window, the global
state was winning at the first four stratified queries and became empty at
query/decision 1678/1680, 126 frames before hit 1,804. The four empty samples
split into one spatial/uncertainty/horizon rescue, one
uncertainty/horizon rescue, and two unresolved late states. Therefore the
clean first failure is not evidence that all Stage-5 emptiness is genuine.

**Observed monotonic exclusions:**

- Five queried collision slots were born after the policy source. Adding
  future hazards can remove winning states but cannot rescue an empty state,
  so these are soundness gaps rather than false-empty causes.
- Of 77 instant-winning queries with a comparable later policy, a terminal
  overlap mask rejected 29. The present instant-safe terminal layer is
  optimistic; it also cannot explain an empty predecessor.
- Replacing the full asynchronous delay envelope with the exact current
  support rescues only 6/195. Full `[1..6]` support is overconservative in
  specific cases but is not the dominant single cause.

## Confirmed Fallback Ordering Defect

The fused native/scalar-parity recurrence labels every losing state by:

1. maximum guaranteed safe modeled frames;
2. bottleneck signed clearance among equal horizons;
3. a best-action mask.

At canonical decision 1,680:

- live 16-pixel Boolean state: empty;
- survival label: 74 frames;
- survival-best actions: `stay`, `up_fast`;
- live fallback: `down_right_fast`;
- fresh local robust collisions: 0;
- fresh local robust clearance: `+6.443`;
- repair volumes were present, so the existing boundary-reserve term was
  disabled completely;
- the selected action's 24-pixel diagnostic control-reserve deficit was 24
  pixels in exact replay.

At canonical decision 1,760:

- survival label: 9 frames;
- survival-best actions: `stay`, `right`, `right_fast`;
- live/replayed fallback: `down_right`;
- survival shadow: `stay`;
- both actions have the same fresh local hard vector.

This is stronger than correlation at a hit. It reproduces the exact moment
where the controller leaves the winning kernel, shows that endpoint/repair
guidance selects outside a longer-survival mask, and shows why the live
boundary heuristic did not participate.

## Shadow Replay

All 195 losing queries were replayed from their retained local bullet, laser,
enemy, timing, and policy inputs. Survival and reserve labels never controlled
physical input.

| Shadow variant | First-action changes | Fresh hard-vector regressions |
| --- | ---: | ---: |
| Repair-state control reserve | 11 | 0 |
| Survival horizon first | 42 | 0 |
| Survival plus reserve | 50 | 0 |

Survival-best membership changed from 134/195 under the baseline replay to
175/195 under the survival shadow. On the 89 rows where the baseline replay
also matched the recorded action, the combined shadow changed 34 actions and
improved best-mask membership from 52 to 81. It changed two replay-aligned
canonical-first-hit actions.

The reserve-only shadow improved the consistently measured endpoint reserve
deficit on 13 rows and regressed it on zero. Survival-first may legitimately
consume reserve when the survival-best mask requires it; the combined shadow
then uses reserve only to order locally hard-equivalent, survival-equivalent
choices.

Local replay median/p95 remained about 11/16 ms for all four variants because
querying a retained label is constant-time. This timing excludes producing
the global label.

## Delivery Gate

Forty-eight stratified Stage-5 capsules compared whole Boolean and fused
solves with capsule decode outside the timed boundary:

| Metric | Boolean | Fused survival |
| --- | ---: | ---: |
| Whole solve median/p95 | 76.96 / 197.99 ms | 125.31 / 229.58 ms |
| Clearance median/p95 | 15.12 / 51.03 ms | 15.93 / 51.17 ms |
| Viability median/p95 | 46.77 / 175.22 ms | 109.69 / 222.69 ms |

Viable arrays and safe-action masks matched on all 48 capsules. The current
kernel is substantially cheaper than the rejected CE-0102 experiment, but
fused induction still adds about 48 ms at the median. Computing it before
publishing the Boolean mask would indirectly change live control through
policy age, even if its labels were called “shadow.”

## Root Cause

**Observed and confirmed:** Once the Boolean kernel is empty, the live
controller has the wrong objective ordering. It may choose a shorter modeled
survival branch, and repair-neighborhood states do not activate the existing
control-reserve term. This is the first repair target.

**Observed but mixed:** Global emptiness has several causes. Spatial
quantization, uncertainty inflation, the 80-frame requirement, and the full
delay envelope each produce real witnesses, but no one factor explains most
sampled empty states.

**Inferred:** Many late/post-respawn states may be genuinely losing under the
current frozen model. That does not prove native uncontrollability. The model
uses an eight-frame decision layer and has no explicit pending-command or
remaining-delay state; the controller cadence and action pipeline can differ.
The 4-frame clipped audit is not an exact replacement. A pending-command
reachability oracle is required before attributing all 147 unresolved samples
to geometry or native impossibility.

**Hypothesized:** Stage-107's large unresolved cohort contains a combination
of contaminated respawn entries, event/trajectory forecast error, and temporal
control abstraction. It should not be addressed by a spell-name branch.

## Implemented Boundary

- `losing_control_reserve` is an explicit default-off shadow switch. It lets
  repair/survival states use delay-scaled reserve during replay without
  changing the live default.
- Diagnostic reserve is now measured consistently even when it has no
  selection authority.
- The audit supports stratified sampling, current-delay and uncertainty
  ablations, and horizon-safe prefix slicing for packed laser trajectories.
- Survival labels remain `LIVE_SURVIVAL_LABELS = False`.
- Fine refinement remains absent from the live path.

## Next Repair Gate

1. Optimize or query-localize fused survival induction so the Boolean policy
   can be published first, without waiting for shadow labels.
2. Preserve the hard order:
   fresh local collision/delay certificate, then guaranteed survival frames,
   then survival bottleneck, then control reserve, then repair/kernel
   distance.
3. Build an independent pending-command/remaining-delay oracle and test the
   canonical 1,680 onset plus a predefined cross-stage cohort.
4. Run repeated clean Stage-5 focused trials. Acceptance compares the first
   hit or clean clear across RNG/entry samples; post-respawn aggregate hit
   counts remain discovery evidence.
5. Do not promote labels merely because the offline action looks better.
   Require no increase in missing/expired policies, policy age, local latency,
   or issue-time hard-vector contradictions.
