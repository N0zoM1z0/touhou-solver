# TH08 Solver Strategy Ledger

This file records which control strategies have been tried, what they were
trying to solve, and why they are live, shadow-only, rejected, or still only a
hypothesis. It is an index, not a replacement for the detailed design notes,
counterexamples, run dossiers, or `notes/RESEARCH_LOG.md`.

Last updated: 2026-07-25.

## Status Vocabulary

- **Live:** permitted to affect physical gameplay under the stated gate.
- **Shadow:** computed or replayed for telemetry, but cannot rank live input.
- **Rejected live:** evidence falsified the current live form. Code may remain
  as an offline oracle, but reactivation requires the listed new evidence.
- **Hypothesis:** plausible and worth testing, but not yet implemented or
  supported by causal physical evidence.
- **Infrastructure:** necessary sensing, timing, or validation machinery; it
  is not itself a winning gameplay strategy.

The ordering contract is unchanged:

```text
native collision avoidance
  -> issue-time/delay certificate
  -> finite-horizon survival viability
  -> damage and phase completion
  -> power/items/score/graze/position
```

Damage is important, but it is never permission to select an action outside
the currently certified viable set. The default physical-practice policy is
hard no-Bomb.

## Current Decision

The live controller remains on the verified coarse Boolean viability path.
Losing-state labels are now computed only after Boolean publication and, when
explicitly enabled, on an independent single-worker shadow executor. This
repairs the publication/expiry regression but does not authorize the labels:
two Stage-5 traces show that exact layer phase, game-observed active input,
and pending-command remaining delay materially change state classification
and best-action sets. Exact-root frontier work has now validated a
lookup-only, phase-sharded prewarm decomposition offline, but its physical
shadow regressed controller latency/action lag and its one-transition value
was then disproved as a complete physical model. The old prewarm remains
rejected. A recursively variable-cadence belief solver now passes
scalar/native differentials offline; its conservative
all-root/focused-continuation policy class is a research candidate, not live
authority.

The next architectural target is a delivery-aware solver:

1. a fresh, bounded-cost issue-time shield certifies the action actually sent;
2. the background planner publishes only versioned policies whose hazard
   coverage and service deadline are valid;
3. event-complete ECL/timeline birth and transform forecasts make the future
   model less stale;
4. longer-horizon objectives, including boss damage, rank only actions that
   survive those gates.

## Strategy History

### S01 — Reactive Local Dodge With Emergency Deathbomb

- **Status:** Rejected live as an acceptance strategy.
- **Intent:** Use short-horizon native bullet/laser avoidance and spend a Bomb
  when the native predeath/deathbomb state says collision is imminent.
- **Observed result:** The first complete Lunatic Final-B run reached the end
  with 91 native hits and requested a deathbomb at 62 hit edges. Patched death
  recovery allowed repeated resource resets, so the observed 98 Bomb-unit
  spend was not a feasible route budget.
- **Failure mode:** Bomb invulnerability, bullet cancellation, resource
  mutation, and respawn changed the state being diagnosed. The strategy hid
  planning failures instead of proving survival.
- **Replacement:** Hard no-Bomb physical practice, adopted on 2026-07-23.
- **Reactivation gate:** Bomb may enter a future resource-aware planner only
  when the no-Bomb viability set is empty and the finite stock is modeled
  across the complete route. Deathbomb is not a default fallback.
- **Evidence:** `notes/RESEARCH_LOG.md` sections “First Complete
  Sakuya/Remilia Lunatic Final-B Run” and “THPRAC Stage Isolation And Hard
  No-Bomb Policy”.

### S02 — Forward Corridor Waypoints And Gate Commitment

- **Status:** Live only as macro guidance; not a survival certificate.
- **Intent:** Keep the player in a long-horizon connected corridor and commit
  to a bottleneck component instead of greedily maximizing immediate
  clearance.
- **Observed result:** It fixed specific gate reversals and made asynchronous
  macro structure queryable, but the first complete run missed a corridor
  deadline at 74/91 hits. A lane label could also alias different path
  branches.
- **Failure mode:** One optimistic forward path cannot establish that future
  escape remains controllable. A stale waypoint has no action-level safety
  meaning.
