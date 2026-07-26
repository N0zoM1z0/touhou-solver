# TH08 Current Handoff

This is the single current-state entrypoint for the TH08 Sakuya/Remilia
Lunatic/Extra no-Bomb solver. It is intentionally short and volatile.
`AGENTS.md` contains durable workspace rules; `STRATEGY.md` is the strategy
status ledger; design notes and run notes contain derivations and history.

## Read In This Order

1. `AGENTS.md`
2. this file
3. `STRATEGY.md`
4. `notes/AUGMENTED_PIPELINE_ROBUST_CONTROL_FORMALIZATION_20260725.md`
5. `notes/FROZEN_MANAGER_INPUT_CLOCK_BOUNDARY_20260726.md`
6. `notes/CANDIDATE_WITNESS_PUBLICATION_CONTRACT_20260726.md`
7. `notes/FEASIBILITY_FIRST_STAGE6B_PHYSICAL_CONTENTION_20260726.md`
8. the lower/upper/anytime notes listed under “Formal references” below
9. the relevant recent run note and counterexample rows before touching live
   behavior

First verify that the physical problem, formal recurrence, implementation, and
publication deadline are still equivalent enough for the claim being made.
Python/C++ parity for the same recurrence is not physical correctness.

## Exact Checkpoint

- Repository: `/home/pentester/coding/codex_ida/th08`
- Branch: `main`
- Algorithmic parent:
  `e41c774 Reject repeated-frame input guard`
- The current HEAD should be the documentation-only handoff checkpoint
  immediately above that parent. If not, inspect the intervening diff before
  trusting this file.
- Source behavior is restored to the better `1ce5b44` controller, with exact
  candidate publication timing retained as shadow telemetry. No TH08 runtime,
  daemon, or unfinished experiment should be alive.
- Linux and Windows quick suites passed `489/489` in `2.495/4.012 s`.
- The only expected untracked file is user-owned `image.png`. Do not stage,
  modify, delete, or clean it.
- The connected IDA database contains some transform-function names/comments
  newer than Git notes. New binary work must use IDA Pro MCP, never REA.

Sanity check:

```bash
cd /home/pentester/coding/codex_ida/th08
git status --short
git log -5 --oneline
PYTHONPATH=scripts python3 -m unittest discover -s tests -p 'test_*.py'
```

Expected pre-work status:

```text
?? image.png
```

## Current Authority Boundary

| Status | Component | Meaning |
| --- | --- | --- |
| live | native-state sensing and TH08 trajectory/laser/enemy projection | Gameplay sensing is native; screenshots are not a sensor. |
| live | local exact collision certificate | Fresh issue-time hard fallback; hard no-Bomb. |
| live | coarse Boolean robust viability | Current global safety authority, subject to its explicit finite model and the unresolved transition-clock boundary. |
| shadow | losing-root stationary candidate verifier | Exact universal verification of a restricted causal candidate can prove finite-model feasibility, but cannot claim unrestricted losing/optimality. |
| shadow | exact candidate witness publication | Retains root, witness, issued-action label, all-action local certificate, version, and timing; it never changes the live mask. |
| offline/shadow | belief lower bounds, revealed-delay upper, resumable threshold refinement | Research tools for feasibility/optimality gaps; too slow and/or too optimistic for live authority as currently integrated. |
| rejected | every-root candidate submission | Caused measurable live CPU/delivery contention. |
| rejected | 50-ms repeated-manager-frame guard | CE-0121: fired on ordinary slow decisions, churned policy versions, and starved viability. |
| rejected | inline/fused survival labels, legacy prewarm, synchronous full upper | Delivery cost or invalid cross-version assumptions outweighed their value. |
| proposal-only | beam, greedy, learned, Monte Carlo, MCTS | May order candidates, never replace worst-case verification. |

Do not quietly promote a shadow component. Promotion requires an updated
formal review, exact authority boundary, focused regressions, clean physical
shadow evidence, and a `STRATEGY.md` status change.

## What Is Actually Open

### P0 — CE-0120: physical input clock at frozen manager frames

Observed in complete Stage-4A replay `100451`: after a spell ended,
`enemy_manager_frame` froze during dialogue/transition while the held
direction continued moving the player. `up_left_fast` moved `434.63 px` to
the top-left boundary across six wall pulses; `left_fast` moved `343.65 px`
to the left boundary across eight.

The attempted 50-ms detector was invalid. Complete Stage-4A run `103856`
produced `2,780` guard firings in `7,925` decisions for only `72` real wall
pulses. Available viability queries fell from `9,073` in `100451` to `691`,
and the run recorded `64` hits. RNG means `21 -> 64` is not a controlled
effect size, but the policy-starvation mechanism is direct. The guard was
reverted.

