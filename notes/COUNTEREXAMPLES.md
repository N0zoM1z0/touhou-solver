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
  native hit. `th08_fullrun_regression.py` now validates every case ID,
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
- **Correction gate:** Add exact spatial/time indexing or tiled batch
  reduction to the game-neutral segment-trajectory clearance builder. Any
  optimization must match the scalar geometry volume and preserve
  appearing/disappearing lifecycle samples.
- **Status:** Observed; unresolved.
