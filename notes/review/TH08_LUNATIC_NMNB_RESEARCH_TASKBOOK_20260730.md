# TH08 Sakuya/Remilia Lunatic NMNB Research Taskbook

Date: 2026-07-30  
Status: research plan and agent handoff; not strategy authority  
Primary workspace: `/home/pentester/coding/codex_ida/th08`

All repository paths below are relative to the workspace root unless stated
otherwise.

## 0. Purpose And How To Use This Taskbook

This taskbook defines a closed research loop for reaching physically validated
Sakuya/Remilia Lunatic no-miss/no-Bomb (NMNB) play. It connects:

- original-game physical evidence;
- the rolling native snapshot causal wind tunnel;
- native/model first-mismatch analysis;
- the exact finite-model solver and live delivery path;
- route/resource reasoning; and
- selected ideas from retained external projects.

It is deliberately not a list of speculative features. Every work item must
end in one of four outcomes:

1. a verified result promoted through its declared evidence gate;
2. a minimal counterexample routed back to the responsible layer;
3. an explicit `UNKNOWN` with a bounded missing dependency; or
4. a rejected proposal retained with a reason and stop condition.

Before acting, every agent must read:

1. `AGENTS.md`;
2. the current `START_HERE.md`;
3. the relevant section of `STRATEGY.md`;
4. the specific formal/design note named by the handoff for the layer being
   changed; and
5. the newest relevant counterexample and run dossier.

Do not restart a repository-wide semantic audit. Select one task card, one
root/event class, one model path, or one physical workload. Reuse compatible
retained evidence and expand scope only when a concrete dependency requires
it.

This file is a planning artifact. `AGENTS.md`, `START_HERE.md`, `STRATEGY.md`,
the formal contracts, shipped-game evidence, and retained immutable reports
remain authoritative when they disagree with this plan.

### 0.1 Iteration-first and gate-proportional operation

Iteration speed, causal learning, and forward progress are first-class
research requirements. The default is the cheapest experiment that can
change the next decision, not the broadest test or audit that can be run.

Agents must:

- begin from the current retained checkpoint and reuse compatible evidence;
- work on one bottleneck, first mismatch, root, or measurable performance
  limit at a time;
- run the smallest focused oracle/test/native branch that can falsify the
  current hypothesis;
- measure before optimizing and optimize the observed dominant cost;
- prefer shortening the model/native/solver feedback loop over adding
  unconsumed schemas, reports, abstractions, or speculative infrastructure;
- stop checking once the task's decision has been established, then advance
  to the next gate or counterexample;
- batch expensive broad gates at verified checkpoints or promotion
  boundaries instead of rerunning them after every local edit;
- record why an omitted broad gate was not triggered, rather than running it
  defensively without a relevant failure mode.

The proportional gate ladder is:

| Change scope | Default iteration gate | Broader gate only when |
| --- | --- | --- |
| Documentation, analysis, task routing | internal consistency and referenced-evidence check | an authority or promotion claim changed |
| Local pure code or fixture | focused deterministic unit/oracle test | shared recurrence/API behavior changed |
| Model/event semantic slice | first-mismatch fixture plus the relevant native root/horizon | event support or reusable native semantics expanded |
| Solver recurrence, bound, or pruning | independent scalar/adversarial differential plus retained roots | a checkpoint is retained or live publication is proposed |
| Windows/process/input/parser/native boundary | focused Windows-relevant gate | the repository contract requires full dual-platform promotion gates |
| Live behavior candidate | exact model/native/replay and shadow delivery gates | it becomes physically eligible |
| Shared major integrated improvement | home-stage physical falsifier and one rotated sentinel | a milestone full-route diagnostic becomes eligible |

Do not routinely perform:

- repository-wide semantic audits for a local question;
- full Linux and Windows suites after documentation-only or isolated
  unchanged-boundary work;
- all-36, long-horizon, broad-corpus, RSS, or performance campaigns when a
  smaller distinguishing case answers the question;
- repeated physical runs of an unchanged candidate merely to seek a better
  aggregate hit total;
- new tooling, schema fields, dashboards, or notes without an immediate
  consumer and a named decision they unblock;
- repeated confirmation of an already retained invariant unless the current
  change can causally invalidate it.

Required authority gates are not optional. “Iteration first” means paying
each necessary gate once, at the point where its evidence can change
promotion, rejection, or implementation—not skipping safety, native
fidelity, delivery, physical, or acceptance evidence.

Evaluate agent progress primarily by:

1. how quickly the earliest unknown or mismatch moved forward;
2. whether a hypothesis was decisively accepted, rejected, or narrowed;
3. whether exact/native/physical coverage increased on a relevant root;
4. whether measured solve or branch latency improved without losing
   authority; and
5. whether the next agent can continue from a smaller, clearer open problem.

Test count, audit breadth, document volume, and number of generated artifacts
are not progress metrics.

### 0.2 Global-outcome rule: no self-referential optimization

The primary selection criterion is whether work can causally improve the
general solver, planner, delivery deadline, or physical hit outcome. An
“optimization” is not successful merely because it:

- adds abstractions, fields, reports, tests, or infrastructure;
- improves an isolated microbenchmark outside the consumed path;
- passes a larger suite;
- produces a more sophisticated score or visualization;
- wins one tuned spell/root while degrading or remaining unknown elsewhere;
  or
- changes an offline label that never reaches the live issued action.

Before implementation, every optimization must state:

1. the earliest live/model decision it can change;
2. the causal path from the change to survival, feasible planning, or issue
   latency;
3. a predeclared fixed-root or held-out metric that can falsify it;
4. the expected cross-stage mechanism rather than only a named spell;
5. the maximum engineering/test cost justified before the first useful
   measurement; and
6. what result causes immediate rejection or deprioritization.

Acceptable leading indicators include:

- moving a canonical fixed-root first hit later or finding an exact no-hit
  policy;
- eliminating a native/model first mismatch that changes a hazard, action,
  resource, or reachable policy;
- reducing false-safe or false-losing decisions on held-out roots;
- increasing exact feasible-root/action coverage without a retained-root
  regression;
- reducing measured end-to-end solve/publication age enough to enable a
  longer horizon, larger action set, or on-time issue;
- preventing verified hostile emissions through earlier enemy removal;
- reaching later phases with safer entry tubes or useful Power without
  leaving the viable set; and
- reducing focused-physical hits or advancing the clean-route first-hit
  frontier under an immutable candidate.

A single different-RNG aggregate hit total is an ultimate-outcome observation,
not a causal A/B. First establish the mechanism on identical native roots,
then validate generalization on unseen roots and focused physical workloads.

Foundational semantic work is allowed when it has a short, named line of sight
to one of these indicators—for example, resolving the first missing event
that blocks action-conditioned planning. Open-ended completeness work with no
current consumer is deprioritized.

Tests and checks are supporting gates, not the center of a solver task. Once
the smallest relevant check establishes the decision, the agent should return
to implementation, branching, measurement, or physical falsification.
Unrelated pre-existing failures are recorded and left alone unless they block
the required gate; agents must not spend the iteration polishing unrelated
details.

### 0.3 General mechanics before stage/spell tuning

The default research order is:

1. shared sensing, update order, movement, input, collision, event, combat,
   item, and resource semantics;
2. game-wide solver recurrence, recovery, action selection, and delivery;
3. event/enemy-class policies that generalize across stages;
4. route/phase options with explicit state and resources;
5. named stage/spell profiles only when retained evidence proves a universal
   rule is insufficient.

Do not begin by adding a constant, waypoint, weight, or action rule keyed to
one stage or spell merely because it improves its development root. A reusable
candidate must state the invariant it exploits and be evaluated on:

- development roots containing that mechanism;
- unseen roots from at least one different stage or event family; and
- the home/sentinel physical gates required by its authority rung.

Stage/spell-specific behavior is permitted only when the content is genuinely
different, the reason is modeled explicitly, and the rule lives in a
versioned profile rather than universal mechanics. It remains workload-local
until the planned physical gate passes.

One mature Stage-5 wind tunnel may be used for fast development, but it must
not silently turn Stage-5 behavior into the global solver. Prefer improving a
mechanism that solves many roots over squeezing one more frame from one tuned
replay.

## 1. Program Objective

### 1.1 Physical success definition

The immediate program target is:

- Touhou 8 version 1.00d;
- Sakuya/Remilia;
- Lunatic;
- Route 2 / Final B;
- normal full-route start from Stage 1 at Power 0;
- zero native hit edges from gameplay start through route completion;
- zero Bomb actions and no observed Bomb bit `0x02`;
- no manual gameplay input, manual `Z`, foreground contamination, debugger
  interference, or unrecorded intervention;
- complete dialogue and stage transitions;
- exact cleanup with every injected key released;
- a replay-capable raw bundle and compact, content-addressed report.

The no-life-decrement patch is research instrumentation. It never converts a
run into a pass: any native hit edge rejects NMNB.

Use the existing acceptance vocabulary:

- **NMNB-1:** one uncontaminated, complete, accepted Lunatic Route-2 NMNB run.
- **NMNB-R:** at least two additional RNG-distinct accepted runs, with at
  least two consecutive successes in the validation set.

NMNB-1 proves one physical witness. It is not a robust success-rate claim.

The repository's ultimate acceptance target also includes Extra. This
taskbook deliberately closes the Lunatic loop first; after NMNB-R, the same
root/event/model/physical machinery becomes the Extra program rather than a
new architecture project.

### 1.2 Mandatory Lunatic physical workloads

Four scene families are mandatory before integrated full-route promotion:

1. Lunatic Stage 3;
2. Lunatic Stage 4A;
3. Lunatic Stage 5;
4. Lunatic Final B;
5. followed by the complete non-practice Lunatic Route-2 run.

Stage 1 and Stage 2 remain regression and route-resource obligations. They are
not current primary research scenes, but any new first hit there immediately
promotes that phase into the focused workload queue.

There are two distinct physical evidence layers:

- **Mechanics-focused stage practice:** original-game Practice Start, useful
  for geometry, event, cadence, delivery, and phase falsification. Practice
  resources are not route authority.
- **Route-faithful prefix/full route:** normal Stage-1 Power-0 start,
  preserving earned Power, items, damage, position, RNG, dialogue, and
  transition history. Only this layer answers the route/resource question.

THPRAC or another modified-game scene launcher, if developed, is a third,
diagnostic-only layer. It can generate roots and exercise mechanics, but it
cannot substitute for either original-game physical layer.

Within the route-faithful layer, distinguish:

- **Milestone full-route diagnostic:** one non-practice Power-0 run after a
  major integrated improvement, used to discover real end-to-end effects and
  the next clean-route bottleneck. It need not wait for every stage to be
  clean.
- **Acceptance full route:** a fully eligible run evaluated against every
  NMNB-1/NMNB-R condition.

