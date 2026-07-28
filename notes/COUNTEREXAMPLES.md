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

## CE-0023: Two hotkey daemons concurrently controlled one game and trace

- **Observed symptom:** The `13:14:07` trial contained concatenated JSON
  fragments, repeated frame numbers, conflicting decisions, and duplicate
  `agent armed` messages. Two controllers were also issuing physical input to
  the same PID, so neither movement nor timing was valid evidence.
- **Why it failed:** The old daemon was launched through `python.exe` but its
  running image name was `python3.12.exe`. Operational cleanup filtered for
  the alias name and left PID 27824 alive before starting PID 7716. Both saw
  the same F8 edge and chose the same second-resolution output name.
- **Containment:** Wrote the shared stop sentinel first so both controllers
  released keys and requested pause, then terminated both daemons and the
  contaminated game. The raw JSONL is retained only as invalid forensic
  evidence and must not enter solver regression results.
- **Correction:** `AgentHotkey` now owns the named Windows mutex
  `Local\Codex_TH08_Agent_Hotkey` for its entire lifetime and rejects any
  second instance before registering hotkeys. The streaming status tool also
  reports its JSON decode-error count instead of silently hiding corruption.
- **Regression:** `test_stream_loader_counts_corrupt_json_lines`; the named
  mutex requires physical Windows startup verification.
- **Status:** fixed and physically verified. A primary daemon retained the
  mutex, a second launch exited, and only one controller process remained.

## CE-0024: Frame-driven auto-confirm deadlocked on dialogue

- **Observed symptom:** The full Lunatic run stalled at sampled empty-scene
  frames 19,382, 27,728, 42,137, 68,117, 74,880, 128,708, and 151,701.
  The operator had to press Z for most dialogue transitions.
- **Invalid assumption:** A fresh Z edge scheduled by enemy-manager frame
  could advance a dialogue that itself freezes that frame counter. Requiring
  player phase 0 also excluded observed phase-3 transition scenes.
- **Correction:** While the counter is frozen, use wall-clock idle/interval
  thresholds, recheck gameplay and foreground ownership, exclude active Bomb,
  and issue one complete Z release/press edge. Phase 0 and 3 empty scenes are
  eligible, and a complete pulse cannot strand Z released.
- **Regression:** `test_auto_confirm_uses_wall_clock_when_game_frame_is_frozen`
  plus the existing fresh-edge/reset tests.
- **Status:** code-fixed; physical full-run verification pending.

## CE-0025: A frozen frame counter hid gameplay-scene unload

- **Observed symptom:** Final B combat ended at manager frame 209,373 with
  engine flags `0x1AA10`, gameplay inactive, and resources unavailable. The
  controller kept waiting for frame advance until an external stop was written.
- **Invalid assumption:** Gameplay state needed checking only after the enemy
  manager counter changed.
- **Correction:** Poll `g_engine_flags` in the frozen-counter branch and end
  with `gameplay_ended` as soon as bit `0x04` clears. This same check runs
  before any wall-clock auto-confirm edge.
- **Status:** code-fixed; physical completion verification pending.

## CE-0026: The full trace could not attribute hits to exact spell cards

- **Observed symptom:** The route manifest identifies 37 reachable Lunatic
  Final-B spells, but every one of the 91 runtime hit edges remains
  spell-unresolved. Approximate `+1800` manager-counter jumps are not one-to-one
  with ECL opcode `0x94` and cannot substitute for the live spell ID.
- **Invalid assumption:** Stage, frame, and static phase markers would be
  sufficient to recover exact spell ownership after the run.
- **Correction:** Every observation and decision now records
  `g_spell_card_state` flags, enemy pointer, exact ID, and decoded Shift-JIS
  name. Active attribution is gated by flags bit `0x01`; stale ID/name bytes
  remain visible after finish. The `spell_card_start` and finish sites carry
  the same layout/lifetime comments in IDA.
- **Regression:** `test_decode_spell_state_exposes_active_id_and_shift_jis_name`
  and `test_decode_spell_state_rejects_truncated_prefix`.
- **Status:** recorder and IDA fixed; physical spell transition trace pending.

## CE-0027: An 80-frame corridor did not produce a run-level feasible route

- **Observed symptom:** The completed no-life-decrement Lunatic Final-B run
  produced 91 native phase-2 edges by stage: `2/4/13/21/22/29`. The agent
  requested 62 deathbombs and observed 98 Bomb units consumed after hit edges;
  Power fell to 19 at completion and reached 3 in Final B. These resources are
  replenished/recycled by patched death handling and are therefore impossible
  as a finite-stock acceptance route.
- **Invalid assumption:** Repeated coarse gate waypoints over an 80-frame
  horizon would approximate whole-phase topology well enough for global
  survival and resource planning.
- **Evidence:** `notes/runs/2026-07-23_lunatic_route2_final_b.md`,
  `artifacts/runtime_reports/lunatic_route2_fullrun_20260723.dossier.json`,
  `.deaths.csv`, and `.regressions.json`. Of 91 edges, 74 had a missed
  corridor deadline, 68 used fast movement, 32 were at a playfield boundary,
  and 19 occurred with active lasers. Exact finite-segment geometry proves 11
  laser contacts; five active-laser cases have no observed contact, while two
  more are already explained by the committed-input prefix and one by a bullet
  overlap. The densest recurrent clusters are five hits at Stage-3 frames
  66,537..67,877 and five at Final-B frames 187,413..189,223.
- **Correction:** First close exact laser, transform, and same-frame ECL
  emission gaps. Then make the global state a connected safe component across
  full spell/phase boundaries, with Bomb/Power/item state in the resource
  search; the local MPC must preserve that selected component instead of
  choosing a late waypoint.
- **Regression:** The companion JSON contains one retained witness for each
  native hit. `scripts/analysis/th08_fullrun_regression.py` now validates
  every case ID,
  classification witness, factor, resource field, and stage count. Cases remain
  separate until executor replay proves equivalent root causes.
- **Status:** corpus executable; full phase/resource solver correction open.

## CE-0028: Local clearance outranked an expiring global gate

- **Observed symptom:** The local node key sorted
  `(collision, safety_deficit, gate_deficit, ...)`. A minimal retained-gate
  fixture at `(192,400)` with a left gate at `(160,400)` chose `down_fast`: it
  gained local clearance but could no longer reach the gate by its deadline.
- **Invalid assumption:** Gate reachability could remain a lower-priority
  preference after the global layer had already selected a viable component.
- **Correction:** Sort collision first, then gate deficit, then local safety.
  The neutral corridor DP can now require the bottleneck gate to remain in a
  specified left/center/right component. The live async controller keeps that
  component through a fixed, non-rolling expiry; if a constrained solve proves
  it unreachable, the same worker computes an unconstrained fallback. Stage or
  live spell-ID changes clear the commitment and discard old-context results.
- **Regressions:**
  `test_gate_reachability_outranks_a_wider_local_dead_end`,
  `test_required_gate_lane_selects_a_stable_component`,
  `test_required_closed_gate_lane_fails_instead_of_switching`,
  `test_corridor_commitment_survives_replans_without_rolling_expiry`, and
  `test_corridor_commitment_resets_at_spell_context_boundary`.
- **Performance:** A synthetic 200-bullet WSL benchmark measured 26.6 ms
  median unconstrained and 26.5..27.9 ms for constrained lanes; gate filtering
  does not materially enlarge the DP.
- **Status:** offline fixed; physical Lunatic recurrence validation pending.

## CE-0029: A lane label aliased disconnected path branches

- **Observed symptom:** In the corrected-commitment Stage-1 run, frame 2358
  retained a `center` gate near x=264 with slack `+2.1269`. The next completed
  corridor at frame 2361 was also labelled `center`, but its waypoint jumped
  to approximately x=88 with slack `-12.2599`; the native hit edge followed at
  frame 2367.
- **Invalid assumption:** Left/center/right bottleneck labels uniquely identify
  the connected safe component selected by the global planner.
- **Evidence:**
  `notes/runs/2026-07-23_lunatic_route2_transition_guard_partials.md` and the
  retained `150027` compact report.
- **Required correction:** Give each time-expanded connected component a
  stable identity and retain a component/path certificate across replans.
  Lane can remain descriptive metadata, but cannot be the commitment key.
- **Status:** physical counterexample retained; component-identity solver fix
  open.

## CE-0030: A stage-resource unload was mistaken for route completion

- **Observed symptom:** Stage 1 ended at manager frame 20,587. The gameplay bit
  cleared transiently, the agent terminated as `gameplay_ended`, and its exit
  handler pressed Escape after Stage 2 became active. No controller remained
  to auto-confirm the following dialogue.
- **Invalid assumption:** Any single inactive `g_engine_flags & 0x04` sample is
  the final gameplay-scene unload.
- **Correction:** A pure scene guard records the last active stage and route-2
  successor. Non-final unloads wait up to 90 wall-clock seconds, release combat
  input, and issue foreground-gated complete Z pulses. A Final-B unload must be
  stable for five seconds before `route_complete`. The transition source is
  fixed at the last committed scene. TH08 was physically observed writing the
  next index before clearing gameplay (`0` became `1` before the Stage-1
  unload), so an active sample cannot commit an index change. A new identity is
  committed only at initial arm or after inactive-to-active resume. Thus an
  early Stage-5-to-Final-B index update cannot reclassify the transition as
  terminal.
- **Regressions:**
  `test_scene_guard_waits_for_nonfinal_stage_transition`,
  `test_scene_guard_does_not_reclassify_stage5_transition_as_final`,
  `test_scene_guard_requires_stable_final_unload`, and
  `test_scene_guard_reports_transition_timeout`.
- **Status:** ordering corrected after the `151557` physical boundary test;
  full-route acceptance pending.

## CE-0031: Frozen collectible items deadlocked auto-confirm

- **Observed symptom:** The stable-stage-identity run stopped advancing at
  Stage-2 frame 28,459. The last decision contained zero bullets, zero lasers,
  Bomb inactive, and eight items; the following probe observed the same frozen
  manager counter. No wall-clock auto-confirm record was emitted.
- **Invalid assumption:** A collectible item makes a fresh Z edge unsafe, or
  will continue updating during a dialogue that freezes the game timeline.
- **Correction:** Auto-confirm eligibility is now a pure hazard policy:
  player phase 0/3, Bomb inactive, and zero bullets/lasers. Items are
  deliberately not an input. The controller still waits 20 empty frames and
  requires foreground ownership before a complete release/press edge.
- **Evidence:**
  `notes/runs/2026-07-23_lunatic_route2_transition_guard_partials.md` and the
  tracked `152539` summary.
- **Regression:**
  `test_auto_confirm_hazard_policy_does_not_gate_on_residual_items`.
- **Status:** code-fixed; unattended full-route acceptance pending.

## CE-0032: Frozen bullets are not evolving hazards

- **Observed symptom:** The `153736` run stopped at Stage-3 frame 53,623 with
  189 bullets and 315 items. The game was foreground and responsive, but the
  manager counter and RNG call count remained fixed and no Z edge was emitted.
- **Invalid assumption:** A hazard snapshot remains dangerous for the purpose
  of a shot-key edge even after the game timeline itself has stopped.
- **Correction:** Keep the hazard-only predicate for frame-driven confirms.
  For the wall-clock frozen-counter path, ignore bullets, lasers, items, and
  player phase because none can evolve; only an active Bomb suppresses the
  complete shot-key release/press edge. Foreground ownership and the idle
  threshold remain mandatory.
- **Evidence:** The tracked `153736` summary and
  `notes/runs/2026-07-23_lunatic_route2_transition_guard_partials.md`.
- **Regression:** `test_frozen_auto_confirm_only_excludes_an_active_bomb`.
- **Status:** code-fixed; practice-stage physical verification pending.

## CE-0033: The projectile-only hazard set drove into an enemy body

- **Observed symptom:** The first authoritative hit of fresh Stage-3 no-Bomb
  practice occurred at frame 4,885 in spell 35 with player
  `(178.775,156)`, zero active bullets, zero lasers, and projectile pipeline
  clearance `9999`. The active spell owner pointer was `0x5826C0`.
- **Invalid assumption:** Bullets, lasers, and playfield bounds form a complete
  lethal-hazard set. Enemy sprite/body contact was absent from local MPC and
  corridor occupancy.
- **Static evidence:** Contact-enabled enemy flag `+0x3324 & 0x04` reaches
  `0x42CF7A`; `enemy_test_player_contact_at_position` scales size
  `enemy+0x2D70` by 1.5; `player_test_deadly_aabb_contact` compares
  `center +/- size/2` with the live player lethal rectangle and invokes
  `player_dead_handler`.
- **Correction:** The live adapter now captures the active spell owner's
  position, velocity, full contact size, contact/disable flags, and motion.
  It lowers the owner to a time-indexed AABB with half-extents
  `0.75 * contact_size` and feeds it to committed-prefix, local, and global
  planners. Trace rows retain the geometry and snapshot frame; hit edges also
  capture the native player rectangle and body geometry in one stable manager
  frame. CE-0059 now generalizes this sensor to all 480 fixed slots for
  nonspell and simultaneous-enemy contact.
- **Regression:** `LUN-S2-F4885-T1` in
  `lunatic_route2_stage3_practice_20260723_160344.regressions.json`, plus
  `test_projectile_free_active_spell_promotes_enemy_body_candidate`.
- **Status:** spell-owner path code-fixed and unit-tested. The `170433`
  physical rerun has zero active spell-35 hits and zero exact body overlaps
  across eight stable hit epochs containing an owner body. Full-pool code is
  complete under CE-0059; physical timing and contact acceptance are pending.

## CE-0034: Spell-50 corridor solutions arrived hundreds of frames stale

- **Observed symptom:** Spell 50 produced six hits from frames 25,115..26,700
  with 180-200 lasers and repeated bottom-boundary occupation. Its 32 unique
  asynchronous corridor solves took 895 ms median, 2.99 s p95, and 3.20 s
  maximum; result age was 193 frames p95. Hit-frame action lag reached
  8-11 frames in this cluster.
- **Invalid assumption:** A correct global corridor computed from an old
  snapshot remains actionable in a dense, rapidly changing laser pattern.
  Background computation hid wall-clock cost but did not preserve freshness.
- **Correction in progress:** Finite laser-segment fields in both local and
  global planners are vectorized. On the preserved frame-25,433 snapshot, the
  global component fell from 64.8 ms median to 32.7 ms median. This reduces
  cost but does not yet enforce a cooperative hard deadline, reject every
  over-age result, or certify a retained connected component.
- **Regressions:** The six spell-50 cases in the Stage-3 practice corpus must
  retain solve latency/age, action lag, laser geometry, and boundary factors.
  A future successful fresh run must compare first divergence rather than
  merging post-respawn hits.
- **Status:** physical freshness target met for this Stage-3 run: spell-50
  solve p95 fell from 2.99 s to 362 ms, age p95 from 193 to 27 frames, and
  stale solutions from eight to zero. Five spell-50 hits remain, so connected
  component viability and local control are still open.

## CE-0035: The MPC modeled a two-frame action but the live loop held it longer

- **Observed symptom:** The corrected Stage-3 run updates control every three
  frames median and four frames p95. In spell-50 hit windows the last input was
  commonly retained for four or five frames. The search expands a new action
  every `PLANNER_ACTION_HOLD=2` predicted frames.
- **Invalid assumption:** Snapshot-to-`SendInput` lag is the complete control
  delay. It omits how long the emitted mask remains active before the next
  planning iteration replaces it.
- **Correction:** Retain a rolling 120-sample operational decision-frame
  cadence. The live MPC uses its p90, clamped to 2..6 frames, as the candidate
  action hold. The initial live estimate is three. Trace rows record the
  chosen hold and complete timing components.
- **Regression:** `test_live_action_hold_tracks_recent_controller_cadence`.
  On persisted pre-hit hazard subsets, hold 4 changes five of ten first actions
  and reduces search time by reducing branch points.
- **Status:** physically supported. The `173245` run used hold 4 for 473 of
  645 active spell-50 decisions; spell-50 hits fell from five to one while its
  corridor solve time became slightly worse. Total hits fell from ten to eight.

## CE-0036: Immediate clearance selected terminal states with no repair space

- **Observed symptom:** During spell 50, bottom-eight-pixel occupancy is 83.1%
  in alive samples within 60 frames of a hit but 8.9% in other alive samples.
  Fast mode rises from 45.9% outside hit windows to 60.6% inside them.
- **Invalid assumption:** A coarse path with acceptable bottleneck clearance
  and boundary exposure remains robust even when its terminal cell has few
  safe successor directions.
- **Required correction:** Add a game-neutral terminal viability certificate:
  future reachable volume, safe-control count, or connected-component repair
  radius. The local controller must prefer a slightly narrower current path
  when it preserves materially more future control authority.
- **Regression:** The five spell-50 cases in the `170433` corpus retain player
  location, bottom occupancy, fast/focus state, hazard density, and plan age.
- **Status:** still open. Dynamic hold reduced spell-50 near-hit bottom
  occupancy from 83.1% to 52.4% and hits from five to one, but the remaining
  frame-25,665 hit occurred at y=423.2 with positive gate slack and 200 lasers.
  Scalar bottleneck/gate scoring still does not certify repair space.

## CE-0037: Decision cadence was mistaken for input actuation delay

- **Observed symptom:** The controller held each candidate for the measured
  three-to-four-frame decision cadence and also kept a fixed three-frame
  previous-input prefix. In the `173245` trace, however, 4,522 of 5,237
  unambiguous output transitions were visible in the next decision snapshot;
  the visible snapshot delta was one frame at median and p95.
- **Invalid assumption:** The time until the next decision replaces an input
  equals the time until a newly injected input begins affecting the game.
- **Correction:** Maintain independent rolling estimates. Action hold follows
  decision-frame deltas. The uncontrollable prefix follows the p90 of native
  snapshot-to-action lag, starts at two frames, and is clamped to `1..4`.
  Scene transitions clear both histories. Trace rows persist the selected
  delay and estimation sample count.
- **Regression:** `test_live_control_delay_tracks_recent_action_lag`.
- **Status:** rejected by the `180832` physical run. The scalar estimator used
  delay 2 for 6,505 of 8,878 decisions, but total hits rose from eight to
  eleven and spell-50 hits from one to three while corridor latency slightly
  improved. See CE-0039.

## CE-0038: The hit-row output was reported as the action that caused the hit

- **Observed symptom:** Death ledgers labelled a hit with the action computed
  after `phase_at_action` became 2. At frame 7,144 the active input was
  `up_right_fast`, while the report incorrectly displayed the newly issued
  focused `up_right`.
- **Invalid assumption:** Every field on one trace row belongs to one causal
  epoch. The live loop observes state, plans, detects phase 2, and only then
  sends the row's output.
- **Correction:** Practice dossiers retain `active_input_action`, the last
  alive decision, post-detection issued action, usable warning lead, physical
  contact class, and planner-failure class separately. Fast-mode regression
  checks now use active input.
- **Regressions:** `test_active_input_action_is_independent_of_post_hit_output`
  and `test_input_visibility_separates_actuation_from_hold`.
- **Status:** analysis pipeline fixed; the eight-case `173245` corpus passes.

## CE-0039: A scalar delay quantile is not a conservative plant model

- **Observed symptom:** The `180832` Stage-3 no-Bomb run used a rolling p90
  snapshot-to-action lag as one uncontrollable-prefix length. Relative to the
  accepted `173245` run, total hits regressed `8 -> 11` and spell-50 hits
  regressed `1 -> 3`. Only one hit had action lag above the chosen scalar.
- **Invalid assumption:** Replacing an uncertain actuation delay with its p90
  value is conservative. Input timing changes the player trajectory: an action
  safe when it starts after two frames can be unsafe when it starts after one
  or three. Delay is a discrete plant uncertainty, not a monotone safety
  margin. The measured `action_lag` also ends at SendInput issuance; it does
  not prove when TH08 sampled the new mask.
- **Correction:** Learn end-to-end `snapshot -> input_current` delay from live
  mask transitions, retain overwritten/unobserved transitions as censored,
  and maintain a bounded discrete support. A hit or support overrun temporarily
  expands its upper tail. The local MPC keeps one nominal long-horizon beam,
  then certifies its surviving first actions across every learned delay until
  the next command can physically take effect. Collision-free support is a
  hard gate; CVaR risk ranks unsafe alternatives.
- **Regressions:** `test_touhou_control_delay.py`,
  `test_multi_delay_certificate_covers_until_next_command_effect`, and
  `test_adaptive_delay_distribution_and_robust_overrides_are_retained`.
- **Status:** physically accepted as the new Stage-3 discovery baseline.
  Run `184741` reduced hits from eight to six and spell-50 hits from one to
  zero under hard no-Bomb. Median local planning rose from 13.7 to 18.2 ms,
  but no corridor result became stale.

## CE-0040: Robust validation waited for the action set to become empty

- **Observed symptom:** All six `184741` hits had a last-alive robust
  certificate with a predicted collision or negative robust clearance.
  Continuous action-set exhaustion began only 3..7 frames before contact.
  Five cases still had positive scalar prefix clearance, so the old failure
  taxonomy called them late collisions.
- **Invalid assumption:** It is sufficient to override the nominal action once
  that action becomes unsafe. At that time every first action surviving the
  nominal beam can already fail under some learned delay. Selecting the least
  bad member cannot recover a viable connected component.
- **Correction:** Added the game-neutral
  `touhou_control.viability` backward-reachability kernel. Its state includes
  current active action, lattice position, and control layer. It admits a next
  action only when every learned delay branch remains collision-free through
  each intermediate physical frame and reaches the next viability kernel.
  The worst-branch local state-action volume ranks admitted actions before
  waypoint, item, and positional preferences. The asynchronous worker retains
  the complete policy so live control can query its current age/position/input
  rather than following a stale representative path.
- **Regressions:** The six cases in
  `lunatic_route2_stage3_adaptive_delay_20260723_184741.regressions.json`
  retain robust support, last-alive certificate, exhaustion frame, and warning
  lead. Spell 46's three hits are the primary phase-specific cases.
- **Status:** code-complete and unit-tested, physical acceptance pending.
  Dossiers now separately classify
  `global_viability_kernel_exhausted_before_hit`, retain its warning lead, and
  continue to retain the old local
  `robust_action_set_exhausted_before_hit`. Spell 46 remains the first physical
  target.

## CE-0041: First observed input visibility is an interval, not a timestamp

- **Observed symptom:** The adaptive estimator spent 6,970 of 8,005 decisions
  in tail-guard mode and frequently expanded support through delay 6. It
  recorded 50 overruns and 486 overwritten/censored transitions while the
  controller cadence itself was 2..4 frames.
- **Invalid assumption:** The first decision snapshot whose `input_current`
  equals the issued mask is the exact pickup frame. The true pickup lies after
  the last mismatching observation and at or before the first match; sparse
  polling supplies an interval.
- **Correction required:** Retain lower/upper pickup bounds and fit a bounded
  discrete distribution under interval censoring. Use its calibrated support
  or tail probability in robust MPC instead of training on upper bounds as
  exact samples.
- **Status:** open. Current upper-bound treatment is conservative and produced
  a physical improvement, but its computation cost and tail calibration are
  not yet general enough for other machines or games.

## CE-0042: The backward policy normally arrived after its own horizon

- **Observed symptom:** The uninterrupted `194644` Lunatic Final-B run
  completed 69,092 hard-no-Bomb decisions with 90 native hit edges. Of 64,412
  robust-mode decisions, 63,653 had no usable policy query and only 563 were
  actually constrained by backward viability. The 1,064 unique solves took
  2,456/4,039/6,142 ms at median/p95/max; their first observed ages were
  152/259/3,899 frames against an 80-frame policy.
- **Invalid assumption:** An asynchronous result remains useful merely because
  the worker returns a complete policy. A policy whose hazard epoch is the
  observation frame has already expired when solve time exceeds its horizon.
  The old trace `stale` flag also only noticed a missing reachable waypoint,
  so 484 reported stale solutions understated the actual loss of guidance.
- **Correction:** The neutral async timing layer estimates solve-frame p90.
  A submission at snapshot `s` builds hazards for a future policy epoch
  `e = s + lead`, with an eight-frame intended overlap. Bullet, laser, and
  enemy uncertainty is grown through the forecast interval. Trace status now
  distinguishes `pending_future_epoch`, `queryable`, `expired`, and
  `outside_policy_horizon`. The daemon prewarms transition geometry before F8.
- **Performance correction:** Moving-AABB clearance is exact below its cap but
  scatters only into nearby lattice cells, grouped by conservative influence
  radius. Repair-space volume is still exact, but is computed lazily for live
  queried states instead of materialized for every state/action. A Windows
  1,500-AABB/250-laser/80-frame-forecast benchmark is 1,237 ms warm median,
  versus the physical run's 2,456 ms median before these changes.
- **Rejected optimization:** Combining all 17 active-action batches into one
  large NumPy operation improved WSL slightly but regressed Windows warm time
  from about 1,497 to 1,903 ms because of large temporary arrays and memory
  bandwidth. It was removed.
- **Regressions:** `test_sparse_aabb_volume_matches_dense_geometry_below_cap`,
  `test_repair_volume_is_computed_exactly_for_the_queried_state`,
  `test_future_policy_epoch_is_pending_then_queryable_then_expired`,
  `test_future_policy_does_not_replace_active_policy_before_epoch`, and
  `test_touhou_control_async_policy.py`.
- **Evidence:** The 90 individual cases remain executable in
  `lunatic_route2_fullrun_robust_viability_20260723_194644.regressions.json`;
  the complete death ledger and per-spell attribution are in the matching
  dossier and run note.
- **Status:** offline fixed; focused Stage 4A/Final-B physical validation is
  required. A single worker can still have a short coverage gap if a
  forecasted solve remains slower than the full policy horizon.

## CE-0043: Respawn Bomb stock reset was reported as Bomb use

- **Observed symptom:** The no-life patch allowed Bomb stock to fall by 44
  units across post-hit reset windows even though the controller requested
  zero deathbombs. The first dossier renderer labelled this as observed Bomb
  spend.
- **Invalid assumption:** A resource decrease after a hit proves a Bomb input.
  TH08 resets respawn stock independently of the injected input mask.
- **Correction:** Dossier v2 verifies no-Bomb from controller configuration,
  the native Bomb input bit, decision Bomb flag, and action name. The `194644`
  trace passes all four checks across all 69,092 decisions. Resource change is
  retained separately as `post_hit_bomb_stock_decrease`.
- **Regressions:** `test_no_bomb_verification_uses_input_not_stock_reset` and
  `test_no_bomb_verification_rejects_bomb_input_bit`.
- **Status:** reporting fixed. The run is a verified hard-no-Bomb failure
  corpus, not a finite-resource Bomb route.

## CE-0044: A future epoch did not make a slow serial worker continuous

- **Observed symptom:** Focused Final B run `20260723_213126` produced 292
  future-epoch policies and 8,454 policy queries, a large delivery improvement
  over the complete-run Final B baseline's 80 queries. It still recorded
  8,834 expired policy decisions. Solve time was
  1,957/2,915/3,268 ms median/p95/max against an 80-frame horizon.
- **Invalid assumption:** Forecasting a policy source near its expected solve
  completion is sufficient for continuous rolling control. A serial worker
  whose solve interval exceeds the horizon necessarily leaves a coverage gap,
  even when each individual result is fresh at first use.
- **Consequences:** Only 3,017 of 19,289 decisions were constrained. Of 8,454
  queries, 4,260 had an empty action set and 2,409 no longer covered the
  current delay support. Spell 162 was empty for 518/552 queries; spell 166
  was empty for 357/452 and spent 65.3% of alive decisions in the bottom eight
  pixels. The run retained 25 hard-no-Bomb hit witnesses.
- **Correction:** Added a game-neutral native C ABI for hazard clearance
  volume and robust backward DP, with NumPy as the reference fallback.
  Randomized parity retains the exact `exists action, forall delay` contract.
  The generic async layer now reports p90 solve frames, serial coverage margin,
  and serviceability. Policy submissions use a bounded one-frame delay-support
  envelope to tolerate estimator drift during a solve.
- **Performance evidence:** On Windows, the retained 1,500-AABB/250-segment
  workload fell from 1,501.9 ms to 540.2 ms warm median. Full delay support
  `1..6` measured 511.4 ms median and 561.4 ms maximum, about 31..34 physical
  frames. Native and reference geometry/viability tests pass on both Windows
  and WSL.
- **Regressions:** `test_native_kernel_matches_numpy_for_randomized_delay_game`,
  `test_native_time_volume_matches_numpy_mixed_hazards`,
  `test_serial_serviceability_requires_solve_inside_horizon`, and
  `test_delay_envelope_covers_one_step_estimator_drift`.
- **Status:** offline corrected, physical acceptance pending. The next focused
  Final B trial must demonstrate sustained queryable coverage and positive
  serial margin under actual game contention.

## CE-0045: A Final-B restart inherited the previous attempt's submit clock

- **Observed symptom:** The selected `222808` Final-B epoch restarted at frame
  zero but emitted no corridor record until frame 70,798. The first policy
  source was 70,925. Nonspells and spells 150 through 186 therefore ran only
  the local controller; only spell 190 exposed 575 policy decisions.
- **Invalid assumption:** Clearing a completed corridor solution at terminal
  unload resets asynchronous planning. `corridor_last_submit` remained near
  70k from the earlier attempt, so the new zero-based manager counter could
  not satisfy the next-submit interval until it caught up to the old value.
  Stage/spell context alone also cannot distinguish two attempts of the same
  thprac phase.
- **Correction:** Scene resume resets the submit timestamp to its initial
  sentinel, clears active and pending policies and the lane commitment, and
  increments `gameplay_epoch`. Async solution context now includes gameplay
  epoch, stage, and spell, so a running future completed after restart is
  discarded even when stage/spell match.
- **Regression:**
  `test_ce_0045_finalb_restart_discards_previous_gameplay_epoch_policy`.
  The practice dossier's `--frame-epoch last` regression separately ensures
  a restarted attempt is scoped with its transition event and earlier
  decisions excluded.
- **Status:** code-fixed and unit-verified; physical restart verification is
  pending. The selected 31-hit epoch is retained as a local-planner failure
  corpus, not native-policy acceptance evidence.

## CE-0046: Dense hazards hid the native DP's open-field worst case

- **Observed symptom:** The first retained benchmark reported about 25 ms in
  the native viability phase for 1,500 AABBs and 250 segments, yet the five
  late live Final-B solutions reported 4,027 ms median and 8,488 ms maximum
  inside the same phase.
- **Invalid assumption:** More hazards imply a harder backward-reachability
  workload. Dense synthetic hazards mark most states unsafe and trigger early
  exits. Sparse or open fields keep more state/action/delay branches alive and
  force the old kernel to recompute lattice rounding and sampling error inside
  every layer.
- **Correction:** Cache hazard-independent transition indices and sampling
  errors for every active action, selected action, delay, lattice state, and
  intermediate physical frame. The cache covers all delays in a layer, so a
  changing adaptive support does not rebuild it. The daemon prewarms this
  table before F8.
- **Performance evidence:** Post-correction Windows warm medians are 294 ms
  open, 184 ms for 600 AABBs/52 segments, and 446 ms for the retained
  1,500/250 dense load. The cold open solve is about 1.69 seconds and remains
  outside gameplay handoff.
- **Status:** semantic parity and synthetic serviceability pass; a fresh live
  trace must still prove positive serial margin under game contention.

## CE-0047: A continuously delivered policy can continuously report no escape

- **Observed symptom:** The clean focused Final-B trial `20260723_234414`
  completed frames `1..70295` with 37 hard-no-Bomb hit edges. The native
  worker produced 911 policies at 208/369/609 ms median/p95/max, exposed
  16,813 live queries, and held a positive 32-frame median serial coverage
  margin. Nevertheless, 8,292 queries had an empty action set and only 8,164
  decisions were actually constrained.
- **Retained failures:** All 37 frames
  `[1441, 2891, 12000, 12832, 13204, 18413, 18996, 19577, 20253, 20813,
  21199, 28834, 32563, 36322, 37079, 37380, 37909, 38281, 38854, 39158,
  44874, 45268, 45644, 46304, 46930, 47228, 50867, 51281, 52989, 53594,
  54020, 54495, 54962, 58300, 60870, 66806, 69692]` are executable in the
  matching regression artifact. Twenty-six follow global-kernel exhaustion,
  nine follow local robust-set exhaustion, and two lack a preceding alive
  sample.
- **Invalid assumption:** Making an 80-frame finite-horizon policy queryable
  is enough to make its guidance useful. Delivery and viability are separate
  gates. The live state can already be outside the returned kernel because
  the preceding finite-horizon choices preserve too little terminal repair
  space, future emissions and laser transitions are incomplete, or the
  projected state crosses the lattice/kernel boundary between policy epochs.
- **General evidence:** Pre-hit bottom-eight-pixel occupancy was 47.3% versus
  20.2% outside the 60-frame windows. Eighteen hits involved a playfield
  boundary. Spell 166 was empty on 1,043 of 1,131 queries; spells 162 and 170
  retained seven hits each.
- **Regression:**
  `lunatic_route2_finalb_policy_epoch_reset_20260723_234414.regressions.json`
  retains every hit window, warning lead, query state, delay support, contact
  geometry, and no-Bomb proof.
- **Status:** policy epoch reset and native throughput are physically
  accepted. Survival is not accepted. The next planner gate is preserving a
  nonempty controlled-invariant funnel, with explicit future-spawn/laser
  prediction and a conservative terminal safe set, before tuning item or
  graze objectives.

## CE-0048: A completed trial returned to an armed hotkey loop

- **Observed symptom:** After `234414` wrote `route_complete`, the same daemon
  later observed another F8 edge and started trace `235835` during active
  Final-B gameplay. It controlled frames `5311..8725` until F9 produced a safe
  external stop. No hit or Bomb occurred in that partial trace.
- **Invalid assumption:** Returning to the daemon's F8 polling loop after a
  trial is harmless. Any physical F8 event, thprac hotkey collision, or other
  process-level key edge can authorize a second trial without a fresh daemon
  boundary.