The next valid step is semantic and shadow-first: identify the actual
phase/dialogue/transition boundary from native state, actuator state, or
verified timing structure; distinguish frozen simulation, ordinary slow
decisions, pauses, and wall-pulse transitions; then replay before granting
any release/epoch/action authority. Use IDA Pro MCP if static binary evidence
is needed. Do not recreate a short raw wall-time threshold.

### P1 — candidate publication is measured, not promoted

Clean Stage-4A shadow `100451` completed `9,222` decisions with `21` hits,
zero Bomb, and no runtime/foreground/manual/JSON failure. Exact losing-root
candidate delivery was `3,913/4,187 = 93.46%`; `438` delivered roots were
candidate-winning, `223` raised the issued action from modeled loss to modeled
feasibility, and publication integrity errors were zero.

Run `103856` added explicit publication-helper timing:

- publication median/p95: approximately `0.0041/0.0059 ms`;
- lookup median/p95: approximately `0.0149/0.0208 ms`;
- exact delivery: `267/297 = 89.9%`;
- `32` winning hits and `17` feasibility-gain rows;
- zero publication-integrity errors.

However, `103856` was physically contaminated by the rejected frame guard.
It validates helper cost and integrity only, not survival or clean contention.
Before considering action authority, run a fresh post-rollback shadow on a
non-Stage-6B workload and retain candidate witness plus alternate-action
certificate. A candidate win proves only feasibility in its declared finite
model.

### P2 — Boolean-losing is not unrestricted losing

Stage-6B losing-only v2 `011639` completed `14,652` hard-no-Bomb decisions
with `26` hits and delivered `6,192/6,618 = 93.56%` exact losing roots without
the contention of the rejected every-root service. All `26` contacts still
followed Boolean-kernel exhaustion.

Two RNG-distinct Stage-6B capsule cohorts each classified 32 roots as:

- 20 exact losing under the tested finite recurrence;
- 11 feasible under a verified stationary candidate;
- 1 feasible only after targeted action-column refinement.

One threshold needed `265.77 ms` before refinement found a positive 32-frame
witness. Candidate exhaustion and a 100-ms deadline therefore remain
unresolved, not losing. The broad research problem is still planning
completeness under partial input-pipeline information, unrestricted
continuation-action growth, future births/transform uncertainty, and issue-time
delivery. Do not spend more performance effort on a recurrence until its
physical/information semantics pass the formal audit.

Priority order:

1. resolve CE-0120’s semantic clock boundary without live authority;
2. obtain a clean post-rollback candidate-publication shadow gate;
3. use retained losing roots to improve attainable lower refinement and
   issue-time feasible-action coverage;
4. refine upper/optimality work only for actions still capable of changing the
   decision;
5. then return to local/native-read latency and broader route strategy.

## Current Physical Evidence

Retain the two newest complete replay-capable bundles per workload:

| Workload | Bundles | Interpretation |
| --- | --- | --- |
| Lunatic Route-2 Stage 6B, candidate shadow | `004142`, `011639` | `004142` every-root service rejected; `011639` losing-only service accepted shadow-only. |
| Lunatic Route-2 Stage 4A, publication/clock boundary | `100451`, `103856` | `100451` clean candidate-delivery shadow and CE-0120 witness; `103856` guard rejection plus helper timing, not a clean survival A/B. |

The `103856` `.session.json` says `failed` only because the original
postprocessor rejected an explicit null enemy snapshot after the accepted
route-complete trial. The parser was repaired and artifacts recovered without
rewriting provenance. Its raw audit passed `10,784` records and `2,060`
capsules; bundle SHA-256:
`d8d6ecdf7b0ae955c58317fd27fa3735fea9c14ee1471faebe1d7fca1f5e4c29`.

The complete `011639` audit passed `14,791` records, `14,652` decisions, and
`2,689` capsules; bundle SHA-256:
`9e8af717c548dc6456d471c15ac2be9777f755d7b94bc3fc6067e4b289b38a77`.

Compact evidence and interpretation live in `notes/runs/`,
`notes/COUNTEREXAMPLES.md`, and `notes/RESEARCH_LOG.md`. Do not delete either
raw bundle until the two-bundle rule in `AGENTS.md` is satisfied by newer
same-workload captures.

Start physical review with:

- `notes/runs/lunatic_route2_stage6b_unattended_20260726_011639.md`
- `notes/runs/lunatic_route2_stage4a_unattended_20260726_100451.md`
- `notes/runs/lunatic_route2_stage4a_unattended_20260726_103856.md`

## Formal References

Read only the subset relevant to the change, but always begin with the base
formalization.

- Base physical/information contract:
  `notes/AUGMENTED_PIPELINE_ROBUST_CONTROL_FORMALIZATION_20260725.md`
