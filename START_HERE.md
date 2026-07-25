# TH08 Agent Handoff

This is the operational handoff for continuing the TH08 Sakuya/Remilia
Lunatic/Extra no-Bomb solver. Read `AGENTS.md` first; its evidence, artifact,
test, physical-trial, and commit requirements are binding.

Read `STRATEGY.md` before changing control objectives. It is the status ledger
for live, shadow, rejected, and proposed strategies; detailed derivations and
runtime evidence remain in `notes/`.

For any viability, losing-state, delay, cadence, reachable-tube, or prewarm
change, also read
`notes/AUGMENTED_PIPELINE_ROBUST_CONTROL_FORMALIZATION_20260725.md` before
touching the algorithm.  First check that the implemented state, observation
partition, transition, uncertainty, and objective still represent the stated
problem.  An engineering approximation is acceptable without a complete
proof, but its optimistic/conservative/unknown error direction, oracle gate,
counterexamples, delivery deadline, and fail-closed fallback must be explicit.
Python/C++ parity for the same recurrence is not by itself problem
correctness.  In particular, verify all three mappings before performance
work:

```text
planner choice -> input transitions actually sent -> native action observed
```

Choosing the already-held desired mask is hold/no-write; it does not sample a
new delay and must not reset an older pending command.  Then answer the five
formal-review questions in `AGENTS.md`: state equivalence, causal uncertainty,
physical relevance, solver/bound validity, and issue-time deliverability.
Engineering approximations are encouraged when useful, but unknown-direction
ones remain shadow-only.

For continuation-action growth, also read
`notes/BUDGETED_BELIEF_REFINEMENT_20260725.md`.  The active native/scalar
prototype gives nested attainable lower bounds `L_0 <= L_1 <= ... <=
V_unrestricted`; agreement between adjacent budgets is not an unrestricted
optimality proof. Then read
`notes/INCUMBENT_UPPER_CERTIFICATION_20260725.md`: a completed attainable
lower label can now drive an exact threshold query against the proved
revealed-delay upper recurrence, without constructing every complete upper
label. Then read
`notes/RESUMABLE_INCUMBENT_CERTIFICATION_20260725.md`: hard threshold roots
can be divided into conservative short service slices only while the
immutable version, canonical root, and bit-identical lower threshold remain
unchanged.
Then read `notes/ANYTIME_DUAL_BOUND_POLICY_SYNTHESIS_20260725.md`. The active
offline result separates modeled feasibility from unrestricted optimality:
an exactly verified causal candidate policy can prove a full-horizon action
in a few milliseconds, while upper work is reserved for unresolved-action
refinement or an optimality claim. Across versions, reuse search order only;
every candidate label must be recomputed under the current immutable model.
Before changing candidate delivery or granting it any authority, read
`notes/FEASIBILITY_FIRST_STAGE6B_PHYSICAL_CONTENTION_20260726.md`. The
accepted shadow form submits only available Boolean-losing exact roots to one
below-normal-priority worker. Candidate/budget exhaustion is unresolved, not
losing, and every-root submission is physically rejected for contention.

## 1. Exact Checkpoint

- Repository: `/home/pentester/coding/codex_ida/th08`
- Branch: `main`
- The current checkpoint builds on
  `4c4b480 Synthesize verified anytime belief policies`. It adds a
  bounded stationary-candidate verifier, aggregate between-candidate budget,
  newest-target exact-key service, below-normal worker priority, losing-only
  admission, raw-bundle read/hash audit, and physical contention/delivery
  analysis. The service remains explicit shadow telemetry and never changes
  the live mask.
- Two RNG-distinct Stage-6B capsule cohorts each classified 32 roots as 20
  exact losing, 11 stationary-candidate feasible, and one feasible only after
  targeted action-column refinement. Candidate median/p95 was
  `2.13/6.75 ms` and `2.22/8.09 ms`. One `000654` threshold required
  `265.77 ms` before refinement found a 32-frame positive witness, proving
  that stationary-candidate exhaustion is not an unrestricted losing claim.
- The first physical candidate shadow `004142` ran on every root. It delivered
  8,004/12,220 exact roots but accumulated 205 queue replacements and 1,099
  stale completions. Relative to Boolean-only `000654`, local-plan median rose
  `21.20 -> 26.46 ms`, iteration `45.89 -> 53.11 ms`, action lag `2 -> 3`
  frames, and policy age `3 -> 4`; this form is rejected.
- Losing-only v2 `011639` completed hard-no-Bomb Stage 6B over frames
  `2..74963`, with 14,652 decisions, 26 native hits, zero Bomb, and no runtime,
  JSON, foreground, or manual-rearm failure. It delivered 6,192/6,618 exact
  losing roots (`93.56%`) with zero replacement/stale completion. Iteration
  median was `44.88 ms`, action lag/cadence `2/3` frames, and first policy age
  `3` frames, all back inside the Boolean-only baseline envelope. This accepts
  the service architecture as shadow-only; the RNG-distinct hit count is not
  a survival claim and all 26 hits still followed Boolean-kernel exhaustion.
- The complete v2 raw bundle passed full JSONL/reference/capsule validation:
  14,791 records, 14,652 decisions, 2,689 readable capsules, zero missing
  references, bundle SHA-256
  `9e8af717c548dc6456d471c15ac2be9777f755d7b94bc3fc6067e4b289b38a77`.
  The two locally retained complete replay bundles are `004142` and `011639`.
- Linux and Windows complete quick suites pass 481 tests in
  `2.187/3.461 s`. Read
  `notes/FEASIBILITY_FIRST_STAGE6B_PHYSICAL_CONTENTION_20260726.md`,
  `notes/INCUMBENT_UPPER_CERTIFICATION_20260725.md`,
  `notes/RESUMABLE_INCUMBENT_CERTIFICATION_20260725.md`,
  `notes/ANYTIME_DUAL_BOUND_POLICY_SYNTHESIS_20260725.md`,
  `notes/BUDGETED_BELIEF_REFINEMENT_20260725.md`,
  `notes/BELIEF_PIPELINE_CORRECTNESS_AND_PERFORMANCE_20260725.md`,
  `notes/AUGMENTED_PIPELINE_ROBUST_CONTROL_FORMALIZATION_20260725.md`,
  `notes/ROLLING_PIPELINE_PREWARM_20260725.md`,
  `notes/EXACT_ROOT_FRONTIER_PREWARM_20260725.md`,
  `notes/AUGMENTED_PIPELINE_REACHABLE_TUBE_20260725.md`,
  `notes/runs/lunatic_route2_stage6b_unattended_20260726_011639.md`,
  `notes/BOOLEAN_FIRST_PENDING_PIPELINE_20260725.md`,
  `notes/LOSING_STATE_ROOT_CAUSE_20260725.md`, CE-0108/0109/0118, and
  `STRATEGY.md` before changing viability queries or losing-state authority.
