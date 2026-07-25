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
- Prefer first-party evidence from the shipped game, runtime traces, and the
  connected IDA Pro database. Internet material is not a dependency unless
  the user explicitly asks for it.
- Do not use REA or the `reverse-engineer-anything` skill in this workspace.
  Use IDA Pro MCP for new binary static analysis and native runtime
  traces/probes for execution evidence. Historical REA Evidence IDs remain
  provenance for old conclusions, but they are not authorization to open a
  new REA session or run REA setup/doctor commands.

## Architecture And Algorithms

- Begin every major planner/model change from a written problem contract:
  physical objective, state, observations, actions, uncertainty, transition,
  horizon, invariants, and delivery deadline. Map each implementation state
  and transition back to that contract before optimizing it. For the current
  losing-state/input-pipeline work,
  `notes/AUGMENTED_PIPELINE_ROBUST_CONTROL_FORMALIZATION_20260725.md` is
  mandatory reading and the active reference. For unrestricted action growth,
  also read `notes/BUDGETED_BELIEF_REFINEMENT_20260725.md`; do not interpret a
  completed small-budget lower bound as unrestricted optimality.
- Audit both mathematical semantics and information semantics. In particular,
  a policy may condition only on observations available at that decision.
  Branching hidden states and then maximizing separately can create a
  clairvoyant policy even when every numeric transition is correct. State
  explicitly whether cadence/delay uncertainty is handled once, recursively,
  or as an information-set support.
- Engineering approximations are allowed; a complete formal proof is not a
  prerequisite for useful research. Every approximation must nevertheless
  declare what it omits or relaxes, whether the resulting value is
  conservative, optimistic, or unknown, and how independent scalar oracles,
  adversarial counterexamples, retained physical evidence, deadlines, and
  fail-closed fallback bound the risk. Do not call an approximation “exact”
  without naming the exact finite model it solves.
- Kernel parity is not problem correctness. Differential agreement between
  Python and C++ implementations of the same recurrence establishes only
  implementation parity. Promotion requires a separate argument that the
  recurrence matches, conservatively approximates, or acceptably bounds the
  written physical problem. If an adversarial case disproves that mapping,
  stop performance iteration on the invalid claim and retain the case.
- Before optimizing or promoting a major algorithm, write a short formal
  review in its design note that answers:
  1. Which physical histories map to one model state, and are they truly
     control-equivalent under the available observations?
  2. Does the recurrence admit every physical uncertainty branch and forbid
     clairvoyant/noncausal choices?
  3. If solved exactly, would this model answer the physical decision we care
     about, or only a proxy?
  4. Does the proposed algorithm actually solve/bound that recurrence, and
     what counterexample would falsify the claim?
  5. Can the result be delivered before issue time without changing the
     modeled cadence or sensing state?
  A concise argument plus adversarial evidence is sufficient for an
  engineering approximation; a complete mathematical proof is welcome but
  not mandatory. Unknown-direction approximations must stay outside hard
  safety authority.
- Prefer proof-backed reductions such as feasibility, canonicalization,
  dominance, admissible bounds, and observation-compatible belief merging.
  When a reduction has no concise correctness argument, keep it heuristic,
  measure its action/label error against the independent oracle, and keep it
  outside hard-safety authority.
- A budgeted continuation solve is an attainable lower bound only for its
  declared base/extra action partition and per-history budget. Root actions
  remain unrestricted. Preserve the budget in native memo identity, refine
  from lower to higher budgets, and publish only a completed lower-bound
  result. Equal labels at two adjacent budgets are empirical stability, not
  an optimality certificate. The current revealed-remaining-delay mode is a
  proved upper bound only when it keeps the unrestricted action class and the
  same transitions/uncertainty; stopping early requires that bound to meet the
  completed lower value on the queried root.
- A selective upper certificate must compare a completed attainable lower
  label against a proved optimistic upper recurrence on the same immutable
  root and policy version. Preserve the original controller-exists /
  nature-for-all quantifiers, observation merging, cadence, delay support,
  actions, horizon, and clearance contract. It may prune only when an
  admissible lexicographic upper bound cannot strictly beat the lower
  incumbent. Report unresolved root actions; never reinterpret a timeout or
  unfinished optimistic search as certification. See
  `notes/INCUMBENT_UPPER_CERTIFICATION_20260725.md`.