- **Correction:** The hotkey daemon is one-shot. Once an agent worker has
  started and is no longer alive, the polling loop exits and the existing
  `finally` path releases all injected keys. A new trial requires a new
  prewarmed daemon.
- **Regression:**
  `test_completed_trial_exits_before_a_second_f8_can_rearm`.
- **Status:** code-fixed and unit-tested. The next physical launch must show
  the daemon process exiting immediately after route completion or F9.

## CE-0049: An allocated warning laser became a full static lethal wall

- **Observed symptom:** Final-B trace `20260723_234414` returned empty robust
  action sets on 68.95, 84.17, 57.96, and 92.22 percent of queries in
  laser-heavy spells 154, 158, 162, and 166. The forecast used a median
  48-frame lead plus an 80-frame horizon.
- **Invalid assumption:** A nonzero laser allocation flag implies the current
  `tail..head` segment remains lethal throughout the forecast. The live
  decoder discarded phase, timer, gates, flags, speed, maximum length, and
  current width; lowering retained a static capsule and added `0.4` pixels of
  uncertainty per forecast/future frame.
- **Native evidence:** `bullet_manager_update` gates collision by phase and
  timer. Its active transverse half-extent is descriptor width/4 after the
  player helper's second division, while the live capsule uses width/2.
  Non-alpha warmup and fade also replace the longitudinal size with the
  width-ramp geometry. See IDA `0x00431C56`, `0x00431E5F`, `0x00432048`, and
  `0x0044A793`.
- **General correction:** Retain the complete runtime record and lower a
  time-indexed rotated rectangle through the native lifecycle. Future angle,
  origin, spawn, and fade mutations come from an executable ECL oracle.
  Spatial uncertainty is learned per predicted field/event rather than grown
  universally.
- **Regression required:** A retained native differential fixture must cover
  warning-before-enable, active, fade-before-disable, fade-after-disable, and
  both phase-fallthrough boundary calls. The coarse planner may not report a
  true empty set until 4/2-pixel refinement also finds none.
- **Status:** lifecycle-aware runtime decoding, local projection, and
  time-indexed corridor lowering are code-complete as of 2026-07-24. Physical
  differential acceptance on laser-heavy phases remains open.

## CE-0050: The patcher's Python could not import the planner

- **Observed symptom:** The first Windows `--help` validation of the unattended
  supervisor failed while importing `corridor_planner`: the IDA 9.3
  `python311` used by the patch BAT has no `numpy`.
- **Invalid assumption:** Because the BAT successfully runs the small memory
  patcher, the same interpreter is suitable for the native planner and live
  agent.
- **Correction:** The clickable wrapper uses the installed Windows Store
  Python alias under `%LOCALAPPDATA%` and performs `import numpy` before
  starting the supervisor. The original BAT continues to use IDA Python only
  for the dependency-free patcher.
- **Regression:**
  `test_ce_0050_wrapper_does_not_use_dependency_free_ida_python`.
- **Status:** wrapper and Windows `--help` validation pass; full physical menu
  and stage acceptance remain pending.

## CE-0051: Nested cmd quoting prevented the game from launching

- **Observed symptom:** Armed unattended Stage-1 session `20260724_005845`
  timed out after 25 seconds with no `th08.exe`. Its launch log reports the
  quoted BAT path as an unrecognized command; no gameplay input occurred.
- **Invalid assumption:** Passing `call "path with spaces"` as one argument to
  `cmd.exe /S /C` preserves the intended inner quoting. Python's Windows
  command-line quoting added another layer and `cmd` retained literal quotes
  around the command name.
- **Correction:** Launch argv is now `cmd.exe /d /c call <bat-path>`, with
  `call` and the path as separate arguments and no `/S`. The exact failed
  session manifest is retained.
- **Regression:**
  `test_ce_0051_patch_batch_path_is_not_nested_in_one_cmd_argument`.
- **Status:** code-fixed and unit-tested; fresh physical launch pending.

## CE-0052: Fresh practice launch does not default to Sakuya/Remilia

- **Observed symptom:** Armed unattended Stage-1 session `20260724_010112`
  reached menu validation with `difficulty=3 route=0`, then failed closed
  before the agent sent the final stage confirm.
- **Invalid assumption:** Sakuya/Remilia was already selected on a fresh team
  screen. It is the third entry; confirming the untouched cursor selected the
  first route.
- **Correction:** After accepting Lunatic, send `Right`, `Right`, `Z` to select
  the third Sakuya/Remilia team, then navigate the stage list.
- **Regression:**
  `test_ce_0052_fresh_team_menu_moves_to_third_sakuya_remilia`.
- **Status:** physically accepted by complete Stage-1 run `20260724_011933`.

## CE-0053: Team selection consumes the horizontal axis

- **Observed symptom:** Session `20260724_011433` reached interactive title
  mode 9, but two `Down` taps left the title cursor at zero.
- **Invalid assumption:** The third team entry used the vertical axis like the
  main, difficulty, and stage menus.
- **Native evidence:** `title_team_menu_update` calls helper `0x00470424`,
  which consumes Left/Right bits `0x40/0x80`. The vertical helper
  `0x0047030B` consumes Up/Down bits `0x10/0x20`.
- **Correction:** Menu navigation declares an axis per native mode. Team mode
  9 uses `Right`; modes 0, 8, and 11 use `Down`.
- **Regression:** The CE-0052 plan test requires `Right`, `Right`, `Z`.
- **Status:** physically accepted by complete Stage-1 run `20260724_011933`.

## CE-0054: Gameplay globals are stale before the final Practice confirm

- **Observed symptom:** Sessions `20260724_010506` and `20260724_010732` were
  rejected because pre-final validation read `g_difficulty_index=0`, even
  though the visible difficulty cursor was Lunatic.
- **Invalid assumption:** Gameplay globals mirror current title-menu cursors.
- **Native evidence:** Difficulty mode 8 stores its cursor at
  `g_title_difficulty_cursor`; team mode 9 commits only `g_player_route_id`.
  `title_practice_stage_menu_update` commits `g_difficulty_index` and
  `g_stage_route_index` only when the final stage `Z` is consumed at
  `0x0046B0A5`.
- **Correction:** Synchronize modes and cursors through
  `g_title_menu_manager`; validate gameplay globals only after final confirm.
- **Status:** physically accepted by complete Stage-1 run `20260724_011933`.

## CE-0055: Session target identity retained the pre-patch byte

- **Observed symptom:** Successful session `20260724_011933` reported runtime
  patch byte `0xFF` and `no_life_decrement=false`, while all four native hit
  edges left the life stock at eight.
- **Invalid assumption:** The identity captured when the process first
  appeared also represented its state after the patch wait completed.
- **Correction:** Re-run exact executable/hash/patch verification after the
  patch byte becomes zero and store that refreshed identity.
- **Status:** code-fixed and covered by the existing target verification gate;
  the next physical session must report patch byte zero.

## CE-0056: Empty viability queries discarded all global repair direction

- **Observed symptom:** Unattended Stage-3 run `20260724_013045` completed with
  11 hits and 4,304 empty queries out of 7,608 available. Seven hit windows
  were classified as global-kernel exhaustion. Once a query was empty, live
  control discarded the policy entirely and returned to local beam search.
- **Invalid assumption:** A policy that cannot certify a strictly safe action
  contains no useful information. Nearby successors may still lead back into
  the controlled-invariant region.
- **Correction:** For an empty action set, compute every action's minimum
  delay-branch viable neighborhood volume. Feed positive volumes to local MPC
  as soft recovery guidance after exact collision and clearance, without
  adding anything to `safe_actions`.
- **Regression:**
  `test_empty_kernel_exposes_soft_recovery_without_claiming_safety` and
  `test_empty_kernel_recovery_is_soft_not_a_hard_action_constraint`.
- **Acceptance gate:** A fresh randomized stage must report nonzero
  recovery-guided/selected query counts, preserve hard no-Bomb, and improve
  former hit-window warning or kernel occupancy without adding local
  collisions.

## CE-0057: Batched stage-menu taps wrapped past Final B

- **Observed symptom:** Unattended session `20260724_014341` requested Stage
  6B, sent seven queued Down taps, and observed cursor zero instead of seven.
  It failed closed before final confirmation.
- **Invalid assumption:** Every synthetic title-menu tap is consumed exactly
  once, so a precomputed modular tap count is sufficient.
- **Correction:** Send one direction edge, read native title mode/substate/
  cursor, and repeat until the requested cursor is observed. Bound the attempt
  count to three complete menu cycles and retain the visited cursor sequence
  when failing.
- **Status:** code-fixed and physically accepted by the immediately following
  Final-B launch `20260724_014545`.

## CE-0058: Soft recovery engaged but did not establish aggregate improvement

- **Observed symptom:** Final-B run `20260724_014545` completed with 42 hits
  and zero Bomb, versus 37 hits in baseline `20260723_234414`. It selected
  soft recovery on 810 empty-kernel decisions, yet still had 8,119 empty
  queries.
- **Measured separation:** Recovery selection occurred on 2.17 percent of
  alive decisions within 60 frames before a hit and 5.24 percent outside
  those windows. Bottom and fast-mode pre-hit occupancy improved, while
  nonpositive pipeline clearance and negative corridor slack worsened.
- **Conclusion:** This one physical run neither accepts nor causally rejects
  recovery. The dominant remaining defect is an invalid hazard oracle:
  allocated warning/fading lasers were still treated as static full-length
  capsules at twice their native active half-width.
- **Correction gate:** Preserve recovery as soft, never as a claimed safe
  action. Re-evaluate it only after the phase-exact laser model and adaptive
  lattice reduce false empty sets; compare repeated phase-level trials rather
  than one aggregate RNG-dependent hit count.

## CE-0059: Spell-owner sensing omitted lethal nonspell enemies

- **Observed symptom:** Unattended Stage-5 run `20260724_022420` completed
  with 20 hits and zero Bomb. Frames 6,810 and 10,993 were classified as
  `sensor_gap_or_unmodeled_hazard`: the nearest retained bullets had 43.60 and
  13.00 pixels of clearance, no laser was active, and no spell owner body was
  available.
- **Invalid assumption:** The active spell owner is the only enemy body that
  can contact the player. Native `enemy_manager_update` applies the contact
  path independently to every active slot, including nonspell stage enemies
  and simultaneous auxiliary enemies.
- **Native evidence:** `enemy_spawn_from_timeline` (`0x0042A4E0`) scans 480
  fixed slots beginning at `0x005826C0`, stride `0x53D0`.
  `enemy_manager_update` gates each slot with flags `+0x3324` before passing
  position `+0x2D88` and full contact size `+0x2D70` to the lethal AABB path.
- **Correction:** Capture the complete enemy pool in one contiguous read,
  decode every contact-enabled record, and feed all resulting moving AABBs to
  committed-prefix, local, and global planners. Stable hit-edge telemetry now
  also captures every contact body rather than only the spell owner.
- **Regression:** `test_full_enemy_pool_retains_nonspell_contact_slots`.
- **Acceptance gate:** A fresh physical run must report enemy-pool read cost,
  retain no new sensor-gap hit where an enabled body exists, and avoid a
  control-delay regression large enough to erase the geometry benefit.

## CE-0060: Synchronous full-pool sensing consumed the control budget

- **Observed symptom:** Stage-5 acceptance run `20260724_023923` reduced total
  hits from 20 to 18 and nonspell hits from 12 to 7, while capturing the first
  exact full-pool enemy-body overlap at frame 11,674. However, the 9.8 MiB pool
  read cost 13.97 ms mean by itself.
- **Measured regression:** Total read median rose from 11.10 to 24.91 ms,
  decision cadence p95 rose from four to five frames, and available policy
  queries fell 20 percent. The run still had two sensor gaps and cannot justify
  paying synchronous latency on every action.
- **Correction:** Move full-pool capture to a dedicated single-worker sensor.
  Live control never waits for it; the latest completed snapshot is projected
  by native velocity and inflated by `0.75 * age_frames`, capped at 16 pixels.
  Snapshot frame, age, and worker read cost remain visible in every trace.
- **Limitation:** A current-state scan cannot predict a body whose contact bit
  activates between snapshots. Frame 11,674 demonstrates such a same-frame
  activation; its prevention requires the ECL spawn/flag oracle rather than a
  faster memory scan.
- **Regression:**
  `test_async_enemy_snapshot_projects_age_with_bounded_uncertainty`.
- **Acceptance gate:** Restore pre-scan read/cadence distributions without
  losing full-pool body witnesses or introducing stale-body false corridors.
- **Status:** Accepted for timing by complete Stage-5 run
  `20260724_030420`: read median returned from 24.91 to 12.03 ms and cadence
  p95 from five to four frames. Operational sensor age was 11/19/25 frames at
  median/p95/max. The run's 24 hits do not establish survival improvement and
  keep the ECL future-hazard gate open.

## CE-0061: A killed latency experiment was labeled completed

- **Observed symptom:** Intentionally terminated partial Stage-5 run
  `20260724_025622` ended with `process_unreadable` at frame 3,303, but the
  supervisor wrote `status=completed`, attempted the post-stage no-save Right,
  and printed `completed iteration`.
- **Invalid assumption:** Any normally joined agent thread represents a
  completed Practice stage.
- **Correction:** Only `termination_reason=route_complete` is accepted.
  Process loss, external stop, timeout, and other endings are persisted as
  `status=discarded`, skip the no-save input, and retain compact artifacts.
- **Regression:**
  `test_killed_partial_is_not_accepted_as_completed_practice`.

## CE-0062: A discarded partial became the next comparison baseline

- **Observed symptom:** Complete Stage-5 run `20260724_030420` was initially
  compared with deliberately killed run `20260724_025622`, producing a
  meaningless 1-to-24 hit delta over 981 versus 10,428 decisions.
- **Invalid assumption:** The newest same-stage dossier is necessarily a valid
  completed baseline.
- **Correction:** Baseline discovery now requires a sibling session with
  `status=completed` and an accepted `route_complete` termination. Missing,
  malformed, failed, and discarded sessions are skipped.
- **Regression:**
  `test_comparison_skips_newer_discarded_partial`.
- **Physical correction:** The retained comparison for `20260724_030420` was
  regenerated against complete run `20260724_023923`; its valid hit delta is
  18 to 24, not 1 to 24.

## CE-0063: Native Practice navigation silently skipped locked stages

- **Observed symptom:** Original-game Final-A selection visited
  `[0,1,2,3,4,5,7,...]` and could never reach cursor 6.
- **Native evidence:** `title_practice_stage_menu_update` (`0x0046ADB0`)
  loads `g_practice_stage_availability_masks[18*route+difficulty]` at
  `0x0046AFCA` and skips every cursor whose bit is clear at `0x0046B006`.
  Runtime route-2 Lunatic state was `0x40AF`; low bits 4 and 6 are clear, so
  Stage 4B and Final A are locked while Final B remains selectable.
- **Correction:** Supervisor title telemetry now reads the native mask and
  fails immediately with `disabled`, rather than cycling three times and
  blaming input reachability. The global and locals are renamed/commented in
  IDA.
- **Regression:** `test_final_a_is_bit_six_of_native_practice_availability`.
- **Remaining route:** Cover locked rows through a legally unlocked save or
  the previously approved thprac focused path; do not write the cursor or mask
  to counterfeit original-menu acceptance.

## CE-0064: Contiguous enemy sensing paid for 9.1 MiB of unused slot data

- **Observed symptom:** Stage-4A retained bodies in 8,231 of 10,431 decisions,
  while its 9.8 MiB contiguous capture cost 17.71/28.04 ms median/p95 and left
  snapshots 11/20 frames old. Frame 32,976 collided with a helper missing from
  the seven-frame-old action snapshot.
- **Invalid assumption:** One large `ReadProcessMemory` call is necessarily
  cheaper than sparse reads across a fixed, mostly inactive pool.
- **Correction:** Read the four-byte flags of all 480 slots, then fetch the
  1,500-byte collision window only for enabled slots. A paused eight-body
  differential retained identical pointer sets in all 30 pairs and reduced
  median capture from 14.06 to 3.34 ms. The faster reader runs every four
  manager frames at approximately the old bandwidth duty cycle.
- **Regression:** `test_sparse_enemy_reader_fetches_only_contact_enabled_windows`.
- **Acceptance gate:** A complete Stage-4A rerun must retain p95 decision
  cadence, reduce operational snapshot age, and not introduce body-set decode
  discrepancies.

## CE-0065: Live progress hid every active spell

- **Observed symptom:** Supervisor status lines printed `spell=None`
  throughout Stage 4A even while native spell IDs 57, 61, 65, 69, and 73 were
  active.
- **Invalid assumption:** Decision traces store `spell_id` at the top level.
  Live decisions store the native state under `spell.spell_id`.
- **Correction:** Progress rendering accepts both report shapes and only shows
  the nested ID while its `active` flag is set.
- **Regression:** `test_progress_text_reads_nested_live_spell_state`.

## CE-0066: Faster sensing cannot predict a just-enabled enemy body

- **Observed symptom:** The four-frame sparse-sensor Stage-4A acceptance run
  still had 27 hits. Stable hit-edge reads found four exact enemy-body
  overlaps. At frames 8,806, 10,483, and 10,794, the colliding pointers were
  absent from the action snapshots even though snapshot age was only 4--6
  frames; frame 9,505's pointer was already visible.
- **Invalid assumption:** Reducing observation age is sufficient to make every
  native contact hazard available to the planner.
- **Correction:** Death evidence now retains whether the exact stable
  contact pointer existed in the action snapshot and reports
  `enemy_body_absent_from_action_snapshot` separately. Sparse sensing remains
  accepted as an observation optimization: operational age fell from
  11/20 to 5/8 frames median/p95, main-loop read p95 fell from 26.03 to
  15.32 ms, and decision cadence stayed 3/4 frames.
- **Regression:** `test_stable_hit_epoch_enemy_body_overlap_is_exact` covers
  both absent and present action-snapshot pointers.
- **Remaining correction:** Execute ECL far enough ahead to publish enemy
  spawn/contact-enable events into the hazard oracle before their native
  flags change. The visible frame-9,505 crowd remains a distinct
  viability-exhaustion failure.

## CE-0067: A fixed 48-frame future-policy lead hid a newly spawned bullet

- **Observed symptom:** Stage-2's canonical hit at frame 1,582 was bullet slot
  637. It was absent at the active policy's snapshot frame 1,498, appeared by
  frame 1,545, and hit 37 frames later. That policy targeted source frame
  1,546; the next one targeted 1,594, after the collision.
- **Invalid assumption:** A 48-frame minimum forecast lead remains necessary
  after the native viability kernel reduces solve latency. The run's rolling
  solve p90 was about 25 frames, so the fixed floor created a larger
  observation-to-policy blind interval than computation required.
- **Observed local fallback:** Ten-frame local MPC did not see the collision
  while it was avoidable. Its robust certificate first became intermittently
  unsafe at frame 1,557, and the retained contiguous warning began only 16
  frames before impact.
- **Correction:** TH08 now configures the game-neutral scheduler with a
  16-frame floor, derived from two viability layers and maximum
  control-delay-plus-hold. Cold start stays at 80; rolling p90, explicit
  eight-frame late-arrival overlap, and horizon serviceability remain active.
  Replaying 387 ordered Stage-2 solves changes median/p95 lead from 48/48 to
  16/18 frames.
- **Regression requirement:** A timing test must prove that a fast, warmed
  worker can reduce its lead below 48 frames without changing the conservative
  initial epoch or allowing the policy to exceed its horizon.
- **Status:** Physically accepted by Stage-2 differential `20260724_043310`.
  Lead median/p95 became 16/18, policy age became 13/26 instead of 25/46,
  unique policies rose 387 to 766, decisions without a query fell 139 to 50,
  expired decisions fell 23 to 11, cadence remained 3/4 frames, and hits fell
  8 to 5. ECL forecasting remains necessary for events inside even the
  reduced interval.

## CE-0068: Stale global repair volume preferred three clamped aliases

- **Observed symptom:** Candidate Stage-2 spell-20 hit at frame 13,517
  occurred at `(304.10, 429.64)`. From frame 13,487 onward, the global policy
  allowed only `stay`, `down`, and `down_fast`. At the bottom boundary these
  all clamp to essentially the same physical successor. The controller chose
  `stay` because its old-policy repair volume was largest, while bullet slot
  443 approached from above.
- **Invalid assumption:** Maximizing an asynchronous policy's repair volume is
  sufficient when the ten-frame local horizon reports no collision. The
  policy snapshot was older than the live hazard geometry, and three action
  labels did not provide three independent escape directions.
- **Evidence:** Slot 443 was already visible at frame 13,481 with stable
  velocity and hit 36 frames later. Local robust control did not become unsafe
  until frame 13,509, only eight frames before impact.
- **Correction:** Add a cheap extended terminal-threat rollout after the
  exact ten-frame beam. It must distinguish physically clamped aliases and
  prefer a beam path whose terminal continuation avoids a visible stable
  hazard before stale repair-volume and positional objectives. It remains a
  heuristic warning, not a viability certificate.
- **Regression:** `test_ce_stage2_frame_13517_terminal_threat_leaves_clamped_aliases`
  reduces the retained wave to six bullets. The ten-frame selector stays at
  the boundary; the 32-frame terminal warning chooses `left_fast`.
- **Performance gate:** The final boundary-degeneracy trigger activated on
  6/100 sampled Stage-2 decisions. An alternating-order Windows replay
  measured 11.01/19.81 ms without the extension and 10.48/21.51 ms with it
  at median/p95; the p95 cost is about 1.7 ms. Physical acceptance remains
  pending.

## CE-0069: Running terminal threat on every decision broke cadence

- **Observed symptom:** Always-on terminal threat run
  `stage4a/20260724_045225` still had 27 hits. Nonspell improved 16 to 12, but
  spell 73 regressed 1 to 4. Local planning rose from 21.36/38.78 to
  27.19/45.32 ms median/p95 and control cadence regressed from 3/4 to 3/5
  frames.
- **Invalid assumption:** A cheap 24-terminal-state rollout is cheap enough to
  execute on every live decision when dense bullets and up to 36 enemy bodies
  share the same hazard kernel.
- **Correction:** Trigger the extension only when at least one old global
  safe-action endpoint is clamped and multiple safe labels collapse to the
  same physical successor. This makes the gate depend on the transition
  model, rather than an arbitrary boundary-distance threshold.
- **Physical gate:** Random Stage-1 run `20260724_050922` activated the
  conditional warning on 97/4,850 decisions. Planning remained 22.04/40.61 ms
  median/p95 and cadence remained 3/4 frames, versus the rejected always-on
  Stage-4A cadence of 3/5. Total hits were unchanged at four; the gate accepts
  bounded runtime cost, not a hit-count improvement.
- **Status:** Always-on design rejected and retained. The boundary-conditional
  design is accepted as a narrowly scoped warning. Its four new Stage-1
  witnesses remain failures of global-kernel preservation, not evidence that
  the warning solves long-horizon planning.

## CE-0070: Coarse safe mask was treated as a continuous-state certificate

- **Observed symptom:** Stage-1 run `20260724_050922`, spell 9, reported
  `stay/down/down_fast` as globally safe at frame 19,811. The player was at
  `(366.322, 424.728)`, 9.636 pixels from the queried 16-pixel lattice point.
  All three actions stayed at or moved into the bottom clamp. Bullet slot 827
  was already visible and hit the unchanged position at frame 19,823.
- **Invalid assumption:** A safe-action mask proved at the nearest coarse
  lattice center is a hard certificate for the observed continuous position.
  The builder accounts for transition sampling error from lattice centers,
  but the live query did not account for its initial 9.636-pixel snap error.
- **Correction:** When allowed labels collapse under the actual clamped
  transition, retain their repair volumes as soft evidence but relax the hard
  mask. The exact local beam considers all physical first actions and applies
  the 32-frame terminal cross-check. Telemetry records
  `viability_constraint_relaxed`; this is a certificate downgrade, not a
  claim that the local result is robustly viable.
- **Regression:** The retained slot-827 test reproduces the old `stay` choice
  with the extension disabled. The corrected selector relaxes the mask and
  leaves `stay`. Replaying frames 19,811 through 19,820 also changes every
  repeated `stay`.
- **Performance gate:** On 68 dense Stage-1 samples, the gate activated 16
  times and changed 11 actions. Alternating Windows measurements were
  8.11/17.32 ms without and 8.76/16.24 ms with the correction at median/p95.
- **Physical gate:** Random Stage-2 run `20260724_052616` completed with two
  hits versus five in the prior adaptive-lead baseline. Nonspell improved
  four to zero and the original spell-20 failure improved one to zero while
  cadence remained 3/4 frames and planning remained 22.65/41.10 ms.
- **Status:** Physically accepted for clamped aliases. The run's two remaining
  failures expose singleton-mask and empty-kernel cases below.

## CE-0071: Off-grid singleton mask forced the player to wait for impact

- **Observed symptom:** Stage-2 run `20260724_052616`, spell 16, queried a
  coarse policy with 6.621 pixels of snap error at frame 8,228. Its only safe
  action was `stay`; visible bullet slot 866 then hit the stationary player at
  frame 8,243.
- **Invalid assumption:** A singleton mask has enough control redundancy to
  remain a hard constraint when the live continuous position differs from the
  lattice state where it was proved.
- **Correction:** An off-grid singleton joins clamped alias collapse as a
  certificate-downgrade trigger. Repair volume remains soft evidence while
  exact local geometry and the terminal cross-check consider all first
  actions.
- **Regression:** The minimized slot-866 case selects `stay` with the
  correction disabled and an escape action when enabled.
- **Performance risk:** A 200-row dense Stage-2 Windows replay activated on 71
  rows and changed 50 actions. Median/p95 planning rose from 10.08/18.01 to
  12.61/27.52 ms.
- **Physical performance gate:** Complete random Stage-6B run
  `20260724_060039` exercised 1,237 constraint downgrades while preserving
  3/5-frame median/p95 cadence and 21.15/55.15 ms local planning. This accepts
  the runtime-cost boundary, but the run is not an ablation and cannot assign
  its survival change to singleton downgrade.
- **Status:** Fixed and accepted for performance; survival effect remains
  unisolated.

## CE-0072: Representative viability rollout used a different tie rule

- **Observed symptom:** Random Stage-6B run `20260724_053742` aborted at frame
  34,506 with `viability rollout left its own backward kernel`.
- **Root cause:** Backward reachability and the native kernel project lattice
  endpoints with round-to-even. The representative waypoint rollout used
  `argmin(abs(axis-x))`, which always selected the lower cell on an exact
  midpoint. It could therefore query a different successor than the one
  certified by the action mask.
- **Correction:** `RobustViabilityPolicy.project_to_lattice` is now the single
  projection rule for queries and representative rollout. A residual rollout
  inconsistency degrades the waypoint plan to `reachable=False` while
  retaining its policy; it can no longer terminate live control.
- **Regressions:** Tests pin 8/24-pixel midpoint round-to-even behavior and
  prove an injected representative-rollout mismatch returns an unreachable
  plan instead of raising.
- **Artifact integrity:** The Stage-6B dossier explicitly records
  `runtime_error` and `accepted_completion=false`; its 24-hit truncated result
  must not be compared as a completed clear.
- **Physical gate:** Repeat Stage-6B run `20260724_060039` reached
  `route_complete` at frame 77,112 and exited through the no-save path without
  another exception. The retained failed run remains the regression witness.
- **Status:** Fixed and physically accepted.

## CE-0073: Dense laser phases collapse the control cadence

- **Observed symptom:** The truncated Stage-6B run reached 205--240 active
  lasers in spell 154. That phase accumulated ten hits, corridor solves rose
  to 1340/1863 ms median/p95, and the partial run's overall local planning and
  decision cadence reached 21.12/97.31 ms and 3/8 frames.
- **Invalid assumption:** Per-frame local and global laser geometry can scale
  linearly over every pool entry without spatial/temporal filtering.
- **Evidence boundary:** One hit has an exact observed laser overlap; ten are
  classified `active_laser_without_observed_overlap`. Collision geometry and
  sensor attribution therefore remain separate from the demonstrated
  performance failure.
- **Correction:** Local exact checks now reject laser segments whose
  conservative segment AABB cannot reach the current node volume. Local and
  global projection also share exact lifecycle geometry templates keyed
  independently of origin and angle. On retained frame 22,002, 215 lasers
  reduced to 19 lifecycle templates; cold projection fell from 372.13 to
  61.48 ms, a 6.05x isolated speedup.
- **Rejected attempt:** Fully materializing a vectorized trajectory-clearance
  volume took about 190 ms on the retained workload versus 168 ms for the
  existing native volume builder. Array construction and reduction outweighed
  the hoped-for batch gain, so that implementation was removed.
- **Physical gate:** Complete repeat `20260724_060039` lowered spell-154
  corridor solve from 1340/1863 to 936/1345 ms median/p95 and hits from ten to
  five relative to the matched pre-cache phase. Overall local-plan p95 fell
  from 97.31 to 55.15 ms and cadence p95 from eight to five frames.
- **Status:** Partially fixed. Template reuse and broad-phase culling are
  accepted, but 936-ms median spell-154 solves and five observed laser hits
  leave both global projection throughput and laser geometry fidelity open.

## CE-0074: Empty viability kernels had no global recovery direction

- **Observed symptom:** Stage-1 baseline `20260724_062416` lost its global
  viability kernel 109--239 frames before all four hits. Once the one-cell
  repair neighborhood was also empty, the 10-frame local beam oscillated near
  boundaries without any signal describing where the next viable region lay.
- **Invalid assumption:** A one-cell repair volume is sufficient soft guidance
  for every state outside the robust kernel.
- **Correction:** For each candidate action, query the next-layer viable set
  for that resulting active action and compute the maximum, over every delay
  branch, of the distance to its nearest viable lattice state. This distant
  recovery distance is soft: exact local collisions and clearance remain
  lexicographically prior, and the distance never claims robust safety.
- **Performance:** A synthetic 24-by-27, 17-action empty-kernel query costs
  about 1.30 ms on Linux. Physical Stage-1 bookkeeping p95 rose from 1.51 to
  4.20 ms after the corrected variant, while end-to-end cadence remained
  3/5 frames.
- **Cross-stage gate:** Stage-3 run `20260724_065029` selected distant
  recovery on 1,761 queries. Against the prior complete Stage-3 baseline,
  pre-laser hits changed from 11 to four, including zero hits in spells 38,
  42, and 46. Total hits fell from 11 to seven despite three new spell-50
  laser failures.
- **Status:** Physically accepted as general soft recovery. It does not solve
  states in which every action is already locally unsafe.

## CE-0075: Beam pruning discarded the best recovery action

- **Observed symptom:** Initial Stage-1 recovery trial `20260724_063701`
  reported at frame 2,512 that `down_left_fast` had a 32-pixel worst-branch
  recovery distance, but issued `up` at 81.58 pixels. The player was then
  driven into the upper-left pressure region and hit at frame 2,571.
- **Root cause:** Recovery distance participated only in final node selection.
  Intermediate beam deduplication and width pruning still used the old local
  key, so the better first action could disappear before final ranking.
- **Correction:** The same collision, gate, and safety priorities remain
  first, but recovery distance now precedes local risk/utility throughout
  deduplication and beam pruning as well as final selection.
- **Regression:** A minimized Stage-1 frame-2,512 contract with
  `beam_width=1` retains the lower-distance action. Exact local collision still
  overrides distant recovery in a separate test.
- **Physical gate:** Corrected Stage-1 run `20260724_064421` remained at four
  hits but changed spell 5 from three hits to zero and reduced 60-frame
  pre-hit bottom occupancy to 1.4 percent. The independent Stage-3 gate in
  CE-0074 supplies the cross-stage survival acceptance.
- **Status:** Fixed and physically accepted.

## CE-0076: Lifecycle caching did not remove global laser-volume scaling

- **Observed symptom:** Stage-3 spell 50 held 200 lasers. Corridor solve
  median/p95 reached 1255/1565 ms, action lag exceeded the model on 29 percent
  of alive decisions, and the phase produced three hits including two exact
  observed laser overlaps.
- **Invalid assumption:** Amortizing `step_laser` lifecycle projection would
  make dense laser policies control-rate. It removes repeated state-machine
  work, but the global clearance builder still applies every instantiated
  segment trajectory to every relevant time/grid slice.
- **Evidence boundary:** The older Stage-3 baseline reported zero hits and
  225/285-ms solves for this phase, but many controller/model changes separate
  the runs. The fresh trace establishes current throughput and geometry
  failures; it is not an isolated cache regression.
- **Correction:** The game-neutral native backend now accepts a frame-major
  flat sample array plus frame offsets. It updates the existing clearance
  volume in place. Each frame/segment is rasterized only over the finite
  lattice rectangle in which its exact Euclidean clearance could improve the
  current capped volume. `None`, appearing, disappearing, moving, zero-length,
  width, and uncertainty-growth semantics are unchanged.
- **Exactness gate:** A mixed AABB/static/trajectory regression compares every
  cell against the framewise scalar geometry, including finite lifecycle gaps
  and a degenerate segment. Linux and Windows both pass within `3e-5`.
- **Performance gate:** The original synthetic profile spent 780 of 832 ms in
  Python segment-field construction/reduction. Retained 200-trajectory
  benchmarks now measure clearance/whole-solve warm medians of 43.66/79.76 ms
  on Linux and 74.13/115.88 ms on Windows. This is a 10x-plus clearance-path
  improvement without reducing trajectory count or horizon.
- **Non-laser physical gate:** Random Stage-1 run `20260724_070946` completed
  with four hits and 3/4-frame cadence. Against `064421`, total hits remained
  four and global solve median changed 220.53 to 216.93 ms. This rejects a
  sparse-phase regression but cannot accept dense-laser survival.
- **Status:** Computational correction accepted; dense-laser physical
  acceptance is now complete. Stage-3 spell-50 solve median/p95 fell from
  1255/1565 to 263/333 ms and policy queries rose 243 to 301. Hits remained
  three, so throughput is fixed but survival is not.

## CE-0077: Distance to a viable endpoint did not prove a safe recovery bridge

- **Observed symptom:** Stage-1 run `20260724_070946` completed hard no-Bomb
  with hits at frames `[1444, 5430, 5863, 6938]`. Three followed global-kernel
  exhaustion and one exhausted the local robust action set. All four had
  negative modeled pipeline clearance, so these are planning failures rather
  than late unmodeled contacts.
