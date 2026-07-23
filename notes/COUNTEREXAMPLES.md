# TH08 Counterexample Ledger

This ledger preserves failures that changed the reverse-engineering model or
the live agent. A row is not complete until it points to reproducible evidence
or states exactly what evidence is still missing.

## Entry Template

```text
ID / date:
Observed symptom:
Invalid assumption:
Evidence or trace:
Root-cause class: world model | sensing/latency | planner | objective/resource | control/runtime
Correction:
Regression test:
Live verification:
Status: observed | inferred | unknown | fixed
```

## CE-0001: Menu navigation entered Replay

- **Observed symptom:** Automated menu input repeatedly selected Replay instead
  of starting a new game.
- **Invalid assumption:** The controller inferred menu position without first
  anchoring the main menu cursor and treated repeated input as harmless.
- **Evidence:** Direct user observation. `START` is the first/top main-menu
  entry for this executable.
- **Correction:** Menu automation must move to the top boundary before confirm,
  verify only menu state visually, and never use Replay for live-agent
  acceptance runs.
- **Status:** fixed operational rule; no in-game vision is used for dodging.

## CE-0002: Screenshot feedback is not a danmaku controller

- **Observed symptom:** Screen capture plus visual judgment had insufficient
  temporal and geometric precision for live bullet dodging.
- **Invalid assumption:** A human-scale screenshot loop could support frame-
  accurate movement decisions.
- **Correction:** Read native player, Bullet, Laser, Item, RNG, resource, and
  frame-counter state. Screenshots are limited to menu audits.
- **Status:** fixed architecture.

## CE-0003: Greedy constant-direction MPC enters future traps

- **Observed symptom:** Route-2 Lunatic movement looked locally good but still
  failed; the controller could not change direction inside its prediction
  horizon.
- **Invalid assumption:** Nine constant focused trajectories over 18 frames
  adequately represented the reachable safe set.
- **Evidence:** `artifacts/runtime_reports/lunatic_route2_live_dodge_120s.jsonl`
  and `lunatic_route2_live_dodge_emergency_bomb_120s.jsonl`.
- **Correction:** Time-expanded beam MPC with direction changes, exact Route-2
  focused/unfocused speeds, transform uncertainty, and read/action-lag
  projection.
- **Regression tests:** `test_incoming_bullet_forces_lateral_motion` and
  `test_fast_mode_is_available_for_urgent_escape`.
- **Status:** model fixed; live verification pending.

## CE-0004: Survival heuristic spent finite Bomb stock

- **Observed symptom:** The first live controller moved well but used Bombs on
  ordinary near-contact frames.
- **Invalid assumption:** Bomb was an ordinary geometric escape action rather
  than a run-level finite resource.
- **Evidence:** Bombs at frames 40047, 41731, 44147, and 45715 in
  `lunatic_route2_live_dodge_emergency_bomb_120s.jsonl`.
- **Correction:** Normal Bomb is disabled by default. Deathbomb is retained as
  a separately observed boundary action. Planner priority is survival, Bomb
  conservation, high-value item collection, then secondary score.
- **Status:** fixed policy; full-run resource-budget validation pending.

## CE-0005: Safe movement ignored Power and drops

- **Observed symptom:** A survival-only controller had no reason to collect
  Power, Bomb, life, or time items and therefore could create an unwinnable
  later resource state.
- **Invalid assumption:** Item collection could be added after trajectory
  planning as a cosmetic reward.
- **Correction:** Decode all 2,096 native item records, read run-state Power at
  `+0x98`, predict item motion, and reward items only when the candidate path's
  minimum clearance remains above the item-safety threshold.
- **Regression tests:** `test_safe_large_power_item_is_collected` and
  `test_unsafe_bomb_item_is_rejected`.
- **Status:** offline fixed; live verification pending.

## CE-0006: Full Python beam search created lethal control latency

- **Observed symptom:** Per-candidate Python collision loops took about 1.38 s
  for a synthetic 1,000-bullet field.
- **Invalid assumption:** A structurally better planner was automatically a
  better live controller without measuring its wall-clock delay.
- **Correction:** Vectorize per-frame hazard evaluation with NumPy, explicitly
  project snapshot lag, and use a 10-frame/24-node receding horizon. The same
  synthetic case is about 20 ms on the current WSL host.
- **Status:** fixed offline; Windows-host read plus planning latency pending.

## CE-0007: Foreground and human input invalidate physical control

- **Observed symptom:** Live control aborted when TH08 lost foreground or when
  physical input was already active.
- **Invalid assumption:** `SendInput` could safely coexist with an unobserved
  focus change or another controller.
