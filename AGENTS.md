# Touhou Solver Workspace Contract

These instructions apply to every task and file in this repository.

## Source Of Truth

- Read `START_HERE.md` before doing work. It is the short, volatile handoff:
  exact checkpoint, authority boundary, open problems, retained workloads,
  commands, and next useful gate.
- Read `STRATEGY.md` before changing objectives or promotion status. It is the
  live/shadow/proposed/rejected strategy ledger.
- Read the formal and design notes named by `START_HERE.md` before changing a
  model, recurrence, uncertainty set, planner, actuator, or delivery service.
- Record durable failures in `notes/COUNTEREXAMPLES.md` and chronological
  evidence in `notes/RESEARCH_LOG.md`. Detailed history does not belong in
  this contract or the short handoff.
- If documents disagree, reconcile them against code and retained evidence,
  then update every affected source of truth in the same checkpoint.

## Repository Hygiene

- Treat this directory as an independent Git repository. Make a focused
  commit at each verified research checkpoint.
- Preserve unrelated user changes.
- Do not commit game executables, large raw JSONL captures, screenshots,
  daemon logs, caches, credentials, secrets, or native build output.
- Keep compact reports and deterministic fixtures required to reproduce a
  conclusion. Existing tracked research fixtures are intentional history;
  do not remove or rewrite them merely because generated files of the same
  type are now ignored.

## Evidence And Reverse Engineering

- Label conclusions **observed**, **inferred**, or **hypothesized**. Static
  reasoning alone is not runtime proof.
- Prefer evidence from the shipped game, native runtime traces/probes, and the
  connected IDA Pro database. Internet material is optional unless explicitly
  requested.
- Do not use REA in this workspace. Use IDA Pro MCP for new binary static
  analysis and native probes for runtime evidence.
- Treat inherited IDA names, types, comments, pseudocode variable names, and
  earlier semantic labels as hypotheses, not authority. Before using one to
  define a model field, offset, recurrence, capture layout, or live decision,
  revalidate it against instructions/dataflow, relevant callers/callees, and
  runtime evidence when available. Record whether a conclusion is inherited,
  revalidated, or corrected; update misleading database annotations and every
  affected source of truth.
- Persist addresses, structures, calling conventions, and reproducible
  evidence in `notes/`. Rename/type strong conclusions in IDA and record
  material database changes in `notes/RESEARCH_LOG.md`.

## Formal Problem And Authority

Before a major model or planner change, write or update a problem contract
covering:

- physical objective;
- state and observations available at each decision;
- actions and actual issue/no-write semantics;
- uncertainty and transitions;
- horizon and resource constraints;
- safety invariants;
- computation/publication deadline and fallback.

The active input-pipeline and losing-state base specification is
`notes/AUGMENTED_PIPELINE_ROBUST_CONTROL_FORMALIZATION_20260725.md`.
Unrestricted action growth and attainable lower bounds use
`notes/BUDGETED_BELIEF_REFINEMENT_20260725.md`. The current frozen-manager
boundary uses `notes/FROZEN_MANAGER_INPUT_CLOCK_BOUNDARY_20260726.md`.

Every major design note must answer:

1. Which physical histories map to one model state, and are they
   control-equivalent under the observations actually available?
2. Does the recurrence include every declared uncertainty branch and forbid
   clairvoyant or noncausal choices?
3. If solved exactly, does the finite model answer the physical question or
   only a proxy?
4. Does the algorithm solve or conservatively bound that recurrence, and what
   counterexample would falsify the claim?
5. Can the result be consumed before issue time without changing cadence,
   phase, sensor state, or immutable problem version?

Approximations must state what they omit, whether error is conservative,
optimistic, or unknown, and how independent oracles, adversarial cases,
physical evidence, deadlines, and fail-closed fallback limit risk. Unknown-
direction approximations remain outside hard safety authority.

### Information And Actuation

- A policy may condition only on observations available at its decision.
  Merge hidden branches that produce the same observation before the next
  controller maximization. Maximizing hidden branches separately is
  clairvoyant.