- **Canonical witness:** Before frame 1,444, the queried global state was
  repeatedly outside the kernel. Distant recovery supplied endpoint distances
  as large as 32--158 pixels, while one-cell repair volumes appeared and
  disappeared. The issued action alternated across opposing directions near
  the lower-right boundary. The corridor gate became negative at frame 1,432,
  pipeline clearance became negative at 1,440, and contact followed at 1,444.
- **Invalid assumption:** Minimizing Euclidean distance from a one-step
  endpoint to any viable next-layer cell is enough to guide a collision-free
  return. It does not prove that a safe path connects the current state to
  that cell, and recomputing it under changing active actions can encourage
  chatter.
- **Correction gate:** Recovery outside the certified kernel needs a
  path-aware bridge value, such as backward reachability over an augmented
  recovery band or a robust minimum-cost path whose intermediate states obey
  the same delay branches. Add hysteresis only after the path objective is
  defined; action smoothing alone is not a safety proof.
- **Status:** Observed and retained. No stage-specific motion rule has been
  added.

## CE-0078: Exact state-backed lasers carried invented horizon drift

- **Observed symptom:** Although Stage-3 spell-50 laser head/origin/angle
  projection was deterministic, the global adapter expanded every exact
  lifecycle sample by another `0.08 * (forecast + frame)` pixels, capped at
  six. With 150--200 radial lasers this erased narrow corridors.
- **Differential evidence:** Across 33,230 same-allocation, same-phase native
  timer pairs, head/tail p99 error was zero. Only 13/10 pairs exceeded `1e-4`,
  with 2.5-pixel maxima at the excluded transition boundary; origin and angle
  error were identically zero. Full lifecycle thresholds and timer fraction
  are now retained for future cross-phase parity.
- **Counterfactual:** At retained frame 26,220, 150 lasers plus 12 nearby
  bullets changed from unreachable/zero safe actions to reachable/13 safe
  actions when only this unsupported growth was removed. Two later snapshots
  showed larger viable sets but one remained truly empty.
- **Correction:** Exact `LaserState` trajectories retain the measured
  per-record read uncertainty only. Unknown-state fallback lasers keep their
  conservative age and horizon inflation.
- **Physical gate:** Spell-50 empty queries fell 180 to 121 (33 percent) in
  run `20260724_073640`, while solve latency and three hits were unchanged.
  This accepts model calibration, not a survival improvement.
- **Status:** Fixed for same-phase geometry. Cross-phase collision-width
  differential is enabled by the extended trace schema and remains a fidelity
  gate.

## CE-0079: Synchronous local laser work consumed live game frames

- **Observed symptom:** In run `20260724_073640`, the frame-26,892 planner
  recomputed the same laser lifecycle three times for prefix, beam, terminal,
  and robust checks. It then rebuilt seven segment arrays in every hazard
  call. The decision took about 100 ms in game and its snapshot-to-action lag
  reached 14 frames, beyond the modeled maximum six; a laser hit followed.
- **Correction:** One exact timeline now covers the maximum required physical
  frame. Prefix, main beam, terminal warning, and robust certificates take
  slices from it. Each frame is packed once into segment arrays shared by
  every node/delay evaluation.
- **Equivalence gate:** The retained frame-26,892 decision remains `right`
  with identical pipeline, local, and robust clearance. Warm offline solve
  fell to 30.64 ms, and a regression requires exactly one lifecycle
  projection call.
- **Physical gate:** Run `20260724_075004` reduced spell-50 local plan
  median/p95 from 62.46/163.12 to 45.90/135.03 ms, cadence from 6/13 to 5/11
  frames, and over-model decisions from 103 to 87. Three hits remained.
- **Status:** Exact sharing accepted as a partial throughput correction.
  Synchronous tail latency still crosses the six-frame certificate and needs
  either a bounded safety shield or a faster lifecycle/bullet kernel.

## CE-0080: Certificate downgrade abandoned a still-safe global action

- **Observed symptom:** At Stage-3 frame 26,892, the global policy's sole safe
  action was `down_fast`. Off-grid singleton handling discarded the hard mask,
  local planning chose `right`, and an exact laser overlap occurred eight
  frames later. In another run, frame 26,928 similarly discarded sole-safe
  `stay`, selected `up`, and hit ten frames later.
- **Invalid assumption:** Any off-grid singleton or clamped alias invalidates
  the whole coarse action mask. The lattice certificate is not continuous,
  but a global action that also passes exact continuous prefix geometry is
  stronger evidence than an unrestricted local alternative.
- **Correction:** Degeneracy and relaxation are now separate. A partial
  clamped alias with a real unclamped motion remains constrained and receives
  the extended terminal warning. An off-grid singleton remains constrained
  only when its action has zero exact prefix collisions, nonnegative
  clearance under every current delay, and repair volume greater than one.
  A complete outward alias or a singleton without that redundant certificate
  is still downgraded.
- **Retained gate:** Frame 26,892 changes from unrestricted `right` to the
  globally certified `down_fast`; frame 27,216 remains inside its four-action
  mask. Frame 26,928 still relaxes because `stay` fails exact prefix geometry,
  proving that this is not unconditional trust in the coarse policy.
- **Regression:** The Stage-2 clamped-alias and unsafe singleton escapes remain
  intact, while a safe redundant singleton is required to keep `stay`.
- **Status:** Fixed in offline retained geometry. Stage-6B completed with the
  contract active; an isolated Stage-3 survival gate remains pending.

## CE-0081: Local beam rejected native-clamped successors and aborted

- **Observed symptom:** Automated Stage-6B run `20260724_081231` reached
  frame 22,801 and then terminated with `KeyError('stay')`. The final global
  mask allowed `down_left_fast` and `down_right_fast`, with repair volumes 10
  and 2, at `(351.77, 412.47)`.
- **Root cause:** Native TH08 motion and the robust certificate clamp each
  coordinate to the playfield. The local beam instead discarded a successor
  when either raw coordinate left the bounds. A held diagonal at the lower
  boundary eventually emptied the beam, installed the legacy neutral `stay`
  fallback, and then attempted to reuse a preflight certificate map that did
  not contain `stay`.
- **Correction:** Local successors now use the same per-axis clamp as the
  native movement model, terminal rollout, and robust certificate. Preflight
  certificates are reused only when their key domain covers every surviving
  first action.
- **Regression:** `test_boundary_clamps_allowed_action_without_neutral_fallback`
  reproduces the retained position, delay support, hold, mask, and repair
  volumes. The selected action remains in the global mask.
- **Physical gate:** Repeat `20260724_081952` crossed the abort frame and
  completed frames `2..75091`, hard no-Bomb, with automatic no-save exit.
- **Status:** Fixed and physically accepted as a lifecycle/control-model
  consistency correction.

## CE-0082: Empty-kernel recovery consumed boundary controllability

- **Observed symptom:** Complete Stage-6B run `20260724_081952` improved total
  hits from 30 to 18 versus the most recent complete baseline, but all 18 hit
  windows had exhausted the global viability kernel. Twelve occurred at a
  playfield boundary. Pre-hit bottom-eight-pixel occupancy rose from 30.4 to
  51.7 percent.
- **Canonical phase:** Spell 170 contributed six bullet-only hits. In each
  retained window the safe-action mask was empty and distant recovery ranked
  scalar distances to a next-layer viable slice while the player repeatedly
  reached `y=432`.
- **Invalid assumption:** A smaller endpoint-to-kernel distance is sufficient
  soft progress when the endpoint has lost control authority. At a clamped
  boundary, outward/stationary actions can look closer to a different
  action-indexed viable slice while preserving no robust bridge and reducing
  the speed available to the next command.
- **Correction gate:** Extend recovery from a scalar endpoint distance to a
  path-aware value that prices intermediate collision clearance and boundary
  control reserve under every delay branch. It must retain the previously
  accepted Stage-1/Stage-3 distant-recovery gains and cannot encode Stage-6B
  or spell-170 directions.
- **Implemented partial correction:** Empty-kernel candidates now carry a
  delay-scaled, axis-symmetric boundary control-reserve deficit. Ranking
  remains collision, terminal gate, and local-safety first; reserve is used
  only before scalar recovery distance. The diagnostic remains active when
  the behavior is ablated so paired retained-trace comparisons are exact.
- **Offline cross-stage gate:** On 200 retained recovery samples, median
  selected deficit changed from `11.62` to `0` on Stage 1, `15.26` to `0` on
  Stage 3, `18.38` to `0` on Stage 6B, and `10.39` to `0` on Stage 4A.
  Planning p95 was effectively unchanged. The Stage-4A pre-hit subset changed
  34 of 104 actions and reduced median deficit from `24` to `3.08`.
- **Physical gate:** Random Stage-4A run `20260724_084835` completed frames
  `2..43356`, hard no-Bomb, with 19 hits versus 27 in complete baseline
  `045225`. Pre-hit bottom occupancy fell from 40.5 to 23.2 percent. Spell 61
  became hitless; nonspell hits fell 12 to eight.
- **Residual:** Sixteen of 19 hit windows still had an exhausted global
  kernel, 11 involved a boundary, and pre-hit mean reserve deficit remained
  `3.654` versus `0.581` outside hit windows. Endpoint reserve does not prove
  an intermediate collision-free bridge.
- **Status:** Partial correction physically accepted. CE-0082 remains open
  for backward-reachable recovery bands and long-horizon path connectivity.

## CE-0083: A coarse policy layer was treated as phase-invariant

- **Observed symptom:** Complete Stage-2 run `20260724_091120` had three
  hard-no-Bomb hits. At frame 17,480 a policy sourced at frame 17,450 was
  queried at age 30. Integer division selected layer 3, whose geometry starts
  at age 24, so the certificate was six frames behind the physical state and
  allowed `left_fast`. A new policy arrived at frame 17,483 with an empty
  kernel; contact followed eight frames later.
- **Invalid assumption:** Every frame inside one eight-frame corridor layer
  has the same reachable state and hazard occupancy. The policy stores one
  lattice slice per layer, but a query at phase `age % frames_per_layer` is
  not equivalent to the layer boundary.
- **Immediate correction:** The rolling worker is work-conserving at one
  layer (eight frames) instead of waiting 24 frames, and every async solve
  covers the full configured delay support `{1..6}`. Query telemetry now
  retains the within-layer phase. This removes estimator-support drift and
  reduces stale-policy exposure but does not make a coarse layer phase-exact.
- **Physical evidence:** Stage 5 run `20260724_093713` had 8,010 available
  queries, zero unsupported-delay queries, and 1,283 unique policies. Its
  8,010 phase samples were spread across all offsets 0 through 7, proving
  phase mismatch is the normal case rather than a rare boundary condition.
- **Rejected shortcut:** Retrying local planning without the policy mask when
  current exact geometry contradicts it changed no sampled Stage-2/3 actions,
  changed 4/23 Stage-4A and 3/14 Stage-6B actions, and gave inconsistent
  terminal-collision results while nearly doubling local planning time. The
  implementation remains opt-in and is disabled in physical control.
- **Correction gate:** Add phase-indexed occupancy/reachability or advance a
  certificate conservatively through the residual frames. The replacement
  must preserve the existential-action/universal-delay quantifiers and cannot
  encode a Stage-2 direction.
- **Status:** Open.

## CE-0084: Spell-111 callback motion was misclassified as a queued transform

- **Observed symptom:** Stage-5 spell 111, `懶惰「生神停止
  (マインドストッパー)」`, produced sensor-gap hits at frames 35,751,
  36,607, and 36,980. Each snapshot contained exactly 96 active bullets and
  no laser; the linear oracle reported 24.6 to 30.8 pixels of robust
  clearance, while the native game registered contact. Nearby stopped bullets
  had zero velocity and `+0xDAC == 0`.
- **Invalid assumption:** The zero-velocity interval came from queued
  transform kind `0x40`, `0x80`, or `0x100`, and bullet `+0xDAC` merely hid
  that lifecycle. The transform layout itself is correct, but it is not the
  mechanism used by this card.
- **Native evidence:** Spawn copies 432 bytes of transform records to
  `+0xDD0`, stores original flags at `+0xDB0`, clears active flags, initializes
  `+0xDCC`, and invokes the queue executor. The stop handlers use timer
  elapsed `+0x100C`, duration `+0x1024`, resume speed `+0x1010`, angle
  parameter `+0x1014`, and repeat limit/count `+0x1028/+0x102C`.
- **Correction gate:** Retain the original flags, queue cursor, records, and
  runtime timer state in live snapshots and traces. Project current stop
  lifecycles exactly; represent future player-relative re-aim as a trajectory
  set or conservative envelope rather than one guessed line.
- **Implemented observation slice:** The live decoder now retains native
  speed/angle, original flags, the next unconsumed record selected by
  `+0xDCC`, and the stop timer/operand/repeat state. A ninth optional compact
  payload extends `nearby_bullets` without changing its eight legacy fields.
  Regression tests prove that neither local nor global projection consumes
  the new state yet.
- **Physical decoder gate:** Complete behavior-neutral Stage-5 run
  `20260724_103617` retained 159,692 spell-111 runtime samples, but the
  player-centered trace covered only 61.5 percent of the active pool at its
  median decision. All retained active flags were already zero, leaving no
  adjacent active-stop pair. This is evidence that the fields are readable,
  not stop/resume parity.
- **Diagnostic correction:** Full-pool runtime capture is now an explicit
  opt-in and records only transform-relevant bullets. A streaming compactor
  retains hashed coverage and same-slot flag/queue/timer/motion/angle/repeat
  transitions without adding full-pool cost to normal acceptance traces.
- **Rejected hypothesis:** Complete full-pool run `20260724_105457` retained
  189,877 spell-111 bullet samples at 100 percent pool coverage. Every active
  transform flag was zero, every original flag was `0x00100202`, every queue
  cursor was zero, and no queued stop record activated. Same-slot batches
  nevertheless stopped and resumed together. This rejects queued-transform
  projection as the spell-111 fix without invalidating the recovered
  transform model for patterns that actually use it.
- **Observed native mechanism:** ECL `ecldata5` sub 63 invokes enemy callback
  12 at local times 350 and 450, then opcode `0x04` jumps from time 710 back
  to 350. Callback 12 at `0x00424A20` toggles bullets whose `+0xDB0` tag bits
  intersect VM `+0x18`: phase `+0x1FC == 1` changes to zero, velocity becomes
  the VM callback angle/speed, and aux `+0x10B4` becomes one; the other branch
  restores the bullet's base angle/speed and phase one. This card supplies
  speed zero for the first toggle.
- **Physical callback differential:** Run `20260724_113250` retained 42,377
  nearby samples with `(phase=0, aux=1, velocity=0)` and 83,930 with
  `(phase=1, aux=0, velocity!=0)`. The pending-time-450 instruction pointer
  contained 41,632 stopped samples; the pending-time-710 jump pointer
  contained 74,404 moving samples. All three fields changed together in
  3,037 adjacent same-slot pairs.
- **Status:** Causal mechanism corrected. Physical planner acceptance remains
  open under CE-0085.

## CE-0085: ECL lookahead appeared enabled but attached to zero bullets

- **Observed symptom:** Complete no-Bomb Stage-5 run `20260724_113250`
  recorded 21 hit edges. Spell 111 was hit at frames 39,706 and 41,151.
  At frame 39,706 the linear pipeline claimed 49.42 pixels of clearance and
  classified the contact as a sensor gap.
- **Implementation failure:** All 844 spell-111 lookahead rows reported
  `timer_elapsed=0`, zero events, and zero attached bullets with no error.
  The code had read VM `+0x94/+0x98`, which belongs to a separate
  `-999`-gated wait timer, instead of the main VM timer rooted at `+0x04`
  with fraction at `+0x08` and integer elapsed at `+0x0C`. The physical run
  therefore exercised the old linear model, not the new trajectory model.
- **Additional clock error:** One variable named `snapshot_lag` represented
  both the old player-state-to-current delay and the much smaller age of the
  freshly read projectile pool. The asynchronous corridor projected fresh
  hazards by the player sensor lag a second time. ECL event frames also lacked
  an explicit conversion from the ECL capture epoch to the bullet-pool epoch.
- **Corrections:** Native opcode-4 disassembly at `0x004186F1..0x0041870F`
  confirms timer integer `VM+0x0C` and target
  `instruction_pointer + signed displacement`. A real decoded sub-63
  regression now predicts stop/resume at `+110/+210` from timer 600. The
  game-neutral `HazardEpochAlignment` separates source-to-hazard lag, hazard
  age, event offset, and capture-window uncertainty. Trace records now expose
  scan stop reason, horizon coverage, tagged/stopped/attached counts, and all
  sensor frame windows.
- **Retained evidence:** The 21-hit ledger remains in the run dossier; the
  compact callback differential hashes the raw source and proves
  event rows/attached rows were both zero. This failed run cannot support an
  improvement claim.
- **Acceptance gate:** Before comparing hit counts, a fresh focused Stage-5
  run must show nonzero callback events and attached tagged bullets on both
  moving and stopped portions, timer progression through the 350/450/710
  loop, and event/phase parity within the recorded capture uncertainty.
- **Physical activation evidence:** Complete Stage-5 run
  `20260724_120128` covered timer values 1 through 709 and eight loop resets.
  Of 721 spell-111 lookahead rows, 672 contained future callback events and
  544 attached at least one bullet. Attached bullets occurred in both moving
  and stopped callback states. This closes the silent-zero-attachment gate,
  but the run regressed to 31 hits and is not a survival acceptance.
- **Status:** Activation gate passed; performance and epoch failures moved to
  CE-0086.

## CE-0086: Exact callback projection starved control and crossed an epoch

- **Observed symptom:** Complete hard-no-Bomb Stage-5 run
  `20260724_120128` recorded 31 hits versus 21 in the preceding failed-
  activation run. Spell 107 regressed from four hits to 11, spell 111 from
  two to five, and overall decision cadence degraded most strongly in the
  callback-heavy phases.
- **Observed timing:** Spell 107 attached callback trajectories on 315 of 346
  decisions, with median 988 and maximum 1,022 attached bullets. Its local
  planning median/p95 was `40.20/463.87 ms`, decision cadence `7/37` frames,
  and global solve median/p95 `556.50/708.46 ms`. Spell 115 had no callback
  events and retained `26.33/39.90 ms` local planning and `4/6`-frame cadence.
  Spell 103 similarly emitted four or six lookahead events on every decision
  and reached `333.19 ms` local p95.
- **Implementation cause:** The general event model was semantically active,
  but the TH08 corridor adapter expanded every event-driven bullet into 81
  `AabbHazard` Python objects. The native wrapper then traversed and repacked
  those objects frame by frame. A 1,024-bullet, 80-frame retained benchmark
  measured `325.88 ms` median end-to-end, including `218.80 ms` in Python
  materialization. A background corridor solve therefore competed with the
  real-time local loop precisely when callback density was highest.
- **Independent epoch failure:** At spell-103 frame 27,169 and spell-107
  frame 36,140, one bullet-pool read crossed native opcode-`0x94`'s `+1800`
  stage-counter jump. The controller joined the pre-jump player/spell state
  to the post-jump pool and treated the 1,800/1,801-frame span as ordinary
  timing uncertainty. These are torn cross-epoch snapshots, not slow physical
  reads.
- **General correction:** `PiecewiseAabbHazard` retains one trajectory plus
  sparse velocity replacements. A new C++ kernel accepts structure-of-arrays
  state and event offsets, performs double-precision projection, and updates
  the clearance volume without `N × T` Python objects. Python scalar sampling
  remains the fallback/oracle. `HazardEpochAlignment.fits_epoch` now rejects
  any source/capture/event/current timestamp extent above the configured
  eight-frame atomicity bound. Live control releases movement, increments the
  gameplay epoch, invalidates cached policy state, and records
  `sensor_epoch_discontinuity` instead of planning from a torn snapshot.
- **Differential/performance gate:** Four deterministic cases with 2,048
  hazards, 32 frames, and up to six velocity events match the independent
  scalar oracle within `9.54e-7` against the unchanged `5e-5` gate. The
  1,024-by-81 dense/sparse benchmark reports `325.88 ms` versus `66.70 ms`
  median, a `4.89×` speedup; lowering alone falls from `218.80 ms` to
  `1.01 ms`. The dense/sparse volume difference is `2.01e-5`.
- **Regression:** `test_ce_0086_large_positive_jump_crosses_sensor_epoch`,
  `test_native_sparse_piecewise_aabbs_match_scalar_samples`,
  `test_piecewise_projection_consumes_and_rebases_past_events`, retained
  adversarial benchmark
  `adversarial_piecewise_native_seed8008.json`, and speed benchmark
  `piecewise_native_speed_seed82408.json`.
- **Status:** Code and synthetic gates passed. A randomized non-Stage-5
  physical run is required before accepting the architecture change.

## CE-0087: A read-valid plan expired before input issue

- **Observed cross-stage control:** Complete hard-no-Bomb Stage-3 run
  `20260724_123136` recorded eight hits. Stage 3 emitted zero callback-motion
  events and attached zero piecewise bullets across spells 35, 38, 42, 46,
  and 50. The eight-hit result is within the prior complete-Stage-3 range
  `7..12` and is second-best among the six retained runs. This is evidence
  against a Stage-5 callback-specific overfit claim, but one randomized run is
  not acceptance.
- **Observed timing failure:** The read-time `fits_epoch` guard emitted zero
  discontinuities, yet frame 11,056 used source frame 9,254: the bullet read
  itself covered only 9,254..9,255 and the native `+1800` counter transition
  occurred while local planning was running. A stale action was therefore
  issued with `action_lag=1802`, and an old asynchronous corridor policy later
  appeared at ages above 3,590.
- **Observed ordinary deadline failure:** Spell 50 had 98/308 decisions
  (31.8 percent) whose snapshot-to-issue lag exceeded the modeled maximum of
  six frames. Three of its four hits were at or immediately preceded by such
  an invalid decision: frame 26,246 issued at lag 13; the last alive decisions
  before frames 26,759 and 27,421 issued at lags 10 and 11. The old dossier
  inspected only the hit row and therefore attributed only the first case.
- **Independent performance cause:** Stage 3 never invoked the sparse
  callback-AABB path. Relative to retained run `20260724_075004`, decode
  median rose `1.85 -> 5.34 ms`, local-plan median `22.90 -> 28.06 ms`, and
  global-solve median `217.71 -> 245.11 ms`. Spell 50's 200 lifecycle lasers
  made local laser construction the dominant sampled hot path; its local
  p95 was already approximately 135 ms in both runs, while the added
  bookkeeping increased the fraction of missed issue deadlines.
- **Invalid assumption:** A sensor epoch that is consistent at the end of
  capture remains valid until `SendInput`. The delay support describes
  snapshot-to-visible-input time; snapshot-to-issue lag is already a lower
  bound and must be checked again immediately before input.
- **General correction:** `ActionIssueAlignment` separates ordinary deadline
  miss from implausible post-capture counter advance. A decision beyond its
  complete delay support no longer injects a newly planned direction; it holds
  the previous actuator command and forces a trace row with planned/issued
  masks. A post-capture advance above the configured contiguous limit releases
  movement, advances the gameplay epoch, invalidates cached policy state, and
  records `action_epoch_discontinuity`.
- **Reporting correction:** `action_lag_over_model` now compares against the
  complete support high value and inspects both the hit row and last alive
  decision. The regenerated Stage-3 dossier attributes frames 26,246, 26,759,
  and 27,421, and retains both lags/support bounds in each death record.
- **Regression:** `test_ce_0087_slow_plan_misses_support_without_claiming_epoch`,
  `test_ce_0087_jump_after_valid_capture_crosses_action_epoch`,
  `test_ce_0087_last_alive_deadline_miss_is_attributed`, and
  `test_action_lag_uses_support_high_not_nominal_delay`.
- **Status:** Code and retained-report gates passed. Focused Stage-3 spell 50
  must show zero stale newly injected directions near its former hit windows;
  holding an old actuator command is fail-closed observability, not itself a
  survival proof.

### Physical follow-up

- Complete Stage-3 run `20260724_132007` exercised the guard. It suppressed
  all 96 expired newly planned inputs, including 95 during spell 50, and
  recorded no stale new direction after a deadline miss.
- The action-side epoch check caught issue frame 21,141 after source/capture
  frames 19,337/19,338 and a post-capture advance of 1,803. It released
  movement and invalidated the policy epoch rather than issuing the stale
  plan.
- Spell 50 still recorded five hits. Holding the older command closes the
  unmodeled-transition bug but does not create a newly certified fallback
  action. The next algorithmic correction must either predict a wider
  compute-delay tail before search or cheaply re-certify at issue time.
- **Status:** Observability and stale-input suppression physically passed;
  survival handling of a missed deadline remains open.

## CE-0088: Exact max-min safety ranking exceeded the live compute budget

- **Observed symptom:** Complete hard-no-Bomb Stage-3 run
  `20260724_132007`, with the optional 32-frame safety-value fallback enabled,
  recorded 15 hits. This is worse than the prior six complete Stage-3 runs,
  whose counts were `11,7,10,12,11,8`.
- **Controlled timing evidence:** Relative to the immediately preceding
  Stage-3 run, global solve median/p95 increased
  `245.11/398.44 -> 300.86/461.06 ms`; safety-value induction itself cost
  `49.97/58.70 ms`. Overall local median was unchanged, but spell-50 local
  p95 rose `134.69 -> 210.37 ms`, pre-trace p95
  `182.58 -> 258.44 ms`, and action-lag p95 `10 -> 15` frames.
- **What is not established:** The attempts used different native RNG states,
  so the hit-count regression alone is not a causal estimate. A paired
  retained-hazard ablation changed 168/300 actions while preserving identical
  robust-collision and negative-clearance counts. The max-min ranking is not
  shown to be geometrically unsafe.
- **Invalid assumption:** Exact equivalence to Boolean viability at positive
  thresholds made negative-margin ranking suitable for the live critical
  path. Mathematical correctness did not provide a wall-clock budget or
  prevent CPU/memory contention with the 200-laser local planner.
- **Correction:** Keep the game-neutral max-min recurrence and compact native
  implementation as an offline oracle/explicit experiment. Live practice
  remains default-off (`--safety-value-horizon 0`) until compute is shared or
  amortized without worsening local tail latency.
- **Independent local correction:** Fuse TH08 laser lifecycle projection
  directly into contiguous numeric frames rather than constructing and
  unpacking thousands of Python objects. On 100 retained spell-50 decisions,
  whole-decision median/p95 fell `33.97/56.96 -> 23.44/46.52 ms`, with zero
  action or full-decision differences.
- **Rejected C++ exploration:** A native per-call segment-hazard kernel only
  reduced the fused decision median/p95 `23.31/42.29 -> 22.19/39.09 ms` and
  changed 1/100 actions through floating-point reduction order. The branch
  was removed.
- **Regression/artifacts:** `test_fused_laser_projection_exactly_matches_object_pipeline`,
  `scripts/benchmarks/benchmark_local_laser_fusion.py`,
  `132007.local_laser_fusion_benchmark.json`, the three
  `132007.safety_value_*_replay.json` ablations, and the complete Stage-3
  dossier.
- **Status:** Failed live variant retained as a counterexample. Fused numeric
  laser projection passed offline differential/performance gates; physical
  cross-stage verification is pending.

## CE-0089: Soft boundary reserve pruned a safer delay-robust action

- **Observed cross-stage run:** Complete hard-no-Bomb Stage-6B run
  `20260724_135201` reached `route_complete` with 27 hits. Safety-value
  guidance was disabled and the fused laser path was active. Retained
  complete Stage-6B hit counts are `42,30,18,27`; different RNG states make
  the new count a workload, not evidence of regression or improvement.
- **Physical failure shape:** Twenty-four of 27 hits followed global
  viability-kernel exhaustion, 17 carried a playfield-boundary factor, and
  5,518/12,374 policy queries had an empty robust action set. Pre-hit
  bottom-eight-pixel occupancy was 0.307 versus 0.132 elsewhere; mean selected
  control-reserve deficit was 10.043 versus 1.422.
- **Root cause exposed by paired replay:** Boundary control reserve is a soft
  recovery preference used during beam pruning. The uncertain-delay
  first-action certificate was previously computed only after the fixed-width
  beam, so reserve could erase a first action before its harder collision
  evidence existed. On 300 identical retained decisions, enabling reserve
  changed robust-collision selections `24 -> 26` and negative-certificate
  selections `39 -> 42`. On 213 pre-hit rows they changed `60 -> 61` and
  `73 -> 75`.
- **General correction:** Compute the existing certificate for eligible first
  actions before beam expansion. Rank modeled collision, certificate collision
  and negative clearance before every soft clearance, boundary, recovery,
  risk, item, and position objective. Reuse the same certificate at final
  robust selection instead of paying twice.
- **Corrected differential:** Across 300 rows, reserve disabled/enabled now
  both select 22 robust collisions and 36 negative certificates; zero-reserve
  selections still improve `60 -> 186`. Across 213 pre-hit rows, both select
  56/72 while zero-reserve selections improve `10 -> 55`. Median local
  clearance is lower under reserve, so this accepts only hard-order
  preservation, not a general clearance improvement.
- **Regression/artifacts:**
  `test_ce_0089_delay_certificate_precedes_recovery_beam_pruning`, the four
  `135201.control_reserve*_replay.json` paired artifacts, and
  `notes/ALGORITHM_REVIEW_20260724.md`.
- **Independent performance correction:** Default live decoding no longer
  builds diagnostic transform queue/stop objects. Explicit
  `--trace-transform-runtime` preserves that evidence path. The retained
  200--1,200-bullet synthetic benchmark keeps exact gameplay-field parity and
  measures 1.25x--2.24x median speedups.
- **Status:** Algorithmic and offline differential gates pass. The 27-hit
  Stage-6B run remains the physical counterexample; the corrected ordering
  has not yet been physically accepted.

### Stage-5 physical and paired follow-up

- Complete hard-no-Bomb Stage-5 run `20260724_144805` reached
  `route_complete` with 16 native hits. The preceding comparable run had 31,
  but native RNG, respawns, Power, and phase lengths differ; the aggregate
  delta is not a causal survival estimate.
- The C++ sparse piecewise boundary passed its physical performance gate.
  Spell 107 local-plan p95 fell `463.61 -> 50.44 ms` and decision-cadence p95
  `37 -> 8` frames. Spell 111 fell `142.72 -> 40.95 ms` and `13 -> 6`
  frames. Default planning traces retained 186,521/104,595 lightweight
  trajectory samples for spells 107/111, including 99,176/102,870 samples
  with projected velocity events; diagnostic queue objects remained absent.
- A corrected replay decoder now reconstructs those retained piecewise events
  instead of silently replaying only current velocity. On 300 Stage-5 rows,
  reserve disabled/enabled both select 28 robust collisions and 45 negative
  certificates; on 60 pre-hit rows both select 18/24. Zero-reserve selections
  increase `87 -> 206` and `8 -> 27`. This cross-stage replay preserves the
  hard-ordering claim.
- Fifteen of 16 physical hits still follow global viability-kernel
  exhaustion. The run accepts activation and performance, not survival.

## CE-0090: The active boss occupied an unscanned special enemy slot

- **Repeated observation:** Five independent complete Stage-5 runs contain a
  spell-115 hit with zero bullets and zero lasers near the upper center:
  `(179.47,118.21)`, `(208.43,136.33)`, `(192.92,125.69)`,
  `(208.83,118.31)`, and `(184.49,120.69)`. Every asynchronous action
  snapshot reported zero enemy bodies.
- **Exact latest chain:** At frame 36,472, after spell 111 ended, a retained
  corridor target at `(184,16)` issued `up_fast`. Spell 115 became active at
  frame 36,475 with the player at `y=192.69`, zero projectiles, and a live
  owner pointer, but the old planner continued upward through frames
  36,478..36,490. A 24-point reversal penalty preserved the previous command
  after the spell context changed. Fourteen residual items supplied additional
  approach potential; one 24-value item became a predicted collection at
  frame 36,490. The hit began at frame 36,493 at `y=120.69`.
- **Observed address-set error:** The authoritative spell owner is
  `0x0057D2F0`. The asynchronous scan begins at `0x005826C0`; their difference
  is exactly one `0x53D0` enemy stride. The owner is therefore special slot
  `-1`, outside every one of the 480 ordinary timeline-enemy slots. Calling
  that scan the “full enemy pool” was false. This directly explains why its
  snapshots never contained Reisen even while her native contact bit was
  enabled.
- **Observed physical geometry:** The follow-up run retained 2,658 successful
  synchronous owner observations, all at `0x0057D2F0` and all outside the
  asynchronous range. Of these, 2,640 were contact-enabled and 18 were
  anticipatory transition observations. At spell-115 entry the owner was
  centered at `(192,128)` with half-size `(36,24)`, whose lethal rectangle
  `x=156..228, y=104..152` contains all five old hit coordinates. This makes
  boss contact the supported explanation for the old cluster; the crossed
  hit-edge read alone had not proved it.
- **Secondary uncertainty:** Even a pointer covered by the async scan can
  change its contact bit between snapshot and actuator pickup. The robust
  enabled/disabled union remains a valid adapter-level uncertainty treatment,
  but it was not the primary reason Reisen was absent.
- **General correction:** The TH08 adapter synchronously reads only the active
  spell owner's 1,500-byte geometry window. Planning takes the union of
  contact-disabled and contact-enabled modes, replacing the older copy of
  that pointer from the async pool. Trace rows distinguish observed
  `contact_enabled` from an `anticipatory` latent guard. This is an adapter
  uncertainty model, not a spell-ID or coordinate exception.
- **Soft-policy correction:** Item approach shaping is reduced from `0.18` to
  `0.02`; total item influence is saturating and bounded. A context boundary
  preserves the old command in the physical delay prefix but drops only its
  soft first-action reversal penalty. Replaying the exact first spell-115
  state changes the first counterfactual command from `up_fast` to `down`;
  later old rows are not a valid closed-loop replay after that divergence.
