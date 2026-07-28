# G3/G4 First-Loss Capsule Experiment Contract

Date: 2026-07-28

Status: Stage-5 finite-model gate complete; physical promotion rejected
because first-successor future-hazard coverage is unknown.

This contract follows CE-0158. Lunatic Stage-5 run
`lunatic_route2_stage5_unattended_20260728_124930` enters the loss episode
containing its canonical first hit at decision frame 2049 and contacts a
bullet at frame 2167. Earlier short empty episodes recover. That run did not
enable `--viability-audit`; its trace contains
the canonical query identity but not the complete lowered hazard slab.
Therefore the frame-2049 finite problem cannot be reconstructed exactly from
that trace.

The next physical workload may collect ignored diagnostic capsules. Capsule
I/O is explicit experiment contamination: the run cannot be used to close or
reopen B4, compare controller timing, or promote a live strategy.

## Physical Question

For the loss episode containing the canonical first native hit in one
gameplay epoch, select its uninterrupted exact queried winning-to-losing
bracket and ask:

1. which exact root actions have completed attainable stationary survival
   witnesses at the last viable root;
2. which exact root actions retain completed positive survival prefixes at
   the first losing root; and
3. did the action actually issued belong to the best set of either restricted
   portfolio?

This separates two questions:

- **G4 / preserve feasibility earlier:** evidence at the last exact viable
  root; and
- **G3 / survive after finite-model loss:** evidence at the first exact losing
  root.

Neither result estimates a route clear rate. Later deaths remain discovery
evidence rather than fresh independent trials.

## Problem Contract

### Physical objective

Hard no-Bomb survival for Sakuya/Remilia on Lunatic and Extra. The immediate
experiment is a Stage-5 workload chosen from CE-0158; stage identity is not a
planner identity.

### State and observations

Each audited root is the immutable join of:

- gameplay epoch, stage route index, spell, manager frame, query frame, and
  target frame;
- float32 player-position bits;
- complete supported, active, held-desired, and optional pending input masks;
- remaining-delay information-set support;
- observation, hazard, policy, model, and clock versions;
- hazard-coverage record rooted at the same query frame; and
- one versioned viability capsule containing the already-lowered neutral
  AABB, piecewise-AABB, segment, and packed-segment hazards.

The identity digest, query frame, coverage root, capsule metadata, capsule
basename, file existence, and file hash are checked before solving.

### Actions and actual issue semantics

Every TH08 no-Bomb complete-mask root action is evaluated. Root actions are
not proposal-pruned. A selected mask equal to the held complete mask is
no-write and preserves/decrements a pending command according to the scalar
belief recurrence. Bomb bit `0x02` is absent from the action alphabet.

The historical issued mask is recorded only for comparison. Offline witnesses
never emit input.

### Uncertainty and transitions

The recurrence retains the root's active/held/pending state, remaining-delay
belief, and the declared recursive decision-frame support. Hidden branches
that produce the same observation are merged before the next controller
choice. The independent Python scalar belief recurrence remains the oracle;
native extraction is a parity check, not the oracle.

### Horizon and restricted policy class

The first implementation uses a declared finite horizon, initially 32 frames.
For each unrestricted root action it completes every declared stationary
complete-mask continuation candidate. This is a causal,
observation-compatible restricted policy class and an attainable lower bound.
It is not unrestricted optimality or an unrestricted losing certificate.

Unvisited, malformed, timed-out, unsupported, or cancelled work is
unresolved. The implementation must not convert it to zero survival.

### Safety invariants

- current-state collision returns zero;
- all 36 no-Bomb root actions are present in canonical order;
- every published action has a completed worst observation-compatible branch;
- replay of that branch equals the published label;
- Python/native labels agree per root action;
- finite margins and immutable problem/portfolio digests are retained; and
- future-hazard coverage status is reported separately from finite-model
  exactness.

### Computation, publication, and fallback

This program is offline. It has no issue deadline and publishes only a compact
deterministic report. Live control remains the current Boolean policy plus
fresh local certificate and existing fallback. No cold solve, lookup, or
capsule write is added to the issue thread by this checkpoint.

## Exact Bracket Selection

