# TH08 Reverse Engineering Workspace

This directory is the persistent workspace for the ongoing TH08 investigation.
All new notes, address maps, scripts, and generated analysis artifacts belong
under this directory.

## Version Control

This directory is an independent Git repository. Commit scripts, tests, notes,
IDA-derived address maps, and compact generated summaries at each verified
checkpoint. Large live JSONL captures, screenshots, daemon logs, and Python
caches remain local through `.gitignore`; keep a compact tracked summary for
any raw capture cited by a conclusion or regression test.

## Layout

- `notes/`: curated findings and chronological research logs
- `scripts/`: importable models, adapters, and live entry points
- `scripts/analysis/`: offline differentials, reports, dossiers, regressions
- `scripts/benchmarks/`: offline timing and ablation experiments
- `scripts/tools/`: explicit build, probe, patch, and capture entry points
- `scripts/touhou_control/`: game-neutral online control components
- `tests/`: unit and retained-counterexample regression tests
- `artifacts/`: generated reports and small derived metadata (no game binaries)

## Current Investigation

The repository has progressed from static danmaku recovery to a physical
robust-control research system. The live controller uses native-state sensing,
an issue-time local collision certificate, and coarse Boolean viability under
hard no-Bomb practice. Augmented belief solves, stationary candidates,
survival labels, damage objectives, and exact witness publication remain
offline or shadow-only.

The highest-priority open problem is no longer raw clearance performance. It
is the physical/information boundary at post-spell transitions:
`enemy_manager_frame` can freeze while held input continues moving the player
(CE-0120), and the attempted 50-ms detector was physically rejected
(CE-0121). Candidate verification also demonstrates that “Boolean-losing” is
not equivalent to unrestricted losing, but candidate wins do not yet have live
action authority.

Do not use this README as a detailed handoff:

- `AGENTS.md` is the binding durable contract.
- `START_HERE.md` is the exact current checkpoint, authority table, open
  problems, retained evidence, commands, and next gate.
- `STRATEGY.md` is the live/shadow/rejected strategy ledger.
- `notes/RESEARCH_LOG.md`, `notes/COUNTEREXAMPLES.md`, design notes, and run
  notes retain derivations and history.

The reconstructed ECL, bullet, laser, enemy, item, movement, damage, and route
models remain available under `scripts/`, `notes/`, and `artifacts/`; they are
research inputs, not proof that Lunatic or Extra has been physically accepted.

## Reproduce

Commands below assume the repository root as the current directory.

```bash
# Quick research checkpoint.
PYTHONPATH=scripts python3 -m unittest discover -s tests -p 'test_*.py'

# Inspect the archive/ECL tools without changing game state.
PYTHONPATH=scripts python3 scripts/th08_pbgz.py --help
PYTHONPATH=scripts python3 scripts/th08_ecl.py info artifacts/decoded

# Inspect offline report entry points.
PYTHONPATH=scripts python3 scripts/analysis/th08_run_dossier.py --help
PYTHONPATH=scripts python3 \
  scripts/analysis/audit_pipeline_formal_correctness.py \
  /tmp/pipeline-formal-quick.json
```

Physical-control commands, WSL/Windows differences, exact executable identity,
retained bundles, and cleanup rules are intentionally centralized in
`START_HERE.md`. Do not reconstruct a live command from this README.

The curated static model and address map remain in
`notes/DANMAKU_SYSTEM.md`; `notes/SOLVER_MODEL.md` is historical architecture
context, while `START_HERE.md` and the active formal notes define current
authority.
