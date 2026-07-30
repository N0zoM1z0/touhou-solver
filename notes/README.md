# Touhou Solver Notes

This is the navigation index for repository evidence. It does not replace
`../START_HERE.md`, `../STRATEGY.md`, or any formal contract.

## Current Entry Points

- [Current handoff](../START_HERE.md): exact checkpoint, authority boundary,
  retained workloads, commands, and next gate.
- [Strategy ledger](../STRATEGY.md): live, shadow, proposed, rejected, and
  retired strategies.
- [Chronological research index](RESEARCH_LOG.md): daily evidence shards;
  append to the current date routed there.
- [Counterexample index](COUNTEREXAMPLES.md): durable failure ranges; append
  to the current CE range routed there.
- [Consolidated roadmap](review/CONSOLIDATED_RESEARCH_AND_REFACTOR_ROADMAP_20260727.md):
  agreed research/refactor order.
- [Native-to-solver audit](review/TH08_NATIVE_TO_SOLVER_READ_ONLY_AUDIT_20260729.md):
  shipped-IDB/source semantic findings, reproductions, and bounded
  performance review.
- [Lunatic NMNB review and roadmap](review/LUNATIC_NMNB_PROGRAM_REVIEW_AND_ROADMAP_20260729.md):
  reconciled current status, authority impact, implementation dependencies,
  and physical acceptance ladder.
- [Notes migration plan](review/NOTES_INFORMATION_ARCHITECTURE_AND_MIGRATION_PLAN_20260728.md):
  topology rationale, preservation digests, and migration gates.
- [Launch and UNC audit](review/LAUNCH_AND_UNC_WORKFLOW_AUDIT_20260729.md):
  verified one-shot commands, preflight, quoting, and cleanup boundaries.
- [Native replay physical falsification](operations/NATIVE_REPLAY_PHYSICAL_FALSIFICATION.md):
  repeatable shipped-runtime hypothesis checks, evidence boundaries, and
  retention/cleanup protocol.
- [Final-B SEM-SCALE live delivery gate](operations/FINALB_SEM_SCALE_LIVE_DELIVERY_GATE.md):
  preregistered original-game Stage-6B transport/exact-transition boundary,
  strict report, and stop conditions.
- [Runtime report retention and emission audit](review/RUNTIME_REPORT_RETENTION_AND_EMISSION_AUDIT_20260729.md):
  required outputs, duplicate suppression, and reviewed raw-cleanup candidates.
- [Reusable agent skills](review/REUSABLE_AGENT_SKILLS_20260729.md):
  installed repo-scoped workflows and authority boundaries.

## Responsibility Directories

| Directory | Responsibility |
| --- | --- |
| [research log](research_log/) | Source-preserved chronological evidence, one shard per date. |
| [counterexamples](counterexamples/) | Source-preserved durable failures, split by CE range. |
| [G5 research](research/g5/README.md) | Future-hazard, ECL, birth, source, and auxiliary-VM contracts/results. |
| [Stage-5 combat](research/stage5_combat/README.md) | Enemy HP/damage, exposure, Power, and survival-filtered combat progress. |
| [architecture](architecture/README.md) | Refactor seams, native/Python boundaries, and implementation performance. |
| [foundations](foundations/README.md) | Durable game, solver, hazard, viability, and strategy models. |
| [operations](operations/README.md) | Practice and unattended-run protocols. |
| [physical runs](runs/) | Compact run reviews; raw JSONL remains local and ignored. |
| [reviews](review/README.md) | Consolidated/internal audits and migration plans. |

## Active Formal Chain

General control formalizations deliberately remain at stable root paths:

1. [augmented pipeline robust control](AUGMENTED_PIPELINE_ROBUST_CONTROL_FORMALIZATION_20260725.md);
2. [pipeline root and hazard coverage](PIPELINE_ROOT_AND_HAZARD_COVERAGE_CONTRACT_20260727.md);
3. [complete-mask issue action](COMPLETE_MASK_ISSUE_ACTION_CONTRACT_20260727.md);
4. [asynchronous ordered input publication](ASYNC_ORDERED_INPUT_PUBLICATION_CONTRACT_20260730.md);
5. [immutable future body/flag/geometry schedule](IMMUTABLE_FUTURE_BODY_FLAG_GEOMETRY_SCHEDULE_CONTRACT_20260730.md);
6. [dual-bound query-local refinement](DUAL_BOUND_QUERY_LOCAL_REFINEMENT_CONTRACT_20260727.md);
7. [budgeted belief refinement](BUDGETED_BELIEF_REFINEMENT_20260725.md);
8. [exact augmented partial survival](EXACT_AUGMENTED_PARTIAL_SURVIVAL_WITNESS_CONTRACT_20260727.md);
9. [frozen manager/input clock](FROZEN_MANAGER_INPUT_CLOCK_BOUNDARY_20260726.md);
10. [pre-loss continuation reserve](PRELOSS_CONTINUATION_RESERVE_CONTRACT_20260726.md); and
11. [exact-version supplemental publication](EXACT_VERSION_ASYNC_SUPPLEMENTAL_PUBLICATION_20260726.md).

`START_HERE.md` remains authoritative for the exact subset and reading order
required by the current checkpoint.

## Placement Rule

New notes go to the narrowest responsibility directory. Keep only canonical
indexes and active general formal contracts at the root. A physical workload
review goes under `runs/`; a chronological checkpoint goes in the current
daily research shard; and a durable failure goes in the current
counterexample range.

Historical path literals inside legacy-marked shards describe the repository
at that checkpoint and are intentionally not rewritten. Current documents use
the new paths.
