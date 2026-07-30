# TH08 Offline Iteration / Native-To-Solver Read-Only Audit

Date: 2026-07-30
Workspace: `/home/pentester/coding/codex_ida/th08`
Reviewed baseline: `main` / `eec2560c2a7b26322287299b77f437db0bfb223c`
Dirty-state caveat: the worktree was clean at audit start. During the review,
other agents began changing strategy/research/roadmap notes, the
future-body/simulator and live CLI/controller surfaces, their tests, and new
enemy-spawn lifecycle differential artifacts. Those concurrent, uncommitted
changes were not modified, tested, or treated as a stable review baseline
here.

Connected IDB identity:

- path:
  `D:\Entertainment\Game\Touhou\[th08] 东方永夜抄 (日文版)\th08.exe`
- image base: `0x00400000`
- file size: `840704`
- IDB input SHA-256:
  `ec101fcff80b77e717d43b54e326375487af19661bb7c8d11a19ee5e0fbf928b`
- IDB input MD5: `454c96e08fe3c14df7064d104c26accf`
- clean physical target SHA-256:
  `330fbdbf58a710829d65277b4f312cfbb38d5448b3df523e79350b879213d924`
- the repository's retained proof reproduces the IDB hash exactly by applying
  only the known no-life-decrement byte change at VA `0x0044D0FA`
  (`FF -> 00`) to the clean target. Native claims below therefore exclude
  shipped miss/life-decrement behavior unless explicitly stated.

Evidence cutoff: current `START_HERE.md`, `STRATEGY.md`, the 2026-07-30 daily
research shard, the current native audit, the formal/model contracts selected
by the handoff, and retained counterexamples through CE-0198.

Scope: determine whether deterministic offline play, replay, an instrumented
native engine, or a reverse-engineered TH08 simulator can materially shorten
solver iteration; identify what physical trials remain irreducible; compare
the current repository pipeline with primary-source external projects; and
propose staged gates without changing live authority.

Non-actions: no repository source, note, IDA database, strategy ledger,
runtime, input, or gameplay mutation. No physical trial. No test suite was run.

## Executive Answer

**Yes: most solver/model iteration can and should move offline. No: final
physical execution cannot be removed.**

The current loop is slow partly because one full physical run combines several
different questions:

1. Is a recurrence or geometry implementation internally correct?
2. Does it match the shipped engine for a fixed history?
3. Does a different policy improve a fixed initial physical state?
4. Does the real Windows sensing/publication/input path meet its deadline?
5. Does the complete Power-0 route survive across physical RNG histories?

Only questions 4 and 5 inherently require the real-time physical path.
Question 2 can already use the original game as a deterministic native replay
oracle. Question 1 is already largely served by scalar oracles, capsules,
semantic fuzzers, and Linux/Windows parity. Question 3 needs one missing
capability: a branchable, action-conditioned future-world producer from a
complete native root.

The recommended target is therefore **not a complete visual TH08 clone**. It is
a headless, short-horizon, fail-closed **causal prefix simulator** that:

- starts from a content-addressed full native state root;
- follows exact native update/event order;
- branches complete controller masks and their actual write/no-write effects;
- advances shared RNG according to the events each action really causes;
- returns `UNKNOWN` before an unsupported event mutates state; and
- is differentially checked against the original executable at every supported
  boundary.

This changes physical play from the inner iteration loop into a sparse oracle
and promotion gate.

## Evidence Labels

- **Observed:** directly visible in shipped instructions/dataflow, current
  source, deterministic execution, retained native runtime evidence, or a
  cited primary external source.
- **Inferred:** supported by multiple observed facts but not directly proved
  at runtime.
- **Hypothesized:** plausible and testable, but missing a decisive fact.

## Capability Matrix

