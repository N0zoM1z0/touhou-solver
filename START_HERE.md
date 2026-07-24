# TH08 Agent Handoff

This is the operational handoff for continuing the TH08 Sakuya/Remilia
Lunatic/Extra no-Bomb solver. Read `AGENTS.md` first; its evidence, artifact,
test, physical-trial, and commit requirements are binding.

## 1. Exact Checkpoint

- Repository: `/home/pentester/coding/codex_ida/th08`
- Branch: `main`
- Handoff base commit:
  `66960dd Guard latent spell bodies across phase changes`
- Complete Linux and Windows test gates at that commit: `368 tests` each, all
  passing.
- The only expected untracked pre-existing file is `image.png`. It is a user
  screenshot. Do not add, delete, overwrite, or otherwise clean it.
- The latest 174 MB Stage-5 raw JSONL and its launch log remain local and
  ignored. Compact review/regression artifacts are committed.
- No runtime session or half-edited experiment is part of the checkpoint.
- The IDA database has newer metadata than Git: the transform functions listed
  in section 10 were renamed/commented during the callback investigation.
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

Randomization guards against tuning only one spell. CE-0089 has now been
cross-checked on Stage 5. The immediate CE-0090 owner-contact gate is one
focused Stage-5 run; follow it with a randomized stage from `1 2 3 4a 6b` so
the conservative owner union is not accepted only on Reisen.

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

| Stage | Latest run | Hits | Interpretation |
| --- | --- | ---: | --- |
| 1 | `070946` | 4 | default-policy control |
| 2 | `091120` | 3 | CE-0083 phase witness |
| 3 | `123136` | 8 | default safety-value-off cross-control |
| 3 | `132007` | 15 | rejected safety-value-on experiment |
| 4A | `084835` | 19 | boundary-reserve physical evidence |
| 5 | `144805` | 16 | piecewise performance pass; CE-0090 body witness |
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
- Native game-neutral clearance and backward-viability kernels.
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
- Original-game unattended menu, monitor, dialogue, no-save, kill, and
  artifact loop.

Latest Stage-5 evidence:

- Run ID: `lunatic_route2_stage5_unattended_20260724_144805`
- Frames: `2..39650`
- Hits: 16; Bomb input: zero; accepted completion: yes
- Local plan median/p95: `24.95/43.18 ms`
- Global solve median/p95: `304.07/485.81 ms`
- Available policy queries: 6,738; empty action sets: 3,139 (46.6 percent)
- Hit attribution: 15 global-kernel exhausted, one unresolved spell-owner
  contact candidate
- Stage-5 reserve replay disabled/enabled: 300-row hard counts `28/28`
  collisions and `45/45` negative certificates; 60-row pre-hit counts
  `18/18` and `24/24`.
- Spell-107 local-plan p95 changed `463.61 -> 50.44 ms` and cadence p95
  `37 -> 8`; spell 111 changed `142.72 -> 40.95 ms` and `13 -> 6`.
- Default traces retained 186,521/104,595 lightweight trajectory samples for
  spells 107/111, including 99,176/102,870 with velocity events. Full
  diagnostic queue objects remained off.

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

### CE-0090: Latent Spell-Owner Contact At A Context Boundary

Priority 1.

Five independent Stage-5 runs contain a spell-115 hit at upper-center
coordinates with zero bullets, zero lasers, and zero asynchronously sensed
bodies. The latest hit is frame 36,493 at `(184.49,120.69)`. Its hit-edge read
crossed two manager frames, so body contact is a strong repeated hypothesis,
not an exact native overlap witness.

The exact chain carried a pre-spell `up_fast` target into the new spell,
retained it with the old context's 24-point reversal penalty, and later added
residual-item approach potential. The adapter could not represent a spell
owner whose contact bit enables between the sparse body snapshot and actuator
pickup.

Correction at `66960dd`:

- synchronously read the active owner geometry window;
- lower the union of latent contact-disabled/enabled modes into both planners;
- retain contact/anticipatory telemetry;
- keep the old physical command in the committed delay prefix but drop its
  soft direction inertia when the stage/spell context changes;
- sharply reduce and saturate item approach influence.

Next physical gate:

1. Run Stage 5 once with hard no-Bomb and safety value disabled.
2. Verify `spell_enemy_body_guard` geometry plus observed/anticipatory mode.
3. Inspect the spell-115 entry transition and require no repeated
   zero-projectile upper-center contact.
4. Compare timing, empty kernels, item behavior, and every hit; a lower total
   hit count is not sufficient.
5. Then run a randomized non-Stage-5 control to detect over-conservatism.

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

Physical Stage-5 run `20260724_144805` now validates callback activation,
lightweight trace retention, and the sparse native performance correction.
Do not reopen the old “read original flags” or dense Python materialization
tasks. Survival remains open through global-kernel exhaustion and CE-0090.

### CE-0083: Coarse Policy Phase Mismatch

Priority 2 after CE-0090's physical gate.

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