A diagnostic run that happens to satisfy every acceptance condition becomes
NMNB-1; the label assigned before launch does not reduce valid evidence.

### 1.3 Non-goals

The current program does not require:

- a portable replacement executable;
- faithful rendering, audio, menus, or animation;
- a full TH08 decompilation before useful progress;
- a screenshot/RL controller as the safety authority;
- forcing future RNG equal after different actions consume RNG differently;
- replaying an action-incompatible recorded future;
- treating one aggregate hit total from a different RNG seed as causal A/B;
- treating THPRAC, Wine, Hourglass, or libTAS as physical acceptance;
- treating Python/C++ parity as native-model validity; or
- using Bomb as a recovery action.

## 2. Authority Ladder And Non-Negotiable Contracts

### 2.1 Evidence planes

| Plane | What it can establish | What it cannot establish |
| --- | --- | --- |
| Static asset/decomp evidence | candidate formats, addresses, event identities, hypotheses | shipped runtime order or physical behavior by itself |
| Independent scalar/adversarial oracle | recurrence and implementation mistakes in the declared finite model | fidelity of that model to TH08 |
| Rebuilt `ModelTrajectory` | deterministic prediction for declared mechanics and events | unsupported event classes or live delivery |
| Rolling native snapshot wind tunnel | original-engine counterfactuals from one explicit root and supported epoch | another root, complete stage, live sensing, or Windows issue timing |
| Native replay/natural frame pump | same-seed original-engine semantic validation at an exact seam | robust live control or route-resource validity |
| Shadow live execution | deadline, contention, observation, and would-have-issued evidence | changed physical behavior |
| Focused original-game physical stage | actual sensing, issue, pickup, transition, and survival on that workload | full-route resources or robustness across RNG |
| Route-faithful full run | the actual Lunatic NMNB objective for one natural history | a robust success rate until repeated |

Never silently move a claim upward in this table.

### 2.2 Action, observation, and timing rules

Every model/planner task must preserve these contracts:

- The policy may condition only on observations available at its decision.
- Hidden branches producing the same next observation must merge before the
  next controller maximization; solving them separately is clairvoyant.
- Cadence uncertainty and command pickup delay are different uncertainties.
- Cadence branches recursively through the declared recurrence; it is not a
  one-time root choice or simply the maximum interval.
- Selecting the complete mask already held is no-write. It samples no new
  delay, preserves a pending command, and advances its remaining support.
- `input_current` is evidence of active native input. Desired or last-issued
  input is not equivalent.
- The full complete-mask action set and Shot/Focus behavior must be versioned.
  Bomb bit `0x02` is forbidden.
- `enemy_manager_frame` is not a universal physical input clock. During
  dialogue or transition freezes, held input may continue moving the player.
- A repeated manager frame does not justify an arbitrary wall-time guard.
- The issue-time consumer uses exact immutable-version matching and a fresh
  local hard certificate; a miss falls back safely.
- Timeout or incomplete search enlarges the unresolved-action set. It does
  not prove losing.

### 2.3 Root and future rules

A branch root is valid only when it captures the state needed by its horizon,
including as applicable:

- executable, route, difficulty, stage, phase, physical clock, and ECL image
  identity;
- player position/motion/mode, active input, desired/held input, pending
  command belief, resources, damage, and phase;
- enemy allocation generation, template, ECL/callback/timer contexts, and
  lifecycle;
- bullet, laser, item, body, transform, and collision-enable state;
- shared gameplay RNG state and causally ordered RNG consumption;
- timeline program counters, callbacks, spawn/end events, and same-update
  ordering;
- external transition state required by the declared horizon; and
- immutable session/root IDs, thread/mapping/stack/FPU epoch checks.

Branches A and B start from the same root and initial RNG state. After actions
diverge, each branch consumes RNG and mutates the world according to its own
native causal history.

Unsupported mutations, mapping/thread/stack changes, missing event data, or
unknown external state return `UNKNOWN`. They are not filled from a recorded
future.

## 3. Current Foundation And Open Gap

### 3.1 Observed foundation as of 2026-07-30

The current retained infrastructure has already crossed the important
feasibility threshold:

- One same-session rolling native root at Stage-5 replay frame/manager frame
  2,129 can be restored and stepped through the original calculation chain.
- All 36 canonical no-Bomb complete-mask branches have been evaluated at H=8
  with exact root restore and retained semantic capture.
- Promoted causal subroots produced an H=32 no-hit native witness:
  `0x94 -> 0x44 -> 0x10 -> 0xA4`.
- The same schedule matched 32/32 natural-frame-pump native
  collision/control projections and compact states.
- Native evidence localized the original first hit to bullet slot 45 at
  manager frame 2,136.
- Native/model differential corrected player-center playfield bounds.
- A retained constant-velocity fixture corrected closed-form motion into
  native-like per-update binary32 storage.
- Replay saving, replay identity, result-menu automation, compact reporting,
  Linux/Windows gates, and exact process cleanup exist.

This is fixed-root offline diagnostic and candidate-search authority. It is
not yet complete hazard, collision, planner, live, stage, or route authority.

### 3.2 Immediate semantic gap

The next useful gate remains:

> A model-consumable hostile-state capsule with an explicit ordered
> birth/redirect/transform/laser/event ledger, driving a causal
> `ModelTrajectory` and planner replay to a real first mismatch or an explicit
> `UNKNOWN`.

The current root proves that native branching works. It does not yet provide
the complete generative data needed for the rebuilt engine to explain every
hostile transition over H=32.

### 3.3 Larger open gaps

- Event-class coverage exists primarily around one Stage-5 first-hit root.
- Full enemy/ECL/callback/timeline and laser evolution is incomplete.
- Integrated model collision/planner parity remains `UNKNOWN`.
- The exact finite recurrence and the native world model are not yet joined
  into a closed-loop policy over a representative multi-root corpus.
- Candidate publication remains shadow-only unless explicitly promoted.
- Live command pickup, no-write, cadence, frozen-manager transitions, and
  issue deadline remain physical obligations.
- Combat, boss damage, kills/despawns, drops, collection, Power, and route
  phase timing are not yet a complete hard-resource model.
- A single clean fixed root says nothing about RNG-root robustness.
- Full-route acceptance has not been achieved.

Any uncommitted in-progress hostile-capsule or H1 work in the shared workspace
must be treated as another agent's work until it is verified and retained.
Future agents must inspect the current handoff rather than restarting it.

### 3.4 Current solver shape

The current solver is a layered robust-control system rather than one
monolithic search:

1. native sensing and action-conditioned hazard projection;
2. a coarse backward robust-viability corridor;
3. a short-horizon local beam that proposes movement;
4. a fresh issue-time collision certificate;
5. versioned action publication and live delivery.

The retained live configuration is approximately:

- global corridor grid step 16 px;
- 8 physical frames per viability layer;
- 80-frame global horizon;
- local beam horizon 10, beam width 24, and action hold 2;
- 17 principal movement/Focus actions in the tactical planner;
- 36 canonical complete no-Bomb masks at the physical issue boundary:
  Focus/unfocus x nine direction/stay choices x Shot on/off.

The exact offline formulation is stronger than the currently promoted live
state. It represents active input, held/desired input, a pending-command
belief, remaining pickup-delay support, recursive cadence, and
observation-compatible hidden-branch merging. Representative unrestricted
instances remain too expensive for direct issue-time use, so budgeted
attainable policies, exact candidate verification, and dual lower/upper
bounds are the intended bridge.

This subsection records observed architecture and configuration. It does not
assert that every layer is physically valid on every event class or that the
current live compression is equivalent to the exact belief recurrence.

### 3.5 Algorithm direction decision

**Inferred direction:** retain the robust viability/belief foundation. Do not
replace it wholesale with ordinary path search, a larger beam, Monte Carlo,
or a learned policy.

The physical problem is a partially observed robust reach-avoid game:

```text
controller chooses one observable-history action
          |
          v
nature selects every physically reachable cadence/pickup/hidden branch
          |
          v
indistinguishable successor branches merge by observation
          |
          v
the controller chooses again
```

Backward viability, exact belief semantics, attainable lower bounds,
admissible upper bounds, and fresh issue-time certification match this
quantifier structure. NMNB needs one physically executable feasible policy;
it does not require unrestricted or globally unique optimality.

The current direction nevertheless has four material gaps:

1. **Generative future fidelity.** Missing birth, redirect, transform, laser,
   callback, lifecycle, combat, or phase events invalidate a planner result
   before search quality matters.
2. **Coarse false loss.** A 16-px/8-frame lattice can erase a narrow real
   continuation and return an empty kernel.
3. **Unproved recovery bridge.** Endpoint distance to a viable cell does not
   prove a collision-free, delay-robust path to that cell.
4. **Missing route layer.** Short-term survival alone does not choose safe
   phase entry position, Shot schedule, damage timing, Power, items, or
   resource-compatible continuation.

The local beam remains useful, but only as a proposal and ordering mechanism.
Beam width, deduplication, and endpoint ranking can discard the only safe
continuation; an exact verifier or hard local certificate remains decisive.

This is a research decision, not an efficacy claim. Every proposed successor
below remains **hypothesized** until an agent implements it, measures it on
retained development and validation roots, passes the declared native/model
gates, and pays the appropriate focused physical debt.

### 3.6 Intended solver hierarchy

Develop toward three decision scales with one ground-truth envelope:

```text
phase/route/resource option planner
  seconds-scale proposal: target tube, Shot/Focus schedule, resources
                  |
                  v
adaptive robust reachability over a sparse reachable belief tube
  32-80 frame hard finite model: admissible root-action set
                  |
                  v
local beam or learned proposer
  approximately 10 frame fast candidate ordering
                  |
                  v
fresh issue-time complete-mask pipeline certificate
  hard delay/no-write/collision gate and fail-closed fallback

rolling native wind tunnel surrounds every layer as original-engine oracle,
counterexample generator, and fixed-root evaluation environment
```

The preferred tactical successor is an observation-keyed sparse AND-OR/CEGIS
search over the reachable belief tube:

1. warm-start with the current policy, local beam, or a retained native
   witness;
2. exactly verify the executable candidate to obtain an attainable lower
   bound;
3. compute an admissible optimistic upper bound;
4. find the first observation/root action where the bounds disagree;
5. refine only that action, belief branch, time interval, or spatial region;
6. reverify the complete candidate before raising its lower bound;
7. stop for feasibility as soon as one full-horizon exact witness exists;
8. retain unresolved actions as unresolved on timeout.

This is a natural extension of the current dual-bound synthesis, not a new
authority model. AO*/LAO*-like best-first ordering may be used internally
only if controller-exists/nature-for-all quantifiers, observation merging,
complete root actions, and admissible bounds remain exact.

The preferred replacement for raw `recovery_distance` is a query-local robust
recovery-band recurrence:

- construct a time-expanded AND-OR graph only over states reachable from the
  current root;
- use the next verified viable kernel as the terminal set;
- require every declared cadence/pickup branch to reach that set without
  collision;
- refine near obstacles, narrow corridors, and lower/upper-bound disagreement;
- preserve vector transitions and nearest-lattice clearance error;
- return `UNKNOWN`, not safe, when the refinement or event support is
  incomplete.

Before reducing conservatism by shrinking timing uncertainty, infer and
revalidate a finite scheduler/actuator automaton from native traces. Remove
only cadence/delay combinations proved physically unreachable. Reading an
additional native state is useful only when that state is legitimately
available before the decision; it must not become hidden-state clairvoyance.

### 3.7 Objective and action-factor rules

Keep objectives lexicographic:

1. guaranteed collision-free survival;
2. safe continuation into a verified terminal viability kernel;
3. robust controllability reserve, such as verified safe successor actions
   or repair volume;
4. worst bottleneck signed clearance;
5. route, damage, item, Power, collection, and position preferences inside
   the viable set.

Do not replace these levels with one weighted sum. In particular, raw
distance to the kernel and high immediate clearance may both prefer a state
with no robust continuation.

Do not naively double every exact tactical layer from 17 to 36 actions without
measuring the causal need and deadline cost. A declared fixed-Shot policy can
be a valid restricted feasibility witness. However:

- Shot/Focus effects on damage, enemy lifetime, phase time, resources, and RNG
  must be modeled;
- a tactical movement choice must ultimately issue and certify one complete
  mask;
- Shot may be factored into a slower phase option only while the resulting
  observation/action partition remains causal;
- failure of the restricted policy triggers deliberate action-set expansion,
  not a claim that the physical root is losing.

### 3.8 Alternative-algorithm roles

| Method | Appropriate role | Why it is not the current hard authority |
| --- | --- | --- |
| A*, Dijkstra, robust AND-OR A* | recovery-band search and deterministic subproblems | ordinary versions omit hidden-branch merging and controller/nature quantifiers |
| MPC or MIQP | smooth trajectory and route proposal | non-convex bullets, discrete delay, and future births make a live universal proof expensive |
| Hamilton-Jacobi reachability | local adaptive tube or conceptual viability oracle | the complete hybrid belief state is too high-dimensional for a uniform live solve |
| MCTS or Monte Carlo | candidate ordering and corpus exploration | sampling can miss a rare but lethal timing branch |
| RL or imitation | proposal/ranking model trained from wind-tunnel exact labels | no hard robustness or physical-model authority |
| Control barrier filter | very short-horizon emergency supplement | delayed discrete input, non-convex safe sets, and future births make it incomplete |
| SAT/SMT/MILP/BMC | bounded offline verifier and counterexample shrinker | unsuitable as the default per-issue live core without measured evidence |
| Native snapshot exhaustive search | ground-truth candidate discovery and validation | one fixed root can overfit and does not prove live delivery or cross-root robustness |

No method in this table is rejected as a research tool. Its output must enter
the authority ladder at the correct rung.

## 4. The Closed Research Loop

### 4.1 One canonical loop

```text
original-game physical stage/full route
          |
          v
canonical first hit + replay + compact dossier
          |
          v
content-addressed NativeRootCapsule before the hit
          |
          v
rolling native all-action causal branches
          |
          v
NativeTrajectory <-> ModelTrajectory first mismatch
          |
          v
classify responsible layer and build minimal falsifier
          |
          v
smallest evidence-backed correction, new immutable version
          |
          v
scalar/adversarial -> model -> native root -> replay/natural gates
          |
          v
shadow deadline/delivery and fresh issue certificate
          |
          v
same named original-game physical workload
          |
          +---- failure: retain new first hit and loop again
          |
          +---- success: repeat distinct root, then expand one level
```

### 4.2 Nested loops

The program runs four nested loops:

1. **Per-root loop:** eliminate or explain one canonical first hit.
2. **Per-event-class loop:** prove the model/executor across multiple roots
   containing the same spawn, redirect, transform, body, laser, collision, or
   transition behavior.
3. **Per-stage loop:** test the exact candidate on its primary workload and a
   deliberately different sentinel workload before claiming reusable
   mechanics.
4. **Route loop:** after major integrated improvements, sample the real
   Stage-1 Power-0 route; preserve history through Stage 3, Stage 4A, Stage 5,
   Final B, and route completion.

Do not jump from a per-root witness directly to route authority. Conversely,
do not wait for a complete game model before using a per-root physical
falsifier.

The per-stage loop is adaptive, not an instruction to run all four stages
after every edit:

- A content-local correction first pays physical debt on its **home stage**.
- A reusable movement, geometry, event, planner, clock, or delivery correction
  also pays **cross-stage generalization debt** on one non-home sentinel
  selected for a different failure signature.
- A complete Stage-3/4A/5/Final-B sweep is reserved for an integrated model/
  policy milestone, explicit strategy promotion, or full-route preflight.
- One full-route diagnostic is appropriate after a major integrated
  improvement that has paid its home-stage and sentinel debt. Acceptance
  repeats remain sparse route-authority gates.

Keep three evidence partitions:

1. **development roots**, used to locate and fix mismatches;
2. **validation/sentinel roots**, not used to choose the correction; and
3. **physical holdouts**, natural RNG histories not repeatedly tuned against.

When a holdout failure becomes a development case, relabel it and nominate a
new holdout. Do not keep calling a repeatedly inspected root “unseen.”

### 4.3 Detailed iteration protocol

For each physical failure or retained counterexample:

1. Freeze the exact source checkpoint, model/policy version, executable,
   replay, workload, route, difficulty, and evidence cutoff.
2. Select the first clean-route native hit as the canonical witness. Later
   contacts are secondary geometry/workload evidence.
3. Attribute the hit to exact phase, native object/slot/generation, signed
   clearance, active input, desired input, and observation/issue timeline.
4. Capture the closest valid pre-hit native root. Reject crossed seams,
   action-incompatible futures, or incomplete epoch ownership.
5. Replay the recorded action as a canary. Require exact parent-root replay
   and restore before branching.
6. Run the smallest distinguishing action set first. Use all 36 no-Bomb masks
   as a retained root gate, not as a mandatory cost for every source edit.
7. Emit per-frame `NativeTrajectory`, causal event ledger, and branch outcome.
8. Run the same root, action, and horizon through `ModelTrajectory`.
9. Stop at the earliest mismatch. Do not debug later differences first.
10. Classify the failure, write the minimal falsifier, and change only the
    responsible layer.
11. Create a new immutable model/policy version. Never rewrite the old
    candidate under the same identity.
12. Run independent scalar/adversarial tests, focused implementation tests,
    native differential, representative all-action/root gates, and replay or
    natural-frame validation.
13. If the behavior may affect live input, run side-effect-free shadow and
    deadline/delivery checks.
14. Name the home workload and whether the change is content-local or
    reusable. For reusable behavior, also name one non-home sentinel and its
    selection reason.
15. Once physically eligible, run the home workload before stacking another
    behavior-changing candidate for that workload. Pay cross-stage debt before
    claiming reusable or integrated authority, not necessarily before the
    next local model experiment.
16. Retain success or failure, update the strategy ledger only if its
    promotion gate passed, and select the next first hit/root.

### 4.4 Failure classification and return path

| Class | Typical evidence | Return to |
| --- | --- | --- |
| EXP | wrong route/team, manual input, foreground loss, crossed seam, corrupt replay | experiment/supervisor; rerun without model changes |
| ROOT | restore mismatch, mapping/thread/stack/FPU epoch change, external-state poison | snapshot executor and rebootstrap policy |
| OBS | stale/missing native field, allocation generation ambiguity, async capture gap | sensor/capsule schema and atomic capture |
| EVT | wrong birth, redirect, transform, laser, callback, timer, RNG, lifecycle, collision order | native semantic revalidation and event model |
| MOD | correct event ledger but wrong movement, float32, geometry, state transition | rebuilt engine/model |
| SOL | correct trajectory but wrong recurrence, hidden-branch clairvoyance, unsound pruning, false loss | scalar oracle, exact solver, verifier |
| DEL | good offline action but stale publication, pickup/no-write mismatch, cadence, frozen clock, deadline | live delivery and actuator model |
| RES | local survival causes wrong kill/despawn/drop/Power/damage/phase history | combat/resource/route model |
| PERF | exact result misses issue deadline or branch throughput blocks corpus expansion | measured optimization only |

If classification is ambiguous, design one experiment that separates two
classes. Do not patch both simultaneously.

## 5. Research Workstreams

### WS-A — Content And Event Atlas

Goal: know what content and event classes exist before claiming coverage.

Primary external input: `thtk`.

Deliverables:

- content-addressed extraction manifest for TH08 ECL/STD/ANM/MSG assets;
- canonical symbolic identity for stage, subroutine, instruction offset,
  callback, and difficulty/route reachability;
- inventory of births, redirects, transforms, lasers, waits, callbacks,
  indexed enemies, phase transitions, and unknown opcodes;
- runtime ECL/timeline pointer-to-static-instruction mapping;
- mandatory-scene coverage matrix for Stage 3, 4A, 5, and Final B;
- parser round-trip/differential fixtures.

Exit gate:

- every retained native event identifies its content version and symbolic
  origin, or is explicitly dynamic/unknown;
- `thtk` output agrees with independent repository parsing at the format
  boundary;
- no claim is made that `thtk` defines runtime order or side effects.

### WS-B — Diagnostic Scene Factory

Goal: reach difficult mechanics quickly without waiting for a full route.

Primary external input: `thprac`, used only as a source of scene/bootstrap
ideas and TH08 section taxonomy.

Deliverables:

- a separate modified-game diagnostic launcher or recipe catalog;
- explicit scene contracts covering stage/section/phase, difficulty, team,
  Power, rank, gauge, resources, ECL/image identity, and patches;
- small scene set for spawn, redirect, transform, body, laser, callback,
  dialogue/frozen-manager, and phase transition events;
- paired natural original-game roots for any scene used to support a model
  correction.

Exit gate:

- modified-scene evidence is labeled diagnostic;
- natural original-game event fingerprints agree over the declared horizon
  before the scene is used as semantic evidence;
- no THPRAC/custom replay enters final physical acceptance.

### WS-C — Native Root And Wind-Tunnel Ground Truth

Goal: make the original executable a fast, causal, exact short-prefix oracle.

Deliverables:

- `NativeRootCapsule` with hostile inventory and ordered event ledger;
- deterministic H1, then H8, then H32 step/restore canaries;
- root/branch/session poison state and automatic replay rebootstrap;
- exact action portfolio with branch-specific RNG and future events;
- multi-root corpus spanning mandatory stages and event classes;
- first-mismatch-ready native trajectory artifacts.

