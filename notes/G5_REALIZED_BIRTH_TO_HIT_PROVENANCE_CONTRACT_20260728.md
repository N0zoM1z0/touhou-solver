# G5 Realized Birth-To-Hit Provenance Contract

Date: 2026-07-28

Status: fixed before implementation. This contract authorizes one deterministic
offline audit over already retained trace and dossier evidence. It adds no
hazard forecast, planner, publication, issue, or physical action authority.

This refines the retrospective B5 boundary in
`TH08_FUTURE_BULLET_BIRTH_OBSERVATION_CONTRACT_20260728.md`. It is motivated
by the Stage-5 gap between two statements that must not be conflated:

- most retained hits happen after finite-kernel exhaustion; and
- an unseen future bullet birth caused a particular hit.

The first statement does not prove the second. This audit establishes the
smallest physically grounded relation available from the retained schema.

## Physical Question

For each retained native hit, did the hostile-bullet slot selected by the
review dossier have a retained native activation observation before or after
the reported viability-loss boundary?

The answer is split by evidence role:

- an `exact_observed_overlap` candidate is an observed bullet AABB overlap in
  the stable hit capture;
- a `nearest_only` candidate is a diagnostic neighbor for a
  modeled-committed-prefix collision and is not the observed collider; and
- missing or ambiguous activation evidence remains unresolved.

Only the first role can support a statement about an observed overlapping
bullet. Even then, the audit does not prove that the overlap was the sole
cause of the native hit or that a different earlier action would survive.

## Exploratory Evidence That Fixes The Gate

The following values are **observed** by a read-only exploratory join over
accepted Lunatic Stage-5 run
`lunatic_route2_stage5_unattended_20260728_124930`:

- the canonical first hit at frame 2,167 has an exact overlap with slot 1,357;
  its latest retained activation edge is frame 1,889, 160 frames before the
  reported viability-loss frame 2,049;
- the exact overlap at frame 3,987 uses slot 152, activated 47 frames before
  its loss boundary;
- the exact overlap at frame 14,043 uses slot 1,295, activated at frame
  13,870, six frames after the reported loss boundary 13,864; and
- the exact overlap at frame 40,693 uses slot 701, activated 78 frames before
  its loss boundary.

At frame 13,870 the observer reports a 30-bullet activation wave. Slot 1,295
is an inactive-to-active edge with finite geometry and candidate age one.
The phase is nonspell, `spell_enemy_pointer == 0`, no intent is available,
and the trace declares that the current intent scope covers only the active
spell enemy main VM. The omitted-source list includes nonspell enemy main VM,
child/auxiliary VM, callback/interrupt, non-ECL native, and deferred runtime
state.

These observations reject two overbroad hypotheses:

1. the canonical first hit is not evidence of a post-loss birth; and
2. every exact Stage-5 overlap is explained entirely by bullets already
   active at the loss boundary.

The second rejection makes nonspell source topology relevant to hit reduction,
but does not grant a forecast or action consumer.

## Problem Contract

### Physical objective

The eventual objective is fewer physical no-Bomb hits by preserving a viable
route under complete causal hazard information. The present objective is only
to classify retained bullet/hit candidates by observed activation timing and
source-observation scope so that the next G5 sensing intervention targets a
demonstrated failure class.

### State and observations

One audit problem is identified by:

```text
(
  immutable raw-trace path, byte count, SHA-256,
  immutable dossier path and SHA-256,
  gameplay epoch and stage filter,
  bullet-birth schema version,
  dossier schema version
)
```

The trace contributes only `bullet_birth_audit` rows. For each evidence
column, the audit retains:

```text
(
  trace frame and snapshot frame,
  observation frame_before/frame_after support,
  slot, evidence code/status,
  previous/current state and age,
  geometry and transform flags,
  intent presence,
  spell-owner pointer,
  declared intent scope and omitted sources
)
```

The dossier contributes native hit frame, sample role, phase attribution,
reported viability-loss frame, primary cause class, and either the exact
observed overlap candidate or the nearest diagnostic bullet.

For one hit candidate, the audit selects the latest qualifying activation
record for the same slot no later than the hit. Qualifying records are
inactive-to-active edges, bounded bootstrap-recent observations, and explicit
timer regressions. Their meanings remain distinct; a timer regression is
slot-reuse ambiguous, not an exact activation.

