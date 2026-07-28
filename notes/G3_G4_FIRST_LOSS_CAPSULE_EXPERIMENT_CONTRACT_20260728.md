# G3/G4 First-Loss Capsule Experiment Contract

Date: 2026-07-28

Status: fixed pre-implementation offline/shadow experiment contract.

This contract follows CE-0158. Lunatic Stage-5 run
`lunatic_route2_stage5_unattended_20260728_124930` first reports an empty
global Boolean action set at decision frame 2049 and first contacts a bullet
at frame 2167. That run did not enable `--viability-audit`; its trace contains
the canonical query identity but not the complete lowered hazard slab.
Therefore the frame-2049 finite problem cannot be reconstructed exactly from
that trace.

The next physical workload may collect ignored diagnostic capsules. Capsule
I/O is explicit experiment contamination: the run cannot be used to close or
reopen B4, compare controller timing, or promote a live strategy.

## Physical Question

For the first clean-attempt global winning-to-losing bracket in one gameplay
epoch:

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

Decision rows are processed in trace order. A bracket is eligible only when:

1. both rows are in the same gameplay epoch and stage route index;
2. both viability queries explicitly report `available == true`;
3. the earlier exact root reports `state_viable == true`;
4. the next eligible exact root reports `state_viable == false`;
5. both rows have an available canonical complete-mask root and an audit
   capsule; and
6. no unavailable query, missing capsule, unavailable canonical root,
   malformed identity, root-frame mismatch, or parse failure occurs between
   them.

Any such interruption resets the viable predecessor. A timeout,
`pending_future_epoch`, expired policy, absent query, or missing capsule is
not a finite-model loss. If an explicit losing query lacks exact root
evidence, the first-loss result is unresolved; a later exact losing row may
not silently replace it.

The selected pair is the first eligible bracket in the requested physical
scope. The report retains every exclusion count and the selected trace line,
decision frame, query frame, source frame, epoch, stage, spell, and immutable
identity digest.

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

## Acceptance Gates

- deterministic synthetic tests cover a clean bracket, unavailable-query
  interruption, missing capsule, malformed identity, epoch transition, and
  explicit losing query without exact evidence;
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

Stop without a survival conclusion if the first explicit losing query lacks
an exact capsule root, if the bracket crosses an unknown row, if capsule
metadata disagrees with the canonical root, if coverage is unknown before the
claimed physical prefix, or if any portfolio is incomplete.

Do not tune the live geometric fallback from aggregate labels. A later
proposal must identify a completed causal policy class, show that its result
was available before issue, intersect it with a fresh local hard set, and pass
a focused physical nonregression gate.
