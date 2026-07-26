# Supplemental Direct-Root Windows Contention Gate

Date: 2026-07-26

Status: experiment contract fixed before measurement; no action authority

## Question

Can the default-off width-4 immutable supplemental continuation lane be
computed from a directly retained local input-pipeline root on Windows while
the normal-priority four-worker native viability planner is active, without
breaking its finite comparison contract, creating a plausible issue miss, or
materially aging authoritative global publication?

This is an offline delivery gate.  It does not inject input, read a live game
process, replay a future physical trajectory, or promote the explicit
active/held/pending root.

## Measurement Boundary

One retained Hard decision supplies:

- the native `input_current` and directly logged active/held/pending root;
- the same player, bullet, laser, enemy, delay, route, and complete
  global-repair query used at that decision;
- physical Windows `observe`, pool-read, raw-pool decode, local-plan,
  issue-path, `observe_to_input`, action-lag, policy-age, and deadline-guard
  telemetry; and
- compact trace hazards sufficient to replay local computation.

The gate keeps two boundaries separate:

1. **Observed physical baseline.**  Existing trace timing measured the real
   game process, persistent `ReadProcessMemory` pool destinations, native
   decode, current live local planner, issue guard, and `SendInput`.
2. **Windows direct-root replay.**  The selected JSON rows are already read
   into memory.  Trace-list reconstruction is measured separately, followed
   by direct-root projection/certification, historical or width-4 search, and
   a forced same-snapshot all-action issue recertification.  JSON parsing and
   `ReadProcessMemory` are outside this replay boundary.

The replay must not call trace reconstruction "pool decode" or call a no-op
function "input issue."  A hybrid issue estimate is only:

```text
recorded physical observe_to_input
  + paired Windows direct-root compute delta(width4 - historical)
```

It is a same-root delivery proxy, not a physical timestamp.  Frozen manager
episodes and suppressed/death states are excluded; CE-0120 remains open.

## State, Actions, And Uncertainty

The explicit local root is parsed fail-closed from:

```text
(native active action,
 held desired action,
 optional pending action,
 remaining-delay support)
```

Mask/action identity, native `input_current`, one-pending estimator
consistency, and non-overdue support must agree.  The local finite lease uses
the existing conditional write/no-write recurrence.  The historical and
supplemental lanes receive the same hazards, delay support, effective global
action set, repair volume, route target, and horizon.

Width truncation and repair/reserve ordering remain bounded proposal
heuristics.  Final effective-action, componentwise issue/local/terminal hard,
route, and strict continuation admission remain exact for the supplied
finite values.  No path may emit Bomb.

## Contention Workload

Each Windows variant replays the identical deterministic root reservoir:

- historical without background viability;
- width 4 without background viability;
- historical with one normal-priority parent repeatedly launching the native
  viability recurrence at worker limit four; and
- width 4 under that same four-worker workload.

Variant and root order rotate by round.  The representative viability problem
is the retained `81 x 27 x 24`, 17-action workload used by
`local_issue_contention_benchmark.py`.  The report retains whether the native
thread-local worker limit was applied, solve latency, solves per wall second,
process CPU/wall ratio, and every local timing segment.

The root reservoir combines broad, pre-hit-300, and highest recorded
observe-to-input/density rows.  Duplicate roots are measured once per variant
and round.

## Fixed Pass/Fail Gate

The offline gate passes only when:

1. historical-incumbent mismatch, effective-global membership violation,
   componentwise hard regression, route regression, continuation-contract
   violation, Bomb, and supplemental exception counts are all zero;
2. every measured root is a valid direct root and every four-worker session
   reports that worker limit four was applied;
3. under four-worker contention, width-4 minus historical direct-root compute
   p95 is at most `5.0 ms` and the maximum paired increment is below one
   nominal 60-Hz frame (`16.667 ms`);
4. four-worker viability solve p95 regresses by no more than `10%`, and solve
   throughput regresses by no more than `10%`, relative to the historical
   four-worker variant; and
5. the hybrid stable-60-Hz deadline proxy creates no new misses relative to
   historical on the same roots:

   ```text
   estimated_observe_to_input_ms
       > support_high * (1000 / 60)
   ```

The deadline proxy assumes ordinary 60-Hz gameplay and is invalid across the
frozen-manager boundary.  Passing it is necessary for the next experiment,
not sufficient for issue-time authority.  The report also retains a stricter
worst-phase added-frame bound, but that deliberately pessimistic count is
diagnostic rather than a pass criterion.

## Fallback And Promotion Boundary

The benchmark never changes a trace action.  A failed gate keeps width 4
default-off and redirects work toward an asynchronous/post-issue or more
native boundary.  A passed gate permits only a focused Hard shadow in which
the historical controller still issues input and supplemental output is
retained for comparison.

Before any physical action authority, the system still needs:

- a real current-issue deadline/budget fallback rather than a retrospective
  timer;
- exact immutable version/root matching;
- fresh issue-time recertification;
- a clean focused shadow with policy-age, action-lag, and deadline evidence;
- CE-0120's separate action-boundary treatment; and
- a strategy-ledger status change.

## Observed Result

