# Feasibility-First Stage-6B Physical Contention Gate

Date: 2026-07-26

Status: the bounded candidate verifier is accepted as an explicit
**shadow-only measurement service** when restricted to Boolean-losing roots.
It has no input authority. The earlier every-root service is rejected.

## Question

The unrestricted belief solve can take hundreds of milliseconds or seconds,
while many roots admit a much cheaper exactly verified restricted policy. The
question is whether a feasibility-first portfolio can:

1. produce a sound attainable lower bound for the current exact public root;
2. arrive before input issue often enough to be useful; and
3. run beside sensing, Boolean publication, and local planning without
   increasing their latency or action lag.

This experiment does **not** ask whether the 32-frame finite model is already
an accurate complete model of TH08. It asks whether candidate verification is
a correct and physically deliverable component inside that declared model.

## Formal Contract

For one immutable Boolean policy version \(v\), let \(P_v\) contain the axes,
clearance volume, action set, delay support, and movement configuration.
The public query root is

```text
r = (phase, row, column, observed_action,
     pending_action, remaining_delay_support)
```

with recursive decision-cadence support `K = {4, 5, 6}` and horizon
`H = 32` frames. The exact delivery key is `(v, r)`. A result computed for
another version, lattice cell, phase, observed action, pending action, or
remaining-delay support is a miss.

For each native action `a_j`, candidate `pi_j` permits every action at the
public root, then restricts all later control decisions to stationary
continuation `a_j`. The belief recurrence still:

- branches every admitted pickup-delay and cadence outcome;
- merges indistinguishable remaining-delay histories before the next
  controller maximization;
- preserves hold/no-write semantics; and
- evaluates all public-root actions.

An exactly completed candidate therefore supplies an attainable per-action
lower label `L_j(a)`. Across completed candidates,

```text
L_portfolio(a) = max_j L_j(a)
```

is attainable because choosing both the public-root action and its retained
candidate witness is part of the public decision. A positive full-horizon
label proves modeled feasibility. It does not prove unrestricted optimality,
unique best action, physical hazard completeness, or route survival.

The 12-ms aggregate budget is a conservative service policy, not a hard
preemptive wall-clock guarantee. The implementation checks the remaining
budget between candidates and gives the in-flight native candidate the
remaining deadline rounded up to one millisecond. Completed labels remain
valid; timed-out and unvisited candidates contribute nothing. Thus:

- `feasible` is a completed attainable witness;
- `candidate_exhausted` means every stationary candidate completed without a
  full-horizon positive label;
- `budget_exhausted` means some completed lowers exist but some candidates
  remain unresolved; and
- `timeout`/`error` supplies no result.

Neither exhaustion status proves unrestricted losing. Only the exact
physical-observation upper threshold, completed against the same root and
lower incumbent, can make that claim.

## Implementation

- `scripts/touhou_control/policy_synthesis.py` supports an aggregate
  between-candidate budget while retaining completed exact lower labels and
  explicitly listing unvisited candidates.
- `scripts/touhou_control/candidate_verifier_service.py` owns one
  below-normal-priority worker. It keeps at most one running and one newest
  queued root, invalidates obsolete work, and exposes nonblocking exact-key
  lookup only.
- `scripts/th08_corridor_runtime.py` constructs the exact current public root
  only after Boolean policy publication.
- `scripts/th08_live_dodge_agent.py` gates the v2 service to available
  Boolean-losing roots, submits immediately before local planning, and looks
  up immediately before input. Every result is telemetry only; a miss falls
  back to the unchanged Boolean policy plus the fresh local hard certificate.
- `scripts/analysis/feasibility_first_capsule_audit.py` replays the candidate,
  threshold, and targeted-refinement layers offline.
- `scripts/analysis/candidate_verifier_shadow_audit.py` separates label
  computation from issue-time delivery and whole-controller contention.
- `scripts/tools/audit_raw_capture_bundle.py` parses the complete JSONL,
  opens every capsule, validates references, and hashes the replay bundle
  before retention cleanup.

## Offline Stage-6B Capsule Evidence

These are observed results for two RNG-distinct complete Stage-6B captures.

| Capture | 32-root classification | Candidate median/p95/max |
| --- | --- | ---: |
| `000654` | 20 exact losing, 11 candidate feasible, 1 refined feasible | 2.13 / 6.75 / 12.37 ms |
| `004142` | 20 exact losing, 11 candidate feasible, 1 refined feasible | 2.22 / 8.09 / 10.21 ms |

The `000654` hard threshold reached 265.77 ms on one root. Targeted action
columns then raised its lower label from 27 to 32 frames with positive margin
and certified optimality. This is a direct counterexample to treating
stationary-candidate exhaustion as unrestricted losing.

Under the live-like `10 ms/candidate, 12 ms aggregate` losing-only budget:

- `000654`: 29 candidate exhausted, one budget exhausted, two candidate
  feasible; none of the 23 selected pre-hit roots was candidate feasible.
- `004142`: 23 candidate exhausted, two budget exhausted, seven candidate
  feasible; all seven were selected pre-hit roots.

The two cohorts show both sides required by the gate: the cheap class often
finishes, and it sometimes finds a full-horizon witness that coarse Boolean
viability called losing. They do not show that a candidate action would have
prevented a native hit.

## Physical Shadow A/B

The baseline and both shadow runs completed Lunatic Stage 6B, used hard
no-Bomb, retained all hit windows, and had no runtime/JSON/manual-rearm
failure. Hit totals are RNG-distinct discovery outcomes, not a causal A/B.