- Put reusable, game-neutral control and planning code in
  `scripts/touhou_control/`. Keep TH08 memory addresses, input masks, movement
  constants, ECL details, and pool layouts in TH08 adapters.
- Keep importable models, adapters, and live entry points out of experiment
  modules. Put offline timing/ablation programs in `scripts/benchmarks/`,
  differential/report/dossier programs in `scripts/analysis/`, and explicit
  build/probe/patch/capture entry points in `scripts/tools/`. A benchmark must
  not become a production dependency.
- A Windows Python entry point below `scripts/tools/` must explicitly prepend
  its parent `scripts/` directory to `sys.path`; Windows starts a UNC script
  with only the tool directory importable. When a tool moves, update the
  external game-directory BAT path as part of the same checkpoint.
- Treat `th08_live_dodge_agent.py` as orchestration, not the permanent owner
  of every model. Move independently testable trace schemas, projection,
  sensing, policy, and strategy logic behind narrow modules while preserving
  one explicit physical-frame and uncertainty contract.
- Never equate the last desired/issued input with the action currently active
  in the game. Native `input_current` is active-action evidence; an unseen
  desired input is a pending command with explicit remaining-delay support.
  Any viability or survival policy that omits layer phase or this pipeline
  state must remain shadow/diagnostic unless a sound conservative equivalence
  has been demonstrated.
- Never equate a planner decision with a new command issue. The actuator sends
  transitions and samples a new delay only when the selected complete mask
  differs from the mask it already holds. Selecting the held desired action
  is no-write: preserve the old pending command and decrement its remaining
  support. The formal state must carry held desired input separately or state
  and verify the estimator invariant used to reconstruct it.
- Treat TH08 stages, spells, and retained deaths as validation workloads and
  counterexamples, not planner identities. Whenever practical, improve the
  accuracy, performance, uncertainty handling, or reachability semantics of
  the reusable solver instead of encoding a route for one observed pattern.
- Generality is a strong preference, not an absolute ban on game-specific
  behavior. TH08-native mechanics and recovered runtime semantics belong in a
  TH08 model or adapter, exposed through game-neutral trajectory, occupancy,
  control, and planning contracts. Record why any stage- or spell-specific
  exception is unavoidable and test that it does not silently become the
  default planner policy.
- Separate universal mechanics from route-conditioned strategy. Collision,
  movement, delay, sensing, event timing, and viability semantics must not be
  tuned until one stage happens to pass. A game/team/stage/phase profile may
  legitimately supply a practiced reference tube, event-relative lead times,
  planning resolution/horizon, resource floors, damage model, and objective
  priorities. Treat such profiles as explicit strategy data with provenance,
  not hidden branches in the safety kernel.
- Do not assume one scalar weight vector is universal. Power, boss HP,
  remaining phase time, lives, and Bombs are state and resource constraints,
  not merely preferences. Tune remaining strategy parameters on more than one
  RNG/entry-state sample, retain adverse trials, and keep a profile shadow-only
  until its hard-safety boundary and cross-sample effect are understood.
- Persist every important algorithmic or architectural decision, breakthrough,
  rejected approach, assumption, and limitation. Use a dedicated design note
  for the algorithm and summarize the checkpoint in
  `notes/RESEARCH_LOG.md`.
- Keep `STRATEGY.md` as the strategy ledger. Before promoting or retiring a
  control objective, update its live/shadow/rejected status, evidence,
  failure mode, and the measurable condition under which it may be tried
  again. A new strategy must not silently erase an older counterexample.
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
- Use deterministic synthetic adversarial workloads to stress reusable
  trajectory, collision, and viability kernels before spending a physical
  trial. Permit densities above any one game's native pool and include stop,
  resume, redirect, and reversal events. Compare optimized/native results to
  an independent scalar oracle, retain failing seeds, and shrink failures to
  a minimal reproducible hazard set. Synthetic success is a differential
  gate, never a substitute for native physical acceptance.