- Controller cadence and command pickup delay are different uncertainties.
  State whether cadence applies once, recursively, or through a verified
  scheduler automaton. CE-0111 rejects replacing recursive cadence with one
  root branch or the maximum interval.
- Remaining-delay support is an information set, not independent exact-delay
  roots. The independent Python scalar belief oracle defines the finite
  recurrence.
- Desired or last-issued input is not native active input. `input_current` is
  active-action evidence; an unseen desired transition is pending with
  remaining-delay support.
- Selecting the complete mask already held by the actuator is no-write. It
  samples no new delay, preserves any pending command, and decrements its
  remaining support. Carry held desired input or document and test the
  estimator invariant that reconstructs it.
- `enemy_manager_frame` is not an unconditional physical input clock.
  Post-spell/dialogue states can freeze it while held input continues moving.
  CE-0120 remains open; CE-0121 rejects the repeated-counter wall-time guard.

### Bounds, Candidates, And Versions

- Python/C++ parity proves implementation parity only, not physical-model
  validity.
- Prefer proof-backed feasibility, canonicalization, dominance, admissible
  bounds, and observation-compatible belief merging. Beam, learned,
  Monte-Carlo, MCTS, and unproved pruning remain proposal-only.
- A completed restricted causal policy is an attainable lower bound only for
  its declared action partition and per-history budget. Root actions remain
  unrestricted; adjacent-budget agreement is empirical stability.
- A candidate gains finite-model feasibility authority only after exact
  universal verification over the declared model and retained publication of
  its witness. Timeout, exhaustion, and unvisited candidates are unresolved,
  not unrestricted losing.
- An upper certificate must preserve controller-exists/nature-for-all
  quantifiers, observation merging, actions, transitions, cadence, delay,
  horizon, and clearance. It may prune only with an admissible upper bound
  that cannot beat a completed attainable lower incumbent.
- Timeout may only enlarge the unresolved-action set. Retain proved
  rejections; never reinterpret unfinished optimistic work as a certificate.
- Resume proof work only for an identical immutable policy version, canonical
  root, target frame, float32 margin bits, action set, axes, clearance volume,
  uncertainty support, and continuation contract.
- A public-root optimality claim must account for every root action. A
  feasibility claim may publish one exact winning witness but must not imply
  unique optimality.
- Background expansion must be cooperatively cancellable and newest-version
  first. Consumers perform lookup-only exact-version matching. Misses fall
  back to the live Boolean policy plus a fresh local hard certificate; the
  issue thread must not start cold expansion.
- Keep exact candidate witnesses and post-publication survival labels
  separate from live guidance until promoted. A shadow sharing live workers,
  CPU budget, or publication path is not side-effect-free.

The detailed contracts are:

- `notes/INCUMBENT_UPPER_CERTIFICATION_20260725.md`
- `notes/RESUMABLE_INCUMBENT_CERTIFICATION_20260725.md`
- `notes/ANYTIME_DUAL_BOUND_POLICY_SYNTHESIS_20260725.md`
- `notes/CANDIDATE_WITNESS_PUBLICATION_CONTRACT_20260726.md`
- `notes/FEASIBILITY_FIRST_STAGE6B_PHYSICAL_CONTENTION_20260726.md`

## Architecture And Strategy

- Put reusable game-neutral control/planning code in
  `scripts/touhou_control/`. Keep TH08 addresses, masks, movement constants,
  ECL details, and pool layouts in TH08 adapters.
- Put offline timing/ablation programs in `scripts/benchmarks/`,
  differential/report/dossier tools in `scripts/analysis/`, and explicit
  build/probe/patch/capture entry points in `scripts/tools/`.
- A Windows Python tool under `scripts/tools/` must prepend its parent
  `scripts/` directory to `sys.path`; update an external BAT path if it moves.
- Keep `th08_live_dodge_agent.py` as orchestration. Move independently
  testable sensing, trace, projection, policy, and strategy behind narrow
  modules while preserving one explicit physical-frame contract.
- Do not replace signed clearance with one occupancy bit per lattice cell:
  current transitions subtract nearest-lattice sampling error. Boolean or
  query-local replacements remain shadow-only until viable-state and
  safe-action-mask parity is complete.