- **Correction:** Fail closed on target identity, route, gameplay state,
  foreground ownership, and initial raw input; always release injected keys in
  `finally`.
- **Status:** fixed safety boundary.

## CE-0008: WSL-to-CMD quoting prevented the requested BAT from launching

- **Observed symptom:** No `th08.exe` process existed although a PTY-backed
  `cmd.exe` session remained alive. A later invocation reported the BAT as an
  unknown command.
- **Invalid assumption:** Backslash-escaped quotes inside a Bash single-quoted
  `cmd.exe /c` argument would become CMD grouping quotes. They remained literal
  `\"`; the UNC working directory also caused a CMD cwd fallback warning.
- **Evidence:** 2026-07-23 launcher output and process enumeration.
- **Correction:** Invoke from a Windows drive cwd and pass literal CMD grouping
  quotes without Bash backslash escaping; verify `th08.exe` exists before
  sending menu input or declaring the patch attached.
- **Status:** observed; corrected launch still to be verified.

## CE-0009: Item manager object was mistaken for a pointer

- **Observed symptom:** The live log reported `active_items=0` throughout a
  segment where Power increased from 0 to 8.
- **Invalid assumption:** `0x1653648` was treated as a global pointer to the
  item pool.
- **Evidence:** `ecl_cb_spawn_route_item` at `0x4253B2` executes
  `mov ecx, offset g_item_manager` before `item_pool_spawn`, not a dereference.
- **Correction:** Read the 2,096 records directly from object base `0x1653648`.
- **Status:** fixed in the sensor; live item-count/collection validation
  pending.

## CE-0010: The BAT patcher and planner use different Python environments

- **Observed symptom:** The first vectorized live-agent calibration exited
  before input with `ModuleNotFoundError: numpy`.
- **Invalid assumption:** Because the Windows `python` command had NumPy 1.26.4,
  the IDA-bundled Python 3.11 used by the BAT would also have it.
- **Evidence:** BAT interpreter
  `D:\Sec-Tools\Reverse\IDA Pro 9.3\python311\python.exe` lacks NumPy; Windows
  Store Python 3.12 has NumPy 1.26.4.
- **Correction:** Keep the minimal runtime patcher on IDA Python 3.11 and run
  the read-only/vectorized planner with the verified Python 3.12 interpreter.
- **Status:** fixed launcher procedure; dependency preflight still needs a
  dedicated command.

## CE-0011: A verified PID became stale before controller arming

- **Observed symptom:** The 30-second run failed at
  `QueryFullProcessImageNameW`; process enumeration immediately afterward found
  no `th08.exe`.
- **Invalid assumption:** The patched no-life-decrement process would remain a
  valid gameplay target during an unbounded analysis interval.
- **Correction:** Treat PID, image identity, foreground, gameplay flag, and
  route as a short-lived arming transaction. Start control immediately after
  route verification and fail closed on any stale handle.
- **Status:** fixed operational procedure.

## CE-0012: Frame 848 bottom-left corner trap

- **Observed symptom:** At frame 837 the old planner already predicted minimum
  horizon clearance 0.22, but it remained at `(8,432)` until frame 846 and was
  hit by slot 149 at frame 848. Deathbomb consumed two Bomb units.
- **Invalid assumption:** Minimizing summed danger before maximizing minimum
  clearance would retain a survivable corridor near a hard corner.
- **Evidence:** `lunatic_route2_resource_mpc_cegar_30s.jsonl`, frames 818..849.
  Greedy delta reduction preserves the bad `stay` action with only slots 142
  and 150.
- **Correction:** Rank collision-free paths by robust minimum-clearance deficit
  before aggregate danger/item utility; penalize hard-boundary occupancy.
- **Regression test:** `test_ce_frame_844_leaves_bottom_left_corner_early`.
- **Status:** fixed offline; live recurrence test pending.

## CE-0013: Frame 1426 bottom-edge reversal trap

- **Observed symptom:** At the bottom boundary, the old controller changed
  `left -> right_fast -> left` at frames 1420/1422/1424 and was hit by slot 605
  at frame 1426. The second deathbomb consumed the final Bomb.
- **Invalid assumption:** A tiny action-change penalty was enough to prevent
  receding-horizon direction oscillation.
- **Evidence:** `lunatic_route2_resource_mpc_cegar_30s.jsonl`, frames 1397..1431.
  Delta reduction preserves the bad `left` action with slots 598/605/607.
- **Correction:** Model one frame of actuator delay under the previous input,
  add opposite-direction hysteresis, and use the same robust minimum-clearance
  and boundary ordering as CE-0012. The earliest counterfactual divergence is
  frame 1420, where slot 605 alone is sufficient to select `right_fast` before
  the later trap forms.
