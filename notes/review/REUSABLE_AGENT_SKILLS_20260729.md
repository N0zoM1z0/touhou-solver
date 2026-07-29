# Reusable Agent Skills

Date: 2026-07-29

Status: six repo-scoped skills discovered and structurally validated; five
created by this handoff

## Decision

The repetitive, fragile workflows should become small low-/medium-freedom
skills. The changing planner/research conclusions should remain in
`START_HERE.md`, `STRATEGY.md`, formal contracts, and evidence notes rather
than being copied into a stale skill.

The user selected repository scope. Current official Codex guidance loads
team skills from `.agents/skills` between the current working directory and
the repository root; personal cross-repository skills belong in
`~/.agents/skills`. These workflows are TH08-specific, so all six are
checked into `.agents/skills/` rather than a legacy/internal
`~/.codex/skills` location.

The five handoff workflows were initialized with the OpenAI `skill-creator`
`init_skill.py`. A concurrently present comprehensive native-to-solver audit
skill was preserved without modification. All six have the required
`SKILL.md` plus recommended `agents/openai.yaml` and pass
`quick_validate.py`.

A fresh Codex `0.144.6` app-server
`skills/list(cwds=[repo], forceReload=true)` reports all six with
`scope: "repo"`, `enabled: true`, correct paths, and parsed interface
metadata. This is an actual new-process discovery check, not only a directory
or YAML check. Codex detects skill changes automatically; restart a client
only if its current picker does not refresh. The physical skill was not
forward-tested because this handoff explicitly stopped physical experiments.

Official reference:
[Build skills](https://learn.chatgpt.com/docs/build-skills).

## Installed Skills

### 1. `th08-run-and-retain-physical-trial`

Trigger examples:

- “run Lunatic Stage 5 and retain it”;
- “do a full Route-2 physical gate”;
- “repeat this observer trial safely”.

Degree of freedom: low.

Core workflow:

1. read `AGENTS.md`, `START_HERE.md`, `STRATEGY.md`, and the named contract;
2. resolve exact workload, flags, immutable versions, and acceptance gates;
3. run a no-side-effect preflight for Python, native libraries, BATs, target
   identity, ECL files/hashes, and output paths;
4. launch exactly one non-TTY supervisor;
5. monitor supervisor process, trace growth, foreground, and terminal
   summary without stealing Windows focus;
6. stop/fail closed, release keys, and verify exact process cleanup;
7. retain compact artifacts, raw SHA-256, first-hit witness, Bomb/resources,
   timing, scope, and provenance; and
8. route failures to counterexamples/daily log and create a focused commit.

Bundled resources:

- a deterministic command builder/preflight script that calls existing BATs
  rather than duplicating supervisor logic;
- a short reference mapping workload to the authoritative command in
  `START_HERE.md`;
- no game binary, raw trace, credential, or hard-coded password.

### 2. `th08-run-dual-platform-gates`

Trigger examples:

- “run quick Linux and Windows tests”;
- “validate a native change on both platforms”;
- “run the UNC gate”.

Degree of freedom: low.

Core workflow:

1. choose focused, quick, or explicitly expensive profile;
2. use discovery for tests;
3. use the exact Windows UNC loader, changing only `pattern`;
4. rebuild only affected native targets;
5. run Linux/Windows differential and retained-report immutability checks;
6. report platform, command, count, duration, skips, and digest; and
7. never promote parity into physical-model validity.

Bundled resource:

- one parameterized UNC test runner so agents do not repeatedly hand-write
  fragile nested quoting.

### 3. `th08-retain-research-checkpoint`

Trigger examples:

- “retain this failed run”;
- “align the handoff and commit”;
- “prepare the repo for the next agent”.

Degree of freedom: medium.

Core workflow:

1. classify each conclusion observed/inferred/hypothesized;
2. keep raw bundles local and hash them;
3. run the dossier/report/audit appropriate to the contract;
4. update run note, result note, counterexample shard, daily shard,
   `STRATEGY.md`, roadmap, G-line index, and `START_HERE.md`;
5. reconcile disagreements against code/evidence;
6. check no process is alive and no raw/secret/audit input is staged; and
7. make one focused English checkpoint commit.

Bundled resource:

- an evidence-manifest checker that verifies required compact paths, hashes,
  run ID, session acceptance, cleanup, and raw-bundle presence.

### 4. `th08-audit-physical-regression`

Trigger examples:

- “why did hits regress from checkpoint X?”;
- “compare this run to the best baseline”;
- “should we roll back?”.

Degree of freedom: medium.

Core workflow:

1. identify exact code checkpoints and immutable workload versions;
2. diff action-authority paths separately from observers, reports, and
   refactors;
3. compare the canonical first hit before aggregate hits;
4. compare phase, resource, position, cadence, issue, sensor, and viability
   metrics using control-equivalent populations;
5. treat post-respawn hits as coupled discovery evidence;
6. state whether the comparison is paired, same-seed, phase-matched, or only
   observational;
7. define the smallest observer-off/control A/B that can distinguish causes;
   and
8. recommend rollback only for an identified causal change.

Bundled reference:

- the method and counterexample in
  `STAGE5_EIGHT_HIT_CHECKPOINT_REGRESSION_AUDIT_20260729.md`.

### 5. `th08-revalidate-ida-runtime-semantics`

Trigger examples:

- “verify this TH08 field/offset in IDA”;
- “deepen ECL/pool understanding”;
- “check whether an inherited function name is right”.

Degree of freedom: medium.

Core workflow:

1. use IDA Pro MCP, never REA;
2. treat inherited names/types/comments as hypotheses;
3. inspect instructions, dataflow, callers, callees, and structure use;
4. design a bounded native runtime probe where static evidence is
   insufficient;
5. label inherited/revalidated/corrected;
6. update strong IDA annotations and all affected source-of-truth notes; and
7. grant model/action authority only after the required runtime evidence.

This skill should reference addresses and structures from `notes/` on demand,
not embed a copy that will drift.

### 6. `th08-audit-native-solver-semantics`

This concurrently present skill is a broader, read-only native-to-solver
audit. It covers IDA baseline identity, native semantic reachability,
Python/C/C++ traceability, robustness/performance review, falsification, and
continuous audit reporting through five focused references.

Use it for repository- or subsystem-wide audits. Use
`th08-revalidate-ida-runtime-semantics` for a bounded field/function question
or when explicitly authorized corrections, IDA annotations, runtime probes,
and source-of-truth updates are required. It passes structural validation and
fresh-process repo discovery; this checkpoint did not rewrite its contents.

## Workflows That Should Not Yet Be Skills

- “reduce hits automatically”: the objective is stable, but the research
  method and accepted strategy are not.
- planner/model promotion: authority depends on current formal contracts and
  counterexamples, not a generic recipe.
- unfocused-shot/nonspell combat: still a proposed experiment without native
  shot-mode, damage, source-life, Power, and survival-margin authority.
- V6 auxiliary delivery promotion: its comparator and compact-tail gates are
  unresolved.
- full-route profile tuning: one RNG sample must not become a skill default.

## Skill Design Constraints

- Keep each `SKILL.md` concise and imperative; put volatile commands in a
  directly referenced repo source rather than copying them.
- Bundle deterministic scripts only where repeated quoting or validation is
  genuinely fragile.
- Do not bundle credentials, the supplied sudo password, proxy state, game
  executables, raw traces, or machine secrets.
- Skills must preserve hard no-Bomb, no unattended process, exact cleanup,
  authority separation, and evidence-retention rules.
- Forward-test physical skills only with explicit approval because they
  control a live game/process; dry-run and retained-artifact tasks can be
  tested safely first.
