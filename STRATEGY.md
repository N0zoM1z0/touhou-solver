# TH08 Solver Strategy Ledger

This file records which control strategies have been tried, what they were
trying to solve, and why they are live, shadow-only, rejected, or still only a
hypothesis. It is an index, not a replacement for the detailed design notes,
counterexamples, run dossiers, or `notes/RESEARCH_LOG.md`.

Last updated: 2026-07-24.

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

The live controller is being returned to the last verified coarse Boolean
viability path. Full-horizon 8-pixel refinement and fused losing-state
survival labels remain shadow/offline only after the Stage-4A experiment
increased policy latency and staleness.

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
  It cannot cover a bullet or enemy born after that snapshot.
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
  certificates can erase safer first actions.
- **Failure mode:** It optimizes an endpoint without representing every
  intermediate state. Hard-before-soft ordering is now enforced at pruning
  and selection.
- **Reactivation/upgrade gate:** Replace endpoint distance with a
  time-expanded robust recovery band that has scalar-oracle parity and does
  not worsen hard-vector counts on retained cross-stage rows.
- **Evidence:** `notes/ALGORITHM_REVIEW_20260724.md`.

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
- **Failure mode:** Uniform full-field refinement was called “adaptive” even
  though it recomputed an entire fine horizon after a coarse empty source.
  More precise labels for a frozen hazard snapshot were allowed to control
  after their delivery relevance had decayed.
- **Reactivation gate:** Query-local/reachable-tube refinement with a hard
  service budget; shadow evidence must show useful action changes at issue
  time without increasing policy expiry or local latency. Scalar parity alone
  is insufficient.
- **Evidence:** `notes/STAGE5_VIABILITY_DIFFERENTIAL_AUDIT_20260724.md`,
  `artifacts/viability_audit/stage5_20260724_201636_adaptive_replay.json`, and
  the retained Stage-4A run dossier.

### S10 — Damage-Aware Phase Completion

- **Status:** Hypothesis; no live authority.
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
- **Confounders:** The no-life-decrement discovery runs still lose Power after
  hits, use different RNG/respawn histories, and may time out phases. Aggregate
  phase length or hit count cannot by itself prove a damage benefit.
- **First experiment:**
  1. add read-only native telemetry for boss current HP, next HP threshold,
     damageable/immunity flags, phase timer/timeout, shot cadence, and observed
     per-frame HP delta;
  2. build a TH08 attack adapter that projects SHT/option shot coverage and
     exposes a game-neutral `phase_progress` utility;
  3. replay retained traces in shadow and report missed safe-DPS opportunity,
     predicted versus observed HP delta, and estimated exposure frames saved;
  4. allow damage to break ties only between actions with the same fresh
     collision, delay, and viability certificate;
  5. physically A/B one focused boss phase, then a different stage, before any
     route-wide claim.
- **Rejection condition:** If HP-delta prediction lacks runtime parity, if the
  objective changes any action across a hard safety boundary, or if phase time
  falls without a repeated survival improvement, keep it shadow-only.
- **Artifact:** `artifacts/strategy/stage4a_attack_alignment_20260724.json`,
  generated by `scripts/th08_attack_alignment_audit.py`.

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
