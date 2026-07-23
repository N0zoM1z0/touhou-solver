# TH08 Workspace Contract

These instructions apply to every file and task below this directory.

## Persistent Workspace

- Keep all TH08 notes, scripts, tests, compact artifacts, and address maps
  under `/home/pentester/coding/codex_ida/th08`.
- Treat this directory as an independent Git repository. Create a focused
  commit at each verified checkpoint so experiments can be compared or
  rolled back.
- Do not commit game binaries, large raw JSONL captures, screenshots, daemon
  logs, caches, credentials, or the sudo password.

## Evidence And Reverse Engineering

- Label conclusions as observed, inferred, or hypothesized. Static reasoning
  alone is not runtime proof.
- Persist reverse-engineering conclusions in `notes/`, with addresses,
  structures, calling conventions, and the evidence needed to reproduce them.
- Rename functions/data and add concise comments or types in the connected IDA
  database when a conclusion is strong enough. Record important IDA changes in
  `notes/RESEARCH_LOG.md`.
- Prefer first-party evidence from the shipped game, runtime traces, IDA, and
  REA. Internet material is not a dependency unless the user explicitly asks
  for it.
- When REA is used, cite its Evidence IDs in the durable note. Record tool
  friction and concrete REA feature requests in a Markdown file under `/tmp`
  for later MCP improvement.

## Architecture And Algorithms

- Put reusable, game-neutral control and planning code in
  `scripts/touhou_control/`. Keep TH08 memory addresses, input masks, movement
  constants, ECL details, and pool layouts in TH08 adapters.
- Persist every important algorithmic or architectural decision, breakthrough,
  rejected approach, assumption, and limitation. Use a dedicated design note
  for the algorithm and summarize the checkpoint in
  `notes/RESEARCH_LOG.md`.
- Survival is a hard constraint. Graze, item collection, power, score, damage,
  and positional preference are objectives only inside the currently viable
  action set.
- Runtime control must use native game state as its gameplay sensor.
  Screenshots are only for bootstrap/menu audits.
- The default physical-practice policy is hard no-Bomb. Do not spend a Bomb
  unless a specific experiment explicitly enables it. Later resource-aware
  planning may use Bomb only when the no-Bomb viability set is empty.

## Counterexamples And Tests

- Every native hit, unexpected Bomb, missed transition, stale-plan failure, or
  other concrete failure must become a durable counterexample in
  `notes/COUNTEREXAMPLES.md`.
- Add the smallest useful regression test or retained regression artifact for
  each understood failure. A strangely specific test name should explain the
  exact way the agent once failed.
- Run focused tests while developing and the complete suite before a checkpoint:

  ```bash
  PYTHONPATH=scripts python -m unittest discover -s tests -p 'test_*.py'
  ```

- Do not weaken a test or erase a counterexample merely to accept a new run.
  State explicitly when a model change invalidates an old expectation.

## Physical Trial Artifacts

- Keep raw runtime JSONL local and ignored. Every completed Lunatic, Extra, or
  focused thprac trial used for a conclusion must produce compact tracked
  artifacts sufficient to review and regress it.
- A complete-run record must include scope and provenance, controller/model
  version, difficulty/team/stage/phase, every hit and Bomb boundary, resources,
  item and power outcomes, action/delay timing, corridor/viability health, and
  per-stage/per-spell attribution.
- Generate and retain the dossier, death ledger, executable regression cases,
  comparison summary, and a human-readable note under `notes/runs/`.
- Record discarded, truncated, reset-tail, lost-foreground, or manually
  contaminated trials as such. Never merge them into an acceptance baseline.
- Stage transitions and dialogue auto-confirm behavior are part of the trial.
  Record manual `Z` intervention and auto-confirm failures.

## Live-Control Protocol

- The user may select difficulty, team, and thprac stage manually. The daemon
  must already be warm; `F8` starts control with minimal handoff latency and
  `F9` stops it.
- Verify executable identity, foreground ownership, route 2, difficulty,
  gameplay state, and the no-life-decrement patch before injecting input.
- Always release injected keys on stop or error. Do not leave a required
  runtime session running unattended at the end of a task.
- Prefer focused thprac trials for an unresolved spell or nonspell. Require
  repeated clean focused passes before spending time on another full route.

## Acceptance Target

- The final target is physically validated Sakuya/Remilia control for both
  Lunatic and Extra.
- A planned route is not accepted until the agent executes it in the actual
  game and retained artifacts show that collision, Bomb/resource, item,
  transition, and timing claims match native state.
- Optimize globally across survival, finite Bomb/life resources, power and item
  collection, damage/phase timing, and graze. Report feasible robust policies
  separately from any claim of a unique global optimum.
