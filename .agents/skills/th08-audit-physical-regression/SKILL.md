---
name: th08-audit-physical-regression
description: Diagnose a TH08 physical hit or survival regression against retained baselines and decide whether rollback is causally justified. Use when a run gets materially worse, checkpoints disagree, aggregate hits rise, or the user asks what change introduced a regression.
---

# Audit A TH08 Physical Regression

Separate causal code changes from RNG, workload, observer, resource, and
post-respawn coupling before recommending rollback.

## Fix The Comparison

1. Read `AGENTS.md`, `START_HERE.md`, `STRATEGY.md`, the relevant run notes,
   and
   `notes/research/g5/STAGE5_EIGHT_HIT_CHECKPOINT_REGRESSION_AUDIT_20260729.md`.
2. Identify exact code checkpoints, physical-code checkpoints, workload,
   route/team/difficulty/stage/phase, immutable versions, flags, and retained
   raw/compact evidence.
3. State whether samples are paired, same-seed, same-entry-state,
   phase-matched, workload-matched, or merely observational.

## Trace Causality Before Aggregates

1. Compare the canonical first hit of each fresh attempt before total hits.
   Treat later contacts as useful but coupled through respawn, Power,
   position, damage, timing, and route state.
2. Attribute hits by phase and compare entry resources, position, boss/enemy
   progress, cadence, issue/no-write behavior, sensor health, viability
   exhaustion, and foreground/transition contamination.
3. Diff action-authority paths separately from optional observers, tracing,
   reporting, refactors, and default-off services.
4. Trace changed values to the issued complete mask and physical frame. Do not
   blame a later observer for a hit that precedes its first envelope or
   activation.
5. Compare only control-equivalent populations. Reject an all-stage versus
   phase-only performance comparator unless a new contract justifies it.

## Decide The Next Experiment

1. Classify each candidate cause as ruled out, supported, unresolved, or
   untestable from retained evidence.
2. Recommend rollback only when a changed authority path has a causal witness
   or a controlled reproduction. Aggregate worsening alone is insufficient.
3. Define the smallest observer-off or single-variable A/B that distinguishes
   the leading causes. Fix checkpoint, flags, entry state, acceptance metric,
   repeat count, and stopping rule.
4. Keep Power, targeting, unfocused shot, combat, and planner changes out of
   the first control unless one of them is the exact variable under test.
5. Retain every outcome, including failed launches and contaminated attempts,
   through `$th08-retain-research-checkpoint`.