- The expected user-owned untracked file is `image.png`. It is a screenshot.
  Do not add, delete, overwrite, or otherwise clean it. The Codex connector
  may also materialize a root `node_modules/` plus `package*.json` for its
  running `leantoken` MCP process; these are not TH08 dependencies or commit
  candidates. Do not confuse them with project artifacts or terminate/delete
  them while that external connector is active.
- Ignored raw JSONL and viability capsules are retained only for the newest
  two read-audited complete bundles per active workload. Screenshots, launch
  logs, caches, native build outputs, discarded raw attempts, and older
  replay bundles are cleanup candidates after compact evidence is verified.
- No TH08 runtime/control session or half-edited experiment is part of the
  checkpoint.
- The IDA database has newer metadata than Git: the transform functions listed
  in section 10 were renamed/commented during the callback investigation.
- Workspace policy now forbids new REA use. Historical REA Evidence IDs remain
  provenance only; use the connected IDA Pro MCP for new binary analysis.

Sanity check:

```bash
cd /home/pentester/coding/codex_ida/th08
git status --short
git log -5 --oneline
PYTHONPATH=scripts python3 -m unittest discover -s tests -p 'test_*.py'
```

Expected status before new work:

```text
?? image.png
```

## 2. Goal And Non-Negotiable Policy

The final acceptance target is physical Sakuya/Remilia control for TH08
Lunatic and Extra. An offline route is not accepted until the real game
executes it and retained artifacts validate collisions, timing, resources,
items, transitions, and inputs.

Current diagnostic policy is hard no-Bomb:

- Never emit input bit `0x02`.
- Do not enable either normal Bomb or deathbomb.
- The no-life-decrement runtime patch keeps a discovery run alive, but a native
  hit is still a failure and must be retained.
- The first hit of a fresh practice attempt is the canonical causal witness.
  Later hits are valid discovery evidence, but death/respawn has changed
  bullets, position, Power, and resources.
- Survival is the hard constraint. Graze, collection, Power, score, damage,
  and preferred position are objectives only inside the viable action set.
- Do not add spell IDs, stage directions, or hand-authored routes to fix one
  trace. Improvements must generalize to other stages and Touhou games.

The user explicitly authorizes unattended launch, physical input injection,
monitoring, stopping, and decisive process termination when a run stalls.

## 3. Environment

### Paths And Identity

- WSL distribution: `ubuntu`
- Workspace root:
  `/home/pentester/coding/codex_ida/th08`
- Windows game directory:
  `D:\Entertainment\Game\Touhou\[th08] 东方永夜抄 (日文版)`
- WSL game directory:
  `/mnt/d/Entertainment/Game/Touhou/[th08] 东方永夜抄 (日文版)`
- Required launcher:
  `run_th08_no_life_decrement_attach.bat`
- That external BAT must invoke
  `scripts\tools\th08_attach_no_life_decrement.py`. The patcher prepends the
  parent `scripts\` directory before importing `th08_runtime_agent`; the old
  pre-reorganization `scripts\th08_attach_no_life_decrement.py` path does not
  exist.
- Target:
  `th08.exe`
- Required SHA-256:
  `330fbdbf58a710829d65277b4f312cfbb38d5448b3df523e79350b879213d924`
- No-life-decrement patch byte:
  `0x0044D0FA`, expected runtime value `0x00`.
- Windows Python used by the wrapper:
  `%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe`
- On this host `%LOCALAPPDATA%` currently resolves below
  `C:\Users\21992\AppData\Local`.

Normal launch/control does not require `sudo`. The operator supplied a sudo
password out of band, but `AGENTS.md` forbids persisting credentials. Ask the
operator if a future, genuinely necessary command needs it; do not write it
into Git, logs, shell history, or artifacts.

### Keyboard And IME

- The operator switched Windows to English input mode.
- The unattended supervisor also enables and verifies Caps Lock before menu
  input. This protects scan-key navigation from IME state.
- Gameplay input uses native state plus Win32 `SendInput`; screenshots are
  never a gameplay sensor.
- Always release injected keys on stop/error.

### Native Planner

Rebuild both ignored native libraries after changing the C++ kernel:

```bash
PYTHONPATH=scripts python3 scripts/tools/build_native_planner.py --target linux
PYTHONPATH=scripts python3 scripts/tools/build_native_planner.py --target windows
```

The agent falls back to NumPy if a native library is absent, but that path is
too slow for the physical acceptance workload. Use
`TOUHOU_DISABLE_NATIVE_PLANNER=1` only for explicit parity/ablation tests.

## 4. Preferred One-Command Physical Trial

Use the original game unattended supervisor. It is the preferred integration
loop and does not require thprac or an F8 handoff.

From a Windows console:

```bat
\\wsl.localhost\ubuntu\home\pentester\coding\codex_ida\th08\run_th08_practice_agent.bat --stage 5
```

From WSL/Codex, launch it without a PTY:

```bash
cd /home/pentester/coding/codex_ida/th08
/mnt/c/Windows/System32/cmd.exe /d /c call \
  '\\wsl.localhost\ubuntu\home\pentester\coding\codex_ida\th08\run_th08_practice_agent.bat' \
  --stage 5 --status-seconds 15 --stall-timeout 120
```

For an explicit post-publication label shadow, the direct Windows Python form
below is also verified. Keep it non-TTY; the supervisor still launches and
verifies the patch BAT itself:

```bash
/mnt/c/Users/21992/AppData/Local/Microsoft/WindowsApps/python.exe \
  '\\wsl.localhost\ubuntu\home\pentester\coding\codex_ida\th08\scripts\th08_practice_supervisor.py' \
  --armed --stage 5 --viability-audit --postpublished-survival-shadow