- **Regressions:**
  `test_ce_0090_latent_spell_owner_replaces_stale_pool_body`,
  `test_ce_0090_latent_spell_owner_blocks_post_spell_item_chase`,
  `test_ce_0090_spell_context_switch_drops_old_direction_inertia`, and
  `test_small_top_item_does_not_override_conservative_position`.
- **Physical follow-up:** Complete hard-no-Bomb Stage-5 run
  `20260724_152719` reached `route_complete` with 21 hits. It retained 700
  spell-115 owner observations and never placed the player above `y=160`
  during a zero-bullet spell-115 row. The only spell-115 death was frame
  41,768 at `(8,432)` amid 1,145 bullets with pipeline/robust clearance
  `-2.441`; it was a modeled viability-kernel exhaustion, not the old contact
  cluster. This accepts the targeted CE once, not overall survival.
- **Non-acceptance:** Total hits rose `16 -> 21`, spell-107 hits rose `3 -> 9`,
  and pre-hit bottom occupancy/control-reserve deficit also worsened. Different
  RNG, respawn, Power, and phase histories prevent attributing this aggregate
  delta to the guard. A randomized non-Stage-5 control remains required before
  accepting cross-stage behavior.

## CE-0091: Regression validation ignored the last-alive deadline miss

- **Observed symptom:** The freshly generated Stage-5 regression corpus failed
  its executable validator at `LUN-S5-F30748-T1`. The hit row had action lag
  `6` within support `[5,6]`, while its last alive row had lag `7`; the dossier
  correctly attributed `action_lag_over_model`, but the validator compared
  only the hit row against nominal delay.
- **Invalid assumption:** A contributing factor attributed over a pre-hit
  window can always be validated from the hit row alone. This had already been
  corrected in dossier generation for CE-0087 but not in the independent
  corpus validator.
- **General correction:** Executable validation now evaluates the complete
  delay-support high value on both the hit and retained last-alive decisions.
  When detailed deadline context is present, its stored booleans are also
  checked against the retained lag/support bounds.
- **Regression:** `test_action_lag_factor_includes_last_alive_support_miss`.
  The 21-case `20260724_152719` corpus and both older full-run corpora pass the
  executable gate.

## CE-0092: A contact ring spawned while the local decision was computing

- **Observed cross-stage control:** Complete hard-no-Bomb Stage-4A run
  `lunatic_route2_stage4a_unattended_20260724_155932` reached
  `route_complete` with 19 native hits, equal to the previous complete
  Stage-4A run. Per-phase hit counts changed in both directions, so native RNG,
  respawn, Power, and phase-length differences do not support an aggregate
  improvement or regression claim.
- **Observed exact contact:** Hit frame 35,419 has a stable crossed-frame
  contact observation at frame 35,420. Ordinary pool slot 18
  (`0x005E0B60`) was at `(325.859,128.534)`, with then-captured internal
  motion component `(-2.274,2.251)`, half-size `(18,18)`, and overlapped the
  native player lethal AABB with clearance `-16.625`. CE-0096 later proved
  that `+0x2D4C` is not generally world velocity.
- **Observed causal gap:** The last alive decision used source frame 35,412,
  captured bullets at frame 35,412, and issued at frame 35,415. Its async
  enemy snapshot was frame 35,410 and contained only the boss. The next
  decision exposed 19 bodies from an async snapshot stamped frame 35,413.
  Therefore the 18-body ring appeared after the causal hazard capture but
  before the old action was issued. The old local certificate reported zero
  collisions and `+27.550` clearance; the hit row, already too late, reported
  11 collisions and `-22.780`.
- **Reporting correction:** The old dossier called a pointer present if it
  appeared on the hit-detection row. It now records
  `present_in_hit_decision_snapshot=true` separately from
  `present_in_causal_snapshot=false`; the compatibility
  `present_in_action_snapshot` field has causal semantics. The run now
  attributes `enemy_body_absent_from_action_snapshot`.
- **General correction:** The TH08 adapter reads the first 64 ordinary enemy
  slots in one contiguous native read at local capture time while retaining
  the complete low-rate scan for tail slots and the special spell-owner
  guard. It reads the same prefix again immediately before input. New/removed
  pointers, contact-mode changes, size/velocity changes, or motion residuals
  trigger a fast all-action robust recertificate against the refreshed
  hazards. This is an allocation-prefix and issue-time version guard, not a
  Stage-4, Reimu, coordinate, or spell exception.
- **Measured emergency cost:** A retained 19-body synthetic recertificate
  costs `4.92/7.17 ms` median/p95 and runs only after a during-plan geometry
  change. The second contiguous read runs every decision and requires physical
  timing validation.
- **Regressions:**
  `test_ce_0092_synchronous_prefix_exposes_new_contact_ring`,
  `test_ce_0092_issue_time_ring_recertifies_stale_up_right`, and
  `test_ce_0092_hit_row_visibility_is_not_causal_visibility`.
- **Status:** Later complete Stage-4A and Stage-5 trials physically exercised
  the issue-time guard. The strict Stage-5 run recertified 2,307 decisions
  with `2.24/4.72 ms` read and `12.24/22.15 ms` recertificate median/p95.
  CE-0094 and CE-0097 separate mode-lifecycle and genuinely post-issue births
  that the original prefix-only correction cannot solve.

## CE-0093: Different-horizon Booleans hid a direct stale-action contradiction

- **Observed reporting defect:** The first Stage-4A consistency report called
  2,395 rows “global-empty/local-safe.” Global asked for a robust policy over
  another 48--80 frames, while local certified only an 8--12-frame selected
  action prefix. Those are not opposite answers to one proposition.
- **Observed action-level defect:** After aligning the contract, 30 of 6,613
  comparable rows selected an action that belonged to the cached global
  winning-action set even though the fresh local uncertain-delay tube checker
  predicted collision. The policy's underlying hazard snapshot was 19--48
  frames old on those rows. Several local clearances were `-10..-22`, so
  initial lattice projection alone cannot explain every contradiction.
- **Invalid assumption:** A cached long-horizon action mask can remain a hard
  constraint after a fresher, shorter-horizon collision certificate
  contradicts it. Long horizon does not make old hazard evidence newer.
- **General correction:** Global winning actions are intersected with the
  fresh prefix-safe action set before beam expansion. If the intersection is
  empty, the controller recertifies all 17 actions and relaxes the cached
  mask. Telemetry distinguishes filtering from full relaxation. This is a
  version-order invariant, not a Stage-4 direction or spell rule.
- **Offline evidence:** On the 30 retained contradiction rows, paired
  trace-radius replay changed 16 actions, improved the hard vector on 10,
  regressed on zero, reduced robust-collision decisions `29 -> 23`, and
  reduced negative-certificate rows `30 -> 23`. Eligible median/p95 cost rose
  `11.39/21.12 -> 20.00/36.08 ms`; the contradiction path represented only
  30/6,613 comparable live rows.
- **Algorithm correction:** “Recovery distance” to a next-layer endpoint is
  not a proof. The new scalar oracle instead maximizes guaranteed safe frames
  and only then bottleneck clearance. On 4,905 losing generated states,
  max-min margin alone forfeited guaranteed frames on 190 states.
- **Regressions/artifacts:**
  `test_fresh_prefix_contradiction_relaxes_stale_global_mask`,
  `test_planner_consistency_separates_horizon_from_action_contract`,
  `test_survival_horizon_outranks_shallower_immediate_collision`,
  `20260724_stage4a_fresh_viability_intersection.json`, and
  `20260724_survival_horizon_oracle.json`.
- **Status:** Reporter semantics, local hard ordering, scalar-oracle parity,
  and deterministic adversarial tests pass. Complete Stage-4A follow-ups and
  CE-0098's Stage-5 cross-control physically exercised the ordering. After
  excluding 1,474 observed issue-version changes, CE-0098 retained zero
  selected cached-action/fresh-prefix contradictions. This does not accept
  losing-state recovery.

## CE-0094: Enemy contact geometry disappeared across native mode switches

- **Observed first follow-up:** Complete hard-no-Bomb Stage-4A run
  `20260724_173718` reached `route_complete` with 22 hits. Three stable exact
  enemy-body overlaps occurred at frames 9,813, 29,012, and 29,474; all three
  pointers were absent from the action snapshot that governed the collision.
- **Observed lifecycle:** The frame-9,813 slot existed through frame 9,785,
  disappeared from the contact-enabled set, and returned in a 34-body ring at
  issue frame 9,811. The frame-29,012 and 29,474 pointers likewise followed
  continuous positions across contact-bit changes. Treating these as wholly
  new objects was false.
- **First correction:** The synchronous 64-slot safety prefix now retains
  active, non-blocked collision geometry even while contact bit `0x04` is
  clear. Complete run `20260724_175647` physically exercised this
  anticipatory union on 1,294 decisions, with as many as 49 latent bodies.
  Exact body overlaps fell from three to one, while total hits changed
  `22 -> 25` and is not a causal aggregate comparison.
- **Second lifecycle mode:** The remaining exact overlap at frame 36,180 used
  pointer `0x005B1910`. It was active through frame 36,144, absent for about
  35 frames, then re-enabled on a continuous curved trajectory at issue frame
  36,179. Contact-bit union alone cannot retain an active bit that also clears.
- **General correction:** A context-scoped observation memory retains absent
  ordinary slots for the 80-frame policy horizon, projects their last
  validated world motion, and adds only snapshot-age uncertainty. It resets
  on gameplay epoch, stage, or spell context changes. Complete run
  `20260724_181700` exercised dormant geometry on 3,785 decisions, maximum 52
  bodies. Its one exact body overlap was present in the action snapshot;
  absent-from-action exact overlaps changed `3 -> 0`. Cadence remained
  `4/6` frames and local planning `27.89/50.41 ms` median/p95.
- **Regressions:**
  `test_ce_0094_prefix_retains_latent_contact_disabled_body`,
  `test_ce_0094_contact_toggle_is_a_mode_change_not_a_respawn`,
  `test_ce_0094_latent_ring_avoids_the_frame_9813_reactivation`,
  `test_ce_0094_dormant_memory_avoids_frame_36180_reactivation`, and
  `test_dormant_enemy_memory_expires_and_resets_by_context`.
- **Limit:** Bounded memory covers previously observed slots, not a pointer
  that is allocated for the first time after the last observation. CE-0097
  keeps that separate instead of extending the TTL without evidence.

## CE-0095: A cached winning action did not contain a future bullet emission

- **Observed direct contradiction:** In run `20260724_175647`, the frame-13,028
  selected `down_fast`. The cached policy was built from snapshot frame
  13,001, queried at 13,025, and reported all 16 non-active alternatives
  winning. The fresh local capture at frame 13,024 found minimum clearance
  `-0.153` and no prefix-safe action; an observed bullet hit followed at
  frame 13,035.
- **Invalid assumption:** A policy and a local certificate can be called the
  same hazard version merely because no enemy-prefix topology change occurred.
  The global snapshot-to-local interval was 23 frames and did not include
  later projectile births/emissions.
- **Reporting correction:** Issue-time enemy invalidations and deadline-held
  old input are excluded from cached-global/local consistency counts. The
  remaining direct count is explicitly a forecast/version contradiction, not
  a same-snapshot theorem failure.
- **Algorithmic consequence:** No risk weight can reconstruct a projectile
  absent from the event set. The TH08 adapter must lower upcoming ECL/timeline
  emissions or a conservative declared birth envelope into the game-neutral
  time-indexed hazard contract.
- **Regression:** Retained case `LUN-S3-F13035-T1` plus
  `test_future_birth_must_be_in_the_event_model_or_revalidated`.
- **Stage-5 corroboration:** Differential capsule
  `policy_32530_32546.npz` did not contain bullet slot 1446. Before native hit
  32,581, later same-context capsules observed a new ring at slots 1420..1457,
  and retained hit geometry identifies slot 1446 as the exact overlap. The
  governing policy was already losing, so this is birth-model evidence rather
  than the cause of that empty kernel.
- **Status:** Observed and classified; ECL projectile-spawn coverage remains
  open.

## CE-0096: Internal enemy motion was misused as lethal world velocity

- **Static observation:** `sub_42DEB0` at `0x0042DEB0` adds
  `enemy+0x2D4C` only to the internal motion component at `+0x2D34`.
  `enemy_manager_update` later composes lethal/render world position
  `+0x2D88` from multiple motion/relative components before the contact call.
  Therefore `+0x2D4C != d(+0x2D88)/dt` in general. IDA comments at
  `0x42DF57` and `0x42CA54` record this correction.
- **Runtime proof:** In `20260724_181700`, pointer `0x00597600` retained world
  `y=164` while the second `+0x2D4C` float rose from `18.512` to `146.910`.
  Its world x position also performed a scripted `405.410 -> -14.963` mode
  jump. The old planner projected the body vertically by hundreds of pixels
  even though the lethal AABB stayed on the same y coordinate.
- **General correction:** Consecutive `+0x2D88` observations estimate planner
  world velocity. Secants above 32 px/frame are hybrid jumps: the exact new
  position is accepted and the last validated velocity is retained.
  `+0x2D4C` remains in compact telemetry only as an internal diagnostic.
  Issue-time motion invalidation compares trajectories aligned to the same
  player epoch; raw snapshots contribute topology/contact/size changes only.
- **Rejected over-conservative attempt:** The first estimator widened every
  unknown or jump sample by 16 px. Run `20260724_183707` rose to 34 hits;
  79,809/85,788 body samples carried uncertainty, issue trajectory changes
  exploded `6,004 -> 26,004`, and recertificates rose `2,841 -> 3,566`.
  This fixed margin had no reachability meaning and was removed.
- **Corrected physical follow-up:** Run `20260724_185059` completed with 26
  hits and zero Bomb. It is not an aggregate improvement claim against the
  21-hit RNG-distinct baseline. The relevant gates passed: global empty
  queries were `3,391` versus `3,376`, local planning was
  `27.05/49.96 ms` versus `27.89/50.41`, cadence stayed `4/6` frames, and
  issue changes/trajectory changes fell to `1,258/1,574`. The old 28.8k
  scripted-wrap body collision did not recur.
- **Regressions:**
  `test_ce_0096_internal_motion_component_is_not_world_velocity` and
  `test_ce_0096_issue_guard_uses_aligned_world_trajectory`.

## CE-0097: New collision rings were born after the final issue observation

- **Observed post-issue births:** In run `20260724_185059`, the action issued
  at frame 18,749 observed one prefix body. Pointer `0x005A7170` first appeared
  with four other bodies on the frame-18,753 hit decision and made exact
  contact. Separately, the action at frame 35,533 observed one body; pointer
  `0x005E5F30` first appeared in a 15-body set on the frame-35,538 hit
  decision. Both exact bodies were absent from the governing action snapshot.
- **What the guard did correctly:** The before-input prefix read was stable
  and contained no such pointer. The births occurred 4 and 5 frames later,
  after final validation. Faster issue recertification cannot observe a
  future allocation, and dormant memory cannot retain a never-observed slot.
- **Information-theoretic boundary:** For an adversary allowed to create an
  arbitrary overlapping body after observation, no state-only controller can
  certify survival. Earlier planning helps only if the spawn event, RNG
  branch, or a sound spatial-temporal envelope is part of the model.
- **Required correction:** Decode upcoming TH08 ECL/timeline enemy-spawn
  commands and lower them to a game-neutral `BirthWindow`/reachable-set event.
  Until coverage is known, an explicit conservative envelope is preferable
  to pretending a larger geometric weight is proof.
- **Regressions:** The two executable retained hit cases and
  `test_future_birth_must_be_in_the_event_model_or_revalidated`.
- **Status:** Open and now the highest-priority enemy-contact model gap.

## CE-0098: Strict enemy versioning did not prevent Stage-5 kernel exhaustion

- **Observed cross-stage trial:** Complete hard-no-Bomb Stage-5 run
  `lunatic_route2_stage5_unattended_20260724_191313` used the final
  0.25-pixel aligned world-trajectory tolerance and reached
  `route_complete`. Its 28 native hit frames were
  `[1934, 4448, 8254, 10690, 11061, 12485, 14270, 22809, 23413, 24500,
  25238, 29403, 29714, 30053, 30369, 30707, 31143, 31439, 31801, 32121,
  32543, 32884, 33410, 39856, 41629, 42782, 43465, 44729]`.
- **Retained contact classes:** Eleven rows have exact bullet overlap, 16
  have a modeled committed-prefix collision, and frame 10,690 remains a
  positive-clearance sensor gap. The seven stable crossed-frame contact
  captures contain no exact enemy-body overlap. Therefore this cross-control
  does not reproduce CE-0094/0096 as the physical contact cause.
- **Planner failure:** Twenty-six of 28 rows lost the long-horizon viability
  kernel before impact; the other two lack a pre-hit alive decision. Spell
  107 alone has 12 hits and 635 empty sets in 769 available queries. Across
  the route, 4,514 of 7,054 available queries are empty. The controller often
  receives tens or hundreds of frames of warning but its endpoint-distance
  recovery does not certify or reliably find a safe bridge back into the
  kernel.
- **Version guard evidence:** The strict issue guard detected and
  recertified 2,307/7,223 decisions, overrode 870 actions, and excluded 1,474
  newer hazard versions from the global/local comparison. Among the remaining
  3,753 comparable decisions, no selected cached-policy action contradicted
  the fresh local prefix certificate. This accepts version ordering, not the
  quality of the losing-state fallback.
- **Cost and non-causal aggregate:** Local planning was `28.53/57.24 ms`
  median/p95 and cadence `4/7` frames, versus `27.85/47.50 ms` and `4/6` in
  the earlier Stage-5 baseline without this guard. Global native solve time
  improved `285.01/474.16 -> 151.78/365.36 ms` after the bounded C++
  clearance traversal. Hit count changed `21 -> 28`, but RNG, respawns,
  Power, and phase duration make that unsuitable as a causal regression
  estimate.
- **General correction gate:** Replace endpoint-distance recovery with native
  lexicographic survival-horizon induction, then refine only around the
  continuous viability boundary. ECL/timeline birth envelopes and a packed
  issue-time native shield remain separate model/freshness gates.
- **Regression:** All 28 cases are retained in
  `lunatic_route2_stage5_unattended_20260724_191313.regressions.json` and
  pinned by
  `test_ce_0098_stage5_retains_strict_enemy_version_failures`.

## CE-0099: Audit capture was wired into the wrong planner call

- **Observed harness failure:** Audit-enabled Stage-5 session
  `lunatic_route2_stage5_unattended_20260724_201536` failed before gameplay
  with `_stage_corridor_solution() got an unexpected keyword argument
  'audit_capsule_dir'`. Menu identity, Lunatic, route 2, Sakuya/Remilia, image
  hash, and no-life-decrement patch had passed, but no gameplay sample was
  accepted.
- **Cause and correction:** The new keyword had been attached to the staging
  helper instead of the asynchronous `_solve_corridor` submission. It is now
  routed only to the worker. The failed session remains tracked as discarded;
  it is not merged into a physical baseline.
- **Instrumentation correction:** The subsequent complete capture showed that
  synchronous capsule I/O added `91.58/117.58 ms` median/p95 to a
  `100.17/166.71 ms` policy solve. Capsule writes now drain through an
  independent one-worker queue so policy publication does not wait for I/O.
- **Regression:**
  `test_ce_0099_audit_capsule_is_wired_to_corridor_worker` executes the exact
  worker keyword path, waits for the asynchronous receipt, and reads the
  produced file.

## CE-0100: A 16-pixel lattice erased three physically queried action sets

- **Observed differential:** The last two available pre-hit queries for all
  27 hits in Stage-5 run `20260724_201636` were reconstructed from exact
  ignored hazard capsules. All 54 live 16-pixel results reproduced. Three
  phase-103 queries that were empty at 16 pixels became winning with the same
  eight-frame layer and full delay support at both 8 and 4 pixels.
- **Witnesses:** Decision/query `23867/23862` changed from zero actions to
  3/4 at 8/4 pixels. `25560/25554` changed to 11/12, and `25569/25562`
  changed to 3/9. Their live-to-cell projection errors fell from
  `9.707/8.416/8.416` pixels to `1.882/0.559/0.559` at 4 pixels.
- **Scope limit:** No sampled phase-107 empty became viable at 8 or 4 pixels.
  This refutes uniform 16-pixel completeness; it does not prove that global
  4-pixel induction fixes Reisen or that any one refined action would have
  prevented the later hit.
- **General correction:** Refine reachable tubes and alleged empty boundaries
  adaptively. Do not encode phase-103 positions or switch the whole live field
  to 4 pixels.
- **Regressions:** Compact audit
  `artifacts/viability_audit/stage5_20260724_201636.json` plus
  `test_narrow_tunnel_requires_spatial_refinement_not_a_weight`.

## CE-0101: Endpoint-distance recovery chose a shorter survival branch

- **Observed modeled counterfactual:** Before native hit 3,491 in complete
  Stage-5 run `20260724_201636`, decision/query `3486/3483` had an empty
  Boolean kernel. The fused native/scalar-parity label guaranteed 10
  collision-free modeled frames for `stay`, `left`, `down`, `down_left`,
  `left_fast`, `down_fast`, and `down_left_fast`. The hit was eight frames
  after the query.
- **Old fallback:** Distant-kernel endpoint recovery selected and issued
  `down_right_fast`, which was absent from the survival-best mask. The retained
  local certificate already reported one collision and minimum clearance
  `-1.699`.
- **Interpretation:** This is a discrete-model counterexample to endpoint
  distance as the primary losing-state objective, not a physical replay proof
  that one of the seven alternatives avoids the native hit. In the other
  53 sampled queries, guaranteed survival was shorter than query-to-hit.
- **General correction:** Losing-state fallback must maximize guaranteed safe
  frames before bottleneck margin or kernel distance. Keep the fused result in
  shadow until its issue-time action path and whole-pipeline budget pass.
- **Regressions:** Full native/scalar label-and-mask parity in
  `test_native_fused_survival_labels_match_scalar_oracle`, plus the retained
  frame-3,491 audit observation.

## CE-0102: Fine viability reduced empty sets but expired the delivered policy

- **Observed physical result:** Complete hard-no-Bomb Stage-4A run
  `lunatic_route2_stage4a_unattended_20260724_220032` enabled coarse fused
  survival labels and full-horizon 8-pixel refinement after coarse source
  emptiness. It reached `route_complete` with 40 hits.
- **Direct delivery regression:** Against the RNG-distinct Boolean comparison,
  solve median/p95 changed `170.77/380.59 -> 532.04/1174.21 ms`, unique
  policies `1728 -> 630`, decisions without queries `68 -> 274`, and expired
  decisions `34 -> 178`. Local-plan median/p95 also changed
  `27.05/49.96 -> 31.06/63.11 ms`.
- **Misleading local success:** Empty queried sets fell
  `3391 -> 2434` (28.2 percent), but fewer model-empty states did not produce
  a fresher or safer delivered controller.
- **Cause:** The purported adaptive step recomputed a complete 8-pixel field
  over the complete 80-frame horizon. It improved a frozen-snapshot discrete
  model while consuming the validity window needed at action issue.
- **Correction:** Live refinement and survival-label authority are disabled;
  both remain shadow/offline. Worker counts and piecewise frame parallelism
  return to the previous committed native path.
- **Regression:**
  `test_rejected_fine_and_survival_strategies_remain_shadow_only`.
- **Reactivation gate:** Query-local/reachable-tube refinement must meet a
  whole-policy service SLO and may not increase expiry, missing-query, or
  local-latency tails. Model parity alone is insufficient.

## CE-0103: Coarse-survival isolation trial ended unreadable and is discarded

- **Observed session:** Stage-4A run
  `lunatic_route2_stage4a_unattended_20260724_221253` disabled fine refinement
  but retained coarse fused survival labels. It stopped at frame 13,077 after
  2,070 decisions and 12 hits with
  `termination_reason=process_unreadable`.
- **Integrity status:** The session records `status=discarded`,
  `trial_accepted=false`, and `game_terminated_after_trial=false`. The compact
  dossier and hit cases remain valid discovery artifacts, but the partial
  trace cannot be merged into a completion baseline.
- **What it can show:** Solve median/p95 returned to
  `196.09/354.90 ms`, supporting the attribution of CE-0102's largest
  background cost to fine refinement.
- **What it cannot show:** It does not establish whether coarse survival
  ranking helps or harms physical survival, and it does not explain why the
  process became unreadable.
- **Correction:** Coarse survival is also returned to shadow until an
  independently complete, delivery-safe experiment is justified. No further
  physical run is launched merely to rescue this strategy.

## CE-0104: Better Boss-x alignment did not produce better native HP response

- **Observed physical samples:** Stage-4A shadow capture
  `lunatic_route2_stage4a_unattended_20260724_231247` and the explicit
  horizontal-alignment experiment
  `lunatic_route2_stage4a_unattended_20260724_231637` both observed spell 57
  through the native Boss registry.
- **Sensor parity:** The shadow/live samples contain 873/906 Boss observations;
  every observation had a stable manager-frame bracket and an open native
  damage gate. Consecutive same-phase HP samples were monotone.
- **Proxy success:** The live experiment changed 123 safe-set actions and
  improved normal player/Boss horizontal-error median
  `51.50 -> 25.19 px`.
- **Native disagreement:** Observed HP response was
  `0.47597 -> 0.37837 HP/frame`. The alignment run's Power first/median was
  higher (`100/84` versus `75/43`), so depleted Power does not explain why the
  improved proxy failed to demonstrate improved damage in this pair.
- **Comparison limit:** The shadow trace was manually stopped at phase timer
  2729/3000, while the live trace reached 2996/3000. RNG, hit history, entry
  state, and Power trajectory differ. This is adverse evidence, not a causal
  estimate or a valid phase-duration comparison.
- **Cause:** Horizontal player/Boss distance omits decoded SHT shot records,
  focus-dependent option positions, cadence, shot travel, hitboxes, piercing,
  and the shared damage cap. It is not a faithful damage model.
- **Correction:** The live alignment CLI/authority was removed. Native
  HP/phase telemetry and safe-set shadow diagnostics remain. Any later damage
  objective must use the executable shot/option model and first demonstrate
  predicted-versus-native HP-delta parity.
- **Artifacts:**
  `artifacts/strategy/stage4a_boss_phase_shadow_20260724.json`,
  `artifacts/strategy/stage4a_boss_phase_live_20260724.json`, and
  `notes/ROUTE_CONDITIONED_STRATEGY_ARCHITECTURE_20260724.md`.

## CE-0105: Final-B inactive evidence precedes route-complete promotion

- **Observed symptom:** The completed full-route trial
  `lunatic_route2_fullrun_unattended_20260725_083917` ended with an agent
  summary of `route_complete`, but the first supervisor postprocessor marked
  the session discarded because it searched for a `scene_inactive` record
  whose status was also `route_complete`.
- **Invalid assumption:** The scene guard writes another inactive record when
  its terminal grace period promotes `terminal_unload` to `route_complete`.
- **Native trace evidence:** The retained final inactive record has frame
  `226864`, engine flags `0x1aa10`, stage/transition-from-stage `7`, no expected
  successor, and status `terminal_unload`. The following summary has
  `termination_reason=route_complete`; there is deliberately no second
  inactive edge.
- **Correction:** Full-route completion extraction now requires the exact
  Final-B `terminal_unload` record and independently requires the later
  route-complete summary/dossier gate. The recovered session records why its
  temporary postprocessing status changed from discarded to completed.
- **Regression:** `test_terminal_unload_precedes_route_complete_summary`.

## CE-0106: Empty-kernel fallback ignored survival horizon and repair-state reserve

- **Observed witness:** In the fresh Stage-5 attempt
  `lunatic_route2_stage5_unattended_20260725_103655`, the exact reconstructed
  Boolean query became empty at decision 1,680, 126 frames before the first
  hit. The fused oracle guaranteed 74 modeled frames for `stay` and
  `up_fast`, while the live fallback selected `down_right_fast`.
- **Hard-vector relation:** The selected action still had zero fresh local
  robust collisions and `+6.443` minimum clearance. This is therefore an
  objective-ordering defect after loss, not evidence that the local
  certificate accepted an immediate collision.
- **Reserve defect:** Repair volumes were present, so the old reserve term was
  disabled. Exact replay measured a 24-pixel control-reserve deficit for the
  selected action. At decision 1,760 the same ordering chose `down_right`
  instead of the nine-frame survival-best `stay`.
- **Correction boundary:** `losing_control_reserve` is explicit and
  default-off; survival/reserve variants remain shadow-only. Across 195 losing
  queries, survival-first changed 42 actions and improved best-mask membership
  `134 -> 175`; reserve-only improved 13 measured deficits and regressed zero.
  Neither result authorizes physical input.
- **Regression:** `test_repair_state_control_reserve_remains_shadow_only`.
- **Evidence:** `notes/LOSING_STATE_ROOT_CAUSE_20260725.md`.

## CE-0107: Short-horizon audit reused an unsliced packed laser batch

- **Observed failure:** The first short-horizon differential passed a packed
  laser trajectory containing 81 frames into a 32/48/64-frame solver
  configuration. The native contract correctly rejected the mismatched frame
  count instead of silently truncating it.
- **Cause:** The audit shortened `horizon_frames` but retained the base
  frame-major offsets and samples. Object trajectories had been naturally
  re-lowered; the packed fast path had not.
- **Correction:** `_packed_horizon_prefix` now slices both offsets and sample
  storage at the requested frame boundary before the counterfactual solve.
- **Regression:** `test_packed_horizon_prefix_slices_frames_and_samples`.

## CE-0108: Serialized post-publication shadow doubled expired decisions

- **Observed failure:** Complete hard-no-Bomb Stage-5 shadow
  `lunatic_route2_stage5_unattended_20260725_122624` computed losing labels
  after Boolean publication but placed the work on the same one-thread
  corridor executor. It completed `2..44065` with 8,233 decisions and 20
  native hits, but expired policy decisions rose from the Boolean-only
  comparison's 14 to 34.
- **Invalid assumption:** “Computed after publication” was treated as
  side-effect-free even though it serialized the next Boolean service request.
  Numeric label parity says nothing about worker availability.
- **Correction and physical gate:** Labels now use a separate executor and
  only one native worker. RNG-distinct complete Stage-5 run
  `lunatic_route2_stage5_unattended_20260725_125037` reached
  `route_complete` over `2..43338`, recorded 7,921 decisions and 18 native
  hits, passed hard no-Bomb, and left no runtime process. First policy age was
  `4/10` frames median/p95, query age `11/27`, and expired decisions 15,
  versus Boolean-only `6/12`, `11/27`, and 14. Local read/plan and action-lag
  medians/p95 were `13.08/18.18 ms`, `22.71/42.74 ms`, and `3/5` frames.
- **Boundary:** This accepts publication isolation, not survival. The 18-hit
  count is not comparable as a causal improvement. Labels took
  `150.43/284.57 ms` and remained shadow-only with zero parity failures.
- **Evidence:** `notes/BOOLEAN_FIRST_PENDING_PIPELINE_20260725.md`, both run
  dossiers, and the compact pending-pipeline audit artifacts.

## CE-0109: Issued desired input was not the game-active action

- **Observed failure:** The authoritative dense Boolean query used the last
  issued desired mask as `active_action`. Native `input_current` disagreed on
  754/8,077 queries in Stage-5 run `122624` and 805/7,772 in run `125037`.
  Where post-publication labels were available, querying the same source/layer
  with native observed input changed winning/losing classification nine times
  in each run: false-winning/false-losing splits were `8/1` and `5/4`.
- **Pending witness:** At `122624` frame 528, the dense observed/no-pending
  shadow guaranteed 18 frames with `stay` best. Exact phase reduced this to
  14. Adding the older pending `left_fast` command with remaining support
  `(1, 2)` reduced the guarantee to two frames and tied every new action. A
  newly selected action could not undo the already pending branch.
- **Independent differential:** The native pending-pipeline kernel matches
  the scalar oracle on 64 randomized seeds. In two deterministic 16-query
  physical-capsule cohorts, adding pending state changed 13 best-action sets
  in each cohort and changed winning classification 4 and 6 times.
- **Correction boundary:** Native observed input and pending estimates are now
  retained, and the phase-exact oracle is implemented. The live dense Boolean
  recurrence still lacks exact phase/pending state, so post-publication labels
  have no action authority. Do not “fix” this by simply substituting observed
  input while ignoring an older pending command.
- **Evidence:** `artifacts/benchmarks/postpublished_survival_20260725.json`,
  `artifacts/viability_audit/stage5_20260725_122624_pending_pipeline.json`,
  `artifacts/viability_audit/stage5_20260725_125037_pending_pipeline.json`,
  and `notes/BOOLEAN_FIRST_PENDING_PIPELINE_20260725.md`.

## CE-0110: Same-version rolling speed hid two cold decisions per policy

- **Observed failure:** The first rolling exact-root benchmark reported seed
  wall separately from Python frontier/continuation-root enumeration. After
  complete preparation was placed inside the four-frame service boundary, the
  retained five-policy workload met the deadline on only 14/25 decisions.
- **Cold/steady split:** Decisions one and two missed in all ten
  policy/decision samples; decision three passed 4/5, and decisions four/five
  passed 10/10. The one decision-three miss was `67.086 ms` against a
  `66.667 ms` budget. Labels still matched every monolithic exact oracle, so
  these are delivery misses rather than model errors.
- **Invalid assumption:** A steady same-version memo was treated as evidence
  for live delivery without comparing its warm-up length to immutable policy
  lifetime. The live controller's earlier global-solve and solution-age
  telemetry makes replacement within the first one or two decisions
  plausible.
- **Correction:** Root and seed enumeration are now included in end-to-end
  timing. A newer version receives a fresh executor and cancels old native
  work, but no memo is reused across changed clearance. S09 stays shadow-only
  until overlap with Boolean induction demonstrates a useful current-version
  exact-hit rate without delivery contention.
- **Regression/evidence:**
  `test_cancel_interrupts_running_native_expansion`,
  `test_new_publication_rejects_every_old_result`,
  `artifacts/benchmarks/rolling_pipeline_prewarm_20260725.json`, and
  `notes/ROLLING_PIPELINE_PREWARM_20260725.md`.

## CE-0111: One-transition cadence falsely certified a winning state

