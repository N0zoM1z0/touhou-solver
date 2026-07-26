# TH08 Workspace Contract

These instructions apply to every task and file below this directory.

## Start Here And Source Of Truth

- Read `START_HERE.md` before doing work. It is the short, volatile handoff:
  exact checkpoint, current authority boundary, open problems, retained
  workloads, commands, and the next useful gate.
- Read `STRATEGY.md` before changing objectives or promotion status. It is the
  live/shadow/rejected/proposed strategy ledger.
- Read the formal and design notes named by `START_HERE.md` before changing a
  model, recurrence, uncertainty set, planner, actuator, or delivery service.
- Use `notes/COUNTEREXAMPLES.md` for durable failures and
  `notes/RESEARCH_LOG.md` for chronological evidence. Detailed history belongs
  there, not in `START_HERE.md` or this contract.
- If these files disagree, do not silently choose the most convenient claim.
  Reconcile them against code and retained evidence, then update all affected
  documents in the same checkpoint.

## Persistent Workspace

- Keep all TH08 notes, scripts, tests, compact artifacts, and address maps
  under `/home/pentester/coding/codex_ida/th08`.
- Treat this directory as an independent Git repository. Make a focused commit
  at each verified checkpoint so experiments can be compared or rolled back.
- Preserve unrelated user changes. In particular, `image.png` is user-owned
  and must not be added, changed, deleted, or cleaned.
- Do not commit game binaries, large raw JSONL captures, screenshots, daemon
  logs, caches, credentials, native build output, or the sudo password.

## Evidence And Reverse Engineering

- Label conclusions as **observed**, **inferred**, or **hypothesized**. Static
  reasoning alone is not runtime proof.
- Prefer first-party evidence from the shipped game, native runtime
  traces/probes, and the connected IDA Pro database. Internet material is not
  a dependency unless the user explicitly asks for it.
- Do not use REA or the `reverse-engineer-anything` skill in this workspace.
  Use IDA Pro MCP for new binary static analysis and native probes for runtime
  evidence. Historical REA Evidence IDs are provenance only.
- Persist reverse-engineering conclusions in `notes/`, including addresses,
  structures, calling conventions, and reproducible evidence. Rename and type
  strong conclusions in IDA; record material IDA changes in
  `notes/RESEARCH_LOG.md`.

## Formal Problem And Authority

Before a major model or planner change, write or update a problem contract:

- physical objective;
- state and observations available at each decision;
- actions and actual issue/no-write semantics;
- uncertainty and transition;
- horizon and resource constraints;
- safety invariants;
- computation/publication deadline and fallback.

For the active input-pipeline and losing-state problem,
`notes/AUGMENTED_PIPELINE_ROBUST_CONTROL_FORMALIZATION_20260725.md` is the
base specification. For unrestricted action growth and its attainable lower
bounds, also read `notes/BUDGETED_BELIEF_REFINEMENT_20260725.md`. For the
current frozen-manager-frame boundary, read
`notes/FROZEN_MANAGER_INPUT_CLOCK_BOUNDARY_20260726.md`.

Before optimizing or promoting a major algorithm, answer these five questions
in its design note:

1. Which physical histories map to one model state, and are they
   control-equivalent under the observations actually available?
2. Does the recurrence include every declared uncertainty branch and forbid
   clairvoyant or noncausal choices?
3. If solved exactly, does the finite model answer the physical decision of
   interest, or only a proxy?
4. Does the algorithm solve or conservatively bound that recurrence, and what
   counterexample would falsify the claim?
5. Can the result be consumed before issue time without changing the cadence,
   phase, sensor state, or immutable problem version it describes?

Engineering approximations are welcome; a complete proof is not mandatory.
Every approximation must state what it omits, whether its error is
conservative, optimistic, or unknown, and how independent oracles,
adversarial cases, retained physical evidence, deadlines, and fail-closed
fallback limit the risk. Unknown-direction approximations remain outside hard
safety authority.