Decision rows are processed in trace order. The canonical target is the first
row with `hit_started == true` in the requested gameplay epoch/stage. Earlier
losing episodes that return to an explicit viable state are counted and
discarded. The transition whose losing state persists through the target hit
is eligible only when:

1. both rows are in the same gameplay epoch and stage route index;
2. both viability queries explicitly report `available == true`;
3. the earlier exact root reports `state_viable == true`;
4. the next eligible exact root reports `state_viable == false`, and all
   subsequent queried states through the target hit remain explicitly losing;
5. both rows have an available canonical complete-mask root and an audit
   capsule; and
6. no unavailable query, missing capsule, unavailable canonical root,
   malformed identity, root-frame mismatch, or parse failure occurs between
   them.

Any such interruption resets the viable predecessor. A timeout,
`pending_future_epoch`, expired policy, absent query, or missing capsule is
not a finite-model loss. If the loss episode active at the target hit lacks
exact root evidence, the result is unresolved; a different episode may not
silently replace it.

The selected pair is the active eligible bracket at the canonical first hit.
The report retains recovered episode counts, every exclusion count, target-hit
frame, and the selected trace line, decision frame, query frame, source frame,
epoch, stage, spell, and immutable identity digest.

## Five Formal Questions

1. **Which histories merge?** Only histories with identical canonical
   complete-mask pipeline roots, float32 observations, versions, coverage
   root, and declared hidden-delay information set share a finite root.
2. **Are quantifiers causal?** Yes for the declared stationary continuation
   class: root action is chosen before nature, hidden successors merge by
   observation, and continuation selection never sees the hidden branch.
3. **What does an exact solve answer?** It answers attainable survival inside
   the retained finite hazard model and restricted continuation class. It
   does not answer physical unrestricted survival when coverage becomes
   unknown.
4. **What falsifies the claim?** A missing/reordered root action, scalar/native
   label mismatch, worst-path replay mismatch, identity/capsule mismatch, an
   unavailable row crossed by bracket selection, or a physical contact before
   the declared lower-bound prefix falsifies the corresponding claim.
5. **Can it be consumed before issue?** No. This checkpoint is offline only.
   Any future G4 shadow or consumer requires a separate immutable publication,
   cancellation, newest-version, deadline, and fresh-certificate gate.

## Implementation Checkpoint

The modular analyzer lives in
`scripts/analysis/first_loss_capsule/` with the command-line entry point
`scripts/analysis/g3_g4_first_loss_capsule_audit.py`. It joins exact roots by
trace line, rejects non-Boolean viability records, selects only the loss
episode containing the canonical first hit, and asks the existing independent
scalar/native capsule machinery to complete all 36 root actions against all
36 stationary continuation candidates.

Two retained workloads bound the current conclusion:

- **Observed negative Stage-5 gate:** Replaying
  `lunatic_route2_stage5_unattended_20260728_124930` selects no substitute.
  It counts 15 recovered loss episodes, identifies the active unresolved
  transition at decision/query frame `2049/2048`, and stops on
  `audit_capsule_missing`. The canonical hit remains frame 2167. This
  deterministically confirms that the missing immutable hazard slab cannot be
  repaired after the fact.
- **Observed positive implementation gate:** Capsule-bearing physical
  Stage-4A trace `lunatic_route2_stage4a_unattended_20260728_020910` selects
  last-viable decision/query `1039/1038` and first-losing decision/query
  `1041/1040` before the frame-1099 canonical hit, after nine earlier
  recovered episodes. Both roots complete `36 x 36` portfolios and worst-path
  replay with zero scalar/native mismatch. The G4 issued mask `0x05` retains
  the full 32-frame restricted prefix but is not best; masks
  `0x50/0x51/0x54/0x55` are best. The G3 issued mask `0x45` retains only five
  frames while best masks `0x50/0x51` retain 32.

Both Stage-4A roots have `UNKNOWN` unseen-future-hazard coverage beginning at
the first successor (`query + 1`). Therefore the positive gate establishes
implementation completeness and a finite-proxy action separation only.
It provides no physical survival prefix, live ranking, or strategy promotion.

