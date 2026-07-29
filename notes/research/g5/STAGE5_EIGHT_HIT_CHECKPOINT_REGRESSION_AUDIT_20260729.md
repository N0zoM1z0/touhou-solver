# Stage-5 Eight-Hit Checkpoint Regression Audit

Date: 2026-07-29

Status: causal source review complete; consecutive observer-off recovery
rejected by CE-0183; no single code regression established

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
| `20260729_161313` | `e4e266f` | `10/2/5/1/0` | 2524 | `2/4` |

All five completed hard no-Bomb Stage 5 with accepted artifacts and cleanup.
They are distinct game histories, not same-seed paired trials. The final run
was launched from repository checkpoint `39366f2`; the two observer-off
controls differ only by first-run compact evidence/documentation and physical
history after executable checkpoint `e4e266f`.

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

### The unchanged consecutive control rejects stable recovery

**Observed:** run `20260729_161313` used an exactly equal controller config,
target hash/patch, native backends, hard no-Bomb policy, stage/difficulty, and
optional-observer/shadow settings. Both observer-off controls entered with
Power 128, lives 8, and Bomb stock 3. The second run nevertheless took 18
hits, resetting the sequence.

The fresh histories diverged before any coupled respawn comparison:

- pass 1 first contacted at frame 10,740 near the lower playfield in an
  exact same-epoch enemy-body overlap, after global loss by nine frames;
- pass 2 first contacted at frame 2,524 near the upper-right in a modeled
  committed-prefix bullet collision, after global loss by 240 frames and
  robust-action exhaustion by eight frames;
- pass-2 first-hit delay support was `2..6`, versus `2..4` in pass 1.

These are workload/config-matched but not same-seed, same-history, or
same-first-hit-state trials. CE-0183 retains the earliest failing state.

### Candidate-cause disposition

| Candidate | Disposition | Evidence boundary |
| --- | --- | --- |
| Changed planner/recurrence/mask authority | Ruled out for this pair | No executable path changed; both use `e4e266f`/`3f02ff1` and exact equal controller config. |
| Different optional observer configuration | Ruled out for this pair | Every optional observer and shadow is off in both sessions. |
| Different practice entry resources | Ruled out | Both start at Power 128, lives 8, Bomb stock 3. |
| Optional V6 observers as a necessary cause of 18 hits | Ruled out | The observer-off pass itself reaches 18; a smaller observer effect remains unresolved without a paired history. |
| General cadence regression | Unsupported | Both cadence median/p95 are `2/4`; local-plan p95 changes only from `23.615` to `24.375 ms` observationally. |
| Different physical/RNG/delay/hazard history | Supported state divergence | First-hit frame, position, hazard class, action, and delay support differ; the causal primitive behind that divergence is unresolved. |
| Persistent viability/model weakness | Supported | All 28 contacts across the consecutive pair follow global-kernel exhaustion; pass 2 loses it 240 frames before first contact. |
| Rollback of trace/report commits | Rejected | There is no changed authority path or controlled reproduction tying those commits to the first hit. |

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

The unchanged pass-2 control has failed, so stop physical expansion:

1. retain CE-0183 and reset the consecutive sequence;
2. do not launch Stage 3, another unchanged Stage-5 sample, or an observer
   A/B as a substitute for causal correction;
3. replay/analyze the frame-2,284 global-loss root and frame-2,516
   committed-prefix boundary with exact delay/action/hazard state;
4. begin the roadmap's ordered native-semantic correction series and take the
   smallest causal Stage-5 falsification after each applicable slice; and
5. only after a versioned correction restarts the baseline, require two
   consecutive Stage-5 runs at no more than ten hits before other stages.

The proposed nonspell damage/Power/unfocused-shot work is a separate
survival-filtered experiment. It remains blocked behind semantic and
viability authority.
