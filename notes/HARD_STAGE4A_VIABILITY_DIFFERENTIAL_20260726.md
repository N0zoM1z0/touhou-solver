# Hard Stage-4A Viability Differential And Next-Round Decision

Date: 2026-07-26

Status: complete audit-only physical capture and offline differential; no new
input authority

## Bottom Line

The decoder and native local geometry remain fast enough to stop being the
primary research target, but the issue-time transaction is not yet
semantically correct. Before choosing a new global strategy, fix the
fresh-enemy recertifier so that it preserves a still-safe planned action and
otherwise intersects fresh local certificates with the cached global winning
mask.

The next strategy target should then be feasibility preservation before
kernel exhaustion, followed by a verified longest-survival fallback after
loss. Uniform 8- or 4-pixel full-field refinement should not be the main next
step.

## Physical Capture And Integrity

Run `hard_route2_stage4a_unattended_20260726_202439` was an explicitly
audit-only Hard Route-2 Stage-4A workload. The ordinary live policy remained
authoritative; synchronous capsule production was enabled and makes hit count
unsuitable as a controller A/B.

**Observed:**

- accepted `route_complete`, Hard index 2, Stage-4A route index 3;
- 13,535 decisions over frames `2..44606`;
- 15 hit edges, zero Bomb input, and no foreground/runtime/JSON failure;
- 7 observed bullet overlaps, 7 modeled committed-prefix collisions, and 1
  observed enemy-body overlap;
- boundary/fast-mode/corridor-deadline factors on 10/11/7 hits;
- local plan `12.903/22.274 ms` median/p95;
- global policy solve `151.377/429.975 ms` median/p95 and first-observed age
  `2/8` frames;
- 1,741 readable capsules, 1,729 referenced by the trace, with no missing
  reference.

Bundle audit:

```text
trace SHA-256  88f54b6a7984878b0e6cf88580fc9f217226b0d6204d29701fb15a7e0af56b41
bundle SHA-256 89b1bd71e299a429091092a59da0cfc628a259fdf181a68c546bccb5d78592e6
```

The 15-case executable regression corpus passes. The raw trace and capsules
remain local and ignored; compact artifacts are retained.

## Exact Same-Root Differential

The audit selected eight stratified queries from each 240-frame pre-hit
window. All 120 selected queries found their capsule and the 16-pixel
reconstruction matched the trace. Sixty-one queries were empty.

| Classification or factor | Empty roots |
| --- | ---: |
| Modeled losing, unresolved by tested variants | 47 / 61 |
| Spatially rescued by 8 or 4 pixels | 6 / 61 |
| Primary finite-horizon collapse | 8 / 61 |
| Any h32 rescue | 11 / 61 |
| Any h48 rescue | 3 / 61 |
| Any h64 rescue | 0 / 61 |
| Current query delay support rescue | 1 / 61 |
| Uncertainty-growth or all-inflation diagnostic rescue | 6 / 61 |
| Fresh 16-pixel policy rescue | 0 / 61 |

The factors overlap. Three spatial witnesses were viable at 8 pixels and
three required 4 pixels. Shortening the horizon is not a safety proof: the
h32 result often becomes winning only because it stops before the later
failure, and no empty root survived the still-shorter-than-live h64
requirement.

**Observed exclusion:** fresh policy recomputation remained empty on all
61 empty roots. Ordinary solution publication staleness is not the dominant
false-empty source in this cohort.

**Observed soundness warnings:**

- 9/59 comparable nonempty roots were rejected when their terminal set was
  intersected with a later same-context policy;
- seven empty observations, concentrated before two physical hits, did not
  contain the later collision projectile at policy source.

Terminal overlap and future births can remove optimistic winning states; they
cannot rescue an already empty state. They are upstream soundness defects,
not explanations for coarse false emptiness.

## New Transaction Counterexample

The design contract says:

```text
issued candidates =
    cached global winning actions intersect fresh prefix-safe actions
```

The issue-time enemy recertifier does not implement that contract. It
recomputes all 17 local certificates and ranks all 17 actions without
receiving the global allowed-action set. It can therefore replace a globally
winning planned action with a locally safe action outside the global winning
mask while leaving `viability_constrained=true`.

**Observed population:**

- 2,672 decisions triggered issue-time enemy recertification;
- 1,435 changed action;
- 255 globally winning rows ultimately issued outside the reported winning
  set;
- 168 rows specifically changed from a planned action inside the winning set
  to an action outside it while telemetry still said constrained and
  unrelaxed;
- 243/255 outside-mask selections were locally hard-safe, showing that this is
  primarily loss of long-horizon authority rather than immediate geometry
  failure.

