# Boolean-First Publication And Pending-Command Survival

Date: 2026-07-25

## Decision

The live global planner now publishes its coarse Boolean viability policy
before optional losing-state survival labels are computed.  Post-publication
labels are a distinct shadow policy and have no action authority.  A separate
phase-exact scalar/native oracle now represents the game-observed input, one
older pending desired command, its remaining-delay support, and the delay
support of the newly selected command.

The publication/delivery change passes its focused Stage-5 gate.  The label
semantics do not pass a live-promotion gate: both retained physical runs show
that the issued desired action and game-observed active input often differ,
and the exact oracle shows that pending state materially changes winning
classification and losing-action ranking.

## Evidence Labels

- **Observed:** values read directly from retained traces, native state,
  physical-run dossiers, or deterministic differential artifacts.
- **Inferred:** causal interpretation supported by more than one observed
  relation but not directly exposed as one native variable.
- **Hypothesized:** a proposed correction that has not passed physical
  authority gates.

## Implemented Contract

### Boolean publication

`CorridorPlan.survival_query_problem` retains immutable axes, signed-clearance
volume, actions, delay support, and viability configuration.  It is retained
while the ordinary Boolean policy is built, but no survival induction runs on
the Boolean publication path.

`solve_postpublished_survival()` consumes the already published Boolean
`viable` and `safe_action_masks` arrays.  The native
`touhou_losing_survival_labels_v1` recurrence skips Boolean-winning states and
computes lexicographic guaranteed-survival/bottleneck labels only for losing
states.  It verifies that the reused Boolean arrays remain identical.

The result is stored in
`CorridorSolution.postpublished_survival_policy`; it is never attached to
`CorridorPlan.survival_policy` and never enters
`assemble_local_policy_guidance()`.  Physical shadow computation requires the
explicit `--postpublished-survival-shadow` option.

### Publication isolation

The first shadow implementation serialized labels on the one global corridor
executor.  The accepted shadow scheduler instead uses:

- one executor for the authoritative Boolean solve;
- one separate executor for post-publication labels; and
- one native worker for labels, versus the Boolean kernel's ordinary worker
  budget.

This is publication isolation, not proof that a concurrent shadow has zero
CPU cost.  Delivery and local-latency evidence remain required.

### Exact input-pipeline state

`touhou_control.query_survival` defines one exact physical-frame state:

```text
(frame, lattice cell,
 observed active action,
 older pending desired action or none,
 robust remaining frames before the older command is visible)
```

At a decision epoch, every new selected action is evaluated over its current
end-to-end delay support.  A branch follows:

```text
observed active -> older pending -> newly selected
```

If the new command cannot become visible during the current eight-frame
decision interval, it is carried into the successor as the next pending
command.  The scalar implementation is the independent oracle.  The memoized
native `touhou_query_local_survival_v1` implementation returns the same state
label, action labels, best-action mask, and evaluated-state count.

`AdaptiveControlDelay.pending_estimate()` exposes the desired mask,
remaining-frame support, snapshot/issue ages, and overdue status.  An overdue
command is not silently promoted to active; the game-observed native input is
the active-action evidence.

The successor boundary uses inclusive activation: when an older pending
command's remaining delay equals the decision interval and the newer command
is later, the older command is active in the successor. The focused
`test_pending_activates_at_successor_boundary_before_later_command` regression
protects this previously missed equality case in both scalar and native
recurrences.

## Deterministic Differential

Retained artifact:
`artifacts/benchmarks/postpublished_survival_20260725.json`.

- **Observed:** 24 structured full Stage-5-size
  `24 x 27 x 81` clearance problems produced zero losing-state frame, margin,
  or best-mask differences between fused induction and post-publication
  induction.
- **Observed:** 64 randomized small pending-pipeline problems produced zero
  scalar/native differences.
- **Observed:** Boolean median/p95 was `282.88/310.69 ms`, fused
  `353.88/379.78 ms`, and single-worker post-publication labeling
  `71.33/89.36 ms`.
- **Interpretation:** this accepts numeric recurrence parity.  It does not
  authorize dense labels at an off-layer, pending-command live query.

## Physical Delivery Experiment

All three runs are hard no-Bomb complete Stage-5 practice runs.  Their hit
counts are shown only for provenance; different RNG and post-hit resource
states prevent treating the differences as survival effects.

| Run / scheduler | Hits | Boolean solve median/p95 ms | First policy age median/p95 f | Query age median/p95 f | Pending/queryable/expired | Local read median/p95 ms | Local plan median/p95 ms | Action lag median/p95 f |
| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| `103655`, Boolean-only baseline | 34 | 126.43/414.08 | 6/12 | 11/27 | 32/6744/14 | 17.00/23.39 | 31.06/71.46 | 3/7 |
| `122624`, labels serialized on global worker | 20 | 115.86/408.58 | 4/10 | 10/25 | 36/8075/34 | 12.81/17.79 | 22.43/42.51 | 3/5 |
| `125037`, separate executor, one label worker | 18 | 114.91/425.22 | 4/10 | 11/27 | 38/7771/15 | 13.08/18.18 | 22.71/42.74 | 3/5 |