- **Current gate:** Corridor targets are subordinate to fresh local collision
  and robust-prefix checks.
- **Evidence:** `notes/ROBUST_VIABILITY.md` and the 2026-07-23 complete-run
  sections in `notes/RESEARCH_LOG.md`.

### S03 — Dynamic Action Hold And Adaptive Delay Support

- **Status:** Live.
- **Intent:** Separate controller cadence from actuation pickup and certify
  candidate actions against the observed distribution of delays rather than a
  single guessed scalar.
- **Observed result:** Dynamic hold reduced the Stage-3 experiment from ten to
  eight hits and spell-50 from five to one under different RNG. A later scalar
  delay experiment regressed to eleven hits, motivating discrete robust
  support. The game-neutral delay estimator now records visible pickup,
  computation, censored commands, overruns, and a guarded support.
- **Limitation:** A delay certificate is only as sound as the hazard snapshot.
  It cannot cover a bullet or enemy born after that snapshot. The estimator
  now exposes one unseen desired command and remaining-delay support, but the
  live dense viability recurrence does not yet include that state.
- **Evidence:** `notes/RESEARCH_LOG.md` sections “Dynamic-Hold Physical Run And
  Actuation Split”, “Scalar Delay Rejection And Adaptive Robust Control”, and
  “Adaptive Robust Stage-3 Physical Acceptance”.

### S04 — Robust Backward Viability

- **Status:** Live coarse Boolean baseline.
- **Intent:** Preserve the set of states with an action that is safe for every
  modeled delay branch over the finite horizon.
- **Observed result:** The native Boolean recurrence has NumPy/scalar parity
  and gives an explicit safe-action set instead of one waypoint. It also
  exposes widespread kernel exhaustion before physical hits.
- **Limitation:** The current 16-pixel, eight-frame lattice and instant-safe
  terminal layer are approximations. More importantly, the policy is computed
  from a forecasted snapshot that may omit later births or mode changes.
- **Current gate:** It may constrain live actions only while its context,
  delay support, horizon, and version are valid; a fresh local certificate
  still dominates it.
- **Evidence:** `notes/ROBUST_VIABILITY.md` and
  `notes/VERSIONED_REACH_AVOID_ARCHITECTURE.md`.

### S05 — Empty-Kernel Endpoint Recovery And Boundary Reserve

- **Status:** Limited live fallback; not a certificate.
- **Intent:** When the Boolean kernel is already empty, prefer actions whose
  delay branches end nearer a later viable set and preserve room to reverse.
- **Observed result:** Cross-stage replay found useful recovery guidance, but
  scalar endpoint distance does not prove a safe bridge. CE-0089 also showed
  that letting a soft reserve enter beam pruning before hard delay
  certificates can erase safer first actions. The 2026-07-25 Stage-5 audit
  found the converse gap after the Boolean kernel became empty: repair-volume
  guidance disabled boundary reserve entirely. At canonical decision 1,680,
  the fallback chose `down_right_fast` outside the 74-frame survival-best
  mask with a 24-pixel diagnostic reserve deficit.
- **Failure mode:** It optimizes an endpoint without representing every
  intermediate state. Hard-before-soft ordering is enforced at pruning and
  selection, but the live losing-state order still lacks guaranteed survival
  horizon and does not apply reserve to repair-neighborhood states.
- **Current shadow:** A default-off `losing_control_reserve` switch applies
  delay-scaled reserve to repair/survival states only after fresh hard-vector
  equivalence. Reserve-only replay improved 13/195 measured deficits and
  regressed zero; it has no physical authority.
- **Reactivation/upgrade gate:** Replace endpoint distance with a
  time-expanded robust survival/recovery band that has scalar-oracle parity,
  meets the delivery budget, and does not worsen hard-vector counts on
  retained cross-stage rows.
- **Evidence:** `notes/ALGORITHM_REVIEW_20260724.md` and
  `notes/LOSING_STATE_ROOT_CAUSE_20260725.md`.

### S06 — Max-Min Safety Value

- **Status:** Rejected live; retained as an offline oracle.
- **Intent:** Rank already-losing states by their best robust bottleneck
  clearance while exactly preserving Boolean threshold sets.
