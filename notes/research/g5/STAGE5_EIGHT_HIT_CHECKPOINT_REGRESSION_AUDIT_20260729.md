# Stage-5 Eight-Hit Checkpoint Regression Audit

Date: 2026-07-29

Status: causal source review complete; observer-off recovery pass 1 retained;
no single code regression established

## Question

Which change between the two retained eight-hit Lunatic Stage-5 checkpoints
and current checkpoint `3f02ff1` caused the 18-hit result
`20260729_125453`?

## Retained Comparison

| Run | Exact code checkpoint | Hits by nonspell/103/107/111/115 | First hit | Cadence p50/p95 |
| --- | --- | --- | ---: | --- |
| `20260727_212624` | `faed791` | `4/1/2/0/1` | 11504 | `2/3` |
| `20260728_171633` | `3adad09` | `3/2/1/1/1` | 12324 | `2/4` |
| `20260729_125453` | `3f02ff1` | `6/2/4/2/4` | 731 | `2/4` |
| `20260729_154229` | `e4e266f` | `5/2/1/1/1` | 10740 | `2/4` |

All four completed hard no-Bomb Stage 5 with accepted artifacts and cleanup.
They are distinct game histories, not same-seed paired trials. The final run
was launched from repository checkpoint `b34f905`; changes after executable
checkpoint `e4e266f` were documentation only.

## Source-Diff Finding

**Observed:** from the newer eight-hit checkpoint `3adad09` to `3f02ff1`:

- `scripts/corridor_planner.py`, `scripts/th08_corridor_runtime.py`,
  the live `scripts/touhou_control/` policy modules, and
  `native/src/pipeline/` have no changed action-authority implementation;
- the only new file in the narrowly filtered issue/policy path is
  `scripts/th08_live/issue_stage.py`;
- commit `9e3bce9` extracted the existing issue-time reads, dispatch,
  delay-recorder mutation, and previous-mask update into that module;
- the extracted function still dispatches
  `(previous_mask, decision.mask)`, records delay only when a transition was
  written, and returns the same issued mask/direction; and
- subsequent controller changes in this range add default-off or explicitly
  selected post-issue tracing, ECL identity, auxiliary capture/event work,
  dossier work, and further structure.

Unit characterization covers the issue transaction, and the complete
1,052-test Linux/Windows suites passed at the V6 implementation checkpoint.
This supports behavior preservation of the mask transaction, not identical
Python instruction timing.

**Conclusion:** there is no observed planner, recurrence, native viability,
action ranking, or issued-mask algorithm change to roll back between
`3adad09` and current code.

## What Can Explain The Current Result

### Early physical-history divergence

**Observed:** the current canonical hit is a frame-731 nonspell
`sensor_gap_or_unmodeled_hazard` at the right/bottom boundary, after global
viability-kernel exhaustion. The eight-hit runs do not take their first hit
until frames 11,504 and 12,324.

The V6 auxiliary workload is selected only in spell 107. It cannot cause the
frame-731 failure or all earlier nonspell hits.

**Inferred:** the dominant difference in the 18-hit sample begins with an
early route/model failure, not with the spell-107 transport. Uncontrolled game
history and timing can change the pattern and position presented to the same
controller. Once the first death occurs, respawn position, phase timing,
Power, damage output, and later hazards diverge. Later hits therefore cannot
be counted as independent evidence of one code change.

### Persistent system weakness

**Observed:** every contact in all three runs follows global viability-kernel
exhaustion. The current run has 7,827 empty queried action sets, and its
canonical hit has three frames of robust warning. The same qualitative
failure class exists at the eight-hit checkpoints.

**Inferred:** the 18-hit run is a worse realization of an unresolved
viability/sensing/route problem; it does not reveal a newly introduced mask
selection bug.

### Observer-off recovery is one accepted control, not causality

**Observed:** run `20260729_154229` disabled every optional observer and
returned to the accepted ten-hit boundary. Its first hit moved to frame
10,740 and was an exact same-epoch enemy-body overlap; the body was already
present in the causal and action snapshots. All ten contacts still followed
global viability exhaustion. CE-0182 retains the exact first-hit state.

**Inferred:** this is evidence that current code can still realize the
historical eight-to-ten band without rollback. It does not isolate optional
observer contention because the physical history and RNG were unmatched, and
it does not close a two-consecutive-run gate.

### Optional observer contention remains plausible only in scope

**Observed:** V6 adds post-issue auxiliary capture, derivation, compaction,
packing, and a larger decision row only during spell 107. Overall cadence
p95 remains four frames, equal to the newer eight-hit run. Replay compaction
still has an `8.388 ms` tail.

**Inferred:** optional work may worsen some spell-107 iterations, but current
evidence cannot attribute the whole 18-hit route to it. Phase-matched V5/V6
emit diagnostics are nearly equal; they are different physical samples, not
a controlled A/B.

## What Is Rejected

- Do not reset to `faed791` or `3adad09` merely because each produced one
  eight-hit sample.
- Do not bisect trace-only commits using one aggregate hit count per commit.
- Do not compare spell-107 bearing rows to an all-stage emit distribution.
- Do not count post-respawn contacts as independent clean-route survival
  samples.
- Do not call the issue-stage extraction timing-identical without a matched
  measurement.

## Next Causal Gate

Keep current code and the identical workload before changing strategy:

1. repeat the exact observer-off Lunatic Stage-5 control for consecutive pass
   2;
2. if it exceeds ten hits, reset the consecutive sequence, stop expansion,
   and compare its canonical first hit against CE-0182 and the two eight-hit
   checkpoints;
3. if the first hit is very early or repeated controls remain high,
   investigate the retained nonspell first-hit geometry and issue/policy
   timing rather than reverting trace commits;
4. if two controls return to the historical range, rerun only one independently
   contracted observer with phase-matched publication metrics;
5. accept recovery only after two consecutive Stage-5 runs at no more than
   ten hits; and
6. then verify Stage 3, retained other stages, and a complete Lunatic route.

The proposed nonspell damage/Power/unfocused-shot work is a separate
survival-filtered experiment. It must not be mixed into the first control.
