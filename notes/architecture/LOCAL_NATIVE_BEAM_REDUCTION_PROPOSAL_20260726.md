# Native Local Beam Reduction Proposal

Date: 2026-07-26

Status: accepted live implementation optimization only for quantized
deduplication when no selected-item objective is present. Python remains the
explicit rollback and handles other beam modes and item-bearing drafts. This
does not promote the finite beam to a safety proof.

## Problem Contract

### Physical objective

Reduce observe-to-issue latency without changing the local planner's action
set, horizon, hazard model, hard collision ordering, target constraint, item
objective, boundary reserve, or no-Bomb authority. The physical acceptance
criterion is fewer stale decisions and deadline misses; a faster proxy alone
does not establish fewer native hits.

### State and observations

The native boundary begins after one beam step's drafts and exact hazard
vectors have been computed. Each supported draft contains:

- position, first and last action;
- accumulated risk and collisions;
- minimum and immediate clearance;
- a collected-item mask. The live native path is disabled whenever selected
  items are present, so nonzero item utility stays in Python.

The reducer also receives the current step, target and deadline,
per-first-action certificate labels, survival/safety preferences, recovery
distance, and boundary-reserve distance. It receives no hidden future
observation and cannot choose an action outside the Python planner's current
draft set.

### Action and transition

The movement transition and hazard query remain outside this reducer. For the
live `quantized` mode it performs only:

1. the existing quantized state key;
2. first-seen stable grouping in Python draft order;
3. strict lexicographic incumbent replacement by the existing pruning key;
4. stable lexicographic ordering of group winners;
5. truncation to the declared beam width.

It returns retained draft indices. Python constructs the next
`SearchNode` objects and continues the unchanged recurrence.

### Uncertainty, horizon, resources, and safety

Pickup delay, pending-command support, cadence, hazard uncertainty, horizon,
action hold, items, target deadline, and viability labels are inputs already
resolved by the Python caller. The reducer neither adds nor removes branches.
Hard survival remains lexicographically ahead of all soft objectives.

The reducer is an exact implementation candidate only for
`beam_dedup_mode="quantized"` without selected items. Other beam modes and
item-bearing drafts keep the Python oracle. A missing native symbol or
invalid result blocks armed native configuration; the explicit
`--local-beam-reducer python` option is the rollback. A parity mismatch
blocks promotion.

### Deadline and fallback

The reducer is useful only if its full wrapper plus native time lowers
Windows beam-search p50 and p95 without increasing end-to-end deadline
misses. The live issue thread must never compile or cold-expand work.
The existing Python beam is the rollback path.

## Five Formal Questions

1. **Which histories merge?** The reducer merges exactly drafts with equal
   existing quantized keys:
   `(round(x/2), round(y/2), last direction, focus, collected mask)`.
   It receives the same first-action-dependent pruning labels as Python.
   It does not introduce a new model-state equivalence.
2. **Are all uncertainty branches causal?** The reducer sees only completed
   draft and certificate values available at this decision. It does not
   branch hidden states or maximize separately over hidden outcomes.
3. **Does an exact solve answer the physical decision?** No. It reproduces
   one finite beam approximation and therefore only its current local
   proposal. The fresh local certificate and live Boolean policy retain their
   existing authority boundaries.
4. **What is solved or bounded, and what falsifies it?** It must reproduce the
   Python reducer exactly for every supplied draft. Any retained-index,
   selected-action, hard-label, collision, or clearance mismatch falsifies
   implementation equivalence. No new optimality or safety bound is claimed.
5. **Can it be consumed before issue time?** Promotion requires paired
   Windows replay timing and a complete physical telemetry run. Native
   library load happens before the measured decision loop; a symbol miss or
   error cannot delay issue behind an asynchronous fallback.

## Approximation Direction

No intentional numeric or semantic approximation is introduced. C++ and
Python `exp`, `hypot`, rounding, and stable tie handling can differ at
machine precision, so the implementation direction is unknown until
differential tests cover adversarial half-grid ties, equal pruning keys,
infinities used for unavailable recovery labels, items, targets, and retained
physical roots. Those implementation gates passed for the declared no-item
boundary. The beam itself remains proposal logic below the hard certificate;
only its exact reducer implementation is live.

## Evidence Before Implementation

Detailed Stage-6B physical telemetry
`lunatic_route2_stage6b_unattended_20260726_165841` measured:

- beam search `11.391/19.310 ms` median/p95;
- certificate geometry `2.113/5.611 ms`;
- bullet decode `2.406/7.282 ms`;
- observe-to-input `30.107/44.914 ms`.

One frame with 111 bullets and 210 lasers reached `110.549 ms`; its local
certificate geometry was `67.119 ms`. This outlier is a separate
multi-frame-query concern and is not evidence that beam reduction alone
would remove every miss.

A 32-root native profile recorded 39,077 `pruning_key` calls and 33,351
sorted-key callbacks. A Python dictionary key-cache experiment was already
paired on Windows and was mixed/worse; it remains rejected rather than being
reintroduced under a new name.

## Implementation And Retained Evidence

Adversarial half-grid/tie/infinity cases, 96 deterministic randomized
reducers, and 32 end-to-end `choose_action` cases passed exact retained-index,
action, and hard-label parity. A paired Windows replay used 128 direct roots
per trace and two repeats:

- Stage 4A `160712`: beam `6.423/8.221` to `4.549/5.759 ms`
  median/p95; complete local planning `9.493/13.138` to
  `7.715/11.072 ms`;
- Stage 6B `165841`: beam `9.547/13.528` to `6.204/8.270 ms`;
  complete local planning `13.222/18.567` to `9.903/14.712 ms`.

Both traces had zero selected-action and hard-label mismatches. The complete
Hard Stage-1 physical run `175049` then completed 7,099 decisions with zero
hits, zero Bomb, and zero deadline misses while using the native reducer.
That is a focused implementation gate, not Lunatic/Extra acceptance.

Retained artifact:
`artifacts/benchmarks/local_native_beam_windows_20260726.json`.