Exit gate per root:

- recorded-action parent replay exact;
- root restore exact;
- epoch/thread/mapping/stack/FPU checks exact;
- unsupported mutations fail closed;
- representative actions match natural frame-pump execution;
- all-36 gate completed before a root is called a canonical portfolio root.

Do not build a permanent warm service merely because bootstrap is annoying.
Build it only after branch throughput is the measured bottleneck and include
single writer, immutable IDs, cancellation, idle TTL, poison cleanup, and
auto-rebootstrap.

### WS-D — Selective Native Semantic Reconstruction

Goal: reconstruct only native behavior needed by observed first mismatches.

Primary inputs: shipped instructions/dataflow, IDA, runtime probes, and
`th08-decomp` as a hypothesis/matching reference.

Protocol:

1. start from one native/model first mismatch;
2. identify the smallest producer/consumer/caller closure;
3. revalidate inherited IDA names, types, offsets, order, and calling
   convention;
4. for a critical routine, compare the same address/behavior with every
   relevant pinned external reconstruction or format reference before
   finalizing the interpretation;
5. write an explicit agreement/disagreement table covering control flow,
   fields, units, signedness, update order, RNG, and callers/callees;
6. resolve every material disagreement against the shipped instructions and
   a bounded runtime probe rather than choosing the more convenient source;
7. write a minimal independent falsifier;
8. implement only the reached semantic slice;
9. compare against native fixtures and, where useful, matching/reccmp
   discipline.

“Critical routine” means one whose interpretation can change sensing,
hazard/event generation, collision, movement/input timing, Shot/Focus,
damage/kill/despawn, items/Power, RNG, solver transitions, or issued actions.
Menu, rendering, and unrelated routines do not justify an external-comparison
campaign.

Relevant external sources include the locally pinned `th08-decomp`, `thtk`,
and `eclmap` snapshots and any later pinned TH08 reconstruction named by
`START_HERE.md`. They are independent hypotheses, not a vote. Record the
exact upstream commit and license; never copy unlicensed material into the
repository.

Exit gate:

- native instructions/dataflow and runtime evidence support the conclusion;
- relevant external implementations were compared for critical routines, or
  the task records why no comparable implementation exists;
- material agreement and disagreement are recorded compactly;
- misleading IDA annotations and affected notes are corrected;
- independent tests cover the distinguishing boundary;
- no completeness claim extends beyond reached event classes.

### WS-E — Rebuilt Short-Prefix Engine

Goal: produce a deterministic `state.step(complete_mask)` engine exact over
declared roots/events/horizons.

Architectural inspiration: PyTouhou's separation of gameplay stepping from
rendering. TH06 semantics are not imported.

Required shape:

- immutable explicit state;
- one native-order update per step;
- renderer/audio/UI-free core;
- ordered event ledger;
- explicit float32 stores and same-frame priority;
- generation-aware pools;
- action-conditioned Shot/Focus/damage/RNG behavior;
- exact collision geometry and enable schedules;
- explicit `UNKNOWN` for unsupported transitions.

Exit gate:

- per-frame bit-level or declared-tolerance parity against native roots;
- first mismatch is machine-readable and shrinks to a retained fixture;
- H1 parity precedes H8; H8 precedes H32;
- longer rollout authority grows only with event coverage, not elapsed time.

### WS-F — Robust Solver And Candidate Synthesis

Goal: turn exact short-prefix mechanics into causal survival policies.

Required work:

- independent scalar recurrence remains the formal oracle;
- full declared action set at the public root;
- recursive cadence and delay belief;
- observation-compatible branch merging;
- exact no-write semantics;
- signed-clearance survival objective;
- resource/combat objectives only inside the viable set;
- restricted candidates labeled attainable lower bounds;
- unresolved actions remain unresolved;
- exact witness and immutable publication identity.

Ordered research ladder:

1. complete enough native/model future coverage for the evaluated horizon;
2. revalidate the physically reachable scheduler/actuator automaton;
3. replace endpoint recovery distance with an exact query-local robust
   recovery band;
4. extend dual-bound synthesis into sparse observation-keyed belief-tube
   refinement;
5. factor phase-level Shot/Focus/resource options from tactical movement
   without weakening complete-mask issue semantics;
6. introduce learned, beam, or sampling proposals only after exact labels and
   validation partitions exist.

For each rung, compare the candidate with the retained predecessor on:

- identical development roots and complete action/root versions;
- unseen validation/sentinel roots;
- native/model first mismatch and exact survival horizon;
- false-safe, false-losing, and `UNKNOWN` counts;
- attainable lower-bound quality and unresolved root actions;
- decode/lower/solve/verify/publication timing at p50, p95, and worst case;
- memory use, cancellation, stale-version rejection, and issue-time misses;
- home-stage and cross-stage physical debt.

Research use of learned or approximate methods:

- native wind-tunnel labels may train action ranking, heuristic ordering, or
  proposal models;
- beam, learned, Monte Carlo, or MCTS results remain proposal-only;
- training roots, validation roots, and physical holdouts remain disjoint;
- every promoted action still needs the exact verifier and issue-time hard
  certificate.

Exit gate:

- exact universal verification over the declared finite model;
- Python/C++ parity against an independent scalar oracle;
- native-root replay shows the policy, not only one open-loop action, survives
  the declared horizon;
- publication meets deadline and immutable-version contracts;
- the new method wins on a predeclared metric or resolves a retained
  counterexample without losing prior exact roots;
- focused physical execution, followed by a rotated sentinel for shared
  changes, determines actual promotion.

A method that is faster offline but creates more false-safe actions, misses
issue time, or fails its home/sentinel physical gate is not promoted. A method
that appears physically better on one different-RNG aggregate run is
interesting discovery evidence, not a causal algorithm comparison.

### WS-G — Live Sensing, Publication, And Delivery

Goal: ensure a correct offline action is the action physically applied in
time.

Deliverables:

- root freshness and observation-age evidence;
- active versus desired/held/pending action trace;
- no-write/pickup-delay trace;
- recursive cadence and issue deadline telemetry;
- manager-freeze/dialogue state and wall-time-safe neutralization contract;
- foreground/transition/cleanup evidence;
- side-effect-free shadow comparison;
- fresh local hard certificate at issue.

Exit gate:

- shadow exact-version lookup is ready before issue;
- no worker/contention regression changes live cadence;
- pickup/no-write behavior matches the declared model;
- focused physical action delivery is observed on the target scene;
- strategy promotion is explicit in `STRATEGY.md`.

### WS-H — Route, Combat, And Resource Control

Goal: preserve survival while reaching the same later attacks with feasible
Power, damage, position, items, and phase timing.

Initial general policy hypotheses, ordered for early falsification:

1. **Unfocused opportunity:** when an exact candidate remains viable and does
   not require precise micro-movement, releasing Shift may provide faster
   travel and wider Sakuya shot coverage, killing distributed enemies sooner.
2. **Kill-before-saturation:** for killable ordinary emitters whose later
   volleys depend on remaining alive, survival-filtered early damage may be
   better than pure evasion.
3. **Power-0 acquisition:** during safer early-route windows, collect useful
   Power only among survival-feasible actions so later combat is not evaluated
   under unrealistic practice-mode max Power.

These are hypotheses, not unconditional rules. Prefer semantic regimes over a
coarse spell flag:

- killable emitters with preventable future volleys use survival as the hard
  constraint and verified kill/exposure reduction as a secondary objective;
- spell and boss phases remain survival-first, while
  survival-equivalent damage may be considered only if it measurably shortens
  dangerous exposure;
- scripted invulnerability, timeout, forced despawn, or bullets that persist
  after source death must not receive a fictional “kill quickly” benefit;
- Focus may be released only through an exactly verified complete-mask policy,
  with refocus before dense geometry or loss of robust reserve;
- Power collection remains inside the viable set and must carry natural
  route history forward.

The NMNB planner does not optimize post-death Power recovery. After a native
hit the acceptance history has already failed. Patched continuation may retain
post-hit items and Power for diagnostics, but those states do not justify or
train the accepted no-miss policy.

Deliverables:

- generation-aware enemy source lifetime and kill/despawn reason;
- verified linkage from source lifetime to future hostile emissions;
- enemy damageability, HP delta, targeting, shot coverage, and kill deadline;
- Shot/Focus action-conditioned damage and RNG effects;
- item/drop/pickup/Power ledger;
- Power thresholds and their action-conditioned effect on shot/damage;
- boss HP/phase/timer transition model;
- hard life/Bomb constraints;
- safe progress objectives only within exact viability;
- route-prefix capsules from Stage-1 Power-0 history.

Exit gate:

- fixed-root ablations distinguish pure evasion, focused fire, and dynamic
  unfocused/refocused policies without reusing action-incompatible futures;
- earlier verified kills demonstrably prevent emissions or shorten exposure
  on development roots and unseen event/stage roots;
- Power collection improves later causal capability or is rejected where its
  movement risk outweighs the benefit;
- local dodge improvement does not create a later unmodeled resource failure;
- route-prefix replay and original game agree on resources and phase entry;
- no practice-injected state is used for route authority.

Current execution checkpoint, 2026-07-31:

- implemented offline/synthetic authority now spans exact stage/root enemy
  generations, resolved HP-damage transactions, end reason, defeat-item
  allocation, pickup/resource delta, and Power-threshold joins in one ordered
  v4 lifecycle schema;
- the joined candidate report retains observed damage count/total/frames and
  the downstream item/resource chain without treating occurrence as causal
  benefit;
- rolling native snapshot v5 and causal-search v3 now retain the complete
  128-slot player-shot pool identity, decoded active shot state, both shot
  timers, active enemy HP/hitbox/gate state, and supported instantaneous
  ordinary-shot overlaps from each immutable native root and future tick;
- the strict combat branch lowerer admits only accepted deterministic
  transactions, rejects native player-phase-2 branches as a hard survival
  filter, and keeps HP-sum change, published frame damage, and supported
  overlap as non-ranking observed/proxy metrics;
- a SHA-pinned shipped-content audit proves all 53 Route-2 normal
  Power-selector records are type 0 with zero update/hit callbacks; focused
  callback 7 is emission-only, while secondary levels 6/7 remain a separate
  Bomb-only override;
- native roots now expose incompatible active slots, so this content closure
  applies only to exact Route-2, zero-Bomb, no-hit histories whose root and
  future slots stay compatible;
- combat projection v2 now reverses the complete loaded-SHT relocation and
  requires both pinned byte identities; rolling v6/causal-search v4 classify
  every active source pointer as exact normal, Bomb-only special, or unknown
  at the root and every future tick;
- field-compatible but unowned pointers remain explicit unknowns in the
  non-ranking branch report; no v6/v4 native corpus has been observed;