- **Shrunk model:** Five x-cells, actions `left/stay/right`, delay `{2,3}`,
  cadence `{1,2}`, ten-frame horizon, start x-cell 2, and only four unsafe
  cells: `(frame,x)={(5,0),(7,1),(9,2),(10,4)}`.
- **Failure:** The no-write-correct public-root cadence/fixed-2 continuation
  reports a complete ten-frame win. Recursive cadence admits a phase-shifted
  short/long sequence that misses the observation/action opportunity assumed
  by fixed continuation and guarantees only nine frames.
- **Cohort:** A 128-case 5-cell/10-frame cohort produced 3 action-label,
  2 best-action, and 1 winning mismatch between one-transition and recursive
  belief values. A smaller 3-cell/6-frame cohort produced zero mismatches;
  that negative evidence is not an equivalence proof.
- **Correction:** The old workspace is now named as a hybrid model only.
  Recursive-cadence authority requires the belief workspace or an explicitly
  conservative bounded policy.
- **Regression/evidence:**
  `test_recursive_cadence_catches_phase_shifted_observation_gap` and
  `artifacts/viability_audit/pipeline_formal_correctness_20260725.json`.

## CE-0112: Hidden remaining delay created a clairvoyant best action

- **Minimal model:** Three x-cells, actions `stay/right`, delay `{2,3}`, fixed
  one-frame cadence, four-frame horizon, and one unsafe cell at frame 4.
- **Failure:** Maximizing separately after exact hidden-delay successors
  reports both actions as complete four-frame best actions. Merging
  indistinguishable remaining-delay branches before the next maximization
  leaves only `stay` best; `right` guarantees three frames.
- **Cohort:** Under fixed cadence, clairvoyant and belief recurrences differed
  on 15/128 action-label sets and 11/128 best-action sets even though the
  maximum state winning label was unchanged.
- **Correction:** Remaining delay is stored as a belief-support bitmask in
  the new scalar/native recurrence and observation classes are merged before
  every future controller choice.
- **Regression/evidence:**
  `test_hidden_remaining_delay_cannot_select_future_action` and
  `artifacts/viability_audit/pipeline_formal_correctness_20260725.json`.

## CE-0113: Exact-root shadow work slowed the controller before it could help

- **Observed runs:** Complete Stage-5 control `171023`, full-frontier shadow
  `171925`, and bounded top-2/low-priority shadow `175339` retained 14, 32,
  and 27 native hits respectively. RNG differs, so hit totals are adverse
  rather than causal evidence.
- **Direct delivery regression:** Iteration median changed
  `45.63 -> 71.82 -> 65.98 ms`, local-plan median
  `20.35 -> 30.83 -> 29.22 ms`, and action-lag median
  `2 -> 4 -> 3` frames.
- **Low useful delivery:** Exact-root hits were `4.49%` for the full frontier
  and `12.47%` for top-2. Every covered root completed in time was consumed;
  root/version lookup was not corrupt.
- **Correction:** Physical prewarm remains explicit shadow-only and disabled
  by default. Do not run another physical prewarm until the finite value is
  semantically valid and offline whole-controller CPU accounting predicts no
  read/local-plan/action-lag regression.
- **Evidence:** The three run notes,
  `stage5_20260725_171925_pipeline_prewarm_shadow.json`,
  `stage5_20260725_175339_pipeline_prewarm_shadow.json`, and
  `notes/BELIEF_PIPELINE_CORRECTNESS_AND_PERFORMANCE_20260725.md`.

## CE-0114: A planner hold was modeled as a new input issue

- **Observed actuator semantics:** Live code calls `send_transitions` and
  `delay_estimator.issued` only when
  `input_transitions(previous_mask, decision.mask)` is nonempty. Selecting the
  held desired mask is no-write and cannot reset or replace an older pending
  command.
- **Minimal model:** Three x-cells, `left/stay`, fixed one-frame cadence,
  new-write delay `{3}`, three-frame horizon, observed `stay`, and `left`
  already pending with remaining delay two. Frame 3 / x-cell 1 is unsafe.
- **Failure:** Holding `left` lets the existing pending command activate and
  survives all three frames. The legacy decision-as-write recurrence replaces
  it at every decision and reports only two guaranteed frames.
- **Cohort:** With singleton delay/cadence, legacy and no-write recurrences
  differed on 30/128 action-label sets, 15/128 best-action sets, and 30/128
  winning classifications. Every state-value difference in this isolated
  cohort was legacy-conservative; the combined legacy model has no general
  bound direction.
- **Correction:** The scalar/native belief workspace issues only when selected
  action differs from held desired. A no-write transition carries/decrements
  the old pending support. The root API reconstructs held desired as pending
  action if present, otherwise observed action, under an explicit estimator
  invariant.
- **Regression/evidence:**
  `test_selecting_same_pending_action_does_not_reset_delay`,
  `artifacts/viability_audit/pipeline_formal_correctness_20260725.json`, and
  `notes/AUGMENTED_PIPELINE_ROBUST_CONTROL_FORMALIZATION_20260725.md`.

## CE-0115: A selective full-horizon margin certificate still grew for two seconds

- **Observed counterexample:** In the fresh Stage 6B capsule cohort, root
  frame 49830 had completed attainable lower label
  `(32, 10.2672501)`. The exact selective upper certificate eventually
  rejected every action, but expanded 111,901 threshold states, ran
  16,405,134 hidden simulations before the prefix shortcut
  (10,073,020 after it), and still required `1907.33 ms` in the retained
  uncapped replay. Root 52885 required `540.83 ms`.
- **Invalid generalization:** The synthetic structured root's zero-state
  `0.062 ms` certificate was treated as if incumbent thresholding eliminated
  unrestricted belief growth on every field. It eliminates irrelevant work,
  but hard margin-only roots may leave many actions/states genuinely capable
  of beating the threshold until deep induction.
- **Correction:** Full-horizon prefix failures now terminate immediately and
  a global suffix-clearance relaxation supplies another admissible upper
  bound. More importantly, a certificate deadline returns every in-flight
  and unvisited action as unresolved with an explicit flag. At 100 ms the two
  hard roots retained all 17 actions unresolved; no false certificate was
  published.
- **Regression/evidence:** The 128-case independent scalar/full-upper
  differential retains zero mask failures. A retained deterministic 1-ms
  case returns all 17 actions unresolved, a conservative superset of the
  exact eight-action gap. Exact and 100-ms physical-capsule reports are
  `stage6b_20260725_204521_belief_upper_certification_uncapped.json` and
  `stage6b_20260725_204521_belief_upper_certification.json`.

## CE-0116: Stage 6B reached contact after widespread global-kernel exhaustion

- **Observed run:** Instrumented hard-no-Bomb Lunatic Stage 6B
  `lunatic_route2_stage6b_unattended_20260725_204521` reached
  `route_complete` over frames `2..76235`, made 15,536 decisions, and
  retained 31 native hits. Hard no-Bomb passed and no runtime/JSON/control
  failure or manual re-arm occurred. The RNG-distinct comparison had 27 hits,
  so this is not survival improvement.
- **Failure boundary:** All 31 contacts were attributed to
  `global_viability_kernel_exhausted_before_hit`. Available policy queries
  were empty on `7213/15149` decisions. About 30 frames before contact, 28/31
  retained belief roots were already losing; the three trace-Boolean viable
  roots had full 32-frame attainable lower labels.
- **Cross-stage performance:** Global solve median improved
  `266.80 -> 97.41 ms` and clearance median `118.55 -> 13.72 ms`, confirming
  the earlier performance work outside Stage 5. The hit causes were 19
  modeled committed-prefix collisions, five observed bullet overlaps, five
  observed laser overlaps, one enemy-body overlap, and one residual
  sensor-gap/unmodeled case.
- **Next falsifiable gate:** Move the audit earlier until it identifies the
  first root at which control reserve/boundary pressure collapses the viable
  set. A correction must preserve a non-empty kernel through retained former
  hit windows, not merely calculate the losing value faster.
- **Evidence:** The run note, dossier, death ledger, executable regression
  cases, comparison, and both compact belief-certificate reports.

## CE-0117: Repeated short upper queries restarted instead of converging

- **Observed synthetic counterexample:** On deterministic structured seed 0,
  the 32-frame/17-action revealed-delay upper query needs about 109 ms exact.
  Before the correction, five calls with a 5-ms deadline each cleared both
  threshold memos. Every call returned all 17 actions unresolved and rebuilt
  roughly 1,000--1,175 states; a fresh 25-ms call also returned all 17.
- **Invalid assumption:** Repeating a deadline-bounded recursive call was
  treated as time slicing even though no completed proof state or root-action
  status survived the call boundary. Independent Monte Carlo-like retries do
  not accumulate a worst-case certificate.
- **Correction:** A session is keyed by immutable workspace/version,
  canonical root, absolute lower frame target, and the exact float32 margin
  bits. It retains only normally completed threshold subproblems and exact
  root-action statuses. Deadline-interrupted work stays unknown and is
  returned unresolved; every key change resets the session.
- **Regression/evidence:** Five retained repetitions completed in 21--23
  5-ms slices, every intermediate mask was a conservative superset, and every
  final mask matched the exact eight-action result. Fresh restarts with the
  same attempt count remained at all 17 unresolved and rebuilt about twice as
  many states. See
  `notes/RESUMABLE_INCUMBENT_CERTIFICATION_20260725.md`,
  `scripts/benchmarks/benchmark_resumable_upper_certification.py`, and
  `artifacts/benchmarks/resumable_upper_certification_20260725.json`.

## CE-0118: Cheap exact-root lookup hid background verifier contention

- **Observed physical counterexample:** Hard-no-Bomb Stage-6B candidate
  shadow `lunatic_route2_stage6b_unattended_20260726_004142` submitted a
  stationary candidate portfolio for every queryable Boolean root. Submit and
  lookup were cheap (`0.042/0.019 ms` median), but exact issue-time delivery
  was only `8004/12220 = 65.50%`; the single worker accumulated 205 queued
  target replacements and 1,099 stale completions.
- **Controller impact:** Relative to RNG-distinct Boolean-only `000654`,
  local-plan median increased `21.20 -> 26.46 ms`, full iteration
  `45.89 -> 53.11 ms`, action lag `2 -> 3` frames, cadence `3 -> 4`, Boolean
  viability `70.68 -> 79.57 ms`, and first policy age `3 -> 4`. The run's 33
  hits versus 23 are not a causal comparison, but the direct timing and queue
  regressions reject the every-root service.
- **Invalid assumption:** Nonblocking lookup was treated as proof that a
  shadow worker was side-effect-free. The native candidate expansion still
  competed with sensing, Boolean viability, and local planning for CPU, while
  work on short-lived viable roots became obsolete before consumption.
- **Correction:** Admit only available Boolean-losing roots, apply one
  below-normal-priority worker and a 12-ms between-candidate budget, discard
  obsolete desired/queued targets on viable or unavailable decisions, and
  require exact `(policy version, phase, cell, observed action, pending
  action, remaining-delay support)` lookup. Completed lower labels remain
  shadow-only; exhaustion and timeout remain unresolved.
- **Physical regression:** Corrected v2 `011639` completed Stage 6B with
  `6192/6618 = 93.56%` exact delivery, zero replacements, and zero stale
  completions. Read/local-plan/iteration medians were
  `12.10/21.85/44.88 ms`, action lag/cadence `2/3` frames, viability
  `69.54 ms`, and policy age `3` frames, all back inside the Boolean-only
  baseline envelope. Its 26 RNG-distinct hits grant no survival authority.
- **Evidence:** raw-bundle hashes and physical audits
  `stage6b_20260726_004142_candidate_verifier_shadow.json` and
  `stage6b_20260726_011639_candidate_verifier_shadow_v2.json`; full analysis
  in
  `notes/FEASIBILITY_FIRST_STAGE6B_PHYSICAL_CONTENTION_20260726.md`.

## CE-0119: Aggregate candidate telemetry could not authorize or replay an alternate action

- **Observed artifact failure:** The retained losing-only Stage-6B v2 trace
  recorded 941 delivered full-horizon candidate wins, but kept only the
  aggregate label, best-action names, and completed candidate names. It
  discarded the per-action candidate witness, the issued action's exact
  candidate label, and every alternate-action fresh hard certificate.
- **Focused replay:** 82 candidate wins fell within 120 frames of 17 contacts.
  Exact root fields matched all 82, but current exact replay reproduced both
  historical state label and best set for only 47, covering 14 contacts. The
  other 35 are `historical_replay_mismatch`; current Windows and Linux agreed
  on two focused mismatch probes, so this is not evidence of a current
  cross-platform kernel split.
- **Consequence:** Of the 47 auditable roots, 23 candidate decisions changed
  action and 21 changed the issued action from a modeled 32-frame loss to a
  modeled win. All 23 alternate actions lacked their issue certificate.
  Trace-radius bullets cannot conservatively reconstruct the full snapshot
  certificate, so none receives retrospective input authority. No winning
  candidate root occurred within 32 frames of contact.
- **Invalid assumption:** Candidate name plus aggregate best actions was
  treated as enough to reconstruct a public decision. It is not
  content-complete: a lower bound is attainable only with its causal witness,
  and local issuability is action-specific.
- **Correction:** Retain every root-action `CandidateActionWitness` in the
  outcome; serialize best witnesses plus the issued-action label; preserve the
  already-computed all-action local certificate vector; and emit a one-shot
  exact-key shadow publication that fails closed on stale keys, deadline,
  missing certificate, collision, or negative clearance. It never changes
  the live mask.
- **Evidence:**
  `artifacts/viability_audit/stage6b_20260726_011639_candidate_witness_counterfactual.json`
  and
  `notes/CANDIDATE_WITNESS_PUBLICATION_CONTRACT_20260726.md`.

## CE-0120: A frozen manager counter held movement through post-spell dialogue

- **Observed physical counterexample:** In complete hard-no-Bomb Stage-4A run
  `lunatic_route2_stage4a_unattended_20260726_100451`, the controller reached
  post-spell manager frame 21467 at `(252.69, 391.37)` while holding
  `up_left_fast`. Six `auto_confirm_wall_pulse` records occurred at the same
  manager frame. The next decision was frame 21470 at `(8.00, 32.16)`, a
  434.63-pixel displacement in only three reported manager frames. A second
  episode held `left_fast` across eight wall pulses and moved 343.65 pixels to
  the left boundary over two reported frames. Equivalent `stay` episodes had
  zero displacement.
- **Rejected attribution:** Item utility was zero and predicted collections
  were empty. The center-lane target legitimately proposed movement in the
  ordinary manager-frame model; the defect was the unbounded hidden
  wall-clock hold, not an item or damage objective. The frame-21611 contact
  followed near the top boundary, but temporal proximity alone is not a
  causal prevention claim.
- **Invalid assumption:** `enemy_manager_frame` was treated as the physical
  clock for both hazards and player motion. During dialogue it can stop while
  held directional input still moves the player. The repeated-counter branch
  toggled only `Z`, so a finite planner hold acquired an unmodeled,
  dialogue-length physical duration. It also left the pre-freeze Boolean
  policy and async sensor epoch intact.
- **Attempted correction, rejected:** A 50-ms repeated-counter guard released
  movement, created a new gameplay epoch, and invalidated policy/sensor work.
  CE-0121 shows that its predicate was not a semantic freeze detector. The
  guard has been removed and the better pre-guard live controller restored.
- **Observed native mechanism:** IDA shows `frscreen_blocks_enemy_clock`
  (`0x4358BB`) tests a non-null FRScreen implementation and signed MSG state
  `>= 0 || == -2`; the enemy manager consults it after the priority-9 player
  callback has already applied movement. Shadow Stage-4A runs `120839` and
  `122014` observed active MSG-state episodes with advancing FRScreen serial.
  Directional episodes moved `282.90`, `355.90`, and `309.51 px`; a `stay`
  episode moved `0 px`.
- **Observed tracker correction:** `120839` exposed a telemetry bug that
  merged the `4963` and `6763` pulse groups while the MSG gate remained
  active. Censoring and reopening when the physical frame changes produced
  five semantic episodes for five delayed pulse groups in `122014`, with no
  mismatch against that proxy. The terminal group remained right-censored.
- **Current boundary:** The sensor/classification boundary is answered for
  the observed Stage-4A MSG states, but the original actuator defect remains
  unresolved. The detector has no movement-release, pending-delay, epoch, or
  policy-retirement authority. `msg_state == -2` was not observed and its
  physical meaning is unknown. Do not infer a phase transition from a short
  repeated manager-frame value.
- **Evidence:** compact audit
  `artifacts/runtime_reports/lunatic_route2_stage4a_unattended_20260726_100451.frozen_input.json`,
  semantic audits for `120839` and `122014`,
  raw JSONL SHA-256
  `b8e9428f648b6c87ee379291d896804410019469b8b7f86ef6233456e050c5a1`,
  and `notes/FROZEN_MANAGER_INPUT_CLOCK_BOUNDARY_20260726.md`.

## CE-0121: A 50-ms repeated-frame guard starved the live Boolean policy

- **Observed physical counterexample:** Complete hard-no-Bomb Stage-4A run
  `lunatic_route2_stage4a_unattended_20260726_103856` used the latest live
  Boolean/local controller, a shadow-only candidate verifier, and the 50-ms
  guard. It reached `route_complete` with 7,925 decisions and 64 hits. The
  guard fired 2,780 times, beginning at manager frame 91, while the trace had
  only 72 actual `auto_confirm_wall_pulse` records.
- **Invalid assumption:** Persisting one `enemy_manager_frame` value for 50 ms
  identifies a dialogue/phase freeze. Ordinary pool reads, planning, logging,
  and Windows scheduling routinely exceed that duration without a semantic
  transition.
- **Direct mechanism:** Every false positive incremented `gameplay_epoch` and
  correctly retired the old corridor policy. Available viability queries fell
  from 9,073 in `100451` to 691; pending-future-epoch decisions rose from 42
  to 623. Thus most of the run fell back to local planning.
- **Causal boundary:** The epoch churn and policy starvation are directly
  observed and sufficient to reject the guard. The `21 -> 64` hit difference
  is supporting physical evidence, not a controlled effect estimate, because
  RNG, timing, and phase histories differ.
- **Observed semantic disagreement:** In shadow-only `120839`, a hypothetical
  50-ms cut occurred on 2,744 gate-inactive repeats and five gate-active
  repeats. Corrected `122014` produced 1,728/5; its first-repeat
  inactive/active counts were 3,016/5. These are threshold/native-gate
  disagreements, not independently labeled false positives. They show that
  the wall-time distributions overlap and independently reproduce the
  rejected predicate's classification failure.
- **No starvation authority claim:** The two shadow runs retained available
  viability queries on 7,216/7,349 and 8,759/8,914 decisions, unlike
  `103856`'s 691/7,925. This is consistent with the absence of epoch mutation,
  but does not prove zero CPU contention because total capture calls, RNG,
  and host timing were not controlled.
- **Correction:** Remove the guard and its unit test; restore `1ce5b44`
  live-controller behavior while retaining only shadow publication timing.
  Keep CE-0120 open.
- **Regression/authority gate:** Live source must contain no
  `FROZEN_INPUT_RELEASE_SECONDS`, `_frozen_input_neutralization_due`, or
  `frozen_input_neutralized` authority path. Any successor starts as shadow
  episode classification.
- **Evidence:**
  `artifacts/viability_audit/stage4a_20260726_103856_frozen_guard_rejection.json`,
  recovered dossier/comparison for `103856`, raw JSONL SHA-256
  `b32c941a7def998d62fc3e2820c5c779534e1a3c10055faed69d717127fb925f`,
  and `notes/FROZEN_MANAGER_INPUT_CLOCK_BOUNDARY_20260726.md`.

## CE-0122: Batched hazard filtering changed a candidate's clearance

- **Observed deterministic counterexample:** Calling
  `_hazards_for_positions` for one position could return different positive
  clearance and risk after an unrelated far-away position was added to the
  same batch. The focused regression reproduces this for both a bullet and a
  laser and compares the two-position batch with two independent
  single-position calls.
- **Invalid assumption:** A single global coarse hazard slice was sufficient
  for all positions in a vectorized batch. The slice admitted every hazard
  near *any* candidate, after which collision, minimum-clearance, and risk
  reductions treated it as relevant to *every* candidate.
- **Consequence:** Hard collision labels were protected only when the
  erroneously admitted hazard remained positively separated. Soft clearance
  and risk, and therefore beam pruning/ranking, depended on companion
  candidates rather than only on the physical state being evaluated.
- **Correction:** Preserve the global coarse slice, then apply a
  per-position/per-hazard relevance mask before collision, robust-clearance,
  and risk reductions for bullets and lasers. Unrelated entries contribute
  zero collision/risk and infinite clearance for that position.
- **Regression:** `test_hazard_batch_is_invariant_to_companion_positions` in
  `tests/test_th08_local_pipeline_certificate.py`.
- **Authority boundary:** This is a deterministic geometry correction in the
  existing local path. Its offline correctness is observed; a causal physical
  survival effect is not.
- **Evidence:** `notes/LOCAL_PIPELINE_CERTIFICATE_AND_BEAM_AUDIT_20260726.md`.

## CE-0123: The local certificate reset a pending no-write pipeline

- **Observed replay counterexample:** On the deliberately mismatch-heavy
  Stage-4A `122014` sample, pending-aware semantics changed the locally safe
  action set on `86/155` roots and changed the recorded action from legacy
  safe to pipeline-unsafe on 21. Stage-6B `011639` changed `85/156` safe sets,
  with nine legacy-safe/pipeline-unsafe and two reverse cases. These are sampled
  model differentials, not population rates or prevented-hit claims.
- **Concrete retained row:** At inferred Stage-4A frame `1738`, native active
  input was `left_fast`, held/pending desired input was `up_fast`, and
  remaining support was `1..3`. The recorded `left_fast` action changed from
  zero modeled collisions and `+0.028` legacy clearance to five collisions
  and `-3.953` pending-aware clearance.
- **Invalid assumption:** The previous local certificate equated the last
  desired mask with native active input and sampled a new full pickup delay
  for every selected action. Selecting the already-held complete mask was
  therefore treated as a write, the observed-active prefix was omitted, and
  the older pending command was reset.
- **Correction:** Make native active, held desired, optional older pending,
  and conditioned remaining-delay support explicit. A held action is
  no-write; a new action universally branches over older remaining and new
  pickup delays in causal order. An independent scalar branch oracle checks
  the packed all-action implementation.
- **Regression:** Five focused oracle tests plus scalar/packed TH08 geometry
  differentials, including 24 deterministic randomized roots, pass. The
  packed equivalent-root implementation had zero hard-label parity failures
  against the corrected-batch legacy recurrence over both retained samples.
- **Authority boundary:** Old traces require inferred roots. New trace rows
  retain explicit root telemetry, but live selection still supplies no
  pending-aware root. No new input, estimator, epoch, or frozen-manager
  authority follows from this checkpoint.
- **Evidence:**
  `artifacts/benchmarks/local_pipeline_certificate_20260726.json` and
  `notes/LOCAL_PIPELINE_CERTIFICATE_AND_BEAM_AUDIT_20260726.md`.

## CE-0124: The first post-discontinuity root was active/held inconsistent

- **Observed physical counterexample:** Complete Hard Stage-1 run
  `hard_route2_stage1_unattended_20260726_175049` emitted an
  `action_epoch_discontinuity` at manager frame `16748`. At the first retained
  decision after it, frame `16750`, native `input_current` was mask `0xA5`
  (`down_right`) while the controller's held desired mask had been reset to
  `0x01` (`stay_unfocused`). There was no retained pending command or
  remaining-delay support, and the root record correctly marked
  `estimator_consistent=false`.
- **Invalid assumption:** An epoch reset or missing prior-write record does
  not make native active input equal to the newly initialized held desired
  value. The actuator can still expose an older active command at the first
  post-discontinuity observation.
- **Consequence:** Reconstructing the first root as active-equals-held would
  erase an observed movement prefix and could certify the wrong first action.
  The current live local fallback still uses active-equals-held semantics, so
  explicit active/held/pending roots remain shadow-only.
- **Correction/gate:** Preserve native `input_current` independently across
  the discontinuity, treat the missing issue history as unresolved rather
  than “no pending,” and fail closed on estimator inconsistency. Do not pass
  the explicit root into live selection until discontinuity initialization,
  pending support, frozen-manager behavior, direct-root replay, and the full
  issue deadline are reconciled.
- **Authority boundary:** The run had zero hits, zero Bomb, and zero deadline
  misses, but this one root is a causal telemetry counterexample, not evidence
  that the fallback is generally safe. No new actuator or planner authority
  follows.
- **Evidence:** ignored raw replay bundle
  `hard_route2_stage1_unattended_20260726_175049.jsonl`, compact run artifacts,
  and `notes/runs/hard_route2_stage1_unattended_20260726_175049.md`.

## CE-0125: Hard Practice preconfirm exposed two different difficulty fields

- **Observed automation counterexample:** The first Hard Stage-1 launch
  attempt `174946` reached the native Practice stage screen with
  `mode=11`, `substate=1`, stage cursor `0`, difficulty cursor `2`, and
  Route 2. The gameplay `difficulty_index` was still `0` before the final
  stage confirm, so a gate that treated it as the selected menu difficulty
  rejected a correct Hard menu state.
- **Invalid assumption:** `difficulty_cursor` is the authoritative
  preconfirm menu selection; `difficulty_index` becomes authoritative only
  after gameplay loads. They are not interchangeable at the stage-selection
  boundary.
- **Correction:** Validate `difficulty_cursor` before final confirm, then let
  the armed live agent independently require gameplay `difficulty_index=2`.
  The next run `175049` passed both gates and completed Stage 1.
- **Regression:** `test_preconfirm_gate_uses_difficulty_cursor_before_gameplay_index`
  plus difficulty-order/parser tests in
  `tests/test_th08_practice_supervisor.py`.
- **Evidence:** retained failed session
  `hard_route2_stage1_unattended_20260726_174946.session.json` and complete
  successor artifacts for `175049`.

## CE-0126: Hard full route entered an empty global kernel before 38 of 39 hits

- **Observed physical run:** Continuous original-game Hard Route-2
  `hard_route2_fullrun_unattended_20260726_184942` reached Final-B
  `terminal_unload` and the later `route_complete` over frames `1..228661`.
  It retained 70,699 decisions, 39 native hits, zero Bomb/deathbomb input,
  zero foreground interruption, zero runtime/JSON error, and the exact stage
  sequence `0,1,2,3,5,7`. Stage hit counts were `1/1/8/11/9/9`.
- **Canonical causal witness:** The first fresh-attempt hit is
  `HARD-S0-F20606-T1`, during Hard spell 8. At the last alive decision,
  frame `20603`, the fresh local prefix already had one modeled collision and
  `-1.889` clearance; the global query had an empty safe-action set. Native
  contact telemetry then observed bullet slot 857 overlapping the player
  AABB. This is a modeled loss reached before contact, not decoder latency
  hiding an otherwise safe last-second action.
- **Observed population shape:** The global viability kernel was already
  exhausted before 38/39 hits. Primary causes were 23 modeled committed-prefix
  collisions, 14 observed bullet overlaps, one observed enemy-body overlap,
  and one sensor-gap/unmodeled case. Contributing factors included
  playfield boundary on 30/39, fast mode on 29/39, corridor deadline miss on
  13/39, and pool density above 1,000 on only 4/39.
- **Observed warning boundary:** Global empty-kernel warning commonly preceded
  contact by tens to hundreds of frames, while the fresh local robust-prefix
  warning was usually only a few frames. This means the global planner often
  knew the route had become losing before the local actuator could repair it.
  The one remaining `late_collision_after_positive_causal_margin` and six
  global-winning/fresh-local-unsafe selected actions remain correctness
  counterexamples; they do not explain the other 38 contacts.
- **Observed implementation performance:** Per-stage pool-read medians were
  `4.09..4.71 ms`; local-plan medians were `11.81..14.55 ms` and p95 values
  `20.86..26.90 ms`, despite maxima of 1,231 bullets and 256 lasers. There was
  no control stall. Relative to the earlier complete Lunatic run, read and
  plan timings are materially lower, but difficulty/RNG make its hit count an
  invalid causal A/B.
- **Inferred main defect:** The dominant next problem is earlier global
  feasibility preservation and losing-state strategy—especially boundary
  reserve, route/tube objectives, lattice false empties, horizon, and
  event/trajectory forecast—not a wholesale decoder or geometry rewrite.
  The data do not prove that all empty kernels are physically unavoidable:
  the live policy uses a 16-pixel/eight-frame/80-frame approximation.
- **Regression/evidence:** All 39 cases are executable regressions. Compact
  dossier, death CSV, summary, session, and human-readable review are retained
  under `artifacts/runtime_reports/` and `notes/runs/`; the 1.84-GB raw JSONL
  remains ignored and replay-capable. The dossier now derives case prefixes
  from physical difficulty, preventing Hard witnesses from being mislabeled
  `LUN`.

## CE-0127: Issue-time enemy recertification bypassed the global winning mask

Status: fixed and physically validated

- **Observed implementation defect:** `recertify_action_for_fresh_hazards`
  recomputes all 17 local action certificates and ranks all 17 actions. It
  receives no retained global allowed-action set and therefore does not
  implement the documented
  `cached winning actions ∩ fresh prefix-safe actions` transaction.
- **Observed physical population:** Complete audit-only Hard Stage-4A run
  `hard_route2_stage4a_unattended_20260726_202439` had 255 globally winning
  decisions whose final action was outside the reported winning set. On 168,
  issue recertification changed a planned action inside the set to one
  outside it while telemetry still reported `viability_constrained=true`,
  with neither general nor fresh-prefix relaxation. Only one of those 168
  selected actions had a negative fresh hard vector; the defect is loss of
  long-horizon authority, not primarily local collision acceptance.
- **Canonical witness:** At frame 3353, before the first fresh-attempt hit at
  3419, the global safe set was
  `{up, up_left, up_fast, up_left_fast}` and local planning selected
  `up_fast`. An enemy-velocity change triggered recertification and replaced
  it with locally safe `down_fast`, outside the global set. The next decision
  at 3356 was globally empty, and the player remained near the left/bottom
  boundary until contact.
- **Causal limit:** The trace did not serialize the fresh four-action
  intersection, so it does not prove that retaining `up_fast` prevents the
  hit. It proves that the live issue transaction silently discards or
  misreports its global constraint.
- **Additional inconsistency:** After replacing the action, the recertifier
  retains repair/recovery/survival fields belonging to the old action. Trace
  strategy telemetry can therefore describe a different action from the one
  issued.
- **Required correction:** Keep a planned action that remains fresh-hard-safe.
  Otherwise intersect the retained global allowed set with the fresh
  all-action certificate; relax only when that intersection is empty and
  mark the relaxation explicitly. Retain the planned certificate,
  intersection, reason, selected certificate, and correct per-action strategy
  fields.
- **Implemented correction:** The issue transaction now computes the exact
  fresh/global intersection, preserves a planned member, restricts
  replacement to the intersection, and explicitly marks an empty-intersection
  relaxation. It retains planned/selected certificates and invalidates the
  old beam-endpoint reserve field when the action changes. Deterministic
  preserve/intersect/relax regressions pass on Linux and Windows. Two
  complete no-audit Hard Stage-4A gates recorded 4,627 transactions, zero
  silent outside-mask selections, zero Bomb, and no latency regression.
- **Regression/evidence:** Add a deterministic intersection/preserve-planned
  regression before physical testing. The 15-case hit corpus and 1,741
  capsule bundle are validated; detailed evidence is in
  `notes/HARD_STAGE4A_VIABILITY_DIFFERENTIAL_20260726.md`.

## CE-0128: Empty fresh/global intersection used the wrong preservation reason

Status: fixed and physically validated

- **Observed physical telemetry defect:** Complete no-audit Hard Stage-4A run
  `hard_route2_stage4a_unattended_20260726_211210` retained 2,417 issue
  transactions. Frames 32,515 and 40,699 had an empty fresh/global
  intersection, explicitly set `global_constraint_relaxed=true`, and safely
  preserved the planned action outside the old global set. The record
  incorrectly labeled those rows
  `preserve_planned_in_fresh_global_intersection`.
- **Authority impact:** None observed. Both rows explicitly relaxed the old
  global constraint, `viability_constrained=false`, and retained the exact
  fresh safe set and selected certificate. The independent audit found zero
  silent outside-global actions and zero certificate/strategy mismatches.
  This is a reason/provenance defect, not another CE-0127 action violation.
- **Cause:** The preserve-planned branch selected its reason from
  `global_constraint_applicable` without first testing the already-computed
  empty-intersection relaxation.
- **Correction:** Empty-intersection preservation now emits
  `relax_empty_fresh_global_intersection_preserve_planned`. The independent
  trace auditor checks reason/state consistency and a deterministic
  regression covers this branch. Complete second gate `212756` retained 2,210
  reason-aware transactions with zero violations.

## CE-0129: Repair-aware beam pruning regressed a later terminal hard score

Status: aggressive beam variant rejected; final-only proposal retained

- **Observed offline counterexample:** A default-off experiment inserted
  exact global `repair_volume` and delay-scaled boundary reserve into local
  beam canonicalization/truncation before the existing route and soft
  columns. In an 800-root fixed reservoir within 300 frames of the next Hard
  hit, it changed 392 issued actions and improved repair volume on 356, but
  two changed actions had worse terminal hard vectors.
- **Canonical roots:** On Stage-4A `202439` frame `28412`, historical
  `up_left` had terminal `(collisions=3, negative-clearance deficit=2.226)`;
  the repair-biased beam chose `up_fast` with `(6, 3.037)`. On Stage-4A
  `212756` frame `12843`, historical `down_right` had terminal `(0, 0)` while
  the repair-biased beam chose `up_fast` with `(0, 0.489)`. In both cases the
  proposal increased repair volume and remained inside the global safe set.
- **Invalid assumption:** A proof-backed root continuation score does not
  make it safe to discard a beam endpoint before the longer terminal-threat
  interval has been evaluated. `repair_volume` is exact for its finite
  global recurrence, but it is not an admissible bound on the local
  10-to-32-frame terminal score.