- **Regression test:**
  `test_ce_frame_1420_commits_away_before_bottom_edge_trap`.
- **Status:** fixed offline; live recurrence test pending.

## CE-0014: Local-only MPC spends the Stage 1 Bomb budget

- **Observed symptom:** After CE-0012/13 reduced corner occupancy, the next
  30-second Lunatic run still hit at frames 1450 and 2558 and reduced Bomb
  stock from 3 to 0.
- **Invalid assumption:** A 10-frame controller could infer which safe-region
  component would remain connected after a later bullet wave.
- **Evidence:**
  `artifacts/runtime_reports/lunatic_route2_resource_mpc_cegar_fixed_30s.jsonl`.
- **Correction:** Add a game-neutral 80-frame time-expanded corridor layer.
  Its waypoint deadline is lexicographically prior to accumulated danger and
  item utility in the local MPC.
- **Regression tests:**
  `test_long_horizon_sees_gate_before_local_horizon_does` and
  `test_global_gate_deadline_forces_commitment_before_local_danger`.
- **Status:** architecture fixed; full Stage 1 live validation pending.

## CE-0015: Cold startup and unattended exit invalidated live trials

- **Observed symptom:** A nominally fresh trial did not emit its first decision
  until Stage frame 955. When its duration ended, injected keys were released
  but the unpaused game continued, so the player later died and stopped moving.
- **Invalid assumption:** Starting Windows Python/NumPy after confirming the
  team would be fast enough, and a released-input game was an unambiguous trial
  terminal state.
- **Evidence:**
  `artifacts/runtime_reports/lunatic_route2_corridor_cegar_30s.jsonl`.
- **Correction:** `th08_agent_hotkey.py` imports and warms the planner before
  gameplay. At the manually selected team page, F8 waits for `wait_ready` and
  then supplies the final confirm. A trial stops after its first hit plus 30
  trace frames and presses Escape on exit; F9 requests the same safe stop.
- **Status:** fixed and verified from Stage frame 1 in the first hotkey trial.

## CE-0016: Background corridor computation was mostly stale

- **Observed symptom:** The first live corridor trial had 652 corridor-tagged
  decisions, of which 410 used a result older than the 48-frame limit. Unique
  solve latency was 538 ms median and 1.59 s maximum.
- **Invalid assumption:** An asynchronous worker made an 8-pixel/4-frame grid
  affordable without measuring contention on the Windows host.
- **Correction:** Keep the tactical MPC per-frame, but coarsen only the
  topological layer to a 16-pixel grid and 8-frame layers over the same
  80-frame horizon. A 200-bullet Windows benchmark is now 41.9 ms median and
  43.0 ms maximum.
- **Status:** fixed and live-verified: zero stale corridor records in both
  hotkey trials, with solve medians 90.7 ms and 114.4 ms.

## CE-0017: Cross-shell launch quoting created ambiguous processes

- **Observed symptom:** Bash expanded PowerShell `$p`/`$existing` variables
  inside double-quoted `-Command` strings. One close-and-restart attempt left
  the old TH08 alive and launched a second process; one daemon wrapper then
  waited indefinitely on redirected output.
- **Invalid assumption:** Backslash escaping was sufficient across both Bash
  and PowerShell parsing layers.
- **Correction:** Use single-quoted PowerShell programs when variables are
  required, assert exactly one `th08.exe`, and separate a persistent daemon
  from its disposable launch wrapper. PID 15144 was verified alive after the
  wrapper was removed.
- **Status:** fixed operational rule.

## CE-0018: Registered F8 never reached the prewarmed daemon

- **Observed symptom:** Pressing F8 at the team-confirmation screen produced no
  log entry and no input even though the daemon process was alive.
- **Invalid assumption:** A background Windows process without the expected
  message-loop/window context would reliably receive `RegisterHotKey`
  notifications.
- **Correction:** Poll the F8/F9/F10 edges with `GetAsyncKeyState` at 10 ms,
  acknowledge `wait_ready` before the final Z, and validate route 2 plus the
  actual runtime difficulty again when gameplay becomes active.
- **Evidence:** The first corrected F8 trial controlled frames 1..3290 without
  a cold-start gap; the second controlled frames 188..5000.
- **Status:** fixed and physically verified.

## CE-0019: Snapshot-time actions were modeled as immediately effective

- **Observed symptom:** The first two prewarmed Lunatic runs improved survival
  to hits at frames 3259 and 4969, but still consumed a Last Spell at each hit.
  The first native witness is bullet slot 1136; the second is slot 471.