- **Observed result:** The native recurrence passed scalar parity, but the
  Stage-3 live experiment recorded 15 hits, the worst of seven retained
  complete Stage-3 attempts. It added about 50 ms to the background solve and
  widened local/control latency tails. Paired replay did not prove that its
  ranking itself caused collisions.
- **Failure mode:** Correct labels inside a frozen model were promoted without
  an end-to-end delivery budget.
- **Reactivation gate:** A packed/query-local implementation must meet the
  live service deadline and repeated physical A/B must separate compute
  contention from ranking quality.
- **Evidence:** `notes/ROBUST_VIABILITY.md` section “Threshold-Free Max-Min
  Safety Value”.

### S07 — Observation-Complete, Versioned Safety Transaction

- **Status:** Live infrastructure; incomplete for future projectile births.
- **Intent:** Treat observe-plan-act as a versioned transaction. Re-read
  lightweight native state immediately before input and recertify when
  relevant geometry changes.
- **Observed result:** CE-0092 found an 18-body ring born during local
  planning. Synchronous enemy-prefix reads and issue recertification remove
  that specific stale-snapshot authority. Separate work recovered Reisen's
  boss slot outside the nominal enemy pool, latent contact modes, and
  world-position motion.
- **Limitation:** Current issue checks do not yet cover every bullet/laser
  birth. Holding the previous action after abort is also not a proof of
  survival.
- **Next gate:** Packed native decode + project + all-action issue-time
  certificate, plus ECL/timeline `BirthWindow` coverage.
- **Evidence:** `notes/VERSIONED_REACH_AVOID_ARCHITECTURE.md`.

### S08 — Item, Power, Score, And Graze Objectives

- **Status:** Disabled for current survival acceptance.
- **Intent:** Improve route resources and score inside the viable set.
- **Observed result:** Residual item potential helped reinforce a climb into a
  newly active boss body, and raw item values could dominate conservative
  position cost.
- **Failure mode:** The hazard and viability layers are not yet reliable
  enough to certify that a pickup is safe. Passive collection remains
  measured but cannot prune or rank actions.
- **Reactivation gate:** Only actions already equivalent under fresh survival
  certificates may be separated by resource utility.
- **Evidence:** `notes/ALGORITHM_REVIEW_20260724.md` and CE-0090.

### S09 — Full-Horizon Fine Refinement And Fused Survival Labels

- **Status:** Rejected live on 2026-07-24; retained shadow/offline.
- **Intent:** Recover coarse false-empty states with an 8-pixel lattice and,
  when no winning state exists, choose the action with the longest guaranteed
  modeled survival horizon.
- **Observed offline result:** Exact Stage-5 capsule replay recovered all
  three CE-0100 coarse false-empty witnesses. Fused survival labels have
  independent scalar parity and correct CE-0101's endpoint-ranking
  counterexample.
- **Observed physical result:** The Stage-4A trial
  `lunatic_route2_stage4a_unattended_20260724_220032` recorded 40 hits versus
  26 in the comparison run. Global solve median/p95 rose from
  170.77/380.59 ms to 532.04/1174.21 ms; unique delivered policies fell from
  1,728 to 630; expired decisions rose from 34 to 178. Empty queries fell, but
  the delivered controller became substantially staler.
- **New shadow evidence:** Exact reconstruction matched all 272 stratified
  Stage-5 queries; 195 were base-empty. Survival-first replay changed 42/195
  actions, increased survival-best membership from 134 to 175, and caused
  zero fresh local hard-vector regressions. Canonical decision 1,680 changed
  from `down_right_fast` to `stay`. On 48 exact capsules, Boolean/fused viable
  arrays and action masks matched, but whole-solve median/p95 was
  `76.96/197.99` versus `125.31/229.58 ms`. Producing the label inline would
  still delay Boolean publication.
- **Boolean-first correction:** The Boolean policy now publishes before an
  optional labels-only recurrence. A serialized Stage-5 shadow run raised
  expired decisions `14 -> 34`; a separate-executor, one-label-worker run
  restored expiry to 15 with first policy age `4/10` frames and query age
  `11/27`, matching the Boolean-only delivery envelope. Label computation
  itself moved to `150.43/284.57 ms` median/p95 and remained non-authoritative.
