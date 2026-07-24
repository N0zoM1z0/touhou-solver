# TH08 Agent Handoff

This is the operational handoff for continuing the TH08 Sakuya/Remilia
Lunatic/Extra no-Bomb solver. Read `AGENTS.md` first; its evidence, artifact,
test, physical-trial, and commit requirements are binding.

## 1. Exact Checkpoint

- Repository: `/home/pentester/coding/codex_ida/th08`
- Branch: `main`
- Handoff base commit: `8afc0d5 Keep asynchronous viability policies fresh`
- Complete Linux test gate at that commit: `312 tests`, all passing.
- The only expected untracked pre-existing file is `image.png`. It is a user
  screenshot. Do not add, delete, overwrite, or otherwise clean it.
- No transform-runtime implementation was left half-edited. The next change
  starts from a clean code checkpoint.
- The IDA database has newer metadata than Git: the transform functions listed
  in section 10 were renamed/commented after `8afc0d5`.
- The REA binary session used for the latest transform analysis was closed
  before this handoff.

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
PYTHONPATH=scripts python3 scripts/build_native_planner.py --target linux
PYTHONPATH=scripts python3 scripts/build_native_planner.py --target windows
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

Important execution detail:

- Use a non-TTY subprocess. A previous PTY launch blocked on a Windows console
  cursor-position query (`ESC[6n`) before the game appeared.
- With Codex `exec_command`, use a short initial yield (about 1 second). If a
  session ID is returned, poll it with `write_stdin` every 15-30 seconds.
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

Randomization guards against tuning only one spell. Focused Stage 5 is still
the next intentional gate because CE-0084 is a concrete transform-oracle
failure; random cross-stage regression follows that gate.

## 6. Monitoring, Stops, And Stalls

The supervisor prints records like:

```text
trial status: kind=decision frame=... stage=... spell=... hits=... bullets=... lasers=...
```

Inspect any growing trace explicitly:

```bash
trace=$(ls -1t artifacts/runtime_reports/*unattended*.jsonl | head -n1)
PYTHONPATH=scripts python3 scripts/th08_longrun_status.py "$trace"
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
5. Run focused tests, then the full suite.
6. Stage files explicitly. Never stage `image.png`, JSONL, launch logs, daemon
   logs, game files, binaries, credentials, or native build output.
7. Commit a focused, verified checkpoint.

Full test command:

```bash
PYTHONPATH=scripts python3 -m unittest discover -s tests -p 'test_*.py'
```

The command must include `PYTHONPATH=scripts`. Running bare unittest discovery
causes import errors for every script module; that is a test invocation error,
not a product regression.

Windows-focused test shell:

```bat
set PYTHONPATH=\\wsl.localhost\ubuntu\home\pentester\coding\codex_ida\th08\scripts
%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe -m unittest discover -s \\wsl.localhost\ubuntu\home\pentester\coding\codex_ida\th08\tests -p test_th08_live_dodge_agent.py
```

Before commit:

```bash
git diff --check
git status --short
git diff --stat
```

## 9. Current Physical Results

These are independent complete Practice runs, not one continuous route and not
same-seed A/B trials:

| Stage | Earlier complete baseline | Latest complete | Change |
| --- | ---: | ---: | ---: |
| 1 | 4 | 4 | unchanged |
| 2 | 2 | 3 | +1 regression |
| 3 | 7 | 11 | +4 regression |
| 4A | 27 | 19 | -8, 29.6% better |
| 5 | 24 | 15 | -9, 37.5% better |
| 6B | 30 | 18 | -12, 40.0% better |

The latest sum is 70 hits versus the selected earlier sum of 94, about 25.5%
better. This is useful directionally, but random pattern realization and
intervening changes prevent causal attribution from the aggregate alone.

Key accepted improvements:

- Phase-exact laser lifecycle and time-indexed segment geometry.
- Shared packed laser timeline across prefix/local/terminal/robust checks.
- Native game-neutral clearance and backward-viability kernels.
- `exists action, forall learned delay` robust control semantics.
- Adaptive delay/hold telemetry.
- Work-conserving async worker with the full configured delay support `{1..6}`.
- Certificate preservation at continuous off-grid/clamped states.
- Native-consistent local motion clamping.
- Delay-scaled boundary control reserve during empty-kernel recovery.
- Original-game unattended menu, monitor, dialogue, no-save, kill, and
  artifact loop.

Latest Stage 5 run:

- Run ID: `lunatic_route2_stage5_unattended_20260724_093713`
- Frames: `2..40607`
- Hits: 15
- Bomb input: zero
- Unique policies: 1,283 versus 626 in baseline
- Unsupported delay queries: 0 versus 148
- Decisions without policy query: 71 versus 201
- Solve median/p95: about 299/445 ms versus 291/422 ms
- Hits by phase, nonspell/103/107/111/115: `3/2/1/6/3`

Latest Stage 2 run:

- Run ID: `lunatic_route2_stage2_unattended_20260724_091120`
- Frames: `1..23129`
- Hits: 3, all nonspell
- Spells 16/20/24/28: zero hits
- The final hit is the canonical CE-0083 policy-phase witness.

## 10. IDA Pro MCP And REA

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

### REA

Read the installed `reverse-engineer-anything` skill before using REA. For a
native binary, open it, get the overview, request bounded function analysis,
cite Evidence IDs in durable notes, and close the binary session when done.
Do not repeat identical analysis calls merely to reread output.

Binary:

```text
/mnt/d/Entertainment/Game/Touhou/[th08] 东方永夜抄 (日文版)/th08.exe
```

Important Evidence IDs:

- Binary overview:
  `ev_907e44b397cc9bfc6e0d9f2579bdc22bd4b98e32cc8a36fc959b21f255159edf`
- Spawn/copy/queue initialization:
  `ev_7f655f7f0cb4948ce0753ef441b6bef7a3008601e345b6b8f40d40db44054338`
- Queue executor and stop setup:
  `ev_f80073c867ce14ae63fe52283dcfeeea322b83b3368b790fb539960fcd65ae2d`
- Stop-turn handler:
  `ev_cb4ea55181ccda8975025583d74b724906f398c642cb3cbfb4ab7e3935304de0`
- Stop-snap handler:
  `ev_32f2db8cee21ec27800551c2a308ed12c19f57c8d0593bf894f68bed4c59b37f`
- Stop-reaim handler:
  `ev_7cf3f4a46e21867c5be0c74c5188fd83f6b6843f6784f33a01f715e024fd34d5`
- Timer elapsed float/current/advance:
  `ev_8cd3b7f623c9bb779121d7d21491b3812bc30fcf9d5284100e63f9868c1050ae`,
  `ev_ba62f112b8bfb52df89711e970634c49babc138aaea9889f1e8dbe6fe05bd41e`,
  `ev_5c50a5e1604263f7141eb0013c3567acf78174ebb964cf6c66a5214889725ae9`

Tool feedback for later REA MCP improvement belongs in
`/tmp/rea_mcp_feedback.md`, not Git.

## 11. Current Blockers

### CE-0084: Live Bullet Transform Lifecycle

Priority 1.

Stage-5 spell 111, `懶惰「生神停止(マインドストッパー)」`, had
sensor-gap hits at frames 35,751, 36,607, and 36,980. Each observation had
exactly 96 bullets, no laser, and an oracle robust clearance of 24.6-30.8
pixels. The game still registered contact.

Root cause:

- `Bullet.transform_flags` currently reads only active flags at `+0xDAC`.
- The live oracle assumes `x + vx*t, y + vy*t`.
- Stopped bullets can have zero current velocity and zero current active flags
  while original transform state or queued work remains relevant.

Recovered runtime layout:

| Field | Offset |
| --- | ---: |
| speed | `+0xD68` |
| angle | `+0xD74` |
| active transform flags | `+0xDAC` |
| original transform flags | `+0xDB0` |
| bullet allocation state | `+0xDB8` |
| transform sound ID | `+0xDC8` |
| current queue index | `+0xDCC` |
| 18 x 24-byte transform records | `+0xDD0` |
| stop `Th08Timer` root | `+0x1004` |
| timer fractional elapsed | `+0x1008` |
| timer integer elapsed | `+0x100C` |
| stop resume speed | `+0x1010` |
| angle delta/offset/absolute angle | `+0x1014` |
| stop duration | `+0x1024` |
| repeat limit | `+0x1028` |
| repeat count | `+0x102C` |

Transform record:

```c
struct TransformRecord {
    float float_0;
    float float_1;
    int32_t int_0;
    int32_t int_1;
    uint32_t kind;
    uint32_t allow_while_active;
};
```

Next implementation slice:

1. Add runtime dataclasses and record parsing to
   `scripts/th08_bullet_transform_model.py`.
2. Extend `Bullet` and `decode_bullets` in
   `scripts/th08_live_dodge_agent.py` with original flags, queue cursor, next
   record, speed/angle, timer, duration, resume speed, angle operand, and
   repeat state.
3. Append these fields to nearby-bullet trace serialization without breaking
   the first eight legacy list fields used by dossiers.
4. First run a behavior-neutral Stage-5 capture and verify same-slot native
   transitions through stop, resume, and re-aim.
5. Implement exact per-frame projection for active 0x40 turn, 0x100 snap, and
   0x80 re-aim. Re-aim depends on the player's future state; represent the
   reachable target as an angle/trajectory envelope or candidate-dependent
   branch. Do not aim one guessed line at the current player and call it exact.
6. Keep unsupported concurrent transforms on a conservative fallback.
7. Feed the same lifecycle into local hazard frames and global corridor
   geometry. Avoid fixing only local MPC while the global certificate still
   sees a stationary bullet.
8. Add parser, stop/resume, repeat, pending-record, and re-aim uncertainty
   tests.
9. Re-run Stage 5. The focused acceptance question is whether the three
   spell-111 false-safe hits disappear without exploding empty kernels.

Do not simply replace active flags with original flags in the old uncertainty
formula. That would label completed transforms forever and may make the
global kernel useless.

### CE-0083: Coarse Policy Phase Mismatch

Priority 2 after the transform decoder/projection gate.

At Stage-2 frame 17,480, policy age 30 selected layer 3. The layer represents
age 24, so its certificate was six physical frames behind. A newer policy
arrived at frame 17,483 already empty; contact followed eight frames later.

Current partial corrections:

- worker submission interval reduced from 24 to 8 frames;
- every async policy solves full delay support `{1..6}`;
- phase telemetry records `age % frames_per_layer`;
- stale-mask local retry exists as an opt-in experiment but is disabled.

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

### CE-0082: Empty-Kernel Recovery Is Not Path-Reachable

Priority 3.

Boundary control reserve reduced Stage-4A and Stage-6B hits, but it is still an
endpoint heuristic. It does not prove a collision-free bridge back to the
viable set. The next recovery design should use backward-reachable recovery
bands or a robust bridge value with intermediate collision checks and control
reserve under every delay branch.

### Remaining Oracle Gaps

- Future ECL emissions are not yet injected into the committed-input horizon.
- Same-frame transform/emission ordering can still explain sensor-gap cases.
- Item/power objectives are present but cannot repair a missing survival
  certificate.
- Stage-3 dense-laser local p95 can still exceed the six-frame delay model,
  although laser lifecycle geometry itself is now phase-exact and shared.
- Extra still has five unresolved native Bomb/Last-Spell replay boundaries;
  hard no-Bomb Lunatic practice remains the immediate diagnostic scope.

## 12. Files To Read In Order

1. `AGENTS.md`
2. `START_HERE.md`
3. `notes/COUNTEREXAMPLES.md`, especially CE-0082..0084
4. `notes/RESEARCH_LOG.md`, latest three dated sections
5. `notes/HAZARD_ORACLE_AND_ADAPTIVE_VIABILITY.md`
6. `notes/ROBUST_VIABILITY.md`
7. `notes/NATIVE_PLANNER_BACKEND.md`
8. `notes/DANMAKU_SYSTEM.md`, Transform Record and Per-Frame Bullet Runtime
9. `scripts/th08_live_dodge_agent.py`
10. `scripts/th08_bullet_transform_model.py`
11. `scripts/th08_corridor_adapter.py`
12. `scripts/touhou_control/viability.py`
13. Latest Stage-2 and Stage-5 notes:
    `notes/runs/lunatic_route2_stage2_unattended_20260724_091120.md` and
    `notes/runs/lunatic_route2_stage5_unattended_20260724_093713.md`

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
  position. Preserve it only with the existing redundant continuous safety
  certificate.
- Policy availability, delay-support coverage, kernel non-emptiness, and
  hazard correctness are separate gates.
- Faster Python/CFFI alone cannot fix a wrong hazard model. Native acceleration
  solved most viability throughput; transformed bullets and policy phase are
  semantic blockers.
- Do not weaken a strangely specific test. It is probably a retained death.

## 14. Definition Of The Next Good Checkpoint

A good next commit is not "spell 111 has fewer hits" by itself. It should:

1. Decode and retain the native transform runtime without stage-specific data.
2. Have synthetic tests for stop/turn/snap/re-aim timing and queue behavior.
3. Show a same-slot physical differential trace matching native stop/resume.
4. Feed the lifecycle consistently to local and global hazard layers.
5. Pass the complete Linux suite and focused Windows tests.
6. Complete a hard-no-Bomb Stage-5 physical trial with compact artifacts.
7. Explain every changed spell-111 hit and any new empty-kernel behavior.
8. Add/update the counterexample and research notes.
9. Commit the verified checkpoint while leaving raw traces and `image.png`
   untracked.

After that, choose a random stage from `1 2 3 4a 5 6b`, run it physically, and
verify that the transform correction generalized instead of overfitting Stage
5.

## 15. Suggested First Prompt For A New Codex

```text
Work in /home/pentester/coding/codex_ida/th08. Read AGENTS.md and
START_HERE.md completely, then inspect git status and the latest commit. Keep
hard no-Bomb. Continue CE-0084 from the clean checkpoint: first add a
behavior-neutral live decoder/trace for bullet original flags, queue cursor,
next transform record, and stop timer/repeat state; test it; obtain a focused
Stage-5 physical differential trace; then implement a general stop/resume and
re-aim trajectory model in both local and global hazard layers. Do not
hardcode Stage 5 or spell 111. Use IDA MCP at localhost:13337 and cite REA
Evidence IDs already listed in START_HERE.md. Run full tests, retain every
physical artifact/counterexample, update notes, and commit verified
checkpoints. The user authorizes unattended launch/input/monitor/kill; use the
one-command supervisor and decisively clean up stalls.
```