| Capability | Current state | What it answers | Main boundary |
| --- | --- | --- | --- |
| Scalar/formal oracle and semantic fuzzer | Available | Is the declared finite recurrence/kernel implemented correctly? | Does not prove the finite model is physically complete. |
| Retained trace/capsule analysis | Available | What does the current model say at captured roots, including all 36 no-Bomb root actions on declared slices? | Recorded future is not a counterfactual after an alternative action. |
| Original-game native replay | Available | Does a decoder/model agree with shipped TH08 for one fixed input/RNG history? | Inputs are fixed; it cannot compare policies that choose different actions. |
| Incremental `th08_simulator.py` | Available but deliberately partial | Can known player/timeline/item/bullet/laser components be composed deterministically in recovered frame order? | Enemy VM state and future births are externally supplied; transforms and complete lifecycle/order are not covered. |
| Branchable causal short-horizon simulator | Not complete | What happens from the same root under alternative actions? | Requires complete reachable event coverage or explicit fail-closed `UNKNOWN`. |
| Accelerated/headless original engine | Not established | Can fixed native histories be produced faster while retaining mechanics? | Any timing/render bypass must be proved not to change game-state order; it cannot validate real-time delivery. |
| Real-time focused/full-route physical gate | Available and required | Does the shipped process, sensor, scheduler, publisher, actuator, and route actually work together? | Slow and RNG-sensitive; should not be used for ordinary semantic iteration. |

## Positive Validations

### V-001 — The repository already has a strong offline foundation

Status: **Observed.**

`scripts/th08_simulator.py` composes replay publication, route-2 player state,
stage timelines, shared gameplay RNG state/call count, items, transform-free
hostile bullets, lasers, contact, and a subset of Bomb/deathbomb behavior in
reconstructed native frame order. Retained capsule and counterfactual tools
already evaluate complete no-Bomb mask portfolios, actuator beliefs,
cadence/delay branches, and scalar/native parity for declared finite slices.

This is not a project starting from screenshots. The useful next step is to
extend and certify the existing state-transition seam, not replace it with a
generic game-AI stack.

### V-002 — Native replay already removes an important class of noise

Status: **Observed.**

The retained native replay protocol lets the shipped executable run its own
ECL, scheduler, timers, managers, pools, and collision logic against a fixed
replay stream. It is the immediate deterministic oracle for:

- decoder and lowering changes;
- geometry/state projections;
- exact update-order questions;
- regression localization on one fixed route; and
- simulator/native per-frame differentials.

It does not prove that a new controller would have generated that input stream,
but it can prevent a model change from consuming a fresh RNG-varying physical
run merely to rediscover a semantic mismatch.

### V-003 — The current authority documents already support an offline-first loop

Status: **Observed.**

The active formalization explicitly says not to spend another physical trial
until offline correctness and delivery gates identify a configuration with a
plausible no-contention budget. The roadmap also rejects another unchanged
observer trial and distinguishes a narrow mechanics-focused physical falsifier
from route-faithful Power-0 authority.

The proposed process change is therefore a rebalancing inside the existing
authority contract, not a relaxation of physical acceptance.

## Findings

### F-001 — A replayable trace is not a branchable save state

Severity: high for iteration speed; not a new live-safety defect.
Status: **Observed source/contracts; inferred architecture consequence.**
Reachability: every experiment asking “what would have happened under a
different earlier action?”
Authority boundary: offline research only.

The current simulator initializer explicitly avoids inventing enemy VM state.
Bullet, laser, and item births are supplied through frame controls. A retained
trace can therefore reproduce or analyze its realized future, but it cannot
causally reuse that future after the controller selects another action.

A complete branch root must cover, at minimum:

- physical/gameplay epoch, route, difficulty, stage, phase, and relevant
  physical clocks;
- immutable ECL/runtime-image identity;
- every live enemy slot's allocation state and generation;
- main and auxiliary VM contexts, stacks, callbacks, timers, and registry
  gates;
- timeline program counters, allocation/retirement events, and ordered
  same-update lifecycle;
- shared gameplay RNG state and call count;
- player position/motion/mode, active input, held desired input, pending
  command belief, shot cadence, Power, damage, lives/Bombs, and phase state;
- bullet, laser, item, transform, collision-suppression, and body eligibility
  state; and
- end/despawn/death/transition state needed by the requested horizon.

Without that root, “offline play” is a useful trace analyzer, not yet a
generative TH08 world.

### F-002 — RNG variance has an exogenous part and an action-caused part

Severity: critical to experimental design.
Status: **Observed native mechanism; inferred protocol.**

The initial RNG root can be held fixed. That removes exogenous sample
variation and enables paired A/B experiments. However, future RNG cannot be
held to a prerecorded stream across different policies without changing the
physical question.

