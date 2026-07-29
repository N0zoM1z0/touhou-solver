# G5 Auxiliary Literal Fire-Cycle Runtime Delivery V2 Stage-5 Failure

Date: 2026-07-29

Status: **physical gate rejected**; schema v5/event v2 remain immutable and
have no delivery or action authority

Run: `lunatic_route2_stage5_unattended_20260729_095849`

Code checkpoint: `5ad2bb1`

## Outcome

**Observed:** the supervised Lunatic Stage-5 practice completed frames
`2..42834`, 11,342 decisions, hard no-Bomb, accepted route completion, and
exact process cleanup. Survival was poor: 20 hits at
`[1423, 2119, 7943, 11145, 12293, 13853, 14262, 14654, 23818, 25339,
29734, 30810, 33601, 35022, 35769, 37404, 38151, 38889, 40646, 41266]`.
Phase attribution is 11 nonspell, 2 spell 103, 2 spell 107, 3 spell 111,
and 2 spell 115.

The delivery gate failed before any event lowering:

- one exact runtime-ECL identity and schema-v1 preparation were accepted at
  controller gameplay epoch 0;
- sensor/action discontinuities advanced the controller epoch to 3 before
  spell 107;
- all 142 schema-v5 batches were coherent native transactions at epoch 3;
- all 142 event records failed closed as `runtime_identity_mismatch`; and
- zero request entered the lowerer, exact cache, or independent replay
  oracle.

The strict V2 auditor correctly refuses to construct a passing report from
this workload. The compact failure inventory is
`artifacts/viability_audit/g5_auxiliary_ecl_event_runtime_delivery_v2_stage5_20260729_095849_failure.json`.

## Root Cause

The V2 event layer incorrectly made controller `gameplay_epoch` part of the
runtime *program* equality key. That epoch marks scene/sensor/action
continuity resets. It is not evidence that the loaded Stage-5 instruction
image, runtime base, relocated bytes, or normalized bytes changed.

This conflicts with the earlier accepted runtime-identity contract, which
defines identity equivalence by executable/route/difficulty/stage, runtime
base, image length, relocated digest, normalized digest, and static digest.
The acceptance epoch is provenance for the one-shot observation, not an
instruction-image mutation event.

The failure is still valuable: fail-closed behavior worked and no stale
version was silently lowered. It also proves the fixed V2 gate omitted a
controller-epoch transition case that occurs naturally in hard gameplay.

## Survival Regression Analysis

The 20-hit result is physically unacceptable for handoff, but current
evidence does not attribute all additional hits to the spell-107 observer:

- the first ten hits occurred by frame 25339, before the selected auxiliary
  batch window began around frame 28657;
- the observer performed no event lowering at all;
- decision cadence remained p50/p95 `2/4`, equal to the 11-hit V1 run;
- retained complete Stage-5 runs already span 8–23 hits; and
- schema-v3 auxiliary-batch run `20260728_193820` also had exactly 20 hits
  with 11 nonspell hits.

**Inferred:** uncontrolled pattern/path variation plus the early two-hit
Power-loss cascade is a stronger explanation than schema-v5 cache contention.
This is not proof of no observer effect. V2 added one 5.317-ms preparation on
decision frame 2, and a one-time issue-loop delay can change subsequent
trajectory even when p95 cadence is unchanged.

Therefore the correction must address both observed risks:

1. separate controller observation epoch from immutable program identity; and
2. move exact static instruction validation/materialization before gameplay,
   leaving only a tightly bounded runtime-base bind after identity.

The user-set physical acceptance boundary is stronger than the delivery
timing gate: retain every subsequent run, require corrected Stage 5 to return
to at most 10 hits without hiding intervening failures, and verify the other
Lunatic stages before handoff.

## Immutable Evidence

- raw trace bytes: `438162039`;
- raw trace SHA-256:
  `793ca124d43f1cd543ce4309a79b734e1ce7e6237e8f05f660564f870a858b6f`;
- exact Stage-5 ECL SHA-256:
  `3148f45faf78bd8211a956edcdc353be73d2781995d3dadd36bdca8132f8fe19`;
- executable SHA-256:
  `330fbdbf58a710829d65277b4f312cfbb38d5448b3df523e79350b879213d924`;
- preparation bind/total: `5.251/5.317 ms`;
- replay compact p95/p99/max: `0.678/0.752/0.898 ms`;
- preceding emit p95/p99/max: `1.620/1.907/3.019 ms`; and
- transaction total p95/p99/max: `2.631/3.329/4.006 ms`.

The event-derive timing is not a performance success: it measured only the
fast unavailable path.

## Decision

Reject V2. Do not loosen its epoch gate or reinterpret this trace as a
delivery pass. A separately versioned schema-v6/event-v3 correction must be
contracted and tested before another physical run.