- Unrestricted action growth and attainable lower bounds:
  `notes/BUDGETED_BELIEF_REFINEMENT_20260725.md`
- Correctness/performance audit:
  `notes/BELIEF_PIPELINE_CORRECTNESS_AND_PERFORMANCE_20260725.md`
- Incumbent/selective upper:
  `notes/INCUMBENT_UPPER_CERTIFICATION_20260725.md`
- Resumable deadline-safe certification:
  `notes/RESUMABLE_INCUMBENT_CERTIFICATION_20260725.md`
- Feasibility-first anytime synthesis:
  `notes/ANYTIME_DUAL_BOUND_POLICY_SYNTHESIS_20260725.md`
- Exact augmented state/reachable tube:
  `notes/AUGMENTED_PIPELINE_REACHABLE_TUBE_20260725.md`
- Rolling/cross-version prewarm:
  `notes/ROLLING_PIPELINE_PREWARM_20260725.md` and
  `notes/EXACT_ROOT_FRONTIER_PREWARM_20260725.md`
- Candidate service and witness publication:
  `notes/FEASIBILITY_FIRST_STAGE6B_PHYSICAL_CONTENTION_20260726.md` and
  `notes/CANDIDATE_WITNESS_PUBLICATION_CONTRACT_20260726.md`
- Frozen manager/input boundary:
  `notes/FROZEN_MANAGER_INPUT_CLOCK_BOUNDARY_20260726.md`
- Earlier Boolean/losing root analysis:
  `notes/BOOLEAN_FIRST_PENDING_PIPELINE_20260725.md` and
  `notes/LOSING_STATE_ROOT_CAUSE_20260725.md`

Relevant durable counterexamples include CE-0108, CE-0109, CE-0111, CE-0118,
CE-0120, and CE-0121. Do not infer present authority from a historical note;
the table above and `STRATEGY.md` control current status.

## Environment And Build

- WSL distribution: `ubuntu`
- Workspace:
  `/home/pentester/coding/codex_ida/th08`
- Windows game directory:
  `D:\Entertainment\Game\Touhou\[th08] 东方永夜抄 (日文版)`
- WSL game directory:
  `/mnt/d/Entertainment/Game/Touhou/[th08] 东方永夜抄 (日文版)`
- Target: `th08.exe`
- Required SHA-256:
  `330fbdbf58a710829d65277b4f312cfbb38d5448b3df523e79350b879213d924`
- Launcher: `run_th08_no_life_decrement_attach.bat`
- Patch byte: `0x0044D0FA`, expected runtime value `0x00`
- Windows Python:
  `%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe`

The external launcher must call
`scripts\tools\th08_attach_no_life_decrement.py`. A Windows entrypoint under
`scripts/tools/` must prepend its parent `scripts/` directory before imports.

Rebuild ignored native libraries after C++ changes:

```bash
PYTHONPATH=scripts python3 scripts/tools/build_native_planner.py --target linux
PYTHONPATH=scripts python3 scripts/tools/build_native_planner.py --target windows
```

The NumPy fallback is useful for parity but too slow for physical acceptance.
Use `TOUHOU_DISABLE_NATIVE_PLANNER=1` only for explicit ablation.

## Tests And Offline Profiles

Focused test:

```bash
PYTHONPATH=scripts python3 -m unittest discover -s tests \
  -p 'test_th08_laser_model.py'
```

Quick complete suite:

```bash
PYTHONPATH=scripts python3 -m unittest discover -s tests -p 'test_*.py'
```

Quick formal/performance profiles:

```bash
PYTHONPATH=scripts python3 \
  scripts/analysis/audit_pipeline_formal_correctness.py \
  /tmp/pipeline-formal-quick.json
PYTHONPATH=scripts python3 \
  scripts/benchmarks/benchmark_belief_pipeline_workspace.py \
  /tmp/belief-pipeline-quick.json
```

Run full 128-case/unrestricted/capsule profiles only when their model or native
recurrence changes or when retaining evidence. Benchmarks belong in
`scripts/benchmarks/`; reports/differentials in `scripts/analysis/`; explicit
build/probe/patch/capture commands in `scripts/tools/`.

Windows UNC discovery must use this loader. Ordinary `unittest -s <UNC>`,
`cmd.exe` UNC `cd/pushd`, and a PowerShell-only `PSDrive` do not provide an
importable test root:

```bash
/mnt/c/Users/21992/AppData/Local/Microsoft/WindowsApps/python.exe -c \
  'import sys,unittest; root=r"\\wsl.localhost\ubuntu\home\pentester\coding\codex_ida\th08"; sys.path.insert(0,root+r"\scripts"); tests=root+r"\tests"; suite=unittest.TestLoader().discover(tests,pattern="test_*.py",top_level_dir=tests); result=unittest.TextTestRunner(verbosity=1).run(suite); raise SystemExit(0 if result.wasSuccessful() else 1)'
```