The retained native audit shows that route-2 Focus/Shot behavior can change
shared gameplay RNG consumption: a player-shot callback can consume RNG before
later enemy/ECL/bullet work. Direction also changes aimed motion; Focus changes
body gates; Shot/Power changes damage, death, despawn, and later sources.
CE-0197 therefore correctly rejects replaying a recorded hazard schedule after
an alternative action.

The correct paired experiment is:

1. start A and B from the same complete root and initial RNG state;
2. let each action branch consume RNG according to exact native semantics;
3. compare outcomes pairwise at the same root;
4. retain RNG state/call-count and ordered cause events; and
5. repeat over a fixed corpus of roots rather than interpreting one seed.

Forcing identical future RNG values after the policies diverge is useful only
as a synthetic ablation, never as a faithful physical counterfactual.

### F-003 — The highest-value simulator is a short exact prefix, not a full game

Severity: architectural.
Status: **Inferred from the solver horizon and missing semantics.**
Reachability: every proposed action-conditioned planning or policy comparison.
Authority boundary: exact only over the event classes and horizon reported
complete by the executor.

Rendering, audio, menus, animation fidelity, dialogue presentation, score
display, and a portable replacement executable do not answer the current
planner question. They create a large second implementation whose agreement
with the solver could still be “two wrong models agree.”

The useful unit is a bounded exact prefix—initially one frame, then short
multi-frame horizons, eventually the current planning horizon—re-rooted from
many native captures. This gives:

- deterministic and parallel counterfactual batches;
- direct all-36-mask comparison;
- small mismatch windows that can be shrunk;
- no long-route accumulated simulator drift; and
- explicit coverage rather than an unsupported impression of completeness.

Only after short-prefix coverage is strong should the same transition core be
used for longer closed-loop offline play.

### F-004 — An accelerated original engine is a valuable middle layer, but not a shortcut around proof

Severity: medium/high opportunity.
Status: **Hypothesized until a native timing experiment is performed.**
Reachability: optional ground-truth generation and mechanics regression only.
Authority boundary: cannot inherit real-time sensing, publication, actuation,
or acceptance authority.

An instrumented `th08.exe` that skips rendering/audio, uses a fixed initial
root, and advances one calculation frame on command could retain more shipped
semantics than a new engine and could produce deterministic oracle traces much
faster. It should be investigated as a **mechanics oracle**, separately from
the branchable simulator.

The risks are material:

- game-state evolution may depend on supervisor timing, callbacks, or frame
  control that an uncapped loop changes;
- process memory contains pointers, threads, DirectX objects, handles, and
  external state that make arbitrary snapshot/restore unsafe;
- a Windows/Wine process or VM snapshot reproduces one continuation more
  readily than it provides clean arbitrary counterfactual branches; and
- accelerated execution says nothing about real-time sensor freshness,
  worker contention, publication age, input pickup delay, foreground
  ownership, or cleanup.

The first admissible experiment is not general process cloning. It is a
fixed-replay A/B where normal-speed and render-skipped native runs must produce
identical per-frame gameplay fingerprints. Until that passes across relevant
event classes, accelerated native output is diagnostic only.

### F-005 — External projects are useful inputs, but no inspected project is a drop-in TH08 simulator

Severity: planning.
Status: **Observed primary sources and inspected source trees; search result is
not an exhaustive proof of absence.**
Reachability: any decision to adopt an external decoder, engine, practice
harness, or native implementation.
Authority boundary: every external semantic claim remains a hypothesis until
revalidated against the shipped TH08 build.

Inspected source snapshots:

- local `thpatch/thtk`:
  `892114a0fcaa0bbdaaecf3cb4ad56f758683fb40`;
- local `Priw8/eclmap`:
  `f146162e330c27d1b0a8880c3a41884615147a11`;
- `GensokyoClub/th08` main:
  `84738749bdcf6cffabe8d0d76e17f19253a20d50`;
- `GovanifY/PyTouhou` mirror:
  `fbfba5269cfc98def3ff0e899694d2686c8f9eac`; and
- `touhouworldcup/thprac` master:
  `8b3338f4d2cc7853d5a32d30dc7d252dc50bf2b3`.

#### thtk

