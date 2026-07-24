# Stage-5 Robust-Viability Differential Audit

Date: 2026-07-24

This checkpoint asks why the rolling robust kernel was empty before Stage-5
hits. It does not assume that every empty result has one cause, and it keeps
TH08 stage/spell identity out of the game-neutral recurrence.

## Physical Corpus And Measurement Scope

**Observed:** complete hard-no-Bomb Practice run
`lunatic_route2_stage5_unattended_20260724_201636` reached `route_complete`
over frames `2..46642`. It retained 27 native hit edges, 7,436 decisions,
1,879 unique policies, and zero Bomb input. The complete dossier, death
ledger, regressions, comparison, summary, session, and run note are tracked.
The raw 240 MiB JSONL and 1,879 lossless lowered-hazard capsules remain
ignored.

The audit selected the last two available policy queries before each hit
inside a 32-frame window. All 54 selected queries were trace-empty. Every one
had its exact governing capsule, and recomputing the 16-pixel policy matched
the retained Boolean result in 54/54 cases.

**Instrumentation limitation:** capsule writing was synchronous in this run.
The policy recurrence took `100.17/166.71 ms` median/p95, capsule I/O added
`91.58/117.58 ms`, and total worker service became `194.25/264.06 ms`.
Therefore this run is valid for reproducing the policies it actually used,
but its hit count and service timing are not a clean comparison with
non-capture runs. Capsule I/O is now submitted to a separate one-worker queue;
policy publication no longer waits for the file write. That correction has a
regression test but is not yet physically timed.

## Comparable Variants

The exact spatial comparison preserves the live eight-frame control layer and
its full recorded delay support:

- `16px / 8f / 80f`, the reconstructed live policy;
- `8px / 8f / 80f`;
- `4px / 8f / 80f`.

The `8px / 4f / 80f` variant clips delays above four frames. It is diagnostic
only. An exact four-frame recurrence for the live `{1..6}` support requires
augmenting state with the pending command and remaining delay; merely changing
the layer size changes the game.

The 32/48/64-frame variants preserve `16px / 8f`. A next-policy terminal mask
was also evaluated where available. Such a mask is a subset of the
instant-safe terminal set: it may reject an optimistic winning state, but it
cannot turn an already-empty state into a winning one. Because every selected
pre-hit query was already empty, this sample contains no instant-winning
terminal cohort. Terminal-overlap quality needs a separate winning-query
audit.

## Empty-Set Classification

**Observed primary classification:**

| Primary class | Queries |
| --- | ---: |
| modeled losing, cause unresolved | 51 |
| 16-pixel spatial coarse false-empty | 3 |
| stale/reconstructed policy mismatch | 0 |
| shorter-horizon winning | 0 |

The three coarse witnesses are:

| Hit | Decision/query | Phase | 16px | 8px | 4px |
| ---: | --- | ---: | --- | --- | --- |
| 23884 | 23867 / 23862 | 103 | empty, survival 17f, projection error 9.707 | 3 actions, error 2.153 | 4 actions, error 1.882 |
| 25577 | 25560 / 25554 | 103 | empty, survival 5f, error 8.416 | 11 actions, error 3.626 | 12 actions, error 0.559 |
| 25577 | 25569 / 25562 | 103 | empty, survival 0f, error 8.416 | 3 actions, error 3.626 | 9 actions, error 0.559 |

This is direct evidence that uniform 16-pixel induction can erase a real
robust action set. It is not evidence that globally replacing the live grid
with 4 pixels is the right architecture. None of the sampled phase-107
queries became viable at 8 or 4 pixels, so Reisen's main sampled failure is
not explained by spatial coarseness alone.

**Observed orthogonal model evidence:** before hit 32581 in phase 107, collision
bullet slot 1446 was absent from governing source frame 32546. A later capsule
observed new slots 1420..1457, including 1446, and the retained hit geometry
shows exact bullet overlap. The governing policy was already losing without
that future bullet, so the birth gap did not cause its empty result. It is
still a separate unsoundness in any claim that the policy covered future
hazards.