Change only the `pattern` for a focused Windows run.

## Physical Trial Commands

The user has authorized unattended launch, input injection, monitoring,
stopping, and identity-scoped cleanup. Do not start a physical run merely to
validate this documentation checkpoint.

Practice stage from WSL, always non-TTY:

```bash
/mnt/c/Windows/System32/cmd.exe /d /c call \
  '\\wsl.localhost\ubuntu\home\pentester\coding\codex_ida\th08\run_th08_practice_agent.bat' \
  --stage 4a --status-seconds 15 --stall-timeout 120
```

Continuous Lunatic Route-2:

```bash
/mnt/c/Windows/System32/cmd.exe /d /c call \
  '\\wsl.localhost\ubuntu\home\pentester\coding\codex_ida\th08\run_th08_full_route_agent.bat' \
  --status-seconds 30 --stall-timeout 120
```

Selectable Sakuya/Remilia Route-2 practice stages are
`1 2 3 4a 5 6b`; 4B and 6A are route-locked. Do not patch the route mask to
claim coverage.

Important WSL/Windows behavior:

- never launch the supervisor with a PTY; a PTY can block on a Windows console
  cursor query before the game appears;
- a WSL `cmd.exe`/Windows-Python call can return while the supervisor remains
  alive under `/init`; completion requires the trace, terminal record, final
  summary, session status, and process cleanup;
- monitor active gameplay using low-load Linux reads; Windows consoles and
  process probes can steal foreground and invalidate the run;
- stop the supervisor first and allow its `finally` cleanup; release keys
  before killing only the verified TH08 image;
- never end a turn with a required game, supervisor, or daemon still running.

Monitor a trace:

```bash
trace=$(ls -1t artifacts/runtime_reports/*unattended*.jsonl | head -n1)
PYTHONPATH=scripts python3 scripts/analysis/th08_longrun_status.py "$trace"
tail -n 1 "$trace"
```

Full-route success requires both Final-B `terminal_unload` and the later
`termination_reason=route_complete`. Record foreground loss, manual input,
manual `Z`, reset tails, unexpected Bomb, and auto-confirm failure as
contamination.

For a focused thprac loop, start a fresh prewarmed Windows hotkey daemon for
each attempt, enter gameplay manually, then use F8 to start, F9 to stop/pause,
and F10 to exit. The unattended supervisor remains the preferred acceptance
path because it also validates menus, terminal unload, no-save handling,
artifacts, and cleanup.

## Next Good Checkpoint

A useful next algorithmic checkpoint is not another threshold tweak. It should:

1. write the semantic frozen-manager/input-clock hypothesis and observation
   contract before code;
2. collect or replay shadow evidence that distinguishes true transition
   freezes from ordinary slow decisions without changing live input;
3. use IDA Pro MCP/native probes if required to identify a stable state bit,
   phase transition, input-poll clock, or dialogue owner;
4. compare against CE-0120 and CE-0121 plus a normal-play negative set;
5. keep detection shadow-only until false-positive/false-negative behavior and
   action consequence are independently bounded;
6. run focused tests and the quick Linux suite;
7. update the formal/design note, `STRATEGY.md`,
   `notes/COUNTEREXAMPLES.md`, and `notes/RESEARCH_LOG.md`;
8. commit one focused checkpoint.

If instead working on candidate authority, first obtain a fresh uncontaminated
post-rollback Stage-4A (or another non-Stage-6B) shadow run with exact witness,
alternate-action certificate, publication timing, and measured
CPU/delivery/policy-age contention. A physical run remains evidence, not a
promotion by itself.

## Common Traps

- Do not use REA.
- Do not treat Python/C++ parity as problem correctness.
- Do not treat a budgeted lower bound, exhausted candidate set, timeout, or
  incomplete upper as unrestricted losing/optimality.
- Do not let hidden delay/cadence branches choose separate future actions.
- Do not reset pending delay when the desired mask is held/no-write.
- Do not use `enemy_manager_frame` or a short wall-time threshold as the only
  physical input clock.
- Do not grant action authority to candidate/label shadow output.
- Do not submit expensive shadow work on every root or share the live
  publication critical path.
- Do not reuse proof labels across immutable policy versions.
- Do not tune one stage/spell into universal mechanics.
- Do not add engineering-plumbing tests that do not protect evidence or a
  safety contract.
- Do not confuse compact reports with replay-capable raw evidence.
- Do not stage `image.png`, connector-created `node_modules/`/`package*.json`,
  raw JSONL, capsules, binaries, logs, caches, or credentials.