- **Pending-pipeline rejection of dense authority:** In two complete Stage-5
  shadows, issued desired input differed from native active input on
  `754/8077` and `805/7772` Boolean queries. Among labeled queries this changed
  winning/losing classification nine times in each run. Two deterministic
  16-query exact cohorts changed best-action sets 13 times each when the
  older pending command and remaining delay were added; winning classification
  changed 4 and 6 times.
- **Sparse augmented prototype:** A versioned C++ reachable-tube workspace now
  preserves exact frame/observed/pending/remaining-delay state and full root
  action labels. It passed 512 scalar differentials and ten full TH08-size v1
  differentials with zero failures. TH08 query median/p95 changed from
  `819.90/986.61 ms` for independent v1 cold queries to
  `38.76/104.46 ms` for cold/incremental workspace roots; an identical warm
  root measured `0.103/0.128 ms`. This accepts the pruning recurrence, not
  issue-time delivery: cold p95 remains outside the live control budget.
- **Exact-root frontier prototype:** The issued action is now lowered into a
  deduplicated set of next roots over command delay and an experimental
  `(4,5,6)` next-decision support. A public root may robustly branch over that
  cadence once while fixed-eight-frame continuation remains explicit; this is
  not a full variable-cadence certificate. Across 512 scalar differentials
  and 70 TH08-shaped exact roots, native results had zero failures. Three
  phase shards reduced post-issue frontier wall time to
  `39.61/49.35/62.50 ms` median/p95/max and lookup-only consumption to
  `0.061/0.100/0.143 ms`. Phase seed wall remained
  `112.51/122.02/140.69 ms`, so a seed started only at issue time is too late.
- **Cancellable rolling prototype:** A bounded newest-version scheduler now
  uses native cooperative cancellation/deadlines, a fresh executor per
  immutable policy, exact continuation-memo merge, and lookup-only
  specialization. Across 256 scheduler/scalar differentials and 25
  TH08-shaped rolling decisions, labels had zero failures and specialization
  added zero continuation states. Full preparation plus seed plus
  specialization measured `59.13/228.99/295.90 ms` median/p95/max; exact
  lookup measured `0.066/0.135/0.445 ms`. The first two decisions of every
  fresh policy missed a four-frame budget, decision three passed 4/5, and
  decisions four/five passed 10/10. Five stale replacements completed in
  `5.27/5.35/6.31 ms`, and old results were never consumable.
- **Physical prewarm rejection:** Complete Stage-5 no-shadow/full-frontier/
  top-2-shadow runs recorded iteration medians `45.63/71.82/65.98 ms`,
  local-plan medians `20.35/30.83/29.22 ms`, and action-lag medians
  `2/4/3` frames. Top-2 raised exact-root hits from `4.49%` to `12.47%` but
  did not restore the clean controller budget. RNG-distinct hit totals
  `14/32/27` are adverse, not causal, evidence.
- **Formal correctness rejection:** CE-0114 shows the legacy recurrence
  mistakes hold/no-write for a newly delayed command; an isolated 128-case
  cohort produced 30 winning errors. Corrected CE-0111 shows
  one-transition cadence can report a full win when recursive cadence loses
  one frame. CE-0112 shows exact hidden remaining delay can add a false best
  action. Therefore the legacy value has unknown error direction and is not an
  upper or lower bound.
- **Belief-state replacement candidate:** The new scalar/native recurrence
  implements conditional issue/no-write, branches cadence recursively, and
  merges remaining-delay supports by next observation. Native parity passes
  another 128 retained cases. On a
  TH08-shaped 32-frame `(4,5,6)` workload, unrestricted 17-action continuation
  took `1507.74 ms`; all 17 root actions with nine focused continuation
  actions took `29.52 ms`. The latter is a conservative attainable policy
  class, not unrestricted optimality. Wide recursive `(2..9)` cadence remains
  outside budget.
- **Budgeted anytime refinement:** Future fast actions may now be used at most
  `B` decision epochs per history while every public root still evaluates all
  17 actions. This gives proved nested attainable lower bounds
  `L_0 <= L_1 <= ... <= V_unrestricted`; sufficiently large `B` recovers the
  unrestricted finite model. A native revealed-delay information relaxation
  is a proved upper bound and passes independent scalar parity. On the
  retained structured workload `L_0` equals that upper label, so it certifies
  the unrestricted state value for that instance. One workspace incrementally
  solved `B=0/1/2` in `32.30/687.54/1054.42 ms`; the complete upper costs
  `1471.15 ms`.