```

Important execution detail:

- Use a non-TTY subprocess. A previous PTY launch blocked on a Windows console
  cursor-position query (`ESC[6n`) before the game appeared.
- With Codex `exec_command`, use a short initial yield (about 1 second). If a
  session ID is returned, poll it with `write_stdin` every 15-30 seconds.
- On this host, direct Windows Python or `cmd.exe` interop may return from the
  Linux call while the Windows supervisor remains alive below `/init`. That
  return is not trial completion. Check the exact interop process, growing
  JSONL, terminal summary, and final `.session.json` status instead.
- During gameplay, monitor through low-load Linux reads only. Do not open a
  Windows console or run PowerShell/process probes merely for status: it can
  steal foreground and the agent will correctly discard the run. Use Windows
  process inspection only after the trace has terminated or for supervised
  recovery from a real stall.
- Do not end a turn while the required trial session is still running.
- The supervisor's default whole-trial timeout is 4,500 seconds.
- Its default no-progress timeout is 120 seconds. It requests an agent stop,
  releases keys, and kills the exact verified game during cleanup.

The supervisor performs this complete sequence:

1. Enable and verify Caps Lock.
2. Terminate only an identity-verified stale copy of this exact TH08 image.
3. Launch `run_th08_no_life_decrement_attach.bat`.
4. Verify image hash and patch byte.
5. Acquire foreground ownership.
6. Select main-menu cursor 3, the fourth item: Practice Start.
7. Select Lunatic cursor 3.
8. Select team cursor 2 by pressing Right twice: Sakuya/Remilia is the third
   team. Do not use Up/Down on the team page.
9. Select the requested stage using native cursor feedback.
10. Prewarm and arm the no-Bomb agent before the final stage-confirm `Z`.
11. Monitor the trace and auto-pulse fresh `Z` edges in sustained empty
    dialogue/transition scenes.
12. On accepted stage completion, press Right once at the save prompt to choose
    no-save, then kill the game.
13. Generate compact dossier, death ledger, regression, comparison, session,
    summary, and run-note artifacts.

Useful supervisor options:

```bat
run_th08_practice_agent.bat --stage 6b --repeat 3
run_th08_practice_agent.bat --stage 4a --forever
run_th08_practice_agent.bat --stage 3 --status-seconds 10 --stall-timeout 90
```

Do not use `--forever` blindly while developing. Run one complete stage,
analyze its counterexamples, fix a general cause, test, then run another
randomized stage.

### Continuous Lunatic Full Route

Use the dedicated normal-Game-Start supervisor for one continuous Stage 1
through Final B trace:

```bat
\\wsl.localhost\ubuntu\home\pentester\coding\codex_ida\th08\run_th08_full_route_agent.bat
```

From WSL/Codex, preserve the same non-TTY and literal-UNC quoting rules:

```bash
/mnt/c/Windows/System32/cmd.exe /d /c call \
  '\\wsl.localhost\ubuntu\home\pentester\coding\codex_ida\th08\run_th08_full_route_agent.bat' \
  --status-seconds 30 --stall-timeout 120
```

The native normal-start title modes are main `0`, difficulty `4`, and team
`5`. On a fresh launch the supervisor deliberately sends Down then Up and
verifies main cursor `0` before `Z`; merely reading cursor `0` did not produce
a reliable Game Start transition. It then selects Lunatic cursor `3`,
Sakuya/Remilia team cursor `2`, prewarms the agent, and lets the agent's final
`Z` enter gameplay. The live worker expects Stage 1 and leaves the terminal
stage unset so the native successor chain must reach route completion.

Full-route acceptance requires a Final-B `scene_inactive` record with status
`terminal_unload`, followed by the terminal summary
`termination_reason=route_complete`. The two-stage guard is intentional: the
summary is promoted only after the terminal inactive grace period. The
supervisor uses a 4,500-second worker deadline, a 4,650-second outer deadline,
hard no-Bomb, no safety-value/refinement/survival-label authority, and always
releases keys and terminates only the exact verified game.

## 5. Stage Mapping And Randomization

The menu supports eight rows, but the current Sakuya/Remilia Lunatic native
availability mask is `0x40AF`. Only six route-2 Practice stages are selectable:

| CLI | Menu row | Native route index | Available |
| --- | ---: | ---: | --- |
| `1` | 1 | 0 | yes |
| `2` | 2 | 1 | yes |
| `3` | 3 | 2 | yes |
| `4a` | 4 | 3 | yes |
| `4b` | 5 | 4 | no, route-locked |
| `5` | 6 | 5 | yes |
| `6a` | 7 | 6 | no, route-locked |
| `6b` | 8 | 7 | yes |

Do not patch the route mask merely to claim 4B/6A coverage. Route 2 naturally
uses 4A and Final B.

Choose among `1 2 3 4a 5 6b` after each verified checkpoint. A simple WSL
choice is:

```bash
stage=$(printf '%s\n' 1 2 3 4a 5 6b | shuf -n1)
printf 'selected stage: %s\n' "$stage"
```

Randomization guards against tuning only one spell. Enemy lifecycle and
world-motion handling have now been exercised on complete Stage 4A and Stage
5 runs. After the next algorithmic checkpoint, choose from `1 2 3 4a 5 6b`
rather than repeating only one Reisen spell.

## 6. Monitoring, Stops, And Stalls

The supervisor prints records like:

```text
trial status: kind=decision frame=... stage=... spell=... hits=... bullets=... lasers=...
```

Inspect any growing trace explicitly:

```bash
trace=$(ls -1t artifacts/runtime_reports/*unattended*.jsonl | head -n1)
PYTHONPATH=scripts python3 scripts/analysis/th08_longrun_status.py "$trace"
tail -n 1 "$trace"
```

Stop order:

1. Send `Ctrl+C` to the active supervisor session.
2. Wait up to 15 seconds for its `finally` cleanup.
3. Verify Windows processes if it does not return.
4. Release injected keys before a forced kill.
5. Kill only the exact TH08 process.

Release keys from WSL with Windows Python:

```bash
/mnt/c/Users/21992/AppData/Local/Microsoft/WindowsApps/python.exe -c \
  "import sys;sys.path.insert(0,r'\\wsl.localhost\\ubuntu\\home\\pentester\\coding\\codex_ida\\th08\\scripts');from th08_runtime_agent import Win32,release_injected_keys;release_injected_keys(Win32())"
```

Audit the target before killing:

```bash
/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe \
  -NoProfile -Command \
  "Get-Process th08 -ErrorAction SilentlyContinue | Select-Object Id,Path"
```

If exactly one process has the expected game path and the supervisor cleanup
is irrecoverably stuck:

```bash
/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe \
  -NoProfile -Command \
  "Get-Process th08 -ErrorAction SilentlyContinue | Where-Object Path -eq 'D:\Entertainment\Game\Touhou\[th08] 东方永夜抄 (日文版)\th08.exe' | Stop-Process -Force"
```

Also terminate a stranded Windows Python supervisor after the game and keys
are safe. Do not use broad `taskkill /IM python.exe` because it can kill IDA
or unrelated Python work.

Reject and label a trial if it has:

- lost foreground ownership;
- wrong difficulty, route, stage, image hash, or patch byte;
- manual gameplay input contamination;
- a frame reset tail merged with an earlier attempt;
- timeout/stall termination rather than `route_complete`;
- an unexpected Bomb bit or Bomb decision;
- missing trace output at gameplay entry.

## 7. Manual thprac/F8 Focused Loop

Use this only to isolate a later stage/spell faster than the original menu.

1. Start the exact game through
   `run_th08_no_life_decrement_attach.bat`.
2. Start a fresh, prewarmed Windows hotkey daemon:

   ```bat
   %LOCALAPPDATA%\Microsoft\WindowsApps\python.exe \\wsl.localhost\ubuntu\home\pentester\coding\codex_ida\th08\scripts\th08_agent_hotkey.py
   ```

3. The operator selects Lunatic, Sakuya/Remilia, and the checkpoint in
   `thprac.v2.1.3.0.exe`.
4. Press F8 only after gameplay is entered. The daemon takes over immediately.
5. Press F9 to stop and pause. F10 quits.
6. The daemon is deliberately one-shot. Start a fresh daemon before every new
   attempt; otherwise a later F8 must not start a second trace.

Daemon logs:

```bash
tail -f /tmp/th08_agent_hotkey.out
tail -f /tmp/th08_agent_hotkey.err
```

The hotkey agent uses `--stop-after-hits 0`, `--trace-radius 160`,
`--auto-confirm-every 15`, `--no-bomb`, and a one-hour duration. F8 validates
the exact process, patch, foreground window, difficulty, and route before it
injects anything.

The unattended supervisor is safer for acceptance because it also verifies
menu state, terminal unload, no-save handling, process cleanup, and artifact
materialization.

## 8. Artifacts, Review, And Commits

Raw runtime files are intentionally ignored:

- `artifacts/runtime_reports/*.jsonl`
- `artifacts/runtime_reports/*.log`
- screenshots and caches

Ignored does not mean disposable. For each active physical validation
workload, keep the two newest complete replay bundles: raw JSONL, matching
audit-capsule directory, and session provenance. A discarded/truncated or
schema-incompatible run does not count. Delete an older bundle only after two
newer same-workload bundles pass a read audit and their compact tracked
reports exist. This floor prevents a compact summary from being mistaken for
replayable evidence.

For every complete physical trial used in a conclusion, retain:

- `.session.json`
- `.summary.json`
- `.dossier.json`
- `.dossier.md`
- `.deaths.csv`
- `.regressions.json`
- `.comparison.json` when a prior accepted stage exists
- matching human-readable note below `notes/runs/`

The unattended supervisor generates these automatically. Then:

1. Read every hit row, per-phase health table, delay/cadence data, kernel
   exhaustion, boundary occupancy, Power/items, and termination evidence.
2. Add a durable failure entry to `notes/COUNTEREXAMPLES.md`.
3. Add the checkpoint and interpretation to `notes/RESEARCH_LOG.md`.
4. Add the smallest useful synthetic or retained regression.
5. Run the smallest focused tests. Before a code checkpoint, run the quick
   complete unit suite. Run heavy capsule/audit replays only when their model
   changed; run Windows validation for Windows/native/live promotion work.
6. Stage files explicitly. Never stage `image.png`, JSONL, launch logs, daemon
   logs, game files, binaries, credentials, or native build output.
7. Commit a focused, verified checkpoint.

Quick complete unit command:

```bash
PYTHONPATH=scripts python3 -m unittest discover -s tests -p 'test_*.py'
```

The default belief/formal research profiles are intentionally short:

```bash
PYTHONPATH=scripts python3 \
  scripts/analysis/audit_pipeline_formal_correctness.py \
  /tmp/pipeline-formal-quick.json
PYTHONPATH=scripts python3 \
  scripts/benchmarks/benchmark_belief_pipeline_workspace.py \
  /tmp/belief-pipeline-quick.json
```

When the belief recurrence or native kernel changes, retain the full
benchmark explicitly:

```bash
PYTHONPATH=scripts python3 \
  scripts/benchmarks/benchmark_belief_pipeline_workspace.py \
  artifacts/benchmarks/budgeted_belief_refinement_20260725.json \
  --profile full --small-cases 128 --timeout-ms 3000
```

Use `--cases 128` on the formal audit only when its model/recurrence changes.
Do not put these full profiles or raw capsule replay into unit-test setup.

The retained augmented-pipeline differential is an experiment, not unit-test
setup:

```bash
PYTHONPATH=scripts python3 \
  scripts/benchmarks/benchmark_augmented_pipeline_workspace.py \
  artifacts/benchmarks/augmented_pipeline_workspace_20260725.json \
  --scalar-seeds 512 --th08-cases 10
```

The retained exact-root frontier/phase-shard experiment is:

```bash
PYTHONPATH=scripts python3 \
  scripts/benchmarks/benchmark_exact_root_frontier.py \
  artifacts/benchmarks/exact_root_frontier_20260725.json \
  --scalar-seeds 512 --th08-cases 5
```

The command must include `PYTHONPATH=scripts`. Running bare unittest discovery
causes import errors for every script module; that is a test invocation error,
not a product regression.

Windows Python cannot use the ordinary CLI discovery command directly on this
UNC workspace: `unittest discover -s <UNC>` treats the non-package `tests/`
directory as non-importable. `cmd.exe` also cannot make UNC a current
directory, and a session-local PowerShell `PSDrive` is not visible to the
external Python process. From WSL, use the loader directly and give it the
same UNC directory as `start_dir` and `top_level_dir`:

```bash
/mnt/c/Users/21992/AppData/Local/Microsoft/WindowsApps/python.exe -c \
  'import sys,unittest; root=r"\\wsl.localhost\ubuntu\home\pentester\coding\codex_ida\th08"; sys.path.insert(0,root+r"\scripts"); tests=root+r"\tests"; suite=unittest.TestLoader().discover(tests,pattern="test_*.py",top_level_dir=tests); result=unittest.TextTestRunner(verbosity=1).run(suite); raise SystemExit(0 if result.wasSuccessful() else 1)'
```

Change only the `pattern` for a focused Windows file. Do not retry CLI UNC
discovery, `cmd.exe` UNC `cd/pushd`, or a PowerShell-only drive mapping.

Before commit:

```bash
git diff --check
git status --short
git diff --stat
```

## 9. Current Physical Results

These are independent complete Practice runs, not one continuous route and not
same-seed A/B trials:

| Stage | Latest run | Hits | Interpretation |
| --- | --- | ---: | --- |
| 1 | `070946` | 4 | default-policy control |
| 2 | `091120` | 3 | CE-0083 phase witness |
| 3 | `123136` | 8 | default safety-value-off cross-control |
| 3 | `132007` | 15 | rejected safety-value-on experiment |
| 4A | `185059` | 26 | corrected world-motion/lifecycle model; two post-issue births |
| 5 | `103655` | 34 | Boolean-only losing-state root-cause baseline |
| 5 | `122624` | 20 | rejected same-executor label shadow; CE-0108 |
| 5 | `125037` | 18 | accepted delivery isolation; labels had no authority |
| 6B | `135201` | 27 | latest fused-laser cross-control |

Do not sum these rows into a route score. Native RNG, controller versions,
death/respawn Power, and experimental switches differ. Stage-5's preceding
comparable run had 31 hits, but the 31-to-16 delta is not a causal survival
estimate.

Key accepted improvements:

- Phase-exact laser lifecycle and time-indexed segment geometry.
- Shared packed laser timeline across prefix/local/terminal/robust checks.
- Fused local lifecycle-to-packed laser projection; Stage-6B spell 154 local
  timing improved across runs, while survival remains open.
- Native game-neutral clearance and backward-viability kernels; the
  cap-bounded hazard-major traversal is physically exercised.
- Sparse native piecewise AABB projection for callback-driven stop/resume
  trajectories; Stage-5 spell-107/111 tail latency is physically accepted.
- `exists action, forall learned delay` robust control semantics.
- Adaptive delay/hold telemetry.
- Work-conserving async worker with the full configured delay support `{1..6}`.
- Certificate preservation at continuous off-grid/clamped states.
- Native-consistent local motion clamping.
- Delay-scaled boundary control reserve during empty-kernel recovery, now
  ordered after preflight robust first-action certificates.
- Capture-time and issue-time epoch/deadline guards that prevent stale new
  direction injection.
- Hybrid enemy observation modes: contact-enabled, active contact-disabled,
  bounded dormant memory, and observed lethal-world-position derivatives.
- Strict issue-time enemy topology/trajectory versioning plus fresh
  global/local action-contract intersection.
- Original-game unattended menu, monitor, dialogue, no-save, kill, and
  artifact loop.

Current Stage-5 Boolean-first evidence:

- Boolean-only `103655` had first policy age `6/12` frames, query age
  `11/27`, and 14 expired decisions.
- Same-executor shadow `122624` retained Boolean/label array parity but raised
  expired decisions to 34. It is rejected as a delivery scheduler.
- Separate-executor, one-label-worker shadow `125037` restored first policy
  age to `4/10`, query age to `11/27`, and expiry to 15. Local read/plan and
  action lag remained `13.08/18.18 ms`, `22.71/42.74 ms`, and `3/5` frames.
- Issued desired input disagreed with game-observed active input on
  754/8,077 and 805/7,772 queries in the two shadows. Exact pending-pipeline
  cohorts changed 13/16 best-action sets in each run. Dense labels therefore
  remain shadow-only; do not compare the RNG-distinct hit totals as a survival
  effect.
- Full evidence:
  `notes/BOOLEAN_FIRST_PENDING_PIPELINE_20260725.md`.

Historical Stage-5 differential-corpus evidence:

- Run ID: `lunatic_route2_stage5_unattended_20260724_201636`
- Frames: `2..46642`
- Hits: 27; Bomb input: zero; accepted completion: yes
- Contact classes: 10 exact bullet overlaps, 16 committed-prefix collisions,
  and one sensor gap.
- Local plan median/p95: `28.45/60.51 ms`; cadence `4/8` frames.
- Global solve median/p95: `100.17/166.71 ms`, excluding diagnostic capsule
  I/O. Synchronous capture added `91.58/117.58 ms` and made this run
  unsuitable for a hit-count or service-time comparison. Writes are now
  asynchronous, with physical timing pending.
- Available policy queries: 7,309; empty action sets: 4,635. The last two
  available pre-hit queries for all 27 hits were reconstructed exactly.
- Differential primary classes are 51 modeled-losing/unresolved and three
  16-pixel spatial coarse false-empties. One separate phase-107 collision
  bullet was absent from the governing policy source.
- Fused survival labels cover 54/54 samples. One query before hit 3,491
  guaranteed 10 modeled safe frames over an eight-frame hit interval while
  endpoint recovery issued an action outside the best mask; the other 53
  guarantees were shorter than time-to-hit.
- The 27-hit count must not be compared causally with `191313`: RNG,
  respawn/Power, and the old synchronous capture path differ.

## 10. IDA Pro MCP

### IDA Pro MCP

- IDA runs on the Windows host.
- MCP endpoint: `http://localhost:13337`
- If IDA tools are not already exposed, use tool discovery for
  `ida-pro-mcp decompile function rename function set comment`.
- Persist strong conclusions by renaming/commenting the IDB and summarize them
  in `notes/RESEARCH_LOG.md`.
- Do not modify game bytes through IDA for solver experiments.

Latest IDA metadata:

| Address | Name |
| --- | --- |
| `0x0042F5F0` | `bullet_spawn_from_emission_descriptor` |
| `0x0042FFC0` | `bullet_apply_next_transform` |
| `0x00432460` | `bullet_update_stop_turn_repeat` |
| `0x004325A0` | `bullet_update_stop_snap_repeat` |
| `0x004326E0` | `bullet_update_stop_reaim_repeat` |

Comments were added at:

- `0x0042FD8C`: copy 18 x 24-byte transform records to bullet `+0xDD0`.
- `0x0042FDA2`: original flags `+0xDB0`, active flags `+0xDAC`, queue index
  `+0xDCC`, then queue execution.
- `0x00430380`: shared 0x40/0x80/0x100 stop setup fields.
- `0x0043246C`: stop timer current/duration.
- `0x00432754`: re-aim completion, repeat clearing, target-relative angle, and
  resume speed.
- `0x0042DF57`: `enemy+0x2D4C` advances an internal component, not the lethal
  world-position derivative.
- `0x0042CA54`: lethal/render world position `+0x2D88` is composed later.

Do not use REA, its skill, setup, or doctor commands for TH08. Historical REA
Evidence IDs in older notes remain provenance for already-recorded
conclusions. New static conclusions must come from the connected IDA Pro
database and new execution claims must come from native runtime
traces/probes.

## 11. Current Blockers

### CE-0090: Missing Special Boss Slot

Targeted Stage-5 gate passed at `6fb9f9c`; subsequent complete Stage-4A and
Stage-5 runs physically exercised the generic lifecycle and issue-time
observation fixes. The special owner remains a TH08 adapter concern, not a
generic solver exception.

The authoritative owner pointer is `0x0057D2F0`, exactly one enemy stride
before the ordinary async pool base `0x005826C0`. The old “full enemy pool”
never scanned Reisen. Complete Stage-5 run `20260724_152719` retained 2,658
error-free synchronous owner observations, all outside the ordinary range;
2,640 were contact-enabled and 18 anticipatory.

The five old zero-projectile spell-115 hit coordinates lie inside the observed
boss rectangle `x=156..228, y=104..152`. After the correction, no zero-bullet
spell-115 row placed the player above `y=160`. The only spell-115 death was at
the bottom amid 1,145 bullets with negative modeled clearance.

This accepts the missing-owner correction, not overall survival. Total hits
changed `16 -> 21`, spell-107 hits `3 -> 9`, and every hit still followed
global viability-kernel exhaustion. Different RNG/respawn/Power histories
make the aggregate comparison non-causal. The subsequent Stage-4A control
supplied the required non-Stage-5 evidence and motivated a generic observation
fix, without any stage/spell-specific direction tuning.

The secondary latent-contact union and context-reset inertia rule remain
active. Item objectives are disabled during survival acceptance: pickups are
still measured, but item utility cannot prune or rank an action.

### CE-0089: Hard-Before-Soft Ordering

The corrected preflight ordering is active and passed Stage-5 physical
activation plus exact retained paired replay. Disabled/enabled reserve variants
keep identical hard counts while reducing boundary deficit. This accepts the
search-order invariant across stages; it does not claim that the 16-hit run is
a survival improvement.

### CE-0084..0086: Callback Motion Is Modeled, Survival Remains Open

The transform/runtime investigation is no longer the next implementation
slice. Native queue state was decoded, callback-driven stop/resume behavior
was separated from queued transforms, ECL callback lookahead was activated,
and sparse native piecewise hazards removed the thousand-bullet Python object
explosion.

Physical Stage-5 run `20260724_144805` validates callback activation,
lightweight trace retention, and the sparse native performance correction.
Do not reopen the old “read original flags” or dense Python materialization
tasks. Survival remains open through CE-0098 global-kernel exhaustion.

### CE-0083: Coarse Policy Phase Mismatch

Priority 2 after CE-0082/0098 survival-horizon work.

At Stage-2 frame 17,480, policy age 30 selected layer 3. The layer represents
age 24, so its certificate was six physical frames behind. A newer policy
arrived at frame 17,483 already empty; contact followed eight frames later.

Current partial corrections:

- worker submission interval reduced from 24 to 8 frames;
- every async policy solves full delay support `{1..6}`;
- phase telemetry records `age % frames_per_layer`;
- the cached action mask is always intersected with the fresh local
  delay-plus-hold certificate;
- a separate longer-terminal-horizon retry remains an opt-in experiment and
  is disabled.

Why it remains open:

- `floor(age / 8)` treats all phases inside a layer as equivalent;
- Stage 5 query offsets are roughly uniform across 0..7, so this is normal,
  not a rare boundary;
- dropping the mask and replanning locally nearly doubled work and had
  inconsistent Stage-4A/6B terminal-collision effects.

Required direction:

- phase-indexed occupancy/reachability; or
- conservative residual-frame propagation of the certificate before query.

Preserve `exists action, forall delay` and every intermediate collision check.
Do not choose a Stage-2-specific escape direction.

### CE-0082/0098: Empty-Kernel Recovery Is Not Path-Reachable

This is now the highest-priority planning defect.

Boundary control reserve is still an endpoint heuristic. It does not prove a
collision-free bridge back to the viable set. Stage 6B had 5,518 empty kernels
and 24 kernel-exhausted hit windows despite policy availability and complete
delay-support coverage. The strict Stage-5 cross-control added
4,514/7,054 empty queries and 26/28 kernel-exhausted hit windows; spell 107
alone had 635/769 empty queries.

Read `notes/VERSIONED_REACH_AVOID_ARCHITECTURE.md` before changing this layer.
On the same exact graph, a collision-free robust bridge into the future kernel
would already make its predecessor viable. Endpoint distance therefore cannot
be promoted into a survival certificate. The retained scalar oracle instead
maximizes guaranteed safe physical frames, then bottleneck clearance. Its
next step is an adaptive/refined native policy, not another recovery weight.

The `201636` differential has now separated the sampled cases. Exact
reconstruction matches 54/54 live results; three are proven 16-pixel spatial
false-empties and 51 remain losing at 4 pixels. Fused survival labels identify
one query where endpoint recovery chose outside the longest-survival mask.
Therefore the next correction is targeted boundary refinement plus a
survival-first losing-state action, not global 4-pixel induction and not a
single tuned distance weight.

The 2026-07-25 focused Stage-5 audit sharpens that result. Exact
reconstruction matched all 272 stratified queries; 195 were empty. Independent
single-factor ablations rescued 16 with 4-pixel refinement, 6 with current
delay support, 24 without uncertainty growth, 34 without retained
uncertainty, and 45 with at least one shorter horizon; the sets overlap and
147 had no tested single-factor rescue. Only frame 1,804 is a fresh canonical
hit. At decision 1,680, 126 frames earlier, the live fallback selected
`down_right_fast` outside the 74-frame survival-best mask and incurred a
24-pixel diagnostic reserve deficit because repair-volume guidance disabled
the old reserve term.

Offline survival-first replay changed 42/195 losing actions, raised
survival-best membership from 134 to 175, and caused zero fresh local
hard-vector regressions. Fused production is not live-ready: on 48 exact
capsules its whole-solve median/p95 was `125.31/229.58 ms` versus
`76.96/197.99 ms` for Boolean induction. A shadow sharing the publication
worker would still stale the authoritative policy. Keep both survival labels
and the new repair-state reserve switch default-off. Read
`notes/LOSING_STATE_ROOT_CAUSE_20260725.md`.

### CE-0087/0088: Compute Deadline And Optional Safety Value

The issue-time guard now suppresses expired new directions and invalidates
implausible `+1800` action epochs. Stage-3 physically exercised both paths,
but holding the older actuator command after a deadline miss is not a safe
fallback.

The exact max-min safety value is retained as an offline/opt-in oracle.
Stage-3 safety-value-on run `132007` added about 50 ms to global solves and
regressed live tail latency; default remains
`--safety-value-horizon 0`. Do not re-enable it without a measured compute
budget and paired physical A/B.

### Remaining Oracle Gaps

- Future ECL enemy births and projectile emissions are not yet injected into
  the committed-input horizon.
- Same-frame transform/emission ordering can still explain sensor-gap cases.
- It is not yet known how much of the 44.6-percent Stage-6B empty-kernel rate
  is true controllability loss versus quantization or conservative uncertainty.
  Calibrate stable same-slot residuals after excluding callbacks, phase
  boundaries, epoch jumps, and unmatched slots.
- Item/power objectives are disabled during the current survival acceptance
  phase. Passive collection remains observable but cannot affect decisions.
- Global solve p95 remains hundreds of milliseconds. Continue using C++ for
  compact numerical batches, but require whole-pipeline gain and oracle/action
  parity. A C++ decoder that reconstructs the same per-bullet Python objects
  is not a useful boundary.
- The old 4-pixel transition cache was a real native scaling defect:
  203,190,120 samples and roughly 1.514 GiB raw. Separable x/y caching reduces
  it to 4,119,984 samples and about 47.15 MiB with full scalar/NumPy parity.
  An isolated 4-pixel capsule solve now peaks at 94,080 KiB, but the complete
  offline audit still peaks near 1.27 GiB and requires separate profiling.
- Extra still has five unresolved native Bomb/Last-Spell replay boundaries;
  hard no-Bomb Lunatic practice remains the immediate diagnostic scope.

### CE-0092: During-Plan Enemy Spawn And Issue-Time Guard

The complete randomized Stage-4A run `20260724_155932` retained 19 hits and
zero Bomb input. At hit 35,419, the causal decision captured hazards at frame
35,412, an 18-body ring appeared in a frame-35,413 async snapshot, and the old
action issued at 35,415. Slot 18 made stable exact contact at frame 35,420.
This is a computation-window observation failure, not SendInput latency.

Every local decision now merges one synchronous 64-slot enemy prefix with the
complete async tail, then reads the prefix again before input. A manager-frame
crossing retries the contiguous read once. A pointer, contact-mode, size, or
aligned lethal-world-trajectory change triggers an all-action robust
recertificate. Five complete Stage-4A follow-ups and the strict Stage-5
cross-control physically exercise this path. Stage 5 recorded 2,307
recertificates and 870 action overrides; no stable hit capture had exact
enemy-body overlap.

The existing C++ moving-AABB clearance kernel now uses a cap-bounded
hazard-major traversal. A fixed 1,360-AABB workload improved `5.74x` by median
with an identical retained float32 volume checksum. Warm full synthetic solve
medians are `76.15 ms` Linux and `82.83 ms` Windows. This checkpoint supports
compact numerical C++ boundaries, not translating the full Python
orchestrator.

### CE-0093: Versioned Winning Actions And Survival Horizon

The earlier `36.217% global-empty/local-safe` statement compared different
questions. Local guaranteed only an 8--12-frame prefix; global required
another 48--80 frames. It is not false-empty evidence.

The original aligned failure was concrete: 30/6,613 selected actions were
inside the cached global winning set but contradicted by the fresh local tube
checker.
The global mask is now intersected with fresh prefix-safe actions; an empty
intersection triggers one rare all-17-action recertificate and relaxes the
cached version. Paired retained replay improved 10/30 hard vectors, regressed
zero, and changed robust-collision decisions `29 -> 23`. In the strict
Stage-5 cross-control, 1,474 observed newer issue versions were excluded and
zero of the remaining 3,753 selected cached actions contradicted the fresh
prefix checker. Version ordering is physically accepted; losing-state
recovery is not.

Outside the exact winning set, use no risk weight. The independent scalar game
maximizes guaranteed collision-free frames first and bottleneck signed
clearance second. It matches Boolean policy membership/masks. On 4,905 losing
generated states, margin-only fallback forfeited guaranteed frames on 190.
The adversarial generator now includes delayed births. Read the dedicated
architecture note before changing global/local contracts.

### CE-0094..0097: Hybrid Enemy Modes And Future Births

Contact-disabled and recently absent ordinary enemy slots are now retained for
the 80-frame policy horizon and reset by gameplay context. Planner motion is
estimated from consecutive lethal world positions at `+0x2D88`; internal
`+0x2D4C` motion is telemetry only. A rejected fixed 16-pixel widening
experiment is retained as run `183707`; do not revive it as a tuned margin.

Runs `173718`, `175647`, and `181700` causally isolate contact-mode and dormant
slot lifecycle. Corrected run `185059` then exposed two genuine bodies first
allocated four/five frames after the final issue observation. State-only
speedups cannot predict them. The next semantic adapter task is ECL/timeline
`BirthWindow` lowering for both enemy allocation and projectile emission.

## 12. Files To Read In Order

1. `AGENTS.md`
2. `START_HERE.md`
3. `notes/AUGMENTED_PIPELINE_ROBUST_CONTROL_FORMALIZATION_20260725.md`
4. `notes/BUDGETED_BELIEF_REFINEMENT_20260725.md`
5. `notes/BELIEF_PIPELINE_CORRECTNESS_AND_PERFORMANCE_20260725.md`
6. `notes/BOOLEAN_FIRST_PENDING_PIPELINE_20260725.md`
7. `notes/LOSING_STATE_ROOT_CAUSE_20260725.md`
8. `notes/VERSIONED_REACH_AVOID_ARCHITECTURE.md`
9. `notes/STAGE5_VIABILITY_DIFFERENTIAL_AUDIT_20260724.md`
10. `notes/ALGORITHM_REVIEW_20260724.md`
11. `notes/COUNTEREXAMPLES.md`, especially CE-0106..0114
12. `notes/RESEARCH_LOG.md`, latest five dated sections
13. `notes/ROBUST_VIABILITY.md`
14. `notes/SOLVER_MODEL.md`, especially Distant-Kernel Recovery
15. `notes/HAZARD_ORACLE_AND_ADAPTIVE_VIABILITY.md`
16. `notes/NATIVE_PLANNER_BACKEND.md`
17. `notes/DANMAKU_SYSTEM.md`, Transform Record and callback-motion sections
18. `scripts/touhou_control/query_survival.py`
19. `scripts/touhou_control/variable_cadence_oracle.py`
20. `scripts/analysis/audit_pipeline_formal_correctness.py`
21. `scripts/analysis/postpublished_survival_audit.py`
22. `scripts/analysis/viability_differential_audit.py`
23. `scripts/th08_live_dodge_agent.py`
24. `scripts/touhou_control/reachability_oracle.py`
25. `scripts/th08_bullet_transform_model.py`
26. `scripts/th08_corridor_adapter.py`
27. `scripts/touhou_control/viability.py`
28. Latest Stage-3, Stage-4A, Stage-5, and Stage-6B notes:
    `notes/runs/lunatic_route2_stage3_unattended_20260724_132007.md`,
    `notes/runs/lunatic_route2_stage4a_unattended_20260724_185059.md`,
    `notes/runs/lunatic_route2_stage5_unattended_20260725_125037.md`, and
    `notes/runs/lunatic_route2_stage6b_unattended_20260724_135201.md`

## 13. Common Traps Already Paid For

- Main-menu Practice Start is the fourth item, cursor 3.
- Sakuya/Remilia is the third team. Use Right twice.
- Do not accidentally enter Replay.
- Arm/prewarm before final Stage `Z`; otherwise the player can die before the
  planner starts.
- Auto-confirm requires a fresh Z edge: release then press. A continuously held
  Z does not advance every transition.
- At the post-stage save prompt, press Right once for no-save, then kill.
- Keep the hotkey daemon one-shot. A reused daemon once started a second run.
- Do not run two daemons; a named Windows mutex now prevents it.
- Do not merge gameplay frame epochs after a reset.
- Do not trust screenshots for bullets, lasers, hits, menu selection, or
  gameplay state when native memory is available.
- Do not interpret Bomb stock changes after death as Bomb input; audit input
  bit `0x02`, `decision.bomb`, and controller configuration.
- Clamp local movement exactly like native TH08; discarding out-of-bounds raw
  successors caused a `KeyError('stay')`.
- A coarse safe-action mask is not automatically invalid at an off-grid
  position. A margin certificate must pay live-to-lattice position error plus
  model error; otherwise preserve it only through the fresh continuous tube
  checker.
- Policy availability, delay-support coverage, kernel non-emptiness, and
  hazard correctness are separate gates.
- The last issued desired action is not the native active input. Preserve
  `input_current`, pending desired command, and remaining-delay support
  separately; do not repair CE-0109 by substituting observed input while
  dropping the pending branch.
- A planner selection is not necessarily an input issue. If the selected full
  mask equals the held desired mask, no key transition is sent and the old
  pending countdown continues. CE-0114 shows that inventing a new delay here
  flips winning classification.
- Hard survival ordering must hold during deduplication and beam truncation,
  not only final action selection. A soft recovery term can otherwise erase a
  safer first action.
- `--trace-transform-runtime` is a diagnostic cost switch. Default planning
  still retains a lightweight callback/tag/velocity-event payload; do not
  remove that evidence merely to improve decode timing.
- Faster Python/CFFI alone cannot fix a wrong hazard model. Native acceleration
  solved major viability/projection costs; policy phase, future emissions,
  uncertainty calibration, and path-reachable recovery remain semantic
  blockers.
- Move work to C++ at a packed numeric boundary. Reject micro-kernels that do
  not materially improve whole-decision/background p95 or that change actions
  without an accepted numeric contract.
- Do not weaken a strangely specific test. It is probably a retained death.

## 14. Definition Of The Next Good Checkpoint

A good next commit is not "the randomized stage had fewer hits" by itself. It
should:

1. Validate the compact root invariant
   `pending => held_desired=pending`, `no pending => held_desired=observed`
   against native multi-key transition traces. If intermediate key edges can
   remain independently in flight, expand the belief state; do not tune the
   one-pending model around the witness.
2. Replace the independent Cartesian cadence envelope with a bounded
   scheduler/workload automaton only after showing that it covers physical
   cadence traces and retains CE-0111. A trace predictor is evidence, not a
   hard timing contract.
3. Measure the implemented incumbent-seeded upper certificate on retained
   physical roots outside Stage 5. Refine only the unresolved actions/states
   whose proved upper can still beat the completed attainable lower label.
   Report certified actions and unresolved gaps at deadline; never publish
   unfinished optimistic labels.
4. Turn the existing physical-shadow evidence into a whole-pipeline CPU
   budget: belief solve/refinement, read, local plan, telemetry, action lag,
   stale work, and hits. Never block the issue-time thread on cold expansion
   or grant veto-only authority while background work worsens the clean
   controller.
5. Prototype a packed native issue-time bullet/laser/enemy
   decode-plus-project-plus-all-action certificate with a fixed service
   budget. It must preserve the strict version contract and improve
   whole-decision p95, not only a micro-kernel.
6. Add ECL/timeline `BirthWindow` coverage for enemy allocations and
   projectile emissions without putting TH08 details in the generic planner.
7. Make background planning anytime/cancellable and publish explicit source
   version, event coverage, delay support, terminal invariant, and expiry.
8. Keep CE-0100 refinement query-local or inside a reachable tube. Reproduce
   all three witnesses in shadow without increasing live expiry, missing
   queries, or local latency.
9. Use the now-validated Boss HP/phase sensor with the existing executable
   SHT/option/cadence model. Validate predicted versus native HP delta in
   shadow; do not restore the rejected Boss-x live proxy.
10. Audit instant-winning terminal states before claiming exact event-time
   layers.
11. Require randomized delayed-birth/stop/reverse/redirect parity, relevant
   platform/native tests, and whole-pipeline timing before physical use.
12. Use repeated fresh Stage-5 focused attempts and then a different stage
    for physical A/B. Retain every required artifact and counterexample while
    leaving raw traces, logs, native binaries, and `image.png` untracked.

## 15. Suggested First Prompt For A New Codex

```text
Work in /home/pentester/coding/codex_ida/th08. Read AGENTS.md and
START_HERE.md and STRATEGY.md completely, then inspect git status and the
latest commit. Keep hard no-Bomb; keep safety value, fused survival labels,
fine refinement shadow-only. Read
`notes/AUGMENTED_PIPELINE_ROBUST_CONTROL_FORMALIZATION_20260725.md` first and
audit every proposed solver against its state, observation partition,
uncertainty, and non-anticipativity contract. Engineering approximations are
allowed, but label their error direction and gates; same-recurrence C++/Python
parity is not proof that the physical problem is solved. Read
`notes/BELIEF_PIPELINE_CORRECTNESS_AND_PERFORMANCE_20260725.md` plus
CE-0111..0114. The legacy workspace is not a bound: it invents writes for
holds, fixes continuation cadence, and exposes hidden remaining delay. The
independent no-write belief oracle and C++ workspace pass 128 retained
scalar/native cases, but unrestricted TH08-shaped 32-frame continuation takes
about 1.51 seconds. All-root/focused-continuation is an attainable lower bound
at about 29.52 ms; recursive wide cadence remains outside budget. Validate
the held-desired/pending estimator invariant and design a verified cadence
automaton plus anytime lower/clairvoyant-upper refinement. Keep every legacy
prewarm and the new belief workspace shadow/offline; no physical trial is
authorized until offline bound gaps and whole-controller contention predict a
safe delivery budget. Continue the packed issue-time certificate
and ECL/timeline `BirthWindow` work; keep mechanics/safety game-neutral while
allowing explicit practiced profiles.
Retain compact artifacts and counterexamples, separate canonical attempts
from post-respawn discovery, use tiered relevant tests, commit verified
checkpoints, and stop every runtime session.
```