- **Correction:** Remove the native-v2/beam-ordering change entirely. Keep
  the historical native reducer and candidate set. The surviving default-off
  proposal inserts repair and reserve only during final selection, after
  local and terminal collision/negative-clearance columns. The same fixed
  reservoirs then had zero hard regressions among 7 broad and 13 pre-hit
  changed actions.
- **Future gate:** A stronger candidate-coverage experiment must preserve the
  complete historical beam as an immutable incumbent and add a separately
  budgeted supplemental lane. Final comparison over the union must retain the
  historical hard endpoint; shared pruning cannot silently displace it.
- **Regression/evidence:** The final-only six-bullet root is reduced in
  `test_preloss_preference_retains_larger_exact_repair_action`. Rejected and
  retained paired reports are under `artifacts/benchmarks/` with
  `hard_preloss_beam_preference_rejected_*` and
  `hard_preloss_continuation_reserve_*` names.

## CE-0130: Synchronous supplemental search exceeded its direct-root issue budget

Status: synchronous current-issue delivery rejected; lane remains offline

- **Observed Windows counterexample:** The width-4 immutable supplemental lane
  kept zero finite-contract, hard, route, continuation, Bomb, or forced-issue
  transaction violations across 1,518 comparisons, but failed its
  predeclared delivery gate under the normal-priority four-worker planner.
  The paired supplemental-minus-historical direct-root compute increment was
  `2.354/14.273/25.184 ms` median/p95/max.  The gate required p95 at most
  `5 ms` and maximum below `16.667 ms`.
- **Canonical root:** Hard Stage-4A `212756`, gameplay epoch 2, frame 37,834,
  with 640 active bullets, physical `observe_to_input=41.999 ms`,
  support-high four, and post-capture advance two.  Historical and
  supplemental compute cost `18.551/43.735 ms`; the hybrid estimate became
  `67.183 ms`, above the `66.667 ms` stable-60-Hz support budget.  All three
  historical/supplemental/recertified actions were `down_left_fast`.
- **Invalid assumption:** A native endpoint reducer made width 4 inexpensive
  in ordinary same-root replay, but did not bound the complete Python/native
  rollout, hazard-query, selection, scheduler, and recertification tail while
  four native viability workers were active.
- **Isolation:** Global planner p95 and throughput ratios were
  `0.998x/1.015x`, inside their fixed `1.10x/0.90x` limits.  Supplemental
  search itself cost `3.273/6.858/10.553 ms`; trace reconstruction and root
  parsing were sub-millisecond tails.  This is a local delivery failure, not
  evidence that the four-worker global planner should be weakened.
- **Correction boundary:** Keep the lane default-off with no physical CLI.
  Either fuse the complete supplemental rollout/hazard-query boundary into a
  deadline-aware native call or publish it asynchronously under exact
  immutable root/version identity.  Timeout, cancellation, miss, or mismatch
  returns the historical action.
- **Regression/evidence:** Fixed gate thresholds and deadline semantics are
  covered by
  `test_benchmark_supplemental_direct_root_contention.py`.  Full evidence is
  retained in
  `artifacts/benchmarks/hard_supplemental_direct_root_contention_windows_20260726.json`
  and
  `notes/SUPPLEMENTAL_DIRECT_ROOT_WINDOWS_CONTENTION_GATE_20260726.md`.

## CE-0131: Same-issue exact-version publication still perturbed delivery

Status: exact-version same-issue delivery rejected; offline implementation retained

- **Observed Windows counterexample:** Moving the complete width-four
  supplemental rollout, hazard query and reduction behind one native C++
  boundary eliminated the Python rollout tail.  Under four global workers,
  completed native work itself cost `0.876/1.365/1.942 ms`
  median/p95/max, retained 100% of reference action changes, and had zero
  completed-native/Python or historical-fallback mismatch.  Nevertheless the
  fixed synchronous end-to-end gate still measured
  `1.249/7.054/53.721 ms` paired median/p95/max and one new deadline-proxy
  miss.
- **Rejected asynchronous follow-up:** A dedicated below-normal-priority,
  newest-wins worker then accepted exact immutable identities, cooperatively
  cancelled stale work, published only complete results, and made consumer
  lookup nonblocking.  On the final identical 253-root, three-round Windows
  gate, 728/729 eligible four-worker queries completed, all 294 reference
  action changes were retained, and all finite, issue, native/reference, and
  fallback checks remained clean.  The paired increment was still
  `2.240/8.139/12.214 ms`; p95 exceeded the fixed `5 ms` limit and one new
  hybrid deadline-proxy miss remained.
- **Canonical async witness:** Hard Stage-4A `212756`, epoch 0, frame 969 had
  123 bullets, no laser, physical `observe_to_input=39.634 ms`,
  support-high three and post-capture advance two.  The paired increment was
  `11.023 ms`, producing `50.658 ms` against a `50.000 ms` support budget.
  Historical, supplemental and recertified actions were all `stay`.
  `choose_action` and recertification contributed `8.894/2.044 ms` of the
  increment while measured async submit/lookup work was only `0.078 ms`.
- **Invalid assumption:** Removing optional work from the Python critical
  path is not the same as removing its same-issue CPU, cache and scheduler
  interference.  Exact identity prevents stale reuse but cannot make a
  current-root result available before the current root exists.
- **Isolation:** The global planner's supplemental-versus-historical
  solve-p95 and throughput ratios were `0.990x/1.021x`, within the fixed
  `1.10x/0.90x` bounds.  The optional native recurrence and publication
  semantics are implementation-parity clean; the failure is delivery
  contention, not evidence for reducing the authoritative four-worker
  planner.
- **Correction boundary:** Keep all supplemental modes default-off and grant
  no physical action authority.  A future publication experiment must obtain
  a causally valid exact hazard/policy version before the issue transaction
  or use genuinely reserved execution resources; it must not reuse a merely
  similar prior root.  Otherwise retain the historical action and return to
  global feasibility/route work.
- **Regression/evidence:** Cancellation, deadline, newest-wins identity,
  fallback and endpoint parity have deterministic tests.  Compact reports
  are
  `artifacts/benchmarks/hard_supplemental_full_native_direct_root_contention_windows_20260726.json`
  and
  `artifacts/benchmarks/hard_supplemental_exact_async_final_direct_root_contention_windows_20260726.json`;
  the publication contract is
  `notes/EXACT_VERSION_ASYNC_SUPPLEMENTAL_PUBLICATION_20260726.md`.

## CE-0132: Post-R5 Stage-1 smoke reached the bottom boundary after kernel exhaustion

Status: observed physical survival failure; R5 lifecycle smoke completed

- **Observed Windows counterexample:** The focused Hard Stage-1
  no-strategy-change smoke
  `hard_route2_stage1_unattended_20260727_133807` completed 7,541 decisions
  through terminal scene handling and supervisor cleanup with zero Bomb
  input, but its fresh attempt took one native hit at frame 5,262 during
  spell 0 `蛍符「地上の流星」`. The player was at `(232.731, 432.000)` with
  208 bullets and no laser. The observed contact candidate was bullet slot
  129 at `(235.567, 426.527)`, with AABB clearance `-1.527`.
- **Causal boundary:** The hit row detected the native hit before issuing its
  new `up_right_fast` action. The physical active input at contact was
  `up_left_fast` (`input_current=0x51`); the decision row's newly issued mask
  `0x91` is not the causal collision input. The signed pipeline clearance was
  already nonpositive at frame 5,255 and was `-1.956` on the hit row.
- **Observed planner state:** The exact published policy was queryable and its
  current delay support `[2,3,4]` was covered, but the queried global state was
  losing with zero safe actions. The dossier classifies the planner failure
  as `global_viability_kernel_exhausted_before_hit` and records a positive
  12-frame robust warning lead.
- **Inference, not proof:** Bottom-boundary occupation and finite-kernel
  exhaustion are contributing evidence, not proof that either alone caused
  the contact or that the R5 structural move regressed survival. The retained
  clean Stage-1 baseline used a different physical attempt; one stochastic
  pair cannot establish strategy equivalence or regression.
- **Correction boundary:** Keep R5 accepted only as a lifecycle, cleanup,
  trace-schema, and no-Bomb structural gate. The algorithmic correction
  remains the roadmap G0/G1/G2 sequence: preserve the exact-root loss window,
  separate model coverage from finite losing and delivery states, then test a
  conservative refinement or attainable continuation witness. Do not change
  live authority based on this single run.
- **Regression/evidence:** The compact witness is retained in
  `notes/runs/hard_route2_stage1_unattended_20260727_133807.md` and the
  matching summary, dossier, comparison, regression, death, and session
  artifacts under `artifacts/runtime_reports/`. The 137 MiB raw JSONL remains
  local and ignored.
- **Additional observed instance:** G1 shadow run
  `hard_route2_stage1_unattended_20260727_153821` completed Hard Stage 1 and
  cleanup with zero Bomb input but took one fresh-attempt hit at frame 2,651.
  The player was near the top at `(124.965,19.253)`, active input was
  `right_fast`, signed pipeline clearance was `-19.248`, the finite kernel
  was already exhausted, and the robust warning lead was eight frames. This
  is a second stochastic instance of the same broad post-exhaustion failure,
  not evidence that G1 shadow telemetry caused the hit.
- **Additional observed instance:** Post-corridor-trace-extraction run
  `hard_route2_stage1_unattended_20260727_175715` completed Hard Stage 1,
  artifact materialization, and cleanup with zero Bomb input but took one
  fresh-attempt hit at frame 6,385. The player was at
  `(337.911,40.561)` during a nonspell with active `down_left_fast`, 118
  bullets, zero lasers, and signed pipeline clearance `-2.787`. The global
  kernel had exhausted six frames before contact. The 7,263 emitted corridor
  records had zero required-field omissions, so this is another stochastic
  post-exhaustion survival failure, not evidence of trace-schema failure.
  Compact evidence is retained under the matching run name in `notes/runs/`
  and `artifacts/runtime_reports/`; raw JSONL SHA-256 is
  `3e0f5f89abd533b0d8f6d2420c71eca3f869fd4f6f4b371dad686b71f1cea83d`.
- **Additional observed instance:** Post-candidate-trace-extraction run
  `hard_route2_stage1_unattended_20260727_181119` completed Hard Stage 1 and
  cleanup with zero Bomb input but took one fresh-attempt hit at frame 2,043.
  At `(376.000,23.812)` on the right/top boundary, active input was `down`,
  144 bullets and zero lasers were present, and signed pipeline clearance was
  `-1.257`. The dossier classifies the physical contact as
  `modeled_committed_prefix_collision` and the planner state as
  `global_viability_kernel_exhausted_before_hit`, with four frames of robust
  warning. No same-epoch observed bullet overlap was retained. This widens the
  CE-0132 instances beyond the bottom boundary; kernel exhaustion and finite
  committed-prefix collision remain the actionable facts. Compact evidence
  is retained under the matching run name; raw JSONL SHA-256 is
  `0dcf0130c3a31be57d2df643a4ca7a12048084cc02afd1f19ac258244aecbc80`.

## CE-0133: A fixed 240-frame pre-hit window missed four exhaustion boundaries

Status: observed audit-coverage failure; corrected in the G0 dossier

- **Observed failure:** the Hard Stage-4A `202439` audit selected queries from
  240 frames before each of 15 contacts, but the latest same-gameplay-epoch
  nonempty-to-empty global-kernel boundaries preceded four contacts by
  `275`, `348`, `866`, and `874` frames. Those fixed windows began with an
  already-empty kernel and could not identify the transition.
- **Why it matters:** an audit that assumes the loss transition is inside a
  fixed pre-hit window can mistake a persistent route/tube loss episode for a
  last-moment local-planner failure. An absent transition is unresolved, not
  proof that the kernel was always empty.
- **Correction boundary:** retain the latest same-epoch viable-to-empty pair
  before each contact and expand the context start to
  `min(hit - 240, preceding_nonempty_frame)`. Keep these 15 transition
  witnesses separate from the 61 stratified empty-query roots.
- **Evidence:** `notes/EXACT_ROOT_LOSS_DOSSIER_20260727.md` and
  `artifacts/viability_audit/hard_stage4a_20260726_202439_exact_root_dossier.json`.
- **Regression:** `test_transition_window_expands_past_240_frames`.

## CE-0134: A complete-mask write collapsed to movement-action no-write

Status: observed physical counterexample; corrected in the offline
scalar/native recurrence, while live authority remains excluded

- **Observed Windows counterexample:** In Hard Stage-1 shadow run
  `hard_route2_stage1_unattended_20260727_153821`, decision frame `13133`
  observed native active mask `0x05` (`stay + Focus + Shot`) while the held
  and pending desired mask was `0x85` (`right + Focus + Shot`) with remaining
  support `[1,2,3]`. The newly selected mask was `0x84`
  (`right + Focus`).
- **Physical issue:** `0x85 != 0x84`, so dispatch released the Shot key and
  the estimator recorded a new issue. The movement projection of both masks
  is `right`, so the current movement-action recurrence evaluates
  `selected_action == held_desired_action` and calls the same decision
  no-write.
- **Why it matters:** The immediate movement trace may coincide because the
  older and newer desired movement are equal. The complete active
  observation, pending command identity, remaining-delay support, and later
  write/no-write transition do not. A recursive value keyed only by movement
  action can therefore merge physically different information states. The
  error direction is unknown.
- **Scope:** The full trace contains 135 movement-equivalent complete-mask
  writes and one with both a pending command and a different active movement.
  This is not evidence that all 135 change movement values; the one pending
  witness is sufficient to reject a general complete-pipeline equivalence.
- **Correction boundary:** Keep the canonical complete-mask root and all
  explicit pipeline ranking shadow-only. Add complete desired mask or an
  equivalent issue token to controller action, observation, pending, and
  scalar/native memo identity. Alternatively prove an actuator invariant
  that forbids such reissues; no such invariant currently exists.
- **Corrected finite witness:** The 36-token no-Bomb action alphabet and
  64-bit belief ABI retain complete-mask indices even when velocities agree.
  In the deterministic six-frame regression, changing only pending `0x85`
  to `0x84` swaps the matching/mismatching root values between `(5,+1)` and
  `(2,-1)`. Python scalar and C++ native labels agree for all 36 root actions.
  This closes the movement-alias bug in the offline recurrence, not the
  future-hazard, clock, delivery, or live-authority gates.
- **Evidence:** Raw trace SHA-256
  `1cc423641141a6c884907754eed8742865f472ae40a1f1c77d47f4b916ab931e`;
  compact report
  `artifacts/runtime_reports/hard_route2_stage1_unattended_20260727_153821.pipeline_pickup.json`;
  problem note
  `notes/PIPELINE_ROOT_AND_HAZARD_COVERAGE_CONTRACT_20260727.md`; correction
  contract `notes/COMPLETE_MASK_ISSUE_ACTION_CONTRACT_20260727.md`.
- **Regression:**
  `test_pending_same_movement_complete_mask_write_blocks_promotion`,
  `test_equal_velocity_pending_identity_changes_no_write_value`, and
  `test_36_action_ce_0134_root_matches_independent_scalar`.

## CE-0135: Sound query-local refinement missed the issue deadline by seconds

Status: observed offline delivery failure; semantic implementation retained,
live delivery rejected

- **Observed retained gate:** All six retained `SPATIAL_AMBIGUITY` roots pass
  the declared lower/reference/upper action inclusion relation and are
  recovered by a completed lower witness. No case uses a full-field patch.
- **Delivery failure:** Across ten attempted root/resolution evaluations,
  Python patch construction takes `3160.63..14153.12 ms` and vectorized
  rectangle solving takes `859.02..4008.67 ms` on Linux. One 4-pixel root
  needs two empty-state expansion layers, 225,004 requested states, and 77.47%
  of the spatial field.
- **Why it matters:** Soundness after the issue deadline cannot authorize the
  current input. A query-local label also does not imply small work when its
  conservative dependency closure approaches the whole field.
- **Correction boundary:** Keep the exact quantifiers, root identity, timeout
  lower-zero/upper-all rule, and retained gate. Replace Python enumeration and
  dense rectangle solving with sparse/native cooperatively cancellable work.
  Do not add a publisher or consumer until Windows age, contention,
  cancellation, and exact-version lookup gates pass.
- **Evidence:** `notes/G2_QUERY_LOCAL_REFINEMENT_GATE_20260727.md` and
  `artifacts/viability_audit/g2_spatial_refinement_gate_20260727.json`,
  SHA-256
  `bfc42d9f1c71f1b8228187360cca76d4023807201713a222d9c05664824f2bde`.
- **Regression:**
  `test_stop_redirect_and_reversal_cases_bound_dense_reference` plus the
  retained `g2_spatial_refinement_gate.py` six-root run.

## CE-0136: Stage 4A remained unsafe across kernel exhaustion and late contact

Status: observed physical survival failure; structural sensing-trace gate
completed

- **Observed high-pressure run:** Supervised no-Bomb run
  `hard_route2_stage4a_unattended_20260727_183640` completed frames
  `2..45392`, 15,122 decisions, route completion, artifact materialization,
  and cleanup. It reached 1,072 active bullets and took eight native hits at
  `[8957,12004,12430,12955,19187,29011,32526,36193]`.
- **Canonical first hit:** Frame 8,957 was a nonspell observed-bullet overlap
  at player `(125.566,432.000)` with active `up_right_fast`, 176 bullets, zero
  lasers, and signed pipeline clearance `-2.343`. The global viability kernel
  was exhausted with a 14-frame robust warning.
- **Later discovery evidence:** Five hits were observed bullet overlaps, two
  were modeled committed-prefix collisions, and frame 19,187 was an exact
  same-epoch enemy-body overlap. Planner attribution counted six
  `global_viability_kernel_exhausted_before_hit`, one
  `late_collision_after_positive_causal_margin`, and one
  `robust_action_set_exhausted_before_hit`. Later contacts are geometry and
  planner evidence, not independent fresh trials.
- **Structural boundary:** All 15,122 decisions retained the 18 required
  sensing field groups, there was no serialization exception or stall, hard
  no-Bomb passed, and all processes cleaned up. This retains the sensing
  refactor but does not rescue physical survival.
- **Correction boundary:** Preserve and analyze the first exhaustion
  transition before each contact, keep late-positive-margin and exact enemy
  body cases separate, and require Stage 4A followed by Stage 5/6B evidence
  for later planner/native changes. Do not infer improvement from the lower
  hit count of an RNG-distinct run.
- **Observed fresh-issue-stage retention:** Lunatic run
  `lunatic_route2_stage4a_unattended_20260727_220330` completed frames
  `2..41645`, 13,295 decisions, maximum 1,362 bullets, hard no-Bomb,
  accepted artifacts, and cleanup after extracting the fresh enemy-prefix
  stage. It took seven hits at
  `[2775,4158,10484,11966,20720,35517,36397]`; five were observed-bullet
  overlaps and two were modeled committed-prefix collisions. Every hit
  followed global-kernel exhaustion.
- **Observed issue-stage integrity:** All 13,295 decisions retained an
  issue-time enemy observation. The 2,178 changed observations produced
  exactly 2,178 recertifications and 2,178 fresh/global transactions, with
  39 action overrides and zero silent outside-global selections. This retains
  the extracted stage but does not rescue survival.
- **Evidence:** Matching compact run and dossier artifacts. Ignored raw JSONL
  SHA-256 values are
  `f22dae779704b0e0189a9cf3129ce77db1aeec83245c82a7264edd579ef4fea8`
  for the Hard run and
  `7a283ce85264a778e2fc24e01ad65efa0d3235161b733ed7105f8b9434264bcf`
  for the post-extraction Lunatic run.

## CE-0137: Stage 5 exhausted every global kernel before contact

Status: observed physical survival failure; timing/optional-hazard trace gate
completed

- **Observed high-pressure run:** Supervised no-Bomb run
  `hard_route2_stage5_unattended_20260727_185422` completed frames
  `2..40448`, 12,602 decisions, route completion, artifact materialization,
  and cleanup. It reached 1,190 active bullets and took eight native hits at
  `[11557,14457,22900,24323,29045,29503,32734,35477]`.
- **Canonical first hit:** Frame 11,557 was a nonspell modeled
  committed-prefix collision at player `(364.616,432.000)` with active
  `up_fast`, 544 bullets, zero lasers, and signed pipeline clearance
  `-2.275`. The global viability kernel was exhausted with a seven-frame
  robust warning.
- **Later discovery evidence:** Seven of eight contacts were modeled
  committed-prefix collisions; one was an observed-bullet overlap. Every hit
  followed global viability-kernel exhaustion, with warning leads
  `[7,6,2,4,124,26,5,8]` frames. Later contacts include spells 102, 106, and
  110 and remain geometry, boundary, delay, and planner evidence rather than
  independent fresh trials.
- **Pressure signature:** Six contacts involved the playfield boundary, five
  used fast movement, and two occurred above 1,000 active bullets. Bottom
  eight-pixel occupancy was 0.528 in the 60-frame pre-hit windows versus
  0.193 elsewhere; mean selected control-reserve deficit was 10.223 versus
  3.291. These are correlations, not causal acceptance claims.
- **Structural boundary:** All 12,602 decisions retained the required timing
  groups and enabled optional-hazard records, there was no serialization
  exception or stall, hard no-Bomb passed, and all processes cleaned up.
  This retains the trace refactor but does not rescue physical survival.
- **Correction boundary:** Treat policy delivery, delay-support coverage, and
  viability exhaustion as separate gates. Preserve a non-empty action kernel
  before the former hit windows and compare phase-specific position and
  warning lead; do not infer improvement from aggregate hits across different
  RNG samples.
- **Observed Lunatic corroboration:** Post-native-split run
  `lunatic_route2_stage5_unattended_20260727_212624` completed frames
  `2..41508`, 12,770 decisions, maximum 1,533 bullets, hard no-Bomb,
  accepted artifacts, and cleanup. It took eight hits at
  `[11504,11936,12952,13466,24394,30393,31143,41238]`; five were modeled
  committed-prefix collisions and three were observed-bullet overlaps.
  Every contact again followed global-kernel exhaustion.
- **Observed separated warnings:** The fresh frame-11,504 hit followed global
  loss by 230 frames, robust action-set exhaustion by nine frames, and
  negative short-pipeline clearance by two frames. The policy therefore
  exposed a long causal intervention window, but its post-loss distant
  recovery did not construct a viable continuation. Seven of eight contacts
  involved the playfield boundary and all eight used fast movement.
- **Observed issue-override corroboration:** After extracting the ordered
  deadline/deathbomb/auto-confirm/final no-Bomb override boundary, supervised
  Lunatic run `lunatic_route2_stage5_unattended_20260727_224146` completed
  frames `1..43371` with 13,953 decisions, maximum 1,529 bullets, accepted
  artifacts, and cleanup. It took 13 hits at
  `[1564,2586,3997,10708,23857,29721,30098,30989,35245,35763,37079,38412,39854]`;
  ten were modeled committed-prefix collisions and three were observed-bullet
  overlaps. Every contact again followed global-kernel exhaustion.
- **Observed issue-path integrity:** Every decision retained an issue
  observation. The 2,419 changed observations produced exactly 2,419
  recertifications and fresh/global transactions, 58 action overrides, 2,361
  preserved planned actions, and zero silent outside-global selections.
  All 13,953 masks, Bomb flags, and action names passed hard no-Bomb.
  Auto-confirm altered 245 decision records. This run exercised no deadline
  hold, whose behavior remains covered by the focused deterministic tests.
- **Comparison boundary:** The 13 contacts are below the 20.5 median of
  previously accepted Lunatic Stage-5 runs, but above the immediately
  preceding run's eight. RNG, phase exposure, density, and post-respawn
  resources differ, so this is observed workload-level progress relative to
  early baselines, not a causal A/B survival improvement from the structural
  extraction.
- **Evidence:** Matching compact run and dossier artifacts. Ignored raw JSONL
  SHA-256 values are
  `14bb67c3f6448a232e338d5067047def7a380814b90fae4ffb2577e49047e1f3`
  for the Hard run and
  `8ea4b761969e978a821ef362163d2be96aa6bfc43be8549eff65d92d0b955a20`
  for the first Lunatic run. The 548,614,220-byte post-override trace has
  SHA-256
  `f6b01748e01eeaceb07aff7f54f703b9dd9e4cf4d184883f23c61d89519e4da6`.

## CE-0138: Stage 6B concentrated contact at boundaries after kernel exhaustion

Status: observed physical survival failure; staged planner-refactor gate
completed

- **Observed high-pressure run:** Supervised no-Bomb run
  `hard_route2_stage6b_unattended_20260727_193155` completed frames
  `1..72862`, 22,140 decisions, route completion, artifact materialization,
  and cleanup. It reached 1,454 active bullets and 256 active lasers and took
  13 native hits at
  `[873,10927,11586,11965,12556,30872,46053,54532,55522,56570,60052,62672,68786]`.
- **Canonical first hit:** Frame 873 was a nonspell observed-bullet overlap
  at player `(376.000,417.100)` with active `up_fast`, 275 bullets, zero
  lasers, and signed pipeline clearance `-2.886`. The global viability kernel
  was exhausted with a nine-frame robust warning.
- **Later discovery evidence:** Ten contacts were observed-bullet overlaps,
  two were modeled committed-prefix collisions, and frame 46,053 was an
  observed-laser overlap during spell 165. Every hit followed global
  viability-kernel exhaustion, with warning leads
  `[9,6,5,14,10,9,7,4,11,5,14,2,6]` frames. Spell 149 contributed four hits
  and spell 169 three; later contacts are pattern/planner evidence rather
  than independent fresh trials.
- **Boundary signature:** Eleven contacts involved a playfield boundary,
  seven used fast movement, and one exceeded 1,000 bullets. Bottom-eight-pixel
  occupancy was 0.237 in the 60-frame pre-hit windows versus 0.151 elsewhere;
  mean selected control-reserve deficit was 9.754 versus 3.659. These are
  correlations, not causal acceptance claims.
- **Structural boundary:** All 22,140 decisions retained the required planner
  groups, zero supplemental failures were serialized, hard no-Bomb passed,
  and all processes cleaned up. This retains the prepare/baseline/
  supplemental/finalize refactor under long mixed-hazard and transition
  pressure but does not rescue physical survival.
- **Correction boundary:** Preserve a non-empty global action kernel before
  the former hit windows, investigate why boundary occupancy remains
  attractive under high control-reserve deficit, and keep bullet, laser, and
  committed-prefix causes separate. Compare phase-specific warning lead and
  position, not aggregate hit counts across RNG samples.
- **Observed Lunatic corroboration:** Post-native-split run
  `lunatic_route2_stage6b_unattended_20260727_213748` completed Final B over
  frames `2..73670`, 22,430 decisions, maximum 1,536 bullets and 245 lasers,
  hard no-Bomb, accepted artifacts, and cleanup. It took 16 hits at
  `[12366,12814,13527,18671,19899,29441,30536,36602,47253,47813,49726,53203,53809,54974,55508,69563]`;
  every hit followed global-kernel exhaustion.
- **Observed cause separation:** The Lunatic contacts classify as seven
  bullet overlaps, six modeled committed-prefix collisions, two laser
  overlaps, and one simultaneous multi-hazard overlap. Spells 154 and 162
  completed active-laser phases without hits. Exact laser contacts were
  retained at frames 30,536 in spell 158 and 47,813 in spell 166; frame
  49,726 in spell 166 overlapped multiple hazards. This rejects treating
  laser presence alone as the cause or globally inflating all laser geometry
  without a phase-specific counterexample gate.
- **Observed boundary signature:** Thirteen of 16 contacts involved a
  playfield boundary, ten used fast movement, and pre-hit bottom-eight-pixel
  occupancy was `0.421` versus `0.157` outside those windows. Mean pre-hit
  control-reserve deficit was `10.868` versus `4.203`. These remain
  correlations, not a causal proof of the recovery mechanism.
- **Evidence:** Matching compact run and dossier artifacts. Ignored raw JSONL
  SHA-256 values are
  `d746c1bcbe3604a32f44ecfbb5f95f22052c8a8de555dbd9906e58872621e29b`
  for the Hard run and
  `5952e485bb26d75493e4b4ff5223e043d1b88de87addd0dd3b45694731306e54`
  for the Lunatic run.

## CE-0139: Lunatic Stage 4A contacted a bullet from a declared unknown future slab

Status: observed physical hazard-coverage and survival failure; post-native-
split structural gate completed

- **Observed high-pressure run:** Supervised no-Bomb run
  `lunatic_route2_stage4a_unattended_20260727_210928` completed frames
  `2..45549`, 15,110 decisions, accepted route completion, compact artifact
  materialization, supervisor completion, and cleanup. It reached 1,528
  active bullets and took 22 native hits at
  `[1174,1553,4081,4492,8984,9506,11484,11899,12648,13429,20747,22408,22882,30100,30586,31340,31754,32519,36073,38423,39649,40468]`.
- **Canonical fresh-attempt hit:** Frame 1,174 was an observed-bullet overlap
  at player `(365.919,415.075)` with active `right_fast`, 332 bullets, and
  zero lasers. Slot 1,376 had AABB clearance `-1.134` in the same retained
  hit observation. The global kernel had become empty at frame 1,112, giving
  62 frames of viability warning, while the short pipeline certificate
  remained positive and provided no collision warning.
- **Observed causal coverage gap:** The last alive decision at frame 1,172
  used snapshot frame 1,171. Its immutable pipeline root explicitly marked
  frames `1172..1203` as `UNKNOWN` with reason
  `th08_unseen_future_hazard_events`. Contacting slot 1,376 was absent from
  that decision's nearby-bullet set and appears in the retained frame-1,174
  set. This is runtime evidence that the declared unknown future-event slab
  can contain a physically fatal event; it is not evidence that the local
  projection or finite recurrence safely covers births.
- **Later discovery evidence:** Ten contacts were modeled committed-prefix
  collisions, nine were observed-bullet overlaps, two were exact same-epoch
  enemy-body overlaps, and one remained sensor-gap/unmodeled-hazard. Every
  hit followed global-kernel exhaustion. Fifteen contacts involved a
  playfield boundary, fifteen used fast movement, and five exceeded 1,000
  bullets. Later contacts are geometry/planner discovery samples after
  respawn, not independent fresh-route survival trials.
- **Structural boundary:** The run exercised the refactored native decoder,
  local hazard kernel, beam reducer, viability families, geometry families,
  pipeline ABI families, compatibility adapter, and internal declarations.
  Hard no-Bomb passed across all 15,110 decisions and the game/controller
  cleaned up. This retains implementation and lifecycle behavior only; it
  does not validate the physical model.
- **Correction boundary:** Unknown future-event slabs remain outside hard
  action authority. Add a causal event/birth coverage model or a conservative
  fail-closed bound that is consumable before issue, then independently
  replay the frame-1,172 root and require a non-empty globally viable
  continuation through the former contact. Do not promote positive
  projected clearance or Python/C++ parity as coverage of an explicitly
  unknown slab.
- **Evidence:** Matching compact run, comparison, and dossier artifacts;
  ignored 457,557,329-byte raw JSONL SHA-256
  `3ac5d31aa4b51359f6352e66bdaf36e3ae629e356f1a25499e404f6beaa8d521`.

## CE-0140: Boolean empty is not stationary or unrestricted exact losing

Status: observed offline finite-model classification counterexample; G3
retained-capsule gate complete

- **Observed Stage-4A counterexample:** Historical Lunatic root
  decision/query/source `761/757/756` in `policy_738_756.npz` was
  trace-Boolean-empty. Exact recursive-cadence belief replay over all 17 root
  actions and all 17 singleton stationary continuations nevertheless retained
  a 32-frame positive witness with margin
  `0x1.eaf6800000000p-3`.
- **Observed Stage-6B counterexample:** Root `410/408/390` in
  `policy_368_390.npz` was also trace-Boolean-empty, yet the same completed
  stationary class retained a 32-frame positive witness with margin
  `0x1.7e38d83ad07c0p-2`.
- **Mode separation:** The first five eligible empty roots in each workload
  also contained a 17/12-frame positive partial witness and an already-unsafe
  zero-prefix root. All six portfolios completed every root action. Selected
  witnesses matched native guaranteed frames with margins inside the existing
  `1e-5` scalar/native tolerance.
- **Rejected inference:** A coarse Boolean-empty label does not certify exact
  augmented-belief loss. Conversely, zero survival in the stationary class
  does not certify unrestricted loss. Without a separate completed
  unrestricted certificate, these roots remain `unresolved`; timeout,
  unvisited candidates, and candidate exhaustion remain unresolved as well.
- **Physical boundary:** This counterexample is exact only for the historical
  17-movement-action capsule model. It omits CE-0134 complete-mask issue
  distinctions and unknown future-event coverage. Stage-4A `103856` also used
  the rejected repeated-counter guard. No live or physical authority follows.
- **Evidence:**
  `notes/G3_STATIONARY_PARTIAL_SURVIVAL_CAPSULE_GATE_20260727.md` and
  `artifacts/viability_audit/g3_stationary_partial_witness_capsule_audit_20260727.json`
  (content digest
  `82ae76afac47f556d01865cba4a0342db6c5b1da44e537e6af7b7a9f28d881f8`).

### Same-session complete-mask extension

- **Observed:** Lunatic Stage-4A physical decision/query/source
  `600/599/598` in run `20260728_005108` joined an exact canonical
  active/held `0x05` root to `policy_582_598.npz`. The live coarse Boolean
  query was empty, but all 36 no-Bomb root actions completed and the exact
  held-mask stationary class retained a 32-frame witness with margin
  `0x1.f87dd20000000p+3`.
- **Boundary:** Every worst path replayed and native labels matched exactly,
  but future-event coverage is `UNKNOWN` from the first successor frame.
  This strengthens the finite-model classification counterexample without
  adding unrestricted feasibility or physical action authority.
- **Evidence:**
  `artifacts/viability_audit/g5_complete_mask_stage4a_20260728.json`.

## CE-0141: Hazard coverage and canonical observation used different roots

Status: observed physical trace-contract failure; construction and physical
recheck fixed; retained pre-fix failure remains authoritative history

- **Observed symptom:** The exact same-session G5 audit rejected 1,613 of
  14,599 available-policy decisions in Lunatic Stage-4A run
  `20260728_005108`. Each rejected row had a valid canonical digest and
  replayable coverage record, but `hazard_coverage.root_frame` differed from
  `canonical_identity.observation.query_frame`.