- **Incumbent-seeded selective upper certification:** The native threshold
  recurrence now asks only which optimistic root actions can strictly beat a
  completed attainable lower label. It preserves controller/nature
  quantifiers and revealed observation merging, and reports unresolved
  actions rather than incomplete upper labels. Across 128 deterministic
  finite games its unresolved mask exactly matches the independent complete
  scalar upper. On the current retained structured workload `L_0` costs
  `29.96 ms`, certification costs `0.047 ms`, and all 17 optimistic actions are certified
  unable to beat `L_0`; the old complete upper cost about `1.5 s`.
  Fresh Stage 6B capsules expose the nontrivial tail: an uncapped 32-root
  cohort certified 31 roots but took as much as `1907.33 ms`; one root
  retained eight unresolved actions. The 100-ms anytime contract certified
  29 roots, retained the same eight-action gap, and conservatively returned
  all 17 actions unresolved on two deadline roots. **Status remains
  offline/shadow-only.**
- **Resumable threshold service:** Exact-root threshold memo and root-action
  proof states now survive repeated calls only for the same immutable version,
  canonical root, and bit-identical lower target. On a deterministic hard
  root, five repetitions completed in 21--23 5-ms slices with exact final
  eight-action mask parity; total median was `112.92 ms` versus `109.39 ms`
  one-shot. Fresh restarts spent the same service time but stayed at all 17
  actions unresolved. This solves bounded service delivery for a sufficiently
  long-lived root, not cross-version cold start, total CPU, or the remaining
  lower/upper gap. **Status remains offline/shadow-only.** The next
  algorithmic gate is targeted lower refinement only for unresolved actions
  plus earlier losing-state prevention, not blind budget widening or
  synchronous complete upper.
- **Feasibility-first candidate synthesis:** Exact stationary continuation
  portfolios now answer the cheaper question first: whether any causal policy
  survives the finite horizon. On retained structured seeds 0/3 the first
  full-horizon witness costs median `4.01/1.90 ms`. Seed 0 previously cost
  `733.42 ms` for the nine-action lower and `4379.39 ms` for unrestricted
  exact belief. If optimality is requested, the unresolved upper action and a
  worst restricted path propose new action columns; every proposal is
  re-solved exactly before it raises the lower. The three-column seed-0 class
  reaches the exact unrestricted label in median `287.64 ms`. A
  previous-version candidate ranking may reduce current-version cold start,
  but every label is recomputed: one changed-clearance root improved
  `3.980 -> 2.200 ms` median with full-portfolio order invariance.
  Remaining-delay bucket upper bounds pass nested scalar/native parity but
  did not reduce the hard first-upper cost. **Status remains
  offline/shadow-only.** The next gate is retained Stage-6B capsule replay and
  whole-controller contention/delivery, not another unrestricted synchronous
  solve.
- **Stage 6B physical counterexample:** Instrumented hard-no-Bomb run
  `lunatic_route2_stage6b_unattended_20260725_204521` completed with 31 hits
  versus 27 in the RNG-distinct comparison. Global solve median improved
  `266.80 -> 97.41 ms` and clearance median `118.55 -> 13.72 ms`, but
  `7213/15149` available queries had an empty action set and every hit was
  attributed to prior global-kernel exhaustion. Performance gains therefore
  generalize beyond Stage 5, while survival acceptance does not.
- **Failure mode:** Uniform full-field refinement was called “adaptive” even
  though it recomputed an entire fine horizon after a coarse empty source.
  More precise labels for a frozen hazard snapshot were allowed to control
  after their delivery relevance had decayed. Dense labels also use a
  source-layer state without the exact observed/pending input pipeline.
- **Reactivation gate:** First establish a verified cadence scheduler or
  bounded cadence automaton and validate the held-desired/pending estimator
  invariant, then measure conservative policy-class lower bounds and the
  selective clairvoyant-upper certificate on retained cross-stage capsules.
  Only a
  non-clairvoyant no-write belief value with an explicit
  policy-class/horizon claim may be delivered.
  Offline evidence must predict no CPU/read/local-plan/action-lag regression
  before another physical shadow. Same-recurrence parity, top-K root coverage,
  and warm lookup speed are insufficient.
