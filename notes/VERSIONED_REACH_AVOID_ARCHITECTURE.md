# Versioned Safety Transactions And Weight-Free Reach-Avoid

Status: architecture and physical Stage-4A checkpoint on 2026-07-24. The
local cached-policy intersection, enemy lifecycle union, observed world-motion
estimator, and aligned issue guard have executed in complete no-Bomb trials.
The survival-horizon game remains an independent scalar oracle, not a live
controller.

## Observed Evidence

CE-0092 is an observe/compute/act race. The Stage-4A decision captured frame
35,412 geometry, an 18-body contact ring appeared in a frame-35,413 snapshot,
the old action issued at 35,415, and slot 18 made exact contact at 35,420.
Reducing Python execution time would shorten this exposure window but could
not make it zero.

The original Stage-4A global/local report also compared different contracts.
The global Boolean asks whether one policy survives every modeled delay over
the remaining 48--80-frame horizon. The local certificate asks whether the
selected first action survives only its 8--12-frame delay-plus-hold prefix.
Consequently, 2,395 global-losing/local-prefix-safe rows are not direct
contradictions.

The action-aligned comparison is smaller and more important:

- 6,613 alive/action-eligible rows were comparable;
- 4,048 had a winning global state and a safe selected prefix;
- 2,395 had a losing global state but a safe short prefix;
- 138 were losing globally and unsafe locally;
- 32 had a winning global state but an unsafe selected prefix;
- in 30 of those 32, the selected action itself belonged to the cached global
  winning-action set.

Those 30 are direct contract contradictions. The live policy's source age was
not exceptional, but its underlying hazard snapshot was 19--48 frames old.
Several contradictions had `-10..-22` local clearance, far beyond a small
nearest-cell margin. Missing births or later hazard state are therefore a
plausible mechanism; this remains inferred until each row has a source-snapshot
hazard differential.

## What Can And Cannot Be Guaranteed

No controller can guarantee collision avoidance if an unmodeled hostile body
may appear at an arbitrary position after the last observation, including
already overlapping the player. This is an information limit, not an
implementation-language problem.

A useful guarantee requires explicit assumptions:

1. the captured player and hazard state is coherent or carries a bounded
   frame window;
2. every hazard birth before the certificate horizon is either predicted or
   contained in a declared birth envelope;
3. motion/model error and actuator-delay support are bounded;
4. the selected action tube is safe for every state in those bounds; and
5. the action is issued before that certificate expires.

When any assumption changes, the plan version is invalid. Continuing to issue
it is a correctness error.

## Enemy Geometry Is A Hybrid Observation Process

CE-0094 and CE-0096 expose two distinct hidden-state errors.

First, native active/contact flags are modes of an enemy slot, not object
identity. A contact body can clear bit `0x04`, or even clear the active mode
for tens of frames, and later resume a continuous lethal trajectory. The
robust geometry for an already observed slot is therefore the union of:

```text
currently contact-enabled body
active but contact-disabled body
bounded projection of a recently absent slot
```

The union is scoped to gameplay epoch, stage, and spell context and expires at
the 80-frame planning horizon. It is not an unbounded ghost cache.

Second, TH08 `enemy+0x2D4C` is the velocity of an internal motion component,
not generally the derivative of lethal world position `+0x2D88`. Static code
at `0x42DEB0` proves where the component is integrated; runtime pointer
`0x00597600` proves the fields diverge, retaining world `y=164` while the
second internal float reaches `146.910`.

The adapter now estimates world velocity from consecutive `+0x2D88`
observations. An implausible secant is a hybrid jump, so the exact new
position is accepted while the last validated velocity is retained. A failed
trial widened every unknown/jump by 16 pixels; that produced 34 hits and
26,004 false trajectory invalidations. The fixed margin was rejected because
it was neither a reachable set nor a calibrated error bound.

Motion invalidation is now computed after aligning both tracked snapshots to
the same player epoch. Raw snapshots still supply allocation, removal,
contact-mode, and size transitions. In the corrected physical run, issue
observations with changes fell from 2,841 to 1,258 while local-plan and cadence
tails remained at `49.96 ms` and `6` frames.

