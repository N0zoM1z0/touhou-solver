# G5 Corridor-Completion Priority Rejection

Date: 2026-07-28

Status: observed physical intervention failure; no second run authorized

## Fixed Experiment

Run `lunatic_route2_stage4a_unattended_20260728_092619` was the first
physical use of the precommitted
`notes/research/g5/G5_CORRIDOR_COMPLETION_PRIORITY_EXPERIMENT_20260728.md` boundary. The only
intervention was an explicit below-normal Python corridor parent. The four
native viability workers, controller/game priority and affinity, recurrence,
cadence, policy consumption, issue/fallback semantics, schema-v9 observer,
GC, and hard no-Bomb remained unchanged.

The run passed executable identity, no-life-decrement patch, Lunatic
Stage-4A selection, `route_complete`, artifact retention, supervisor
completion, exact-target cleanup, and hard no-Bomb. It covered frames
`2..44999`, 14,649 decisions, and 18 contacts.

## Observed Application And Delivery

- All 1,900 unique completed solutions report
  `background_priority_lowered=true`.
- All 1,900 report native worker limit four requested and applied.
- Corridor solve median/p95/max is
  `111.4190/302.3068/407.8457 ms`, inside the fixed limit.
- First-observed policy age median/p95/max is `2/4/1803` frames, also inside
  the median/p95 limit.
- Local-plan p95 is `17.9999 ms`; action-lag p95/max is `2/3` frames.
- Delay-support-uncovered query count is zero.
- No-query and queryable fractions are `0.8309%` and `99.1622%`, both
  passing.
- Expired-policy fraction is `36/14562 = 0.2472%`, exceeding the fixed
  `0.20%` rejection limit.

The deterministic priority report therefore has
`application_pass=true` and `delivery_pass=false`.

## Observed Observer Result

All 14,649 birth rows retain schema-v9/native/GIL-held provenance and
`windows_query_thread_cycle_time`. Validation and cycle attribution pass.
Observer p50/p95/p99/p99.9/max is
`0.1022/0.2049/0.3401/0.5282/0.8925 ms`.

The maximum improved descriptively from the normal-priority run's
`5.1274 ms`, but p95 still exceeds the fixed `0.200 ms` limit. More
importantly, the observer retained zero `inflight -> done` endpoints.
Every corridor endpoint was `absent -> absent`, `done -> done`, or
`inflight -> inflight`. The experiment therefore lacks the precommitted
positive completion-transition witness and cannot attribute its lower
maximum to the intervention.

No cyclic-GC completion overlapped the observer. Prepare/native/materialize/
controller-residual p95/max is respectively
`0.0073/0.0777`, `0.0585/0.5103`, `0.0812/0.7891`, and
`0.0746/0.5077 ms`.

## Physical Safety Boundary

The canonical first contact occurred at frame 1,299. The finite viability
kernel exhausted at frame 1,259 and the robust action set at frame 1,290,
providing positive warning leads of 40 and 9 frames. All 18 contacts followed
global-kernel exhaustion. There is no fresh viable-policy/action
contradiction. The 18 versus 12 hit counts are RNG/trajectory/resource
distinct and do not estimate an intervention survival effect.

## Decision

**Rejected:** lowering only the Python corridor parent is not a promotable
B4 correction. It failed the observer p95 and expired-policy gates and
retained no completion-transition witness. The lower maximum alone is
selection-sensitive evidence and may not be promoted.

Do not run the required second pass. Keep the option default-off only for
reproduction; it has no live or physical authority.

The next performance/model checkpoint should not try another ungrounded
worker-priority variant. The stronger joint bottleneck is the issue-thread
ECL callback traversal: incomplete paths remain semantically `UNKNOWN`, and
current Stage-4A spell lookahead still costs p95 up to `0.5360 ms` with
multi-millisecond maxima. The next contract should test exact-state memoized
or transfer-summary traversal while preserving complete/unknown semantics,
the 256-instruction falsifier, epoch/version identity, and fail-closed
lowering. This targets both future-event coverage and issue latency without
claiming that trace-only B4 tails caused hits.

## Evidence

- Raw JSONL: 497,836,057 bytes, SHA-256
  `cedcc97153373bee1758b8dc0a0e4e8ad3879f0c3647091cb27250390a827e12`.
- Deterministic priority audit SHA-256
  `5a2d0884147f12bbd18ce66cae4b9ebdcefd8c9b19034e73fd14731e95716686`.
- Deterministic birth audit SHA-256
  `3bcbf3e25667c9f5f2efa6ba57a4dd2899dafbf10e0207e08562b8a1a6ff2dab`.
- Matching retained session, summary, dossier, comparison, regression,
  death-ledger, and run-note artifacts.