- **Minimal physical witness:** At decision frame 267 the canonical manager
  frame was 266, canonical query frame was 267, coverage root was 266, and
  coverage declared unknown from 267. Adjacent decisions at 265 and 269
  matched. This is a mixed-root record, not one immutable physical query.
- **Invalid assumption:** The trace-only pipeline builder treated the sampled
  manager/source frame as the hazard-coverage root while the canonical
  observation, player state, and policy query used the later snapshot/query
  frame. A one-frame advance during capture exposed the difference.
- **Correction:** Checkpoint `d5866c4` roots coverage at `query_frame`, the
  observable recurrence root required by the formal coverage contract. The
  manager frame remains separately retained under the open CE-0120 clock
  version. No planner, issue, or action authority changes.
- **Regression tests:** `test_pending_multikey_root_retains_complete_masks`
  now uses manager/query `100/102` and requires coverage root/unknown-from
  `102/103`. The G5 audit continues to reject any mixed root and aggregates
  duplicate failures without hiding their count or bounded samples. Linux
  and Windows quick suites pass `733/733` after adding the retained-artifact
  contract.
- **Evidence:** raw trace SHA-256
  `93037d9febe609accd44eb150150088c29610443783a4434328478409fee41b0`;
  compact audit
  `artifacts/viability_audit/g5_complete_mask_stage4a_20260728.json`.
- **Physical verification:** Post-fix Lunatic Stage-4A run
  `20260728_020910` completed 15,260 hard-no-Bomb decisions and accepted
  15,069 canonical root/capsule joins with zero root validation failures,
  zero missing capsules, and zero coverage/query-root mismatches. The raw
  trace SHA-256 is
  `6473e6706f8378b62dc02e870beffaf026716f98c0f6ea424e7de1c39cd82cd8`;
  the compact passing audit is
  `artifacts/viability_audit/g5_complete_mask_stage4a_postfix_20260728.json`.
  Coverage remains correctly fail-closed `UNKNOWN` from each first
  successor; this closes only the trace construction defect and adds no
  action authority.

## CE-0142: Physical float32 tie paths need not choose the same hidden delay

Status: observed finite-model implementation tie; label/path contract fixed;
no physical action authority

- **Observed symptom:** Physical decision/query/source `612/611/598` from
  Stage-4A run `20260728_005108`, identity
  `8eb661e12d6ab81709ac91bca1a58c3dbf293227828b49ecfd1412af0ffef5cc`,
  root action `th08_mask_54`, produced the same exact successor and guaranteed
  frames but different hidden pickup-delay witnesses at path step 1. Native
  chose delay 2; the Python scalar witness chose delay 4.
- **Invalid assumption:** Margin parity within `1e-5` implied exact equality
  of every deterministic nature tie field on physical coordinates.
- **Evidence:** Native/scalar prefix margins were respectively
  `0x1.3cd5220000000p+4` and `0x1.3cd522339908fp+4`; root bottleneck margins
  differed by one float32 ULP. Both branches use cadence 6 and reach the same
  merged successor. The final Windows delivery reports count two such action
  ties whenever this root occurs.
- **Correction:** Keep exact guaranteed-frame and tolerant margin parity,
  but replay each native path on its own terms: stationary policy choice,
  declared delay/cadence membership, no-write semantics, state links,
  nested-label recurrence, and complete termination. Record deterministic
  scalar/native tie divergence separately instead of rejecting a valid
  equal-label path or silently treating it as exact equality.
- **Regression tests:** Same-process binding tests retain exact randomized
  path parity where no physical precision tie exists. The 18-root Windows
  gate fails any malformed path, unknown action, undeclared uncertainty,
  label mismatch, incomplete action set, stale version, or partial
  publication.
- **Evidence files:**
  `notes/STATIONARY_WITNESS_WINDOWS_DELIVERY_GATE_20260728.md` and the two
  retained P-core affinity reports.
- **Status boundary:** fixed for delivery validation. This does not prove
  physical hazard completeness or add action authority.

## CE-0143: Birth observation passed synthetic timing but failed the physical issue boundary

Status: observed physical delivery failure; corrected by native extraction
and two consecutive GIL-held physical passes under the declared B4 boundary

- **Observed symptom:** Default-off Lunatic Stage-4A trial
  `20260728_031127` completed 14,411 birth-audit decisions with zero observer
  error, but physical observer extraction p95/p99/max was
  `1.7795/2.7495/10.9700 ms`. The fixed gate is
  `0.20/0.40/2.00 ms`. Previous-record JSON emission p95/max was
  `1.2511/13.7303 ms`.
- **Observed workload:** the trace retained 86,396 inactive-to-active edges,
  23 bootstrap candidates, 99 timer regressions, and 17 invalid active
  timers. Bursts reached 592 evidence rows in one decision, but even
  zero-evidence decisions had roughly `1.75 ms` p95 under physical planner
  contention. The earlier isolated 1,536-active benchmark measured only
  `0.0339 ms` p95 and therefore did not represent the issue-thread workload.
- **Invalid assumption:** isolated full-pool scan cost plus interleaved decode
  parity bounded the live cost of repeated NumPy strided scans, Python
  evidence construction, scheduling contention, and JSON publication.
  Worse, the first integration ran the optional observer and classifier
  before the current input dispatch, contradicting the fixed fallback
  boundary.
- **Correction:** move all B1/B3 work after the current input transaction;
  keep the captured pool blob and VM snapshot immutable until then. Retain
  separate extraction and prior-emit tails. Post-issue ECL classification is
  lookup-only against the already warmed immutable instruction cache, so it
  cannot start cold RPM. Compact double-buffer scratch now limits state/age
  to one strided copy each and performs comparisons contiguously. Linux/
  Windows full-pool p95 improved to `0.0171/0.0242 ms`, but 592-birth burst
  p95 remains `2.2671/2.7465 ms`; physical contention and output-linear burst
  cost remain open. The next B4 reports trace-build and pre-emit timing in
  addition to extraction and prior emit. A budget failure remains trace
  failure and cannot gain coverage or action authority.
- **Evidence:** raw trace SHA-256
  `7788114afb988536c9152fe0c9473379d28c59864e86cac4c3ee9b2a829922e5`;
  first deterministic compact report SHA-256
  `65ff30f5363a13ed77df676fe8f829ed8a55948f987191b92915de23c6da2c34`.
- **Physical recheck:** Schema-v2 run `20260728_040144` improved observer
  p95/p99 to `0.4496/0.9314 ms` but retained a `10.2189 ms` maximum and
  therefore still failed the same fixed gate. Evidence per row had
  p95/p99.9/max `33/320/592`; prior-record emission p95/max was
  `1.2484/12.8322 ms`. This rejects treating compact scratch alone as the
  physical fix. Per-birth dataclass construction and repeated-key JSON remain
  output-linear work, while even zero/small-birth rows retain scheduler
  tails. Raw SHA-256
  `c8d25c8b638794db93c1490a07829658d42bc707d1b65f8c674ec499458dec83`;
  deterministic report SHA-256
  `9ce122552d0b35e4379a4accad712ba5960671e2fac6d345a6687b0826a4890c`.
- **Columnar correction:** Schema v3 keeps every candidate in read-only
  columns and lazily materializes scalar witness objects. On Linux/Windows,
  592-birth observer p95 falls from `2.4100/2.5376 ms` to
  `0.1704/0.1528 ms`; record-plus-JSON p95 falls from
  `2.3496/2.3570 ms` to `0.7763/1.0727 ms`, and payload size falls from
  160,077 to 32,956 bytes. The independent scalar transition oracle and v2/v3
  analyzer semantics pass. Scheduler, file-write, and physical contention
  tails remain open until B4 repeats.
- **Schema-v3 physical recheck:** Run `20260728_043724` improves observer
  p95/p99 from `0.4496/0.9314 ms` to `0.3413/0.6625 ms`, but maximum remains
  `10.6158 ms`; the fixed gate still fails. Zero-evidence p95 is
  `0.1960 ms`. Non-empty evidence buckets retain `0.3987..0.4626 ms` p95,
  so isolated columnar cost did not bound scheduler/cold-buffer tails.
  Prior-record emission p95 is `0.0724 ms` after zero evidence but
  `1.3307..1.9791 ms` after non-empty rows, exposing the redundant
  per-evidence flush as a separate next-cadence cost.
- **Schema-v4 correction:** Ordinary birth rows no longer flush independently;
  enabling birth trace forces the same-iteration decision record, whose
  existing flush bounds durability. Observation/intent errors still flush
  immediately. Thread-CPU and wall extraction are recorded separately, but
  only wall time remains the acceptance gate. A scalar small-candidate gather
  brings fixed Linux/Windows 1/8/32-candidate p95 to
  `0.0578/0.0627/0.1038` and `0.0495/0.0790/0.0963 ms`. Physical scheduler
  tails remain open.
- **Schema-v4 physical recheck:** Run `20260728_050305` reduced overall
  previous birth-record emit p95 from `1.1783` to `0.1708 ms`, proving that
  the redundant flush was real. Observer wall p95/p99/max nevertheless
  remained `0.2997/0.5772/10.2234 ms`, so the unchanged gate failed again.
  Windows current-thread CPU samples were quantized at 15.625-ms increments
  and cannot explain sub-millisecond wall samples or weaken the gate.
  Synchronous JSON encode/write remains output-linear: the 321+ evidence
  bucket has p95/max `5.3563 ms`. Raw SHA-256 is
  `cf5161cf34209fd44be85c177ddaf89c5cee7c3bb73be6103f95296a8c834a9f`;
  deterministic report SHA-256 is
  `bcd153b041c046ca1047181b62becdc8f144fc95a42076c94610576bbf23105e`.
- **Next correction gate:** Compare a parity-gated native extractor with an
  exact active-slot handoff from the existing decode path. Either path must
  preserve all transition/status/state/age/geometry columns, ordering,
  independent Python scalar parity, no extra RPM, and fixed wall limits.
  Optional asynchronous serialization may be measured separately, but it
  cannot hide extraction or weaken same-iteration durability.
- **Observed closure:** The parity-gated native extractor preserved the
  independent scalar recurrence and complete ordered output. After
  native-call tail attribution and an explicit `CDLL`/`PyDLL` boundary
  experiment, schema-v7 `gil-held` runs `20260728_065316` and
  `20260728_070838` passed B4 consecutively over 28,907 observations.
  Their p95/p99/max values were `0.1475/0.2021/1.0595 ms` and
  `0.1420/0.1967/0.9087 ms`; neither run contained a sample above 2 ms.
  This closes the physical extraction/delivery counterexample for the
  declared retrospective observer boundary. It does not close birth-source
  coverage, callback completeness, or future-hazard authority.

## CE-0144: Unknown deferred-fire state erased every physical timed intent

Status: observed B5 live-integration omission physically corrected; no timed
birth or geometry authority

- **Observed symptom:** Across the same Stage-4A trace, the active-spell
  main-VM scanner produced 1,641 fire-intent sightings but zero timed events.
  Every visible intent was classified `deferred` because
  `deferred_fire_active=None`; the one deduplicated untimed signature retained
  player aim, dynamic angle, transform, template, origin, minimum-distance,
  pool, and deferred-state dependencies.
- **Observed residual:** all 86,396 activation edges were unmatched. 36,870
  occurred with no active spell main-VM source, while 49,526 occurred inside
  that scope without a timed overlapping intent. Classifier stop rows were
  2,099 unsupported-control-flow and 1,209 horizon.
- **Invalid assumption:** the live integration treated the current deferred
  state as unavailable even though the existing boss-body guard already reads
  enemy flags at `+0x3324`. The classifier correctly refused to distinguish
  immediate fire from descriptor staging; the integration discarded observed
  state it already owned.
- **Inferred static correction:** connected IDA decompilation shows `0x6B`
  sets enemy-flags bit `0x20000`, `0x6C` clears it, direct-fire opcodes
  `0x60..0x68` stage the descriptor while set and otherwise call
  `enemy_ecl_emit_bullets`, and `0x6D` emits the staged descriptor.
- **Correction boundary:** trace schema v2 passes that existing native flag
  only when the boss-guard pointer and all guard/ECL manager-frame endpoints
  are identical. Missing, spanned, or mismatched captures remain unknown.
  This adds no RPM and does not infer state from desired opcode history.
  Child/auxiliary/callback/non-spell sources remain separate residual classes.
- **Authority:** the B5 report is a valid failure report, not event coverage.
  Future geometry, hazard coverage, strategy, and physical action authority
  remain unchanged.
- **Physical recheck:** In schema-v2 run `20260728_040144`, 5,723/5,780
  active-spell main-VM rows had exactly aligned observed state and 57
  capture-spanned rows remained unknown. The classifier produced 1,642 timed
  sightings in 58 deduplicated events, so the discarded-state omission is
  physically closed. Only temporal support was established; every match
  retained unresolved template/origin/aim/pool/transform dependencies.

## CE-0145: Main-VM lookahead explained births in only one Stage-4A spell

Status: observed source-coverage failure; one capture/parser coupling defect
corrected offline, ownership diagnosis and physical recheck open

- **Observed symptom:** Schema-v2 run `20260728_040144` retained 87,673
  activation edges. Only 2,860 had one temporal main-VM intent match and 73
  had multiple matches; all matched edges occurred during spell 69. The
  remaining 84,740 edges were unmatched: 37,767 during nonspell capture and
  46,973 inside an active-spell scope without an overlapping timed main-VM
  intent.
- **Observed classifier boundary:** Across the run, lookahead stopped at the
  horizon 1,230 times and at unsupported control flow 2,164 times. The
  current trace intentionally scans only the active spell owner's main VM
  and omits child enemies, auxiliary VMs, callbacks, nonspell sources, and
  dynamic source topology.
- **Invalid inference:** unmatched temporal edges do not prove that the
  main-VM classifier missed a visible direct-fire instruction. They can be
  produced by an omitted source or lie beyond a deliberately fail-closed
  branch/loop boundary. Conversely, the 3.2621% unique temporal fraction is
  not a prediction-success rate because every match still has unresolved
  geometry and source competition.
- **Correction gate:** attribute intent sightings and stop reasons by phase,
  retain instruction/control-flow witnesses around each stop, and establish
  source ownership before extending the interpreter. Any loop/call support
  must model the observable VM stack/register state causally; it may not
  guess hidden branches. All-enemy or auxiliary-source scanning requires a
  separate capture, delivery, and contention contract.
- **Authority:** future-event coverage remains `UNKNOWN` from the first
  successor. This counterexample authorizes diagnostics only.

## CE-0146: Header-only ECL instructions erased a valid main-VM snapshot

Status: parser and capture coupling physically corrected; downstream
callback-horizon coverage remains open

- **Observed physical residual:** The enhanced schema-v2 source report found
  2,386 decision rows whose callback lookahead failed with
  `ValueError: process read buffer size must be positive`. These included
  every active-main-VM row in spells 61 (823) and 65 (1,124), plus 91/101/247
  rows in spells 57/69/73. The birth classifier received no snapshot on those
  rows.
- **Invalid implementation:** `EclInstructionCache.instruction` validated a
  legal 12-byte header-only instruction and then invoked the process reader
  with `size=0`. The Windows reader rejects non-positive reads. A broad
  controller exception path then set both callback lookahead and the already
  observed `EclVmSnapshot` to `None`.
- **Correction:** Zero payload is now represented by `b""` without process
  I/O. `th08_live.ecl_capture` separates VM capture from callback
  classification: a classifier error retains the immutable snapshot, empty
  callback events, and explicit error. A strict deterministic reader fixture
  rejects zero reads and all three capture/success/failure paths are tested.
- **Potential impact:** Correct parsing can restore velocity-callback hazard
  events as well as post-issue birth-intent diagnostics. This is therefore
  not merely trace-schema plumbing and is not physically promoted from unit
  tests. The next Stage-4A gate must retain per-phase callback outcomes,
  geometry/action timing, hits, hard no-Bomb, and deterministic birth
  residuals.
- **Authority:** no new future-hazard coverage or action authority follows
  until the physical recheck.
- **Physical recheck:** Schema-v3 run `20260728_043724` has no callback read
  error and retains a birth-classifier result on all 6,101 active-main-VM
  rows. Spell 61 contributes 434 timed sightings and 3,054 temporal matches.
  This closes the zero-read/snapshot-erasure defect only; it does not validate
  empty callback results or omitted birth sources.

## CE-0147: Instruction-limit callback lookahead was consumed as an empty event list

Status: observed incomplete model result; invalid prefix consumption
physically corrected, unresolved suffix remains open

- **Observed physical workload:** On all 1,261 spell-57 rows in schema-v3 run
  `20260728_043724`, callback lookahead scanned the maximum 256 instructions,
  returned `stop_reason=instruction_limit`, reported no callback events, and
  did not cover the 80-frame horizon. It scanned 322,816 instructions in that
  phase; read/lookahead p50/p95/max was `0.2761/0.5387/3.1771 ms`.
- **Invalid model use:** The live lowering consumes
  `ecl_lookahead.events` even when `horizon_covered` is false. An empty tuple
  after instruction exhaustion is therefore treated like no future velocity
  callback, although the algorithm only established that none occurred in
  the visited prefix. This is optimistic/unknown-direction omission.
- **Additional scope:** Spell 73 stopped at an exact repeated state on 968
  rows. A repeated-state proof may eventually certify a periodic no-event
  suffix, but the current result does not label that proof or propagate a
  coverage certificate. Spells 61/65/69 reached horizon or terminate and are
  separate cases.
- **Correction gate:** represent callback coverage as complete/incomplete
  over an exact frame support. Incomplete results must leave affected future
  transform geometry `UNKNOWN` and cannot hard-authorize the current
  trajectory. Improve canonical control-flow traversal, caching, or a
  separately bounded native data plane without reducing the instruction cap
  or silently dropping branches. Retain a minimal spell-57 instruction/VM
  fixture and compare it with runtime callback/transform evidence.
- **Implemented correction:** Callback and birth-intent results now carry
  requested horizon, stop frame, covered-through frame, and first unknown
  frame. Only `horizon` and `terminate` expose `complete_events`; incomplete
  prefixes are retained for trace but never lowered, and the compatibility
  API raises `IncompleteEclLookaheadError`. Schema v8/audit v6 fail closed on
  inconsistent coverage, stop reason, result kind, or lowering status.
- **Retained legacy re-audit:** Schema-v7 run `20260728_070838` contains
  3,723 legacy-declared complete rows and 2,405 legacy-declared unknown rows.
  The latter used the old unchecked schedule interface; 975 contain tagged
  bullets and the maximum is 1,367. The exact split is 1,350
  `instruction_limit` rows with zero tagged bullets and 1,055
  `repeated_state` rows, 975 with tagged bullets. Recorded event tuples are
  empty in all 2,405 rows.
- **Remaining falsifier:** A schema-v8 physical trace must show that every
  incomplete result is labeled `UNKNOWN`, preserves any prefix separately,
  and lowers zero prefix events. That does not establish safe geometry after
  `unknown_from_frame`; repeated-state proof, a conservative containing
  envelope, or certificate unavailability is still required.
- **Physical semantic recheck:** Accepted schema-v8 run `20260728_075455`
  validates all 14,903 audit rows and all 6,089 active-main-VM decision
  joins. It records 3,763 complete and 2,326 unknown callback rows. Every
  unknown row is `incomplete_prefix_not_lowered`; prefix and lowered event
  totals are both zero. Spell 57 contributes 1,313
  `instruction_limit`/unknown rows. Spell 73 contributes 1,013
  `repeated_state`/unknown rows and 125 complete horizon rows. Of all
  incomplete rows, 936 contain tagged bullets, maximum 1,360.
- **Authority:** this counterexample does not prove that a missing callback
  caused a hit. The invalid empty-schedule consumption is corrected, but the
  unknown suffix is still not a complete physical-hazard answer and grants no
  action authority.

## CE-0148: Per-call ctypes allocation created a periodic native-observer GC tail

Status: observed isolated performance failure; pointer/view reuse corrected
offline, physical recheck pending

- **Observed symptom:** The first one-pass native birth extractor had
  full-density p95 near `0.03 ms`, but repeated Windows fixed profiles failed
  the unchanged `2.00 ms` maximum. A 5,000-call zero-density probe placed a
  `5.4094 ms` outlier at call 1,741. The pre-fix all-profile benchmark
  reported `5.4165 ms`.
- **Rejected diagnosis:** Pinning the benchmark thread to preferred CPU 11
  still produced a `4.8275 ms` maximum. The tail was not evidence that the
  C++ slot scan needed more affinity or a weaker deadline.
- **Observed cause separation:** Running the same probe with cyclic GC
  disabled reduced maximum to `0.2859 ms`. The wrapper created a NumPy blob
  view, ctypes pointers, two count scalars, and byref objects on every call;
  the accumulated tracked allocations triggered a collection inside the
  observer timing boundary. Disabling GC was rejected because it could move
  unbounded cleanup or cyclic retention elsewhere in a long controller run.
- **Correction:** `NativeBulletBirthTracker` now owns and reuses the exact
  persistent blob view/pointer, all array pointers, and result-count storage.
  With GC enabled, the same 5,000-call probe has maximum `0.0988 ms`.
  Linux/Windows full-density p95 is `0.0120/0.0109 ms`; 592-birth p95 is
  `0.0570/0.0452 ms`; every density/burst profile passes
  `0.20/0.40/2.00 ms` without affinity.
- **Evidence:** The rejected CPU-11 report SHA-256 is
  `0fe659c65a22d850c7b4db0f98e9419a620344702c496bba5a7c500ca04c05f3`.
  Final Linux/Windows report SHA-256 values are
  `bfb106b6970f98610c2537cd40113a81d1cd6ef0a7ac1b751ec9c943b71dc667`
  and
  `1f73455491c8ccb83d1a53ab7a8c2c0f1792ebf2844f91faa4920de5adebcd63`.
- **Authority:** This closes the isolated wrapper tail only. It does not
  establish physical B4, future-event coverage, or action authority.

## CE-0149: Native extraction passed physical percentiles but retained a 9-ms wall tail

Status: observed physical performance failure; correction physically
verified by two consecutive passes under the declared B4 boundary

- **Observed symptom:** Explicit-native schema-v5 run
  `lunatic_route2_stage4a_unattended_20260728_055104` completed an accepted
  hard-no-Bomb Stage-4A route, but observer wall maximum was `9.0498 ms`
  against the unchanged `2.00 ms` limit. The deterministic audit therefore
  returns `passed=false`.
- **Observed improvement:** p50/p95/p99 fell to
  `0.0545/0.1393/0.2111 ms` from schema-v4
  `0.1284/0.2997/0.5772 ms`. This is the first physical run to pass both
  percentile limits and validates that the native data plane fixes the
  steady cost.
- **Rejected explanation:** Sixteen observations exceed `2.00 ms`. Ten have
  zero evidence; the remaining six have only 4, 6, or 20 rows. No tail
  sample is a 592-row burst, so output-linear evidence copying is not a
  sufficient cause.
- **Observed attribution:** Schema-v6 physical repeat
  `lunatic_route2_stage4a_unattended_20260728_062321` records 17 observations
  above `2.00 ms`; every one is dominated by native-call wall time. Native
  call p50/p95/p99/p99.9/max is
  `0.0365/0.0603/0.1125/2.1281/8.2585 ms`, while
  prepare/materialization/controller-residual maxima are
  `0.0703/0.7076/0.2362 ms`.
- **Observed exclusion:** All nine phase/generation GC completion totals are
  zero across 14,868 observations. Evidence counts in tail rows are only
  `0, 4, 10, 20, 33, 48`. Python materialization, cyclic GC, and large-burst
  copying are not supported as the remaining cause.
- **Inference boundary:** A released-GIL call-boundary scheduling effect is
  plausible because normal native-call p50 is only `0.0365 ms`.
  Scheduler/preemption events were not directly traced, so an OS cause
  remains hypothesized.
- **Next falsifier:** Compare explicit GIL-held and GIL-released calls while
  preserving the same C++ recurrence/output, independent scalar parity, GC,
  unpinned controller, and fixed wall gate. A retained native-call tail in
  the held mode falsifies Python-thread GIL handoff as a sufficient cause.
- **Offline correction status:** Separate `CDLL`/`PyDLL` loaders, schema-v7
  call-mode provenance, exact three-way parity, and all fixed unpinned
  Linux/Windows profiles pass. This makes one `gil-held` Stage-4A diagnostic
  eligible; it does not yet close the physical failure.
- **Observed physical correction:** Explicit `gil-held` schema-v7 runs
  `20260728_065316` and `20260728_070838` pass consecutively over
  13,896 and 15,011 observations. Their native-call maxima are
  `0.5008/0.4384 ms`; total observation maxima are `1.0595/0.9087 ms`;
  neither run has an observation above 2 ms or an overlapping completed
  cyclic-GC collection. This rejects the previously frequent released-call
  tail under the declared unpinned, GC-enabled workloads.
- **Evidence:** Raw trace is 510,433,900 bytes with SHA-256
  `ed4fbbb932e12ac7ef7f3e4b560fad1fa7dc8b0428c712edc5a02ec1c09b7a79`.
  Canonical deterministic report SHA-256 is
  `1689bf8468b9129b16aaf1aeacee7b569975a4302a92ab7860ef77c4665a84ec`.
  The schema-v6 raw trace is 483,475,546 bytes with SHA-256
  `9f075f795327e6e1669b2cf18e0cfd28656a87ced1212cddf2ff3157b0dacc30`;
  its canonical deterministic report SHA-256 is
  `c0e71b3660651e11e15e3a924bef0d1f22adc49a3513bbc7ab39b83528d3e008`.
  The second held raw/audit SHA-256 values are
  `ee7b1f1048746a690bf9a6445297d0f8d517975547edbc78ee693e6193335f12`
  and
  `acdd2e25d04b3a69b1a20e4f5d6a7f83f4a1409350f3960d3f569ec9f0a53bd0`.
- **Authority:** The specific B4 native-call tail is closed. The evidence
  does not prove the scheduler mechanism, rule out every possible future
  preemption, close CE-0147, or grant future-hazard/physical action
  authority. A later over-budget held observation reopens this
  counterexample.

## CE-0150: Block-ordered decode ratio flipped across identical adjacent runs

Status: observed isolated benchmark failure; ABBA pairing corrects the
measurement design offline

- **Observed symptom:** After adding schema-v6 attribution telemetry, the
  first unpinned Windows benchmark passed all eight observer profiles but
  failed the combined gate because decode p95 was measured as two separate
  blocks: baseline `8.0259 ms`, later interleaved `8.6458 ms`, ratio `1.0772`.
- **Adjacent contradiction:** An immediately repeated identical command also
  passed all observer profiles, but the block ratio flipped to `0.9398`
  (baseline `8.9540 ms`, interleaved `8.4152 ms`). The telemetry did not
  alternately speed up and slow down the decoder; block drift dominated the
  ratio.
- **Rejected practice:** Repeating the command until one block ratio passes
  and retaining only that run is not a nonregression gate.
- **Correction:** Benchmark schema v5 uses an ABBA pair inside every
  iteration: baseline, interleaved, interleaved, baseline. Each distribution
  receives the mean of its two adjacent measurements before the unchanged
  p95 ratio and `1.05` limit are applied.
- **Observed correction:** Linux paired ratio is `1.0123`. Two adjacent
  Windows paired ratios are `1.0156` and `1.0248`; all observer and combined
  gates pass without affinity. This corrects first-order block drift, not
  arbitrary scheduler noise.
- **Evidence:** Rejected Windows report SHA-256 values are
  `99fca1972e9ea7f9cd5fd39baafefae7838965de08467aa985794a42baeaa66e`
  and
  `64ead5b3a69f7f59468204daf58caff70549ecca419d6b6e7d74e3161b2949b4`.
  Paired Linux/Windows/Windows-repeat SHA-256 values are
  `e4a08ff7d7b2fa3b5f753dc800786040613b298363dc2d4d7c79b0668f2df8f6`,
  `713a6bff6fd4181802f52f30308c513624923244b335fafaf67f94be7e0a731e`,
  and
  `8563fe93ba758a8aed2354ba7dacda979a8286d763c2076d15834b9b7b8d49e8`.
- **Authority:** This repairs isolated measurement pairing only. It does not
  close CE-0149 or grant physical action authority.

## CE-0151: Residual-audit v5 validated schema v7 but omitted its native diagnostics

Status: observed report aggregation failure; corrected and regression-tested

- **Observed symptom:** The first `gil-held` physical audit returned
  `passed=true` and correctly reported 13,896 schema-v7/native/held rows, but
  `native_diagnostics.rows` was zero with empty segment distributions.
- **Cause:** `_validated_audit` correctly accepted and reconciled diagnostics
  for schemas 6 and 7. The later aggregation loop still used
  `schema_version == 6`, silently excluding every valid schema-v7 diagnostic
  from the compact report.
- **Preserved evidence:** The 483,745,822-byte raw trace contains all
  per-row segments and GC counters. No physical rerun or inferred replacement
  data was needed.
- **Correction:** Aggregation now uses `{6, 7}`. The schema-v7 audit test
  requires four native diagnostic rows in addition to valid held-mode
  provenance, so a future validation/aggregation split fails loud.
- **Verification:** The focused audit suite passes 9/9; complete
  Linux/Windows suites pass 801/801 in `9.202/15.761 s`, with three existing
  Windows skips. Two corrected generations from the same raw trace are
  byte-identical at canonical LF SHA-256
  `8f77c0afeaa8b7a31730f9ca799cd6c369f45edc695187e79a1c6ad31001b737`.
- **Authority:** The corrected report supports one candidate B4 pass. It does
  not erase the two-pass requirement, close CE-0147, or grant action
  authority.

## CE-0152: A GIL-held observer incurred an isolated materialization wall tail

Status: observed physical performance failure; schema-v9 attribution shows a
corridor-completion correlation with mixed scheduler/executed-work evidence,
while the latest normal-priority repeat fails p95 without that transition

- **Observed symptom:** Accepted schema-v8 Stage-4A run `20260728_075455`
  passes callback/intention validation but fails the unchanged B4 observer
  maximum. Observation p50/p95/p99/p99.9/max is
  `0.0636/0.1448/0.2007/0.3858/8.9834 ms`.
- **Observed segment:** Exactly one of 14,903 observations exceeds `2.00 ms`.
  At nonspell frame 15,809 it has 24 evidence rows and spends
  `0.0019/0.0335/8.9333/0.0147 ms` in
  prepare/native-call/materialize/controller-residual. Native-call maximum
  over the full run remains `0.3911 ms`, so CE-0149's released-call mechanism
  did not recur.
- **Rejected output-size explanation:** Adjacent 24-row materializations at
  frames 15,793, 15,801, 15,817, and 15,824 take
  `0.0741/0.0575/0.0527/0.0707 ms`. The next-highest 20–28-row
  materialization in the run is `0.2658 ms`; 24 rows do not explain
  `8.9333 ms`.
- **Observed exclusion:** No completed cyclic-GC collection overlaps any
  observer phase. Windows thread CPU telemetry remains too coarse to
  distinguish executed copying from descheduling. OS preemption or
  background native-worker contention is therefore hypothesized, not
  observed.
- **Schema-v9 falsifier outcome:** Accepted Stage-4A run `20260728_083433`
  retains valid Windows current-thread cycles on all 13,842 native rows and
  again fails B4 at p95/max `0.2039/5.1274 ms`. Its only three ambiguous
  endpoint rows are all `corridor_future: inflight -> done`; they are exactly
  the complete run's three largest materialization walls at
  `5.0415/4.2546/1.1657 ms`. The next-largest materialization is
  `0.4756 ms`, and definite-overlap maximum is `0.4270 ms`.
- **Mixed cycle evidence:** The 6- and 3-evidence transition rows use
  `271,960/311,714` materialization cycles, ordinary-to-p95 for their
  1–8-evidence bucket. The 25-evidence transition uses `646,576` cycles, the
  9–32 bucket and run-wide maximum. This supports a completion/GIL handoff
  with one mixed executed-work sample; it rejects pure output-size scaling
  but does not prove that the corridor worker caused the OS schedule.
- **Diagnostic overhead:** Schema-v9 p95 also marginally exceeds `0.20 ms`.
  Future endpoint and cycle telemetry remains inside the declared wall
  boundary and may not be subtracted to claim a pass.
- **Latest normal-priority repeat:** Fresh ECL-control run
  `20260728_101804` again fails only p95:
  `0.1018/0.2018/0.3326/0.5441/0.7539 ms`
  p50/p95/p99/p99.9/max. There are no over-2-ms rows, no completed GC, valid
  Windows cycle attribution on all 14,126 rows, and no endpoint transition.
  Segment p95/max values are `0.0065/0.0940` prepare,
  `0.0593/0.6459` native call, `0.0823/0.5023` materialize, and
  `0.0720/0.5382 ms` residual. This does not reproduce the prior
  corridor-completion correlation and does not authorize selecting the lower
  maximum as a closed B4 result.
- **Related trace cost:** The same run's pure-Python callback traversal is
  also expensive on incomplete paths. Spell-57 read/lookahead
  p50/p95/p99/p99.9/max is
  `0.2868/0.5460/0.8128/1.9979/10.3328 ms`; spell 73 maximum is
  `2.5051 ms`. This does not violate the narrow birth-observer gate but is
  part of issue-thread performance debt.
- **Next falsifier:** Fix a separate default-off corridor-worker priority
  intervention using the existing tested `background_low_priority` seam.
  Preserve recurrence, worker count, native worker limit, GC, unpinned
  controller, observer output, issue semantics, and fixed wall limits.
  Reject it if solve/publication age, viable-query coverage, action lag, or
  first-hit warning degrades.
- **Evidence:** Raw trace is 503,847,529 bytes with SHA-256
  `4f0d1cb39c3f125998cd9d2b3b36ef5366cf8683d97d5e37e63e98f01892f908`.
  Two audit generations are byte-identical at canonical LF SHA-256
  `a620ec0077820ec7516138bc4051fa9d7fd36549af43262d90d011e2ed2599ea`.
  The schema-v9 raw trace is 477,513,549 bytes with SHA-256
  `a01d0b172415b2c19759e11bfa03c68936f209827331dd8381d4bacf2232e82a`;
  two audit generations are byte-identical at SHA-256
  `0b2dcad76644b90ce39c0922b5a82b41b5a09cd2c403ecd8048440c4462b9961`.