### Information and actuation semantics

- A policy may condition only on observations available at that decision.
  Merge hidden branches that produce the same observation before the next
  controller maximization. Branching hidden states and maximizing separately
  creates a clairvoyant policy even when numeric transitions are correct.
- Treat controller cadence and command pickup delay as different
  uncertainties. State whether cadence uncertainty applies once, recursively,
  or through a verified scheduler automaton. CE-0111 disproves replacing
  recursive cadence by one root branch or the maximum interval.
- Remaining-delay support is an information set, not a list of independent
  exact-delay roots. The independent Python scalar belief oracle specifies the
  finite recurrence.
- Never equate desired or last-issued input with native active input.
  `input_current` is active-action evidence; an unseen desired transition is a
  pending command with remaining-delay support.
- Selecting the complete mask already held by the actuator is no-write: it
  samples no new delay, preserves the pending command, and decrements its
  remaining support. Carry held desired input explicitly or document and test
  the estimator invariant that reconstructs it.
- `enemy_manager_frame` is not an unconditional physical input clock.
  Post-spell/dialogue states can freeze it while held input keeps moving the
  player. CE-0120 is open and CE-0121 rejects the 50-ms repeated-counter
  detector. Do not grant live action authority to another raw wall-time
  threshold without an independently validated semantic boundary.

### Bounds, candidates, and version identity

- Python/C++ differential parity proves implementation parity only. It does
  not prove that the recurrence matches the physical problem.
- Prefer proof-backed feasibility, canonicalization, dominance, admissible
  bounds, and observation-compatible belief merging. Treat unproved pruning,
  beam, learned, Monte Carlo, MCTS, and action ordering as proposal-only.
- A completed budgeted/restricted causal policy is an attainable lower bound
  only for its declared action partition and per-history budget. Root actions
  remain unrestricted. Adjacent-budget agreement is empirical stability, not
  unrestricted optimality.
- A candidate action gains finite-model feasibility authority only after exact
  universal verification over the declared uncertainty model and after its
  witness is retained with the public root decision. Candidate exhaustion,
  aggregate-budget exhaustion, timeout, and unvisited candidates are
  unresolved, never unrestricted losing.
- An upper certificate must preserve the controller-exists/nature-for-all
  quantifiers, observation merging, actions, transitions, cadence, delay,
  horizon, and clearance contract. It may prune only when an admissible
  lexicographic upper bound cannot beat a completed attainable lower
  incumbent.
- A timeout may only enlarge the unresolved-action set. Retain proved
  rejections; mark in-flight and unvisited work unresolved. Never reinterpret
  unfinished optimistic search as a certificate.
- Resume or reuse proof work only for an identical immutable policy version,
  canonical root, absolute target frame, float32 margin bits, action set,
  axes, clearance volume, uncertainty support, and continuation contract.
  Across versions, reuse proposal order or policy shape only; recompute every
  label.
- A public-root optimality claim must account for every root action with an
  exact label or a valid lower/upper certificate. A feasibility claim may
  publish one retained winning witness, but must not imply unique optimality.
- Background expansion must be cooperatively cancellable. Newest version wins;
  do not queue current work behind a stale FIFO. A consumer performs
  lookup-only exact-root/version matching; a miss falls back to the live
  Boolean policy plus a fresh local hard certificate and must not start cold
  expansion on the issue thread. Do not destroy a native workspace until its
  running future has stopped.
- Keep exact candidate witness publication and post-publication survival
  labels separate from live guidance until explicitly promoted. A shadow that
  shares the live worker, CPU budget, or publication path is not
  side-effect-free. Publish the authoritative safety object before optional
  shadow work and measure delivery contention separately from lookup time.

The lower/upper/anytime contracts are detailed in:

- `notes/INCUMBENT_UPPER_CERTIFICATION_20260725.md`
- `notes/RESUMABLE_INCUMBENT_CERTIFICATION_20260725.md`
- `notes/ANYTIME_DUAL_BOUND_POLICY_SYNTHESIS_20260725.md`
- `notes/CANDIDATE_WITNESS_PUBLICATION_CONTRACT_20260726.md`
- `notes/FEASIBILITY_FIRST_STAGE6B_PHYSICAL_CONTENTION_20260726.md`

## Architecture And Strategy

- Put reusable, game-neutral control and planning code in
  `scripts/touhou_control/`. Keep TH08 addresses, masks, movement constants,
  ECL details, and pool layouts in TH08 adapters.
- Keep importable models, adapters, and live entry points out of experiment
  modules. Put offline timing/ablation programs in `scripts/benchmarks/`,
  differential/report/dossier programs in `scripts/analysis/`, and explicit
  build/probe/patch/capture entry points in `scripts/tools/`.
- A Windows Python tool below `scripts/tools/` must prepend its parent
  `scripts/` directory to `sys.path`. If it moves, update the external
  game-directory BAT path in the same checkpoint.
- Treat `th08_live_dodge_agent.py` as orchestration. Move independently
  testable sensing, trace, projection, policy, and strategy logic behind
  narrow modules while preserving one explicit physical-frame contract.
- Do not replace signed clearance with one occupancy bit per lattice cell
  under the current recurrence: transitions subtract nearest-lattice sampling
  error. Any Boolean/query-local replacement remains shadow-only until complete
  viable-state and safe-action-mask parity is established.
- Treat stages, spells, and deaths as workloads and counterexamples, not
  planner identities. Generalize mechanics; put unavoidable TH08 behavior in
  the adapter and document why it is game-specific.
- Separate universal mechanics from explicit route-conditioned strategy.
  Game/team/difficulty/stage/phase profiles may supply practiced tubes,
  event-relative timing, resolution/horizon, resource floors, damage models,
  and objective priorities, but must be explicit, versioned strategy data.
- Power, boss HP, remaining phase time, lives, and Bombs are state/resource
  constraints, not merely scalar weights. Do not promote a profile from a
  single RNG/entry-state sample.
- Survival is a hard constraint. Graze, collection, Power, score, damage, and
  positional preference are objectives only inside the currently viable set.
- The default physical policy is hard no-Bomb. Never emit Bomb bit `0x02`
  unless an explicitly scoped experiment authorizes it.
- Runtime gameplay sensing must use native game state. Screenshots are only
  for bootstrap or menu audits.

## Counterexamples And Research Tests

- Every native hit, unexpected Bomb, missed transition, stale-plan failure,
  noncausal policy, or concrete model failure belongs in
  `notes/COUNTEREXAMPLES.md`.
- Retain the smallest deterministic adversarial case for each understood
  failure. Stress reusable geometry with densities beyond the native pool and
  with stop, resume, redirect, reversal, laser, segment, and transform events.
  Compare optimized code with an independent scalar oracle; shrink failures.
- Use the smallest focused test while iterating. Keep unit tests deterministic
  and fast. Full native solves, broad trace scans, memory/RSS benchmarks,
  capsule corpora, and physical trials are explicit research experiments.
- Optimize tests for research evidence, not engineering completeness. Do not
  add duplicate formatting, CLI-help, schema-plumbing, or private-call tests
  unless they protect a concrete failure, artifact, or authority boundary.
- Do not weaken a test or erase a counterexample to accept a new run. State
  when a changed model genuinely invalidates an old expectation.
- Invoke focused files through discovery because `tests/` is not a package:

  ```bash
  PYTHONPATH=scripts python3 -m unittest discover -s tests \
    -p 'test_th08_laser_model.py'
  ```

- Before a code checkpoint, run the quick complete suite:

  ```bash
  PYTHONPATH=scripts python3 -m unittest discover -s tests -p 'test_*.py'
  ```