The serialized `122624` run labeled 1,303 policies at
`79.05/131.29 ms` median/p95, but expired decisions rose from 14 to 34.  The
isolated `125037` run labeled 1,359 policies at `150.43/284.57 ms`; label
attachment moved later to `11/19` frames, while authoritative expiry returned
to 15 and Boolean/local latency stayed at the comparison level.  Both runs
had zero Boolean/label parity failures.

- **Observed acceptance:** the isolated scheduler removes the serialized
  label-delivery regression.
- **Observed limitation:** label completion is intentionally later and has no
  input authority.
- **Not claimed:** `18 < 20 < 34` is not a survival improvement.

The `125037` run completed `2..43338`, recorded 7,921 decisions and 18 native
hit edges, passed hard no-Bomb, reached `route_complete`, and left no TH08 or
control process running.  Its first fresh hit was a modeled committed-prefix
collision.  The other 17 hits remain post-respawn discovery evidence.

## Active-Input And Pending-State Differential

Compact exact artifacts:

- `artifacts/viability_audit/stage5_20260725_122624_pending_pipeline.json`
- `artifacts/viability_audit/stage5_20260725_125037_pending_pipeline.json`

### Complete trace aggregates

| Run | Boolean queries | Issued/observed active mismatch | Pending / overdue | Labeled queries | Issued-vs-observed state flips | Legacy false winning / false losing |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `122624` | 8,077 | 754 | 782 / 113 | 5,562 | 9 | 8 / 1 |
| `125037` | 7,772 | 805 | 854 / 158 | 4,917 | 9 | 5 / 4 |

Here “legacy” is the authoritative Boolean query using the last issued desired
action.  The post-publication shadow queries the same source/layer policy with
the game-observed action.  Nine state-classification flips in each
RNG-distinct run are therefore direct evidence that desired and active input
are not interchangeable.

### Phase-exact cohorts

Each artifact retains a deterministic 16-query cohort: all positive-label
issued/observed classification flips first, then pending-command coverage
across layer phases, followed by high-survival issued-outside-label cases.
The cohort is diagnostic and deliberately biased; it is not a population
rate.

- **Observed, `122624`:** replacing phase-exact observed-only state with the
  pending pipeline changed 13/16 best-action sets and 4/16 winning
  classifications.
- **Observed, `125037`:** it again changed 13/16 best-action sets and 6/16
  winning classifications.
- **Observed:** selected native query time had p95/max
  `86.13/183.04 ms` and `68.33/250.76 ms` for the two cohorts.  The sparse
  exact oracle is not an issue-time live backend.

At `122624` frame 528, the dense source-layer label used observed `stay` and
reported 18 guaranteed frames with only `stay` best.  Exact phase with
observed input and no pending command reported 14 frames.  Adding the older
pending `left_fast` command with remaining support `(1, 2)` reduced the
guarantee to two frames and tied every newly selected action: the imminent
branch was already outside new-command control.  The live controller issued
`left_fast`.  This is a concrete pipeline-state counterexample, not a
stage/spell tuning argument.

## Interpretation

- **Observed:** Boolean-first publication and independent low-worker shadow
  scheduling meet the focused delivery gate.
- **Observed:** dense source-layer labels omit exact phase and pending-command
  state; the omission changes both Boolean classification and losing-action
  ranking.
- **Inferred:** the principal remaining S09 blocker is now input-pipeline and
  phase semantics, not inline Boolean publication cost.
- **Hypothesized:** a reachable-tube or augmented event-phase recurrence can
  amortize pending-aware labels enough for issue-time use.

Do not promote post-publication labels merely because the isolated scheduler
passes.  A live losing-state order must consume a certificate for the action
that can physically be active, not the last desired action, and must preserve
fresh local hard-vector authority.

## Promotion Gate

Before repeated action-authority Stage-5 A/B:

1. represent exact layer phase plus observed/pending/remaining-delay state in
   the queried policy or a sound conservative equivalent;
2. make the query incremental, reachable-tube, or precomputed enough that it
   does not worsen policy expiry, local p95, or action lag;
3. reproduce the two retained 16-query cohorts plus canonical decision 1,680
   and cross-stage losing witnesses with scalar/native parity;
4. keep ordering `fresh hard vector -> guaranteed survival frames ->
   bottleneck clearance -> control reserve -> recovery distance`;
5. run multiple fresh Stage-5 samples and then another stage, reporting
   delivery separately from survival.

Until then, the live path remains coarse Boolean viability plus fresh local
certification.  Post-publication labels and the pending pipeline remain
shadow/offline diagnostics.
