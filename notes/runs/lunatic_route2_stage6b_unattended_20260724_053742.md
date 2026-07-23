# TH08 Final B / Kaguya No-Bomb Practice Review: lunatic_route2_stage6b_unattended_20260724_053742

## Scope And Integrity

- Valid practice scope: `2..34506` (6112 decisions).
- Selected frame epoch: 0 of 1; 0 earlier decisions were excluded.
- Scope terminator: `runtime_error`; 0 reset-tail decisions were excluded.
- The agent's raw summary agrees with the scoped trace.
- Accepted complete practice: **NO**.
- Native hit edges: 24, at `[11930, 12356, 19396, 19890, 20365, 20825, 21239, 21924, 22321, 22692, 23007, 23315, 23697, 24099, 24487, 24821, 25113, 27308, 28132, 31308, 31785, 32320, 33202, 33759]`.
- Hard no-Bomb verification: **PASS** across 6112 decisions; mask/flag/action violations are all empty.

Bomb-stock changes in the trace are death/respawn state changes. They are not Bomb use: every scoped input mask has bit `0x02` clear, every decision has `bomb=false`, and no action requests Bomb.

## Primary Finding

The authoritative fresh-attempt hit is `LUN-S7-F11930-T1`. It occurred during spell 150 `薬符「壺中の大銀河」` at player (153.096, 234.701), with 490 bullets and 0 lasers. The projectile model reported pipeline clearance 1.251.

The primary class is `observed_bullet_overlap`. This trace contains the retained hit-window geometry for that classification; later post-respawn hits remain discovery evidence rather than fresh independent trials.

## Failure Taxonomy

| Cause | Hits |
| --- | ---: |
| `active_laser_without_observed_overlap` | 10 |
| `modeled_committed_prefix_collision` | 6 |
| `observed_bullet_overlap` | 6 |
| `observed_laser_overlap` | 1 |
| `sensor_gap_or_unmodeled_hazard` | 1 |

Contributing factors:

- `fast_mode`: 16
- `corridor_deadline_miss`: 15
- `action_lag_over_model`: 13
- `playfield_boundary`: 9
- `pool_density_over_1000`: 5

## Death Ledger