Boundary control reserve is still an endpoint heuristic. It does not prove a
collision-free bridge back to the viable set. Stage 6B had 5,518 empty kernels
and 24 kernel-exhausted hit windows despite policy availability and complete
delay-support coverage.

Read `notes/ALGORITHM_REVIEW_20260724.md` before changing this layer. The next
candidate is a time-expanded min-max recovery band whose lexicographic cost
includes every intermediate collision/clearance violation, boundary control
loss, and terminal distance to the Boolean viability kernel. Build it first
against a small independent scalar oracle and multi-stage/adversarial replay.
Do not promote endpoint distance or centrality into a survival certificate.

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

- Future ECL emissions are not yet injected into the committed-input horizon.
- Same-frame transform/emission ordering can still explain sensor-gap cases.
- It is not yet known how much of the 44.6-percent Stage-6B empty-kernel rate
  is true controllability loss versus quantization or conservative uncertainty.
  Calibrate stable same-slot residuals after excluding callbacks, phase
  boundaries, epoch jumps, and unmatched slots.
- Item/power objectives are present but cannot repair a missing survival
  certificate.
- Global solve p95 remains hundreds of milliseconds. Continue using C++ for
  compact numerical batches, but require whole-pipeline gain and oracle/action
  parity. A C++ decoder that reconstructs the same per-bullet Python objects
  is not a useful boundary.
- Extra still has five unresolved native Bomb/Last-Spell replay boundaries;
  hard no-Bomb Lunatic practice remains the immediate diagnostic scope.

## 12. Files To Read In Order

1. `AGENTS.md`
2. `START_HERE.md`
3. `notes/ALGORITHM_REVIEW_20260724.md`
4. `notes/COUNTEREXAMPLES.md`, especially CE-0082..0090
5. `notes/RESEARCH_LOG.md`, latest four dated sections
6. `notes/ROBUST_VIABILITY.md`
7. `notes/SOLVER_MODEL.md`, especially Distant-Kernel Recovery
8. `notes/HAZARD_ORACLE_AND_ADAPTIVE_VIABILITY.md`
9. `notes/NATIVE_PLANNER_BACKEND.md`
10. `notes/DANMAKU_SYSTEM.md`, Transform Record and callback-motion sections
11. `scripts/th08_live_dodge_agent.py`
12. `scripts/th08_bullet_transform_model.py`
13. `scripts/th08_corridor_adapter.py`
14. `scripts/touhou_control/viability.py`
15. Latest Stage-3, Stage-5, and Stage-6B notes:
    `notes/runs/lunatic_route2_stage3_unattended_20260724_132007.md`,
    `notes/runs/lunatic_route2_stage5_unattended_20260724_144805.md`, and
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
  position. Preserve it only with the existing redundant continuous safety
  certificate.
- Policy availability, delay-support coverage, kernel non-emptiness, and
  hazard correctness are separate gates.
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

1. Run one focused Stage-5 physical trial with hard no-Bomb, safety value
   disabled, and the CE-0090 latent-owner guard active.
2. Retain the complete dossier, death ledger, regression cases, comparison,
   session/summary, and human-readable run note.
3. Verify owner geometry/mode telemetry and compact planning callback events.
4. Compare decode/local/global p50/p95, decision cadence, deadline suppression,
   robust hard-vector counts, kernel exhaustion, boundary occupancy, and every
   hit window.
5. Add a counterexample and smallest useful regression for every new concrete
   failure. Do not tune a stage/spell direction.
6. Pass the complete 368-plus Linux and Windows suites.
7. Commit the verified checkpoint while leaving raw traces, logs, native
   binaries, and `image.png` untracked.

After the Stage-5 gate, run one randomized non-Stage-5 control before
prototyping recovery-band semantics offline across multiple stages and
adversarial generated workloads. Do not introduce another C++ boundary until
profiling shows an end-to-end limiter and the independent oracle/action-parity
gate is defined.

## 15. Suggested First Prompt For A New Codex

```text
Work in /home/pentester/coding/codex_ida/th08. Read AGENTS.md and
START_HERE.md completely, then inspect git status and the latest commit. Keep
hard no-Bomb and leave safety value disabled. Continue from 66960dd: physically
validate CE-0090 on Stage 5. Verify synchronous spell-owner geometry and
observed/anticipatory contact mode, inspect the spell-115 entry transition,
and analyze every hit, empty-kernel state, item behavior, and timing—not only
aggregate hit count. Then run a randomized non-Stage-5 control before accepting
the conservative owner union. Keep generic planners game-neutral and TH08
memory/contact mechanics in the adapter. After those gates, investigate a
robust time-expanded recovery band with an independent scalar oracle and
adversarial generated cases. Use C++ only at a packed numerical boundary with
whole-pipeline performance and parity evidence. Run complete Linux and Windows
tests, retain compact artifacts/counterexamples, update notes, commit verified
checkpoints, and cleanly stop every runtime session.
```