- no runtime v4 event has been observed, so target-motion/action attribution,
  no v5/v3 combat corpus has been captured, and generation-safe kill,
  prevented hostile births, safe collection, later benefit, and every exit
  gate above remain open; and
- continue higher-ROI general WS-H foundations while runtime authorization is
  absent rather than returning to isolated hit-producer detail.

### WS-I — Optional TAS Acceleration

Goal: determine whether Hourglass or libTAS can cheaply generate native
counterfactual corpora without weakening authority.

This is optional and must not block WS-C through WS-H.

Hourglass hypothesis:

- same Windows/Win32/DX8 environment may offer process/thread savestate,
  deterministic time/input, stale-state recovery, and fast-forward.

libTAS hypothesis:

- Wine plus Lua memory/savestate APIs and soft-dirty/fork techniques may offer
  highly programmable, high-throughput branching.

Required bake-off:

1. exact executable and replay identity;
2. same canonical root and seam;
3. recorded parent trajectory exact;
4. save/load parent exact;
5. all-36 H1/H8 fingerprints exact;
6. representative birth/redirect/laser H32 roots exact;
7. end-to-end throughput and contamination measurement.

Default continuation rule:

- continue integration only with zero unexplained semantic mismatch and a
  predeclared material throughput gain, suggested at least 2x end-to-end;
- otherwise retain engineering lessons and stop.

Neither tool gains physical Windows acceptance authority. Avoid copying or
linking copyleft code into the solver without an explicit license decision.

## 6. Milestone Roadmap And Promotion Gates

### M0 — Rolling native wind tunnel foundation

Status: observed on the canonical Stage-5 root.

Already established:

- same-session root restore;
- H8 all-36 portfolio;
- causal subroot promotion;
- H32 native no-hit witness;
- natural-frame-pump parity;
- first player and hazard model corrections.

No agent should redo M0 from scratch unless a retained counterexample
invalidates it.

### M1 — Model-consumable hostile H1

Required:

- hostile bullet/enemy/laser/body inventory at the exact root seam;
- allocation generation and collision-enable identity;
- ordered birth/end/redirect/transform/laser ledger;
- one-step native and model trajectories;
- explicit first mismatch or H1 exactness;
- recorded-action restore/repeat canary.

Exit:

- H1 model/native parity for every declared hostile object at root2129, or a
  minimal retained first mismatch assigned to WS-C/D/E.

Physical gate:

- none merely for schema plumbing;
- if the correction changes integrated live behavior, it accrues physical
  debt for the relevant Stage-5 scene after M3/M5 gates.

### M2 — Event atlas and multi-root corpus

Required:

- `thtk`-backed immutable content manifest;
- event-class inventory for Stage 3, 4A, 5, Final B;
- at least one natural native root for each currently supported critical
  event class;
- diagnostic scene recipes where useful;
- explicit unsupported/unknown matrix.

Exit:

- coverage is measured by roots x event classes x horizon x actions, not by
  lines of code or time spent.

Physical gate:

- modified scene roots require paired natural original-game validation;
- no strategy promotion yet.

### M3 — Exact short-prefix model over representative roots

Required:

- H1 parity across the root corpus;
- H8 parity across all critical event classes;
- H32 parity for roots whose event ledger remains complete;
- exact collision/control summaries;
- machine-readable first mismatch and minimal fixtures;
- all-36 canonical portfolios on promotion roots.

Exit:

- no unexplained mismatch inside the declared support;
- every unsupported transition returns `UNKNOWN`;
- scalar/object/packed/native implementations agree where applicable.

Physical debt rule:

- once an integrated behavior-changing candidate passes M3, it may not be
  followed by another unrelated behavior-changing candidate for the same
  workload until M5 and the named physical falsifier are completed or the
  candidate is explicitly rejected;
- a home-stage pass grants workload-local evidence only;
- reusable-mechanic or integrated authority remains blocked by
  `cross_stage_debt` until a non-home sentinel passes;
- offline native/model validation should cover all mandatory-stage event
  corpora much more frequently than physical play.

### M4 — Closed-loop causal policy witnesses

Required:

- observation-compatible multi-decision policies, not open-loop replay
  suffixes;
- exact finite-model verification;
- candidate witnesses on multiple RNG-distinct native roots;
- stress cases for boundary, dense bullets, laser, spawn, redirect, phase
  transition, and no-write/pending input;
- survival labels separated from progress/resource labels.

Exit:

- at least one exact no-hit policy witness per active canonical root;
- no hidden-branch clairvoyance;
- no unresolved action reported as losing;
- root/action/version/witness records content-addressed.

Physical gate:

- still not eligible until M5 proves delivery and deadline behavior.

### M5 — Shadow and delivery readiness

Required:

- side-effect-free shadow execution;
- exact immutable-version lookup;
- deadline/CPU/contention measurements;
- fresh issue-time hard certificate;
- active/desired/pending/no-write telemetry;
- frozen-manager/dialogue and transition handling;
- fail-closed fallback.

Exit:

- proposed action is available and valid before issue on the target scene;
- shadow does not perturb live cadence;
- one exact candidate is designated for one named physical workload.

Physical gate:

- mandatory next checkpoint for that candidate's home workload, subject to
  explicit user authorization and the physical-run skill;
- if the change is reusable, schedule one rotated non-home sentinel before
  broader promotion. Do not automatically schedule the other three stages.

### M5R — Milestone full-route diagnostic

Purpose:

- observe the actual from-zero effect of a major improvement;
- expose cross-stage generalization, resource, transition, and route-history
  failures that stage practice cannot represent;
- choose the next canonical clean-route first hit.

A candidate qualifies as a major improvement when at least one is true:

- it changes a shared mechanic, solver recurrence, planner, delivery path, or
  resource model used by more than one mandatory stage;
- it resolves a dominant retained causal failure family across multiple
  native roots;
- it introduces a coherent new integrated model/policy version intended for
  broader live use; or
- it materially changes route-level Shot/Focus, damage, item, Power, phase, or
  transition behavior.

Entry gate:

- immutable integrated source/model/policy version;
- no known unexplained native/model mismatch in the exercised support;
- required Linux/Windows and report-integrity gates pass;
- the primary home-stage physical debt is paid;
- one non-home sentinel has passed for a reusable change;
- hard no-Bomb supervisor, replay, transition, and cleanup paths are ready;
- explicit user authorization.

Execution:

- start normal non-practice Lunatic Route 2 at Stage 1, Power 0;
- run the complete route when instrumentation permits, even after a hit, to
  collect workload-discovery evidence;
- score NMNB only from native hit/Bomb evidence, never from patched
  continuation;
- retain replay, raw bundle, compact dossier, and exact integrated version.

Interpretation:

- before the first hit, the run is clean route-faithful evidence;
- the first hit becomes the next canonical route bottleneck;
- after the first hit, later phases remain useful workload/mechanics evidence
  but are not independent clean-route survival samples;
- aggregate hit distribution may guide root collection but is not a causal
  A/B against a different RNG run;
- zero hit plus every acceptance condition immediately qualifies as NMNB-1.

Do not repeat an unchanged milestone diagnostic merely to chase a better
aggregate. Return to root/model work, or proceed to integration/acceptance
only when the evidence says so.

### M6 — Mandatory stage integration closure

M6 is an integration gate, not the per-edit inner loop. Most candidates reach
M6 only after fast root/model iteration, one home-stage falsifier, and—when
the changed mechanic is reusable—one cross-stage sentinel. M5R may occur
before M6 to discover real route behavior; M6 remains required before planned
acceptance promotion.

Development order:

1. Stage 5 first, because the canonical wind-tunnel infrastructure and first
   causal root already exist there;
2. Stage 3 for early resource, nonspell boundary, laser, and action-lag
   behavior;
3. Stage 4A for dense ECL/body/callback and frozen-manager behavior;
4. Final B for non-unit scale, lasers, funnels, long horizon, and phase
   transitions.

Route promotion is evaluated in natural route order:

1. Stage 3;
2. Stage 4A;
3. Stage 5;
4. Final B.

Exit per stage:

- one complete original-game mechanics-focused zero-hit/no-Bomb run is a
  physical witness, not robust acceptance;
- route-prefix evidence must preserve natural accumulated resources;
- recommended stage-readiness target is three RNG-distinct clean completes
  with at least two consecutive successes under the same immutable integrated
  candidate;
- the exact repetition threshold must be frozen in `STRATEGY.md` before it is
  used as promotion authority.

The repetition target above applies to stage-integration/route readiness, not
to every intermediate correction. During local development, one decisive
home-stage falsifier plus one appropriately rotated sentinel is normally the
maximum physical scope before returning to the wind tunnel.

Any first hit resets the per-root loop but does not erase earlier clean roots.

### M7 — Full-route NMNB-1

Entry:

- all four mandatory stages have fresh, compatible physical evidence;
- Stage 1/2 regressions pass;
- one immutable integrated candidate is frozen;
- route/resource history is modeled or conservatively guarded;
- supervisor, replay saving, transitions, foreground, and cleanup pass.

Execution:

- normal non-practice Stage-1 Power-0 Route-2 start;
- no manual gameplay input;
- complete original-game route;
- retain exact replay and compact report.

Exit:

- every NMNB-1 acceptance condition in Section 1.1 passes.

Failure:

- retain the first clean-route hit as the next canonical root;
- later contacts are not independent survival samples;
- return to the responsible per-root/event/stage loop.

### M8 — Lunatic NMNB-R, then Extra

Required:

- two additional RNG-distinct accepted full routes;
- at least two consecutive accepted runs;
- no silent model/policy mutation between counted runs;
- full retained evidence and exact cleanup.

After NMNB-R:

- freeze the Lunatic result;
- preserve it as a regression corpus;
- open an Extra-specific event/root/resource coverage matrix;
- reuse the same architecture and authority ladder.

## 7. Physical Validation Program

### 7.1 Physical play is sparse but mandatory

Do not launch the game after every source edit. Do not postpone it until a
large speculative rewrite is complete.

Run physical play when:

- an immutable candidate has passed its targeted scalar/model/native/replay
  and delivery gates;
- the workload directly exercises the changed behavior;
- the result will decide promotion, rejection, or the next canonical root.

Operational rule:

> At most one physically eligible behavior-changing candidate may be pending
> per home workload. Once eligible, its next workload checkpoint is the named
> physical falsifier, not another unrelated behavior change on that workload.

Physical runs always require explicit user authorization. Use
`$th08-run-and-retain-physical-trial`; resolve volatile commands and menu
constants from the current `START_HERE.md`.

### 7.2 Adaptive workload sampling and generalization

Use five physical tiers:

| Tier | When | Physical scope | Authority gained |
| --- | --- | --- | --- |
| P1 home falsifier | one eligible focused correction | one stage that most directly exercises the change | workload-local evidence |
| P2 rotated sentinel | reusable mechanic passed P1 | one non-home stage with a different hazard/clock/resource signature | cross-stage evidence for that mechanic |
| P3 milestone route diagnostic | major integrated improvement passed P1/P2 | one non-practice Power-0 full Lunatic route | end-to-end discovery and clean prefix authority |
| P4 integration sweep | coherent model/policy release or strategy promotion | Stage 3, 4A, 5, and Final B, scheduled as separate focused runs | mandatory-scene compatibility |
| P5 acceptance route | P4 and route-resource gates complete | one non-practice Power-0 full route | NMNB-1/NMNB-R evidence |

Classify each behavior change before assigning physical work:

- **Content-local:** one ECL instruction, spell-specific event, or one stage
  route rule. Run P1; defer P2 unless the implementation touches shared code.
- **Reusable mechanic:** player movement, float/time recurrence, geometry,
  collision, spawn/lifecycle, solver recurrence, cadence, or delivery. Run P1
  and one P2 sentinel before reusable promotion.
- **Systemic integration:** several shared mechanics or a new live policy
  version. After P1/P2, run one P3 full-route diagnostic. Run P4 only when the
  version is ready for integrated promotion.
- **Route/resource:** Power, items, damage, death/despawn, phase timing, or
  transition history. Mechanics practice is insufficient; require P3 and
  later P5 as appropriate.

Choose the smallest sentinel that maximizes semantic difference from the home
stage:

| Changed behavior | Good sentinel choices |
| --- | --- |
| boundary/movement/recovery | Stage 3 or Final B, choosing the one not used as home and with stalest evidence |
| ECL callback/enemy body/dialogue/frozen manager | Stage 4A |
| spawn/future source/combat/Shot/Focus/Power | Stage 5 |
| laser/time scale/funnel/phase transition | Final B |
| generic solver/cadence/delivery | the non-home stage with the oldest compatible evidence and a different hazard signature |

Maintain a stage-generalization board keyed by immutable candidate version:

```text
candidate
  -> home stage/result/root
  -> sentinel stage/result/root
  -> event classes covered
  -> development roots
  -> validation roots
  -> physical holdouts
  -> physical_debt
  -> cross_stage_debt
  -> integration_sweep_status
```

Selection rules:

- Do not use Stage 5 as the sentinel by default merely because its wind tunnel
  is mature.
- Rotate sentinel stages by uncovered mechanic and oldest compatible evidence,
  not simple round-robin or convenience.
- A sentinel failure is valuable generalization evidence; route it to the
  earliest mismatch instead of adding a stage-specific heuristic.
- A home-stage success with unpaid cross-stage debt remains
  `workload_local_only`.
- P3 is blocked by the major change's unpaid home/sentinel debt, but does not
  require the complete P4 four-stage sweep.
- P4/P5 are blocked by any material unpaid physical or cross-stage debt, but
  local offline research on unrelated roots may continue.

### 7.3 Preflight for every physical trial

Verify:

- exact source checkpoint and cleanly identified concurrent changes;
- immutable model/policy/action-set version;
- focused Linux tests and required full Linux/Windows gates;
- executable hash and known instrumentation;
- foreground ownership;
- route, difficulty, team, stage, and gameplay state;
- hard no-Bomb configuration;
- daemon warm before menu selection;
- replay/result-save capacity;
- trace/report destination and disk capacity;
- supervisor ownership and terminal completion monitoring;
- key-release cleanup on every stop/error path.

Do not run Windows CLI probes during gameplay.

### 7.4 Workload-specific physical questions

| Workload | Mechanics-focused question | Route-faithful question |
| --- | --- | --- |
| Stage 3 | Are early nonspell boundary, spell-50 laser, cadence, delay, and recovery behaviors correct? | Does Stage-1 Power-0 history reach and clear Stage 3 with natural Power/items/RNG? |
| Stage 4A | Are dense bullets, callbacks, enemy bodies, dialogue, manager freeze, and held-input transitions correct? | Does natural Stage-1–4A history preserve entry resources and transition behavior? |
| Stage 5 | Does the Stage-5 causal policy survive future sources, nonspells, combat/Power, Shot/Focus, and current first-hit roots? | Does normal route history preserve kills/despawns, drops, pickups, Power, and phase entry? |
| Final B | Are scaled movement, laser geometry, funnels, long horizon, and phase transitions correct? | Can the same accumulated Route-2 history reach, clear, and complete Final B? |
| Full route | N/A; this is not a practice workload | Does one immutable candidate complete the exact NMNB objective? |

### 7.5 Interpreting physical outcomes

If a run hits:

- the candidate is physically falsified for that history;
- save the replay and compact dossier;
- use the first hit as the canonical causal witness;
- in a milestone full-route diagnostic, treat only the prefix before that hit
  as clean route-faithful survival evidence;
- do not infer rollback from aggregate hits alone;
- classify the failure and route it through Section 4.4.

If a run is clean:

- retain it as one physical witness;
- do not claim robust success;
- for local work, either run the named non-home sentinel or return to offline
  work according to the candidate's debt state;
- repeat on distinct natural RNG roots only for stage-integration or route
  readiness, not reflexively after every clean intermediate run;
- ensure the next run uses the identical immutable integrated candidate.

If a run is contaminated:

- exclude it from survival comparison;
- retain protocol evidence if it exposes a supervisor/delivery defect;
- rerun only after the contamination cause is fixed.

If aggregate hits improve but the first-hit root differs:

- treat it as discovery evidence only;
- use retained fixed-root/replay pairs for causal comparison.

### 7.6 Physical success still feeds the loop

A clean stage does not end research. It advances the frontier:

- pay a named cross-stage sentinel debt;
- repeat the same stage on a new root when stage-readiness is the active gate;
- promote to the next mandatory stage only at integration scope;
- or enter the route-prefix/full-route gate.

After a major integrated improvement, a P3 full-route diagnostic is often
more informative than immediately repeating another practice stage: it tests
Stage-1 Power-0 startup, accumulated resources, cross-stage transitions, and
the first real route bottleneck in one experiment.

A clean physical run with an unexplained model/native mismatch does not
validate the model. Retain the run, but repair the mismatch before granting
semantic authority.

## 8. External Project Integration Matrix

| Project | Immediate role | Proposed deliverable | Authority limit |
| --- | --- | --- | --- |
| `thtk` | content extraction and format oracle | immutable asset manifest, symbolic event atlas, parser corpus | no runtime order/side-effect authority |
| `thprac` | scene taxonomy/bootstrap reference | separate diagnostic scene factory and paired natural roots | modified-game evidence only |
| `th08-decomp` | address/struct/matching reference | demand-driven semantic slices and matching discipline | central updates incomplete; revalidate every claim |
| `eclmap` | ECL opcode/signature hypothesis reference | compact per-routine agreement/disagreement checks | unlicensed snapshot; do not copy; no runtime authority |
| PyTouhou | engine architecture precedent | renderer-free deterministic `state.step(action)` design | TH06 semantics are not TH08 authority |
| Hourglass | Windows TAS/savestate engineering | bounded same-root parity/throughput spike | invasive external state; no physical acceptance |
| libTAS | programmable Wine savestate experiment | Lua-driven corpus generator if parity holds | Wine experimental; no Windows/live authority |

For every external adoption:

1. pin the exact retained upstream commit;
2. record its license and whether code is copied, linked, invoked, or only
   studied;
3. state the exact hypothesis it contributes;
4. cross-check against shipped TH08 evidence;
5. retain a minimal differential;
6. stop using it as semantic input after an unexplained mismatch.

External agreement may prioritize an IDA/runtime check. It never overrides
the shipped executable.

## 9. Measurements And Retained Artifacts

### 9.1 Primary progress measures

Use, in descending authority:

1. accepted full-route NMNB count;
2. clean route-faithful mandatory-stage completions;
3. clean mechanics-focused stage completions;
4. paid versus unpaid home-stage and cross-stage generalization debt;
5. canonical physical first-hit frontier by phase/frame;
6. native-root exact policy witnesses across development and held-out roots,
   including verified emissions prevented or phase exposure shortened;
7. general solver feasible-root/action coverage and false-safe/false-losing
   counts;
8. model/native exact horizon and event-class coverage that is consumed by an
   active solver or planner question;
9. end-to-end solve/publication latency and the capability it unlocks;
10. unresolved/unknown event and action sets blocking current roots;
11. deadline/delivery health;
12. aggregate hits as a secondary workload summary only.

Do not optimize the chart instead of the physical objective.

A task that only increases test count, schema completeness, report detail, or
microbenchmark speed without moving one of the measures above must state the
specific near-term blocker it removes. Otherwise deprioritize it.

### 9.2 Root coverage record

Every canonical root record should include:

- root/session/content hashes;
- source replay/run/workload;
- route/difficulty/team/stage/phase;
- native frame and calculation seam;
- player/input/pending/resource identity;
- hostile inventory/event coverage;
- RNG state/call-count provenance;
- action set and horizon;
- recorded-action canary result;
- action portfolio status;
- model exact prefix and first mismatch;
- exact witness if one exists;
- natural/replay validation;
- development/validation/physical-holdout partition;
- home/sentinel selection and physical follow-up status.

### 9.3 Event coverage matrix

Track at least:

- constant velocity and acceleration;
- spawn/birth and immediate same-update behavior;
- redirect and reversal;
- transform/shape/scale;
- laser create/start/grow/active/fade/end;
- collision enable/disable;
- enemy body and familiar behavior;
- ECL/timeline callbacks and indexed dependencies;
- death/despawn/drop/item/Power;
- Shot/Focus/damage/RNG coupling;
- dialogue/manager freeze/phase transition;
- pool-full/allocation reuse/generation;
- time scale and float32 timer boundaries.

Each cell is one of:

- `native_model_exact`;
- `native_only`;
- `diagnostic_modified_only`;
- `counterexample`;
- `unsupported_unknown`;
- `not_reached`.

### 9.4 Candidate dossier

Every behavior candidate must pin:

- source commit and dirty-state caveat;
- formal problem version;
- model/policy/action-set version;
- root corpus and content hashes;
- exact recurrence and uncertainty support;
- horizon and float32 margin bits;
- candidate witness and verifier result;
- unresolved actions;
- timing/deadline measurements;
- shadow result;
- named home workload, sentinel workload, physical debt, and cross-stage debt;
- promotion/rejection status.

### 9.5 Physical dossier

Every complete mandatory stage or full route used for a conclusion retains:

- replay and raw-bundle identity;
- source/model/policy versions;
- frames, hits, Bombs, route completion;
- first-hit attribution;
- lives/resources/items/Power/damage;
- stage/phase/spell attribution;
- cadence, sensing age, pickup/no-write, deadline;
- viability/certificate health;
- manual/foreground/transition contamination;
- cleanup result.

Keep the two newest compatible replay-capable raw bundles for each active
workload under the repository retention policy.

## 10. Agent Task-Card Protocol