- Treat stages, spells, and deaths as workloads and counterexamples, not
  planner identities. Separate universal mechanics from explicit,
  versioned route/team/difficulty/stage/phase strategy profiles.
- Power, boss HP, phase time, lives, and Bombs are state/resource constraints,
  not merely scalar weights. Do not promote a profile from one RNG sample.
- Survival is hard. Graze, collection, Power, score, damage, and position are
  objectives only inside the viable set.
- Physical policy is hard no-Bomb by default. Never emit Bomb bit `0x02`
  unless an explicitly scoped experiment authorizes it.
- Runtime gameplay sensing uses native game state. Screenshots are only for
  bootstrap or menu audits.

## Tests And Counterexamples

- Every native hit, unexpected Bomb, missed transition, stale-plan failure,
  noncausal policy, or concrete model failure belongs in
  `notes/COUNTEREXAMPLES.md`.
- Retain the smallest deterministic adversarial case for each understood
  failure. Stress geometry beyond native pools with stop, resume, redirect,
  reversal, laser, segment, and transform events; compare optimized code to
  an independent scalar oracle and shrink failures.
- Use the smallest focused test while iterating. Keep default tests
  deterministic and fast. Full native solves, broad trace scans, RSS tests,
  capsule corpora, and physical trials are explicit research experiments.
- Tests protect evidence and authority boundaries, not formatting, CLI help,
  or schema plumbing. Do not weaken a test or erase a counterexample to make a
  new result pass.
- Invoke focused files through discovery because `tests/` is not a package:

  ```bash
  PYTHONPATH=scripts python3 -m unittest discover -s tests \
    -p 'test_th08_laser_model.py'
  ```

- Before a code checkpoint run:

  ```bash
  PYTHONPATH=scripts python3 -m unittest discover -s tests -p 'test_*.py'
  ```

- Keep the quick suite on the order of seconds. Run 128-case, unrestricted,
  long-horizon, multi-resolution, wide-cadence, or expensive capsule profiles
  only when their recurrence/kernel changes or evidence is being retained.
- Keep the formal oracle independent Python. Do not replace it with the C++
  implementation it checks.
- Run Windows tests for Windows/process/input/parser/native changes or before
  physical promotion. Use the verified UNC loader in `START_HERE.md`.
- Report clearance timings by workload identity and state whether decoding,
  lowering, packing, and induction are inside the boundary.

## Physical Evidence And Live Control

- Raw runtime JSONL remains local and ignored. Every completed Lunatic, Extra,
  or focused trial used for a conclusion must retain compact reviewable scope,
  provenance, model version, workload, hits/Bombs, resources, items/Power,
  timing, viability health, and stage/phase attribution.
- For each active workload retain the two newest complete replay-capable raw
  bundles locally. Do not delete an older bundle until two newer compatible
  bundles and compact tracked reports exist. Record material removal.
- The first hit of a fresh attempt is the canonical causal witness. Later
  contacts remain useful geometry/planner evidence but are not independent
  clean-route survival samples.
- The daemon is warm before menu selection. F8 starts, F9 stops, and F10
  exits. The user may select difficulty/team/stage manually.
- Before injection verify executable identity, foreground ownership, route,
  difficulty, gameplay state, and the no-life-decrement patch.
- WSL launch return is not supervisor completion. Monitor the exact interop
  process, trace growth, terminal summary, and session status. Avoid Windows
  CLI probes during gameplay because they can steal foreground.
- Always release injected keys on stop or error. Never leave a required game
  or controller session running unattended at turn end.
- Prefer focused trials for one unresolved phase and require repeated clean
  passes before another full route.
- Stage transitions and dialogue confirmation are acceptance behavior. Record
  every manual `Z`, auto-confirm failure, foreground loss, or contamination.
- Route-specific menu constants and verified launch commands live only in
  `START_HERE.md`.

## Acceptance Target

The target is physically validated Sakuya/Remilia control for both Lunatic and
Extra. A planned route is not accepted until the actual game executes it and
retained artifacts verify collisions, Bomb/resources, items, transitions,
sensing, and timing.

Report robust finite-model feasibility separately from unique/global
optimality, and offline/shadow evidence separately from live action authority.
