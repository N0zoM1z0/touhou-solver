# TH08 Stage 3 No-Bomb Comparison: 160344 Versus 170433

## Integrity

Both practice scopes pass the hard no-Bomb invariant. The candidate run covers
Stage-3 frames `93..26383`, contains 7,576 decisions and ten native hit edges,
and ends on the Stage-3 unload with a scope-valid raw summary. Its initial
resources are 8 lives, 4 Bombs, and 128 Power. Later resource values are
post-respawn discovery state, not independent full-resource attempts.

The executable comparison is
`artifacts/runtime_reports/lunatic_route2_stage3_practice_20260723_comparison.json`.
The full candidate ledger is
`artifacts/runtime_reports/lunatic_route2_stage3_practice_20260723_170433.dossier.json`.

## Physical Result

| Metric | Baseline | Candidate | Change |
| --- | ---: | ---: | ---: |
| Total hits | 16 | 10 | -37.5% |
| Active spell-35 hits | 2 | 0 | eliminated in this run |
| Active spell-50 hits | 6 | 5 | -16.7% |
| Spell-50 solve median | 895.4 ms | 164.3 ms | -81.7% |
| Spell-50 solve p95 | 2993.6 ms | 362.2 ms | -87.9% |
| Spell-50 solution-age p95 | 193 frames | 27 frames | -86.0% |
| Spell-50 stale solutions | 8 | 0 | eliminated |

Every candidate hit obtained a stable same-manager-frame player lethal AABB
capture. Eight also contained a live spell-owner body. None of those eight
enemy AABBs overlapped the player. Spell 35 remained active without the prior
body-contact failure and its later frame-7,266 hit occurred after the owner
became inactive, with a retained bullet overlap. This physically supports the
enemy-body correction without claiming a general Stage-3 clear.

## Why It Still Misses

The candidate controller cadence is three game frames median and four frames
p95. In the 60 frames before the five spell-50 hits, individual updates commonly
held one input for four or five frames. The MPC, however, assumed that each
candidate action would be held for exactly two frames. Thus an action judged
safe for a two-frame segment could continue moving for twice that duration
before a replacement arrived.

This mismatch becomes worse under dense lasers:

- local planning is 16.9 ms median and 45.1 ms p95;
- pool reads alone are 8.5 ms median;
- the old trace does not time pool decoding, `SendInput`, record construction,
  UNC flush, or the complete loop;
- spell-50 hit windows averaged roughly 3.7-3.8 frames between decisions.

Performance is therefore causal for part of the failure, especially the two
hits whose snapshot-to-action lag exceeded the modeled three frames. It is not
the whole cause. Vectorization removed the seconds-old corridor plans, yet the
spell-50 hit rate changed only slightly.

The stronger remaining geometric signal is terminal escape-space collapse.
During spell 50, the player occupied the bottom eight pixels in 83.1% of alive
samples within 60 frames of a hit, versus 8.9% outside those windows. Fast mode
also rose from 45.9% outside hit windows to 60.6% inside them. The planner is
often reaching a currently clear bottom cell that has too few repair
directions for the next wave.

The `corridor_deadline_miss` factor appears in all ten 240-frame windows, but it
is not by itself causal: spell-50 negative-slack frequency is lower near hits
than outside them. It is a historical pressure flag, not proof that a late
global solve caused a particular collision.

## CFFI Decision

`cffi` is an interface, not an optimizer. Moving unchanged Python loops behind
it would not help. NumPy already executes the vectorized bullet/laser fields in
native code. A compiled core becomes justified only after full-loop timing
shows that beam expansion or occupancy dynamic programming remains the dominant
budget after architecture fixes.

If native migration is required, the useful boundary is one coarse call over
contiguous structure-of-arrays state into a C++/Rust kernel, returning a
multi-frame control prefix and certificate. Per-bullet or per-grid-cell CFFI
calls would add conversion and call overhead.

## Prepared Correction

The next controller records observe, pool-read, pool-decode, corridor
bookkeeping, local-plan, input, trace-flush, and complete-iteration timings.
Its local MPC estimates action hold from the rolling p90 of real decision-frame
deltas, clamped to 2..6 frames; the initial live estimate is three frames.
Holding actions longer in the model also reduces beam branching. On the ten
persisted pre-hit hazard subsets, hold 4 changed five first actions and roughly
halved local search time, though already-negative committed prefixes remained
unrecoverable.

This fixes the performance/model coupling. A separate planner change is still
required: score terminal connected components by future reachable volume or
repair directions, rather than treating immediate clearance and a shallow
boundary penalty as sufficient.

## Next Acceptance

1. Repeat fresh Stage 3 with 8/4/128 and hard no-Bomb.
2. Require stable timing telemetry and verify modeled action hold matches
   observed p90 cadence.
3. Preserve zero active spell-35 enemy-body hits.
4. Reduce the first nonspell hit and spell-42/46 bullet overlaps before using
   spell-50 post-respawn counts as a clear-rate metric.
5. For spell 50, compare bottom occupancy and first divergence, not only solve
   latency. A useful correction must reduce both bottom trapping and hits.