The compact Stage-5 negative report has internal digest
`846dd73c6d3f8a56689b1d0d88eb71bef192a3b64ac3450974c92b3cf82c08e4`
and file SHA-256
`03d20656358fee400fdcad7dc211091c9a84a0d93fdd4a9e7a41ba9fbffa0535`.
The Stage-4A positive report has internal digest
`010cbbc819b82066153bfcf5b4e022a5e6c223667bb7ae5182b9a820ffd77c1b`
and file SHA-256
`c29004d280634b892a7e36e0705a6693c3b7c2150a3665ab63a71813be29ac63`.
Both regenerate byte-identically.

## Fresh Stage-5 Physical Gate

**Observed:** Capsule-enabled run
`lunatic_route2_stage5_unattended_20260728_133633` completed frames
`1..44822` over 13,304 decisions with 23 hits, hard no-Bomb, accepted
automatic transitions, `route_complete`, exact key release, and complete
process cleanup. It retained 1,879 readable capsules totaling 104,461,318
bytes. The sorted `SHA-256 basename` manifest digest is
`065b7da853125239f1389dc1077f562199da1509ace886c7474db25cee43779f`.
Capsule I/O makes the run ineligible for timing conclusions.

The canonical first hit is frame 4027. After 24 earlier recovered loss
episodes, the persistent episode begins at first-losing decision/query
`3752/3751`; the last viable decision/query is `3750/3749`. Thus the
finite-model loss precedes contact by 275 frames.

Both selected roots complete all 36 root actions against all 36 stationary
continuation candidates. Every worst path replays and scalar/native mismatch
count is zero:

- G4 issued mask `0x55` has a 30-frame label; best masks `0x10/0x11` have
  32-frame labels.
- G3 issued mask `0x85` has a 22-frame label; best masks `0x20/0x21` have
  32-frame labels.

Both roots declare `UNKNOWN` coverage from the first successor
(`3750` and `3752` respectively). The audit therefore passes only its
finite-model implementation gate:
`finite_model_audit_passed=true`,
`physical_survival_claim_available=false`, and
`strategy_promotion_available=false`. The apparent 10-frame G3 separation is
not a physical counterfactual because the finite slab omits all future births
from that first successor.

The report regenerates byte-identically with internal digest
`8a1efd3ecaf38f215c9a739befef674e95ae83de4a723cd27c0a8707c2678a2b`
and file SHA-256
`122db4b26be6f36416a3eb69e72c88faeae195c77a784265bd9696d20502aa1e`.
The immutable raw trace SHA-256 is
`5a40e13e0979fc484f41147e15730c23ebf4876e463e1428fc4ac9ad80fc9bdd`.

**Decision:** The experiment is complete as an offline discriminator. It
falsifies the claim that the historical issued actions were always best in
the retained finite proxy, but it cannot falsify or prove their physical
survival ordering. Continue G5 future-hazard coverage; rerun this exact
quantified audit only after a causal containing model covers the claimed
prefix.

## Acceptance Gates

- deterministic synthetic tests cover a clean pre-hit persistent bracket, a
  recovered earlier loss episode, unavailable-query interruption, missing
  capsule, malformed identity, epoch transition, and a hit-containing losing
  episode without exact evidence;
- existing complete-mask trace/capsule tests remain unchanged and pass;
- both selected roots complete all 36 root actions and all declared
  stationary continuation candidates;
- scalar/native per-action parity and worst-path replay have zero mismatch;
- two report generations are byte-identical;
- the fresh physical run verifies hard no-Bomb, accepted transitions, key
  release, artifact completion, and process cleanup; and
- raw trace/capsules remain ignored while the compact report, hashes,
  provenance, contamination statement, and result enter the research log.

## Stop Rules

Stop without a survival conclusion if the loss episode active at the
canonical first hit lacks an exact capsule root, if its bracket crosses an
unknown row, if capsule metadata disagrees with the canonical root, if
coverage is unknown before the claimed physical prefix, or if any portfolio
is incomplete.

Do not tune the live geometric fallback from aggregate labels. A later
proposal must identify a completed causal policy class, show that its result
was available before issue, intersect it with a fresh local hard set, and pass
a focused physical nonregression gate.
