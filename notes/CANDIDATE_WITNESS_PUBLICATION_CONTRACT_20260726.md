# Candidate Witness Publication Contract

Date: 2026-07-26

Status: implemented as shadow-only telemetry; no input authority

## Question

Can a completed, exact-key candidate-policy lower bound be turned into a
reviewable proposed root action without recomputing on the issue thread or
silently weakening the existing hard certificate?

The answer is conditionally yes for telemetry:

1. the verifier must retain which causal candidate policy attained each root
   action label;
2. the delivered result must match the immutable Boolean policy version and
   full augmented root;
3. the proposed root action must have a fresh, already-computed local hard
   certificate at the one issue where it is published; and
4. the record must expire after that issue.

This checkpoint does **not** give the candidate result control authority.

## Written Problem Contract

### Physical objective

When the Boolean viability set is empty, propose an action that has a
completed attainable 32-frame survival witness and does not violate the
fresh committed-prefix collision certificate. Survival remains the hard
objective; damage, position, items, and score remain subordinate.

### State and observation

The candidate root is

```text
(policy_version,
 layer phase,
 lattice row/column,
 observed active action,
 held/pending command,
 remaining-delay support)
```

The policy may condition only on observations available at its decision
times. Cadence uncertainty is recursively branched over `(4, 5, 6)`, and
indistinguishable delay states are merged by the finite belief recurrence.

### Actions and transition

The root action is unrestricted over the 17 TH08 movement/focus actions. A
candidate then uses one declared stationary continuation action. Selecting
the already-held desired action remains no-write; a new pickup delay is
sampled only for an actual command transition.

### Uncertainty and horizon

- Candidate recurrence: the retained finite clearance volume, recursive
  cadence `(4, 5, 6)`, the policy's delay support, and 32 physical frames.
- Issue certificate: all supported pickup delays, action hold, bullets,
  lasers, and enemy bodies over the existing short committed-prefix
  certificate.
- The finite hazard forecast can still omit or conservatively approximate
  physical births/transforms. A finite-model win is not physical proof.

### Invariants

- A timeout, budget exhaustion, missing/inconsistent witness, stale result,
  key mismatch, deathbomb/dialogue input override, missed deadline, missing
  issue certificate, collision, or negative clearance never publishes an
  issue-eligible record.
- Candidate output never changes `Decision.mask`.
- Candidate labels are never carried across policy versions.
- The publication contains the full root key, policy version, candidate
  witness, label, certificate, valid issue frame, and expiry frame.
- Trace-radius hazards are never used to reconstruct an alternate-action
  certificate.

### Delivery deadline

The publication is valid only for the current `counter_at_action` and expires
after that same issue. It reuses the exact-key background result and the
certificate vector already computed by local planning or issue-time enemy
recertification. A lookup miss never starts synchronous candidate expansion.

## Historical Stage 6B Audit

The retained losing-only v2 run
`lunatic_route2_stage6b_unattended_20260726_011639` contains 941 delivered
full-horizon candidate wins, but its schema retained only the aggregate label,
best-action names, and completed candidate names. It did not retain:

- the root-action-to-candidate witness mapping;
- the issued action's exact candidate label; or
- the alternate-action fresh certificate vector.

The focused pre-hit audit selected 82 winning roots within 120 frames of 17
native contacts. Exact root fields matched in all 82. Current exact replay
reproduced both the historical aggregate label and best-action set in only 47
roots, covering 14 contacts; 35 roots fail closed as
`historical_replay_mismatch`. Current Linux and Windows kernels agreed on the
two focused mismatch probes, so this is not evidence of a current
cross-platform divergence. The old artifact simply does not retain a
content-complete historical solver dependency/output contract.

Within the 47 auditable roots:

- 23 candidate decisions would change the issued action;
- 21 of those change the issued action from a modeled 32-frame loss to a
  modeled 32-frame win;
- all 23 alternate actions lack a retained issue certificate and therefore
  remain unresolved;
- 24 roots issued an action already in the candidate-best set and retained a
  safe selected-action certificate; and
- no delivered winning root was within 32 frames of the next contact.