### Actions and issue semantics

There are no actions. The program:

- reads retained files only;
- does not attach to TH08 or read process memory;
- does not select, rank, or write input;
- cannot emit Bomb bit `0x02`;
- does not change cadence, workers, policy versions, or live trace schemas;
  and
- cannot reclassify a G1/G3/G4 `model_unknown` result.

### Uncertainty and transitions

An activation is compared with loss using its retained capture support:

```text
activation_after_loss:
  support_start > loss_frame

activation_before_or_at_loss:
  support_end <= loss_frame

activation_straddles_loss:
  otherwise
```

The trace row frame is descriptive and must not replace the support interval
when both endpoints are available.

The audit explicitly preserves:

- capture-spanned activation time;
- bootstrap observations whose prior inactive state was not observed;
- timer-regression/slot-reuse ambiguity;
- missing or malformed evidence;
- multiple generations of one slot;
- exact overlap versus nearest-only candidate role;
- canonical fresh-attempt versus post-respawn discovery role;
- unknown source identity and the declared omitted-source set; and
- the fact that reported viability-loss time is itself a finite-model result,
  not physical inevitability.

No future observation is inserted into an earlier controller decision. This
is hindsight provenance only.

### Horizon and resources

The audit scans the retained JSONL once and holds only per-slot activation
records needed by dossier hits. Memory is bounded by the number of selected
slots and their observed generations, not by all bullet births. It performs no
native solve and has no live deadline.

The compact report retains source hashes, exact counts, every selected hit
record, unresolved reasons, and a canonical SHA-256 digest. It uses strict
JSON (`allow_nan=False`) and two generations from the same inputs must be
byte-identical.

### Safety invariants and authority

- Survival remains hard and Bomb remains forbidden.
- `nearest_only` is never counted as observed contact provenance.
- A post-loss exact overlap does not prove the birth caused kernel exhaustion.
- A pre-loss activation does not prove the bullet was included correctly in
  every cached hazard snapshot.
- A matched activation does not identify its enemy/ECL/native source.
- Later post-respawn hits remain geometry/source counterexamples, not clean
  route-survival samples.
- Missing activation evidence is unresolved, not pre-loss.
- `model_unknown` remains unknown.
- The report has `physical_action_authority: none` and
  `strategy_promotion_available: false`.

## Formal Review

1. **Control-equivalent histories:** no histories are merged for control. The
   audit joins exact epoch/stage/slot histories retrospectively and preserves
   multiple slot generations.
2. **Uncertainty and causality:** activation support, reuse ambiguity, source
   omissions, and candidate role are explicit. The controller makes no choice
   using hindsight.
3. **Physical answer:** an exact result can state that an observed overlapping
   bullet slot was seen to activate before, after, or across a reported
   finite-model loss boundary. It cannot answer the counterfactual action or
   complete future hazard field.
4. **Algorithm and falsifiers:** a streaming exact-key join solves the stated
   provenance question. A later qualifying generation selected incorrectly,
   an exact overlap counted as nearest-only (or vice versa), a support interval
   collapsed to one frame, an unreported unmatched candidate, or
   order-dependent output falsifies it.
5. **Deadline and fallback:** there is no issue-time consumer. Parse, schema,
   hash, or validation failure makes the offline report fail closed.

## Ordered Gates

1. Add synthetic cases for activation before, after, and straddling loss.
2. Separate exact overlap, nearest-only, missing candidate, missing activation,
   bootstrap, and timer-regression results.
3. Preserve source scope and omitted-source declarations on the selected
   generation.
4. Reject malformed column lengths, nonfinite geometry, invalid support, and
   duplicate inconsistent dossier hits.
5. Generate the Stage-5 report twice and require byte identity.
6. Record the exact-overlap counts and the frame-14,043 nonspell witness in
   `COUNTEREXAMPLES.md`, `RESEARCH_LOG.md`, `START_HERE.md`, `STRATEGY.md`,
   and the consolidated roadmap.
7. Use the result to contract the next nonspell source-topology observation.
   Do not change live sensing or action authority in this checkpoint.
