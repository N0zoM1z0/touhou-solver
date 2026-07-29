# G5 Auxiliary Literal Fire-Cycle Coalesced Delivery V6 Stage-5 Failure

Date: 2026-07-29

Status: exact semantics and one-write composition observed; full delivery
gate and survival rejected

Contract:
`G5_AUXILIARY_LITERAL_FIRE_CYCLE_COALESCED_DELIVERY_V6_CONTRACT_20260729.md`

## Result

**Observed:** run
`lunatic_route2_stage5_unattended_20260729_125453`, from code checkpoint
`3f02ff1`, completed Lunatic Route-2 Stage-5 practice over frames
`2..44053` with 12,039 decisions. Executable identity, route, difficulty,
Sakuya/Remilia team, no-life-decrement patch, foreground ownership, hard
no-Bomb input, accepted artifacts, route completion, and exact cleanup
passed.

The run took 18 hits:

- nonspell: 6;
- spell 103: 2;
- spell 107: 4;
- spell 111: 2; and
- spell 115: 4.

This is outside the fixed single-run maximum of ten and contributes no pass
to the two-consecutive-run requirement.

## Exact Semantic And Composition Evidence

**Observed:** all 186 coalesced schema-v8 envelopes were successful and
ordered `0..185`. There were zero standalone `auxiliary_vm_batch` writes.
The independent decoder recovered canonical inner evidence and replayed all
5,250 requests with zero unknown:

- target 69: 1,304;
- target 72: 1,321;
- target 73: 2,625;
- six valid empty prefixes;
- cache misses: 46;
- persistent hits: 2,413;
- request-local hits: 2,791; and
- evictions: zero.

Canonical-inner/compressed/base64 maximum sizes were
`14026/5362/7152` bytes. Pack p95/p99/max was
`0.642/0.773/1.203 ms`. Event-derive p95/p99/max was
`0.421/0.548/0.672 ms`, and transaction-total p95/p99/max was
`2.933/3.868/9.480 ms`. These gates pass.

V6 therefore physically observes that the selected schema-v8 evidence can be
bound to the same-iteration decision, published without a second auxiliary
write, recovered exactly, and replayed independently. This is trace-only
evidence. It grants no source-completeness, future-geometry, planner, damage,
or action authority.

## Failed And Invalid Timing Gates

The strict V6 report remains failed:

| Boundary | p50 | p95 | p99 | max | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| replay compact | 0.350 | 0.535 | 0.879 | 8.388 | fail |
| coalesced pack | 0.490 | 0.642 | 0.773 | 1.203 | pass |
| evidence plus pack | 2.239 | 3.481 | 4.753 | 9.878 | pass |
| transaction total | 1.736 | 2.933 | 3.868 | 9.480 | pass |
| all decision emit | 1.847 | 4.570 | 6.644 | 18.813 | pass p95 |
| bearing decision emit | 4.535 | 6.633 | 7.544 | 8.898 | reported fail |

**Observed:** decision cadence p50/p95/p99 was `2/4/5` frames versus the
retained baseline's `2/4/4`; the fixed p95 regression gate passes.

**Corrected interpretation:** the V6 contract compares spell-107-only
envelope-bearing decisions against all decisions from run `20260728_200739`.
That baseline population is not phase- or workload-matched. Dense spell-107
decision rows are intrinsically larger and slower than the all-stage
population, so the `bearing_decision_emit_regression = false` result cannot
establish a V6 regression.

The immutable report must remain failed as written; do not silently replace
its comparator. A diagnostic comparison, not a corrected gate, gives:

- V5 exact-batch parent decisions: emit p95/p99
  `6.507/8.443 ms`;
- V6 envelope-bearing decisions: emit p95/p99
  `6.633/7.544 ms`;
- all V5 spell-107 decisions: emit p95/p99
  `6.778/8.311 ms`; and
- all V6 spell-107 decisions: emit p95/p99
  `6.756/8.286 ms`.

These different physical runs suggest that coalescing removed the second
write without a material phase-matched decision-emit regression, but they are
not a controlled A/B result. A new contract/report version must fix the
matched comparator before making that claim.