This model cannot cover a never-observed slot. CE-0097 contains two exact
collisions from rings born 4 and 5 frames after the governing action's final
issue observation. Those require a future spawn event or a sound birth
envelope, not a longer memory TTL.

## Observe-Plan-Validate-Act As A Transaction

The controller should behave like optimistic concurrency control:

```text
capture coherent version v
    -> build nominal long-horizon plan P(v)
    -> compute fresh local action and tube certificate C(v)
    -> recapture lightweight version v'
    -> if relevant geometry changed:
           recompute the all-action short tube certificate C(v')
    -> if the certificate is still inside its delay deadline:
           issue the certified action
       else:
           abort the transaction and reobserve
```

The TH08 adapter now retries one synchronous 64-slot prefix read when the
enemy-manager frame changes across the read. It reads that prefix before and
after local planning. Adds/removes, contact-mode changes, size changes, and
aligned world-trajectory residuals invalidate the old enemy-body certificate.

This closes the observed enemy-prefix race only under its observation scope.
Bullets and lasers can also be born during planning. The general next native
boundary should therefore be an issue-time safety shield:

1. read compact/current bullet, laser, and enemy state;
2. decode and spatially filter it without constructing per-hazard Python
   objects;
3. project every candidate action tube over delay support;
4. return the certified action set and lexicographic labels in one packed
   result.

That packed decode-plus-project-plus-certify batch is a good C++ boundary.
Python should retain process/session orchestration, policy versioning,
telemetry, experiments, and TH08 adapter configuration.

Faster computation still matters: it narrows the invalidation window and makes
the shield cheaper. Planning further ahead matters only for births represented
by ECL/timeline/RNG state or a conservative event envelope. Neither replaces
issue-time validation.

## The Exact Weight-Free Control Problem

For the modeled state, control is a finite adversarial reach-avoid game:

```text
K[k, active, x] =
    exists issued action u
    such that for every actuator delay d:
        every physical state in the transition tube is safe
        and the successor belongs to K[k + 1, u]
```

This `exists action / forall delay` recurrence is already correct for the
discrete model. It should not be replaced with a weighted risk sum.

Three approximation boundaries must instead become explicit.

### Fresh Local Intersection

A cached long-horizon winning mask is advice from an older model version. It
cannot force an action that the fresh local tube checker already proves
unsafe. The implemented rule is:

```text
issued candidates =
    cached winning actions intersect fresh prefix-safe actions
```

If that intersection is empty, all actions are recertified and the cached mask
is relaxed. This path is rare and marked in telemetry.

Hard Stage-4A audit `202439` found that this contract was implemented during
ordinary local planning but not during the later enemy-change recertification.
That recertifier ranked all 17 locally certified actions and could replace an
in-mask global plan with an out-of-mask local action while retaining
constrained telemetry (CE-0127).

The issue transaction now computes the complete fresh safe set once and
applies the following deterministic rule:

```text
I = cached winning actions intersect fresh prefix-safe actions

if I is nonempty:
    preserve the planned action when it belongs to I
    otherwise choose the best fresh hard certificate inside I
else:
    explicitly relax the global constraint
    preserve a fresh-safe planned action or choose the best fresh-safe escape
    use a least-bad local action only when no fresh-safe action exists
```

The transaction retains the planned and selected certificates, complete fresh
safe set, exact intersection, selection reason, and relaxation state.
Repair-volume, recovery-distance, safety-value membership, and survival-best
membership are rebound to the selected action. A beam-endpoint control-reserve
value is marked invalid if recertification changes the action because the
issue shield does not rerun the long beam. This is an offline-verified
correctness repair; one no-audit Hard Stage-4A physical gate is still required.

