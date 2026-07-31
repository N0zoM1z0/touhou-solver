# Touhou Solver Workspace Contract

These instructions apply to the entire repository.

## Start Here

Read, in order:

1. `START_HERE.md` — current checkpoint, evidence, commands, and next gate.
2. `STRATEGY.md` — live/shadow/offline/proposed/rejected authority.
3. `notes/review/TH08_LUNATIC_NMNB_RESEARCH_TASKBOOK.md` — research loop and
   prioritized backlog.
4. Only the focused contract named by those files for the task at hand.

`ARCHIVE_INDEX.md` explains how to recover retired history. Archived material
has no current authority and must not be restored merely because an old note
mentions it.

## Mission And Priority

The target is physically validated Sakuya/Remilia Lunatic and Extra NMNB.
Optimize for real reduction of hits and eventual clean-route completion.

Iteration is the default priority:

- solve the current hit, model, planner, or delivery bottleneck;
- prefer the smallest experiment that can falsify the proposed improvement;
- do not spend a turn on broad audits, redundant tests, formatting, schemas,
  or cleanup unless they block that experiment;
- do not call an implementation improvement progress unless a same-root
  offline/native metric or a suitably repeated physical workload connects it
  to global solver performance.

General mechanics come before stage/spell patches. Treat a stage or spell as a
workload/counterexample, not a planner identity. A local exception is allowed
only after a general solution has been tried and evidence shows the exception
is physically necessary.

## Evidence And Reverse Engineering

Label conclusions **observed**, **inferred**, or **hypothesized**.

The shipped TH08 program, retained native traces, and the connected IDA
database are primary evidence. For a key native semantic, compare the relevant
external decompilation/reimplementation repositories when useful, but recheck
the shipped instructions, dataflow, callers/callees, and runtime behavior.
Inherited IDA names, types, comments, and pseudocode labels are hypotheses.
Correct misleading IDA annotations and record material address/type changes.

Do not use REA in this workspace. Use IDA Pro MCP and bounded native probes.
Runtime gameplay sensing uses native state; screenshots are only for
bootstrap/menu checks.

## Model And Control Authority

Before a major model, planner, or actuator change, state:

- physical objective and hard constraints;
- observations available at each decision;
- complete action/no-write semantics;
- uncertainty, transition, horizon, and resource state;
- deadline, publication version, fallback, and falsifier.

The current compact contract is `notes/CURRENT_SOLVER_CONTRACT.md`.

Non-negotiable rules:

- a policy may condition only on observations available at its decision;
- merge hidden branches that share the next observation before maximizing;
- cadence and command pickup delay are distinct uncertainties;
- held desired input is not native active input;
- selecting the held complete mask is no-write: it samples no new delay and
  preserves a pending command;
- `enemy_manager_frame` may freeze while held input still moves the player;
- action-diverged branches may not reuse a recorded future or forced-equal RNG;
- signed clearance is authoritative; one occupancy bit per cell is not;
- Python/native parity proves implementation parity, not physical validity;
- timeout leaves work unresolved; it never proves losing or winning;
- exact witnesses, shadow guidance, and live action authority are separate;
- survival is hard; Power, damage, collection, position, and score are
  objectives only inside the viable set.

Physical input is hard no-Bomb. Never emit bit `0x02` without an explicitly
authorized experiment.

## Architecture

- Reusable control/planning: `scripts/touhou_control/`
- TH08 live orchestration: `scripts/th08_live/` and
  `scripts/th08_live_dodge_agent.py`
- Native/runtime adapters: `scripts/th08_runtime/`
- Offline analysis and reports: `scripts/analysis/`
- Benchmarks: `scripts/benchmarks/`
- Explicit build/probe/capture entrypoints: `scripts/tools/`

Keep TH08 addresses, layouts, ECL details, masks, and movement constants out
of game-neutral modules. Preserve one explicit physical-frame contract.
Windows tools under `scripts/tools/` must prepend `scripts/` to `sys.path`.

## Iteration And Tests

During research, run import smoke plus only affected focused tests. Add the
smallest deterministic regression for an understood semantic failure. Do not
run broad corpus, performance, native, Windows, or physical gates merely
because code changed nearby.

Use discovery because `tests/` is not a package:

```bash
PYTHONPATH=scripts python3 -m unittest discover -s tests \
  -p 'test_relevant_file.py'
```

Run complete Linux discovery once at a verified code checkpoint:

```bash
PYTHONPATH=scripts python3 -m unittest discover -s tests -p 'test_*.py'
```

Run the Windows UNC gate only for Windows/process/input/parser/native changes
or immediately before physical promotion. The exact loader is in
`START_HERE.md`. Never run Linux and Windows performance gates concurrently.
Keep the independent scalar Python oracle independent.

Record every native hit, unexpected Bomb, stale issue, missed transition,
noncausal policy, or concrete model failure in
`notes/counterexamples/CE-0220-0269.md`. Keep only compact evidence needed to
reproduce the conclusion.

## Physical Validation

Physical play is sparse but mandatory:

- use focused Stage 3, 4A, 5, or Final-B trials for a named hypothesis;
- rotate workloads so improvements do not overfit one stage or RNG root;
- after a material integrated improvement, run one fresh full Lunatic Route-2
  game-start diagnostic;
- require repeated clean passes before NMNB acceptance.

Before injection verify executable identity, foreground ownership, route,
difficulty, gameplay state, no-life-decrement patch, and hard no-Bomb.
F8 starts, F9 stops, and F10 exits. Monitor the exact Windows process and
trace growth; release all keys on every stop/error. Do not leave TH08,
controller, supervisor, replay runner, or Windows test processes running.

Retain compact provenance, hits/Bombs/resources, first hit, stage/phase
attribution, timing, and replay identity. The first hit of a fresh attempt is
the canonical causal witness. Different-RNG aggregate counts are
observational, not causal A/B evidence.

Use `.agents/skills/th08-run-and-retain-physical-trial` only when the user
explicitly authorizes gameplay. No audit/checkpoint/test skill is required for
ordinary focused research.

## Repository Hygiene

Treat this as an independent Git repository. Preserve unrelated user changes.
Make one focused English commit at each verified research checkpoint.

Do not commit executables, raw JSONL, screenshots, daemon logs, caches,
credentials, native build output, or `archive/`. Keep the two newest compatible
local replay-capable raw bundles for each active workload until newer compact
evidence exists. Record material removals.

If current documents disagree, reconcile against code and retained evidence
and update every affected current source in the same checkpoint.