The replay-compact failure is real under the original fixed limits:
p95 exceeds `0.500 ms` and one `8.388 ms` tail exceeds `3.000 ms`.
Scheduling, allocation, collection, hashing, and inner compression remain
hypotheses; the trace does not attribute the tail. Do not weaken the
historical limit or call the tail solved.

## Survival And Regression Interpretation

**Observed:** the canonical first hit occurs at frame 731 in nonspell, before
the first spell-107 auxiliary envelope. It is classified
`sensor_gap_or_unmodeled_hazard`; every hit follows global viability-kernel
exhaustion.

**Inferred:** V6 auxiliary work cannot be the cause of that first hit or of
the five nonspell hits that precede the first envelope. It may still add
synchronous contention during spell 107. Later contacts are coupled to the
first death through
position, route timing, respawn, and Power loss, so they are not independent
clean-route samples.

The 18-hit aggregate must not be read as a deterministic code regression.
The retained 8-hit checkpoints and current code are compared separately in
`STAGE5_EIGHT_HIT_CHECKPOINT_REGRESSION_AUDIT_20260729.md`.

## Pre-Launch Failure

Attempt `lunatic_route2_stage5_unattended_20260729_125411` failed before the
controller became ready. A shell-escaped Windows argument changed the static
ECL path to `artifactsdecodedecldata5.ecl`. No accepted gameplay trial or
auxiliary evidence resulted. Cleanup completed.

The supervisor now resolves, reads, and SHA-256-validates the immutable ECL
image before any game/process side effect at launch-only checkpoint
`d85cca1`. The canonical WSL command uses a single-quoted absolute UNC path.
See
`notes/review/LAUNCH_AND_UNC_WORKFLOW_AUDIT_20260729.md`.

## Next Gate

Do not rerun V6 unchanged as though its report were authoritative.

1. Preserve the failed V6 report.
2. Fix a new report/contract with a phase- and workload-matched publication
   comparator.
3. Attribute or reduce replay-compact tails without weakening old gates.
4. Separately run current code with all optional observers disabled to
   establish a fresh survival control.
5. Require two consecutive corrected Stage-5 runs at no more than ten hits,
   then Stage 3, other-stage checks, and one complete Lunatic Route-2 run.

The proposed survival-filtered unfocused Sakuya and nonspell damage work
remains separate. It was not exercised in this trial.

## Retained Evidence

- raw trace SHA-256:
  `bee834257bc577299d1ca684383bcc8c0591e3fcc02a8b0e43bf39932fc2a2ca`;
- strict failed report:
  `artifacts/viability_audit/g5_auxiliary_ecl_event_coalesced_delivery_v6_stage5_20260729_125453.json`,
  SHA-256
  `bd64f9d8d88af6d907d316c0c46b743667cbc5e2c1fc6c480e281144c23a25cd`;
- report digest:
  `625ac84d26b3ee4cf90fd75b4664448247a741970d716f739861d871058359ed`;
- compact dossier:
  `artifacts/runtime_reports/lunatic_route2_stage5_unattended_20260729_125453.dossier.json`,
  SHA-256
  `5bfa9c9e2ed550fd8a95aa5afe0adf0b6b44fbac0210714ace3d25430d0e7aeb`;
- normalized session:
  `artifacts/runtime_reports/lunatic_route2_stage5_unattended_20260729_125453.session.json`,
  SHA-256
  `999cc47cddc006999839dffb3e13a20352ffdffc9e5a60db4e3f13fb88d9bd13`;
- run review:
  `notes/runs/lunatic_route2_stage5_unattended_20260729_125453.md`,
  SHA-256
  `253af81bd671e473234008203aee489727b7113318d4a27d75e0317642f500ea`;
- pre-launch failure session:
  `artifacts/runtime_reports/lunatic_route2_stage5_unattended_20260729_125411.session.json`,
  SHA-256
  `c3190690e1b0f2483570f3ea4ab8b252900016e1b5cdf6cfb7fd9f6064df656b`.