The same function also retains per-action repair/recovery fields from the old
action after replacing the action, so its strategy telemetry can describe the
wrong action.

### Canonical fresh-attempt witness

Before the first hit at frame 3419:

1. frame 3351 was globally winning and issued `up_fast`;
2. frame 3353 still had exactly four global winning actions:
   `up`, `up_left`, `up_fast`, `up_left_fast`;
3. local planning selected `up_fast`;
4. an enemy-velocity version change triggered issue recertification;
5. recertification replaced `up_fast` with locally safe `down_fast`, which was
   outside the global winning set;
6. the next decision at frame 3356 was globally empty;
7. the player remained near the left/bottom boundary until contact.

This is not proof that retaining `up_fast` prevents the hit: the trace did not
serialize the fresh all-action certificate vector, so the four-way fresh
intersection cannot be reconstructed. It is proof that the current
recertifier neither preserves nor explicitly invalidates the global
constraint.

## Losing-State Evidence

The coarse survival shadow labeled all 61 empty roots:

- 27 issued actions were outside its best-action mask;
- six labels guaranteed at least the observed query-to-hit interval;
- all six covering roots issued outside the best mask.

Those six roots occur after the canonical first hit and are not independent
clean-route effects. They nevertheless reproduce CE-0101/CE-0106 on a new
difficulty and stage workload: endpoint/repair fallback can forfeit modeled
survival time.

A dense active-only fused label is not ready for authority. Active/held/
pending semantics changed prior exact cohorts materially, and a label from
the frozen finite forecast is not a native survival proof. The safer next
form is an attainable lower witness from the exact augmented root, retained
per proposed action and intersected with the fresh all-action certificate.

## Performance And CPU

The complete differential used `7:32.59` wall time, `1,341.87 s` user time,
298% average CPU, 1.56-GB maximum RSS, and no swap.

A 12-root same-capsule cost sample measured:

| Grid | Median | p95 | Empty roots rescued |
| --- | ---: | ---: | ---: |
| 16 px | 59.10 ms | 201.94 ms | baseline |
| 8 px | 225.90 ms | 907.68 ms | 3 / 61 |
| 4 px | 1,062.85 ms | 3,506.43 ms | 6 / 61 |

Uniform 4-pixel induction is about 18x the sampled 16-pixel median for a
9.8% empty-root rescue rate. It is unsuitable for the live issue path.

The host's 20 logical CPUs are useful for independent immutable-root work:
three or four process-level shards, each retaining the proven four-worker
native kernel, can consume roughly 12--16 logical CPUs without sharing a
workspace. Results must be merged in deterministic root order. This is an
offline/precompute optimization, not permission to raise the live
same-root worker limit or run stale FIFO work.

## Formal Review Of The Proposed Order

1. **History equivalence:** the mandatory issue fix adds no model merge. It
   preserves the exact cached root/version and intersects it with a newer
   local observation. Losing-state authority must use explicit active,
   held, pending, and remaining-delay state; inconsistent discontinuity roots
   fail closed.
2. **Causality:** the fresh local certificate universally covers declared
   pickup support. A losing-state witness must keep cadence and hidden-delay
   branches merged before future maximization.
3. **Physical decision:** the intersection answers whether an already planned
   finite-model action is still locally issuable. A spatial or survival
   variant remains a finite-model proxy, not physical proof.
4. **Bound:** an exactly verified restricted candidate is an attainable lower
   bound only for its retained witness. Fine-grid Boolean feasibility is exact
   only for that discretized recurrence. Neither may relabel unfinished work
   as losing or optimal.
5. **Deadline:** the issue shield consumes only the already required
   all-action local certificate. Optional survival/refinement work publishes
   later on a separate newest-version-wins service; a miss falls back without
   starting cold work on the issue thread.

## Decision Matrix

### Required before every option: repair the issue transaction

- Keep the planned action when its fresh hard certificate remains safe.
- If it is unsafe, intersect fresh prefix-safe actions with the retained
  global allowed set.
- Relax the global mask only when that intersection is empty, and mark
  `viability_constrained=false`,
  `viability_fresh_prefix_relaxed=true`.
- Retain the fresh planned-action certificate, intersection, selected
  certificate, reason, and correct per-action strategy fields.
- Gate on zero silent outside-mask issues, focused deterministic tests, full
  quick suites, replay, then one no-audit Hard Stage-4A trial.

This is a correctness repair, not a strategy experiment.

### Option A — feasibility preservation before loss (recommended)

Build an explicit Hard/route/phase strategy profile that, only inside the
current viable set, prefers:

1. exact continuation-compatible terminal states;
2. larger viable repair volume and reversible interior reserve;
3. the practiced route tube;
4. local risk/position/damage objectives afterward.

Why: the canonical hit entered loss at the left/bottom boundary; boundary
factors occurred on 10/15 focused and 30/39 full-route hits. This option acts
before the state is losing.

Gate: offline same-root safe-action counterfactuals, exact residual-frame
terminal overlap, no fresh-hard regression, then repeated clean focused
trials. The profile is explicit strategy data, not universal mechanics.

### Option B — verified longest-survival fallback after loss

Extend the exact losing-root candidate service to publish per-action partial
survival lower labels and the causal witness, not only full-horizon wins.
Choose lexicographically by fresh local hard certificate, guaranteed survival
frames, bottleneck margin, control reserve, then recovery distance.

Why: 47/61 roots remained losing in every safe comparable variant, and all six
survival labels that reached a later hit disagreed with the issued action.

Gate: explicit augmented root, completed witness, exact version/deadline
match, all-action issue certificate, shadow delivery/contention measurement,
then an opt-in physical trial. Timeout or candidate exhaustion remains
unresolved.

### Option C — adaptive spatial refinement

Refine only queried boundary tubes or candidate action columns when the
16-pixel root is empty and a proof-backed bound says refinement can change the
label. Never solve the full 4-pixel field synchronously.

Why: it repairs real false empties, but only 6/61 in this cohort and costs
about 18x at the median as a full field.

Gate: continuous-position oracle, 8/4-pixel parity, retained witness, strict
deadline, and no effect on authoritative publication latency.

## Recommendation

Execute the required transaction repair first. Then pursue Option A as the
primary route-survival improvement and Option B as the bounded losing-state
fallback. Keep Option C as selective supporting machinery, not the main
planner rewrite.

## Post-Decision Result

The transaction repair passed two complete no-audit Hard Stage-4A physical
gates. Runs `211210` and `212756` retained 4,627 issue transactions with zero
silent outside-global actions and zero Bomb. The second reason-aware audit had
zero intersection, constraint, certificate, selected-strategy, or reason
violations. Local, recertification, and global-solve latency did not regress.
CE-0127/0128 are closed for the current enemy-change issue boundary, so
Option A is now the active design target.

## Option-A First Result

The first implementation placed exact repair volume and delay-scaled
interior reserve into Python/native beam pruning. It is rejected by CE-0129.
A fixed 800-root hit-window replay changed 392 actions and improved repair
volume on 356, but Stage-4A `202439` frame `28412` and `212756` frame `12843`
had worse later terminal hard vectors. The repair score is exact for the
global finite recurrence but is not an admissible bound on local terminal
threat.

The native-v2 experiment was removed and the historical reducer/ABI restored.
The retained default-off form changes only final selection after terminal
scoring. Across the same deterministic reservoir method it changed 7/800
broad actions and 13/800 roots within 300 frames of a hit. Every changed
action kept an equal hard vector and remained inside the global safe set. In
the pre-hit cohort, reserve deficit improved on 11/13 actions and repair
volume on 2/13, with no regressions in either value. Same-root timing and
single-step replay do not establish prevented hits.

This safely establishes a small final-only proposal, not a sufficient
pre-loss solution. The next Option-A algorithm should keep the complete
historical beam as an immutable incumbent and add a bounded supplemental
continuation lane. Final terminal-hard comparison over the union must leave
the historical endpoint available. See
`notes/PRELOSS_CONTINUATION_RESERVE_CONTRACT_20260726.md`.

## Option-A Supplemental Result

The immutable successor is implemented default-off, without a live CLI. It
does not share pruning capacity with the historical beam and cannot remove
its endpoint. A separate width-4 lane changed 286/800 broad and 341/800
pre-hit actions, improving exact repair volume on 273 and 323 and
equal-repair reserve on another 13 and 18. Historical selected-action
identity, effective-global membership, componentwise issue/local/terminal
hard constraints, route deficit, and strict continuation admission had zero
violations. Supplemental median/p95 cost was `2.449/3.114 ms` broad and
`2.425/3.026 ms` pre-hit.

This closes the offline construction gate, not the physical gate. Width 4 is
the only retained candidate because widths 8 and 12 paid larger tails for
small additional coverage. The next Option-A step is direct-root Windows
observe/decode/project/certify/supplemental/issue telemetry under the
four-worker planner workload, with historical fallback and no publication
delay. See
`notes/IMMUTABLE_SUPPLEMENTAL_CONTINUATION_LANE_20260726.md`.