- Keep that suite on the order of seconds. The default offline belief gate is
  the bounded quick formal/benchmark profile; run 128-case, unrestricted,
  long-horizon, multi-resolution, or wide-cadence profiles only when their
  recurrence/kernel changes or evidence is being retained.
- Keep the formal oracle in independent Python. Do not replace it with the C++
  implementation it checks.
- Run expensive capsule replays only when their model or algorithm changed.
  Run Windows tests for Windows/process/input/parser/native changes or before
  physical promotion; documentation-only work does not require them.
- Windows UNC test discovery has a verified loader command in
  `START_HERE.md`. Do not retry `unittest -s <UNC>`, `cmd.exe` UNC `cd/pushd`,
  or a PowerShell-only `PSDrive`.
- Separate clearance benchmarks by workload identity: TH08 live-like moving
  AABBs plus packed lasers, game-neutral static segments, and piecewise
  transform adversarial motion. State whether decoding, lowering, packing,
  and induction are inside the timing boundary.

## Physical Trial Artifacts

- Raw runtime JSONL remains local and ignored. Every completed Lunatic, Extra,
  or focused trial used for a conclusion must produce compact tracked evidence
  sufficient to review it.
- For each active workload, retain the two newest complete replay-capable raw
  bundles. Workload identity includes game/team/difficulty/stage or phase and
  capture schema/options. A bundle contains raw JSONL, matching capsules, and
  provenance needed to reconstruct roots.
- Do not delete an older bundle until two newer same-workload bundles are
  complete, readable, schema-compatible, and represented by compact tracked
  reports. Discarded, truncated, reset-tail, foreground-contaminated, or
  schema-incompatible attempts do not count toward the floor.
- Older replay bundles, screenshots, logs, caches, and native builds are
  cleanup candidates only after that audit. Record material removal. Never
  claim replay evidence when only a compact summary survives.
- A complete record must include scope/provenance, model version, workload,
  every hit and Bomb boundary, resources, items/Power, timing, viability
  health, and per-stage/per-phase attribution.
- Retain the dossier, death ledger, executable regressions, comparison,
  session/summary, and a human-readable note under `notes/runs/`.
- The first hit of a fresh attempt is the canonical causal witness. Later
  post-hit/respawn contacts remain valid geometry/planner evidence but are not
  independent clean-route survival samples.

## Live-Control Protocol

- The user may select difficulty/team/stage manually. The daemon must already
  be warm; F8 starts with minimal handoff latency, F9 stops, and F10 exits.
- Use `run_th08_full_route_agent.bat` for one continuous original-game
  Lunatic Route-2 run. Normal Game Start modes are main `0`, difficulty `4`,
  team `5`; force Down then Up before confirming main cursor `0`.
- At Final B, require both `terminal_unload` and the later
  `route_complete` summary.
- Before injecting input, verify executable identity, foreground ownership,
  route 2, difficulty, gameplay state, and the no-life-decrement patch.
- WSL launch return is not proof that the Windows supervisor finished. Monitor
  the exact interop process, growing trace, terminal summary, and session
  status. Avoid Windows CLI probes while gameplay is active because they can
  steal foreground.
- Always release injected keys on stop or error. Never leave a required game
  or control session running unattended at turn end.
- Prefer focused trials for one unresolved phase. Require repeated clean
  focused passes before spending another full route.
- Stage transitions and dialogue auto-confirm are part of acceptance. Record
  every manual `Z`, auto-confirm failure, foreground loss, or contamination.

## Acceptance Target

- The target is physically validated Sakuya/Remilia control for both Lunatic
  and Extra.
- A planned route is not accepted until the actual game executes it and
  retained artifacts verify collision, Bomb/resources, items, transitions,
  sensing, and timing.
- Report robust finite-model feasibility separately from unique/global
  optimality, and report offline/shadow evidence separately from live action
  authority.