- **Authority:** The fresh failure reopens B4 regression status despite the
  two earlier passing runs. It does not invalidate their native-call
  attribution, alter callback coverage authority, or support a survival
  comparison.

## CE-0153: Lowering the corridor parent removed the transition witness but failed fixed delivery gates

Status: observed physical intervention failure; rejected after the first
precommitted run

- **Observed application:** Priority-on Stage-4A run `20260728_092619`
  completed frames `2..44999` with 14,649 decisions. All 1,900 unique
  corridor solutions report the below-normal parent priority and the
  unchanged four-worker native limit applied.
- **Observed failure:** Observer p95 is `0.2049 ms`, above the fixed
  `0.200 ms` limit. Expired-policy fraction is `36/14562 = 0.2472%`, above
  the fixed `0.20%` limit. The deterministic priority audit therefore passes
  application but fails delivery.
- **Missing falsifier witness:** Observer maximum fell descriptively from
  `5.1274` to `0.8925 ms`, but none of 14,649 rows retained a corridor
  `inflight -> done` endpoint. The contract required at least one such row.
  Without it, the lower maximum cannot be attributed to completion priority
  and may not be selected as a passing result.
- **Preserved controls:** Solve p95/max `302.3068/407.8457 ms`,
  first-observed age median/p95 `2/4`, no-query/queryable fractions
  `0.8309%/99.1622%`, zero support-uncovered query, local-plan p95
  `17.9999 ms`, and action-lag p95/max `2/3` all pass. No observer row
  exceeds `2 ms`; no completed GC overlaps it.
- **Physical boundary:** The accepted route completed with 18 hits and hard
  no-Bomb. The first hit at frame 1,299 followed viability/robust exhaustion
  at `1,259/1,290`, retaining positive `40/9`-frame warnings. All contacts
  followed global-kernel exhaustion; hit count remains a descriptive,
  RNG-distinct workload result.
- **Rejected inference:** A lower single-run maximum with no matching
  completion transition does not prove that below-normal parent priority
  removed the CE-0152 mechanism. Do not run-select a second sample after the
  fixed p95 and expiration failures.
- **Correction boundary:** Keep the option default-off for reproduction.
  Reopen performance work through a new causal contract; prioritize exact
  memoized/transfer-summary ECL callback traversal because it combines
  issue-thread latency with the still-open incomplete future-event boundary.
- **Evidence:** Raw SHA-256
  `cedcc97153373bee1758b8dc0a0e4e8ad3879f0c3647091cb27250390a827e12`;
  priority/birth audit SHA-256 values
  `5a2d0884147f12bbd18ce66cae4b9ebdcefd8c9b19034e73fd14731e95716686`
  and
  `3bcbf3e25667c9f5f2efa6ba57a4dd2899dafbf10e0207e08562b8a1a6ff2dab`.

## CE-0154: Callback traversal declared complete after skipping hidden ECL branches

Status: observed deterministic and retained-trace model failure; fail-closed
correction implemented, offline validated, and fresh physical runtime scope
validated

- **Minimal falsifier:** Put an eligible `loop_decrement_jump` (`0x05`) or
  conditional jump (`0x28..0x33`) before two successors, place callback 12
  only on the branch, omit the local/dynamic operand from `EclVmSnapshot`,
  and put the encoded fallthrough's next timestamp beyond the horizon. The
  old scanner skipped the branch opcode and could publish a complete empty
  schedule although an observation-compatible physical successor invokes
  the callback.
- **Observed native dependency:** IDA shows spell 73's opcode `0x33` reads
  ECL variable `10050`, the Euclidean distance between the current global
  player and enemy positions. Spell 57's opcode `0x05` reads/decrements VM
  local state, including a loop initialized from gameplay RNG. Neither
  future dependency is in the current snapshot.
- **Observed retained scope:** Replaying 5,788/5,803 callback rows from
  physical run `20260728_092619` finds 1,996 old
  `complete:horizon` rows that cross unsupported control: all 997 replayed
  spell-61 rows and 999/1,035 spell-65 rows. This is a concrete completeness
  failure, not only a performance inefficiency.
- **Correction:** Callback traversal now stops at unsupported timer reset,
  loop/conditional control, and call/return. Incomplete prefixes remain
  unavailable to lowering. No unknown row becomes complete.
- **Performance effect:** Total retained-scope instruction work falls
  `563,466 -> 58,204` (`89.6704%`). Spell 57 falls
  `344,320 -> 3,155` (`99.0837%`), maximum 26 instructions per row.
  Linux/Windows 10,000-iteration spell-57 p95 is
  `0.0223/0.0307 ms`.
- **Former evidence gap:** Fifteen late spell-73 transition rows cannot be replayed
  from the retained decoded file because its bytes are not aligned with the
  then-live runtime instruction image. That historical audit correctly
  remains failed rather than inferring them.
- **Observed physical closure:** Fresh normal-priority run
  `20260728_101804` exercises the corrected live image over 5,749 callback
  rows. Exactly 1,442 are complete horizon rows and 4,307 stop
  `unsupported_control_flow`; no row uses `instruction_limit` or
  `repeated_state`, and every incomplete prefix is not lowered. All 25
  phase-end rows validate, closing the prior runtime-transition class without
  rewriting the historical failed audit. Spell-57 has 1,308/1,308
  unsupported-control rows and a maximum of 26 inspected instructions.
- **Physical contacts:** The route completed with 13 hits at
  `[3919, 4271, 9854, 11602, 12243, 13162, 20611, 21058, 21383, 29548,
  30483, 34070, 38026]` and hard no-Bomb. The first hit is the canonical
  fresh-attempt witness; all 13 follow global viability exhaustion. This
  trace-only correction does not establish a hit reduction.
- **Evidence:** Deterministic replay report SHA-256 is
  `99f17fbc0a98a5bb9c2711c98e52bef00f3703566d97a26a0e59cfbb10f1edd1`.
  Linux/Windows benchmark SHA-256 values are
  `c4ab3cd721b7cf9ce9cb8c62f17366f4b3527a8f780af8be749ef72bfe6ceaaa`
  and
  `89174afc0565dacda7345bb128face3b4ad3892dece153b8d05f092cf522aaa7`.
  The fresh physical ECL audit is byte-identical across two generations at
  `e1d89da6cee5aced7a87187bde950a2d3fed2303292a366621134526bc963210`.
  Complete pre-physical suites pass 823/823 on both systems.
- **Authority:** This correction shrinks callback completeness and reduces
  issue work. It does not model the hidden branches, bound their callback
  effects spatially, prove survival, or add action authority.

## CE-0155: Observed ECL loop locals did not restore viability or close B4

Status: observed physical Stage-4A counterexample; capture correction
validated, survival and performance failures remain open

- **Observed physical counterexample:** Fresh normal-priority Lunatic
  Stage-4A run `lunatic_route2_stage4a_unattended_20260728_110438` completed
  hard no-Bomb with 14 hits at
  `[2189, 4221, 8883, 9533, 9959, 11488, 13337, 13845, 21517, 33483, 36211,
  36901, 37425, 40372]`. Frame 2189 is the canonical fresh-attempt witness.
  Thirteen contacts follow global viability exhaustion.
- **Distinct late failure:** frame 33483 is an enemy-body overlap after
  positive causal margin (`pipeline 17.837`, robust 6.394) and is classified
  `late_collision_after_positive_causal_margin`. It remains a separate
  sensing/latency/body-transition counterexample, not evidence that the local
  projection changed behavior.
- **Observed state-alias correction:** every one of 5,615 callback rows has a
  valid projection. Variable `10036` takes 12/33/13 distinct values in spells
  57/61/65, proving that the old seven fields merged physically distinct
  loop-control histories.
- **Rejected inference:** making those locals observable does not itself
  complete hidden control, produce a viable action, or reduce hits. Coverage
  remains 1,490 complete / 4,125 unknown and phase A is trace-only.
- **Performance counterexample:** native observer p95 is `0.2059 ms` against
  the fixed `0.2000 ms` B4 limit. No completed GC or dominant segment explains
  the miss. Do not claim the 40-byte read is free, but do not attribute the
  cross-run ECL delta without matched paths.
- **Correction boundary:** retain phase-A capture. Build an independent scalar
  oracle for only exact local opcode `0x05` histories, and separately
  attribute matched-path decode/read work. Keep calls, interrupts, dynamic
  `10050`, auxiliary VMs, and unsupported writes unknown.
- **Evidence:** raw/projection/control/birth SHA-256 values are
  `aa86ba40f2b2141ff5212ffca7374d27d73ca6680c21cad22e09a9520ad1cf9e`,
  `cbfb75db83988e48b1c5305124a31383218c426df3bcde18e9a6d3f34ed09b3e`,
  `aedbe0fece76b7cf4bfe8722babd1093694e07b4e6ee4da33547157bd97166ba`,
  and `91c25c9594e8a5711bb5cf742765bd5b46741436ef55ae96d204dde198d0cccb`.

## CE-0156: Cycle bookkeeping reduction passed p95 but not physical B4 maximum

Status: observed physical performance counterexample; optimization retained,
B4 open

- **Observed physical gate:** Fresh unchanged normal-priority GIL-held
  Stage-4A run `20260728_121028` completed 14,066 decisions with hard no-Bomb,
  accepted route completion, and exact cleanup.
- **Mixed result:** Observation p50/p95/p99/p99.9/max is
  `0.0983/0.1986/0.3400/0.5439/8.3269 ms`. The optimized path now passes the
  fixed `0.20/0.40 ms` p95/p99 limits, but two materialization tails exceed
  the `2.00 ms` maximum.
- **First tail:** Frame 11969 uses `8.2328/8.3269 ms` in materialization for
  four evidence rows. Its `373734` materialization cycles are ordinary for
  the 1–8 evidence cohort; corridor remains `inflight -> inflight`, and no GC
  completes. This supports descheduling/contention rather than output-size or
  executed-cycle growth.
- **Second tail:** Frame 38043 uses `4.9519/5.0455 ms` in materialization for
  48 evidence rows. Its `681916` materialization cycles are the run maximum
  and the corridor Future changes `inflight -> done`. This supports executed
  completion/GIL-handoff work in addition to wall scheduling.
- **Rejected inference:** The offline Windows p95 improvement and fresh
  physical p95 pass do not establish bounded maximum latency. Conversely,
  these two mixed tails do not identify one worker or justify re-enabling the
  rejected priority intervention.
- **Correction boundary:** Retain the exact cycle-delta optimization. Keep
  B4 open. Any native-output validation shortcut needs a separate invariant
  gate; any process isolation or publication-worker change needs a
  precommitted causal delivery experiment with unchanged correctness,
  cadence, and fallback gates.
- **Evidence:** Birth audit SHA-256 is
  `c4a715c0e50f6af8b0d712cfe36ae1a2697173aec49369b3dd93601b91382e9d`;
  raw local trace SHA-256 is
  `e15fc270fdb2afe188987aa8f22798f36cbc6da8e07192a2c4af0aed132fe43d`.

## CE-0157: A stale ECL file mapping can decode plausible later instructions

Status: observed offline evidence-accounting counterexample; conservative
mapping-epoch correction implemented

- **Observed trigger:** Static replay of physical run `20260728_121028`
  encounters an invalid instruction size at spell-73 frame 44212, proving
  that the retained decoded Stage-4A file is no longer byte-aligned with the
  late runtime instruction image.
- **Old failure:** The auditor treated each later row independently. At
  frames 44216, 44246, and 44266, the stale file bytes at the reused runtime
  addresses happened to form valid instructions and produced three false
  `unknown:unsupported_control_flow -> complete:horizon` transitions.
- **Minimal falsifier:** Place an invalid header before a later byte-aligned,
  syntactically valid future instruction in one retained static image. After
  the first mapping failure, independently replaying the later address can
  manufacture a complete result from a mapping already disproved by the
  trace.
- **Correction:** The first decode/read failure now invalidates the static
  runtime-to-file mapping for all later callback rows. The corrected audit
  excludes 27 late rows, reports zero unknown-to-complete transitions, and
  deliberately still fails its all-rows and no-unknown-exclusion gates.
- **Required future evidence:** Retain raw instruction bytes or an immutable
  runtime image/version identity at the callback capture before attempting
  to recover these late rows. Do not infer validity from a plausible static
  decode.
- **Evidence:** Corrected deterministic audit SHA-256 is
  `b8b8695fcf710c693201a87ecb99840c33e569fbf68e8236653e7b213142d839`.
- **Authority:** This only prevents optimistic offline evidence. The live
  scanner already remained fail-closed; no schedule, geometry, or action
  authority changes.

## CE-0158: Stage-5 pre-hit loss episodes outlived the restricted horizon

Status: observed physical survival counterexample; exact Stage-5 capsules
retained, future-hazard coverage still blocks action comparison

- **Observed run:** Lunatic Stage-5 workload
  `lunatic_route2_stage5_unattended_20260728_124930` completed frames
  `1..44593` over 13,326 decisions with 15 hits, hard no-Bomb, accepted
  automatic transitions, `route_complete`, exact key release, and no residual
  process.
- **Canonical causal witness:** The run has earlier short Boolean-empty
  episodes that later return to viable. The viable-to-losing transition of
  the episode containing the first native hit is frame 2049. Contact occurs
  at frame 2167, 118 frames later, at `(8.000, 424.000)` with active input
  `up_right_fast`, 657 bullets, and observed slot-1357 overlap/AABB clearance
  `-2.202`.
- **Observed fallback path:** The frame-2049 query is already losing while
  some repair volumes remain positive; it selects `down_right_fast`. At frame
  2163 the root is still losing, distant recovery distances are hundreds of
  pixels, and selected `up_fast` has two predicted committed-prefix
  collisions with minimum clearance `-2.602`. Frame 2165 selects
  `up_right_fast` with one predicted collision. The frame-2167 newly issued
  `right_fast` occurs after hit detection and is not the causal active input.
- **Route-wide recurrence:** All 15 contacts are classified
  `global_viability_kernel_exhausted_before_hit`; 8,494 of 13,146 available
  queries have empty action sets. Spell 107 contributes six later contacts,
  including warning leads of 120 and 81 frames. These later deaths are
  geometry/planner discovery evidence, not independent initial-stock clears.
- **Rejected explanation:** This is not principally a missing-policy-query or
  unsupported-delay sample. The run has zero queried supports outside the
  cached policy, only 24 expired statuses, and 104 robust decisions without a
  query. The canonical root remains post-loss for far longer than the
  ordinary query/pickup age.
- **Model gap:** Current repair-volume and distant-kernel ranking provide
  geometric direction after a Boolean loss but carry no completed causal
  survival label. They cannot distinguish a continuation that survives 17,
  32, or more frames from one that merely approaches a distant viable cell.
- **Required falsifier:** Retain the exact immutable roots bracketing the
  viable-to-losing transition of the episode containing the canonical first
  hit, including hazard/policy versions,
  float32-margin identity, active/held/pending complete masks, remaining-delay
  information set, cadence support, action set, and continuation contract.
  Compare every proposed root action using completed G3/G4 causal
  partial-survival witnesses and the independent scalar belief oracle.
- **Decision:** Do not tune the live geometric fallback from this trace.
  First implement deterministic pre-hit loss-bracket capsule selection,
  reproduce the Boolean-empty root offline, and measure whether a completed
  restricted policy class provides a longer attainable survival prefix. Any
  unvisited, timed-out, or unsupported action remains unresolved.
- **Observed tooling gate:** The implemented analyzer counts 15 earlier
  recovered episodes and stops unresolved at decision/query `2049/2048`
  because this run has no audit capsule. It does not substitute a later or
  similar root. A capsule-bearing Stage-4A implementation check completes
  both `36 x 36` portfolios with zero scalar/native mismatch, but both roots
  are `model_unknown` from the first successor. The Stage-5 physical
  counterexample and future-hazard-coverage blocker therefore remain open.
- **Fresh physical falsifier workload:** Capsule-enabled Stage-5 run
  `lunatic_route2_stage5_unattended_20260728_133633` completes 13,304
  decisions over frames `1..44822` with 23 hits and hard no-Bomb. Its
  canonical hit is frame 4027; after 24 earlier recovered episodes the active
  loss begins at frame 3752, 275 frames before contact. All 1,879 capsules
  are readable and cleanup is complete.
- **Finite-model separation:** Exact roots
  `3750 viable -> 3752 losing` complete both `36 x 36` portfolios with zero
  scalar/native mismatch. Issued masks `0x55/0x85` retain `30/22` frames,
  while best G4/G3 masks `0x10/0x11` and `0x20/0x21` retain 32.
- **Why this does not close the counterexample:** Both roots declare unseen
  future hazards `UNKNOWN` from the first successor. The ten-frame G3
  difference is exact only inside the retained finite proxy. It is not a
  physical lower bound and cannot authorize replacing the live action.
- **Revised decision:** The missing-capsule gate is closed. Keep CE-0158 open
  on physical-model validity and continue G5 causal containing coverage
  before another action-ranking or promotion experiment.
- **Evidence:** Raw trace SHA-256 is
  `711e9e7fe86b65ee7f6993e3081df9f5d25bdb9bf32721ee222ce8402b630965`;
  the compact run review is
  `notes/runs/lunatic_route2_stage5_unattended_20260728_124930.md`.

## CE-0159: Nonfinite lane sentinels produced non-standard JSON evidence

Status: observed artifact-integrity counterexample; future publication fixed
offline, post-fix physical trace gate pending

- **Observed:** Fresh Stage-5 raw trace `20260728_133633` contains 9,104
  `-Infinity` tokens. Its generated summary and embedded session summary each
  contain 98 more. Strict RFC-compatible JSON readers reject those files.
- **Cause:** An unreachable corridor plan represents
  `lane=none` bottleneck clearance as negative infinity. The trace adapter
  copied that internal numeric sentinel directly, and JSON writers used
  Python's permissive default.
- **Correction:** The trace adapter now publishes a nonfinite
  bottleneck-clearance sentinel as explicit JSON `null`. The live `TraceSink`
  and every unattended summary, session, dossier, regression, and comparison
  writer use `allow_nan=False`, so any unhandled nonfinite value fails before
  publishing the offending record.
- **Retained evidence:** The raw trace is not rewritten and remains SHA-256
  `5a40e13e0979fc484f41147e15730c23ebf4876e463e1428fc4ac9ad80fc9bdd`.
  The two new derived compact files were mechanically normalized only at the
  98 known lane-transition sentinels; strict readers accept every retained
  compact JSON.
- **Performance check:** On one retained 27,253-byte decision record, ABBA
  strict/default JSON median ratios are `1.0082` on Linux and `1.0163` on
  Windows, adding about `0.003/0.008 ms`. This is a local serialization
  check, not a physical B4 pass.
- **Validation:** Deterministic tests cover `null` normalization, strict
  single/batch emission, and rejection before publishing a nonfinite record.
  Complete Linux/Windows suites pass 866 tests; Windows has three existing
  skips.
- **Authority:** Artifact serialization only. No recurrence, planner,
  actuator, cadence, or live action changed. A future no-capsule physical
  run must confirm trace compatibility and unchanged timing before any B4
  conclusion.

## CE-0160: A post-loss nonspell birth and reused slots defeat naive hit provenance

Status: observed physical source-coverage and provenance counterexample;
offline join corrected, G5 source coverage open

- **Observed workload:** Accepted Stage-5 run `20260728_124930` contains 15
  dossier hits. The strict same-epoch audit classifies four candidates as
  exact observed overlaps and eleven as nearest-only; it never upgrades a
  nearest candidate into an exact collider.
- **Canonical negative result:** The canonical frame-2167 exact overlap in
  slot 1357 has native activation support `1887..1888`, before loss frame
  2049. It is not a realized post-loss birth.
- **Positive source-coverage witness:** Slot 1295 belongs to a 30-bullet
  activation wave with native support `13868..13869`, strictly after loss
  frame 13864. It later overlaps exactly at frame 14043 with signed clearance
  about `-1.4697`. The phase is nonspell, `spell_enemy_pointer == 0`, and no
  captured intent covers the wave. Current observer scope is
  `active_spell_enemy_main_vm_only`; omitted source classes include nonspell
  main VMs, child/auxiliary VMs, callbacks or interrupts, deferred native
  state, and non-ECL native sources.
- **Analysis counterexample:** A first implementation applied one global
  epoch to all dossier hits and selected an older reused-slot generation for
  frame 14043. Joining each hit to its exact decision row first, then selecting
  only a latest activation in that hit's gameplay epoch, corrects the result.
  Bootstrap and timer-regression rows remain explicit ambiguity instead of
  invented exact birth times.
- **Rejected inferences:** The witness does not show that every hit is a
  future-birth failure, that this later post-death contact is an independent
  survival trial, or that observing the source would have produced a viable
  counterfactual action. Eleven nearest-only candidates are not colliders.
- **Correction and next gate:** Retain the modular action-free audit. Contract
  nonspell source identity, update order, observation availability, and
  deadline before extending live capture. In parallel, keep working on
  earlier finite-model viability loss; do not promote an envelope or action.
- **Evidence:** Compact report
  `artifacts/viability_audit/g5_birth_hit_stage5_20260728_124930.json` has
  internal/file SHA-256
  `4d774124cf4de47ba69f53b462a0fe642377a988f3ec1a1b0d64ab0e20e2ff5c` /
  `7934ac279aef7911f23141efa6287239f427a2c08e87e376c0d10d873691d676`.
  Raw trace SHA-256 is
  `711e9e7fe86b65ee7f6993e3081df9f5d25bdb9bf32721ee222ce8402b630965`.
- **Authority:** Evidence and offline analysis only. No planner, recurrence,
  actuator, cadence, or live action changed.

## CE-0161: A ready-parent transform shadow had zero signal and broke its combined budget

Status: observed physical source and performance counterexample; source
hypothesis rejected and observer isolated behind a separate explicit opt-in

- **Observed workload:** Lunatic Stage-5 run `20260728_150827` completed
  11,801 decisions over frames `2..42172` with 12 hits, hard no-Bomb,
  `route_complete`, exact cleanup, and no residual process.
- **Source falsifier:** All 11,801 native source scans validated without
  error, but candidate rows and candidate sightings were both zero. The
  repeating 30-bullet nonspell wave was reproduced at frames 13861 and 13879
  with the same two-age, ten-groups-of-three shape and no previously observed
  ready parent.
- **Bounded conclusion:** The exact readiness predicate cannot attribute the
  target wave. This does not exclude a derived transform that becomes ready
  and executes entirely inside a controller capture gap.
- **Performance falsifier:** Combined birth-plus-source p50/p95/p99/p99.9/max
  was `0.1346/0.2633/0.4982/3.7388/9.0368 ms`, failing the fixed
  `0.20/0.40/2.00 ms` gate. The separate source pass contributed p95
  `0.0474 ms`. Its max was a `gil-released` native-call wall tail, so the
  scheduler cause remains inferred rather than observed.
- **Correction:** Source scanning now requires the separate
  `--trace-derived-pattern-sources` opt-in. Ordinary birth tracing retains
  schema v9 and does not pay the rejected second pool pass; the explicit
  source experiment alone emits schema v10.
- **Rejected next action:** Do not fuse or publish this zero-signal source
  class merely to make its benchmark pass. Reopen fusion only if a new
  source contract has physical signal that justifies the contention budget.
  Follow the fixed stop-rule source order.
- **Evidence:** Deterministic audit/file SHA-256
  `a08f137081e51b70994125f7c4a2d165541d936e61a924bde8d58a4f6f0c9bda`;
  raw trace SHA-256
  `9081e3ed9ea337016ecfd5fdf4cc8d2a17591b1416ec19060233ade6e3e6565b`.
- **Authority:** Negative source/performance evidence only. No planner,
  recurrence, actuator, cadence, future geometry, or action authority changed.

## CE-0162: Main-PC-only source coverage omits demonstrated auxiliary VMs and still loses Stage 5

Status: observed physical source-topology, performance, and survival
counterexample; ordinary inventory retained, main-only completeness rejected

- **Observed workload:** Lunatic Stage-5 run `20260728_155426` completed
  11,891 decisions over frames `1..41612` with 11 hits, hard no-Bomb,
  `route_complete`, exact key release, and no residual process. The canonical
  frame-2,390 nonspell contact and every later contact follow global viability
  exhaustion.
- **Main-VM observation:** All 11,891 schema-v11 rows validate. There are
  138,255 valid main-VM rows, 64 unique PCs, zero invalid active VMs, 11,890
  stable brackets, and one capture-spanned bracket. One unique affine base
  maps 64/64 PCs to decoded Stage-5 ECL instruction boundaries.
- **Direct source signal:** Twenty exact captured opcode-`0x60` to sequential
  successor transitions align one-to-one with 20 activation batches containing
  260 bullets. This falsifies treating the useful main-VM source class like
  the zero-signal ready-parent scan.
- **Completeness falsifier:** IDA observes opcode `0x87` allocating and
  scheduling one of four heap auxiliary ECL contexts rooted at
  `enemy+0x3384`. The trace contains 81 exact `0x87` advances, all compatible
  with activation support, covering 105 batches and 1,520 bullets. Recording
  only the main PC cannot be complete source coverage.
- **Remaining source uncertainty:** Runtime ECL bytes are not keyed to the
  decoded file, auxiliary context PCs are not captured, reachable fire paths
  and operands are not independently lowered, slot reuse is not excluded,
  and source candidates are not joined to hit slot generations. No hit-causal
  coverage follows from the availability counts.
- **Performance counterexample:** Inventory decode p50/p95/p99/max is
  `0.1068/0.2384/0.3136/0.5379 ms`. Combined observer
  p50/p95/p99/p99.9/max is
  `0.1032/0.2029/0.3238/0.5339/1.7937 ms`: p99/max pass but p95 narrowly
  misses the fixed `0.20 ms` limit. The instrumentation remains an explicit
  action-free opt-in while decode/serialization are fused or moved off the
  issue boundary.
- **Correction:** Preserve the demonstrated source signal. First retain the
  four auxiliary pointers from the already captured enemy blob, then contract
  bounded post-issue context observation and exact immutable runtime ECL
  identity. Unknown contexts enlarge unresolved coverage; they do not become
  absent, safe, or losing.
- **Evidence:** Source-join internal digest
  `077a9c7655a44db3228ebd86a3a2e03988c9286ed10233f6476275461ebaf691`;
  raw trace SHA-256
  `8569d64d3ce50ced529bdcf4b48e8f0daa00bfbfa8d8cec9695665f04d0283a7`.
- **Authority:** Source availability and negative completeness/performance/
  survival evidence only. No future geometry, planner, recurrence, actuator,
  cadence, feasibility, or live action authority changed.

## CE-0163: An inherited IDA label confused saved call frames with live locals

Status: observed static-analysis provenance failure; corrected before
auxiliary-VM capture implementation

- **Observed failure:** The first auxiliary-context topology note, generated
  source-join report, and inherited IDA comment labeled context `+0x230` as
  the auxiliary VM's live-local base.
- **Invalid assumption:** A pre-existing IDA name or comment was treated as
  semantic evidence without revalidating every consumer of the field.
- **Revalidation:** `ecl_eval_int` at `0x0041F420` and the corresponding
  lvalue resolver read current integers, floats, and scratch values from the
  active VM pointer at context `+0x08`, with locals at VM
  `+0x18..+0x64`. `ecl_call_subroutine` at `0x00421BD0` copies the complete
  `0x228`-byte active VM into context `+0x230 + depth * 0x228`.
  Context `+0x06` is signed 16-bit depth, saturating at 15. The allocation
  contains 16 physical slots; ordinary return restores at most slots
  `0..14`, while a saturated call can write slot 15 before return restores
  slot 14.
- **Impact:** The already retained main-VM PC, timer, and local projection
  bytes are correct, and the bad label never reached the planner or actuator.
  It would, however, have made a later auxiliary capture semantically wrong
  across calls if left uncorrected.
- **Correction:** The IDA comment at `0x0041EBE9`, source generator, retained
  report, formal observation contract, result note, research log, and
  repository contract now distinguish active state from saved frames.
  Regression coverage rejects the obsolete `local_state_offset_in_context`
  field.
- **Evidence:** Corrected source-join internal digest
  `077a9c7655a44db3228ebd86a3a2e03988c9286ed10233f6476275461ebaf691`;
  corrected retained-file SHA-256
  `10cd5bcc31badeed2b6d617125665cf168bdf1b44916e3f56677b8c774c1af5f`.
- **Durable rule:** Inherited IDA names, types, comments, pseudocode
  variables, and earlier semantic labels are hypotheses. Material conclusions
  require instruction/dataflow, caller/callee, and where possible runtime
  revalidation, with inherited, confirmed, and corrected provenance recorded
  separately.

## CE-0164: A separate owner-pool copy crosses the batch coherence frame

Status: observed physical delivery/coherence counterexample; v1 batch
semantics retained, external-owner-capture composition rejected

- **Observed workload:** Explicit trace-only Lunatic Stage-5 spell-107 run
  `20260728_185838` completed 12,216 decisions over frames `1..41601`, ten
  hits, hard no-Bomb, `route_complete`, accepted transition/session cleanup,
  and no residual game or controller process.
- **Precommitted falsifier:** Initial physical acceptance required zero
  frame-bracket, context, owner, capacity, or native failures at once per 16
  changed manager frames. Skipped or unvisited attempts could not be
  reinterpreted as success.
- **Observed failure:** The Python service separately bracketed and copied
  the 64-record, about 1.37-MiB owner prefix before entering the native
  context transaction. Nine of 124 due attempts changed by exactly one
  enemy-manager frame across that copy. Owner-capture p50/p95/max was
  `1.372/1.952/3.215 ms`.
- **Native negative evidence:** All 115 attempts that entered native code had
  zero batch status; 3,028 non-null contexts were usable, 5,848 null rows were
  explicit, and depth/PC/marker/context/owner/frame/capacity/native failures
  were all zero. Native p95/p99/max was
  `0.154/0.185/0.301 ms`. The failure is therefore localized to the external
  owner-capture transport boundary, not evidence that auxiliary VM state has
  no value.
- **Correction:** Do not waive, silently skip, or retry around the fixed
  failure. Contract a versioned one-call native transaction that brackets and
  captures the owner prefix, derives context pointers from that exact buffer,
  captures/rechecks contexts and owners, and closes the same manager bracket
  using caller-owned storage. Repeat the unchanged physical gate.
- **Evidence:** Strict physical report digest
  `440bf0ba3c653714a0b53a17f98c2413e5f592ebe85ac7e709b011901ab5bc18`;
  raw trace SHA-256
  `734878ffe0bfe891767621971b8d220ec2f5c4108d516a4776a2396f6e0a6927`.
- **Authority:** Delivery/coherence, state-density, and timing evidence only.
  No future geometry, source completeness, planner, recurrence, actuator,
  cadence, feasibility, or live action authority changed.

## CE-0165: One native-owned snapshot can still cross the game update boundary

Status: observed physical asynchronous-snapshot counterexample; v2 transport
retained, no-retry physical acceptance rejected; bounded-visible-retry
correction physically accepted

- **Observed workload:** Explicit trace-only Lunatic Stage-5 spell-107 run
  `20260728_193820` completed 13,586 decisions over frames `2..45403`, twenty
  hits, hard no-Bomb, `route_complete`, accepted transition/session cleanup,
  and no residual game or controller process.
- **Correction already achieved:** V2 removed all Python owner reads/copies,
  selected its own post-entry frame, exposed four manager frames, and captured
  owner plus contexts in one native call. Full native p95/p99/max is
  `0.463/0.584/0.894 ms`; cadence and every non-coherence gate pass.
- **Observed failure:** 7 of 235 due transactions were rejected. Two crossed
  from selected frame to owner-close frame; five retained equal selected,
  owner-close, and context-open frames but the final frame advanced by one.
  The exact frame pairs are
  `30871->30872`, `33360->33361`, `30888->30889`,
  `31946->31947`, `32975->32976`, `33135->33136`, and
  `33549->33550`.
- **Invalid assumption:** Removing the Python/native gap would make every
  asynchronously started external snapshot fit wholly inside one 60-Hz game
  update interval. Even a sub-millisecond transaction can begin immediately
  before an update boundary.
- **Correction:** Retain v2 transport and frame evidence. Reject the no-retry
  acceptance claim. Before any retry implementation, contract a fixed small
  attempt budget, expose every attempt, publish only one coherent final
  attempt, treat exhaustion as failure, and charge all attempts to unchanged
  timing/cadence gates. Do not poll for up to one frame or pause the game.
- **Observed correction validation:** Schema-v3 Stage-5 spell-107 run
  `20260728_200739` exercised four owner-close crossings among 123 due
  transactions. Each failed attempt performed three reads, exposed status
  bit 64 and its frame pair, then selected a coherent complete second attempt
  at the later frame. All 123 transactions succeeded; maximum attempt count
  was two, with zero exhaustion, terminal failure, exception, or validation
  error. Summed native p95/p99/max was
  `0.487/0.536/0.848 ms`, cadence remained `2/4/4`, and every hard no-Bomb,
  route, session, and cleanup gate passed.
- **Retained lesson:** This validates a bounded fail-closed correction, not
  the invalid atomic-snapshot assumption. Any future delivery change must
  retain complete attempt visibility, hard exhaustion, selected-version
  identity, and total transaction charging.
- **Evidence:** Strict physical report digest
  `23313712483c80c3a8323f18f31d19abbf2ed00e3bd2efcf8ef02f9b03712634`;
  raw trace SHA-256
  `76472605d19b32b875b33d918527f0e6d13169ba862362451bc0f0ae015d8f13`.
  Corrected v3 report/raw digests are
  `faf5009c326fa65d18aae331221a6fc3ce0652e313de3c1d41d27b5f916748f6`
  and
  `953a5c3cb4bef84a809c9d2681aedcc081f67cc7f8dc39aa942bc42f0da779e9`.
- **Authority:** Delivery/coherence, density, and timing evidence only. No
  future geometry, source completeness, planner, recurrence, actuator,
  feasibility, or live action authority changed.