- **Invalid assumption:** Player state, the 6.6 MB bullet-pool read, the local
  plan, and injected input belonged to one frame, and one frame of previous
  input was enough to cover their delay.
- **Evidence:** Both trials have action-lag median 2 frames, P95 3, maximum 4.
  At frame 4963 the one-frame model reverses right into slot 471 while the
  delay-aware model keeps moving left. At frame 3254 the committed prefix
  already intersects slot 1136 even though the old next-action clearance was
  positive.
- **Correction:** Treat sensor and actuator time as part of the plant. Project
  the old player snapshot through a three-frame committed-input prefix, offset
  bullet prediction by the later bullet-read epoch, score hazards throughout
  the uncontrollable prefix, and advance corridor deadlines to the same
  actuation epoch. Trial reports now emit snapshot/action lag, first
  nonpositive pipeline clearance, and the nearest native hit witness.
- **Regression tests:**
  `test_ce_frame_3254_pipeline_detects_slot_1136_before_hit`,
  `test_ce_frame_4963_does_not_reverse_into_delayed_slot_471_path`, and
  `test_ce_frame_4969_slot_471_explains_native_hit`.
- **Status:** fixed offline; next physical F8 trial is the recurrence test.

## CE-0020: A same-frame native hit can be absent from both pool snapshots

- **Observed symptom:** The delay-aware trial ran from frame 1 to a native hit
  at frame 5016 with Power 46. The planner still reported pipeline clearance
  8.14; no laser was active, and the nearest bullet in the post-hit read had
  AABB clearance 14.12. The harness then used a deathbomb and stopped 30 frames
  later under the old first-hit policy.
- **Invalid assumption:** Reading the bullet pool before choosing an input
  captures every hazard that can collide later in that same game frame.
- **Static mechanism:** Enemy ECL/emission runs at priority 11 after the
  player update, while hostile bullet collision runs at priority 14. A bullet
  emitted after the controller's read can enter that same later scan; an exact
  hit removes its slot before the next controller read. This explains the
  observation gap but is not yet a runtime-identified hit slot.
- **Correction:** The report distinguishes the nearest observed bullet from an
  actual overlapping contact candidate. The F8 harness now retains all hits in
  a one-hour/F9-bounded long run. The real model fix is to merge executor/ECL
  predicted same-frame emissions into tactical hazards before input search.
- **Regression test:** `test_f8_long_run_does_not_stop_at_the_first_hit`; the
  existing update-order and hostile-pool tests pin the static mechanism.
- **Status:** open world-model counterexample; collecting recurrence evidence.

## CE-0021: Held Z did not advance dialogue and process exit lost the summary

- **Observed symptom:** The first no-life-decrement long run reached manager
  frame 9,429 but stopped producing normal combat observations after frame
  7,629. The final frame had no bullets, lasers, or items and still carried a
  stale corridor. Exiting TH08 then raised `ReadProcessMemory` error 299 before
  the live agent could append its summary.
- **Why it failed:** Continuous shooting leaves Z held. TH08 dialogue requires
  fresh confirm edges, so holding Z is not equivalent to repeatedly pressing
  it. The live loop also treated target-process disappearance as an uncaught
  I/O failure.
- **Correction:** After 20 consecutive empty-scene frames, alternate one-frame
  Z release/press edges every 15 frames. Any projectile, laser, item, or
  non-normal player phase resets the idle window, and a pending release is
  always restored first. Catch process-read failure, append a structured
  `runtime_error` plus a `process_unreadable` summary, and flush before closing.
- **Regression:** `test_auto_confirm_creates_fresh_z_edge_after_sustained_empty_scene`
  and `test_auto_confirm_combat_resets_idle_window_and_restores_z`.
- **Status:** unit-verified; pending the next full Lunatic physical run.

## CE-0022: One first-hit report is not a long-run death ledger

- **Observed symptom:** The old trial summary could explain only the first hit.
  A no-life-decrement run is specifically intended to retain every failure
  through all stages, so later counterexamples would have remained buried in
  the raw JSONL.
- **Correction:** Every native phase-2 edge now receives an independent
  240-frame analysis with resource state, player state, corridor deadline,
  pipeline clearance, nearest observed bullet, and active-laser count.
  Runtime traces also read `g_stage_route_index` at `0x0164D2CC`; reports group
  deaths and progress under the exact ECL stage resource index.
- **IDA persistence:** Renamed `dword_164D2CC` to `g_stage_route_index` and
  documented its exact `ecldata1` through `ecldata8` mapping at the
  `enemy_manager_init_stage` selection site.
- **Regression:** `test_every_hit_gets_a_stage_and_resource_ledger_entry`.
- **Status:** unit-verified; stage transitions await physical observation.