The first no-audit gate `211210` recorded 2,417 transactions, preserved 2,387
planned actions, changed 30, and had zero silent outside-global selections.
Local, recertification, and global-solve p95 were
`21.486/4.704/421.706 ms`, none worse than audit capture `202439`.
Two empty-intersection rows used the wrong preservation reason while still
explicitly relaxed and unconstrained (CE-0128); the reason was corrected
without changing the selected action.

On the 30 retained Stage-4A direct contradictions, paired trace-radius replay
changed 16 actions. The hard vector improved on 10 rows and regressed on zero;
robust-collision decisions changed `29 -> 23`, and negative-certificate rows
changed `30 -> 23`. Eligible replay median/p95 rose
`11.39/21.12 -> 20.00/36.08 ms`; because only 30 of 6,613 comparable live rows
were eligible, this does not imply a general local-latency regression.
Physical validation remains required.

### Sound Continuous Query And Adaptive Refinement

Nearest-cell membership is not a continuous-state proof. Hazard clearance is
1-Lipschitz in player position, and clamped constant-velocity dynamics are
nonexpansive. If `Q(node, action)` is the robust bottleneck clearance value,
then a live position at distance `r` from that node is certified only when:

```text
Q(node, action) > required_clearance + r + model_error
```

The game-neutral safety-value query now exposes this margin test. When the
coarse value is inconclusive but the fresh local prefix is safe, refine space
and time only around the reachable tube and viability boundary. A generated
narrow-tunnel regression proves that a coarse grid can miss a real winning
state that a refined grid recovers; changing a weight cannot recover an
unrepresented state.

### Outside The Winning Set

On one fixed exact graph, a collision-free robust bridge into the future
winning set would make the predecessor winning by definition. Therefore a
soft endpoint `recovery_distance` is never a new proof. It is compensating for
an abstraction/model mismatch or intentionally weakening the contract.

If the exact/refined winning set is genuinely empty, survival is no longer
guaranteed to the full horizon. The correct fallback is still weight-free:

```text
maximize guaranteed collision-free physical frames
then maximize bottleneck signed clearance
then apply control simplicity or positional preferences
```

`touhou_control.reachability_oracle` implements this recurrence with explicit
scalar loops. It exactly matches Boolean winning membership and action masks
on randomized small games. A constructed regression shows why max-min
clearance alone is insufficient outside the kernel: it can prefer a shallow
collision now over a deeper collision one frame later.

Across 9,720 states from 24 deterministic dense birth/stop/redirect games,
4,905 were losing. Margin-only and survival-horizon best-action sets differed
on 3,882 losing states. On 190 states, margin-only selection guaranteed fewer
survival frames, losing 226 guaranteed frames in aggregate. This supports
survival horizon as the first fallback label; it does not establish TH08
physical improvement.

## Ordered Implementation

1. Keep the physically validated enemy lifecycle and issue-time version
   contract as a hard gate; use Stage 4A and Stage 5 retained corpora for
   regression.
2. Attribute every direct action-contract contradiction to stale births,
   policy age, off-grid margin, or a transition-model difference.
3. Move lexicographic survival-horizon induction into the existing native
   viability recurrence and require scalar-oracle parity.
4. Prototype adaptive fine-grid value induction around contradicted/empty
   queries and require scalar-oracle parity.
5. Build the packed issue-time bullet/laser/enemy safety shield in C++ and
   compare its full action certificates with the Python oracle before physical
   use.
6. Use ECL/timeline/RNG evidence to declare future birth events or envelopes;
   keep game-specific decoding in the adapter and event contracts
   game-neutral.

Every native step must pass independent scalar parity, generated adversarial
birth/stop/reverse/redirect cases, Linux and Windows builds, whole-pipeline
timing, and physical no-Bomb validation.

The current full-horizon native clearance-value pass is not ready to enable
live. On the fixed 1,360-AABB workload, Boolean-only warm median was
`67.28 ms`; separately adding the 80-frame value recurrence raised it to
`151.30 ms`, of which `87.59 ms` was value induction. A native implementation
should fuse Boolean/margin outputs or compute values adaptively rather than
paying two complete backward passes.