- **Evidence:** `notes/STAGE5_VIABILITY_DIFFERENTIAL_AUDIT_20260724.md`,
  `notes/LOSING_STATE_ROOT_CAUSE_20260725.md`,
  `notes/BOOLEAN_FIRST_PENDING_PIPELINE_20260725.md`,
  `notes/AUGMENTED_PIPELINE_REACHABLE_TUBE_20260725.md`,
  `notes/EXACT_ROOT_FRONTIER_PREWARM_20260725.md`,
  `notes/ROLLING_PIPELINE_PREWARM_20260725.md`,
  `notes/AUGMENTED_PIPELINE_ROBUST_CONTROL_FORMALIZATION_20260725.md`,
  `notes/BUDGETED_BELIEF_REFINEMENT_20260725.md`,
  `notes/RESUMABLE_INCUMBENT_CERTIFICATION_20260725.md`,
  `notes/ANYTIME_DUAL_BOUND_POLICY_SYNTHESIS_20260725.md`,
  `notes/BELIEF_PIPELINE_CORRECTNESS_AND_PERFORMANCE_20260725.md`,
  `artifacts/benchmarks/augmented_pipeline_workspace_20260725.json`,
  `artifacts/benchmarks/exact_root_frontier_20260725.json`,
  `artifacts/benchmarks/rolling_pipeline_prewarm_20260725.json`,
  `artifacts/benchmarks/belief_pipeline_workspace_20260725.json`,
  `artifacts/benchmarks/budgeted_belief_refinement_20260725.json`,
  `artifacts/benchmarks/resumable_upper_certification_20260725.json`,
  `artifacts/benchmarks/dual_bound_policy_synthesis_20260725.json`,
  `artifacts/benchmarks/upper_hierarchy_cross_version_20260725.json`,
  `artifacts/viability_audit/pipeline_formal_correctness_20260725.json`,
  `artifacts/viability_audit/stage5_20260724_201636_adaptive_replay.json`, and
  the retained Stage-4A/Stage-5 run dossiers.

### S10 — Damage-Aware Phase Completion

- **Status:** Native telemetry and safe-set shadow are live infrastructure;
  Boss-x alignment is rejected live. Exact shot-model planning remains a
  hypothesis.
- **Intent:** Among actions that are already survival-equivalent, maximize
  expected player-shot damage or minimize robust time-to-phase-completion.
  Ending a boss phase earlier can prevent exposure to its later, denser
  pattern, so “survive the next horizon” and “survive the route” are not the
  same objective.
- **Observed facts supporting investigation:**
  - The live controller already keeps Shot in normal decision masks.
  - Its local terminal position cost prefers bottom-center or a corridor
    waypoint; it does not use boss HP, damage rate, shot cadence, option
    geometry, damageability, or remaining phase time.
  - Recovered route-2 SHT data show that full-power Sakuya and Remilia fire
    narrow upward/spread lanes. Horizontal alignment with a damageable boss
    can therefore change realized DPS.
  - `notes/HAZARD_ORACLE_AND_ADAPTIVE_VIABILITY.md` already identifies boss
    HP, damage rate, shot state, and phase timers as missing phase state.
- **Initial shadow audit:** In the two retained Stage-4A traces, Shot appears
  in 97.38--97.78 percent of output decisions and 97.39--97.66 percent of
  observed active input, but normal-phase horizontal owner alignment varies
  sharply. Some phases spend under 20 percent of measured rows within 48
  pixels. All measured spell spans are roughly 2,808--3,229 frames while
  post-hit Power is commonly near zero. These observations motivate HP
  telemetry but do not prove that an alignment action increases damage.
- **Observed native experiment:** Stable registry/HP/timer telemetry was
  physically validated on Stage 4A. For spell 57, the shadow capture recorded
  873 stable Boss samples and the explicit alignment experiment recorded 906;
  every sample had an open native damage gate. Live alignment changed 123
  actions and improved normal horizontal-error median
  `51.50 -> 25.19 px`, but observed HP rate was adverse
  `0.47597 -> 0.37837 HP/frame` even though measured Power was higher in the
  alignment run. The shadow capture ended manually at timer 2729/3000, while
  the live capture reached 2996/3000, so this is not a phase-duration A/B and
  is not a causal estimate.