- Add the smallest useful regression test or retained regression artifact for
  each understood failure. A strangely specific test name should explain the
  exact way the agent once failed.
- Use the smallest focused test while iterating on a hypothesis. Keep unit
  tests deterministic and fast; full native solves, multi-resolution audits,
  replay corpora, memory benchmarks, and physical trials are retained research
  experiments rather than unit-test setup.
- Invoke focused files through discovery because `tests/` is not a Python
  package, for example:

  ```bash
  PYTHONPATH=scripts python -m unittest discover -s tests \
    -p 'test_th08_laser_model.py'
  ```

- Optimize tests for research evidence, not engineering completeness. Do not
  add duplicate formatting, CLI-help, schema-plumbing, or private-call tests
  unless they protect a concrete failure, evidence artifact, or safety
  contract. Prefer one oracle/differential invariant over many
  implementation-shaped examples.
- Keep benchmark/report CLI wiring and retired shadow integration out of the
  unit suite unless a concrete artifact or authority boundary failed there.
  Exercise those programs through quick/full research profiles instead.
  Retain constant-time live-vs-shadow authority assertions even when the
  rejected shadow implementation itself is no longer integration-tested.
- Run the quick complete unit suite before a code checkpoint:

  ```bash
  PYTHONPATH=scripts python -m unittest discover -s tests -p 'test_*.py'
  ```

- Run expensive capsule replays only when their model or algorithm changed.
  Run Windows tests only for Windows/process/input/parser/native changes or
  immediately before physical promotion. A documentation or offline-analysis
  checkpoint does not require duplicating the complete suite on Windows.
- When Windows Python reads this WSL workspace, use the UNC-safe loader command
  recorded in `START_HERE.md`: insert the UNC `scripts` directory into
  `sys.path` and pass the same UNC `tests` directory as both `start_dir` and
  `top_level_dir`. Do not retry CLI discovery with `-s <UNC>`, `cmd.exe`
  `cd/pushd` to UNC, or a PowerShell-only `PSDrive`; those interfaces do not
  provide an importable test root to the external Windows Python process.
- The quick suite is the default checkpoint gate only while it remains on the
  order of seconds. Never put complete 16/8/4-pixel solves, large trace scans,
  native memory/RSS benchmarks, or physical integration in that suite.
- Offline belief work has three levels: focused unit tests; the default quick
  formal/benchmark profiles (16 scalar cases and bounded structured cases);
  and explicit retained full profiles (128 cases, unrestricted/long-horizon/
  wide-cadence scaling). Run full only when the recurrence/native kernel
  changes or evidence is being retained. Keep the formal oracle in independent
  Python; do not replace it with the C++ implementation it is meant to check.
- Keep clearance benchmarks separated by workload identity: TH08 live-like
  moving AABBs plus packed laser trajectories, game-neutral static finite
  segments, and piecewise transform adversarial motion. Every performance
  report must state whether decoding, lowering, packing, and policy induction
  are inside or outside its timing boundary.
- Do not replace signed clearance with one Boolean occupancy bit per lattice
  cell under the current robust recurrence: it subtracts
  transition-specific nearest-lattice sampling error. Any occupancy or
  query-local successor stays shadow-only until complete viable-state and
  safe-action-mask parity is demonstrated, not only representative endpoint
  parity.
- A shadow computation that shares the live worker, CPU budget, or
  publication critical path can change policy age and therefore is not
  side-effect-free. Publish the authoritative safety result before optional
  shadow work, or keep the shadow offline; report its delivery cost separately
  from label-query cost.
- Post-publication survival labels must remain a separate policy object and
  must not silently enter local guidance. Physical shadow collection requires
  an explicit option, an executor independent of Boolean publication, and a
  measured worker budget. Passing Boolean/label array parity is not
  authorization for input authority.
- An augmented/pending-input workspace is owned by one immutable policy
  version. Never reuse its memo across a clearance volume, axes, action set,
  delay support, source frame, or context change. Non-root optimality pruning
  may discard work only when an admissible lexicographic upper bound cannot
  beat the incumbent; public roots must retain exact labels for every action.
  A cold reachable-tube expansion must stay off the issue-time thread. Publish
  and consume only an exact root/version match; otherwise fall back to the
  Boolean policy plus the fresh local hard certificate.