## Fused Survival-Horizon Shadow

The native shadow recurrence performs one backward pass and labels every
state lexicographically by:

1. maximum guaranteed collision-free physical frames;
2. bottleneck signed clearance among equal survival horizons.

It also emits best-action masks plus the ordinary Boolean viability and
safe-action masks. Randomized small games compare every native state, label,
margin, and mask against an independent scalar oracle.

**Observed on all 54 queries:** 53 guaranteed fewer frames than the actual
query-to-hit interval. One modeled counterfactual is actionable:

- hit 3491, decision/query `3486/3483`, query-to-hit 8 frames;
- fused label guarantees 10 frames;
- best set is `stay`, `left`, `down`, `down_left`, `left_fast`,
  `down_fast`, `down_left_fast`;
- endpoint-distance recovery selected and issued `down_right_fast`, outside
  that set.

Thus survival-horizon fallback is more correct than endpoint distance for at
least one retained losing state. It is not a general explanation for the
other 53 sampled hits. After stripping trace-only `+deadline_hold` suffixes,
47/54 issued actions were already in the oracle's best set.

The fused labels remain shadow-only. On one retained 16-pixel capsule, warm
native Boolean and fused medians were `11.38 ms` and `42.46 ms` respectively
over seven calls. This is small enough for offline differential work, but it
has not yet passed a live whole-pipeline budget or physical A/B.

## Native Transition-Cache Scaling

The first 4-pixel audit exposed a separate native data-structure defect.
The old cache materialized:

```text
active * selected * delay-slot * (row * column) * physical-step
```

For 17 actions, 9 delay slots, 105 rows, 93 columns, and 8 steps, that is
203,190,120 samples. An `int32` cell plus `float32` error consumes 1.514 GiB
before other policy and allocator memory. The audit process reached roughly
3.1--3.5 GiB RSS.

Regular-lattice movement is separable. The corrected native cache stores x
and y transitions independently:

```text
active * selected * delay-slot * (row + column) * physical-step
```

This is 4,119,984 axis samples, 49.3 times fewer. Using `int32` indices and
`float64` per-axis errors costs about 47.15 MiB and reconstructs the original
Euclidean error with `hypot`. Randomized Boolean, safety-value, and fused
survival scalar parity all pass.

**Observed isolated end-to-end capsule solves after the correction:**

| Grid | Elapsed | Peak RSS |
| --- | ---: | ---: |
| 16px | 0.30 s | 47 MiB |
| 8px | 0.46 s | 60 MiB |
| 4px | 0.82 s | 92 MiB |

The complete 54-query audit now takes about 158 seconds. Its process peak is
still about 1.27 GiB because it cycles many policy variants, metadata, Python
hazard objects, and native allocations; that remaining offline high-water
needs separate profiling.

This scaling bug does **not** explain the old 16-pixel live p95: live never
built the 4-pixel table. It made naive fine-grid auditing and any proposed
uniform fine-grid live policy impractical, and memory bandwidth was part of
that new workload's latency.

## Consequences

**Inferred next algorithmic work:**

1. Refine only the reachable tube and alleged empty boundary. The three
   physical coarse witnesses are gates for a generic adaptive refinement, not
   licenses for a phase-103 route.
2. Replace endpoint-distance fallback with fused survival labels only after a
   packed/query-local implementation meets the live deadline. The frame-3491
   witness is the first required action regression.
3. Lower TH08 ECL/projectile emissions into generic `BirthWindow` events. The
   phase-107 slot-1446 witness is a direct parity gate.
4. Audit winning pre-hit states separately for terminal-overlap rejection.
5. Model pending command and remaining delay before claiming exact 4-frame or
   event-time layers.
6. Profile the remaining 1.27-GiB offline audit high-water; do not attribute
   it to the live 16-pixel controller without a matching physical workload.

**Hypothesis pending physical validation:** adaptive fine-grid recovery plus a
survival-first losing-state action can prevent some phase-103/nonspell
failures without weakening the Boolean safety set. Phase 107 is more likely
to require event-complete birth/stop/resume modelling and earlier
reachability preservation.