The retained Windows run used
`hard_route2_stage4a_unattended_20260726_212756.jsonl`, whose SHA-256 is
`cea41e2914c32d7157082cefca81e60a8d83e6d891886d294fdffcdf5f6c79a2`.
It found 8,180 non-overdue valid direct roots from 8,188 eligible decisions;
eight roots were explicitly overdue and none failed direct-root parsing.
Broad `128`, pre-hit-300 `64`, and high-latency/density `64` reservoirs
deduplicated to 253 roots.  Three rounds produced 759 measurements per
variant and 1,518 idle/four-worker finite comparisons.

**Observed physical baseline:** all 8,180 retained direct-root rows ran with
native viability worker limit four applied.  There were zero recorded
deadline misses.  The actual game-process chain was:

| physical field | median | p95 | maximum |
| --- | ---: | ---: | ---: |
| observe | 0.229 ms | 0.526 ms | 9.264 ms |
| pool reads | 4.337 ms | 7.662 ms | 24.834 ms |
| raw-pool decode | 0.502 ms | 1.986 ms | 14.604 ms |
| initial local plan | 11.701 ms | 20.144 ms | 38.136 ms |
| issue path to input | 2.724 ms | 7.247 ms | 22.019 ms |
| `SendInput` | 0.001 ms | 3.387 ms | 15.748 ms |
| observe to input | 21.783 ms | 33.229 ms | 52.722 ms |

Action lag was `1/2/3` frames median/p95/max.  Corridor policy age was
`11/28/80`; viability-query age was `10/27/79`.  This is direct physical
telemetry from the prior focused Hard run, not a counterfactual age measured
while the supplemental lane was active.

**Observed finite comparison:** the supplemental lane was active on 729/759
width-4 measurements in each contention class; 30 fresh-global contradiction
measurements correctly left it inactive.  Across the 1,518 comparisons,
width 4 changed 588 actions.  Historical-incumbent mismatch,
effective-global membership violation, componentwise hard regression, route
regression, continuation-contract violation, Bomb, supplemental exception,
missing issue transaction, and nonrelaxed issue-global violation counts were
all zero.  Forced same-snapshot recertification changed none of the selected
actions.

The first report incorrectly counted inactive fresh-global contradiction
roots as historical/membership failures because their intentionally absent
`preloss_historical_action` was compared as though the lane had authority.
The comparison now gates those two claims on
`preloss_continuation_preference_active`; a deterministic regression protects
the distinction.  Hard, route, Bomb, and issue-transaction checks remain
unconditional.

**Observed contention:** the normal-priority four-worker planner itself
passed.  Historical/supplemental viability solve p95 was
`40.135/40.060 ms`, a `0.998x` ratio.  Throughput was
`29.439/29.873 solves/s`, a `1.015x` ratio.  Worker limit four was applied in
every round and the parent priority was not lowered.

The synchronous local lane failed:

| Windows four-worker value | observed | fixed gate |
| --- | ---: | ---: |
| paired compute increment median | 2.354 ms | diagnostic |
| paired compute increment p95 | 14.273 ms | <= 5.000 ms |
| paired compute increment maximum | 25.184 ms | < 16.667 ms |
| supplemental search median/p95/max | 3.273/6.858/10.553 ms | diagnostic |
| new stable-60-Hz proxy misses | 1/759 | 0 |

The canonical retained delivery witness is epoch 2, frame 37,834.  It had
640 active bullets, no laser, physical `observe_to_input=41.999 ms`,
support-high four, and post-capture advance two.  Under four-worker
contention, historical and supplemental direct-root compute were
`18.551/43.735 ms`; the `25.184 ms` increment included `21.472 ms` in
`choose_action`, of which the separate supplemental search reported
`5.758 ms`.  The hybrid estimate was `67.183 ms`, above the four-frame
`66.667 ms` budget.  Historical, supplemental, and recertified action were
all `down_left_fast`; this is a delivery counterexample, not a finite-label
or selected-action disagreement.

The compact artifact is
`artifacts/benchmarks/hard_supplemental_direct_root_contention_windows_20260726.json`,
SHA-256
`43751f0a74c6285156acf1454df0c5be85deb27c3856d6570d3667ebba466ad0`.

## Decision And Next Gate

**Observed:** the width-4 finite selection/admission contract survived direct
active/held/pending roots and forced issue recertification.  The four-worker
global planner did not materially lose throughput or freshness capacity.

**Inferred:** synchronous current-issue supplemental delivery is not stable
enough for a focused physical A/B.  The tail is centered in `choose_action`
and the separate supplemental rollout, not trace reconstruction
(`p95 delta 0.315 ms`), root parsing (`0.010 ms`), or forced recertification
(`1.579 ms` paired delta).  The supplemental search's own `6.858 ms` p95
already exceeds the complete-increment gate, so cross-session paired noise
cannot explain away the rejection.

**Hypothesized next implementation:** if width 4 remains the preferred
proposal, fuse the complete supplemental rollout/hazard-query boundary into
native code and give it an explicit cooperative deadline, or publish it
asynchronously under exact immutable root/version identity.  A miss,
cancellation, version mismatch, or unfinished result must return the
historical action without blocking issue.  CPU affinity or worker
partitioning may be measured, but cannot replace the deadline fallback.

The same Windows gate must pass before a focused Hard shadow.  No physical
A/B is authorized by this checkpoint.

Linux and Windows quick suites pass `587/587` in `5.283/8.008 s`.