Therefore the old run supports the hypothesis that candidate witnesses often
improve finite-model feasibility, but it cannot establish that an alternate
candidate action was physically issuable or would have prevented a contact.

Retained report:
`artifacts/viability_audit/stage6b_20260726_011639_candidate_witness_counterfactual.json`.

## Implementation

`CandidateVerifierOutcome` now keeps the completed portfolio's
`CandidateActionWitness` for every root action. Runtime JSON keeps only:

- witnesses for the aggregate best actions; and
- the exact label/witness for the action actually issued.

`Decision` now carries the action certificate tuple already built by local
planning. If enemy geometry changes before issue, the existing issue-time
recertification replaces it with the newly computed all-action tuple.

`_candidate_shadow_publications` intersects these immutable facts. A record is
`issue_eligible` only when:

```text
exact lookup
and status == feasible
and full-horizon positive label
and not stale
and witness label == delivered state label
and witness candidate was completed
and no deathbomb/dialogue input override
and not deadline_missed
and certificate exists
and worst_collisions == 0
and min_clearance >= 0
```

The helper has no input side effect. A 200,000-call synthetic timing probe was
`1.376 us/call` on Linux; no candidate recurrence or hazard geometry is added
to the issue thread. Physical contention still requires measurement because
larger JSON records and certificate-tuple copying are not represented by that
micro-probe.

## Formal Review

### 1. Which physical histories map to one model state?

Histories merge only when they share the immutable policy problem and the
same augmented observed root, including observed action and pending
remaining-delay support. This is the intended finite information state.
Physical histories with unmodeled hazard futures can still merge, so the
result is exact only for the declared finite model.

### 2. Does the recurrence preserve uncertainty and non-anticipativity?

Within that finite model, yes: cadence and hidden remaining-delay branches are
universal, and future maximization occurs after observation-compatible
merging. The stationary continuation policy is causal. Publication does not
branch on a hidden action or delay. The local certificate separately checks
the proposed root action over every supported pickup delay.

### 3. If solved exactly, does it answer the physical decision?

It answers a useful proxy: whether one candidate continuation guarantees 32
finite-model frames and whether its first action is locally certificate-safe
at issue. It does not prove recursive feasibility beyond 32 frames, exact
physical hazard prediction, contact avoidance after the horizon, or global
optimality.

Direction of approximation:

- candidate restriction is conservative relative to unrestricted finite-model
  controller choices;
- finite horizon is unknown-direction relative to indefinite survival;
- forecast/model error is bounded only by retained physical evidence and
  fresh local certification, not by a complete physical proof.

Consequently it remains outside hard action authority.

### 4. Does the implementation solve or bound that recurrence?

The native candidate workspace exactly evaluates each completed declared
stationary policy under the finite belief recurrence. Taking the best
completed witness per root action is an attainable lower bound because the
chosen candidate witness is retained with the public root decision.

The publication helper does not solve another recurrence; it joins the
completed label to the precomputed hard certificate by exact action name and
exact issue. A falsifying counterexample is any record marked
`issue_eligible` with a missing/mismatched root, non-best or incomplete
witness, missed deadline, collision, or negative clearance. Unit regressions
cover missing, unsafe, and expired certificates.

### 5. Can it be delivered before issue without changing modeled state?

The join is lookup-only and microsecond-scale in isolation. No cold workspace
is created. However physical acceptance requires a new shadow run that
measures iteration time, action lag, JSON cost, exact publication hit rate,
and CPU contention. Until then, publication remains observation only.

## Decision And Next Gate

Keep the existing controller authoritative. Run a fresh non-Stage-6B physical
shadow after Linux and Windows quick-suite parity. The next report must
separate:

- delivered candidate wins;
- exact best witnesses;
- alternate actions with safe/unsafe/missing issue certificates;
- one-shot deadline rejection;
- modeled feasibility gain over the issued action;
- publication construction/serialization cost; and
- full iteration/action-lag deltas against an uncontended baseline.

Only after repeated clean evidence may a separate experiment allow a
candidate action to enter the local choice set, still behind the fresh hard
certificate and with an immediate Boolean/local fallback.

Checkpoint validation: Linux and Windows complete quick suites both pass 487
tests in `2.210/5.092 s`.