- **Decision:** Runtime live alignment authority and its CLI switch were
  removed. Native HP/phase telemetry and the hard-safe shadow selector remain.
  The next experiment must use the existing executable SHT/option/cadence
  model and validate predicted damage against native HP delta.
- **Confounders:** The no-life-decrement discovery runs still lose Power after
  hits, use different RNG/respawn histories, and may time out phases. Aggregate
  phase length or hit count cannot by itself prove a damage benefit.
- **Next experiment:**
  1. read or reconstruct native player-shot cadence and option state;
  2. project the decoded Power-dependent SHT records through the existing
     executable shot collision/damage model;
  3. report predicted versus native HP delta by Power/focus/Boss motion;
  4. shadow-rank only actions in the same fresh collision, delay, and viability
     set;
  5. require repeated focused A/B and a second stage before live promotion.
- **Rejection condition:** If HP-delta prediction lacks runtime parity, if the
  objective changes any action across a hard safety boundary, or if phase time
  falls without a repeated survival improvement, keep it shadow-only.
- **Artifact:** `artifacts/strategy/stage4a_attack_alignment_20260724.json`,
  plus `stage4a_boss_phase_shadow_20260724.json` and
  `stage4a_boss_phase_live_20260724.json`, generated by
  `scripts/analysis/th08_attack_alignment_audit.py`.

### S11 — Delivery-Aware Hierarchical Planning

- **Status:** Proposed next architecture.
- **Intent:** Optimize the policy that can be delivered before its assumptions
  expire, not the most detailed solution of an old snapshot.
- **Model:** A fresh issue-time shield owns immediate authority; an anytime
  background planner supplies topology/invariant tubes and publishes only with
  a validity certificate; event forecasts cover future births; damage and
  other progress objectives operate inside the resulting set.
- **Success gates:** Whole-pipeline p95, policy age/expiry, issue-time action
  parity, cross-stage hard-vector counts, adversarial scalar parity, and
  repeated physical focused passes. No single-stage hit-count delta is enough.
- **Evidence:** The physical rejection of S09 and
  `notes/VERSIONED_REACH_AVOID_ARCHITECTURE.md`.

### S12 — Route/Stage/Phase-Conditioned Practiced Profiles

- **Status:** Accepted architecture; profile data and live selection are not
  yet implemented.
- **Intent:** Preserve a reusable mechanics/safety engine while allowing the
  macro strategy to be specialized to game, team, difficulty, stage, phase,
  timer/event window, and resource state—the agent equivalent of a practiced
  route.
- **Model:** A profile may provide a timed reference tube, event-relative lead,
  grid/horizon/cadence, resource floors, exact damage adapter, pickup windows,
  and objective order. It may not alter native collision semantics or select
  outside the fresh viable and issue-safe action set.
- **Why this changed:** Current process-wide constants include local/global
  horizons, lattice resolution, corridor lead/commit, boundary reserve, and
  disabled item policy. The Boss experiment showed that one generic geometric
  proxy can improve its own metric while worsening the native quantity it was
  meant to represent.
- **Tuning gate:** Fit on multiple RNG/entry-resource samples, validate on
  held-out samples and repeated physical captures, retain adverse evidence,
  and compare native survival, HP, Power, exit cause, and policy freshness.
  One stage-specific profile is expected; a hidden stage conditional inside
  the safety kernel is not.
- **Evidence:** `notes/ROUTE_CONDITIONED_STRATEGY_ARCHITECTURE_20260724.md`.

## How To Add A Strategy

Every new entry must state:

1. what failure it is intended to solve;
2. whether it is live, shadow, rejected, hypothesis, or infrastructure;
3. which hard constraints dominate it;
4. the smallest differential/offline gate;
5. the physical acceptance workload and comparison limitations;
6. what evidence would reject it or permit it to become live;
7. links to counterexamples, artifacts, and detailed notes.

Do not rename a failed strategy and retry it with new weights. Explain which
assumption, algorithm, model, or delivery boundary changed.