| Metric (median/p95) | Baseline `000654` | Every-root v1 `004142` | Losing-only v2 `011639` |
| --- | ---: | ---: | ---: |
| Decisions / hits | 14,339 / 23 | 12,607 / 33 | 14,652 / 26 |
| Exact delivery | n/a | 8,004 / 12,220 = 65.50% | 6,192 / 6,618 = 93.56% |
| Queue replacement / stale completion | n/a | 205 / 1,099 | 0 / 0 |
| Read ms | 12.77 / 17.86 | 13.77 / 19.54 | 12.10 / 17.09 |
| Local plan ms | 21.20 / 42.09 | 26.46 / 51.93 | 21.85 / 38.95 |
| Full iteration ms | 45.89 / 72.10 | 53.11 / 86.07 | 44.88 / 67.42 |
| Action lag frames | 2 / 4 | 3 / 5 | 2 / 4 |
| Decision cadence frames | 3 / 5 | 4 / 6 | 3 / 5 |
| Boolean solve ms | 100.31 / 427.16 | 110.44 / 453.79 | 95.02 / 421.61 |
| Viability induction ms | 70.68 / 411.43 | 79.57 / 436.86 | 69.54 / 407.96 |
| First policy age frames | 3 / 9 | 4 / 10 | 3 / 9 |

Observed v2 details:

- only the 6,618 available Boolean-losing roots were submitted; 7,661 viable
  roots were explicitly skipped;
- the worker completed all 6,618 revisions with 0 replacement and 0 stale
  completion;
- outcomes were 949 feasible, 899 complete candidate exhausted, 4,524
  budget exhausted, and 7 timeout;
- candidate queue median/p95 was `1.41/7.13 ms`, computation
  `13.46/19.10 ms`, submit `0.0045/0.0554 ms`, and lookup
  `0.0140/0.0221 ms`;
- 941 delivered results contained a completed full-horizon witness;
- all 26 native contacts followed Boolean-kernel exhaustion; causes were 18
  modeled committed-prefix collisions, five bullet overlaps, one laser
  overlap, one multiple-hazard overlap, and one residual
  sensor-gap/unmodeled case.

## Interpretation

**Observed:** every-root v1 materially slowed the controller even though
submit and lookup themselves were cheap. The background worker contended for
CPU while Boolean viability and local planning were active, accumulated
obsolete roots, and raised median action lag from two to three frames.

**Observed:** losing-only v2 removed the queue pathology and recovered the
baseline latency envelope. Its full-iteration median was 2.2% below baseline,
action lag/cadence were identical, and policy publication age was identical.
The exact-key result was already available at issue time on 93.56% of eligible
roots.

**Inferred:** candidate feasibility is no longer blocked by cross-version
cold start on this workload when work is restricted to losing roots. The
important change is admission control and a bounded exact lower, not faster
lookup or unsafe memo reuse.

**Not established:** v2 does not improve survival because it has no action
authority and the three hit totals use different RNG histories. It also does
not show that 32 frames, current future-hazard coverage, or stationary
continuations are sufficient for route survival.

## Decision And Next Gate

1. Keep every-root candidate shadow rejected.
2. Keep losing-only v2 available behind explicit
   `--candidate-verifier-shadow`, with zero action authority.
3. Do not promote `candidate_exhausted` or `budget_exhausted` to losing.
4. The offline counterfactual and explicit publication-object steps are now
   implemented. Publication retains the immutable version, full augmented
   root, root action, causal witness, label, deadline, and the already
   computed all-action hard certificate. See
   `CANDIDATE_WITNESS_PUBLICATION_CONTRACT_20260726.md`.
5. Stage-4A `100451` supplied a clean outside-Stage-6B delivery/integrity
   shadow; Stage-4A `103856` supplied helper timing but is contaminated by the
   rejected 50-ms manager-frame guard. Neither grants action authority.
6. The remaining candidate gate is a fresh uncontaminated post-rollback
   non-Stage-6B shadow with alternate-action certificates and clean
   CPU/delivery/policy-age/action-lag comparison. Keep the current controller
   authoritative until that gate and the separate CE-0120 input-clock
   boundary are resolved.

## Retained Evidence

- `artifacts/viability_audit/stage6b_20260726_000654_feasibility_first.json`
- `artifacts/viability_audit/stage6b_20260726_000654_budgeted_losing_candidates.json`
- `artifacts/viability_audit/stage6b_20260726_004142_feasibility_first.json`
- `artifacts/viability_audit/stage6b_20260726_004142_budgeted_losing_candidates.json`
- `artifacts/viability_audit/stage6b_20260726_004142_candidate_verifier_shadow.json`
- `artifacts/viability_audit/stage6b_20260726_011639_candidate_verifier_shadow_v2.json`
- all three compact run dossiers and death ledgers
- raw-bundle audits with bundle hashes:
  `13a2cd9721dfbbb5d64cdef2ef011fe9c56347f86afcd6b74df57e4bb15663cd`,
  `af492097179021756a593133dbccf7ed1080c7f2e9e0c1e3041cc0a988ee8304`,
  and
  `9e8af717c548dc6456d471c15ac2be9777f755d7b94bc3fc6067e4b289b38a77`.

The two newest complete replayable raw bundles retained locally are `004142`
and `011639`. The older complete `000654` raw bundle may be removed after this
note and its compact/hash evidence are committed.