| Role | Frame | Spell | Player | Active input | Bullets/lasers | Pipeline/min 240f | Pipeline/robust warning | Contact/cause | Planner failure |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| canonical | 11930 | 150 薬符「壺中の大銀河」 | (153.096, 234.701) | `up_right_fast` | 490/0 | 1.251/-0.997 | 6f/11f | `observed_bullet_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 12356 | 150 薬符「壺中の大銀河」 | (11.457, 416.421) | `up_fast` | 700/0 | -0.961/-2.951 | 0f/33f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 19396 | nonspell | (15.489, 430.173) | `stay` | 1178/0 | 0.264/-1.435 | 5f/9f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 19890 | nonspell | (372.160, 429.179) | `right` | 1205/0 | -2.287/-2.287 | 0f/10f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 20365 | nonspell | (12.708, 424.920) | `up_fast` | 1183/0 | -1.378/-1.496 | 3f/5f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 20825 | nonspell | (363.734, 426.682) | `up_left` | 1059/0 | -2.056/-2.056 | 3f/6f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21239 | nonspell | (177.364, 426.399) | `up` | 1136/0 | -1.493/-1.493 | 0f/7f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 21924 | 154 神宝「ブリリアントドラゴンバレッタ」 | (325.649, 367.354) | `down_fast` | 68/160 | 2.821/2.821 | 0f/0f | `active_laser_without_observed_overlap` | `unresolved_planner_failure` |
| discovery | 22321 | 154 神宝「ブリリアントドラゴンバレッタ」 | (138.108, 347.402) | `down_fast` | 97/205 | 25.888/-6.676 | 0f/0f | `active_laser_without_observed_overlap` | `unresolved_planner_failure` |
| discovery | 22692 | 154 神宝「ブリリアントドラゴンバレッタ」 | (228.153, 432.000) | `up_left_fast` | 101/220 | 3.046/-5.614 | 0f/0f | `active_laser_without_observed_overlap` | `unresolved_planner_failure` |
| discovery | 23007 | 154 神宝「ブリリアントドラゴンバレッタ」 | (177.481, 314.701) | `up_right_fast` | 88/240 | -0.417/-0.417 | 0f/0f | `observed_bullet_overlap` | `missing_pre_hit_alive_decision` |
| discovery | 23315 | 154 神宝「ブリリアントドラゴンバレッタ」 | (192.417, 400.887) | `down_fast` | 72/220 | 67.605/-8.097 | 0f/0f | `active_laser_without_observed_overlap` | `missing_pre_hit_alive_decision` |
| discovery | 23697 | 154 神宝「ブリリアントドラゴンバレッタ」 | (376.000, 432.000) | `left_fast` | 93/205 | 5.049/2.557 | 0f/0f | `active_laser_without_observed_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 24099 | 154 神宝「ブリリアントドラゴンバレッタ」 | (376.000, 432.000) | `up_fast` | 108/215 | 1.387/-2.911 | 0f/14f | `active_laser_without_observed_overlap` | `robust_action_set_exhausted_before_hit` |
| discovery | 24487 | 154 神宝「ブリリアントドラゴンバレッタ」 | (232.060, 395.230) | `left_fast` | 100/220 | 30.649/-5.554 | 0f/0f | `active_laser_without_observed_overlap` | `unresolved_planner_failure` |
| discovery | 24821 | 154 神宝「ブリリアントドラゴンバレッタ」 | (8.223, 16.000) | `left` | 85/205 | 11.201/4.466 | 0f/0f | `active_laser_without_observed_overlap` | `unresolved_planner_failure` |
| discovery | 25113 | 154 神宝「ブリリアントドラゴンバレッタ」 | (132.087, 215.709) | `right_fast` | 90/215 | -0.003/-5.355 | 0f/0f | `modeled_committed_prefix_collision` | `missing_pre_hit_alive_decision` |
| discovery | 27308 | nonspell | (199.190, 118.837) | `down_fast` | 0/0 | 9999.000/45.281 | 0f/0f | `sensor_gap_or_unmodeled_hazard` | `unresolved_planner_failure` |
| discovery | 28132 | nonspell | (372.164, 407.606) | `down_left_fast` | 421/0 | 1.545/-1.430 | 3f/12f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 31308 | 158 神宝「ブディストダイアモンド」 | (208.555, 413.575) | `stay` | 164/66 | 4.797/4.797 | 0f/0f | `active_laser_without_observed_overlap` | `unresolved_planner_failure` |
| discovery | 31785 | 158 神宝「ブディストダイアモンド」 | (134.721, 424.168) | `right_fast` | 212/33 | 1.458/-1.162 | 5f/5f | `observed_bullet_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 32320 | 158 神宝「ブディストダイアモンド」 | (354.347, 432.000) | `up_right` | 196/33 | -0.371/-3.018 | 6f/6f | `observed_laser_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 33202 | 158 神宝「ブディストダイアモンド」 | (24.721, 418.695) | `down_right` | 241/66 | 6.640/-1.052 | 13f/22f | `active_laser_without_observed_overlap` | `global_viability_kernel_exhausted_before_hit` |
| discovery | 33759 | 158 神宝「ブディストダイアモンド」 | (234.277, 414.487) | `down_right_fast` | 224/66 | -1.835/-1.835 | 0f/0f | `modeled_committed_prefix_collision` | `global_viability_kernel_exhausted_before_hit` |

## Per-Phase Planner Health

| Phase | Hits | Decisions | Queries | Empty | Support outside | Constrained | Solves | Solve median ms | Bottom alive |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nonspell | 7 | 4393 | 4243 | 1720 | 95 | 2228 | 504 | 281.903 | 0.139 |
| 150 薬符「壺中の大銀河」 | 2 | 846 | 811 | 264 | 0 | 489 | 101 | 321.097 | 0.164 |
| 154 神宝「ブリリアントドラゴンバレッタ」 | 10 | 228 | 126 | 53 | 0 | 61 | 35 | 1340.422 | 0.173 |
| 158 神宝「ブディストダイアモンド」 | 5 | 645 | 627 | 261 | 0 | 235 | 118 | 430.219 | 0.223 |

## Interpretation