Every agent should begin with one task card:

```markdown
Task ID:
Question / hypothesis:
Why this is the next bottleneck:
Scope:
Explicitly out of scope:
Global hit/solver/planner causal chain:
Earliest decision or issued action this can change:
Predeclared win and rejection metric:
General mechanism and anti-overfit sentinel:
Cheapest decision-changing experiment:
Checks intentionally deferred and trigger for running them:
Authority inputs:
Immutable root/content/model/policy IDs:
Native prediction:
Model/solver prediction:
Smallest differentiating experiment:
Expected artifact:
Focused tests:
Native/replay gate:
Physical debt and named workload:
Stop conditions:
```

At completion, add:

```markdown
Outcome: observed / inferred / hypothesized / unknown / rejected
First mismatch or exact horizon:
Artifacts and hashes:
Tests actually run:
Authority gained:
Authority not gained:
Counterexample routing:
Next smallest task:
```

Operating rules:

- Preserve unrelated shared-worktree changes.
- Do not broaden a focused task into a complete audit.
- Optimize for the shortest causal feedback loop and move to the next
  mismatch once the current decision is established.
- Do not run a broad suite, all-action corpus, dual-platform gate, or physical
  trial unless the changed boundary or promotion rung triggers it.
- Reuse compatible retained results and state which exact change could have
  invalidated any gate that is rerun.
- Prefer one measured bottleneck optimization over speculative performance
  infrastructure.
- Use `$th08-revalidate-ida-runtime-semantics` before new native reliance.
- Use the smallest deterministic test during iteration.
- Run complete Linux/Windows gates when required by changed process/native/
  parser/formal-recurrence code or before physical promotion.
- Use `$th08-run-and-retain-physical-trial` only after explicit authorization.
- Use `$th08-retain-research-checkpoint` for a verified durable result.
- Create one focused English Git commit per verified research checkpoint.
- Update `STRATEGY.md` only for an actual status/promotion change.
- Route durable failures through `notes/COUNTEREXAMPLES.md` and chronological
  evidence through `notes/RESEARCH_LOG.md`.
- Never mutate an immutable candidate or report to make a later result fit.

## 11. Decision And Stop Rules

| Observation | Required decision |
| --- | --- |
| First mismatch at frame 1 | fix root/schema/player/input ordering before longer horizons |
| H1 exact, H8 mismatch | isolate first event transition; do not tune planner |
| Model exact, solver differs from scalar | fix recurrence/implementation; no native experiment needed yet |
| Solver witness loses in native root | first native/model mismatch becomes the task; withdraw witness authority |
| Native root wins, natural frame pump differs | snapshot/external-state/seam problem; poison root/session |
| Offline/replay wins, physical action differs | delivery/clock/pickup/deadline problem; do not add geometry heuristics |
| Physical action matches but hit remains | missing horizon/event/resource or policy deficiency; capture new first-hit root |
| Different RNG run has more aggregate hits | no rollback without causal retained-root evidence |
| Search times out | retain completed lower bounds and unresolved actions; never label unrestricted losing |
| Microbenchmark/test count improves but no consumed solver, deadline, or hit-facing metric moves | stop calling it an optimization; identify a concrete blocker it removes or deprioritize |
| One tuned stage/spell improves but an unseen mechanism sentinel does not | keep the result workload-local/proposal-only; do not add it to universal policy |
| External reconstruction and inherited IDA interpretation disagree on a critical routine | resolve the smallest distinguishing instruction/dataflow and runtime probe before changing the model |
| THPRAC scene and natural root differ | keep scene diagnostic-only and investigate bootstrap distortion |
| Hourglass/libTAS differs from Windows native | stop semantic adoption; retain engineering lessons only |
| Optimization changes labels/order | correctness regression unless exact recurrence intentionally versioned |
| Candidate passes offline but remains physically untested | mark `physical_debt_pending`; do not promote |
| Home stage passes but reusable mechanic lacks a non-home sentinel | mark `cross_stage_debt`; authority remains workload-local |
| Home stage passes and sentinel fails | treat as a generalization counterexample; fix the shared earliest mismatch, not a stage heuristic |
| Major integrated improvement passes home and sentinel | run one non-practice Power-0 milestone full route before further broad live changes |
| Milestone full route hits | keep the pre-hit prefix as route-faithful evidence and promote its first hit to the canonical queue |
| Physical run is clean but report/cleanup/replay is incomplete | useful observation, not accepted gate |

## 12. Prioritized Initial Backlog

Future agents must reconcile this list with the current `START_HERE.md`.
Do not duplicate an in-progress or newly retained task.

### Priority 0 — Complete the current semantic bridge

#### CORE-01 — Model-consumable hostile H1 capsule

Dependency: M0.  
Output: full root2129 hostile inventory, generation identity, collision state,
and ordered H1 event ledger.  
Gate: recorded/native/model H1 exact or minimal first mismatch.

#### CORE-02 — Extend the same capsule to H8/H32

Dependency: CORE-01.  
Output: causal event stream, no future backfill, explicit unsupported events.  
Gate: H8 exact; H32 exact only while coverage remains complete.

#### CORE-03 — Integrated collision/planner first mismatch

Dependency: CORE-02.  
Output: exact same-root solver replay and the first divergent frame/object/
action/value.  
Gate: one retained minimal falsifier and assigned failure class.

### Priority 0.5 — Early combat and Power hypothesis sprint

Do not leave S18 as an indefinitely trace-only idea. Begin these bounded
experiments as soon as their minimum native semantics are available; do not
wait for a complete reconstructed engine or every stage corpus. Their first
goal is a fast causal accept/reject decision, not immediate live promotion.

The sprint order is:

1. verify unfocused shot/movement effects and dynamic Focus opportunity;
2. test kill-before-saturation on killable ordinary emitters;
3. test survival-filtered early Power acquisition from a natural Power-0
   route.

The first two may share the same native roots and combat instrumentation, but
must retain separate causal measurements. None may weaken hard survival.

#### COMBAT-FAST-01 — Dynamic unfocused opportunity

Hypothesis: when precise micro-dodge is unnecessary, releasing Shift gives
Sakuya wider useful attack coverage and faster movement; a causal
unfocused/refocused policy can kill distributed enemies earlier without
reducing robust survival.  
Minimum semantics: verify native team/character/Focus/Shot state, movement
speed and pickup timing, shot origin/coverage/targeting, damage, enemy HP, and
kill/end reason. Compare critical routines with pinned external TH08
references, resolving differences against native evidence.  
Cheapest experiment: from identical native roots with several ordinary
enemies, branch focused, unfocused, and dynamic-refocus complete-mask
schedules; regenerate each causal future and measure shot coverage, HP delta,
kill time, later hostile births, exact clearance/reserve, and first hit.  
Win: at least one dynamic policy remains exactly survival-feasible and
prevents emissions, increases verified kills/damage, or reaches a better
terminal tube on development roots without regression on unseen roots.  
Reject/defer: no causal combat benefit, any survival/cadence/delivery
regression, or benefit confined to one tuned stage/spell identity.  
Next gate: encode only as survival-filtered proposal ranking, then shadow,
home-stage physical falsifier, and a rotated non-home sentinel before live
promotion. Never implement unconditional “release Shift.”

#### COMBAT-KILL-01 — Kill-before-saturation emitter policy

Hypothesis: some killable nonspell emitters have a deadline before a later
dense/homing volley; killing them before that deadline reduces hostile
exposure and physical hits more than pure evasion.  
Minimum semantics: generation-aware HP/damageability, Shot damage, target
identity, kill versus timeout/scripted despawn, bullet ownership/persistence,
future-volley program state, drops, and branch-specific RNG.  
Cheapest experiment: select roots before a verified emitter deadline; compare
an exact pure-survival policy with survival-feasible damage-maximizing
policies from the same root. Measure kill time, prevented births, bullet-time
integral, viable-action reserve, exact survival horizon, and first hit.  
Win: earlier verified kill causally removes one or more later emissions or
shortens dangerous exposure and improves exact feasible continuation across
more than one root/event family.  
Reject/defer: kill timing does not affect later emissions, bullets persist so
no useful exposure is removed, the damage policy leaves the viable set, or
the result is only a different-RNG aggregate.  
Output: an enemy/event-class kill-deadline model, not a blanket
`if nonspell: attack` weight. Spell/boss damage remains survival-first unless
its own phase-shortening experiment passes.

#### POWER-ROUTE-01 — Survival-filtered Power-0 acquisition

Hypothesis: collecting Power during easy early-route opportunities increases
later damage and kill-before-saturation capability enough to improve route
survival, without taking unsafe collection paths.  
Minimum semantics: item identity/value/motion/expiry, pickup geometry and
auto-collection behavior, current Power, Power thresholds, action-conditioned
shot changes, enemy damage, route phase entry, and RNG coupling.  
Cheapest experiment: use natural Stage-1/2 Power-0 route-prefix roots and
compare survival-feasible actions with and without collection preference.
Carry the resulting Power and causal world state into later combat roots;
measure collection risk, Power threshold timing, damage/kill changes, viable
reserve, and later first-hit frontier.  
Win: a collection policy stays inside exact viability and creates a measured
later combat or survival benefit on held-out route prefixes.  
Reject/defer: Power is acquired only through reduced survival reserve, later
capability does not improve, or the benefit depends on practice-mode max
Power.  
Boundary: no post-death recovery objective exists in the NMNB policy. Post-hit
Power traces are diagnostic-only.

### Priority 1 — Turn one root into a representative corpus

#### CONTENT-01 — TH08 immutable content manifest

Dependency: none.  
Output: `thtk`-assisted asset hashes and independent parser comparisons.  
Gate: Stage 3/4A/5/Final-B content versions pinned.

#### CONTENT-02 — Mandatory-stage event atlas

Dependency: CONTENT-01.  
Output: reachable event classes and symbolic runtime mapping.  
Gate: unknown events explicitly listed and prioritized by physical
reachability.

#### ROOTS-01 — Stage-5 multi-root first-hit corpus

Dependency: CORE-01.  
Output: several RNG-distinct canonical Stage-5 roots, not repeated aggregate
runs without root retention.  
Gate: exact canary/restore and representative action branches per root.

#### ROOTS-02 — Stage 3, 4A, Final-B seed roots

Dependency: CONTENT-02 and stable capsule schema.  
Output: at least one natural root per mandatory workload and critical event
class.  
Gate: event/root matrix has no fabricated coverage.

#### GENERALIZE-01 — Development/validation/holdout root split

Dependency: ROOTS-01 and ROOTS-02.  
Output: immutable partition by stage, event class, and RNG root, with no
candidate tuned against its validation or physical-holdout labels.  
Gate: every reusable candidate reports development and unseen validation
results separately.

#### GENERALIZE-02 — Stage sentinel selection board