- Treat controller cadence separately from command pickup delay. A
  variable-cadence value must state whether uncertainty applies once,
  recursively, or through a verified scheduler automaton. The legacy
  public-root/fixed-continuation workspace is not a full variable-cadence
  proof; the recursive belief workspace is the finite-model reference but can
  exceed the service budget. CE-0111 shows that replacing recursive cadence
  with a single root branch or the maximum interval can be optimistic. Do not
  narrow cadence schedules without an equivalence proof or an explicitly
  measured unknown-direction approximation.
- Remaining-delay support is an information set, not just a list of scalar
  roots. If several delay branches produce the same next observation, merge
  them before the next controller maximization. The scalar belief oracle is
  the specification for this finite recurrence; the legacy exact-remaining
  memo is an unbounded-direction hybrid research model and must remain
  shadow-only.
- A warmed phase memo is not a cached exact root. Background code may seed
  phase skeletons before action selection, but it must still materialize the
  full frame/cell/observed/pending/remaining-support root after issuance.
  Controller-side consumption must use lookup-only semantics: a miss must
  never start cold C++ expansion. Report phase-seed, root-specialization, and
  consumption timings separately, including root/seed enumeration and
  measured worker contention.
- Native background expansion must have cooperative cancellation and a hard
  deadline before it is attached to a rolling executor. A newer immutable
  policy cancels every older native workspace and receives a fresh bounded
  executor; do not rely on Python future cancellation or put new work behind
  a stale FIFO queue. Do not destroy a native handle until its running future
  has stopped.
- Merge continuation memos only for the exact same immutable policy problem
  and fixed-continuation contract. A clearance or version change invalidates
  the memo. Report cold per-version decisions separately from steady rolling
  decisions and compare the warm-up length with measured live policy lifetime;
  a steady-state timing win is not a delivery win if most policies expire
  during warm-up.
- Do not weaken a test or erase a counterexample merely to accept a new run.
  State explicitly when a model change invalidates an old expectation.

## Physical Trial Artifacts

- Keep raw runtime JSONL local and ignored. Every completed Lunatic, Extra, or
  focused thprac trial used for a conclusion must produce compact tracked
  artifacts sufficient to review and regress it.
- Raw JSONL, viability capsules, screenshots, logs, caches, and native build
  outputs are temporary working data. Once the compact dossier, ledger,
  regression cases, comparison, and note have been verified and committed,
  delete the raw copy by default. Retain raw data only for a named active
  differential; record why it is still needed and remove it when that
  experiment closes.
- A complete-run record must include scope and provenance, controller/model
  version, difficulty/team/stage/phase, every hit and Bomb boundary, resources,
  item and power outcomes, action/delay timing, corridor/viability health, and
  per-stage/per-spell attribution.
- Generate and retain the dossier, death ledger, executable regression cases,
  comparison summary, and a human-readable note under `notes/runs/`.
- Record discarded, truncated, reset-tail, lost-foreground, or manually
  contaminated trials as such. Never merge them into an acceptance baseline.
- Report a fresh canonical attempt separately from later post-hit/respawn
  discovery. Retained later deaths are valid geometry and planner
  counterexamples, but they are not independent clean-route survival samples.
- Stage transitions and dialogue auto-confirm behavior are part of the trial.
  Record manual `Z` intervention and auto-confirm failures.

## Live-Control Protocol

- The user may select difficulty, team, and thprac stage manually. The daemon
  must already be warm; `F8` starts control with minimal handoff latency and
  `F9` stops it.
- Use `run_th08_full_route_agent.bat` for one continuous original-game
  Lunatic Route-2 run. Normal Game Start title modes are main `0`, difficulty
  `4`, and team `5`. Force a real Down-then-Up cursor transition back to main
  cursor `0` before confirming Game Start; a freshly read cursor `0` alone
  does not prove the selection transition is armed.
- At Final B completion the first inactive record is `terminal_unload`; only
  after the terminal grace period does the run summary become
  `route_complete`. Require both records when finalizing a full-run dossier.
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