- Retained witnesses classify 6 bullet overlaps, 1 laser overlaps, and 0 exact same-epoch enemy-body overlaps; 0 of those enemy slots were absent from the action snapshot.
- The controller decision cadence was 3.000 frames median and 8.000 frames p95. The local plan took 21.117 ms median and 97.308 ms p95.
- The full enemy sensor produced 3894 snapshots; capture read time was `{'median': 27.299149995087646, 'p95': 111.80590000003576, 'max': 717.6292999938596}`, snapshot age was `{'median': 5.0, 'p95': 10.0, 'max': 65.0}` frames, and 8 phase-counter discontinuities were excluded; 134 decisions retained at least one contact-enabled body (maximum 26).
- The terminal-threat heuristic covered 6112 decisions with horizon counts `{'0': 121, '10': 5581, '32': 410}`; it reported 1 collision and 47 sub-safety-clearance warnings, and relaxed 410 coarse constraints at clamped aliases.
- Modeled action hold counts were `{'2': 50, '3': 987, '4': 3973, '5': 317, '6': 785}` overall.
- Modeled uncontrollable-prefix counts were `{'2': 63, '3': 1712, '4': 3572, '5': 62, '6': 703}`.
- Adaptive delay supports were `{'1,2,3': 65, '1,2,3,4': 6, '2,3': 37, '2,3,4': 94, '2,3,4,5': 1366, '2,3,4,5,6': 1798, '3,4': 23, '3,4,5': 268, '3,4,5,6': 2120, '4,5,6': 257, '5,6': 20, '6': 58}`; 83 decisions changed their nominal first action, 120 end-to-end transition samples were retained, and the maximum observed overrun/censored counters were 277/356.
- Robust viability supplied 5807 available policy queries (95 had new delay support outside the cached policy), constrained 3013 decisions, and exposed 2298 empty queried action sets. Recovery guidance was available/selected on 752/393 empty-kernel queries. Safe-action count and selected repair-volume statistics were `{'median': 5.0, 'p95': 17.0, 'max': 17.0}` and `{'median': 21.0, 'p95': 153.0, 'max': 153.0}`.
- The rolling worker produced 758 unique policies with solve-time statistics `{'median': 311.8143500032602, 'p95': 602.0749000017531, 'max': 1944.9129000131506}` and first-observed ages `{'median': 6.0, 'p95': 27.0, 'max': 1845.0}`. Policy status counts were `{'pending_future_epoch': 74, 'queryable': 5779, 'expired': 171}`; 217 robust-mode decisions had no query.
- Of 3411 unambiguous output transitions, 2976 (0.872) were already visible in the next decision snapshot; their snapshot delta had median 1.000 frame.
- Separating physical contact from planner causality gives `{'robust_action_set_exhausted_before_hit': 2, 'global_viability_kernel_exhausted_before_hit': 12, 'unresolved_planner_failure': 7, 'missing_pre_hit_alive_decision': 3}`. Active input is the game-observed input at collision; the newly issued action on a hit row occurs after hit detection.
- Robust action-set exhaustion supplied 12 hit windows with a positive warning lead; those leads were `[11, 33, 9, 10, 5, 6, 7, 0, 0, 0, 0, 0, 0, 14, 0, 0, 0, 0, 12, 0, 5, 6, 22, 0]` frames.
- Across all phases, bottom-eight-pixel occupancy was 0.331 during the 60 frames preceding a hit versus 0.140 outside those windows.
- Soft recovery was selected on 0.037 of alive decisions in the 60-frame pre-hit windows versus 0.077 outside; correlation alone is not a causal acceptance result.
- Later hits cannot estimate an initial-stock clear rate because Power falls from 128 to 1.000 after respawns. They remain valid counterexamples for geometry, latency, boundary use, and spell-specific pressure.

## Next Correction Gate

Treat policy delivery, delay-support coverage, and viability exhaustion as separate gates. The next focused run must keep rolling-policy queries available, reduce unsupported query epochs, and preserve a non-empty action kernel before each former hit window. Compare per-phase position and warning lead, not only aggregate hit count.

## Experiment Decision

This trial is **rejected as a completion baseline**. It ended at frame 34,506
with an internal representative-rollout exception, before spells 162 and
later phases. The compact dossier and 24 hit witnesses are retained only for
failure discovery.

CE-0072 fixes the crash by sharing round-to-even lattice projection and making
representative waypoint failure nonfatal. CE-0073 retains the independent
laser performance result: spell 154 reached 205--240 active lasers, produced
ten hits, and drove cadence p95 to eight frames. Stage 6B must be repeated
after both the crash regression and laser performance correction.