Dependency: GENERALIZE-01.  
Output: candidate-version matrix for home stage, rotated sentinel,
physical/cross-stage debt, stale evidence, and integration status.  
Gate: no reusable promotion is supported only by Stage 5 or one repeated
physical seed.

### Priority 2 — Close policy and delivery

#### SOLVER-01 — Reachable scheduler/actuator automaton

Dependency: CORE-03 and retained pickup/cadence/no-write traces.  
Question: which combinations in the current uncertainty product are actually
reachable at a decision observation?  
Output: independently checked finite automaton with observation labels,
active/held/pending transitions, cadence, pickup, and no-write semantics.  
Gate: every removed branch is proved unreachable by revalidated native
semantics and bounded runtime probes; scalar recurrence and adversarial tests
pass.  
Stop: if support cannot be justified, preserve the wider belief and return
`UNKNOWN`; do not reduce uncertainty for performance alone.  
Physical debt: none for an offline automaton hypothesis; focused delivery
shadow and the appropriate home/sentinel stages are mandatory before live
promotion.

#### SOLVER-02 — Query-local robust recovery band

Dependency: CORE-03 and exact vector transitions for the selected roots.  
Question: can an apparently non-viable coarse root robustly reach the next
verified viability kernel?  
Output: independent scalar recurrence plus optimized time-expanded AND-OR
recovery implementation, sparse/adaptive reachable tube, exact witness or
`UNKNOWN`, and a false-loss corpus for the old distance heuristic.  
Gate: exact parity with the scalar oracle; no false-safe result on
adversarial stop/resume/reversal/laser/boundary cases; measurable resolution
of retained coarse false-loss roots inside the deadline budget.  
Native gate: replay the complete recovery policy over development and unseen
validation roots, not only one endpoint trajectory.  
Physical debt: one boundary/recovery home workload and one non-home sentinel
before replacing live recovery guidance.

#### SOLVER-03 — Sparse dual-bound belief-tube CEGIS

Dependency: SOLVER-01 where timing support changes, SOLVER-02 where recovery
is needed, and a representative multi-root corpus.  
Question: can feasibility be found before issue time without solving the
entire unrestricted belief game?  
Output: observation-keyed policy patches, executable-candidate lower bounds,
admissible upper bounds, first-gap refinement, cooperative cancellation, and
exact immutable witness publication.  
Gate: full public-root action accounting; no unresolved action labeled
losing; exact verifier agreement; better predeclared feasibility latency or
more exact winning roots than the predecessor on held-out roots.  
Stop: if admissibility, observation merging, or exact re-verification cannot
be preserved, keep the method proposal-only.  
Physical debt: generic solver changes require a home workload, a rotated
sentinel, and a milestone full-route diagnostic after successful integration.

#### SOLVER-04 — Complete-mask action factorization

Dependency: WS-H Shot/Focus/damage/RNG evidence and SOLVER-03 candidate
identity.  
Question: is a slower phase-level Shot/Focus option plus tactical movement
control-equivalent to expanding all 36 masks at every future decision?  
Output: explicit restricted policy contract, causal factorization test,
complete-mask issue verifier, and counterexamples where factorization loses
feasibility.  
Gate: exact comparison against all-36 short-horizon roots and no unexplained
resource/phase divergence; restricted loss remains restricted loss.  
Physical debt: Stage 5 home evidence plus a sentinel chosen for different
damage/phase behavior, followed by a route-faithful diagnostic if promoted.

#### POLICY-01 — Multi-decision observation-compatible policy

Dependency: CORE-03 and ROOTS-01; may use SOLVER-02/03 incrementally without
waiting for every proposed optimization.  
Output: exact causal policies across multiple roots.  
Gate: scalar verification, no clairvoyance, exact native witness.

#### POLICY-02 — Corpus robustness and proposal ranking

Dependency: POLICY-01.  
Output: action ordering/heuristic trained or tuned only as proposal logic.  
Gate: exact verifier remains decisive, development/validation/physical
holdout partitions remain disjoint, and no retained exact root regresses.

#### ROUTE-OPT-01 — Phase option and terminal-tube graph

Dependency: WS-H combat/resource ledger and exact tactical terminal kernels.  
Question: which phase entry tube, Shot/Focus schedule, and resource interval
preserve a feasible continuation without solving the entire route as one
giant belief game?  
Output: versioned phase/stage option graph whose edges declare entry/exit
position tubes, resource bounds, event support, damage/time conditions, and
fallback.  
Gate: every option edge is backed by exact short-prefix policies plus
route-prefix native/model evidence; soft progress never leaves the tactical
viable set.  
Physical debt: route-resource changes require a non-practice Power-0
milestone full-route diagnostic after home and sentinel gates.

#### DELIVERY-01 — Exact-version shadow publication

Dependency: POLICY-01.  
Output: deadline, lookup, fallback, and fresh-certificate dossier.  
Gate: side-effect-free shadow and no cadence/contention regression.

#### DELIVERY-02 — Frozen-manager and no-write physical boundary

Dependency: DELIVERY-01.  
Output: target Stage-4A/transition trace proving active input and safe
neutralization behavior.  
Gate: focused original-game physical evidence before promotion.

### Priority 3 — Physical stage campaign

#### PHYS-05 — Stage-5 causal candidate falsifier

Dependency: CORE-03, POLICY-01, DELIVERY-01.  
Output: one named original-game Lunatic Stage-5 run.  
Pass: zero hit/zero Bomb complete stage for one root.  
Fail: canonical first hit becomes ROOTS-01 input.

#### PHYS-03 — Stage-3 candidate falsifier

Dependency: Stage-3 root/model coverage and delivery gate.  
Output: complete practice, then route-faithful prefix evidence.  
Fail: first laser/nonspell/resource root enters CORE/ROOTS.

#### PHYS-04A — Stage-4A candidate falsifier

Dependency: callback/body/frozen-manager coverage.  
Output: complete practice and route-prefix evidence.  
Fail: classify EVT versus DEL before any planner tuning.

#### PHYS-FB — Final-B candidate falsifier

Dependency: scale/laser/phase coverage and route-resource readiness.  
Output: complete Final-B practice and compatible full-route reach.  
Fail: root enters scale/laser/event or route-resource loop.

### Priority 4 — Route acceptance

#### ROUTE-DIAG — Major-improvement full-route diagnostic

Dependency: one immutable major integrated candidate, paid home-stage debt,
and one paid cross-stage sentinel debt.  
Output: one normal non-practice Stage-1 Power-0 Route-2 run, complete replay,
resource/transition ledger, and canonical first clean-route hit if any.  
Pass: end-to-end discovery complete; zero hit with all acceptance fields also
becomes NMNB-1.  
Fail: route the first hit into CORE/ROOTS without interpreting RNG-distinct
aggregate totals as causal regression.

#### ROUTE-01 — Integrated Power-0 full-route candidate

Dependency: compatible mandatory-scene evidence and frozen integrated version.  
Output: normal non-practice Route-2 run with full retained dossier.  
Pass: NMNB-1.  
Fail: first clean-route hit becomes the highest-priority canonical root.

#### ROUTE-02 — NMNB-R campaign

Dependency: NMNB-1.  
Output: two further RNG-distinct accepted runs, including two consecutive
successes.  
Gate: identical immutable candidate and complete evidence.

### Optional parallel research

#### EXT-01 — THPRAC-derived diagnostic scene spike

Run only as a separate modified-game lane. Pair useful roots with natural
original-game evidence.

#### EXT-02 — Hourglass versus libTAS bake-off

Run only after compact hostile/native/model fingerprints are stable. Stop on
the first unexplained mismatch or insufficient measured throughput benefit.

#### PERF-01 — Dirty-page/write-watch acceleration

Run only if endpoint scanning is the measured dominant bottleneck after the
semantic pipeline works across multiple roots. Preserve exact restore and
poison checks.

## 13. Focused Authority Reading Map

Use this map to avoid loading the entire research history for every task.

| Task layer | Required current sources |
| --- | --- |
| Any task | `AGENTS.md`, `START_HERE.md`, relevant `STRATEGY.md` status |
| Native root/wind tunnel | `notes/architecture/NATIVE_REPLAY_CAUSAL_WIND_TUNNEL_AND_REPLAY_SAVE_CONTRACT_20260730.md` |
| Action/cadence/delay recurrence | `notes/AUGMENTED_PIPELINE_ROBUST_CONTROL_FORMALIZATION_20260725.md`, then the exact bounded-belief note named by the handoff |
| Input clock/dialogue transition | `notes/FROZEN_MANAGER_INPUT_CLOCK_BOUNDARY_20260726.md` and CE-0120/0121 |
| Candidate publication | `notes/CANDIDATE_WITNESS_PUBLICATION_CONTRACT_20260726.md` |
| Candidate contention/deadline | `notes/FEASIBILITY_FIRST_STAGE6B_PHYSICAL_CONTENTION_20260726.md` |
| Offline/external-project design | `notes/review/TH08_OFFLINE_ITERATION_RESEARCH_20260730.md`, `notes/review/EXTERNAL_REFERENCE_SNAPSHOT_INDEX_20260730.md` |
| Mandatory scenes/full-route acceptance | `notes/review/LUNATIC_NMNB_PROGRAM_REVIEW_AND_ROADMAP_20260729.md` plus current run dossiers |
| New native semantic reliance | the smallest relevant IDA/runtime note plus `$th08-revalidate-ida-runtime-semantics` |
| Physical execution | current `START_HERE.md`, relevant recent run note, `$th08-run-and-retain-physical-trial` |
| Durable checkpoint | `notes/RESEARCH_LOG.md`, `notes/COUNTEREXAMPLES.md`, `$th08-retain-research-checkpoint` |

Read additional notes only when a concrete dependency or counterexample
requires them. A taskbook workstream is not authorization for a comprehensive
audit.

## 14. Research Closure Criteria

The Lunatic program is closed only when:

1. the same immutable integrated candidate has complete evidence through the
   formal, model, native, delivery, focused physical, and route layers;
2. Stage 3, Stage 4A, Stage 5, and Final B have compatible original-game
   evidence;
3. a normal non-practice Power-0 route satisfies NMNB-1;
4. RNG-distinct repeats satisfy NMNB-R;
5. no Bomb, manual intervention, foreground contamination, replay/report gap,
   or cleanup defect invalidates the runs;
6. retained artifacts allow another agent to reproduce every authority claim;
7. `STRATEGY.md`, `START_HERE.md`, counterexamples, research log, code, tests,
   and retained reports agree at one focused checkpoint.

Until then, progress should be reported as the strongest completed rung:

- model exactness;
- native fixed-root witness;
- replay/natural witness;
- shadow delivery readiness;
- focused physical witness;
- route-faithful stage witness;
- NMNB-1;
- NMNB-R.

Never collapse these into the single phrase “the solver works.”