The official [thtk repository](https://github.com/thpatch/thtk) supports TH08
archive extraction/creation and ECL/MSG/STD decompilation/compilation. Its
source tree and documentation expose file formats and syntax, not a running
enemy/timeline/bullet/player engine.

Best use here:

- extract immutable content;
- build canonical ECL/STD IR and coverage inventories;
- generate parser round-trip and opcode corpus tests; and
- identify unknown opcodes/callback references for native revalidation.

It must not be treated as authority for runtime order, callback side effects,
allocation/reuse, RNG coupling, geometry, or collision.

#### GensokyoClub/th08

The [TH08 matching-decomp project](https://github.com/GensokyoClub/th08)
targets the same clean 1.00d SHA-256 as this workspace and uses `reccmp` to
compare rebuilt code with the original binary. That validation discipline is
directly relevant.

It is not currently an engine dependency: the project's README calls it early
WIP, its implemented manifest is small relative to its function inventory,
and the inspected
[`EnemyManager.cpp`](https://github.com/GensokyoClub/th08/blob/main/src/EnemyManager.cpp),
[`BulletManager.cpp`](https://github.com/GensokyoClub/th08/blob/main/src/BulletManager.cpp),
and [`Player.cpp`](https://github.com/GensokyoClub/th08/blob/main/src/Player.cpp)
still stub the central update routines.

Best use here:

- monitor and cross-reference recovered structs/functions;
- borrow matching/diff methodology;
- upstream or consume only evidence-backed, license-compatible work; and
- revalidate every imported semantic claim against this connected IDB and
  runtime evidence.

#### PyTouhou

[PyTouhou](https://github.com/GovanifY/PyTouhou) demonstrates that a Touhou
game-state runner can be separated from its window/renderer and that frames can
be advanced without a display. Its primary Mercurial history includes
render-skipping, replay support, and a `GameRunner` made independent of the
window. It targets the first-generation Windows engine, principally TH06, and
its history also documents years of synchronization and semantic fixes.

Best lesson: separate deterministic game state, input/replay, and rendering;
make the runner directly step-able; keep replay compatibility as a continuous
oracle. It does not provide TH08 mechanics to reuse as authority.

#### thprac

[thprac](https://github.com/touhouworldcup/thprac) is valuable as an
original-game practice/injection harness. It can select narrow practice
workloads and retain custom options in replays. Its own documentation says
custom-mode replays are not compatible with the unmodified game and that
mid-game replay saving for TH06–10 is generally unsupported due to technical
difficulty, with a special TH06 exception.

Best use here: scene bootstrapping and diagnostic patch ideas, not a branchable
save-state engine or acceptance authority.

#### Screenshot/RL agents

Inspected public Touhou AI examples use screenshots/YOLO or visual
reinforcement learning plus synthetic keyboard input. For example,
[wcycn/touhou_ai](https://github.com/wcycn/touhou_ai) explicitly reports
resolution/inference sensitivity, incomplete laser/state-machine coverage, and
failure to complete Stage 1 reliably.

These projects validate safe observation/session-review ideas, but their
screen/input loop preserves the physical bottleneck and discards the stronger
native state already available here. They are not the right foundation for
this solver.

### F-006 — Physical evidence remains irreducible, but much less frequently

Severity: acceptance boundary.
Status: **Observed workspace contract.**
Reachability: every live promotion and final Lunatic/Extra acceptance claim.
Authority boundary: offline evidence can select what to falsify physically;
it cannot award physical acceptance.

Offline or accelerated mechanics cannot validate:

- real-time process reads and coherent capture;
- Windows scheduling, contention, and computation/publication deadlines;
- ordered complete-mask dispatch, no-write behavior, and physical pickup
  delay;
- foreground ownership, focus loss, menu/dialogue transitions, and key
  release/cleanup;
- full-route Power/items/damage/resource accumulation from Stage 1; or
- survival across physical initial roots and histories.

The final target remains original-game Sakuya/Remilia Lunatic and Extra
execution. Physical play should therefore remain:

1. a smallest focused falsifier for one immutable integrated behavior change;
2. a real-time delivery/contention gate;
3. fresh Stage 3, Stage 4A, Stage 5, and Final B evidence for an integrated
   model version; and
4. repeated full-route acceptance.

It should not remain the default way to discover parser, recurrence, geometry,
or event-order defects.

## Recommended Architecture

### 1. Content-addressed native root capsule

Define one canonical root schema and hash every dependency:

- clean executable and known patch identity;
- ECL/STD/content images;
- route/team/difficulty/stage/phase;
- physical clock and update position;
- all controller/input-pipeline state;
- player/combat/resource state;
- full live VM/timeline/manager/pool state;
- allocation generations and ordered lifecycle ledger; and
- RNG state/call count.

Reject partial roots for counterfactual authority. A partial root may still be
used by a component test under an explicitly smaller contract.

### 2. Exact-prefix executor with three coverage results

Every transition returns one of:

- `COMPLETE_EXACT`: every reachable event in the requested horizon was
  modeled exactly for the declared root/version;
- `COMPLETE_CONSERVATIVE`: only if the omitted effect has a proved
  conservative envelope for the exact queried property; or
- `UNKNOWN(event_class, frame, identity)`: stop before unsupported mutation.

Unknown-direction approximations never produce hard safe/losing labels.

The executor should be event-ledger driven rather than a precomputed future
schedule. Same-update allocation, initial VM execution, callback, retirement,
and slot reuse must preserve total order and generational identity.

### 3. Original-game differential oracle

For every newly supported event class:

1. construct or select the smallest native replay scene that exercises it;
2. capture the exact initial root;
3. run the original engine and prefix executor from that root with the same
   action;
4. compare per-frame fingerprints, not only final geometry;
5. shrink the first mismatch into a deterministic fixture; and
6. add the failure to the counterexample route before expanding coverage.

Fingerprints should include RNG state/calls, VM/timeline positions, lifecycle
events, manager counts/generations, player/body modes, projectile states,
resources, collisions, and end/despawn events.

### 4. Fixed-root counterfactual corpus

Build a stable corpus from retained native bundles:

- canonical first-hit prefixes;
- viable-to-losing transitions;
- Stage 3, Stage 4A, Stage 5, and Final B;
- unit and non-unit time scale;
- Focus/Shot/Power transition edges;
- dense bullet, laser, transform, stop/resume/redirect/reversal cases;
- allocation/retirement/reuse boundaries; and
- dialogue/frozen-manager-clock boundaries where relevant.

Run every candidate policy version pairwise from the same roots. Report
per-root first contact, exact coverage, viable-action masks, clearance,
resources, and deadlines. Aggregate only after preserving the paired result
and causal first failure.

### 5. Native fast-step oracle as a separate experiment

After deterministic replay fingerprints exist, test a render-skipped or
single-step native mode:

- identical executable/content/root/input;
- normal-speed versus accelerated mechanics;
- exact gameplay fingerprint equality;
- no claim about live deadlines; and
- immediate fallback to normal-speed native replay on divergence.

This may yield a faster ground-truth generator without making its process
snapshot a solver state representation.

### 6. Keep mechanics, planning, delivery, and acceptance versions separate

Do not let:

- simulator completeness imply planner optimality;
- planner parity imply physical-model validity;
- accelerated native parity imply real-time delivery;
- one fixed-root win imply RNG robustness; or
- a focused practice win imply Power-0 route authority.

Each artifact should carry immutable model, root, action, content, executable,
coverage, and continuation identities.

## Proposed Iteration Ladder

| Change type | Required inner gate | Native/physical escalation |
| --- | --- | --- |
| Pure proof, recurrence, canonicalization, or planner optimization | Independent scalar oracle, deterministic adversarial cases, Linux/Windows parity as applicable | None unless behavior/model semantics change. |
| Decoder, geometry, lifecycle, RNG, or event-order change | Component simulator + semantic fuzzer + exact-prefix differential | Same short original-game native replay scene. |
| Policy/ranking change inside unchanged exact model | All fixed-root offline counterfactual portfolios | Fixed-initial-root native A/B diagnostic if the policy actually differs. |
| Integrated model version | Full fixed-root corpus, complete coverage report, timing/delivery preflight | One smallest focused real-time falsifier per exercised behavior. |
| Promotion candidate | All mandatory scene families with immutable compatible evidence | Repeated original-game Power-0 route acceptance. |

This ladder means a normal edit can cycle many times without launching the
game. A physical launch occurs only after the offline evidence identifies a
specific claim that the launch can falsify.

## Prioritized Roadmap

### P-001 — Change the experiment protocol immediately

Priority: immediate; no new simulator completeness required.
Evidence: **Observed existing capability.**

- Use the same short native replay scene before and after semantic/model
  changes.
- Freeze a versioned corpus of retained roots/capsules rather than comparing
  aggregate hit counts from unrelated RNG histories.
- Separate fixed-input semantic comparison from policy comparison.
- Do not launch another unchanged full stage merely to see whether the hit
  count moves.
- Preserve fresh physical runs for a named integrated hypothesis and immutable
  version.

### P-002 — Finish a complete one-frame causal root and event ledger

Priority: highest implementation leverage.
Evidence: **Observed gap; concurrent work is already moving in this area.**

The first milestone is not an 80-frame engine. It is one exact physical update
from a full root, including:

- ordered input publication/player/enemy/timeline/bullet/laser/item phases;
- timeline allocation and initial VM execution;
- generational slot identity through same-update retire/reuse;
- player Focus/Shot mode and shared RNG consumption;
- body gates, collision suppression, and end state; and
- explicit `UNKNOWN` for every unsupported callback/opcode/effect.

### P-003 — Grow coverage by reachable event class

Priority order:

1. action publication, player mode/shot cadence, shared RNG;
2. timeline allocation, main/aux VM control, and callback ledger;
3. enemy motion/flags/body eligibility/damage/death/despawn;
4. bullet/laser/item births, transforms, lifecycle, and suppression;
5. exact collision/resource transitions; then
6. bounded multi-frame continuation.

Choose each next class from actual fixed-root coverage failures, not from file
or opcode enumeration alone.

### P-004 — Certify 1, then short, then planning-horizon branches

- Pass exact native differential at one frame.
- Extend to the shortest horizon that crosses a real event boundary.
- Run all 36 complete no-Bomb root masks from the same root.
- Increase horizons only when every shorter mismatch is understood.
- Re-root frequently from native captures to prevent silent long-run drift.

### P-005 — Add fixed-initial-root native policy A/B

Use a default-off diagnostic that fixes the complete initial root/seed while
allowing each controller's actions to consume RNG naturally. This is the
correct native bridge between fixed-input replay and unrelated physical RNG
runs. It remains diagnostic/patch authority, not final unmodified-game
acceptance.

### P-006 — Investigate accelerated native mechanics

Only after P-001–P-004 provide fingerprints capable of detecting changed
semantics.
Do not begin with arbitrary Windows process save states or a full portable
engine.

### P-007 — Retain the existing physical promotion ladder

Once an immutable integrated model wins its offline paired corpus and passes
delivery preflight, run the narrow focused scene, mandatory scene families,
then repeated Power-0 routes. A physical regression routes back to the exact
root/event mismatch rather than to undirected parameter tuning.

## Consolidated Native/IDA Backlog

No IDA database change is proposed merely from external source agreement. The
following read-only native checks are the evidence backlog for the recommended
architecture:

1. recover and revalidate the complete producer/consumer chain for every field
   admitted to the native root capsule;
2. enumerate the exact same-update order of timeline allocation, initial VM
   execution, callbacks, enemy retirement, and slot reuse;
3. close the shared gameplay RNG consumer inventory across player shot,
   enemy/ECL, bullet, item, and callback paths, preserving call order;
4. map unsupported ECL opcodes and callback/global/custom effects to explicit
   executor stop reasons;
5. verify supervisor/frame-control dependencies before any render-skip,
   uncapped, or single-step native experiment; and
6. if process restore is ever reconsidered, establish ownership and restore
   contracts for threads, heaps, pointers, DirectX objects, handles, timers,
   and external input state before using a snapshot as evidence.

Each strong conclusion should be renamed, typed, or commented in IDA only in a
future authorized correction checkpoint and then reconciled with all affected
notes and source.

## Minimal Verification Matrix

| Claim | Minimum deterministic check | Independent/native check | Failure meaning |
| --- | --- | --- | --- |
| One event class is implemented | Scalar or separately written transition oracle; boundary and adversarial cases | Original-game replay from the same exact root/action | First mismatch rejects exact coverage and becomes a shrinkable fixture. |
| One-frame root is complete | Serialize/deserialize/hash round trip; no hidden defaulted state | Capture-close invariants and native before/after fingerprint | Missing/unstable field makes the root partial and counterfactual authority unavailable. |
| Multi-frame prefix is exact | Repeated one-step equals batched stepping; all 36 masks; deterministic rerun | Native replay fingerprint at every frame | End-only agreement is insufficient; first divergent frame is the boundary. |
| Fixed-root policy A/B is causal | Same root/version, separate endogenous RNG evolution, paired result retained | Patched diagnostic native runs from the same initial root | Unpaired or forced-future-RNG results are synthetic ablations only. |
| Accelerated native mode preserves mechanics | Normal-speed and accelerated fixed-replay fingerprints are identical | Repeat across representative event classes and transitions | Any difference rejects accelerated output for semantic authority. |
| Integrated version is promotable | Complete fixed-root corpus, offline timing, exact versions, no unresolved hard-safety coverage | Focused real-time scene, mandatory stages, then repeated Power-0 route | Physical failure remains a counterexample; offline success is not acceptance. |

## Commands And Results Actually Run

- Re-read the connected IDB metadata through IDA Pro MCP. Result: base
  `0x00400000`, file size `840704`, IDB SHA-256 `ec101f...`; this matches the
  retained clean-target-plus-one-byte-patch proof.
- Inspected the clean local `thtk` and `eclmap` snapshots and their remotes.
  Result: TH08 data/ECL tooling and mnemonic maps are present; no runtime
  engine was found.
- Searched GitHub repositories for TH08 simulators/decompilations, Touhou
  engines, replay parsers, and Touhou AI work; then inspected primary
  repositories and source. Result: the matching TH08 decomp exists but its
  central enemy/bullet/player updates are still stubs; PyTouhou is the
  relevant headless architecture precedent; thprac is a native practice
  harness, not a general TH08 save-state engine; visual agents do not remove
  the physical loop.
- Inspected the reviewed repository baseline, handoff/strategy/formal
  contracts, current daily/counterexample shards, simulator, replay protocol,
  causal/future-body contracts, and retained native audit. Result: the missing
  seam is the complete action-conditioned future-world producer, not a lack of
  offline infrastructure.
- Ran no unit, native, Windows, performance, or physical tests. This audit made
  no implementation claim and deliberately avoided the concurrently modified
  worktree.

## Approaches Not Recommended Now

- Building a full renderer/audio/UI-compatible TH08 clone before an exact
  one-frame causal executor.
- Treating thtk/eclmap opcode names as runtime semantics.
- Replaying recorded future bullets after an alternative action.
- Holding future RNG outputs fixed across policies and calling the result
  physical.
- Using Python/C++ agreement as independent physical validation.
- Depending on the current external TH08 decomp for enemy/bullet/player
  execution while those routines remain stubs.
- Replacing native sensing with screenshot detection.
- Using a single full-route hit count as the inner optimization objective.
- General Windows/Wine process snapshotting before exact state ownership,
  thread, handle, and restore boundaries are proved.

## Final Assessment

The workspace does not need to choose between “physical every time” and “write
all of TH08 from scratch.” The effective route is hybrid:

1. **offline scalar/capsule/fuzzer** for most edits;
2. **branchable causal prefix simulator** for policy counterfactuals;
3. **original-game deterministic replay** as the semantic oracle;
4. optionally **accelerated native mechanics** after equality proof; and
5. **real-time physical play** only for delivery and promotion.

thtk helps decode the program content; the matching decomp helps locate and
cross-check native implementation; PyTouhou supplies an architectural
precedent; thprac supplies practice-harness lessons. None replaces the missing
action-conditioned state transition.

The highest-leverage checkpoint is a complete, fail-closed one-frame native
root/executor. Once that seam is correct, iteration can become deterministic,
parallel, paired by initial root, and much faster without weakening the
original-game acceptance target.

## Audit Completion

- All selected authority, formal, counterexample, implementation, and external
  primary-source checks for this scope are complete.
- Connected IDB identity was re-read without database mutation.
- No repository or IDA changes were made by this audit.
- No tests or gameplay were run because the request was analysis-only and the
  shared worktree had concurrent changes.
